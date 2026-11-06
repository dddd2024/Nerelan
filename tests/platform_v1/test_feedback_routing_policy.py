"""Measured production ranking remains bounded by all existing hard gates."""
import copy
import json

import pytest

from reverse_agent.platform_v1.multi_account import MultiAccountConfig, MultiAccountOrchestrator, dispatch
from reverse_agent.platform_v1.multi_account.feedback_policy import routing_snapshot
from reverse_agent.platform_v1.multi_account.scoring import AccountScoreboard, PRUNE_HORIZON_SECONDS
from tests.platform_v1.test_model_router import candidate, choose, fixture_host
from reverse_agent.platform_v1.goal_service import PlannedTask

NOW = 1_790_000_000.0


def snapshot(*, a_ok=True, b_ok=True, a_cost=1.0, b_cost=1.0,
             a_latency=10.0, b_latency=10.0, attempts=3, **config):
    cfg = MultiAccountConfig(enable_feedback_routing=True, **config)
    scores = AccountScoreboard(cfg, clock=lambda: NOW)
    for _ in range(attempts):
        scores.observe("account-a", ok=a_ok, cost_units=a_cost, wall_seconds=a_latency)
        scores.observe("account-b", ok=b_ok, cost_units=b_cost, wall_seconds=b_latency)
    return routing_snapshot(cfg, scores.snapshot(), owner="local", now=NOW)


def pool():
    return [candidate("a", "flash-lite", account_ref="account-a"),
            candidate("b", "flash-lite", account_ref="account-b")]


def test_measured_reliability_changes_real_router_choice_with_evidence():
    result = choose(pool(), account_feedback=snapshot(a_ok=False), now=NOW)
    assert result["binding_ref"] == "b"
    evidence = result["score_breakdown"]["account_feedback"]
    assert evidence["account_ref"] == "account-b" and evidence["sample"]["attempts"] == 3
    assert len(evidence["policy_id"]) == len(evidence["snapshot_id"]) == 64
    assert abs(evidence["adjustment"]) <= 0.1
    json.dumps(result, allow_nan=False)


def test_complete_relative_cost_and_latency_feedback_are_consumed():
    cheap = choose(pool(), account_feedback=snapshot(a_cost=10, b_cost=1, reliability_weight=0,
                                                     latency_weight=0), now=NOW)
    assert cheap["binding_ref"] == "b"
    assert cheap["score_breakdown"]["account_feedback"]["cost_comparison"] == "list_price"
    fast = choose(pool(), account_feedback=snapshot(a_latency=100, b_latency=1, reliability_weight=0,
                                                    cost_weight=0), now=NOW)
    assert fast["binding_ref"] == "b"
    assert fast["score_breakdown"]["account_feedback"]["latency_comparison"] == "attempt_elapsed"


def test_unknown_cost_is_not_a_free_account_preference():
    result = choose(pool(), account_feedback=snapshot(a_cost=100, b_cost=None, reliability_weight=0,
                                                      latency_weight=0), now=NOW)
    assert result["binding_ref"] == "a"
    for row in result["candidates"]:
        evidence = row["score_breakdown"]["account_feedback"]
        assert evidence["cost_comparison"] == "UNKNOWN" and evidence["cost_reference"] is None
        assert evidence["adjustment"] == 0


def test_missing_legacy_coverage_does_not_invent_cost_measurements():
    cfg = MultiAccountConfig(enable_feedback_routing=True, reliability_weight=0, latency_weight=0)
    states = {ref: {"account_ref": ref, "attempts": 3, "successes": 3, "reliability": 1,
                    "updated_at": NOW, "mean_cost_units": cost}
              for ref, cost in (("account-a", 100), ("account-b", 1))}
    legacy = routing_snapshot(cfg, states, owner="local", now=NOW)
    result = choose(pool(), account_feedback=legacy, now=NOW)
    assert result["binding_ref"] == "a"
    assert result["score_breakdown"]["account_feedback"]["cost_comparison"] == "UNKNOWN"


def test_minimum_samples_and_expired_feedback_preserve_original_routing():
    for feedback, now in ((snapshot(a_ok=False, attempts=2), NOW),
                          (snapshot(a_ok=False), NOW + PRUNE_HORIZON_SECONDS + 1)):
        result = choose(pool(), account_feedback=feedback, now=now)
        assert result["binding_ref"] == "a"
        assert "account_feedback" not in result["score_breakdown"]


