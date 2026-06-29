"""Minimal local job contract validation for project_state/jobs/*.json."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


JOB_SCHEMA_VERSION = 1
JOB_STATUSES = {
    "DRAFT",
    "READY",
    "RUNNING",
    "DONE",
    "FINAL_CHECKED",
    "AUDITED",
    "ACCEPTED",
    "ACCEPTED_WITH_LIMITATIONS",
    "REWORK_REQUIRED",
    "BLOCKED",
}
JOB_RUNNER_KINDS = {"manual", "codex", "trae", "human", "none"}
JOB_TERMINAL_STATUSES = {
    "ACCEPTED",
    "ACCEPTED_WITH_LIMITATIONS",
    "REWORK_REQUIRED",
    "BLOCKED",
}
JOB_STATUS_TRANSITIONS = {
    "DRAFT": {"READY", "BLOCKED"},
    "READY": {"RUNNING", "BLOCKED"},
    "RUNNING": {"DONE", "REWORK_REQUIRED", "BLOCKED"},
    "DONE": {"FINAL_CHECKED", "REWORK_REQUIRED", "BLOCKED"},
    "FINAL_CHECKED": {"AUDITED", "REWORK_REQUIRED", "BLOCKED"},
    "AUDITED": {
        "ACCEPTED",
        "ACCEPTED_WITH_LIMITATIONS",
        "REWORK_REQUIRED",
        "BLOCKED",
    },
    "ACCEPTED": set(),
    "ACCEPTED_WITH_LIMITATIONS": set(),
    "REWORK_REQUIRED": set(),
    "BLOCKED": set(),
}
REQUIRED_FIELDS = {
    "schema_version",
    "job_id",
    "round_id",
    "decision_id",
    "mainline",
    "status",
    "runner",
    "required_inputs",
    "required_outputs",
    "permissions",
    "budgets",
}
FORBIDDEN_PERMISSION_FLAGS = {
    "allow_remote_mutation",
    "allow_llm_calls",
    "allow_agent_dispatch",
    "allow_reverse_solving",
}
JOB_ORCHESTRATION_JOB_OUTPUT_TEMPLATE = "project_state/jobs/{job_id}.json"
JOB_ORCHESTRATION_REQUIRED_INPUTS = [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
]
JOB_ORCHESTRATION_REQUIRED_OUTPUTS = [
    "project_state/jobs/{job_id}.json",
    "project_state/gates/job_orchestration_result.json",
    "project_state/gates/runner_contract_result.json",
    "project_state/gates/control_plane_snapshot.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
]


def _string_value(payload: Mapping[str, Any], field: str, errors: list[str]) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")
        return ""
    return value.strip()


def _string_list(payload: Mapping[str, Any], field: str, errors: list[str]) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{field} must be a list of non-empty strings")
        return []
    return [item.strip() for item in value]


def _validate_runner(value: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        errors.append("runner must be an object")
        return {}
    kind = value.get("kind")
    dispatch_enabled = value.get("dispatch_enabled")
    if kind not in JOB_RUNNER_KINDS:
        errors.append(f"runner.kind must be one of {sorted(JOB_RUNNER_KINDS)}")
    if dispatch_enabled is not False:
        errors.append("runner.dispatch_enabled must be false")
    return {"kind": kind, "dispatch_enabled": dispatch_enabled}


def _validate_permissions(value: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        errors.append("permissions must be an object")
        return {}
    permissions = dict(value)
    missing_flags = sorted(flag for flag in FORBIDDEN_PERMISSION_FLAGS if flag not in permissions)
    if missing_flags:
        errors.append(f"permissions missing required false flags: {missing_flags}")
    enabled_flags = sorted(
        flag for flag in FORBIDDEN_PERMISSION_FLAGS if permissions.get(flag) is not False
    )
    if enabled_flags:
        errors.append(f"permissions must set these flags to false: {enabled_flags}")
    return permissions


def _validate_budgets(value: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        errors.append("budgets must be an object")
        return {}
    budgets = dict(value)
    for field in ("max_runtime_seconds", "max_commands"):
        budget_value = budgets.get(field)
        if not isinstance(budget_value, int) or budget_value < 0:
            errors.append(f"budgets.{field} must be a non-negative integer")
    return budgets


def _iso_datetime(value: Any, field: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty ISO-8601 timestamp")
        return ""
    text = value.strip()
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 timestamp")
    return text


def _validate_lock(value: Any, errors: list[str]) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        errors.append("lock must be an object when present")
        return {}
    lock = dict(value)
    for field in ("lock_id", "owner"):
        if not isinstance(lock.get(field), str) or not lock.get(field, "").strip():
            errors.append(f"lock.{field} must be a non-empty string")
    if "created_at" in lock:
        _iso_datetime(lock.get("created_at"), "lock.created_at", errors)
    return lock


def _validate_lease(value: Any, errors: list[str]) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        errors.append("lease must be an object when present")
        return {}
    lease = dict(value)
    for field in ("lease_id", "owner", "expires_at"):
        if field == "expires_at":
            continue
        if not isinstance(lease.get(field), str) or not lease.get(field, "").strip():
            errors.append(f"lease.{field} must be a non-empty string")
    expires_at = _iso_datetime(lease.get("expires_at"), "lease.expires_at", errors)
    acquired_at = ""
    if "acquired_at" in lease:
        acquired_at = _iso_datetime(lease.get("acquired_at"), "lease.acquired_at", errors)
    if "heartbeat_at" in lease:
        _iso_datetime(lease.get("heartbeat_at"), "lease.heartbeat_at", errors)
    if acquired_at and expires_at:
        try:
            acquired = datetime.fromisoformat(acquired_at.replace("Z", "+00:00"))
            expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires <= acquired:
                errors.append("lease.expires_at must be later than lease.acquired_at")
        except ValueError:
            pass
    return lease


def planned_job_id_for_round(round_id: str) -> str:
    """Return the deterministic local job id for a decision round."""

    text = str(round_id or "").strip()
    if text.startswith("round_"):
        return f"job_{text[len('round_'):]}"
    return f"job_{text}" if text else ""


def planned_job_artifact_path(job_id: str) -> str:
    """Return the project-relative path for a planned local job artifact."""

    return JOB_ORCHESTRATION_JOB_OUTPUT_TEMPLATE.format(job_id=str(job_id or "").strip())


def build_planned_job_payload(
    decision: Mapping[str, Any],
    *,
    status: str = "DRAFT",
) -> dict[str, Any]:
    """Build a deterministic non-dispatching job plan from decision metadata."""

    round_id = str(decision.get("round_id") or "").strip()
    decision_id = str(decision.get("decision_id") or "").strip()
    mainline = str(decision.get("mainline") or "").strip()
    job_id = planned_job_id_for_round(round_id)
    job_path = planned_job_artifact_path(job_id)
    required_outputs = [
        output.format(job_id=job_id) for output in JOB_ORCHESTRATION_REQUIRED_OUTPUTS
    ]
    if job_path not in required_outputs:
        required_outputs.insert(0, job_path)
    return {
        "schema_version": JOB_SCHEMA_VERSION,
        "job_id": job_id,
        "round_id": round_id,
        "decision_id": decision_id,
        "mainline": mainline,
        "status": str(status or "DRAFT").strip().upper(),
        "runner": {
            "kind": "none",
            "dispatch_enabled": False,
        },
        "required_inputs": list(JOB_ORCHESTRATION_REQUIRED_INPUTS),
        "required_outputs": required_outputs,
        "permissions": {
            "allow_remote_mutation": False,
            "allow_llm_calls": False,
            "allow_agent_dispatch": False,
            "allow_reverse_solving": False,
            "allow_github_actions": False,
            "allow_database_writes": False,
            "allow_scheduler": False,
            "allow_web_ui_mutation": False,
        },
        "budgets": {
            "max_runtime_seconds": 0,
            "max_commands": 0,
        },
        "orchestration": {
            "planning_mode": "non_dispatching",
            "dispatch_policy": "disabled_by_default",
            "task_contract_path": "project_state/decision_packet.md",
            "command_plan_path": "project_state/gates/command_plan.json",
            "execution_authority": "project_state/gates/command_plan.json",
        },
    }


def validate_job_transition(from_status: str, to_status: str) -> dict[str, Any]:
    """Validate a status transition without mutating or dispatching a job."""

    from_value = str(from_status or "").strip().upper()
    to_value = str(to_status or "").strip().upper()
    errors: list[str] = []
    if from_value not in JOB_STATUSES:
        errors.append(f"from_status must be one of {sorted(JOB_STATUSES)}")
    if to_value not in JOB_STATUSES:
        errors.append(f"to_status must be one of {sorted(JOB_STATUSES)}")
    allowed_to = sorted(JOB_STATUS_TRANSITIONS.get(from_value, set()))
    if not errors and to_value not in JOB_STATUS_TRANSITIONS.get(from_value, set()):
        errors.append(f"transition {from_value}->{to_value} is not allowed")
    return {
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "from_status": from_value,
        "to_status": to_value,
        "allowed_to": allowed_to,
        "terminal_from_status": from_value in JOB_TERMINAL_STATUSES,
    }


def _validate_transition(value: Any, status: str, errors: list[str]) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        errors.append("transition must be an object when present")
        return {}
    transition = dict(value)
    from_status = str(transition.get("from_status") or "").strip().upper()
    to_status = str(transition.get("to_status") or "").strip().upper()
    result = validate_job_transition(from_status, to_status)
    errors.extend(result["errors"])
    if to_status and status and to_status != status:
        errors.append("transition.to_status must match job status")
    return {
        "from_status": from_status,
        "to_status": to_status,
        "validation_status": result["validation_status"],
        "allowed_to": result["allowed_to"],
    }


def validate_job_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a project job contract without dispatching anything."""

    errors: list[str] = []
    warnings: list[str] = []
    missing = sorted(field for field in REQUIRED_FIELDS if field not in payload)
    if missing:
        errors.append(f"missing required fields: {missing}")

    schema_version = payload.get("schema_version")
    if schema_version != JOB_SCHEMA_VERSION:
        errors.append(f"schema_version must be {JOB_SCHEMA_VERSION}")

    job_id = _string_value(payload, "job_id", errors)
    round_id = _string_value(payload, "round_id", errors)
    decision_id = _string_value(payload, "decision_id", errors)
    mainline = _string_value(payload, "mainline", errors)
    status = _string_value(payload, "status", errors).upper()
    if status and status not in JOB_STATUSES:
        errors.append(f"status must be one of {sorted(JOB_STATUSES)}")

    runner = _validate_runner(payload.get("runner"), errors)
    required_inputs = _string_list(payload, "required_inputs", errors)
    required_outputs = _string_list(payload, "required_outputs", errors)
    permissions = _validate_permissions(payload.get("permissions"), errors)
    budgets = _validate_budgets(payload.get("budgets"), errors)
    transition = _validate_transition(payload.get("transition"), status, errors)
    lock = _validate_lock(payload.get("lock"), errors)
    lease = _validate_lease(payload.get("lease"), errors)

    return {
        "schema_version": JOB_SCHEMA_VERSION,
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "warnings": warnings,
        "job_id": job_id,
        "round_id": round_id,
        "decision_id": decision_id,
        "mainline": mainline,
        "status": status,
        "runner": runner,
        "required_inputs": required_inputs,
        "required_outputs": required_outputs,
        "permissions": permissions,
        "budgets": budgets,
        "transition": transition,
        "lock": lock,
        "lease": lease,
        "dispatch_enabled": False,
    }


