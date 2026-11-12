"""GET /api/goals/<id>/timeline: one goal as one conversation."""
import json
from datetime import datetime, timedelta, timezone

from reverse_agent.platform_v1 import task_service as ts
from reverse_agent.platform_v1.run_read_model import RunReadModel
from reverse_agent.platform_v1.run_store import TaskStore
from test_contract_miss_fixup import case  # noqa: F401 (fixture)
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)
from test_task_service import _enable_legacy_window_fixture, _req, _synthetic_window, task_server  # noqa: F401


def test_public_events_skip_evidence_never_return_raw_log_and_are_bounded():
    store = TaskStore()
    task = store.create_task(title="t")
    store.add_event(task.id, event_type="EXECUTOR_RUNNING", title="OpenCode CLI started", raw_log="Authorization: secret")
    for i in range(5):
        store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="Executor action evidence", description=f"tool_use {i}")
    for i in range(4):
        store.add_event(task.id, event_type="EXECUTOR_PROGRESS", title="OpenCode", description=f"read f{i}.py")
    events, total = store.public_events(task.id, limit=3)
    assert total == 6  # DISCOVERED, started and four progress rows; evidence excluded
    assert [e["description"] for e in events] == ["read f1.py", "read f2.py", "read f3.py"]  # newest three, in time order
    assert all("raw_log" not in e for e in events)


def test_timeline_strings_attempts_in_order_with_their_reasons(case):
    root, _, store, control, service, goal, _, task = case
    store.add_event(task.id, event_type="WORKSPACE_READY", title="Workspace ready",
                    metadata={"execution_id": task.execution_id, "workspace": str(root)})
    store.add_event(task.id, event_type="EXECUTOR_PROGRESS", title="OpenCode", description="read README.md",
                    metadata={"activity_kind": "READ", "role": "executor"})
    store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="OpenCode stalled",
                    description="OpenCode CLI wrote nothing for too long (often a provider 429 it waits out)",
                    metadata={"failure_classification": "executor_stalled", "role": "executor"})
    store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="Executor action evidence", description="step_start")
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='provider_overloaded', "
                        "failure_detail='overloaded', updated_at='2000-01-01T00:00:00Z' WHERE id=?", (task.id,))
    store._conn.commit()
    [step] = service.escalate_failed_tasks(goal.id)
    retry_id = step["to_task_id"]
    store.add_event(retry_id, event_type="EXECUTOR_PROGRESS", title="OpenCode", description="edit README.md",
                    metadata={"activity_kind": "EDIT", "role": "executor"})

    timeline = RunReadModel(store=store, control_store=control).goal_timeline(service.timeline_snapshot(goal.id))
    assert timeline["goal"]["id"] == goal.id and timeline["plan"]
    [plan_step] = [s for s in timeline["steps"] if any(a["task_id"] == retry_id for a in s["attempts"])]
    first, second = plan_step["attempts"]
    assert (first["index"], first["task_id"], first["status"]) == (1, task.id, "FAILED")
    assert first["failure"]["classification"] == "provider_overloaded"
    assert first["failure"]["message"].startswith("OpenCode stalled")
    descriptions = [e["description"] for e in first["events"]]
    assert "read README.md" in descriptions
    assert any("provider 429" in d for d in descriptions)
    assert "step_start" not in json.dumps(first["events"])  # evidence rows never appear
    assert first["live"] is None  # history is never live
    assert second["task_id"] == retry_id and second["live"] is not None
    assert [e["description"] for e in second["events"] if e["description"]] == ["edit README.md"]


def test_timeline_endpoint_serves_the_goal_and_404s_unknown(task_server):
    base, server = task_server
    _enable_legacy_window_fixture(server)
    store = server.RequestHandlerClass.store
    status, goal = _req(base, "POST", "/api/goals", {
        "objective": "Timeline over HTTP", "repository": "dddd2024/reverse-agent",
        "idempotency_key": "http-goal-timeline-v1", "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    assert status == 201
    _req(base, "POST", f"/api/goals/{goal['id']}/plan", {"expected_revision": 1})
    _req(base, "POST", f"/api/goals/{goal['id']}/approve", {"expected_revision": 1})
    now = datetime.now(timezone.utc)
    status, window = _synthetic_window(server, {
        "policy_id": "http-timeline-window", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 3, "max_retries": 0, "confirmation": "ACTIVATE",
    })
    assert status == 201
    status, launched = _req(base, "POST", f"/api/goals/{goal['id']}/launch", {"expected_revision": 1, "window_id": window["id"]})
    assert status == 200
    task_id = launched["task_links"][0]["task_id"]
    store.add_event(task_id, event_type="EXECUTOR_PROGRESS", title="OpenCode", description="read a.py",
                    metadata={"activity_kind": "READ"})

    status, timeline = _req(base, "GET", f"/api/goals/{goal['id']}/timeline")
    assert status == 200
    [step] = timeline["steps"]
    [attempt] = step["attempts"]
    assert attempt["task_id"] == task_id and attempt["index"] == 1
    assert "read a.py" in [e["description"] for e in attempt["events"]]
    status, _ = _req(base, "GET", "/api/goals/goal-missing/timeline")
    assert status == 404


def test_timeline_polls_share_a_bounded_slot():
    assert "/api/goals/*/timeline" in ts._POLLED_SLOTS
    assert ts._TIMELINE_PATH.match("/api/goals/goal-1/timeline")
    assert not ts._TIMELINE_PATH.match("/api/goals/goal-1/timeline/extra")
