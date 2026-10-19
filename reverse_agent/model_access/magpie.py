"""Default-off, read-only observations from a loopback Magpie gateway.

Only cached quotas are requested. No credential discovery or logging occurs here.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request

from . import http_safe


def magpie_enabled(env: Mapping[str, str]) -> bool:
    return env.get("REVERSE_AGENT_MAGPIE") == "1"


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
            if key in ("user", "alias", "from") and isinstance(value, str) and value:
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


def parse_hello(payload: Any) -> str | None:
    payload = _decode(payload)
    if not isinstance(payload, dict) or payload.get("name") != "magpie":
        return None
    return _text(payload.get("version"), _private_strings(payload))


def _number(value: Any, maximum: float = math.inf) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value < 0 or value > maximum:
        return None
    # Avoid converting arbitrarily large JSON integers to floats.
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def parse_models(payload: Any) -> list[dict[str, Any]]:
    payload = _decode(payload)
    if not isinstance(payload, dict) or payload.get("object") != "list" or not isinstance(payload.get("data"), list):
        return []
    secrets = _private_strings(payload)
    result = []
    for item in payload["data"]:
        if not isinstance(item, dict):
            continue
        model_id = _text(item.get("id"), secrets)
        if model_id is None:
            continue
        result.append({
            "model_id": model_id,
            "provider": model_id.split("/", 1)[0] if "/" in model_id else _text(item.get("owned_by"), secrets),
            "display_name": _text(item.get("display_name"), secrets),
            "reasoning": item.get("reasoning") if isinstance(item.get("reasoning"), bool) else None,
            "context_window": _number(item.get("context_window")),
            "max_output_tokens": _number(item.get("max_output_tokens")),
            "is_group": "/" not in model_id,
        })
    return result


def _date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def _account() -> dict[str, Any]:
    return dict(provider=None, kind=None, plan=None, account_ref=None, windows=[],
                cached_windows=[], state="UNKNOWN", reason="invalid_schema", observed_at=None,
                provenance="EXTERNAL_MAGPIE", source_version=None)


def parse_quotas(payload: Any, now: datetime, max_age_seconds: float = 900) -> list[dict[str, Any]]:
    """Normalize cache readings; unknown observations contain no quota percentages.

    source_version is populated by fetch after the separate hello handshake.
    """
    payload = _decode(payload)
    if not isinstance(payload, dict) or payload.get("object") != "list" or not isinstance(payload.get("data"), list):
        return [_account()]
    secrets = _private_strings(payload)
    result = []
    for raw in payload["data"]:
        account = _account()
        result.append(account)
        if not isinstance(raw, dict):
            continue
        provider = _text(raw.get("provider"), secrets)
        user = raw.get("user")
        account.update(provider=provider, kind=raw.get("kind") if raw.get("kind") in ("subscription", "plan", "balance") else None,
                       plan=_text(raw.get("plan"), secrets))
        if provider:
            identity = json.dumps([provider, user if isinstance(user, str) else None], ensure_ascii=True)
            account["account_ref"] = hashlib.sha256(identity.encode()).hexdigest()[:12]
        dates = [_date(raw[key]) for key in ("readAt", "asOf") if key in raw]
        if dates and all(dates):
            account["observed_at"] = min(dates).isoformat()
        reason, undated = None, False
        if not provider or not account["kind"]:
            reason = "invalid_schema"
        elif "error" in raw:
            reason = "quota_error"
        elif raw.get("readDeferred") is not None and raw.get("readDeferred") is not False:
            reason = "read_deferred"
        elif not dates:
            # Magpie leaves asOf out of a new reading and readAt out when it does not know it:
            # the windows are real, only their age is unknown.
            undated = True
        elif not all(dates) or not isinstance(now, datetime) or now.tzinfo is None or _number(max_age_seconds) is None:
            reason = "invalid_timestamp"
        elif any((now - date).total_seconds() < 0 for date in dates):
            reason = "invalid_timestamp"
        elif any((now - date).total_seconds() > max_age_seconds for date in dates):
            account["state"] = "STALE"
            reason = "stale_reading"
        windows = raw.get("windows")
        if reason is None and (not isinstance(windows, list) or not windows):
            reason = "missing_windows"
        # Validate windows with the same checks/privacy filtering for fresh,
        # undated, and stale readings.  Stale windows are preserved in
        # cached_windows for display only; windows stays [] so admission
        # semantics treat stale the same as unknown.
        stale = reason == "stale_reading"
        normalized = []
        if reason is None or stale:
            for window in (windows if isinstance(windows, list) else []):
                if not isinstance(window, dict):
                    reason = "invalid_window"
                    normalized = []
                    break
                used, remaining = _number(window.get("used"), 100), _number(window.get("remaining"), 100)
                name = _text(window.get("name"), secrets)
                reset = _date(window.get("resetsAt"))
                if name is None or used is None or remaining is None or ("resetsAt" in window and reset is None) or ("unlimited" in window and not isinstance(window["unlimited"], bool)):
                    reason = "invalid_window"
                    normalized = []
                    break
                normalized.append(dict(name=name, used_percent=used, remaining_percent=remaining,
                                       resets_at=reset.isoformat() if reset else None,
                                       unlimited=window.get("unlimited", False)))
        if reason is None:
            account.update(state="UNDATED", reason="no_read_time") if undated else account.update(state="FRESH", reason=None)
            account.update(windows=normalized, cached_windows=[])
        elif reason == "stale_reading":
            account.update(state="STALE", reason=reason, windows=[], cached_windows=normalized)
        else:
            # Errors (including invalid_window found while validating a stale
            # reading) override any earlier stale state to UNKNOWN.
            account.update(state="UNKNOWN", reason=reason, windows=[], cached_windows=[])
    counts: dict[str, int] = {}
    for account in result:
        ref = account["account_ref"]
        if ref:
            counts[ref] = counts.get(ref, 0) + 1
    for account in result:
        if counts.get(account["account_ref"], 0) > 1:
            account.update(state="UNKNOWN", reason="duplicate_account", windows=[], cached_windows=[])
    return result


def fetch_magpie_snapshot(base_url: str = "http://127.0.0.1:3425", timeout: float = 2.0,
                          opener: Any = None) -> dict[str, Any]:
    """Fetch explicitly; callers may pass REVERSE_AGENT_MAGPIE_URL as base_url.

    The injectable opener has the same callable contract as http_safe.urlopen.
    """
    snapshot = dict(status="refused", version=None, models=[], accounts=[], reason="invalid_url")
    try:
        url = urlsplit(base_url)
        if (url.scheme not in ("http", "https") or url.hostname not in ("127.0.0.1", "::1", "localhost")
                or url.username is not None or url.password is not None or url.path not in ("", "/")
                or url.query or url.fragment):
            return snapshot
        url.port  # Validate the port before issuing any request.
    except (ValueError, TypeError, AttributeError):
        return snapshot
    open_request = opener or http_safe.urlopen

    def get(path: str) -> Any:
        request = Request(base_url.rstrip("/") + path, headers={"Authorization": "Bearer magpie-nerelan"}, method="GET")
        with open_request(request, timeout=timeout) as response:
            status = response.getcode()
            if status is not None and not 200 <= status < 300:
                raise HTTPError(request.full_url, status, "request refused", {}, None)
            return _decode(response.read())

    try:
        hello = get("/api/hello")
        version = parse_hello(hello)
        if version is None:
            snapshot.update(status="not_magpie", reason="invalid_hello")
            return snapshot
        snapshot["version"] = version
        models = parse_models(get("/v1/models"))
        accounts = parse_quotas(get("/v1/magpie/quotas?kept=1"), datetime.now(timezone.utc))
        for account in accounts:
            account["source_version"] = version
        snapshot.update(status="available", models=models, accounts=accounts, reason=None)
    except HTTPError as exc:
        snapshot.update(status="refused" if 300 <= exc.code < 400 else "unavailable",
                        reason="redirect_refused" if 300 <= exc.code < 400 else "http_error")
    except Exception:
        # Transport errors may embed URLs, response bodies, or personal data.
        snapshot.update(status="unavailable", reason="request_failed")
    return snapshot


DEFAULT_MAGPIE = {"enabled": False, "executable": "", "base_url": "http://127.0.0.1:3425"}


def validate_settings(value: Any, *, check_file: bool = True) -> dict[str, Any]:
    """Validate Owner metadata; defer file existence on load to keep host startup available."""
    if not isinstance(value, dict) or set(value) - set(DEFAULT_MAGPIE):
        raise ValueError("invalid Magpie settings")
    result = {**DEFAULT_MAGPIE, **value}
    if type(result["enabled"]) is not bool:
        raise ValueError("Magpie enabled must be a boolean")
    executable = result["executable"]
    if not isinstance(executable, str):
        raise ValueError("Magpie executable must be an absolute .exe path")
    if executable or result["enabled"]:
        path = Path(executable)
        if not path.is_absolute() or path.suffix.lower() != ".exe":
            raise ValueError("Magpie executable must be an absolute .exe path")
        if check_file and not path.is_file():
            raise ValueError("Magpie executable must be an existing file")
    try:
        url = urlsplit(result["base_url"])
        host = url.hostname
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise ValueError()
        if (url.scheme not in ("http", "https") or url.username is not None or url.password is not None
                or url.path not in ("", "/") or url.query or url.fragment or url.port == 0):
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Magpie base_url must be a loopback HTTP(S) origin") from None
    result["base_url"] = result["base_url"].rstrip("/")
    return result
