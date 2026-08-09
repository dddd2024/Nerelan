"""LangGraph parallel team subgraph tests.

Covers:
- structured team contracts (WorkerAssignment, WorkerExecutionResult, TeamExecutionResult);
- native LangGraph ``Send`` fan-out concurrency;
- real TaskStore + ExecutorRouter integration with two deterministic-fixture tasks;
- verifier rejection semantics;
- parent execution-node adapter;
- acceptance gate team-result propagation;
- full parent-graph end-to-end composition.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

import pytest

from reverse_agent.architecture.contracts import (
    AuthorizationRequest,
    AuthorizationResult,
    RiskPolicySnapshot,
    TeamExecutionResult,
    WorkerAssignment,
    WorkerExecutionResult,
)
from reverse_agent.architecture.policy_provider import AuthorizedRiskPolicyProvider
from reverse_agent.architecture.risk import (
    AcceptanceStatus,
    AuthorizationStatus,
    RiskTier,
    WorkflowRoute,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_execution import TaskExecutionService
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.workflows.development_graph import build_development_graph
from reverse_agent.workflows.team_graph import (
    TeamGraphError,
    build_team_execution_node,
    build_team_graph,
    build_worker_adapter,
)


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------


def test_worker_assignment_validates_required_fields() -> None:
    wa = WorkerAssignment(
        worker_id="w-a", role="implementer", task_id="task-1", workspace_root="/tmp/a"
    )
    d = wa.to_dict()
    assert d["worker_id"] == "w-a"
    assert d["role"] == "implementer"
    assert d["task_id"] == "task-1"
    assert d["workspace_root"] == "/tmp/a"
    roundtripped = WorkerAssignment.from_mapping(d)
    assert roundtripped.worker_id == "w-a"


def test_worker_assignment_rejects_empty_worker_id() -> None:
    with pytest.raises(ValueError):
        WorkerAssignment(worker_id="", role="r", task_id="t", workspace_root="/ws")


def test_worker_execution_result_deterministic_to_dict() -> None:
    wr = WorkerExecutionResult(
        worker_id="w-a",
        task_id="task-1",
        execution_id="exec-task-1",
        success=True,
        validation_exit_code=0,
        evidence_ids=("ev-1", "ev-2"),
        failure_classification="",
        failure_detail="",
    )
    d = wr.to_dict()
    assert d["worker_id"] == "w-a"
    assert d["success"] is True
    assert d["validation_exit_code"] == 0
    assert d["evidence_ids"] == ["ev-1", "ev-2"]


def test_team_execution_result_deterministic() -> None:
    wrs = (
        WorkerExecutionResult(
            worker_id="w-a",
            task_id="task-1",
            execution_id="exec-1",
            success=True,
            validation_exit_code=0,
        ),
        WorkerExecutionResult(
            worker_id="w-b",
            task_id="task-2",
            execution_id="exec-2",
            success=True,
            validation_exit_code=0,
        ),
    )
    team = TeamExecutionResult(accepted=True, worker_results=wrs)
    d = team.to_dict()
    assert d["accepted"] is True
    assert len(d["worker_results"]) == 2
    assert d["worker_results"][0]["worker_id"] == "w-a"
    assert d["worker_results"][1]["worker_id"] == "w-b"


def test_default_verifier_rejects_any_failed_worker() -> None:
    from reverse_agent.workflows.team_graph import _default_verifier

    wrs = (
        WorkerExecutionResult(
            worker_id="w-a", task_id="t1", execution_id="e1",
            success=True, validation_exit_code=0,
        ),
        WorkerExecutionResult(
            worker_id="w-b", task_id="t2", execution_id="e2",
            success=False, validation_exit_code=1, failure_classification="failed",
        ),
    )
    team = _default_verifier(wrs)
    assert team.accepted is False
    assert any("worker_failed" in r for r in team.reasons)


# ---------------------------------------------------------------------------
# Team graph fan-out concurrency proof
# ---------------------------------------------------------------------------


def test_team_graph_fan_out_is_parallel_via_barrier() -> None:
    """LangGraph ``Send`` must fan out worker branches in parallel. A
    ``threading.Barrier(2)`` inside fake workers must be reachable by both
    branches simultaneously; sequential execution would deadlock/timeout.
    """
    barrier = threading.Barrier(2, timeout=5)
    arrived: list[str] = []
    lock = threading.Lock()

    def fake_worker(wa: WorkerAssignment) -> WorkerExecutionResult:
        barrier.wait(5)
        with lock:
            arrived.append(wa.worker_id)
        return WorkerExecutionResult(
            worker_id=wa.worker_id,
            task_id=wa.task_id,
            execution_id="fake-exec",
            success=True,
            validation_exit_code=0,
        )

    team_graph = build_team_graph(worker=fake_worker)
    assignments = [
        WorkerAssignment(
            worker_id="w-a", role="a", task_id="t1", workspace_root="/ws1"
        ).to_dict(),
        WorkerAssignment(
            worker_id="w-b", role="b", task_id="t2", workspace_root="/ws2"
        ).to_dict(),
    ]
    result = team_graph.invoke({"assignments": assignments})
    assert len(arrived) == 2
    assert set(arrived) == {"w-a", "w-b"}
    team_result = result["team_execution_result"]
    assert team_result["accepted"] is True
    worker_ids = sorted(wr["worker_id"] for wr in team_result["worker_results"])
    assert worker_ids == ["w-a", "w-b"]


def test_team_graph_verifier_can_reject_despite_worker_success() -> None:
    """Both workers succeed, but the injected verifier rejects worker-b.
    The aggregate TeamExecutionResult must reflect that rejection while
    individual worker results remain successful.
    """

    def fake_worker(wa: WorkerAssignment) -> WorkerExecutionResult:
        return WorkerExecutionResult(
            worker_id=wa.worker_id,
            task_id=wa.task_id,
            execution_id="fake-exec",
            success=True,
            validation_exit_code=0,
        )

    def rejecting_verifier(
        worker_results: tuple[WorkerExecutionResult, ...],
    ) -> TeamExecutionResult:
        reasons: list[str] = []
        accepted = True
        for wr in worker_results:
            if wr.worker_id == "w-b":
                accepted = False
                reasons.append("verifier_rejected:worker-b")
        return TeamExecutionResult(
            accepted=accepted, worker_results=worker_results, reasons=tuple(reasons)
        )

    team_graph = build_team_graph(
        worker=fake_worker, verifier=rejecting_verifier
    )
    assignments = [
        WorkerAssignment(
            worker_id="w-a", role="a", task_id="t1", workspace_root="/ws1"
        ).to_dict(),
        WorkerAssignment(
            worker_id="w-b", role="b", task_id="t2", workspace_root="/ws2"
        ).to_dict(),
    ]
    result = team_graph.invoke({"assignments": assignments})
    team = result["team_execution_result"]
    assert team["accepted"] is False
    assert any("verifier_rejected" in r for r in team["reasons"])
    for wr in team["worker_results"]:
        assert wr["success"] is True


def test_team_graph_rejects_empty_assignments() -> None:
    def fake_worker(wa: WorkerAssignment) -> WorkerExecutionResult:
        return WorkerExecutionResult(
            worker_id=wa.worker_id,
            task_id=wa.task_id,
            execution_id="exec",
            success=True,
            validation_exit_code=0,
        )

    team_graph = build_team_graph(worker=fake_worker)
    with pytest.raises(TeamGraphError):
        team_graph.invoke({"assignments": []})


def test_team_graph_rejects_duplicate_worker_ids() -> None:
    def fake_worker(wa: WorkerAssignment) -> WorkerExecutionResult:
        return WorkerExecutionResult(
            worker_id=wa.worker_id,
            task_id=wa.task_id,
            execution_id="exec",
            success=True,
            validation_exit_code=0,
        )

    team_graph = build_team_graph(worker=fake_worker)
    assignments = [
        WorkerAssignment(
            worker_id="w-a", role="a", task_id="t1", workspace_root="/ws1"
        ).to_dict(),
        WorkerAssignment(
            worker_id="w-a", role="b", task_id="t2", workspace_root="/ws2"
        ).to_dict(),
    ]
    with pytest.raises(TeamGraphError):
        team_graph.invoke({"assignments": assignments})


# ---------------------------------------------------------------------------
# Real TaskStore + ExecutorRouter integration
# ---------------------------------------------------------------------------


def test_team_graph_real_two_worker_integration(tmp_path) -> None:
    """Two real deterministic_fixture tasks, one shared TaskStore, one
    ExecutorRouter, one TaskExecutionService. The team graph must fan out
    through ``Send``, each worker must persist real evidence/events/changed
    files, and both tasks must reach ``READY_FOR_REVIEW_FIXTURE``.
    """
    db_path = str(tmp_path / "real.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    service = TaskExecutionService(store=store, router=router)
    worker_adapter = build_worker_adapter(service=service)

    task_a = store.create_task(
        title="real-a", executor_kind="deterministic_fixture", idempotency_key="real-a"
    )
    task_b = store.create_task(
        title="real-b", executor_kind="deterministic_fixture", idempotency_key="real-b"
    )
    assert task_a.id != task_b.id

    assignments = [
        WorkerAssignment(
            worker_id="w-a", role="a",
            task_id=task_a.id, workspace_root=str(tmp_path / "ws-a"),
        ).to_dict(),
        WorkerAssignment(
            worker_id="w-b", role="b",
            task_id=task_b.id, workspace_root=str(tmp_path / "ws-b"),
        ).to_dict(),
    ]

    team_graph = build_team_graph(worker=worker_adapter)
    result = team_graph.invoke({"assignments": assignments})

    team = result["team_execution_result"]
    assert team["accepted"] is True
    assert len(team["worker_results"]) == 2

    task_a_final = store.get_task(task_a.id)
    task_b_final = store.get_task(task_b.id)
    assert task_a_final.status == "READY_FOR_REVIEW_FIXTURE"
    assert task_b_final.status == "READY_FOR_REVIEW_FIXTURE"
    assert task_a_final.validation_exit_code == 0
    assert task_b_final.validation_exit_code == 0
    assert task_a_final.evidence_refs
    assert task_b_final.evidence_refs
    assert task_a_final.changed_files
    assert task_b_final.changed_files

    # Proves no executor_kind = "multi_agent" was created
    assert task_a_final.executor_kind == "deterministic_fixture"
    assert task_b_final.executor_kind == "deterministic_fixture"

    for wr in team["worker_results"]:
        assert wr["success"] is True
        assert wr["validation_exit_code"] == 0
        assert wr["evidence_ids"]


def test_team_graph_verifier_reject_with_real_tasks(tmp_path) -> None:
    """Both real tasks succeed at executor level, but an injected verifier
    rejects worker-b. Durable tasks stay READY_FOR_REVIEW_FIXTURE; team
    aggregate is rejected with deterministic reasons.
    """
    db_path = str(tmp_path / "verifier-reject.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    service = TaskExecutionService(store=store, router=router)
    worker_adapter = build_worker_adapter(service=service)

    task_a = store.create_task(title="va", idempotency_key="va")
    task_b = store.create_task(title="vb", idempotency_key="vb")

    def rejecting_verifier(
        worker_results: tuple[WorkerExecutionResult, ...],
    ) -> TeamExecutionResult:
        reasons: list[str] = ["verifier_rejected:worker-b:w-b"]
        return TeamExecutionResult(
            accepted=False,
            worker_results=worker_results,
            reasons=tuple(reasons),
        )

    team_graph = build_team_graph(
        worker=worker_adapter, verifier=rejecting_verifier
    )
    assignments = [
        WorkerAssignment(
            worker_id="w-a", role="a",
            task_id=task_a.id, workspace_root=str(tmp_path / "ws-va"),
        ).to_dict(),
        WorkerAssignment(
            worker_id="w-b", role="b",
            task_id=task_b.id, workspace_root=str(tmp_path / "ws-vb"),
        ).to_dict(),
    ]
    result = team_graph.invoke({"assignments": assignments})

    team = result["team_execution_result"]
    assert team["accepted"] is False
    assert any("verifier_rejected" in r for r in team["reasons"])

    assert store.get_task(task_a.id).status == "READY_FOR_REVIEW_FIXTURE"
    assert store.get_task(task_b.id).status == "READY_FOR_REVIEW_FIXTURE"
    for wr in team["worker_results"]:
        assert wr["success"] is True


# ---------------------------------------------------------------------------
# Parent adapter
# ---------------------------------------------------------------------------


def test_parent_adapter_maps_team_assignments_to_team_result() -> None:
    """The parent adapter must read ``team_assignments`` from parent state,
    invoke the internal team graph, and return only ``team_execution_result``
    plus a node-trace marker. It must NOT dump TaskStore rows/evidence into
    parent state.
    """
    calls: list[dict] = []

    def fake_worker(wa: WorkerAssignment) -> WorkerExecutionResult:
        calls.append({"worker_id": wa.worker_id, "task_id": wa.task_id})
        return WorkerExecutionResult(
            worker_id=wa.worker_id,
            task_id=wa.task_id,
            execution_id="fake-exec",
            success=True,
            validation_exit_code=0,
        )

    team_graph = build_team_graph(worker=fake_worker)
    adapter = build_team_execution_node(team_graph=team_graph)

    parent_state: dict[str, Any] = {
        "team_assignments": [
            WorkerAssignment(
                worker_id="w-a", role="a", task_id="t1", workspace_root="/ws1"
            ).to_dict(),
            WorkerAssignment(
                worker_id="w-b", role="b", task_id="t2", workspace_root="/ws2"
            ).to_dict(),
        ],
        "node_trace": ["classify_risk"],
    }
    out = adapter(parent_state)

    assert len(calls) == 2
    assert {c["worker_id"] for c in calls} == {"w-a", "w-b"}
    assert "team_execution_result" in out
    assert out["team_execution_result"]["accepted"] is True
    assert out["node_trace"] == ["classify_risk", "team_execution"]

    # Must NOT leak internal team state or durable TaskStore rows into output
    forbidden_keys = {"worker_results", "assignments", "assignment"}
    assert not forbidden_keys.intersection(out.keys())


# ---------------------------------------------------------------------------
# Acceptance gate: team_execution_result propagation
# ---------------------------------------------------------------------------


def test_acceptance_gate_no_team_result_uses_existing_behavior() -> None:
    """Without team_execution_result, the gate must behave as before #151."""
    from reverse_agent.workflows.nodes.acceptance_gate import acceptance_gate_node

    state: dict[str, Any] = {
        "risk_decision": {"route": WorkflowRoute.STANDARD_PATH.value, "reasons": ()},
        "node_trace": [],
    }
    out = acceptance_gate_node(state)
    assert out["acceptance_result"]["status"] == AcceptanceStatus.ACCEPTED.value
    assert out["acceptance_result"]["executable"] is True


