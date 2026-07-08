from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

CONTRACT_SCHEMA_VERSION = 1


class UserSolveStatus(StrEnum):
    UPLOADED = "uploaded"
    FAST_ANALYZING = "fast_analyzing"
    CANDIDATE_FOUND = "candidate_found"
    STATIC_VERIFIED = "static_verified"
    RUNTIME_VALIDATION_PENDING = "runtime_validation_pending"
    RUNTIME_VALIDATED = "runtime_validated"
    VALIDATING = "validating"
    VERIFIED = "verified"
    DEEP_ANALYSIS_RUNNING = "deep_analysis_running"
    FAILED = "failed"
    BLOCKED = "blocked"


class ValidationStatus(StrEnum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    CANDIDATE_ONLY = "candidate_only"
    STATIC_VERIFIED = "static_verified"
    RUNTIME_VALIDATED = "runtime_validated"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    UNAVAILABLE = "unavailable"


class EvidenceStatus(StrEnum):
    NONE = "none"
    PARTIAL = "partial"
    BUILDING = "building"
    COMPLETE = "complete"
    FAILED = "failed"


class UserSolveMode(StrEnum):
    FAST = "fast"
    DEEP = "deep"
    AUTO = "auto"


INTERNAL_REFERENCE_TOKENS = (
    "project_state/",
    "project_state\\",
    "decision_packet.md",
    "command_plan.json",
    "artifact_index.json",
    "negative_results.json",
    "codex_execution_report.md",
    "pytest_result.txt",
)


def _coerce_enum(enum_type: type[StrEnum], value: StrEnum | str, field_name: str) -> StrEnum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_type)
        raise ValueError(f"{field_name} must be one of: {allowed}") from exc


def redact_internal_references(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for token in INTERNAL_REFERENCE_TOKENS:
            redacted = redacted.replace(token, "[internal]")
        return redacted
    if isinstance(value, list):
        return [redact_internal_references(item) for item in value]
    if isinstance(value, tuple):
        return [redact_internal_references(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): redact_internal_references(item)
            for key, item in value.items()
        }
    return value


def contains_internal_reference(value: Any) -> bool:
    text = str(value)
    lowered = text.lower()
    return any(token.lower() in lowered for token in INTERNAL_REFERENCE_TOKENS)


@dataclass(frozen=True)
class UserSolveTask:
    task_id: str
    sample_label: str = ""
    mode: UserSolveMode = UserSolveMode.AUTO
    requested_validation: ValidationStatus = ValidationStatus.PENDING
    user_context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        task_id = str(self.task_id or "").strip()
        if not task_id:
            raise ValueError("task_id must be non-empty")
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "mode", _coerce_enum(UserSolveMode, self.mode, "mode"))
        object.__setattr__(
            self,
            "requested_validation",
            _coerce_enum(ValidationStatus, self.requested_validation, "requested_validation"),
        )
        if not isinstance(self.user_context, dict):
            raise ValueError("user_context must be a dict")

    def to_user_dict(self) -> dict[str, Any]:
        return redact_internal_references(
            {
                "task_id": self.task_id,
                "sample_label": self.sample_label,
                "mode": self.mode.value,
                "requested_validation": self.requested_validation.value,
                "user_context": dict(self.user_context),
            }
        )

    def to_developer_dict(self) -> dict[str, Any]:
        return self.to_user_dict()


@dataclass(frozen=True)
class UserSolveCandidate:
    value: str
    confidence: float | None = None
    label: str = ""
    validation_status: ValidationStatus = ValidationStatus.NOT_STARTED
    developer_trace_ref: str = ""

    def __post_init__(self) -> None:
        value = str(self.value or "").strip()
        if not value:
            raise ValueError("candidate value must be non-empty")
        object.__setattr__(self, "value", value)
        object.__setattr__(
            self,
            "validation_status",
            _coerce_enum(ValidationStatus, self.validation_status, "candidate.validation_status"),
        )
        if self.confidence is not None:
            confidence = float(self.confidence)
            if confidence < 0.0 or confidence > 1.0:
                raise ValueError("candidate confidence must be between 0.0 and 1.0")
            object.__setattr__(self, "confidence", confidence)

    def to_user_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "value": self.value,
            "validation_status": self.validation_status.value,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.label:
            payload["label"] = redact_internal_references(self.label)
        return payload

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        if self.developer_trace_ref:
            payload["developer_trace_ref"] = self.developer_trace_ref
        return payload


