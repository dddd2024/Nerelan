"""Subscription quota windows as the official CLIs report them (P0-3).

Two first-party sources, no vendor call and no credential access:

* Codex writes ``token_count`` events with the account's ``rate_limits`` (5-hour and
  weekly windows, percent used, reset time, plan, credits) into its session logs under
  ``$CODEX_HOME/sessions`` (default ``~/.codex``). Only those events are parsed; the
  conversation lines around them are skipped unread beyond JSON decoding.
* Claude Code emits ``rate_limit_event`` notices in its stream output. Nerelan's Claude
  executor keeps an allowlisted projection of them, so they are read from the TaskStore
  by the trusted host and normalized here.

A window whose reset time has passed is reported as ``reset_passed``: the CLI has not
said anything newer, so its current use is unknown, not zero.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Iterable, Mapping

_TAIL_BYTES = 2 * 1024 * 1024
_MAX_FILES = 12
_MAX_AGE_SECONDS = 8 * 24 * 3600
_CLAUDE_WINDOWS = {"five_hour": "five_hour", "seven_day": "weekly"}


def _iso(epoch: float | int | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _window_name(minutes: Any) -> str:
    return {300: "five_hour", 10080: "weekly"}.get(minutes, f"{minutes}_minutes" if type(minutes) is int else "window")


def _window(name: str, *, used_percent: Any, resets_at: Any, minutes: Any = None, status: Any = None,
            now: float) -> dict[str, Any]:
    used = float(used_percent) if type(used_percent) in (int, float) and 0 <= used_percent <= 100 else None
    resets = resets_at if type(resets_at) is int and 0 < resets_at < 10**11 else None
    return {"window": name, "used_percent": used, "resets_at": _iso(resets),
            "window_minutes": minutes if type(minutes) is int else None,
            "status": status if isinstance(status, str) else None,
            "reset_passed": bool(resets is not None and resets <= now)}


def unknown(reason: str) -> dict[str, Any]:
    return {"state": "UNKNOWN", "provenance": "UNAVAILABLE", "reason": reason, "windows": []}


def codex_rate_limits(event: Mapping[str, Any], observed_at: str | None, *, now: float | None = None) -> dict[str, Any]:
    """Normalize one Codex ``token_count`` payload's ``rate_limits``."""
    now = time.time() if now is None else now
    limits = event.get("rate_limits")
    if not isinstance(limits, Mapping):
        return unknown("no_rate_limits_reported")
    windows = []
    for key in ("primary", "secondary"):
        window = limits.get(key)
        if isinstance(window, Mapping):
            windows.append(_window(_window_name(window.get("window_minutes")), used_percent=window.get("used_percent"),
                                   resets_at=window.get("resets_at"), minutes=window.get("window_minutes"), now=now))
    result: dict[str, Any] = {"state": "OBSERVED", "provenance": "OFFICIAL_VIA_CLI", "source": "codex_session_log",
                              "observed_at": observed_at, "windows": windows}
    if isinstance(limits.get("plan_type"), str):
        result["plan"] = limits["plan_type"][:40]
    credits = limits.get("credits")
    if isinstance(credits, Mapping):
        result["credits"] = {k: credits[k] for k in ("has_credits", "unlimited") if isinstance(credits.get(k), bool)}
        if isinstance(credits.get("balance"), str) and len(credits["balance"]) <= 40:
            result["credits"]["balance"] = credits["balance"]
    if isinstance(limits.get("rate_limit_reached_type"), str):
        result["limit_reached"] = limits["rate_limit_reached_type"][:40]
    return result


def _latest_token_count(path: Path) -> tuple[dict[str, Any], str | None] | None:
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - _TAIL_BYTES))
        lines = handle.read().splitlines()
    for raw in reversed(lines):
        if b'"token_count"' not in raw or b'"rate_limits"' not in raw:
            continue  # never decode conversation lines
        try:
            entry = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            continue
        payload = entry.get("payload") if isinstance(entry, dict) else None
        if isinstance(payload, dict) and payload.get("type") == "token_count" and payload.get("rate_limits"):
            stamp = entry.get("timestamp")
            return payload, stamp if isinstance(stamp, str) and len(stamp) <= 40 else None
    return None


