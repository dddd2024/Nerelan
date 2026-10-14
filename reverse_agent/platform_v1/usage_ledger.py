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

import json
from typing import Any

OK_STATUSES = frozenset({"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "COMPLETED"})
COUNTERS = ("input", "cache_read", "cache_write", "output", "reasoning")


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


def task_token_records(store: Any, *, limit: int = 500) -> list[dict[str, Any]]:
    """Normalized token counters for the most recent ``limit`` finished, model-backed tasks."""
    conn = store._conn
    tasks = conn.execute(
        "SELECT id, binding_ref, executor_kind, status FROM tasks WHERE binding_ref <> '' "
        "AND status IN ({}) ORDER BY rowid DESC LIMIT ?".format(",".join("?" * (len(OK_STATUSES) + 1))),
        (*sorted(OK_STATUSES), "FAILED", limit)).fetchall()
    if not tasks:
        return []
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
            "models": models,
            "cli_reported_cost_usd": float(cost) if type(cost) in (int, float) and cost >= 0 else None,
        })
    return records


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
