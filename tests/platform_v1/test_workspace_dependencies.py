"""Host-owned provisioning of Node dependencies inside a task workspace (#1503).

A task workspace is a fresh linked Git worktree, so ``node_modules`` is
absent and an ``npm_test`` check fails with "vitest is not recognized"
before any product code is read. These tests cover the shared helper and the
workspace-preparation wiring that closes that gap.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import functional_validation as fv
from reverse_agent.platform_v1 import workspace_dependencies as wd
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args],
                                   encoding="utf-8").strip()


def _frontend_project(root: Path, *, lockfile: str = "lock-v1") -> None:
    """A minimal Node workspace with a pinned lockfile."""
    frontend = root / "frontend"
    frontend.mkdir(parents=True, exist_ok=True)
    (frontend / "package.json").write_text(
        json.dumps({"name": "fixture", "private": True,
                    "scripts": {"test": "vitest run"}}), encoding="utf-8")
    (frontend / "package-lock.json").write_text(lockfile, encoding="utf-8")
    (frontend / ".gitignore").write_text("node_modules\n", encoding="utf-8")


@pytest.fixture
def repository(tmp_path):
    """A Git repository with a frontend Node workspace, committed at base."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Dependency fixture")
    git(root, "remote", "add", "origin", "https://github.com/owner/sample.git")
    _frontend_project(root)
    git(root, "add", "--", "frontend")
    git(root, "commit", "-q", "-m", "frozen frontend fixture")
    base = git(root, "rev-parse", "HEAD")
    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    task = store.create_task(title="Implement frontend change",
                             repository="owner/sample", executor_kind="opencode")
    goal = SimpleNamespace(id="goal-deps", revision=1, artifact_digest="a" * 64)
    yield root, base, store, task
    store._conn.close()


def _freeze(store, task, checks, base):
    plan = SimpleNamespace(id="T001", capability="execute_task", validation_checks=checks)
    goal = SimpleNamespace(id="goal-deps", revision=1, artifact_digest="a" * 64)
    fv.freeze_contract(store, task, goal=goal, plan_task=plan, base_commit=base)


def _fake_runner(calls, *, exit_code=0, timed_out=False):
    """A stand-in for the npm install that records the exact command."""

    def runner(command, cwd, env, timeout):
        calls.append({"command": list(command), "cwd": Path(cwd),
                      "env": dict(env), "timeout": timeout})
        return {"exit_code": exit_code, "timed_out": timed_out, "duration_ms": 1,
                "output_digest": "0" * 64, "output_bytes": 0}

    return runner


# ---------------------------------------------------------------------------
# The plan
# ---------------------------------------------------------------------------


def test_npm_test_profile_needs_dependencies_and_pytest_does_not():
    plan = wd.dependency_plan_from_checks(
        [{"profile_id": "npm_test", "working_directory": "frontend"}],
        base_commit="a" * 40)
    assert plan.directories == ("frontend",)
    assert plan.base_commit == "a" * 40

    empty = wd.dependency_plan_from_checks(
        [{"profile_id": "python_pytest", "working_directory": "."}],
        base_commit="a" * 40)
    assert empty.directories == ()
    assert not empty


def test_a_plan_without_node_checks_never_runs_npm(repository):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "python_pytest", "working_directory": "."}], base)
    plan = wd.task_dependency_plan(store, task.id)
    assert plan.directories == ()

    calls: list[dict] = []
    document = wd.provision_workspace_dependencies(
        store, task.id, plan, root, runner=_fake_runner(calls))
    assert document["status"] == "NOT_REQUIRED"
    assert calls == []
    assert wd.dependency_evidence(store.get_task(task.id)) == []


def test_dependency_plan_reads_the_frozen_contract(repository):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)
    assert plan.directories == ("frontend",)
    assert plan.base_commit == base


def test_dependency_plan_is_empty_without_a_contract(repository):
    root, base, store, task = repository
    plan = wd.task_dependency_plan(store, task.id)
    assert plan.directories == ()


@pytest.mark.parametrize("directory", ["../escape", "/absolute", "a\\b", "a//b",
                                       "@opts", "", "a/../b"])
def test_unsafe_dependency_directories_are_rejected(directory):
    with pytest.raises(TaskStoreError):
        wd.normalize_dependency_directory(directory)


