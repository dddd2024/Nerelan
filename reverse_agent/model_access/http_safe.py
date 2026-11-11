"""Outbound HTTP for requests that carry a provider credential.

urllib's default opener follows redirects and copies request headers, including
Authorization, to the new location, even on another host. A request that carries a
provider key must never be replayed elsewhere, so redirects are refused and surface as
an HTTPError with the redirect status instead.
"""

from __future__ import annotations

from typing import Any
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class _RefuseRedirects(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        raise HTTPError(req.full_url, code, "redirect refused: credentials are never forwarded", headers, fp)


_OPENER = build_opener(_RefuseRedirects)
# No proxy at all: a loopback-only request must not be handed to an
# http_proxy/HTTP_PROXY or system proxy that no_proxy happens not to cover.
_DIRECT_OPENER = build_opener(ProxyHandler({}), _RefuseRedirects)


def urlopen(request: Request, timeout: float) -> Any:
    """Drop-in for urllib.request.urlopen that never follows a redirect."""
    return _OPENER.open(request, timeout=timeout)


def urlopen_direct(request: Request, timeout: float) -> Any:
    """Like urlopen, and also never uses a proxy (for loopback-only destinations)."""
    return _DIRECT_OPENER.open(request, timeout=timeout)
