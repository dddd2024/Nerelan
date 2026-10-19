"""Pure per-task routing. Priors are bootstrap estimates, never measured claims.

Three completed attempts in a kind/difficulty bucket establish evidence. A bucket
with >=80% success and <=20% timeouts demonstrates that difficulty; otherwise
its tier is one lower. Exploration uses an injected draw (no hidden randomness).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

KINDS = frozenset({"code", "analysis", "writing", "research_design", "review"})
LEGACY_DIFFICULTY = {"simple": 2, "coder": 3, "complex": 4, "planner": 4, "reviewer": 4}
MIN_SAMPLES = 3


def task_traits(raw: Mapping[str, Any]) -> tuple[int, str]:
    role = raw.get("agent_role") or ""
    if isinstance(role, str):
        role = role.strip()
    if not isinstance(role, str) or (role and role not in LEGACY_DIFFICULTY):
        raise ValueError(f"unsupported_agent_role:{role}" if isinstance(role, str) else "unsupported_agent_role")
    difficulty = raw.get("difficulty", LEGACY_DIFFICULTY.get(role, 3))
    kind = raw.get("kind", "review" if role == "reviewer" else "code")
    if type(difficulty) is not int or not 1 <= difficulty <= 5:
        raise ValueError("invalid_task_difficulty")
    if not isinstance(kind, str) or kind not in KINDS:
        raise ValueError("invalid_task_kind")
    return difficulty, kind


def prior_tier(model: str) -> tuple[int, bool]:
    """Bootstrap family table: flagship=5, strong open=4, flash=3, lite/unknown=2.

    Match lite before flash; unknown families stay unproven until measured.
    Provider prefixes and dated family suffixes do not affect these estimates.
    """
    model = model.lower()
    if "flash-lite" in model:
        return 2, False
    for names, tier in ((("gpt-6", "opus", "sonnet"), 5),
                        (("kimi-k3", "deepseek-v4-pro"), 4),
                        (("glm-5.3", "flash"), 3)):
        if any(name in model for name in names):
            return tier, False
    return 2, True


def capability(model: str, profile: Mapping[str, Any], kind: str, difficulty: int) -> tuple[int, bool]:
    bucket = profile.get("task_buckets", {}).get(f"{kind}:{difficulty}", {})
    if bucket.get("attempts", 0) >= MIN_SAMPLES:
        good = bucket.get("success_rate", 0) >= .8 and bucket.get("timeouts", 0) / bucket["attempts"] <= .2
        return max(1, difficulty if good else difficulty - 1), False
    return prior_tier(model)


def model_identity(model: str) -> str:
    """Provider namespaces and free gateway suffixes do not make a new author."""
    return model.lower().rsplit("/", 1)[-1].removesuffix(":free").removesuffix("-free")


def select_model(candidates: Sequence[Mapping[str, Any]], *, difficulty: int, kind: str,
                 profiles: Mapping[str, Any] | None = None, role: str = "",
                 author_model: str = "", pin: str = "", failed_model: str = "",
                 failed_tier: int = 0, exploration_draw: float = 1.0,
                 exploration_budget: float = .1) -> dict[str, Any]:
    """Pick from public binding metadata and precomputed quota observations.

    Scores are lexicographic: cost, negative success rate, median turn seconds.
    Subscription cost ranges from 1 to 2 as headroom falls; paid API cost is 3.
    Pins override price/tier, while readiness, quota and review fitness still apply.
    The injected uniform draw gives easy tasks a default 10% exploration rate.
    """
    task_traits({"difficulty": difficulty, "kind": kind})
    ranked = []
    for candidate in candidates:
        if not candidate.get("enabled", True) or not candidate.get("runnable", True):
            continue
        if role == "planner" and candidate["executor_id"] not in {"codex", "claude_code"}:
            continue
        if (kind == "review" or role == "reviewer") and author_model and model_identity(candidate["model_id"]) == model_identity(author_model):
            continue
        quota = candidate.get("quota") or {}
        if quota.get("decision") in {"switch", "warn"}:
            continue
        profile = (profiles or {}).get(candidate["binding_id"], {})
        tier, unproven = capability(candidate["model_id"], profile, kind, difficulty)
        bucket = profile.get("task_buckets", {}).get(f"{kind}:{difficulty}", profile)
        cost_class = candidate.get("cost_class", "paid_api")
        headroom = max(.01, min(1., candidate.get("quota_headroom", 1.)))
        cost = {"free": 0., "subscription": 1. + (1. - headroom), "paid_api": 3.}[cost_class]
        success = bucket.get("success_rate")
        speed = bucket.get("median_ok_seconds")
        tier_source = "measured" if bucket.get("attempts", 0) >= MIN_SAMPLES and profile.get(
            "task_buckets", {}).get(f"{kind}:{difficulty}") else "prior"
        ranked.append(dict(candidate, tier=tier, tier_source=tier_source, unproven=unproven, cost_class=cost_class,
                           cost=cost, success_rate=success, speed=speed,
                           score=[cost, -(success if success is not None else -1),
                                  speed if speed is not None else float("inf")]))
    ranked.sort(key=lambda c: (*c["score"], c["binding_id"]))
    if not ranked:
        raise ValueError("no_runnable_model")
    pinned = next((c for c in ranked if c["binding_id"] == pin), None)
    if pin and pinned is None:
        raise ValueError("pinned_model_unavailable")
    pool = ranked
    if failed_model and not pinned:
        distinct = [c for c in pool if model_identity(c["model_id"]) != model_identity(failed_model)]
        pool = distinct or pool
        higher = [c for c in pool if c["tier"] > failed_tier]
        if higher:
            pool = higher
        else:
            same = [c for c in pool if c["tier"] == failed_tier]
            pool = same or [c for c in pool if c["tier"] == max(item["tier"] for item in pool)]
    qualifying = [c for c in pool if c["tier"] >= difficulty]
    exploratory = [c for c in pool if c["unproven"] and c["cost_class"] == "free"]
    reason = "cheapest_qualifying"
    if pinned:
        chosen, reason = pinned, "pin"
    elif not failed_model and difficulty <= 2 and exploration_draw < exploration_budget and exploratory:
        chosen, reason = exploratory[0], "exploration"
    elif qualifying:
        chosen = qualifying[0]
    else:
        chosen, reason = max(pool, key=lambda c: c["tier"]), "underpowered"
    if failed_model and not pinned and reason != "underpowered":
        reason = ("escalation_higher_tier" if chosen["tier"] > failed_tier else
                  "retry_different_model" if model_identity(chosen["model_id"]) != model_identity(failed_model) else "retry_only_model")
    # JSON-safe evidence: unknown speed is null, never Infinity.
    for item in ranked:
        if item["score"][2] == float("inf"):
            item["score"][2] = None
    top = ranked[:5]
    if chosen not in top:
        top = [*top[:4], chosen]
    evidence = [{key: item[key] for key in ("binding_id", "model_id", "executor_id", "tier", "tier_source", "unproven",
                                            "cost_class", "cost", "success_rate", "speed", "score")}
                for item in top]
    return {"difficulty": difficulty, "kind": kind, "binding_ref": chosen["binding_id"],
            "executor_kind": chosen["executor_id"], "tier": chosen["tier"], "reason": reason,
            "underpowered": chosen["tier"] < difficulty, "candidates": evidence}
