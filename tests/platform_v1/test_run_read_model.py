"""Agent Runs read-model contract tests: the view is derived from TaskStore,
goal links and publications, and mutating the store changes the view with no
read-model write path."""

from dataclasses import fields
from datetime import datetime, timedelta, timezone
import json

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_read_model import MAX_DETAIL_EVENTS, RunReadModel
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
    assert run["stage"] == "PUBLISH"
    assert model.run_detail(task.id)["events"][0]["stage"] == "PLAN"


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


def test_durable_observation_is_bounded_and_read_only(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(
        title="bounded durable observation",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="obs-test",
        expiry_ms=60_000,
    )
    before = store._conn.total_changes
    observation = store.get_latest_durable_run_observation(task.id)
    assert store._conn.total_changes == before
    assert observation is not None
    assert {field.name for field in fields(observation)} == {
        "run_id", "execution_id", "current_role", "role_attempt",
        "accepted_checkpoint", "heartbeat_at_ms", "lease_expiry_ms",
        "recovery_classification", "interrupted_at", "updated_at",
    }
    assert not hasattr(observation, "worktree_path")
    assert not hasattr(observation, "checkpoint_db_path")
    assert model.list_runs()["total"] == 1
    assert store._get_durable_run(lease.run_id).run_id == observation.run_id


def test_structured_activity_allowlist_never_returns_raw_metadata_or_log(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="allowlisted activity")
    store.add_event(
        task.id,
        event_type="EXECUTOR_FINISHED",
        title="Read source",
        description="bounded event",
        raw_log="Authorization: bearer-secret",
        metadata={
            "activity_kind": "READ",
            "role": "coder",
            "agent_id": "worker-coder",
            "path": "src/service.py",
            "validation_command_id": "git_diff_check",
            "prompt": "private reasoning must not escape",
            "nested_secret": "token-value",
        },
    )
    detail = model.run_detail(task.id)
    event = detail["events"][-1]
    assert event["category"] == "READ"
    assert event["role"] == "coder"
    assert event["agent_id"].startswith("agent-")
    assert event["agent_id"] != "worker-coder"
    assert event["path"] == "src/service.py"
    assert event["command"]["summary"] == "git_diff_check"
    assert "raw_log" not in event
    assert "metadata" not in event
    assert "Authorization" not in json.dumps(detail)
    assert "private reasoning" not in json.dumps(detail)
    assert "token-value" not in json.dumps(detail)


def test_worker_fallback_identity_and_invalid_metadata_are_bounded(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="bounded worker fallback")

    discovered = model.run_detail(task.id)["events"][0]
    assert discovered["category"] == "PLAN"
    assert discovered["agent"] is None

    store.add_event(
        task.id,
        event_type="EXECUTOR_RUNNING",
        title="worker started",
        metadata={
            "activity_kind": "NOT_A_CATEGORY",
            "role": "untrusted-custom-role",
            "agent_id": "Authorization bearer-secret",
        },
    )
    projected = model.run_detail(task.id)["events"][-1]
    assert projected["category"] == "AGENT_STARTED"
    assert projected["agent_id"].startswith("agent-")
    assert projected["role"] == ""
    assert projected["agent"]["display_name"] == projected["agent_id"]
    assert "bearer-secret" not in json.dumps(projected)


def test_activity_and_detail_event_payloads_are_explicitly_bounded(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="bounded activity")
    event_ids = []
    for index in range(MAX_DETAIL_EVENTS + 3):
        created = store.add_event(
            task.id,
            event_type="EXECUTOR_RUNNING",
            title=f"worker event {index}",
            metadata={"role": "coder", "agent_id": "worker-coder"},
        )
        event_ids.append(created.id)

    detail = model.run_detail(task.id)
    assert len(detail["events"]) == MAX_DETAIL_EVENTS
    assert detail["event_count"] == MAX_DETAIL_EVENTS + 4
    assert detail["events_truncated"] is True
    assert len(detail["activity"]) == 5
    assert detail["activity_total"] == MAX_DETAIL_EVENTS + 4
    assert [event["id"] for event in detail["activity"]] == event_ids[-5:]
    assert {event["stage"] for event in detail["activity"]} == {"EXECUTE"}


def test_opaque_secrets_and_non_repository_paths_are_rejected(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="opaque secret filtering")
    store.add_event(
        task.id,
        event_type="EXECUTOR_FINISHED",
        title="qwertyuiopasdfghjklzxcvbnm",
        description="X-Key:qwertyuiopasdfghjklzxcvbnm",
        metadata={
            "activity_kind": "COMMAND",
            "command": "curl https://user:sk-test-opaque-123@example.invalid/path",
            "path": "F:\\private-worktree\\source.py",
            "evidence_ref": "sk-test-opaque-456",
        },
    )
    store.set_changed_files(
        task.id,
        [{
            "path": "F:\\private-worktree\\source.py",
            "status": "modified",
            "additions": 1,
            "deletions": 0,
        }],
    )

    detail = model.run_detail(task.id)
    event = detail["events"][-1]
    assert event["command"] is None
    assert event["path"] == ""
    assert event["evidence_ref"] == ""
    assert event["title"] == "Approved command"
    assert event["description"] == ""
    assert detail["changed_files"] == []
    assert detail["change_summary"]["file_count"] == 0
    serialized = json.dumps(detail)
    assert "sk-test-opaque" not in serialized
    assert "private-worktree" not in serialized


def test_liveness_uses_fixed_clock_and_no_lease_event_fallback(read_model) -> None:
    _, store, control = read_model
    now = datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc)
    model = RunReadModel(
        store=store, control_store=control, clock=lambda: now,
        stale_after_seconds=600,
    )
    task = store.create_task(title="fresh event fallback")
    store.set_state(task.id, "RUNNING")
    store.add_event(
        task.id,
        event_type="EXECUTOR_RUNNING",
        title="worker started",
        metadata={"role": "coder", "execution_id": "exec-fallback"},
    )
    store._conn.execute(
        "UPDATE task_events SET timestamp = ? WHERE task_id = ?",
        ("2026-01-01T00:09:59Z", task.id),
    )
    store._conn.execute(
        "UPDATE tasks SET updated_at = ? WHERE id = ?",
        ("2026-01-01T00:09:59Z", task.id),
    )
    fresh = model.list_runs()["runs"][0]
    assert fresh["liveness"] == "ACTIVE"
    assert fresh["liveness_detail"]["last_activity_source"] == "event"
    assert fresh["liveness_detail"]["seconds_since_activity"] == 1

    store._conn.execute(
        "UPDATE task_events SET timestamp = ? WHERE task_id = ?",
        ("2026-01-01T00:00:00Z", task.id),
    )
    store._conn.execute(
        "UPDATE tasks SET updated_at = ? WHERE id = ?",
        ("2026-01-01T00:00:00Z", task.id),
    )
    stale = model.list_runs()["runs"][0]
    assert stale["liveness"] == "STALE"
    assert stale["liveness_detail"]["stale_reason"] == "no_recent_activity"


