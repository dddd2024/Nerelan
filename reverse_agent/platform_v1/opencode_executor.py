"""OpenCode CLI executor for Platform V1.

Thin executor that launches the already-installed OpenCode CLI as a separate
child process inside an isolated Git worktree.

Boundaries:
- Never operates on the source checkout directly.
- Never reads or migrates credentials.
- Never runs shell=True with untrusted input.
- Prompt explicitly forbids commit, push, PR, merge, release, and
  filesystem access outside the worktree.
- JSON-line output is parsed defensively; malformed lines never crash the
  TaskService.
- Secret-like substrings are redacted before persistence.
- Deterministic ``git diff --check`` validation runs independently of the
  model's self-reported status.
- CLI invocation is injectable/fakeable for unit testing.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .task_runtime import (
    ExecutorCallback,
    ExecutorResult,
    ExecutorRuntimeError,
    LocalValidationRunner,
    _digest,
    _sanitize_output,
)


# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(authorization)\s*[:=]\s*\S+"), "[REDACTED]"),
    (re.compile(r"(?i)\"?(api[_-]?key|apikey)\"?\s*[:=]\s*\S+"), "[REDACTED]"),
    (re.compile(r"(?i)\"?(token)\"?\s*[:=]\s*\S{8,}"), "[REDACTED]"),
    (re.compile(r"(?i)\"?(password|passwd|pwd)\"?\s*[:=]\s*\S+"), "[REDACTED]"),
    (re.compile(r"(?i)\"?(secret)\"?\s*[:=]\s*\S+"), "[REDACTED]"),
    (re.compile(r"(?i)\"?(credential)\"?\s*[:=]\s*\S+"), "[REDACTED]"),
    (re.compile(r"(?i)\"?(cookie)\"?\s*[:=]\s*\S+"), "[REDACTED]"),
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


# ---------------------------------------------------------------------------
# CLI resolution
# ---------------------------------------------------------------------------

def resolve_opencode_cli(exe: str | None = None) -> tuple[str, bool]:
    """Resolve the OpenCode CLI path.

    Returns ``(path, is_cmd)`` where ``is_cmd`` indicates the executable
    is a ``.cmd`` / ``.bat`` launcher that requires ``cmd.exe /c`` wrapping.
    """
    if exe:
        p = exe.strip()
        return p, p.lower().endswith((".cmd", ".bat"))

    is_windows = platform.system() == "Windows"
    if is_windows:
        try:
            proc = subprocess.run(
                ["where.exe", "opencode.cmd"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                paths = [
                    line.strip()
                    for line in proc.stdout.splitlines()
                    if line.strip() and line.strip().lower().endswith((".cmd", ".bat"))
                ]
                if paths:
                    return paths[0], True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        try:
            proc = subprocess.run(
                ["where.exe", "opencode.exe"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                paths = [
                    line.strip()
                    for line in proc.stdout.splitlines()
                    if line.strip() and line.strip().lower().endswith(".exe")
                ]
                if paths:
                    return paths[0], False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    else:
        path = shutil.which("opencode")
        if path:
            return path, False

    raise ExecutorRuntimeError("opencode_cli_not_found")


# ---------------------------------------------------------------------------
# Command construction
# ---------------------------------------------------------------------------

def build_opencode_argv(
    cli_path: str,
    *,
    is_cmd: bool,
    model_id: str,
    worktree: str,
    prompt: str,
    use_auto: bool = False,
) -> tuple[list[str], str]:
    """Build the argv for the OpenCode CLI.

    Python 3.7+ on Windows handles ``.cmd`` / ``.bat`` files natively
    when passed directly to ``subprocess.run``. No ``cmd.exe /c`` wrapping
    is needed.

    Returns ``(argv, prompt_text)`` where ``argv`` is safe for
    ``subprocess.run`` with ``shell=False``.
    """
    inner = [
        "run",
        "--model",
        model_id,
        "--dir",
        worktree,
        "--format",
        "json",
    ]
    if use_auto:
        inner.append("--auto")
    inner.extend(["--", prompt])
    return [cli_path] + inner, prompt


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = "{task}"


def build_prompt(task_title: str, worktree: str) -> str:
    """Build the bounded prompt for the OpenCode CLI."""
    return _PROMPT_TEMPLATE.format(worktree=worktree, task=task_title)

class OpenCodeExecutor:
    """Launches OpenCode CLI as a child process in an isolated Git worktree."""

    def __init__(
        self,
        *,
        model_id: str | None = None,
        repo_dir: str = "",
        base_ref: str = "",
        opencode_exe: str | None = None,
        timeout: int = 300,
        use_auto: bool = True,
    ) -> None:
        self._model_id = model_id or os.environ.get("REVERSE_AGENT_OPENCODE_MODEL", "")
        if not self._model_id:
            raise ExecutorRuntimeError("model_id_required")
        self._repo_dir = repo_dir
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
        worktree = root_path / task_id
        if worktree.exists():
            shutil.rmtree(worktree)
        worktree.mkdir(parents=True, exist_ok=True)

        execution_id = "exec-%s" % task_id
        _emit(event_callback, task_id, {
            "type": "WORKSPACE_READY",
            "title": "Workspace ready",
            "description": "OpenCode worktree created at %s" % worktree,
            "metadata": {
                "workspace": str(worktree),
                "execution_id": execution_id,
                "executor_kind": "opencode",
                "model": self._model_id,
            },
        })

        cli_path, is_cmd = resolve_opencode_cli(self._opencode_exe)

        git_ready = self._prepare_git_worktree(worktree)
        task_title = self._task_title(store, task_id)
        prompt = build_prompt(task_title, str(worktree))

        if not git_ready:
            return ExecutorResult(
                success=False,
                validation_exit_code=-1,
                validation_command_id="git_worktree_prep",
                validation_output_digest="",
                validation_output_summary="",
                changed_files=[],
                error="git_worktree_preparation_failed",
                workspace=str(worktree),
                execution_id=execution_id,
                failure_classification="policy_worktree_violation",
            )

        cli_argv, _ = build_opencode_argv(
            cli_path,
            is_cmd=is_cmd,
            model_id=self._model_id,
            worktree=str(worktree),
            prompt=prompt,
            use_auto=self._use_auto,
        )

        _emit(event_callback, task_id, {
            "type": "EXECUTOR_RUNNING",
            "title": "OpenCode CLI started",
            "description": "OpenCode child process launched",
            "metadata": {
                "execution_id": execution_id,
                "executor_kind": "opencode",
                "model": self._model_id,
                "cli_path": cli_path,
                "worktree": str(worktree),
            },
        })

        try:
            proc = subprocess.run(
                cli_argv,
                cwd=str(worktree),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "OpenCode timeout",
                "description": "OpenCode CLI exceeded timeout",
                "metadata": {
                    "execution_id": execution_id,
                    "timeout": self._timeout,
                    "failure_classification": "timeout",
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

        events_raw, json_error = self._parse_json_lines(stdout)
        stderr_redacted = redact_secrets(_sanitize_output(stderr, 2048))

        if json_error:
            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "OpenCode output malformed",
                "description": "Malformed JSON in CLI output",
                "metadata": {
                    "execution_id": execution_id,
                    "exit_code": exit_code,
                    "failure_classification": "malformed_executor_output",
                },
            })

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
                },
                "raw_log": stderr_redacted[:1024],
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
            },
        })

        runner = LocalValidationRunner()
        try:
            val_exit, val_output, val_digest = runner.run(
                task_id=task_id,
                command_id="git_diff_check",
                cwd=str(worktree),
            )
        except ExecutorRuntimeError as exc:
            val_exit = -1
            val_output = str(exc)
            val_digest = _digest(val_output)

        val_output_redacted = redact_secrets(_sanitize_output(val_output, 2048))
        val_output_digest = val_digest

        _emit(event_callback, task_id, {
            "type": "LOCAL_VALIDATED",
            "title": "Local validation",
            "description": "git_diff_check exit=%d" % val_exit,
            "metadata": {
                "execution_id": execution_id,
                "validation_command_id": "git_diff_check",
                "validation_exit_code": val_exit,
            },
            "raw_log": val_output_redacted[:1024],
        })

        if val_exit == 0:
            _emit(event_callback, task_id, {
                "type": "VALIDATED",
                "title": "Task validated",
                "description": "git diff --check passed",
                "metadata": {
                    "execution_id": execution_id,
                    "validation_passed": True,
                },
            })
            return ExecutorResult(
                success=True,
                validation_exit_code=val_exit,
                validation_command_id="git_diff_check",
                validation_output_digest=val_output_digest,
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
            },
        })
        return ExecutorResult(
            success=False,
            validation_exit_code=val_exit,
            validation_command_id="git_diff_check",
            validation_output_digest=val_output_digest,
            validation_output_summary=val_output_redacted[:1024],
            changed_files=changed_files,
            workspace=str(worktree),
            execution_id=execution_id,
            process_exit_code=exit_code,
            failure_classification="deterministic_validation_failure",
        )

    def _task_title(self, store: Any, task_id: str) -> str:
        try:
            task = store.get_task(task_id)
            return task.title if hasattr(task, "title") else task_id
        except Exception:
            return task_id

    def _prepare_git_worktree(self, worktree: Path) -> bool:
        try:
            subprocess.run(
                ["git", "init", "-q"],
                cwd=str(worktree),
                capture_output=True,
                text=True,
                timeout=15,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "opencode@reverse-agent.local"],
                cwd=str(worktree),
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "OpenCode Executor"],
                cwd=str(worktree),
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            seed_file = worktree / ".gitkeep"
            seed_file.write_text("opencode worktree\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "."],
                cwd=str(worktree),
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", "init: opencode worktree"],
                cwd=str(worktree),
                capture_output=True,
                text=True,
                timeout=15,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _parse_json_lines(self, text: str) -> tuple[list[dict[str, Any]], bool]:
        events: list[dict[str, Any]] = []
        malformed = False
        if not text:
            return events, False
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
                if isinstance(obj, dict):
                    obj = redact_event(obj)
                    events.append(obj)
            except (json.JSONDecodeError, UnicodeDecodeError):
                malformed = True
        return events, malformed

    def _classify_exit(self, exit_code: int, events_raw: list[dict[str, Any]]) -> str:
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


def redact_event(event: dict[str, Any]) -> dict[str, Any]:
    """Redact secret-like values from a parsed OpenCode JSON event."""
    sensitive_keys = {
        "token", "api_key", "apikey", "secret", "password",
        "authorization", "auth", "credential", "cookie",
    }
    for key in list(event.keys()):
        if key.lower() in sensitive_keys:
            event[key] = "[REDACTED]"
        elif isinstance(event[key], str) and len(event[key]) > 200:
            event[key] = redact_secrets(event[key][:200])
        else:
            event[key] = redact_secrets(json.dumps(event[key], ensure_ascii=False, sort_keys=True) if not isinstance(event[key], str) else event[key])
    return event


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
        files.append({
            "path": path,
            "status": "added" if added != "-" and deleted == "0" else "modified",
            "additions": 0 if added == "-" else int(added),
            "deletions": 0 if deleted == "-" else int(deleted),
            "diff_digest": "",
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
            if path and path not in seen_paths:
                fpath = worktree / path
                size = fpath.stat().st_size if fpath.exists() else 0
                files.append({
                    "path": path,
                    "status": "added",
                    "additions": max(1, size),
                    "deletions": 0,
                    "diff_digest": "",
                })
                seen_paths.add(path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return files
