"""Fault injection: lease invariants (C3 I1/I2, F1/F2 partial).

`C3_LEASE_RECOVERY_PROJECT.md` requires every gap to be *reproduced* before it is
fixed. This suite is that reproduction harness for the part that needs no
production change: the durable lease's fencing token and recovery protocol,
exercised directly against `TaskStore`.

What is asserted here (and already true today):

* I1 single writer — a run belongs to exactly one ``(owner, epoch)``;
* I2 monotonic   — recovery advances the epoch and never reuses it;
* F1 (db part)   — the superseded owner's writes are refused after recovery;
* F2 (guard)     — a live lease cannot be "recovered" into a second writer.

What is *not* covered, and is marked with a strict ``xfail`` so it fails loudly
once fixed: fencing of the **workspace** (files on disk). The token currently
guards database rows only; a stale executor that wakes up can still write to its
worktree. That is the headline item of the C3 project, deliberately not fixed
here.
"""
from __future__ import annotations

import pytest

from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def _store() -> TaskStore:
    return TaskStore(":memory:")


def _queued_task(store: TaskStore, **overrides):
    defaults = dict(title="lease fixture", executor_kind="opencode", binding_ref="b",
                    repository="o/r", orchestration_mode="single",
                    model_profile_ref="p", permission_profile="ASK_FOR_APPROVAL",
                    policy_ref="", workspace="", branch="")
    defaults.update(overrides)
    if "orchestration_mode" not in overrides:
        # create_task defaults to single already; keep the fixture explicit.
        defaults["orchestration_mode"] = "single"
    return store.create_task(**defaults)


def _acquire(store: TaskStore, task, owner: str = "owner-A", *, expiry_ms: int = 600_000,
             task_status: str | None = "QUEUED"):
    return store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id, lease_owner=owner,
        expiry_ms=expiry_ms, task_status=task_status)


def _make_recoverable(store: TaskStore, run_id: str, *, task_id: str) -> None:
    """Simulate a crash: task INTERRUPTED, stale lease, recoverable classification."""
    store._conn.execute(
        "UPDATE tasks SET status='INTERRUPTED' WHERE id=?", (task_id,))
    store._conn.execute(
        "UPDATE durable_runs SET recovery_classification='interrupted', "
        "lease_expiry_ms=1 WHERE run_id=?", (run_id,))
    store._conn.commit()


def test_first_claim_owns_the_run_and_the_token_verifies():
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task)
    assert lease.epoch == 1 and lease.owner == "owner-A"

    store._validate_durable_lease(lease.run_id, "owner-A", 1)  # no raise
    assert store.get_task(task.id).status == "PREPARING_WORKSPACE"


def test_a_second_claim_on_the_same_task_is_refused():
    store = _store()
    task = _queued_task(store)
    _acquire(store, task)
    # The second claimant does not assert a status; it must still be refused
    # because the run already exists (no task_status override to hide behind).
    with pytest.raises(TaskStoreError) as error:
        _acquire(store, task, "owner-B", task_status=None)
    assert "durable_run_already_active" in str(error.value)


def test_recovery_advances_the_epoch_and_fences_the_old_owner():
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A")
    _make_recoverable(store, lease.run_id, task_id=task.id)

    recovered = store._recover_durable_lease(lease.run_id, "owner-B", require_interrupted=True)
    assert recovered.epoch == lease.epoch + 1, "I2: the token must move forward, never reset"
    assert recovered.owner == "owner-B"

    store._validate_durable_lease(lease.run_id, "owner-B", recovered.epoch)  # current owner works
    with pytest.raises(TaskStoreError) as stale:
        store._validate_durable_lease(lease.run_id, "owner-A", lease.epoch)
    assert "lease_fenced" in str(stale.value), "I1: the superseded writer must be refused"


def test_a_stale_owner_cannot_persist_evidence_after_recovery():
    """F1 (database half): the old writer's fenced write must fail, not overwrite."""
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A")
    _make_recoverable(store, lease.run_id, task_id=task.id)
    recovered = store._recover_durable_lease(lease.run_id, "owner-B", require_interrupted=True)

    store._fenced_add_evidence(
        lease.run_id, task.id, category="test", label="from-new-owner", value="ok",
        status="ACCEPTED", owner="owner-B", epoch=recovered.epoch)

    with pytest.raises(TaskStoreError) as stale:
        store._fenced_add_evidence(
            lease.run_id, task.id, category="test", label="from-old-owner", value="stale",
            status="ACCEPTED", owner="owner-A", epoch=lease.epoch)
    assert "fenced" in str(stale.value).lower()

    labels = [entry.get("label") for entry in store.get_task(task.id).evidence_refs]
    assert "from-new-owner" in labels and "from-old-owner" not in labels


