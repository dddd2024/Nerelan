"""Fake native transports: no provider, network, login or dependency installation."""
import io
import json
import sqlite3
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import codex_executor as codex
from reverse_agent.platform_v1 import claude_executor as claude
from reverse_agent.platform_v1 import context_builder, durable_execution, functional_validation
from reverse_agent.platform_v1 import native_quota, opencode_executor, quota_inflight, run_store, task_runtime


@pytest.fixture
def native(tmp_path, monkeypatch, request):
    monkeypatch.setattr(run_store.time, "time", lambda: 1_800_000_000.0)
    store = run_store.TaskStore(str(tmp_path / "tasks.db"))
    request.addfinalizer(store._conn.close)
    task = store.create_task(title="Finish partial file and verify behavior", executor_kind="codex", binding_ref="fake-binding")
    root = tmp_path / task.id
    root.mkdir()
    (root / "existing.txt").write_bytes(b"preserve existing work")
    lease = store._acquire_durable_lease(task_id=task.id, execution_id=task.execution_id,
        lease_owner="host", worktree_path=str(root))
    snapshot = {"account_ref": "account", "attempt": "1", "reservation_id": task.id,
        "evidence": {"account_ref": "account", "source": "official", "observed_at": time.time(),
                     "windows": [{"window": w, "used_percent": 50, "resets_at": time.time()+3600}
                                 for w in ("five_hour", "weekly")]},
        "need": {"account_ref": "account", "estimate": {"model": "fake"},
                 "calibration": {"five_hour": 1, "weekly": 1},
                 "windows": {w: {"p80": 25} for w in ("five_hour", "weekly")}},
        "outstanding": [], "headroom": 10}
    monkeypatch.setattr(store, "native_quota_snapshot", lambda *a: snapshot)
    facade = durable_execution._DurableFencedExecutorStore(store, lease.run_id, task.id, "host", lease.epoch)
    monkeypatch.setattr(context_builder, "executor_context", lambda *a, **k: "")
    monkeypatch.setattr(codex, "_persist_usage_observations", lambda *a, **k: None)
    monkeypatch.setattr(codex, "_task_temp_env", lambda root, env: {})
    monkeypatch.setattr(quota_inflight.pricing, "equivalent_cost", lambda model, tokens: {"usd": tokens["input"]})
    monkeypatch.setattr(opencode_executor, "_collect_product_diff", lambda root: (
        {"path": "partial.txt", "content": (root / "partial.txt").read_text()},) if (root / "partial.txt").exists() else ())
    class Job:
        def attach_and_resume(self, proc):
            pass
        def close(self):
            pass
    monkeypatch.setattr(functional_validation, "_WindowsJob", Job)
    monkeypatch.setattr(functional_validation, "_terminate", lambda proc, job: proc.stop())
    state = SimpleNamespace(store=store, task=task, root=root, lease=lease, facade=facade,
                            snapshot=snapshot, stopped=False, confirm=True, save="ok", cooperative=False)
    def confirm(proc, job):
        assert state.quota.journal(None, None)["state"] == "REQUESTED"
        proc.stop()
        return state.confirm
    monkeypatch.setattr(native_quota, "stop_and_confirm", confirm)
    yield state


def execute(native, monkeypatch, kind):
    n = native
    if kind == "codex":
        events = [{"type": "token_count", "info": {"total_token_usage": {
            "input_tokens": value, "cached_input_tokens": 0, "output_tokens": 0}, "secret": "discard"}}
                  for value in (10, 41, 100)]
        cls = codex.CodexExecutor
    else:
        events = [{"type": "rate_limit_event", "rate_limit_info": {
            "status": "allowed_warning", "rateLimitType": "seven_day", "utilization": value,
            "secret": "discard"}} for value in (.6, .91, 1)]
        if getattr(n, "rejected", False):
            events = [{"type": "rate_limit_event", "rate_limit_info": {
                "status": "rejected", "rateLimitType": "seven_day", "utilization": 1}}]
        cls = claude.ClaudeCodeExecutor
    class Input(io.BytesIO):
        def write(self, data):
            (n.root / "partial.txt").write_bytes(b"unfinished prefix")
            n.written.set()
            return super().write(data)
    class Output(io.BytesIO):
        def read(self, size=-1):
            assert n.written.wait(3)
            return super().read(size)
        read1 = read
    class Process:
        supports_quota_checkpoint = n.cooperative
        def __init__(self, *a, **k):
            self.stdin = Input()
            self.stdout = Output(b"".join(json.dumps(e).encode()+b"\n" for e in events))
            self.stderr = io.BytesIO()
            self.returncode = None
            n.proc = self
        def stop(self):
            n.stopped = True
            self.returncode = -1
        def poll(self):
            return self.returncode
        def wait(self, **k):
            return self.returncode
        def request_quota_checkpoint(self, cp):
            assert not self.stdin.closed
            assert n.quota.journal(None, None)["state"] == "REQUESTED"
            if n.save == "raise":
                raise OSError("save failed")
            payload = n.quota.payload("Saved prefix", "Complete suffix and validate", "cooperative_agent")
            if n.save == "corrupt":
                payload["artifact_digest"] = "wrong"
            if n.save in {"wait_changed", "claim_changed", "baseline_changed"}:
                field = {"wait_changed": "quota_wait", "claim_changed": "reservation_claim",
                         "baseline_changed": "usage_before"}[n.save]
                payload[field] = {} if field != "usage_before" else ["forged"]
                proof = dict(payload)
                proof.pop("artifact_digest")
                payload["artifact_digest"] = native_quota.digest(proof)
            return payload
        def stop_quota_checkpoint(self, cp):
            return n.save != "stop_failed"
    n.written = threading.Event()
    executor = cls(model_id="fake", parent_env={}, process_factory=Process)
    monkeypatch.setattr(executor, "_verify_workspace", lambda *a: None)
    prepared = codex.CodexPreparedContext(n.root, "a"*40, n.task.execution_id, "fake.exe", kind)
    # Use the actual fenced facade/controller, wrapping creation only to expose it to the fake transport.
    original = durable_execution._DurableFencedExecutorStore.native_quota
    def create(self, task_id, prepared):
        n.quota = original(self, task_id, prepared)
        return n.quota
    monkeypatch.setattr(durable_execution._DurableFencedExecutorStore, "native_quota", create)
    return executor.execute_role_prepared(prepared, n.facade,
        role_context=opencode_executor.RoleContext("executor", n.task.id, n.root))


