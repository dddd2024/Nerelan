"""Read-only Claude subscription reset awareness from a public, untrusted source.

None of the events authorizes model execution or proves *account* availability.
Source: https://clauderesets.com/api/docs (third party; not Anthropic).
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

STATUS_URL = "https://clauderesets.com/api/v1/status"
MAX_BODY = 262_144
MAX_FETCH_SECONDS = 5.0
MAX_FEED_AGE = timedelta(hours=1)
MAX_RESET_AGE = timedelta(days=7)
MAX_CLOCK_SKEW = timedelta(minutes=5)
MIN_POLL_SECONDS = 1800
DEFAULT_POLL_SECONDS = 3600
_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9-]{1,110}\Z")
_PLANS = frozenset({"pro", "max", "team", "free", "enterprise"})
_WINDOWS = frozenset({"five_hour", "weekly", "unspecified"})
_HANDLES = frozenset({"ClaudeDevs", "lydiahallie", "alexalbert__", "AnthropicAI", "claudeai"})
_X_POST = re.compile(r"https://x\.com/([A-Za-z0-9_]+)/status/([0-9]{15,25})\Z")
_X_EPOCH_MS = 1288834974657
_NETWORK_LOCK = threading.Lock()
_NETWORK_WORKER: threading.Thread | None = None


@dataclass(frozen=True)
class ClaudeResetEvent:
    event_id: str
    revision: int
    kind: str
    action: str  # PLAN_ONLY, REFRESH_QUOTA, CLAIM_MANUALLY, or INVALIDATE_HINT
    published_at: str | None
    source_url: str
    evidence_url: str
    plans: tuple[str, ...]
    windows: tuple[str, ...]
    expires_on: str | None


@dataclass(frozen=True)
class ClaudeResetObservation:
    status: str  # FRESH, STALE, UNKNOWN
    checked_at: str | None
    editorial_reviewed_at: str | None
    events: tuple[ClaudeResetEvent, ...]
    reason: str | None = None


def _utc(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("expected UTC Z timestamp")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("non-UTC timestamp")
    return parsed


def _source_url(sources: object) -> str | None:
    if not isinstance(sources, list) or len(sources) > 20:
        return None
    for source in sources:
        if not isinstance(source, dict) or source.get("role") != "original":
            continue
        url = source.get("url")
        if not isinstance(url, str) or len(url) > 400:
            continue
        match = _X_POST.fullmatch(url)
        if match and match.group(1) in _HANDLES:
            return url
        if source.get("kind") == "web_page":
            parsed = urlparse(url)
            if (parsed.scheme == "https" and parsed.hostname in {"www.anthropic.com", "anthropic.com", "claude.com"}
                    and not parsed.username and not parsed.password and parsed.port is None):
                return url
    return None


def _event(item: object, *, slot: str, now: datetime) -> ClaudeResetEvent | None:
    if not isinstance(item, dict):
        return None
    identity, status, kind = item.get("id"), item.get("event_status"), item.get("kind")
    revision = item.get("revision")
    if not isinstance(identity, str) or not _ID.fullmatch(identity):
        return None
    if type(revision) is not int or not (1 <= revision <= 10000):
        return None
    if kind not in ("usage_reset", "credit"):
        return None
    if status not in ("confirmed", "announced", "retracted", "cancelled"):
        return None
    if item.get("allocation") != "subscription_usage":
        return None
    evidence_url = f"https://clauderesets.com/resets/{identity}"
    if item.get("url") != evidence_url:
        return None
    source_url = _source_url(item.get("sources"))
    if source_url is None:
        return None
    audience = item.get("audience")
    if not isinstance(audience, dict) or audience.get("scope") not in ("broad", "limited"):
        return None
    plans_raw = audience.get("plans")
    if not isinstance(plans_raw, list) or len(plans_raw) > 6:
        return None
    if any(not isinstance(p, str) or p not in _PLANS for p in plans_raw):
        return None
    # A known limited audience with no named plans is not a scheduling hint.
    if audience.get("scope") == "limited" and not plans_raw:
        return None
    windows_raw = item.get("windows")
    if not isinstance(windows_raw, list) or not windows_raw or len(windows_raw) > 3:
        return None
    if any(not isinstance(w, str) or w not in _WINDOWS for w in windows_raw):
        return None

    precise = item.get("time_precision")
    announced = item.get("announced_at")
    try:
        when = _utc(announced) if precise == "exact" else None
        if precise == "date" and isinstance(item.get("announced_on"), str):
            when = datetime.fromisoformat(item["announced_on"]).replace(tzinfo=timezone.utc)
        elif precise not in ("exact", "date"):
            return None
    except (ValueError, TypeError, OverflowError):
        return None
    if when is None or when > now + MAX_CLOCK_SKEW:
        return None
    published = when.isoformat().replace("+00:00", "Z")

    # A published X original should agree with its Snowflake timestamp.
    original_match = _X_POST.fullmatch(source_url)
    if original_match and precise == "exact":
        try:
            snowflake = datetime.fromtimestamp(
                ((int(original_match.group(2)) >> 22) + _X_EPOCH_MS) / 1000, timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None
        if abs(snowflake - when) > MAX_CLOCK_SKEW:
            return None

    expired = False
    expires = None
    if kind == "credit":
        offer = item.get("reset_offer")
        if not isinstance(offer, dict):
            return None
        expires = offer.get("expires_on")
        try:
            if not isinstance(expires, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", expires):
                return None
            expired = date.fromisoformat(expires) < now.date()
        except ValueError:
            return None

    if status in ("retracted", "cancelled"):
        action, event_kind = "INVALIDATE_HINT", "RETRACTED"
    elif kind == "credit":
        if expired:
            return None
        # Only a *confirmed* banked grant is actionable for the user. An
        # announced future offer is advisory, not something to redeem today.
        action = "CLAIM_MANUALLY" if status == "confirmed" else "PLAN_ONLY"
        event_kind = "BANKED_OFFER" if status == "confirmed" else "BANKED_ANNOUNCEMENT"
    elif slot == "announced_reset" or status == "announced":
        action, event_kind = "PLAN_ONLY", "RESET_ANNOUNCEMENT"
    elif status == "confirmed" and kind == "usage_reset":
        # An applied reset from weeks ago cannot be a new quota refresh hint.
        if now - when > MAX_RESET_AGE:
            return None
        action, event_kind = "REFRESH_QUOTA", "RESET_REPORTED_COMPLETE"
    else:
        return None
    if now - when > MAX_RESET_AGE and event_kind not in ("BANKED_OFFER", "RETRACTED"):
        return None
    return ClaudeResetEvent(
        event_id=f"claude-reset:{identity}",
        revision=revision, kind=event_kind, action=action,
        published_at=published, source_url=source_url, evidence_url=evidence_url,
        plans=tuple(plans_raw), windows=tuple(windows_raw), expires_on=expires,
    )


def parse_status(payload: object, *, now: datetime | None = None) -> ClaudeResetObservation:
    now = now or datetime.now(timezone.utc)
    if not isinstance(payload, dict):
        return ClaudeResetObservation("UNKNOWN", None, None, (), "invalid_json_root")
    meta, data = payload.get("meta"), payload.get("data")
    if not isinstance(meta, dict) or not isinstance(data, dict) or meta.get("api_version") != "v1":
        return ClaudeResetObservation("UNKNOWN", None, None, (), "unsupported_api_schema")
    try:
        generated = _utc(meta.get("generated_at"))
        editorial = meta.get("editorial_reviewed_at")
        if editorial is not None:
            _utc(editorial)
    except (ValueError, TypeError):
        return ClaudeResetObservation("UNKNOWN", None, None, (), "invalid_source_timestamp")
    checked_at = generated.isoformat().replace("+00:00", "Z")
    if generated > now + MAX_CLOCK_SKEW or now - generated > MAX_FEED_AGE:
        return ClaudeResetObservation("STALE", checked_at, editorial, (), "feed_age_out_of_bounds")
    offers = data.get("reset_offers")
    if not isinstance(offers, list) or len(offers) > 20:
        return ClaudeResetObservation("UNKNOWN", checked_at, editorial, (), "invalid_offers")
    slots: list[tuple[str, Any]] = [(k, data.get(k)) for k in ("latest_reset", "announced_reset")]
    slots.extend(("reset_offer", v) for v in offers)
    events: dict[str, ClaudeResetEvent] = {}
    for slot, raw in slots:
        if raw is None:
            continue
        event = _event(raw, slot=slot, now=now)
        if event is not None:
            earlier = events.get(event.event_id)
            if earlier is None or event.revision > earlier.revision:
                events[event.event_id] = event
    return ClaudeResetObservation("FRESH", checked_at, editorial, tuple(events.values()))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _http_fetch(opener: Callable[..., Any] | None) -> bytes:
    request = urllib.request.Request(
        STATUS_URL,
        headers={"Accept": "application/json", "User-Agent": "Nerelan-claude-reset-observer/1"},
        method="GET",
    )
    deadline = time.monotonic() + MAX_FETCH_SECONDS
    open_func = opener or urllib.request.build_opener(_NoRedirect()).open
    with open_func(request, timeout=MAX_FETCH_SECONDS) as response:
        if "application/json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("wrong_content_type")
        chunks: list[bytes] = []
        total = 0
        while total <= MAX_BODY:
            # HTTPResponse closes its fp as soon as a complete small body is
            # consumed. EOF is not a missing TLS socket or deadline failure.
            if opener is None and response.isclosed():
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("deadline_exceeded")
            sock = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
            if opener is None and sock is None:
                raise TimeoutError("socket_deadline_unavailable")
            if sock is not None:
                sock.settimeout(remaining)
            data = response.read1(min(8192, MAX_BODY - total + 1))
            if time.monotonic() > deadline:
                raise TimeoutError("deadline_exceeded")
            if not data:
                break
            total += len(data)
            chunks.append(data)
        if total > MAX_BODY:
            raise ValueError("response_too_large")
    return b"".join(chunks)


def fetch_status(*, opener: Callable[..., Any] | None = None,
                 now: datetime | None = None) -> ClaudeResetObservation:
    """One read-only HTTPS fetch; DNS stalls never block caller past 5 seconds."""
    global _NETWORK_WORKER
    done = threading.Event()
    result = [ClaudeResetObservation("UNKNOWN", None, None, (), "fetch_timeout")]

    def worker() -> None:
        try:
            result[0] = parse_status(json.loads(_http_fetch(opener)), now=now)
        except (Exception,):
            result[0] = ClaudeResetObservation("UNKNOWN", None, None, (), "feed_unavailable_or_invalid")
        finally:
            done.set()

    with _NETWORK_LOCK:
        if _NETWORK_WORKER is not None and _NETWORK_WORKER.is_alive():
            return ClaudeResetObservation("UNKNOWN", None, None, (), "previous_fetch_still_running")
        th = threading.Thread(target=worker, name="nerelan-claude-reset-http", daemon=True)
        _NETWORK_WORKER = th
        th.start()
    if not done.wait(MAX_FETCH_SECONDS):
        return ClaudeResetObservation("UNKNOWN", None, None, (), "fetch_timeout")
    return result[0]


class ClaudeResetWatcher:
    """Opt-in host-owned, read-only watcher with crash-safe, non-sensitive receipts.

    Only observed event metadata is stored. This never changes quota status,
    buys credits, redeems a banked offer, starts tasks or calls a model.
    """

    def __init__(self, store_dir: str | Path, *,
                 fetcher: Callable[[], ClaudeResetObservation] = fetch_status,
                 poll_seconds: int = DEFAULT_POLL_SECONDS,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                 on_quota_refresh: Callable[[], None] | None = None):
        if poll_seconds < MIN_POLL_SECONDS:
            raise ValueError("poll interval must be >= 1800 seconds")
        self._path = Path(store_dir) / "claude_reset_observations.json"
        self._fetcher = fetcher
        self._poll_seconds = poll_seconds
        self._clock = clock
        self._on_quota_refresh = on_quota_refresh
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "provider": "claude-code", "status": "UNKNOWN",
            "last_checked_at": None, "editorial_reviewed_at": None,
            "reason": "not_checked", "events": {}, "new_events": [],
        }
        if self._path.exists():
            try:
                stored = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(stored, dict) and stored.get("provider") == "claude-code":
                    self._state.update({k: stored[k] for k in self._state if k in stored})
            except (OSError, ValueError, TypeError):
                pass

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state))

    def poll_once(self) -> dict[str, Any]:
        try:
            observation = self._fetcher()
        except Exception:
            observation = ClaudeResetObservation("UNKNOWN", None, None, (), "observer_error")
        with self._lock:
            known = self._state.get("events")
            if not isinstance(known, dict):
                known = {}
            updated = dict(known)
            new_events: list[dict[str, Any]] = []
            # A banked entitlement is a manual offer, not unlimited. Invalidate
            # its local advisory receipt after its deadline even during source
            # outages; do not infer an account redemption.
            today = self._clock().date()
            for identity, previous in list(updated.items()):
                if (isinstance(previous, dict)
                        and previous.get("action") == "CLAIM_MANUALLY"
                        and isinstance(previous.get("expires_on"), str)):
                    try:
                        is_expired = date.fromisoformat(previous["expires_on"]) < today
                    except ValueError:
                        is_expired = True
                    if is_expired:
                        expired = {**previous, "action": "INVALIDATE_HINT",
                                   "kind": "BANKED_OFFER_EXPIRED"}
                        updated[identity] = expired
                        new_events.append(expired)
            if observation.status == "FRESH":
                for event in observation.events:
                    prior = updated.get(event.event_id)
                    prior_rev = prior.get("revision") if isinstance(prior, dict) else None
                    if type(prior_rev) is not int or prior_rev < event.revision:
                        detail = asdict(event)
                        new_events.append(detail)
                        updated[event.event_id] = detail
                # Keep a bounded history. Retracted updates keep the same ID.
                updated = dict(list(updated.items())[-64:])
            self._state.update({
                "status": observation.status,
                "last_checked_at": observation.checked_at,
                "editorial_reviewed_at": observation.editorial_reviewed_at,
                "reason": observation.reason,
                "events": updated, "new_events": new_events,
            })
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self._path.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(self._state, ensure_ascii=False), encoding="utf-8")
                os.replace(tmp, self._path)
            except OSError:
                self._state["reason"] = "persistence_failed"
            snapshot = json.loads(json.dumps(self._state))
        # Never call arbitrary host code under the persistence lock. This
        # schedules only a read of existing official CLI telemetry, not a
        # model invocation, authorization grant, or account change.
        if (self._on_quota_refresh is not None
                and any(e.get("action") == "REFRESH_QUOTA" for e in new_events)):
            try:
                self._on_quota_refresh()
            except Exception:
                pass  # notifications/remote source cannot block the host
        return snapshot

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="nerelan-claude-reset-watch", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            self.poll_once()
            if self._stop.wait(self._poll_seconds):
                break

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=MAX_FETCH_SECONDS + 1)
            self._thread = None