def test_acceptance_gate_accepted_team_passes_through() -> None:
    from reverse_agent.workflows.nodes.acceptance_gate import acceptance_gate_node

    state: dict[str, Any] = {
        "risk_decision": {"route": WorkflowRoute.STANDARD_PATH.value, "reasons": ()},
        "team_execution_result": {"accepted": True, "worker_results": [], "reasons": []},
        "node_trace": [],
    }
    out = acceptance_gate_node(state)
    assert out["acceptance_result"]["status"] == AcceptanceStatus.ACCEPTED.value
    assert out["acceptance_result"]["executable"] is True


def test_acceptance_gate_rejected_team_blocks() -> None:
    """When team_execution_result.accepted == False, the gate must return
    BLOCKED / non-executable with the team reasons, regardless of risk route.
    """
    from reverse_agent.workflows.nodes.acceptance_gate import acceptance_gate_node

    state: dict[str, Any] = {
        "risk_decision": {"route": WorkflowRoute.STANDARD_PATH.value, "reasons": ()},
        "team_execution_result": {
            "accepted": False,
            "worker_results": [],
            "reasons": ("verifier_rejected:w-b",),
        },
        "node_trace": [],
    }
    out = acceptance_gate_node(state)
    assert out["acceptance_result"]["status"] == AcceptanceStatus.BLOCKED.value
    assert out["acceptance_result"]["executable"] is False
    assert "verifier_rejected" in " ".join(out["acceptance_result"]["reasons"])


