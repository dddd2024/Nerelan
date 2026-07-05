from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .project_state import read_decision_contract, read_decision_meta


BOUNDED_CONTEXT_FILES = (
    "decision_packet.md",
    "gates/command_plan.json",
    "gates/final_gate_result.json",
    "gates/report_summary_synthesis.json",
    "codex_execution_report.md",
    "pytest_result.txt",
)


def build_orchestrator_context_snapshot(
    *,
    state_dir: str | Path = "project_state",
    profile: str = "planner",
) -> dict[str, Any]:
    root = Path(state_dir)
    decision = read_decision_meta(root)
    contract = read_decision_contract(root)
    sources: dict[str, Any] = {}
    for rel in BOUNDED_CONTEXT_FILES:
        path = root / rel
        if path.suffix == ".json":
            sources[rel] = _read_json(path)
        else:
            sources[rel] = {"exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0}
    return {
        "schema_version": 1,
        "snapshot_kind": f"{profile}_context",
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": str(decision.get("round_id") or ""),
        "mainline": str(decision.get("mainline") or ""),
        "decision_authority": "project_state/decision_packet.md",
        "task_packet_role": "background_only",
        "bounded_sources": sources,
        "allowed_source_files": list(contract.get("allowed_source_files") or []),
        "forbidden_mutated_paths": list(contract.get("forbidden_mutated_paths") or []),
        "model_api_invocation": False,
        "full_solve_reports_read": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"exists": path.exists()}
    return payload if isinstance(payload, dict) else {"exists": True, "type": type(payload).__name__}
