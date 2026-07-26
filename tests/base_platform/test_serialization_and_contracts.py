from __future__ import annotations

import json

import pytest

from reverse_agent.base_platform import (
    AcceptanceResult,
    AgentTask,
    BasePlatformError,
    ExecutionEnvelope,
    FailureEnvelope,
    GoalContract,
    NaturalLanguageRequest,
    ResolvedExecutionPolicy,
    RetryPolicy,
    SpecPackage,
    TaskSubmission,
    canonical_digest,
    canonical_json_bytes,
    resolve_policy,
)


def test_canonical_serialization_is_byte_stable_and_normalizes_semantic_sets() -> None:
    left = {"é": {"b", "a"}, "nested": {"z": 1, "a": 2}}
    right = {"nested": {"a": 2, "z": 1}, "e\u0301": {"a", "b"}}

    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert canonical_digest(left) == canonical_digest(right)
    assert canonical_json_bytes(left) == b'{"nested":{"a":2,"z":1},"\xc3\xa9":["a","b"]}'


def test_contract_collection_normalization_is_stable() -> None:
    first = NaturalLanguageRequest(
        identity="request:1",
        text="same",
        requested_operations=("unit_test", "source_edit", "unit_test"),
    )
    second = NaturalLanguageRequest(
        identity="request:1",
        text="same",
        requested_operations=("source_edit", "unit_test"),
    )

    assert first.requested_operations == ("source_edit", "unit_test")
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.digest() == second.digest()


def test_spec_round_trip_preserves_semantics(approved_spec: SpecPackage) -> None:
    encoded = approved_spec.canonical_bytes()
    decoded = SpecPackage.from_mapping(json.loads(encoded))

    assert decoded == approved_spec
    assert decoded.canonical_bytes() == encoded


def test_required_protocol_contracts_round_trip(
    approved_spec: SpecPackage,
    capabilities,
) -> None:
    policy = resolve_policy(approved_spec, capabilities)
    task = AgentTask(identity="task:1", operation="source_edit", parameters={"path": "example.py"})
    envelope = ExecutionEnvelope(identity="envelope:1", policy=policy, task_identity=task.identity)
    contracts = [
        approved_spec.request,
        approved_spec,
        approved_spec.goal,
        capabilities,
        policy,
        envelope,
        task,
        TaskSubmission(identity="submission:1", task=task, envelope=envelope),
        FailureEnvelope(
            identity="failure:1",
            error_code="LOCKED_FILE",
            message="File is temporarily locked.",
            retryable=True,
        ),
        AcceptanceResult(
            identity="acceptance:1",
            accepted=True,
            check_results={"pytest": True},
        ),
    ]

    for contract in contracts:
        encoded = contract.canonical_bytes()
        decoded = type(contract).from_mapping(json.loads(encoded))
        assert decoded == contract
        assert decoded.identity
        assert decoded.schema_version == "0.1"


def test_unsupported_schema_version_fails_closed() -> None:
    with pytest.raises(BasePlatformError) as captured:
        NaturalLanguageRequest(
            identity="request:bad",
            schema_version="99",
            text="unsupported",
        )

    assert captured.value.code == "UNSUPPORTED_SCHEMA_VERSION"
    assert captured.value.to_dict()["code"] == "UNSUPPORTED_SCHEMA_VERSION"


def test_contract_type_mismatch_fails_closed() -> None:
    payload = {
        "contract_type": "GoalContract",
        "schema_version": "0.1",
        "identity": "request:bad",
        "text": "wrong type",
        "requested_operations": [],
    }
    with pytest.raises(BasePlatformError) as captured:
        NaturalLanguageRequest.from_mapping(payload)

    assert captured.value.code == "CONTRACT_TYPE_MISMATCH"


def test_task_submission_requires_matching_identity(
    approved_spec: SpecPackage,
    capabilities,
) -> None:
    policy = resolve_policy(approved_spec, capabilities)
    task = AgentTask(identity="task:1", operation="source_edit", parameters={})
    envelope = ExecutionEnvelope(identity="envelope:1", policy=policy, task_identity="task:2")

    with pytest.raises(BasePlatformError) as captured:
        TaskSubmission(identity="submission:1", task=task, envelope=envelope)

    assert captured.value.code == "TASK_IDENTITY_MISMATCH"


def test_acceptance_result_rejects_inconsistent_acceptance() -> None:
    with pytest.raises(BasePlatformError) as captured:
        AcceptanceResult(
            identity="acceptance:bad",
            accepted=True,
            check_results={"pytest": False},
        )

    assert captured.value.code == "ACCEPTANCE_RESULT_INCONSISTENT"


def test_goal_preserves_semantic_acceptance_order_but_sorts_checks() -> None:
    goal = GoalContract(
        identity="goal:1",
        objective="Do the work.",
        acceptance_criteria=("first", "second"),
        required_checks=("z", "a", "z"),
    )

    assert goal.acceptance_criteria == ("first", "second")
    assert goal.required_checks == ("a", "z")


def test_retry_policy_rejects_zero_attempts() -> None:
    with pytest.raises(BasePlatformError) as captured:
        RetryPolicy(identity="retry:bad", max_attempts=0)

    assert captured.value.code == "INVALID_FIELD"
