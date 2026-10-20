"""Provider-free review execution fixtures; real Git, SQLite and host checks."""
import json
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from test_goal_functional_checks import goal_checks, planned_check
from test_functional_execution import LocalImplementation, durable, ordinary
from test_artifact_handoff import git
from reverse_agent.platform_v1 import model_review, durable_execution, codex_executor
from reverse_agent.platform_v1.artifact_handoff import load_input_binding
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter

ACCEPT = '{"verdict":"ACCEPT","findings":[]}'
REJECT = json.dumps({"verdict": "REJECT", "findings": [
    {"path": "app.py", "line": 1, "severity": "high", "message": "Incorrect value"}]})


class Reviewer(LocalImplementation):
    def __init__(self, root, base, response=ACCEPT, mutation="", actual=None, supported=True):
        super().__init__(root, base, "")
        self.response, self.mutation, self.actual, self.supported = response, mutation, actual, supported
        self.prompt = ""

    def enforces_read_only_review(self):
        return self.supported

    def reconstruct_prepared_context(self, *, worktree_path, base_sha, execution_id):
        return SimpleNamespace(worktree=Path(worktree_path), base_sha=base_sha, execution_id=execution_id)

    def execute_review_prepared(self, prepared, store, *, task_id, prompt):
        self.calls.append("reviewer")
        self.prompt = prompt
        if self.mutation == "tracked":
            (prepared.worktree / "app.py").write_text("value = 3\n")
        elif self.mutation == "untracked":
            (prepared.worktree / "extra.txt").write_text("mutation")
        elif self.mutation == "ignored":
            (prepared.worktree / "__pycache__").mkdir()
            (prepared.worktree / "__pycache__" / "ignored.pyc").write_bytes(b"mutation")
        elif self.mutation == "index":
            git(prepared.worktree, "update-index", "--assume-unchanged", "app.py")
        elif self.mutation == "head":
            git(prepared.worktree, "update-ref", "HEAD", git(prepared.worktree, "rev-parse", "HEAD^"))
        return {"response": self.response, "actual_models": self.actual if self.actual is not None else ["local/test"],
                "request_id": "fixture-request", "execution_id": f"exec-{task_id}",
                "binding_ref": "local-test-binding", "quota_observations": [{"status": "unknown"}]}


@pytest.fixture
def review_setup(goal_checks, tmp_path, request):
    root, base, store, control, goals, goal, window = goal_checks
    mode = getattr(request, "param", "single")
    if mode != goal.orchestration_mode:
        goal = goals.amend(goal.id, expected_revision=goal.revision, objective=goal.objective, orchestration_mode=mode)
    planned = goals.plan(goal.id, expected_revision=goal.revision, tasks=[planned_check("A"),
        {**planned_check("B"), "kind": "review", "agent_role": "reviewer", "dependencies": ["A"],
         "artifact_input": {"plan_task_id": "A"}}]).goal
    goals.approve(goal.id, expected_revision=planned.revision)
    goals.launch(goal.id, expected_revision=planned.revision, window_id=window.id)
    producer, consumer = [link["task_id"] for link in control.list_goal_tasks(goal.id)]
    router = ExecutorRouter()
    implementation = LocalImplementation(root, base, "value = 2\n")
    router.replace("opencode", lambda **kwargs: implementation)
    assert ordinary(store, router).execute(producer, workspace_root=str(tmp_path / "producer")).success
    store.append_usage_observation(producer, observation_id="author-observation",
        execution_id=store.get_task(producer).execution_id, role="executor", model_id="local/author",
        provider_id="local", source_kind="assistant_message", source_id="author-turn", status="UNKNOWN")
    created = []
    options = {}
    def factory(**kwargs):
        reviewer = Reviewer(root, kwargs["base_ref"], **options)
        created.append(reviewer)
        return reviewer
    router.replace("opencode", factory)
    return store, router, producer, consumer, created, options, tmp_path / "reviews"


def run_review(setup):
    store, router, _, consumer, _, _, root = setup
    method = getattr(durable(store, router), "execute_durable_" + store.get_task(consumer).orchestration_mode)
    return method(consumer, workspace_root=str(root))


def evidence(store, task_id):
    return [row for row in store.get_task(task_id).evidence_refs if row["category"] == "ModelReview"]


