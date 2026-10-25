"""Real repository/test-process proof for the fixed functional oracle."""
from pathlib import Path
import os
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import functional_validation as fv
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], encoding="utf-8").strip()


@pytest.fixture
def implementation(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Functional fixture")
    git(root, "remote", "add", "origin", "https://github.com/owner/sample.git")
    (root / "app.py").write_text("value = 1\n", encoding="utf-8")
    (root / "test_app.py").write_text("from app import value\ndef test_requested_behavior():\n    assert value == 2\n", encoding="utf-8")
    (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    git(root, "add", "--", "app.py", "test_app.py", ".gitignore")
    git(root, "commit", "-q", "-m", "frozen acceptance fixture")
    base = git(root, "rev-parse", "HEAD")
    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    task = store.create_task(title="Implement value two", repository="owner/sample", executor_kind="opencode")
    goal = SimpleNamespace(id="goal-functional", revision=2, artifact_digest="a" * 64)
    plan = SimpleNamespace(id="T001", capability="execute_task", validation_checks=(
        {"profile_id": "python_pytest", "working_directory": "."},))
    fv.freeze_contract(store, task, goal=goal, plan_task=plan, base_commit=base)
    yield root, base, store, task.id
    store._conn.close()


def validate(fixture):
    root, base, store, task_id = fixture
    return fv.validate_functional(store.get_task(task_id), worktree=root, base_commit=base, execution_id="run-exact")


def test_actual_pytest_accepts_the_changed_artifact_and_preserves_real_index(implementation):
    root, base, store, task_id = implementation
    index = root / ".git/index"
    index_before = index.read_bytes()
    (root / "app.py").write_text("value = 2\n", encoding="utf-8")
    result = validate(implementation)
    assert result["passed"] is True and result["verified"] is True, result
    assert result["head_before"] == result["head_after"] == base
    assert result["tree_before"] == result["tree_after"] != git(root, "rev-parse", "HEAD^{tree}")
    assert result["checks"][0]["exit_code"] == 0
    assert len(result["checks"][0]["output_digest"]) == 64
    assert "stdout" not in result["checks"][0]
    assert index.read_bytes() == index_before
    reopened = TaskStore(store.db_path)
    try:
        assert fv.load_contract(reopened.get_task(task_id)) == fv.load_contract(store.get_task(task_id))
    finally:
        reopened._conn.close()


@pytest.mark.parametrize("code", ["value = (\n", "value = 3\n"])
def test_syntax_error_and_failed_assertion_do_not_verify(implementation, code):
    root, *_ = implementation
    (root / "app.py").write_text(code, encoding="utf-8")
    result = validate(implementation)
    assert result["passed"] is False and result["verified"] is False
    assert result["reason"] == "functional_check_failed"
    assert result["checks"][0]["exit_code"] != 0


def test_failed_checks_leave_feedback_for_the_next_attempt(implementation):
    root, base, store, task_id = implementation
    (root / "app.py").write_text("value = 3\n", encoding="utf-8")
    command, code, reason, _ = fv.run_task_validation(store, task_id, worktree=root, base_commit=base,
                                                      execution_id="run-exact")
    assert (command, code, reason) == (fv.FUNCTIONAL_COMMAND_ID, 1, "functional_check_failed")
    [event] = [item for item in store.get_task(task_id).events if item["title"] == "Functional check failed"]
    assert "FAILED test_app::test_requested_behavior: assert 3 == 2" in event["description"]
    assert "0 passed, 1 failed" in event["description"]

    (root / "app.py").write_text("value = (\n", encoding="utf-8")  # collection error: no test named
    report = fv.validate_functional(store.get_task(task_id), worktree=root, base_commit=base,
                                    execution_id="run-exact")["checks"][0]["test_report"]
    assert "failures" in report or "SyntaxError" in report["output_tail"]


def test_unchanged_baseline_cannot_claim_implementation(implementation):
    result = validate(implementation)
    assert result["reason"] == "functional_implementation_missing"
    assert result["checks"] == [] and result["verified"] is False


def test_mutation_during_tests_invalidates_the_proof(implementation):
    root, *_ = implementation
    (root / "app.py").write_text("value = 2\n", encoding="utf-8")
    (root / "test_app.py").write_text(
        "from pathlib import Path\ndef test_mutating():\n    Path('app.py').write_text('value = 99\\n')\n", encoding="utf-8")
    result = validate(implementation)
    assert result["checks"][0]["exit_code"] == 0
    assert result["reason"] == "functional_artifact_changed_during_checks"
    assert result["tree_before"] != result["tree_after"] and result["verified"] is False


@pytest.mark.parametrize("checks", [
    [{"profile_id": "shell"}], [{"profile_id": "python_pytest", "argv": ["whoami"]}],
    [{"profile_id": "python_pytest", "working_directory": "../elsewhere"}],
    [{"profile_id": "python_pytest", "working_directory": "/absolute"}],
    [{"profile_id": "python_pytest", "working_directory": "C:/absolute"}],
    [{"profile_id": "python_pytest", "working_directory": "a\\b"}],
    [{"profile_id": "python_pytest", "working_directory": "a//b"}],
    [{"profile_id": "python_pytest"}, {"profile_id": "python_pytest"}],
    [{"profile_id": "npm_test", "targets": ["x.test.js"]}],
    [{"profile_id": "python_pytest", "targets": []}],
    [{"profile_id": "python_pytest", "targets": "test_app.py"}],
    [{"profile_id": "python_pytest", "targets": ["-k", "x"]}],
    [{"profile_id": "python_pytest", "targets": ["@opts"]}],
    [{"profile_id": "python_pytest", "targets": [["test_app.py"]]}],
    [{"profile_id": "python_pytest", "targets": [{"path": "test_app.py"}]}],
    [{"profile_id": "python_pytest", "working_directory": "@opts"}],
    [{"profile_id": "python_pytest", "targets": ["../test_app.py"]}],
    [{"profile_id": "python_pytest", "targets": ["."]}],
    [{"profile_id": "python_pytest", "targets": ["a.py", "a.py"]}],
    [{"profile_id": "python_pytest", "targets": [f"t{i}.py" for i in range(17)]}],
])
def test_unapproved_command_fields_and_paths_are_rejected(checks):
    with pytest.raises(TaskStoreError):
        fv.normalize_checks(checks)


def test_wrong_base_and_tampered_contract_fail_closed(implementation):
    root, base, store, task_id = implementation
    result = fv.validate_functional(store.get_task(task_id), worktree=root, base_commit="b" * 40, execution_id="run")
    assert result["reason"] == "functional_base_mismatch" and result["checks"] == []
    store._conn.execute("UPDATE task_evidence SET detail = '{}' WHERE task_id = ?", (task_id,))
    with pytest.raises(TaskStoreError, match="functional_contract_invalid_or_stale"):
        validate(implementation)


def test_fixture_never_becomes_real_functional_delivery(implementation):
    root, _, store, task_id = implementation
    (root / "app.py").write_text("value = 2\n", encoding="utf-8")
    store._conn.execute("UPDATE tasks SET executor_kind = 'deterministic_fixture' WHERE id = ?", (task_id,))
    result = validate(implementation)
    assert result["passed"] is True and result["status"] == "FIXTURE_VERIFIED"
    assert result["verified"] is False


def test_real_npm_profile_uses_installed_cli_without_installing(tmp_path):
    root = tmp_path / "npm-project"
    root.mkdir()
    (root / "package.json").write_text('{"name":"functional-fixture","scripts":{"test":"node --test"}}', encoding="utf-8")
    (root / "app.test.cjs").write_text(
        "require('node:test')('actual assertion', () => require('node:assert/strict').equal(2 + 2, 4));\n", encoding="utf-8")
    result = fv._run_check({"profile_id": "npm_test", "working_directory": "."}, root)
    assert result["exit_code"] == 0 and result["timed_out"] is False, result
    assert not (root / "node_modules").exists()
    assert not (root / "package-lock.json").exists()


def test_sensitive_parent_environment_is_not_inherited(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "isolated-test-sentinel")
    monkeypatch.setenv("GITHUB_TOKEN", "isolated-test-sentinel")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--skip-everything")
    env = fv._environment(tmp_path)
    assert not {"OPENAI_API_KEY", "GITHUB_TOKEN", "PYTEST_ADDOPTS"} & env.keys()
    assert env["CI"] == "true" and env["NPM_CONFIG_OFFLINE"] == "true"


@pytest.mark.parametrize("test_code", ["# no tests\n", "import pytest\n@pytest.mark.skip(reason='fixture')\ndef test_skipped(): pass\n"])
def test_no_executed_tests_cannot_verify(implementation, test_code):
    root, *_ = implementation
    (root / "app.py").write_text("value = 2\n", encoding="utf-8")
    (root / "test_app.py").write_text(test_code, encoding="utf-8")
    result = validate(implementation)
    assert result["verified"] is False and result["reason"] == "functional_check_failed"
    assert result["checks"][0]["test_report"]["passed"] == 0


def test_npm_echo_success_is_not_a_test_run(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts":{"test":"echo success"}}', encoding="utf-8")
    with pytest.raises(TaskStoreError, match="functional_npm_test_runner_unsupported"):
        fv._run_check({"profile_id": "npm_test", "working_directory": "."}, tmp_path)


def test_npm_pretest_cannot_install_dependencies(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"scripts":{"test":"node --test","pretest":"npm install"}}', encoding="utf-8")
    with pytest.raises(TaskStoreError, match="functional_npm_lifecycle_hooks_unsupported"):
        fv._run_check({"profile_id": "npm_test", "working_directory": "."}, tmp_path)


def test_process_output_is_drained_and_bounded(tmp_path):
    result = fv._run_process({"profile_id": "python_pytest", "working_directory": "."},
        [sys.executable, "-c", "print('x' * 100000)"], tmp_path, fv._environment(tmp_path))
    assert result["exit_code"] == 0 and result["output_bytes"] >= 100000
    assert result["output_truncated"] is True and len(result["_output_tail"]) == fv.OUTPUT_LIMIT


@pytest.mark.parametrize("parent_waits", [True, False])
def test_timeout_terminates_owned_descendants(tmp_path, monkeypatch, parent_waits):
    monkeypatch.setitem(fv._CATALOG["python_pytest"], "timeout_seconds", 2)
    marker = tmp_path / "descendant-survived.txt"
    child = "import time; from pathlib import Path; time.sleep(4); Path('descendant-survived.txt').write_text('escaped')"
    script = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); " + (
        "time.sleep(30)" if parent_waits else "sys.exit(0)")
    started = time.monotonic()
    result = fv._run_process({"profile_id": "python_pytest", "working_directory": "."},
        [sys.executable, "-c", script], tmp_path, fv._environment(tmp_path))
    assert result["timed_out"] is True and time.monotonic() - started < 8
    time.sleep(3)
    assert not marker.exists(), "an owned descendant escaped termination"


def test_working_directory_real_link_escape_is_rejected(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "escape"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], check=True, capture_output=True)
    else:
        link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(TaskStoreError, match="functional_directory_outside_worktree"):
        fv._working_directory(root.resolve(), "escape")


