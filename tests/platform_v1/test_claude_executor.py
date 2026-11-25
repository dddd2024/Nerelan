"""Claude Code native executor: real local subprocess/Git fixtures, zero model calls."""

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.claude_executor import (
    ClaudeCodeExecutor, build_claude_argv, claude_child_env, probe_claude_code_readiness,
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
        assert "--restricted" in argv and argv[argv.index("--permission-mode") + 1] == "acceptEdits"
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
    edit_script = "from pathlib import Path;Path('fixture.txt').write_text('updated\\n');" + SUCCESS_SCRIPT
    executor, launched = fixture_executor(repo, base, edit_script)
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


def test_native_claude_noop_turn_not_accepted_as_implementation(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(
        title="Change fixture.txt so the requested regression passes"))
    result = executor.execute("claude-noop", store,
        workspace_root=str(tmp_path / "workspaces"))
    assert not result.success
    assert result.failure_classification == "claude_code_no_product_changes"
    assert result.validation_command_id == "git_diff_check"
    assert result.validation_exit_code == 0
    assert result.process_exit_code == 0
    assert not result.changed_files
    assert git(Path(result.workspace), "status", "--short") == ""
    assert len(launched) == 1 and launched[0].poll() == 0


@pytest.mark.parametrize("script,classification", [
    ("import sys;sys.stdin.read();print('invalid json')", "claude_code_invalid_jsonl"),
    (SUCCESS_SCRIPT + ";raise SystemExit(7)", "claude_code_process_failed"),
    ("import sys;sys.stdin.read()", "claude_code_turn_incomplete"),
    ("import sys,json;sys.stdin.read();print(json.dumps({'type':'system','subtype':'init','session_id':'s'}));"
     "print(json.dumps({'type':'result','subtype':'error_max_turns','is_error':True}))",
     "claude_code_turn_failed:error_max_turns"),
    ("import sys,json;sys.stdin.read();print(json.dumps({'type':'system','subtype':'init','session_id':'s'}));"
     "print(json.dumps({'type':'result','subtype':'success','is_error':True,'api_error_status':429}))",
     "claude_code_turn_failed:api_error_429"),
    ("import sys,json;sys.stdin.read();print(json.dumps({'type':'system','subtype':'init','session_id':'s'}));"
     "print(json.dumps({'type':'result','subtype':'success','is_error':True}))",
     "claude_code_turn_failed:api_error"),
])
def test_process_and_protocol_failures_remain_failures(repository, tmp_path, script, classification):
    repo, base = repository
    executor, _ = fixture_executor(repo, base, script)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Bounded fixture instruction"))
    result = executor.execute("claude-2", store, workspace_root=str(tmp_path / "workspaces"))
    assert not result.success and result.failure_classification == classification


def test_argv_grants_no_code_running_tool_and_ignores_all_settings():
    write = build_claude_argv("claude", "claude-sonnet-5-5", "workspace-write")
    assert write[:3] == ["claude", "-p", "--output-format"]
    for flag in ("--restricted", "--strict-mcp-config", "--no-session-persistence"):
        assert flag in write
    assert write[write.index("--tools") + 1] == "Read,Glob,Grep,Edit,Write"
    assert write[write.index("--permission-mode") + 1] == "acceptEdits"
    assert write[write.index("--permission-prompts") + 1] == "none"
    assert "--setting-sources" not in write and "--allowedTools" not in write
    assert not any(part.startswith(("Bash", "PowerShell", "WebFetch")) for part in write)
    read_only = build_claude_argv("claude", "opus", "read-only")
    assert read_only[read_only.index("--tools") + 1] == "Read,Glob,Grep"
    assert read_only[read_only.index("--permission-mode") + 1] == "dontAsk"
    with pytest.raises(ExecutorRuntimeError, match="claude_code_sandbox_invalid"):
        build_claude_argv("claude", "opus", "danger-full-access")
    with pytest.raises(ExecutorRuntimeError, match="claude_code_model_id_invalid"):
        build_claude_argv("claude", "--dangerously-skip-permissions", "read-only")
    with pytest.raises(ExecutorRuntimeError, match="claude_code_model_id_invalid"):
        ClaudeCodeExecutor(model_id="--bad", claude_exe=sys.executable)


def test_child_environment_strips_api_credentials():
    env = claude_child_env({"PATH": "p", "USERPROFILE": "u", "ANTHROPIC_API_KEY": "k",
                            "ANTHROPIC_AUTH_TOKEN": "t", "ANTHROPIC_BASE_URL": "b", "OPENAI_API_KEY": "o",
                            "CLAUDE_CODE_USE_BEDROCK": "1", "CLAUDE_CODE_USE_VERTEX": "1",
                            "CLAUDE_CONFIG_DIR": "c", "HTTPS_PROXY": "h", "SystemRoot": "s"})
    assert env == {"PATH": "p", "USERPROFILE": "u", "CLAUDE_CONFIG_DIR": "c", "SystemRoot": "s"}


def test_child_environment_preserves_os_username_keys():
    env = claude_child_env({"PATH": "p", "USERNAME": "u-win", "USER": "u-posix", "LOGNAME": "u-log",
                            "ANTHROPIC_API_KEY": "k", "OPENAI_API_KEY": "o", "HTTPS_PROXY": "h"})
    assert env == {"PATH": "p", "USERNAME": "u-win", "USER": "u-posix", "LOGNAME": "u-log"}


def _runner(status_payload, *, help_text=None, status_code=0):
    help_text = help_text or ("--print --output-format --permission-mode --strict-mcp-config "
                              "--restricted --tools --permission-prompts --no-session-persistence")

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
    # An old CLI whose auth status also fails must not look like "CLI fine, just logged out".
    assert probe_claude_code_readiness(
        sys.executable, runner=_runner({}, help_text="--print", status_code=1)) == "cli_incompatible"


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


def test_thinking_progress_notices_do_not_spend_the_event_bound():
    # Observed with GLM-5.2 through the relay: one notice per 1-4 thinking tokens (#1164).
    notice = b'{"type":"system","subtype":"thinking_tokens","estimated_tokens":3,"estimated_tokens_delta":2}\n'
    parser = ClaudeStreamJson(max_events=3)
    parser.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n' + notice * 500
                + b'{"type":"result","subtype":"success","is_error":false,"result":"done"}\n')
    assert parser.finish().final_text == "done"
    parser = ClaudeStreamJson(max_events=2)
    with pytest.raises(ClaudeProtocolError, match="claude_code_event_limit_exceeded"):
        parser.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n'
                    + b'{"type":"assistant","message":{"content":[]}}\n' * 2)
    parser = ClaudeStreamJson(max_frame_bytes=1024, max_stream_bytes=4096)
    with pytest.raises(ClaudeProtocolError, match="claude_code_stream_limit_exceeded"):
        parser.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n' + notice * 100)
    assert ClaudeStreamJson()._stream_limit is None
    assert ClaudeStreamJson(max_stream_bytes=64 * 1024 * 1024)._stream_limit == 64 * 1024 * 1024
    with pytest.raises(ValueError, match="claude_protocol_limits_invalid"):
        ClaudeStreamJson(max_stream_bytes=64 * 1024 * 1024 + 1)
    # Normal bounded events past max_progress_bytes stay valid; noise floods past max_progress_bytes still abort.
    long_turn = ClaudeStreamJson(max_frame_bytes=4096, max_progress_bytes=512, max_events=100)
    user_line = b'{"type":"user","message":{"role":"user","content":"' + b"x" * 600 + b'"}}\n'
    long_turn.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n' + user_line * 4
                   + b'{"type":"result","subtype":"success","is_error":false,"result":"ok"}\n')
    assert long_turn.finish().final_text == "ok"
    noise_flood = ClaudeStreamJson(max_frame_bytes=1024, max_progress_bytes=512)
    with pytest.raises(ClaudeProtocolError, match="claude_code_stream_limit_exceeded"):
        noise_flood.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n' + notice * 10)
    # A single huge multi-line chunk is sliced at frame_limit+1 so _buffer stays bounded.
    sliced = ClaudeStreamJson(max_frame_bytes=512, max_events=50)
    big_chunk = b'{"type":"system","subtype":"init","session_id":"s"}\n' + (b'{"type":"user","message":{"role":"user","content":"' + b"z" * 200 + b'"}}\n') * 10 + b'{"type":"result","subtype":"success","is_error":false,"result":"sliced"}\n'
    sliced.feed(big_chunk)
    assert sliced.finish().final_text == "sliced" and len(sliced._buffer) == 0


