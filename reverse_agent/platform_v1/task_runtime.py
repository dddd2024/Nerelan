"""Executor router, deterministic fixture executor, and local validation.

The ExecutorRouter dispatches by ``executor_kind``. This round only registers
``DeterministicFixtureExecutor``. The router interface allows future
executor kinds (e.g. a Codex executor) to be registered without changing the
Task API or frontend architecture.

The deterministic fixture executor:
- operates only inside an approved disposable workspace/worktree;
- runs exactly one deterministic mutation;
- validates with an approved command ID (structured argv, never shell=True);
- returns normalized changed-file and validation evidence.

It does NOT access model APIs, provider credentials, or the network.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

# ---------------------------------------------------------------------------
# Result contract
# ---------------------------------------------------------------------------

@dataclass
class FixtureExecutorResult:
    success: bool
    validation_exit_code: int
    validation_command_id: str
    validation_output_digest: str
    validation_output_summary: str
    changed_files: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    workspace: str = ""
    execution_id: str = ""


ExecutorCallback = Callable[[str, dict[str, Any]], None]


# ---------------------------------------------------------------------------
# Executor protocol
# ---------------------------------------------------------------------------

class Executor(Protocol):
    def execute(
        self,
        task_id: str,
        store: Any,
        *,
        workspace_root: str = "",
        event_callback: ExecutorCallback | None = None,
    ) -> FixtureExecutorResult: ...


# ---------------------------------------------------------------------------
# Approved validation commands
# ---------------------------------------------------------------------------

_APPROVED_VALIDATION_COMMANDS: dict[str, list[str]] = {
    "git_diff_check": ["git", "diff", "--check"],
    "git_status_porcelain": ["git", "status", "--porcelain=v1"],
}

_APPROVED_MUTATION_COMMANDS: dict[str, list[str]] = {
    "append_to_file": ["_mutate_append_to_file"],
    "write_file": ["_mutate_write_file"],
}


class ExecutorRuntimeError(Exception):
    """Raised when executor runtime fails (invalid command, workspace, etc.)."""


class ValidationCommandError(ExecutorRuntimeError):
    """Raised when a validation command fails its expected contract."""


def _approved_argv(command_id: str, registry: dict[str, list[str]]) -> list[str]:
    if command_id not in registry:
        raise ExecutorRuntimeError(f"unapproved_command:{command_id}")
    return list(registry[command_id])


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sanitize_output(text: str, max_bytes: int = 4096) -> str:
    truncated = text[:max_bytes]
    return truncated.replace("\x00", "")


# ---------------------------------------------------------------------------
# LocalValidationRunner
# ---------------------------------------------------------------------------

class LocalValidationRunner:
    """Run a bounded validation command by approved command ID.

    Only command IDs registered in ``_APPROVED_VALIDATION_COMMANDS`` may be
    executed. argv is structured; ``shell=True`` is never used.
    """

    def run(
        self,
        *,
        task_id: str,
        command_id: str,
        cwd: str,
    ) -> tuple[int, str, str]:
        argv = _approved_argv(command_id, _APPROVED_VALIDATION_COMMANDS)
        if not cwd:
            raise ExecutorRuntimeError("validation_requires_cwd")
        if not os.path.isdir(cwd):
            raise ExecutorRuntimeError(f"workspace_not_found:{cwd}")
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired) as exc:
            raise ValidationCommandError(
                f"validation_command_failed:{command_id}:{exc.__class__.__name__}"
            ) from exc
        output = _sanitize_output(proc.stdout + ("\n" + proc.stderr if proc.stderr else ""))
        return proc.returncode, output, _digest(output)


# ---------------------------------------------------------------------------
# DeterministicFixtureExecutor
# ---------------------------------------------------------------------------

class DeterministicFixtureExecutor:
    """A non-model executor that exercises the full task plane deterministically.

    It creates a fresh disposable git worktree, applies one deterministic
    mutation to a fixture file, validates the result, and returns normalized
    changed-file and validation evidence.
    """

    def __init__(
        self,
        *,
        mutation_command_id: str = "append_to_file",
        validation_command_id: str = "git_diff_check",
        fixture_path: str = "fixture.txt",
    ) -> None:
        if mutation_command_id not in _APPROVED_MUTATION_COMMANDS:
            raise ExecutorRuntimeError(
                f"unapproved_mutation_command:{mutation_command_id}"
            )
        _approved_argv(validation_command_id, _APPROVED_VALIDATION_COMMANDS)
        self._mutation_command_id = mutation_command_id
        self._validation_command_id = validation_command_id
        self._fixture_path = fixture_path

    def execute(
        self,
        task_id: str,
        store: Any,
        *,
        workspace_root: str = "",
        event_callback: ExecutorCallback | None = None,
    ) -> FixtureExecutorResult:
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

        execution_id = f"exec-{task_id}"
        _emit(event_callback, task_id, {
            "type": "WORKSPACE_READY",
            "title": "Workspace ready",
            "description": f"Disposable worktree created at {worktree}",
            "metadata": {"workspace": str(worktree), "execution_id": execution_id},
        })

        try:
            _git_init(worktree)
            initial_content = "provider-free task plane fixture\n"
            fixture_file = worktree / self._fixture_path
            fixture_file.write_text(initial_content, encoding="utf-8")
            _git_add_and_commit(worktree, "init: fixture")

            _apply_mutation(self._mutation_command_id, fixture_file)

            _emit(event_callback, task_id, {
                "type": "EXECUTOR_FINISHED",
                "title": "Fixture mutation applied",
                "description": f"Mutation {self._mutation_command_id} applied",
                "metadata": {
                    "execution_id": execution_id,
                    "mutation_command_id": self._mutation_command_id,
                    "fixture_path": self._fixture_path,
                },
            })

            runner = LocalValidationRunner()
            exit_code, output, output_digest = runner.run(
                task_id=task_id,
                command_id=self._validation_command_id,
                cwd=str(worktree),
            )

            _emit(event_callback, task_id, {
                "type": "LOCAL_VALIDATED",
                "title": "Local validation",
                "description": f"{self._validation_command_id} exit={exit_code}",
                "metadata": {
                    "execution_id": execution_id,
                    "validation_command_id": self._validation_command_id,
                    "validation_exit_code": exit_code,
                },
                "raw_log": _sanitize_output(output, 2048),
            })

            changed_files = _collect_changed_files(worktree, task_id)
            success = exit_code == 0
            if success:
                _emit(event_callback, task_id, {
                    "type": "VALIDATED",
                    "title": "Task validated",
                    "description": "Deterministic fixture validation passed",
                    "metadata": {
                        "execution_id": execution_id,
                        "validation_passed": True,
                    },
                })
            return FixtureExecutorResult(
                success=success,
                validation_exit_code=exit_code,
                validation_command_id=self._validation_command_id,
                validation_output_digest=output_digest,
                validation_output_summary=_sanitize_output(output, 1024),
                changed_files=changed_files,
                workspace=str(worktree),
                execution_id=execution_id,
            )
        except ExecutorRuntimeError:
            raise
        except Exception as exc:
            return FixtureExecutorResult(
                success=False,
                validation_exit_code=-1,
                validation_command_id=self._validation_command_id,
                validation_output_digest="",
                validation_output_summary="",
                changed_files=[],
                error=f"executor_error:{exc.__class__.__name__}",
                workspace=str(worktree),
                execution_id=execution_id,
            )


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


def _apply_mutation(command_id: str, fixture_file: Path) -> None:
    if command_id == "append_to_file":
        with fixture_file.open("a", encoding="utf-8") as fh:
            fh.write("deterministic mutation applied\n")
        return
    if command_id == "write_file":
        fixture_file.write_text("provider-free task plane fixture\nrewritten content\n", encoding="utf-8")
        return
    raise ExecutorRuntimeError(f"unknown_mutation_command:{command_id}")


# ---------------------------------------------------------------------------
# Git helpers (structured argv, never shell=True)
# ---------------------------------------------------------------------------

def _git_init(worktree: Path) -> None:
    _run(["git", "init", "-q"], cwd=worktree)
    _run(["git", "config", "user.email", "fixture@provider-free.local"], cwd=worktree)
    _run(["git", "config", "user.name", "ProviderFree Fixture"], cwd=worktree)


def _git_add_and_commit(worktree: Path, message: str) -> None:
    _run(["git", "add", "."], cwd=worktree)
    _run(["git", "commit", "-q", "-m", message], cwd=worktree)


def _run(argv: list[str], cwd: Path) -> None:
    subprocess.run(
        argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )


def _collect_changed_files(worktree: Path, task_id: str) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["git", "diff", "--numstat", "HEAD"],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    files: list[dict[str, Any]] = []
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
    return files


# ---------------------------------------------------------------------------
# ExecutorRouter
# ---------------------------------------------------------------------------

class ExecutorRouter:
    """Dispatch to the registered executor for a given executor_kind.

    Future executor kinds (e.g. ``codex``) register here without changing the
    Task API or the frontend task hooks.
    """

    def __init__(self) -> None:
        self._registry: dict[str, Callable[[], Executor]] = {
            "deterministic_fixture": lambda: DeterministicFixtureExecutor(),
        }

    def register(self, kind: str, factory: Callable[[], Executor]) -> None:
        if not isinstance(kind, str) or not kind.strip():
            raise ExecutorRuntimeError("executor_kind_must_be_non_empty")
        self._registry[kind] = factory

    def dispatch_execute(
        self,
        *,
        task_id: str,
        store: Any,
        executor_kind: str,
        workspace_root: str = "",
        event_callback: ExecutorCallback | None = None,
    ) -> FixtureExecutorResult:
        factory = self._registry.get(executor_kind)
        if factory is None:
            raise ExecutorRuntimeError(f"unknown_executor_kind:{executor_kind}")
        return factory().execute(
            task_id,
            store,
            workspace_root=workspace_root,
            event_callback=event_callback,
        )