# ---------------------------------------------------------------------------
# The install
# ---------------------------------------------------------------------------


def test_install_runs_npm_ci_from_the_base_lockfile_with_ignore_scripts(repository):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    calls: list[dict] = []
    document = wd.provision_workspace_dependencies(
        store, task.id, plan, root, runner=_fake_runner(calls))

    assert document["status"] == "INSTALLED"
    assert len(calls) == 1
    command = calls[0]["command"]
    assert "ci" in command
    assert "--ignore-scripts" in command
    assert "--no-audit" in command
    assert "--no-fund" in command
    assert calls[0]["cwd"] == (root / "frontend").resolve()


def test_install_ignores_the_agent_tree_and_uses_the_base_lockfile(repository):
    """The agent's own lockfile cannot influence the preparation install."""
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    (root / "frontend" / "package-lock.json").write_text("agent-lock", encoding="utf-8")
    plan = wd.task_dependency_plan(store, task.id)

    calls: list[dict] = []
    wd.provision_workspace_dependencies(
        store, task.id, plan, root, runner=_fake_runner(calls))

    restored = (root / "frontend" / "package-lock.json").read_text(encoding="utf-8")
    assert restored == "lock-v1"
    assert calls[0]["command"][-1] == "--no-fund"


def test_install_records_its_own_evidence_row(repository):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    wd.provision_workspace_dependencies(
        store, task.id, plan, root, runner=_fake_runner([]))

    rows = wd.dependency_evidence(store.get_task(task.id))
    assert len(rows) == 1
    document = json.loads(rows[0]["detail"])
    assert document["status"] == "INSTALLED"
    entry = document["directories"][0]
    assert entry["directory"] == "frontend"
    assert entry["lockfile_digest"] == hashlib.sha256(b"lock-v1").hexdigest()
    assert entry["lockfile_source"] == "base"
    assert wd.installed_lockfile_digests(store.get_task(task.id)) == {
        "frontend": hashlib.sha256(b"lock-v1").hexdigest()}


def test_failed_install_is_a_host_fault_not_a_model_failure(repository):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    calls: list[dict] = []
    with pytest.raises(wd.WorkspaceDependencyError) as caught:
        wd.provision_workspace_dependencies(
            store, task.id, plan, root, runner=_fake_runner(calls, exit_code=1))

    assert caught.value.code == "workspace_dependencies_unavailable"
    assert str(caught.value) == "workspace_dependencies_unavailable"
    rows = wd.dependency_evidence(store.get_task(task.id))
    assert len(rows) == 1
    document = json.loads(rows[0]["detail"])
    assert document["status"] == "FAILED"
    assert document["failure"] == "workspace_dependencies_unavailable"


def test_timed_out_install_is_a_host_fault(repository):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    with pytest.raises(wd.WorkspaceDependencyError):
        wd.provision_workspace_dependencies(
            store, task.id, plan, root, runner=_fake_runner([], timed_out=True))


def test_a_missing_lockfile_blocks_instead_of_installing(repository):
    """Without a lockfile there is nothing to install from, so the step blocks."""
    root, base, store, task = repository
    (root / "frontend" / "package-lock.json").unlink()
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    calls: list[dict] = []
    with pytest.raises(wd.WorkspaceDependencyError):
        wd.provision_workspace_dependencies(
            store, task.id, plan, root, runner=_fake_runner(calls),
            lockfile_source="workspace")
    assert calls == []


def test_the_base_lockfile_is_restored_when_the_agent_deleted_it(repository):
    root, base, store, task = repository
    (root / "frontend" / "package-lock.json").unlink()
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    wd.provision_workspace_dependencies(
        store, task.id, plan, root, runner=_fake_runner([]))
    restored = (root / "frontend" / "package-lock.json").read_text(encoding="utf-8")
    assert restored == "lock-v1"


