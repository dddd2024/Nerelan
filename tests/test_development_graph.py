from __future__ import annotations

from dataclasses import dataclass

from langgraph.checkpoint.memory import InMemorySaver

from reverse_agent.architecture.contracts import (
    AuthorizationRequest,
    AuthorizationResult,
    RiskPolicySnapshot,
)
from reverse_agent.architecture.policy_provider import AuthorizedRiskPolicyProvider
from reverse_agent.architecture.risk import AcceptanceStatus, AuthorizationStatus, RiskTier, WorkflowRoute
from reverse_agent.workflows.development_graph import build_development_graph


@dataclass
class RecordingPort:
    status: AuthorizationStatus = AuthorizationStatus.AUTHORIZED
    calls: int = 0

    def authorize(self, _request: AuthorizationRequest) -> AuthorizationResult:
        self.calls += 1
        return AuthorizationResult(self.status, () if self.status is AuthorizationStatus.AUTHORIZED else ("denied",))


def _contract(
    *,
    decision_id: str = "decision_one",
    round_id: str = "round_one",
    path_risk_floor: list | None = None,
    capability_risk_rules: list | None = None,
) -> dict:
    return {
        "decision_id": decision_id,
        "round_id": round_id,
        "path_risk_floor": path_risk_floor
        if path_risk_floor is not None
        else [
            [".github/workflows/**", "R2"],
            ["pyproject.toml", "R2"],
            ["project_state/decision_packet.md", "R2"],
            ["project_state/gates/**", "R2"],
            ["**/secrets/**", "R3"],
            ["**/*.exe", "R3"],
        ],
        "capability_risk_rules": capability_risk_rules
        if capability_risk_rules is not None
        else [
            {"operation": "network_access", "risk_tier": "R2"},
            {"operation": "unknown_binary_execution", "risk_tier": "R3"},
            {"operation": "destructive", "risk_tier": "R3"},
        ],
    }


def _provider(
    *,
    decision_id: str = "decision_one",
    round_id: str = "round_one",
    path_risk_floor: list | None = None,
    capability_risk_rules: list | None = None,
) -> AuthorizedRiskPolicyProvider:
    return AuthorizedRiskPolicyProvider(
        _contract(
            decision_id=decision_id,
            round_id=round_id,
            path_risk_floor=path_risk_floor,
            capability_risk_rules=capability_risk_rules,
        )
    )


def _policy(*, decision_id: str = "decision_one", round_id: str = "round_one") -> RiskPolicySnapshot:
    return _provider(decision_id=decision_id, round_id=round_id).provide()


