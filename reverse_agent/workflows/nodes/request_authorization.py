"""Request high-risk authorization through the narrow Trust port."""

from __future__ import annotations

from typing import Any

from reverse_agent.architecture.contracts import AuthorizationRequest, DevelopmentWorkflowState, ExecutionEnvelope, GitHubWorkItem, WorkflowIdentity
from reverse_agent.architecture.risk import RiskTier
from reverse_agent.trust.authorization import TrustAuthorizationPort


def request_authorization_node(state: DevelopmentWorkflowState, port: TrustAuthorizationPort) -> dict[str, Any]:
    item = GitHubWorkItem.from_mapping(state["work_item"])
    identity_payload = state["workflow_identity"]
    identity = WorkflowIdentity(
        workflow_id=identity_payload["workflow_id"],
        work_item_identity=identity_payload["work_item_identity"],
        attempt=identity_payload["attempt"],
    )
    request = AuthorizationRequest(
        workflow_identity=identity,
        risk_tier=RiskTier(state["risk_decision"]["risk_tier"]),
        envelope=ExecutionEnvelope(item.requested_operations, item.requested_paths),
    )
    result = port.authorize(request)
    return {
        "authorization_result": result.to_dict(),
        "node_trace": [*(state.get("node_trace") or []), "request_trust_authorization"],
    }