@pytest.mark.parametrize("kind", ["codex", "claude_code"])
def test_streaming_projection_request_before_next_limit_and_salvage(native, monkeypatch, kind):
    result = execute(native, monkeypatch, kind)
    assert not result.success and result.quota_pause["state"] == "PAUSED"
    assert result.failure_classification == "quota_paused"
    assert result.quota_pause["provenance"] == "host_salvaged"
    assert result.quota_pause["agent_acknowledged"] is False
    assert native.proc.stdin.closed and native.stopped
    signals = native.quota.signals()
    assert signals["sequences"][kind] == 1  # third frame would simulate exhaustion
    assert "discard" not in json.dumps(signals)
    row = native.quota.journal(None, None)
    payload = json.loads(row["payload_json"])
    assert native.quota.verify(payload)
    assert payload["summary"] and payload["remaining_work"]
    assert payload["resume_state"]["base_sha"] == "a"*40
    assert (native.root / "partial.txt").read_bytes() == b"unfinished prefix"
    assert (native.root / "existing.txt").read_bytes() == b"preserve existing work"
    run = native.store._get_durable_run(native.lease.run_id)
    assert run.partial_coder_diff_digest and not run.accepted_checkpoint
    native.store.interrupt_for_quota(native.lease.run_id, native.task.id, "host", native.lease.epoch, result.quota_pause)
    assert native.store.get_task(native.task.id).status == "QUOTA_WAIT"
    (native.root / "partial.txt").write_bytes(b"changed after save")
    assert not native.quota.verify(payload)


@pytest.mark.parametrize("kind", ["codex", "claude_code"])
def test_explicit_cooperative_transport_acknowledges_save_and_stop(native, monkeypatch, kind):
    native.cooperative = True
    result = execute(native, monkeypatch, kind)
    assert result.quota_pause["state"] == "PAUSED"
    assert result.quota_pause["agent_acknowledged"] is True
    assert result.quota_pause["provenance"] == "cooperative_agent"


@pytest.mark.parametrize("failure", ["raise", "corrupt", "stop_failed", "wait_changed", "claim_changed", "baseline_changed"])
def test_failed_cooperative_save_or_stop_is_never_pause(native, monkeypatch, failure):
    native.cooperative, native.save = True, failure
    result = execute(native, monkeypatch, "codex")
    assert not result.success
    assert result.quota_pause["state"] == "FAILED"
    assert native.quota.journal(None, None)["state"] == "FAILED"
    assert (native.root / "existing.txt").read_bytes() == b"preserve existing work"


def test_unconfirmed_descendants_never_saved(native, monkeypatch):
    native.confirm = False
    result = execute(native, monkeypatch, "claude_code")
    assert native.stopped  # parent termination alone is insufficient
    assert result.quota_pause["state"] == "FAILED"
    assert json.loads(native.quota.journal(None, None)["payload_json"]) == {}


def test_partial_write_during_verification_fails_closed(native, monkeypatch):
    original = native_quota.workspace_manifest
    count = 0
    def manifest(root):
        nonlocal count
        count += 1
        if count == 2:
            (root / "partial.txt").write_bytes(b"late descendant write")
        return original(root)
    monkeypatch.setattr(native_quota, "workspace_manifest", manifest)
    result = execute(native, monkeypatch, "codex")
    assert result.quota_pause["state"] == "FAILED"
    assert native.quota.journal(None, None)["state"] == "FAILED"
    assert (native.root / "partial.txt").read_bytes() == b"late descendant write"


@pytest.mark.parametrize("state", ["PAUSED", "FAILED"])
def test_durable_initial_dispatch_keeps_quota_outcome_and_milestones(native, monkeypatch, state):
    native.confirm = state == "PAUSED"
    raw = execute(native, monkeypatch, "codex")
    service = durable_execution.DurableExecutionService(store=native.store, router=task_runtime.ExecutorRouter())
    executor = SimpleNamespace(execute_role_prepared=lambda *a, **k: raw)
    prepared = SimpleNamespace(worktree=native.root)
    run = native.store._get_durable_run(native.lease.run_id)
    outcome = service._dispatch_opencode_durable_single(task_id=native.task.id, run=run,
        lease=native.lease, executor=executor, prepared=prepared, workspace_root=str(native.root.parent),
        idempotency_key="fake-native", request_digest="request")
    assert outcome.quota_pause["state"] == state
    assert outcome.success is False
    assert outcome.failure_classification == ("quota_paused" if state == "PAUSED" else "quota_checkpoint_failed")
    assert native.store.get_task(native.task.id).status == ("QUOTA_WAIT" if state == "PAUSED" else "INTERRUPTED")
    assert native.store._get_durable_run(run.run_id).accepted_checkpoint == ""


def test_real_quota_snapshot_reads_frozen_admission_and_other_reservations(native, monkeypatch):
    from reverse_agent.platform_v1 import control_store
    n = native
    control_store.PlatformControlStore(n.store)
    monkeypatch.delattr(n.store, "native_quota_snapshot")
    assert n.store.native_quota_snapshot(n.lease.run_id, "host", n.lease.epoch) is None
    conn = n.store._conn
    conn.execute("INSERT INTO platform_quota_admissions (task_id,binding_ref,account_ref,evidence_json,need_json,small_task,safety_buffer) VALUES (?,?,?,?,?,?,?)",
                 (n.task.id, "fake-binding", "account", json.dumps(n.snapshot["evidence"]), json.dumps(n.snapshot["need"]), 0, 10))
    other = n.store.create_task(title="Other reservation")
    for task_id in (n.task.id, other.id):
        conn.execute("INSERT INTO platform_coordinator_claims VALUES (?,?,?,?,?,?,?,?)",
                     (task_id, "window", "host", 1, int(time.time()*1000)+60000, "ACTIVE", "now", "now"))
        conn.execute("INSERT INTO platform_budget_reservations (task_id,claim_epoch,window_id,reserved_token_units,reserved_cost_micro_units,state,created_at,updated_at,account_ref,binding_ref,quota_windows_json,estimate_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     (task_id, 1, "window", 1, 1, "ACTIVE", "now", "now", "account", "fake-binding",
                      json.dumps({"five_hour": 25, "weekly": 25}), json.dumps(n.snapshot["need"])))
    conn.commit()
    snapshot = n.store.native_quota_snapshot(n.lease.run_id, "host", n.lease.epoch)
    assert snapshot["need"] == n.snapshot["need"]
    assert snapshot["outstanding"][0]["task_id"] == other.id
    assert snapshot["outstanding"][0]["quota_windows"]["weekly"] == 25
    with pytest.raises(run_store.TaskStoreError):
        n.store.native_quota_snapshot(n.lease.run_id, "wrong owner", n.lease.epoch)
    conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?", (n.task.id,))
    conn.commit()
    with pytest.raises(run_store.TaskStoreError, match="native_quota_reservation_missing"):
        n.store.native_quota_snapshot(n.lease.run_id, "host", n.lease.epoch)


