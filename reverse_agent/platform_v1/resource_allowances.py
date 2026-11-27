"""Time-limited resources Magpie reports, as routing input (#1471, #1429).

Magpie reads every connected account. Two kinds of reading matter for routing
and were dropped before this module:

* A **model allowance**: a window named ``"<model> tokens"`` (for example
  WorkBuddy's ``"deepseek-v4.1-flash tokens (est.)"``, 200M a day). While it has
  headroom above a reserve and its reset is in the future, the matching binding
  costs nothing, so it routes as ``free`` instead of its namespace default.
* **Expiring credits**: a window with ``runs_out_at``/``runs_out`` (for example
  300 raccoon credits that lapse tomorrow). Unused, they are lost.

Both give a bounded preference that grows as the reset or expiry nears, so the
soonest-to-lapse resource is used first. The preference never makes a
subscription cheaper than a free route and never overrides a hard filter.

Fail-safe rules: only FRESH readings count; a provider with more than one account
(in any state) is ambiguous (the gateway picks the account, not us) and contributes
nothing; an allowance that names no model (WorkBuddy AI's "Free model tokens",
"input tokens") is reported but not attributed; an explicit Owner cost class always
wins; a weekly-paced provider is never made free (it keeps its subscription guards);
only bindings that run through the Magpie gateway are matched.
"""
from __future__ import annotations

from datetime import datetime
import os
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

# Headroom kept back so a nearly used allowance is not assumed free.
ALLOWANCE_RESERVE_PERCENT = 5.0
# Credits that run out within this horizon get a growing preference.
CREDIT_HORIZON_SECONDS = 7 * 86400
# Allowances resetting within this horizon get a growing preference.
ALLOWANCE_HORIZON_SECONDS = 86400
# Bounded preferences (score units; free costs 0, subscription at least 1).
ALLOWANCE_BASE_BONUS = .05
ALLOWANCE_URGENCY_BONUS = .25
CREDIT_URGENCY_BONUS = .5
DAILY_POOL_URGENCY_BONUS = .20
PROMO_BASE_BONUS = .08
PROMO_URGENCY_BONUS = .25

_MODEL_TOKENS = re.compile(
    r"\s*(?P<model>[A-Za-z0-9][A-Za-z0-9 ._:-]{0,120}?)\s+tokens(?:\s*\((?:est\.?|estimated)\))?\s*", re.I)
# Window titles that say "tokens" without naming a model.
_UNNAMED = frozenset({"free model", "free models", "model", "models", "free", "total", "daily", "weekly",
                      "monthly", "input", "output", "prompt", "completion", "cached", "cache", "premium",
                      "extra", "bonus", "remaining", "used"})
_PROMO_KEYWORDS = ("promo", "promotion", "限时免费", "free trial", "limited free", "limited-time free", "gift", "bonus credits")

EMPTY: dict[str, Any] = {"models": {}, "credits": {}, "unattributed": [], "ambiguous": []}


def _timestamp(value: Any) -> float | None:
    if not isinstance(value, str) or len(value) > 40:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.timestamp() if parsed.tzinfo else None


def _number(value: Any) -> float | None:
    return float(value) if type(value) in (int, float) and value == value and value >= 0 else None


