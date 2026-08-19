"""Pure classification for governed working-tree paths.

This module classifies observations only.  It never deletes, restores, stages,
or otherwise mutates a working tree.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from typing import Iterable


class WorktreeClassification(str, Enum):
    AUTHORIZED_TRACKED_DELTA = "AUTHORIZED_TRACKED_DELTA"
    KNOWN_RUNTIME_SCRATCH = "KNOWN_RUNTIME_SCRATCH"
    GENERATED_GOVERNANCE_ARTIFACT = "GENERATED_GOVERNANCE_ARTIFACT"
    UNKNOWN_UNTRACKED = "UNKNOWN_UNTRACKED"
    UNAUTHORIZED_TRACKED_OR_SENSITIVE = "UNAUTHORIZED_TRACKED_OR_SENSITIVE"


@dataclass(frozen=True)
class WorktreePathClassification:
    path: str
    classification: WorktreeClassification
    stageable: bool
    bootstrap_blocking: bool
    publication_blocking: bool
    deleted: bool = False
    tracked: bool = False
    status_code: str = ""

    def to_mapping(self) -> dict[str, object]:
        payload = asdict(self)
        payload["classification"] = self.classification.value
        return payload


_SENSITIVE_PATTERNS = (
    "secrets/**",
    "**/secrets/**",
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "*credential*",
    "**/*credential*",
    "*secret*",
    "**/*secret*",
    "*.pem",
    "**/credentials*",
    "**/*private*key*",
    "**/*.pem",
    "*.key",
    "**/*.key",
    "*.p12",
    "**/*.p12",
    "*.pfx",
    "**/*.pfx",
    "*.exe",
    "**/*.exe",
    "*.dll",
    "**/*.dll",
    "*.so",
    "**/*.so",
    "*.dylib",
    "**/*.dylib",
)


def _normalized(path: str) -> str:
    value = path.replace("\\", "/").strip("/")
    pure = PurePosixPath(value)
    if not value or pure.is_absolute() or ".." in pure.parts or "\x00" in value:
        raise ValueError(f"unsafe worktree path: {path!r}")
    return value


def _matches(path: str, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        if pattern.endswith("/**"):
            root = pattern[:-3].rstrip("/")
            if path == root or path.startswith(root + "/"):
                return True
        if fnmatchcase(path, pattern):
            return True
    return False


def classify_worktree_path(
    path: str,
    *,
    tracked: bool,
    authorized_paths: Iterable[str] = (),
) -> WorktreePathClassification:
    """Classify one path without changing it or the repository."""

    normalized = _normalized(path)
    folded = normalized.casefold()
    sensitive = _matches(folded, (pattern.casefold() for pattern in _SENSITIVE_PATTERNS))
    if sensitive:
        classification = WorktreeClassification.UNAUTHORIZED_TRACKED_OR_SENSITIVE
    elif normalized == "project_state/gates" or normalized.startswith("project_state/gates/"):
        classification = WorktreeClassification.GENERATED_GOVERNANCE_ARTIFACT
    elif tracked:
        normalized_authority = tuple(_normalized(item) for item in authorized_paths)
        classification = (
            WorktreeClassification.AUTHORIZED_TRACKED_DELTA
            if _matches(normalized, normalized_authority)
            else WorktreeClassification.UNAUTHORIZED_TRACKED_OR_SENSITIVE
        )
    elif normalized in {"task_workspaces", ".platform_v1_runtime"} or normalized.startswith(
        ("task_workspaces/", ".platform_v1_runtime/")
    ):
        classification = WorktreeClassification.KNOWN_RUNTIME_SCRATCH
    else:
        classification = WorktreeClassification.UNKNOWN_UNTRACKED

    stageable = classification is WorktreeClassification.AUTHORIZED_TRACKED_DELTA
    bootstrap_blocking = classification is WorktreeClassification.UNAUTHORIZED_TRACKED_OR_SENSITIVE
    publication_blocking = classification in {
        WorktreeClassification.UNKNOWN_UNTRACKED,
        WorktreeClassification.UNAUTHORIZED_TRACKED_OR_SENSITIVE,
    }
    return WorktreePathClassification(
        path=normalized,
        classification=classification,
        stageable=stageable,
        bootstrap_blocking=bootstrap_blocking,
        publication_blocking=publication_blocking,
    )


def classify_worktree_status(
    status_lines: Iterable[str],
    *,
    authorized_paths: Iterable[str] = (),
) -> tuple[WorktreePathClassification, ...]:
    """Normalize ``git status --short`` records and classify every path.

    Exact-authorized untracked additions are governed deltas rather than
    arbitrary untracked content. Rename/copy records classify both the old and
    new path so authority cannot be bypassed through a previous pathname.
    """

    authority = tuple(_normalized(path) for path in authorized_paths)
    records: list[WorktreePathClassification] = []
    for raw_line in status_lines:
        line = str(raw_line).rstrip()
        if len(line) < 4:
            raise ValueError(f"malformed git status record: {line!r}")
        status_code = line[:2]
        path_text = line[3:].strip().strip('"')
        paths = tuple(part.strip().strip('"') for part in path_text.split(" -> "))
        if not all(paths):
            raise ValueError(f"malformed git status path: {line!r}")
        git_tracked = status_code != "??"
        for path in paths:
            normalized = _normalized(path)
            authority_tracked = _matches(normalized, authority)
            classified = classify_worktree_path(
                normalized,
                tracked=git_tracked or authority_tracked,
                authorized_paths=authority,
            )
            records.append(
                replace(
                    classified,
                    tracked=git_tracked,
                    status_code=status_code,
                )
            )
    unique = {(record.status_code, record.path): record for record in records}
    return tuple(unique[key] for key in sorted(unique))
