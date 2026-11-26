"""Tests for dynamic invalidation of cached probe holds on recovery or config change."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reverse_agent.platform_v1.model_availability import AvailabilityCache, NO_CREDITS, observation
from reverse_agent.platform_v1.pool_verifier import PoolVerifier


def _binding(binding_id: str = "opencode:m1", model_id: str = "claude-sonnet", updated_at: str = "2027-01-01T00:00:00Z"):
    return {
        "binding_id": binding_id,
        "model_id": model_id,
        "executor_id": "opencode",
        "connection_id": "conn-1",
        "enabled": True,
        "cost_class": "subscription",
        "native_endpoint": None,
        "updated_at": updated_at,
    }


def _connection(base_url: str = "https://relay.example/v1", updated_at: str = "2027-01-01T00:00:00Z"):
    return {
        "connection_id": "conn-1",
        "base_url": base_url,
        "auth_method": "api_key",
        "account_ref": "codex:1",
        "enabled": True,
        "updated_at": updated_at,
    }


def test_availability_cache_clears_no_credits_only_on_credit_recovery():
    cache = AvailabilityCache()
    b, c = _binding(), _connection()
    t0 = 1_700_000_000.0
    cache.remember(b, c, observation(now=t0, state="UNAVAILABLE", reason=NO_CREDITS, ttl_seconds=7 * 86400),
                   config_version="v1")

    held = cache.check(b, c, allow_probe=False, now=t0 + 60, recovered_at=t0 + 30, config_version="v1")
    assert held["state"] == "UNAVAILABLE" and held["reason"] == NO_CREDITS

    probes = []
    recovered = cache.check(
        b, c,
        probe=lambda item: (probes.append(item["binding_id"]), {"ok": True})[1],
        allow_probe=True,
        now=t0 + 120,
        credit_recovered_at=t0 + 90,
        config_version="v1",
    )
    assert probes == ["opencode:m1"]
    assert recovered["state"] == "AVAILABLE"
    assert recovered["config_version"] == "v1"


def test_availability_cache_clears_quota_exhausted_on_window_recovery():
    cache = AvailabilityCache()
    b, c = _binding(), _connection()
    t0 = 1_700_000_000.0
    cache.remember(b, c, observation(now=t0, state="UNAVAILABLE", reason="quota_exhausted", ttl_seconds=86400),
                   config_version="v1")

    probes = []
    recovered = cache.check(
        b, c,
        probe=lambda item: (probes.append(item["binding_id"]), {"ok": True})[1],
        allow_probe=True,
        now=t0 + 120,
        recovered_at=t0 + 90,
        config_version="v1",
    )
    assert probes == ["opencode:m1"]
    assert recovered["state"] == "AVAILABLE"


def test_availability_cache_does_not_clear_rate_limit_on_quota_or_credit_recovery():
    cache = AvailabilityCache()
    b, c = _binding(), _connection()
    t0 = 1_700_000_000.0
    cache.remember(b, c, observation(now=t0, state="TRANSIENT", reason="rate_limited", ttl_seconds=1800),
                   config_version="v1")

    still_held = cache.check(
        b, c,
        allow_probe=False,
        now=t0 + 120,
        recovered_at=t0 + 90,
        credit_recovered_at=t0 + 90,
        config_version="v1",
    )
    assert still_held["state"] == "TRANSIENT" and still_held["reason"] == "rate_limited"


def test_availability_cache_does_not_clear_model_not_found_on_quota_recovery():
    cache = AvailabilityCache()
    b, c = _binding(), _connection()
    t0 = 1_700_000_000.0
    cache.remember(b, c, observation(now=t0, state="UNAVAILABLE", reason="model_not_found", ttl_seconds=86400),
                   config_version="v1")

    still_held = cache.check(
        b, c,
        allow_probe=False,
        now=t0 + 120,
        recovered_at=t0 + 90,
        credit_recovered_at=t0 + 90,
        config_version="v1",
    )
    assert still_held["state"] == "UNAVAILABLE" and still_held["reason"] == "model_not_found"


def test_availability_cache_clears_any_hold_on_config_change():
    cache = AvailabilityCache()
    b, c = _binding(), _connection()
    t0 = 1_700_000_000.0
    cache.remember(b, c, observation(now=t0, state="UNAVAILABLE", reason="model_not_found", ttl_seconds=86400),
                   config_version="v1")

    probes = []
    reprobed = cache.check(
        b, c,
        probe=lambda item: (probes.append(item["binding_id"]), {"ok": True})[1],
        allow_probe=True,
        now=t0 + 120,
        config_version="v2",
    )
    assert probes == ["opencode:m1"]
    assert reprobed["state"] == "AVAILABLE"
    assert reprobed["config_version"] == "v2"


def test_availability_cache_returns_invalidation_reason_when_probe_deferred():
    cache = AvailabilityCache()
    b, c = _binding(), _connection()
    t0 = 1_700_000_000.0
    cache.remember(b, c, observation(now=t0, state="UNAVAILABLE", reason="http_401", ttl_seconds=86400),
                   config_version="v1")

    res = cache.check(b, c, allow_probe=False, now=t0 + 120, config_version="v2")
    assert res == {"state": "UNKNOWN", "reason": "config_changed"}


def test_trusted_host_invalidation_distinguishes_5h_window_from_credits_and_rate_limit(tmp_path):
    from reverse_agent.model_access.store import ModelProfileStore
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    task_store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    host = CombinedTrustedHost(store=ModelProfileStore(), task_store=task_store, auth_list_probe=lambda: {})
    try:
        b = _binding()
        c = _connection()
        cfg1 = host._availability_config_version(b, c)
        cfg2 = host._availability_config_version(b, _connection(updated_at="2027-01-02T00:00:00Z"))
        assert cfg1 != cfg2

        cache = AvailabilityCache()
        host._availability_cache = cache
        t0 = 1_700_000_000.0
        obs_iso = datetime.fromtimestamp(t0 + 60, tz=timezone.utc).isoformat()
        host._magpie_provider_accounts = {"codex": ["codex:1"]}
        # A 5-hour time window does NOT invalidate a billing `no_credits` hold.
        host._magpie_account_readings = {
            "codex:1": {
                "account_ref": "codex:1",
                "provider": "codex",
                "state": "FRESH",
                "observed_at": obs_iso,
                "windows": [{"name": "5 hours", "used_percent": 15.0, "unlimited": False}],
            }
        }
        cache.remember(b, c, observation(now=t0, state="UNAVAILABLE", reason=NO_CREDITS, ttl_seconds=7 * 86400),
                       config_version=cfg1)
        rec_at, cred_at, cfg = host._availability_invalidation(
            b, c, cached_entry=cache.entries[cache.key(b, c)],
        )
        assert rec_at is None and cred_at is None and cfg == cfg1

        # A FRESH `Credits` window with headroom DOES clear `no_credits`.
        host._magpie_account_readings["codex:1"]["windows"] = [
            {"name": "Credits", "used_percent": 15.0, "unlimited": False}
        ]
        rec_at, cred_at, cfg = host._availability_invalidation(
            b, c, cached_entry=cache.entries[cache.key(b, c)],
        )
        assert rec_at is None and cred_at == t0 + 60 and cfg == cfg1

        # RPM/TPM `rate_limited` keeps its time cooldown even when Credits has headroom.
        cache.remember(b, c, observation(now=t0, state="TRANSIENT", reason="rate_limited", ttl_seconds=1800),
                       config_version=cfg1)
        rec_at, cred_at, cfg = host._availability_invalidation(
            b, c, cached_entry=cache.entries[cache.key(b, c)],
        )
        assert rec_at is None and cred_at is None and cfg == cfg1

        verifier = PoolVerifier(host)
        verifier._tried[b["binding_id"]] = t0
        verifier.clear_tried()
        assert b["binding_id"] not in verifier._tried
    finally:
        task_store._conn.close()
