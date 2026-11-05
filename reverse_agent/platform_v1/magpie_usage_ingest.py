"""Read-only ingestion of Magpie's per-request usage CSV (P1 step 1).

Why this exists: `equivalent_cost()` in this repository prices tokens from a
published list. Magpie already records what each request actually cost, which
account it ran on, whether the model was swapped and whether it was rejected.
Reading that is strictly cheaper and more accurate than estimating it — and it
answers the three cost bases the Owner asked to keep apart:

* **cash**    — billed pay-as-you-go spend (``billing_class == "payg"``);
* **quota**   — allowance consumed on a signed-in subscription, valued at the
  price Magpie reports (``billing_class == "subscription"``);
* **list price** — the local estimate, still the fallback when Magpie is absent.

The classification is deliberately conservative and recorded per row
(``billing_class``) so a later correction never needs a re-ingest:

    session_account present -> ran on a signed-in subscription -> payment is
    allowance, not cash. Magpie still prints a cost for it; that number is the
    opportunity value of the allowance, not money billed.

Boundaries — this module never changes dispatch, never calls a model, and never
stores an account identity:

* the executable must be given explicitly (``REVERSE_AGENT_MAGPIE_EXE``); there
  is no machine-path default and no PATH lookup;
* the CSV is read through one bounded subprocess with a timeout, no shell;
* account identity is reduced to a salted-free SHA-256 prefix — the raw e-mail
  or key name never reaches disk;
* an absent Magpie, a timeout or a malformed CSV yields ``[]``, never an error.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

# Bounded so a long window cannot exhaust memory; Magpie writes one row per request.
MAX_ROWS = 20_000
CACHE_LIMIT = 5_000
DEFAULT_LAST = "6h"
DEFAULT_TIMEOUT = 25.0
# The desktop app serves aggregates over loopback HTTP and ships no CLI at all,
# so the CSV path cannot be the only source. Same origin discipline as every
# other Magpie read: loopback only, no credential handling.
DEFAULT_MAGPIE_URL = "http://127.0.0.1:3425"
LOOPBACK_PREFIXES = ("http://127.0.0.1", "http://localhost", "http://[::1]")

# Columns kept from the CSV. Everything else (keys, caller names, error bodies)
# is dropped on purpose: it is either PII or not needed for economics.
_TOKEN_COLUMNS = {
    "input": "input_tokens",
    "output": "output_tokens",
    "cache_read": "cache_read_tokens",
    "cache_write": "cache_write_tokens",
    "reasoning": "reasoning_tokens",
}


def magpie_executable(env: Mapping[str, str] | None = None) -> Optional[Path]:
    """The explicitly configured Magpie CLI, or ``None``.

    No default and no PATH lookup: running an arbitrary binary found by name is
    exactly the kind of implicit authority this repository avoids.
    """
    raw = (env if env is not None else os.environ).get("REVERSE_AGENT_MAGPIE_EXE", "").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() and path.is_file() else None


def _number(value: Any) -> Optional[float]:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _flag(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _account_id(value: Any) -> Optional[str]:
    """Stable, non-reversible account handle; the raw identifier is discarded."""
    text = str(value or "").strip().lower()
    if not text:
        return None
    return "acct_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def read_usage(exe: Path, *, last: str = DEFAULT_LAST,
               timeout: float = DEFAULT_TIMEOUT) -> list[dict[str, Any]]:
    """Run ``magpie usage --csv --last <last>`` once and parse it.

    Read-only: the CLI prints what it already stored. A non-zero exit, a timeout
    or an unreadable file returns ``[]`` — the caller degrades to list-price
    estimates instead of failing.
    """
    command = [str(exe), "usage", "--csv", "--last", str(last)]
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, explicit path
            command, capture_output=True, text=True, timeout=timeout,
            shell=False, check=False, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return []
    if completed.returncode != 0 or not completed.stdout:
        return []
    return parse_usage_csv(completed.stdout)


def parse_usage_csv(text: str) -> list[dict[str, Any]]:
    """Normalize Magpie's CSV into rows safe to persist and aggregate."""
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "cost_usd" not in reader.fieldnames:
        return []
    rows: list[dict[str, Any]] = []
    for raw in reader:
        if len(rows) >= MAX_ROWS:
            break
        row = _normalize(raw)
        if row is not None:
            rows.append(row)
    return rows


