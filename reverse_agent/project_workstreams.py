"""File-backed project workstream registry."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_state import read_decision_contract, read_decision_meta


WORKSTREAMS_SCHEMA_VERSION = 1
WORKSTREAMS_PATH = "project_state/roadmap/workstreams.json"
WORKSTREAM_STATES = (
    "IDEA",
    "CANDIDATE",
    "ROADMAP_ACCEPTED",
    "READY_FOR_DECISION",
    "ACTIVE_ROUND",
    "ACCEPTED",
    "DEFERRED",
    "REJECTED",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _entry(
    workstream_id: str,
    family: str,
    status: str,
    *,
    current_decision_id: str,
    current_round_id: str,
    baseline_round_id: str = "",
    notes: str = "",
) -> dict[str, Any]:
    payload = {
        "workstream_id": workstream_id,
        "family": family,
        "status": status,
        "lifecycle": list(WORKSTREAM_STATES),
        "execution_authority": "project_state/decision_packet.md",
        "is_execution_authority": False,
        "active_decision_id": "",
        "active_round_id": "",
        "baseline_round_id": baseline_round_id,
        "notes": notes,
    }
    if status == "ACTIVE_ROUND":
        payload["active_decision_id"] = current_decision_id
        payload["active_round_id"] = current_round_id
        payload["is_execution_authority"] = False
        payload["notes"] = notes or "Active only because selected by current decision_packet."
    return payload


def build_workstream_registry(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    decision = read_decision_meta(state_dir_path)
    contract = read_decision_contract(state_dir_path)
    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    baseline_round_id = str(contract.get("follows_last_accepted_round_id") or "")

    workstreams = [
        _entry(
            "project_governance_context_registry",
            "project_governance",
            "ACTIVE_ROUND",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="Seeds deterministic manifest, context packet, workstream registry, and governance gate indexes.",
        ),
        _entry(
            "state_hygiene_retention_policy",
            "state_hygiene",
            "READY_FOR_DECISION",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="Future bounded retention policy; no cleanup or deletion in this round.",
        ),
        _entry(
            "manual_mode_web_orchestrator",
            "web_orchestrator",
            "ACCEPTED",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="Accepted baseline from the previous manual-mode Web orchestrator round.",
        ),
        _entry(
            "user_solve_layer",
            "user_solve",
            "ACCEPTED",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="Existing foundation only; not reopened by this governance round.",
        ),
        _entry(
            "agent_runner_dispatch",
            "runner_dispatch",
            "DEFERRED",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="Deferred because this round forbids runner dispatch and remote execution.",
        ),
        _entry(
            "github_ci_and_state_gate",
            "ci_state_gate",
            "ROADMAP_ACCEPTED",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="Read-only CI/state gate foundation exists; no workflow mutation in this round.",
        ),
        _entry(
            "reverse_solving_capability_matrix",
            "reverse_solving",
            "CANDIDATE",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="Future planning track; no sample solving, runtime validation, or candidate search now.",
        ),
        _entry(
            "tool_integration_ida_ghidra_debugger",
            "tool_integration",
            "DEFERRED",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="External reverse tools are forbidden for this round.",
        ),
        _entry(
            "sqlite_query_index",
            "database_indexing",
            "IDEA",
            current_decision_id=decision_id,
            current_round_id=round_id,
            baseline_round_id=baseline_round_id,
            notes="Idea only; database and query index implementation is explicitly out of scope.",
        ),
    ]

    registry = {
        "schema_version": WORKSTREAMS_SCHEMA_VERSION,
        "artifact_name": "workstreams.json",
        "artifact_kind": "governance_index",
        "artifact_path": WORKSTREAMS_PATH,
        "generated_at": _now_iso(),
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": str(decision.get("mainline") or ""),
        "lifecycle_states": list(WORKSTREAM_STATES),
        "authority_policy": {
            "decision_packet_is_execution_authority": True,
            "roadmap_entries_are_not_execution_authority": True,
            "only_current_decision_may_mark_active_round": True,
        },
        "workstreams": workstreams,
    }
    if write_result:
        out_path = state_dir_path / "roadmap" / "workstreams.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(registry, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return registry


def validate_workstream_registry(payload: Mapping[str, Any], *, decision_id: str, round_id: str) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != WORKSTREAMS_SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if str(payload.get("decision_id") or "") != decision_id:
        errors.append("decision_id mismatch")
    if str(payload.get("round_id") or "") != round_id:
        errors.append("round_id mismatch")
    if tuple(payload.get("lifecycle_states") or []) != WORKSTREAM_STATES:
        errors.append("lifecycle states mismatch")
    workstreams = payload.get("workstreams")
    if not isinstance(workstreams, list):
        errors.append("workstreams must be a list")
        return errors
    required_ids = {
        "project_governance_context_registry",
        "state_hygiene_retention_policy",
        "manual_mode_web_orchestrator",
        "user_solve_layer",
        "agent_runner_dispatch",
        "github_ci_and_state_gate",
        "reverse_solving_capability_matrix",
        "tool_integration_ida_ghidra_debugger",
        "sqlite_query_index",
    }
    seen_ids = {str(item.get("workstream_id") or "") for item in workstreams if isinstance(item, Mapping)}
    missing = sorted(required_ids - seen_ids)
    if missing:
        errors.append(f"missing workstreams: {missing}")
    active = [item for item in workstreams if isinstance(item, Mapping) and item.get("status") == "ACTIVE_ROUND"]
    if len(active) != 1:
        errors.append("exactly one ACTIVE_ROUND workstream is required")
    elif str(active[0].get("active_decision_id") or "") != decision_id or str(active[0].get("active_round_id") or "") != round_id:
        errors.append("ACTIVE_ROUND workstream ids mismatch current decision")
    if any(item.get("is_execution_authority") is not False for item in workstreams if isinstance(item, Mapping)):
        errors.append("workstreams must not be execution authority")
    return errors
