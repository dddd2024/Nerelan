"""GoalService holds automatic review replacement over unresolved reviewer calls (#1191).

If parking BLOCKED fails after a reviewer call may have completed, generic
dispatch cleanup can leave FAILED over a PENDING intent. The real GoalService
must then schedule nothing and record one typed hold. Fake providers and
disposable Git/SQLite only; no real reboot or billing behaviour is proven.
"""
import sqlite3
import time

import pytest

from test_goal_functional_checks import goal_checks
from test_model_review_execution import review_setup
from test_model_review_toolless import toolless
from test_model_review_rpc_journal import harness, journal, escalate, fail_entry_binding
from test_model_review_feedback import rejected
from reverse_agent.platform_v1 import artifact_handoff, goal_service, model_review, model_review_transport as transport
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStoreError

HOLD = "model_review_intent_unresolved"


def unsave_reply(h, monkeypatch):
    """The reviewer replies, then saving the reply fails: its outcome stays unknown.

    A call that ended with no reply settles instead (#1618), so the unresolved
    intent these tests need comes from a reply the host could not save.
    """
    store = h["store"]
    original = store._bind_artifact_evidence
    def fail(*args, **kwargs):
        if kwargs.get("category") == model_review.CATEGORY:
            raise TaskStoreError("synthetic_evidence_write_failed")
        return original(*args, **kwargs)
    monkeypatch.setattr(store, "_bind_artifact_evidence", fail)


def fail_blocked_writers(store, monkeypatch, attempts, *, all_writers=False):
    """Make the BLOCKED writers fail; return a restore for the transient fault."""
    names = (("_fenced_classify_failure", "classify_failure", "block_model_selection")
             if all_writers else ("_fenced_classify_failure",))
    originals = {name: getattr(store, name) for name in names}
    def wrap(name):
        original = originals[name]
        def fail(*args, **kwargs):
            if name == "block_model_selection" or kwargs.get("classification") == "blocked":
                attempts.append(name)
                raise TaskStoreError("synthetic_blocked_state_write_failed")
            return original(*args, **kwargs)
        monkeypatch.setattr(store, name, fail)
    for name in names:
        wrap(name)
    def restore():
        for name, original in originals.items():
            monkeypatch.setattr(store, name, original)
    return restore


def failed_over_pending(h, monkeypatch, *, all_writers=False):
    """Reproduce FAILED/executor_dispatch_failed over a PENDING reviewer intent.

    Inverts the independent bad-behaviour repro: the setup is identical, the
    scheduler outcome is asserted by the callers.
    """
    store = h["store"]
    unsave_reply(h, monkeypatch)
    attempts = []
    restore = fail_blocked_writers(store, monkeypatch, attempts, all_writers=all_writers)
    with pytest.raises(TaskStoreError, match="synthetic_blocked_state_write_failed"):
        h["run"]()
    assert "_fenced_classify_failure" in attempts and h["calls"]() == 1
    task = store.get_task(h["consumer"])
    # Cleanup's FAILED stays visible; BLOCKED was never written.
    assert task.status == "FAILED" and task.failure_classification == "executor_dispatch_failed"
    rows = journal(store, h["consumer"])
    assert [row["state"] for row in rows] == ["PENDING"]
    return rows, restore


def holds(store, task_id):
    return [event for event in store.get_events(task_id)
            if event.type == "MODEL_SELECTION_FAILED" and event.metadata.get("reason") == HOLD]


def assert_held(h, rows, ticks=3):
    store = h["store"]
    count = store.count_tasks()
    for _ in range(ticks):
        replacements, before, after = escalate(h)
        assert replacements == () and after == before
    assert store.count_tasks() == count and h["calls"]() == 1
    assert journal(store, h["consumer"]) == rows
    held = holds(store, h["consumer"])
    assert len(held) == 1  # repeated ticks never flood history
    assert held[0].metadata["hold"] == f"intent_pending:{rows[0]['operation_id']}"
    assert "may have been dispatched" in held[0].description and "reconcile manually" in held[0].description
    task = store.get_task(h["consumer"])
    assert task.status == "FAILED" and "FAILED/executor_dispatch_failed" in held[0].description


def test_blocked_state_write_failure_holds_replacement(harness, monkeypatch):
    rows, restore = failed_over_pending(harness, monkeypatch)
    restore()  # the transient fault clears before the scheduler ticks
    assert_held(harness, rows)