def test_accept_reviews_exact_retained_diff_and_persists_identities(review_setup):
    store, router, producer, consumer, created, _, _ = review_setup
    result = run_review(review_setup)
    assert result.success, result
    assert created[0].calls == ["reviewer"]
    assert "-value = 1" in created[0].prompt and "+value = 2" in created[0].prompt
    assert "producer_functional_results" in created[0].prompt and "acceptance_criteria" in created[0].prompt
    record = json.loads(evidence(store, consumer)[0]["detail"])
    binding = load_input_binding(store.get_task(consumer))
    assert record["tree"] == binding["producer"]["tree"]
    assert record["head"] == binding["producer"]["commit"]
    assert record["base"] == binding["base_commit"]
    assert record["result"]["verdict"] == "ACCEPT" and record["actual_models"] == ["local/test"]
    assert record["request_id"] == "fixture-request" and record["response_digest"]
    assert durable(store, router).resume_single(consumer).success
    assert len(created) == 1


@pytest.mark.parametrize("options,reason", [
    ({"response": REJECT}, "model_review_rejected"),
    ({"response": "```json\n" + ACCEPT + "\n```"}, "model_review_invalid_output"),
    ({"response": '{"verdict":"ACCEPT","findings":[],"extra":true}'}, "model_review_invalid_output"),
    ({"supported": False}, "model_review_sandbox_unsupported"),
    ({"actual": ["alias/author:free"]}, "review_not_independent"),
    ({"actual": []}, "review_not_independent"),
    ({"actual": ["unexpected/model"]}, "review_not_independent"),
    *[({"mutation": mutation}, "model_review_input_mutation") for mutation in
      ("tracked", "untracked", "ignored", "index", "head")],
])
def test_fail_closed_review(review_setup, options, reason):
    store, _, _, consumer, created, selected, _ = review_setup
    selected.update(options)
    result = run_review(review_setup)
    assert not result.success and result.failure_classification == reason, result
    if reason == "model_review_rejected":
        assert json.loads(evidence(store, consumer)[0]["detail"])["result"]["findings"]
    else:
        assert not evidence(store, consumer)
    assert store.get_task(consumer).status in {"FAILED", "BLOCKED"}


@pytest.mark.parametrize("seam,expected_calls", [
    ("MODEL_REVIEW_BEFORE_PRE_PLANNER", 1), ("PRE_PLANNER", 1), ("MODEL_REVIEW_BEFORE_CALL", 1), ("MODEL_REVIEW_BEFORE_EVIDENCE", 2),
    ("MODEL_REVIEW_BEFORE_POST_PLANNER", 1),
    ("MODEL_REVIEW_AFTER_EVIDENCE", 1), ("POST_PLANNER", 1),
    ("POST_CODER", 1), ("POST_REVIEWER", 1), ("POST_VALIDATION", 1),
])
def test_restart_reuses_only_persisted_accepted_review(review_setup, monkeypatch, seam, expected_calls):
    store, router, _, consumer, created, _, _ = review_setup
    original = durable_execution._check_crash_seam
    def crash(checkpoint):
        if checkpoint == seam:
            raise durable_execution._CrashSimulated(checkpoint)
        return original(checkpoint)
    monkeypatch.setattr(durable_execution, "_check_crash_seam", crash)
    with pytest.raises(durable_execution._CrashSimulated):
        run_review(review_setup)
    monkeypatch.setattr(durable_execution, "_check_crash_seam", original)
    now = int(time.time() * 1000)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?", (now - 10000, consumer))
    durable(store, router).reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    reopened = TaskStore(store.db_path)
    try:
        resume = getattr(durable(reopened, router), "resume_" + reopened.get_task(consumer).orchestration_mode)
        result = resume(consumer, lease_owner="review-restart")
        assert result.success, result
        assert sum(len(item.calls) for item in created) == expected_calls
        assert len(evidence(reopened, consumer)) == 1
    finally:
        reopened._conn.close()


@pytest.mark.parametrize("raw", ["null", "[]", '{"verdict":"MAYBE","findings":[]}',
    '{"verdict":"REJECT","findings":[]}', '{"verdict":"ACCEPT","verdict":"ACCEPT","findings":[]}',
    '{"verdict":"REJECT","findings":[{"path":"a","line":true,"severity":"high","message":"bad"}]}'])
def test_strict_json_contract(raw):
    with pytest.raises(TaskStoreError, match="model_review_invalid_output"):
        model_review.parse_response(raw)


def test_native_review_support_requires_codex_read_only():
    native = codex_executor.CodexExecutor(model_id="gpt-5", sandbox="read-only")
    assert native.enforces_read_only_review()
    assert not codex_executor.CodexExecutor(model_id="gpt-5").enforces_read_only_review()


