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

REPO = "dddd2024/reverse-agent"
MAIN_SHA = "16526801bda2a816fc707342f903c1ad037de9bd"


def _safe_task() -> dict:
    return {
        "title": "Bounded next task",
        "goal": "Add a bounded deterministic check",
        "allowed_scope": ["reverse_agent/example.py", "tests/test_example.py"],
        "forbidden_scope": ["merge", "push main"],
        "acceptance_checks": ["python -m pytest tests/test_example.py -q"],
        "execution_prompt": "Implement the bounded check using only the standard library.",
    }


def _safe_result(status: str = "continue", task: dict | None = None) -> dict:
    return {
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


def test_merge_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = ["merge pull request"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_MERGE_FORBIDDEN in errors


def test_auto_merge_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = ["enable auto-merge on PR"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_MERGE_FORBIDDEN in errors


def test_push_main_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = ["push to main"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_MAIN_PUSH_FORBIDDEN in errors


def test_release_rejected() -> None:
    task = _safe_task()
    task["execution_prompt"] = "Create a release for the project"
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_RELEASE_FORBIDDEN in errors


def test_deploy_rejected() -> None:
    task = _safe_task()
    task["execution_prompt"] = "Run deployment to production"
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_DEPLOYMENT_FORBIDDEN in errors


def test_credential_access_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = ["read credentials from secrets"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_CREDENTIAL_ACCESS_FORBIDDEN in errors


def test_unrelated_issue_mutation_rejected() -> None:
    task = _safe_task()
    task["allowed_scope"] = ["close unrelated issue"]
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_UNRELATED_MUTATION_FORBIDDEN in errors


def test_unrelated_pr_mutation_rejected() -> None:
    task = _safe_task()
    task["execution_prompt"] = "modify unrelated PR description"
    ok, errors, _ = sv.validate_audit_result(_safe_result(task=task), expected_repository=REPO, expected_main_sha=MAIN_SHA)
    assert not ok
    assert sv.POLICY_UNRELATED_MUTATION_FORBIDDEN in errors


# --- idempotency / marker stability ---------------------------------------


def test_equivalent_inputs_produce_same_marker() -> None:
    task = _safe_task()
    k1 = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        acceptance_checks=task["acceptance_checks"],
    )
    # Same goal, acceptance checks in different order, extra whitespace.
    k2 = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION,
        goal="  Add a bounded   deterministic check  ",
        acceptance_checks=list(reversed(task["acceptance_checks"])) + ["python -m pytest tests/test_example.py -q"],
    )
    assert k1 == k2
    assert len(k1) == 64


def test_material_change_changes_marker() -> None:
    task = _safe_task()
    base = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        acceptance_checks=task["acceptance_checks"],
    )
    different_goal = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal="A different bounded goal",
        acceptance_checks=task["acceptance_checks"],
    )
    different_sha = sv.compute_cycle_key(
        repository=REPO, main_sha="0" * 40, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        acceptance_checks=task["acceptance_checks"],
    )
    different_checks = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal=task["goal"],
        acceptance_checks=["a different deterministic check"],
    )
    assert base != different_goal
    assert base != different_sha
    assert base != different_checks


def test_marker_round_trip() -> None:
    key = sv.compute_cycle_key(
        repository=REPO, main_sha=MAIN_SHA, schema_version=sv.SCHEMA_VERSION,
        policy_version=sv.POLICY_VERSION, goal="g", acceptance_checks=["c"],
    )
    marker = sv.make_marker(key)
    assert sv.find_marker_key(marker) == key
    assert sv.find_marker_key("no marker here") is None


# --- publication planner ---------------------------------------------------


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
    existing = [{"number": 42, "title": first["title"], "body": first["body"]}]
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
    # Same marker (same goal + checks) but body altered by a title change.
    existing = [{"number": 7, "title": "Old title", "body": first["body"] + "\nextra human note"}]
    second = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert second["action"] == sp.ACTION_UPDATE_ISSUE
    assert second["target_issue"] == 7
    assert second["idempotency_key"] == first["idempotency_key"]


def test_duplicate_run_no_duplicate_create() -> None:
    first = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=[],
    )
    # Second run sees the first issue (with marker) -> never creates again.
    existing = [{"number": 100, "title": first["title"], "body": first["body"]}]
    second = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=existing,
    )
    assert second["action"] in (sp.ACTION_NO_OP, sp.ACTION_UPDATE_ISSUE)
    assert second["action"] != sp.ACTION_CREATE_ISSUE


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


# --- dry-run zero writes ---------------------------------------------------


class _RecordingRunner:
    """Records calls; simulates gh without network."""

    def __init__(self, issues_json: str = "[]") -> None:
        self.issues_json = issues_json
        self.calls: list[list[str]] = []

    def __call__(self, args, timeout):
        self.calls.append(list(args))
        from supervisor_context import CommandOutcome

        if args[:2] == ["gh", "issue"] and "list" in args:
            return CommandOutcome(0, self.issues_json, "", False)
        return CommandOutcome(0, "", "", False)


def test_dry_run_performs_zero_writes() -> None:
    runner = _RecordingRunner(issues_json="[]")
    issues = sp.fetch_existing_issues(REPO, runner=runner)
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=issues,
    )
    assert plan["action"] == sp.ACTION_CREATE_ISSUE
    # apply_plan in dry-run must not perform any write.
    result = sp.apply_plan(plan, repository=REPO, runner=runner, live=False)
    assert result["applied"] is False
    # No `gh issue create` / `gh issue edit` call was made.
    write_calls = [c for c in runner.calls if "create" in c or "edit" in c]
    assert write_calls == []


def test_live_create_calls_gh_issue_create() -> None:
    runner = _RecordingRunner(issues_json="[]")
    issues = sp.fetch_existing_issues(REPO, runner=runner)
    plan = sp.plan_publication(
        audit_result=_safe_result(), repository=REPO, main_sha=MAIN_SHA,
        existing_issues=issues,
    )
    result = sp.apply_plan(plan, repository=REPO, runner=runner, live=True)
    assert result["applied"] is True
    assert any("create" in c for c in runner.calls)


# --- context bounds and safety --------------------------------------------


def test_context_bounds_issues_and_commits() -> None:
    from supervisor_context import MAX_ISSUES, MAX_PRS, MAX_COMMITS

    assert MAX_ISSUES == 50
    assert MAX_PRS == 50
    assert MAX_COMMITS == 50


def test_context_output_has_no_env_or_credentials() -> None:
    # The context collector only reads git/gh JSON; it never reads os.environ.
    # Verify the module does not import or expose environment data.
    import supervisor_context as sc

    src = pathlib.Path(sc.__file__).read_text(encoding="utf-8")
    assert "os.environ" not in src
    assert "API_KEY" not in src
    assert "GITHUB_TOKEN" not in src


def test_git_and_gh_args_are_bounded_and_explicit() -> None:
    # No shell=True, no wildcard expansion; args are explicit lists.
    import supervisor_context as sc

    runner_calls: list[list[str]] = []

    def fake_runner(args, timeout):
        runner_calls.append(list(args))
        return sc.CommandOutcome(0, "", "", False)

    sc.collect_context(REPO, runner=fake_runner)
    for call in runner_calls:
        assert call[0] in ("git", "gh")
        # No shell metacharacters in any arg.
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
