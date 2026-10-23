"""Owned CLI process-lifecycle regression coverage (provider-free).

These tests drive ``_run_owned_cli_process`` with *real* trusted Python
parent/child scripts. No model, provider, network, credential or user process
is touched. They pin the timeout-path contract for #1328:

* the owned process tree (parent + descendants) is confirmed stopped before
  any worktree read/hash/snapshot, on timeout, error and normal return;
* a timeout preserves bounded partial numeric usage as PARTIAL, never as a
  wholly-OBSERVED accounting total, so the reservation stays UNKNOWN;
* an unconfirmed cleanup must fail closed and never be treated as proof that
  descendants exited or that capacity was freed.

Windows assigns the child to a kill-on-close job object *suspended*, then
resumes it; POSIX starts a session/process-group leader. Both are exercised
here through the same public seam, so the assertions hold on either host.
"""
from __future__ import annotations

import json
import io
import os
import subprocess
import sys
import time
import threading
from types import SimpleNamespace
from pathlib import Path

import pytest

from reverse_agent.platform_v1 import opencode_executor as oe
from reverse_agent.platform_v1.run_store import TaskStore


@pytest.mark.parametrize("disappears", [False, True])
def test_posix_confirmation_waits_for_group_disappearance(monkeypatch, disappears):
    from reverse_agent.platform_v1 import native_quota
    clock, probes, sleeps = [0.], [], []

    def killpg(pid, sig):
        assert pid == 123  # Controlled seam only; no real OS signal.
        if sig == 0:
            probes.append(clock[0])
            if disappears and len(probes) == 2:
                raise ProcessLookupError()

    def sleep(delay):
        sleeps.append(delay)
        clock[0] += 5.

    proc = SimpleNamespace(pid=123, wait=lambda timeout: 0, poll=lambda: 0)
    monkeypatch.setattr(native_quota, "os", SimpleNamespace(killpg=killpg))
    monkeypatch.setattr(native_quota, "signal", SimpleNamespace(SIGKILL=9))
    monkeypatch.setattr(native_quota, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=sleep))
    assert native_quota.stop_and_confirm(proc, None) is disappears
    assert sleeps and len(probes) >= 2
    if not disappears:
        assert clock[0] == 10.


