"""LangGraph-native parallel worker team subgraph.

Owns:
- workflow routing via ``langgraph.types.Send`` fan-out;
- reducer/join of structured worker results;
- verifier routing;
- checkpoint mechanics via the inherited ``CompiledStateGraph``.

Does NOT own:
- durable task truth (that lives in ``TaskStore``);
- concrete executor selection (``ExecutorRouter``);
- a custom thread pool or scheduler.

The internal team graph uses a team-specific state schema.
``build_team_execution_node`` in :mod:`reverse_agent.workflows.team_graph`
provides the thin adapter to the parent ``DevelopmentWorkflowState``.
"""

from __future__ import annotations

import operator
from dataclasses import asdict
from typing import Annotated, Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from reverse_agent.architecture.contracts import (
    TeamExecutionResult,
    WorkerAssignment,
    WorkerExecutionResult,
)


class TeamGraphError(Exception):
    """Raised on invalid team-graph input or construction."""


class TeamWorkflowState(TypedDict, total=False):
    assignments: list[dict[str, Any]]
    assignment: dict[str, Any]
    worker_results: Annotated[list[dict[str, Any]], operator.add]
    team_execution_result: dict[str, Any]


def _default_verifier(
    worker_results: tuple[WorkerExecutionResult, ...],
) -> TeamExecutionResult:
    reasons: list[str] = []
    accepted = True
    for wr in worker_results:
        if not wr.success:
            accepted = False
            reasons.append(
                f"worker_failed:{wr.worker_id}:task={wr.task_id}:"
                f"classification={wr.failure_classification or 'unknown'}"
            )
    return TeamExecutionResult(
        accepted=accepted,
        worker_results=worker_results,
        reasons=tuple(reasons),
    )


def _validate_assignments(assignments: list[dict[str, Any]]) -> list[WorkerAssignment]:
    if not assignments:
        raise TeamGraphError("team_assignments_empty")
    parsed: list[WorkerAssignment] = []
    seen: set[str] = set()
    for idx, a in enumerate(assignments):
        try:
            wa = WorkerAssignment.from_mapping(a)
        except (ValueError, TypeError) as exc:
            raise TeamGraphError(f"invalid_assignment[{idx}]:{exc}") from exc
        if wa.worker_id in seen:
            raise TeamGraphError(f"duplicate_worker_id:{wa.worker_id}")
        seen.add(wa.worker_id)
        parsed.append(wa)
    return parsed


def build_team_graph(
    *,
    worker: Callable[[WorkerAssignment], WorkerExecutionResult],
    verifier: (
        Callable[[tuple[WorkerExecutionResult, ...]], TeamExecutionResult] | None
    ) = None,
) -> StateGraph:
    """Build a compiled LangGraph team subgraph.

    Uses native ``Send`` for parallel fan-out, a reducer to join worker
    results, and an injectable verifier callable for aggregate acceptance.
    """

    default_ver = verifier or _default_verifier

    def _dispatch_workers(state: TeamWorkflowState) -> dict[str, Any]:
        """No-op node that prepares for fan-out. The actual ``Send`` routing
        lives in the conditional-edges function attached to this node."""

        _validate_assignments(list(state.get("assignments") or []))
        return {}

    def _worker_node(state: TeamWorkflowState) -> dict[str, Any]:
        assignment = state.get("assignment", {})
        try:
            wa = WorkerAssignment.from_mapping(assignment)
        except (ValueError, TypeError) as exc:
            raise TeamGraphError(f"worker_assignment_invalid:{exc}") from exc
        result = worker(wa)
        return {"worker_results": [result.to_dict()]}

    def _verifier_node(state: TeamWorkflowState) -> dict[str, Any]:
        raw_results = list(state.get("worker_results") or [])
        worker_results: list[WorkerExecutionResult] = []
        for raw in raw_results:
            worker_results.append(WorkerExecutionResult(
                worker_id=raw.get("worker_id", ""),
                task_id=raw.get("task_id", ""),
                execution_id=raw.get("execution_id", ""),
                success=bool(raw.get("success", False)),
                validation_exit_code=int(raw.get("validation_exit_code", -1)),
                evidence_ids=tuple(raw.get("evidence_ids", ())),
                failure_classification=raw.get("failure_classification", ""),
                failure_detail=raw.get("failure_detail", ""),
                reasons=tuple(raw.get("reasons", ())),
            ))
        worker_results.sort(key=lambda wr: wr.worker_id)
        team = default_ver(tuple(worker_results))
        return {"team_execution_result": team.to_dict()}

    builder = StateGraph(TeamWorkflowState)
    builder.add_node("dispatch_workers", _dispatch_workers)
    builder.add_node("worker", _worker_node)
    builder.add_node("verifier", _verifier_node)
    builder.add_edge(START, "dispatch_workers")
    builder.add_conditional_edges(
        "dispatch_workers",
        lambda state: [
            Send("worker", {"assignment": a.to_dict()})
            for a in _validate_assignments(list(state.get("assignments") or []))
        ],
        ["worker"],
    )
    builder.add_edge("worker", "verifier")
    builder.add_edge("verifier", END)
    return builder.compile()


def build_team_execution_node(
    *,
    team_graph: StateGraph,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Thin parent execution-node adapter.

    Reads ``team_assignments`` from the parent ``DevelopmentWorkflowState``,
    invokes the internal team subgraph, and returns only
    ``team_execution_result`` plus a node-trace marker to the parent.
    """

    def _adapter(state: dict[str, Any]) -> dict[str, Any]:
        assignments = list(state.get("team_assignments") or [])
        internal_state: TeamWorkflowState = {"assignments": assignments}
        internal_result = team_graph.invoke(internal_state)
        team_result = internal_result.get("team_execution_result", {})
        trace = list(state.get("node_trace") or [])
        return {
            "team_execution_result": team_result,
            "node_trace": trace + ["team_execution"],
        }

    return _adapter


def build_worker_adapter(
    *,
    service: Any,
) -> Callable[[WorkerAssignment], WorkerExecutionResult]:
    """Thin callable that executes a ``WorkerAssignment`` through
    ``TaskExecutionService.execute`` and returns a structured
    ``WorkerExecutionResult``.
    """

    def _adapt(assignment: WorkerAssignment) -> WorkerExecutionResult:
        try:
            outcome = service.execute(
                assignment.task_id,
                workspace_root=assignment.workspace_root,
            )
            return WorkerExecutionResult(
                worker_id=assignment.worker_id,
                task_id=assignment.task_id,
                execution_id=outcome.execution_id,
                success=outcome.success,
                validation_exit_code=outcome.validation_exit_code,
                evidence_ids=outcome.evidence_ids,
                failure_classification=outcome.failure_classification,
                failure_detail=outcome.failure_detail,
            )
        except Exception as exc:
            return WorkerExecutionResult(
                worker_id=assignment.worker_id,
                task_id=assignment.task_id,
                execution_id="",
                success=False,
                validation_exit_code=-1,
                failure_classification="executor_error",
                failure_detail=f"{exc.__class__.__name__}:{exc}",
                reasons=(f"worker_exception:{exc.__class__.__name__}",),
            )

    return _adapt
