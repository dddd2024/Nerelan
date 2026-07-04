from __future__ import annotations

from typing import Any, Mapping


DISPLAY_STATES = (
    "ready",
    "candidate_pending_validation",
    "needs_more_evidence",
    "verified",
    "blocked",
    "failed",
    "review",
)


def map_response_to_ui_state(response: Mapping[str, Any]) -> dict[str, Any]:
    status = str(response.get("status") or "").strip().lower()
    validation = str(response.get("validation_status") or "").strip().lower()
    evidence = str(response.get("evidence_status") or "").strip().lower()
    next_action = response.get("next_action") if isinstance(response.get("next_action"), Mapping) else {}

    if status == "candidate_found" and validation != "passed":
        display_state = "candidate_pending_validation"
        tone = "attention"
    elif status == "deep_analysis_running":
        display_state = "needs_more_evidence"
        tone = "info"
    elif status == "verified" and validation == "passed":
        display_state = "verified"
        tone = "success"
    elif status == "blocked":
        display_state = "blocked"
        tone = "blocked"
    elif status == "failed":
        display_state = "failed"
        tone = "danger"
    elif status in {"uploaded", "fast_analyzing", "validating"}:
        display_state = "review"
        tone = "info"
    else:
        display_state = "ready"
        tone = "neutral"

    return {
        "display_state": display_state,
        "tone": tone,
        "status": status or "ready",
        "validation_status": validation or "not_started",
        "evidence_status": evidence or "none",
        "next_action_kind": str(next_action.get("kind") or ""),
        "label": _label_for(display_state),
    }


def _label_for(display_state: str) -> str:
    labels = {
        "ready": "Ready",
        "candidate_pending_validation": "Candidate pending validation",
        "needs_more_evidence": "Needs more evidence",
        "verified": "Verified",
        "blocked": "Blocked",
        "failed": "Failed",
        "review": "Review",
    }
    return labels.get(display_state, "Review")
