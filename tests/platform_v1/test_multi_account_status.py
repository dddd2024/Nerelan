"""Status perception: account/quota health, freshness, headroom, anomalies.

Perception is tested with an injected observation source so it stays decoupled
from Magpie; a light end-to-end check exercises the reused
``pool_account_quotas`` projection. No network, no credentials.
"""
from datetime import datetime, timezone

from reverse_agent.platform_v1.multi_account.status import (
    AccountHealth, AccountStatus, MultiAccountStatusMonitor, merge_account_quotas,
    pool_account_quotas,
)
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig


NOW = 1_700_000_000.0


def iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def win(used_percent, *, resets_at=None, status=None, reset_passed=False):
    return {"window": "five_hour", "used_percent": used_percent,
            "resets_at": resets_at, "reset_passed": reset_passed, "status": status,
            "source": "magpie"}


def ev(account_ref, *, provider="codex", used_percent=10.0, observed_age=0.0,
       status=None, reset_passed=False, resets_at=None):
    return {"account_ref": account_ref, "provider": provider,
            "state": "OBSERVED", "observed_at": iso(NOW - observed_age),
            "windows": [win(used_percent, resets_at=resets_at, status=status,
                            reset_passed=reset_passed)]}


def make_monitor(fetch):
    return MultiAccountStatusMonitor(MultiAccountConfig(), fetch_quotas=fetch)


def test_healthy_account():
    m = make_monitor(lambda _: {"a1": ev("a1", used_percent=40.0)})
    (status,) = m.perceive(None, now=NOW)
    assert status.health is AccountHealth.HEALTHY
    assert status.headroom_pct == 60.0
    assert status.provider == "codex"


def test_exhausted_account():
    m = make_monitor(lambda _: {"a1": ev("a1", used_percent=100.0, status="rejected")})
    (status,) = m.perceive(None, now=NOW)
    assert status.health is AccountHealth.EXHAUSTED
    assert "exhausted:five_hour" in status.anomaly_flags
    assert "rate_limited:five_hour" in status.anomaly_flags


def test_abnormal_account():
    m = make_monitor(lambda _: {"a1": ev("a1", status="unauthorized")})
    (status,) = m.perceive(None, now=NOW)
    assert status.health is AccountHealth.ABNORMAL
    assert "abnormal:five_hour" in status.anomaly_flags


def test_degraded_high_utilization():
    m = make_monitor(lambda _: {"a1": ev("a1", used_percent=95.0)})
    (status,) = m.perceive(None, now=NOW)
    assert status.health is AccountHealth.DEGRADED
    assert "high_utilization:five_hour" in status.anomaly_flags


def test_stale_account():
    # Well past the 1800 s budget: this test is about the rule, not the threshold.
    m = make_monitor(lambda _: {"a1": ev("a1", observed_age=3600.0)})
    (status,) = m.perceive(None, now=NOW)
    assert status.health is AccountHealth.STALE
    assert status.freshness_age == 3600.0


def test_unknown_account():
    m = make_monitor(lambda _: {"a1": {"account_ref": "a1", "provider": "codex",
                                       "windows": [], "observed_at": None}})
    (status,) = m.perceive(None, now=NOW)
    assert status.health is AccountHealth.UNKNOWN


def test_reset_soon_anomaly():
    future = iso(NOW + 600.0)  # within 1800s reset_soon threshold
    m = make_monitor(lambda _: {"a1": ev("a1", used_percent=20.0, resets_at=future)})
    (status,) = m.perceive(None, now=NOW)
    assert "reset_soon:five_hour" in status.anomaly_flags


def test_health_summary_counts():
    fetch = lambda _: {
        "a1": ev("a1", used_percent=40.0),
        "a2": ev("a2", used_percent=100.0, status="rejected"),
        "a3": ev("a3", observed_age=3600.0),
    }
    m = make_monitor(fetch)
    summary = m.health_summary(m.perceive(None, now=NOW))
    assert summary["total_accounts"] == 3
    assert summary["eligible_accounts"] == 1  # only the healthy one
    assert summary["by_health"]["EXHAUSTED"] == 1
    assert summary["by_health"]["STALE"] == 1
    assert summary["best_headroom_pct"] == 60.0