def test_old_history_is_pruned_before_new_sample_is_learned():
    cfg = MultiAccountConfig(enable_feedback_routing=True)
    scores = AccountScoreboard(cfg, clock=lambda: NOW)
    for _ in range(3):
        scores.observe("account-a", ok=False, now=NOW)
    scores.observe("account-a", ok=True, now=NOW + PRUNE_HORIZON_SECONDS + 1)
    assert scores.get("account-a").attempts == 1


def test_advice_does_not_override_pin_availability_quota_or_paid_permission():
    feedback = snapshot(a_ok=False)
    assert choose(pool(), pin="a", account_feedback=feedback, now=NOW)["binding_ref"] == "a"
    candidates = pool()
    candidates[1]["availability"] = {"state": "UNKNOWN"}
    assert choose(candidates, account_feedback=feedback, now=NOW)["binding_ref"] == "a"
    candidates = pool()
    candidates[1]["quota"] = {"decision": "switch", "reason": "limit_hit"}
    assert choose(candidates, account_feedback=feedback, now=NOW)["binding_ref"] == "a"
    candidates = pool()
    candidates[1]["cost_class"] = "paid_api"
    assert choose(candidates, allow_paid=False, account_feedback=feedback, now=NOW)["binding_ref"] == "a"


def test_policy_clamp_and_disabled_policy_provide_nondestructive_rollback():
    feedback = snapshot(a_ok=False, reliability_weight=1_000_000,
                        feedback_routing_max_adjustment=0.025)
    result = choose(pool(), account_feedback=feedback, now=NOW)
    assert result["binding_ref"] == "b"
    assert all(abs(row["score_breakdown"]["account_feedback"]["adjustment"]) <= 0.025
               for row in result["candidates"])
    original = copy.deepcopy(feedback)
    assert choose(pool(), now=NOW)["binding_ref"] == "a"
    assert feedback == original


@pytest.mark.parametrize("mutate", [lambda row: row.update(snapshot_id="bad"),
                                    lambda row: row["policy"].update(cost_weight=999),
                                    lambda row: row["accounts"]["account-b"].update(reliability=1)])
def test_tampered_snapshot_falls_back_without_partial_adjustments(mutate):
    feedback = snapshot(a_ok=False)
    mutate(feedback)
    result = choose(pool(), account_feedback=feedback, now=NOW)
    assert result["binding_ref"] == "a"
    assert all("account_feedback" not in row["score_breakdown"] for row in result["candidates"])