@dataclass(frozen=True)
class CandidateResult:
    value: str
    confidence: float | None = None
    label: str = ""
    validation_status: ValidationStatus = ValidationStatus.CANDIDATE_ONLY
    evidence_refs: list[str] = field(default_factory=list)
    developer_trace_ref: str = ""

    def __post_init__(self) -> None:
        value = str(self.value or "").strip()
        if not value:
            raise ValueError("candidate value must be non-empty")
        object.__setattr__(self, "value", value)
        object.__setattr__(
            self,
            "validation_status",
            _coerce_enum(ValidationStatus, self.validation_status, "candidate.validation_status"),
        )
        if self.confidence is not None:
            confidence = float(self.confidence)
            if confidence < 0.0 or confidence > 1.0:
                raise ValueError("candidate confidence must be between 0.0 and 1.0")
            object.__setattr__(self, "confidence", confidence)
        if self.validation_status == ValidationStatus.RUNTIME_VALIDATED:
            raise ValueError("CandidateResult must not imply runtime validation; use validation_status=runtime_validated only at UserSolveResult level with evidence")

    def to_user_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "value": self.value,
            "validation_status": self.validation_status.value,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.label:
            payload["label"] = redact_internal_references(self.label)
        return payload

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        if self.developer_trace_ref:
            payload["developer_trace_ref"] = self.developer_trace_ref
        if self.evidence_refs:
            payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True)
