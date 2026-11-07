"""Bounded, auditable, reversible policy self-evolution.

Domain E. :mod:`.scoring` learns *facts* about accounts (reliability, cost,
latency). This module turns those facts — plus the failure-type distribution —
into small, bounded changes to the scheduling weights, and keeps every change on
a version chain so it can be inspected and undone.

The four requirements from the spec map to four mechanisms here:

===============  ===========================================================
可配置            weights, clamps, step size and the on/off switch are
                 :class:`~.config.MultiAccountConfig` fields
可审计            every change appends an entry (before/after/reason/evidence)
                 to a bounded, persisted audit trail
可回滚            :meth:`PolicyLedger.rollback` restores any earlier version,
                 including ``0`` = the configured baseline
有限幅            a weight may only move within
                 ``policy_max_weight_drift_ratio`` of its baseline, at most
                 ``policy_step_ratio`` per cycle, and the learned ranking bonus
                 is hard-capped by ``policy_max_bonus_points``
===============  ===========================================================

Deliberately *not* a learning framework: no gradient step, no free-form
parameter search, no model call. Each cycle evaluates a fixed, reviewable rule
list and may move one weight by one step. That is enough to adapt to a drifting
account pool and small enough to explain in a review.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Mapping, Optional

from .config import MultiAccountConfig

# Weights the loop is allowed to touch. Structural knobs (reroute limits,
# cooldowns, timeouts) are deliberately absent: changing them mid-run changes
# failure *semantics*, which must stay an explicit operator decision.
TUNABLE_WEIGHTS = ("reliability_weight", "cost_weight", "latency_weight")

# Failure kinds that indicate the account itself is unreliable.
RELIABILITY_KINDS = frozenset({
    "account_abnormal", "unauthorized", "error", "auth", "login", "session", "invalid_credentials",
})
# Failure kinds that indicate latency/timeout pressure.
LATENCY_KINDS = frozenset({"timeout", "latency", "slow", "stalled", "deadline"})
# Failure kinds that indicate the pool is capacity-bound rather than quality-bound.
CAPACITY_KINDS = frozenset({"quota_exhausted", "limit_hit", "rate_limit", "quota", "exhausted"})

# A dominant failure kind must exceed this share before it may steer a change.
DOMINANT_SHARE = 0.4
# Cost/latency trend above this multiple of the reference is treated as pressure.
PRESSURE_RATIO = 1.2


def _clamp(value: float, baseline: float, drift: float) -> float:
    low, high = baseline * (1.0 - drift), baseline * (1.0 + drift)
    return round(min(high, max(low, value)), 6)


class PolicyLedger:
    """Versioned scheduling policy with clamps, an audit trail and rollback."""

    def __init__(self, config: MultiAccountConfig, *,
                 clock: Callable[[], float] = time.time,
                 state: Optional[Mapping[str, Any]] = None,
                 persist: Optional[Callable[[dict[str, Any]], None]] = None) -> None:
        self._config = config
        self._clock = clock
        self._persist = persist
        self._baseline = self._baseline_from_config()
        self._version = 0
        self._effective = dict(self._baseline)
        self._audit: list[dict[str, Any]] = []
        self._reference: dict[str, Optional[float]] = {"cost": None, "latency": None}
        self.load(state)

    # --- baseline / read ------------------------------------------------------
    def _baseline_from_config(self) -> dict[str, float]:
        return {
            "reliability_weight": float(self._config.reliability_weight),
            "cost_weight": float(self._config.cost_weight),
            "latency_weight": float(self._config.latency_weight),
            "bonus_cap": float(self._config.policy_max_bonus_points),
        }

    def effective(self) -> dict[str, float]:
        return dict(self._effective)

    def weights(self) -> dict[str, float]:
        return {key: self._effective[key] for key in TUNABLE_WEIGHTS}

    def bonus_cap(self) -> float:
        """Hard cap the scheduler applies to a learned ranking bonus."""
        return float(self._effective.get("bonus_cap", self._config.policy_max_bonus_points))

    def version(self) -> int:
        return self._version

    def current(self) -> dict[str, Any]:
        return {"version": self._version, "effective": self.effective(),
                "baseline": dict(self._baseline),
                "drift_ratio": {key: round(self._drift(key), 4) for key in self._effective},
                "enabled": bool(self._config.policy_enabled)}

    def _drift(self, key: str) -> float:
        base = self._baseline.get(key) or 0.0
        if not base:
            return 0.0
        return (self._effective.get(key, base) - base) / base

    def audit(self) -> list[dict[str, Any]]:
        return [dict(entry) for entry in self._audit]

    # --- evaluation -----------------------------------------------------------
    def observe(self, profile: Mapping[str, Any], *, now: Optional[float] = None) -> dict[str, Any]:
        """Evaluate the rule list and apply at most one bounded change.

        ``profile`` comes from :meth:`~.scoring.AccountScoreboard.failure_profile`
        (``attempts``, ``success_rate``, ``failure_kinds``, ``cost_units``,
        ``wall_seconds``). Returns the decision actually applied, including a
        no-change decision with its reason so the loop is observable even when
        it does nothing.
        """
        now = self._clock() if now is None else now
        decision = self.propose(profile, now=now)
        if decision.get("changed"):
            # Return what actually happened, not what was proposed: if the write
            # was refused the caller must see ``changed: False`` and the reason,
            # otherwise a phantom version leaks into run evidence.
            return self._commit(decision, now=now)
        return decision

    def propose(self, profile: Mapping[str, Any], *, now: Optional[float] = None) -> dict[str, Any]:
        """Dry run: compute the change the rules would make, without applying it."""
        now = self._clock() if now is None else now
        if not self._config.policy_enabled:
            return self._no_change("policy_disabled", profile, now=now)
        attempts = profile.get("attempts")
        if not isinstance(attempts, int) or attempts < self._config.policy_min_samples:
            return self._no_change("insufficient_samples", profile, now=now)

        self._update_reference(profile)
        success_rate = self._success_rate(profile)
        kinds = self._failure_kinds(profile)
        dominant = self._dominant_kind(kinds)

        # 1. Unstable pool: stop trusting learned preferences at all and walk the
        #    weights back toward the configured baseline. Stability first.
        if success_rate is not None and success_rate < self._config.policy_target_success_rate:
            return self._stabilise(profile, success_rate=success_rate, now=now)

        # 2. Capacity-bound pool: reliability/cost preferences cannot buy capacity,
        #    so shrink the learned bonus instead of pretending to re-rank.
        if dominant and dominant in CAPACITY_KINDS:
            return self._adjust_cap(profile, direction=-1,
                                    reason="capacity_bound_reduce_bonus",
                                    evidence={"dominant_failure": dominant}, now=now)

        # 3. Quality-bound pool: prefer proven-reliable accounts / faster accounts.
        if dominant and dominant in RELIABILITY_KINDS:
            return self._adjust_weight(profile, "reliability_weight", +1,
                                       reason="failure_profile_reliability",
                                       evidence={"dominant_failure": dominant}, now=now)
        if dominant and dominant in LATENCY_KINDS:
            return self._adjust_weight(profile, "latency_weight", +1,
                                       reason="failure_profile_latency",
                                       evidence={"dominant_failure": dominant}, now=now)

        # 4. Cost pressure independent of the dominant failure kind.
        cost_ratio = self._ratio(profile.get("cost_units"), "cost")
        if cost_ratio is not None and cost_ratio > PRESSURE_RATIO:
            return self._adjust_weight(profile, "cost_weight", +1, reason="cost_pressure",
                                       evidence={"cost_ratio": round(cost_ratio, 4)}, now=now)
        latency_ratio = self._ratio(profile.get("wall_seconds"), "latency")
        if latency_ratio is not None and latency_ratio > PRESSURE_RATIO:
            return self._adjust_weight(profile, "latency_weight", +1, reason="latency_pressure",
                                       evidence={"latency_ratio": round(latency_ratio, 4)}, now=now)

        # 5. Stable and healthy: relax a previously shrunk bonus one step.
        if self.bonus_cap() < self._config.policy_max_bonus_points:
            return self._adjust_cap(profile, direction=+1, reason="stable_restore_bonus",
                                    evidence={"success_rate": self._round(success_rate)}, now=now)
        return self._no_change("stable_no_change", profile, now=now)

    # --- rule helpers ---------------------------------------------------------
    def _stabilise(self, profile: Mapping[str, Any], *, success_rate: Optional[float],
                   now: float) -> dict[str, Any]:
        before = self.effective()
        after = dict(before)
        step = self._config.policy_step_ratio
        moved: list[str] = []
        for key in TUNABLE_WEIGHTS:
            base = self._baseline[key]
            # Walk *toward* the baseline by at most one step and never past it.
            # Clamping alone is not enough: from a weight already at baseline a
            # naive subtraction would push it below the baseline floor and the
            # "stabilise" rule would itself become drift.
            delta = after[key] - base
            if abs(delta) < 1e-9:
                continue
            step_units = base * step
            stepped = base if abs(delta) <= step_units else after[key] - step_units * (1 if delta > 0 else -1)
            clamped = _clamp(stepped, base, self._config.policy_max_weight_drift_ratio)
            if clamped != after[key]:
                after[key] = clamped
                moved.append(key)
        cap_now = after["bonus_cap"]
        after["bonus_cap"] = max(0.0, round(cap_now - self._config.policy_max_bonus_points * step, 6))
        if not moved and after["bonus_cap"] == cap_now:
            return self._no_change("unstable_at_baseline", profile, now=now)
        return self._decision("unstable_revert", before, after, profile, now=now,
                              evidence={"success_rate": self._round(success_rate),
                                        "target": self._config.policy_target_success_rate})

    def _adjust_weight(self, profile: Mapping[str, Any], key: str, direction: int, *,
                       reason: str, evidence: Mapping[str, Any], now: float) -> dict[str, Any]:
        before = self.effective()
        base = self._baseline[key]
        stepped = before[key] + direction * base * self._config.policy_step_ratio
        clamped = _clamp(stepped, base, self._config.policy_max_weight_drift_ratio)
        if clamped == before[key]:
            return self._no_change(f"{reason}_at_clamp_limit", profile, now=now)
        after = dict(before)
        after[key] = clamped
        return self._decision(reason, before, after, profile, now=now, evidence=evidence)

    def _adjust_cap(self, profile: Mapping[str, Any], *, direction: int, reason: str,
                    evidence: Mapping[str, Any], now: float) -> dict[str, Any]:
        before = self.effective()
        maximum = float(self._config.policy_max_bonus_points)
        stepped = before["bonus_cap"] + direction * maximum * self._config.policy_step_ratio
        capped = round(min(maximum, max(0.0, stepped)), 6)
        if capped == before["bonus_cap"]:
            return self._no_change(f"{reason}_at_clamp_limit", profile, now=now)
        after = dict(before)
        after["bonus_cap"] = capped
        return self._decision(reason, before, after, profile, now=now, evidence=evidence)

    # --- commit / rollback ----------------------------------------------------
    def _commit(self, decision: Mapping[str, Any], *, now: float) -> dict[str, Any]:
        """Append one audited change — but only if it is durably persisted.

        A version that exists in memory and not on disk is worse than no change:
        the operator reads "policy v7" in the audit trail, the process restarts,
        and the pool quietly reverts to v6 with no record of why. So the new
        state is written first and adopted only after the write succeeds; a
        failed write reports ``persist_failed`` and leaves the ledger untouched.
        Dispatch is unaffected either way — this bounded optimisation simply
        declines to advance.
        """
        version = self._version + 1
        effective = dict(decision["after"])
        entry = {
            "version": version, "at": now, "kind": "change",
            "reason": decision.get("reason"),
            "before": dict(decision["before"]), "after": dict(effective),
            # What actually moved, so the trail answers "what changed" without
            # a reader having to diff two full snapshots by eye.
            "changed_keys": dict(decision.get("changed_keys") or {}),
            "evolved": version,
            "evidence": dict(decision.get("evidence") or {}),
        }
        audit = self._next_audit(entry)
        if not self._persist_state(version, effective, audit):
            return {**decision, "changed": False, "reason": "persist_failed",
                    "after": self.effective(), "changed_keys": {},
                    "version": self._version,
                    "evidence": {**dict(decision.get("evidence") or {}),
                                 "rejected": "persist_failed"}}
        self._version, self._effective, self._audit = version, effective, audit
        return {**decision, "version": self._version, "audit_entry": entry}

    def rollback(self, version: int = 0, *, now: Optional[float] = None,
                 reason: str = "operator_rollback") -> dict[str, Any]:
        """Restore the policy as it stood at ``version`` (``0`` = baseline).

        Rollback is itself an audited change: it appends an entry rather than
        erasing history, so "who removed what, and when" survives. It is also
        all-or-nothing: an operator who is told the rollback happened must be
        able to restart the process and still find the baseline in effect.
        """
        now = self._clock() if now is None else now
        before = self.effective()
        if version == 0:
            target = dict(self._baseline)
        else:
            match = next((e for e in reversed(self._audit)
                          if e.get("version") == version and e.get("kind") == "change"), None)
            if match is None:
                return {"changed": False, "reason": "unknown_version", "version": self._version,
                        "requested_version": version, "effective": before}
            target = dict(match["after"])
        if target == before:
            return {"changed": False, "reason": "already_at_version",
                    "version": self._version, "requested_version": version,
                    "effective": before}
        next_version = self._version + 1
        entry = {"version": next_version, "at": now, "kind": "rollback",
                 "reason": reason, "before": before, "after": dict(target),
                 "evolved": next_version, "rolled_back_to": version, "evidence": {}}
        audit = self._next_audit(entry)
        if not self._persist_state(next_version, target, audit):
            return {"changed": False, "reason": "persist_failed", "version": self._version,
                    "requested_version": version, "effective": before,
                    "audit_entry": None}
        self._version, self._effective, self._audit = next_version, target, audit
        return {"changed": True, "reason": reason, "version": self._version,
                "requested_version": version, "effective": self.effective(),
                "audit_entry": entry}

    def reset(self, *, clear_audit: bool = False, now: Optional[float] = None) -> dict[str, Any]:
        """Return to the configured baseline; optionally forget the audit trail."""
        result = self.rollback(0, now=now, reason="reset")
        if clear_audit and result.get("reason") != "persist_failed":
            audit: list[dict[str, Any]] = []
            if not self._persist_state(0, dict(self._baseline), audit):
                return result
            self._audit, self._version = audit, 0
            self._effective = dict(self._baseline)
            result = {"changed": True, "reason": "reset_and_cleared", "version": 0,
                      "effective": self.effective()}
        return result

    # --- profile helpers ------------------------------------------------------
    def _update_reference(self, profile: Mapping[str, Any]) -> None:
        """Freeze the cost/latency reference the first time evidence arrives.

        The ratios then mean "versus when this policy started steering", which is
        what an operator comparing a before/after report expects, and it cannot
        drift with the thing it is supposed to detect.
        """
        changed = False
        for key, field in (("cost", "cost_units"), ("latency", "wall_seconds")):
            value = profile.get(field)
            if self._reference.get(key) is None and isinstance(value, (int, float)) and value > 0:
                self._reference[key] = float(value)
                changed = True
        if changed:
            self._save()

    def _ratio(self, value: Any, key: str) -> Optional[float]:
        reference = self._reference.get(key)
        if reference is None or not isinstance(value, (int, float)):
            return None
        if reference <= 0:
            return None
        return float(value) / reference

    @staticmethod
    def _failure_kinds(profile: Mapping[str, Any]) -> dict[str, int]:
        raw = profile.get("failure_kinds")
        if not isinstance(raw, Mapping):
            return {}
        return {str(k): int(v) for k, v in raw.items()
                if isinstance(v, (int, float)) and v > 0}

    @staticmethod
    def _dominant_kind(kinds: Mapping[str, int]) -> Optional[str]:
        total = sum(kinds.values())
        if total <= 0:
            return None
        kind, count = max(kinds.items(), key=lambda item: item[1])
        return kind if count / total >= DOMINANT_SHARE else None

    @staticmethod
    def _success_rate(profile: Mapping[str, Any]) -> Optional[float]:
        rate = profile.get("success_rate")
        if isinstance(rate, (int, float)):
            return float(rate)
        attempts = profile.get("attempts")
        successes = profile.get("successes")
        if isinstance(attempts, int) and attempts > 0 and isinstance(successes, int):
            return successes / attempts
        return None

    @staticmethod
    def _round(value: Optional[float]) -> Optional[float]:
        return None if value is None else round(float(value), 4)

    # --- decision payloads ----------------------------------------------------
    def _decision(self, reason: str, before: Mapping[str, float],
                  after: Mapping[str, float], profile: Mapping[str, Any], *,
                  now: float, evidence: Mapping[str, Any]) -> dict[str, Any]:
        changed = {k: {"before": before[k], "after": after[k]}
                   for k in after if before.get(k) != after.get(k)}
        return {"changed": bool(changed), "reason": reason, "before": dict(before),
                "after": dict(after), "changed_keys": changed,
                "evidence": {**dict(evidence),
                             "samples": profile.get("attempts"),
                             "at": now},
                "version": self._version}

    def _no_change(self, reason: str, profile: Mapping[str, Any], *, now: float) -> dict[str, Any]:
        return {"changed": False, "reason": reason, "before": self.effective(),
                "after": self.effective(), "changed_keys": {},
                "evidence": {"samples": profile.get("attempts"), "at": now},
                "version": self._version}

    def _trim_audit(self) -> None:
        overflow = len(self._audit) - self._config.policy_audit_max_entries
        if overflow > 0:
            del self._audit[:overflow]

    def _next_audit(self, entry: Mapping[str, Any]) -> list[dict[str, Any]]:
        """The audit trail as it *would* look with ``entry`` appended, trimmed."""
        audit = [*self._audit, dict(entry)]
        overflow = len(audit) - self._config.policy_audit_max_entries
        return audit[overflow:] if overflow > 0 else audit

    # --- persistence ----------------------------------------------------------
    def _persist_state(self, version: int, effective: Mapping[str, float],
                       audit: list[dict[str, Any]]) -> bool:
        """Write the prospective state; ``False`` means the change must not stand.

        Persisting *before* adopting is what keeps the reported version equal to
        the durable one. With no persister (in-memory runs, tests) there is
        nothing to fail.
        """
        if self._persist is None:
            return True
        snapshot = {"version": version, "effective": dict(effective),
                    "audit": list(audit), "reference": dict(self._reference)}
        try:
            self._persist(snapshot)
        except Exception:  # noqa: BLE001 - a failed write is a "no", not a crash
            return False
        return True

    def snapshot(self) -> dict[str, Any]:
        return {"version": self._version, "effective": self.effective(),
                "audit": list(self._audit), "reference": dict(self._reference)}

    def load(self, state: Optional[Mapping[str, Any]]) -> None:
        if not isinstance(state, Mapping):
            return
        version = state.get("version")
        if isinstance(version, int) and version >= 0:
            self._version = version
        effective = state.get("effective")
        if isinstance(effective, Mapping):
            merged = dict(self._baseline)
            for key in merged:
                value = effective.get(key)
                if isinstance(value, (int, float)):
                    # Reloading must not escape the clamp: a hand-edited state
                    # file cannot widen the policy beyond its configured bounds.
                    merged[key] = (_clamp(float(value), self._baseline[key],
                                          self._config.policy_max_weight_drift_ratio)
                                   if key in TUNABLE_WEIGHTS
                                   else round(min(self._config.policy_max_bonus_points,
                                                  max(0.0, float(value))), 6))
            self._effective = merged
        audit = state.get("audit")
        if isinstance(audit, (list, tuple)):
            self._audit = [dict(row) for row in audit if isinstance(row, Mapping)]
            self._trim_audit()
        reference = state.get("reference")
        if isinstance(reference, Mapping):
            for key in ("cost", "latency"):
                value = reference.get(key)
                if isinstance(value, (int, float)) and value > 0:
                    self._reference[key] = float(value)

    def _save(self) -> None:
        if self._persist is None:
            return
        try:
            self._persist(self.snapshot())
        except Exception:  # noqa: BLE001 - policy bookkeeping must never break dispatch
            pass