def _normalize(raw: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    request_id = str(raw.get("request_id") or "").strip()
    time = str(raw.get("time") or "").strip()
    if not request_id and not time:
        return None  # a row without identity cannot be de-duplicated
    account = _account_id(raw.get("session_account") or raw.get("provider_account"))
    tokens = {key: int(_number(raw.get(column)) or 0) for key, column in _TOKEN_COLUMNS.items()}
    return {
        "request_id": request_id or f"{time}:{raw.get('served_model') or raw.get('model') or ''}",
        "time": time or None,
        # ``agent`` is the executor name (codex/claude/workbuddy). ``provider`` is
        # the vendor (anthropic/openai) and must never be used for attribution.
        "agent": str(raw.get("agent") or "").strip().lower() or None,
        # Opaque UUID: the executor reports the same value as agent_session_id,
        # which turns attribution from a time-window guess into an exact match.
        "session": str(raw.get("session") or "").strip() or None,
        "provider": str(raw.get("provider") or "").strip() or None,
        "asked_model": str(raw.get("requested_model") or "").strip() or None,
        "served_model": str(raw.get("served_model") or raw.get("model") or "").strip() or None,
        "swapped": _flag(raw.get("swapped")),
        "rejected": _flag(raw.get("rejected")),
        "status": _number(raw.get("status")),
        "tries": _number(raw.get("tries")),
        "duration_ms": _number(raw.get("duration_ms")),
        "tokens": tokens,
        # Magpie's own number, kept verbatim so a classification change is reversible.
        "reported_cost_usd": _number(raw.get("cost_usd")),
        "account_id": account,
        "billing_class": "subscription" if account else "payg",
    }


def cost_basis_values(row: Mapping[str, Any]) -> dict[str, Optional[float]]:
    """Split one request into the cash and quota bases (never blended).

    A subscription request is paid in allowance: its reported cost is the
    opportunity value of what it consumed, so ``cash`` is a real ``0.0`` while
    ``quota`` carries the number. A pay-as-you-go request is the opposite. An
    unknown reported cost stays ``None`` in both — not zero.
    """
    reported = row.get("reported_cost_usd")
    if reported is None:
        return {"cash_cost_usd": None, "quota_opportunity_units": None}
    if row.get("billing_class") == "subscription":
        return {"cash_cost_usd": 0.0, "quota_opportunity_units": float(reported)}
    return {"cash_cost_usd": float(reported), "quota_opportunity_units": 0.0}


def cost_facts(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate spend per account / provider, with failed-attempt cost visible.

    ``failed_cost_share`` is what makes a cheap-but-flaky route visible: it is
    the money that bought no successful response (in both bases).
    """
    accounts: dict[str, dict[str, Any]] = {}
    totals = {"requests": 0, "failed": 0, "unknown_cost": 0,
              "cash_usd": 0.0, "quota_value_usd": 0.0,
              "failed_cash_usd": 0.0, "failed_quota_value_usd": 0.0}
    for row in rows:
        basis = cost_basis_values(row)
        failed = bool(row.get("rejected")) or (row.get("status") or 0) >= 400
        key = row.get("account_id") or "unattributed"
        entry = accounts.setdefault(key, {
            "account_id": None if key == "unattributed" else key,
            "billing_class": row.get("billing_class"),
            "requests": 0, "failed": 0, "unknown_cost": 0,
            "cash_usd": 0.0, "quota_value_usd": 0.0,
            "swapped": 0, "providers": set(), "models": set(),
        })
        entry["requests"] += 1
        totals["requests"] += 1
        if failed:
            entry["failed"] += 1
            totals["failed"] += 1
        if row.get("swapped"):
            entry["swapped"] += 1
        if row.get("provider"):
            entry["providers"].add(row["provider"])
        if row.get("served_model"):
            entry["models"].add(row["served_model"])
        cash, quota = basis["cash_cost_usd"], basis["quota_opportunity_units"]
        if cash is None or quota is None:
            entry["unknown_cost"] += 1
            totals["unknown_cost"] += 1
            continue
        entry["cash_usd"] = round(entry["cash_usd"] + cash, 6)
        entry["quota_value_usd"] = round(entry["quota_value_usd"] + quota, 6)
        totals["cash_usd"] = round(totals["cash_usd"] + cash, 6)
        totals["quota_value_usd"] = round(totals["quota_value_usd"] + quota, 6)
        if failed:
            totals["failed_cash_usd"] = round(totals["failed_cash_usd"] + cash, 6)
            totals["failed_quota_value_usd"] = round(totals["failed_quota_value_usd"] + quota, 6)
    for entry in accounts.values():
        entry["providers"] = sorted(entry["providers"])
        entry["models"] = sorted(entry["models"])[:8]
        spend = entry["cash_usd"] + entry["quota_value_usd"]
        entry["spend_total"] = round(spend, 6)
    totals["spend_total"] = round(totals["cash_usd"] + totals["quota_value_usd"], 6)
    totals["failed_cost_share"] = (
        round((totals["failed_cash_usd"] + totals["failed_quota_value_usd"]) / totals["spend_total"], 4)
        if totals["spend_total"] else None)
    totals["basis_provenance"] = "magpie_reported_cost"
    return {"totals": totals, "accounts": accounts}


def read_usage_http(base_url: Optional[str] = None, *, period: str = "30d",
                    timeout: float = 5.0, opener: Any = None) -> Optional[dict[str, Any]]:
    """Fetch Magpie's aggregate usage over loopback HTTP (the app ships no CLI).

    Returns the parsed payload or ``None``. Read-only: it asks the app what it
    already recorded. Non-loopback URLs are refused outright, and no credential
    is read — the app accepts the same static loopback header the snapshot
    client uses.
    """
    url = (base_url or os.environ.get("REVERSE_AGENT_MAGPIE_URL")
           or DEFAULT_MAGPIE_URL).rstrip("/")
    if not url.startswith(LOOPBACK_PREFIXES):
        return None
    from urllib.request import Request

    from ..model_access import http_safe
    from ..model_access.magpie import MAGPIE_AUTH

    request = Request(f"{url}/v1/magpie/usage?period={period}",
                      headers={"Authorization": MAGPIE_AUTH}, method="GET")
    try:
        with (opener or http_safe.urlopen)(request, timeout=timeout) as response:
            payload = json.loads(response.read())
    except Exception:  # noqa: BLE001 - an absent app is a normal outcome
        return None
    return payload if isinstance(payload, dict) else None


def facts_from_http(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Aggregate facts from the HTTP view, in the shape :func:`cost_facts` returns.

    The HTTP view is **aggregate-only**: per account it reports calls, errors and
    one cost total, but not per-request rows and not a cash/subscription split.
    So this deliberately leaves ``cash_usd`` and ``quota_value_usd`` at zero and
    puts the reported total in ``reported_cost_usd`` / ``spend_total``, named by
    ``basis_provenance``. Reading that field as "money billed" would be wrong:
    most of it is subscription allowance valued at list price.

    ``failed_cost_share`` is ``None`` here for the same reason — the app counts
    errors but does not price them per request.
    """
    if not isinstance(payload, Mapping):
        payload = {}
    reported = _as_float(payload.get("cost"))
    calls = int(_as_float(payload.get("calls")) or 0)
    errors = int(_as_float(payload.get("errors")) or 0)
    unpriced = int(_as_float(payload.get("unpriced")) or 0)
    totals: dict[str, Any] = {
        "requests": calls, "failed": errors, "unknown_cost": unpriced,
        "cash_usd": 0.0, "quota_value_usd": 0.0,
        "failed_cash_usd": 0.0, "failed_quota_value_usd": 0.0,
        "reported_cost_usd": round(reported, 6),
        "spend_total": round(reported, 6),
        "failed_cost_share": None,
        "split_unavailable": True,
        "retried": int(_as_float(payload.get("retried")) or 0),
        "credits": _as_float(payload.get("credits")),
        "period": payload.get("period"),
        "since": payload.get("since"),
        # Latency aggregates the app already computed; kept raw, not re-derived.
        "timed": int(_as_float(payload.get("timed")) or 0),
        "ttft_ms_total": _as_float(payload.get("ttft_ms")),
        "decode_ms_total": _as_float(payload.get("decode_ms")),
        "decode_out": _as_float(payload.get("decode_out")),
        "decode_n": _as_float(payload.get("decode_n")),
        "basis_provenance": "magpie_http_reported_cost",
    }
    accounts: dict[str, dict[str, Any]] = {}
    for entry in payload.get("accounts") or []:
        if not isinstance(entry, Mapping):
            continue
        # Same identity discipline as the CSV path: the app returns a readable
        # handle (provider@user), which must never reach disk or a report.
        key = _account_id(entry.get("id") or entry.get("account")) or "unattributed"
        account_cost = _as_float(entry.get("cost")) or 0.0
        entry_calls = int(_as_float(entry.get("calls")) or 0)
        entry_errors = int(_as_float(entry.get("errors")) or 0)
        accounts[key] = {
            "account_id": key,
            "billing_class": None,
            "requests": entry_calls,
            "failed": entry_errors,
            "unknown_cost": int(_as_float(entry.get("unpriced")) or 0),
            "cash_usd": 0.0, "quota_value_usd": 0.0,
            "reported_cost_usd": round(account_cost, 6),
            "spend_total": round(account_cost, 6),
            "swapped": 0,
            "retried": int(_as_float(entry.get("retried")) or 0),
            "providers": [entry["provider"]] if entry.get("provider") else [],
            "models": [],
        }
    return {"totals": totals, "accounts": accounts}


def _as_float(value: Any) -> float:
    """Tolerant numeric read: Magpie omits fields it has no data for."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def default_cache_path() -> Path:
    base = os.environ.get("REVERSE_AGENT_RUNTIME_DIR") or str(Path.cwd() / ".platform_v1_runtime")
    return Path(base) / "magpie_usage_cache.jsonl"


def merge_into_cache(rows: Iterable[Mapping[str, Any]], *,
                     path: Optional[Path] = None,
                     limit: int = CACHE_LIMIT) -> int:
    """Append unseen requests to the JSONL cache, keeping the newest ``limit``.

    Dedupe is by ``request_id``: re-reading an overlapping window must not
    double-count spend. Written atomically so a crash cannot truncate history.
    """
    target = Path(path) if path is not None else default_cache_path()
    known: dict[str, dict[str, Any]] = {}
    if target.exists():
        try:
            with target.open("r", encoding="utf-8") as stream:
                for line in stream:
                    try:
                        item = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(item, dict) and item.get("request_id"):
                        known[item["request_id"]] = item
        except OSError:
            known = {}
    added = 0
    for row in rows:
        request_id = row.get("request_id")
        if not request_id or request_id in known:
            continue
        known[request_id] = dict(row)
        added += 1
    if not added:
        return 0
    ordered = sorted(known.values(), key=lambda item: str(item.get("time") or ""))[-limit:]
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            for item in ordered:
                stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return added


def read_cache(path: Optional[Path] = None) -> list[dict[str, Any]]:
    target = Path(path) if path is not None else default_cache_path()
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with target.open("r", encoding="utf-8") as stream:
            for line in stream:
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                if isinstance(item, dict):
                    rows.append(item)
    except OSError:
        return []
    return rows


def ingest(*, last: str = DEFAULT_LAST, timeout: float = DEFAULT_TIMEOUT,
           cache_path: Optional[Path] = None,
           env: Mapping[str, str] | None = None,
           source: str = "auto",
           base_url: Optional[str] = None,
           http_fetch: Any = None) -> dict[str, Any]:
    """One read-only refresh; CSV when a CLI exists, HTTP aggregates otherwise.

    ``source`` is ``auto`` (CLI first, then HTTP), ``cli`` (CSV only) or ``http``
    (aggregates only). The desktop app ships no CLI, so without the HTTP path a
    real installation reports ``magpie_executable_not_configured`` forever and
    the cost basis silently stays at the local list-price estimate. The two
    sources answer different questions: only the CSV has per-request rows, so
    ``spend_total`` is comparable but ``cash_usd`` / ``quota_value_usd`` and
    task correlation still require the CLI.

    Returns ``{"available", "reason", "source", "added", "rows", "facts"}``.
    Unavailable Magpie is a normal outcome, not an error.
    """
    chosen = str(source or "auto").lower()
    if chosen not in {"auto", "cli", "http"}:
        chosen = "auto"
    if chosen in {"auto", "cli"}:
        exe = magpie_executable(env)
        if exe is not None:
            rows = read_usage(exe, last=last, timeout=timeout)
            if rows:
                added = merge_into_cache(rows, path=cache_path)
                return {"available": True, "reason": None, "source": "cli",
                        "added": added, "rows": len(rows), "facts": cost_facts(rows),
                        "cache_rows": len(read_cache(cache_path))}
        if chosen == "cli":
            return {"available": False, "reason": "magpie_executable_not_configured",
                    "source": "cli", "added": 0, "rows": 0, "facts": cost_facts([])}
    payload = (http_fetch or read_usage_http)(base_url, period=last, timeout=timeout)
    if isinstance(payload, Mapping) and payload:
        return {"available": True, "reason": None, "source": "http", "added": 0,
                "rows": 0, "facts": facts_from_http(payload),
                "period": payload.get("period")}
    reason = "magpie_executable_not_configured" if chosen == "auto" else "magpie_http_unavailable"
    return {"available": False, "reason": reason, "source": "http", "added": 0,
            "rows": 0, "facts": cost_facts([])}


def main(argv: Optional[list[str]] = None) -> int:
    """``python -m reverse_agent.platform_v1.magpie_usage_ingest --json``."""
    import argparse
    parser = argparse.ArgumentParser(description="Read Magpie usage (read-only) into the local cache.")
    parser.add_argument("--last", default=DEFAULT_LAST, help="window such as 2h, 90m, 7d")
    parser.add_argument("--json", action="store_true", help="print the normalized aggregate")
    args = parser.parse_args(argv)
    result = ingest(last=args.last)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"available={result['available']} reason={result['reason']} "
              f"rows={result['rows']} added={result['added']}")
        totals = result["facts"]["totals"]
        print(f"cash=${totals['cash_usd']} quota_value=${totals['quota_value_usd']} "
              f"failed_share={totals['failed_cost_share']}")
    return 0 if result["available"] else 1


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())


# --- conservative attribution to task attempts ----------------------------------
#
# Magpie reports a session UUID, not a Nerelan task id, and there is no shared
# join key yet (P1 step 2). Rather than invent one, an attempt window plus the
# executor's agent name decides attribution, and **only when exactly one
# attempt matches**. Two overlapping attempts leave the request `ambiguous`:
# splitting spend evenly would manufacture a number that no evidence supports.

# Magpie's agent names per executor kind. Only verified pairs are listed; an
# executor not listed here simply never matches, instead of guessing.
AGENTS_BY_EXECUTOR: dict[str, frozenset[str]] = {
    "codex": frozenset({"codex"}),
    "claude_code": frozenset({"claude", "claude-desktop"}),
}

ATTRIBUTION_SLACK_SECONDS = 120.0


def _epoch(value: Any) -> Optional[float]:
    """ISO timestamp -> epoch seconds; ``None`` when unreadable."""
    from datetime import datetime
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def attempts_from_store(store: Any, *, limit: int = 200,
                        accepted_statuses: Optional[set[str]] = None) -> list[dict[str, Any]]:
    """Recent finished tasks, shaped as attribution windows.

    ``accepted`` reuses the ledger's definition of a successful run, so cost per
    accepted change here and in :func:`usage_ledger.task_token_records` agree.
    """
    from .usage_ledger import OK_STATUSES
    statuses = accepted_statuses if accepted_statuses is not None else set(OK_STATUSES)
    rows = store._conn.execute(
        "SELECT id, status, executor_kind, orchestration_mode, created_at, updated_at "
        "FROM tasks WHERE binding_ref <> '' ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
    sessions = _agent_sessions(store, [row["id"] for row in rows])
    attempts = []
    for row in rows:
        started, finished = _epoch(row["created_at"]), _epoch(row["updated_at"])
        if started is None:
            continue
        attempts.append({
            "task_id": row["id"],
            "executor_kind": row["executor_kind"],
            "mode": row["orchestration_mode"] or "single",
            "started_at": started,
            "finished_at": finished if finished is not None and finished >= started else started,
            "accepted": row["status"] in statuses,
            "status": row["status"],
            "agent_session_id": sessions.get(row["id"]),
        })
    return attempts


def _agent_sessions(store: Any, task_ids: list[str]) -> dict[str, str]:
    """The agent session id each attempt reported, when the executor exposes one.

    Written by the executor into ``EXECUTOR_COMPLETED.metadata.agent_session_id``.
    Absent for executors that do not publish one; those attempts stay on the
    time-window fallback instead of being excluded.
    """
    if not task_ids:
        return {}
    import json
    marks = ",".join("?" * len(task_ids))
    found: dict[str, str] = {}
    rows = store._conn.execute(
        f"SELECT e.task_id, e.metadata FROM task_events e JOIN ("
        f"  SELECT task_id, MAX(seq) AS seq FROM task_events "
        f"  WHERE type = 'EXECUTOR_COMPLETED' AND task_id IN ({marks}) GROUP BY task_id"
        f") latest ON latest.task_id = e.task_id AND latest.seq = e.seq", tuple(task_ids)).fetchall()
    for row in rows:
        try:
            metadata = json.loads(row["metadata"] or "{}")
        except (TypeError, ValueError):
            continue
        if isinstance(metadata, dict):
            session = metadata.get("agent_session_id")
            if isinstance(session, str) and session:
                found[row["task_id"]] = session
    return found


def correlate_usage(rows: Iterable[Mapping[str, Any]],
                    attempts: Iterable[Mapping[str, Any]], *,
                    slack_seconds: float = ATTRIBUTION_SLACK_SECONDS,
                    agents_by_executor: Optional[Mapping[str, Iterable[str]]] = None) -> dict[str, Any]:
    """Attribute each request to at most one attempt, or say why it could not be.

    Returns ``{"attempts": {task_id: {...}}, "unattributed": [...],
    "ambiguous": [...], "summary": {...}}``. A request is attributed only when
    its provider agent matches the executor **and** its time falls inside the
    attempt window (plus slack) **and** exactly one attempt qualifies.
    """
    mapping = {key: {str(a) for a in value} for key, value in
               (agents_by_executor or AGENTS_BY_EXECUTOR).items()}
    windows = []
    for attempt in attempts:
        windows.append({
            "task_id": attempt["task_id"],
            "agents": mapping.get(str(attempt.get("executor_kind")), set()),
            "start": float(attempt["started_at"]) - slack_seconds,
            "end": float(attempt["finished_at"]) + slack_seconds,
            "mode": attempt.get("mode") or "single",
            "accepted": bool(attempt.get("accepted")),
            "status": attempt.get("status"),
            "agent_session_id": attempt.get("agent_session_id"),
            "rows": [],
        })
    by_task = {window["task_id"]: window for window in windows}
    unattributed: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    by_session = {window["agent_session_id"]: window for window in windows
                  if window.get("agent_session_id")}
    for row in rows:
        at = _epoch(row.get("time"))
        session = str(row.get("session") or "").strip()
        exact = by_session.get(session) if session else None
        if exact is not None:
            # An exact id needs no window and cannot be ambiguous.
            exact["rows"].append(row)
            continue
        agent = str(row.get("agent") or row.get("provider") or "").strip().lower()
        if at is None or not agent:
            unattributed.append({"request_id": row.get("request_id"), "reason": "no_time_or_agent"})
            continue
        matches = [window for window in windows
                   if at >= window["start"] and at <= window["end"] and agent in window["agents"]]
        if not matches:
            unattributed.append({"request_id": row.get("request_id"), "reason": "no_matching_attempt"})
            continue
        if len(matches) > 1:
            ambiguous.append({"request_id": row.get("request_id"),
                              "candidates": [window["task_id"] for window in matches]})
            continue
        matches[0]["rows"].append(row)

    for window in windows:
        windows_rows = window.pop("rows")
        cash = quota = 0.0
        unknown = 0
        for row in windows_rows:
            basis = cost_basis_values(row)
            if basis["cash_cost_usd"] is None or basis["quota_opportunity_units"] is None:
                unknown += 1
                continue
            cash += basis["cash_cost_usd"]
            quota += basis["quota_opportunity_units"]
        window.update({
            "requests": len(windows_rows),
            "unknown_cost_requests": unknown,
            "cash_cost_usd": round(cash, 6),
            "quota_opportunity_units": round(quota, 6),
            "spend_total": round(cash + quota, 6),
        })
    attributed = sum(window["requests"] for window in windows)
    row_times = [_epoch(row.get("time")) for row in rows]
    row_times = [value for value in row_times if value is not None]
    usage_window = [min(row_times), max(row_times)] if row_times else None
    overlapping = [window for window in windows
                   if usage_window and window["end"] >= usage_window[0]
                   and window["start"] <= usage_window[1]]
    return {
        "attempts": {task_id: window for task_id, window in by_task.items()},
        "unattributed": unattributed,
        "ambiguous": ambiguous,
        "summary": {
            "requests": attributed + len(unattributed) + len(ambiguous),
            "attributed": attributed,
            "unattributed": len(unattributed),
            "ambiguous": len(ambiguous),
            # 0 attributed with 0 overlapping attempts means the two datasets do
            # not cover the same period — a data fact, not a matching failure.
            "exact_attempts": sum(1 for window in windows if window.get("agent_session_id")),
            "overlap_attempts": len(overlapping),
            # No usage rows means no overlap at all — not "partial". Reporting
            # partial here used to make an empty dataset look mildly usable.
            "overlap": ("none" if not usage_window or not windows or not overlapping
                        else "full" if len(overlapping) == len(windows) else "partial"),
            "usage_window": usage_window,
            "ambiguity_rate": round(
                (len(ambiguous) / (attributed + len(ambiguous))), 4)
            if attributed + len(ambiguous) else None,
        },
    }


def economics_runs(correlated: Mapping[str, Any], *, strict: bool = True) -> list[dict[str, Any]]:
    """Shape attributed attempts as ``all_in_economics`` input rows.

    ``strict`` (the default, and the only setting fit for decisions) turns an
    incomplete attempt into ``None`` — unknown, not zero. An attempt whose
    requests could not all be matched may have spent money that simply is not
    visible here; pricing that at ``0.0`` would report "free" for work that
    certainly cost something. Pass ``strict=False`` only for a labelled lower
    bound in a dashboard, never to decide between strategies.
    """
    runs = []
    for task_id, window in sorted(correlated.get("attempts", {}).items()):
        complete = bool(window.get("requests")) and not window.get("unknown_cost_requests")
        cash = window.get("cash_cost_usd", 0.0)
        quota = window.get("quota_opportunity_units", 0.0)
        if strict and not complete:
            cash = quota = None
        runs.append({
            "mode": window.get("mode") or "single",
            "accepted": bool(window.get("accepted")),
            "task_count": 1,
            "tokens": {},
            "wall_seconds": None,
            "size_band": "unbanded",
            "task_id": task_id,
            "cash_cost_usd": cash,
            "quota_opportunity_units": quota,
            "cost_complete": complete,
        })
    return runs