def test_pool_account_quotas_preserves_all_accounts():
    # Two real accounts of the SAME routeable provider must both survive (the
    # defect this package fixes). Exercises the reused magpie_account_quotas
    # projection, which keeps one entry per account_ref rather than one per
    # provider.
    future = iso(NOW + 3600.0)
    snapshot = {"status": "available", "accounts": [
        {"account_ref": "codex-a", "provider": "codex", "state": "FRESH",
         "windows": [{"name": "five_hour", "used_percent": 10, "resets_at": future,
                      "unlimited": False}]},
        {"account_ref": "codex-b", "provider": "codex", "state": "FRESH",
         "windows": [{"name": "five_hour", "used_percent": 20, "resets_at": future,
                      "unlimited": False}]},
    ]}
    pooled = pool_account_quotas(snapshot, now=NOW)
    assert set(pooled.keys()) == {"codex-a", "codex-b"}
    assert pooled["codex-a"]["account_ref"] == "codex-a"
    assert pooled["codex-b"]["provider"] == "codex"  # route key reused, account preserved
    assert "windows" in pooled["codex-b"]


def test_merge_account_quotas_is_additive_and_keeps_provider_key():
    # The dispatch quota view consumes BOTH provider-keyed lookups and
    # account_ref-keyed lookups. The merge must keep the legacy provider key
    # while also preserving every account under its account_ref (the defect fix).
    future = iso(NOW + 3600.0)
    snapshot = {"status": "available", "accounts": [
        {"account_ref": "codex-a", "provider": "codex", "state": "FRESH",
         "windows": [{"name": "five_hour", "used_percent": 10, "resets_at": future,
                      "unlimited": False}]},
        {"account_ref": "codex-b", "provider": "codex", "state": "FRESH",
         "windows": [{"name": "five_hour", "used_percent": 20, "resets_at": future,
                      "unlimited": False}]},
    ]}
    local = {"claude-code": {"state": "OBSERVED", "provider": "claude-code", "windows": []}}
    merged = merge_account_quotas(local, snapshot, now=NOW)
    # Legacy provider key from Magpie is present (backward compatible).
    assert "codex" in merged
    # A local-only provider key is preserved (additive; no key dropped).
    assert merged["claude-code"] is local["claude-code"]
    # Every account preserved under its own account_ref (the defect fix).
    assert set(a for a in merged if a.startswith("codex-")) == {"codex-a", "codex-b"}


# --- freshness budget vs a lazy provider -------------------------------------

def test_a_lazily_read_account_stays_usable_for_half_an_hour():
    """Real evidence: readings were 20-30 minutes old and the pool emptied.

    Magpie re-reads on demand, not on a timer, so a 600 s budget turned a healthy
    eleven-account pool into one usable account within half an hour while nothing
    was wrong. The default now tolerates a lazy re-read.
    """
    m = make_monitor(lambda _: {"a1": ev("a1", used_percent=40.0, observed_age=1500.0)})
    (status,) = m.perceive(None, now=NOW)
    assert status.health is AccountHealth.HEALTHY, "25 minutes old must still be usable"
    assert status.headroom_pct == 60.0


def test_a_genuinely_stale_reading_is_still_caught():
    """Raising the budget must not disable the freshness rule."""
    m = make_monitor(lambda _: {"a1": ev("a1", observed_age=3600.0)})
    (status,) = m.perceive(None, now=NOW)
    assert status.health is AccountHealth.STALE
    assert "stale" in status.anomaly_flags


def test_the_freshness_budget_still_fits_inside_the_snapshot_age():
    """The invariant that keeps two clocks from disagreeing."""
    cfg = MultiAccountConfig()
    assert cfg.observation_freshness_seconds < cfg.magpie_max_age_seconds
