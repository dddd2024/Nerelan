"""Real loopback Task API, disk SQLite and Git/pytest; only model/binding are doubles."""
import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from test_goal_functional_checks import goal_checks, planned_check
from test_functional_execution import LocalBinding, LocalImplementation
from reverse_agent.platform_v1.artifact_handoff import load_input_binding
from reverse_agent.platform_v1.functional_validation import functional_evidence
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import _handler_factory


@pytest.mark.parametrize("mode", ["single", "sequential_team"])
def test_http_selection_clear_approval_launch_and_input_proof(goal_checks, tmp_path, monkeypatch, mode):
    root, base, store, control, service, goal, window = goal_checks
    if mode != goal.orchestration_mode:
        goal = service.amend(goal.id, expected_revision=goal.revision, objective=goal.objective, orchestration_mode=mode)
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    monkeypatch.setenv("REVERSE_AGENT_TASK_WORKSPACE_ROOT", str(tmp_path / "worktrees"))
    created = []
    router = ExecutorRouter()
    def factory(**kwargs):
        executor = LocalImplementation(root, kwargs.get("base_ref") or base, "value = 2\n")
        created.append(executor)
        return executor
    router.replace("opencode", factory)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_factory(store, router,
        allowed_origin="http://localhost:5173", binding_resolver=LocalBinding(),
        execution_authority_sha="artifact-http-authority", planning_sha="artifact-http-plan"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(path, body=None):
        req = Request(f"http://127.0.0.1:{server.server_port}" + path,
                      data=json.dumps(body).encode() if body is not None else None,
                      headers={"Origin": "http://localhost:5173", "Content-Type": "application/json"})
        with urlopen(req, timeout=120) as response:
            return json.load(response)
    try:
        prefix = f"/api/goals/{goal.id}"
        tasks = [planned_check("A"), {**planned_check("B"), "dependencies": ["A"],
            "capability": "validate_task", "artifact_input": {"plan_task_id": "A"}}]
        selected = request(prefix + "/plan", {"expected_revision": goal.revision, "tasks": tasks})
        removed_tasks = [{**task, "artifact_input": None} for task in selected["tasks"]]
        removed = request(prefix + "/plan", {"expected_revision": selected["revision"], "tasks": removed_tasks})
        assert removed["revision"] > selected["revision"]
        assert removed["artifact_digest"] != selected["artifact_digest"]
        assert removed["tasks"][1].get("artifact_input") is None
        with pytest.raises(HTTPError) as stale:
            request(prefix + "/approve", {"expected_revision": selected["revision"]})
        assert stale.value.code == 409
        restored = request(prefix + "/plan", {"expected_revision": removed["revision"], "tasks": tasks})
        request(prefix + "/approve", {"expected_revision": restored["revision"]})
        launched = request(prefix + "/launch", {"expected_revision": restored["revision"], "window_id": window.id})
        links = control.list_goal_tasks(goal.id)
        assert len(links) == 2
        producer, consumer = [link["task_id"] for link in links]
        request(f"/api/tasks/{producer}/execute", {})
        request(f"/api/tasks/{consumer}/execute", {})
        detail = request(f"/api/tasks/{consumer}")
        proof = detail["frontend_task"]["functionalValidation"]
        assert proof["verified"] is True
        assert proof["artifact_input"]["task_id"] == producer
        assert proof["checks"][0]["test_report"]["tests"] == 1
        assert created[1].calls == [] and len(created) == 2
        assert request(prefix)["artifact_digest"] == launched["artifact_digest"]
        reopened = TaskStore(store.db_path)
        try:
            task = reopened.get_task(consumer)
            assert functional_evidence(task) == proof
            assert load_input_binding(task)["producer"]["task_id"] == producer
        finally:
            reopened._conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
