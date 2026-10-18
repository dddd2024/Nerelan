"""Machine MCP policy readiness checks: metadata only, zero provider calls."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import claude_executor as claude


@pytest.mark.parametrize("platform,expected", [
    ("win32", r"C:\Program Files\ClaudeCode\managed-mcp.json"),
    ("darwin", "/Library/Application Support/ClaudeCode/managed-mcp.json"),
    ("linux", "/etc/claude-code/managed-mcp.json"),
])
def test_documented_machine_path(platform, expected):
    assert claude._managed_mcp_path(platform) == Path(expected)


@pytest.fixture
def metadata_probe(monkeypatch):
    calls = []

    def install(error=None):
        def lstat(path):
            calls.append(path)
            if error is not None:
                raise error
            return SimpleNamespace()

        monkeypatch.setattr(Path, "lstat", lstat)
        # Any raw config/credential read or executable resolution is a bug on
        # the blocked path. The absent path uses a fake CLI and runner below.
        def forbidden(*args, **kwargs):
            pytest.fail("unexpected file content access")

        monkeypatch.setattr(Path, "open", forbidden)
        monkeypatch.setattr("builtins.open", forbidden)
        return calls

    return install


@pytest.mark.parametrize("error", [None, PermissionError("private details"),
                                   OSError("private details"), NotADirectoryError()])
def test_policy_or_uncertain_metadata_refuses_before_cli(metadata_probe, monkeypatch, error):
    calls = metadata_probe(error)

    def forbidden(*args, **kwargs):
        pytest.fail("blocked policy must not launch or resolve CLI")

    monkeypatch.setattr(claude, "resolve_claude_cli", forbidden)
    assert claude.probe_claude_code_readiness(runner=forbidden) == "cli_incompatible"
    assert calls == [claude._managed_mcp_path(claude.sys.platform)]


@pytest.mark.parametrize("help_text,status,expected", [
    (None, {"loggedIn": True, "authMethod": "claude.ai"}, "managed_login_ready"),
    (None, {"loggedIn": False}, "managed_login_unavailable"),
    ("--print", {}, "cli_incompatible"),
])
def test_absent_policy_preserves_help_and_login_only(
        metadata_probe, monkeypatch, help_text, status, expected):
    metadata_calls = metadata_probe(FileNotFoundError())
    monkeypatch.setattr(claude, "resolve_claude_cli", lambda _: "fixture-claude")
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        assert "ANTHROPIC_API_KEY" not in kwargs["env"]
        assert kwargs["stdin"] == claude.subprocess.DEVNULL
        if argv[1:] == ["--help"]:
            output = help_text or (
                "--print --output-format --permission-mode --strict-mcp-config "
                "--restricted --tools --permission-prompts --no-session-persistence")
        else:
            assert argv[1:] == ["auth", "status", "--json"]
            output = json.dumps(status)
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    assert claude.probe_claude_code_readiness(runner=runner) == expected
    assert metadata_calls == [claude._managed_mcp_path(claude.sys.platform)]
    assert calls == ([["fixture-claude", "--help"]] if help_text else [
        ["fixture-claude", "--help"], ["fixture-claude", "auth", "status", "--json"]])
