"""Policy adapter: fail-closed validation for Platform V1 execution.

Enforces that only authorized R2 operations proceed. R3, broad path scope,
empty path scope, and forbidden publication operations all fail closed.
"""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

from .contracts import (
    FORBIDDEN_PUBLICATION_OPERATIONS,
    ExecutionBinding,
    PlatformWorkItem,
)


# ---------------------------------------------------------------------------
# Path matching
# ---------------------------------------------------------------------------

def _path_matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    candidate = pattern.replace("\\", "/").lstrip("./")
    if candidate.endswith("/**"):
        prefix = candidate[:-3].rstrip("/")
        return normalized == prefix or normalized.startswith(prefix + "/")
    return normalized == candidate or fnmatch(normalized, candidate)


def _path_within_scope(path: str, patterns: tuple[str, ...]) -> bool:
    return any(_path_matches(path, pattern) for pattern in patterns)


def _paths_outside_scope(paths: tuple[str, ...], patterns: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(p for p in paths if not _path_within_scope(p, patterns))


# ---------------------------------------------------------------------------
# Policy result
# ---------------------------------------------------------------------------

class PolicyViolation(Exception):
    """Raised when a policy check fails. The message is a stable error code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


# ---------------------------------------------------------------------------
# Policy checks
# ---------------------------------------------------------------------------

def validate_work_item(work_item: PlatformWorkItem) -> None:
    """Validate a Work Item against the platform policy.

    Raises ``PolicyViolation`` on any failure. Fail-closed for:
    - R3 or higher risk tier
    - broad or empty path scope

    Note: ``work_item.forbidden_operations`` is a deny-list (operations the
    Work Item declares as not allowed). Listing ``push_main`` or ``merge``
    there is correct and expected — it is not a grant. Use
    ``validate_publication_operation`` to reject an operation when it is
    actually attempted.
    """

    # R3+ is never authorized by this platform.
    if work_item.risk_tier not in ("R0", "R1", "R2"):
        raise PolicyViolation("risk_tier_exceeds_R2", work_item.risk_tier)

    # R2 requires explicit path binding; broad/empty is rejected in __post_init__.
    # Re-check here for defense in depth.
    if not work_item.allowed_paths:
        raise PolicyViolation("empty_path_scope")

    for path in work_item.allowed_paths:
        if path in ("**", "*", ".", "./", "/", "", "./**", "*.*"):
            raise PolicyViolation("broad_path_rejected", path)


def validate_binding(binding: ExecutionBinding) -> None:
    """Validate an execution binding, including retry limits."""

    validate_work_item(binding.work_item)
    if binding.attempt < 1:
        raise PolicyViolation("invalid_attempt", str(binding.attempt))
    from .contracts import MAX_ATTEMPTS
    if binding.attempt > MAX_ATTEMPTS:
        raise PolicyViolation("max_attempts_exceeded", f"{binding.attempt}/{MAX_ATTEMPTS}")


def validate_changed_paths(
    changed_paths: tuple[str, ...],
    allowed_paths: tuple[str, ...],
) -> tuple[str, ...]:
    """Return paths that are outside the allowed scope, or raise if broad."""

    if not changed_paths:
        return ()
    outside = _paths_outside_scope(changed_paths, allowed_paths)
    return outside


def validate_publication_operation(operation: str) -> None:
    """Reject forbidden publication operations."""

    if operation in FORBIDDEN_PUBLICATION_OPERATIONS:
        raise PolicyViolation("forbidden_publication_operation", operation)


def generate_task_prompt(work_item: PlatformWorkItem) -> str:
    """Generate a bounded OpenHands/Codex task prompt from the Work Item.

    The prompt is fully derived from the approved Work Item — it does not
    inject credentials, does not broaden the scope, and explicitly lists
    forbidden operations.
    """

    return (
        f"# Bounded execution task\n\n"
        f"execution_id: {work_item.execution_id}\n"
        f"branch: {work_item.branch_name}\n"
        f"base_sha: {work_item.base_sha}\n"
        f"repository: {work_item.repository}\n\n"
        f"## Allowed paths\n"
        + "\n".join(f"- {p}" for p in work_item.allowed_paths)
        + "\n\n"
        f"## Forbidden operations\n"
        + "\n".join(f"- {op}" for op in work_item.forbidden_operations)
        + "\n\n"
        f"## Acceptance criteria\n"
        + "\n".join(f"- {c}" for c in work_item.acceptance_criteria)
        + "\n\n"
        f"## Constraints\n"
        f"- Modify only the allowed paths listed above.\n"
        f"- Do not push to main, mark ready, merge, release, or deploy.\n"
        f"- Do not access secrets or credentials.\n"
        f"- Do not commit credentials, tokens, or environment files.\n"
        f"- Your completion claim does not override Git or test results.\n"
    )
