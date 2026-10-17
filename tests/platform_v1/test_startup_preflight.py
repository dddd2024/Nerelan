"""Provider-free restart planning proof against a *real* TaskStore schema."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.startup_preflight import (
    ClaimState, WindowState, assess_boot_readiness, inspect_task_store,
)

NOW = datetime(2026, 10, 16, 10, tzinfo=timezone.utc)


def window(status="ACTIVE", start=-1, end=3, name="win"):
    return WindowState(
        name, status, (NOW+timedelta(hours=start)).isoformat(),
        (NOW+timedelta(hours=end)).isoformat())


def evaluate(windows=None, claims=None, counts=None):
    return assess_boot_readiness(
        windows=windows if windows is not None else [window()],
        claims=claims or [], task_counts=counts or {}, now=NOW)


def test_no_window_is_idle_not_execution_permission():
    x=evaluate(windows=[window("EXPIRED")], counts={"QUEUED":9})
    assert x["state"]=="HOST_IDLE_NO_WINDOW"
    assert x["dispatch_permitted"] is False
    assert x["auto_extend_window"] is False
    assert x["queued_tasks"]==9


def test_completed_historical_window_is_valid_but_not_authority():
    x=evaluate(windows=[window("COMPLETED", start=-6, end=-4)])
    assert x["state"]=="HOST_IDLE_NO_WINDOW"
    assert x["dispatch_permitted"] is False
    assert x["required_next_action"]=="WAIT_FOR_OWNER_WINDOW"


def test_completed_history_coexists_with_current_window_without_granting_dispatch():
    x=evaluate(windows=[window("COMPLETED", start=-6, end=-4, name="older"), window()])
    assert x["state"]=="READY_FOR_HOST_RECONCILIATION"
    assert x["dispatch_permitted"] is False
    assert x["active_window_id"]=="win"


def test_single_active_window_requires_separate_fenced_reconciliation():
    x=evaluate()
    assert x["state"]=="READY_FOR_HOST_RECONCILIATION"
    assert x["dispatch_permitted"] is False
    assert x["required_next_action"]=="RUN_EXISTING_FENCED_RECONCILER"


def test_window_expired_but_still_active_must_not_resume():
    x=evaluate(windows=[window(end=-.1)])
    assert x["state"]=="HOLD_WINDOW_TIME_MISMATCH"
    assert not x["dispatch_permitted"]


def test_old_active_claim_requires_remote_job_reconciliation_even_after_lease_expiry():
    x=evaluate(claims=[ClaimState("gpu-job-1","win","ACTIVE")])
    assert x["state"]=="HOLD_REMOTE_RECONCILIATION"
    assert x["required_next_action"]=="VERIFY_REMOTE_JOB_IDENTITIES"


def test_stopped_window_with_active_claim_is_orphan():
    x=evaluate(windows=[window("STOPPED")],
               claims=[ClaimState("task","win","ACTIVE")])
    assert x["state"]=="HOLD_ORPHANED_CLAIMS"


def test_claim_for_another_window_blocks_new_window_dispatch():
    x=evaluate(claims=[ClaimState("task","old-window","ACTIVE")])
    assert x["state"]=="HOLD_ORPHANED_CLAIMS"


def test_interrupted_task_blocks_without_lease():
    x=evaluate(counts={"QUEUED":3,"INTERRUPTED":1})
    assert x["state"]=="HOLD_INTERRUPTED_TASKS"
    assert not x["dispatch_permitted"]


def test_multiple_active_windows_are_ambiguous():
    x=evaluate(windows=[window(),window(name="other")])
    assert x["state"]=="UNKNOWN"
    assert x["reason"]=="multiple_active_windows"


@pytest.mark.parametrize("windows,claims,counts", [
    ([window(start=5,end=1)],[],{}),
    ([WindowState("win","ACTIVE","bad","2026-10-17T10:00:00Z")],[],{}),
    ([WindowState("win","ACTIVE","2026-10-16T09:00:00","2026-10-17T09:00:00Z")],[],{}),
    ([window(),window()],[],{}),
    ([WindowState("win","UNKNOWN",window().starts_at,window().expires_at)],[],{}),
    ([window()],[ClaimState("job","win","MYSTERY")],{}),
    ([window()],[],{"READY_FOR_REVIEW":-2}),
    ([window()],[],{"SECRETS":1}),
    ([window()],[],{"QUEUED":True}),
])
def test_contradictions_hold(windows,claims,counts):
    x=evaluate(windows=windows,claims=claims,counts=counts)
    assert x["state"]=="UNKNOWN"
    assert x["dispatch_permitted"] is False


def test_naive_clock_refuses_dispatch():
    x=assess_boot_readiness(windows=[window()], claims=[],
                            task_counts={},now=datetime(2026,10,16))
    assert x["state"]=="UNKNOWN"


def test_actual_sqlite_taskstore_read_only_and_no_new_authority(tmp_path):
    path=tmp_path/"tasks.sqlite3"
    store=TaskStore(str(path))
    control=PlatformControlStore(store)
    # Exercise actual schema instead of a hand-built fake SQLite table.
    stored_before=path.read_bytes()
    digest_before=sha256(stored_before).hexdigest()
    x=inspect_task_store(path,now=NOW)
    assert x["state"]=="HOST_IDLE_NO_WINDOW"
    assert x["dispatch_permitted"] is False
    assert sha256(path.read_bytes()).hexdigest()==digest_before
    assert not (tmp_path/"tasks.sqlite3-journal").exists()
    store._conn.close()


def test_cli_is_read_only_with_real_sqlite_and_restarts_same_result(tmp_path):
    path=tmp_path/"real.sqlite3"
    store=TaskStore(str(path))
    PlatformControlStore(store)  # Creates the real autonomy tables.
    store._conn.close()
    outputs=[]
    for _ in range(2):
        proc=subprocess.run(
            [sys.executable,"-m","reverse_agent.platform_v1.startup_preflight",
             "--db",str(path)],text=True,capture_output=True,timeout=10)
        assert proc.returncode==0,proc.stderr
        outputs.append(proc.stdout)
    assert outputs[0]==outputs[1]
    assert '"HOST_IDLE_NO_WINDOW"' in outputs[0]


def test_no_database_is_unknown_without_creation(tmp_path):
    p=tmp_path/"absent.sqlite3"
    assert inspect_task_store(p)["state"]=="UNKNOWN"
    assert not p.exists()