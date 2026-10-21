from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import context_builder as cb
from reverse_agent.platform_v1 import functional_validation as fv
from reverse_agent.platform_v1 import goal_service as gs
from reverse_agent.platform_v1 import artifact_handoff as ah


CHECKS = [{"profile_id": "python_pytest", "working_directory": "tests", "targets": ["test_a.py", "test_b.py"]}]


def test_instructions_and_context_use_normalized_targets(monkeypatch):
    task = SimpleNamespace(id="T001", title="change", instruction="Implement", needs=(), validation_checks=CHECKS,
                           status="RUNNING", execution_id="run", failure_classification="", evidence_refs=[{}])
    text = gs.GoalService._execution_title(SimpleNamespace(title="goal"), task)
    assert "your tests must be in exactly these files: tests/test_a.py, tests/test_b.py" in text
    monkeypatch.setattr(fv, "load_contract", lambda task: {"checks": CHECKS})
    assert cb._task_summary(task)["validation"] == {
        "targets": ["tests/test_a.py", "tests/test_b.py"],
        "focused_checks": [{"working_directory": "tests", "command": "python -m pytest test_a.py test_b.py"}]}


@pytest.fixture
def host(tmp_path, monkeypatch):
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr(fv, "load_contract", lambda task: {"base_commit": "a" * 40, "requires_implementation": True, "checks": CHECKS})
    monkeypatch.setattr(fv, "resolve_repository_workspace", lambda *args, **kw: SimpleNamespace(repo_dir=tmp_path))
    monkeypatch.setattr(fv, "git_output", lambda *args: "a" * 40)
    monkeypatch.setattr(fv, "_snapshot_workspace", lambda *args: (None, "b" * 40, ["app.py"], {"exit_code": 0}))
    monkeypatch.setattr(ah, "check_input_snapshot", lambda *args, **kw: None)
    task = SimpleNamespace(id="task", repository="owner/repo", executor_kind="codex")
    return tmp_path, lambda: fv.validate_functional(task, worktree=tmp_path, base_commit="a" * 40, execution_id="run")


def test_all_missing_targets_report_paths(host):
    _, validate = host
    result = validate()
    assert result["reason"].splitlines() == ["functional_target_missing:tests/test_a.py", "functional_target_missing:tests/test_b.py"]
    assert result["failure_kind"] == "target_mismatch"
    assert not result["passed"]


def test_hygiene_is_not_capability_failure(host, monkeypatch):
    _, validate = host
    monkeypatch.setattr(fv, "_snapshot_workspace", lambda *args: (None, "b" * 40, ["app.py"], {"exit_code": 1}))
    result = validate()
    assert result["failure_kind"] == "patch_hygiene"
    assert result["checks"] == []


def test_timeout_retains_observed_failures(host, monkeypatch):
    root, validate = host
    for name in ("test_a.py", "test_b.py"):
        (root / "tests" / name).write_text("", encoding="utf-8")
    observed = {"profile_id": "python_pytest", "timed_out": True, "exit_code": -1,
                "test_report": {"accepted": False, "passed": 1, "failed": 1,
                                "failures": [{"test": "test_bad", "message": "assert False"}]}}
    monkeypatch.setattr(fv, "_run_check", lambda *args: observed)
    result = validate()
    assert result["reason"] == result["failure_kind"] == "check_timeout"
    assert result["checks"][0] == observed
    assert "incomplete report; not accepted" in fv.functional_feedback(result)
    assert "assert False" in fv.functional_feedback(result)
    assert not result["passed"]


def test_real_failing_tests_are_capability_failures(host):
    root, validate = host
    for name in ("test_a.py", "test_b.py"):
        (root / "tests" / name).write_text("def test_bad():\n    assert False\n", encoding="utf-8")
    result = validate()
    assert result["reason"] == "functional_check_failed"
    assert result["failure_kind"] == "capability_failure"
    assert result["checks"][0]["test_report"]["failed"] == 2
    assert not result["passed"]


def test_planner_warns_against_slow_and_whole_suite_checks():
    from reverse_agent.platform_v1 import agent_planner as planner
    prompt = planner.build_planner_prompt(objective="change", repository="owner/repo")
    assert "Do not list slow existing suites or untargeted whole-suite checks" in prompt
    assert "your tests must be in exactly these files:" in prompt


