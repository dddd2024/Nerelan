"""Host-owned provisioning of Node dependencies inside a task workspace (#1503).

A task workspace is a fresh linked Git worktree, so ``node_modules`` is
absent and an ``npm_test`` check fails with "vitest is not recognized"
before any product code is read. These tests cover the shared helper and the
workspace-preparation wiring that closes that gap.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

import test_goal_functional_checks as goal_fixture
from test_goal_functional_checks import goal_checks  # noqa: F401 - fixture
from test_functional_execution import LocalImplementation, durable, ordinary
from reverse_agent.platform_v1 import functional_validation as fv
from reverse_agent.platform_v1 import workspace_dependencies as wd
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter


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


# A stand-in "vitest": the genuine runner (what npm ci installs) reports the
# agent's test file honestly; the agent-planted one always reports a pass.
_GENUINE_VITEST = """
import sys
from pathlib import Path
out = next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--outputFile="))
failing = "FAIL" in Path("sum.test.txt").read_text(encoding="utf-8")
case = '<testcase classname="sum" name="adds"><failure message="boom">boom</failure></testcase>' if failing else '<testcase classname="sum" name="adds"/>'
Path(out).write_text('<testsuite tests="1">' + case + '</testsuite>', encoding="utf-8")
"""
_POISONED_VITEST = """
import sys
from pathlib import Path
out = next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--outputFile="))
Path(out).write_text('<testsuite tests="1"><testcase classname="sum" name="adds"/></testsuite>', encoding="utf-8")
"""
# "npm test": runs whatever node_modules/.bin/vitest.py the workspace holds.
_FAKE_NPM = """
import runpy, sys
sys.argv = ["vitest", *sys.argv[1:]]
runpy.run_path("node_modules/.bin/vitest.py", run_name="__main__")
"""


def _genuine_install(calls):
    """A fake npm ci: records whether node_modules existed, then installs fresh."""

    def install(command, cwd, env, timeout):
        modules = Path(cwd) / "node_modules"
        calls.append({"command": list(command), "had_node_modules":
                      modules.exists() or wd._is_link(modules)})
        (modules / ".bin").mkdir(parents=True)
        (modules / ".bin" / "vitest.py").write_text(_GENUINE_VITEST, encoding="utf-8")
        (modules / "vitest").mkdir()
        (modules / "vitest" / "index.js").write_text("genuine", encoding="utf-8")
        return {"exit_code": 0, "timed_out": False, "duration_ms": 1,
                "output_digest": "0" * 64, "output_bytes": 0, "cleanup": "confirmed"}

    return install


def _make_dir_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       check=True, capture_output=True)
    else:
        link.symlink_to(target, target_is_directory=True)


@pytest.mark.parametrize("state", ["tampered_shim", "tampered_dependency_source",
                                   "partial_install", "missing_install"])
def test_the_check_never_trusts_the_agent_writable_install(repository, monkeypatch, tmp_path, state):
    """#1557 review P1: an unchanged lockfile plus an existing node_modules is not proof.

    The preparation install is recorded with the same lockfile digest the
    workspace still has; the agent then tampers with the ignored tree. The
    check must install afresh, so nothing the agent left behind survives.
    """
    root, base, store, task = repository
    checks = [{"profile_id": "npm_test", "working_directory": "frontend"}]
    _freeze(store, task, checks, base)
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    wd.provision_workspace_dependencies(store, task.id, wd.task_dependency_plan(store, task.id),
                                        root, runner=_genuine_install([]))
    modules = root / "frontend" / "node_modules"
    if state == "tampered_shim":
        (modules / ".bin" / "vitest.py").write_text(_POISONED_VITEST, encoding="utf-8")
    elif state == "tampered_dependency_source":
        (modules / "vitest" / "index.js").write_text("poisoned", encoding="utf-8")
    elif state == "partial_install":
        (modules / ".bin" / "vitest.py").unlink()
    else:
        shutil.rmtree(modules)

    calls: list[dict] = []
    monkeypatch.setattr(wd, "_run_install", _genuine_install(calls))
    context = fv._dependency_context(store, store.get_task(task.id), base, None, checks)
    # The digest the old fast path trusted still matches the workspace lockfile.
    assert context.installed["frontend"] == hashlib.sha256(b"lock-v1").hexdigest()
    fv._ensure_check_dependencies(checks[0], root, context)

    assert len(calls) == 1 and calls[0]["had_node_modules"] is False
    assert (modules / ".bin" / "vitest.py").read_text(encoding="utf-8") == _GENUINE_VITEST
    assert (modules / "vitest" / "index.js").read_text(encoding="utf-8") == "genuine"
    entry = json.loads(wd.dependency_evidence(store.get_task(task.id))[-1]["detail"])["directories"][0]
    assert entry["fresh_install"] is True and entry["lockfile_source"] == "workspace"
    assert entry["previous_lockfile_digest"] == entry["lockfile_digest"]


def test_a_poisoned_runner_cannot_make_a_failing_test_pass(repository, monkeypatch, tmp_path):
    """The reviewer's counterexample end to end through the real _run_check."""
    root, base, store, task = repository
    checks = [{"profile_id": "npm_test", "working_directory": "frontend"}]
    _freeze(store, task, checks, base)
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "npm.py").write_text(_FAKE_NPM, encoding="utf-8")
    monkeypatch.setattr(fv, "_resolved_argv", lambda profile: [sys.executable, str(tools / "npm.py")])
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    wd.provision_workspace_dependencies(store, task.id, wd.task_dependency_plan(store, task.id),
                                        root, runner=_genuine_install([]))
    # The agent adds a failing test and swaps in a runner that only reports a pass.
    (root / "frontend" / "sum.test.txt").write_text("FAIL", encoding="utf-8")
    (root / "frontend" / "node_modules" / ".bin" / "vitest.py").write_text(
        _POISONED_VITEST, encoding="utf-8")
    poisoned = fv._run_check(checks[0], root)  # without host provisioning
    assert poisoned["test_report"]["accepted"] is True, "fixture must reproduce the attack"
    (root / "frontend" / "node_modules" / ".bin" / "vitest.py").write_text(
        _POISONED_VITEST, encoding="utf-8")

    monkeypatch.setattr(wd, "_run_install", _genuine_install([]))
    context = fv._dependency_context(store, store.get_task(task.id), base, None, checks)
    observed = fv._run_check(checks[0], root, dependencies=context)

    assert observed["test_report"]["failed"] == 1
    assert observed["test_report"]["accepted"] is False


