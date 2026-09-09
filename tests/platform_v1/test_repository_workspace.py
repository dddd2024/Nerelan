from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from reverse_agent.platform_v1.repository_workspace import (
    RepositoryWorkspaceError,
    normalize_github_origin,
    normalize_repository_identity,
    resolve_repository_workspace,
)


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    return completed.stdout.strip()


def _repo(tmp_path: Path, *, origin: str | None = "https://github.com/owner/A.git") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    if origin is not None:
        _git(repo, "remote", "add", "origin", origin)
    return repo


@pytest.mark.parametrize(
    "origin",
    [
        "https://github.com/owner/repo.git",
        "https://github.com/owner/repo",
        "ssh://git@github.com/owner/repo.git",
        "ssh://git@github.com/owner/repo",
        "git@github.com:owner/repo.git",
        "git@github.com:owner/repo",
    ],
)
def test_common_github_origin_forms_normalize_without_network(origin: str) -> None:
    assert normalize_github_origin(origin) == "owner/repo"


@pytest.mark.parametrize(
    "origin",
    [
        "https://gitlab.com/owner/repo.git",
        "https://user:secret@github.com/owner/repo.git",
        "ssh://other@github.com/owner/repo.git",
        "https://github.com/owner/repo/extra.git",
        "https://github.com/owner/repo.git?token=secret",
        "file:///tmp/repo",
        "owner/repo",
        "",
    ],
)
def test_unsupported_or_credential_bearing_origins_fail_closed(origin: str) -> None:
    with pytest.raises(ValueError):
        normalize_github_origin(origin)


def test_task_goal_repository_identity_requires_exact_owner_repo_form() -> None:
    assert normalize_repository_identity("owner/repo") == "owner/repo"
    with pytest.raises(ValueError):
        normalize_repository_identity("https://github.com/owner/repo")
    with pytest.raises(ValueError):
        normalize_repository_identity("repo")


