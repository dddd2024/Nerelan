"""#1473 / #1321: a silent CLI, a sleeping host and a restart do not strand goal tasks. Provider-free."""
from __future__ import annotations

import os
import sys
import time

import pytest

from reverse_agent.platform_v1 import durable_execution as de
from reverse_agent.platform_v1 import goal_service as gs
from reverse_agent.platform_v1 import opencode_executor as oe
from reverse_agent.platform_v1.run_store import TaskStoreError
from test_contract_miss_fixup import case  # noqa: F401 (fixture)
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)


# --- A: a CLI that goes silent is stopped as stalled --------------------------------------

class TestStall:
    def test_a_silent_cli_is_stopped_as_stalled(self):
        started = time.monotonic()
        owned = oe._run_owned_cli_process(
            [sys.executable, "-c", "import time; print('{}', flush=True); time.sleep(60)"],
            cwd=".", env=dict(os.environ), timeout=30, stall_seconds=1.0, poll_seconds=.1)
        assert owned.stalled and owned.timed_out and owned.cleanup_confirmed
        assert time.monotonic() - started < 15

    def test_a_cli_that_keeps_writing_is_not_stalled(self):
        owned = oe._run_owned_cli_process(
            [sys.executable, "-c", "import time\nfor i in range(8):\n print(i, flush=True); time.sleep(.25)"],
            cwd=".", env=dict(os.environ), timeout=30, stall_seconds=1.0, poll_seconds=.1)
        assert not owned.stalled and not owned.timed_out and owned.returncode == 0

    def test_without_a_stall_limit_only_the_timeout_applies(self):
        owned = oe._run_owned_cli_process([sys.executable, "-c", "import time; time.sleep(30)"],
                                          cwd=".", env=dict(os.environ), timeout=1, stall_seconds=None)
        assert owned.timed_out and not owned.stalled

    @pytest.mark.parametrize("raw, expected", [("", 900.0), ("0", None), ("30", 120.0), ("1800", 1800.0),
                                               ("junk", 900.0), ("-5", 900.0)])
    def test_stall_setting(self, monkeypatch, raw, expected):
        monkeypatch.setenv("REVERSE_AGENT_EXECUTOR_STALL_SECONDS", raw)
        assert oe.executor_stall_seconds() == expected


# --- B: sleep past the lease does not fence a live executor (#1321) -----------------------

def _run(store, task, *, owner="coordinator-1", epoch=1, expiry_ms=None):
    now = int(time.time() * 1000)
    store._conn.execute(
        "INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_owner, lease_epoch, "
        "heartbeat_at_ms, lease_expiry_ms, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (f"run-{task.id}", task.id, task.execution_id, "wt", owner, epoch, now - 600_000,
         now - 1000 if expiry_ms is None else expiry_ms, "2026-11-12T00:00:00Z", "2026-11-12T00:00:00Z"))
    store._conn.execute("UPDATE tasks SET status='RUNNING' WHERE id=?", (task.id,))
    store._conn.commit()
    return f"run-{task.id}"


class TestSleepingHost:
    def test_reconcile_leaves_this_process_s_live_run_alone(self, case):
        store, task = case[2], case[-1]
        _run(store, task)
        now = int(time.time() * 1000)
        assert store._reconcile_expired_runs(now_ms=now, max_age_ms=1000, live_owner="coordinator-1",
                                             live_task_ids={task.id}) == ()
        assert store.get_task(task.id).status == "RUNNING"
        # Another owner's run, or ours after the executor is gone, is still reconciled.
        records = store._reconcile_expired_runs(now_ms=now, max_age_ms=1000, live_owner="coordinator-1",
                                                live_task_ids=set())
        assert [r["recovery_classification"] for r in records] == ["orphan_stale_lease"]
        assert store.get_task(task.id).status == "INTERRUPTED"

    def test_heartbeat_renews_an_aged_lease_only_while_still_held(self, case):
        store, task = case[2], case[-1]
        run_id = _run(store, task)
        with pytest.raises(TaskStoreError, match="lease_expired"):
            store._heartbeat_durable_lease(run_id, "coordinator-1", 1, 300_000)
        store._heartbeat_durable_lease(run_id, "coordinator-1", 1, 300_000, renew_expired=True)
        expiry = store._conn.execute("SELECT lease_expiry_ms FROM durable_runs WHERE run_id=?", (run_id,)).fetchone()[0]
        assert expiry > time.time() * 1000
        # Once reconciled (owner cleared) or taken over, it is fenced even after sleep.
        store._conn.execute("UPDATE durable_runs SET lease_owner='', lease_expiry_ms=1 WHERE run_id=?", (run_id,))
        store._conn.commit()
        with pytest.raises(TaskStoreError, match="lease_fenced"):
            store._heartbeat_durable_lease(run_id, "coordinator-1", 1, 300_000, renew_expired=True)

    def test_the_heartbeat_asks_for_renewal_after_the_wall_clock_jumped(self, monkeypatch):
        calls = []

        class Store:
            def _heartbeat_durable_lease(self, run_id, owner, epoch, expiry_ms, **kwargs):
                calls.append(kwargs)
                if len(calls) >= 3:
                    context._stop_event.set()

        wall = [1_000_000.0]
        real_time = time.time
        monkeypatch.setattr(de.time, "time", lambda: wall[0])
        context = de._HeartbeatContext(store=Store(), run_id="r", owner="o", epoch=1,
                                       expiry_ms=300_000, heartbeat_window_ms=50)

        def body():
            deadline = real_time() + 5
            while len(calls) < 1 and real_time() < deadline:
                time.sleep(.005)
            wall[0] += 3600  # an hour of sleep: the monotonic clock barely moved
            while len(calls) < 3 and real_time() < deadline:
                time.sleep(.005)
        context.heartbeat_during(body)
        assert calls[0] == {} and calls[1] == {"renew_expired": True} and calls[2] == {}


