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
_MAX_FILES = 64
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


def _latest_token_count(path: Path, *, now: float) -> tuple[dict[str, Any], str | None] | None:
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
        limits = payload.get("rate_limits") if isinstance(payload, dict) and payload.get("type") == "token_count" else None
        # Empty window metadata is not proof of current available quota.
        if isinstance(limits, dict) and any(isinstance(limits.get(k), dict) for k in ("primary", "secondary")):
            from .quota_forecast import parse_time
            stamp = entry.get("timestamp")
            at = parse_time(stamp)
            # A clock-skewed future record must not hide an earlier actual
            # account observation in the *same* Codex session file.
            if at is not None and at <= now + 60:
                return payload, stamp
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
    from .quota_forecast import parse_time

    # File mtime is a scanner bound, NOT the account observation clock. Other
    # sessions may be modified after an older quota event, so select the most
    # recent provider-stamped window across bounded eligible files.
    latest: tuple[dict[str, Any], str | None] | None = None
    latest_at = -1.0
    for path in files:
        try:
            found = _latest_token_count(path, now=now)
        except OSError:
            continue
        if found:
            at = parse_time(found[1])
            if at is not None and at <= now + 60 and at > latest_at:
                latest, latest_at = found, at
    if latest is not None:
        return codex_rate_limits(latest[0], latest[1], now=now)
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


CLAUDE_WINDOW_SECONDS = {"five_hour": 5 * 3600, "weekly": 7 * 24 * 3600}
HIT_CAPACITY_SPREAD = 1.5
FRESH_SECONDS = 600


def read_statusline_records(path: str | os.PathLike[str] | None = None, *, now: float | None = None) -> list[dict]:
    """Official Claude windows recorded by the Nerelan status line (claude_statusline.py)."""
    from .claude_statusline import log_path
    now = time.time() if now is None else now
    try:
        lines = Path(path or log_path()).read_bytes().splitlines()[-4000:]
    except OSError:
        return []
    records = []
    for raw in lines:
        try:
            item = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            continue
        if not isinstance(item, dict):
            continue
        at, window, used, reset = item.get("at"), item.get("window"), item.get("used_percent"), item.get("resets_at")
        if (type(at) is int and now - _MAX_AGE_SECONDS <= at <= now + 60 and window in CLAUDE_WINDOW_SECONDS
                and type(used) in (int, float) and 0 <= used <= 100 and (reset is None or type(reset) is int)):
            records.append({"at": at, "window": window, "used_percent": float(used), "resets_at": reset,
                            "source": "claude_statusline"})
    return records


def _notice_samples(notices: tuple[list, str | None] | None) -> list[dict]:
    """Official percents carried by Nerelan's own Claude runs (rate_limit_event utilization)."""
    from .quota_forecast import parse_time
    if not notices:
        return []
    items, observed = notices
    at = parse_time(observed)
    samples = []
    for notice in items if at is not None else ():
        if not isinstance(notice, Mapping):
            continue
        window = _CLAUDE_WINDOWS.get(notice.get("window"))
        utilization, reset = notice.get("utilization"), notice.get("resets_at")
        if window and type(utilization) in (int, float) and 0 <= utilization <= 1:
            samples.append({"at": int(at), "window": window, "used_percent": utilization * 100,
                            "resets_at": reset if type(reset) is int else None, "source": "claude_rate_limit_event"})
    return samples


