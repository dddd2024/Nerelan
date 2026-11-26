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
    from test_task_service import _req
    base, server = task_server
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


def test_owner_retry_retains_non_empty_worktree_across_executor_change(case, tmp_path):
    import subprocess
    from reverse_agent.platform_v1.artifact_handoff import _load_evidence
    from reverse_agent.platform_v1.contract_recovery import FIXUP
    root, _, store, _, service, goal, _, task = case
    wt = tmp_path / "wt"
    subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", str(wt), "HEAD"], check=True)
    (wt / "kept.txt").write_text("saved\n", encoding="utf-8")
    store.add_event(task.id, event_type="WORKSPACE_READY", title="wt", description="wt",
                    metadata={"execution_id": task.execution_id, "workspace": str(wt)})
    _fail(store, task, classification="api_error_429")
    service.task_resolver = lambda plan_task, *, goal, **kw: {
        "binding_ref": "claude-sonnet", "executor_kind": "claude_code", "model_id": "sonnet",
        "tier": 4, "reason": "fixture", "context_window": 200000}
    retry = store.get_task(_retry(service, goal)["to_task_id"])
    fixup = _load_evidence(retry, FIXUP, retry.execution_id)
    assert fixup is not None and fixup["rerouted"] is True
    assert retry.executor_kind == "claude_code" and retry.branch
    disp = _load_evidence(store.get_task(task.id), "AttemptDisposition", task.execution_id)
    assert disp is not None and disp["disposition"] == "reused"


def test_owner_retry_discards_empty_worktree(case, tmp_path):
    import subprocess
    from reverse_agent.platform_v1.artifact_handoff import _load_evidence
    from reverse_agent.platform_v1.contract_recovery import FIXUP
    root, _, store, _, service, goal, _, task = case
    wt = tmp_path / "wt-empty"
    subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", str(wt), "HEAD"], check=True)
    store.add_event(task.id, event_type="WORKSPACE_READY", title="wt", description="wt",
                    metadata={"execution_id": task.execution_id, "workspace": str(wt)})
    _fail(store, task, classification="api_error_429")
    retry = store.get_task(_retry(service, goal)["to_task_id"])
    assert _load_evidence(retry, FIXUP, retry.execution_id) is None
    disp = _load_evidence(store.get_task(task.id), "AttemptDisposition", task.execution_id)
    assert disp is not None and disp["disposition"] == "discarded"


