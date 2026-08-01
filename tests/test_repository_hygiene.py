from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Sequence

import pytest

# Make scripts/ importable (reuses the bounded-args / no-credentials checks).
_SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

# --- Disposition codes (mirror docs/repository-hygiene-report.md) ----------

KEEP_ACTIVE = "KEEP_ACTIVE"
CLOSE_PR_KEEP_BRANCH = "CLOSE_PR_KEEP_BRANCH"
DELETE_REMOTE_SAFE = "DELETE_REMOTE_SAFE"
KEEP_HISTORICAL_UNIQUE = "KEEP_HISTORICAL_UNIQUE"
BLOCKED_DIRTY_WORKTREE = "BLOCKED_DIRTY_WORKTREE"
BLOCKED_UNKNOWN_PROVENANCE = "BLOCKED_UNKNOWN_PROVENANCE"

ALL_DISPOSITIONS = {
    KEEP_ACTIVE, CLOSE_PR_KEEP_BRANCH, DELETE_REMOTE_SAFE,
    KEEP_HISTORICAL_UNIQUE, BLOCKED_DIRTY_WORKTREE, BLOCKED_UNKNOWN_PROVENANCE,
}


@dataclass(frozen=True)
class BranchFacts:
    """Bounded facts about a remote branch, as collected by the hygiene audit."""

    name: str
    is_main: bool
    is_protected: bool
    head_sha: str
    audited_head_sha: str
    has_open_pr: bool
    has_dirty_worktree: bool
    has_locked_worktree: bool
    head_in_main: bool  # is-ancestor of main (fully contained)
    unique_commit_count: int
    unique_history_preserved_by_merged_pr: bool
    owner_drop_remote: bool
    has_authority_issue: bool
    provenance_known: bool


@dataclass(frozen=True)
class WorktreeFacts:
    path: str
    is_main_worktree: bool
    locked: bool
    clean: bool
    has_untracked_important_files: bool
    branch_done_or_superseded: bool
    belongs_to_repo: bool


def classify_branch(facts: BranchFacts) -> str:
    """Apply the Issue #92 section-3/5 disposition rules.

    A branch is only DELETE_REMOTE_SAFE when every deletion condition holds.
    Unique history that is not preserved by a merged PR is NEVER deleted.
    """

    if facts.is_main or facts.is_protected:
        return KEEP_ACTIVE
    if not facts.provenance_known:
        return BLOCKED_UNKNOWN_PROVENANCE
    if facts.has_dirty_worktree or facts.has_locked_worktree:
        return BLOCKED_DIRTY_WORKTREE
    if facts.has_open_pr:
        # Open PR still needs the branch; do not delete.
        return KEEP_ACTIVE if facts.has_authority_issue else CLOSE_PR_KEEP_BRANCH
    if facts.head_sha != facts.audited_head_sha:
        # State drifted since audit; do not delete.
        return BLOCKED_UNKNOWN_PROVENANCE
    if facts.has_authority_issue:
        return KEEP_ACTIVE
    if facts.head_in_main:
        # Fully contained in main; safe to delete (no unique code lost).
        return DELETE_REMOTE_SAFE
    # Branch has unique commits not in main.
    if facts.unique_history_preserved_by_merged_pr and facts.owner_drop_remote:
        return DELETE_REMOTE_SAFE
    return KEEP_HISTORICAL_UNIQUE


def can_delete_branch(facts: BranchFacts) -> tuple[bool, list[str]]:
    """Return (allowed, reasons). Deletion requires all conditions."""

    reasons: list[str] = []
    if facts.is_main or facts.is_protected:
        reasons.append("is_main_or_protected")
    if not facts.provenance_known:
        reasons.append("unknown_provenance")
    if facts.has_open_pr:
        reasons.append("open_pr_present")
    if facts.has_dirty_worktree or facts.has_locked_worktree:
        reasons.append("dirty_or_locked_worktree")
    if facts.head_sha != facts.audited_head_sha:
        reasons.append("head_drifted_since_audit")
    if facts.has_authority_issue:
        reasons.append("authority_issue_present")
    if not facts.head_in_main and not (
        facts.unique_history_preserved_by_merged_pr and facts.owner_drop_remote
    ):
        reasons.append("unique_history_not_preserved")
    return (len(reasons) == 0), reasons


