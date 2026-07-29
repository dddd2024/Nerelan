"""Immutable public contracts for the v0 unattended baseline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_RISK_TIERS = frozenset({"R0", "R1", "R2", "R3"})
_ACCEPTANCE_STATUSES = frozenset(
    {
        "ACCEPTED",
        "REWORK_REQUIRED",
        "BLOCKED_APPROVAL",
        "FAILED_TERMINAL",
        "CANCELLED",
    }
)


def _text(value: object, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"invalid_{field}")
    return value


def _strings(values: object, field: str, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{field}_must_be_tuple")
    if required and not values:
        raise ValueError(f"empty_{field}")
    for value in values:
        _text(value, field)
    return values


def _attempt(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 2:
        raise ValueError("invalid_attempt")
    return value


def _sha(value: object, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or _SHA40.fullmatch(value) is None:
        raise ValueError(f"invalid_{field}")
    return value


@dataclass(frozen=True, slots=True)
class MinimalWorkItem:
    schema_version: int
    work_item_id: str
    source_issue: int
    repository: str
    base_sha: str
    goal: str
    acceptance_criteria: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    required_checks: tuple[str, ...]
    risk_tier: str
    max_attempts: int

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported_schema_version")
        _text(self.work_item_id, "work_item_id")
        if (
            isinstance(self.source_issue, bool)
            or not isinstance(self.source_issue, int)
            or self.source_issue <= 0
        ):
            raise ValueError("invalid_source_issue")
        repository = _text(self.repository, "repository")
        if repository is None or repository.count("/") != 1:
            raise ValueError("invalid_repository")
        _sha(self.base_sha, "base_sha")
        _text(self.goal, "goal")
        _strings(self.acceptance_criteria, "acceptance_criteria", required=True)
        _strings(self.allowed_paths, "allowed_paths", required=True)
        _strings(self.forbidden_operations, "forbidden_operations")
        _strings(self.required_checks, "required_checks", required=True)
        if self.risk_tier not in _RISK_TIERS:
            raise ValueError("invalid_risk_tier")
        _attempt(self.max_attempts)


@dataclass(frozen=True, slots=True)
class ResolvedExecutionPolicy:
    unattended_allowed: bool
    allowed_paths: tuple[str, ...]
    allowed_operations: tuple[str, ...]
    network_mode: str
    max_attempts: int
    draft_pr_allowed: bool
    auto_merge_allowed: bool
    approval_required: bool
    blocking_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in (
            "unattended_allowed",
            "draft_pr_allowed",
            "auto_merge_allowed",
            "approval_required",
        ):
            if not isinstance(getattr(self, field), bool):
                raise ValueError(f"invalid_{field}")
        _strings(self.allowed_paths, "allowed_paths", required=True)
        _strings(self.allowed_operations, "allowed_operations")
        if self.network_mode not in {"none", "bounded"}:
            raise ValueError("invalid_network_mode")
        _attempt(self.max_attempts)
        _strings(self.blocking_reasons, "blocking_reasons")
        if self.auto_merge_allowed:
            raise ValueError("auto_merge_forbidden")
        if self.unattended_allowed and (
            self.approval_required or self.blocking_reasons
        ):
            raise ValueError("unattended_policy_inconsistent")
        if self.draft_pr_allowed and self.network_mode != "bounded":
            raise ValueError("draft_pr_requires_bounded_network")


@dataclass(frozen=True, slots=True)
class ExecutionHandle:
    workflow_id: str
    attempt: int
    workspace_id: str
    executor_id: str
    started_at: str

    def __post_init__(self) -> None:
        from .identifiers import executor_id, workspace_id

        _text(self.workflow_id, "workflow_id")
        _attempt(self.attempt)
        if self.workspace_id != workspace_id(self.workflow_id):
            raise ValueError("workspace_id_mismatch")
        if self.executor_id != executor_id(self.workflow_id, self.attempt):
            raise ValueError("executor_id_mismatch")
        started = _text(self.started_at, "started_at")
        try:
            parsed = datetime.fromisoformat(started.replace("Z", "+00:00"))  # type: ignore[union-attr]
        except ValueError as error:
            raise ValueError("invalid_started_at") from error
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("started_at_timezone_required")


@dataclass(frozen=True, slots=True)
class TaskSubmission:
    verdict: str
    summary: str
    changed_paths: tuple[str, ...]
    commands_executed: tuple[str, ...]
    test_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    failure_reason: str | None

    def __post_init__(self) -> None:
        _text(self.verdict, "verdict")
        _text(self.summary, "summary")
        _strings(self.changed_paths, "changed_paths")
        _strings(self.commands_executed, "commands_executed")
        _strings(self.test_evidence, "test_evidence")
        _strings(self.limitations, "limitations")
        _text(self.failure_reason, "failure_reason", optional=True)


@dataclass(frozen=True, slots=True)
class AcceptanceResult:
    status: str
    attempt: int
    policy_passed: bool
    path_scope_passed: bool
    required_checks_passed: bool
    exact_head_sha: str | None
    pr_number: int | None
    rework_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in _ACCEPTANCE_STATUSES:
            raise ValueError("invalid_acceptance_status")
        _attempt(self.attempt)
        for field in (
            "policy_passed",
            "path_scope_passed",
            "required_checks_passed",
        ):
            if not isinstance(getattr(self, field), bool):
                raise ValueError(f"invalid_{field}")
        _sha(self.exact_head_sha, "exact_head_sha", optional=True)
        if self.pr_number is not None and (
            isinstance(self.pr_number, bool)
            or not isinstance(self.pr_number, int)
            or self.pr_number <= 0
        ):
            raise ValueError("invalid_pr_number")
        _strings(self.rework_reasons, "rework_reasons")

        all_checks_passed = (
            self.policy_passed
            and self.path_scope_passed
            and self.required_checks_passed
        )
        complete_acceptance_claim = (
            all_checks_passed
            and self.exact_head_sha is not None
            and self.pr_number is not None
        )
        if self.status == "ACCEPTED":
            if (
                not complete_acceptance_claim
                or self.rework_reasons
            ):
                raise ValueError("accepted_invariant_violation")
            return
        if self.status == "REWORK_REQUIRED" and not self.rework_reasons:
            raise ValueError("rework_reason_required")
        if complete_acceptance_claim:
            raise ValueError("nonaccepted_status_claims_acceptance")


@dataclass(frozen=True, slots=True)
class FailureEnvelope:
    failure_type: str
    retryable: bool
    workflow_id: str
    activity: str
    attempt: int
    reason: str
    sanitized_evidence_ref: str | None

    def __post_init__(self) -> None:
        _text(self.failure_type, "failure_type")
        if not isinstance(self.retryable, bool):
            raise ValueError("invalid_retryable")
        _text(self.workflow_id, "workflow_id")
        _text(self.activity, "activity")
        _attempt(self.attempt)
        _text(self.reason, "reason")
        _text(
            self.sanitized_evidence_ref,
            "sanitized_evidence_ref",
            optional=True,
        )
