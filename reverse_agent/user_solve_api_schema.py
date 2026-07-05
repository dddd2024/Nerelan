from __future__ import annotations

from typing import Any

from .user_solve_errors import ERRORS
from .user_solve_fixtures import FIXTURE_NAMES, fixture_catalog
from .user_solve_ui_state import DISPLAY_STATES
from .tool_capabilities import capability_snapshot
from .tool_profiles import tool_profile_snapshot
from .orchestrator_console_schema import CONSOLE_PANELS


def schema_snapshot() -> dict[str, Any]:
    workbench_routes = [
        {"method": "GET", "path": "/api/workbench/fixtures", "kind": "workbench_catalog"},
        {"method": "GET", "path": "/api/workbench/capabilities", "kind": "capability_snapshot"},
        {"method": "GET", "path": "/api/workbench/schema", "kind": "schema_snapshot"},
        {"method": "GET", "path": "/api/workbench/route-plan/{fixture_name}", "kind": "route_plan"},
        {"method": "GET", "path": "/api/workbench/trace/{fixture_name}", "kind": "task_trace"},
        {"method": "POST", "path": "/api/workbench/preview", "kind": "workbench_preview"},
    ]
    manual_routes = [
        {"method": "GET", "path": "/api/manual/dashboard", "kind": "dashboard"},
        {"method": "GET", "path": "/api/manual/decision", "kind": "decision"},
        {"method": "GET", "path": "/api/manual/command-plan", "kind": "command_plan"},
        {"method": "GET", "path": "/api/manual/jobs", "kind": "jobs"},
        {"method": "GET", "path": "/api/manual/tasks", "kind": "tasks"},
        {"method": "GET", "path": "/api/manual/handoff", "kind": "manual_handoff"},
        {"method": "GET", "path": "/api/manual/import-preview", "kind": "manual_import_preview"},
        {"method": "GET", "path": "/api/manual/gates", "kind": "gate_summary"},
        {"method": "GET", "path": "/api/manual/audit", "kind": "audit_context"},
        {"method": "GET", "path": "/api/manual/actions", "kind": "available_actions"},
    ]
    return {
        "schema_version": 1,
        "fixture_only": True,
        "request": {
            "required": ["request_id", "input_kind", "fixture_name", "mode"],
            "input_kinds": ["fixture", "demo", "synthetic"],
            "persistent_sessions": False,
            "real_uploads": False,
        },
        "response": {
            "required": [
                "request",
                "status",
                "validation_status",
                "evidence_status",
                "public_message",
                "next_action",
                "fallback_summary",
                "handoff",
            ],
            "default_user_output_hides_internal_refs": True,
            "developer_serialization_explicit": True,
        },
        "error_payload": {
            "required": ["code", "public_message", "retryable"],
            "codes": sorted(ERRORS),
        },
        "ui_state": {
            "display_states": list(DISPLAY_STATES),
            "verified_requires_validation_passed": True,
            "candidate_found_is_pending_validation": True,
            "missing_evidence_maps_to_fallback": True,
        },
        "routes": [
            {"method": "GET", "path": "/api/fixtures", "kind": "catalog"},
            {"method": "GET", "path": "/api/fixtures/{fixture_name}", "kind": "fixture"},
            {"method": "POST", "path": "/api/solve", "kind": "fixture_request"},
        ] + workbench_routes + manual_routes,
        "fixture_catalog": fixture_catalog(),
        "tool_profiles": tool_profile_snapshot(),
        "runner_capabilities": capability_snapshot(),
        "route_plan": {
            "required": ["fixture_name", "status", "validation_status", "planned_actions", "executed"],
            "executes_actions": False,
        },
        "task_trace": {
            "required": ["trace_id", "request_id", "fixture_name", "status", "route_plan", "persisted"],
            "persistent_task_files": False,
            "developer_trace_refs_hidden_by_default": True,
        },
        "workbench": {
            "fixture_only": True,
            "production_service": False,
            "persistent_tasks": False,
            "external_tool_invocation": False,
        },
        "manual_mode_orchestrator": {
            "task_statuses": [
                "DRAFT",
                "READY",
                "MANUAL_DISPATCHED",
                "MANUAL_RESULT_IMPORTED",
                "FINAL_CHECKED",
                "AUDITED",
                "ACCEPTED",
                "REWORK_REQUIRED",
                "BLOCKED",
            ],
            "job_statuses": [
                "DRAFT",
                "READY",
                "MANUAL_DISPATCHED",
                "MANUAL_RESULT_IMPORTED",
                "FINAL_CHECKED",
                "AUDITED",
                "ACCEPTED",
                "REWORK_REQUIRED",
                "BLOCKED",
            ],
            "routes": manual_routes,
            "console_panels": list(CONSOLE_PANELS),
            "production_service": False,
            "runner_dispatch": False,
            "model_api_invocation": False,
            "real_sample_processing": False,
        },
        "frontend_demo": {
            "root": "frontend/user_solve_demo",
            "required_files": [
                "index.html",
                "app.js",
                "style.css",
                "README.md",
                "fixtures/catalog.json",
            ],
            "fixture_names": list(FIXTURE_NAMES),
        },
    }
