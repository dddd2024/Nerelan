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


def test_plan_task_keeps_routing_traits_with_required_artifacts():
    # Regression: _normalize_task built PlannedTask(task_id=...) but the field is id.
    planned=GoalService._normalize_task(
        {"title":"Reviewer","instruction":"Inspect","id":"T009","difficulty":4,"kind":"analysis",
         "context_need":1000,"needs":["tool_use"],"required_artifacts":[REQUIRED]},seq=0)
    assert planned.id=="T009"
    assert (planned.difficulty,planned.kind,planned.context_need,planned.needs)==(4,"analysis",1000,("tool_use",))
    assert planned.required_artifacts==(REQUIRED,)


@pytest.mark.parametrize("extra",[
    {"capability":"validate_task"},
    {"validation_command_id":"git_diff_check","capability":"validate_task"},
])
def test_plan_rejects_review_artifact_on_non_standalone_tasks(extra):
    with pytest.raises(TaskStoreError):
        GoalService._normalize_task({"title":"Reviewer","instruction":"Report","id":"T001",
                                     "required_artifacts":[REQUIRED],**extra},seq=0)


def test_tampered_contract_does_not_become_legacy_success(tmp_path):
    store,task,workspace,_=setup_case(tmp_path,report())
    detail=next(ref["detail"] for ref in store.get_task(task.id).evidence_refs
                if ref.get("category")=="RequiredReviewArtifactContract")
    store._conn.execute("UPDATE task_evidence SET detail=? WHERE task_id=? AND category=?",
                        (detail.replace(SHA,"b"*40),task.id,"RequiredReviewArtifactContract"))
    cmd,code,reason,_=run_task_validation(store,task.id,worktree=workspace)
    assert cmd=="required_review_artifact" and code!=0
    assert reason=="required_artifact_contract_tampered"


def test_required_artifacts_survive_real_sqlite_close_reopen_and_service_rebuild(tmp_path):
    from datetime import datetime, timedelta, timezone
    from reverse_agent.platform_v1.autonomy import AutonomyService
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    from reverse_agent.platform_v1.control_store import PlatformControlStore

    db=str(tmp_path/"platform.sqlite3")
    now=datetime.now(timezone.utc)
    store=TaskStore(db)
    try:
        control=PlatformControlStore(store)
        goals=GoalService(store=store,control_store=control)
        window=AutonomyService(control_store=control,capabilities=CapabilityRegistry()).activate({
            "policy_id":"owner-window-1","policy_revision":1,"owner_identity":"owner@example",
            "starts_at":(now-timedelta(seconds=5)).isoformat(),"expires_at":(now+timedelta(hours=1)).isoformat(),
            "repositories":["dddd2024/reverse-agent"],"capabilities":["execute_task","validate_task"],
            "max_concurrent_tasks":2,"max_tasks":10,"max_retries":1,"confirmation":"ACTIVATE"})
        goal=goals.create({"objective":"Produce an exact-head review report",
                           "repository":"dddd2024/reverse-agent","idempotency_key":"required-report-reopen",
                           "executor_kind":"deterministic_fixture","orchestration_mode":"single"})
        goals.plan(goal.id,expected_revision=1,tasks=[{
            "id":"T001","title":"Reviewer","instruction":"Inspect and report",
            "difficulty":4,"kind":"analysis","context_need":1000,"needs":["tool_use"],
            "required_artifacts":[REQUIRED]}])
        goals.approve(goal.id,expected_revision=1,policy_ref="owner-window-1")
        goals.launch(goal.id,expected_revision=1,window_id=window.id)
        task_id=control.list_goal_tasks(goal.id)[0]["task_id"]
        frozen=load_required_artifacts(store.get_task(task_id))
    finally:
        store._conn.close()

    store=TaskStore(db)
    try:
        control=PlatformControlStore(store)
        goals=GoalService(store=store,control_store=control)
        reopened=control.get_goal(goal.id)
        assert reopened.tasks[0]["required_artifacts"]==[REQUIRED]
        plan_task=goals._normalize_task(reopened.tasks[0],seq=0)
        assert plan_task.required_artifacts==(REQUIRED,)
        assert (plan_task.difficulty,plan_task.kind,plan_task.context_need,plan_task.needs)==(
            4,"analysis",1000,("tool_use",))
        contract=load_required_artifacts(store.get_task(task_id))
        assert contract==frozen and contract["task_id"]==task_id and contract["files"]==[REQUIRED]
        assert (contract["goal_id"],contract["goal_revision"])==(goal.id,reopened.revision)
        # Re-freezing the same plan task is idempotent after reconstruction.
        freeze_required_artifacts(store,store.get_task(task_id),goal=reopened,plan_task=plan_task)
        # A replacement task freezes its own copy, as the escalation path does.
        replacement=store.create_task(title="Reviewer retry",executor_kind="deterministic_fixture")
        freeze_required_artifacts(store,replacement,goal=reopened,plan_task=plan_task)
        replacement_id=replacement.id
    finally:
        store._conn.close()

    store=TaskStore(db)
    try:
        repo=tmp_path/"repo"
        repo.mkdir()
        subprocess.run(["git","init",str(repo)],capture_output=True,check=True)
        for tid in (task_id,replacement_id):
            contract=load_required_artifacts(store.get_task(tid))
            assert contract["task_id"]==tid and contract["files"]==[REQUIRED]
            cmd,code,_,_=run_task_validation(store,tid,worktree=repo)
            assert cmd=="required_review_artifact" and code!=0
        (repo/"review_evidence").mkdir()
        (repo/"review_evidence"/"review.md").write_text(report(),encoding="utf-8")
        cmd,code,_,_=run_task_validation(store,replacement_id,worktree=repo)
        assert cmd=="git_diff_check" and code==0
    finally:
        store._conn.close()


