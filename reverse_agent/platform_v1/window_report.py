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

    Task membership is decided from window-scoped evidence (task claims, budget
    reservations and usage observations that carry the window id), not from the
    goal's current ``window_id``. A goal rebound to a successor window therefore
    appears in both reports, each listing only the tasks that ran in it. A task
    that has not yet run anywhere (no window-scoped evidence) is attributed to
    its goal's current window.
    """
    window = control_store.get_window(window_id)

    task_window_evidence = _task_window_evidence(control_store)

    goals_by_id: dict[str, Any] = {}
    for task_id, windows in task_window_evidence.items():
        if window_id not in windows:
            continue
        try:
            goal_id = control_store.goal_id_for_task(task_id)
        except TaskStoreError:
            continue
        if goal_id not in goals_by_id:
            try:
                goals_by_id[goal_id] = control_store.get_goal(goal_id)
            except TaskStoreError:
                continue
    for goal in control_store.list_window_goals(window_id):
        goals_by_id[goal.id] = goal

    goals = sorted(goals_by_id.values(), key=lambda g: g.created_at)

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
            evidence_windows = task_window_evidence.get(task_id)
            if evidence_windows is not None:
                if window_id not in evidence_windows:
                    continue
            elif goal.window_id != window_id:
                continue
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
            bucket["total_tokens"] += int(token_totals.get(task_id, 0))
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

    return {
        "window_id": window.id,
        "window": {
            "status": window.status,
            "stop_reason": window.stop_reason,
            "starts_at": window.starts_at,
            "expires_at": window.expires_at,
            "observed_token_units": int(window.observed_token_units),
            "observed_cost_micro_units": int(window.observed_cost_micro_units),
            "unknown_observation_count": int(window.unknown_observation_count),
        },
        "goals": goal_blocks,
        "bindings": bindings,
        "failures_by_class": failures_by_class,
        "draft_prs": draft_prs,
    }


def _empty_binding() -> dict[str, Any]:
    return {"task_count": 0, "success_count": 0, "total_tokens": 0, "total_wall_seconds": 0.0}


def _task_window_evidence(control_store: Any) -> dict[str, set[str]]:
    """Map task ids to the set of windows they ran in, from window-scoped evidence.

    A task is associated with a window if any of its claims, budget reservations
    or usage observations carry that window id. Claims are the primary signal:
    reservations are created at claim time and usage observations reference the
    claim epoch, so the claim table covers every dispatched attempt. Reservations
    and usage are unioned in as a safety net for edge cases where a claim row
    has been retired or a usage observation was recorded before its claim.
    """
    conn = control_store._conn
    result: dict[str, set[str]] = {}
    for table, column in (
        ("platform_coordinator_claims", "task_id"),
        ("platform_budget_reservations", "task_id"),
        ("task_usage_observations", "task_id"),
    ):
        try:
            rows = conn.execute(
                f"SELECT DISTINCT {column}, window_id FROM {table}"
            ).fetchall()
        except Exception:
            continue
        for row in rows:
            task_id = str(row[column])
            result.setdefault(task_id, set()).add(str(row["window_id"]))
    return result


def _window_task_tokens(task_store: TaskStore, window_id: str) -> dict[str, int]:
    conn = task_store._conn
    totals: dict[str, int] = {}
    try:
        rows = conn.execute(
            "SELECT task_id, "
            "COALESCE(SUM(input_units),0) AS input_units, "
            "COALESCE(SUM(cache_read_units),0) AS cache_read_units, "
            "COALESCE(SUM(cache_write_units),0) AS cache_write_units, "
            "COALESCE(SUM(output_units),0) AS output_units, "
            "COALESCE(SUM(reasoning_units),0) AS reasoning_units "
            "FROM task_usage_observations WHERE window_id = ? AND status = 'OBSERVED' "
            "GROUP BY task_id",
            (window_id,),
        ).fetchall()
    except Exception:
        return totals
    for row in rows:
        total = sum(int(row[key] or 0) for key in (
            "input_units", "cache_read_units", "cache_write_units",
            "output_units", "reasoning_units",
        ))
        totals[str(row["task_id"])] = total
    return totals


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
        lines.append("| binding | tasks | successes | tokens | wall_seconds |")
        lines.append("| --- | --- | --- | --- | --- |")
        for binding, agg in bindings.items():
            wall = agg.get("total_wall_seconds", 0.0)
            wall_text = f"{wall:.3f}" if isinstance(wall, (int, float)) else str(wall)
            lines.append(
                f"| {binding} | {agg.get('task_count', 0)} | "
                f"{agg.get('success_count', 0)} | "
                f"{agg.get('total_tokens', 0)} | "
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