def test_the_install_environment_carries_no_credentials(repository, monkeypatch):
    root, base, store, task = repository
    monkeypatch.setenv("OPENAI_API_KEY", "isolated-test-sentinel")
    monkeypatch.setenv("GITHUB_TOKEN", "isolated-test-sentinel")
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    calls: list[dict] = []
    wd.provision_workspace_dependencies(
        store, task.id, plan, root, runner=_fake_runner(calls))

    env = calls[0]["env"]
    assert "OPENAI_API_KEY" not in env and "GITHUB_TOKEN" not in env
    assert env["CI"] == "true"
    assert env["NPM_CONFIG_IGNORE_SCRIPTS"] == "true"
    assert env["NPM_CONFIG_AUDIT"] == "false"
    assert env["NPM_CONFIG_FUND"] == "false"
    # The install may reach the registry; the check itself stays offline.
    assert env["NPM_CONFIG_OFFLINE"] == "false"


def test_the_install_uses_a_private_npm_configuration(repository):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    seen: list[dict] = []

    def runner(command, cwd, env, timeout):
        user = Path(env["NPM_CONFIG_USERCONFIG"])
        global_config = Path(env["NPM_CONFIG_GLOBALCONFIG"])
        seen.append({"user": user, "global": global_config,
                     "user_text": user.read_text(encoding="utf-8"),
                     "global_text": global_config.read_text(encoding="utf-8")})
        return {"exit_code": 0, "timed_out": False, "duration_ms": 1,
                "output_digest": "0" * 64, "output_bytes": 0}

    wd.provision_workspace_dependencies(store, task.id, plan, root, runner=runner)

    assert len(seen) == 1
    assert seen[0]["user"] != seen[0]["global"]
    assert seen[0]["user_text"] == "" and seen[0]["global_text"] == ""


# ---------------------------------------------------------------------------
# The workspace-preparation wiring
# ---------------------------------------------------------------------------


def test_workspace_preparation_installs_dependencies_once_from_the_base_lockfile(
        repository, monkeypatch):
    """A plan with an npm_test check installs before the executor starts."""
    from reverse_agent.platform_v1.repository_preparation import prepare_linked_worktree
    from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError

    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    monkeypatch.setattr(wd, "_run_install",
                        lambda command, cwd, env, timeout: _fake_runner(calls)(
                            command, cwd, env, timeout))

    workspace_root = root.parent / "task_workspaces"
    workspace_root.mkdir()
    worktree, base_sha = prepare_linked_worktree(
        task.id, workspace_root, None,
        repo_dir_value=str(root), base_ref=base,
        dependencies=plan, dependency_store=store,
    )

    assert base_sha == base
    assert len(calls) == 1
    assert "--ignore-scripts" in calls[0]["command"]
    rows = wd.dependency_evidence(store.get_task(task.id))
    assert len(rows) == 1
    assert json.loads(rows[0]["detail"])["status"] == "INSTALLED"


def test_a_failed_install_blocks_the_step_with_the_stable_code(repository, monkeypatch):
    from reverse_agent.platform_v1.repository_preparation import prepare_linked_worktree
    from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError

    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    monkeypatch.setattr(wd, "_run_install",
                        lambda command, cwd, env, timeout: _fake_runner(calls, exit_code=1)(
                            command, cwd, env, timeout))

    workspace_root = root.parent / "task_workspaces"
    workspace_root.mkdir()
    with pytest.raises(ExecutorRuntimeError) as caught:
        prepare_linked_worktree(
            task.id, workspace_root, None,
            repo_dir_value=str(root), base_ref=base,
            dependencies=plan, dependency_store=store,
        )

    assert str(caught.value) == "workspace_dependencies_unavailable"


def test_workspace_preparation_without_node_checks_runs_no_npm(repository, monkeypatch):
    from reverse_agent.platform_v1.repository_preparation import prepare_linked_worktree

    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "python_pytest", "working_directory": "."}], base)
    plan = wd.task_dependency_plan(store, task.id)
    assert plan.directories == ()

    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: calls.append({"argv": True}) or ["npm", "ci"])

    workspace_root = root.parent / "task_workspaces"
    workspace_root.mkdir()
    prepare_linked_worktree(
        task.id, workspace_root, None,
        repo_dir_value=str(root), base_ref=base,
        dependencies=plan, dependency_store=store,
    )

    assert calls == []
    assert wd.dependency_evidence(store.get_task(task.id)) == []


