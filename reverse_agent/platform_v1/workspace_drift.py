"""Read-only local workspace-generation drift classification.

DRIFT-1 binds an explicitly Agent-confirmed workspace generation to Git's
content tree plus index/worktree status. Later comparison never guesses which
human or process changed the workspace: any mutation outside the captured
generation is classified as external local mutation; unprovable identity is
UNKNOWN_DIRTY_STATE.

The implementation deliberately reuses the executor-neutral Git snapshot
primitive. It owns no watcher, workspace database, merge engine, or mutation
command.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
from typing import Any

from reverse_agent.executor_neutral.core import _git, _snapshot_workspace, sha256_digest


_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SCHEMA_VERSION = "1"
_MAX_GENERATION_ID_LENGTH = 128
_MAX_PATH_BYTES = 4096
_MAX_STATUS_RECORDS = 10_000
_MAX_CHANGED_PATHS = 10_000

NO_DRIFT = "NO_DRIFT"
AGENT_EXPECTED_MUTATION = "AGENT_EXPECTED_MUTATION"
EXTERNAL_LOCAL_MUTATION = "EXTERNAL_LOCAL_MUTATION"
UNKNOWN_DIRTY_STATE = "UNKNOWN_DIRTY_STATE"

_VALID_STATES = frozenset(
    {
        NO_DRIFT,
        AGENT_EXPECTED_MUTATION,
        EXTERNAL_LOCAL_MUTATION,
        UNKNOWN_DIRTY_STATE,
    }
)


class WorkspaceObservationError(ValueError):
    """Stable, sanitized error raised while taking one workspace observation."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class WorkspaceStatusRecord:
    index_status: str
    worktree_status: str
    path: str

    def __post_init__(self) -> None:
        if len(self.index_status) != 1 or len(self.worktree_status) != 1:
            raise ValueError("workspace_status_code_invalid")
        if not _valid_path(self.path):
            raise ValueError("workspace_status_path_invalid")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class WorkspaceGeneration:
    schema_version: str
    generation_id: str
    repository_root_identity: str
    base_commit: str
    head_commit: str
    base_tree: str
    observed_tree: str
    changed_paths: tuple[str, ...]
    status_records: tuple[WorkspaceStatusRecord, ...]
    dirty: bool

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("workspace_generation_schema_invalid")
        if (
            not isinstance(self.generation_id, str)
            or not self.generation_id
            or self.generation_id != self.generation_id.strip()
            or len(self.generation_id) > _MAX_GENERATION_ID_LENGTH
        ):
            raise ValueError("workspace_generation_id_invalid")
        for name in ("base_commit", "head_commit", "base_tree", "observed_tree"):
            if not _SHA40.fullmatch(str(getattr(self, name))):
                raise ValueError(f"workspace_generation_{name}_invalid")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.repository_root_identity):
            raise ValueError("workspace_generation_repository_identity_invalid")
        if (
            len(self.changed_paths) > _MAX_CHANGED_PATHS
            or tuple(sorted(set(self.changed_paths))) != self.changed_paths
            or any(not _valid_path(path) for path in self.changed_paths)
        ):
            raise ValueError("workspace_generation_changed_paths_invalid")
        status_key = lambda item: (item.path, item.index_status, item.worktree_status)
        if (
            len(self.status_records) > _MAX_STATUS_RECORDS
            or tuple(sorted(set(self.status_records), key=status_key)) != self.status_records
            or len({item.path for item in self.status_records}) != len(self.status_records)
        ):
            raise ValueError("workspace_generation_status_records_invalid")
        if self.dirty is not bool(self.status_records):
            raise ValueError("workspace_generation_dirty_invalid")

    @property
    def digest(self) -> str:
        return sha256_digest(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generation_id": self.generation_id,
            "repository_root_identity": self.repository_root_identity,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "base_tree": self.base_tree,
            "observed_tree": self.observed_tree,
            "changed_paths": list(self.changed_paths),
            "status_records": [item.to_dict() for item in self.status_records],
            "dirty": self.dirty,
            "digest": self.digest,
        }


@dataclass(frozen=True)
class WorkspaceDriftResult:
    state: str
    expected_generation_digest: str
    current_generation_digest: str | None
    changed_paths: tuple[str, ...]
    reason_code: str

    def __post_init__(self) -> None:
        if self.state not in _VALID_STATES:
            raise ValueError("workspace_drift_state_invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "expected_generation_digest": self.expected_generation_digest,
            "current_generation_digest": self.current_generation_digest,
            "changed_paths": list(self.changed_paths),
            "reason_code": self.reason_code,
        }


