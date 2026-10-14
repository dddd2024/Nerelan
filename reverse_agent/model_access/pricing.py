"""Equivalent cost at the model vendor's official API list price (P0-3).

"Equivalent cost" answers: what would these tokens have cost on the model maker's own
pay-as-you-go API? It is an estimate for comparing routes. It is not an invoice: a
subscription, a free gateway or a discounted relay may have cost something else
entirely, which is why every figure carries ``provenance: ESTIMATED_LIST_PRICE`` and the
price snapshot's source and date.

Prices come from a vendored snapshot of models.dev (MIT, https://models.dev), pruned to
the model makers' own provider entries. Refreshing it is an explicit, offline step:

    python -m reverse_agent.model_access.pricing refresh <downloaded models.dev api.json>

Nothing here performs network I/O.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

SNAPSHOT_PATH = Path(__file__).with_name("pricing_snapshot.json")
PRICE_FIELDS = ("input", "cache_read", "cache_write", "output")

# The model maker whose own API price defines "equivalent cost" for a model id prefix.
_VENDOR_PREFIXES = (
    ("claude-", "anthropic"), ("gpt-", "openai"), ("o1", "openai"), ("o3", "openai"), ("o4", "openai"),
    ("codex-", "openai"), ("gemini-", "google"), ("glm-", "zhipuai"), ("kimi-", "moonshotai"),
    ("deepseek-", "deepseek"), ("mistral-", "mistral"), ("codestral-", "mistral"), ("devstral-", "mistral"),
    ("magistral-", "mistral"), ("grok-", "xai"), ("qwen", "alibaba"), ("minimax-", "minimax"),
    ("sensenova-", "sensenova"),
)
SNAPSHOT_VENDORS = tuple(sorted({vendor for _, vendor in _VENDOR_PREFIXES}))
# Claude Code's model aliases name no concrete model; the CLI's result says which one ran.
_ALIASES = frozenset({"sonnet", "opus", "haiku", "fable", "default", "best", "opusplan"})

_snapshot_cache: dict[str, Any] | None = None


def load_snapshot() -> dict[str, Any]:
    global _snapshot_cache
    if _snapshot_cache is None:
        _snapshot_cache = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return _snapshot_cache


def build_snapshot(raw: Mapping[str, Any], *, fetched_at: str) -> dict[str, Any]:
    """Prune a models.dev ``api.json`` to the model makers' own per-1M-token USD prices."""
    models: dict[str, dict[str, dict[str, Any]]] = {}
    for vendor in SNAPSHOT_VENDORS:
        for model_id, model in sorted(((raw.get(vendor) or {}).get("models") or {}).items()):
            cost = model.get("cost") if isinstance(model, Mapping) else None
            if not isinstance(cost, Mapping) or not all(isinstance(cost.get(k), (int, float)) for k in ("input", "output")):
                continue
            entry = {k: cost[k] for k in PRICE_FIELDS if isinstance(cost.get(k), (int, float))}
            if cost.get("tiers") or cost.get("context_over_200k"):
                entry["tiered"] = True
            models.setdefault(vendor, {})[model_id] = entry
    return {"source": "https://models.dev/api.json", "license": "MIT (models.dev)", "fetched_at": fetched_at,
            "unit": "USD per 1M tokens", "models": models}


def canonical_model(model_id: str) -> str:
    name = model_id.strip().rsplit("/", 1)[-1].casefold()
    return re.sub(r"\[[^\]]*\]$", "", name)  # e.g. "claude-fable-5-1[1m]"


def vendor_for(model_id: str) -> str | None:
    name = canonical_model(model_id)
    return next((vendor for prefix, vendor in _VENDOR_PREFIXES if name.startswith(prefix)), None)


def lookup_price(model_id: str, snapshot: Mapping[str, Any] | None = None) -> tuple[str | None, dict[str, Any] | None]:
    """(vendor, price entry) for a model id, or (vendor-or-None, None) when unpriced."""
    snapshot = snapshot or load_snapshot()
    name = canonical_model(model_id)
    vendor = vendor_for(name)
    table = (snapshot.get("models") or {}).get(vendor or "", {})
    for candidate in (name, re.sub(r"-\d{8}$", "", name)):
        if candidate in table:
            return vendor, table[candidate]
    return vendor, None


def equivalent_cost(model_id: str, tokens: Mapping[str, Any],
                    snapshot: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """List-price cost of normalized token counters (see usage_ledger.COUNTERS)."""
    snapshot = snapshot or load_snapshot()
    base = {"provenance": "ESTIMATED_LIST_PRICE", "price_source": snapshot.get("source"),
            "price_as_of": snapshot.get("fetched_at"), "currency": "USD"}
    if not model_id or canonical_model(model_id) in _ALIASES:
        return base | {"state": "UNKNOWN", "reason": "model_unresolved", "usd": None}
    vendor, price = lookup_price(model_id, snapshot)
    if price is None:
        return base | {"state": "UNKNOWN", "reason": "no_list_price" if vendor else "vendor_unknown",
                       "vendor": vendor, "usd": None}
    notes = []
    total = Decimal(0)
    for field in PRICE_FIELDS:
        count = tokens.get(field)
        if not count:
            continue
        rate = price.get(field)
        if rate is None:
            # Unlisted cache price: bill at the input price, an upper bound for cache reads.
            rate = price["input"]
            notes.append(f"{field}_priced_as_input")
        total += Decimal(str(count)) * Decimal(str(rate)) / Decimal(1_000_000)
    if price.get("tiered"):
        notes.append("long_context_tier_not_applied")
    return base | {"state": "ESTIMATED", "vendor": vendor, "model": canonical_model(model_id),
                   "usd": float(round(total, 6)), "notes": notes}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] != "refresh":
        print("usage: python -m reverse_agent.model_access.pricing refresh <models.dev api.json>", file=sys.stderr)
        return 2
    from datetime import datetime, timezone
    raw = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    snapshot = build_snapshot(raw, fetched_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    SNAPSHOT_PATH.write_bytes((json.dumps(snapshot, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print(f"wrote {sum(len(v) for v in snapshot['models'].values())} prices to {SNAPSHOT_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