def can_remove_worktree(facts: WorktreeFacts) -> tuple[bool, list[str]]:
    """Return (allowed, reasons). Worktree removal requires all conditions."""

    reasons: list[str] = []
    if facts.is_main_worktree:
        reasons.append("is_main_worktree")
    if facts.locked:
        reasons.append("locked")
    if not facts.clean:
        reasons.append("dirty")
    if facts.has_untracked_important_files:
        reasons.append("untracked_important_files")
    if not facts.branch_done_or_superseded:
        reasons.append("branch_not_done")
    if not facts.belongs_to_repo:
        reasons.append("not_repo_worktree")
    return (len(reasons) == 0), reasons


# --- representative fixtures (reflect the real audit findings) -------------


def _merged_branch(name: str, head: str) -> BranchFacts:
    """A fully-merged branch with no open PR and no worktree."""

    return BranchFacts(
        name=name, is_main=False, is_protected=False, head_sha=head,
        audited_head_sha=head, has_open_pr=False, has_dirty_worktree=False,
        has_locked_worktree=False, head_in_main=True, unique_commit_count=0,
        unique_history_preserved_by_merged_pr=True, owner_drop_remote=True,
        has_authority_issue=False, provenance_known=True,
    )


def _unique_branch(name: str, head: str, unique: int) -> BranchFacts:
    """A branch with unique commits not in main and no merged PR preserving them."""

    return BranchFacts(
        name=name, is_main=False, is_protected=False, head_sha=head,
        audited_head_sha=head, has_open_pr=False, has_dirty_worktree=False,
        has_locked_worktree=False, head_in_main=False, unique_commit_count=unique,
        unique_history_preserved_by_merged_pr=False, owner_drop_remote=False,
        has_authority_issue=False, provenance_known=True,
    )


# --- branch disposition tests ---------------------------------------------


def test_main_branch_is_keep_active() -> None:
    facts = BranchFacts(
        name="main", is_main=True, is_protected=True, head_sha="a" * 40,
        audited_head_sha="a" * 40, has_open_pr=False, has_dirty_worktree=False,
        has_locked_worktree=False, head_in_main=True, unique_commit_count=0,
        unique_history_preserved_by_merged_pr=False, owner_drop_remote=False,
        has_authority_issue=False, provenance_known=True,
    )
    assert classify_branch(facts) == KEEP_ACTIVE
    allowed, _ = can_delete_branch(facts)
    assert not allowed


def test_merged_branch_is_delete_safe() -> None:
    facts = _merged_branch("codex/readme-minimal-integration-pilot-v1", "4ce3c19b")
    assert classify_branch(facts) == DELETE_REMOTE_SAFE
    allowed, reasons = can_delete_branch(facts)
    assert allowed and reasons == []


def test_unique_branch_rejects_deletion() -> None:
    facts = _unique_branch("agent/terminal-status-propagation-seal-restart-rework-v3", "6a286746", 44)
    assert classify_branch(facts) == KEEP_HISTORICAL_UNIQUE
    allowed, reasons = can_delete_branch(facts)
    assert not allowed
    assert "unique_history_not_preserved" in reasons


def test_unique_branch_with_open_pr_closes_pr_keeps_branch() -> None:
    facts = _unique_branch("codex/p1a-v3-exact-head-external-approval", "4baa1c61", 5)
    facts = BranchFacts(
        **{**facts.__dict__, "has_open_pr": True}
    )
    assert classify_branch(facts) == CLOSE_PR_KEEP_BRANCH
    allowed, _ = can_delete_branch(facts)
    assert not allowed


def test_dirty_worktree_blocks_branch_deletion() -> None:
    facts = BranchFacts(
        **{**_merged_branch("codex/some-merged", "a" * 40).__dict__, "has_dirty_worktree": True}
    )
    assert classify_branch(facts) == BLOCKED_DIRTY_WORKTREE
    allowed, reasons = can_delete_branch(facts)
    assert not allowed
    assert "dirty_or_locked_worktree" in reasons


