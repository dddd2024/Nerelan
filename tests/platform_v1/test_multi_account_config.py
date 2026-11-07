"""Validated configuration for the multi-account orchestration brain.

Mirrors the repo's provider-free, deterministic test style: no I/O, no network.
"""
import pytest
from pydantic import ValidationError

from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig


def test_defaults_are_valid():
    cfg = MultiAccountConfig()
    # 1800 s, not 600: a provider that re-reads lazily leaves readings older than
    # ten minutes, and treating those as STALE emptied a real eleven-account pool.
    assert cfg.observation_freshness_seconds == 1800
    assert cfg.magpie_max_age_seconds == 2400
    assert cfg.reroute_max_attempts == 3
    assert cfg.dead_letter_enabled is True
    assert cfg.enable_self_evolution is True


def test_freshness_must_not_exceed_magpie_max_age():
    with pytest.raises(ValidationError):
        MultiAccountConfig(observation_freshness_seconds=1000, magpie_max_age_seconds=900)


def test_positive_int_and_percent_bounds():
    with pytest.raises(ValidationError):
        MultiAccountConfig(reroute_max_attempts=0)
    with pytest.raises(ValidationError):
        MultiAccountConfig(high_utilization_threshold=120.0)
    with pytest.raises(ValidationError):
        MultiAccountConfig(small_task_percent_ceiling=-1.0)


def test_high_threshold_must_exceed_small_ceiling():
    with pytest.raises(ValidationError):
        MultiAccountConfig(high_utilization_threshold=1.0, small_task_percent_ceiling=2.0)


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        MultiAccountConfig(unknown_knob=1)


def test_from_env_relocates_store(monkeypatch, tmp_path):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_STORE", str(tmp_path / "be.json"))
    cfg = MultiAccountConfig.from_env()
    assert cfg.break_even_store_path == tmp_path / "be.json"


def test_validate_assignment_blocks_bad_mutation():
    cfg = MultiAccountConfig()
    with pytest.raises(ValidationError):
        cfg.reroute_max_attempts = 0


def test_environment_controls_learning_thresholds_weights_and_backoff(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_SELF_EVOLUTION", "false")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_MIN_OBSERVATIONS_PER_MODE", "7")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_COST_WEIGHT", "2.5")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_FAILURE_BACKOFF_MAX_SECONDS", "1200")
    cfg = MultiAccountConfig.from_env()
    assert cfg.enable_self_evolution is False
    assert cfg.min_observations_per_mode == 7
    assert cfg.cost_weight == 2.5
    assert cfg.failure_backoff_max_seconds == 1200
    assert MultiAccountConfig.from_env(cost_weight=0).cost_weight == 0


@pytest.mark.parametrize("field,value", [
    ("ENABLE_SELF_EVOLUTION", "perhaps"), ("MIN_OBSERVATIONS_PER_MODE", "2"),
    ("MIN_OBSERVATIONS_PER_MODE", "3.5"), ("COST_WEIGHT", "nan"),
    ("LATENCY_WEIGHT", "inf"), ("FAILURE_BACKOFF_MAX_SECONDS", "-1"),
])
def test_invalid_environment_is_rejected(monkeypatch, field, value):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_" + field, value)
    with pytest.raises(ValidationError):
        MultiAccountConfig.from_env()


# --- v3 knobs: cost ceiling, alerting, run duration, policy clamps -----------

def test_v3_defaults_keep_previous_behaviour():
    cfg = MultiAccountConfig()
    # Nothing is capped, alerted on by default via logging, or time-limited
    # unless an operator opts in — a default must never silently change a run.
    assert cfg.cost_budget_enabled is False
    assert cfg.max_run_duration_seconds == 0.0
    assert cfg.max_idle_seconds == 0.0
    assert cfg.alert_log_enabled is False
    assert cfg.policy_enabled is True
    assert cfg.policy_max_bonus_points == 12.0


def test_an_enforced_budget_requires_a_positive_ceiling():
    with pytest.raises(ValidationError):
        MultiAccountConfig(cost_budget_enabled=True)


def test_fractions_must_stay_inside_the_unit_interval():
    for field in ("cost_budget_soft_ratio", "policy_max_weight_drift_ratio", "policy_step_ratio"):
        with pytest.raises(ValidationError):
            MultiAccountConfig(**{field: 0.0})
        with pytest.raises(ValidationError):
            MultiAccountConfig(**{field: 1.5})


def test_idle_window_cannot_exceed_the_run_budget():
    with pytest.raises(ValidationError):
        MultiAccountConfig(max_run_duration_seconds=100.0, max_idle_seconds=200.0)


def test_target_success_rate_must_exceed_the_alert_floor():
    with pytest.raises(ValidationError):
        MultiAccountConfig(alert_min_success_rate=0.9, policy_target_success_rate=0.5)


