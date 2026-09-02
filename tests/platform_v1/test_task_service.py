"""HTTP Task API tests: loopback-only, Origin fail-closed, bounded body, no secrets."""

import http.client
import json
import os
import tempfile
import threading
from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import (
    TaskService,
    _handler_factory,
    validate_bind_host,
)


@pytest.fixture()
def task_server(tmp_path):
    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    handler_cls = _handler_factory(
        store, router,
        allowed_origin="http://localhost:5173",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:%d" % port, server
    server.shutdown()
    server.server_close()


def _req(base_url: str, method: str, path: str, body=None, origin=None):
    host, port = base_url.replace("http://", "").split(":", 1)
    conn = http.client.HTTPConnection(host, int(port), timeout=10)
    headers = {
        "Accept": "application/json",
        "Origin": origin or "http://localhost:5173",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, json.loads(data.decode()) if data else None


def _ordered_sqlite_race(first, second):
    """Run two operations on independent SQLite connections in a known order.

    Both workers start together; the second waits only until the first has
    committed or raised.  Separate connections and threads preserve the
    SQLite arbitration boundary while making each winner order deterministic.
    """

    ready = threading.Barrier(2)
    first_done = threading.Event()
    results = {}
    result_lock = threading.Lock()

    def worker(name, operation, wait_for_first):
        ready.wait()
        if wait_for_first:
            first_done.wait(timeout=10)
        try:
            value = operation()
            result = ("ok", value)
        except Exception as exc:  # assert the bounded failure in the caller
            result = ("error", exc)
        with result_lock:
            results[name] = result
        if not wait_for_first:
            first_done.set()

    threads = [
        threading.Thread(target=worker, args=("first", first, False)),
        threading.Thread(target=worker, args=("second", second, True)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    assert set(results) == {"first", "second"}
    return results


def _simultaneous_sqlite_race(first, second):
    """Run two independent-connection operations after one shared barrier."""

    ready = threading.Barrier(2)
    results = {}
    result_lock = threading.Lock()

    def worker(name, operation):
        ready.wait()
        try:
            result = ("ok", operation())
        except Exception as exc:
            result = ("error", exc)
        with result_lock:
            results[name] = result

    threads = [
        threading.Thread(target=worker, args=("first", first)),
        threading.Thread(target=worker, args=("second", second)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    assert set(results) == {"first", "second"}
    return results


def _independent_store(server):
    """Open a fresh TaskStore connection to the task-server database."""

    store = TaskStore(db_path=server.RequestHandlerClass.store.db_path)
    return store


def test_create_and_read_task(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "POST", "/api/tasks", {"title": "t1", "executor_kind": "deterministic_fixture"})
    assert status == 201
    assert body["status"] == "QUEUED"
    assert body["executor_kind"] == "deterministic_fixture"
    assert body["frontend_task"]["executor"] == "fixture/provider-free"
    tid = body["id"]

    status, got = _req(base, "GET", f"/api/tasks/{tid}")
    assert status == 200
    assert got["id"] == tid
    assert got["events"][0]["type"] == "DISCOVERED"
    assert got["usage"]["status"] == "USAGE_UNKNOWN"


def test_platform_status_capabilities_and_goal_window_flow(task_server) -> None:
    base, _ = task_server
    status, platform = _req(base, "GET", "/api/platform/status")
    assert status == 200
    assert platform["service"] == "reverse-agent-platform-v2"
    assert platform["coordinator"]["enabled"] is False
    status, capabilities = _req(base, "GET", "/api/capabilities")
    assert status == 200
    assert capabilities["total"] >= 6

    status, goal = _req(base, "POST", "/api/goals", {
        "objective": "Deliver a provider-free platform check",
        "repository": "dddd2024/reverse-agent",
        "idempotency_key": "http-goal-window-v1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    assert status == 201
    goal_id = goal["id"]
    status, planned = _req(base, "POST", f"/api/goals/{goal_id}/plan", {
        "expected_revision": 1,
        "tasks": [{"id": "T001", "title": "check", "instruction": "run fixture"}],
    })
    assert status == 200
    assert planned["status"] == "PLANNED"
    status, approved = _req(base, "POST", f"/api/goals/{goal_id}/approve", {
        "expected_revision": 1,
    })
    assert status == 200
    assert approved["status"] == "APPROVED"

    now = datetime.now(timezone.utc)
    status, window = _req(base, "POST", "/api/windows/activate", {
        "policy_id": "http-window-v1", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 2, "max_retries": 0,
        "confirmation": "ACTIVATE",
    })
    assert status == 201
    assert window["enforcement_class"] == "POST_RUN_OBSERVED"
    status, launched = _req(base, "POST", f"/api/goals/{goal_id}/launch", {
        "expected_revision": 1, "window_id": window["id"],
    })
    assert status == 200
    assert launched["status"] == "RUNNING"
    assert len(launched["task_links"]) == 1
    status, listed = _req(base, "GET", "/api/goals")
    assert status == 200 and listed["total"] == 1
    status, summary = _req(base, "GET", f"/api/windows/{window['id']}/summary")
    assert status == 200
    assert summary["budget"]["tasks_remaining"] == 2


def test_runs_api_returns_sanitized_numeric_usage_without_raw_event_fields(task_server) -> None:
    base, server = task_server
    status, task = _req(base, "POST", "/api/tasks", {
        "title": "usage api", "executor_kind": "deterministic_fixture",
    })
    assert status == 201
    store = server.RequestHandlerClass.store
    store.append_usage_observation(
        task["id"],
        observation_id="usage-api-visible",
        execution_id="exec-api",
        role="reviewer",
        model_id="provider/model",
        provider_id="provider",
        source_kind="step_finish",
        source_id="msg-api:part-api",
        status="OBSERVED",
        input_units=11,
        output_units=3,
        reasoning_units=2,
        cache_read_units=5,
        cache_write_units=1,
        cost_micro_units=4321,
    )
    status, payload = _req(base, "GET", "/api/runs")
    assert status == 200
    run = next(item for item in payload["runs"] if item["task_id"] == task["id"])
    assert run["usage"]["total_token_units"] == 22
    assert run["usage"]["cost_micro_units"] == 4321
    assert run["usage"]["per_role"][0]["role"] == "reviewer"
    serialized = json.dumps(payload).lower()
    for forbidden in ("prompt", "response", "authorization", "raw_event", "tool_payload"):
        assert forbidden not in serialized


def test_task_api_round_trips_explicit_binding_ref(task_server) -> None:
    base, _store = task_server
    status, created = _req(
        base,
        "POST",
        "/api/tasks",
        {
            "title": "bound task",
            "executor_kind": "opencode",
            "repository": "https://github.com/dddd2024/reverse-agent",
            "binding_ref": "coding-fast",
            "model_profile_ref": "legacy-profile",
        },
    )

    assert status == 201
    assert created["binding_ref"] == "coding-fast"
    assert created["model_profile_ref"] == "legacy-profile"
    status, fetched = _req(base, "GET", f"/api/tasks/{created['id']}")
    assert status == 200
    assert fetched["binding_ref"] == "coding-fast"


def test_task_api_keeps_legacy_empty_binding_compatible(task_server) -> None:
    base, _store = task_server
    status, created = _req(
        base,
        "POST",
        "/api/tasks",
        {
            "title": "legacy opencode",
            "executor_kind": "opencode",
            "repository": "https://github.com/dddd2024/reverse-agent",
            "model_profile_ref": "provider/model",
        },
    )

    assert status == 201
    assert created["binding_ref"] == ""
    assert created["model_profile_ref"] == "provider/model"


def test_list_tasks_and_events(task_server) -> None:
    base, _ = task_server
    _, created = _req(base, "POST", "/api/tasks", {"title": "t", "executor_kind": "deterministic_fixture"})
    tid = created["id"]
    status, listed = _req(base, "GET", "/api/tasks")
    assert status == 200
    assert any(t["id"] == tid for t in listed["tasks"])

    status, events = _req(base, "GET", f"/api/tasks/{tid}/events")
    assert status == 200
    assert events["task_id"] == tid
    assert events["events"][0]["type"] == "DISCOVERED"


def test_queue_cancel_http_applies_once_and_exposes_run_activity(task_server) -> None:
    base, server = task_server
    status, created = _req(
        base, "POST", "/api/tasks",
        {"title": "queue cancel", "executor_kind": "deterministic_fixture"},
    )
    assert status == 201
    task_id = created["id"]

    status, detail = _req(base, "GET", f"/api/runs/{task_id}")
    assert status == 200
    assert detail["controls"]["cancel"] == {
        "action": "CANCEL",
        "scope": "QUEUE_ONLY",
        "availability": "AVAILABLE",
        "reason_code": "QUEUED_UNCLAIMED",
    }

    status, result = _req(base, "POST", f"/api/runs/{task_id}/cancel")
    assert status == 200
    assert result == {"status": "APPLIED"}
    status, again = _req(base, "POST", f"/api/runs/{task_id}/cancel", {})
    assert status == 200
    assert again == {"status": "ALREADY_APPLIED"}

    status, detail = _req(base, "GET", f"/api/runs/{task_id}")
    assert status == 200
    assert detail["status"] == "CANCELLED"
    assert detail["controls"]["cancel"]["availability"] == "ALREADY_APPLIED"
    assert detail["controls"]["cancel"]["reason_code"] == "ALREADY_CANCELLED"
    assert [event["type"] for event in detail["events"]].count("QUEUE_CANCELLED") == 1
    activity = detail["activity"][-1]
    assert activity["category"] == "CHECKPOINT"
    assert activity["stage"] == "PLAN"
    assert activity["status"] == "COMPLETED"
    assert activity["agent"] is None
    assert activity["description"] == ""
    assert server.RequestHandlerClass.store.get_task(task_id).status == "CANCELLED"


def test_queue_cancel_http_concurrent_duplicates_commit_one_event(task_server) -> None:
    base, server = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "concurrent queue cancel", "executor_kind": "deterministic_fixture"},
    )
    task_id = created["id"]
    barrier = threading.Barrier(2)
    results: list[tuple[int, dict]] = []
    result_lock = threading.Lock()

    def cancel() -> None:
        barrier.wait()
        result = _req(base, "POST", f"/api/runs/{task_id}/cancel")
        with result_lock:
            results.append(result)

    workers = [threading.Thread(target=cancel) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=10)
    assert all(not worker.is_alive() for worker in workers)
    assert sorted(status for status, _ in results) == [200, 200]
    assert sorted(body["status"] for _, body in results) == [
        "ALREADY_APPLIED", "APPLIED",
    ]
    assert server.RequestHandlerClass.store._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'",
        (task_id,),
    ).fetchone()["c"] == 1


def test_cancel_cancel_independent_sqlite_connections_have_one_winner(task_server) -> None:
    base, server = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "independent cancel race", "executor_kind": "deterministic_fixture"},
    )
    task_id = created["id"]
    db_path = server.RequestHandlerClass.store.db_path
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    first_store = TaskStore(db_path=db_path)
    second_store = TaskStore(db_path=db_path)
    PlatformControlStore(first_store)
    PlatformControlStore(second_store)

    first_order = _ordered_sqlite_race(
        lambda: first_store.cancel_queued_task(task_id).status,
        lambda: second_store.cancel_queued_task(task_id).status,
    )
    assert sorted(value for kind, value in first_order.values() if kind == "ok") == [
        "ALREADY_APPLIED", "APPLIED",
    ]
    store = _independent_store(server)
    assert store.get_task(task_id).status == "CANCELLED"
    assert store._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'", (task_id,)
    ).fetchone()["c"] == 1
    assert store._conn.execute(
        "SELECT COUNT(*) AS c FROM platform_coordinator_claims WHERE task_id = ?",
        (task_id,),
    ).fetchone()["c"] == 0
    assert store._conn.execute(
        "SELECT COUNT(*) AS c FROM platform_budget_reservations WHERE task_id = ?",
        (task_id,),
    ).fetchone()["c"] == 0


def test_claim_cancel_independent_sqlite_connections_both_winner_orders(
    task_server,
) -> None:
    base, server = task_server
    db_path = server.RequestHandlerClass.store.db_path
    from reverse_agent.platform_v1.control_store import PlatformControlStore

    control_store = PlatformControlStore(TaskStore(db_path=db_path))
    now = datetime.now(timezone.utc)
    window = control_store.activate_window(
        {
            "window_id": "window-claim-cancel-race",
            "policy_id": "claim-cancel-race-independent",
            "policy_revision": 1,
            "owner_identity": "owner",
            "starts_at": (now - timedelta(seconds=1)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "repositories": ["dddd2024/reverse-agent"],
            "capabilities": ["execute_task"],
            "max_concurrent_tasks": 2,
            "max_tasks": 2,
            "max_retries": 0,
        },
        confirmation="ACTIVATE",
    )
    _, claim_first_task = _req(
        base, "POST", "/api/tasks",
        {"title": "claim first independent", "executor_kind": "deterministic_fixture"},
    )
    _, cancel_first_task = _req(
        base, "POST", "/api/tasks",
        {"title": "cancel first independent", "executor_kind": "deterministic_fixture"},
    )

    claim_store = TaskStore(db_path=db_path)
    claim_control = PlatformControlStore(claim_store)
    cancel_store = TaskStore(db_path=db_path)

    def claim(task_id):
        return claim_control.claim_task(
            window_id=window.id, task_id=task_id,
            owner="independent-claim", lease_ms=60_000,
        )

    def cancel(task_id):
        return cancel_store.cancel_queued_task(task_id)

    claim_first = _ordered_sqlite_race(
        lambda: claim(claim_first_task["id"]),
        lambda: cancel(claim_first_task["id"]),
    )
    assert claim_first["first"][0] == "ok"
    assert claim_first["second"][0] == "ok"
    assert claim_first["second"][1].status == "UNAVAILABLE"
    assert claim_first["second"][1].reason_code == "EXECUTION_HISTORY_PRESENT"
    state = _independent_store(server)
    assert state.get_task(claim_first_task["id"]).status == "QUEUED"
    assert state._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'",
        (claim_first_task["id"],),
    ).fetchone()["c"] == 0

    cancel_first = _ordered_sqlite_race(
        lambda: cancel(cancel_first_task["id"]),
        lambda: claim(cancel_first_task["id"]),
    )
    assert cancel_first["first"][0] == "ok"
    assert cancel_first["first"][1].status == "APPLIED"
    assert cancel_first["second"][0] == "error"
    assert isinstance(cancel_first["second"][1], Exception)
    assert "task_not_claimable" in str(cancel_first["second"][1])
    state = _independent_store(server)
    assert state.get_task(cancel_first_task["id"]).status == "CANCELLED"
    assert state._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'",
        (cancel_first_task["id"],),
    ).fetchone()["c"] == 1
    assert state._conn.execute(
        "SELECT COUNT(*) AS c FROM platform_coordinator_claims WHERE task_id = ?",
        (cancel_first_task["id"],),
    ).fetchone()["c"] == 0
    assert state._conn.execute(
        "SELECT COUNT(*) AS c FROM platform_budget_reservations WHERE task_id = ?",
        (cancel_first_task["id"],),
    ).fetchone()["c"] == 0
    assert state._conn.execute(
        "SELECT tasks_started FROM platform_autonomous_windows WHERE id = ?",
        (window.id,),
    ).fetchone()["tasks_started"] == 1


def test_durable_cancel_independent_sqlite_connections_both_winner_orders(
    task_server,
) -> None:
    base, server = task_server
    db_path = server.RequestHandlerClass.store.db_path
    _, durable_first_task = _req(
        base, "POST", "/api/tasks",
        {
            "title": "durable first independent", "executor_kind": "opencode",
            "repository": "repo", "orchestration_mode": "single",
        },
    )
    _, cancel_first_task = _req(
        base, "POST", "/api/tasks",
        {
            "title": "cancel first durable independent", "executor_kind": "opencode",
            "repository": "repo", "orchestration_mode": "single",
        },
    )

    durable_store = TaskStore(db_path=db_path)
    cancel_store = TaskStore(db_path=db_path)

    def acquire(task_id, owner):
        return durable_store._acquire_durable_lease(
            task_id=task_id, execution_id=f"exec-{task_id}",
            lease_owner=owner, expiry_ms=60_000,
        )

    def cancel(task_id):
        return cancel_store.cancel_queued_task(task_id)

    durable_first = _ordered_sqlite_race(
        lambda: acquire(durable_first_task["id"], "durable-first"),
        lambda: cancel(durable_first_task["id"]),
    )
    assert durable_first["first"][0] == "ok"
    assert durable_first["second"][0] == "ok"
    assert durable_first["second"][1].status == "UNAVAILABLE"
    assert durable_first["second"][1].reason_code == "STATUS_NOT_CANCELLABLE"
    state = _independent_store(server)
    assert state.get_task(durable_first_task["id"]).status == "PREPARING_WORKSPACE"
    assert state._conn.execute(
        "SELECT COUNT(*) AS c FROM durable_runs WHERE task_id = ?",
        (durable_first_task["id"],),
    ).fetchone()["c"] == 1
    assert state._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'",
        (durable_first_task["id"],),
    ).fetchone()["c"] == 0

    cancel_first = _ordered_sqlite_race(
        lambda: cancel(cancel_first_task["id"]),
        lambda: acquire(cancel_first_task["id"], "late-durable"),
    )
    assert cancel_first["first"][0] == "ok"
    assert cancel_first["first"][1].status == "APPLIED"
    assert cancel_first["second"][0] == "error"
    assert "durable_claim_" in str(cancel_first["second"][1])
    state = _independent_store(server)
    assert state.get_task(cancel_first_task["id"]).status == "CANCELLED"
    assert state._conn.execute(
        "SELECT COUNT(*) AS c FROM durable_runs WHERE task_id = ?",
        (cancel_first_task["id"],),
    ).fetchone()["c"] == 0
    assert state._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'",
        (cancel_first_task["id"],),
    ).fetchone()["c"] == 1


