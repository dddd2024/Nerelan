"""Self-evolution loop: measured feedback into scheduling and cost strategy.

Domain E. This closes the two open items in the planning spec:

  - E1 ``break_even`` persistence + being actually called by the scheduling
    decision. :mod:`orchestration_selector` already holds the decision core and
    the linear break-even model; we only add *persistence* and a *feedback
    loop*. The algorithm is never rewritten.
  - E2 the ``delta_calibration`` usage->cost-rate path already exists in
    :mod:`quota_reservation`; we expose a thin, opt-in hook so measured runs
    keep feeding it (no reimplementation).

Design constraints from the spec: no general RL framework, no unreviewable
parameter drift. Every stored record is JSON-safe and every recomputed
break-even is the deterministic output of :func:`update_break_even`, so the
loop is bounded, explainable and rollback-able (just truncate the store).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from .config import MultiAccountConfig


class SelfEvolutionStore:
    """Append-only ledger of accepted-run outcomes and the measured break-even.

    A ``path`` of ``None`` keeps everything in memory (used by tests and by a
    host that wants to disable local persistence). Otherwise the file is written
    atomically (temp + rename) so a crash mid-write never leaves a half file.

    The document is one JSON object with four sections — ``runs``,
    ``break_even``, ``accounts`` and ``cooldowns`` — so a single atomic write
    keeps account feedback and the mode-level break-even consistent with each
    other, and a single truncate rolls the whole self-evolution loop back.

    ``runs`` is bounded by ``max_recorded_runs``: an unattended run must not grow
    the ledger without limit. Old outcomes still influence the break-even through
    the previous record carried forward by :func:`update_break_even`.
    """

    def __init__(self, config: MultiAccountConfig, *,
                 path: Optional[Path] = None) -> None:
        self._config = config
        self._path = Path(path) if path is not None else None
        self._state = (self._load() if self._path is not None else self._empty())
        # Account feedback (scores/cooldowns) and the mode ledger share one
        # document, so writes are serialized to prevent a torn read-modify-write.
        import threading
        self._lock = threading.RLock()

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {"runs": [], "break_even": None, "accounts": {}, "cooldowns": {},
                "updated_at": None}

    # --- persistence ----------------------------------------------------------
    def _load(self) -> dict[str, Any]:
        if self._path is None or not self._path.exists():
            return self._empty()
        try:
            with self._path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
            if not isinstance(data, dict):
                return self._empty()
            state = self._empty()
            state.update({key: data[key] for key in state if key in data})
            state["runs"] = list(state["runs"])[-self._config.max_recorded_runs:]
            for key in ("accounts", "cooldowns"):
                if not isinstance(state[key], dict):
                    state[key] = {}
            return state
        except (OSError, ValueError):
            # A corrupted ledger must not crash the coordinator; start clean.
            return self._empty()

    def _save_unlocked(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(dir=str(self._path.parent), suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as stream:
                json.dump(self._state, stream, ensure_ascii=False, sort_keys=True)
            os.replace(tmp_name, self._path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def _save(self) -> None:
        with self._lock:
            self._save_unlocked()

    # --- generic section access (used to wire cooldowns / scores) -------------
    def section(self, name: str) -> dict[str, Any]:
        with self._lock:
            value = self._state.get(name)
            return dict(value) if isinstance(value, dict) else {}

    def patch(self, name: str, value: Any) -> None:
        """Replace one section and persist, keeping every other section intact."""
        with self._lock:
            self._state[name] = value
            self._save_unlocked()

    # --- API ------------------------------------------------------------------
    def record_run(self, outcome: Mapping[str, Any], *,
                   now: Optional[float] = None) -> dict[str, Any]:
        """Append one goal outcome and recompute the measured break-even."""
        import time
        now = time.time() if now is None else now
        cleaned = {
            "mode": outcome.get("mode"),
            "accepted": bool(outcome.get("accepted")),
            "cost_units": outcome.get("cost_units"),
            "task_count": outcome.get("task_count"),
            "tokens": outcome.get("tokens"),
            "wall_seconds": outcome.get("wall_seconds"),
            "size_band": outcome.get("size_band"),
            "recorded_at": now,
        }
        with self._lock:
            runs = self._state["runs"]
            runs.append(cleaned)
            overflow = len(runs) - self._config.max_recorded_runs
            if overflow > 0:
                del runs[:overflow]
            self._state["break_even"] = self._recompute_break_even()
            self._state["updated_at"] = now
            self._save_unlocked()
            return self._state["break_even"] or {}

    def _recompute_break_even(self) -> Optional[dict[str, Any]]:
        if not self._config.enable_self_evolution:
            return None
        from ..orchestration_selector import update_break_even
        previous = self._state.get("break_even")
        # The selector's evidence bar already enforces per-mode minimums; we
        # pass the stored previous so a sparse window carries the last good value.
        return update_break_even(self._state["runs"], previous=previous)

    def get_break_even(self) -> Optional[dict[str, Any]]:
        return self._state.get("break_even")

    def get_runs(self) -> list[dict[str, Any]]:
        return list(self._state.get("runs", []))

    def reset(self) -> None:
        """Roll the whole loop back: mode ledger, account feedback, cooldowns."""
        with self._lock:
            self._state = self._empty()
            self._save_unlocked()


class SelfEvolutionLoop:
    """Records outcomes and turns them into orchestration recommendations.

    Two feedback levels share one bounded ledger:

    * **mode level** (``record_outcome`` / ``recommend_mode``) — single agent vs
      team, via the existing :func:`select_orchestration` decision core.
    * **account level** (``record_account_outcome`` / ``account_scores``) —
      reliability, cost and latency per account, via
      :class:`.scoring.AccountScoreboard`.
    """

    def __init__(self, store: SelfEvolutionStore, config: MultiAccountConfig,
                 scoreboard: Optional[Any] = None) -> None:
        self._store = store
        self._config = config
        self._scoreboard = scoreboard

    def record_outcome(self, outcome: Mapping[str, Any], *,
                       now: Optional[float] = None) -> dict[str, Any]:
        return self._store.record_run(outcome, now=now)

    def record_account_outcome(self, account_ref: str, *, ok: bool,
                               cost_units: Optional[float] = None,
                               wall_seconds: Optional[float] = None,
                               failure_kind: Optional[str] = None,
                               now: Optional[float] = None) -> Optional[dict[str, Any]]:
        """Fold one per-account run result into the EWMA scoreboard.

        Disabled by ``enable_account_scoring``; never raises — feedback is
        best-effort and must not fail a landing.
        """
        if self._scoreboard is None or not self._config.enable_account_scoring:
            return None
        try:
            score = self._scoreboard.observe(
                account_ref, ok=ok, cost_units=cost_units, wall_seconds=wall_seconds,
                failure_kind=failure_kind, now=now)
            return score.public_view()
        except Exception:  # noqa: BLE001 - feedback must never break the run
            return None

    def account_scores(self) -> dict[str, dict[str, Any]]:
        if self._scoreboard is None:
            return {}
        return {ref: score.public_view() for ref, score in self._scoreboard.scores().items()}

    def recommend_mode(self, size_estimate: Mapping[str, Any], *,
                       pin: Any = None) -> dict[str, Any]:
        """Pick single vs agent_team from measured evidence (E1 closed)."""
        from ..orchestration_selector import select_orchestration
        return select_orchestration(
            size_estimate=size_estimate,
            break_even=self._store.get_break_even(),
            pin=pin,
        )

    def calibration_feedback(self, before: Any, after: Any,
                            settlements: Iterable[Mapping[str, Any]],
                            *, task_id: str = "multi_account") -> Optional[dict[str, Any]]:
        """Feed measured usage into the existing cost-rate calibration (E2).

        This reuses :func:`quota_reservation.delta_calibration` — the one
        already-closed calibration loop — rather than inventing a new one.
        Returns its record, or ``None`` when disabled or unavailable.
        """
        if not self._config.calibration_feedback_enabled:
            return None
        try:
            from ..quota_reservation import delta_calibration
        except Exception:  # noqa: BLE001 - optional; never block the loop
            return None
        try:
            return delta_calibration(task_id, before, after, list(settlements))
        except Exception:  # noqa: BLE001 - calibration must not break the run
            return None
