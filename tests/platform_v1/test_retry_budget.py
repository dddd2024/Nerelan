"""Owner decision 2026-11-12 B: non-model failures retry without spending max_retries, capped per step."""
import pytest

from reverse_agent.platform_v1 import goal_service as gs
from test_contract_miss_fixup import case, wrong_tree  # noqa: F401 (fixture)
from test_executor_termination import RETRY_REASON, _fail_terminated
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)


def rows(*pairs):
    return [{"plan_task_id": step, "reason": reason} for step, reason in pairs]


@pytest.mark.parametrize("reason", ["transient_overload", "executor_terminated", "host_retry:executor_stalled",
                                    "host_retry:interrupted", "failed:quota_exhausted"])
def test_non_model_reasons(reason):
    assert gs._non_model_reason(reason)


@pytest.mark.parametrize("reason", ["failed:deterministic_validation_failure", "contract_fixup",
                                    "failed:MODEL_REFUSED", "owner_retry", "", None])
def test_model_reasons(reason):
    assert not gs._non_model_reason(reason)


def test_free_retries_share_one_cap_per_step():
    history = rows(("a", "transient_overload"), ("a", "failed:quota_exhausted"), ("b", "host_retry:interrupted"))
    assert gs._free_retries_used(history, "a") == 2
    assert gs._free_retries_used(history, "b") == 1
    assert gs._free_retries_used(history, "c") == 0


def test_only_model_retries_and_those_past_the_cap_spend_max_retries():
    assert gs._routing_retries_spent(rows(("a", "transient_overload"), ("a", "host_retry:interrupted"))) == 0
    # A third non-model retry on the same step is past the cap of 2 and spends one.
    assert gs._routing_retries_spent(rows(("a", "transient_overload"), ("a", "host_retry:interrupted"),
                                          ("a", "failed:quota_exhausted"))) == 1
    # The cap is per step.
    assert gs._routing_retries_spent(rows(("a", "transient_overload"), ("a", "transient_overload"),
                                          ("b", "transient_overload"))) == 0
    assert gs._routing_retries_spent(rows(("a", "failed:deterministic_validation_failure"),
                                          ("a", "contract_fixup"))) == 2
    # Decision A: Owner retries never spend max_retries and never use the free cap.
    assert gs._routing_retries_spent(rows(("a", "owner_retry"), ("a", "owner_retry"), ("a", "owner_retry"))) == 0
    assert gs._routing_retries_spent(rows(("a", "owner_retry"), ("a", "transient_overload"),
                                          ("a", "transient_overload"))) == 0


def _no_routing_retries(store, window):
    store._conn.execute("UPDATE platform_autonomous_windows SET max_retries=0 WHERE id=?", (window.id,))
    store._conn.commit()


def test_terminated_agent_retries_with_no_routing_retries_left(case, monkeypatch):
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _no_routing_retries(store, window)
    _fail_terminated(store, task, root)
    monkeypatch.setattr(gs, "TRANSIENT_BACKOFF_SECONDS", 0)
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == RETRY_REASON


def test_past_the_cap_a_host_failure_needs_a_routing_retry(case, monkeypatch):
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _no_routing_retries(store, window)
    _fail_terminated(store, task, root)
    monkeypatch.setattr(gs, "TRANSIENT_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count


# Continuous run (#1538, #1553): provider/liveness failures never end a goal.

def _continuous(store, window):
    store._conn.execute("UPDATE platform_autonomous_windows SET confirmation_mode='OWNER_WINDOW', expires_at='' "
                        "WHERE id=?", (window.id,))
    store._conn.commit()


def test_in_a_continuous_window_no_non_model_retry_spends_max_retries():
    history = rows(*[("a", "transient_overload")] * 5, ("a", "failed:api_error_429"), ("a", "host_retry:executor_stalled"))
    assert gs._routing_retries_spent(history) == 5
    assert gs._routing_retries_spent(history, patient=True) == 0
    # Model-judging retries still spend it.
    assert gs._routing_retries_spent(rows(("a", "failed:deterministic_validation_failure"), ("a", "failed:timeout")),
                                     patient=True) == 2


def test_past_the_cap_a_continuous_window_keeps_retrying_a_host_failure(case, monkeypatch):
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _no_routing_retries(store, window)
    _continuous(store, window)
    _fail_terminated(store, task, root)
    monkeypatch.setattr(gs, "TRANSIENT_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    [step] = service.escalate_failed_tasks(goal.id)
    # No router in this fixture: no alternative, so the same binding resumes after the backoff.
    assert step["reason"] == f"{RETRY_REASON}:{gs.STALL_NO_ALTERNATIVE}"
    assert store.get_task(step["to_task_id"]).binding_ref == task.binding_ref


def test_a_patient_retry_waits_for_its_doubling_backoff(case, monkeypatch):
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _continuous(store, window)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    from datetime import datetime, timedelta, timezone
    recent = (datetime.now(timezone.utc) - timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _fail_terminated(store, task, root, age=recent)  # 60 s ago; the first backoff is 120 s
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count


def test_the_patient_backoff_doubles_to_a_ceiling(case, monkeypatch):
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _continuous(store, window)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    monkeypatch.setattr(gs, "PATIENT_BACKOFF_MAX_SECONDS", 30)
    from datetime import datetime, timedelta, timezone
    recent = (datetime.now(timezone.utc) - timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _fail_terminated(store, task, root, age=recent)  # past the 30 s ceiling, though under 120 s
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"].startswith(RETRY_REASON)


def test_patient_quota_failure_retries_without_budget(case, monkeypatch):
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _no_routing_retries(store, window)
    _continuous(store, window)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    monkeypatch.setattr(gs, "TRANSIENT_BACKOFF_SECONDS", 0)
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='api_error_429', "
                        "failure_detail='opencode_nonzero:exit=1:api_error_429', updated_at='2000-01-01T00:00:00Z' "
                        "WHERE id=?", (task.id,))
    store._conn.commit()
    service.task_resolver = lambda plan_task, *, goal, failed_binding="", **kw: {
        "binding_ref": "other-account", "executor_kind": "opencode", "model_id": "zai/glm-5.3", "tier": 3,
        "reason": "fixture", "context_window": 128000}
    [step] = service.escalate_failed_tasks(goal.id)
    assert store.get_task(step["to_task_id"]).binding_ref == "other-account"


def test_outside_a_continuous_window_a_quota_failure_past_the_cap_stops(case, monkeypatch):
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _no_routing_retries(store, window)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='api_error_429', "
                        "failure_detail='x', updated_at='2000-01-01T00:00:00Z' WHERE id=?", (task.id,))
    store._conn.commit()
    service.task_resolver = lambda plan_task, *, goal, **kw: {"binding_ref": "other-account", "executor_kind": "opencode",
                                                              "model_id": "m", "tier": 3, "reason": "f", "context_window": 1}
    assert service.escalate_failed_tasks(goal.id) == ()
