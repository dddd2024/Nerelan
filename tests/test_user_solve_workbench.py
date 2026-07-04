from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_workbench import UserSolveWorkbench, build_workbench_demo_payloads


def test_workbench_preview_composes_response_route_plan_capability_and_trace() -> None:
    payload = UserSolveWorkbench().preview_fixture("candidate")

    assert payload["fixture_only"] is True
    assert payload["persistent_task_created"] is False
    assert payload["external_tool_invocation"] is False
    assert payload["response"]["status"] == "candidate_found"
    assert payload["route_plan"]["planned_actions"][0]["kind"] == "validate_candidate"
    assert payload["capability"]["can_dispatch"] is False
    assert payload["task_trace"]["persisted"] is False
    assert not contains_internal_reference(payload)


def test_workbench_demo_payloads_cover_all_fixtures() -> None:
    payload = build_workbench_demo_payloads()
    names = {item["fixture_name"] for item in payload["fixtures"]}

    assert names == {"candidate", "missing-evidence", "blocked", "failed", "verified"}
    assert payload["tool_profiles"]["executes_tools"] is False
