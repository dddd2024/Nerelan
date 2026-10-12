"""Real local subprocess/Git fixtures, with zero model or provider calls."""

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.codex_executor import (
    CodexExecutor, CodexPreparedContext, build_codex_argv, codex_child_env, validate_codex_model,
)
from reverse_agent.platform_v1.opencode_executor import RoleContext
from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()


@pytest.fixture
def repository(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "fixture.txt").write_text("original\n")
    git(repo, "add", "fixture.txt")
    git(repo, "commit", "-m", "fixture")
    return repo, git(repo, "rev-parse", "HEAD")


def fixture_executor(repo, base, script, *, timeout=5):
    launched = []
    def factory(argv, **kwargs):
        assert argv[1:5] == ["exec", "--ignore-user-config", "--ephemeral", "--json"]
        assert argv[-1] == "-" and kwargs["shell"] is False
        assert "OPENAI_API_KEY" not in kwargs["env"]
        proc = subprocess.Popen([sys.executable, "-u", "-c", script], **kwargs)
        launched.append(proc)
        return proc
    executor = CodexExecutor(model_id="gpt-5.4", repo_dir=str(repo), base_ref=base,
        codex_exe=sys.executable, timeout=timeout, process_factory=factory,
        readiness_probe=lambda _: "managed_login_ready",
        parent_env={"PATH": str(Path(sys.executable).parent), "OPENAI_API_KEY": "fixture-secret"})
    return executor, launched


EVENTS = [
    {"type": "thread.started", "thread_id": "fixture-thread"},
    {"type": "turn.started"},
    {"type": "item.completed", "item": {"type": "agent_message", "text": "Readable fixture result"}},
    {"type": "turn.completed"},
]
SUCCESS_SCRIPT = "import sys,json;sys.stdin.read();print(" + repr("\n".join(json.dumps(e) for e in EVENTS)) + ")"


def test_native_subprocess_worktree_progress_and_final_response(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    seen = []
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Bounded fixture instruction"))
    result = executor.execute("native-1", store, workspace_root=str(tmp_path / "workspaces"),
        event_callback=lambda _, event: seen.append(event))
    assert result.success and result.process_exit_code == 0
    assert result.validation_command_id == "git_diff_check"
    assert git(Path(result.workspace), "rev-parse", "HEAD") == base
    assert git(repo, "status", "--porcelain") == ""
    assert len(launched) == 1 and launched[0].poll() == 0
    final = next(e for e in seen if e["type"] == "EXECUTOR_COMPLETED")
    assert final["metadata"]["final_text"] == "Readable fixture result"
    assert final["metadata"]["usage_status"] == "unknown"
    assert final["metadata"]["cost_status"] == "unknown"
    assert any(e["type"] == "EXECUTOR_PROGRESS" for e in seen)


@pytest.mark.parametrize("script,classification", [
    ("import sys;sys.stdin.read();print('invalid json')", "codex_invalid_jsonl"),
    (SUCCESS_SCRIPT + ";raise SystemExit(7)", "codex_process_failed"),
    ("import sys;sys.stdin.read();sys.stderr.write('Authorization: Bearer private-token')", "codex_turn_incomplete"),
])
def test_process_and_protocol_failures_remain_failures(repository, tmp_path, script, classification):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, script)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Fixture"))
    result = executor.execute("native-1", store, workspace_root=str(tmp_path / "workspaces"))
    assert not result.success and result.failure_classification == classification
    assert "private-token" not in repr(result)
    assert len(launched) == 1 and launched[0].poll() is not None


def test_timeout_is_bounded_and_terminates_only_owned_fixture_process(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base,
        "import sys,time;sys.stdin.read();time.sleep(30)", timeout=0.2)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Fixture"))
    result = executor.execute("native-1", store, workspace_root=str(tmp_path / "workspaces"))
    assert result.failure_classification == "codex_timeout"
    assert launched[0].poll() is not None


