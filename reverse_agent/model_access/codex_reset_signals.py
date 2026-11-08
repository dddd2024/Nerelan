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
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any, Callable, Sequence
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
# Tibo's own wording for a same-day global reset ("Just kidding, today is a reset.").
_TODAY_RESET = re.compile(r"\btoday is (?:a|the) (?:global )?reset\b", re.IGNORECASE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# Allowlist, not a hedge list: only these openings may precede the phrase. Real
# October posts: "Just kidding, today is a reset." and "But today is a reset."
# Anything else ("I heard", "Some say", "They think") is not Tibo announcing.
_ALLOWED_LEAD = re.compile(
    r"(?:(?:but|and|so|ok(?:ay)?|alright|yes|update|just kidding)[,:]?\s+)?\Z", re.IGNORECASE)
# Any of these in any other sentence of the post voids it: a miss costs only the
# drain, a false hit spends the week.
_VOIDING = re.compile(
    r"\?|\.\.|…|\b(?:not|no|nope|never|nah|jk|kidding|joke|joking|fools?|psych|sike|fake|lies|"
    r"or is it|ha(?:ha)+|lol|lmao|"
    r"rofl|if|what|who|whether|maybe|perhaps|rumou?r|would|could|should|might|wish|pretend|suppose|"
    r"unless|wonder|heard|apparently|allegedly)\b",
    re.IGNORECASE)


def plain_statement(text: str) -> bool:
    """No question, ellipsis, negation, hedge, hearsay or joke marker anywhere."""
    return not _VOIDING.search(text)


def announces_today(text: str) -> bool:
    """A plain first-hand statement that today is a reset, and nothing that undoes it.

    The phrase's sentence must be exactly an allowed opening ("", "But", "So",
    "Just kidding,", ...) plus the phrase, closed by one "." or "!" or by the end
    of the text. Every later sentence must be plain (``plain_statement``), so
    "Today is a reset... NOT", "Today is a reset. Not.", "... April fools.",
    "... Haha" and "... Or is it?" are refused, as is "I heard today is a reset."
    Real October posts that pass: "Just kidding, today is a reset." and "But today
    is a reset." A miss costs only the drain; a false hit spends the week.
    """
    sentences = [part for part in _SENTENCE_END.split(text.strip()) if part]
    for index, sentence in enumerate(sentences):
        match = _TODAY_RESET.search(sentence)
        if not match:
            continue
        lead, tail = sentence[:match.start()], sentence[match.end():]
        if not _ALLOWED_LEAD.match(lead) or tail not in {"", ".", "!"}:
            continue
        # Earlier sentences are context ("Wonder what happens the remaining seven
        # days. But today is a reset."); only later ones can undo the statement.
        if all(plain_statement(later) for later in sentences[index + 1:]):
            return True
    return False
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
class Announcement:
    """A global reset the feed's own classifier recorded, with when it should land."""
    event_id: str
    announced_at: str
    expected_at: str | None  # from a time stated in the announcement or its replies
    source_url: str


@dataclass(frozen=True)
class ResetObservation:
    status: str  # FRESH, STALE, UNKNOWN
    checked_at: str | None
    events: tuple[ResetEvent, ...]
    reason: str | None = None
    announcements: tuple[Announcement, ...] = ()


# --- times stated in a post, read relative to the post that states them -------

class _USZone(tzinfo):
    """US daylight time without a tz database (Windows lacks one unless tzdata is installed).

    DST runs from 02:00 local standard time on the second Sunday of March to 02:00
    local daylight time on the first Sunday of November, as since 2007.
    """

    def __init__(self, standard_hours: int, name: str) -> None:
        self._standard = timedelta(hours=standard_hours)
        self._name = name

    @staticmethod
    def _sunday(year: int, month: int, nth: int) -> datetime:
        first = datetime(year, month, 1)
        return first + timedelta(days=(6 - first.weekday()) % 7 + 7 * (nth - 1))

    def _dst_utc(self, year: int) -> tuple[datetime, datetime]:
        start = self._sunday(year, 3, 2) + timedelta(hours=2) - self._standard
        end = self._sunday(year, 11, 1) + timedelta(hours=1) - self._standard
        return start, end

    def utcoffset(self, moment: datetime | None) -> timedelta:
        return self._standard + self.dst(moment)

    def dst(self, moment: datetime | None) -> timedelta:
        if moment is None:
            return timedelta(0)
        naive = moment.replace(tzinfo=None)
        start, end = self._dst_utc(naive.year)
        as_daylight = start <= naive - self._standard - timedelta(hours=1) < end
        as_standard = start <= naive - self._standard < end
        if as_daylight == as_standard:
            return timedelta(hours=1) if as_daylight else timedelta(0)
        # The repeated hour in November (or the skipped one in March): PEP 495,
        # fold=0 is the first occurrence, which is daylight time in November.
        if as_daylight:
            return timedelta(0) if moment.fold else timedelta(hours=1)
        return timedelta(0)

    def fromutc(self, moment: datetime) -> datetime:
        naive = moment.replace(tzinfo=None)
        start, end = self._dst_utc(naive.year)
        daylight = start <= naive < end
        local = naive + self._standard + (timedelta(hours=1) if daylight else timedelta(0))
        # The hour after daylight time ends repeats on the wall clock: mark it fold=1.
        repeated = not daylight and end <= naive < end + timedelta(hours=1)
        return local.replace(tzinfo=self, fold=int(repeated))

    def tzname(self, moment: datetime | None) -> str:
        return self._name


try:
    from zoneinfo import ZoneInfo
    _PACIFIC, _EASTERN = ZoneInfo("America/Los_Angeles"), ZoneInfo("America/New_York")
except Exception:  # noqa: BLE001 - no tz database: the same US rules, computed here
    _PACIFIC, _EASTERN = _USZone(-8, "US/Pacific"), _USZone(-5, "US/Eastern")
_ZONES = {"pst": _PACIFIC, "pdt": _PACIFIC, "pt": _PACIFIC, "pacific": _PACIFIC,
          "est": _EASTERN, "edt": _EASTERN, "et": _EASTERN, "utc": timezone.utc, "gmt": timezone.utc}
_ZONE = r"(pst|pdt|pt|pacific|est|edt|et|utc|gmt)"
_MIDNIGHT = re.compile(r"\b(?:by|at|before|around)\s+midnight\s+" + _ZONE + r"\b", re.I)
_CLOCK = re.compile(r"\b(?:by|at|before|around)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*" + _ZONE + r"\b", re.I)
_RELATIVE = re.compile(r"\bin\s+(?:the\s+next\s+)?(\d{1,2}|an?|one|two|three)\s+(hours?|hrs?|minutes?|mins?)\b", re.I)
_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3}
MAX_STATED_AHEAD = timedelta(hours=72)


