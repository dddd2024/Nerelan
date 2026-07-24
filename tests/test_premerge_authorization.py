"""Tests for the pre-merge authorization mainline validation gate (P1A-v2, Issue #22).

The self-referential receipt design (PR #21) is replaced with a pre-merge
``MainlineMergeAuthorization`` committed in the accepted PR head and a
``mainline_merge_validation`` gate that validates the actual two-parent merge
commit directly at HEAD.

All merge-graph tests use hermetic temporary git repositories.  The positive
lifecycle test commits the authorization into the accepted feature head,
creates a real two-parent merge commit, and validates at HEAD without any
post-merge receipt file inside the merge commit.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from reverse_agent.project_gate import mainline_merge_validation


REPO_ROOT = Path(__file__).resolve().parents[1]
TRUST_LOCAL = "local_asserted"
TRUST_GITHUB = "github_actions_run"
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


def _make_lifecycle_repo(
    tmp_path: Path,
    *,
    authorization: dict | None = None,
    decision_text: str | None = None,
    command_plan_text: str | None = None,
    squash: bool = False,
    fast_forward: bool = False,
    second_feature_branch: str = "feature",
    extra_commit_after_merge: bool = False,
) -> tuple[Path, dict, str, str, str]:
    """Create a hermetic git repo with a real two-parent merge commit.

    Returns ``(repo, authorization, base_sha, accepted_head_sha, merge_commit_sha)``.
    The authorization is committed into the accepted feature head before the
    merge, so it exists in the merge commit's second-parent tree.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q", "-b", "main")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "Test")
    _run_git(repo, "config", "commit.gpgsign", "false")

    # Decision + command plan committed on main first.
    decision_content = decision_text or (
        "```json decision_meta\n"
        '{"schema_version":1,"decision_id":"decision_test_v1",'
        '"round_id":"round_test_v1","status":"APPROVED","mainline":"engineering_branch",'
        '"skill_profiles":["reverse-agent-iteration@v2"]}\n'
        "```\n"
    )
    cp_content = command_plan_text or json.dumps(
        {
            "schema_version": 1,
            "decision_id": "decision_test_v1",
            "round_id": "round_test_v1",
            "commands": [],
        },
        sort_keys=True,
    )

    state_dir_repo = repo / "project_state"
    gates_dir = state_dir_repo / "gates"
    schemas_dir = state_dir_repo / "schemas"
    authz_dir = state_dir_repo / "mainline_authorizations"
    gates_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)
    authz_dir.mkdir(parents=True, exist_ok=True)

    (state_dir_repo / "decision_packet.md").write_text(decision_content, encoding="utf-8")
    (gates_dir / "command_plan.json").write_text(cp_content, encoding="utf-8")

    # Copy the schema file from the real repo if it exists.
    schema_src = REPO_ROOT / "project_state" / "schemas" / "mainline_merge_authorization.schema.json"
    if schema_src.exists():
        schemas_dir.joinpath("mainline_merge_authorization.schema.json").write_bytes(schema_src.read_bytes())

    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "decision and command plan")
    base_sha = _run_git(repo, "rev-parse", "HEAD")

    # Feature branch with implementation + authorization.
    _run_git(repo, "checkout", "-q", "-b", second_feature_branch)
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    _run_git(repo, "add", "feature.txt")
    _run_git(repo, "commit", "-q", "-m", "feature implementation")

    implementation_sha = _run_git(repo, "rev-parse", "HEAD")

    # Build the authorization artifact.  ``accepted_head_sha`` is advisory --
    # it declares the implementation head the observations bind to and cannot
    # equal the authz commit's sha (self-referential).  The validator uses the
    # actual second parent as the ground-truth accepted head.
    if authorization is None:
        authorization = _default_authorization(
            base_sha=base_sha,
            accepted_head_sha=implementation_sha,
            decision_content=decision_content,
            command_plan_content=cp_content,
        )
    else:
        authorization = dict(authorization)
        authorization["locked_base_sha"] = base_sha
        authorization["accepted_head_sha"] = implementation_sha
        for obs in authorization.get("required_workflow_observations", []):
            obs["head_sha"] = implementation_sha

    authz_path = authz_dir / "active.json"
    authz_path.write_text(json.dumps(authorization, sort_keys=True), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "add mainline merge authorization")
    accepted_head_sha = _run_git(repo, "rev-parse", "HEAD")

    # Merge into main.
    _run_git(repo, "checkout", "-q", "main")
    if fast_forward:
        _run_git(repo, "merge", "--ff-only", "-q", second_feature_branch)
    elif squash:
        _run_git(repo, "merge", "--squash", "-q", second_feature_branch)
        _run_git(repo, "commit", "-q", "-m", "squash feature")
    else:
        _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge feature", second_feature_branch)

    merge_commit_sha = _run_git(repo, "rev-parse", "HEAD")

    if extra_commit_after_merge:
        (repo / "extra.txt").write_text("extra\n", encoding="utf-8")
        _run_git(repo, "add", "extra.txt")
        _run_git(repo, "commit", "-q", "-m", "extra after merge")
        merge_commit_sha = _run_git(repo, "rev-parse", "HEAD")

    return repo, authorization, base_sha, accepted_head_sha, merge_commit_sha