def _input(
    operation: str,
    *,
    paths: list[str] | None = None,
    policy: RiskPolicySnapshot | None = None,
) -> dict[str, object]:
    """Build graph input. Phase E: caller does NOT supply the snapshot; the
    provider generates it inside ``load_work_item_node``. The ``policy``
    argument is kept only for the tampering tests (caller-supplied snapshot).
    """

    state: dict[str, object] = {
        "work_item_input": {
            "schema_version": 1,
            "repository": "owner/repo",
            "item_number": 9,
            "immutable_observation_ref": "issue-node-9",
            "title": "Architecture shadow task",
            "acceptance_criteria": ["deterministic result"],
            "requested_operations": [operation],
            "requested_paths": paths if paths is not None else ["reverse_agent/architecture/contracts.py"],
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
    if policy is not None:
        state["risk_policy_snapshot"] = policy.to_dict()
    return state


def test_low_risk_path_bypasses_trust_port() -> None:
    port = RecordingPort()
    graph = build_development_graph(port, provider=_provider())
    result = graph.invoke(_input("source_edit"), {"configurable": {"thread_id": "r1"}})
    assert result["acceptance_result"]["status"] == AcceptanceStatus.ACCEPTED.value
    assert port.calls == 0
    assert "request_trust_authorization" not in result["node_trace"]


def test_high_risk_path_invokes_trust_port() -> None:
    port = RecordingPort()
    result = build_development_graph(port, provider=_provider()).invoke(
        _input("dependency_change"), {"configurable": {"thread_id": "r2"}}
    )
    assert result["acceptance_result"]["status"] == AcceptanceStatus.ACCEPTED.value
    assert port.calls == 1


def test_blocked_trust_result_cannot_become_executable() -> None:
    port = RecordingPort(AuthorizationStatus.BLOCKED)
    result = build_development_graph(port, provider=_provider()).invoke(
        _input("workflow_change"), {"configurable": {"thread_id": "blocked"}}
    )
    assert result["acceptance_result"]["status"] == AcceptanceStatus.BLOCKED.value
    assert result["acceptance_result"]["executable"] is False


def test_checkpoint_resume_and_replay_are_deterministic() -> None:
    port = RecordingPort()
    graph = build_development_graph(port, provider=_provider(), checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "checkpoint-thread"}}
    first = graph.invoke(_input("source_edit"), config)
    snapshot = graph.get_state(config)
    resumed = graph.invoke(None, config)
    replay = graph.invoke(_input("source_edit"), {"configurable": {"thread_id": "replay-thread"}})
    assert snapshot.values["acceptance_result"] == first["acceptance_result"]
    assert resumed["acceptance_result"] == first["acceptance_result"]
    assert replay["acceptance_result"] == first["acceptance_result"]
    assert replay["workflow_identity"] == first["workflow_identity"]


# --- Phase D: end-to-end runtime risk wiring ----------------------------


def test_workflow_path_source_edit_routes_to_trust_authorization() -> None:
    """Editing a workflow file must route to Trust Authorization (R2)."""

    port = RecordingPort()
    graph = build_development_graph(port, provider=_provider())
    result = graph.invoke(
        _input("source_edit", paths=[".github/workflows/ci.yml"]),
        {"configurable": {"thread_id": "workflow-r2"}},
    )
    assert result["risk_decision"]["route"] == WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED.value
    assert result["risk_decision"]["risk_tier"] == RiskTier.R2.value
    assert port.calls == 1


def test_dependency_path_source_edit_routes_to_trust_authorization() -> None:
    """Editing pyproject.toml must route to Trust Authorization (R2)."""

    port = RecordingPort()
    graph = build_development_graph(port, provider=_provider())
    result = graph.invoke(
        _input("source_edit", paths=["pyproject.toml"]),
        {"configurable": {"thread_id": "pyproject-r2"}},
    )
    assert result["risk_decision"]["route"] == WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED.value
    assert result["risk_decision"]["risk_tier"] == RiskTier.R2.value


def test_decision_or_gate_path_routes_to_trust_authorization() -> None:
    """Editing a Decision/gate artifact must route to Trust Authorization (R2)."""

    port = RecordingPort()
    graph = build_development_graph(port, provider=_provider())
    result = graph.invoke(
        _input("source_edit", paths=["project_state/gates/command_plan.json"]),
        {"configurable": {"thread_id": "gate-r2"}},
    )
    assert result["risk_decision"]["route"] == WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED.value
    assert result["risk_decision"]["risk_tier"] == RiskTier.R2.value


def test_secret_path_routes_to_trust_authorization_at_r3() -> None:
    """Secrets paths must route to Trust Authorization at R3."""

    port = RecordingPort()
    graph = build_development_graph(port, provider=_provider())
    result = graph.invoke(
        _input("source_edit", paths=["config/secrets/api.key"]),
        {"configurable": {"thread_id": "secrets-r3"}},
    )
    assert result["risk_decision"]["route"] == WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED.value
    assert result["risk_decision"]["risk_tier"] == RiskTier.R3.value


def test_binary_path_routes_to_trust_authorization_at_r3() -> None:
    """Binary paths must route to Trust Authorization at R3."""

    port = RecordingPort()
    graph = build_development_graph(port, provider=_provider())
    result = graph.invoke(
        _input("source_edit", paths=["tools/debugger.exe"]),
        {"configurable": {"thread_id": "binary-r3"}},
    )
    assert result["risk_decision"]["route"] == WorkflowRoute.TRUST_AUTHORIZATION_REQUIRED.value
    assert result["risk_decision"]["risk_tier"] == RiskTier.R3.value


def test_policy_snapshot_is_propagated_through_state() -> None:
    """The classify node must publish the snapshot dict back into state."""

    port = RecordingPort()
    provider = _provider()
    graph = build_development_graph(port, provider=provider)
    result = graph.invoke(
        _input("source_edit"),
        {"configurable": {"thread_id": "snapshot-propagation"}},
    )
    snapshot = result.get("risk_policy_snapshot")
    assert snapshot is not None
    expected = provider.provide()
    assert snapshot["decision_id"] == expected.decision_id
    assert snapshot["round_id"] == expected.round_id
    assert snapshot["policy_digest"] == expected.policy_digest


# --- Phase E: provider-bound identity + tampering rejection --------------


def test_load_work_item_identity_carries_decision_round_and_digest() -> None:
    """Phase E 8.2: identity must carry decision_id, round_id, policy_digest."""

    port = RecordingPort()
    provider = _provider(decision_id="decision_e", round_id="round_e")
    graph = build_development_graph(port, provider=provider)
    result = graph.invoke(
        _input("source_edit"),
        {"configurable": {"thread_id": "identity-binding"}},
    )
    identity = result["workflow_identity"]
    assert identity["decision_id"] == "decision_e"
    assert identity["round_id"] == "round_e"
    assert identity["policy_digest"]
    assert len(identity["policy_digest"]) == 64


def test_classify_risk_rejects_tampered_caller_supplied_snapshot() -> None:
    """Phase E 8.3: caller-supplied snapshot that diverges from the
    authorized snapshot must be rejected (BLOCKED).
    """

    port = RecordingPort()
    provider = _provider()
    # Caller supplies a snapshot with a tampered digest (different decision_id).
    tampered = _provider(decision_id="decision_OTHER").provide()
    graph = build_development_graph(port, provider=provider)
    result = graph.invoke(
        _input("source_edit", policy=tampered),
        {"configurable": {"thread_id": "tampered-snapshot"}},
    )
    assert result["risk_decision"]["route"] == WorkflowRoute.BLOCKED.value
    reasons = " ".join(result["risk_decision"]["reasons"])
    assert "caller_snapshot_tampered" in reasons or "identity" in reasons


def test_classify_risk_rejects_lowered_path_risk_rule() -> None:
    """Phase E 8.4 test 3: lowering a path-risk rule must be rejected by
    the provider (caller cannot weaken the authorized floor).
    """

    port = RecordingPort()
    provider = _provider()
    # Caller supplies a snapshot that lowers .github/workflows from R2 to R1.
    lowered_floor = [
        [".github/workflows/**", "R1"],  # lowered from R2
        ["**/secrets/**", "R3"],
    ]
    tampered = _provider(path_risk_floor=lowered_floor).provide()
    graph = build_development_graph(port, provider=provider)
    result = graph.invoke(
        _input("source_edit", paths=[".github/workflows/ci.yml"], policy=tampered),
        {"configurable": {"thread_id": "lowered-rule"}},
    )
    assert result["risk_decision"]["route"] == WorkflowRoute.BLOCKED.value


def test_classify_risk_rejects_replaced_policy_digest() -> None:
    """Phase E 8.4 test 4: replacing the policy digest must be rejected."""

    port = RecordingPort()
    provider = _provider()
    # Build a snapshot from the same provider but mutate the digest.
    snapshot = provider.provide()
    tampered_dict = snapshot.to_dict()
    tampered_dict["policy_digest"] = "a" * 64  # forged digest
    graph = build_development_graph(port, provider=provider)
    result = graph.invoke(
        _input("source_edit", policy=RiskPolicySnapshot.from_mapping(tampered_dict)),
        {"configurable": {"thread_id": "replaced-digest"}},
    )
    assert result["risk_decision"]["route"] == WorkflowRoute.BLOCKED.value


def test_caller_without_policy_snapshot_still_proceeds_via_provider() -> None:
    """Phase E 8.4 test 6: a caller that does not supply a policy snapshot
    still proceeds normally — the provider is the authoritative source.
    """

    port = RecordingPort()
    provider = _provider()
    graph = build_development_graph(port, provider=provider)
    result = graph.invoke(
        _input("source_edit"),  # no risk_policy_snapshot in state
        {"configurable": {"thread_id": "no-caller-snapshot"}},
    )
    assert result["risk_decision"]["route"] != WorkflowRoute.BLOCKED.value
    assert result["workflow_identity"]["policy_digest"]
