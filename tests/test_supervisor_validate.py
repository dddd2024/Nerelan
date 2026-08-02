from __future__ import annotations

import json
import pathlib
import subprocess
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


def test_negation_not_skipped_v03() -> None:
    """v0.3: no negation skip. 'Do not merge' and 'Never push to main' are
    still rejected because forbidden operations belong in forbidden_scope,
    not prompt negation. Legitimate prohibitions must be expressed as
    forbidden_scope entries, not as natural-language negation in goal /
    execution_prompt.
    """
    task = _safe_task()
    task["execution_prompt"] = "Do not merge anything. Never push to main."
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    # Both "merge" and "push to main" must be flagged (no negation skip).
    assert sv.POLICY_MERGE_FORBIDDEN in errors
    assert sv.POLICY_MAIN_PUSH_FORBIDDEN in errors


def test_do_not_merge_but_deploy_rejected() -> None:
    """v0.3: 'do not merge but deploy' is rejected because:
    (a) the negation is no longer skipped, so 'merge' is flagged, and
    (b) 'deploy' is flagged regardless of any preceding 'do not'.
    """
    task = _safe_task()
    task["execution_prompt"] = "Do not merge anything but deploy to production."
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_MERGE_FORBIDDEN in errors
    assert sv.POLICY_DEPLOYMENT_FORBIDDEN in errors


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


def _api_path(args: list[str], prefix: str) -> bool:
    """True if args is a ``gh api <prefix>`` call."""
    return args[:2] == ["gh", "api"] and len(args) > 2 and args[2].startswith(prefix)


def _page_arg(args: list[str]) -> int:
    """Extract the ``page=N`` value from a gh api paginated call."""
    for a in args:
        if isinstance(a, str) and a.startswith("page="):
            try:
                return int(a.split("=", 1)[1])
            except ValueError:
                return 1
    return 1


def _paginated_issues_response(issues_json: str, page: int) -> str:
    """Return the requested page of a pre-built issues JSON array.

    ``issues_json`` is a full JSON array. Split it into PAGE_SIZE chunks so
    that callers can simulate multi-page responses.
    """
    try:
        all_items = json.loads(issues_json)
    except json.JSONDecodeError:
        return issues_json  # let the caller surface the parse error
    if not isinstance(all_items, list):
        return issues_json
    page_size = 100
    start = (page - 1) * page_size
    chunk = all_items[start:start + page_size]
    return json.dumps(chunk)


class _RecordingRunner:
    """Records calls; simulates gh without network (v0.3 paginated api)."""

    def __init__(self, issues_json: str = "[]", *, fail_issues: bool = False) -> None:
        self.issues_json = issues_json
        self.fail_issues = fail_issues
        self.calls: list[list[str]] = []

    def __call__(self, args, timeout):
        self.calls.append(list(args))
        from supervisor_context import CommandOutcome

        # gh api repos/<repo>/issues (paginated) — replaces gh issue list.
        if self.fail_issues and _api_path(args, "repos/") and "/issues" in args[2]:
            return CommandOutcome(1, "", "discovery failed", False)
        if _api_path(args, "repos/") and "/issues" in args[2]:
            page = _page_arg(args)
            return CommandOutcome(0, _paginated_issues_response(self.issues_json, page), "", False)
        if args[:3] == ["gh", "api", "user"]:
            return CommandOutcome(0, "dddd2024", "", False)
        if args[:2] == ["git", "status"]:
            return CommandOutcome(0, "", "", False)
        if args[:2] == ["git", "branch"]:
            return CommandOutcome(0, "agent/codex-supervisor-foundation-v0", "", False)
        if args[:2] == ["git", "rev-parse"] and "refs/remotes/origin/main" in args:
            return CommandOutcome(0, MAIN_SHA, "", False)
        if _api_path(args, "repos/") and args[2].endswith("/git/refs/heads/main"):
            return CommandOutcome(0, json.dumps({"object": {"sha": MAIN_SHA, "type": "commit"}}), "", False)
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
    """Runner that allows controlling guard check outcomes (v0.3 paginated api)."""

    def __init__(
        self,
        *,
        issues_json: str = "[]",
        owner: str = "dddd2024",
        worktree_clean: bool = True,
        branch: str = "agent/codex-supervisor-foundation-v0",
        main_sha: str = MAIN_SHA,
        remote_main_sha: str | None = None,
        fail_issues_page: int | None = None,
    ) -> None:
        self.issues_json = issues_json
        self.owner = owner
        self.worktree_clean = worktree_clean
        self.branch = branch
        self.main_sha = main_sha
        # GitHub-side main SHA (gh api refs/heads/main). Defaults to main_sha.
        self.remote_main_sha = remote_main_sha if remote_main_sha is not None else main_sha
        # If set, the given page of gh api issues fails (for pagination tests).
        self.fail_issues_page = fail_issues_page
        self.calls: list[list[str]] = []

    def __call__(self, args, timeout):
        self.calls.append(list(args))
        from supervisor_context import CommandOutcome

        if args[:3] == ["gh", "api", "user"]:
            return CommandOutcome(0, self.owner, "", False)
        # gh api repos/<repo>/issues (paginated) — replaces gh issue list.
        if _api_path(args, "repos/") and "/issues" in args[2]:
            page = _page_arg(args)
            if self.fail_issues_page is not None and page >= self.fail_issues_page:
                return CommandOutcome(1, "", "page failed", False)
            return CommandOutcome(0, _paginated_issues_response(self.issues_json, page), "", False)
        if _api_path(args, "repos/") and args[2].endswith("/git/refs/heads/main"):
            if self.remote_main_sha is None:
                return CommandOutcome(1, "", "remote main fetch failed", False)
            return CommandOutcome(0, json.dumps({"object": {"sha": self.remote_main_sha, "type": "commit"}}), "", False)
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


