"""Phase D: runtime risk policy snapshot tests.

Covers the immutable ``RiskPolicySnapshot`` bound to an active Decision,
the path-risk floor data, capability risk rules, and the policy digest
that detects drift from the authorized snapshot.
"""

from __future__ import annotations

import pytest

from reverse_agent.architecture.contracts import RiskPolicySnapshot
from reverse_agent.architecture.risk import RiskTier


def _path_floor_entries() -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    """Return (entries, expected_matches) for a small path risk floor."""

    entries = (
        (".github/workflows/**", "R2"),
        ("pyproject.toml", "R2"),
        ("**/secrets/**", "R3"),
    )
    matches = (
        (".github/workflows/ci.yml", "R2"),
        ("pyproject.toml", "R2"),
        ("config/secrets/api.key", "R3"),
    )
    return entries, matches


def _capability_rules() -> tuple[tuple[tuple[str, str], ...], tuple[tuple[tuple[str, ...], RiskTier | None], ...]]:
    """Return (rules, cases) for capability risk resolution."""

    rules = (
        ("network_access", "R2"),
        ("unknown_binary_execution", "R3"),
        ("destructive", "R3"),
    )
    cases = (
        (("source_edit",), None),
        (("network_access",), RiskTier.R2),
        (("unknown_binary_execution",), RiskTier.R3),
        (("source_edit", "network_access"), RiskTier.R2),
        (("network_access", "unknown_binary_execution"), RiskTier.R3),
    )
    return rules, cases


def test_risk_policy_snapshot_rejects_missing_decision_id() -> None:
    entries, _ = _path_floor_entries()
    rules, _ = _capability_rules()
    with pytest.raises(ValueError, match="missing_or_invalid:decision_id"):
        RiskPolicySnapshot.from_mapping({
            "schema_version": 1,
            "decision_id": "",
            "round_id": "round_one",
            "path_risk_floor": {"entries": list(list(item) for item in entries)},
            "capability_risk_rules": list(list(item) for item in rules),
        })


def test_risk_policy_snapshot_rejects_missing_round_id() -> None:
    entries, _ = _path_floor_entries()
    rules, _ = _capability_rules()
    with pytest.raises(ValueError, match="missing_or_invalid:round_id"):
        RiskPolicySnapshot.from_mapping({
            "schema_version": 1,
            "decision_id": "decision_one",
            "round_id": "",
            "path_risk_floor": {"entries": list(list(item) for item in entries)},
            "capability_risk_rules": list(list(item) for item in rules),
        })


def test_risk_policy_snapshot_path_risk_floor_returns_tier_for_sensitive_paths() -> None:
    entries, matches = _path_floor_entries()
    rules, _ = _capability_rules()
    snapshot = RiskPolicySnapshot.from_mapping({
        "schema_version": 1,
        "decision_id": "decision_one",
        "round_id": "round_one",
        "path_risk_floor": {"entries": list(list(item) for item in entries)},
        "capability_risk_rules": list(list(item) for item in rules),
    })
    for path, expected_tier in matches:
        assert snapshot.path_risk_floor.risk_for_path(path) == expected_tier, path


def test_risk_policy_snapshot_resolves_capability_risk_to_max_tier() -> None:
    _, cases = _capability_rules()
    entries, _ = _path_floor_entries()
    rules, _ = _capability_rules()
    snapshot = RiskPolicySnapshot.from_mapping({
        "schema_version": 1,
        "decision_id": "decision_one",
        "round_id": "round_one",
        "path_risk_floor": {"entries": list(list(item) for item in entries)},
        "capability_risk_rules": list(list(item) for item in rules),
    })
    for operations, expected_tier in cases:
        actual = snapshot.resolved_capability_risk_for(operations)
        assert actual == expected_tier, (operations, expected_tier)


def test_risk_policy_snapshot_digest_is_deterministic() -> None:
    entries, _ = _path_floor_entries()
    rules, _ = _capability_rules()
    payload = {
        "schema_version": 1,
        "decision_id": "decision_one",
        "round_id": "round_one",
        "path_risk_floor": {"entries": list(list(item) for item in entries)},
        "capability_risk_rules": list(list(item) for item in rules),
    }
    snapshot_a = RiskPolicySnapshot.from_mapping(payload)
    snapshot_b = RiskPolicySnapshot.from_mapping(payload)
    assert snapshot_a.policy_digest == snapshot_b.policy_digest
    assert len(snapshot_a.policy_digest) == 64


def test_risk_policy_snapshot_digest_detects_drift() -> None:
    entries, _ = _path_floor_entries()
    rules, _ = _capability_rules()
    base = {
        "schema_version": 1,
        "decision_id": "decision_one",
        "round_id": "round_one",
        "path_risk_floor": {"entries": list(list(item) for item in entries)},
        "capability_risk_rules": list(list(item) for item in rules),
    }
    drifted = dict(base)
    drifted["path_risk_floor"] = {
        "entries": [(".github/workflows/**", "R3")]  # bumped from R2 to R3
    }
    snapshot_a = RiskPolicySnapshot.from_mapping(base)
    snapshot_b = RiskPolicySnapshot.from_mapping(drifted)
    assert snapshot_a.policy_digest != snapshot_b.policy_digest


def test_risk_policy_snapshot_identity_matches_decision_round() -> None:
    entries, _ = _path_floor_entries()
    rules, _ = _capability_rules()
    snapshot = RiskPolicySnapshot.from_mapping({
        "schema_version": 1,
        "decision_id": "decision_one",
        "round_id": "round_one",
        "path_risk_floor": {"entries": list(list(item) for item in entries)},
        "capability_risk_rules": list(list(item) for item in rules),
    })
    assert snapshot.identity_matches("decision_one", "round_one") is True
    assert snapshot.identity_matches("decision_other", "round_one") is False
    assert snapshot.identity_matches("decision_one", "round_other") is False
