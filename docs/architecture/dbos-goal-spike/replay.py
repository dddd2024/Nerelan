"""Opt-in DBOS #1546 experiment. Uses only fresh local files and fixture executors."""

from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from uuid import uuid4

from dbos import DBOS, SetWorkflowID
from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "platform_v1"))

import test_chaos_liveness as chaos
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.durable_execution import DurableExecutionService
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import DeterministicFixtureExecutor, ExecutorRouter

WORKFLOW = "goal-engine-spike"
DATABASE = "tasks.sqlite3"
CRASH = 73
WORKSPACES = Path("workspaces").resolve()
FIXTURE_PREFIX = "nerelan-dbos-goal-replay-"
SCENARIOS = ("reroute", "unknown", "unjournaled")


class CrashAfterFixtureEffect(DeterministicFixtureExecutor):
    def execute(self, *args, **kwargs):
        result = super().execute(*args, **kwargs)
        assert result.success
        os._exit(CRASH)


def execute_fixture(store, task_id, *, crash=False):
    # The fixture executor may replace an existing workspace. Require a new
    # directory under this experiment's workspace root before dispatch.
    workspace = (WORKSPACES / task_id).resolve()
    assert workspace.parent == WORKSPACES and not workspace.exists()
    router = ExecutorRouter()
    if crash:
        router.replace("deterministic_fixture", CrashAfterFixtureEffect)
    service = DurableExecutionService(
        store=store, router=router, execution_authority_sha=chaos.BASE, planning_sha=chaos.BASE,
    )
    assert service.execute_durable_single(task_id, workspace_root=str(WORKSPACES)).success


@DBOS.step()
def plan():
    with MonkeyPatch.context() as patch:
        patch.setattr(chaos, "TaskStore", lambda _path: TaskStore(DATABASE))
        bed = chaos.Bed(patch)
        with closing(bed.store._conn):
            goal_id = bed.add_goal("isolated-dbos", [], steps=1)
            bed.make_continuous()
            return goal_id


@DBOS.step()
def unjournaled_review():
    # A receiver that commits a review before DBOS records the step result.
    with closing(sqlite3.connect("receiver.sqlite3")) as conn, conn:
        conn.execute("CREATE TABLE IF NOT EXISTS calls (role TEXT NOT NULL)")
        conn.execute("INSERT INTO calls VALUES ('review')")
        [count] = conn.execute("SELECT COUNT(*) FROM calls").fetchone()
    if count == 1:
        os._exit(CRASH)
    return {"state": "REVIEW_REPLY", "calls": count}


@DBOS.step()
def unknown_effect():
    store = TaskStore(DATABASE)
    with closing(store._conn) as conn:
        task = fixture_task(store, "fixture-unknown")
        pending = conn.execute(
            "SELECT 1 FROM durable_external_operations WHERE task_id=? AND state='PENDING'",
            (task.id,),
        ).fetchone()
        if pending:
            return {"state": "HOLD", "task_id": task.id}
        execute_fixture(store, task.id, crash=True)
        raise AssertionError("expected process crash before receipt settlement")


@DBOS.step()
def implement(goal_id):
    store = TaskStore(DATABASE)
    with closing(store._conn) as conn:
        control = PlatformControlStore(store)
        [link] = control.list_goal_tasks(goal_id)
        task = store.get_task(link["task_id"])
        if task.binding_ref == chaos.BINDINGS[0] and task.status == "QUEUED":
            # Inject a settled refusal using the same #1696 scenario as the
            # test bed. Crash after the fault is durable, before DBOS commits.
            chaos.BY_NAME["rate_limit_429"].apply(store, task)
            conn.commit()
            os._exit(CRASH)
        if task.status == "FAILED":
            goals = GoalService(store=store, control_store=control, task_resolver=chaos._resolver)
            [replacement] = goals.escalate_failed_tasks(goal_id)
            task = store.get_task(replacement["to_task_id"])
            assert task.binding_ref == chaos.BINDINGS[1]
        # Named bindings are synthetic. Exercise the existing executor through
        # an unbound fixture task, then record the injected adapter's result.
        execute_fixture(store, fixture_task(store, "fixture-implementation").id)
        chaos._finish(store, task, "READY_FOR_REVIEW", "")
        conn.commit()
        assert control.refresh_goal_status(goal_id).status == "COMPLETED"
        return {"state": "IMPLEMENTED", "binding": task.binding_ref}


