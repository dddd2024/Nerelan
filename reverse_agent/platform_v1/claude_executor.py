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

# Claude Code has no OS sandbox here, so the model gets no tool that runs
# commands or code at all. --restricted removes Bash/PowerShell/REPL-style tools
# and WebFetch, ignores every settings file and confines file tools to the
# working directory; --tools then names the only built-ins that exist. Running
# tests is the host's job after the turn (git_diff_check, functional checks).
READ_TOOLS = ("Read", "Glob", "Grep")
# Claude Code may pick a separate small/fast or per-tier model; in relay mode all point at the leased one.
RELAY_MODEL_VARIABLES = ("ANTHROPIC_MODEL", "ANTHROPIC_SMALL_FAST_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
                         "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL")
WRITE_TOOLS = ("Edit", "Write")


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
        # Proxy variables stay out: their URLs can carry credentials.
        "systemdrive", "comspec", "windir", "programfiles", "programfiles(x86)", "programdata",
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
                "--restricted", "--tools", "--permission-prompts", "--no-session-persistence")):
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
        tools, mode = READ_TOOLS, "dontAsk"
    elif sandbox == "workspace-write":
        # acceptEdits approves edits to files inside the working directory only.
        tools, mode = READ_TOOLS + WRITE_TOOLS, "acceptEdits"
    else:
        raise ExecutorRuntimeError("claude_code_sandbox_invalid")
    return [cli, "-p", "--output-format", "stream-json", "--verbose", "--no-session-persistence",
            "--model", validate_claude_model(model), "--restricted", "--strict-mcp-config",
            "--tools", ",".join(tools), "--permission-mode", mode,
            # Nobody answers prompts in an unattended run: deny instead of waiting.
            "--permission-prompts", "none"]


def claude_executor_kwargs(task, *, binding_resolver, artifact_input=None):
    from .codex_executor import codex_executor_kwargs
    return codex_executor_kwargs(task, binding_resolver=binding_resolver,
                                 artifact_input=artifact_input, kind="claude_code")


class ClaudeCodeExecutor(CodexExecutor):
    """Single-mode native executor backed by the Owner's Claude account."""

    KIND = "claude_code"
    LABEL = "Claude Code"
    PROVIDER_ID = "claude-code"
    # --restricted ignores every settings file and --strict-mcp-config skips MCP
    # servers, so repository files cannot add hooks, permissions or tools.
    PROJECT_CONFIG: tuple[str, ...] = ()
    default_readiness_probe = staticmethod(probe_claude_code_readiness)

    def __init__(self, *, claude_exe: str | None = None, **kwargs):
        try:
            super().__init__(codex_exe=claude_exe, **kwargs)
        except ExecutorRuntimeError as exc:
            if str(exc) == "codex_model_id_invalid":
                raise ExecutorRuntimeError("claude_code_model_id_invalid") from None
            raise

    @property
    def relay_mode(self) -> bool:
        """An Anthropic-compatible API-key model run through the host's credential relay."""
        return bool(self._binding_resolution is not None and self._binding_resolution.relay_required)

    def _accept_binding(self, resolution) -> None:
        if resolution.executor_id == self.KIND and resolution.relay_required and resolution.auth_method == "api_key":
            if self._lease_provider is None:
                raise ExecutorRuntimeError("claude_code_relay_requires_lease_provider")
            return
        super()._accept_binding(resolution)

    def _require_ready(self, cli) -> None:
        if not self.relay_mode:
            super()._require_ready(cli)  # the Owner's claude.ai login
            return
        # Relay mode never uses the saved login, only a CLI new enough for the confined flags.
        if self._readiness_probe(cli) not in {"managed_login_ready", "managed_login_unavailable"}:
            raise ExecutorRuntimeError("claude_code_cli_unavailable")

    def execute_role_prepared(self, prepared, store, *, role_context, event_callback=None):
        if not self.relay_mode:
            return super().execute_role_prepared(prepared, store, role_context=role_context,
                                                 event_callback=event_callback)
        lease = self._lease_provider(self._binding_resolution)
        try:
            lease.bind_execution_deadline(self._timeout)
            # The child sees only the loopback relay and a short-lived capability, never the provider key.
            self._relay_env = {"ANTHROPIC_BASE_URL": lease.relay_url, "ANTHROPIC_AUTH_TOKEN": lease.lease_id,
                               "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                               # The lease admits one model; background/small-model calls must use it too.
                               **{name: self._model_id for name in RELAY_MODEL_VARIABLES}}
            return super().execute_role_prepared(prepared, store, role_context=role_context,
                                                 event_callback=event_callback)
        finally:
            self._relay_env = {}
            lease.release()

    def _validate_options(self) -> None:
        build_claude_argv("claude", self._model_id, self._sandbox)

    def _resolve_cli(self) -> str:
        return resolve_claude_cli(self._codex_exe)

    def _argv(self, prepared) -> list[str]:
        # The workspace is the process cwd; the prompt arrives on stdin.
        return build_claude_argv(prepared.cli_path, self._model_id, self._sandbox)

    def _child_env(self) -> dict[str, str]:
        return {**claude_child_env(self._parent_env), **getattr(self, "_relay_env", {})}

    def _parser(self, callback):
        return ClaudeStreamJson(callback)
