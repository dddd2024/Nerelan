"""Goal truth over real HTTP/Git/pytest/SQLite; model/binding are local doubles."""
from contextlib import contextmanager
import json
import sqlite3
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

import pytest

from test_goal_functional_checks import goal_checks, launch_checks
from test_functional_execution import LocalBinding, LocalImplementation, ordinary, setup_execution
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.functional_validation import RESULT_CATEGORY, functional_evidence
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import _handler_factory


@contextmanager
def api(store, router, tmp_path, monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    monkeypatch.setenv("REVERSE_AGENT_TASK_WORKSPACE_ROOT", str(tmp_path / "worktrees"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_factory(
        store, router, allowed_origin="http://localhost:5173", binding_resolver=LocalBinding(),
        execution_authority_sha="goal-evidence-test-authority", planning_sha="goal-evidence-test-plan"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(path, body=None):
        req = Request(f"http://127.0.0.1:{server.server_port}{path}",
                      data=json.dumps(body).encode() if body is not None else None,
                      headers={"Origin": "http://localhost:5173", "Content-Type": "application/json"})
        with urlopen(req, timeout=120) as response:
            return json.load(response)
    try:
        yield request
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def publish_record(control, task_id, repository="owner/functional", **changes):
    return control.upsert_publication(task_id=task_id, repository=repository, base_branch="main",
        branch="codex/accepted", request_digest="local-publication-request", **{
            "status": "COMPLETE", "commit_sha": "a" * 40, "pr_number": 42,
            "pr_url": "https://github.com/owner/functional/pull/42", **changes})


def assert_scope(response):
    assert response["completion_scope"] == "EXECUTION_ONLY"
    assert response["remote_acceptance"] == "NOT_OBSERVED"
    assert "merged" not in response and "delivered" not in response


@pytest.mark.parametrize("mode", ["single", "sequential_team"])
@pytest.mark.parametrize("code,verified", [("value = 2\n", True), ("value = (\n", False),
                                           ("value = 3\n", False), ("value = 1\n", False)])
def test_http_goal_evidence_uses_real_implementation_tests_and_reopens(
    goal_checks, tmp_path, monkeypatch, mode, code, verified
):
    _, _, store, control, goals, goal, _ = goal_checks
    task_id, executor, router = setup_execution(goal_checks, mode, code)
    with api(store, router, tmp_path, monkeypatch) as request:
        request(f"/api/tasks/{task_id}/execute", {})
        detail = request(f"/api/goals/{goal.id}")
        for response in (detail, request("/api/goals")["goals"][0],
                         request("/api/goals?limit=1")["goals"][0]):
            assert_scope(response)
            assert response["status"] == ("COMPLETED" if verified else "BLOCKED")
            link = response["task_links"][0]
            assert link["task_id"] == task_id and link["executor_kind"] == "opencode"
            assert link["publication"] is None
            assert link["functional_validation"] == functional_evidence(store.get_task(task_id))
            assert link["functional_validation"]["verified"] is verified
            assert link["status"] == ("READY_FOR_REVIEW" if verified else "FAILED")
        if mode == "sequential_team" and code == "value = 1\n":
            assert executor.calls == ["planner", "coder"]
            assert detail["task_links"][0]["failure_classification"] == "no_coder_product_diff"
        else:
            assert executor.calls == (["executor"] if mode == "single" else ["planner", "coder", "reviewer"])
        if verified:
            proof = detail["task_links"][0]["functional_validation"]
            assert proof["checks"][0]["test_report"]["passed"] == 1
            assert proof["checks"][0]["exit_code"] == 0
            assert len(proof["head"]) == len(proof["tree"]) == 40
            assert len(proof["contract_digest"]) == len(proof["result_digest"]) == 64
        publish_record(control, task_id)
        published = request(f"/api/goals/{goal.id}")
        assert_scope(published)
        assert published["task_links"][0]["functional_validation"]["verified"] is verified
        run = request(f"/api/runs/{task_id}")
        assert published["task_links"][0]["publication"] == run["publication"]
        assert published["task_links"][0]["publication"]["status"] == "COMPLETE"
        assert "reviewed" not in published["task_links"][0]["publication"]
    reopened = TaskStore(store.db_path)
    try:
        reopened_goals = GoalService(store=reopened, control_store=PlatformControlStore(reopened))
        assert json.loads(json.dumps(reopened_goals.detail(goal.id))) == published
    finally:
        reopened._conn.close()


def test_zero_executed_tests_never_verify_a_goal(goal_checks, tmp_path):
    root, base, store, control, goals, goal, _ = goal_checks
    launch_checks(goal_checks)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    class NoTests(LocalImplementation):
        def execute_role_prepared(self, prepared, store, **kwargs):
            (prepared.worktree / "test_app.py").write_text("# no tests\n", encoding="utf-8")
            return super().execute_role_prepared(prepared, store, **kwargs)
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: NoTests(root, base, "value = 2\n"))
    assert not ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees")).success
    proof = goals.detail(goal.id)["task_links"][0]["functional_validation"]
    assert proof["verified"] is False
    assert proof["checks"][0]["test_report"]["tests"] == 0


def test_actual_fixture_validation_is_not_real_goal_acceptance(goal_checks, tmp_path):
    root, base, store, control, goals, goal, window = goal_checks
    goal = goals.amend(goal.id, expected_revision=goal.revision, objective=goal.objective,
                      executor_kind="deterministic_fixture", binding_ref="")
    launch_checks((root, base, store, control, goals, goal, window))
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    router = ExecutorRouter()
    router.replace("deterministic_fixture", lambda **kwargs: LocalImplementation(root, base, "value = 2\n"))
    assert ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees")).success
    response = goals.detail(goal.id)
    assert_scope(response)
    link = response["task_links"][0]
    assert response["status"] == "COMPLETED" and link["status"] == "READY_FOR_REVIEW_FIXTURE"
    assert link["executor_kind"] == "deterministic_fixture"
    assert link["functional_validation"]["status"] == "FIXTURE_VERIFIED"
    assert link["functional_validation"]["verified"] is False


@pytest.mark.parametrize("mutation", ["missing_result", "execution", "result_digest", "exit_code",
                                      "goal_digest", "goal_revision", "plan_task", "goal_identity",
                                      "repository", "executor"])
def test_stale_or_misbound_proof_never_verifies_the_goal(goal_checks, tmp_path, mutation):
    _, _, store, control, goals, goal, _ = goal_checks
    task_id, _, router = setup_execution(goal_checks, "single", "value = 2\n")
    assert ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees")).success
    assert goals.detail(goal.id)["task_links"][0]["functional_validation"]["verified"]
    if mutation == "missing_result":
        store._conn.execute("DELETE FROM task_evidence WHERE task_id = ? AND category = ?", (task_id, RESULT_CATEGORY))
    elif mutation in {"execution", "result_digest", "exit_code"}:
        column, value = {"execution": ("execution_id", "later-execution"),
                         "result_digest": ("validation_output_digest", "b" * 64),
                         "exit_code": ("validation_exit_code", 1)}[mutation]
        store._conn.execute(f"UPDATE tasks SET {column} = ? WHERE id = ?", (value, task_id))
    elif mutation == "goal_digest":
        store._conn.execute("UPDATE platform_goals SET artifact_digest = ? WHERE id = ?", ("b" * 64, goal.id))
    elif mutation == "goal_revision":
        store._conn.execute("UPDATE platform_goals SET revision = revision + 1 WHERE id = ?", (goal.id,))
        store._conn.execute("UPDATE platform_goal_task_links SET goal_revision = goal_revision + 1 WHERE task_id = ?", (task_id,))
    elif mutation == "plan_task":
        store._conn.execute("UPDATE platform_goal_task_links SET plan_task_id = 'other' WHERE task_id = ?", (task_id,))
    elif mutation == "goal_identity":
        other = goals.create({"objective": "Other goal", "idempotency_key": "other-goal", "repository": goal.repository})
        store._conn.execute("UPDATE platform_goal_task_links SET goal_id = ? WHERE task_id = ?", (other.id, task_id))
        store._conn.execute("UPDATE platform_goals SET artifact_digest = ? WHERE id = ?", (control.get_goal(goal.id).artifact_digest, other.id))
        goal = other
    else:
        column, value = {"repository": ("repository", "owner/other"),
                         "executor": ("executor_kind", "deterministic_fixture")}[mutation]
        store._conn.execute(f"UPDATE platform_goals SET {column} = ? WHERE id = ?", (value, goal.id))
    response = goals.detail(goal.id)
    assert_scope(response)
    assert response["task_links"][0]["functional_validation"]["verified"] is False


def test_missing_checks_and_historical_links_cannot_claim_current_completion(goal_checks):
    _, _, store, control, goals, goal, window = goal_checks
    goals.plan(goal.id, expected_revision=goal.revision)
    goals.approve(goal.id, expected_revision=goal.revision)
    goals.launch(goal.id, expected_revision=goal.revision, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    store.set_state(task_id, "READY_FOR_REVIEW")
    response = goals.detail(goal.id)
    assert_scope(response)
    assert response["status"] == "COMPLETED"
    assert response["task_links"][0]["functional_validation"] == {"status": "UNVERIFIED", "verified": False}
    store._conn.execute("UPDATE platform_goals SET revision = revision + 1, status = 'DRAFT' WHERE id = ?", (goal.id,))
    revised = goals.detail(goal.id)
    assert revised["task_links"] == [] and revised["status"] == "DRAFT"


def test_goal_projection_does_not_load_event_history_or_leak_publication_internals(goal_checks, monkeypatch):
    _, _, store, control, goals, goal, _ = goal_checks
    launch_checks(goal_checks)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    store.set_state(task_id, "READY_FOR_REVIEW")
    store.add_event(task_id, event_type="LOCAL_VALIDATED", title="history", metadata={"private_output": "raw-secret-sentinel"})
    publish_record(control, task_id, failure_classification="raw-secret-sentinel")
    observed = []
    original = store.get_task
    def bounded(task_id, *, event_limit=None):
        observed.append(event_limit)
        assert event_limit == 0
        return original(task_id, event_limit=event_limit)
    monkeypatch.setattr(store, "get_task", bounded)
    response = goals.detail(goal.id)
    assert observed == [0]
    assert "raw-secret-sentinel" not in json.dumps(response)
    assert set(response["task_links"][0]["publication"]) == {"status", "branch", "pr_number", "pr_url", "commit_sha"}
    store._conn.execute("UPDATE platform_publications SET repository = 'owner/other' WHERE task_id = ?", (task_id,))
    assert goals.detail(goal.id)["task_links"][0]["publication"] is None


@pytest.mark.parametrize("enclosing", [False, True])
def test_response_failure_rolls_back_only_its_own_reconciliation(goal_checks, monkeypatch, enclosing):
    _, _, store, control, goals, goal, _ = goal_checks
    launch_checks(goal_checks)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    store.set_state(task_id, "READY_FOR_REVIEW")
    before = control.get_goal(goal.id)
    if enclosing:
        store._conn.execute("BEGIN IMMEDIATE")
        store._conn.execute("UPDATE tasks SET title = 'outer transaction' WHERE id = ?", (task_id,))
    def unavailable(_task_id):
        raise TaskStoreError("publication_observation_unavailable")
    monkeypatch.setattr(control, "get_publication", unavailable)
    with pytest.raises(TaskStoreError, match="publication_observation_unavailable"):
        goals.detail(goal.id)
    assert control.get_goal(goal.id) == before
    assert store._conn.in_transaction is enclosing
    if enclosing:
        assert store.get_task(task_id).title == "outer transaction"
        store._conn.execute("ROLLBACK")
        assert store.get_task(task_id).title != "outer transaction"


def test_successful_response_does_not_commit_the_callers_transaction(goal_checks):
    _, _, store, control, goals, goal, _ = goal_checks
    launch_checks(goal_checks)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    store._conn.execute("BEGIN IMMEDIATE")
    try:
        store.set_state(task_id, "READY_FOR_REVIEW")
        assert goals.detail(goal.id)["status"] == "COMPLETED"
        assert store._conn.in_transaction
    finally:
        store._conn.execute("ROLLBACK")
    assert store.get_task(task_id).status == "QUEUED"
    assert control.get_goal(goal.id).status == "RUNNING"


@pytest.mark.parametrize("read", ["detail", "list", "page"])
def test_other_sqlite_connection_cannot_split_status_proof_and_publication(goal_checks, tmp_path, monkeypatch, read):
    _, _, store, control, goals, goal, _ = goal_checks
    task_id, _, router = setup_execution(goal_checks, "single", "value = 2\n")
    assert ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees")).success
    publish_record(control, task_id, status="PENDING", commit_sha="", pr_number=0, pr_url="")
    other = sqlite3.connect(store.db_path, timeout=0, isolation_level=None)
    original = control.refresh_goal_status
    attempts = []
    def refresh_then_race(goal_id):
        current = original(goal_id)
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            other.execute("BEGIN IMMEDIATE")
        attempts.append("write_blocked")
        return current
    monkeypatch.setattr(control, "refresh_goal_status", refresh_then_race)
    try:
        response = (goals.detail(goal.id) if read == "detail" else goals.list()[0]
                    if read == "list" else goals.list_page(limit=1)["goals"][0])
        assert attempts == ["write_blocked"]
        assert response["status"] == "COMPLETED"
        assert response["task_links"][0]["status"] == "READY_FOR_REVIEW"
        assert response["task_links"][0]["publication"]["status"] == "PENDING"
        assert response["task_links"][0]["functional_validation"]["verified"] is True
        other.execute("BEGIN IMMEDIATE")
        other.execute("UPDATE tasks SET status = 'FAILED', execution_id = 'new' WHERE id = ?", (task_id,))
        other.execute("UPDATE platform_publications SET status = 'COMPLETE', pr_number = 42 WHERE task_id = ?", (task_id,))
        other.execute("UPDATE platform_goals SET revision = revision + 1 WHERE id = ?", (goal.id,))
        other.execute("UPDATE platform_goal_task_links SET goal_revision = goal_revision + 1 WHERE task_id = ?", (task_id,))
        other.execute("COMMIT")
        monkeypatch.setattr(control, "refresh_goal_status", original)
        later = goals.detail(goal.id)
        assert later["status"] == "BLOCKED"
        assert later["task_links"][0]["status"] == "FAILED"
        assert later["task_links"][0]["functional_validation"]["verified"] is False
        assert later["task_links"][0]["publication"]["status"] == "COMPLETE"
        assert later["revision"] == response["revision"] + 1
    finally:
        other.close()
