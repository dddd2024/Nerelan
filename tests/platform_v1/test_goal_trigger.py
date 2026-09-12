from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.goal_trigger import (
    CREATED,
    DISABLED,
    FIXED_INTERVAL,
    LATEST_ONLY,
    NOT_DUE,
    ONE_TIME,
    SKIP,
    SKIPPED_ACTIVE_BACKLOG,
    SKIPPED_MISSED,
    GoalTriggerService,
)
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


BASE = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)


def _bundle(db_path: str = ":memory:"):
    store = TaskStore(db_path=db_path)
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    triggers = GoalTriggerService(
        store=store, control_store=control, goal_service=goals
    )
    return store, control, goals, triggers


def _payload(**updates):
    payload = {
        "idempotency_key": "schedule-1",
        "kind": ONE_TIME,
        "title": "Scheduled maintenance",
        "objective": "Inspect the repository and prepare a reviewable draft.",
        "repository": "dddd2024/Nerelan",
        "start_at_utc": "2026-09-12T12:00:00Z",
        "interval_seconds": 0,
        "missed_policy": LATEST_ONLY,
        "max_lateness_seconds": 0,
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
        "binding_ref": "",
        "policy_ref": "",
    }
    payload.update(updates)
    return payload


def _count(store: TaskStore, table: str) -> int:
    return int(store._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def test_trigger_definition_is_normalized_and_idempotent():
    store, _, _, service = _bundle()
    first = service.create(
        _payload(start_at_utc="2026-09-12T12:00:00.900000Z")
    )
    before = store._conn.total_changes
    second = service.create(
        _payload(start_at_utc="2026-09-12T12:00:00.100000Z")
    )

    assert first == second
    assert first.start_at_utc == "2026-09-12T12:00:00Z"
    assert first.status == "ENABLED"
    assert store._conn.total_changes == before
    assert _count(store, "platform_goal_triggers") == 1


def test_trigger_idempotency_key_reuse_with_different_definition_fails_closed():
    _, _, _, service = _bundle()
    service.create(_payload())
    with pytest.raises(
        TaskStoreError,
        match="goal_trigger_idempotency_key_reused_with_different_definition",
    ):
        service.create(_payload(objective="Different objective"))


@pytest.mark.parametrize(
    "updates, error",
    [
        ({"start_at_utc": "2026-09-12T12:00:00+00:00"}, "start_at_must_be"),
        ({"kind": ONE_TIME, "interval_seconds": 60}, "one_time_interval"),
        (
            {"kind": FIXED_INTERVAL, "interval_seconds": 59},
            "interval_out_of_range",
        ),
        (
            {"kind": FIXED_INTERVAL, "interval_seconds": 2_678_401},
            "interval_out_of_range",
        ),
        ({"max_lateness_seconds": 604_801}, "max_lateness_out_of_range"),
        ({"executor_kind": "deterministic_fixture", "orchestration_mode": "sequential_team"},
         "sequential_team_requires_opencode"),
    ],
)
def test_invalid_trigger_contract_fails_closed(updates, error):
    _, _, _, service = _bundle()
    with pytest.raises(TaskStoreError, match=error):
        service.create(_payload(**updates))


def test_sensitive_or_unknown_fields_are_rejected():
    _, _, _, service = _bundle()
    with pytest.raises(TaskStoreError, match="sensitive_control_field_rejected"):
        service.create({**_payload(), "api_key": "do-not-store"})
    with pytest.raises(TaskStoreError, match="goal_trigger_unknown_field"):
        service.create({**_payload(), "free_form": "no"})


def test_before_due_is_read_only_not_due_and_creates_no_invocation_or_goal():
    store, _, _, service = _bundle()
    trigger = service.create(_payload())
    before = store._conn.total_changes

    result = service.fire_due(trigger.id, now=BASE - timedelta(seconds=1))

    assert result.outcome == NOT_DUE
    assert result.persisted is False
    assert store._conn.total_changes == before
    assert _count(store, "platform_goal_trigger_invocations") == 0
    assert _count(store, "platform_goals") == 0


def test_due_one_time_creates_one_draft_goal_and_retry_is_zero_write():
    store, control, _, service = _bundle()
    trigger = service.create(_payload())

    first = service.fire_due(trigger.id, now=BASE)
    assert first.outcome == CREATED
    assert first.persisted is True
    goal = control.get_goal(first.goal_id)
    assert goal.status == "DRAFT"
    assert control.list_goal_tasks(goal.id) == ()
    assert _count(store, "tasks") == 0
    assert _count(store, "platform_goal_trigger_invocations") == 1

    before = store._conn.total_changes
    second = service.fire_due(trigger.id, now=BASE + timedelta(hours=1))
    assert second == first
    assert store._conn.total_changes == before
    assert _count(store, "platform_goals") == 1


def test_fixed_interval_latest_only_collapses_long_downtime_to_one_occurrence():
    store, control, _, service = _bundle()
    trigger = service.create(
        _payload(
            kind=FIXED_INTERVAL,
            interval_seconds=300,
            missed_policy=LATEST_ONLY,
        )
    )

    result = service.fire_due(
        trigger.id, now=BASE + timedelta(days=3, minutes=7, seconds=20)
    )

    assert result.outcome == CREATED
    assert result.scheduled_for_utc == "2026-09-15T12:05:00Z"
    assert _count(store, "platform_goal_trigger_invocations") == 1
    assert _count(store, "platform_goals") == 1
    assert control.get_goal(result.goal_id).status == "DRAFT"


def test_skip_policy_records_only_latest_missed_occurrence_without_goal():
    store, _, _, service = _bundle()
    trigger = service.create(
        _payload(
            kind=FIXED_INTERVAL,
            interval_seconds=60,
            missed_policy=SKIP,
            max_lateness_seconds=10,
        )
    )

    result = service.fire_due(
        trigger.id, now=BASE + timedelta(hours=1, seconds=45)
    )

    assert result.outcome == SKIPPED_MISSED
    assert result.scheduled_for_utc == "2026-09-12T13:00:00Z"
    assert _count(store, "platform_goal_trigger_invocations") == 1
    assert _count(store, "platform_goals") == 0


def test_active_trigger_goal_bounds_recurring_backlog_then_terminal_allows_next():
    store, control, _, service = _bundle()
    trigger = service.create(
        _payload(kind=FIXED_INTERVAL, interval_seconds=60)
    )
    first = service.fire_due(trigger.id, now=BASE)
    assert first.outcome == CREATED

    second = service.fire_due(trigger.id, now=BASE + timedelta(minutes=1))
    assert second.outcome == SKIPPED_ACTIVE_BACKLOG
    assert second.goal_id == ""
    assert _count(store, "platform_goals") == 1

    with store._lock:
        store._conn.execute(
            "UPDATE platform_goals SET status = 'COMPLETED' WHERE id = ?",
            (first.goal_id,),
        )

    third = service.fire_due(trigger.id, now=BASE + timedelta(minutes=2))
    assert third.outcome == CREATED
    assert third.goal_id != first.goal_id
    assert control.get_goal(third.goal_id).status == "DRAFT"
    assert _count(store, "platform_goals") == 2


def test_disable_is_idempotent_preserves_history_and_prevents_new_goal():
    store, _, _, service = _bundle()
    trigger = service.create(
        _payload(kind=FIXED_INTERVAL, interval_seconds=60)
    )
    first = service.fire_due(trigger.id, now=BASE)
    assert first.outcome == CREATED
    disabled = service.disable(trigger.id)
    assert disabled.status == DISABLED
    before = store._conn.total_changes
    assert service.disable(trigger.id) == disabled
    assert store._conn.total_changes == before

    later = service.fire_due(trigger.id, now=BASE + timedelta(minutes=1))
    assert later.outcome == DISABLED
    assert later.persisted is False
    assert _count(store, "platform_goal_trigger_invocations") == 1
    assert _count(store, "platform_goals") == 1


def test_two_connections_racing_same_occurrence_converge_to_one_goal(tmp_path):
    db_path = str(tmp_path / "tasks.sqlite3")
    store1, _, _, service1 = _bundle(db_path)
    trigger = service1.create(_payload())

    store2, _, _, service2 = _bundle(db_path)
    assert service2.get(trigger.id).definition_digest == trigger.definition_digest

    barrier = Barrier(3)

    def fire(service):
        barrier.wait()
        return service.fire_due(trigger.id, now=BASE)

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(fire, service1)
        f2 = pool.submit(fire, service2)
        barrier.wait()
        r1, r2 = f1.result(timeout=10), f2.result(timeout=10)

    assert r1 == r2
    assert r1.outcome == CREATED
    assert _count(store1, "platform_goal_trigger_invocations") == 1
    assert _count(store1, "platform_goals") == 1
    assert _count(store1, "tasks") == 0


def test_reads_are_bounded_and_zero_write():
    store, _, _, service = _bundle()
    trigger = service.create(_payload())
    service.fire_due(trigger.id, now=BASE)
    before = store._conn.total_changes

    assert service.get(trigger.id).id == trigger.id
    assert service.list(limit=1)[0].id == trigger.id
    assert len(service.list_invocations(trigger.id, limit=1)) == 1
    assert store._conn.total_changes == before
    with pytest.raises(TaskStoreError, match="limit_out_of_range"):
        service.list(limit=201)
    with pytest.raises(TaskStoreError, match="limit_out_of_range"):
        service.list_invocations(trigger.id, limit=0)


def test_schema_initialization_is_idempotent_and_uses_same_database():
    store, control, goals, service = _bundle()
    before = store._conn.total_changes
    again = GoalTriggerService(
        store=store, control_store=control, goal_service=goals
    )
    assert again.list() == service.list()
    assert store._conn.total_changes == before
    tables = {
        row[0]
        for row in store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert "platform_goal_triggers" in tables
    assert "platform_goal_trigger_invocations" in tables


def test_invocation_persistence_is_fixed_machine_data_only():
    store, _, _, service = _bundle()
    trigger = service.create(_payload(objective="secret-looking user objective"))
    service.fire_due(trigger.id, now=BASE)
    row = store._conn.execute(
        "SELECT * FROM platform_goal_trigger_invocations"
    ).fetchone()
    assert set(row.keys()) == {
        "trigger_id",
        "occurrence_digest",
        "scheduled_for_utc",
        "outcome",
        "goal_id",
        "reason_code",
        "created_at",
    }
    persisted = " ".join(str(row[key]) for key in row.keys()).lower()
    for forbidden in (
        "secret-looking user objective",
        "password",
        "api_key",
        "authorization",
        "worktree",
        "prompt",
        "response",
    ):
        assert forbidden not in persisted
