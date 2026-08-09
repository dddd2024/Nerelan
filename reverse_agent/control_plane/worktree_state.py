"""Pure classification for governed working-tree paths.

This module classifies observations only.  It never deletes, restores, stages,
or otherwise mutates a working tree.
"""

from __future__ import annotations

from dataclasses import dataclass
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


_SENSITIVE_PATTERNS = (
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "**/credentials*",
    "**/*private*key*",
    "**/*.pem",
    "**/*.p12",
    "**/*.pfx",
    "**/*.exe",
    "**/*.dll",
)


def _normalized(path: str) -> str:
    value = path.replace("\\", "/").strip("/")
    pure = PurePosixPath(value)
    if not value or pure.is_absolute() or ".." in pure.parts or "\x00" in value:
        raise ValueError(f"unsafe worktree path: {path!r}")
    return value


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(
        path == pattern.rstrip("/**")
        or (pattern.endswith("/**") and path.startswith(pattern[:-3].rstrip("/") + "/"))
        or fnmatchcase(path, pattern)
        for pattern in patterns
    )


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
