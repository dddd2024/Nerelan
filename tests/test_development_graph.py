from __future__ import annotations

from dataclasses import dataclass

from langgraph.checkpoint.memory import InMemorySaver

from reverse_agent.architecture.contracts import AuthorizationRequest, AuthorizationResult
from reverse_agent.architecture.risk import AcceptanceStatus, AuthorizationStatus
from reverse_agent.workflows.development_graph import build_development_graph


@dataclass
class RecordingPort:
    status: AuthorizationStatus = AuthorizationStatus.AUTHORIZED
    calls: int = 0

    def authorize(self, _request: AuthorizationRequest) -> AuthorizationResult:
        self.calls += 1
        return AuthorizationResult(self.status, () if self.status is AuthorizationStatus.AUTHORIZED else ("denied",))


def _input(operation: str) -> dict[str, object]:
    return {
        "work_item_input": {
            "schema_version": 1,
            "repository": "owner/repo",
            "item_number": 9,
            "immutable_observation_ref": "issue-node-9",
            "title": "Architecture shadow task",
            "acceptance_criteria": ["deterministic result"],
            "requested_operations": [operation],
            "requested_paths": ["reverse_agent/architecture/contracts.py"],
        },
        "planning_inputs": [
            {
                "schema_version": 1,
                "artifact_type": "story",
                "path_or_uri": "planning/story-9.md",
                "digest": "c" * 64,
                "summary": "Bounded story context",
            }
        ],
        "node_trace": [],
    }


def test_low_risk_path_bypasses_trust_port() -> None:
    port = RecordingPort()
    graph = build_development_graph(port)
    result = graph.invoke(_input("source_edit"), {"configurable": {"thread_id": "r1"}})
    assert result["acceptance_result"]["status"] == AcceptanceStatus.ACCEPTED.value
    assert port.calls == 0
    assert "request_trust_authorization" not in result["node_trace"]


def test_high_risk_path_invokes_trust_port() -> None:
    port = RecordingPort()
    result = build_development_graph(port).invoke(_input("dependency_change"), {"configurable": {"thread_id": "r2"}})
    assert result["acceptance_result"]["status"] == AcceptanceStatus.ACCEPTED.value
    assert port.calls == 1


def test_blocked_trust_result_cannot_become_executable() -> None:
    port = RecordingPort(AuthorizationStatus.BLOCKED)
    result = build_development_graph(port).invoke(_input("workflow_change"), {"configurable": {"thread_id": "blocked"}})
    assert result["acceptance_result"]["status"] == AcceptanceStatus.BLOCKED.value
    assert result["acceptance_result"]["executable"] is False


def test_checkpoint_resume_and_replay_are_deterministic() -> None:
    port = RecordingPort()
    graph = build_development_graph(port, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "checkpoint-thread"}}
    first = graph.invoke(_input("source_edit"), config)
    snapshot = graph.get_state(config)
    resumed = graph.invoke(None, config)
    replay = graph.invoke(_input("source_edit"), {"configurable": {"thread_id": "replay-thread"}})
    assert snapshot.values["acceptance_result"] == first["acceptance_result"]
    assert resumed["acceptance_result"] == first["acceptance_result"]
    assert replay["acceptance_result"] == first["acceptance_result"]
    assert replay["workflow_identity"] == first["workflow_identity"]
