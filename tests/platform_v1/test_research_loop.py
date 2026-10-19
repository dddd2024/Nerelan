"""Provider-free campaign tests: real local git and deterministic service fakes."""

import hashlib
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from reverse_agent.platform_v1.research_loop import ResearchLoop, main, configured_loop


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class Goals:
    def __init__(self):
        self.records = {}
        self.requests = []
        self.launches = []
        self.windows = [SimpleNamespace(id="window", status="ACTIVE", repositories=("owner/research",))]
        self.control_store = SimpleNamespace(active_window=lambda: next(
            (w for w in self.windows if w.status == "ACTIVE"), None))

    def create(self, payload):
        key = payload["idempotency_key"]
        if key not in self.records:
            self.requests.append(payload)
            self.records[key] = dict(id=key, status="DRAFT", revision=1, task_links=[])
        return SimpleNamespace(**self.records[key])

    def detail(self, goal_id):
        return dict(self.records[goal_id])

    def approve(self, goal_id, **kwargs):
        self.records[goal_id]["status"] = "APPROVED"

    def launch(self, goal_id, **kwargs):
        if self.records[goal_id]["status"] != "RUNNING":
            self.launches.append(goal_id)
            self.records[goal_id]["status"] = "RUNNING"


class Planner:
    def __init__(self, goals):
        self.goals = goals
        self.starts = []

    def status(self, goal_id):
        return {"status": "NONE"}

    def start(self, goal_id, **kwargs):
        self.starts.append(goal_id)
        self.goals.records[goal_id]["status"] = "PLANNED"


class ResearchLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Tests")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")
        self.git("remote", "add", "origin", "https://github.com/owner/research.git")
        (self.repo / "seed").write_text("base\n")
        self.git("add", "seed")
        self.git("commit", "-m", "initial")
        self.base = self.git("rev-parse", "HEAD")
        self.config = dict(campaign_id="campaign", repository="owner/research", objective="Find evidence",
                           state_dir=str(self.root / "state"), executor_kind="codex", binding_ref="binding",
                           max_rounds=12, max_hours=72, max_consecutive_failed_rounds=2, poll_seconds=1,
                           max_job_wait_hours=24)
        self.file = self.root / "campaign.json"
        write_json(self.file, self.config)
        self.goals = Goals()
        self.planner = Planner(self.goals)
        self.now = 1000
        self.broker = self.root / "broker"

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result.stdout.strip()

    def loop(self):
        return ResearchLoop(self.file, goal_service=self.goals, planner=self.planner,
                            broker_root=self.broker, repo_dir=self.repo, clock=lambda: self.now)

    def state(self):
        return json.loads((self.root / "state/campaign/state.json").read_text())

    def round(self, n=1):
        return json.loads((self.root / f"state/campaign/rounds/{n}.json").read_text())

    def tick(self):
        # Every tick uses a fresh instance: exercise all persisted phase boundaries.
        self.loop().tick()

    def launch(self):
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round(self.state()["round"])["state"], "LAUNCHED")

    def task(self, task_id, files, base=None):
        self.git("switch", "-c", task_id, base or "main")
        for name, content in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.git("add", "--", *files)
        self.git("commit", "-m", task_id)
        sha = self.git("rev-parse", "HEAD")
        self.git("switch", "main")
        return dict(task_id=task_id, status="READY_FOR_REVIEW", publication={"commit_sha": sha})

    def complete(self, tasks, n=1, status="COMPLETED"):
        self.goals.records[f"campaign-round-{n}"].update(status=status, task_links=tasks)

    def receipt(self, job, mismatch=False):
        source = self.broker / job
        source.mkdir(parents=True, exist_ok=True)
        data = b"measurement\n"
        (source / "outputs").mkdir(exist_ok=True)
        (source / "outputs/value.txt").write_bytes(data)
        (source / "stdout.log").write_bytes(b"ok")
        write_json(source / "receipt.json", {"job_id": job, "state": "RESULT_COLLECTED"})
        write_json(source / "manifest.json", {"files": [
            {"path": "outputs/value.txt", "size": len(data),
             "sha256": "0" * 64 if mismatch else hashlib.sha256(data).hexdigest()},
            {"path": "stdout.log", "size": 2, "sha256": hashlib.sha256(b"ok").hexdigest()}]})

    def test_three_rounds_and_restarts(self):
        for n in range(1, 4):
            self.launch()
            job = f"r{n}-experiment"
            files = {"RESEARCH_LOG.md": f"Round {n}: hypothesis, run, result uncertain, next\n",
                     f".nerelan-remote/outbox/{job}/job.json": json.dumps({"job_id": job})}
            if n == 3:
                files["CAMPAIGN_DONE.md"] = "Objective met with evidence."
            task = self.task(f"task-{n}", files)
            self.complete([task], n)
            for _ in range(3):
                self.tick()
            self.assertEqual(self.round(n)["state"], "WAITING_JOBS")
            self.tick()
            self.assertEqual(self.round(n)["state"], "WAITING_JOBS")
            self.receipt(job)
            self.tick()
            self.assertEqual(self.round(n)["state"], "RESULTS_IMPORTED")
            self.assertEqual((self.repo / f"results/{job}/outputs/value.txt").read_bytes(), b"measurement\n")
            for _ in range(2):
                self.tick()
            self.assertEqual(self.round(n)["state"], "DONE")
            self.assertTrue(self.round(n)["research_log_present"])
            self.assertTrue(self.round(n)["research_log_updated"])
            transitions = [event["state"] for event in self.round(n)["history"]]
            self.assertEqual(transitions[:6], ["CREATING", "PLANNING", "LAUNCHED", "GOAL_DONE",
                                               "INTEGRATED", "WAITING_JOBS"])
            self.assertEqual(transitions[-2:], ["RESULTS_IMPORTED", "DONE"])
        self.tick()
        self.assertEqual(self.state()["state"], "COMPLETED")
        self.assertEqual([r["idempotency_key"] for r in self.goals.requests],
                         [f"campaign-round-{n}" for n in range(1, 4)])
        self.assertEqual(len(self.planner.starts), 3)
        self.assertEqual(len(self.goals.launches), 3)
        for request in self.goals.requests:
            self.assertIn("~/wjc", request["objective"])
            self.assertIn("RESEARCH_LOG.md", request["objective"])
        self.assertEqual(len(self.git("log", "--merges", "--format=%s").splitlines()), 3)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_no_window_and_recovery(self):
        self.goals.windows = []
        self.tick()
        self.assertEqual(self.state()["state"], "PAUSED_NO_WINDOW")
        self.assertEqual(self.goals.requests, [])
        self.goals.windows = [SimpleNamespace(id="existing", status="ACTIVE", repositories=("owner/research",))]
        self.launch()
        self.assertEqual(self.state()["state"], "RUNNING")
        self.assertEqual(self.goals.windows[0].id, "existing")

    def test_conflict_continues(self):
        first = self.task("first", {"seed": "first\n"}, self.base)
        conflict = self.task("conflict", {"seed": "conflict\n"}, self.base)
        other = self.task("other", {"other": "other\n"}, self.base)
        self.launch()
        self.complete([first, conflict, other])
        self.tick()
        self.tick()
        integrations = self.round()["integrations"]
        self.assertTrue(integrations["first"]["integrated"])
        self.assertIn("error", integrations["conflict"])
        self.assertTrue(integrations["other"]["integrated"])
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_restart_aborts_only_the_campaigns_conflicting_merge(self):
        first = self.task("first", {"seed": "first\n"}, self.base)
        conflict = self.task("conflict", {"seed": "conflict\n"}, self.base)
        other = self.task("other", {"other": "other\n"}, self.base)
        self.launch()
        self.complete([first, conflict, other])
        self.tick()
        loop = self.loop()
        original = loop._git
        def crash(*args, **kwargs):
            result = original(*args, **kwargs)
            if args[0] == "merge" and result.returncode:
                raise RuntimeError("crash before abort")
            return result
        with patch.object(loop, "_git", side_effect=crash):
            with self.assertRaisesRegex(RuntimeError, "crash before abort"):
                loop.tick()
        self.tick()
        self.assertIn("interrupted", self.round()["integrations"]["conflict"]["error"])
        self.assertTrue(self.round()["integrations"]["other"]["integrated"])
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_terminal_snapshot_pins_task_commit(self):
        first = self.task("first", {"evidence": "first\n"})
        alternate = self.task("alternate", {"evidence": "alternate\n"})
        self.launch()
        self.complete([first])
        self.tick()
        first["publication"]["commit_sha"] = alternate["publication"]["commit_sha"]
        self.tick()
        self.assertEqual((self.repo / "evidence").read_text(), "first\n")

    def test_native_task_snapshot_reuses_temporary_index_without_mutating_worktree(self):
        worktree = self.root / "native-task"
        self.git("worktree", "add", "--detach", str(worktree), self.base)
        (worktree / "RESEARCH_LOG.md").write_bytes(b"Hypothesis, run, uncertain result, next.\n")
        (worktree / ".nerelan-remote/outbox/r1-native").mkdir(parents=True)
        (worktree / ".nerelan-remote/outbox/r1-native/job.json").write_bytes(b"{}\n")
        task = SimpleNamespace(id="native-task", execution_id="native-exec", evidence_refs=[],
                               repository="owner/research")
        run = SimpleNamespace(worktree_path=str(worktree), execution_id=task.execution_id,
                              accepted_checkpoint="POST_VALIDATION", repository_base_sha=self.base)
        self.goals.store = SimpleNamespace(get_task=lambda task_id: task,
            get_latest_durable_run_observation=lambda task_id: SimpleNamespace(run_id="run"),
            _get_durable_run=lambda run_id: run)
        self.launch()
        self.complete([dict(task_id=task.id, status="READY_FOR_REVIEW", publication=None)])
        self.tick()
        sha = self.round()["tasks"][0]["commit_sha"]
        self.assertEqual(len(sha), 40, self.round()["tasks"])
        self.assertNotEqual(sha, self.base)
        self.assertEqual(subprocess.check_output(["git", "-C", str(worktree), "rev-parse", "HEAD"],
                                                text=True).strip(), self.base)
        self.assertEqual(subprocess.check_output(["git", "-C", str(worktree), "diff", "--cached", "--name-only"],
                                                text=True).strip(), "")
        self.assertTrue((worktree / "RESEARCH_LOG.md").exists())
        self.assertEqual(self.loop()._task_commit(dict(task_id=task.id)), sha)
        self.tick()
        self.assertTrue((self.repo / "RESEARCH_LOG.md").exists())
        self.assertEqual(self.round()["jobs"], ["r1-native"])

    def test_manifest_mismatch_recorded(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-bad/job.json": "{}"})])
        self.receipt("r1-bad", mismatch=True)
        for _ in range(4):
            self.tick()
        self.assertIn("manifest mismatch", self.round()["imports"]["r1-bad"]["error"])
        self.assertFalse((self.repo / "results/r1-bad").exists())

    def test_stop_and_expiry(self):
        self.tick()
        stop = self.root / "state/campaign/STOP"
        stop.touch()
        self.tick()
        self.assertEqual(self.state()["state"], "STOPPED")
        stop.unlink()
        self.tick()
        self.assertEqual(self.state()["state"], "STOPPED")

    def test_max_hours(self):
        self.tick()
        self.now += 72 * 3600
        self.tick()
        self.assertEqual(self.state()["state"], "EXPIRED")

    def test_max_rounds(self):
        self.config["max_rounds"] = 1
        write_json(self.file, self.config)
        self.launch()
        self.complete([self.task("task", {"RESEARCH_LOG.md": "round 1"})])
        for _ in range(8):
            self.tick()
        self.assertEqual(self.state()["state"], "COMPLETED")
        self.assertEqual(len(self.goals.requests), 1)

    def test_consecutive_failures(self):
        for n in (1, 2):
            self.launch()
            self.complete([], n, "FAILED")
            for _ in range(6):
                self.tick()
        self.assertEqual(self.state()["state"], "PAUSED_FAILING")
        self.assertEqual(len(self.goals.requests), 2)

    def test_interrupted_round_not_replayed(self):
        self.launch()
        self.complete([dict(task_id="interrupted", status="INTERRUPTED")], status="RUNNING")
        for _ in range(6):
            self.tick()
        self.assertEqual(self.round()["state"], "INTERRUPTED")
        self.tick()
        self.assertIn("previous round was INTERRUPTED", self.goals.requests[-1]["objective"])
        self.assertEqual(len(self.goals.launches), 1)

    def test_idempotency_crash_after_create(self):
        loop = self.loop()
        original = loop._event
        def crash(record, state, detail, path):
            if state == "PLANNING":
                raise RuntimeError("simulated crash")
            original(record, state, detail, path)
        with patch.object(loop, "_event", side_effect=crash):
            with self.assertRaisesRegex(RuntimeError, "simulated"):
                loop.tick()
        self.tick()
        self.assertEqual(len(self.goals.requests), 1)

    def test_crash_after_merge_and_results_commit(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}"})])
        self.tick()
        loop = self.loop()
        original = loop._save
        def crash(record, path):
            if record.get("integrations", {}).get("task", {}).get("integrated"):
                raise RuntimeError("crash after merge")
            original(record, path)
        with patch.object(loop, "_save", side_effect=crash):
            with self.assertRaisesRegex(RuntimeError, "crash after merge"):
                loop.tick()
        self.tick()
        self.assertEqual(self.round()["jobs"], ["r1-job"])
        self.assertEqual(len(self.git("log", "--merges", "--format=%s").splitlines()), 1)
        self.tick()
        self.receipt("r1-job")
        loop = self.loop()
        original_event = loop._event
        def crash_import(record, state, detail, path):
            if state == "RESULTS_IMPORTED":
                raise RuntimeError("crash after import commit")
            original_event(record, state, detail, path)
        with patch.object(loop, "_event", side_effect=crash_import):
            with self.assertRaisesRegex(RuntimeError, "crash after import commit"):
                loop.tick()
        self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.git("log", "--format=%s").splitlines().count("round 1: results"), 1)

    def test_repository_mismatch(self):
        self.config["repository"] = "other/repository"
        write_json(self.file, self.config)
        with self.assertRaisesRegex(Exception, "repository_workspace_mismatch"):
            self.loop()
        self.assertFalse((self.root / "state").exists())

    def test_launch_recovery_without_window(self):
        self.tick()
        self.tick()
        self.assertEqual(self.round()["state"], "PLANNING")
        # Simulate launch's durable database commit preceding its state-file write.
        self.goals.records["campaign-round-1"]["status"] = "RUNNING"
        self.goals.windows = []
        self.tick()
        self.assertEqual(self.round()["state"], "LAUNCHED")
        self.assertEqual(self.goals.launches, [])

    def test_window_disappears_after_planning(self):
        for _ in range(2):
            self.tick()
        self.goals.windows = []
        self.tick()
        self.assertEqual(self.state()["state"], "PAUSED_NO_WINDOW")
        self.assertEqual(self.goals.launches, [])
        self.assertEqual(self.planner.starts, ["campaign-round-1"])

    def test_rejected_receipt_is_imported(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-reject/job.json": "{}"})])
        write_json(self.broker / "r1-reject/receipt.json", {"state": "REJECTED", "job_id": "r1-reject"})
        for _ in range(4):
            self.tick()
        self.assertTrue(self.round()["imports"]["r1-reject"]["imported"])
        self.assertTrue((self.repo / "results/r1-reject/receipt.json").exists())

    def test_failed_execution_waits_for_collection(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-failed/job.json": "{}"})])
        write_json(self.broker / "r1-failed/receipt.json", {"state": "FAILED"})
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "WAITING_JOBS")

    def test_transient_collection_error_then_success(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}"})])
        # The broker marks the receipt LOST/TIMED_OUT/FAILED before collecting;
        # the loop must not import early, and must retry once collected.
        write_json(self.broker / "r1-job/receipt.json", {"state": "TIMED_OUT"})
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "WAITING_JOBS")
        self.assertNotIn("r1-job", self.round()["imports"])
        self.receipt("r1-job")
        self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertTrue(self.round()["imports"]["r1-job"]["imported"])

    def test_import_rechecks_manifest_exists(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}"})])
        self.receipt("r1-job")
        # Simulate the broker receipt claiming collection while no manifest exists.
        write_json(self.broker / "r1-job/receipt.json", {"state": "RESULT_COLLECTED"})
        (self.broker / "r1-job/manifest.json").unlink()
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.round()["imports"]["r1-job"]["error"], "collection manifest missing")

    def test_no_broker_records_and_continues(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}"})])
        self.broker = None
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.round()["imports"]["r1-job"]["error"], "NO_BROKER")
        self.tick()
        self.assertEqual(self.round()["state"], "DONE")

    def test_self_heal_crash_left_import_temporary(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}"})])
        self.receipt("r1-job")
        for _ in range(3):
            self.tick()
        from reverse_agent.platform_v1 import research_loop
        replace = research_loop.os.replace
        def crash(source, dest):
            if str(dest).endswith("value.txt"):
                raise OSError("crash leaving temporary")
            replace(source, dest)
        with patch.object(research_loop.os, "replace", side_effect=crash):
            self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertIn("error", self.round()["imports"]["r1-job"])
        leftover = self.repo / "results/r1-job/outputs/.value.txt.nerelan-import"
        self.assertTrue(leftover.exists())
        self.assertIn("results", self.git("status", "--porcelain"))
        # A fresh tick that re-enters a checkout must self-heal the loop's own leftover.
        loop = self.loop()
        loop._checkout({"branch": "main"})
        self.assertFalse(leftover.exists())
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_self_heal_leaves_unrelated_work_paused(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}"})])
        self.receipt("r1-job")
        for _ in range(6):
            self.tick()
        self.assertEqual(self.round()["state"], "DONE")
        (self.repo / "unrelated").write_text("not the loop's")
        loop = self.loop()
        with self.assertRaisesRegex(RuntimeError, "existing work"):
            loop._checkout({"branch": "main"})
        self.assertEqual((self.repo / "unrelated").read_text(), "not the loop's")

    def test_loop_commits_use_explicit_identity(self):
        self.task("task", {"RESEARCH_LOG.md": "round 1 evidence\n"})
        self.git("config", "--unset", "user.name")
        self.git("config", "--unset", "user.email")
        self.launch()
        self.complete([dict(task_id="task", status="READY_FOR_REVIEW",
                            publication={"commit_sha": self.git("rev-parse", "task")})])
        for _ in range(4):
            self.tick()
        author = self.git("log", "-1", "--format=%an <%ae>")
        self.assertEqual(author, "Nerelan research <research@nerelan.invalid>")

    def test_stop_records_still_running_goal(self):
        self.launch()
        self.assertEqual(self.round()["state"], "LAUNCHED")
        stop = self.root / "state/campaign/STOP"
        stop.touch()
        self.tick()
        self.assertEqual(self.state()["state"], "STOPPED")
        detail = self.round()["history"][-1]["detail"]
        self.assertIn("while goal still running", detail)
        self.assertEqual(self.goals.records["campaign-round-1"]["status"], "RUNNING")

    def test_lost_job_waits_until_deadline(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-lost/job.json": "{}"})])
        write_json(self.broker / "r1-lost/receipt.json", {"state": "LOST"})
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "WAITING_JOBS")
        self.assertEqual(self.round()["job_states"], {"r1-lost": "LOST"})
        self.now += self.config["max_job_wait_hours"] * 3600
        self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.round()["imports"]["r1-lost"]["error"], "JOB_WAIT_EXPIRED")

    def test_deadline_preserves_collected_results(self):
        self.launch()
        self.complete([self.task("task", {
            ".nerelan-remote/outbox/r1-a/job.json": "{}",
            ".nerelan-remote/outbox/r1-b/job.json": "{}"})])
        write_json(self.broker / "r1-b/receipt.json", {"state": "RUNNING"})
        for _ in range(4):
            self.tick()
        record = self.round()
        self.assertEqual(record["state"], "WAITING_JOBS")
        self.assertEqual(record["job_states"], {"r1-a": "NO_RECEIPT", "r1-b": "RUNNING"})
        self.receipt("r1-a")
        self.now = record["waiting_since"] + self.config["max_job_wait_hours"] * 3600
        self.assertLess(self.now - self.state()["started_at"], self.config["max_hours"] * 3600)
        self.tick()
        record = self.round()
        self.assertEqual(record["state"], "RESULTS_IMPORTED")
        self.assertTrue(record["imports"]["r1-a"]["imported"])
        self.assertNotIn("error", record["imports"]["r1-a"])
        self.assertEqual((self.repo / "results/r1-a/outputs/value.txt").read_bytes(), b"measurement\n")
        self.assertEqual(record["imports"]["r1-b"]["error"], "JOB_WAIT_EXPIRED")
        self.assertFalse((self.repo / "results/r1-b").exists())
        committed = self.git("show", "--pretty=format:", "--name-only", "HEAD").split()
        self.assertIn("results/r1-a/outputs/value.txt", committed)
        self.assertEqual(self.git("status", "--porcelain"), "")
        for _ in range(2):
            self.tick()
        self.assertEqual(self.round()["state"], "DONE")
        self.assertEqual(self.state()["round"], 2)
        self.assertEqual(self.state()["state"], "RUNNING")

    def test_failed_goal_with_queued_dependents_finishes(self):
        self.launch()
        self.complete([{ "task_id": "failed", "status": "FAILED"},
                       {"task_id": "dependent", "status": "QUEUED"}], status="BLOCKED")
        for _ in range(5):
            self.tick()
        self.assertEqual(self.round()["state"], "FAILED")

    def test_blocked_goal_waits_for_running_siblings(self):
        self.launch()
        self.complete([{"task_id": "failed", "status": "FAILED"},
                       {"task_id": "sibling", "status": "RUNNING"}], status="BLOCKED")
        self.tick()
        self.assertEqual(self.round()["state"], "LAUNCHED")
        self.complete([{"task_id": "failed", "status": "FAILED"},
                       {"task_id": "sibling", "status": "CANCELLED"}], status="BLOCKED")
        self.tick()
        self.assertEqual(self.round()["state"], "GOAL_DONE")

    def test_os_lock_excludes_another_instance(self):
        from reverse_agent.platform_v1.remote_jobs import _BrokerLock
        loop = self.loop()
        with _BrokerLock(loop.root / "loop.lock"):
            with self.assertRaises(OSError):
                self.loop().tick()
        self.tick()
        self.assertEqual(len(self.goals.requests), 1)

    def test_manifest_traversal_rejected(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}"})])
        self.receipt("r1-job")
        manifest = self.broker / "r1-job/manifest.json"
        write_json(manifest, {"files": [{"path": "../../escape", "size": 0, "sha256": "0" * 64}]})
        for _ in range(4):
            self.tick()
        self.assertIn("error", self.round()["imports"]["r1-job"])
        self.assertFalse((self.repo / "results").exists())

    def test_existing_results_preserved(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}",
                                           "results/r1-job/precious": "preserve me"})])
        self.receipt("r1-job")
        for _ in range(4):
            self.tick()
        self.assertIn("already exists", self.round()["imports"]["r1-job"]["error"])
        self.assertEqual((self.repo / "results/r1-job/precious").read_text(), "preserve me")

    def test_crash_during_results_copy(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/r1-job/job.json": "{}"})])
        for _ in range(3):
            self.tick()
        self.receipt("r1-job")
        from reverse_agent.platform_v1 import research_loop
        replace = research_loop.os.replace
        def crash(source, dest):
            if str(dest).endswith("value.txt"):
                raise RuntimeError("crash during copy")
            replace(source, dest)
        with patch.object(research_loop.os, "replace", side_effect=crash):
            with self.assertRaisesRegex(RuntimeError, "crash during copy"):
                self.tick()
        self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_dirty_repository_preserved(self):
        self.launch()
        self.complete([self.task("task", {"research": "new evidence"})])
        self.tick()
        (self.repo / "precious").write_text("existing work")
        with self.assertRaisesRegex(RuntimeError, "existing work"):
            self.tick()
        self.assertEqual((self.repo / "precious").read_text(), "existing work")

    def test_push_failure_attempted_once(self):
        self.config["push"] = True
        write_json(self.file, self.config)
        self.launch()
        self.complete([self.task("task", {"RESEARCH_LOG.md": "round 1"})])
        for _ in range(4):
            self.tick()
        loop = self.loop()
        original = loop._git
        calls = []
        def git(*args, **kwargs):
            if args[0] == "push":
                calls.append(args)
                return SimpleNamespace(returncode=1, stderr="fake failure")
            return original(*args, **kwargs)
        with patch.object(loop, "_git", side_effect=git):
            loop.tick()
        self.tick()
        self.assertEqual(calls, [("push", "origin", "main")])
        self.assertEqual(self.round()["push"]["returncode"], 1)

    def test_status_is_read_only_and_disabled_default(self):
        with patch("builtins.print") as output:
            self.assertEqual(main(["status", "--campaign", str(self.file), "--json"]), 0)
        self.assertIn("NOT_STARTED", output.call_args.args[0])
        self.assertFalse((self.root / "state").exists())
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(configured_loop(goal_service=self.goals, planner=self.planner))

    def test_real_goal_service_and_agent_planner_with_fake_runner(self):
        from reverse_agent.platform_v1.agent_planner import AgentPlanner
        from reverse_agent.platform_v1.autonomy import AutonomyService
        from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
        from reverse_agent.platform_v1.control_store import PlatformControlStore
        from reverse_agent.platform_v1.goal_service import GoalService
        from reverse_agent.platform_v1.run_store import TaskStore
        store = TaskStore(":memory:")
        self.addCleanup(store._conn.close)
        control = PlatformControlStore(store)
        autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
        now = datetime.now(timezone.utc)
        autonomy.activate({"policy_id": "research-window", "policy_revision": 1,
            "owner_identity": "test-owner", "starts_at": (now - timedelta(seconds=5)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(), "repositories": ["owner/research"],
            "capabilities": ["execute_task", "validate_task"], "max_concurrent_tasks": 2,
            "max_tasks": 10, "max_retries": 1, "confirmation": "ACTIVATE"})
        self.goals = GoalService(store=store, control_store=control,
                                 roster_resolver=lambda role: ("codex", "binding"))
        calls = []
        def runner(**kwargs):
            calls.append(kwargs)
            return json.dumps({"acceptance_criteria": ["Document evidence"], "tasks": [
                {"id": "T001", "title": "Research", "instruction": "Document evidence"}]})
        self.planner = AgentPlanner(goal_service=self.goals,
            roster_resolver=lambda role: ("codex", "binding"), binding_model=lambda ref: "fake",
            repo_dir_for=lambda repository: str(self.repo), runner=runner)
        # Complete synchronously to remove scheduling timing from this API test.
        start = self.planner.start
        with patch.dict("os.environ", {"REVERSE_AGENT_REPO_DIR": str(self.repo)}), patch.object(
                self.planner, "start", side_effect=lambda *a, **kw: start(*a, **kw, background=False)):
            self.launch()
        self.assertEqual(len(calls), 1)
        goal = control.get_goal(self.round()["goal_id"])
        self.assertEqual(goal.status, "RUNNING")
        self.assertEqual(goal.idempotency_key, "campaign-round-1")
        self.assertEqual(len(control.list_goal_tasks(goal.id)), 1)

    def test_host_lifecycle_uses_fakes_without_sockets_or_providers(self):
        from reverse_agent.platform_v1 import trusted_host
        from reverse_agent.platform_v1.run_store import TaskStore
        events = []
        broker = SimpleNamespace(start=lambda: events.append("broker start"),
                                 stop=lambda: events.append("broker stop"))
        loop = SimpleNamespace(start=lambda: events.append("loop start"),
                               stop=lambda: events.append("loop stop"))
        class Server:
            server_address = ("127.0.0.1", 12345)
            def __init__(self, *args, **kwargs):
                pass
            def serve_forever(self):
                pass
            def shutdown(self):
                pass
            def server_close(self):
                pass
        store = TaskStore(str(self.root / "host.sqlite3"))
        self.addCleanup(store._conn.close)
        with patch.dict("os.environ", {}, clear=True), patch.multiple(trusted_host,
                ThreadingHTTPServer=Server, configured_broker=lambda: broker,
                _model_control_handler_factory=lambda *a, **kw: None,
                _task_handler_factory=lambda *a, **kw: None), patch(
                "reverse_agent.model_access.credential_relay.run_credential_relay_server", Server), patch(
                "reverse_agent.platform_v1.research_loop.configured_loop", return_value=loop) as factory:
            host = trusted_host.CombinedTrustedHost(task_store=store, vault=None)
            with patch.object(host, "_refresh_external_session_auth"), patch.object(
                    host, "_agent_planner", return_value=self.planner):
                host.start(model_control_port=0, task_api_port=0)
                host.stop()
            self.assertIs(factory.call_args.kwargs["goal_service"], host._goal_service)
            self.assertIs(factory.call_args.kwargs["planner"], self.planner)
            self.assertIs(factory.call_args.kwargs["broker"], broker)
        self.assertEqual(events, ["broker start", "loop start", "loop stop", "broker stop"])


if __name__ == "__main__":
    unittest.main()