def test_a_node_modules_junction_is_removed_not_followed(repository, monkeypatch, tmp_path):
    root, base, store, task = repository
    checks = [{"profile_id": "npm_test", "working_directory": "frontend"}]
    _freeze(store, task, checks, base)
    outside = tmp_path / "outside-modules"
    outside.mkdir()
    (outside / "sentinel.txt").write_text("keep", encoding="utf-8")
    _make_dir_link(root / "frontend" / "node_modules", outside)

    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    monkeypatch.setattr(wd, "_run_install", _genuine_install(calls))
    context = fv._dependency_context(store, store.get_task(task.id), base, None, checks)
    fv._ensure_check_dependencies(checks[0], root, context)

    assert (outside / "sentinel.txt").read_text(encoding="utf-8") == "keep"
    assert not (outside / ".bin").exists()
    assert calls[0]["had_node_modules"] is False
    modules = root / "frontend" / "node_modules"
    assert not wd._is_link(modules) and (modules / ".bin" / "vitest.py").is_file()


# A runner that resolves its assertion library the way Node and Vite resolve a
# bare import: from the importing (test) file's directory upward.
_RESOLVING_VITEST = """
import runpy, sys
from pathlib import Path
out = next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--outputFile="))
test = Path("src/sum.test.txt")
library = None
for folder in (test.parent.resolve(), *test.parent.resolve().parents):
    candidate = folder / "node_modules" / "chai" / "index.py"
    if candidate.is_file():
        library = runpy.run_path(str(candidate))
        break
failing = not library["verdict"](test.read_text(encoding="utf-8"))
case = '<testcase classname="sum" name="adds"><failure message="boom">boom</failure></testcase>' if failing else '<testcase classname="sum" name="adds"/>'
Path(out).write_text('<testsuite tests="1">' + case + '</testsuite>', encoding="utf-8")
"""
_GENUINE_CHAI = "def verdict(text):\n    return 'FAIL' not in text\n"
_POISONED_CHAI = "def verdict(text):\n    return True\n"


