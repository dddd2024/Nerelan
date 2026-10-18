"""Provider-free R0 transaction bridge tests. No live Owner grant or dispatch."""
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def _payload(policy="owner-one"):
    now = datetime.now(timezone.utc)
    return {
        "policy_id": policy, "policy_revision": 1, "owner_identity": "LOCAL_OWNER",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
        "repositories": ["dddd2024/Nerelan"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 1, "max_retries": 0,
        "max_token_units": 0, "max_cost_micro_units": 0,
        "provider_quota_state": "UNKNOWN", "enforcement_class": "HARD_ADMISSION_ENFORCED",
    }


@pytest.fixture
def store(tmp_path):
    db = TaskStore(str(tmp_path / "host-atomic.sqlite"))
    yield db, PlatformControlStore(db)
    db._conn.close()


def test_window_and_host_sql_admission_share_commit(store, monkeypatch):
    db, control = store
    goals, planned = _planned_goal(db, control, monkeypatch)
    seen = []

    def admit(window_id):
        assert control.get_window(window_id).status == "ACTIVE"
        db._conn.execute(
            "CREATE TABLE IF NOT EXISTS test_atomic_receipts (window_id TEXT NOT NULL)")
        db._conn.execute("INSERT INTO test_atomic_receipts VALUES (?)", (window_id,))
        control.approve_goal(planned.id, expected_revision=planned.revision)
        goals._launch(planned.id, expected_revision=planned.revision, window_id=window_id)
        seen.append(window_id)

    data = {**_payload(), "repositories": [planned.repository]}
    window = control.activate_window(data, confirmation="ACTIVATE",
                                     _host_expected_goal_id=planned.id, _host_sql_admit=admit)
    assert seen == [window.id]
    assert db._conn.execute("SELECT window_id FROM test_atomic_receipts").fetchone()[0] == window.id


def test_host_sql_denial_rolls_back_window_and_receipt(store):
    db, control = store
    db._conn.execute("CREATE TABLE test_atomic_receipts (window_id TEXT)")

    def refuse(window_id):
        db._conn.execute("INSERT INTO test_atomic_receipts VALUES (?)", (window_id,))
        raise TaskStoreError("host_goal_snapshot_changed")

    with pytest.raises(TaskStoreError, match="host_goal_snapshot_changed"):
        control.activate_window(_payload(), confirmation="ACTIVATE",
                                _host_expected_goal_id="selected-goal", _host_sql_admit=refuse)
    assert control.list_windows() == ()
    assert db._conn.execute("SELECT COUNT(*) FROM test_atomic_receipts").fetchone()[0] == 0


def test_replay_never_skips_host_sql_admission(store):
    _, control = store
    data = _payload()
    original = control.activate_window(data, confirmation="ACTIVATE")
    with pytest.raises(TaskStoreError, match="host_atomic_admission_replay"):
        control.activate_window(data, confirmation="ACTIVATE",
                                _host_expected_goal_id="selected-goal",
                                _host_sql_admit=lambda _: pytest.fail("cannot silently replay"))
    assert control.list_windows() == (original,)


def test_invalid_callback_and_delegated_mix_rejected_without_writes(store):
    _, control = store
    with pytest.raises(TaskStoreError, match="host_atomic_admission_invalid"):
        control.activate_window(_payload(), confirmation="ACTIVATE", _host_sql_admit="forged")
    with pytest.raises(TaskStoreError, match="host_atomic_admission_invalid"):
        control.activate_window(_payload(), confirmation="ACTIVATE",
                                _host_sql_admit=lambda _: None, _trusted_binding={"any": "binding"})
    assert control.list_windows() == ()


def test_callback_cannot_reactivate_existing_window(store):
    _, control = store
    data = _payload()
    original = control.activate_window(data, confirmation="ACTIVATE")
    control.stop_window(original.id)
    with pytest.raises(TaskStoreError, match="host_atomic_admission_replay"):
        control.activate_window(data, confirmation="ACTIVATE",
                                _host_expected_goal_id="selected-goal", _host_sql_admit=lambda _: None)
    assert control.get_window(original.id).status == "STOPPED"


def test_two_hosts_cannot_both_admit_same_one_task_window(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import reverse_agent.platform_v1.goal_service as module

    path = tmp_path / "competing.sqlite3"
    stores = [TaskStore(str(path)) for _ in range(2)]
    controls = [PlatformControlStore(s) for s in stores]
    goals = [module.GoalService(store=s, control_store=c) for s, c in zip(stores, controls)]
    monkeypatch.setattr(module, "resolve_repository_workspace",
                        lambda repository: SimpleNamespace(repository=repository, repo_dir=tmp_path))
    monkeypatch.setattr(module, "repository_base", lambda repository: "a" * 40)
    planned = []
    for index in range(2):
        goal = goals[index].create({
            "objective": f"Task {index}", "repository": "owner/repo",
            "idempotency_key": f"goal-{index}", "executor_kind": "codex",
            "binding_ref": "pinned", "orchestration_mode": "single",
        })
        planned.append(goals[index].plan(goal.id, expected_revision=goal.revision, tasks=[{
            "id": "ONE", "title": "one", "instruction": "read",
        }]).goal)
    barrier = Barrier(2)

    def attempt(index):
        barrier.wait(timeout=5)
        goal = planned[index]
        def admit(window_id):
            controls[index].approve_goal(goal.id, expected_revision=goal.revision)
            goals[index]._launch(goal.id, expected_revision=goal.revision, window_id=window_id)
        try:
            return controls[index].activate_window(
                {**_payload(f"distinct-{index}"), "repositories": [goal.repository]},
                confirmation="ACTIVATE", _host_expected_goal_id=goal.id,
                _host_sql_admit=admit)
        except TaskStoreError as exc:
            return exc
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, [0, 1]))
        assert sum(not isinstance(item, Exception) for item in results) == 1
        assert sum(isinstance(item, TaskStoreError)
                   and "active_window_already_exists" in str(item) for item in results) == 1
        assert len(controls[0].list_windows()) == 1
        assert sum(controls[0].get_goal(g.id).status == "RUNNING" for g in planned) == 1
        assert stores[0]._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
    finally:
        for s in stores:
            s._conn.close()