def capture_workspace_generation(
    repository_root: str | Path,
    base_commit: str,
    generation_id: str,
) -> WorkspaceGeneration:
    """Capture one stable Agent-confirmed workspace generation without mutation."""

    if (
        not isinstance(generation_id, str)
        or not generation_id.strip()
        or len(generation_id.strip()) > _MAX_GENERATION_ID_LENGTH
    ):
        raise WorkspaceObservationError("GENERATION_ID_INVALID")
    supplied = _resolve_directory(repository_root)
    repo = _resolve_git_root(supplied)
    if repo != supplied:
        raise WorkspaceObservationError("REPOSITORY_ROOT_MISMATCH")

    normalized_base = str(base_commit).strip().lower()
    if not _SHA40.fullmatch(normalized_base):
        raise WorkspaceObservationError("BASE_COMMIT_INVALID")
    try:
        actual_base = _git(repo, "rev-parse", f"{normalized_base}^{{commit}}").stdout.strip().lower()
    except (OSError, RuntimeError, ValueError) as exc:
        raise WorkspaceObservationError("BASE_COMMIT_UNOBSERVABLE") from exc
    if actual_base != normalized_base:
        raise WorkspaceObservationError("BASE_COMMIT_MISMATCH")

    first = _observe(repo, actual_base)
    second = _observe(repo, actual_base)
    if first != second:
        raise WorkspaceObservationError("WORKSPACE_CHANGED_DURING_CAPTURE")

    head_commit, base_tree, observed_tree, changed_paths, status_records = first
    return WorkspaceGeneration(
        schema_version=_SCHEMA_VERSION,
        generation_id=generation_id.strip(),
        repository_root_identity=_repository_identity(repo),
        base_commit=actual_base,
        head_commit=head_commit,
        base_tree=base_tree,
        observed_tree=observed_tree,
        changed_paths=changed_paths,
        status_records=status_records,
        dirty=bool(status_records),
    )


def classify_workspace_generation(
    expected: WorkspaceGeneration,
    repository_root: str | Path,
) -> WorkspaceDriftResult:
    """Compare current local Git state with one explicit captured generation."""

    expected_digest = _safe_expected_digest(expected)
    if expected_digest is None:
        return WorkspaceDriftResult(
            state=UNKNOWN_DIRTY_STATE,
            expected_generation_digest="",
            current_generation_digest=None,
            changed_paths=(),
            reason_code="EXPECTED_GENERATION_INVALID",
        )

    try:
        supplied = _resolve_directory(repository_root)
        repo = _resolve_git_root(supplied)
        if repo != supplied or _repository_identity(repo) != expected.repository_root_identity:
            return _unknown(expected_digest, "REPOSITORY_IDENTITY_MISMATCH")
        current = capture_workspace_generation(
            repo,
            expected.base_commit,
            expected.generation_id,
        )
    except WorkspaceObservationError as exc:
        return _unknown(expected_digest, exc.code)
    except (OSError, RuntimeError, TypeError, ValueError):
        return _unknown(expected_digest, "WORKSPACE_OBSERVATION_FAILED")

    if current.base_commit != expected.base_commit:
        return _unknown(expected_digest, "BASE_COMMIT_MISMATCH")
    if current.head_commit != expected.head_commit:
        return _unknown(expected_digest, "HEAD_IDENTITY_DRIFT")
    if current.base_tree != expected.base_tree:
        return _unknown(expected_digest, "BASE_TREE_IDENTITY_DRIFT")

    if current.digest == expected_digest:
        state = AGENT_EXPECTED_MUTATION if expected.dirty else NO_DRIFT
        return WorkspaceDriftResult(
            state=state,
            expected_generation_digest=expected_digest,
            current_generation_digest=current.digest,
            changed_paths=(),
            reason_code="WORKSPACE_GENERATION_MATCH",
        )

    return WorkspaceDriftResult(
        state=EXTERNAL_LOCAL_MUTATION,
        expected_generation_digest=expected_digest,
        current_generation_digest=current.digest,
        changed_paths=_conservative_delta_paths(expected, current),
        reason_code="WORKSPACE_GENERATION_CHANGED",
    )


def _resolve_directory(repository_root: str | Path) -> Path:
    try:
        path = Path(repository_root).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise WorkspaceObservationError("REPOSITORY_UNOBSERVABLE") from exc
    if not path.is_dir():
        raise WorkspaceObservationError("REPOSITORY_UNOBSERVABLE")
    return path


