from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_frontend_bridge import UserSolveFrontendBridge, build_frontend_demo_payloads


def test_frontend_bridge_renders_all_demo_states() -> None:
    payload = build_frontend_demo_payloads()
    states = {
        item["fixture_name"]: item["ui_state"]["display_state"]
        for item in payload["fixtures"]
    }

    assert states == {
        "candidate": "candidate_pending_validation",
        "missing-evidence": "needs_more_evidence",
        "blocked": "blocked",
        "failed": "failed",
        "verified": "verified",
    }
    assert payload["fixture_only"] is True
    assert not contains_internal_reference(payload)


def test_frontend_bridge_delegates_to_controller_contract() -> None:
    rendered = UserSolveFrontendBridge().render_fixture("candidate")

    assert rendered["response"]["status"] == "candidate_found"
    assert rendered["response"]["next_action"]["kind"] == "validate_candidate"
    assert rendered["ui_state"]["display_state"] == "candidate_pending_validation"
