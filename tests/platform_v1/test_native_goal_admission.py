"""Provider-free native admission regressions. No server, model or dispatch."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from threading import Barrier, Event
from types import SimpleNamespace

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1 import native_goal_admission as native
from reverse_agent.platform_v1 import goal_service
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


@pytest.fixture
def setup(tmp_path, monkeypatch):
    owner = native.native_owner_identity.InteractiveOwner("S-1-5-21-fixture", 3)
    monkeypatch.setattr(native.native_owner_identity, "interactive_owner", lambda: owner)
    models = ModelProfileStore()
    models.upsert_connection({"connection_id": "native", "name": "Fixture",
        "provider": "codex", "base_url": "https://chatgpt.com",
        "auth_method": "external_cli_session", "enabled": True})
    models.upsert_binding({"binding_id": "pinned", "name": "Pinned", "connection_id": "native",
        "executor_id": "codex", "model_id": "gpt-test", "enabled": True})
    db = TaskStore(str(tmp_path / "admission.sqlite"))
    host = CombinedTrustedHost(task_store=db, store=models, vault=None)
    goals = host._goal_service
    goal = goals.create({"objective": "Bounded fixture", "repository": "owner/repo",
        "idempotency_key": "one", "executor_kind": "codex", "binding_ref": "pinned",
        "orchestration_mode": "single"})
    goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[{
        "id": "ONE", "title": "One task", "instruction": "Read the complete fixture"}]).goal
    workspace = SimpleNamespace(repository=goal.repository, repo_dir=tmp_path.resolve())
    monkeypatch.setattr(native, "resolve_repository_workspace", lambda _: workspace)
    monkeypatch.setattr(native, "repository_base", lambda _: "a" * 40)
    monkeypatch.setattr(goal_service, "resolve_repository_workspace", lambda _: workspace)
    monkeypatch.setattr(goal_service, "repository_base", lambda _: "a" * 40)
    seen = []
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission",
                        lambda scope: seen.append(scope.text(admission=True)) or True)
    yield host, goal, seen
    db._conn.close()


def unchanged(host, goal):
    assert host._control_store.get_goal(goal.id) == goal
    assert host._control_store.list_windows() == ()
    for table in ("tasks", "platform_operation_receipts", "platform_goal_task_links"):
        assert host._task_store._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    assert host._native_goal_admission._nonce is None
    assert not host._task_store._conn.in_transaction


def test_success_exact_scope_and_atomic_receipt(setup):
    host, goal, seen = setup
    window = host._native_owner_admit_goal(goal.id)
    assert window.max_tasks == 1 and window.max_concurrent_tasks == 1 and window.max_retries == 0
    from datetime import datetime
    assert (datetime.fromisoformat(window.expires_at) - datetime.fromisoformat(window.starts_at)).total_seconds() == 1800
    control = host._control_store
    assert control.get_goal(goal.id).status == "RUNNING"
    links = control.list_goal_tasks(goal.id)
    assert len(links) == 1 and links[0]["status"] == "QUEUED"
    task = host._task_store.get_task(links[0]["task_id"])
    assert task.binding_ref == goal.binding_ref and task.branch == "a" * 40
    assert task.permission_profile == "AUTONOMOUS_WINDOW"
    row = host._task_store._conn.execute("SELECT * FROM platform_operation_receipts").fetchone()
    proof = json.loads(row["evidence_json"])
    assert proof["base_sha"] == task.branch and proof["owner"]["session_id"] == 3
    assert row["confirmation_mode"] == "NATIVE_OWNER"
    assert control.get_window(window.id).confirmation_mode == "NATIVE_OWNER"
    for text in (goal.tasks[0]["instruction"], goal.binding_ref, goal.repository, "a" * 40,
                 proof["workspace"].replace("\\", "\\\\"), '"max_tasks":1', '"max_retries":0'):
        assert text in seen[0]
    assert host._native_goal_admission._nonce is None
    with pytest.raises(TaskStoreError):
        host._native_owner_admit_goal(goal.id)
    assert host._task_store._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1


@pytest.mark.parametrize("field", ["objective", "revision", "tasks", "binding_ref", "repository"])
def test_goal_change_during_consent(setup, monkeypatch, field):
    host, goal, _ = setup
    control = host._control_store
    original = control.get_goal
    def consent(_):
        value = {"objective": "changed", "revision": goal.revision + 1,
                 "tasks": ({**goal.tasks[0], "instruction": "substituted"},),
                 "binding_ref": "different", "repository": "other/repo"}[field]
        monkeypatch.setattr(control, "get_goal", lambda _: replace(goal, **{field: value}))
        return True
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", consent)
    with pytest.raises((TaskStoreError, KeyError)):
        host._native_owner_admit_goal(goal.id)
    monkeypatch.setattr(control, "get_goal", original)
    unchanged(host, goal)


@pytest.mark.parametrize("change", ["binding", "workspace", "base", "identity", "goal"])
@pytest.mark.parametrize("point", ["dialog", "sql", "after_launch"])
def test_scope_changes_at_every_boundary(setup, monkeypatch, change, point):
    host, goal, _ = setup
    def mutate():
        if change == "binding":
            original = host._store.get_binding_public
            monkeypatch.setattr(host._store, "get_binding_public",
                                lambda ref: {**original(ref), "model_id": "substituted"})
        elif change == "workspace":
            monkeypatch.setattr(native, "resolve_repository_workspace",
                lambda _: SimpleNamespace(repository=goal.repository, repo_dir="different"))
        elif change == "base":
            monkeypatch.setattr(native, "repository_base", lambda _: "b" * 40)
        elif change == "identity":
            monkeypatch.setattr(native.native_owner_identity, "interactive_owner", lambda: None)
        else:
            host._task_store._conn.execute("UPDATE platform_goals SET objective = 'substituted' WHERE id = ?", (goal.id,))
    if point == "dialog":
        monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", lambda _: mutate() or True)
    elif point == "sql":
        original = host._control_store.activate_window
        def activation(*args, **kwargs):
            callback = kwargs["_host_sql_admit"]
            def wrapped(window_id):
                assert host._task_store._conn.in_transaction
                mutate()
                callback(window_id)
            return original(*args, **{**kwargs, "_host_sql_admit": wrapped})
        monkeypatch.setattr(host._control_store, "activate_window", activation)
    else:
        original = host._goal_service._launch
        def launch(*args, **kwargs):
            result = original(*args, **kwargs)
            mutate()
            return result
        monkeypatch.setattr(host._goal_service, "_launch", launch)
    with pytest.raises(TaskStoreError):
        host._native_owner_admit_goal(goal.id)
    if point == "dialog" and change == "goal":
        # An unrelated writer's pretransaction change must be preserved.
        assert host._control_store.get_goal(goal.id).objective == "substituted"
        goal = host._control_store.get_goal(goal.id)
    unchanged(host, goal)


@pytest.mark.parametrize("mode", ["refusal", "exception", "expiry"])
def test_denial_burns_nonce(setup, monkeypatch, mode):
    host, goal, _ = setup
    now = [100.0]
    monkeypatch.setattr(native.time, "monotonic", lambda: now[0])
    def dialog(_):
        assert host._native_goal_admission._nonce is not None
        if mode == "exception":
            raise OSError("native helper unavailable")
        if mode == "expiry":
            now[0] += 30
        return mode != "refusal"
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", dialog)
    with pytest.raises((TaskStoreError, OSError)):
        host._native_owner_admit_goal(goal.id)
    unchanged(host, goal)


def test_receipt_failure_rolls_back_every_write(setup):
    host, goal, _ = setup
    host._task_store._conn.execute("CREATE TRIGGER reject_receipt BEFORE INSERT ON platform_operation_receipts "
                                 "BEGIN SELECT RAISE(ABORT, 'fixture receipt failure'); END")
    with pytest.raises(TaskStoreError, match="receipt_persistence_failed"):
        host._native_owner_admit_goal(goal.id)
    unchanged(host, goal)


def test_two_consumers_only_one_consent_and_admission(setup, monkeypatch):
    host, goal, _ = setup
    entered, release = Event(), Event()
    def consent(_):
        entered.set()
        assert release.wait(5)
        return True
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", consent)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(host._native_owner_admit_goal, goal.id)
        assert entered.wait(5)
        second = pool.submit(host._native_owner_admit_goal, goal.id)
        with pytest.raises(TaskStoreError, match="native_admission_in_progress"):
            second.result(timeout=5)
        release.set()
        assert first.result(timeout=5).status == "ACTIVE"
    assert host._task_store._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1


def test_missing_initial_owner_cannot_become_authorized(setup, monkeypatch):
    host, goal, _ = setup
    host._native_goal_admission._identity = None
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", lambda _: pytest.fail("prompted"))
    with pytest.raises(TaskStoreError, match="identity_unavailable"):
        host._native_owner_admit_goal(goal.id)
    unchanged(host, goal)


def test_expiry_after_materialization_rolls_back(setup, monkeypatch):
    host, goal, _ = setup
    now = [100.0]
    monkeypatch.setattr(native.time, "monotonic", lambda: now[0])
    launch = host._goal_service._launch
    def slow_launch(*args, **kwargs):
        result = launch(*args, **kwargs)
        now[0] += 30
        return result
    monkeypatch.setattr(host._goal_service, "_launch", slow_launch)
    with pytest.raises(TaskStoreError, match="consent_expired"):
        host._native_owner_admit_goal(goal.id)
    unchanged(host, goal)


def test_old_active_claims_remain_hold(setup, monkeypatch):
    host, goal, _ = setup
    db = host._task_store
    old = db.create_task(title="Old held task", executor_kind="deterministic_fixture")
    db._conn.execute("INSERT INTO platform_coordinator_claims VALUES (?, 'old-window', 'old-owner', 1, 1, 'ACTIVE', 'old', 'old')", (old.id,))
    previous = tuple(db._conn.execute("SELECT * FROM platform_coordinator_claims").fetchone())
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", lambda _: pytest.fail("prompted"))
    with pytest.raises(TaskStoreError, match="old_active_claims_hold"):
        host._native_owner_admit_goal(goal.id)
    assert tuple(db._conn.execute("SELECT * FROM platform_coordinator_claims").fetchone()) == previous
    assert host._control_store.get_goal(goal.id) == goal
    assert host._control_store.list_windows() == ()
    assert db.get_task(old.id) == old


def test_receipt_update_failure_rolls_back(setup):
    host, goal, _ = setup
    host._task_store._conn.execute("CREATE TRIGGER reject_proof BEFORE UPDATE ON platform_operation_receipts "
                                 "BEGIN SELECT RAISE(ABORT, 'fixture provenance failure'); END")
    with pytest.raises(TaskStoreError):
        host._native_owner_admit_goal(goal.id)
    unchanged(host, goal)


def test_two_host_instances_cannot_double_admit(setup, monkeypatch):
    host, goal, _ = setup
    second_db = TaskStore(host._task_store.db_path)
    other = CombinedTrustedHost(task_store=second_db, store=host._store, vault=None)
    barrier = Barrier(2)
    def consent(_):
        barrier.wait(timeout=5)
        return True
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", consent)
    def admit(candidate):
        try:
            return candidate._native_owner_admit_goal(goal.id)
        except TaskStoreError:
            return None
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(admit, (host, other)))
        assert sum(result is not None for result in results) == 1
        for table in ("tasks", "platform_operation_receipts", "platform_autonomous_windows"):
            assert host._task_store._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 1
    finally:
        second_db._conn.close()


def test_dispatch_binding_guard_fences_late_model_mutation(setup):
    """A consented queued Task cannot silently execute a later model ID."""
    from dataclasses import replace
    from reverse_agent.platform_v1.binding_resolver import CodexBindingResolution
    from reverse_agent.platform_v1.durable_execution import _require_native_owner_execution_binding
    from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError

    host, goal, _ = setup
    window = host._native_owner_admit_goal(goal.id)
    task_id = host._control_store.list_goal_tasks(goal.id)[0]["task_id"]
    task = host._task_store.get_task(task_id)
    assert task.policy_ref == window.policy_id
    row = host._task_store._conn.execute(
        "SELECT evidence_json FROM platform_operation_receipts "
        "WHERE operation_type = 'native_goal_admission'").fetchone()
    proof = json.loads(row["evidence_json"])
    pinned = proof["approved_binding"]
    good = CodexBindingResolution(
        **pinned, external_session_status="executor_managed", relay_required=False)
    _require_native_owner_execution_binding(host._task_store, task, good)
    with pytest.raises(ExecutorRuntimeError, match="native_owner_execution_binding_changed_or_missing"):
        _require_native_owner_execution_binding(
            host._task_store, task, replace(good, model_id="model-after"))
    with pytest.raises(ExecutorRuntimeError, match="native_owner_execution_binding_changed_or_missing"):
        _require_native_owner_execution_binding(
            host._task_store, task, replace(good, connection_id="other"))
    with pytest.raises(ExecutorRuntimeError, match="native_owner_execution_binding_changed_or_missing"):
        _require_native_owner_execution_binding(
            host._task_store, task, replace(good, base_url="https://other.example"))
    assert host._task_store.get_task(task_id).status == "QUEUED"


def test_dispatch_binding_guard_requires_authentic_single_receipt(setup):
    from reverse_agent.platform_v1.binding_resolver import CodexBindingResolution
    from reverse_agent.platform_v1.durable_execution import _require_native_owner_execution_binding
    from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError

    host, goal, _ = setup
    host._native_owner_admit_goal(goal.id)
    task_id = host._control_store.list_goal_tasks(goal.id)[0]["task_id"]
    task = host._task_store.get_task(task_id)
    proof = json.loads(host._task_store._conn.execute(
        "SELECT evidence_json FROM platform_operation_receipts "
        "WHERE operation_type='native_goal_admission'").fetchone()[0])
    good = CodexBindingResolution(**proof["approved_binding"],
                                   external_session_status="executor_managed", relay_required=False)
    host._task_store._conn.execute(
        "UPDATE platform_operation_receipts SET evidence_json = '{}' "
        "WHERE operation_type='native_goal_admission'")
    with pytest.raises(ExecutorRuntimeError, match="native_owner_execution_binding_changed_or_missing"):
        _require_native_owner_execution_binding(host._task_store, task, good)
    assert host._task_store.get_task(task_id).status == "QUEUED"
