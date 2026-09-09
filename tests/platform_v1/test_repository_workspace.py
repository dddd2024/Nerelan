"""Tests for repository workspace identity validation (Issue #691).

Provider-free regression coverage using temporary Git repositories with
different marker contents/origins. No network, no provider, no credentials.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.platform_v1.repository_workspace import (
    RepositoryWorkspaceError,
    RepositoryWorkspaceIdentityUnavailable,
    RepositoryWorkspaceInvalid,
    RepositoryWorkspaceMismatch,
    RepositoryWorkspaceUnconfigured,
    normalize_github_origin,
    resolve_repository_identity,
    validate_repository_workspace,
)


def _git_init_repo(path: Path, origin_url: str = "", marker: str = "") -> Path:
    """Create a temporary Git repository with optional origin and marker file."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init"],
        cwd=path, capture_output=True, text=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path, capture_output=True, text=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path, capture_output=True, text=True, check=True,
    )
    (path / "marker.txt").write_text(marker or "init", encoding="utf-8")
    subprocess.run(
        ["git", "add", "."],
        cwd=path, capture_output=True, text=True, check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=path, capture_output=True, text=True, check=True,
    )
    if origin_url:
        subprocess.run(
            ["git", "remote", "add", "origin", origin_url],
            cwd=path, capture_output=True, text=True, check=True,
        )
    return path


class TestNormalizeGitHubOrigin:
    """Test GitHub origin URL normalization."""

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("https://github.com/owner/repo.git", "owner/repo"),
            ("https://github.com/owner/repo", "owner/repo"),
            ("ssh://git@github.com/owner/repo.git", "owner/repo"),
            ("ssh://git@github.com/owner/repo", "owner/repo"),
            ("git@github.com:owner/repo.git", "owner/repo"),
            ("git@github.com:owner/repo", "owner/repo"),
        ],
    )
    def test_normalizes_github_urls(self, url: str, expected: str) -> None:
        assert normalize_github_origin(url) == expected

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "https://gitlab.com/owner/repo.git",
            "https://github.com/owner/repo/subdir",
            "git@github.com:owner/repo.git/extra",
            "https://github.com/owner",
            "not-a-url",
        ],
    )
    def test_rejects_non_github_or_invalid(self, url: str) -> None:
        assert normalize_github_origin(url) == ""


class TestResolveRepositoryIdentity:
    """Test resolving repository identity from a local Git repository."""

    def test_resolves_https_origin(self, tmp_path: Path) -> None:
        repo = _git_init_repo(tmp_path / "repo", "https://github.com/owner/repo.git")
        identity = resolve_repository_identity(str(repo))
        assert identity == "owner/repo"

    def test_resolves_ssh_origin(self, tmp_path: Path) -> None:
        repo = _git_init_repo(tmp_path / "repo", "git@github.com:owner/repo.git")
        identity = resolve_repository_identity(str(repo))
        assert identity == "owner/repo"

    def test_non_git_directory_raises_invalid(self, tmp_path: Path) -> None:
        (tmp_path / "plain").mkdir()
        with pytest.raises(RepositoryWorkspaceInvalid):
            resolve_repository_identity(str(tmp_path / "plain"))

    def test_missing_origin_raises_identity_unavailable(self, tmp_path: Path) -> None:
        repo = _git_init_repo(tmp_path / "repo")  # no origin
        with pytest.raises(RepositoryWorkspaceIdentityUnavailable):
            resolve_repository_identity(str(repo))

    def test_unsupported_origin_raises_identity_unavailable(self, tmp_path: Path) -> None:
        repo = _git_init_repo(tmp_path / "repo", "https://gitlab.com/owner/repo.git")
        with pytest.raises(RepositoryWorkspaceIdentityUnavailable):
            resolve_repository_identity(str(repo))


