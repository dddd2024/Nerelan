"""Normalize the real Magpie session route endpoint (not a synthetic list).

GET /v1/magpie/route?session=<id> returns {session, seq, route}.
The route has time, asked, group, model, tries, done, status, and served.
model is only a candidate until the route finishes. served is the reply's
vendor-native model and might lack the provider prefix. The route does not
reveal the upstream account. Account attribution and cash cost remain UNKNOWN.
Fail closed for stale, incomplete, conflicting or unsupported evidence.

Based on yetone/magpie internal/gateway/session_route.go; the local 0.1.1250
gateway was independently probed on 2026-10-16 with a synthetic absent session.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from typing import Any

SOURCE = "MAGPIE_SESSION_ROUTE"


def _unknown(reason: str, *, state: str = "UNKNOWN", seq: int | None = None,
             asked: str | None = None, group: str | None = None,
             candidate: str | None = None, at: str | None = None) -> dict[str, Any]:
    return {
        "state": state, "reason": reason, "source": SOURCE,
        "seq": seq, "requested_model": asked, "group": group,
        "candidate_model": candidate, "routed_model": None,
        "provider": None, "account_ref": None,
        "account_state": "UNKNOWN", "observed_at": at,
        "fallback_count": None,
    }


def _safe_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value or len(value) > 256:
        return None
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return None
    return value


def _concrete_model(value: Any) -> str | None:
    text = _safe_text(value)
    if not text or "/" not in text:
        return None
    provider, model = text.split("/", 1)
    if not provider or not model or provider == "group":
        return None
    return text


def _parsed_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError, OverflowError):
        return None


def parse_route_evidence(payload: Any, session_id: Any, now: datetime,
                         max_age_seconds: float = 900,
                         *, after_seq: int | None = None) -> dict[str, Any]:
    """Parse one session route. No network I/O, credentials or cost guesses.

    Use after_seq sampled before dispatch to distinguish consecutive turns of
    one conversation. With a unique per-request session it may be omitted.
    The route timestamp still enforces a freshness bound.
    """
    if not isinstance(session_id, str) or not 0 < len(session_id.strip()) <= 128:
        return _unknown("invalid_session_id")
    session_id = session_id.strip()
    if not isinstance(now, datetime) or now.tzinfo is None:
        return _unknown("invalid_clock")
    if isinstance(max_age_seconds, bool) or not isinstance(max_age_seconds, (int, float)) or (
        not math.isfinite(max_age_seconds) or max_age_seconds < 0
    ):
        return _unknown("invalid_clock")
    if after_seq is not None and (type(after_seq) is not int or after_seq < 0):
        return _unknown("invalid_sequence")
    if isinstance(payload, (str, bytes, bytearray)):
        try:
            payload = json.loads(payload)
        except (UnicodeError, ValueError, TypeError):
            return _unknown("invalid_schema")
    if not isinstance(payload, dict):
        return _unknown("invalid_schema")
    if payload.get("session") != session_id:
        return _unknown("session_mismatch")
    seq = payload.get("seq")
    if type(seq) is not int or seq < 0:
        return _unknown("invalid_sequence")
    if after_seq is not None and seq <= after_seq:
        return _unknown("sequence_not_advanced", seq=seq)
    route = payload.get("route")
    if route is None:
        return _unknown("session_has_no_route", seq=seq)
    if not isinstance(route, dict):
        return _unknown("invalid_route", seq=seq)
    asked = _safe_text(route.get("asked"))
    group = _safe_text(route.get("group"))
    candidate = _concrete_model(route.get("model"))
    at = _parsed_time(route.get("time"))
    if at is None:
        return _unknown("missing_route_timestamp", seq=seq, asked=asked, group=group)
    stamp = at.isoformat()
    age = (now.astimezone(timezone.utc) - at).total_seconds()
    if age < 0:
        return _unknown("future_route", seq=seq, asked=asked, group=group)
    if age > max_age_seconds:
        return _unknown("stale_route", state="STALE", seq=seq, asked=asked, group=group, at=stamp)
    if route.get("done") is not True:
        return _unknown("route_in_flight", state="IN_FLIGHT", seq=seq,
                        asked=asked, group=group, candidate=candidate, at=stamp)
    status = route.get("status")
    if type(status) is not int or not 200 <= status < 300:
        return _unknown("route_failed", seq=seq, asked=asked, group=group, at=stamp)
    tries = route.get("tries")
    if not isinstance(tries, list) or not tries or not all(isinstance(t, dict) for t in tries):
        return _unknown("missing_route_tries", seq=seq, asked=asked, group=group, at=stamp)
    last = tries[-1]
    member = _concrete_model(last.get("model"))
    if (not member or candidate != member or last.get("done") is not True or
        type(last.get("status")) is not int or not 200 <= last["status"] < 300 or
        bool(last.get("fail"))):
        return _unknown("last_try_not_verified", seq=seq, asked=asked, group=group, at=stamp)
    served = _safe_text(route.get("served"))
    if served:
        model_name = member.split("/", 1)[1]
        if served not in (member, model_name):
            return _unknown("served_model_conflict", seq=seq, asked=asked, group=group, at=stamp)
    fallback_count = sum(bool(t.get("fail")) for t in tries[:-1])
    return {
        "state": "VERIFIED_ROUTE", "reason": None, "source": SOURCE,
        "seq": seq, "requested_model": asked, "group": group,
        "candidate_model": member, "routed_model": member,
        "provider": member.split("/", 1)[0], "account_ref": None,
        "account_state": "UNKNOWN", "observed_at": stamp,
        "fallback_count": fallback_count,
    }