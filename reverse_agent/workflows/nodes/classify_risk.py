"""Classify the work item through deterministic rules."""

from __future__ import annotations

from typing import Any

from reverse_agent.architecture.contracts import (
    DevelopmentWorkflowState,
    ExecutionEnvelope,
    GitHubWorkItem,
    RiskPolicySnapshot,
)
from reverse_agent.architecture.risk import WorkflowRoute
from reverse_agent.architecture.risk_classifier import classify_risk


def classify_risk_node(state: DevelopmentWorkflowState) -> dict[str, Any]:
    """Classify risk using the immutable policy snapshot carried in state.

    Phase D: the policy snapshot is bound to the active Decision and flows
    through workflow state (``risk_policy_snapshot``) rather than being
    injected as a graph-construction keyword argument. This keeps the graph
    builder decoupled from the Decision and ensures the policy snapshot is
    part of the workflow's checkpointed state.
    """

    item = GitHubWorkItem.from_mapping(state["work_item"])
    envelope = ExecutionEnvelope(item.requested_operations, item.requested_paths)
    policy_dict = state.get("risk_policy_snapshot")
    if policy_dict is None:
        return {
            "risk_decision": {
                "schema_version": 1,
                "risk_tier": None,
                "route": WorkflowRoute.BLOCKED.value,
                "reasons": ["missing_risk_policy_snapshot"],
            },
            "node_trace": [*(state.get("node_trace") or []), "classify_risk"],
        }
    policy = RiskPolicySnapshot.from_mapping(policy_dict)
    workflow_identity = state.get("workflow_identity") or {}
    expected_decision_id = str(workflow_identity.get("decision_id") or policy.decision_id)
    expected_round_id = str(workflow_identity.get("round_id") or policy.round_id)
    if not policy.identity_matches(expected_decision_id, expected_round_id):
        return {
            "risk_decision": {
                "schema_version": 1,
                "risk_tier": None,
                "route": WorkflowRoute.BLOCKED.value,
                "reasons": [f"risk_policy_identity_mismatch:{expected_decision_id}:{expected_round_id}"],
            },
            "node_trace": [*(state.get("node_trace") or []), "classify_risk"],
        }
    capability_flag_risk = policy.resolved_capability_risk_for(item.requested_operations)
    decision = classify_risk(
        envelope,
        path_risk_floor=policy.path_risk_floor,
        capability_flag_risk=capability_flag_risk,
    )
    return {
        "risk_decision": decision.to_dict(),
        "risk_policy_snapshot": policy.to_dict(),
        "node_trace": [*(state.get("node_trace") or []), "classify_risk"],
    }
