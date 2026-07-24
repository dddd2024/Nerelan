"""Tests for the post-merge ``MainlineIntegrationReceipt`` audit output (P1A-v2, Issue #22).

The receipt is an *output* emitted after the merge -- it is NOT a prerequisite
for :func:`mainline_merge_validation`.  It records the actual merge commit,
ordered parents, trees, and observation references so a later audit can
reconstruct what was validated without re-running the gate.

Key semantics tested here (Issue #22 finding: self-referential receipt):

1. The receipt can be emitted while the merge commit is at HEAD.
2. The receipt can be emitted from a *later* commit that stores the receipt,
   referencing the merge commit by SHA.  The validator does not require
   ``receipt_commit_HEAD == receipt.merge_commit_sha``.
3. ``mainline_merge_validation`` passes regardless of whether a receipt exists.
4. The receipt captures the full merge-graph identity: merge SHA, both parents,
   both trees, authorization id, decision identity, and observation references.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from reverse_agent.project_gate import (
    emit_mainline_integration_receipt,
    mainline_merge_validation,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TRUST_LOCAL = "local_asserted"
REQUIRED_RUN_NAMES = (
    "CI",
    "Decision Preflight",
    "State Gate (pull_request)",
    "State Gate (push)",
)


def _run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _make_merged_repo(tmp_path: Path) -> tuple[Path, dict, str, str, str]:
    """Create a hermetic repo with a valid two-parent merge commit at HEAD.

    Returns ``(repo, authorization, base_sha, accepted_head_sha, merge_commit_sha)``.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q", "-b", "main")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "Test")
    _run_git(repo, "config", "commit.gpgsign", "false")

    decision_content = (
        "```json decision_meta\n"
        '{"schema_version":1,"decision_id":"decision_receipt_v1",'
        '"round_id":"round_receipt_v1","status":"APPROVED","mainline":"engineering_branch",'
        '"skill_profiles":["reverse-agent-iteration@v2"]}\n'
        "```\n"
    )
    cp_content = json.dumps(
        {
            "schema_version": 1,
            "decision_id": "decision_receipt_v1",
            "round_id": "round_receipt_v1",
            "commands": [],
        },
        sort_keys=True,
    )

    state_dir = repo / "project_state"
    gates_dir = state_dir / "gates"
    schemas_dir = state_dir / "schemas"
    authz_dir = state_dir / "mainline_authorizations"
    gates_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)
    authz_dir.mkdir(parents=True, exist_ok=True)

    (state_dir / "decision_packet.md").write_text(decision_content, encoding="utf-8")
    (gates_dir / "command_plan.json").write_text(cp_content, encoding="utf-8")

    schema_src = REPO_ROOT / "project_state" / "schemas" / "mainline_merge_authorization.schema.json"
    if schema_src.exists():
        schemas_dir.joinpath("mainline_merge_authorization.schema.json").write_bytes(schema_src.read_bytes())

    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "decision and command plan")
    base_sha = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "-b", "feature")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    _run_git(repo, "add", "feature.txt")
    _run_git(repo, "commit", "-q", "-m", "feature implementation")
    implementation_sha = _run_git(repo, "rev-parse", "HEAD")

    authorization = {
        "schema_version": 1,
        "authorization_id": "authz_receipt_v1",
        "source_pr": 888,
        "accepted_head_sha": implementation_sha,
        "locked_base_sha": base_sha,
        "allowed_merge_method": "merge",
        "decision_identity": {
            "decision_id": "decision_receipt_v1",
            "decision_content_digest": _sha256(decision_content),
        },
        "command_plan_digest": _sha256(cp_content),
        "required_workflow_observations": [
            {
                "name": name,
                "trust_source": TRUST_LOCAL,
                "head_sha": implementation_sha,
                "conclusion": "success",
                "run_id": i + 1,
            }
            for i, name in enumerate(REQUIRED_RUN_NAMES)
        ],
        "minimum_trust_source": TRUST_LOCAL,
        "human_r2_approval_reference": "audit:PR888:comment1",
        "merge_tree_policy": "equal_to_accepted_head_tree",
        "authorization_status": "active",
        "expires_at": None,
        "superseded_by": None,
        "committed_at": "2026-07-24T06:00:00Z",
    }

    authz_path = authz_dir / "active.json"
    authz_path.write_text(json.dumps(authorization, sort_keys=True), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "add mainline merge authorization")
    accepted_head_sha = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge feature", "feature")
    merge_commit_sha = _run_git(repo, "rev-parse", "HEAD")

    return repo, authorization, base_sha, accepted_head_sha, merge_commit_sha


# ---------------------------------------------------------------------------
# Positive: receipt emitted from merge commit at HEAD
# ---------------------------------------------------------------------------