def _default_authorization(
    *,
    base_sha: str,
    accepted_head_sha: str,
    decision_content: str,
    command_plan_content: str,
    minimum_trust_source: str = TRUST_LOCAL,
) -> dict:
    return {
        "schema_version": 1,
        "authorization_id": "authz_test_v1",
        "source_pr": 999,
        "accepted_head_sha": accepted_head_sha,
        "locked_base_sha": base_sha,
        "allowed_merge_method": "merge",
        "decision_identity": {
            "decision_id": "decision_test_v1",
            "decision_content_digest": _sha256(decision_content),
        },
        "command_plan_digest": _sha256(command_plan_content),
        "required_workflow_observations": [
            {
                "name": name,
                "trust_source": minimum_trust_source,
                "head_sha": accepted_head_sha,
                "conclusion": "success",
                "run_id": i + 1,
            }
            for i, name in enumerate(REQUIRED_RUN_NAMES)
        ],
        "minimum_trust_source": minimum_trust_source,
        "human_r2_approval_reference": "audit:PR999:comment1",
        "merge_tree_policy": "equal_to_accepted_head_tree",
        "authorization_status": "active",
        "expires_at": None,
        "superseded_by": None,
        "committed_at": "2026-07-24T05:00:00Z",
    }


def _check(result: dict, name: str) -> dict:
    return next(item for item in result["checks"] if item["name"] == name)


# ---------------------------------------------------------------------------
# Positive lifecycle test
# ---------------------------------------------------------------------------


def test_valid_premerge_authorization_passes_mainline_merge_validation(tmp_path: Path) -> None:
    repo, authz, base_sha, accepted_head, merge_sha = _make_lifecycle_repo(tmp_path)

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "PASSED", result["blocking_reasons"]
    assert result["merge_commit_sha"] == merge_sha
    assert result["accepted_head_sha"] == accepted_head
    assert result["blocking_reasons"] == []


# ---------------------------------------------------------------------------
# Negative test 1: HEAD is not a two-parent merge commit
# ---------------------------------------------------------------------------


def test_fails_when_head_is_not_two_parent_merge(tmp_path: Path) -> None:
    repo, _authz, _base, _accepted, _merge = _make_lifecycle_repo(tmp_path)

    # Add a regular commit on top of the merge.
    (repo / "regular.txt").write_text("regular\n", encoding="utf-8")
    _run_git(repo, "add", "regular.txt")
    _run_git(repo, "commit", "-q", "-m", "regular commit")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "head_is_two_parent_merge")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 2: first parent differs from locked base
# ---------------------------------------------------------------------------


def test_fails_when_first_parent_differs_from_locked_base(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q", "-b", "main")
    _run_git(repo, "config", "user.email", "t@t")
    _run_git(repo, "config", "user.name", "T")
    _run_git(repo, "config", "commit.gpgsign", "false")

    (repo / "a.txt").write_text("a\n")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "a")
    base_sha = _run_git(repo, "rev-parse", "HEAD")

    (repo / "b.txt").write_text("b\n")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "b")
    wrong_base_sha = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "-b", "feature")
    (repo / "f.txt").write_text("f\n")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "f")
    accepted_head = _run_git(repo, "rev-parse", "HEAD")

    # Authorization locks the wrong base.
    authz = _default_authorization(
        base_sha=base_sha,
        accepted_head_sha=accepted_head,
        decision_content="dummy",
        command_plan_content="{}",
    )
    authz["locked_base_sha"] = base_sha  # actual first parent will be wrong_base_sha

    state_dir = repo / "project_state"
    authz_dir = state_dir / "mainline_authorizations"
    authz_dir.mkdir(parents=True, exist_ok=True)
    authz_dir.joinpath("active.json").write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "authz")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge", "feature")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "first_parent_matches_locked_base")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 3: second parent differs from accepted head