def test_acceptance_gate_rejected_team_without_reasons_gets_default() -> None:
    from reverse_agent.workflows.nodes.acceptance_gate import acceptance_gate_node

    state: dict[str, Any] = {
        "risk_decision": {"route": WorkflowRoute.STANDARD_PATH.value, "reasons": ()},
        "team_execution_result": {
            "accepted": False,
            "worker_results": [],
            "reasons": [],
        },
        "node_trace": [],
    }
    out = acceptance_gate_node(state)
    assert out["acceptance_result"]["status"] == AcceptanceStatus.BLOCKED.value
    assert "team_execution_rejected" in " ".join(out["acceptance_result"]["reasons"])


# ---------------------------------------------------------------------------
# End-to-end parent graph integration
# ---------------------------------------------------------------------------


@dataclass
class RecordingPort:
    status: AuthorizationStatus = AuthorizationStatus.AUTHORIZED
    calls: int = 0

    def authorize(self, _request: AuthorizationRequest) -> AuthorizationResult:
        self.calls += 1
        return AuthorizationResult(
            self.status,
            () if self.status is AuthorizationStatus.AUTHORIZED else ("denied",),
        )


def _contract() -> dict:
    return {
        "decision_id": "decision_t",
        "round_id": "round_t",
        "path_risk_floor": [["**/secrets/**", "R3"]],
        "capability_risk_rules": [
            {"operation": "network_access", "risk_tier": "R2"},
            {"operation": "unknown_binary_execution", "risk_tier": "R3"},
            {"operation": "destructive", "risk_tier": "R3"},
        ],
    }


