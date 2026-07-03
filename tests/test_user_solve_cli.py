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