class UserSolveResult:
    status: UserSolveStatus
    validation_status: ValidationStatus = ValidationStatus.NOT_STARTED
    evidence_status: EvidenceStatus = EvidenceStatus.NONE
    mode: UserSolveMode = UserSolveMode.AUTO
    answer: str = ""
    candidates: list[UserSolveCandidate] = field(default_factory=list)
    confidence: float | None = None
    message: str = ""
    reason: str = ""
    developer_trace_ref: str = ""
    internal_references: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _coerce_enum(UserSolveStatus, self.status, "status"))
        object.__setattr__(
            self,
            "validation_status",
            _coerce_enum(ValidationStatus, self.validation_status, "validation_status"),
        )
        object.__setattr__(
            self,
            "evidence_status",
            _coerce_enum(EvidenceStatus, self.evidence_status, "evidence_status"),
        )
        object.__setattr__(self, "mode", _coerce_enum(UserSolveMode, self.mode, "mode"))
        candidates = [
            candidate if isinstance(candidate, UserSolveCandidate) else UserSolveCandidate(**candidate)
            for candidate in self.candidates
        ]
        object.__setattr__(self, "candidates", candidates)
        if self.confidence is not None:
            confidence = float(self.confidence)
            if confidence < 0.0 or confidence > 1.0:
                raise ValueError("confidence must be between 0.0 and 1.0")
            object.__setattr__(self, "confidence", confidence)
        self.validate()

    @property
    def usable_answer(self) -> str:
        return str(self.answer or "").strip() or (self.candidates[0].value if self.candidates else "")

    def validate(self) -> None:
        if self.status == UserSolveStatus.VERIFIED:
            if self.validation_status != ValidationStatus.PASSED:
                raise ValueError("verified requires validation_status=passed")
            if not self.usable_answer:
                raise ValueError("verified requires an answer or candidate")
        if self.status == UserSolveStatus.STATIC_VERIFIED:
            if self.validation_status == ValidationStatus.RUNTIME_VALIDATED:
                raise ValueError("static_verified must not have validation_status=runtime_validated")
            if self.validation_status not in (ValidationStatus.STATIC_VERIFIED, ValidationStatus.PASSED):
                raise ValueError("static_verified requires validation_status=static_verified or passed")
            if not self.usable_answer:
                raise ValueError("static_verified requires an answer or candidate")
        if self.status == UserSolveStatus.RUNTIME_VALIDATED:
            if self.validation_status not in (ValidationStatus.RUNTIME_VALIDATED, ValidationStatus.PASSED):
                raise ValueError("runtime_validated requires validation_status=runtime_validated or passed")
            if not self.usable_answer:
                raise ValueError("runtime_validated requires an answer or candidate")
            if not self.internal_references and not self.developer_trace_ref:
                raise ValueError("runtime_validated requires runtime validation evidence (internal_references or developer_trace_ref)")
        if self.status == UserSolveStatus.RUNTIME_VALIDATION_PENDING:
            if self.validation_status == ValidationStatus.RUNTIME_VALIDATED:
                raise ValueError("runtime_validation_pending must not have validation_status=runtime_validated")
        if self.status == UserSolveStatus.STATIC_VERIFIED and self.validation_status == ValidationStatus.RUNTIME_VALIDATED:
            raise ValueError("static_verified must not have validation_status=runtime_validated")
        if self.status == UserSolveStatus.FAILED and not (self.reason or self.message):
            raise ValueError("failed requires a reason or message")
        if self.status == UserSolveStatus.BLOCKED and not (self.reason or self.message):
            raise ValueError("blocked requires a reason or message")
        if self.status == UserSolveStatus.CANDIDATE_FOUND and not self.candidates and not self.answer:
            raise ValueError("candidate_found requires an answer or candidate")

    def to_user_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "status": self.status.value,
            "validation_status": self.validation_status.value,
            "evidence_status": self.evidence_status.value,
            "mode": self.mode.value,
            "message": self.message,
            "reason": self.reason,
            "candidates": [candidate.to_user_dict() for candidate in self.candidates],
        }
        if self.answer:
            payload["answer"] = self.answer
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return redact_internal_references(payload)

    def to_developer_dict(self) -> dict[str, Any]:
        payload = self.to_user_dict()
        payload["developer_trace_ref"] = self.developer_trace_ref
        payload["internal_references"] = list(self.internal_references)
        payload["candidates"] = [candidate.to_developer_dict() for candidate in self.candidates]
        return payload

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "payload": self.to_developer_dict(),
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> "UserSolveResult":
        schema_version = data.get("schema_version")
        if schema_version is None:
            raise ValueError("schema_version is required")
        if not isinstance(schema_version, int):
            raise ValueError("schema_version must be an integer")
        if schema_version > CONTRACT_SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version={schema_version}, max={CONTRACT_SCHEMA_VERSION}")
        payload = data.get("payload")
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be a mapping")
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "UserSolveResult":
        candidates = payload.get("candidates") or []
        if not isinstance(candidates, list):
            raise ValueError("candidates must be a list")
        return cls(
            status=payload.get("status", UserSolveStatus.FAILED),
            validation_status=payload.get("validation_status", ValidationStatus.NOT_STARTED),
            evidence_status=payload.get("evidence_status", EvidenceStatus.NONE),
            mode=payload.get("mode", UserSolveMode.AUTO),
            answer=str(payload.get("answer") or ""),
            candidates=[
                candidate if isinstance(candidate, UserSolveCandidate) else UserSolveCandidate(**candidate)
                for candidate in candidates
            ],
            confidence=payload.get("confidence"),
            message=str(payload.get("message") or ""),
            reason=str(payload.get("reason") or ""),
            developer_trace_ref=str(payload.get("developer_trace_ref") or ""),
            internal_references=[str(item) for item in payload.get("internal_references") or []],
        )
