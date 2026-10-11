"""Native Claude Code CLI executor using the Owner's own Claude account login.

The installed ``claude`` CLI owns its saved claude.ai login. Nerelan never
reads, copies or relays that credential: readiness comes from
``claude auth status --json`` (projected to two fields), and every Anthropic
API-key or endpoint variable is stripped from the child environment so the
subscription login, not an API key, is what runs the task.

Everything else (isolated linked worktree, exact base, process confinement,
bounded parsing, host-run functional checks) is the shared native-CLI path
in :class:`CodexExecutor`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .claude_protocol import ClaudeStreamJson
from .codex_executor import CodexExecutor, validate_codex_model
from .task_runtime import ExecutorRuntimeError

# Read-only exploration plus a bounded set of local checks. Anything else
# (network, git commit/push, gh, package installs, arbitrary shell) is denied:
# with --permission-mode dontAsk an unlisted tool is refused, never prompted.
READ_TOOLS = ("Read", "Glob", "Grep", "LS", "TodoWrite")
WRITE_TOOLS = ("Edit", "MultiEdit", "Write", "NotebookEdit")
CHECK_COMMANDS = (
    "Bash(git status *)", "Bash(git diff *)", "Bash(git log *)", "Bash(git show *)",
    "Bash(python -m pytest *)", "Bash(pytest *)", "Bash(npm test *)", "Bash(npx vitest *)",
    "Bash(npx tsc *)", "Bash(ls *)",
)
DENIED_TOOLS = ("WebFetch", "WebSearch", "Bash(git push *)", "Bash(git commit *)", "Bash(gh *)",
                "Bash(curl *)", "Bash(pip install *)", "Bash(npm install *)")


def validate_claude_model(value: Any) -> str:
    try:
        return validate_codex_model(value)
    except ExecutorRuntimeError:
        raise ExecutorRuntimeError("claude_code_model_id_invalid") from None


def claude_child_env(parent: Mapping[str, str]) -> dict[str, str]:
    """CLI owns its saved login; API keys, auth tokens and endpoints stay out."""
    allowed = {
        "path", "systemroot", "pathext", "home", "userprofile", "localappdata",
        "appdata", "temp", "tmp", "claude_config_dir", "lang", "lc_all",
    }
    return {k: v for k, v in parent.items() if k.casefold() in allowed}


def resolve_claude_cli(exe: str | None = None) -> str:
    candidate = (exe or os.environ.get("REVERSE_AGENT_CLAUDE_CODE_EXE")
                 or shutil.which("claude.exe" if os.name == "nt" else "claude"))
    if not candidate:
        raise ExecutorRuntimeError("claude_code_cli_missing")
    path = Path(candidate).resolve()
    if not path.is_file() or (os.name == "nt" and path.suffix.casefold() != ".exe"):
        raise ExecutorRuntimeError("claude_code_cli_requires_native_executable")
    return str(path)


def probe_claude_code_readiness(exe: str | None = None, *, runner=subprocess.run) -> str:
    """Opt-in metadata probe; no inference and no raw credential-file access."""
    try:
        cli = resolve_claude_cli(exe)
        environment = claude_child_env(os.environ)
        outputs = []
        for args in (["--help"], ["auth", "status", "--json"]):
            result = runner([cli, *args], env=environment, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
                check=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            if len((result.stdout + result.stderr).encode()) > 64 * 1024:
                return "probe_output_invalid"
            if result.returncode:
                return "managed_login_unavailable" if args[0] == "auth" else "cli_unavailable"
            outputs.append(result.stdout)
        if not all(flag in outputs[0] for flag in (
                "--print", "--output-format", "--permission-mode", "--strict-mcp-config",
                "--setting-sources", "--no-session-persistence")):
            return "cli_incompatible"
        try:
            status = json.loads(outputs[1])
        except (json.JSONDecodeError, RecursionError):
            return "probe_output_invalid"
        # Project only the two fields that matter; the status also carries email/org.
        if not isinstance(status, dict) or status.get("loggedIn") is not True:
            return "managed_login_unavailable"
        if status.get("authMethod") != "claude.ai":
            # An API-key login is not the Owner's account session.
            return "managed_login_unavailable"
        return "managed_login_ready"
    except (ExecutorRuntimeError, OSError, subprocess.SubprocessError):
        return "cli_unavailable"


def build_claude_argv(cli: str, model: str, sandbox: str) -> list[str]:
    if sandbox == "read-only":
        allowed = READ_TOOLS
    elif sandbox == "workspace-write":
        allowed = READ_TOOLS + WRITE_TOOLS + CHECK_COMMANDS
    else:
        raise ExecutorRuntimeError("claude_code_sandbox_invalid")
    return [cli, "-p", "--output-format", "stream-json", "--verbose", "--no-session-persistence",
            "--model", validate_claude_model(model), "--permission-mode", "dontAsk",
            "--setting-sources", "user", "--strict-mcp-config",
            "--allowedTools", *allowed, "--disallowedTools", *DENIED_TOOLS]


def claude_executor_kwargs(task, *, binding_resolver, artifact_input=None):
    from .codex_executor import codex_executor_kwargs
    return codex_executor_kwargs(task, binding_resolver=binding_resolver,
                                 artifact_input=artifact_input, kind="claude_code")


class ClaudeCodeExecutor(CodexExecutor):
    """Single-mode native executor backed by the Owner's Claude account."""

    KIND = "claude_code"
    LABEL = "Claude Code"
    PROVIDER_ID = "claude-code"
    # --setting-sources user and --strict-mcp-config already ignore project
    # settings and MCP servers, so repository files cannot add hooks or tools.
    PROJECT_CONFIG: tuple[str, ...] = ()
    default_readiness_probe = staticmethod(probe_claude_code_readiness)

    def __init__(self, *, claude_exe: str | None = None, **kwargs):
        super().__init__(codex_exe=claude_exe, **kwargs)

    def _validate_options(self) -> None:
        build_claude_argv("claude", self._model_id, self._sandbox)

    def _resolve_cli(self) -> str:
        return resolve_claude_cli(self._codex_exe)

    def _argv(self, prepared) -> list[str]:
        # The workspace is the process cwd; the prompt arrives on stdin.
        return build_claude_argv(prepared.cli_path, self._model_id, self._sandbox)

    def _child_env(self) -> dict[str, str]:
        return claude_child_env(self._parent_env)

    def _parser(self, callback):
        return ClaudeStreamJson(callback)
