"""Mapping between server task state and frontend Task domain model.

Backend statuses (outer) live in ``run_store.TASK_STATUS_ORDER``. Inner
activity event types remain the canonical set recognized by the Frontend V1
activity stream. This module keeps those mappings centralized so both the
TaskService HTTP responses and the acceptance test can translate consistently.
"""

from __future__ import annotations

from typing import Any, Mapping


BACKEND_STATUS_TO_FRONTEND_STATE: dict[str, str] = {
    "QUEUED": "WAITING_FOR_OWNER",
    "PREPARING_WORKSPACE": "RUNNING",
    "RUNNING_FIXTURE": "RUNNING",
    "VALIDATING": "RUNNING",
    "READY_FOR_REVIEW_FIXTURE": "READY_FOR_HUMAN",
    "BLOCKED": "BLOCKED_EXTERNAL",
    "FAILED": "FAILED_TERMINAL",
    "CANCELLED": "FAILED_TERMINAL",
}

FAILURE_CLASSIFICATION_TO_TEST_STATUS: dict[str, str] = {
    "": "PENDING",
    "validation_failed": "FAIL",
    "execution_failed": "FAIL",
    "blocked": "PENDING",
    "failed": "FAIL",
}


def map_task_status_to_frontend_state(status: str) -> str:
    return BACKEND_STATUS_TO_FRONTEND_STATE.get(status, "WAITING_FOR_OWNER")


def _g(obj: Mapping[str, Any], key: str, default: Any = "") -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _seq(obj: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = _g(obj, key, [])
    return list(value) if value is not None else []


def map_task_to_frontend(task: Mapping[str, Any]) -> dict[str, Any]:
    """Build a frontend-consumable Task mapping from a server Task row.

    Accepts either a dict or a dataclass/task instance. Returns only
    sanitized, frontend-visible fields. Provider credentials, raw secrets,
    and internal authorization state never cross this boundary.
    """

    state = map_task_status_to_frontend_state(str(_g(task, "status", "")))
    failure_class = str(_g(task, "failure_classification", "") or "")
    blocker = ""
    next_action = ""
    if state == "READY_FOR_HUMAN":
        next_action = "Owner review of fixture-validated result"
    elif failure_class:
        blocker = _g(task, "failure_detail", failure_class) or failure_class
        next_action = "Investigate failure classification"
    elif state == "WAITING_FOR_OWNER":
        next_action = "Waiting for executor dispatch"
    elif state == "RUNNING":
        next_action = "Executor running"

    return {
        "id": _g(task, "id", ""),
        "title": _g(task, "title", ""),
        "issueNumber": 0,
        "state": state,
        "riskTier": "R1",
        "updatedAt": _g(task, "updated_at", ""),
        "blocker": blocker,
        "nextAction": next_action,
        "permissionProfile": _g(task, "permission_profile", "ASK_FOR_APPROVAL") or "ASK_FOR_APPROVAL",
        "modelProfileId": _g(task, "model_profile_ref", ""),
        "branch": _g(task, "branch", "") or _g(task, "id", ""),
        "activity": _map_events(_seq(task, "events")),
        "changes": _map_changed_files(_seq(task, "changed_files")),
        "evidence": _map_evidence(_seq(task, "evidence_refs") or _seq(task, "evidence")),
        "authorityStatus": "APPROVED",
        "testStatus": FAILURE_CLASSIFICATION_TO_TEST_STATUS.get(failure_class, "PENDING"),
        "workflowStatus": "PENDING",
        "executor": "fixture/provider-free"
        if _g(task, "executor_kind", "") == "deterministic_fixture"
        else _g(task, "executor_kind", ""),
    }


def _map_events(events: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": e.get("id", ""),
            "type": e.get("type", "EXECUTOR_FINISHED"),
            "timestamp": e.get("timestamp", ""),
            "title": e.get("title", ""),
            "description": e.get("description", ""),
            "rawLog": e.get("raw_log", ""),
            "expanded": False,
        }
        for e in events
    ]


def _map_changed_files(files: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    status_map = {
        "added": "added",
        "modified": "modified",
        "deleted": "deleted",
        "renamed": "renamed",
        "new": "added",
    }
    return [
        {
            "path": f.get("path", ""),
            "status": status_map.get(f.get("status", "modified"), "modified"),
            "additions": int(f.get("additions", 0)),
            "deletions": int(f.get("deletions", 0)),
            "diff": "",
        }
        for f in files
    ]


def _map_evidence(items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": it.get("id", ""),
            "category": it.get("category", "Info"),
            "label": it.get("label", ""),
            "value": it.get("value", ""),
            "status": _map_evidence_status(it.get("status", "info")),
            "detail": it.get("detail", ""),
            "rawJson": it.get("raw_json_digest", ""),
        }
        for it in items
    ]


def _map_evidence_status(status: str) -> str:
    return {
        "pass": "pass",
        "fail": "fail",
        "pending": "pending",
        "info": "info",
    }.get(str(status), "info")