# --- C/D: interrupted work moves to a new task ------------------------------------------

def _resolver(plan_task, **kwargs):
    return {"executor_kind": "opencode", "binding_ref": "local-test-binding", "model_id": "fixture/model",
            "reason": "fixture_route", "tier": 3}


class TestEscalation:
    def test_a_dispatch_refused_after_a_stale_lease_retries_in_a_new_task(self, case):
        store, control, service, goal, task = case[2], case[3], case[4], case[5], case[-1]
        run_id = _run(store, task)
        store._conn.execute("UPDATE durable_runs SET recovery_classification='orphan_stale_lease' WHERE run_id=?",
                            (run_id,))
        store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='ambiguous_external_operation', "
                            "failure_detail=? WHERE id=?", (gs.REFUSED_SECOND_DISPATCH, task.id))
        store._conn.commit()
        service.task_resolver = _resolver
        steps = service.escalate_failed_tasks(goal.id)
        assert [s["from_task_id"] for s in steps] == [task.id]
        assert control.list_goal_tasks(goal.id)[0]["task_id"] == steps[0]["to_task_id"] != task.id

    def test_refused_dispatch_with_pending_operation_stays_parked(self, case):
        store, control, service, goal, task = case[2], case[3], case[4], case[5], case[-1]
        run_id = _run(store, task)
        store._conn.execute("UPDATE durable_runs SET recovery_classification='orphan_stale_lease' WHERE run_id=?",
                            (run_id,))
        store._conn.execute("INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
                            "idempotency_key, request_digest, created_at, updated_at) VALUES "
                            "('pending-dispatch', ?, ?, 'remote-dispatch', 'idem', 'digest', 'now', 'now')",
                            (run_id, task.id))
        store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='ambiguous_external_operation', "
                            "failure_detail=? WHERE id=?", (gs.REFUSED_SECOND_DISPATCH, task.id))
        store._conn.commit()
        service.task_resolver = _resolver
        assert service.escalate_failed_tasks(goal.id) == ()
        assert control.list_goal_tasks(goal.id)[0]["task_id"] == task.id
        assert store._conn.execute("SELECT state FROM durable_external_operations WHERE operation_id='pending-dispatch'").fetchone()["state"] == "PENDING"
        with pytest.raises(Exception, match="owner_retry_external_operation_unresolved"):
            service.owner_retry(goal.id, "T001", expected_revision=goal.revision)

    def test_an_ambiguous_dispatch_without_an_interruption_stays_put(self, case):
        store, service, goal, task = case[2], case[4], case[5], case[-1]
        _run(store, task)  # recovery_classification stays 'normal'
        store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='ambiguous_external_operation', "
                            "failure_detail=? WHERE id=?", (gs.REFUSED_SECOND_DISPATCH, task.id))
        store._conn.commit()
        service.task_resolver = _resolver
        assert service.escalate_failed_tasks(goal.id) == ()

    def test_preparation_broken_by_a_restart_retries_with_the_same_binding(self, case):
        store, control, service, goal, task = case[2], case[3], case[4], case[5], case[-1]
        store._conn.execute("UPDATE tasks SET status='BLOCKED', failure_classification='blocked', "
                            "failure_detail='worktree_preparation_failed:worktree_not_registered' WHERE id=?", (task.id,))
        store._conn.commit()
        def forbidden(*args, **kwargs):
            raise AssertionError("a host-broken preparation is not a capability failure")
        service.task_resolver = forbidden
        [step] = service.escalate_failed_tasks(goal.id)
        retry = store.get_task(step["to_task_id"])
        assert (retry.binding_ref, retry.executor_kind) == (task.binding_ref, task.executor_kind)

    def test_other_blocked_tasks_and_dispatched_preparations_never_escalate(self, case):
        store, service, goal, task = case[2], case[4], case[5], case[-1]
        store._conn.execute("UPDATE tasks SET status='BLOCKED', failure_classification='blocked', "
                            "failure_detail='owner_policy_denied' WHERE id=?", (task.id,))
        store._conn.commit()
        assert service.escalate_failed_tasks(goal.id) == ()
        run_id = _run(store, task)
        store._conn.execute("UPDATE tasks SET status='BLOCKED', failure_detail='worktree_preparation_failed:x' WHERE id=?",
                            (task.id,))
        store._conn.execute("INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
                            "idempotency_key, request_digest, created_at, updated_at) VALUES "
                            "('op', ?, ?, 'k', 'i', 'd', 'now', 'now')", (run_id, task.id))
        store._conn.commit()
        assert service.escalate_failed_tasks(goal.id) == ()


