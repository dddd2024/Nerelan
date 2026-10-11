"""Claude Code native executor: real local subprocess/Git fixtures, zero model calls."""

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.claude_executor import (
    DENIED_TOOLS, ClaudeCodeExecutor, build_claude_argv, claude_child_env, probe_claude_code_readiness,
)
from reverse_agent.platform_v1.claude_protocol import ClaudeProtocolError, ClaudeStreamJson
from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError, ExecutorRouter


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


EVENTS = [
    {"type": "system", "subtype": "init", "session_id": "fixture-session", "model": "claude-sonnet-5-5"},
    {"type": "assistant", "session_id": "fixture-session", "message": {"content": [
        {"type": "text", "text": "Looking at the fixture."},
        {"type": "tool_use", "name": "Bash", "input": {"command": "git status --short"}},
    ]}},
    {"type": "user", "message": {"content": [{"type": "tool_result", "content": "SECRET FILE BODY"}]}},
    {"type": "result", "subtype": "success", "is_error": False, "result": "Readable fixture result",
     "usage": {"input_tokens": 10, "cache_read_input_tokens": 2, "output_tokens": 5}, "total_cost_usd": 0.01},
]
SUCCESS_SCRIPT = "import sys,json;sys.stdin.read();print(" + repr("\n".join(json.dumps(e) for e in EVENTS)) + ")"


def fixture_executor(repo, base, script, *, timeout=5):
    launched = []

    def factory(argv, **kwargs):
        assert argv[1:4] == ["-p", "--output-format", "stream-json"]
        assert "--permission-mode" in argv and argv[argv.index("--permission-mode") + 1] == "dontAsk"
        assert kwargs["shell"] is False
        for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"):
            assert name not in kwargs["env"]
        proc = subprocess.Popen([sys.executable, "-u", "-c", script], **kwargs)
        launched.append(proc)
        return proc

    executor = ClaudeCodeExecutor(model_id="claude-sonnet-5-5", repo_dir=str(repo), base_ref=base,
        claude_exe=sys.executable, timeout=timeout, process_factory=factory,
        readiness_probe=lambda _: "managed_login_ready",
        parent_env={"PATH": str(Path(sys.executable).parent), "ANTHROPIC_API_KEY": "fixture-secret",
                    "ANTHROPIC_AUTH_TOKEN": "fixture-token", "ANTHROPIC_BASE_URL": "https://example.invalid"})
    return executor, launched