def test_simultaneous_claim_cancel_independent_connections_preserve_invariants(
    task_server,
) -> None:
    base, server = task_server
    db_path = server.RequestHandlerClass.store.db_path
    from reverse_agent.platform_v1.control_store import PlatformControlStore

    setup_store = TaskStore(db_path=db_path)
    setup_control = PlatformControlStore(setup_store)
    now = datetime.now(timezone.utc)
    window = setup_control.activate_window(
        {
            "window_id": "window-simultaneous-claim-cancel",
            "policy_id": "simultaneous-claim-cancel",
            "policy_revision": 1,
            "owner_identity": "owner",
            "starts_at": (now - timedelta(seconds=1)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "repositories": ["dddd2024/reverse-agent"],
            "capabilities": ["execute_task"],
            "max_concurrent_tasks": 1,
            "max_tasks": 1,
            "max_retries": 0,
        },
        confirmation="ACTIVATE",
    )
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "simultaneous claim cancel", "executor_kind": "deterministic_fixture"},
    )
    task_id = created["id"]
    claim_store = TaskStore(db_path=db_path)
    claim_control = PlatformControlStore(claim_store)
    cancel_store = TaskStore(db_path=db_path)
    results = _simultaneous_sqlite_race(
        lambda: claim_control.claim_task(
            window_id=window.id, task_id=task_id,
            owner="simultaneous-claim", lease_ms=60_000,
        ),
        lambda: cancel_store.cancel_queued_task(task_id),
    )
    state = _independent_store(server)
    claim_row = state._conn.execute(
        "SELECT status FROM platform_coordinator_claims WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    reservation_row = state._conn.execute(
        "SELECT state FROM platform_budget_reservations WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    event_count = state._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'", (task_id,)
    ).fetchone()["c"]
    if results["first"][0] == "ok" and isinstance(results["first"][1], tuple):
        assert results["second"][0] == "ok"
        assert results["second"][1].status == "UNAVAILABLE"
        assert state.get_task(task_id).status == "QUEUED"
        assert claim_row is not None and claim_row["status"] == "ACTIVE"
        assert reservation_row is not None and reservation_row["state"] == "ACTIVE"
        assert event_count == 0
    else:
        cancel_result = next(
            value for kind, value in results.values()
            if kind == "ok" and hasattr(value, "status")
        )
        assert cancel_result.status == "APPLIED"
        assert results["first"][0] == "error" or results["second"][0] == "error"
        assert state.get_task(task_id).status == "CANCELLED"
        assert claim_row is None
        assert reservation_row is None
        assert event_count == 1