def test_head_drift_blocks_deletion() -> None:
    facts = BranchFacts(
        **{**_merged_branch("codex/some-merged", "a" * 40).__dict__,
           "head_sha": "b" * 40, "audited_head_sha": "a" * 40}
    )
    assert classify_branch(facts) == BLOCKED_UNKNOWN_PROVENANCE
    allowed, reasons = can_delete_branch(facts)
    assert not allowed
    assert "head_drifted_since_audit" in reasons


def test_unknown_provenance_rejects_deletion() -> None:
    facts = BranchFacts(
        **{**_merged_branch("codex/some-merged", "a" * 40).__dict__, "provenance_known": False}
    )
    assert classify_branch(facts) == BLOCKED_UNKNOWN_PROVENANCE
    allowed, reasons = can_delete_branch(facts)
    assert not allowed
    assert "unknown_provenance" in reasons


def test_authority_issue_blocks_deletion() -> None:
    facts = BranchFacts(
        **{**_merged_branch("agent/codex-supervisor-foundation-v0", "16526801").__dict__,
           "has_authority_issue": True}
    )
    # Active supervisor branch backing Issue #92.
    assert classify_branch(facts) == KEEP_ACTIVE
    allowed, reasons = can_delete_branch(facts)
    assert not allowed
    assert "authority_issue_present" in reasons


def test_unique_history_preserved_by_merged_pr_can_delete_if_owner_drops() -> None:
    facts = BranchFacts(
        **{**_unique_branch("codex/material-hook-runtime-validation", "d689c28f", 1).__dict__,
           "unique_history_preserved_by_merged_pr": True, "owner_drop_remote": True}
    )
    assert classify_branch(facts) == DELETE_REMOTE_SAFE
    allowed, _ = can_delete_branch(facts)
    assert allowed


# --- worktree tests --------------------------------------------------------


def test_clean_done_worktree_can_be_removed() -> None:
    facts = WorktreeFacts(
        path="F:/reverse-agent-executor-neutral-vertical-slice-v1",
        is_main_worktree=False, locked=False, clean=True,
        has_untracked_important_files=False, branch_done_or_superseded=True,
        belongs_to_repo=True,
    )
    allowed, reasons = can_remove_worktree(facts)
    assert allowed and reasons == []


def test_main_worktree_not_removed() -> None:
    facts = WorktreeFacts(
        path="F:/reverse-agent", is_main_worktree=True, locked=False, clean=False,
        has_untracked_important_files=True, branch_done_or_superseded=False,
        belongs_to_repo=True,
    )
    allowed, reasons = can_remove_worktree(facts)
    assert not allowed
    assert "is_main_worktree" in reasons


def test_dirty_worktree_not_removed() -> None:
    facts = WorktreeFacts(
        path="F:/reverse-agent-pr60-mainline-landing-repair-v1",
        is_main_worktree=False, locked=False, clean=False,
        has_untracked_important_files=True, branch_done_or_superseded=False,
        belongs_to_repo=True,
    )
    allowed, reasons = can_remove_worktree(facts)
    assert not allowed
    assert "dirty" in reasons
    assert "untracked_important_files" in reasons


def test_locked_worktree_not_removed() -> None:
    facts = WorktreeFacts(
        path="F:/some-locked", is_main_worktree=False, locked=True, clean=True,
        has_untracked_important_files=False, branch_done_or_superseded=True,
        belongs_to_repo=True,
    )
    allowed, reasons = can_remove_worktree(facts)
    assert not allowed
    assert "locked" in reasons


# --- forbidden operations are never sanctioned -----------------------------


@pytest.mark.parametrize("disposition", sorted(ALL_DISPOSITIONS))
def test_no_disposition_authorizes_force_push_or_wildcard_delete(disposition: str) -> None:
    # The disposition vocabulary never carries a "force push" or "wildcard
    # delete" semantics; deletion is only ever DELETE_REMOTE_SAFE and only
    # after per-branch re-verification.
    assert disposition != "FORCE_PUSH"
    assert disposition != "WILDCARD_DELETE"
    assert disposition != "BATCH_DELETE"


def test_delete_safe_requires_per_branch_reverification_fields() -> None:
    # can_delete_branch checks head == audited_head explicitly, modelling the
    # mandatory re-verification (ls-remote + is-ancestor) before each delete.
    facts = _merged_branch("codex/some-merged", "a" * 40)
    allowed, reasons = can_delete_branch(facts)
    assert allowed
    # If the head drifted, the same branch must be blocked.
    drifted = BranchFacts(**{**facts.__dict__, "head_sha": "c" * 40})
    allowed2, reasons2 = can_delete_branch(drifted)
    assert not allowed2
    assert "head_drifted_since_audit" in reasons2


