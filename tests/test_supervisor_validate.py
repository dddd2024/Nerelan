from __future__ import annotations

import json
import pathlib
import sys

import pytest

# Make scripts/ importable without a package.
_SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import supervisor_validate as sv  # noqa: E402
import supervisor_publish as sp  # noqa: E402
import supervisor_context as sc  # noqa: E402

REPO = "dddd2024/reverse-agent"
MAIN_SHA = "16526801bda2a816fc707342f903c1ad037de9bd"
WRONG_REPO = "other/owner"
WRONG_SHA = "0" * 40


def _safe_task() -> dict:
    return {
        "title": "Bounded next task",
        "goal": "Add a bounded deterministic check",
        "allowed_scope": ["reverse_agent/example.py", "tests/test_example.py"],
        "forbidden_scope": ["merge", "push main"],
        "requested_operations": ["read_repository", "edit_bounded_files", "run_checks"],
        "acceptance_checks": ["python -m pytest tests/test_example.py -q"],
        "execution_prompt": "Implement the bounded check using only the standard library.",
    }


def _safe_result(status: str = "continue", task: dict | None = None) -> dict:
    return {
        "schema_version": "0.2",
        "repository": REPO,
        "audited_main_sha": MAIN_SHA,
        "status": status,
        "findings": [
            {"claim": "Bounded finding", "evidence": ["issue #92", "main sha 16526801"]}
        ],
        "next_task": task if task is not None else _safe_task(),
    }


# --- happy paths -----------------------------------------------------------


def test_safe_continue_passes() -> None:
    ok, errors, parsed = sv.validate_audit_result(_safe_result("continue"), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors and parsed is not None
    assert parsed["status"] == "continue"
    assert parsed["schema_version"] == "0.2"
    assert parsed["repository"] == REPO
    assert parsed["audited_main_sha"] == MAIN_SHA


def test_safe_revise_passes() -> None:
    ok, errors, parsed = sv.validate_audit_result(_safe_result("revise"), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and parsed is not None


def test_safe_stop_passes() -> None:
    ok, errors, _ = sv.validate_audit_result(_safe_result("stop"), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok


def test_next_task_null_passes() -> None:
    payload = _safe_result("stop")
    payload["next_task"] = None
    ok, errors, parsed = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and parsed is not None and parsed["next_task"] is None


# --- schema_version / repository / main SHA fail-closed --------------------


def test_schema_version_mismatch_rejected() -> None:
    payload = _safe_result()
    payload["schema_version"] = "0.1"
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.SCHEMA_VERSION_MISMATCH) for e in errors)


def test_repository_mismatch_rejected() -> None:
    payload = _safe_result()
    payload["repository"] = WRONG_REPO
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.REPOSITORY_MISMATCH) for e in errors)


def test_main_sha_mismatch_rejected() -> None:
    payload = _safe_result()
    payload["audited_main_sha"] = WRONG_SHA
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.MAIN_SHA_MISMATCH) for e in errors)


def test_main_sha_short_rejected() -> None:
    payload = _safe_result()
    payload["audited_main_sha"] = "16526801"
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.INVALID_MAIN_SHA_FORMAT) for e in errors)


def test_main_sha_missing_rejected() -> None:
    payload = _safe_result()
    del payload["audited_main_sha"]
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.INVALID_MAIN_SHA_FORMAT) for e in errors)


# --- unknown fields rejected -----------------------------------------------


def test_unknown_top_level_field_rejected() -> None:
    payload = _safe_result()
    payload["extra_field"] = "bad"
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.UNKNOWN_FIELD) for e in errors)


def test_unknown_next_task_field_rejected() -> None:
    payload = _safe_result()
    payload["next_task"]["extra"] = "bad"
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.UNKNOWN_FIELD) for e in errors)


def test_unknown_finding_field_rejected() -> None:
    payload = _safe_result()
    payload["findings"][0]["extra"] = "bad"
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.UNKNOWN_FIELD) for e in errors)


