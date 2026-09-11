"""History remains bounded and complete while newer records arrive."""

import base64
import json

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.history_pagination import HistoryPaginationError, encode_cursor
from reverse_agent.platform_v1.run_read_model import RunReadModel
from reverse_agent.platform_v1.run_store import TaskStore


@pytest.fixture
def history():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    yield store, control, GoalService(store=store, control_store=control), RunReadModel(store=store, control_store=control)
    store._conn.close()


def _seed(store, control, count=151):
    goals, tasks = [], []
    for index in range(count):
        goals.append(control.create_goal(
            title=f"Goal {index}", objective="History", repository="owner/repo",
            idempotency_key=f"history-{index}", executor_kind="deterministic_fixture",
            orchestration_mode="single",
        ))
        tasks.append(store.create_task(title=f"Run {index}", repository="owner/repo"))
    store._conn.execute("UPDATE platform_goals SET created_at = '2026-09-01T00:00:00Z'")
    store._conn.execute("UPDATE tasks SET created_at = '2026-09-01T00:00:00Z'")
    return goals, tasks


@pytest.mark.parametrize("kind", ["goals", "runs"])
@pytest.mark.parametrize("limit", [1, 37, 100])
def test_history_cursor_has_no_gaps_or_duplicates_with_ties_and_new_records(history, kind, limit):
    store, control, goals, runs = history
    goal_records, tasks = _seed(store, control)
    original = {record.id for record in (goal_records if kind == "goals" else tasks)}
    read = goals.list_page if kind == "goals" else runs.list_runs
    id_key = "id" if kind == "goals" else "task_id"
    cursor = None
    seen = []
    first = True
    while True:
        page = read(limit=limit, cursor=cursor)
        assert 0 < len(page[kind]) <= limit
        assert page["total"] == (151 if first else 152)
        seen.extend(item[id_key] for item in page[kind])
        if first:
            if kind == "goals":
                control.create_goal(title="New Goal", objective="New", repository="owner/repo", idempotency_key="new")
            else:
                store.create_task(title="New Run")
            first = False
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(seen) == len(set(seen)) == 151
    assert set(seen) == original
    assert seen == sorted(original, reverse=True)
    latest = read(limit=limit)
    assert latest[kind][0][id_key] not in original


def test_goal_history_reads_preserve_real_status_timestamps_and_do_not_write(history):
    store, control, goals, _ = history
    records, tasks = _seed(store, control, 4)
    control.link_goal_task(records[0].id, goal_revision=1, plan_task_id="T1", task_id=tasks[0].id, dependencies=[], seq=0)
    control.refresh_goal_status(records[0].id)
    before = {record.id: control.get_goal(record.id).updated_at for record in records}
    writes = store._conn.total_changes
    first = goals.list_page(limit=2)
    second = goals.list_page(limit=2, cursor=first["next_cursor"])
    assert {row["id"]: row["updated_at"] for row in first["goals"] + second["goals"]} == before
    assert store._conn.total_changes == writes
    assert second["next_cursor"] is None


def test_empty_and_exhausted_histories_are_truthful(history):
    store, control, goals, runs = history
    assert goals.list_page() == {"goals": [], "total": 0, "next_cursor": None}
    assert runs.list_runs() == {"runs": [], "total": 0, "next_cursor": None}
    records, tasks = _seed(store, control, 1)
    assert goals.list_page(cursor=encode_cursor("goals", "2026-09-01T00:00:00Z", records[0].id)) == {
        "goals": [], "total": 1, "next_cursor": None,
    }
    assert runs.list_runs(cursor=encode_cursor("runs", "2026-09-01T00:00:00Z", tasks[0].id)) == {
        "runs": [], "total": 1, "next_cursor": None,
    }


@pytest.mark.parametrize("limit", [0, -1, 101, True, "10", 1.5])
def test_store_page_limits_are_bounded(history, limit):
    store, control, _, _ = history
    for read in (store.list_tasks_page, control.list_goals_page):
        with pytest.raises(HistoryPaginationError):
            read(limit=limit)


@pytest.mark.parametrize("cursor", ["", "not!base64", "x" * 1025, "☃", "e30=", "bnVsbA=="])
def test_malformed_cursors_are_bounded_errors(history, cursor):
    _, _, goals, runs = history
    for read in (goals.list_page, runs.list_runs):
        with pytest.raises(HistoryPaginationError, match="invalid_history_pagination"):
            read(cursor=cursor)


@pytest.mark.parametrize("payload", [
    [2, "goals", "2026-09-01T00:00:00Z", "id"],
    [True, "goals", "2026-09-01T00:00:00Z", "id"],
    [1, "runs", "2026-09-01T00:00:00Z", "id"],
    [1, "goals", "invalid-time", "id"],
    [1, "goals", "2026-09-01T00:00:00Z", ""],
    [1, "goals", "2026-09-01T00:00:00Z", ["id"]],
])
def test_cursor_version_kind_and_position_are_validated(history, payload):
    cursor = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    with pytest.raises(HistoryPaginationError):
        history[2].list_page(cursor=cursor)