def test_native_subprocess_worktree_progress_and_final_response(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    seen = []
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Bounded fixture instruction"))
    result = executor.execute("claude-1", store, workspace_root=str(tmp_path / "workspaces"),
        event_callback=lambda _, event: seen.append(event))
    assert result.success and result.process_exit_code == 0
    assert result.validation_command_id == "git_diff_check"
    assert git(Path(result.workspace), "rev-parse", "HEAD") == base
    assert git(repo, "status", "--porcelain") == ""
    assert len(launched) == 1 and launched[0].poll() == 0
    final = next(e for e in seen if e["type"] == "EXECUTOR_COMPLETED")
    assert final["title"] == "Claude Code response"
    assert final["metadata"]["executor_kind"] == "claude_code"
    assert final["metadata"]["final_text"] == "Readable fixture result"
    assert final["metadata"]["token_usage"] == {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 5}
    assert final["metadata"]["cost_status"] == "unknown"
    progress = [e for e in seen if e["type"] == "EXECUTOR_PROGRESS"]
    assert any(e["metadata"]["event"].get("command") == "git status --short" for e in progress)
    # Tool results can echo file contents; they are never relayed.
    assert "SECRET FILE BODY" not in json.dumps(seen)


@pytest.mark.parametrize("script,classification", [
    ("import sys;sys.stdin.read();print('invalid json')", "claude_code_invalid_jsonl"),
    (SUCCESS_SCRIPT + ";raise SystemExit(7)", "claude_code_process_failed"),
    ("import sys;sys.stdin.read()", "claude_code_turn_incomplete"),
    ("import sys,json;sys.stdin.read();print(json.dumps({'type':'system','subtype':'init','session_id':'s'}));"
     "print(json.dumps({'type':'result','subtype':'error_max_turns','is_error':True}))",
     "claude_code_turn_failed:error_max_turns"),
])
def test_process_and_protocol_failures_remain_failures(repository, tmp_path, script, classification):
    repo, base = repository
    executor, _ = fixture_executor(repo, base, script)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Bounded fixture instruction"))
    result = executor.execute("claude-2", store, workspace_root=str(tmp_path / "workspaces"))
    assert not result.success and result.failure_classification == classification


def test_argv_allows_only_bounded_tools_and_ignores_project_configuration():
    write = build_claude_argv("claude", "claude-sonnet-5-5", "workspace-write")
    assert write[:3] == ["claude", "-p", "--output-format"]
    assert "--no-session-persistence" in write and "--strict-mcp-config" in write
    assert write[write.index("--setting-sources") + 1] == "user"
    allowed = write[write.index("--allowedTools") + 1:write.index("--disallowedTools")]
    assert "Edit" in allowed and "Bash(python -m pytest *)" in allowed
    assert not any(tool in ("Bash", "Bash(*)") for tool in allowed)
    assert tuple(write[write.index("--disallowedTools") + 1:]) == DENIED_TOOLS
    read_only = build_claude_argv("claude", "opus", "read-only")
    allowed_ro = read_only[read_only.index("--allowedTools") + 1:read_only.index("--disallowedTools")]
    assert "Edit" not in allowed_ro and not any(tool.startswith("Bash") for tool in allowed_ro)
    with pytest.raises(ExecutorRuntimeError, match="claude_code_sandbox_invalid"):
        build_claude_argv("claude", "opus", "danger-full-access")
    with pytest.raises(ExecutorRuntimeError, match="claude_code_model_id_invalid"):
        build_claude_argv("claude", "--dangerously-skip-permissions", "read-only")


def test_child_environment_strips_api_credentials():
    env = claude_child_env({"PATH": "p", "USERPROFILE": "u", "ANTHROPIC_API_KEY": "k",
                            "ANTHROPIC_AUTH_TOKEN": "t", "ANTHROPIC_BASE_URL": "b", "OPENAI_API_KEY": "o",
                            "CLAUDE_CONFIG_DIR": "c"})
    assert env == {"PATH": "p", "USERPROFILE": "u", "CLAUDE_CONFIG_DIR": "c"}


def _runner(status_payload, *, help_text=None, status_code=0):
    help_text = help_text or ("--print --output-format --permission-mode --strict-mcp-config "
                              "--setting-sources --no-session-persistence")

    def run(argv, **kwargs):
        assert "ANTHROPIC_API_KEY" not in kwargs["env"]
        if argv[1:] == ["--help"]:
            return SimpleNamespace(returncode=0, stdout=help_text, stderr="")
        return SimpleNamespace(returncode=status_code, stdout=json.dumps(status_payload), stderr="")
    return run


@pytest.mark.parametrize("payload,expected", [
    ({"loggedIn": True, "authMethod": "claude.ai", "email": "owner@example.invalid"}, "managed_login_ready"),
    ({"loggedIn": True, "authMethod": "api_key"}, "managed_login_unavailable"),
    ({"loggedIn": False}, "managed_login_unavailable"),
    ([], "managed_login_unavailable"),
])
def test_readiness_uses_auth_status_without_inference(payload, expected, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-leak")
    assert probe_claude_code_readiness(sys.executable, runner=_runner(payload)) == expected


def test_readiness_rejects_incompatible_cli():
    assert probe_claude_code_readiness(sys.executable, runner=_runner({}, help_text="--print")) == "cli_incompatible"


def test_protocol_requires_session_and_terminal_result():
    parser = ClaudeStreamJson()
    with pytest.raises(ClaudeProtocolError, match="claude_code_session_identity_invalid"):
        parser.feed(b'{"type":"assistant","message":{"content":[]}}\n')
    parser = ClaudeStreamJson()
    parser.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n')
    with pytest.raises(ClaudeProtocolError, match="claude_code_turn_incomplete"):
        parser.finish()
    parser = ClaudeStreamJson()
    parser.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n'
                b'{"type":"result","subtype":"success","is_error":false,"result":"done"}\n')
    with pytest.raises(ClaudeProtocolError, match="claude_code_event_after_terminal"):
        parser.feed(b'{"type":"assistant","message":{"content":[]}}\n')


def test_router_registers_claude_code_executor():
    factory = ExecutorRouter()._registry["claude_code"]
    executor = factory(model_id="claude-sonnet-5-5", claude_exe=sys.executable,
                       readiness_probe=lambda _: "managed_login_ready")
    assert isinstance(executor, ClaudeCodeExecutor) and executor.KIND == "claude_code"


def test_claude_account_connection_and_binding_never_accept_api_keys(tmp_path):
    store = ModelProfileStore(state_path=tmp_path / "state.json")
    connection = {"connection_id": "claude-account", "name": "Claude 账号", "provider": "claude-code",
                  "base_url": "https://claude.ai", "auth_method": "external_cli_session", "enabled": True}
    with pytest.raises(ValueError, match="claude_code_credentials_owned_by_cli"):
        store.upsert_connection({**connection, "api_key": "sk-ant-fixture"})
    store.upsert_connection(connection)
    saved = store.get_connection_public("claude-account")
    assert saved["upstream_provider_id"] == "anthropic" and saved["protocol_family"] == "claude-code-cli"
    assert saved["external_session_status"] == "missing"
    store.set_native_readiness("claude_code", "managed_login_ready")
    assert store.get_connection_public("claude-account")["external_session_status"] == "available"
    assert store.get_executor_public("claude_code")["operational"] is True
    store.upsert_binding({"binding_id": "claude-default", "name": "Claude", "connection_id": "claude-account",
                          "executor_id": "claude_code", "model_id": "claude-sonnet-5-5", "enabled": True})
    with pytest.raises(ValueError, match="claude_code_connection_requires_native_executor"):
        store.upsert_binding({"binding_id": "claude-via-opencode", "name": "x", "connection_id": "claude-account",
                              "executor_id": "opencode", "model_id": "claude-sonnet-5-5", "enabled": True})
    with pytest.raises(ValueError, match="claude_code_requires_managed_session_connection"):
        store.upsert_connection({**connection, "connection_id": "claude-key", "auth_method": "api_key"})
