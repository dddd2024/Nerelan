"""Red-phase tests for the v3 exact-head mainline merge lifecycle (Issue #23).

These tests specify ``mainline_merge_validation`` in
``reverse_agent.project_gate``: the gate that binds a real git merge commit to
an externally approved *exact* PR head.  They are expected to FAIL during the
red phase because ``mainline_merge_validation`` (and the
``RemoteAcceptanceVerifier`` contract it depends on) has not been implemented
yet.

The shared helpers in ``tests._v3_helpers`` build hermetic git fixtures and
fake remote evidence so the full lifecycle can be exercised without network
access or a real GitHub API.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from reverse_agent.project_gate import mainline_merge_validation
from tests._v3_helpers import (
    ACCEPTED_EXACT_HEAD_SHA,
    COMMAND_PLAN_DIGEST,
    DECISION_CONTENT_DIGEST,
    DECISION_ID,
    LOCKED_BASE_SHA,
    create_merge_fixture,
    make_attestation,
    make_fake_verifier,
    make_merge_intent,
    sha256_text,
)

VALIDATION_TIME = "2026-07-24T12:00:00Z"


def _git(repo: Path, *args: str) -> str:
    """Run a git command in ``repo`` and return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_final_pr_head_contains_committed_merge_intent(tmp_path):
    """Issue #23 test 1: the PR head commit carries a committed MergeIntent.

    The MergeIntent must be reachable at
    ``project_state/mainline_merge_intents/active.json`` inside the PR head
    (second parent) tree, proving it was committed before the merge rather than
    synthesized after the fact.
    """
    intent = make_merge_intent(
        decision_id=DECISION_ID,
        decision_content_digest=DECISION_CONTENT_DIGEST,
        command_plan_digest=COMMAND_PLAN_DIGEST,
    )
    fixture = create_merge_fixture(tmp_path, intent=intent)
    repo = Path(fixture["repo"])
    head_sha = fixture["head_sha"]
    base_sha = fixture["base_sha"]

    # The fixture must use real git SHAs, not the placeholder constants.
    assert head_sha != ACCEPTED_EXACT_HEAD_SHA
    assert base_sha != LOCKED_BASE_SHA

    intent_text = _git(
        repo, "show", f"{head_sha}:project_state/mainline_merge_intents/active.json"
    )

    assert "locked_base_sha" in intent_text
    assert base_sha in intent_text
    assert DECISION_ID in intent_text
    assert DECISION_CONTENT_DIGEST in intent_text
    assert COMMAND_PLAN_DIGEST in intent_text


