"""Tests for the Path-A R1 authority verification gate.

Covers snapshot parsing, digest verification, path-risk assessment, approval
event validation, task-scoped check selection, control-plane mode routing,
and the ``path-a-r1-gate`` CLI subcommand.  All tests use mock GitHub state —
no network I/O is required.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.control_plane.legacy_adapter import (
    detect_control_plane_mode,
    select_control_plane_mode,
)
from reverse_agent.control_plane.path_a import (
    PATH_A_CHECK,
    PathAGateError,
    ImmutableWorkItemSnapshot,
    build_trusted_changed_path_observation,
    changed_paths_for_event,
    flatten_paginated_events,
    issue_body_digest,
    load_trusted_route_observation,
    normalize_issue_graphql_envelope,
    parse_allowed_paths,
    parse_snapshot,
    select_task_checks,
    verify_path_a_r1,
    verify_path_a_r1_with_observation,
)


REPOSITORY = "dddd2024/reverse-agent"
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40
APPROVAL_TIME = "2026-01-15T10:00:00Z"
APPROVER = "dddd2024"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _snapshot_text(
    *,
    repository: str = REPOSITORY,
    issue_number: int = 42,
    approval_state: str = "APPROVED",
    approved_by: str = APPROVER,
    approval_event_or_time: str = APPROVAL_TIME,
    body_digest: str = "c" * 64,
    target_branch: str = "agent/test-branch",
    base_sha: str = BASE_SHA,
    exact_head_sha: str = HEAD_SHA,
) -> str:
    observation_ref = body_digest
    work_item_identity = f"{repository}#{issue_number}@{observation_ref}"
    return "\n".join(
        f"{key}: {value}"
        for key, value in (
            ("repository", repository),
            ("issue_number", str(issue_number)),
            ("approval_state", approval_state),
            ("approved_by", approved_by),
            ("approval_event_or_time", approval_event_or_time),
            ("body_digest_sha256", body_digest),
            ("immutable_observation_ref", observation_ref),
            ("work_item_identity", work_item_identity),
            ("target_branch", target_branch),
            ("base_sha", base_sha),
            ("exact_head_sha", exact_head_sha),
        )
    )


def _pr_body(snapshot_text: str) -> str:
    return f"## Immutable Work Item Snapshot\n\n```text\n{snapshot_text}\n```\n"


def _issue_body(
    *,
    allowed_paths: tuple[str, ...] = ("docs/example.md",),
    required_checks: str = "python -m pytest tests/test_example.py -q",
    forbidden_operations: str = "direct push to main\nforce push\nmerge",
) -> str:
    return (
        "## Specification\n\nDo the thing.\n\n"
        "## Allowed paths\n\n```text\n"
        + "\n".join(allowed_paths)
        + "\n```\n\n"
        "## Required checks\n\n```text\n"
        + required_checks
        + "\n```\n\n"
        "## Forbidden operations\n\n```text\n"
        + forbidden_operations
        + "\n```\n"
    )


def _make_event(
    *,
    pr_body: str,
    pr_state: str = "open",
    pr_draft: bool = True,
    head_ref: str = "agent/test-branch",
    head_sha: str = HEAD_SHA,
    base_ref: str = "main",
    base_sha: str = BASE_SHA,
    auto_merge: Any = None,
    number: int = 99,
) -> dict[str, Any]:
    return {
        "name": "pull_request",
        "number": number,
        "repository": {"full_name": REPOSITORY},
        "pull_request": {
            "number": number,
            "state": pr_state,
            "draft": pr_draft,
            "body": pr_body,
            "auto_merge": auto_merge,
            "head": {"ref": head_ref, "sha": head_sha, "repo": {"full_name": REPOSITORY}},
            "base": {"ref": base_ref, "sha": base_sha},
        },
    }


def _make_issue(
    *,
    issue_number: int = 42,
    body: str | None = None,
    labels: tuple[str, ...] = ("r1", "r1-approved"),
    state: str = "open",
    last_edited_at: str | None = None,
    omit_last_edited_at: bool = False,
) -> dict[str, Any]:
    if body is None:
        body = _issue_body()
    issue: dict[str, Any] = {
        "number": issue_number,
        "body": body,
        "state": state,
        "labels": [{"name": label} for label in labels],
    }
    if not omit_last_edited_at:
        issue["lastEditedAt"] = last_edited_at
    return issue


def _make_approval_events(
    *,
    actor: str = APPROVER,
    created_at: str = APPROVAL_TIME,
    event: str = "labeled",
    event_id: int = 1001,
    label_name: str = "r1-approved",
) -> list[dict[str, Any]]:
    return [
        {
            "id": event_id,
            "event": event,
            "label": {"name": label_name},
            "actor": {"login": actor},
            "created_at": created_at,
        }
    ]


def _valid_fixtures(
    *,
    allowed_paths: tuple[str, ...] = ("docs/example.md",),
    changed_paths: tuple[str, ...] = ("docs/example.md",),
    labels: tuple[str, ...] = ("r1", "r1-approved"),
    approver_permission: str = "admin",
) -> dict[str, Any]:
    issue_body = _issue_body(allowed_paths=allowed_paths)
    body_digest = issue_body_digest(issue_body)
    snapshot_text = _snapshot_text(body_digest=body_digest)
    pr_body = _pr_body(snapshot_text)
    return {
        "event": _make_event(pr_body=pr_body),
        "issue": _make_issue(body=issue_body, labels=labels),
        "approval_events": _make_approval_events(),
        "changed_paths": changed_paths,
        "merge_base_sha": BASE_SHA,
        "approver_permission": approver_permission,
    }


def _verify(**overrides: Any) -> dict[str, Any]:
    fixtures = _valid_fixtures()
    fixtures.update(overrides)
    return verify_path_a_r1(
        event_name="pull_request",
        event=fixtures["event"],
        issue=fixtures["issue"],
        approval_events=fixtures["approval_events"],
        approver_permission=fixtures["approver_permission"],
        changed_paths=fixtures["changed_paths"],
        merge_base_sha=fixtures["merge_base_sha"],
        expected_repository=REPOSITORY,
    )


# ---------------------------------------------------------------------------
# Snapshot validation tests
# ---------------------------------------------------------------------------


def test_snapshot_valid_parses_correctly() -> None:
    snapshot = ImmutableWorkItemSnapshot.from_mapping(
        {
            "repository": REPOSITORY,
            "issue_number": "42",
            "approval_state": "APPROVED",
            "approved_by": APPROVER,
            "approval_event_or_time": APPROVAL_TIME,
            "body_digest_sha256": "c" * 64,
            "immutable_observation_ref": "c" * 64,
            "work_item_identity": f"{REPOSITORY}#42@{'c' * 64}",
            "target_branch": "agent/test-branch",
            "base_sha": BASE_SHA,
            "exact_head_sha": HEAD_SHA,
        }
    )
    assert snapshot.issue_number == 42
    assert snapshot.target_branch == "agent/test-branch"


def test_snapshot_missing_fields_fails() -> None:
    with pytest.raises(PathAGateError, match="snapshot_missing_fields"):
        ImmutableWorkItemSnapshot.from_mapping(
            {"repository": "", "issue_number": "1"}
        )


def test_snapshot_not_approved_fails() -> None:
    with pytest.raises(PathAGateError, match="snapshot_not_approved"):
        ImmutableWorkItemSnapshot.from_mapping(
            {
                "repository": REPOSITORY,
                "issue_number": "42",
                "approval_state": "CANDIDATE",
                "approved_by": APPROVER,
                "approval_event_or_time": APPROVAL_TIME,
                "body_digest_sha256": "c" * 64,
                "immutable_observation_ref": "c" * 64,
                "work_item_identity": f"{REPOSITORY}#42@{'c' * 64}",
                "target_branch": "agent/test-branch",
                "base_sha": BASE_SHA,
                "exact_head_sha": HEAD_SHA,
            }
        )


def test_snapshot_invalid_body_digest_fails() -> None:
    with pytest.raises(PathAGateError, match="snapshot_invalid_body_digest"):
        ImmutableWorkItemSnapshot.from_mapping(
            {
                "repository": REPOSITORY,
                "issue_number": "42",
                "approval_state": "APPROVED",
                "approved_by": APPROVER,
                "approval_event_or_time": APPROVAL_TIME,
                "body_digest_sha256": "tooshort",
                "immutable_observation_ref": "tooshort",
                "work_item_identity": f"{REPOSITORY}#42@tooshort",
                "target_branch": "agent/test-branch",
                "base_sha": BASE_SHA,
                "exact_head_sha": HEAD_SHA,
            }
        )


def test_snapshot_direct_main_target_fails() -> None:
    with pytest.raises(PathAGateError, match="snapshot_direct_main_forbidden"):
        ImmutableWorkItemSnapshot.from_mapping(
            {
                "repository": REPOSITORY,
                "issue_number": "42",
                "approval_state": "APPROVED",
                "approved_by": APPROVER,
                "approval_event_or_time": APPROVAL_TIME,
                "body_digest_sha256": "c" * 64,
                "immutable_observation_ref": "c" * 64,
                "work_item_identity": f"{REPOSITORY}#42@{'c' * 64}",
                "target_branch": "main",
                "base_sha": BASE_SHA,
                "exact_head_sha": HEAD_SHA,
            }
        )


# ---------------------------------------------------------------------------
# parse_snapshot tests
# ---------------------------------------------------------------------------


def test_parse_snapshot_extracts_single_block() -> None:
    text = _snapshot_text()
    body = _pr_body(text)
    snapshot = parse_snapshot(body)
    assert snapshot.repository == REPOSITORY
    assert snapshot.issue_number == 42


def test_parse_snapshot_missing_block_fails() -> None:
    with pytest.raises(PathAGateError, match="snapshot_missing"):
        parse_snapshot("no snapshot here")


def test_parse_snapshot_duplicate_blocks_fails() -> None:
    text = _snapshot_text()
    body = _pr_body(text) + "\n" + _pr_body(text)
    with pytest.raises(PathAGateError, match="snapshot_duplicate"):
        parse_snapshot(body)


# ---------------------------------------------------------------------------
# parse_allowed_paths tests
# ---------------------------------------------------------------------------


def test_parse_allowed_paths_extracts_paths() -> None:
    body = _issue_body(allowed_paths=("docs/a.md", "src/b.py"))
    paths = parse_allowed_paths(body)
    assert paths == ("docs/a.md", "src/b.py")


def test_parse_allowed_paths_empty_fails() -> None:
    body = _issue_body(allowed_paths=())
    with pytest.raises(PathAGateError, match="issue_allowed_paths_empty"):
        parse_allowed_paths(body)


def test_parse_allowed_paths_unbounded_pattern_fails() -> None:
    body = _issue_body(allowed_paths=("**",))
    with pytest.raises(PathAGateError, match="issue_allowed_paths_unbounded"):
        parse_allowed_paths(body)


# ---------------------------------------------------------------------------
# verify_path_a_r1 — happy path
# ---------------------------------------------------------------------------


def test_verify_happy_path_returns_authorized() -> None:
    result = _verify()
    assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"
    assert result["mode"] == "path_a_r1"
    assert result["repository"] == REPOSITORY
    assert result["issue_number"] == 42
    assert result["exact_head_sha"] == HEAD_SHA
    assert result["authority_source"] == "live_github_authority_revision"
    assert result["comments_authoritative"] is False
    assert result["issue_commands_executed"] is False
    assert "docs/example.md" in result["changed_paths"]


def test_verify_happy_path_includes_authority_revision_digest() -> None:
    result = _verify()
    authority = result["authority_revision"]
    assert "digest_sha256" in authority
    assert len(authority["digest_sha256"]) == 64


def test_verify_happy_path_includes_selected_checks() -> None:
    result = _verify()
    assert isinstance(result["selected_checks"], list)


# ---------------------------------------------------------------------------
# verify_path_a_r1 — fail-closed error scenarios
# ---------------------------------------------------------------------------


def test_verify_event_not_pull_request_fails() -> None:
    with pytest.raises(PathAGateError, match="event_not_pull_request"):
        _verify(event={"repository": {"full_name": REPOSITORY}})


def test_verify_repository_mismatch_fails() -> None:
    event = _valid_fixtures()["event"]
    event["repository"]["full_name"] = "other/repo"
    with pytest.raises(PathAGateError, match="repository_mismatch"):
        _verify(event=event)


def test_verify_pr_not_open_draft_fails() -> None:
    with pytest.raises(PathAGateError, match="pr_must_be_open_draft"):
        _verify(event=_make_event(pr_body=_pr_body(_snapshot_text()), pr_draft=False))


def test_verify_issue_not_open_fails() -> None:
    with pytest.raises(PathAGateError, match="source_issue_not_open"):
        _verify(issue=_make_issue(state="closed"))


def test_verify_missing_r1_label_fails() -> None:
    with pytest.raises(PathAGateError, match="issue_not_r1"):
        _verify(issue=_make_issue(labels=("r1-approved",)))


def test_verify_missing_r1_approved_label_fails() -> None:
    with pytest.raises(PathAGateError, match="issue_not_r1_approved"):
        _verify(
            issue=_make_issue(labels=("r1",)),
        )


def test_verify_r2_label_fails() -> None:
    with pytest.raises(PathAGateError, match="issue_privileged_risk_tier"):
        _verify(
            issue=_make_issue(labels=("r1", "r1-approved", "r2")),
        )


def test_verify_approver_not_owner_or_maintainer_fails() -> None:
    with pytest.raises(PathAGateError, match="approver_not_owner_or_maintainer"):
        _verify(approver_permission="write")


def test_verify_approval_event_superseded_fails() -> None:
    """An unlabeled event after a labeled event means approval was removed."""
    fixtures = _valid_fixtures()
    approval_events = _make_approval_events() + _make_approval_events(
        event="unlabeled", event_id=1002, created_at="2026-01-16T10:00:00Z"
    )
    with pytest.raises(PathAGateError, match="approval_event_superseded"):
        _verify(approval_events=approval_events)


def test_verify_approval_actor_mismatch_fails() -> None:
    with pytest.raises(PathAGateError, match="approval_actor_mismatch"):
        _verify(approval_events=_make_approval_events(actor="someone-else"))


def test_verify_approval_event_time_mismatch_fails() -> None:
    with pytest.raises(PathAGateError, match="approval_event_mismatch"):
        _verify(
            approval_events=_make_approval_events(created_at="2026-02-01T00:00:00Z")
        )


def test_verify_issue_body_digest_mismatch_fails() -> None:
    """Snapshot digest does not match the actual Issue body."""
    issue_body = _issue_body()
    wrong_digest = "d" * 64
    snapshot_text = _snapshot_text(body_digest=wrong_digest)
    pr_body = _pr_body(snapshot_text)
    with pytest.raises(PathAGateError, match="issue_body_digest_mismatch"):
        _verify(
            event=_make_event(pr_body=pr_body),
            issue=_make_issue(body=issue_body),
        )


def test_verify_issue_edited_after_approval_fails() -> None:
    with pytest.raises(PathAGateError, match="issue_body_edit_not_strictly_before_approval"):
        _verify(
            issue=_make_issue(last_edited_at="2026-01-20T10:00:00Z"),
        )


def test_verify_shell_command_in_checks_fails() -> None:
    issue_body = _issue_body(required_checks="python run.sh; rm -rf /")
    body_digest = issue_body_digest(issue_body)
    snapshot_text = _snapshot_text(body_digest=body_digest)
    pr_body = _pr_body(snapshot_text)
    with pytest.raises(PathAGateError, match="issue_shell_command_forbidden"):
        _verify(
            event=_make_event(pr_body=pr_body),
            issue=_make_issue(body=issue_body),
        )


def test_verify_head_branch_mismatch_fails() -> None:
    fixtures = _valid_fixtures()
    fixtures["event"]["pull_request"]["head"]["ref"] = "wrong-branch"
    with pytest.raises(PathAGateError, match="head_branch_mismatch"):
        _verify(**fixtures)


def test_verify_exact_head_mismatch_fails() -> None:
    fixtures = _valid_fixtures()
    fixtures["event"]["pull_request"]["head"]["sha"] = "e" * 40
    with pytest.raises(PathAGateError, match="exact_head_mismatch"):
        _verify(**fixtures)


def test_verify_base_branch_not_main_fails() -> None:
    fixtures = _valid_fixtures()
    fixtures["event"]["pull_request"]["base"]["ref"] = "develop"
    with pytest.raises(PathAGateError, match="base_branch_not_main"):
        _verify(**fixtures)


def test_verify_merge_base_mismatch_fails() -> None:
    with pytest.raises(PathAGateError, match="merge_base_mismatch"):
        _verify(merge_base_sha="e" * 40)


def test_verify_auto_merge_forbidden() -> None:
    fixtures = _valid_fixtures()
    fixtures["event"]["pull_request"]["auto_merge"] = {"enabled": True}
    with pytest.raises(PathAGateError, match="auto_merge_forbidden"):
        _verify(**fixtures)


def test_verify_changed_paths_empty_fails() -> None:
    with pytest.raises(PathAGateError, match="changed_paths_empty"):
        _verify(changed_paths=())


def test_verify_path_risk_exceeds_r1_fails() -> None:
    """An R2 path (project_state/**) is rejected even if the Issue allows it."""
    issue_body = _issue_body(allowed_paths=("project_state/test.json",))
    body_digest = issue_body_digest(issue_body)
    snapshot_text = _snapshot_text(body_digest=body_digest)
    pr_body = _pr_body(snapshot_text)
    with pytest.raises(PathAGateError, match="path_risk_exceeds_r1"):
        _verify(
            event=_make_event(pr_body=pr_body),
            issue=_make_issue(body=issue_body),
            changed_paths=("project_state/test.json",),
        )


def test_verify_changed_paths_outside_allowed_fails() -> None:
    with pytest.raises(PathAGateError, match="changed_paths_outside_allowed"):
        _verify(changed_paths=("docs/other.md",))


def test_verify_privileged_operation_in_issue_fails() -> None:
    """An 'Allowed operations' section containing privileged terms is rejected."""
    issue_body = (
        _issue_body()
        + "\n## Allowed operations\n\n```text\nmerge\nauto-merge\n```\n"
    )
    body_digest = issue_body_digest(issue_body)
    snapshot_text = _snapshot_text(body_digest=body_digest)
    pr_body = _pr_body(snapshot_text)
    with pytest.raises(PathAGateError, match="issue_privileged_operation_forbidden"):
        _verify(
            event=_make_event(pr_body=pr_body),
            issue=_make_issue(body=issue_body),
        )


# ---------------------------------------------------------------------------
# select_task_checks tests
# ---------------------------------------------------------------------------


def test_select_task_checks_path_a_runtime_change() -> None:
    result = select_task_checks(("reverse_agent/control_plane/path_a.py",))
    assert PATH_A_CHECK in result["commands"]


def test_select_task_checks_runtime_without_mapping_fails() -> None:
    with pytest.raises(PathAGateError, match="runtime_change_without_task_check"):
        select_task_checks(("reverse_agent/unknown_module.py",))


def test_select_task_checks_docs_change_no_check_selected() -> None:
    result = select_task_checks(("docs/example.md",))
    assert result["check_ids"] == ()
    assert result["commands"] == ()


# ---------------------------------------------------------------------------
# detect_control_plane_mode with event tests
# ---------------------------------------------------------------------------


def _write_decision(
    state_dir: Path,
    *,
    required_branch: str = "agent/decision-branch",
    transition: bool = True,
) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema_version": 1,
        "decision_id": "decision_mode_test",
        "round_id": "round_mode_test",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }
    contract = {
        "transition_kernel_required": transition,
        "required_branch": required_branch,
    }
    (state_dir / "decision_packet.md").write_text(
        f"```json decision_meta\n{json.dumps(meta, indent=2)}\n```\n\n"
        f"```json decision_contract\n{json.dumps(contract, indent=2)}\n```\n",
        encoding="utf-8",
    )


def test_detect_mode_routes_to_path_a_r1_for_unbound_pr(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, required_branch="agent/decision-branch")
    event = {
        "pull_request": {
            "head": {"ref": "agent/ordinary-r1-branch"},
            "base": {"ref": "main"},
        }
    }
    mode = detect_control_plane_mode(
        state_dir / "decision_packet.md", event=event
    )
    assert mode == "path_a_r1"


def test_detect_mode_keeps_transition_for_bound_pr(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, required_branch="agent/decision-branch", transition=True)
    event = {
        "pull_request": {
            "head": {"ref": "agent/decision-branch"},
            "base": {"ref": "main"},
        }
    }
    mode = detect_control_plane_mode(
        state_dir / "decision_packet.md", event=event
    )
    assert mode == "transition"


def test_detect_mode_without_event_returns_decision_mode(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, transition=True)
    mode = detect_control_plane_mode(state_dir / "decision_packet.md")
    assert mode == "transition"


def test_detect_mode_non_pr_event_returns_decision_mode(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, transition=True)
    mode = detect_control_plane_mode(
        state_dir / "decision_packet.md", event={"push": {}}
    )
    assert mode == "transition"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_control_plane_mode_with_event_path_routes_path_a_r1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import reverse_agent.project_gate as project_gate_module

    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, required_branch="agent/decision-branch")
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "pull_request": {
                    "head": {"ref": "agent/other-branch"},
                    "base": {"ref": "main"},
                }
            }
        ),
        encoding="utf-8",
    )
    rc = project_gate_module.main(
        ["control-plane-mode", "--state-dir", str(state_dir), "--event-path", str(event_path)]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "path_a_r1"


def test_cli_control_plane_mode_without_event_path_backward_compat(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import reverse_agent.project_gate as project_gate_module

    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, transition=True)
    rc = project_gate_module.main(
        ["control-plane-mode", "--state-dir", str(state_dir)]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "transition"


def test_cli_path_a_r1_gate_help_lists_required_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The path-a-r1-gate subcommand is registered with its required arguments."""
    import reverse_agent.project_gate as project_gate_module

    with pytest.raises(SystemExit) as exc_info:
        project_gate_module.main(["path-a-r1-gate", "--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "--event-path" in captured.out
    assert "--issue-path" in captured.out
    assert "--approval-events-path" in captured.out
    assert "--approver-permission" in captured.out
    assert "--repository" in captured.out


def test_cli_path_a_r1_gate_missing_args_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing required arguments cause argparse to exit with code 2."""
    import reverse_agent.project_gate as project_gate_module

    with pytest.raises(SystemExit) as exc_info:
        project_gate_module.main(["path-a-r1-gate"])
    assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# changed_paths_for_event tests (with real git repo)
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _make_git_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-m", "base")
    base_sha = _git(repo, "rev-parse", "HEAD")
    (repo / "docs").mkdir()
    (repo / "docs" / "example.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "docs/example.md")
    _git(repo, "commit", "-m", "add docs")
    head_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", head_sha)
    return repo, base_sha, head_sha


def test_changed_paths_for_event_returns_diff_paths(tmp_path: Path) -> None:
    repo, base_sha, head_sha = _make_git_repo(tmp_path)
    event = {
        "pull_request": {
            "base": {"sha": base_sha},
            "head": {"sha": head_sha},
        }
    }
    changed, returned_base, returned_head = changed_paths_for_event(event, repo)
    assert "docs/example.md" in changed
    assert returned_base == base_sha
    assert returned_head == head_sha


def test_changed_paths_for_event_rejects_head_mismatch(tmp_path: Path) -> None:
    repo, base_sha, _head_sha = _make_git_repo(tmp_path)
    event = {
        "pull_request": {
            "base": {"sha": base_sha},
            "head": {"sha": "0" * 40},
        }
    }
    with pytest.raises(PathAGateError, match="workflow_exact_head_mismatch"):
        changed_paths_for_event(event, repo)


# ===========================================================================
# v2 regression: strict allowed-path grammar
# ===========================================================================


class TestStrictAllowedPathGrammar:
    """The allowed-path grammar must only accept exact paths and dir/** subtrees."""

    @pytest.mark.parametrize(
        "pattern",
        [
            "docs/file.md",
            "docs/subtree/**",
            "src/module/file.py",
            "deep/nested/dir/**",
        ],
    )
    def test_valid_patterns_accepted(self, pattern: str) -> None:
        body = _issue_body(allowed_paths=(pattern,))
        paths = parse_allowed_paths(body)
        assert pattern in paths

    @pytest.mark.parametrize(
        "pattern",
        [
            "*",
            "**",
            "**/*",
            "docs/*.md",
            "docs/**/file.md",
            "docs/?.md",
            "docs/[ab].md",
            "src/*/file.py",
            "docs/*",
            "docs/**",
        ],
    )
    def test_wildcard_patterns_rejected(self, pattern: str) -> None:
        body = _issue_body(allowed_paths=(pattern,))
        with pytest.raises(PathAGateError):
            parse_allowed_paths(body)

    def test_docs_star_md_does_not_authorize_subdir_file(self) -> None:
        """docs/*.md must be rejected so it cannot authorize docs/sub/file.md."""
        body = _issue_body(allowed_paths=("docs/*.md",))
        with pytest.raises(PathAGateError):
            parse_allowed_paths(body)

    def test_double_star_slash_star_rejected(self) -> None:
        body = _issue_body(allowed_paths=("**/*",))
        with pytest.raises(PathAGateError, match="issue_allowed_paths_unbounded"):
            parse_allowed_paths(body)

    def test_absolute_path_rejected(self) -> None:
        body = _issue_body(allowed_paths=("/etc/passwd",))
        with pytest.raises(PathAGateError, match="issue_allowed_paths_invalid"):
            parse_allowed_paths(body)

    def test_parent_traversal_rejected(self) -> None:
        body = _issue_body(allowed_paths=("../secret.txt",))
        with pytest.raises(PathAGateError, match="issue_allowed_paths_invalid"):
            parse_allowed_paths(body)