def test_emit_receipt_from_merge_head(tmp_path: Path) -> None:
    repo, authz, base, accepted, merge_sha = _make_merged_repo(tmp_path)

    receipt = emit_mainline_integration_receipt(repo_root=repo)

    assert receipt["schema_version"] == 1
    assert receipt["merge_commit_sha"] == merge_sha
    assert receipt["first_parent_sha"] == base
    assert receipt["second_parent_sha"] == accepted
    assert receipt["accepted_head_sha"] == accepted
    assert receipt["locked_base_sha"] == base
    assert receipt["authorization_id"] == authz["authorization_id"]
    assert receipt["decision_identity"]["decision_id"] == "decision_receipt_v1"
    assert receipt["validation_status"] == "PASSED"
    assert receipt["emitted_at"]
    # Trees are captured for audit reconstruction.
    assert receipt["merge_tree_sha"]
    assert receipt["accepted_head_tree_sha"]
    # Observation references are carried forward.
    obs_refs = receipt["observation_references"]
    assert len(obs_refs) == 4
    assert {o["name"] for o in obs_refs} == set(REQUIRED_RUN_NAMES)


# ---------------------------------------------------------------------------
# Positive: receipt emitted from a LATER commit referencing the merge
# ---------------------------------------------------------------------------


def test_emit_receipt_from_later_commit_references_merge(tmp_path: Path) -> None:
    repo, authz, base, accepted, merge_sha = _make_merged_repo(tmp_path)

    # Add a later commit on top of the merge (e.g. storing the receipt).
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    _run_git(repo, "add", "later.txt")
    _run_git(repo, "commit", "-q", "-m", "later commit storing receipt")
    later_head = _run_git(repo, "rev-parse", "HEAD")
    assert later_head != merge_sha

    receipt = emit_mainline_integration_receipt(repo_root=repo, merge_commit_sha=merge_sha)

    assert receipt["merge_commit_sha"] == merge_sha
    assert receipt["first_parent_sha"] == base
    assert receipt["second_parent_sha"] == accepted
    assert receipt["validation_status"] == "PASSED"
    # The receipt's own commit context is recorded but does not equal the merge.
    assert receipt["receipt_context_sha"] == later_head


# ---------------------------------------------------------------------------
# Negative: validation passes without any receipt file
# ---------------------------------------------------------------------------


def test_validation_passes_without_receipt_file(tmp_path: Path) -> None:
    repo, _authz, _base, _accepted, _merge = _make_merged_repo(tmp_path)

    # Ensure no receipt directory exists.
    receipt_dir = repo / "project_state" / "mainline_receipts"
    assert not receipt_dir.exists() or not any(receipt_dir.iterdir())

    result = mainline_merge_validation(repo_root=repo)
    assert result["gate_status"] == "PASSED", result["blocking_reasons"]


# ---------------------------------------------------------------------------
# Negative: receipt cannot be emitted for a non-merge commit
# ---------------------------------------------------------------------------


def test_receipt_rejected_for_non_merge_commit(tmp_path: Path) -> None:
    repo, _authz, _base, _accepted, _merge = _make_merged_repo(tmp_path)

    # Add a regular commit on top of the merge.
    (repo / "regular.txt").write_text("regular\n", encoding="utf-8")
    _run_git(repo, "add", "regular.txt")
    _run_git(repo, "commit", "-q", "-m", "regular commit")
    regular_sha = _run_git(repo, "rev-parse", "HEAD")

    receipt = emit_mainline_integration_receipt(repo_root=repo, merge_commit_sha=regular_sha)

    assert receipt["receipt_status"] == "BLOCKED"
    assert receipt["validation_status"] == "BLOCKED"
    assert "head_is_not_two_parent_merge" in receipt["blocking_reasons"][0]


# ---------------------------------------------------------------------------
# Negative: receipt cannot be emitted for a merge that fails validation
# ---------------------------------------------------------------------------


def test_receipt_records_blocked_validation(tmp_path: Path) -> None:
    repo, authz, base, accepted, merge_sha = _make_merged_repo(tmp_path)

    # Tamper: reset main to base and merge a different branch carrying the
    # stale authz, so validation fails.
    _run_git(repo, "checkout", "-q", "-b", "other")
    (repo / "other.txt").write_text("other\n", encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "other")
    other_head = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "reset", "--hard", "-q", base)
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge other", "other")
    bad_merge = _run_git(repo, "rev-parse", "HEAD")

    receipt = emit_mainline_integration_receipt(repo_root=repo, merge_commit_sha=bad_merge)

    assert receipt["receipt_status"] == "BLOCKED"
    assert receipt["validation_status"] == "BLOCKED"
    assert receipt["merge_commit_sha"] == bad_merge
    assert receipt["blocking_reasons"]


# ---------------------------------------------------------------------------
# Schema conformance
# ---------------------------------------------------------------------------


def test_receipt_conforms_to_schema(tmp_path: Path) -> None:
    repo, _authz, _base, _accepted, _merge = _make_merged_repo(tmp_path)

    receipt = emit_mainline_integration_receipt(repo_root=repo)

    schema_path = REPO_ROOT / "project_state" / "schemas" / "mainline_integration_receipt.schema.json"
    assert schema_path.exists(), "mainline_integration_receipt.schema.json must exist"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Lightweight schema validation: check required fields are present.
    for field in schema.get("required", []):
        assert field in receipt, f"receipt missing required field: {field}"