def test_router_registers_claude_code_executor():
    factory = ExecutorRouter()._registry["claude_code"]
    executor = factory(model_id="claude-sonnet-5-5", claude_exe=sys.executable,
                       readiness_probe=lambda _: "managed_login_ready")
    assert isinstance(executor, ClaudeCodeExecutor) and executor.KIND == "claude_code"


def test_result_usage_limit_message_classifies_and_redacts():
    seen = []
    parser = ClaudeStreamJson(seen.append)
    parser.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n'
                b'{"type":"result","subtype":"success","is_error":true,'
                b'"error":"You\'ve hit your usage limit sk-verysecret"}\n')
    turn = parser.finish()
    assert turn.failed
    assert turn.failure_classification == "claude_code_usage_limit"
    assert "usage limit" in turn.failure_detail
    assert "sk-verysecret" not in turn.failure_detail
    assert seen and seen[-1]["type"] == "turn.error"


def test_result_generic_error_stays_turn_failed_with_detail():
    seen = []
    parser = ClaudeStreamJson(seen.append)
    parser.feed(b'{"type":"system","subtype":"init","session_id":"s"}\n'
                b'{"type":"result","subtype":"error_max_turns","is_error":true,"error":"boom"}\n')
    turn = parser.finish()
    assert turn.failure_classification == "claude_code_turn_failed:error_max_turns"
    assert turn.failure_detail == "boom"


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