class TestValidateRepositoryWorkspace:
    """Test the primary validation entry point."""

    def test_matches_when_repo_a_and_task_a(self, tmp_path: Path, monkeypatch) -> None:
        repo = _git_init_repo(tmp_path / "repo_a", "https://github.com/owner/repoA.git")
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo))
        validate_repository_workspace("owner/repoA")  # should not raise

    def test_mismatch_when_repo_a_and_task_b(self, tmp_path: Path, monkeypatch) -> None:
        repo = _git_init_repo(tmp_path / "repo_a", "https://github.com/owner/repoA.git")
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo))
        with pytest.raises(RepositoryWorkspaceMismatch):
            validate_repository_workspace("owner/repoB")

    def test_missing_env_raises_unconfigured(self, monkeypatch) -> None:
        monkeypatch.delenv("REVERSE_AGENT_REPO_DIR", raising=False)
        with pytest.raises(RepositoryWorkspaceUnconfigured):
            validate_repository_workspace("owner/repo")

    def test_non_git_source_raises_invalid(self, tmp_path: Path, monkeypatch) -> None:
        plain = tmp_path / "plain"
        plain.mkdir()
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(plain))
        with pytest.raises(RepositoryWorkspaceInvalid):
            validate_repository_workspace("owner/repo")

    def test_missing_origin_raises_identity_unavailable(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        repo = _git_init_repo(tmp_path / "repo")  # no origin
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo))
        with pytest.raises(RepositoryWorkspaceIdentityUnavailable):
            validate_repository_workspace("owner/repo")

    @pytest.mark.parametrize(
        "origin_url",
        [
            "https://github.com/owner/repo.git",
            "ssh://git@github.com/owner/repo.git",
            "git@github.com:owner/repo.git",
        ],
    )
    def test_all_github_syntax_normalizes_to_same(
        self, tmp_path: Path, monkeypatch, origin_url: str
    ) -> None:
        repo = _git_init_repo(tmp_path / "repo", origin_url)
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo))
        validate_repository_workspace("owner/repo")  # should not raise


class TestGoalLaunchMismatch:
    """Test that goal launch blocks on repository/workspace mismatch."""

    def _services(self, tmp_path: Path) -> tuple[Any, Any, Any]:
        from reverse_agent.platform_v1.autonomy import AutonomyService
        from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
        from reverse_agent.platform_v1.control_store import PlatformControlStore
        from reverse_agent.platform_v1.goal_service import GoalService
        from reverse_agent.platform_v1.run_store import TaskStore

        store = TaskStore(":memory:")
        control = PlatformControlStore(store)
        autonomy = AutonomyService(
            control_store=control, capabilities=CapabilityRegistry()
        )
        return store, control, GoalService(store=store, control_store=control)

    def _window_payload(self) -> dict[str, Any]:
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        return {
            "policy_id": "owner-window-1",
            "policy_revision": 1,
            "owner_identity": "owner@example",
            "starts_at": (now - timedelta(seconds=5)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "repositories": ["owner/repoA"],
            "capabilities": ["execute_task", "validate_task"],
            "max_concurrent_tasks": 2,
            "max_tasks": 10,
            "max_retries": 1,
            "confirmation": "ACTIVATE",
        }

    def test_goal_launch_mismatch_no_task_materialization(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        repo = _git_init_repo(tmp_path / "repo_a", "https://github.com/owner/repoA.git")
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo))
        store, control, goals = self._services(tmp_path)

        goal = goals.create({
            "objective": "Test goal launch mismatch",
            "repository": "owner/repoA",
            "idempotency_key": "goal-mismatch-v1",
            "executor_kind": "opencode",
            "orchestration_mode": "sequential_team",
        })
        goals.plan(goal.id, expected_revision=1)
        goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")

        from reverse_agent.platform_v1.autonomy import AutonomyService
        from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
        autonomy = AutonomyService(
            control_store=control, capabilities=CapabilityRegistry()
        )
        window = autonomy.activate(self._window_payload())

        # Now point REVERSE_AGENT_REPO_DIR to a DIFFERENT repo
        repo_b = _git_init_repo(
            tmp_path / "repo_b", "https://github.com/owner/repoB.git"
        )
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo_b))

        from reverse_agent.platform_v1.run_store import TaskStoreError
        with pytest.raises(TaskStoreError, match="goal_repository_workspace_mismatch"):
            goals.launch(goal.id, expected_revision=1, window_id=window.id)

        # Verify no tasks were materialized
        assert store.count_tasks() == 0
        updated_goal = control.get_goal(goal.id)
        assert updated_goal.status != "RUNNING"

    def test_goal_launch_match_continues(self, tmp_path: Path, monkeypatch) -> None:
        repo = _git_init_repo(tmp_path / "repo_a", "https://github.com/owner/repoA.git")
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo))
        store, control, goals = self._services(tmp_path)

        goal = goals.create({
            "objective": "Test goal launch match",
            "repository": "owner/repoA",
            "idempotency_key": "goal-match-v1",
            "executor_kind": "opencode",
            "orchestration_mode": "sequential_team",
        })
        goals.plan(goal.id, expected_revision=1)
        goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")

        from reverse_agent.platform_v1.autonomy import AutonomyService
        from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
        autonomy = AutonomyService(
            control_store=control, capabilities=CapabilityRegistry()
        )
        window = autonomy.activate(self._window_payload())

        running = goals.launch(goal.id, expected_revision=1, window_id=window.id)
        assert running.status == "RUNNING"
        assert store.count_tasks() > 0


