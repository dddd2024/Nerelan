"""Untrusted public Codex reset announcements; never an account quota grant.

The caller/scheduler owns polling, persistent deduplication, authorisation and
vendor quota refresh. This observer only returns conservative advisory events.
"""

from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError

FEED_URL = "https://codex-reset.com/api/feed"
MAX_FEED_BYTES = 262_144
MAX_FEED_AGE = timedelta(hours=1)
MAX_POST_AGE = timedelta(days=7)
MAX_CLOCK_SKEW = timedelta(minutes=5)
_POST_ID = re.compile(r"[0-9]{10,25}\Z")
_RESET = re.compile(r"\breset\b", re.IGNORECASE)
_DONE = re.compile(
    r"\b(we have reset|has been reset|have been reset|"
    r"reset has been processed|fully reset|reset is done|reset completed)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ResetEvent:
    event_id: str
    kind: str
    source_url: str
    published_at: str
    excerpt: str
    action: str  # PLAN_ONLY or REFRESH_QUOTA; never DISPATCH


@dataclass(frozen=True)
class ResetObservation:
    status: str  # FRESH, STALE, UNKNOWN
    checked_at: str | None
    events: tuple[ResetEvent, ...]
    reason: str | None = None


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be UTC ISO-8601")
    value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("non-UTC timestamp")
    return parsed


def parse_feed(payload: object, *, now: datetime | None = None) -> ResetObservation:
    """Validate the public feed and return *advisory* events with original links.

    An unverified forecast, unrelated post, or third-party classifier is not a
    proof that the current account has capacity. No dispatch action is returned.
    """
    now = now or datetime.now(timezone.utc)
    if now.utcoffset() != timedelta(0):
        raise ValueError("now must be UTC")
    if not isinstance(payload, dict) or payload.get("version") != 1:
        return ResetObservation("UNKNOWN", None, (), "unsupported_feed_schema")
    if payload.get("source") != "x-api" or payload.get("stale") is not False:
        return ResetObservation("UNKNOWN", None, (), "source_unverified_or_stale")
    try:
        checked = _parse_time(payload.get("fetched_at"))
    except (TypeError, ValueError):
        return ResetObservation("UNKNOWN", None, (), "invalid_checked_at")
    checked_at = checked.isoformat().replace("+00:00", "Z")
    if checked > now + MAX_CLOCK_SKEW or now - checked > MAX_FEED_AGE:
        return ResetObservation("STALE", checked_at, (), "feed_age_out_of_bounds")
    tweets = payload.get("tweets")
    if not isinstance(tweets, list) or len(tweets) > 200:
        return ResetObservation("UNKNOWN", checked_at, (), "invalid_tweet_list")
    by_id = {t.get("id"): t for t in tweets if isinstance(t, dict)}
    events: list[ResetEvent] = []
    seen: set[str] = set()
    for entry in tweets:
        if not isinstance(entry, dict):
            continue
        identity, text, url = entry.get("id"), entry.get("text"), entry.get("url")
        if (not isinstance(identity, str) or not _POST_ID.fullmatch(identity)
                or not isinstance(text, str) or not isinstance(url, str)
                or len(text) > 8000
                or url != f"https://x.com/thsottiaux/status/{identity}"):
            continue
        try:
            when = _parse_time(entry.get("at"))
        except (TypeError, ValueError):
            continue
        if when > now + MAX_CLOCK_SKEW or now - when > MAX_POST_AGE:
            continue
        kind = None
        if entry.get("kind") == "banked" and re.search(r"\bbanked\b", text, re.I):
            kind = "BANKED_ANNOUNCEMENT"
        elif entry.get("explicit_reset_claim") is True and _RESET.search(text):
            kind = "RESET_REPORTED_COMPLETE" if _DONE.search(text) else "RESET_ANNOUNCEMENT"
        elif entry.get("kind") == "signal" and entry.get("reset_verification_candidate") is True:
            parent = by_id.get(entry.get("in_reply_to_tweet_id"))
            if (isinstance(parent, dict) and _RESET.search(str(parent.get("text", "")))
                    and re.search(r"\blanding\b", text, re.I)):
                kind = "RESET_ANNOUNCEMENT"
        elif isinstance(entry.get("tease_classification"), dict):
            if entry["tease_classification"].get("teasing") is True:
                kind = "POSSIBLE_HINT"
        if kind is None:
            continue
        event_id = f"tibo-x:{identity}:{kind}"
        if event_id in seen:
            continue
        seen.add(event_id)
        events.append(ResetEvent(
            event_id=event_id, kind=kind, source_url=url,
            published_at=when.isoformat().replace("+00:00", "Z"),
            excerpt=text[:240],
            action="REFRESH_QUOTA" if kind == "RESET_REPORTED_COMPLETE" else "PLAN_ONLY",
        ))
    return ResetObservation("FRESH", checked_at, tuple(events))


def fetch_feed(*, opener: Callable[..., Any] | None = None,
               now: datetime | None = None) -> ResetObservation:
    """Bounded unauthenticated public GET; no X cookies or model calls."""
    request = urllib.request.Request(
        FEED_URL,
        headers={"Accept": "application/json", "User-Agent": "Nerelan-readonly-reset-observer/1"},
        method="GET",
    )
    try:
        stream = (opener or urllib.request.urlopen)(request, timeout=5)
        with stream as response:
            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type.lower():
                return ResetObservation("UNKNOWN", None, (), "wrong_content_type")
            raw = response.read(MAX_FEED_BYTES + 1)
        if len(raw) > MAX_FEED_BYTES:
            return ResetObservation("UNKNOWN", None, (), "response_too_large")
        return parse_feed(json.loads(raw), now=now)
    except (OSError, URLError, HTTPError, ValueError, TypeError, json.JSONDecodeError):
        return ResetObservation("UNKNOWN", None, (), "feed_unavailable_or_invalid")
