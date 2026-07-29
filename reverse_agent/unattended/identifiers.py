"""Deterministic identifiers for one bounded unattended attempt."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

TASK_QUEUE = "reverse-agent-unattended-v0"
_SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")


def _slug(value: str, field: str) -> str:
    normalized = value.strip()
    if not _SLUG.fullmatch(normalized):
        raise ValueError(f"invalid_{field}")
    return normalized


def workflow_id(owner: str, repository: str, issue_number: int) -> str:
    """Return the frozen Gate 2 workflow identifier."""

    if isinstance(issue_number, bool) or issue_number <= 0:
        raise ValueError("invalid_issue_number")
    return (
        f"unattended:{_slug(owner, 'owner')}/{_slug(repository, 'repository')}"
        f":issue:{issue_number}"
    )


def workspace_path(identifier: str, attempt: int) -> str:
    """Return the exact repository-relative POSIX workspace projection."""

    if not identifier.startswith("unattended:") or "\x00" in identifier:
        raise ValueError("invalid_workflow_id")
    if isinstance(attempt, bool) or attempt < 1 or attempt > 2:
        raise ValueError("invalid_attempt")
    path = PurePosixPath(".var", "unattended", identifier, str(attempt))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("workspace_escape")
    return path.as_posix()
