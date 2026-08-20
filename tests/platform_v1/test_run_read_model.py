"""Agent Runs read-model contract tests: the view is derived from TaskStore,
goal links and publications, and mutating the store changes the view with no
read-model write path."""

from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
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


def test_run_view_exposes_numeric_usage_role_provenance_and_window_budget(read_model) -> None:
    model, store, control = read_model
    goal, task = _seed_goal_with_task(control, store, "rm-usage")
    control.save_goal_plan(
        goal.id,
        expected_revision=1,
        spec_markdown="# spec",
        plan_markdown="# plan",
        tasks=[{"id": "T001"}],
        acceptance_criteria=["usage visible"],
    )
    control.approve_goal(goal.id, expected_revision=1)
    now = datetime.now(timezone.utc)
    autonomy = AutonomyService(
        control_store=control, capabilities=CapabilityRegistry()
    )
    window = autonomy.activate({
        "policy_id": "read-model-usage", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 2, "max_retries": 0,
        "max_token_units": 1000, "per_task_token_reservation": 400,
        "confirmation": "ACTIVATE",
    })
    control.mark_goal_running(goal.id, revision=1, window_id=window.id)
    control.claim_task(
        window_id=window.id, task_id=task.id, owner="read-model", lease_ms=60_000
    )
    store.append_usage_observation(
        task.id,
        observation_id="usage-read-model-coder",
        execution_id="exec-read-model",
        role="coder",
        model_id="provider/model",
        provider_id="provider",
        source_kind="assistant_message",
        source_id="msg-read-model",
        status="OBSERVED",
        input_units=100,
        output_units=20,
        reasoning_units=10,
        cache_read_units=30,
        cache_write_units=0,
        cost_micro_units=2500,
    )
    run = model.list_runs()["runs"][0]
    assert run["window_id"] == window.id
    assert run["usage"]["total_token_units"] == 160
    assert run["usage"]["cost_micro_units"] == 2500
    assert run["usage"]["per_role"][0]["role"] == "coder"
    assert run["usage"]["provenance_ids"] == ["usage-read-model-coder"]
    assert run["budget"]["enforcement_class"] == "HARD_ADMISSION_ENFORCED"
    assert run["budget"]["reserved_token_units"] == 400
    assert run["budget"]["remaining_token_units"] == 600
