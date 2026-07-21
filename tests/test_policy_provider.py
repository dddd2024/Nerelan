"""Phase D: Decision-issued runtime risk policy provider tests.

The ``AuthorizedRiskPolicyProvider`` loads the active Decision, produces a
canonical ``RiskPolicySnapshot``, and computes the authorized policy digest.
Callers cannot supply their own snapshot; the workflow identity must bind
the authorized digest. Tampering with path risk, capability risk, or the
digest itself must fail closed (F6).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reverse_agent.architecture.contracts import (
    RiskPolicySnapshot,
    WorkflowIdentity,
)
from reverse_agent.architecture.policy_provider import (
    AuthorizedRiskPolicyProvider,
    PolicyTamperingError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decision_contract(
    *,
    decision_id: str = "decision_policy",
    round_id: str = "round_policy",
    path_risk_floor: list | None = None,
    capability_risk_rules: list | None = None,
) -> dict:
    if path_risk_floor is None:
        path_risk_floor = [
            [".github/workflows/**", "R2"],
            ["pyproject.toml", "R2"],
            [".env", "R3"],
        ]
    if capability_risk_rules is None:
        capability_risk_rules = [
            {"operation": "network_access", "risk_tier": "R2"},
            {"operation": "push", "risk_tier": "R2"},
            {"operation": "unknown_binary_execution", "risk_tier": "R3"},
        ]
    return {
        "decision_id": decision_id,
        "round_id": round_id,
        "path_risk_floor": path_risk_floor,
        "capability_risk_rules": capability_risk_rules,
    }


# ---------------------------------------------------------------------------
# Provider: canonical policy from active Decision
# ---------------------------------------------------------------------------


def test_provider_produces_canonical_snapshot() -> None:
    """Provider must produce a RiskPolicySnapshot from the active Decision."""

    contract = _decision_contract()
    provider = AuthorizedRiskPolicyProvider(contract)
    snapshot = provider.provide()
    assert isinstance(snapshot, RiskPolicySnapshot)
    assert snapshot.decision_id == "decision_policy"
    assert snapshot.round_id == "round_policy"
    assert snapshot.policy_digest  # non-empty
    # Digest must be 64-char lowercase hex.
    assert len(snapshot.policy_digest) == 64
    assert all(c in "0123456789abcdef" for c in snapshot.policy_digest)


def test_provider_digest_is_deterministic() -> None:
    """Same Decision contract must always produce the same digest."""

    contract = _decision_contract()
    p1 = AuthorizedRiskPolicyProvider(contract)
    p2 = AuthorizedRiskPolicyProvider(contract)
    assert p1.provide().policy_digest == p2.provide().policy_digest


def test_provider_digest_changes_when_path_risk_changes() -> None:
    """Tampering with path-risk floor must change the digest."""

    base = _decision_contract()
    tampered = _decision_contract(
        path_risk_floor=[
            [".github/workflows/**", "R1"],  # lowered from R2 to R1
            ["pyproject.toml", "R2"],
            [".env", "R3"],
        ],
    )
    base_digest = AuthorizedRiskPolicyProvider(base).provide().policy_digest
    tampered_digest = AuthorizedRiskPolicyProvider(tampered).provide().policy_digest
    assert base_digest != tampered_digest


def test_provider_digest_changes_when_capability_rules_change() -> None:
    """Tampering with capability-risk rules must change the digest."""

    base = _decision_contract()
    tampered = _decision_contract(
        capability_risk_rules=[
            {"operation": "network_access", "risk_tier": "R1"},  # lowered
            {"operation": "push", "risk_tier": "R2"},
            {"operation": "unknown_binary_execution", "risk_tier": "R3"},
        ],
    )
    base_digest = AuthorizedRiskPolicyProvider(base).provide().policy_digest
    tampered_digest = AuthorizedRiskPolicyProvider(tampered).provide().policy_digest
    assert base_digest != tampered_digest


# ---------------------------------------------------------------------------
# Workflow identity binding
# ---------------------------------------------------------------------------


def test_provider_binds_workflow_identity() -> None:
    """Provider must produce a workflow identity that binds the policy digest."""

    contract = _decision_contract()
    provider = AuthorizedRiskPolicyProvider(contract)
    snapshot = provider.provide()
    identity = provider.workflow_identity(
        workflow_id="wf-1",
        work_item_identity="repo#1@ref",
    )
    assert identity.workflow_id == "wf-1"
    assert identity.work_item_identity == "repo#1@ref"
    # Identity must carry decision_id, round_id and policy_digest so the
    # classifier can verify them at runtime.
    assert identity.decision_id == snapshot.decision_id
    assert identity.round_id == snapshot.round_id
    assert identity.policy_digest == snapshot.policy_digest


# ---------------------------------------------------------------------------
# Tampering detection
# ---------------------------------------------------------------------------


def test_verify_snapshot_rejects_tampered_digest() -> None:
    """A snapshot with a forged policy_digest must be rejected."""

    contract = _decision_contract()
    provider = AuthorizedRiskPolicyProvider(contract)
    snapshot = provider.provide()
    # Forge a different digest.
    tampered = RiskPolicySnapshot(
        decision_id=snapshot.decision_id,
        round_id=snapshot.round_id,
        path_risk_floor=snapshot.path_risk_floor,
        capability_risk_rules=snapshot.capability_risk_rules,
        policy_digest="0" * 64,
    )
    with pytest.raises(PolicyTamperingError, match="policy_digest_mismatch"):
        provider.verify(tampered)


def test_verify_snapshot_rejects_tampered_path_risk() -> None:
    """A snapshot with altered path-risk floor must be rejected."""

    from reverse_agent.architecture.contracts import PathRiskFloorSnapshot

    contract = _decision_contract()
    provider = AuthorizedRiskPolicyProvider(contract)
    snapshot = provider.provide()
    tampered_floor = PathRiskFloorSnapshot(
        entries=(
            (".github/workflows/**", "R1"),  # lowered
            ("pyproject.toml", "R2"),
            (".env", "R3"),
        ),
    )
    tampered = RiskPolicySnapshot(
        decision_id=snapshot.decision_id,
        round_id=snapshot.round_id,
        path_risk_floor=tampered_floor,
        capability_risk_rules=snapshot.capability_risk_rules,
        policy_digest=snapshot.policy_digest,  # keep old digest
    )
    with pytest.raises(PolicyTamperingError):
        provider.verify(tampered)


def test_verify_snapshot_rejects_identity_mismatch() -> None:
    """A snapshot from a different Decision must be rejected."""

    contract = _decision_contract()
    provider = AuthorizedRiskPolicyProvider(contract)
    snapshot = provider.provide()
    # Identity mismatch: different decision_id.
    from reverse_agent.architecture.contracts import RiskPolicySnapshot

    tampered = RiskPolicySnapshot(
        decision_id="other_decision",
        round_id=snapshot.round_id,
        path_risk_floor=snapshot.path_risk_floor,
        capability_risk_rules=snapshot.capability_risk_rules,
        policy_digest=snapshot.policy_digest,
    )
    with pytest.raises(PolicyTamperingError, match="identity_mismatch"):
        provider.verify(tampered)


def test_verify_snapshot_rejects_replay_with_stale_policy() -> None:
    """Replay with an older policy digest must be rejected."""

    contract_v1 = _decision_contract()
    provider_v1 = AuthorizedRiskPolicyProvider(contract_v1)
    snapshot_v1 = provider_v1.provide()

    # Decision updates: path-risk floor tightens.
    contract_v2 = _decision_contract(
        path_risk_floor=[
            [".github/workflows/**", "R3"],  # raised from R2 to R3
            ["pyproject.toml", "R2"],
            [".env", "R3"],
        ],
    )
    provider_v2 = AuthorizedRiskPolicyProvider(contract_v2)

    # Replay old snapshot against new provider.
    with pytest.raises(PolicyTamperingError):
        provider_v2.verify(snapshot_v1)


def test_caller_supplied_lower_risk_policy_rejected() -> None:
    """A caller-supplied policy with lower risk must be rejected by verify()."""

    contract = _decision_contract()
    provider = AuthorizedRiskPolicyProvider(contract)
    authorized = provider.provide()

    # Caller tries to supply a snapshot with lower path risk but same digest.
    from reverse_agent.architecture.contracts import PathRiskFloorSnapshot

    lower_floor = PathRiskFloorSnapshot(
        entries=(
            (".github/workflows/**", "R0"),  # lowered
            ("pyproject.toml", "R0"),
            (".env", "R0"),
        ),
    )
    caller_supplied = RiskPolicySnapshot(
        decision_id=authorized.decision_id,
        round_id=authorized.round_id,
        path_risk_floor=lower_floor,
        capability_risk_rules=authorized.capability_risk_rules,
        policy_digest=authorized.policy_digest,  # claim same digest
    )
    with pytest.raises(PolicyTamperingError):
        provider.verify(caller_supplied)
