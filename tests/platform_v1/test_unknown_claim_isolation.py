"""Synthetic provider-free isolation tests; these do not establish human consent."""
import json
from types import SimpleNamespace

import pytest

from test_native_goal_admission import setup
from reverse_agent.platform_v1 import native_goal_admission as native
from reverse_agent.platform_v1.control_store import sha256_json
from reverse_agent.platform_v1.unknown_claim_isolation import snapshot
from reverse_agent.platform_v1.run_store import TaskStoreError
from reverse_agent.platform_v1.durable_execution import DurableExecutionService
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


@pytest.fixture
def isolated(setup):
    host, old_goal, seen = setup
    old_window = host._native_owner_admit_goal(old_goal.id)
    db = host._task_store._conn
    old_id = host._control_store.list_goal_tasks(old_goal.id)[0]["task_id"]
    db.execute("UPDATE tasks SET status='INTERRUPTED' WHERE id=?", (old_id,))
    db.execute("UPDATE platform_autonomous_windows SET expires_at='2000-01-01T00:00:00+00:00' WHERE id=?",
               (old_window.id,))
    db.execute("INSERT INTO platform_coordinator_claims VALUES (?, ?, 'original', 7, 1, 'ACTIVE', 'old', 'old')",
               (old_id, old_window.id))
    db.execute("INSERT INTO platform_budget_reservations VALUES (?, 7, ?, 123, 456, 'ACTIVE', NULL, NULL, 'old', 'old', '')",
               (old_id, old_window.id))
    db.execute("INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_epoch, "
               "lease_expiry_ms, created_at, updated_at) VALUES ('old-run', ?, 'old-execution', 'fixture', 9, 1, 'old', 'old')",
               (old_id,))
    goal = host._goal_service.create({"objective": "Independent fresh Goal", "repository": "owner/repo",
        "idempotency_key": "fresh", "executor_kind": "codex", "binding_ref": "pinned",
        "orchestration_mode": "single"})
    goal = host._goal_service.plan(goal.id, expected_revision=goal.revision,
        tasks=[{"id": "FRESH", "title": "Fresh", "instruction": "Independent work"}]).goal
    before = snapshot(db)
    seen.clear()
    return host, goal, old_id, old_window, before, sha256_json(before), seen


def admit(data):
    host, goal, _, _, _, digest, _ = data
    return host._native_owner_admit_goal(goal.id, unknown_claims_sha256=digest)


def retained(conn, before):
    for item in before["claims"]:
        for key, table, column, identity in (
            ("claim", "platform_coordinator_claims", "task_id", item["claim"]["task_id"]),
            ("task", "tasks", "id", item["task"]["id"]),
            ("window", "platform_autonomous_windows", "id", item["window"]["id"])):
            assert dict(conn.execute(f"SELECT * FROM {table} WHERE {column}=?", (identity,)).fetchone()) == item[key]
        for key, table, order in (("runs", "durable_runs", "run_id"),
                                  ("reservations", "platform_budget_reservations", "claim_epoch")):
            assert [dict(r) for r in conn.execute(
                f"SELECT * FROM {table} WHERE task_id=? ORDER BY {order}", (item["task"]["id"],))] == item[key]