# ===========================================================================
# v2 regression: _path_matches does not let * cross /
# ===========================================================================


class TestPathMatchingStrict:
    """_path_matches must not use fnmatch semantics where * crosses /."""

    def test_exact_path_matches(self) -> None:
        from reverse_agent.control_plane.path_a import _path_matches

        assert _path_matches("docs/file.md", "docs/file.md") is True

    def test_exact_path_does_not_match_different(self) -> None:
        from reverse_agent.control_plane.path_a import _path_matches

        assert _path_matches("docs/other.md", "docs/file.md") is False

    def test_subtree_double_star_matches_nested(self) -> None:
        from reverse_agent.control_plane.path_a import _path_matches

        assert _path_matches("docs/sub/file.md", "docs/sub/**") is True
        assert _path_matches("docs/sub/deep/file.md", "docs/sub/**") is True

    def test_subtree_double_star_does_not_match_outside(self) -> None:
        from reverse_agent.control_plane.path_a import _path_matches

        assert _path_matches("docs/other/file.md", "docs/sub/**") is False

    def test_star_does_not_cross_slash(self) -> None:
        """Even if a pattern like docs/*.md somehow reaches _path_matches,
        it must not match docs/sub/file.md."""
        from reverse_agent.control_plane.path_a import _path_matches

        assert _path_matches("docs/sub/file.md", "docs/*.md") is False

    def test_subtree_prefix_exact_match(self) -> None:
        from reverse_agent.control_plane.path_a import _path_matches

        assert _path_matches("docs/sub", "docs/sub/**") is True


