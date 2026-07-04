from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_local_api import handle_local_fixture_request


def test_local_api_fixture_catalog_route() -> None:
    response = handle_local_fixture_request("GET", "/api/fixtures")

    assert response["status_code"] == 200
    assert response["fixture_only"] is True
    assert response["production_service"] is False
    assert "candidate" in response["body"]["catalog"]["names"]
    assert not contains_internal_reference(response)


def test_local_api_fixture_detail_and_post_solve_routes() -> None:
    candidate = handle_local_fixture_request("GET", "/api/fixtures/candidate")
    verified = handle_local_fixture_request("POST", "/api/solve", {"fixture_name": "verified"})

    assert candidate["body"]["response"]["status"] == "candidate_found"
    assert verified["body"]["response"]["status"] == "verified"
    assert verified["body"]["ui_state"]["display_state"] == "verified"


def test_local_api_errors_are_public_safe() -> None:
    missing = handle_local_fixture_request("GET", "/api/fixtures/nope")
    route = handle_local_fixture_request("GET", "/api/nope")

    assert missing["status_code"] == 404
    assert missing["body"]["error"]["code"] == "fixture_not_found"
    assert route["body"]["error"]["code"] == "route_not_found"
    assert not contains_internal_reference(missing)