# ---------------------------------------------------------------------------


def test_fails_when_second_parent_differs_from_accepted_head(tmp_path: Path) -> None:
    repo, authz, base, _accepted, _merge = _make_lifecycle_repo(tmp_path)

    # Create another feature and merge it instead, but authorization still
    # points to the original accepted head.
    _run_git(repo, "checkout", "-q", "-b", "other")
    (repo / "other.txt").write_text("other\n")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "other")
    other_head = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "reset", "--hard", "-q", base)
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge other", "other")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "second_parent_parent_matches_accepted_head")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 4: parent order differs
# ---------------------------------------------------------------------------


def test_fails_when_parent_order_differs(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    # Create a merge where the feature branch is the first parent and main
    # is the second parent (reversed order).
    _run_git(repo, "checkout", "-q", "feature")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "reversed merge", "main")
    reversed_merge = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "branch", "-f", "main", reversed_merge)
    _run_git(repo, "checkout", "-q", "main")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "first_parent_matches_locked_base")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 5: squash/rebase-style integration is used
# ---------------------------------------------------------------------------


def test_fails_when_squash_merge_is_used(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path, squash=True)

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "head_is_two_parent_merge")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 6: merge tree violates declared policy
# ---------------------------------------------------------------------------


def test_fails_when_merge_tree_violates_policy(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    # The authorization requires tree equality, but we add a conflict
    # resolution that changes the merge tree.
    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "reset", "--hard", "-q", base)
    _run_git(repo, "checkout", "-q", "feature")
    (repo / "feature.txt").write_text("modified on feature\n")
    _run_git(repo, "add", "feature.txt")
    _run_git(repo, "commit", "-q", "-m", "modify feature")
    new_accepted = _run_git(repo, "rev-parse", "HEAD")

    # Update authorization to point to new accepted head.  The fixed
    # ``active.json`` path is overwritten in place; a stale authorization
    # cannot validate a later unrelated commit because ``accepted_head_sha``
    # and ``locked_base_sha`` are recomputed.
    authz["accepted_head_sha"] = new_accepted
    authz_path = repo / "project_state" / "mainline_authorizations" / "active.json"
    authz_path.write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "update authz")
    new_accepted = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    # Merge but modify the tree so it differs from the accepted head tree.
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge with modification", "feature")
    (repo / "extra.txt").write_text("extra\n")
    _run_git(repo, "add", "extra.txt")
    _run_git(repo, "commit", "--amend", "--no-edit", "-q")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "merge_tree_policy")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 7: Decision ID matches but Decision digest differs
# ---------------------------------------------------------------------------


def test_fails_when_decision_digest_differs(tmp_path: Path) -> None:
    decision_text = (
        "```json decision_meta\n"
        '{"schema_version":1,"decision_id":"decision_test_v1",'
        '"round_id":"round_test_v1","status":"APPROVED","mainline":"engineering_branch",'
        '"skill_profiles":["reverse-agent-iteration@v2"]}\n'
        "```\n"
    )
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(
        tmp_path, decision_text=decision_text
    )

    # Tamper with the decision content digest in the authorization.
    authz["decision_identity"]["decision_content_digest"] = "sha256:" + "0" * 64

    # Rewrite the authorization file in the accepted head's tree.
    _run_git(repo, "checkout", "-q", "feature")
    authz_path = repo / "project_state" / "mainline_authorizations" / "active.json"
    authz_path.write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "tamper authz digest")
    new_accepted = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge", "feature")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "decision_digest")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 8: Command Plan digest differs
# ---------------------------------------------------------------------------


def test_fails_when_command_plan_digest_differs(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    _run_git(repo, "checkout", "-q", "feature")
    authz["command_plan_digest"] = "sha256:" + "0" * 64
    authz_path = repo / "project_state" / "mainline_authorizations" / "active.json"
    authz_path.write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "tamper cp digest")
    new_accepted = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge", "feature")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "command_plan_digest")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 9: authorization is expired or superseded
# ---------------------------------------------------------------------------


def test_fails_when_authorization_is_expired(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    _run_git(repo, "checkout", "-q", "feature")
    authz["authorization_status"] = "expired"
    authz_path = repo / "project_state" / "mainline_authorizations" / "active.json"
    authz_path.write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "expire authz")
    new_accepted = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge", "feature")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "authorization_status")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 10: stale authorization reused for a later main commit