def test_failed_cleanup_does_not_turn_quota_stop_failure_into_timeout(native, monkeypatch):
    import subprocess
    native.confirm = False
    def timeout(proc, job):
        raise subprocess.TimeoutExpired("fake native process", 10)
    monkeypatch.setattr(functional_validation, "_terminate", timeout)
    result = execute(native, monkeypatch, "codex")
    assert result.quota_pause["state"] == "FAILED"
    assert result.failure_classification == "quota_checkpoint_failed"
    assert native.proc.stdout.closed and native.proc.stderr.closed


@pytest.fixture
def reserved(native, monkeypatch):
    from reverse_agent.platform_v1 import control_store
    n = native
    control = control_store.PlatformControlStore(n.store)
    window = control.activate_window({
        "window_id": "quota-window", "policy_id": "fake", "policy_revision": 1,
        "owner_identity": "test", "starts_at": "2020-01-01T00:00:00Z",
        "expires_at": "2099-01-01T00:00:00Z", "repositories": [],
        "capabilities": ["execute_task"], "max_concurrent_tasks": 1, "max_tasks": 5,
    }, confirmation="ACTIVATE")
    conn = n.store._conn
    conn.execute("INSERT INTO platform_coordinator_claims VALUES (?,?,?,?,?,?,?,?)",
                 (n.task.id, window.id, "coordinator", 1, int(time.time()*1000)+60000, "ACTIVE", "now", "now"))
    conn.execute("INSERT INTO platform_quota_admissions (task_id,binding_ref,account_ref,evidence_json,need_json,small_task,safety_buffer) VALUES (?,?,?,?,?,?,?)",
                 (n.task.id, "fake-binding", "account", json.dumps(n.snapshot["evidence"]), json.dumps(n.snapshot["need"]), 0, 10))
    conn.execute("INSERT INTO platform_budget_reservations (task_id,claim_epoch,window_id,reserved_token_units,reserved_cost_micro_units,state,created_at,updated_at,account_ref,binding_ref,quota_windows_json,estimate_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                 (n.task.id, 1, window.id, 1000, 1000, "ACTIVE", "now", "now", "account", "fake-binding",
                  json.dumps({"five_hour": 25, "weekly": 25}), json.dumps(n.snapshot["need"])))
    conn.commit()
    monkeypatch.delattr(n.store, "native_quota_snapshot")
    n.control, n.window = control, window
    return n


def host_dispatch(n, monkeypatch, raw):
    """Public host execution with only transport, repository and lease acquisition faked."""
    router = task_runtime.ExecutorRouter()
    executor = SimpleNamespace(
        prepare_worktree_once=lambda *a: codex.CodexPreparedContext(
            n.root, "a"*40, n.task.execution_id, "fake.exe", "codex"),
        execute_role_prepared=lambda *a, **k: raw() if callable(raw) else raw)
    monkeypatch.setattr(router, "create_executor", lambda **k: executor)
    monkeypatch.setattr(durable_execution, "resolve_repository_workspace", lambda *a: None)
    service = durable_execution.DurableExecutionService(store=n.store, router=router,
        execution_authority_sha="b"*40, planning_sha="c"*40)
    monkeypatch.setattr(service, "_acquire_or_find_lease", lambda *a: n.lease)
    monkeypatch.setattr(service, "_build_executor_kwargs", lambda *a: {})
    monkeypatch.setattr(service, "_git_rev_parse_head", lambda *a: "a"*40)
    return service, lambda: service.execute_durable_single(n.task.id, workspace_root=str(n.root.parent))


def reservation_row(n):
    return dict(n.store._conn.execute("SELECT * FROM platform_budget_reservations WHERE task_id=?", (n.task.id,)).fetchone())


@pytest.mark.parametrize("kind", ["codex", "claude_code"])
@pytest.mark.parametrize("observed", ["complete", "tokens_only", "missing"])
@pytest.mark.parametrize("cooperative", [False, True])
def test_host_parks_and_settles_once_with_reset_persisted(reserved, monkeypatch, kind, observed, cooperative):
    n = reserved
    n.cooperative = cooperative
    def transport():
        n.raw = execute(n, monkeypatch, kind)
        if observed != "missing":
            n.store.append_usage_observation(n.task.id, observation_id="paused-usage", execution_id=n.task.execution_id,
                role="executor", model_id="fake", provider_id=kind, source_kind="native_summary", source_id="attempt-1",
                status="OBSERVED" if observed == "complete" else "PARTIAL", input_units=7, output_units=2, reasoning_units=0,
                cache_read_units=0, cache_write_units=0, cost_micro_units=12 if observed == "complete" else None)
        return n.raw
    measured = observed == "complete"
    tokens_measured = observed != "missing"
    service, dispatch = host_dispatch(n, monkeypatch, transport)
    result = dispatch()
    raw = n.raw
    assert result.quota_pause == raw.quota_pause and not result.success
    task = n.store.get_task(n.task.id)
    assert task.status == "QUOTA_WAIT" and task.failure_classification == "quota_paused"
    assert task.failure_reset_at == "2027-01-15T09:00:00Z"
    hold = n.control.quota_hold(n.task.id)
    assert hold["until"] == task.failure_reset_at and hold["checkpoint_id"] == raw.quota_pause["checkpoint_id"]
    assert hold["reason"] == "quota_capacity"  # forecast, not confirmed provider exhaustion
    run = n.store._get_durable_run(n.lease.run_id)
    assert run.accepted_checkpoint == "PRE_PLANNER"
    row = reservation_row(n)
    # PARTIAL rows keep the reservation and overrun enforcement conservative
    # (never reconciled), but their measured tokens still carry a list-price
    # price_units so delta calibration can learn (#1323).
    assert row["state"] == ("RECONCILED" if measured else "UNKNOWN")
    assert row["observed_token_units"] == (9 if measured else None)
    assert row["observed_cost_micro_units"] == (12 if measured else None)
    settlement = json.loads(row["settlement_json"])
    assert not settlement["limit_cutoff"]
    assert settlement["tokens"]["input"] == (7 if tokens_measured else None)
    assert settlement["state"] == ("ESTIMATED" if measured else "UNKNOWN")
    assert settlement["price_units"] == (7 if tokens_measured else None)
    assert n.control.get_window(n.window.id).tasks_completed == 0
    n.store.interrupt_for_quota(n.lease.run_id, n.task.id, "host", n.lease.epoch, raw.quota_pause)
    n.control.complete_task_claim(window_id=n.window.id, task_id=n.task.id, owner="coordinator", epoch=1, result="terminal:QUOTA_WAIT")
    assert reservation_row(n) == row
    assert n.store._conn.execute("SELECT COUNT(*) FROM platform_usage_charges").fetchone()[0] == int(observed != "missing")
    assert len(n.control.list_receipts(window_id=n.window.id)) == 1
    with pytest.raises(run_store.TaskStoreError):
        n.control.complete_task_claim(window_id=n.window.id, task_id=n.task.id, owner="stale", epoch=1, result="pause")
    with pytest.raises(durable_execution.DurableResumeError):
        service.resume_single(n.task.id, workspace_root=str(n.root.parent))
    with pytest.raises(run_store.TaskStoreError, match="quota_pause_requires_readmission"):
        n.quota.journal("RESUMING", None)


