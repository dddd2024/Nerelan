"""Bounded, untrusted public Codex reset announcements; never account quota evidence.

The host scheduler owns polling, durable event deduplication, owner authorisation
and actual vendor quota refresh. This observer cannot create/dispatch a task.
"""

from __future__ import annotations

import json
import re
import threading
import time
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
MAX_ID_TIME_SKEW = timedelta(minutes=5)
MAX_FETCH_SECONDS = 5.0
X_EPOCH_MS = 1288834974657

_POST_ID = re.compile(r"[0-9]{10,25}\Z")
_RESET = re.compile(r"\breset\b", re.IGNORECASE)
_DONE = re.compile(
    r"\b(we have reset|we've reset|has been reset|have been reset|"
    r"reset has been processed|fully reset|reset is done|reset completed)\b",
    re.IGNORECASE,
)
# This is deliberately an allowlist, not a keyword/negation classifier.
# Only a small number of unambiguous complete Codex-wide reset statements can
# prompt a *read-only* account quota refresh. Every other sentence is advisory.
_UNAMBIGUOUS_GLOBAL_DONE = re.compile(
    r"(?:we (?:have|'ve) reset (?:the )?(?:usage )?limits for all codex users|"
    r"we (?:have|'ve) reset (?:all )?codex (?:usage )?limits for everyone|"
    r"global codex (?:usage )?(?:limits?|quotas?) reset (?:is )?(?:done|complete|completed))"
    r"[.!]?\Z",
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
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("non-UTC timestamp")
    return parsed


def _valid_post(entry: object, now: datetime) -> tuple[str, str, datetime] | None:
    """Check ID, immutable original permalink and X Snowflake creation time."""
    if not isinstance(entry, dict):
        return None
    identity, text, url = entry.get("id"), entry.get("text"), entry.get("url")
    if (not isinstance(identity, str) or not _POST_ID.fullmatch(identity)
            or not isinstance(text, str) or len(text) > 8000
            or not isinstance(url, str)
            or url != f"https://x.com/thsottiaux/status/{identity}"):
        return None
    try:
        when = _parse_time(entry.get("at"))
        snowflake_ms = (int(identity) >> 22) + X_EPOCH_MS
        created = datetime.fromtimestamp(snowflake_ms / 1000, timezone.utc)
    except (ValueError, TypeError, OverflowError, OSError):
        return None
    if (abs(when - created) > MAX_ID_TIME_SKEW
            or created > now + MAX_CLOCK_SKEW
            or now - created > MAX_POST_AGE):
        return None
    # The source may skew `at` inside tolerance; only the X Snowflake is
    # immutable enough to order replies and timestamp advisory events.
    return identity, text, created


def _global_codex_reset(text: str) -> bool:
    # Reject negations, exceptions, partial scope and trailing clauses by
    # requiring the entire message to match a narrow completion grammar.
    return bool(_UNAMBIGUOUS_GLOBAL_DONE.fullmatch(text.strip()))


def parse_feed(payload: object, *, now: datetime | None = None) -> ResetObservation:
    """Return advisory classifications only; ignore invalid/replayed mirror data."""
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

    # Parent must pass all the same checks as the child. Validate before indexing,
    # so malformed mirror IDs (e.g. a list) can never raise an exception.
    valid: dict[str, tuple[dict, str, datetime]] = {}
    for entry in tweets:
        record = _valid_post(entry, now)
        if record is not None:
            identity, text, when = record
            valid.setdefault(identity, (entry, text, when))

    events: list[ResetEvent] = []
    for identity, (entry, text, when) in valid.items():
        kind = None
        if entry.get("kind") == "banked" and re.search(r"\bbanked\b", text, re.I):
            kind = "BANKED_ANNOUNCEMENT"
        elif entry.get("explicit_reset_claim") is True and _RESET.search(text):
            if _DONE.search(text):
                # Third-party labels cannot turn a personal/banked statement into
                # proof of a global Codex reset or clear a subscription limit.
                kind = ("RESET_REPORTED_COMPLETE" if _global_codex_reset(text)
                        else "RESET_SCOPE_UNVERIFIED")
            else:
                kind = "RESET_ANNOUNCEMENT"
        elif entry.get("kind") == "signal" and entry.get("reset_verification_candidate") is True:
            parent_id = entry.get("in_reply_to_tweet_id")
            parent = valid.get(parent_id) if isinstance(parent_id, str) else None
            if (parent is not None and parent[2] < when
                    and _RESET.search(parent[1])
                    and re.search(r"\blanding\b", text, re.I)):
                kind = "RESET_ANNOUNCEMENT"
        elif isinstance(entry.get("tease_classification"), dict):
            if entry["tease_classification"].get("teasing") is True:
                kind = "POSSIBLE_HINT"
        if kind is None:
            continue
        events.append(ResetEvent(
            event_id=f"tibo-x:{identity}",  # stable even if the mirror reclassifies a post
            kind=kind,
            source_url=f"https://x.com/thsottiaux/status/{identity}",
            published_at=when.isoformat().replace("+00:00", "Z"),
            excerpt=text[:240],
            action="REFRESH_QUOTA" if kind == "RESET_REPORTED_COMPLETE" else "PLAN_ONLY",
        ))
    return ResetObservation("FRESH", checked_at, tuple(events))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch_feed_worker(*, opener: Callable[..., Any] | None = None,
                       now: datetime | None = None) -> ResetObservation:
    """Internal HTTP worker; caller applies a hard wall-clock deadline."""
    request = urllib.request.Request(
        FEED_URL,
        headers={"Accept": "application/json", "User-Agent": "Nerelan-readonly-reset-observer/1"},
        method="GET",
    )
    deadline = time.monotonic() + MAX_FETCH_SECONDS
    try:
        handler = opener or urllib.request.build_opener(_NoRedirect()).open
        stream = handler(request, timeout=MAX_FETCH_SECONDS)
        with stream as response:
            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type.lower():
                return ResetObservation("UNKNOWN", None, (), "wrong_content_type")
            chunks: list[bytes] = []
            total = 0
            while total <= MAX_FEED_BYTES:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return ResetObservation("UNKNOWN", None, (), "fetch_deadline_exceeded")
                # HTTPResponse.read1() makes one raw read per iteration; set its
                # socket timeout to the actual *remaining total* time. Without
                # socket control a real response cannot claim a hard deadline.
                socket = getattr(
                    getattr(getattr(response, "fp", None), "raw", None), "_sock", None
                )
                if opener is None and socket is None:
                    return ResetObservation("UNKNOWN", None, (), "socket_deadline_unavailable")
                if socket is not None:
                    socket.settimeout(remaining)
                chunk = response.read1(min(8192, MAX_FEED_BYTES - total + 1))
                if time.monotonic() > deadline:
                    return ResetObservation("UNKNOWN", None, (), "fetch_deadline_exceeded")
                if not chunk:
                    break
                total += len(chunk)
                chunks.append(chunk)
        if total > MAX_FEED_BYTES:
            return ResetObservation("UNKNOWN", None, (), "response_too_large")
        return parse_feed(json.loads(b"".join(chunks)), now=now)
    except (OSError, URLError, HTTPError, ValueError, TypeError):
        return ResetObservation("UNKNOWN", None, (), "feed_unavailable_or_invalid")


# A DNS resolver can ignore socket timeouts. Keep at most one daemon worker
# outstanding, so no host caller waits past the 5s deadline and repeated
# polling cannot accumulate blocked DNS threads.
_FETCH_LOCK = threading.Lock()
_FETCH_WORKER: threading.Thread | None = None


def fetch_feed(*, opener: Callable[..., Any] | None = None,
               now: datetime | None = None) -> ResetObservation:
    """Bound the full HTTP operation including DNS/connection establishment.

    A stuck DNS worker may finish later, but its result is discarded and a
    second worker will not start until it exits. No task or quota is mutated.
    """
    global _FETCH_WORKER
    completed = threading.Event()
    result = [ResetObservation("UNKNOWN", None, (), "worker_not_completed")]

    def work() -> None:
        try:
            result[0] = _fetch_feed_worker(opener=opener, now=now)
        except Exception:
            result[0] = ResetObservation("UNKNOWN", None, (), "feed_unavailable_or_invalid")
        finally:
            completed.set()

    with _FETCH_LOCK:
        if _FETCH_WORKER is not None and _FETCH_WORKER.is_alive():
            return ResetObservation("UNKNOWN", None, (), "previous_fetch_still_running")
        worker = threading.Thread(target=work, name="nerelan-reset-feed", daemon=True)
        _FETCH_WORKER = worker
        worker.start()
    if not completed.wait(MAX_FETCH_SECONDS):
        return ResetObservation("UNKNOWN", None, (), "fetch_deadline_exceeded")
    return result[0]
