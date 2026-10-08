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
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

HOST_VALIDATION_CONTRACT = "HostValidationContract"


def load_host_validation_contract(task: Any) -> dict[str, Any] | None:
    """Load the immutable host-check intent frozen when a Goal is materialized."""
    rows = [row for row in task.evidence_refs if row.get("category") == HOST_VALIDATION_CONTRACT]
    if not rows:
        return None
    if len(rows) != 1:
        raise ExecutorRuntimeError("host_validation_contract_ambiguous")
    row = rows[0]
    try:
        value = json.loads(row["detail"])
        identity = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                             separators=(",", ":")).encode("utf-8")).hexdigest()
        fields = {"version", "task_id", "repository", "goal_id", "goal_revision",
                  "goal_artifact_digest", "plan_task_id", "capability", "validation_command_id",
                  "window_id", "policy_digest", "workspace_path", "base_sha", "allowed_paths",
                  "goal_idempotency_key"}
        if (not isinstance(value, dict) or set(value) != fields or type(value["version"]) is not int or value["version"] != 1
                or row["status"] != "APPROVED" or row["value"] != identity
                or row["raw_json_digest"] != identity or value["task_id"] != task.id
                or value["repository"] != task.repository or value["capability"] != "validate_task"
                or value["validation_command_id"] != "git_diff_check"
                or type(value["goal_revision"]) is not int or value["goal_revision"] < 1
                or not re.fullmatch(r"[0-9a-f]{40}", value["base_sha"])
                or not re.fullmatch(r"[0-9a-f]{64}", value["goal_artifact_digest"])
                or not re.fullmatch(r"[0-9a-f]{64}", value["policy_digest"])
                or not isinstance(value["allowed_paths"], list) or not value["allowed_paths"]
                or any(not isinstance(value[key], str) or not value[key]
                       for key in ("workspace_path", "window_id", "goal_id", "plan_task_id", "goal_idempotency_key"))):
            raise ValueError
        return value
    except (ValueError, TypeError, KeyError) as exc:
        raise ExecutorRuntimeError("host_validation_contract_invalid") from exc


def task_operation(task: Any) -> str:
    return "validate_task" if load_host_validation_contract(task) is not None else "execute_task"

# ---------------------------------------------------------------------------
# Result contract
# ---------------------------------------------------------------------------

@dataclass
class ExecutorResult:
    """Neutral executor result returned by any registered executor."""
    success: bool
    validation_exit_code: int
    validation_command_id: str
    validation_output_digest: str
    validation_output_summary: str
    changed_files: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    workspace: str = ""
    execution_id: str = ""
    process_exit_code: int | None = None
    failure_classification: str = ""


FixtureExecutorResult = ExecutorResult


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

VALIDATION_SURFACE_PATCH_HYGIENE = "PATCH_HYGIENE"
VALIDATION_SURFACE_FUNCTIONAL = "FUNCTIONAL"
VALIDATION_SURFACE_UNKNOWN = "UNKNOWN"

_VALIDATION_COMMAND_SURFACES: dict[str, str] = {
    "git_diff_check": VALIDATION_SURFACE_PATCH_HYGIENE,
    "git_status_porcelain": VALIDATION_SURFACE_PATCH_HYGIENE,
    "approved_functional_checks": VALIDATION_SURFACE_FUNCTIONAL,
}

_APPROVED_MUTATION_COMMANDS: dict[str, list[str]] = {
    "append_to_file": ["_mutate_append_to_file"],
    "write_file": ["_mutate_write_file"],
}


class ExecutorRuntimeError(Exception):
    """Raised when executor runtime fails (invalid command, workspace, etc.)."""


class ValidationCommandError(ExecutorRuntimeError):
    """Raised when a validation command fails its expected contract."""


