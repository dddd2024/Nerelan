"""Side-by-side cost report: old metric, new metric, three cost bases.

The Owner decision of 2026-11-04 keeps the decision target on the old
accepted-run metric until a controlled comparison and an independent review;
this module builds that comparison instead of changing any decision.

It joins three independent sources and never blends them:

* **list price** — ``usage_ledger.task_feedback_metrics`` (local estimate, always
  available, priced from the models.dev snapshot);
* **cash** — Magpie's per-request ``cost_usd`` for pay-as-you-go traffic;
* **quota** — Magpie's per-request ``cost_usd`` for subscription traffic, i.e.
  the opportunity value of consumed allowance.

Requests are attached to task attempts by the conservative
:func:`magpie_usage_ingest.correlate_usage` rules; an attempt that could not be
fully attributed carries ``None`` for the Magpie bases, so a comparison can
exclude it rather than treating invisible spend as free.

Read-only: no dispatch, no model call, no write except the optional usage cache.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from .magpie_usage_ingest import (
    attempts_from_store, correlate_usage, economics_runs, ingest, read_cache,
)
from .orchestration_selector import (
    COST_BASIS_FIELDS, all_in_economics, cost_per_accepted_change,
)


def _list_price_runs(store: Any, attempts: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Legacy-shaped runs priced from the local estimate.

    Kept separate from the Magpie-based runs on purpose: this is the number the
    current decision uses, and mixing it with measured cash would make the
    comparison meaningless.
    """
    from .usage_ledger import task_feedback_metrics

    runs = []
    for attempt in attempts:
        metrics = task_feedback_metrics(store, str(attempt["task_id"]))
        runs.append({
            "mode": attempt.get("mode") or "single",
            "accepted": bool(attempt.get("accepted")),
            "cost_units": metrics.get("cost_units"),
            "task_count": 1,
            "tokens": {},
            "wall_seconds": metrics.get("wall_seconds"),
            "size_band": "unbanded",
            "task_id": attempt["task_id"],
        })
    return runs


def build_cost_report(store: Any, rows: list[Mapping[str, Any]], *,
                      limit: int = 200,
                      coverage_window: Optional[tuple[float, float]] = None) -> dict[str, Any]:
    """Everything needed to compare the old and the new metric honestly."""
    attempts = attempts_from_store(store, limit=limit)
    correlated = correlate_usage(rows, attempts, coverage_window=coverage_window)
    measured = economics_runs(correlated, strict=True)
    listed = _list_price_runs(store, attempts)
    legacy = cost_per_accepted_change(listed)

    return {
        "generated_at": time.time(),
        "decision_ready": False,
        "acceptance_basis": "task_execution_status_not_independent_review",
        "window": {"attempts": len(attempts), "requests": len(rows)},
        "attribution": correlated["summary"],
        "legacy": {
            "metric": "cost_per_accepted (accepted runs only)",
            "per_mode": legacy,
            "note": "The metric the selector uses today. Its numerator excludes "
                    "failed attempts, so it flatters flaky strategies.",
        },
        "all_in": {
            basis: {
                "metric": f"cost_per_accepted_all_in ({basis})",
                "per_mode": all_in_economics(listed if basis == "list_price" else measured,
                                             basis=basis),
            }
            for basis in sorted(COST_BASIS_FIELDS)
        },
        "caveats": [
            "accepted_runs here means task execution readiness, not independent product acceptance; do not promote policies from this report.",
            "list_price is an estimate from the published price list, not a bill.",
            "cash counts pay-as-you-go requests only; a subscription run bills 0 there.",
            "quota is the opportunity value of consumed allowance, priced by Magpie.",
            "An attempt with unattributed or unpriced requests carries null, never 0.",
            "Without verified export coverage, cash/quota all-in metrics remain unknown; matched rows are lower bounds.",
            "Attribution is time-window + executor based until a shared join key exists.",
        ],
    }


def run_report(*, last: str = "6h", cache_path: Optional[Path] = None,
               from_cache: bool = False, limit: int = 200) -> dict[str, Any]:
    """Refresh (or reuse) Magpie usage, then build the report against the live store."""
    from .trusted_host import _make_task_store

    refresh = {"available": True, "reason": None, "added": 0}
    if from_cache:
        rows = read_cache(cache_path)
    else:
        refresh = ingest(last=last, cache_path=cache_path)
        rows = read_cache(cache_path)
    report = build_cost_report(_make_task_store(None), rows, limit=limit)
    report["ingest"] = {"available": refresh.get("available"), "reason": refresh.get("reason"),
                        "added": refresh.get("added"), "source": "cache" if from_cache else "cli"}
    return report


SNAPSHOT_VERSION = 2


def snapshot_document(report: Mapping[str, Any], *, label: str) -> dict[str, Any]:
    """The frozen, self-describing form of one report (no I/O)."""
    return {
        "version": SNAPSHOT_VERSION,
        "label": str(label),
        "generated_at": report.get("generated_at"),
        "window": dict(report.get("window") or {}),
        "attribution": dict(report.get("attribution") or {}),
        "legacy": report.get("legacy"),
        "all_in": report.get("all_in"),
        "caveats": list(report.get("caveats") or []),
    }


