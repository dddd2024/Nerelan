from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .manual_execution_handoff import build_manual_execution_handoff
from .manual_result_bridge import preview_manual_result_import
from .orchestrator_context import build_orchestrator_context_snapshot
from .project_jobs import build_demo_manual_job_payload
from .project_state import read_decision_meta
from .user_solve_manual_import import build_demo_manual_result
from .user_solve_task_lifecycle import build_demo_task_payload
from .user_solve_task_store import list_demo_tasks


def handle_orchestrator_request(
    method: str,
    path: str,
    body: Mapping[str, Any] | None = None,
    *,
    state_dir: str | Path = "project_state",
) -> dict[str, Any]:
    route_method = str(method or "GET").upper()
    route_path = "/" + str(path or "").strip("/")
    payload = dict(body or {})
    root = Path(state_dir)
    decision = read_decision_meta(root)
    command_plan = _read_json(root / "gates" / "command_plan.json")
    report_id = _report_id(decision)
    task = build_demo_task_payload(
        task_id=str(payload.get("task_id") or "demo_manual_mode_task"),
        decision_id=str(decision.get("decision_id") or ""),
        round_id=str(decision.get("round_id") or ""),
        report_id=report_id,
        status="READY",
    )
    job = build_demo_manual_job_payload(decision, task_id=task["task_id"])

    if route_method == "GET" and route_path == "/api/manual/dashboard":
        return _response(200, {"dashboard": _dashboard(decision, command_plan)})
    if route_method == "GET" and route_path == "/api/manual/decision":
        return _response(200, {"decision": decision})
    if route_method == "GET" and route_path == "/api/manual/command-plan":
        return _response(200, {"command_plan": _command_plan_summary(command_plan)})
    if route_method == "GET" and route_path == "/api/manual/jobs":
        return _response(200, {"jobs": [job]})
    if route_method == "GET" and route_path == "/api/manual/tasks":
        tasks = list_demo_tasks(root)
        return _response(200, {"tasks": tasks or [{"task_id": task["task_id"], "status": task["status"]}]})
    if route_method == "GET" and route_path == "/api/manual/handoff":
        return _response(200, {"handoff": build_manual_execution_handoff(decision=decision, command_plan=command_plan, task_id=task["task_id"], job_id=job["job_id"])})
    if route_method in {"GET", "POST"} and route_path == "/api/manual/import-preview":
        result = build_demo_manual_result(
            decision_id=str(decision.get("decision_id") or ""),
            round_id=str(decision.get("round_id") or ""),
            task_id=task["task_id"],
            job_id=job["job_id"],
        )
        allowed_commands = [str(item.get("command") or "") for item in command_plan.get("commands", []) if isinstance(item, Mapping)]
        return _response(200, {"import_preview": preview_manual_result_import(task_payload=task, result_payload=result, decision_id=str(decision.get("decision_id") or ""), round_id=str(decision.get("round_id") or ""), allowed_commands=allowed_commands)})
    if route_method == "GET" and route_path == "/api/manual/gates":
        return _response(200, {"gates": _gate_summary(root)})
    if route_method == "GET" and route_path == "/api/manual/audit":
        return _response(200, {"audit": build_orchestrator_context_snapshot(state_dir=root, profile="auditor")})
    if route_method == "GET" and route_path == "/api/manual/actions":
        return _response(200, {"actions": available_actions()})
    return _response(404, {"error": {"code": "route_not_found", "public_message": "Manual orchestrator route not found."}})


def available_actions() -> list[dict[str, Any]]:
    return [
        {"id": "review_decision", "label": "Review decision", "enabled": True, "executes": False},
        {"id": "export_handoff", "label": "Export handoff", "enabled": True, "executes": False},
        {"id": "preview_import", "label": "Preview import", "enabled": True, "executes": False},
        {"id": "run_final_check", "label": "Run final-check manually", "enabled": False, "executes": False},
    ]


def _dashboard(decision: Mapping[str, Any], command_plan: Mapping[str, Any]) -> dict[str, Any]:
    commands = command_plan.get("commands") if isinstance(command_plan.get("commands"), list) else []
    return {
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": str(decision.get("round_id") or ""),
        "mode": "manual",
        "command_count": len(commands),
        "dispatch_enabled": False,
        "production_service": False,
    }


def _command_plan_summary(command_plan: Mapping[str, Any]) -> dict[str, Any]:
    commands = command_plan.get("commands") if isinstance(command_plan.get("commands"), list) else []
    return {
        "plan_status": str(command_plan.get("plan_status") or ""),
        "command_count": len(commands),
        "omitted_count": len(command_plan.get("omitted_commands") or []),
        "command_plan_is_authority": True,
    }


def _gate_summary(root: Path) -> dict[str, Any]:
    gates_dir = root / "gates"
    names = ["command_plan.json", "final_gate_result.json", "manual_mode_orchestrator_result.json"]
    return {"gate_files": [{"name": name, "exists": (gates_dir / name).exists()} for name in names]}


def _read_json(path: Path) -> dict[str, Any]:
    import json

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _report_id(decision: Mapping[str, Any]) -> str:
    decision_id = str(decision.get("decision_id") or "")
    return "codex_report_" + decision_id.removeprefix("decision_") if decision_id else ""


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "status_code": status_code,
        "headers": {"content_type": "application/json"},
        "body": body,
        "fixture_only": True,
        "production_service": False,
        "dispatch_enabled": False,
        "model_api_invocation": False,
        "external_tool_invocation": False,
    }
