"""Tests for the current-merge mainline validation gate (P1A, Issue #20).

The historical ``integration-baseline`` gate only proves the frozen PR #9 merge
remains in ancestry.  ``current_merge_validation`` binds the *current* ``main``
HEAD to an accepted merge receipt so that a later, unrelated commit on ``main``
cannot pass merely because the old merge is still an ancestor.

All merge-graph tests use hermetic temporary git repositories instead of the
live repository history.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from reverse_agent.project_gate import current_merge_validation


REPO_ROOT = Path(__file__).resolve().parents[1]


def _receipt_digest(receipt: dict) -> str:
    """Deterministic SHA-256 over the identity fields of a merge receipt."""

    identity = json.dumps(
        {
            "source_pr": receipt["source_pr"],
            "decision_identity": receipt["decision_identity"],
            "base_sha": receipt["base_sha"],
            "accepted_head_sha": receipt["accepted_head_sha"],
            "merge_commit_sha": receipt["merge_commit_sha"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(identity).hexdigest()


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


def _make_merge_repo(tmp_path: Path) -> tuple[Path, dict, dict]:
    """Create a hermetic git repo with a synthetic merge commit.

    Returns ``(repo, receipt, state_dir)`` where ``receipt`` carries the real
    SHAs from the synthetic repo and ``state_dir`` is the project_state path
    that already contains the schema and the written receipt.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q", "-b", "main")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "Test")
    _run_git(repo, "config", "commit.gpgsign", "false")

    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _run_git(repo, "add", "README.md")
    _run_git(repo, "commit", "-q", "-m", "base")
    base_sha = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "-b", "feature")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    _run_git(repo, "add", "feature.txt")
    _run_git(repo, "commit", "-q", "-m", "feature")
    subject_sha = _run_git(repo, "rev-parse", "HEAD")
    subject_tree = _run_git(repo, "show", "-s", "--format=%T", subject_sha)

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge feature", "feature")
    merge_sha = _run_git(repo, "rev-parse", "HEAD")
    merge_tree = _run_git(repo, "show", "-s", "--format=%T", merge_sha)

    receipt = {
        "schema_version": 1,
        "receipt_id": "test_merge_v1",
        "source_pr": 999,
        "decision_identity": "decision_test_v1",
        "base_sha": base_sha,
        "accepted_head_sha": subject_sha,
        "merge_commit_sha": merge_sha,
        "ordered_parent_shas": [base_sha, subject_sha],
        "accepted_head_tree_sha": subject_tree,
        "merge_tree_sha": merge_tree,
        "require_tree_equality": True,
        "required_exact_head_runs": [
            {"name": "CI", "run_id": 1, "head_sha": subject_sha, "conclusion": "success"},
            {"name": "Decision Preflight", "run_id": 2, "head_sha": subject_sha, "conclusion": "success"},
            {"name": "State Gate (pull_request)", "run_id": 3, "head_sha": subject_sha, "conclusion": "success"},
            {"name": "State Gate (push)", "run_id": 4, "head_sha": subject_sha, "conclusion": "success"},
        ],
        "observed_at": "2026-07-24T03:00:00Z",
    }
    receipt["receipt_digest"] = _receipt_digest(receipt)

    state_dir = _write_state(tmp_path, receipt)
    return repo, receipt, state_dir


def _write_state(tmp_path: Path, receipt: dict, *, receipt_name: str | None = None) -> Path:
    """Write the schema + receipt into a fresh project_state tree."""

    state_dir = tmp_path / "project_state"
    receipts_dir = state_dir / "mainline_receipts"
    schema_dir = state_dir / "schemas"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)

    schema_path = REPO_ROOT / "project_state" / "schemas" / "mainline_integration_receipt.schema.json"
    schema_dir.joinpath("mainline_integration_receipt.schema.json").write_bytes(schema_path.read_bytes())

    name = receipt_name or f"{receipt['merge_commit_sha']}.json"
    receipts_dir.joinpath(name).write_text(json.dumps(receipt), encoding="utf-8")
    return state_dir


