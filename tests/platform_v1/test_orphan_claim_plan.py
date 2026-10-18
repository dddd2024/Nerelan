"""Synthetic evidence only: no remote receipt or side effect is simulated as trusted."""

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.orphan_claim_plan import plan_orphan_claim
from reverse_agent.platform_v1.run_store import TaskStore


@pytest.fixture
def subject():
    store = TaskStore()
    control = PlatformControlStore(store)
    task = store.create_task(title="Synthetic orphan", executor_kind="opencode")
    store.set_state(task.id, "FAILED")
    conn = store._conn
    conn.execute(
        "INSERT INTO platform_autonomous_windows "
        "(id,policy_id,policy_revision,policy_digest,owner_identity,confirmation,"
        "starts_at,expires_at,status,repositories_json,capabilities_json,"
        "max_concurrent_tasks,max_tasks,max_retries,created_at,updated_at) "
        "VALUES ('old','policy',1,'digest','owner','fixture','2000-01-01T00:00:00Z',"
        "'2000-01-02T00:00:00Z','EXPIRED','[]','[]',1,3,0,'old','old')"
    )
    conn.execute(
        "INSERT INTO platform_coordinator_claims VALUES (?, 'old', 'owner', 7, 1, 'ACTIVE', 'old', 'old')",
        (task.id,),
    )
    conn.execute(
        "INSERT INTO platform_budget_reservations VALUES (?,7,'old',50,60,'ACTIVE',NULL,NULL,'old','old','')",
        (task.id,),
    )
    conn.execute(
        "INSERT INTO durable_runs (run_id,task_id,execution_id,worktree_path,lease_owner,"
        "lease_epoch,lease_expiry_ms,created_at,updated_at) VALUES ('run',?,'exec','',"
        "'worker',2,1,'old','old')", (task.id,),
    )
    yield store, control, task.id
    store._conn.close()


def observe_unchanged(subject, **kwargs):
    store, control, task_id = subject
    before = list(store._conn.iterdump())
    changes = store._conn.total_changes
    for _ in range(2):
        plan = plan_orphan_claim(control, task_id=task_id, run_id="run", now_ms=2_000_000_000_000, **kwargs)
        assert plan.classification == "UNKNOWN"
        assert plan.budget_state == "UNKNOWN"
        assert plan.release_allowed is False
    assert store._conn.total_changes == changes
    assert list(store._conn.iterdump()) == before
    assert store._conn.execute("SELECT status FROM platform_coordinator_claims").fetchone()[0] == "ACTIVE"
    assert store._conn.execute("SELECT state FROM platform_budget_reservations").fetchone()[0] == "ACTIVE"
    return plan


@pytest.mark.parametrize("status", ["FAILED", "INTERRUPTED"])
def test_absent_remote_operations_cannot_prove_terminal(subject, status):
    store, _, task_id = subject
    store.set_state(task_id, status)
    plan = observe_unchanged(subject)
    assert plan.reason == "authoritative_terminal_receipt_format_unavailable"
    assert (plan.owner, plan.epoch, plan.window_id) == ("owner", 7, "old")
    assert plan.policy_binding == ("policy", 1, "digest")
    assert plan.reservation_binding == (task_id, 7, "old", 50, 60)
    assert plan.run_lease_owner == "worker"
    assert plan.run_lease_epoch == 2


@pytest.mark.parametrize("kind", ["counterfeit", "mismatched_task", "mismatched_run", "stale", "pending"])
def test_dispatch_bookkeeping_is_never_a_terminal_receipt(subject, kind):
    store, _, task_id = subject
    other = store.create_task(title="Other synthetic task")
    if kind == "mismatched_run":
        store._conn.execute(
            "INSERT INTO durable_runs (run_id,task_id,execution_id,worktree_path,created_at,updated_at) "
                "VALUES ('other',?,'other','','old','old')", (other.id,))
    store._conn.execute(
        "INSERT INTO durable_external_operations VALUES ('op',?,?,?,?,?,?,?,?,?,?)",
        ("other" if kind == "mismatched_run" else "run",
         other.id if kind == "mismatched_task" else task_id,
         "remote_terminal", "idempotency", "digest", "PENDING" if kind == "pending" else "SUCCESS",
         "caller-asserted-remote-id", "success", "old", "old"),
    )
    if kind == "stale":
        store._conn.execute("UPDATE durable_runs SET lease_epoch=99")
    assert observe_unchanged(subject).reason == "authoritative_terminal_receipt_format_unavailable"


@pytest.mark.parametrize("sql,reason", [
    ("UPDATE platform_budget_reservations SET claim_epoch=6", "active_claim_reservation_pair_missing"),
    ("UPDATE platform_budget_reservations SET window_id='different'", "active_claim_reservation_pair_missing"),
    ("UPDATE platform_autonomous_windows SET policy_digest=''", "original_policy_binding_missing"),
    ("UPDATE platform_autonomous_windows SET expires_at='2999-01-01T00:00:00Z'", "original_claim_or_window_not_expired"),
    ("UPDATE platform_coordinator_claims SET expires_at_ms=9999999999999", "original_claim_or_window_not_expired"),
    ("UPDATE durable_runs SET lease_expiry_ms=9999999999999", "run_lease_not_expired"),
    ("UPDATE durable_runs SET lease_owner=''", "original_run_lease_fence_missing"),
    ("UPDATE durable_runs SET lease_epoch=0", "original_run_lease_fence_missing"),
    ("UPDATE platform_coordinator_claims SET owner=''", "original_claim_fence_missing"),
    ("UPDATE platform_coordinator_claims SET epoch=0", "active_claim_reservation_pair_missing"),
    ("UPDATE durable_runs SET run_id='different'", "task_run_binding_missing"),
    ("UPDATE tasks SET status='RUNNING'", "task_not_terminal_candidate"),
])
def test_binding_and_lease_diagnostics_preserve_active_pair(subject, sql, reason):
    subject[0]._conn.execute(sql)
    assert observe_unchanged(subject).reason == reason


def test_missing_task_and_invalid_input_fail_closed(subject):
    _, control, _ = subject
    plan = plan_orphan_claim(control, task_id="missing", run_id="run", now_ms=0)
    assert plan.reason == "task_missing"
    assert plan.release_allowed is False
    with pytest.raises(ValueError):
        plan_orphan_claim(control, task_id="", run_id="run", now_ms=0)