MARKER = "Nerelan-Review: ACCEPT " + SHA
LIMIT = 128 * 1024


@pytest.mark.parametrize("bad", [
    # Reproductions from independent REVIEW REJECT at a4836900.
    "<script>\n" + MARKER + "\n</script>",
    "<style>\n" + MARKER + "\n</style>",
    "`\n" + MARKER + "\n`",
    "``\n" + MARKER + "\n``",
    "<script/>\n" + MARKER + "\n</script>\n",
    "`\r\n" + MARKER + "\r\n`\r\n",
    "Notes `\n<script>\n`\n" + MARKER + "\n</script>\n",
])
def test_raw_text_or_multiline_code_span_never_passes_full_validation(tmp_path, bad):
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(bad.encode("utf-8"))
    assert validate_required_artifacts(store.get_task(task.id), workspace)[0] is False
    command, status, reason, _ = run_task_validation(store, task.id, worktree=workspace)
    assert command == "required_review_artifact"
    assert status != 0
    assert reason.startswith("review_")


def test_closed_literal_examples_then_genuine_marker_pass_full_validation(tmp_path):
    doc = ("Independent evidence: reviewed exact-head source.\n"
           "<script>\n" + MARKER + "\n</script>\n"
           "<style>\n" + MARKER + "\n</style>\n"
           "Inline `example\n" + MARKER + "\n` and ``other\n" + MARKER + "\n``.\n"
           "<!-- " + MARKER + " -->\n"
           "```text\n" + MARKER + "\n```\n"
           "<pre>\n" + MARKER + "\n</pre>\n"
           "Current review:\n" + MARKER + "\n")
    store, task, workspace, _ = setup_case(tmp_path, doc)
    assert validate_required_artifacts(store.get_task(task.id), workspace) == (
        True, "required_review_artifact_present")
    command, code, _, _ = run_task_validation(store, task.id, worktree=workspace)
    assert command == "git_diff_check" and code == 0


def _sized_report(size):
    body = report().encode("utf-8")
    return b"x" * (size - len(body) - 1) + b"\n" + body


def test_report_at_exact_byte_limit_passes(tmp_path):
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(_sized_report(LIMIT))
    assert path.stat().st_size == LIMIT
    assert validate_required_artifacts(store.get_task(task.id), workspace) == (
        True, "required_review_artifact_present")


def test_report_one_byte_over_limit_is_oversized(tmp_path):
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(_sized_report(LIMIT + 1))
    assert validate_required_artifacts(store.get_task(task.id), workspace) == (
        False, "artifact_empty_or_oversized")


def test_report_with_malformed_utf8_is_rejected(tmp_path):
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(report().encode("utf-8") + b"\xff\xfe\n")
    assert validate_required_artifacts(store.get_task(task.id), workspace) == (
        False, "required_artifact_missing_or_invalid")


