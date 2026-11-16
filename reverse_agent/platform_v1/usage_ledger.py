"""One token ledger for every executor (P0-3, provider-free observation).

Executors count tokens differently. OpenCode records non-cached input, cache
reads/writes and reasoning separately from output (``task_usage_observations``). Codex reports ``input_tokens``
*including* the cached part. Claude Code reports non-cached input and cache reads and
writes separately. Here every finished task becomes the same five counters, so totals
and prices compare like with like:

    input        non-cached input tokens
    cache_read   input tokens served from the provider's prompt cache
    cache_write  input tokens written to the prompt cache (None when the CLI did not say)
    output       output tokens (reasoning included, as providers bill it)
    reasoning    the reasoning part of ``output`` when reported, informational only

Nothing here reads provider output beyond the persisted, allowlisted event metadata.
"""

from __future__ import annotations

from contextlib import nullcontext
from functools import wraps
import json
import math
from typing import Any, Mapping

OK_STATUSES = frozenset({"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "COMPLETED"})
COUNTERS = ("input", "cache_read", "cache_write", "output", "reasoning")

# Cost-equivalent weights (#1504): a window's token budget is charged in
# weighted units, not the raw counter sum, so a prompt-cache read (about 10%
# of fresh input's list price on most providers) no longer exhausts a window
# as fast as fresh input. Module constants; a window policy may override
# individual counters later.
COST_EQUIVALENT_WEIGHTS: dict[str, float] = {
    "input": 1.0,
    "cache_read": 0.1,
    "cache_write": 1.25,
    "output": 1.0,
    "reasoning": 1.0,
}
_UNIT_FIELDS = {
    "input": "input_units",
    "cache_read": "cache_read_units",
    "cache_write": "cache_write_units",
    "output": "output_units",
    "reasoning": "reasoning_units",
}


def cost_equivalent_units(
    observation: Any,
    weights: Mapping[str, float] | None = None,
    *,
    unknown_as_zero: bool = False,
) -> int | None:
    """Cost-equivalent token units of one usage observation (#1504).

    Fresh input counts 1.0, a cache read 0.1, a cache write 1.25 and output
    1.0. OpenCode reports reasoning beside output, so it counts 1.0 too;
    ``native_summary`` rows already fold reasoning into output and must not
    count it twice (the per-executor rules above). An override mapping
    replaces only the counters it names. Unknown usage stays unknown
    (``None``, never a silent zero); ``unknown_as_zero`` serves only the
    Owner window's partial-reading fallback charge, which by Owner decision
    2026-11-08 charges what partial readings say with the reservation as
    the floor. Accepts mappings and ``sqlite3.Row`` observations.
    """
    if not isinstance(observation, Mapping):
        try:
            observation = dict(observation)
        except (TypeError, ValueError):
            return None
    if not isinstance(observation, Mapping):
        return None
    charged = {**COST_EQUIVALENT_WEIGHTS, **(weights or {})}
    if observation.get("status") != "OBSERVED" and not unknown_as_zero:
        return None
    total = 0.0
    for counter, weight in charged.items():
        value = _int(observation.get(_UNIT_FIELDS.get(counter, f"{counter}_units")))
        if value is None:
            if not unknown_as_zero:
                return None
            continue
        if counter == "reasoning" and observation.get("source_kind") == "native_summary":
            continue
        total += value * weight
    return int(math.floor(total + 0.5))


def _store_locked(function):
    """Read through the TaskStore's own lock.

    The store shares one SQLite connection across the host's threads. Reading it
    unlocked while the coordinator writes interleaves cursors: a planning request
    then sees another query's rows or a half-written reservation (2026-11-14).
    The lock is re-entrant, so callers that already hold it are unaffected.
    """
    @wraps(function)
    def locked(store: Any, *args: Any, **kwargs: Any) -> Any:
        with getattr(store, "_lock", None) or nullcontext():
            return function(store, *args, **kwargs)
    return locked


def _int(value: Any) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _native(usage: dict[str, Any], executor_kind: str) -> dict[str, int | None] | None:
    total_in, cached, output = (_int(usage.get(key)) for key in ("input_tokens", "cached_input_tokens", "output_tokens"))
    if total_in is None or output is None:
        return None
    cached = cached or 0
    if executor_kind == "codex":
        # OpenAI usage counts cached tokens inside input_tokens.
        return {"input": max(total_in - cached, 0), "cache_read": cached, "cache_write": None,
                "output": output, "reasoning": _int(usage.get("reasoning_output_tokens"))}
    return {"input": total_in, "cache_read": cached, "cache_write": _int(usage.get("cache_write_input_tokens")),
            "output": output, "reasoning": None}


@_store_locked
def task_token_records(store: Any, *, limit: int = 500) -> list[dict[str, Any]]:
    """Normalized token counters for the most recent ``limit`` finished, model-backed tasks."""
    conn = store._conn
    tasks = conn.execute(
        "SELECT id, binding_ref, executor_kind, status FROM tasks WHERE binding_ref <> '' "
        "AND status IN ({}) ORDER BY rowid DESC LIMIT ?".format(",".join("?" * (len(OK_STATUSES) + 1))),
        (*sorted(OK_STATUSES), "FAILED", limit)).fetchall()
    ids = [row["id"] for row in tasks]
    marks = ",".join("?" * len(ids))
    observed: dict[str, dict[str, int | None]] = {}
    for row in conn.execute(
            "SELECT task_id, SUM(input_units) AS input, SUM(cache_read_units) AS cache_read, "
            "SUM(cache_write_units) AS cache_write, SUM(output_units) AS output, "
            "SUM(reasoning_units) AS reasoning, COUNT(input_units) AS known "
            f"FROM task_usage_observations WHERE status = 'OBSERVED' AND task_id IN ({marks}) GROUP BY task_id", ids):
        if row["known"] and row["output"] is not None:
            counters = {key: (int(row[key]) if row[key] is not None else None) for key in COUNTERS}
            counters["cache_read"] = counters["cache_read"] or 0
            # OpenCode counts reasoning beside output, not inside it (often reasoning > output);
            # providers bill reasoning as output, so fold it in and keep the part for reference.
            counters["output"] += counters["reasoning"] or 0
            observed[row["task_id"]] = counters
    completion: dict[str, dict[str, Any]] = {}
    for row in conn.execute(f"SELECT task_id, metadata FROM task_events WHERE type = 'EXECUTOR_COMPLETED' "
                            f"AND task_id IN ({marks}) ORDER BY seq", ids):
        try:
            metadata = json.loads(row["metadata"] or "{}")
        except (ValueError, TypeError):
            continue
        if isinstance(metadata, dict):
            completion[row["task_id"]] = metadata
    records = []
    for row in tasks:
        meta = completion.get(row["id"], {})
        counters = observed.get(row["id"])
        source = "usage_observation"
        if counters is None and isinstance(meta.get("token_usage"), dict):
            counters, source = _native(meta["token_usage"], row["executor_kind"]), "executor_completed"
        models = [name for name in meta.get("models", []) if isinstance(name, str)][:8]
        cost = meta.get("cli_reported_cost_usd")
        records.append({
            "task_id": row["id"], "binding_ref": row["binding_ref"], "executor_kind": row["executor_kind"],
            "ok": row["status"] in OK_STATUSES, "tokens": counters, "source": source if counters else None,
            "models": models, "kind": "code", "difficulty": "unknown",
            "observed_at": meta.get("observed_at"), "turn_count": _int(meta.get("turn_count")),
            "cli_reported_cost_usd": float(cost) if type(cost) in (int, float) and cost >= 0 else None,
        })
    return records


@_store_locked
def estimation_records(store: Any, *, limit: int = 500) -> list[dict[str, Any]]:
    """Claim-level measured history without changing the task accounting projection."""
    records = task_token_records(store, limit=limit)
    conn = store._conn
    # Claim snapshots are the durable training boundary, including failed attempts.
    table = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='platform_budget_reservations'").fetchone()
    if table:
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(platform_budget_reservations)")}
        if "settlement_json" in columns:
            learned = []
            for row in conn.execute("SELECT * FROM platform_budget_reservations WHERE state<>'ACTIVE' ORDER BY rowid DESC LIMIT ?", (limit,)):
                try:
                    fact = json.loads(row["settlement_json"])
                except (TypeError, ValueError):
                    continue  # a reservation without a readable settlement teaches nothing
                if not isinstance(fact, dict):
                    continue
                estimate = fact.get("estimate", {}).get("estimate", {})
                if not estimate or not fact.get("tokens") or any(fact["tokens"].get(k) is None for k in ("input", "cache_read", "output")):
                    continue
                learned.append({"task_id": row["task_id"], "claim_epoch": row["claim_epoch"],
                    "binding_ref": row["binding_ref"], "kind": estimate.get("kind", "code"),
                    "difficulty": estimate.get("difficulty", "unknown"), "ok": False, "measured": True,
                    "tokens": fact["tokens"], "turn_count": fact["turn_count"],
                    "observed_at": row["reconciled_at"], "source": "claim_settlement",
                    "models": [], "cli_reported_cost_usd": None})
            trained = {r["task_id"] for r in learned}
            records = [r for r in records if r["task_id"] not in trained] + learned
    return records


@_store_locked
def latest_rate_limits(store: Any, binding_refs: list[str], *, limit: int = 200) -> tuple[list, str] | None:
    """The newest persisted ``rate_limits`` notices among tasks of these bindings, with their time."""
    if not binding_refs:
        return None
    marks = ",".join("?" * len(binding_refs))
    for row in store._conn.execute(
            f"SELECT e.metadata, e.timestamp FROM task_events e JOIN tasks t ON t.id = e.task_id "
            f"WHERE e.type = 'EXECUTOR_COMPLETED' AND t.binding_ref IN ({marks}) "
            f"ORDER BY e.timestamp DESC LIMIT ?", (*binding_refs, limit)):
        try:
            notices = json.loads(row["metadata"] or "{}").get("rate_limits")
        except (ValueError, TypeError, AttributeError):
            continue
        if isinstance(notices, list) and notices:
            return notices, row["timestamp"]
    return None


@_store_locked
def task_feedback_metrics(store: Any, task_id: str) -> dict[str, Any]:
    """List-price cost (USD) and wall time of one task, for per-account feedback.

    The multi-account scheduler ranks accounts by *relative* cost, so this
    reuses the same normalized counters and list prices as
    :func:`quota_guard.typical_task_units` instead of inventing a second cost
    model. It is deliberately one task at a time — it is called once per finished
    attempt, never in a loop over history.

    A completed coordinator claim restricts usage to its exact window/epoch and
    returns the account captured by its reservation plus a stable outcome id.
    One unknown model or missing token counter keeps the whole cost UNKNOWN.
    Manual task lifetime remains available for reporting, labelled as including
    waits; it is not an attempt's response latency. Completed claims may instead
    expose a monotonic executor interval recorded by the host in their fenced
    settlement. Missing/recovered intervals stay UNKNOWN, not task age.

    ``cost_units`` is a **list-price estimate**, not
    money billed: Magpie's ``usage --csv`` carries the real per-request
    ``cost_usd`` and is the preferred cash source when it is available
    (see docs/architecture/MAGPIE_CAPABILITY_AUDIT_2026-11-04.md). Unknown prices
    or missing telemetry yield ``None`` for that field: an unpriced task must not
    be counted as free.
    """
    metrics: dict[str, Any] = {"cost_units": None, "wall_seconds": None,
                              "basis": "list_price", "cost_state": "UNKNOWN",
                              "scope": "unavailable", "outcome_id": None, "account_ref": None,
                              "wall_time_basis": "task_lifetime_including_waits"}
    if not task_id:
        return metrics
    conn = store._conn
    try:
        from ..model_access.pricing import equivalent_cost
        import math
        tables = {row["name"] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('platform_coordinator_claims', 'platform_budget_reservations')")}
        claim = (conn.execute("SELECT window_id, epoch, status FROM platform_coordinator_claims WHERE task_id=?",
                              (task_id,)).fetchone() if "platform_coordinator_claims" in tables else None)
        params: tuple = (task_id,)
        where = "task_id=? AND claim_epoch=0"
        metrics["scope"] = "task"
        if claim is not None:
            metrics["scope"] = "incomplete_claim"
            # This callback runs after completion. Never substitute another
            # epoch, a live binding's changed identity, or an unfinished claim.
            if claim["status"] != "COMPLETE" or "platform_budget_reservations" not in tables:
                return metrics
            reservation = conn.execute(
                "SELECT account_ref, state, estimate_json, settlement_json FROM platform_budget_reservations "
                "WHERE task_id=? AND window_id=? AND claim_epoch=?",
                (task_id, claim["window_id"], claim["epoch"])).fetchone()
            if reservation is None or reservation["state"] not in {"RECONCILED", "UNKNOWN", "OVERRUN"}:
                return metrics
            frozen = json.loads(reservation["estimate_json"] or "{}").get("feedback_identity", {})
            frozen_account = reservation["account_ref"] or frozen.get("account_ref")
            metrics.update(scope="claim_attempt", account_ref=frozen_account or None,
                           outcome_id=f"{task_id}:{claim['window_id']}:{claim['epoch']}",
                           wall_time_basis="UNKNOWN")
            wall = _settled_attempt_seconds(reservation["settlement_json"])
            if wall is not None:
                metrics.update(wall_seconds=wall, wall_time_basis="attempt_elapsed")
            where = "task_id=? AND window_id=? AND claim_epoch=?"
            params = (task_id, claim["window_id"], claim["epoch"])
        rows = conn.execute(
            "SELECT model_id, status, input_units, cache_read_units, cache_write_units, "
            f"output_units, reasoning_units FROM task_usage_observations WHERE {where}", params).fetchall()
        total = 0.0
        unknown = 0
        groups: dict[str, dict[str, Any]] = {}
        for row in rows:
            fields = ("input_units", "cache_read_units", "cache_write_units", "output_units", "reasoning_units")
            if row["status"] not in {"OBSERVED", "PARTIAL"} or any(_int(row[key]) is None for key in fields):
                unknown += 1
                continue
            counters = {"input": row["input_units"], "cache_read": row["cache_read_units"],
                        "cache_write": row["cache_write_units"],
                        "output": row["output_units"] + row["reasoning_units"]}
            group = groups.setdefault(row["model_id"] or "", {"count": 0,
                "tokens": {key: 0 for key in counters}})
            group["count"] += 1
            for key, value in counters.items():
                group["tokens"][key] += value
        # Price after aggregation: the shared price core rounds USD to six
        # decimals, so rounding every tiny streaming row would erase real cost.
        for model, group in groups.items():
            usd = equivalent_cost(model, group["tokens"]).get("usd")
            if type(usd) not in (int, float) or not math.isfinite(usd) or usd < 0:
                unknown += group["count"]
                continue
            total += usd
        metrics.update(observation_count=len(rows), unpriced_observations=unknown)
        if rows and not unknown and math.isfinite(total):
            metrics.update(cost_units=round(total, 6), cost_state="ESTIMATED_LIST_PRICE")
    except Exception:  # noqa: BLE001 - feedback must never break a finished task
        metrics["cost_units"] = None
    try:
        row = conn.execute("SELECT created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is not None and metrics["scope"] == "task":
            metrics["wall_seconds"] = _elapsed_seconds(row["created_at"], row["updated_at"])
    except Exception:  # noqa: BLE001
        metrics["wall_seconds"] = None
    return metrics


def _settled_attempt_seconds(raw: Any) -> float | None:
    import math
    try:
        timing = json.loads(raw or "{}").get("attempt_metrics", {})
        wall = timing.get("wall_seconds")
        if (type(timing.get("schema_version")) is int and timing["schema_version"] == 1
                and timing.get("state") == "OBSERVED" and timing.get("basis") == "executor_attempt_elapsed"
                and type(wall) in (int, float) and math.isfinite(wall) and wall >= 0):
            return float(wall)
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        pass
    return None


def _elapsed_seconds(start: Any, end: Any) -> float | None:
    from datetime import datetime
    try:
        first = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        last = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    seconds = (last - first).total_seconds()
    return round(seconds, 3) if seconds >= 0 else None


def binding_token_totals(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per binding: summed counters, how many tasks reported tokens, and the models seen."""
    totals: dict[str, dict[str, Any]] = {}
    for record in records:
        entry = totals.setdefault(record["binding_ref"], {
            **dict.fromkeys(COUNTERS, 0), "tasks": 0, "tasks_with_tokens": 0,
            "cache_write_unknown_tasks": 0, "models": {}, "cli_reported_cost_usd": None})
        entry["tasks"] += 1
        tokens = record["tokens"]
        if not tokens:
            continue
        entry["tasks_with_tokens"] += 1
        for key in COUNTERS:
            entry[key] += tokens.get(key) or 0
        if tokens.get("cache_write") is None:
            entry["cache_write_unknown_tasks"] += 1
        # Attribute the task's tokens to the one concrete model it reported, if exactly one.
        model = record["models"][0] if len(record["models"]) == 1 else ""
        per_model = entry["models"].setdefault(model, dict.fromkeys(COUNTERS, 0))
        for key in COUNTERS:
            per_model[key] += tokens.get(key) or 0
        if record["cli_reported_cost_usd"] is not None:
            entry["cli_reported_cost_usd"] = (entry["cli_reported_cost_usd"] or 0.0) + record["cli_reported_cost_usd"]
    return totals