def test_fresh_and_expired_durable_leases_are_distinguishable(read_model) -> None:
    _, store, control = read_model
    now = datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc)
    now_ms = int(now.timestamp() * 1000)
    model = RunReadModel(store=store, control_store=control, clock=lambda: now)
    task = store.create_task(
        title="durable liveness",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="not-exposed",
        expiry_ms=60_000,
    )
    store.set_state(task.id, "RUNNING")
    store._conn.execute(
        "UPDATE task_events SET timestamp = ? WHERE task_id = ?",
        ("2026-01-01T00:09:00Z", task.id),
    )
    store._conn.execute(
        "UPDATE tasks SET updated_at = ? WHERE id = ?",
        ("2026-01-01T00:09:00Z", task.id),
    )
    store._conn.execute(
        "UPDATE durable_runs SET heartbeat_at_ms = ?, lease_expiry_ms = ?, "
        "updated_at = ? WHERE run_id = ?",
        (now_ms - 2_000, now_ms + 60_000, "2026-01-01T00:09:58Z", lease.run_id),
    )
    fresh = model.list_runs()["runs"][0]
    assert fresh["liveness"] == "ACTIVE"
    assert fresh["liveness_detail"]["last_activity_source"] == "heartbeat"
    assert "not-exposed" not in json.dumps(fresh)
    assert "worktree_path" not in json.dumps(fresh)
    assert "checkpoint_db_path" not in json.dumps(fresh)

    store._conn.execute(
        "UPDATE durable_runs SET heartbeat_at_ms = ?, lease_expiry_ms = ?, "
        "updated_at = ? WHERE run_id = ?",
        (now_ms - 601_000, now_ms - 1_000, "2026-01-01T00:00:00Z", lease.run_id),
    )
    stale = model.list_runs()["runs"][0]
    assert stale["liveness"] == "STALE"
    assert stale["liveness_detail"]["stale_reason"] == "lease_expired"


