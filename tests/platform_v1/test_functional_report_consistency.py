"""Report consistency regressions; no model, provider or GitHub calls.

Synthetic records test admission, not report authenticity. The final integration
cases use real Git/pytest/SQLite/read models and existing model/binding doubles.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import functional_validation as fv


VALID = {"format": "junit", "tests": 1, "passed": 1, "failed": 0, "skipped": 0, "accepted": True}
INVALID_REPORTS = [
    pytest.param({**VALID, "tests": 0, "passed": 0}, id="zero-tests"),
    pytest.param({**VALID, "passed": 0, "skipped": 1}, id="all-skipped"),
    pytest.param({**VALID, "tests": 2, "failed": 1}, id="failed-test"),
    pytest.param({**VALID, "tests": 9}, id="wrong-sum"),
    pytest.param({**VALID, "tests": True, "passed": True}, id="boolean-counts"),
    pytest.param({**VALID, "tests": 0, "passed": -1, "skipped": 1}, id="negative-count"),
    pytest.param({**VALID, "tests": 1.0}, id="float-count"),
    pytest.param({**VALID, "tests": "1"}, id="string-count"),
    pytest.param({**VALID, "format": "made-up"}, id="unknown-format"),
    pytest.param({**VALID, "format": []}, id="nonstring-format"),
    pytest.param({**VALID, "format": "tap"}, id="python-tap-mismatch"),
    pytest.param({**VALID, "accepted": False}, id="explicit-false"),
    pytest.param({**VALID, "accepted": 1}, id="integer-flag"),
    pytest.param({**VALID, "accepted": "true"}, id="string-flag"),
    pytest.param({k: v for k, v in VALID.items() if k != "accepted"}, id="missing-flag"),
    pytest.param({k: v for k, v in VALID.items() if k != "skipped"}, id="missing-count"),
    pytest.param({k: v for k, v in VALID.items() if k != "format"}, id="missing-format"),
    pytest.param(None, id="null-report"),
    pytest.param([], id="list-report"),
]


def _task_with_report(report, profile="python_pytest", *, fixture=False):
    """Encode matching contract/result identities, varying only report evidence."""
    contract = {"version": 1, "catalog_digest": fv.catalog_digest(), "task_id": "task-proof",
        "repository": "dddd2024/Nerelan", "base_commit": "a" * 40, "goal_id": "goal-proof",
        "goal_revision": 1, "goal_artifact_digest": "e" * 64, "plan_task_id": "T001",
        "requires_implementation": True, "checks": [{"profile_id": profile, "working_directory": "."}]}
    argv = ["python", "-m", "pytest"]
    check = {**contract["checks"][0], "argv": argv, "argv_digest": fv.digest(argv),
        "exit_code": 0, "timed_out": False, "duration_ms": 12, "output_digest": "d" * 64,
        "output_bytes": 10, "output_truncated": False, "test_report": copy.deepcopy(report)}
    status = "FIXTURE_VERIFIED" if fixture else "VERIFIED"
    result = {"version": 1, "task_id": "task-proof", "execution_id": "exec-proof",
        "contract_digest": fv.digest(contract), "repository": "dddd2024/Nerelan", "base_commit": "a" * 40,
        "head_before": "b" * 40, "head_after": "b" * 40, "tree_before": "c" * 40, "tree_after": "c" * 40,
        "checks": [check], "passed": True, "verified": not fixture, "status": status, "reason": ""}
    rows = [{"category": category, "value": fv.digest(value), "raw_json_digest": fv.digest(value),
             "status": row_status, "detail": fv.canonical(value)}
            for category, value, row_status in ((fv.CONTRACT_CATEGORY, contract, "APPROVED"),
                                                (fv.RESULT_CATEGORY, result, status))]
    return SimpleNamespace(id="task-proof", repository="dddd2024/Nerelan", execution_id="exec-proof",
        executor_kind="deterministic_fixture" if fixture else "opencode", status="READY_FOR_REVIEW",
        evidence_refs=rows, validation_command_id=fv.FUNCTIONAL_COMMAND_ID,
        validation_output_digest=fv.digest(result), validation_exit_code=0)


@pytest.mark.parametrize("report", INVALID_REPORTS)
def test_report_flag_cannot_override_invalid_counts_or_format(report):
    task = _task_with_report(report)
    before = copy.deepcopy(task.evidence_refs)
    proof = fv.functional_evidence(task)
    assert proof["verified"] is False
    assert proof["status"] != "VERIFIED"
    assert fv._report_accepted(report, profile_id="python_pytest") is False
    assert task.evidence_refs == before  # Readback does not repair or rewrite history.


@pytest.mark.parametrize("key", ["tests", "passed", "failed", "skipped"])
@pytest.mark.parametrize("value", [True, False, 0.0, "0", -1, None])
def test_each_count_requires_a_real_nonnegative_integer(key, value):
    assert fv._report_accepted({**VALID, key: value}) is False


@pytest.mark.parametrize("profile,kind", [("python_pytest", "junit"), ("npm_test", "junit"), ("npm_test", "tap")])
@pytest.mark.parametrize("skipped", [0, 2])
def test_valid_reports_preserve_existing_mixed_skip_semantics(profile, kind, skipped):
    report = {**VALID, "format": kind, "tests": 1 + skipped, "skipped": skipped}
    assert fv._report_accepted(report, profile_id=profile) is True
    assert fv.functional_evidence(_task_with_report(report, profile))["verified"] is True


@pytest.mark.parametrize("profile", ["unknown", "", [], 42])
def test_unknown_profile_cannot_admit_a_report(profile):
    assert fv._report_accepted(VALID, profile_id=profile) is False


def test_fixture_remains_fixture_only_and_invalid_fixture_is_rejected():
    valid = fv.functional_evidence(_task_with_report(VALID, fixture=True))
    assert valid["status"] == "FIXTURE_VERIFIED" and valid["verified"] is False
    bad = fv.functional_evidence(_task_with_report({**VALID, "tests": 0, "passed": 0}, fixture=True))
    assert bad["verified"] is False and bad["status"] != "FIXTURE_VERIFIED"


@pytest.mark.parametrize("mutation", ["digest", "execution", "exit_code", "contract"])
def test_new_predicate_does_not_replace_existing_identity_checks(mutation):
    task = _task_with_report(VALID)
    if mutation == "digest":
        task.validation_output_digest = "f" * 64
    elif mutation == "execution":
        task.execution_id = "another-execution"
    elif mutation == "exit_code":
        task.validation_exit_code = 1
    else:
        task.evidence_refs[0]["detail"] = "{}"
    assert fv.functional_evidence(task)["verified"] is False


def _tap(**changes):
    counts = {"tests": 1, "pass": 1, "fail": 0, "cancelled": 0, "skipped": 0}
    counts.update(changes)
    return "TAP version 13\nok 1 - actual test\n1..1\n" + "".join(f"# {k} {v}\n" for k, v in counts.items())


@pytest.mark.parametrize("key", ["tests", "pass", "fail", "cancelled", "skipped"])
@pytest.mark.parametrize("value", ["0", "1", "-1", "invalid", ""])
def test_tap_duplicate_or_malformed_summary_never_uses_last_value(key, value, tmp_path):
    tail = (f"# {key} {value}\n" + _tap()).encode()
    assert fv._test_report("tap", tmp_path / "unused.xml", tail)["accepted"] is False


@pytest.mark.parametrize("kind", ["other", "", "TAP", None])
def test_unknown_report_kind_is_not_parsed_as_tap(kind, tmp_path):
    assert fv._test_report(kind, tmp_path / "unused.xml", _tap().encode())["accepted"] is False


@pytest.mark.parametrize("changes,accepted", [
    ({}, True), ({"tests": 3, "skipped": 2}, True),
    ({"tests": 0, "pass": 0}, False), ({"pass": 0, "skipped": 1}, False),
    ({"tests": 2, "fail": 1}, False), ({"tests": 2, "cancelled": 1}, False),
    ({"tests": 99}, False), ({"pass": "invalid"}, False),
])
def test_tap_parser_agrees_with_admission(changes, accepted, tmp_path):
    report = fv._test_report("tap", tmp_path / "unused.xml", _tap(**changes).encode())
    assert report["accepted"] is accepted
    assert fv._report_accepted(report, profile_id="npm_test") is accepted


@pytest.mark.parametrize("cases,accepted", [
    ('<testcase name="pass"/>', True),
    ('<testcase name="pass"/><testcase name="skip"><skipped/></testcase>', True),
    ('', False), ('<testcase name="skip"><skipped/></testcase>', False),
    ('<testcase name="pass"/><testcase name="fail"><failure/></testcase>', False),
])
def test_junit_parser_agrees_with_admission(cases, accepted, tmp_path):
    path = tmp_path / "tests.xml"
    path.write_text(f"<testsuite>{cases}</testsuite>", encoding="utf-8")
    report = fv._test_report("junit", path, b"")
    assert report["accepted"] is accepted
    assert fv._report_accepted(report, profile_id="python_pytest") is accepted


@pytest.mark.parametrize("code,accepted", [
    ("def test_actual():\n    assert 2 + 2 == 4\n", True),
    ("def test_actual():\n    assert 2 + 2 == 5\n", False),
    ("import pytest\n@pytest.mark.skip(reason='test input exercises all-skipped rejection')\ndef test_actual():\n    pass\n", False),
])
def test_actual_fixed_pytest_process_produces_admissible_report(code, accepted, tmp_path):
    (tmp_path / "test_actual.py").write_text(code, encoding="utf-8")
    observed = fv._run_check({"profile_id": "python_pytest", "working_directory": "."}, tmp_path)
    assert observed["timed_out"] is False
    assert observed["test_report"]["tests"] == 1
    assert observed["test_report"]["accepted"] is accepted
    assert fv._report_accepted(observed["test_report"], profile_id="python_pytest") is accepted
    assert observed["output_bytes"] > 0 and len(observed["output_digest"]) == 64


@pytest.fixture
def report_goal(tmp_path, monkeypatch):
    # Reuse the existing full-package integration fixture without loading its
    # heavy service dependencies for the pure report tests above.
    from test_goal_functional_checks import goal_checks
    yield from goal_checks.__wrapped__(tmp_path, monkeypatch)


@pytest.mark.parametrize("mutation", ["zero", "failed", "wrong_format", "valid_control"])
def test_sqlite_roundtrip_and_real_task_run_projection_reject_corruption(report_goal, tmp_path, mutation):
    from test_functional_execution import setup_execution, ordinary
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.run_read_model import RunReadModel
    from reverse_agent.platform_v1.task_service import _map_task_to_frontend

    _, _, store, control, *_ = report_goal
    task_id, executor, router = setup_execution(report_goal, "single", "value = 2\n")
    outcome = ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees"))
    assert outcome.success is True, outcome
    task = store.get_task(task_id)
    assert fv.functional_evidence(task)["verified"] is True
    row = next(row for row in task.evidence_refs if row["category"] == fv.RESULT_CATEGORY)
    result = json.loads(row["detail"])
    report = result["checks"][0]["test_report"]
    if mutation == "zero":
        report.update(tests=0, passed=0, failed=0, skipped=0)
    elif mutation == "failed":
        report.update(tests=2, passed=1, failed=1, skipped=0)
    elif mutation == "wrong_format":
        report["format"] = "tap"
    assert report["accepted"] is True
    identity = fv.digest(result)
    # Deliberate test-only persistence fault injection. Recompute ordinary
    # hashes so this exercises report consistency, not an existing hash check.
    # This is NOT evidence that untrusted actors can write the production DB.
    changed = store._conn.execute(
        "UPDATE task_evidence SET detail = ?, value = ?, raw_json_digest = ? "
        "WHERE task_id = ? AND category = ? AND value = ?",
        (fv.canonical(result), identity, identity, task_id, fv.RESULT_CATEGORY, row["value"]))
    assert changed.rowcount == 1
    changed = store._conn.execute("UPDATE tasks SET validation_output_digest = ? WHERE id = ?", (identity, task_id))
    assert changed.rowcount == 1
    store._conn.commit()
    reopened = TaskStore(store.db_path)
    try:
        actual = reopened.get_task(task_id)
        expected = mutation == "valid_control"
        assert actual.validation_exit_code == 0
        assert fv.functional_evidence(actual)["verified"] is expected
        front = _map_task_to_frontend(actual)
        assert (front["testStatus"] == "PASS") is expected
        proof = RunReadModel(store=reopened, control_store=control).run_detail(task_id)["validation"]["functional"]
        assert proof["verified"] is expected
        assert executor.calls == ["executor"]  # Readback did not rerun the task.
    finally:
        reopened._conn.close()