def test_nonexistent_directory_does_not_run_in_fallback_cwd(tmp_path):
    with pytest.raises(FileNotFoundError):
        fv._run_check({"profile_id": "python_pytest", "working_directory": "missing"}, tmp_path)


def test_catalog_change_invalidates_frozen_checks(implementation, monkeypatch):
    monkeypatch.setitem(fv._CATALOG["python_pytest"], "timeout_seconds", 1)
    with pytest.raises(TaskStoreError, match="functional_contract_invalid_or_stale"):
        validate(implementation)


def test_targets_limit_pytest_to_the_named_files(tmp_path):
    (tmp_path / "test_wanted.py").write_text("def test_wanted():\n    assert True\n", encoding="utf-8")
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert False\n", encoding="utf-8")
    [check] = fv.normalize_checks([{"profile_id": "python_pytest", "working_directory": ".", "targets": ["test_wanted.py"]}])
    assert check == {"profile_id": "python_pytest", "working_directory": ".", "targets": ["test_wanted.py"]}
    result = fv._run_check(check, tmp_path)
    assert result["exit_code"] == 0 and result["test_report"]["tests"] == 1, result
    assert result["argv"][-1] == "test_wanted.py"
    with pytest.raises(TaskStoreError, match="functional_target_missing"):
        fv._run_check({**check, "targets": ["test_absent.py"]}, tmp_path)


