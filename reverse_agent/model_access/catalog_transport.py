"""Deadline-bounded catalog transport with no credential-bearing late threads."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from .catalog_worker import ERROR_STATUSES, MAX_BODY_BYTES, MAX_INPUT_BYTES, validate_request


_WORKER_SLOTS = threading.BoundedSemaphore(2)
_popen = subprocess.Popen


class CatalogTransportError(OSError):
    """A finite public classification, with no upstream request or exception."""

    def __init__(self, status: str):
        self.status = status if status in ERROR_STATUSES.values() else "worker_error"
        super().__init__(self.status)


def _worker_command() -> list[str]:
    return [sys.executable, "-I", "-B", str(Path(__file__).with_name("catalog_worker.py").resolve())]


def _worker_env() -> dict[str, str]:
    # Only operating-system paths needed by the known Python interpreter.
    # No provider keys, proxy settings, Python config or saved auth references.
    return {name: os.environ[name] for name in ("SystemRoot", "WINDIR", "TEMP", "TMP") if name in os.environ}


def _cleanup(proc: subprocess.Popen, deadline: float) -> None:
    try:
        if proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=max(0.0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                raise CatalogTransportError("worker_error") from None
    finally:
        for pipe in (proc.stdin, proc.stdout):
            if pipe is not None:
                pipe.close()


def catalog_transport(
    url: str, headers: dict[str, str], timeout: float
) -> tuple[int, bytes]:
    """Issue exactly one admitted GET, including DNS in a <=10s wall budget.

    The service owns LIVE opt-in and credential resolution. Neither importing
    this module nor constructing the service launches a child or any request.
    This helper receives that private frozen request through anonymous stdin;
    credentials never appear in argv, environment, disk, stderr, or errors.
    """
    started = time.monotonic()
    try:
        url, headers, timeout = validate_request(url, headers, timeout)
    except (ValueError, TypeError, UnicodeError, OverflowError):
        raise CatalogTransportError("invalid_request") from None
    deadline = started + timeout
    # Leave part of the same total budget for owned-process termination/reaping.
    network_deadline = deadline - min(0.2, timeout / 4)
    payload = json.dumps({"url": url, "headers": headers, "deadline": network_deadline},
                         ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_INPUT_BYTES:
        raise CatalogTransportError("invalid_request")
    if time.monotonic() >= network_deadline:
        raise CatalogTransportError("timeout")
    if not _WORKER_SLOTS.acquire(blocking=False):
        raise CatalogTransportError("busy")
    proc = None
    try:
        proc = _popen(_worker_command(), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=_worker_env(),
            shell=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        remaining = network_deadline - time.monotonic()
        if remaining <= 0:
            raise CatalogTransportError("timeout")
        output, _ = proc.communicate(input=payload, timeout=remaining)
        if proc.returncode != 0:
            raise CatalogTransportError(ERROR_STATUSES.get(proc.returncode, "worker_error"))
        if len(output) > MAX_BODY_BYTES + 4:
            raise CatalogTransportError("worker_error")
        status_line, separator, body = output.partition(b"\n")
        if not separator or len(status_line) != 3 or not status_line.isdigit():
            raise CatalogTransportError("worker_error")
        status = int(status_line)
        if not 100 <= status <= 599 or (not 200 <= status < 300 and body):
            raise CatalogTransportError("worker_error")
        return status, body
    except subprocess.TimeoutExpired:
        raise CatalogTransportError("timeout") from None
    except CatalogTransportError:
        raise
    except OSError:
        raise CatalogTransportError("worker_error") from None
    finally:
        try:
            if proc is not None:
                _cleanup(proc, deadline)
        finally:
            _WORKER_SLOTS.release()
