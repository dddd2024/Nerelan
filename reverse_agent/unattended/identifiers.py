"""Deterministic identifiers for one bounded unattended attempt."""

from __future__ import annotations

import re
import uuid
from pathlib import PurePosixPath

TASK_QUEUE = "reverse-agent-unattended-v0"
_SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")
_WORKSPACE_NAMESPACE = uuid.UUID("0e62e967-8aa7-5d4c-93a8-eb98feaa7b45")
_EXECUTOR_NAMESPACE = uuid.UUID("f1ea8fb8-d944-54c7-8706-3e3ef71b030d")


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


def _validate_identifier(identifier: str) -> None:
    if not identifier.startswith("unattended:") or "\x00" in identifier:
        raise ValueError("invalid_workflow_id")


def workspace_id(identifier: str) -> str:
    """Return the deterministic workspace identity for one workflow."""

    _validate_identifier(identifier)
    return str(uuid.uuid5(_WORKSPACE_NAMESPACE, identifier))


def executor_id(identifier: str, attempt: int) -> str:
    """Return the deterministic OpenHands executor identity for one attempt."""

    _validate_identifier(identifier)
    if isinstance(attempt, bool) or attempt < 1 or attempt > 2:
        raise ValueError("invalid_attempt")
    return str(
        uuid.uuid5(
            _EXECUTOR_NAMESPACE,
            f"{identifier}:attempt:{attempt}",
        )
    )


def workspace_path(identifier: str, attempt: int) -> str:
    """Return the exact repository-relative POSIX workspace projection."""

    stable_workspace_id = workspace_id(identifier)
    if isinstance(attempt, bool) or attempt < 1 or attempt > 2:
        raise ValueError("invalid_attempt")
    path = PurePosixPath(".var", "unattended", stable_workspace_id, str(attempt))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("workspace_escape")
    return path.as_posix()
