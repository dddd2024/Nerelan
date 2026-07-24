"""Shared helpers for v3 exact-head external merge approval tests.

These helpers create hermetic git fixtures and fake remote evidence so the
26 required tests from Issue #23 can run without network access or a real
GitHub API.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


# --- SHA constants (40 hex chars, used across fixtures) ---

LOCKED_BASE_SHA = "a" * 40
ACCEPTED_EXACT_HEAD_SHA = "b" * 40
MERGE_COMMIT_SHA = "c" * 40
FIRST_PARENT_SHA = LOCKED_BASE_SHA  # main side of the merge
SECOND_PARENT_SHA = ACCEPTED_EXACT_HEAD_SHA  # PR head side of the merge
WRONG_HEAD_SHA = "d" * 40
WRONG_BASE_SHA = "e" * 40
OTHER_REPO_HEAD_SHA = "f" * 40

DECISION_ID = "decision_20260724_p1a_exact_head_external_merge_approval_rework_v3"
DECISION_CONTENT_DIGEST = "sha256:" + "1" * 64
COMMAND_PLAN_DIGEST = "sha256:" + "2" * 64

REQUIRED_WORKFLOWS = ["CI", "Decision Preflight", "State Gate (pull_request)", "State Gate (push)"]


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- MergeIntent fixture ---

def make_merge_intent(
    *,
    intent_id: str = "intent_v3_001",
    source_pr: int = 23,
    locked_base_sha: str = LOCKED_BASE_SHA,
    allowed_merge_method: str = "merge",
    decision_id: str = DECISION_ID,
    decision_content_digest: str = DECISION_CONTENT_DIGEST,
    command_plan_digest: str = COMMAND_PLAN_DIGEST,
    merge_tree_policy: str = "equal_to_accepted_head_tree",
    expires_at: str | None = "2026-08-24T00:00:00Z",
    max_age_seconds: int = 2592000,
    required_workflows: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "intent_id": intent_id,
        "source_pr": source_pr,
        "locked_base_sha": locked_base_sha,
        "allowed_merge_method": allowed_merge_method,
        "decision_identity": {
            "decision_id": decision_id,
            "decision_content_digest": decision_content_digest,
        },
        "command_plan_digest": command_plan_digest,
        "merge_tree_policy": merge_tree_policy,
        "expiry_policy": {
            "expires_at": expires_at,
            "max_age_seconds": max_age_seconds,
        },
        "required_workflows": required_workflows or REQUIRED_WORKFLOWS,
    }


# --- MergeApprovalAttestation fixture ---

def make_attestation(
    *,
    attestation_id: str = "attestation_v3_001",
    repository: str = "dddd2024/reverse-agent",
    source_pr: int = 23,
    locked_base_sha: str = LOCKED_BASE_SHA,
    accepted_exact_head_sha: str = ACCEPTED_EXACT_HEAD_SHA,
    workflow_observations: list[dict[str, Any]] | None = None,
    approver: str = "dddd2024",
    approval_object_id: str = "issuecomment-12345",
    approval_content_digest: str | None = None,
    content_digest: str | None = None,
    authorization_status: str = "active",
    expires_at: str | None = "2026-08-24T00:00:00Z",
    superseded_by: str | None = None,
    attested_at: str = "2026-07-24T12:00:00Z",
) -> dict[str, Any]:
    if workflow_observations is None:
        workflow_observations = [
            make_workflow_observation(name=name, run_id=1000 + i, head_sha=accepted_exact_head_sha)
            for i, name in enumerate(REQUIRED_WORKFLOWS)
        ]
    if approval_content_digest is None:
        approval_content_digest = sha256_text(approver + approval_object_id)
    if content_digest is None:
        content_digest = sha256_text(attestation_id + accepted_exact_head_sha)
    return {
        "schema_version": 1,
        "attestation_id": attestation_id,
        "repository": repository,
        "source_pr": source_pr,
        "locked_base_sha": locked_base_sha,
        "accepted_exact_head_sha": accepted_exact_head_sha,
        "workflow_observations": workflow_observations,
        "human_r2_approval": {
            "approver": approver,
            "approval_object_id": approval_object_id,
            "approval_content_digest": approval_content_digest,
        },
        "content_digest": content_digest,
        "authorization_status": authorization_status,
        "expires_at": expires_at,
        "superseded_by": superseded_by,
        "attested_at": attested_at,
    }


def _workflow_file_for(name: str) -> str:
    """Derive the workflow file path from a workflow name (matches make_fake_verifier)."""
    slug = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    return f".github/workflows/{slug}.yml"


def make_workflow_observation(
    *,
    name: str = "CI",
    run_id: int = 1001,
    workflow_file: str | None = None,
    event: str = "pull_request",
    run_attempt: int = 1,
    conclusion: str = "success",
    head_sha: str = ACCEPTED_EXACT_HEAD_SHA,
) -> dict[str, Any]:
    return {
        "name": name,
        "run_id": run_id,
        "workflow_file": workflow_file or _workflow_file_for(name),
        "event": event,
        "run_attempt": run_attempt,
        "conclusion": conclusion,
        "head_sha": head_sha,
    }


# --- Fake RemoteAcceptanceVerifier ---

class FakeRemoteAcceptanceVerifier:
    """Hermetic test implementation of the remote acceptance verifier.

    Pre-loaded with fixture data so tests can verify that the production
    gate actually calls the verifier for each run/approval fact.  Tests
    that expect a specific failure simply omit the run/pr/approval from
    the fixture or configure it with mismatched data.
    """

    def __init__(
        self,
        *,
        runs: dict[int, dict[str, Any]] | None = None,
        prs: dict[int, dict[str, Any]] | None = None,
        approvals: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._runs = runs or {}
        self._prs = prs or {}
        self._approvals = approvals or {}
        self.verify_workflow_run_calls: list[dict[str, Any]] = []
        self.verify_pr_calls: list[dict[str, Any]] = []
        self.verify_pr_approval_calls: list[dict[str, Any]] = []

    def verify_workflow_run(
        self,
        *,
        run_id: int,
        expected_head_sha: str,
        expected_workflow_file: str,
        expected_event: str,
        expected_conclusion: str = "success",
    ) -> dict[str, Any]:
        self.verify_workflow_run_calls.append({
            "run_id": run_id,
            "expected_head_sha": expected_head_sha,
            "expected_workflow_file": expected_workflow_file,
            "expected_event": expected_event,
            "expected_conclusion": expected_conclusion,
        })
        run = self._runs.get(run_id)
        if run is None:
            return {"verified": False, "reason": f"run_not_found:{run_id}"}
        if run.get("head_sha") != expected_head_sha:
            return {"verified": False, "reason": "head_sha_mismatch"}
        if run.get("workflow_file") != expected_workflow_file:
            return {"verified": False, "reason": "workflow_file_mismatch"}
        if run.get("event") != expected_event:
            return {"verified": False, "reason": "event_mismatch"}
        if run.get("conclusion") != expected_conclusion:
            return {"verified": False, "reason": f"conclusion_mismatch:{run.get('conclusion')}"}
        if run.get("repository") != "dddd2024/reverse-agent":
            return {"verified": False, "reason": "repository_mismatch"}
        return {"verified": True, "run": run}

    def verify_pr(
        self,
        *,
        pr_number: int,
        expected_head_sha: str,
        expected_base_sha: str,
        expected_repository: str = "dddd2024/reverse-agent",
    ) -> dict[str, Any]:
        self.verify_pr_calls.append({
            "pr_number": pr_number,
            "expected_head_sha": expected_head_sha,
            "expected_base_sha": expected_base_sha,
            "expected_repository": expected_repository,
        })
        pr = self._prs.get(pr_number)
        if pr is None:
            return {"verified": False, "reason": f"pr_not_found:{pr_number}"}
        if pr.get("repository") != expected_repository:
            return {"verified": False, "reason": "repository_mismatch"}
        if pr.get("head_sha") != expected_head_sha:
            return {"verified": False, "reason": "head_sha_mismatch"}
        if pr.get("base_sha") != expected_base_sha:
            return {"verified": False, "reason": "base_sha_mismatch"}
        return {"verified": True, "pr": pr}

    def verify_pr_approval(
        self,
        *,
        pr_number: int,
        approval_reference: str,
        expected_head_sha: str,
        expected_base_sha: str,
        expected_merge_method: str,
        allowed_approvers: list[str],
    ) -> dict[str, Any]:
        self.verify_pr_approval_calls.append({
            "pr_number": pr_number,
            "approval_reference": approval_reference,
            "expected_head_sha": expected_head_sha,
            "expected_base_sha": expected_base_sha,
            "expected_merge_method": expected_merge_method,
            "allowed_approvers": list(allowed_approvers),
        })
        approval = self._approvals.get(approval_reference)
        if approval is None:
            return {"verified": False, "reason": f"approval_not_found:{approval_reference}"}
        if approval.get("approver") not in allowed_approvers:
            return {"verified": False, "reason": f"unauthorized_approver:{approval.get('approver')}"}
        if approval.get("head_sha") != expected_head_sha:
            return {"verified": False, "reason": "head_sha_mismatch"}
        if approval.get("base_sha") != expected_base_sha:
            return {"verified": False, "reason": "base_sha_mismatch"}
        if approval.get("merge_method") != expected_merge_method:
            return {"verified": False, "reason": "merge_method_mismatch"}
        return {"verified": True, "approval": approval}


def make_fake_verifier(
    *,
    head_sha: str = ACCEPTED_EXACT_HEAD_SHA,
    base_sha: str = LOCKED_BASE_SHA,
    source_pr: int = 23,
    runs: dict[int, dict[str, Any]] | None = None,
    prs: dict[int, dict[str, Any]] | None = None,
    approvals: dict[str, dict[str, Any]] | None = None,
) -> FakeRemoteAcceptanceVerifier:
    """Build a verifier pre-loaded with a valid baseline set of evidence."""
    default_runs = {}
    for i, name in enumerate(REQUIRED_WORKFLOWS):
        run_id = 1000 + i
        default_runs[run_id] = {
            "run_id": run_id,
            "name": name,
            "head_sha": head_sha,
            "workflow_file": _workflow_file_for(name),
            "event": "pull_request",
            "run_attempt": 1,
            "conclusion": "success",
            "repository": "dddd2024/reverse-agent",
        }
    default_prs = {
        source_pr: {
            "number": source_pr,
            "repository": "dddd2024/reverse-agent",
            "head_sha": head_sha,
            "base_sha": base_sha,
        }
    }
    default_approvals = {
        "issuecomment-12345": {
            "approver": "dddd2024",
            "head_sha": head_sha,
            "base_sha": base_sha,
            "merge_method": "merge",
        }
    }
    return FakeRemoteAcceptanceVerifier(
        runs=runs if runs is not None else default_runs,
        prs=prs if prs is not None else default_prs,
        approvals=approvals if approvals is not None else default_approvals,
    )


# --- Git fixture helpers ---

def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def create_merge_fixture(
    tmp_path: Path,
    *,
    include_intent: bool = True,
    intent: dict[str, Any] | None = None,
    extra_files_on_head: dict[str, str] | None = None,
    extra_files_after_head: dict[str, str] | None = None,
) -> dict[str, str]:
    """Create a temporary git repo with a two-parent merge commit.

    Returns a dict with keys: ``repo``, ``base_sha``, ``head_sha``,
    ``merge_sha``.
    """
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")

    # Base commit on main (represents locked_base_sha)
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base commit")
    base_sha = _git(repo, "rev-parse", "HEAD")

    # Feature branch with PR head commit
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "feature.txt").write_text("feature work\n", encoding="utf-8")
    if include_intent:
        intent_dir = repo / "project_state" / "mainline_merge_intents"
        intent_dir.mkdir(parents=True, exist_ok=True)
        intent_data = intent or make_merge_intent(locked_base_sha=base_sha)
        # Adjust the intent's locked_base_sha to the real base SHA
        intent_data["locked_base_sha"] = base_sha
        (intent_dir / "active.json").write_text(
            json.dumps(intent_data, indent=2), encoding="utf-8"
        )
    if extra_files_on_head:
        for path, content in extra_files_on_head.items():
            file_path = repo / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "feature head with merge intent")
    head_sha = _git(repo, "rev-parse", "HEAD")

    # Optional: extra commit after the head (should cause validation failure)
    if extra_files_after_head:
        for path, content in extra_files_after_head.items():
            file_path = repo / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "post-head commit (should fail)")
        # head_sha stays as the original feature head; the new HEAD is different

    # Merge commit on main (two parents)
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "--no-ff", "--no-edit", "-q", "feature")
    merge_sha = _git(repo, "rev-parse", "HEAD")

    return {
        "repo": str(repo),
        "base_sha": base_sha,
        "head_sha": head_sha,
        "merge_sha": merge_sha,
    }
