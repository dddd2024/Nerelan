"""Manual acceptance: kill -9 an executor, recover the run, prove the invariants.

This is the end-to-end companion to `tests/platform_v1/test_lease_invariants.py`.
The unit suite proves the *rules*; this script proves them across a real process
boundary, which is the only way to reproduce "the old executor did not die, it
just went quiet".

What it actually does:

1. makes a temporary task database and a task in a real filesystem workspace;
2. starts a **child process** that claims a durable lease, writes a workspace
   marker and the lease token, then blocks forever;
3. kills that child with an unhandleable kill (``SIGKILL``/``TerminateProcess``);
4. recovers the run as a second owner and asserts:

   * ``I2``  the epoch advanced by exactly one;
   * ``I1``  the dead owner's lease validation is now fenced;
   * ``F1``  the dead owner's fenced evidence write is refused *and* nothing lands;
   * ``F1``  the workspace token belongs to the new owner after takeover;
   * ``I1``  no second run can be claimed for the same task.

Exit codes: ``0`` all invariants held, ``1`` an invariant was violated,
``2`` the harness itself could not run. Nothing here touches the real platform
directory or makes a model call.

    python scripts/lease_kill9_check.py            # self-cleaning
    python scripts/lease_kill9_check.py --keep     # keep the temp directory
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

READY_PREFIX = "LEASE_READY "
CHILD_TIMEOUT_SECONDS = 60.0

CHILD = r"""
import json, os, sys, time
from pathlib import Path
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.workspace_fence import fence_workspace

db_path, task_id, worktree = sys.argv[1], sys.argv[2], sys.argv[3]
store = TaskStore(db_path=db_path)
task = store.get_task(task_id)
lease = store._acquire_durable_lease(
    task_id=task_id, execution_id=task.execution_id, lease_owner="owner-old",
    expiry_ms=600000, task_status="QUEUED")
Path(worktree, "old-executor-touch.txt").write_text("written by the executor that dies\n")
fence_workspace(Path(worktree), run_id=lease.run_id, owner=lease.owner, epoch=lease.epoch)
print("LEASE_READY " + json.dumps(
    {"run_id": lease.run_id, "owner": lease.owner, "epoch": lease.epoch}), flush=True)