def test_host_production_path_consumes_snapshot_and_master_off_restores_route(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    host._store.upsert_connection(dict(connection_id="second-api", name="second", provider="openai-compatible",
        base_url="https://example.invalid/v1", auth_method="none", enabled=True, account_ref="account-b"))
    host._store.upsert_binding(dict(binding_id="other", name="other", executor_id="opencode",
        connection_id="second-api", model_id="flash-lite", enabled=True))
    host._store.upsert_connection(dict(connection_id="free-api", name="first", provider="openai-compatible",
        base_url="https://example.invalid/v1", auth_method="none", enabled=True, account_ref="account-a"))
    monkeypatch.setattr(host, "_runnable_bindings", lambda: {"cheap", "other"})
    cfg = MultiAccountConfig(enable_feedback_routing=True)
    brain = MultiAccountOrchestrator(cfg, store_path=tmp_path / "feedback.json")
    for _ in range(3):
        brain.record_account_outcome("account-a", ok=False, failure_kind="task_failed")
        brain.record_account_outcome("account-b", ok=True)
    monkeypatch.setattr(dispatch, "get_orchestrator", lambda *args, **kwargs: brain)
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "other"
    saved = (tmp_path / "feedback.json").read_bytes()
    brain.config.enable_feedback_routing = False
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "cheap"
    assert (tmp_path / "feedback.json").read_bytes() == saved
    brain.config.enable_feedback_routing = True
    monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED")
    assert host._resolve_task_model(PlannedTask("T1", "edit", "edit", difficulty=2))["binding_ref"] == "cheap"


def test_delegated_routing_owner_never_receives_local_ranking_policy():
    cfg = MultiAccountConfig(enable_feedback_routing=True)
    assert routing_snapshot(cfg, {}, owner="magpie", now=NOW) is None


def test_candidate_evidence_replays_the_exact_bounded_adjustment():
    result = choose(pool(), account_feedback=snapshot(a_cost=8, b_cost=1, a_latency=20, b_latency=5), now=NOW)
    for row in result["candidates"]:
        evidence = row["score_breakdown"]["account_feedback"]
        cfg = MultiAccountConfig(**evidence["policy"])
        scoreboard = AccountScoreboard(cfg, state={evidence["account_ref"]: evidence["sample"]})
        points = scoreboard.bonus(evidence["account_ref"], cost_reference=evidence["cost_reference"],
                                  latency_reference=evidence["latency_reference"])
        cap = cfg.feedback_routing_max_adjustment
        adjustment = max(-cap, min(cap, points / 100))
        assert adjustment == evidence["adjustment"]
        assert row["score"][1] == evidence["base_adjusted_cost"] - adjustment


def test_new_policy_controls_are_validated_and_reachable_from_environment(monkeypatch):
    from pydantic import ValidationError
    assert MultiAccountConfig().enable_feedback_routing is False
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_FEEDBACK_ROUTING", "true")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_FEEDBACK_ROUTING_MIN_ATTEMPTS", "5")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_FEEDBACK_ROUTING_MAX_ADJUSTMENT", "0.05")
    cfg = MultiAccountConfig.from_env()
    assert cfg.enable_feedback_routing is True
    assert cfg.feedback_routing_min_attempts == 5 and cfg.feedback_routing_max_adjustment == .05
    for values in ({"feedback_routing_min_attempts": 2}, {"feedback_routing_max_adjustment": .251},
                   {"feedback_routing_max_adjustment": -1}, {"feedback_routing_max_adjustment": float("nan")}):
        with pytest.raises(ValidationError):
            MultiAccountConfig(**values)


@pytest.mark.parametrize("dimension", ["cost", "latency"])
def test_zero_median_keeps_known_zero_distinct_from_positive_peers(dimension):
    cfg = MultiAccountConfig(enable_feedback_routing=True, reliability_weight=0,
                             latency_weight=0 if dimension == "cost" else 5,
                             cost_weight=10 if dimension == "cost" else 0)
    scores = AccountScoreboard(cfg, clock=lambda: NOW)
    candidates = []
    for ref, value in (("a", 100), ("b", 0), ("c", 0)):
        for _ in range(3):
            scores.observe(ref, ok=True, cost_units=value if dimension == "cost" else 0,
                           wall_seconds=value if dimension == "latency" else 0)
        candidates.append(candidate(ref, "flash-lite", account_ref=ref))
    feedback = routing_snapshot(cfg, scores.snapshot(), owner="local", now=NOW)
    result = choose(candidates, account_feedback=feedback, now=NOW)
    assert result["binding_ref"] == "b"
    evidence = {row["binding_id"]: row["score_breakdown"]["account_feedback"] for row in result["candidates"]}
    assert evidence["a"]["adjustment"] < 0
    assert evidence["b"]["adjustment"] == evidence["c"]["adjustment"] == 0


def test_finite_extreme_measurements_do_not_overflow_decision_evidence():
    feedback = snapshot(a_cost=1e308, b_cost=1e308, a_latency=1e308, b_latency=1e308)
    result = choose(pool(), account_feedback=feedback, now=NOW)
    for row in result["candidates"]:
        evidence = row["score_breakdown"]["account_feedback"]
        assert evidence["cost_reference"] == evidence["latency_reference"] == 1e308
    json.dumps(result, allow_nan=False)


def test_arithmetic_failure_preserves_all_original_scores():
    feedback = snapshot(a_ok=False, reliability_weight=1.7e308, cost_weight=1.7e308, latency_weight=1.7e308)
    result = choose(pool(), account_feedback=feedback, now=NOW)
    assert result["binding_ref"] == "a"
    assert all("account_feedback" not in row["score_breakdown"] for row in result["candidates"])
    json.dumps(result, allow_nan=False)
