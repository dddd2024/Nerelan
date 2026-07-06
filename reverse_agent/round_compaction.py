"""Dry-run-only round compaction planning."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_state import read_decision_contract, read_decision_meta


ROUND_COMPACTION_SCHEMA_VERSION = 1
ROUND_COMPACTION_PLAN_PATH = "project_state/gates/round_compaction_plan.json"
ROUND_COMPACTION_DRY_RUN_PATH = "project_state/gates/round_compaction_dry_run.json"
ROUND_COMPACTION_MANIFEST_DRY_RUN_PATH = "project_state/gates/round_compaction_manifest_dry_run.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _identity(state_dir: Path, artifact_name: str, artifact_path: str) -> dict[str, Any]:
    decision = read_decision_meta(state_dir)
    round_id = str(decision.get("round_id") or "")
    return {
        "schema_version": ROUND_COMPACTION_SCHEMA_VERSION,
        "artifact_name": artifact_name,
        "artifact_path": artifact_path,
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": round_id,
        "report_id": f"codex_report_{round_id.removeprefix('round_')}" if round_id else "",
        "mainline": str(decision.get("mainline") or ""),
        "generated_at": _now_iso(),
    }


def _round_ref(state_dir: Path, round_id: str, role: str) -> dict[str, Any]:
    manifest = state_dir / "rounds" / round_id / "round_manifest.json"
    return {
        "round_id": round_id,
        "role": role,
        "manifest_path": f"project_state/rounds/{round_id}/round_manifest.json",
        "manifest_exists": manifest.exists(),
        "future_action": "retain",
        "compaction_apply_allowed": False,
    }


def _bounded_rounds(state_dir: Path) -> list[dict[str, Any]]:
    decision = read_decision_meta(state_dir)
    contract = read_decision_contract(state_dir)
    current_round = str(decision.get("round_id") or "")
    accepted_round = str(contract.get("follows_last_accepted_round_id") or "")
    superseded_decision = str(contract.get("supersedes_unexecuted_decision_id") or "")
    refs: list[dict[str, Any]] = []
    if current_round:
        refs.append(_round_ref(state_dir, current_round, "current_round"))
    if accepted_round and accepted_round != current_round:
        refs.append(_round_ref(state_dir, accepted_round, "accepted_baseline"))
    if superseded_decision:
        refs.append(
            {
                "round_id": "",
                "decision_id": superseded_decision,
                "role": "superseded_unexecuted_decision",
                "manifest_path": "",
                "manifest_exists": False,
                "future_action": "reference_only",
                "compaction_apply_allowed": False,
            }
        )
    return refs


def build_round_compaction_plan(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    rounds = _bounded_rounds(state_dir_path)
    payload = {
        **_identity(state_dir_path, "round_compaction_plan.json", ROUND_COMPACTION_PLAN_PATH),
        "gate_name": "round-compaction-plan",
        "plan_status": "DRY_RUN_READY",
        "dry_run_only": True,
        "archive_compaction_apply_allowed": False,
        "compaction_apply_allowed": False,
        "recursive_rounds_scan": False,
        "full_solve_reports_scan": False,
        "bounded_selection_policy": [
            "current decision round",
            "previous accepted baseline from decision_contract",
            "explicit superseded unexecuted decision reference",
        ],
        "source_rounds": rounds,
        "future_action_classes": ["retain", "summarize", "reference_only", "reject_for_lack_of_manifest"],
        "generated_artifacts": [ROUND_COMPACTION_PLAN_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "round_compaction_plan.json", payload)
    return payload


def build_round_compaction_dry_run(
    *,
    state_dir: str | Path = "project_state",
    plan: Mapping[str, Any] | None = None,
    write_result: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    state_dir_path = Path(state_dir)
    compaction_plan = dict(plan or build_round_compaction_plan(state_dir=state_dir_path, write_result=write_result))
    actions: list[dict[str, Any]] = []
    for item in compaction_plan.get("source_rounds", []) if isinstance(compaction_plan.get("source_rounds"), list) else []:
        if not isinstance(item, Mapping):
            continue
        role = str(item.get("role") or "")
        manifest_exists = item.get("manifest_exists") is True
        future_action = "retain" if role in {"current_round", "accepted_baseline"} else "reference_only"
        if role == "accepted_baseline" and manifest_exists:
            future_action = "summarize_and_retain_manifest_reference"
        actions.append(
            {
                "round_id": str(item.get("round_id") or ""),
                "decision_id": str(item.get("decision_id") or ""),
                "role": role,
                "manifest_path": str(item.get("manifest_path") or ""),
                "manifest_exists": manifest_exists,
                "future_action": future_action,
                "archive_written": False,
                "file_deleted": False,
                "file_moved": False,
                "compaction_apply_allowed": False,
            }
        )
    dry_run = {
        **_identity(state_dir_path, "round_compaction_dry_run.json", ROUND_COMPACTION_DRY_RUN_PATH),
        "gate_name": "round-compaction-dry-run",
        "dry_run_status": "PASSED",
        "dry_run_only": True,
        "archive_compaction_apply_allowed": False,
        "compaction_apply_allowed": False,
        "archive_written": False,
        "files_deleted": [],
        "files_moved": [],
        "archives_mutated": [],
        "recursive_rounds_scan": False,
        "actions": actions,
        "generated_artifacts": [ROUND_COMPACTION_DRY_RUN_PATH],
    }
    manifest = {
        **_identity(state_dir_path, "round_compaction_manifest_dry_run.json", ROUND_COMPACTION_MANIFEST_DRY_RUN_PATH),
        "gate_name": "round-compaction-manifest-dry-run",
        "manifest_status": "PASSED",
        "dry_run_only": True,
        "real_manifest_written": False,
        "compaction_apply_allowed": False,
        "future_manifest_entries": actions,
        "generated_artifacts": [ROUND_COMPACTION_MANIFEST_DRY_RUN_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "round_compaction_dry_run.json", dry_run)
        _write_json(state_dir_path / "gates" / "round_compaction_manifest_dry_run.json", manifest)
    return dry_run, manifest


def validate_round_compaction_bundle(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("gate_status") != "PASSED":
        errors.append("round compaction gate did not pass")
    if payload.get("dry_run_only") is not True:
        errors.append("dry_run_only must be true")
    if payload.get("compaction_apply_allowed") is not False:
        errors.append("compaction_apply_allowed must be false")
    for field in ("archive_written", "files_deleted", "files_moved", "archives_mutated"):
        value = payload.get(field)
        if value not in (False, []):
            errors.append(f"{field} must be false or empty")
    return errors


def build_round_compaction_bundle(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    plan = build_round_compaction_plan(state_dir=state_dir_path, write_result=write_result)
    dry_run, manifest = build_round_compaction_dry_run(state_dir=state_dir_path, plan=plan, write_result=write_result)
    errors: list[str] = []
    if plan.get("recursive_rounds_scan") is not False:
        errors.append("recursive rounds scan was enabled")
    if dry_run.get("archive_written") is not False:
        errors.append("dry-run wrote an archive")
    if dry_run.get("files_deleted") != [] or dry_run.get("files_moved") != []:
        errors.append("dry-run mutated files")
    if manifest.get("compaction_apply_allowed") is not False:
        errors.append("manifest allows compaction apply")
    payload = {
        **_identity(state_dir_path, "round_compaction_dry_run.json", ROUND_COMPACTION_DRY_RUN_PATH),
        "gate_name": "round-compaction",
        "gate_status": "PASSED" if not errors else "FAILED",
        "dry_run_only": True,
        "compaction_apply_allowed": False,
        "archive_compaction_apply_allowed": False,
        "archive_written": False,
        "files_deleted": [],
        "files_moved": [],
        "archives_mutated": [],
        "plan_path": ROUND_COMPACTION_PLAN_PATH,
        "dry_run_path": ROUND_COMPACTION_DRY_RUN_PATH,
        "manifest_dry_run_path": ROUND_COMPACTION_MANIFEST_DRY_RUN_PATH,
        "source_round_count": len(plan.get("source_rounds") or []),
        "checks": [
            {"name": "bounded_round_selection", "status": "PASS", "detail": "bounded source list only"},
            {"name": "no_archive_apply", "status": "PASS", "detail": "no archive write/move/delete occurred"},
            {"name": "dry_run_manifest_only", "status": "PASS", "detail": "manifest is dry-run-only"},
        ],
        "errors": errors,
        "generated_artifacts": [
            ROUND_COMPACTION_PLAN_PATH,
            ROUND_COMPACTION_DRY_RUN_PATH,
            ROUND_COMPACTION_MANIFEST_DRY_RUN_PATH,
        ],
    }
    return payload
