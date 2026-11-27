"""Automated Magpie routing group planner & read-only sync foundation (#1664).

Builds ``group/<id>`` member recommendations from Magpie's live model catalog,
cached quota health, and observed prompt-cache / success / credit telemetry
without synthetic probe spam and while strictly excluding #1743 paid-subscription
gateway providers.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping, Sequence

from .model_router import _base_identity
from .routing_inputs import DEFAULT_PAID_SUBSCRIPTIONS, GATEWAY_COST_CLASSES, read_overrides, routing_group_id

_SAFE_SLUG = re.compile(r"[^a-z0-9._-]+")
_IGNORED_NAMESPACES = frozenset({"group", "auto"})
_META_MODEL_LEAVES = frozenset({"auto", "default", "max-model"})
_DEFAULT_COMPLIANCE_EXCLUDED = frozenset({"copilot"})


def _is_unmetered_free_provider(provider: str) -> bool:
    p = str(provider or "").strip().lower()
    return GATEWAY_COST_CLASSES.get(p) == "free" or p.endswith("-free")


def _compliance_provider_names(extra: Iterable[str] | None) -> set[str]:
    names = set(_DEFAULT_COMPLIANCE_EXCLUDED)
    for item in extra or ():
        if isinstance(item, str) and item.strip():
            names.add(item.strip().lower())
    return names


def _paid_provider_names(paid_subscriptions: Mapping[str, Any] | None) -> set[str]:
    names: set[str] = {
        str(name).strip().lower()
        for name in (DEFAULT_PAID_SUBSCRIPTIONS.get("providers") or {})
        if isinstance(name, str) and name.strip()
    }
    if isinstance(paid_subscriptions, Mapping):
        extra = paid_subscriptions.get("providers")
        if isinstance(extra, Mapping):
            names.update(
                str(name).strip().lower()
                for name in extra
                if isinstance(name, str) and name.strip()
            )
    return names


def _is_healthy_provider_accounts(
    accounts: Sequence[Mapping[str, Any]],
    *,
    provider: str = "",
) -> tuple[bool, str, float | None]:
    """Fail-closed provider health from /v1/magpie/quotas entries (missing != healthy)."""
    if not accounts:
        if _is_unmetered_free_provider(provider):
            return True, "unmetered_free", None
        return False, "unknown_quota:no_quota_row", None
    any_usable = False
    best_headroom: float | None = None
    reasons: list[str] = []
    for account in accounts:
        err = account.get("error") or account.get("reason")
        state = str(account.get("state") or account.get("status") or "").upper()
        if err:
            reasons.append(f"error:{err}")
            continue
        if state != "FRESH":
            reasons.append(f"unknown_quota:{state.lower() or 'missing_state'}")
            continue
        windows = account.get("windows") or ()
        if not windows and not _is_unmetered_free_provider(provider):
            reasons.append("unknown_quota:empty_windows")
            continue
        exhausted_window = False
        numeric_windows = 0
        min_remaining: float | None = None
        for w in windows:
            if not isinstance(w, Mapping) or w.get("reset_passed"):
                continue
            if w.get("unlimited") is True:
                numeric_windows += 1
                min_remaining = 100.0 if min_remaining is None else min(min_remaining, 100.0)
                continue
            rem = w.get("remaining_percent")
            if isinstance(rem, (int, float)) and not isinstance(rem, bool):
                remaining = float(rem)
            else:
                used = w.get("used_percent")
                if not isinstance(used, (int, float)) or isinstance(used, bool):
                    continue
                remaining = 100.0 - float(used)
            numeric_windows += 1
            min_remaining = remaining if min_remaining is None else min(min_remaining, remaining)
            if remaining <= 0.0:
                exhausted_window = True
                break
        if exhausted_window:
            reasons.append("quota_exhausted")
            continue
        if numeric_windows == 0 and not _is_unmetered_free_provider(provider):
            reasons.append("unknown_quota:no_numeric_window")
            continue
        any_usable = True
        if min_remaining is not None:
            best_headroom = min_remaining if best_headroom is None else max(best_headroom, min_remaining)
    if any_usable:
        return True, "healthy", best_headroom
    return False, reasons[0] if reasons else "unhealthy", None


def _telemetry_by_member(usage_rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Aggregate observed prompt-cache, success, and credit rate; missing stays None."""
    acc: dict[str, dict[str, float]] = {}
    for row in usage_rows:
        if not isinstance(row, Mapping):
            continue
        served = str(row.get("served_model") or row.get("served") or row.get("model") or "").strip().lower()
        prov = str(row.get("provider") or "").strip().lower()
        key = served if "/" in served else (f"{prov}/{served}" if prov and served else served)
        if not key:
            continue
        stats = acc.setdefault(key, {
            "requests": 0.0,
            "ok": 0.0,
            "input": 0.0,
            "cache_read": 0.0,
            "cache_write": 0.0,
            "credits": 0.0,
            "credit_tokens": 0.0,
            "credit_samples": 0.0,
        })
        stats["requests"] += 1.0
        status = row.get("status")
        failed = bool(row.get("rejected")) or (isinstance(status, (int, float)) and status >= 400)
        if not failed:
            stats["ok"] += 1.0
        tokens = row.get("tokens") if isinstance(row.get("tokens"), Mapping) else row
        row_tok = 0.0
        for src_k, dst_k in (("input", "input"), ("cache_read", "cache_read"), ("cache_write", "cache_write")):
            val = tokens.get(src_k, row.get("in" if src_k == "input" else src_k))
            if isinstance(val, (int, float)) and not isinstance(val, bool) and val >= 0:
                stats[dst_k] += float(val)
                row_tok += float(val)
        cred = row.get("reported_credits")
        if isinstance(cred, (int, float)) and not isinstance(cred, bool) and math.isfinite(cred) and cred >= 0:
            stats["credit_samples"] += 1.0
            stats["credits"] += float(cred)
            stats["credit_tokens"] += row_tok

    metrics: dict[str, dict[str, Any]] = {}
    for key, stats in acc.items():
        req = stats["requests"]
        denom = stats["input"] + stats["cache_read"] + stats["cache_write"]
        c_tok = stats["credit_tokens"]
        credits_per_1m = (
            round(stats["credits"] * 1_000_000.0 / c_tok, 4)
            if stats["credit_samples"] > 0 and c_tok > 0
            else None
        )
        metrics[key] = {
            "requests": req,
            "cache_hit_rate": round(stats["cache_read"] / denom, 6) if denom > 0 else None,
            "success_rate": round(stats["ok"] / req, 6) if req > 0 else None,
            "credits_per_1m": credits_per_1m,
            "credit_samples": int(stats["credit_samples"]),
        }
    return metrics


