"""Equivalent cost at the model vendor's list price (provider-free, vendored snapshot)."""
from __future__ import annotations

from reverse_agent.model_access.pricing import build_snapshot, equivalent_cost, load_snapshot, lookup_price

SNAPSHOT = {"source": "test", "fetched_at": "2026-10-14", "models": {
    "anthropic": {"claude-sonnet-5-5": {"input": 2, "output": 10, "cache_read": 0.1, "cache_write": 2.5}},
    "zhipuai": {"glm-5.2": {"input": 1.4, "output": 4.4}},
    "openai": {"gpt-6.1-sol": {"input": 2, "output": 10, "cache_read": 0.1, "tiered": True}},
}}


def test_cost_uses_the_model_makers_price_for_every_counter():
    cost = equivalent_cost("claude-sonnet-5-5", {"input": 1_000_000, "cache_read": 2_000_000,
                                                 "cache_write": 400_000, "output": 100_000}, SNAPSHOT)
    assert cost["state"] == "ESTIMATED" and cost["vendor"] == "anthropic"
    assert cost["usd"] == 2 + 0.2 + 1.0 + 1.0 and cost["notes"] == []
    assert cost["provenance"] == "ESTIMATED_LIST_PRICE" and cost["price_as_of"] == "2026-10-14"


def test_gateway_prefixes_and_context_suffixes_resolve_to_the_vendor_model():
    assert lookup_price("litellm-proxy/z-ai/glm-5.2", SNAPSHOT)[0] == "zhipuai"
    assert equivalent_cost("claude-sonnet-5-5[1m]", {"input": 1_000_000}, SNAPSHOT)["usd"] == 2.0


def test_missing_cache_prices_and_long_context_tiers_are_flagged_not_hidden():
    cost = equivalent_cost("glm-5.2", {"input": 0, "cache_read": 1_000_000, "output": 0}, SNAPSHOT)
    assert cost["usd"] == 1.4 and cost["notes"] == ["cache_read_priced_as_input"]
    assert "long_context_tier_not_applied" in equivalent_cost("gpt-6.1-sol", {"input": 1}, SNAPSHOT)["notes"]


def test_unknown_or_unresolved_models_are_never_priced():
    assert equivalent_cost("sonnet", {"input": 5}, SNAPSHOT)["reason"] == "model_unresolved"
    assert equivalent_cost("", {"input": 5}, SNAPSHOT)["reason"] == "model_unresolved"
    assert equivalent_cost("mystery-9", {"input": 5}, SNAPSHOT)["reason"] == "vendor_unknown"
    assert equivalent_cost("claude-unreleased-9", {"input": 5}, SNAPSHOT)["reason"] == "no_list_price"
    assert equivalent_cost("claude-unreleased-9", {"input": 5}, SNAPSHOT)["usd"] is None


def test_snapshot_keeps_only_model_makers_and_priced_models():
    raw = {"anthropic": {"models": {"claude-x": {"cost": {"input": 1, "output": 2, "cache_read": 0.1}},
                                    "claude-free-text": {"cost": {"input": "n/a"}}}},
           "some-reseller": {"models": {"claude-x": {"cost": {"input": 0.1, "output": 0.2}}}},
           "openai": {"models": {"gpt-y": {"cost": {"input": 1, "output": 2, "tiers": [{"input": 3}]}}}}}
    snapshot = build_snapshot(raw, fetched_at="2026-10-14")
    assert snapshot["models"] == {"anthropic": {"claude-x": {"input": 1, "output": 2, "cache_read": 0.1}},
                                  "openai": {"gpt-y": {"input": 1, "output": 2, "tiered": True}}}


def test_vendored_snapshot_prices_the_models_in_use():
    snapshot = load_snapshot()
    assert snapshot["source"] == "https://models.dev/api.json" and snapshot["fetched_at"]
    for model in ("claude-sonnet-5-5", "claude-opus-5-5", "gpt-6.1-sol", "glm-5.2", "kimi-k3"):
        assert lookup_price(model)[1] is not None, model