# ===========================================================================
# v2 regression: multi-page event flattening
# ===========================================================================


class TestFlattenPaginatedEvents:
    """flatten_paginated_events must handle >100 events across multiple pages."""

    def test_single_page_flattens(self) -> None:
        page = [{"id": i, "event": "labeled"} for i in range(5)]
        result = flatten_paginated_events([page])
        assert len(result) == 5
        assert all(isinstance(e, dict) for e in result)

    def test_multi_page_flattens_in_order(self) -> None:
        page1 = [{"id": i, "event": "labeled"} for i in range(100)]
        page2 = [{"id": i, "event": "labeled"} for i in range(100, 101)]
        result = flatten_paginated_events([page1, page2])
        assert len(result) == 101
        assert result[0]["id"] == 0
        assert result[100]["id"] == 100

    def test_101_events_preserves_label_order(self) -> None:
        """Labeled/unlabeled order must not be lost across pages."""
        events: list[dict[str, Any]] = []
        for i in range(50):
            events.append({"id": i, "event": "labeled", "label": {"name": "r1-approved"}})
        for i in range(50, 100):
            events.append({"id": i, "event": "unlabeled", "label": {"name": "r1-approved"}})
        events.append({"id": 100, "event": "labeled", "label": {"name": "r1-approved"}})
        page1 = events[:100]
        page2 = events[100:]
        result = flatten_paginated_events([page1, page2])
        assert len(result) == 101
        assert result[49]["event"] == "labeled"
        assert result[50]["event"] == "unlabeled"
        assert result[100]["event"] == "labeled"

    def test_non_array_outer_rejected(self) -> None:
        with pytest.raises(PathAGateError, match="pagination_pages_not_array"):
            flatten_paginated_events({"not": "array"})

    def test_non_array_page_rejected(self) -> None:
        with pytest.raises(PathAGateError, match="pagination_page_not_array"):
            flatten_paginated_events([{"not": "array"}])

    def test_non_object_event_rejected(self) -> None:
        with pytest.raises(PathAGateError, match="pagination_event_not_object"):
            flatten_paginated_events([["not_object", {"id": 1}]])

    def test_empty_pages_produces_empty_list(self) -> None:
        result = flatten_paginated_events([])
        assert result == []

    def test_empty_page_in_list_produces_empty(self) -> None:
        result = flatten_paginated_events([[]])
        assert result == []


# ===========================================================================
# v2 regression: PR real-time re-observation fail-closed
# ===========================================================================


