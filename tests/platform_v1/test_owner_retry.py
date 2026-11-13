"""Owner decision 2026-11-12 A: the Owner retries a stopped step inside the Goal's active window."""
import pytest

from reverse_agent.platform_v1 import goal_service as gs
from reverse_agent.platform_v1.run_store import TaskStoreError
from test_contract_miss_fixup import case  # noqa: F401 (fixture)
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)
from test_task_service import task_server  # noqa: F401 (fixture)


def _fail(store, task, classification="deterministic_validation_failure"):
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification=? WHERE id=?",
                        (classification, task.id))
    store._conn.commit()


def _retry(service, goal, **kwargs):
    goal = service.control_store.get_goal(goal.id)
    return service.owner_retry(goal.id, "T001", expected_revision=goal.revision, **kwargs)


def test_owner_retry_starts_a_new_attempt_without_spending_max_retries(case):
    _, _, store, control, service, goal, window, task = case
    store._conn.execute("UPDATE platform_autonomous_windows SET max_retries=0 WHERE id=?", (window.id,))
    _fail(store, task)
    result = _retry(service, goal)
    assert result["reason"] == gs.OWNER_RETRY_REASON and result["from_task_id"] == task.id
    retry = store.get_task(result["to_task_id"])
    assert (retry.executor_kind, retry.binding_ref) == ("opencode", "local-test-binding")
    assert retry.policy_ref == window.policy_id and retry.status not in {"FAILED", "BLOCKED"}
    [row] = control.list_task_escalations(goal.id)
    assert row["reason"] == gs.OWNER_RETRY_REASON
    assert gs._routing_retries_spent(control.list_task_escalations(goal.id)) == 0
    # A second click while the new attempt is pending is refused, not a second task.
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="owner_retry_step_not_stopped"):
        _retry(service, goal)
    assert store.count_tasks() == count


def test_a_running_step_cannot_be_retried(case):
    *_, service, goal, _, _ = case
    with pytest.raises(TaskStoreError, match="owner_retry_step_not_stopped"):
        _retry(service, goal)


@pytest.mark.parametrize("change", ["status='STOPPED'", "expires_at='2000-01-01T00:00:00Z'"])
def test_no_active_window_no_retry(case, change):
    _, _, store, _, service, goal, window, task = case
    _fail(store, task)
    store._conn.execute(f"UPDATE platform_autonomous_windows SET {change} WHERE id=?", (window.id,))
    store._conn.commit()
    with pytest.raises(TaskStoreError, match="owner_retry_no_active_window"):
        _retry(service, goal)


def test_stale_revision_is_refused(case):
    _, _, store, _, service, goal, _, task = case
    _fail(store, task)
    with pytest.raises(TaskStoreError, match="goal_revision_conflict"):
        service.owner_retry(goal.id, "T001", expected_revision=goal.revision + 5)


def test_unknown_step_is_refused(case):
    _, _, store, _, service, goal, _, task = case
    _fail(store, task)
    with pytest.raises(TaskStoreError, match="owner_retry_step_not_found"):
        service.owner_retry(goal.id, "T999", expected_revision=service.control_store.get_goal(goal.id).revision)


def test_a_model_pick_needs_an_owner_confirmed_pool(case):
    _, _, store, _, service, goal, _, task = case
    _fail(store, task)
    with pytest.raises(TaskStoreError, match="owner_retry_model_choice_unavailable"):
        _retry(service, goal, binding_ref="local-test-binding")


def _routed(service, monkeypatch, pool, pick):
    calls = []

    def resolver(plan_task, *, goal, failed_binding="", **kwargs):
        calls.append(goal.binding_ref)
        # The fixture Goal is itself pinned to local-test-binding; only an Owner pick overrides the router here.
        chosen = pick if goal.binding_ref in {"", "local-test-binding"} else goal.binding_ref
        return {"binding_ref": chosen, "executor_kind": "opencode", "reason": "fixture"}
    service.task_resolver = resolver
    monkeypatch.setattr(service, "_owner_window_pool",
                        lambda goal, window_id: tuple({"binding_ref": ref, "model_id": f"m-{ref}"} for ref in pool))
    return calls


def test_owner_pick_inside_the_pool_is_pinned(case, monkeypatch):
    _, _, store, _, service, goal, _, task = case
    _fail(store, task)
    calls = _routed(service, monkeypatch, ("pool-a", "pool-b"), "pool-a")
    result = _retry(service, goal, binding_ref="pool-b")
    assert calls == ["pool-b"] and store.get_task(result["to_task_id"]).binding_ref == "pool-b"


