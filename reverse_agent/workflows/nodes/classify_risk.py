"""Classify the work item through deterministic rules."""

from __future__ import annotations

from typing import Any

from reverse_agent.architecture.contracts import DevelopmentWorkflowState, ExecutionEnvelope, GitHubWorkItem
from reverse_agent.architecture.risk_classifier import classify_risk


def classify_risk_node(state: DevelopmentWorkflowState) -> dict[str, Any]:
    item = GitHubWorkItem.from_mapping(state["work_item"])
    envelope = ExecutionEnvelope(item.requested_operations, item.requested_paths)
    decision = classify_risk(envelope)
    return {
        "risk_decision": decision.to_dict(),
        "node_trace": [*(state.get("node_trace") or []), "classify_risk"],
    }