def test_growth_after_size_check_is_refused_by_bounded_actual_read(tmp_path, monkeypatch):
    store, task, workspace, path = setup_case(tmp_path, report())
    target = path.resolve()
    assert target.stat().st_size < LIMIT
    grown = (report() + "x" * LIMIT + "\n").encode("utf-8")
    original_open = Path.open
    opened, requests, observed = [], [], []

    class RecordingHandle:
        def __init__(self, handle):
            self._handle = handle

        def __enter__(self):
            self._handle.__enter__()
            return self

        def __exit__(self, *exc):
            return self._handle.__exit__(*exc)

        def read(self, size=-1, /):
            requests.append(size)
            data = self._handle.read(size)
            observed.append(len(data))
            return data

        def __getattr__(self, name):
            return getattr(self._handle, name)

    def grow_then_open(self, *args, **kwargs):
        if not opened and Path(self).resolve() == target:
            # Actual growth lands after the validator's stat() size check and
            # before the file is opened and read.
            with open(target, "wb") as handle:
                handle.write(grown)
            opened.append(target.stat().st_size)
            return RecordingHandle(original_open(self, *args, **kwargs))
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", grow_then_open)
    result = validate_required_artifacts(store.get_task(task.id), workspace)
    assert opened and opened[0] == len(grown) > LIMIT + 1
    assert result == (False, "artifact_empty_or_oversized")
    # Every read request is bounded: never unbounded and at most one
    # overflow-detection byte past the cap.
    assert requests and all(type(size) is int and 0 < size <= LIMIT + 1 for size in requests)
    assert sum(observed) == LIMIT + 1


def test_actual_unquoted_duplicate_verdicts_remain_ambiguous(tmp_path):
    doc = ("Nerelan-Review: ACCEPT " + SHA + "\n"
           "Nerelan-Review: WITHHELD " + SHA + "\n")
    store, task, workspace, _ = setup_case(tmp_path, doc)
    command, code, reason, _ = run_task_validation(store, task.id, worktree=workspace)
    assert command == "required_review_artifact"
    assert code != 0
    assert reason == "review_verdict_missing_or_ambiguous"


STALE = "Nerelan-Review: ACCEPT " + "b" * 40


@pytest.mark.parametrize("bad", [
    # Reproduction from independent REVIEW REJECT at ef658f6e.
    "<blockquote>\n" + MARKER + "\n</blockquote>\n",
    "<blockquote>\n<blockquote>\n" + STALE + "\n</blockquote>\n" + MARKER + "\n</blockquote>\n",
    "<q>\n" + MARKER + "\n</q>\n",
    "Notes `\n<blockquote>\n`\n" + MARKER + "\n</blockquote>\n",
    "<blockquote/>\n" + MARKER + "\n",
    "<blockquote />\n" + MARKER + "\n",
    "<pre/>\n" + MARKER + "\n",
    "<code/>\n" + MARKER + "\n",
])
def test_html_quotation_or_self_closing_container_never_passes_full_validation(tmp_path, bad):
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(bad.encode("utf-8"))
    assert validate_required_artifacts(store.get_task(task.id), workspace)[0] is False
    command, status, reason, _ = run_task_validation(store, task.id, worktree=workspace)
    assert command == "required_review_artifact"
    assert status != 0
    assert reason.startswith("review_")


@pytest.mark.parametrize("prefix", [
    "<blockquote>\n<blockquote>\n" + MARKER + "\n</blockquote>\n" + STALE + "\n</blockquote>\n",
    "<!-- note --><blockquote cite=\"\n</blockquote>\n\">\n" + MARKER + "\n</blockquote>\n",
    "Use `<blockquote>` and `<q>` inline.\n",
    "See `quoted <blockquote>\n" + MARKER + "\n</blockquote>` end\n",
    "```html\n<blockquote>\n" + MARKER + "\n```\n",
    "<blockquote/>\n" + STALE + "\n</blockquote>\n",
    "<pre />\n" + MARKER + "\n</pre>\n",
    "<code/>\n" + MARKER + "\n</code>\n",
])
def test_genuine_marker_after_closed_quotation_passes_full_validation(tmp_path, prefix):
    doc = "Independent evidence: reviewed exact-head source.\n" + prefix + MARKER + "\n"
    store, task, workspace, _ = setup_case(tmp_path, doc)
    assert validate_required_artifacts(store.get_task(task.id), workspace) == (
        True, "required_review_artifact_present")
    command, code, _, _ = run_task_validation(store, task.id, worktree=workspace)
    assert command == "git_diff_check" and code == 0


# Regression from independent REJECT at 7d31e90c: quote syntax inside a closed
# HTML attribute or code span must not quote the genuine marker after it.
@pytest.mark.parametrize("doc,expected", [
    ('<span title="\n> template\n">\n' + MARKER + "\n", True),
    ("<span title='\n> template\n'>\n" + MARKER + "\n", True),
    ('<span title="\n> template\n">\n\n' + MARKER + "\n", True),
    ('<span title="\n> template\n' + MARKER + '\n">\n', False),
    ('<span title="quoted > template">\n' + MARKER + "\n", True),
    ('<span title="\n> literal\n">\n> real quote\n' + MARKER + "\n", False),
    ("Note `\n> template\n`\n" + MARKER + "\n", True),
    ("Note `\n> literal\n`\n> real quote\n" + MARKER + "\n", False),
], ids=["closed_double_attribute", "closed_single_attribute",
        "closed_attribute_blank_termination", "quoted_marker_inside_attribute",
        "plain_closed_attribute", "real_quote_after_closed_attribute",
        "closed_code_span", "real_quote_after_closed_code_span"])
