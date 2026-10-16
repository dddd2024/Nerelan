"""Opt-in required review report check: process exit 0 is not task success."""
from pathlib import Path
from types import SimpleNamespace
import subprocess

import pytest

from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.required_review_artifact import (
    normalize_required_artifacts, freeze_required_artifacts,
    load_required_artifacts, validate_required_artifacts,
)
from reverse_agent.platform_v1.functional_validation import run_task_validation

SHA = "a" * 40
REQUIRED = {"path": "review_evidence/review.md", "kind": "review_report", "expected_sha": SHA}


def setup_case(tmp_path, artifact=None):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    subprocess.run(["git","init",str(workspace)],capture_output=True,check=True)
    # Current validator is a hygiene command, not functional acceptance.
    store=TaskStore(":memory:")
    task=store.create_task(title="Review PR",executor_kind="opencode")
    goal=SimpleNamespace(id="goal-demo",revision=1)
    plan=SimpleNamespace(required_artifacts=(REQUIRED,))
    freeze_required_artifacts(store,task,goal=goal,plan_task=plan)
    path=workspace/"review_evidence"/"review.md"
    if artifact is not None:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(artifact,encoding="utf-8")
    return store,task,workspace,path


def report(verdict="ACCEPT",sha=SHA):
    return ("Independent evidence: source files and test cases inspected.\n"
            "Checks reproduced: provider-free fixture test.\n"
            f"Nerelan-Review: {verdict} {sha}\n")


def test_missing_review_report_fails_real_validation_even_with_clean_git(tmp_path):
    store,task,workspace,_=setup_case(tmp_path)
    cmd,code,detail,_=run_task_validation(store,task.id,worktree=workspace)
    assert cmd=="required_review_artifact"
    assert code!=0 and "artifact" in detail


def test_withheld_or_rejected_review_does_not_pass(tmp_path):
    for verdict in ("WITHHELD","REJECT"):
        root=tmp_path/verdict
        root.mkdir()
        store,task,workspace,_=setup_case(root, report(verdict))
        _,exit_code,reason,_=run_task_validation(store,task.id,worktree=workspace)
        assert exit_code==1
        assert verdict.lower() in reason


def test_wrong_sha_or_missing_explicit_review_marker_fails(tmp_path):
    for idx,doc in enumerate([report(sha="b"*40), "Tools failed; no source inspection."]):
        root=tmp_path/str(idx)
        root.mkdir()
        store,task,workspace,_=setup_case(root,doc)
        _,exit_code,_,_=run_task_validation(store,task.id,worktree=workspace)
        assert exit_code==1


def test_valid_report_is_not_claim_of_independent_github_review(tmp_path):
    store,task,workspace,_=setup_case(tmp_path,report())
    cmd,code,_,_=run_task_validation(store,task.id,worktree=workspace)
    assert cmd=="git_diff_check" and code==0
    contract=load_required_artifacts(store.get_task(task.id))
    assert contract["files"]==[REQUIRED]


def test_report_outside_workspace_is_rejected(tmp_path):
    store,task,workspace,p=setup_case(tmp_path)
    p.parent.mkdir(exist_ok=True)
    other=tmp_path/"outside.md"
    other.write_text(report(),encoding="utf-8")
    try:
        p.symlink_to(other)
    except (OSError, NotImplementedError):
        pytest.skip("symlink privilege unavailable")
    passed,reason=validate_required_artifacts(store.get_task(task.id),workspace)
    assert not passed
    assert "symlink" in reason


@pytest.mark.parametrize("bad",[
    {"path":"../secrets.txt","kind":"review_report","expected_sha":SHA},
    {"path":"review_evidence/../../outside.md","kind":"review_report","expected_sha":SHA},
    {"path":"review_evidence/a.txt","kind":"review_report","expected_sha":SHA},
    {"path":"review_evidence/x.md","kind":"review_report","expected_sha":"wrong"},
    {"path":"review_evidence/x.md","kind":"arbitrary","expected_sha":SHA},
    {"path":"review_evidence/x.md","kind":"review_report","expected_sha":SHA,"extra":"unsafe"},
])
def test_malformed_contract_is_rejected(bad):
    with pytest.raises(TaskStoreError):
        normalize_required_artifacts([bad])


def test_duplicate_and_over_limit_contract_is_rejected():
    with pytest.raises(TaskStoreError):
        normalize_required_artifacts([REQUIRED,REQUIRED])
    with pytest.raises(TaskStoreError):
        normalize_required_artifacts([REQUIRED]*3)


