"""LangGraph-only, non-dispatching development workflow."""

from __future__ import annotations

from functools import partial
from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from reverse_agent.architecture.contracts import DevelopmentWorkflowState
from reverse_agent.architecture.risk import WorkflowRoute
from reverse_agent.trust.authorization import TrustAuthorizationPort

from .nodes.acceptance_gate import acceptance_gate_node
from .nodes.classify_risk import classify_risk_node
from .nodes.load_planning_context import load_planning_context_node
from .nodes.load_work_item import load_work_item_node
from .nodes.request_authorization import request_authorization_node


def _route(state: DevelopmentWorkflowState) -> Literal["acceptance_gate", "request_trust_authorization"]:
    route = WorkflowRoute(state["risk_decision"]["route"])
    return "request_trust_authorization" if route is WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED else "acceptance_gate"


def build_development_graph(port: TrustAuthorizationPort, *, checkpointer: InMemorySaver | None = None):
    builder = StateGraph(DevelopmentWorkflowState)
    builder.add_node("load_work_item", load_work_item_node)
    builder.add_node("load_planning_context", load_planning_context_node)
    builder.add_node("classify_risk", classify_risk_node)
    builder.add_node("request_trust_authorization", partial(request_authorization_node, port=port))
    builder.add_node("acceptance_gate", acceptance_gate_node)
    builder.add_edge(START, "load_work_item")
    builder.add_edge("load_work_item", "load_planning_context")
    builder.add_edge("load_planning_context", "classify_risk")
    builder.add_conditional_edges("classify_risk", _route)
    builder.add_edge("request_trust_authorization", "acceptance_gate")
    builder.add_edge("acceptance_gate", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())
