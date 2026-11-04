"""Validated configuration for the multi-account orchestration brain.

Mirrors the repo's provider-free, deterministic test style: no I/O, no network.
"""
import pytest
from pydantic import ValidationError

from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig


def test_defaults_are_valid():
    cfg = MultiAccountConfig()
    assert cfg.observation_freshness_seconds == 600
    assert cfg.magpie_max_age_seconds == 900
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
