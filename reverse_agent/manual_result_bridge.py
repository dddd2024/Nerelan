from __future__ import annotations

from typing import Any, Mapping

from .user_solve_manual_import import merge_manual_result, validate_manual_result_payload


def preview_manual_result_import(
    *,
    task_payload: dict[str, Any],
    result_payload: Mapping[str, Any],
    decision_id: str,
    round_id: str,
    allowed_commands: list[str] | None = None,
) -> dict[str, Any]:
    validation = validate_manual_result_payload(
        result_payload,
        decision_id=decision_id,
        round_id=round_id,
        allowed_commands=allowed_commands,
    )
    merged = merge_manual_result(task_payload, result_payload) if validation["validation_status"] == "PASSED" else None
    return {
        "schema_version": 1,
        "preview_status": validation["validation_status"],
        "validation": validation,
        "merged_task": merged,
        "writes_performed": False,
        "verified_evidence": False,
        "manual_claim_only": True,
    }


def evidence_summary_from_import(preview: Mapping[str, Any]) -> dict[str, Any]:
    validation = preview.get("validation") if isinstance(preview.get("validation"), Mapping) else {}
    return {
        "schema_version": 1,
        "evidence_status": "manual_import_preview",
        "validation_status": str(validation.get("validation_status") or "FAILED"),
        "verified_evidence": False,
        "manual_claim_only": True,
        "task_id": str(validation.get("task_id") or ""),
        "job_id": str(validation.get("job_id") or ""),
    }