class TestTaskExecutionMismatch:
    """Test that ordinary task execution blocks on repository/workspace mismatch."""

    def test_execution_mismatch_zero_executor_calls(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from reverse_agent.platform_v1.run_store import TaskStore
        from reverse_agent.platform_v1.task_execution import (
            TaskExecutionOutcome,
            TaskExecutionService,
        )
        from reverse_agent.platform_v1.task_runtime import ExecutorRouter

        repo_a = _git_init_repo(
            tmp_path / "repo_a", "https://github.com/owner/repoA.git"
        )
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo_a))

        store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
        task = store.create_task(
            title="exec-test",
            repository="owner/repoB",
            executor_kind="opencode",
            orchestration_mode="single",
        )

        call_count = 0

        class FakeExecutor:
            def __init__(self, **kwargs: Any) -> None:
                nonlocal call_count
                call_count += 1

        router = ExecutorRouter()
        router._executors = {"opencode": FakeExecutor}
        service = TaskExecutionService(store=store, router=router)

        outcome = service.execute(task.id, workspace_root=str(tmp_path / "ws"))
        assert outcome.success is False
        assert "repository_workspace_mismatch" in (
            outcome.failure_detail or ""
        )
        assert call_count == 0


class TestDurableExecutionMismatch:
    """Test that durable first-run blocks on repository/workspace mismatch."""

    def test_durable_first_run_mismatch_zero_calls(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from reverse_agent.platform_v1.durable_execution import (
            DurableExecutionService,
        )
        from reverse_agent.platform_v1.run_store import TaskStore
        from reverse_agent.platform_v1.task_execution import (
            TaskExecutionError,
        )
        from reverse_agent.platform_v1.task_runtime import ExecutorRouter

        repo_a = _git_init_repo(
            tmp_path / "repo_a", "https://github.com/owner/repoA.git"
        )
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo_a))

        store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
        task = store.create_task(
            title="durable-test",
            repository="owner/repoB",
            executor_kind="opencode",
            orchestration_mode="single",
        )

        router = ExecutorRouter()
        service = DurableExecutionService(
            store=store,
            router=router,
            execution_authority_sha="auth-sha-1",
            planning_sha="plan-sha-1",
        )

        with pytest.raises(TaskExecutionError, match="repository_workspace_mismatch"):
            service.execute_durable_single(
                task.id,
                workspace_root=str(tmp_path / "ws"),
            )


class TestDurableResumeRevalidation:
    """Test that resume revalidates the current source binding."""

    def test_resume_after_source_change_blocked(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from reverse_agent.platform_v1.durable_execution import (
            DurableExecutionService,
            DurableResumeError,
        )
        from reverse_agent.platform_v1.run_store import TaskStore
        from reverse_agent.platform_v1.task_runtime import ExecutorRouter

        repo_a = _git_init_repo(
            tmp_path / "repo_a", "https://github.com/owner/repoA.git"
        )
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo_a))

        store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
        task = store.create_task(
            title="resume-test",
            repository="owner/repoA",
            executor_kind="opencode",
            orchestration_mode="single",
        )

        router = ExecutorRouter()
        service = DurableExecutionService(
            store=store,
            router=router,
            execution_authority_sha="auth-sha-1",
            planning_sha="plan-sha-1",
        )

        # Start a durable run that will be interrupted
        try:
            service.execute_durable_single(
                task.id,
                workspace_root=str(tmp_path / "ws"),
            )
        except Exception:
            pass  # expected to fail if no real executor

        # Get the durable run ID directly from the database
        row = store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()
        assert row is not None, "durable run should have been created"
        run_id = row["run_id"]
        run_obj = store._get_durable_run(run_id)

        # Set task to INTERRUPTED so resume can find the active run
        store.set_state(task.id, "INTERRUPTED")
        store._set_recovery_classification(run_id, "interrupted", "task-api", 1)

        # Now change REVERSE_AGENT_REPO_DIR to point to a different repo
        repo_b = _git_init_repo(
            tmp_path / "repo_b", "https://github.com/owner/repoB.git"
        )
        monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo_b))

        with pytest.raises(DurableResumeError, match="repository_workspace_mismatch"):
            service.resume_single(
                task.id,
                workspace_root=str(tmp_path / "ws"),
                execution_authority_sha="auth-sha-1",
                planning_sha="plan-sha-1",
            )