def test_native_codex_tokens_only_settlement_feeds_delta_calibration(reserved, monkeypatch):
    """#1323: native CLI turn totals must reach the settlement with price units.

    A PARTIAL native_summary observation (measured tokens, no dollar cost) settles
    the reservation on the token axis, keeps the cost axis honestly NULL, and the
    resulting price_units lets delta calibration learn a units-per-percent rate
    from the account's provider-reported window delta.
    """
    from reverse_agent.model_access import quota_forecast

    n = reserved
    def transport():
        n.raw = execute(n, monkeypatch, "codex")
        n.store.append_usage_observation(n.task.id, observation_id="native-turn", execution_id=n.task.execution_id,
            role="executor", model_id="fake", provider_id="codex", source_kind="native_summary", source_id="attempt-1",
            status="PARTIAL", input_units=7, output_units=2, reasoning_units=0,
            cache_read_units=0, cache_write_units=0, cost_micro_units=None)
        return n.raw
    service, dispatch = host_dispatch(n, monkeypatch, transport)
    assert not dispatch().success
    row = reservation_row(n)
    # The reservation stays conservative (PARTIAL never reconciles the budget
    # axes), but the settlement prices the measured turn totals so that delta
    # calibration can finally learn from native Codex runs.
    assert row["state"] == "UNKNOWN"
    assert row["observed_token_units"] is None and row["observed_cost_micro_units"] is None
    settlement = json.loads(row["settlement_json"])
    assert settlement["state"] == "UNKNOWN"  # window attribution still needs dollar cost
    assert settlement["price_units"] == 7  # list-price equivalent of measured tokens

    # A later fresh provider reading lets delta calibration learn from this task.
    start = 1_800_000_000.0
    conn = n.store._conn
    # delta_calibration parses timestamps; normalize the admission evidence to ISO.
    admission = conn.execute(
        "SELECT evidence_json FROM platform_quota_admissions WHERE task_id=?", (n.task.id,)).fetchone()
    before = json.loads(admission[0])
    before["observed_at"] = quota_forecast.iso(start)
    conn.execute(
        "UPDATE platform_quota_admissions SET evidence_json=? WHERE task_id=?",
        (json.dumps(before), n.task.id),
    )
    conn.execute(
        "UPDATE platform_budget_reservations SET created_at=?, reconciled_at=? WHERE task_id=?",
        (quota_forecast.iso(start + 10), quota_forecast.iso(start + 500), n.task.id),
    )
    conn.commit()
    before_windows = before["windows"]
    after = {"account_ref": "account", "source": "official", "observed_at": quota_forecast.iso(start + 900),
             "windows": [dict(before_windows[0], used_percent=60), before_windows[1]]}
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM platform_budget_reservations WHERE account_ref='account'")]
    for item in rows:
        item["settlement"] = json.loads(item["settlement_json"])
    with n.control._lock, conn:
        n.control._delta_calibrate_locked("account", after, rows)
    rates = n.control.quota_calibration("account")
    # units per percentage point: 7 units over (60 - 50 + 1) pp, weekly saw no increase.
    assert rates == pytest.approx({"five_hour": 7 / 11})


@pytest.mark.parametrize("boundary", ["saved", "settlement", "park"])
@pytest.mark.parametrize("kind", ["codex", "claude_code"])
def test_host_crash_recovery_is_atomic_and_idempotent(reserved, monkeypatch, boundary, kind):
    from reverse_agent.platform_v1 import control_store
    n = reserved
    # A previous role's complete record cannot settle an unobserved paused attempt.
    n.store.append_usage_observation(n.task.id, observation_id="earlier-role", execution_id=n.task.execution_id,
        role="planner", model_id="fake", provider_id=kind, source_kind="native_summary", source_id="earlier",
        status="OBSERVED", input_units=3, output_units=1, reasoning_units=0,
        cache_read_units=0, cache_write_units=0, cost_micro_units=4)
    raw = execute(n, monkeypatch, kind)
    service, dispatch = host_dispatch(n, monkeypatch, raw)
    class Crash(BaseException):
        pass
    original = control_store.PlatformControlStore._finalize_task_claim
    def crash_settlement(self, **kwargs):
        original(self, **kwargs)
        raise Crash()
    with monkeypatch.context() as crash_patch:
        if boundary == "saved":
            crash_patch.setattr(n.store, "interrupt_for_quota", lambda *a, **k: (_ for _ in ()).throw(Crash()))
        elif boundary == "settlement":
            crash_patch.setattr(control_store.PlatformControlStore, "_finalize_task_claim", crash_settlement)
        else:
            # Fail the task parking write after reconciliation has written its rows.
            n.store._conn.execute("CREATE TRIGGER crash_park BEFORE UPDATE OF status ON tasks WHEN NEW.status='QUOTA_WAIT' BEGIN SELECT RAISE(ABORT, 'crash park'); END")
        with pytest.raises((Crash, sqlite3.IntegrityError)):
            dispatch()
    if boundary == "park":
        n.store._conn.execute("DROP TRIGGER crash_park")
    assert reservation_row(n)["state"] == "ACTIVE"
    assert n.control.get_window(n.window.id).unknown_observation_count == 0
    assert n.store._conn.execute("SELECT COUNT(*) FROM platform_usage_charges").fetchone()[0] == 0
    assert n.store.get_task(n.task.id).status == "RUNNING"
    # A coordinator's generic exception cleanup must leave pending pause accounting alone.
    with pytest.raises(run_store.TaskStoreError, match="quota_pause_pending_recovery"):
        n.control.abandon_task_claim(window_id=n.window.id, task_id=n.task.id, owner="coordinator", epoch=1, reason="crash")
    n.store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=0 WHERE run_id=?", (n.lease.run_id,))
    n.store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?", (n.task.id,))
    restarted = run_store.TaskStore(n.store.db_path)
    recovery = durable_execution.DurableExecutionService(store=restarted, router=task_runtime.ExecutorRouter())
    try:
        records = recovery.reconcile_expired_runs()
        assert recovery.reconcile_expired_runs() == ()
    finally:
        restarted._conn.close()
    assert records[0]["recovery_classification"] == "quota_wait"
    assert n.store.get_task(n.task.id).status == "QUOTA_WAIT"
    assert reservation_row(n)["state"] == "UNKNOWN"
    assert n.control.get_window(n.window.id).unknown_observation_count == 1
    assert service.reconcile_expired_runs() == ()
    assert n.control.get_window(n.window.id).unknown_observation_count == 1