def test_checks_without_targets_keep_their_frozen_shape():
    assert fv.normalize_checks([{"profile_id": "python_pytest", "working_directory": "."}]) == (
        {"profile_id": "python_pytest", "working_directory": "."},)


def test_public_hygiene_is_bounded_rule_data_only():
    from reverse_agent.platform_v1.functional_validation import public_hygiene
    raw = {"exit_code": 1, "stdout": "PRIVATE SOURCE SENTINEL", "stderr": "PRIVATE STDERR",
           "diagnostics": [{"path": "src/a.py", "rule": "whitespace"}] * 25}
    public = public_hygiene(raw)
    assert len(public["diagnostics"]) == 20 and public["diagnostics_truncated"]
    assert "PRIVATE" not in str(public)
    assert "SENTINEL" not in str(public)
    assert "src/a.py" in str(public)
    assert "whitespace" in str(public)
    assert len(public["observation_digest"]) == 64


def test_public_hygiene_whitespace_fallback_when_exit_nonzero_no_diagnostics():
    from reverse_agent.platform_v1.functional_validation import public_hygiene
    raw = {"exit_code": 1, "stdout": "some git diff --check", "diagnostics": []}
    public = public_hygiene(raw)
    assert public["exit_code"] == 1
    assert public["diagnostics"] == [{"path": "(patch)", "rule": "whitespace"}]


