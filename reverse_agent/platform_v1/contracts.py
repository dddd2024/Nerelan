"""Core contracts for the Platform V1 thin adapter.

All data structures are immutable and deterministic. A Work Item's identity
(execution_id, branch_name, pr_marker) is derived from its source Issue and
base SHA, so duplicate events for the same Work Item produce the same identity
— they never create a second execution, branch, or Draft PR.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Sequence

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_ATTEMPTS = 2  # at most one bounded retry; the third attempt is rejected

VALID_ACCEPTANCE_STATUSES = frozenset({
    "ACCEPTED",
    "REWORK_REQUIRED",
    "BLOCKED_APPROVAL",
    "FAILED_TERMINAL",
})

FORBIDDEN_PUBLICATION_OPERATIONS = frozenset({
    "push_main",
    "mark_ready",
    "merge",
    "auto_merge",
    "release",
    "deployment",
    "secret_access",
    "force_push",
    "rebase",
    "squash",
    "tag_or_release",
})

# Path patterns that are too broad to authorize safely.
_BROAD_PATH_PATTERNS = frozenset({
    "**",
    "*",
    ".",
    "./",
    "/",
    "",
    "./**",
    "*.*",
})

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{40}$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_paths(paths: Sequence[str]) -> tuple[str, ...]:
    """Normalize and validate a path list, returning an immutable tuple."""

    normalized: list[str] = []
    for raw in paths:
        if not isinstance(raw, str):
            raise ValueError(f"path_must_be_string:{raw!r}")
        stripped = raw.strip()
        # Check the raw stripped value against broad patterns first, before
        # normalization strips leading "./". This ensures ".", "./", "/", ""
        # are reported as broad_path_rejected rather than empty_path_scope.
        if stripped in _BROAD_PATH_PATTERNS:
            raise ValueError(f"broad_path_rejected:{raw}")
        cleaned = stripped.replace("\\", "/").lstrip("./")
        if not cleaned:
            continue
        if cleaned in _BROAD_PATH_PATTERNS:
            raise ValueError(f"broad_path_rejected:{raw}")
        normalized.append(cleaned)
    return tuple(dict.fromkeys(normalized))  # de-duplicate, preserve order


def _normalize_operations(operations: Sequence[str]) -> tuple[str, ...]:
    """Normalize an operation list, returning an immutable tuple."""

    normalized = tuple(
        str(op).strip() for op in operations
        if isinstance(op, str) and op.strip()
    )
    return tuple(dict.fromkeys(normalized))


def _compute_digest(payload: dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 digest over a normalized JSON payload."""

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Core contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlatformWorkItem:
    """An approved Work Item normalized from a GitHub Issue.

    The ``execution_id``, ``branch_name``, and ``pr_marker`` are deterministic
    over the Issue number and base SHA. Two events for the same Issue+base
    produce the same identity — duplicate events never create a second
    execution, branch, or Draft PR.
    """

    source_issue_number: int
    repository: str  # e.g. "dddd2024/reverse-agent"
    base_sha: str
    allowed_paths: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    risk_tier: str = "R2"
    target_branch: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.source_issue_number, int) or self.source_issue_number <= 0:
            raise ValueError("source_issue_number_must_be_positive_int")
        if not isinstance(self.repository, str) or "/" not in self.repository:
            raise ValueError(f"invalid_repository:{self.repository}")
        if not isinstance(self.base_sha, str) or not _SHA256_HEX_RE.match(self.base_sha):
            raise ValueError(f"invalid_base_sha:{self.base_sha}")
        if self.risk_tier not in ("R0", "R1", "R2"):
            raise ValueError(f"risk_tier_R3_or_higher_rejected:{self.risk_tier}")
        # Path scope is validated and normalized.
        object.__setattr__(self, "allowed_paths", _normalize_paths(self.allowed_paths))
        if not self.allowed_paths:
            raise ValueError("empty_path_scope_rejected")
        object.__setattr__(self, "forbidden_operations", _normalize_operations(self.forbidden_operations))
        object.__setattr__(self, "acceptance_criteria", tuple(self.acceptance_criteria))
        if not self.target_branch:
            object.__setattr__(self, "target_branch", self.branch_name)

    @property
    def execution_id(self) -> str:
        """Deterministic execution identity."""

        return f"exec-issue-{self.source_issue_number}-{self.base_sha[:12]}"

    @property
    def branch_name(self) -> str:
        """Deterministic branch name derived from the Work Item."""

        return self.target_branch or f"agent/work-item-{self.source_issue_number}"

    @property
    def pr_marker(self) -> str:
        """Deterministic PR marker for idempotent Draft PR creation."""

        return f"pr-marker-issue-{self.source_issue_number}-{self.base_sha[:12]}"

    @property
    def digest(self) -> str:
        """SHA-256 digest of the normalized Work Item."""

        return _compute_digest(self.to_digest_payload())

    def to_digest_payload(self) -> dict[str, Any]:
        """Return the canonical payload used for digest computation."""

        return {
            "source_issue_number": self.source_issue_number,
            "repository": self.repository,
            "base_sha": self.base_sha,
            "allowed_paths": list(self.allowed_paths),
            "forbidden_operations": list(self.forbidden_operations),
            "acceptance_criteria": list(self.acceptance_criteria),
            "risk_tier": self.risk_tier,
        }

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> PlatformWorkItem:
        """Build a PlatformWorkItem from a dict (e.g. parsed from JSON)."""

        return cls(
            source_issue_number=int(data["source_issue_number"]),
            repository=str(data["repository"]),
            base_sha=str(data["base_sha"]),
            allowed_paths=tuple(data.get("allowed_paths", ())),
            forbidden_operations=tuple(data.get("forbidden_operations", ())),
            acceptance_criteria=tuple(data.get("acceptance_criteria", ())),
            risk_tier=str(data.get("risk_tier", "R2")),
            target_branch=str(data.get("target_branch", "")),
        )