def fixture_task(store, label):
    return store.create_task(title=label, repository="dddd2024/Nerelan", executor_kind="deterministic_fixture",
                             idempotency_key=f"{DBOS.workflow_id}:{label}")


@DBOS.step()
def fixture_step(label):
    store = TaskStore(DATABASE)
    with closing(store._conn):
        execute_fixture(store, fixture_task(store, label).id)
        return label


@DBOS.workflow()
def goal_workflow(scenario):
    if scenario == "unjournaled":
        return unjournaled_review()
    if scenario == "unknown":
        return unknown_effect()
    result = implement(plan())
    # Exercise the retry/repair shape with deterministic checking. These labels
    # are fixture outcomes and never authorize a real review or publication.
    fixture_step("fixture-review-reject")
    fixture_step("fixture-repair")
    review = fixture_step("fixture-refreshed-review")
    return {**result, "last_step": review}


def worker(action, scenario):
    cwd = Path.cwd().resolve()
    root = cwd.parent
    marker = root / "driver.marker"
    token = os.environ.get("NERELAN_DBOS_FIXTURE_TOKEN")
    if (action not in {"start", "resume"} or scenario not in SCENARIOS or cwd.name != scenario
            or root.parent != Path(tempfile.gettempdir()).resolve()
            or not root.name.startswith(FIXTURE_PREFIX)
            or not token or not marker.is_file() or marker.read_text(encoding="ascii") != token
            or (action == "start" and any(cwd.iterdir()))):
        raise SystemExit("Run the experiment without arguments to allocate isolated fixtures.")
    DBOS(config={
        "name": "nerelan-goal-recovery-spike",
        "system_database_url": "sqlite:///dbos.sqlite3",
        "application_version": "spike-1",
        "executor_id": "isolated",
    })
    DBOS.launch()
    try:
        if action == "start":
            with SetWorkflowID(WORKFLOW):
                goal_workflow(scenario)
        else:
            print("RESULT " + json.dumps(DBOS.retrieve_workflow(WORKFLOW).get_result()), flush=True)
    finally:
        DBOS.destroy()


def verify():
    root = Path(tempfile.mkdtemp(prefix=FIXTURE_PREFIX))
    token = uuid4().hex
    (root / "driver.marker").write_text(token, encoding="ascii")
    # Discard any inherited repository target or remote DBOS control plane.
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(("GIT_", "DBOS_"))}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, NERELAN_DBOS_FIXTURE_TOKEN=token)
    print(f"Fixtures: {root}", flush=True)
    for scenario in SCENARIOS:
        directory = root / scenario
        directory.mkdir()
        receipts = []
        for action in ("start", "resume", "resume"):
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), action, scenario],
                cwd=directory, env=env, capture_output=True, text=True, timeout=60,
            )
            assert result.returncode == (CRASH if action == "start" else 0), (
                scenario, action, result.stdout, "\n".join(result.stderr.splitlines()[-24:]),
            )
            if action == "resume":
                [line] = [line for line in result.stdout.splitlines() if line.startswith("RESULT ")]
                receipts.append(json.loads(line.removeprefix("RESULT ")))
        assert receipts[0] == receipts[1]
        if scenario == "unjournaled":
            with closing(sqlite3.connect(directory / "receiver.sqlite3")) as conn:
                [count] = conn.execute("SELECT COUNT(*) FROM calls").fetchone()
            assert receipts[0] == {"state": "REVIEW_REPLY", "calls": 2} and count == 2
            print(f"{scenario}: committed review effect occurred {count} times")
            continue
        with closing(sqlite3.connect(directory / DATABASE)) as conn:
            external = conn.execute("SELECT state FROM durable_external_operations").fetchall()
            attempts = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if scenario == "unknown":
            assert receipts[0]["state"] == "HOLD" and external == [("PENDING",)]
            assert attempts == 1
            assert (directory / "workspaces" / receipts[0]["task_id"] / "fixture.txt").is_file()
        else:
            store = TaskStore(str(directory / DATABASE))
            with closing(store._conn):
                control = PlatformControlStore(store)
                [goal] = control.list_goals()
                escalations = len(control.list_task_escalations(goal.id))
            assert receipts[0] == {"state": "IMPLEMENTED", "binding": "bind-b",
                                   "last_step": "fixture-refreshed-review"}
            assert escalations == 1 and attempts == 6
            assert external == [("SUCCESS",)] * 4
        print(f"{scenario}: {receipts[0]}, attempts={attempts}, external={external}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        verify()
    elif len(sys.argv) == 3:
        worker(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit("Run the experiment without arguments to allocate isolated fixtures.")
