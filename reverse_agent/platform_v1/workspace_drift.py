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
from typing import Any, Mapping, Sequence

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_SCHEMA_VERSION = "3"
_MAX_GENERATION_ID_LENGTH = 128
_MAX_PATH_BYTES = 4096
_MAX_PATHS = 10_000
_MAX_GIT_OUTPUT_BYTES = 32 * 1024 * 1024
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


@dataclass(frozen=True, order=True)
class WorkspaceIndexEntry:
    path: str
    mode: str
    object_id: str

    def __post_init__(self) -> None:
        if not _valid_path(self.path):
            raise ValueError("workspace_index_path_invalid")
        if self.mode not in _SUPPORTED_FILE_MODES:
            raise ValueError("workspace_index_mode_invalid")
        if not _SHA40.fullmatch(self.object_id):
            raise ValueError("workspace_index_object_invalid")

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
        for name in ("base_commit", "head_commit", "base_tree", "observed_tree"):
            if not _SHA40.fullmatch(str(getattr(self, name))):
                raise ValueError(f"workspace_generation_{name}_invalid")
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
    base = str(base_commit).strip().lower()
    if not _SHA40.fullmatch(base):
        raise WorkspaceObservationError("BASE_COMMIT_INVALID")
    actual = _git_text(
        repo,
        "rev-parse",
        f"{base}^{{commit}}",
        error_code="BASE_COMMIT_UNOBSERVABLE",
    ).strip().lower()
    if actual != base:
        raise WorkspaceObservationError("BASE_COMMIT_MISMATCH")
    first = _observe_once(repo, actual)
    second = _observe_once(repo, actual)
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


def _observe_once(repo: Path, base_commit: str) -> _Observation:
    index_path = _real_index_path(repo)
    index_before = _read_optional_bytes(index_path)
    head_before = _git_text(repo, "rev-parse", "HEAD").strip().lower()
    base_tree = _git_text(repo, "rev-parse", f"{base_commit}^{{tree}}").strip().lower()
    if not _SHA40.fullmatch(head_before) or not _SHA40.fullmatch(base_tree):
        raise WorkspaceObservationError("GIT_IDENTITY_INVALID")
    base_entries = _base_entries(repo, base_commit)
    index_entries = _index_entries(repo)
    untracked = _untracked_paths(repo)
    observed_tree, worktree_delta = _raw_observed_tree(
        repo, base_tree, index_entries, untracked
    )
    changed_paths = _bounded_paths(
        (*worktree_delta, *_entry_delta_paths(base_entries, index_entries))
    )
    head_after = _git_text(repo, "rev-parse", "HEAD").strip().lower()
    index_after = _read_optional_bytes(index_path)
    if head_before != head_after or index_before != index_after:
        raise WorkspaceObservationError("WORKSPACE_CHANGED_DURING_CAPTURE")
    return _Observation(
        head_after,
        base_tree,
        observed_tree,
        _sha256_id(index_before),
        changed_paths,
        index_entries,
    )