def read_allowances(snapshot: Mapping[str, Any] | None, *, now: float) -> dict[str, Any]:
    """Allowances and expiring credits from one parsed Magpie snapshot; EMPTY when unusable."""
    if not isinstance(snapshot, Mapping) or snapshot.get("status") != "available":
        return {key: type(value)() for key, value in EMPTY.items()}
    # Every account Magpie lists, whatever its state: with more than one, the gateway
    # may pick any of them, so no single reading speaks for the route.
    by_provider: dict[str, list[Mapping[str, Any]]] = {}
    for account in snapshot.get("accounts") or ():
        if isinstance(account, Mapping) and isinstance(account.get("provider"), str) and account["provider"]:
            by_provider.setdefault(account["provider"].lower(), []).append(account)
    result: dict[str, Any] = {"models": {}, "credits": {}, "unattributed": [], "ambiguous": []}
    for provider, accounts in sorted(by_provider.items()):
        if len(accounts) != 1:
            result["ambiguous"].append(provider)
            continue
        account = accounts[0]
        if account.get("state") != "FRESH":
            continue
        for window in account.get("windows") or ():
            if not isinstance(window, Mapping) or not isinstance(window.get("name"), str):
                continue
            remaining = _number(window.get("remaining_percent"))
            resets_at = _timestamp(window.get("resets_at"))
            runs_out_at = _timestamp(window.get("runs_out_at"))
            runs_out = _number(window.get("runs_out"))
            if runs_out_at is not None and runs_out_at > now and runs_out:
                current = result["credits"].get(provider)
                if current is None or runs_out_at < current["runs_out_at"]:
                    result["credits"][provider] = {"provider": provider, "window": window["name"],
                                                   "runs_out_at": runs_out_at, "runs_out": runs_out,
                                                   "account_ref": account.get("account_ref")}
            if ("daily" in window["name"].lower() and remaining is not None
                    and remaining > ALLOWANCE_RESERVE_PERCENT and window.get("unlimited") is not True
                    and (resets_at is None or resets_at > now)):
                daily_map = result.setdefault("daily_pools", {})
                prev = daily_map.get(provider)
                if prev is None or (resets_at is not None and (prev.get("resets_at") is None or resets_at < prev["resets_at"])):
                    daily_map[provider] = {"provider": provider, "window": window["name"],
                                           "remaining_percent": remaining, "resets_at": resets_at,
                                           "limit": _number(window.get("limit")),
                                           "account_ref": account.get("account_ref")}
            promo_until = _timestamp(window.get("free_until") or window.get("promo_until")) or resets_at
            is_promo = (bool(window.get("promotional")) or bool(window.get("free_until"))
                        or any(kw in window["name"].lower() for kw in _PROMO_KEYWORDS))
            has_promo_headroom = (
                window.get("unlimited") is True
                or (remaining is not None and remaining > ALLOWANCE_RESERVE_PERCENT)
            )
            if is_promo and has_promo_headroom and (promo_until is None or promo_until > now):
                promo_models = [
                    str(m).strip().lower()
                    for m in (window.get("models") or ())
                    if isinstance(m, str) and m.strip()
                ]
                promo_map = result.setdefault("promotions", {})
                promo_entry = {
                    "provider": provider, "window": window["name"],
                    "remaining_percent": remaining, "free_until": promo_until,
                    "models": promo_models,
                    "account_ref": account.get("account_ref"),
                }
                prev_promo = promo_map.get(provider)
                if prev_promo is None or (promo_until is not None and (prev_promo.get("free_until") is None or promo_until < prev_promo["free_until"])):
                    promo_map[provider] = promo_entry
                for promo_model in promo_entry["models"]:
                    if promo_model == "*" or promo_model == f"{provider}/*":
                        continue
                    target_key = promo_model if "/" in promo_model else f"{provider}/{promo_model}"
                    result["models"].setdefault(target_key, {
                        "provider": provider, "window": window["name"],
                        "remaining_percent": remaining if remaining is not None else 100.0,
                        "resets_at": promo_until, "limit": _number(window.get("limit")),
                        "account_ref": account.get("account_ref"), "model": promo_model.split("/", 1)[-1],
                        "promotional": True,
                    })
            match = _MODEL_TOKENS.fullmatch(window["name"])
            if match is None or remaining is None or window.get("unlimited") is True:
                continue
            model = match["model"].lower()
            entry = {"provider": provider, "window": window["name"], "remaining_percent": remaining,
                     "resets_at": resets_at, "limit": _number(window.get("limit")),
                     "account_ref": account.get("account_ref")}
            if model in _UNNAMED or " " in model:  # a description, not a model id
                result["unattributed"].append(entry)
            else:
                result["models"][f"{provider}/{model}"] = {**entry, "model": model}
    return result


def allowance_active(allowance: Mapping[str, Any] | None, *, now: float) -> bool:
    if not allowance:
        return False
    resets_at = allowance.get("resets_at")
    return (allowance.get("remaining_percent", 0) > ALLOWANCE_RESERVE_PERCENT
            and (resets_at is None or resets_at > now))


def gateway_connection(connection: Mapping[str, Any], magpie_url: str | None = None) -> bool:
    """The connection is the local Magpie gateway (same loopback port as its URL)."""
    origin = urlsplit(magpie_url or os.environ.get("REVERSE_AGENT_MAGPIE_URL", "http://127.0.0.1:3425"))
    try:
        url = urlsplit(str(connection.get("base_url") or ""))
        port, expected = url.port, origin.port
    except ValueError:
        return False
    return url.hostname in {"127.0.0.1", "::1", "localhost"} and port is not None and port == expected