def test_reconcile_sweeps_window_goals_with_failed_or_blocked_tasks(case):
    from types import SimpleNamespace
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
    store, control, goal, window, task = case[2], case[3], case[5], case[6], case[-1]
    store._conn.execute("UPDATE tasks SET status='BLOCKED' WHERE id=?", (task.id,))
    store._conn.commit()
    seen = []
    coordinator = UnattendedCoordinator.__new__(UnattendedCoordinator)
    coordinator.control_store, coordinator._last_error = control, ""
    coordinator.goal_escalator = seen.append
    coordinator._sweep_escalations()
    assert seen == [goal.id]
    coordinator.control_store = SimpleNamespace(active_window=lambda: None)
    seen.clear()
    coordinator._sweep_escalations()
    assert seen == []


def test_an_unchanged_stuck_goal_is_swept_at_most_every_repeat_interval(case, monkeypatch):
    from reverse_agent.platform_v1 import unattended_coordinator as uc
    store, control, goal, task = case[2], case[3], case[5], case[-1]
    store._conn.execute("UPDATE tasks SET status='FAILED', updated_at='2026-11-12T00:00:00Z' WHERE id=?", (task.id,))
    store._conn.commit()
    clock = [1000.0]
    monkeypatch.setattr(uc.time, "monotonic", lambda: clock[0])
    seen = []
    coordinator = uc.UnattendedCoordinator.__new__(uc.UnattendedCoordinator)
    coordinator.control_store, coordinator._last_error, coordinator.goal_escalator = control, "", seen.append
    coordinator._sweep_escalations()
    clock[0] += 60
    coordinator._sweep_escalations()
    assert seen == [goal.id]  # unchanged: not again after a minute
    store._conn.execute("UPDATE tasks SET updated_at='2026-11-12T00:05:00Z' WHERE id=?", (task.id,))
    store._conn.commit()
    coordinator._sweep_escalations()
    assert seen == [goal.id, goal.id]  # changed: at once
    clock[0] += uc.SWEEP_REPEAT_SECONDS
    coordinator._sweep_escalations()
    assert seen == [goal.id, goal.id, goal.id]  # unchanged but due again


# --- 2026-11-17: a restart during preparation, before anything was dispatched ------------

def _stranded_preparation(store, control, window, task, *, claim_expired=True):
    """The incident row: a dead owner's claim and an INTERRUPTED pre-dispatch durable run."""
    epoch, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="dead-host", lease_ms=60_000)
    now = int(time.time() * 1000)
    if claim_expired:
        store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms = ? WHERE task_id = ?",
                            (now - 1000, task.id))
    store._conn.execute(
        "INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_owner, lease_epoch, "
        "heartbeat_at_ms, lease_expiry_ms, recovery_classification, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (f"run-{task.id}", task.id, task.execution_id, "wt", "", 1, now - 600_000, now - 300_000,
         "orphan_stale_lease", "2026-11-17T07:00:00Z", "2026-11-17T07:00:00Z"))
    store._conn.execute("UPDATE tasks SET status='INTERRUPTED' WHERE id=?", (task.id,))
    store._conn.commit()
    return epoch


def _orphaned(store, task):
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='orphaned_preparation', "
                        "failure_detail='orphaned_preparation' WHERE id=?", (task.id,))
    store._conn.commit()


