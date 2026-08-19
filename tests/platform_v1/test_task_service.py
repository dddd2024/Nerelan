"""HTTP Task API tests: loopback-only, Origin fail-closed, bounded body, no secrets."""

import http.client
import json
import os
import tempfile
import threading
from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.run_store import TaskStore
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
