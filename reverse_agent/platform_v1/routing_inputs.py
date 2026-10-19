"""Small provider-free contracts for routing; forecasts never grant capacity.

The reset reader is injected by the host until codex_reset_signals is available.
Only a validated PLAN_ONLY announcement with an absolute time enables draining.
"""
from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

NEEDS = frozenset({"long_context", "tool_use", "vision", "security_simulation", "chinese", "low_latency"})
# Owner-observed gateway plans, 2026-10-19; entitlement still needs verification.
GATEWAY_COST_CLASSES = {"workbuddy": "free", "workbuddy-ai": "free", "trae-cn": "free",
                        "opencode-zen-free": "free", "copilot": "subscription",
                        "codex": "subscription", "claude": "subscription"}

REFUSAL_PATTERNS = tuple(re.compile(pattern, re.I) for pattern in (
    r"^\s*(?:(?:I'm sorry|I am sorry|Sorry)[, .!\s]*(?:but\s+)?)?I (?:cannot|can't|won't|will not|am unable to) (?:help|assist|comply|perform|provide|carry out|fulfill|participate)",
    r"^\s*I'm unable to (?:help|assist|comply|perform|provide|carry out|fulfill|participate)",
    r"^\s*I (?:must|have to) decline (?:this|the|your) (?:request|task)",
    r"^\s*(?:This request|The task) (?:violates|is against) (?:my |our )?(?:safety|policy)",
    r"^\s*(?:\u62b1\u6b49|\u5bf9\u4e0d\u8d77)[\uff0c,\u3002\s]*(?:\u6211)?(?:\u65e0\u6cd5|\u4e0d\u80fd)(?:\u5e2e\u52a9|\u534f\u52a9|\u63d0\u4f9b|\u6267\u884c|\u53c2\u4e0e)",
))


def requirements(raw: Mapping[str, Any]) -> tuple[int, tuple[str, ...]]:
    context = raw.get("context_need", 0)
    needs = raw.get("needs", ())
    if type(context) is not int or context < 0:
        raise ValueError("invalid_task_context_need")
    if not isinstance(needs, (list, tuple)) or any(not isinstance(n, str) or n not in NEEDS for n in needs):
        raise ValueError("invalid_task_needs")
    return context, tuple(sorted(set(needs)))


def model_refused(final_text: str, *, changed_files: Any = (), policy_refusal: bool = False) -> bool:
    """Changes override text heuristics; an executor policy report is explicit evidence."""
    text = final_text.replace("\u2019", "'") if isinstance(final_text, str) else ""
    return policy_refusal or (not changed_files and any(p.search(text) for p in REFUSAL_PATTERNS))


def binding_cost_class(binding: Mapping[str, Any], connection: Mapping[str, Any], owner: Mapping[str, Any]) -> str:
    explicit = owner.get("bindings", {}).get(binding["binding_id"], {}).get("cost_class")
    explicit = explicit or owner.get("connections", {}).get(binding["connection_id"], {}).get("cost_class")
    if explicit:
        return explicit
    if connection.get("auth_method") == "external_cli_session":
        return "subscription"
    model = binding["model_id"].lower()
    namespace = model.split("/", 1)[0]
    if namespace in GATEWAY_COST_CLASSES:
        return GATEWAY_COST_CLASSES[namespace]
    if connection.get("auth_method") == "none" or model.endswith((":free", "-free")):
        return "free"
    return GATEWAY_COST_CLASSES.get(model.split("/", 1)[0], "paid_api") if "/" in model else "paid_api"


