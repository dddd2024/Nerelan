"""Host-memory local client identity; possession grants no operation authority.

Only trusted native launcher code may receive a capability through ``deliver``.
There is no HTTP bootstrap, serialization, environment or persistent store.
"""

from __future__ import annotations

from collections.abc import Callable
import hmac
import hashlib
import math
import secrets
import threading
import time


class LocalClientSession:
    """Revocable 256-bit identity for one bounded trusted-host lifecycle."""

    def __init__(
        self,
        *,
        ttl_seconds: float = 604800,
        clock: Callable[[], float] = time.monotonic,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        if isinstance(ttl_seconds, bool):
            raise ValueError("invalid_client_session_lifetime")
        try:
            ttl = float(ttl_seconds)
        except (TypeError, ValueError, OverflowError):
            ttl = float("nan")
        if not math.isfinite(ttl) or not 1 <= ttl <= 604800:
            raise ValueError("invalid_client_session_lifetime")
        self._ttl = ttl
        self._clock = clock
        self._token_factory = token_factory or (lambda: secrets.token_hex(32))
        self._lock = threading.RLock()
        self._token: str | None = None
        self._last_token_digest: bytes | None = None
        self._expires = 0.0
        self._last_clock: float | None = None

    def __repr__(self) -> str:
        return "LocalClientSession(<host-private>)"

    @staticmethod
    def _valid_shape(value: object) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(c in "0123456789abcdef" for c in value)
        )

    def _revoke_locked(self) -> None:
        self._token = None
        self._expires = 0.0

    def _now_locked(self) -> float | None:
        try:
            now = self._clock()
            valid = (
                not isinstance(now, bool)
                and isinstance(now, (float, int))
                and math.isfinite(now)
                and (self._last_clock is None or now >= self._last_clock)
            )
        except Exception:
            valid = False
        if not valid:
            self._revoke_locked()
            return None
        self._last_clock = float(now)
        return float(now)

    def rotate(self) -> None:
        """Revoke first; mint a fresh session or leave it unusable on failure."""
        with self._lock:
            self._revoke_locked()
            now = self._now_locked()
            if now is None:
                raise RuntimeError("client_session_clock_unavailable")
            try:
                candidate = self._token_factory()
                valid = self._valid_shape(candidate)
                digest = hashlib.sha256(candidate.encode("ascii")).digest() if valid else None
                valid = valid and digest != self._last_token_digest
            except Exception:
                valid = False
            if not valid:
                # Raise outside the except block: injected entropy failures
                # must not attach a potentially sensitive exception context.
                raise RuntimeError("client_session_entropy_unavailable")
            self._token = candidate
            self._last_token_digest = digest
            self._expires = now + self._ttl

    def revoke(self) -> None:
        with self._lock:
            self._revoke_locked()

    def _active_locked(self) -> bool:
        now = self._now_locked()
        if now is None or self._token is None:
            return False
        if now >= self._expires:
            self._revoke_locked()
            return False
        return True

    def accepts(self, supplied: object) -> bool:
        """Validate a bounded value; callers still enforce Origin and authority."""
        if not self._valid_shape(supplied):
            return False
        with self._lock:
            if not self._active_locked():
                return False
            return hmac.compare_digest(self._token, supplied)

    def deliver(self, trusted_receiver: Callable[[str], None]) -> None:
        """Deliver only to an in-process trusted native bootstrap boundary.

        This method is not an HTTP handler or a permission to export a token.
        A failed receiver revokes the session and produces a fixed error.
        """
        with self._lock:
            if not self._active_locked():
                raise RuntimeError("client_session_unavailable")
            try:
                trusted_receiver(self._token)
                failed = False
            except Exception:
                failed = True
            if failed:
                self._revoke_locked()
                raise RuntimeError("client_session_bootstrap_failed")
