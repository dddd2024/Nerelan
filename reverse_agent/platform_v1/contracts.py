"""Core contracts for the Platform V1 thin adapter.

All data structures are immutable and deterministic. A Work Item's identity
(execution_id, branch_name, pr_marker) is derived from its canonical digest,
which covers every materially meaningful field. A material change to goal,
allowed_paths, acceptance_criteria, required_checks, risk_tier, target_branch,
or the approved Issue body digest changes the digest, execution_id, and
pr_marker — preventing identity collision with stale execution state.
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

# Module-private sentinel required to construct live evidence.
# Only evidence_adapter._create_trusted_evidence() may import and use this.
_LIVE_FACTORY_TOKEN = object()

VALID_ACCEPTANCE_STATUSES = frozenset({
    "ACCEPTED",
    "FIXTURE_VALIDATED",
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

# Risk tiers that may proceed through unattended execution.
UNATTENDED_ALLOWED_TIERS = frozenset({"R0", "R1"})

# All recognized risk tiers.
VALID_RISK_TIERS = frozenset({"R0", "R1", "R2", "R3"})

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

# Git commit SHAs are SHA-1 (40 hex chars).
_SHA1_HEX_RE = re.compile(r"^[0-9a-f]{40}$")
# SHA-256 digests are 64 hex chars (e.g. approved Issue body digest, Work Item digest).
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

# CI workflow statuses that are NOT successful.
_FAILED_CI_STATUSES = frozenset({
    "PENDING",
    "SKIPPED",
    "CANCELLED",
    "UNKNOWN",
    "FAILURE",
    "TIMED_OUT",
    "ACTION_REQUIRED",
    "STALE",
    "NEUTRAL",
})


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
        if stripped in _BROAD_PATH_PATTERNS:
            raise ValueError(f"broad_path_rejected:{raw}")
        cleaned = stripped.replace("\\", "/").lstrip("./")
        if not cleaned:
            continue
        if cleaned in _BROAD_PATH_PATTERNS:
            raise ValueError(f"broad_path_rejected:{raw}")
        normalized.append(cleaned)
    return tuple(dict.fromkeys(normalized))


def _normalize_operations(operations: Sequence[str]) -> tuple[str, ...]:
    """Normalize an operation list, returning an immutable tuple."""

    normalized = tuple(
        str(op).strip() for op in operations
        if isinstance(op, str) and op.strip()
    )
    return tuple(dict.fromkeys(normalized))


def _normalize_strings(items: Sequence[str]) -> tuple[str, ...]:
    """Normalize a string list, returning an immutable tuple."""

    normalized = tuple(
        str(item).strip() for item in items
        if isinstance(item, str) and item.strip()
    )
    return tuple(dict.fromkeys(normalized))


def _compute_digest(payload: dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 digest over a normalized JSON payload."""

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class EvidenceBindingError(Exception):
    """Raised when trusted evidence binding validation fails.

    The message is a stable, machine-readable error code so callers can map
    it to a documented nonzero exit code.
    """

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