def test_durable_role_attribution_is_projected_without_lease_owner(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(
        title="durable attribution",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="private-lease-owner",
        expiry_ms=60_000,
    )
    store._set_role_attempt(lease.run_id, "coder", 2, lease.owner, lease.epoch)
    store.add_event(
        task.id,
        event_type="EXECUTOR_RUNNING",
        title="durable worker started",
    )

    run = model.list_runs()["runs"][0]
    assert run["current_agent"] == {
        "agent_id": f"{task.execution_id}:coder",
        "role": "coder",
        "display_name": "Coder",
    }
    assert any(
        agent["agent_id"] == f"{task.execution_id}:coder"
        and agent["role"] == "coder"
        and agent["attempt"] == 2
        for agent in run["agents"]
    )
    assert "private-lease-owner" not in json.dumps(run)


def test_historical_worker_events_are_not_relabelled_as_current_durable_role(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(
        title="historical attribution",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="attribution-owner",
        expiry_ms=60_000,
    )
    store._set_role_attempt(lease.run_id, "reviewer", 1, lease.owner, lease.epoch)
    store.add_event(
        task.id,
        event_type="EXECUTOR_RUNNING",
        title="planner event",
        metadata={"role": "planner"},
    )
    store.add_event(
        task.id,
        event_type="EXECUTOR_FINISHED",
        title="roleless historical event",
        metadata={},
    )

    run = model.list_runs()["runs"][0]
    planner, roleless = run["activity"][-2:]
    assert planner["role"] == "planner"
    assert planner["agent_id"] == f"{task.execution_id}:planner"
    assert roleless["role"] == ""
    assert roleless["agent_id"] == task.execution_id
    assert run["current_agent"]["role"] == "reviewer"
    assert run["current_agent"]["agent_id"] == f"{task.execution_id}:reviewer"
    assert [(agent["agent_id"], agent["role"]) for agent in run["agents"]] == [
        (f"{task.execution_id}:planner", "planner"),
        (f"{task.execution_id}:reviewer", "reviewer"),
    ]


@pytest.mark.parametrize("status", ["PREPARING_WORKSPACE", "VALIDATING"])
def test_expired_durable_lease_overrides_live_status(status: str, read_model) -> None:
    _, store, control = read_model
    now = datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc)
    now_ms = int(now.timestamp() * 1000)
    task = store.create_task(title=f"expired-{status}")
    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="expired-owner",
        expiry_ms=60_000,
    )
    store.set_state(task.id, status)
    store._conn.execute(
        "UPDATE durable_runs SET heartbeat_at_ms = ?, lease_expiry_ms = ? "
        "WHERE run_id = ?",
        (now_ms - 601_000, now_ms - 1_000, lease.run_id),
    )
    model = RunReadModel(store=store, control_store=control, clock=lambda: now)

    run = model.list_runs()["runs"][0]
    assert run["liveness"] == "STALE"
    assert run["liveness_detail"]["stale_reason"] == "lease_expired"


def test_post_validation_stage_remains_verify_without_publication(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="post-validation stage")
    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="stage-owner",
        expiry_ms=60_000,
    )
    for checkpoint in (
        "PRE_PLANNER", "POST_PLANNER", "POST_CODER", "POST_REVIEWER", "POST_VALIDATION"
    ):
        store._accept_checkpoint(
            lease.run_id, checkpoint, f"digest-{checkpoint}", 1,
            lease.owner, lease.epoch,
        )

    assert model.list_runs()["runs"][0]["stage"] == "VERIFY"
    assert model.run_detail(task.id)["events"][0]["stage"] == "PLAN"


