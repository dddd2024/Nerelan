from __future__ import annotations

from typing import Any

from .user_solve_contract import (
    CONTRACT_SCHEMA_VERSION,
    UserSolveResult,
    UserSolveTask,
    contains_internal_reference,
    redact_internal_references,
)
from .user_solve_errors import BlockedReason, FailedReason, blocked_reason_payload, failed_reason_payload


def build_task_view(task: UserSolveTask) -> dict[str, Any]:
    payload = task.to_user_dict()
    payload["schema_version"] = CONTRACT_SCHEMA_VERSION
    return redact_internal_references(payload)


def build_result_view(result: UserSolveResult) -> dict[str, Any]:
    payload = result.to_user_dict()
    if not contains_internal_reference(payload):
        return payload
    return redact_internal_references(payload)


def build_blocked_view(reason: BlockedReason | str, *, message: str = "") -> dict[str, Any]:
    reason_payload = blocked_reason_payload(reason)
    payload: dict[str, Any] = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "status": "blocked",
        "reason": reason_payload["code"],
        "message": message or reason_payload["public_message"],
        "retryable": reason_payload["retryable"],
    }
    return redact_internal_references(payload)


def build_failed_view(reason: FailedReason | str, *, message: str = "") -> dict[str, Any]:
    reason_payload = failed_reason_payload(reason)
    payload: dict[str, Any] = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "status": "failed",
        "reason": reason_payload["code"],
        "message": message or reason_payload["public_message"],
        "retryable": reason_payload["retryable"],
    }
    return redact_internal_references(payload)


def build_summary_view(result: UserSolveResult) -> dict[str, Any]:
    user_view = build_result_view(result)
    return {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "status": user_view.get("status"),
        "validation_status": user_view.get("validation_status"),
        "message": user_view.get("message", ""),
        "candidate_count": len(user_view.get("candidates", [])),
        "has_answer": bool(user_view.get("answer")),
    }
