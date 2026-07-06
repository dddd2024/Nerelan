"""State hygiene planning helpers.

This module is intentionally a thin facade over the non-destructive state
governance builders.  It does not implement cleanup-apply.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_state import read_codex_report_summary, read_decision_contract, read_decision_meta
from .state_governance import build_cleanup_plan, build_retention_policy


STATE_HYGIENE_DASHBOARD_FEED_PATH = "project_state/gates/state_hygiene_dashboard_feed.json"
STATE_HYGIENE_DASHBOARD_SUMMARY_PATH = "project_state/gates/state_hygiene_dashboard_summary.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def build_state_hygiene_retention_bundle(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    policy = build_retention_policy(state_dir=state_dir, write_result=write_result)
    cleanup_plan, cleanup_summary = build_cleanup_plan(state_dir=state_dir, write_result=write_result)
    return {
        "retention_policy": policy,
        "cleanup_plan": cleanup_plan,
        "cleanup_plan_summary": cleanup_summary,
        "cleanup_apply_allowed": False,
        "destructive_operation_performed": False,
    }


def build_state_hygiene_dashboard_feed(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    state_dir_path = Path(state_dir)
    decision = read_decision_meta(state_dir_path)
    contract = read_decision_contract(state_dir_path)
    report = read_codex_report_summary(state_dir_path)
    final_gate = _read_json(state_dir_path / "gates" / "final_gate_result.json")
    doctor_split = _read_json(state_dir_path / "gates" / "doctor_backlog_split_result.json")
    cleanup_review = _read_json(state_dir_path / "gates" / "cleanup_apply_review_result.json")
    compaction = _read_json(state_dir_path / "gates" / "round_compaction_dry_run.json")
    index_result = _read_json(state_dir_path / "gates" / "state_index_readiness_result.json")
    archive_summary = _read_json(state_dir_path / "gates" / "archive_index_summary.json")
    lifecycle_guard = _read_json(state_dir_path / "gates" / "lifecycle_transition_guard_result.json")
    workstreams = _read_json(state_dir_path / "roadmap" / "workstreams.json")
    active_workstreams = [
        item for item in workstreams.get("workstreams", [])
        if isinstance(item, Mapping) and item.get("status") == "ACTIVE_ROUND"
    ]
    round_id = str(decision.get("round_id") or "")
    feed = {
        "schema_version": 1,
        "artifact_name": "state_hygiene_dashboard_feed.json",
        "artifact_path": STATE_HYGIENE_DASHBOARD_FEED_PATH,
        "generated_at": _now_iso(),
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": round_id,
        "report_id": str(report.get("report_id") or f"codex_report_{round_id.removeprefix('round_')}"),
        "mainline": str(decision.get("mainline") or ""),
        "dashboard_feed_only": True,
        "web_runtime_started": False,
        "current_decision": {
            "decision_id": str(decision.get("decision_id") or ""),
            "status": str(decision.get("status") or ""),
            "skill_profiles": list(decision.get("skill_profiles") or []),
        },
        "current_round": {
            "round_id": round_id,
            "phase_label": str(contract.get("phase_label") or ""),
            "last_accepted_round_id": str(contract.get("follows_last_accepted_round_id") or ""),
        },
        "latest_report": {
            "report_id": str(report.get("report_id") or ""),
            "status": str(report.get("status") or ""),
            "acceptance_recommendation": str(report.get("acceptance_recommendation") or ""),
        },
        "final_check": {
            "gate_status": str(final_gate.get("gate_status") or ""),
            "acceptance_recommendation": str((final_gate.get("status_summary") or {}).get("report_acceptance_recommendation") or ""),
        },
        "workstream_state": {
            "active_count": len(active_workstreams),
            "active_ids": [str(item.get("workstream_id") or "") for item in active_workstreams],
        },
        "backlog_notices": list(doctor_split.get("historical_backlog_notices") or []),
        "cleanup_readiness": {
            "gate_status": str(cleanup_review.get("gate_status") or ""),
            "review_status": str(cleanup_review.get("review_status") or ""),
            "real_cleanup_apply": False,
        },
        "compaction_readiness": {
            "dry_run_status": str(compaction.get("dry_run_status") or ""),
            "compaction_apply_allowed": False,
        },
        "index_readiness": {
            "gate_status": str(index_result.get("gate_status") or ""),
            "readiness_status": str(index_result.get("readiness_status") or ""),
            "database_file_created": False,
        },
        "archive_index": {
            "index_status": str(archive_summary.get("index_status") or ""),
            "entry_count": archive_summary.get("entry_count"),
        },
        "lifecycle_guard": {
            "gate_status": str(lifecycle_guard.get("gate_status") or ""),
            "real_cleanup_apply_deferred": lifecycle_guard.get("real_cleanup_apply_deferred"),
        },
        "forbidden_capability_status": {
            name: False for name in contract.get("forbidden_capabilities_this_round", [])
        },
        "generated_artifacts": [STATE_HYGIENE_DASHBOARD_FEED_PATH],
    }
    summary = {
        "schema_version": 1,
        "artifact_name": "state_hygiene_dashboard_summary.json",
        "artifact_path": STATE_HYGIENE_DASHBOARD_SUMMARY_PATH,
        "generated_at": _now_iso(),
        "decision_id": feed["decision_id"],
        "round_id": feed["round_id"],
        "report_id": feed["report_id"],
        "dashboard_status": "READY" if feed["dashboard_feed_only"] and not feed["web_runtime_started"] else "FAILED",
        "active_workstream_count": len(active_workstreams),
        "backlog_notice_count": len(feed["backlog_notices"]),
        "cleanup_review_status": feed["cleanup_readiness"]["review_status"],
        "compaction_dry_run_status": feed["compaction_readiness"]["dry_run_status"],
        "index_readiness_status": feed["index_readiness"]["readiness_status"],
        "web_runtime_started": False,
        "generated_artifacts": [STATE_HYGIENE_DASHBOARD_SUMMARY_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "state_hygiene_dashboard_feed.json", feed)
        _write_json(state_dir_path / "gates" / "state_hygiene_dashboard_summary.json", summary)
    return feed, summary


def validate_state_hygiene_dashboard_feed(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("dashboard_feed_only") is not True:
        errors.append("dashboard feed must be static/feed-only")
    if payload.get("web_runtime_started") is not False:
        errors.append("web runtime must not be started")
    required = ("current_decision", "current_round", "latest_report", "final_check", "backlog_notices", "cleanup_readiness", "compaction_readiness", "index_readiness")
    for key in required:
        if key not in payload:
            errors.append(f"missing dashboard section: {key}")
    return errors
