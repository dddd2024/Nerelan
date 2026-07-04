from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .fallback_ladder import FallbackDecision
from .user_solve_contract import (
    EvidenceStatus,
    UserSolveResult,
    UserSolveStatus,
    ValidationStatus,
    contains_internal_reference,
    redact_internal_references,
)
from .user_solve_trace import UserSolveTaskTrace


@dataclass(frozen=True)
class SessionNextAction:
    kind: str
    label: str
    safe_to_show: bool = True
    developer_trace_ref: str = ""

    def __post_init__(self) -> None:
        if not str(self.kind or "").strip():
            raise ValueError("next action kind must be non-empty")
        if not str(self.label or "").strip():
            raise ValueError("next action label must be non-empty")

    def to_user_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "kind": self.kind,
                "label": self.label,
                "safe_to_show": self.safe_to_show,
            }
        )

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_trace_ref"] = self.developer_trace_ref
        return payload


@dataclass(frozen=True)
class UserSolveSessionBundle:
    session_id: str
    result: UserSolveResult
    trace: UserSolveTaskTrace
    fallback_decision: FallbackDecision
    validation_status: ValidationStatus
    evidence_status: EvidenceStatus
    missing_evidence_summary: list[str] = field(default_factory=list)
    public_message: str = ""
    next_action: SessionNextAction | dict[str, Any] | None = None
    developer_trace_refs: list[str] = field(default_factory=list)
    artifact_references: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not str(self.session_id or "").strip():
            raise ValueError("session_id must be non-empty")
        result = self.result if isinstance(self.result, UserSolveResult) else UserSolveResult.from_mapping(self.result)
        object.__setattr__(self, "result", result)
        trace = self.trace if isinstance(self.trace, UserSolveTaskTrace) else UserSolveTaskTrace(**self.trace)
        object.__setattr__(self, "trace", trace)
        object.__setattr__(self, "validation_status", ValidationStatus(self.validation_status))
        object.__setattr__(self, "evidence_status", EvidenceStatus(self.evidence_status))
        if self.next_action is None:
            next_action = infer_next_action(
                result=result,
                fallback_decision=self.fallback_decision,
                missing_evidence=self.missing_evidence_summary,
            )
        elif isinstance(self.next_action, SessionNextAction):
            next_action = self.next_action
        else:
            next_action = SessionNextAction(**self.next_action)
        object.__setattr__(self, "next_action", next_action)
        object.__setattr__(
            self,
            "missing_evidence_summary",
            [str(item) for item in self.missing_evidence_summary if str(item).strip()],
        )
        object.__setattr__(
            self,
            "developer_trace_refs",
            [str(item) for item in self.developer_trace_refs if str(item).strip()],
        )
        object.__setattr__(
            self,
            "artifact_references",
            [str(item) for item in self.artifact_references if str(item).strip()],
        )
        self.validate()

    def validate(self) -> None:
        if self.result.status == UserSolveStatus.VERIFIED and self.validation_status != ValidationStatus.PASSED:
            raise ValueError("verified session requires passed validation")
        if self.result.status != self.trace.user_status:
            raise ValueError("session result and trace user statuses must match")
        if self.result.validation_status != self.validation_status:
            raise ValueError("session validation_status must match result validation_status")
        if self.result.evidence_status != self.evidence_status:
            raise ValueError("session evidence_status must match result evidence_status")
        if self.result.status == UserSolveStatus.VERIFIED:
            if self.missing_evidence_summary:
                raise ValueError("verified session cannot carry unresolved missing evidence")
            if self.evidence_status != EvidenceStatus.COMPLETE:
                raise ValueError("verified session requires complete evidence")
        if self.fallback_decision.executed:
            raise ValueError("session fallback decision must be non-executing")

    def to_user_dict(self) -> dict[str, Any]:
        payload = {
            "session_id": self.session_id,
            "result": self.result.to_user_dict(),
            "trace_summary": self.trace.to_user_dict(),
            "fallback_decision": self.fallback_decision.to_user_dict(),
            "validation_status": self.validation_status.value,
            "evidence_status": self.evidence_status.value,
            "missing_evidence_summary": list(self.missing_evidence_summary),
            "public_message": self.public_message or self.result.message,
            "next_action": self.next_action.to_user_dict() if self.next_action else None,
        }
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["result"] = self.result.to_developer_dict()
        payload["trace"] = self.trace.to_developer_dict()
        payload["fallback_decision"] = self.fallback_decision.to_developer_dict()
        payload["next_action"] = self.next_action.to_developer_dict() if self.next_action else None
        payload["developer_trace_refs"] = list(self.developer_trace_refs)
        payload["artifact_references"] = list(self.artifact_references)
        return payload


def infer_next_action(
    *,
    result: UserSolveResult,
    fallback_decision: FallbackDecision,
    missing_evidence: Iterable[str] | None = None,
) -> SessionNextAction:
    if result.status == UserSolveStatus.VERIFIED:
        return SessionNextAction(kind="return_answer", label="Return the verified answer.")
    if result.status == UserSolveStatus.CANDIDATE_FOUND:
        return SessionNextAction(kind="validate_candidate", label="Validate the candidate before final acceptance.")
    if result.status == UserSolveStatus.BLOCKED:
        return SessionNextAction(kind="blocked", label="Resolve the blocking condition before continuing.")
    if fallback_decision.selected_step is not None:
        return SessionNextAction(
            kind="fallback",
            label=f"Collect more evidence with {fallback_decision.selected_step.name.value}.",
        )
    if list(missing_evidence or []):
        return SessionNextAction(kind="collect_evidence", label="Collect the missing evidence before final acceptance.")
    return SessionNextAction(kind="review", label="Review the supplied analysis result.")


def build_session_bundle(
    *,
    session_id: str,
    result: UserSolveResult,
    trace: UserSolveTaskTrace,
    fallback_decision: FallbackDecision,
    missing_evidence: Iterable[str] | None = None,
    public_message: str = "",
    developer_trace_refs: Iterable[str] | None = None,
    artifact_references: Iterable[str] | None = None,
) -> UserSolveSessionBundle:
    bundle = UserSolveSessionBundle(
        session_id=session_id,
        result=result,
        trace=trace,
        fallback_decision=fallback_decision,
        validation_status=result.validation_status,
        evidence_status=result.evidence_status,
        missing_evidence_summary=[str(item) for item in (missing_evidence or []) if str(item).strip()],
        public_message=public_message or result.message,
        developer_trace_refs=[str(item) for item in (developer_trace_refs or []) if str(item).strip()],
        artifact_references=[str(item) for item in (artifact_references or []) if str(item).strip()],
    )
    if contains_internal_reference(bundle.to_user_dict()):
        raise ValueError("session user serialization leaked an internal reference")
    return bundle