class TestOrphanedPreparation:
    def test_escalation_retries_it_on_the_same_binding_without_spending_max_retries(self, case):
        store, control, service, goal, window, task = case[2], case[3], case[4], case[5], case[6], case[-1]
        store._conn.execute("UPDATE platform_autonomous_windows SET max_retries = 0 WHERE id = ?", (window.id,))
        _orphaned(store, task)

        def forbidden(*args, **kwargs):
            raise AssertionError("a restart before dispatch is not a capability failure")
        service.task_resolver = forbidden
        [step] = service.escalate_failed_tasks(goal.id)
        assert step["reason"] == f"{gs.HOST_RETRY_REASON}:interrupted"
        retry = store.get_task(step["to_task_id"])
        assert (retry.binding_ref, retry.executor_kind) == (task.binding_ref, task.executor_kind)
        assert gs._routing_retries_spent(control.list_task_escalations(goal.id)) == 0

    @pytest.mark.parametrize("trace", ["external_operation", "claim_live", "lease_live", "worktree", "checkpoint"])
    def test_no_replacement_while_anything_of_the_attempt_may_remain(self, case, trace):
        store, control, service, goal, window, task = case[2], case[3], case[4], case[5], case[6], case[-1]
        _stranded_preparation(store, control, window, task, claim_expired=trace != "claim_live")
        _orphaned(store, task)
        run_id = f"run-{task.id}"
        if trace == "external_operation":
            store._conn.execute("INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
                                "idempotency_key, request_digest, state, created_at, updated_at) VALUES "
                                "('op', ?, ?, 'k', 'i', 'd', 'SUCCESS', 'now', 'now')", (run_id, task.id))
        elif trace == "lease_live":
            store._conn.execute("UPDATE durable_runs SET lease_owner='other', lease_expiry_ms=? WHERE run_id=?",
                                (int(time.time() * 1000) + 600_000, run_id))
        elif trace == "worktree":
            store._conn.execute("UPDATE durable_runs SET worktree_prepared_at='now' WHERE run_id=?", (run_id,))
        elif trace == "checkpoint":
            store._conn.execute("UPDATE durable_runs SET accepted_checkpoint='PRE_PLANNER' WHERE run_id=?", (run_id,))
        store._conn.commit()
        service.task_resolver = _resolver
        assert service.escalate_failed_tasks(goal.id) == ()
        assert control.list_goal_tasks(goal.id)[0]["task_id"] == task.id

    def test_catch_up_closes_the_legacy_interrupted_row_and_settles_the_dead_claim(self, case):
        store, control, service, goal, window, task = case[2], case[3], case[4], case[5], case[6], case[-1]
        epoch = _stranded_preparation(store, control, window, task)
        assert control.recover_orphaned_preparations() == (task.id,)
        closed = store.get_task(task.id)
        assert (closed.status, closed.failure_classification) == ("FAILED", "orphaned_preparation")
        assert len([e for e in store.get_events(task.id) if e.title == "Orphaned preparation failed"]) == 1
        claim = store._conn.execute("SELECT owner, epoch, status FROM platform_coordinator_claims WHERE task_id=?",
                                    (task.id,)).fetchone()
        assert dict(claim) == {"owner": "dead-host", "epoch": epoch, "status": "FAILED"}
        reservation = store._conn.execute("SELECT state FROM platform_budget_reservations WHERE task_id=?",
                                          (task.id,)).fetchone()
        assert reservation["state"] == "UNKNOWN"  # never released or refunded
        # Idempotent: nothing more to close or settle.
        assert control.recover_orphaned_preparations() == ()
        assert len([e for e in store.get_events(task.id) if e.title == "Orphaned preparation failed"]) == 1
        # The goal now retries it as a host fault.
        service.task_resolver = _resolver
        [step] = service.escalate_failed_tasks(goal.id)
        assert step["from_task_id"] == task.id and step["reason"] == f"{gs.HOST_RETRY_REASON}:interrupted"

    @pytest.mark.parametrize("trace", ["claim_live", "external_operation", "worktree", "not_orphan_stale"])
    def test_catch_up_leaves_anything_that_may_still_matter_interrupted(self, case, trace):
        store, control, window, task = case[2], case[3], case[6], case[-1]
        _stranded_preparation(store, control, window, task, claim_expired=trace != "claim_live")
        run_id = f"run-{task.id}"
        if trace == "external_operation":
            store._conn.execute("INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
                                "idempotency_key, request_digest, state, created_at, updated_at) VALUES "
                                "('op', ?, ?, 'k', 'i', 'd', 'PENDING', 'now', 'now')", (run_id, task.id))
        elif trace == "worktree":
            store._conn.execute("UPDATE durable_runs SET worktree_prepared_at='now' WHERE run_id=?", (run_id,))
        elif trace == "not_orphan_stale":
            store._conn.execute("UPDATE durable_runs SET recovery_classification='interrupted' WHERE run_id=?",
                                (run_id,))
        store._conn.commit()
        assert control.recover_orphaned_preparations() == ()
        assert store.get_task(task.id).status == "INTERRUPTED"
        claim = store._conn.execute("SELECT status FROM platform_coordinator_claims WHERE task_id=?",
                                    (task.id,)).fetchone()
        assert claim["status"] == "ACTIVE"  # only claims of closed tasks are settled
