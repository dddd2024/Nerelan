"""OpenCode CLI executor for Platform V1.

Thin executor that launches the already-installed OpenCode CLI as a separate
child process inside a real Git worktree linked to the configured source
repository.

Boundaries:
- Never operates on the source checkout directly.
- Never reads or migrates credentials.
- Never runs shell=True with untrusted input.
- Prompt explicitly forbids commit, push, PR, merge, release, and
  filesystem access outside the worktree.
- JSON-line output is parsed defensively; malformed lines never crash the
  TaskService.
- Secret-like values are redacted recursively before persistence.
- Deterministic ``git diff --check`` validation runs independently of the
  model's self-reported status.
- CLI invocation is injectable/fakeable for unit testing.
- For api_key bindings, the executor obtains a short-lived execution-scoped
  lease from a trusted relay before launching OpenCode; the provider master
  key never enters the child process.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from .binding_resolver import OpenCodeBindingResolution
from .task_runtime import (
    ExecutorCallback,
    ExecutorResult,
    ExecutorRuntimeError,
    LocalValidationRunner,
    _digest,
    _sanitize_output,
)


# ---------------------------------------------------------------------------
# Bounded evidence limits (documented for tests)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ExecutionLeaseHandle:
    """Handle returned by the trusted lease provider.

    The executor uses the lease_id and relay_url to configure OpenCode,
    then calls ``release()`` after the subprocess completes (success,
    failure, or timeout). The release callback, when present, invokes the
    trusted host's manager.release_lease(exact_lease_id). The callback is
    consumed once (idempotent) and never exposes the provider master.
    """

    lease_id: str
    relay_url: str
    model_id: str
    _release_callback: Callable[[], None] | None = None

    def release(self) -> None:
        callback = self._release_callback
        if callback is None:
            return
        self._release_callback = None
        try:
            callback()
        except Exception:
            pass


LeaseProvider = Callable[[OpenCodeBindingResolution], ExecutionLeaseHandle]


@dataclass
class PreparedWorkspaceContext:
    """Bounded metadata returned by prepare_worktree_once().

    Passed into execute_role_prepared() so all three sequential roles
    planner->coder->reviewer run inside the SAME already-prepared linked
    worktree without re-running CLI resolution, binding setup, or
    worktree creation.
    """
    worktree: Path
    base_sha: str
    execution_id: str
    cli_path: str
    is_cmd: bool
    opencode_exe: str | None


@dataclass
class RoleContext:
    """Bounded instruction payload for one bounded role execution.

    ``role`` is one of ``planner``, ``coder``, ``reviewer``.
    ``task_id`` and ``workspace`` MUST equal the single durable Task's
    task_id and the shared worktree path for every role in the sequence.
    ``plan_path`` points to the planner's runtime handoff (``.reverse-agent-handoff/plan.md``)
    and is required by both ``coder`` (as input) and ``reviewer`` (as input).
    ``plan_digest`` is the SHA-256 of the planner handoff captured by the
    caller before the role runs; it is recorded into the result so the
    TaskExecutionService can prove role-order/shared-workspace evidence.
    """
    role: str
    task_id: str
    workspace: Path
    plan_path: Path | None = None
    plan_digest: str = ""
    role_order_index: int = 0


MAX_EVIDENCE_ITEMS = 40
MAX_EVIDENCE_STRING_LEN = 250
MAX_EVIDENCE_DEPTH = 6
MAX_EVIDENCE_TOTAL_BYTES = 64 * 1024

# Runtime handoff directory shared between sequential planner/coder/reviewer
# roles inside one executor-owned linked worktree. Files in this directory
# are runtime communication, never product changes.
_HANDOFF_DIR = ".reverse-agent-handoff"
_PLAN_HANDOFF = "plan.md"
_REVIEW_HANDOFF = "review.md"
_MAX_HANDOFF_BYTES = 128 * 1024  # 128 KiB
_SEQUENTIAL_ROLES = ("planner", "coder", "reviewer")


# ---------------------------------------------------------------------------
# Recursive secret redaction
# ---------------------------------------------------------------------------

_SECRET_KEYS = {
    "authorization",
    "auth",
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "passwd",
    "pwd",
    "credential",
    "cookie",
}

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(authorization)\s*[:=]\s*\S+"), r"\1: [REDACTED]"),
    (re.compile(r"(?i)\"?(api[_-]?key|apikey)\"?\s*[:=]\s*\S+"), r"\1: [REDACTED]"),
    (re.compile(r"(?i)\"?(token)\"?\s*[:=]\s*\S{8,}"), r"\1: [REDACTED]"),
    (re.compile(r"(?i)\"?(password|passwd|pwd)\"?\s*[:=]\s*\S+"), r"\1: [REDACTED]"),
    (re.compile(r"(?i)\"?(secret)\"?\s*[:=]\s*\S+"), r"\1: [REDACTED]"),
    (re.compile(r"(?i)\"?(credential)\"?\s*[:=]\s*\S+"), r"\1: [REDACTED]"),
    (re.compile(r"(?i)\"?(cookie)\"?\s*[:=]\s*\S+"), r"\1: [REDACTED]"),
    (re.compile(r"(?i)bearer\s+[a-zA-Z0-9+/=]{16,}"), "[REDACTED]"),
    (re.compile(r"(?i)basic\s+[a-zA-Z0-9+/=]{16,}"), "[REDACTED]"),
    (re.compile(r"(?i)(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{20,}"), "[REDACTED]"),
]


def redact_secrets(text: str) -> str:
    """Remove common secret patterns from captured text."""
    if not text:
        return text
    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def _redact_recursively(obj: Any, depth: int = 0, total_bytes: int = 0) -> Any:
    if total_bytes > MAX_EVIDENCE_TOTAL_BYTES:
        return "[REDACTED: payload_too_large]"
    if depth > MAX_EVIDENCE_DEPTH:
        return "[REDACTED: max_depth_exceeded]"
    if isinstance(obj, str):
        sanitized = redact_secrets(obj)
        if len(sanitized) > MAX_EVIDENCE_STRING_LEN:
            _trunc_suffix = "...[TRUNCATED]"
            sanitized = sanitized[:MAX_EVIDENCE_STRING_LEN - len(_trunc_suffix)] + _trunc_suffix
        return sanitized
    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            key_str = str(key)
            if key_str.lower() in _SECRET_KEYS:
                out[key_str] = "[REDACTED]"
                total_bytes += len(key_str) + 11
            else:
                out[key_str] = _redact_recursively(
                    value, depth + 1, total_bytes + len(key_str)
                )
        return out
    if isinstance(obj, (list, tuple)):
        result: list[Any] = []
        for item in obj:
            total_bytes += 1
            result.append(_redact_recursively(item, depth + 1, total_bytes))
        return list(obj) if isinstance(obj, tuple) else result
    return str(obj)[:MAX_EVIDENCE_STRING_LEN]


# ---------------------------------------------------------------------------
# Model identifier validation
# ---------------------------------------------------------------------------

_MAX_MODEL_ID_LENGTH = 128
_MODEL_ID_RE = re.compile(r"^[A-Za-z0-9._:/@\-]{1,128}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")

_BINDING_CHILD_ENV_ALLOWLIST = (
    "PATH",
    "SystemRoot",
)


def validate_model_id(model_id: str) -> str:
    if not isinstance(model_id, str):
        raise ExecutorRuntimeError("model_id_must_be_string")
    if not model_id:
        raise ExecutorRuntimeError("model_id_required")
    stripped = model_id.strip()
    if stripped != model_id:
        raise ExecutorRuntimeError("model_id_must_not_have_leading_trailing_whitespace")
    if len(stripped) > _MAX_MODEL_ID_LENGTH:
        raise ExecutorRuntimeError("model_id_too_long")
    if _CONTROL_RE.search(stripped):
        raise ExecutorRuntimeError("model_id_contains_control_characters")
    if not _MODEL_ID_RE.match(stripped):
        raise ExecutorRuntimeError("model_id_contains_invalid_characters")
    parts = stripped.split("/", 1)
    if len(parts) == 2:
        if not parts[0] or not parts[1]:
            raise ExecutorRuntimeError("model_id_must_be_provider_model_form")
    if any(c.isspace() for c in stripped):
        raise ExecutorRuntimeError("model_id_contains_whitespace")
    return stripped


_TRANSIENT_PROVIDER_ID = "reverse-agent-relay"
_TRANSIENT_PROVIDER_NPM = "@ai-sdk/openai-compatible"
_TRANSIENT_PROVIDER_NAME = "Reverse Agent Relay"

_OPENCODE_DISABLE_ENV = {
    "OPENCODE_DISABLE_AUTOUPDATE": "true",
    "OPENCODE_DISABLE_MODELS_FETCH": "true",
    "OPENCODE_DISABLE_LSP_DOWNLOAD": "true",
    "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true",
    "OPENCODE_DISABLE_CLAUDE_CODE": "true",
}


def build_binding_config_content(
    resolution: OpenCodeBindingResolution,
    lease: ExecutionLeaseHandle | None = None,
) -> str:
    """Build transient non-secret provider metadata for one OpenCode child.

    For api_key bindings (lease is provided), the config contains only the
    relay URL and the execution-scoped lease under a dedicated transient
    custom provider. The provider master key is never present. OpenCode model
    IDs are of the form ``provider_id/model_id``; the CLI selector therefore
    uses the transient provider ID as its prefix so OpenCode routes inference
    through this custom OpenAI-compatible provider.

    For non-api_key bindings (none/external_cli_session/account_login), the
    config keys providers under the actual Connection provider ID
    (``resolution.provider_id``) rather than ``reverse-agent-relay``. The
    adapter remains ``@ai-sdk/openai-compatible``, the ``baseURL`` comes from
    the Connection, and no ``apiKey``/token/cookie/credential material is
    ever written. OpenCode resolves credentials itself via persisted provider
    auth by provider ID.
    """
    if lease is not None:
        if not lease.lease_id:
            raise ExecutorRuntimeError("lease_id_required")
        if not lease.relay_url:
            raise ExecutorRuntimeError("relay_url_required")
        provider_key = _TRANSIENT_PROVIDER_ID
        options = {
            "baseURL": lease.relay_url,
            "apiKey": lease.lease_id,
        }
        provider_facing_model = _extract_provider_facing_model(lease.model_id)
    else:
        if resolution.auth_method == "api_key":
            raise ExecutorRuntimeError("api_key_lease_required")
        provider_key = resolution.provider_id or _TRANSIENT_PROVIDER_ID
        options = {"baseURL": resolution.base_url}
        provider_facing_model = _extract_provider_facing_model(resolution.model_id)
    payload = {
        "provider": {
            provider_key: {
                "npm": _TRANSIENT_PROVIDER_NPM,
                "name": _TRANSIENT_PROVIDER_NAME,
                "options": options,
                "models": {provider_facing_model: {}},
            }
        }
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Role-specific runtime permission configuration
# ---------------------------------------------------------------------------

_ROLE_PERMISSION_CONFIGS: dict[str, dict[str, Any]] = {
    "planner": {
        "permission": {
            "edit": {
                "*": "deny",
                ".reverse-agent-handoff/plan.md": "allow",
            },
            "bash": {"*": "deny"},
            "external_directory": {"*": "deny"},
            "task": {"*": "deny"},
            "webfetch": "deny",
            "websearch": "deny",
        }
    },
    "reviewer": {
        "permission": {
            "edit": {
                "*": "deny",
                ".reverse-agent-handoff/review.md": "allow",
            },
            "bash": {
                "*": "deny",
                "git diff*": "allow",
                "git status*": "allow",
            },
            "external_directory": {"*": "deny"},
            "task": {"*": "deny"},
            "webfetch": "deny",
            "websearch": "deny",
        }
    },
    "coder": {
        "permission": {
            "bash": {
                "git commit*": "deny",
                "git push*": "deny",
                "git merge*": "deny",
                "git tag*": "deny",
            },
        }
    },
}


def build_role_permission_config(role: str) -> str | None:
    """Build the role-specific OpenCode permission config JSON for one role.

    Returns a compact JSON string for ``planner`` and ``reviewer`` roles.
    For ``coder`` the config restricts only dangerous repository publication
    commands; it does NOT install a wildcard product edit deny. For any
    other role (including ordinary executor), returns None to leave
    permission policy untouched.
    """
    payload = _ROLE_PERMISSION_CONFIGS.get(role)
    if payload is None:
        return None
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _merge_opencode_config(existing: str | None, role_config: str | None) -> str | None:
    """Merge an existing config with a role permission config.

    If neither is provided, return None. If only one is provided,
    return that one as JSON. If both are provided, merge them into a
    single JSON object preserving both ``provider`` and ``permission``
    keys.
    """
    merged: dict[str, Any] = {}
    if existing:
        try:
            parsed = json.loads(existing)
            if isinstance(parsed, dict):
                merged = parsed
        except (json.JSONDecodeError, TypeError):
            pass
    if role_config:
        try:
            parsed = json.loads(role_config)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    merged[k] = v
        except (json.JSONDecodeError, TypeError):
            pass
    if not merged:
        return None
    return json.dumps(merged, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def build_role_child_env(
    parent_env: Mapping[str, str],
    existing_config: str | None,
    role: str,
) -> dict[str, str]:
    """Build the child environment for a sequential role execution.

    For Binding/relay sessions the existing provider config is preserved
    and role permissions are merged in. For direct authenticated sessions
    (no binding config), the parent environment is copied in full (not
    restricted to the Binding allowlist) and role permissions are injected
    via OPENCODE_CONFIG_CONTENT. The OpenCode safety disable flags are
    injected regardless.
    """
    child: dict[str, str] = {}
    if existing_config:
        for key in _BINDING_CHILD_ENV_ALLOWLIST:
            value = parent_env.get(key)
            if isinstance(value, str) and value:
                child[key] = value
        for key, value in _OPENCODE_DISABLE_ENV.items():
            child[key] = value
        merged = _merge_opencode_config(existing_config, build_role_permission_config(role))
        if merged:
            child["OPENCODE_CONFIG_CONTENT"] = merged
    else:
        for key, value in parent_env.items():
            if isinstance(value, str) and value:
                child[key] = value
        for key, value in _OPENCODE_DISABLE_ENV.items():
            child[key] = value
        role_perm = build_role_permission_config(role)
        if role_perm:
            child["OPENCODE_CONFIG_CONTENT"] = role_perm
    return child


def _extract_provider_facing_model(cli_model_id: str) -> str:
    """Extract the provider-facing model from a CLI selector.

    Given ``reverse-agent-relay/gpt-4o`` return ``gpt-4o``.
    Given ``openai-compatible/gpt-4o`` return ``gpt-4o``.
    Given ``gpt-4o`` return ``gpt-4o``.
    Never strip slashes that are part of the provider-facing model itself.
    Only the first slash separates the CLI provider prefix from the
    provider-facing model.
    """
    if "/" not in cli_model_id:
        return cli_model_id
    return cli_model_id.split("/", 1)[1]


def build_binding_child_env(
    parent_env: Mapping[str, str],
    config_content: str,
) -> dict[str, str]:
    """Copy only explicit non-secret runtime/location keys for Binding launch.

    Fixed executor-chosen OpenCode safety flags are injected regardless of
    parent env. These disable unrelated network/plugin surfaces so the fake
    loopback relay/provider is the only inference network target.
    """
    child: dict[str, str] = {}
    for key in _BINDING_CHILD_ENV_ALLOWLIST:
        value = parent_env.get(key)
        if isinstance(value, str) and value:
            child[key] = value
    for key, value in _OPENCODE_DISABLE_ENV.items():
        child[key] = value
    child["OPENCODE_CONFIG_CONTENT"] = config_content
    return child


# ---------------------------------------------------------------------------
# CLI resolution
# ---------------------------------------------------------------------------

def resolve_opencode_cli(exe: str | None = None) -> tuple[str, bool]:
    """Resolve the OpenCode CLI path.

    Returns ``(path, is_cmd)`` where ``is_cmd`` indicates the executable
    is a ``.cmd`` / ``.bat`` launcher. On Windows, prefer the true
    ``.exe`` if it can be deterministically resolved without installation
    or PATH mutation; fall back to ``.cmd`` / ``.bat`` only if no ``.exe``
    is found.
    """
    if exe:
        p = exe.strip()
        return p, p.lower().endswith((".cmd", ".bat"))

    is_windows = platform.system() == "Windows"
    if is_windows:
        exe_path = _resolve_windows_exe()
        if exe_path:
            return exe_path, False
        cmd_path = _resolve_windows_cmd()
        if cmd_path:
            return cmd_path, True
    else:
        path = shutil.which("opencode")
        if path:
            return path, False

    raise ExecutorRuntimeError("opencode_cli_not_found")


def _resolve_windows_exe() -> str | None:
    """Find the true opencode.exe without PATH mutation or installation."""
    # 1. Try `where.exe opencode.exe`
    for candidate in ("opencode.exe", "opencode"):
        try:
            proc = subprocess.run(
                ["where.exe", candidate],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    p = line.strip()
                    if p and p.lower().endswith(".exe"):
                        return p
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # 2. Follow npm shim: `where.exe opencode` -> parent/node_modules/opencode-ai/bin/opencode.exe
    try:
        proc = subprocess.run(
            ["where.exe", "opencode"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                shim = line.strip()
                if not shim:
                    continue
                shim_path = Path(shim)
                npm_bin = shim_path.parent
                exe_candidate = npm_bin / "node_modules" / "opencode-ai" / "bin" / "opencode.exe"
                if exe_candidate.is_file():
                    return str(exe_candidate)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _resolve_windows_cmd() -> str | None:
    """Fallback: find opencode.cmd/.bat if no .exe found."""
    try:
        proc = subprocess.run(
            ["where.exe", "opencode.cmd"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                p = line.strip()
                if p and p.lower().endswith((".cmd", ".bat")):
                    return p
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


# ---------------------------------------------------------------------------
# OpenCode persisted auth metadata probe
# ---------------------------------------------------------------------------

# Provider IDs accepted by reverse-agent. Only safe identifier grammar is
# accepted; display labels ("GitHub Copilot") must not be auto-mapped to an ID.
_SAFE_PROVIDER_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_TERMINAL_GLYPHS_RE = re.compile(
    r"[●◆▪▸►■□▪▫├└┴┬┼│─┌┐┘└├┤┬┴┼░▒▓█]"
)
_AUTH_TYPE_TOKEN_STRIP_RE = re.compile(r"[^A-Za-z0-9_]+$")

_ALLOWED_AUTH_TYPES = frozenset({
    "api",
    "oauth",
    "sso",
    "account_login",
    "external_cli_session",
    "api_key",
    "session",
    "credential",
})

_AUTH_LIST_COMMANDS = ("auth", "list")
_AUTH_LS_COMMANDS = ("auth", "ls")

_AUTH_PROBE_ENV = dict(_OPENCODE_DISABLE_ENV)


def parse_opencode_auth_list(stdout: str) -> dict[str, str]:
    """Parse sanitized OpenCode ``auth list`` output into {provider_id: auth_type}.

    Only provider identity and auth type are returned. No raw stdout,
    credential-file path, header, or auth.json path ever appears in the
    returned metadata.

    Accepted input shapes (in order of attempt):
      - JSON object: {"providers": [{"id": "sensetime", "authType": "api"}, ...]}
      - JSON array:  [{"id": "sensetime", "authType": "api"}, ...]
      - JSON object with top-level list-valued keys whose values look like
        provider records: {"sensetime": [{"authType": "api"}]}
      - Human-readable terminal list (OpenCode 1.18.x default):
            Credentials <path>
            ● sensetime api
            ● GitHub Copilot oauth
            2 credentials

    A provider ID is accepted only when it matches the safe identifier
    grammar. Display labels like "GitHub Copilot" do not match and are
    silently ignored rather than auto-mapped to "github-copilot".

    Malformed or unrecognized output returns an empty mapping.
    """
    if not stdout:
        return {}
    text = stdout.strip()
    if not text:
        return {}
    result = _try_json_auth_list_parse(text)
    if result is not None:
        return result
    return _parse_opencode_auth_list_text(stdout)


def _try_json_auth_list_parse(text: str) -> dict[str, str] | None:
    """Try to parse JSON-shaped auth list output. Returns None on JSON failure
    so the caller can fall through to text parsing."""
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    result: dict[str, str] = {}
    records: list[Any]
    if isinstance(parsed, list):
        records = parsed
    elif isinstance(parsed, dict):
        providers = parsed.get("providers")
        if isinstance(providers, list):
            records = providers
        else:
            records = _dict_values_to_records(parsed)
    else:
        return {}
    if not isinstance(records, list):
        return {}
    for entry in records:
        if not isinstance(entry, dict):
            continue
        pid = _extract_value(entry, ("id", "provider", "providerId", "name"))
        if not pid or not isinstance(pid, str):
            continue
        pid = pid.strip()
        if not pid:
            continue
        if not _SAFE_PROVIDER_ID_RE.match(pid):
            continue
        if pid in result:
            continue
        auth_type = _extract_value(entry, ("authType", "auth_type", "type", "kind"))
        if not auth_type or not isinstance(auth_type, str):
            auth_type = "unknown"
        else:
            auth_type = auth_type.strip() or "unknown"
        if auth_type.lower() not in _ALLOWED_AUTH_TYPES:
            continue
        result[pid] = auth_type
    return result


def _parse_opencode_auth_list_text(stdout: str) -> dict[str, str]:
    """Parse human-readable OpenCode ``auth list`` terminal output.

    Expected real CLI shape (OpenCode 1.18.x):
        Credentials /home/user/.config/opencode/credentials.json
        ● sensetime api
        ● GitHub Copilot oauth
        2 credentials

    Rules:
      - ANSI escape sequences are stripped before any parsing.
      - Terminal glyphs (bullets, box-drawing characters) are stripped.
      - Each non-empty line is split on whitespace into tokens.
      - The last token is the candidate auth type; it must be an
        exact member of _ALLOWED_AUTH_TYPES (case-insensitive match,
        stored lowercase).
      - All preceding tokens joined by a single space form the candidate
        provider label; it must exactly match the safe identifier regex
        _SAFE_PROVIDER_ID_RE. No slugification, no case guessing, no
        space-to-hyphen replacement, no fuzzy matching.
      - Headers ("Credentials ..."), file paths, total-count lines,
        environment sections, empty lines, and unrecognized lines are
        silently ignored.
      - No raw stdout, credential path, or CLI decoration is persisted
        or returned.
    """
    result: dict[str, str] = {}
    cleaned = _ANSI_ESCAPE_RE.sub("", stdout)
    for raw_line in cleaned.splitlines():
        line = _TERMINAL_GLYPHS_RE.sub("", raw_line).strip()
        if not line:
            continue
        tokens = line.split()
        if len(tokens) < 2:
            continue
        raw_auth_type = tokens[-1]
        auth_type = _AUTH_TYPE_TOKEN_STRIP_RE.sub("", raw_auth_type).lower()
        if not auth_type:
            continue
        if auth_type not in _ALLOWED_AUTH_TYPES:
            continue
        provider_label = " ".join(tokens[:-1]).strip()
        if not provider_label:
            continue
        if not _SAFE_PROVIDER_ID_RE.match(provider_label):
            continue
        if provider_label in result:
            continue
        result[provider_label] = auth_type
    return result


def _extract_value(entry: Mapping[str, Any], candidates: tuple[str, ...]) -> Any:
    for key in candidates:
        v = entry.get(key)
        if v is not None and v != "":
            return v
    return None


def _dict_values_to_records(mapping: Mapping[str, Any]) -> list[Any]:
    records: list[Any] = []
    for value in mapping.values():
        if isinstance(value, dict):
            records.append(value)
        elif isinstance(value, list):
            records.extend(value)
        else:
            records.append({"name": value})
    return records


def execute_opencode_auth_list_probe(
    *,
    subprocess_run: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    opencode_exe: str | None = None,
) -> dict[str, str]:
    """Run the sanitized OpenCode auth-list probe and return provider metadata.

    Executes ``opencode auth list`` (falling back to ``opencode auth ls``).
    The child environment is restricted to the Binding-compatible
    non-secret allowlist plus the OpenCode safety-disable flags; no
    arbitrary parent environment is copied.

    On any failure (CLI missing, nonzero exit, malformed output,
    timeout) the probe returns an empty authenticated-provider set so the
    trusted host may still start with external sessions marked ``missing``.
    """
    run = subprocess_run or subprocess.run
    try:
        cli_path, _is_cmd = resolve_opencode_cli(exe=opencode_exe)
    except ExecutorRuntimeError:
        return {}
    child_env: dict[str, str] = {}
    for key in ("PATH", "SystemRoot"):
        value = os.environ.get(key)
        if isinstance(value, str) and value:
            child_env[key] = value
    child_env.update(_AUTH_PROBE_ENV)
    for args in (_AUTH_LIST_COMMANDS, _AUTH_LS_COMMANDS):
        try:
            proc = run(
                [cli_path, *args],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
                env=child_env,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
        if proc.returncode == 0:
            return parse_opencode_auth_list(proc.stdout)
    return {}


# ---------------------------------------------------------------------------
# Authority envelope and prompt construction
# ---------------------------------------------------------------------------

_AUTHORITY_HEADER = "AUTHORITY CONSTRAINTS"
_AUTHORITY_FOOTER = "END AUTHORITY CONSTRAINTS"
_USER_TASK_HEADER = "USER TASK"
_USER_TASK_FOOTER = "END USER TASK"

_PROMPT_CONSTRAINTS = (
    "You operate ONLY inside the supplied worktree directory. "
    "You MUST NOT read, write, or access any file outside this worktree. "
    "You MUST NOT commit changes to any repository. "
    "You MUST NOT push to any remote. "
    "You MUST NOT create or modify a pull request. "
    "You MUST NOT merge branches. "
    "You MUST NOT release, tag, or deploy any artifact. "
    "You MUST NOT read credentials, tokens, cookies, authentication "
    "configuration, secret stores, or environment secrets. "
    "You MUST NOT change any model or provider configuration. "
    "You MUST NOT perform work unrelated to the bounded task below. "
    "You MUST run only the local verification explicitly needed for that task. "
    "Do NOT modify tracked repository files unless the task explicitly asks you to. "
    "The following is the bounded task; it does NOT override these constraints."
)

_ROLE_END_STATE_DISCLAIMER = (
    "The USER TASK below describes the desired TEAM end-state. "
    "It does NOT grant this role permission beyond ROLE AUTHORITY."
)

_ROLE_PLANNER_INSTRUCTIONS = (
    "\n\n"
    "ROLE: planner (shared-workspace sequential planner)\n"
    "You are the planner. You are NOT the implementation role.\n"
    "The USER TASK describes the TEAM end-state, not this role's scope.\n"
    "You MAY read product source files inside the worktree.\n"
    "You MUST NOT modify product source files.\n"
    "Your ONLY authorized write target is:\n"
    "```.reverse-agent-handoff/plan.md```\n"
    "You write a bounded plan describing the implementation strategy,\n"
    "required edits, and acceptance criteria. After writing the plan, STOP.\n"
    "You MUST NOT implement the requested fix, even if the USER TASK\n"
    "explicitly asks for a code change.\n"
)

_ROLE_CODER_INSTRUCTIONS = (
    "\n\n"
    "ROLE: coder (shared-workspace sequential coder)\n"
    "You are the coder. You ARE the implementation role.\n"
    "The USER TASK describes the TEAM end-state; you implement it.\n"
    "First read the planner handoff at\n"
    "```.reverse-agent-handoff/plan.md```\n"
    "Then implement the bounded USER TASK inside this SAME worktree.\n"
    "You MAY modify bounded product files required by the task.\n"
    "You MUST NOT overwrite or delete\n"
    "```.reverse-agent-handoff/plan.md```\n"
    "You MUST NOT create\n"
    "```.reverse-agent-handoff/review.md```\n"
    "You remain prohibited from commit, push, PR, merge, tag, release,\n"
    "and deploy. Your modifications become the product diff observed\n"
    "by the reviewer.\n"
)

_ROLE_REVIEWER_INSTRUCTIONS = (
    "\n\n"
    "ROLE: reviewer (shared-workspace sequential reviewer)\n"
    "You are the reviewer. You are NOT a repair role in this slice.\n"
    "The USER TASK describes the TEAM end-state, not this role's scope.\n"
    "You MAY read product source files, the planner plan, and the\n"
    "coder diff.\n"
    "You MUST NOT modify product source files.\n"
    "Your ONLY authorized write target is:\n"
    "```.reverse-agent-handoff/review.md```\n"
    "Observe: (1) the planner handoff at\n"
    "```.reverse-agent-handoff/plan.md```, and (2) the current\n"
    "uncommitted git diff (``git diff HEAD``) -- that is the coder's\n"
    "product diff. Write your bounded review to\n"
    "```.reverse-agent-handoff/review.md```. Do NOT rewrite, amend, or\n"
    "repair any product file in this slice. You MUST NOT fix a defect\n"
    "you discover.\n"
)

_ROLE_INSTRUCTIONS: dict[str, str] = {
    "planner": _ROLE_PLANNER_INSTRUCTIONS,
    "coder": _ROLE_CODER_INSTRUCTIONS,
    "reviewer": _ROLE_REVIEWER_INSTRUCTIONS,
}


def build_prompt(task_title: str, worktree: str) -> str:
    """Build the bounded authority envelope wrapping the user task."""
    return (
        f"{_AUTHORITY_HEADER}\n"
        f"{_PROMPT_CONSTRAINTS}\n"
        f"Worktree: {worktree}\n"
        f"{_AUTHORITY_FOOTER}\n"
        f"{_USER_TASK_HEADER}\n"
        f"{task_title}\n"
        f"{_USER_TASK_FOOTER}"
    )


def build_role_prompt(
    task_title: str,
    worktree: str,
    role_context: RoleContext | None = None,
) -> str:
    """Build an authority envelope with an optional bounded role instruction.

    For sequential roles (planner/coder/reviewer) the ROLE AUTHORITY section
    is placed INSIDE the authority block BEFORE the USER TASK so the
    role-specific constraints are established before the user task is
    presented. The user task is always the last region and is framed as
    the TEAM end-state, not as a grant of permission.

    For ordinary non-sequential execution (role_context=None or
    role_context.role not in _ROLE_INSTRUCTIONS) the existing build_prompt()
    behavior is preserved exactly.
    """
    if role_context is None:
        return build_prompt(task_title, worktree)
    role = role_context.role
    instructions = _ROLE_INSTRUCTIONS.get(role)
    if instructions is None:
        return build_prompt(task_title, worktree)
    return (
        f"{_AUTHORITY_HEADER}\n"
        f"{_PROMPT_CONSTRAINTS}\n"
        f"ROLE AUTHORITY:\n"
        f"{instructions}\n"
        f"{_ROLE_END_STATE_DISCLAIMER}\n"
        f"Worktree: {worktree}\n"
        f"{_AUTHORITY_FOOTER}\n"
        f"{_USER_TASK_HEADER}\n"
        f"{task_title}\n"
        f"{_USER_TASK_FOOTER}"
    )


def _write_prompt_file(content: str) -> Path:
    fd, path = tempfile.mkstemp(
        prefix="opencode_prompt_", suffix=".txt", dir=tempfile.gettempdir()
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise
    return Path(path)


# ---------------------------------------------------------------------------
# Command construction
# ---------------------------------------------------------------------------

_CLI_POSITIONAL_MESSAGE = "execute bounded task from attached prompt file"


def handoff_dir(workspace: Path) -> Path:
    return workspace / _HANDOFF_DIR


def _iter_handoff_files(handoff: Path) -> list[Path]:
    if not handoff.is_dir():
        return []
    return sorted(p for p in handoff.iterdir() if p.is_file())


def _has_handoff_files(handoff: Path) -> bool:
    return any(True for _ in _iter_handoff_files(handoff))


def _remove_handoff(handoff: Path) -> bool:
    """Remove the handoff directory recursively if it exists and contains files.

    Returns True iff the directory existed and had at least one file (i.e.
    there was something to clean up).
    """
    if not handoff.is_dir():
        return False
    if not _has_handoff_files(handoff):
        return False
    shutil.rmtree(handoff, ignore_errors=True)
    return not handoff.exists()


def build_opencode_argv(
    cli_path: str,
    *,
    is_cmd: bool,
    model_id: str,
    worktree: str,
    prompt_file: str = "",
    prompt: str = "",
    use_auto: bool = False,
) -> tuple[list[str], str]:
    """Build the argv for the OpenCode CLI.

    The user task text is transported via the ``--file`` flag to an
    executor-owned UTF-8 prompt file when ``prompt_file`` is provided.
    The legacy ``prompt`` kwarg is retained for backward-compatible unit
    tests; it places the task text as a positional argv element after
    ``--``. Never ``shell=True`` in either path. The ``--pure`` flag
    disables unrelated OpenCode features so only the configured transient
    provider is used.
    """
    inner = [
        "run",
        "--pure",
        "--model",
        model_id,
        "--dir",
        worktree,
        "--format",
        "json",
    ]
    if use_auto:
        inner.append("--auto")
    if prompt_file:
        inner.extend(["--file", prompt_file])
        inner.extend(["--", _CLI_POSITIONAL_MESSAGE])
        positional = _CLI_POSITIONAL_MESSAGE
    elif prompt:
        inner.extend(["--", prompt])
        positional = prompt
    else:
        inner.extend(["--", _CLI_POSITIONAL_MESSAGE])
        positional = _CLI_POSITIONAL_MESSAGE
    return [cli_path] + inner, positional


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

class OpenCodeExecutor:
    """Launches OpenCode CLI as a child process in a real linked Git worktree."""

    def __init__(
        self,
        *,
        model_id: str | None = None,
        binding_resolution: OpenCodeBindingResolution | None = None,
        parent_env: Mapping[str, str] | None = None,
        repo_dir: str = "",
        base_ref: str = "",
        opencode_exe: str | None = None,
        timeout: int = 300,
        use_auto: bool = True,
        lease_provider: LeaseProvider | None = None,
    ) -> None:
        self._binding_resolution = binding_resolution
        self._lease_provider = lease_provider
        if binding_resolution is not None:
            if binding_resolution.executor_id != "opencode":
                raise ExecutorRuntimeError("binding_executor_mismatch")
            if binding_resolution.auth_method == "api_key":
                if not binding_resolution.relay_required:
                    raise ExecutorRuntimeError("api_key_requires_relay")
                if lease_provider is None:
                    raise ExecutorRuntimeError("lease_provider_required")
            elif binding_resolution.auth_method in {
                "external_cli_session",
                "account_login",
            } and binding_resolution.external_session_status != "available":
                raise ExecutorRuntimeError("external_session_unavailable")
            self._model_id = validate_model_id(binding_resolution.model_id)
        else:
            self._model_id = validate_model_id(
                model_id or os.environ.get("REVERSE_AGENT_OPENCODE_MODEL", "")
            )
        self._parent_env = parent_env if parent_env is not None else os.environ
        self._repo_dir = repo_dir.strip()
        self._repo_dir_explicit = bool(self._repo_dir)
        self._base_ref = base_ref
        self._opencode_exe = opencode_exe
        self._timeout = timeout
        self._use_auto = use_auto

    def execute(
        self,
        task_id: str,
        store: Any,
        *,
        workspace_root: str = "",
        event_callback: ExecutorCallback | None = None,
    ) -> ExecutorResult:
        if not workspace_root:
            raise ExecutorRuntimeError("workspace_root_required")
        if not isinstance(workspace_root, str) or not workspace_root.strip():
            raise ExecutorRuntimeError("workspace_root_must_be_non_empty")

        root_path = Path(workspace_root)
        root_path.mkdir(parents=True, exist_ok=True)
        prepared = self.prepare_worktree_once(
            task_id, root_path, event_callback
        )
        role_context = RoleContext(
            role="executor",
            task_id=task_id,
            workspace=prepared.worktree,
            role_order_index=0,
        )
        return self.execute_role_prepared(
            prepared,
            store,
            role_context=role_context,
            event_callback=event_callback,
        )

    def _run_executor_core(
        self,
        *,
        task_id: str,
        store: Any,
        worktree: Path,
        base_sha: str,
        execution_id: str,
        cli_path: str,
        is_cmd: bool,
        event_callback: ExecutorCallback | None,
        role_context: RoleContext,
    ) -> ExecutorResult:
        """Run the bounded OpenCode role subprocess inside an already-prepared
        worktree and return a normalised ``ExecutorResult``.

        All three sequential roles planner->coder->reviewer reuse the same
        CLI resolution, binding config, child environment isolation, lease
        acquisition, prompt-file transport, subprocess runner, secret
        redaction, evidence parsing/persistence, and ``git diff --check``
        validation. ``role_context`` carries the role-specific instruction
        that is merged into the authority envelope.
        """
        task_title = self._task_title(store, task_id)
        prompt = build_role_prompt(
            task_title,
            str(worktree),
            role_context,
        )
        prompt_file = _write_prompt_file(prompt)

        binding_metadata = self._binding_event_metadata()

        lease_handle: ExecutionLeaseHandle | None = None
        try:
            if self._binding_resolution is not None and self._binding_resolution.relay_required:
                lease_handle = self._lease_provider(self._binding_resolution)

            model_for_cli = self._model_id
            if lease_handle is not None:
                model_for_cli = lease_handle.model_id

            cli_argv, _positional = build_opencode_argv(
                cli_path,
                is_cmd=is_cmd,
                model_id=model_for_cli,
                worktree=str(worktree),
                prompt_file=str(prompt_file),
                use_auto=self._use_auto,
            )

            _emit(event_callback, task_id, {
                "type": "EXECUTOR_RUNNING",
                "title": "OpenCode CLI started",
                "description": "OpenCode child process launched",
                "metadata": {
                    "execution_id": execution_id,
                    "executor_kind": "opencode",
                    "role": role_context.role,
                    "model": model_for_cli,
                    "cli_path": cli_path,
                    "worktree": str(worktree),
                    "prompt_transport": "file",
                    **binding_metadata,
                },
            })

            try:
                run_kwargs: dict[str, Any] = {
                    "cwd": str(worktree),
                    "capture_output": True,
                    "text": True,
                    "encoding": "utf-8",
                    "errors": "replace",
                    "timeout": self._timeout,
                    "check": False,
                }
                role = role_context.role
                is_sequential_role = role in _ROLE_INSTRUCTIONS
                if self._binding_resolution is not None:
                    config_content = build_binding_config_content(
                        self._binding_resolution,
                        lease=lease_handle,
                    )
                    run_kwargs["env"] = build_role_child_env(
                        self._parent_env,
                        config_content,
                        role,
                    )
                elif is_sequential_role:
                    run_kwargs["env"] = build_role_child_env(
                        self._parent_env,
                        None,
                        role,
                    )
                proc = subprocess.run(cli_argv, **run_kwargs)
            finally:
                if lease_handle is not None:
                    try:
                        lease_handle.release()
                    except Exception:
                        pass
        except subprocess.TimeoutExpired as exc:
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "OpenCode timeout",
                "description": "OpenCode CLI exceeded timeout",
                "metadata": {
                    "execution_id": execution_id,
                    "timeout": self._timeout,
                    "failure_classification": "timeout",
                    "role": role_context.role,
                },
            })
            changed_files = _collect_changed_files(worktree)
            return ExecutorResult(
                success=False,
                validation_exit_code=-1,
                validation_command_id="",
                validation_output_digest="",
                validation_output_summary="",
                changed_files=changed_files,
                error="opencode_timeout:%s" % self._timeout,
                workspace=str(worktree),
                execution_id=execution_id,
                process_exit_code=-1,
                failure_classification="timeout",
            )
        except FileNotFoundError as exc:
            return ExecutorResult(
                success=False,
                validation_exit_code=-1,
                validation_command_id="",
                validation_output_digest="",
                validation_output_summary="",
                changed_files=[],
                error="opencode_cli_not_found:%s" % cli_path,
                workspace=str(worktree),
                execution_id=execution_id,
                process_exit_code=-2,
                failure_classification="cli_unavailable",
            )

        exit_code = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        events_raw, _json_error = self._parse_json_lines(stdout)
        executor_evidence = _build_executor_evidence(
            events_raw,
            exit_code=exit_code,
            model_id=self._model_id,
        )
        _emit_executor_evidence_events(event_callback, task_id, execution_id, executor_evidence)
        _persist_executor_evidence(store, task_id, executor_evidence)
        stderr_redacted = redact_secrets(_sanitize_output(stderr, 2048))

        if exit_code != 0:
            fail_class = self._classify_exit(exit_code, events_raw)
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "OpenCode nonzero exit",
                "description": "exit=%d" % exit_code,
                "metadata": {
                    "execution_id": execution_id,
                    "exit_code": exit_code,
                    "failure_classification": fail_class,
                    "stderr_summary": stderr_redacted[:512],
                    "role": role_context.role,
                },
            })
            changed_files = _collect_changed_files(worktree)
            return ExecutorResult(
                success=False,
                validation_exit_code=-1,
                validation_command_id="",
                validation_output_digest="",
                validation_output_summary=stderr_redacted[:1024],
                changed_files=changed_files,
                error="opencode_nonzero:exit=%d:%s" % (exit_code, fail_class),
                workspace=str(worktree),
                execution_id=execution_id,
                process_exit_code=exit_code,
                failure_classification=fail_class,
            )

        changed_files = _collect_changed_files(worktree)

        _emit(event_callback, task_id, {
            "type": "EXECUTOR_FINISHED",
            "title": "OpenCode CLI finished",
            "description": "exit=0 changed_files=%d" % len(changed_files),
            "metadata": {
                "execution_id": execution_id,
                "exit_code": exit_code,
                "changed_file_count": len(changed_files),
                "model": self._model_id,
                "role": role_context.role,
            },
        })

        val_argv = ["git", "diff", "--check"]
        val_proc = self._run_git(val_argv, cwd=worktree, timeout=30)
        val_exit = val_proc.returncode
        val_output = val_proc.stdout
        if val_proc.stderr:
            val_output = val_output + ("\n" + val_proc.stderr)
        val_digest = _digest(val_output)

        val_output_redacted = redact_secrets(_sanitize_output(val_output, 2048))

        _emit(event_callback, task_id, {
            "type": "LOCAL_VALIDATED",
            "title": "Local validation",
            "description": "git_diff_check exit=%d" % val_exit,
            "metadata": {
                "execution_id": execution_id,
                "validation_command_id": "git_diff_check",
                "validation_exit_code": val_exit,
                "role": role_context.role,
            },
        })

        if val_exit == 0:
            return ExecutorResult(
                success=True,
                validation_exit_code=val_exit,
                validation_command_id="git_diff_check",
                validation_output_digest=val_digest,
                validation_output_summary=val_output_redacted[:1024],
                changed_files=changed_files,
                workspace=str(worktree),
                execution_id=execution_id,
                process_exit_code=exit_code,
            )

        _emit(event_callback, task_id, {
            "type": "EXECUTOR_FINISHED",
            "title": "Validation failed",
            "description": "git_diff_check exit=%d" % val_exit,
            "metadata": {
                "execution_id": execution_id,
                "validation_exit_code": val_exit,
                "failure_classification": "deterministic_validation_failure",
                "role": role_context.role,
            },
        })
        return ExecutorResult(
            success=False,
            validation_exit_code=val_exit,
            validation_command_id="git_diff_check",
            validation_output_digest=val_digest,
            validation_output_summary=val_output_redacted[:1024],
            changed_files=changed_files,
            workspace=str(worktree),
            execution_id=execution_id,
            process_exit_code=exit_code,
            failure_classification="deterministic_validation_failure",
        )

    def prepare_worktree_once(
        self,
        task_id: str,
        root_path: Path,
        event_callback: ExecutorCallback | None,
    ) -> PreparedWorkspaceContext:
        """Prepare exactly one linked worktree for shared sequential use.

        Called ONCE by TaskExecutionService.execute_sequential_team() before
        any role executes. Returns a ``PreparedWorkspaceContext`` that is
        passed into ``execute_role_prepared`` for planner, coder, and
        reviewer so all three roles reuse the same CLI resolution and
        binding setup.
        """
        worktree, base_sha = self._prepare_linked_worktree(
            task_id, root_path, event_callback
        )
        execution_id = "exec-%s" % task_id
        cli_path, is_cmd = resolve_opencode_cli(self._opencode_exe)

        _emit(event_callback, task_id, {
            "type": "WORKSPACE_READY",
            "title": "Workspace ready",
            "description": "Linked worktree bound to %s" % base_sha,
            "metadata": {
                "workspace": str(worktree),
                "execution_id": execution_id,
                "executor_kind": "opencode",
                "model": self._model_id,
                "base_sha": base_sha,
                "repo_dir": str(self._repo_dir),
                **self._binding_event_metadata(),
            },
        })

        return PreparedWorkspaceContext(
            worktree=worktree,
            base_sha=base_sha,
            execution_id=execution_id,
            cli_path=cli_path,
            is_cmd=is_cmd,
            opencode_exe=self._opencode_exe,
        )

    def execute_role_prepared(
        self,
        prepared: PreparedWorkspaceContext,
        store: Any,
        *,
        role_context: RoleContext,
        event_callback: ExecutorCallback | None = None,
    ) -> ExecutorResult:
        """Run a single bounded role inside an already-prepared worktree.

        Reuses the same CLI resolution, binding configuration, prompt
        envelope, environment isolation, lease semantics, subprocess
        runner, secret redaction, event/evidence parsing, and
        ``git diff --check`` validation as ``execute()``. The caller
        (TaskExecutionService.execute_sequential_team) is responsible
        for preparing the worktree once and sequencing the roles.
        """
        return self._run_executor_core(
            task_id=role_context.task_id,
            store=store,
            worktree=prepared.worktree,
            base_sha=prepared.base_sha,
            execution_id=prepared.execution_id,
            cli_path=prepared.cli_path,
            is_cmd=prepared.is_cmd,
            event_callback=event_callback,
            role_context=role_context,
        )

    def _task_title(self, store: Any, task_id: str) -> str:
        try:
            task = store.get_task(task_id)
            return task.title if hasattr(task, "title") else task_id
        except Exception:
            return task_id

    def _binding_event_metadata(self) -> dict[str, str]:
        resolution = self._binding_resolution
        if resolution is None:
            return {}
        return {
            "binding_ref": resolution.binding_ref,
            "connection_id": resolution.connection_id,
            "executor_id": resolution.executor_id,
            "provider_id": resolution.provider_id,
            "model_id": resolution.model_id,
            "auth_method": resolution.auth_method,
        }

    def _run_git(self, argv: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                argv,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                args=argv,
                returncode=-1,
                stdout="",
                stderr="timeout",
            )

    def _prepare_linked_worktree(
        self,
        task_id: str,
        root_path: Path,
        event_callback: ExecutorCallback | None,
    ) -> tuple[Path, str]:
        if self._repo_dir_explicit:
            return self._prepare_real_linked_worktree(
                task_id, root_path, event_callback
            )
        return self._prepare_test_worktree(
            task_id, root_path, event_callback
        )

    def _prepare_real_linked_worktree(
        self,
        task_id: str,
        root_path: Path,
        event_callback: ExecutorCallback | None,
    ) -> tuple[Path, str]:
        """Create a real linked Git worktree from the configured source repo."""
        if not self._repo_dir:
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "repo_dir required",
                "description": "OpenCode executor requires a non-empty repo_dir",
                "metadata": {"failure_classification": "policy_worktree_violation"},
            })
            raise ExecutorRuntimeError("repo_dir_required")

        repo_dir = Path(self._repo_dir).resolve()
        if not repo_dir.exists() or not repo_dir.is_dir():
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "repo_dir not a directory",
                "description": "repo_dir does not exist or is not a directory",
                "metadata": {"failure_classification": "policy_worktree_violation"},
            })
            raise ExecutorRuntimeError(
                "repo_dir_invalid:%s" % self._repo_dir
            )

        is_inside = self._run_git(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_dir,
            timeout=10,
        )
        if is_inside.returncode != 0:
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "repo_dir not a git repository",
                "description": "repo_dir is not inside a git work tree",
                "metadata": {"failure_classification": "policy_worktree_violation"},
            })
            raise ExecutorRuntimeError("repo_dir_not_a_git_repository")

        base_ref = self._base_ref.strip()
        if base_ref:
            resolved = self._run_git(
                ["git", "rev-parse", "--verify", "%s^{commit}" % base_ref],
                cwd=repo_dir,
                timeout=10,
            )
            if resolved.returncode != 0:
                _emit(event_callback, task_id, {
                    "type": "EXECUTOR_FINISHED",
                    "title": "base_ref invalid",
                    "description": "Could not resolve base_ref %s" % base_ref,
                    "metadata": {"failure_classification": "policy_worktree_violation"},
                })
                raise ExecutorRuntimeError(
                    "base_ref_unresolved:%s" % base_ref
                )
            base_sha = resolved.stdout.strip()
        else:
            head = self._run_git(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                timeout=10,
            )
            if head.returncode != 0:
                raise ExecutorRuntimeError("repo_dir_has_no_HEAD")
            base_sha = head.stdout.strip()

        dest = (root_path / task_id).resolve()
        repo_dir_resolved = repo_dir.resolve()
        if dest == repo_dir_resolved:
            raise ExecutorRuntimeError("worktree_must_be_outside_repo_dir")
        if _is_path_contained(dest, repo_dir_resolved):
            raise ExecutorRuntimeError("worktree_must_be_outside_repo_dir")

        if dest.exists():
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "workspace destination exists",
                "description": "Destination path already exists; refusing to overwrite",
                "metadata": {"failure_classification": "policy_worktree_violation"},
            })
            raise ExecutorRuntimeError("workspace_destination_exists")

        parents = dest.parent
        parents.mkdir(parents=True, exist_ok=True)

        add_proc = self._run_git(
            ["git", "worktree", "add", "--detach", str(dest), base_sha],
            cwd=repo_dir,
            timeout=60,
        )
        if add_proc.returncode != 0:
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "worktree creation failed",
                "description": "git worktree add failed",
                "metadata": {
                    "failure_classification": "policy_worktree_violation",
                    "stderr_summary": redact_secrets(
                        _sanitize_output(add_proc.stderr, 512)
                    )[:512],
                },
            })
            raise ExecutorRuntimeError(
                "worktree_add_failed:%s" % add_proc.stderr[:200]
            )

        head_check = self._run_git(
            ["git", "rev-parse", "HEAD"],
            cwd=dest,
            timeout=10,
        )
        if head_check.returncode != 0 or head_check.stdout.strip() != base_sha:
            raise ExecutorRuntimeError("worktree_head_mismatch")

        list_proc = self._run_git(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo_dir,
            timeout=10,
        )
        if dest.as_posix() not in list_proc.stdout and str(dest) not in list_proc.stdout:
            raise ExecutorRuntimeError("worktree_not_registered")

        return dest, base_sha

    def _prepare_test_worktree(
        self,
        task_id: str,
        root_path: Path,
        event_callback: ExecutorCallback | None,
    ) -> tuple[Path, str]:
        """Create a disposable test worktree when repo_dir is not set (unit-test mode)."""
        worktree = (root_path / task_id).resolve()
        if worktree.exists():
            import shutil
            shutil.rmtree(worktree)
        worktree.mkdir(parents=True, exist_ok=True)

        init_proc = self._run_git(
            ["git", "init", "-q"],
            cwd=worktree,
            timeout=10,
        )
        if init_proc.returncode != 0:
            raise ExecutorRuntimeError("test_worktree_git_init_failed")

        self._run_git(
            ["git", "config", "user.email", "test@provider-free.local"],
            cwd=worktree,
            timeout=5,
        )
        self._run_git(
            ["git", "config", "user.name", "Test Fixture"],
            cwd=worktree,
            timeout=5,
        )

        fixture_file = worktree / "fixture.txt"
        fixture_file.write_text("test fixture\n", encoding="utf-8")

        self._run_git(
            ["git", "add", "fixture.txt"],
            cwd=worktree,
            timeout=5,
        )
        self._run_git(
            ["git", "commit", "-q", "-m", "init: test fixture"],
            cwd=worktree,
            timeout=10,
        )

        head_proc = self._run_git(
            ["git", "rev-parse", "HEAD"],
            cwd=worktree,
            timeout=5,
        )
        base_sha = head_proc.stdout.strip() if head_proc.returncode == 0 else ""

        return worktree, base_sha


def _is_path_contained(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _handoff_path(path: str) -> bool:
    try:
        Path(path).resolve().relative_to(Path(_HANDOFF_DIR).resolve())
        return True
    except (ValueError, OSError):
        return False


def _is_handoff_path(path: str) -> bool:
    return path.startswith(_HANDOFF_DIR + "/") or path == _HANDOFF_DIR


def _handoff_file_under_worktree(file_path: Path, worktree: Path) -> bool:
    """Return True iff file_path resolves to a real file strictly under worktree
    and under the executor-owned handoff directory, with no symlink traversal."""
    try:
        if file_path.is_symlink():
            return False
        real = file_path.resolve(strict=True)
        worktree_real = worktree.resolve()
        handoff_real = (worktree_real / _HANDOFF_DIR).resolve()
        try:
            real.relative_to(handoff_real)
        except ValueError:
            return False
        try:
            real.relative_to(worktree_real)
        except ValueError:
            return False
    except (OSError, RuntimeError):
        return False
    return True


def _handoff_file_size_ok(file_path: Path) -> tuple[bool, str]:
    if not file_path.exists():
        return False, "handoff_missing"
    if not file_path.is_file():
        return False, "handoff_not_regular_file"
    try:
        size = file_path.stat().st_size
    except OSError:
        return False, "handoff_stat_failed"
    if size == 0:
        return False, "handoff_empty"
    if size > _MAX_HANDOFF_BYTES:
        return False, f"handoff_oversized:{size}"
    return True, ""


def _validate_handoff_file(
    file_path: Path,
    worktree: Path,
    *,
    label: str,
) -> str:
    """Validate a bounded handoff file (plan.md or review.md).

    Checks (all must pass):
    - exists
    - not a symlink/junction
    - resolves under the executor-owned handoff directory
    - resolves under the shared worktree
    - regular file
    - non-empty
    - <= 128 KiB

    Returns '' on valid handoff, else a short failure reason prefixed with
    the ``label`` (e.g. ``plan_missing``, ``review_oversized``).
    """
    if not file_path.exists():
        return f"{label}_missing"
    if file_path.is_symlink():
        return f"{label}_symlink"
    if not _handoff_file_under_worktree(file_path, worktree):
        return f"{label}_workspace_escape"
    ok, reason = _handoff_file_size_ok(file_path)
    if not ok:
        safe = reason.replace("handoff_", f"{label}_")
        return safe
    return ""


def _validate_plan_handoff(plan_path: Path) -> str:
    """Return '' on valid plan handoff, else a short failure reason."""
    worktree = plan_path.parent.parent if plan_path.parent.name == _HANDOFF_DIR else plan_path.parent
    return _validate_handoff_file(plan_path, worktree, label="plan")


def _validate_review_handoff(review_path: Path) -> str:
    """Return '' on valid review handoff, else a short failure reason."""
    worktree = review_path.parent.parent if review_path.parent.name == _HANDOFF_DIR else review_path.parent
    return _validate_handoff_file(review_path, worktree, label="review")


def _handoff_digest(handoff_path: Path) -> str:
    if not handoff_path.is_file():
        return ""
    return hashlib.sha256(handoff_path.read_bytes()).hexdigest()


def _collect_product_diff(worktree: Path) -> tuple[dict[str, Any], ...]:
    """Collect tracked/untracked product changes inside ``worktree``,
    excluding the runtime handoff directory.

    Used by TaskExecutionService to snapshot the product diff before and
    after each role. A role that changes only ``.reverse-agent-handoff/**``
    will not affect the returned tuple; a role that changes any tracked or
    untracked non-handoff file will appear here.
    """
    return tuple(
        f
        for f in _collect_changed_files(worktree)
        if f.get("path") and not _is_handoff_path(f["path"])
    )


def _collect_final_product_files(worktree: Path) -> list[dict[str, Any]]:
    """Collect product changed files after handoff cleanup.

    The handoff directory has already been removed at this point, so this
    is a thin wrapper that preserves the API shape used by TaskExecutionService.
    """
    return [
        f
        for f in _collect_changed_files(worktree)
        if f.get("path") and not _is_handoff_path(f["path"])
    ]


# ---------------------------------------------------------------------------
# JSON-line parsing with recursive redaction
# ---------------------------------------------------------------------------

def redact_event(event: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact secret-like values from a parsed OpenCode JSON event."""
    return dict(_redact_recursively(event))


def _parse_json_lines(
    self: "OpenCodeExecutor", text: str
) -> tuple[list[dict[str, Any]], bool]:
    events: list[dict[str, Any]] = []
    malformed = False
    if not text:
        return events, False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except (json.JSONDecodeError, UnicodeDecodeError):
            malformed = True
            continue
        if isinstance(obj, dict):
            events.append(redact_event(obj))
    return events, malformed


def _build_executor_evidence(
    events: list[dict[str, Any]],
    *,
    exit_code: int,
    model_id: str,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    seen = 0
    for event in events[:MAX_EVIDENCE_ITEMS]:
        if seen >= MAX_EVIDENCE_ITEMS:
            break
        t = event.get("type") or event.get("event") or event.get("kind") or "event"
        action = event.get("action") or event.get("tool") or event.get("command") or t
        status = "pass" if exit_code == 0 else "info"
        label = str(action)[:MAX_EVIDENCE_STRING_LEN]
        value = _bounded_value(event, MAX_EVIDENCE_STRING_LEN)
        detail = _bounded_summary(event, MAX_EVIDENCE_STRING_LEN)
        evidence.append({
            "category": "ExecutorAction",
            "label": label,
            "value": value,
            "status": status,
            "detail": detail,
        })
        seen += 1
    return evidence


def _bounded_value(event: dict[str, Any], limit: int) -> str:
    for key in ("path", "file", "command", "result", "message"):
        v = event.get(key)
        if v is not None:
            s = str(v)[:limit]
            return redact_secrets(s)
    return ""


def _bounded_summary(event: dict[str, Any], limit: int) -> str:
    keys = ["type", "action", "tool", "status", "exit_code"]
    parts: list[str] = []
    for key in keys:
        v = event.get(key)
        if v is not None:
            parts.append("%s=%s" % (key, str(v)[:64]))
    return redact_secrets(" ".join(parts))[:limit]


# ---------------------------------------------------------------------------
# Emit executor evidence as events
# ---------------------------------------------------------------------------

def _emit_executor_evidence_events(
    callback: ExecutorCallback | None,
    task_id: str,
    execution_id: str,
    evidence: list[dict[str, Any]],
) -> None:
    """Emit executor action evidence items as bounded task events.

    Each evidence item becomes an EXECUTOR_FINISHED event with metadata
    carrying the redacted/bounded evidence fields. The task_service callback
    persists these as task events for readback.
    """
    for item in evidence[:MAX_EVIDENCE_ITEMS]:
        _emit(callback, task_id, {
            "type": "EXECUTOR_FINISHED",
            "title": "Executor action evidence",
            "description": str(item.get("label", ""))[:MAX_EVIDENCE_STRING_LEN],
            "metadata": {
                "execution_id": execution_id,
                "evidence_category": str(item.get("category", ""))[:64],
                "evidence_label": str(item.get("label", ""))[:MAX_EVIDENCE_STRING_LEN],
                "evidence_value": str(item.get("value", ""))[:MAX_EVIDENCE_STRING_LEN],
                "evidence_status": str(item.get("status", "info"))[:32],
            },
        })


def _persist_executor_evidence(
    store: Any,
    task_id: str,
    evidence: list[dict[str, Any]],
) -> None:
    """Persist executor action evidence directly to TaskStore.

    The executor has a store reference; use it to add bounded/redacted
    ExecutorAction evidence rows so the TaskStore readback contains
    tool/action proof even when task_service.py does not iterate over
    executor_evidence.
    """
    if store is None:
        return
    for item in evidence[:MAX_EVIDENCE_ITEMS]:
        try:
            store.add_evidence(
                task_id,
                category=str(item.get("category", "ExecutorAction")),
                label=str(item.get("label", ""))[:MAX_EVIDENCE_STRING_LEN],
                value=str(item.get("value", ""))[:MAX_EVIDENCE_STRING_LEN],
                status=str(item.get("status", "info"))[:32],
                detail=str(item.get("detail", ""))[:MAX_EVIDENCE_STRING_LEN],
                raw_json_digest="",
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Changed-file collection
# ---------------------------------------------------------------------------

def _collect_changed_files(worktree: Path) -> list[dict[str, Any]]:
    try:
        proc = subprocess.run(
            ["git", "diff", "--numstat", "HEAD"],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    files: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], parts[2]
        fpath = worktree / path
        content_digest = ""
        try:
            if fpath.exists() and fpath.is_file() and not fpath.is_symlink():
                content_digest = hashlib.sha256(
                    fpath.read_bytes()
                ).hexdigest()
        except (OSError, UnicodeDecodeError):
            content_digest = ""
        files.append({
            "path": path,
            "status": "added" if added != "-" and deleted == "0" else "modified",
            "additions": 0 if added == "-" else int(added),
            "deletions": 0 if deleted == "-" else int(deleted),
            "diff_digest": "",
            "content_digest": content_digest,
        })
        seen_paths.add(path)

    try:
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        for line in untracked.stdout.splitlines():
            path = line.strip()
            if not path or path in seen_paths:
                continue
            fpath = worktree / path
            adds, dels = _count_untracked_lines(fpath)
            content_digest = ""
            try:
                if fpath.exists() and fpath.is_file() and not fpath.is_symlink():
                    content_digest = hashlib.sha256(
                        fpath.read_bytes()
                    ).hexdigest()
            except (OSError, UnicodeDecodeError):
                content_digest = ""
            files.append({
                "path": path,
                "status": "added",
                "additions": adds,
                "deletions": dels,
                "diff_digest": "",
                "content_digest": content_digest,
            })
            seen_paths.add(path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return files


def _count_untracked_lines(fpath: Path) -> tuple[int, int]:
    try:
        if not fpath.exists():
            return 0, 0
        if _is_binary_file(fpath):
            return 1, 0
        text = fpath.read_text(encoding="utf-8", errors="replace")
        if not text:
            return 0, 0
        return len(text.splitlines()), 0
    except (OSError, UnicodeDecodeError):
        return 1, 0


def _is_binary_file(fpath: Path) -> bool:
    try:
        with fpath.open("rb") as fh:
            chunk = fh.read(8192)
        return b"\x00" in chunk
    except OSError:
        return True


# ---------------------------------------------------------------------------
# Exit classification
# ---------------------------------------------------------------------------

def _classify_exit(
    self: "OpenCodeExecutor",
    exit_code: int,
    events_raw: list[dict[str, Any]],
) -> str:
    if exit_code in (127, 126):
        return "cli_unavailable"
    if exit_code in (124, 137, 143):
        return "timeout"
    for ev in events_raw:
        msg = json.dumps(ev, ensure_ascii=False, sort_keys=True).lower()
        if "auth" in msg or "unauthorized" in msg or "forbidden" in msg:
            return "auth_provider_route_failure"
        if "network" in msg or "connection" in msg or "dns" in msg:
            return "network_provider_failure"
        if "model" in msg and ("not found" in msg or "unavailable" in msg):
            return "model_provider_unavailable"
    return "executor_nonzero"


# ---------------------------------------------------------------------------
# Emit helper
# ---------------------------------------------------------------------------

def _emit(
    callback: ExecutorCallback | None,
    task_id: str,
    event: dict[str, Any],
) -> None:
    if callback is None:
        return
    try:
        callback(task_id, event)
    except Exception:
        pass


# Bind the instance methods that use `self` for compatibility with existing
# test code that calls `executor._parse_json_lines(text)` and
# `executor._classify_exit(exit_code, events)`.
OpenCodeExecutor._parse_json_lines = _parse_json_lines
OpenCodeExecutor._classify_exit = _classify_exit