def _planned_goal(db, control, monkeypatch):
    from types import SimpleNamespace
    import reverse_agent.platform_v1.goal_service as module

    goals = module.GoalService(store=db, control_store=control)
    goal = goals.create({
        "objective": "One bounded fixture",
        "repository": "owner/repo",
        "idempotency_key": "one",
        "executor_kind": "codex",
        "binding_ref": "pinned",
        "orchestration_mode": "single",
    })
    goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[{
        "id": "ONE", "title": "One safe task", "instruction": "Read one file",
    }]).goal
    monkeypatch.setattr(module, "resolve_repository_workspace",
                        lambda repository: SimpleNamespace(repository=repository, repo_dir="/fixture"))
    monkeypatch.setattr(module, "repository_base", lambda repository: "a" * 40)
    return goals, goal


@pytest.mark.parametrize("fail_after_launch", [False, True])
def test_host_callback_atomically_binds_one_goal_and_one_task(
    store, monkeypatch, fail_after_launch,
):
    db, control = store
    goals, planned = _planned_goal(db, control, monkeypatch)
    data = {**_payload("selected-goal"), "repositories": [planned.repository]}
    window_id = None

    def admit(created):
        nonlocal window_id
        window_id = created
        assert control.get_goal(planned.id) == planned  # persisted snapshot before approval
        control.approve_goal(planned.id, expected_revision=planned.revision,
                             policy_ref=data["policy_id"])
        goals._launch(planned.id, expected_revision=planned.revision, window_id=created)
        if fail_after_launch:
            raise TaskStoreError("injected_after_materialization")

    if fail_after_launch:
        with pytest.raises(TaskStoreError, match="injected_after_materialization"):
            control.activate_window(data, confirmation="ACTIVATE",
                                    _host_expected_goal_id=planned.id, _host_sql_admit=admit)
        assert control.list_windows() == ()
        assert control.get_goal(planned.id) == planned
        assert control.list_goal_tasks(planned.id) == ()
        assert db._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
    else:
        window = control.activate_window(data, confirmation="ACTIVATE",
                                         _host_expected_goal_id=planned.id, _host_sql_admit=admit)
        assert window.id == window_id
        current = control.get_goal(planned.id)
        links = control.list_goal_tasks(planned.id)
        assert current.status == "RUNNING" and current.window_id == window.id
        assert len(links) == 1 and links[0]["status"] == "QUEUED"
        assert control.is_strict_owner_window(window)
        control.check_strict_task_admission(window.id, links[0]["task_id"])


def test_empty_host_callback_cannot_leave_an_active_window(store):
    _, control = store
    with pytest.raises(TaskStoreError, match="host_atomic_goal_binding_missing"):
        control.activate_window(_payload(), confirmation="ACTIVATE",
                                _host_expected_goal_id="persisted-goal", _host_sql_admit=lambda _: None)
    assert control.list_windows() == ()


