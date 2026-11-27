"""Read-only, zero-LLM deterministic health audit for Nerelan TaskStore & Magpie usage."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any, Iterable, Mapping

FAILED_FRESH_SHARE_THRESHOLD = 0.30
UNPRICED_OBS_THRESHOLD = 0.05
PROBE_ERROR_RATE_THRESHOLD = 0.10
CACHE_HIT_MIN_THRESHOLD = 0.70
CACHE_HIT_MIN_OBS = 20
SUPERVISION_TO_WORKER_THRESHOLD = 1.0
WAITING_RECEIPT_RATE_THRESHOLD = 20.0
REPEAT_FAILURE_MIN_ATTEMPTS = 4

SUPERVISION_AGENTS = frozenset({"antigravity", "claude-desktop", "codex"})
WORKER_AGENTS = frozenset({"opencode", "claude", "nerelan"})
_ISSUE_RE = re.compile(r"#(\d+)")


def _utc_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    return now.astimezone(timezone.utc) if now.tzinfo else now.replace(tzinfo=timezone.utc)


def _iso_cutoff(now: datetime, *, days: int = 0, hours: int = 0) -> str:
    return (now - timedelta(days=days, hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _invariant(
    invariant_id: str,
    status: str,
    metric: Any,
    threshold: Any,
    detail: str,
) -> dict[str, Any]:
    return {
        "id": invariant_id,
        "status": status,
        "metric": metric,
        "threshold": threshold,
        "detail": detail,
    }


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _check_failed_fresh_token_share(
    conn: sqlite3.Connection, tables: set[str], cutoff_iso: str
) -> dict[str, Any]:
    if "task_usage_observations" not in tables or "tasks" not in tables:
        return _invariant("failed_fresh_token_share", "UNKNOWN", None, FAILED_FRESH_SHARE_THRESHOLD, "missing required tables")
    cols = _table_columns(conn, "task_usage_observations")
    status_filter = "AND u.status IN ('OBSERVED', 'PARTIAL')" if "status" in cols else ""
    rows = conn.execute(
        f"""
        SELECT COALESCE(t.status, '') AS st, SUM(COALESCE(u.input_units, 0)) AS inp
        FROM task_usage_observations u
        JOIN tasks t ON t.id = u.task_id
        WHERE u.created_at >= ?
          {status_filter}
          AND u.input_units IS NOT NULL
          AND t.status IN ('FAILED', 'READY_FOR_REVIEW', 'READY_FOR_REVIEW_FIXTURE', 'COMPLETED')
        GROUP BY t.status
        """,
        (cutoff_iso,),
    ).fetchall()
    by_status = {r["st"]: int(r["inp"] or 0) for r in rows}
    failed_inp = by_status.get("FAILED", 0)
    total_inp = sum(by_status.values())
    if total_inp <= 0:
        return _invariant("failed_fresh_token_share", "UNKNOWN", None, FAILED_FRESH_SHARE_THRESHOLD, "no terminal fresh input observations in window")
    share = round(failed_inp / total_inp, 4)
    status = "ALERT" if share > FAILED_FRESH_SHARE_THRESHOLD else "OK"
    return _invariant(
        "failed_fresh_token_share",
        status,
        share,
        FAILED_FRESH_SHARE_THRESHOLD,
        f"failed_input_units={failed_inp}, total_terminal_input_units={total_inp}",
    )


def _check_unpriced_usage_obs_ratio(
    conn: sqlite3.Connection, tables: set[str], cutoff_iso: str
) -> dict[str, Any]:
    if "task_usage_observations" not in tables:
        return _invariant("unpriced_usage_obs_ratio", "UNKNOWN", None, UNPRICED_OBS_THRESHOLD, "missing task_usage_observations")
    cols = _table_columns(conn, "task_usage_observations")
    if "status" in cols:
        row = conn.execute(
            """
            SELECT
                SUM(CASE WHEN status IN ('OBSERVED', 'PARTIAL') THEN 1 ELSE 0 END) AS eligible,
                SUM(CASE WHEN status IN ('OBSERVED', 'PARTIAL') AND cost_micro_units IS NULL THEN 1 ELSE 0 END) AS null_cost,
                SUM(CASE WHEN status IN ('OBSERVED', 'PARTIAL') AND cost_micro_units = 0 THEN 1 ELSE 0 END) AS zero_cost,
                SUM(CASE WHEN status IN ('OBSERVED', 'PARTIAL') AND cost_micro_units > 0 THEN 1 ELSE 0 END) AS pos_cost,
                SUM(CASE WHEN status NOT IN ('OBSERVED', 'PARTIAL') OR status IS NULL THEN 1 ELSE 0 END) AS unknown_rows
            FROM task_usage_observations
            WHERE created_at >= ?
            """,
            (cutoff_iso,),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS eligible,
                SUM(CASE WHEN cost_micro_units IS NULL THEN 1 ELSE 0 END) AS null_cost,
                SUM(CASE WHEN cost_micro_units = 0 THEN 1 ELSE 0 END) AS zero_cost,
                SUM(CASE WHEN cost_micro_units > 0 THEN 1 ELSE 0 END) AS pos_cost,
                0 AS unknown_rows
            FROM task_usage_observations
            WHERE created_at >= ?
            """,
            (cutoff_iso,),
        ).fetchone()
    eligible = int(row["eligible"] or 0)
    null_cost = int(row["null_cost"] or 0)
    zero_cost = int(row["zero_cost"] or 0)
    pos_cost = int(row["pos_cost"] or 0)
    unknown_rows = int(row["unknown_rows"] or 0)
    if eligible <= 0:
        return _invariant(
            "unpriced_usage_obs_ratio",
            "UNKNOWN",
            None,
            UNPRICED_OBS_THRESHOLD,
            f"no OBSERVED/PARTIAL usage observations in window (unknown_status_rows={unknown_rows})",
        )
    unpriced = null_cost + zero_cost
    ratio = round(unpriced / eligible, 4)
    status = "ALERT" if ratio > UNPRICED_OBS_THRESHOLD else "OK"
    return _invariant(
        "unpriced_usage_obs_ratio",
        status,
        ratio,
        UNPRICED_OBS_THRESHOLD,
        (
            f"unpriced={unpriced}/{eligible} "
            f"(null_cost_rows={null_cost}, zero_cost_rows={zero_cost}, "
            f"positive_cost_rows={pos_cost}, unknown_status_rows={unknown_rows})"
        ),
    )


