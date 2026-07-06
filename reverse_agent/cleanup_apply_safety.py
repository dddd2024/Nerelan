"""Dry-run-only cleanup-apply safety artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_context_builder import build_current_context_packet
from .project_state import read_codex_report_summary, read_decision_contract, read_decision_meta
from .project_state_manifest import build_state_manifest
from .project_workstreams import build_workstream_registry
from .state_governance import (
    build_archive_index,
    build_cleanup_plan,
    build_deletion_manifest_schema,
    build_retention_policy,
    build_state_lifecycle_registry,
    build_tombstone_schema,
)


CLEANUP_APPLY_SAFETY_SCHEMA_VERSION = 1

STATUS_POLICY_RECONCILE_PATH = "project_state/gates/status_policy_reconcile_result.json"
DOCTOR_BACKLOG_SPLIT_PATH = "project_state/gates/doctor_backlog_split_result.json"
GOVERNANCE_FIX_RESULT_PATH = "project_state/gates/governance_fix_result.json"
CLEANUP_APPLY_SAFETY_PLAN_PATH = "project_state/gates/cleanup_apply_safety_plan.json"
CLEANUP_APPLY_DRY_RUN_PATH = "project_state/gates/cleanup_apply_dry_run.json"
CLEANUP_APPLY_SAFETY_RESULT_PATH = "project_state/gates/cleanup_apply_safety_result.json"
CLEANUP_APPLY_SAFETY_SNAPSHOT_PATH = "project_state/gates/cleanup_apply_safety_snapshot.json"
DELETION_MANIFEST_VALIDATION_PATH = "project_state/gates/deletion_manifest_validation_result.json"
TOMBSTONE_VALIDATION_PATH = "project_state/gates/tombstone_validation_result.json"
ROLLBACK_HANDOFF_PLAN_PATH = "project_state/gates/rollback_handoff_plan.json"
AUDIT_HANDOFF_FOR_CLEANUP_APPLY_PATH = "project_state/gates/audit_handoff_for_cleanup_apply.json"
CLEANUP_APPLY_REVIEW_BUNDLE_PATH = "project_state/gates/cleanup_apply_review_bundle.json"
CLEANUP_APPLY_REVIEW_RESULT_PATH = "project_state/gates/cleanup_apply_review_result.json"
CLEANUP_APPLY_REVIEW_SNAPSHOT_PATH = "project_state/gates/cleanup_apply_review_snapshot.json"
CLEANUP_CANDIDATE_RISK_MATRIX_PATH = "project_state/gates/cleanup_candidate_risk_matrix.json"
CLEANUP_APPLY_APPROVAL_CHECKLIST_PATH = "project_state/gates/cleanup_apply_approval_checklist.json"
EVIDENCE_LOCK_MANIFEST_PATH = "project_state/gates/evidence_lock_manifest.json"
DELETION_MANIFEST_DRY_RUN_PATH = "project_state/gates/deletion_manifest_dry_run.json"
TOMBSTONE_PLAN_DRY_RUN_PATH = "project_state/gates/tombstone_plan_dry_run.json"

DESTRUCTIVE_RESULT_FIELDS = (
    "deleted_files",
    "moved_files",
    "archived_files",
    "compacted_archives",
    "written_tombstones",
    "real_deletion_manifests",
)

FORBIDDEN_CAPABILITIES = (
    "real_cleanup_apply",
    "file_delete",
    "file_move",
    "archive_compaction",
    "archive_apply",
    "real_tombstone_write",
    "real_deletion_manifest_write",
    "real_sample_analysis_execution",
    "real_user_upload_ingestion",
    "binary_parsing_or_unpacking",
    "external_analysis_tool_invocation",
    "candidate_search_on_real_samples",
    "runtime_validation_on_real_samples",
    "automatic_runner_dispatch",
    "manual_runner_dispatch",
    "model_api_invocation",
    "production_http_service",
    "database_or_queue",
    "scheduler_or_service",
    "remote_runner_dispatch",
    "ci_dispatch_or_polling",
    "github_workflow_modification",
    "auto_iteration",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _norm_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _identity(state_dir: Path, artifact_name: str, artifact_path: str) -> dict[str, Any]:
    decision = read_decision_meta(state_dir)
    round_id = str(decision.get("round_id") or "")
    return {
        "schema_version": CLEANUP_APPLY_SAFETY_SCHEMA_VERSION,
        "artifact_name": artifact_name,
        "artifact_path": artifact_path,
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": round_id,
        "report_id": f"codex_report_{round_id.removeprefix('round_')}" if round_id else "",
        "mainline": str(decision.get("mainline") or ""),
        "generated_at": _now_iso(),
    }


def _artifact_index_counts(state_dir: Path) -> dict[str, int]:
    artifact_index = _read_json(state_dir / "artifact_index.json")
    latest_v2 = artifact_index.get("latest_artifacts_v2")
    counts: dict[str, int] = {}
    if isinstance(latest_v2, Mapping):
        for entry in latest_v2.values():
            if not isinstance(entry, Mapping):
                continue
            freshness = str(entry.get("freshness") or "unknown")
            counts[freshness] = counts.get(freshness, 0) + 1
    for item in artifact_index.get("missing", []) if isinstance(artifact_index.get("missing"), list) else []:
        counts["missing"] = counts.get("missing", 0) + 1
    return dict(sorted(counts.items()))


def _historical_backlog_notice(counts: Mapping[str, int]) -> str:
    missing = int(counts.get("missing") or 0)
    stale = int(counts.get("stale") or 0)
    return f"{missing} missing, {stale} stale historical sample artifacts"


def _report_claims_sample_evidence(report: Mapping[str, Any]) -> bool:
    fields = (
        list(report.get("generated_artifacts") or [])
        + list(report.get("referenced_artifacts") or [])
        + list(report.get("files_changed") or [])
    )
    return any(str(item).replace("\\", "/").startswith("solve_reports/") for item in fields)


def build_status_policy_reconcile(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    decision = read_decision_meta(state_dir_path)
    report = read_codex_report_summary(state_dir_path)
    counts = _artifact_index_counts(state_dir_path)
    is_non_sample_governance = (
        str(decision.get("mainline") or "") == "project_governance"
        and not _report_claims_sample_evidence(report)
    )
    backlog_notice = _historical_backlog_notice(counts)
    classifications = []
    if counts.get("missing") or counts.get("stale"):
        classifications.append(
            {
                "issue": backlog_notice,
                "classification": "historical_backlog_notice" if is_non_sample_governance else "current_blocker",
                "blocking_for_current_governance_evidence": not is_non_sample_governance,
            }
        )
    payload = {
        **_identity(state_dir_path, "status_policy_reconcile_result.json", STATUS_POLICY_RECONCILE_PATH),
        "gate_name": "status-policy-reconcile",
        "gate_status": "PASSED" if is_non_sample_governance else "FAILED",
        "reconcile_status": "RECONCILED" if is_non_sample_governance else "BLOCKED_BY_CURRENT_SAMPLE_CLAIM",
        "current_governance_evidence_status": "PASSED" if is_non_sample_governance else "FAILED",
        "historical_backlog_blocking_current_round": False if is_non_sample_governance else True,
        "historical_sample_backlog_visible": True,
        "artifact_freshness_counts": counts,
        "issue_classifications": classifications,
        "current_evidence_claims_sample_artifacts": _report_claims_sample_evidence(report),
        "non_sample_governance_round": is_non_sample_governance,
        "generated_artifacts": [STATUS_POLICY_RECONCILE_PATH],
        "errors": [] if is_non_sample_governance else ["current report claims sample evidence"],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "status_policy_reconcile_result.json", payload)
    return payload


def build_doctor_backlog_split(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    counts = _artifact_index_counts(state_dir_path)
    backlog_notice = _historical_backlog_notice(counts)
    backlog = []
    if counts.get("missing") or counts.get("stale"):
        backlog.append(
            {
                "notice": backlog_notice,
                "classification": "historical_backlog_notice",
                "current_blocker": False,
            }
        )
    payload = {
        **_identity(state_dir_path, "doctor_backlog_split_result.json", DOCTOR_BACKLOG_SPLIT_PATH),
        "gate_name": "doctor-backlog-split",
        "gate_status": "PASSED",
        "split_status": "PASSED",
        "current_blockers": [],
        "current_warnings": [],
        "historical_backlog_notices": backlog,
        "external_notices": [],
        "historical_sample_gaps_hidden": False,
        "historical_sample_gaps_block_current_round": False,
        "generated_artifacts": [DOCTOR_BACKLOG_SPLIT_PATH],
        "errors": [],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "doctor_backlog_split_result.json", payload)
    return payload


def build_governance_fix(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    status_reconcile = build_status_policy_reconcile(state_dir=state_dir_path, write_result=write_result)
    doctor_split = build_doctor_backlog_split(state_dir=state_dir_path, write_result=write_result)
    previous = read_decision_contract(state_dir_path)
    errors: list[str] = []
    if status_reconcile.get("gate_status") != "PASSED":
        errors.append("status policy reconcile did not pass")
    if doctor_split.get("gate_status") != "PASSED":
        errors.append("doctor backlog split did not pass")
    payload = {
        **_identity(state_dir_path, "governance_fix_result.json", GOVERNANCE_FIX_RESULT_PATH),
        "gate_name": "governance-fix",
        "gate_status": "PASSED" if not errors else "FAILED",
        "fix_status": "RESOLVED_FOR_CURRENT_GOVERNANCE_EVIDENCE" if not errors else "FAILED",
        "previous_accepted_with_limitations_round_id": str(previous.get("follows_last_accepted_round_id") or ""),
        "previous_limitation_resolved_for_current_non_sample_governance": not errors,
        "historical_sample_backlog_hidden": False,
        "historical_sample_backlog_blocking_current_round": False,
        "status_policy_reconcile_path": STATUS_POLICY_RECONCILE_PATH,
        "doctor_backlog_split_path": DOCTOR_BACKLOG_SPLIT_PATH,
        "generated_artifacts": [
            STATUS_POLICY_RECONCILE_PATH,
            DOCTOR_BACKLOG_SPLIT_PATH,
            GOVERNANCE_FIX_RESULT_PATH,
        ],
        "errors": errors,
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "governance_fix_result.json", payload)
    return payload


def _dry_run_candidates(cleanup_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in cleanup_plan.get("future_candidates", []) if isinstance(cleanup_plan.get("future_candidates"), list) else []:
        if not isinstance(item, Mapping):
            continue
        candidates.append(
            {
                "path": str(item.get("path") or ""),
                "retention_class": str(item.get("retention_class") or ""),
                "simulated_action": str(item.get("recommended_action") or "delete-candidate"),
                "real_action_allowed": False,
                "delete_allowed_now": False,
                "requires_future_cleanup_apply_decision": True,
                "requires_tombstone_if_deleted": True,
            }
        )
    return candidates


def build_cleanup_apply_safety_plan(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    cleanup_plan = build_cleanup_plan(state_dir=state_dir_path, write_result=write_result)[0]
    candidates = _dry_run_candidates(cleanup_plan)
    payload = {
        **_identity(state_dir_path, "cleanup_apply_safety_plan.json", CLEANUP_APPLY_SAFETY_PLAN_PATH),
        "gate_name": "cleanup-apply-safety-plan",
        "plan_status": "READY_FOR_DRY_RUN_ONLY",
        "real_cleanup_apply": False,
        "cleanup_apply_allowed": False,
        "dry_run_candidate_count": len(candidates),
        "dry_run_candidates": candidates,
        "future_cleanup_apply_required_preconditions": [
            "separate APPROVED cleanup-apply decision",
            "command-plan authorization for cleanup apply",
            "accepted deletion manifest",
            "accepted tombstone plan",
            "rollback handoff",
            "audit handoff",
            "final-check with real cleanup capability explicitly allowed",
        ],
        "generated_artifacts": [CLEANUP_APPLY_SAFETY_PLAN_PATH, "project_state/gates/cleanup_plan.json", "project_state/gates/cleanup_plan_summary.json"],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "cleanup_apply_safety_plan.json", payload)
    return payload


def build_cleanup_apply_dry_run(
    *,
    state_dir: str | Path = "project_state",
    safety_plan: Mapping[str, Any] | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    plan = safety_plan or build_cleanup_apply_safety_plan(state_dir=state_dir_path, write_result=write_result)
    payload = {
        **_identity(state_dir_path, "cleanup_apply_dry_run.json", CLEANUP_APPLY_DRY_RUN_PATH),
        "gate_name": "cleanup-apply-dry-run",
        "dry_run_status": "PASSED",
        "real_cleanup_apply": False,
        "cleanup_apply_executed": False,
        "dry_run_only": True,
        "candidates": list(plan.get("dry_run_candidates") or []),
        **{field: [] for field in DESTRUCTIVE_RESULT_FIELDS},
        "generated_artifacts": [CLEANUP_APPLY_DRY_RUN_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "cleanup_apply_dry_run.json", payload)
    return payload


def build_deletion_manifest_validation(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    schema = build_deletion_manifest_schema(state_dir=state_dir_path, write_result=write_result)
    example = {
        "future_decision_id": "future_cleanup_apply_decision_required",
        "future_round_id": "future_cleanup_apply_round_required",
        "original_path": "DRY_RUN_EXAMPLE_ONLY",
        "original_sha256": "0" * 64,
        "reason": "dry-run schema validation example",
        "retention_class": "transient_closeout_log",
        "audit_approval": "required_in_future_round",
        "tombstone_target": "required_in_future_round",
    }
    missing = [field for field in schema.get("required_fields", []) if field not in example]
    payload = {
        **_identity(state_dir_path, "deletion_manifest_validation_result.json", DELETION_MANIFEST_VALIDATION_PATH),
        "gate_name": "deletion-manifest-validation",
        "validation_status": "PASSED" if not missing else "FAILED",
        "schema_only": True,
        "dry_run_only": True,
        "real_deletion_payload": False,
        "example_payload": example,
        "missing_required_fields": missing,
        "generated_artifacts": [DELETION_MANIFEST_VALIDATION_PATH, "project_state/gates/deletion_manifest_schema.json"],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "deletion_manifest_validation_result.json", payload)
    return payload


def build_tombstone_validation(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    schema = build_tombstone_schema(state_dir=state_dir_path, write_result=write_result)
    example = {
        "original_path": "DRY_RUN_EXAMPLE_ONLY",
        "deleted_sha256": "0" * 64,
        "deletion_manifest_id": "future_manifest_required",
        "deletion_round_id": "future_cleanup_apply_round_required",
        "deletion_timestamp_utc": "future_timestamp_required",
        "reason": "dry-run schema validation example",
        "restore_notes": "future rollback plan required",
        "audit_notes": "future audit handoff required",
    }
    missing = [field for field in schema.get("required_fields", []) if field not in example]
    payload = {
        **_identity(state_dir_path, "tombstone_validation_result.json", TOMBSTONE_VALIDATION_PATH),
        "gate_name": "tombstone-validation",
        "validation_status": "PASSED" if not missing else "FAILED",
        "schema_only": True,
        "dry_run_only": True,
        "real_tombstone_payload": False,
        "example_payload": example,
        "missing_required_fields": missing,
        "generated_artifacts": [TOMBSTONE_VALIDATION_PATH, "project_state/gates/tombstone_schema.json"],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "tombstone_validation_result.json", payload)
    return payload


def build_rollback_handoff_plan(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    payload = {
        **_identity(state_dir_path, "rollback_handoff_plan.json", ROLLBACK_HANDOFF_PLAN_PATH),
        "gate_name": "rollback-handoff-plan",
        "handoff_status": "READY_FOR_FUTURE_DECISION",
        "future_cleanup_apply_requires_separate_decision": True,
        "required_future_inputs": [
            "per-file original hashes",
            "accepted deletion manifest",
            "accepted tombstone plan",
            "restore notes for every candidate",
            "final-check before and after cleanup apply",
        ],
        "real_cleanup_apply_this_round": False,
        "generated_artifacts": [ROLLBACK_HANDOFF_PLAN_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "rollback_handoff_plan.json", payload)
    return payload


def build_audit_handoff_for_cleanup_apply(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    payload = {
        **_identity(state_dir_path, "audit_handoff_for_cleanup_apply.json", AUDIT_HANDOFF_FOR_CLEANUP_APPLY_PATH),
        "gate_name": "audit-handoff-for-cleanup-apply",
        "handoff_status": "READY_FOR_FUTURE_AUDIT",
        "future_cleanup_apply_requires_separate_decision": True,
        "future_cleanup_apply_requires_audit": True,
        "audit_requirements": [
            "review deletion manifest",
            "review tombstone plan",
            "review rollback handoff",
            "verify command-plan explicitly authorizes real cleanup apply",
            "verify forbidden protected evidence remains untouched",
        ],
        "real_cleanup_apply_this_round": False,
        "generated_artifacts": [AUDIT_HANDOFF_FOR_CLEANUP_APPLY_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "audit_handoff_for_cleanup_apply.json", payload)
    return payload


def _cleanup_review_risk_matrix(cleanup_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in cleanup_plan.get("current_evidence_protection", []) if isinstance(cleanup_plan.get("current_evidence_protection"), list) else []:
        if not isinstance(item, Mapping):
            continue
        rows.append(
            {
                "path": str(item.get("path") or ""),
                "evidence_role": "current_audit_fact_source",
                "retention_class": str(item.get("retention_class") or "current_audit_fact_source"),
                "future_action": "retain",
                "risk": "critical_if_modified_or_deleted",
                "confidence": "high",
                "required_approval": "not_applicable_retain",
                "future_decision_required": False,
                "delete_allowed_now": False,
                "archive_allowed_now": False,
            }
        )
    for item in cleanup_plan.get("future_candidates", []) if isinstance(cleanup_plan.get("future_candidates"), list) else []:
        if not isinstance(item, Mapping):
            continue
        rows.append(
            {
                "path": str(item.get("path") or ""),
                "evidence_role": "future_cleanup_candidate",
                "retention_class": str(item.get("retention_class") or "unknown_requires_manual_review"),
                "future_action": str(item.get("recommended_action") or "manual-review"),
                "risk": "medium_requires_human_review",
                "confidence": "medium",
                "required_approval": "separate_cleanup_apply_decision",
                "future_decision_required": True,
                "delete_allowed_now": False,
                "archive_allowed_now": False,
            }
        )
    for item in cleanup_plan.get("missing_historical_sample_references", []) if isinstance(cleanup_plan.get("missing_historical_sample_references"), list) else []:
        if not isinstance(item, Mapping):
            continue
        rows.append(
            {
                "path": str(item.get("artifact_kind") or ""),
                "evidence_role": "historical_backlog_reference",
                "retention_class": str(item.get("retention_class") or "missing_historical_sample_reference"),
                "future_action": "retain-reference",
                "risk": "low_nonblocking_backlog_visibility",
                "confidence": "high",
                "required_approval": "not_applicable_reference_only",
                "future_decision_required": False,
                "delete_allowed_now": False,
                "archive_allowed_now": False,
            }
        )
    return rows


def build_cleanup_apply_review_bundle(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    policy = build_retention_policy(state_dir=state_dir_path, write_result=write_result)
    cleanup_plan = build_cleanup_plan(state_dir=state_dir_path, write_result=write_result)[0]
    archive_index = build_archive_index(state_dir=state_dir_path, write_result=write_result)[0]
    safety = build_cleanup_apply_safety_bundle(state_dir=state_dir_path, write_result=write_result)
    deletion_schema = build_deletion_manifest_schema(state_dir=state_dir_path, write_result=write_result)
    tombstone_schema = build_tombstone_schema(state_dir=state_dir_path, write_result=write_result)
    rollback = build_rollback_handoff_plan(state_dir=state_dir_path, write_result=write_result)
    audit = build_audit_handoff_for_cleanup_apply(state_dir=state_dir_path, write_result=write_result)
    decision_contract = read_decision_contract(state_dir_path)
    current_sources = [
        str(item.get("path") or "")
        for item in cleanup_plan.get("current_evidence_protection", [])
        if isinstance(item, Mapping)
    ]
    accepted_round = str(decision_contract.get("follows_last_accepted_round_id") or "")
    accepted_sources = [
        f"project_state/rounds/{accepted_round}/round_manifest.json",
        f"project_state/rounds/{accepted_round}/codex_execution_report.md",
        f"project_state/rounds/{accepted_round}/pytest_result.txt",
    ] if accepted_round else []
    risk_matrix_rows = _cleanup_review_risk_matrix(cleanup_plan)
    risk_matrix = {
        **_identity(state_dir_path, "cleanup_candidate_risk_matrix.json", CLEANUP_CANDIDATE_RISK_MATRIX_PATH),
        "gate_name": "cleanup-candidate-risk-matrix",
        "matrix_status": "READY_FOR_HUMAN_REVIEW",
        "rows": risk_matrix_rows,
        "delete_allowed_now": False,
        "archive_allowed_now": False,
        "generated_artifacts": [CLEANUP_CANDIDATE_RISK_MATRIX_PATH],
    }
    checklist_items = [
        {"item": "separate APPROVED cleanup-apply decision", "required": True, "satisfied_this_round": False},
        {"item": "command-plan authorizes real cleanup apply", "required": True, "satisfied_this_round": False},
        {"item": "accepted deletion manifest", "required": True, "satisfied_this_round": False},
        {"item": "accepted tombstone plan", "required": True, "satisfied_this_round": False},
        {"item": "rollback handoff reviewed", "required": True, "satisfied_this_round": False},
        {"item": "audit approval for every candidate", "required": True, "satisfied_this_round": False},
    ]
    checklist = {
        **_identity(state_dir_path, "cleanup_apply_approval_checklist.json", CLEANUP_APPLY_APPROVAL_CHECKLIST_PATH),
        "gate_name": "cleanup-apply-approval-checklist",
        "checklist_status": "FUTURE_DECISION_REQUIRED",
        "cleanup_apply_allowed_now": False,
        "items": checklist_items,
        "generated_artifacts": [CLEANUP_APPLY_APPROVAL_CHECKLIST_PATH],
    }
    evidence_lock = {
        **_identity(state_dir_path, "evidence_lock_manifest.json", EVIDENCE_LOCK_MANIFEST_PATH),
        "gate_name": "evidence-lock-manifest",
        "lock_status": "ACTIVE_FOR_CURRENT_ROUND",
        "current_audit_fact_sources": current_sources,
        "accepted_round_minimum_evidence": accepted_sources,
        "protected_from_cleanup_apply_this_round": True,
        "generated_artifacts": [EVIDENCE_LOCK_MANIFEST_PATH],
    }
    deletion_dry_run = {
        **_identity(state_dir_path, "deletion_manifest_dry_run.json", DELETION_MANIFEST_DRY_RUN_PATH),
        "gate_name": "deletion-manifest-dry-run",
        "dry_run_only": True,
        "real_deletion_manifest": False,
        "delete_allowed_now": False,
        "schema_path": "project_state/gates/deletion_manifest_schema.json",
        "entries": [
            {
                "path": row["path"],
                "retention_class": row["retention_class"],
                "future_action": row["future_action"],
                "delete_allowed_now": False,
                "future_decision_required": row["future_decision_required"],
            }
            for row in risk_matrix_rows
            if row["future_action"] == "delete-candidate"
        ],
        "generated_artifacts": [DELETION_MANIFEST_DRY_RUN_PATH],
    }
    tombstone_dry_run = {
        **_identity(state_dir_path, "tombstone_plan_dry_run.json", TOMBSTONE_PLAN_DRY_RUN_PATH),
        "gate_name": "tombstone-plan-dry-run",
        "dry_run_only": True,
        "real_tombstone_write": False,
        "schema_path": "project_state/gates/tombstone_schema.json",
        "planned_tombstones": [
            {
                "path": item["path"],
                "would_write_tombstone": False,
                "future_cleanup_apply_required": True,
            }
            for item in deletion_dry_run["entries"]
        ],
        "generated_artifacts": [TOMBSTONE_PLAN_DRY_RUN_PATH],
    }
    errors: list[str] = []
    if any(row["delete_allowed_now"] or row["archive_allowed_now"] for row in risk_matrix_rows):
        errors.append("risk matrix allows immediate cleanup action")
    if deletion_dry_run["real_deletion_manifest"] is not False or deletion_dry_run["delete_allowed_now"] is not False:
        errors.append("deletion dry-run is not safe")
    if tombstone_dry_run["real_tombstone_write"] is not False:
        errors.append("tombstone dry-run allows real writes")
    if safety.get("gate_status") != "PASSED":
        errors.append("cleanup apply safety bundle did not pass")
    review_bundle = {
        **_identity(state_dir_path, "cleanup_apply_review_bundle.json", CLEANUP_APPLY_REVIEW_BUNDLE_PATH),
        "gate_name": "cleanup-apply-review-bundle",
        "bundle_status": "READY_FOR_HUMAN_REVIEW" if not errors else "FAILED",
        "advisory_readiness_only": True,
        "real_cleanup_apply": False,
        "cleanup_apply_allowed_now": False,
        "policy_path": "project_state/retention_policy.json",
        "cleanup_plan_path": "project_state/gates/cleanup_plan.json",
        "archive_index_path": "project_state/gates/archive_index.json",
        "deletion_schema_path": str(deletion_schema.get("artifact_path") or ""),
        "tombstone_schema_path": str(tombstone_schema.get("artifact_path") or ""),
        "safety_result_path": str(safety.get("artifact_path") or CLEANUP_APPLY_SAFETY_RESULT_PATH),
        "rollback_handoff_path": str(rollback.get("artifact_path") or ROLLBACK_HANDOFF_PLAN_PATH),
        "audit_handoff_path": str(audit.get("artifact_path") or AUDIT_HANDOFF_FOR_CLEANUP_APPLY_PATH),
        "risk_matrix_path": CLEANUP_CANDIDATE_RISK_MATRIX_PATH,
        "approval_checklist_path": CLEANUP_APPLY_APPROVAL_CHECKLIST_PATH,
        "evidence_lock_manifest_path": EVIDENCE_LOCK_MANIFEST_PATH,
        "delete_allowed_now": False,
        "archive_allowed_now": False,
        "unknown_entries_require_manual_review": True,
        "generated_artifacts": [CLEANUP_APPLY_REVIEW_BUNDLE_PATH],
    }
    result = {
        **_identity(state_dir_path, "cleanup_apply_review_result.json", CLEANUP_APPLY_REVIEW_RESULT_PATH),
        "gate_name": "cleanup-apply-review",
        "gate_status": "PASSED" if not errors else "FAILED",
        "review_status": "READY_FOR_HUMAN_REVIEW" if not errors else "FAILED",
        "advisory_readiness_only": True,
        "real_cleanup_apply": False,
        "cleanup_apply_allowed_now": False,
        "candidate_count": len(risk_matrix_rows),
        "cleanup_plan_status": cleanup_plan.get("plan_status"),
        "archive_index_status": archive_index.get("index_status"),
        "retention_policy_status": policy.get("policy_status"),
        "checks": [
            {"name": "safety_bundle_passed", "status": "PASS" if safety.get("gate_status") == "PASSED" else "FAIL"},
            {"name": "risk_matrix_no_immediate_actions", "status": "PASS"},
            {"name": "future_approval_required", "status": "PASS"},
            {"name": "evidence_lock_present", "status": "PASS" if current_sources else "FAIL"},
            {"name": "dry_run_manifest_and_tombstone_only", "status": "PASS"},
        ],
        "errors": errors,
        "generated_artifacts": [
            CLEANUP_APPLY_REVIEW_BUNDLE_PATH,
            CLEANUP_APPLY_REVIEW_RESULT_PATH,
            CLEANUP_APPLY_REVIEW_SNAPSHOT_PATH,
            CLEANUP_CANDIDATE_RISK_MATRIX_PATH,
            CLEANUP_APPLY_APPROVAL_CHECKLIST_PATH,
            EVIDENCE_LOCK_MANIFEST_PATH,
            DELETION_MANIFEST_DRY_RUN_PATH,
            TOMBSTONE_PLAN_DRY_RUN_PATH,
        ],
    }
    snapshot = {
        **_identity(state_dir_path, "cleanup_apply_review_snapshot.json", CLEANUP_APPLY_REVIEW_SNAPSHOT_PATH),
        "gate_status": result["gate_status"],
        "candidate_count": len(risk_matrix_rows),
        "current_audit_fact_source_count": len(current_sources),
        "accepted_round_minimum_evidence_count": len(accepted_sources),
        "real_cleanup_apply": False,
        "delete_allowed_now": False,
        "archive_allowed_now": False,
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "cleanup_candidate_risk_matrix.json", risk_matrix)
        _write_json(state_dir_path / "gates" / "cleanup_apply_approval_checklist.json", checklist)
        _write_json(state_dir_path / "gates" / "evidence_lock_manifest.json", evidence_lock)
        _write_json(state_dir_path / "gates" / "deletion_manifest_dry_run.json", deletion_dry_run)
        _write_json(state_dir_path / "gates" / "tombstone_plan_dry_run.json", tombstone_dry_run)
        _write_json(state_dir_path / "gates" / "cleanup_apply_review_bundle.json", review_bundle)
        _write_json(state_dir_path / "gates" / "cleanup_apply_review_snapshot.json", snapshot)
        _write_json(state_dir_path / "gates" / "cleanup_apply_review_result.json", result)
    return result


def validate_cleanup_apply_review_result(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("gate_status") != "PASSED":
        errors.append("cleanup apply review gate did not pass")
    if payload.get("advisory_readiness_only") is not True:
        errors.append("review must be advisory/readiness only")
    if payload.get("real_cleanup_apply") is not False:
        errors.append("real_cleanup_apply must be false")
    if payload.get("cleanup_apply_allowed_now") is not False:
        errors.append("cleanup_apply_allowed_now must be false")
    generated = {str(item) for item in payload.get("generated_artifacts", [])}
    required = {
        CLEANUP_APPLY_REVIEW_BUNDLE_PATH,
        CLEANUP_APPLY_REVIEW_RESULT_PATH,
        CLEANUP_APPLY_REVIEW_SNAPSHOT_PATH,
        CLEANUP_CANDIDATE_RISK_MATRIX_PATH,
        CLEANUP_APPLY_APPROVAL_CHECKLIST_PATH,
        EVIDENCE_LOCK_MANIFEST_PATH,
        DELETION_MANIFEST_DRY_RUN_PATH,
        TOMBSTONE_PLAN_DRY_RUN_PATH,
    }
    missing = sorted(required - generated)
    if missing:
        errors.append(f"generated_artifacts missing: {missing}")
    return errors


def validate_cleanup_apply_safety_bundle(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("gate_status") != "PASSED":
        errors.append("cleanup apply safety gate did not pass")
    if payload.get("real_cleanup_apply") is not False:
        errors.append("real_cleanup_apply must be false")
    if payload.get("dry_run_only") is not True:
        errors.append("dry_run_only must be true")
    for field in DESTRUCTIVE_RESULT_FIELDS:
        if payload.get(field) != []:
            errors.append(f"{field} must be empty")
    forbidden = payload.get("forbidden_capabilities") if isinstance(payload.get("forbidden_capabilities"), Mapping) else {}
    enabled = sorted(name for name, value in forbidden.items() if value is not False)
    if enabled:
        errors.append(f"forbidden capabilities enabled: {enabled}")
    required = {
        STATUS_POLICY_RECONCILE_PATH,
        DOCTOR_BACKLOG_SPLIT_PATH,
        GOVERNANCE_FIX_RESULT_PATH,
        CLEANUP_APPLY_SAFETY_PLAN_PATH,
        CLEANUP_APPLY_DRY_RUN_PATH,
        CLEANUP_APPLY_SAFETY_RESULT_PATH,
        CLEANUP_APPLY_SAFETY_SNAPSHOT_PATH,
        DELETION_MANIFEST_VALIDATION_PATH,
        TOMBSTONE_VALIDATION_PATH,
        ROLLBACK_HANDOFF_PLAN_PATH,
        AUDIT_HANDOFF_FOR_CLEANUP_APPLY_PATH,
    }
    generated = {str(item) for item in payload.get("generated_artifacts", [])}
    missing = sorted(required - generated)
    if missing:
        errors.append(f"generated_artifacts missing: {missing}")
    return errors


def build_cleanup_apply_safety_bundle(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    policy = build_retention_policy(state_dir=state_dir_path, write_result=write_result)
    cleanup_plan = build_cleanup_plan(state_dir=state_dir_path, write_result=write_result)[0]
    archive_index = build_archive_index(state_dir=state_dir_path, write_result=write_result)[0]
    lifecycle = build_state_lifecycle_registry(
        state_dir=state_dir_path,
        retention_policy=policy,
        cleanup_plan=cleanup_plan,
        archive_index=archive_index,
        write_result=write_result,
    )
    status_reconcile = build_status_policy_reconcile(state_dir=state_dir_path, write_result=write_result)
    doctor_split = build_doctor_backlog_split(state_dir=state_dir_path, write_result=write_result)
    governance_fix = build_governance_fix(state_dir=state_dir_path, write_result=write_result)
    safety_plan = build_cleanup_apply_safety_plan(state_dir=state_dir_path, write_result=write_result)
    dry_run = build_cleanup_apply_dry_run(state_dir=state_dir_path, safety_plan=safety_plan, write_result=write_result)
    deletion_validation = build_deletion_manifest_validation(state_dir=state_dir_path, write_result=write_result)
    tombstone_validation = build_tombstone_validation(state_dir=state_dir_path, write_result=write_result)
    rollback = build_rollback_handoff_plan(state_dir=state_dir_path, write_result=write_result)
    audit = build_audit_handoff_for_cleanup_apply(state_dir=state_dir_path, write_result=write_result)
    manifest = build_state_manifest(state_dir=state_dir_path, write_result=write_result)
    context = build_current_context_packet(state_dir=state_dir_path, write_result=write_result)
    workstreams = build_workstream_registry(state_dir=state_dir_path, write_result=write_result)

    errors: list[str] = []
    for name, payload in (
        ("status_policy_reconcile", status_reconcile),
        ("doctor_backlog_split", doctor_split),
        ("governance_fix", governance_fix),
    ):
        if payload.get("gate_status") != "PASSED":
            errors.append(f"{name} did not pass")
    for name, payload in (
        ("deletion_manifest_validation", deletion_validation),
        ("tombstone_validation", tombstone_validation),
    ):
        if payload.get("validation_status") != "PASSED":
            errors.append(f"{name} did not pass")
    for item in dry_run.get("candidates", []):
        if isinstance(item, Mapping) and item.get("real_action_allowed") is not False:
            errors.append("dry-run candidate allows real action")
    destructive_counts = {field: len(dry_run.get(field) or []) for field in DESTRUCTIVE_RESULT_FIELDS}
    if any(destructive_counts.values()):
        errors.append("dry-run produced destructive results")

    forbidden_capabilities = {name: False for name in FORBIDDEN_CAPABILITIES}
    generated_artifacts = [
        "project_state/retention_policy.json",
        "project_state/state_lifecycle_registry.json",
        "project_state/gates/cleanup_plan.json",
        "project_state/gates/cleanup_plan_summary.json",
        "project_state/gates/archive_index.json",
        "project_state/gates/archive_index_summary.json",
        "project_state/gates/deletion_manifest_schema.json",
        "project_state/gates/tombstone_schema.json",
        STATUS_POLICY_RECONCILE_PATH,
        DOCTOR_BACKLOG_SPLIT_PATH,
        GOVERNANCE_FIX_RESULT_PATH,
        CLEANUP_APPLY_SAFETY_PLAN_PATH,
        CLEANUP_APPLY_DRY_RUN_PATH,
        CLEANUP_APPLY_SAFETY_RESULT_PATH,
        CLEANUP_APPLY_SAFETY_SNAPSHOT_PATH,
        DELETION_MANIFEST_VALIDATION_PATH,
        TOMBSTONE_VALIDATION_PATH,
        ROLLBACK_HANDOFF_PLAN_PATH,
        AUDIT_HANDOFF_FOR_CLEANUP_APPLY_PATH,
        "project_state/state_manifest.json",
        "project_state/context/current_context_packet.json",
        "project_state/roadmap/workstreams.json",
    ]
    checks = [
        {
            "name": "status_policy_reconcile",
            "status": "PASS" if status_reconcile.get("gate_status") == "PASSED" else "FAIL",
        },
        {
            "name": "doctor_backlog_split",
            "status": "PASS" if doctor_split.get("gate_status") == "PASSED" else "FAIL",
        },
        {
            "name": "cleanup_apply_dry_run_noop",
            "status": "PASS" if not any(destructive_counts.values()) and dry_run.get("real_cleanup_apply") is False else "FAIL",
            "destructive_action_counts": destructive_counts,
        },
        {
            "name": "manifest_and_tombstone_validation",
            "status": "PASS" if deletion_validation.get("validation_status") == "PASSED" and tombstone_validation.get("validation_status") == "PASSED" else "FAIL",
        },
        {
            "name": "rollback_and_audit_handoff",
            "status": "PASS" if rollback.get("future_cleanup_apply_requires_separate_decision") is True and audit.get("future_cleanup_apply_requires_audit") is True else "FAIL",
        },
    ]
    result = {
        **_identity(state_dir_path, "cleanup_apply_safety_result.json", CLEANUP_APPLY_SAFETY_RESULT_PATH),
        "gate_name": "cleanup-apply-safety",
        "gate_status": "PASSED" if not errors else "FAILED",
        "checks": checks,
        "errors": errors,
        "real_cleanup_apply": False,
        "dry_run_only": True,
        "cleanup_apply_allowed": False,
        "forbidden_capabilities": forbidden_capabilities,
        "destructive_action_counts": destructive_counts,
        **{field: [] for field in DESTRUCTIVE_RESULT_FIELDS},
        "generated_artifacts": generated_artifacts,
        "artifact_path": CLEANUP_APPLY_SAFETY_RESULT_PATH,
        "snapshot_path": CLEANUP_APPLY_SAFETY_SNAPSHOT_PATH,
        "no_concrete_sample_claims": True,
    }
    snapshot = {
        **_identity(state_dir_path, "cleanup_apply_safety_snapshot.json", CLEANUP_APPLY_SAFETY_SNAPSHOT_PATH),
        "gate_status": result["gate_status"],
        "fix_status": governance_fix.get("fix_status"),
        "dry_run_status": dry_run.get("dry_run_status"),
        "deletion_manifest_validation_status": deletion_validation.get("validation_status"),
        "tombstone_validation_status": tombstone_validation.get("validation_status"),
        "rollback_handoff_status": rollback.get("handoff_status"),
        "audit_handoff_status": audit.get("handoff_status"),
        "lifecycle_registry_status": lifecycle.get("registry_status"),
        "state_manifest_decision_id": manifest.get("decision_id"),
        "context_packet_decision_id": context.get("decision_id"),
        "active_workstreams": [
            str(item.get("workstream_id") or "")
            for item in workstreams.get("workstreams", [])
            if isinstance(item, Mapping) and item.get("status") == "ACTIVE_ROUND"
        ],
        "real_cleanup_apply": False,
        "destructive_action_counts": destructive_counts,
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "cleanup_apply_safety_snapshot.json", snapshot)
        _write_json(state_dir_path / "gates" / "cleanup_apply_safety_result.json", result)
    return result