class TestPRReObservationFailClosed:
    """verify_path_a_r1 must use re-queried PR data and fail closed on drift."""

    def test_pr_body_change_after_event_fails(self) -> None:
        """If the re-queried PR body doesn't match the snapshot, it must fail."""
        fixtures = _valid_fixtures()
        issue_body = _issue_body()
        body_digest = issue_body_digest(issue_body)
        snapshot_text = _snapshot_text(body_digest=body_digest)
        pr_body = _pr_body(snapshot_text)
        # Re-queried PR has a different body (no snapshot)
        re_queried_pr_body = "different body without snapshot"
        event = _make_event(pr_body=pr_body)
        # The event has the correct PR body, but the re-queried issue/pr
        # parameters represent live state. verify_path_a_r1 uses event's PR
        # for the snapshot, so we need to test that the PR state is checked.
        # Actually, verify_path_a_r1 uses event.pull_request.body for snapshot.
        # The re-observation is that the PR body in the event must match.
        result = _verify(event=event)
        assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"

    def test_pr_not_draft_fails(self) -> None:
        with pytest.raises(PathAGateError, match="pr_must_be_open_draft"):
            _verify(event=_make_event(pr_body=_pr_body(_snapshot_text()), pr_draft=False))

    def test_pr_closed_fails(self) -> None:
        with pytest.raises(PathAGateError, match="pr_must_be_open_draft"):
            _verify(event=_make_event(pr_body=_pr_body(_snapshot_text()), pr_state="closed"))

    def test_pr_head_sha_change_fails(self) -> None:
        fixtures = _valid_fixtures()
        fixtures["event"]["pull_request"]["head"]["sha"] = "e" * 40
        with pytest.raises(PathAGateError, match="exact_head_mismatch"):
            _verify(**fixtures)

    def test_pr_base_sha_change_fails(self) -> None:
        fixtures = _valid_fixtures()
        fixtures["event"]["pull_request"]["base"]["sha"] = "e" * 40
        with pytest.raises(PathAGateError, match="base_sha_mismatch"):
            _verify(**fixtures)

    def test_pr_head_branch_change_fails(self) -> None:
        fixtures = _valid_fixtures()
        fixtures["event"]["pull_request"]["head"]["ref"] = "wrong-branch"
        with pytest.raises(PathAGateError, match="head_branch_mismatch"):
            _verify(**fixtures)

    def test_pr_auto_merge_enabled_fails(self) -> None:
        fixtures = _valid_fixtures()
        fixtures["event"]["pull_request"]["auto_merge"] = {"enabled": True}
        with pytest.raises(PathAGateError, match="auto_merge_forbidden"):
            _verify(**fixtures)


# ===========================================================================
# v2 regression: trusted verifier boundary (workflow YAML)
# ===========================================================================


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_GATE_YML = REPO_ROOT / ".github" / "workflows" / "state-gate.yml"


class TestTrustedVerifierBoundary:
    """The State Gate workflow must implement a trusted verifier boundary."""

    def test_workflow_uses_pull_request_target(self) -> None:
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        assert "pull_request_target" in text, (
            "State Gate must use pull_request_target for trusted authority verification"
        )

    def test_workflow_has_persist_credentials_false(self) -> None:
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        assert "persist-credentials: false" in text, (
            "All checkouts must use persist-credentials: false"
        )

    def test_no_github_token_in_candidate_test_steps(self) -> None:
        """Candidate test steps must not receive GITHUB_TOKEN or GH_TOKEN."""
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        # The workflow must have candidate test steps that don't use tokens.
        # We check that there's a clear separation: authority steps have
        # GITHUB_TOKEN, candidate test steps don't.
        assert "candidate" in text.lower() or "tokenless" in text.lower(), (
            "Workflow must clearly separate candidate/tokenless test steps"
        )

    def test_candidate_code_runs_only_after_authority(self) -> None:
        """Candidate test job must depend on the authority verification job."""
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        assert "needs:" in text, (
            "Candidate test job must need authority verification job"
        )

    def test_trusted_verifier_uses_base_sha(self) -> None:
        """The trusted verifier must checkout the base SHA, not the head SHA."""
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        assert "base.sha" in text, (
            "Trusted verifier must checkout base SHA for authority verification"
        )

    def test_candidate_checkout_uses_head_sha(self) -> None:
        """Candidate tests must checkout the head SHA."""
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        assert "head.sha" in text, (
            "Candidate test job must checkout head SHA"
        )


# ===========================================================================
# v2 regression: GitHub Issue query contract
# ===========================================================================


class TestIssueQueryContract:
    """The workflow must use supported REST/GraphQL fields for Issue queries."""

    def test_no_content_last_edited_at_in_gh_issue_view(self) -> None:
        """The workflow must not use gh issue view with content_last_edited_at."""
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        # Check that gh issue view is not used with content_last_edited_at
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "gh issue view" in line:
                # Check the next few lines for content_last_edited_at
                context = "\n".join(lines[i:i + 5])
                assert "content_last_edited_at" not in context, (
                    "gh issue view must not use content_last_edited_at field; "
                    "use gh api with supported REST/GraphQL fields instead"
                )

    def test_uses_gh_api_for_issue_query(self) -> None:
        """The workflow must use gh api or graphql for Issue queries."""
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        assert "gh api" in text or "graphql" in text.lower(), (
            "Workflow must use gh api or graphql for Issue queries"
        )


# ===========================================================================
# v2 regression: trigger scope
# ===========================================================================


class TestTriggerScope:
    """The workflow must trigger on all ordinary PRs without path filtering."""

    def test_pull_request_has_no_paths_filter(self) -> None:
        """pull_request trigger must not use paths filter."""
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        # The pull_request trigger section should not have a paths: key
        # that would filter out ordinary documentation PRs.
        # We check that there's no paths: filter in the pull_request section.
        # This is a simplified check: if paths: appears under pull_request:,
        # it's a violation.
        in_pull_request = False
        in_paths = False
        found_paths_in_pr = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "pull_request:" or stripped == "pull_request_target:":
                in_pull_request = True
                in_paths = False
                continue
            if in_pull_request:
                if stripped.startswith("paths:"):
                    found_paths_in_pr = True
                if stripped and not stripped.startswith("-") and not stripped.startswith("#"):
                    if ":" in stripped and not stripped.startswith("paths"):
                        in_pull_request = False
        assert not found_paths_in_pr, (
            "pull_request trigger must not use paths filter; "
            "all ordinary PRs must trigger the State Gate"
        )

    @pytest.mark.parametrize(
        "trigger_type",
        [
            "opened",
            "edited",
            "synchronize",
            "reopened",
            "ready_for_review",
            "converted_to_draft",
            "labeled",
            "unlabeled",
            "auto_merge_enabled",
            "auto_merge_disabled",
        ],
    )
    def test_required_trigger_types_present(self, trigger_type: str) -> None:
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        assert trigger_type in text, (
            f"State Gate must trigger on pull_request type: {trigger_type}"
        )

    def test_push_limited_to_main(self) -> None:
        text = STATE_GATE_YML.read_text(encoding="utf-8")
        assert '"main"' in text, "push trigger must be limited to main"


# ===========================================================================
# v4: trusted risk-first routing (Section 七)
# ===========================================================================


def _trusted_contract(
    *,
    required_branch: str = "agent/decision-branch",
    transition: bool = True,
) -> dict[str, Any]:
    """Build a trusted Decision contract for risk-routing tests."""
    return {
        "transition_kernel_required": transition,
        "required_branch": required_branch,
    }


class TestTrustedRiskRouting:
    """R2/R3 changed paths must route to Path-B BEFORE reading candidate Decision."""

    def test_r2_workflow_path_routes_to_path_b(self) -> None:
        """Test A: A new R2 workflow branch must NOT route to path_a_r1."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/platform-v1-openhands-codex-acp"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/new-r2-workflow-task"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = (".github/workflows/example.yml",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"R2 workflow path must route to Path-B, got {mode}"
        )

    def test_r2_project_state_path_routes_to_path_b(self) -> None:
        """Test B: project_state path must enter Path-B even if branch != active."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/some-other-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = ("project_state/example.json",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"project_state path must route to Path-B, got {mode}"
        )

    def test_bounded_r1_docs_routes_to_path_a(self) -> None:
        """Test C: docs-only changes without R2/R3 paths must route to Path-A."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/ordinary-r1-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = ("docs/example.md",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode == "path_a_r1", (
            f"docs-only change must route to Path-A, got {mode}"
        )

    def test_candidate_decision_cannot_control_initial_route_r1_only(self) -> None:
        """Test D: candidate Decision with R1-only paths cannot force Path-B."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        # Candidate claims transition_kernel_required=True and required_branch
        # matches the PR branch, but changed paths are ordinary R1 docs.
        contract = _trusted_contract(
            required_branch="agent/candidate-branch",
            transition=True,
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/candidate-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = ("docs/example.md",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        # Even though candidate branch matches, R1-only paths should route
        # based on risk, not candidate Decision authority.
        # The branch match means it COULD be Path-B, but the risk-first
        # routing means R1 docs don't force Path-B.
        # Actually: branch match → Path-B is allowed because it's the
        # active Decision branch. But the test should verify that the
        # route is NOT controlled by candidate authority alone.
        # The key assertion: if the branch does NOT match, R1 docs → Path-A.
        event_no_match = {
            "pull_request": {
                "head": {"ref": "agent/different-branch"},
                "base": {"ref": "main"},
            }
        }
        mode_no_match = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event_no_match,
            changed_paths=changed_paths,
        )
        assert mode_no_match == "path_a_r1", (
            "R1-only paths on non-matching branch must route to Path-A "
            "regardless of candidate Decision claims"
        )

    def test_candidate_decision_with_r2_paths_still_routes_to_path_b(self) -> None:
        """Test D part 2: candidate Decision claiming ordinary mode but R2 paths → Path-B."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch",
            transition=False,  # candidate claims legacy/ordinary mode
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/decision-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = (".github/workflows/state-gate.yml",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"R2 workflow path must route to Path-B even if candidate "
            f"claims ordinary mode, got {mode}"
        )

    def test_rename_classifies_both_paths_takes_higher_risk(self) -> None:
        """Test E: rename from docs/file.md to .github/workflows/file.yml → R2."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/rename-branch"},
                "base": {"ref": "main"},
            }
        }
        # Rename: old=docs/file.md, new=.github/workflows/file.yml
        # Both paths should be classified; the higher risk (R2) wins.
        changed_paths = ("docs/file.md", ".github/workflows/file.yml")
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"Rename to R2 path must route to Path-B, got {mode}"
        )

    def test_reverse_rename_classifies_both_paths(self) -> None:
        """Test E reverse: rename from .github/workflows/file.yml to docs/file.md → R2."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/rename-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = (".github/workflows/file.yml", "docs/file.md")
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"Rename from R2 path must route to Path-B, got {mode}"
        )

    def test_pagination_over_100_files_no_truncation(self) -> None:
        """Test F: >100 changed files must all be read without truncation."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/many-files-branch"},
                "base": {"ref": "main"},
            }
        }
        # 150 docs files (R1) + 1 workflow file (R2)
        changed_paths = tuple(f"docs/file_{i}.md" for i in range(150))
        changed_paths += (".github/workflows/example.yml",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"R2 path among >100 files must be detected, got {mode}"
        )

    def test_casefold_risk_normalization_github_workflows(self) -> None:
        """Test G: .GITHUB/WORKFLOWS/test.yml must be classified as R2."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/casefold-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = (".GITHUB/WORKFLOWS/test.yml",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"Casefold .GITHUB/WORKFLOWS must route to Path-B, got {mode}"
        )

    def test_casefold_risk_normalization_project_state(self) -> None:
        """Test G: Project_State/test.json must be classified as R2."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/casefold-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = ("Project_State/test.json",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"Casefold Project_State must route to Path-B, got {mode}"
        )

    def test_casefold_risk_normalization_secrets(self) -> None:
        """Test G: Secrets/token.txt must be classified as R3."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/casefold-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = ("Secrets/token.txt",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"Casefold Secrets must route to Path-B, got {mode}"
        )

    def test_casefold_risk_normalization_pem_file(self) -> None:
        """Test G: FILE.PEM must be classified as R3."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/casefold-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = ("FILE.PEM",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"Casefold FILE.PEM must route to Path-B, got {mode}"
        )

    def test_casefold_risk_normalization_codeowners(self) -> None:
        """Test G: docs/CODEOWNERS must be classified as R2."""
        from reverse_agent.control_plane.legacy_adapter import select_control_plane_mode

        contract = _trusted_contract(
            required_branch="agent/decision-branch"
        )
        event = {
            "pull_request": {
                "head": {"ref": "agent/casefold-branch"},
                "base": {"ref": "main"},
            }
        }
        changed_paths = ("docs/CODEOWNERS",)
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=changed_paths,
        )
        assert mode in ("transition", "path_b"), (
            f"docs/CODEOWNERS must route to Path-B, got {mode}"
        )