def read_overrides(state_path: Path | None) -> dict[str, Any]:
    """Owner-owned JSON beside setup state: {bindings: {id: {...}}, reset_buffer: .03}."""
    if state_path is None:
        return {}
    path = Path(state_path).with_name("model_routing_overrides.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        raise ValueError("invalid_model_routing_overrides") from exc
    if not isinstance(data, dict) or not isinstance(data.get("bindings", {}), dict):
        raise ValueError("invalid_model_routing_overrides")
    for override in data.get("bindings", {}).values():
        if not isinstance(override, dict):
            raise ValueError("invalid_model_routing_overrides")
        if "cost_class" in override and (not isinstance(override["cost_class"], str) or override["cost_class"] not in {"free", "subscription", "paid_api"}):
            raise ValueError("invalid_model_routing_overrides")
        for key in ("reasoning", "chinese", "tool_use"):
            if key in override and type(override[key]) is not bool:
                raise ValueError("invalid_model_routing_overrides")
        if "tool_reliability" in override and (type(override["tool_reliability"]) not in (int, float)
                or not 0 <= override["tool_reliability"] <= 1):
            raise ValueError("invalid_model_routing_overrides")
        if "refusal_rates" in override and (not isinstance(override["refusal_rates"], dict)
                or any(type(v) not in (int, float) or not 0 <= v <= 1 for v in override["refusal_rates"].values())):
            raise ValueError("invalid_model_routing_overrides")
        if "median_ok_seconds" in override and (type(override["median_ok_seconds"]) not in (int, float)
                or not math.isfinite(override["median_ok_seconds"]) or override["median_ok_seconds"] < 0):
            raise ValueError("invalid_model_routing_overrides")
        if "notes" in override and not isinstance(override["notes"], str):
            raise ValueError("invalid_model_routing_overrides")
        for key in ("context_window", "max_output_tokens"):
            if key in override and (type(override[key]) is not int or override[key] <= 0):
                raise ValueError("invalid_model_routing_overrides")
        if "input_modalities" in override and (not isinstance(override["input_modalities"], list)
                or any(not isinstance(x, str) or x not in {"text", "image", "audio", "video"} for x in override["input_modalities"])):
            raise ValueError("invalid_model_routing_overrides")
        if "exclude" in override and type(override["exclude"]) is not bool:
            raise ValueError("invalid_model_routing_overrides")
        if "max_difficulty" in override and (type(override["max_difficulty"]) is not int or not 1 <= override["max_difficulty"] <= 5):
            raise ValueError("invalid_model_routing_overrides")
        for key in ("allowed_content", "denied_content"):
            if key in override and (not isinstance(override[key], list) or any(not isinstance(x, str) for x in override[key])):
                raise ValueError("invalid_model_routing_overrides")
    connections = data.get("connections", {})
    if not isinstance(connections, dict) or any(not isinstance(v, dict) or not isinstance(v.get("cost_class"), str) or v.get("cost_class") not in
            {"free", "subscription", "paid_api"} for v in connections.values()):
        raise ValueError("invalid_model_routing_overrides")
    paid = data.get("paid_api_windows", [])
    if not isinstance(paid, list) or any(not isinstance(v, str) or not v for v in paid):
        raise ValueError("invalid_model_routing_overrides")
    buffer = data.get("reset_buffer", .03)
    if type(buffer) not in (float, int) or not .0 <= buffer <= .2:
        raise ValueError("invalid_model_routing_overrides")
    return data


def reset_decision(signal: Mapping[str, Any] | None, *, now: float, buffer: float = .03,
                   weekly_remaining: float | None = None, demand: bool = True,
                   short_resets_at: float | None = None) -> dict[str, Any]:
    """Input: state, expected_reset_at (UTC ISO/epoch), announcement_id, validated.

    UNKNOWN/STALE and malformed or unvalidated announcements are neutral. Quota
    re-reads are requested after the time, even if the claimed reset did not occur.
    """
    signal = signal or {}
    state = signal.get("state", "UNKNOWN")
    if not isinstance(state, str) or state not in {"UNKNOWN", "STALE", "PLAN_ONLY", "REFRESH_QUOTA"}:
        state = "UNKNOWN"
    expected = signal.get("expected_reset_at")
    try:
        when = float(expected) if type(expected) in (int, float) else datetime.fromisoformat(
            expected.replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError, AttributeError, OverflowError):
        when = None
    if isinstance(expected, str) and not re.search(r"(?:Z|[+-]\d\d:\d\d)$", expected):
        when = None
    if when is None or not math.isfinite(when):
        expected = None
    if type(weekly_remaining) not in (int, float) or not math.isfinite(weekly_remaining):
        weekly_remaining = None
    else:
        weekly_remaining = max(0., min(1., weekly_remaining))
    valid = (signal.get("validated") is True and when is not None and math.isfinite(when)
             and signal.get("scope", "global") == "global" and signal.get("kind", "global_reset") == "global_reset")
    before = valid and state == "PLAN_ONLY" and now < when
    after = valid and state in {"PLAN_ONLY", "REFRESH_QUOTA"} and now >= when
    windows = math.ceil((when - now) / 18000) if before else None
    if before and short_resets_at is not None and short_resets_at > now:
        windows = 1 + math.ceil(max(0., when - short_resets_at) / 18000)
    unreliable = bool(after and now > when + 900 and weekly_remaining is not None and weekly_remaining < max(.2, buffer))
    return {"signal_state": state, "expected_reset_at": expected,
            "announcement_id": signal.get("announcement_id") if isinstance(signal.get("announcement_id"), str) else None, "drain_target": buffer if before else None,
            "remaining_buffer": min(buffer, max(0., weekly_remaining)) if weekly_remaining is not None else None,
            "weekly_remaining": weekly_remaining, "announced_at": signal.get("announced_at") if isinstance(signal.get("announced_at"), str) else None,
            "remaining_short_windows": windows,
            "target_per_short_window": max(0., weekly_remaining - buffer) / max(1, windows or 1)
                if before and weekly_remaining is not None else None, "drain": bool(before and demand and weekly_remaining is not None and weekly_remaining > buffer),
            "demand": "QUEUED_TASK" if demand else "NO_DEMAND",
            "refresh_quota": state == "REFRESH_QUOTA" or bool(after),
            "source_unreliable": unreliable, "cost_adjustment": 0.}
