from __future__ import annotations

from typing import Any, Mapping


MANUAL_IMPORT_SCHEMA_VERSION = 1
MANUAL_RESULT_STATUSES = {"MANUAL_RESULT_IMPORTED", "REWORK_REQUIRED", "BLOCKED"}
FORBIDDEN_TRUE_FLAGS = {
    "real_execution",
    "external_analysis_tool_invoked",
    "runner_dispatched",
    "model_api_invoked",
    "runtime_validation_on_real_sample",
    "static_verification_on_real_sample",
    "concrete_sample_solved",
}


def validate_manual_result_payload(
    payload: Mapping[str, Any],
    *,
    decision_id: str,
    round_id: str,
    allowed_commands: list[str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    allowed = set(allowed_commands or [])
    if payload.get("schema_version") != MANUAL_IMPORT_SCHEMA_VERSION:
        errors.append(f"schema_version must be {MANUAL_IMPORT_SCHEMA_VERSION}")
    if str(payload.get("decision_id") or "") != decision_id:
        errors.append("decision_id mismatch")
    if str(payload.get("round_id") or "") != round_id:
        errors.append("round_id mismatch")
    task_id = str(payload.get("task_id") or "")
    job_id = str(payload.get("job_id") or "")
    if not task_id.startswith("demo_"):
        errors.append("task_id must start with demo_")
    if not job_id.startswith("job_demo_"):
        errors.append("job_id must start with job_demo_")
    status = str(payload.get("status") or "").strip().upper()
    if status not in MANUAL_RESULT_STATUSES:
        errors.append(f"status must be one of {sorted(MANUAL_RESULT_STATUSES)}")
    claims = payload.get("claims") if isinstance(payload.get("claims"), Mapping) else {}
    for flag in sorted(FORBIDDEN_TRUE_FLAGS):
        if claims.get(flag) is not False:
            errors.append(f"claims.{flag} must be false")
    commands = payload.get("commands_claimed") or []
    if not isinstance(commands, list) or not all(isinstance(item, str) for item in commands):
        errors.append("commands_claimed must be a list of strings")
        commands = []
    outside = sorted(set(commands) - allowed)
    if outside:
        errors.append("commands_claimed include commands outside command-plan")
    return {
        "schema_version": MANUAL_IMPORT_SCHEMA_VERSION,
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "task_id": task_id,
        "job_id": job_id,
        "status": status,
        "commands_claimed": list(commands),
        "verified_evidence": False,
        "manual_claim_only": True,
    }


def merge_manual_result(task_payload: dict[str, Any], result_payload: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(task_payload)
    status = str(result_payload.get("status") or "MANUAL_RESULT_IMPORTED").strip().upper()
    merged["status"] = status
    merged["result"] = {
        "source": "manual_import",
        "result_id": str(result_payload.get("result_id") or "manual_result_demo"),
        "summary": str(result_payload.get("summary") or ""),
        "commands_claimed": list(result_payload.get("commands_claimed") or []),
        "verified_evidence": False,
        "manual_claim_only": True,
    }
    history = list(merged.get("history") or [])
    history.append({"status": status, "reason": "manual result imported as unverified structured evidence"})
    merged["history"] = history
    return merged


def build_demo_manual_result(*, decision_id: str, round_id: str, task_id: str, job_id: str) -> dict[str, Any]:
    return {
        "schema_version": MANUAL_IMPORT_SCHEMA_VERSION,
        "result_id": "manual_result_demo_preview",
        "decision_id": decision_id,
        "round_id": round_id,
        "task_id": task_id,
        "job_id": job_id,
        "status": "MANUAL_RESULT_IMPORTED",
        "summary": "Demo manual result preview; no real execution or verification is claimed.",
        "commands_claimed": [],
        "claims": {flag: False for flag in sorted(FORBIDDEN_TRUE_FLAGS)},
    }