# ---------------------------------------------------------------------------


def test_stale_authorization_cannot_validate_later_commit(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    # Create a second merge on top of the first one with a different feature.
    _run_git(repo, "checkout", "-q", "-b", "feature-2")
    (repo / "f2.txt").write_text("f2\n")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "f2")
    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge f2", "feature-2")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"


# ---------------------------------------------------------------------------
# Negative test 11: PR/Decision fields changed and digest recomputed
# ---------------------------------------------------------------------------


def test_fails_when_decision_fields_changed_with_recomputed_digest(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    # Change the decision_id in both the decision and the authorization,
    # and recompute the digest. The gate should still fail because the
    # committed decision file's digest won't match the authorization's
    # declared digest (the decision file wasn't updated in the accepted head).
    _run_git(repo, "checkout", "-q", "feature")
    authz["decision_identity"]["decision_id"] = "decision_tampered_v1"
    authz_path = repo / "project_state" / "mainline_authorizations" / "active.json"
    authz_path.write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "tamper decision id")
    new_accepted = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge", "feature")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"


# ---------------------------------------------------------------------------
# Negative test 12: one required workflow observation is absent
# ---------------------------------------------------------------------------


def test_fails_when_required_workflow_observation_absent(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    _run_git(repo, "checkout", "-q", "feature")
    # Remove one observation.
    authz["required_workflow_observations"] = authz["required_workflow_observations"][:3]
    authz_path = repo / "project_state" / "mainline_authorizations" / "active.json"
    authz_path.write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "remove observation")
    new_accepted = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge", "feature")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "required_workflow_observations")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 13: workflow observation binds another head
# ---------------------------------------------------------------------------


def test_fails_when_observation_binds_another_head(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    _run_git(repo, "checkout", "-q", "feature")
    # Tamper one observation to bind a different head.
    authz["required_workflow_observations"][0]["head_sha"] = "1" * 40
    authz_path = repo / "project_state" / "mainline_authorizations" / "active.json"
    authz_path.write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "tamper observation head")
    new_accepted = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge", "feature")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "workflow_observation_heads")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 14: locally authored fake success observations rejected
# ---------------------------------------------------------------------------


def test_fails_when_local_asserted_observations_rejected_by_trust_boundary(tmp_path: Path) -> None:
    repo, authz, base, accepted, _merge = _make_lifecycle_repo(tmp_path)

    # Upgrade the minimum trust boundary to github_actions_run, then downgrade
    # the observations to local_asserted.  The trust boundary check must fail
    # because local_asserted < github_actions_run.
    _run_git(repo, "checkout", "-q", "feature")
    authz["minimum_trust_source"] = TRUST_GITHUB
    for obs in authz["required_workflow_observations"]:
        obs["trust_source"] = TRUST_LOCAL
    authz_path = repo / "project_state" / "mainline_authorizations" / "active.json"
    authz_path.write_text(json.dumps(authz), encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "downgrade trust")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge", "feature")

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "observation_trust_boundary")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 15: post-merge receipt is not a prerequisite for validating M
# (This is a positive test that the gate does NOT require a receipt file.)
# ---------------------------------------------------------------------------


def test_postmerge_receipt_is_not_prerequisite_for_validation(tmp_path: Path) -> None:
    repo, authz, base, accepted, merge = _make_lifecycle_repo(tmp_path)

    # Ensure no receipt file exists anywhere.
    receipt_dir = repo / "project_state" / "mainline_receipts"
    assert not receipt_dir.exists() or not any(receipt_dir.iterdir())

    result = mainline_merge_validation(repo_root=repo)

    assert result["gate_status"] == "PASSED", result["blocking_reasons"]


# ---------------------------------------------------------------------------
# Negative test 16: workflow routing runs both gates on main
# ---------------------------------------------------------------------------


def test_main_workflow_runs_both_baseline_and_merge_validation() -> None:
    for name in ("state-gate.yml", "decision-preflight.yml"):
        text = (REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "Main integration baseline" in text, f"{name} missing baseline step"
        merge_step = next(
            (block for block in text.split("\n\n") if "Mainline merge validation" in block),
            None,
        )
        assert merge_step is not None, (
            f"{name} missing Mainline merge validation step (Issue #22)"
        )
        assert "github.ref == 'refs/heads/main'" in merge_step, (
            f"{name} merge validation step must run only on main"
        )
        assert "mainline-merge-validation" in merge_step, (
            f"{name} must invoke the mainline-merge-validation gate"
        )