def _claude_window(name: str, samples: list[dict], history: Any, hit_times: list[float],
                   now: float) -> dict[str, Any] | None:
    from .quota_forecast import (calibrate, capacity_from_hits, estimated_window, iso, rolling_blocks,
                                 usage_between)
    length = CLAUDE_WINDOW_SECONDS[name]
    capacity = calibrate(samples, history.usage, length=length)
    capacity_source = "official_calibration" if capacity else None
    if capacity is None and name == "five_hour":
        capacity = capacity_from_hits(history.usage, hit_times)
        capacity_source = "limit_hits" if capacity else None
        if capacity:
            # Limits do not weigh token kinds exactly like list prices: in a cache-read-heavy
            # window (Owner's data, 2026-10-14) the real capacity was ~1.4x the hit-based figure.
            # Until official readings calibrate it, the optimistic end allows for that.
            capacity = dict(capacity, high=round(capacity["high"] * HIT_CAPACITY_SPREAD, 4))
    latest = samples[-1] if samples else None
    if latest and latest["resets_at"] and latest["resets_at"] > now:
        reset = latest["resets_at"]
        window: dict[str, Any] = {"window": name, "resets_at": iso(reset), "resets_at_estimated": False,
                                  "reset_passed": False, "status": None, "as_of": iso(latest["at"]),
                                  "official_source": latest["source"], "capacity_source": capacity_source}
        if now - latest["at"] <= FRESH_SECONDS or capacity is None:
            window |= {"basis": "official_percent", "used_percent": latest["used_percent"]}
            if capacity:
                left = (100 - latest["used_percent"]) / 100
                window["capacity_units"] = capacity
                window["remaining_units_range"] = [round(left * capacity["low"], 4), round(left * capacity["high"], 4)]
            return window
        # The official figure is older: add what was used since, at the calibrated capacity.
        added = usage_between(history.usage, latest["at"], now)
        clamp = lambda v: round(min(max(v, 0.0), 100.0), 1)  # noqa: E731
        base = latest["used_percent"]
        mid, low, high = (clamp(base + added / capacity[k] * 100) for k in ("mid", "high", "low"))
        return window | {"basis": "estimated", "used_percent": mid, "used_percent_range": [low, high],
                         "capacity_units": capacity, "used_units": round(added, 4),
                         "anchor": {"used_percent": base, "at": iso(latest["at"])},
                         "remaining_units_range": [round(max((100 - high) / 100 * capacity["low"], 0.0), 4),
                                                   round(max((100 - low) / 100 * capacity["high"], 0.0), 4)]}
    if name == "weekly":
        if not latest or not latest["resets_at"]:
            return None
        reset = latest["resets_at"]
        while reset <= now:  # the weekly window renews on a fixed schedule
            reset += length
        used_units = usage_between(history.usage, reset - length, now)
        if capacity:
            return estimated_window("weekly", used_units=used_units, capacity=capacity, resets_at=reset, now=now) | {
                "resets_at_estimated": False, "capacity_source": capacity_source}
        return {"window": "weekly", "basis": "unknown", "used_percent": None, "used_units": round(used_units, 4),
                "resets_at": iso(reset), "resets_at_estimated": False, "reset_passed": False,
                "reason": "capacity_unknown"}
    blocks = rolling_blocks(history.usage)
    current = blocks[-1] if blocks and now < blocks[-1]["end"] else None
    if current and any(current["start"] <= hit < current["end"] for hit in hit_times):
        return {"window": "five_hour", "basis": "estimated", "used_percent": 100.0,
                "used_percent_range": [100.0, 100.0], "availability": "limit_reached",
                "resets_at": iso(current["end"]), "resets_at_estimated": True, "reset_passed": False,
                "remaining_units_range": [0.0, 0.0], "used_units": round(current["units"], 4),
                "capacity_source": capacity_source}
    if capacity:
        # No usage in the last five hours: the next request opens a fresh window.
        return estimated_window("five_hour", used_units=current["units"] if current else 0.0, capacity=capacity,
                                resets_at=current["end"] if current else None, now=now) | {
            "resets_at_estimated": True, "capacity_source": capacity_source}
    if current:
        return {"window": "five_hour", "basis": "unknown", "used_percent": None,
                "used_units": round(current["units"], 4), "resets_at": iso(current["end"]),
                "resets_at_estimated": True, "reset_passed": False, "reason": "capacity_unknown_no_limit_hit_yet"}
    return None