def test_literal_context_priority_over_markdown_quote_in_full_validation(tmp_path, doc,
                                                                       expected):
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(doc.encode("utf-8"))
    assert validate_required_artifacts(store.get_task(task.id), workspace)[0] is expected
    command, code, reason, _ = run_task_validation(store, task.id, worktree=workspace)
    if expected:
        assert command == "git_diff_check" and code == 0
    else:
        assert command == "required_review_artifact"
        assert code != 0
        assert reason == "review_verdict_missing_or_ambiguous"


# Regression from independent REJECT at 11c328ce: a real quote after a closed
# line-start HTML container is still a quote that hides its lazy marker.
CLOSED_HTML_SEAMS = [
    ("<blockquote>\n> literal\n</blockquote>\n", "blockquote"),
    ("<code>\n> literal\n</code>\n", "code"),
    ("<q>\n> literal\n</q>\n", "q"),
    ("<script>\n> literal\n</script\n>\n", "script_split_close"),
    ("<style>\n> literal\n</style\n>\n", "style_split_close"),
    ("<pre>\n> literal\n</pre\n>\n", "pre_split_close"),
]


@pytest.mark.parametrize("seam", [seam for seam, _ in CLOSED_HTML_SEAMS],
                         ids=[name for _, name in CLOSED_HTML_SEAMS])
@pytest.mark.parametrize("quoted", [True, False], ids=["real_quote", "outside"])
def test_real_quote_after_closed_line_start_html_in_full_validation(tmp_path, seam, quoted):
    doc = seam + ("> real quote\n" if quoted else "") + MARKER + "\n"
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(doc.encode("utf-8"))
    assert validate_required_artifacts(store.get_task(task.id), workspace)[0] is (not quoted)
    command, code, reason, _ = run_task_validation(store, task.id, worktree=workspace)
    if quoted:
        assert command == "required_review_artifact"
        assert code != 0
        assert reason == "review_verdict_missing_or_ambiguous"
    else:
        assert command == "git_diff_check" and code == 0


# Regression from FAILED candidate 55b26f57: a real line-start HTML block
# interrupts an earlier quoted paragraph, so the genuine marker after it is
# live, while a real quote after the closed block still hides its lazy marker.
FAKE_MARKER = "Nerelan-Review: ACCEPT " + "b" * 40
EARLIER_QUOTE = "> Earlier quoted template:\n> " + FAKE_MARKER + "\n"
# <code> and <q> cannot interrupt a paragraph, so they are not listed here.
INTERRUPTING_HTML = [
    ("<pre>\n" + FAKE_MARKER + "\n</pre>\n", "pre"),
    ("<!-- note -->\n", "comment"),
    *[(seam, name) for seam, name in CLOSED_HTML_SEAMS if name not in ("code", "q")],
]


@pytest.mark.parametrize("seam", ["<code>\n> literal\n</code>\n", "<q>\n> literal\n</q>\n"],
                         ids=["code", "q"])
def test_inline_html_after_earlier_quote_stays_quoted_in_full_validation(tmp_path, seam):
    doc = EARLIER_QUOTE + seam + MARKER + "\n"
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(doc.encode("utf-8"))
    assert validate_required_artifacts(store.get_task(task.id), workspace)[0] is False
    command, code, reason, _ = run_task_validation(store, task.id, worktree=workspace)
    assert command == "required_review_artifact"
    assert code != 0
    assert reason == "review_verdict_missing_or_ambiguous"


@pytest.mark.parametrize("seam", [seam for seam, _ in INTERRUPTING_HTML],
                         ids=[name for _, name in INTERRUPTING_HTML])
@pytest.mark.parametrize("quoted", [True, False], ids=["real_quote", "outside"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["lf", "crlf"])
def test_line_start_html_interrupts_earlier_quote_in_full_validation(tmp_path, seam,
                                                                     quoted, newline):
    doc = EARLIER_QUOTE + seam + ("> real quote\n" if quoted else "") + MARKER + "\n"
    doc = doc.replace("\n", newline)
    store, task, workspace, path = setup_case(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(doc.encode("utf-8"))
    assert validate_required_artifacts(store.get_task(task.id), workspace)[0] is (not quoted)
    command, code, reason, _ = run_task_validation(store, task.id, worktree=workspace)
    if quoted:
        assert command == "required_review_artifact"
        assert code != 0
        assert reason == "review_verdict_missing_or_ambiguous"
    else:
        assert command == "git_diff_check" and code == 0
