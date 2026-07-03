from reverse_agent.user_solve import adapt_fast_session_bundle
from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_handoff import build_handoff_packet
from reverse_agent.user_solve_request import demo_request
from reverse_agent.user_solve_response import build_response_envelope


def test_response_envelope_contains_user_fields_and_redacts_internal_refs() -> None:
    request = demo_request("candidate")
    session = adapt_fast_session_bundle(
        {
            "session_id": "response-session",
            "selected_candidate": "flag{candidate}",
            "developer_trace_ref": "project_state/decision_packet.md",
        }
    )
    handoff = build_handoff_packet(session)

    envelope = build_response_envelope(
        request=request,
        session=session,
        handoff=handoff,
        developer_audit={"artifact": "project_state/gates/user_solve_control_plane_result.json"},
    )
    user_payload = envelope.to_user_dict()
    developer_payload = envelope.to_developer_dict()

    assert user_payload["status"] == "candidate_found"
    assert user_payload["answer"] == "flag{candidate}"
    assert user_payload["validation_status"] == "pending"
    assert user_payload["evidence_status"] == "building"
    assert user_payload["next_action"]["kind"] == "validate_candidate"
    assert "fallback_summary" in user_payload
    assert not contains_internal_reference(user_payload)
    assert contains_internal_reference(developer_payload["developer_audit"])