def validation_command_surface(command_id: str) -> str:
    """Return what an exact approved validation command is allowed to prove.

    Unknown/unregistered identities fail closed to ``UNKNOWN``.  A zero exit
    code is not enough to promote patch-hygiene evidence to functional proof.
    """
    if not isinstance(command_id, str):
        return VALIDATION_SURFACE_UNKNOWN
    return _VALIDATION_COMMAND_SURFACES.get(
        command_id,
        VALIDATION_SURFACE_UNKNOWN,
    )


def _approved_argv(command_id: str, registry: dict[str, list[str]]) -> list[str]:
    if command_id not in registry:
        raise ExecutorRuntimeError(f"unapproved_command:{command_id}")
    return list(registry[command_id])


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sanitize_output(text: str, max_bytes: int = 4096) -> str:
    cleaned = text.replace("\x00", "")
    encoded = cleaned.encode("utf-8")
    if len(encoded) <= max_bytes:
        return cleaned
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


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
        allowed_paths: list[str] | None = None,
        expected_head: str = "",
    ) -> tuple[int, str, str]:
        argv = _approved_argv(command_id, _APPROVED_VALIDATION_COMMANDS)
        if not cwd:
            raise ExecutorRuntimeError("validation_requires_cwd")
        if not os.path.isdir(cwd):
            raise ExecutorRuntimeError(f"workspace_not_found:{cwd}")
        environment = None
        if allowed_paths is not None:
            if command_id != "git_diff_check":
                raise ExecutorRuntimeError("host_validation_command_unapproved")
            root = Path(cwd)
            if root.is_symlink() or str(root.resolve(strict=True)) != str(root.absolute()):
                raise ExecutorRuntimeError("host_validation_workspace_indirect")
            metadata = root / ".git"
            if metadata.is_symlink() or (hasattr(metadata, "is_junction") and metadata.is_junction()):
                raise ExecutorRuntimeError("host_validation_metadata_indirect")
            if not allowed_paths or len(allowed_paths) > 128:
                raise ExecutorRuntimeError("host_validation_paths_required")
            for relative in allowed_paths:
                if (not isinstance(relative, str) or not relative or "\\" in relative
                        or ":" in relative or "\x00" in relative or relative.startswith("/")
                        or any(part in {"", ".", "..", ".git"} for part in relative.split("/"))):
                    raise ExecutorRuntimeError("host_validation_path_invalid")
                candidate = root
                for part in relative.split("/"):
                    candidate = candidate / part
                    if candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction()):
                        raise ExecutorRuntimeError("host_validation_path_indirect")
                if not candidate.resolve().is_relative_to(root):
                    raise ExecutorRuntimeError("host_validation_path_outside_workspace")
            environment = {key: os.environ[key] for key in
                           ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "PATHEXT") if key in os.environ}
            environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                               GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0",
                               GIT_OPTIONAL_LOCKS="0", GIT_LITERAL_PATHSPECS="1")
            prefix = ["git", "--no-pager", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
                      "-c", "core.pager=cat", "-c", "diff.external=", "-c", "core.attributesFile=" + os.devnull]
            if expected_head:
                observed = subprocess.run([*prefix, "rev-parse", "--verify", "HEAD"], cwd=cwd,
                                          env=environment, stdin=subprocess.DEVNULL, capture_output=True,
                                          text=True, timeout=10, check=False)
                if observed.returncode or observed.stdout.strip() != expected_head:
                    raise ExecutorRuntimeError("host_validation_base_drift")
            # diff HEAD cannot inspect new files: observe selected literal
            # paths separately, including ignored files, before claiming PASS.
            try:
                untracked = subprocess.run(
                    [*prefix, "ls-files", "--others", "-z", "--", *allowed_paths],
                    cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                    capture_output=True, timeout=10, check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ValidationCommandError("host_validation_git_observation_failed") from exc
            if untracked.returncode or (untracked.stdout and not untracked.stdout.endswith(b"\x00")):
                raise ValidationCommandError("host_validation_git_observation_failed")
            if untracked.stdout:
                raise ValidationCommandError("host_validation_untracked_paths")
            argv = [*prefix, "diff", "--check", "--no-ext-diff", "--no-textconv", "HEAD", "--", *allowed_paths]
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                env=environment,
                stdin=subprocess.DEVNULL,
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
            fixture_file.write_text(initial_content, encoding="utf-8", newline="\n")
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
        with fixture_file.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write("deterministic mutation applied\n")
        return
    if command_id == "write_file":
        fixture_file.write_text("provider-free task plane fixture\nrewritten content\n", encoding="utf-8", newline="\n")
        return
    raise ExecutorRuntimeError(f"unknown_mutation_command:{command_id}")


# ---------------------------------------------------------------------------
# Git helpers (structured argv, never shell=True)
# ---------------------------------------------------------------------------

def _git_init(worktree: Path) -> None:
    _run(["git", "-c", "core.longpaths=true", "init", "-q"], cwd=worktree)
    # Only this disposable fixture repository is configured. Windows object
    # paths exceed the worktree path by .git/objects/<2>/<38>; user-global
    # defaults must not make a bounded provider-free fixture fail or run hooks.
    for name, value in (("core.longpaths", "true"), ("core.autocrlf", "false"),
                        ("core.hooksPath", os.devnull), ("commit.gpgsign", "false")):
        _run(["git", "config", "--local", name, value], cwd=worktree)
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

def _normalize_executor_kind(kind: str) -> str:
    if not isinstance(kind, str) or not kind.strip():
        raise ExecutorRuntimeError("executor_kind_must_be_non_empty")
    return kind.strip().casefold()


class ExecutorRouter:
    """Dispatch to the registered executor for a given executor_kind."""

    def __init__(self) -> None:
        from .opencode_executor import OpenCodeExecutor

        self._registry: dict[str, Callable[..., Executor]] = {
            "deterministic_fixture": lambda **_: DeterministicFixtureExecutor(),
            "opencode": lambda **kwargs: OpenCodeExecutor(**kwargs),
        }

    def register(self, kind: str, factory: Callable[..., Executor]) -> None:
        normalized_kind = _normalize_executor_kind(kind)
        if normalized_kind in self._registry:
            raise ExecutorRuntimeError(f"duplicate_executor_kind:{normalized_kind}")
        self._registry[normalized_kind] = factory

    def replace(self, kind: str, factory: Callable[..., Executor]) -> None:
        normalized_kind = _normalize_executor_kind(kind)
        if normalized_kind not in self._registry:
            raise ExecutorRuntimeError(f"unknown_executor_kind:{normalized_kind}")
        self._registry[normalized_kind] = factory

    def dispatch_execute(
        self,
        *,
        task_id: str,
        store: Any,
        executor_kind: str,
        workspace_root: str = "",
        event_callback: ExecutorCallback | None = None,
        **executor_kwargs: Any,
    ) -> FixtureExecutorResult:
        normalized_kind = _normalize_executor_kind(executor_kind)
        factory = self._registry.get(normalized_kind)
        if factory is None:
            raise ExecutorRuntimeError(f"unknown_executor_kind:{normalized_kind}")
        return factory(**executor_kwargs).execute(
            task_id,
            store,
            workspace_root=workspace_root,
            event_callback=event_callback,
        )

    def create_executor(
        self,
        *,
        executor_kind: str,
        **executor_kwargs: Any,
    ) -> Executor:
        """Instantiate the registered executor without dispatching execute().

        Used by TaskExecutionService to obtain the configured OpenCode
        executor and call its bounded prepare/execute-role methods for the
        shared-workspace sequential planner->coder->reviewer flow.
        """
        normalized_kind = _normalize_executor_kind(executor_kind)
        factory = self._registry.get(normalized_kind)
        if factory is None:
            raise ExecutorRuntimeError(f"unknown_executor_kind:{normalized_kind}")
        return factory(**executor_kwargs)