def snapshot(report: Mapping[str, Any], *, label: str, path: Path) -> dict[str, Any]:
    """Persist one labelled report so two later runs can be compared.

    A snapshot exists because the comparison experiment needs a *frozen* pair of
    measurements: recomputing later against a changed task history would compare
    two moving targets.
    """
    document = snapshot_document(report, label=label)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return document


def compare_snapshots(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Per-basis deltas between two snapshots of the same schema.

    Refuses to compare across schema versions: a silently reinterpreted field
    would make the "improvement" meaningless.
    """
    left, right = int(baseline.get("version") or 0), int(candidate.get("version") or 0)
    if left != right or left != SNAPSHOT_VERSION:
        raise ValueError(f"incomparable snapshots: {left} vs {right} (expected {SNAPSHOT_VERSION})")

    def _number(value: Any) -> Optional[float]:
        return float(value) if isinstance(value, (int, float)) else None

    rows = []
    for section in ("legacy",):
        for mode, entry in ((baseline.get(section) or {}).get("per_mode") or {}).items():
            after = ((candidate.get(section) or {}).get("per_mode") or {}).get(mode, {})
            rows.append(_delta_row(section, "list_price", mode, entry, after,
                                   _number(entry.get("cost_per_accepted")),
                                   _number(after.get("cost_per_accepted"))))
    for basis, block in (baseline.get("all_in") or {}).items():
        for mode, entry in (block.get("per_mode") or {}).items():
            after = ((candidate.get("all_in") or {}).get(basis) or {}).get("per_mode", {}).get(mode, {})
            rows.append(_delta_row("all_in", basis, mode, entry, after,
                                   _number(entry.get("cost_per_accepted_all_in")),
                                   _number(after.get("cost_per_accepted_all_in"))))
    # A mode with no data on either side stays out: an all-null row is noise,
    # not a comparison.
    rows = [row for row in rows if not (row["before"] is None and row["after"] is None)]
    return {
        "baseline": baseline.get("label"),
        "candidate": candidate.get("label"),
        "rows": rows,
        "attribution": {
            "baseline": baseline.get("attribution"),
            "candidate": candidate.get("attribution"),
        },
        "note": "A cheaper number with fewer accepted results is a regression, "
                "never a saving: read accepted_runs beside every delta.",
    }


def _delta_row(section: str, basis: str, mode: str, before: Mapping[str, Any],
               after: Mapping[str, Any], before_value: Optional[float],
               after_value: Optional[float]) -> dict[str, Any]:
    delta = None if before_value is None or after_value is None else round(after_value - before_value, 6)
    relative = (round(delta / before_value, 4)
                if delta is not None and before_value else None)
    return {
        "section": section, "basis": basis, "mode": mode,
        "before": before_value, "after": after_value,
        "delta": delta, "relative": relative,
        "before_runs": before.get("runs"), "after_runs": after.get("runs"),
        "before_accepted": before.get("accepted_runs"), "after_accepted": after.get("accepted_runs"),
    }


def doctor_report(*, exe_configured: bool, magpie_status: Optional[str],
                  rows: list[Mapping[str, Any]], attempts: list[Mapping[str, Any]],
                  correlated: Mapping[str, Any]) -> dict[str, Any]:
    """Can the comparison experiment actually run right now?

    Pure: every input is already measured. The point is to say *why not* in
    operator language, because the usual failure is not an error — it is a
    silently empty dataset that would produce a beautiful `n/a` report.
    """
    summary = correlated.get("summary") or {}
    with_session = sum(1 for attempt in attempts if attempt.get("agent_session_id"))
    checks: dict[str, dict[str, Any]] = {
        "magpie_cli_configured": {
            "ok": bool(exe_configured),
            "detail": "REVERSE_AGENT_MAGPIE_EXE points at a real file" if exe_configured
                      else "set REVERSE_AGENT_MAGPIE_EXE to read real cost",
        },
        "magpie_reachable": {
            "ok": magpie_status == "available",
            "detail": f"magpie status={magpie_status or 'unknown'}",
        },
        "usage_rows": {
            "ok": bool(rows),
            "detail": f"{len(rows)} requests in the window",
        },
        "tasks_with_session_id": {
            "ok": with_session > 0,
            "detail": f"{with_session}/{len(attempts)} attempts carry agent_session_id "
                      "(only runs after the join-key change have one)",
        },
        "windows_overlap": {
            "ok": summary.get("overlap") in {"full", "partial"},
            "detail": f"overlap={summary.get('overlap')} "
                      f"({summary.get('overlap_attempts', 0)} attempts in the usage window)",
        },
        "complete_cost_evidence": {
            "ok": bool(summary.get("coverage_complete"))
                  and summary.get("attributed", 0) > 0
                  and not summary.get("ambiguous") and not summary.get("unattributed"),
            "detail": "requires verified export coverage and no unresolved request attribution",
        },
    }
    blockers = [name for name, check in checks.items() if not check["ok"]]
    ambiguity = summary.get("ambiguity_rate")
    warnings = []
    if isinstance(ambiguity, (int, float)) and ambiguity > 0.2:
        warnings.append(f"ambiguity_rate={ambiguity}: attribution is mostly by time window")
    if summary.get("attributed") == 0:
        warnings.append("no request was attributed to a task")
    return {
        "ready": not blockers,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "next": ("run the comparison: --save baseline.json before switching strategy"
                 if not blockers else
                 "produce at least one run with a session id and overlapping usage, "
                 "then re-run --doctor"),
    }


def run_doctor(*, last: str = "6h", limit: int = 200) -> dict[str, Any]:
    """Measure the four inputs the report needs, then explain what is missing."""
    from .magpie_usage_ingest import (
        attempts_from_store, correlate_usage, magpie_executable, read_usage,
    )
    from .trusted_host import _make_task_store

    exe = magpie_executable()
    status: Optional[str] = None
    if exe is not None:
        try:
            from ..model_access.magpie import fetch_magpie_snapshot
            status = fetch_magpie_snapshot().get("status")
        except Exception:  # noqa: BLE001 - reachability is one of the checks
            status = "unavailable"
    rows = read_usage(exe, last=last) if exe is not None else []
    store = _make_task_store(None)
    attempts = attempts_from_store(store, limit=limit)
    correlated = correlate_usage(rows, attempts)
    report = doctor_report(exe_configured=exe is not None, magpie_status=status,
                           rows=rows, attempts=attempts, correlated=correlated)
    report["window"] = {"requests": len(rows), "attempts": len(attempts)}
    report["attribution"] = correlated.get("summary")
    return report


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Compare the accepted-only cost metric with all-in costs per basis (read-only).")
    parser.add_argument("--last", default="6h", help="Magpie usage window such as 2h, 90m, 7d")
    parser.add_argument("--from-cache", action="store_true", help="skip the CLI and reuse the cache")
    parser.add_argument("--limit", type=int, default=200, help="how many recent tasks to consider")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--save", type=Path, help="write a labelled snapshot for later comparison")
    parser.add_argument("--label", default="", help="snapshot label, e.g. local-routing-7d")
    parser.add_argument("--compare", type=Path, help="compare this run with an earlier snapshot")
    parser.add_argument("--doctor", action="store_true",
                        help="check whether the comparison can run at all, then exit")
    args = parser.parse_args(argv)
    if args.doctor:
        doctor = run_doctor(last=args.last, limit=args.limit)
        if args.json:
            print(json.dumps(doctor, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for name, check in doctor["checks"].items():
                print(f"{'ok  ' if check['ok'] else 'FAIL'} {name}: {check['detail']}")
            for warning in doctor["warnings"]:
                print(f"warn {warning}")
            print("READY" if doctor["ready"] else f"NOT READY: {', '.join(doctor['blockers'])}")
            print(doctor["next"])
        return 0 if doctor["ready"] else 1
    report = run_report(last=args.last, from_cache=args.from_cache, limit=args.limit)
    if args.save:
        snapshot(report, label=args.label or "unlabelled", path=args.save)
    if args.compare:
        baseline = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        comparison = compare_snapshots(baseline, snapshot_document(report, label=args.label or "candidate"))
        if args.json:
            print(json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"compare {comparison['baseline']} -> {comparison['candidate']}")
            for row in comparison["rows"]:
                mark = "" if row["delta"] is None else (" better" if row["delta"] < 0 else " worse")
                print(f"{row['basis']:<11}{row['mode']:<11}"
                      f"{row['before']!s:>10} -> {row['after']!s:>10}{mark}"
                      f"  accepted {row['before_accepted']} -> {row['after_accepted']}")
            print(comparison["note"])
        return 0
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    attribution = report["attribution"]
    print(f"attempts={report['window']['attempts']} requests={report['window']['requests']} "
          f"attributed={attribution['attributed']} ambiguous={attribution['ambiguous']} "
          f"overlap={attribution['overlap']}")
    print(f"{'basis':<12}{'mode':<12}{'runs':>6}{'accepted':>9}{'per_accepted':>14}")
    for name, block in report["all_in"].items():
        for mode, entry in block["per_mode"].items():
            value = entry["cost_per_accepted_all_in"]
            print(f"{name:<12}{mode:<12}{entry['runs']:>6}{entry['accepted_runs']:>9}"
                  f"{'n/a' if value is None else round(value, 4):>14}")
    for mode, entry in report["legacy"]["per_mode"].items():
        value = entry["cost_per_accepted"]
        print(f"{'legacy':<12}{mode:<12}{entry['runs']:>6}{entry['accepted_runs']:>9}"
              f"{'n/a' if value is None else round(value, 4):>14}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())
