"""Hook-safe, lazy-fetch-safe, actor-neutral Git workspace observation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import threading
import time
from typing import Any, Mapping, Sequence

_OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_OBJECT_FORMAT_LENGTHS = {"sha1": 40, "sha256": 64}
_SHA256_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_SCHEMA_VERSION = "3"
_MAX_GENERATION_ID_LENGTH = 128
_MAX_PATH_BYTES = 4096
_MAX_PATHS = 10_000
_MAX_GIT_OUTPUT_BYTES = 32 * 1024 * 1024
_GIT_IO_CHUNK_BYTES = 64 * 1024
_MAX_HASH_ARG_BATCH_COUNT = 256
_MAX_HASH_ARG_BATCH_BYTES = 24 * 1024
_GIT_TIMEOUT_SECONDS = 60
_SUPPORTED_FILE_MODES = frozenset({"100644", "100755", "120000"})

NO_DRIFT = "NO_DRIFT"
CAPTURED_DIRTY_MATCH = "CAPTURED_DIRTY_MATCH"
LOCAL_GENERATION_CHANGED = "LOCAL_GENERATION_CHANGED"
UNKNOWN_DIRTY_STATE = "UNKNOWN_DIRTY_STATE"
_VALID_STATES = frozenset(
    {NO_DRIFT, CAPTURED_DIRTY_MATCH, LOCAL_GENERATION_CHANGED, UNKNOWN_DIRTY_STATE}
)


class WorkspaceObservationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _valid_object_id(value: str, expected_length: int | None = None) -> bool:
    if not isinstance(value, str) or _OBJECT_ID.fullmatch(value) is None:
        return False
    return expected_length is None or len(value) == expected_length


def _object_id_length(value: str) -> int | None:
    return len(value) if _valid_object_id(value) else None


def _storage_object_id_length(repo: Path) -> int:
    object_format = _git_text(
        repo,
        "rev-parse",
        "--show-object-format=storage",
        error_code="OBJECT_FORMAT_UNOBSERVABLE",
    ).strip()
    length = _OBJECT_FORMAT_LENGTHS.get(object_format)
    if length is None:
        raise WorkspaceObservationError("OBJECT_FORMAT_UNSUPPORTED")
    return length


@dataclass(frozen=True, order=True)
class WorkspaceIndexEntry:
    path: str
    mode: str
    object_id: str
    skip_worktree: bool = False
    assume_unchanged: bool = False

    def __post_init__(self) -> None:
        if not _valid_path(self.path):
            raise ValueError("workspace_index_path_invalid")
        if self.mode not in _SUPPORTED_FILE_MODES:
            raise ValueError("workspace_index_mode_invalid")
        if not _valid_object_id(self.object_id):
            raise ValueError("workspace_index_object_invalid")
        if not isinstance(self.skip_worktree, bool) or not isinstance(
            self.assume_unchanged, bool
        ):
            raise ValueError("workspace_index_flags_invalid")

    def to_dict(self) -> dict[str, Any]:
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
    index_digest: str
    changed_paths: tuple[str, ...]
    index_entries: tuple[WorkspaceIndexEntry, ...]
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
        if not _SHA256_ID.fullmatch(self.repository_root_identity):
            raise ValueError("workspace_generation_repository_identity_invalid")
        if not _SHA256_ID.fullmatch(self.index_digest):
            raise ValueError("workspace_generation_index_digest_invalid")
        object_ids = [
            str(getattr(self, name))
            for name in ("base_commit", "head_commit", "base_tree", "observed_tree")
        ]
        object_lengths = {_object_id_length(value) for value in object_ids}
        if None in object_lengths or len(object_lengths) != 1:
            raise ValueError("workspace_generation_object_format_invalid")
        expected_oid_length = next(iter(object_lengths))
        for entry in self.index_entries:
            if not _valid_object_id(entry.object_id, expected_oid_length):
                raise ValueError("workspace_generation_index_object_format_invalid")
        if (
            len(self.changed_paths) > _MAX_PATHS
            or tuple(sorted(set(self.changed_paths))) != self.changed_paths
            or any(not _valid_path(path) for path in self.changed_paths)
        ):
            raise ValueError("workspace_generation_changed_paths_invalid")
        if (
            len(self.index_entries) > _MAX_PATHS
            or tuple(sorted(set(self.index_entries))) != self.index_entries
            or len({entry.path for entry in self.index_entries}) != len(self.index_entries)
        ):
            raise ValueError("workspace_generation_index_entries_invalid")
        if self.dirty is not bool(self.changed_paths):
            raise ValueError("workspace_generation_dirty_invalid")

    @property
    def digest(self) -> str:
        return _sha256_digest(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generation_id": self.generation_id,
            "repository_root_identity": self.repository_root_identity,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "base_tree": self.base_tree,
            "observed_tree": self.observed_tree,
            "index_digest": self.index_digest,
            "changed_paths": list(self.changed_paths),
            "index_entries": [entry.to_dict() for entry in self.index_entries],
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
        if self.expected_generation_digest and not re.fullmatch(
            r"[0-9a-f]{64}", self.expected_generation_digest
        ):
            raise ValueError("workspace_drift_expected_digest_invalid")
        if self.current_generation_digest is not None and not re.fullmatch(
            r"[0-9a-f]{64}", self.current_generation_digest
        ):
            raise ValueError("workspace_drift_current_digest_invalid")
        if tuple(sorted(set(self.changed_paths))) != self.changed_paths:
            raise ValueError("workspace_drift_changed_paths_invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "expected_generation_digest": self.expected_generation_digest,
            "current_generation_digest": self.current_generation_digest,
            "changed_paths": list(self.changed_paths),
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class _Observation:
    head_commit: str
    base_tree: str
    observed_tree: str
    index_digest: str
    changed_paths: tuple[str, ...]
    index_entries: tuple[WorkspaceIndexEntry, ...]


def capture_workspace_generation(
    repository_root: str | Path,
    base_commit: str,
    generation_id: str,
) -> WorkspaceGeneration:
    gid = str(generation_id).strip()
    if (
        not gid
        or gid != generation_id
        or len(gid) > _MAX_GENERATION_ID_LENGTH
    ):
        raise WorkspaceObservationError("GENERATION_ID_INVALID")
    supplied = _resolve_directory(repository_root)
    repo = _resolve_git_root(supplied)
    if repo != supplied:
        raise WorkspaceObservationError("REPOSITORY_ROOT_MISMATCH")
    oid_length = _storage_object_id_length(repo)
    base = str(base_commit).strip().lower()
    if not _valid_object_id(base, oid_length):
        raise WorkspaceObservationError("BASE_COMMIT_INVALID")
    actual = _git_text(
        repo,
        "rev-parse",
        f"{base}^{{commit}}",
        error_code="BASE_COMMIT_UNOBSERVABLE",
    ).strip().lower()
    if actual != base or not _valid_object_id(actual, oid_length):
        raise WorkspaceObservationError("BASE_COMMIT_MISMATCH")
    first = _observe_once(repo, actual, oid_length)
    second = _observe_once(repo, actual, oid_length)
    if first != second:
        raise WorkspaceObservationError("WORKSPACE_CHANGED_DURING_CAPTURE")
    return WorkspaceGeneration(
        _SCHEMA_VERSION,
        gid,
        _repository_identity(repo),
        actual,
        first.head_commit,
        first.base_tree,
        first.observed_tree,
        first.index_digest,
        first.changed_paths,
        first.index_entries,
        bool(first.changed_paths),
    )


def classify_workspace_generation(
    expected: WorkspaceGeneration,
    repository_root: str | Path,
) -> WorkspaceDriftResult:
    digest = _safe_expected_digest(expected)
    if digest is None:
        return _unknown("", "EXPECTED_GENERATION_INVALID")
    try:
        supplied = _resolve_directory(repository_root)
        repo = _resolve_git_root(supplied)
        if repo != supplied or _repository_identity(repo) != expected.repository_root_identity:
            return _unknown(digest, "REPOSITORY_IDENTITY_MISMATCH")
        current = capture_workspace_generation(
            repo, expected.base_commit, expected.generation_id
        )
    except WorkspaceObservationError as exc:
        return _unknown(digest, exc.code)
    except (OSError, RuntimeError, TypeError, ValueError):
        return _unknown(digest, "WORKSPACE_OBSERVATION_FAILED")
    if current.base_commit != expected.base_commit:
        return _unknown(digest, "BASE_COMMIT_MISMATCH")
    if current.head_commit != expected.head_commit:
        return _unknown(digest, "HEAD_IDENTITY_DRIFT")
    if current.base_tree != expected.base_tree:
        return _unknown(digest, "BASE_TREE_IDENTITY_DRIFT")
    if current.digest == digest:
        state = CAPTURED_DIRTY_MATCH if expected.dirty else NO_DRIFT
        return WorkspaceDriftResult(
            state,
            digest,
            current.digest,
            (),
            "WORKSPACE_GENERATION_MATCH",
        )
    return WorkspaceDriftResult(
        LOCAL_GENERATION_CHANGED,
        digest,
        current.digest,
        _conservative_delta_paths(expected, current),
        "WORKSPACE_GENERATION_CHANGED",
    )


def _observe_once(
    repo: Path, base_commit: str, oid_length: int
) -> _Observation:
    index_path = _real_index_path(repo)
    index_before = _read_optional_bytes(index_path)
    head_before = _git_text(repo, "rev-parse", "HEAD").strip().lower()
    base_tree = _git_text(repo, "rev-parse", f"{base_commit}^{{tree}}").strip().lower()
    if not _valid_object_id(head_before, oid_length) or not _valid_object_id(
        base_tree, oid_length
    ):
        raise WorkspaceObservationError("GIT_IDENTITY_INVALID")
    base_entries = _base_entries(repo, base_commit, oid_length)
    index_entries = _index_entries(repo, oid_length)
    untracked = _untracked_paths(repo)
    observed_tree, worktree_delta = _raw_observed_tree(
        repo, base_tree, index_entries, untracked, oid_length
    )
    changed_paths = _bounded_paths(
        (*worktree_delta, *_entry_delta_paths(base_entries, index_entries))
    )
    head_after = _git_text(repo, "rev-parse", "HEAD").strip().lower()
    index_after = _read_optional_bytes(index_path)
    if (
        head_before != head_after
        or not _valid_object_id(head_after, oid_length)
        or index_before != index_after
    ):
        raise WorkspaceObservationError("WORKSPACE_CHANGED_DURING_CAPTURE")
    return _Observation(
        head_after,
        base_tree,
        observed_tree,
        _semantic_index_digest(index_entries),
        changed_paths,
        index_entries,
    )


def _raw_observed_tree(
    repo: Path,
    base_tree: str,
    index_entries: tuple[WorkspaceIndexEntry, ...],
    untracked_paths: tuple[str, ...],
    oid_length: int,
) -> tuple[str, tuple[str, ...]]:
    tracked = {entry.path: entry for entry in index_entries}
    paths = _bounded_paths((*tracked, *untracked_paths))
    real_objects = _git_path(repo, "objects")
    with tempfile.TemporaryDirectory(prefix="nerelan-drift-") as temp_dir:
        temp = Path(temp_dir).resolve()
        index = temp / "index"
        objects = temp / "objects"
        objects.mkdir()
        env = {
            "GIT_INDEX_FILE": str(index),
            "GIT_OBJECT_DIRECTORY": str(objects),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": _git_alternate_object_directory(
                real_objects
            ),
        }
        _git_bytes(repo, "read-tree", "--empty", extra_env=env)
        items = _worktree_items(repo, paths, tracked, env, oid_length, temp)
        if items:
            index_info = b"".join(
                mode.encode("ascii")
                + b" "
                + oid.encode("ascii")
                + b"\t"
                + path.encode("utf-8")
                + b"\0"
                for path, mode, oid in items
            )
            _git_bytes(
                repo,
                "update-index",
                "-z",
                "--index-info",
                extra_env=env,
                input_bytes=index_info,
            )
        tree = _git_text(repo, "write-tree", extra_env=env).strip().lower()
        if not _valid_object_id(tree, oid_length):
            raise WorkspaceObservationError("OBSERVED_TREE_INVALID")
        delta = _git_bytes(
            repo,
            "diff-tree",
            "--no-ext-diff",
            "--no-textconv",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            "--no-renames",
            base_tree,
            tree,
            "--",
            extra_env=env,
        )
        return tree, _parse_path_tokens(delta)


def _worktree_items(
    repo: Path,
    paths: Sequence[str],
    tracked: Mapping[str, WorkspaceIndexEntry],
    env: Mapping[str, str],
    oid_length: int,
    scratch: Path,
) -> tuple[tuple[str, str, str], ...]:
    modes: dict[str, str] = {}
    line_safe_paths: list[str] = []
    argv_sources: list[tuple[str, str]] = []
    payload_dir = scratch / "hash-inputs"

    for path in paths:
        _ensure_no_parent_symlink(repo, path)
        candidate = repo.joinpath(*path.split("/"))
        try:
            info = os.lstat(candidate)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise WorkspaceObservationError("WORKTREE_PATH_UNOBSERVABLE") from exc

        if stat.S_ISLNK(info.st_mode):
            try:
                payload = os.fsencode(os.readlink(candidate))
            except OSError as exc:
                raise WorkspaceObservationError("WORKTREE_PATH_UNOBSERVABLE") from exc
            payload_dir.mkdir(exist_ok=True)
            payload_file = payload_dir / f"{len(argv_sources):05d}.blob"
            try:
                payload_file.write_bytes(payload)
            except OSError as exc:
                raise WorkspaceObservationError("WORKTREE_PATH_UNOBSERVABLE") from exc
            modes[path] = "120000"
            argv_sources.append((path, str(payload_file)))
            continue
        if not stat.S_ISREG(info.st_mode):
            raise WorkspaceObservationError("WORKTREE_PATH_TYPE_UNSUPPORTED")

        tracked_entry = tracked.get(path)
        modes[path] = (
            tracked_entry.mode
            if os.name == "nt"
            and tracked_entry is not None
            and tracked_entry.mode in {"100644", "100755"}
            else (
                "100755"
                if os.name != "nt" and info.st_mode & 0o111
                else "100644"
            )
        )
        if "\n" in path or "\r" in path:
            argv_sources.append((path, str(candidate)))
        else:
            line_safe_paths.append(path)

    object_ids: dict[str, str] = {}
    if line_safe_paths:
        output = _git_bytes(
            repo,
            "hash-object",
            "-w",
            "--no-filters",
            "--stdin-paths",
            extra_env=env,
            input_bytes=("\n".join(line_safe_paths) + "\n").encode("utf-8"),
        )
        hashed = output.splitlines()
        if len(hashed) != len(line_safe_paths):
            raise WorkspaceObservationError("WORKTREE_OBJECT_INVALID")
        for path, raw_oid in zip(line_safe_paths, hashed, strict=True):
            oid = _ascii(raw_oid, "WORKTREE_OBJECT_INVALID").lower()
            if not _valid_object_id(oid, oid_length):
                raise WorkspaceObservationError("WORKTREE_OBJECT_INVALID")
            object_ids[path] = oid

    if argv_sources:
        source_paths = [source for _, source in argv_sources]
        hashed = _hash_object_argv_batches(repo, source_paths, env, oid_length)
        for (path, _), oid in zip(argv_sources, hashed, strict=True):
            object_ids[path] = oid

    return tuple(
        (path, modes[path], object_ids[path])
        for path in paths
        if path in object_ids
    )


def _hash_object_argv_batches(
    repo: Path,
    source_paths: Sequence[str],
    env: Mapping[str, str],
    oid_length: int,
) -> tuple[str, ...]:
    object_ids: list[str] = []
    for batch in _command_arg_batches(source_paths):
        output = _git_bytes(
            repo,
            "hash-object",
            "-w",
            "--no-filters",
            "--",
            *batch,
            extra_env=env,
        )
        hashed = output.splitlines()
        if len(hashed) != len(batch):
            raise WorkspaceObservationError("WORKTREE_OBJECT_INVALID")
        for raw_oid in hashed:
            oid = _ascii(raw_oid, "WORKTREE_OBJECT_INVALID").lower()
            if not _valid_object_id(oid, oid_length):
                raise WorkspaceObservationError("WORKTREE_OBJECT_INVALID")
            object_ids.append(oid)
    if len(object_ids) != len(source_paths):
        raise WorkspaceObservationError("WORKTREE_OBJECT_INVALID")
    return tuple(object_ids)


def _command_arg_batches(values: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    batches: list[tuple[str, ...]] = []
    current: list[str] = []
    current_cost = 0
    for value in values:
        # Conservative cross-platform allowance for quoting / UTF encoding.
        item_cost = len(os.fsencode(value)) * 2 + 4
        if item_cost > _MAX_HASH_ARG_BATCH_BYTES:
            raise WorkspaceObservationError("WORKTREE_PATH_UNOBSERVABLE")
        if current and (
            len(current) >= _MAX_HASH_ARG_BATCH_COUNT
            or current_cost + item_cost > _MAX_HASH_ARG_BATCH_BYTES
        ):
            batches.append(tuple(current))
            current = []
            current_cost = 0
        current.append(value)
        current_cost += item_cost
    if current:
        batches.append(tuple(current))
    return tuple(batches)

def _base_entries(
    repo: Path, base: str, oid_length: int
) -> tuple[WorkspaceIndexEntry, ...]:
    output = _git_bytes(repo, "ls-tree", "-r", "-z", "--full-tree", base, "--")
    entries: list[WorkspaceIndexEntry] = []
    for token in _nul_tokens(output):
        try:
            metadata, raw_path = token.split(b"\t", 1)
            mode_raw, kind, oid_raw = metadata.split(b" ", 2)
        except ValueError as exc:
            raise WorkspaceObservationError("BASE_TREE_EVIDENCE_INVALID") from exc
        mode = _ascii(mode_raw, "BASE_TREE_EVIDENCE_INVALID")
        oid = _ascii(oid_raw, "BASE_TREE_EVIDENCE_INVALID").lower()
        path = _path_text(raw_path)
        if (
            kind != b"blob"
            or mode not in _SUPPORTED_FILE_MODES
            or not _valid_object_id(oid, oid_length)
        ):
            raise WorkspaceObservationError("GITLINK_OR_TREE_STATE_UNSUPPORTED")
        entries.append(WorkspaceIndexEntry(path, mode, oid))
    return _sorted_entries(entries)


def _index_entries(
    repo: Path, oid_length: int
) -> tuple[WorkspaceIndexEntry, ...]:
    output = _git_bytes(repo, "ls-files", "--stage", "-z", "--full-name", "--")
    raw_entries: list[WorkspaceIndexEntry] = []
    for token in _nul_tokens(output):
        try:
            metadata, raw_path = token.split(b"\t", 1)
            mode_raw, oid_raw, stage_raw = metadata.split(b" ", 2)
        except ValueError as exc:
            raise WorkspaceObservationError("INDEX_EVIDENCE_INVALID") from exc
        if _ascii(stage_raw, "INDEX_EVIDENCE_INVALID") != "0":
            raise WorkspaceObservationError("UNMERGED_INDEX")
        mode = _ascii(mode_raw, "INDEX_EVIDENCE_INVALID")
        oid = _ascii(oid_raw, "INDEX_EVIDENCE_INVALID").lower()
        if (
            mode not in _SUPPORTED_FILE_MODES
            or not _valid_object_id(oid, oid_length)
        ):
            raise WorkspaceObservationError("GITLINK_OR_INDEX_STATE_UNSUPPORTED")
        raw_entries.append(WorkspaceIndexEntry(_path_text(raw_path), mode, oid))

    semantic_flags = _index_semantic_flags(repo)
    raw_paths = {entry.path for entry in raw_entries}
    if set(semantic_flags) != raw_paths:
        raise WorkspaceObservationError("INDEX_EVIDENCE_INVALID")
    ordered = _sorted_entries(
        [
            WorkspaceIndexEntry(
                entry.path,
                entry.mode,
                entry.object_id,
                semantic_flags[entry.path][0],
                semantic_flags[entry.path][1],
            )
            for entry in raw_entries
        ]
    )
    _validate_index_blobs(repo, ordered)
    return ordered


def _index_semantic_flags(repo: Path) -> dict[str, tuple[bool, bool]]:
    # -v lowercases the ordinary/skip-worktree tag for assume-unchanged.
    # Deliberately do not use -f: fsmonitor-valid is cache state, not semantic
    # generation identity.
    output = _git_bytes(repo, "ls-files", "-v", "-z", "--full-name", "--")
    flags: dict[str, tuple[bool, bool]] = {}
    for token in _nul_tokens(output):
        if len(token) < 3 or token[1:2] != b" ":
            raise WorkspaceObservationError("INDEX_EVIDENCE_INVALID")
        tag = token[:1]
        if tag not in {b"H", b"h", b"S", b"s"}:
            raise WorkspaceObservationError("INDEX_EVIDENCE_INVALID")
        path = _path_text(token[2:])
        if path in flags:
            raise WorkspaceObservationError("INDEX_EVIDENCE_DUPLICATE_PATH")
        flags[path] = (tag in {b"S", b"s"}, tag in {b"h", b"s"})
    return flags

def _validate_index_blobs(repo: Path, entries: Sequence[WorkspaceIndexEntry]) -> None:
    # ls-files reports index metadata even when the recorded object is missing
    # or has a non-blob type. Worktree bytes cannot validate that staged object.
    object_ids = sorted({entry.object_id for entry in entries})
    if not object_ids:
        return
    output = _git_bytes(
        repo,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype)",
        input_bytes=("\n".join(object_ids) + "\n").encode("ascii"),
        error_code="INDEX_BLOB_UNOBSERVABLE",
    )
    expected = [(oid + " blob").encode("ascii") for oid in object_ids]
    if output.splitlines() != expected:
        raise WorkspaceObservationError("INDEX_BLOB_UNOBSERVABLE")



def _untracked_paths(repo: Path) -> tuple[str, ...]:
    return _parse_path_tokens(
        _git_bytes(repo, "ls-files", "--others", "--exclude-standard", "-z", "--full-name", "--")
    )


def _entry_delta_paths(
    base: tuple[WorkspaceIndexEntry, ...],
    current: tuple[WorkspaceIndexEntry, ...],
) -> tuple[str, ...]:
    left = {entry.path: _entry_identity(entry) for entry in base}
    right = {entry.path: _entry_identity(entry) for entry in current}
    return tuple(sorted(path for path in set(left) | set(right) if left.get(path) != right.get(path)))


def _conservative_delta_paths(
    expected: WorkspaceGeneration,
    current: WorkspaceGeneration,
) -> tuple[str, ...]:
    left = {
        entry.path: _entry_identity(entry) for entry in expected.index_entries
    }
    right = {
        entry.path: _entry_identity(entry) for entry in current.index_entries
    }
    changed = {
        path for path in set(left) | set(right) if left.get(path) != right.get(path)
    }
    if expected.observed_tree != current.observed_tree:
        changed.update(expected.changed_paths)
        changed.update(current.changed_paths)
    return _bounded_paths(changed)


def _entry_identity(entry: WorkspaceIndexEntry) -> tuple[str, str, bool, bool]:
    return (
        entry.mode,
        entry.object_id,
        entry.skip_worktree,
        entry.assume_unchanged,
    )


def _sorted_entries(
    entries: Sequence[WorkspaceIndexEntry],
) -> tuple[WorkspaceIndexEntry, ...]:
    if len(entries) > _MAX_PATHS:
        raise WorkspaceObservationError("PATH_EVIDENCE_TOO_LARGE")
    ordered = tuple(sorted(entries))
    if len({entry.path for entry in ordered}) != len(ordered):
        raise WorkspaceObservationError("INDEX_EVIDENCE_DUPLICATE_PATH")
    return ordered


def _bounded_paths(paths: Sequence[str] | set[str]) -> tuple[str, ...]:
    ordered = tuple(sorted(set(paths)))
    if len(ordered) > _MAX_PATHS or any(not _valid_path(path) for path in ordered):
        raise WorkspaceObservationError("PATH_EVIDENCE_INVALID")
    return ordered


def _valid_path(path: str) -> bool:
    if not isinstance(path, str) or not path or "\0" in path:
        return False
    try:
        encoded = path.encode("utf-8", "strict")
    except UnicodeError:
        return False
    if len(encoded) > _MAX_PATH_BYTES or path.startswith("/"):
        return False
    if os.name == "nt":
        if path.startswith("\\") or re.match(r"^[A-Za-z]:[/\\]", path):
            return False
        parts = path.replace("\\", "/").split("/")
    else:
        parts = path.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def _path_text(payload: bytes) -> str:
    try:
        value = payload.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise WorkspaceObservationError("PATH_EVIDENCE_INVALID") from exc
    if os.name == "nt":
        value = value.replace("\\", "/")
    if not _valid_path(value):
        raise WorkspaceObservationError("PATH_EVIDENCE_INVALID")
    return value


def _parse_path_tokens(payload: bytes) -> tuple[str, ...]:
    return _bounded_paths(tuple(_path_text(token) for token in _nul_tokens(payload)))


def _nul_tokens(payload: bytes) -> list[bytes]:
    parts = payload.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    if len(parts) > _MAX_PATHS:
        raise WorkspaceObservationError("PATH_EVIDENCE_TOO_LARGE")
    return parts


def _ensure_no_parent_symlink(repo: Path, path: str) -> None:
    current = repo
    for part in path.split("/")[:-1]:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise WorkspaceObservationError("WORKTREE_PATH_UNOBSERVABLE") from exc
        if stat.S_ISLNK(info.st_mode):
            raise WorkspaceObservationError("WORKTREE_PATH_PARENT_SYMLINK_UNSUPPORTED")
        if not stat.S_ISDIR(info.st_mode):
            raise WorkspaceObservationError("WORKTREE_PATH_UNOBSERVABLE")


def _resolve_directory(root: str | Path) -> Path:
    try:
        path = Path(root).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise WorkspaceObservationError("REPOSITORY_UNOBSERVABLE") from exc
    if not path.is_dir():
        raise WorkspaceObservationError("REPOSITORY_UNOBSERVABLE")
    return path


def _resolve_git_root(supplied: Path) -> Path:
    raw = _git_text(
        supplied,
        "rev-parse",
        "--show-toplevel",
        error_code="REPOSITORY_UNOBSERVABLE",
    )
    try:
        return Path(raw.strip()).resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise WorkspaceObservationError("REPOSITORY_UNOBSERVABLE") from exc


def _repository_identity(repo: Path) -> str:
    normalized = repo.as_posix()
    if re.match(r"^[A-Za-z]:/", normalized):
        normalized = normalized[0].lower() + normalized[1:]
    return _sha256_id(normalized.encode())


def _real_index_path(repo: Path) -> Path:
    return _git_path(repo, "index")


def _git_path(repo: Path, name: str) -> Path:
    raw = _git_text(repo, "rev-parse", "--git-path", name).strip()
    try:
        path = Path(raw)
        return (path if path.is_absolute() else repo / path).resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise WorkspaceObservationError("GIT_PATH_UNOBSERVABLE") from exc


def _read_optional_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes() if path.exists() else b""
    except OSError as exc:
        raise WorkspaceObservationError("INDEX_UNOBSERVABLE") from exc


def _git_alternate_object_directory(path: Path) -> str:
    raw = os.fsencode(str(path))
    pieces: list[str] = []
    for byte in raw:
        if 0x20 <= byte <= 0x7E and byte not in (0x22, 0x5C):
            pieces.append(chr(byte))
        elif byte == 0x22:
            pieces.append(r'\"')
        elif byte == 0x5C:
            pieces.append(r'\\')
        else:
            pieces.append(f"\\{byte:03o}")
    return '"' + "".join(pieces) + '"'


def _git_text(
    repo: Path,
    *args: str,
    extra_env: Mapping[str, str] | None = None,
    input_bytes: bytes | None = None,
    error_code: str = "GIT_OBSERVATION_FAILED",
) -> str:
    data = _git_bytes(
        repo,
        *args,
        extra_env=extra_env,
        input_bytes=input_bytes,
        error_code=error_code,
    )
    try:
        return data.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise WorkspaceObservationError(error_code) from exc


def _git_bytes(
    repo: Path,
    *args: str,
    extra_env: Mapping[str, str] | None = None,
    input_bytes: bytes | None = None,
    error_code: str = "GIT_OBSERVATION_FAILED",
) -> bytes:
    # Repository selection/configuration belongs to this observation, never
    # to ambient Git environment inherited from a caller or another worktree.
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    if extra_env:
        scratch_keys = {"GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"}
        env.update({key: str(value) for key, value in extra_env.items() if key in scratch_keys})
    # Security invariants are written after extra_env so no internal scratch
    # configuration can weaken observation safety.
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_NO_LAZY_FETCH"] = "1"
    # Check the named raw objects, not repository-controlled replacement refs.
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    command = (
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        *args,
    )
    try:
        result = _execute_git(
            command, cwd=repo, env=env, input_bytes=input_bytes
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkspaceObservationError(error_code) from exc
    if result.returncode != 0 or len(result.stdout) > _MAX_GIT_OUTPUT_BYTES:
        raise WorkspaceObservationError(error_code)
    return result.stdout


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _execute_git(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    input_bytes: bytes | None,
) -> subprocess.CompletedProcess[bytes]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=dict(env),
        stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        shell=False,
        bufsize=0,
    )
    assert process.stdout is not None and process.stderr is not None

    stdout = bytearray()
    stderr = bytearray()
    overflow = threading.Event()

    def read_bounded(stream: Any, sink: bytearray) -> None:
        while True:
            chunk = stream.read(_GIT_IO_CHUNK_BYTES)
            if not chunk:
                return
            remaining = _MAX_GIT_OUTPUT_BYTES - len(sink)
            if remaining > 0:
                sink.extend(chunk[:remaining])
            if len(chunk) > max(remaining, 0):
                overflow.set()

    readers = [
        threading.Thread(target=read_bounded, args=(process.stdout, stdout), daemon=True),
        threading.Thread(target=read_bounded, args=(process.stderr, stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()

    writer: threading.Thread | None = None
    if input_bytes is not None:
        assert process.stdin is not None

        def write_input() -> None:
            try:
                process.stdin.write(input_bytes)
            except (BrokenPipeError, OSError):
                pass
            finally:
                try:
                    process.stdin.close()
                except OSError:
                    pass

        writer = threading.Thread(target=write_input, daemon=True)
        writer.start()

    deadline = time.monotonic() + _GIT_TIMEOUT_SECONDS
    timed_out = False
    while process.poll() is None:
        if overflow.is_set():
            _stop_process(process)
            break
        if time.monotonic() >= deadline:
            timed_out = True
            _stop_process(process)
            break
        time.sleep(0.005)

    if writer is not None:
        writer.join(timeout=1)
    for reader in readers:
        reader.join(timeout=1)

    if timed_out:
        raise subprocess.TimeoutExpired(
            command,
            _GIT_TIMEOUT_SECONDS,
            output=bytes(stdout),
            stderr=bytes(stderr),
        )
    returncode = process.returncode if process.returncode is not None else 1
    if overflow.is_set() and returncode == 0:
        returncode = 125
    return subprocess.CompletedProcess(
        command,
        returncode,
        bytes(stdout),
        bytes(stderr),
    )


def _ascii(payload: bytes, code: str) -> str:
    try:
        return payload.decode("ascii", "strict")
    except UnicodeError as exc:
        raise WorkspaceObservationError(code) from exc


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("unsupported_workspace_digest_type")


def _sha256_digest(value: Any) -> str:
    payload = json.dumps(
        _plain(value),
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _sha256_id(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _semantic_index_digest(
    entries: Sequence[WorkspaceIndexEntry],
) -> str:
    payload = json.dumps(
        [
            [
                entry.mode,
                entry.object_id,
                entry.path,
                entry.skip_worktree,
                entry.assume_unchanged,
            ]
            for entry in entries
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_id(payload)


def _safe_expected_digest(expected: WorkspaceGeneration) -> str | None:
    try:
        if not isinstance(expected, WorkspaceGeneration):
            return None
        digest = expected.digest
    except (TypeError, ValueError):
        return None
    return digest if re.fullmatch(r"[0-9a-f]{64}", digest) else None


def _unknown(digest: str, reason: str) -> WorkspaceDriftResult:
    return WorkspaceDriftResult(UNKNOWN_DIRTY_STATE, digest, None, (), reason)