# ---------------------------------------------------------------------------
# Core contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlatformWorkItem:
    """An approved Work Item normalized from a GitHub Issue.

    The ``execution_id``, ``pr_marker`` are derived from the canonical digest
    which covers every materially meaningful field. Two events for the same
    Work Item produce the same identity — duplicate events never create a
    second execution, branch, or Draft PR. A material change to any
    meaningful field changes the digest and identity, preventing collision
    with stale execution state.
    """

    source_issue_number: int
    repository: str
    base_sha: str
    allowed_paths: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    goal: str
    required_checks: tuple[str, ...]
    approved_issue_body_digest: str
    risk_tier: str = "R2"
    target_branch: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.source_issue_number, int) or self.source_issue_number <= 0:
            raise ValueError("source_issue_number_must_be_positive_int")
        if not isinstance(self.repository, str) or "/" not in self.repository:
            raise ValueError(f"invalid_repository:{self.repository}")
        if not isinstance(self.base_sha, str) or not _SHA1_HEX_RE.match(self.base_sha):
            raise ValueError(f"invalid_base_sha:{self.base_sha}")
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("goal_must_be_non_empty_string")
        if not isinstance(self.approved_issue_body_digest, str) or not _SHA256_HEX_RE.match(self.approved_issue_body_digest):
            raise ValueError(f"invalid_approved_issue_body_digest:{self.approved_issue_body_digest}")
        if self.risk_tier not in VALID_RISK_TIERS:
            raise ValueError(f"invalid_risk_tier:{self.risk_tier}")
        object.__setattr__(self, "allowed_paths", _normalize_paths(self.allowed_paths))
        if not self.allowed_paths:
            raise ValueError("empty_path_scope_rejected")
        object.__setattr__(self, "forbidden_operations", _normalize_operations(self.forbidden_operations))
        object.__setattr__(self, "acceptance_criteria", _normalize_strings(self.acceptance_criteria))
        object.__setattr__(self, "required_checks", _normalize_strings(self.required_checks))
        if not self.required_checks:
            raise ValueError("required_checks_must_not_be_empty")
        if not self.target_branch:
            object.__setattr__(self, "target_branch", self.branch_name)

    @property
    def digest(self) -> str:
        """SHA-256 digest of the canonical Work Item payload."""

        return _compute_digest(self.to_digest_payload())

    @property
    def execution_id(self) -> str:
        """Deterministic execution identity derived from the full digest."""

        return f"exec-issue-{self.source_issue_number}-{self.digest[:12]}"

    @property
    def branch_name(self) -> str:
        """Deterministic branch name derived from the Work Item."""

        return self.target_branch or f"agent/work-item-{self.source_issue_number}"

    @property
    def pr_marker(self) -> str:
        """Deterministic PR marker for idempotent Draft PR creation."""

        return f"pr-marker-issue-{self.source_issue_number}-{self.digest[:12]}"

    def to_digest_payload(self) -> dict[str, Any]:
        """Return the canonical payload used for digest computation.

        Covers every materially meaningful field: goal, allowed_paths,
        acceptance_criteria, required_checks, risk_tier, target_branch,
        and the approved Issue body digest, plus the source issue number,
        repository, and base_sha that bind the Work Item to its authority.
        """

        return {
            "source_issue_number": self.source_issue_number,
            "repository": self.repository,
            "base_sha": self.base_sha,
            "goal": self.goal,
            "allowed_paths": list(self.allowed_paths),
            "forbidden_operations": list(self.forbidden_operations),
            "acceptance_criteria": list(self.acceptance_criteria),
            "required_checks": list(self.required_checks),
            "risk_tier": self.risk_tier,
            "target_branch": self.target_branch,
            "approved_issue_body_digest": self.approved_issue_body_digest,
        }

    def required_checks_as_workflows(self) -> tuple[str, ...]:
        """Return required_checks as the canonical workflow name set.

        F12: Required workflows come from the approved Work Item, not from
        evidence. This method exposes ``required_checks`` as the workflow
        name tuple used by the live acceptance path.
        """

        return self.required_checks

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
            goal=str(data.get("goal", "")),
            required_checks=tuple(data.get("required_checks", ())),
            approved_issue_body_digest=str(data.get("approved_issue_body_digest", "")),
            risk_tier=str(data.get("risk_tier", "R2")),
            target_branch=str(data.get("target_branch", "")),
        )


@dataclass(frozen=True)
class ExecutionBinding:
    """Binds a Work Item to one execution attempt.

    ``attempt`` starts at 1. A bounded retry increments to 2. Attempt 3 is
    rejected by the policy adapter before any execution begins.

    ``expected_head_sha`` and ``expected_pr_number`` optionally bind the
    execution to a specific PR head and PR number. When set, the acceptance
    evaluator rejects evidence whose ``head_sha`` or ``pr_number`` does not
    match.
    """

    work_item: PlatformWorkItem
    attempt: int = 1
    expected_head_sha: str = ""
    expected_pr_number: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.attempt, int) or self.attempt < 1:
            raise ValueError(f"invalid_attempt:{self.attempt}")
        if self.attempt > MAX_ATTEMPTS:
            raise ValueError(f"max_attempts_exceeded:{self.attempt}/{MAX_ATTEMPTS}")

    @property
    def execution_id(self) -> str:
        return self.work_item.execution_id

    @property
    def branch_name(self) -> str:
        return self.work_item.branch_name

    @property
    def pr_marker(self) -> str:
        return self.work_item.pr_marker

    @property
    def is_retry(self) -> bool:
        return self.attempt > 1

    def next_attempt(self) -> ExecutionBinding:
        """Return a binding for the next attempt, or raise if exhausted."""

        if self.attempt >= MAX_ATTEMPTS:
            raise ValueError("retry_limit_exceeded")
        return ExecutionBinding(
            work_item=self.work_item,
            attempt=self.attempt + 1,
            expected_head_sha=self.expected_head_sha,
            expected_pr_number=self.expected_pr_number,
        )


