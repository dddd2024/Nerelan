"""Pure account-weight transitions for the existing atomic feedback document.

Adapts the bounded rules from the local policy prototype, excluding its separate
mutable ledger and best-effort persistence. No dispatch, model call, budget,
authorization or publication authority is introduced here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from collections import Counter
from typing import Any, Mapping

from .config import MultiAccountConfig

WEIGHTS = ("reliability_weight", "cost_weight", "latency_weight")
FAILURES = frozenset({"account_abnormal", "quota_exhausted", "task_failed", "timeout"})


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _baseline(config: MultiAccountConfig) -> dict[str, float]:
    return {key: float(getattr(config, key)) for key in WEIGHTS}


def _parameters(config: MultiAccountConfig) -> dict[str, Any]:
    return {key: getattr(config, key) for key in (*WEIGHTS, "policy_step_ratio", "policy_max_weight_drift_ratio",
            "policy_min_new_attempts", "policy_target_success_rate", "policy_observation_max_age_seconds")}


def _context(config: MultiAccountConfig) -> str:
    return hashlib.sha256(json.dumps(_parameters(config), sort_keys=True, allow_nan=False).encode()).hexdigest()


def _bounds(config: MultiAccountConfig, key: str) -> tuple[float, float]:
    base, drift = float(getattr(config, key)), config.policy_max_weight_drift_ratio
    high = sys.float_info.max if base > sys.float_info.max / (1 + drift) else base * (1 + drift)
    return base * (1 - drift), high


def _validate_weights(weights: Any, config: MultiAccountConfig) -> dict[str, float]:
    if not isinstance(weights, Mapping) or set(weights) != set(WEIGHTS):
        raise ValueError("invalid_policy_weights")
    for key, value in weights.items():
        low, high = _bounds(config, key)
        if not _number(value) or not low <= value <= high:
            raise ValueError("policy_target_outside_current_bounds")
    return {key: float(weights[key]) for key in WEIGHTS}


def _load(state: Any, config: MultiAccountConfig) -> dict[str, Any]:
    if state == {}:
        return {"schema_version": 1, "revision": 0, "context": _context(config),
                "effective": _baseline(config), "history": [], "observations": [],
                "references": {"cost": None, "latency": None}, "last_assessment": None}
    if (not isinstance(state, Mapping) or state.get("schema_version") != 1
            or type(state.get("revision")) is not int or state["revision"] < 0
            or not isinstance(state.get("history"), list)
            or not isinstance(state.get("observations"), list)
            or not isinstance(state.get("references"), Mapping)
            or not isinstance(state.get("context"), str)
            or not isinstance(state.get("effective"), Mapping)):
        raise ValueError("invalid_policy_state")
    result = copy.deepcopy(dict(state))
    if set(result["effective"]) != set(WEIGHTS) or any(not _number(value) for value in result["effective"].values()):
        raise ValueError("invalid_policy_weights")
    revisions = [row.get("revision") for row in result["history"] if isinstance(row, Mapping)]
    if (len(revisions) != len(result["history"]) or any(type(v) is not int or not 0 < v <= result["revision"] for v in revisions)
            or revisions != sorted(set(revisions))):
        raise ValueError("invalid_policy_history")
    for row in result["history"]:
        for name in ("before", "after"):
            values = row.get(name)
            if not isinstance(values, Mapping) or set(values) != set(WEIGHTS) or any(not _number(v) for v in values.values()):
                raise ValueError("invalid_policy_history")
    if any(value is not None and not _number(value) for value in result["references"].values()):
        raise ValueError("invalid_policy_reference")
    for row in result["observations"]:
        if (not isinstance(row, Mapping) or type(row.get("ok")) is not bool
                or not isinstance(row.get("id"), str)
                or not _number(row.get("at"))
                or any(row.get(key) is not None and not _number(row[key]) for key in ("cost", "latency"))):
            raise ValueError("invalid_policy_observation")
    if result["context"] == _context(config):
        _validate_weights(result["effective"], config)
    return result


def _commit(state: dict[str, Any], config: MultiAccountConfig, *, after: dict[str, float],
            kind: str, reason: str, evidence: Mapping[str, Any], now: float) -> None:
    after = _validate_weights(after, config)
    state["revision"] += 1
    state["history"].append({"revision": state["revision"], "kind": kind, "reason": reason,
        "at": now, "context": _context(config), "before": copy.deepcopy(state["effective"]),
        "after": after, "parameters": _parameters(config), "evidence": copy.deepcopy(dict(evidence))})
    state["history"] = state["history"][-config.policy_audit_limit:]
    state["effective"] = after


def _activate_context(state: dict[str, Any], config: MultiAccountConfig, *, now: float) -> None:
    if state["context"] != _context(config):
        _commit(state, config, after=_baseline(config), kind="configuration", reason="owner_configuration_changed",
                evidence={"previous_context": state["context"]}, now=now)
        state.update(context=_context(config), observations=[], references={"cost": None, "latency": None})


def effective_weights(state: Any, config: MultiAccountConfig) -> dict[str, float]:
    """Read-only: disabled evolution or changed Owner bounds uses the baseline."""
    if not config.enable_policy_evolution:
        return _baseline(config)
    loaded = _load(state, config)
    if loaded["context"] != _context(config):
        return _baseline(config)
    return _validate_weights(loaded["effective"], config)


def _per_result(values: list[Any], denominator: int) -> float | None:
    if not denominator or any(not _number(value) for value in values):
        return None
    try:
        result = math.fsum(value / denominator for value in values)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


def advance_policy(state: Any, config: MultiAccountConfig, *, outcome: Mapping[str, Any],
                   outcome_id: str | None, now: float) -> dict[str, Any]:
    """Dry-run a transition; the caller alone commits the returned document.

    Only distinct terminal receipts admitted by the surrounding transaction may
    enter this window. Anonymous/manual observations do not trigger evolution.
    """
    if not config.enable_policy_evolution or not config.enable_account_scoring or outcome_id is None:
        return copy.deepcopy(state)
    if type(outcome.get("ok")) is not bool or not _number(now):
        raise ValueError("invalid_policy_observation")
    result = _load(state, config)
    _activate_context(result, config, now=now)
    kind = outcome.get("failure_kind")
    result["observations"] = [row for row in result["observations"]
                              if now - config.policy_observation_max_age_seconds <= row["at"] <= now]
    result["observations"].append({"id": outcome_id, "at": now, "ok": outcome["ok"],
        "failure_kind": kind if kind in FAILURES else "task_failed",
        "cost": outcome.get("cost_units") if _number(outcome.get("cost_units")) else None,
        "latency": outcome.get("wall_seconds") if _number(outcome.get("wall_seconds")) else None})
    result["observations"] = result["observations"][-config.max_recorded_runs:]
    rows = result["observations"]
    if len(rows) < config.policy_min_new_attempts:
        return result
    successes = sum(row["ok"] is True for row in rows)
    rate = successes / len(rows)
    failures = Counter(row["failure_kind"] for row in rows if not row["ok"])
    quality_rows = [row for row in rows if row["ok"] or row["failure_kind"] != "quota_exhausted"]
    quality_rate = successes / len(quality_rows) if quality_rows else None
    cost = _per_result([row["cost"] for row in rows], successes)
    latency = _per_result([row["latency"] for row in rows], len(rows))
    references = result["references"]
    def pressure(value, reference):
        return value is not None and reference is not None and value > reference * 1.2
    key, reason = None, "capacity_only" if not quality_rows else "healthy_no_pressure"
    quality_failures = {kind: count for kind, count in failures.items() if kind != "quota_exhausted"}
    dominant = max(quality_failures, key=quality_failures.get) if quality_failures else None
    if dominant == "account_abnormal" and failures[dominant] >= 3:
        key, reason = "reliability_weight", "measured_failure_pressure"
    elif dominant == "timeout" and failures[dominant] >= 3:
        key, reason = "latency_weight", "measured_timeout_pressure"
    elif quality_rate is not None and quality_rate < config.policy_target_success_rate:
        key, reason = "reliability_weight", "measured_failure_pressure"
    elif pressure(cost, references.get("cost")):
        key, reason = "cost_weight", "measured_cost_per_success_pressure"
    elif pressure(latency, references.get("latency")):
        key, reason = "latency_weight", "measured_attempt_latency_pressure"
    summary = {"attempts": len(rows), "successes": successes, "success_rate": rate,
               "quality_success_rate_excluding_capacity": quality_rate,
               "failure_kinds": dict(failures), "cost_per_executor_success": cost,
               "mean_attempt_seconds": latency, "references": copy.deepcopy(dict(references)),
               "source_ids": [row["id"] for row in rows], "source_at_range": [rows[0]["at"], rows[-1]["at"]]}
    after = dict(result["effective"])
    if key is not None:
        low, high = _bounds(config, key)
        after[key] = min(high, max(low, after[key] + getattr(config, key) * config.policy_step_ratio))
        if after != result["effective"]:
            _commit(result, config, after=after, kind="evolution", reason=reason, evidence=summary, now=now)
        else:
            reason = "current_clamp_limit"
    for name, measured in (("cost", cost), ("latency", latency)):
        if references.get(name) is None and measured is not None:
            references[name] = measured
    result.update(observations=[], last_assessment={"reason": reason, "at": now, **summary})
    return result


def rollback_policy(state: Any, config: MultiAccountConfig, *, target: int,
                    expected_revision: int, now: float) -> dict[str, Any]:
    """Return a new audited revision, or reject without mutating the input."""
    result = _load(state, config)
    if type(expected_revision) is not int or result["revision"] != expected_revision:
        raise ValueError("policy_revision_changed")
    if type(target) is not int or target < 0 or not _number(now):
        raise ValueError("invalid_policy_rollback")
    found = next((row for row in result["history"] if row["revision"] == target), None)
    if target != 0 and found is None:
        raise ValueError("policy_revision_not_retained")
    after = _baseline(config) if target == 0 else _validate_weights(found["after"], config)
    _activate_context(result, config, now=now)
    _commit(result, config, after=after, kind="rollback", reason="operator_rollback",
            evidence={"target_revision": target}, now=now)
    result["observations"] = []
    return result
