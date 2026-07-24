"""Load read-only planning references."""

from __future__ import annotations

from typing import Any

from reverse_agent.adapters.bmad_planning import load_planning_reference
from reverse_agent.architecture.contracts import DevelopmentWorkflowState


def load_planning_context_node(state: DevelopmentWorkflowState) -> dict[str, Any]:
    references = [load_planning_reference(item).to_dict() for item in state.get("planning_inputs", [])]
    return {
        "planning_references": references,
        "node_trace": [*(state.get("node_trace") or []), "load_planning_context"],
    }
