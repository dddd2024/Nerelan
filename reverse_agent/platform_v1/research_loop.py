"""Durable, host-side research campaign orchestration (no direct model calls)."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import threading
import time

from .repository_workspace import resolve_repository_workspace
from .remote_jobs import _atomic_json, _relative
from .run_store import TaskStoreError

ENV_CAMPAIGN = "REVERSE_AGENT_RESEARCH_CAMPAIGN"
LOG = logging.getLogger(__name__)
FINAL = {"STOPPED", "COMPLETED", "EXPIRED", "PAUSED_FAILING"}
ROUND_FINAL = {"DONE", "FAILED", "INTERRUPTED"}
COMMIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Nerelan research",
    "GIT_COMMITTER_NAME": "Nerelan research",
    "GIT_AUTHOR_EMAIL": "research@nerelan.invalid",
    "GIT_COMMITTER_EMAIL": "research@nerelan.invalid",
}


def load_campaign(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,100}", config["campaign_id"]):
        raise ValueError("invalid campaign_id")
    for name, default in (("max_rounds", 12), ("max_hours", 72),
                          ("max_consecutive_failed_rounds", 2), ("poll_seconds", 30),
                          ("max_job_wait_hours", 24)):
        value = config.setdefault(name, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value < float("inf"):
            raise ValueError(name + " must be positive and finite")
        if name in {"max_rounds", "max_consecutive_failed_rounds"} and type(value) is not int:
            raise ValueError(name + " must be an integer")
    for name in ("objective", "repository", "state_dir", "executor_kind", "binding_ref"):
        if not isinstance(config.get(name), str) or not config[name].strip():
            raise ValueError(name + " required")
    if type(config.get("push", False)) is not bool:
        raise ValueError("push must be boolean")
    return config


class ResearchLoop:
    """One tick advances one durable phase; external work is always reconciled first.

    Only one host may own a campaign. The OS lock also excludes manual/test ticks
    from a second instance; it is released automatically after process death.
    """

    def __init__(self, campaign, *, goal_service, planner, broker_root=None,
                 repo_dir=None, clock=time.time):
        self.config = load_campaign(campaign)
        self.repo = resolve_repository_workspace(
            self.config["repository"], source_dir=repo_dir).repo_dir
        self.goals, self.planner, self.clock = goal_service, planner, clock
        self.broker_root = Path(broker_root) if broker_root is not None else None
        self.root = Path(self.config["state_dir"]) / self.config["campaign_id"]
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "state.json"
        self._stop = threading.Event()
        self._thread = None
        self._mutex = threading.Lock()

    def _git(self, *args, check=True, env=None):
        result = subprocess.run(["git", "-C", str(self.repo), *args],
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                check=False, stdin=subprocess.DEVNULL, timeout=120, env=env)
        if check and result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result

    def _commit_env(self, extra=None):
        env = dict(os.environ, **COMMIT_IDENTITY, GIT_CONFIG_NOSYSTEM="1",
                   GIT_CONFIG_GLOBAL=os.devnull)
        if extra:
            env.update(extra)
        return env

    def _save(self, record, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_json(path, record)

    def _event(self, record, state, detail, path):
        record["state"] = state
        record.setdefault("history", []).append(
            {"state": state, "at": self.clock(), "detail": detail})
        self._save(record, path)

    def _record_stopped_round(self, campaign, stop):
        # The goal itself is left to its window, never cancelled here; record
        # that the bound was hit while it was still in flight.
        path = self.root / "rounds" / f"{campaign['round']}.json"
        if not path.exists():
            return
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["state"] in ROUND_FINAL:
            return
        goal_id = record.get("goal_id")
        running = goal_id and self.goals.detail(goal_id)["status"] in {
            "DRAFT", "PLANNED", "APPROVED", "RUNNING"}
        detail = f"campaign {stop.lower()} while goal still running" if running else f"campaign {stop.lower()}"
        record.setdefault("history", []).append(
            {"state": record["state"], "at": self.clock(), "detail": detail})
        self._save(record, path)

    def start(self):
        if self._thread is None:
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="research-loop", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _run(self):
        from .remote_jobs import _BrokerLock
        try:
            # Keep ownership while asynchronous planning/execution is in flight,
            # so a second host cannot invoke its own planner for the same Goal.
            with _BrokerLock(self.root / "loop.lock"):
                while not self._stop.is_set():
                    try:
                        with self._mutex:
                            self._tick()
                    except Exception:
                        LOG.exception("research campaign tick failed")
                    self._stop.wait(self.config["poll_seconds"])
        except OSError:
            LOG.exception("research campaign already owned by another host")

    def tick(self):
        # Reuse the broker's portable OS lock, not its job submission machinery.
        from .remote_jobs import _BrokerLock
        with self._mutex:
            with _BrokerLock(self.root / "loop.lock"):
                self._tick()

    def _tick(self):
        if self._stop.is_set():
            return
        if self.state_path.exists():
            campaign = json.loads(self.state_path.read_text(encoding="utf-8"))
            if campaign["repository"] != self.config["repository"]:
                raise ValueError("persisted campaign repository mismatch")
        else:
            branch = self._git("symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
            branch = branch.stdout.strip().removeprefix("origin/")
            if not branch:
                # Offline repositories need a known local default, never the task branch.
                branch = next((b for b in ("main", "master") if self._git(
                    "show-ref", "--verify", "refs/heads/" + b, check=False).returncode == 0), "")
            if not branch:
                raise ValueError("research default branch unavailable")
            campaign = {"campaign_id": self.config["campaign_id"], "repository": self.config["repository"],
                        "started_at": self.clock(), "round": 1, "failed_rounds": 0, "branch": branch,
                        "history": []}
            self._event(campaign, "RUNNING", "campaign started", self.state_path)
        if campaign["state"] in FINAL:
            return
        stop = ("STOPPED" if (self.root / "STOP").exists() else
                "EXPIRED" if self.clock() - campaign["started_at"] >= self.config["max_hours"] * 3600 else "")
        if stop:
            self._record_stopped_round(campaign, stop)
            self._event(campaign, stop, "campaign bound reached", self.state_path)
            return
        n = campaign["round"]
        path = self.root / "rounds" / f"{n}.json"
        if not path.exists():
            if n > self.config["max_rounds"] or self._git(
                    "cat-file", "-e", campaign["branch"] + ":CAMPAIGN_DONE.md", check=False).returncode == 0:
                self._event(campaign, "COMPLETED", "round limit or CAMPAIGN_DONE.md", self.state_path)
                return
            record = {"number": n, "history": [], "integrations": {}, "imports": {}, "jobs": []}
            previous = self.root / "rounds" / f"{n - 1}.json"
            interrupted = previous.exists() and json.loads(previous.read_text(encoding="utf-8"))["state"] == "INTERRUPTED"
            record["objective"] = self._objective(n, interrupted)
            self._event(record, "CREATING", "round reserved", path)
        else:
            record = json.loads(path.read_text(encoding="utf-8"))
        state = record["state"]
        if state in ROUND_FINAL:
            # Campaign update and round completion are separate atomic files.
            failed = record.get("goal_failed", False) or not any(
                v.get("integrated") for v in record["integrations"].values())
            campaign["failed_rounds"] = campaign["failed_rounds"] + 1 if failed else 0
            campaign["round"] = n + 1
            self._event(campaign, "PAUSED_FAILING" if campaign["failed_rounds"] >=
                        self.config["max_consecutive_failed_rounds"] else "RUNNING",
                        f"round {n} {state}", self.state_path)
            return
        if state == "PLANNING":
            # Launch can commit in SQLite just before the phase file is replaced.
            # Its recovery must not require the old window still to be active.
            goal = self.goals.detail(record["goal_id"])
            if goal["status"] not in {"DRAFT", "PLANNED", "APPROVED"}:
                if campaign["state"] == "PAUSED_NO_WINDOW":
                    self._event(campaign, "RUNNING", "existing goal already launched", self.state_path)
                self._event(record, "LAUNCHED", "recovered existing goal launch", path)
                return
        window = self.goals.control_store.active_window()
        if window is not None and self.config["repository"] not in window.repositories:
            window = None
        if state in {"CREATING", "PLANNING"} and window is None:
            if campaign["state"] != "PAUSED_NO_WINDOW":
                self._event(campaign, "PAUSED_NO_WINDOW", "no active research window", self.state_path)
            return
        if campaign["state"] == "PAUSED_NO_WINDOW" and window is not None:
            self._event(campaign, "RUNNING", "active window available", self.state_path)
        if state == "CREATING":
            goal = self.goals.create({**{k: self.config[k] for k in
                ("repository", "executor_kind", "binding_ref")}, "objective": record["objective"],
                "title": f"{self.config['campaign_id']} round {n}", "orchestration_mode": "agent_team",
                "idempotency_key": f"{self.config['campaign_id']}-round-{n}"})
            record["goal_id"] = goal.id
            self._event(record, "PLANNING", "goal created or recovered", path)
        elif state == "PLANNING":
            goal = self.goals.detail(record["goal_id"])
            if goal["status"] == "DRAFT":
                status = self.planner.status(goal["id"])
                if status["status"] == "FAILED":
                    record["goal_failed"] = True
                    self._event(record, "FAILED", status.get("error", "planning failed"), path)
                elif status["status"] != "RUNNING":
                    self.planner.start(goal["id"], expected_revision=goal["revision"])
                return
            if goal["status"] == "PLANNED":
                self.goals.approve(goal["id"], expected_revision=goal["revision"])
                goal = self.goals.detail(goal["id"])
            if goal["status"] == "APPROVED":
                self.goals.launch(goal["id"], expected_revision=goal["revision"], window_id=window.id)
            self._event(record, "LAUNCHED", "goal launch reconciled", path)
        elif state == "LAUNCHED":
            goal = self.goals.detail(record["goal_id"])
            tasks = goal.get("task_links", [])
            terminal = {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "FAILED", "BLOCKED", "CANCELLED", "INTERRUPTED"}
            # GoalService reports BLOCKED as soon as one task fails. Let any
            # already-running siblings finish before freezing their commits.
            if any(t["status"] in {"PREPARING_WORKSPACE", "RUNNING", "RUNNING_FIXTURE", "VALIDATING"} for t in tasks):
                return
            goal_terminal = goal["status"] in {"COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "INTERRUPTED"}
            if not goal_terminal and (not tasks or not all(t["status"] in terminal for t in tasks)):
                return
            record["tasks"] = [dict(t) for t in tasks]
            for task in record["tasks"]:
                if task["status"] in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}:
                    try:
                        task["commit_sha"] = self._task_commit(task)
                    except (OSError, ValueError, TaskStoreError, subprocess.TimeoutExpired) as exc:
                        task["commit_sha"] = ""
                        task["commit_error"] = str(exc)
            record["interrupted"] = goal["status"] == "INTERRUPTED" or any(t["status"] == "INTERRUPTED" for t in tasks)
            record["goal_failed"] = goal["status"] != "COMPLETED"
            self._event(record, "GOAL_DONE", "terminal task evidence captured", path)
        elif state == "GOAL_DONE":
            self._integrate(campaign, record, path)
        elif state == "INTEGRATED":
            self._event(record, "WAITING_JOBS", "waiting for broker collections", path)
        elif state == "WAITING_JOBS":
            if not self.broker_root:
                if record["jobs"]:
                    for job in record["jobs"]:
                        if job not in record["imports"]:
                            record["imports"][job] = {"error": "NO_BROKER"}
                self._save(record, path)
                self._import(campaign, record, path)
                return
            record.setdefault("waiting_since", self.clock())
            expired = self.clock() - record["waiting_since"] >= self.config["max_job_wait_hours"] * 3600
            observed = {}
            ready = {}
            for job in record["jobs"]:
                source = self.broker_root / job
                if not (source / "receipt.json").exists():
                    observed[job] = "NO_RECEIPT"
                    ready[job] = False
                    continue
                receipt = json.loads((source / "receipt.json").read_text(encoding="utf-8"))
                observed[job] = receipt["state"]
                # Ready means the result was actually collected, or the job was
                # rejected with nothing to collect. LOST/TIMED_OUT/FAILED leave
                # collection pending until the broker actually collects a result.
                ready[job] = (receipt["state"] in {"RESULT_COLLECTED", "REJECTED"} or
                              receipt["state"] == "FAILED" and (source / "manifest.json").exists())
            if observed != record.get("job_states"):
                record["job_states"] = observed
                self._event(record, "WAITING_JOBS", json.dumps(observed, sort_keys=True), path)
            if expired:
                for job in record["jobs"]:
                    if not ready[job] and job not in record["imports"]:
                        record["imports"][job] = {"error": "JOB_WAIT_EXPIRED"}
                self._save(record, path)
                self._import(campaign, record, path)
            elif all(ready.values()):
                self._import(campaign, record, path)
        elif state == "RESULTS_IMPORTED":
            if self.config.get("push") and not record.get("push_attempted"):
                record["push_attempted"] = True
                record["push"] = {"detail": "attempt reserved; outcome unknown until recorded"}
                self._save(record, path)  # At most one attempt, even after a crash.
                try:
                    result = self._git("push", "origin", campaign["branch"], check=False)
                    record["push"] = {"returncode": result.returncode, "detail": result.stderr[-2000:]}
                except (OSError, subprocess.TimeoutExpired) as exc:
                    record["push"] = {"error": str(exc)}
            outcome = ("INTERRUPTED" if record.get("interrupted") else
                       "FAILED" if record.get("goal_failed") else "DONE")
            self._event(record, outcome, "round finished", path)

    def _objective(self, n, interrupted):
        return (f"{self.config['objective']}\n\nResearch round {n}.\n"
                + ("The previous round was INTERRUPTED; nothing was automatically replayed.\n" if interrupted else "")
                + "Read RESEARCH_LOG.md, results/ and earlier rounds in the repository. "
                "Append a section for this round to RESEARCH_LOG.md: hypothesis, what was run, "
                "what the results show, what's next; state uncertainty. Request remote experiments "
                f"only through .nerelan-remote/outbox/<job_id>/job.json; prefix job ids r{n}-. "
                "All server research directories, experiment files and raw data MUST live under ~/wjc; "
                "write outputs, temporary files and caches inside the broker job directory. "
                "Write CAMPAIGN_DONE.md with justification when the objective is met or cannot be met. "
                "Successful CLI execution is not functional or scientific acceptance.")

    def _checkout(self, campaign, record=None):
        self._self_heal()
        if self._git("status", "--porcelain").stdout.strip():
            raise RuntimeError("research repository has existing work; integration paused")
        self._git("switch", campaign["branch"])

    def _self_heal(self):
        # A crash can leave the loop's own uncommitted import temporaries or a
        # partially written results/<job_id>/ behind, which would otherwise block
        # every future checkout. Remove only files the round records prove the
        # loop itself created, and only when they are not committed.
        owned = {}
        for round_path in sorted(self.root.glob("rounds/*.json")):
            try:
                record = json.loads(round_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for job, entry in record.get("imports", {}).items():
                for name in entry.get("files", {}):
                    owned.setdefault(job, set()).add(name)
        for job, names in owned.items():
            for name in names:
                dest = self.repo / "results" / job / name
                for candidate in (dest, dest.with_name("." + dest.name + ".nerelan-import")):
                    if not candidate.exists() and not candidate.is_symlink():
                        continue
                    rel = candidate.relative_to(self.repo).as_posix()
                    if self._git("cat-file", "-e", "HEAD:" + rel, check=False).returncode == 0:
                        continue
                    if self._git("ls-files", "--error-unmatch", "--", rel, check=False).returncode == 0:
                        self._git("reset", "-q", "--", rel)
                    candidate.unlink()

    def _task_commit(self, link):
        if "commit_sha" in link:
            return link["commit_sha"]
        sha = (link.get("publication") or {}).get("commit_sha", "")
        if sha:
            return sha
        # Agent-team handoffs retain accepted trees as commits without pushing.
        from .artifact_handoff import _load_evidence, ACCEPTED_CATEGORY
        task = self.goals.store.get_task(link["task_id"])
        accepted = _load_evidence(task, ACCEPTED_CATEGORY, task.execution_id)
        if accepted:
            return accepted["commit"]
        observation = self.goals.store.get_latest_durable_run_observation(task.id)
        if observation is not None:
            run = self.goals.store._get_durable_run(observation.run_id)
            if (run.worktree_path and run.execution_id == task.execution_id
                    and run.accepted_checkpoint == "POST_VALIDATION"):
                return self._retain_task_snapshot(task, run)
        return ""

    def _retain_task_snapshot(self, task, run):
        # Native executors deliberately do not commit. Reuse the established
        # temporary-index snapshot, keeping their real HEAD/index untouched.
        from reverse_agent.executor_neutral.core import _snapshot_workspace
        from .functional_validation import git_output
        root = resolve_repository_workspace(task.repository, source_dir=run.worktree_path).repo_dir
        common = ("rev-parse", "--path-format=absolute", "--git-common-dir")
        if git_output(root, *common) != self._git(*common).stdout.strip():
            raise ValueError("task worktree uses a different object store")
        head = git_output(root, "rev-parse", "HEAD")
        if git_output(root, "merge-base", run.repository_base_sha, head) != run.repository_base_sha:
            raise ValueError("task snapshot is outside its approved base")
        _, tree, _, hygiene = _snapshot_workspace(root, run.repository_base_sha)
        if hygiene["exit_code"] != 0:
            raise ValueError("task snapshot failed git diff --check")
        if git_output(root, "rev-parse", head + "^{tree}") == tree:
            return head
        if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", value)
               for value in (task.id, task.execution_id)):
            raise ValueError("invalid task snapshot identity")
        # Content-addressed and deterministic across a crash before journaling.
        env = {key: value for key, value in os.environ.items() if key in {
            "PATH", "Path", "SystemRoot", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR"}}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_AUTHOR_NAME="Nerelan research", GIT_COMMITTER_NAME="Nerelan research",
                   GIT_AUTHOR_EMAIL="research@nerelan.invalid", GIT_COMMITTER_EMAIL="research@nerelan.invalid",
                   GIT_AUTHOR_DATE="2000-01-01T00:00:00+00:00", GIT_COMMITTER_DATE="2000-01-01T00:00:00+00:00")
        sha = self._git("-c", "commit.gpgSign=false",
                        "commit-tree", tree, "-p", head, "-m",
                        f"Research task {task.id}: {task.execution_id}", env=env).stdout.strip()
        campaign_ref = hashlib.sha256(self.config["campaign_id"].encode()).hexdigest()
        ref = f"refs/nerelan/research/{campaign_ref}/{task.id}/{task.execution_id}"
        existing = self._git("rev-parse", "--verify", ref, check=False).stdout.strip()
        if existing and existing != sha:
            raise ValueError("task snapshot changed after retention")
        if not existing:
            self._git("update-ref", ref, sha, "0" * 40)
        return sha

    def _integrate(self, campaign, record, path):
        if record.get("merging"):
            task_id = record["merging"]
            merge_head = self._git("rev-parse", "--verify", "MERGE_HEAD", check=False).stdout.strip()
            if (merge_head == record.get("merge_sha") and
                    self._git("rev-parse", "HEAD").stdout.strip() == record.get("base_" + task_id) and
                    self._git("branch", "--show-current").stdout.strip() == campaign["branch"]):
                self._git("merge", "--abort")
                record["integrations"][record.pop("merging")] = {"error": "interrupted conflicting merge"}
                self._save(record, path)
        self._checkout(campaign, record)
        for task in record.get("tasks", []):
            if self._stop.is_set():
                return
            task_id = task["task_id"]
            if task_id in record["integrations"] or task["status"] not in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}:
                continue
            sha = self._task_commit(task)
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                record["integrations"][task_id] = {"error": task.get("commit_error", "completed task has no commit evidence")}
                self._save(record, path)
                continue
            # Persist the boundary before merging, so a crash can rediscover added jobs.
            key = "base_" + task_id
            record.setdefault(key, self._git("rev-parse", "HEAD").stdout.strip())
            record["merging"] = task_id
            record["merge_sha"] = sha
            self._save(record, path)
            ancestor = self._git("merge-base", "--is-ancestor", sha, "HEAD", check=False).returncode == 0
            result = None if ancestor else self._git("merge", "--no-ff", "-m",
                f"round {record['number']}: {task_id}", sha, check=False, env=self._commit_env())
            if result is not None and result.returncode:
                if self._git("rev-parse", "--verify", "MERGE_HEAD", check=False).returncode == 0:
                    self._git("merge", "--abort")
                record["integrations"][task_id] = {"error": result.stderr[-2000:] or result.stdout[-2000:]}
            else:
                changed_paths = self._git("diff", "--name-only", record[key], "HEAD").stdout.splitlines()
                if "RESEARCH_LOG.md" in changed_paths:
                    record["research_log_updated"] = True
                changed = self._git("diff", "--diff-filter=A", "--name-only", record[key], "HEAD").stdout.splitlines()
                for name in changed:
                    parts = PurePosixPath(name).parts
                    if len(parts) == 4 and parts[:2] == (".nerelan-remote", "outbox") and parts[3] == "job.json":
                        if parts[2].startswith(f"r{record['number']}-") and re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", parts[2]):
                            record["jobs"] = sorted(set(record["jobs"]) | {parts[2]})
                record["integrations"][task_id] = {"integrated": record[key] != self._git("rev-parse", "HEAD").stdout.strip(), "sha": sha}
            record.pop("merging", None)
            record.pop("merge_sha", None)
            self._save(record, path)
        record.pop("merging", None)
        record["research_log_present"] = self._git("cat-file", "-e", "HEAD:RESEARCH_LOG.md", check=False).returncode == 0
        log_detail = "" if record.get("research_log_updated") else "; RESEARCH_LOG.md was not updated"
        self._event(record, "INTEGRATED", "local task merges finished" + log_detail, path)

    def _import(self, campaign, record, path):
        message = f"round {record['number']}: results"
        if not record.get("import_pending"):
            self._checkout(campaign, record)
            record["import_pending"] = True
            record["import_base"] = self._git("rev-parse", "HEAD").stdout.strip()
            self._save(record, path)
        elif self._git("branch", "--show-current").stdout.strip() != campaign["branch"]:
            raise RuntimeError("research branch changed during import")
        # Reconcile the exact commit boundary, rather than trusting a message alone.
        head = self._git("rev-parse", "HEAD").stdout.strip()
        if head != record["import_base"]:
            if (self._git("log", "-1", "--format=%s").stdout.strip() != message or
                    self._git("rev-parse", "HEAD^").stdout.strip() != record["import_base"]):
                raise RuntimeError("research head changed during import")
            self._event(record, "RESULTS_IMPORTED", "recovered results commit", path)
            return
        paths = []
        for job in record["jobs"]:
            if self._stop.is_set():
                return
            if record["imports"].get(job, {}).get("error"):
                continue
            source = self.broker_root / job
            target = self.repo / "results" / job
            job_paths = []
            try:
                snapshot = self.root / "rounds" / f"{record['number']}-imports" / job
                entry = record["imports"].get(job)
                if entry is None:
                    if target.exists() or target.is_symlink():
                        raise ValueError("result destination already exists")
                    receipt = json.loads((source / "receipt.json").read_text(encoding="utf-8"))
                    files = {"receipt.json": None}
                    if receipt["state"] != "REJECTED":
                        if not (source / "manifest.json").exists():
                            raise ValueError("collection manifest missing")
                        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
                        files["manifest.json"] = None
                        for item in manifest["files"]:
                            name = _relative(item["path"])
                            if name not in {"stdout.log", "stderr.log"} and not name.startswith("outputs/"):
                                raise ValueError("unexpected manifest path")
                            if PurePosixPath(name).name.endswith(".nerelan-import"):
                                raise ValueError("reserved import temporary filename")
                            if name in files:
                                raise ValueError("duplicate manifest path")
                            files[name] = item
                    hashes = {}
                    # Freeze and verify every file before touching the repository.
                    for name, item in files.items():
                        candidate = source / name
                        if candidate.is_symlink() or any(p.is_symlink() for p in candidate.parents):
                            raise ValueError("symlink in result")
                        data = candidate.read_bytes()
                        digest = hashlib.sha256(data).hexdigest()
                        if item is not None and (digest != item["sha256"] or len(data) != item["size"]):
                            raise ValueError("manifest mismatch: " + name)
                        dest = snapshot / name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(data)
                        hashes[name] = digest
                    entry = record["imports"][job] = {"files": hashes}
                    self._save(record, path)  # Ownership recorded before first destination write.
                for name, digest in entry["files"].items():
                    dest = target / name
                    if dest.is_symlink() or any(p.is_symlink() for p in dest.parents):
                        raise ValueError("symlink in destination")
                    data = (snapshot / name).read_bytes()
                    if hashlib.sha256(data).hexdigest() != digest:
                        raise ValueError("snapshot mismatch")
                    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
                        raise ValueError("result destination changed")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if not dest.exists():
                        temporary = dest.with_name("." + dest.name + ".nerelan-import")
                        if temporary.is_symlink():
                            raise ValueError("symlink in import temporary file")
                        # This name is reserved beneath an initially absent job
                        # directory, after durable ownership of its files is saved.
                        with temporary.open("wb") as stream:
                            stream.write(data)
                            stream.flush()
                            os.fsync(stream.fileno())
                        os.replace(temporary, dest)
                    if hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
                        raise ValueError("copied manifest mismatch")
                    job_paths.append(dest.relative_to(self.repo).as_posix())
                entry["imported"] = True
                paths.extend(job_paths)
            except (OSError, ValueError, KeyError) as exc:
                record["imports"][job] = {**record["imports"].get(job, {}), "error": str(exc)}
        if paths:
            self._git("add", "--", *paths)
            staged = self._git("diff", "--cached", "--name-only").stdout.splitlines()
            if set(staged) != set(paths):
                raise RuntimeError("unrelated staged files; results commit paused")
            self._save(record, path)
            self._git("commit", "-m", message, env=self._commit_env())
        self._event(record, "RESULTS_IMPORTED", "broker evidence import finished", path)


def configured_loop(*, goal_service, planner, broker=None):
    path = os.environ.get(ENV_CAMPAIGN, "").strip()
    if not path:
        return None
    return ResearchLoop(path, goal_service=goal_service, planner=planner,
                        broker_root=broker.profile.local_root if broker else None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status"])
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    config = load_campaign(args.campaign)
    root = Path(config["state_dir"]) / config["campaign_id"]
    state = json.loads((root / "state.json").read_text(encoding="utf-8")) if (root / "state.json").exists() else {"state": "NOT_STARTED"}
    if "round" in state:
        current = root / "rounds" / f"{state['round']}.json"
        if current.exists():
            state["current_round"] = json.loads(current.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(state["state"], "round", state.get("round", "-"),
              state.get("current_round", {}).get("state", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