def claude_quota(notices: tuple[list, str | None] | None, config_dir: str | os.PathLike[str] | None = None,
                 *, now: float | None = None, statusline_path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Claude's 5-hour and weekly windows, on the best basis available.

    Official percents come from the Nerelan status line and from Nerelan's own Claude runs.
    A fresh one is shown as is; an older one is carried forward with the usage since, at a
    capacity calibrated from earlier official readings (local usage in the window divided by
    its percent). Without official readings, actual limit hits calibrate the 5-hour window.
    """
    from .quota_forecast import availability, parse_time
    from .quota_history import read_claude_history
    now = time.time() if now is None else now
    history = read_claude_history(config_dir, now=now)
    # Only what had happened by ``now`` (logs may hold later lines when ``now`` is in the past).
    history.usage = [event for event in history.usage if event.at <= now]
    history.hits = [hit for hit in history.hits if hit["at"] <= now]
    samples = sorted((s for s in read_statusline_records(statusline_path, now=now) + _notice_samples(notices)
                      if s["at"] <= now), key=lambda sample: sample["at"])
    hit_times = [hit["at"] for hit in history.hits]
    windows = []
    for name in CLAUDE_WINDOW_SECONDS:
        window = _claude_window(name, [s for s in samples if s["window"] == name], history, hit_times, now)
        if window is not None:
            windows.append(window)
    # Notices that only state availability (or name another window) are kept beside the numbers.
    official = claude_rate_limits(*notices, now=now) if notices else unknown("no_rate_limits_reported")
    hits = list(history.hits)
    for notice in official["windows"]:
        if notice["status"] == "rejected":
            hits.append({"at": parse_time(official.get("observed_at")) or now, "window": notice["window"],
                         "source": "claude_rate_limit_event"})
        if notice["reset_passed"]:
            continue
        same = next((w for w in windows if w["window"] == notice["window"]), None)
        if same is None and notice["used_percent"] is None:
            windows.append(notice | {"basis": "official_status", "availability": availability(notice["status"])})
        elif same is not None and same.get("availability") != "limit_reached":
            same["status"] = notice["status"]
            same["availability"] = availability(notice["status"])
    if not windows:
        return unknown("no_claude_quota_signal")
    is_official = any(w["basis"].startswith("official") or w.get("anchor") for w in windows)
    sources = sorted({s["source"] for s in samples})
    return {"state": "OBSERVED", "provenance": "OFFICIAL_VIA_CLI" if is_official else "ESTIMATED_FROM_HISTORY",
            "source": sources[-1] if sources else "claude_session_log",
            "observed_at": iso_or_none(samples[-1]["at"]) if samples else official.get("observed_at"),
            "windows": windows, "limit_hits": _hits_public(hits), "usage_scope": "this_machine"}


def iso_or_none(epoch: float | None) -> str | None:
    from .quota_forecast import iso
    return iso(epoch)


# ---- Magpie observation: official numbers first, local CLI logs as fallback ----

# Magpie account `provider` strings are not the executor provider ids the guard keys by.
_MAGPIE_PROVIDER_KEYS = {
    "codex": "codex",
    "openai": "codex",
    "chatgpt": "codex",
    "claude-code": "claude-code",
    "claude_code": "claude-code",
    "anthropic": "claude-code",
    "claude": "claude-code",
}


def magpie_quota_windows(snapshot: Mapping[str, Any], *, now: float | None = None) -> dict[str, dict[str, Any]]:
    """Map a Magpie snapshot's fresh subscription accounts onto the guard's quota shape.

    Only ``FRESH`` accounts (already age-checked by :func:`parse_quotas` at <= 15 min)
    contribute; anything else is dropped so the caller can fall back to the local CLI
    source. The official ``used_percent``/``resets_at`` are kept verbatim, so a 100% 5h
    window drives ``switch`` and the account is held until its stated reset.

    One account is chosen per provider: the one with the least remaining headroom in its
    most constrained active window, matching the guard's per-window admission rule. Stale
    or unknown accounts, invalid windows, and windows whose stated reset has passed do not
    influence that choice. Ties are broken by sanitized ``account_ref``, then observation
    time and window content, so input order never decides the result. When no usable
    account exists the provider is omitted and the caller keeps its local fallback.
    """
    now = time.time() if now is None else now
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(snapshot, Mapping) or snapshot.get("status") != "available":
        return result
    candidates: dict[str, list[tuple[tuple[Any, ...], Mapping[str, Any], list[dict[str, Any]]]]] = {}
    for account in snapshot.get("accounts") or []:
        if not isinstance(account, Mapping) or account.get("state") != "FRESH":
            continue
        key = _MAGPIE_PROVIDER_KEYS.get(account.get("provider"))
        if key is None:
            continue
        windows = []
        for window in account.get("windows") or []:
            if not isinstance(window, Mapping) or window.get("unlimited") is True:
                continue  # an unlimited window never constrains admission
            used = window.get("used_percent")
            if type(used) not in (int, float) or not 0 <= used <= 100:
                continue
            resets_at = window.get("resets_at")
            reset = parse_iso_time(resets_at)
            if resets_at is not None and reset is None:
                continue  # a stated reset that cannot be read makes the window invalid
            windows.append({
                "window": window.get("name") if isinstance(window.get("name"), str) else "window",
                "basis": "official_percent",
                "used_percent": used,
                "resets_at": resets_at if isinstance(resets_at, str) else None,
                "reset_passed": bool(reset is not None and reset <= now),
                "status": None,
                "source": "magpie",
            })
        active = [window for window in windows if not window["reset_passed"]]
        if not active:
            continue
        headroom = min(100 - window["used_percent"] for window in active)
        ref = account.get("account_ref")
        observed = account.get("observed_at")
        signature = tuple(
            (window["window"], window["used_percent"], window["resets_at"] or "")
            for window in windows)
        order = (headroom, ref if isinstance(ref, str) and ref else "\uffff",
                 observed if isinstance(observed, str) else "", signature)
        candidates.setdefault(key, []).append((order, account, windows))
    for key, choices in candidates.items():
        _, account, windows = min(choices, key=lambda choice: choice[0])
        evidence: dict[str, Any] = {"state": "OBSERVED", "provenance": "EXTERNAL_MAGPIE", "source": "magpie",
                                    "observed_at": account.get("observed_at"), "windows": windows}
        ref = account.get("account_ref")
        if isinstance(ref, str) and ref:
            evidence["account_ref"] = ref
        result[key] = evidence
    return result


def parse_iso_time(value: Any) -> float | None:
    if not isinstance(value, str) or len(value) > 40:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None