def _provider() -> AuthorizedRiskPolicyProvider:
    return AuthorizedRiskPolicyProvider(_contract())


def _input(operation: str, *, paths: list[str] | None = None) -> dict[str, object]:
    return {
        "work_item_input": {
            "schema_version": 1,
            "repository": "owner/repo",
            "item_number": 151,
            "immutable_observation_ref": "issue-151",
            "title": "Team adapter task",
            "acceptance_criteria": ["deterministic result"],
            "requested_operations": [operation],
            "requested_paths": paths or ["reverse_agent/architecture/contracts.py"],
        },
        "planning_inputs": [{
            "schema_version": 1,
            "artifact_type": "story",
            "path_or_uri": "planning/story-151.md",
            "digest": "c" * 64,
            "summary": "Bounded story context",
        }],
        "team_assignments": [
            WorkerAssignment(
                worker_id="w-a", role="a", task_id="t1", workspace_root="/ws1"
            ).to_dict(),
            WorkerAssignment(
                worker_id="w-b", role="b", task_id="t2", workspace_root="/ws2"
            ).to_dict(),
        ],
        "node_trace": [],
    }


def test_parent_graph_standard_path_with_team_execution() -> None:
    port = RecordingPort()
    team_graph = build_team_graph(worker=_team_fake_worker)
    execution_node = build_team_execution_node(team_graph=team_graph)
    graph = build_development_graph(port, provider=_provider(), execution_node=execution_node)
    result = graph.invoke(_input("source_edit"), {"configurable": {"thread_id": "team-r1"}})
    trace = result["node_trace"]
    assert "team_execution" in trace
    assert result["team_execution_result"]["accepted"] is True
    assert result["acceptance_result"]["status"] == AcceptanceStatus.ACCEPTED.value
    assert result["acceptance_result"]["executable"] is True
    assert port.calls == 0


