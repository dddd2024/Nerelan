"""Fail-closed policy resolution for the v0 unattended lane."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from .contracts import MinimalWorkItem, ResolvedExecutionPolicy

_RISK_TIERS = frozenset({"R0", "R1", "R2", "R3"})
_DANGEROUS_OPERATIONS = frozenset(
    {
        "auto_merge",
        "direct_push_to_main",
        "force_push",
        "merge",
        "rebase",
        "release",
        "secret_access",
        "squash",
        "tag",
    }
)
_R0_OPERATIONS = ("observe_repository", "run_required_checks")
_R1_OPERATIONS = (
    "edit_allowed_paths",
    "run_required_checks",
    "push_bound_branch",
    "create_draft_pr",
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


def _normalize_operation(raw: str) -> str:
    if not isinstance(raw, str):
        raise PolicyViolation("forbidden_operation_must_be_string")
    operation = raw.strip().lower().replace("-", "_").replace(" ", "_")
    if not operation or "\x00" in operation:
        raise PolicyViolation("empty_forbidden_operation")
    return operation


def resolve_execution_policy(work_item: MinimalWorkItem) -> ResolvedExecutionPolicy:
    """Preserve restrictions and derive only the fixed bounded v0 operations."""

    risk_tier = work_item.risk_tier.strip().upper()
    if risk_tier not in _RISK_TIERS:
        raise PolicyViolation("invalid_risk_tier")
    if isinstance(work_item.max_attempts, bool) or not 1 <= work_item.max_attempts <= 2:
        raise PolicyViolation("max_attempts_out_of_bounds")
    if not work_item.allowed_paths:
        raise PolicyViolation("empty_allowed_paths")

    normalized_paths = tuple(
        dict.fromkeys(_normalize_allowed_path(path) for path in work_item.allowed_paths)
    )
    restrictions = frozenset(
        _normalize_operation(operation)
        for operation in work_item.forbidden_operations
    )

    approval_required = risk_tier in {"R2", "R3"}
    candidates = _R0_OPERATIONS if risk_tier == "R0" else _R1_OPERATIONS
    allowed_operations = tuple(
        operation
        for operation in candidates
        if operation not in restrictions and operation not in _DANGEROUS_OPERATIONS
    )
    if _DANGEROUS_OPERATIONS.intersection(allowed_operations):
        raise PolicyViolation("dangerous_operation_resolved")

    blocking_reasons = (
        (f"{risk_tier.lower()}_approval_required",)
        if approval_required
        else ()
    )
    unattended_allowed = not blocking_reasons
    draft_pr_allowed = (
        unattended_allowed and "create_draft_pr" in allowed_operations
    )
    network_mode = (
        "bounded"
        if unattended_allowed
        and {"push_bound_branch", "create_draft_pr"}.intersection(
            allowed_operations
        )
        else "none"
    )

    return ResolvedExecutionPolicy(
        unattended_allowed=unattended_allowed,
        allowed_paths=normalized_paths,
        allowed_operations=allowed_operations if unattended_allowed else (),
        network_mode=network_mode,
        max_attempts=work_item.max_attempts,
        draft_pr_allowed=draft_pr_allowed,
        auto_merge_allowed=False,
        approval_required=approval_required,
        blocking_reasons=blocking_reasons,
    )