def _resolving_install(calls):
    def install(command, cwd, env, timeout):
        modules = Path(cwd) / "node_modules"
        calls.append({"command": list(command)})
        (modules / ".bin").mkdir(parents=True)
        (modules / ".bin" / "vitest.py").write_text(_RESOLVING_VITEST, encoding="utf-8")
        (modules / "chai").mkdir()
        (modules / "chai" / "index.py").write_text(_GENUINE_CHAI, encoding="utf-8")
        return {"exit_code": 0, "timed_out": False, "duration_ms": 1,
                "output_digest": "0" * 64, "output_bytes": 0, "cleanup": "confirmed"}

    return install


def _plant_chai(folder: Path) -> None:
    (folder / "chai").mkdir(parents=True)
    (folder / "chai" / "index.py").write_text(_POISONED_CHAI, encoding="utf-8")


@pytest.mark.parametrize("placement", ["nested", "deeply_nested", "nested_junction", "workspace_root"])
def test_a_nested_node_modules_cannot_shadow_the_fresh_install(
        repository, monkeypatch, tmp_path, placement):
    """#1557 review on 3078fcbf: an ignored frontend/src/node_modules forged a pass.

    Bare imports resolve from the importing file's directory upward, so a
    planted node_modules below the check directory wins over the host's
    install, and .gitignore keeps it out of the diff. Every node_modules in
    the workspace is removed (a junction unlinked, never followed).
    """
    root, base, store, task = repository
    checks = [{"profile_id": "npm_test", "working_directory": "frontend"}]
    _freeze(store, task, checks, base)
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "npm.py").write_text(_FAKE_NPM, encoding="utf-8")
    monkeypatch.setattr(fv, "_resolved_argv", lambda profile: [sys.executable, str(tools / "npm.py")])
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    wd.provision_workspace_dependencies(store, task.id, wd.task_dependency_plan(store, task.id),
                                        root, runner=_resolving_install([]))
    source = root / "frontend" / "src"
    source.mkdir()
    (source / "sum.test.txt").write_text("FAIL", encoding="utf-8")
    outside = tmp_path / "outside-modules"
    planted = {"nested": source / "node_modules",
               "deeply_nested": source / "deep" / "node_modules",
               "nested_junction": source / "node_modules",
               "workspace_root": root / "node_modules"}[placement]
    if placement == "nested_junction":
        _plant_chai(outside)
        (outside / "sentinel.txt").write_text("keep", encoding="utf-8")
        _make_dir_link(planted, outside)
    else:
        _plant_chai(planted)
    if placement in {"nested", "deeply_nested"}:
        ignored = git(root, "status", "--porcelain=v1", "--ignored", "--", str(planted))
        assert ignored.startswith("!!"), "the planted tree must be ignored, i.e. outside the diff"
    if placement in {"nested", "nested_junction"}:
        attacked = fv._run_check(checks[0], root)  # no host provisioning: the attack works
        assert attacked["test_report"]["accepted"] is True

    calls: list[dict] = []
    monkeypatch.setattr(wd, "_run_install", _resolving_install(calls))
    context = fv._dependency_context(store, store.get_task(task.id), base, None, checks)
    observed = fv._run_check(checks[0], root, dependencies=context)

    assert len(calls) == 1
    assert observed["test_report"]["failed"] == 1 and observed["test_report"]["accepted"] is False
    assert not planted.exists() and not wd._is_link(planted)
    if placement == "nested_junction":
        assert (outside / "sentinel.txt").read_text(encoding="utf-8") == "keep"
        assert (outside / "chai" / "index.py").is_file()
    entry = json.loads(wd.dependency_evidence(store.get_task(task.id))[-1]["detail"])["directories"][0]
    assert entry["node_modules_removed"] == 2  # the previous install and the planted tree