def test_simultaneous_durable_cancel_independent_connections_preserve_invariants(
    task_server,
) -> None:
    base, server = task_server
    db_path = server.RequestHandlerClass.store.db_path
    _, created = _req(
        base, "POST", "/api/tasks",
        {
            "title": "simultaneous durable cancel", "executor_kind": "opencode",
            "repository": "repo", "orchestration_mode": "single",
        },
    )
    task_id = created["id"]
    durable_store = TaskStore(db_path=db_path)
    cancel_store = TaskStore(db_path=db_path)
    results = _simultaneous_sqlite_race(
        lambda: durable_store._acquire_durable_lease(
            task_id=task_id, execution_id=f"exec-{task_id}",
            lease_owner="simultaneous-durable", expiry_ms=60_000,
        ),
        lambda: cancel_store.cancel_queued_task(task_id),
    )
    state = _independent_store(server)
    run_count = state._conn.execute(
        "SELECT COUNT(*) AS c FROM durable_runs WHERE task_id = ?", (task_id,)
    ).fetchone()["c"]
    event_count = state._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'", (task_id,)
    ).fetchone()["c"]
    if any(kind == "ok" and hasattr(value, "run_id") for kind, value in results.values()):
        assert state.get_task(task_id).status == "PREPARING_WORKSPACE"
        assert run_count == 1
        assert event_count == 0
    else:
        cancel_result = next(
            value for kind, value in results.values()
            if kind == "ok" and hasattr(value, "status")
        )
        assert cancel_result.status == "APPLIED"
        assert state.get_task(task_id).status == "CANCELLED"
        assert run_count == 0
        assert event_count == 1


@pytest.mark.parametrize("body", [{"reason": "stop"}, {"force": True}, ["cancel"], None])
def test_queue_cancel_http_rejects_non_empty_or_non_object_body(task_server, body) -> None:
    base, _ = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "body contract", "executor_kind": "deterministic_fixture"},
    )
    task_id = created["id"]
    if body is None:
        # A literal JSON null is non-empty and must be rejected as well.
        raw_body = b"null"
        host, port = base.replace("http://", "").split(":", 1)
        conn = http.client.HTTPConnection(host, int(port), timeout=10)
        conn.request(
            "POST", f"/api/runs/{task_id}/cancel", body=raw_body,
            headers={
                "Accept": "application/json", "Origin": "http://localhost:5173",
                "Content-Type": "application/json",
            },
        )
        response = conn.getresponse()
        status = response.status
        payload = json.loads(response.read().decode())
    else:
        status, payload = _req(base, "POST", f"/api/runs/{task_id}/cancel", body)
    assert status == 400
    assert payload == {"error": "cancel_request_must_be_empty"}


def test_queue_cancel_http_is_fail_closed_for_active_status_and_unknown_run(task_server) -> None:
    base, server = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "active cancel", "executor_kind": "deterministic_fixture"},
    )
    task_id = created["id"]
    server.RequestHandlerClass.store.set_state(task_id, "RUNNING")
    status, payload = _req(base, "POST", f"/api/runs/{task_id}/cancel")
    assert status == 409
    assert payload == {
        "error": "queue_cancel_unavailable",
        "reason_code": "STATUS_NOT_CANCELLABLE",
    }
    assert server.RequestHandlerClass.store.get_task(task_id).status == "RUNNING"

    status, payload = _req(base, "POST", "/api/runs/missing-run/cancel")
    assert status == 404
    assert payload == {"error": "run_not_found"}


@pytest.mark.parametrize(
    "table,columns,values",
    [
        (
            "platform_coordinator_claims",
            "task_id,window_id,owner,epoch,expires_at_ms,status,created_at,updated_at",
            ("{task}", "window-1", "worker", 1, 1, "COMPLETE", "now", "now"),
        ),
        (
            "platform_budget_reservations",
            "task_id,claim_epoch,window_id,reserved_token_units,reserved_cost_micro_units,state,observed_token_units,observed_cost_micro_units,created_at,updated_at,reconciled_at",
            ("{task}", 1, "window-1", 10, 1, "RECONCILED", 10, 1, "now", "now", "now"),
        ),
        (
            "platform_publications",
            "id,task_id,repository,base_branch,branch,status,commit_sha,pr_number,pr_url,request_digest,failure_classification,created_at,updated_at",
            ("publication-1", "{task}", "repo", "main", "branch", "FAILED", "", 0, "", "", "", "now", "now"),
        ),
    ],
)
def test_queue_cancel_rejects_any_historical_execution_evidence(
    task_server, table: str, columns: str, values: tuple
) -> None:
    base, server = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "history evidence", "executor_kind": "deterministic_fixture"},
    )
    task_id = created["id"]
    rendered_values = tuple(task_id if value == "{task}" else value for value in values)
    placeholders = ",".join("?" for _ in rendered_values)
    server.RequestHandlerClass.store._conn.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        rendered_values,
    )

    status, payload = _req(base, "POST", f"/api/runs/{task_id}/cancel")
    assert status == 409
    assert payload == {
        "error": "queue_cancel_unavailable",
        "reason_code": "EXECUTION_HISTORY_PRESENT",
    }
    assert server.RequestHandlerClass.store.get_task(task_id).status == "QUEUED"


def test_queue_cancel_rejects_durable_run_even_with_queued_status(task_server) -> None:
    base, server = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {
            "title": "durable history", "executor_kind": "opencode",
            "orchestration_mode": "single", "repository": "repo",
        },
    )
    task_id = created["id"]
    store = server.RequestHandlerClass.store
    lease = store._acquire_durable_lease(
        task_id=task_id, execution_id=created["execution_id"],
        lease_owner="durable-test", expiry_ms=60_000,
    )
    # Deliberately create an inconsistent fixture: history exists while the
    # task is QUEUED.  The history check must still fail closed.
    store._conn.execute(
        "UPDATE tasks SET status = 'QUEUED' WHERE id = ?", (task_id,)
    )
    status, payload = _req(base, "POST", f"/api/runs/{task_id}/cancel")
    assert status == 409
    assert payload == {
        "error": "queue_cancel_unavailable",
        "reason_code": "EXECUTION_HISTORY_PRESENT",
    }
    assert store._get_durable_run(lease.run_id).run_id == lease.run_id
    assert store.get_task(task_id).status == "QUEUED"


def test_cancel_first_blocks_later_durable_acquisition_without_side_effects(task_server) -> None:
    base, server = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "cancel then durable", "executor_kind": "opencode", "repository": "repo"},
    )
    task_id = created["id"]
    store = server.RequestHandlerClass.store
    status, result = _req(base, "POST", f"/api/runs/{task_id}/cancel")
    assert status == 200 and result == {"status": "APPLIED"}
    with pytest.raises(
        TaskStoreError,
        match="durable_claim_(wrong_task_status|task_not_active)",
    ):
        store._acquire_durable_lease(
            task_id=task_id, execution_id=created["execution_id"],
            lease_owner="late-durable", expiry_ms=60_000,
        )
    assert store.get_task(task_id).status == "CANCELLED"
    assert store._conn.execute(
        "SELECT COUNT(*) AS c FROM durable_runs WHERE task_id = ?", (task_id,)
    ).fetchone()["c"] == 0


def test_durable_first_blocks_cancel_without_representing_stop(task_server) -> None:
    base, server = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "durable then cancel", "executor_kind": "opencode", "repository": "repo"},
    )
    task_id = created["id"]
    store = server.RequestHandlerClass.store
    lease = store._acquire_durable_lease(
        task_id=task_id, execution_id=created["execution_id"],
        lease_owner="early-durable", expiry_ms=60_000,
    )
    status, payload = _req(base, "POST", f"/api/runs/{task_id}/cancel")
    assert status == 409
    assert payload == {
        "error": "queue_cancel_unavailable",
        "reason_code": "STATUS_NOT_CANCELLABLE",
    }
    assert store.get_task(task_id).status == "PREPARING_WORKSPACE"
    assert store._get_durable_run(lease.run_id).run_id == lease.run_id