# --- findings rejections ---------------------------------------------------


def test_invalid_json_rejected() -> None:
    ok, errors, _ = sv.validate_audit_result("not a dict", expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.INVALID_JSON in errors


def test_finding_missing_evidence_rejected() -> None:
    payload = _safe_result()
    payload["findings"][0]["evidence"] = []
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.FINDING_NO_EVIDENCE) for e in errors)


def test_finding_evidence_not_list_rejected() -> None:
    payload = _safe_result()
    payload["findings"][0]["evidence"] = "issue #92"
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok


def test_findings_missing_rejected() -> None:
    payload = _safe_result()
    payload["findings"] = []
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.FINDINGS_MISSING in errors


def test_invalid_status_rejected() -> None:
    payload = _safe_result("proceed")
    ok, errors, _ = sv.validate_audit_result(payload, expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.INVALID_STATUS) for e in errors)


# --- next_task rejections --------------------------------------------------


def test_acceptance_checks_empty_rejected() -> None:
    task = _safe_task()
    task["acceptance_checks"] = []
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED in errors


def test_allowed_scope_empty_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = []
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.NEXT_TASK_ALLOWED_SCOPE_EMPTY in errors


@pytest.mark.parametrize("scope", ["*", "**", "**/*", ".", "./", "./**", "all", "entire repository", "whole repo"])
def test_broad_scope_rejected(scope: str) -> None:
    task = _safe_task()
    task["allowed_scope"] = [scope]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.NEXT_TASK_SCOPE_TOO_BROAD) for e in errors)


# --- requested_operations whitelist (authoritative) ------------------------


def test_requested_operations_required() -> None:
    task = _safe_task()
    del task["requested_operations"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.NEXT_TASK_OPERATIONS_REQUIRED in errors


def test_requested_operations_empty_rejected() -> None:
    task = _safe_task()
    task["requested_operations"] = []
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.NEXT_TASK_OPERATIONS_REQUIRED in errors


@pytest.mark.parametrize("op", ["push_main", "merge", "mark_ready", "auto_merge", "release", "deploy", "credential_access", "close_issue", "delete_branch", "rewrite_history", "unknown_operation"])
def test_forbidden_operation_rejected(op: str) -> None:
    task = _safe_task()
    task["requested_operations"] = [op]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.NEXT_TASK_OPERATION_UNKNOWN) for e in errors)