def _check_low_cache_hit_routes(
    conn: sqlite3.Connection, tables: set[str], cutoff_iso: str
) -> dict[str, Any]:
    if "task_usage_observations" not in tables:
        return _invariant("low_cache_hit_routes", "UNKNOWN", None, CACHE_HIT_MIN_THRESHOLD, "missing task_usage_observations")
    cols = _table_columns(conn, "task_usage_observations")
    status_filter = "AND status IN ('OBSERVED', 'PARTIAL')" if "status" in cols else ""
    rows = conn.execute(
        f"""
        SELECT COALESCE(provider_id, '?') AS prov,
               COALESCE(model_id, '?') AS mod,
               COUNT(*) AS obs_count,
               SUM(COALESCE(input_units, 0)) AS inp,
               SUM(COALESCE(cache_read_units, 0)) AS cr,
               SUM(COALESCE(cache_write_units, 0)) AS cw
        FROM task_usage_observations
        WHERE created_at >= ?
          {status_filter}
          AND input_units IS NOT NULL
        GROUP BY prov, mod
        HAVING obs_count >= ?
        """,
        (cutoff_iso, CACHE_HIT_MIN_OBS),
    ).fetchall()
    if not rows:
        return _invariant("low_cache_hit_routes", "OK", [], CACHE_HIT_MIN_THRESHOLD, f"no routes with >= {CACHE_HIT_MIN_OBS} observations")
    low_routes: list[dict[str, Any]] = []
    for r in rows:
        denom = int(r["inp"] or 0) + int(r["cr"] or 0) + int(r["cw"] or 0)
        if denom <= 0:
            continue
        hit_rate = round(int(r["cr"] or 0) / denom, 4)
        if hit_rate < CACHE_HIT_MIN_THRESHOLD:
            low_routes.append({
                "provider_id": r["prov"],
                "model_id": r["mod"],
                "obs": int(r["obs_count"]),
                "cache_hit_rate": hit_rate,
            })
    low_routes.sort(key=lambda item: item["cache_hit_rate"])
    status = "ALERT" if low_routes else "OK"
    return _invariant(
        "low_cache_hit_routes",
        status,
        low_routes,
        CACHE_HIT_MIN_THRESHOLD,
        f"{len(low_routes)} active route(s) below {int(CACHE_HIT_MIN_THRESHOLD * 100)}% cache hit",
    )