def test_owner_pick_outside_the_pool_is_refused(case, monkeypatch):
    _, _, store, _, service, goal, _, task = case
    _fail(store, task)
    calls = _routed(service, monkeypatch, ("pool-a",), "pool-a")
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="owner_retry_model_outside_window"):
        _retry(service, goal, binding_ref="elsewhere")
    assert calls == [] and store.count_tasks() == count


def test_automatic_pick_stays_inside_the_pool(case, monkeypatch):
    _, _, store, _, service, goal, _, task = case
    _fail(store, task)
    _routed(service, monkeypatch, ("pool-a",), "elsewhere")
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="owner_retry_no_model_in_window"):
        _retry(service, goal)
    assert store.count_tasks() == count
    _routed(service, monkeypatch, ("pool-a",), "pool-a")
    assert store.get_task(_retry(service, goal)["to_task_id"]).binding_ref == "pool-a"


def test_router_refusing_the_pin_is_refused(case, monkeypatch):
    _, _, store, _, service, goal, _, task = case
    _fail(store, task)
    _routed(service, monkeypatch, ("pool-a", "pool-b"), "pool-a")
    service.task_resolver = lambda plan_task, *, goal, **kwargs: {"binding_ref": "pool-a", "executor_kind": "opencode"}
    with pytest.raises(TaskStoreError, match="owner_retry_model_unavailable"):
        _retry(service, goal, binding_ref="pool-b")


def test_retry_route_is_wired_and_refuses_with_a_reason(task_server):
    from test_task_service import _enable_legacy_window_fixture, _req
    base, server = task_server
    _enable_legacy_window_fixture(server)
    status, goal = _req(base, "POST", "/api/goals", {
        "objective": "Retry over HTTP", "repository": "dddd2024/reverse-agent",
        "idempotency_key": "http-goal-owner-retry-v1", "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    assert status == 201
    path = f"/api/goals/{goal['id']}/tasks/T001/retry"
    status, body = _req(base, "POST", path, {"expected_revision": 1})
    assert (status, body["error"]) == (409, "owner_retry_not_agent_team")
    status, body = _req(base, "POST", path, {"expected_revision": 1, "binding_ref": 7})
    assert (status, body["error"]) == (409, "owner_retry_model_invalid")


def test_retry_options_report_the_pool_and_retries_left(case, monkeypatch):
    _, _, store, control, service, goal, window, task = case
    options = service.retry_options(goal.id)
    assert options["available"] and options["pool"] == [] and options["automatic_retries_left"] == {"T001": 2}
    _routed(service, monkeypatch, ("pool-a",), "pool-a")
    assert service.retry_options(goal.id)["pool"] == [{"binding_ref": "pool-a", "model_id": "m-pool-a",
                                                        "executor_id": ""}]
    store._conn.execute("UPDATE platform_autonomous_windows SET status='STOPPED' WHERE id=?", (window.id,))
    store._conn.commit()
    stopped = service.retry_options(goal.id)
    assert (stopped["available"], stopped["reason"]) == (False, "owner_retry_no_active_window")


def test_a_step_that_moved_on_during_routing_is_not_retried_twice(case, monkeypatch):
    _, _, store, control, service, goal, _, task = case
    _fail(store, task)
    _routed(service, monkeypatch, ("pool-a",), "pool-a")
    routed = service.task_resolver

    def racing(plan_task, **kwargs):
        # The host's own escalation (or a second click) restarts the step while routing runs.
        store._conn.execute("UPDATE tasks SET status='QUEUED' WHERE id=?", (task.id,))
        store._conn.commit()
        return routed(plan_task, **kwargs)
    service.task_resolver = racing
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="owner_retry_step_not_stopped"):
        _retry(service, goal)
    assert store.count_tasks() == count and control.list_task_escalations(goal.id) == ()


def test_unconfirmed_cleanup_is_not_retried(case):
    _, _, store, _, service, goal, _, task = case
    _fail(store, task, classification="cleanup_unconfirmed")
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="owner_retry_cleanup_unconfirmed"):
        _retry(service, goal)
    assert store.count_tasks() == count


def test_owner_retry_of_a_review_repair_keeps_its_findings(case):
    from reverse_agent.platform_v1.artifact_handoff import _load_evidence
    _, _, store, _, service, goal, _, task = case
    document = {"review_task_id": "task-review", "review_digest": "d" * 64, "findings": ["fix the name"],
                "producer": {"task_id": "task-producer", "commit": "c" * 40}}
    store._bind_artifact_evidence(task.id, category="ReviewRepair", label=task.execution_id, document=document)
    _fail(store, task)
    retry = store.get_task(_retry(service, goal)["to_task_id"])
    assert _load_evidence(retry, "ReviewRepair", retry.execution_id) == document