def test_default_runner_decodes_utf8_bytes_without_locale_dependency(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(args, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(
            args,
            0,
            stdout="Windows UTF-8: \u6d4b\u8bd5".encode("utf-8"),
            stderr="\u5b8c\u6210".encode("utf-8"),
        )

    monkeypatch.setattr(sc.subprocess, "run", fake_run)
    outcome = sc.default_runner(["example", "--read-only"], 1.0)

    assert outcome.exit_code == 0
    assert outcome.stdout == "Windows UTF-8: \u6d4b\u8bd5"
    assert outcome.stderr == "\u5b8c\u6210"
    assert captured["text"] is False
    assert "encoding" not in captured
    assert "errors" not in captured


def test_default_runner_invalid_utf8_returns_finite_error_without_partial_output(
    monkeypatch,
) -> None:
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args,
            0,
            stdout=b"valid prefix\xff",
            stderr=b"partial diagnostic",
        )

    monkeypatch.setattr(sc.subprocess, "run", fake_run)
    outcome = sc.default_runner(["example"], 1.0)

    assert outcome.exit_code == sc.DECODE_ERROR_EXIT_CODE
    assert outcome.stdout == ""
    assert outcome.stderr == "UTF8_DECODE_ERROR"
    assert outcome.timed_out is False
    assert isinstance(outcome.stdout, str)
    assert isinstance(outcome.stderr, str)


def test_default_runner_none_streams_are_empty_strings(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout=None, stderr=None)

    monkeypatch.setattr(sc.subprocess, "run", fake_run)
    outcome = sc.default_runner(["example"], 1.0)

    assert outcome.stdout == ""
    assert outcome.stderr == ""
    assert isinstance(outcome.stdout, str)
    assert isinstance(outcome.stderr, str)


def test_default_runner_timeout_bytes_and_none_are_stable_strings(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=args,
            timeout=kwargs["timeout"],
            output="\u8d85\u65f6\u524d\u8f93\u51fa".encode("utf-8"),
            stderr=None,
        )

    monkeypatch.setattr(sc.subprocess, "run", fake_run)
    outcome = sc.default_runner(["example"], 1.0)

    assert outcome.exit_code == -1
    assert outcome.stdout == "\u8d85\u65f6\u524d\u8f93\u51fa"
    assert outcome.stderr == ""
    assert outcome.timed_out is True
    assert isinstance(outcome.stdout, str)
    assert isinstance(outcome.stderr, str)


def test_default_runner_timeout_invalid_utf8_discards_partial_output(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=args,
            timeout=kwargs["timeout"],
            output=b"partial\xff",
            stderr=None,
        )

    monkeypatch.setattr(sc.subprocess, "run", fake_run)
    outcome = sc.default_runner(["example"], 1.0)

    assert outcome.exit_code == sc.DECODE_ERROR_EXIT_CODE
    assert outcome.stdout == ""
    assert outcome.stderr == "UTF8_DECODE_ERROR"
    assert outcome.timed_out is True


def test_context_decode_failure_raises_without_partial_context(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args,
            0,
            stdout=b"partial context\xff",
            stderr=None,
        )

    monkeypatch.setattr(sc.subprocess, "run", fake_run)

    with pytest.raises(sc.ContextError, match=r"exit=-2"):
        sc.collect_context(REPO, runner=sc.default_runner)


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
        # v0.3: gh api repos/<repo>/issues (paginated) — replaces gh issue list.
        if _api_path(list(args), "repos/") and "/issues" in args[2]:
            return sc.CommandOutcome(0, "not valid json", "", False)
        if args[:2] == ["gh", "pr"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:3] == ["gh", "issue", "view"]:
            return sc.CommandOutcome(0, '{"number":90,"title":"t","body":"b"}', "", False)
        if args[:3] == ["gh", "pr", "view"]:
            return sc.CommandOutcome(0, '{"number":93,"title":"t","isDraft":true,"state":"OPEN","headRefName":"b","headRefOid":"' + "a" * 40 + '","baseRefName":"main"}', "", False)
        # v0.3: gh api check-runs (paginated) — replaces gh pr checks.
        if _api_path(list(args), "repos/") and "/check-runs" in args[2]:
            return sc.CommandOutcome(0, '{"check_runs":[]}', "", False)
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
        # v0.3: gh api repos/<repo>/issues (paginated) — replaces gh issue list.
        if _api_path(list(args), "repos/") and "/issues" in args[2]:
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
    """Context must include Issue #90 goal and PR #93 facts (v0.3 configurable)."""

    def good_runner(args, timeout):
        if _api_path(list(args), "repos/") and args[2].endswith("/git/refs/heads/main"):
            return sc.CommandOutcome(0, json.dumps({"object": {"sha": MAIN_SHA}}), "", False)
        # v0.3: gh api repos/<repo>/issues (paginated) — replaces gh issue list.
        if _api_path(list(args), "repos/") and "/issues" in args[2]:
            page = _page_arg(list(args))
            return sc.CommandOutcome(0, _paginated_issues_response("[]", page), "", False)
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
        # v0.3: gh api check-runs bound to exact head — replaces gh pr checks.
        if _api_path(list(args), "repos/") and "/check-runs" in args[2]:
            return sc.CommandOutcome(0, json.dumps({
                "total_count": 2,
                "check_runs": [
                    {"name": "state-gate", "status": "completed", "conclusion": "failure", "html_url": "https://github.com/dddd2024/reverse-agent/runs/1"},
                    {"name": "baseline", "status": "completed", "conclusion": "success", "html_url": "https://github.com/dddd2024/reverse-agent/runs/2"},
                ]
            }), "", False)
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

    # v0.3: goal_issue and active_pr are configurable; pass explicitly so the
    # test does not depend on branch-derived PR lookup.
    context = sc.collect_context(REPO, goal_issue=90, active_pr=93, runner=good_runner)
    # v0.3: field names are configurable (issue_goal / pr_facts, not hardcoded).
    assert "issue_goal" in context
    assert context["issue_goal"]["number"] == 90
    assert "supervisor" in context["issue_goal"]["goal_excerpt"].lower()
    assert "pr_facts" in context
    assert context["pr_facts"]["number"] == 93
    assert context["pr_facts"]["draft"] is True
    assert context["pr_facts"]["head_sha"] == "a" * 40
    # v0.3: failed checks still appear (not masked by gh pr checks exit code).
    check_names = {c["name"] for c in context["pr_facts"]["checks"]}
    assert "state-gate" in check_names
    assert "baseline" in check_names
    # Failed check retains name, status, conclusion, and bounded run_url.
    state_gate = next(c for c in context["pr_facts"]["checks"] if c["name"] == "state-gate")
    assert state_gate["conclusion"] == "failure"
    assert state_gate["status"] == "completed"
    assert "run_url" in state_gate


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


# =========================================================================
# v0.3 fail-closed closure tests.
#
# These tests cover the new behaviors required by Issue #92 PR #93 rework:
#   - Checks collection via gh api check-runs (failed checks retained).
#   - Check API failure → no Context.
#   - Paginated Issue discovery (101st Issue Marker found).
#   - Page 2 failure → zero writes.
#   - Malformed Issue entry → fail-closed.
#   - GitHub remote main drift → zero writes.
#   - Local origin/main drift → zero writes.
#   - Closed Issue with changed Marker → zero writes (CLOSED_MARKER_REQUIRES_OWNER).
#   - Duplicate Marker → fail-closed (v0.2 behavior preserved).
#   - Multiple Markers in one Issue → fail-closed.
#   - git merge-base allowed; gh pr merge rejected.
#   - Shell chaining / substitution rejected.
#   - Operation–prompt inconsistency rejected.
#   - Active PR configurable.
#   - Single-machine publish lock: contention → zero writes; released after exception.
# =========================================================================


def _v03_good_runner_factory(*, check_runs_payload: str | None = None, fail_check_api: bool = False):
    """Build a runner that returns valid v0.3 responses for collect_context.

    Returns a (runner, calls) tuple where calls is the list of recorded args.
    """

    calls: list[list[str]] = []

    def runner(args, timeout):
        calls.append(list(args))
        if _api_path(list(args), "repos/") and args[2].endswith("/git/refs/heads/main"):
            return sc.CommandOutcome(0, json.dumps({"object": {"sha": MAIN_SHA}}), "", False)
        if _api_path(list(args), "repos/") and "/issues" in args[2]:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:2] == ["gh", "pr"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:3] == ["gh", "issue", "view"]:
            return sc.CommandOutcome(0, json.dumps({"number": 90, "title": "t", "body": "b"}), "", False)
        if args[:3] == ["gh", "pr", "view"]:
            return sc.CommandOutcome(0, json.dumps({
                "number": 93, "title": "t", "isDraft": True, "state": "OPEN",
                "headRefName": "b", "headRefOid": "a" * 40, "baseRefName": "main",
            }), "", False)
        if _api_path(list(args), "repos/") and "/check-runs" in args[2]:
            if fail_check_api:
                return sc.CommandOutcome(1, "", "check api failed", False)
            return sc.CommandOutcome(0, check_runs_payload or '{"total_count":0,"check_runs":[]}', "", False)
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

    return runner, calls


