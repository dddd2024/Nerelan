"""CLI-0: safe headless discovery; NOT an authenticated control-plane client.

Only /api/health is public. A CLI must not acquire browser capabilities,
read TaskStore SQLite directly, or infer authorization from localhost.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Callable, Sequence
from typing import Any
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

PROTOCOL = "nerelan-control/v1"
HEALTH_URL = "http://127.0.0.1:8766/api/health"
BLOCKED = 50
MAX_HEALTH_BYTES = 4096


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not send even an unauthenticated probe to a redirected host.
        return None


def _public_health(probe: Callable[[], bytes] | None = None) -> bool:
    """Observe only the deliberately unauthenticated loopback health route."""
    try:
        if probe is None:
            # Never use ambient HTTP proxies or user-supplied endpoints.
            opener = build_opener(ProxyHandler({}), _NoRedirect())
            with opener.open(Request(HEALTH_URL, method="GET"), timeout=2) as response:
                if response.geturl() != HEALTH_URL or response.status != 200:
                    return False
                raw = response.read(MAX_HEALTH_BYTES + 1)
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
