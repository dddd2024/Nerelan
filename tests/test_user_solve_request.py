import pytest

from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_request import UserSolveRequest, demo_request


def test_request_user_serialization_is_safe() -> None:
    request = demo_request("candidate")

    payload = request.to_user_dict()

    assert payload["request_id"] == "demo-candidate"
    assert payload["input_kind"] == "fixture"
    assert payload["candidate"] == "flag{demo_candidate}"
    assert not contains_internal_reference(payload)


def test_request_rejects_real_file_semantics() -> None:
    with pytest.raises(ValueError, match="local paths"):
        UserSolveRequest(
            request_id="unsafe",
            input_kind="fixture",
            fixture_name=r"F:\reverse-agent\sample.exe",
        )


def test_request_rejects_persistent_session_request() -> None:
    with pytest.raises(ValueError, match="persistent user sessions"):
        UserSolveRequest(request_id="persistent", persistent_session_requested=True)
