from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_workbench_api import handle_workbench_request


def test_workbench_api_preview_is_route_shaped_and_pure() -> None:
    response = handle_workbench_request("POST", "/api/workbench/preview", {"fixture_name": "verified"})

    assert response["status_code"] == 200
    assert response["fixture_only"] is True
    assert response["production_service"] is False
    assert response["persistent_tasks"] is False
    assert response["external_tool_invocation"] is False
    assert response["body"]["response"]["status"] == "verified"
    assert not contains_internal_reference(response)


def test_workbench_api_capabilities_and_route_plan() -> None:
    capability = handle_workbench_request("GET", "/api/workbench/capabilities")
    route_plan = handle_workbench_request("GET", "/api/workbench/route-plan/missing-evidence")

    assert capability["status_code"] == 200
    assert capability["body"]["capability"]["can_dispatch"] is False
    assert route_plan["status_code"] == 200
    assert route_plan["body"]["route_plan"]["executed"] is False
