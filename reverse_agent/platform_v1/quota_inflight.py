"""Cooperative quota control. All provider and save transports are injected.

Native transports feed this controller through the durable executor facade.
The host parks verified partial work and settles reservations; model selection
and readmission remain with existing host authority.

A signal is an estimate, never authority to stop or resume. Only durable SAVED
plus an acknowledged clean stop permits PAUSED. Role milestones are untouched.
"""
from __future__ import annotations

import json

from . import quota_reservation, usage_ledger
from ..model_access import pricing


def reduce_signal(state, source, sequence, signal):
    """Reduce ordered cumulative counters; decreases start a new counter segment."""
    state = json.loads(json.dumps(state))
    if not source or type(sequence) is not int or sequence < 0:
        raise ValueError("invalid signal identity")
    if sequence <= state["sequences"].get(source, -1):
        return state, False
    signal = dict(signal)
    previous = state["sources"].get(source, {})
    values = signal.get("spent", {})
    if "tokens" in signal:
        raw = signal["tokens"]
        keys = ("input_tokens", "cached_input_tokens", "output_tokens")
        if any(type(raw.get(k)) is not int or raw[k] < 0 for k in keys) or raw[keys[1]] > raw[keys[0]]:
            raise ValueError("invalid token counters")
        old = previous.get("tokens", {})
        reset = any(raw[k] < old.get(k, 0) for k in keys)
        totals = {k: previous.get("totals", {}).get(k, 0) +
                  (raw[k] if reset else raw[k] - old.get(k, 0)) for k in keys}
        estimate = state["estimate"]
        cost = pricing.equivalent_cost(estimate.get("estimate", {}).get("model", ""),
                                      usage_ledger._native(totals, "codex"))["usd"]
        values = {w: cost / rate if quota_reservation._number(cost) and
                  quota_reservation._number(rate) and rate > 0 else None
                  for w in ("five_hour", "weekly")
                  for rate in [estimate.get("calibration", {}).get(w)]}
        previous.update(tokens={k: raw[k] for k in keys}, totals=totals)
    for window, value in values.items():
        if window not in {"five_hour", "weekly"}:
            raise ValueError("invalid signal window")
        if value is None:
            state["uncertain"] = True
            state["high_water"][window] = None
        elif not quota_reservation._number(value):
            raise ValueError("invalid signal spend")
        elif state["high_water"].get(window, 0) is not None:
            state["high_water"][window] = max(state["high_water"].get(window, 0), value)
    if "rate_limit" in signal:
        notice = signal["rate_limit"]
        window = {"five_hour": "five_hour", "seven_day": "weekly", "weekly": "weekly"}.get(notice.get("window"))
        value = notice.get("utilization")
        if window and notice.get("status") == "rejected":
            state["pressure"][window] = 100
        elif window and quota_reservation._number(value) and value <= 100:
            value = value * 100 if value <= 1 else value
            state["pressure"][window] = max(state["pressure"].get(window, 0), value)
        else:
            state["uncertain"] = True
            for name in ([window] if window else ("five_hour", "weekly")):
                state["high_water"][name] = None
    previous["signal"] = signal
    state["sources"][source] = previous
    state["sequences"][source] = sequence
    return state, True


def projection(evidence, need, outstanding=(), *, reservation_id, spent, now, headroom=10, anchor=None, pressure=None):
    """Project cumulative spend plus remaining p80 in each account window.

    Keep the frozen observation as the accounting anchor: refreshing an account
    observation cannot silently erase local spend or concurrent reservations.
    No signals means no measured progress, so the whole p80 remains reserved.
    """
    if need.get("account_ref", evidence.get("account_ref")) != evidence.get("account_ref"):
        raise ValueError("projection account mismatch")
    anchor = anchor or evidence
    if anchor.get("account_ref") != evidence.get("account_ref"):
        raise ValueError("projection account mismatch")
    baseline = {w.get("window", w.get("name")): w for w in anchor.get("windows", [])}
    adjusted = []
    windows = {}
    for window in evidence.get("windows", []):
        name = window.get("window", window.get("name"))
        total = need.get("windows", {}).get(name, {}).get("p80")
        used = spent.get(name, 0)
        if used is not None and not quota_reservation._number(used):
            raise ValueError("invalid live spend")
        remaining = max(0, total - used) if quota_reservation._number(total) and used is not None else None
        windows[name] = {"p80": remaining}
        prior = baseline.get(name, {}).get("used_percent")
        current = window.get("used_percent")
        measured = prior + used if quota_reservation._number(prior) and used is not None else None
        candidates = [v for v in (current, measured, (pressure or {}).get(name)) if quota_reservation._number(v)]
        adjusted.append(dict(window, used_percent=max(candidates) if candidates else None))
    evidence = dict(evidence, windows=adjusted)
    others = [r for r in outstanding if r.get("reservation_id") != reservation_id]
    # An absent identity must not exclude every unidentified reservation.
    if not reservation_id:
        raise ValueError("reservation identity required")
    return quota_reservation.admission(evidence, {"windows": windows}, others,
                                      now=now, buffer=headroom)