def test_remote_observations_bind_exact_final_head(tmp_path):
    """Issue #23 test 2: every workflow observation binds to the exact head.

    When all ``workflow_observations`` report ``head_sha`` equal to the
    attestation's ``accepted_exact_head_sha``, the observation binding check in
    ``mainline_merge_validation`` must pass and the gate must ask the verifier
    to confirm each observation against that exact head.
    """
    fixture = create_merge_fixture(tmp_path)
    repo = Path(fixture["repo"])
    head_sha = fixture["head_sha"]
    base_sha = fixture["base_sha"]
    merge_sha = fixture["merge_sha"]

    attestation = make_attestation(
        locked_base_sha=base_sha,
        accepted_exact_head_sha=head_sha,
    )
    # Precondition: the attestation's content digest is bound to the exact head.
    assert attestation["content_digest"] == sha256_text(
        attestation["attestation_id"] + head_sha
    )
    # Precondition: every observation binds to the accepted exact head.
    for obs in attestation["workflow_observations"]:
        assert obs["head_sha"] == attestation["accepted_exact_head_sha"]

    verifier = make_fake_verifier(head_sha=head_sha, base_sha=base_sha)

    result = mainline_merge_validation(
        repo_root=repo,
        commit_sha=merge_sha,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    # The gate must verify each observation against the accepted exact head.
    assert len(verifier.verify_workflow_run_calls) == len(
        attestation["workflow_observations"]
    )
    for call in verifier.verify_workflow_run_calls:
        assert call["expected_head_sha"] == head_sha

    assert result["gate_status"] == "PASSED"
    assert result["blocking_reasons"] == []


def test_merge_second_parent_equals_accepted_exact_head(tmp_path):
    """Issue #23 test 3: the merge commit's second parent is the accepted head.

    A valid mainline merge must have its second parent (the PR side) pointing
    exactly at ``accepted_exact_head_sha``.  ``mainline_merge_validation`` must
    pass the ``second_parent_identity`` check for such a merge.
    """
    fixture = create_merge_fixture(tmp_path)
    repo = Path(fixture["repo"])
    head_sha = fixture["head_sha"]
    base_sha = fixture["base_sha"]
    merge_sha = fixture["merge_sha"]

    second_parent = _git(repo, "rev-parse", f"{merge_sha}^2")
    assert second_parent == head_sha

    attestation = make_attestation(
        locked_base_sha=base_sha,
        accepted_exact_head_sha=head_sha,
    )
    verifier = make_fake_verifier(head_sha=head_sha, base_sha=base_sha)

    result = mainline_merge_validation(
        repo_root=repo,
        commit_sha=merge_sha,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["gate_status"] == "PASSED"
    assert result["blocking_reasons"] == []


def test_mainline_validation_passes_at_real_merge_commit(tmp_path):
    """Issue #23 test 4: full positive lifecycle at a real merge commit.

    With a real two-parent merge commit, an attestation whose
    ``accepted_exact_head_sha``/``locked_base_sha`` match the fixture, and a
    fake verifier pre-loaded with matching evidence,
    ``mainline_merge_validation`` must return ``PASSED`` with no blocking
    reasons.
    """
    fixture = create_merge_fixture(tmp_path)
    repo = Path(fixture["repo"])
    head_sha = fixture["head_sha"]
    base_sha = fixture["base_sha"]
    merge_sha = fixture["merge_sha"]

    attestation = make_attestation(
        locked_base_sha=base_sha,
        accepted_exact_head_sha=head_sha,
    )
    verifier = make_fake_verifier(head_sha=head_sha, base_sha=base_sha)

    result = mainline_merge_validation(
        repo_root=repo,
        commit_sha=merge_sha,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["gate_status"] == "PASSED"
    assert result["blocking_reasons"] == []


def test_commit_after_accepted_exact_head_causes_failure(tmp_path):
    """Issue #23 test 5: a commit added after the accepted head must fail.

    When an extra commit is appended to the feature branch after the accepted
    head, the merge's second parent becomes that post-head commit instead of
    the accepted exact head.  The attestation still points at the original
    head, so ``mainline_merge_validation`` must return ``BLOCKED``.
    """
    fixture = create_merge_fixture(
        tmp_path,
        extra_files_after_head={"post_head_change.txt": "change after head\n"},
    )
    repo = Path(fixture["repo"])
    head_sha = fixture["head_sha"]
    base_sha = fixture["base_sha"]
    merge_sha = fixture["merge_sha"]

    # Sanity: the merge's second parent is no longer the accepted head.
    second_parent = _git(repo, "rev-parse", f"{merge_sha}^2")
    assert second_parent != head_sha

    attestation = make_attestation(
        locked_base_sha=base_sha,
        accepted_exact_head_sha=head_sha,
    )
    verifier = make_fake_verifier(head_sha=head_sha, base_sha=base_sha)

    result = mainline_merge_validation(
        repo_root=repo,
        commit_sha=merge_sha,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["gate_status"] == "BLOCKED"
    assert result["blocking_reasons"]


def test_authorization_only_post_ci_commit_causes_failure(tmp_path):
    """Issue #23 test 6: a post-CI authorization-only commit must fail.

    A feature branch that adds an extra commit after the accepted head carrying
    only an authorization artifact still moves the merge's second parent past
    the accepted exact head.  The attestation still points at the original
    head, so ``mainline_merge_validation`` must return ``BLOCKED``.
    """
    fixture = create_merge_fixture(
        tmp_path,
        extra_files_after_head={
            "project_state/authorizations/active.json": '{"status": "active"}\n',
        },
    )
    repo = Path(fixture["repo"])
    head_sha = fixture["head_sha"]
    base_sha = fixture["base_sha"]
    merge_sha = fixture["merge_sha"]

    second_parent = _git(repo, "rev-parse", f"{merge_sha}^2")
    assert second_parent != head_sha

    attestation = make_attestation(
        locked_base_sha=base_sha,
        accepted_exact_head_sha=head_sha,
    )
    verifier = make_fake_verifier(head_sha=head_sha, base_sha=base_sha)

    result = mainline_merge_validation(
        repo_root=repo,
        commit_sha=merge_sha,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["gate_status"] == "BLOCKED"
    assert result["blocking_reasons"]


def test_post_ci_commit_with_unrelated_changes_causes_failure(tmp_path):
    """Issue #23 test 7: a post-CI commit with unrelated source changes must fail.

    A feature branch that adds an extra commit after the accepted head carrying
    unrelated source files still moves the merge's second parent past the
    accepted exact head.  The attestation still points at the original head, so
    ``mainline_merge_validation`` must return ``BLOCKED``.
    """
    fixture = create_merge_fixture(
        tmp_path,
        extra_files_after_head={
            "src/unrelated_module.py": "def unrelated():\n    return None\n",
            "src/extra_helper.py": "EXTRA = 42\n",
        },
    )
    repo = Path(fixture["repo"])
    head_sha = fixture["head_sha"]
    base_sha = fixture["base_sha"]
    merge_sha = fixture["merge_sha"]

    second_parent = _git(repo, "rev-parse", f"{merge_sha}^2")
    assert second_parent != head_sha

    attestation = make_attestation(
        locked_base_sha=base_sha,
        accepted_exact_head_sha=head_sha,
    )
    verifier = make_fake_verifier(head_sha=head_sha, base_sha=base_sha)

    result = mainline_merge_validation(
        repo_root=repo,
        commit_sha=merge_sha,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["gate_status"] == "BLOCKED"
    assert result["blocking_reasons"]