def test_retention_receipt_and_actual_scheduler(isolated, monkeypatch, tmp_path):
    host, goal, old, old_window, before, digest, seen = isolated
    window = admit(isolated)
    control = host._control_store
    new = control.list_goal_tasks(goal.id)[0]["task_id"]
    retained(host._task_store._conn, before)
    assert old in seen[0] and goal.id in seen[0] and digest in seen[0]
    assert '"provider_terminal_state":"UNKNOWN"' in seen[0]
    proof = json.loads(host._task_store._conn.execute(
        "SELECT evidence_json FROM platform_operation_receipts WHERE subject_id=?", (goal.id,)).fetchone()[0])
    assert proof["unknown_claim_isolation"]["snapshot"] == before
    assert control.runnable_tasks(old_window.id) == ()
    assert control.runnable_tasks(window.id) == (new,)
    selected = []
    coordinator = UnattendedCoordinator(store=host._task_store, control_store=control,
        autonomy=SimpleNamespace(authorize=lambda **kw: True), router=host._router,
        workspace_root=tmp_path)
    monkeypatch.setattr(coordinator, "_execute_claimed_batch",
                        lambda **kw: selected.extend(kw["claimed"]) or len(kw["claimed"]))
    assert coordinator.tick() == 1
    assert selected == [new]
    retained(host._task_store._conn, before)
    with pytest.raises(TaskStoreError, match="unknown_claim_task_held"):
        control.claim_task(window_id=old_window.id, task_id=old, owner="forbidden", lease_ms=10000)
    assert not control.can_complete_host_claim(window_id=old_window.id, task_id=old)
    for method in (control.complete_task_claim, control.abandon_task_claim):
        with pytest.raises(TaskStoreError, match="unknown_claim_task_held"):
            method(window_id=old_window.id, task_id=old, owner="original", epoch=7,
                   **({"reason": "forbidden"} if method == control.abandon_task_claim else {"result": "forbidden"}))
    service = DurableExecutionService(store=host._task_store, router=host._router)
    for method in (service.execute_durable_single, service.execute_durable_sequential_team,
                   service.resume_single, service.resume_sequential_team):
        with pytest.raises(TaskStoreError, match="unknown_claim_task_held"):
            method(old, workspace_root=str(tmp_path))
    retained(host._task_store._conn, before)


@pytest.mark.parametrize("change", ["epoch", "window", "reservation", "claim", "budget", "goal", "binding"])
@pytest.mark.parametrize("point", ["dialog", "transaction"])
def test_drift_refuses_and_rolls_back_new_rows(isolated, monkeypatch, change, point):
    host, goal, old, window, before, digest, _ = isolated
    db = host._task_store._conn
    def mutate():
        if change == "epoch":
            db.execute("UPDATE platform_coordinator_claims SET epoch=8 WHERE task_id=?", (old,))
        elif change == "window":
            db.execute("UPDATE platform_autonomous_windows SET stop_reason='changed' WHERE id=?", (window.id,))
        elif change == "reservation":
            db.execute("UPDATE platform_budget_reservations SET reserved_token_units=124 WHERE task_id=?", (old,))
        elif change == "claim":
            task = host._task_store.create_task(title="Another", executor_kind="codex", binding_ref="pinned")
            db.execute("INSERT INTO platform_coordinator_claims VALUES (?, ?, 'new', 1, 1, 'ACTIVE', 'x', 'x')",
                       (task.id, window.id))
        elif change == "budget":
            db.execute("UPDATE platform_autonomous_windows SET max_tasks=2 WHERE id=?", (window.id,))
        elif change == "goal":
            db.execute("UPDATE platform_goals SET objective='changed' WHERE id=?", (goal.id,))
        else:
            getter = host._store.get_binding_public
            monkeypatch.setattr(host._store, "get_binding_public",
                                lambda ref: {**getter(ref), "model_id": "changed"})
    if point == "dialog":
        monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", lambda _: mutate() or True)
    else:
        activate = host._control_store.activate_window
        def wrapped(*args, **kwargs):
            callback = kwargs["_host_sql_admit"]
            def inside(window_id):
                mutate()
                callback(window_id)
            return activate(*args, **{**kwargs, "_host_sql_admit": inside})
        monkeypatch.setattr(host._control_store, "activate_window", wrapped)
    with pytest.raises(TaskStoreError):
        admit(isolated)
    assert host._control_store.list_goal_tasks(goal.id) == ()
    assert len(host._control_store.list_windows()) == 1
    assert db.execute("SELECT COUNT(*) FROM platform_operation_receipts WHERE subject_id=?", (goal.id,)).fetchone()[0] == 0
    if point == "transaction":
        assert snapshot(db) == before


