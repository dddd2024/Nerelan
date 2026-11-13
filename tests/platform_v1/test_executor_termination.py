"""An agent the machine stopped (shutdown, closed console) is interrupted, not failed."""
import pytest

from reverse_agent.platform_v1 import goal_service as gs
from reverse_agent.platform_v1 import model_availability
from reverse_agent.platform_v1 import model_profiles
from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor
from test_contract_miss_fixup import case, destination, git, wrong_tree  # noqa: F401 (fixture)
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)
import reverse_agent.platform_v1.contract_recovery as recovery

TERMINATED = model_availability.EXECUTOR_TERMINATED
RETRY_REASON = f"{gs.HOST_RETRY_REASON}:{TERMINATED}"
# Seen on the run host 2026-11-12: OpenCode killed by a Start-menu shutdown.
SHUTDOWN_EXIT = 1073807364


@pytest.mark.parametrize("exit_code", [SHUTDOWN_EXIT, 0x40010004, 0xC000013A, -1073741510])
def test_external_termination_exit_codes_are_classified(exit_code):
    executor = OpenCodeExecutor(model_id="fixture/model")
    assert executor._classify_exit(exit_code, []) == TERMINATED


@pytest.mark.parametrize("exit_code", [1, 2, 3221225477, 124, 127])
def test_ordinary_exit_codes_are_not_termination(exit_code):
    executor = OpenCodeExecutor(model_id="fixture/model")
    assert executor._classify_exit(exit_code, []) != TERMINATED


def _fail_terminated(store, task, root, *, age="2000-01-01T00:00:00Z"):
    store.add_event(task.id, event_type="WORKSPACE_READY", title="Workspace ready",
                    metadata={"execution_id": task.execution_id, "workspace": str(root)})
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification=?, failure_detail=?, "
                        "updated_at=? WHERE id=?",
                        (TERMINATED, f"opencode_nonzero:exit={SHUTDOWN_EXIT}:{TERMINATED}", age, task.id))
    store._conn.commit()


def test_termination_is_not_capability_evidence(case):
    root, _, store, _, _, _, _, task = case
    _fail_terminated(store, task, root)
    profile = model_profiles.compute_agent_profiles(store)[task.binding_ref]
    assert profile["attempts"] == 0 and profile["failed"] == 0
    assert TERMINATED not in profile["failure_kinds"]


def test_termination_resumes_same_binding_from_the_retained_tree(case, tmp_path):
    root, base, store, _, service, goal, _, task = case
    wrong_tree(root)
    store.add_event(task.id, event_type="MODEL_SELECTED", title="Model selected", description="fixture",
                    metadata={"binding_ref": task.binding_ref, "reason": "fixture", "context_window": 128000,
                              "context_need": 24000})
    _fail_terminated(store, task, root)

    def forbidden(*args, **kwargs):
        raise AssertionError("a stopped agent must not run capability selection")
    service.task_resolver = forbidden
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == RETRY_REASON
    retry = store.get_task(step["to_task_id"])
    assert (retry.binding_ref, retry.executor_kind) == (task.binding_ref, task.executor_kind)
    binding = recovery.recovery_input(retry)
    assert binding["source_task_id"] == task.id
    assert "machine stopped" in binding["feedback"] and "continue from them" in binding["feedback"]
    events = store.get_events(retry.id)
    assert any(e.type == "VALIDATED" and e.title == "Retry after the agent was stopped" for e in events)
    dest = destination(case, tmp_path)
    recovery.restore_failed_tree(store, retry.id, worktree=dest)
    assert (dest / "wrong_name.py").exists()
    assert git(dest, "rev-parse", "HEAD") == base


def test_termination_waits_for_backoff(case, monkeypatch):
    root, _, store, _, service, goal, _, task = case
    from datetime import datetime, timezone
    _fail_terminated(store, task, root, age=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count
    monkeypatch.setattr(gs, "TRANSIENT_BACKOFF_SECONDS", 0)
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == RETRY_REASON


def test_repeated_termination_falls_back_to_ordinary_routing(case, monkeypatch):
    root, _, store, _, service, goal, _, task = case
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    _fail_terminated(store, task, root)
    [step] = service.escalate_failed_tasks(goal.id) or [None]
    assert step is None or step["reason"] != RETRY_REASON