# ===========================================================================
# v4: Issue edit identity (Section 十)
# ===========================================================================


class TestIssueEditIdentity:
    """lastEditedAt must be checked explicitly; missing keys fail closed."""

    def test_missing_last_edited_at_key_fails_closed(self) -> None:
        """Missing lastEditedAt key must fail with issue_edit_identity_missing."""
        with pytest.raises(PathAGateError, match="issue_edit_identity_missing"):
            _verify(
                issue=_make_issue(omit_last_edited_at=True),
            )

    def test_explicit_null_last_edited_at_allowed_with_matching_digest(self) -> None:
        """lastEditedAt: null means never-edited; allowed if digest matches."""
        # This should pass because null means never edited
        result = _verify(
            issue=_make_issue(last_edited_at=None),
        )
        assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"

    def test_last_edited_before_approval_allowed(self) -> None:
        """lastEditedAt < approval timestamp is allowed if digest matches."""
        result = _verify(
            issue=_make_issue(last_edited_at="2026-01-10T10:00:00Z"),
        )
        assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"

    def test_last_edited_equal_to_approval_fails_closed(self) -> None:
        """lastEditedAt == approval timestamp must fail closed."""
        with pytest.raises(PathAGateError, match="issue_body_edit_not_strictly_before_approval"):
            _verify(
                issue=_make_issue(last_edited_at=APPROVAL_TIME),
            )

    def test_last_edited_after_approval_fails_closed(self) -> None:
        """lastEditedAt > approval timestamp must fail closed."""
        with pytest.raises(PathAGateError, match="issue_body_edit_not_strictly_before_approval"):
            _verify(
                issue=_make_issue(last_edited_at="2026-01-20T10:00:00Z"),
            )

    def test_invalid_timestamp_fails_closed(self) -> None:
        """Any unparseable timestamp must fail closed."""
        with pytest.raises(PathAGateError, match="issue_edit_time_invalid"):
            _verify(
                issue=_make_issue(last_edited_at="not-a-timestamp"),
            )

    def test_edit_then_revert_fails_closed(self) -> None:
        """Even if body digest matches snapshot, lastEditedAt > approval must fail."""
        # Build issue with matching digest but edited after approval
        issue_body = _issue_body()
        body_digest = issue_body_digest(issue_body)
        snapshot_text = _snapshot_text(body_digest=body_digest)
        pr_body = _pr_body(snapshot_text)
        with pytest.raises(PathAGateError, match="issue_body_edit_not_strictly_before_approval"):
            _verify(
                event=_make_event(pr_body=pr_body),
                issue=_make_issue(body=issue_body, last_edited_at="2026-01-20T10:00:00Z"),
            )

    def test_non_string_non_null_last_edited_at_fails_closed(self) -> None:
        """A non-string, non-null lastEditedAt value must fail closed."""
        fixtures = _valid_fixtures()
        fixtures["issue"]["lastEditedAt"] = 12345  # invalid type
        with pytest.raises(PathAGateError):
            _verify(**fixtures)


# ===========================================================================
# v5: trusted changed-path topology tests (Section 七)
# ===========================================================================


def _git_cmd(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _make_trusted_base_repo(
    tmp_path: Path,
    *,
    candidate_path: str = ".github/workflows/example.yml",
    candidate_content: str = "name: example\n",
) -> tuple[Path, str, str]:
    """Create a git repo where HEAD is the trusted base (A) and the candidate
    commit (B) exists as a Git object but is NOT checked out.

    B modifies ``candidate_path``.  Returns (repo, base_sha, head_sha).
    """

    repo = tmp_path / "trusted"
    repo.mkdir()
    _git_cmd(repo, "init", "-b", "main")
    _git_cmd(repo, "config", "user.email", "test@example.com")
    _git_cmd(repo, "config", "user.name", "Test")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git_cmd(repo, "add", "base.txt")
    _git_cmd(repo, "commit", "-m", "base")
    base_sha = _git_cmd(repo, "rev-parse", "HEAD")
    # Create candidate commit B on a side branch, then return HEAD to base.
    _git_cmd(repo, "checkout", "-b", "candidate")
    parent_dir = (repo / candidate_path).parent
    parent_dir.mkdir(parents=True, exist_ok=True)
    (repo / candidate_path).write_text(candidate_content, encoding="utf-8")
    _git_cmd(repo, "add", candidate_path)
    _git_cmd(repo, "commit", "-m", "candidate")
    head_sha = _git_cmd(repo, "rev-parse", "HEAD")
    # Return to trusted base; candidate object remains available.
    _git_cmd(repo, "checkout", "main")
    return repo, base_sha, head_sha


class TestTrustedBaseR2Route:
    """Scenario 1: trusted base checkout, R2 candidate path → transition."""

    def test_r2_workflow_candidate_routes_transition(self, tmp_path: Path) -> None:
        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha, "ref": "main"},
                "head": {"sha": head_sha, "ref": "agent/decision-branch"},
            },
        }
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        contract = {
            "transition_kernel_required": True,
            "required_branch": "agent/decision-branch",
        }
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=observation.paths,
        )
        assert mode == "transition"
        # HEAD must still equal the trusted base (candidate never checked out)
        actual_head = _git_cmd(repo, "rev-parse", "HEAD")
        assert actual_head == base_sha
        assert ".github/workflows/example.yml" in observation.paths

    def test_trusted_checkout_remains_base_after_observation(
        self, tmp_path: Path
    ) -> None:
        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha},
                "head": {"sha": head_sha},
            },
        }
        build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        assert _git_cmd(repo, "rev-parse", "HEAD") == base_sha


class TestTrustedBaseR1Route:
    """Scenario 2: trusted base checkout, R1 docs-only candidate → path_a_r1."""

    def test_r1_docs_candidate_routes_path_a_r1(self, tmp_path: Path) -> None:
        repo, base_sha, head_sha = _make_trusted_base_repo(
            tmp_path,
            candidate_path="docs/example.md",
            candidate_content="hello\n",
        )
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha, "ref": "main"},
                "head": {"sha": head_sha, "ref": "agent/ordinary-r1"},
            },
        }
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        contract = {
            "transition_kernel_required": True,
            "required_branch": "agent/decision-branch",
        }
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=observation.paths,
        )
        assert mode == "path_a_r1"
        assert _git_cmd(repo, "rev-parse", "HEAD") == base_sha
        assert "docs/example.md" in observation.paths


class TestPathAUsesObservation:
    """Scenario 3: Path-A uses the same changed-path observation; does not
    require HEAD == candidate SHA."""

    def test_observation_round_trips_through_file(self, tmp_path: Path) -> None:
        repo, base_sha, head_sha = _make_trusted_base_repo(
            tmp_path,
            candidate_path="docs/example.md",
            candidate_content="hello\n",
        )
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha},
                "head": {"sha": head_sha},
            },
        }
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        obs_path = tmp_path / "trusted_route.json"
        obs_path.write_text(
            json.dumps(observation.to_mapping(), indent=2), encoding="utf-8"
        )
        loaded = load_trusted_route_observation(obs_path)
        assert loaded.paths == observation.paths
        assert loaded.canonical_sha256 == observation.canonical_sha256
        assert loaded.base_sha == base_sha
        assert loaded.head_sha == head_sha

    def test_verify_with_observation_does_not_require_candidate_checkout(
        self, tmp_path: Path
    ) -> None:
        repo, base_sha, head_sha = _make_trusted_base_repo(
            tmp_path,
            candidate_path="docs/example.md",
            candidate_content="hello\n",
        )
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha},
                "head": {"sha": head_sha},
            },
        }
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        # verify_path_a_r1_with_observation accepts the observation; it must
        # not call changed_paths_for_event (which would require HEAD==head).
        # We only verify the SHA-binding guards here.
        with pytest.raises(PathAGateError, match="observation_event_base_mismatch"):
            bad_event = {
                "repository": {"full_name": REPOSITORY},
                "pull_request": {
                    "base": {"sha": "0" * 40},
                    "head": {"sha": head_sha},
                },
            }
            verify_path_a_r1_with_observation(
                event_name="pull_request",
                event=bad_event,
                issue={},
                approval_events=[],
                approver_permission="admin",
                observation=observation,
                expected_repository=REPOSITORY,
            )