time.sleep(3600)
"""


def _store(db_path: str):
    from reverse_agent.platform_v1.run_store import TaskStore
    return TaskStore(db_path=db_path)


def _start_child(db_path: str, task_id: str, worktree: Path) -> tuple[subprocess.Popen, dict]:
    env = dict(os.environ)
    env["REVERSE_AGENT_WORKSPACE_FENCE"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.Popen(  # noqa: S603 - fixed argv, no shell, this interpreter
        [sys.executable, "-c", CHILD, db_path, task_id, str(worktree)],
        cwd=str(REPO_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, shell=False)
    deadline = time.monotonic() + CHILD_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        line = proc.stdout.readline() if proc.stdout else ""
        if line.startswith(READY_PREFIX):
            return proc, json.loads(line[len(READY_PREFIX):])
        if proc.poll() is not None:
            stderr = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(f"child exited early ({proc.returncode}): {stderr[-800:]}")
    proc.kill()
    raise RuntimeError("child never reported readiness")


def run(keep: bool = False, root: Path | None = None) -> dict:
    from reverse_agent.platform_v1.workspace_fence import read_token

    workdir = Path(root or tempfile.mkdtemp(prefix="nerelan-kill9-"))
    workdir.mkdir(parents=True, exist_ok=True)
    db_path = str(workdir / "tasks.sqlite3")
    worktree = workdir / "worktree"
    worktree.mkdir()

    results: dict[str, object] = {}
    verdict = {"workdir": str(workdir), "checks": results, "ok": False}
    try:
        store = _store(db_path)
        task = store.create_task(title="kill -9 probe", executor_kind="opencode",
                                 binding_ref="b", repository="o/r", orchestration_mode="single")

        child, lease = _start_child(db_path, task.id, worktree)
        time.sleep(0.5)  # let the marker + token flush before the kill
        killed_at = time.time()
        child.kill()  # unhandleable: no cleanup handler in the child can run
        child.wait(timeout=30)
        results["child_killed_ms"] = int((time.time() - killed_at) * 1000)
        results["child_returncode"] = child.returncode
        results["marker_written_before_kill"] = (worktree / "old-executor-touch.txt").exists()

        # The crash the coordinator would eventually observe.
        store._conn.execute("UPDATE tasks SET status='INTERRUPTED' WHERE id=?", (task.id,))
        store._conn.execute("UPDATE durable_runs SET recovery_classification='interrupted', "
                            "lease_expiry_ms=1 WHERE run_id=?", (lease["run_id"],))
        store._conn.commit()

        recovered = store._recover_durable_lease(lease["run_id"], "owner-new",
                                                 require_interrupted=True)
        results["epoch_advanced_by_one"] = recovered.epoch == lease["epoch"] + 1

        try:
            store._validate_durable_lease(lease["run_id"], "owner-old", lease["epoch"])
            results["old_owner_fenced"] = False
        except Exception as exc:  # noqa: BLE001 - the fence is the expected outcome
            results["old_owner_fenced"] = "lease_fenced" in str(exc)

        try:
            store._fenced_add_evidence(
                lease["run_id"], task.id, category="probe", label="from-dead-owner",
                value="should not land", status="ACCEPTED",
                owner="owner-old", epoch=lease["epoch"])
            results["dead_owner_write_refused"] = False
        except Exception as exc:  # noqa: BLE001
            results["dead_owner_write_refused"] = "fenc" in str(exc).lower()
        labels = [entry.get("label") for entry in store.get_task(task.id).evidence_refs]
        results["dead_owner_evidence_absent"] = "from-dead-owner" not in labels

        # Workspace takeover: the new epoch claims the worktree the dead one held.
        from reverse_agent.platform_v1.durable_execution import DurableExecutionService
        from reverse_agent.platform_v1.task_runtime import ExecutorRouter
        service = DurableExecutionService(store=store, router=ExecutorRouter(),
                                          execution_authority_sha="probe", planning_sha="probe")
        os.environ["REVERSE_AGENT_WORKSPACE_FENCE"] = "1"
        service._fence_workspace(worktree, recovered)
        token = read_token(worktree)
        results["workspace_token_owner"] = token.owner if token else None
        results["workspace_taken_over"] = bool(token and token.owner == "owner-new"
                                              and token.epoch == recovered.epoch)

        try:
            store._acquire_durable_lease(task_id=task.id, execution_id=task.execution_id,
                                         lease_owner="owner-third", expiry_ms=600000)
            results["no_second_run"] = False
        except Exception as exc:  # noqa: BLE001
            results["no_second_run"] = "durable_run_already_active" in str(exc)

        verdict["ok"] = all(bool(value) for key, value in results.items()
                            if isinstance(value, bool))
    except Exception as exc:  # noqa: BLE001 - the harness reports, never raises
        verdict["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if not keep:
            shutil.rmtree(workdir, ignore_errors=True)
            verdict["workdir"] = ""
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="kill -9 recovery acceptance (manual, no CI).")
    parser.add_argument("--keep", action="store_true", help="keep the temporary workspace")
    parser.add_argument("--json", action="store_true", help="print only the JSON verdict")
    args = parser.parse_args(argv)

    verdict = run(keep=args.keep)
    if args.json:
        print(json.dumps(verdict, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for name, value in (verdict.get("checks") or {}).items():
            mark = "ok  " if value is True or isinstance(value, (int, str)) and value not in (None, False) else "FAIL"
            print(f"{mark} {name}: {value}")
        if verdict.get("error"):
            print(f"error {verdict['error']}")
        print("VERDICT:", "PASS" if verdict["ok"] else "FAIL")
    if verdict.get("error"):
        return 2
    return 0 if verdict["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
