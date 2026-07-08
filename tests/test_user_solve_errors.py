from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_errors import (
    BLOCKED_REASONS,
    ERRORS,
    FAILED_REASONS,
    BlockedReason,
    FailedReason,
    UserSolveError,
    blocked_reason_payload,
    error_payload,
    failed_reason_payload,
)


def test_error_taxonomy_has_stable_public_payloads() -> None:
    assert {"fixture_not_found", "route_not_found", "method_not_allowed", "unsafe_request"} <= set(ERRORS)

    payload = error_payload("fixture_not_found")

    assert payload["code"] == "fixture_not_found"
    assert payload["retryable"] is False
    assert "project_state" not in payload["public_message"]
    assert not contains_internal_reference(payload)


def test_developer_diagnostics_are_explicit() -> None:
    error = UserSolveError(
        code="fixture_not_found",
        public_message="That local demo fixture is not available.",
        developer_diagnostics={"artifact": "project_state/gates/user_solve_local_frontend_mvp_result.json"},
    )

    assert not contains_internal_reference(error.to_user_dict())
    assert contains_internal_reference(error.to_developer_dict()["developer_diagnostics"])


def test_blocked_reason_codes_cover_required_categories() -> None:
    required = {"policy", "tool", "environment", "sample_format", "unsupported"}
    actual = {reason.value for reason in BlockedReason}
    assert required <= actual
    assert set(BLOCKED_REASONS.keys()) >= {BlockedReason(r) for r in required}


def test_failed_reason_codes_cover_required_categories() -> None:
    required = {"policy", "tool", "environment", "sample_format", "unsupported"}
    actual = {reason.value for reason in FailedReason}
    assert required <= actual


def test_blocked_reason_payload_is_serializable() -> None:
    payload = blocked_reason_payload("tool")
    assert payload["code"] == "tool"
    assert payload["retryable"] is True
    assert not contains_internal_reference(payload)


def test_failed_reason_payload_is_serializable() -> None:
    payload = failed_reason_payload("analysis")
    assert payload["code"] == "analysis"
    assert payload["retryable"] is False
    assert not contains_internal_reference(payload)


def test_blocked_reason_payload_redacts_internal_references() -> None:
    payload = blocked_reason_payload("environment")
    assert not contains_internal_reference(payload)


def test_failed_reason_payload_unknown_reason_falls_back() -> None:
    payload = failed_reason_payload("unknown_reason")
    assert payload["code"] in {"analysis", "unsupported"}


def test_reason_codes_are_explicit_and_serializable() -> None:
    for reason in BlockedReason:
        payload = blocked_reason_payload(reason)
        assert "code" in payload
        assert "public_message" in payload
        assert "retryable" in payload
        assert isinstance(payload["code"], str)
        assert isinstance(payload["public_message"], str)
        assert isinstance(payload["retryable"], bool)