# --- Task 1: Checks collection via gh api check-runs ----------------------


def test_failed_check_appears_in_context() -> None:
    """A failed check must still appear in the Context with name, status,
    conclusion, and bounded run_url — not masked by an exit code.
    """
    payload = json.dumps({
        "total_count": 2,
        "check_runs": [
            {"name": "state-gate", "status": "completed", "conclusion": "failure", "html_url": "https://github.com/dddd2024/reverse-agent/runs/1"},
            {"name": "baseline", "status": "completed", "conclusion": "success", "html_url": "https://github.com/dddd2024/reverse-agent/runs/2"},
        ]
    })
    runner, _ = _v03_good_runner_factory(check_runs_payload=payload)
    context = sc.collect_context(REPO, goal_issue=90, active_pr=93, runner=runner)
    checks = context["pr_facts"]["checks"]
    names = {c["name"] for c in checks}
    assert "state-gate" in names and "baseline" in names
    failed = next(c for c in checks if c["name"] == "state-gate")
    assert failed["conclusion"] == "failure"
    assert failed["status"] == "completed"
    assert "run_url" in failed and failed["run_url"]


def test_check_api_failure_no_context() -> None:
    """If gh api check-runs fails, no Context is emitted (fail-closed)."""
    runner, _ = _v03_good_runner_factory(fail_check_api=True)
    with pytest.raises(sc.ContextError):
        sc.collect_context(REPO, goal_issue=90, active_pr=93, runner=runner)


# --- Task 2: paginated Issue discovery ------------------------------------


def test_issue_101_marker_discovered() -> None:
    """The 101st Issue (page 2, item 1) carrying the marker must be found.
    This exercises the paginated gh api discovery path.
    """
    # Build a create plan (computes the marker body).
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    marker_body = plan["body"]
    # 100 dummy issues on page 1, then the marker issue as #101 on page 2.
    page1 = [{"number": i, "title": f"old-{i}", "body": "", "state": "CLOSED"} for i in range(1, 101)]
    page2 = [{"number": 101, "title": "marker-issue", "body": marker_body, "state": "OPEN"}]
    all_issues = page1 + page2
    runner = _RecordingRunner(issues_json=json.dumps(all_issues))
    issues, err = sp.fetch_existing_issues(REPO, runner=runner)
    assert err is None
    # The 101st issue (marker) must be present in the fetched set.
    numbers = {i.get("number") for i in issues}
    assert 101 in numbers


def test_page2_failure_zero_writes() -> None:
    """If page 2 of gh api issues fails, discovery returns an error and
    live writes do not occur.
    """
    # Page 1 has 100 issues (full page), forcing a page 2 fetch which fails.
    page1 = [{"number": i, "title": f"old-{i}", "body": "", "state": "CLOSED"} for i in range(1, 101)]
    runner = _GuardRunner(issues_json=json.dumps(page1), fail_issues_page=2)
    issues, err = sp.fetch_existing_issues(REPO, runner=runner)
    assert err is not None
    assert issues == []
    assert "page 2" in err


def test_malformed_issue_entry_fail_closed() -> None:
    """A malformed Issue entry (missing number/body/state) must fail-closed
    rather than being silently skipped.
    """
    malformed = json.dumps([
        {"number": 1, "body": "x", "state": "OPEN"},  # missing title is OK
        {"number": 2, "title": "no-body", "state": "OPEN"},  # missing body
    ])
    runner = _RecordingRunner(issues_json=malformed)
    issues, err = sp.fetch_existing_issues(REPO, runner=runner)
    assert err is not None
    assert "missing" in err


def test_pr_entries_filtered_from_issues() -> None:
    """The /issues endpoint returns PR entries (with a pull_request field).
    These must be filtered out — they are NOT Issues.
    """
    mixed = json.dumps([
        {"number": 1, "title": "real issue", "body": "b", "state": "OPEN"},
        {"number": 2, "title": "pr leak", "body": "b", "state": "OPEN", "pull_request": {"url": "x"}},
    ])
    runner = _RecordingRunner(issues_json=mixed)
    issues, err = sp.fetch_existing_issues(REPO, runner=runner)
    assert err is None
    numbers = {i.get("number") for i in issues}
    assert 1 in numbers
    assert 2 not in numbers  # PR entry filtered out.


# --- Task 3: remote main verification -------------------------------------


