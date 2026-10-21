"""Provider capacity/overload is transient availability, not capability evidence."""
import pytest

from reverse_agent.platform_v1 import goal_service as gs
from reverse_agent.platform_v1 import model_availability
from reverse_agent.platform_v1 import model_profiles
from reverse_agent.platform_v1.codex_protocol import CodexJsonl
from test_codex_protocol import START, wire
from test_contract_miss_fixup import case, destination, git, wrong_tree  # noqa: F401 (fixture)
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)
import reverse_agent.platform_v1.contract_recovery as recovery

LIVE = "Selected model is at capacity. Please try a different model."


@pytest.mark.parametrize("text, expected", [
    (LIVE, True), ("overloaded_error: Overloaded", True), ("api_error_529", True),
    ("503 Service Unavailable", True), ("The server is busy, try again later", True),
    ("usage limit reached", False), ("model_not_found", False), ("context limit reached", False),
    ("failed at app.py:529", False), ("HTTP 529", True), ("", False),
])
def test_overload_wording(text, expected):
    assert model_availability.provider_overloaded(text) is expected


def test_codex_capacity_terminal_failure_is_classified_transient():
    parser = CodexJsonl()
    parser.feed(wire(*START, {"type": "turn.failed", "error": {"message": LIVE}}))
    assert parser.finish().failure_classification == model_availability.OVERLOADED


def _fail_overloaded(store, task, root, *, classification="codex_turn_failed", age="2000-01-01T00:00:00Z"):
    store.add_event(task.id, event_type="WORKSPACE_READY", title="Workspace ready",
                    metadata={"execution_id": task.execution_id, "workspace": str(root)})
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification=?, failure_detail=?, "
                        "updated_at=? WHERE id=?", (classification, "Terminal: " + LIVE, age, task.id))
    store._conn.commit()


def test_overload_is_excluded_from_capability_profiles(case):
    root, _, store, _, _, _, _, task = case
    _fail_overloaded(store, task, root)
    profile = model_profiles.compute_agent_profiles(store)[task.binding_ref]
    assert profile["overloaded"] == 1
    assert profile["attempts"] == 0 and profile["failed"] == 0
    assert "codex_turn_failed" not in profile["failure_kinds"]


def test_overload_retries_same_binding_from_the_retained_tree(case, tmp_path):
    root, base, store, _, service, goal, _, task = case
    wrong_tree(root)
    _fail_overloaded(store, task, root)
    def forbidden(*args, **kwargs):
        raise AssertionError("overload must not run capability selection")
    service.task_resolver = forbidden
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == "transient_overload"
    retry = store.get_task(step["to_task_id"])
    assert (retry.binding_ref, retry.executor_kind) == (task.binding_ref, task.executor_kind)
    binding = recovery.recovery_input(retry)
    assert binding["source_task_id"] == task.id and "continue from them" in binding["feedback"]
    dest = destination(case, tmp_path)
    recovery.restore_failed_tree(store, retry.id, worktree=dest)
    assert (dest / "wrong_name.py").exists()
    assert git(dest, "rev-parse", "HEAD") == base


def test_overload_waits_for_backoff(case, monkeypatch):
    root, _, store, _, service, goal, _, task = case
    from datetime import datetime, timezone
    _fail_overloaded(store, task, root, age=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count
    monkeypatch.setattr(gs, "TRANSIENT_BACKOFF_SECONDS", 0)
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == "transient_overload"


def test_overload_without_worktree_still_retries_same_binding_from_base(case):
    root, _, store, _, service, goal, _, task = case
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='provider_overloaded', "
                        "failure_detail='overloaded', updated_at='2000-01-01T00:00:00Z' WHERE id=?", (task.id,))
    store._conn.commit()
    [step] = service.escalate_failed_tasks(goal.id)
    retry = store.get_task(step["to_task_id"])
    assert step["reason"] == "transient_overload" and retry.binding_ref == task.binding_ref
    assert recovery.recovery_input(retry) is None


def test_persistent_overload_falls_back_to_ordinary_routing(case, monkeypatch):
    root, _, store, control, service, goal, _, task = case
    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    _fail_overloaded(store, task, root)
    [step] = service.escalate_failed_tasks(goal.id) or [None]
    assert step is None or step["reason"] != "transient_overload"
