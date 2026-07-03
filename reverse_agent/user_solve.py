from __future__ import annotations

from typing import Any, Mapping

from .evidence_quality import EvidenceQualityMapper
from .user_solve_contract import (
    EvidenceStatus,
    UserSolveCandidate,
    UserSolveMode,
    UserSolveResult,
    UserSolveStatus,
    ValidationStatus,
)
from .user_solve_trace import ArtifactReference, UserSolveTaskTrace
from .user_solve_session import UserSolveSessionBundle, build_session_bundle


NEGATIVE_CANDIDATES = {"", "NOT_FOUND", "UNKNOWN", "N/A", "NONE", "NULL"}


def _string(value: Any) -> str:
    return str(value or "").strip()


def _candidate_values(payload: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("selected_flag", "selected_candidate", "answer", "candidate", "final_answer"):
        value = _string(payload.get(key))
        if value.upper() not in NEGATIVE_CANDIDATES:
            values.append(value)
    raw_candidates = payload.get("candidates") or []
    if isinstance(raw_candidates, list):
        for item in raw_candidates:
            if isinstance(item, Mapping):
                value = _string(item.get("value") or item.get("candidate") or item.get("flag"))
            else:
                value = _string(item)
            if value.upper() not in NEGATIVE_CANDIDATES:
                values.append(value)
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _validation_status(payload: Mapping[str, Any]) -> ValidationStatus:
    raw = _string(payload.get("validation_status")).lower()
    if raw in {item.value for item in ValidationStatus}:
        return ValidationStatus(raw)
    runtime = payload.get("runtime_validation") or payload.get("validation") or {}
    if isinstance(runtime, Mapping):
        status = _string(runtime.get("status") or runtime.get("validation_status")).lower()
        if status in {"passed", "valid", "runtime_validated", "success"}:
            return ValidationStatus.PASSED
        if status in {"failed", "invalid", "rejected"}:
            return ValidationStatus.FAILED
    validations = payload.get("candidate_validations") or []
    if isinstance(validations, list):
        for item in validations:
            if isinstance(item, Mapping) and _string(item.get("status")).lower() in {"passed", "valid"}:
                return ValidationStatus.PASSED
        for item in validations:
            if isinstance(item, Mapping) and _string(item.get("status")).lower() in {"failed", "invalid", "rejected"}:
                return ValidationStatus.FAILED
    return ValidationStatus.PENDING


def _confidence(payload: Mapping[str, Any]) -> float | None:
    for key in ("confidence", "score"):
        if key not in payload:
            continue
        try:
            value = float(payload[key])
        except (TypeError, ValueError):
            continue
        if value > 1.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))
    return None


