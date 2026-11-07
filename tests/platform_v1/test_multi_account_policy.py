"""Policy self-evolution: bounded steps, audit trail, rollback.

The loop may only move one weight by one step per cycle, always inside a clamp
around the configured baseline, and every change must be reversible.
"""
import json

import pytest

from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.policy import PolicyLedger
from reverse_agent.platform_v1.multi_account.scoring import AccountScoreboard

NOW = 1_700_000_000.0


def ledger(**overrides):
    config = MultiAccountConfig(**overrides)
    clock = lambda: NOW  # noqa: E731
    return PolicyLedger(config, clock=clock)


def profile(*, attempts=10, success_rate=0.9, kinds=None, cost=None, wall=None):
    return {"attempts": attempts, "successes": int(attempts * success_rate),
            "success_rate": success_rate, "failure_kinds": dict(kinds or {}),
            "cost_units": cost, "wall_seconds": wall}


# --- gating ------------------------------------------------------------------

def test_insufficient_evidence_never_changes_anything():
    result = ledger().observe(profile(attempts=2, success_rate=0.0))
    assert result["changed"] is False
    assert result["reason"] == "insufficient_samples"


def test_disabled_policy_never_changes_anything():
    result = ledger(policy_enabled=False).observe(profile(success_rate=0.0))
    assert result["reason"] == "policy_disabled"


def test_stable_pool_at_baseline_makes_no_change():
    result = ledger().observe(profile(success_rate=0.95))
    assert result["changed"] is False
    assert result["reason"] == "stable_no_change"


# --- rules -------------------------------------------------------------------

def test_unstable_pool_reverts_toward_baseline():
    pol = ledger()
    first = pol.observe(profile(success_rate=0.5))
    assert first["changed"] is True
    assert first["reason"] == "unstable_revert"
    # Weights were already at baseline, so only the learned-bonus cap moved.
    assert set(first["changed_keys"]) == {"bonus_cap"}
    assert first["after"]["bonus_cap"] < first["before"]["bonus_cap"]


def test_capacity_bound_pool_shrinks_the_learned_bonus():
    pol = ledger()
    result = pol.observe(profile(success_rate=0.9, kinds={"quota_exhausted": 8}))
    assert result["reason"] == "capacity_bound_reduce_bonus"
    assert result["after"]["bonus_cap"] == 9.0      # 12 - 12*0.25


def test_reliability_failures_raise_the_reliability_weight():
    pol = ledger()
    result = pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    assert result["reason"] == "failure_profile_reliability"
    assert result["after"]["reliability_weight"] == 15.0   # 12 + 12*0.25


def test_weight_cannot_exceed_the_drift_clamp():
    pol = ledger(policy_max_weight_drift_ratio=0.2)
    for _ in range(6):
        pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    assert pol.weights()["reliability_weight"] == pytest.approx(12.0 * 1.2)
    # Once clamped, further identical evidence is reported as a no-op, not as
    # a change, so the audit trail cannot fill with identical entries.
    result = pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    assert result["changed"] is False
    assert result["reason"].endswith("at_clamp_limit")


def test_latency_failures_raise_the_latency_weight():
    pol = ledger()
    result = pol.observe(profile(success_rate=0.9, kinds={"timeout": 7}))
    assert result["reason"] == "failure_profile_latency"
    assert result["after"]["latency_weight"] == 6.25


def test_cost_pressure_requires_a_reference_to_compare_against():
    pol = ledger()
    first = pol.observe(profile(success_rate=0.95, cost=10.0))
    assert first["changed"] is False            # reference captured, no pressure yet
    second = pol.observe(profile(success_rate=0.95, cost=20.0))
    assert second["reason"] == "cost_pressure"
    assert second["after"]["cost_weight"] == 12.5


def test_stable_pool_restores_a_shrunk_bonus():
    pol = ledger()
    pol.observe(profile(success_rate=0.9, kinds={"quota_exhausted": 8}))
    assert pol.bonus_cap() == 9.0
    restored = pol.observe(profile(success_rate=0.97))
    assert restored["reason"] == "stable_restore_bonus"
    assert pol.bonus_cap() == 12.0


def test_task_failures_alone_do_not_steer_account_policy():
    # "task_failed" is not an account-quality signal; the loop must stay put
    # rather than invent a preference from it.
    result = ledger().observe(profile(success_rate=0.9, kinds={"task_failed": 9}))
    assert result["changed"] is False


# --- audit and rollback ------------------------------------------------------

def test_every_change_is_audited_with_before_after_and_reason():
    pol = ledger()
    pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    audit = pol.audit()
    assert len(audit) == 1
    entry = audit[0]
    assert entry["version"] == 1
    assert entry["kind"] == "change"
    assert entry["reason"] == "failure_profile_reliability"
    assert entry["before"]["reliability_weight"] == 12.0
    assert entry["after"]["reliability_weight"] == 15.0
    assert entry["evidence"]["samples"] == 10


def test_rollback_to_baseline_and_to_a_specific_version():
    pol = ledger()
    pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))   # v1
    pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))   # v2
    assert pol.version() == 2

    back_to_one = pol.rollback(1)
    assert back_to_one["changed"] is True
    assert pol.weights()["reliability_weight"] == 15.0
    assert pol.version() == 3
    assert pol.audit()[-1]["kind"] == "rollback"
    assert pol.audit()[-1]["rolled_back_to"] == 1

    to_baseline = pol.rollback(0)
    assert to_baseline["changed"] is True
    assert pol.weights()["reliability_weight"] == 12.0