def _check_goal_hygiene(
    conn: sqlite3.Connection,
    tables: set[str],
    closed_issue_numbers: set[int] | None,
    closed_issue_refs: set[tuple[str, int]] | None = None,
) -> dict[str, Any]:
    if "platform_goals" not in tables or "platform_autonomous_windows" not in tables:
        return _invariant("goal_hygiene", "UNKNOWN", None, 0, "missing goal/window tables")
    windows = {
        r["id"]: r["status"]
        for r in conn.execute("SELECT id, status FROM platform_autonomous_windows").fetchall()
    }
    has_pub_link = "platform_publications" in tables and "platform_goal_task_links" in tables
    goal_cols = _table_columns(conn, "platform_goals")
    repo_select = "repository" if "repository" in goal_cols else "'' AS repository"
    goals = conn.execute(f"SELECT id, status, window_id, title, {repo_select} FROM platform_goals").fetchall()

    active_window_running = 0
    stranded_running = 0
    stranded_with_publications = 0
    by_active_issue: dict[int, list[str]] = {}
    by_blocked_issue: dict[int, list[str]] = {}
    closed_known = closed_issue_refs is not None or closed_issue_numbers is not None
    closed_issue_active = 0

    for g in goals:
        st = g["status"]
        if st not in ("RUNNING", "PLANNED", "BLOCKED"):
            continue
        match = _ISSUE_RE.search(g["title"] or "")
        issue_num = int(match.group(1)) if match else None
        if issue_num is not None:
            if st in ("RUNNING", "PLANNED"):
                by_active_issue.setdefault(issue_num, []).append(g["id"])
                repo_name = str(g["repository"] or "").strip().lower()
                is_closed = (
                    ((repo_name, issue_num) in closed_issue_refs)
                    if closed_issue_refs is not None
                    else (issue_num in closed_issue_numbers if closed_issue_numbers is not None else False)
                )
                if is_closed:
                    closed_issue_active += 1
            else:
                by_blocked_issue.setdefault(issue_num, []).append(g["id"])

        if st == "RUNNING":
            win_status = windows.get(g["window_id"], "NONE")
            if win_status == "ACTIVE":
                active_window_running += 1
            else:
                stranded_running += 1
                if has_pub_link:
                    pub_count = conn.execute(
                        """
                        SELECT COUNT(*) FROM platform_publications p
                        JOIN platform_goal_task_links l ON l.task_id = p.task_id
                        WHERE l.goal_id = ?
                        """,
                        (g["id"],),
                    ).fetchone()[0]
                    if int(pub_count or 0) > 0:
                        stranded_with_publications += 1

    duplicate_issue_groups = sum(1 for gids in by_active_issue.values() if len(gids) > 1)
    blocked_duplicate_issue_groups = sum(1 for gids in by_blocked_issue.values() if len(gids) > 1)
    metric = {
        "active_window_running": active_window_running,
        "stranded_running_inactive_windows": stranded_running,
        "stranded_with_publications": stranded_with_publications,
        "duplicate_issue_groups": duplicate_issue_groups,
        "blocked_duplicate_issue_groups": blocked_duplicate_issue_groups,
        "closed_issue_active_goals": closed_issue_active if closed_known else "UNKNOWN",
    }
    alert = (
        stranded_running > 0
        or duplicate_issue_groups > 0
        or (closed_known and closed_issue_active > 0)
    )
    return _invariant(
        "goal_hygiene",
        "ALERT" if alert else "OK",
        metric,
        {"stranded_running": 0, "duplicate_issue_groups": 0, "closed_issue_active_goals": 0},
        "separates ACTIVE-window running goals from inactive-window stranded goals and preserves publication counts",
    )