def test_running_without_any_parseable_persisted_activity_is_unknown(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="unknown activity")
    store.set_state(task.id, "RUNNING")
    store._conn.execute("DELETE FROM task_events WHERE task_id = ?", (task.id,))
    store._conn.execute(
        "UPDATE tasks SET updated_at = '' WHERE id = ?",
        (task.id,),
    )

    run = model.list_runs()["runs"][0]
    assert run["liveness"] == "UNKNOWN"
    assert run["liveness_detail"]["stale_reason"] == "no_persisted_activity"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("QUEUED", "WAITING"),
        ("VALIDATING", "VALIDATING"),
        ("BLOCKED", "BLOCKED"),
        ("READY_FOR_REVIEW", "OWNER_ACTION_REQUIRED"),
        ("FAILED", "TERMINAL"),
        ("CANCELLED", "TERMINAL"),
        ("INTERRUPTED", "STALE"),
    ],
)
def test_liveness_statuses_are_deterministic(read_model, status: str, expected: str) -> None:
    _, store, control = read_model
    task = store.create_task(title=f"status-{status}")
    store.set_state(task.id, status)
    model = RunReadModel(
        store=store, control_store=control,
        clock=lambda: datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc),
    )
    assert model.list_runs()["runs"][0]["liveness"] == expected


def test_multi_role_agents_and_change_summary_are_distinct(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="multi-role activity")
    for role, worker in (("planner", "agent-plan"), ("coder", "agent-code"), ("reviewer", "agent-review")):
        store.add_event(
            task.id, event_type="EXECUTOR_RUNNING", title=f"{role} started",
            metadata={"role": role, "agent_id": worker, "execution_id": f"exec-{worker}"},
        )
    store.set_changed_files(
        task.id,
        [
            {"path": "a.py", "status": "added", "additions": 4, "deletions": 0},
            {"path": "b.py", "status": "modified", "additions": 2, "deletions": 1},
        ],
    )
    run = model.list_runs()["runs"][0]
    assert {agent["role"] for agent in run["agents"]} == {
        "planner", "coder", "reviewer",
    }
    assert len({agent["agent_id"] for agent in run["agents"]}) == 3
    assert run["change_summary"] == {
        "file_count": 2, "additions": 6, "deletions": 1,
        "status_counts": {"added": 1, "modified": 1, "deleted": 0, "renamed": 0},
    }


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


def test_queue_cancel_control_and_event_projection_are_bounded(read_model) -> None:
    model, store, _ = read_model
    task = store.create_task(title="queue cancel", executor_kind="deterministic_fixture")

    before = store._conn.total_changes
    detail = model.run_detail(task.id)
    assert store._conn.total_changes == before
    assert detail["controls"] == {
        "cancel": {
            "action": "CANCEL",
            "scope": "QUEUE_ONLY",
            "availability": "AVAILABLE",
            "reason_code": "QUEUED_UNCLAIMED",
        }
    }

    store.cancel_queued_task(task.id)
    detail = model.run_detail(task.id)
    assert detail["status"] == "CANCELLED"
    assert detail["liveness"] == "TERMINAL"
    assert detail["controls"]["cancel"]["availability"] == "ALREADY_APPLIED"
    assert detail["controls"]["cancel"]["reason_code"] == "ALREADY_CANCELLED"
    activity = detail["activity"][-1]
    assert activity["type"] == "QUEUE_CANCELLED"
    assert activity["title"] == "Queued task cancelled"
    assert activity["category"] == "CHECKPOINT"
    assert activity["stage"] == "PLAN"
    assert activity["status"] == "COMPLETED"
    assert activity["agent"] is None
    assert activity["description"] == ""


@pytest.mark.parametrize(
    "status,expected_reason",
    [
        ("PREPARING_WORKSPACE", "STATUS_NOT_CANCELLABLE"),
        ("RUNNING", "STATUS_NOT_CANCELLABLE"),
        ("RUNNING_FIXTURE", "STATUS_NOT_CANCELLABLE"),
        ("VALIDATING", "STATUS_NOT_CANCELLABLE"),
        ("INTERRUPTED", "STATUS_NOT_CANCELLABLE"),
        ("READY_FOR_REVIEW", "STATUS_NOT_CANCELLABLE"),
        ("READY_FOR_REVIEW_FIXTURE", "STATUS_NOT_CANCELLABLE"),
        ("BLOCKED", "STATUS_NOT_CANCELLABLE"),
        ("FAILED", "STATUS_NOT_CANCELLABLE"),
    ],
)
def test_queue_cancel_control_is_disabled_for_every_non_queue_status(
    read_model, status: str, expected_reason: str
) -> None:
    model, store, _ = read_model
    task = store.create_task(title="not queue cancellable", executor_kind="deterministic_fixture")
    store.set_state(task.id, status)
    control = model.run_detail(task.id)["controls"]["cancel"]
    assert control["availability"] == "UNAVAILABLE"
    assert control["reason_code"] == expected_reason