def read_codex_quota(codex_home: str | os.PathLike[str] | None = None, *, now: float | None = None) -> dict[str, Any]:
    """Latest Codex account windows from recent session logs, or UNKNOWN."""
    now = time.time() if now is None else now
    home = Path(codex_home or os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    sessions = home / "sessions"
    if not sessions.is_dir():
        return unknown("codex_sessions_not_found")
    try:
        files = sorted((p for p in sessions.glob("*/*/*/*.jsonl") if now - p.stat().st_mtime <= _MAX_AGE_SECONDS),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:_MAX_FILES]
    except OSError:
        return unknown("codex_sessions_unreadable")
    for path in files:
        try:
            found = _latest_token_count(path)
        except OSError:
            continue
        if found:
            return codex_rate_limits(found[0], found[1], now=now)
    return unknown("no_recent_codex_rate_limits")


def claude_rate_limits(notices: Iterable[Mapping[str, Any]], observed_at: str | None,
                       *, now: float | None = None) -> dict[str, Any]:
    """Normalize the Claude executor's persisted ``rate_limits`` projection."""
    now = time.time() if now is None else now
    windows = []
    for notice in notices:
        if not isinstance(notice, Mapping):
            continue
        raw_name = notice.get("window") if isinstance(notice.get("window"), str) else "window"
        utilization = notice.get("utilization")
        # Claude reports utilization as a 0-1 fraction of the window.
        used = utilization * 100 if type(utilization) in (int, float) and 0 <= utilization <= 1 else None
        windows.append(_window(_CLAUDE_WINDOWS.get(raw_name, raw_name), used_percent=used,
                               resets_at=notice.get("resets_at"), status=notice.get("status"), now=now))
    if not windows:
        return unknown("no_rate_limits_reported")
    return {"state": "OBSERVED", "provenance": "OFFICIAL_VIA_CLI", "source": "claude_rate_limit_event",
            "observed_at": observed_at, "windows": windows}


# ---- Tiered windows: official percent > official status > estimate from history > unknown ----

_RECENT_HITS = 20


def _hits_public(hits: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    from .quota_forecast import iso
    ordered = sorted(hits, key=lambda hit: hit["at"], reverse=True)[:_RECENT_HITS]
    return [{"at": iso(hit["at"]), "window": hit.get("window"), "source": hit.get("source")} for hit in ordered]


def codex_quota(codex_home: str | os.PathLike[str] | None = None, *, now: float | None = None) -> dict[str, Any]:
    """Official Codex windows plus, from history, how many usage units are left in each."""
    from .quota_forecast import capacity_from_percent
    from .quota_history import read_codex_history
    now = time.time() if now is None else now
    history = read_codex_history(codex_home, now=now)
    if history.latest is None:
        return unknown("no_recent_codex_rate_limits")
    snapshot = codex_rate_limits(*history.latest, now=now)
    capacity = capacity_from_percent(history.percents)
    for window in snapshot["windows"]:
        window["basis"] = "official_percent" if window["used_percent"] is not None else "unknown"
        cap = capacity.get(window["window"])
        if cap and window["used_percent"] is not None and not window["reset_passed"]:
            left = (100 - window["used_percent"]) / 100
            window["capacity_units"] = cap
            window["remaining_units_range"] = [round(left * cap["low"], 4), round(left * cap["high"], 4)]
    snapshot["limit_hits"] = _hits_public(history.hits)
    snapshot["usage_scope"] = "this_machine"
    return snapshot


def claude_quota(notices: tuple[list, str | None] | None, config_dir: str | os.PathLike[str] | None = None,
                 *, now: float | None = None) -> dict[str, Any]:
    """Claude windows: official notices where seen, else estimated from local history."""
    from .quota_forecast import (availability, capacity_from_hits, estimated_window, iso, parse_time,
                                 rolling_blocks)
    from .quota_history import read_claude_history
    now = time.time() if now is None else now
    official = claude_rate_limits(*notices, now=now) if notices else unknown("no_rate_limits_reported")
    windows = []
    for window in official["windows"]:
        window["basis"] = "official_percent" if window["used_percent"] is not None else "official_status"
        window["availability"] = availability(window["status"])
        windows.append(window)
    history = read_claude_history(config_dir, now=now)
    hits = list(history.hits) + [{"at": parse_time(official.get("observed_at")) or now, "window": w["window"],
                                  "source": "claude_rate_limit_event"}
                                 for w in windows if w["status"] == "rejected"]
    five = next((w for w in windows if w["window"] == "five_hour"), None)
    if five is None or five["used_percent"] is None:
        capacity = capacity_from_hits(history.usage, [hit["at"] for hit in history.hits])
        blocks = rolling_blocks(history.usage)
        current = blocks[-1] if blocks and now < blocks[-1]["end"] else None
        official_reset = parse_time(five["resets_at"]) if five else None
        estimate: dict[str, Any] | None = None
        if current and any(current["start"] <= hit["at"] < current["end"] for hit in history.hits):
            estimate = {"window": "five_hour", "basis": "estimated", "used_percent": 100.0,
                        "used_percent_range": [100.0, 100.0], "availability": "limit_reached",
                        "resets_at": iso(official_reset or current["end"]), "reset_passed": False,
                        "remaining_units_range": [0.0, 0.0], "used_units": round(current["units"], 4)}
        elif capacity:
            used = current["units"] if current else 0.0
            # No usage in the last five hours: the next request opens a fresh window.
            estimate = estimated_window("five_hour", used_units=used, capacity=capacity,
                                        resets_at=official_reset or (current["end"] if current else None), now=now)
        elif current:
            estimate = {"window": "five_hour", "basis": "unknown", "used_percent": None,
                        "used_units": round(current["units"], 4), "resets_at": iso(official_reset or current["end"]),
                        "reset_passed": False, "reason": "capacity_unknown_no_limit_hit_yet"}
        if estimate is not None:
            estimate["resets_at_estimated"] = official_reset is None
            if five is not None:
                if estimate.get("availability") != "limit_reached" and not five["reset_passed"]:
                    estimate["status"] = five["status"]
                    estimate["availability"] = five["availability"]
                windows.remove(five)
            windows.insert(0, estimate)
    if not windows:
        return unknown("no_claude_quota_signal")
    is_official = any(w["basis"].startswith("official") for w in windows)
    return {"state": "OBSERVED", "provenance": "OFFICIAL_VIA_CLI" if is_official else "ESTIMATED_FROM_HISTORY",
            "source": official.get("source") or "claude_session_log", "observed_at": official.get("observed_at"),
            "windows": windows, "limit_hits": _hits_public(hits), "usage_scope": "this_machine"}