@pytest.mark.parametrize("review_setup", ["sequential_team"], indirect=True)
def test_sequential_mode_still_runs_only_reviewer(review_setup):
    store, router, _, consumer, created, _, _ = review_setup
    result = run_review(review_setup)
    assert result.success, result
    assert created[0].calls == ["reviewer"]
    assert durable(store, router).resume_sequential_team(consumer).success
    assert len(created) == 1


def test_task_service_routes_review_through_durable_entry(review_setup):
    from reverse_agent.platform_v1.task_execution import TaskExecutionService
    from test_functional_execution import LocalBinding
    store, router, _, consumer, created, _, root = review_setup
    service = TaskExecutionService(store=store, router=router, binding_resolver=LocalBinding(),
        execution_authority_sha="test-functional-authority", planning_sha="test-functional-plan")
    result = service.execute(consumer, workspace_root=str(root))
    assert result.success, result
    assert created[0].calls == ["reviewer"]


def test_terminal_replay_rejects_changed_input_and_missing_review(review_setup):
    store, router, _, consumer, created, _, _ = review_setup
    assert run_review(review_setup).success
    (created[0].prepared.worktree / "app.py").write_text("value = 3\n")
    assert not durable(store, router).resume_single(consumer).success
    store._conn.execute("DELETE FROM task_evidence WHERE task_id = ? AND category = 'ModelReview'", (consumer,))
    assert not durable(store, router).resume_single(consumer).success


def test_missing_author_execution_fails_before_call(review_setup):
    store, _, producer, _, created, _, _ = review_setup
    store._conn.execute("DELETE FROM task_usage_observations WHERE task_id = ?", (producer,))
    result = run_review(review_setup)
    assert not result.success and result.failure_classification == "review_not_independent"
    assert not created


def test_native_adapter_review_uses_read_only_argv_and_external_runtime(tmp_path):
    from test_codex_executor import fixture_executor
    import subprocess
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Review fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    (root / "file.txt").write_text("original\n")
    git(root, "add", "file.txt")
    git(root, "commit", "-q", "-m", "fixture")
    base = git(root, "rev-parse", "HEAD")
    events = [{"type": "thread.started", "thread_id": "review-thread"},
              {"type": "turn.started", "model": "gpt-5.4"},
              {"type": "item.completed", "item": {"type": "agent_message", "text": ACCEPT}},
              {"type": "turn.completed"}]
    script = "import sys;sys.stdin.read();print(" + repr("\n".join(json.dumps(event) for event in events)) + ")"
    executor, launched = fixture_executor(root, base, script)
    executor._sandbox = "read-only"
    executor._binding_resolution = SimpleNamespace(binding_ref="review-binding")
    factory = executor._process_factory
    observed_temp = []
    def assert_read_only(argv, **kwargs):
        assert argv[argv.index("--sandbox") + 1] == "read-only"
        runtime = Path(kwargs["env"]["TEMP"]).resolve()
        assert Path(kwargs["cwd"]).resolve() not in runtime.parents
        observed_temp.append(runtime)
        return factory(argv, **kwargs)
    executor._process_factory = assert_read_only
    prepared = executor.prepare_worktree_once("review-native", tmp_path / "worktrees")
    observed_usage = []
    store = SimpleNamespace(append_usage_observation=lambda *args, **kwargs: observed_usage.append(kwargs))
    result = executor.execute_review_prepared(prepared, store, task_id="review-native", prompt="Review this artifact")
    assert result["response"] == ACCEPT and result["actual_models"] == ["gpt-5.4"]
    assert result["request_id"] == "review-thread" and observed_usage[0]["role"] == "reviewer"
    assert git(prepared.worktree, "status", "--porcelain", "--ignored") == ""
    assert not observed_temp[0].exists() and len(launched) == 1


@pytest.mark.parametrize("past_model", ["gateway/test:free", None])
def test_repair_attempt_author_provenance_cannot_be_ignored(review_setup, monkeypatch, past_model):
    from reverse_agent.platform_v1 import control_store
    store, _, producer, _, created, _, _ = review_setup
    old = store.create_task(title="Earlier repair attempt", executor_kind="opencode")
    if past_model:
        store.append_usage_observation(old.id, observation_id="past-observation", execution_id=old.execution_id,
            role="executor", model_id=past_model, provider_id="fixture", source_kind="assistant_message",
            source_id="past-turn", status="UNKNOWN")
    original = control_store.PlatformControlStore.list_task_escalations
    def with_repair(self, goal_id):
        goal = self.get_goal(goal_id)
        return (*original(self, goal_id), {"from_task_id": old.id, "plan_task_id": "A", "goal_revision": goal.revision})
    monkeypatch.setattr(control_store.PlatformControlStore, "list_task_escalations", with_repair)
    result = run_review(review_setup)
    assert not result.success and result.failure_classification == "review_not_independent", result
    assert not created


