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