def _check(result: dict, name: str) -> dict:
    return next(item for item in result["checks"] if item["name"] == name)


# ---------------------------------------------------------------------------
# Positive test
# ---------------------------------------------------------------------------


def test_valid_receipt_passes_current_merge_validation(tmp_path: Path) -> None:
    repo, receipt, state_dir = _make_merge_repo(tmp_path)

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "PASSED", result["blocking_reasons"]
    assert result["merge_commit_sha"] == receipt["merge_commit_sha"]
    assert result["accepted_head_sha"] == receipt["accepted_head_sha"]
    assert result["blocking_reasons"] == []


# ---------------------------------------------------------------------------
# Negative test 1: HEAD is only a descendant of the old baseline, not the
# recorded current merge.  After the recorded merge, a new unrelated commit
# lands on main; HEAD no longer equals the recorded merge commit and no
# receipt exists for the new HEAD.
# ---------------------------------------------------------------------------


def test_fails_closed_when_head_is_descendant_but_not_recorded_merge(tmp_path: Path) -> None:
    repo, _receipt, state_dir = _make_merge_repo(tmp_path)

    # Add an unrelated commit after the recorded merge.
    (repo / "extra.txt").write_text("extra\n", encoding="utf-8")
    _run_git(repo, "add", "extra.txt")
    _run_git(repo, "commit", "-q", "-m", "extra unrelated commit")

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert any("no_receipt_for_head" in reason for reason in result["blocking_reasons"])


# ---------------------------------------------------------------------------
# Negative test 2: second parent differs from accepted PR head.
# ---------------------------------------------------------------------------


def test_fails_when_second_parent_differs_from_accepted_head(tmp_path: Path) -> None:
    repo, receipt, _state_dir = _make_merge_repo(tmp_path)

    # Build a different feature branch and re-merge so the second parent
    # differs from the accepted head.
    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "checkout", "-q", "-b", "other-feature")
    (repo / "other.txt").write_text("other\n", encoding="utf-8")
    _run_git(repo, "add", "other.txt")
    _run_git(repo, "commit", "-q", "-m", "other feature")
    other_sha = _run_git(repo, "rev-parse", "HEAD")

    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "reset", "--hard", "-q", receipt["base_sha"])
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge other", "other-feature")
    bad_merge_sha = _run_git(repo, "rev-parse", "HEAD")

    tampered = dict(receipt)
    tampered["merge_commit_sha"] = bad_merge_sha
    tampered["ordered_parent_shas"] = [receipt["base_sha"], other_sha]
    tampered["merge_tree_sha"] = _run_git(repo, "show", "-s", "--format=%T", bad_merge_sha)
    tampered["receipt_digest"] = _receipt_digest(tampered)
    state_dir = _write_state(tmp_path, tampered, receipt_name=f"{bad_merge_sha}.json")

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "second_parent_matches_accepted_head")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 3: parent order differs.
# ---------------------------------------------------------------------------


def test_fails_when_parent_order_differs(tmp_path: Path) -> None:
    repo, receipt, _state_dir = _make_merge_repo(tmp_path)

    swapped = dict(receipt)
    swapped["ordered_parent_shas"] = [receipt["accepted_head_sha"], receipt["base_sha"]]
    state_dir = _write_state(tmp_path, swapped, receipt_name=f"{receipt['merge_commit_sha']}.json")

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "parent_order")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 4: merge tree differs from accepted subject tree.
# ---------------------------------------------------------------------------


def test_fails_when_merge_tree_differs_from_accepted_subject_tree(tmp_path: Path) -> None:
    repo, receipt, _state_dir = _make_merge_repo(tmp_path)

    tampered = dict(receipt)
    tampered["merge_tree_sha"] = "0" * 40
    state_dir = _write_state(tmp_path, tampered, receipt_name=f"{receipt['merge_commit_sha']}.json")

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "tree_identity")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 5: receipt names a different PR or Decision.
# ---------------------------------------------------------------------------


