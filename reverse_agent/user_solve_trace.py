from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .fallback_ladder import FallbackDecision, FallbackStepName
from .user_solve_contract import (
    UserSolveResult,
    UserSolveStatus,
    ValidationStatus,
    redact_internal_references,
)


@dataclass(frozen=True)
class CandidateSource:
    name: str
    source_type: str = "synthetic"
    confidence: float | None = None
    developer_trace_ref: str = ""

    def __post_init__(self) -> None:
        if not str(self.name or "").strip():
            raise ValueError("candidate source name must be non-empty")
        if self.confidence is not None:
            confidence = float(self.confidence)
            if confidence < 0.0 or confidence > 1.0:
                raise ValueError("candidate source confidence must be between 0.0 and 1.0")
            object.__setattr__(self, "confidence", confidence)

    def to_user_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "source_type": self.source_type,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_trace_ref"] = self.developer_trace_ref
        return payload


@dataclass(frozen=True)
class FallbackStepRecord:
    name: FallbackStepName | str
    status: str = "suggested"
    sequence: int = 0
    missing_evidence: list[str] = field(default_factory=list)
    executed: bool = False
    developer_trace_ref: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", FallbackStepName(self.name))
        if int(self.sequence) < 0:
            raise ValueError("fallback step sequence must be non-negative")
        object.__setattr__(self, "sequence", int(self.sequence))

    def to_user_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "name": self.name.value,
                "status": self.status,
                "sequence": self.sequence,
                "missing_evidence": list(self.missing_evidence),
                "executed": self.executed,
            }
        )

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_trace_ref"] = self.developer_trace_ref
        return payload


@dataclass(frozen=True)
class ValidationRecord:
    status: ValidationStatus
    result: str = ""
    validator: str = ""
    developer_trace_ref: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", ValidationStatus(self.status))

    def to_user_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "status": self.status.value,
                "result": self.result,
                "validator": self.validator,
            }
        )

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_trace_ref"] = self.developer_trace_ref
        return payload


@dataclass(frozen=True)
class ArtifactReference:
    label: str
    path: str
    public: bool = False

    def to_user_dict(self) -> dict[str, Any]:
        payload = {"label": self.label}
        if self.public:
            payload["path"] = self.path
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "path": self.path,
            "public": self.public,
        }


@dataclass(frozen=True)
class UserSolveTaskTrace:
    task_id: str
    user_status: UserSolveStatus
    engineering_status: str
    validation: ValidationRecord
    candidate_sources: list[CandidateSource] = field(default_factory=list)
    fallback_steps: list[FallbackStepRecord] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    artifact_references: list[ArtifactReference] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    sequence: int = 0
    developer_trace_ref: str = ""

    def __post_init__(self) -> None:
        if not str(self.task_id or "").strip():
            raise ValueError("task_id must be non-empty")
        object.__setattr__(self, "user_status", UserSolveStatus(self.user_status))
        validation = self.validation if isinstance(self.validation, ValidationRecord) else ValidationRecord(**self.validation)
        object.__setattr__(self, "validation", validation)
        object.__setattr__(
            self,
            "candidate_sources",
            [item if isinstance(item, CandidateSource) else CandidateSource(**item) for item in self.candidate_sources],
        )
        object.__setattr__(
            self,
            "fallback_steps",
            [item if isinstance(item, FallbackStepRecord) else FallbackStepRecord(**item) for item in self.fallback_steps],
        )
        object.__setattr__(
            self,
            "artifact_references",
            [item if isinstance(item, ArtifactReference) else ArtifactReference(**item) for item in self.artifact_references],
        )
        if int(self.sequence) < 0:
            raise ValueError("trace sequence must be non-negative")
        object.__setattr__(self, "sequence", int(self.sequence))
        self.validate()

    def validate(self) -> None:
        if self.user_status == UserSolveStatus.VERIFIED and self.validation.status != ValidationStatus.PASSED:
            raise ValueError("verified trace requires passed validation")
        sequences = [step.sequence for step in self.fallback_steps]
        if sequences != sorted(sequences):
            raise ValueError("fallback step records must be ordered by sequence")

    def to_user_dict(self) -> dict[str, Any]:
        payload = {
            "task_id": self.task_id,
            "user_status": self.user_status.value,
            "engineering_status": self.engineering_status,
            "validation": self.validation.to_user_dict(),
            "candidate_sources": [item.to_user_dict() for item in self.candidate_sources],
            "fallback_steps": [item.to_user_dict() for item in self.fallback_steps],
            "missing_evidence": list(self.missing_evidence),
            "artifact_references": [item.to_user_dict() for item in self.artifact_references if item.public],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sequence": self.sequence,
        }
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_trace_ref"] = self.developer_trace_ref
        payload["candidate_sources"] = [item.to_developer_dict() for item in self.candidate_sources]
        payload["fallback_steps"] = [item.to_developer_dict() for item in self.fallback_steps]
        payload["artifact_references"] = [item.to_developer_dict() for item in self.artifact_references]
        return payload

    @classmethod
    def from_result(
        cls,
        *,
        task_id: str,
        result: UserSolveResult,
        fallback_decision: FallbackDecision | None = None,
        missing_evidence: Iterable[str] | None = None,
        artifact_references: Iterable[ArtifactReference] | None = None,
        developer_trace_ref: str = "",
    ) -> "UserSolveTaskTrace":
        fallback_steps: list[FallbackStepRecord] = []
        if fallback_decision and fallback_decision.selected_step:
            fallback_steps.append(
                FallbackStepRecord(
                    name=fallback_decision.selected_step.name,
                    status="suggested",
                    sequence=1,
                    missing_evidence=list(fallback_decision.missing_evidence),
                    executed=fallback_decision.executed,
                )
            )
        sources = [
            CandidateSource(
                name="supplied_candidate",
                source_type="in_memory_result",
                confidence=result.confidence,
                developer_trace_ref=result.developer_trace_ref,
            )
            for _candidate in ([result.usable_answer] if result.usable_answer else [])
        ]
        gaps = list(missing_evidence or [])
        if fallback_decision:
            gaps.extend(fallback_decision.missing_evidence)
        return cls(
            task_id=task_id,
            user_status=result.status,
            engineering_status=result.evidence_status.value,
            validation=ValidationRecord(status=result.validation_status, result=result.message),
            candidate_sources=sources,
            fallback_steps=fallback_steps,
            missing_evidence=gaps,
            artifact_references=list(artifact_references or []),
            sequence=1,
            developer_trace_ref=developer_trace_ref or result.developer_trace_ref,
        )
