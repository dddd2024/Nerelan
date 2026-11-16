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


def test_another_binding_of_the_held_model_is_not_a_move(monkeypatch):
    store, control, goals, goal = _launched(monkeypatch)
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    same = dict(ALTERNATIVE, binding_ref="codex-via-magpie", model_id="codex/gpt-6.1-sol", tier=4)
    goals.task_resolver = _resolver(same, [])
    assert goals.escalate_failed_tasks(goal.id) == ()
    # Not marked as rerouted: a genuinely different model can still be chosen later.
    goals.task_resolver = _resolver(ALTERNATIVE, [])
    [moved] = goals.escalate_failed_tasks(goal.id)
    assert moved["to_binding"] == "kimi-bind"


def test_native_target_needs_an_exact_launch_base(monkeypatch):
    native = dict(ALTERNATIVE, binding_ref="claude-bind", executor_kind="claude_code", model_id="claude-opus", tier=5)
    store, control, goals, goal = _launched(monkeypatch)  # no checks: launch froze no base
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    goals.task_resolver = _resolver(native, [])
    assert goals.escalate_failed_tasks(goal.id) == ()
    assert store.get_task(task_id).binding_ref == "codex-bind"
    checks = [{"profile_id": "python_pytest", "working_directory": ".", "targets": ["tests/test_x.py"]}]
    store, control, goals, goal = _launched(monkeypatch, checks=checks)
    task_id = _link(control, goal.id, "T001")["task_id"]
    _hold(store, control, task_id)
    goals.task_resolver = _resolver(native, [])
    [moved] = goals.escalate_failed_tasks(goal.id)
    task = store.get_task(task_id)
    assert moved["to_binding"] == "claude-bind" and task.executor_kind == "claude_code" and len(task.branch) == 40


