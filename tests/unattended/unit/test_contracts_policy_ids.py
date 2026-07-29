from __future__ import annotations

from dataclasses import fields

import pytest

from reverse_agent.unattended import (
    TASK_QUEUE,
    AcceptanceResult,
    ExecutionHandle,
    FailureEnvelope,
    MinimalWorkItem,
    ResolvedExecutionPolicy,
    TaskSubmission,
    executor_id,
    resolve_execution_policy,
    workflow_id,
    workspace_id,
    workspace_path,
)

_BASE = "2aacf42dbab7f283454908da861b6ef44990f1d5"
_HEAD = "22c37c5050891cd10c868de8047dd948d0c89220"


def _work_item(**overrides: object) -> MinimalWorkItem:
    values: dict[str, object] = {
        "schema_version": 1,
        "work_item_id": "dddd2024/reverse-agent#79@approved",
        "source_issue": 79,
        "repository": "dddd2024/reverse-agent",
        "base_sha": _BASE,
        "goal": "Apply bounded Gate 2 owner-audit rework",
        "acceptance_criteria": ("all deterministic checks pass",),
        "allowed_paths": ("reverse_agent/unattended/**",),
        "forbidden_operations": (
            "merge",
            "direct_push_to_main",
            "force_push",
            "rebase",
            "squash",
            "tag",
            "release",
            "auto_merge",
            "secret_access",
        ),
        "required_checks": ("python -m pytest tests/unattended/unit -q",),
        "risk_tier": "R1",
        "max_attempts": 2,
    }
    values.update(overrides)
    return MinimalWorkItem(**values)  # type: ignore[arg-type]


def _handle(attempt: int = 1) -> ExecutionHandle:
    identifier = workflow_id("dddd2024", "reverse-agent", 79)
    return ExecutionHandle(
        workflow_id=identifier,
        attempt=attempt,
        workspace_id=workspace_id(identifier),
        executor_id=executor_id(identifier, attempt),
        started_at="2026-07-29T08:00:00+00:00",
    )


def test_exact_public_contract_field_matrix() -> None:
    assert tuple(field.name for field in fields(MinimalWorkItem)) == (
        "schema_version",
        "work_item_id",
        "source_issue",
        "repository",
        "base_sha",
        "goal",
        "acceptance_criteria",
        "allowed_paths",
        "forbidden_operations",
        "required_checks",
        "risk_tier",
        "max_attempts",
    )
    assert tuple(field.name for field in fields(ResolvedExecutionPolicy)) == (
        "unattended_allowed",
        "allowed_paths",
        "allowed_operations",
        "network_mode",
        "max_attempts",
        "draft_pr_allowed",
        "auto_merge_allowed",
        "approval_required",
        "blocking_reasons",
    )
    assert tuple(field.name for field in fields(ExecutionHandle)) == (
        "workflow_id",
        "attempt",
        "workspace_id",
        "executor_id",
        "started_at",
    )
    assert tuple(field.name for field in fields(TaskSubmission)) == (
        "verdict",
        "summary",
        "changed_paths",
        "commands_executed",
        "test_evidence",
        "limitations",
        "failure_reason",
    )
    assert tuple(field.name for field in fields(AcceptanceResult)) == (
        "status",
        "attempt",
        "policy_passed",
        "path_scope_passed",
        "required_checks_passed",
        "exact_head_sha",
        "pr_number",
        "rework_reasons",
    )
    assert tuple(field.name for field in fields(FailureEnvelope)) == (
        "failure_type",
        "retryable",
        "workflow_id",
        "activity",
        "attempt",
        "reason",
        "sanitized_evidence_ref",
    )


def test_r0_and_r1_bounded_scope_execute_unattended() -> None:
    r0 = resolve_execution_policy(_work_item(risk_tier="R0"))
    assert r0.unattended_allowed is True
    assert r0.allowed_operations == ("observe_repository", "run_required_checks")
    assert r0.network_mode == "none"
    assert r0.draft_pr_allowed is False

    r1 = resolve_execution_policy(_work_item(risk_tier="R1"))
    assert r1.unattended_allowed is True
    assert r1.allowed_operations == (
        "edit_allowed_paths",
        "run_required_checks",
        "push_bound_branch",
        "create_draft_pr",
    )
    assert r1.network_mode == "bounded"
    assert r1.draft_pr_allowed is True
    assert r1.auto_merge_allowed is False


def test_r2_and_r3_produce_approval_required_state_without_self_authorization() -> None:
    for tier in ("R2", "R3"):
        policy = resolve_execution_policy(_work_item(risk_tier=tier))
        assert policy.unattended_allowed is False
        assert policy.approval_required is True
        assert policy.allowed_operations == ()
        assert policy.network_mode == "none"
        assert policy.blocking_reasons == (f"{tier.lower()}_approval_required",)


@pytest.mark.parametrize(
    "path",
    ["", ".", "*", "**", "*/**", "/tmp/x", "C:\\tmp", "../x", "a/../b"],
)
def test_empty_broad_absolute_and_traversal_paths_fail_closed(path: str) -> None:
    with pytest.raises((ValueError, TypeError)):
        resolve_execution_policy(_work_item(allowed_paths=(path,)))


