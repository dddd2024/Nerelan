"""Deterministic provider-free fixtures for the route cost forecast (#1304 C3)."""
import pytest

from reverse_agent.model_access.quota_forecast import iso
from reverse_agent.platform_v1 import route_cost_forecast as rcf

MODEL = "gpt-6.1-sol"
SNAPSHOT = {"source": "fixture", "fetched_at": "2026-10-24T00:00:00Z",
            "models": {"openai": {MODEL: {"input": 1.0, "cache_read": 0.1,
                                          "cache_write": 1.25, "output": 2.0}}}}
NOW = 1_800_000_000.0


def obs(at, *, cache_read, prompt=100, fingerprint="fp-a", model=MODEL,
        provider="p1", account="acct-1", timestamp=True):
    row = {"model_id": model, "provider_id": provider, "account_ref": account,
           "input": prompt, "cache_read": cache_read, "prefix_fingerprint": fingerprint}
    if timestamp:
        row["created_at"] = iso(at)
    return row


def forecast(history, **kwargs):
    options = dict(model=MODEL, provider_id="p1", account_ref="acct-1",
                   prompt_tokens=1000, prefix_fingerprint="fp-a", now=NOW,
                   price_snapshot=SNAPSHOT)
    options.update(kwargs)
    return rcf.forecast_route_cost(history, **options)


def test_warm_affinity_prices_expected_token_mix():
    history = [obs(NOW - 60, cache_read=100)]  # one warm request, 50% read ratio
    fact = forecast(history, expected_output_tokens=200)
    assert fact["cache_read_probability"] == pytest.approx(0.5)
    assert fact["probability_basis"] == "observed_affinity(n=1)"
    assert fact["expected_tokens"] == {"input": 500, "cache_read": 500, "cache_write": 500, "output": 200}
    # 500*1.0 + 500*0.1 + 500*1.25 + 200*2.0 = 1575 (USD per 1M tokens)
    assert fact["list_price_usd"] == pytest.approx(0.001575)
    assert fact["cost_provenance"] == "ESTIMATED_LIST_PRICE"
    assert fact["uncertainty"] == [] and "ttl_assumed_1h" in fact["reasons"]


def test_even_sample_count_uses_median_ratio():
    history = [obs(NOW - 60, cache_read=25), obs(NOW - 30, cache_read=150, prompt=100)]  # 0.2, 0.6
    fact = forecast(history)
    assert fact["cache_read_probability"] == pytest.approx(0.4)
    assert fact["warm_observation_count"] == 2
    assert fact["expected_tokens"]["cache_read"] == 400


def test_cold_route_charges_full_cache_write():
    fact = forecast([], expected_output_tokens=0)
    assert fact["cache_read_probability"] == 0.0
    assert fact["probability_basis"] == "cold_assumption"
    assert fact["expected_tokens"] == {"input": 1000, "cache_read": 0, "cache_write": 1000, "output": 0}
    # 1000*1.0 + 1000*1.25 = 2250 per 1M
    assert fact["list_price_usd"] == pytest.approx(0.00225)
    assert "cold_assumption" in fact["uncertainty"]
    assert "no_observations_for_route" in fact["reasons"]


def test_ttl_lapse_invalidates_affinity():
    history = [obs(NOW - 7200, cache_read=100)]  # older than the assumed 1h TTL
    fact = forecast(history)
    assert fact["cache_read_probability"] == 0.0
    assert "warm_window_expired" in fact["reasons"]
    assert fact["warm_observation_count"] == 0 and fact["route_observation_count"] == 1
    # An explicit provider TTL keeps a recent-enough observation warm.
    assert forecast(history, ttl_seconds=8000)["cache_read_probability"] == pytest.approx(0.5)


def test_prefix_change_is_cold():
    history = [obs(NOW - 60, cache_read=100, fingerprint="fp-other")]
    fact = forecast(history)
    assert fact["cache_read_probability"] == 0.0
    assert "prefix_fingerprint_mismatch" in fact["reasons"]


def test_route_switch_has_no_affinity():
    history = [obs(NOW - 60, cache_read=100, account="acct-2"),
               obs(NOW - 60, cache_read=100, model="other-model"),
               obs(NOW - 60, cache_read=100, provider="p2")]
    fact = forecast(history)
    assert fact["cache_read_probability"] == 0.0
    assert fact["route_observation_count"] == 0
    assert "no_observations_for_route" in fact["reasons"]


def test_untimestamped_or_unmeasured_rows_never_inflate_affinity():
    history = [obs(NOW, cache_read=100, timestamp=False),
               obs(NOW - 60, cache_read=None, prompt=None)]
    fact = forecast(history)
    assert fact["cache_read_probability"] == 0.0
    assert fact["warm_observation_count"] == 0 and fact["route_observation_count"] == 2
    assert "observation_without_timestamp" in fact["reasons"]
    assert "observation_without_cache_counters" in fact["reasons"]


def test_unknown_price_fails_closed_without_fabricated_cost():
    fact = forecast([], model="vendor-unknown-model")
    assert fact["list_price_usd"] is None
    assert "unknown_price" in fact["uncertainty"]
    assert "vendor_unknown" in fact["reasons"]


def test_missing_cache_write_price_is_billed_as_input():
    snapshot = {"source": "fixture", "fetched_at": "2026-10-24T00:00:00Z",
                "models": {"openai": {MODEL: {"input": 1.0, "cache_read": 0.1, "output": 2.0}}}}
    fact = forecast([], price_snapshot=snapshot, expected_output_tokens=0)
    assert fact["list_price_usd"] == pytest.approx(0.002)  # 1000 input + 1000 write at input price
    assert fact["price_notes"] == ["cache_write_priced_as_input"]


def test_output_forecast_is_optional_and_flagged():
    fact = forecast([obs(NOW - 60, cache_read=100)])
    assert fact["expected_tokens"]["output"] is None
    assert "no_output_forecast" in fact["uncertainty"]


def test_negative_prompt_tokens_are_rejected():
    with pytest.raises(ValueError, match="prompt_tokens_must_not_be_negative"):
        forecast([], prompt_tokens=-1)