@pytest.mark.parametrize("change", [
    {"max_tasks": 2}, {"max_concurrent_tasks": 2}, {"max_retries": 1},
    {"capabilities": ["execute_task", "approve_goal"]},
    {"repositories": ["owner/a", "owner/b"]},
])
def test_atomic_hook_rejects_broad_window_scope(store, change):
    _, control = store
    with pytest.raises(TaskStoreError, match="host_atomic_window_scope_invalid"):
        control.activate_window({**_payload(), **change}, confirmation="ACTIVATE",
                                _host_expected_goal_id="persisted-goal", _host_sql_admit=lambda _: None)
    assert control.list_windows() == ()


@pytest.mark.parametrize("delta", [timedelta(minutes=31), timedelta(seconds=-1)])
def test_atomic_hook_rejects_wide_or_expired_window(store, delta):
    _, control = store
    now = datetime.now(timezone.utc)
    data = {**_payload(), "expires_at": (now + delta).isoformat()}
    with pytest.raises(TaskStoreError, match="host_atomic_window_time_invalid"):
        control.activate_window(data, confirmation="ACTIVATE",
                                _host_expected_goal_id="persisted-goal", _host_sql_admit=lambda _: None)
    assert control.list_windows() == ()


def test_host_interrupt_rolls_back_and_connection_recovers(store):
    db, control = store
    def interrupted(window_id):
        db._conn.execute("CREATE TABLE IF NOT EXISTS transient (id TEXT)")
        db._conn.execute("INSERT INTO transient VALUES (?)", (window_id,))
        raise KeyboardInterrupt("host interrupted")

    with pytest.raises(KeyboardInterrupt, match="host interrupted"):
        control.activate_window(_payload(), confirmation="ACTIVATE",
                                _host_expected_goal_id="persisted-goal", _host_sql_admit=interrupted)
    assert not db._conn.in_transaction
    assert control.list_windows() == ()
    assert db._conn.execute("SELECT name FROM sqlite_master WHERE name='transient'").fetchone() is None