@pytest.mark.parametrize("mode", ["no_opt_in", "bad_digest", "stale", "refusal", "expiry", "receipt"])
def test_fail_closed(isolated, monkeypatch, mode):
    host, goal, old, window, before, digest, _ = isolated
    if mode == "refusal":
        monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", lambda _: False)
    elif mode == "expiry":
        clock = [10]
        monkeypatch.setattr(native.time, "monotonic", lambda: clock[0])
        monkeypatch.setattr(native.native_owner_dialog, "confirm_admission",
                            lambda _: clock.__setitem__(0, 50) or True)
    elif mode == "receipt":
        original = host._control_store.append_receipt
        def broken(**kw):
            if kw["operation_type"] == "native_goal_admission":
                raise TaskStoreError("fixture_receipt_failure")
            return original(**kw)
        monkeypatch.setattr(host._control_store, "append_receipt", broken)
    with pytest.raises(TaskStoreError):
        if mode == "no_opt_in":
            host._native_owner_admit_goal(goal.id)
        elif mode in {"bad_digest", "stale"}:
            host._native_owner_admit_goal(goal.id, unknown_claims_sha256="bad" if mode == "bad_digest" else "0"*64)
        else:
            admit(isolated)
    retained(host._task_store._conn, before)
    assert host._control_store.get_goal(goal.id) == goal
    assert host._control_store.list_goal_tasks(goal.id) == ()
    assert len(host._control_store.list_windows()) == 1



def test_three_historical_claims_fit_native_dialog(isolated):
    host, goal, old, window, _, _, seen = isolated
    db = host._task_store._conn
    for index in range(2):
        task = host._task_store.create_task(title="Other retained UNKNOWN", executor_kind="codex", binding_ref="pinned")
        db.execute("UPDATE tasks SET status='FAILED' WHERE id=?", (task.id,))
        db.execute("INSERT INTO platform_coordinator_claims VALUES (?, ?, 'original', 7, 1, 'ACTIVE', 'old', 'old')",
                   (task.id, window.id))
        db.execute("INSERT INTO platform_budget_reservations VALUES (?, 7, ?, 123, 456, 'ACTIVE', NULL, NULL, 'old', 'old', '')",
                   (task.id, window.id))
        db.execute("INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, "
                   "lease_expiry_ms, created_at, updated_at) VALUES (?, ?, 'old', 'fixture', 1, 'old', 'old')",
                   (f"extra-{index}", task.id))
    before = snapshot(db)
    host._native_owner_admit_goal(goal.id, unknown_claims_sha256=sha256_json(before))
    retained(db, before)
    assert len(seen) == 1
    for item in before["claims"]:
        assert item["task"]["id"] in seen[0]


@pytest.mark.parametrize("change", ["unbounded", "bad_window", "live_lease", "missing_run"])
def test_invalid_snapshot_never_prompts(isolated, monkeypatch, change):
    host, goal, old, window, _, digest, _ = isolated
    db = host._task_store._conn
    if change == "unbounded":
        for index in range(100):
            task = host._task_store.create_task(title="extra", executor_kind="codex", binding_ref="pinned")
            db.execute("INSERT INTO platform_coordinator_claims VALUES (?, ?, 'extra', 1, 1, 'ACTIVE', 'x', 'x')",
                       (task.id, window.id))
    elif change == "bad_window":
        db.execute("UPDATE platform_autonomous_windows SET expires_at='invalid' WHERE id=?", (window.id,))
    elif change == "live_lease":
        db.execute("UPDATE durable_runs SET lease_expiry_ms=9999999999999 WHERE task_id=?", (old,))
    else:
        db.execute("DELETE FROM durable_runs WHERE task_id=?", (old,))
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission",
                        lambda _: pytest.fail("invalid snapshot prompted"))
    with pytest.raises(TaskStoreError):
        host._native_owner_admit_goal(goal.id, unknown_claims_sha256=digest)
    assert host._control_store.get_goal(goal.id) == goal
    assert host._control_store.list_goal_tasks(goal.id) == ()