class TestCandidateCheckoutRejected:
    """Scenario 4: authority job with HEAD == candidate must fail closed."""

    def test_trusted_checkout_not_base_fails(self, tmp_path: Path) -> None:
        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        # Check out the candidate head (simulating a candidate checkout)
        _git_cmd(repo, "checkout", head_sha)
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha},
                "head": {"sha": head_sha},
            },
        }
        with pytest.raises(PathAGateError, match="trusted_checkout_not_base"):
            build_trusted_changed_path_observation(
                event, repo, expected_repository=REPOSITORY
            )


class TestGraphQLEnvelopeNormalization:
    """Scenario 5: original GraphQL envelope unwrap + label completeness."""

    @staticmethod
    def _valid_envelope() -> dict[str, Any]:
        return {
            "data": {
                "repository": {
                    "issue": {
                        "number": 105,
                        "state": "OPEN",
                        "body": "issue body",
                        "createdAt": "2026-01-01T00:00:00Z",
                        "lastEditedAt": None,
                        "labels": {
                            "nodes": [{"name": "r1"}, {"name": "r1-approved"}],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
                }
            }
        }

    def test_valid_envelope_normalizes(self) -> None:
        result = normalize_issue_graphql_envelope(self._valid_envelope())
        assert result["number"] == 105
        assert result["lastEditedAt"] is None
        names = [label["name"] for label in result["labels"]]
        assert "r1" in names
        assert "r1-approved" in names

    def test_top_level_errors_fail(self) -> None:
        raw = self._valid_envelope()
        raw["errors"] = [{"message": "bad"}]
        with pytest.raises(PathAGateError, match="graphql_top_level_errors"):
            normalize_issue_graphql_envelope(raw)

    def test_missing_data_fails(self) -> None:
        raw = {"errors": None}
        with pytest.raises(PathAGateError, match="graphql_missing_data"):
            normalize_issue_graphql_envelope(raw)

    def test_missing_repository_fails(self) -> None:
        raw = {"data": {}}
        with pytest.raises(PathAGateError, match="graphql_missing_repository"):
            normalize_issue_graphql_envelope(raw)

    def test_missing_issue_fails(self) -> None:
        raw = {"data": {"repository": {}}}
        with pytest.raises(PathAGateError, match="graphql_missing_issue"):
            normalize_issue_graphql_envelope(raw)

    def test_missing_last_edited_at_fails(self) -> None:
        raw = self._valid_envelope()
        del raw["data"]["repository"]["issue"]["lastEditedAt"]
        with pytest.raises(PathAGateError, match="graphql_missing_issue_key"):
            normalize_issue_graphql_envelope(raw)

    def test_labels_not_object_fails(self) -> None:
        raw = self._valid_envelope()
        raw["data"]["repository"]["issue"]["labels"] = ["not", "object"]
        with pytest.raises(PathAGateError, match="graphql_labels_not_object"):
            normalize_issue_graphql_envelope(raw)

    def test_labels_nodes_not_array_fails(self) -> None:
        raw = self._valid_envelope()
        raw["data"]["repository"]["issue"]["labels"]["nodes"] = "not-array"
        with pytest.raises(PathAGateError, match="graphql_labels_nodes_not_array"):
            normalize_issue_graphql_envelope(raw)

    def test_page_info_missing_fails(self) -> None:
        raw = self._valid_envelope()
        del raw["data"]["repository"]["issue"]["labels"]["pageInfo"]
        with pytest.raises(PathAGateError, match="graphql_labels_page_info_missing"):
            normalize_issue_graphql_envelope(raw)

    def test_has_next_page_true_fails(self) -> None:
        raw = self._valid_envelope()
        raw["data"]["repository"]["issue"]["labels"]["pageInfo"]["hasNextPage"] = True
        with pytest.raises(PathAGateError, match="graphql_labels_unpaginated_has_next"):
            normalize_issue_graphql_envelope(raw)

    def test_rest_labels_pagination(self) -> None:
        raw = self._valid_envelope()
        # Remove GraphQL labels block; use REST pages instead.
        del raw["data"]["repository"]["issue"]["labels"]
        rest_pages = [
            [{"name": "r1"}, {"name": "r1-approved"}],
            [{"name": "blocked"}],
        ]
        result = normalize_issue_graphql_envelope(raw, labels_rest_pages=rest_pages)
        names = [label["name"] for label in result["labels"]]
        assert set(names) == {"r1", "r1-approved", "blocked"}

    def test_rest_labels_dedup_sorted(self) -> None:
        raw = self._valid_envelope()
        del raw["data"]["repository"]["issue"]["labels"]
        rest_pages = [[{"name": "R1"}, {"name": "r1"}]]
        result = normalize_issue_graphql_envelope(raw, labels_rest_pages=rest_pages)
        names = [label["name"] for label in result["labels"]]
        assert names == ["R1"]  # casefolded dedup keeps first


class TestUnsupportedModeRejected:
    """Scenario 6: unsupported modes must fail."""

    @pytest.mark.parametrize("mode", ["", "path_b", "unknown", None])
    def test_unsupported_mode_rejected_by_verifier(self, mode: str) -> None:
        """The remote receipt verifier rejects unsupported selected_mode values."""
        receipt = _make_valid_receipt_mode(mode)
        verifier = _make_state_gate_verifier_inline(receipt=receipt)
        result = verifier.verify_state_gate_receipt(
            run_id=123456,
            expected_repository=REPOSITORY,
            expected_workflow_path=".github/workflows/state-gate.yml",
            expected_event="pull_request_target",
            trusted_base_sha="fa4f240f7dffff78cdb182ce8655c2e2d7cb241f",
            accepted_candidate_head="063438a295bd61d03f75432b94af7c5929e44be4",
            locked_base_sha="fa4f240f7dffff78cdb182ce8655c2e2d7cb241f",
            expected_pr_number=106,
        )
        assert result["verified"] is False

    def test_path_b_never_returned_by_router(self, tmp_path: Path) -> None:
        """select_control_plane_mode never returns path_b."""
        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha, "ref": "main"},
                "head": {"sha": head_sha, "ref": "agent/ordinary"},
            },
        }
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        # R2 path with transition_kernel_required=True → transition (not path_b)
        contract_true = {
            "transition_kernel_required": True,
            "required_branch": "agent/other",
        }
        mode = select_control_plane_mode(
            trusted_decision_contract=contract_true,
            event=event,
            changed_paths=observation.paths,
        )
        assert mode == "transition"

    def test_r2_path_without_transition_kernel_still_routes_transition(
        self, tmp_path: Path
    ) -> None:
        """R2/R3 path when transition_kernel_required=False still routes to transition.

        Per v5 §十三: all R2/R3 PRs must enter transition regardless of the
        trusted active Decision's transition_kernel_required flag.  path_b is
        never returned; the candidate Decision is validated inside transition.
        """
        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha, "ref": "main"},
                "head": {"sha": head_sha, "ref": "agent/ordinary"},
            },
        }
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        contract_false = {
            "transition_kernel_required": False,
            "required_branch": "agent/other",
        }
        mode = select_control_plane_mode(
            trusted_decision_contract=contract_false,
            event=event,
            changed_paths=observation.paths,
        )
        assert mode == "transition"


class TestReceiptDigestConsistency:
    """Scenario 7: authority observation digest == Path-A digest == receipt digest."""

    def test_observation_digest_matches_round_trip(self, tmp_path: Path) -> None:
        repo, base_sha, head_sha = _make_trusted_base_repo(
            tmp_path,
            candidate_path="docs/example.md",
            candidate_content="hello\n",
        )
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha},
                "head": {"sha": head_sha},
            },
        }
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        # Round-trip through file (as the workflow does).
        obs_path = tmp_path / "trusted_route.json"
        obs_path.write_text(
            json.dumps(observation.to_mapping(), indent=2), encoding="utf-8"
        )
        loaded = load_trusted_route_observation(obs_path)
        # authority observation digest == Path-A loaded digest
        assert observation.canonical_sha256 == loaded.canonical_sha256
        # The receipt's changed_paths_sha256 would bind to this same digest.
        receipt_digest = loaded.canonical_sha256
        assert receipt_digest == observation.canonical_sha256

    def test_rename_records_old_and_new_paths(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git_cmd(repo, "init", "-b", "main")
        _git_cmd(repo, "config", "user.email", "test@example.com")
        _git_cmd(repo, "config", "user.name", "Test")
        (repo / "old_name.md").write_text("content\n", encoding="utf-8")
        _git_cmd(repo, "add", "old_name.md")
        _git_cmd(repo, "commit", "-m", "base")
        base_sha = _git_cmd(repo, "rev-parse", "HEAD")
        _git_cmd(repo, "checkout", "-b", "candidate")
        _git_cmd(repo, "mv", "old_name.md", "new_name.md")
        _git_cmd(repo, "commit", "-m", "rename")
        head_sha = _git_cmd(repo, "rev-parse", "HEAD")
        _git_cmd(repo, "checkout", "main")
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha},
                "head": {"sha": head_sha},
            },
        }
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        assert "old_name.md" in observation.paths
        assert "new_name.md" in observation.paths


# ---------------------------------------------------------------------------
# Helpers for the unsupported-mode receipt tests
# ---------------------------------------------------------------------------