def test_remote_main_drift_zero_writes() -> None:
    """If GitHub's refs/heads/main differs from audited_main_sha, zero writes."""
    plan = _make_create_plan()
    # GitHub remote main has drifted to a different SHA.
    runner = _GuardRunner(remote_main_sha="b" * 40)
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert any(sp.ERR_LIVE_GUARD_REMOTE_MAIN in e for e in result["guard_errors"])
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_local_main_drift_zero_writes() -> None:
    """If local origin/main differs from audited_main_sha, zero writes."""
    plan = _make_create_plan()
    # Local origin/main has drifted (git rev-parse returns a different SHA).
    runner = _GuardRunner(main_sha="c" * 40, remote_main_sha=MAIN_SHA)
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert any(sp.ERR_LIVE_GUARD_LOCAL_MAIN in e for e in result["guard_errors"])
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_remote_main_api_failure_zero_writes() -> None:
    """If gh api refs/heads/main fails, zero writes."""
    plan = _make_create_plan()
    runner = _GuardRunner()
    # Override remote main to None → gh api failure.
    runner.remote_main_sha = None
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert any(sp.ERR_LIVE_GUARD_REMOTE_MAIN in e for e in result["guard_errors"])


# --- Task 4: closed Issue Marker handling ---------------------------------


def test_closed_changed_marker_zero_writes() -> None:
    """A closed Issue carrying the same Marker but different content must
    yield CLOSED_MARKER_REQUIRES_OWNER (zero writes, no auto-edit, no
    reopen, no surrogate create).
    """
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    # Same marker (same key) but body altered by a human note, in a CLOSED issue.
    existing = [{"number": 7, "title": first["title"], "body": first["body"] + "\nhuman edit", "state": "CLOSED"}]
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert plan["action"] == sp.ACTION_NO_OP
    assert plan["policy_allowed"] is False
    assert any(sp.ERR_CLOSED_MARKER_REQUIRES_OWNER in e for e in plan["errors"])
    assert plan["target_issue"] == 7


def test_closed_same_marker_no_op() -> None:
    """A closed Issue carrying the same Marker with identical content is no_op."""
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    existing = [{"number": 99, "title": first["title"], "body": first["body"], "state": "CLOSED"}]
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert plan["action"] == sp.ACTION_NO_OP
    assert plan["policy_allowed"] is True
    assert plan["errors"] == []
    assert plan["target_issue"] == 99


def test_multi_marker_in_one_issue_fail_closed() -> None:
    """If a single Issue carries multiple distinct markers, fail-closed."""
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    # Build a second marker by changing the goal.
    task2 = _safe_task()
    task2["goal"] = "A different bounded goal"
    second = sp.plan_publication(
        audit_result=_safe_result(task=task2), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    # One Issue carrying both markers.
    combined_body = first["body"] + "\n" + second["body"]
    existing = [{"number": 1, "title": "multi", "body": combined_body, "state": "OPEN"}]
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert plan["action"] == sp.ACTION_NO_OP
    assert plan["policy_allowed"] is False
    assert any(sp.ERR_MULTI_MARKER_IN_ISSUE in e for e in plan["errors"])


# --- Task 5: command / token checks ---------------------------------------


def test_git_merge_base_allowed() -> None:
    """git merge-base is a safe command and must NOT be rejected."""
    task = _safe_task()
    task["acceptance_checks"] = ["git merge-base HEAD origin/main"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors


def test_gh_pr_merge_rejected() -> None:
    """gh pr merge is a dangerous command and must be rejected."""
    task = _safe_task()
    task["acceptance_checks"] = ["gh pr merge 93 --merge"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_DANGEROUS_ACCEPTANCE_CHECK in e for e in errors)


def test_git_branch_D_rejected() -> None:
    """git branch -D (branch deletion) must be rejected."""
    task = _safe_task()
    task["acceptance_checks"] = ["git branch -D feature/x"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_BRANCH_DELETION_FORBIDDEN in e for e in errors)


def test_shell_chain_rejected() -> None:
    """Shell chaining (&&) in acceptance_checks must be rejected."""
    task = _safe_task()
    task["acceptance_checks"] = ["pytest && flake8"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_SHELL_METACHAR_FORBIDDEN in e for e in errors)


def test_shell_substitution_rejected() -> None:
    """Shell command substitution $() in acceptance_checks must be rejected."""
    task = _safe_task()
    task["acceptance_checks"] = ["echo $(whoami)"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_SHELL_METACHAR_FORBIDDEN in e for e in errors)


def test_shell_redirect_rejected() -> None:
    """Shell redirection (>) in acceptance_checks must be rejected."""
    task = _safe_task()
    task["acceptance_checks"] = ["pytest tests/ > out.txt"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_SHELL_METACHAR_FORBIDDEN in e for e in errors)


# --- Task 5: operation–prompt consistency ---------------------------------


def test_operation_prompt_consistency_read_only_file_scope_passes() -> None:
    """Bounded repository paths remain read-only without edit authority."""
    task = _safe_task()
    task["goal"] = "Inspect and analyze the bounded validator behavior."
    task["allowed_scope"] = [
        "scripts/supervisor_validate.py",
        "docs/supervisor/audit-instructions.md",
    ]
    task["requested_operations"] = ["read_repository", "run_checks"]
    task["execution_prompt"] = (
        "Verify the operation consistency contract and report the results."
    )
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors


def test_operation_prompt_consistency_edit_intent_without_permission_rejected() -> None:
    task = _safe_task()
    task["goal"] = "Correct the bounded validator behavior."
    task["allowed_scope"] = ["scripts/supervisor_validate.py"]
    task["requested_operations"] = ["read_repository", "run_checks"]
    task["execution_prompt"] = "Implement the bounded validator correction."
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert (
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:edit_bounded_files_required"
        in errors
    )


def test_operation_prompt_consistency_edit_intent_with_permission_passes() -> None:
    task = _safe_task()
    task["goal"] = "Correct the bounded validator behavior."
    task["allowed_scope"] = ["scripts/supervisor_validate.py"]
    task["requested_operations"] = [
        "read_repository",
        "edit_bounded_files",
        "run_checks",
    ]
    task["execution_prompt"] = "Implement the bounded validator correction."
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Modify the audit report.",
        "Write an audit report.",
        "Update the status summary.",
        "Add evidence to the report.",
        "Change the result description.",
        "Remove a stale status note.",
        "Create a test report.",
    ],
)
def test_operation_prompt_consistency_reporting_language_is_read_only(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect and report the bounded result."
    task["allowed_scope"] = ["scripts/supervisor_validate.py"]
    task["requested_operations"] = ["read_repository", "run_checks"]
    task["execution_prompt"] = execution_prompt
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Do not edit repository files. Inspect and report only.",
        "Do not under any circumstances edit repository files.",
        "Never modify source code. Inspect and report only.",
        "Must not modify source code. Inspect and report only.",
        "Should not patch the validator. Inspect and report only.",
        "Under no circumstances fix repository files. Inspect and report only.",
        "Must never refactor the validator. Inspect and report only.",
        "Without changing any files, inspect the validator and report only.",
        "Never create an Issue comment. Inspect and report only.",
    ],
)
def test_operation_prompt_consistency_direct_negation_is_read_only(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect and report the bounded result."
    task["requested_operations"] = ["read_repository", "run_checks"]
    task["execution_prompt"] = execution_prompt
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


def test_operation_prompt_consistency_negation_does_not_hide_later_edit() -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded validator behavior."
    task["requested_operations"] = ["read_repository", "run_checks"]
    task["execution_prompt"] = (
        "Do not edit file X, but implement the validator correction in "
        "scripts/supervisor_validate.py."
    )
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert (
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:edit_bounded_files_required"
        in errors
    )


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Implement the validator correction.",
        "Update scripts/supervisor_validate.py.",
        "Add a regression test.",
        "Patch the validator function.",
        "Refactor the bounded implementation.",
    ],
)
def test_operation_prompt_consistency_repository_edit_requires_permission(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded validator behavior."
    task["requested_operations"] = ["read_repository", "run_checks"]
    task["execution_prompt"] = execution_prompt
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert (
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:edit_bounded_files_required"
        in errors
    )

    task["requested_operations"].append("edit_bounded_files")
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


def test_operation_prompt_consistency_push_without_permission_rejected() -> None:
    """If the prompt mentions 'push' but requested_operations lacks
    push_named_branch, the plan must be rejected.
    """
    task = _safe_task()
    task["execution_prompt"] = "Push the bounded changes to the named branch."
    task["requested_operations"] = ["read_repository", "edit_bounded_files", "run_checks", "create_or_update_draft_pr"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.OPERATION_PROMPT_INCONSISTENCY in e for e in errors)


def test_operation_prompt_consistency_push_with_permission_passes() -> None:
    task = _safe_task()
    task["execution_prompt"] = "Edit the bounded file and push the named branch."
    task["requested_operations"] = [
        "read_repository",
        "edit_bounded_files",
        "run_checks",
        "push_named_branch",
    ]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors


def test_operation_prompt_consistency_draft_pr_without_permission_rejected() -> None:
    """If the prompt mentions 'draft pr' but requested_operations lacks
    create_or_update_draft_pr, the plan must be rejected.
    """
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = "Fix the draft PR description with evidence."
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert errors == [
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:create_or_update_draft_pr_required"
    ]


def test_operation_prompt_consistency_draft_pr_with_permission_passes() -> None:
    """Draft PR metadata authority does not imply repository edit authority."""
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = "Fix the draft PR description with evidence."
    task["requested_operations"] = ["read_repository", "create_or_update_draft_pr"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Edit the PR body with evidence.",
        "Modify the draft pull request description with evidence.",
        "Update github.com/dddd2024/reverse-agent/pull/93 description.",
        "Update https://github.com/dddd2024/reverse-agent/pull/93 description.",
        "Update PR #93 body.",
        "Update pull request #93 description.",
        "Edit PR #93 body with evidence.",
        "Modify pull request #93 description with evidence.",
    ],
)
def test_operation_prompt_consistency_draft_pr_surface_never_requires_file_edit(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository", "create_or_update_draft_pr"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Update PR #93 body.",
        "Update pull request #93 description.",
        "Edit PR #93 body with evidence.",
        "Modify pull request #93 description.",
    ],
)
def test_operation_prompt_consistency_numbered_draft_pr_metadata_requires_permission(
    execution_prompt: str,
) -> None:
    """Numbered Draft PR metadata phrases must require create_or_update_draft_pr."""
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert f"{sv.OPERATION_PROMPT_INCONSISTENCY}:create_or_update_draft_pr_required" in errors

    task["requested_operations"].append("create_or_update_draft_pr")
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


