from __future__ import annotations

import pytest

from reverse_agent.unattended import (
    TASK_QUEUE,
    AcceptanceResult,
    ExecutionHandle,
    FailureEnvelope,
    MinimalWorkItem,
    PolicyViolation,
    TaskSubmission,
    resolve_execution_policy,
    workflow_id,
    workspace_path,
)


def _work_item(**overrides: object) -> MinimalWorkItem:
    values: dict[str, object] = {
        "owner": "dddd2024",
        "repository": "reverse-agent",
        "issue_number": 76,
        "risk_tier": "R1",
        "allowed_paths": ("reverse_agent/unattended/**",),
    }
    values.update(overrides)
    return MinimalWorkItem(**values)  # type: ignore[arg-type]


def test_r0_and_r1_bounded_scope_execute_unattended() -> None:
    for tier in ("R0", "R1"):
        policy = resolve_execution_policy(_work_item(risk_tier=tier))
        assert policy.unattended_allowed is True
        assert policy.approval_required is False
        assert policy.auto_merge_allowed is False


def test_r2_and_r3_require_approval() -> None:
    for tier in ("R2", "R3"):
        with pytest.raises(PolicyViolation, match="approval_required"):
            resolve_execution_policy(_work_item(risk_tier=tier))
        assert resolve_execution_policy(
            _work_item(risk_tier=tier, approval_granted=True)
        ).approval_required


@pytest.mark.parametrize("path", ["", ".", "*", "**", "*/**", "/tmp/x", "C:\\tmp", "../x", "a/../b"])
def test_empty_broad_absolute_and_traversal_paths_fail_closed(path: str) -> None:
    with pytest.raises(PolicyViolation):
        resolve_execution_policy(_work_item(allowed_paths=(path,)))


def test_empty_scope_fails_closed() -> None:
    with pytest.raises(PolicyViolation, match="empty_allowed_paths"):
        resolve_execution_policy(_work_item(allowed_paths=()))


@pytest.mark.parametrize("attempts", [0, 3, True])
def test_attempt_limit_is_one_or_two(attempts: int) -> None:
    with pytest.raises(PolicyViolation, match="max_attempts_out_of_bounds"):
        resolve_execution_policy(_work_item(max_attempts=attempts))


def test_auto_merge_always_fails_closed() -> None:
    with pytest.raises(PolicyViolation, match="auto_merge_forbidden"):
        resolve_execution_policy(_work_item(auto_merge_allowed=True))


@pytest.mark.parametrize(
    "operation", ["merge", "auto_merge", "direct_push_to_main", "force_push", "rebase"]
)
def test_forbidden_operations_fail_closed(operation: str) -> None:
    with pytest.raises(PolicyViolation, match="forbidden_operation_requested"):
        resolve_execution_policy(_work_item(forbidden_operations=(operation,)))


def test_paths_and_operations_are_deduplicated_deterministically() -> None:
    policy = resolve_execution_policy(
        _work_item(
            allowed_paths=("src/**", "src/**"),
            forbidden_operations=("network", "network"),
        )
    )
    assert policy.allowed_paths == ("src/**",)
    assert policy.forbidden_operations == ("network",)


def test_frozen_identifiers_match_gate2_contract() -> None:
    identifier = workflow_id("dddd2024", "reverse-agent", 76)
    assert identifier == "unattended:dddd2024/reverse-agent:issue:76"
    assert TASK_QUEUE == "reverse-agent-unattended-v0"
    assert workspace_path(identifier, 2) == (
        ".var/unattended/unattended:dddd2024/reverse-agent:issue:76/2"
    )


@pytest.mark.parametrize(
    ("owner", "repo", "issue"),
    [("", "repo", 1), ("owner/x", "repo", 1), ("owner", "..", 1), ("owner", "repo", 0)],
)
def test_invalid_workflow_identity_rejected(owner: str, repo: str, issue: int) -> None:
    with pytest.raises(ValueError):
        workflow_id(owner, repo, issue)


def test_minimal_contracts_are_constructible_and_immutable() -> None:
    handle = ExecutionHandle("unattended:o/r:issue:1", 1)
    submission = TaskSubmission(handle, "synthetic task", ".var/unattended/x/1")
    result = AcceptanceResult(False, ("deterministic-check",), "agent output is evidence")
    failure = FailureEnvelope("FAILED", "bounded failure", False, {"attempt": 1})
    assert submission.handle == handle
    assert result.accepted is False
    assert failure.details == {"attempt": 1}
    with pytest.raises(AttributeError):
        handle.attempt = 2  # type: ignore[misc]