def effective_cost(binding: Mapping[str, Any], connection: Mapping[str, Any], owner: Mapping[str, Any],
                   allowances: Mapping[str, Any], *, now: float,
                   magpie_url: str | None = None) -> tuple[str, dict[str, Any]]:
    """The binding's cost class with Magpie's time-limited resources applied, and why.

    Returns ``(cost_class, resources)``; ``resources`` is empty when nothing applies.
    """
    from .routing_inputs import binding_cost_class, explicit_cost_class, weekly_pace_config
    cost_class = binding_cost_class(binding, connection, owner)
    # A weekly-paced account (Codex, Claude...) keeps its subscription guards: pacing,
    # quota capacity and reset buffers apply only to the subscription class.
    paced = {str(name).lower() for name in weekly_pace_config(owner).get("providers", ())}
    model_id = binding.get("model_id") if isinstance(binding.get("model_id"), str) else ""
    if "/" not in model_id or not allowances or not gateway_connection(connection, magpie_url):
        return cost_class, {}
    provider = model_id.split("/", 1)[0].lower()
    resources: dict[str, Any] = {}
    allowance = (allowances.get("models") or {}).get(model_id.lower())
    if allowance_active(allowance, now=now):
        resources["allowance"] = {key: allowance.get(key) for key in
                                  ("window", "remaining_percent", "resets_at", "limit")}
        if (cost_class == "subscription" and provider not in paced
                and not explicit_cost_class(binding, connection, owner)):
            resources["allowance"]["default_cost_class"] = cost_class
            cost_class = "free"
    credit = (allowances.get("credits") or {}).get(provider)
    if credit and cost_class in {"free", "subscription"}:
        resources["credit_expiry"] = {key: credit.get(key) for key in ("window", "runs_out_at", "runs_out")}
    daily = (allowances.get("daily_pools") or {}).get(provider)
    if daily and cost_class in {"free", "subscription"}:
        resources["daily_pool"] = {key: daily.get(key) for key in ("window", "remaining_percent", "resets_at", "limit")}
    promo = (allowances.get("promotions") or {}).get(provider)
    promo_models = promo.get("models") if isinstance(promo, Mapping) else None
    promo_matches = bool(
        isinstance(promo_models, (list, tuple, set, frozenset))
        and promo_models
        and (
            "*" in promo_models
            or f"{provider}/*" in promo_models
            or model_id.lower() in promo_models
            or model_id.split("/", 1)[1].lower() in promo_models
        )
    )
    if promo and promo_matches:
        free_until = promo.get("free_until")
        if free_until is None or free_until > now:
            resources["promotional_free"] = {key: promo.get(key) for key in ("window", "remaining_percent", "free_until")}
            if (cost_class == "subscription" and provider not in paced
                    and not explicit_cost_class(binding, connection, owner)):
                resources["promotional_free"]["default_cost_class"] = cost_class
                cost_class = "free"
    return cost_class, resources


def _approach(seconds_left: float, horizon: float) -> float:
    """0 at the horizon or beyond, rising to 1 when the moment is now."""
    return max(0., min(1., 1. - seconds_left / horizon))


def urgency(resources: Mapping[str, Any] | None, *, now: float) -> float:
    """Bounded preference for using a resource before it resets or runs out."""
    if not resources:
        return 0.
    bonus = 0.
    allowance = resources.get("allowance")
    if allowance:
        bonus += ALLOWANCE_BASE_BONUS
        resets_at = allowance.get("resets_at")
        if type(resets_at) in (int, float):
            bonus += ALLOWANCE_URGENCY_BONUS * _approach(resets_at - now, ALLOWANCE_HORIZON_SECONDS)
    credit = resources.get("credit_expiry")
    if credit and type(credit.get("runs_out_at")) in (int, float):
        bonus += CREDIT_URGENCY_BONUS * _approach(credit["runs_out_at"] - now, CREDIT_HORIZON_SECONDS)
    daily = resources.get("daily_pool")
    if daily:
        bonus += ALLOWANCE_BASE_BONUS
        resets_at = daily.get("resets_at")
        if type(resets_at) in (int, float):
            bonus += DAILY_POOL_URGENCY_BONUS * _approach(resets_at - now, ALLOWANCE_HORIZON_SECONDS)
    promo = resources.get("promotional_free")
    if promo:
        bonus += PROMO_BASE_BONUS
        free_until = promo.get("free_until")
        if type(free_until) in (int, float):
            bonus += PROMO_URGENCY_BONUS * _approach(free_until - now, ALLOWANCE_HORIZON_SECONDS)
    return round(min(0.95, bonus), 6)