def _next_at(posted: datetime, zone: Any, hour: int, minute: int) -> datetime:
    local = posted.astimezone(zone)
    target = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= local:
        target = (local + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return target.astimezone(timezone.utc)


def stated_time(text: str, posted: datetime) -> datetime | None:
    """A reset time the post states ("by midnight PST", "at 10am PT", "in 2 hours").

    Read only when unambiguous and within 72 hours after the post; anything else
    is None, and the caller falls back to the Owner's assumed window.
    """
    found = None
    if match := _MIDNIGHT.search(text):
        found = _next_at(posted, _ZONES[match.group(1).lower()], 0, 0)
    elif (match := _CLOCK.search(text)) and (match.group(3) or match.group(2)):
        hour, minute = int(match.group(1)), int(match.group(2) or 0)
        meridian = (match.group(3) or "").lower()
        if meridian:
            if not 1 <= hour <= 12:
                return None
            hour = hour % 12 + (12 if meridian == "pm" else 0)
        if hour <= 23 and minute <= 59:
            found = _next_at(posted, _ZONES[match.group(4).lower()], hour, minute)
    elif match := _RELATIVE.search(text):
        count = _WORDS.get(match.group(1).lower()) or int(match.group(1))
        unit = timedelta(hours=1) if match.group(2).lower().startswith("h") else timedelta(minutes=1)
        found = posted + count * unit
    if found is None or not posted < found <= posted + MAX_STATED_AHEAD:
        return None
    return found


_ANNOUNCEMENT_GROUP = timedelta(hours=12)


def _site_announcements(events: object, now: datetime,
                        posts: Sequence[tuple[datetime, str, str, bool, frozenset[str]]] = ()
                        ) -> tuple[Announcement, ...]:
    """The freshest global reset announcement, from the feed's events and Tibo's posts.

    Anchors are the feed's own reset events and posts already classified as an
    announcement. Anchors within 12 hours of the newest one are one announcement.
    A reply joins it only when it replies into an anchor's thread: the time is
    often stated there ("Lands by midnight PST.") rather than in the announcement.
    Each post's time is its X Snowflake creation time, never a mirror's claim.
    """
    found: list[tuple[datetime, str, str, str]] = []
    for event in events[:500] if isinstance(events, list) else ():
        if not isinstance(event, dict):
            continue
        url, summary = event.get("url"), event.get("summary")
        if (event.get("type") != "reset" or event.get("scope") != "global"
                or event.get("reset_kind") == "banked" or event.get("preview") is not False
                or event.get("confidence") not in {"medium", "high"}
                or event.get("announcement_state") == "none"
                or not isinstance(url, str) or not isinstance(summary, str) or len(summary) > 8000
                or summary.rstrip().endswith("?")):
            continue
        identity = url.rsplit("/", 1)[-1]
        if not _POST_ID.fullmatch(identity) or url != f"https://x.com/thsottiaux/status/{identity}":
            continue
        try:
            claimed = _parse_time(event.get("announced_at"))
            posted = datetime.fromtimestamp(((int(identity) >> 22) + X_EPOCH_MS) / 1000, timezone.utc)
        except (TypeError, ValueError, OverflowError, OSError):
            continue
        # A mirror may record when it noticed a post, never before the post existed.
        if claimed < posted - MAX_ID_TIME_SKEW:
            continue
        if posted > now + MAX_CLOCK_SKEW or now - posted > MAX_POST_AGE:
            continue
        found.append((posted, identity, summary, url))
    for posted, identity, text, announces, _ in posts:
        if announces:
            found.append((posted, identity, text, f"https://x.com/thsottiaux/status/{identity}"))
    if not found:
        return ()
    newest = max(posted for posted, *_ in found)
    group = sorted(item for item in found if newest - item[0] <= _ANNOUNCEMENT_GROUP)
    start = group[0][0]
    anchors = {identity for _, identity, _, _ in group}
    texts = [(posted, text) for posted, _, text, _ in group]
    # A reply's time counts only when the reply is a plain statement ("Lands by
    # midnight PST."), never a guess ("maybe by 10am PT?").
    texts += [(posted, text) for posted, _, text, _, thread in posts
              if thread & anchors and start <= posted <= start + _ANNOUNCEMENT_GROUP
              and plain_statement(text)]
    stated = sorted(t for t in (stated_time(text, posted) for posted, text in texts) if t and t > newest)
    if not stated and any(announces_today(text) for _, text in texts):
        # "today is a reset" with no time: today in Pacific time, where Tibo posts from.
        stated = [_next_at(start, _PACIFIC, 0, 0)]
    expected = stated[0].isoformat().replace("+00:00", "Z") if stated else None
    first = group[0]
    return (Announcement(f"tibo-x:{first[1]}", first[0].isoformat().replace("+00:00", "Z"), expected, first[3]),)


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
            # The strict completion allowlist is the *only* completion gate.
            # Broader _DONE matches do not imply a global/account reset.
            if _global_codex_reset(text):
                kind = "RESET_REPORTED_COMPLETE"
            elif _DONE.search(text):
                kind = "RESET_SCOPE_UNVERIFIED"
            elif entry.get("is_reply") is not True and plain_statement(text):
                kind = "RESET_ANNOUNCEMENT"
            else:
                # The mirror's flag alone is not enough: "No reset today" carries it too.
                kind = "POSSIBLE_HINT"
        elif (announces_today(text) and entry.get("is_reply") is not True
              and not (isinstance(entry.get("tease_classification"), dict)
                       and entry["tease_classification"].get("teasing") is True)):
            # The mirror does not flag this wording as an explicit claim, which
            # made every real announcement in October invisible.
            kind = "RESET_ANNOUNCEMENT"
        elif entry.get("kind") == "signal" and entry.get("reset_verification_candidate") is True:
            parent_id = entry.get("in_reply_to_tweet_id")
            parent = valid.get(parent_id) if isinstance(parent_id, str) else None
            # Parent and reply must both be plain statements:
            # "Is today a reset? who knows" / "landing soon? lol" are not.
            if (parent is not None and parent[2] < when
                    and parent[0].get("is_reply") is not True
                    and _RESET.search(parent[1]) and plain_statement(parent[1])
                    and re.search(r"\blanding\b", text, re.I) and plain_statement(text)):
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
    announcing = {event.event_id for event in events if event.kind == "RESET_ANNOUNCEMENT"}
    def thread(entry: dict) -> frozenset[str]:
        """Posts this one replies into; empty for an original post."""
        if entry.get("is_reply") is not True:
            return frozenset()
        return frozenset(str(entry.get(key)) for key in ("in_reply_to_tweet_id", "conversation_id")
                         if isinstance(entry.get(key), str) and _POST_ID.fullmatch(entry[key]))

    posts = [(when, identity, text, f"tibo-x:{identity}" in announcing, thread(entry))
             for identity, (entry, text, when) in valid.items()]
    return ResetObservation("FRESH", checked_at, tuple(events),
                            announcements=_site_announcements(payload.get("events"), now, posts))


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
                # Tighten the per-read timeout to the remaining total when the
                # socket is reachable. When it is not (CPython 3.13 no longer
                # exposes it here), fetch_feed's outer wall-clock wait still
                # bounds the caller, so the read proceeds instead of giving up.
                socket = getattr(
                    getattr(getattr(response, "fp", None), "raw", None), "_sock", None
                )
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


# Owner rule 2026-11-07: an announced Codex reset lands within a day, so treat an
# announcement as a reset expected this long after it was posted.
DEFAULT_ASSUMED_RESET_WITHIN = timedelta(hours=24)


def routing_signal(observation: ResetObservation, *, now: datetime,
                   within: timedelta = DEFAULT_ASSUMED_RESET_WITHIN) -> dict[str, Any]:
    """Translate an observation into the router's reset signal.

    The feed gives no reset time. A fresh, validated announcement is read as a
    reset expected ``within`` its post, which lets the router drain Codex to its
    reset buffer before then. A reported completion asks for a quota re-read.
    Anything else is UNKNOWN, which the router treats as no announcement.
    """
    if observation.status != "FRESH":
        return {"state": "STALE" if observation.status == "STALE" else "UNKNOWN",
                "reason": observation.reason}
    def posted(event: ResetEvent) -> datetime:
        return _parse_time(event.published_at)
    # (posted, expected, assumed, id, url) for every announcement either source holds.
    # parse_feed folds announcing posts into `announcements` together with any
    # time a reply states; the raw events are only a fallback when it has none.
    candidates = [] if observation.announcements else [
        (posted(e), posted(e) + within, True, e.event_id, e.source_url)
        for e in observation.events if e.kind == "RESET_ANNOUNCEMENT"]
    for item in observation.announcements:
        announced_at = _parse_time(item.announced_at)
        stated = _parse_time(item.expected_at) if item.expected_at else None
        candidates.append((announced_at, stated or announced_at + within, stated is None,
                           item.event_id, item.source_url))
    completed = [e for e in observation.events if e.action == "REFRESH_QUOTA"]
    latest_done = max(completed, key=posted, default=None)
    latest = max(candidates, key=lambda c: c[0], default=None)
    if latest_done is not None and (latest is None or posted(latest_done) >= latest[0]):
        return {"state": "REFRESH_QUOTA", "validated": True, "scope": "global", "kind": "global_reset",
                "expected_reset_at": latest_done.published_at, "announcement_id": latest_done.event_id,
                "source_url": latest_done.source_url}
    if latest is not None and now < latest[1]:
        return {"state": "PLAN_ONLY", "validated": True, "scope": "global", "kind": "global_reset",
                "expected_reset_at": latest[1].isoformat().replace("+00:00", "Z"),
                "announcement_id": latest[3], "source_url": latest[4], "assumed": latest[2],
                "announced_at": latest[0].isoformat().replace("+00:00", "Z")}
    return {"state": "UNKNOWN", "reason": "no_current_announcement"}


class CodexResetSignalReader:
    """Cached, non-blocking reader for the routing path.

    Routing never waits on the network: a call returns the last translation and,
    when it is older than ``poll_seconds``, starts one background refresh.
    """

    def __init__(self, *, poll_seconds: float = 900.0,
                 within: timedelta = DEFAULT_ASSUMED_RESET_WITHIN,
                 fetch: Callable[[], ResetObservation] | None = None,
                 clock: Callable[[], float] = time.time) -> None:
        self._poll_seconds = poll_seconds
        self._within = within
        self._fetch = fetch or fetch_feed
        self._clock = clock
        self._lock = threading.Lock()
        self._observation = ResetObservation("UNKNOWN", None, (), "not_yet_read")
        self._read_at: float | None = None
        self._refreshing = False

    def _refresh(self) -> None:
        try:
            observation = self._fetch()
        except Exception:  # noqa: BLE001 - an advisory source never breaks routing
            observation = ResetObservation("UNKNOWN", None, (), "feed_unavailable_or_invalid")
        with self._lock:
            self._observation, self._read_at, self._refreshing = observation, self._clock(), False

    def __call__(self) -> dict[str, Any]:
        with self._lock:
            due = self._read_at is None or self._clock() - self._read_at >= self._poll_seconds
            if due and not self._refreshing:
                self._refreshing = True
                threading.Thread(target=self._refresh, name="nerelan-codex-reset", daemon=True).start()
            observation = self._observation
        now = datetime.fromtimestamp(self._clock(), timezone.utc)
        return routing_signal(observation, now=now, within=self._within)


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
