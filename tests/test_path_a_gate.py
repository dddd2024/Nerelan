from __future__ import annotations

import json
from pathlib import Path

import pytest

from reverse_agent.control_plane.legacy_adapter import detect_control_plane_mode
from reverse_agent.control_plane.path_a import (
    BASE_PLATFORM_CHECK,
    PATH_A_CHECK,
    PathAGateError,
    TaskCheck,
    _collect_paginated_list,
    _paths_from_api_file_entries,
    changed_paths_for_event,
    execute_task_checks,
    issue_body_digest,
    parse_snapshot,
    select_task_checks,
    verify_path_a_r1,
)


REPOSITORY = "dddd2024/reverse-agent"
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40
APPROVAL_TIME = "2026-07-26T10:32:41Z"


def _issue_body(
    *,
    allowed_paths: str = "reverse_agent/control_plane/**\ntests/test_path_a_gate.py",
    required_checks: str = "python -m pytest tests/test_path_a_gate.py -q\ngit diff --check",
    extra: str = "",
) -> str:
    return f"""# Approved R1 task

## Allowed paths

```text
{allowed_paths}
```

## Required checks

```text
{required_checks}
```

## Forbidden operations

```text
direct push to main
force push
rebase
squash
merge or mark-ready
auto-merge
tag or release
```

{extra}
"""


def _snapshot(
    body: str,
    *,
    repository: str = REPOSITORY,
    issue_number: int = 46,
    branch: str = "codex/base-platform-m1-spec-policy-core-v1",
    base_sha: str = BASE_SHA,
    head_sha: str = HEAD_SHA,
) -> str:
    digest = issue_body_digest(body)
    return f"""```text
repository: {repository}
issue_number: {issue_number}
approval_state: APPROVED
approved_by: dddd2024
approval_event_or_time: {APPROVAL_TIME}
body_digest_sha256: {digest}
immutable_observation_ref: {digest}
work_item_identity: {repository}#{issue_number}@{digest}
target_branch: {branch}
base_sha: {base_sha}
exact_head_sha: {head_sha}
```"""


def _fixture(
    *,
    issue_body: str | None = None,
    pr_body: str | None = None,
    changed_paths: tuple[str, ...] = ("reverse_agent/control_plane/path_a.py",),
) -> dict:
    body = issue_body if issue_body is not None else _issue_body()
    snapshot_body = pr_body if pr_body is not None else _snapshot(body)
    return {
        "event_name": "pull_request",
        "event": {
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "state": "open",
                "draft": True,
                "body": snapshot_body,
                "head": {
                    "ref": "codex/base-platform-m1-spec-policy-core-v1",
                    "sha": HEAD_SHA,
                },
                "base": {"ref": "main", "sha": BASE_SHA},
                "auto_merge": None,
            },
        },
        "issue": {
            "number": 46,
            "state": "open",
            "body": body,
            "labels": [{"name": "r1"}, {"name": "r1-approved"}],
        },
        "approval_events": [
            {
                "event": "labeled",
                "id": 1,
                "label": {"name": "r1-approved"},
                "actor": {"login": "dddd2024"},
                "created_at": APPROVAL_TIME,
            }
        ],
        "approver_permission": "admin",
        "changed_paths": changed_paths,
        "merge_base_sha": BASE_SHA,
        "expected_repository": REPOSITORY,
    }


def _verify(**overrides):
    fixture = _fixture()
    fixture.update(overrides)
    return verify_path_a_r1(**fixture)


def _write_decision(path: Path, *, transition: bool, branch: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "```json decision_meta\n"
        + json.dumps(
            {
                "decision_id": "decision_test",
                "round_id": "round_test",
                "status": "APPROVED",
                "mainline": "engineering_branch",
                "skill_profiles": ["reverse-agent-iteration@v2"],
            }
        )
        + "\n```\n\n```json decision_contract\n"
        + json.dumps(
            {
                "transition_kernel_required": transition,
                "required_branch": branch,
            }
        )
        + "\n```\n",
        encoding="utf-8",
    )


def _pr_event(branch: str, body: str = "") -> dict:
    return {"pull_request": {"head": {"ref": branch}, "body": body}}


def test_valid_r1_fixture_selects_path_a_and_passes(tmp_path: Path) -> None:
    decision = tmp_path / "project_state" / "decision_packet.md"
    _write_decision(decision, transition=True, branch="codex/transition-v1")
    assert detect_control_plane_mode(
        decision,
        event=_pr_event("codex/base-platform-m1-spec-policy-core-v1"),
    ) == "path_a_r1"

    result = _verify()
    assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"
    assert result["mode"] == "path_a_r1"
    assert result["issue_commands_executed"] is False
    assert result["comments_authoritative"] is False
    assert result["selected_checks"] == [PATH_A_CHECK]


