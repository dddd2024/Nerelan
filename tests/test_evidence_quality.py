from reverse_agent.evidence_quality import EvidenceQualityMapper
from reverse_agent.user_solve_contract import (
    EvidenceStatus,
    UserSolveStatus,
    ValidationStatus,
    contains_internal_reference,
)


def test_missing_targeted_static_evidence_maps_to_deep_analysis() -> None:
    mapper = EvidenceQualityMapper()

    assessment = mapper.assess(
        missing_evidence=[
            "targeted_decompile_missing",
            "project_state/artifact_index.json",
        ]
    )

    assert assessment.user_status == UserSolveStatus.DEEP_ANALYSIS_RUNNING
    assert assessment.evidence_status == EvidenceStatus.BUILDING
    assert assessment.validation_status == ValidationStatus.UNAVAILABLE
    assert not contains_internal_reference(assessment.message)


def test_policy_blocker_maps_to_blocked_without_raw_internal_path() -> None:
    result = EvidenceQualityMapper().to_result(
        blockers=["policy blocked by project_state/negative_results.json"]
    )

    user_payload = result.to_user_dict()

    assert user_payload["status"] == "blocked"
    assert user_payload["evidence_status"] == "failed"
    assert not contains_internal_reference(user_payload)


def test_complete_evidence_is_nonterminal_candidate_ready() -> None:
    assessment = EvidenceQualityMapper().assess(missing_evidence=[])

    assert assessment.user_status == UserSolveStatus.CANDIDATE_FOUND
    assert assessment.evidence_status == EvidenceStatus.COMPLETE