def test_a_live_lease_cannot_be_recovered_into_a_second_writer():
    """F2 guard: recover() must refuse while the task is not INTERRUPTED."""
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A")
    # The lease row still says 'normal' and the task is PREPARING_WORKSPACE:
    # exactly the state of an executor that is alive but briefly unreachable.
    with pytest.raises(TaskStoreError) as error:
        store._recover_durable_lease(lease.run_id, "owner-B", require_interrupted=True)
    assert "durable_recover_wrong_task_status" in str(error.value)
    store._validate_durable_lease(lease.run_id, "owner-A", lease.epoch)  # owner-A keeps the run


def test_recovery_cannot_run_twice_for_the_same_crash():
    """Two rescuers must not both win: the second sees a non-INTERRUPTED task."""
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A")
    _make_recoverable(store, lease.run_id, task_id=task.id)

    first = store._recover_durable_lease(lease.run_id, "owner-B", require_interrupted=True)
    with pytest.raises(TaskStoreError):
        store._recover_durable_lease(lease.run_id, "owner-C", require_interrupted=True)
    store._validate_durable_lease(lease.run_id, "owner-B", first.epoch)


# (The wiring placeholder is gone: `test_service_helper_publishes_and_checks_the_workspace_token`
# below now exercises the real publish/verify path through the service.)


# --- I3 checkpoint monotonicity / I5 no heartbeat after sleep --------------------

def test_checkpoint_sequence_cannot_regress_or_skip():
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A")

    store._accept_checkpoint(lease.run_id, "PRE_PLANNER", "digest-0", 1, "owner-A", lease.epoch)
    store._accept_checkpoint(lease.run_id, "POST_PLANNER", "digest-1", 1, "owner-A", lease.epoch)

    with pytest.raises(TaskStoreError) as regression:
        store._accept_checkpoint(lease.run_id, "PRE_PLANNER", "digest-0", 1, "owner-A", lease.epoch)
    assert "checkpoint_sequence_regression" in str(regression.value)

    with pytest.raises(TaskStoreError) as skip:
        store._accept_checkpoint(lease.run_id, "POST_REVIEWER", "digest-3", 1, "owner-A", lease.epoch)
    assert "checkpoint" in str(skip.value)  # skipping POST_CODER is refused


def test_checkpoint_acceptance_is_fenced_and_idempotent():
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A")
    store._accept_checkpoint(lease.run_id, "PRE_PLANNER", "digest-0", 1, "owner-A", lease.epoch)

    # Same checkpoint, same digest: idempotent, no duplicate history row.
    store._accept_checkpoint(lease.run_id, "PRE_PLANNER", "digest-0", 1, "owner-A", lease.epoch)
    history = store._get_durable_checkpoints(lease.run_id)
    assert len([row for row in history if row.checkpoint_name == "PRE_PLANNER"]) == 1

    with pytest.raises(TaskStoreError) as stale:
        store._accept_checkpoint(lease.run_id, "POST_PLANNER", "digest-1", 1, "owner-B", lease.epoch)
    assert "lease_fenced" in str(stale.value)


def test_a_lease_that_slept_past_its_expiry_cannot_be_heartbeated_back():
    """I5: the sleep itself is not the bug — silently resuming as owner would be.

    A host that hibernates sends no heartbeats. By the time it wakes, another
    owner may have recovered the run; its heartbeat must then be fenced instead
    of quietly extending a lease it no longer holds.
    """
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A", expiry_ms=1_000)  # expires almost at once
    _make_recoverable(store, lease.run_id, task_id=task.id)
    recovered = store._recover_durable_lease(lease.run_id, "owner-B", require_interrupted=True)

    with pytest.raises(TaskStoreError) as fenced:
        store._heartbeat_durable_lease(lease.run_id, "owner-A", lease.epoch, 600_000)
    assert "lease_fenced" in str(fenced.value)

    # The owner that actually holds the run can still extend it.
    store._heartbeat_durable_lease(lease.run_id, "owner-B", recovered.epoch, 600_000)
    store._validate_durable_lease(lease.run_id, "owner-B", recovered.epoch)


# --- workspace token (C3 F1, filesystem half) -----------------------------------

from reverse_agent.platform_v1.workspace_fence import (  # noqa: E402
    TOKEN_NAME, LeaseToken, WorkspaceFenced, publish_token, read_token,
    verify_token, workspace_fence_enabled,
)


def test_workspace_token_is_published_atomically_and_read_back(tmp_path):
    token = LeaseToken(run_id="run-1", owner="owner-A", epoch=3)
    publish_token(tmp_path, token)
    assert (tmp_path / TOKEN_NAME).exists()
    assert read_token(tmp_path) == token
    # No temp files left behind, and the payload is self-describing.
    assert [item.name for item in tmp_path.iterdir() if item.suffix == ".tmp"] == []
    import json
    payload = json.loads((tmp_path / TOKEN_NAME).read_text(encoding="utf-8"))
    assert payload == {"version": 1, "run_id": "run-1", "owner": "owner-A", "epoch": 3}