def test_allowed_operations_pass() -> None:
    task = _safe_task()
    task["requested_operations"] = ["read_repository", "edit_bounded_files", "run_checks", "push_named_branch", "create_or_update_draft_pr"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors


# --- acceptance_checks dangerous command scan ------------------------------


def test_acceptance_check_push_main_rejected() -> None:
    task = _safe_task()
    task["acceptance_checks"] = ["git push origin main"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_DANGEROUS_ACCEPTANCE_CHECK in e for e in errors)


def test_acceptance_check_deploy_rejected() -> None:
    task = _safe_task()
    task["acceptance_checks"] = ["deploy to production"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_DANGEROUS_ACCEPTANCE_CHECK in e for e in errors)


def test_acceptance_check_merge_rejected() -> None:
    task = _safe_task()
    task["acceptance_checks"] = ["gh pr merge 93"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_DANGEROUS_ACCEPTANCE_CHECK in e for e in errors)


def test_acceptance_check_force_push_rejected() -> None:
    task = _safe_task()
    task["acceptance_checks"] = ["git push --force origin main"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_DANGEROUS_ACCEPTANCE_CHECK in e for e in errors)


def test_acceptance_check_safe_passes() -> None:
    task = _safe_task()
    task["acceptance_checks"] = ["python -m pytest tests/test_example.py -q", "git diff --check"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors


# --- forbidden_scope element validation ------------------------------------


def test_forbidden_scope_non_string_rejected() -> None:
    task = _safe_task()
    task["forbidden_scope"] = ["merge", 123]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert "NEXT_TASK_FORBIDDEN_SCOPE_INVALID" in errors


def test_forbidden_scope_too_long_rejected() -> None:
    task = _safe_task()
    task["forbidden_scope"] = ["x" * 600]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(e.startswith(sv.FIELD_TOO_LONG) for e in errors)


# --- natural-language policy scan (secondary) ------------------------------


def test_merge_in_allowed_scope_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = ["merge pull request"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_MERGE_FORBIDDEN in errors


def test_push_main_in_allowed_scope_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = ["push to main"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_MAIN_PUSH_FORBIDDEN in errors


def test_release_in_execution_prompt_rejected() -> None:
    task = _safe_task()
    task["execution_prompt"] = "Create a release for the project"
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_RELEASE_FORBIDDEN in errors


def test_deploy_in_goal_rejected() -> None:
    task = _safe_task()
    task["goal"] = "Run deployment to production"
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_DEPLOYMENT_FORBIDDEN in errors


def test_credential_access_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = ["read credentials from secrets"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_CREDENTIAL_ACCESS_FORBIDDEN in errors


def test_negation_not_flagged() -> None:
    task = _safe_task()
    task["execution_prompt"] = "Do not merge anything. Never push to main."
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors


# --- idempotency / marker stability ---------------------------------------


def test_equivalent_inputs_produce_same_marker() -> None:
    task = _safe_task()
    k1 = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        allowed_scope=task["allowed_scope"], forbidden_scope=task["forbidden_scope"],
        requested_operations=task["requested_operations"], acceptance_checks=task["acceptance_checks"],
    )
    # Same inputs, different order, extra whitespace.
    k2 = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION,
        goal="  Add a bounded   deterministic check  ",
        allowed_scope=list(reversed(task["allowed_scope"])),
        forbidden_scope=list(reversed(task["forbidden_scope"])),
        requested_operations=list(reversed(task["requested_operations"])),
        acceptance_checks=list(reversed(task["acceptance_checks"])),
    )
    assert k1 == k2
    assert len(k1) == 64


def test_scope_change_changes_marker() -> None:
    task = _safe_task()
    base = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        allowed_scope=task["allowed_scope"], forbidden_scope=task["forbidden_scope"],
        requested_operations=task["requested_operations"], acceptance_checks=task["acceptance_checks"],
    )
    different_scope = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        allowed_scope=["different/file.py"], forbidden_scope=task["forbidden_scope"],
        requested_operations=task["requested_operations"], acceptance_checks=task["acceptance_checks"],
    )
    assert base != different_scope


def test_operations_change_changes_marker() -> None:
    task = _safe_task()
    base = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        allowed_scope=task["allowed_scope"], forbidden_scope=task["forbidden_scope"],
        requested_operations=task["requested_operations"], acceptance_checks=task["acceptance_checks"],
    )
    different_ops = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        allowed_scope=task["allowed_scope"], forbidden_scope=task["forbidden_scope"],
        requested_operations=["read_repository"], acceptance_checks=task["acceptance_checks"],
    )
    assert base != different_ops


def test_material_change_changes_marker() -> None:
    task = _safe_task()
    base = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        allowed_scope=task["allowed_scope"], forbidden_scope=task["forbidden_scope"],
        requested_operations=task["requested_operations"], acceptance_checks=task["acceptance_checks"],
    )
    different_goal = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal="A different bounded goal",
        allowed_scope=task["allowed_scope"], forbidden_scope=task["forbidden_scope"],
        requested_operations=task["requested_operations"], acceptance_checks=task["acceptance_checks"],
    )
    different_sha = sv.compute_cycle_key(
        repository=REPO, main_sha="0" * 40, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        allowed_scope=task["allowed_scope"], forbidden_scope=task["forbidden_scope"],
        requested_operations=task["requested_operations"], acceptance_checks=task["acceptance_checks"],
    )
    different_checks = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        allowed_scope=task["allowed_scope"], forbidden_scope=task["forbidden_scope"],
        requested_operations=task["requested_operations"], acceptance_checks=["a different check"],
    )
    assert base != different_goal
    assert base != different_sha
    assert base != different_checks


