from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_errors import ERRORS, UserSolveError, error_payload


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