@pytest.mark.parametrize("stale", ["durable_owner", "claim_epoch", "claim_expired", "workspace"])
def test_host_pause_refuses_stale_or_changed_proof(reserved, monkeypatch, stale):
    n = reserved
    raw = execute(n, monkeypatch, "claude_code")
    service, dispatch = host_dispatch(n, monkeypatch, raw)
    if stale == "durable_owner":
        n.store._conn.execute("UPDATE durable_runs SET lease_owner='replacement',lease_epoch=lease_epoch+1 WHERE run_id=?", (n.lease.run_id,))
    elif stale == "claim_epoch":
        n.store._conn.execute("UPDATE platform_coordinator_claims SET epoch=2 WHERE task_id=?", (n.task.id,))
    elif stale == "claim_expired":
        n.store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?", (n.task.id,))
    else:
        (n.root / "partial.txt").write_text("changed after native save")
    with pytest.raises(run_store.TaskStoreError):
        dispatch()
    assert reservation_row(n)["state"] == "ACTIVE"
    assert n.control.get_window(n.window.id).tasks_completed == 0
    assert n.store.get_task(n.task.id).status != "QUOTA_WAIT"


def test_confirmed_provider_rejection_is_not_a_forecast_hold(reserved, monkeypatch):
    n = reserved
    n.rejected = True
    service, dispatch = host_dispatch(n, monkeypatch, lambda: execute(n, monkeypatch, "claude_code"))
    result = dispatch()
    assert result.quota_pause["state"] == "PAUSED"
    hold = n.control.quota_hold(n.task.id)
    assert hold["reason"] == "provider_exhaustion" and hold["confirmed_exhaustion"] is True
    assert json.loads(reservation_row(n)["settlement_json"])["limit_cutoff"] is True


def test_unknown_reset_stays_unknown_after_restart(reserved, monkeypatch):
    n = reserved
    for window in n.snapshot["evidence"]["windows"]:
        window["resets_at"] = None
    n.store._conn.execute("UPDATE platform_quota_admissions SET evidence_json=? WHERE task_id=?",
                          (json.dumps(n.snapshot["evidence"]), n.task.id))
    service, dispatch = host_dispatch(n, monkeypatch, lambda: execute(n, monkeypatch, "codex"))
    dispatch()
    restarted = run_store.TaskStore(n.store.db_path)
    try:
        from reverse_agent.platform_v1 import control_store
        control = control_store.PlatformControlStore(restarted)
        assert restarted.get_task(n.task.id).status == "QUOTA_WAIT"
        assert restarted.get_task(n.task.id).failure_reset_at == ""
        assert control.quota_hold(n.task.id)["until"] is None
        assert reservation_row(n)["quota_state"] == "UNKNOWN"
        for store in (n.store, restarted):
            with pytest.raises(run_store.TaskStoreError, match="quota_pause_requires_readmission"):
                store._recover_durable_lease(n.lease.run_id, "another-host")
            assert not store._conn.in_transaction
        assert restarted._get_durable_run(n.lease.run_id).lease_epoch == n.lease.epoch
    finally:
        restarted._conn.close()


def test_two_recovering_hosts_do_not_duplicate_settlement(reserved, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from reverse_agent.platform_v1 import control_store
    n = reserved
    execute(n, monkeypatch, "codex")
    n.store._conn.execute("UPDATE tasks SET status='RUNNING' WHERE id=?", (n.task.id,))
    n.store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=0 WHERE run_id=?", (n.lease.run_id,))
    barrier = threading.Barrier(2)
    stores = [run_store.TaskStore(n.store.db_path) for _ in range(2)]
    for store in stores:
        control_store.PlatformControlStore(store)
    def recover(store):
        service = durable_execution.DurableExecutionService(store=store, router=task_runtime.ExecutorRouter())
        barrier.wait(timeout=3)
        service.reconcile_expired_runs()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(recover, store) for store in stores]
            for future in futures:
                future.result(timeout=5)
        assert n.store.get_task(n.task.id).status == "QUOTA_WAIT"
        assert reservation_row(n)["state"] == "UNKNOWN"
        assert n.control.get_window(n.window.id).unknown_observation_count == 1
        assert n.control.get_window(n.window.id).tasks_completed == 0
        assert len(n.control.list_receipts(window_id=n.window.id)) == 1
    finally:
        for store in stores:
            store._conn.close()