def _resolve_git_root(supplied: Path) -> Path:
    try:
        raw = _git(supplied, "rev-parse", "--show-toplevel").stdout.strip()
        return Path(raw).resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise WorkspaceObservationError("REPOSITORY_UNOBSERVABLE") from exc


def _repository_identity(repo: Path) -> str:
    normalized = repo.as_posix()
    if re.match(r"^[A-Za-z]:/", normalized):
        normalized = normalized[0].lower() + normalized[1:]
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _observe(
    repo: Path,
    base_commit: str,
) -> tuple[
    str,
    str,
    str,
    tuple[str, ...],
    tuple[WorkspaceStatusRecord, ...],
]:
    try:
        head_before = _git(repo, "rev-parse", "HEAD").stdout.strip().lower()
        status_before = _status_records(repo)
        base_tree, observed_tree, changed_paths, _ = _snapshot_workspace(repo, base_commit)
        status_after = _status_records(repo)
        head_after = _git(repo, "rev-parse", "HEAD").stdout.strip().lower()
    except (OSError, RuntimeError, ValueError) as exc:
        raise WorkspaceObservationError("WORKSPACE_OBSERVATION_FAILED") from exc

    if (
        head_before != head_after
        or status_before != status_after
        or not _SHA40.fullmatch(head_before)
    ):
        raise WorkspaceObservationError("WORKSPACE_CHANGED_DURING_CAPTURE")
    return (
        head_after,
        base_tree,
        observed_tree,
        _bounded_changed_paths(changed_paths),
        status_after,
    )


def _status_records(repo: Path) -> tuple[WorkspaceStatusRecord, ...]:
    result = _git(
        repo,
        "-c",
        "status.relativePaths=false",
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--no-renames",
        "--ignore-submodules=none",
        "--",
    )
    records: list[WorkspaceStatusRecord] = []
    tokens = result.stdout.split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    if len(tokens) > _MAX_STATUS_RECORDS:
        raise WorkspaceObservationError("STATUS_EVIDENCE_TOO_LARGE")
    for raw in tokens:
        if len(raw) < 4 or raw[2] != " ":
            raise WorkspaceObservationError("STATUS_EVIDENCE_INVALID")
        path = raw[3:].replace("\\", "/")
        if not _valid_path(path):
            raise WorkspaceObservationError("STATUS_EVIDENCE_INVALID")
        records.append(
            WorkspaceStatusRecord(
                index_status=raw[0],
                worktree_status=raw[1],
                path=path,
            )
        )
    return tuple(sorted(records, key=lambda item: (item.path, item.index_status, item.worktree_status)))


def _valid_path(path: str) -> bool:
    return (
        isinstance(path, str)
        and bool(path)
        and "\0" not in path
        and len(path.encode("utf-8", errors="replace")) <= _MAX_PATH_BYTES
    )


def _bounded_changed_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(sorted(set(path.replace("\\", "/") for path in paths)))
    if len(normalized) > _MAX_CHANGED_PATHS or any(not _valid_path(path) for path in normalized):
        raise WorkspaceObservationError("CHANGED_PATH_EVIDENCE_TOO_LARGE")
    return normalized


def _safe_expected_digest(expected: WorkspaceGeneration) -> str | None:
    try:
        if not isinstance(expected, WorkspaceGeneration):
            return None
        digest = expected.digest
    except (TypeError, ValueError):
        return None
    return digest if re.fullmatch(r"[0-9a-f]{64}", digest) else None


def _unknown(expected_digest: str, reason: str) -> WorkspaceDriftResult:
    return WorkspaceDriftResult(
        state=UNKNOWN_DIRTY_STATE,
        expected_generation_digest=expected_digest,
        current_generation_digest=None,
        changed_paths=(),
        reason_code=reason,
    )


def _conservative_delta_paths(
    expected: WorkspaceGeneration,
    current: WorkspaceGeneration,
) -> tuple[str, ...]:
    expected_status = {
        item.path: (item.index_status, item.worktree_status)
        for item in expected.status_records
    }
    current_status = {
        item.path: (item.index_status, item.worktree_status)
        for item in current.status_records
    }
    status_delta = {
        path
        for path in set(expected_status) | set(current_status)
        if expected_status.get(path) != current_status.get(path)
    }
    if expected.observed_tree != current.observed_tree:
        # Tree identity tells us bytes changed, but deliberately does not maintain
        # a second per-file content database. Report the bounded Git path union.
        status_delta.update(expected.changed_paths)
        status_delta.update(current.changed_paths)
    return tuple(sorted(status_delta))
