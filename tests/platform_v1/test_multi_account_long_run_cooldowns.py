"""Long-run account failures must remain bounded and preserve isolation."""

import pytest

from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.cooldowns import QUARANTINE, CooldownRegistry


def test_thousands_of_consecutive_failures_keep_the_delay_capped():
    config = MultiAccountConfig()
    registry = CooldownRegistry(config)
    now = 1_700_000_000.0
    for _ in range(2000):
        entry = registry.record_failure("account", "task_failed", now=now)
        assert 0 <= entry.until - now <= config.failure_backoff_max_seconds
        now = entry.until + 1
    assert entry.streak == 2000
    assert entry.until == now - 1


def test_late_task_failure_cannot_replace_an_active_account_quarantine():
    registry = CooldownRegistry(MultiAccountConfig())
    first = registry.record_failure("account", "account_abnormal", now=100)
    late = registry.record_failure("account", "task_failed", now=101)
    assert late.tier == QUARANTINE
    assert late.kind == "account_abnormal"
    assert late.until >= first.until
    registry.clear_transient()
    registry.record_success("account", now=102)
    assert registry.is_cooling("account", now=102)


def test_success_after_quarantine_expiry_resets_the_failure_streak():
    registry = CooldownRegistry(MultiAccountConfig())
    entry = registry.record_failure("account", "account_abnormal", now=100)
    registry.record_success("account", now=entry.until + 1)
    assert registry.get("account") is None


def test_zero_base_and_large_multiplier_do_not_overflow():
    registry = CooldownRegistry(MultiAccountConfig(
        failure_backoff_base_seconds=0, failure_backoff_multiplier=1e300))
    for _ in range(10):
        entry = registry.record_failure("account", "task_failed", now=100)
    assert entry.until == 130


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_backoff_is_rejected(value):
    with pytest.raises(ValueError):
        MultiAccountConfig(failure_backoff_multiplier=value)
