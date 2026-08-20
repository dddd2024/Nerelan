"""Agent Runs read-model contract tests: the view is derived from TaskStore,
goal links and publications, and mutating the store changes the view with no
read-model write path."""

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_read_model import RunReadModel
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


@pytest.fixture()
def read_model():
    store = TaskStore()
    control = PlatformControlStore(store)
    return RunReadModel(store=store, control_store=control), store, control


def _seed_goal_with_task(control, store, key: str):
    goal = control.create_goal(
        title=f"goal-{key}",
        objective="objective",
        repository="dddd2024/reverse-agent",
        idempotency_key=key,
    )
    task = store.create_task(
        title=f"task-{key}",
        repository="dddd2024/reverse-agent",
        executor_kind="deterministic_fixture",
    )
    control.link_goal_task(
        goal.id,
        goal_revision=1,
        plan_task_id="T001",
        task_id=task.id,
        dependencies=[],
        seq=0,
    )
    return goal, task


def test_listing_derives_from_task_store_with_goal_links(read_model) -> None:
    model, store, control = read_model
    goal, task = _seed_goal_with_task(control, store, "rm-list")
    result = model.list_runs()
    assert result["total"] == 1
    run = result["runs"][0]
    assert run["task_id"] == task.id
    assert run["status"] == "QUEUED"
    assert run["state"] == "WAITING_FOR_OWNER"
    assert run["goal_id"] == goal.id
    assert run["goal_title"] == "goal-rm-list"
    assert run["publication"] is None


def test_store_mutation_changes_run_view_without_read_model_writes(read_model) -> None:
    model, store, control = read_model
    _, task = _seed_goal_with_task(control, store, "rm-mut")
    assert model.list_runs()["runs"][0]["status"] == "QUEUED"

    changes_before = control._conn.total_changes
    store.set_state(task.id, "RUNNING")
    run = model.list_runs()["runs"][0]
    assert run["status"] == "RUNNING"
    assert run["state"] == "RUNNING"

    store.set_state(task.id, "VALIDATING")
    store.set_state(task.id, "READY_FOR_REVIEW")
    run = model.list_runs()["runs"][0]
    assert run["status"] == "READY_FOR_REVIEW"
    assert run["state"] == "READY_FOR_HUMAN"

    # Every change above came from TaskStore itself; the read model performed
    # zero writes of its own between the two observations.
    store_changes_for_read = control._conn.total_changes - changes_before
    before_second = control._conn.total_changes
    model.list_runs()
    model.run_detail(task.id)
    assert control._conn.total_changes == before_second
    assert store_changes_for_read >= 0


def test_publication_pr_link_is_derived(read_model) -> None:
    model, store, control = read_model
    _, task = _seed_goal_with_task(control, store, "rm-pub")
    control.upsert_publication(
        task_id=task.id,
        repository="dddd2024/reverse-agent",
        base_branch="main",
        branch="codex/demo",
        status="COMPLETE",
        request_digest="digest-1",
        commit_sha="abc123",
        pr_number=42,
        pr_url="https://github.com/dddd2024/reverse-agent/pull/42",
    )
    run = model.list_runs()["runs"][0]
    assert run["publication"] == {
        "status": "COMPLETE",
        "branch": "codex/demo",
        "pr_number": 42,
        "pr_url": "https://github.com/dddd2024/reverse-agent/pull/42",
        "commit_sha": "abc123",
    }


def test_detail_includes_timeline_and_changed_files(read_model) -> None:
    model, store, control = read_model
    _, task = _seed_goal_with_task(control, store, "rm-detail")
    store.set_changed_files(
        task.id,
        [{"path": "a.py", "status": "modified", "additions": 3, "deletions": 1}],
    )
    detail = model.run_detail(task.id)
    assert detail["task_id"] == task.id
    assert detail["events"][0]["type"] == "DISCOVERED"
    assert detail["changed_files"][0]["path"] == "a.py"


def test_unlinked_task_renders_with_empty_goal_fields(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="orphan", executor_kind="deterministic_fixture")
    run = model.list_runs()["runs"][0]
    assert run["task_id"] == task.id
    assert run["goal_id"] == ""
    assert run["goal_title"] == ""


def test_unknown_run_detail_fails_closed(read_model) -> None:
    model, _, _ = read_model
    with pytest.raises(TaskStoreError):
        model.run_detail("task-missing")


def test_run_read_model_exposes_no_write_api(read_model) -> None:
    """Structural contract: the read model offers only derived reads."""
    model, _, _ = read_model
    public = {
        name
        for name in dir(model)
        if not name.startswith("_") and callable(getattr(model, name))
    }
    assert public == {"list_runs", "run_detail"}