def _check_waiting_receipt_rate(
    conn: sqlite3.Connection, tables: set[str], cutoff_24h: str
) -> dict[str, Any]:
    if "platform_operation_receipts" not in tables:
        return _invariant("waiting_receipt_rate", "UNKNOWN", None, WAITING_RECEIPT_RATE_THRESHOLD, "missing platform_operation_receipts")
    rows = conn.execute(
        """
        SELECT COALESCE(subject_id, '?') AS subj, COUNT(*) AS cnt
        FROM platform_operation_receipts
        WHERE created_at >= ? AND operation_type = 'policy_evaluation'
        GROUP BY subj
        ORDER BY cnt DESC
        LIMIT 5
        """,
        (cutoff_24h,),
    ).fetchall()
    if not rows:
        return _invariant("waiting_receipt_rate", "OK", 0.0, WAITING_RECEIPT_RATE_THRESHOLD, "no policy_evaluation receipts in last 24h")
    max_per_hour = round(int(rows[0]["cnt"]) / 24.0, 2)
    status = "ALERT" if max_per_hour > WAITING_RECEIPT_RATE_THRESHOLD else "OK"
    return _invariant(
        "waiting_receipt_rate",
        status,
        max_per_hour,
        WAITING_RECEIPT_RATE_THRESHOLD,
        f"peak={rows[0]['cnt']} policy_evaluation receipts/24h for subject={rows[0]['subj'][:24]}",
    )


def _check_stalled_or_repeating_tasks(
    conn: sqlite3.Connection, tables: set[str], cutoff_iso: str
) -> dict[str, Any]:
    if "platform_goals" not in tables or "platform_goal_task_links" not in tables or "tasks" not in tables:
        return _invariant("stalled_or_repeating_tasks", "UNKNOWN", None, REPEAT_FAILURE_MIN_ATTEMPTS, "missing goal/task tables")
    rows = conn.execute(
        """
        SELECT g.id AS goal_id, g.status AS goal_status,
               SUM(CASE WHEN t.status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count
        FROM platform_goals g
        JOIN platform_goal_task_links l ON l.goal_id = g.id
        JOIN tasks t ON t.id = l.task_id
        WHERE t.created_at >= ?
        GROUP BY g.id, g.status
        HAVING failed_count >= ?
        ORDER BY failed_count DESC
        """,
        (cutoff_iso, REPEAT_FAILURE_MIN_ATTEMPTS),
    ).fetchall()
    items = [{"goal_id": r["goal_id"], "status": r["goal_status"], "failed_count": int(r["failed_count"])} for r in rows]
    return _invariant(
        "stalled_or_repeating_tasks",
        "ALERT" if items else "OK",
        items,
        REPEAT_FAILURE_MIN_ATTEMPTS,
        f"{len(items)} goal(s) with >= {REPEAT_FAILURE_MIN_ATTEMPTS} failed attempts in window",
    )


def _load_magpie_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def _parse_magpie_cost(raw: Any) -> float | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if value < 0 or value != value:  # reject negative or NaN
        return None
    return value


def _row_in_window(row: Mapping[str, str], cutoff_dt: datetime | None) -> bool:
    if cutoff_dt is None:
        return True
    raw_time = (row.get("time") or "").strip()
    if not raw_time:
        return True
    try:
        parsed = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed >= cutoff_dt