def test_stale_owner_cannot_rebind_review_evidence(review_setup):
    store, _, _, consumer, _, _, _ = review_setup
    assert run_review(review_setup).success
    row = evidence(store, consumer)[0]
    document = json.loads(row["detail"])
    stale = SimpleNamespace(run_id=document["run_id"], owner="stale-owner", epoch=document["lease_epoch"])
    with pytest.raises(TaskStoreError, match="lease"):
        store._bind_artifact_evidence(consumer, category="ModelReview", label=store.get_task(consumer).execution_id,
                                     document=document, lease=stale)
    assert len(evidence(store, consumer)) == 1


def test_quota_admission_failure_does_not_dispatch_review(review_setup, monkeypatch):
    from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError
    store, router, _, consumer, created, _, root = review_setup
    service = durable(store, router)
    def quota(*args, **kwargs):
        raise ExecutorRuntimeError("quota_exhausted:fixture")
    monkeypatch.setattr(service.binding_resolver, "resolve", quota)
    result = service.execute_durable_single(consumer, workspace_root=str(root))
    assert not result.success and result.failure_classification == "quota_exhausted"
    assert not created


def test_host_check_mutation_cannot_promote_accepted_review(review_setup, monkeypatch):
    store, _, _, consumer, created, _, _ = review_setup
    original = durable_execution.run_task_validation
    def mutate_after_checks(*args, **kwargs):
        result = original(*args, **kwargs)
        (Path(kwargs["worktree"]) / "extra.txt").write_text("host mutation")
        return result
    monkeypatch.setattr(durable_execution, "run_task_validation", mutate_after_checks)
    result = run_review(review_setup)
    assert not result.success and "model_review_input_mutation" in result.failure_detail
    assert len(evidence(store, consumer)) == 1  # Verdict survives; host acceptance does not.
    assert store.get_task(consumer).status == "FAILED"


@pytest.mark.parametrize("review_setup", ["sequential_team"], indirect=True)
@pytest.mark.parametrize("seam", ["MODEL_REVIEW_BEFORE_PRE_PLANNER", "MODEL_REVIEW_AFTER_EVIDENCE"])
def test_sequential_review_restart(review_setup, monkeypatch, seam):
    test_restart_reuses_only_persisted_accepted_review(review_setup, monkeypatch, seam, 1)


def test_native_binding_sequential_resume_keeps_reviewer_only_path(review_setup, goal_checks, monkeypatch):
    store, router, _, consumer, created, _, root = review_setup
    # Native transport/admission is replaced only in this provider-free fixture.
    # Real Git, retained input, lease, evidence and host checks remain in use.
    store._conn.execute("UPDATE tasks SET executor_kind = 'codex', orchestration_mode = 'sequential_team' WHERE id = ?", (consumer,))
    def kwargs(task):
        binding = load_input_binding(store.get_task(task.id))
        return {"base_ref": binding["producer"]["commit"], "binding_resolution": SimpleNamespace(
            model_id="local/test", binding_ref=task.binding_ref, executor_id="codex",
            provider_id="local", connection_id="fixture", auth_method="none")}
    def factory(**options):
        reviewer = Reviewer(goal_checks[0], options["base_ref"])
        created.append(reviewer)
        return reviewer
    router.replace("codex", factory)
    service = durable(store, router)
    monkeypatch.setattr(service, "_build_executor_kwargs", kwargs)
    original = durable_execution._check_crash_seam
    def crash(checkpoint):
        if checkpoint == "MODEL_REVIEW_AFTER_EVIDENCE":
            raise durable_execution._CrashSimulated(checkpoint)
        return original(checkpoint)
    monkeypatch.setattr(durable_execution, "_check_crash_seam", crash)
    with pytest.raises(durable_execution._CrashSimulated):
        service.execute_durable_sequential_team(consumer, workspace_root=str(root))
    monkeypatch.setattr(durable_execution, "_check_crash_seam", original)
    now = int(time.time() * 1000)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?", (now - 10000, consumer))
    service.reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    restarted = durable(store, router)
    monkeypatch.setattr(restarted, "_build_executor_kwargs", kwargs)
    result = restarted.resume_sequential_team(consumer, lease_owner="native-review-restart")
    assert result.success, result
    assert len(created) == 1 and created[0].calls == ["reviewer"]