def test_an_ignored_package_manifest_refuses_the_check(repository, monkeypatch):
    """An ignored package.json could remap imports/exports/type outside the diff."""
    root, base, store, task = repository
    checks = [{"profile_id": "npm_test", "working_directory": "frontend"}]
    _freeze(store, task, checks, base)
    generated = root / "frontend" / "src" / "generated"
    generated.mkdir(parents=True)
    (generated / "package.json").write_text('{"imports": {"#chai": "./chai.js"}}', encoding="utf-8")
    with (root / ".git" / "info" / "exclude").open("a", encoding="utf-8") as handle:
        handle.write("frontend/src/generated/\n")
    calls: list[dict] = []
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    monkeypatch.setattr(wd, "_run_install", _fake_runner(calls))
    context = fv._dependency_context(store, store.get_task(task.id), base, None, checks)
    with pytest.raises(TaskStoreError) as caught:
        fv._ensure_check_dependencies(checks[0], root, context)
    reason = str(caught.value)
    assert reason == "functional_workspace_dependency_resolution_untrusted"
    assert calls == []
    assert fv.validation_failure_outcome(reason) == ("FAILED", "deterministic_validation_failure")


@pytest.mark.parametrize("source", ["base", "workspace"])
def test_a_linked_target_directory_is_refused_before_any_write(repository, tmp_path, source):
    """#1557 review: lexical containment followed a junction outside the workspace."""
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    plan = wd.task_dependency_plan(store, task.id)
    outside = tmp_path / "outside-frontend"
    outside.mkdir()
    (outside / "package.json").write_text("{}", encoding="utf-8")
    (outside / "package-lock.json").write_text("external-sentinel", encoding="utf-8")
    shutil.rmtree(root / "frontend")
    _make_dir_link(root / "frontend", outside)

    calls: list[dict] = []
    with pytest.raises(wd.WorkspaceDependencyError) as caught:
        wd.provision_workspace_dependencies(store, task.id, plan, root,
                                            runner=_fake_runner(calls), lockfile_source=source)
    assert caught.value.code == wd.PATH_UNTRUSTED_CODE
    assert calls == []
    assert (outside / "package-lock.json").read_text(encoding="utf-8") == "external-sentinel"


def test_a_linked_lockfile_is_refused(repository, tmp_path):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    outside = tmp_path / "outside-lock.json"
    outside.write_text("external-sentinel", encoding="utf-8")
    lockfile = root / "frontend" / "package-lock.json"
    lockfile.unlink()
    try:
        lockfile.symlink_to(outside)
    except OSError as exc:  # WinError 1314 without the symlink privilege
        pytest.skip(f"file symlinks unavailable: {exc}")
    calls: list[dict] = []
    with pytest.raises(wd.WorkspaceDependencyError) as caught:
        wd.provision_workspace_dependencies(store, task.id, wd.task_dependency_plan(store, task.id),
                                            root, runner=_fake_runner(calls))
    assert caught.value.code == wd.PATH_UNTRUSTED_CODE
    assert calls == [] and outside.read_text(encoding="utf-8") == "external-sentinel"