def test_parent_graph_trust_path_with_team_execution() -> None:
    port = RecordingPort()
    team_graph = build_team_graph(worker=_team_fake_worker)
    execution_node = build_team_execution_node(team_graph=team_graph)
    graph = build_development_graph(port, provider=_provider(), execution_node=execution_node)
    result = graph.invoke(
        _input("dependency_change"), {"configurable": {"thread_id": "team-r2"}}
    )
    trace = result["node_trace"]
    assert "request_trust_authorization" in trace
    assert "team_execution" in trace
    assert result["acceptance_result"]["status"] == AcceptanceStatus.ACCEPTED.value
    assert port.calls == 1


def test_parent_graph_blocked_authorization_skips_team() -> None:
    port = RecordingPort(AuthorizationStatus.BLOCKED)
    team_graph = build_team_graph(worker=_team_fake_worker)
    execution_node = build_team_execution_node(team_graph=team_graph)
    graph = build_development_graph(port, provider=_provider(), execution_node=execution_node)
    result = graph.invoke(
        _input("workflow_change"), {"configurable": {"thread_id": "team-blocked"}}
    )
    assert "team_execution" not in result["node_trace"]
    assert result["acceptance_result"]["status"] == AcceptanceStatus.BLOCKED.value
    assert port.calls == 1


def test_parent_graph_verifier_reject_blocks_acceptance() -> None:
    port = RecordingPort()

    def rejecting_worker(wa: WorkerAssignment) -> WorkerExecutionResult:
        return WorkerExecutionResult(
            worker_id=wa.worker_id,
            task_id=wa.task_id,
            execution_id="exec",
            success=True,
            validation_exit_code=0,
        )

    def rejecting_verifier(
        worker_results: tuple[WorkerExecutionResult, ...],
    ) -> TeamExecutionResult:
        return TeamExecutionResult(
            accepted=False,
            worker_results=worker_results,
            reasons=("verifier_rejected:all",),
        )

    team_graph = build_team_graph(
        worker=rejecting_worker, verifier=rejecting_verifier
    )
    execution_node = build_team_execution_node(team_graph=team_graph)
    graph = build_development_graph(port, provider=_provider(), execution_node=execution_node)
    result = graph.invoke(_input("source_edit"), {"configurable": {"thread_id": "team-vr"}})
    assert result["team_execution_result"]["accepted"] is False
    assert result["acceptance_result"]["status"] == AcceptanceStatus.BLOCKED.value
    assert result["acceptance_result"]["executable"] is False


def _team_fake_worker(wa: WorkerAssignment) -> WorkerExecutionResult:
    return WorkerExecutionResult(
        worker_id=wa.worker_id,
        task_id=wa.task_id,
        execution_id="fake-exec",
        success=True,
        validation_exit_code=0,
    )
