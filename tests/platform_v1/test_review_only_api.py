"""Real loopback HTTP path; injected provider-free review role, never a model."""
import http.client
from http.server import ThreadingHTTPServer
import json
from threading import Thread

import pytest

from test_review_execution import setup_review
from reverse_agent.platform_v1.task_service import _handler_factory


@pytest.fixture
def review_server(tmp_path, monkeypatch):
    fixture = setup_review(tmp_path, monkeypatch)
    handler = _handler_factory(fixture.store, fixture.router, allowed_origin="http://localhost:5173")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield fixture, server.server_address[1]
    server.shutdown()
    server.server_close()
    thread.join(5)


def request(port, path, body, origin="http://localhost:5173"):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        connection.request("POST", path, json.dumps(body), headers={
            "Content-Type": "application/json", "Origin": origin,
        })
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


def test_http_review_completes_task_and_remains_functionally_unverified(review_server):
    f, port = review_server
    status, body = request(port, f"/api/tasks/{f.task.id}/review", f.request)
    assert status == 200 and body["status"] == "READY_FOR_REVIEW"
    assert len(f.calls) == 1 and not body["changed_files"]
    assert body["frontend_task"]["testStatus"] == "PENDING"
    assert body["validation_exit_code"] is None
    record = json.loads(next(e for e in body["evidence"] if e["category"] == "Review")["detail"])
    assert record["functional_verification"] is False
    assert record["independent_acceptance"] is False
    status, _ = request(port, f"/api/tasks/{f.task.id}/review", f.request)
    assert status == 409 and len(f.calls) == 1


@pytest.mark.parametrize("extra", ["repo_dir", "workspace_root", "executor_kind", "model", "policy", "tools"])
def test_http_cannot_supply_execution_authority(review_server, extra):
    f, port = review_server
    status, body = request(port, f"/api/tasks/{f.task.id}/review",
                           {**f.request, extra: "private forbidden value"})
    assert status == 400 and body == {"error": "review_request_invalid"}
    assert not f.calls and f.store.get_task(f.task.id).status == "QUEUED"


def test_http_rejects_untrusted_origin_before_task_or_git(review_server):
    f, port = review_server
    status, _ = request(port, f"/api/tasks/{f.task.id}/review", f.request, origin="https://attacker.invalid")
    assert status == 403 and not f.calls
    assert f.store.get_task(f.task.id).status == "QUEUED"


def test_http_missing_task_is_bounded_404(review_server):
    f, port = review_server
    status, body = request(port, "/api/tasks/missing/review", f.request)
    assert status == 404 and body == {"error": "task not found"} and not f.calls