def test_operation_prompt_consistency_repository_and_draft_pr_need_both_permissions() -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = (
        "Fix scripts/supervisor_validate.py, then edit the PR body with evidence."
    )
    task["requested_operations"] = ["read_repository", "create_or_update_draft_pr"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert f"{sv.OPERATION_PROMPT_INCONSISTENCY}:edit_bounded_files_required" in errors

    task["requested_operations"].append("edit_bounded_files")
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Update scripts/supervisor_validate.py and edit the PR body.",
        "Edit the PR body and update scripts/supervisor_validate.py.",
    ],
)
def test_operation_prompt_consistency_same_clause_surfaces_are_additive(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert set(errors) == {
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:edit_bounded_files_required",
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:create_or_update_draft_pr_required",
    }

    task["requested_operations"].extend(
        ["edit_bounded_files", "create_or_update_draft_pr"]
    )
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


@pytest.mark.parametrize(
    ("requested_operations", "expected_error"),
    [
        (
            ["read_repository", "edit_bounded_files"],
            "create_or_update_draft_pr_required",
        ),
        (
            ["read_repository", "create_or_update_draft_pr"],
            "edit_bounded_files_required",
        ),
    ],
)
def test_operation_prompt_consistency_same_clause_requires_missing_surface_permission(
    requested_operations: list[str],
    expected_error: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = (
        "Update scripts/supervisor_validate.py and edit the PR body."
    )
    task["requested_operations"] = requested_operations
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert errors == [f"{sv.OPERATION_PROMPT_INCONSISTENCY}:{expected_error}"]


def test_operation_prompt_consistency_draft_pr_and_issue_surfaces_are_additive() -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = (
        "Update the draft PR description and create an Issue comment."
    )
    task["requested_operations"] = ["read_repository", "create_or_update_draft_pr"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert errors == [
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:unsupported_mutation_surface"
    ]


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Write an audit report for Issue #92.",
        "Update the status summary for Issue #92.",
        "Write an evidence summary for Issue #92.",
        "Write the evidence summary for PR #93.",
        "Update the status summary for PR #93.",
        "Describe the result of PR #93.",
    ],
)
def test_operation_prompt_consistency_github_number_reference_is_read_only(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository", "run_checks"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Modify the audit report.",
        "Create an audit report.",
        "Create a test report.",
        "Update the status summary.",
        "Change the result description.",
    ],
)
def test_operation_prompt_consistency_reporting_without_repository_target_is_read_only(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository", "run_checks"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Create a test report file.",
        "Modify the audit report generator function.",
        "Modify the status report module.",
        "Update the report-building code.",
        "Edit the report implementation.",
        "Edit docs/report.md.",
        "Add a regression test.",
        "Modify the validator test.",
    ],
)
def test_operation_prompt_consistency_reporting_noun_does_not_hide_repository_target(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert errors == [
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:edit_bounded_files_required"
    ]


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Edit the Issue comment.",
        "Create an Issue comment.",
        "Edit the Issue body.",
        "Edit Issue #92 body.",
        "Close the Issue.",
        "Close Issue #92.",
        "Reopen Issue #92.",
        "Change the Issue labels.",
        "Assign the Issue.",
        "Assign Issue #92.",
        "Unassign Issue #92.",
        "Comment on Issue #92.",
        "Add a PR review comment.",
        "Review PR #93.",
        "Approve PR #93.",
        "Label PR #93.",
        "Mark PR #93 ready.",
        "Create a branch.",
        "Delete the branch.",
        "Rename the branch.",
        "Add label to PR #93.",
        "Add labels to PR #93.",
        "Add comment to PR #93.",
        "Add review to PR #93.",
        "Add label to pull request #93.",
        "Add comment to Issue #92.",
        "Add label to Issue #92.",
    ],
)
def test_operation_prompt_consistency_unsupported_github_mutation_rejected(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert errors == [
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:unsupported_mutation_surface"
    ]


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Do not push the branch.",
        "Never push to origin.",
        "Must not push the current branch.",
        "Push evidence into the report.",
        "Push the analysis further.",
    ],
)
def test_operation_prompt_consistency_nonpublication_push_is_read_only(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


def test_operation_prompt_consistency_push_negation_is_occurrence_bounded() -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = (
        "Do not push branch X, but push the named branch to origin."
    )
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert errors == [
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:push_named_branch_required"
    ]


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Push the named branch.",
        "Push the current branch to origin.",
        "Push agent/codex-supervisor-foundation-v0 to origin.",
    ],
)
def test_operation_prompt_consistency_positive_named_branch_push_requires_permission(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert errors == [
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:push_named_branch_required"
    ]

    task["requested_operations"].append("push_named_branch")
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Update pass/fail status.",
        "Update read/write status.",
        "Update allow/deny status.",
        "Update version 1.0.",
        "Update version 2.5.",
        "Update score 2.5.",
        "Update score 3.0.",
        "Review https://github.com/dddd2024/reverse-agent/pull/93.",
        "Review github.com/dddd2024/reverse-agent/issues/92.",
    ],
)
def test_operation_prompt_consistency_nonpaths_do_not_require_file_edit(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert ok and not errors


@pytest.mark.parametrize(
    "execution_prompt",
    [
        "Update scripts/supervisor_validate.py.",
        "Update tests/test_supervisor_validate.py.",
        "Update docs/supervisor/audit-instructions.md.",
        "Update README.md.",
        "Update config.json.",
        "Update src/module.py.",
        'Update "README.md".',
        'Update (README.md).',
        'Edit "config.json".',
        'Modify (src/module.py).',
    ],
)
def test_operation_prompt_consistency_real_relative_paths_require_file_edit(
    execution_prompt: str,
) -> None:
    task = _safe_task()
    task["goal"] = "Inspect the bounded evidence."
    task["execution_prompt"] = execution_prompt
    task["requested_operations"] = ["read_repository"]
    ok, errors, _ = sv.validate_audit_result(
        _safe_result(task=task),
        expected_repository=REPO,
        expected_main_sha=MAIN_SHA,
    )
    assert not ok
    assert errors == [
        f"{sv.OPERATION_PROMPT_INCONSISTENCY}:edit_bounded_files_required"
    ]


def test_operation_prompt_consistency_dangerous_command_scan_unchanged() -> None:
    task = _safe_task()
    task["acceptance_checks"] = ["gh pr merge 93"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert any(sv.POLICY_DANGEROUS_ACCEPTANCE_CHECK in e for e in errors)


# --- Task 6: active PR configurable ---------------------------------------


def test_active_pr_configurable() -> None:
    """collect_context must accept an explicit active_pr number other than
    93 without source changes — the PR number is not hardcoded.
    """
    def runner(args, timeout):
        if _api_path(list(args), "repos/") and args[2].endswith("/git/refs/heads/main"):
            return sc.CommandOutcome(0, json.dumps({"object": {"sha": MAIN_SHA}}), "", False)
        if _api_path(list(args), "repos/") and "/issues" in args[2]:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:2] == ["gh", "pr"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:3] == ["gh", "issue", "view"] and "90" in args:
            return sc.CommandOutcome(0, json.dumps({"number": 90, "title": "t", "body": "b"}), "", False)
        # Respond for PR #777 (NOT #93) to prove the number is configurable.
        if args[:3] == ["gh", "pr", "view"] and "777" in args:
            return sc.CommandOutcome(0, json.dumps({
                "number": 777, "title": "other PR", "isDraft": True, "state": "OPEN",
                "headRefName": "other-branch", "headRefOid": "b" * 40, "baseRefName": "main",
            }), "", False)
        if _api_path(list(args), "repos/") and "/check-runs" in args[2]:
            return sc.CommandOutcome(0, '{"total_count":0,"check_runs":[]}', "", False)
        if args[0] == "git":
            if "symbolic-ref" in args:
                return sc.CommandOutcome(0, "refs/remotes/origin/main", "", False)
            if "rev-parse" in args and "HEAD" in args:
                return sc.CommandOutcome(0, "b" * 40, "", False)
            if "rev-parse" in args:
                return sc.CommandOutcome(0, MAIN_SHA, "", False)
            if "branch" in args:
                return sc.CommandOutcome(0, "other-branch", "", False)
            if "status" in args:
                return sc.CommandOutcome(0, "", "", False)
            if "log" in args:
                return sc.CommandOutcome(0, "abcdef0 Title", "", False)
        return sc.CommandOutcome(0, "", "", False)

    context = sc.collect_context(REPO, goal_issue=90, active_pr=777, runner=runner)
    assert context["active_pr_number"] == 777
    assert context["pr_facts"]["number"] == 777
    assert context["pr_facts"]["title"] == "other PR"


def test_active_pr_derived_from_branch() -> None:
    """When active_pr is None, it is derived from the current branch via
    gh api pulls. Exactly one match is required.
    """
    def runner(args, timeout):
        if _api_path(list(args), "repos/") and args[2].endswith("/git/refs/heads/main"):
            return sc.CommandOutcome(0, json.dumps({"object": {"sha": MAIN_SHA}}), "", False)
        if _api_path(list(args), "repos/") and "/issues" in args[2]:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:2] == ["gh", "pr"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:3] == ["gh", "issue", "view"]:
            return sc.CommandOutcome(0, json.dumps({"number": 90, "title": "t", "body": "b"}), "", False)
        if args[:3] == ["gh", "pr", "view"] and "42" in args:
            return sc.CommandOutcome(0, json.dumps({
                "number": 42, "title": "derived", "isDraft": True, "state": "OPEN",
                "headRefName": "agent/codex-supervisor-foundation-v0",
                "headRefOid": "a" * 40, "baseRefName": "main",
            }), "", False)
        # gh api pulls (derive) — return exactly one PR.
        if _api_path(list(args), "repos/") and "/pulls" in args[2]:
            return sc.CommandOutcome(0, json.dumps([{"number": 42}]), "", False)
        if _api_path(list(args), "repos/") and "/check-runs" in args[2]:
            return sc.CommandOutcome(0, '{"total_count":0,"check_runs":[]}', "", False)
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

    context = sc.collect_context(REPO, goal_issue=90, active_pr=None, runner=runner)
    assert context["active_pr_number"] == 42