def test_timeout_cannot_accept_a_passing_partial_report(tmp_path, monkeypatch):
    check = {"profile_id": "python_pytest", "working_directory": ".", "targets": ["test_a.py"]}
    (tmp_path / "test_a.py").write_text("", encoding="utf-8")

    def process(check, argv, cwd, env):
        report = next(arg.split("=", 1)[1] for arg in argv if arg.startswith("--junitxml="))
        from pathlib import Path
        Path(report).write_text('<testsuite><testcase name="observed_pass"/></testsuite>', encoding="utf-8")
        return {"timed_out": True, "exit_code": -1, "_output_tail": b"interrupted"}

    monkeypatch.setattr(fv, "_run_process", process)
    result = fv._run_check(check, tmp_path)
    assert result["test_report"]["passed"] == 1
    assert result["test_report"]["accepted"] is False


"""Provider-free local Git coverage for bounded failed-tree recovery."""
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from test_goal_functional_checks import goal_checks
import reverse_agent.platform_v1.functional_validation as validation
import reverse_agent.platform_v1.contract_recovery as recovery
from reverse_agent.platform_v1.artifact_handoff import _load_evidence, ACCEPTED_CATEGORY
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStoreError


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def case(goal_checks):
    root, base, store, control, _, goal, window = goal_checks
    service = GoalService(store=store, control_store=control,
        roster_resolver=lambda role: ("opencode", "local-test-binding"))
    goal = service.amend(goal.id, expected_revision=goal.revision, objective=goal.objective,
                         orchestration_mode="agent_team")
    (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    # Keep pytest independent from the outer repository's root/config.
    planned = service.plan(goal.id, expected_revision=goal.revision, tasks=[{
        "id": "T001", "title": "Implement", "instruction": "Implement with exact test name",
        "agent_role": "simple", "validation_checks": [{"profile_id": "python_pytest",
        "working_directory": ".", "targets": ["test_exact.py"]}]}]).goal
    service.approve(goal.id, expected_revision=planned.revision)
    service.launch(goal.id, expected_revision=planned.revision, window_id=window.id)
    task = store.get_task(control.list_goal_tasks(goal.id)[0]["task_id"])
    return root, base, store, control, service, goal, window, task


def validate(case, task=None, root=None):
    source, base, store, *_ = case
    task = task or case[-1]
    command, code, reason, identity = validation.run_task_validation(store, task.id,
        worktree=root or source, base_commit=base, execution_id=task.execution_id)
    store._conn.execute("UPDATE tasks SET status=?, validation_command_id=?, validation_exit_code=?, "
        "validation_output_digest=?, failure_classification=? WHERE id=?",
        ("FAILED" if code else "READY_FOR_REVIEW", command, code, identity,
         "deterministic_validation_failure" if code else "", task.id))
    store._conn.commit()
    return code, reason, identity


def wrong_tree(root, hygiene=False):
    (root / "app.py").write_text("value = 2" + ("  " if hygiene else "") + "\n", encoding="utf-8")
    (root / "wrong_name.py").write_text("from app import value\ndef test_exact():\n    assert value == 2\n", encoding="utf-8")


def destination(case, tmp_path):
    root, base, *_ = case
    dest = tmp_path / "recovery"
    git(root, "worktree", "add", "--detach", str(dest), base)
    return dest


@pytest.mark.parametrize("hygiene", [False, True])
def test_exact_failed_tree_same_binding_rename_and_validation(case, tmp_path, hygiene):
    root, base, store, control, service, goal, _, task = case
    wrong_tree(root, hygiene)
    code, _, identity = validate(case)
    assert code == 1
    failed = store.get_task(task.id)
    before = len(failed.evidence_refs)
    assert validate(case)[2] == identity
    assert len(store.get_task(task.id).evidence_refs) == before
    snapshot = recovery.failed_snapshot(failed, root=root)
    assert "wrong_name.py" in snapshot["changed_paths"]
    assert _load_evidence(failed, ACCEPTED_CATEGORY, task.execution_id) is None
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == "contract_fixup"
    fixup = store.get_task(step["to_task_id"])
    assert fixup.binding_ref == task.binding_ref and fixup.executor_kind == task.executor_kind
    assert validation.load_contract(fixup)["checks"] == validation.load_contract(task)["checks"]
    assert "test_exact.py" in recovery.recovery_input(fixup)["feedback"] or hygiene
    dest = destination(case, tmp_path)
    recovery.restore_failed_tree(store, fixup.id, worktree=dest)
    assert (dest / "wrong_name.py").read_bytes() == (root / "wrong_name.py").read_bytes()
    assert (dest / "app.py").read_bytes() == (root / "app.py").read_bytes()
    assert git(dest, "rev-parse", "HEAD") == base
    (dest / "wrong_name.py").rename(dest / "test_exact.py")
    (dest / "app.py").write_text("value = 2\n", encoding="utf-8")
    # Restoration replay preserves work done by the fix-up.
    recovery.restore_failed_tree(store, fixup.id, worktree=dest)
    assert (dest / "test_exact.py").exists() and not (dest / "wrong_name.py").exists()
    assert validate(case, fixup, dest)[0] == 0
    assert validation.functional_evidence(store.get_task(fixup.id))["verified"]
    assert service.escalate_failed_tasks(goal.id) == ()
    disposition = _load_evidence(store.get_task(task.id), "AttemptDisposition", task.execution_id)
    assert disposition["disposition"] == "reused" and disposition["tokens"] is None
    assert disposition["discarded_elapsed_ms"] is None


@pytest.mark.parametrize("bound", ["retry", "window", "chain"])
def test_exhausted_bounds_do_not_loop(case, tmp_path, bound):
    root, _, store, control, service, goal, window, task = case
    wrong_tree(root)
    validate(case)
    if bound == "retry":
        store._conn.execute("UPDATE platform_autonomous_windows SET max_retries=0 WHERE id=?", (window.id,))
    elif bound == "window":
        store._conn.execute("UPDATE platform_autonomous_windows SET status='EXPIRED' WHERE id=?", (window.id,))
    store._conn.commit()
    if bound == "chain":
        [step] = service.escalate_failed_tasks(goal.id)
        fixup = store.get_task(step["to_task_id"])
        dest = destination(case, tmp_path)
        recovery.restore_failed_tree(store, fixup.id, worktree=dest)
        validate(case, fixup, dest)
    assert service.escalate_failed_tasks(goal.id) == ()
    assert service.escalate_failed_tasks(goal.id) == ()


@pytest.mark.parametrize("defect", ["missing", "identity", "stale", "ref"])
def test_snapshot_identity_rejection(case, defect):
    root, _, store, _, service, goal, _, task = case
    wrong_tree(root)
    validate(case)
    failed = store.get_task(task.id)
    snapshot = recovery.failed_snapshot(failed, root=root)
    if defect == "missing":
        failed = replace(failed, evidence_refs=tuple(r for r in failed.evidence_refs if r["category"] != recovery.FAILED))
    elif defect == "identity":
        failed = replace(failed, execution_id="exec-other")
    elif defect == "stale":
        rows = [dict(r) for r in failed.evidence_refs]
        next(r for r in rows if r["category"] == validation.RESULT_CATEGORY)["value"] = "f" * 64
        failed = replace(failed, evidence_refs=tuple(rows))
    else:
        git(root, "update-ref", snapshot["ref"], git(root, "rev-parse", "HEAD^{tree}"))
    with pytest.raises((TaskStoreError, RuntimeError)):
        recovery.failed_snapshot(failed, root=root)
    if defect == "ref":
        assert service.escalate_failed_tasks(goal.id) == ()


@pytest.mark.parametrize("outcome", ["pass", "timeout", "failure", "unsafe"])
def test_timeout_once_with_explicit_targets(case, monkeypatch, outcome):
    root, _, store, _, service, goal, _, task = case
    wrong_tree(root)
    (root / "wrong_name.py").rename(root / "test_exact.py")
    original = validation._run_check
    calls = []
    def check(spec, worktree):
        calls.append(spec)
        observed = original(spec, worktree)
        if len(calls) == 1 or outcome == "timeout":
            observed.update(timed_out=True, exit_code=-1)
            observed["test_report"].update(accepted=False)
            if outcome == "failure":
                observed["test_report"]["failed"] = 1
        return observed
    monkeypatch.setattr(validation, "_run_check", check)
    if outcome == "unsafe":
        # A directory is an explicit target but cannot safely narrow a timeout rerun.
        contract = validation.load_contract(task)
        (root / "checks").mkdir()
        (root / "checks" / "test_safe.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
        contract["checks"][0]["targets"] = ["checks"]
        detail = validation.canonical(contract)
        identity = validation.digest(contract)
        store._conn.execute("UPDATE task_evidence SET detail=?,value=?,raw_json_digest=? WHERE task_id=? AND category=?",
            (detail, identity, identity, task.id, validation.CONTRACT_CATEGORY))
        store._conn.commit()
    code, reason, _ = validate(case)
    assert len(calls) == (2 if outcome in {"pass", "timeout"} else 1)
    assert (code == 0) == (outcome == "pass")
    if code:
        assert reason == "check_timeout"
        assert service.escalate_failed_tasks(goal.id) == ()
    assert _load_evidence(store.get_task(task.id), recovery.FAILED, task.execution_id)
    before = len(calls)
    replay = validate(case)
    assert replay[:2] == (code, reason)
    assert len(calls) == before


@pytest.mark.parametrize("engine", ["ordinary", "durable"])
@pytest.mark.parametrize("hygiene", [False, True])
def test_execution_services_recover_exact_new_file(case, tmp_path, engine, hygiene):
    from test_functional_execution import LocalImplementation, ordinary, durable
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter
    root, base, store, _, service, goal, _, task = case
    class Model(LocalImplementation):
        def execute_role_prepared(self, prepared, store_view, *, role_context, event_callback=None):
            (prepared.worktree / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
            if recovery.recovery_input(store.get_task(prepared.worktree.name)):
                assert (prepared.worktree / "wrong_name.py").exists()
                assert (prepared.worktree / "app.py").read_text().strip() == "value = 2"
                (prepared.worktree / "wrong_name.py").rename(prepared.worktree / "test_exact.py")
            else:
                wrong_tree(prepared.worktree, hygiene)
            result = super().execute_role_prepared(prepared, store_view, role_context=role_context,
                                                   event_callback=event_callback)
            if hygiene and recovery.recovery_input(store.get_task(prepared.worktree.name)) is None:
                (prepared.worktree / "app.py").write_text("value = 2  \n", encoding="utf-8")
                result.success = False
                result.validation_exit_code = 2
                result.failure_classification = "patch_hygiene_failed"
            return result
    model = Model(root, base, "value = 2\n")
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: model)
    execution = durable(store, router) if engine == "durable" else ordinary(store, router)
    method = execution.execute_durable_single if engine == "durable" else execution.execute
    first = method(task.id, workspace_root=str(tmp_path / "worktrees"))
    assert not first.success
    failed = store.get_task(task.id)
    snapshot = recovery.failed_snapshot(failed, root=root)
    assert snapshot["failure_kind"] == ("patch_hygiene" if hygiene else "target_mismatch")
    [step] = service.escalate_failed_tasks(goal.id)
    second = method(step["to_task_id"], workspace_root=str(tmp_path / "worktrees"))
    assert second.success, second
    assert validation.functional_evidence(store.get_task(step["to_task_id"]))["verified"]


def test_destination_change_and_binding_change_fail_closed(case, tmp_path):
    root, _, store, _, service, goal, _, task = case
    wrong_tree(root)
    validate(case)
    [step] = service.escalate_failed_tasks(goal.id)
    fixup = store.get_task(step["to_task_id"])
    dest = destination(case, tmp_path)
    (dest / "app.py").write_text("value = 77\n", encoding="utf-8")
    with pytest.raises(TaskStoreError, match="destination_changed"):
        recovery.restore_failed_tree(store, fixup.id, worktree=dest)
    assert "77" in (dest / "app.py").read_text()
    store._conn.execute("UPDATE tasks SET binding_ref='different' WHERE id=?", (fixup.id,))
    store._conn.commit()
    with pytest.raises(TaskStoreError, match="recovery_mismatch"):
        recovery.restore_failed_tree(store, fixup.id, worktree=dest)


def test_discarded_usage_is_measured_once_and_unknown_stays_unknown(case):
    _, _, store, _, _, _, _, task = case
    store._conn.execute("UPDATE tasks SET status='FAILED' WHERE id=?", (task.id,))
    store._conn.commit()
    store.add_event(task.id, event_type="EXECUTOR_COMPLETED", title="Local observation",
        metadata={"token_usage": {"input_tokens": 20, "output_tokens": 5}, "duration_ms": 1200})
    failed = store.get_task(task.id)
    recovery.record_attempt_disposition(store, failed, reused=False, snapshot_digest="")
    recovery.record_attempt_disposition(store, store.get_task(task.id), reused=False, snapshot_digest="")
    fact = _load_evidence(store.get_task(task.id), "AttemptDisposition", task.execution_id)
    assert fact["discarded_elapsed_ms"] == 1200
    assert fact["tokens"]["input"] == 20 and fact["discarded_tokens"]["output"] == 5
    assert fact["tokens"]["cache_write"] is None
    assert len([r for r in store.get_task(task.id).evidence_refs if r["category"] == "AttemptDisposition"]) == 1


def test_unsettled_claim_prevents_fixup_reservation(case, monkeypatch):
    root, _, store, control, service, goal, _, task = case
    wrong_tree(root)
    validate(case)
    monkeypatch.setattr(control, "can_complete_host_claim", lambda **kwargs: True)
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count
    assert recovery.failed_snapshot(store.get_task(task.id), root=root)


# Capability escalation never downgrades while an eligible equal-or-higher tier exists.
from test_model_router import candidate, choose


def test_top_tier_failure_with_only_weaker_alternatives_retries_same_model():
    pool = [candidate("codex", "gpt-6.1-sol", "subscription", "codex"),
            candidate("ds", "deepseek-v4-pro"), candidate("flash", "flash-lite")]
    result = choose(pool, failed_model="gpt-6.1-sol", failed_tier=5, difficulty=4)
    assert result["binding_ref"] == "codex" and result["reason"] == "retry_only_model"
    assert "downgrade_fallback" not in result


def test_equal_and_higher_tier_alternatives_are_preferred_over_weaker():
    pool = [candidate("codex", "gpt-6.1-sol", "subscription", "codex"), candidate("opus", "opus", "paid_api"),
            candidate("ds", "deepseek-v4-pro")]
    equal = choose(pool, failed_model="gpt-6.1-sol", failed_tier=5, difficulty=4)
    assert equal["binding_ref"] == "opus" and equal["reason"] == "retry_different_model"
    stronger = choose(pool[1:] + [candidate("glm", "glm-5.3")], failed_model="glm-5.3", failed_tier=3, difficulty=3)
    assert stronger["tier"] > 3 and stronger["reason"] == "escalation_higher_tier"


def test_unavailable_stronger_models_fall_back_explicitly():
    pool = [candidate("codex", "gpt-6.1-sol", "subscription", "codex", runnable=False),
            candidate("ds", "deepseek-v4-pro"), candidate("flash", "flash-lite")]
    result = choose(pool, failed_model="gpt-6.1-sol", failed_tier=5, difficulty=4)
    assert result["binding_ref"] == "ds" and result["tier"] == 4
    assert result["downgrade_fallback"] and result["reason"] == "retry_lower_tier_fallback"


def test_recorded_failed_tier_not_current_profile_bounds_selection():
    # The failed model now looks weaker, but the recorded tier 5 still forbids a tier-4 pick.
    pool = [candidate("codex", "gpt-6.1-sol", "subscription", "codex"), candidate("ds", "deepseek-v4-pro")]
    profiles = {"codex": {"task_buckets": {"code:5": {"attempts": 3, "success_rate": 1., "timeouts": 0}}},
                "ds": {"task_buckets": {"code:4": {"attempts": 3, "success_rate": 1., "timeouts": 0}}}}
    result = choose(pool, failed_model="gpt-6.1-sol", failed_tier=5, difficulty=4, profiles=profiles)
    assert result["binding_ref"] == "codex"


def test_contract_miss_fixup_never_consults_capability_routing(case):
    root, _, store, _, service, goal, _, task = case
    wrong_tree(root)
    validate(case)
    def forbidden(*args, **kwargs):
        raise AssertionError("contract misses must not run capability selection")
    service.task_resolver = forbidden
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == "contract_fixup"
    assert store.get_task(step["to_task_id"]).binding_ref == task.binding_ref