def test_marker_round_trip() -> None:
    key = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal="g",
        allowed_scope=["a"], forbidden_scope=["b"],
        requested_operations=["read_repository"], acceptance_checks=["c"],
    )
    marker = sv.make_marker(key)
    assert sv.find_marker_key(marker) == key
    assert sv.find_marker_key("no marker here") is None


# --- publication planner (fail-closed) -------------------------------------


def test_no_marker_creates_issue() -> None:
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    assert plan["action"] == sp.ACTION_CREATE_ISSUE
    assert plan["schema_valid"] is True
    assert plan["policy_allowed"] is True
    assert plan["marker"] is not None
    assert plan["target_issue"] is None


def test_matching_marker_unchanged_is_no_op() -> None:
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    existing = [{"number": 42, "title": first["title"], "body": first["body"], "state": "OPEN"}]
    second = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert second["action"] == sp.ACTION_NO_OP
    assert second["target_issue"] == 42
    assert second["idempotency_key"] == first["idempotency_key"]


def test_matching_marker_changed_is_update() -> None:
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    # Same marker (same key) but body altered by a human note.
    existing = [{"number": 7, "title": "Old title", "body": first["body"] + "\nextra human note", "state": "OPEN"}]
    second = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert second["action"] == sp.ACTION_UPDATE_ISSUE
    assert second["target_issue"] == 7


def test_closed_marker_no_duplicate_create() -> None:
    """A closed Issue with the same marker must NOT trigger a create."""
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    existing = [{"number": 99, "title": first["title"], "body": first["body"], "state": "CLOSED"}]
    second = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert second["action"] == sp.ACTION_NO_OP
    assert second["target_issue"] == 99


def test_duplicate_marker_fail_closed() -> None:
    """Marker in two Issues → fail-closed, zero writes."""
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    existing = [
        {"number": 1, "title": "first", "body": first["body"], "state": "OPEN"},
        {"number": 2, "title": "second", "body": first["body"], "state": "CLOSED"},
    ]
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert plan["action"] == sp.ACTION_NO_OP
    assert plan["policy_allowed"] is False
    assert any(sp.ERR_DUPLICATE_MARKER in e for e in plan["errors"])


def test_invalid_result_yields_no_op_plan_with_errors() -> None:
    bad = _safe_result()
    bad["findings"][0]["evidence"] = []
    plan = sp.plan_publication(
        audit_result=bad, repository=REPO, main_sha=MAIN_SHA, existing_issues=[],
    )
    assert plan["schema_valid"] is False
    assert plan["policy_allowed"] is False
    assert plan["action"] == sp.ACTION_NO_OP
    assert plan["marker"] is None


def test_next_task_null_yields_no_op() -> None:
    payload = _safe_result("stop")
    payload["next_task"] = None
    plan = sp.plan_publication(
        audit_result=payload, repository=REPO, main_sha=MAIN_SHA, existing_issues=[],
    )
    assert plan["schema_valid"] is True
    assert plan["action"] == sp.ACTION_NO_OP
    assert plan["marker"] is None