def test_active_pr_derive_zero_match_fail_closed() -> None:
    """Zero matching PRs for the current branch → ContextError (fail-closed)."""
    def runner(args, timeout):
        if _api_path(list(args), "repos/") and "/issues" in args[2]:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:2] == ["gh", "pr"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:3] == ["gh", "issue", "view"]:
            return sc.CommandOutcome(0, json.dumps({"number": 90, "title": "t", "body": "b"}), "", False)
        # gh api pulls (derive) — return zero PRs.
        if _api_path(list(args), "repos/") and "/pulls" in args[2]:
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
        sc.collect_context(REPO, goal_issue=90, active_pr=None, runner=runner)


def test_active_pr_derive_multiple_match_fail_closed() -> None:
    """Multiple matching PRs for the current branch → ContextError."""
    def runner(args, timeout):
        if _api_path(list(args), "repos/") and "/issues" in args[2]:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:2] == ["gh", "pr"] and "list" in args:
            return sc.CommandOutcome(0, "[]", "", False)
        if args[:3] == ["gh", "issue", "view"]:
            return sc.CommandOutcome(0, json.dumps({"number": 90, "title": "t", "body": "b"}), "", False)
        if _api_path(list(args), "repos/") and "/pulls" in args[2]:
            return sc.CommandOutcome(0, json.dumps([{"number": 41}, {"number": 42}]), "", False)
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
        sc.collect_context(REPO, goal_issue=90, active_pr=None, runner=runner)


