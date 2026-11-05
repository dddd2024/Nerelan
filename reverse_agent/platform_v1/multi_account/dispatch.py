"""Dispatch integration seam for the multi-account orchestration brain.

This is the *safe* hand-off between the new brain and the existing dispatch
path (``goal_service`` / ``task_service`` / ``unattended_coordinator``). It never
takes a hard dependency on the brain at import time and every entry point is
guarded: if the brain is unavailable or raises, the caller degrades to the
legacy behaviour instead of breaking dispatch.

The seam is intentionally tiny — the real logic lives in :mod:`config`,
:mod:`status`, :mod:`scheduler` and :mod:`evolution`. Once the R1 review and CI
gates pass, the callers listed in ``MULTI_ACCOUNT_ORCHESTRATION_SPEC.md`` §10.4
call these functions at their seams.
"""
from __future__ import annotations

import threading
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

_ORCHESTRATOR: Any = None
_LOCK = threading.Lock()


def get_orchestrator(store_path: Optional[Path] = None) -> Any:
    """Use configured persistence when enabled; disabled callers stay in memory."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        with _LOCK:
            if _ORCHESTRATOR is None:
                from . import MultiAccountConfig, MultiAccountOrchestrator
                config = MultiAccountConfig.from_env()
                path = store_path
                if path is None and os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") == "1":
                    path = config.break_even_store_path
                _ORCHESTRATOR = MultiAccountOrchestrator(config, store_path=path)
    return _ORCHESTRATOR


def reset_orchestrator() -> None:
    """Drop the cached orchestrator (used by tests and by config reload)."""
    global _ORCHESTRATOR
    with _LOCK:
        _ORCHESTRATOR = None


def recommend_orchestration_mode(size_estimate: Mapping[str, Any], *,
                                 pin: Any = None,
                                 store_path: Optional[Path] = None) -> dict[str, Any]:
    """Measured single-vs-team choice; falls back to the pure default ladder."""
    try:
        return get_orchestrator(store_path).recommend_mode(size_estimate, pin=pin)
    except Exception:  # noqa: BLE001 - brain optional; legacy ladder must still work
        from ..orchestration_selector import select_orchestration
        return select_orchestration(size_estimate=size_estimate, pin=pin)


def record_goal_outcome(outcome: Mapping[str, Any], *,
                        store_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Persist one goal outcome so the break-even loop can learn from it."""
    try:
        return get_orchestrator(store_path).record_outcome(outcome)
    except Exception:  # noqa: BLE001 - learning is best-effort, never blocks landing
        return None


def record_account_outcome(account_ref: Optional[str], *, ok: bool,
                           cost_units: Optional[float] = None,
                           wall_seconds: Optional[float] = None,
                           failure_kind: Optional[str] = None,
                           store_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Per-account feedback for the scheduler (reliability / cost / latency).

    Best-effort by design: an unknown account or an unavailable brain returns
    ``None`` and the caller keeps its existing behaviour.
    """
    if not account_ref:
        return None
    try:
        return get_orchestrator(store_path).record_account_outcome(
            account_ref, ok=ok, cost_units=cost_units, wall_seconds=wall_seconds,
            failure_kind=failure_kind)
    except Exception:  # noqa: BLE001
        return None


def report_account_success(account_ref: Optional[str], *,
                           store_path: Optional[Path] = None) -> None:
    """Clear an account's quiet time and failure streak after a successful run."""
    if not account_ref:
        return
    try:
        get_orchestrator(store_path).on_success(account_ref)
    except Exception:  # noqa: BLE001 - bookkeeping must never block dispatch
        pass


def account_scores(store_path: Optional[Path] = None) -> dict[str, dict[str, Any]]:
    """Read-only view for ``/api/resources``; empty when the brain is off."""
    try:
        return get_orchestrator(store_path).account_scores()
    except Exception:  # noqa: BLE001
        return {}


def idle_wait_seconds(store_path: Optional[Path] = None) -> Optional[float]:
    """Seconds until the earliest account cooldown expires (coordinator hint).

    ``None`` means "no signal, poll normally" — never "wait forever".
    """
    try:
        brain = get_orchestrator(store_path)
        if brain.routing_owner == "magpie":
            # Magpie blocks on allowance itself (`quota wait`); a local sleep
            # hint would only add a second, conflicting wait.
            return None
        return brain.next_retry_in()
    except Exception:  # noqa: BLE001
        return None


def account_routing(store_path: Optional[Path] = None) -> dict[str, Any]:
    """Who selects accounts right now, and why. Defaults to ``local``."""
    try:
        return get_orchestrator(store_path).routing()
    except Exception:  # noqa: BLE001 - an unavailable brain delegates to nothing
        return {"requested": "local", "owner": "local", "reason": "orchestrator_unavailable"}


def select_dispatch_account(statuses: Iterable[Any], *,
                            small_task: bool = False,
                            need: Optional[Mapping[str, Any]] = None,
                            store_path: Optional[Path] = None) -> dict[str, Any]:
    """Account-aware selection; degrades to ``hold`` if the brain is down."""
    try:
        return get_orchestrator(store_path).select(
            statuses, small_task=small_task, need=need)
    except Exception:  # noqa: BLE001
        return {"decision": "hold", "account_ref": None,
                "reason": "orchestrator_unavailable", "evidence": {}}


def reroute_failed_account(statuses: Iterable[Any], *,
                           failed_ref: str, failure_kind: str, attempt: int,
                           small_task: bool = False,
                           store_path: Optional[Path] = None) -> dict[str, Any]:
    """Bounded reroute / dead-letter on quota / account / task failure."""
    try:
        return get_orchestrator(store_path).on_failure(
            statuses, failed_ref=failed_ref, failure_kind=failure_kind,
            attempt=attempt, small_task=small_task)
    except Exception:  # noqa: BLE001
        return {"decision": "hold", "next_account_ref": None,
                "reason": "orchestrator_unavailable", "evidence": {}}


def reroute_guard(statuses: Iterable[Any], account_ref: str) -> dict[str, Any]:
    """Account-aware reroute guard used by ``goal_service._reroute_quota_held``.

    Returns ``{"skip": True}`` only when the candidate account is concretely
    unfit — EXHAUSTED (a window hit 100% / provider rejected) or ABNORMAL
    (account-level error). STALE/UNKNOWN accounts are *not* skipped: when we
    cannot be sure an account is bad we must not block a legitimate reroute. Any
    error or a missing account yields ``skip=False`` so the legacy reroute still
    happens. This keeps the guard strictly additive and safe.
    """
    try:
        owner = account_routing().get("owner")
        if owner == "magpie":
            # Magpie owns account switching; a local health verdict must not
            # override it (that would re-implement the upstream decision).
            return {"skip": False, "health": None, "reason": "routing_delegated_to_magpie"}
        from .status import AccountHealth
        for status in statuses:
            if getattr(status, "account_ref", None) == account_ref:
                if status.health in (AccountHealth.EXHAUSTED, AccountHealth.ABNORMAL):
                    return {"skip": True, "health": status.health.value,
                            "reason": "account_unfit"}
                return {"skip": False, "health": status.health.value, "reason": "account_fit"}
        return {"skip": False, "health": None, "reason": "account_unknown"}
    except Exception:  # noqa: BLE001 - never block the reroute on a guard failure
        return {"skip": False, "health": None, "reason": "guard_error"}