def test_missing_contract_does_not_break_existing_tasks(tmp_path):
    store=TaskStore(":memory:")
    task=store.create_task(title="ordinary task")
    root=tmp_path/"repo"
    root.mkdir()
    subprocess.run(["git","init",str(root)],capture_output=True,check=True)
    cmd,code,_,_=run_task_validation(store,task.id,worktree=root)
    assert cmd=="git_diff_check" and code==0


def test_plan_rejects_review_artifact_plus_functional_checks():
    task={"title":"Reviewer","instruction":"Report","id":"T001",
          "required_artifacts":[REQUIRED],
          "validation_checks":[{"profile_id":"python_pytest","working_directory":"."}]}
    with pytest.raises(TaskStoreError,match="required_artifacts_require_standalone_execution"):
        GoalService._normalize_task(task,seq=0)


def test_plan_accepts_opt_in_review_and_defaults_not_required():
    valid=GoalService._normalize_task(
        {"title":"Reviewer","instruction":"Inspect","id":"T001","required_artifacts":[REQUIRED]},seq=0)
    assert valid.required_artifacts==(REQUIRED,)
    old=GoalService._normalize_task({"title":"Coder","instruction":"Implement","id":"T002"},seq=1)
    assert old.required_artifacts==()

@pytest.mark.parametrize("bad", [
    # Reproductions from independent REVIEW REJECT at previous exact head:
    "Outcome: WITHHELD. Tools failed; no source inspection or tests.\n"
    "```text\nNerelan-Review: ACCEPT " + SHA + "\n```\n",
    "Outcome: WITHHELD. Tools failed.\n"
    "<!--\nNerelan-Review: ACCEPT " + SHA + "\n-->\n",
    # A real marker cannot overrule contradictory structured status.
    "Decision: REJECT\nNerelan-Review: ACCEPT " + SHA + "\n",
    "## Outcome: WITHHELD\nNerelan-Review: ACCEPT " + SHA + "\n",
    # The fenced example must not count; only a real marker would.
    "Literal example follows:\n~~~text\nNerelan-Review: ACCEPT " + SHA + "\n~~~\n",
    "Quoted verdict:\n> Nerelan-Review: ACCEPT " + SHA + "\n",
    "Literal example:\n    Nerelan-Review: ACCEPT " + SHA + "\n",
    # Unclosed comment/fence is ambiguous and cannot bless an outcome.
    "Nerelan-Review: ACCEPT " + SHA + "\n<!-- partial\n",
    "Nerelan-Review: AC<!-- template -->CEPT " + SHA + "\n",
    "<pre>\nNerelan-Review: ACCEPT " + SHA + "\n</pre>\n",
    "<code>\nNerelan-Review: ACCEPT " + SHA + "\n</code>\n",
    "<pre>\nNerelan-Review: ACCEPT " + SHA + "\n",
    "Nerelan-Review: ACCEPT " + SHA + "\n```text\n",
])
def test_quoted_or_contradictory_accept_never_passes_real_host_validation(tmp_path, bad):
    store, task, workspace, _ = setup_case(tmp_path, bad)
    command, status, reason, _ = run_task_validation(
        store, task.id, worktree=workspace,
    )
    assert command == "required_review_artifact"
    assert status != 0
    assert reason.startswith("review_")


def test_example_marker_plus_actual_top_level_accept_counts_only_real_declaration(tmp_path):
    doc = (
        "Independent evidence: reviewed complete exact-head source.\n"
        "Earlier template example:\n"
        "```text\nNerelan-Review: ACCEPT " + ("b" * 40) + "\n```\n"
        "Current review:\nNerelan-Review: ACCEPT " + SHA + "\n"
    )
    store, task, workspace, _ = setup_case(tmp_path, doc)
    command, code, _, _ = run_task_validation(store, task.id, worktree=workspace)
    assert command == "git_diff_check" and code == 0


def test_actual_unquoted_duplicate_verdicts_remain_ambiguous(tmp_path):
    doc = ("Nerelan-Review: ACCEPT " + SHA + "\n"
           "Nerelan-Review: WITHHELD " + SHA + "\n")
    store, task, workspace, _ = setup_case(tmp_path, doc)
    command, code, reason, _ = run_task_validation(store, task.id, worktree=workspace)
    assert command == "required_review_artifact"
    assert code != 0
    assert reason == "review_verdict_missing_or_ambiguous"