def test_uncertain_cleanup_does_not_close_a_locked_reader(monkeypatch, tmp_path):
    """Release the fixture ourselves even if a regression blocks close()."""
    entered, release, done = threading.Event(), threading.Event(), threading.Event()
    lock = threading.Lock()

    class Pipe:
        closed = False

        def read(self, size):
            with lock:
                entered.set()
                release.wait()
            return b""

        def close(self):
            with lock:
                self.closed = True

    pipe = Pipe()

    class Proc:
        stdout, stderr, stdin, returncode = pipe, io.BytesIO(), None, None

        def wait(self, timeout):
            assert entered.wait(1)
            raise subprocess.TimeoutExpired("controlled fixture", timeout)

        def poll(self):
            return None

    class Job:
        def attach_and_resume(self, proc):
            pass

        def close(self):
            pass  # Deliberately do not unblock the reader; no real process.

    from reverse_agent.platform_v1 import functional_validation, native_quota
    monkeypatch.setattr(oe, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(oe.subprocess, "CREATE_NEW_PROCESS_GROUP", 0, raising=False)
    monkeypatch.setattr(oe.subprocess, "CREATE_NO_WINDOW", 0, raising=False)
    monkeypatch.setattr(oe.subprocess, "Popen", lambda *a, **k: Proc())
    monkeypatch.setattr(functional_validation, "_WindowsJob", Job)
    monkeypatch.setattr(native_quota, "stop_and_confirm", lambda *a: False)
    results, errors = [], []

    def invoke():
        try:
            results.append(oe._run_owned_cli_process(["fixture"], cwd=str(tmp_path), env={}, timeout=.01))
        except BaseException as exc:
            errors.append(exc)
        finally:
            done.set()

    runner = threading.Thread(target=invoke, daemon=True)
    runner.start()
    try:
        returned_before_release = done.wait(3)
        closed_before_release = pipe.closed
    finally:
        release.set()
        runner.join(3)
    assert returned_before_release, "blocked BufferedReader.close must not extend the deadline"
    assert not closed_before_release
    assert not errors
    assert results[0].timed_out and not results[0].cleanup_confirmed


@pytest.mark.parametrize("confirmed", [False, True])
def test_process_exception_always_stops_posix_owned_group(monkeypatch, tmp_path, confirmed):
    from reverse_agent.platform_v1 import native_quota
    stdout, stderr, stops, kills = io.BytesIO(), io.BytesIO(), [], []

    class Proc:
        stdin, pid = None, 123  # No actual OS call uses this fixture identifier.

        def wait(self, timeout):
            raise OSError("controlled wait failure")

    proc = Proc()
    proc.stdout, proc.stderr = stdout, stderr

    def stop(owned, job):
        assert owned is proc and job is None
        assert not stdout.closed and not stderr.closed
        stops.append(owned)
        return confirmed

    monkeypatch.setattr(oe, "os", SimpleNamespace(name="posix", killpg=lambda *args: kills.append(args)))
    monkeypatch.setattr(oe, "signal", SimpleNamespace(SIGKILL=9))
    monkeypatch.setattr(oe.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(native_quota, "stop_and_confirm", stop)
    expected = OSError if confirmed else oe.OwnedCliCleanupUnconfirmedError
    with pytest.raises(expected):
        oe._run_owned_cli_process(["fixture"], cwd=str(tmp_path), env={}, timeout=.01)
    assert stops == [proc]
    assert len(kills) == (0 if confirmed else 1)
    assert stdout.closed and stderr.closed


@pytest.mark.parametrize("outcome", ["exception", "normal", "timeout"])
def test_core_uncertainty_never_collects_artifacts(monkeypatch, tmp_path, outcome):
    store = TaskStore(":memory:")
    task = store.create_task(title="controlled cleanup uncertainty", executor_kind="opencode")
    events = []

    def run(*args, **kwargs):
        if outcome == "exception":
            raise oe.OwnedCliCleanupUnconfirmedError("controlled")
        return oe.OwnedCliProcessResult(returncode=0, stdout="", stderr="",
                                       timed_out=outcome == "timeout", cleanup_confirmed=False)

    def collect(*args):
        pytest.fail("uncertain cleanup must not read artifacts")

    monkeypatch.setattr(oe, "_run_owned_cli_process", run)
    monkeypatch.setattr(oe, "_collect_changed_files", collect)
    result = oe.OpenCodeExecutor(model_id="fixture/model")._run_executor_core(
        task_id=task.id, store=store, worktree=tmp_path, base_sha="controlled",
        execution_id="controlled", cli_path="fixture", is_cmd=False,
        event_callback=lambda tid, event: events.append(event),
        role_context=oe.RoleContext(role="executor", task_id=task.id, workspace=tmp_path))
    assert not result.success and result.changed_files == []
    assert (result.failure_classification == "cleanup_unconfirmed"
            or result.failure_classification == "timeout"
            and result.error.startswith("opencode_timeout:cleanup_unconfirmed:"))
    assert any(e.get("metadata", {}).get("cleanup_confirmed") is False for e in events)
    if outcome != "timeout":
        rows = store._conn.execute(
            "SELECT status FROM task_usage_observations WHERE task_id = ?", (task.id,)).fetchall()
        assert [row["status"] for row in rows] == ["UNKNOWN"]


def _interpreter_available() -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


needs_real_interpreter = pytest.mark.skipif(
    not _interpreter_available(),
    reason="real host interpreter is required",
)


def _minimal_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for key in ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def _write_parent(
    directory: Path,
    marker: Path,
    *,
    emit_usage: bool = False,
    parent_sleep: float = 30.0,
    child_sleep: float = 3.0,
) -> tuple[Path, Path]:
    """Write a trusted parent that (optionally) emits one numeric usage row,
    spawns a child that sleeps then writes a marker, and then sleeps.

    Returns ``(parent_path, child_path)``.
    """
    child = directory / "child.py"
    child.write_text(
        "import sys,time\n"
        "from pathlib import Path\n"
        "time.sleep(%r)\n"
        "Path(sys.argv[1]).write_text('controlled child completed')\n"
        % (child_sleep,),
        encoding="utf8",
    )
    usage_lines = ""
    if emit_usage:
        usage_lines = (
            "import json\n"
            "ev={'type':'step_finish','message':{'role':'assistant','id':'controlled-message',"
            "'tokens':{'input':11,'output':3,'reasoning':1,'cache':{'read':2,'write':0}},'cost':0.0}}\n"
            "print(json.dumps(ev), flush=True)\n"
        )
    parent = directory / "parent.py"
    parent.write_text(
        "import subprocess,sys,time\n"
        + usage_lines
        + "subprocess.Popen([sys.executable,sys.argv[1],sys.argv[2]],"
        "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
        "time.sleep(%r)\n" % (parent_sleep,),
        encoding="utf8",
    )
    return parent, child


def _run(
    parent: Path,
    child: Path,
    marker: Path,
    *,
    cwd: Path,
    timeout: float,
) -> oe.OwnedCliProcessResult:
    return oe._run_owned_cli_process(
        [sys.executable, str(parent), str(child), str(marker)],
        cwd=str(cwd),
        env=_minimal_env(),
        timeout=timeout,
    )


@needs_real_interpreter
def test_timeout_confirms_owned_child_stopped_and_preserves_partial_usage(
    tmp_path: Path,
) -> None:
    """A timed-out parent that spawned a child must be proven empty, and its
    numeric usage row must be recoverable as INCOMPLETE (never wholly-OBSERVED).

    This is the controlled equivalent of the #1328 fixture: a parent emits a
    parseable usage row and starts a child that would otherwise outlive the
    timeout. After the timeout the child must NOT complete, cleanup must be
    confirmed, and the emitted usage row must parse to one numeric observation.
    """
    marker = tmp_path / "child-finished.txt"
    parent, child = _write_parent(tmp_path, marker, emit_usage=True)

    result = _run(parent, child, marker, cwd=tmp_path, timeout=1)

    assert result.timed_out is True
    assert result.cleanup_confirmed is True

    # The child had 3s of work left; a confirmed cleanup must prevent it from
    # completing after the parent returned.
    time.sleep(4)
    assert not marker.exists()

    observations = oe._extract_usage_observations(
        result.stdout,
        task_id="controlled",
        execution_id="controlled-timeout",
        role="executor",
        fallback_model_id="fixture/model",
    )
    assert len(observations) == 1
    assert observations[0]["status"] == "OBSERVED"
    assert observations[0]["input_units"] == 11
    # The executor downgrades this OBSERVED row to PARTIAL before persistence;
    # PARTIAL never participates in a wholly-OBSERVED accounting total.


@needs_real_interpreter
def test_timeout_partial_observation_is_persisted_as_partial_not_observed(
    tmp_path: Path,
) -> None:
    """The timeout path persists the numeric row as PARTIAL, keeping the
    reservation UNKNOWN instead of releasing holds on a partial total."""
    store = TaskStore(":memory:")
    store.create_task(title="t", executor_kind="opencode", model_profile_ref="m")
    task_id = store.list_tasks()[0].id

    marker = tmp_path / "child-finished.txt"
    parent, child = _write_parent(tmp_path, marker, emit_usage=True)
    result = _run(parent, child, marker, cwd=tmp_path, timeout=1)
    assert result.timed_out and result.cleanup_confirmed

    partial = oe._extract_usage_observations(
        result.stdout,
        task_id=task_id,
        execution_id="controlled-timeout",
        role="executor",
        fallback_model_id="fixture/model",
    )
    for observation in partial:
        if observation.get("status") == "OBSERVED":
            observation["status"] = "PARTIAL"
    oe._persist_usage_observations(store, task_id, partial)

    rows = store._conn.execute(
        "SELECT status FROM task_usage_observations WHERE task_id = ?", (task_id,)
    ).fetchall()
    assert [row["status"] for row in rows] == ["PARTIAL"]


@needs_real_interpreter
def test_normal_return_cleans_up_leftover_child(tmp_path: Path) -> None:
    """A parent that returns 0 while leaving a child running must have that
    child cleaned up before the call reports success."""
    child = tmp_path / "child.py"
    child.write_text(
        "import sys,time\n"
        "from pathlib import Path\n"
        "time.sleep(3)\n"
        "Path(sys.argv[1]).write_text('leftover child completed')\n",
        encoding="utf8",
    )
    marker = tmp_path / "leftover-child.txt"
    parent = tmp_path / "parent.py"
    parent.write_text(
        "import subprocess,sys\n"
        "subprocess.Popen([sys.executable,sys.argv[1],sys.argv[2]],"
        "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
        "print('parent returned normally')\n",
        encoding="utf8",
    )

    result = _run(parent, child, marker, cwd=tmp_path, timeout=10)

    assert result.timed_out is False
    assert result.cleanup_confirmed is True
    assert result.returncode == 0
    time.sleep(4)
    assert not marker.exists()


@needs_real_interpreter
def test_unconfirmed_cleanup_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When stop-and-confirm cannot prove the tree empty, the result must not
    claim cleanup (the executor then refuses artifact acceptance and keeps
    usage UNKNOWN)."""
    marker = tmp_path / "child-finished.txt"
    parent, child = _write_parent(tmp_path, marker)

    import reverse_agent.platform_v1.native_quota as native_quota

    def unconfirmed(proc, job):
        return False

    monkeypatch.setattr(native_quota, "stop_and_confirm", unconfirmed)

    result = _run(parent, child, marker, cwd=tmp_path, timeout=1)

    assert result.timed_out is True
    assert result.cleanup_confirmed is False


@needs_real_interpreter
def test_timeout_usage_accounting_stays_unknown(tmp_path: Path) -> None:
    """A wholly-OBSERVED row may not survive a timeout as a complete total:
    the executor downgrades it to PARTIAL, and the reservation reconciliation
    stays UNKNOWN. Cleanup uncertainty is enforced separately by the retry guard."""
    from reverse_agent.platform_v1.control_store import PlatformControlStore

    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    control = PlatformControlStore(store)
    task = store.create_task(title="t", executor_kind="opencode", model_profile_ref="m")

    window = control.activate_window(
        {
            "window_id": "owned-window",
            "policy_id": "fake",
            "policy_revision": 1,
            "owner_identity": "test",
            "starts_at": "2020-01-01T00:00:00Z",
            "expires_at": "2099-01-01T00:00:00Z",
            "repositories": [],
            "capabilities": ["execute_task"],
            "max_concurrent_tasks": 1,
            "max_tasks": 5,
        },
        confirmation="ACTIVATE",
    )
    conn = store._conn
    conn.execute(
        "INSERT INTO platform_coordinator_claims VALUES (?,?,?,?,?,?,?,?)",
        (task.id, window.id, "coordinator", 1, int(time.time() * 1000) + 60000, "ACTIVE", "now", "now"),
    )
    conn.execute(
        "INSERT INTO platform_budget_reservations "
        "(task_id,claim_epoch,window_id,reserved_token_units,reserved_cost_micro_units,state,"
        "created_at,updated_at,account_ref,binding_ref,quota_windows_json,estimate_json) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            task.id,
            1,
            window.id,
            1000,
            1000,
            "ACTIVE",
            "now",
            "now",
            "account",
            "fake-binding",
            json.dumps({"five_hour": 25, "weekly": 25}),
            json.dumps({"account_ref": "account", "estimate": {"model": "fake"}}),
        ),
    )
    conn.commit()

    # A PARTIAL row is the timeout-path artifact: numeric values are present but
    # must not be treated as a complete OBSERVED total.
    store.append_usage_observation(
        task.id,
        observation_id="partial-usage",
        execution_id=task.execution_id,
        role="executor",
        model_id="fixture/model",
        provider_id="fixture",
        source_kind="step_finish",
        source_id="controlled",
        status="PARTIAL",
        input_units=11,
        output_units=3,
        reasoning_units=1,
        cache_read_units=2,
        cache_write_units=0,
    )

    reservation_state = control._finalize_task_claim(
        window_id=window.id,
        task_id=task.id,
        owner="coordinator",
        epoch=1,
        claim_status="COMPLETE",
        count_completion=True,
        receipt_reason="controlled timeout partial usage",
        receipt_result="timeout",
    )

    assert reservation_state == "UNKNOWN"
    row = dict(
        store._conn.execute(
            "SELECT state, observed_token_units, observed_cost_micro_units "
            "FROM platform_budget_reservations WHERE task_id = ?",
            (task.id,),
        ).fetchone()
    )
    assert row["state"] == "UNKNOWN"
    assert row["observed_token_units"] is None
    assert row["observed_cost_micro_units"] is None


@needs_real_interpreter
def test_complete_observed_usage_reconciles_for_contrast(tmp_path: Path) -> None:
    """Contrast fixture: a wholly-OBSERVED row reconciles (RETCONCILED), proving
    the PARTIAL/UNKNOWN path above is what preserves the hold."""
    from reverse_agent.platform_v1.control_store import PlatformControlStore

    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    control = PlatformControlStore(store)
    task = store.create_task(title="t", executor_kind="opencode", model_profile_ref="m")

    window = control.activate_window(
        {
            "window_id": "owned-window",
            "policy_id": "fake",
            "policy_revision": 1,
            "owner_identity": "test",
            "starts_at": "2020-01-01T00:00:00Z",
            "expires_at": "2099-01-01T00:00:00Z",
            "repositories": [],
            "capabilities": ["execute_task"],
            "max_concurrent_tasks": 1,
            "max_tasks": 5,
        },
        confirmation="ACTIVATE",
    )
    conn = store._conn
    conn.execute(
        "INSERT INTO platform_coordinator_claims VALUES (?,?,?,?,?,?,?,?)",
        (task.id, window.id, "coordinator", 1, int(time.time() * 1000) + 60000, "ACTIVE", "now", "now"),
    )
    conn.execute(
        "INSERT INTO platform_budget_reservations "
        "(task_id,claim_epoch,window_id,reserved_token_units,reserved_cost_micro_units,state,"
        "created_at,updated_at,account_ref,binding_ref,quota_windows_json,estimate_json) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            task.id,
            1,
            window.id,
            1000,
            1000,
            "ACTIVE",
            "now",
            "now",
            "account",
            "fake-binding",
            json.dumps({"five_hour": 25, "weekly": 25}),
            json.dumps({"account_ref": "account", "estimate": {"model": "fake"}}),
        ),
    )
    conn.commit()

    store.append_usage_observation(
        task.id,
        observation_id="observed-usage",
        execution_id=task.execution_id,
        role="executor",
        model_id="fixture/model",
        provider_id="fixture",
        source_kind="assistant_message",
        source_id="controlled",
        status="OBSERVED",
        input_units=11,
        output_units=3,
        reasoning_units=1,
        cache_read_units=2,
        cache_write_units=0,
        cost_micro_units=0,
    )

    reservation_state = control._finalize_task_claim(
        window_id=window.id,
        task_id=task.id,
        owner="coordinator",
        epoch=1,
        claim_status="COMPLETE",
        count_completion=True,
        receipt_reason="controlled complete usage",
        receipt_result="success",
    )

    assert reservation_state == "RECONCILED"