def test_coordinator_offers_fully_held_goals_to_the_rerouter(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
    store, control, goals, goal = _launched(monkeypatch)
    rerouted = []
    def held(task):
        raise TaskStoreError("QUOTA_WAIT:2026-10-21T09:16:37Z")
    coordinator = UnattendedCoordinator(store=store, control_store=control,
        autonomy=SimpleNamespace(authorize=lambda **kwargs: True), router=SimpleNamespace(),
        workspace_root=tmp_path, quota_preparer=held, quota_rerouter=rerouted.append)
    assert coordinator.tick() == 0
    assert rerouted == [goal.id]


# --- #1596: liveness cool-down on a stalled binding, derived from its attempt rows -------

from datetime import datetime, timezone  # noqa: E402

from reverse_agent.platform_v1 import quota_guard  # noqa: E402

NOW = 1_800_000_000.0
MIN = 60


def _stall(at):
    return {"status": "FAILED", "failure_classification": "executor_stalled", "at": at}


def _ok(at):
    return {"status": "READY_FOR_REVIEW", "failure_classification": "", "at": at}


def test_one_stall_cools_the_binding_down_for_the_base_time_then_expires():
    hold = quota_guard.liveness_cooldown([_stall(NOW - 5 * MIN)], now=NOW)
    assert hold["reason"] == "liveness_cooldown" and hold["stalls"] == 1
    assert hold["seconds"] == quota_guard.LIVENESS_COOLDOWN_SECONDS == 15 * MIN
    assert hold["until"] == NOW + 10 * MIN
    assert quota_guard.liveness_cooldown([_stall(NOW - 5 * MIN)], now=NOW + 10 * MIN) is None  # expired


def test_repeated_stalls_lengthen_the_cooldown_up_to_the_cap():
    seconds = [quota_guard.liveness_cooldown([_stall(NOW - i) for i in range(n)], now=NOW)["seconds"]
               for n in range(1, 7)]
    assert seconds == [15 * MIN, 30 * MIN, 60 * MIN, 120 * MIN, 120 * MIN, 120 * MIN]
    assert quota_guard.LIVENESS_COOLDOWN_MAX_SECONDS == 120 * MIN


def test_a_success_clears_earlier_stalls_and_other_failures_do_not_count():
    assert quota_guard.liveness_cooldown([_ok(NOW - MIN), _stall(NOW - 2 * MIN)], now=NOW) is None
    # A stall after the success counts alone; the stalls before it are cleared.
    hold = quota_guard.liveness_cooldown([_stall(NOW - MIN), _ok(NOW - 2 * MIN), _stall(NOW - 3 * MIN)], now=NOW)
    assert hold["stalls"] == 1
    other = {"status": "FAILED", "failure_classification": "deterministic_validation_failure", "at": NOW - MIN}
    assert quota_guard.liveness_cooldown([other], now=NOW) is None
    assert quota_guard.liveness_cooldown([other, _stall(NOW - 2 * MIN)], now=NOW)["stalls"] == 1
    # Stalls older than the look-back are history, not a reason to grow the cool-down.
    old = NOW - quota_guard.LIVENESS_LOOKBACK_SECONDS - 1
    assert quota_guard.liveness_cooldown([_stall(NOW - MIN), _stall(old)], now=NOW)["stalls"] == 1


def _iso(at):
    return datetime.fromtimestamp(at, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_host_hold_comes_from_task_rows_and_routes_other_goals_away(monkeypatch, tmp_path):
    """No second ledger: the hold is read from the binding's attempts, like a limit-hit hold."""
    from test_model_router import fixture_host
    from reverse_agent.platform_v1 import trusted_host
    from reverse_agent.platform_v1.goal_service import PlannedTask
    from reverse_agent.platform_v1.run_store import TaskStore
    host = fixture_host(monkeypatch, tmp_path)
    monkeypatch.delattr(host, "_quota_check")  # the real check, with the real hold
    monkeypatch.setattr(host, "_limit_hit_until", lambda connection, binding=None: None)
    host._task_store = TaskStore(":memory:")
    clock = {"now": NOW}
    monkeypatch.setattr(trusted_host.time, "time", lambda: clock["now"])

    def attempt(binding, status, classification, at):
        task = host._task_store.create_task(title="attempt", binding_ref=binding, executor_kind="opencode")
        host._task_store._conn.execute(
            "UPDATE tasks SET status=?, failure_classification=?, updated_at=? WHERE id=?",
            (status, classification, _iso(at), task.id))
        host._task_store._conn.commit()

    task = PlannedTask("T009", "another goal", "i", difficulty=2)
    assert host._resolve_task_model(task)["binding_ref"] == "cheap"
    attempt("cheap", "FAILED", "executor_stalled", NOW - MIN)
    verdict = host._quota_check(host._store.get_binding_public("cheap"))
    assert verdict["decision"] == "switch" and verdict["reason"] == "liveness_cooldown"
    assert verdict["until"] == _iso(NOW - MIN + 15 * MIN) and verdict["stalls"] == 1
    # Another goal now avoids the cooling binding and the decision records why.
    result = host._resolve_task_model(task)
    assert result["binding_ref"] != "cheap"
    assert any(row["binding_id"] == "cheap" and row["filter"] == "liveness_cooldown"
               for row in result["excluded_candidates"])
    # It expires on the fake clock ...
    clock["now"] = NOW + 15 * MIN
    assert host._quota_check(host._store.get_binding_public("cheap")) is None
    assert host._resolve_task_model(task)["binding_ref"] == "cheap"
    # ... and a successful attempt on the binding clears a fresh one at once.
    attempt("cheap", "FAILED", "executor_stalled", NOW + 15 * MIN)
    assert host._quota_check(host._store.get_binding_public("cheap"))["reason"] == "liveness_cooldown"
    attempt("cheap", "READY_FOR_REVIEW", "", NOW + 15 * MIN + 1)
    clock["now"] = NOW + 15 * MIN + 2
    assert host._quota_check(host._store.get_binding_public("cheap")) is None
