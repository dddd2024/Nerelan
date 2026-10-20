"""Cooperative quota control. All provider and save transports are injected.

This controller is not yet wired into TaskRuntime, durable role dispatch or the
unattended coordinator. Current native one-shot CLI transports cannot provide
cooperative save/clean-stop acknowledgements. Reservation settlement and model
selection remain with existing host authority; these callbacks do not replace it.

A signal is an estimate, never authority to stop or resume. Only durable SAVED
plus an acknowledged clean stop permits PAUSED. Role milestones are untouched.
"""
from __future__ import annotations

import json
import math

from . import quota_reservation


def projection(evidence, need, outstanding=(), *, reservation_id, spent, now, headroom=10):
    """Project cumulative spend plus remaining p80 in each account window.

    Keep the frozen observation as the accounting anchor: refreshing an account
    observation cannot silently erase local spend or concurrent reservations.
    No signals means no measured progress, so the whole p80 remains reserved.
    """
    windows = {}
    for name in ("five_hour", "weekly"):
        total = need.get("windows", {}).get(name, {}).get("p80")
        used = spent.get(name, 0)
        if type(used) not in (int, float) or not math.isfinite(used) or used < 0:
            raise ValueError("invalid live spend")
        remaining = max(0, total - used) if quota_reservation._number(total) else None
        windows[name] = {"p80": used + remaining if remaining is not None else None}
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
    def __init__(self, *, checkpoint_id, journal, request, verify, stop, clock):
        self.checkpoint_id = checkpoint_id
        self.journal = journal
        self.request = request
        self.verify = verify
        self.stop = stop
        self.clock = clock
        self.high_water = {}
        self.sequences = {}

    def observe(self, source, sequence, spent):
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
        row = self.journal(None, None)
        if row is not None:
            return row["state"]
        result = projection(evidence, need, outstanding, reservation_id=reservation_id,
                            spent=self.high_water, now=self.clock(), headroom=headroom)
        if refresh is not None:
            fresh = refresh(evidence["account_ref"])
            if fresh is not None:
                # Both the frozen accounting anchor and refreshed pressure apply.
                updated = projection(fresh, need, outstanding, reservation_id=reservation_id,
                                     spent=self.high_water, now=self.clock(), headroom=headroom)
                if updated["decision"] == "quota_wait":
                    result = updated
        if result["decision"] == "quota_wait":
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