@pytest.mark.parametrize('field', ['error', 'result'])
def test_failed_result_text_limit_reset_and_email_redaction(field):
    seen = []
    parser = ClaudeStreamJson(seen.append)
    event = {'type': 'result', 'subtype': 'success', 'is_error': True,
             field: 'Account quota exceeded; try again at 2026-10-20T02:00:00+02:00 owner@example.invalid token: sk-verysecret'}
    parser.feed(('\n'.join(json.dumps(e) for e in (EVENTS[0], event)) + '\n').encode())
    turn = parser.finish()
    assert turn.failure_classification == 'claude_code_usage_limit'
    assert turn.failure_reset_at == '2026-10-20T00:00:00Z'
    assert 'owner@example.invalid' not in repr(turn) + repr(seen)
    assert 'sk-verysecret' not in repr(turn) + repr(seen)
    assert len(turn.failure_detail) <= 500


def test_successful_result_limit_words_remain_success():
    parser = ClaudeStreamJson()
    event = {'type': 'result', 'subtype': 'success', 'result': 'Explained usage limit', 'is_error': False}
    parser.feed(('\n'.join(json.dumps(e) for e in (EVENTS[0], event)) + '\n').encode())
    turn = parser.finish()
    assert turn.completed and turn.final_text == 'Explained usage limit'
    assert not turn.failure_classification and not turn.failure_reset_at


def test_failed_result_clock_reset_uses_host_local_time(monkeypatch):
    from datetime import datetime
    from reverse_agent.platform_v1 import claude_protocol
    monkeypatch.setattr(claude_protocol, 'local_now',
                        lambda: datetime.fromisoformat('2026-10-19T12:00:00-04:00'))
    parser = ClaudeStreamJson()
    event = {'type': 'result', 'subtype': 'success', 'is_error': True,
             'result': 'Claude usage limit reached; try again at 14:30'}
    parser.feed(('\n'.join(json.dumps(e) for e in (EVENTS[0], event)) + '\n').encode())
    turn = parser.finish()
    assert turn.failure_classification == 'claude_code_usage_limit'
    assert turn.failure_reset_at == '2026-10-19T18:30:00Z'


def test_claude_read_only_review_argv_and_execution(repository, tmp_path):
    repo, base = repository
    review_argv = build_claude_argv("claude", "sonnet", "read-only", review_only=True)
    assert review_argv[review_argv.index("--tools") + 1] == ""
    assert review_argv[review_argv.index("--permission-mode") + 1] == "dontAsk"
    assert "--restricted" in review_argv and "--strict-mcp-config" in review_argv

    seen_argv = []
    review_events = [
        {"type": "system", "subtype": "init", "session_id": "rev-sess"},
        {"type": "result", "subtype": "success", "is_error": False,
         "result": '{"verdict":"ACCEPT","findings":[]}',
         "usage": {"input_tokens": 12, "cache_read_input_tokens": 0, "output_tokens": 4},
         "modelUsage": {"claude-sonnet-5-5": {"inputTokens": 12}}, "total_cost_usd": 0.01},
    ]
    review_script = "import sys,json;sys.stdin.read();print(" + repr("\n".join(json.dumps(e) for e in review_events)) + ")"

    def factory(argv, **kwargs):
        seen_argv.append(list(argv))
        return subprocess.Popen([sys.executable, "-u", "-c", review_script], **kwargs)

    resolution = SimpleNamespace(binding_ref="claude-sonnet", model_id="sonnet", executor_id="claude_code",
                                 relay_required=False, auth_method="external_cli_session",
                                 external_session_status="available")
    executor = ClaudeCodeExecutor(model_id="sonnet", repo_dir=str(repo), base_ref=base, sandbox="read-only",
                                  claude_exe=sys.executable, timeout=5, process_factory=factory,
                                  readiness_probe=lambda _: "managed_login_ready",
                                  binding_resolution=resolution, parent_env={"PATH": str(Path(sys.executable).parent)})
    assert executor.enforces_read_only_review() is True
    assert ClaudeCodeExecutor(model_id="sonnet", repo_dir=str(repo), base_ref=base, sandbox="workspace-write",
                              claude_exe=sys.executable).enforces_read_only_review() is False
    relay_res = SimpleNamespace(binding_ref="claude-relay", model_id="claude-sonnet-5-5", executor_id="claude_code",
                                relay_required=True, auth_method="api_key")
    assert ClaudeCodeExecutor(model_id="claude-sonnet-5-5", repo_dir=str(repo), base_ref=base, sandbox="read-only",
                              claude_exe=sys.executable, binding_resolution=relay_res,
                              lease_provider=lambda r: None).enforces_read_only_review() is False

    ws_root = tmp_path / "rev_ws"
    prepared = executor.prepare_worktree_once("rev-1", ws_root)
    store = SimpleNamespace(append_usage_observations=lambda *a, **k: None)
    reply = executor.execute_review_prepared(prepared, store, task_id="rev-1", prompt="Review JSON")
    assert seen_argv[0][seen_argv[0].index("--tools") + 1] == ""
    assert reply["actual_models"] == ["claude-sonnet-5-5"]
    assert reply["binding_ref"] == "claude-sonnet"
    assert json.loads(reply["response"]) == {"verdict": "ACCEPT", "findings": []}