def test_oversize_body_rejected_not_truncated() -> None:
    """Body exceeding MAX_BODY_LENGTH must be rejected, not truncated.

    Use an execution_prompt that passes validation (<= MAX_EXECUTION_PROMPT_LENGTH)
    but whose resulting body (marker + headers + prompt) exceeds MAX_BODY_LENGTH.
    """
    task = _safe_task()
    # MAX_EXECUTION_PROMPT_LENGTH == MAX_BODY_LENGTH == 8000; a prompt of 8000
    # chars passes validation but the built body (marker + headers + 8000) > 8000.
    task["execution_prompt"] = "x" * sv.MAX_EXECUTION_PROMPT_LENGTH
    plan = sp.plan_publication(
        audit_result=_safe_result(task=task), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    assert plan["action"] == sp.ACTION_NO_OP
    assert plan["policy_allowed"] is False
    assert any(sp.ERR_BODY_TOO_LONG in e for e in plan["errors"])
    assert plan["body"] is None


# --- discovery failure → zero writes ---------------------------------------


class _RecordingRunner:
    """Records calls; simulates gh without network."""

    def __init__(self, issues_json: str = "[]", *, fail_issues: bool = False) -> None:
        self.issues_json = issues_json
        self.fail_issues = fail_issues
        self.calls: list[list[str]] = []

    def __call__(self, args, timeout):
        self.calls.append(list(args))
        from supervisor_context import CommandOutcome

        if self.fail_issues and args[:2] == ["gh", "issue"] and "list" in args:
            return CommandOutcome(1, "", "discovery failed", False)
        if args[:2] == ["gh", "issue"] and "list" in args:
            return CommandOutcome(0, self.issues_json, "", False)
        if args[:3] == ["gh", "api", "user"]:
            return CommandOutcome(0, "dddd2024", "", False)
        if args[:2] == ["git", "status"]:
            return CommandOutcome(0, "", "", False)
        if args[:2] == ["git", "branch"]:
            return CommandOutcome(0, "agent/codex-supervisor-foundation-v0", "", False)
        if args[:2] == ["git", "rev-parse"] and "refs/remotes/origin/main" in args:
            return CommandOutcome(0, MAIN_SHA, "", False)
        return CommandOutcome(0, "", "", False)


def test_dry_run_performs_zero_writes() -> None:
    runner = _RecordingRunner(issues_json="[]")
    issues, err = sp.fetch_existing_issues(REPO, runner=runner)
    assert err is None
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=issues,
    )
    assert plan["action"] == sp.ACTION_CREATE_ISSUE
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=False)
    assert result["applied"] is False
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_discovery_failure_zero_writes() -> None:
    """gh issue list failure → zero writes."""
    runner = _RecordingRunner(fail_issues=True)
    issues, err = sp.fetch_existing_issues(REPO, runner=runner)
    assert err is not None
    assert issues == []
    # Even with discovery failure, dry-run plan should be no-op with errors.
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=issues,
    )
    # plan_publication with empty issues still produces a create plan;
    # the discovery failure is handled at the fetch level.
    # In live mode, the guard catches it.
    if plan["action"] == sp.ACTION_CREATE_ISSUE:
        result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
        # Live guard re-queries and fails on discovery.
        assert result["applied"] is False
        write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
        assert write_calls == []


def test_live_create_calls_gh_issue_create() -> None:
    runner = _RecordingRunner(issues_json="[]")
    issues, err = sp.fetch_existing_issues(REPO, runner=runner)
    assert err is None
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=issues,
    )
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is True
    assert any("create" in c for c in runner.calls)


# --- live guard fail-closed ------------------------------------------------


class _GuardRunner:
    """Runner that allows controlling guard check outcomes."""

    def __init__(
        self,
        *,
        issues_json: str = "[]",
        owner: str = "dddd2024",
        worktree_clean: bool = True,
        branch: str = "agent/codex-supervisor-foundation-v0",
        main_sha: str = MAIN_SHA,
    ) -> None:
        self.issues_json = issues_json
        self.owner = owner
        self.worktree_clean = worktree_clean
        self.branch = branch
        self.main_sha = main_sha
        self.calls: list[list[str]] = []

    def __call__(self, args, timeout):
        self.calls.append(list(args))
        from supervisor_context import CommandOutcome

        if args[:3] == ["gh", "api", "user"]:
            return CommandOutcome(0, self.owner, "", False)
        if args[:2] == ["gh", "issue"] and "list" in args:
            return CommandOutcome(0, self.issues_json, "", False)
        if args[:2] == ["git", "status"]:
            return CommandOutcome(0, "" if self.worktree_clean else " M file.txt", "", False)
        if args[:2] == ["git", "branch"]:
            return CommandOutcome(0, self.branch, "", False)
        if args[:2] == ["git", "rev-parse"] and "refs/remotes/origin/main" in args:
            return CommandOutcome(0, self.main_sha, "", False)
        return CommandOutcome(0, "", "", False)