def test_owner_retry_discards_out_of_scope_worktree(case, tmp_path):
    import json, subprocess
    from reverse_agent.platform_v1.artifact_handoff import _load_evidence
    from reverse_agent.platform_v1.contract_recovery import FIXUP
    from reverse_agent.platform_v1.functional_validation import CONTRACT_CATEGORY, digest, normalize_allowed_paths
    root, _, store, _, service, goal, _, task = case
    row = store._conn.execute("SELECT detail FROM task_evidence WHERE task_id=? AND category=?", (task.id, CONTRACT_CATEGORY)).fetchone()
    contract = json.loads(row["detail"])
    contract["requires_implementation"] = True
    contract["allowed_paths"] = list(normalize_allowed_paths(["allowed/file.txt"]))
    raw_detail = json.dumps(contract, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    d = digest(contract)
    store._conn.execute(
        "UPDATE task_evidence SET detail=?, value=?, raw_json_digest=? WHERE task_id=? AND category=?",
        (raw_detail, d, d, task.id, CONTRACT_CATEGORY))
    wt = tmp_path / "wt-oob"
    subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach", str(wt), "HEAD"], check=True)
    (wt / "outside.txt").write_text("oob\n", encoding="utf-8")
    store.add_event(task.id, event_type="WORKSPACE_READY", title="wt", description="wt",
                    metadata={"execution_id": task.execution_id, "workspace": str(wt)})
    _fail(store, task, classification="deterministic_validation_failure")
    retry = store.get_task(_retry(service, goal)["to_task_id"])
    assert _load_evidence(retry, FIXUP, retry.execution_id) is None
    disp = _load_evidence(store.get_task(task.id), "AttemptDisposition", task.execution_id)
    assert disp is not None and disp["disposition"] == "discarded"


# --- Host upgrade sweep: host-caused stops resume without an Owner click (2026-11-26) ---

def _sweep(service, window, version="new-host-sha", allow=True):
    seen = []

    def authorize(goal, failed):
        seen.append(failed.id)
        return allow
    return service.retry_after_upgrade(window.id, host_version=version, authorize=authorize), seen


@pytest.mark.parametrize("classification", ["patch_hygiene_failed", "review_not_independent", "server_stream_stalled"])
def test_upgrade_sweep_retries_a_host_caused_stop_once(case, classification):
    _, _, store, control, service, goal, window, task = case
    _fail(store, task, classification)
    retried, seen = _sweep(service, window)
    assert [row["from_task_id"] for row in retried] == [task.id] and seen == [task.id]
    [row] = control.list_task_escalations(goal.id)
    assert row["reason"] == gs.OWNER_RETRY_REASON  # the Owner-retry path: no max_retries spent
    events = store.get_events(retried[0]["to_task_id"])
    assert any(e.metadata.get("origin") == gs.UPGRADE_RETRY_ORIGIN for e in events)
    # The new attempt is pending: a second sweep moves nothing.
    assert _sweep(service, window)[0] == []


@pytest.mark.parametrize("detail, retried", [("functional_patch_hygiene_failed", True),
                                             ("functional_check_failed", False)])
def test_upgrade_sweep_reads_the_hygiene_gate_inside_a_generic_validation_failure(case, detail, retried):
    _, _, store, _, service, _, window, task = case
    _fail(store, task, "deterministic_validation_failure")
    store._conn.execute("UPDATE tasks SET failure_detail=? WHERE id=?", (detail, task.id))
    store._conn.commit()
    assert bool(_sweep(service, window)[0]) is retried


def test_upgrade_sweep_retries_a_step_at_most_once_per_host_version(case):
    # Even when the retried attempt fails the same way again on this code and its
    # run recorded a different (explicit) execution authority (#1785 review).
    _, _, store, control, service, goal, window, task = case
    _fail(store, task, "patch_hygiene_failed")
    retried, _ = _sweep(service, window)
    second = store.get_task(retried[0]["to_task_id"])
    _fail(store, second, "patch_hygiene_failed")
    assert _sweep(service, window)[0] == []
    assert len(control.list_task_escalations(goal.id)) == 1
    retried, _ = _sweep(service, window, version="newer-host-sha")
    assert [row["from_task_id"] for row in retried] == [second.id]


def test_upgrade_retry_and_its_version_mark_commit_together(case, monkeypatch):
    _, _, store, control, service, goal, window, task = case
    _fail(store, task, "patch_hygiene_failed")
    count = store.count_tasks()
    original = store._append_event

    import sqlite3

    def failing(**kwargs):
        if (kwargs.get("metadata") or {}).get("origin") == gs.UPGRADE_RETRY_ORIGIN:
            raise sqlite3.OperationalError("disk I/O error")
        return original(**kwargs)
    monkeypatch.setattr(store, "_append_event", failing)
    # A storage fault is not a refusal: it ends the sweep unfinished (the
    # coordinator retries next tick) and commits nothing.
    with pytest.raises(sqlite3.OperationalError):
        _sweep(service, window)
    assert store.count_tasks() == count and tuple(control.list_task_escalations(goal.id)) == ()
    monkeypatch.setattr(store, "_append_event", original)
    assert [row["from_task_id"] for row in _sweep(service, window)[0]] == [task.id]


def test_upgrade_sweep_leaves_model_judged_failures_alone(case):
    _, _, store, _, service, _, window, task = case
    _fail(store, task, "deterministic_validation_failure")
    assert _sweep(service, window) == ([], [])


def test_owner_retry_refuses_when_the_step_moved_past_the_expected_attempt(case):
    _, _, store, control, service, goal, _, task = case
    _fail(store, task, "patch_hygiene_failed")
    with pytest.raises(TaskStoreError, match="owner_retry_step_not_stopped"):
        _retry(service, goal, expected_source_task_id="task-some-older-attempt")
    assert tuple(control.list_task_escalations(goal.id)) == ()
    assert _retry(service, goal, expected_source_task_id=task.id)["from_task_id"] == task.id


def test_upgrade_sweep_skips_an_attempt_that_already_ran_on_this_version(case):
    _, _, store, _, service, _, window, task = case
    _fail(store, task, "patch_hygiene_failed")
    values = {"run_id": "run-x", "task_id": task.id, "execution_authority_sha": "new-host-sha",
              "created_at": "2026-11-26T00:00:00Z", "updated_at": "2026-11-26T00:00:00Z"}
    for _, name, kind, notnull, default, _ in store._conn.execute("PRAGMA table_info(durable_runs)").fetchall():
        if notnull and default is None and name not in values:
            values[name] = 0 if "INT" in str(kind).upper() else "x"
    store._conn.execute(f"INSERT INTO durable_runs ({', '.join(values)}) VALUES ({', '.join('?' * len(values))})",
                        tuple(values.values()))
    store._conn.commit()
    assert _sweep(service, window) == ([], [])
    retried, _ = _sweep(service, window, version="newer-host-sha")
    assert [row["from_task_id"] for row in retried] == [task.id]


def test_upgrade_sweep_needs_the_dispatch_authorization(case):
    _, _, store, control, service, goal, window, task = case
    _fail(store, task, "patch_hygiene_failed")
    retried, seen = _sweep(service, window, allow=False)
    assert retried == [] and seen == [task.id]
    assert tuple(control.list_task_escalations(goal.id)) == ()


def test_upgrade_sweep_repairs_a_blocked_goal_left_over_a_queued_retry(case):
    # #1785 review: a crash after owner_retry committed but before the goal status
    # refresh leaves a BLOCKED goal whose current attempt is QUEUED.
    _, _, store, control, service, goal, window, task = case
    _fail(store, task, "patch_hygiene_failed")
    retried, _ = _sweep(service, window)
    store._conn.execute("UPDATE platform_goals SET status='BLOCKED' WHERE id=?", (goal.id,))
    store._conn.commit()
    assert _sweep(service, window, version="restarted-same-or-newer")[0] == []
    assert control.get_goal(goal.id).status == "RUNNING"