def test_fails_when_receipt_names_different_pr_or_decision(tmp_path: Path) -> None:
    repo, receipt, _state_dir = _make_merge_repo(tmp_path)

    tampered = dict(receipt)
    tampered["source_pr"] = 1111
    tampered["decision_identity"] = "decision_other_v1"
    state_dir = _write_state(tmp_path, tampered, receipt_name=f"{receipt['merge_commit_sha']}.json")

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "receipt_identity")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 6: exact-head run names or head SHA differ.
# ---------------------------------------------------------------------------


def test_fails_when_exact_head_run_head_sha_differs(tmp_path: Path) -> None:
    repo, receipt, _state_dir = _make_merge_repo(tmp_path)

    tampered = dict(receipt)
    tampered_runs = [dict(run) for run in receipt["required_exact_head_runs"]]
    tampered_runs[0]["head_sha"] = "1" * 40
    tampered["required_exact_head_runs"] = tampered_runs
    state_dir = _write_state(tmp_path, tampered, receipt_name=f"{receipt['merge_commit_sha']}.json")

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "exact_head_runs")["status"] == "FAIL"


def test_fails_when_required_run_name_missing(tmp_path: Path) -> None:
    repo, receipt, _state_dir = _make_merge_repo(tmp_path)

    tampered = dict(receipt)
    tampered_runs = [dict(run) for run in receipt["required_exact_head_runs"]]
    tampered_runs[0]["name"] = "Wrong Name"
    tampered["required_exact_head_runs"] = tampered_runs
    state_dir = _write_state(tmp_path, tampered, receipt_name=f"{receipt['merge_commit_sha']}.json")

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "required_run_names")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Negative test 7: stale receipt is reused for a later main commit.
# ---------------------------------------------------------------------------


def test_stale_receipt_cannot_validate_later_main_commit(tmp_path: Path) -> None:
    repo, receipt, state_dir = _make_merge_repo(tmp_path)

    # Create a second merge on top of the first one.
    _run_git(repo, "checkout", "-q", "-b", "feature-2")
    (repo / "feature2.txt").write_text("feature2\n", encoding="utf-8")
    _run_git(repo, "add", "feature2.txt")
    _run_git(repo, "commit", "-q", "-m", "feature 2")
    _run_git(repo, "checkout", "-q", "main")
    _run_git(repo, "merge", "--no-ff", "-q", "-m", "merge feature 2", "feature-2")
    # HEAD is now a new merge commit, but the receipt directory only has the
    # old merge commit receipt.

    result = current_merge_validation(state_dir=state_dir, repo_root=repo)

    assert result["gate_status"] == "BLOCKED"
    assert any("no_receipt_for_head" in reason for reason in result["blocking_reasons"])


# ---------------------------------------------------------------------------
# Negative test 8: main workflow runs the historical invariant but omits the
# current-merge validation.  This is a workflow routing test.
# ---------------------------------------------------------------------------


def test_main_workflow_runs_both_baseline_and_current_merge_validation() -> None:
    for name in ("state-gate.yml", "decision-preflight.yml"):
        text = (REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        baseline_block = next(
            (block for block in text.split("\n\n") if "Main integration baseline" in block),
            None,
        )
        current_merge_block = next(
            (block for block in text.split("\n\n") if "Current merge validation" in block),
            None,
        )
        assert baseline_block is not None, f"{name} missing Main integration baseline step"
        assert current_merge_block is not None, (
            f"{name} missing Current merge validation step (Issue #20 blocking finding)"
        )
        assert "github.ref == 'refs/heads/main'" in current_merge_block, (
            f"{name} current-merge step must run only on main"
        )
        assert "current-merge-validation" in current_merge_block, (
            f"{name} current-merge step must invoke the current-merge-validation gate"
        )
