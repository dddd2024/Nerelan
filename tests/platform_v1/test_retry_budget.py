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


def _seconds_ago(seconds):
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_a_patient_reroute_still_waits_for_the_backoff(case, monkeypatch):
    # #1619 review B1: a failure that repeats in seconds on every binding must not
    # bounce between bindings on each tick.
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _continuous(store, window)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    calls = []

    def resolve(plan_task, *, goal, **kwargs):
        calls.append(kwargs)
        return {"binding_ref": "other-binding", "executor_kind": "opencode", "model_id": "m", "tier": 3,
                "reason": "fixture", "context_window": 128000}
    service.task_resolver = resolve
    _fail_terminated(store, task, root, age=_seconds_ago(5))
    count = store.count_tasks()
    for _ in range(3):
        assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count and calls == []
    # Once the backoff is over it moves to the other binding.
    _fail_terminated(store, task, root, age=_seconds_ago(10_000))
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == f"{RETRY_REASON}:{gs.STALL_REROUTED}"
    assert store.get_task(step["to_task_id"]).binding_ref == "other-binding"


def test_a_patient_interrupted_preparation_waits_for_the_backoff(case, monkeypatch):
    # #1619 review B2: a preparation failure that repeats every time (full disk) is not retried each tick.
    root, _, store, _, service, goal, window, task = case
    _no_routing_retries(store, window)
    _continuous(store, window)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    store._conn.execute("UPDATE tasks SET status='BLOCKED', failure_classification='blocked', "
                        "failure_detail='worktree_preparation_failed:OSError: disk full', updated_at=? WHERE id=?",
                        (_seconds_ago(5), task.id))
    store._conn.commit()
    count = store.count_tasks()
    for _ in range(3):
        assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count


def caused(*triples):
    return [{"plan_task_id": step, "reason": reason, "cause": cause} for step, reason, cause in triples]


def test_a_legacy_failed_row_with_a_host_cause_is_a_host_retry():
    # Rows written before #1601/#1619 named a stall "failed:executor_stalled". Its honest
    # cause (#1677 neutral_failure) is the host, so a continuous window never spends on it.
    history = caused(("a", "failed:executor_stalled", "executor_stalled"),
                     ("a", "failed:executor_stalled", "executor_stalled"),
                     ("a", "failed:api_error_429", "quota_or_rate_limit"),
                     ("b", "failed:model_review_abandoned_no_reply", "model_review_abandoned_no_reply"))
    assert [gs._retry_kind(row) for row in history] == ["host"] * 4
    assert gs._routing_retries_spent(history, patient=True) == 0
    # Outside a continuous window they share the per-step free cap like any host retry.
    assert gs._routing_retries_spent(history) == 1
    assert gs._free_retries_used(history, "a") == 3


def test_a_legacy_failed_row_with_host_plumbing_shares_the_cap_even_when_patient():
    # A base the host prepared wrong repeats deterministically: it is not the model's
    # failure, but it must not retry forever in a continuous window either.
    history = caused(*[("a", "failed:deterministic_validation_failure", "functional_base_mismatch")] * 3)
    assert {gs._retry_kind(row) for row in history} == {"plumbing"}
    assert gs._routing_retries_spent(history, patient=True) == 1
    assert gs._free_retries_used(history, "a") == 3


def test_misroutes_fill_the_free_cap_without_erasing_other_plumbing_charges():
    misroute = "owner_window_binding_outside_confirmed_pool"
    misroutes = [("a", f"failed:{misroute}", misroute)] * 3
    other_plumbing = ("a", "failed:deterministic_validation_failure", "functional_base_mismatch")
    history = caused(*misroutes, other_plumbing)
    assert gs._routing_retries_spent(caused(*misroutes), patient=True) == 0
    assert gs._routing_retries_spent(history, patient=True) == 1
    assert gs._free_retries_used(history, "a") == 4


def test_a_failed_row_without_a_neutral_cause_still_judges_the_model():
    history = caused(("a", "failed:timeout", ""), ("a", "failed:deterministic_validation_failure", ""),
                     ("a", "failed:model_review_invalid_output", ""))
    assert {gs._retry_kind(row) for row in history} == {"model"}
    assert gs._routing_retries_spent(history, patient=True) == 3
    # A cause on a non-"failed:" reason is ignored; owner retries never spend.
    assert gs._retry_kind({"reason": "contract_fixup", "cause": "executor_stalled"}) == "model"
    assert gs._retry_kind({"reason": "owner_retry", "cause": ""}) == "owner"