def test_claim_cancel_both_winner_orders_fail_closed(task_server) -> None:
    base, server = task_server
    store = server.RequestHandlerClass.store
    control = server.RequestHandlerClass.control_store
    autonomy = server.RequestHandlerClass.autonomy_service
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "claim-cancel-race", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2, "max_tasks": 2, "max_retries": 0,
        "confirmation": "ACTIVATE",
    })
    _, first = _req(
        base, "POST", "/api/tasks",
        {"title": "claim first", "executor_kind": "deterministic_fixture"},
    )
    _, second = _req(
        base, "POST", "/api/tasks",
        {"title": "cancel first", "executor_kind": "deterministic_fixture"},
    )

    control.claim_task(
        window_id=window.id, task_id=first["id"], owner="race-owner", lease_ms=60_000
    )
    status, payload = _req(base, "POST", f"/api/runs/{first['id']}/cancel")
    assert status == 409
    assert payload["error"] == "queue_cancel_unavailable"
    assert payload["reason_code"] == "EXECUTION_HISTORY_PRESENT"
    first_claim = store._conn.execute(
        "SELECT status FROM platform_coordinator_claims WHERE task_id = ?",
        (first["id"],),
    ).fetchone()
    assert first_claim["status"] == "ACTIVE"

    status, result = _req(base, "POST", f"/api/runs/{second['id']}/cancel")
    assert status == 200 and result == {"status": "APPLIED"}
    with pytest.raises(TaskStoreError, match="task_not_claimable"):
        control.claim_task(
            window_id=window.id, task_id=second["id"], owner="late-owner", lease_ms=60_000
        )
    assert store._conn.execute(
        "SELECT COUNT(*) AS c FROM platform_coordinator_claims WHERE task_id = ?",
        (second["id"],),
    ).fetchone()["c"] == 0
    assert store._conn.execute(
        "SELECT COUNT(*) AS c FROM platform_budget_reservations WHERE task_id = ?",
        (second["id"],),
    ).fetchone()["c"] == 0
    assert control.get_window(window.id).tasks_started == 1


def test_queue_cancel_event_failure_rolls_back_status_and_event(task_server, monkeypatch) -> None:
    base, server = task_server
    _, created = _req(
        base, "POST", "/api/tasks",
        {"title": "atomic cancel", "executor_kind": "deterministic_fixture"},
    )
    task_id = created["id"]
    store = server.RequestHandlerClass.store
    before_events = store._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events WHERE task_id = ?", (task_id,)
    ).fetchone()["c"]

    def fail_event(**_kwargs):
        raise RuntimeError("injected event failure")

    monkeypatch.setattr(store, "_append_event", fail_event)
    status, payload = _req(base, "POST", f"/api/runs/{task_id}/cancel")
    assert status == 500
    assert payload == {"error": "queue_cancel_failed"}
    assert store.get_task(task_id).status == "QUEUED"
    after_events = store._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events WHERE task_id = ?", (task_id,)
    ).fetchone()["c"]
    assert after_events == before_events


def test_queue_cancel_conditional_update_loss_does_not_claim_success(task_server, monkeypatch) -> None:
    _, server = task_server
    store = server.RequestHandlerClass.store
    task = store.create_task(title="conditional update loss", executor_kind="deterministic_fixture")
    store.set_state(task.id, "RUNNING")
    monkeypatch.setattr(
        store, "_queue_cancel_reason_locked", lambda *_args: "QUEUED_UNCLAIMED"
    )
    outcome = store.cancel_queued_task(task.id)
    assert outcome.status == "UNAVAILABLE"
    assert outcome.reason_code == "STATUS_NOT_CANCELLABLE"
    assert store.get_task(task.id).status == "RUNNING"
    assert store._conn.execute(
        "SELECT COUNT(*) AS c FROM task_events "
        "WHERE task_id = ? AND type = 'QUEUE_CANCELLED'",
        (task.id,),
    ).fetchone()["c"] == 0


def test_execute_endpoint_runs_fixture_and_persists(task_server) -> None:
    base, _ = task_server
    _, created = _req(base, "POST", "/api/tasks", {"title": "exec", "executor_kind": "deterministic_fixture"})
    tid = created["id"]
    status, executed = _req(base, "POST", f"/api/tasks/{tid}/execute")
    assert status == 200
    assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
    assert executed["validation_exit_code"] == 0
    assert executed["validation_command_id"] == "git_diff_check"
    assert executed["changed_files"]
    assert any(e["category"] == "Validation" for e in executed["evidence"])


def test_idempotency_key_across_http_creates_once(task_server) -> None:
    base, _ = task_server
    payload = {"title": "id", "executor_kind": "deterministic_fixture", "idempotency_key": "http-k-1"}
    _, first = _req(base, "POST", "/api/tasks", payload)
    _, second = _req(base, "POST", "/api/tasks", payload)
    assert first["id"] == second["id"]
    _, listed = _req(base, "GET", "/api/tasks")
    assert sum(1 for t in listed["tasks"] if t["id"] == first["id"]) == 1


def test_idempotency_conflict_across_http(task_server) -> None:
    base, _ = task_server
    payload = {"title": "idem", "executor_kind": "deterministic_fixture", "idempotency_key": "http-k-conflict"}
    _req(base, "POST", "/api/tasks", payload)
    status, body = _req(base, "POST", "/api/tasks", {"title": "DIFFERENT", "executor_kind": "deterministic_fixture", "idempotency_key": "http-k-conflict"})
    assert status == 409
    assert "idempotency" in body["error"].lower()


def test_origin_fail_closed(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "GET", "/api/tasks", origin="https://evil.example")
    assert status == 403
    assert body == {"error": "forbidden"}


def test_missing_title_rejected(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "POST", "/api/tasks", {"executor_kind": "deterministic_fixture"})
    assert status == 409
    assert "title_required" in body["error"]


def test_unsupported_executor_kind_rejected(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "POST", "/api/tasks", {"title": "t", "executor_kind": "codex"})
    assert status == 409
    assert "unsupported_executor_kind" in body["error"]


def test_unknown_task_returns_404(task_server) -> None:
    base, _ = task_server
    status, _ = _req(base, "GET", "/api/tasks/task-nonexistent")
    assert status == 404


def test_validate_bind_host_loopback_only() -> None:
    assert validate_bind_host("127.0.0.1") == "127.0.0.1"
    assert validate_bind_host("localhost") == "localhost"
    assert validate_bind_host("::1") == "::1"
    with pytest.raises(ValueError):
        validate_bind_host("0.0.0.0")
    with pytest.raises(ValueError):
        validate_bind_host("192.168.1.1")


def test_task_service_wrapper_starts_and_serves(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "GET", "/api/tasks")
    assert status == 200
    assert "tasks" in body


def test_router_injection_http_execute(task_server) -> None:
    from reverse_agent.platform_v1.task_runtime import (
        ExecutorRouter,
        DeterministicFixtureExecutor,
    )

    base, _ = task_server

    dispatched_kinds: list[str] = []

    class _TracingFixtureExecutor:
        def __init__(self, **kwargs):
            self._inner = DeterministicFixtureExecutor(**kwargs)
        def execute(self, task_id, store, **kw):
            dispatched_kinds.append("deterministic_fixture")
            return self._inner.execute(task_id, store, **kw)
        def __getattr__(self, name):
            return getattr(self._inner, name)

    store = TaskStore(":memory:")
    router = ExecutorRouter()
    router.register("deterministic_fixture", _TracingFixtureExecutor)

    from http.server import ThreadingHTTPServer

    handler_cls = _handler_factory(
        store, router,
        allowed_origin="http://localhost:5173",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        trace_base = "http://127.0.0.1:%d" % port
        _, created = _req(trace_base, "POST", "/api/tasks", {"title": "inj", "executor_kind": "deterministic_fixture"})
        tid = created["id"]
        before = len(dispatched_kinds)
        status, executed = _req(trace_base, "POST", f"/api/tasks/{tid}/execute")
        assert status == 200
        assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
        assert len(dispatched_kinds) > before
        assert dispatched_kinds[-1] == "deterministic_fixture"
    finally:
        server.shutdown()
        server.server_close()


# ---------------------------------------------------------------------------
# Timeline regression (v4-F1): executor runs while state == RUNNING, not VALIDATING
# ---------------------------------------------------------------------------

def test_task_service_executor_runs_while_state_is_running_not_validating(tmp_path) -> None:
    from reverse_agent.platform_v1.task_runtime import (
        DeterministicFixtureExecutor,
    )

    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)

    states_at_dispatch: list[str] = []

    class _TimelineFixtureExecutor:
        def __init__(self, **kwargs):
            self._inner = DeterministicFixtureExecutor(**kwargs)
        def execute(self, task_id, store, **kw):
            states_at_dispatch.append(store.get_task(task_id).status)
            return self._inner.execute(task_id, store, **kw)
        def __getattr__(self, name):
            return getattr(self._inner, name)

    router = ExecutorRouter()
    router.register("deterministic_fixture", _TimelineFixtureExecutor)

    handler_cls = _handler_factory(
        store, router,
        allowed_origin="http://localhost:5173",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = "http://127.0.0.1:%d" % port
        _, created = _req(base, "POST", "/api/tasks", {"title": "timeline", "executor_kind": "deterministic_fixture"})
        tid = created["id"]
        status, executed = _req(base, "POST", f"/api/tasks/{tid}/execute")
        assert status == 200
        assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
        assert states_at_dispatch, "executor must be dispatched"
        for s in states_at_dispatch:
            assert s == "RUNNING", s
            assert s != "VALIDATING", s
            assert s != "READY_FOR_REVIEW", s
    finally:
        server.shutdown()
        server.server_close()


def test_task_service_validator_runs_after_executor(tmp_path) -> None:
    from reverse_agent.platform_v1.task_runtime import (
        ExecutorRouter,
        DeterministicFixtureExecutor,
    )

    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)

    class _StateObserverExecutor:
        def __init__(self, **kwargs):
            self._inner = DeterministicFixtureExecutor(**kwargs)
            self.states: list[tuple[str, str]] = []

        def execute(self, task_id, store, **kw):
            before = store.get_task(task_id).status
            result = self._inner.execute(task_id, store, **kw)
            after = store.get_task(task_id).status
            self.states.append((before, after))
            return result

        def __getattr__(self, name):
            return getattr(self._inner, name)

    router = ExecutorRouter()
    router.register("deterministic_fixture", _StateObserverExecutor)

    handler_cls = _handler_factory(
        store, router,
        allowed_origin="http://localhost:5173",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = "http://127.0.0.1:%d" % port
        _, created = _req(base, "POST", "/api/tasks", {"title": "timeline2", "executor_kind": "deterministic_fixture"})
        tid = created["id"]
        status, executed = _req(base, "POST", f"/api/tasks/{tid}/execute")
        assert status == 200
        assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
        task = store.get_task(tid)
        assert task.validation_exit_code == 0
        assert task.validation_command_id == "git_diff_check"
    finally:
        server.shutdown()
        server.server_close()


def test_frontend_task_test_status_uses_validation_exit_code() -> None:
    from reverse_agent.platform_v1.task_service import _map_task_to_frontend

    ok = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "READY_FOR_REVIEW",
        "executor_kind": "opencode", "validation_exit_code": 0,
        "failure_classification": "",
    })
    assert ok["testStatus"] == "PASS"

    fail = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "FAILED",
        "executor_kind": "opencode", "validation_exit_code": 1,
        "failure_classification": "",
    })
    assert fail["testStatus"] == "FAIL"