def _check_magpie_csv_invariants(
    magpie_rows: list[dict[str, str]] | None,
    *,
    cutoff_dt: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if magpie_rows is None:
        return (
            _invariant("probe_error_rate", "UNKNOWN", None, PROBE_ERROR_RATE_THRESHOLD, "no Magpie usage CSV provided"),
            _invariant("supervision_to_worker_cost_ratio", "UNKNOWN", None, SUPERVISION_TO_WORKER_THRESHOLD, "no Magpie usage CSV provided"),
        )
    probe_total = 0
    probe_err = 0
    sup_cost = 0.0
    worker_cost = 0.0
    sup_unpriced = 0
    worker_unpriced = 0
    for row in magpie_rows:
        if not _row_in_window(row, cutoff_dt):
            continue
        agent = (row.get("agent") or "").strip()
        status = (row.get("status") or "0").strip()
        err_text = (row.get("error") or row.get("error_type") or "").strip()
        rejected = (row.get("rejected") or "").strip().lower() in ("1", "true", "yes")
        is_err = (status not in ("0", "200", "")) or bool(err_text) or rejected
        cost = _parse_magpie_cost(row.get("cost_usd"))
        if agent.lower() == "python-urllib":
            probe_total += 1
            if is_err:
                probe_err += 1
        if agent in SUPERVISION_AGENTS:
            if cost is None:
                sup_unpriced += 1
            else:
                sup_cost += cost
        elif agent in WORKER_AGENTS:
            if cost is None:
                worker_unpriced += 1
            else:
                worker_cost += cost

    if probe_total == 0:
        probe_inv = _invariant("probe_error_rate", "OK", 0.0, PROBE_ERROR_RATE_THRESHOLD, "0 Python-urllib probe rows")
    else:
        err_rate = round(probe_err / probe_total, 4)
        probe_inv = _invariant(
            "probe_error_rate",
            "ALERT" if err_rate > PROBE_ERROR_RATE_THRESHOLD else "OK",
            err_rate,
            PROBE_ERROR_RATE_THRESHOLD,
            f"probe_errors={probe_err}/{probe_total}",
        )

    if sup_unpriced > 0 or worker_unpriced > 0:
        sup_inv = _invariant(
            "supervision_to_worker_cost_ratio",
            "UNKNOWN",
            None,
            SUPERVISION_TO_WORKER_THRESHOLD,
            (
                f"unpriced_sup_rows={sup_unpriced}, unpriced_worker_rows={worker_unpriced}, "
                f"supervision_list_usd={sup_cost:.4f}, worker_list_usd={worker_cost:.4f} "
                "(missing prices stay UNKNOWN)"
            ),
        )
    elif worker_cost <= 0.0:
        sup_inv = _invariant(
            "supervision_to_worker_cost_ratio",
            "UNKNOWN",
            None,
            SUPERVISION_TO_WORKER_THRESHOLD,
            f"supervision_list_usd={sup_cost:.4f}, worker_list_usd=0.0 (cannot divide)",
        )
    else:
        ratio = round(sup_cost / worker_cost, 2)
        sup_inv = _invariant(
            "supervision_to_worker_cost_ratio",
            "ALERT" if ratio > SUPERVISION_TO_WORKER_THRESHOLD else "OK",
            ratio,
            SUPERVISION_TO_WORKER_THRESHOLD,
            f"supervision_list_usd={sup_cost:.2f}, worker_list_usd={worker_cost:.2f}",
        )
    return probe_inv, sup_inv


def _load_magpie_cache_as_rows(cache_path: Path) -> list[dict[str, str]] | None:
    if not cache_path.is_file():
        return None
    from .magpie_usage_ingest import read_cache

    adapted: list[dict[str, str]] = []
    for item in read_cache(cache_path):
        status = item.get("status")
        reported = item.get("reported_cost_usd")
        adapted.append({
            "time": str(item.get("time") or ""),
            "agent": str(item.get("agent") or ""),
            "status": str(int(status)) if isinstance(status, (int, float)) else "0",
            "rejected": "true" if item.get("rejected") else "false",
            "cost_usd": "" if reported is None else str(reported),
            "error": "",
        })
    return adapted


def run_health_audit(
    db_path: Path | str,
    *,
    now: datetime | None = None,
    lookback_days: int = 7,
    magpie_csv_path: Path | str | None = None,
    magpie_cache_path: Path | str | None = None,
    closed_issue_numbers: Iterable[int] | None = None,
    closed_issue_refs: Iterable[tuple[str, int]] | None = None,
) -> dict[str, Any]:
    """Run all 8 deterministic read-only invariants without LLM or network calls."""
    if lookback_days <= 0:
        raise ValueError("lookback_days must be positive")
    ref_now = _utc_now(now)
    cutoff_dt = ref_now - timedelta(days=lookback_days)
    cutoff_iso = _iso_cutoff(ref_now, days=lookback_days)
    cutoff_24h = _iso_cutoff(ref_now, hours=24)
    closed_set = set(int(n) for n in closed_issue_numbers) if closed_issue_numbers is not None else None
    closed_ref_set = (
        {(str(repo).strip().lower(), int(num)) for repo, num in closed_issue_refs}
        if closed_issue_refs is not None
        else None
    )
    if magpie_csv_path is not None:
        magpie_rows = _load_magpie_csv(Path(magpie_csv_path))
    elif magpie_cache_path is not None:
        magpie_rows = _load_magpie_cache_as_rows(Path(magpie_cache_path))
    else:
        magpie_rows = None

    db = Path(db_path)
    conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = _table_names(conn)
        probe_inv, sup_inv = _check_magpie_csv_invariants(magpie_rows, cutoff_dt=cutoff_dt)
        invariants = [
            _check_failed_fresh_token_share(conn, tables, cutoff_iso),
            _check_unpriced_usage_obs_ratio(conn, tables, cutoff_iso),
            probe_inv,
            _check_low_cache_hit_routes(conn, tables, cutoff_iso),
            _check_goal_hygiene(conn, tables, closed_set, closed_ref_set),
            sup_inv,
            _check_waiting_receipt_rate(conn, tables, cutoff_24h),
            _check_stalled_or_repeating_tasks(conn, tables, cutoff_iso),
        ]
    finally:
        conn.close()

    statuses = {item["status"] for item in invariants}
    if "ALERT" in statuses:
        overall = "ALERT"
    elif statuses == {"OK"}:
        overall = "OK"
    else:
        overall = "PARTIAL_UNKNOWN"
    return {
        "schema_version": 1,
        "generated_at": ref_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lookback_days": lookback_days,
        "overall_status": overall,
        "invariants": invariants,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zero-LLM deterministic Nerelan health audit")
    parser.add_argument("--db", required=True, help="Path to tasks.sqlite3 (opened read-only)")
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--magpie-csv", default=None, help="Optional path to `magpie usage --csv` export")
    parser.add_argument("--magpie-cache", default=None, help="Optional path to magpie_usage_cache.jsonl")
    parser.add_argument("--closed-issues", default=None, help="Optional JSON file with list of closed GitHub issue numbers")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    closed: list[int] | None = None
    if args.closed_issues:
        loaded = json.loads(Path(args.closed_issues).read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            closed = [int(x) for x in loaded]
    report = run_health_audit(
        Path(args.db),
        lookback_days=args.lookback_days,
        magpie_csv_path=Path(args.magpie_csv) if args.magpie_csv else None,
        magpie_cache_path=Path(args.magpie_cache) if args.magpie_cache else None,
        closed_issue_numbers=closed,
    )
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"overall={report['overall_status']} generated_at={report['generated_at']} lookback_days={report['lookback_days']}")
        for inv in report["invariants"]:
            print(f"  [{inv['status']:7s}] {inv['id']}: metric={inv['metric']} (threshold={inv['threshold']}) - {inv['detail']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