@dataclass(frozen=True)
class ExecutionEvidence:
    """Trusted evidence collected from Git/GitHub state — never from agent claims.

    Binds execution_id, repository, base_sha, head_sha, pr_number,
    required_workflows, changed_paths, test_results, git_diff_check,
    ci_checks, collection_mode, and provenance. The
    ``agent_completion_claim`` is recorded but never used to override Git
    or test failures.

    F9: ``collection_mode`` and ``provenance`` can only be set to live/trusted
    by the internal trusted collector factory (:meth:`create_live`). The
    public :meth:`from_mapping` constructor always forces fixture/caller_asserted
    regardless of what the caller supplies — a caller-asserted
    ``collection_mode=live`` or trusted provenance can never become live evidence.

    ``collection_mode`` is ``"live"`` when evidence comes from real Git/GitHub
    observation by the trusted collector, or ``"fixture"`` when evidence is
    supplied from a test fixture or caller JSON. Fixture evidence can never
    produce a live merge-ready result.

    ``provenance`` records the source of the evidence (e.g.,
    ``"trusted_git_github_collector"``, ``"caller_asserted"``).
    """

    execution_id: str
    repository: str
    base_sha: str
    head_sha: str
    pr_number: int
    required_workflows: tuple[str, ...]
    changed_paths: tuple[str, ...] = ()
    test_results: dict[str, Any] = field(default_factory=dict)
    git_diff_check_passed: bool = False
    agent_completion_claim: str = ""
    ci_checks: tuple[dict[str, Any], ...] = ()
    collected_at: str = ""
    collection_mode: str = "fixture"
    provenance: str = "caller_asserted"
    _factory_token: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise ValueError("execution_id_must_be_non_empty_string")
        if not isinstance(self.repository, str) or "/" not in self.repository:
            raise ValueError(f"invalid_repository:{self.repository}")
        if not isinstance(self.base_sha, str) or not _SHA1_HEX_RE.match(self.base_sha):
            raise ValueError(f"invalid_base_sha:{self.base_sha}")
        if not isinstance(self.head_sha, str) or not _SHA1_HEX_RE.match(self.head_sha):
            raise ValueError(f"invalid_head_sha:{self.head_sha}")
        if not isinstance(self.pr_number, int) or self.pr_number <= 0:
            raise ValueError(f"invalid_pr_number:{self.pr_number}")
        if not isinstance(self.test_results, dict):
            raise ValueError("test_results_must_be_dict")
        object.__setattr__(self, "changed_paths", _normalize_paths(self.changed_paths))
        object.__setattr__(self, "required_workflows", _normalize_strings(self.required_workflows))
        if not isinstance(self.ci_checks, tuple):
            object.__setattr__(self, "ci_checks", tuple(self.ci_checks))
        if self.collection_mode not in ("live", "fixture"):
            raise ValueError(f"invalid_collection_mode:{self.collection_mode}")
        # F27: live mode requires the module-private trusted factory token.
        # This prevents external callers from constructing acceptance-grade
        # live evidence directly. Only evidence_adapter._create_trusted_evidence
        # imports _LIVE_FACTORY_TOKEN and passes it.
        if self.collection_mode == "live" and self._factory_token is not _LIVE_FACTORY_TOKEN:
            raise ValueError("live_mode_requires_trusted_factory")

    @property
    def tests_passed(self) -> bool:
        """True only when test_results explicitly reports success."""

        return bool(self.test_results.get("passed", False))

    @property
    def ci_passed(self) -> bool:
        """True only when all required workflows report SUCCESS on the exact head.

        F12: The observed workflow set must match the required set exactly —
        no subset, no superset. Fail-closed for: missing required workflows,
        duplicate authoritative workflows, extra unexpected workflows, and
        any non-SUCCESS status (PENDING, SKIPPED, CANCELLED, UNKNOWN, FAILURE,
        TIMED_OUT, ACTION_REQUIRED, STALE, NEUTRAL).

        F24: A completed run with empty conclusion never passes. Both
        ``status=completed`` AND ``conclusion=success`` are required.
        """

        if not self.ci_checks or not self.required_workflows:
            return False
        # Check for duplicate workflow names
        names = [check.get("name", "") for check in self.ci_checks]
        seen: set[str] = set()
        for name in names:
            if name in seen:
                return False  # duplicate authoritative workflow
            seen.add(name)
        # F12: observed set must match required set exactly (no subset)
        observed_set = set(names)
        required_set = set(self.required_workflows)
        if observed_set != required_set:
            return False  # subset or superset rejected
        # Check all required workflows are present and SUCCESS
        checks_by_name = {check.get("name", ""): check for check in self.ci_checks}
        for required in self.required_workflows:
            if required not in checks_by_name:
                return False  # missing required workflow
            check = checks_by_name[required]
            conclusion = str(check.get("conclusion", "")).upper()
            status = str(check.get("status", "")).upper()
            # F24: strict success — both status=completed AND conclusion=success
            if status != "COMPLETED" or conclusion != "SUCCESS":
                return False
        return True

    @property
    def is_live(self) -> bool:
        """True only when evidence comes from live Git/GitHub observation.

        F9: This can only be True when the evidence was constructed by the
        internal trusted collector factory (:meth:`create_live`). The public
        :meth:`from_mapping` constructor always forces fixture mode.
        """

        return self.collection_mode == "live"

    @property
    def live_ready(self) -> bool:
        """True only when this evidence is live (not fixture).

        F9: Fixture evidence is never live_ready, regardless of what the
        caller asserted.
        """

        return self.is_live

    def validate_binding(self, work_item: PlatformWorkItem) -> None:
        """Validate that this evidence binds to the given Work Item.

        Raises ``EvidenceBindingError`` on any mismatch:
        - execution_id mismatch
        - repository mismatch
        - base_sha mismatch
        """

        if self.execution_id != work_item.execution_id:
            raise EvidenceBindingError(
                "execution_id_mismatch",
                f"evidence={self.execution_id} work_item={work_item.execution_id}",
            )
        if self.repository != work_item.repository:
            raise EvidenceBindingError(
                "repository_mismatch",
                f"evidence={self.repository} work_item={work_item.repository}",
            )
        if self.base_sha != work_item.base_sha:
            raise EvidenceBindingError(
                "base_sha_mismatch",
                f"evidence={self.base_sha} work_item={work_item.base_sha}",
            )

    def validate_exact_binding(
        self,
        work_item: PlatformWorkItem,
        *,
        expected_head_sha: str,
        expected_pr_number: int,
        expected_branch: str,
        authority_digest: str,
    ) -> None:
        """Validate exact binding for the live path (F11).

        All parameters are mandatory — no optional defaults. Raises
        ``EvidenceBindingError`` on any mismatch.
        """

        self.validate_binding(work_item)
        if not expected_head_sha or not _SHA1_HEX_RE.match(expected_head_sha):
            raise EvidenceBindingError("invalid_expected_head_sha", expected_head_sha)
        if self.head_sha != expected_head_sha:
            raise EvidenceBindingError(
                "head_sha_mismatch",
                f"evidence={self.head_sha} expected={expected_head_sha}",
            )
        if not isinstance(expected_pr_number, int) or expected_pr_number <= 0:
            raise EvidenceBindingError("invalid_expected_pr_number", str(expected_pr_number))
        if self.pr_number != expected_pr_number:
            raise EvidenceBindingError(
                "pr_number_mismatch",
                f"evidence={self.pr_number} expected={expected_pr_number}",
            )
        if not expected_branch:
            raise EvidenceBindingError("empty_expected_branch", "")
        if work_item.target_branch != expected_branch:
            raise EvidenceBindingError(
                "branch_mismatch",
                f"work_item={work_item.target_branch} expected={expected_branch}",
            )
        if not authority_digest or not _SHA256_HEX_RE.match(authority_digest):
            raise EvidenceBindingError("invalid_authority_digest", authority_digest)
        if work_item.digest != authority_digest:
            raise EvidenceBindingError(
                "authority_digest_mismatch",
                f"work_item={work_item.digest} expected={authority_digest}",
            )

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ExecutionEvidence:
        """Build evidence from a dict (e.g. parsed from stdin JSON).

        F9: Caller-supplied ``collection_mode`` and ``provenance`` are always
        ignored — the result is always ``collection_mode=fixture`` and
        ``provenance=caller_asserted``. Only the internal :meth:`create_live`
        factory can produce live evidence.
        """

        return cls(
            execution_id=str(data["execution_id"]),
            repository=str(data.get("repository", "")),
            base_sha=str(data.get("base_sha", "")),
            head_sha=str(data.get("head_sha", "")),
            pr_number=int(data.get("pr_number", 0)),
            required_workflows=tuple(data.get("required_workflows", ())),
            changed_paths=tuple(data.get("changed_paths", ())),
            test_results=dict(data.get("test_results", {})),
            git_diff_check_passed=bool(data.get("git_diff_check_passed", False)),
            agent_completion_claim=str(data.get("agent_completion_claim", "")),
            ci_checks=tuple(data.get("ci_checks", ())),
            collected_at=str(data.get("collected_at", "")),
            # F9: always fixture — ignore caller-supplied labels
            collection_mode="fixture",
            provenance="caller_asserted",
        )

    @classmethod
    def create_live(
        cls,
        *,
        execution_id: str,
        repository: str,
        base_sha: str,
        head_sha: str,
        pr_number: int,
        required_workflows: tuple[str, ...],
        changed_paths: tuple[str, ...] = (),
        test_results: dict[str, Any] | None = None,
        git_diff_check_passed: bool = False,
        agent_completion_claim: str = "",
        ci_checks: tuple[dict[str, Any], ...] = (),
        collected_at: str = "",
    ) -> ExecutionEvidence:
        """DEPRECATED: use ``evidence_adapter._create_trusted_evidence``.

        F27: This public factory can no longer produce acceptance-grade live
        evidence. It returns fixture evidence (``collection_mode=fixture``,
        ``provenance=caller_asserted``) regardless of caller intent. Only
        ``evidence_adapter._create_trusted_evidence`` imports the module-private
        ``_LIVE_FACTORY_TOKEN`` and can construct live evidence.
        """

        return cls(
            execution_id=execution_id,
            repository=repository,
            base_sha=base_sha,
            head_sha=head_sha,
            pr_number=pr_number,
            required_workflows=required_workflows,
            changed_paths=changed_paths,
            test_results=test_results or {},
            git_diff_check_passed=git_diff_check_passed,
            agent_completion_claim=agent_completion_claim,
            ci_checks=ci_checks,
            collected_at=collected_at,
            # F27: always fixture — public factory cannot produce live evidence
            collection_mode="fixture",
            provenance="caller_asserted",
        )


