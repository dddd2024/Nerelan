"""Deterministic terminal acceptance gate."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from reverse_agent.architecture.contracts import AcceptanceResult, DevelopmentWorkflowState
from reverse_agent.architecture.risk import AcceptanceStatus, AuthorizationStatus, WorkflowRoute


def acceptance_gate_node(state: DevelopmentWorkflowState) -> dict[str, Any]:
    if "team_execution_result" in state:
        team_result = state["team_execution_result"]
        invalid = not isinstance(team_result, Mapping)
        if not invalid:
            invalid = "accepted" not in team_result or type(team_result["accepted"]) is not bool
        raw_reasons = team_result.get("reasons", ()) if not invalid else ()
        if not invalid:
            invalid = not isinstance(raw_reasons, (list, tuple)) or not all(
                isinstance(reason, str) for reason in raw_reasons
            )
        if invalid:
            return {
                "acceptance_result": AcceptanceResult(
                    AcceptanceStatus.BLOCKED,
                    False,
                    ("team_execution_result_invalid",),
                ).to_dict(),
                "node_trace": [*(state.get("node_trace") or []), "acceptance_gate"],
            }

        accepted = team_result["accepted"]
        if not accepted:
            reasons = tuple(raw_reasons)
            if not reasons:
                reasons = ("team_execution_rejected",)
            return {
                "acceptance_result": AcceptanceResult(
                    AcceptanceStatus.BLOCKED, False, reasons
                ).to_dict(),
                "node_trace": [*(state.get("node_trace") or []), "acceptance_gate"],
            }

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
