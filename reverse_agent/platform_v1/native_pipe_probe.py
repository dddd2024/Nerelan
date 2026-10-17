"""CLI-2A Windows AF_PIPE transport proof, deliberately not a control service.

Host-owned one-shot authenticated IPC (not browser session and not Owner
identity). No persistent listener is installed, no TaskStore or provider
operations exist, and no command can dispatch or inspect private state.

IMPORTANT: this is a test-only transport spike. A production listener still
requires bounded unauthenticated-handshake timeouts, verified Windows pipe
DACL/client identity, and secure native-child key delivery.
"""
from __future__ import annotations

import json
import os
import secrets
import threading
from collections.abc import Callable
from multiprocessing.connection import AuthenticationError, Listener

PROTOCOL = "nerelan-native-pipe-probe/v1"
MAX_REQUEST_BYTES = 4096
BLOCKED = "NOT_SUPPORTED"
PIPE_PREFIX = r"\\.\pipe\nerelan-cli2-probe-"


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_request_field")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError("invalid_constant")


def _parse_probe(payload: bytes) -> bool:
    if type(payload) is not bytes or len(payload) > MAX_REQUEST_BYTES:
        return False
    try:
        envelope = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, TypeError, RecursionError):
        return False
    return (
        type(envelope) is dict
        and set(envelope) == {"protocol", "operation"}
        and envelope["protocol"] == PROTOCOL
        and envelope["operation"] == "doctor"
    )


def _reply(valid_probe: bool) -> bytes:
    # A transport handshake authenticates possession of a host-local session
    # key ONLY. It is not proof of human approval or scheduler authority.
    result = {
        "protocol": PROTOCOL,
        "status": "TRANSPORT_PROOF_ONLY" if valid_probe else BLOCKED,
        "transport_authenticated": True,
        "principal_authenticated": False,
        "dispatch_permitted": False,
        "execution_started": False,
    }
    return json.dumps(result, sort_keys=True, separators=(",", ":")).encode("ascii")


class NativePipeProbe:
    """One-use proof fixture: no background server or model-call capability."""

    def __init__(
        self,
        *,
        key_factory: Callable[[int], bytes] = secrets.token_bytes,
        nonce_factory: Callable[[int], str] = secrets.token_hex,
    ) -> None:
        if os.name != "nt":
            raise RuntimeError("windows_native_pipe_required")
        self._lock = threading.RLock()
        key = key_factory(32)
        name = nonce_factory(16)
        if type(key) is not bytes or len(key) != 32 or key == bytes(32):
            raise RuntimeError("native_pipe_key_unavailable")
        if (
            type(name) is not str
            or len(name) != 32
            or any(ch not in "0123456789abcdef" for ch in name)
        ):
            raise RuntimeError("native_pipe_name_unavailable")
        self._key: bytes | None = key
        self._address = PIPE_PREFIX + name
        self._used = False

    def __repr__(self) -> str:
        return "NativePipeProbe(<host-private>)"

    def deliver_to_trusted_bootstrap(self, receiver: Callable[[str, bytes], None]) -> None:
        """Only trusted in-process/native launcher code may call this.

        Never put the key into argv/env/URLs/SQLite/logs or the browser token
        channel. Real host integration must verify the receiver identity.
        """
        with self._lock:
            if self._used or self._key is None:
                raise RuntimeError("native_pipe_not_available")
            try:
                receiver(self._address, self._key)
            except Exception:
                self._key = None
                self._used = True
                raise RuntimeError("native_pipe_delivery_failed") from None

    def serve_one(self, *, bound: threading.Event | None = None) -> str:
        """Accept exactly one Windows named-pipe connection, then revoke.

        UNSUITABLE for unattended use: Python AF_PIPE accept/authentication has
        no proven handshake timeout. Do not install in a running host yet.
        """
        with self._lock:
            if self._used or self._key is None:
                return "NOT_AVAILABLE"
            self._used = True
            key = self._key
        try:
            listener = Listener(address=self._address, family="AF_PIPE", authkey=key)
            try:
                if bound is not None:
                    bound.set()
                try:
                    connection = listener.accept()
                except (AuthenticationError, EOFError, OSError):
                    return "AUTHENTICATION_FAILED"
                try:
                    with connection:
                        try:
                            packet = connection.recv_bytes(MAX_REQUEST_BYTES + 1)
                        except (EOFError, OSError, ValueError):
                            packet = b""
                        response = _reply(_parse_probe(packet))
                        connection.send_bytes(response)
                except (EOFError, OSError, ValueError):
                    return "TRANSPORT_FAILED"
                return "PROBE_COMPLETED"
            finally:
                listener.close()
        except (OSError, ValueError):
            if bound is not None:
                bound.set()
            return "HOST_UNAVAILABLE"
        finally:
            # A reboot/crash naturally discards all host-memory credentials.
            with self._lock:
                self._key = None