def _make_create_plan() -> dict:
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    assert plan["action"] == sp.ACTION_CREATE_ISSUE
    return dict(plan)


def test_live_guard_owner_mismatch_zero_writes() -> None:
    runner = _GuardRunner(owner="other-user")
    plan = _make_create_plan()
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert any(sp.ERR_LIVE_GUARD_OWNER in e for e in result["guard_errors"])
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_live_guard_dirty_worktree_zero_writes() -> None:
    runner = _GuardRunner(worktree_clean=False)
    plan = _make_create_plan()
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert any(sp.ERR_LIVE_GUARD_WORKTREE_DIRTY in e for e in result["guard_errors"])
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_live_guard_main_drift_zero_writes() -> None:
    runner = _GuardRunner(main_sha="a" * 40)
    plan = _make_create_plan()
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert any(sp.ERR_LIVE_GUARD_MAIN_DRIFT in e for e in result["guard_errors"])
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_live_guard_branch_mismatch_zero_writes() -> None:
    runner = _GuardRunner(branch="codex/some-other-branch")
    plan = _make_create_plan()
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert any(sp.ERR_LIVE_GUARD_BRANCH in e for e in result["guard_errors"])
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_live_guard_on_main_zero_writes() -> None:
    runner = _GuardRunner(branch="main")
    plan = _make_create_plan()
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert any(sp.ERR_LIVE_GUARD_BRANCH in e for e in result["guard_errors"])


# --- TOCTOU re-query -------------------------------------------------------


def test_toctou_marker_appeared_before_create() -> None:
    """If marker appears between plan and live write, fail-closed."""
    plan = _make_create_plan()
    # Simulate another process creating the issue between plan and apply.
    marker = plan["marker"]
    runner = _GuardRunner(issues_json=json.dumps([{"number": 999, "title": "race", "body": marker, "state": "OPEN"}]))
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert result["reason"] == sp.ERR_TOCTOU
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_toctou_duplicate_marker_during_create() -> None:
    """If two issues carry the marker at live time, fail-closed."""
    plan = _make_create_plan()
    marker = plan["marker"]
    issues = json.dumps([
        {"number": 1, "title": "a", "body": marker, "state": "OPEN"},
        {"number": 2, "title": "b", "body": marker, "state": "OPEN"},
    ])
    runner = _GuardRunner(issues_json=issues)
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert "duplicate" in result["reason"]
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_toctou_update_re_queries_before_write() -> None:
    """Update path also re-queries marker before writing."""
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    marker = first["marker"]
    # Existing issue with marker but different body → update plan.
    existing = [{"number": 5, "title": "old", "body": marker + "\nold note", "state": "OPEN"}]
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert plan["action"] == sp.ACTION_UPDATE_ISSUE
    # At live time, the issue is gone (TOCTOU).
    runner = _GuardRunner(issues_json="[]")
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert result["reason"] == sp.ERR_TOCTOU


# --- context fail-closed ---------------------------------------------------


def test_context_git_failure_raises_no_output() -> None:
    """git/gh failure → ContextError, no context emitted."""

    def failing_runner(args, timeout):
        return sc.CommandOutcome(1, "", "git failed", False)

    with pytest.raises(sc.ContextError):
        sc.collect_context(REPO, runner=failing_runner)


def test_context_timeout_raises_no_output() -> None:
    def timeout_runner(args, timeout):
        return sc.CommandOutcome(-1, "", "", True)

    with pytest.raises(sc.ContextError):
        sc.collect_context(REPO, runner=timeout_runner)