def plan_group_sync(
    models_payload: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    quotas_snapshot: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    usage_rows: Iterable[Mapping[str, Any]] = (),
    *,
    paid_subscriptions: Mapping[str, Any] | None = None,
    compliance_excluded: Iterable[str] | None = None,
    existing_groups: Mapping[str, Any] | None = None,
    min_providers: int = 2,
) -> dict[str, Any]:
    """Compute desired ``group/<id>`` declarations & diff without touching external services."""
    raw_models = (
        list(models_payload.get("data") or ())
        if isinstance(models_payload, Mapping)
        else list(models_payload)
    )
    raw_quotas = (
        list((quotas_snapshot or {}).get("data") or (quotas_snapshot or {}).get("accounts") or ())
        if isinstance(quotas_snapshot, Mapping)
        else list(quotas_snapshot or ())
    )
    paid_providers = _paid_provider_names(paid_subscriptions)
    compliance_providers = _compliance_provider_names(compliance_excluded)
    by_provider_quotas: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in raw_quotas:
        if isinstance(item, Mapping) and isinstance(item.get("provider"), str) and item["provider"].strip():
            by_provider_quotas[item["provider"].strip().lower()].append(item)

    provider_health: dict[str, tuple[bool, str, float | None]] = {}
    telemetry = _telemetry_by_member(usage_rows)

    grouped_candidates: dict[str, list[str]] = defaultdict(list)
    excluded_paid: list[str] = []
    excluded_compliance: list[str] = []
    excluded_meta: list[str] = []
    excluded_unhealthy: list[dict[str, str]] = []

    seen_ids: set[str] = set()
    for item in raw_models:
        model_id = str((item.get("id") if isinstance(item, Mapping) else None)
                       or (item.get("model_id") if isinstance(item, Mapping) else "")).strip()
        if not model_id or "/" not in model_id or routing_group_id(model_id):
            continue
        lower = model_id.lower()
        if lower in seen_ids:
            continue
        seen_ids.add(lower)
        provider, _, leaf = lower.partition("/")
        if provider in _IGNORED_NAMESPACES:
            excluded_meta.append(model_id)
            continue
        identity = _base_identity(model_id)
        if leaf in _META_MODEL_LEAVES or identity in _META_MODEL_LEAVES:
            excluded_meta.append(model_id)
            continue
        if provider in paid_providers:
            excluded_paid.append(model_id)
            continue
        if provider in compliance_providers:
            excluded_compliance.append(model_id)
            continue
        if provider not in provider_health:
            provider_health[provider] = _is_healthy_provider_accounts(
                by_provider_quotas.get(provider, ()),
                provider=provider,
            )
        healthy, health_reason, _ = provider_health[provider]
        if not healthy:
            excluded_unhealthy.append({"member": model_id, "reason": health_reason})
            continue
        if identity:
            grouped_candidates[identity].append(model_id)

    desired: dict[str, dict[str, Any]] = {}
    for identity, members in sorted(grouped_candidates.items()):
        distinct_providers = {m.split("/", 1)[0].lower() for m in members}
        slug = _SAFE_SLUG.sub("-", f"nerelan-{identity}").strip("-")
        group_id = f"group/{slug}"
        if len(distinct_providers) < min_providers and group_id not in (existing_groups or {}):
            continue

        def sort_key(member_id: str) -> tuple[float, str]:
            t = telemetry.get(member_id.lower(), {})
            prov = member_id.split("/", 1)[0].lower()
            _, _, headroom = provider_health.get(prov, (False, "", None))
            sr = t.get("success_rate")
            rel_penalty = (1.0 - float(sr)) * 2.5 if isinstance(sr, (int, float)) else 0.35
            cp1m = t.get("credits_per_1m")
            if _is_unmetered_free_provider(prov):
                cost_penalty = 0.0
            elif isinstance(cp1m, (int, float)):
                cost_penalty = min(1.5, math.log1p(float(cp1m) / 100.0) * 0.22)
            else:
                cost_penalty = 0.45  # unknown credit cost != 0 cost
            cache_rate = t.get("cache_hit_rate")
            cache_bonus = float(cache_rate) * 0.50 if isinstance(cache_rate, (int, float)) else 0.0
            headroom_bonus = (float(headroom) / 100.0) * 0.25 if isinstance(headroom, (int, float)) else 0.0
            score = rel_penalty + cost_penalty - cache_bonus - headroom_bonus
            return (round(score, 6), member_id.lower())

        ordered = sorted(members, key=sort_key)
        desired[group_id] = {"identity": identity, "members": ordered}

    existing = {str(k).strip().lower(): v for k, v in (existing_groups or {}).items()}
    added = sorted(g for g in desired if g not in existing)
    updated = sorted(
        g for g in desired
        if g in existing and (existing[g].get("members") != desired[g]["members"] or existing[g].get("identity") != desired[g]["identity"])
    )
    unchanged = sorted(g for g in desired if g not in added and g not in updated)
    return {
        "groups": desired,
        "diff": {
            "added": added,
            "updated": updated,
            "unchanged": unchanged,
            "excluded_paid_subscription": sorted(excluded_paid),
            "excluded_compliance": sorted(excluded_compliance),
            "excluded_meta_models": sorted(excluded_meta),
            "removed_unhealthy": excluded_unhealthy,
        },
    }