def test_both_blocked_writers_fail_while_failed_cleanup_writable(harness, monkeypatch):
    rows, _ = failed_over_pending(harness, monkeypatch, all_writers=True)
    # The BLOCKED writers stay broken while GoalService ticks: the hold needs none of them.
    assert_held(harness, rows)


def test_hold_reason_write_failure_creates_no_task(harness, monkeypatch):
    rows, restore = failed_over_pending(harness, monkeypatch)
    restore()
    store = harness["store"]
    original = store.add_event
    def fail(task_id, **kwargs):
        if kwargs.get("event_type") == "MODEL_SELECTION_FAILED":
            raise TaskStoreError("synthetic_event_write_failed")
        return original(task_id, **kwargs)
    monkeypatch.setattr(store, "add_event", fail)
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="model_review_retry_hold_unrecorded"):
        escalate(harness)
    assert store.count_tasks() == count and harness["calls"]() == 1 and not holds(store, harness["consumer"])
    monkeypatch.setattr(store, "add_event", original)
    assert_held(harness, rows)


def test_unreadable_journal_in_scheduler_denies_replacement(harness, monkeypatch):
    # A known invalid reply settles its receipt, so the review is otherwise retryable.
    if harness["kind"] == "toolless":
        harness["state"]["payload"]["choices"][0]["message"]["content"] = "not json"
    else:
        harness["options"]["response"] = "not json"
    assert harness["run"]().failure_classification == "model_review_invalid_output"
    store = harness["store"]
    assert [row["state"] for row in journal(store, harness["consumer"])] == ["RECONCILED"]
    def unreadable(store, key):
        raise sqlite3.OperationalError("database is locked")
    original = model_review._journal_rows
    monkeypatch.setattr(model_review, "_journal_rows", unreadable)
    for _ in range(2):
        replacements, before, after = escalate(harness)
        assert replacements == () and after == before
    held = holds(store, harness["consumer"])
    assert [event.metadata["hold"] for event in held] == ["intent_unverifiable:OperationalError"]
    assert store.get_task(harness["consumer"]).status == "FAILED" and harness["calls"]() == 1
    monkeypatch.setattr(model_review, "_journal_rows", original)
    replacements, before, after = escalate(harness)
    assert len(replacements) == 1 and after != before  # once readable and settled, retry resumes


def test_no_intent_dispatch_failure_still_retries(harness, monkeypatch):
    original = fail_entry_binding(harness, monkeypatch, RuntimeError("synthetic recovery entry fault"))
    with pytest.raises(RuntimeError, match="synthetic recovery entry fault"):
        harness["run"]()
    monkeypatch.setattr(artifact_handoff, "bind_consumer_input", original)
    task = harness["store"].get_task(harness["consumer"])
    assert task.status == "FAILED" and task.failure_classification == "executor_dispatch_failed"
    assert journal(harness["store"], harness["consumer"]) == [] and harness["calls"]() == 0
    replacements, before, after = escalate(harness)
    assert len(replacements) == 1 and after != before
    assert not holds(harness["store"], harness["consumer"])


def test_known_reject_with_success_journal_still_repairs(review_setup):
    store, control, service, goal_id = rejected(review_setup)
    consumer = review_setup[3]
    assert [row["state"] for row in journal(store, consumer)] == ["SUCCESS"]
    outcome, = service.escalate_failed_tasks(goal_id)
    assert outcome["plan_task_id"] == "A" and outcome["to_task_id"]
    assert not holds(store, consumer)


def test_non_review_task_ignores_review_journal(review_setup, monkeypatch):
    store, _, producer, consumer, _, _, _ = review_setup
    control = PlatformControlStore(store)
    goal = control.get_goal(control.goal_id_for_task(producer))
    service = GoalService(store=store, control_store=control)
    planned = {raw["id"]: service._normalize_task(raw, seq=seq) for seq, raw in enumerate(goal.tasks)}
    def unreadable(store, key):
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(model_review, "_journal_rows", unreadable)
    events = len(store.get_events(producer))
    assert service._review_intent_hold(store.get_task(producer), planned["A"]) is False
    assert len(store.get_events(producer)) == events
    # The same unreadable journal does hold the review task.
    assert service._review_intent_hold(store.get_task(consumer), planned["B"]) is True