@pytest.mark.parametrize("where", ["frontend", "."])
def test_a_project_npmrc_is_refused_before_installing(repository, monkeypatch, where):
    root, base, store, task = repository
    checks = [{"profile_id": "npm_test", "working_directory": "frontend"}]
    _freeze(store, task, checks, base)
    (root / where / ".npmrc").write_text("registry=https://example.invalid/\n", encoding="utf-8")
    calls: list[dict] = []
    with pytest.raises(wd.WorkspaceDependencyError) as caught:
        wd.provision_workspace_dependencies(store, task.id, wd.task_dependency_plan(store, task.id),
                                            root, runner=_fake_runner(calls))
    assert caught.value.code == wd.PROJECT_CONFIG_CODE and calls == []

    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    monkeypatch.setattr(wd, "_run_install", _fake_runner(calls))
    context = fv._dependency_context(store, store.get_task(task.id), base, None, checks)
    with pytest.raises(TaskStoreError, match="functional_npm_project_config_unsupported"):
        fv._ensure_check_dependencies(checks[0], root, context)
    assert calls == []


def test_an_agent_deleted_lockfile_is_not_an_infrastructure_fault(repository, monkeypatch):
    root, base, store, task = repository
    checks = [{"profile_id": "npm_test", "working_directory": "frontend"}]
    _freeze(store, task, checks, base)
    (root / "frontend" / "package-lock.json").unlink()
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    context = fv._dependency_context(store, store.get_task(task.id), base, None, checks)
    with pytest.raises(TaskStoreError) as caught:
        fv._ensure_check_dependencies(checks[0], root, context)
    reason = str(caught.value)
    assert reason == "functional_workspace_dependency_lockfile_invalid"
    assert fv.validation_failure_outcome(reason) == ("FAILED", "deterministic_validation_failure")


# ---------------------------------------------------------------------------
# The install's process tree (#1557 review P1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("parent_waits", [True, False])
def test_install_timeout_ends_the_whole_process_tree(tmp_path, parent_waits):
    marker = tmp_path / "descendant-survived.txt"
    child = ("import time; from pathlib import Path; time.sleep(3); "
             "Path('descendant-survived.txt').write_text('escaped')")
    script = ("import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); "
              + ("time.sleep(30)" if parent_waits else "sys.exit(0)"))
    started = time.monotonic()
    observed = wd._run_install([sys.executable, "-c", script], tmp_path,
                               fv._environment(tmp_path), 1)
    assert observed["timed_out"] is True and observed["cleanup"] == "confirmed"
    assert time.monotonic() - started < 8
    time.sleep(3.5)
    assert not marker.exists(), "an install descendant outlived the timeout"


def test_a_timed_out_install_records_a_bounded_host_fault(repository, monkeypatch):
    root, base, store, task = repository
    _freeze(store, task, [{"profile_id": "npm_test", "working_directory": "frontend"}], base)
    monkeypatch.setattr(wd, "_npm_argv", lambda: [sys.executable, "-c", "import time; time.sleep(30)"])
    started = time.monotonic()
    with pytest.raises(wd.WorkspaceDependencyError) as caught:
        wd.provision_workspace_dependencies(store, task.id, wd.task_dependency_plan(store, task.id),
                                            root, timeout=1)
    assert time.monotonic() - started < 8
    assert caught.value.code == wd.DEPENDENCY_FAILURE_CODE
    entry = json.loads(wd.dependency_evidence(store.get_task(task.id))[-1]["detail"])["directories"][0]
    assert entry["timed_out"] is True and entry["cleanup"] == "confirmed"