@pytest.mark.parametrize(
    ("transition", "branch", "expected"),
    [
        (True, "codex/transition-v1", "transition"),
        (False, "codex/legacy-v1", "legacy"),
    ],
)
def test_decision_bound_pr_selects_exactly_one_existing_mode(
    tmp_path: Path,
    transition: bool,
    branch: str,
    expected: str,
) -> None:
    decision = tmp_path / "decision_packet.md"
    _write_decision(decision, transition=transition, branch=branch)
    mode = detect_control_plane_mode(decision, event=_pr_event(branch))
    assert mode == expected
    assert [mode == candidate for candidate in ("path_a_r1", "transition", "legacy")].count(True) == 1


def test_invalid_path_a_data_never_falls_back(tmp_path: Path) -> None:
    decision = tmp_path / "decision_packet.md"
    _write_decision(decision, transition=True, branch="codex/transition-v1")
    event = _pr_event("codex/ordinary-r1", body="no snapshot")
    assert detect_control_plane_mode(decision, event=event) == "path_a_r1"
    with pytest.raises(PathAGateError, match="snapshot_missing"):
        _verify(event={**_fixture()["event"], "pull_request": {**_fixture()["event"]["pull_request"], "body": ""}})


@pytest.mark.parametrize(
    ("pr_body", "code"),
    [
        ("", "snapshot_missing"),
        ("placeholder", "snapshot_missing"),
    ],
)
def test_snapshot_missing_is_rejected(pr_body: str, code: str) -> None:
    with pytest.raises(PathAGateError, match=code):
        verify_path_a_r1(**_fixture(pr_body=pr_body))


def test_duplicate_snapshot_is_rejected() -> None:
    body = _issue_body()
    snapshot = _snapshot(body)
    with pytest.raises(PathAGateError, match="snapshot_duplicate"):
        parse_snapshot(snapshot + "\n\n" + snapshot)


def test_malformed_or_duplicate_snapshot_field_is_rejected() -> None:
    body = _issue_body()
    malformed = _snapshot(body).replace(
        f"issue_number: 46",
        "issue_number: 46\nissue_number: 47",
    )
    with pytest.raises(PathAGateError, match="snapshot_duplicate_field"):
        parse_snapshot(malformed)


def test_issue_without_r1_approved_is_rejected() -> None:
    fixture = _fixture()
    fixture["issue"]["labels"] = [{"name": "r1"}]
    with pytest.raises(PathAGateError, match="issue_not_r1_approved"):
        verify_path_a_r1(**fixture)


def test_issue_requires_r1_and_rejects_r2_or_r3() -> None:
    fixture = _fixture()
    fixture["issue"]["labels"] = [{"name": "r1-approved"}]
    with pytest.raises(PathAGateError, match="issue_not_r1"):
        verify_path_a_r1(**fixture)

    for tier in ("r2", "r3"):
        fixture = _fixture()
        fixture["issue"]["labels"].append({"name": tier})
        with pytest.raises(PathAGateError, match="issue_privileged_risk_tier"):
            verify_path_a_r1(**fixture)


def test_issue_body_change_after_approval_is_rejected() -> None:
    approved_body = _issue_body()
    changed_body = approved_body + "\nmaterial edit\n"
    with pytest.raises(PathAGateError, match="issue_body_digest_mismatch"):
        verify_path_a_r1(**_fixture(issue_body=changed_body, pr_body=_snapshot(approved_body)))


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("repository", "repository_mismatch"),
        ("snapshot_repository", "snapshot_repository_mismatch"),
        ("issue", "snapshot_issue_mismatch"),
        ("branch", "head_branch_mismatch"),
        ("base", "base_sha_mismatch"),
        ("merge_base", "merge_base_mismatch"),
        ("head", "exact_head_mismatch"),
    ],
)
def test_repository_issue_branch_base_and_head_mismatches_are_rejected(
    mutation: str,
    code: str,
) -> None:
    fixture = _fixture()
    if mutation == "repository":
        fixture["event"]["repository"]["full_name"] = "other/repo"
    elif mutation == "snapshot_repository":
        body = fixture["issue"]["body"]
        fixture["event"]["pull_request"]["body"] = _snapshot(body, repository="other/repo")
    elif mutation == "issue":
        fixture["issue"]["number"] = 47
    elif mutation == "branch":
        fixture["event"]["pull_request"]["head"]["ref"] = "codex/wrong"
    elif mutation == "base":
        fixture["event"]["pull_request"]["base"]["sha"] = "c" * 40
    elif mutation == "merge_base":
        fixture["merge_base_sha"] = "c" * 40
    elif mutation == "head":
        fixture["event"]["pull_request"]["head"]["sha"] = "c" * 40
    with pytest.raises(PathAGateError, match=code):
        verify_path_a_r1(**fixture)