@dataclass(frozen=True)
class ExecutionBinding:
    """Binds a Work Item to one execution attempt.

    ``attempt`` starts at 1. A bounded retry increments to 2. Attempt 3 is
    rejected by the policy adapter before any execution begins.
    """

    work_item: PlatformWorkItem
    attempt: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.attempt, int) or self.attempt < 1:
            raise ValueError(f"invalid_attempt:{self.attempt}")
        if self.attempt > MAX_ATTEMPTS:
            raise ValueError(f"max_attempts_exceeded:{self.attempt}/{MAX_ATTEMPTS}")

    @property
    def execution_id(self) -> str:
        """Same deterministic identity as the Work Item."""

        return self.work_item.execution_id

    @property
    def branch_name(self) -> str:
        """Same deterministic branch as the Work Item."""

        return self.work_item.branch_name

    @property
    def pr_marker(self) -> str:
        """Same deterministic PR marker as the Work Item."""

        return self.work_item.pr_marker

    @property
    def is_retry(self) -> bool:
        """True when this binding represents the bounded retry attempt."""

        return self.attempt > 1

    def next_attempt(self) -> ExecutionBinding:
        """Return a binding for the next attempt, or raise if exhausted."""

        if self.attempt >= MAX_ATTEMPTS:
            raise ValueError("retry_limit_exceeded")
        return ExecutionBinding(work_item=self.work_item, attempt=self.attempt + 1)


@dataclass(frozen=True)
class ExecutionEvidence:
    """Evidence collected from execution — never trusts the agent's claim.

    The ``agent_completion_claim`` is recorded but never used to override Git
    or test failures. Acceptance is derived from ``changed_paths``,
    ``test_results``, ``git_diff_check_passed``, and ``ci_checks``.
    """

    execution_id: str
    changed_paths: tuple[str, ...] = ()
    test_results: dict[str, Any] = field(default_factory=dict)
    git_diff_check_passed: bool = False
    agent_completion_claim: str = ""
    ci_checks: tuple[dict[str, Any], ...] = ()
    collected_at: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "changed_paths", _normalize_paths(self.changed_paths))
        if not isinstance(self.test_results, dict):
            raise ValueError("test_results_must_be_dict")
        if not isinstance(self.ci_checks, tuple):
            object.__setattr__(self, "ci_checks", tuple(self.ci_checks))

    @property
    def tests_passed(self) -> bool:
        """True only when test_results explicitly reports success."""

        return bool(self.test_results.get("passed", False))

    @property
    def ci_passed(self) -> bool:
        """True only when all CI checks report SUCCESS."""

        if not self.ci_checks:
            return False
        return all(
            check.get("conclusion") == "SUCCESS" or check.get("status") == "SUCCESS"
            for check in self.ci_checks
        )

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ExecutionEvidence:
        return cls(
            execution_id=str(data["execution_id"]),
            changed_paths=tuple(data.get("changed_paths", ())),
            test_results=dict(data.get("test_results", {})),
            git_diff_check_passed=bool(data.get("git_diff_check_passed", False)),
            agent_completion_claim=str(data.get("agent_completion_claim", "")),
            ci_checks=tuple(data.get("ci_checks", ())),
            collected_at=str(data.get("collected_at", "")),
        )


@dataclass(frozen=True)
class PlatformAcceptanceResult:
    """Final acceptance decision — never derived from the agent's claim.

    Status must be one of ``VALID_ACCEPTANCE_STATUSES``. ``reasons`` explains
    the decision. ``evidence`` is the evidence the decision was based on.
    """

    execution_id: str
    status: str
    reasons: tuple[str, ...] = ()
    evidence: ExecutionEvidence | None = None

    def __post_init__(self) -> None:
        if self.status not in VALID_ACCEPTANCE_STATUSES:
            raise ValueError(f"invalid_acceptance_status:{self.status}")
        object.__setattr__(self, "reasons", tuple(self.reasons))

    @property
    def accepted(self) -> bool:
        return self.status == "ACCEPTED"

    def to_mapping(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "reasons": list(self.reasons),
            "evidence": {
                "changed_paths": list(self.evidence.changed_paths) if self.evidence else [],
                "tests_passed": self.evidence.tests_passed if self.evidence else False,
                "git_diff_check_passed": self.evidence.git_diff_check_passed if self.evidence else False,
                "ci_passed": self.evidence.ci_passed if self.evidence else False,
                "agent_completion_claim": self.evidence.agent_completion_claim if self.evidence else "",
            } if self.evidence else None,
        }
