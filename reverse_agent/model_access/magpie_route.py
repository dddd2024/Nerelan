"""Pure, read-only normalization of Magpie route evidence per logical session.

Support boundary (fails closed outside it): the only accepted payload shape is
a Magpie route log envelope ``{"object": "list", "data": [...]}`` where each
entry is a mapping carrying, for one logical session, the concrete route that
actually served the request: a routed model identifier that names a concrete
model (``provider/model``), the upstream provider, and an account reference.
Unsupported shapes, unknown extra fields, private data, missing route fields,
ambiguous fallback (more than one route entry for the session) and stale
readings all normalize to a non-verified record; the actual provider/model is
never inferred from a route group name, and no costs are estimated.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from typing import Any, Mapping

PROVENANCE = "EXTERNAL_MAGPIE"

# Keys a route entry may carry. Anything else is untrusted and fails closed.
SUPPORTED_ENTRY_KEYS = frozenset({
    "sessionId", "requestedModel", "routedModel", "provider", "accountRef",
    "occurredAt", "sourceVersion",
})
PRIVATE_KEYS = frozenset({"user", "alias", "from"})


def _decode(payload: Any) -> Any:
    if isinstance(payload, (str, bytes, bytearray)):
        try:
            return json.loads(payload)
        except (ValueError, UnicodeError):
            return None
    return payload


def _private_strings(payload: Any) -> set[str]:
    values: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in PRIVATE_KEYS and isinstance(value, str) and value:
                values.add(value)
            values.update(_private_strings(value))
    elif isinstance(payload, list):
        for value in payload:
            values.update(_private_strings(value))
    return values


def _text(value: Any, secrets: set[str]) -> str | None:
    if not isinstance(value, str) or not value or any(s in value for s in secrets):
        return None
    return value


def _date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def _unverified(reason: str) -> dict[str, Any]:
    return dict(state="UNKNOWN", reason=reason, session_id=None,
                requested_model=None, routed_model=None, provider=None,
                account_ref=None, observed_at=None, provenance=PROVENANCE,
                source_version=None)


def parse_route_evidence(payload: Any, session_id: Any, now: datetime,
                         max_age_seconds: float = 900) -> dict[str, Any]:
    """Normalize the actual route that served ``session_id``, or why it is unknown.

    Pure and read-only: no network, no credentials, no inference from group
    names and no cost estimation. Unsupported evidence fails closed to UNKNOWN.
    """
    if not isinstance(session_id, str) or not session_id.strip():
        return _unverified("invalid_session_id")
    session_id = session_id.strip()
    payload = _decode(payload)
    if not isinstance(payload, dict) or payload.get("object") != "list" or not isinstance(payload.get("data"), list):
        return _unverified("invalid_schema")
    secrets = _private_strings(payload)
    matches: list[dict[str, Any]] = []
    for raw in payload["data"]:
        if not isinstance(raw, dict):
            continue
        if raw.get("sessionId") == session_id:
            matches.append(raw)
    if not matches:
        return _unverified("session_not_found")
    if len(matches) > 1:
        # More than one route entry for one session is an ambiguous fallback.
        return _unverified("fallback_ambiguous")
    raw = matches[0]
    if not SUPPORTED_ENTRY_KEYS.issuperset(raw):
        return _unverified("untrusted_field")
    if secrets:
        return _unverified("untrusted_field")
    record = _unverified(None)
    record["session_id"] = session_id
    requested = _text(raw.get("requestedModel"), secrets)
    routed = _text(raw.get("routedModel"), secrets)
    provider = _text(raw.get("provider"), secrets)
    account_ref = _text(raw.get("accountRef"), secrets)
    version = _text(raw.get("sourceVersion"), secrets)
    record.update(requested_model=requested, routed_model=routed,
                  provider=provider, account_ref=account_ref,
                  source_version=version)
    if not routed or not provider or not account_ref:
        # The actual route is never derived from a requested group name.
        return record | {"reason": "missing_route_fields", "routed_model": None,
                         "provider": None, "account_ref": None}
    if "/" not in routed or routed.split("/", 1)[1] == "":
        return record | {"reason": "invalid_route_model", "routed_model": None,
                         "provider": None, "account_ref": None}
    occurred = _date(raw.get("occurredAt"))
    if occurred is None:
        return record | {"reason": "invalid_timestamp", "routed_model": None,
                         "provider": None, "account_ref": None}
    if (not isinstance(now, datetime) or now.tzinfo is None
            or isinstance(max_age_seconds, bool)
            or not isinstance(max_age_seconds, (int, float))
            or not math.isfinite(max_age_seconds) or max_age_seconds < 0):
        return record | {"reason": "invalid_timestamp", "routed_model": None,
                         "provider": None, "account_ref": None}
    age = (now - occurred).total_seconds()
    if age < 0:
        return record | {"reason": "invalid_timestamp", "routed_model": None,
                         "provider": None, "account_ref": None}
    record["observed_at"] = occurred.isoformat()
    if age > max_age_seconds:
        return record | {"state": "STALE", "reason": "stale_reading",
                         "routed_model": None, "provider": None,
                         "account_ref": None}
    record["state"] = "VERIFIED"
    record["reason"] = None
    return record
