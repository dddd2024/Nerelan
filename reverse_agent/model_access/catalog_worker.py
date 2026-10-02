"""One bounded catalog GET, run only by the isolated trusted-host child.

This script has only standard-library imports and never reads configuration,
credential files, proxy environment settings, or arbitrary request overrides.
Its input is private anonymous-pipe data; its output is an HTTP status line and
a bounded body. Failures are finite exit codes, never exception text.
"""

from __future__ import annotations

from ipaddress import ip_address
import json
import math
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


MAX_BODY_BYTES = 1_048_576
MAX_INPUT_BYTES = 65_536
MAX_TIMEOUT_SECONDS = 10.0
ERROR_STATUSES = {
    20: "invalid_request",
    21: "timeout",
    22: "connection_error",
    23: "response_too_large",
    24: "worker_error",
    25: "busy",
}


def validate_request(
    url: str, headers: dict[str, str], timeout: float
) -> tuple[str, dict[str, str], float]:
    """Validate and copy the complete request without resolving a hostname."""
    if (
        not isinstance(url, str)
        or not url
        or len(url.encode("utf-8")) > 4096
        or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url)
        or "\\" in url
        or "?" in url
        or "#" in url
    ):
        raise ValueError("invalid_request")
    try:
        url.encode("ascii")
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
        if (
            parsed.scheme not in {"http", "https"}
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or (port is not None and not 1 <= port <= 65535)
            or not parsed.path.endswith("/models")
        ):
            raise ValueError("invalid_request")
        if parsed.scheme == "http" and hostname.casefold() != "localhost":
            if not ip_address(hostname).is_loopback:
                raise ValueError("invalid_request")
    except (UnicodeError, ValueError):
        raise ValueError("invalid_request") from None
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (float, int))
        or not math.isfinite(timeout)
        or not 0 < timeout <= MAX_TIMEOUT_SECONDS
        or not isinstance(headers, dict)
        or len(headers) > 2
    ):
        raise ValueError("invalid_request")
    copied: dict[str, str] = {}
    for name, value in headers.items():
        if not isinstance(name, str) or name.casefold() not in {"accept", "authorization"}:
            raise ValueError("invalid_request")
        canonical = {"accept": "Accept", "authorization": "Authorization"}[name.casefold()]
        if (
            canonical in copied
            or not isinstance(value, str)
            or not value
            or len(value) > 16_384
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError("invalid_request")
        try:
            value.encode("latin-1")
        except UnicodeError:
            raise ValueError("invalid_request") from None
        copied[canonical] = value
    return url, copied, float(timeout)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        return None


def _fetch(payload: object) -> tuple[int, bytes]:
    if not isinstance(payload, dict) or set(payload) != {"url", "headers", "deadline"}:
        raise ValueError("invalid_request")
    deadline = payload["deadline"]
    if isinstance(deadline, bool) or not isinstance(deadline, (float, int)) or not math.isfinite(deadline):
        raise ValueError("invalid_request")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError
    url, headers, _ = validate_request(payload["url"], payload["headers"], remaining)
    request = Request(url, headers=headers, method="GET")
    # An explicit empty ProxyHandler prevents urllib's environment discovery.
    # No auth handler, cookie handler, retry, pagination, or redirect is added.
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError
    try:
        response = opener.open(request, timeout=remaining)
    except HTTPError as error:
        # Status alone is sufficient for errors; never project their bodies.
        with error:
            return int(error.code), b""
    with response:
        status = int(response.status)
        if not 200 <= status < 300:
            return status, b""
        body = response.read(MAX_BODY_BYTES + 1)
    if time.monotonic() >= deadline:
        raise TimeoutError
    if len(body) > MAX_BODY_BYTES:
        raise OverflowError
    return status, body


def main() -> int:
    try:
        data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if not data or len(data) > MAX_INPUT_BYTES:
            return 20
        try:
            payload = json.loads(data.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError, RecursionError):
            return 20
        status, body = _fetch(payload)
        if not 100 <= status <= 599:
            return 24
        sys.stdout.buffer.write(str(status).encode("ascii") + b"\n" + body)
        sys.stdout.buffer.flush()
        return 0
    except ValueError:
        return 20
    except TimeoutError:
        return 21
    except OverflowError:
        return 23
    except Exception:
        return 22


if __name__ == "__main__":
    raise SystemExit(main())