@dataclass(frozen=True)
class PlatformAcceptanceResult:
    """Final acceptance decision — never derived from the agent's claim.

    Status must be one of ``VALID_ACCEPTANCE_STATUSES``. ``reasons`` explains
    the decision. ``evidence`` is the evidence the decision was based on.
    ``live_ready`` is True only when the result is ACCEPTED with live-mode
    evidence. Fixture evidence that passes all checks returns
    ``FIXTURE_VALIDATED`` — never ``ACCEPTED`` or ``live_ready: True``.
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
        """True only for live ACCEPTED — never for FIXTURE_VALIDATED."""

        return self.status == "ACCEPTED"

    @property
    def live_ready(self) -> bool:
        """True only when ACCEPTED with live-mode evidence.

        F9: FIXTURE_VALIDATED is never live_ready, even if all checks pass.
        """

        return self.accepted and self.evidence is not None and self.evidence.is_live

    def to_mapping(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "reasons": list(self.reasons),
            "live_ready": self.live_ready,
            "evidence": {
                "changed_paths": list(self.evidence.changed_paths) if self.evidence else [],
                "tests_passed": self.evidence.tests_passed if self.evidence else False,
                "git_diff_check_passed": self.evidence.git_diff_check_passed if self.evidence else False,
                "ci_passed": self.evidence.ci_passed if self.evidence else False,
                "agent_completion_claim": self.evidence.agent_completion_claim if self.evidence else "",
                "collection_mode": self.evidence.collection_mode if self.evidence else "",
                "provenance": self.evidence.provenance if self.evidence else "",
            } if self.evidence else None,
        }
