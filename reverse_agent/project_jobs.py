"""Minimal local job contract validation for project_state/jobs/*.json."""

from __future__ import annotations

import json
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