def test_functional_feedback_includes_hygiene_diagnostics():
    from reverse_agent.platform_v1.functional_validation import functional_feedback
    result = {"reason": "functional_patch_hygiene_failed", "checks": [],
              "hygiene_diagnostics": [{"path": "native", "rule": "native_executable"},
                                      {"path": "a/node_modules/x.js", "rule": "package_payload"}]}
    feedback = functional_feedback(result)
    assert "Artifact rule native_executable: native" in feedback
    assert "Artifact rule package_payload: a/node_modules/x.js" in feedback
    assert feedback.count("Artifact rule") == 2


def test_functional_feedback_truncates_hygiene_diagnostics_to_twenty():
    from reverse_agent.platform_v1.functional_validation import functional_feedback
    result = {"reason": "functional_patch_hygiene_failed", "checks": [],
              "hygiene_diagnostics": [{"path": "src/a.py", "rule": "whitespace"}] * 30}
    feedback = functional_feedback(result)
    assert feedback.count("Artifact rule") == 20


def test_preexisting_junction_is_classified_patch_hygiene_not_host_observation(implementation):
    root, base, store, task_id = implementation
    index_before = (root / ".git/index").read_bytes()
    outside = root.parent / "outside-sentinel"
    outside.mkdir()
    (outside / "sentinel.txt").write_text("OUTSIDE SECRET\n", encoding="utf-8")
    (root / "app.py").write_text("value = 2\n", encoding="utf-8")
    junction = root / "link"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                       capture_output=True, check=True)
    else:
        junction.symlink_to(outside, target_is_directory=True)
    try:
        result = validate(implementation)
        assert result["passed"] is False
        assert result["reason"] == "functional_patch_hygiene_failed"
        assert result["failure_kind"] == "patch_hygiene"
        feedback = fv.functional_feedback(result)
        assert "link" in feedback
        assert any(token in feedback for token in ("reparse", "symlink", "indirection"))
        assert (root / ".git/index").read_bytes() == index_before
        assert git(root, "rev-parse", "HEAD") == base
    finally:
        if junction.exists() and junction.is_dir() and not junction.is_symlink():
            junction.rmdir()
        elif junction.is_symlink():
            junction.unlink()


@pytest.fixture
def red_phase(implementation):
    root, base, store, _task_id = implementation
    goal = SimpleNamespace(id="goal-functional", revision=2, artifact_digest="a" * 64)
    plan = SimpleNamespace(id="T002", capability="execute_task", validation_checks=(
        {"profile_id": "python_pytest", "working_directory": ".", "targets": ["test_new.py"],
         "expected_failures": ["test_new::test_new_behavior"]},))
    task = store.create_task(title="Deliver the expected failing test first",
                             repository="owner/sample", executor_kind="opencode")
    fv.freeze_contract(store, task, goal=goal, plan_task=plan, base_commit=base)
    yield root, base, store, task.id


