"""Tests 8-15 (Issue #23): remote evidence authenticity for external merge approvals.

Red-phase TDD: ``reverse_agent.project_gate.validate_external_attestation`` is
not implemented yet, so every test in this module is expected to fail at import
time until the v3 remote acceptance verifier plumbing lands.

Each test builds a hermetic ``FakeRemoteAcceptanceVerifier`` plus a
``MergeApprovalAttestation`` fixture and asserts that
``validate_external_attestation`` rejects the attestation when the remote
evidence is missing, mismatched, stale, or incomplete.  No network access is
required.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests._v3_helpers import (
    ACCEPTED_EXACT_HEAD_SHA,
    LOCKED_BASE_SHA,
    REQUIRED_WORKFLOWS,
    FakeRemoteAcceptanceVerifier,
    make_attestation,
    make_fake_verifier,
    make_workflow_observation,
    sha256_text,
)
from reverse_agent.project_gate import validate_external_attestation


VALIDATION_TIME = "2026-07-24T12:00:00Z"


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def _workflow_file_for(name: str) -> str:
    """Match the ``workflow_file`` convention used by ``make_fake_verifier``."""
    normalized = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    return f".github/workflows/{normalized}.yml"


def _make_run(run_id: int, name: str, **overrides: Any) -> dict[str, Any]:
    """Build a single verifier run dict that lines up with the attestation."""
    base: dict[str, Any] = {
        "run_id": run_id,
        "name": name,
        "head_sha": ACCEPTED_EXACT_HEAD_SHA,
        "workflow_file": _workflow_file_for(name),
        "event": "pull_request",
        "run_attempt": 1,
        "conclusion": "success",
        "repository": "dddd2024/reverse-agent",
    }
    base.update(overrides)
    return base


def _baseline_observations() -> list[dict[str, Any]]:
    """Four workflow observations that line up with ``make_fake_verifier()`` runs."""
    return [
        make_workflow_observation(
            name=name,
            run_id=1000 + i,
            head_sha=ACCEPTED_EXACT_HEAD_SHA,
            workflow_file=_workflow_file_for(name),
        )
        for i, name in enumerate(REQUIRED_WORKFLOWS)
    ]


def _baseline_attestation() -> dict[str, Any]:
    """An attestation that should pass validation against ``make_fake_verifier()``."""
    return make_attestation(workflow_observations=_baseline_observations())


# ---------------------------------------------------------------------------
# Tests 8-15
# ---------------------------------------------------------------------------

def test_nonexistent_run_id_fails() -> None:
    """Test 8 (Issue #23): an attestation referencing an unknown run_id is rejected."""
    observations = _baseline_observations()
    # Point the last observation at a run the verifier does not know about.
    observations[-1] = make_workflow_observation(
        name=REQUIRED_WORKFLOWS[-1],
        run_id=99999,
        head_sha=ACCEPTED_EXACT_HEAD_SHA,
        workflow_file=_workflow_file_for(REQUIRED_WORKFLOWS[-1]),
    )
    attestation = make_attestation(workflow_observations=observations)
    # Sanity: the attestation's content_digest binds id+head_sha (fixture contract).
    assert attestation["content_digest"] == sha256_text(
        attestation["attestation_id"] + attestation["accepted_exact_head_sha"]
    )

    verifier = make_fake_verifier()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
    joined_reasons = " ".join(result["reasons"]).lower()
    assert "99999" in joined_reasons or "run" in joined_reasons


def test_run_from_another_repository_fails() -> None:
    """Test 9 (Issue #23): a run that lives in a different repository is rejected."""
    runs = {
        1000 + i: _make_run(
            1000 + i,
            name,
            repository="other/repo" if i == 0 else "dddd2024/reverse-agent",
        )
        for i, name in enumerate(REQUIRED_WORKFLOWS)
    }
    verifier = FakeRemoteAcceptanceVerifier(
        runs=runs,
        prs={
            23: {
                "number": 23,
                "repository": "dddd2024/reverse-agent",
                "head_sha": ACCEPTED_EXACT_HEAD_SHA,
                "base_sha": LOCKED_BASE_SHA,
            }
        },
        approvals={
            "issuecomment-12345": {
                "approver": "dddd2024",
                "head_sha": ACCEPTED_EXACT_HEAD_SHA,
                "base_sha": LOCKED_BASE_SHA,
                "merge_method": "merge",
            }
        },
    )
    attestation = _baseline_attestation()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False


def test_run_for_another_sha_fails() -> None:
    """Test 10 (Issue #23): a run whose head_sha differs from accepted_exact_head_sha is rejected."""
    verifier = make_fake_verifier()
    verifier._runs[1000]["head_sha"] = "d" * 40
    attestation = _baseline_attestation()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False


def test_wrong_workflow_name_or_file_fails() -> None:
    """Test 11 (Issue #23): a run whose workflow_file differs from the attestation is rejected."""
    verifier = make_fake_verifier()
    verifier._runs[1000]["workflow_file"] = ".github/workflows/wrong.yml"
    attestation = _baseline_attestation()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False


def test_wrong_event_type_fails() -> None:
    """Test 12 (Issue #23): a run triggered by 'push' instead of 'pull_request' is rejected."""
    verifier = make_fake_verifier()
    verifier._runs[1000]["event"] = "push"
    attestation = _baseline_attestation()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False


@pytest.mark.parametrize(
    "bad_conclusion", ["failure", "cancelled", "skipped", "in_progress"]
)
def test_failed_or_cancelled_run_fails(bad_conclusion: str) -> None:
    """Test 13 (Issue #23): a run that did not reach 'success' is rejected."""
    verifier = make_fake_verifier()
    verifier._runs[1000]["conclusion"] = bad_conclusion
    attestation = _baseline_attestation()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False


def test_stale_run_attempt_fails() -> None:
    """Test 14 (Issue #23): a run whose actual run_attempt is older than declared is rejected."""
    observations = _baseline_observations()
    # Attestation claims run_attempt=2, but the verifier's run only has attempt 1.
    observations[0] = make_workflow_observation(
        name=REQUIRED_WORKFLOWS[0],
        run_id=1000,
        head_sha=ACCEPTED_EXACT_HEAD_SHA,
        workflow_file=_workflow_file_for(REQUIRED_WORKFLOWS[0]),
        run_attempt=2,
    )
    attestation = make_attestation(workflow_observations=observations)
    verifier = make_fake_verifier()  # run 1000 has run_attempt=1

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False


def test_missing_one_required_run_fails() -> None:
    """Test 15 (Issue #23): an attestation missing one required workflow observation is rejected."""
    observations = _baseline_observations()[:3]  # drop the 4th required workflow
    attestation = make_attestation(workflow_observations=observations)
    verifier = make_fake_verifier()

    result = validate_external_attestation(
        attestation=attestation,
        verifier=verifier,
        validation_time=VALIDATION_TIME,
    )

    assert result["valid"] is False
