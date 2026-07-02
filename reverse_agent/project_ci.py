from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CI_OBSERVATION_REQUIRED_FIELDS: tuple[str, ...] = (
    "commit_sha",
    "workflow_name",
    "run_id",
    "status",
    "conclusion",
    "job_summaries",
    "observed_commands",
    "artifacts",
    "provenance",
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _truthy_current(payload: dict[str, Any], decision_id: str, round_id: str) -> bool:
    return (
        bool(payload)
        and str(payload.get("decision_id") or "") == decision_id
        and str(payload.get("round_id") or "") == round_id
    )


def _gate_summary(state_dir: Path, artifact_name: str, decision_id: str, round_id: str) -> dict[str, Any]:
    payload = _read_json(state_dir / "gates" / artifact_name)
    return {
        "artifact": f"project_state/gates/{artifact_name}",
        "exists": bool(payload),
        "current_round": _truthy_current(payload, decision_id, round_id),
        "gate_status": payload.get("gate_status"),
        "status": payload.get("readiness_status")
        or payload.get("observation_state")
        or payload.get("ci_observation_status")
        or payload.get("manifest_status")
        or payload.get("reconcile_status")
        or payload.get("closeout_status"),
        "recommendation": payload.get("recommendation"),
        "errors": payload.get("errors") or payload.get("blocking_reasons") or [],
        "warnings": payload.get("warnings") or [],
    }


def build_observation_schema_artifact(
    *,
    decision_id: str,
    round_id: str,
    report_id: str,
    generated_at: str,
    artifact_name: str,
    output_path: str,
) -> dict[str, Any]:
    fields = {
        "commit_sha": "Git commit SHA observed for the workflow run.",
        "workflow_name": "Workflow display name, for example State Gate.",
        "run_id": "Workflow run ID or equivalent immutable CI run identifier.",
        "status": "Workflow status, such as queued, in_progress, or completed.",
        "conclusion": "Workflow conclusion, such as success, failure, cancelled, or skipped.",
        "job_summaries": "List of jobs with job name, status, conclusion, and step summaries.",
        "observed_commands": "Commands observed from CI logs or job summaries.",
        "artifacts": "CI artifacts exported by the workflow, including name, path, and metadata.",
        "provenance": "Where the snapshot came from and who/what captured it.",
    }
    return {
        "schema_version": 1,
        "artifact_name": artifact_name,
        "gate_name": "ci-observation-schema",
        "gate_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "generated_at": generated_at,
        "schema_status": "DEFINED",
        "required_fields": list(CI_OBSERVATION_REQUIRED_FIELDS),
        "field_definitions": fields,
        "accepted_snapshot_shape": {
            "commit_sha": "string",
            "workflow_name": "string",
            "run_id": "string",
            "status": "string",
            "conclusion": "string",
            "job_summaries": "list[object]",
            "observed_commands": "list[string|object]",
            "artifacts": "list[object]",
            "provenance": "object",
        },
        "evidence_only": True,
        "executable": False,
        "can_execute": False,
        "can_dispatch": False,
        "mutates_state": False,
        "generated_artifacts": [output_path],
        "errors": [],
        "warnings": [],
    }


def validate_observation_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {"status": "FAILED", "errors": ["snapshot is not a JSON object"]}
    for field in CI_OBSERVATION_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing required field: {field}")
    for field in ("job_summaries", "observed_commands", "artifacts"):
        if field in payload and not isinstance(payload.get(field), list):
            errors.append(f"{field} must be a list")
    if "provenance" in payload and not isinstance(payload.get("provenance"), dict):
        errors.append("provenance must be an object")
    for field in ("commit_sha", "workflow_name", "run_id", "status", "conclusion"):
        if field in payload and not str(payload.get(field) or "").strip():
            errors.append(f"{field} must be non-empty")
    return {
        "status": "PASSED" if not errors else "FAILED",
        "errors": errors,
        "normalized_snapshot": {
            "commit_sha": str(payload.get("commit_sha") or ""),
            "workflow_name": str(payload.get("workflow_name") or ""),
            "run_id": str(payload.get("run_id") or ""),
            "status": str(payload.get("status") or ""),
            "conclusion": str(payload.get("conclusion") or ""),
            "job_summaries": payload.get("job_summaries") if isinstance(payload.get("job_summaries"), list) else [],
            "observed_commands": payload.get("observed_commands") if isinstance(payload.get("observed_commands"), list) else [],
            "artifacts": payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else [],
            "provenance": payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {},
        },
    }


def build_observation_handoff_artifact(
    *,
    decision_id: str,
    round_id: str,
    report_id: str,
    generated_at: str,
    artifact_name: str,
    output_path: str,
    snapshot_payload: dict[str, Any] | None,
    snapshot_path: str | None,
) -> dict[str, Any]:
    errors: list[str] = []
    if snapshot_payload is None:
        observation_state = "AWAITING_EXTERNAL_OBSERVATION"
        snapshot_validation_status = "NOT_SUPPLIED"
        normalized_snapshot: dict[str, Any] | None = None
    else:
        validation = validate_observation_snapshot(snapshot_payload)
        snapshot_validation_status = str(validation["status"])
        errors.extend(validation["errors"])
        normalized_snapshot = validation["normalized_snapshot"]
        observation_state = "SUPPLIED_BOUNDED_INPUT" if not errors else "INVALID_SUPPLIED_INPUT"
    return {
        "schema_version": 1,
        "artifact_name": artifact_name,
        "gate_name": "ci-observation-handoff",
        "gate_status": "PASSED" if not errors else "FAILED",
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "generated_at": generated_at,
        "observation_state": observation_state,
        "snapshot_validation_status": snapshot_validation_status,
        "snapshot_source": snapshot_path or None,
        "snapshot": normalized_snapshot,
        "handoff_contract": {
            "external_observer_required": snapshot_payload is None,
            "dispatch_performed": False,
            "polling_performed": False,
            "repository_write_performed": False,
        },
        "evidence_only": True,
        "executable": False,
        "can_execute": False,
        "can_dispatch": False,
        "mutates_state": False,
        "generated_artifacts": [output_path],
        "errors": errors,
        "warnings": ["external CI observation has not been supplied"] if snapshot_payload is None else [],
    }


def build_observation_reconcile_artifact(
    *,
    state_dir: Path,
    decision_id: str,
    round_id: str,
    report_id: str,
    generated_at: str,
    artifact_name: str,
    output_path: str,
    source_artifacts: dict[str, str],
) -> dict[str, Any]:
    summaries = {
        key: _gate_summary(state_dir, name, decision_id, round_id)
        for key, name in source_artifacts.items()
    }
    handoff = summaries.get("ci_observation_handoff", {})
    pending_diagnostic_keys = {"execution_log", "report_summary"}
    hard_failures = [
        key for key, summary in summaries.items()
        if summary.get("exists") and summary.get("gate_status") == "FAILED"
        and key not in pending_diagnostic_keys
    ]
    stale = [
        key for key, summary in summaries.items()
        if summary.get("exists") and not summary.get("current_round")
    ]
    observation_state = str(handoff.get("status") or "UNKNOWN")
    errors = []
    if hard_failures:
        errors.append("source artifact gate failures: " + ", ".join(hard_failures))
    if stale:
        errors.append("source artifacts are stale: " + ", ".join(stale))
    return {
        "schema_version": 1,
        "artifact_name": artifact_name,
        "gate_name": "ci-observation-reconcile",
        "gate_status": "PASSED" if not errors else "FAILED",
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "generated_at": generated_at,
        "reconcile_status": "RECONCILED" if not errors else "REWORK_REQUIRED",
        "observation_state": observation_state,
        "source_artifacts": summaries,
        "evidence_only": True,
        "executable": False,
        "can_execute": False,
        "can_dispatch": False,
        "mutates_state": False,
        "generated_artifacts": [output_path],
        "errors": errors,
        "warnings": [
            *(
                ["external CI observation is still pending"]
                if observation_state == "AWAITING_EXTERNAL_OBSERVATION"
                else []
            ),
            *[
                f"{key} is diagnostic and not yet converged"
                for key in pending_diagnostic_keys
                if summaries.get(key, {}).get("gate_status") == "FAILED"
            ],
        ],
    }


def _workflow_hits(text: str, patterns: tuple[str, ...]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            if re.search(pattern, line, flags=re.IGNORECASE):
                hits.append({"line": line_number, "pattern": pattern, "text": line.strip()})
    return hits


def build_artifact_manifest_artifact(
    *,
    workflow_texts: dict[str, str],
    decision_id: str,
    round_id: str,
    report_id: str,
    generated_at: str,
    artifact_name: str,
    output_path: str,
) -> dict[str, Any]:
    unsafe_patterns = {
        "write_permissions": (r"\bcontents:\s*write\b", r"\bpull-requests:\s*write\b", r"\bwrite-all\b"),
        "repo_mutation": (r"\bgit\s+push\b", r"\bgit\s+commit\b", r"\bgh\s+api\b", r"\bgh\s+pr\s+"),
        "external_model_call": (r"\bapi\.openai\.com\b", r"\bopenai\b", r"\banthropic\b", r"\bcopilot\b"),
    }
    required_terms = {
        "upload_artifact_action": "actions/upload-artifact@v4",
        "gate_json_export": "project_state/gates/*.json",
        "pytest_result_export": "project_state/pytest_result.txt",
    }
    combined = "\n".join(workflow_texts.values())
    observed_terms = {
        key: any(term.lower() in text.lower() for text in workflow_texts.values())
        for key, term in required_terms.items()
    }
    unsafe_hits = [
        {"id": key, "workflow": rel, "hits": hits}
        for key, patterns in unsafe_patterns.items()
        for rel, text in workflow_texts.items()
        for hits in [_workflow_hits(text, patterns)]
        if hits
    ]
    missing = [key for key, present in observed_terms.items() if not present]
    read_only_permissions = "contents: read" in combined.lower() and "contents: write" not in combined.lower()
    if not read_only_permissions:
        missing.append("read_only_contents_permission")
    errors = []
    if missing:
        errors.append("artifact export expectations missing: " + ", ".join(sorted(set(missing))))
    if unsafe_hits:
        errors.append("unsafe workflow artifact/export patterns found")
    return {
        "schema_version": 1,
        "artifact_name": artifact_name,
        "gate_name": "ci-artifact-manifest",
        "gate_status": "PASSED" if not errors else "FAILED",
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "generated_at": generated_at,
        "manifest_status": "READY" if not errors else "REWORK_REQUIRED",
        "required_export_terms": required_terms,
        "observed_export_terms": observed_terms,
        "read_only_permissions": read_only_permissions,
        "unsafe_patterns_found": unsafe_hits,
        "evidence_only": True,
        "executable": False,
        "can_execute": False,
        "can_dispatch": False,
        "mutates_state": False,
        "generated_artifacts": [output_path],
        "errors": errors,
        "warnings": [],
    }


def build_audit_handoff_bundle_artifact(
    *,
    state_dir: Path,
    decision_id: str,
    round_id: str,
    report_id: str,
    generated_at: str,
    artifact_name: str,
    output_path: str,
    source_artifacts: dict[str, str],
) -> dict[str, Any]:
    summaries = {
        key: _gate_summary(state_dir, name, decision_id, round_id)
        for key, name in source_artifacts.items()
    }
    pending_diagnostic_keys = {"execution_log", "report_summary", "final_check", "run_closeout"}
    failed = [
        key for key, summary in summaries.items()
        if summary.get("gate_status") == "FAILED" and key not in pending_diagnostic_keys
    ]
    missing = [key for key, summary in summaries.items() if not summary.get("exists")]
    return {
        "schema_version": 1,
        "artifact_name": artifact_name,
        "gate_name": "ci-audit-handoff-bundle",
        "gate_status": "PASSED" if not failed else "FAILED",
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "generated_at": generated_at,
        "handoff_status": "READY_FOR_AUDIT" if not failed else "REWORK_REQUIRED",
        "source_artifacts": summaries,
        "audit_summary": {
            "failed_sources": failed,
            "missing_sources": missing,
            "external_observation_pending": summaries.get("ci_observation_handoff", {}).get("status")
            == "AWAITING_EXTERNAL_OBSERVATION",
            "pending_diagnostic_sources": [
                key for key in sorted(pending_diagnostic_keys)
                if summaries.get(key, {}).get("gate_status") == "FAILED"
                or summaries.get(key, {}).get("status") == "FAILED"
            ],
        },
        "evidence_only": True,
        "executable": False,
        "can_execute": False,
        "can_dispatch": False,
        "mutates_state": False,
        "generated_artifacts": [output_path],
        "errors": ["source artifact gate failures: " + ", ".join(failed)] if failed else [],
        "warnings": ["some source artifacts are not present yet: " + ", ".join(missing)] if missing else [],
    }
