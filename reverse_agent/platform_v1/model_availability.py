"""Rare host-side availability observations; catalogs never prove entitlement."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import threading
import time
from typing import Any, Callable, Mapping

UNAVAILABLE_MARKERS = ('model_not_supported', 'not allowed for user type', 'not_allowed', 'not-allowed', 'not allowed',
                       'model_not_found', 'invalid_api_key', 'authentication_error')


def native_owner_account(binding: Mapping[str, Any], connection: Mapping[str, Any]) -> bool:
    return (connection.get('auth_method') == 'external_cli_session'
            or binding.get('executor_id') in {'codex', 'claude_code'}
            or binding.get('model_id', '').lower().split('/', 1)[0] in {'codex', 'claude'})


def availability_error(value: str) -> str | None:
    text = (value or '').lower()
    return next((marker.replace(' ', '_') for marker in UNAVAILABLE_MARKERS if marker in text or marker.replace(' ', '_') in text), None)


def observation(*, now: float, success: bool = False, error: str = '') -> dict[str, Any]:
    reason = availability_error(error)
    return {'state': 'AVAILABLE' if success else 'UNAVAILABLE' if reason else 'TRANSIENT',
            'reason': 'verified_request' if success else reason or 'transient_error',
            'observed_at': now, 'expires_at': now + (86400 if success or reason else 300)}


class AvailabilityCache:
    """Sanitized daily cache, keyed by public pairing + endpoint configuration.

    A global per-host minute limit bounds first-time catalog exploration. The
    callback receives public metadata and must use the host relay/executor; no
    keys or upstream response text enter this cache.
    """
    def __init__(self, path: Path | None = None):
        self.path = path
        self.entries: dict[str, Any] = {}
        self.next_probe = 0.
        self.lock = threading.RLock()
        if path:
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    self.entries = {key: value for key, value in data.items()
                                    if isinstance(value, dict) and value.get("state") in {"AVAILABLE", "UNAVAILABLE", "TRANSIENT"}
                                    and all(type(value.get(field)) in (int, float) and math.isfinite(value[field])
                                            for field in ("observed_at", "expires_at"))}
            except (OSError, ValueError):
                pass

    @staticmethod
    def key(binding: Mapping[str, Any], connection: Mapping[str, Any]) -> str:
        identity = [binding.get(k) for k in ('binding_id', 'model_id', 'executor_id', 'native_endpoint')]
        identity += [connection.get(k) for k in ('connection_id', 'base_url', 'auth_method')]
        return hashlib.sha256(json.dumps(identity).encode()).hexdigest()

    def remember(self, binding: Mapping[str, Any], connection: Mapping[str, Any], result: Mapping[str, Any]) -> None:
        with self.lock:
            key = self.key(binding, connection)
            result = dict(result)
            previous = self.entries.get(key, {})
            if result.get("state") == "TRANSIENT":
                if previous.get("state") == "AVAILABLE":
                    result["verified_until"] = previous.get("expires_at", 0)
                elif previous.get("state") == "TRANSIENT":
                    result["verified_until"] = previous.get("verified_until", 0)
            self.entries[key] = result
            if self.path:
                from ..model_access.store import _write_atomic
                _write_atomic(json.dumps(self.entries, allow_nan=False).encode('utf-8'), self.path)

    def check(self, binding: Mapping[str, Any], connection: Mapping[str, Any], *,
              probe: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
              allow_probe: bool = False, now: float | None = None,
              recent_success: float | None = None) -> dict[str, Any]:
        now = time.time() if now is None else now
        with self.lock:
            entry = self.entries.get(self.key(binding, connection), {})
            # A more recent successful task supersedes an earlier rejection.
            if recent_success is not None and 0 <= now - recent_success < 86400 and recent_success > entry.get('observed_at', 0):
                entry = observation(now=recent_success, success=True)
                self.remember(binding, connection, entry)
            if entry.get('observed_at', 0) > now:
                return {'state': 'UNKNOWN', 'reason': 'clock_discontinuity'}
            if entry.get('state') == 'TRANSIENT' and entry.get('verified_until', 0) > now and entry.get('expires_at', 0) <= now:
                return dict(entry, state='AVAILABLE', penalty=0., reason='recent_success', expires_at=entry['verified_until'])
            if entry.get('expires_at', 0) > now:
                if entry.get('state') == 'TRANSIENT' and entry.get('verified_until', 0) > now:
                    return dict(entry, state='AVAILABLE', penalty=.5)
                return dict(entry)
            owner_account = native_owner_account(binding, connection)
            if not allow_probe or owner_account or probe is None or now < self.next_probe:
                return {'state': 'UNKNOWN', 'reason': 'unverified'}
            self.next_probe = now + 60
            try:
                value = probe(binding)
                result = observation(now=now, success=value.get('ok') is True, error=str(value.get('error', '')))
            except Exception:
                result = observation(now=now, error='transient')
            self.remember(binding, connection, result)
            return result
