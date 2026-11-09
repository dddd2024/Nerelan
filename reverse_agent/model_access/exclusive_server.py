"""HTTP servers that own their port exclusively.

``http.server.HTTPServer`` sets ``SO_REUSEADDR``. On Windows that option lets a
second process bind a port another process is already listening on, so two Nerelan
hosts ran side by side on 8765/8766 over one task store (2026-11-09). On Windows
this class binds with ``SO_EXCLUSIVEADDRUSE`` instead, so the second host fails
to start. Elsewhere ``SO_REUSEADDR`` already refuses a port in LISTEN and only
eases restarts, so behaviour there is unchanged.
"""
from __future__ import annotations

from http.server import ThreadingHTTPServer
import os
import socket


class ExclusiveThreadingHTTPServer(ThreadingHTTPServer):
    def server_bind(self) -> None:
        if os.name == "nt":
            # SO_REUSEADDR and SO_EXCLUSIVEADDRUSE cannot be combined.
            self.allow_reuse_address = False
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()