def test_changed_path_outside_allowed_paths_is_rejected() -> None:
    with pytest.raises(PathAGateError, match="changed_paths_outside_allowed"):
        verify_path_a_r1(**_fixture(changed_paths=("README.md",)))


@pytest.mark.parametrize(
    "path",
    [
        "project_state/decision_packet.md",
        ".github/workflows/ci.yml",
        "pyproject.toml",
    ],
)
def test_ordinary_r1_forbidden_governance_workflow_and_dependency_paths(path: str) -> None:
    issue_body = _issue_body(allowed_paths=path)
    with pytest.raises(PathAGateError, match="ordinary_r1_forbidden_paths"):
        verify_path_a_r1(**_fixture(issue_body=issue_body, changed_paths=(path,)))


@pytest.mark.parametrize(
    "term",
    [
        "direct push to main",
        "merge",
        "mark-ready",
        "auto-merge",
        "force push",
        "rebase",
        "squash",
        "tag",
        "release",
    ],
)
def test_privileged_r2_operations_cannot_be_allowed(term: str) -> None:
    extra = f"## Allowed operations\n\n```text\n{term}\n```\n"
    issue_body = _issue_body(extra=extra)
    with pytest.raises(PathAGateError, match="issue_privileged_operation_forbidden"):
        verify_path_a_r1(**_fixture(issue_body=issue_body))


def test_auto_merge_and_direct_main_are_rejected() -> None:
    fixture = _fixture()
    fixture["event"]["pull_request"]["auto_merge"] = {"enabled_by": {"login": "user"}}
    with pytest.raises(PathAGateError, match="auto_merge_forbidden"):
        verify_path_a_r1(**fixture)

    body = _issue_body()
    with pytest.raises(PathAGateError, match="snapshot_direct_main_forbidden"):
        parse_snapshot(_snapshot(body, branch="main"))


def test_issue_shell_metacharacters_are_rejected_and_never_executed() -> None:
    issue_body = _issue_body(required_checks="python -m pytest tests/base_platform -q; curl attacker")
    with pytest.raises(PathAGateError, match="issue_shell_command_forbidden"):
        verify_path_a_r1(**_fixture(issue_body=issue_body))


def test_pr_must_be_open_draft_and_event_must_be_pull_request() -> None:
    fixture = _fixture()
    fixture["event_name"] = "push"
    with pytest.raises(PathAGateError, match="event_not_pull_request"):
        verify_path_a_r1(**fixture)
    fixture = _fixture()
    fixture["event"]["pull_request"]["draft"] = False
    with pytest.raises(PathAGateError, match="pr_must_be_open_draft"):
        verify_path_a_r1(**fixture)


def test_approver_and_approval_event_are_verified() -> None:
    fixture = _fixture()
    fixture["approver_permission"] = "read"
    with pytest.raises(PathAGateError, match="approver_not_owner_or_maintainer"):
        verify_path_a_r1(**fixture)
    fixture = _fixture()
    fixture["approval_events"] = []
    with pytest.raises(PathAGateError, match="approval_event_missing"):
        verify_path_a_r1(**fixture)


@pytest.mark.parametrize("event", ["unlabeled", "other_actor_relabel"])
def test_latest_approval_transition_must_remain_effective(event: str) -> None:
    fixture = _fixture()
    if event == "unlabeled":
        fixture["approval_events"].append(
            {
                "event": "unlabeled",
                "id": 2,
                "label": {"name": "r1-approved"},
                "actor": {"login": "dddd2024"},
                "created_at": "2026-07-26T10:33:00Z",
            }
        )
        expected = "approval_event_superseded"
    else:
        fixture["approval_events"].append(
            {
                "event": "labeled",
                "id": 2,
                "label": {"name": "r1-approved"},
                "actor": {"login": "other-maintainer"},
                "created_at": "2026-07-26T10:33:00Z",
            }
        )
        expected = "approval_actor_mismatch"
    with pytest.raises(PathAGateError, match=expected):
        verify_path_a_r1(**fixture)


def test_post_approval_body_edit_state_is_rejected_even_with_current_digest() -> None:
    fixture = _fixture()
    fixture["issue"]["content_last_edited_at"] = "2026-07-26T10:33:00Z"
    with pytest.raises(PathAGateError, match="issue_body_edited_after_approval"):
        verify_path_a_r1(**fixture)


