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

from reverse_agent.control_plane.legacy_adapter import detect_control_plane_mode
from reverse_agent.control_plane.path_a import (
    PATH_A_CHECK,
    PathAGateError,
    ImmutableWorkItemSnapshot,
    changed_paths_for_event,
    issue_body_digest,
    parse_allowed_paths,
    parse_snapshot,
    select_task_checks,
    verify_path_a_r1,
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
) -> dict[str, Any]:
    if body is None:
        body = _issue_body()
    return {
        "number": issue_number,
        "body": body,
        "state": state,
        "labels": [{"name": label} for label in labels],
        "content_last_edited_at": last_edited_at,
    }


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