def test_rollback_to_unknown_version_is_refused():
    pol = ledger()
    result = pol.rollback(99)
    assert result["changed"] is False
    assert result["reason"] == "unknown_version"


def test_audit_trail_is_bounded():
    pol = ledger(policy_audit_max_entries=3)
    for _ in range(10):
        pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    assert len(pol.audit()) <= 3


def test_state_survives_a_restart(tmp_path):
    path = tmp_path / "policy.json"
    config = MultiAccountConfig()
    first = PolicyLedger(config, clock=lambda: NOW,
                         persist=lambda snap: path.write_text(json.dumps(snap), encoding="utf-8"))
    first.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))

    restored = PolicyLedger(config, clock=lambda: NOW,
                            state=json.loads(path.read_text(encoding="utf-8")))
    assert restored.version() == 1
    assert restored.weights()["reliability_weight"] == 15.0
    assert len(restored.audit()) == 1


def test_a_hand_edited_state_cannot_widen_the_clamp():
    pol = ledger()
    pol.load({"version": 7, "effective": {"reliability_weight": 999.0,
                                          "bonus_cap": 999.0}})
    assert pol.weights()["reliability_weight"] == 18.0     # 12 * (1 + 0.5)
    assert pol.bonus_cap() == 12.0


# --- effect on ranking -------------------------------------------------------

def test_bonus_cap_zero_makes_ranking_pure_headroom():
    config = MultiAccountConfig(policy_max_bonus_points=0.0)
    scores = AccountScoreboard(config, clock=lambda: NOW)
    scores.observe("a", ok=True, cost_units=1.0, now=NOW)
    assert scores.bonus("a", cost_reference=1.0) != 0.0
    assert scores.bonus("a", cost_reference=1.0, cap=0.0) == 0.0


def test_bonus_is_clamped_symmetrically():
    config = MultiAccountConfig()
    scores = AccountScoreboard(config, clock=lambda: NOW)
    for _ in range(5):
        scores.observe("a", ok=False, failure_kind="task_failed", now=NOW)
    assert scores.bonus("a", cap=3.0) >= -3.0
    assert scores.bonus("a", cap=3.0) <= 3.0


# --- a change that cannot be written must not be reported --------------------

class _FailingPersister:
    """Persists once, then refuses: the disk went away mid-run."""

    def __init__(self, fail_from: int = 1):
        self.calls: list[dict] = []
        self.fail_from = fail_from

    def __call__(self, snapshot):
        self.calls.append(snapshot)
        if len(self.calls) >= self.fail_from:
            raise OSError("disk full")


def test_a_failed_write_is_not_reported_as_a_new_version():
    """The audit trail must never name a version that does not exist on disk."""
    persist = _FailingPersister(fail_from=1)
    pol = PolicyLedger(MultiAccountConfig(), clock=lambda: NOW, persist=persist)
    result = pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    assert result["changed"] is False
    assert result["reason"] == "persist_failed"
    assert pol.version() == 0
    assert pol.current()["effective"] == pol.current()["baseline"]
    assert pol.audit() == []


def test_a_transient_write_failure_does_not_wedge_the_loop():
    """One failed write declines that change only; the next cycle may commit."""
    attempts = {"n": 0}

    def flaky(snapshot):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise OSError("temporary")

    pol = PolicyLedger(MultiAccountConfig(), clock=lambda: NOW, persist=flaky)
    first = pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    assert first["reason"] == "persist_failed" and pol.version() == 0
    second = pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    assert second["changed"] is True
    assert pol.version() == 1
    assert len(pol.audit()) == 1


def test_a_refused_rollback_leaves_the_previous_weights_in_force():
    """Telling an operator "rolled back" and then restarting into v6 is a lie."""
    path = {}

    def persist(snapshot):
        if path.get("fail"):
            raise OSError("read-only filesystem")
        path["snap"] = json.loads(json.dumps(snapshot))

    pol = PolicyLedger(MultiAccountConfig(), clock=lambda: NOW, persist=persist)
    assert pol.observe(profile(success_rate=0.9,
                               kinds={"account_abnormal": 6}))["changed"] is True
    moved = pol.weights()["reliability_weight"]
    path["fail"] = True
    refused = pol.rollback(0)
    assert refused["changed"] is False
    assert refused["reason"] == "persist_failed"
    assert pol.weights()["reliability_weight"] == moved
    assert pol.version() == 1
    assert path["snap"]["effective"]["reliability_weight"] == moved


def test_the_persisted_snapshot_is_what_a_restart_would_load():
    snapshots: list[dict] = []
    pol = PolicyLedger(MultiAccountConfig(), clock=lambda: NOW, persist=snapshots.append)
    pol.observe(profile(success_rate=0.9, kinds={"account_abnormal": 6}))
    restored = PolicyLedger(MultiAccountConfig(), clock=lambda: NOW, state=snapshots[-1])
    assert restored.version() == pol.version()
    assert restored.weights() == pol.weights()
    assert [row["version"] for row in restored.audit()] == [1]
