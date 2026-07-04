from __future__ import annotations

from copy import deepcopy
from typing import Any

from .user_solve_contract import UserSolveMode, redact_internal_references
from .user_solve_request import UserSolveRequest


FIXTURE_NAMES = ("candidate", "missing-evidence", "blocked", "failed", "verified")

_FIXTURE_PAYLOADS: dict[str, dict[str, Any]] = {
    "candidate": {
        "session_id": "demo-candidate",
        "task_id": "demo-candidate",
        "mode": UserSolveMode.FAST,
        "public_message": "Offline fixture preview only.",
        "developer_trace_ref": "fixture:candidate",
        "selected_candidate": "flag{demo_candidate}",
        "confidence": 0.64,
        "validation_status": "pending",
    },
    "missing-evidence": {
        "session_id": "demo-missing-evidence",
        "task_id": "demo-missing-evidence",
        "mode": UserSolveMode.FAST,
        "public_message": "More evidence is needed before a final answer can be verified.",
        "developer_trace_ref": "fixture:missing-evidence",
        "missing_evidence": ["targeted_decompile_missing"],
    },
    "blocked": {
        "session_id": "demo-blocked",
        "task_id": "demo-blocked",
        "mode": UserSolveMode.AUTO,
        "public_message": "The fixture is blocked by a policy or environment requirement.",
        "developer_trace_ref": "fixture:blocked",
        "status": "blocked",
        "blockers": ["policy_blocked_fixture"],
    },
    "failed": {
        "session_id": "demo-failed",
        "task_id": "demo-failed",
        "mode": UserSolveMode.FAST,
        "public_message": "No candidate answer was found in the supplied fixture.",
        "developer_trace_ref": "fixture:failed",
        "validation_status": "unavailable",
    },
    "verified": {
        "session_id": "demo-verified",
        "task_id": "demo-verified",
        "mode": UserSolveMode.FAST,
        "public_message": "A supplied fixture candidate has passed validation evidence.",
        "developer_trace_ref": "fixture:verified",
        "selected_candidate": "flag{demo_verified}",
        "confidence": 0.98,
        "validation_status": "passed",
    },
}


def normalize_fixture_name(name: str) -> str:
    fixture = str(name or "").strip().lower().replace("_", "-")
    aliases = {
        "candidate-found": "candidate",
        "missing": "missing-evidence",
        "missing-evidence": "missing-evidence",
        "needs-more-evidence": "missing-evidence",
        "need-more-evidence": "missing-evidence",
    }
    fixture = aliases.get(fixture, fixture)
    if fixture not in _FIXTURE_PAYLOADS:
        raise ValueError(f"unknown fixture: {name}")
    return fixture


def fixture_payload(name: str) -> dict[str, Any]:
    return deepcopy(_FIXTURE_PAYLOADS[normalize_fixture_name(name)])


def fixture_request(name: str) -> UserSolveRequest:
    fixture = normalize_fixture_name(name)
    payload = fixture_payload(fixture)
    return UserSolveRequest(
        request_id=str(payload["session_id"]),
        mode=payload.get("mode") or UserSolveMode.AUTO,
        input_kind="fixture",
        fixture_name=fixture,
        candidate=str(payload.get("selected_candidate") or ""),
        missing_evidence=list(payload.get("missing_evidence") or []),
        public_context={"source": "fixture_catalog", "state": fixture},
    )


def fixture_catalog() -> dict[str, Any]:
    fixtures = []
    for name in FIXTURE_NAMES:
        payload = fixture_payload(name)
        fixtures.append(
            redact_internal_references(
                {
                    "name": name,
                    "request_id": payload["session_id"],
                    "mode": str(payload.get("mode") or UserSolveMode.AUTO),
                    "candidate": payload.get("selected_candidate", ""),
                    "validation_status": payload.get("validation_status", "unavailable"),
                    "missing_evidence": list(payload.get("missing_evidence") or []),
                    "public_message": payload.get("public_message", ""),
                }
            )
        )
    return {
        "schema_version": 1,
        "fixture_only": True,
        "names": list(FIXTURE_NAMES),
        "fixtures": fixtures,
    }