def test_context_invalid_json_raises_no_output() -> None:
    def bad_json_runner(args, timeout):
        if args[:2] == ["gh", "issue"] and "list" in args:
            return sc.CommandOutcome(0, "not valid json", "", False)
        if args[:2] == ["gh", "pr"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:3] == ["gh", "issue", "view"]:
            return sc.CommandOutcome(0, '{"number":90,"title":"t","body":"b"}', "", False)
        if args[:3] == ["gh", "pr", "view"]:
            return sc.CommandOutcome(0, '{"number":93,"title":"t","isDraft":true,"state":"OPEN","headRefName":"b","headRefOid":"' + "a" * 40 + '","baseRefName":"main"}', "", False)
        if args[:3] == ["gh", "pr", "checks"]:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[0] == "git":
            if "symbolic-ref" in args:
                return sc.CommandOutcome(0, "refs/remotes/origin/main", "", False)
            if "rev-parse" in args and "HEAD" in args:
                return sc.CommandOutcome(0, "a" * 40, "", False)
            if "rev-parse" in args:
                return sc.CommandOutcome(0, MAIN_SHA, "", False)
            if "branch" in args:
                return sc.CommandOutcome(0, "agent/codex-supervisor-foundation-v0", "", False)
            if "status" in args:
                return sc.CommandOutcome(0, "", "", False)
            if "log" in args:
                return sc.CommandOutcome(0, "abcdef0 Title", "", False)
        return sc.CommandOutcome(0, "", "", False)

    with pytest.raises(sc.ContextError):
        sc.collect_context(REPO, runner=bad_json_runner)


def test_context_missing_main_sha_raises() -> None:
    def missing_sha_runner(args, timeout):
        if args[0] == "git" and "rev-parse" in args and "refs/remotes/origin/main" in args:
            return sc.CommandOutcome(1, "", "not found", False)
        if args[0] == "git" and "symbolic-ref" in args:
            return sc.CommandOutcome(0, "refs/remotes/origin/main", "", False)
        return sc.CommandOutcome(0, "", "", False)

    with pytest.raises(sc.ContextError):
        sc.collect_context(REPO, runner=missing_sha_runner)


def test_context_does_not_mask_failures_as_empty() -> None:
    """Read failures must NOT be masked as empty Issue/PR lists."""

    def fail_issue_runner(args, timeout):
        if args[:2] == ["gh", "issue"] and "list" in args:
            return sc.CommandOutcome(1, "", "forbidden", False)
        if args[0] == "git":
            if "symbolic-ref" in args:
                return sc.CommandOutcome(0, "refs/remotes/origin/main", "", False)
            if "rev-parse" in args and "HEAD" in args:
                return sc.CommandOutcome(0, "a" * 40, "", False)
            if "rev-parse" in args:
                return sc.CommandOutcome(0, MAIN_SHA, "", False)
            if "branch" in args:
                return sc.CommandOutcome(0, "agent/codex-supervisor-foundation-v0", "", False)
            if "status" in args:
                return sc.CommandOutcome(0, "", "", False)
            if "log" in args:
                return sc.CommandOutcome(0, "abcdef0 Title", "", False)
        return sc.CommandOutcome(0, "", "", False)

    with pytest.raises(sc.ContextError):
        sc.collect_context(REPO, runner=fail_issue_runner)