def test_frontend_task_test_status_is_running_while_validating() -> None:
    from reverse_agent.platform_v1.task_service import _map_task_to_frontend

    val = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "VALIDATING",
        "executor_kind": "opencode",
    })
    assert val["testStatus"] == "RUNNING"

    running = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "RUNNING",
        "executor_kind": "opencode",
    })
    assert running["testStatus"] == "PENDING"


def test_ready_for_human_next_action_is_executor_neutral() -> None:
    from reverse_agent.platform_v1.task_service import _map_task_to_frontend

    ok = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "READY_FOR_REVIEW",
        "executor_kind": "opencode", "validation_exit_code": 0,
        "failure_classification": "",
    })
    assert ok["state"] == "READY_FOR_HUMAN"
    assert ok["testStatus"] == "PASS"
    assert "fixture" not in ok["nextAction"].lower()


# ---------------------------------------------------------------------------
# Repository selection / discovery
# ---------------------------------------------------------------------------

class _TestRepoAdapter:
    """Minimal fake GitHub adapter returning configured repositories."""

    def __init__(self, repos=None, fail_with=None):
        from reverse_agent.platform_v1.github_adapter import (
            GitHubAdapterError, Repository,
        )
        self._repos = tuple(repos) if repos else ()
        self._fail_with = fail_with
        self.call_count = 0

    def get_workflow_runs(self, repository, exact_head_sha):
        return ()

    def discover_repositories(self):
        from reverse_agent.platform_v1.github_adapter import GitHubAdapterError
        self.call_count += 1
        if self._fail_with is not None:
            raise self._fail_with
        return self._repos


@pytest.fixture()
def task_server_with_github(tmp_path):
    """Task server with an injected fake GitHub adapter."""
    from reverse_agent.platform_v1.github_adapter import Repository
    from reverse_agent.platform_v1.task_service import _handler_factory

    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    repos = (
        Repository(
            full_name="dddd2024/reverse-agent",
            html_url="https://github.com/dddd2024/reverse-agent",
            is_private=False,
            default_branch="main",
        ),
        Repository(
            full_name="dddd2024/another-repo",
            html_url="https://github.com/dddd2024/another-repo",
            is_private=True,
            default_branch="develop",
        ),
    )
    adapter = _TestRepoAdapter(repos=repos)
    handler_cls = _handler_factory(
        store, router,
        allowed_origin="http://localhost:5173",
        github_adapter=adapter,
    )
    from http.server import ThreadingHTTPServer
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:%d" % port, server, adapter
    server.shutdown()
    server.server_close()


def test_opencode_task_without_repository_rejected(task_server) -> None:
    """R2 v2: opencode executor requires an explicit repository; missing -> 409."""
    base_url, server = task_server
    status, body = _req(base_url, "POST", "/api/tasks", {
        "title": "real opencode task",
        "executor_kind": "opencode",
        "idempotency_key": "repo-test-1",
    })
    assert status == 409
    assert "repository_required" in body["error"]


