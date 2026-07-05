import json

from reverse_agent.orchestrator_api import handle_orchestrator_request
from reverse_agent.user_solve_cli import main


def test_orchestrator_api_dashboard_is_pure_preview() -> None:
    response = handle_orchestrator_request("GET", "/api/manual/dashboard")

    assert response["status_code"] == 200
    assert response["fixture_only"] is True
    assert response["dispatch_enabled"] is False
    assert response["body"]["dashboard"]["production_service"] is False


def test_orchestrator_api_exposes_handoff_and_import_preview() -> None:
    handoff = handle_orchestrator_request("GET", "/api/manual/handoff")
    preview = handle_orchestrator_request("GET", "/api/manual/import-preview")

    assert handoff["body"]["handoff"]["runner_dispatch_enabled"] is False
    assert preview["body"]["import_preview"]["preview_status"] == "PASSED"


def test_cli_manual_console_dashboard_preview(capsys) -> None:
    assert main(["--manual-console-demo", "dashboard"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["dashboard"]["mode"] == "manual"
    assert payload["dashboard"]["dispatch_enabled"] is False


def test_cli_manual_console_available_actions_preview(capsys) -> None:
    assert main(["--manual-console-demo", "available-actions"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["actions"][0]["executes"] is False