def test_unconfirmed_install_cleanup_is_never_an_ordinary_failure(repository, monkeypatch):
    from reverse_agent.platform_v1.goal_service import _interrupted_preparation

    root, base, store, task = repository
    checks = [{"profile_id": "npm_test", "working_directory": "frontend"}]
    _freeze(store, task, checks, base)
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])

    def drain_incomplete(*args, **kwargs):
        raise TaskStoreError("functional_output_drain_incomplete")

    monkeypatch.setattr(fv, "run_owned_process", drain_incomplete)
    with pytest.raises(wd.WorkspaceDependencyError) as caught:
        wd.provision_workspace_dependencies(store, task.id, wd.task_dependency_plan(store, task.id), root)
    assert caught.value.code == wd.DEPENDENCY_CLEANUP_CODE
    document = json.loads(wd.dependency_evidence(store.get_task(task.id))[-1]["detail"])
    assert document["failure"] == wd.DEPENDENCY_CLEANUP_CODE
    assert document["directories"][0]["cleanup"] == "unknown"

    context = fv._dependency_context(store, store.get_task(task.id), base, None, checks)
    with pytest.raises(TaskStoreError) as raised:
        fv._ensure_check_dependencies(checks[0], root, context)
    assert str(raised.value) == fv.DEPENDENCY_CLEANUP_REASON
    assert fv.validation_failure_outcome(fv.DEPENDENCY_CLEANUP_REASON) == ("FAILED", "cleanup_unconfirmed")
    # A preparation-time cleanup uncertainty is not retried as an interrupted preparation.
    failed = SimpleNamespace(id=task.id, status="BLOCKED",
                             failure_detail="worktree_preparation_failed:" + wd.DEPENDENCY_CLEANUP_CODE)
    assert _interrupted_preparation(store, failed) is False


# ---------------------------------------------------------------------------
# Validation-time install failures stay host faults end to end (#1557 review P2)
# ---------------------------------------------------------------------------


class _DependencyAwareImplementation(LocalImplementation):
    def prepare_worktree_once(self, task_id, workspace_root, callback=None, *,
                              dependencies=None, dependency_store=None):
        return super().prepare_worktree_once(task_id, workspace_root, callback)


@pytest.mark.parametrize("engine", ["ordinary", "durable"])
def test_a_validation_time_install_failure_blocks_without_spending_retries(
        goal_checks, tmp_path, monkeypatch, engine):
    root, _, store, control, *_ = goal_checks
    _frontend_project(root)
    git(root, "add", "--", "frontend")
    git(root, "commit", "-q", "-m", "frontend workspace")
    base = git(root, "rev-parse", "HEAD")
    fixture = (root, base, *goal_checks[2:])
    monkeypatch.setattr(goal_fixture, "planned_check", lambda task_id="T001", directory=".": {
        "id": task_id, "title": "Implement value two", "instruction": "Make value equal two",
        "validation_checks": [{"profile_id": "npm_test", "working_directory": "frontend"}]})
    launched = goal_fixture.launch_checks(fixture)
    task_id = control.list_goal_tasks(launched.id)[0]["task_id"]
    executor = _DependencyAwareImplementation(root, base, "value = 2\n")
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: executor)
    monkeypatch.setattr(fv, "_resolved_argv", lambda profile: [sys.executable, "-c", "pass"])
    monkeypatch.setattr(wd, "_npm_argv", lambda: ["npm", "ci"])
    calls: list[dict] = []
    # The registry is unreachable when validation re-installs.
    monkeypatch.setattr(wd, "_run_install", _fake_runner(calls, exit_code=1))

    service = durable(store, router) if engine == "durable" else ordinary(store, router)
    method = service.execute_durable_single if engine == "durable" else service.execute
    outcome = method(task_id, workspace_root=str(tmp_path / "worktrees"))

    assert outcome.success is False
    assert len(calls) == 1
    task = store.get_task(task_id)
    assert task.status == "BLOCKED"
    assert task.failure_classification == "blocked"
    assert task.failure_detail == fv.DEPENDENCY_UNAVAILABLE_REASON
    assert outcome.failure_classification == "blocked"
    result = json.loads([row for row in task.evidence_refs
                         if row.get("category") == fv.RESULT_CATEGORY][-1]["detail"])
    assert result["reason"] == fv.DEPENDENCY_UNAVAILABLE_REASON
    assert result["failure_kind"] == "infrastructure"
    install = json.loads(wd.dependency_evidence(task)[-1]["detail"])
    assert install["status"] == "FAILED" and install["directories"][0]["lockfile_source"] == "workspace"
    # The agent's artifact is preserved for a later run.
    assert (executor.prepared.worktree / "app.py").read_text(encoding="utf-8") == "value = 2\n"


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
