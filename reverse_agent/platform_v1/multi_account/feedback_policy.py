"""Bounded, replayable feedback inputs for the existing production router.

No dispatch, persistence, authority or learning algorithm lives here. Policy and
sample snapshots travel with the existing MODEL_SELECTED evidence. The EWMA and
weighted bonus are reused from AccountScoreboard; disabling this policy restores
the original routing score without deleting feedback.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from .config import MultiAccountConfig
from .scoring import AccountScoreboard, PRUNE_HORIZON_SECONDS

POLICY_FIELDS = ("enable_feedback_routing", "enable_account_scoring", "score_ewma_alpha",
                 "feedback_routing_min_attempts", "feedback_routing_max_adjustment",
                 "reliability_weight", "cost_weight", "latency_weight")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def routing_snapshot(config: MultiAccountConfig, accounts: Mapping[str, Any], *,
                     owner: str, now: float) -> dict[str, Any] | None:
    if not config.enable_feedback_routing or not config.enable_account_scoring or owner != "local":
        return None
    policy = {key: getattr(config, key) for key in POLICY_FIELDS}
    scores = AccountScoreboard(config, state=accounts).scores()
    public = {ref: score.public_view() for ref, score in sorted(scores.items())}
    content = {"schema_version": 1, "policy": policy, "accounts": public, "observed_at": now}
    return {**content, "policy_id": _digest(policy), "snapshot_id": _digest(content)}


def apply_routing_feedback(ranked: list[dict[str, Any]], snapshot: Mapping[str, Any], *, now: float) -> None:
    """Adjust cost only after the router's hard filters; commit updates together.

    Availability, quota pressure, capability, paid-spend permission, independent
    review, pins and retry fitness remain owned by model_router. Complete peer
    coverage is required for price/latency comparisons; UNKNOWN is not cheaper.
    """
    if snapshot.get("schema_version") != 1:
        return
    content = {key: snapshot[key] for key in ("schema_version", "policy", "accounts", "observed_at")}
    if snapshot.get("snapshot_id") != _digest(content) or snapshot.get("policy_id") != _digest(content["policy"]):
        return
    policy = content["policy"]
    if not isinstance(policy, Mapping) or set(policy) != set(POLICY_FIELDS):
        return
    config = MultiAccountConfig(**policy)
    if not config.enable_feedback_routing or not config.enable_account_scoring:
        return
    accounts = content["accounts"]
    if not isinstance(accounts, Mapping) or not _number(now):
        return
    eligible = {}
    for ref, raw in accounts.items():
        if not isinstance(raw, Mapping):
            continue
        attempts, updated = raw.get("attempts"), raw.get("updated_at")
        reliability = raw.get("reliability")
        if (type(attempts) is not int or attempts < config.feedback_routing_min_attempts
                or not _number(updated) or not now - PRUNE_HORIZON_SECONDS <= updated <= now
                or not _number(reliability) or reliability > 1):
            continue
        eligible[ref] = dict(raw)
    groups: dict[tuple, list[dict[str, Any]]] = {}
    for item in ranked:
        key = (item["availability_rank"], item["quota_penalty"], item["tier"], item["cost_class"])
        groups.setdefault(key, []).append(item)
    updates = []
    for items in groups.values():
        refs = {item.get("account_ref") for item in items}
        peers = {ref: eligible[ref] for ref in refs if ref in eligible}
        scores = AccountScoreboard(config, state=peers)
        # Legacy samples have no coverage counters. They may support measured
        # reliability, but do not become evidence of complete cost/latency.
        def complete(field: str, count: str) -> bool:
            return len(refs) >= 2 and len(peers) == len(refs) and all(
                _number(row.get(field)) and type(row.get(count)) is int
                and row[count] == row["attempts"] for row in peers.values())
        cost_known = complete("mean_cost_units", "cost_samples")
        latency_known = complete("mean_wall_seconds", "latency_samples")
        cost_reference, latency_reference = scores.references()
        for item in items:
            ref = item.get("account_ref")
            if ref not in peers:
                continue
            points = scores.bonus(ref, cost_reference=cost_reference if cost_known else None,
                                  latency_reference=latency_reference if latency_known else None)
            cap = config.feedback_routing_max_adjustment
            adjustment = max(-cap, min(cap, points / 100.0))
            evidence = {"policy_id": snapshot["policy_id"], "snapshot_id": snapshot["snapshot_id"],
                        "policy": dict(policy), "account_ref": ref, "sample": peers[ref],
                        "adjustment": adjustment, "cost_comparison": "list_price" if cost_known else "UNKNOWN",
                        "latency_comparison": "attempt_elapsed" if latency_known else "UNKNOWN",
                        "cost_reference": cost_reference if cost_known else None,
                        "latency_reference": latency_reference if latency_known else None,
                        "base_adjusted_cost": item["score"][1]}
            updates.append((item, adjustment, evidence))
    for item, adjustment, evidence in updates:
        item["score"][1] -= adjustment
        item["score_breakdown"]["account_feedback"] = evidence
