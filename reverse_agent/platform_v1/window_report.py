"""End-of-window report for an unattended autonomous window.

Read-only: no writes, no network, no model calls. Builds a single dict that
summarises what a window did and why it stopped, then renders it as Markdown.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Mapping

from .run_store import TaskStore, TaskStoreError

_SUCCESS_STATES = frozenset({"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "COMPLETED"})


def build_report(control_store: Any, task_store: TaskStore, window_id: str) -> dict[str, Any]:
    """Read-only summary of one autonomous window.

    The report carries the window status and stop reason, every Goal with its
    tasks (status, failure classification, executor, binding and any draft PR),
    per-binding aggregates (task count, successes, tokens, wall seconds), and a
    failure-classification histogram.
    """
    window = control_store.get_window(window_id)
    goals = control_store.list_window_goals(window_id)

    goal_blocks: list[dict[str, Any]] = []
    bindings: dict[str, dict[str, Any]] = {}
    failures_by_class: dict[str, int] = {}
    draft_prs: list[dict[str, str]] = []

    token_totals = _window_task_tokens(task_store, window_id)

    for goal in goals:
        links = control_store.list_goal_tasks(goal.id)
        task_blocks: list[dict[str, Any]] = []
        for link in links:
            task_id = str(link["task_id"])
            try:
                task = task_store.get_task(task_id)
            except TaskStoreError:
                continue
            publication = control_store.get_publication(task_id)
            pr_url = publication.pr_url if publication is not None else ""
            if pr_url:
                draft_prs.append({"task_id": task_id, "pr_url": pr_url})
            task_blocks.append({
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "failure_classification": task.failure_classification,
                "executor_kind": task.executor_kind,
                "binding_ref": task.binding_ref,
                "draft_pr_url": pr_url,
            })
            binding = task.binding_ref or ""
            bucket = bindings.setdefault(binding, _empty_binding())
            bucket["task_count"] += 1
            if task.status in _SUCCESS_STATES:
                bucket["success_count"] += 1
            charged = token_totals.get(task_id, {})
            bucket["total_tokens"] += int(charged.get("raw", 0))
            bucket["cost_equivalent_tokens"] += int(charged.get("cost_equivalent", 0))
            wall = _task_wall_seconds(task_store, task.id)
            if wall is not None:
                bucket["total_wall_seconds"] += wall
            classification = task.failure_classification or ""
            if classification:
                failures_by_class[classification] = failures_by_class.get(classification, 0) + 1
        goal_blocks.append({
            "id": goal.id,
            "title": goal.title,
            "status": goal.status,
            "tasks": task_blocks,
        })

    raw_totals = _window_raw_tokens(task_store, window_id)
    return {
        "window_id": window.id,
        "window": {
            "status": window.status,
            "stop_reason": window.stop_reason,
            "starts_at": window.starts_at,
            "expires_at": window.expires_at,
            "observed_token_units": int(window.observed_token_units),
            "raw_token_units": raw_totals["total"],
            "raw_token_counters": raw_totals["counters"],
            "observed_cost_micro_units": int(window.observed_cost_micro_units),
            "unknown_observation_count": int(window.unknown_observation_count),
        },
        "goals": goal_blocks,
        "bindings": bindings,
        "failures_by_class": failures_by_class,
        "draft_prs": draft_prs,
    }


def _empty_binding() -> dict[str, Any]:
    return {"task_count": 0, "success_count": 0, "total_tokens": 0,
            "cost_equivalent_tokens": 0, "total_wall_seconds": 0.0}


_USAGE_COUNTERS = ("input_units", "cache_read_units", "cache_write_units",
                   "output_units", "reasoning_units")


def _window_usage_rows(task_store: TaskStore, window_id: str) -> list[dict[str, Any]]:
    conn = task_store._conn
    try:
        rows = conn.execute(
            "SELECT task_id, source_kind, status, input_units, cache_read_units, "
            "cache_write_units, output_units, reasoning_units "
            "FROM task_usage_observations WHERE window_id = ? AND status = 'OBSERVED'",
            (window_id,),
        ).fetchall()
    except Exception:
        return []
    return [dict(row) for row in rows]


def _window_task_tokens(task_store: TaskStore, window_id: str) -> dict[str, dict[str, int]]:
    """Per task: the raw counter sum and the cost-equivalent charged units (#1504)."""
    from .usage_ledger import cost_equivalent_units
    totals: dict[str, dict[str, int]] = {}
    for row in _window_usage_rows(task_store, window_id):
        entry = totals.setdefault(str(row["task_id"]), {"raw": 0, "cost_equivalent": 0})
        entry["raw"] += sum(int(row[key] or 0) for key in _USAGE_COUNTERS)
        entry["cost_equivalent"] += cost_equivalent_units(row) or 0
    return totals


def _window_raw_tokens(task_store: TaskStore, window_id: str) -> dict[str, Any]:
    counters = {key: 0 for key in _USAGE_COUNTERS}
    for row in _window_usage_rows(task_store, window_id):
        for key in counters:
            counters[key] += int(row[key] or 0)
    return {"total": sum(counters.values()), "counters": counters}


def _task_wall_seconds(task_store: TaskStore, task_id: str) -> float | None:
    try:
        from .usage_ledger import task_feedback_metrics
    except Exception:
        return None
    try:
        metrics = task_feedback_metrics(task_store, task_id)
    except Exception:
        return None
    wall = metrics.get("wall_seconds")
    if isinstance(wall, (int, float)):
        return float(wall)
    return None


def render_markdown(report: Mapping[str, Any]) -> str:
    window = report.get("window") or {}
    lines: list[str] = []
    lines.append(f"# Window report: {report.get('window_id', '')}")
    lines.append("")
    lines.append("## Window")
    lines.append(f"- status: {window.get('status', '')}")
    lines.append(f"- stop_reason: {window.get('stop_reason', '')}")
    lines.append(f"- starts_at: {window.get('starts_at', '')}")
    lines.append(f"- expires_at: {window.get('expires_at', '')}")
    lines.append(f"- observed_token_units: {window.get('observed_token_units', 0)}")
    lines.append(f"- raw_token_units: {window.get('raw_token_units', 0)}")
    counters = window.get("raw_token_counters") or {}
    lines.append("- raw_token_counters: " + ", ".join(
        f"{key}={counters.get(key, 0)}" for key in (
            "input_units", "cache_read_units", "cache_write_units",
            "output_units", "reasoning_units")))
    lines.append(f"- observed_cost_micro_units: {window.get('observed_cost_micro_units', 0)}")
    lines.append(f"- unknown_observation_count: {window.get('unknown_observation_count', 0)}")

    lines.append("")
    lines.append("## Goals")
    goals = report.get("goals") or []
    if not goals:
        lines.append("_no goals_")
    for goal in goals:
        lines.append("")
        lines.append(f"### {goal.get('title', '')} ({goal.get('id', '')})")
        lines.append(f"- status: {goal.get('status', '')}")
        tasks = goal.get("tasks") or []
        if not tasks:
            lines.append("- _no tasks_")
            continue
        lines.append("")
        lines.append("| task | status | executor | binding | failure | draft PR |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for task in tasks:
            pr = task.get("draft_pr_url", "")
            pr_cell = pr if pr else ""
            lines.append(
                f"| {task.get('title', '')} ({task.get('id', '')}) | "
                f"{task.get('status', '')} | "
                f"{task.get('executor_kind', '')} | "
                f"{task.get('binding_ref', '')} | "
                f"{task.get('failure_classification', '')} | "
                f"{pr_cell} |"
            )

    lines.append("")
    lines.append("## Bindings")
    bindings = report.get("bindings") or {}
    if not bindings:
        lines.append("_no bindings_")
    else:
        lines.append("")
        lines.append("| binding | tasks | successes | tokens | cost_eq_tokens | wall_seconds |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for binding, agg in bindings.items():
            wall = agg.get("total_wall_seconds", 0.0)
            wall_text = f"{wall:.3f}" if isinstance(wall, (int, float)) else str(wall)
            lines.append(
                f"| {binding} | {agg.get('task_count', 0)} | "
                f"{agg.get('success_count', 0)} | "
                f"{agg.get('total_tokens', 0)} | "
                f"{agg.get('cost_equivalent_tokens', 0)} | "
                f"{wall_text} |"
            )

    lines.append("")
    lines.append("## Failures by class")
    failures = report.get("failures_by_class") or {}
    if not failures:
        lines.append("_none_")
    else:
        for classification, count in sorted(failures.items()):
            lines.append(f"- {classification}: {count}")

    lines.append("")
    lines.append("## Draft PRs")
    draft_prs = report.get("draft_prs") or []
    if not draft_prs:
        lines.append("_none_")
    else:
        for item in draft_prs:
            lines.append(f"- {item.get('task_id', '')}: {item.get('pr_url', '')}")

    return "\n".join(lines) + "\n"


def _open_stores() -> tuple[TaskStore, Any]:
    from .control_store import PlatformControlStore
    from .trusted_host import _make_task_store

    store = _make_task_store(None)
    control = PlatformControlStore(store)
    return store, control


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or not args[0]:
        sys.stderr.write("usage: python -m reverse_agent.platform_v1.window_report <window_id>\n")
        return 2
    window_id = args[0]
    store, control = _open_stores()
    try:
        report = build_report(control, store, window_id)
    except TaskStoreError as exc:
        sys.stderr.write(f"window_not_found: {exc}\n")
        return 1
    sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())
