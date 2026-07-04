import json

from reverse_agent.user_solve_cli import main
from reverse_agent.user_solve_contract import contains_internal_reference


def test_cli_candidate_demo_outputs_safe_response(capsys) -> None:
    assert main(["--demo", "candidate"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "candidate_found"
    assert payload["next_action"]["kind"] == "validate_candidate"
    assert not contains_internal_reference(payload)


def test_cli_missing_evidence_demo_outputs_safe_response(capsys) -> None:
    assert main(["--demo", "missing-evidence"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "deep_analysis_running"
    assert payload["next_action"]["kind"] == "fallback"
    assert payload["fallback_summary"]["executed"] is False
    assert not contains_internal_reference(payload)


def test_cli_workbench_route_plan_preview(capsys) -> None:
    assert main(["--workbench-demo", "route-plan"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["fixture_name"] == "missing-evidence"
    assert payload["executed"] is False
    assert payload["planned_actions"][0]["kind"] == "collect_evidence"
    assert not contains_internal_reference(payload)


def test_cli_workbench_capability_preview(capsys) -> None:
    assert main(["--workbench-demo", "capability"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["capability"]["can_dispatch"] is False
    assert payload["capability"]["executes_external_tools"] is False
    assert not contains_internal_reference(payload)