def test_matching_configured_repository_returns_proven_git_root(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    nested = repo / "nested"
    nested.mkdir()

    binding = resolve_repository_workspace("owner/A", source_dir=nested)

    assert binding.repository == "owner/A"
    assert binding.repo_dir == repo.resolve()


def test_repository_mismatch_is_stable_sanitized_and_precedes_fallback(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin="git@github.com:owner/A.git")

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/B", source_dir=repo)

    assert caught.value.code == "repository_workspace_mismatch"
    assert str(caught.value) == "repository_workspace_mismatch"
    assert "github.com" not in str(caught.value)
    assert str(repo) not in str(caught.value)


def test_missing_configuration_never_falls_back_to_process_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/A", environ={})

    assert caught.value.code == "repository_workspace_unconfigured"


@pytest.mark.parametrize("kind", ["missing", "file", "directory"])
def test_invalid_source_directory_fails_closed(tmp_path: Path, kind: str) -> None:
    if kind == "missing":
        source = tmp_path / "does-not-exist"
    elif kind == "file":
        source = tmp_path / "plain-file"
        source.write_text("not a repository", encoding="utf-8")
    else:
        source = tmp_path / "plain-directory"
        source.mkdir()

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/A", source_dir=source)

    assert caught.value.code == "repository_workspace_invalid"


def test_missing_origin_is_identity_unavailable(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin=None)

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/A", source_dir=repo)

    assert caught.value.code == "repository_workspace_identity_unavailable"


def test_unsupported_origin_is_identity_unavailable_without_leaking_remote(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin="https://example.invalid/secret-owner/secret-repo.git")

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("owner/A", source_dir=repo)

    assert caught.value.code == "repository_workspace_identity_unavailable"
    assert str(caught.value) == "repository_workspace_identity_unavailable"
    assert "secret-owner" not in str(caught.value)


def test_environment_binding_uses_only_reverse_agent_repo_dir(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin="ssh://git@github.com/owner/A.git")
    environment = {
        "REVERSE_AGENT_REPO_DIR": str(repo),
        "UNRELATED_REPOSITORY": str(tmp_path / "other"),
    }

    binding = resolve_repository_workspace("owner/A", environ=environment)

    assert binding.repository == "owner/A"
    assert binding.repo_dir == repo.resolve()


def test_current_slug_is_not_rewritten_to_historical_alias(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin="https://github.com/dddd2024/Nerelan.git")

    binding = resolve_repository_workspace("dddd2024/Nerelan", source_dir=repo)
    assert binding.repository == "dddd2024/Nerelan"

    with pytest.raises(RepositoryWorkspaceError) as caught:
        resolve_repository_workspace("dddd2024/reverse-agent", source_dir=repo)
    assert caught.value.code == "repository_workspace_mismatch"


# ---------------------------------------------------------------------------
# Integration tests: Goal launch, Task execution, Durable execution/resume
# ---------------------------------------------------------------------------


def _git_init_repo(path: Path, origin_url: str = "", marker: str = "") -> Path:
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


def test_goal_launch_mismatch_no_task_materialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Goal launch for an OpenCode Goal rejects a known repository/source mismatch
    before materializing task links or marking the Goal RUNNING."""
    from datetime import datetime, timedelta, timezone

    from reverse_agent.platform_v1.autonomy import AutonomyService
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    from reverse_agent.platform_v1.goal_service import GoalService
    from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError

    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)

    repo_a = _git_init_repo(tmp_path / "repo_a", "https://github.com/owner/repoA.git")
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo_a))

    goal = goals.create({
        "objective": "Test goal launch mismatch",
        "repository": "owner/repoA",
        "idempotency_key": "goal-mismatch-v1",
        "executor_kind": "opencode",
        "orchestration_mode": "sequential_team",
    })
    goals.plan(goal.id, expected_revision=1)
    goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")

    now = datetime.now(timezone.utc)
    window_payload = {
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
    autonomy = AutonomyService(
        control_store=control, capabilities=CapabilityRegistry()
    )
    window = autonomy.activate(window_payload)

    # Now point REVERSE_AGENT_REPO_DIR to a DIFFERENT repo
    repo_b = _git_init_repo(
        tmp_path / "repo_b", "https://github.com/owner/repoB.git"
    )
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo_b))

    with pytest.raises(TaskStoreError) as caught:
        goals.launch(goal.id, expected_revision=1, window_id=window.id)

    assert str(caught.value) == "repository_workspace_mismatch"

    assert store.count_tasks() == 0
    updated_goal = control.get_goal(goal.id)
    assert updated_goal.status != "RUNNING"


def test_goal_launch_match_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Goal launch with matching repository/workspace continues and materializes tasks."""
    from datetime import datetime, timedelta, timezone

    from reverse_agent.platform_v1.autonomy import AutonomyService
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    from reverse_agent.platform_v1.goal_service import GoalService
    from reverse_agent.platform_v1.run_store import TaskStore

    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)

    repo = _git_init_repo(tmp_path / "repo_a", "https://github.com/owner/repoA.git")
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo))

    goal = goals.create({
        "objective": "Test goal launch match",
        "repository": "owner/repoA",
        "idempotency_key": "goal-match-v1",
        "executor_kind": "opencode",
        "orchestration_mode": "sequential_team",
    })
    goals.plan(goal.id, expected_revision=1)
    goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")

    now = datetime.now(timezone.utc)
    window_payload = {
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
    autonomy = AutonomyService(
        control_store=control, capabilities=CapabilityRegistry()
    )
    window = autonomy.activate(window_payload)

    running = goals.launch(goal.id, expected_revision=1, window_id=window.id)
    assert running.status == "RUNNING"
    assert store.count_tasks() > 0


def test_execution_mismatch_zero_executor_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ordinary Task execution performs the same check before state/workspace
    side effects and records a blocked outcome through the existing failure path."""
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
    assert outcome.failure_detail == "repository_workspace_mismatch"
    assert call_count == 0


def test_durable_first_run_mismatch_zero_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Durable first execution performs the same check before executor
    creation/worktree preparation and preserves fencing/failure semantics."""
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

    with pytest.raises(TaskExecutionError) as caught:
        service.execute_durable_single(
            task.id,
            workspace_root=str(tmp_path / "ws"),
        )

    assert str(caught.value) == "repository_workspace_mismatch"


def test_resume_after_source_change_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Durable recovery/resume revalidates the current trusted-host source
    binding; changing the configured source repository after interruption
    cannot resume the old Task against a different repository."""
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

    # Start a durable run that will fail (no real executor)
    try:
        service.execute_durable_single(
            task.id,
            workspace_root=str(tmp_path / "ws"),
        )
    except Exception:
        pass

    # Get the durable run ID directly from the database
    row = store._conn.execute(
        "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    assert row is not None, "durable run should have been created"
    run_id = row["run_id"]

    # Set task to INTERRUPTED so resume can find the active run
    store.set_state(task.id, "INTERRUPTED")
    store._set_recovery_classification(run_id, "interrupted", "task-api", 1)

    # Now change REVERSE_AGENT_REPO_DIR to point to a different repo
    repo_b = _git_init_repo(
        tmp_path / "repo_b", "https://github.com/owner/repoB.git"
    )
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo_b))

    with pytest.raises(DurableResumeError) as caught:
        service.resume_single(
            task.id,
            workspace_root=str(tmp_path / "ws"),
            execution_authority_sha="auth-sha-1",
            planning_sha="plan-sha-1",
        )

    assert str(caught.value) == "repository_workspace_mismatch"


def test_execution_unconfigured_exact_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ordinary Task execution with missing REVERSE_AGENT_REPO_DIR fails with
    the exact stable code repository_workspace_unconfigured."""
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.task_execution import (
        TaskExecutionOutcome,
        TaskExecutionService,
    )
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    monkeypatch.delenv("REVERSE_AGENT_REPO_DIR", raising=False)

    store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    task = store.create_task(
        title="exec-unconfigured",
        repository="owner/repoA",
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
    assert outcome.failure_detail == "repository_workspace_unconfigured"
    assert call_count == 0


def test_durable_resume_unconfigured_exact_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Durable resume with missing REVERSE_AGENT_REPO_DIR fails with the exact
    stable code repository_workspace_unconfigured."""
    from reverse_agent.platform_v1.durable_execution import (
        DurableExecutionService,
        DurableResumeError,
    )
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    repo = _git_init_repo(
        tmp_path / "repo_a", "https://github.com/owner/repoA.git"
    )
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(repo))

    store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    task = store.create_task(
        title="resume-unconfigured",
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

    try:
        service.execute_durable_single(
            task.id,
            workspace_root=str(tmp_path / "ws"),
        )
    except Exception:
        pass

    row = store._conn.execute(
        "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    assert row is not None
    run_id = row["run_id"]
    store.set_state(task.id, "INTERRUPTED")
    store._set_recovery_classification(run_id, "interrupted", "task-api", 1)

    monkeypatch.delenv("REVERSE_AGENT_REPO_DIR", raising=False)

    with pytest.raises(DurableResumeError) as caught:
        service.resume_single(
            task.id,
            workspace_root=str(tmp_path / "ws"),
            execution_authority_sha="auth-sha-1",
            planning_sha="plan-sha-1",
        )

    assert str(caught.value) == "repository_workspace_unconfigured"