# Legacy parks (#1618): before the fix a call with no reply parked BLOCKED forever.
GRACE = transport.TIMEOUT_SECONDS + goal_service.NO_REPLY_GRACE_SECONDS


def legacy_park(h, monkeypatch, *, age, cause="timeout"):
    """A pre-#1618 park: BLOCKED model_review_completion_unknown:<cause> over its PENDING intent."""
    store = h["store"]
    original = store._bind_artifact_evidence
    unsave_reply(h, monkeypatch)
    h["run"]()
    monkeypatch.setattr(store, "_bind_artifact_evidence", original)
    row, = journal(store, h["consumer"])
    assert row["state"] == "PENDING"
    store._conn.execute("UPDATE tasks SET failure_detail = ? WHERE id = ?", (
        f"model_review_completion_unknown:{cause}: reviewer call {row['operation_id']} may have completed "
        "remotely; journal stays PENDING, not replayed, reconcile manually", h["consumer"]))
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - age))
    store._conn.execute("UPDATE durable_external_operations SET created_at = ? WHERE operation_id = ?",
                        (started, row["operation_id"]))
    # The parked invocation's lease has long expired.
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?",
                        (int((time.time() - age) * 1000), h["consumer"]))
    task = store.get_task(h["consumer"])
    assert task.status == "BLOCKED" and not [r for r in task.evidence_refs if r["category"] == model_review.CATEGORY]
    return row


def recoveries(store, task_id):
    return [event for event in store.get_events(task_id) if event.type == "MODEL_SELECTION_FAILED"
            and event.metadata.get("reason") == model_review.ABANDONED_NO_REPLY]


def test_legacy_no_reply_park_past_grace_is_settled_and_retried_once(harness, monkeypatch):
    row = legacy_park(harness, monkeypatch, age=GRACE + 60)
    store = harness["store"]
    replacements, before, after = escalate(harness)
    assert len(replacements) == 1 and after != before
    assert replacements[0]["reason"] == f"host_retry:{model_review.ABANDONED_NO_REPLY}"
    settled, = journal(store, harness["consumer"])
    assert (settled["operation_id"], settled["state"], settled["result_state"]) == (
        row["operation_id"], "RECONCILED", "failure")
    event, = recoveries(store, harness["consumer"])
    assert event.metadata["operation_id"] == row["operation_id"] and event.metadata["cause"] == "timeout"
    count = store.count_tasks()
    for _ in range(2):  # later ticks neither retry again nor record a second event
        assert escalate(harness)[0] == ()
    assert store.count_tasks() == count and len(recoveries(store, harness["consumer"])) == 1
    assert harness["calls"]() == 1 and not holds(store, harness["consumer"])


def test_legacy_no_reply_park_inside_grace_stays_held(harness, monkeypatch):
    row = legacy_park(harness, monkeypatch, age=transport.TIMEOUT_SECONDS)
    store = harness["store"]
    count = store.count_tasks()
    replacements, before, after = escalate(harness)
    assert replacements == () and after == before and store.count_tasks() == count
    current, = journal(store, harness["consumer"])
    assert (current["operation_id"], current["state"]) == (row["operation_id"], "PENDING")
    assert not recoveries(store, harness["consumer"])


@pytest.mark.parametrize("cause", ["response_unsaved", "receipt_conflict", "intent_scope_conflict",
                                   "intent_pending", "OperationalError"])
def test_legacy_parks_with_a_reply_or_unknown_scope_stay_held(harness, monkeypatch, cause):
    legacy_park(harness, monkeypatch, age=GRACE + 60, cause=cause)
    store = harness["store"]
    assert escalate(harness)[0] == ()
    assert [r["state"] for r in journal(store, harness["consumer"])] == ["PENDING"]
    assert not recoveries(store, harness["consumer"])


def test_legacy_no_reply_park_with_live_lease_stays_held(harness, monkeypatch):
    legacy_park(harness, monkeypatch, age=GRACE + 60)
    store = harness["store"]
    store._conn.execute("UPDATE durable_runs SET lease_owner = 'still-running', lease_expiry_ms = ? WHERE task_id = ?",
                        (int(time.time() * 1000) + 600000, harness["consumer"]))
    assert escalate(harness)[0] == ()
    assert [r["state"] for r in journal(store, harness["consumer"])] == ["PENDING"]
    assert not recoveries(store, harness["consumer"])
