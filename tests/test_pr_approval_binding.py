"""Tests 16-21 from Issue #23: PR and approval binding for the v3 exact-head
external merge approval architecture.

These tests are part of the TDD red phase.  They exercise
``reverse_agent.project_gate.validate_external_attestation`` and assert that
PR binding, approval reference resolution, approver authorization, and
approval base/head/method coherence are all enforced against external remote
evidence via the ``RemoteAcceptanceVerifier``.

The implementation does not exist yet, so every test is expected to fail
(import error / missing symbol) until the green phase lands.  All tests are
hermetic: they use the ``FakeRemoteAcceptanceVerifier`` and never touch the
network.
"""

from __future__ import annotations

from tests._v3_helpers import (
    make_merge_intent,
    make_attestation,
    make_fake_verifier,
    FakeRemoteAcceptanceVerifier,
    create_merge_fixture,
    ACCEPTED_EXACT_HEAD_SHA,
    LOCKED_BASE_SHA,
    WRONG_HEAD_SHA,
    WRONG_BASE_SHA,
    DECISION_ID,
    DECISION_CONTENT_DIGEST,
    COMMAND_PLAN_DIGEST,
    sha256_text,
)
from reverse_agent.project_gate import (
    validate_external_attestation,
    mainline_merge_validation,
)

VALIDATION_TIME = "2026-07-24T12:00:00Z"


def test_wrong_source_pr_fails_even_with_recomputed_digests():
    """Test #16 (Issue #23).

    An attestation whose ``source_pr`` does not match any PR known to the
    verifier must be rejected, even when its ``content_digest`` is recomputed
    to be internally coherent with the wrong PR.  PR binding is verified
    against external remote evidence, so a self-consistent digest cannot
    bypass it.
    """
    attestation = make_attestation(source_pr=99)
    # Recompute content_digest so it is coherent with the (wrong) PR payload,
    # isolating the failure to external PR binding.
    attestation["content_digest"] = sha256_text(
        attestation["attestation_id"] + attestation["accepted_exact_head_sha"]
    )
    # Default verifier only knows PR #23, not #99.
    verifier = make_fake_verifier()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    reasons_blob = " ".join(result["reasons"]).lower()
    assert "pr" in reasons_blob


def test_pr_head_base_mismatch_fails():
    """Test #17 (Issue #23).

    When the attestation's ``accepted_exact_head_sha`` / ``locked_base_sha``
    do not match the PR's head/base in the verifier, the attestation must be
    rejected.  The verifier's PR #23 carries head=d*40 while the attestation
    declares head=b*40.
    """
    attestation = make_attestation(
        accepted_exact_head_sha=ACCEPTED_EXACT_HEAD_SHA,
        locked_base_sha=LOCKED_BASE_SHA,
    )
    # PR #23 has head=d*40 (WRONG_HEAD_SHA); runs and approval still match the
    # attestation so the PR head/base check is the binding under test.
    verifier = make_fake_verifier(
        prs={
            23: {
                "number": 23,
                "repository": "dddd2024/reverse-agent",
                "head_sha": WRONG_HEAD_SHA,
                "base_sha": LOCKED_BASE_SHA,
            }
        }
    )

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    assert result["reasons"]


def test_nonexistent_approval_reference_fails():
    """Test #18 (Issue #23).

    An attestation that references an approval object the verifier cannot
    find must be rejected.  The approval reference is resolved against the
    external remote (e.g. GitHub PR comment id), so a fabricated reference
    fails.
    """
    attestation = make_attestation(approval_object_id="issuecomment-nonexistent")
    # make_attestation recomputes approval_content_digest to stay coherent
    # with the new approval_object_id, isolating the failure to the lookup.
    verifier = make_fake_verifier()  # only knows "issuecomment-12345"

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    assert result["reasons"]


def test_unauthorized_approver_fails():
    """Test #19 (Issue #23).

    When the approval exists remotely but was left by an approver who is not
    in ``allowed_approvers``, the attestation must be rejected.  The remote
    approval is configured with ``approver: "unauthorized_user"`` while the
    attestation declares an authorized approver.
    """
    attestation = make_attestation(approver="dddd2024")
    verifier = make_fake_verifier(
        approvals={
            "issuecomment-12345": {
                "approver": "unauthorized_user",
                "head_sha": ACCEPTED_EXACT_HEAD_SHA,
                "base_sha": LOCKED_BASE_SHA,
                "merge_method": "merge",
            }
        }
    )

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    assert result["reasons"]


def test_approval_digest_base_head_method_mismatch_fails():
    """Test #20 (Issue #23).

    When the remote approval's ``base_sha`` / ``head_sha`` / ``merge_method``
    do not match what the attestation declares, the attestation must be
    rejected.  This binds the human approval to the exact head, base, and
    merge method.  Here the approval's base_sha is e*40 (vs a*40) and its
    merge_method is "squash" (vs "merge").
    """
    attestation = make_attestation(
        accepted_exact_head_sha=ACCEPTED_EXACT_HEAD_SHA,
        locked_base_sha=LOCKED_BASE_SHA,
    )
    verifier = make_fake_verifier(
        approvals={
            "issuecomment-12345": {
                "approver": "dddd2024",
                "head_sha": ACCEPTED_EXACT_HEAD_SHA,  # matches attestation
                "base_sha": WRONG_BASE_SHA,           # mismatches a*40
                "merge_method": "squash",             # mismatches "merge"
            }
        }
    )

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    assert result["reasons"]


def test_coherently_rewritten_fields_still_fail_without_external_approval():
    """Test #21 (Issue #23): the coherent-forgery backstop test.

    A forgery that rewrites ``source_pr``, ``decision_identity``, and
    recomputes ``content_digest`` to match must still be rejected, because
    the external PR/approval evidence does not match the rewritten
    attestation.  The verifier still only knows PR #23, so the PR check for
    ``source_pr=24`` fails regardless of the coherent digest.  This proves
    external binding is the backstop against self-consistent forgeries.
    """
    attestation = make_attestation()  # valid baseline, source_pr=23
    # Rewrite fields to point at a different PR and decision...
    attestation["source_pr"] = 24
    attestation["decision_identity"] = {
        "decision_id": "decision_forged_20260724",
        "decision_content_digest": DECISION_CONTENT_DIGEST,
    }
    # ...and recompute content_digest so the payload is internally coherent.
    attestation["content_digest"] = sha256_text(
        attestation["attestation_id"]
        + attestation["accepted_exact_head_sha"]
        + "forged"
    )
    # Verifier still only knows PR #23, so the PR check for source_pr=24
    # fails regardless of the coherent digest.
    verifier = make_fake_verifier()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    assert result["reasons"]
