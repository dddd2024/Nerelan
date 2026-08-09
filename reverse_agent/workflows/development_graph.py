"""LangGraph-only, non-dispatching development workflow.

Phase E: the graph is built from a trusted ``AuthorizedRiskPolicyProvider``
and a ``TrustAuthorizationPort``. Callers cannot inject arbitrary policy
snapshots into initial state — the provider is the single authoritative
source (roadmap 8.1).

Phase F: an optional ``execution_node`` exposes one bounded LangGraph-native
seam between authorization and acceptance. When omitted the graph is byte-for-
behavior equivalent to the current Phase E shape; the seam is a pure
workflow-mechanics insertion point and does not introduce any second durable
task, event, evidence, or policy store.
"""

from __future__ import annotations

from functools import partial
from typing import Callable

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from reverse_agent.architecture.contracts import DevelopmentWorkflowState
from reverse_agent.architecture.policy_provider import AuthorizedRiskPolicyProvider
from reverse_agent.architecture.risk import AuthorizationStatus, WorkflowRoute
from reverse_agent.trust.authorization import TrustAuthorizationPort

from .nodes.acceptance_gate import acceptance_gate_node
from .nodes.classify_risk import classify_risk_node
from .nodes.load_planning_context import load_planning_context_node
from .nodes.load_work_item import load_work_item_node
from .nodes.request_authorization import request_authorization_node


def _classify_route(execution_node: Callable | None):
    """Route after classification: trust-required or blocked follow their
    existing paths; the standard path optionally traverses the supplied
    execution seam before acceptance.
    """

    def _route(state: DevelopmentWorkflowState) -> str:
        route = WorkflowRoute(state["risk_decision"]["route"])
        if route is WorkflowRoute.BLOCKED:
            return "acceptance_gate"
        if route is WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED:
            return "request_trust_authorization"
        return "execution_seam" if execution_node is not None else "acceptance_gate"

    return _route


def _post_authorization_route(execution_node: Callable | None):
    """Route after trust authorization: BLOCKED skips the seam; otherwise
    either traverse the supplied execution seam or jump straight to the
    acceptance gate.
    """

    def _route_authz(state: DevelopmentWorkflowState) -> str:
        authorization_result = state.get("authorization_result") or {}
        status = AuthorizationStatus(authorization_result.get("status", "BLOCKED"))
        if status is not AuthorizationStatus.AUTHORIZED:
            return "acceptance_gate"
        return "execution_seam" if execution_node is not None else "acceptance_gate"

    return _route_authz


def build_development_graph(
    port: TrustAuthorizationPort,
    *,
    provider: AuthorizedRiskPolicyProvider,
    checkpointer: InMemorySaver | None = None,
    execution_node: Callable | None = None,
):
    """Build the development workflow graph.

    Phase E: ``provider`` is required. It is the single authoritative source
    of ``RiskPolicySnapshot`` and ``WorkflowIdentity``. Callers cannot supply
    their own snapshot into initial state (roadmap 8.1).

    Phase F: ``execution_node`` is an optional LangGraph-native node callable
    ``state -> dict`` that is inserted between authorization and
    ``acceptance_gate``. When omitted the graph preserves the current Phase E
    behavior and does not traverse any execution seam. The seam is bounded:
    it operates over the existing ``DevelopmentWorkflowState`` only and never
    persists a second product truth.
    """

    builder = StateGraph(DevelopmentWorkflowState)
    builder.add_node("load_work_item", partial(load_work_item_node, provider=provider))
    builder.add_node("load_planning_context", load_planning_context_node)
    builder.add_node("classify_risk", partial(classify_risk_node, provider=provider))
    builder.add_node("request_trust_authorization", partial(request_authorization_node, port=port))
    if execution_node is not None:
        builder.add_node("execution_seam", execution_node)
    builder.add_node("acceptance_gate", acceptance_gate_node)
    builder.add_edge(START, "load_work_item")
    builder.add_edge("load_work_item", "load_planning_context")
    builder.add_edge("load_planning_context", "classify_risk")
    builder.add_conditional_edges("classify_risk", _classify_route(execution_node))
    builder.add_conditional_edges(
        "request_trust_authorization",
        _post_authorization_route(execution_node),
    )
    if execution_node is not None:
        builder.add_edge("execution_seam", "acceptance_gate")
    builder.add_edge("acceptance_gate", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())
