"""Fail-closed policy resolution for the v0 unattended lane."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from .contracts import MinimalWorkItem, ResolvedExecutionPolicy

_RISK_TIERS = frozenset({"R0", "R1", "R2", "R3"})
_UNATTENDED_FORBIDDEN = frozenset(
    {
        "auto_merge",
        "direct_push_to_main",
        "force_push",
        "merge",
        "rebase",
        "release",
        "squash",
        "tag",
    }
)
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:")


class PolicyViolation(ValueError):
    """A bounded work item failed closed."""


def _normalize_allowed_path(raw: str) -> str:
    if not isinstance(raw, str):
        raise PolicyViolation("allowed_path_must_be_string")
    value = raw.strip().replace("\\", "/")
    if (
        not value
        or value in {".", "*", "**", "*/**"}
        or value.startswith("/")
        or _WINDOWS_ABSOLUTE.match(value)
        or "\x00" in value
    ):
        raise PolicyViolation("empty_broad_or_absolute_allowed_path")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise PolicyViolation("allowed_path_traversal")
    if path.parts[0] in {"*", "**"}:
        raise PolicyViolation("repository_wide_allowed_path")
    return path.as_posix()


def resolve_execution_policy(work_item: MinimalWorkItem) -> ResolvedExecutionPolicy:
    """Validate and resolve policy without widening the supplied authority."""

    risk_tier = work_item.risk_tier.strip().upper()
    if risk_tier not in _RISK_TIERS:
        raise PolicyViolation("invalid_risk_tier")
    if isinstance(work_item.max_attempts, bool) or not 1 <= work_item.max_attempts <= 2:
        raise PolicyViolation("max_attempts_out_of_bounds")
    if work_item.auto_merge_allowed:
        raise PolicyViolation("auto_merge_forbidden")
    if not work_item.allowed_paths:
        raise PolicyViolation("empty_allowed_paths")

    normalized_paths = tuple(
        dict.fromkeys(_normalize_allowed_path(path) for path in work_item.allowed_paths)
    )
    normalized_operations = tuple(
        dict.fromkeys(operation.strip().lower() for operation in work_item.forbidden_operations)
    )
    if any(not operation for operation in normalized_operations):
        raise PolicyViolation("empty_forbidden_operation")
    if _UNATTENDED_FORBIDDEN.intersection(normalized_operations):
        raise PolicyViolation("forbidden_operation_requested")

    approval_required = risk_tier in {"R2", "R3"}
    if approval_required and not work_item.approval_granted:
        raise PolicyViolation("approval_required")

    return ResolvedExecutionPolicy(
        unattended_allowed=True,
        approval_required=approval_required,
        allowed_paths=normalized_paths,
        forbidden_operations=normalized_operations,
        auto_merge_allowed=False,
        max_attempts=work_item.max_attempts,
    )
