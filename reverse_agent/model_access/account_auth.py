"""Bounded account-login lifecycle delegated to provider-owned OpenCode OAuth.

This module never implements OAuth, persists authorization material, or reads
OpenCode credential files.  It coordinates one short-lived authenticated
loopback OpenCode server and exposes only a sanitized browser continuation.
"""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Any, Callable, Protocol

from .store import ModelProfileStore


class AccountAuthServer(Protocol):
    def provider_auth_methods(self, *, provider_id: str) -> tuple[Any, ...]: ...

    def provider_oauth_authorize(
        self, *, provider_id: str, method_index: int
    ) -> Any: ...

    def provider_oauth_callback(
        self, *, provider_id: str, method_index: int, code: str | None = None
    ) -> bool: ...

    def close(self) -> None: ...


class TimerHandle(Protocol):
    daemon: bool

    def start(self) -> None: ...

    def cancel(self) -> None: ...


ServerFactory = Callable[[], AccountAuthServer]
RefreshCallback = Callable[[bool, str | None], None]
TimerFactory = Callable[[float, Callable[[], None]], TimerHandle]


@dataclass
class _ActiveFlow:
    connection_id: str
    provider_id: str
    method_index: int
    callback_method: str
    deadline: float
    generation: int
    server: AccountAuthServer
    timer: TimerHandle


class AccountAuthManager:
    """Thread-safe, one-flow-at-a-time coordinator for OpenAI account login."""

    def __init__(
        self,
        *,
        store: ModelProfileStore,
        server_factory: ServerFactory | None,
        refresh: RefreshCallback,
        timeout_seconds: float = 300.0,
        clock: Callable[[], float] = time.monotonic,
        timer_factory: TimerFactory = threading.Timer,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 900:
            raise ValueError("account auth timeout must be between 0 and 900 seconds")
        self._store = store
        self._server_factory = server_factory
        self._refresh = refresh
        self._timeout_seconds = float(timeout_seconds)
        self._clock = clock
        self._timer_factory = timer_factory
        self._lock = threading.RLock()
        self._active: _ActiveFlow | None = None
        self._generation = 0
        self._last_terminal: tuple[str, str] | None = None

    def start(self, connection_id: str) -> dict[str, Any]:
        connection = self._validated_connection(connection_id)
        factory = self._server_factory
        if factory is None:
            raise ValueError("native account login is unavailable on this host")
        with self._lock:
            self._cancel_locked()
            server = factory()
            try:
                methods = server.provider_auth_methods(provider_id="openai")
                method = next(
                    (candidate for candidate in methods if candidate.type == "oauth"),
                    None,
                )
                if method is None:
                    raise ValueError("OpenCode did not advertise OpenAI OAuth")
                authorization = server.provider_oauth_authorize(
                    provider_id="openai", method_index=method.index
                )
                deadline = self._clock() + self._timeout_seconds
                self._generation += 1
                generation = self._generation
                timer = self._timer_factory(
                    self._timeout_seconds,
                    lambda: self._expire(generation),
                )
                timer.daemon = True
                self._active = _ActiveFlow(
                    connection_id=connection["connection_id"],
                    provider_id="openai",
                    method_index=method.index,
                    callback_method=authorization.method,
                    deadline=deadline,
                    generation=generation,
                    server=server,
                    timer=timer,
                )
                self._last_terminal = None
                timer.start()
                return {
                    "status": "awaiting_browser",
                    "provider": "openai",
                    "authorization_url": authorization.url,
                    "callback_method": authorization.method,
                    "instructions": authorization.instructions,
                    "expires_in_seconds": int(self._timeout_seconds),
                }
            except Exception:
                active = self._active
                if active is not None and active.server is server:
                    self._cancel_locked()
                else:
                    server.close()
                raise

    def status(self, connection_id: str) -> dict[str, Any]:
        connection = self._validated_connection(connection_id)
        with self._lock:
            flow_status = (
                self._last_terminal[1]
                if self._last_terminal is not None
                and self._last_terminal[0] == connection_id
                else "idle"
            )
            active = self._active
            if active is not None:
                if self._clock() >= active.deadline:
                    self._expire_locked()
                    flow_status = "expired"
                elif active.connection_id == connection_id:
                    flow_status = "awaiting_browser"
                else:
                    flow_status = "busy"
            return self._status_payload(connection, flow_status)

    def callback(self, connection_id: str, code: str | None = None) -> dict[str, Any]:
        self._validated_connection(connection_id)
        with self._lock:
            active = self._active
            if active is None or active.connection_id != connection_id:
                raise ValueError("no active account login for this connection")
            if self._clock() >= active.deadline:
                self._expire_locked()
                raise ValueError("account login expired")
            if active.callback_method == "code":
                if not isinstance(code, str) or not code.strip() or len(code) > 4096:
                    raise ValueError("authorization code is required")
                callback_code = code.strip()
            else:
                if code not in {None, ""}:
                    raise ValueError("authorization code is not accepted for this flow")
                callback_code = None
            try:
                completed = active.server.provider_oauth_callback(
                    provider_id=active.provider_id,
                    method_index=active.method_index,
                    code=callback_code,
                )
                if not completed:
                    raise ValueError("OpenCode did not complete account login")
            finally:
                self._cancel_locked()
        self._refresh(True, connection_id)
        connection = self._validated_connection(connection_id)
        flow_status = (
            "authenticated"
            if connection["external_session_status"] == "available"
            else "verification_pending"
        )
        return self._status_payload(connection, flow_status)

    def cancel(self, connection_id: str) -> dict[str, Any]:
        connection = self._validated_connection(connection_id)
        with self._lock:
            active = self._active
            if active is not None and active.connection_id != connection_id:
                raise ValueError("another connection owns the active account login")
            self._cancel_locked()
        return self._status_payload(connection, "canceled")

    def logout(self, connection_id: str) -> dict[str, Any]:
        """Cancel local flow and describe the provider-owned logout boundary.

        OpenCode's provider OAuth HTTP surface currently has no credential
        removal endpoint.  Claiming success or editing its credential file
        would violate the ownership boundary, so this typed result is explicit.
        """

        connection = self._validated_connection(connection_id)
        with self._lock:
            active = self._active
            if active is not None and active.connection_id == connection_id:
                self._cancel_locked()
        payload = self._status_payload(connection, "provider_logout_required")
        payload["instructions"] = "Use OpenCode `auth logout` to remove the provider-owned session."
        return payload

    def close(self) -> None:
        with self._lock:
            self._cancel_locked()

    def _validated_connection(self, connection_id: str) -> dict[str, Any]:
        connection = self._store.get_connection_public(connection_id)
        if not connection["enabled"]:
            raise ValueError("connection is disabled")
        if connection["auth_method"] != "account_login":
            raise ValueError("connection does not use account_login")
        if connection["provider"] != "openai":
            raise ValueError("native account login currently supports OpenAI only")
        return connection

    def _status_payload(
        self, connection: dict[str, Any], flow_status: str
    ) -> dict[str, Any]:
        return {
            "status": flow_status,
            "provider": "openai",
            "external_session_status": connection["external_session_status"],
        }

    def _cancel_locked(self) -> None:
        active = self._active
        self._active = None
        if active is not None:
            active.timer.cancel()
            active.server.close()

    def _expire(self, generation: int) -> None:
        with self._lock:
            active = self._active
            if active is None or active.generation != generation:
                return
            self._expire_locked()

    def _expire_locked(self) -> None:
        active = self._active
        if active is None:
            return
        connection_id = active.connection_id
        self._cancel_locked()
        self._last_terminal = (connection_id, "expired")