def test_workspace_preparation_without_a_plan_runs_no_npm(repository, monkeypatch):
    from reverse_agent.platform_v1.repository_preparation import prepare_linked_worktree

    root, base, store, task = repository
    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: calls.append({"argv": True}) or ["npm", "ci"])

    workspace_root = root.parent / "task_workspaces"
    workspace_root.mkdir()
    prepare_linked_worktree(
        task.id, workspace_root, None,
        repo_dir_value=str(root), base_ref=base,
    )

    assert calls == []


def test_the_install_leaves_the_workspace_tree_unchanged(repository, monkeypatch):
    """node_modules is not tracked, so the artifact proof still holds."""
    from reverse_agent.platform_v1.repository_preparation import prepare_linked_worktree

    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)

    def _install(command, cwd, env, timeout):
        Path(cwd, "node_modules").mkdir(exist_ok=True)
        Path(cwd, "node_modules", "vitest").write_text("{}", encoding="utf-8")
        return {"exit_code": 0, "timed_out": False, "duration_ms": 1,
                "output_digest": "0" * 64, "output_bytes": 0}

    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    monkeypatch.setattr(wd, "_run_install", _install)

    workspace_root = root.parent / "task_workspaces"
    workspace_root.mkdir()
    worktree, _ = prepare_linked_worktree(
        task.id, workspace_root, None,
        repo_dir_value=str(root), base_ref=base,
        dependencies=plan, dependency_store=store,
    )

    assert (Path(worktree) / "frontend" / "node_modules" / "vitest").is_file()
    status = subprocess.run(["git", "-C", str(worktree), "status", "--porcelain=v1",
                             "--untracked-files=all"], capture_output=True, text=True,
                            check=True).stdout.strip()
    assert status == ""


# ---------------------------------------------------------------------------
# The functional check
# ---------------------------------------------------------------------------


def test_the_check_reuses_the_preparation_install(repository, monkeypatch):
    """A workspace whose lockfile did not change is not reinstalled."""
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)
    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    monkeypatch.setattr(wd, "_run_install",
                        lambda command, cwd, env, timeout: _fake_runner(calls)(
                            command, cwd, env, timeout))
    wd.provision_workspace_dependencies(
        store, task.id, plan, root, runner=_fake_runner([]))
    (root / "frontend" / "node_modules").mkdir(exist_ok=True)

    context = fv._dependency_context(store, store.get_task(task.id), base, None,
                                     [{"profile_id": "npm_test", "working_directory": "frontend"}])
    assert context is not None
    fv._ensure_check_dependencies(
        {"profile_id": "npm_test", "working_directory": "frontend"}, root, context)
    assert calls == []


def test_the_check_reprovisions_when_the_agent_changed_the_lockfile(repository, monkeypatch):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)
    wd.provision_workspace_dependencies(
        store, task.id, plan, root, runner=_fake_runner([]))
    (root / "frontend" / "node_modules").mkdir(exist_ok=True)
    (root / "frontend" / "package-lock.json").write_text("agent-lock", encoding="utf-8")

    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    monkeypatch.setattr(wd, "_run_install",
                        lambda command, cwd, env, timeout: _fake_runner(calls)(
                            command, cwd, env, timeout))

    context = fv._dependency_context(store, store.get_task(task.id), base, None,
                                     [{"profile_id": "npm_test", "working_directory": "frontend"}])
    fv._ensure_check_dependencies(
        {"profile_id": "npm_test", "working_directory": "frontend"}, root, context)

    assert len(calls) == 1
    rows = wd.dependency_evidence(store.get_task(task.id))
    document = json.loads(rows[-1]["detail"])
    assert document["status"] == "INSTALLED"
    assert document["directories"][0]["lockfile_source"] == "workspace"
    assert document["directories"][0]["lockfile_digest"] == hashlib.sha256(
        b"agent-lock").hexdigest()


def test_the_check_without_a_dependency_context_never_installs(repository, monkeypatch):
    root, base, store, task = repository
    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: calls.append({"argv": True}) or ["npm", "ci"])
    fv._ensure_check_dependencies(
        {"profile_id": "npm_test", "working_directory": "frontend"}, root, None)
    assert calls == []


def test_a_plan_without_node_checks_has_no_check_context(repository):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "python_pytest", "working_directory": "."}], base)
    assert fv._dependency_context(store, store.get_task(task.id), base, None,
                                  [{"profile_id": "python_pytest", "working_directory": "."}]) is None