def test_expected_failures_field_requires_pytest_targets_and_bounded_names():
    valid = {"profile_id": "python_pytest", "working_directory": ".",
             "targets": ["test_new.py"], "expected_failures": ["test_new::test_new_behavior"]}
    assert fv.normalize_checks([valid])[0]["expected_failures"] == ["test_new::test_new_behavior"]
    # The frozen shape of a plain check is unchanged by the optional field.
    assert fv.normalize_checks([{"profile_id": "python_pytest", "working_directory": "."}]) == (
        {"profile_id": "python_pytest", "working_directory": "."},)
    with pytest.raises(TaskStoreError, match="functional_expected_failures_invalid"):
        fv.normalize_checks([{**valid, "expected_failures": []}])
    with pytest.raises(TaskStoreError, match="functional_expected_failures_invalid"):
        fv.normalize_checks([{**valid, "expected_failures": ["a", "a"]}])
    with pytest.raises(TaskStoreError, match="functional_expected_failures_invalid"):
        fv.normalize_checks([{**valid, "expected_failures": ["bad\x1bname"]}])
    with pytest.raises(TaskStoreError, match="functional_expected_failures_invalid"):
        # An expected-RED contract without explicit targets cannot be judged.
        fv.normalize_checks([{"profile_id": "python_pytest", "working_directory": ".",
                              "expected_failures": ["test_new::test_new_behavior"]}])


def test_expected_red_phase_accepts_the_failing_first_deliverable(red_phase):
    root, base, store, task_id = red_phase
    (root / "test_new.py").write_text(
        "from app import value\ndef test_new_behavior():\n    assert value == 2\n", encoding="utf-8")
    result = fv.validate_functional(store.get_task(task_id), worktree=root, base_commit=base,
                                    execution_id="run-red")
    assert result["passed"] is True and result["verified"] is True, result
    assert result["expected_red_phase"] is True
    check = result["checks"][0]
    assert check["exit_code"] != 0 and check["expected_red_met"] is True
    assert check["missing_expected_failures"] == [] and check["unexpected_failures"] == []
    assert check["expected_failures"] == ["test_new::test_new_behavior"]


def test_expected_red_names_the_missing_failure_when_the_test_passes(red_phase):
    root, base, store, task_id = red_phase
    (root / "app.py").write_text("value = 2\n", encoding="utf-8")
    (root / "test_new.py").write_text(
        "from app import value\ndef test_new_behavior():\n    assert value == 2\n", encoding="utf-8")
    result = fv.validate_functional(store.get_task(task_id), worktree=root, base_commit=base,
                                    execution_id="run-red-missing")
    assert result["passed"] is False
    assert result["reason"] == "expected_red_missing:test_new::test_new_behavior"
    assert result["failure_kind"] == "expected_red"
    assert result["checks"][0]["missing_expected_failures"] == ["test_new::test_new_behavior"]


def test_expected_red_rejects_unexpected_failures(red_phase):
    root, base, store, task_id = red_phase
    (root / "test_new.py").write_text(
        "from app import value\n"
        "def test_new_behavior():\n    assert value == 2\n"
        "def test_neighbor_behavior():\n    assert value == 3\n", encoding="utf-8")
    result = fv.validate_functional(store.get_task(task_id), worktree=root, base_commit=base,
                                    execution_id="run-red-unexpected")
    assert result["passed"] is False
    assert result["reason"] == "expected_red_unexpected:test_new::test_neighbor_behavior"
    assert result["failure_kind"] == "expected_red"
    assert result["checks"][0]["unexpected_failures"] == ["test_new::test_neighbor_behavior"]


def test_expected_red_rejects_an_interrupted_run(red_phase):
    """#1354 review: KeyboardInterrupt still writes the JUnit report with the
    expected failure, but the tests after the interrupt never ran to a verdict
    — an interrupted run is not RED evidence."""
    root, base, store, task_id = red_phase
    (root / "test_new.py").write_text(
        "from app import value\n"
        "import pytest\n"
        "@pytest.mark.order(1)\n"
        "def test_new_behavior():\n"
        "    assert value == 2\n"
        "@pytest.mark.order(2)\n"
        "def test_interrupted_neighbor():\n"
        "    raise KeyboardInterrupt\n", encoding="utf-8")
    result = fv.validate_functional(store.get_task(task_id), worktree=root, base_commit=base,
                                    execution_id="run-red-interrupted")
    assert result["passed"] is False
    assert result["failure_kind"] == "expected_red"
    check = result["checks"][0]
    assert check["expected_red_met"] is False
    assert check["exit_code"] != 1  # pytest was interrupted, not merely failing
