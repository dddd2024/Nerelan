"""Non-destructive state governance bundle artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_state import read_decision_contract, read_decision_meta
from .project_context_builder import build_current_context_packet
from .project_state_manifest import build_state_manifest
from .project_workstreams import build_workstream_registry


STATE_GOVERNANCE_SCHEMA_VERSION = 1
RETENTION_POLICY_PATH = "project_state/retention_policy.json"
STATE_LIFECYCLE_REGISTRY_PATH = "project_state/state_lifecycle_registry.json"
CLEANUP_PLAN_PATH = "project_state/gates/cleanup_plan.json"
CLEANUP_PLAN_SUMMARY_PATH = "project_state/gates/cleanup_plan_summary.json"
ARCHIVE_INDEX_PATH = "project_state/gates/archive_index.json"
ARCHIVE_INDEX_SUMMARY_PATH = "project_state/gates/archive_index_summary.json"
DELETION_MANIFEST_SCHEMA_PATH = "project_state/gates/deletion_manifest_schema.json"
TOMBSTONE_SCHEMA_PATH = "project_state/gates/tombstone_schema.json"
RETENTION_POLICY_VALIDATION_PATH = "project_state/gates/retention_policy_validation.json"
STATE_GOVERNANCE_BUNDLE_RESULT_PATH = "project_state/gates/state_governance_bundle_result.json"
STATE_GOVERNANCE_BUNDLE_SNAPSHOT_PATH = "project_state/gates/state_governance_bundle_snapshot.json"

RETENTION_CLASSES = (
    "current_audit_fact_source",
    "accepted_round_minimum_evidence",
    "current_generated_governance_index",
    "current_gate_artifact",
    "historical_nonblocking_gate_artifact",
    "historical_sample_reference",
    "missing_historical_sample_reference",
    "transient_closeout_log",
    "transient_closeout_pid",
    "documentation",
    "configuration",
    "unknown_requires_manual_review",
    "disposable_candidate_requires_future_decision",
)

DESTRUCTIVE_ARRAY_FIELDS = (
    "deleted_files",
    "moved_files",
    "archived_files",
    "compacted_archives",
    "written_tombstones",
)

FORBIDDEN_CAPABILITIES = (
    "cleanup_apply",
    "file_delete",
    "file_move",
    "archive_compaction",
    "archive_apply",
    "tombstone_write_for_real_deletion",
    "real_deletion_manifest_write",
    "real_sample_analysis_execution",
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


def _file_ref(state_dir: Path, rel: str, role: str) -> dict[str, Any]:
    path = state_dir / rel
    return {
        "path": _norm_path(Path("project_state") / rel),
        "exists": path.exists(),
        "role": role,
        "sha256": _sha256_file(path) if path.exists() else "",
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def _identity(state_dir: Path) -> dict[str, str]:
    decision = read_decision_meta(state_dir)
    round_id = str(decision.get("round_id") or "")
    return {
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": round_id,
        "report_id": f"codex_report_{round_id.removeprefix('round_')}" if round_id else "",
        "mainline": str(decision.get("mainline") or ""),
    }


def _artifact_header(state_dir: Path, artifact_name: str, artifact_path: str) -> dict[str, Any]:
    ident = _identity(state_dir)
    return {
        "schema_version": STATE_GOVERNANCE_SCHEMA_VERSION,
        "artifact_name": artifact_name,
        "artifact_kind": "governance_planning_artifact",
        "artifact_path": artifact_path,
        "generated_at": _now_iso(),
        **ident,
    }


def build_retention_policy(*, state_dir: str | Path = "project_state", write_result: bool = True) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    policies: dict[str, dict[str, Any]] = {}
    for cls in RETENTION_CLASSES:
        archive_policy = "eligible_for_future_archive_plan" if cls in {
            "historical_nonblocking_gate_artifact",
            "historical_sample_reference",
            "transient_closeout_log",
            "transient_closeout_pid",
        } else "retain_in_place"
        delete_policy = "future_cleanup_apply_only" if cls in {
            "transient_closeout_log",
            "transient_closeout_pid",
            "disposable_candidate_requires_future_decision",
        } else "not_a_delete_candidate_without_future_decision"
        policies[cls] = {
            "retain_policy": "retain_current_round" if cls.startswith("current_") else "retain_until_future_decision",
            "archive_policy": archive_policy,
            "delete_policy": delete_policy,
            "future_cleanup_apply_required": True,
            "tombstone_required_if_deleted": True,
            "deletion_allowed_this_round": False,
        }
    payload = {
        **_artifact_header(state_dir_path, "retention_policy.json", RETENTION_POLICY_PATH),
        "policy_status": "ACTIVE_DESIGN_ONLY",
        "cleanup_apply_allowed": False,
        "retention_classes": policies,
        "global_rules": {
            "deletion_without_future_cleanup_apply_decision": False,
            "cleanup_plan_is_not_cleanup_apply": True,
            "real_deletion_manifest_allowed_this_round": False,
            "real_tombstone_write_allowed_this_round": False,
        },
    }
    if write_result:
        _write_json(state_dir_path / "retention_policy.json", payload)
    return payload


def _cleanup_candidate(path: str, retention_class: str, action: str, reason: str) -> dict[str, Any]:
    return {
        "path": path,
        "retention_class": retention_class,
        "recommended_action": action,
        "reason": reason,
        "delete_allowed_now": False,
        "requires_future_cleanup_apply_decision": True,
        "requires_tombstone_if_deleted": True,
    }


def build_cleanup_plan(*, state_dir: str | Path = "project_state", write_result: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    state_dir_path = Path(state_dir)
    artifact_index = _read_json(state_dir_path / "artifact_index.json")
    missing = [str(item) for item in artifact_index.get("missing", [])] if isinstance(artifact_index.get("missing"), list) else []

    transient_candidates = []
    gates_dir = state_dir_path / "gates"
    for pattern, cls in (("run_closeout_*.out.log", "transient_closeout_log"), ("run_closeout_*.err.log", "transient_closeout_log"), ("run_closeout_*.pid", "transient_closeout_pid")):
        for path in sorted(gates_dir.glob(pattern)):
            transient_candidates.append(
                _cleanup_candidate(
                    _norm_path(Path("project_state") / "gates" / path.name),
                    cls,
                    "delete-candidate",
                    "transient closeout side file; future cleanup-apply may remove after accepted deletion manifest",
                )
            )

    protected_paths = [
        "project_state/decision_packet.md",
        "project_state/codex_execution_report.md",
        "project_state/execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/command_plan.json",
        "project_state/gates/execution_log.json",
        "project_state/gates/final_gate_result.json",
        "project_state/gates/run_closeout_result.json",
        "project_state/state_manifest.json",
        "project_state/context/current_context_packet.json",
        "project_state/roadmap/workstreams.json",
    ]
    protected = [
        {
            "path": path,
            "retention_class": "current_audit_fact_source" if "project_state/gates" not in path else "current_gate_artifact",
            "recommended_action": "retain",
            "delete_allowed_now": False,
            "requires_future_cleanup_apply_decision": False,
            "requires_tombstone_if_deleted": True,
        }
        for path in protected_paths
    ]
    missing_refs = [
        {
            "artifact_kind": item,
            "retention_class": "missing_historical_sample_reference",
            "recommended_action": "retain-reference",
            "blocking_for_current_round": False,
            "delete_allowed_now": False,
            "requires_future_cleanup_apply_decision": False,
            "requires_tombstone_if_deleted": False,
        }
        for item in missing
    ]
    plan = {
        **_artifact_header(state_dir_path, "cleanup_plan.json", CLEANUP_PLAN_PATH),
        "plan_status": "PLANNING_ONLY",
        "cleanup_apply_allowed": False,
        "deleted_files": [],
        "moved_files": [],
        "archived_files": [],
        "compacted_archives": [],
        "written_tombstones": [],
        "current_evidence_protection": protected,
        "future_candidates": transient_candidates,
        "missing_historical_sample_references": missing_refs,
        "recommendation_classes": ["retain", "archive-candidate", "delete-candidate"],
        "assertions": {
            "no_destructive_operation_performed": True,
            "no_candidate_delete_allowed_now": True,
            "historical_sample_missing_artifacts_are_nonblocking": True,
        },
    }
    summary = {
        **_artifact_header(state_dir_path, "cleanup_plan_summary.json", CLEANUP_PLAN_SUMMARY_PATH),
        "plan_status": plan["plan_status"],
        "cleanup_apply_allowed": False,
        "protected_current_evidence_count": len(protected),
        "future_candidate_count": len(transient_candidates),
        "missing_historical_sample_reference_count": len(missing_refs),
        "destructive_action_counts": {field: len(plan[field]) for field in DESTRUCTIVE_ARRAY_FIELDS},
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "cleanup_plan.json", plan)
        _write_json(state_dir_path / "gates" / "cleanup_plan_summary.json", summary)
    return plan, summary


def build_archive_index(*, state_dir: str | Path = "project_state", write_result: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    state_dir_path = Path(state_dir)
    contract = read_decision_contract(state_dir_path)
    current_round = str(read_decision_meta(state_dir_path).get("round_id") or "")
    previous_round = str(contract.get("follows_last_accepted_round_id") or "")
    historical_hygiene = [
        "project_state/gates/state_hygiene_inventory.json",
        "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/decision_packet.md",
        "project_state/rounds/round_20260623_naming_hygiene_inventory_v1/decision_packet.md",
        "project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/decision_packet.md",
    ]
    entries: list[dict[str, Any]] = []
    current_outputs = [
        RETENTION_POLICY_PATH,
        STATE_LIFECYCLE_REGISTRY_PATH,
        CLEANUP_PLAN_PATH,
        CLEANUP_PLAN_SUMMARY_PATH,
        ARCHIVE_INDEX_PATH,
        ARCHIVE_INDEX_SUMMARY_PATH,
        DELETION_MANIFEST_SCHEMA_PATH,
        TOMBSTONE_SCHEMA_PATH,
        STATE_GOVERNANCE_BUNDLE_RESULT_PATH,
        STATE_GOVERNANCE_BUNDLE_SNAPSHOT_PATH,
        "project_state/gates/cleanup_apply_review_bundle.json",
        "project_state/gates/cleanup_apply_review_result.json",
        "project_state/gates/cleanup_apply_review_snapshot.json",
        "project_state/gates/cleanup_candidate_risk_matrix.json",
        "project_state/gates/cleanup_apply_approval_checklist.json",
        "project_state/gates/evidence_lock_manifest.json",
        "project_state/gates/deletion_manifest_dry_run.json",
        "project_state/gates/tombstone_plan_dry_run.json",
        "project_state/gates/round_compaction_plan.json",
        "project_state/gates/round_compaction_dry_run.json",
        "project_state/gates/round_compaction_manifest_dry_run.json",
        "project_state/gates/state_index_readiness_schema.json",
        "project_state/gates/state_index_readiness_plan.json",
        "project_state/gates/state_index_readiness_result.json",
        "project_state/gates/state_hygiene_dashboard_feed.json",
        "project_state/gates/state_hygiene_dashboard_summary.json",
        "project_state/gates/lifecycle_transition_guard_result.json",
        "project_state/gates/governance_operations_bundle_result.json",
        "project_state/gates/governance_operations_bundle_snapshot.json",
    ]
    for path in current_outputs:
        rel = path.removeprefix("project_state/")
        entries.append({**_file_ref(state_dir_path, rel, "current"), "archive_role": "current"})
    if previous_round:
        entries.append({
            **_file_ref(state_dir_path, f"rounds/{previous_round}/round_manifest.json", "archived"),
            "archive_role": "accepted_round_minimum_evidence",
        })
    for path in historical_hygiene:
        entries.append({
            **_file_ref(state_dir_path, path.removeprefix("project_state/"), "historical_nonblocking"),
            "archive_role": "historical_nonblocking",
        })
    index = {
        **_artifact_header(state_dir_path, "archive_index.json", ARCHIVE_INDEX_PATH),
        "index_status": "BOUNDED_INDEX_ONLY",
        "bounded_sources": [
            "current round output list",
            "previous accepted round manifest",
            "known historical state hygiene decision packets",
            "state_manifest artifact roles",
            "report_summary artifact roles",
        ],
        "full_solve_reports_scan": False,
        "recursive_rounds_scan": False,
        "current_round_id": current_round,
        "previous_accepted_round_id": previous_round,
        "entries": entries,
    }
    role_counts: dict[str, int] = {}
    for entry in entries:
        role = str(entry.get("archive_role") or "unknown")
        role_counts[role] = role_counts.get(role, 0) + 1
    summary = {
        **_artifact_header(state_dir_path, "archive_index_summary.json", ARCHIVE_INDEX_SUMMARY_PATH),
        "index_status": index["index_status"],
        "entry_count": len(entries),
        "role_counts": dict(sorted(role_counts.items())),
        "full_solve_reports_scan": False,
        "recursive_rounds_scan": False,
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "archive_index.json", index)
        _write_json(state_dir_path / "gates" / "archive_index_summary.json", summary)
    return index, summary


def build_deletion_manifest_schema(*, state_dir: str | Path = "project_state", write_result: bool = True) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    payload = {
        **_artifact_header(state_dir_path, "deletion_manifest_schema.json", DELETION_MANIFEST_SCHEMA_PATH),
        "schema_status": "SCHEMA_ONLY",
        "real_manifest_for_actual_files": False,
        "required_fields": [
            "future_decision_id",
            "future_round_id",
            "original_path",
            "original_sha256",
            "reason",
            "retention_class",
            "audit_approval",
            "tombstone_target",
        ],
        "forbidden_this_round": ["actual_file_path_instances", "delete_allowed_now_true"],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "deletion_manifest_schema.json", payload)
    return payload


def build_tombstone_schema(*, state_dir: str | Path = "project_state", write_result: bool = True) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    payload = {
        **_artifact_header(state_dir_path, "tombstone_schema.json", TOMBSTONE_SCHEMA_PATH),
        "schema_status": "SCHEMA_ONLY",
        "real_tombstone_written": False,
        "required_fields": [
            "original_path",
            "deleted_sha256",
            "deletion_manifest_id",
            "deletion_round_id",
            "deletion_timestamp_utc",
            "reason",
            "restore_notes",
            "audit_notes",
        ],
        "forbidden_this_round": ["actual_deleted_file_record", "real_tombstone_path"],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "tombstone_schema.json", payload)
    return payload


def build_state_lifecycle_registry(
    *,
    state_dir: str | Path = "project_state",
    retention_policy: Mapping[str, Any] | None = None,
    cleanup_plan: Mapping[str, Any] | None = None,
    archive_index: Mapping[str, Any] | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    policy = retention_policy or build_retention_policy(state_dir=state_dir_path, write_result=False)
    plan = cleanup_plan or build_cleanup_plan(state_dir=state_dir_path, write_result=False)[0]
    archive = archive_index or build_archive_index(state_dir=state_dir_path, write_result=False)[0]
    registry = {
        **_artifact_header(state_dir_path, "state_lifecycle_registry.json", STATE_LIFECYCLE_REGISTRY_PATH),
        "registry_status": "ACTIVE_DESIGN_ONLY",
        "retention_policy_path": RETENTION_POLICY_PATH,
        "cleanup_plan_path": CLEANUP_PLAN_PATH,
        "archive_index_path": ARCHIVE_INDEX_PATH,
        "deletion_manifest_schema_path": DELETION_MANIFEST_SCHEMA_PATH,
        "tombstone_schema_path": TOMBSTONE_SCHEMA_PATH,
        "retention_classes": sorted((policy.get("retention_classes") or {}).keys()),
        "cleanup_plan_actions": sorted({str(item.get("recommended_action") or "") for item in plan.get("future_candidates", []) if isinstance(item, Mapping)} | {"retain", "archive-candidate", "delete-candidate"}),
        "archive_index_roles": sorted({str(item.get("archive_role") or "") for item in archive.get("entries", []) if isinstance(item, Mapping)}),
        "current_allowed_transitions": {
            "current_audit_fact_source": ["retain"],
            "transient_closeout_log": ["retain", "future-delete-candidate"],
            "transient_closeout_pid": ["retain", "future-delete-candidate"],
            "missing_historical_sample_reference": ["retain-reference"],
        },
        "future_cleanup_apply_preconditions": [
            "separate APPROVED cleanup-apply decision packet",
            "accepted deletion manifest schema",
            "accepted tombstone schema",
            "per-file hashes captured before deletion",
            "audit approval for every delete candidate",
            "final gate proves delete_allowed_now remains false until future round",
        ],
        "cleanup_apply_allowed_this_round": False,
    }
    if write_result:
        _write_json(state_dir_path / "state_lifecycle_registry.json", registry)
    return registry


def validate_retention_policy(policy: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    classes = policy.get("retention_classes") if isinstance(policy.get("retention_classes"), Mapping) else {}
    missing = sorted(set(RETENTION_CLASSES) - set(str(key) for key in classes.keys()))
    if missing:
        errors.append(f"missing retention classes: {missing}")
    for name, entry in classes.items():
        if not isinstance(entry, Mapping):
            errors.append(f"{name} retention class is not an object")
            continue
        if entry.get("deletion_allowed_this_round") is not False:
            errors.append(f"{name} deletion_allowed_this_round must be false")
        if entry.get("future_cleanup_apply_required") is not True:
            errors.append(f"{name} future_cleanup_apply_required must be true")
        if entry.get("tombstone_required_if_deleted") is not True:
            errors.append(f"{name} tombstone_required_if_deleted must be true")
    if policy.get("cleanup_apply_allowed") is not False:
        errors.append("retention policy must not allow cleanup apply")
    return errors


def validate_cleanup_plan(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("cleanup_apply_allowed") is not False:
        errors.append("cleanup_apply_allowed must be false")
    for field in DESTRUCTIVE_ARRAY_FIELDS:
        if plan.get(field) != []:
            errors.append(f"{field} must be empty")
    for bucket_name in ("future_candidates", "current_evidence_protection"):
        bucket = plan.get(bucket_name) if isinstance(plan.get(bucket_name), list) else []
        for item in bucket:
            if not isinstance(item, Mapping):
                continue
            if item.get("delete_allowed_now") is not False:
                errors.append(f"{bucket_name} candidate allows immediate deletion")
    for item in plan.get("future_candidates", []) if isinstance(plan.get("future_candidates"), list) else []:
        if not isinstance(item, Mapping):
            continue
        if item.get("requires_future_cleanup_apply_decision") is not True:
            errors.append("future candidate missing cleanup-apply precondition")
        if item.get("requires_tombstone_if_deleted") is not True:
            errors.append("future candidate missing tombstone precondition")
    return errors


def validate_state_governance_bundle(bundle: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if bundle.get("gate_status") != "PASSED":
        errors.append("bundle gate did not pass")
    if bundle.get("planning_index_schema_only") is not True:
        errors.append("bundle must be planning/index/schema only")
    for field in ("cleanup_apply_allowed", "destructive_operation_performed"):
        expected = False
        if bundle.get(field) is not expected:
            errors.append(f"{field} must be false")
    forbidden = bundle.get("forbidden_capabilities") if isinstance(bundle.get("forbidden_capabilities"), Mapping) else {}
    enabled = sorted(key for key, value in forbidden.items() if value is not False)
    if enabled:
        errors.append(f"forbidden capabilities enabled: {enabled}")
    generated = set(str(item) for item in bundle.get("generated_artifacts", []) if isinstance(item, str))
    required = {
        RETENTION_POLICY_PATH,
        STATE_LIFECYCLE_REGISTRY_PATH,
        CLEANUP_PLAN_PATH,
        CLEANUP_PLAN_SUMMARY_PATH,
        ARCHIVE_INDEX_PATH,
        ARCHIVE_INDEX_SUMMARY_PATH,
        DELETION_MANIFEST_SCHEMA_PATH,
        TOMBSTONE_SCHEMA_PATH,
        RETENTION_POLICY_VALIDATION_PATH,
        STATE_GOVERNANCE_BUNDLE_RESULT_PATH,
        STATE_GOVERNANCE_BUNDLE_SNAPSHOT_PATH,
        "project_state/state_manifest.json",
        "project_state/context/current_context_packet.json",
        "project_state/roadmap/workstreams.json",
    }
    missing = sorted(required - generated)
    if missing:
        errors.append(f"generated_artifacts missing: {missing}")
    return errors


def build_state_governance_bundle(*, state_dir: str | Path = "project_state", write_result: bool = True) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    policy = build_retention_policy(state_dir=state_dir_path, write_result=write_result)
    cleanup_plan, cleanup_summary = build_cleanup_plan(state_dir=state_dir_path, write_result=write_result)
    archive_index, archive_summary = build_archive_index(state_dir=state_dir_path, write_result=write_result)
    deletion_schema = build_deletion_manifest_schema(state_dir=state_dir_path, write_result=write_result)
    tombstone_schema = build_tombstone_schema(state_dir=state_dir_path, write_result=write_result)
    lifecycle = build_state_lifecycle_registry(
        state_dir=state_dir_path,
        retention_policy=policy,
        cleanup_plan=cleanup_plan,
        archive_index=archive_index,
        write_result=write_result,
    )
    manifest = build_state_manifest(state_dir=state_dir_path, write_result=write_result)
    context = build_current_context_packet(state_dir=state_dir_path, write_result=write_result)
    workstreams = build_workstream_registry(state_dir=state_dir_path, write_result=write_result)

    policy_errors = validate_retention_policy(policy)
    cleanup_errors = validate_cleanup_plan(cleanup_plan)
    destructive_counts = {field: len(cleanup_plan.get(field) or []) for field in DESTRUCTIVE_ARRAY_FIELDS}
    validation = {
        **_artifact_header(state_dir_path, "retention_policy_validation.json", RETENTION_POLICY_VALIDATION_PATH),
        "validation_status": "PASSED" if not policy_errors else "FAILED",
        "errors": policy_errors,
        "retention_class_count": len(policy.get("retention_classes") or {}),
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "retention_policy_validation.json", validation)

    forbidden_capabilities = {name: False for name in FORBIDDEN_CAPABILITIES}
    active_workstreams = [
        item for item in workstreams.get("workstreams", [])
        if isinstance(item, Mapping) and item.get("status") == "ACTIVE_ROUND"
    ]
    checks = [
        {
            "name": "retention_policy_valid",
            "status": "PASS" if not policy_errors else "FAIL",
            "errors": policy_errors,
        },
        {
            "name": "cleanup_plan_non_destructive",
            "status": "PASS" if not cleanup_errors else "FAIL",
            "errors": cleanup_errors,
            "destructive_action_counts": destructive_counts,
        },
        {
            "name": "archive_index_bounded",
            "status": "PASS" if archive_index.get("full_solve_reports_scan") is False and archive_index.get("recursive_rounds_scan") is False else "FAIL",
            "full_solve_reports_scan": archive_index.get("full_solve_reports_scan"),
            "recursive_rounds_scan": archive_index.get("recursive_rounds_scan"),
        },
        {
            "name": "schema_only_deletion_and_tombstone",
            "status": "PASS" if deletion_schema.get("real_manifest_for_actual_files") is False and tombstone_schema.get("real_tombstone_written") is False else "FAIL",
        },
        {
            "name": "unique_active_workstream",
            "status": "PASS" if len(active_workstreams) == 1 and active_workstreams[0].get("workstream_id") == "state_governance_bundle_big_step" else "FAIL",
            "active_workstreams": active_workstreams,
        },
        {
            "name": "historical_sample_gaps_nonblocking",
            "status": "PASS" if cleanup_plan.get("assertions", {}).get("historical_sample_missing_artifacts_are_nonblocking") is True else "FAIL",
            "missing_historical_sample_reference_count": len(cleanup_plan.get("missing_historical_sample_references") or []),
        },
        {
            "name": "forbidden_capabilities_disabled",
            "status": "PASS",
            "capabilities": forbidden_capabilities,
        },
    ]
    errors = []
    for check in checks:
        if check.get("status") != "PASS":
            errors.append(str(check.get("name") or "unknown_check"))
    generated_artifacts = [
        RETENTION_POLICY_PATH,
        STATE_LIFECYCLE_REGISTRY_PATH,
        CLEANUP_PLAN_PATH,
        CLEANUP_PLAN_SUMMARY_PATH,
        ARCHIVE_INDEX_PATH,
        ARCHIVE_INDEX_SUMMARY_PATH,
        DELETION_MANIFEST_SCHEMA_PATH,
        TOMBSTONE_SCHEMA_PATH,
        RETENTION_POLICY_VALIDATION_PATH,
        STATE_GOVERNANCE_BUNDLE_RESULT_PATH,
        STATE_GOVERNANCE_BUNDLE_SNAPSHOT_PATH,
        "project_state/state_manifest.json",
        "project_state/context/current_context_packet.json",
        "project_state/roadmap/workstreams.json",
    ]
    result = {
        **_artifact_header(state_dir_path, "state_governance_bundle_result.json", STATE_GOVERNANCE_BUNDLE_RESULT_PATH),
        "gate_name": "state-governance-bundle",
        "gate_status": "PASSED" if not errors else "FAILED",
        "checks": checks,
        "errors": errors,
        "generated_artifacts": generated_artifacts,
        "cleanup_apply_allowed": False,
        "destructive_operation_performed": False,
        "planning_index_schema_only": True,
        "forbidden_capabilities": forbidden_capabilities,
        "no_concrete_sample_claims": True,
        "artifact_path": STATE_GOVERNANCE_BUNDLE_RESULT_PATH,
        "snapshot_path": STATE_GOVERNANCE_BUNDLE_SNAPSHOT_PATH,
    }
    snapshot = {
        **_artifact_header(state_dir_path, "state_governance_bundle_snapshot.json", STATE_GOVERNANCE_BUNDLE_SNAPSHOT_PATH),
        "gate_status": result["gate_status"],
        "retention_policy_status": validation["validation_status"],
        "cleanup_plan_status": "PASSED" if not cleanup_errors else "FAILED",
        "archive_index_status": archive_summary.get("index_status"),
        "lifecycle_registry_status": lifecycle.get("registry_status"),
        "state_manifest_decision_id": manifest.get("decision_id"),
        "context_packet_decision_id": context.get("decision_id"),
        "workstream_active_ids": [str(item.get("workstream_id") or "") for item in active_workstreams],
        "destructive_action_counts": destructive_counts,
        "planning_index_schema_only": True,
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "state_governance_bundle_snapshot.json", snapshot)
        _write_json(state_dir_path / "gates" / "state_governance_bundle_result.json", result)
    return result
