"""Post-final evidence synchronization for project_state context packets."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .project_context_builder import build_current_context_packet
from .project_state import read_decision_meta


POST_FINAL_EVIDENCE_SYNC_RESULT_NAME = "post_final_evidence_sync_result.json"
POST_FINAL_EVIDENCE_SYNC_SNAPSHOT_NAME = "post_final_evidence_sync_snapshot.json"
POST_FINAL_EVIDENCE_SYNC_OUTPUT_PATH = f"project_state/gates/{POST_FINAL_EVIDENCE_SYNC_RESULT_NAME}"
POST_FINAL_EVIDENCE_SYNC_SNAPSHOT_OUTPUT_PATH = f"project_state/gates/{POST_FINAL_EVIDENCE_SYNC_SNAPSHOT_NAME}"


def _now_iso() -> str:
    from datetime import timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _artifact_current(payload: Mapping[str, Any], *, decision_id: str, round_id: str) -> bool:
    return (
        str(payload.get("decision_id") or "") == decision_id
        and str(payload.get("round_id") or "") == round_id
    )


def build_post_final_evidence_sync_result(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
    refresh_context: bool = True,
) -> dict[str, Any]:
    """Refresh or validate context/final-check synchronization.

    The gate is deterministic and local-only. It may rewrite the bounded
    context packet but never dispatches runners, calls models, or mutates
    external state.
    """

    state_dir_path = Path(state_dir)
    decision = read_decision_meta(state_dir_path)
    decision_id = str(decision.get("decision_id") or "")
    round_id = str(decision.get("round_id") or "")
    report_id = f"codex_report_{round_id.removeprefix('round_')}" if round_id else ""

    before_context = _read_json(state_dir_path / "context" / "current_context_packet.json")
    final_gate = _read_json(state_dir_path / "gates" / "final_gate_result.json")
    final_gate_current = bool(final_gate) and _artifact_current(
        final_gate, decision_id=decision_id, round_id=round_id
    )

    context = (
        build_current_context_packet(state_dir=state_dir_path, write_result=write_result)
        if refresh_context
        else before_context
    )
    auditor = context.get("auditor_context") if isinstance(context.get("auditor_context"), Mapping) else {}
    final_status = str(final_gate.get("gate_status") or "")
    context_status = str(auditor.get("final_gate_status") or "")
    context_current = bool(context) and _artifact_current(context, decision_id=decision_id, round_id=round_id)

    final_generated_at = str(final_gate.get("generated_at") or "")
    context_generated_at = str(context.get("generated_at") or "")
    final_time = _parse_time(final_generated_at)
    context_time = _parse_time(context_generated_at)
    context_after_final = bool(final_time and context_time and context_time >= final_time)

    errors: list[str] = []
    warnings: list[str] = []
    if not context_current:
        errors.append("current_context_packet.json is missing or stale for current decision/round")
    if final_gate_current:
        if context_status != final_status:
            errors.append("context final_gate_status does not match current final_gate_result gate_status")
        if not context_after_final:
            warnings.append("context packet is current but was generated before final_gate_result timestamp")
    else:
        warnings.append("final_gate_result.json is missing or stale; context is marked pre-final/stale")

    stale_context_detected = bool(
        before_context
        and (
            not _artifact_current(before_context, decision_id=decision_id, round_id=round_id)
            or str(
                (
                    before_context.get("auditor_context")
                    if isinstance(before_context.get("auditor_context"), Mapping)
                    else {}
                ).get("final_gate_status")
                or ""
            )
            != final_status
        )
    )

    gate_status = "FAILED" if errors else "PASSED"
    result = {
        "schema_version": 1,
        "artifact_name": POST_FINAL_EVIDENCE_SYNC_RESULT_NAME,
        "gate_name": "post-final-evidence-sync",
        "gate_status": gate_status,
        "sync_status": gate_status,
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": report_id,
        "generated_at": _now_iso(),
        "final_gate_current": final_gate_current,
        "final_gate_status": final_status,
        "final_gate_generated_at": final_generated_at,
        "context_current": context_current,
        "context_final_gate_status": context_status,
        "context_generated_at": context_generated_at,
        "context_generated_after_final_gate": context_after_final,
        "context_final_gate_status_source": auditor.get("final_gate_status_source"),
        "post_final_sync_status": auditor.get("post_final_sync_status"),
        "stale_context_detected": stale_context_detected,
        "refresh_context": refresh_context,
        "non_dispatching": True,
        "runner_dispatch": False,
        "model_api_invocation": False,
        "github_actions_dispatch": False,
        "remote_mutation": False,
        "errors": errors,
        "warnings": warnings,
        "generated_artifacts": [
            POST_FINAL_EVIDENCE_SYNC_OUTPUT_PATH,
            POST_FINAL_EVIDENCE_SYNC_SNAPSHOT_OUTPUT_PATH,
            "project_state/context/current_context_packet.json",
        ],
    }
    snapshot = {
        "schema_version": 1,
        "artifact_name": POST_FINAL_EVIDENCE_SYNC_SNAPSHOT_NAME,
        "decision_id": decision_id,
        "round_id": round_id,
        "generated_at": result["generated_at"],
        "before_context_decision_id": before_context.get("decision_id"),
        "before_context_round_id": before_context.get("round_id"),
        "before_context_final_gate_status": (
            before_context.get("auditor_context", {}).get("final_gate_status")
            if isinstance(before_context.get("auditor_context"), Mapping)
            else None
        ),
        "after_context_decision_id": context.get("decision_id"),
        "after_context_round_id": context.get("round_id"),
        "after_context_final_gate_status": context_status,
        "final_gate_status": final_status,
        "stale_context_detected": stale_context_detected,
    }

    if write_result:
        gates_dir = state_dir_path / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)
        (gates_dir / POST_FINAL_EVIDENCE_SYNC_RESULT_NAME).write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (gates_dir / POST_FINAL_EVIDENCE_SYNC_SNAPSHOT_NAME).write_text(
            json.dumps(snapshot, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    return result


def validate_post_final_evidence_sync_result(
    payload: Mapping[str, Any],
    *,
    decision_id: str,
    round_id: str,
) -> list[str]:
    errors: list[str] = []
    if str(payload.get("decision_id") or "") != decision_id:
        errors.append("decision_id mismatch")
    if str(payload.get("round_id") or "") != round_id:
        errors.append("round_id mismatch")
    if payload.get("runner_dispatch") is not False:
        errors.append("runner_dispatch must be false")
    if payload.get("model_api_invocation") is not False:
        errors.append("model_api_invocation must be false")
    if payload.get("github_actions_dispatch") is not False:
        errors.append("github_actions_dispatch must be false")
    if payload.get("remote_mutation") is not False:
        errors.append("remote_mutation must be false")
    if str(payload.get("gate_status") or "") != "PASSED":
        errors.append("gate_status is not PASSED")
    return errors
