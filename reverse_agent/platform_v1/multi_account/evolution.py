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
loop is bounded and explainable. Disabling learning stops using its policy
without deleting the evidence ledger.
"""
from __future__ import annotations

import copy
import json
import math
import os
import tempfile
import threading
import weakref
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from .config import MultiAccountConfig

_PATH_LOCKS: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
_PATH_LOCKS_GUARD = threading.Lock()


def _store_lock(path: Optional[Path]):
    """Serialize instances in this host; this is not a cross-process lock."""
    if path is None:
        return threading.RLock()
    key = os.path.normcase(str(path.resolve()))
    with _PATH_LOCKS_GUARD:
        lock = _PATH_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _PATH_LOCKS[key] = lock
        return lock


def _measurement(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) and number >= 0 else None


class SelfEvolutionStore:
    """Bounded ledger of run outcomes and the measured break-even.

    A ``path`` of ``None`` keeps everything in memory (used by tests and by a
    host that wants to disable local persistence). Otherwise the file is written
    atomically (temp + rename) so a crash mid-write never leaves a half file.

    The document is one JSON object with four sections — ``runs``,
    ``break_even``, ``accounts`` and ``cooldowns`` — so a single atomic write
    keeps account feedback and the mode-level break-even consistent with each
    other. Shared-path instances serialize writes inside one host process;
    independent host processes must not share this file.

    ``runs`` is bounded by ``max_recorded_runs``: an unattended run must not grow
    the ledger without limit. Recommendations are recomputed only from retained
    outcomes; pruned samples do not support a future recommendation.
    """

    def __init__(self, config: MultiAccountConfig, *,
                 path: Optional[Path] = None) -> None:
        self._config = config
        self._path = Path(path) if path is not None else None
        self._lock = _store_lock(self._path)
        with self._lock:
            self._state = self._load() if self._path is not None else self._empty()

    @staticmethod
    def _empty() -> dict[str, Any]:
        """Every section the document may hold.

        This is the load whitelist as well as the initial shape: a section
        missing here is *silently dropped on the next restart*, which would
        reset the cost window, the alert dedupe state, the policy chain and the
        run clock after every crash — exactly the failure this store exists to
        prevent.
        """
        return {"runs": [], "break_even": None, "accounts": {}, "cooldowns": {},
                "account_feedback": {}, "budget": {}, "alerts": {}, "policy": {},
                "watchdog": {}, "updated_at": None}

    # --- persistence ----------------------------------------------------------
    def _load(self) -> dict[str, Any]:
        if self._path is None or not self._path.exists():
            return self._empty()
        try:
            with self._path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
            if not isinstance(data, dict):
                raise ValueError("invalid feedback ledger")
            state = self._empty()
            state.update({key: data[key] for key in state if key in data})
            if not isinstance(state["runs"], list):
                raise ValueError("invalid feedback runs")
            if any(not isinstance(row, dict) for row in state["runs"]):
                raise ValueError("invalid feedback run")
            state["runs"] = state["runs"][-self._config.max_recorded_runs:]
            for key in ("accounts", "cooldowns", "account_feedback", "budget", "alerts",
                        "policy", "watchdog"):
                if not isinstance(state[key], dict):
                    raise ValueError("invalid feedback section")
            return state
        except (OSError, ValueError) as exc:
            # The optional dispatch seam handles unavailability; never replace
            # unreadable historical evidence with an apparently empty ledger.
            raise ValueError("feedback ledger unavailable") from exc

    def _save_unlocked(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(dir=str(self._path.parent), suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as stream:
                json.dump(self._state, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
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
    def _refresh_unlocked(self) -> None:
        if self._path is not None:
            self._state = self._load()

    def section(self, name: str) -> dict[str, Any]:
        with self._lock:
            self._refresh_unlocked()
            value = self._state.get(name)
            return copy.deepcopy(value) if isinstance(value, dict) else {}

    def patch(self, name: str, value: Any) -> None:
        """Replace one section and persist, keeping every other section intact."""
        with self._lock:
            self._refresh_unlocked()
            self._state[name] = copy.deepcopy(value)
            self._save_unlocked()

    # --- API ------------------------------------------------------------------
    def record_run(self, outcome: Mapping[str, Any], *,
                   now: Optional[float] = None) -> dict[str, Any]:
        """Append one goal outcome and recompute the measured break-even."""
        import time
        now = time.time() if now is None else now
        if type(outcome.get("accepted")) is not bool:
            raise ValueError("accepted must be a boolean")
        if _measurement(now) is None:
            raise ValueError("recorded_at must be finite and non-negative")
        outcome_id = outcome.get("outcome_id")
        if outcome_id is not None and (not isinstance(outcome_id, str)
                                      or not outcome_id.strip() or len(outcome_id) > 200):
            raise ValueError("outcome_id must be a non-empty string of at most 200 characters")
        tokens = outcome.get("tokens")
        band = outcome.get("size_band")
        if band is not None and (not isinstance(band, str) or len(band) > 80):
            raise ValueError("size_band must be a string of at most 80 characters")
        cleaned = {
            "mode": outcome.get("mode") if outcome.get("mode") in ("single", "agent_team") else None,
            "accepted": outcome["accepted"],
            "cost_units": _measurement(outcome.get("cost_units")),
            "task_count": _measurement(outcome.get("task_count")),
            "tokens": ({role: _measurement(tokens.get(role)) for role in ("planner", "executor", "reviewer")}
                       if isinstance(tokens, Mapping) else None),
            "wall_seconds": _measurement(outcome.get("wall_seconds")),
            "size_band": band,
            "recorded_at": now,
        }
        if outcome_id is not None:
            cleaned["outcome_id"] = outcome_id
        with self._lock:
            self._refresh_unlocked()
            runs = self._state["runs"]
            for row in runs if outcome_id is not None else ():
                if row.get("outcome_id") == outcome_id:
                    if any(row.get(key) != value for key, value in cleaned.items() if key != "recorded_at"):
                        raise ValueError("conflicting outcome_id")
                    return copy.deepcopy(self._recompute_break_even() or {})
            runs.append(cleaned)
            overflow = len(runs) - self._config.max_recorded_runs
            if overflow > 0:
                del runs[:overflow]
            self._state["break_even"] = self._recompute_break_even()
            self._state["updated_at"] = now
            self._save_unlocked()
            return copy.deepcopy(self._state["break_even"] or {})

    def _recompute_break_even(self) -> Optional[dict[str, Any]]:
        if not self._config.enable_self_evolution or not self._state["runs"]:
            return None
        from ..orchestration_selector import update_break_even
        # Recompute from the retained evidence. A cached recommendation from a
        # weaker configuration must not bypass a newly raised sample threshold.
        return update_break_even(self._state["runs"],
                                 min_observations_per_mode=self._config.min_observations_per_mode)

    def get_break_even(self) -> Optional[dict[str, Any]]:
        with self._lock:
            self._refresh_unlocked()
            return copy.deepcopy(self._recompute_break_even())

    def get_runs(self) -> list[dict[str, Any]]:
        with self._lock:
            self._refresh_unlocked()
            return copy.deepcopy(self._state.get("runs", []))

    def record_account_feedback(self, account_ref: str, *, ok: bool,
                                cost_units: Optional[float], wall_seconds: Optional[float],
                                failure_kind: Optional[str], outcome_id: Optional[str],
                                now: float) -> dict[str, Any]:
        """Commit scores, isolation and replay identity in one atomic document.

        The lock covers all same-host instances. A failed replace commits none
        of the transition; retrying the same terminal receipt cannot double-train.
        """
        import hashlib
        from .cooldowns import CooldownRegistry
        from .scoring import AccountScoreboard
        if type(ok) is not bool or _measurement(now) is None:
            raise ValueError("invalid account feedback")
        if not isinstance(account_ref, str) or not account_ref or len(account_ref) > 256:
            raise ValueError("invalid account_ref")
        if outcome_id is not None and (not isinstance(outcome_id, str)
                                      or not outcome_id or len(outcome_id) > 256):
            raise ValueError("invalid outcome_id")
        normalized = {"account_ref": account_ref, "ok": ok,
                      "cost_units": _measurement(cost_units), "wall_seconds": _measurement(wall_seconds),
                      "failure_kind": failure_kind if not ok else None}
        digest = hashlib.sha256(json.dumps(normalized, sort_keys=True, allow_nan=False).encode()).hexdigest()
        with self._lock:
            self._refresh_unlocked()
            previous = self._state
            candidate = copy.deepcopy(previous)
            receipts = candidate["account_feedback"]
            if outcome_id is not None and outcome_id in receipts:
                receipt = receipts[outcome_id]
                if receipt.get("digest") != digest:
                    raise ValueError("conflicting account outcome_id")
                return {"view": copy.deepcopy(receipt.get("view")),
                        "accounts": candidate["accounts"], "cooldowns": candidate["cooldowns"], "replayed": True}
            cooldowns = CooldownRegistry(self._config, state=candidate["cooldowns"], clock=lambda: now)
            scores = AccountScoreboard(self._config, state=candidate["accounts"], clock=lambda: now)
            if ok:
                cooldowns.record_success(account_ref, now=now)
            else:
                cooldowns.record_failure(account_ref, failure_kind or "task_failed", now=now)
            view = None
            if self._config.enable_account_scoring:
                view = scores.observe(account_ref, ok=ok, cost_units=normalized["cost_units"],
                                      wall_seconds=normalized["wall_seconds"],
                                      failure_kind=failure_kind, now=now).public_view()
            candidate["accounts"] = scores.snapshot()
            candidate["cooldowns"] = cooldowns.snapshot()
            if outcome_id is not None:
                receipts[outcome_id] = {"digest": digest, "view": view, "recorded_at": now}
                while len(receipts) > self._config.max_recorded_runs:
                    oldest = min(receipts, key=lambda key: (receipts[key]["recorded_at"], key))
                    del receipts[oldest]
            candidate["updated_at"] = now
            self._state = candidate
            try:
                self._save_unlocked()
            except BaseException:
                self._state = previous
                raise
            return {"view": copy.deepcopy(view), "accounts": copy.deepcopy(candidate["accounts"]),
                    "cooldowns": copy.deepcopy(candidate["cooldowns"]), "replayed": False}

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
            break_even=self._store.get_break_even() if self._config.enable_self_evolution else None,
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
