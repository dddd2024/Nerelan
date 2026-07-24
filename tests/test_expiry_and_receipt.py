"""Expiry and receipt tests for the v3 exact-head external merge approval gate.

These are tests 22-26 from Issue #23. They form part of the TDD red phase for
the v3 architecture: the production functions ``validate_external_attestation``,
``mainline_merge_validation`` and ``emit_mainline_integration_receipt`` do not
exist yet, so collection of this file is expected to fail until they are
implemented in ``reverse_agent.project_gate``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests._v3_helpers import (
    ACCEPTED_EXACT_HEAD_SHA,
    LOCKED_BASE_SHA,
    create_merge_fixture,
    make_attestation,
    make_fake_verifier,
    make_merge_intent,
    sha256_text,
)
from reverse_agent.project_gate import (
    emit_mainline_integration_receipt,
    integration_baseline,
    mainline_merge_validation,
    validate_external_attestation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_TIME = "2026-07-24T12:00:00Z"


def test_active_status_with_past_expires_at_fails() -> None:
    """Test 22 (Issue #23): an active attestation past its expires_at is invalid.

    The attestation is otherwise valid (active status, matching remote evidence)
    but its ``expires_at`` timestamp is in the past relative to ``validation_time``,
    so validation must fail with a reason that mentions expiry.
    """
    attestation = make_attestation(
        authorization_status="active",
        expires_at="2026-07-01T00:00:00Z",
    )
    verifier = make_fake_verifier()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    joined_reasons = " ".join(result["reasons"]).lower()
    assert "expir" in joined_reasons


def test_superseded_approval_fails() -> None:
    """Test 23 (Issue #23): a superseded attestation must fail validation.

    The attestation has ``authorization_status`` of ``superseded`` and points to
    a replacement via ``superseded_by``. Even with otherwise valid evidence it
    must be rejected with a reason that mentions supersession.
    """
    attestation = make_attestation(
        authorization_status="superseded",
        superseded_by="attestation_v3_002",
    )
    verifier = make_fake_verifier()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    joined_reasons = " ".join(result["reasons"]).lower()
    assert "supersed" in joined_reasons


def test_post_merge_receipt_emitted_without_being_prerequisite(tmp_path: Path) -> None:
    """Test 24 (Issue #23): validation passes without a receipt; emitting produces one.

    A fresh merge fixture has no integration receipt file, yet
    ``mainline_merge_validation`` must still pass -- proving the receipt is an
    output artifact, not a prerequisite. ``emit_mainline_integration_receipt``
    then produces a receipt carrying the merge commit and parent identities.
    """
    fixture = create_merge_fixture(tmp_path)
    repo_root = Path(fixture["repo"])
    attestation = make_attestation(
        accepted_exact_head_sha=fixture["head_sha"],
        locked_base_sha=fixture["base_sha"],
    )
    verifier = make_fake_verifier(
        head_sha=fixture["head_sha"],
        base_sha=fixture["base_sha"],
    )

    # No receipt file exists in the fresh fixture; validation must still pass.
    validation = mainline_merge_validation(
        repo_root=repo_root,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )
    assert validation["gate_status"] == "PASSED"

    receipt = emit_mainline_integration_receipt(
        repo_root=repo_root,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )
    assert receipt["receipt_status"] == "EMITTED"
    assert receipt["validation_status"] == "PASSED"
    assert receipt["merge_commit_sha"] == fixture["merge_sha"]
    assert receipt["first_parent_sha"] == fixture["base_sha"]
    assert receipt["second_parent_sha"] == fixture["head_sha"]
    assert receipt["accepted_head_sha"] == fixture["head_sha"]


def test_receipt_publication_does_not_create_main_commit(tmp_path: Path) -> None:
    """Test 25 (Issue #23): emitting a receipt must not add a commit to the repo.

    The receipt is an output artifact only. ``git rev-parse HEAD`` must return
    the same SHA before and after ``emit_mainline_integration_receipt`` runs.
    """
    fixture = create_merge_fixture(tmp_path)
    repo_root = Path(fixture["repo"])
    attestation = make_attestation(
        accepted_exact_head_sha=fixture["head_sha"],
        locked_base_sha=fixture["base_sha"],
    )
    verifier = make_fake_verifier(
        head_sha=fixture["head_sha"],
        base_sha=fixture["base_sha"],
    )

    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    emit_mainline_integration_receipt(
        repo_root=repo_root,
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert head_before == head_after
    assert head_before == fixture["merge_sha"]


def test_historical_integration_baseline_remains_active() -> None:
    """Test 26 (Issue #23): the historical architecture_spine_v1 baseline still passes.

    This verifies that the pre-existing frozen PR #9 integration baseline
    invariant continues to hold against the real project state, independent of
    the new v3 mainline merge validation path.
    """
    result = integration_baseline(
        state_dir=REPO_ROOT / "project_state",
        repo_root=REPO_ROOT,
    )
    assert result["gate_status"] == "PASSED"
    assert result["baseline_id"] == "architecture_spine_v1"