def test_context_includes_issue_90_and_pr_93_facts() -> None:
    """Context must include Issue #90 goal and PR #93 facts."""

    def good_runner(args, timeout):
        if args[:2] == ["gh", "issue"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:2] == ["gh", "pr"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:3] == ["gh", "issue", "view"] and "90" in args:
            return sc.CommandOutcome(0, json.dumps({"number": 90, "title": "Codex Supervisor v0", "body": "Implement one minimal supervisor cycle"}), "", False)
        if args[:3] == ["gh", "pr", "view"] and "93" in args:
            return sc.CommandOutcome(0, json.dumps({
                "number": 93, "title": "PR #93", "isDraft": True, "state": "OPEN",
                "headRefName": "agent/codex-supervisor-foundation-v0",
                "headRefOid": "a" * 40, "baseRefName": "main",
            }), "", False)
        if args[:3] == ["gh", "pr", "checks"]:
            return sc.CommandOutcome(0, json.dumps([
                {"name": "state-gate", "state": "fail", "link": "https://github.com/dddd2024/reverse-agent/actions/runs/30681854818/job/91320333803"},
                {"name": "baseline", "state": "pass", "link": "https://github.com/dddd2024/reverse-agent/actions/runs/30681854828/job/91320333865"},
            ]), "", False)
        if args[0] == "git":
            if "symbolic-ref" in args:
                return sc.CommandOutcome(0, "refs/remotes/origin/main", "", False)
            if "rev-parse" in args and "HEAD" in args:
                return sc.CommandOutcome(0, "a" * 40, "", False)
            if "rev-parse" in args:
                return sc.CommandOutcome(0, MAIN_SHA, "", False)
            if "branch" in args:
                return sc.CommandOutcome(0, "agent/codex-supervisor-foundation-v0", "", False)
            if "status" in args:
                return sc.CommandOutcome(0, "", "", False)
            if "log" in args:
                return sc.CommandOutcome(0, "abcdef0 Title", "", False)
        return sc.CommandOutcome(0, "", "", False)

    context = sc.collect_context(REPO, runner=good_runner)
    assert "issue_90_goal" in context
    assert context["issue_90_goal"]["number"] == 90
    assert "supervisor" in context["issue_90_goal"]["goal_excerpt"].lower()
    assert "pr_93_facts" in context
    assert context["pr_93_facts"]["number"] == 93
    assert context["pr_93_facts"]["draft"] is True
    assert context["pr_93_facts"]["head_sha"] == "a" * 40
    # Checks include state-gate fail and baseline pass.
    check_names = {c["name"] for c in context["pr_93_facts"]["checks"]}
    assert "state-gate" in check_names
    assert "baseline" in check_names


# --- context bounds and safety --------------------------------------------


def test_context_bounds_issues_and_commits() -> None:
    assert sc.MAX_ISSUES == 50
    assert sc.MAX_PRS == 50
    assert sc.MAX_COMMITS == 50


def test_context_output_has_no_env_or_credentials() -> None:
    import supervisor_context as sc_mod

    src = pathlib.Path(sc_mod.__file__).read_text(encoding="utf-8")
    assert "os.environ" not in src
    assert "API_KEY" not in src
    assert "GITHUB_TOKEN" not in src


def test_git_and_gh_args_are_bounded_and_explicit() -> None:
    runner_calls: list[list[str]] = []

    def fake_runner(args, timeout):
        runner_calls.append(list(args))
        return sc.CommandOutcome(0, "", "", False)

    with pytest.raises(sc.ContextError):
        sc.collect_context(REPO, runner=fake_runner)
    for call in runner_calls:
        assert call[0] in ("git", "gh")
        for arg in call[1:]:
            assert isinstance(arg, str)
            assert all(ch not in arg for ch in ("|", ";", "&", "`", "$("))


# --- security: output contains no secrets ----------------------------------


def test_plan_output_has_no_credentials_or_env_dump() -> None:
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    blob = json.dumps(plan)
    forbidden = ["gho_", "ghp_", "Authorization:", "Bearer ", "os.environ", "CHATGPT_SESSION"]
    for token in forbidden:
        assert token not in blob


def test_supervisor_scripts_have_no_shell_or_credentials() -> None:
    for name in ("supervisor_context.py", "supervisor_validate.py", "supervisor_publish.py"):
        src = (_SCRIPTS / name).read_text(encoding="utf-8")
        assert "shell=True" not in src
        assert "os.environ" not in src
        for token in ("gho_", "ghp_", "Bearer ", "Authorization:", "CHATGPT_SESSION"):
            assert token not in src
