"""Deterministic project-state manifest for governance rounds."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_state import (
    parse_pytest_result_header,
    read_codex_report_summary,
    read_decision_contract,
    read_decision_meta,
    status_summary,
)


STATE_MANIFEST_SCHEMA_VERSION = 1
STATE_MANIFEST_PATH = "project_state/state_manifest.json"
GOVERNANCE_ARTIFACT_KIND = "governance_index"


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


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _file_ref(state_dir: Path, rel: str, role: str, required: bool = False) -> dict[str, Any]:
    path = state_dir / rel
    exists = path.exists()
    return {
        "path": _norm_path(Path("project_state") / rel),
        "role": role if exists else ("missing_blocking" if required else "missing_optional"),
        "exists": exists,
        "required": required,
        "sha256": _sha256_file(path) if exists else "",
        "size_bytes": path.stat().st_size if exists else 0,
    }


def _gate_ref(state_dir: Path, name: str, role: str, required: bool = False) -> dict[str, Any]:
    return _file_ref(state_dir, f"gates/{name}", role, required)


def _artifact_freshness_summary(artifact_index: Mapping[str, Any]) -> dict[str, Any]:
    latest_v2 = artifact_index.get("latest_artifacts_v2")
    counts: dict[str, int] = {}
    if isinstance(latest_v2, Mapping):
        for entry in latest_v2.values():
            if not isinstance(entry, Mapping):
                continue
            freshness = str(entry.get("freshness") or "unknown")
            counts[freshness] = counts.get(freshness, 0) + 1
    missing = artifact_index.get("missing")
    return {
        "counts": dict(sorted(counts.items())),
        "missing_sample_artifacts": list(missing or []) if isinstance(missing, list) else [],
        "missing_sample_artifacts_blocking_for_current_round": False,
    }


def build_state_manifest(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    decision = read_decision_meta(state_dir_path)
    contract = read_decision_contract(state_dir_path)
    report = read_codex_report_summary(state_dir_path)
    try:
        pytest_text = (state_dir_path / "pytest_result.txt").read_text(encoding="utf-8")
    except OSError:
        pytest_text = ""
    pytest_result = parse_pytest_result_header(pytest_text)
    status = status_summary(state_dir=state_dir_path)
    artifact_index = _read_json(state_dir_path / "artifact_index.json")

    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    report_id = str(report.get("report_id") or f"codex_report_{round_id.removeprefix('round_')}")
    previous_round_id = str(contract.get("follows_last_accepted_round_id") or status.get("latest_accepted_round_id") or "")
    previous_manifest = (
        f"rounds/{previous_round_id}/round_manifest.json" if previous_round_id else ""
    )

    current_refs = {
        "decision_packet": _file_ref(state_dir_path, "decision_packet.md", "current", True),
        "codex_execution_report": _file_ref(state_dir_path, "codex_execution_report.md", "current", False),
        "execution_report": _file_ref(state_dir_path, "execution_report.md", "current", False),
        "pytest_result": _file_ref(state_dir_path, "pytest_result.txt", "current", False),
        "command_plan": _gate_ref(state_dir_path, "command_plan.json", "current", True),
        "execution_log": _gate_ref(state_dir_path, "execution_log.json", "current", False),
        "final_check": _gate_ref(state_dir_path, "final_gate_result.json", "current", False),
        "report_summary": _gate_ref(state_dir_path, "report_summary_synthesis.json", "current", False),
        "run_closeout": _gate_ref(state_dir_path, "run_closeout_result.json", "current", False),
    }

    generated_refs = {
        "state_manifest": _file_ref(state_dir_path, "state_manifest.json", "generated_or_updated", False),
        "current_context_packet": _file_ref(
            state_dir_path, "context/current_context_packet.json", "generated_or_updated", False
        ),
        "workstreams": _file_ref(state_dir_path, "roadmap/workstreams.json", "generated_or_updated", False),
        "retention_policy": _file_ref(state_dir_path, "retention_policy.json", "generated_or_updated", False),
        "state_lifecycle_registry": _file_ref(
            state_dir_path, "state_lifecycle_registry.json", "generated_or_updated", False
        ),
        "cleanup_plan": _gate_ref(state_dir_path, "cleanup_plan.json", "generated_or_updated", False),
        "cleanup_plan_summary": _gate_ref(state_dir_path, "cleanup_plan_summary.json", "generated_or_updated", False),
        "archive_index": _gate_ref(state_dir_path, "archive_index.json", "generated_or_updated", False),
        "archive_index_summary": _gate_ref(state_dir_path, "archive_index_summary.json", "generated_or_updated", False),
        "deletion_manifest_schema": _gate_ref(
            state_dir_path, "deletion_manifest_schema.json", "generated_or_updated", False
        ),
        "tombstone_schema": _gate_ref(state_dir_path, "tombstone_schema.json", "generated_or_updated", False),
        "retention_policy_validation": _gate_ref(
            state_dir_path, "retention_policy_validation.json", "generated_or_updated", False
        ),
        "state_governance_bundle_result": _gate_ref(
            state_dir_path, "state_governance_bundle_result.json", "generated_or_updated", False
        ),
        "state_governance_bundle_snapshot": _gate_ref(
            state_dir_path, "state_governance_bundle_snapshot.json", "generated_or_updated", False
        ),
        "project_governance_context_result": _gate_ref(
            state_dir_path, "project_governance_context_result.json", "generated_or_updated", False
        ),
        "project_governance_context_snapshot": _gate_ref(
            state_dir_path, "project_governance_context_snapshot.json", "generated_or_updated", False
        ),
    }

    historical_refs = {
        "task_packet": _file_ref(state_dir_path, "task_packet.json", "historical_nonblocking", False),
        "current_state": _file_ref(state_dir_path, "current_state.json", "historical_nonblocking", False),
        "artifact_index": _file_ref(state_dir_path, "artifact_index.json", "historical_nonblocking", False),
        "negative_results": _file_ref(state_dir_path, "negative_results.json", "historical_nonblocking", False),
    }
    archived_refs = {}
    if previous_manifest:
        archived_refs["latest_accepted_round_manifest"] = _file_ref(
            state_dir_path, previous_manifest, "archived", False
        )

    manifest = {
        "schema_version": STATE_MANIFEST_SCHEMA_VERSION,
        "artifact_name": "state_manifest.json",
        "artifact_kind": GOVERNANCE_ARTIFACT_KIND,
        "artifact_path": STATE_MANIFEST_PATH,
        "generated_at": _now_iso(),
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "mainline": str(decision.get("mainline") or ""),
        "state_build_id": str(decision.get("based_on_state_build_id") or ""),
        "state_digest": str(decision.get("based_on_state_digest") or ""),
        "authority": {
            "task_authority": "project_state/decision_packet.md",
            "command_authority": "project_state/gates/command_plan.json",
            "task_packet_role": "background_only",
            "governance_artifacts_are_fact_source_replacements": False,
        },
        "status": {
            "decision_status": str(decision.get("status") or ""),
            "report_status": str(report.get("status") or ""),
            "acceptance_recommendation": str(report.get("acceptance_recommendation") or ""),
            "pytest_status": str(pytest_result.get("status") or ""),
            "command_plan_status": str(_read_json(state_dir_path / "gates" / "command_plan.json").get("plan_status") or ""),
            "execution_log_status": str(_read_json(state_dir_path / "gates" / "execution_log.json").get("gate_status") or ""),
            "final_check_status": str(_read_json(state_dir_path / "gates" / "final_gate_result.json").get("gate_status") or ""),
            "closeout_status": str(_read_json(state_dir_path / "gates" / "run_closeout_result.json").get("closeout_status") or ""),
        },
        "latest_accepted_baseline": {
            "round_id": previous_round_id,
            "decision_id": str(contract.get("follows_last_accepted_decision_id") or status.get("latest_accepted_decision_id") or ""),
            "round_manifest": _norm_path(Path("project_state") / previous_manifest) if previous_manifest else "",
        },
        "artifact_roles": {
            "current": current_refs,
            "generated_or_updated": generated_refs,
            "historical_nonblocking": historical_refs,
            "archived": archived_refs,
            "missing_optional": {
                key: value
                for bucket in (current_refs, generated_refs, historical_refs, archived_refs)
                for key, value in bucket.items()
                if value["role"] == "missing_optional"
            },
            "missing_blocking": {
                key: value
                for bucket in (current_refs, generated_refs, historical_refs, archived_refs)
                for key, value in bucket.items()
                if value["role"] == "missing_blocking"
            },
        },
        "artifact_freshness": _artifact_freshness_summary(artifact_index),
        "classification_policy": {
            "historical_sample_artifact_gaps_are_nonblocking": True,
            "state_manifest_indexes_current_state_only": True,
            "project_state_files_remain_audit_fact_sources": True,
        },
    }
    if write_result:
        out_path = state_dir_path / "state_manifest.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return manifest


def validate_state_manifest(payload: Mapping[str, Any], *, decision_id: str, round_id: str) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != STATE_MANIFEST_SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if str(payload.get("decision_id") or "") != decision_id:
        errors.append("decision_id mismatch")
    if str(payload.get("round_id") or "") != round_id:
        errors.append("round_id mismatch")
    if payload.get("artifact_kind") != GOVERNANCE_ARTIFACT_KIND:
        errors.append("artifact_kind mismatch")
    authority = payload.get("authority") if isinstance(payload.get("authority"), Mapping) else {}
    if authority.get("governance_artifacts_are_fact_source_replacements") is not False:
        errors.append("governance artifacts must not replace fact sources")
    roles = payload.get("artifact_roles") if isinstance(payload.get("artifact_roles"), Mapping) else {}
    for role in ("current", "generated_or_updated", "historical_nonblocking", "archived", "missing_optional", "missing_blocking"):
        if role not in roles:
            errors.append(f"artifact role missing: {role}")
    freshness = payload.get("artifact_freshness") if isinstance(payload.get("artifact_freshness"), Mapping) else {}
    if freshness.get("missing_sample_artifacts_blocking_for_current_round") is not False:
        errors.append("missing historical sample artifacts must be nonblocking")
    return errors