def _internal_references(payload: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("report_path", "artifact_path", "trace_path", "developer_trace_ref"):
        value = _string(payload.get(key))
        if value:
            refs.append(value)
    artifacts = payload.get("artifacts") or payload.get("tool_artifacts") or []
    if isinstance(artifacts, list):
        for item in artifacts:
            if isinstance(item, Mapping):
                value = _string(item.get("path") or item.get("artifact_path"))
            else:
                value = _string(item)
            if value:
                refs.append(value)
    return refs


class FastSolveWrapper:
    """Adapt already-built in-memory results into user-facing solve results.

    This class intentionally performs no subprocess, network, runner, harness, or
    sample execution. It only normalizes dictionaries produced elsewhere.
    """

    def __init__(self, evidence_mapper: EvidenceQualityMapper | None = None):
        self.evidence_mapper = evidence_mapper or EvidenceQualityMapper()

    def adapt(self, payload: Mapping[str, Any]) -> UserSolveResult:
        if not isinstance(payload, Mapping):
            raise TypeError("FastSolveWrapper.adapt expects a mapping")

        status_text = _string(payload.get("status")).lower()
        blockers = payload.get("blockers") or payload.get("blocking_reasons") or []
        if isinstance(blockers, str):
            blockers = [blockers]
        if status_text == "blocked" or blockers:
            reason = "; ".join(str(item) for item in blockers) or _string(payload.get("error")) or "analysis blocked"
            return UserSolveResult(
                status=UserSolveStatus.BLOCKED,
                validation_status=ValidationStatus.UNAVAILABLE,
                evidence_status=EvidenceStatus.FAILED,
                message="Analysis is blocked before a user-facing answer can be verified.",
                reason=reason,
                developer_trace_ref=_string(payload.get("developer_trace_ref")),
                internal_references=_internal_references(payload),
            )

        candidates = _candidate_values(payload)
        validation_status = _validation_status(payload)
        confidence = _confidence(payload)
        internal_refs = _internal_references(payload)
        mode = payload.get("mode") or UserSolveMode.FAST

        if not candidates:
            missing = payload.get("missing_evidence") or []
            if missing:
                result = self.evidence_mapper.to_result(missing_evidence=missing)
                return UserSolveResult(
                    status=result.status,
                    validation_status=result.validation_status,
                    evidence_status=result.evidence_status,
                    mode=mode,
                    message=result.message,
                    reason=result.reason,
                    developer_trace_ref=_string(payload.get("developer_trace_ref")),
                    internal_references=[*internal_refs, *result.internal_references],
                )
            return UserSolveResult(
                status=UserSolveStatus.FAILED,
                validation_status=ValidationStatus.UNAVAILABLE,
                evidence_status=EvidenceStatus.PARTIAL,
                mode=mode,
                message="No candidate answer was found in the supplied analysis result.",
                developer_trace_ref=_string(payload.get("developer_trace_ref")),
                internal_references=internal_refs,
            )

        candidate_objs = [
            UserSolveCandidate(
                value=value,
                confidence=confidence if index == 0 else None,
                validation_status=validation_status if index == 0 else ValidationStatus.NOT_STARTED,
            )
            for index, value in enumerate(candidates)
        ]
        if validation_status == ValidationStatus.PASSED:
            return UserSolveResult(
                status=UserSolveStatus.VERIFIED,
                validation_status=ValidationStatus.PASSED,
                evidence_status=EvidenceStatus.COMPLETE,
                mode=mode,
                answer=candidates[0],
                candidates=candidate_objs,
                confidence=confidence,
                message="A candidate answer is verified by supplied validation evidence.",
                developer_trace_ref=_string(payload.get("developer_trace_ref")),
                internal_references=internal_refs,
            )
        if validation_status == ValidationStatus.FAILED:
            return UserSolveResult(
                status=UserSolveStatus.FAILED,
                validation_status=ValidationStatus.FAILED,
                evidence_status=EvidenceStatus.PARTIAL,
                mode=mode,
                candidates=candidate_objs,
                confidence=confidence,
                message="Candidate validation failed in the supplied evidence.",
                developer_trace_ref=_string(payload.get("developer_trace_ref")),
                internal_references=internal_refs,
            )
        return UserSolveResult(
            status=UserSolveStatus.CANDIDATE_FOUND,
            validation_status=ValidationStatus.PENDING,
            evidence_status=EvidenceStatus.BUILDING,
            mode=mode,
            answer=candidates[0],
            candidates=candidate_objs,
            confidence=confidence,
            message="A candidate answer is available while validation evidence is still pending.",
            developer_trace_ref=_string(payload.get("developer_trace_ref")),
            internal_references=internal_refs,
        )

    def adapt_with_trace(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        result = self.adapt(payload)
        missing = payload.get("missing_evidence") or []
        if isinstance(missing, str):
            missing = [missing]
        missing_list = [str(item) for item in missing if str(item).strip()]
        fallback_decision = self.evidence_mapper.fallback_recommendation(
            missing_evidence=missing_list,
            completed_steps=payload.get("completed_fallback_steps") or [],
        )
        artifacts = [
            ArtifactReference(label="internal_artifact", path=path, public=False)
            for path in _internal_references(payload)
        ]
        trace = UserSolveTaskTrace.from_result(
            task_id=_string(payload.get("task_id")) or "user_solve_task",
            result=result,
            fallback_decision=fallback_decision,
            missing_evidence=missing_list,
            artifact_references=artifacts,
            developer_trace_ref=_string(payload.get("developer_trace_ref")),
        )
        return {
            "result": result,
            "trace": trace,
            "fallback_decision": fallback_decision,
        }

    def adapt_session_bundle(self, payload: Mapping[str, Any]) -> UserSolveSessionBundle:
        result_bundle = self.adapt_with_trace(payload)
        internal_refs = _internal_references(payload)
        missing = payload.get("missing_evidence") or []
        if isinstance(missing, str):
            missing = [missing]
        return build_session_bundle(
            session_id=_string(payload.get("session_id")) or _string(payload.get("task_id")) or "user_solve_session",
            result=result_bundle["result"],
            trace=result_bundle["trace"],
            fallback_decision=result_bundle["fallback_decision"],
            missing_evidence=[str(item) for item in missing if str(item).strip()],
            public_message=_string(payload.get("public_message")) or result_bundle["result"].message,
            developer_trace_refs=[
                ref for ref in [_string(payload.get("developer_trace_ref")), *internal_refs] if ref
            ],
            artifact_references=internal_refs,
        )


def adapt_fast_result(payload: Mapping[str, Any]) -> UserSolveResult:
    return FastSolveWrapper().adapt(payload)


def adapt_fast_session_bundle(payload: Mapping[str, Any]) -> UserSolveSessionBundle:
    return FastSolveWrapper().adapt_session_bundle(payload)
