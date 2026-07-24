"""Deterministic terminal acceptance gate."""

from __future__ import annotations

from typing import Any

from reverse_agent.architecture.contracts import AcceptanceResult, DevelopmentWorkflowState
from reverse_agent.architecture.risk import AcceptanceStatus, AuthorizationStatus, WorkflowRoute


def acceptance_gate_node(state: DevelopmentWorkflowState) -> dict[str, Any]:
    route = WorkflowRoute(state["risk_decision"]["route"])
    if route is WorkflowRoute.STANDARD_PATH:
        result = AcceptanceResult(AcceptanceStatus.ACCEPTED, True, ("standard_path",))
    elif route is WorkflowRoute.BLOCKED:
        result = AcceptanceResult(AcceptanceStatus.BLOCKED, False, tuple(state["risk_decision"]["reasons"]))
    else:
        status = AuthorizationStatus((state.get("authorization_result") or {}).get("status", "BLOCKED"))
        reasons = tuple((state.get("authorization_result") or {}).get("reasons", []))
        if status is AuthorizationStatus.AUTHORIZED:
            result = AcceptanceResult(AcceptanceStatus.ACCEPTED, True, ("trust_authorized",))
        elif status is AuthorizationStatus.APPROVAL_REQUIRED:
            result = AcceptanceResult(AcceptanceStatus.APPROVAL_REQUIRED, False, reasons or ("approval_required",))
        else:
            result = AcceptanceResult(AcceptanceStatus.BLOCKED, False, reasons or ("trust_blocked",))
    return {
        "acceptance_result": result.to_dict(),
        "node_trace": [*(state.get("node_trace") or []), "acceptance_gate"],
    }
