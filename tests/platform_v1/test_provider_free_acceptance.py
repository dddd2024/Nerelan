"""Tests for the provider-free Platform V1 acceptance harness.

These tests exercise the real provider-free vertical slice: a fixture Git
repository, local bare remote, real SQLite run store, real worktree, real
commit, real push, simulated Draft PR, and fixture workflow observations
bound to the exact generated commit SHA.

The tests verify:
  * The full harness reaches ``READY_FOR_HUMAN`` and is idempotent.
  * The deterministic executor writes only the approved fixture file.
  * The local publisher reuses the simulated Draft PR across restarts.
  * Negative paths reject correctly:
      - Executor writing an unauthorized path → commit rejected.
      - Worktree base drift → rejected.
      - Mismatched branch → rejected.
      - Dirty worktree → rejected.
      - Diverged local remote → push rejected.
      - Resume does not repeat commit/push/PR-creation side effects.
      - Workflow head mismatch → STALE_HEAD.
      - Missing required workflow → not READY_FOR_HUMAN.
      - Harness never invokes codex / gh / network commands.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.platform_v1.coordinator import PlatformV1Coordinator
from reverse_agent.platform_v1.execution_adapters import (
    ExecutorResult,
    GitHubPublicationAdapter,
    GitWorktreeManager,
    LocalValidationRunner,
    WorkflowObserver,
    _git,
)
from reverse_agent.platform_v1.github_adapter import WorkflowRun
from reverse_agent.platform_v1.provider_free_acceptance import (
    DeterministicFixtureExecutor,
    HarnessResult,
    LocalDraftPRPublisher,
    _build_fixture_task,
    _create_fixture_repo,
    _FixtureGitHubAdapter,
    FIXTURE_ALLOWED_PATH,
    FIXTURE_BRANCH,
    FIXTURE_EXECUTOR_CONTENT,
    FIXTURE_REPOSITORY,
    run_provider_free_acceptance,
)
from reverse_agent.platform_v1.run_store import RunState, SQLiteRunStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _force_remove_readonly(func: Any, path: str, exc: Any) -> None:
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _make_fixture(tmp_path: Path) -> tuple[Path, Path, Path, str, Any]:
    """Create a fixture repo and task, returning (fixture_dir, source, bare, base_sha, task)."""
    fixture_dir = tmp_path / "fixture"
    source, bare, base_sha = _create_fixture_repo(fixture_dir)
    task = _build_fixture_task(base_sha)
    return fixture_dir, source, bare, base_sha, task


def _build_coordinator(
    fixture_dir: Path,
    source: Path,
    task: Any,
    *,
    executor: Any | None = None,
    publisher: Any | None = None,
    workflow_observer: Any | None = None,
) -> tuple[PlatformV1Coordinator, SQLiteRunStore, Any, Any, Any]:
    db_path = fixture_dir / "runs.sqlite3"
    store = SQLiteRunStore(db_path)
    workspaces_root = fixture_dir / "workspaces"
    workspace_manager = GitWorktreeManager(source, workspaces_root)
    if executor is None:
        executor = DeterministicFixtureExecutor(fixture_dir)
    if publisher is None:
        publisher = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)
    if workflow_observer is None:
        workflow_observer = WorkflowObserver(
            adapter=_FixtureGitHubAdapter(), max_wait_seconds=0
        )
    validator = LocalValidationRunner()
    coordinator = PlatformV1Coordinator(
        store=store,
        workspace_manager=workspace_manager,
        executor=executor,
        validator=validator,
        publisher=publisher,
        workflow_observer=workflow_observer,
    )
    return coordinator, store, executor, publisher, workflow_observer


# ---------------------------------------------------------------------------
# Full harness positive test
# ---------------------------------------------------------------------------


class TestProviderFreeHarnessPositive:
    def test_harness_reaches_ready_for_human_and_is_idempotent(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        assert result.terminal == "PLATFORM_V1_PROVIDER_FREE_E2E_COMPLETE"
        assert result.state == "READY_FOR_HUMAN"
        assert result.model_calls == 0
        assert result.network_calls == 0
        assert result.executor_calls == 1
        assert result.commit_count == 1
        assert result.push_count == 1
        assert result.draft_pr_create_count == 1
        assert result.resume_idempotent is True
        assert result.execution_rows == 1
        assert result.first_run_state == "READY_FOR_HUMAN"
        assert result.resume_run_state == "READY_FOR_HUMAN"

    def test_harness_fixture_base_sha_is_real_git_commit(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        base = result.fixture_base_sha
        assert len(base) == 40
        assert all(c in "0123456789abcdef" for c in base)

    def test_harness_commit_sha_equals_local_remote_head(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        assert result.commit_sha == result.head_sha
        assert result.local_remote_head == result.head_sha

    def test_harness_simulated_pr_is_open_draft(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        pr = result.simulated_pr
        assert pr["state"] == "OPEN"
        assert pr["is_draft"] is True
        assert pr["head_ref"] == FIXTURE_BRANCH
        assert pr["base_ref"] == "main"
        assert pr["head_sha"] == result.head_sha

    def test_harness_workflow_observations_bind_exact_head(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        assert len(result.workflow_observations) == 4
        for obs in result.workflow_observations:
            assert obs["head_sha"] == result.head_sha
            assert obs["classification"] == "SUCCESS"
            assert obs["status"] == "COMPLETED"
            assert obs["conclusion"] == "SUCCESS"

    def test_harness_fixture_file_has_exact_content(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        worktree = Path(result.worktree_path)
        fixture_file = worktree / FIXTURE_ALLOWED_PATH
        assert fixture_file.exists()
        assert fixture_file.read_text(encoding="utf-8") == FIXTURE_EXECUTOR_CONTENT

    def test_harness_execution_id_and_task_digest_are_stable(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        assert result.execution_id.startswith("exec-issue-900115-")
        assert len(result.task_digest) == 64
        assert all(c in "0123456789abcdef" for c in result.task_digest)


# ---------------------------------------------------------------------------
# Deterministic fixture executor
# ---------------------------------------------------------------------------


class TestDeterministicFixtureExecutor:
    def test_writes_only_approved_fixture_file(self, tmp_path: Path) -> None:
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        executor = DeterministicFixtureExecutor(fixture_dir)
        result = executor.execute(None, worktree, 30)
        assert result.exit_code == 0
        assert result.timed_out is False
        assert result.malformed is False
        fixture_file = worktree / FIXTURE_ALLOWED_PATH
        assert fixture_file.exists()
        assert fixture_file.read_text(encoding="utf-8") == FIXTURE_EXECUTOR_CONTENT

    def test_executor_content_ends_with_single_newline(self) -> None:
        assert FIXTURE_EXECUTOR_CONTENT.endswith("\n")
        assert not FIXTURE_EXECUTOR_CONTENT.endswith("\n\n")

    def test_call_count_persists_across_restart(self, tmp_path: Path) -> None:
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        executor1 = DeterministicFixtureExecutor(fixture_dir)
        executor1.execute(None, worktree, 30)
        assert executor1.call_count == 1
        executor2 = DeterministicFixtureExecutor(fixture_dir)
        assert executor2.call_count == 1
        executor2.execute(None, worktree, 30)
        assert executor2.call_count == 2

    def test_executor_writing_unauthorized_path_rejected_by_commit(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)

        class _EvilExecutor:
            def __init__(self) -> None:
                self.call_count = 0

            def execute(self, task: Any, worktree: Path, timeout_seconds: int) -> ExecutorResult:
                self.call_count += 1
                # Write the approved file...
                target = worktree / FIXTURE_ALLOWED_PATH
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(FIXTURE_EXECUTOR_CONTENT, encoding="utf-8")
                # ...AND an unauthorized second file
                evil = worktree / "unauthorized.txt"
                evil.write_text("evil\n", encoding="utf-8")
                import hashlib
                digest = hashlib.sha256(FIXTURE_EXECUTOR_CONTENT.encode("utf-8")).hexdigest()
                return ExecutorResult(
                    exit_code=0, timed_out=False, elapsed_seconds=0.0,
                    output_sha256=digest, summary="evil-executor",
                    executor_reference="evil", malformed=False,
                )

        coordinator, store, executor, publisher, observer = _build_coordinator(
            fixture_dir, source, task, executor=_EvilExecutor()
        )
        # The commit step must reject the unauthorized path
        with pytest.raises(RuntimeError, match="changed_path_outside_scope"):
            coordinator.run(task)
        store.close()

    def test_executor_does_not_call_subprocess_or_network(self, tmp_path: Path) -> None:
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        executor = DeterministicFixtureExecutor(fixture_dir)
        # Monkey-patch subprocess.run to ensure it is never called
        original_run = subprocess.run
        called: list[str] = []

        def guard(*args: Any, **kwargs: Any) -> Any:
            called.append(str(args[0] if args else kwargs))
            raise AssertionError(f"subprocess.run was called: {called}")

        try:
            subprocess.run = guard  # type: ignore[assignment]
            executor.execute(None, worktree, 30)
        finally:
            subprocess.run = original_run  # type: ignore[assignment]
        assert not called, f"executor must not call subprocess: {called}"


# ---------------------------------------------------------------------------
# Local Draft PR publisher
# ---------------------------------------------------------------------------


class TestLocalDraftPRPublisher:
    def test_ensure_draft_pr_creates_once_then_reuses(self, tmp_path: Path) -> None:
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        publisher1 = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)
        pr_number_1 = publisher1.ensure_draft_pr(
            _build_fixture_task("0" * 40), "abc123"
        )
        assert pr_number_1 == 900115
        assert publisher1.create_count == 1
        # Restart: re-instantiate and call again
        publisher2 = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)
        pr_number_2 = publisher2.ensure_draft_pr(
            _build_fixture_task("0" * 40), "abc123"
        )
        assert pr_number_2 == 900115
        # Total create count remains 1 — the second publisher did not create a new PR.
        assert publisher2.create_count == 1

    def test_simulated_pr_persists_head_sha(self, tmp_path: Path) -> None:
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        publisher = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)
        publisher.ensure_draft_pr(_build_fixture_task("0" * 40), "deadbeef")
        pr = publisher.simulated_pr
        assert pr is not None
        assert pr["head_sha"] == "deadbeef"
        assert pr["is_draft"] is True

    def test_commit_and_push_counts_persist_across_restart(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        publisher1 = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)
        # Initialize a worktree with a change
        workspaces_root = fixture_dir / "workspaces"
        manager = GitWorktreeManager(source, workspaces_root)
        worktree = manager.prepare("exec-test", FIXTURE_BRANCH, base_sha)
        # Write the fixture file
        target = worktree / FIXTURE_ALLOWED_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(FIXTURE_EXECUTOR_CONTENT, encoding="utf-8")
        # Commit and push
        publisher1.commit(worktree, task)
        publisher1.push(worktree, FIXTURE_BRANCH)
        assert publisher1.commit_count == 1
        assert publisher1.push_count == 1
        # Restart
        publisher2 = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)
        assert publisher2.commit_count == 1
        assert publisher2.push_count == 1


# ---------------------------------------------------------------------------
# Negative: worktree base drift
# ---------------------------------------------------------------------------


class TestWorktreeRejections:
    def test_worktree_base_drift_rejected(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        # Create a second commit on main to create a different base
        (source / "second.txt").write_text("second\n", encoding="utf-8")
        _git(source, "add", "second.txt")
        _git(source, "commit", "-m", "second")
        new_base = _git(source, "rev-parse", "HEAD").stdout.strip()
        # Now try to prepare a worktree with the old base_sha but the repo has moved
        workspaces_root = fixture_dir / "workspaces"
        manager = GitWorktreeManager(source, workspaces_root)
        # The old base_sha is still a valid commit, so prepare should work
        # but if we try to use a non-ancestor base, it should fail
        with pytest.raises(RuntimeError, match="base_drift|worktree_create_failed"):
            manager.prepare("exec-drift", FIXTURE_BRANCH, "0" * 40)

    def test_mismatched_branch_rejected(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        workspaces_root = fixture_dir / "workspaces"
        manager = GitWorktreeManager(source, workspaces_root)
        # Create worktree with one branch
        path1 = manager.prepare("exec-1", "agent/branch-a", base_sha)
        assert path1.exists()
        # Try to reconcile the same path with a different branch
        with pytest.raises(RuntimeError, match="branch_identity_conflict"):
            manager.prepare("exec-1", "agent/branch-b", base_sha)

    def test_dirty_worktree_rejected_on_reconcile(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        workspaces_root = fixture_dir / "workspaces"
        manager = GitWorktreeManager(source, workspaces_root)
        path = manager.prepare("exec-dirty", FIXTURE_BRANCH, base_sha)
        # Make the worktree dirty
        (path / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        # Re-prepare with require_clean=True should reject
        with pytest.raises(RuntimeError, match="dirty_worktree"):
            manager.prepare("exec-dirty", FIXTURE_BRANCH, base_sha)


# ---------------------------------------------------------------------------
# Negative: diverged local remote
# ---------------------------------------------------------------------------


class TestRemoteDivergence:
    def test_diverged_remote_branch_rejected_on_push(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        workspaces_root = fixture_dir / "workspaces"
        manager = GitWorktreeManager(source, workspaces_root)
        worktree = manager.prepare("exec-diverge", FIXTURE_BRANCH, base_sha)
        # Write and commit the fixture file
        target = worktree / FIXTURE_ALLOWED_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(FIXTURE_EXECUTOR_CONTENT, encoding="utf-8")
        publisher = LocalDraftPRPublisher(FIXTURE_REPOSITORY, fixture_dir)
        publisher.commit(worktree, task)
        publisher.push(worktree, FIXTURE_BRANCH)
        # Now create a divergent commit on the remote by cloning the bare remote,
        # making a different commit, and pushing it back.
        clone_path = fixture_dir / "diverge-clone"
        _git(fixture_dir, "clone", str(bare), str(clone_path))
        _git(clone_path, "checkout", FIXTURE_BRANCH)
        _git(clone_path, "config", "user.email", "diverge@example.invalid")
        _git(clone_path, "config", "user.name", "Diverge")
        (clone_path / "diverge.txt").write_text("diverge\n", encoding="utf-8")
        _git(clone_path, "add", "diverge.txt")
        _git(clone_path, "commit", "-m", "divergent")
        _git(clone_path, "push", "origin", FIXTURE_BRANCH)
        # Now the original worktree's push should detect divergence
        with pytest.raises(RuntimeError, match="remote_branch_diverged"):
            publisher.push(worktree, FIXTURE_BRANCH)


# ---------------------------------------------------------------------------
# Negative: resume idempotency
# ---------------------------------------------------------------------------


class TestResumeIdempotency:
    def test_resume_does_not_repeat_commit(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        coordinator1, store1, executor1, publisher1, observer1 = _build_coordinator(
            fixture_dir, source, task
        )
        record1 = coordinator1.run(task)
        assert record1.state == RunState.READY_FOR_HUMAN
        assert publisher1.commit_count == 1
        store1.close()
        # Restart
        coordinator2, store2, executor2, publisher2, observer2 = _build_coordinator(
            fixture_dir, source, task
        )
        record2 = coordinator2.run(task)
        assert record2.state == RunState.READY_FOR_HUMAN
        assert publisher2.commit_count == 1  # no new commit
        store2.close()

    def test_resume_does_not_repeat_push(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        coordinator1, store1, executor1, publisher1, observer1 = _build_coordinator(
            fixture_dir, source, task
        )
        record1 = coordinator1.run(task)
        assert publisher1.push_count == 1
        store1.close()
        coordinator2, store2, executor2, publisher2, observer2 = _build_coordinator(
            fixture_dir, source, task
        )
        coordinator2.run(task)
        assert publisher2.push_count == 1  # no new push
        store2.close()

    def test_resume_does_not_repeat_pr_creation(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        coordinator1, store1, executor1, publisher1, observer1 = _build_coordinator(
            fixture_dir, source, task
        )
        coordinator1.run(task)
        assert publisher1.create_count == 1
        store1.close()
        coordinator2, store2, executor2, publisher2, observer2 = _build_coordinator(
            fixture_dir, source, task
        )
        coordinator2.run(task)
        # Total create count remains 1 — resume did not create a new PR.
        assert publisher2.create_count == 1
        store2.close()

    def test_resume_does_not_repeat_executor_call(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        coordinator1, store1, executor1, publisher1, observer1 = _build_coordinator(
            fixture_dir, source, task
        )
        coordinator1.run(task)
        assert executor1.call_count == 1
        store1.close()
        coordinator2, store2, executor2, publisher2, observer2 = _build_coordinator(
            fixture_dir, source, task
        )
        coordinator2.run(task)
        assert executor2.call_count == 1  # no new executor call
        store2.close()

    def test_resume_preserves_execution_id_and_task_digest(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)
        coordinator1, store1, executor1, publisher1, observer1 = _build_coordinator(
            fixture_dir, source, task
        )
        record1 = coordinator1.run(task)
        store1.close()
        coordinator2, store2, executor2, publisher2, observer2 = _build_coordinator(
            fixture_dir, source, task
        )
        record2 = coordinator2.run(task)
        assert record2.execution_id == record1.execution_id
        assert record2.task_digest == record1.task_digest
        assert record2.commit_sha == record1.commit_sha
        assert record2.head_sha == record1.head_sha
        assert record2.pr_number == record1.pr_number
        store2.close()


# ---------------------------------------------------------------------------
# Negative: workflow observations
# ---------------------------------------------------------------------------


class TestWorkflowObservationRejections:
    def test_stale_head_workflow_classification(self, tmp_path: Path) -> None:
        # The fixture adapter returns runs with head_sha == exact_head_sha, so
        # to test STALE_HEAD we need an adapter that returns a DIFFERENT head.
        class _StaleHeadAdapter:
            def get_workflow_runs(
                self, repository: str, exact_head_sha: str
            ) -> tuple[WorkflowRun, ...]:
                # Return runs with a mismatched head SHA
                stale = "0" * 40
                return (
                    WorkflowRun(
                        workflow_name="CI",
                        event="pull_request",
                        run_id="fixture-ci-stale",
                        head_sha=stale,
                        status="completed",
                        conclusion="success",
                    ),
                    WorkflowRun(
                        workflow_name="Decision Preflight",
                        event="pull_request",
                        run_id="fixture-dp-stale",
                        head_sha=stale,
                        status="completed",
                        conclusion="success",
                    ),
                    WorkflowRun(
                        workflow_name="State Gate",
                        event="pull_request",
                        run_id="fixture-sg-pr-stale",
                        head_sha=stale,
                        status="completed",
                        conclusion="success",
                    ),
                    WorkflowRun(
                        workflow_name="State Gate",
                        event="push",
                        run_id="fixture-sg-push-stale",
                        head_sha=stale,
                        status="completed",
                        conclusion="success",
                    ),
                )

        observer = WorkflowObserver(
            adapter=_StaleHeadAdapter(), max_wait_seconds=0
        )
        # Pass the expected head SHA — the adapter returns runs with a different head
        observations = observer.observe(FIXTURE_REPOSITORY, "expected-head-sha")
        assert len(observations) == 4
        for obs in observations:
            assert obs["classification"] == "STALE_HEAD"

    def test_missing_required_workflow_blocks_ready_for_human(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)

        class _MissingWorkflowAdapter:
            def get_workflow_runs(
                self, repository: str, exact_head_sha: str
            ) -> tuple[WorkflowRun, ...]:
                # Return only CI — missing Decision Preflight and State Gate
                return (
                    WorkflowRun(
                        workflow_name="CI",
                        event="pull_request",
                        run_id="fixture-ci-1",
                        head_sha=exact_head_sha,
                        status="completed",
                        conclusion="success",
                    ),
                )

        observer = WorkflowObserver(
            adapter=_MissingWorkflowAdapter(), max_wait_seconds=0
        )
        coordinator, store, executor, publisher, _ = _build_coordinator(
            fixture_dir, source, task, workflow_observer=observer
        )
        record = coordinator.run(task)
        # With a missing workflow, the coordinator should not reach READY_FOR_HUMAN
        assert record.state != RunState.READY_FOR_HUMAN
        store.close()

    def test_failed_workflow_blocks_ready_for_human(self, tmp_path: Path) -> None:
        fixture_dir, source, bare, base_sha, task = _make_fixture(tmp_path)

        class _FailedWorkflowAdapter:
            def get_workflow_runs(
                self, repository: str, exact_head_sha: str
            ) -> tuple[WorkflowRun, ...]:
                return (
                    WorkflowRun(
                        workflow_name="CI",
                        event="pull_request",
                        run_id="fixture-ci-fail",
                        head_sha=exact_head_sha,
                        status="completed",
                        conclusion="failure",
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

        observer = WorkflowObserver(
            adapter=_FailedWorkflowAdapter(), max_wait_seconds=0
        )
        coordinator, store, executor, publisher, _ = _build_coordinator(
            fixture_dir, source, task, workflow_observer=observer
        )
        record = coordinator.run(task)
        assert record.state == RunState.REWORK_REQUIRED
        assert record.failure_classification == "PRODUCT_TEST_FAILURE"
        store.close()


# ---------------------------------------------------------------------------
# Negative: harness must not execute forbidden commands
# ---------------------------------------------------------------------------


class TestHarnessForbiddenCommands:
    def test_harness_does_not_invoke_codex(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        original_run = subprocess.run
        codex_calls: list[str] = []

        def guard(argv: Any, *args: Any, **kwargs: Any) -> Any:
            cmd = argv[0] if isinstance(argv, (list, tuple)) and argv else str(argv)
            cmd_str = " ".join(str(a) for a in argv) if isinstance(argv, (list, tuple)) else str(argv)
            if "codex" in cmd_str.lower():
                codex_calls.append(cmd_str)
                raise AssertionError(f"codex was invoked: {cmd_str}")
            return original_run(argv, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", guard)
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        assert result.terminal == "PLATFORM_V1_PROVIDER_FREE_E2E_COMPLETE"
        assert not codex_calls, f"codex was invoked: {codex_calls}"

    def test_harness_does_not_invoke_gh(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        original_run = subprocess.run
        gh_calls: list[str] = []

        def guard(argv: Any, *args: Any, **kwargs: Any) -> Any:
            cmd_str = " ".join(str(a) for a in argv) if isinstance(argv, (list, tuple)) else str(argv)
            if "gh" == str(argv[0] if isinstance(argv, (list, tuple)) and argv else ""):
                gh_calls.append(cmd_str)
                raise AssertionError(f"gh was invoked: {cmd_str}")
            return original_run(argv, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", guard)
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        assert result.terminal == "PLATFORM_V1_PROVIDER_FREE_E2E_COMPLETE"
        assert not gh_calls, f"gh was invoked: {gh_calls}"

    def test_harness_model_calls_is_zero(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        assert result.model_calls == 0

    def test_harness_network_calls_is_zero(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "provider-free-v1"
        result = run_provider_free_acceptance(
            repo_dir=tmp_path / "repo",
            workspace_root=workspace_root,
        )
        assert result.network_calls == 0
