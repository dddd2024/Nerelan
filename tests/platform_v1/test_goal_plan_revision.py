"""A review may approve only the material plan revision it observed."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import hashlib
import json
from http.server import ThreadingHTTPServer
from threading import Barrier, Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

import reverse_agent.platform_v1.control_store as control_store_module
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import _handler_factory


@pytest.fixture
def services():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    service = GoalService(store=store, control_store=control)
    goal = service.create({
        "objective": "Implement and review the exact plan",
        "repository": "owner/repo",
        "idempotency_key": "plan-revision",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    yield store, control, service, goal
    store._conn.close()


def plan_payload(marker="A"):
    return {
        "spec_markdown": "Specification",
        "plan_markdown": f"Plan {marker}",
        "tasks": [{"id": "T001", "title": "Implement", "instruction": marker}],
        "acceptance_criteria": [f"Deliver {marker}"],
    }


def assert_artifact(goal):
    payload = {
        "goal_id": goal.id, "revision": goal.revision,
        "spec_markdown": goal.spec_markdown, "plan_markdown": goal.plan_markdown,
        "tasks": list(goal.tasks), "acceptance_criteria": list(goal.acceptance_criteria),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert goal.artifact_digest == hashlib.sha256(serialized.encode()).hexdigest()


def test_reviewer_cannot_approve_an_unseen_replacement(services):
    store, control, service, goal = services
    seen = service.plan(goal.id, expected_revision=1, acceptance_criteria=["Plan A"]).goal
    replacement = service.plan(goal.id, expected_revision=seen.revision, acceptance_criteria=["Plan B"]).goal
    assert replacement.id == seen.id == goal.id
    assert seen.revision == 1 and replacement.revision == 2
    assert replacement.artifact_digest != seen.artifact_digest
    with pytest.raises(TaskStoreError, match="goal_not_approvable"):
        service.approve(goal.id, expected_revision=seen.revision)
    assert control.get_goal(goal.id) == replacement
    approved = service.approve(goal.id, expected_revision=replacement.revision)
    assert approved.status == "APPROVED"
    assert approved.artifact_digest == replacement.artifact_digest
    assert_artifact(approved)
    assert store.count_tasks() == 0


@pytest.mark.parametrize("field,value", [
    ("spec_markdown", "Changed specification"),
    ("plan_markdown", "Changed plan"),
    ("tasks", [{"id": "T001", "title": "Implement", "instruction": "Changed"}]),
    ("acceptance_criteria", ["Changed acceptance"]),
])
def test_every_material_plan_surface_advances_revision(services, field, value):
    _, control, _, goal = services
    payload = plan_payload()
    original = control.save_goal_plan(goal.id, expected_revision=1, **payload)
    payload[field] = value
    updated = control.save_goal_plan(goal.id, expected_revision=1, **payload)
    assert updated.revision == 2 and updated.status == "PLANNED"
    assert updated.artifact_digest != original.artifact_digest
    assert_artifact(updated)


def test_identical_retry_is_a_noop_and_each_edit_advances_once(services, monkeypatch):
    store, control, _, goal = services
    clock = ["2026-09-11T00:00:00Z"]
    monkeypatch.setattr(control_store_module, "_utc_now", lambda: clock[0])
    current = control.save_goal_plan(goal.id, expected_revision=1, **plan_payload())
    for marker in ["A", "B", "C"]:
        clock[0] = f"2026-09-11T00:0{ord(marker) - ord('A') + 1}:00Z"
        edited = control.save_goal_plan(goal.id, expected_revision=current.revision, **plan_payload(marker))
        assert edited.revision == (1 if marker == "A" else current.revision + 1)
        if marker != "A":
            assert edited.updated_at == clock[0]
        current = edited
        changes = store._conn.total_changes
        payload = plan_payload(marker)
        payload["tasks"] = [dict(reversed(list(payload["tasks"][0].items())))]
        clock[0] = "2026-09-11T01:00:00Z"
        assert control.save_goal_plan(goal.id, expected_revision=current.revision, **payload) == current
        assert store._conn.total_changes == changes
        assert_artifact(current)


@pytest.mark.parametrize("status", ["APPROVED", "RUNNING", "COMPLETED", "BLOCKED", "INVALIDATED"])
def test_non_plannable_state_rejects_even_identical_content(services, status):
    store, control, _, goal = services
    control.save_goal_plan(goal.id, expected_revision=1, **plan_payload())
    store._conn.execute("UPDATE platform_goals SET status = ? WHERE id = ?", (status, goal.id))
    before = control.get_goal(goal.id)
    with pytest.raises(TaskStoreError, match="goal_revision_or_state_mismatch"):
        control.save_goal_plan(goal.id, expected_revision=1, **plan_payload())
    assert control.get_goal(goal.id) == before


def test_stale_generation_cannot_replace_or_retry_current_plan(services):
    _, control, service, goal = services
    service.plan(goal.id, expected_revision=1, acceptance_criteria=["A"])
    current = service.plan(goal.id, expected_revision=1, acceptance_criteria=["B"]).goal
    for criteria in [["A"], ["B"], ["C"]]:
        with pytest.raises(TaskStoreError, match="goal_revision_mismatch"):
            service.plan(goal.id, expected_revision=1, acceptance_criteria=criteria)
        assert control.get_goal(goal.id) == current
    with pytest.raises(TaskStoreError, match="goal_revision_or_state_mismatch"):
        control.save_goal_plan(goal.id, expected_revision=1, **plan_payload())
    assert control.get_goal(goal.id) == current


@pytest.mark.parametrize("initially_planned", [False, True])
def test_separate_database_connections_cannot_both_replace_observed_plan(tmp_path, monkeypatch, initially_planned):
    path = str(tmp_path / "tasks.sqlite3")
    stores = [TaskStore(path), TaskStore(path)]
    controls = [PlatformControlStore(store) for store in stores]
    goal = controls[0].create_goal(title="Goal", objective="Review", repository="owner/repo", idempotency_key="race")
    if initially_planned:
        controls[0].save_goal_plan(goal.id, expected_revision=1, **plan_payload())
    barrier = Barrier(2)
    for control in controls:
        original_get = control.get_goal
        def synchronized_get(goal_id, original_get=original_get, seen=[False]):
            record = original_get(goal_id)
            if not seen[0]:
                seen[0] = True
                barrier.wait(timeout=10)
            return record
        monkeypatch.setattr(control, "get_goal", synchronized_get)

    def save(index):
        try:
            return controls[index].save_goal_plan(goal.id, expected_revision=1, **plan_payload(str(index)))
        except TaskStoreError as exc:
            return str(exc)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(save, [0, 1]))
        failures = [result for result in results if isinstance(result, str)]
        winners = [result for result in results if not isinstance(result, str)]
        assert failures == ["goal_revision_or_state_mismatch"]
        assert len(winners) == 1
        current = controls[0].get_goal(goal.id)
        assert current == winners[0]
        assert current.revision == (2 if initially_planned else 1)
        marker = current.tasks[0]["instruction"]
        assert current.plan_markdown == f"Plan {marker}"
        assert current.acceptance_criteria == (f"Deliver {marker}",)
        assert_artifact(current)
    finally:
        for store in stores:
            store._conn.close()


def test_revision_and_artifact_survive_reopen_and_objective_amendment(tmp_path):
    path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(path)
    control = PlatformControlStore(store)
    goal = control.create_goal(title="Goal", objective="Review", repository="owner/repo", idempotency_key="restart")
    control.save_goal_plan(goal.id, expected_revision=1, **plan_payload())
    current = control.save_goal_plan(goal.id, expected_revision=1, **plan_payload("B"))
    store._conn.close()
    store = TaskStore(path)
    try:
        control = PlatformControlStore(store)
        assert asdict(control.get_goal(goal.id)) == asdict(current)
        amended = control.amend_goal(goal.id, expected_revision=2, objective="Revised objective")
        assert amended.id == goal.id and amended.revision == 3
        assert amended.status == "DRAFT" and amended.artifact_digest == ""
        with pytest.raises(TaskStoreError, match="goal_not_approvable"):
            control.approve_goal(goal.id, expected_revision=3)
        replanned = control.save_goal_plan(goal.id, expected_revision=3, **plan_payload("C"))
        assert replanned.revision == 3 and replanned.status == "PLANNED"
        assert_artifact(replanned)
    finally:
        store._conn.close()


def test_http_review_rejects_old_plan_and_accepts_refreshed_revision():
    store = TaskStore(":memory:")
    handler = _handler_factory(store, ExecutorRouter(), allowed_origin="http://localhost:5173")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()

    def post(path, payload):
        request = Request(
            f"http://127.0.0.1:{server.server_port}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Origin": "http://localhost:5173"},
            method="POST",
        )
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    try:
        status, created = post("/api/goals", {
            "objective": "Review the exact plan", "repository": "owner/repo",
            "idempotency_key": "http-review", "executor_kind": "deterministic_fixture",
            "orchestration_mode": "single",
        })
        assert status == 201
        path = f"/api/goals/{created['id']}"
        status, seen = post(path + "/plan", {"expected_revision": 1, "acceptance_criteria": ["A"]})
        assert status == 200 and seen["revision"] == 1
        status, replacement = post(path + "/plan", {"expected_revision": 1, "acceptance_criteria": ["B"]})
        assert status == 200 and replacement["revision"] == 2
        status, error = post(path + "/approve", {"expected_revision": seen["revision"]})
        assert status == 409 and error["error"] == "goal_not_approvable"
        status, approved = post(path + "/approve", {"expected_revision": replacement["revision"]})
        assert status == 200 and approved["status"] == "APPROVED"
        assert approved["id"] == seen["id"] == replacement["id"]
        assert approved["artifact_digest"] == replacement["artifact_digest"] != seen["artifact_digest"]
        assert store.count_tasks() == 0
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=10)
        store._conn.close()