def load_job_file(path: str | Path) -> dict[str, Any]:
    """Load a job contract JSON file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("job contract must be a JSON object")
    return payload


def validate_job_file(path: str | Path) -> dict[str, Any]:
    """Validate a project_state/jobs/*.json job contract."""

    return validate_job_payload(load_job_file(path))


def validate_jobs_dir(state_dir: str | Path) -> dict[str, Any]:
    """Validate all job contracts under project_state/jobs without dispatching."""

    root = Path(state_dir)
    jobs_dir = root / "jobs"
    errors: list[str] = []
    warnings: list[str] = []
    validated_paths: list[str] = []
    status_counts = {status: 0 for status in sorted(JOB_STATUSES)}
    seen_job_ids: dict[str, str] = {}

    if not jobs_dir.exists():
        return {
            "schema_version": JOB_SCHEMA_VERSION,
            "validation_status": "PASSED",
            "errors": errors,
            "warnings": warnings,
            "jobs_dir": str(jobs_dir),
            "job_count": 0,
            "validated_paths": validated_paths,
            "status_counts": status_counts,
            "jobs": [],
            "dispatch_enabled": False,
        }
    if not jobs_dir.is_dir():
        errors.append(f"jobs path is not a directory: {jobs_dir}")
        return {
            "schema_version": JOB_SCHEMA_VERSION,
            "validation_status": "FAILED",
            "errors": errors,
            "warnings": warnings,
            "jobs_dir": str(jobs_dir),
            "job_count": 0,
            "validated_paths": validated_paths,
            "status_counts": status_counts,
            "jobs": [],
            "dispatch_enabled": False,
        }

    jobs: list[dict[str, Any]] = []
    for job_path in sorted(jobs_dir.glob("*.json")):
        path_text = str(job_path)
        try:
            result = validate_job_file(job_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{path_text}: {exc}")
            continue

        errors.extend(f"{path_text}: {error}" for error in result["errors"])
        job_id = result.get("job_id", "")
        if job_id:
            if job_id in seen_job_ids:
                errors.append(
                    f"duplicate job_id {job_id!r}: {seen_job_ids[job_id]} and {path_text}"
                )
            else:
                seen_job_ids[job_id] = path_text
        status = result.get("status", "")
        if status in status_counts:
            status_counts[status] += 1
        if result["validation_status"] == "PASSED":
            validated_paths.append(path_text)
        jobs.append(
            {
                "path": path_text,
                "job_id": job_id,
                "round_id": result.get("round_id", ""),
                "decision_id": result.get("decision_id", ""),
                "status": status,
                "validation_status": result["validation_status"],
                "errors": result["errors"],
            }
        )

    return {
        "schema_version": JOB_SCHEMA_VERSION,
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "warnings": warnings,
        "jobs_dir": str(jobs_dir),
        "job_count": len(jobs),
        "validated_paths": validated_paths,
        "status_counts": status_counts,
        "jobs": jobs,
        "dispatch_enabled": False,
    }