@pytest.mark.parametrize("attempts", [0, 3, True])
def test_attempt_limit_is_one_or_two(attempts: int) -> None:
    with pytest.raises(ValueError, match="attempt"):
        _work_item(max_attempts=attempts)


def test_forbidden_operations_are_preserved_restrictions_not_requests() -> None:
    policy = resolve_execution_policy(_work_item())
    assert policy.unattended_allowed is True
    dangerous = {
        "merge",
        "direct_push_to_main",
        "force_push",
        "rebase",
        "squash",
        "tag",
        "release",
        "auto_merge",
        "secret_access",
    }
    assert dangerous.isdisjoint(policy.allowed_operations)


def test_restriction_removes_an_otherwise_bounded_operation() -> None:
    policy = resolve_execution_policy(
        _work_item(forbidden_operations=("create-draft-pr",))
    )
    assert "create_draft_pr" not in policy.allowed_operations
    assert policy.draft_pr_allowed is False
    assert policy.network_mode == "bounded"


def test_paths_and_restrictions_are_deduplicated_deterministically() -> None:
    policy = resolve_execution_policy(
        _work_item(
            allowed_paths=("src/**", "src/**"),
            forbidden_operations=("create-draft-pr", "create draft pr"),
        )
    )
    assert policy.allowed_paths == ("src/**",)
    assert policy.allowed_operations == (
        "edit_allowed_paths",
        "run_required_checks",
        "push_bound_branch",
    )


def test_frozen_identifiers_match_gate2_contract() -> None:
    identifier = workflow_id("dddd2024", "reverse-agent", 79)
    assert identifier == "unattended:dddd2024/reverse-agent:issue:79"
    assert TASK_QUEUE == "reverse-agent-unattended-v0"
    assert workspace_id(identifier) == workspace_id(identifier)
    assert executor_id(identifier, 1) == executor_id(identifier, 1)
    assert executor_id(identifier, 1) != executor_id(identifier, 2)
    assert workspace_path(identifier, 2) == (
        f".var/unattended/{workspace_id(identifier)}/2"
    )


@pytest.mark.parametrize(
    ("owner", "repo", "issue"),
    [
        ("", "repo", 1),
        ("owner/x", "repo", 1),
        ("owner", "..", 1),
        ("owner", "repo", 0),
    ],
)
def test_invalid_workflow_identity_rejected(
    owner: str, repo: str, issue: int
) -> None:
    with pytest.raises(ValueError):
        workflow_id(owner, repo, issue)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"base_sha": "not-a-sha"}, "base_sha"),
        ({"goal": ""}, "goal"),
        ({"acceptance_criteria": ()}, "acceptance_criteria"),
        ({"required_checks": ()}, "required_checks"),
        ({"allowed_paths": []}, "allowed_paths_must_be_tuple"),
    ],
)
def test_work_item_validates_identity_and_immutable_values(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _work_item(**overrides)


def test_execution_handle_validates_deterministic_ids_and_timestamp() -> None:
    handle = _handle()
    with pytest.raises(ValueError, match="workspace_id_mismatch"):
        ExecutionHandle(
            handle.workflow_id,
            1,
            "wrong",
            handle.executor_id,
            handle.started_at,
        )
    with pytest.raises(ValueError, match="executor_id_mismatch"):
        ExecutionHandle(
            handle.workflow_id,
            1,
            handle.workspace_id,
            "wrong",
            handle.started_at,
        )
    with pytest.raises(ValueError, match="timezone"):
        ExecutionHandle(
            handle.workflow_id,
            1,
            handle.workspace_id,
            handle.executor_id,
            "2026-07-29T08:00:00",
        )


def test_executor_output_is_evidence_and_distinct_from_acceptance() -> None:
    submission = TaskSubmission(
        verdict="EVIDENCE_ONLY",
        summary="synthetic task completed",
        changed_paths=("synthetic.txt",),
        commands_executed=("python -m pytest -q",),
        test_evidence=("1 passed",),
        limitations=("independent acceptance not performed",),
        failure_reason=None,
    )
    result = AcceptanceResult(
        status="REWORK_REQUIRED",
        attempt=1,
        policy_passed=True,
        path_scope_passed=True,
        required_checks_passed=False,
        exact_head_sha=_HEAD,
        pr_number=78,
        rework_reasons=("required check failed",),
    )
    failure = FailureEnvelope(
        failure_type="ACTIVITY_FAILURE",
        retryable=False,
        workflow_id=_handle().workflow_id,
        activity="collect_result",
        attempt=1,
        reason="bounded failure",
        sanitized_evidence_ref="artifact://sanitized/1",
    )
    assert submission.verdict == "EVIDENCE_ONLY"
    assert result.status == "REWORK_REQUIRED"
    assert failure.retryable is False
    with pytest.raises(AttributeError):
        submission.summary = "mutated"  # type: ignore[misc]