def test_opencode_task_without_repository_rejected_without_origin(tmp_path) -> None:
    """Raw HTTP regression: opencode executor without explicit repository
    must be rejected even when no Origin header is present."""
    import tempfile as _tmp
    import http.client as _http
    import json as _json
    import threading as _thread

    db_path = str(tmp_path / "tasks_no_origin.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    handler_cls = _handler_factory(store, router, allowed_origin="http://localhost:5173")
    from http.server import ThreadingHTTPServer as _Srv
    server = _Srv(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = _thread.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        body_bytes = _json.dumps({
            "title": "opencode-no-origin-no-repo",
            "executor_kind": "opencode",
        }).encode("utf-8")
        conn = _http.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request(
            "POST",
            "/api/tasks",
            body=body_bytes,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        conn.close()
        assert resp.status == 409
        assert "repository_required_for_opencode" in data
    finally:
        server.shutdown()
        server.server_close()


def test_fixture_task_without_repository_still_works(task_server) -> None:
    """deterministic_fixture remains provider-free; no repository required."""
    base_url, server = task_server
    status, _ = _req(base_url, "POST", "/api/tasks", {
        "title": "fixture task",
        "executor_kind": "deterministic_fixture",
        "idempotency_key": "repo-test-2",
    })
    assert status == 201


def test_opencode_task_with_repository_accepted(task_server) -> None:
    """opencode with explicit repository creates successfully."""
    base_url, server = task_server
    status, body = _req(base_url, "POST", "/api/tasks", {
        "title": "real opencode task",
        "executor_kind": "opencode",
        "repository": "https://github.com/dddd2024/reverse-agent",
        "idempotency_key": "repo-test-3",
    })
    assert status == 201
    assert body["repository"] == "https://github.com/dddd2024/reverse-agent"
    assert body["executor_kind"] == "opencode"


def test_repository_catalog_endpoint_success(task_server_with_github) -> None:
    """GET /api/repositories returns sanitized metadata from injected adapter."""
    base_url, server, adapter = task_server_with_github
    status, body = _req(base_url, "GET", "/api/repositories")
    assert status == 200
    repos = body["repositories"]
    assert len(repos) == 2
    assert repos[0]["full_name"] == "dddd2024/reverse-agent"
    assert repos[0]["html_url"] == "https://github.com/dddd2024/reverse-agent"
    assert repos[0]["is_private"] is False
    assert repos[0]["visibility"] == "public"
    assert repos[1]["full_name"] == "dddd2024/another-repo"
    assert repos[1]["is_private"] is True
    assert repos[1]["visibility"] == "private"
    assert body["total"] == 2
    assert adapter.call_count == 1


def test_repository_catalog_endpoint_adapter_unavailable(task_server) -> None:
    """GET /api/repositories without injected adapter -> 503."""
    base_url, server = task_server
    status, body = _req(base_url, "GET", "/api/repositories")
    assert status == 503
    assert body["error"] == "github_adapter_unavailable"


def test_repository_catalog_endpoint_adapter_error_sanitized(task_server_with_github) -> None:
    """GET /api/repositories with failing adapter -> 500 sanitized error."""
    from reverse_agent.platform_v1.github_adapter import GitHubAdapterError
    from reverse_agent.platform_v1.task_service import _handler_factory

    # Re-create server with failing adapter
    base_url, _, _ = task_server_with_github
    server_used, _ = task_server_with_github[:2]
    # We'll just use the adapter that was already created but force it to fail
    # by creating a new server
    import tempfile
    tmp = tempfile.mkdtemp()
    from reverse_agent.platform_v1.run_store import TaskStore as TS
    store2 = TS(db_path=str(tmp + "/t.db"))
    failing_adapter = _TestRepoAdapter(fail_with=GitHubAdapterError("gh_repo_list_failed", "exit=1"))
    handler_cls2 = _handler_factory(
        store2, ExecutorRouter(),
        allowed_origin="http://localhost:5173",
        github_adapter=failing_adapter,
    )
    from http.server import ThreadingHTTPServer
    s2 = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls2)
    port2 = s2.server_address[1]
    t2 = threading.Thread(target=s2.serve_forever, daemon=True)
    t2.start()
    try:
        status, body = _req(
            "http://127.0.0.1:%d" % port2, "GET", "/api/repositories"
        )
        assert status == 500
        assert body["error"] == "repository_discovery_failed"
    finally:
        s2.shutdown()
        s2.server_close()


def test_repository_preserved_in_task_create_readback(task_server) -> None:
    """Selected repository is preserved through create and readback."""
    base_url, server = task_server
    repo_url = "https://github.com/dddd2024/reverse-agent"
    status, body = _req(base_url, "POST", "/api/tasks", {
        "title": "repo-preserved",
        "executor_kind": "opencode",
        "repository": repo_url,
        "idempotency_key": "repo-preserved-1",
    })
    assert status == 201
    task_id = body["id"]
    status2, body2 = _req(base_url, "GET", f"/api/tasks/{task_id}")
    assert status2 == 200
    assert body2["repository"] == repo_url


# ---------------------------------------------------------------------------
# Regression: CombinedTrustedHost production wiring supplies LiveGitHubAdapter
# ---------------------------------------------------------------------------

def test_combined_trusted_host_wires_live_github_adapter(tmp_path) -> None:
    """CombinedTrustedHost start() creates a LiveGitHubAdapter and passes it
    to the Task API handler, so GET /api/repositories never returns 503 in
    production when no explicit adapter was injected.
    """
    from reverse_agent.platform_v1.github_adapter import LiveGitHubAdapter
    from reverse_agent.platform_v1.task_service import _handler_factory
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    host = CombinedTrustedHost()
    assert host.github_adapter is None

    db_path = str(tmp_path / "ctw.db")
    host = CombinedTrustedHost(
        task_db_path=db_path,
        model_control_port=0,
        task_api_port=0,
        allowed_origin="http://localhost:5173",
    )
    host.start()
    try:
        base = host.task_api_url
        assert base.startswith("http://127.0.0.1:")
        status, body = _req(base, "GET", "/api/repositories")
        assert status in (200, 500), (
            f"CombinedTrustedHost must not return 503 github_adapter_unavailable; got {status}: {body}"
        )
    finally:
        host.stop()


def test_combined_trusted_host_allows_fake_adapter_injection(tmp_path) -> None:
    """CombinedTrustedHost still accepts an injected fake adapter for tests."""
    from reverse_agent.platform_v1.github_adapter import (
        FakeGitHubAdapter, Repository,
    )
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    fake = FakeGitHubAdapter(
        repositories=(
            Repository(
                full_name="test/repo",
                html_url="https://github.com/test/repo",
                is_private=False,
                default_branch="main",
            ),
        )
    )
    db_path = str(tmp_path / "ctw2.db")
    host = CombinedTrustedHost(
        task_db_path=db_path,
        model_control_port=0,
        task_api_port=0,
        allowed_origin="http://localhost:5173",
        github_adapter=fake,
    )
    assert host.github_adapter is fake
    host.start()
    try:
        base = host.task_api_url
        status, body = _req(base, "GET", "/api/repositories")
        assert status == 200, body
        assert len(body["repositories"]) == 1
        assert body["repositories"][0]["full_name"] == "test/repo"
    finally:
        host.stop()


# ---------------------------------------------------------------------------
# Issue #192: orchestration_mode HTTP API and dispatch
# ---------------------------------------------------------------------------

def test_create_task_default_orchestration_mode_is_single(task_server) -> None:
    base, _ = task_server
    status, body = _req(
        base, "POST", "/api/tasks", {"title": "default-mode"}
    )
    assert status == 201
    assert body["orchestration_mode"] == "single"
    tid = body["id"]
    status2, got = _req(base, "GET", f"/api/tasks/{tid}")
    assert status2 == 200
    assert got["orchestration_mode"] == "single"


def test_create_task_sequential_team_persists_and_readback(task_server) -> None:
    base, _ = task_server
    payload = {
        "title": "seq task",
        "executor_kind": "opencode",
        "repository": "https://github.com/dddd2024/reverse-agent",
        "orchestration_mode": "sequential_team",
        "idempotency_key": "issue192-seq-create-1",
    }
    status, created = _req(base, "POST", "/api/tasks", payload)
    assert status == 201
    assert created["orchestration_mode"] == "sequential_team"
    assert created["executor_kind"] == "opencode"
    tid = created["id"]
    status2, got = _req(base, "GET", f"/api/tasks/{tid}")
    assert status2 == 200
    assert got["orchestration_mode"] == "sequential_team"


def test_create_task_invalid_orchestration_mode_fails_closed(task_server) -> None:
    base, _ = task_server
    status, body = _req(
        base,
        "POST",
        "/api/tasks",
        {
            "title": "bad",
            "executor_kind": "opencode",
            "repository": "https://github.com/dddd2024/reverse-agent",
            "orchestration_mode": "parallel",
        },
    )
    assert status == 409
    assert "unsupported_orchestration_mode" in body["error"]


def test_create_task_sequential_team_with_fixture_fails_closed(task_server) -> None:
    base, _ = task_server
    status, body = _req(
        base,
        "POST",
        "/api/tasks",
        {
            "title": "bad",
            "executor_kind": "deterministic_fixture",
            "orchestration_mode": "sequential_team",
        },
    )
    assert status == 409
    assert "sequential_team_requires_opencode_executor" in body["error"]


def test_sequential_task_execute_dispatches_to_sequential_team_method_once(
    tmp_path,
) -> None:
    from reverse_agent.platform_v1.task_execution import TaskExecutionService
    from reverse_agent.platform_v1.task_runtime import (
        ExecutorRuntimeError,
        ExecutorRouter,
    )

    db_path = str(tmp_path / "seq_dispatch.sqlite3")
    store = TaskStore(db_path=db_path)

    class _TracingTaskExecutionService(TaskExecutionService):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.execute_calls = 0
            self.execute_sequential_team_calls = 0

        def execute(self, task_id, **kwargs):
            self.execute_calls += 1
            raise ExecutorRuntimeError("traced", "execute should not be called")

        def execute_sequential_team(self, task_id, **kwargs):
            self.execute_sequential_team_calls += 1
            from reverse_agent.platform_v1.task_execution import TaskExecutionError
            raise TaskExecutionError("traced_sequential")

    router = ExecutorRouter()
    svc = _TracingTaskExecutionService(
        store=store, router=router,
    )

    seq_task = store.create_task(
        title="seq dispatch",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(seq_task.id, "QUEUED")

    try:
        svc.execute_sequential_team(
            task_id=seq_task.id,
            workspace_root=str(tmp_path / "ws"),
        )
    except Exception:
        pass

    assert svc.execute_calls == 0
    assert svc.execute_sequential_team_calls == 1


def test_http_resume_sequential_routes_to_durable_recovery_once(
    tmp_path, monkeypatch
) -> None:
    """The public resume route must preserve the sequential durable path.

    This is provider-free: a tracing service replaces durable execution and
    proves that the API dispatches exactly one sequential resume, never the
    single-mode path.
    """
    from http.server import ThreadingHTTPServer
    import reverse_agent.platform_v1.task_service as task_service_module

    store = TaskStore(db_path=str(tmp_path / "resume-route.sqlite3"))
    task = store.create_task(
        title="issue-246-http-resume",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store._acquire_durable_lease(
        task_id=task.id,
        execution_id=f"exec-{task.id}",
        lease_owner="expired-worker",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )

    calls = []

    class TracingDurableExecutionService:
        def __init__(self, **kwargs):
            self.store = kwargs["store"]

        def resume_single(self, **kwargs):
            raise AssertionError("single resume must not be selected")

        def resume_sequential_team(self, **kwargs):
            calls.append(kwargs)
            return object()

    monkeypatch.setattr(
        task_service_module,
        "DurableExecutionService",
        TracingDurableExecutionService,
    )
    handler_cls = _handler_factory(
        store,
        ExecutorRouter(),
        allowed_origin="http://localhost:5173",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        status, body = _req(base, "POST", f"/api/tasks/{task.id}/resume")
        assert status == 200
        assert body["id"] == task.id
    finally:
        server.shutdown()
        server.server_close()

    assert calls == [{"task_id": task.id, "lease_owner": "task-api-resume"}]


def test_single_task_execute_does_not_call_sequential_team(tmp_path) -> None:
    from reverse_agent.platform_v1.task_execution import TaskExecutionService
    from reverse_agent.platform_v1.task_runtime import (
        ExecutorRuntimeError,
        ExecutorRouter,
    )

    db_path = str(tmp_path / "single_dispatch.sqlite3")
    store = TaskStore(db_path=db_path)

    class _TracingService(TaskExecutionService):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.execute_calls = 0
            self.execute_sequential_team_calls = 0

        def execute(self, task_id, **kwargs):
            self.execute_calls += 1
            raise ExecutorRuntimeError("traced", "execute called")

        def execute_sequential_team(self, task_id, **kwargs):
            self.execute_sequential_team_calls += 1
            raise ExecutorRuntimeError("traced_seq", "seq should not be called")

    router = ExecutorRouter()
    svc = _TracingService(store=store, router=router)

    single_task = store.create_task(
        title="single dispatch",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    try:
        svc.execute(
            task_id=single_task.id,
            workspace_root=str(tmp_path / "ws"),
        )
    except Exception:
        pass

    assert svc.execute_calls == 1
    assert svc.execute_sequential_team_calls == 0


def test_http_execute_uses_persisted_mode_not_request_override(tmp_path) -> None:
    from http.server import ThreadingHTTPServer
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    db_path = str(tmp_path / "persist_mode.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    handler_cls = _handler_factory(store, router, allowed_origin="http://localhost:5173")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = "http://127.0.0.1:%d" % port
        _, created = _req(
            base,
            "POST",
            "/api/tasks",
            {
                "title": "persist-mode-test",
                "executor_kind": "opencode",
                "repository": "https://github.com/dddd2024/reverse-agent",
                "orchestration_mode": "sequential_team",
            },
        )
        assert created["orchestration_mode"] == "sequential_team"
        tid = created["id"]

        override_body = {"orchestration_mode": "single", "validation_command_id": "x"}
        _req(base, "POST", f"/api/tasks/{tid}/execute", override_body)

        task_after = store.get_task(tid)
        assert task_after.orchestration_mode == "sequential_team"
    finally:
        server.shutdown()
        server.server_close()


def test_sequential_task_preserves_binding_ref_through_http(
    task_server,
) -> None:
    base, _ = task_server
    payload = {
        "title": "seq-binding",
        "executor_kind": "opencode",
        "repository": "https://github.com/dddd2024/reverse-agent",
        "orchestration_mode": "sequential_team",
        "binding_ref": "coding-fast",
        "model_profile_ref": "legacy-profile",
        "idempotency_key": "issue192-seq-binding-1",
    }
    status, created = _req(base, "POST", "/api/tasks", payload)
    assert status == 201
    assert created["binding_ref"] == "coding-fast"
    assert created["orchestration_mode"] == "sequential_team"
    assert created["model_profile_ref"] == "legacy-profile"
    tid = created["id"]
    status2, got = _req(base, "GET", f"/api/tasks/{tid}")
    assert status2 == 200
    assert got["binding_ref"] == "coding-fast"
    assert got["orchestration_mode"] == "sequential_team"
    assert got["model_profile_ref"] == "legacy-profile"


def test_http_execute_mode_dispatches_correctly_for_sequential_team(
    tmp_path,
) -> None:
    from http.server import ThreadingHTTPServer
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    db_path = str(tmp_path / "http-seq-dispatch.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    handler_cls = _handler_factory(store, router, allowed_origin="http://localhost:5173")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = "http://127.0.0.1:%d" % port
        _, created = _req(
            base,
            "POST",
            "/api/tasks",
            {
                "title": "http-seq-test",
                "executor_kind": "opencode",
                "repository": "https://github.com/dddd2024/reverse-agent",
                "orchestration_mode": "sequential_team",
                "binding_ref": "coding-fast",
            },
        )
        assert created["orchestration_mode"] == "sequential_team"
        assert created["binding_ref"] == "coding-fast"
        tid = created["id"]

        _req(base, "POST", f"/api/tasks/{tid}/execute", {})

        task_after = store.get_task(tid)
        assert task_after.orchestration_mode == "sequential_team"
        assert task_after.binding_ref == "coding-fast"
    finally:
        server.shutdown()
        server.server_close()


def test_http_response_contains_no_credentials(task_server) -> None:
    import re
    base, _ = task_server
    payload = {
        "title": "no-leak",
        "executor_kind": "opencode",
        "repository": "https://github.com/dddd2024/reverse-agent",
        "orchestration_mode": "single",
        "binding_ref": "coding-fast",
    }
    status, created = _req(base, "POST", "/api/tasks", payload)
    assert status == 201
    response_text = json.dumps(created)
    assert not re.search(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9+/=]{16,}", response_text)
    assert not re.search(r"(?i)bearer\s+[a-zA-Z0-9+/=]{16,}", response_text)
    assert not re.search(r"(?i)(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{20,}", response_text)


def test_single_mode_execute_backward_compatible_http(tmp_path) -> None:
    from http.server import ThreadingHTTPServer
    from reverse_agent.platform_v1.task_runtime import (
        ExecutorRouter,
        DeterministicFixtureExecutor,
    )

    db_path = str(tmp_path / "bc-single.sqlite3")
    store = TaskStore(db_path=db_path)

    dispatched: list[str] = []

    class _TraceFixtureExecutor:
        def __init__(self, **kwargs):
            self._inner = DeterministicFixtureExecutor(**kwargs)
        def execute(self, task_id, store, **kw):
            dispatched.append("deterministic_fixture")
            return self._inner.execute(task_id, store, **kw)
        def __getattr__(self, name):
            return getattr(self._inner, name)

    router = ExecutorRouter()
    router.register("deterministic_fixture", _TraceFixtureExecutor)

    handler_cls = _handler_factory(
        store, router,
        allowed_origin="http://localhost:5173",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = "http://127.0.0.1:%d" % port
        _, created = _req(
            base,
            "POST",
            "/api/tasks",
            {"title": "bc-single", "executor_kind": "deterministic_fixture"},
        )
        assert created["orchestration_mode"] == "single"
        tid = created["id"]
        status, executed = _req(base, "POST", f"/api/tasks/{tid}/execute")
        assert status == 200
        assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
        assert executed["orchestration_mode"] == "single"
        assert len(dispatched) == 1
        assert dispatched[0] == "deterministic_fixture"
    finally:
        server.shutdown()
        server.server_close()


def test_binding_ref_and_orchestration_mode_persisted_together(
    tmp_path,
) -> None:
    import sqlite3 as _sqlite3
    db_path = str(tmp_path / "persist-together.sqlite3")
    store = TaskStore(db_path=db_path)
    task = store.create_task(
        title="persist-both",
        executor_kind="opencode",
        binding_ref="coding-fast",
        orchestration_mode="sequential_team",
    )
    raw = store._conn.execute(
        "SELECT binding_ref, orchestration_mode FROM tasks WHERE id = ?",
        (task.id,),
    ).fetchone()
    assert raw["binding_ref"] == "coding-fast"
    assert raw["orchestration_mode"] == "sequential_team"


# ---------------------------------------------------------------------------
# Issue #265 / #260: Inbox, Roadmap and Agent Runs read-model endpoints
# ---------------------------------------------------------------------------

def test_inbox_capture_list_promote_dismiss_over_http(task_server) -> None:
    base, _ = task_server
    status, item = _req(base, "POST", "/api/inbox", {
        "title": "Idea", "objective": "做一个无人值守平台",
    })
    assert status == 201
    assert item["status"] == "CAPTURED"
    assert item["promoted_goal_id"] == ""

    status, listing = _req(base, "GET", "/api/inbox")
    assert status == 200
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == item["id"]

    status, promoted = _req(base, "POST", f"/api/inbox/{item['id']}/promote")
    assert status == 200
    goal_id = promoted["goal"]["id"]
    assert promoted["goal"]["status"] == "DRAFT"
    assert promoted["item"]["promoted_goal_id"] == goal_id

    status, again = _req(base, "POST", f"/api/inbox/{item['id']}/promote")
    assert status == 200
    assert again["goal"]["id"] == goal_id

    status, goals = _req(base, "GET", "/api/goals")
    assert status == 200
    assert goals["total"] == 1

    status, other = _req(base, "POST", "/api/inbox", {"objective": "第二个想法"})
    assert status == 201
    status, dismissed = _req(base, "POST", f"/api/inbox/{other['id']}/dismiss")
    assert status == 200
    assert dismissed["status"] == "DISMISSED"

    status, history = _req(base, "GET", "/api/inbox")
    assert history["total"] == 2

    status, _ = _req(base, "POST", f"/api/inbox/{other['id']}/promote")
    assert status == 409


def test_inbox_capture_rejects_secret_fields_over_http(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "POST", "/api/inbox", {
        "objective": "x", "api_key": "k" * 20,
    })
    assert status == 409
    assert "sensitive_control_field_rejected" in body["error"]


def test_roadmap_phase_lifecycle_and_derived_status_over_http(task_server) -> None:
    base, _ = task_server
    status, goal = _req(base, "POST", "/api/goals", {
        "objective": "roadmap goal",
        "idempotency_key": "roadmap-http-1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    assert status == 201

    status, phase = _req(base, "POST", "/api/roadmap", {
        "title": "Phase 0", "position": 1, "description": "基础",
    })
    assert status == 201
    assert phase["derived_status"] == "PLANNED"
    assert phase["goals"] == []

    status, attached = _req(base, "POST", f"/api/roadmap/{phase['id']}/attach", {
        "goal_id": goal["id"],
    })
    assert status == 200
    assert attached["goals"][0]["id"] == goal["id"]
    assert attached["derived_status"] == "PLANNED"

    status, planned = _req(base, "POST", f"/api/goals/{goal['id']}/plan", {
        "expected_revision": 1,
        "tasks": [{"id": "T001", "title": "t", "instruction": "i"}],
    })
    assert status == 200
    status, approved = _req(base, "POST", f"/api/goals/{goal['id']}/approve", {
        "expected_revision": 1,
    })
    assert status == 200

    status, listing = _req(base, "GET", "/api/roadmap")
    assert status == 200
    assert listing["phases"][0]["derived_status"] == "PLANNED"
    assert listing["phases"][0]["goals"][0]["status"] == "APPROVED"

    status, _ = _req(base, "POST", f"/api/roadmap/{phase['id']}/detach", {
        "goal_id": goal["id"],
    })
    assert status == 200
    status, detached = _req(base, "GET", "/api/roadmap")
    assert detached["phases"][0]["goals"] == []

    status, _ = _req(base, "POST", f"/api/roadmap/{phase['id']}/attach", {})
    assert status == 400


def test_agent_runs_listing_and_detail_over_http(task_server) -> None:
    base, _ = task_server
    status, goal = _req(base, "POST", "/api/goals", {
        "objective": "runs goal",
        "idempotency_key": "runs-http-1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    assert status == 201
    status, launched_plan = _req(base, "POST", f"/api/goals/{goal['id']}/plan", {
        "expected_revision": 1,
        "tasks": [{"id": "T001", "title": "step", "instruction": "run"}],
    })
    assert status == 200
    status, approved = _req(base, "POST", f"/api/goals/{goal['id']}/approve", {
        "expected_revision": 1,
    })
    assert status == 200

    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    status, window = _req(base, "POST", "/api/windows/activate", {
        "policy_id": "runs-window-1", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": [goal["repository"]], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 5, "max_retries": 0,
        "confirmation": "ACTIVATE",
    })
    assert status == 201
    status, launched = _req(base, "POST", f"/api/goals/{goal['id']}/launch", {
        "expected_revision": 1, "window_id": window["id"],
    })
    assert status == 200
    task_id = launched["task_links"][0]["task_id"]

    status, runs = _req(base, "GET", "/api/runs")
    assert status == 200
    assert runs["total"] == 1
    run = runs["runs"][0]
    assert run["task_id"] == task_id
    assert run["goal_id"] == goal["id"]
    assert run["state"] in {"WAITING_FOR_OWNER", "RUNNING"}
    assert run["stage"] in {"PLAN", "EXECUTE", "VERIFY", "PUBLISH", "UNKNOWN"}
    assert run["liveness"] in {"WAITING", "ACTIVE", "UNKNOWN"}
    assert "raw_log" not in json.dumps(run)
    assert "metadata" not in json.dumps(run)

    status, detail = _req(base, "GET", f"/api/runs/{task_id}")
    assert status == 200
    assert detail["task_id"] == task_id
    assert detail["events"][0]["type"] == "DISCOVERED"
    assert detail["events"][0]["category"] == "PLAN"
    assert "raw_log" not in json.dumps(detail)
    assert "metadata" not in json.dumps(detail)

    status, missing = _req(base, "GET", "/api/runs/task-missing")
    assert status == 404


def test_new_read_model_routes_fail_closed_on_unknown_paths(task_server) -> None:
    base, _ = task_server
    status, _ = _req(base, "GET", "/api/inbox/extra/segments")
    assert status == 404
    status, _ = _req(base, "POST", "/api/inbox/x/unknown", {})
    assert status == 404
    status, _ = _req(base, "GET", "/api/roadmap/phase-x")
    assert status == 404


def test_goal_http_list_and_detail_converge_on_task_status(task_server) -> None:
    base, server = task_server
    store = server.RequestHandlerClass.store

    status, goal = _req(base, "POST", "/api/goals", {
        "objective": "HTTP goal convergence",
        "repository": "dddd2024/reverse-agent",
        "idempotency_key": "http-goal-converge-v1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    assert status == 201
    goal_id = goal["id"]
    _req(base, "POST", f"/api/goals/{goal_id}/plan", {"expected_revision": 1})
    _req(base, "POST", f"/api/goals/{goal_id}/approve", {"expected_revision": 1})

    now = datetime.now(timezone.utc)
    status, window = _req(base, "POST", "/api/windows/activate", {
        "policy_id": "http-converge-window", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 3, "max_retries": 0,
        "confirmation": "ACTIVATE",
    })
    assert status == 201
    status, launched = _req(base, "POST", f"/api/goals/{goal_id}/launch", {
        "expected_revision": 1, "window_id": window["id"],
    })
    assert status == 200 and launched["status"] == "RUNNING"
    assert len(launched["task_links"]) == 3

    for link in launched["task_links"]:
        store.set_state(link["task_id"], "READY_FOR_REVIEW")

    status, listed = _req(base, "GET", "/api/goals")
    assert status == 200
    listed_goal = next(g for g in listed["goals"] if g["id"] == goal_id)
    status, detail = _req(base, "GET", f"/api/goals/{goal_id}")
    assert status == 200

    assert listed_goal["status"] == "COMPLETED"
    assert detail["status"] == "COMPLETED"
    assert listed_goal["status"] == detail["status"]
    assert len(listed_goal["task_links"]) == 3
    assert {link["status"] for link in listed_goal["task_links"]} == {"READY_FOR_REVIEW"}
    assert [link["task_id"] for link in listed_goal["task_links"]] == [
        link["task_id"] for link in detail["task_links"]
    ]


def _launch_http_goal(base, goal_key_suffix):
    status, goal = _req(base, "POST", "/api/goals", {
        "objective": "HTTP convergence " + goal_key_suffix,
        "repository": "dddd2024/reverse-agent",
        "idempotency_key": "http-goal-" + goal_key_suffix + "-v1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    assert status == 201
    goal_id = goal["id"]
    _req(base, "POST", f"/api/goals/{goal_id}/plan", {"expected_revision": 1})
    _req(base, "POST", f"/api/goals/{goal_id}/approve", {"expected_revision": 1})
    now = datetime.now(timezone.utc)
    status, window = _req(base, "POST", "/api/windows/activate", {
        "policy_id": "http-" + goal_key_suffix + "-window", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 3, "max_retries": 0,
        "confirmation": "ACTIVATE",
    })
    assert status == 201
    status, launched = _req(base, "POST", f"/api/goals/{goal_id}/launch", {
        "expected_revision": 1, "window_id": window["id"],
    })
    assert status == 200
    return goal_id, launched


def test_goal_http_converges_to_blocked_on_failed_task(task_server) -> None:
    base, server = task_server
    store = server.RequestHandlerClass.store
    goal_id, launched = _launch_http_goal(base, "failed")
    links = launched["task_links"]
    store.set_state(links[0]["task_id"], "FAILED")
    status, listed = _req(base, "GET", "/api/goals")
    listed_goal = next(g for g in listed["goals"] if g["id"] == goal_id)
    status, detail = _req(base, "GET", f"/api/goals/{goal_id}")
    assert listed_goal["status"] == "BLOCKED"
    assert detail["status"] == "BLOCKED"
    assert listed_goal["status"] == detail["status"]
    assert any(link["task_id"] == links[0]["task_id"] and link["status"] == "FAILED"
               for link in listed_goal["task_links"])


def test_goal_http_converges_to_blocked_on_blocked_task(task_server) -> None:
    base, server = task_server
    store = server.RequestHandlerClass.store
    goal_id, launched = _launch_http_goal(base, "blocked")
    links = launched["task_links"]
    store.set_state(links[0]["task_id"], "BLOCKED")
    status, listed = _req(base, "GET", "/api/goals")
    listed_goal = next(g for g in listed["goals"] if g["id"] == goal_id)
    status, detail = _req(base, "GET", f"/api/goals/{goal_id}")
    assert listed_goal["status"] == "BLOCKED"
    assert detail["status"] == "BLOCKED"
    assert listed_goal["status"] == detail["status"]
    assert any(link["task_id"] == links[0]["task_id"] and link["status"] == "BLOCKED"
               for link in listed_goal["task_links"])


def test_goal_http_converges_to_blocked_on_cancelled_task(task_server) -> None:
    base, server = task_server
    store = server.RequestHandlerClass.store
    goal_id, launched = _launch_http_goal(base, "cancelled")
    links = launched["task_links"]
    store.set_state(links[0]["task_id"], "CANCELLED")
    status, listed = _req(base, "GET", "/api/goals")
    listed_goal = next(g for g in listed["goals"] if g["id"] == goal_id)
    status, detail = _req(base, "GET", f"/api/goals/{goal_id}")
    assert listed_goal["status"] == "BLOCKED"
    assert detail["status"] == "BLOCKED"
    assert listed_goal["status"] == detail["status"]
    assert any(link["task_id"] == links[0]["task_id"] and link["status"] == "CANCELLED"
               for link in listed_goal["task_links"])
    assert any(link["task_id"] == links[0]["task_id"] and link["status"] == "CANCELLED"
               for link in detail["task_links"])


def test_goal_http_cancel_endpoint_converges_without_cascade(task_server) -> None:
    base, server = task_server
    goal_id, launched = _launch_http_goal(base, "queue-cancel-convergence")
    task_id = launched["task_links"][0]["task_id"]
    store = server.RequestHandlerClass.store
    control = server.RequestHandlerClass.control_store
    other = store.create_task(
        title="same goal remains queued",
        repository="dddd2024/reverse-agent",
        executor_kind="deterministic_fixture",
    )
    control.link_goal_task(
        goal_id,
        goal_revision=1,
        plan_task_id="T999",
        task_id=other.id,
        dependencies=[],
        seq=1,
    )
    assert store.get_task(other.id).status == "QUEUED"
    status, result = _req(base, "POST", f"/api/runs/{task_id}/cancel")
    assert status == 200
    assert result == {"status": "APPLIED"}

    status, goals = _req(base, "GET", "/api/goals")
    assert status == 200
    listed_goal = next(goal for goal in goals["goals"] if goal["id"] == goal_id)
    status, detail = _req(base, "GET", f"/api/goals/{goal_id}")
    assert status == 200
    assert listed_goal["status"] == "BLOCKED"
    assert detail["status"] == "BLOCKED"
    links = {link["task_id"]: link["status"] for link in detail["task_links"]}
    assert links[task_id] == "CANCELLED"
    assert links[other.id] == "QUEUED"
    assert server.RequestHandlerClass.store.get_task(task_id).status == "CANCELLED"
    assert server.RequestHandlerClass.store.get_task(other.id).status == "QUEUED"