# --- git/gh args bounded + no credentials in scripts -----------------------


def test_supervisor_scripts_have_no_shell_or_credentials() -> None:
    for name in ("supervisor_context.py", "supervisor_validate.py", "supervisor_publish.py"):
        src = (_SCRIPTS / name).read_text(encoding="utf-8")
        assert "shell=True" not in src
        assert "os.environ" not in src
        for token in ("gho_", "ghp_", "Bearer ", "Authorization:", "CHATGPT_SESSION"):
            assert token not in src


def test_supervisor_context_args_are_explicit_lists() -> None:
    import json as _json

    import supervisor_context as sc

    calls: list[list[str]] = []

    def fake_runner(args, timeout):
        calls.append(list(args))
        # Return bounded, valid responses for each git/gh call so that
        # collect_context succeeds and we can inspect all arg lists.
        if args[0] == "git":
            if "symbolic-ref" in args:
                return sc.CommandOutcome(0, "refs/remotes/origin/main", "", False)
            if "rev-parse" in args and "HEAD" in args:
                return sc.CommandOutcome(0, "a" * 40, "", False)
            if "rev-parse" in args:
                return sc.CommandOutcome(0, "16526801bda2a816fc707342f903c1ad037de9bd", "", False)
            if "branch" in args:
                return sc.CommandOutcome(0, "agent/codex-supervisor-foundation-v0", "", False)
            if "status" in args:
                return sc.CommandOutcome(0, "", "", False)
            if "log" in args:
                return sc.CommandOutcome(0, "abcdef0 Title", "", False)
        if args[0] == "gh":
            if args[:2] == ["gh", "api"] and len(args) > 2 and args[2].endswith("/git/refs/heads/main"):
                return sc.CommandOutcome(0, _json.dumps({"object": {"sha": "16526801bda2a816fc707342f903c1ad037de9bd"}}), "", False)
            # v0.3: gh api repos/<repo>/issues (paginated) — replaces gh issue list.
            if args[:2] == ["gh", "api"] and len(args) > 2 and "/issues" in args[2]:
                return sc.CommandOutcome(0, "[]", "", False)
            if args[:2] == ["gh", "pr"] and "list" in args:
                return sc.CommandOutcome(0, "[]", "", False)
            if args[:3] == ["gh", "issue", "view"]:
                return sc.CommandOutcome(0, _json.dumps({"number": 90, "title": "t", "body": "b"}), "", False)
            if args[:3] == ["gh", "pr", "view"]:
                return sc.CommandOutcome(0, _json.dumps({
                    "number": 93, "title": "t", "isDraft": True, "state": "OPEN",
                    "headRefName": "b", "headRefOid": "a" * 40, "baseRefName": "main",
                }), "", False)
            # v0.3: gh api check-runs bound to exact head — replaces gh pr checks.
            if args[:2] == ["gh", "api"] and len(args) > 2 and "/check-runs" in args[2]:
                return sc.CommandOutcome(0, _json.dumps({"total_count": 0, "check_runs": []}), "", False)
        return sc.CommandOutcome(0, "", "", False)

    # v0.3: pass active_pr explicitly so the test focuses on arg bounds and
    # does not depend on branch-derived PR lookup (gh api pulls).
    sc.collect_context("dddd2024/reverse-agent", goal_issue=90, active_pr=93, runner=fake_runner)
    assert calls  # at least one git/gh invocation
    for call in calls:
        assert call[0] in ("git", "gh")
        for arg in call[1:]:
            assert isinstance(arg, str)
            assert all(ch not in arg for ch in ("|", ";", "&", "`", "$("))


def test_hygiene_report_document_exists_and_documents_dispositions() -> None:
    report = pathlib.Path(__file__).resolve().parents[1] / "docs" / "repository-hygiene-report.md"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    for code in ALL_DISPOSITIONS:
        assert code in text
    # No credentials in the report.
    for token in ("gho_", "ghp_", "Bearer ", "Authorization:", "CHATGPT_SESSION"):
        assert token not in text
