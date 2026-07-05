from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TASK_SCHEMA_VERSION = 1
TASK_STATUSES = (
    "DRAFT",
    "READY",
    "MANUAL_DISPATCHED",
    "MANUAL_RESULT_IMPORTED",
    "FINAL_CHECKED",
    "AUDITED",
    "ACCEPTED",
    "REWORK_REQUIRED",
    "BLOCKED",
)
TASK_TERMINAL_STATUSES = {"ACCEPTED", "REWORK_REQUIRED", "BLOCKED"}
TASK_STATUS_TRANSITIONS = {
    "DRAFT": {"READY", "BLOCKED"},
    "READY": {"MANUAL_DISPATCHED", "BLOCKED"},
    "MANUAL_DISPATCHED": {"MANUAL_RESULT_IMPORTED", "REWORK_REQUIRED", "BLOCKED"},
    "MANUAL_RESULT_IMPORTED": {"FINAL_CHECKED", "REWORK_REQUIRED", "BLOCKED"},
    "FINAL_CHECKED": {"AUDITED", "REWORK_REQUIRED", "BLOCKED"},
    "AUDITED": {"ACCEPTED", "REWORK_REQUIRED", "BLOCKED"},
    "ACCEPTED": set(),
    "REWORK_REQUIRED": set(),
    "BLOCKED": set(),
}


@dataclass(frozen=True)
class UserSolveTaskLifecycle:
    status: str

    def allowed_next(self) -> list[str]:
        return sorted(TASK_STATUS_TRANSITIONS.get(normalize_task_status(self.status), set()))

    def validate_transition(self, next_status: str) -> dict[str, Any]:
        return validate_task_transition(self.status, next_status)


def normalize_task_status(status: str) -> str:
    return str(status or "").strip().upper()


def validate_task_transition(from_status: str, to_status: str) -> dict[str, Any]:
    source = normalize_task_status(from_status)
    target = normalize_task_status(to_status)
    errors: list[str] = []
    if source not in TASK_STATUSES:
        errors.append(f"from_status must be one of {list(TASK_STATUSES)}")
    if target not in TASK_STATUSES:
        errors.append(f"to_status must be one of {list(TASK_STATUSES)}")
    allowed = sorted(TASK_STATUS_TRANSITIONS.get(source, set()))
    if not errors and target not in TASK_STATUS_TRANSITIONS[source]:
        errors.append(f"transition {source}->{target} is not allowed")
    return {
        "schema_version": TASK_SCHEMA_VERSION,
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "from_status": source,
        "to_status": target,
        "allowed_to": allowed,
        "terminal_from_status": source in TASK_TERMINAL_STATUSES,
        "dispatch_enabled": False,
    }


def build_demo_task_payload(
    *,
    task_id: str,
    decision_id: str,
    round_id: str,
    report_id: str = "",
    status: str = "DRAFT",
) -> dict[str, Any]:
    normalized = normalize_task_status(status)
    return {
        "schema_version": TASK_SCHEMA_VERSION,
        "task_id": str(task_id),
        "decision_id": str(decision_id),
        "round_id": str(round_id),
        "report_id": str(report_id),
        "status": normalized,
        "source": "demo_fixture",
        "fixture_only": True,
        "real_sample": False,
        "manual_execution": {
            "handoff_exported": normalized in {"MANUAL_DISPATCHED", "MANUAL_RESULT_IMPORTED", "FINAL_CHECKED", "AUDITED", "ACCEPTED"},
            "dispatch_enabled": False,
            "external_tool_invocation": False,
            "model_api_invocation": False,
        },
        "result": None,
        "audit": {
            "final_check_required": True,
            "auditor_required": True,
            "claims_concrete_sample_solved": False,
        },
        "history": [
            {
                "status": normalized,
                "reason": "demo task created for manual-mode orchestrator preview",
            }
        ],
    }


def validate_task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in ("schema_version", "task_id", "decision_id", "round_id", "status"):
        if field not in payload:
            errors.append(f"missing required field: {field}")
    if payload.get("schema_version") != TASK_SCHEMA_VERSION:
        errors.append(f"schema_version must be {TASK_SCHEMA_VERSION}")
    task_id = str(payload.get("task_id") or "")
    if not task_id.startswith("demo_"):
        errors.append("task_id must start with demo_")
    status = normalize_task_status(str(payload.get("status") or ""))
    if status not in TASK_STATUSES:
        errors.append(f"status must be one of {list(TASK_STATUSES)}")
    manual = payload.get("manual_execution") if isinstance(payload.get("manual_execution"), dict) else {}
    for flag in ("dispatch_enabled", "external_tool_invocation", "model_api_invocation"):
        if manual.get(flag) is not False:
            errors.append(f"manual_execution.{flag} must be false")
    if payload.get("real_sample") is not False:
        errors.append("real_sample must be false")
    if payload.get("fixture_only") is not True:
        errors.append("fixture_only must be true")
    return {
        "schema_version": TASK_SCHEMA_VERSION,
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "task_id": task_id,
        "status": status,
        "dispatch_enabled": False,
    }
