"""CLI-0: safe headless discovery; NOT an authenticated control-plane client.

Only /api/health is public. A CLI must not acquire browser capabilities,
read TaskStore SQLite directly, or infer authorization from localhost.
"""
from __future__ import annotations

import json
import socket
import sys
import time
from collections.abc import Callable, Sequence
from http.client import HTTPResponse
from typing import Any

PROTOCOL = "nerelan-control/v1"
HEALTH_URL = "http://127.0.0.1:8766/api/health"
BLOCKED = 50
MAX_HEALTH_BYTES = 4096


class _DeadlineSocket(socket.socket):
    """Socket file reads share the connect/send monotonic deadline."""

    def __init__(self, deadline: float):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.deadline = deadline

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("health deadline")
        return remaining

    def recv_into(self, buffer, nbytes=0, flags=0):
        # SocketIO (used by HTTPResponse.makefile) calls this for EVERY recv,
        # including status, headers, chunk framing and the entire body.
        self.settimeout(self.remaining())
        return super().recv_into(buffer, nbytes, flags)


def _read_public_health() -> bytes:
    deadline = time.monotonic() + 2.0
    with _DeadlineSocket(deadline) as sock:
        sock.settimeout(sock.remaining())
        # Numeric IPv4 only: no DNS, proxy, URL override or ambient auth.
        sock.connect(("127.0.0.1", 8766))
        sock.settimeout(sock.remaining())
        sock.sendall(b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1:8766\r\nConnection: close\r\n\r\n")
        with HTTPResponse(sock) as response:
            response.begin()
            # HTTPResponse does not follow redirects. Reject every non-200.
            if response.status != 200:
                raise ValueError("health status")
            raw = response.read(MAX_HEALTH_BYTES + 1)
        sock.remaining()
        return raw


def _public_health(probe: Callable[[], bytes] | None = None) -> bool:
    """Observe only the deliberately unauthenticated loopback health route."""
    try:
        if probe is None:
            raw = _read_public_health()
        else:
            raw = probe()
        if not isinstance(raw, bytes) or len(raw) > MAX_HEALTH_BYTES:
            return False
        payload = json.loads(raw)
        return type(payload) is dict and payload.get("ready") is True
    except (Exception,):
        # No exception strings, file paths, response bodies, or credentials
        # are allowed into this public diagnostic.
        return False


def evaluate(argv: Sequence[str], *, probe: Callable[[], bytes] | None = None) -> tuple[int, dict[str, Any]]:
    """Pure command gate; no Goal/Task/window mutator can reach an API."""
    if type(argv) not in {list, tuple} or any(type(arg) is not str for arg in argv):
        return BLOCKED, {"protocol": PROTOCOL, "status": "INVALID_COMMAND"}
    args = list(argv)
    if args and args[-1] == "--json":
        args.pop()
    if args == ["doctor"]:
        reachable = _public_health(probe)
        return (0 if reachable else BLOCKED), {
            "protocol": PROTOCOL,
            "status": "PUBLIC_HEALTH_OBSERVED" if reachable else "PUBLIC_HEALTH_UNAVAILABLE",
            "public_health_reachable": reachable,
            "authenticated": False,
            "dispatch_permitted": False,
            "control_plane": "NOT_CONNECTED",
        }
    if args == ["status"]:
        # Status contains task identities and budget/usage, so /api/health
        # cannot serve it and the browser's bearer identity must not be reused.
        return BLOCKED, {
            "protocol": PROTOCOL,
            "status": "WAITING",
            "reason": "authenticated_control_transport_not_implemented",
            "dispatch_permitted": False,
        }
    return BLOCKED, {
        "protocol": PROTOCOL,
        "status": "NOT_SUPPORTED",
        "reason": "authenticated_control_transport_not_implemented",
        "dispatch_permitted": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        exit_code, payload = evaluate(sys.argv[1:] if argv is None else argv)
        print(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
        return exit_code
    except Exception:
        # An unexpected exception must never look like a successful action.
        print(json.dumps({"protocol": PROTOCOL, "status": "UNKNOWN", "dispatch_permitted": False}))
        return BLOCKED


if __name__ == "__main__":
    raise SystemExit(main())