def coordinator_recovery(n, monkeypatch, *, alternative=False, pinned=False):
    """Real SQLite admission/coordinator/durable path with provider-free host inputs."""
    from reverse_agent.platform_v1 import control_store, unattended_coordinator, trusted_host
    from reverse_agent.platform_v1 import model_router
    # A new process opens the persisted database rather than retaining native controller state.
    store = run_store.TaskStore(n.store.db_path)
    control = control_store.PlatformControlStore(store)
    goal = control.create_goal(title="Resume", objective="Finish saved work", repository="dddd2024/Nerelan",
        idempotency_key="resume-goal", executor_kind="codex", orchestration_mode="agent_team" if alternative else "single",
        binding_ref="fake-binding" if pinned or not alternative else "")
    control.save_goal_plan(goal.id, expected_revision=1, spec_markdown="Saved work", plan_markdown="Resume",
        tasks=[{"id": "T1", "title": "Finish", "instruction": "Finish and validate", "difficulty": 3}], acceptance_criteria=[])
    control.approve_goal(goal.id, expected_revision=1)
    control.link_goal_task(goal.id, goal_revision=1, plan_task_id="T1", task_id=n.task.id, dependencies=[], seq=0)
    control.mark_goal_running(goal.id, revision=1, window_id=n.window.id)
    store._conn.execute("UPDATE platform_autonomous_windows SET capabilities_json=?,max_retries=5 WHERE id=?",
                        (json.dumps(["execute_task", "resume_task"]), n.window.id))
    host = object.__new__(trusted_host.CombinedTrustedHost)
    host._task_store, host._control_store = store, control
    bindings = [{"binding_id": ref, "connection_id": account, "model_id": model, "executor_id": kind, "enabled": True}
                for ref, account, model, kind in [("fake-binding", "account", "gpt-6-sol", "codex"),
                    ("alternative", "other-account", "claude-sonnet-4-6", "claude_code")]]
    host._store = SimpleNamespace(list_bindings_public=lambda: bindings,
        get_connection_public=lambda account: {"connection_id": account, "account_ref": account, "auth_method": "external_cli_session",
                                               "executor_provider_id": "codex" if account == "account" else "claude-code"})
    fresh = {account: {"account_ref": account, "source": "official", "observed_at": time.time(),
             "windows": [{"window": w, "used_percent": 0, "resets_at": time.time()+3600} for w in ("five_hour", "weekly")]}
             for account in ("account", "other-account")}
    host._subscription_quotas = lambda: fresh
    host._account_task_need = lambda binding, task, evidence, records: dict(n.snapshot["need"], account_ref=evidence["account_ref"])
    # Exercise the production pure qualifying router with deterministic catalog/qualification fixtures.
    def route(task, *, goal, forecast, quota_evidence):
        assert forecast is True
        assert quota_evidence["other-account"]["fresh"]
        rows = [dict(b, cost_class="subscription", runnable=True, availability={"state": "AVAILABLE"},
                     quota={"decision": "switch", "reason": "quota_capacity"} if b["binding_id"] == "fake-binding" else None)
                for b in bindings]
        return model_router.select_model(rows, difficulty=task.difficulty, kind=task.kind,
            capability_table={b["model_id"]: {"tiers": {"code": 5}} for b in bindings}, exploration_draw=1)
    host._resolve_task_model = route
    router = task_runtime.ExecutorRouter()
    permissions = SimpleNamespace(allowed=True, calls=[])
    def authorize(**kwargs):
        permissions.calls.append(kwargs)
        return permissions.allowed
    autonomy = SimpleNamespace(authorize=authorize)
    coordinator = unattended_coordinator.UnattendedCoordinator(store=store, control_store=control,
        autonomy=autonomy, router=router, workspace_root=n.root.parent, owner="resumed-coordinator",
        execution_authority_sha="b"*40, planning_sha="c"*40, quota_preparer=host._prepare_task_quota)
    monkeypatch.setattr(durable_execution, "resolve_repository_workspace", lambda *a: None)
    monkeypatch.setattr(durable_execution.DurableExecutionService, "_git_rev_parse_head", lambda *a: "a"*40)
    monkeypatch.setattr(durable_execution.DurableExecutionService, "_build_executor_kwargs", lambda *a: {})
    return SimpleNamespace(store=store, control=control, host=host, fresh=fresh, coordinator=coordinator,
                           router=router, permissions=permissions, goal=goal)


def park_for_resume(n, monkeypatch):
    n.cooperative = True
    service, dispatch = host_dispatch(n, monkeypatch, lambda: execute(n, monkeypatch, "codex"))
    dispatch()
    assert n.store.get_task(n.task.id).status == "QUOTA_WAIT"
    # A fresh observation is required even when the previous one remains within its TTL.
    monkeypatch.setattr(run_store.time, "time", lambda: 1_800_000_001.0)


def resume_transport(n, recovered, monkeypatch, *, crash=False):
    launches = []
    class Crash(BaseException):
        pass
    def factory(*, executor_kind, **kwargs):
        cls = codex.CodexExecutor if executor_kind == "codex" else claude.ClaudeCodeExecutor
        executor = cls(model_id="fake", parent_env={})
        monkeypatch.setattr(executor, "_verify_workspace", lambda *a: None)
        monkeypatch.setattr(executor, "reconstruct_prepared_context", lambda **k: codex.CodexPreparedContext(
            n.root, "a"*40, n.task.execution_id, "fake.exe", executor_kind))
        def stream(prepared, prompt, parser):
            launches.append((executor_kind, prompt))
            assert (n.root / "partial.txt").read_bytes() == b"unfinished prefix"
            assert "Saved prefix" in prompt and "Complete suffix and validate" in prompt
            assert recovered.store._get_durable_run(n.lease.run_id).lease_epoch == n.lease.epoch+1
            if crash:
                raise Crash()
            # Fake protocol transport; production executor still builds the prompt and consumes the parser.
            if executor_kind == "codex":
                events = [{"type": "thread.started", "thread_id": "fresh-thread"}, {"type": "turn.started"},
                    {"type": "item.completed", "item": {"type": "agent_message", "text": "Completed suffix"}},
                    {"type": "turn.completed"}]
            else:
                events = [{"type": "result", "subtype": "success", "is_error": False, "result": "Completed suffix"}]
            for event in events:
                parser.feed(json.dumps(event).encode()+b"\n")
            return 0
        monkeypatch.setattr(executor, "_stream", stream)
        return executor
    monkeypatch.setattr(recovered.router, "create_executor", factory)
    monkeypatch.setattr(task_runtime.LocalValidationRunner, "run", lambda *a, **k: (0, "fixture hygiene", "digest"))
    monkeypatch.setattr(codex, "_collect_final_product_files", lambda *a: [{"path": "partial.txt", "content": "unfinished prefix"}])
    return launches, Crash


