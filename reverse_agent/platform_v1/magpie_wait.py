"""Bounded adapter for ``magpie quota wait`` (read-only, never blocking forever).

Magpie can block until a subscription or account has allowance again. That is
strictly better than Nerelan polling, but a blocking child process is a hazard in
an unattended loop: it must be bounded, cancellable by timeout, and it must never
turn a missing binary into a stuck coordinator.

This module therefore exposes one function that always returns within a known
bound and never raises. It does **not** decide when to wait — the caller does;
wiring it into the coordinator's idle path is deliberately left to the P2
fault-injection work, which can test shutdown while a wait is in flight.

Target validation matters: the target is passed as a positional argument to a
CLI, so anything that looks like a flag, contains whitespace, or carries shell
metacharacters is rejected before a process is spawned.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Optional

from .magpie_usage_ingest import magpie_executable

# A provider or account name as Magpie prints it: letters, digits, . _ - @ :
_TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@:+-]{0,79}$")
_DURATION = re.compile(r"^(\d+)(s|m|h|d)$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
GRACE_SECONDS = 15.0
DEFAULT_TIMEOUT = "10m"


def parse_duration(value: Any) -> Optional[float]:
    """``"90s"``/``"5m"``/``"2h"``/``"1d"`` -> seconds; ``None`` when malformed."""
    match = _DURATION.match(str(value or "").strip().lower())
    if match is None:
        return None
    amount, unit = match.group(1), match.group(2)
    return float(int(amount) * _UNIT_SECONDS[unit])


def valid_target(target: Any) -> bool:
    return isinstance(target, str) and bool(_TARGET.match(target.strip()))


def wait_for_allowance(target: str, *, timeout: str = DEFAULT_TIMEOUT,
                       exe: Optional[Path] = None,
                       env: Optional[Mapping[str, str]] = None,
                       popen: Any = None,
                       cancel: Any = None,
                       poll_seconds: float = 0.2) -> dict[str, Any]:
    """Block (bounded, cancellable) until ``target`` has allowance.

    Returns ``{"available": bool, "reason": str, "waited_seconds": float|None}``.
    ``reason`` is one of ``allowance_available``, ``timeout``, ``cancelled``,
    ``magpie_error``, ``magpie_not_configured``, ``invalid_target``,
    ``invalid_timeout``.

    ``cancel`` is any object with ``is_set()`` (a ``threading.Event``). It is
    polled every ``poll_seconds`` so an unattended coordinator can stop promptly
    instead of waiting out a multi-minute quota window. Cancellation terminates
    the child — Magpie's wait is idempotent and read-only, so killing it cannot
    corrupt anything.
    """
    if not valid_target(target):
        return {"available": False, "reason": "invalid_target", "waited_seconds": None}
    seconds = parse_duration(timeout)
    if seconds is None:
        return {"available": False, "reason": "invalid_timeout", "waited_seconds": None}
    binary = exe if exe is not None else magpie_executable(env)
    if binary is None:
        return {"available": False, "reason": "magpie_not_configured", "waited_seconds": None}

    command = [str(binary), "quota", "wait", target.strip(), "--timeout", str(timeout), "--quiet"]
    spawn = popen or subprocess.Popen
    import time
    started = time.monotonic()
    deadline = started + seconds + GRACE_SECONDS
    try:
        proc = spawn(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     shell=False, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return {"available": False, "reason": "magpie_error",
                "waited_seconds": round(time.monotonic() - started, 3)}

    def terminate() -> None:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except (OSError, subprocess.SubprocessError, AttributeError):
            try:
                proc.kill()
            except (OSError, subprocess.SubprocessError, AttributeError):
                pass

    while True:
        if cancel is not None and getattr(cancel, "is_set", lambda: False)():
            terminate()
            return {"available": False, "reason": "cancelled",
                    "waited_seconds": round(time.monotonic() - started, 3)}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            terminate()
            return {"available": False, "reason": "timeout",
                    "waited_seconds": round(time.monotonic() - started, 3)}
        try:
            proc.wait(timeout=min(poll_seconds, remaining))
            break
        except subprocess.TimeoutExpired:
            continue
        except (OSError, subprocess.SubprocessError):
            terminate()
            return {"available": False, "reason": "magpie_error",
                    "waited_seconds": round(time.monotonic() - started, 3)}
    waited = round(time.monotonic() - started, 3)
    if getattr(proc, "returncode", 1) == 0:
        return {"available": True, "reason": "allowance_available", "waited_seconds": waited}
    return {"available": False, "reason": "magpie_error", "waited_seconds": waited}
