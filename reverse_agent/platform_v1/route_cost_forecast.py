"""Prospective cache-aware expected cost per candidate route (#1304 C1.1/C1.2).

Stateless forecast helper for the existing model selector: for one otherwise
eligible route it estimates the probability that the task's prompt prefix is
served from the provider prompt cache and prices the expected token mix at
vendor list prices. It never mutates state, never stores observations and
never changes selection order by itself — wiring it into ``model_router``
ranking is C1, sequenced behind the #1267 benchmark and coordination with
#1170/#1281. Every figure is an ESTIMATED_LIST_PRICE equivalent, never a bill;
missing data fails conservative (cold) with explicit uncertainty instead of
fabricating cache benefits.
"""
from __future__ import annotations

from statistics import median
from typing import Any, Iterable, Mapping

from ..model_access import pricing
from ..model_access.quota_forecast import parse_time

# Conservative warm window when the provider's cache TTL is unknown; shorter
# than or equal to the cold-gap family used by quota_reservation.task_need.
DEFAULT_WARM_TTL_SECONDS = 3600.0


def _cache_read_ratio(observation: Mapping[str, Any]) -> float | None:
    cache_read = observation.get("cache_read")
    prompt = observation.get("input")
    if cache_read is None or prompt is None:
        return None
    # Separately reported cache writes are part of the same prompt; omitting
    # them would inflate the observed affinity (input=0, read=100, write=900
    # must rate 0.1, not 1.0).
    cache_write = observation.get("cache_write") or 0
    total = prompt + cache_read + cache_write
    if total <= 0:
        return None
    return min(1.0, max(0.0, cache_read / total))


def forecast_route_cost(
    observations: Iterable[Mapping[str, Any]],
    *,
    model: str,
    provider_id: str,
    account_ref: str,
    prompt_tokens: int,
    prefix_fingerprint: str,
    now: float,
    ttl_seconds: float | None = None,
    expected_output_tokens: int | None = None,
    price_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Expected warm/cold token mix and list-price cost for one candidate route.

    ``observations`` are historical normalized usage records (usage_ledger
    counter semantics: ``input`` is non-cached input, ``cache_read`` tokens
    served from cache) with ``model_id``/``provider_id``/``account_ref``,
    ``created_at``, ``cache_read``/``input`` and an optional non-sensitive
    ``prefix_fingerprint``. Only records on the exact same route (model,
    provider, account) with the same prefix fingerprint, inside the cache TTL,
    count as warm evidence; everything else is cold. The uncached prompt
    fraction is charged as a cache write this request (conservative upper
    bound). Output tokens are priced only when a forecast is supplied.
    """
    if prompt_tokens < 0:
        raise ValueError("prompt_tokens_must_not_be_negative")
    ttl = DEFAULT_WARM_TTL_SECONDS if ttl_seconds is None else max(0.0, float(ttl_seconds))
    reasons: list[str] = []
    if ttl_seconds is None:
        reasons.append("ttl_assumed_1h")

    same_route = [
        o for o in observations
        if (o.get("model_id"), o.get("provider_id"), o.get("account_ref"))
        == (model, provider_id, account_ref)
    ]
    if not same_route:
        reasons.append("no_observations_for_route")
    ratios: list[float] = []
    expired = mismatched = untimestamped = unmeasured = False
    for observation in same_route:
        created = parse_time(observation.get("created_at") or observation.get("observed_at"))
        if created is None:
            untimestamped = True
            continue
        if now - created > ttl:
            expired = True
            continue
        if not observation.get("prefix_fingerprint") or observation.get("prefix_fingerprint") != prefix_fingerprint:
            mismatched = True
            continue
        ratio = _cache_read_ratio(observation)
        if ratio is None:
            unmeasured = True
            continue
        ratios.append(ratio)
    if expired:
        reasons.append("warm_window_expired")
    if mismatched:
        reasons.append("prefix_fingerprint_mismatch")
    if untimestamped:
        reasons.append("observation_without_timestamp")
    if unmeasured:
        reasons.append("observation_without_cache_counters")

    uncertainty: list[str] = []
    if ratios:
        probability = min(1.0, max(0.0, median(ratios)))
        probability_basis = f"observed_affinity(n={len(ratios)})"
    else:
        # Predicted cold start, never an observed hit: the conservative
        # assumption when no compatible evidence exists.
        probability = 0.0
        probability_basis = "cold_assumption"
        uncertainty.append("cold_assumption")

    cache_read_tokens = round(prompt_tokens * probability)
    input_uncached = prompt_tokens - cache_read_tokens
    cache_write_tokens = input_uncached
    expected_tokens: dict[str, int | None] = {
        "input": input_uncached,
        "cache_read": cache_read_tokens,
        "cache_write": cache_write_tokens,
        "output": expected_output_tokens,
    }
    if expected_output_tokens is None:
        uncertainty.append("no_output_forecast")

    priced = {name: value for name, value in expected_tokens.items() if value}
    fact = pricing.equivalent_cost(model, priced, snapshot=price_snapshot)
    list_price_usd = fact.get("usd")
    if fact.get("state") != "ESTIMATED" or list_price_usd is None:
        uncertainty.append("unknown_price")
        if fact.get("reason"):
            reasons.append(str(fact["reason"]))

    return {
        "model": model,
        "provider_id": provider_id,
        "account_ref": account_ref,
        "cache_read_probability": probability,
        "probability_basis": probability_basis,
        "warm_ttl_seconds": ttl,
        "warm_observation_count": len(ratios),
        "route_observation_count": len(same_route),
        "expected_tokens": expected_tokens,
        "list_price_usd": list_price_usd,
        "cost_provenance": fact.get("provenance", "UNKNOWN"),
        "price_notes": list(fact.get("notes", ())),
        "uncertainty": uncertainty,
        "reasons": reasons,
    }
