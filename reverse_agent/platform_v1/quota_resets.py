"""Quota resets seen in an account's own readings (Owner decision 2026-11-24).

Announcements cover Codex and Claude only. Here two readings of the same account and
window show a reset of any provider:

* ``early``: usage fell and the reset time moved later, before the stated reset;
* ``scheduled``: the stated reset passed and a reading taken after it shows usage fell.

A reset is evidence, never capacity: admission and pacing keep their own reading rules,
and a refusal hold is only released while a current reading shows room (``released``).

Not evidence: an unused or sliding window whose reset time moves with every read (it is
never *anchored*), a dip with the reset unchanged, a reading that is older than one
already seen, undated, or past ``READING_MAX_AGE_SECONDS``, and another account, plan or
window. A window of one model tier says nothing about another tier of the same account.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from typing import Any, Iterable, Mapping

from ..model_access.quota_forecast import iso, parse_time

READING_MAX_AGE_SECONDS = 3600
MIN_DROP = 5.0            # percentage points; smaller moves are provider rounding
MIN_LATER_SECONDS = 900   # a reset time also drifts by seconds to minutes
ROOM_LIMIT = 98.0         # as the guard's near-limit: above it a hold is not released
KEEP_SECONDS = 30 * 86400
RECENT_LIMIT = 20

_LENGTH = re.compile(r"(?<![\w.])(\d{1,3})\s*-?\s*(hours?|days?|h|d)(?!\w)", re.IGNORECASE)
_FAMILIES = ("claude", "fable", "opus", "sonnet", "haiku", "gpt", "codex", "gemini", "gemma", "glm",
             "deepseek", "kimi", "qwen", "grok", "doubao", "minimax", "mistral", "llama", "hy3")

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS platform_quota_reset_state (account_ref TEXT NOT NULL, window TEXT NOT NULL, "
    "state_json TEXT NOT NULL, PRIMARY KEY (account_ref, window))",
    "CREATE TABLE IF NOT EXISTS platform_quota_resets (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, "
    "window TEXT NOT NULL, provider TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL, "
    "detected_at REAL NOT NULL, observed_at REAL NOT NULL, before_observed_at REAL NOT NULL, "
    "used_before REAL NOT NULL, used_after REAL NOT NULL, previous_resets_at REAL NOT NULL, resets_at REAL, "
    "UNIQUE (account_ref, window, previous_resets_at))",
    "CREATE INDEX IF NOT EXISTS idx_platform_quota_resets_account "
    "ON platform_quota_resets(account_ref, observed_at)",
)


def _percent(value: Any) -> float | None:
    return float(value) if type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100 else None


def window_seconds(name: str) -> float | None:
    """The stated length of a window: ``Gemini · 7 days`` is a week; None when the name has none."""
    match = _LENGTH.search(name)
    if match:
        return int(match.group(1)) * (3600 if match.group(2).lower().startswith("h") else 86400)
    return 7 * 86400 if "weekly" in name.lower() else None


def applies_to_model(window: str, model_id: str) -> bool:
    """Whether a window limits this model: a window naming model families limits only those.

    ``Gemini · 7 days`` never limits a Claude model on the same account; ``7 days`` and
    ``Credits`` limit every model. ``Gemini 4 Argon`` limits that model line only.
    """
    label = _LENGTH.sub(" ", window.lower())
    if not any(family in label for family in _FAMILIES):
        return True
    model = re.sub(r"[^a-z0-9]+", "-", str(model_id).lower().rsplit("/", 1)[-1])
    for part in re.split(r"[&/,·|]|\band\b", label):
        name = re.sub(r"[^a-z0-9]+", "-", part).strip("-")
        if name and any(family in name for family in _FAMILIES) and name in model:
            return True
    return False


def unidentified(provider: str, account_ref: str) -> bool:
    """Whether the account has no user behind it: two logins would share this reference."""
    identity = json.dumps([provider, None], ensure_ascii=True)
    return hashlib.sha256(identity.encode()).hexdigest()[:12] == account_ref


def readings(snapshot: Any, *, now: float) -> list[dict[str, Any]]:
    """The dated, identified account readings of one Magpie snapshot usable here."""
    accounts = snapshot.get("accounts") if isinstance(snapshot, Mapping) and snapshot.get("status") == "available" else None
    accounts = [a for a in accounts if isinstance(a, Mapping)] if isinstance(accounts, list) else []
    refs = [a.get("account_ref") for a in accounts]
    result = []
    for account in accounts:
        ref, provider = account.get("account_ref"), account.get("provider")
        at = parse_time(account.get("observed_at"))
        if (not isinstance(ref, str) or not ref or refs.count(ref) != 1 or not isinstance(provider, str)
                or account.get("state") not in {"FRESH", "STALE"}
                or at is None or not 0 <= now - at <= READING_MAX_AGE_SECONDS):
            continue
        rows = account.get("windows") or account.get("cached_windows") or []
        names = [w.get("name") for w in rows if isinstance(w, Mapping)]
        windows = {}
        for window in rows:
            if not isinstance(window, Mapping) or window.get("unlimited") is True:
                continue
            name, used = window.get("name"), _percent(window.get("used_percent"))
            raw = window.get("resets_at")
            reset = parse_time(raw)
            if not isinstance(name, str) or not name or names.count(name) != 1 or used is None \
                    or (raw is not None and reset is None):
                continue
            windows[name] = {"used": used, "resets_at": reset}
        if windows:
            result.append({"account_ref": ref, "provider": provider, "plan": account.get("plan") or "",
                           "observed_at": at, "windows": windows})
    return result


def _anchored(name: str, at: float, reset: float, previous: Mapping[str, Any] | None) -> bool:
    """Whether this reset time is a fixed point, not one that moves with every read."""
    length = window_seconds(name)
    if length is not None and reset < at + length - 300:
        # Started before this read. A sliding window stays a full length ahead of it.
        return True
    if previous is None or previous.get("resets_at") is None:
        return False
    elapsed = at - previous["observed_at"]
    shift = abs(reset - previous["resets_at"])
    return elapsed >= 60 and shift <= min(300.0, elapsed / 2)


class QuotaResets:
    """Baselines and events, stored with the control data; every call is one transaction."""

    def __init__(self, conn: Any, lock: Any) -> None:
        self._conn, self._lock = conn, lock

    def observe(self, snapshot: Any, *, now: float) -> list[dict[str, Any]]:
        """Record readings; return the resets this snapshot shows for the first time."""
        found = []
        with self._lock, self._conn:
            for reading in readings(snapshot, now=now):
                for name, window in reading["windows"].items():
                    event = self._observe_window(reading, name, window, now)
                    if event is not None:
                        found.append(event)
            self._conn.execute("DELETE FROM platform_quota_resets WHERE observed_at < ?", (now - KEEP_SECONDS,))
        return found

    def _observe_window(self, reading: Mapping[str, Any], name: str, window: Mapping[str, Any],
                        now: float) -> dict[str, Any] | None:
        ref, at = reading["account_ref"], reading["observed_at"]
        used, reset = window["used"], window["resets_at"]
        row = self._conn.execute("SELECT state_json FROM platform_quota_reset_state WHERE account_ref=? AND window=?",
                                 (ref, name)).fetchone()
        state = json.loads(row[0]) if row else None
        if state is not None and at <= state["latest_at"]:
            return None  # repeated or out-of-order reading
        base = state["base"] if state else None
        if state is not None and state["plan"] != reading["plan"]:
            base = None  # another subscription answers now: nothing to compare with
        event = None
        if base is not None:
            event = self._event(reading, name, base, at, used, reset, now)
            self._retract(ref, name, at, reset, used, now)
        if reset is not None:
            base = {"observed_at": at, "used": used, "resets_at": reset,
                    "anchored": _anchored(name, at, reset, base)}
        elif base is not None and at >= base["resets_at"]:
            base = None  # the old window is over and no new one has started
        self._conn.execute(
            "INSERT OR REPLACE INTO platform_quota_reset_state VALUES (?,?,?)",
            (ref, name, json.dumps({"provider": reading["provider"], "plan": reading["plan"], "latest_at": at,
                                    "used": used, "resets_at": reset, "base": base})))
        return event

    def _event(self, reading: Mapping[str, Any], name: str, base: Mapping[str, Any], at: float,
               used: float, reset: float | None, now: float) -> dict[str, Any] | None:
        ref, old = reading["account_ref"], base["resets_at"]
        if not base["anchored"] or base["used"] - used < MIN_DROP:
            return None
        later = reset is not None and reset - old >= MIN_LATER_SECONDS
        if at >= old and (later or reset is None):
            kind = "scheduled"
        elif at < old and later and not unidentified(reading["provider"], ref):
            kind = "early"
        else:
            return None
        values = {"provider": reading["provider"], "kind": kind, "status": "active", "detected_at": now,
                  "observed_at": at, "before_observed_at": base["observed_at"], "used_before": base["used"],
                  "used_after": used, "resets_at": reset}
        # One event per account, window and ended cycle; a reset time drifts by seconds.
        known = self._conn.execute(
            "SELECT id, status FROM platform_quota_resets WHERE account_ref=? AND window=? "
            "AND ABS(previous_resets_at - ?) < ? ORDER BY observed_at DESC LIMIT 1",
            (ref, name, old, MIN_LATER_SECONDS)).fetchone()
        if known is not None:
            if known["status"] == "active":
                return None
            self._conn.execute("UPDATE platform_quota_resets SET " + ", ".join(f"{k}=?" for k in values)
                               + " WHERE id=?", (*values.values(), known["id"]))
        else:
            values |= {"account_ref": ref, "window": name, "previous_resets_at": old}
            self._conn.execute(f"INSERT INTO platform_quota_resets ({', '.join(values)}) "
                               f"VALUES ({', '.join('?' * len(values))})", tuple(values.values()))
        return {**values, "account_ref": ref, "window": name, "previous_resets_at": old}

    def _retract(self, ref: str, name: str, at: float, reset: float | None, used: float, now: float) -> None:
        """A later reading back on the old window shows the earlier one was wrong."""
        if reset is None:
            return
        self._conn.execute(
            "UPDATE platform_quota_resets SET status='retracted', detected_at=? WHERE account_ref=? AND window=? "
            "AND kind='early' AND status='active' AND observed_at < ? AND previous_resets_at > ? "
            "AND ABS(previous_resets_at - ?) < 300 AND used_after + ? <= ?",
            (now, ref, name, at, at, reset, MIN_DROP, used))

    def passed(self, *, since: float, now: float) -> bool:
        """Whether a used window's stated reset passed in (since, now]: time to read again."""
        with self._lock:
            rows = self._conn.execute("SELECT state_json FROM platform_quota_reset_state").fetchall()
        for row in rows:
            base = json.loads(row[0])["base"]
            if base and base["anchored"] and base["used"] >= MIN_DROP and since < base["resets_at"] <= now:
                return True
        return False

    def recent(self, accounts: Iterable[str] | None = None, *, since: float = 0) -> list[dict[str, Any]]:
        """Confirmed resets, newest first, for display."""
        with self._lock:
            rows = [dict(r) for r in self._conn.execute(
                "SELECT account_ref, window, provider, kind, detected_at, observed_at, used_before, used_after, "
                "previous_resets_at, resets_at FROM platform_quota_resets WHERE status='active' "
                "AND observed_at >= ? ORDER BY observed_at DESC, id DESC", (since,))]
        wanted = None if accounts is None else set(accounts)
        return [r for r in rows if wanted is None or r["account_ref"] in wanted][:RECENT_LIMIT]

    def released(self, account_ref: str, model_id: str, *, hit_at: float, now: float,
                 stated_reset: float | None = None) -> bool:
        """Whether the account reset after it refused a run, and has room again now.

        A refusal that stated its own reset is only answered by a reset of that very
        window: another, shorter window starting over says nothing about it.
        """
        with self._lock:
            events = self._conn.execute(
                "SELECT window, previous_resets_at FROM platform_quota_resets "
                "WHERE account_ref=? AND status='active' AND observed_at > ?", (account_ref, hit_at)).fetchall()
            rows = [(r["window"], json.loads(r["state_json"])) for r in self._conn.execute(
                "SELECT window, state_json FROM platform_quota_reset_state WHERE account_ref=?", (account_ref,))]
        events = [e for e in events if applies_to_model(e["window"], model_id)
                  and (stated_reset is None or abs(e["previous_resets_at"] - stated_reset) <= MIN_LATER_SECONDS)]
        if not events or not rows:
            return False
        latest = max(state["latest_at"] for _, state in rows)
        if not hit_at < latest or now - latest > READING_MAX_AGE_SECONDS:
            return False
        current = [state for name, state in rows if state["latest_at"] == latest and applies_to_model(name, model_id)]
        return bool(current) and all(state["used"] < ROOM_LIMIT for state in current)


def public_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Event as the web client reads it; times as ISO text."""
    return {**{k: event[k] for k in ("account_ref", "provider", "window", "kind", "used_before", "used_after")},
            "observed_at": iso(event["observed_at"]), "previous_resets_at": iso(event["previous_resets_at"]),
            "resets_at": iso(event["resets_at"]) if event["resets_at"] is not None else None}