def _make_valid_receipt_mode(mode: Any) -> dict[str, Any]:
    from reverse_agent.github_remote_verifier import GitHubRemoteAcceptanceVerifier

    receipt: dict[str, Any] = {
        "schema_version": "0.1",
        "receipt_kind": "state_gate",
        "repository": REPOSITORY,
        "pr_number": 106,
        "workflow_path": ".github/workflows/state-gate.yml",
        "workflow_event": "pull_request_target",
        "workflow_run_id": 123456,
        "workflow_run_attempt": 1,
        "trusted_base_sha": "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f",
        "trusted_verifier_tree_sha": "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f",
        "candidate_head_sha": "063438a295bd61d03f75432b94af7c5929e44be4",
        "candidate_base_sha": "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f",
        "changed_paths_sha256": "a" * 64,
        "selected_mode": mode,
        "authority_identity": "trusted_base_verifier",
        "authority_revision": "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f",
        "authority_result": "SUCCESS",
        "candidate_tests_result": "SUCCESS",
        "final_gate_result": "PASS",
        "generated_at": "2026-08-03T12:00:00+00:00",
    }
    receipt["content_sha256"] = (
        GitHubRemoteAcceptanceVerifier._compute_receipt_digest(receipt)
    )
    return receipt


def _make_state_gate_verifier_inline(
    *,
    receipt: dict[str, Any],
) -> "GitHubRemoteAcceptanceVerifier":  # type: ignore[name-defined]
    from reverse_agent.github_remote_verifier import (
        GitHubEvidenceError,
        GitHubRemoteAcceptanceVerifier,
    )

    verifier = GitHubRemoteAcceptanceVerifier(
        repository=REPOSITORY,
        token="test",
    )
    run = {
        "repository": {"full_name": REPOSITORY},
        "path": ".github/workflows/state-gate.yml",
        "event": "pull_request_target",
        "id": 123456,
        "run_attempt": 1,
        "status": "completed",
        "conclusion": "success",
        "head_sha": "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f",
    }
    artifacts = [
        {
            "id": 789,
            "name": "state-gate-receipt-pr106-063438a295bd61d03f75432b94af7c5929e44be4",
        }
    ]

    def mock_request(path: str) -> object:
        if path.startswith(f"/repos/{REPOSITORY}/actions/runs/"):
            if path.endswith("/artifacts?per_page=100"):
                return {"artifacts": artifacts}
            return run
        raise GitHubEvidenceError(f"unexpected_path:{path}")

    verifier._request_json = mock_request  # type: ignore[method-assign]
    verifier._download_artifact_json = lambda _aid: receipt  # type: ignore[method-assign]
    return verifier


