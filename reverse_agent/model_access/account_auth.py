"""Bounded account-login lifecycle delegated to provider-owned OpenCode OAuth.

This module never implements OAuth, persists authorization material, or reads
OpenCode credential files.  It coordinates one short-lived authenticated
loopback OpenCode server and exposes only a sanitized browser continuation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    deadline: float
    generation: int
    server: AccountAuthServer
    method_index: int | None = None
    callback_method: str | None = None
    timer: TimerHandle | None = None
    _state_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)
    _expired: bool = field(default=False, init=False, repr=False)

    def is_expired(self) -> bool:
        with self._state_lock:
            return self._expired

    def expire(self) -> bool:
        """Claim the flow and close its child without the manager lock."""

        with self._state_lock:
            if self._closed:
                return False
            self._expired = True
            self._closed = True
            timer = self.timer
        if timer is not None:
            timer.cancel()
        self.server.close()
        return True

    def expire_if_due(self, clock: Callable[[], float]) -> bool:
        """Claim expiry from the absolute deadline even if the timer is late."""

        with self._state_lock:
            if self._closed:
                return self._expired
            if clock() < self.deadline:
                return False
            self._expired = True
            self._closed = True
            timer = self.timer
        if timer is not None:
            timer.cancel()
        self.server.close()
        return True

    def finish(self, clock: Callable[[], float]) -> bool:
        """Atomically claim success only while still before the deadline."""

        with self._state_lock:
            if self._closed:
                return False
            succeeded = clock() < self.deadline
            self._expired = not succeeded
            self._closed = True
            timer = self.timer
        if timer is not None:
            timer.cancel()
        self.server.close()
        return succeeded

    def cancel(self) -> None:
        with self._state_lock:
            if self._closed:
                return
            self._closed = True
            timer = self.timer
        if timer is not None:
            timer.cancel()
        self.server.close()


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
            deadline = self._clock() + self._timeout_seconds
            self._generation += 1
            flow = _ActiveFlow(
                connection_id=connection["connection_id"],
                provider_id="openai",
                deadline=deadline,
                generation=self._generation,
                server=server,
            )
            timer = self._timer_factory(
                self._timeout_seconds,
                lambda: self._expire(flow),
            )
            timer.daemon = True
            flow.timer = timer
            self._active = flow
            self._last_terminal = None
            timer.start()
            try:
                methods = server.provider_auth_methods(provider_id="openai")
                self._raise_if_expired(flow)
                method = next(
                    (candidate for candidate in methods if candidate.type == "oauth"),
                    None,
                )
                if method is None:
                    raise ValueError("OpenCode did not advertise OpenAI OAuth")
                authorization = server.provider_oauth_authorize(
                    provider_id="openai", method_index=method.index
                )
                self._raise_if_expired(flow)
                flow.method_index = method.index
                flow.callback_method = authorization.method
                return {
                    "status": "awaiting_browser",
                    "provider": "openai",
                    "authorization_url": authorization.url,
                    "callback_method": authorization.method,
                    "instructions": authorization.instructions,
                    "expires_in_seconds": int(self._timeout_seconds),
                }
            except Exception as exc:
                expired = self._expire_if_needed(flow)
                if self._active is flow:
                    self._active = None
                flow.cancel()
                if expired and str(exc) != "account login expired":
                    raise ValueError("account login expired") from exc
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
            self._raise_if_expired(active)
            if active.method_index is None or active.callback_method is None:
                raise ValueError("account login is still starting")
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
                self._raise_if_expired(active)
                if not completed:
                    raise ValueError("OpenCode did not complete account login")
                if not active.finish(self._clock):
                    raise ValueError("account login expired")
                if self._active is active:
                    self._active = None
            except Exception as exc:
                expired = self._expire_if_needed(active)
                if self._active is active:
                    self._active = None
                active.cancel()
                if expired and str(exc) != "account login expired":
                    raise ValueError("account login expired") from exc
                raise
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
            active.cancel()

    def _expire(self, flow: _ActiveFlow) -> None:
        if not flow.expire():
            return
        with self._lock:
            active = self._active
            if active is not flow:
                return
            self._active = None
            self._last_terminal = (flow.connection_id, "expired")

    def _expire_locked(self) -> None:
        active = self._active
        if active is None:
            return
        self._active = None
        active.expire()
        self._last_terminal = (active.connection_id, "expired")

    def _raise_if_expired(self, flow: _ActiveFlow) -> None:
        if self._expire_if_needed(flow):
            raise ValueError("account login expired")

    def _expire_if_needed(self, flow: _ActiveFlow) -> bool:
        expired = flow.expire_if_due(self._clock) or flow.is_expired()
        if expired:
            if self._active is flow:
                self._active = None
            self._last_terminal = (flow.connection_id, "expired")
        return expired