def test_a_superseded_writer_is_refused_by_the_workspace_token(tmp_path):
    """F1 (filesystem half): the old epoch cannot claim a worktree the new one owns."""
    publish_token(tmp_path, LeaseToken(run_id="run-1", owner="owner-B", epoch=2))
    with pytest.raises(WorkspaceFenced) as fenced:
        verify_token(tmp_path, LeaseToken(run_id="run-1", owner="owner-A", epoch=1))
    assert "workspace_fenced" in str(fenced.value)
    assert "owner-A" in str(fenced.value) and "epoch=1" in str(fenced.value)


def test_current_owner_verifies_and_missing_tokens_are_adopted(tmp_path):
    token = LeaseToken(run_id="run-1", owner="owner-A", epoch=1)
    assert verify_token(tmp_path, token) == token          # adopted on first use
    assert read_token(tmp_path) == token                    # and persisted
    assert verify_token(tmp_path, token) == token           # stable afterwards

    with pytest.raises(WorkspaceFenced) as strict:
        verify_token(tmp_path / "elsewhere", token, adopt_missing=False)
    assert "workspace_token_missing" in str(strict.value)


def test_a_corrupt_token_is_treated_as_unowned_not_trusted(tmp_path):
    (tmp_path / TOKEN_NAME).write_text("{not json", encoding="utf-8")
    assert read_token(tmp_path) is None
    token = LeaseToken(run_id="run-1", owner="owner-C", epoch=4)
    assert verify_token(tmp_path, token) == token  # adopted, then overwritten atomically
    assert read_token(tmp_path) == token


def test_token_parsing_rejects_incomplete_payloads():
    assert LeaseToken.parse({}) is None
    assert LeaseToken.parse({"run_id": "", "owner": "o", "epoch": 1}) is None
    assert LeaseToken.parse({"run_id": "r", "owner": "", "epoch": 1}) is None
    assert LeaseToken.parse({"run_id": "r", "owner": "o", "epoch": -1}) is None
    assert LeaseToken.parse({"run_id": "r", "owner": "o", "epoch": "1"}) is None
    assert LeaseToken.parse({"run_id": "r", "owner": "o", "epoch": 2, "version": 9}).version == 9


def test_the_fence_is_off_unless_explicitly_enabled():
    assert workspace_fence_enabled({}) is False
    assert workspace_fence_enabled({"REVERSE_AGENT_WORKSPACE_FENCE": "0"}) is False
    assert workspace_fence_enabled({"REVERSE_AGENT_WORKSPACE_FENCE": "1"}) is True


# --- component probe: no production execution/recovery coverage ---

def _service(store):
    from reverse_agent.platform_v1.durable_execution import DurableExecutionService
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter
    return DurableExecutionService(store=store, router=ExecutorRouter(),
                                   execution_authority_sha="test_authority",
                                   planning_sha="test_planning")


def test_service_helper_publishes_and_checks_the_workspace_token(tmp_path, monkeypatch):
    """C3 W1/W2: the run claims its worktree, and a superseded lease is refused.

    Exercised through the component helper, not a production call site, with the flag
    on; the same helper is a no-op with the flag off (next test).
    """
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A")
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    service = _service(store)

    monkeypatch.setenv("REVERSE_AGENT_WORKSPACE_FENCE", "1")
    service._fence_workspace(worktree, lease)                       # W1: publish
    assert read_token(worktree) == LeaseToken(lease.run_id, "owner-A", 1)
    service._fence_workspace(worktree, lease, verify_only=True)     # W2: verify

    # A newer epoch recovers the run and takes the worktree.
    _make_recoverable(store, lease.run_id, task_id=task.id)
    recovered = store._recover_durable_lease(lease.run_id, "owner-B", require_interrupted=True)
    service._fence_workspace(worktree, recovered)                   # W3: new owner claims

    from reverse_agent.platform_v1.task_execution import TaskExecutionError
    with pytest.raises(TaskExecutionError) as fenced:
        service._fence_workspace(worktree, lease, verify_only=True)
    assert "workspace_fenced" in str(fenced.value)
    assert read_token(worktree).owner == "owner-B"  # the worktree stayed with the winner


def test_fencing_is_a_no_op_when_disabled(tmp_path, monkeypatch):
    """Default off: no token is written, so behaviour is byte-identical."""
    monkeypatch.delenv("REVERSE_AGENT_WORKSPACE_FENCE", raising=False)
    store = _store()
    task = _queued_task(store)
    lease = _acquire(store, task, "owner-A")
    worktree = tmp_path / "worktree"
    worktree.mkdir()

    _service(store)._fence_workspace(worktree, lease)
    assert read_token(worktree) is None
    assert list(worktree.iterdir()) == []
