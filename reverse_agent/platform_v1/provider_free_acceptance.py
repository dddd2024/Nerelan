"""Provider-free Platform V1 acceptance harness.

This module proves the Platform V1 coordination middleware reaches
``READY_FOR_HUMAN`` without any model API call, Codex invocation, OpenHands
invocation, GitHub network call, or nested agent. It uses a real temporary
Git repository, real isolated worktree, real SQLite database, real local
validation, real commit, and real push to a local bare remote. The Draft PR
and workflow observations are simulated fixtures that bind to the actual
generated commit SHA.

The harness is executable via:

    python -m reverse_agent.platform_v1.provider_free_acceptance \
      --repo-dir F:/reverse-agent \
      --workspace-root F:/reverse-agent-workspaces/provider-free-v1

It emits canonical JSON and exits ``0`` on success. The terminal marker is
``PLATFORM_V1_PROVIDER_FREE_E2E_COMPLETE``.

Design constraints:
  * No ``codex``, ``gh``, model API, or network command is executed.
  * The fixture repository, bare remote, SQLite database, worktree, commit,
    and simulated Draft PR are all isolated under ``--workspace-root``.
  * The existing ``#115`` execution identity and ``.platform_v1_runtime``
    database are never touched.
  * Restart and resume reuse the same execution, worktree, branch, commit,
    local-remote head, simulated Draft PR, and workflow evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .coordinator import PlatformV1Coordinator
from .execution_adapters import (
    ExecutorResult,
    GitHubPublicationAdapter,
    GitWorktreeManager,
    LocalValidationRunner,
    WorkflowObserver,
    _git,
)
from .github_adapter import WorkflowRun
from .issue_task import IssueTaskLoader
from .run_store import RunState, SQLiteRunStore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURE_REPOSITORY = "fixture/provider-free"
FIXTURE_ISSUE_NUMBER = 900115
FIXTURE_BRANCH = "agent/provider-free-v1"
FIXTURE_ALLOWED_PATH = "fixtures/provider_free_v1.txt"
FIXTURE_REQUIRED_CHECK = "git diff --check"
FIXTURE_EXECUTOR_CONTENT = (
    "platform-v1-provider-free\n"
    "executor=deterministic-fixture\n"
    "publication=simulated-draft-pr\n"
)


# ---------------------------------------------------------------------------
# Deterministic fixture executor
# ---------------------------------------------------------------------------


class DeterministicFixtureExecutor:
    """Executor that writes exactly one approved fixture file.

    It does not start a subprocess, does not call a model, and does not
    access the network. The call count is persisted to the fixture
    directory so restarts can verify idempotency.
    """

    def __init__(self, fixture_dir: Path) -> None:
        self._fixture_dir = Path(fixture_dir)
        self._fixture_dir.mkdir(parents=True, exist_ok=True)
        self._counter_path = self._fixture_dir / "executor_counter.json"
        self._counter = self._load_counter()

    def _load_counter(self) -> dict[str, int]:
        if self._counter_path.exists():
            try:
                return json.loads(self._counter_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"execute": 0}

    def _save_counter(self) -> None:
        self._counter_path.write_text(
            json.dumps(self._counter, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )

    @property
    def call_count(self) -> int:
        return self._counter["execute"]

    def execute(self, task: Any, worktree: Path, timeout_seconds: int) -> ExecutorResult:
        self._counter["execute"] += 1
        self._save_counter()
        target = worktree / FIXTURE_ALLOWED_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(FIXTURE_EXECUTOR_CONTENT, encoding="utf-8")
        digest = hashlib.sha256(FIXTURE_EXECUTOR_CONTENT.encode("utf-8")).hexdigest()
        return ExecutorResult(
            exit_code=0,
            timed_out=False,
            elapsed_seconds=0.0,
            output_sha256=digest,
            summary="deterministic-fixture-executor: wrote approved fixture file",
            executor_reference="deterministic-fixture",
            malformed=False,
        )


# ---------------------------------------------------------------------------
# Local Draft PR publisher
# ---------------------------------------------------------------------------


class LocalDraftPRPublisher:
    """Narrow local publisher: real Git commit/push, simulated Draft PR.

    ``commit`` and ``push`` delegate to the production :class:`GitHubPublicationAdapter`
    Git logic. ``ensure_draft_pr`` simulates a Draft PR and persists its state
    to the fixture directory so restarts can discover and reuse the same PR.
    ``publish_evidence`` is a no-op (the harness does not publish to GitHub).

    All side-effect counts are persisted to survive process restarts.
    """

    def __init__(self, repository: str, fixture_dir: Path) -> None:
        self._fixture_dir = Path(fixture_dir)
        self._fixture_dir.mkdir(parents=True, exist_ok=True)
        self._pr_state_path = self._fixture_dir / "simulated_pr.json"
        self._counter_path = self._fixture_dir / "publisher_counters.json"
        self._counters = self._load_counters()
        self._git_publisher = GitHubPublicationAdapter(
            repository, task_refresher=lambda task: task
        )

    def _load_counters(self) -> dict[str, int]:
        if self._counter_path.exists():
            try:
                return json.loads(self._counter_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"commit": 0, "push": 0, "create": 0}

    def _save_counters(self) -> None:
        self._counter_path.write_text(
            json.dumps(self._counters, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )

    @property
    def commit_count(self) -> int:
        return self._counters["commit"]

    @property
    def push_count(self) -> int:
        return self._counters["push"]

    @property
    def create_count(self) -> int:
        return self._counters["create"]

    def commit(self, worktree: Path, task: Any) -> str:
        self._counters["commit"] += 1
        self._save_counters()
        return self._git_publisher.commit(worktree, task)

    def push(self, worktree: Path, branch: str) -> str:
        self._counters["push"] += 1
        self._save_counters()
        return self._git_publisher.push(worktree, branch)

    def ensure_draft_pr(self, task: Any, head_sha: str) -> int:
        if self._pr_state_path.exists():
            data = json.loads(self._pr_state_path.read_text(encoding="utf-8"))
            return int(data["pr_number"])
        self._counters["create"] += 1
        self._save_counters()
        pr_number = task.work_item.source_issue_number
        data = {
            "pr_number": pr_number,
            "head_sha": head_sha,
            "state": "OPEN",
            "is_draft": True,
            "head_ref": task.work_item.target_branch,
            "base_ref": "main",
        }
        self._pr_state_path.write_text(
            json.dumps(data, sort_keys=True, indent=2), encoding="utf-8"
        )
        return pr_number

    def publish_evidence(self, record: Any, task: Any) -> None:
        """No-op for the provider-free harness."""

    @property
    def simulated_pr(self) -> dict[str, Any] | None:
        if self._pr_state_path.exists():
            return json.loads(self._pr_state_path.read_text(encoding="utf-8"))
        return None


# ---------------------------------------------------------------------------
# Fixture workflow observer
# ---------------------------------------------------------------------------


class _FixtureGitHubAdapter:
    """Returns SUCCESS workflow runs bound to whatever exact head is requested.

    This replaces the live ``gh run list`` call with a deterministic fixture
    that always reports the four required workflows as SUCCESS on the exact
    head SHA. No network access occurs.
    """

    def __init__(self) -> None:
        self.call_count = 0

    def get_workflow_runs(
        self, repository: str, exact_head_sha: str
    ) -> tuple[WorkflowRun, ...]:
        self.call_count += 1
        return (
            WorkflowRun(
                workflow_name="CI",
                event="pull_request",
                run_id="fixture-ci-1",
                head_sha=exact_head_sha,
                status="completed",
                conclusion="success",
            ),
            WorkflowRun(
                workflow_name="Decision Preflight",
                event="pull_request",
                run_id="fixture-dp-1",
                head_sha=exact_head_sha,
                status="completed",
                conclusion="success",
            ),
            WorkflowRun(
                workflow_name="State Gate",
                event="pull_request",
                run_id="fixture-sg-pr-1",
                head_sha=exact_head_sha,
                status="completed",
                conclusion="success",
            ),
            WorkflowRun(
                workflow_name="State Gate",
                event="push",
                run_id="fixture-sg-push-1",
                head_sha=exact_head_sha,
                status="completed",
                conclusion="success",
            ),
        )


def _build_fixture_workflow_observer() -> WorkflowObserver:
    """Build a WorkflowObserver backed by the fixture adapter."""
    adapter = _FixtureGitHubAdapter()
    return WorkflowObserver(adapter=adapter, max_wait_seconds=0)


# ---------------------------------------------------------------------------
# Fixture repository and task construction
# ---------------------------------------------------------------------------


def _force_remove_readonly(func: Any, path: str, exc: Any) -> None:
    """Windows rmtree error handler for read-only git object files."""
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _create_fixture_repo(fixture_dir: Path) -> tuple[Path, Path, str]:
    """Create a fixture Git repo with a local bare remote and initial main commit.

    Returns ``(source_repo, bare_remote, base_sha)``. All prior fixture state
    (SQLite database, counters, simulated PR, workspaces) is removed to ensure
    a clean run.
    """
    fixture_dir.mkdir(parents=True, exist_ok=True)

    # Clean up all prior fixture state so the harness is reproducible.
    for stale in (
        "fixture-source-repo",
        "fixture-bare-remote.git",
        "workspaces",
        "runs.sqlite3",
        "runs.sqlite3-wal",
        "runs.sqlite3-shm",
        "executor_counter.json",
        "publisher_counters.json",
        "simulated_pr.json",
    ):
        stale_path = fixture_dir / stale
        if stale_path.exists():
            if stale_path.is_dir():
                shutil.rmtree(stale_path, onerror=_force_remove_readonly)
            else:
                stale_path.unlink()

    source = fixture_dir / "fixture-source-repo"
    bare = fixture_dir / "fixture-bare-remote.git"

    source.mkdir()
    _git(source, "init")
    _git(source, "symbolic-ref", "HEAD", "refs/heads/main")
    _git(source, "config", "user.email", "fixture@example.invalid")
    _git(source, "config", "user.name", "Fixture")
    (source / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(source, "add", "README.md")
    _git(source, "commit", "-m", "fixture initial main")

    bare.mkdir()
    _git(bare, "init", "--bare")
    _git(source, "remote", "add", "origin", str(bare))
    _git(source, "push", "origin", "main")

    base_sha = _git(source, "rev-parse", "HEAD").stdout.strip()
    return source, bare, base_sha


def _build_fixture_task(base_sha: str):
    """Build an approved fixture task using ``IssueTaskLoader.parse()``."""
    body = (
        "# Provider-free V1 fixture\n\n"
        "```json\n"
        + json.dumps(
            {
                "schema_version": 1,
                "repository": FIXTURE_REPOSITORY,
                "base_sha": base_sha,
                "goal": "Create the provider-free fixture evidence file.",
                "allowed_paths": [FIXTURE_ALLOWED_PATH],
                "forbidden_operations": [
                    "push_main",
                    "merge",
                    "mark_ready",
                    "auto_merge",
                    "force_push",
                    "release",
                    "deployment",
                    "credential_publication",
                ],
                "required_checks": [FIXTURE_REQUIRED_CHECK],
                "target_branch": FIXTURE_BRANCH,
                "publication": "draft_pr",
                "risk_tier": "R1",
                "max_rework_attempts": 1,
            },
            indent=2,
        )
        + "\n```\n"
    )
    issue = {
        "number": FIXTURE_ISSUE_NUMBER,
        "state": "OPEN",
        "body": body,
        "labels": [{"name": "r1-approved"}, {"name": "work-item"}],
    }
    events = [
        {
            "id": 9001,
            "event": "labeled",
            "label": {"name": "r1-approved"},
            "actor": {"login": "fixture"},
            "created_at": "2026-08-05T00:00:00Z",
        }
    ]
    return IssueTaskLoader.parse(
        issue=issue,
        events=events,
        expected_repository=FIXTURE_REPOSITORY,
        expected_base_sha=base_sha,
    )


# ---------------------------------------------------------------------------
# Harness result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HarnessResult:
    terminal: str
    state: str
    model_calls: int
    network_calls: int
    executor_calls: int
    commit_count: int
    push_count: int
    draft_pr_create_count: int
    resume_idempotent: bool
    fixture_base_sha: str
    execution_id: str
    task_digest: str
    worktree_path: str
    commit_sha: str
    head_sha: str
    local_remote_head: str
    simulated_pr: dict[str, Any]
    workflow_observations: list[dict[str, Any]]
    execution_rows: int
    first_run_state: str
    resume_run_state: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "terminal": self.terminal,
            "state": self.state,
            "model_calls": self.model_calls,
            "network_calls": self.network_calls,
            "executor_calls": self.executor_calls,
            "commit_count": self.commit_count,
            "push_count": self.push_count,
            "draft_pr_create_count": self.draft_pr_create_count,
            "resume_idempotent": self.resume_idempotent,
            "fixture_base_sha": self.fixture_base_sha,
            "execution_id": self.execution_id,
            "task_digest": self.task_digest,
            "worktree_path": self.worktree_path,
            "commit_sha": self.commit_sha,
            "head_sha": self.head_sha,
            "local_remote_head": self.local_remote_head,
            "simulated_pr": self.simulated_pr,
            "workflow_observations": self.workflow_observations,
            "execution_rows": self.execution_rows,
            "first_run_state": self.first_run_state,
            "resume_run_state": self.resume_run_state,
        }


# ---------------------------------------------------------------------------
# Main harness
# ---------------------------------------------------------------------------


def run_provider_free_acceptance(
    *, repo_dir: Path | str, workspace_root: Path | str
) -> HarnessResult:
    """Run the provider-free acceptance harness.

    Creates an isolated fixture Git repository, executes the Platform V1
    coordinator with a deterministic executor, verifies ``READY_FOR_HUMAN``,
    then restarts and proves idempotency. Returns a :class:`HarnessResult`.
    """
    repo_dir = Path(repo_dir).resolve()
    workspace_root = Path(workspace_root).resolve()
    fixture_dir = workspace_root

    # Create fixture repository (fresh each run of the harness script)
    source_repo, bare_remote, base_sha = _create_fixture_repo(fixture_dir)

    # Build the approved fixture task
    task = _build_fixture_task(base_sha)

    # SQLite database inside the fixture directory (never .platform_v1_runtime)
    db_path = fixture_dir / "runs.sqlite3"
    store = SQLiteRunStore(db_path)

    # Real worktree manager pointing at the fixture source repo
    workspaces_root = fixture_dir / "workspaces"
    workspace_manager = GitWorktreeManager(source_repo, workspaces_root)

    # Deterministic executor with persistent call count
    executor = DeterministicFixtureExecutor(fixture_dir)

    # Local publisher: real git commit/push, simulated Draft PR
    publisher = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)

    # Real validation runner (runs `git diff --check` in the worktree)
    validator = LocalValidationRunner()

    # Fixture workflow observer (no network)
    workflow_observer = _build_fixture_workflow_observer()

    # Build and run the coordinator
    coordinator = PlatformV1Coordinator(
        store=store,
        workspace_manager=workspace_manager,
        executor=executor,
        validator=validator,
        publisher=publisher,
        workflow_observer=workflow_observer,
    )

    first_record = coordinator.run(task)
    first_state = first_record.state

    if first_record.state != RunState.READY_FOR_HUMAN:
        store.close()
        raise RuntimeError(
            f"provider_free_first_run_failed: state={first_record.state.value} "
            f"classification={first_record.failure_classification}"
        )

    # Collect first-run evidence
    first_commit_sha = first_record.commit_sha
    first_head_sha = first_record.head_sha
    first_execution_id = first_record.execution_id
    first_task_digest = first_record.task_digest
    first_worktree_path = first_record.worktree_path
    first_pr_number = first_record.pr_number
    first_workflow_observations = list(first_record.workflow_observations)

    # Verify local bare remote head equals the local commit
    remote_check = _git(
        source_repo, "ls-remote", "--heads", "origin", FIXTURE_BRANCH, check=False
    )
    local_remote_head = (
        remote_check.stdout.split()[0] if remote_check.stdout.strip() else ""
    )
    if local_remote_head != first_head_sha:
        store.close()
        raise RuntimeError(
            f"local_remote_head_mismatch: remote={local_remote_head} "
            f"local={first_head_sha}"
        )

    # Verify the fixture file content
    worktree_path = Path(first_worktree_path)
    fixture_file = worktree_path / FIXTURE_ALLOWED_PATH
    if not fixture_file.exists():
        store.close()
        raise RuntimeError("fixture_file_missing_after_run")
    actual_content = fixture_file.read_text(encoding="utf-8")
    if actual_content != FIXTURE_EXECUTOR_CONTENT:
        store.close()
        raise RuntimeError(
            f"fixture_file_content_mismatch: expected={FIXTURE_EXECUTOR_CONTENT!r} "
            f"actual={actual_content!r}"
        )

    first_executor_calls = executor.call_count
    first_commit_count = publisher.commit_count
    first_push_count = publisher.push_count
    first_create_count = publisher.create_count
    first_execution_rows = store.count_runs()

    # --- Restart and idempotency proof ---
    store.close()

    # Re-instantiate store, publisher, executor, coordinator
    store2 = SQLiteRunStore(db_path)
    publisher2 = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)
    executor2 = DeterministicFixtureExecutor(fixture_dir)
    coordinator2 = PlatformV1Coordinator(
        store=store2,
        workspace_manager=GitWorktreeManager(source_repo, workspaces_root),
        executor=executor2,
        validator=LocalValidationRunner(),
        publisher=publisher2,
        workflow_observer=_build_fixture_workflow_observer(),
    )

    resume_record = coordinator2.run(task)
    resume_state = resume_record.state

    # Verify idempotency
    idempotent = (
        resume_record.execution_id == first_execution_id
        and resume_record.task_digest == first_task_digest
        and resume_record.worktree_path == first_worktree_path
        and resume_record.commit_sha == first_commit_sha
        and resume_record.head_sha == first_head_sha
        and resume_record.pr_number == first_pr_number
        and list(resume_record.workflow_observations) == first_workflow_observations
        and executor2.call_count == first_executor_calls
        and publisher2.commit_count == first_commit_count
        and publisher2.push_count == first_push_count
        and publisher2.create_count == first_create_count
        and store2.count_runs() == first_execution_rows
    )

    # Verify local remote head is still stable
    remote_check2 = _git(
        source_repo, "ls-remote", "--heads", "origin", FIXTURE_BRANCH, check=False
    )
    local_remote_head_2 = (
        remote_check2.stdout.split()[0] if remote_check2.stdout.strip() else ""
    )

    if local_remote_head_2 != first_head_sha:
        idempotent = False

    # Verify simulated PR is reused
    simulated_pr = publisher2.simulated_pr
    if simulated_pr is None or simulated_pr.get("head_sha") != first_head_sha:
        idempotent = False

    store2.close()

    return HarnessResult(
        terminal="PLATFORM_V1_PROVIDER_FREE_E2E_COMPLETE" if idempotent else "HARNESS_FAILED",
        state=first_record.state.value,
        model_calls=0,
        network_calls=0,
        executor_calls=executor2.call_count,
        commit_count=publisher2.commit_count,
        push_count=publisher2.push_count,
        draft_pr_create_count=publisher2.create_count,
        resume_idempotent=idempotent,
        fixture_base_sha=base_sha,
        execution_id=first_execution_id,
        task_digest=first_task_digest,
        worktree_path=first_worktree_path,
        commit_sha=first_commit_sha,
        head_sha=first_head_sha,
        local_remote_head=local_remote_head_2,
        simulated_pr=simulated_pr or {},
        workflow_observations=first_workflow_observations,
        execution_rows=first_execution_rows,
        first_run_state=first_state.value,
        resume_run_state=resume_state.value,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Provider-free Platform V1 acceptance harness"
    )
    parser.add_argument("--repo-dir", required=True, help="Path to the real repository")
    parser.add_argument(
        "--workspace-root", required=True, help="Root for isolated fixture workspace"
    )
    args = parser.parse_args(argv)

    try:
        result = run_provider_free_acceptance(
            repo_dir=args.repo_dir, workspace_root=args.workspace_root
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "terminal": "HARNESS_FAILED",
                    "error": str(exc),
                    "model_calls": 0,
                    "network_calls": 0,
                },
                indent=2,
            )
        )
        return 1

    print(json.dumps(result.to_mapping(), indent=2, sort_keys=True))
    if result.terminal == "PLATFORM_V1_PROVIDER_FREE_E2E_COMPLETE":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