def test_escalations_annotate_failed_rows_with_the_attempt_cause():
    from types import SimpleNamespace
    from reverse_agent.platform_v1.run_store import TaskStoreError

    attempts = {"t1": ("executor_stalled", ""), "t2": ("deterministic_validation_failure", "functional_base_mismatch"),
                "t3": ("deterministic_validation_failure", "functional_check_failed")}

    def get_task(task_id, *, event_limit=None):
        if task_id not in attempts:
            raise TaskStoreError(f"task_not_found:{task_id}")
        cls, detail = attempts[task_id]
        return SimpleNamespace(failure_classification=cls, failure_detail=detail)

    escalations = ({"plan_task_id": "a", "reason": "failed:executor_stalled", "from_task_id": "t1"},
                   {"plan_task_id": "a", "reason": "failed:deterministic_validation_failure", "from_task_id": "t2"},
                   {"plan_task_id": "a", "reason": "failed:deterministic_validation_failure", "from_task_id": "t3"},
                   {"plan_task_id": "a", "reason": "failed:timeout", "from_task_id": "gone"},
                   {"plan_task_id": "a", "reason": "host_retry:interrupted", "from_task_id": "t1"})
    fake = SimpleNamespace(store=SimpleNamespace(get_task=get_task),
                           control_store=SimpleNamespace(list_task_escalations=lambda goal_id: escalations))
    rows = gs.GoalService._escalations(fake, "goal")
    assert [row.get("cause") for row in rows] == ["executor_stalled", "functional_base_mismatch", "", "", None]
    assert escalations[0].get("cause") is None  # the store's rows are not mutated
    assert [gs._retry_kind(row) for row in rows] == ["host", "plumbing", "model", "model", "host"]


def test_a_patient_reroute_of_a_cut_off_tree_restores_on_the_new_binding(case, monkeypatch, tmp_path):
    # #1528 (2026-11-17, 2026-11-19): a terminated or redeploy-closed attempt that escalation
    # rerouted with its retained tree was refused at preparation (failed_snapshot_recovery_mismatch),
    # because restore only accepted a binding change after a stall.
    from test_contract_miss_fixup import destination, git
    import reverse_agent.platform_v1.contract_recovery as recovery
    root, base, store, _, service, goal, window, task = case
    wrong_tree(root)
    _continuous(store, window)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    service.task_resolver = lambda plan_task, *, goal, **kwargs: {
        "binding_ref": "other-binding", "executor_kind": "opencode", "model_id": "m", "tier": 3,
        "reason": "fixture", "context_window": 128000}
    _fail_terminated(store, task, root, age=_seconds_ago(10_000))
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == f"{RETRY_REASON}:{gs.STALL_REROUTED}"
    retry = store.get_task(step["to_task_id"])
    assert retry.binding_ref == "other-binding"
    assert recovery.recovery_input(retry)["rerouted"] is True
    dest = destination(case, tmp_path)
    recovery.restore_failed_tree(store, retry.id, worktree=dest)
    assert (dest / "wrong_name.py").exists()
    assert git(dest, "rev-parse", "HEAD") == base


def test_an_unflagged_binding_change_of_a_cut_off_tree_is_still_refused(case, monkeypatch, tmp_path):
    # Only escalation's explicit reroute may move a non-stall tree; a binding that changed
    # without that flag (e.g. a record written before it existed) keeps the refusal.
    from test_contract_miss_fixup import destination
    import reverse_agent.platform_v1.contract_recovery as recovery
    from reverse_agent.platform_v1.run_store import TaskStoreError
    root, _, store, _, service, goal, window, task = case
    wrong_tree(root)
    _continuous(store, window)
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    service.task_resolver = lambda plan_task, *, goal, **kwargs: {
        "binding_ref": "other-binding", "executor_kind": "opencode", "model_id": "m", "tier": 3,
        "reason": "fixture", "context_window": 128000}
    _fail_terminated(store, task, root, age=_seconds_ago(10_000))
    [step] = service.escalate_failed_tasks(goal.id)
    retry = store.get_task(step["to_task_id"])
    original = recovery.recovery_input
    monkeypatch.setattr(recovery, "recovery_input",
                        lambda t: {k: v for k, v in original(t).items() if k != "rerouted"})
    with pytest.raises(TaskStoreError, match="failed_snapshot_recovery_mismatch"):
        recovery.restore_failed_tree(store, retry.id, worktree=destination(case, tmp_path))
