from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_controller import UserSolveController
from reverse_agent.user_solve_request import demo_request


def test_controller_candidate_fixture_returns_pending_validation_envelope() -> None:
    envelope = UserSolveController().solve(demo_request("candidate"))
    payload = envelope.to_user_dict()

    assert payload["status"] == "candidate_found"
    assert payload["validation_status"] == "pending"
    assert payload["next_action"]["kind"] == "validate_candidate"
    assert "fixture_only_preview" in payload["warnings"]
    assert not contains_internal_reference(payload)


def test_controller_missing_evidence_fixture_returns_fallback_envelope() -> None:
    envelope = UserSolveController().solve(demo_request("missing-evidence"))
    payload = envelope.to_user_dict()

    assert payload["status"] == "deep_analysis_running"
    assert payload["evidence_status"] == "building"
    assert payload["next_action"]["kind"] == "fallback"
    assert payload["fallback_summary"]["executed"] is False
    assert not contains_internal_reference(payload)
