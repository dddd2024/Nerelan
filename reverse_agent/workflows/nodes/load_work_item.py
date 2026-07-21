"""Load and validate one structured GitHub Work Item fixture.

Phase E: the workflow identity is produced by the trusted
``AuthorizedRiskPolicyProvider`` so it carries ``decision_id``,
``round_id`` and ``policy_digest``. The provider's canonical snapshot is
written into state; callers cannot supply their own snapshot.

If a caller supplies a ``risk_policy_snapshot`` in the initial state
(roadmap 8.1 prohibits this, but 8.3 requires us to detect it), the
value is preserved under ``caller_supplied_risk_policy_snapshot`` so
``classify_risk_node`` can verify it against the authorized snapshot and
block on divergence.
"""

from __future__ import annotations

import hashlib
from typing import Any

from reverse_agent.adapters.github_work_item import load_github_work_item
from reverse_agent.architecture.contracts import DevelopmentWorkflowState, stable_json
from reverse_agent.architecture.policy_provider import AuthorizedRiskPolicyProvider


def load_work_item_node(
    state: DevelopmentWorkflowState,
    *,
    provider: AuthorizedRiskPolicyProvider,
) -> dict[str, Any]:
    item = load_github_work_item(state["work_item_input"])
    workflow_id = "workflow-" + hashlib.sha256(stable_json(item.to_dict()).encode("utf-8")).hexdigest()[:20]
    # Phase E: identity is produced by the trusted provider, not by the caller.
    identity = provider.workflow_identity(
        workflow_id=workflow_id,
        work_item_identity=item.identity,
    )
    # Phase E: canonical snapshot comes from the provider; callers cannot
    # supply their own snapshot into initial state.
    snapshot = provider.provide()
    result: dict[str, Any] = {
        "work_item": item.to_dict(),
        "workflow_identity": identity.to_dict(),
        "risk_policy_snapshot": snapshot.to_dict(),
        "node_trace": [*(state.get("node_trace") or []), "load_work_item"],
    }
    # Phase E 8.3: preserve a caller-supplied snapshot so classify_risk can
    # verify it against the authorized snapshot and reject divergence.
    caller_snapshot = state.get("risk_policy_snapshot")
    if caller_snapshot is not None:
        result["caller_supplied_risk_policy_snapshot"] = caller_snapshot
    return result