def test_env_can_enable_the_cost_ceiling(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_COST_BUDGET", "true")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_COST_BUDGET_UNITS", "25")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_MAX_RUN_SECONDS", "3600")
    cfg = MultiAccountConfig.from_env()
    assert cfg.cost_budget_enabled is True
    assert cfg.cost_budget_units == 25.0
    assert cfg.max_run_duration_seconds == 3600.0


def test_explicit_override_wins_over_the_environment(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_REROUTE_ATTEMPTS", "9")
    assert MultiAccountConfig.from_env(reroute_max_attempts=2).reroute_max_attempts == 2


def test_a_malformed_env_value_fails_fast_instead_of_widening_a_limit(monkeypatch):
    """A typo must stop the deployment, not silently become the permissive default."""
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_MAX_RUN_SECONDS", "not-a-number")
    with pytest.raises(ValidationError):
        MultiAccountConfig.from_env()


# --- the deployment surface must cover the model -----------------------------

def test_every_knob_is_reachable_from_the_environment():
    """A knob that only exists in Python is not configurable for an unattended run.

    Pins the coverage so a new field cannot be added without also deciding how an
    operator sets it — or explicitly listing it as owning its own variable.
    """
    from reverse_agent.platform_v1.multi_account.config import (
        _ENV_OWN_VARIABLE, _ENV_SCALARS)

    fields = set(MultiAccountConfig.model_fields)
    assert not fields - set(_ENV_SCALARS) - set(_ENV_OWN_VARIABLE)
    assert not set(_ENV_SCALARS) - fields, "the map must not name a removed knob"
    assert len(set(_ENV_SCALARS.values())) == len(_ENV_SCALARS), "variables must be unique"
    assert all(name.startswith("REVERSE_AGENT_") for name in _ENV_SCALARS.values())


def test_the_self_evolution_clamps_are_settable_from_the_environment(monkeypatch):
    """自进化限幅 must be tunable without a code change, and stay bounded."""
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_POLICY_STEP", "0.1")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_POLICY_DRIFT", "0.2")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_POLICY_MIN_SAMPLES", "8")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_POLICY_TARGET_SUCCESS", "0.9")
    cfg = MultiAccountConfig.from_env()
    assert cfg.policy_step_ratio == 0.1
    assert cfg.policy_max_weight_drift_ratio == 0.2
    assert cfg.policy_min_samples == 8
    assert cfg.policy_target_success_rate == 0.9


def test_boolean_knobs_are_parsed_even_when_they_do_not_end_in_enabled(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_PERSIST_STATE", "false")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_SCORING", "off")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_SELF_EVOLUTION", "0")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_CALIBRATION_FEEDBACK", "yes")
    cfg = MultiAccountConfig.from_env()
    assert cfg.persist_account_state is False
    assert cfg.enable_account_scoring is False
    assert cfg.enable_self_evolution is False
    assert cfg.calibration_feedback_enabled is True


def test_a_bad_clamp_still_fails_fast(monkeypatch):
    """A typo in a limit must stop startup, not silently widen it."""
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_POLICY_STEP", "5.0")
    with pytest.raises(ValidationError):
        MultiAccountConfig.from_env()


def test_alert_and_backoff_knobs_are_reachable(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ALERT_STREAK", "4")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_BACKOFF_MAX", "1200")
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_COST_WEIGHT", "20")
    cfg = MultiAccountConfig.from_env()
    assert cfg.alert_failure_streak_threshold == 4
    assert cfg.failure_backoff_max_seconds == 1200.0
    assert cfg.cost_weight == 20.0


def test_the_env_example_documents_every_variable():
    """A knob nobody can find is a knob nobody can use.

    ``.env.example`` is the operator-facing list; keep it in step with the map so
    a new variable cannot ship undocumented (or a stale one linger).
    """
    import re
    from pathlib import Path

    from reverse_agent.platform_v1.multi_account.config import _ENV_SCALARS

    text = (Path(__file__).resolve().parents[2] / ".env.example").read_text(encoding="utf-8")
    documented = set(re.findall(r"^(REVERSE_AGENT_[A-Z0-9_]+)=", text, re.M))
    owned = {"REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "REVERSE_AGENT_MULTI_ACCOUNT_STORE",
             "REVERSE_AGENT_ACCOUNT_ROUTING", "REVERSE_AGENT_MAGPIE_URL",
             "REVERSE_AGENT_MAGPIE_EXE"}
    assert not set(_ENV_SCALARS.values()) - documented
    assert not documented - set(_ENV_SCALARS.values()) - owned - {
        "REVERSE_AGENT_OLLYDBG_PATH", "REVERSE_AGENT_SAMPLE_PATH"}
