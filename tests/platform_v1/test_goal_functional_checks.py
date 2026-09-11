"""Goal review and atomic launch bind selected checks to SQLite task identity."""
from datetime import datetime, timedelta, timezone
import subprocess

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.functional_validation import load_contract
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


@pytest.fixture
def goal_checks(tmp_path, monkeypatch):
    root = tmp_path / "source"
    root.mkdir()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], encoding="utf-8").strip()
    git("init", "-q")
    git("config", "user.name", "Functional acceptance")
    git("config", "user.email", "fixture@example.invalid")
    git("remote", "add", "origin", "https://github.com/owner/functional.git")
    (root / "app.py").write_text("value = 1\n", encoding="utf-8")
    (root / "test_app.py").write_text("from app import value\ndef test_requested():\n    assert value == 2\n", encoding="utf-8")
    (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    git("add", "--", "app.py", "test_app.py", ".gitignore")
    git("commit", "-q", "-m", "approved acceptance base")
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(root))
    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    control = PlatformControlStore(store)
    service = GoalService(store=store, control_store=control)
    goal = service.create({"objective": "Implement value two", "repository": "owner/functional",
                           "idempotency_key": "functional", "executor_kind": "opencode", "orchestration_mode": "single",
                           "binding_ref": "local-test-binding"})
    now = datetime.now(timezone.utc)
    window = AutonomyService(control_store=control, capabilities=CapabilityRegistry()).activate({
        "policy_id": "functional-policy", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": [goal.repository], "capabilities": ["execute_task", "validate_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1, "confirmation": "ACTIVATE"})
    yield root, git("rev-parse", "HEAD"), store, control, service, goal, window
    store._conn.close()


def planned_check(task_id="T001", directory="."):
    return {"id": task_id, "title": "Implement value two", "instruction": "Make value equal two",
            "validation_checks": [{"profile_id": "python_pytest", "working_directory": directory}]}


def launch_checks(fixture):
    _, _, _, _, service, goal, window = fixture
    planned = service.plan(goal.id, expected_revision=goal.revision, tasks=[planned_check()]).goal
    service.approve(goal.id, expected_revision=planned.revision)
    return service.launch(goal.id, expected_revision=planned.revision, window_id=window.id)


def test_approved_check_contract_survives_duplicate_launch_and_reopen(goal_checks):
    _, base, store, control, service, _, window = goal_checks
    launched = launch_checks(goal_checks)
    task_id = control.list_goal_tasks(launched.id)[0]["task_id"]
    contract = load_contract(store.get_task(task_id))
    assert contract["base_commit"] == base and contract["goal_artifact_digest"] == launched.artifact_digest
    assert contract["goal_revision"] == launched.revision and contract["goal_id"] == launched.id
    assert "python_pytest" in launched.plan_markdown
    assert service.launch(launched.id, expected_revision=launched.revision, window_id=window.id) == launched
    assert store.count_tasks() == 1 and len(store.get_task(task_id).evidence_refs) == 1
    reopened = TaskStore(store.db_path)
    try:
        assert load_contract(reopened.get_task(task_id)) == contract
    finally:
        reopened._conn.close()


def test_check_edit_invalidates_approval_and_contract_follows_new_revision(goal_checks):
    _, _, store, control, service, goal, window = goal_checks
    first = service.plan(goal.id, expected_revision=1, tasks=[planned_check()]).goal
    service.approve(goal.id, expected_revision=first.revision)
    with pytest.raises(TaskStoreError, match="goal_revision_or_state_mismatch"):
        service.plan(goal.id, expected_revision=first.revision, tasks=[planned_check(directory="tests")])
    amended = service.amend(goal.id, expected_revision=first.revision, objective=goal.objective + " with nested tests")
    revised = service.plan(goal.id, expected_revision=amended.revision, tasks=[planned_check(directory="tests")]).goal
    assert revised.revision == first.revision + 1 and revised.artifact_digest != first.artifact_digest
    with pytest.raises(TaskStoreError):
        service.launch(goal.id, expected_revision=first.revision, window_id=window.id)
    assert store.count_tasks() == 0
    service.approve(goal.id, expected_revision=revised.revision)
    service.launch(goal.id, expected_revision=revised.revision, window_id=window.id)
    task = store.get_task(control.list_goal_tasks(goal.id)[0]["task_id"])
    assert load_contract(task)["checks"] == [{"profile_id": "python_pytest", "working_directory": "tests"}]


def test_contract_persistence_failure_rolls_back_entire_launch(goal_checks, monkeypatch):
    _, _, store, control, service, goal, window = goal_checks
    service.plan(goal.id, expected_revision=1, tasks=[planned_check("A"), planned_check("B")])
    service.approve(goal.id, expected_revision=1)
    original = store.add_evidence
    calls = []
    def fail_second(*args, **kwargs):
        calls.append(args)
        if len(calls) == 2:
            raise TaskStoreError("fixture_contract_write_failure")
        return original(*args, **kwargs)
    monkeypatch.setattr(store, "add_evidence", fail_second)
    with pytest.raises(TaskStoreError, match="fixture_contract_write_failure"):
        service.launch(goal.id, expected_revision=1, window_id=window.id)
    assert store.count_tasks() == 0 and control.list_goal_tasks(goal.id) == ()
    assert control.get_goal(goal.id).status == "APPROVED"
    assert store._conn.execute("SELECT count(*) FROM task_evidence").fetchone()[0] == 0
    monkeypatch.setattr(store, "add_evidence", original)
    service.launch(goal.id, expected_revision=1, window_id=window.id)
    assert store.count_tasks() == 2
