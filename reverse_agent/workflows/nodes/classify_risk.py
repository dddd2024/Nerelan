"""Classify the work item through deterministic rules.

Phase E: the classifier must reject identity with missing decision_id,
round_id or policy_digest. The snapshot is verified against the trusted
provider — caller-supplied snapshots that diverge from the authorized
snapshot are rejected. The previous "fallback to policy's own ID when
identity is missing" behavior is removed.
"""

from __future__ import annotations

from typing import Any

from reverse_agent.architecture.contracts import (
    DevelopmentWorkflowState,
    ExecutionEnvelope,
    GitHubWorkItem,
    RiskPolicySnapshot,
)
from reverse_agent.architecture.policy_provider import (
    AuthorizedRiskPolicyProvider,
    PolicyTamperingError,
)
from reverse_agent.architecture.risk import WorkflowRoute
from reverse_agent.architecture.risk_classifier import classify_risk


def _blocked(reasons: list[str], trace: list[str]) -> dict[str, Any]:
    return {
        "risk_decision": {
            "schema_version": 1,
            "risk_tier": None,
            "route": WorkflowRoute.BLOCKED.value,
            "reasons": reasons,
        },
        "node_trace": [*trace, "classify_risk"],
    }


def classify_risk_node(
    state: DevelopmentWorkflowState,
    *,
    provider: AuthorizedRiskPolicyProvider,
) -> dict[str, Any]:
    """Classify risk using the provider-authorized policy snapshot.

    Phase E rejection rules (roadmap 8.3):
    - identity missing decision_id / round_id / policy_digest → BLOCKED
    - caller-supplied snapshot digest mismatch with identity → BLOCKED
    - provider verify failure (tampered snapshot) → BLOCKED
    - caller-supplied snapshot mismatch with authorized snapshot → BLOCKED
    """

    trace = [*(state.get("node_trace") or []), "classify_risk"]
    workflow_identity = state.get("workflow_identity") or {}
    decision_id = str(workflow_identity.get("decision_id") or "")
    round_id = str(workflow_identity.get("round_id") or "")
    policy_digest = str(workflow_identity.get("policy_digest") or "")

    # Phase E: identity must carry decision_id, round_id and policy_digest.
    if not decision_id:
        return _blocked(["identity_missing_decision_id"], trace)
    if not round_id:
        return _blocked(["identity_missing_round_id"], trace)
    if not policy_digest:
        return _blocked(["identity_missing_policy_digest"], trace)

    # Phase E: the caller-supplied snapshot (if any) is ignored; the provider
    # is the single authoritative source. Verify the authorized snapshot.
    try:
        authorized = provider.provide()
    except ValueError as exc:
        return _blocked([f"provider_error:{exc}"], trace)

    if authorized.policy_digest != policy_digest:
        return _blocked(
            [f"identity_policy_digest_mismatch:{policy_digest}:{authorized.policy_digest}"],
            trace,
        )
    if authorized.decision_id != decision_id or authorized.round_id != round_id:
        return _blocked(
            [f"identity_decision_round_mismatch:{decision_id}:{round_id}"],
            trace,
        )

    # Phase E 8.3: if a caller supplied a snapshot in initial state, verify it
    # matches the authorized snapshot. Divergence indicates tampering. The
    # caller-supplied value is preserved by ``load_work_item_node`` under
    # ``caller_supplied_risk_policy_snapshot`` so we can inspect it here even
    # after the canonical snapshot has been written into state.
    caller_snapshot_dict = state.get("caller_supplied_risk_policy_snapshot")
    if caller_snapshot_dict is not None:
        try:
            caller_snapshot = RiskPolicySnapshot.from_mapping(caller_snapshot_dict)
            provider.verify(caller_snapshot)
        except (ValueError, PolicyTamperingError) as exc:
            return _blocked([f"caller_snapshot_tampered:{exc}"], trace)

    item = GitHubWorkItem.from_mapping(state["work_item"])
    envelope = ExecutionEnvelope(item.requested_operations, item.requested_paths)
    capability_flag_risk = authorized.resolved_capability_risk_for(item.requested_operations)
    decision = classify_risk(
        envelope,
        path_risk_floor=authorized.path_risk_floor,
        capability_flag_risk=capability_flag_risk,
    )
    return {
        "risk_decision": decision.to_dict(),
        "risk_policy_snapshot": authorized.to_dict(),
        "node_trace": trace,
    }
