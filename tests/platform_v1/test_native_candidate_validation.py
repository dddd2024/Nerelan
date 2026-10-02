"""Real Git/Goal/SQLite/pytest integration using explicitly synthetic source fixtures.

These small fixture suites prove routing/admission, not the actual #1038 candidate.
The native executor/router are unmodified. No provider/model/binding doubles.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.durable_execution import DurableExecutionService
from reverse_agent.platform_v1.functional_validation import (
    FUNCTIONAL_COMMAND_ID, RESULT_CATEGORY, _CATALOG, _report_accepted, _resolved_argv,
    _run_check, catalog_digest, digest, functional_evidence, load_contract,
    normalize_checks, validate_functional,
)
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_read_model import RunReadModel
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_execution import TaskExecutionService
from reverse_agent.platform_v1.task_runtime import ExecutorRouter


PROFILES = ("python_pytest_report_consistency", "python_pytest_functional_artifact")
TARGETS = {
    PROFILES[0]: ["tests/platform_v1/test_functional_report_consistency.py"],
    PROFILES[1]: ["tests/platform_v1/test_functional_execution.py", "tests/platform_v1/test_artifact_handoff.py"],
}


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(source), *args], encoding="utf-8").strip()
    git("init", "-q")
    git("config", "core.autocrlf", "false")
    git("config", "core.longpaths", "true")
    git("config", "user.name", "Synthetic candidate fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("remote", "add", "origin", "https://github.com/owner/candidate.git")
    (source / "app.py").write_bytes(b"value = 1\n")
    (source / ".gitignore").write_bytes(b"__pycache__/\n.pytest_cache/\n")
    archive = source / ("archive_" + "x" * 55) / ("round_" + "y" * 55) / ("evidence_" + "z" * 55) / "retained.txt"
    # Explicit extended path creates fixture bytes without an OS policy change.
    archive_io = Path("\\\\?\\" + str(archive.resolve())) if os.name == "nt" else archive
    archive_io.parent.mkdir(parents=True, exist_ok=True)
    archive_io.write_bytes(b"tracked historical evidence\n")
    for target in (*TARGETS[PROFILES[0]], *TARGETS[PROFILES[1]]):
        path = source / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"from app import value\ndef test_candidate():\n    assert value == 2\n")
    git("add", "--", "app.py", ".gitignore", "tests", archive.relative_to(source).as_posix())
    git("commit", "-qm", "synthetic approved base")
    base = git("rev-parse", "HEAD")
    git("checkout", "--detach", base)
    (source / "app.py").write_bytes(b"value = 2\n")
    git("add", "--", "app.py")
    git("commit", "-qm", "synthetic candidate")
    expected = git("rev-parse", "HEAD")
    git("checkout", "--detach", base)
    assert git("for-each-ref", "--contains", expected, "--format=%(refname)") == ""
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(source))
    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = AutonomyService(control_store=control, capabilities=CapabilityRegistry()).activate({
        "policy_id": "candidate-tests", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["owner/candidate"], "capabilities": ["execute_task", "validate_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 0, "confirmation": "ACTIVATE"})
    yield source, git, base, expected, store, control, goals, window
    store._conn.close()


def launch(fixture, *, checks=None, sha=None, capability="validate_task"):
    _, _, _, expected, store, control, goals, window = fixture
    goal = goals.create({"title": "Check exact synthetic candidate", "objective": "Verify the approved commit only",
        "repository": "owner/candidate", "idempotency_key": "candidate-test",
        "executor_kind": "candidate_validation", "orchestration_mode": "single"})
    planned = goals.plan(goal.id, expected_revision=goal.revision, tasks=[{
        "id": "CHECK", "title": "Check approved candidate", "instruction": "Run fixed host checks",
        "capability": capability, "expected_candidate_sha": expected if sha is None else sha,
        "validation_checks": checks or [{"profile_id": key, "working_directory": "."} for key in PROFILES],
    }]).goal
    goals.approve(goal.id, expected_revision=planned.revision)
    launched = goals.launch(goal.id, expected_revision=planned.revision, window_id=window.id)
    assert (expected if sha is None else sha) in launched.plan_markdown
    return store.get_task(control.list_goal_tasks(launched.id)[0]["task_id"])


def engine(store, kind):
    if kind == "durable":
        return DurableExecutionService(store=store, router=ExecutorRouter(),
            execution_authority_sha="native-test-authority", planning_sha="native-test-plan")
    return TaskExecutionService(store=store, router=ExecutorRouter())


@pytest.mark.parametrize("kind", ["ordinary", "durable"])
def test_real_native_goal_checks_and_sqlite_projection(candidate, tmp_path, kind):
    source, git, base, expected, store, control, *_ = candidate
    task = launch(candidate)
    service = engine(store, kind)
    method = service.execute_durable_single if kind == "durable" else service.execute
    outcome = method(task.id, workspace_root=str(tmp_path / "execution"))
    assert outcome.success, outcome
    assert outcome.validation_command_id == FUNCTIONAL_COMMAND_ID
    reopened = TaskStore(store.db_path)
    try:
        current = reopened.get_task(task.id)
        proof = functional_evidence(current)
        assert current.status == "READY_FOR_REVIEW" and current.executor_kind == "candidate_validation"
        assert proof["verified"] is True and proof["head"] == expected and proof["base_commit"] == base
        assert [item["test_report"]["tests"] for item in proof["checks"]] == [1, 2]
        assert proof["checks"][0]["test_report"]["format"] == "junit"
        assert current.changed_files == () or current.changed_files == []
        assert not any(row["category"].startswith("Accepted") for row in current.evidence_refs)
        assert [row["value"] for row in current.evidence_refs if row["category"] == "Executor"] == ["candidate_validation"]
        assert RunReadModel(store=reopened, control_store=PlatformControlStore(reopened)).run_detail(task.id)["validation"]["functional"]["verified"] is True
        if kind == "durable":
            run = reopened._get_durable_run(proof["run_id"])
            assert run.worktree_head_sha == expected and run.repository_base_sha == base and proof["lease_epoch"] == 1
            resumed = service.resume_single(task.id,
                execution_authority_sha="native-test-authority", planning_sha="native-test-plan")
            assert resumed.success, resumed
    finally:
        reopened._conn.close()
    assert git("rev-parse", "HEAD") == base and git("status", "--porcelain") == ""


@pytest.mark.parametrize("profile", PROFILES)
def test_profiles_have_exact_argv_and_real_junit(candidate, profile):
    source, git, _, expected, *_ = candidate
    git("checkout", "--detach", expected)
    check = {"profile_id": profile, "working_directory": "."}
    assert _resolved_argv(profile) == [str(Path(sys.executable).resolve()), "-m", "pytest", "-q", "-p", "no:cacheprovider", *TARGETS[profile]]
    observed = _run_check(check, source)
    assert observed["exit_code"] == 0 and observed["test_report"]["accepted"] is True
    assert observed["argv"][:-1] == _resolved_argv(profile)
    assert observed["argv"][-1].startswith("--junitxml=")
    assert observed["test_report"]["format"] == "junit" and observed["test_report"]["tests"] == len(TARGETS[profile])


@pytest.mark.parametrize("extra", ["argv", "targets", "env", "timeout_seconds"])
def test_request_cannot_expand_fixed_command(extra):
    with pytest.raises(TaskStoreError, match="functional_check_fields_invalid"):
        normalize_checks([{"profile_id": PROFILES[0], extra: ["anything"]}])


def test_fixed_profile_requires_root_and_unknown_profile_rejected():
    with pytest.raises(TaskStoreError, match="functional_fixed_profile_requires_root"):
        normalize_checks([{"profile_id": PROFILES[0], "working_directory": "tests"}])
    with pytest.raises(TaskStoreError, match="functional_profile_unapproved"):
        normalize_checks([{"profile_id": "python_arbitrary"}])


@pytest.mark.parametrize("change", ["catalog", "version", "candidate", "extra"])
def test_stale_or_malformed_frozen_contract_rejected(candidate, change):
    task = launch(candidate)
    rows = [dict(row) for row in task.evidence_refs]
    row = next(row for row in rows if row["category"] == "FunctionalContract")
    contract = json.loads(row["detail"])
    if change == "catalog": contract["catalog_digest"] = "0" * 64
    elif change == "version": contract["version"] -= 1
    elif change == "candidate": contract["expected_candidate_sha"] = ""
    else: contract["argv"] = ["arbitrary"]
    row.update(detail=json.dumps(contract), value=digest(contract), raw_json_digest=digest(contract))
    with pytest.raises(TaskStoreError, match="functional_contract_invalid_or_stale"):
        load_contract(replace(task, evidence_refs=rows))


def test_another_stable_descendant_of_same_base_is_rejected(candidate):
    source, git, base, expected, *_ = candidate
    task = launch(candidate)
    git("checkout", "--detach", expected)
    (source / "extra.txt").write_bytes(b"another stable descendant\n")
    git("add", "--", "extra.txt")
    git("commit", "-qm", "different stable candidate")
    assert git("merge-base", base, "HEAD") == base
    result = validate_functional(task, worktree=source, base_commit=base, execution_id=task.execution_id)
    assert result["reason"] == "functional_candidate_head_mismatch" and result["checks"] == []
    assert not result["verified"]


def test_dirty_candidate_tree_is_rejected_before_tests(candidate):
    source, git, base, expected, *_ = candidate
    task = launch(candidate)
    git("checkout", "--detach", expected)
    (source / "app.py").write_bytes(b"value = 3\n")
    result = validate_functional(task, worktree=source, base_commit=base, execution_id=task.execution_id)
    assert result["reason"] == "functional_candidate_tree_mismatch" and result["checks"] == []


@pytest.mark.parametrize("drift", ["head", "tree"])
def test_candidate_change_during_tests_fails_closed(candidate, monkeypatch, drift):
    source, git, base, expected, *_ = candidate
    task = launch(candidate)
    git("checkout", "--detach", expected)
    from reverse_agent.platform_v1 import functional_validation as module
    original = module._run_check
    def mutate(check, root):
        result = original(check, root)
        if drift == "head": git("commit", "--allow-empty", "-qm", "head changed during check")
        else: (source / "app.py").write_bytes(b"value = 3\n")
        return result
    monkeypatch.setattr(module, "_run_check", mutate)
    result = validate_functional(task, worktree=source, base_commit=base, execution_id=task.execution_id)
    assert result["reason"] == "functional_artifact_changed_during_checks" and not result["verified"]


@pytest.mark.parametrize("reason", ["stopped_window", "expired_window", "stale_goal", "wrong_repository"])
@pytest.mark.parametrize("kind", ["ordinary", "durable"])
def test_live_native_admission_rechecked(candidate, tmp_path, reason, kind):
    _, git, _, _, store, control, *_ = candidate
    task = launch(candidate)
    if reason == "stopped_window": control.stop_window(candidate[-1].id, reason="owner_stopped")
    elif reason == "expired_window":
        store._conn.execute("UPDATE platform_autonomous_windows SET expires_at=? WHERE id=?",
            ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), candidate[-1].id))
    elif reason == "stale_goal": store._conn.execute("UPDATE platform_goals SET revision=revision+1 WHERE id=?", (control.goal_id_for_task(task.id),))
    else: git("remote", "set-url", "origin", "https://github.com/other/candidate.git")
    service = engine(store, kind)
    method = service.execute_durable_single if kind == "durable" else service.execute
    outcome = method(task.id, workspace_root=str(tmp_path / "execution"))
    assert not outcome.success and not functional_evidence(store.get_task(task.id))["verified"]
    assert not (tmp_path / "execution").exists()


@pytest.mark.parametrize("sha", ["", "f" * 39, "F" * 40, "main", "0" * 40 + " "])
def test_candidate_requires_exact_owner_plan_sha(candidate, sha):
    with pytest.raises(TaskStoreError, match="candidate_plan_invalid"):
        launch(candidate, sha=sha)
    assert candidate[4].count_tasks() == 0


@pytest.mark.parametrize("report", [None, {},
    {"format": "junit", "tests": 0, "passed": 0, "failed": 0, "skipped": 0, "accepted": True},
    {"format": "junit", "tests": 1, "passed": 0, "failed": 0, "skipped": 1, "accepted": True},
    {"format": "junit", "tests": 1, "passed": 2, "failed": 0, "skipped": 0, "accepted": True},
    {"format": "tap", "tests": 1, "passed": 1, "failed": 0, "skipped": 0, "accepted": True}])
def test_fixed_profiles_reject_missing_contradictory_and_allskip_reports(report):
    assert not _report_accepted(report, profile_id=PROFILES[0])


def test_direct_task_cannot_invent_candidate_approval(candidate, tmp_path):
    store = candidate[4]
    task = store.create_task(title="Unapproved candidate", repository="owner/candidate",
        executor_kind="candidate_validation", orchestration_mode="single", idempotency_key="unapproved")
    outcome = engine(store, "ordinary").execute(task.id, workspace_root=str(tmp_path / "execution"))
    assert not outcome.success and outcome.failure_detail == "candidate_contract_required"
    assert not (tmp_path / "execution").exists()


def test_real_all_skipped_candidate_cannot_pass(candidate, tmp_path):
    source, git, _, expected, store, *_ = candidate
    git("checkout", "--detach", expected)
    (source / TARGETS[PROFILES[0]][0]).write_bytes(
        b"import pytest\n@pytest.mark.skip(reason='synthetic all-skipped oracle')\ndef test_skipped():\n    pass\n")
    git("add", "--", TARGETS[PROFILES[0]][0])
    git("commit", "-qm", "synthetic all-skipped candidate")
    task = launch(candidate, sha=git("rev-parse", "HEAD"), checks=[{"profile_id": PROFILES[0]}])
    outcome = engine(store, "durable").execute_durable_single(task.id, workspace_root=str(tmp_path / "execution"))
    assert not outcome.success and store.get_task(task.id).status == "FAILED"
    proof = functional_evidence(store.get_task(task.id))
    assert proof["verified"] is False and proof["checks"][0]["test_report"]["skipped"] == 1


def test_candidate_report_readback_rejects_corruption(candidate, tmp_path):
    store = candidate[4]
    task = launch(candidate, checks=[{"profile_id": PROFILES[0]}])
    outcome = engine(store, "durable").execute_durable_single(task.id, workspace_root=str(tmp_path / "execution"))
    assert outcome.success, outcome
    current = store.get_task(task.id)
    row = next(row for row in current.evidence_refs if row["category"] == RESULT_CATEGORY)
    result = json.loads(row["detail"])
    result["checks"][0]["test_report"].update(tests=0, passed=0, failed=0, skipped=0)
    identity = digest(result)
    store._conn.execute("UPDATE task_evidence SET detail=?, value=?, raw_json_digest=? WHERE task_id=? AND category=?",
        (json.dumps(result), identity, identity, task.id, RESULT_CATEGORY))
    store._conn.execute("UPDATE tasks SET validation_output_digest=? WHERE id=?", (identity, task.id))
    assert not functional_evidence(store.get_task(task.id))["verified"]


def test_frozen_checks_must_match_owner_approved_plan(candidate, tmp_path):
    store = candidate[4]
    task = launch(candidate, checks=[{"profile_id": PROFILES[0]}])
    contract = load_contract(task)
    contract["checks"] = [{"profile_id": PROFILES[1], "working_directory": "."}]
    identity = digest(contract)
    store._conn.execute("UPDATE task_evidence SET detail=?, value=?, raw_json_digest=? WHERE task_id=? AND category=?",
        (json.dumps(contract), identity, identity, task.id, "FunctionalContract"))
    outcome = engine(store, "ordinary").execute(task.id, workspace_root=str(tmp_path / "execution"))
    assert not outcome.success and outcome.failure_detail == "candidate_goal_snapshot_stale"
    assert not (tmp_path / "execution").exists()


@pytest.mark.parametrize("existing_root", [False, True])
@pytest.mark.parametrize("legacy_empty_base", [False, True])
def test_candidate_pre_planner_recovery_keeps_frozen_base(candidate, tmp_path, existing_root, legacy_empty_base):
    from reverse_agent.platform_v1.durable_execution import (
        _CrashSimulated, reset_crash_seam, set_crash_after_checkpoint,
    )
    _, _, base, expected, store, *_ = candidate
    task = launch(candidate, checks=[{"profile_id": PROFILES[0]}])
    service = engine(store, "durable")
    root = tmp_path / "execution"
    if existing_root:
        root.mkdir()
    set_crash_after_checkpoint("PRE_PLANNER")
    try:
        with pytest.raises(_CrashSimulated):
            service.execute_durable_single(task.id, workspace_root=str(root), lease_owner="first")
    finally:
        reset_crash_seam()
    run = store._conn.execute("SELECT * FROM durable_runs WHERE task_id=?", (task.id,)).fetchone()
    assert run["accepted_checkpoint"] == "PRE_PLANNER" and run["repository_base_sha"] == base
    # Simulate an admitted run persisted by the predecessor, without rewriting a
    # real runtime. Both new and historical empty-base recovery must be fenced.
    if legacy_empty_base:
        store._conn.execute("UPDATE durable_runs SET repository_base_sha='' WHERE run_id=?", (run["run_id"],))
    now = int(time.time() * 1000)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=? WHERE run_id=?", (now - 10000, run["run_id"]))
    service.reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    outcome = service.resume_single(task.id, workspace_root=str(root), lease_owner="recovered",
        execution_authority_sha="native-test-authority", planning_sha="native-test-plan")
    assert outcome.success, outcome
    proof = functional_evidence(store.get_task(task.id))
    recovered = store._get_durable_run(run["run_id"])
    assert proof["base_commit"] == recovered.repository_base_sha == base
    assert proof["head"] == recovered.worktree_head_sha == expected
    assert recovered.lease_epoch > run["lease_epoch"]


@pytest.mark.parametrize("change", ["completed_goal", "expired_window", "stopped_window"])
def test_candidate_terminal_readback_is_not_new_execution(candidate, tmp_path, monkeypatch, change):
    _, _, _, _, store, control, goals, window = candidate
    task = launch(candidate, checks=[{"profile_id": PROFILES[0]}])
    service = engine(store, "durable")
    outcome = service.execute_durable_single(task.id, workspace_root=str(tmp_path / "execution"))
    assert outcome.success, outcome
    before = functional_evidence(store.get_task(task.id))
    if change == "completed_goal":
        assert goals.detail(control.goal_id_for_task(task.id))["status"] == "COMPLETED"
    elif change == "stopped_window":
        control.stop_window(window.id, reason="owner_stopped")
    else:
        store._conn.execute("UPDATE platform_autonomous_windows SET expires_at=? WHERE id=?",
            ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), window.id))
    def forbidden_dispatch(*args, **kwargs):
        pytest.fail("accepted terminal checkpoint must not dispatch an executor")
    monkeypatch.setattr(service.router, "create_executor", forbidden_dispatch)
    result = service.resume_single(task.id,
        execution_authority_sha="native-test-authority", planning_sha="native-test-plan")
    assert result.success, result
    assert functional_evidence(store.get_task(task.id)) == before


@pytest.mark.parametrize("change", ["goal_revision", "goal_digest", "planned_candidate", "task_link", "run_base", "run_head", "report", "tree"])
def test_candidate_terminal_readback_rejects_binding_corruption(candidate, tmp_path, change):
    _, _, _, _, store, control, *_ = candidate
    task = launch(candidate, checks=[{"profile_id": PROFILES[0]}])
    service = engine(store, "durable")
    first = service.execute_durable_single(task.id, workspace_root=str(tmp_path / "execution"))
    assert first.success, first
    goal_id = control.goal_id_for_task(task.id)
    run = store._conn.execute("SELECT * FROM durable_runs WHERE task_id=?", (task.id,)).fetchone()
    if change == "goal_revision":
        store._conn.execute("UPDATE platform_goals SET revision=revision+1 WHERE id=?", (goal_id,))
    elif change == "goal_digest":
        store._conn.execute("UPDATE platform_goals SET artifact_digest=? WHERE id=?", ("0" * 64, goal_id))
    elif change == "planned_candidate":
        goal = control.get_goal(goal_id)
        planned = [dict(item) for item in goal.tasks]
        planned[0]["expected_candidate_sha"] = "0" * 40
        store._conn.execute("UPDATE platform_goals SET tasks_json=? WHERE id=?", (json.dumps(planned), goal_id))
    elif change == "task_link":
        store._conn.execute("UPDATE platform_goal_task_links SET goal_revision=goal_revision+1 WHERE task_id=?", (task.id,))
    elif change in {"run_base", "run_head"}:
        column = "repository_base_sha" if change == "run_base" else "worktree_head_sha"
        store._conn.execute(f"UPDATE durable_runs SET {column}=? WHERE run_id=?", ("0" * 40, run["run_id"]))
    elif change == "tree":
        (Path(run["worktree_path"]) / "app.py").write_bytes(b"value = 3\n")
    else:
        current = store.get_task(task.id)
        row = next(row for row in current.evidence_refs if row["category"] == RESULT_CATEGORY)
        result = json.loads(row["detail"])
        result["checks"][0]["test_report"].update(tests=0, passed=0, failed=0, skipped=0)
        identity = digest(result)
        store._conn.execute("UPDATE task_evidence SET detail=?, value=?, raw_json_digest=? WHERE task_id=? AND category=?",
            (json.dumps(result), identity, identity, task.id, RESULT_CATEGORY))
        store._conn.execute("UPDATE tasks SET validation_output_digest=? WHERE id=?", (identity, task.id))
    outcome = service.resume_single(task.id,
        execution_authority_sha="native-test-authority", planning_sha="native-test-plan")
    assert not outcome.success, outcome


@pytest.mark.parametrize("change", ["git_container", "expired_window", "run_base"])
def test_candidate_recovery_rejects_drift(candidate, tmp_path, change):
    from reverse_agent.platform_v1.durable_execution import (
        DurableResumeError, _CrashSimulated, reset_crash_seam, set_crash_after_checkpoint,
    )
    source, _, _, _, store, _, _, window = candidate
    task = launch(candidate, checks=[{"profile_id": PROFILES[0]}])
    service = engine(store, "durable")
    root = tmp_path / "execution"
    set_crash_after_checkpoint("PRE_PLANNER")
    try:
        with pytest.raises(_CrashSimulated):
            service.execute_durable_single(task.id, workspace_root=str(root), lease_owner="first")
    finally:
        reset_crash_seam()
    run = store._conn.execute("SELECT * FROM durable_runs WHERE task_id=?", (task.id,)).fetchone()
    now = int(time.time() * 1000)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=? WHERE run_id=?", (now - 10000, run["run_id"]))
    service.reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    kwargs = dict(workspace_root=str(root), lease_owner="recovered",
        execution_authority_sha="native-test-authority", planning_sha="native-test-plan")
    if change == "git_container":
        subprocess.run(["git", "-c", "core.longpaths=true", "clone", "--", str(source), str(root)], check=True, capture_output=True)
        with pytest.raises(DurableResumeError, match="repository_base_head_mismatch"):
            service.resume_single(task.id, **kwargs)
        assert not (root / task.id).exists()
    elif change == "expired_window":
        store._conn.execute("UPDATE platform_autonomous_windows SET expires_at=? WHERE id=?",
            ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), window.id))
        with pytest.raises(TaskStoreError, match="candidate_requires_active_window"):
            service.resume_single(task.id, **kwargs)
        assert not root.exists()
    else:
        store._conn.execute("UPDATE durable_runs SET repository_base_sha=? WHERE run_id=?", ("0" * 40, run["run_id"]))
        outcome = service.resume_single(task.id, **kwargs)
        assert not outcome.success and "candidate_run_base_mismatch" in outcome.failure_detail
        assert not functional_evidence(store.get_task(task.id))["verified"]