@pytest.mark.parametrize("alternative", [False, True])
def test_coordinator_restart_readmits_saved_native_work_with_new_reservation(reserved, monkeypatch, alternative):
    n = reserved
    park_for_resume(n, monkeypatch)
    old = reservation_row(n)
    checkpoint_id = n.quota.checkpoint_id
    r = coordinator_recovery(n, monkeypatch, alternative=alternative)
    launches, _ = resume_transport(n, r, monkeypatch)
    try:
        assert r.coordinator.tick() == 1, (r.coordinator._last_error, r.coordinator._last_batch)
        assert len(launches) == 1, (r.coordinator._last_batch, r.store.get_task(n.task.id).failure_detail)
        assert launches[0][0] == ("claude_code" if alternative else "codex")
        assert all(c["operation"] == "resume_task" for c in r.permissions.calls)
        reservations = [dict(row) for row in r.store._conn.execute(
            "SELECT * FROM platform_budget_reservations WHERE task_id=? ORDER BY claim_epoch", (n.task.id,))]
        assert len(reservations) == 2 and reservations[0] == old
        assert reservations[1]["claim_epoch"] == 2
        assert reservations[1]["binding_ref"] == ("alternative" if alternative else "fake-binding")
        assert reservations[1]["account_ref"] == ("other-account" if alternative else "account")
        assert r.store.quota_checkpoint(n.lease.run_id, checkpoint_id,
            "resumed-coordinator", n.lease.epoch+1)["state"] == "RESUMED"
        assert r.coordinator.tick() == 0
        assert len(launches) == 1, (r.coordinator._last_batch, r.store.get_task(n.task.id).failure_detail)
    finally:
        r.store._conn.close()


def test_quota_parked_goal_is_stranded_then_rebound_and_resumed_in_a_new_window(reserved, monkeypatch):
    n = reserved
    park_for_resume(n, monkeypatch)
    r = coordinator_recovery(n, monkeypatch)
    launches, _ = resume_transport(n, r, monkeypatch)
    try:
        # The quota reset outlives the window: the parked Goal must surface and move, not freeze.
        r.store._conn.execute("UPDATE platform_autonomous_windows SET status='EXPIRED' WHERE id=?", (n.window.id,))
        stranded = r.control.stranded_goals()
        assert [(g["goal_id"], g["quota_wait"]) for g in stranded] == [(r.goal.id, 1)]
        repositories = sorted({r.goal.repository, n.task.repository})
        successor = r.control.activate_window({
            "window_id": "quota-window-2", "policy_id": "fake-successor", "policy_revision": 1,
            "owner_identity": "test", "starts_at": "2020-01-01T00:00:00Z",
            "expires_at": "2099-01-01T00:00:00Z", "repositories": repositories,
            "capabilities": ["execute_task", "resume_task"], "max_concurrent_tasks": 1, "max_tasks": 5,
            "max_retries": 5,
        }, confirmation="ACTIVATE")
        # The window ends long after the paused attempt's durable lease (5 minutes).
        monkeypatch.setattr(run_store.time, "time", lambda: 1_800_000_400.0)
        rebound = r.control.rebind_goal_to_window(r.goal.id, window_id=successor.id)
        assert [(t["task_id"], t["status"], t["operation"]) for t in rebound["tasks"]] == [
            (n.task.id, "QUOTA_WAIT", "resume_task")]
        assert r.control.stranded_goals() == ()
        assert r.coordinator.tick() == 1, (r.coordinator._last_error, r.coordinator._last_batch)
        assert len(launches) == 1
        assert r.store._conn.execute(
            "SELECT window_id FROM platform_budget_reservations WHERE task_id=? AND claim_epoch=2",
            (n.task.id,)).fetchone()[0] == successor.id
    finally:
        r.store._conn.close()


@pytest.mark.parametrize("refusal", ["missing", "tampered", "unknown", "cached", "authority", "binding", "no_model"])
def test_coordinator_quota_recovery_stays_parked_without_proof_or_authority(reserved, monkeypatch, refusal):
    n = reserved
    park_for_resume(n, monkeypatch)
    r = coordinator_recovery(n, monkeypatch, alternative=refusal == "no_model")
    launches, _ = resume_transport(n, r, monkeypatch)
    if refusal == "missing":
        n.root.rename(n.root.with_name("preserved-missing-workspace"))
    elif refusal == "tampered":
        (n.root / "partial.txt").write_text("tampered")
    elif refusal == "unknown":
        r.fresh.clear()
    elif refusal == "cached":
        for value in r.fresh.values():
            value["observed_at"] = 1_800_000_000
    elif refusal == "authority":
        r.permissions.allowed = False
    elif refusal == "binding":
        r.store._conn.execute("UPDATE tasks SET binding_ref='unauthorized' WHERE id=?", (n.task.id,))
    elif refusal == "no_model":
        r.host._resolve_task_model = lambda *a, **k: (_ for _ in ()).throw(run_store.TaskStoreError("no_runnable_model"))
    try:
        assert r.coordinator.tick() == 0
        assert launches == []
        assert r.store.get_task(n.task.id).status == "QUOTA_WAIT"
        assert r.store._get_durable_run(n.lease.run_id).lease_epoch == n.lease.epoch
        assert r.store._conn.execute("SELECT COUNT(*) FROM platform_budget_reservations WHERE task_id=?", (n.task.id,)).fetchone()[0] == 1
    finally:
        r.store._conn.close()


def test_2026_10_19_codex_ninety_percent_large_queue_parks_before_launch(reserved, monkeypatch):
    n = reserved
    # Deterministic replay: no in-flight save exists yet; admission alone must stop launch.
    r = coordinator_recovery(n, monkeypatch)
    r.store._conn.execute("UPDATE tasks SET status='QUEUED' WHERE id=?", (n.task.id,))
    r.store._conn.execute("UPDATE platform_coordinator_claims SET status='COMPLETE' WHERE task_id=?", (n.task.id,))
    r.store._conn.execute("UPDATE platform_budget_reservations SET state='RECONCILED' WHERE task_id=?", (n.task.id,))
    for value in r.fresh.values():
        value["observed_at"] = "2026-10-19T12:00:00Z"
        value["windows"] = [{"window": "five_hour", "used_percent": 90, "resets_at": "2026-10-19T17:00:00Z"},
                            {"window": "weekly", "used_percent": 20, "resets_at": "2026-10-26T12:00:00Z"}]
    from datetime import datetime
    replay = datetime.fromisoformat("2026-10-19T12:00:00+00:00").timestamp()
    monkeypatch.setattr(run_store.time, "time", lambda: replay)
    launches = []
    monkeypatch.setattr(r.router, "create_executor", lambda **kwargs: launches.append(kwargs))
    try:
        assert r.coordinator.tick() == 0
        assert launches == []
        assert r.control.quota_hold(n.task.id)["decision"] == "quota_wait"
        assert r.store.get_task(n.task.id).status == "QUEUED"
    finally:
        r.store._conn.close()