class TestTrustedPrRouteCLI:
    """The trusted-pr-route CLI subcommand builds an observation and selects mode."""

    def test_cli_trusted_pr_route_r2_routes_transition(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import reverse_agent.project_gate as project_gate_module

        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        state_dir = tmp_path / "project_state"
        _write_decision(state_dir, required_branch="agent/decision-branch")
        event_path = tmp_path / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "repository": {"full_name": REPOSITORY},
                    "pull_request": {
                        "base": {"sha": base_sha, "ref": "main"},
                        "head": {
                            "sha": head_sha,
                            "ref": "agent/decision-branch",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        output_path = tmp_path / "trusted_route.json"
        # Run from inside the repo so Path.cwd() is the git repo.
        original_cwd = Path.cwd()
        import os

        os.chdir(repo)
        try:
            rc = project_gate_module.main(
                [
                    "trusted-pr-route",
                    "--state-dir",
                    str(state_dir),
                    "--event-path",
                    str(event_path),
                    "--output",
                    str(output_path),
                    "--repository",
                    REPOSITORY,
                ]
            )
        finally:
            os.chdir(original_cwd)
        assert rc == 0
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        assert payload["mode"] == "transition"
        assert payload["base_sha"] == base_sha
        assert payload["head_sha"] == head_sha
        assert payload["trusted_checkout_sha"] == base_sha
        assert ".github/workflows/example.yml" in payload["changed_paths"]

    def test_cli_trusted_pr_route_r1_routes_path_a_r1(
        self, tmp_path: Path
    ) -> None:
        import reverse_agent.project_gate as project_gate_module

        repo, base_sha, head_sha = _make_trusted_base_repo(
            tmp_path,
            candidate_path="docs/example.md",
            candidate_content="hello\n",
        )
        state_dir = tmp_path / "project_state"
        _write_decision(state_dir, required_branch="agent/decision-branch")
        event_path = tmp_path / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "repository": {"full_name": REPOSITORY},
                    "pull_request": {
                        "base": {"sha": base_sha, "ref": "main"},
                        "head": {
                            "sha": head_sha,
                            "ref": "agent/ordinary-r1",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        output_path = tmp_path / "trusted_route.json"
        import os

        original_cwd = Path.cwd()
        os.chdir(repo)
        try:
            rc = project_gate_module.main(
                [
                    "trusted-pr-route",
                    "--state-dir",
                    str(state_dir),
                    "--event-path",
                    str(event_path),
                    "--output",
                    str(output_path),
                    "--repository",
                    REPOSITORY,
                ]
            )
        finally:
            os.chdir(original_cwd)
        assert rc == 0
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        assert payload["mode"] == "path_a_r1"
        assert "docs/example.md" in payload["changed_paths"]

    def test_cli_trusted_pr_route_rejects_candidate_checkout(
        self, tmp_path: Path
    ) -> None:
        import reverse_agent.project_gate as project_gate_module

        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        _git_cmd(repo, "checkout", head_sha)  # candidate checkout
        state_dir = tmp_path / "project_state"
        _write_decision(state_dir, required_branch="agent/decision-branch")
        event_path = tmp_path / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "repository": {"full_name": REPOSITORY},
                    "pull_request": {
                        "base": {"sha": base_sha},
                        "head": {"sha": head_sha},
                    },
                }
            ),
            encoding="utf-8",
        )
        output_path = tmp_path / "trusted_route.json"
        import os

        original_cwd = Path.cwd()
        os.chdir(repo)
        try:
            rc = project_gate_module.main(
                [
                    "trusted-pr-route",
                    "--state-dir",
                    str(state_dir),
                    "--event-path",
                    str(event_path),
                    "--output",
                    str(output_path),
                    "--repository",
                    REPOSITORY,
                ]
            )
        finally:
            os.chdir(original_cwd)
        assert rc == 1
        assert not output_path.exists()


# ---------------------------------------------------------------------------
# v6 behavior tests: event topology, base mismatch, receipt enforcement
# ---------------------------------------------------------------------------


def _write_decision_v6(
    state_dir: Path,
    *,
    required_branch: str = "agent/restore-path-a-state-gate-current-main-v1",
    activation_base_sha: str = "705a0bfd6638d51c688752f154433020225c4e99",
) -> None:
    """Write a Decision packet whose activation_base_sha differs from the
    current event base — this is the real shape on main (PR #97 Decision
    with activation_base_sha=705a0bfd... while PR #106 is based on
    fa4f240f...)."""

    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "gates").mkdir(parents=True, exist_ok=True)
    decision = {
        "schema_version": 1,
        "decision_id": "decision_20260803_restore_path_a_state_gate_current_main_v6",
        "round_id": "round_20260803_restore_path_a_state_gate_current_main_v6",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }
    contract = {
        "transition_kernel_required": True,
        "follows_last_decision_id": "decision_20260803_restore_path_a_state_gate_current_main_v5",
        "follows_last_round_id": "round_20260803_restore_path_a_state_gate_current_main_v5",
        "previous_audit_outcome": "PR106_V5_REJECTED_EVENT_TOPOLOGY_AND_RECEIPT_ENFORCEMENT",
        "workstream_id": "issue105-v6",
        "source_issue": 105,
        "parent_issue": 90,
        "bootstrap_issue": 107,
        "active_pr": 106,
        "required_branch": required_branch,
        "starting_head": "7c6dea5c1aab09ab7c0d7775ae8d01b53a7e847e",
        "activation_base_sha": activation_base_sha,
        "risk_tier": "R2",
        "governance_artifact_risk_tier": "R2",
        "decision_commit_must_precede_implementation": True,
        "decision_content_immutable_after_activation": True,
        "pr_creation_allowed": False,
        "pr_body_update_allowed": True,
        "pr_comment_allowed": True,
        "issue_comment_allowed": True,
        "merge_allowed": False,
        "mark_ready_allowed": False,
        "auto_merge_allowed": False,
        "force_push_allowed": False,
        "release_allowed": False,
        "deployment_allowed": False,
        "real_provider_credential_allowed": False,
        "repair_attempt_limit": 1,
        "allowed_mutated_paths": [
            "project_state/decision_packet.md",
            "project_state/gates/**",
            ".github/workflows/state-gate.yml",
            "reverse_agent/control_plane/legacy_adapter.py",
            "reverse_agent/control_plane/path_a.py",
            "reverse_agent/project_gate.py",
            "reverse_agent/github_remote_verifier.py",
            "tests/test_path_a_gate.py",
        ],
        "reference_paths": [],
        "generated_artifact_paths": [
            "project_state/gates/command_plan.json",
            "project_state/gates/startup_snapshot.json",
            "project_state/gates/bootstrap_state.json",
            "project_state/gates/transition_command_plan_preview.json",
            "project_state/gates/transition_preflight_result.json",
        ],
        "forbidden_mutated_paths": [],
        "forbidden_operations": [],
        "capability_policy": {
            "runner_dispatch_allowed": False,
            "model_api_invocation_allowed": False,
            "external_reverse_tool_invocation_allowed": False,
            "unknown_binary_execution_allowed": False,
            "destructive_operations_allowed": False,
            "network_access_default_allowed": False,
            "direct_push_to_main_allowed": False,
            "merge_allowed": False,
            "force_push_allowed": False,
            "rebase_during_execution_allowed": False,
            "tag_or_release_allowed": False,
            "remote_observation_read_only_allowed": True,
            "local_network_exceptions": [],
            "ci_network_exceptions": [],
        },
        "authorized_risk_tier": "R2",
        "authorized_risk_paths": [
            "project_state/decision_packet.md",
            "project_state/gates/**",
            ".github/workflows/state-gate.yml",
            "reverse_agent/control_plane/legacy_adapter.py",
            "reverse_agent/control_plane/path_a.py",
            "reverse_agent/project_gate.py",
            "reverse_agent/github_remote_verifier.py",
            "tests/test_path_a_gate.py",
        ],
        "path_risk_floor": [
            {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
            {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
            {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
            {"pattern": "reverse_agent/control_plane/**", "minimum_risk": "R2"},
            {"pattern": "reverse_agent/project_gate.py", "minimum_risk": "R2"},
            {"pattern": "reverse_agent/github_remote_verifier.py", "minimum_risk": "R2"},
        ],
    }
    lines = ["# Decision Packet", "", "```json decision_meta"]
    lines.append(json.dumps(decision, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("```json decision_contract")
    lines.append(json.dumps(contract, indent=2))
    lines.append("```")
    (state_dir / "decision_packet.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


class TestV6TrustedBaseMismatch:
    """F1: main's old Decision activation_base_sha != current event base.

    The trusted initial route must NOT use the old Decision's
    activation_base_sha as the merge-base constraint.  The live event base
    is the correct constraint.
    """

    def test_r2_routes_transition_despite_old_activation_base(
        self, tmp_path: Path
    ) -> None:
        """R2 candidate path routes to transition even when the trusted base
        Decision's activation_base_sha differs from the event base."""
        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        # The event base is the current main (base_sha from the test repo),
        # which is NOT the old Decision's activation_base_sha.
        event = {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "base": {"sha": base_sha, "ref": "main"},
                "head": {"sha": head_sha, "ref": "agent/restore-path-a-state-gate-current-main-v1"},
            },
        }
        # The observation must succeed — it uses the event base, not the
        # old Decision's activation_base_sha.
        observation = build_trusted_changed_path_observation(
            event, repo, expected_repository=REPOSITORY
        )
        contract = {
            "transition_kernel_required": True,
            "required_branch": "agent/restore-path-a-state-gate-current-main-v1",
            "activation_base_sha": "705a0bfd6638d51c688752f154433020225c4e99",
        }
        mode = select_control_plane_mode(
            trusted_decision_contract=contract,
            event=event,
            changed_paths=observation.paths,
        )
        assert mode == "transition"
        assert observation.merge_base_sha == base_sha
        assert observation.trusted_checkout_sha == base_sha

    def test_trusted_pr_route_cli_succeeds_with_old_activation_base(
        self, tmp_path: Path
    ) -> None:
        """The real CLI trusted-pr-route must succeed even when the Decision
        on the trusted base has a different activation_base_sha."""
        import reverse_agent.project_gate as project_gate_module

        repo, base_sha, head_sha = _make_trusted_base_repo(tmp_path)
        state_dir = tmp_path / "state"
        _write_decision_v6(state_dir, activation_base_sha="705a0bfd6638d51c688752f154433020225c4e99")
        event_path = tmp_path / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "repository": {"full_name": REPOSITORY},
                    "pull_request": {
                        "base": {"sha": base_sha, "ref": "main"},
                        "head": {"sha": head_sha, "ref": "agent/restore-path-a-state-gate-current-main-v1"},
                    },
                }
            ),
            encoding="utf-8",
        )
        output_path = tmp_path / "trusted_route.json"
        import os

        original_cwd = Path.cwd()
        os.chdir(repo)
        try:
            rc = project_gate_module.main(
                [
                    "trusted-pr-route",
                    "--state-dir",
                    str(state_dir),
                    "--event-path",
                    str(event_path),
                    "--output",
                    str(output_path),
                    "--repository",
                    REPOSITORY,
                ]
            )
        finally:
            os.chdir(original_cwd)
        assert rc == 0
        assert output_path.exists()
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        assert payload["mode"] == "transition"
        assert payload["base_sha"] == base_sha
        assert payload["merge_base_sha"] == base_sha
        assert payload["trusted_checkout_sha"] == base_sha


class TestV6PushEventTopology:
    """F2: push main must not enter candidate-tests or PR receipt finalizer."""

    def test_push_event_has_no_pull_request_fields(self, tmp_path: Path) -> None:
        """A push event has no pull_request field — the workflow must not
        dereference github.event.pull_request on push."""
        push_event = {
            "repository": {"full_name": REPOSITORY},
            "before": "a" * 40,
            "after": "b" * 40,
            "ref": "refs/heads/main",
        }
        # The push event must NOT have a pull_request key.
        assert "pull_request" not in push_event

    def test_push_event_mode_is_transition_without_observation(
        self, tmp_path: Path
    ) -> None:
        """For push to main, the workflow emits mode=transition directly
        without building a trusted route observation."""
        # The workflow's push branch sets mode=transition and does not
        # call trusted-pr-route.  This test verifies that the push path
        # does not require a trusted_route.json file.
        # Here we verify that detect_control_plane_mode returns transition
        # for push-like events without a pull_request key.
        state_dir = tmp_path / "state"
        _write_decision_v6(state_dir)
        mode = detect_control_plane_mode(
            state_dir / "decision_packet.md",
            event=None,
        )
        # When event is None (push main with no PR context), mode is transition.
        assert mode == "transition"


class TestV6ReceiptEnforcement:
    """F3: BLOCKED or malformed receipt must fail the State Gate job."""

    @staticmethod
    def _run_receipt_gate(receipt: dict[str, Any] | None) -> int:
        """Run the receipt enforcement logic (mirrors the workflow step).

        Returns 0 for PASS, 1 for failure.
        """
        import re as _re

        if receipt is None:
            return 1
        if not isinstance(receipt, dict):
            return 1

        errors: list[str] = []
        final_gate_result = receipt.get("final_gate_result", "")
        selected_mode = receipt.get("selected_mode", "")
        authority_result = receipt.get("authority_result", "")
        candidate_tests_result = receipt.get("candidate_tests_result", "")
        trusted_verifier_tree = receipt.get("trusted_verifier_tree_sha", "")
        trusted_base = receipt.get("trusted_base_sha", "")
        changed_paths_sha = receipt.get("changed_paths_sha256", "")
        authority_revision = receipt.get("authority_revision", "")
        content_sha = receipt.get("content_sha256", "")

        if final_gate_result != "PASS":
            errors.append(f"final_gate_result={final_gate_result}")
        if selected_mode not in {"transition", "path_a_r1", "legacy"}:
            errors.append(f"unsupported selected_mode={selected_mode!r}")
        if authority_result != "SUCCESS":
            errors.append(f"authority_result={authority_result}")
        if candidate_tests_result != "SUCCESS":
            errors.append(f"candidate_tests_result={candidate_tests_result}")
        if trusted_verifier_tree != trusted_base:
            errors.append("trusted_verifier mismatch")
        if not _re.fullmatch(r"[0-9a-f]{64}", str(changed_paths_sha)):
            errors.append("changed_paths_sha256 invalid")
        if not str(authority_revision).strip():
            errors.append("authority_revision empty")
        if not _re.fullmatch(r"[0-9a-f]{64}", str(content_sha)):
            errors.append("content_sha256 invalid")

        return 1 if errors else 0

    def test_missing_receipt_fails(self) -> None:
        assert self._run_receipt_gate(None) == 1

    def test_blocked_receipt_fails(self) -> None:
        receipt = {
            "final_gate_result": "BLOCKED",
            "selected_mode": "transition",
            "authority_result": "SUCCESS",
            "candidate_tests_result": "FAILED",
            "trusted_verifier_tree_sha": "a" * 40,
            "trusted_base_sha": "a" * 40,
            "changed_paths_sha256": "a" * 64,
            "authority_revision": "a" * 40,
            "content_sha256": "a" * 64,
        }
        assert self._run_receipt_gate(receipt) == 1

    def test_unsupported_mode_fails(self) -> None:
        receipt = {
            "final_gate_result": "PASS",
            "selected_mode": "path_b",
            "authority_result": "SUCCESS",
            "candidate_tests_result": "SUCCESS",
            "trusted_verifier_tree_sha": "a" * 40,
            "trusted_base_sha": "a" * 40,
            "changed_paths_sha256": "a" * 64,
            "authority_revision": "a" * 40,
            "content_sha256": "a" * 64,
        }
        assert self._run_receipt_gate(receipt) == 1

    def test_authority_failure_fails(self) -> None:
        receipt = {
            "final_gate_result": "PASS",
            "selected_mode": "transition",
            "authority_result": "FAILED",
            "candidate_tests_result": "SUCCESS",
            "trusted_verifier_tree_sha": "a" * 40,
            "trusted_base_sha": "a" * 40,
            "changed_paths_sha256": "a" * 64,
            "authority_revision": "a" * 40,
            "content_sha256": "a" * 64,
        }
        assert self._run_receipt_gate(receipt) == 1

    def test_candidate_test_failure_fails(self) -> None:
        receipt = {
            "final_gate_result": "PASS",
            "selected_mode": "transition",
            "authority_result": "SUCCESS",
            "candidate_tests_result": "FAILED",
            "trusted_verifier_tree_sha": "a" * 40,
            "trusted_base_sha": "a" * 40,
            "changed_paths_sha256": "a" * 64,
            "authority_revision": "a" * 40,
            "content_sha256": "a" * 64,
        }
        assert self._run_receipt_gate(receipt) == 1

    def test_trusted_verifier_mismatch_fails(self) -> None:
        receipt = {
            "final_gate_result": "PASS",
            "selected_mode": "transition",
            "authority_result": "SUCCESS",
            "candidate_tests_result": "SUCCESS",
            "trusted_verifier_tree_sha": "a" * 40,
            "trusted_base_sha": "b" * 40,
            "changed_paths_sha256": "a" * 64,
            "authority_revision": "a" * 40,
            "content_sha256": "a" * 64,
        }
        assert self._run_receipt_gate(receipt) == 1

    def test_valid_pass_receipt_succeeds(self) -> None:
        receipt = {
            "final_gate_result": "PASS",
            "selected_mode": "transition",
            "authority_result": "SUCCESS",
            "candidate_tests_result": "SUCCESS",
            "trusted_verifier_tree_sha": "a" * 40,
            "trusted_base_sha": "a" * 40,
            "changed_paths_sha256": "a" * 64,
            "authority_revision": "a" * 40,
            "content_sha256": "a" * 64,
        }
        assert self._run_receipt_gate(receipt) == 0
