"""Native binding, real HTTP/SQLite, durable recovery and functional fixtures.

These local CLI stand-ins prove integration, never model entitlement or review.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.binding_resolver import BindingResolver
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.codex_executor import CodexExecutor
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.durable_execution import (
    DurableExecutionService, _CrashSimulated, reset_crash_seam, set_crash_after_checkpoint,
)
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.functional_validation import functional_evidence
from reverse_agent.platform_v1.artifact_handoff import load_input_binding
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


def models(path=None):
    store = ModelProfileStore(state_path=path)
    store.upsert_connection({"connection_id": "native-login", "name": "Native CLI",
        "provider": "codex", "base_url": "https://chatgpt.com", "auth_method": "external_cli_session"})
    store.upsert_binding({"binding_id": "native-binding", "name": "Explicit native model",
        "executor_id": "codex", "connection_id": "native-login", "model_id": "gpt-5.4"})
    store.set_codex_readiness("managed_login_ready")
    return store


@pytest.fixture
def source(tmp_path, monkeypatch):
    root = tmp_path / "source"
    root.mkdir()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], encoding="utf-8").strip()
    git("init", "-q")
    git("config", "user.name", "Native fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("remote", "add", "origin", "https://github.com/owner/native-fixture.git")
    (root / "app.py").write_text("value = 1\n")
    (root / "test_app.py").write_text("from app import value\ndef test_requested():\n    assert value == 2\n")
    (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    git("add", ".")
    git("commit", "-q", "-m", "approved fixture base")
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(root))
    monkeypatch.setenv("REVERSE_AGENT_TASK_WORKSPACE_ROOT", str(tmp_path / "workspaces"))
    return root, git("rev-parse", "HEAD")


def native_factory(calls, *, value=2):
    events = [
        {"type": "thread.started", "thread_id": "native-fixture-thread"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "Fixture changed app.py; independent review pending."}},
        {"type": "turn.completed"},
    ]
    script = "import sys;from pathlib import Path;sys.stdin.read();Path('app.py').write_text(" + repr(f"value = {value}\n") + ");print(" + repr("\n".join(json.dumps(e) for e in events)) + ")"
    def factory(**kwargs):
        def launch(argv, **options):
            calls.append({"argv": argv, "cwd": options["cwd"]})
            return subprocess.Popen([sys.executable, "-u", "-c", script], **options)
        return CodexExecutor(**kwargs, codex_exe=sys.executable, process_factory=launch,
            readiness_probe=lambda _: "managed_login_ready")
    return factory


def resolver(store):
    def get(url, timeout, max_bytes):
        _, kind, identity = urlsplit(url).path.lstrip("/").split("/")
        methods = {"bindings": store.get_binding_public, "connections": store.get_connection_public,
                   "executors": store.get_executor_public}
        return 200, methods[kind](identity)
    return BindingResolver(transport=get)


def request(url, payload=None):
    req = Request(url, data=None if payload is None else json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as response:
        return response.status, json.load(response)


def test_saved_native_namespace_and_readiness_are_independent_from_opencode(tmp_path):
    path = tmp_path / "setup.json"
    store = models(path)
    store.refresh_external_session_status({})
    connection = store.get_connection_public("native-login")
    assert connection["external_session_status"] == "available"
    assert connection["upstream_provider_id"] == "openai"
    assert connection["protocol_family"] == "codex-cli"
    assert connection["executor_provider_id"] == "codex"
    resolved = resolver(store).resolve("native-binding", task_executor="codex")
    assert resolved.model_id == "gpt-5.4" and resolved.relay_required is False
    reopened = ModelProfileStore(path)
    assert reopened.get_binding_public("native-binding")["executor_id"] == "codex"
    assert reopened.get_executor_public("codex")["operational"] is False
    assert "available" not in path.read_text()
    assert reopened.get_executor_public("opencode")["operational"] is True


def test_bad_native_connection_or_model_cannot_be_saved():
    store = models()
    with pytest.raises(ValueError, match="codex_model_id_invalid"):
        store.upsert_binding({"binding_id": "bad", "name": "bad", "executor_id": "codex",
            "connection_id": "native-login", "model_id": "openai/gpt-5.4"})
    with pytest.raises(ValueError, match="codex_connection_requires_native_executor"):
        store.upsert_binding({"binding_id": "bad", "name": "bad", "executor_id": "opencode",
            "connection_id": "native-login", "model_id": "gpt-5.4"})
    with pytest.raises(ValueError, match="codex_requires_managed_session_connection"):
        store.upsert_connection({"connection_id": "bad", "name": "bad", "provider": "codex",
            "base_url": "https://chatgpt.com", "auth_method": "api_key"})
    with pytest.raises(ValueError, match="codex_credentials_owned_by_cli"):
        store.upsert_connection({"connection_id": "bad", "name": "bad", "provider": "codex",
            "base_url": "https://chatgpt.com", "auth_method": "external_cli_session", "api_key": "fixture-private-key"})


def test_real_http_native_task_freezes_base_and_preserves_executor_and_result(source, tmp_path):
    _, base = source
    calls = []
    host = CombinedTrustedHost(store=models(), task_db_path=str(tmp_path / "tasks.sqlite3"),
        model_control_port=0, task_api_port=0, vault=None,
        execution_authority_sha="fixture-authority", planning_sha="fixture-plan",
        auth_list_probe=lambda: pytest.fail("native must not probe OpenCode auth"),
        codex_readiness_probe=lambda: "managed_login_ready")
    host._router.replace("codex", native_factory(calls))
    try:
        host.start()
        _, created = request(host.task_api_url + "/api/tasks", {"title": "Change app value to two",
            "repository": "owner/native-fixture", "executor_kind": "codex", "binding_ref": "native-binding",
            "orchestration_mode": "single", "idempotency_key": "http-native-1"})
        task_id = created["id"]
        assert host.task_store.get_task(task_id).branch == base
        _, completed = request(host.task_api_url + f"/api/tasks/{task_id}/execute", {})
        task = host.task_store.get_task(task_id)
        assert task.executor_kind == "codex" and task.status == "READY_FOR_REVIEW"
        assert len(calls) == 1
        run = host.task_store._conn.execute("SELECT run_id FROM durable_runs WHERE task_id=?", (task_id,)).fetchone()
        stored = host.task_store._get_durable_run(run["run_id"])
        assert stored.repository_base_sha == base and stored.accepted_checkpoint == "POST_VALIDATION"
        assert completed["executor_kind"] == "codex"
        assert (Path(stored.worktree_path) / "app.py").read_text() == "value = 2\n"
        assert any(e["type"] == "EXECUTOR_COMPLETED" for e in task.events)
        usage = host.task_store._conn.execute("SELECT status,cost_micro_units,input_units FROM task_usage_observations WHERE task_id=?", (task_id,)).fetchall()
        assert len(usage) == 1 and usage[0]["status"] == "UNKNOWN"
        assert usage[0]["cost_micro_units"] is None and usage[0]["input_units"] is None
        try:
            request(host.task_api_url + f"/api/tasks/{task_id}/execute", {})
        except HTTPError as error:
            assert error.code == 409
        assert len(calls) == 1
    finally:
        host.stop()


@pytest.mark.parametrize("value,successful", [(2, True), (3, False)])
def test_true_goal_materialization_and_functional_checks_do_not_accept_cli_exit_alone(source, tmp_path, value, successful):
    _, base = source
    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    goal = goals.create({"objective": "Set value to two and pass requested tests", "repository": "owner/native-fixture",
        "idempotency_key": "native-goal", "executor_kind": "codex", "orchestration_mode": "single", "binding_ref": "native-binding"})
    goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[{"id": "T001", "title": "Value two",
        "instruction": "Change app.py value to two", "validation_checks": [{"profile_id": "python_pytest", "working_directory": "."}]},
        {"id": "T002", "title": "Validate exact accepted artifact", "instruction": "Validate producer output",
         "dependencies": ["T001"], "capability": "validate_task", "artifact_input": {"plan_task_id": "T001"},
         "validation_checks": [{"profile_id": "python_pytest", "working_directory": "."}]}]).goal
    goals.approve(goal.id, expected_revision=goal.revision)
    now = datetime.now(timezone.utc)
    window = AutonomyService(control_store=control, capabilities=CapabilityRegistry()).activate({
        "policy_id": "native-window", "policy_revision": 1, "owner_identity": "fixture-owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": [goal.repository], "capabilities": ["execute_task", "validate_task"],
        "max_concurrent_tasks": 1, "max_tasks": 2, "max_retries": 0, "confirmation": "ACTIVATE"})
    goals.launch(goal.id, expected_revision=goal.revision, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    assert store.get_task(task_id).branch == base
    calls = []
    router = ExecutorRouter()
    router.replace("codex", native_factory(calls, value=value))
    service = DurableExecutionService(store=store, router=router, binding_resolver=resolver(models()),
        execution_authority_sha="fixture-authority", planning_sha="fixture-plan")
    try:
        outcome = service.execute_durable_single(task_id, workspace_root=str(tmp_path / "workspaces"))
        assert outcome.success is successful
        assert len(calls) == 1
        assert store.get_task(task_id).executor_kind == "codex"
        reports = [e for e in store.get_task(task_id).evidence_refs if e.get("category") == "FunctionalValidation"]
        assert reports
        if successful:
            assert store.get_task(task_id).status == "READY_FOR_REVIEW"
            assert functional_evidence(store.get_task(task_id))["verified"] is True
            consumer_id = control.list_goal_tasks(goal.id)[1]["task_id"]
            consumed = service.execute_durable_single(consumer_id, workspace_root=str(tmp_path / "workspaces"))
            assert consumed.success and len(calls) == 1
            binding = load_input_binding(store.get_task(consumer_id))
            assert binding["producer"]["task_id"] == task_id
            assert binding["producer"]["result_digest"] == functional_evidence(store.get_task(task_id))["result_digest"]
            assert functional_evidence(store.get_task(consumer_id))["verified"] is True
        else:
            assert store.get_task(task_id).status != "READY_FOR_REVIEW"
    finally:
        store._conn.close()


def test_native_checkpoint_recovery_does_not_dispatch_a_second_cli(source, tmp_path):
    _, base = source
    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    task = store.create_task(title="Change app value to two", repository="owner/native-fixture",
        executor_kind="codex", binding_ref="native-binding", branch=base, idempotency_key="resume-native")
    calls = []
    router = ExecutorRouter()
    router.replace("codex", native_factory(calls))
    service = DurableExecutionService(store=store, router=router, binding_resolver=resolver(models()),
        execution_authority_sha="fixture-authority", planning_sha="fixture-plan")
    set_crash_after_checkpoint("POST_PLANNER")
    try:
        with pytest.raises(_CrashSimulated):
            service.execute_durable_single(task.id, workspace_root=str(tmp_path / "workspaces"))
        reset_crash_seam()
        run = store._find_active_durable_run(task.id)
        store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=? WHERE run_id=?", (int(time.time() * 1000) - 10000, run["run_id"]))
        store._conn.commit()
        service.reconcile_expired_runs(now_ms=int(time.time() * 1000), max_age_ms=1000)
        outcome = service.resume_single(task.id, lease_owner="recovery", execution_authority_sha="fixture-authority", planning_sha="fixture-plan")
        assert outcome.success and len(calls) == 1
        assert store.get_task(task.id).executor_kind == "codex"
    finally:
        reset_crash_seam()
        store._conn.close()