def run_group_sync(
    *,
    magpie_url: str | None = None,
    cache_path: Path | None = None,
    state_path: Path | None = None,
    timeout: float = 3.0,
) -> dict[str, Any]:
    """Read local Magpie /v1/models, /v1/magpie/quotas?kept=1, and usage cache in read-only mode."""
    from urllib.request import Request
    from ..model_access import http_safe
    from ..model_access.magpie import MAGPIE_AUTH, _decode, parse_quotas, validate_loopback_origin
    from .magpie_usage_ingest import read_cache
    from datetime import datetime, timezone

    url = (magpie_url or os.environ.get("REVERSE_AGENT_MAGPIE_URL") or "http://127.0.0.1:3425").rstrip("/")
    if not validate_loopback_origin(url):
        raise ValueError("invalid_magpie_url")

    def _get(path: str) -> Any:
        req = Request(url + path, headers={"Authorization": MAGPIE_AUTH}, method="GET")
        with http_safe.urlopen(req, timeout=timeout) as resp:
            return _decode(resp.read())

    models_payload = _get("/v1/models") or {}
    quotas_raw = _get("/v1/magpie/quotas?kept=1") or {}
    parsed_accounts = parse_quotas(quotas_raw, datetime.now(timezone.utc)) if quotas_raw else []
    usage_rows = read_cache(cache_path)
    owner = read_overrides(state_path) if state_path else {}
    return plan_group_sync(
        models_payload,
        {"accounts": parsed_accounts},
        usage_rows,
        paid_subscriptions=owner.get("paid_subscriptions"),
        compliance_excluded=owner.get("compliance_excluded_providers"),
        existing_groups=owner.get("groups"),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Magpie group/<id> routing planner (dry-run only).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Read-only dry-run mode (only mode currently implemented; no writes performed)",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output")
    parser.add_argument("--magpie-url", default=None, help="Loopback Magpie URL")
    parser.add_argument("--cache-path", default=None, help="Optional magpie_usage_cache.jsonl path")
    parser.add_argument("--state-path", default=None, help="Optional model_setup_state.json path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    plan = run_group_sync(
        magpie_url=args.magpie_url,
        cache_path=Path(args.cache_path) if args.cache_path else None,
        state_path=Path(args.state_path) if args.state_path else None,
    )
    if args.as_json:
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        diff = plan["diff"]
        print(
            f"groups={len(plan['groups'])} added={len(diff['added'])} updated={len(diff['updated'])} "
            f"unchanged={len(diff['unchanged'])} unhealthy={len(diff['removed_unhealthy'])} "
            f"paid_excluded={len(diff['excluded_paid_subscription'])}"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