def test_coordinator_refuses_pinned_goal_substitution_even_with_fresh_capacity(reserved, monkeypatch):
    n = reserved
    park_for_resume(n, monkeypatch)
    r = coordinator_recovery(n, monkeypatch, alternative=True, pinned=True)
    launches, _ = resume_transport(n, r, monkeypatch)
    prepare = r.coordinator.quota_preparer
    def unauthorized(task):
        prepare(task)
        row = r.store._conn.execute("SELECT verdict_json FROM platform_quota_admissions WHERE task_id=?", (task.id,)).fetchone()
        verdict = json.loads(row[0])
        verdict["resume_route"] = {"goal_id": r.goal.id, "goal_revision": 1, "source_binding": task.binding_ref,
                                   "binding_ref": "alternative", "executor_kind": "claude_code"}
        r.store._conn.execute("UPDATE platform_quota_admissions SET binding_ref='alternative',verdict_json=? WHERE task_id=?",
                             (json.dumps(verdict), task.id))
    r.coordinator.quota_preparer = unauthorized
    try:
        assert r.coordinator.tick() == 0
        assert r.coordinator._last_error == "quota_resume_substitution_unauthorized"
        assert launches == []
        assert r.store.get_task(n.task.id).binding_ref == "fake-binding"
        assert r.store.get_task(n.task.id).status == "QUOTA_WAIT"
    finally:
        r.store._conn.close()


@pytest.mark.parametrize("reason", ["underpowered", "review_ancestry"])
def test_coordinator_preserves_qualification_and_review_boundary(reserved, monkeypatch, reason):
    n = reserved
    park_for_resume(n, monkeypatch)
    r = coordinator_recovery(n, monkeypatch, alternative=True)
    launches, _ = resume_transport(n, r, monkeypatch)
    if reason == "underpowered":
        r.host._resolve_task_model = lambda *a, **k: {"binding_ref": "alternative", "executor_kind": "claude_code", "underpowered": True}
    else:
        r.store._conn.execute("UPDATE platform_goals SET tasks_json=? WHERE id=?", (json.dumps([
            {"id": "T1", "title": "Review", "instruction": "Review independently", "kind": "review", "agent_role": "reviewer"}]), r.goal.id))
    try:
        assert r.coordinator.tick() == 0
        assert launches == []
        assert r.store.get_task(n.task.id).status == "QUOTA_WAIT"
    finally:
        r.store._conn.close()


def test_resume_crash_is_ambiguous_and_cannot_launch_again(reserved, monkeypatch):
    n = reserved
    park_for_resume(n, monkeypatch)
    checkpoint_id = n.quota.checkpoint_id
    r = coordinator_recovery(n, monkeypatch)
    launches, crash = resume_transport(n, r, monkeypatch, crash=True)
    try:
        with pytest.raises(crash):
            r.coordinator.tick()
        assert len(launches) == 1
        assert r.store._conn.execute("SELECT state FROM quota_partial_checkpoints WHERE checkpoint_id=?", (checkpoint_id,)).fetchone()[0] == "RESUMING"
        r.store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=1 WHERE run_id=?", (n.lease.run_id,))
        r.store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?", (n.task.id,))
        r.coordinator.reconcile()
        assert r.store.get_task(n.task.id).status == "INTERRUPTED"
        assert r.coordinator.tick() == 0  # durable recovery refuses the ambiguous dispatch
        assert len(launches) == 1
        assert r.store._get_durable_run(n.lease.run_id).lease_epoch == n.lease.epoch+1
        assert r.store._conn.execute("SELECT state FROM quota_partial_checkpoints WHERE checkpoint_id=?", (checkpoint_id,)).fetchone()[0] == "RESUMING"
    finally:
        r.store._conn.close()


def test_recovery_rechecks_saved_bytes_after_reservation(reserved, monkeypatch):
    n = reserved
    park_for_resume(n, monkeypatch)
    r = coordinator_recovery(n, monkeypatch)
    launches, _ = resume_transport(n, r, monkeypatch)
    original = r.control.claim_task
    def claim(**kwargs):
        result = original(**kwargs)
        (n.root / "partial.txt").write_bytes(b"changed after reservation")
        return result
    monkeypatch.setattr(r.control, "claim_task", claim)
    try:
        assert r.coordinator.tick() == 0
        assert launches == []
        assert r.store._get_durable_run(n.lease.run_id).lease_epoch == n.lease.epoch
    finally:
        r.store._conn.close()


def test_two_coordinators_only_one_can_readmit_and_recover_saved_run(reserved, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from reverse_agent.platform_v1 import control_store
    n = reserved
    park_for_resume(n, monkeypatch)
    r = coordinator_recovery(n, monkeypatch)
    second = run_store.TaskStore(n.store.db_path)
    other = control_store.PlatformControlStore(second)
    # Both coordinators have selected fresh evidence; claims still serialize in SQLite.
    r.host._prepare_task_quota(r.store.get_task(n.task.id))
    barrier = threading.Barrier(2)
    def claim(control, owner):
        barrier.wait(timeout=3)
        try:
            return control.claim_task(window_id=n.window.id, task_id=n.task.id, owner=owner, lease_ms=60000)[0]
        except run_store.TaskStoreError as exc:
            return str(exc)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(claim, control, owner) for control, owner in [(r.control, "one"), (other, "two")]]
            results = [f.result(timeout=5) for f in futures]
        assert results.count(2) == 1
        assert sum(isinstance(v, str) for v in results) == 1
        assert r.store._conn.execute("SELECT COUNT(*) FROM platform_budget_reservations WHERE task_id=? AND state='ACTIVE'", (n.task.id,)).fetchone()[0] == 1
        winner = "one" if results[0] == 2 else "two"
        recovered = r.store._recover_durable_lease(n.lease.run_id, winner, require_interrupted=True)
        with pytest.raises(run_store.TaskStoreError, match="quota_resume_dispatch_ambiguous"):
            second._recover_durable_lease(n.lease.run_id, "duplicate", require_interrupted=True)
        assert recovered.epoch == n.lease.epoch+1
    finally:
        r.store._conn.close()
        second._conn.close()
