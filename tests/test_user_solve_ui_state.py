from reverse_agent.user_solve_ui_state import DISPLAY_STATES, map_response_to_ui_state


def test_ui_state_mapping_covers_expected_display_states() -> None:
    assert set(DISPLAY_STATES) == {
        "ready",
        "candidate_pending_validation",
        "needs_more_evidence",
        "verified",
        "blocked",
        "failed",
        "review",
    }


def test_candidate_pending_validation_maps_to_attention_state() -> None:
    state = map_response_to_ui_state(
        {"status": "candidate_found", "validation_status": "pending", "evidence_status": "building"}
    )

    assert state["display_state"] == "candidate_pending_validation"
    assert state["tone"] == "attention"


def test_verified_requires_passed_validation_for_verified_display() -> None:
    state = map_response_to_ui_state(
        {"status": "verified", "validation_status": "passed", "evidence_status": "complete"}
    )
    fallback = map_response_to_ui_state(
        {"status": "verified", "validation_status": "pending", "evidence_status": "building"}
    )

    assert state["display_state"] == "verified"
    assert fallback["display_state"] == "ready"
