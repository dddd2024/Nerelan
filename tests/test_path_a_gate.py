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
    DeltaObservation,
    execute_task_checks,
    issue_body_digest,
    parse_snapshot,
    run_path_a_gate,
    select_task_checks,
    verify_path_a_r1,
)
from reverse_agent.control_plane.worktree_state import (
    WorktreeClassification,
    classify_worktree_path,
)


REPOSITORY = "dddd2024/reverse-agent"
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40
APPROVAL_TIME = "2026-07-26T10:32:41Z"
PLANNING_REF = "owner/repository-modernization-v2-planning"


def _issue_body(
    *,
    allowed_paths: str = "reverse_agent/base_platform/**\ntests/base_platform/**",
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
    integration_base_ref: str = "main",
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
integration_base_ref: {integration_base_ref}
base_sha: {base_sha}
target_branch: {branch}
exact_head_sha: {head_sha}
```"""


def _fixture(
    *,
    issue_body: str | None = None,
    pr_body: str | None = None,
    changed_paths: tuple[str, ...] = ("reverse_agent/base_platform/models.py",),
) -> dict:
    body = issue_body if issue_body is not None else _issue_body()
    snapshot_body = pr_body if pr_body is not None else _snapshot(body)
    return {
        "event_name": "pull_request",
        "event": {
            "number": 49,
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "number": 49,
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
    assert result["selected_checks"] == [BASE_PLATFORM_CHECK]
    assert result["integration_base_ref"] == "main"


def test_owner_approved_planning_branch_is_valid_integration_base() -> None:
    body = _issue_body()
    fixture = _fixture(
        pr_body=_snapshot(body, integration_base_ref=PLANNING_REF),
    )
    fixture["event"]["pull_request"]["base"]["ref"] = PLANNING_REF

    result = verify_path_a_r1(**fixture)

    assert result["integration_base_ref"] == PLANNING_REF
    assert result["base_sha"] == BASE_SHA


def test_integration_base_ref_mismatch_is_rejected() -> None:
    fixture = _fixture()
    fixture["event"]["pull_request"]["base"]["ref"] = PLANNING_REF

    with pytest.raises(PathAGateError, match="integration_base_ref_mismatch"):
        verify_path_a_r1(**fixture)


def test_missing_integration_base_ref_is_rejected_without_compatibility_fallback() -> None:
    body = _issue_body()
    legacy_snapshot = _snapshot(body).replace("integration_base_ref: main\n", "")

    with pytest.raises(PathAGateError, match="snapshot_missing_fields"):
        verify_path_a_r1(**_fixture(pr_body=legacy_snapshot))


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


@pytest.mark.parametrize("pr_number", [1, 49, 151, 153, 9999])
def test_mode_routing_has_no_pr_number_specific_behavior(
    tmp_path: Path,
    pr_number: int,
) -> None:
    decision = tmp_path / "decision_packet.md"
    _write_decision(decision, transition=True, branch="owner/decision-bound-r2")
    event = _pr_event("owner/ordinary-r1")
    event["number"] = pr_number
    event["pull_request"]["number"] = pr_number

    assert detect_control_plane_mode(decision, event=event) == "path_a_r1"


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
    ("path", "minimum_risk"),
    [
        ("reverse_agent/control_plane/path_a.py", "R2"),
        ("reverse_agent/project_gate.py", "R2"),
        ("reverse_agent/github_adapter.py", "R2"),
        (".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml", "R2"),
        (".github/CODEOWNERS", "R2"),
        ("config/secrets/api.key", "R3"),
        ("config/service-credential.json", "R3"),
        ("tools/sample.exe", "R3"),
        ("pyproject.toml", "R2"),
        ("package-lock.json", "R2"),
    ],
)
def test_ordinary_r1_path_risk_floor_rejects_privileged_paths(
    path: str,
    minimum_risk: str,
) -> None:
    issue_body = _issue_body(allowed_paths=path)
    with pytest.raises(PathAGateError, match="path_risk_exceeds_r1") as exc_info:
        verify_path_a_r1(**_fixture(issue_body=issue_body, changed_paths=(path,)))
    assert f"path={path}" in exc_info.value.detail
    assert f"minimum_risk={minimum_risk}" in exc_info.value.detail
    assert "matched_pattern=" in exc_info.value.detail


@pytest.mark.parametrize("allowed_paths", ["*", "**", "**/*", ".", "./", ".//"])
def test_unbounded_allowed_paths_are_rejected(allowed_paths: str) -> None:
    issue_body = _issue_body(allowed_paths=allowed_paths)
    with pytest.raises(PathAGateError, match="issue_allowed_paths_unbounded"):
        verify_path_a_r1(**_fixture(issue_body=issue_body))


@pytest.mark.parametrize(
    "changed_paths",
    [
        ("reverse_agent/base_platform/models.py",),
        ("tests/base_platform/test_models.py",),
        (
            "reverse_agent/base_platform/models.py",
            "tests/base_platform/test_models.py",
        ),
    ],
)
def test_bounded_m1_paths_remain_r1_eligible(changed_paths: tuple[str, ...]) -> None:
    result = verify_path_a_r1(**_fixture(changed_paths=changed_paths))
    assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"
    assert result["selected_checks"] == [BASE_PLATFORM_CHECK]


def test_authority_revision_contains_all_live_authority_inputs() -> None:
    revision = _verify()["authority_revision"]
    assert len(revision["digest_sha256"]) == 64
    assert revision["repository"] == REPOSITORY
    assert revision["source_issue_number"] == 46
    assert len(revision["normalized_issue_body_digest"]) == 64
    assert revision["current_risk_labels"] == ["r1"]
    assert revision["latest_effective_r1_approved_event_id"] == 1
    assert revision["latest_effective_r1_approved_actor"] == "dddd2024"
    assert revision["latest_effective_r1_approved_timestamp"] == APPROVAL_TIME
    assert revision["source_issue_last_edited_at"] is None
    assert revision["pr_number"] == 49
    assert len(revision["pr_body_digest"]) == 64
    assert revision["pr_draft_state"] is True
    assert revision["pr_auto_merge_state"] is None
    assert revision["base_sha"] == BASE_SHA
    assert revision["exact_head_sha"] == HEAD_SHA


@pytest.mark.parametrize(
    "mutation",
    [
        "issue_body",
        "approval_removed",
        "approval_reapplied",
        "risk_label",
        "pr_body",
        "ready",
        "auto_merge",
    ],
)
def test_live_authority_mutation_invalidates_previous_revision(mutation: str) -> None:
    initial = _fixture()
    previous_revision = verify_path_a_r1(**initial)["authority_revision"]["digest_sha256"]
    current = _fixture()
    if mutation == "issue_body":
        body = current["issue"]["body"] + "\nmaterial authority edit\n"
        current["issue"]["body"] = body
        current["event"]["pull_request"]["body"] = _snapshot(body)
    elif mutation == "approval_removed":
        current["issue"]["labels"] = [{"name": "r1"}]
        current["approval_events"].append(
            {
                "event": "unlabeled",
                "id": 2,
                "label": {"name": "r1-approved"},
                "actor": {"login": "dddd2024"},
                "created_at": "2026-07-26T10:33:00Z",
            }
        )
    elif mutation == "approval_reapplied":
        current["approval_events"].append(
            {
                "event": "labeled",
                "id": 2,
                "label": {"name": "r1-approved"},
                "actor": {"login": "dddd2024"},
                "created_at": APPROVAL_TIME,
            }
        )
    elif mutation == "risk_label":
        current["issue"]["labels"] = [{"name": "r2"}, {"name": "r1-approved"}]
    elif mutation == "pr_body":
        current["event"]["pull_request"]["body"] += "\n\nnon-snapshot PR metadata edit"
    elif mutation == "ready":
        current["event"]["pull_request"]["draft"] = False
    else:
        current["event"]["pull_request"]["auto_merge"] = {
            "enabled_by": {"login": "dddd2024"}
        }
    with pytest.raises(PathAGateError, match="authority_revision_mismatch"):
        verify_path_a_r1(
            **current,
            expected_authority_revision=previous_revision,
        )


def test_path_a_gate_requeries_live_pr_and_issue_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fixture = _fixture()
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(fixture["event"]), encoding="utf-8")
    calls: list[str] = []

    def fake_github_get(path: str):
        calls.append(path)
        if path == f"/repos/{REPOSITORY}/pulls/49":
            return fixture["event"]["pull_request"]
        if path == f"/repos/{REPOSITORY}/issues/46":
            return fixture["issue"]
        raise AssertionError(path)

    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setattr(
        "reverse_agent.control_plane.path_a._github_get",
        fake_github_get,
    )
    monkeypatch.setattr(
        "reverse_agent.control_plane.path_a._issue_last_edited_at",
        lambda repository, issue_number: None,
    )
    monkeypatch.setattr(
        "reverse_agent.control_plane.path_a._collect_paginated_list",
        lambda path: fixture["approval_events"],
    )
    monkeypatch.setattr(
        "reverse_agent.control_plane.path_a.changed_paths_for_event",
        lambda event, repo_root: DeltaObservation(
            changed_paths=fixture["changed_paths"],
            base_sha=BASE_SHA,
            head_sha=HEAD_SHA,
            empty_delta=False,
        ),
    )
    monkeypatch.setattr(
        "reverse_agent.control_plane.path_a.subprocess.check_output",
        lambda *args, **kwargs: BASE_SHA,
    )

    result = run_path_a_gate(
        event_path=event_path,
        repository=REPOSITORY,
        repo_root=tmp_path,
    )
    assert calls[:2] == [
        f"/repos/{REPOSITORY}/pulls/49",
        f"/repos/{REPOSITORY}/issues/46",
    ]
    assert result["live_github_state_observed"] is True
    assert result["authority_revalidation_required"] is True


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
    with pytest.raises(PathAGateError, match="stage_mismatch"):
        verify_path_a_r1(**fixture, stage="IMPLEMENTATION_DRAFT")


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
    with pytest.raises(
        PathAGateError,
        match="issue_body_edit_not_strictly_before_approval",
    ):
        verify_path_a_r1(**fixture)


def test_body_edit_equal_to_approval_time_is_rejected() -> None:
    fixture = _fixture()
    fixture["issue"]["content_last_edited_at"] = APPROVAL_TIME
    with pytest.raises(
        PathAGateError,
        match="issue_body_edit_not_strictly_before_approval",
    ):
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


@pytest.mark.parametrize(
    "path",
    [
        "reverse_agent/platform_v1/run_store.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/task_service.py",
        "tests/platform_v1/test_task_execution.py",
    ],
)
def test_platform_v1_paths_select_repository_owned_platform_suite(path: str) -> None:
    result = select_task_checks((path,))

    assert result["check_ids"] == ("platform_v1",)
    assert result["commands"] == ("python -m pytest tests/platform_v1 -q",)


@pytest.mark.parametrize(
    "path",
    [
        "reverse_agent/architecture/contracts.py",
        "reverse_agent/workflows/team_graph.py",
        "reverse_agent/workflows/nodes/acceptance_gate.py",
        "tests/test_team_graph.py",
    ],
)
def test_team_paths_select_repository_owned_team_regression_suite(path: str) -> None:
    result = select_task_checks((path,))

    assert result["check_ids"] == ("team_targets",)
    assert result["commands"] == (
        "python -m pytest tests/test_development_graph.py tests/test_team_graph.py -q",
    )


def test_mixed_issue_151_paths_select_both_suites_once() -> None:
    result = select_task_checks(
        (
            "reverse_agent/platform_v1/task_service.py",
            "tests/platform_v1/test_task_execution.py",
            "reverse_agent/workflows/team_graph.py",
            "tests/test_team_graph.py",
        )
    )

    assert result["check_ids"] == ("platform_v1", "team_targets")
    assert result["commands"] == (
        "python -m pytest tests/platform_v1 -q",
        "python -m pytest tests/test_development_graph.py tests/test_team_graph.py -q",
    )


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
@pytest.mark.parametrize(
    ("previous_filename", "minimum_risk"),
    [
        ("config/secrets/api.key", "R3"),
        ("project_state/old.py", "R2"),
        ("reverse_agent/control_plane/old.py", "R2"),
    ],
)
def test_rename_and_copy_reject_risky_previous_paths(
    status: str,
    previous_filename: str,
    minimum_risk: str,
) -> None:
    paths = _paths_from_api_file_entries(
        [
            {
                "filename": "allowed/new.py",
                "previous_filename": previous_filename,
                "status": status,
            }
        ]
    )
    assert paths == ("allowed/new.py", previous_filename)
    issue_body = _issue_body(allowed_paths="allowed/**")
    with pytest.raises(PathAGateError, match="path_risk_exceeds_r1") as exc_info:
        verify_path_a_r1(**_fixture(issue_body=issue_body, changed_paths=paths))
    assert f"path={previous_filename}" in exc_info.value.detail
    assert f"minimum_risk={minimum_risk}" in exc_info.value.detail


@pytest.mark.parametrize(
    ("path", "minimum_risk"),
    [
        ("CODEOWNERS", "R2"),
        ("docs/CODEOWNERS", "R2"),
        ("Config/Secrets/API.KEY", "R3"),
        ("service-CREDENTIAL.json", "R3"),
        ("tools/payload.EXE", "R3"),
        (".ENV", "R3"),
        (".ENV.production", "R3"),
        ("certs/CLIENT.PEM", "R3"),
        ("certs/CLIENT.KEY", "R3"),
        ("certs/CLIENT.P12", "R3"),
        ("certs/CLIENT.PFX", "R3"),
        ("native/LIBRARY.DLL", "R3"),
        ("native/LIBRARY.SO", "R3"),
        ("native/LIBRARY.DYLIB", "R3"),
    ],
)
def test_security_path_risk_matching_is_case_insensitive(
    path: str,
    minimum_risk: str,
) -> None:
    issue_body = _issue_body(allowed_paths=path)
    with pytest.raises(PathAGateError, match="path_risk_exceeds_r1") as exc_info:
        verify_path_a_r1(**_fixture(issue_body=issue_body, changed_paths=(path,)))
    assert f"path={path}" in exc_info.value.detail
    assert f"minimum_risk={minimum_risk}" in exc_info.value.detail


@pytest.mark.parametrize("status", ["renamed", "copied"])
def test_mixed_case_risky_previous_path_is_rejected(status: str) -> None:
    paths = _paths_from_api_file_entries(
        [
            {
                "filename": "allowed/new.py",
                "previous_filename": "Config/Secrets/API.KEY",
                "status": status,
            }
        ]
    )
    with pytest.raises(PathAGateError, match="path_risk_exceeds_r1") as exc_info:
        verify_path_a_r1(
            **_fixture(
                issue_body=_issue_body(allowed_paths="allowed/**"),
                changed_paths=paths,
            )
        )
    assert "path=Config/Secrets/API.KEY" in exc_info.value.detail
    assert "minimum_risk=R3" in exc_info.value.detail


@pytest.mark.parametrize(
    "only_changed_path",
    [
        "pyproject.toml",
        "requirements-dev.txt",
        "setup.py",
        "uv.lock",
        "Dockerfile",
        "CODEOWNERS",
        "docs/CODEOWNERS",
        ".env",
        "config/Secrets/API.KEY",
        "tools/payload.EXE",
    ],
)
def test_state_gate_pull_request_trigger_reaches_every_risk_only_change(
    only_changed_path: str,
) -> None:
    state_gate = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "state-gate.yml"
    ).read_text(encoding="utf-8")
    pull_request_block = state_gate.split("  pull_request:", 1)[1].split(
        "\n\npermissions:",
        1,
    )[0]
    assert "paths:" not in pull_request_block, only_changed_path
    assert "Path-A R1 gate" in state_gate


def test_state_gate_revalidates_on_pr_authority_metadata_changes() -> None:
    state_gate = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "state-gate.yml"
    ).read_text(encoding="utf-8")
    pull_request_block = state_gate.split("  pull_request:", 1)[1].split(
        "\n\npermissions:",
        1,
    )[0]
    for event_type in (
        "opened",
        "edited",
        "synchronize",
        "reopened",
        "converted_to_draft",
        "ready_for_review",
        "labeled",
        "unlabeled",
        "auto_merge_enabled",
        "auto_merge_disabled",
    ):
        assert f"- {event_type}" in pull_request_block


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


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("task_workspaces/task-a/output.txt", WorktreeClassification.KNOWN_RUNTIME_SCRATCH),
        (".platform_v1_runtime/tasks.sqlite3", WorktreeClassification.KNOWN_RUNTIME_SCRATCH),
        ("project_state/gates/command_plan.json", WorktreeClassification.GENERATED_GOVERNANCE_ARTIFACT),
        ("notes/local.txt", WorktreeClassification.UNKNOWN_UNTRACKED),
    ],
)
def test_untracked_worktree_paths_are_deterministically_classified(
    path: str,
    expected: WorktreeClassification,
) -> None:
    result = classify_worktree_path(path, tracked=False, authorized_paths=())

    assert result.classification is expected
    assert result.stageable is False
    assert result.deleted is False


def test_authorized_tracked_delta_is_stageable_but_still_allowlisted() -> None:
    result = classify_worktree_path(
        "tests/test_path_a_gate.py",
        tracked=True,
        authorized_paths=("tests/test_path_a_gate.py",),
    )

    assert result.classification is WorktreeClassification.AUTHORIZED_TRACKED_DELTA
    assert result.stageable is True
    assert result.publication_blocking is False


def test_unknown_untracked_is_non_destructive_but_blocks_publication() -> None:
    result = classify_worktree_path(
        "scratch/unexplained.txt",
        tracked=False,
        authorized_paths=(),
    )

    assert result.classification is WorktreeClassification.UNKNOWN_UNTRACKED
    assert result.bootstrap_blocking is False
    assert result.publication_blocking is True
    assert result.deleted is False


def test_unauthorized_tracked_path_is_immediate_hard_stop() -> None:
    result = classify_worktree_path(
        "frontend/src/unauthorized.ts",
        tracked=True,
        authorized_paths=("tests/**",),
    )

    assert result.classification is WorktreeClassification.UNAUTHORIZED_TRACKED_OR_SENSITIVE
    assert result.bootstrap_blocking is True
    assert result.publication_blocking is True
    assert result.stageable is False


@pytest.mark.parametrize(
    "path",
    [
        "config/service-secret.json",
        "config/service-credential.json",
        ".env",
        "config/.env.production",
        "certs/client.pem",
        "certs/client.KEY",
        "certs/client.p12",
        "certs/client.PFX",
        "native/tool.exe",
        "native/tool.DLL",
        "native/library.SO",
        "native/library.DYLIB",
        "Config/Secrets/API.KEY",
    ],
)
def test_untracked_path_a_r3_categories_are_sensitive_case_insensitively(path: str) -> None:
    result = classify_worktree_path(path, tracked=False, authorized_paths=())

    assert result.classification is WorktreeClassification.UNAUTHORIZED_TRACKED_OR_SENSITIVE
    assert result.bootstrap_blocking is True
    assert result.publication_blocking is True
    assert result.stageable is False


# ---------------------------------------------------------------------------
# Stage-aware Path-A lifecycle regressions (Issue #364 / parent #353).
# ---------------------------------------------------------------------------


def _activation_fixture() -> dict:
    body = _issue_body()
    return {
        "event_name": "pull_request",
        "event": {
            "number": 49,
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "number": 49,
                "state": "open",
                "draft": True,
                "body": _snapshot(body),
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
        "changed_paths": (),
        "merge_base_sha": BASE_SHA,
        "expected_repository": REPOSITORY,
    }


def _ready_fixture(*, changed_paths: tuple[str, ...] = ()) -> dict:
    fx = _activation_fixture()
    fx["event"]["pull_request"]["draft"] = False
    fx["changed_paths"] = changed_paths
    return fx


def _ready_fixture_with_implementation_delta() -> dict:
    return _ready_fixture(
        changed_paths=("reverse_agent/base_platform/models.py",)
    )


def test_A1_activation_draft_zero_delta_passes() -> None:
    result = verify_path_a_r1(**_activation_fixture())

    assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"
    assert result["lifecycle_stage"] == "ACTIVATION_DRAFT"
    assert result["implementation_authority"] is False
    assert result["product_accepted"] is False
    assert result["implementation_complete"] is False
    assert result["merge_authority"] is False
    assert result["ready_authority"] is False
    assert result["no_task_checks"] is True
    assert result["empty_delta"] is True
    assert result["changed_paths"] == []
    assert result["selected_checks"] == []
    assert result["authority_revalidation_required"] is True


def test_A2_activation_draft_approval_invalid_blocks() -> None:
    fixture = _activation_fixture()
    fixture["issue"]["labels"] = [{"name": "r1"}]
    with pytest.raises(PathAGateError, match="issue_not_r1_approved"):
        verify_path_a_r1(**fixture)


def test_A3_activation_draft_cannot_be_product_accepted() -> None:
    result = verify_path_a_r1(**_activation_fixture())

    assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"
    assert result["lifecycle_stage"] == "ACTIVATION_DRAFT"
    assert result["implementation_authority"] is False
    assert result["product_accepted"] is False
    assert result["implementation_complete"] is False
    assert result["merge_authority"] is False
    assert result["ready_authority"] is False
    assert result["no_task_checks"] is True
    assert result["empty_delta"] is True
    assert result["changed_paths"] == []
    assert result["selected_checks"] == []
    assert result["authority_revalidation_required"] is True


@pytest.mark.parametrize(
    "changed_paths",
    [
        ("reverse_agent/base_platform/models.py",),
        ("tests/base_platform/test_models.py",),
        (
            "reverse_agent/base_platform/models.py",
            "tests/base_platform/test_models.py",
        ),
    ],
)
def test_I1_valid_implementation_draft_remains_authorized(
    changed_paths: tuple[str, ...],
) -> None:
    result = verify_path_a_r1(**_fixture(changed_paths=changed_paths))

    assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"
    assert result["lifecycle_stage"] == "IMPLEMENTATION_DRAFT"
    assert result["implementation_authority"] is True
    assert result["product_accepted"] is True
    assert result["implementation_complete"] is True
    assert result["merge_authority"] is False
    assert result["ready_authority"] is False
    assert result["no_task_checks"] is False
    assert result["empty_delta"] is False
    assert result["selected_checks"] == [BASE_PLATFORM_CHECK]


def test_I2_invalid_implementation_draft_still_fails_closed() -> None:
    with pytest.raises(PathAGateError, match="changed_paths_outside_allowed"):
        verify_path_a_r1(**_fixture(changed_paths=("README.md",)))


def test_I2b_implementation_draft_with_zero_delta_rejects() -> None:
    with pytest.raises(PathAGateError, match="stage_mismatch"):
        verify_path_a_r1(
            **_activation_fixture(),
            stage="IMPLEMENTATION_DRAFT",
        )


def test_R1_ready_with_implementation_delta_passes() -> None:
    result = verify_path_a_r1(**_ready_fixture_with_implementation_delta())

    assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"
    assert result["lifecycle_stage"] == "READY_FINAL_READINESS"
    assert result["implementation_authority"] is False
    assert result["product_accepted"] is False
    assert result["implementation_complete"] is False
    assert result["merge_authority"] is False
    assert result["ready_authority"] is True
    assert result["no_task_checks"] is True
    assert result["selected_checks"] == []
    assert result["authority_revalidation_required"] is True
    assert result["changed_paths"] == ["reverse_agent/base_platform/models.py"]


def test_R2_ready_head_drift_blocks() -> None:
    fixture = _ready_fixture_with_implementation_delta()
    fixture["event"]["pull_request"]["head"]["sha"] = "c" * 40
    with pytest.raises(PathAGateError, match="exact_head_mismatch"):
        verify_path_a_r1(**fixture)


def test_R2b_ready_base_drift_blocks() -> None:
    fixture = _ready_fixture_with_implementation_delta()
    fixture["event"]["pull_request"]["base"]["sha"] = "c" * 40
    with pytest.raises(PathAGateError, match="base_sha_mismatch"):
        verify_path_a_r1(**fixture)


def test_R2c_ready_merge_base_drift_blocks() -> None:
    fixture = _ready_fixture_with_implementation_delta()
    fixture["merge_base_sha"] = "c" * 40
    with pytest.raises(PathAGateError, match="merge_base_mismatch"):
        verify_path_a_r1(**fixture)


def test_R3_ready_issue_digest_drift_blocks() -> None:
    fixture = _ready_fixture_with_implementation_delta()
    approved_body = fixture["issue"]["body"]
    fixture["issue"]["body"] = approved_body + "\nmaterial edit\n"
    with pytest.raises(PathAGateError, match="issue_body_digest_mismatch"):
        verify_path_a_r1(**fixture)


def test_R3b_ready_approval_removed_blocks() -> None:
    fixture = _ready_fixture_with_implementation_delta()
    fixture["issue"]["labels"] = [{"name": "r1"}]
    fixture["approval_events"].append(
        {
            "event": "unlabeled",
            "id": 2,
            "label": {"name": "r1-approved"},
            "actor": {"login": "dddd2024"},
            "created_at": "2026-07-26T10:33:00Z",
        }
    )
    with pytest.raises(PathAGateError, match="issue_not_r1_approved"):
        verify_path_a_r1(**fixture)


def test_R4_ready_missing_snapshot_blocks() -> None:
    fixture = _ready_fixture_with_implementation_delta()
    fixture["event"]["pull_request"]["body"] = ""
    with pytest.raises(PathAGateError, match="snapshot_missing"):
        verify_path_a_r1(**fixture)


def test_R4b_ready_missing_approval_blocks() -> None:
    fixture = _ready_fixture_with_implementation_delta()
    fixture["approval_events"] = []
    with pytest.raises(PathAGateError, match="approval_event_missing"):
        verify_path_a_r1(**fixture)


def test_D1_converted_to_draft_empty_delta_is_activation() -> None:
    body = _issue_body()
    fixture = {
        "event_name": "pull_request",
        "event": {
            "number": 49,
            "repository": {"full_name": REPOSITORY},
            "pull_request": {
                "number": 49,
                "state": "open",
                "draft": True,
                "body": _snapshot(body),
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
        "changed_paths": (),
        "merge_base_sha": BASE_SHA,
        "expected_repository": REPOSITORY,
    }
    result = verify_path_a_r1(**fixture)

    assert result["lifecycle_stage"] == "ACTIVATION_DRAFT"
    assert result["empty_delta"] is True
    assert result["implementation_authority"] is False
    assert result["product_accepted"] is False


def test_D2_converted_to_draft_with_delta_is_implementation() -> None:
    fixture = _fixture(changed_paths=("reverse_agent/base_platform/models.py",))
    fixture["event"]["pull_request"]["draft"] = True
    result = verify_path_a_r1(**fixture)

    assert result["lifecycle_stage"] == "IMPLEMENTATION_DRAFT"
    assert result["empty_delta"] is False
    assert result["implementation_authority"] is True
    assert result["product_accepted"] is True


def test_L1_ready_recomputes_authority_revision_on_live_pr_state() -> None:
    initial = _ready_fixture_with_implementation_delta()
    initial["event"]["pull_request"]["draft"] = False
    previous_revision = verify_path_a_r1(**initial)["authority_revision"]["digest_sha256"]

    current = _ready_fixture_with_implementation_delta()
    current["event"]["pull_request"]["body"] += "\n\nnon-snapshot PR metadata edit"
    with pytest.raises(PathAGateError, match="authority_revision_mismatch"):
        verify_path_a_r1(
            **current,
            expected_authority_revision=previous_revision,
        )


def test_L1b_ready_issue_body_mutation_invalidates_previous_revision() -> None:
    initial = _ready_fixture_with_implementation_delta()
    previous_revision = verify_path_a_r1(**initial)["authority_revision"]["digest_sha256"]

    current = _ready_fixture_with_implementation_delta()
    body = current["issue"]["body"] + "\nmaterial authority edit\n"
    current["issue"]["body"] = body
    current["event"]["pull_request"]["body"] = _snapshot(body)
    with pytest.raises(PathAGateError, match="authority_revision_mismatch"):
        verify_path_a_r1(
            **current,
            expected_authority_revision=previous_revision,
        )


def test_L1c_ready_approval_reapplied_invalidates_previous_revision() -> None:
    initial = _ready_fixture_with_implementation_delta()
    previous_revision = verify_path_a_r1(**initial)["authority_revision"]["digest_sha256"]

    current = _ready_fixture_with_implementation_delta()
    current["approval_events"].append(
        {
            "event": "labeled",
            "id": 2,
            "label": {"name": "r1-approved"},
            "actor": {"login": "dddd2024"},
            "created_at": APPROVAL_TIME,
        }
    )
    with pytest.raises(PathAGateError, match="authority_revision_mismatch"):
        verify_path_a_r1(
            **current,
            expected_authority_revision=previous_revision,
        )


def test_M1_auto_merge_blocks_in_implementation_draft() -> None:
    fixture = _fixture(changed_paths=("reverse_agent/base_platform/models.py",))
    fixture["event"]["pull_request"]["auto_merge"] = {
        "enabled_by": {"login": "user"},
    }
    with pytest.raises(PathAGateError, match="auto_merge_forbidden"):
        verify_path_a_r1(**fixture)


def test_M1b_auto_merge_blocks_in_ready_final_readiness() -> None:
    fixture = _ready_fixture_with_implementation_delta()
    fixture["event"]["pull_request"]["auto_merge"] = {
        "enabled_by": {"login": "user"},
    }
    with pytest.raises(PathAGateError, match="auto_merge_forbidden"):
        verify_path_a_r1(**fixture)


def test_M1c_auto_merge_blocks_in_activation_draft() -> None:
    fixture = _activation_fixture()
    fixture["event"]["pull_request"]["auto_merge"] = {
        "enabled_by": {"login": "user"},
    }
    with pytest.raises(PathAGateError, match="auto_merge_forbidden"):
        verify_path_a_r1(**fixture)


def test_G1_state_gate_pull_request_triggers_cover_every_lifecycle_transition() -> None:
    state_gate = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "state-gate.yml"
    ).read_text(encoding="utf-8")
    pull_request_block = state_gate.split("  pull_request:", 1)[1].split(
        "\n\npermissions:",
        1,
    )[0]
    for event_type in (
        "opened",
        "edited",
        "synchronize",
        "reopened",
        "converted_to_draft",
        "ready_for_review",
        "labeled",
        "unlabeled",
        "auto_merge_enabled",
        "auto_merge_disabled",
    ):
        assert f"- {event_type}" in pull_request_block
    assert "Path-A R1 gate" in state_gate
    assert "path-a-r1-gate" in state_gate


def test_explicit_stage_mismatch_fails_closed() -> None:
    with pytest.raises(PathAGateError, match="stage_mismatch"):
        verify_path_a_r1(
            **_activation_fixture(),
            stage="IMPLEMENTATION_DRAFT",
        )

    with pytest.raises(PathAGateError, match="stage_mismatch"):
        verify_path_a_r1(
            **_ready_fixture_with_implementation_delta(),
            stage="ACTIVATION_DRAFT",
        )


def test_invalid_stage_token_fails_closed() -> None:
    with pytest.raises(PathAGateError, match="invalid_stage"):
        verify_path_a_r1(
            **_activation_fixture(),
            stage="UNKNOWN_STAGE",
        )


# ---------------------------------------------------------------------------
# Correction regressions for Issue #364 re-audit (blockers A / B / C).
# ---------------------------------------------------------------------------


def test_ready_with_empty_delta_blocks() -> None:
    with pytest.raises(PathAGateError, match="ready_without_implementation_delta"):
        verify_path_a_r1(**_ready_fixture())


@pytest.mark.parametrize("draft_value", [None, "false", 1, "True"])
def test_malformed_pr_draft_state_blocks(draft_value: object) -> None:
    fixture = _fixture()
    fixture["event"]["pull_request"]["draft"] = draft_value
    with pytest.raises(PathAGateError, match="pr_draft_state_invalid"):
        verify_path_a_r1(**fixture)


def test_draft_missing_blocks() -> None:
    fixture = _fixture()
    del fixture["event"]["pull_request"]["draft"]
    with pytest.raises(PathAGateError, match="pr_draft_state_invalid"):
        verify_path_a_r1(**fixture)


def test_activation_shell_metacharacter_blocks() -> None:
    issue_body = _issue_body(
        required_checks="python -m pytest tests/base_platform -q; curl attacker"
    )
    fixture = _activation_fixture()
    fixture["issue"]["body"] = issue_body
    fixture["event"]["pull_request"]["body"] = _snapshot(issue_body)
    with pytest.raises(PathAGateError, match="issue_shell_command_forbidden"):
        verify_path_a_r1(**fixture)


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
def test_activation_privileged_operation_blocks(term: str) -> None:
    extra = f"## Allowed operations\n\n```text\n{term}\n```\n"
    issue_body = _issue_body(extra=extra)
    fixture = _activation_fixture()
    fixture["issue"]["body"] = issue_body
    fixture["event"]["pull_request"]["body"] = _snapshot(issue_body)
    with pytest.raises(PathAGateError, match="issue_privileged_operation_forbidden"):
        verify_path_a_r1(**fixture)


# ---------------------------------------------------------------------------
# Model-access task-check mapping regressions (Issue #48 R2 v3).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "reverse_agent/model_access/contracts.py",
        "reverse_agent/model_access/store.py",
        "reverse_agent/model_access/credential_relay.py",
        "tests/test_model_access.py",
        "tests/test_connection_binding.py",
    ],
)
def test_model_access_paths_select_repository_owned_model_access_suite(path: str) -> None:
    result = select_task_checks((path,))

    assert result["check_ids"] == ("model_access",)
    assert result["commands"] == (
        "python -m pytest tests/test_model_access.py tests/test_connection_binding.py -q",
    )


def test_issue_required_check_text_cannot_supply_missing_runtime_mapping() -> None:
    issue_body = _issue_body(
        allowed_paths="reverse_agent/unmapped_runtime.py",
        required_checks="python -m pytest tests/test_connection_binding.py -q",
    )

    with pytest.raises(PathAGateError, match="runtime_change_without_task_check"):
        verify_path_a_r1(
            **_fixture(
                issue_body=issue_body,
                changed_paths=("reverse_agent/unmapped_runtime.py",),
            )
        )
