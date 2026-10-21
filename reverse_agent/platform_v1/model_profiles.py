"""Per-agent profiles learned from real task outcomes (provider-free observation).

Each Binding pins one model behind one executor, so a profile keyed by binding_ref is a
(model x executor) profile: how often it succeeds, how it fails, how long a successful
turn takes and how many tokens it uses. Planning, policy and execution read these instead
of assuming every model behaves alike; e.g. a slow but productive model gets a longer turn.
"""

from __future__ import annotations

from datetime import datetime
import json
import math
import threading
import time
from statistics import median
from typing import Any

from .model_availability import provider_overloaded

from .durable_execution import DEFAULT_EXECUTOR_TIMEOUT_SECONDS, MAX_EXECUTOR_TIMEOUT_SECONDS

OK_STATUSES = frozenset({"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "COMPLETED"})
# OpenCode reports EXECUTOR_RUNNING; native CLIs start right after WORKSPACE_READY.
_STARTS, _ENDS = ("EXECUTOR_RUNNING", "WORKSPACE_READY"), ("EXECUTOR_COMPLETED", "EXECUTOR_FINISHED")
MIN_SAMPLES = 2


def _seconds(start: str, end: str) -> float | None:
    try:
        parse = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        delta = (parse(end) - parse(start)).total_seconds()
    except (TypeError, ValueError):
        return None
    return delta if delta >= 0 else None


def _p90(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(0.9 * len(ordered)) - 1)]


def compute_agent_profiles(store: Any, *, limit: int = 500) -> dict[str, dict[str, Any]]:
    """Profiles for the most recent ``limit`` model-backed tasks, keyed by binding_ref."""
    conn = store._conn
    tasks = conn.execute(
        "SELECT id, binding_ref, executor_kind, status, failure_classification, failure_detail FROM tasks "
        "WHERE binding_ref <> '' ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
    if not tasks:
        return {}
    ids = [row["id"] for row in tasks]
    marks = ",".join("?" * len(ids))
    spans: dict[str, list[str]] = {}
    for row in conn.execute(f"SELECT task_id, type, timestamp FROM task_events WHERE task_id IN ({marks}) "
                            "AND type IN (?, ?, ?, ?) ORDER BY seq", [*ids, *_STARTS, *_ENDS]):
        span = spans.setdefault(row["task_id"], ["", ""])
        if row["type"] in _STARTS and not span[0]:
            span[0] = row["timestamp"]
        elif row["type"] in _ENDS:
            span[1] = row["timestamp"]
    tokens: dict[str, int] = {}
    for row in conn.execute(
            f"SELECT task_id, SUM(COALESCE(input_units,0) + COALESCE(output_units,0)) AS units "
            f"FROM task_usage_observations WHERE status = 'OBSERVED' AND task_id IN ({marks}) GROUP BY task_id", ids):
        tokens[row["task_id"]] = int(row["units"] or 0)
    # Native CLIs keep budget usage UNKNOWN (no reasoning/cost figures), but their completion event
    # carries the token counts they did report; profiles use those for comparison only.
    for row in conn.execute(f"SELECT task_id, metadata FROM task_events WHERE type = 'EXECUTOR_COMPLETED' "
                            f"AND task_id IN ({marks})", ids):
        if row["task_id"] in tokens:
            continue
        try:
            usage = json.loads(row["metadata"] or "{}").get("token_usage")
        except (ValueError, AttributeError):
            usage = None
        if isinstance(usage, dict):
            counts = [usage.get(key) for key in ("input_tokens", "output_tokens")]
            if all(type(value) is int and value >= 0 for value in counts):
                tokens[row["task_id"]] = sum(counts)

    traits, contents = {}, {}
    for row in conn.execute(f"SELECT task_id, metadata FROM task_events WHERE type = 'MODEL_SELECTED' "
                            f"AND task_id IN ({marks}) ORDER BY seq", ids):
        try:
            data = json.loads(row["metadata"] or "{}")
            contents[row["task_id"]] = data.get("content_class", data.get("kind", "code"))
            if data.get("kind") and type(data.get("difficulty")) is int:
                traits[row["task_id"]] = f"{data['kind']}:{data['difficulty']}"
        except (ValueError, AttributeError):
            continue
    refused_tasks = {row["task_id"] for row in conn.execute(
        f"SELECT DISTINCT task_id FROM task_events WHERE type='MODEL_REFUSED' AND task_id IN ({marks})", ids)}
    grouped: dict[str, dict[str, Any]] = {}
    for row in tasks:
        profile = grouped.setdefault(row["binding_ref"], {
            "binding_ref": row["binding_ref"], "executor_kind": row["executor_kind"], "attempts": 0,
            "ok": 0, "failed": 0, "timeouts": 0, "rate_limited": 0, "failure_kinds": {}, "observed_tokens": 0,
            "_ok_seconds": [], "_timeout_seconds": [], "_ok_tokens": []})
        status = row["status"]
        classification = (row["failure_classification"] or "").lower()
        span = spans.get(row["id"], ["", ""])
        seconds = _seconds(span[0], span[1]) if span[0] and span[1] else None
        if classification.startswith("model_unavailable"):
            continue  # entitlement and transient dispatch errors are not capability evidence
        if status == "FAILED" and (classification.startswith("provider_overloaded")
                                   or provider_overloaded(row["failure_detail"] or "")):
            # Provider capacity is availability evidence, never capability evidence.
            profile["overloaded"] = profile.get("overloaded", 0) + 1
            continue
        content = contents.get(row["id"], "code")
        refused = row["id"] in refused_tasks or classification in {"model_refused", "no_willing_model"}
        if refused or status in OK_STATUSES or status == "FAILED":
            evidence = profile.setdefault("content_attempts", {}).setdefault(content, {"attempts": 0, "refusals": 0})
            evidence["attempts"] += 1
            evidence["refusals"] += int(refused)
        if refused:
            profile["observed_tokens"] += tokens.get(row["id"], 0)
            profile["refusal_tokens"] = profile.get("refusal_tokens", 0) + tokens.get(row["id"], 0)
            continue  # refusal is willingness evidence, never capability failure
        if any(code in classification for code in ("protocol", "malformed_tool", "tool_call")):
            profile["tool_errors"] = profile.get("tool_errors", 0) + 1
        if row["id"] in traits and (status in OK_STATUSES or status == "FAILED"):
            bucket = profile.setdefault("task_buckets", {}).setdefault(traits[row["id"]],
                        {"attempts": 0, "ok": 0, "timeouts": 0, "_seconds": [], "_tokens": []})
            bucket["attempts"] += 1
            bucket["ok"] += int(status in OK_STATUSES)
            bucket["timeouts"] += int("timeout" in classification)
            if seconds is not None and status in OK_STATUSES:
                bucket["_seconds"].append(seconds)
            if row["id"] in tokens and status in OK_STATUSES:
                bucket["_tokens"].append(tokens[row["id"]])
        if status in OK_STATUSES or status == "FAILED":
            profile["observed_tokens"] += tokens.get(row["id"], 0)
        if status in OK_STATUSES:
            profile["attempts"] += 1
            profile["ok"] += 1
            if seconds is not None:
                profile["_ok_seconds"].append(seconds)
            if row["id"] in tokens:
                profile["_ok_tokens"].append(tokens[row["id"]])
        elif status == "FAILED":
            profile["attempts"] += 1
            profile["failed"] += 1
            kind = classification.split(":")[0] or "unknown"
            profile["failure_kinds"][kind] = profile["failure_kinds"].get(kind, 0) + 1
            if "timeout" in classification:
                profile["timeouts"] += 1
                if seconds is not None:
                    profile["_timeout_seconds"].append(seconds)
            if "rate" in classification or "429" in classification or "quota" in classification:
                profile["rate_limited"] += 1
    for profile in grouped.values():
        profile["refusal_rates"] = {content: evidence["refusals"] / evidence["attempts"]
                                     for content, evidence in profile.get("content_attempts", {}).items()}
        profile["tool_reliability"] = 1 - profile.get("tool_errors", 0) / max(1, profile["attempts"])
        for bucket in profile.get("task_buckets", {}).values():
            values = bucket.pop("_seconds")
            bucket["success_rate"] = bucket["ok"] / bucket["attempts"]
            bucket["median_ok_seconds"] = median(values) if values else None
            bucket_tokens = bucket.pop("_tokens")
            bucket["median_ok_tokens"] = median(bucket_tokens) if bucket_tokens else None
        ok_seconds, ok_tokens = profile.pop("_ok_seconds"), profile.pop("_ok_tokens")
        timeout_seconds = profile.pop("_timeout_seconds")
        profile["failure_kinds"] = dict(sorted(profile["failure_kinds"].items(), key=lambda kv: -kv[1])[:4])
        profile["success_rate"] = round(profile["ok"] / profile["attempts"], 2) if profile["attempts"] else None
        profile["median_ok_seconds"] = round(median(ok_seconds)) if ok_seconds else None
        profile["p90_ok_seconds"] = round(_p90(ok_seconds)) if ok_seconds else None
        profile["median_ok_tokens"] = round(median(ok_tokens)) if ok_tokens else None
        profile["recommended_timeout_seconds"] = _recommend_timeout(ok_seconds, timeout_seconds)
    return grouped


def _recommend_timeout(ok_seconds: list[float], timeout_seconds: list[float]) -> int | None:
    """A turn limit that fits how long this agent actually needs, within the host bounds."""
    if len(ok_seconds) >= MIN_SAMPLES:
        wanted = math.ceil(_p90(ok_seconds) * 1.4)
    elif timeout_seconds:
        # Only ever cut off: give it the longest turn the host allows.
        wanted = MAX_EXECUTOR_TIMEOUT_SECONDS
    else:
        return None
    return max(DEFAULT_EXECUTOR_TIMEOUT_SECONDS, min(wanted, MAX_EXECUTOR_TIMEOUT_SECONDS))


MIN_ROUTING_ATTEMPTS = 3


def best_pairing(profiles: dict[str, dict[str, Any]], chosen: str, siblings: list[str]) -> str:
    """Among bindings of the same model on different executors, the one real runs favour.

    A sibling replaces the chosen binding only with enough evidence: at least
    MIN_ROUTING_ATTEMPTS finished attempts and a higher success rate, or the same rate
    and a faster typical successful turn than the chosen binding's own record. Until the
    chosen binding has that much evidence too, the configured choice stands.
    """
    def score(binding: str) -> tuple[float, float] | None:
        profile = profiles.get(binding)
        if not profile or profile.get("attempts", 0) < MIN_ROUTING_ATTEMPTS or profile.get("success_rate") is None:
            return None
        return (profile["success_rate"], -(profile.get("median_ok_seconds") or float("inf")))
    best, best_score = chosen, score(chosen)
    if best_score is None:
        return chosen
    for sibling in siblings:
        candidate = score(sibling)
        if candidate is not None and candidate > best_score:
            best, best_score = sibling, candidate
    return best


_CACHE_SECONDS = 60.0
_cache_lock = threading.Lock()


def cached_agent_profiles(store: Any) -> dict[str, dict[str, Any]]:
    """Profiles recomputed at most once a minute per store."""
    now = time.monotonic()
    with _cache_lock:
        cached = getattr(store, "_agent_profile_cache", None)
    if cached is None or now - cached[0] > _CACHE_SECONDS:
        cached = (now, compute_agent_profiles(store, limit=500))
        with _cache_lock:
            store._agent_profile_cache = cached
    return cached[1]


def recommended_timeout_seconds(store: Any, binding_ref: str) -> int | None:
    """Learned turn limit for one binding (from the cached profiles)."""
    if not binding_ref:
        return None
    return cached_agent_profiles(store).get(binding_ref, {}).get("recommended_timeout_seconds")
