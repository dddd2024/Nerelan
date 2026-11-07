"""Run watchdog: bounded run duration and idle detection for unattended runs.

Domain D (运行时长). "长时间不间断" needs a definition of *when to stop*. Without
one, an unattended run either ends only when a human kills it, or exits silently
on the first quiet moment. This module supplies the missing contract:

* ``max_run_duration_seconds`` — wall-clock budget of one run. At the budget the
  verdict is ``conclude``: stop *starting* work and let in-flight attempts land
  (no half-written evidence). Past ``watchdog_hard_stop_ratio`` it escalates to
  ``stop``.
* ``max_idle_seconds`` — no completed attempt for that long means there is
  nothing useful to wait for, so conclude instead of sleeping forever.
* Both default to ``0`` = unlimited, so the previous behaviour is unchanged.

The watchdog is pure bookkeeping with an injected clock: it never cancels
anything itself. The caller decides how to finish, which keeps cancellation
semantics in the runtime (:mod:`durable_execution`) where they belong.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Mapping, Optional

from .config import MultiAccountConfig


class RunWatchdog:
    """Tracks elapsed and idle time and returns a bounded run verdict."""

    def __init__(self, config: MultiAccountConfig, *,
                 clock: Callable[[], float] = time.time,
                 state: Optional[Mapping[str, Any]] = None,
                 persist: Optional[Callable[[dict[str, Any]], None]] = None) -> None:
        self._config = config
        self._clock = clock
        self._persist = persist
        self._started_at: Optional[float] = None
        self._last_progress_at: Optional[float] = None
        self._attempts = 0
        self._concluded_at: Optional[float] = None
        self.load(state)

    # --- lifecycle ------------------------------------------------------------
    def start(self, *, now: Optional[float] = None) -> dict[str, Any]:
        """Begin (or restart) the timed window; a no-op when disabled."""
        now = self._clock() if now is None else now
        self._started_at = now
        self._last_progress_at = now
        self._attempts = 0
        self._concluded_at = None
        self._save()
        return self.status(now=now)

    def heartbeat(self, *, now: Optional[float] = None) -> None:
        """Record that one attempt completed (success *or* terminal failure).

        A failed attempt still counts as progress: the run is doing work and
        should not be concluded just because the work is failing — that is what
        cooldowns and dead-letter are for.
        """
        now = self._clock() if now is None else now
        if self._started_at is None:
            self._started_at = now
        self._last_progress_at = now
        self._attempts += 1
        self._save()

    def conclude(self, *, now: Optional[float] = None) -> None:
        """Mark the run as concluded so :meth:`check` stops asking for more work."""
        now = self._clock() if now is None else now
        self._concluded_at = now
        self._save()

    # --- verdict --------------------------------------------------------------
    def check(self, *, now: Optional[float] = None) -> dict[str, Any]:
        """Return ``continue`` / ``conclude`` / ``stop`` with the reason.

        Precedence is hard-stop, then deadline, then idle, so the most severe
        condition names the verdict.
        """
        now = self._clock() if now is None else now
        status = self.status(now=now)
        if not self._config.watchdog_enabled:
            return {**status, "action": "continue", "reason": "watchdog_disabled"}
        if self._concluded_at is not None:
            return {**status, "action": "conclude", "reason": "already_concluded"}

        deadline = self._config.max_run_duration_seconds
        if deadline > 0:
            elapsed = status["elapsed_seconds"]
            if elapsed >= deadline * self._config.watchdog_hard_stop_ratio:
                return {**status, "action": "stop", "reason": "hard_deadline_exceeded"}
            if elapsed >= deadline:
                return {**status, "action": "conclude", "reason": "run_deadline_reached"}

        idle_limit = self._config.max_idle_seconds
        if idle_limit > 0:
            idle = status["idle_seconds"]
            if idle >= idle_limit:
                return {**status, "action": "conclude", "reason": "idle_timeout"}
        return {**status, "action": "continue", "reason": "within_budget"}

    def should_dispatch(self, *, now: Optional[float] = None) -> bool:
        """``True`` only while the run may start new work."""
        return self.check(now=now)["action"] == "continue"

    def remaining_seconds(self, *, now: Optional[float] = None) -> Optional[float]:
        """Seconds left before the deadline; ``None`` when unlimited.

        Bounded so a coordinator can size its idle sleep without overshooting
        the deadline it is supposed to honour.
        """
        if self._config.max_run_duration_seconds <= 0:
            return None
        now = self._clock() if now is None else now
        if self._started_at is None:
            return float(self._config.max_run_duration_seconds)
        left = self._config.max_run_duration_seconds - (now - self._started_at)
        return max(0.0, left)

    def status(self, *, now: Optional[float] = None) -> dict[str, Any]:
        now = self._clock() if now is None else now
        elapsed = 0.0 if self._started_at is None else max(0.0, now - self._started_at)
        idle = (0.0 if self._last_progress_at is None
                else max(0.0, now - self._last_progress_at))
        return {
            "enabled": bool(self._config.watchdog_enabled),
            "started_at": self._started_at,
            "elapsed_seconds": round(elapsed, 3),
            "idle_seconds": round(idle, 3),
            "attempts": self._attempts,
            "max_run_duration_seconds": self._config.max_run_duration_seconds,
            "max_idle_seconds": self._config.max_idle_seconds,
            "remaining_seconds": self.remaining_seconds(now=now),
            "concluded_at": self._concluded_at,
        }

    # --- persistence (host restarts keep the budget honest) --------------------
    def snapshot(self) -> dict[str, Any]:
        return {"started_at": self._started_at, "last_progress_at": self._last_progress_at,
                "attempts": self._attempts, "concluded_at": self._concluded_at}

    def load(self, state: Optional[Mapping[str, Any]]) -> None:
        if not isinstance(state, Mapping):
            return
        for field, attr in (("started_at", "_started_at"),
                            ("last_progress_at", "_last_progress_at"),
                            ("concluded_at", "_concluded_at")):
            value = state.get(field)
            if isinstance(value, (int, float)):
                setattr(self, attr, float(value))
        attempts = state.get("attempts")
        if isinstance(attempts, int) and attempts >= 0:
            self._attempts = attempts

    def _save(self) -> None:
        if self._persist is None:
            return
        try:
            self._persist(self.snapshot())
        except Exception:  # noqa: BLE001 - bookkeeping must never break the run
            pass
