"""Context packet domain awareness for Phase A state taxonomy.

Provides helpers to classify context packet fields by domain and detect
stale domain facts. Phase A policy: stale or cross-domain facts are
non-blocking warnings, never hard failures. Legacy context packets
without domain metadata remain readable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .project_state import read_decision_meta


CONTEXT_DOMAIN_AWARENESS_VERSION = 1

# Known domain taxonomy. Each domain maps to the mainline that owns it.
# This is the same taxonomy used by the domain README skeletons under
# project_state/domains/*/README.md.
DOMAIN_TAXONOMY: dict[str, dict[str, str]] = {
    "reverse_solving": {
        "mainline": "reverse_solving",
        "scope": "sample",
        "description": "Reverse-solving sample state and artifact traces.",
    },
    "project_governance": {
        "mainline": "project_governance",
        "scope": "global",
        "description": "Governance gates, decision packets, reports, and closeout artifacts.",
    },
    "user_solve_layer": {
        "mainline": "project_governance",
        "scope": "global",
        "description": "User solve contract and execution layer (future).",
    },
    "evidence_replay": {
        "mainline": "project_governance",
        "scope": "global",
        "description": "Evidence trace schema and replay (future).",
    },
    "web_workbench": {
        "mainline": "project_governance",
        "scope": "global",
        "description": "Web read model and workbench UI (future).",
    },
    "tool_integration": {
        "mainline": "project_governance",
        "scope": "global",
        "description": "Tool provider contracts and integrations (future).",
    },
    "automation_runner": {
        "mainline": "project_governance",
        "scope": "global",
        "description": "Automation runner dispatch and lifecycle (future).",
    },
    "training_dataset": {
        "mainline": "project_governance",
        "scope": "global",
        "description": "Training dataset curation and provenance (future).",
    },
    "engineering_branch": {
        "mainline": "engineering_branch",
        "scope": "global",
        "description": "Engineering branch planning and broader infrastructure.",
    },
}

# Context packet fields that carry decision/round/mainline identifiers used
# to detect stale domain facts. Each entry maps a field path to the domain
# it belongs to.
_CONTEXT_IDENTITY_FIELDS: list[tuple[str, str]] = [
    ("decision_id", "project_governance"),
    ("round_id", "project_governance"),
    ("report_id", "project_governance"),
    ("mainline", "project_governance"),
    ("planner_context.current_mainline", "project_governance"),
    ("planner_context.active_decision_status", "project_governance"),
    ("planner_context.task_authority", "project_governance"),
    ("planner_context.command_authority", "project_governance"),
    ("planner_context.previous_accepted_baseline", "project_governance"),
    ("auditor_context.final_gate_decision_id", "project_governance"),
    ("auditor_context.final_gate_round_id", "project_governance"),
    ("auditor_context.final_gate_report_id", "project_governance"),
    ("auditor_context.final_gate_status", "project_governance"),
    ("auditor_context.final_gate_source_path", "project_governance"),
    ("auditor_context.context_generated_after_final_gate", "project_governance"),
    ("auditor_context.stale_context_detected", "project_governance"),
]

# Context packet fields that reference reverse-solving sample state.
_CONTEXT_REVERSE_SOLVING_FIELDS: list[tuple[str, str]] = [
    ("planner_context.artifact_freshness", "reverse_solving"),
    ("planner_context.missing_sample_artifacts_blocking_for_current_round", "reverse_solving"),
    ("negative_results_constraints", "reverse_solving"),
    ("source_files", "project_governance"),
]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _get_nested(data: Mapping[str, Any], dotted_key: str) -> Any:
    """Retrieve a nested value using dot notation (e.g. ``a.b.c``)."""
    current: Any = data
    for part in dotted_key.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        else:
            return None
    return current


def classify_context_field_domain(field_path: str) -> str:
    """Best-effort domain classification for a context packet field path.

    Returns the domain name (e.g. ``project_governance``,
    ``reverse_solving``) or empty string if unclassified.
    """
    for known_path, domain in _CONTEXT_IDENTITY_FIELDS:
        if field_path == known_path or field_path.startswith(known_path + "."):
            return domain
    for known_path, domain in _CONTEXT_REVERSE_SOLVING_FIELDS:
        if field_path == known_path or field_path.startswith(known_path + "."):
            return domain
    return ""


def detect_stale_domain_facts(
    context_payload: Mapping[str, Any],
    *,
    current_decision_id: str = "",
    current_round_id: str = "",
    current_mainline: str = "",
) -> list[dict[str, str]]:
    """Detect stale domain facts in a context packet.

    A stale domain fact is a field that references identifiers from a
    different decision/round/mainline than the current round. Phase A
    policy: stale facts are non-blocking warnings.
    """
    stale_facts: list[dict[str, str]] = []

    context_decision_id = str(_get_nested(context_payload, "decision_id") or "")
    context_round_id = str(_get_nested(context_payload, "round_id") or "")
    context_mainline = str(_get_nested(context_payload, "mainline") or "")

    if current_decision_id and context_decision_id and context_decision_id != current_decision_id:
        stale_facts.append(
            {
                "field": "decision_id",
                "domain": "project_governance",
                "observed_value": context_decision_id,
                "expected_value": current_decision_id,
                "reason": "context packet decision_id does not match current decision",
            }
        )

    if current_round_id and context_round_id and context_round_id != current_round_id:
        stale_facts.append(
            {
                "field": "round_id",
                "domain": "project_governance",
                "observed_value": context_round_id,
                "expected_value": current_round_id,
                "reason": "context packet round_id does not match current round",
            }
        )

    if current_mainline and context_mainline and context_mainline != current_mainline:
        stale_facts.append(
            {
                "field": "mainline",
                "domain": "project_governance",
                "observed_value": context_mainline,
                "expected_value": current_mainline,
                "reason": "context packet mainline does not match current mainline",
            }
        )

    # Check auditor_context stale detection
    auditor = _get_nested(context_payload, "auditor_context")
    if isinstance(auditor, Mapping):
        stale_detected = auditor.get("stale_context_detected")
        if stale_detected is True:
            stale_facts.append(
                {
                    "field": "auditor_context.stale_context_detected",
                    "domain": "project_governance",
                    "observed_value": "true",
                    "expected_value": "false",
                    "reason": "context packet itself reports stale context",
                }
            )

    return stale_facts


def build_context_domain_awareness(
    *,
    state_dir: str | Path = "project_state",
) -> dict[str, Any]:
    """Build Phase A domain awareness metadata for the context packet.

    Reads ``project_state/context/current_context_packet.json`` and the
    current decision meta to classify fields by domain and detect stale
    domain facts. Returns a summary suitable for final-check consumption.
    """
    state_dir_path = Path(state_dir)
    context_payload = _read_json(state_dir_path / "context" / "current_context_packet.json")
    decision = read_decision_meta(state_dir_path)

    current_decision_id = str(decision.get("decision_id") or "")
    current_round_id = str(decision.get("round_id") or "")
    current_mainline = str(decision.get("mainline") or "")

    stale_facts = detect_stale_domain_facts(
        context_payload,
        current_decision_id=current_decision_id,
        current_round_id=current_round_id,
        current_mainline=current_mainline,
    )

    # Classify top-level fields by domain
    field_domains: dict[str, str] = {}
    if isinstance(context_payload, Mapping):
        for key in context_payload:
            field_domains[str(key)] = classify_context_field_domain(str(key))

    # Identify which domains are represented in the context packet
    represented_domains = sorted({d for d in field_domains.values() if d})

    context_packet_present = bool(context_payload)

    return {
        "schema_version": CONTEXT_DOMAIN_AWARENESS_VERSION,
        "phase": "A",
        "context_packet_present": context_packet_present,
        "context_decision_id": str(_get_nested(context_payload, "decision_id") or ""),
        "context_round_id": str(_get_nested(context_payload, "round_id") or ""),
        "context_mainline": str(_get_nested(context_payload, "mainline") or ""),
        "current_decision_id": current_decision_id,
        "current_round_id": current_round_id,
        "current_mainline": current_mainline,
        "field_domains": field_domains,
        "represented_domains": represented_domains,
        "stale_domain_facts": stale_facts,
        "stale_fact_count": len(stale_facts),
        "policy": {
            "stale_domain_facts_are_non_blocking": True,
            "legacy_context_packets_remain_readable": True,
            "no_context_files_moved_or_deleted": True,
            "domain_awareness_is_advisory_only": True,
        },
    }
