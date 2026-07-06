"""Bounded current-context packet for project governance planning."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_state import read_decision_contract, read_decision_meta
from .project_state_manifest import build_state_manifest


CONTEXT_PACKET_SCHEMA_VERSION = 1
CONTEXT_PACKET_PATH = "project_state/context/current_context_packet.json"


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


def _read_json_list(path: Path) -> list[Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def _source_ref(path: Path, rel: str) -> dict[str, Any]:
    full = path / rel
    exists = full.exists()
    try:
        data = full.read_bytes()
    except OSError:
        data = b""
    return {
        "path": _norm_path(Path("project_state") / rel),
        "exists": exists,
        "sha256": hashlib.sha256(data).hexdigest() if exists else "",
        "size_bytes": len(data) if exists else 0,
    }


def _negative_constraints(state_dir: Path) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []
    for entry in _read_json_list(state_dir / "negative_results.json"):
        if not isinstance(entry, Mapping):
            continue
        constraints.append(
            {
                "direction": str(entry.get("direction") or ""),
                "severity": str(entry.get("severity") or ""),
                "do_not_repeat": bool(entry.get("do_not_repeat")),
            }
        )
    return constraints


def build_current_context_packet(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    decision = read_decision_meta(state_dir_path)
    contract = read_decision_contract(state_dir_path)
    manifest = build_state_manifest(state_dir=state_dir_path, write_result=False)
    command_plan = _read_json(state_dir_path / "gates" / "command_plan.json")
    final_gate = _read_json(state_dir_path / "gates" / "final_gate_result.json")

    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    report_id = f"codex_report_{round_id.removeprefix('round_')}" if round_id else ""
    forbidden_capabilities = list(contract.get("forbidden_capabilities_this_round") or [])
    allowed_source_files = list(contract.get("allowed_source_files") or [])

    packet = {
        "schema_version": CONTEXT_PACKET_SCHEMA_VERSION,
        "artifact_name": "current_context_packet.json",
        "artifact_kind": "governance_index",
        "artifact_path": CONTEXT_PACKET_PATH,
        "generated_at": _now_iso(),
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "mainline": str(decision.get("mainline") or ""),
        "planner_context": {
            "task_authority": "project_state/decision_packet.md",
            "command_authority": "project_state/gates/command_plan.json",
            "task_packet_role": "background_only",
            "current_mainline": str(decision.get("mainline") or ""),
            "active_decision_status": str(decision.get("status") or ""),
            "previous_accepted_baseline": manifest.get("latest_accepted_baseline"),
            "state_build_id": str(decision.get("based_on_state_build_id") or ""),
            "state_digest": str(decision.get("based_on_state_digest") or ""),
            "artifact_freshness": manifest.get("artifact_freshness"),
            "next_action_policy": "follow command_plan; do not execute roadmap entries unless selected by decision_packet",
        },
        "auditor_context": {
            "report_id": report_id,
            "command_plan_status": str(command_plan.get("plan_status") or ""),
            "final_gate_status": str(final_gate.get("gate_status") or ""),
            "required_governance_artifacts": [
                "project_state/state_manifest.json",
                CONTEXT_PACKET_PATH,
                "project_state/roadmap/workstreams.json",
                "project_state/retention_policy.json",
                "project_state/state_lifecycle_registry.json",
                "project_state/gates/cleanup_plan.json",
                "project_state/gates/archive_index.json",
                "project_state/gates/deletion_manifest_schema.json",
                "project_state/gates/tombstone_schema.json",
                "project_state/gates/state_governance_bundle_result.json",
                "project_state/gates/state_governance_bundle_snapshot.json",
                "project_state/gates/status_policy_reconcile_result.json",
                "project_state/gates/doctor_backlog_split_result.json",
                "project_state/gates/governance_fix_result.json",
                "project_state/gates/cleanup_apply_safety_plan.json",
                "project_state/gates/cleanup_apply_dry_run.json",
                "project_state/gates/cleanup_apply_safety_result.json",
                "project_state/gates/cleanup_apply_safety_snapshot.json",
                "project_state/gates/deletion_manifest_validation_result.json",
                "project_state/gates/tombstone_validation_result.json",
                "project_state/gates/rollback_handoff_plan.json",
                "project_state/gates/audit_handoff_for_cleanup_apply.json",
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
                "project_state/gates/project_governance_context_result.json",
                "project_state/gates/project_governance_context_snapshot.json",
            ],
            "governance_artifacts_are_fact_source_replacements": False,
            "large_sources_omitted": ["solve_reports/**", "full PROJECT_PROGRESS_LOG.txt"],
        },
        "existing_capabilities": [
            "project_gate hard gates",
            "command-plan authority",
            "execution-log synthesis",
            "report-summary synthesis",
            "run-closeout and round archive",
            "policy-lint and prompt-consistency foundations",
            "job lifecycle and runner contract foundations",
            "manual-mode orchestrator foundations",
            "artifact role taxonomy",
            "retention policy design",
            "cleanup-plan design without cleanup-apply",
            "bounded archive index",
            "deletion manifest and tombstone schema design",
            "state lifecycle registry",
            "status-policy reconciliation for non-sample governance",
            "doctor/backlog split for historical sample gaps",
            "cleanup-apply dry-run safety planning",
            "deletion manifest and tombstone dry-run validation",
            "rollback and audit handoff planning for future cleanup apply",
            "cleanup-apply review package",
            "round compaction dry-run planning",
            "SQLite read-index schema readiness without database creation",
            "state hygiene dashboard feed generation without Web runtime",
            "lifecycle transition guard for deferred destructive work",
        ],
        "dynamic_state_caveats": [
            "task_packet.json, current_state.json, and artifact_index.json contain older sample context for this governance round",
            "missing historical sample artifacts are nonblocking for project_governance",
            "dynamic facts belong in project_state artifacts, not long-term skills or prompt docs",
        ],
        "negative_results_constraints": _negative_constraints(state_dir_path),
        "allowed_capability_profile": {
            "local_deterministic_python": True,
            "file_backed_json_artifacts": True,
            "docs": True,
            "tests": True,
            "cleanup_apply": False,
            "cleanup_apply_dry_run": True,
            "destructive_file_operations": False,
        },
        "forbidden_capabilities": forbidden_capabilities,
        "stop_conditions": list(contract.get("stop_conditions") or []),
        "source_files": {
            rel: _source_ref(state_dir_path, rel)
            for rel in [
                "decision_packet.md",
                "gates/command_plan.json",
                "gates/final_gate_result.json",
                "gates/report_summary_synthesis.json",
                "codex_execution_report.md",
                "pytest_result.txt",
                "negative_results.json",
            ]
        },
        "allowed_source_files": allowed_source_files,
        "forbidden_mutated_paths": list(contract.get("forbidden_mutated_paths") or []),
        "do_not_assume": [
            "missing sample artifacts are current blockers for this governance round",
            "roadmap workstreams grant execution authority",
            "generated governance indexes replace project_state fact sources",
            "model APIs, runners, Web services, databases, queues, schedulers, or external reverse tools are available",
        ],
        "bounded": True,
        "model_api_invocation": False,
        "runner_dispatch": False,
        "external_analysis_tool_invocation": False,
    }
    if write_result:
        out_path = state_dir_path / "context" / "current_context_packet.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return packet


def validate_current_context_packet(payload: Mapping[str, Any], *, decision_id: str, round_id: str) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != CONTEXT_PACKET_SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if str(payload.get("decision_id") or "") != decision_id:
        errors.append("decision_id mismatch")
    if str(payload.get("round_id") or "") != round_id:
        errors.append("round_id mismatch")
    if payload.get("artifact_kind") != "governance_index":
        errors.append("artifact_kind mismatch")
    auditor = payload.get("auditor_context") if isinstance(payload.get("auditor_context"), Mapping) else {}
    if auditor.get("governance_artifacts_are_fact_source_replacements") is not False:
        errors.append("context packet must not replace fact sources")
    if payload.get("model_api_invocation") is not False:
        errors.append("model API invocation must be false")
    if payload.get("runner_dispatch") is not False:
        errors.append("runner dispatch must be false")
    if payload.get("external_analysis_tool_invocation") is not False:
        errors.append("external analysis tool invocation must be false")
    return errors
