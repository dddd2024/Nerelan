from reverse_agent.user_solve import adapt_fast_session_bundle
from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_handoff import build_handoff_packet


def test_handoff_packet_derives_from_session_and_redacts_user_view() -> None:
    session = adapt_fast_session_bundle(
        {
            "session_id": "session-handoff",
            "selected_candidate": "flag{candidate}",
            "developer_trace_ref": "project_state/decision_packet.md",
        }
    )

    packet = build_handoff_packet(session)

    assert packet.to_user_dict()["session_id"] == "session-handoff"
    assert packet.to_user_dict()["next_action"]["kind"] == "validate_candidate"
    assert not contains_internal_reference(packet.to_user_dict())
    assert contains_internal_reference(packet.to_developer_dict()["developer_audit_refs"])
