from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer

from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.system_doctor import (
    BLOCKED,
    DEGRADED,
    READY,
    UNKNOWN,
    DoctorCheck,
    SystemDoctor,
    aggregate_state,
)
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import _handler_factory


def _check(state: str, *, required: bool = True, check_id: str = "check") -> DoctorCheck:
    return DoctorCheck(
        id=check_id,
        component="test",
        state=state,
        required=required,
        summary="bounded test check",
        reason_code="test_reason",
        remediation_id="none",
    )


def _by_id(report: dict) -> dict[str, dict]:
    return {check["id"]: check for check in report["checks"]}


def _runtime_status() -> dict[str, object]:
    return {"service": "reverse-agent-platform-v2"}


def test_aggregate_state_uses_fail_closed_precedence() -> None:
    assert aggregate_state((_check(READY),)) == READY
    assert aggregate_state((_check(READY), _check(DEGRADED, required=False))) == DEGRADED
    assert aggregate_state((_check(UNKNOWN), _check(DEGRADED, required=False))) == UNKNOWN
    assert aggregate_state((_check(UNKNOWN), _check(BLOCKED))) == BLOCKED


def test_file_backed_store_proves_core_checks_but_not_unintegrated_truth(tmp_path) -> None:
    store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    report = SystemDoctor(store=store, runtime_status_provider=_runtime_status).run()
    checks = _by_id(report)

    assert report["schema_version"] == 1
    assert report["state"] == UNKNOWN
    assert [check["id"] for check in report["checks"]] == [
        "task_api_reachable",
        "task_store_readable",
        "task_store_storage_path",
        "runtime_status_available",
        "repository_workspace_readiness",
        "executor_readiness",
        "connection_binding_readiness",
        "desktop_lifecycle_readiness",
    ]
    assert checks["task_api_reachable"]["state"] == READY
    assert checks["task_store_readable"]["state"] == READY
    assert checks["task_store_storage_path"]["state"] == READY
    assert checks["runtime_status_available"]["state"] == READY
    assert checks["repository_workspace_readiness"]["state"] == UNKNOWN
    assert checks["executor_readiness"]["state"] == UNKNOWN
    assert checks["connection_binding_readiness"]["state"] == UNKNOWN
    assert checks["desktop_lifecycle_readiness"]["state"] == UNKNOWN


def test_in_memory_store_does_not_claim_durable_storage_readiness() -> None:
    report = SystemDoctor(
        store=TaskStore(":memory:"),
        runtime_status_provider=_runtime_status,
    ).run()
    storage = _by_id(report)["task_store_storage_path"]

    assert storage["state"] == UNKNOWN
    assert storage["reason_code"] == "task_store_path_non_durable"
    assert report["state"] == UNKNOWN


def test_store_failure_is_blocked_and_exception_secret_is_not_exposed() -> None:
    secret = "SECRET_SENTINEL_697_STORE"

    class BrokenStore:
        db_path = ":memory:"

        def count_tasks(self) -> int:
            raise RuntimeError(secret)

    report = SystemDoctor(
        store=BrokenStore(),
        runtime_status_provider=_runtime_status,
    ).run()
    readable = _by_id(report)["task_store_readable"]

    assert report["state"] == BLOCKED
    assert readable["state"] == BLOCKED
    assert readable["reason_code"] == "task_store_read_failed"
    assert secret not in json.dumps(report, sort_keys=True)


def test_runtime_failure_is_blocked_and_exception_secret_is_not_exposed() -> None:
    secret = "SECRET_SENTINEL_697_RUNTIME"

    def broken_runtime() -> dict[str, object]:
        raise RuntimeError(secret)

    report = SystemDoctor(
        store=TaskStore(":memory:"),
        runtime_status_provider=broken_runtime,
    ).run()
    runtime = _by_id(report)["runtime_status_available"]

    assert report["state"] == BLOCKED
    assert runtime["state"] == BLOCKED
    assert runtime["reason_code"] == "runtime_status_unavailable"
    assert secret not in json.dumps(report, sort_keys=True)


def test_doctor_does_not_probe_unowned_store_capabilities() -> None:
    class GuardedStore:
        db_path = ":memory:"

        def count_tasks(self) -> int:
            return 0

        def __getattr__(self, name: str):
            raise AssertionError(f"unexpected_store_probe:{name}")

    report = SystemDoctor(
        store=GuardedStore(),
        runtime_status_provider=_runtime_status,
    ).run()

    assert report["state"] == UNKNOWN


def _request(base_url: str, *, origin: str) -> tuple[int, dict]:
    host, port = base_url.replace("http://", "").split(":", 1)
    conn = http.client.HTTPConnection(host, int(port), timeout=10)
    conn.request(
        "GET",
        "/api/platform/doctor",
        headers={"Accept": "application/json", "Origin": origin},
    )
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()
    return response.status, payload


def test_http_doctor_route_is_read_only_structured_and_origin_fail_closed(tmp_path) -> None:
    store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    handler = _handler_factory(
        store,
        ExecutorRouter(),
        allowed_origin="http://localhost:5173",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        status, report = _request(base, origin="http://localhost:5173")
        assert status == 200
        assert report["schema_version"] == 1
        assert report["state"] == UNKNOWN
        assert _by_id(report)["task_store_readable"]["state"] == READY

        forbidden_status, forbidden = _request(base, origin="http://evil.example")
        assert forbidden_status == 403
        assert forbidden == {"error": "forbidden"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
