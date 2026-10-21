"""A quota-held task moves to an equal-or-higher-tier model instead of waiting (#1313 D)."""
import json

import pytest

from test_agent_escalation import _launched, _link
from reverse_agent.platform_v1.run_store import TaskStoreError


def _hold(store, control, task_id, *, binding="codex-bind", tier=4):
    store._conn.execute("UPDATE tasks SET binding_ref=?, executor_kind='codex' WHERE id=?", (binding, task_id))
    store._conn.execute(
        "INSERT OR REPLACE INTO platform_quota_admissions (task_id,binding_ref,account_ref,evidence_json,need_json,"
        "small_task,safety_buffer,verdict_json) VALUES (?,?,?,?,?,?,?,?)",
        (task_id, binding, "acct", "{}", "{}", 0, 10,
         json.dumps({"decision": "quota_wait", "reason": "quota_capacity", "until": "2026-10-21T09:16:37Z"})))
    store._conn.commit()
    store.add_event(task_id, event_type="MODEL_SELECTED", title="Model selected", description=binding,
                    metadata={"binding_ref": binding, "tier": tier, "model_id": "gpt-6.1-sol", "reason": "cheapest"})


def _resolver(choice, calls):
    def resolve(plan_task, *, goal, failed_binding="", failed_tier=None, **kwargs):
        calls.append((plan_task.id, failed_binding, failed_tier))
        if isinstance(choice, Exception):
            raise choice
        return dict(choice)
    return resolve


ALTERNATIVE = {"binding_ref": "kimi-bind", "executor_kind": "opencode", "model_id": "kimi-k3", "tier": 4,
               "reason": "retry_different_model", "context_window": 256000}


def test_held_task_moves_to_an_equal_tier_model_once(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch)
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    calls = []
    goals.task_resolver = _resolver(ALTERNATIVE, calls)
    [moved] = goals.escalate_failed_tasks(goal.id)
    assert moved["reason"] == "quota_hold_reroute" and moved["to_binding"] == "kimi-bind"
    assert calls == [("T001", "codex-bind", 4)]  # the held model and its tier are the floor
    task = store.get_task(task_id)
    assert (task.binding_ref, task.executor_kind, task.status) == ("kimi-bind", "opencode", "QUEUED")
    assert control.quota_hold(task_id) is None  # stale admission for the old binding is gone
    latest = [e for e in store.get_events(task_id) if e.type == "MODEL_SELECTED"][-1]
    assert latest.metadata["binding_ref"] == "kimi-bind" and latest.metadata["reroute_reason"] == "quota_hold"
    assert control.list_task_escalations(goal.id) == ()  # not a retry: no budget spent
    # A second hold on the new model never flips the task back.
    _hold(store, control, task_id, binding="kimi-bind", tier=4)
    assert goals.escalate_failed_tasks(goal.id) == ()


@pytest.mark.parametrize("choice", [
    dict(ALTERNATIVE, binding_ref="codex-bind"),                                 # only the held model
    dict(ALTERNATIVE, tier=3),                                                    # a downgrade
    dict(ALTERNATIVE, tier=3, downgrade_fallback=True, reason="retry_lower_tier_fallback"),
    TaskStoreError("no_runnable_model"),
])
def test_held_task_keeps_waiting_without_an_equal_or_higher_alternative(monkeypatch, choice):
    store, control, goals, goal = _launched(monkeypatch)
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    goals.task_resolver = _resolver(choice, [])
    assert goals.escalate_failed_tasks(goal.id) == ()
    assert store.get_task(task_id).binding_ref == "codex-bind"
    assert control.quota_hold(task_id) is not None


def test_started_or_unheld_or_unselected_tasks_are_never_moved(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch)
    task_id = _link(control, goal.id, "T001")["task_id"]
    calls = []
    goals.task_resolver = _resolver(ALTERNATIVE, calls)
    assert goals.escalate_failed_tasks(goal.id) == () and calls == []  # no hold
    _hold(store, control, task_id)
    store._conn.execute("DELETE FROM task_events WHERE task_id=? AND type='MODEL_SELECTED'", (task_id,))
    store._conn.commit()
    assert goals.escalate_failed_tasks(goal.id) == () and calls == []  # no recorded tier: no floor
    _hold(store, control, task_id)
    store._conn.execute("INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_epoch, "
                        "lease_expiry_ms, created_at, updated_at) VALUES ('run-x', ?, 'e', 'w', 1, 1, 'x', 'x')",
                        (task_id,))
    store._conn.commit()
    assert goals.escalate_failed_tasks(goal.id) == ()
    assert store.get_task(task_id).binding_ref == "codex-bind"
