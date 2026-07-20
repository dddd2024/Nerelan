"""Load and validate one structured GitHub Work Item fixture."""

from __future__ import annotations

import hashlib
from typing import Any

from reverse_agent.adapters.github_work_item import load_github_work_item
from reverse_agent.architecture.contracts import DevelopmentWorkflowState, WorkflowIdentity, stable_json


def load_work_item_node(state: DevelopmentWorkflowState) -> dict[str, Any]:
    item = load_github_work_item(state["work_item_input"])
    workflow_id = "workflow-" + hashlib.sha256(stable_json(item.to_dict()).encode("utf-8")).hexdigest()[:20]
    identity = WorkflowIdentity(workflow_id=workflow_id, work_item_identity=item.identity)
    return {
        "work_item": item.to_dict(),
        "workflow_identity": identity.to_dict(),
        "node_trace": [*(state.get("node_trace") or []), "load_work_item"],
    }