@pytest.mark.parametrize("overrides", [
    {"starts_at": "2026-W42-7T00:00:00Z"},
    {"expires_at": "2026-W42-7T23:00:00+00:00"},
    {"starts_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "+23:00")},
    {"expires_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "-23:00")},
])
def test_host_window_rejects_python_only_calendar_formats(store, overrides):
    _, control = store
    with pytest.raises(TaskStoreError, match="host_atomic_window_time_invalid"):
        control.activate_window({**_payload(), **overrides}, confirmation="ACTIVATE",
                                _host_expected_goal_id="persisted-goal", _host_sql_admit=lambda _: None)
    assert control.list_windows() == ()


@pytest.mark.parametrize("illegal", ["commit", "rollback", "executescript"])
def test_host_callback_cannot_commit_or_rollback_behind_store(store, illegal):
    db, control = store
    def escape_transaction(window_id):
        db._conn.execute("CREATE TABLE IF NOT EXISTS test_escape (window_id TEXT)")
        db._conn.execute("INSERT INTO test_escape VALUES (?)", (window_id,))
        if illegal == "commit":
            db._conn.commit()
        elif illegal == "rollback":
            db._conn.rollback()
        else:
            db._conn.executescript("INSERT INTO test_escape VALUES ('unexpected')")

    with pytest.raises(TaskStoreError, match="window_activation_failed"):
        control.activate_window(_payload(), confirmation="ACTIVATE",
                                _host_expected_goal_id="persisted-goal",
                                _host_sql_admit=escape_transaction)
    assert not db._conn.in_transaction
    assert control.list_windows() == ()
    assert db._conn.execute("SELECT name FROM sqlite_master WHERE name='test_escape'").fetchone() is None


def test_host_callback_expiring_before_commit_rolls_back_all_writes(store):
    import time
    db, control = store
    now = datetime.now(timezone.utc)
    data = {**_payload(), "expires_at": (now + timedelta(milliseconds=180)).isoformat()}
    def slow(window_id):
        db._conn.execute("CREATE TABLE IF NOT EXISTS test_slow (window_id TEXT)")
        db._conn.execute("INSERT INTO test_slow VALUES (?)", (window_id,))
        time.sleep(0.3)
    with pytest.raises(TaskStoreError, match="host_atomic_window_expired"):
        control.activate_window(data, confirmation="ACTIVATE",
                                _host_expected_goal_id="persisted-goal", _host_sql_admit=slow)
    assert not db._conn.in_transaction
    assert control.list_windows() == ()
    assert db._conn.execute("SELECT name FROM sqlite_master WHERE name='test_slow'").fetchone() is None

def test_callback_expiry_after_valid_goal_and_task_materialization(store, monkeypatch):
    import time
    db, control = store
    goals, planned = _planned_goal(db, control, monkeypatch)
    now = datetime.now(timezone.utc)
    data = {**_payload(), "repositories": [planned.repository],
            "expires_at": (now + timedelta(milliseconds=180)).isoformat()}

    def slow_admission(window_id):
        control.approve_goal(planned.id, expected_revision=planned.revision)
        goals._launch(planned.id, expected_revision=planned.revision, window_id=window_id)
        time.sleep(0.25)

    with pytest.raises(TaskStoreError, match="host_atomic_window_expired"):
        control.activate_window(data, confirmation="ACTIVATE",
                                _host_expected_goal_id=planned.id,
                                _host_sql_admit=slow_admission)
    assert not db._conn.in_transaction
    assert control.list_windows() == ()
    assert control.get_goal(planned.id) == planned
    assert control.list_goal_tasks(planned.id) == ()
    assert db._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0


def test_implicit_rollback_in_callback_cannot_escape_to_autocommit(store):
    import sqlite3
    db, control = store

    def implicit_rollback(window_id):
        db._conn.execute("CREATE TABLE rollback_probe (value TEXT)")
        db._conn.execute(
            "CREATE TRIGGER rollback_trigger BEFORE INSERT ON rollback_probe "
            "BEGIN SELECT RAISE(ROLLBACK, 'rollback_requested'); END")
        try:
            db._conn.execute("INSERT INTO rollback_probe VALUES (?)", (window_id,))
        except sqlite3.DatabaseError:
            pass  # An unsafe callback could suppress the SQLite error.
        # This MUST fail; a previous SQLite implicit ROLLBACK must never
        # permit subsequent autocommitted writes in the same callback.
        db._conn.execute("CREATE TABLE must_not_survive (value TEXT)")

    with pytest.raises((TaskStoreError, sqlite3.DatabaseError)):
        control.activate_window(_payload(), confirmation="ACTIVATE",
                                _host_expected_goal_id="selected-goal",
                                _host_sql_admit=implicit_rollback)
    assert not db._conn.in_transaction
    assert control.list_windows() == ()
    assert db._conn.execute(
        "SELECT name FROM sqlite_master WHERE name='must_not_survive'").fetchone() is None
    assert db._conn.execute(
        "SELECT name FROM sqlite_master WHERE name='rollback_probe'").fetchone() is None

def test_host_window_expiring_while_waiting_for_sqlite_lock_denies(tmp_path):
    import sqlite3
    import time

    db_path = str(tmp_path / "lock-expire.sqlite3")
    db = TaskStore(db_path)
    control = PlatformControlStore(db)
    competing = sqlite3.connect(db_path, timeout=5)
    competing.execute("BEGIN IMMEDIATE")
    now = datetime.now(timezone.utc)
    data = {**_payload(), "expires_at": (now + timedelta(milliseconds=180)).isoformat()}

    def wait_then_try():
        try:
            control.activate_window(data, confirmation="ACTIVATE",
                                    _host_expected_goal_id="selected-goal",
                                    _host_sql_admit=lambda _: pytest.fail("expired window callback invoked"))
        except TaskStoreError as exc:
            return str(exc)
        return "unexpected_success"

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            attempted = pool.submit(wait_then_try)
            time.sleep(0.3)
            competing.commit()
            assert "host_atomic_window_expired" in attempted.result(timeout=6)
        assert control.list_windows() == ()
        assert not db._conn.in_transaction
    finally:
        competing.rollback()
        competing.close()
        db._conn.close()


def test_expired_committed_window_cannot_claim_a_queued_task(store, monkeypatch):
    import time

    db, control = store
    goals, planned = _planned_goal(db, control, monkeypatch)
    data = {**_payload(), "repositories": [planned.repository],
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()}

    def admit(window_id):
        control.approve_goal(planned.id, expected_revision=planned.revision)
        goals._launch(planned.id, expected_revision=planned.revision, window_id=window_id)

    window = control.activate_window(data, confirmation="ACTIVATE",
                                     _host_expected_goal_id=planned.id, _host_sql_admit=admit)
    links = control.list_goal_tasks(planned.id)
    assert len(links) == 1 and links[0]["status"] == "QUEUED"

    time.sleep(1.1)
    assert control.active_window() is None
    with pytest.raises(TaskStoreError, match="window_not_active|window_expired"):
        control.claim_task(window_id=window.id, task_id=links[0]["task_id"],
                           owner="test-worker", lease_ms=5000)
    assert db._conn.execute(
        "SELECT COUNT(*) FROM platform_coordinator_claims WHERE window_id = ?",
        (window.id,),
    ).fetchone()[0] == 0
    assert db._conn.execute(
        "SELECT COUNT(*) FROM platform_budget_reservations WHERE window_id = ?",
        (window.id,),
    ).fetchone()[0] == 0
