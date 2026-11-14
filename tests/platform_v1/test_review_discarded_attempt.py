"""A failed attempt that called no model and was discarded authored nothing (#1504).

On 2026-11-14 an implement attempt exited before its first model request
(``executor_nonzero`` after one second). The host recorded its tree as
discarded and the next attempt started over; that attempt produced the diff.
Every later review of the step was refused as ``review_not_independent``,
because review authorship demanded model observations for the empty attempt.
"""
from __future__ import annotations

import pytest

from test_goal_functional_checks import goal_checks  # noqa: F401 - fixture
from test_model_review_execution import review_setup, run_review  # noqa: F401 - fixture
from reverse_agent.platform_v1.control_store import PlatformControlStore


def _earlier_attempt(store, producer, *, disposition, usage_model=None, status="FAILED"):
    control = PlatformControlStore(store)
    goal_id = control.goal_id_for_task(producer)
    goal = control.get_goal(goal_id)
    attempt = store.create_task(title="earlier implement attempt", executor_kind="opencode",
                                binding_ref="fixture-earlier", idempotency_key="earlier-" + producer)
    execution_id = "exec-" + attempt.id
    store._conn.execute("UPDATE tasks SET status = ?, execution_id = ?, failure_classification = "
                        "'executor_nonzero' WHERE id = ?", (status, execution_id, attempt.id))
    if disposition is not None:
        store._bind_artifact_evidence(attempt.id, category="AttemptDisposition", label=execution_id,
            document={"task_id": attempt.id, "execution_id": execution_id, "disposition": disposition,
                      "snapshot_digest": "", "tokens": None})
    if usage_model:
        store.append_usage_observation(attempt.id, observation_id="earlier-" + attempt.id,
            execution_id=execution_id, role="executor", model_id=usage_model, provider_id="local",
            source_kind="assistant_message", source_id="earlier-turn", status="UNKNOWN")
    store._conn.execute(
        "INSERT INTO platform_task_escalations (goal_id, goal_revision, plan_task_id, step, from_task_id, "
        "to_task_id, from_role, to_role, reason, created_at) VALUES (?, ?, 'A', 1, ?, ?, 'coder', 'coder', "
        "'failed:executor_nonzero', '2026-11-14T14:32:57Z')", (goal_id, goal.revision, attempt.id, producer))
    return attempt.id


def test_discarded_attempt_without_model_call_does_not_block_review(review_setup):
    store, _, producer, *_ = review_setup
    _earlier_attempt(store, producer, disposition="discarded")
    result = run_review(review_setup)
    assert result.success, result


@pytest.mark.parametrize("disposition", ["reused", None])
def test_attempt_whose_tree_may_have_been_reused_still_needs_its_model(review_setup, disposition):
    store, _, producer, *_ = review_setup
    _earlier_attempt(store, producer, disposition=disposition)
    result = run_review(review_setup)
    assert result.failure_classification == "review_not_independent"


def test_discarded_attempt_that_did_call_a_model_still_counts_as_author(review_setup):
    # The reviewer fixture answers as local/test; an earlier attempt by that model keeps it out.
    store, _, producer, *_ = review_setup
    _earlier_attempt(store, producer, disposition="discarded", usage_model="local/test")
    result = run_review(review_setup)
    assert result.failure_classification == "review_not_independent"
