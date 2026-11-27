"""Host wiring for real resource settlement (#1531).

Reuses the existing positive-identity Magpie usage reader
(:mod:`reverse_agent.model_access.magpie_usage`) and interval credit settlement
(:mod:`reverse_agent.model_access.magpie_settlement`) rather than duplicating
gateway clients or inventing heuristic time-window spend splits.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..model_access.magpie import magpie_enabled
from ..model_access.magpie_settlement import reconcile_account_interval
from ..model_access.magpie_usage import correlate_task_usage, fetch_usage_requests

_logger = logging.getLogger(__name__)

# Pre-dispatch refusals / setup blocks where no executor ever ran a model call.
PRE_DISPATCH_ZERO_CLASSES = frozenset({
    "review_not_independent",
    "no_runnable_model",
    "pinned_model_unavailable",
    "no_willing_model",
    "policy_denied",
    "executor_unavailable",
    "review_transport_unsupported",
})


def is_confirmed_pre_dispatch_zero(conn: Any, task_id: str, task_row: Mapping[str, Any]) -> bool:
    """True only when failure occurred before any executor run was started.

    Requires BOTH an explicit pre-dispatch classification (or pre-worktree
    preparation block) AND zero ``EXECUTOR_RUNNING``/``EXECUTOR_COMPLETED``
    events so genuine mid-run crashes never collapse to ``$0``.
    """
    classification = str(task_row["failure_classification"] or "").strip()
    detail = str(task_row["failure_detail"] or "").strip() if "failure_detail" in task_row.keys() else ""
    eligible_failure = classification in PRE_DISPATCH_ZERO_CLASSES or (
        classification == "blocked" and detail.startswith("worktree_preparation_failed:")
    )
    if not eligible_failure:
        return False
    executed = conn.execute(
        "SELECT 1 FROM task_events WHERE task_id = ? "
        "AND type IN ('EXECUTOR_RUNNING', 'EXECUTOR_COMPLETED') LIMIT 1",
        (task_id,),
    ).fetchone()
    return executed is None


def task_positive_identities(store: Any, task_id: str) -> tuple[list[str], list[str]]:
    """Collect positive Magpie join keys (``agent_session_id`` and ``request_id``s)."""
    sessions: list[str] = []
    rids: list[str] = []
    seen_sessions: set[str] = set()
    seen_rids: set[str] = set()
    rows = store._conn.execute(
        "SELECT metadata FROM task_events WHERE task_id = ? "
        "AND type IN ('EXECUTOR_COMPLETED', 'EXECUTOR_FINISHED', 'EXECUTOR_RUNNING', "
        "'STREAM_ABORT_CONFIRMED', 'STREAM_ABORT_UNKNOWN') "
        "ORDER BY seq ASC",
        (task_id,),
    ).fetchall()
    for row in rows:
        try:
            meta = json.loads(row["metadata"] or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(meta, Mapping):
            continue
        session = meta.get("agent_session_id")
        if isinstance(session, str):
            session = session.strip()
            if session and session not in seen_sessions:
                seen_sessions.add(session)
                sessions.append(session)
        raw_rids = meta.get("request_ids") or meta.get("rids") or ()
        rid_candidates: list[Any] = list(raw_rids) if isinstance(raw_rids, (list, tuple)) else []
        for singular_key in ("request_id", "rid"):
            if singular_key in meta:
                rid_candidates.append(meta.get(singular_key))
        for rid in rid_candidates:
            if isinstance(rid, str):
                rid = rid.strip()
                if rid and rid not in seen_rids:
                    seen_rids.add(rid)
                    rids.append(rid)
    return sessions, rids


def reconcile_task_usage_from_magpie(
    store: Any,
    task: Any,
    *,
    env: Mapping[str, str] | None = None,
    magpie_url: str | None = None,
    usage_rows: Iterable[Mapping[str, Any]] | None = None,
    usage_fetcher: Callable[..., Mapping[str, Any]] | None = None,
    complete: bool = True,
) -> dict[str, Any]:
    """Backfill/reconcile missing, incomplete, or unpriced task usage via Magpie.

    Zero network calls when ``REVERSE_AGENT_MAGPIE`` is not ``1`` (unless test
    inputs ``usage_rows`` or ``usage_fetcher`` are supplied directly).
    Never sums Magpie rows with local observations for the same execution, and
    never emits a superseding ``magpie_measured`` observation when gateway usage
    coverage is incomplete (``complete is not True``).
    """
    active_env = env if env is not None else os.environ
    task_id = str(getattr(task, "id", "") or "")
    if not task_id:
        return {"status": "skipped", "reason": "missing_task_id"}
    if usage_rows is None and usage_fetcher is None and not magpie_enabled(active_env):
        return {"status": "skipped", "reason": "magpie_disabled"}

    local_rows = store._conn.execute(
        "SELECT id, execution_id, role, model_id, provider_id, source_kind, status, "
        "input_units, output_units, reasoning_units, cache_read_units, cache_write_units, "
        "cost_micro_units FROM task_usage_observations WHERE task_id = ? "
        "ORDER BY created_at ASC, id ASC",
        (task_id,),
    ).fetchall()
    local_dicts = [dict(row) for row in local_rows]
    execution_id = str(getattr(task, "execution_id", "") or "exec-unknown")

    # Skip unnecessary gateway reads when the current execution already has a
    # complete OBSERVED record with known cost (or a magpie_measured record).
    if any(
        row["source_kind"] == "magpie_measured" and row["execution_id"] == execution_id
        for row in local_dicts
    ):
        return {"status": "skipped", "reason": "already_reconciled"}
    if local_dicts and all(
        row["status"] == "OBSERVED"
        and row["cost_micro_units"] is not None
        and all(
            row[col] is not None
            for col in ("input_units", "output_units", "reasoning_units", "cache_read_units", "cache_write_units")
        )
        for row in local_dicts
    ):
        return {"status": "skipped", "reason": "local_complete"}

    sessions, rids = task_positive_identities(store, task_id)
    if not sessions and not rids:
        return {"status": "skipped", "reason": "no_positive_identity"}

    if usage_rows is not None:
        if complete is not True:
            return {"status": "incomplete", "reason": "incomplete_gateway_coverage"}
        fetched_rows = list(usage_rows)
    else:
        url = magpie_url or active_env.get("REVERSE_AGENT_MAGPIE_URL", "http://127.0.0.1:3425")
        fetcher = usage_fetcher or fetch_usage_requests
        payload = fetcher(base_url=url)
        if not isinstance(payload, Mapping) or payload.get("status") != "ok":
            reason = payload.get("reason") if isinstance(payload, Mapping) else "fetch_failed"
            return {"status": "unavailable", "reason": str(reason or "fetch_failed")}
        if payload.get("complete") is not True:
            return {"status": "incomplete", "reason": "incomplete_gateway_coverage"}
        fetched_rows = list(payload.get("rows") or ())

    correlated = correlate_task_usage(local_dicts, fetched_rows, sessions=sessions, rids=rids)
    if correlated.get("basis") != "magpie_measured" or correlated.get("request_count", 0) <= 0:
        return {"status": "no_match", "reason": "no_matching_magpie_requests"}

    totals = correlated["totals"]
    req_rows = correlated.get("requests") or ()
    rid_key = sorted(str(r.get("rid") or r.get("session") or "") for r in req_rows if (r.get("rid") or r.get("session")))
    if not rid_key:
        rid_key = [*sorted(sessions), *sorted(rids)]
    digest = hashlib.sha256(json.dumps({"execution_id": execution_id, "keys": rid_key}, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    observation_id = f"magpie-{task_id[-12:]}-{digest}"
    source_id = f"magpie-req-{digest}"

    token_keys = ("input", "output", "reasoning", "cache_read", "cache_write")
    all_tokens_present = all(
        isinstance(totals.get(k), int) and not isinstance(totals.get(k), bool) and totals[k] >= 0
        for k in token_keys
    )
    unpriced_calls = int(totals.get("unpriced_calls") or 0)
    cost_usd = totals.get("cost_usd")
    if unpriced_calls == 0 and isinstance(cost_usd, (int, float)) and cost_usd >= 0:
        cost_micro_units: int | None = int(round(float(cost_usd) * 1_000_000))
    else:
        cost_micro_units = None

    obs_status = "OBSERVED" if all_tokens_present else "PARTIAL"
    served_models = sorted((correlated.get("served_models") or {}).keys())
    model_id = str(getattr(task, "binding_ref", "") or (served_models[0] if served_models else "magpie-measured"))
    accounts = sorted((correlated.get("accounts") or {}).keys())
    provider_id = f"magpie:{accounts[0]}" if len(accounts) == 1 else "magpie"
    safe_provider = "".join(ch if ch.isalnum() or ch in "._:/@-" else "_" for ch in provider_id)[:120]
    safe_model = "".join(ch if ch.isalnum() or ch in "._:/@-" else "_" for ch in model_id)[:120] or "magpie"

    kwargs: dict[str, Any] = {
        "observation_id": observation_id,
        "execution_id": execution_id,
        "role": "executor",
        "model_id": safe_model,
        "provider_id": safe_provider,
        "source_kind": "magpie_measured",
        "source_id": source_id,
        "status": obs_status,
        "input_units": totals.get("input"),
        "output_units": totals.get("output"),
        "reasoning_units": (int(totals.get("reasoning") or 0) if obs_status == "OBSERVED" else totals.get("reasoning")),
        "cache_read_units": totals.get("cache_read"),
        "cache_write_units": totals.get("cache_write"),
        "cost_micro_units": cost_micro_units,
    }
    if obs_status == "OBSERVED" and kwargs["cache_read_units"] is None:
        kwargs["cache_read_units"] = 0
    if obs_status == "OBSERVED" and kwargs["cache_write_units"] is None:
        kwargs["cache_write_units"] = 0

    try:
        store.append_usage_observation(task_id, **kwargs)
    except Exception:  # noqa: BLE001 - observation mismatch/collision must not crash coordinator
        _logger.debug("magpie usage observation append skipped for %s", task_id, exc_info=True)
        return {"status": "skipped", "reason": "record_rejected"}

    return {
        "status": "reconciled",
        "observation_id": observation_id,
        "observation_status": obs_status,
        "requests": int(totals.get("requests") or 0),
        "unpriced_calls": unpriced_calls,
        "cost_micro_units": cost_micro_units,
    }


def settle_account_interval_from_store(
    store: Any,
    *,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    magpie_rows: Iterable[Mapping[str, Any]],
    account_ref: str,
    window_id: str | None = None,
    credit_conversion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Reconcile an account's before/after credit delta via ``magpie_settlement``.

    Uses active/historical ``platform_budget_reservations`` for ``account_ref``
    to enforce the verified-exclusive overlap check and positive-identity
    ``correlate_task_usage`` for each bound task attempt.
    """
    rows = list(magpie_rows)
    res_rows = [
        dict(r)
        for r in store._conn.execute(
            "SELECT task_id, account_ref, window_id, created_at, reconciled_at "
            "FROM platform_budget_reservations WHERE account_ref = ?",
            (account_ref,),
        ).fetchall()
    ]
    scoped = [r for r in res_rows if window_id is None or r.get("window_id") == window_id]
    task_ids = list(dict.fromkeys(str(r["task_id"]) for r in scoped if r.get("task_id")))

    task_usages: list[dict[str, Any]] = []
    attributed_rids: set[str] = set()
    for tid in task_ids:
        sessions, rids = task_positive_identities(store, tid)
        if not sessions and not rids:
            continue
        local_obs = [
            dict(o)
            for o in store._conn.execute(
                "SELECT * FROM task_usage_observations WHERE task_id = ?",
                (tid,),
            ).fetchall()
        ]
        corr = correlate_task_usage(local_obs, rows, sessions=sessions, rids=rids)
        if corr["request_count"] <= 0:
            continue
        for req in corr["requests"]:
            if isinstance(req.get("rid"), str) and req["rid"]:
                attributed_rids.add(req["rid"])
        totals = corr["totals"]
        task_usages.append({
            "task_id": tid,
            "account_ref": account_ref,
            "coverage": "identity_bound",
            "requests": totals["requests"],
            "tokens": {
                k: totals.get(k)
                for k in ("input", "output", "cache_read", "cache_write", "cache_write_1h", "reasoning")
            },
            "cost_usd": totals.get("cost_usd"),
            "priced": totals.get("unpriced_calls", 0) == 0 and totals.get("cost_usd") is not None,
        })

    unattributed_rows = sum(
        1 for row in rows
        if isinstance(row, Mapping)
        and not row.get("handed_on")
        and (not row.get("rid") or row.get("rid") not in attributed_rids)
    )
    # Exclude settled tasks inside task_usages from `other_reservations`; siblings stay checked.
    settled_ids = {t["task_id"] for t in task_usages}
    other_reservations = [
        {"account_ref": r["account_ref"], "created_at": r["created_at"], "reconciled_at": r["reconciled_at"]}
        for r in res_rows
        if r.get("task_id") not in settled_ids
    ]
    return reconcile_account_interval(
        before,
        after,
        task_usages=task_usages,
        other_reservations=other_reservations,
        unattributed_request_rows=unattributed_rows,
        credit_conversion=credit_conversion,
    )
