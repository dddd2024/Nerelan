"""Provider-free EBA-0 regressions in the blocking Platform V1 suite.

These exercise actual Path-A/preflight functions, not model transcripts. They
prove authorization and structural readiness, not end-to-end product autonomy.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from reverse_agent.control_plane import path_a
from reverse_agent.control_plane import work_item_preflight as preflight

REPOSITORY = "dddd2024/Nerelan"
BASE = "a" * 40
HEAD = "b" * 40
BRANCH = "owner/evidence-bound-test"
APPROVED_AT = "2026-09-29T14:00:00Z"
BODY = f"""## Candidate R1 Work Item

## Approved specification candidate

Add one byte-identical branded launcher alias. Do not change its behavior.

## Allowed paths

```text
launch_nerelan.bat
```

## Forbidden operations

```text
direct push to main
force push
rebase
squash
mark-ready
merge
auto-merge
```

## Acceptance criteria

- The committed alias has the same bytes as the base launcher.
- The base launcher remains unchanged; exactly one file is added.

## Required deterministic checks

```text
git diff --check
```

## Target branch

```text
{BRANCH}
```

## Integration base ref

```text
main
```

## Base SHA

```text
{BASE}
```
"""


def _snapshot(body: str = BODY, **changes: object) -> str:
    digest = path_a.issue_body_digest(body)
    fields = {
        "repository": REPOSITORY,
        "issue_number": 1033,
        "approval_state": "APPROVED",
        "approved_by": "dddd2024",
        "approval_event_or_time": APPROVED_AT,
        "body_digest_sha256": digest,
        "immutable_observation_ref": digest,
        "work_item_identity": f"{REPOSITORY}#1033@{digest}",
        "target_branch": BRANCH,
        "integration_base_ref": "main",
        "base_sha": BASE,
        "exact_head_sha": HEAD,
    }
    fields.update(changes)
    if "work_item_identity" not in changes:
        fields["work_item_identity"] = (
            f"{fields['repository']}#{fields['issue_number']}@{fields['immutable_observation_ref']}"
        )
    return "```text\n" + "\n".join(f"{k}: {v}" for k, v in fields.items()) + "\n```\n"


def _authority_fixture(*, draft: bool = True, changed: bool = True) -> dict:
    pr = {
        "number": 1035, "state": "open", "draft": draft, "auto_merge": None,
        "body": _snapshot(),
        "base": {"ref": "main", "sha": BASE},
        "head": {"ref": BRANCH, "sha": HEAD, "repo": {"full_name": REPOSITORY}},
    }
    return {
        "event_name": "pull_request",
        "event": {"number": 1035, "repository": {"full_name": REPOSITORY}, "pull_request": pr},
        "issue": {
            "number": 1033, "state": "open", "body": BODY,
            "labels": ["r1", "r1-approved"],
            "content_last_edited_at": "2026-09-29T13:00:00Z",
        },
        "approval_events": [{
            "id": 1, "event": "labeled", "label": {"name": "r1-approved"},
            "actor": {"login": "dddd2024"}, "created_at": APPROVED_AT,
        }],
        "approver_permission": "admin",
        "changed_paths": ("launch_nerelan.bat",) if changed else (),
        "merge_base_sha": BASE,
        "expected_repository": REPOSITORY,
    }


def _codes(result: dict) -> set[str]:
    return {item["code"] for item in result["diagnostics"]}


def _run(body: str = BODY, **kwargs: object) -> dict:
    return preflight.preflight_work_item(body, repository=REPOSITORY, **kwargs)


def _assert_no_authority(result: dict) -> None:
    for key in (
        "approval_granted", "implementation_authority", "ready_authority",
        "merge_authority", "product_accepted", "implementation_complete",
        "commands_executed", "live_state_verified",
    ):
        assert result[key] is False, key


@pytest.mark.parametrize("draft,changed,stage,implementation_authority,ready_authority", [
    (True, False, path_a.ACTIVATION_DRAFT, False, False),
    (True, True, path_a.IMPLEMENTATION_DRAFT, True, False),
    (False, True, path_a.READY_FINAL_READINESS, False, True),
])
def test_authorization_never_certifies_product_completion(
    draft: bool, changed: bool, stage: str, implementation_authority: bool, ready_authority: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def must_not_execute(*args: object, **kwargs: object) -> None:
        raise AssertionError("Authorization must not execute evidence-producing commands")
    monkeypatch.setattr(path_a, "execute_task_checks", must_not_execute)
    result = path_a.verify_path_a_r1(**_authority_fixture(draft=draft, changed=changed))
    assert result["gate_status"] == "PATH_A_R1_AUTHORIZED"
    assert result["lifecycle_stage"] == stage
    assert result["implementation_authority"] is implementation_authority
    assert result["ready_authority"] is ready_authority  # Preserve existing stage contract.
    assert result["product_accepted"] is False
    assert result["implementation_complete"] is False
    assert result["merge_authority"] is False
    assert result["issue_commands_executed"] is False


@pytest.mark.parametrize("defect,code", [
    ("revoked", "issue_not_r1_approved"),
    ("body_changed", "issue_body_digest_mismatch"),
    ("edited_after_approval", "issue_body_edit_not_strictly_before_approval"),
    ("base_changed", "base_sha_mismatch"),
    ("path_expanded", "changed_paths_outside_allowed"),
    ("auto_merge", "auto_merge_forbidden"),
])
def test_claim_ceiling_does_not_weaken_existing_denials(defect: str, code: str) -> None:
    kwargs = _authority_fixture()
    if defect == "revoked":
        kwargs["issue"]["labels"] = ["r1"]
    elif defect == "body_changed":
        kwargs["issue"]["body"] += "\nChanged requirement.\n"
    elif defect == "edited_after_approval":
        kwargs["issue"]["content_last_edited_at"] = "2026-09-29T14:01:00Z"
    elif defect == "base_changed":
        kwargs["event"]["pull_request"]["base"]["sha"] = "c" * 40
    elif defect == "path_expanded":
        kwargs["changed_paths"] = ("unapproved.txt",)
    else:
        kwargs["event"]["pull_request"]["auto_merge"] = {"enabled": True}
    with pytest.raises(path_a.PathAGateError, match=code):
        path_a.verify_path_a_r1(**kwargs)


def test_github_task_output_binds_observed_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    event_file = tmp_path / "event.json"
    event_file.write_text("{}", encoding="utf-8")
    output = tmp_path / "github-output"
    output.write_text("earlier=value\n", encoding="utf-8")
    delta = path_a.DeltaObservation(("launch_nerelan.bat",), BASE, HEAD, False)
    monkeypatch.setattr(path_a, "changed_paths_for_event", lambda *args: delta)
    result = path_a.write_task_check_outputs(event_path=event_file, repo_root=tmp_path, output_path=output)
    lines = output.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "earlier=value"
    assert f"exact_head_sha={HEAD}" in lines
    assert result["exact_head_sha"] == HEAD
    assert result["base_sha"] == BASE
    assert json.loads(next(line.split("=", 1)[1] for line in lines if line.startswith("selected_checks_json="))) == result["commands"]


def test_valid_candidate_needs_no_preactivation_snapshot() -> None:
    result = _run(observed_base_sha=BASE)
    assert result["readiness"] == "APPROVAL_READY", result
    assert result["allowed_path_count"] == 1
    assert result["body_digest_sha256"] == path_a.issue_body_digest(BODY)
    assert result["snapshot_parsed"] is False
    assert result["requires_owner_review"] is True
    _assert_no_authority(result)


@pytest.mark.parametrize("old,new", [
    ("Approved specification candidate", "Approved specification"),
    ("Required deterministic checks", "Required checks"),
    ("## Allowed paths", "### Allowed paths"),
    ("byte-identical", "字节一致"),
    ("\n", "\r\n"),
])
def test_supported_template_variants(old: str, new: str) -> None:
    result = _run(BODY.replace(old, new))
    assert result["readiness"] == "APPROVAL_READY", result
    _assert_no_authority(result)


@pytest.mark.parametrize("heading", [
    "Approved specification candidate", "Allowed paths", "Forbidden operations",
    "Acceptance criteria", "Required deterministic checks", "Target branch",
    "Integration base ref", "Base SHA",
])
def test_missing_and_duplicate_required_sections(heading: str) -> None:
    missing = _run(BODY.replace(f"## {heading}", "## Other section"))
    assert "issue_missing_section" in _codes(missing)
    duplicate = _run(BODY + f"\n## {heading}\n\n```text\nother\n```\n")
    assert "issue_duplicate_section" in _codes(duplicate)
    _assert_no_authority(duplicate)


def test_duplicate_aliases_are_not_first_match_wins() -> None:
    result = _run(BODY + "\n## Required checks\n\n```text\ngit status\n```\n")
    assert "issue_duplicate_section" in _codes(result)


def test_historical_shell_placeholder_is_rejected_before_approval() -> None:
    result = _run(BODY.replace("git diff --check", "git diff --name-only <base_sha>..<exact_head_sha>"))
    assert "issue_shell_command_forbidden" in _codes(result)
    assert result["readiness"] == "NEEDS_REVISION"
    _assert_no_authority(result)


@pytest.mark.parametrize("command", ["echo x && echo y", "echo x; echo y", "echo x | cat", "echo `x`", "echo $(x)", "echo ${X}"])
def test_all_existing_shell_metacharacter_denials_are_reused(command: str) -> None:
    assert "issue_shell_command_forbidden" in _codes(_run(BODY.replace("git diff --check", command)))


def test_multiple_independent_defects_are_reported_together() -> None:
    body = BODY.replace("git diff --check", "echo x; echo y").replace(BRANCH, "main").replace(BASE, "not-a-sha")
    codes = _codes(_run(body))
    assert {"issue_shell_command_forbidden", "work_branch_is_integration_branch", "base_sha_invalid"} <= codes


@pytest.mark.parametrize("path", ["../escape.py", "/absolute.py", "C:/host/file.py", "**", "*", "./", "a/../../b"])
def test_unsafe_paths_fail(path: str) -> None:
    result = _run(BODY.replace("launch_nerelan.bat\n", path + "\n"))
    assert result["readiness"] == "NEEDS_REVISION"
    _assert_no_authority(result)


@pytest.mark.parametrize("path", ["AGENTS.md", "reverse_agent/control_plane/path_a.py", ".github/workflows/ci.yml", "pyproject.toml", ".env", "host/secrets/token.txt", "key.pem"])
def test_declared_r1_scope_is_checked_against_current_risk_floor(path: str) -> None:
    result = _run(BODY.replace("launch_nerelan.bat\n", path + "\n"))
    assert "path_risk_exceeds_r1" in _codes(result)


@pytest.mark.parametrize("path", ["frontend/**", "docs/*.md", "src/file?.py", "src/[ab].py"])
def test_offline_glob_coverage_is_unknown_not_ready(path: str) -> None:
    assert "path_scope_requires_expansion" in _codes(_run(BODY.replace("launch_nerelan.bat\n", path + "\n")))


def test_duplicate_normalized_paths_are_diagnosed() -> None:
    body = BODY.replace("launch_nerelan.bat\n", "launch_nerelan.bat\n./launch_nerelan.bat\n")
    assert "duplicate_allowed_path" in _codes(_run(body))


def test_occupied_path_observation_is_conservative_and_non_authorizing() -> None:
    assert _run(occupied_paths=["other.txt"])["readiness"] == "APPROVAL_READY"
    result = _run(occupied_paths=["LAUNCH_NERELAN.BAT"])
    assert "occupied_path_overlap" in _codes(result)
    assert "observed_base_mismatch" in _codes(_run(observed_base_sha="c" * 40))
    _assert_no_authority(result)


@pytest.mark.parametrize("occupied", ["not-a-list", ["../escape"], ["docs/**"], [42]])
def test_invalid_occupancy_input_is_not_ignored(occupied: object) -> None:
    assert _run(occupied_paths=occupied)["readiness"] == "NEEDS_REVISION"


@pytest.mark.parametrize("branch", ["main", "HEAD", "refs/heads/a", "-option", "a..b", "a.lock", "a/.hidden", "a b", "a@{1}", "a\\b", "a?b"])
def test_invalid_work_branch_is_not_ready(branch: str) -> None:
    assert _run(BODY.replace(BRANCH, branch))["readiness"] == "NEEDS_REVISION"


def test_snapshot_is_optional_but_when_present_must_match() -> None:
    result = _run(pr_body=_snapshot(), issue_number=1033, observed_head_sha=HEAD)
    assert result["readiness"] == "APPROVAL_READY", result
    assert result["snapshot_parsed"] is True
    _assert_no_authority(result)
    for fields in ({"base_sha": "c" * 40}, {"target_branch": "owner/other"}, {"issue_number": 1034}, {"exact_head_sha": "d" * 40}):
        failed = _run(pr_body=_snapshot(**fields), issue_number=1033, observed_head_sha=HEAD)
        assert "snapshot_binding_mismatch" in _codes(failed)


def test_changed_body_cannot_reuse_a_stale_snapshot() -> None:
    result = _run(BODY + "\nMaterial change.\n", pr_body=_snapshot())
    assert "snapshot_binding_mismatch" in _codes(result)


def test_candidate_cannot_embed_an_approval_snapshot() -> None:
    assert "candidate_contains_snapshot" in _codes(_run(BODY + _snapshot()))
    assert "candidate_contains_snapshot" in _codes(_run(BODY + "\n```text\nrepository: other/repo\n```\n"))


def test_missing_fence_cannot_borrow_next_sections_block() -> None:
    body = BODY.replace("## Allowed paths\n\n```text\nlaunch_nerelan.bat\n```", "## Allowed paths\n\nlaunch_nerelan.bat")
    assert "section_requires_one_text_block" in _codes(_run(body))


def test_heading_inside_fence_is_ambiguous_not_ready() -> None:
    body = BODY + "\n```python\n## Allowed paths\nwrong.py\n```\n"
    assert "section_heading_inside_fence" in _codes(_run(body))
    assert "unclosed_fence" in _codes(_run(BODY + "\n```text\nunclosed\n"))


def test_required_check_selection_reuses_repository_owned_mapping(tmp_path: Path) -> None:
    body = BODY.replace("launch_nerelan.bat\n", "reverse_agent/platform_v1/run_read_model.py\n")
    result = _run(body)
    assert result["selected_checks"] == [path_a.PLATFORM_V1_CHECK]
    assert result["readiness"] == "APPROVAL_READY"
    missing = _run(body, repo_root=tmp_path)
    assert "mapped_test_target_missing" in _codes(missing)
    (tmp_path / "tests/platform_v1").mkdir(parents=True)
    assert _run(body, repo_root=tmp_path)["readiness"] == "APPROVAL_READY"


def test_no_issue_command_or_live_api_is_executed(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("preflight attempted execution or external observation")
    monkeypatch.setattr(path_a.subprocess, "run", forbidden)
    monkeypatch.setattr(path_a.subprocess, "check_output", forbidden)
    monkeypatch.setattr(path_a, "_github_get", forbidden)
    monkeypatch.setattr(path_a.urllib.request, "urlopen", forbidden)
    result = _run(BODY.replace("git diff --check", "python dangerous_program.py"))
    assert result["readiness"] == "APPROVAL_READY"
    assert "dangerous_program.py" not in json.dumps(result)
    _assert_no_authority(result)


@pytest.mark.parametrize("body,code", [
    (None, "input_not_text"), ("x" * (preflight.MAX_INPUT_BYTES + 1), "input_too_large"),
    ("中" * preflight.MAX_INPUT_BYTES, "input_too_large"), ("\ud800", "input_not_utf8"),
    (BODY + "\x00", "input_control_character"),
])
def test_input_bounds_and_encoding(body: object, code: str) -> None:
    result = _run(body)
    assert code in _codes(result)
    assert result["readiness"] == "NEEDS_REVISION"
    _assert_no_authority(result)


def test_reports_never_echo_untrusted_prose_or_command_values() -> None:
    sentinel = "PRIVATE_SENTINEL_do_not_echo_123456"
    result = _run(BODY.replace("git diff --check", "echo " + sentinel + ";"))
    assert sentinel not in json.dumps(result)


def test_diagnostics_are_bounded() -> None:
    paths = [f"reverse_agent/control_plane/module{i}.py" for i in range(preflight.MAX_PATHS)]
    result = _run(BODY.replace("launch_nerelan.bat\n", "\n".join(paths) + "\n"))
    assert len(result["diagnostics"]) <= preflight.MAX_DIAGNOSTICS
    assert result["diagnostics_truncated"] is True
    assert result["readiness"] == "NEEDS_REVISION"


def test_cli_uses_real_file_and_json_without_mutation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "issue.md"
    source.write_text(BODY, encoding="utf-8")
    original = source.read_bytes()
    assert preflight.main(["--issue-body-file", str(source), "--repository", REPOSITORY]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["readiness"] == "APPROVAL_READY"
    _assert_no_authority(result)
    assert source.read_bytes() == original
    source.write_text(BODY.replace("git diff --check", "cat <file>"), encoding="utf-8")
    assert preflight.main(["--issue-body-file", str(source), "--repository", REPOSITORY]) == 1
    assert "issue_shell_command_forbidden" in _codes(json.loads(capsys.readouterr().out))


@pytest.mark.parametrize("kind", ["missing", "directory", "too_large", "invalid_utf8"])
def test_cli_invalid_files_are_bounded_errors(kind: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "input.md"
    if kind == "directory":
        source.mkdir()
    elif kind == "too_large":
        source.write_bytes(b"x" * (preflight.MAX_INPUT_BYTES + 1))
    elif kind == "invalid_utf8":
        source.write_bytes(b"\xff\xfe")
    assert preflight.main(["--issue-body-file", str(source), "--repository", REPOSITORY]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["readiness"] == "NEEDS_REVISION"
    assert _codes(result) == {"input_file_unreadable_or_invalid"}
    _assert_no_authority(result)


@pytest.mark.parametrize("repo", ["", "owner", "https://github.com/a/b", "a/..", "a/b c", None])
def test_repository_input_is_validated(repo: object) -> None:
    result = preflight.preflight_work_item(BODY, repository=repo)
    assert "repository_invalid" in _codes(result)
    _assert_no_authority(result)


@pytest.mark.parametrize("field,value", [("observed_base_sha", "x"), ("observed_head_sha", 42), ("issue_number", True), ("issue_number", 0), ("repo_root", "not-a-Path")])
def test_invalid_optional_observations_fail(field: str, value: object) -> None:
    result = _run(**{field: value})
    assert result["readiness"] == "NEEDS_REVISION"
    _assert_no_authority(result)


def test_no_test_target_presence_claim_without_checked_targets(tmp_path: Path) -> None:
    assert _run(repo_root=tmp_path)["test_targets_present"] is False
    body = BODY.replace("launch_nerelan.bat\n", "reverse_agent/platform_v1/run_read_model.py\n")
    assert _run(body)["test_targets_present"] is False
    assert _run(body, repo_root=tmp_path)["test_targets_present"] is False
    (tmp_path / "tests/platform_v1").mkdir(parents=True)
    assert _run(body, repo_root=tmp_path)["test_targets_present"] is True


def test_optional_allowed_operations_cannot_hide_ambiguity() -> None:
    section = "\n## Allowed operations\n\n```text\nread\n```\n"
    assert _run(BODY + section)["readiness"] == "APPROVAL_READY"
    assert "issue_duplicate_section" in _codes(_run(BODY + section + section))
    assert "issue_privileged_operation_forbidden" in _codes(_run(BODY + section.replace("\nread\n", "\nmerge\n")))


@pytest.mark.parametrize("path", [".git/config", "src/.git/config", "a./b", "name.\n", "a:stream"])
def test_nonportable_or_git_metadata_paths_are_not_ready(path: str) -> None:
    assert _run(BODY.replace("launch_nerelan.bat\n", path.rstrip("\n") + "\n"))["readiness"] == "NEEDS_REVISION"


def test_noncanonical_fence_cannot_be_reported_ready() -> None:
    body = BODY.replace("```text\nlaunch_nerelan.bat\n```", "````text\nlaunch_nerelan.bat\n````")
    assert "section_requires_one_text_block" in _codes(_run(body))


def test_cli_refuses_symlink_using_handle_type_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Inject lstat metadata rather than requiring platform-specific symlink
    # creation privileges. The production read must refuse before os.open.
    import stat
    from types import SimpleNamespace
    monkeypatch.setattr(Path, "lstat", lambda self: SimpleNamespace(st_mode=stat.S_IFLNK, st_size=0))
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("symlink input must not be opened")
    monkeypatch.setattr(preflight.os, "open", forbidden)
    assert preflight.main(["--issue-body-file", str(tmp_path / "link"), "--repository", REPOSITORY]) == 2
    _assert_no_authority(json.loads(capsys.readouterr().out))