def test_task_check_selection_is_stable_visible_and_deduplicated(tmp_path: Path) -> None:
    changed = (
        "tests/base_platform/test_models.py",
        "reverse_agent/base_platform/models.py",
        "reverse_agent/control_plane/path_a.py",
    )
    (tmp_path / "tests" / "base_platform").mkdir(parents=True)
    (tmp_path / "tests" / "test_path_a_gate.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "test_control_plane_transition.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "test_planning_and_github_adapters.py").write_text("", encoding="utf-8")
    first = select_task_checks(changed, repo_root=tmp_path)
    second = select_task_checks(reversed(changed), repo_root=tmp_path)
    assert first == second
    assert first["check_ids"] == ("base_platform", "path_a_gate")
    assert first["commands"] == (BASE_PLATFORM_CHECK, PATH_A_CHECK)


def test_runtime_change_without_task_test_mapping_fails_closed() -> None:
    with pytest.raises(PathAGateError, match="runtime_change_without_task_check"):
        select_task_checks(("reverse_agent/unmapped_runtime.py",))


def test_missing_mapped_test_target_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import reverse_agent.control_plane.path_a as path_a

    monkeypatch.setattr(
        path_a,
        "TASK_CHECK_MAPPING",
        (
            (
                ("reverse_agent/mapped/**",),
                TaskCheck(
                    check_id="missing",
                    argv=("python", "-m", "pytest", "tests/exists.py", "tests/does-not-exist.py", "-q"),
                    required_targets=("tests/exists.py", "tests/does-not-exist.py"),
                ),
            ),
        ),
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "exists.py").write_text("", encoding="utf-8")
    with pytest.raises(PathAGateError, match="mapped_test_target_missing"):
        path_a.select_task_checks(("reverse_agent/mapped/runtime.py",), repo_root=tmp_path)


def test_workflow_selection_is_bound_to_checked_out_exact_head(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "reverse_agent.control_plane.path_a.subprocess.check_output",
        lambda *args, **kwargs: "c" * 40 + "\n",
    )
    event = {
        "repository": {"full_name": REPOSITORY},
        "number": 46,
        "pull_request": {
            "number": 46,
            "head": {"sha": HEAD_SHA},
            "base": {"sha": BASE_SHA},
        },
    }
    with pytest.raises(PathAGateError, match="workflow_exact_head_mismatch"):
        changed_paths_for_event(event, tmp_path)


def test_task_check_executor_rejects_non_mapping_command(tmp_path: Path) -> None:
    with pytest.raises(PathAGateError, match="untrusted_task_check_command"):
        execute_task_checks(
            {"commands": ["python -c \"print('not mapped')\""]},
            repo_root=tmp_path,
        )


def test_paginated_file_observation_reads_more_than_100_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = [{"filename": f"src/file-{index}.py", "status": "modified"} for index in range(100)]
    second = [{"filename": "src/file-100.py", "status": "modified"}]
    pages = {
        "/files?page=1": (first, "/files?page=2"),
        "/files?page=2": (second, None),
    }
    monkeypatch.setattr(
        "reverse_agent.control_plane.path_a._github_get_page",
        lambda path: pages[path],
    )
    entries = _collect_paginated_list("/files?page=1", expected_count=101)
    assert len(entries) == 101


def test_incomplete_api_file_pagination_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "reverse_agent.control_plane.path_a._github_get_page",
        lambda path: ([{"filename": "only.py", "status": "modified"}], None),
    )
    with pytest.raises(PathAGateError, match="github_file_pagination_incomplete"):
        _collect_paginated_list("/files", expected_count=101)


@pytest.mark.parametrize("status", ["renamed", "copied"])
def test_rename_and_copy_observe_current_and_previous_paths(status: str) -> None:
    paths = _paths_from_api_file_entries(
        [
            {
                "filename": "allowed/new.py",
                "previous_filename": "project_state/old.py",
                "status": status,
            }
        ]
    )
    assert paths == ("allowed/new.py", "project_state/old.py")
    issue_body = _issue_body(allowed_paths="allowed/**\nproject_state/**")
    with pytest.raises(PathAGateError, match="ordinary_r1_forbidden_paths"):
        verify_path_a_r1(**_fixture(issue_body=issue_body, changed_paths=paths))


def test_feature_push_is_not_path_a_authority_and_main_push_keeps_decision_mode(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision_packet.md"
    _write_decision(decision, transition=True, branch="codex/transition-v1")
    push_event = {"ref": "refs/heads/main", "before": BASE_SHA, "after": HEAD_SHA}
    assert detect_control_plane_mode(decision, event=push_event) == "transition"

    state_gate = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "state-gate.yml"
    ).read_text(encoding="utf-8")
    push_block = state_gate.split("  pull_request:", 1)[0]
    assert "push:\n    branches:\n      - main" in push_block
