from __future__ import annotations

from typing import Any

from .user_solve_errors import ERRORS
from .user_solve_fixtures import FIXTURE_NAMES, fixture_catalog
from .user_solve_ui_state import DISPLAY_STATES


def schema_snapshot() -> dict[str, Any]:
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
        ],
        "fixture_catalog": fixture_catalog(),
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