# =========================================================================
# v0.4 exact transport, binding, completeness, and TOCTOU tests.
# =========================================================================


def _assert_explicit_get(args: list[str]) -> None:
    assert "--method" in args
    method_index = args.index("--method")
    assert args[method_index + 1] == "GET"


def test_every_parameterized_gh_api_read_uses_explicit_get() -> None:
    calls: list[list[str]] = []

    def runner(args, timeout):
        call = list(args)
        calls.append(call)
        if "/check-runs" in call[2]:
            return sc.CommandOutcome(0, '{"total_count":0,"check_runs":[]}', "", False)
        if call[2].endswith("/pulls"):
            return sc.CommandOutcome(0, '[{"number":93}]', "", False)
        return sc.CommandOutcome(0, "[]", "", False)

    assert sc._gh_open_issues(REPO, runner) == []
    assert sc._derive_active_pr(REPO, "agent/codex-supervisor-foundation-v0", runner) == 93
    assert sc._gh_check_runs(REPO, "a" * 40, runner) == []
    issues, error = sp.fetch_existing_issues(REPO, runner=runner)
    assert issues == [] and error is None

    parameterized_reads = [call for call in calls if "--field" in call or "-F" in call]
    assert len(parameterized_reads) == 4
    for call in parameterized_reads:
        assert call[:2] == ["gh", "api"]
        _assert_explicit_get(call)


def test_pr_head_mismatch_rejected_before_check_collection() -> None:
    calls: list[list[str]] = []

    def runner(args, timeout):
        calls.append(list(args))
        return sc.CommandOutcome(0, json.dumps({
            "number": 93,
            "title": "PR #93",
            "isDraft": True,
            "state": "OPEN",
            "headRefName": "agent/codex-supervisor-foundation-v0",
            "headRefOid": "b" * 40,
            "baseRefName": "main",
        }), "", False)

    with pytest.raises(sc.ContextError, match="does not match local HEAD"):
        sc._gh_pr_facts(REPO, 93, runner, exact_head="a" * 40)
    assert not any("/check-runs" in arg for call in calls for arg in call)


def test_github_main_mismatch_rejects_context() -> None:
    def runner(args, timeout):
        if args[:3] == ["git", "symbolic-ref", "--short"]:
            return sc.CommandOutcome(0, "refs/remotes/origin/main", "", False)
        if args[:2] == ["git", "rev-parse"]:
            return sc.CommandOutcome(0, MAIN_SHA, "", False)
        if _api_path(list(args), "repos/") and args[2].endswith("/git/refs/heads/main"):
            return sc.CommandOutcome(0, json.dumps({"object": {"sha": "b" * 40}}), "", False)
        return sc.CommandOutcome(0, "", "", False)

    with pytest.raises(sc.ContextError, match="does not match local origin/main"):
        sc.collect_context(REPO, goal_issue=90, active_pr=93, runner=runner)


def test_check_total_count_overflow_rejected() -> None:
    def runner(args, timeout):
        return sc.CommandOutcome(0, json.dumps({
            "total_count": sc.MAX_TOTAL_CHECK_RUNS + 1,
            "check_runs": [],
        }), "", False)

    with pytest.raises(sc.ContextError, match="exceeds safety cap"):
        sc._gh_check_runs(REPO, "a" * 40, runner)


def test_check_total_count_incomplete_rejected() -> None:
    def runner(args, timeout):
        return sc.CommandOutcome(0, json.dumps({
            "total_count": 2,
            "check_runs": [{"name": "one", "status": "completed", "conclusion": "success", "html_url": ""}],
        }), "", False)

    with pytest.raises(sc.ContextError, match="incomplete pagination"):
        sc._gh_check_runs(REPO, "a" * 40, runner)


def test_check_page_failure_rejected() -> None:
    runs = [
        {"name": f"check-{index}", "status": "completed", "conclusion": "success", "html_url": ""}
        for index in range(sc.PAGE_SIZE)
    ]

    def runner(args, timeout):
        page = _page_arg(list(args))
        if page == 1:
            return sc.CommandOutcome(0, json.dumps({"total_count": 101, "check_runs": runs}), "", False)
        return sc.CommandOutcome(1, "", "page failed", False)

    with pytest.raises(sc.ContextError, match="page 2 failed"):
        sc._gh_check_runs(REPO, "a" * 40, runner)