def _raw_observed_tree(
    repo: Path,
    base_tree: str,
    index_entries: tuple[WorkspaceIndexEntry, ...],
    untracked_paths: tuple[str, ...],
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
        for path in paths:
            item = _worktree_item(repo, path, tracked.get(path), env)
            if item is not None:
                _git_bytes(
                    repo,
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    item[0],
                    item[1],
                    path,
                    extra_env=env,
                )
        tree = _git_text(repo, "write-tree", extra_env=env).strip().lower()
        if not _SHA40.fullmatch(tree):
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


def _worktree_item(
    repo: Path,
    path: str,
    tracked: WorkspaceIndexEntry | None,
    env: Mapping[str, str],
) -> tuple[str, str] | None:
    _ensure_no_parent_symlink(repo, path)
    candidate = repo.joinpath(*path.split("/"))
    try:
        info = os.lstat(candidate)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise WorkspaceObservationError("WORKTREE_PATH_UNOBSERVABLE") from exc
    if stat.S_ISLNK(info.st_mode):
        try:
            payload = os.fsencode(os.readlink(candidate))
        except OSError as exc:
            raise WorkspaceObservationError("WORKTREE_PATH_UNOBSERVABLE") from exc
        oid = _git_text(
            repo,
            "hash-object",
            "-w",
            "--no-filters",
            "--stdin",
            extra_env=env,
            input_bytes=payload,
        ).strip().lower()
        mode = "120000"
    elif stat.S_ISREG(info.st_mode):
        oid = _git_text(
            repo,
            "hash-object",
            "-w",
            "--no-filters",
            "--",
            path,
            extra_env=env,
        ).strip().lower()
        mode = (
            tracked.mode
            if os.name == "nt"
            and tracked is not None
            and tracked.mode in {"100644", "100755"}
            else (
                "100755"
                if os.name != "nt" and info.st_mode & 0o111
                else "100644"
            )
        )
    else:
        raise WorkspaceObservationError("WORKTREE_PATH_TYPE_UNSUPPORTED")
    if not _SHA40.fullmatch(oid):
        raise WorkspaceObservationError("WORKTREE_OBJECT_INVALID")
    return mode, oid


def _base_entries(repo: Path, base: str) -> tuple[WorkspaceIndexEntry, ...]:
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
        if kind != b"blob" or mode not in _SUPPORTED_FILE_MODES:
            raise WorkspaceObservationError("GITLINK_OR_TREE_STATE_UNSUPPORTED")
        entries.append(WorkspaceIndexEntry(path, mode, oid))
    return _sorted_entries(entries)


def _index_entries(repo: Path) -> tuple[WorkspaceIndexEntry, ...]:
    output = _git_bytes(repo, "ls-files", "--stage", "-z", "--full-name", "--")
    entries: list[WorkspaceIndexEntry] = []
    for token in _nul_tokens(output):
        try:
            metadata, raw_path = token.split(b"\t", 1)
            mode_raw, oid_raw, stage_raw = metadata.split(b" ", 2)
        except ValueError as exc:
            raise WorkspaceObservationError("INDEX_EVIDENCE_INVALID") from exc
        if _ascii(stage_raw, "INDEX_EVIDENCE_INVALID") != "0":
            raise WorkspaceObservationError("UNMERGED_INDEX")
        mode = _ascii(mode_raw, "INDEX_EVIDENCE_INVALID")
        if mode not in _SUPPORTED_FILE_MODES:
            raise WorkspaceObservationError("GITLINK_OR_INDEX_STATE_UNSUPPORTED")
        entries.append(
            WorkspaceIndexEntry(
                _path_text(raw_path),
                mode,
                _ascii(oid_raw, "INDEX_EVIDENCE_INVALID").lower(),
            )
        )
    return _sorted_entries(entries)


def _untracked_paths(repo: Path) -> tuple[str, ...]:
    return _parse_path_tokens(
        _git_bytes(repo, "ls-files", "--others", "--exclude-standard", "-z", "--full-name", "--")
    )


def _entry_delta_paths(
    base: tuple[WorkspaceIndexEntry, ...],
    current: tuple[WorkspaceIndexEntry, ...],
) -> tuple[str, ...]:
    left = {entry.path: (entry.mode, entry.object_id) for entry in base}
    right = {entry.path: (entry.mode, entry.object_id) for entry in current}
    return tuple(sorted(path for path in set(left) | set(right) if left.get(path) != right.get(path)))


def _conservative_delta_paths(
    expected: WorkspaceGeneration,
    current: WorkspaceGeneration,
) -> tuple[str, ...]:
    left = {
        entry.path: (entry.mode, entry.object_id) for entry in expected.index_entries
    }
    right = {
        entry.path: (entry.mode, entry.object_id) for entry in current.index_entries
    }
    changed = {
        path for path in set(left) | set(right) if left.get(path) != right.get(path)
    }
    if expected.observed_tree != current.observed_tree:
        changed.update(expected.changed_paths)
        changed.update(current.changed_paths)
    return _bounded_paths(changed)


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
    env = os.environ.copy()
    if extra_env:
        env.update({str(key): str(value) for key, value in extra_env.items()})
    # Security invariants are written after extra_env so no internal scratch
    # configuration can weaken observation safety.
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_NO_LAZY_FETCH"] = "1"
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


def _execute_git(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    input_bytes: bytes | None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=dict(env),
        input=input_bytes,
        capture_output=True,
        text=False,
        timeout=_GIT_TIMEOUT_SECONDS,
        check=False,
        shell=False,
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
