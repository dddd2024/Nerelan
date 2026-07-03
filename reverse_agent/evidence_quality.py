from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .user_solve_contract import (
    EvidenceStatus,
    UserSolveResult,
    UserSolveStatus,
    ValidationStatus,
    redact_internal_references,
)


TARGETED_EVIDENCE_KEYWORDS = (
    "decompile",
    "static",
    "function_semantics",
    "runtime_validation",
    "frontier",
    "strata",
    "summary",
    "case_results",
)

BLOCKING_KEYWORDS = (
    "policy",
    "permission",
    "environment",
    "tool_unavailable",
    "blocked",
)


@dataclass(frozen=True)
class MissingEvidenceAssessment:
    missing_evidence: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    user_status: UserSolveStatus = UserSolveStatus.DEEP_ANALYSIS_RUNNING
    evidence_status: EvidenceStatus = EvidenceStatus.BUILDING
    validation_status: ValidationStatus = ValidationStatus.UNAVAILABLE
    message: str = ""


class EvidenceQualityMapper:
    def assess(
        self,
        *,
        missing_evidence: Iterable[str] | None = None,
        blockers: Iterable[str] | None = None,
    ) -> MissingEvidenceAssessment:
        missing = [str(item) for item in (missing_evidence or []) if str(item).strip()]
        blocker_list = [str(item) for item in (blockers or []) if str(item).strip()]
        lowered_blockers = " ".join(blocker_list).lower()
        lowered_missing = " ".join(missing).lower()
        has_blocker = bool(blocker_list) and any(keyword in lowered_blockers for keyword in BLOCKING_KEYWORDS)
        targeted_gap = any(keyword in lowered_missing for keyword in TARGETED_EVIDENCE_KEYWORDS)

        if has_blocker:
            return MissingEvidenceAssessment(
                missing_evidence=missing,
                blockers=blocker_list,
                user_status=UserSolveStatus.BLOCKED,
                evidence_status=EvidenceStatus.FAILED,
                validation_status=ValidationStatus.UNAVAILABLE,
                message=redact_internal_references("Analysis is blocked by an environment or policy requirement."),
            )
        if targeted_gap or missing:
            return MissingEvidenceAssessment(
                missing_evidence=missing,
                blockers=blocker_list,
                user_status=UserSolveStatus.DEEP_ANALYSIS_RUNNING,
                evidence_status=EvidenceStatus.BUILDING,
                validation_status=ValidationStatus.UNAVAILABLE,
                message=redact_internal_references(
                    "More analysis evidence is still being collected before a final answer can be verified."
                ),
            )
        return MissingEvidenceAssessment(
            missing_evidence=[],
            blockers=[],
            user_status=UserSolveStatus.CANDIDATE_FOUND,
            evidence_status=EvidenceStatus.COMPLETE,
            validation_status=ValidationStatus.NOT_STARTED,
            message="Evidence is available for a user-facing candidate result.",
        )

    def to_result(
        self,
        *,
        missing_evidence: Iterable[str] | None = None,
        blockers: Iterable[str] | None = None,
    ) -> UserSolveResult:
        assessment = self.assess(missing_evidence=missing_evidence, blockers=blockers)
        reason = "; ".join(assessment.blockers) if assessment.user_status == UserSolveStatus.BLOCKED else ""
        return UserSolveResult(
            status=assessment.user_status,
            validation_status=assessment.validation_status,
            evidence_status=assessment.evidence_status,
            message=assessment.message,
            reason=redact_internal_references(reason),
            internal_references=[*assessment.missing_evidence, *assessment.blockers],
        )