class CooperativeQuotaCheckpoint:
    """Host-side state machine; callbacks must implement real cooperative I/O.

    journal(state, payload) is a fenced TaskStore transaction. verify(payload)
    independently checks saved artifact/workspace bytes. Stop returns True only
    after a clean transport acknowledgement, never merely after kill/terminate.
    resume(checkpoint_id, payload) must deduplicate dispatch by checkpoint ID.
    A RESUMING journal after a crash is intentionally left for reconciliation.
    """
    def __init__(self, *, checkpoint_id, journal, request, verify, stop, clock, signals=None):
        self.checkpoint_id = checkpoint_id
        self.journal = journal
        self.request = request
        self.verify = verify
        self.stop = stop
        self.clock = clock
        self.signals = signals
        self.wait_verdict = None
        self.pressure = {}
        self.high_water = {}
        self.sequences = {}
        if signals is not None:
            self._load_signals(signals())

    def _load_signals(self, state):
        self.high_water = state["high_water"]
        self.sequences = state["sequences"]
        self.pressure = state["pressure"]
        self.account_ref = state["account_ref"]

    def observe_signal(self, source, sequence, signal):
        if self.signals is None:
            raise ValueError("durable signal journal required")
        state = self.signals(source=source, sequence=sequence, signal=signal)
        self._load_signals(state)
        return state["accepted"]

    def observe(self, source, sequence, spent):
        if self.signals is not None:
            return self.observe_signal(source, sequence, {"spent": spent})
        if type(sequence) is not int or sequence < 0:
            raise ValueError("invalid signal sequence")
        if sequence <= self.sequences.get(source, -1):
            return False
        values = dict(spent)
        if any(not quota_reservation._number(v) for v in values.values()):
            raise ValueError("invalid signal spend")
        self.sequences[source] = sequence
        for window, value in values.items():
            self.high_water[window] = max(self.high_water.get(window, 0), value)
        return True

    def tick(self, evidence, need, outstanding, *, reservation_id, headroom=10, refresh=None):
        if self.signals is not None:
            self._load_signals(self.signals())
            if evidence.get("account_ref") != self.account_ref:
                raise ValueError("live signal account mismatch")
        row = self.journal(None, None)
        if row is not None:
            return row["state"]
        result = projection(evidence, need, outstanding, reservation_id=reservation_id,
                            spent=self.high_water, now=self.clock(), headroom=headroom, pressure=self.pressure)
        if refresh is not None:
            fresh = refresh(evidence["account_ref"])
            if fresh is not None:
                # Both the frozen accounting anchor and refreshed pressure apply.
                updated = projection(fresh, need, outstanding, reservation_id=reservation_id,
                                     spent=self.high_water, now=self.clock(), headroom=headroom,
                                     anchor=evidence, pressure=self.pressure)
                if updated["decision"] == "quota_wait":
                    result = updated
        if result["decision"] == "quota_wait":
            self.wait_verdict = result
            requested = self.journal("REQUESTED", None)
            if not requested["transitioned"]:
                return requested["state"]
            # Persist first. A crash/failed request cannot manufacture a save.
            self.request(self.checkpoint_id)
            return "REQUESTED"
        return "RUNNING"

    def saved(self, checkpoint_id, payload):
        if checkpoint_id != self.checkpoint_id:
            raise ValueError("checkpoint acknowledgement mismatch")
        row = self.journal(None, None)
        if row is None or row["state"] not in {"REQUESTED", "SAVED", "PAUSED"}:
            raise ValueError("checkpoint not requested")
        if row["state"] == "PAUSED":
            if json.loads(row["payload_json"]) != payload:
                raise ValueError("conflicting saved acknowledgement")
            return "PAUSED"
        if not self.verify(payload):
            self.journal("FAILED", None)
            return "FAILED"
        self.journal("SAVED", payload)
        # A failed stop leaves SAVED for recovery; it is not a quota pause.
        if self.stop(self.checkpoint_id) is True:
            self.journal("PAUSED", None)
            return "PAUSED"
        return "SAVED"

    def limit_hit(self):
        self.journal("LIMIT_HIT", None)

    def resume(self, *, admit, dispatch):
        row = self.journal(None, None)
        if row is None or row["state"] != "PAUSED":
            raise ValueError("checkpoint not paused; reconcile ambiguous dispatch first")
        payload = json.loads(row["payload_json"])
        if not self.verify(payload):
            raise ValueError("checkpoint proof changed")
        if admit(payload) is not True:
            return "QUOTA_WAIT"
        claimed = self.journal("RESUMING", None)
        if not claimed["transitioned"]:
            raise ValueError("checkpoint resume already claimed")
        dispatch(self.checkpoint_id, payload)
        self.journal("RESUMED", None)
        return "RESUMED"