def test_resume_preserves_native_identity_and_never_prepares_or_dispatches(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    original = executor.prepare_worktree_once("native-1", tmp_path / "workspaces")
    prepared = executor.reconstruct_prepared_context(worktree_path=str(original.worktree), base_sha=base, execution_id="exec-native-1")
    assert prepared.executor_kind == "codex" and prepared.base_sha == base
    assert not launched
    with pytest.raises(ExecutorRuntimeError, match="codex_worktree_head_mismatch"):
        executor.reconstruct_prepared_context(worktree_path=str(original.worktree), base_sha="0" * 40, execution_id="exec-native-1")
    with pytest.raises(ExecutorRuntimeError, match="codex_worktree_identity_invalid"):
        executor.reconstruct_prepared_context(worktree_path=str(repo), base_sha=base, execution_id="exec-native-1")
    assert not launched


def test_unsupported_role_and_wrong_prepared_identity_deny_before_dispatch(repository):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    prepared = CodexPreparedContext(repo, base, "exec-native-1", sys.executable)
    with pytest.raises(ExecutorRuntimeError, match="codex_single_mode_only"):
        executor.execute_role_prepared(prepared, None, role_context=RoleContext("reviewer", "native-1", repo))
    with pytest.raises(ExecutorRuntimeError, match="codex_task_identity_mismatch"):
        executor.execute_role_prepared(prepared, None, role_context=RoleContext("executor", "other-task", repo))
    assert not launched


def test_existing_workspace_is_preserved_and_floating_base_denied(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    root = tmp_path / "workspaces"
    existing = root / "native-1"
    existing.mkdir(parents=True)
    (existing / "preserve.txt").write_text("owner content")
    with pytest.raises(ExecutorRuntimeError, match="workspace_destination_exists"):
        executor.prepare_worktree_once("native-1", root)
    assert (existing / "preserve.txt").read_text() == "owner content"
    executor._base_ref = "main"
    with pytest.raises(ExecutorRuntimeError, match="codex_requires_exact_base_sha"):
        executor.prepare_worktree_once("native-2", root)
    assert not launched


def test_child_environment_and_argv_preserve_policy_and_exclude_provider_authority():
    env = codex_child_env({"Path": "safe", "CODEX_HOME": "managed-login-home",
        "OPENAI_API_KEY": "secret", "OPENAI_BASE_URL": "https://untrusted.invalid",
        "OPENCODE_CONFIG_CONTENT": "private", "HTTP_PROXY": "http://user:password@host"})
    assert env == {"Path": "safe", "CODEX_HOME": "managed-login-home"}
    argv = build_codex_argv("native.exe", Path("owned space"), "gpt-5.4", "workspace-write")
    assert "owned space" in argv and "--ignore-rules" not in argv
    assert "--dangerously-bypass-approvals-and-sandbox" not in argv
    assert "--sandbox" in argv and argv[-1] == "-"
    with pytest.raises(ExecutorRuntimeError, match="codex_sandbox_invalid"):
        build_codex_argv("native.exe", Path("."), "gpt-5.4", "danger-full-access")


def test_project_provider_or_hook_configuration_is_denied_without_dispatch(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    prepared = executor.prepare_worktree_once("native-1", tmp_path / "workspaces")
    directory = prepared.worktree / ".codex"
    directory.mkdir()
    (directory / "config.toml").write_text('model_provider="unapproved-provider"\n')
    with pytest.raises(ExecutorRuntimeError, match="codex_project_configuration_unapproved"):
        executor.execute_role_prepared(prepared, None, role_context=RoleContext("executor", "native-1", prepared.worktree))
    assert not launched


@pytest.mark.parametrize("model", ["openai/gpt-5.4", "--flag", "gpt\n5", "", "a" * 129])
def test_opencode_prefixes_and_argv_injection_are_not_native_model_ids(model):
    with pytest.raises(ExecutorRuntimeError, match="codex_model_id_invalid"):
        validate_codex_model(model)
