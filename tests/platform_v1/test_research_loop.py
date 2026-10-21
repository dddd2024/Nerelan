"""Provider-free campaign tests: real local git and deterministic service fakes."""

import builtins
import os
import hashlib
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from reverse_agent.platform_v1 import research_loop
from reverse_agent.model_access import credential_relay
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
            if name.endswith("/job.json"):
                content = json.dumps(self.request(Path(name).parent.name))
            path.write_text(content)
        self.git("add", "--", *files)
        self.git("commit", "-m", task_id)
        sha = self.git("rev-parse", "HEAD")
        self.git("switch", "main")
        return dict(task_id=task_id, status="READY_FOR_REVIEW", publication={"commit_sha": sha})

    def complete(self, tasks, n=1, status="COMPLETED"):
        self.goals.records[f"campaign-round-{n}"].update(status=status, task_links=tasks)

    def request(self, job):
        return dict(job_id=job, command="true", files=[], outputs=[],
                    max_wall_seconds=10, gpu=False, purpose="test")

    def digest(self, job):
        raw = json.dumps(self.request(job)).encode()
        return hashlib.sha256(raw + b"{}").hexdigest()

    def receipt(self, job, mismatch=False):
        source = self.broker / job
        source.mkdir(parents=True, exist_ok=True)
        data = b"measurement\n"
        (source / "outputs").mkdir(exist_ok=True)
        (source / "outputs/value.txt").write_bytes(data)
        (source / "stdout.log").write_bytes(b"ok")
        write_json(source / "receipt.json", {"job_id": job, "state": "RESULT_COLLECTED", "request_digest": self.digest(job)})
        write_json(source / "manifest.json", {"files": [
            {"path": "outputs/value.txt", "size": len(data),
             "sha256": "0" * 64 if mismatch else hashlib.sha256(data).hexdigest()},
            {"path": "stdout.log", "size": 2, "sha256": hashlib.sha256(b"ok").hexdigest()}]})

    def ignore_results(self):
        (self.repo / ".gitignore").write_text("results/\n*.log\n*.bin\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "ignore result artifacts")
        self.base = self.git("rev-parse", "HEAD")

    def ignored_receipt(self, job):
        source = self.broker / job
        files = {"outputs/value.bin": b"measurement\n", "stdout.log": b"ok\n", "stderr.log": b"err\n"}
        for name, data in files.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        write_json(source / "receipt.json", {"job_id": job, "state": "RESULT_COLLECTED",
                                             "request_digest": self.digest(job)})
        write_json(source / "manifest.json", {"files": [
            {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in files.items()]})

    def crash_import_leftovers(self):
        job = "campaign-r1-job"
        self.launch()
        self.complete([self.task("task", {f".nerelan-remote/outbox/{job}/job.json": "{}"})])
        self.receipt(job)
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
        return job

    def test_three_rounds_and_restarts(self):
        for n in range(1, 4):
            self.launch()
            job = f"campaign-r{n}-experiment"
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
        (worktree / ".nerelan-remote/outbox/campaign-r1-native").mkdir(parents=True)
        (worktree / ".nerelan-remote/outbox/campaign-r1-native/job.json").write_bytes(json.dumps(self.request("campaign-r1-native")).encode())
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
        self.assertEqual(self.round()["jobs"], ["campaign-r1-native"])

    def test_manifest_mismatch_recorded(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-bad/job.json": "{}"})])
        self.receipt("campaign-r1-bad", mismatch=True)
        for _ in range(4):
            self.tick()
        self.assertIn("manifest mismatch", self.round()["imports"]["campaign-r1-bad"]["error"])
        self.assertFalse((self.repo / "results/campaign-r1-bad").exists())

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
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
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
        self.assertEqual(self.round()["jobs"], ["campaign-r1-job"])
        self.assertEqual(len(self.git("log", "--merges", "--format=%s").splitlines()), 1)
        self.tick()
        self.receipt("campaign-r1-job")
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

    def test_force_adds_only_verified_results_from_ignored_paths(self):
        self.ignore_results()
        (self.repo / "notes.log").write_text("unrelated log\n")
        unrelated = self.repo / "results/unrelated/value.bin"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("unrelated output\n")
        self.launch()
        job = "campaign-r1-job"
        self.complete([self.task("task", {f".nerelan-remote/outbox/{job}/job.json": "{}"})])
        self.ignored_receipt(job)
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        committed = self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        expected = [f"results/{job}/{name}" for name in (
            "receipt.json", "manifest.json", "stdout.log", "stderr.log", "outputs/value.bin")]
        self.assertEqual(sorted(committed), sorted(expected))
        self.assertEqual(self.git("ls-files", "--", "notes.log", "results/unrelated/value.bin"), "")
        ignored = self.git("status", "--porcelain", "--ignored").splitlines()
        self.assertIn("!! notes.log", ignored)
        self.assertIn("!! results/unrelated/", ignored)
        for _ in range(2):
            self.tick()
        self.assertEqual(self.git("log", "--format=%s").splitlines().count("round 1: results"), 1)

    def test_unrelated_staged_file_blocks_results_commit(self):
        self.ignore_results()
        self.launch()
        job = "campaign-r1-job"
        self.complete([self.task("task", {f".nerelan-remote/outbox/{job}/job.json": "{}"})])
        self.ignored_receipt(job)
        for _ in range(3):
            self.tick()
        self.assertEqual(self.round()["state"], "WAITING_JOBS")
        loop = self.loop()
        original = loop._git
        def crash_on_add(*args, **kwargs):
            if args[:2] == ("add", "-f"):
                raise RuntimeError("simulated import interruption")
            return original(*args, **kwargs)
        with patch.object(loop, "_git", side_effect=crash_on_add):
            with self.assertRaisesRegex(RuntimeError, "simulated import"):
                loop.tick()
        self.assertTrue(self.round()["import_pending"])
        staged = self.repo / "staged.txt"
        staged.write_text("unrelated\n")
        self.git("add", "--", "staged.txt")
        with self.assertRaisesRegex(RuntimeError, "unrelated staged files"):
            self.tick()
        self.assertNotIn("round 1: results", self.git("log", "--format=%s").splitlines())
        self.assertTrue((self.repo / f"results/{job}/receipt.json").exists())
        self.git("reset", "-q", "--", "staged.txt")
        staged.unlink()
        self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.git("log", "--format=%s").splitlines().count("round 1: results"), 1)

    def test_results_staging_is_not_retried_after_restart(self):
        self.ignore_results()
        self.launch()
        job = "campaign-r1-job"
        self.complete([self.task("task", {f".nerelan-remote/outbox/{job}/job.json": "{}"})])
        self.ignored_receipt(job)
        for _ in range(3):
            self.tick()
        self.assertEqual(self.round()["state"], "WAITING_JOBS")
        adds = []
        for _ in range(3):
            loop = self.loop()
            original = loop._git
            def counting(*args, original=original, **kwargs):
                if args[:2] == ("add", "-f"):
                    adds.append(args)
                return original(*args, **kwargs)
            with patch.object(loop, "_git", side_effect=counting):
                loop.tick()
        self.assertEqual(len(adds), 1)
        self.assertEqual(self.git("log", "--format=%s").splitlines().count("round 1: results"), 1)

    def test_slug_and_discovery_prefix(self):
        loop = self.loop()
        for identity in ("UPPER.Name", "a" * 101, "x", "A___B"):
            loop.config["campaign_id"] = identity
            slug = loop._job_prefix(1).removesuffix("-r1-")
            self.assertRegex(slug, r"^[a-z0-9-]{1,20}$")
            self.assertEqual(loop._job_prefix(1), loop._job_prefix(1))
        self.launch()
        task = self.task("task", {f".nerelan-remote/outbox/{job}/job.json": "{}"
                         for job in ("campaign-r1-ok", "other-r1-job", "campaign-r2-job")})
        self.complete([task])
        self.tick()
        self.tick()
        self.assertEqual(self.round()["jobs"], ["campaign-r1-ok"])
        self.assertIn("campaign-r1-", self.round()["objective"])

    def test_stale_receipts_resolve_and_next_objective(self):
        for state in ("RUNNING", "REJECTED", "RESULT_COLLECTED"):
            with self.subTest(state=state):
                record = {"imports": {}, "request_commit": self.base}
                self.assertFalse(self.loop()._bound_receipt(record, "campaign-r1-none", {"state": state}))
                self.assertEqual(record["imports"]["campaign-r1-none"]["error"], "STALE_RECEIPT")
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
        write_json(self.broker / "campaign-r1-job/receipt.json", {"state": "RUNNING"})
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.round()["imports"]["campaign-r1-job"]["error"], "STALE_RECEIPT")
        self.assertFalse((self.repo / "results").exists())
        objective = self.loop()._objective(2, False)
        self.assertIn("campaign-r1-job", objective)
        self.assertIn("new job ids", objective)

    def test_objective_states_a_request_the_broker_accepts(self):
        # Short test 2026-10-21: without the schema, agents refused to invent one and requested nothing.
        from reverse_agent.platform_v1.remote_jobs import RemoteJobBroker, REQUEST_FIELDS
        objective = self.loop()._objective(1, False)
        example = json.loads(objective.split("for example ", 1)[1].split("}", 1)[0] + "}")
        self.assertEqual(sorted(example), sorted(REQUEST_FIELDS))
        directory = self.repo / ".nerelan-remote/outbox" / example["job_id"]
        directory.mkdir(parents=True)
        (directory / "run.py").write_text("print('ok')\n", encoding="utf-8")
        write_json(directory / "job.json", example)
        broker = RemoteJobBroker.__new__(RemoteJobBroker)
        broker.profile = SimpleNamespace(max_wall_seconds=900, max_upload_bytes=10000)
        request, _ = broker._request(directory / "job.json")
        self.assertTrue(request["job_id"].startswith(self.loop()._job_prefix(1)))

    def test_committed_digest_matches_broker_and_ignores_worktree(self):
        from reverse_agent.platform_v1.remote_jobs import RemoteJobBroker
        job = "campaign-r1-job"
        directory = self.repo / ".nerelan-remote/outbox" / job
        directory.mkdir(parents=True)
        request = self.request(job)
        request["files"] = ["input.bin"]
        write_json(directory / "job.json", request)
        (directory / "input.bin").write_bytes(b"original\x00\xff")
        self.git("add", ".nerelan-remote")
        self.git("commit", "-m", "request")
        record = {"request_commit": self.git("rev-parse", "HEAD"), "imports": {}}
        broker = RemoteJobBroker.__new__(RemoteJobBroker)
        broker.profile = SimpleNamespace(max_wall_seconds=100, max_upload_bytes=10000)
        _, digest = broker._request(directory / "job.json")
        self.assertEqual(self.loop()._committed_digest(record, job), digest)
        for name in ("input.bin", "job.json"):
            original = (directory / name).read_bytes()
            (directory / name).write_bytes(original + b" ")
            self.assertEqual(self.loop()._committed_digest(record, job), digest)
            self.git("add", ".nerelan-remote")
            self.git("commit", "-m", "changed " + name)
            changed = {"request_commit": self.git("rev-parse", "HEAD"), "imports": {}}
            self.assertFalse(self.loop()._bound_receipt(changed, job, {"request_digest": digest}))

    def test_mixed_stale_and_pending_survives_restart(self):
        self.launch()
        stale, pending = "campaign-r1-stale", "campaign-r1-pending"
        self.complete([self.task("task", {f".nerelan-remote/outbox/{job}/job.json": "{}"
                                         for job in (stale, pending)})])
        write_json(self.broker / stale / "receipt.json", {"state": "RUNNING", "request_digest": "old"})
        write_json(self.broker / pending / "receipt.json", {"state": "RUNNING", "request_digest": self.digest(pending)})
        for _ in range(4):
            self.tick()
        record = self.round()
        boundary = record["request_commit"]
        self.assertEqual(record["state"], "WAITING_JOBS")
        self.assertEqual(record["imports"][stale]["error"], "STALE_RECEIPT")
        self.tick()
        self.assertEqual(self.round()["request_commit"], boundary)
        self.assertEqual(self.round()["state"], "WAITING_JOBS")
        self.receipt(pending)
        self.tick()
        self.assertTrue(self.round()["imports"][pending]["imported"])
        self.assertFalse((self.repo / "results" / stale).exists())

    def test_resumed_snapshot_requires_bound_receipt(self):
        self.launch()
        job = "campaign-r1-job"
        self.complete([self.task("task", {f".nerelan-remote/outbox/{job}/job.json": "{}"})])
        self.receipt(job)
        for _ in range(3):
            self.tick()
        loop = self.loop()
        save = loop._save
        def crash(record, path):
            save(record, path)
            if record.get("imports", {}).get(job, {}).get("files"):
                raise RuntimeError("frozen")
        with patch.object(loop, "_save", side_effect=crash):
            with self.assertRaisesRegex(RuntimeError, "frozen"):
                loop.tick()
        snapshot = loop.root / "rounds/1-imports" / job / "receipt.json"
        write_json(snapshot, {"state": "REJECTED", "request_digest": "old"})
        record = self.round()
        record["imports"][job]["files"]["receipt.json"] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        write_json(loop.root / "rounds/1.json", record)
        self.tick()
        self.assertEqual(self.round()["imports"][job]["error"], "STALE_RECEIPT")
        self.assertFalse((self.repo / "results" / job).exists())

    def test_malformed_committed_requests_fail_closed(self):
        job = "campaign-r1-job"
        directory = self.repo / ".nerelan-remote/outbox" / job
        directory.mkdir(parents=True)
        for raw in (b"{", b"[]", b'{}', b'{"files":["missing"]}'):
            (directory / "job.json").write_bytes(raw)
            self.git("add", ".nerelan-remote")
            self.git("commit", "-m", "malformed")
            record = {"request_commit": self.git("rev-parse", "HEAD"), "imports": {}}
            self.assertFalse(self.loop()._bound_receipt(record, job, {"request_digest": "old"}))
            self.assertEqual(record["imports"][job]["error"], "STALE_RECEIPT")

    def test_receipt_changes_before_import(self):
        self.launch()
        job = "campaign-r1-job"
        self.complete([self.task("task", {f".nerelan-remote/outbox/{job}/job.json": "{}"})])
        self.receipt(job)
        for _ in range(3):
            self.tick()
        loop = self.loop()
        original = loop._import
        def changed(*args):
            write_json(self.broker / job / "receipt.json", {"state": "REJECTED", "request_digest": "old"})
            return original(*args)
        with patch.object(loop, "_import", side_effect=changed):
            loop.tick()
        self.assertEqual(self.round()["imports"][job]["error"], "STALE_RECEIPT")
        self.assertFalse((self.repo / "results").exists())

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
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-reject/job.json": "{}"})])
        write_json(self.broker / "campaign-r1-reject/receipt.json", {"state": "REJECTED", "request_digest": self.digest("campaign-r1-reject")})
        for _ in range(4):
            self.tick()
        self.assertTrue(self.round()["imports"]["campaign-r1-reject"]["imported"])
        self.assertTrue((self.repo / "results/campaign-r1-reject/receipt.json").exists())

    def test_failed_execution_waits_for_collection(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-failed/job.json": "{}"})])
        write_json(self.broker / "campaign-r1-failed/receipt.json", {"state": "FAILED", "request_digest": self.digest("campaign-r1-failed")})
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "WAITING_JOBS")

    def test_transient_collection_error_then_success(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
        # The broker marks the receipt LOST/TIMED_OUT/FAILED before collecting;
        # the loop must not import early, and must retry once collected.
        write_json(self.broker / "campaign-r1-job/receipt.json", {"state": "TIMED_OUT", "request_digest": self.digest("campaign-r1-job")})
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "WAITING_JOBS")
        self.assertNotIn("campaign-r1-job", self.round()["imports"])
        self.receipt("campaign-r1-job")
        self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertTrue(self.round()["imports"]["campaign-r1-job"]["imported"])

    def test_import_rechecks_manifest_exists(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
        self.receipt("campaign-r1-job")
        # Simulate the broker receipt claiming collection while no manifest exists.
        write_json(self.broker / "campaign-r1-job/receipt.json", {"state": "RESULT_COLLECTED", "request_digest": self.digest("campaign-r1-job")})
        (self.broker / "campaign-r1-job/manifest.json").unlink()
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.round()["imports"]["campaign-r1-job"]["error"], "collection manifest missing")

    def test_no_broker_records_and_continues(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
        self.broker = None
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.round()["imports"]["campaign-r1-job"]["error"], "NO_BROKER")
        self.tick()
        self.assertEqual(self.round()["state"], "DONE")

    def test_self_heal_crash_left_import_temporary(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
        self.receipt("campaign-r1-job")
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
        self.assertIn("error", self.round()["imports"]["campaign-r1-job"])
        leftover = self.repo / "results/campaign-r1-job/outputs/.value.txt.nerelan-import"
        self.assertTrue(leftover.exists())
        self.assertIn("results", self.git("status", "--porcelain"))
        # A fresh tick that re-enters a checkout must self-heal the loop's own leftover.
        loop = self.loop()
        loop._checkout({"branch": "main"})
        self.assertFalse(leftover.exists())
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_self_heal_leaves_unrelated_work_paused(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
        self.receipt("campaign-r1-job")
        for _ in range(6):
            self.tick()
        self.assertEqual(self.round()["state"], "DONE")
        (self.repo / "unrelated").write_text("not the loop's")
        loop = self.loop()
        with self.assertRaisesRegex(RuntimeError, "existing work"):
            loop._checkout({"branch": "main"})
        self.assertEqual((self.repo / "unrelated").read_text(), "not the loop's")

    def test_self_heal_preserves_modified_destination_and_pauses(self):
        job = self.crash_import_leftovers()
        dest = self.repo / f"results/{job}/receipt.json"
        dest.write_bytes(b"edited evidence")
        campaign = self.state()
        with self.assertRaisesRegex(RuntimeError, "import recovery paused"):
            self.loop()._checkout(campaign)
        self.assertEqual(dest.read_bytes(), b"edited evidence")
        state = self.state()
        self.assertEqual(state["state"], "PAUSED_FAILING")
        rel = dest.relative_to(self.repo).as_posix()
        self.assertIn(rel, state["history"][-1]["detail"])

    def test_self_heal_preserves_modified_temporary_and_pauses(self):
        job = self.crash_import_leftovers()
        temporary = self.repo / f"results/{job}/outputs/.value.txt.nerelan-import"
        untouched = self.repo / f"results/{job}/manifest.json"
        temporary.write_bytes(b"edited temporary")
        campaign = self.state()
        with self.assertRaisesRegex(RuntimeError, "import recovery paused"):
            self.loop()._checkout(campaign)
        rel = temporary.relative_to(self.repo).as_posix()
        self.assertEqual(temporary.read_bytes(), b"edited temporary")
        self.assertTrue(untouched.exists())
        self.assertIn(rel, self.state()["history"][-1]["detail"])

    def test_self_heal_preserves_modified_staged_destination(self):
        job = self.crash_import_leftovers()
        dest = self.repo / f"results/{job}/receipt.json"
        dest.write_bytes(b"staged evidence")
        rel = dest.relative_to(self.repo).as_posix()
        self.git("add", "--", rel)
        with self.assertRaisesRegex(RuntimeError, "import recovery paused"):
            self.loop()._checkout(self.state())
        self.assertEqual(dest.read_bytes(), b"staged evidence")
        self.assertIn(rel, self.git("diff", "--cached", "--name-only").splitlines())
        staged = subprocess.run(["git", "-C", str(self.repo), "show", ":" + rel],
                                capture_output=True, check=True)
        self.assertEqual(staged.stdout, b"staged evidence")

    def test_self_heal_lists_every_modified_path_and_pauses(self):
        job = self.crash_import_leftovers()
        destination = self.repo / f"results/{job}/receipt.json"
        temporary = self.repo / f"results/{job}/outputs/.value.txt.nerelan-import"
        destination.write_bytes(b"edited destination")
        temporary.write_bytes(b"edited temporary")
        with self.assertRaises(RuntimeError) as caught:
            self.loop()._checkout(self.state())
        for path in (destination, temporary):
            rel = path.relative_to(self.repo).as_posix()
            self.assertIn(rel, str(caught.exception))
            self.assertIn(rel, self.state()["history"][-1]["detail"])
        self.assertEqual(destination.read_bytes(), b"edited destination")
        self.assertEqual(temporary.read_bytes(), b"edited temporary")
        self.assertEqual(self.state()["state"], "PAUSED_FAILING")

    def test_self_heal_recovers_unchanged_destination_and_temporary(self):
        job = self.crash_import_leftovers()
        leftovers = [
            self.repo / f"results/{job}/receipt.json",
            self.repo / f"results/{job}/manifest.json",
            self.repo / f"results/{job}/outputs/.value.txt.nerelan-import",
        ]
        for path in leftovers:
            self.assertTrue(path.exists(), path)
        campaign = self.state()
        self.loop()._checkout(campaign)
        for path in leftovers:
            self.assertFalse(path.exists(), path)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.state()["state"], "RUNNING")

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
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-lost/job.json": "{}"})])
        write_json(self.broker / "campaign-r1-lost/receipt.json", {"state": "LOST", "request_digest": self.digest("campaign-r1-lost")})
        for _ in range(4):
            self.tick()
        self.assertEqual(self.round()["state"], "WAITING_JOBS")
        self.assertEqual(self.round()["job_states"], {"campaign-r1-lost": "LOST"})
        self.now += self.config["max_job_wait_hours"] * 3600
        self.tick()
        self.assertEqual(self.round()["state"], "RESULTS_IMPORTED")
        self.assertEqual(self.round()["imports"]["campaign-r1-lost"]["error"], "JOB_WAIT_EXPIRED")

    def test_deadline_preserves_collected_results(self):
        self.launch()
        self.complete([self.task("task", {
            ".nerelan-remote/outbox/campaign-r1-a/job.json": "{}",
            ".nerelan-remote/outbox/campaign-r1-b/job.json": "{}"})])
        write_json(self.broker / "campaign-r1-b/receipt.json", {"state": "RUNNING", "request_digest": self.digest("campaign-r1-b")})
        for _ in range(4):
            self.tick()
        record = self.round()
        self.assertEqual(record["state"], "WAITING_JOBS")
        self.assertEqual(record["job_states"], {"campaign-r1-a": "NO_RECEIPT", "campaign-r1-b": "RUNNING"})
        self.receipt("campaign-r1-a")
        self.now = record["waiting_since"] + self.config["max_job_wait_hours"] * 3600
        self.assertLess(self.now - self.state()["started_at"], self.config["max_hours"] * 3600)
        self.tick()
        record = self.round()
        self.assertEqual(record["state"], "RESULTS_IMPORTED")
        self.assertTrue(record["imports"]["campaign-r1-a"]["imported"])
        self.assertNotIn("error", record["imports"]["campaign-r1-a"])
        self.assertEqual((self.repo / "results/campaign-r1-a/outputs/value.txt").read_bytes(), b"measurement\n")
        self.assertEqual(record["imports"]["campaign-r1-b"]["error"], "JOB_WAIT_EXPIRED")
        self.assertFalse((self.repo / "results/campaign-r1-b").exists())
        committed = self.git("show", "--pretty=format:", "--name-only", "HEAD").split()
        self.assertIn("results/campaign-r1-a/outputs/value.txt", committed)
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
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
        self.receipt("campaign-r1-job")
        manifest = self.broker / "campaign-r1-job/manifest.json"
        write_json(manifest, {"files": [{"path": "../../escape", "size": 0, "sha256": "0" * 64}]})
        for _ in range(4):
            self.tick()
        self.assertIn("error", self.round()["imports"]["campaign-r1-job"])
        self.assertFalse((self.repo / "results").exists())

    def test_existing_results_preserved(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}",
                                           "results/campaign-r1-job/precious": "preserve me"})])
        self.receipt("campaign-r1-job")
        for _ in range(4):
            self.tick()
        self.assertIn("already exists", self.round()["imports"]["campaign-r1-job"]["error"])
        self.assertEqual((self.repo / "results/campaign-r1-job/precious").read_text(), "preserve me")

    def test_crash_during_results_copy(self):
        self.launch()
        self.complete([self.task("task", {".nerelan-remote/outbox/campaign-r1-job/job.json": "{}"})])
        for _ in range(3):
            self.tick()
        self.receipt("campaign-r1-job")
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
        with patch.object(builtins, "print") as output:
            self.assertEqual(main(["status", "--campaign", str(self.file), "--json"]), 0)
        self.assertIn("NOT_STARTED", output.call_args.args[0])
        self.assertFalse((self.root / "state").exists())
        with patch.dict(os.environ, {}, clear=True):
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
        with patch.dict(os.environ, {"REVERSE_AGENT_REPO_DIR": str(self.repo)}), patch.object(
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
        with patch.dict(os.environ, {}, clear=True), patch.multiple(trusted_host,
                ThreadingHTTPServer=Server, configured_broker=lambda: broker,
                _model_control_handler_factory=lambda *a, **kw: None,
                _task_handler_factory=lambda *a, **kw: None), patch.object(credential_relay, "run_credential_relay_server", Server), patch.object(research_loop, "configured_loop", return_value=loop) as factory:
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