def test_malformed_check_run_rejected() -> None:
    def runner(args, timeout):
        return sc.CommandOutcome(0, json.dumps({
            "total_count": 1,
            "check_runs": [{"name": "", "status": "completed"}],
        }), "", False)

    with pytest.raises(sc.ContextError, match="malformed name"):
        sc._gh_check_runs(REPO, "a" * 40, runner)


def _make_update_plan_and_issue() -> tuple[dict, dict]:
    create_plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    issue = {
        "number": 5,
        "title": "owner title",
        "body": create_plan["marker"] + "\nowner preimage",
        "state": "OPEN",
    }
    update_plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[issue],
    )
    assert update_plan["action"] == sp.ACTION_UPDATE_ISSUE
    return dict(update_plan), issue


def _issue_write_calls(calls: list[list[str]]) -> list[list[str]]:
    return [call for call in calls if call[:3] in (["gh", "issue", "edit"], ["gh", "issue", "create"])]


def test_update_issue_closed_after_plan_zero_writes() -> None:
    plan, issue = _make_update_plan_and_issue()
    issue["state"] = "CLOSED"
    runner = _GuardRunner(issues_json=json.dumps([issue]))
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert result["reason"] == "toctou_target_not_open"
    assert _issue_write_calls(runner.calls) == []


@pytest.mark.parametrize("field", ["title", "body"])
def test_update_issue_edited_after_plan_zero_writes(field: str) -> None:
    plan, issue = _make_update_plan_and_issue()
    issue[field] += " concurrent owner edit"
    runner = _GuardRunner(issues_json=json.dumps([issue]))
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert result["reason"] == f"toctou_{field}_changed"
    assert _issue_write_calls(runner.calls) == []


def test_update_issue_second_marker_after_plan_zero_writes() -> None:
    plan, issue = _make_update_plan_and_issue()
    second_task = _safe_task()
    second_task["goal"] = "A distinct bounded goal"
    second = sp.plan_publication(
        audit_result=_safe_result(task=second_task), repository=REPO,
        main_sha=MAIN_SHA, existing_issues=[],
    )
    issue["body"] += "\n" + second["marker"]
    runner = _GuardRunner(issues_json=json.dumps([issue]))
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert result["reason"] == "toctou_marker_changed"
    assert _issue_write_calls(runner.calls) == []


def test_update_issue_duplicate_marker_after_plan_zero_writes() -> None:
    plan, issue = _make_update_plan_and_issue()
    duplicate = {"number": 6, "title": "duplicate", "body": plan["marker"], "state": "OPEN"}
    runner = _GuardRunner(issues_json=json.dumps([issue, duplicate]))
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is False
    assert result["reason"] == "toctou_duplicate_marker"
    assert _issue_write_calls(runner.calls) == []


def test_unchanged_open_issue_allows_one_bounded_update() -> None:
    plan, issue = _make_update_plan_and_issue()
    runner = _GuardRunner(issues_json=json.dumps([issue]))
    result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
    assert result["applied"] is True
    writes = _issue_write_calls(runner.calls)
    assert len(writes) == 1
    assert writes[0][:4] == ["gh", "issue", "edit", "5"]


# --- Task 7: single-machine publish lock ----------------------------------


def test_lock_contention_zero_writes() -> None:
    """If the publish lock is already held, zero writes occur."""
    plan = _make_create_plan()
    # Pre-acquire the lock with the same name so apply_plan's acquisition fails.
    shared_lock = sp.PublishLock(name="reverse-agent-supervisor-publish.lock")
    acquired_path = None
    try:
        with shared_lock:
            acquired_path = shared_lock.path
            runner = _GuardRunner()  # all guards pass.
            result = sp.apply_plan(plan, repository=REPO, expected_main_sha=MAIN_SHA, runner=runner, live=True)
            assert result["applied"] is False
            assert result["reason"] == sp.ERR_LOCK_BUSY
            write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
            assert write_calls == []
    finally:
        # The lock should still be held by shared_lock (released on exit).
        if acquired_path and not shared_lock._owned:
            # shared_lock.__exit__ already unlinked; ensure no leftover.
            import os as _os
            assert not _os.path.exists(acquired_path)


def test_lock_released_after_exception() -> None:
    """If an exception occurs while holding the lock, the lock is released
    in the finally block (the file is unlinked).
    """
    import os as _os
    lock = sp.PublishLock(name="reverse-agent-supervisor-publish-test-exception.lock")
    lock_path = None
    try:
        with lock:
            lock_path = lock.path
            assert _os.path.exists(lock_path)
            raise RuntimeError("simulated failure")
    except RuntimeError:
        pass
    # Lock file must be unlinked even after the exception.
    assert lock_path is not None
    assert not _os.path.exists(lock_path)


def test_lock_atomic_acquisition() -> None:
    """Two concurrent PublishLock instances with the same name: the second
    acquisition fails with LockBusyError (atomic O_EXCL).
    """
    import os as _os
    lock1 = sp.PublishLock(name="reverse-agent-supervisor-publish-test-atomic.lock")
    lock2 = sp.PublishLock(name="reverse-agent-supervisor-publish-test-atomic.lock")
    try:
        with lock1:
            with pytest.raises(sp.LockBusyError):
                with lock2:
                    pass
    finally:
        pass  # lock1.__exit__ unlinks the file.


def test_lock_not_in_repository() -> None:
    """The lock file must NOT be created inside the repository."""
    lock = sp.PublishLock(name="reverse-agent-supervisor-publish-test-location.lock")
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    try:
        with lock:
            assert lock.path is not None
            lock_path = pathlib.Path(lock.path).resolve()
            repo_root_resolved = repo_root.resolve()
            # lock_path must not be inside the repo.
            assert not str(lock_path).startswith(str(repo_root_resolved))
    finally:
        pass


# --- Task 8: volatile evidence not in tracking docs -----------------------


def test_no_hardcoded_head_or_run_id_in_hygiene_report() -> None:
    """The hygiene report must not hardcode exact Head SHAs or Actions run
    IDs as 'current facts' — those are volatile and expire on every push.
    Stable hygiene facts (branch counts, dispositions) are permitted.
    """
    report = pathlib.Path(__file__).resolve().parents[1] / "docs" / "repository-hygiene-report.md"
    text = report.read_text(encoding="utf-8")
    # The report may record the audited main SHA (stable for the round) but
    # must not present the implementation branch HEAD or CI run IDs as
    # current facts. Look for the volatile markers explicitly.
    # (The historical 'post-cleanup evidence' section is removed in v0.3.)
    assert "Current observed state" not in text
    assert "exact Head" not in text.lower()
