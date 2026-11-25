"""Small provider-free contracts for routing; forecasts never grant capacity.

The reset reader is injected by the host until codex_reset_signals is available.
Only a validated PLAN_ONLY announcement with an absolute time enables draining.
"""
from __future__ import annotations

from datetime import datetime
import json
import logging
import math
from pathlib import Path
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

from .routing_capabilities import KINDS

NEEDS = frozenset({"long_context", "tool_use", "vision", "security_simulation", "chinese", "low_latency"})
COST_CLASSES = frozenset({"free", "subscription", "paid_api"})

# Built-in, Owner-editable cost defaults keyed by model-id namespace (the part
# before the first "/"). WorkBuddy/WorkBuddy-AI and Trae expose credit/plan
# subscriptions (docs/resource-management.md), so they are subscription rather
# than per-token paid routes. OpenCode Zen's free namespace and SenseNova's free
# gateway are free. Every entry can be overridden per binding, model or
# connection in model_routing_overrides.json; paid_api is reserved for
# per-token billed routes such as a non-free OpenRouter key.
GATEWAY_COST_CLASSES = {
    "workbuddy": "subscription",
    "workbuddy-ai": "subscription",
    "trae-cn": "subscription",
    "opencode-zen-free": "free",
    "sensenova": "free",
    "sensetime": "free",
    # Magpie's id for the SenseNova gateway (#1170).
    "token-sensenova": "free",
    "copilot": "subscription",
    "codex": "subscription",
    "claude": "subscription",
}

# Magpie routing ids (Owner decision 2026-11-17, "route by Magpie group, not account"):
# ``group/<id>`` names an Owner-created routing group whose members are several
# accounts serving the same model, and ``auto/<id>`` names Magpie's auto-router.
# The gateway fails over across members inside one request.
ROUTING_GROUP_NAMESPACES = ("group", "auto")


def routing_group_id(model_id: Any) -> str:
    """``group/<id>`` or ``auto/<id>`` named by a model id, lower-cased, else "".

    The id may carry one provider prefix (``magpie/group/<id>``), as a resolved
    binding's model id does. ``openrouter/auto`` names no group.
    """
    if not isinstance(model_id, str):
        return ""
    model = model_id.strip().lower()
    for candidate in (model, model.split("/", 1)[1] if "/" in model else ""):
        head, _, rest = candidate.partition("/")
        if head in ROUTING_GROUP_NAMESPACES and rest.strip("/"):
            return candidate
    return ""


def upstream_namespace(model_id: Any) -> str:
    """The upstream a gateway model id spends: ``trae-cn`` for ``trae-cn/glm-5.2``, else "".

    A routing group is its own upstream (``group:<id>``): its members are separate
    accounts, so one group's refusal or stall says nothing about another group or
    about a single-account binding.
    """
    group = routing_group_id(model_id)
    if group:
        head, _, rest = group.partition("/")
        return f"{head}:{rest}"
    model = str(model_id or "")
    return model.split("/", 1)[0].lower() if "/" in model else ""


def parse_groups(raw: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Valid Owner group declarations and the errors of the ignored ones.

    Shape: ``{"group/<id>": {"identity": "<model>", "members": ["<upstream>/<model>", ...]}}``.
    A key must name a ``group/`` or ``auto/`` id and the identity must be a non-empty
    string. An invalid entry is ignored (its group then stays undeclared, which review
    treats as never independent) and reported, without discarding the rest of the file.
    ``members`` is optional: the gateway model ids the group fails over across, as the
    gateway lists them. Invalid members are dropped and reported; the group stays declared.
    """
    if raw is None:
        return {}, []
    if not isinstance(raw, Mapping):
        return {}, ["invalid_model_routing_groups"]
    groups: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for key, value in raw.items():
        name = key.strip().lower() if isinstance(key, str) else ""
        identity = value.get("identity") if isinstance(value, Mapping) else None
        if (not name or not name.startswith(tuple(f"{n}/" for n in ROUTING_GROUP_NAMESPACES))
                or routing_group_id(name) != name or not isinstance(identity, str) or not identity.strip()):
            errors.append(f"invalid_model_routing_group:{key if isinstance(key, str) else type(key).__name__}")
            continue
        groups[name] = {"identity": identity.strip()}
        members = value.get("members")
        if members is not None:
            if (isinstance(members, list) and members
                    and all(isinstance(m, str) and "/" in m.strip() and not routing_group_id(m) for m in members)):
                groups[name]["members"] = [m.strip() for m in members]
            else:
                errors.append(f"invalid_model_routing_group_members:{key}")
    return groups, errors


def group_members(model_id: Any, groups: Mapping[str, Any] | None) -> tuple[str, ...]:
    """The member model ids the Owner declared for the routing group ``model_id`` names, or ()."""
    group = routing_group_id(model_id)
    if not group or not isinstance(groups, Mapping):
        return ()
    entry = groups.get(group)
    if entry is None:
        entry = next((value for key, value in groups.items()
                      if isinstance(key, str) and key.strip().lower() == group), None)
    members = entry.get("members") if isinstance(entry, Mapping) else None
    return tuple(m for m in members if isinstance(m, str)) if isinstance(members, list) else ()


def paced_group_provider(model_id: Any, groups: Mapping[str, Any] | None, paced: Any) -> str:
    """The first paced upstream among a declared group's members, or "".

    A group that fails over onto a paced account (``codex/...``) spends that account's
    weekly allowance, so it is paced against that account like a direct gateway model.
    """
    for member in group_members(model_id, groups):
        namespace = member.split("/", 1)[0].lower()
        if namespace in paced:
            return namespace
    return ""


_READY_STATES = frozenset({"AVAILABLE", "READY"})


def inherit_group_availability(candidates: list[dict[str, Any]], groups: Mapping[str, Any] | None,
                               paced: Any = ()) -> None:
    """A declared group with no availability evidence of its own takes a member's.

    Availability comes from the binding's own task history or a probe; a new group has
    neither, so it stayed UNKNOWN and ranked behind every single account it fails over
    across, and was never chosen (2026-11-18). A group is AVAILABLE when a declared
    member binding on the same connection is AVAILABLE/READY. Members on a paced
    upstream never lend availability: the group's own pacing decides those.
    """
    ready = {(c.get("connection_id"), str(c.get("model_id", "")).lower()): c.get("binding_id")
             for c in candidates if not routing_group_id(c.get("model_id"))
             and str((c.get("availability") or {}).get("state", "UNKNOWN")).upper() in _READY_STATES}
    for candidate in candidates:
        members = group_members(candidate.get("model_id"), groups)
        if not members or str((candidate.get("availability") or {}).get("state", "UNKNOWN")).upper() != "UNKNOWN":
            continue
        for member in members:
            if member.split("/", 1)[0].lower() in paced:
                continue
            source = ready.get((candidate.get("connection_id"), member.lower()))
            if source:
                candidate["availability"] = {"state": "AVAILABLE", "reason": "group_member_available",
                                             "member_binding": source}
                break


# Weekly pacing for subscription accounts whose weekly allowance must last the
# week (Owner requirement 2026-11-07): use may run ahead of elapsed time by
# `slack` and never past `1 - reserve`. Keyed by executor id for the native CLIs and,
# for gateways such as Magpie, by the upstream account a model id names
# ("claude/...", "codex/..."): the same weekly allowance, whatever executor runs it.
DEFAULT_WEEKLY_PACE: dict[str, Any] = {
    "enabled": True, "executors": ["codex", "claude_code"], "providers": ["codex", "claude"],
    "slack": .10, "reserve": .10,
    # The reserve is released this many hours before the weekly reset; 0 keeps it to the end.
    "reserve_release_hours": 0,
    # True (Owner decision 2026-11-25): ahead-of-pace slows selection via soft
    # penalty rather than hard exclusion; reserve and freshness holds stay hard.
    "soft_pacing": True,
    # True: a paced account whose weekly usage is unknown or stale is held, not
    # left to the other quota rules (Owner decision 2026-11-08, long-run plan).
    "require_fresh": False}


# Paid subscriptions that run only in their official agent, never through a gateway
# (Owner decision 2026-11-23, #1743): gateway provider name -> the model families its
# accounts serve. The families decide ids that name no provider and groups whose
# members are unknown. Copilot, WorkBuddy, Trae and other non-paid sources are absent.
DEFAULT_PAID_SUBSCRIPTIONS: dict[str, Any] = {"providers": {
    "claude": ["claude", "opus", "sonnet", "haiku", "fable"],
    "codex": ["gpt", "o1", "o3", "o4"],
    "chatgpt": ["gpt"],
    "antigravity": ["gemini"],
}}
_PLAIN_WORD = re.compile(r"[a-z0-9]{1,40}")


def _valid_paid_subscriptions(raw: Any) -> bool:
    providers = raw.get("providers") if isinstance(raw, dict) and set(raw) == {"providers"} else None
    return (isinstance(providers, dict) and bool(providers)
            and all(isinstance(name, str) and _PLAIN_WORD.fullmatch(name) and isinstance(families, list)
                    and all(isinstance(family, str) and _PLAIN_WORD.fullmatch(family) for family in families)
                    for name, families in providers.items()))


def weekly_pace_config(owner: Mapping[str, Any]) -> dict[str, Any]:
    """Owner overrides on top of the defaults; read_overrides already validated them."""
    return {**DEFAULT_WEEKLY_PACE, **(owner.get("weekly_pace") or {})}


# Shipped shape of the Owner-editable file. The maps start empty so no runtime
# connection id is hard-coded; the namespace defaults above already apply.
# Copy this structure with `default_overrides()` into model_routing_overrides.json
# beside model_setup_state.json to override any decision.
DEFAULT_MODEL_ROUTING_OVERRIDES: dict[str, Any] = {
    "bindings": {}, "models": {}, "connections": {}, "paid_api_windows": [], "reset_buffer": .03,
}

_SENSENOVA_HOST_SUFFIX = "sensenova.cn"
_SENSENOVA_PROVIDER_IDS = frozenset({"sensetime", "sensenova"})

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


def default_overrides() -> dict[str, Any]:
    """A fresh copy of the shipped, Owner-editable configuration template."""
    return json.loads(json.dumps(DEFAULT_MODEL_ROUTING_OVERRIDES))


def _cost_entry(value: Any) -> str | None:
    """The validated cost class of one Owner override entry, or ``None``."""
    if isinstance(value, str):
        return value if value in COST_CLASSES else None
    if isinstance(value, Mapping):
        cost = value.get("cost_class")
        return cost if cost in COST_CLASSES else None
    return None


def _owner_cost(owner: Mapping[str, Any] | None, section: str, key: Any) -> str | None:
    if not isinstance(owner, Mapping) or not isinstance(key, str) or not key:
        return None
    entries = owner.get(section)
    if not isinstance(entries, Mapping):
        return None
    value = entries.get(key)
    if value is None:
        lowered = key.lower()
        value = next((entry for name, entry in entries.items()
                      if isinstance(name, str) and name.lower() == lowered), None)
    return _cost_entry(value)


def _connection_host(connection: Mapping[str, Any] | None) -> str:
    base = connection.get("base_url") if isinstance(connection, Mapping) else None
    if not isinstance(base, str):
        return ""
    try:
        return (urlsplit(base).hostname or "").lower()
    except ValueError:
        return ""


def _is_sensenova_gateway(connection: Mapping[str, Any] | None) -> bool:
    connection = connection or {}
    if any(isinstance(connection.get(key), str)
           and connection[key].lower() in _SENSENOVA_PROVIDER_IDS
           for key in ("upstream_provider_id", "executor_provider_id", "provider")):
        return True
    host = _connection_host(connection)
    return host == _SENSENOVA_HOST_SUFFIX or host.endswith("." + _SENSENOVA_HOST_SUFFIX)


def explicit_cost_class(binding: Mapping[str, Any], connection: Mapping[str, Any], owner: Mapping[str, Any]) -> str:
    """The Owner's own cost class for this binding, model or connection, or "" when unset."""
    binding, connection = binding or {}, connection or {}
    model_id = binding.get("model_id") if isinstance(binding.get("model_id"), str) else ""
    return (_owner_cost(owner, "bindings", binding.get("binding_id"))
            or _owner_cost(owner, "models", model_id)
            or _owner_cost(owner, "connections", binding.get("connection_id")) or "")


def binding_cost_class(binding: Mapping[str, Any], connection: Mapping[str, Any], owner: Mapping[str, Any]) -> str:
    """Resolve a binding's cost class with explicit Owner precedence.

    Precedence: Owner per-binding, then per-model, then per-connection override.
    Otherwise native CLI accounts are subscriptions, ids ending ``:free`` or
    ``-free`` are free, known namespaces and the SenseNova gateway use their
    built-in class, keyless endpoints are free, and every other per-token route
    is ``paid_api``. An API key alone never grants free access.
    """
    binding, connection = binding or {}, connection or {}
    model_id = binding.get("model_id")
    model_id = model_id if isinstance(model_id, str) else ""
    explicit = (_owner_cost(owner, "bindings", binding.get("binding_id"))
                or _owner_cost(owner, "models", model_id)
                or _owner_cost(owner, "connections", binding.get("connection_id")))
    if explicit:
        return explicit
    if connection.get("auth_method") == "external_cli_session":
        return "subscription"
    model = model_id.lower()
    if model.endswith((":free", "-free")):
        return "free"
    declared = owner.get("groups") if isinstance(owner, Mapping) else None
    if (connection.get("auth_method") == "none" and model.startswith("group/")
            and isinstance(declared, Mapping)
            and any(isinstance(name, str) and name.lower() == model for name in declared)):
        # A routing group the Owner declared fails over across the Owner's own
        # subscription accounts (2026-11-17). Undeclared groups and Magpie's own
        # auto/<model> groups may include per-token members (e.g. OpenRouter), so
        # they keep the paid default below until the Owner classifies them (#1661 review).
        return "subscription"
    namespace = model.split("/", 1)[0]
    if namespace in GATEWAY_COST_CLASSES:
        return GATEWAY_COST_CLASSES[namespace]
    if _is_sensenova_gateway(connection):
        return "free"
    if connection.get("auth_method") == "none" and "/" not in model:
        # A keyless local model (Ollama-style id). A keyless *gateway* such as Magpie
        # forwards "upstream/model" ids to accounts that may bill per token, so an
        # unlisted upstream namespace stays paid until the Owner classifies it.
        return "free"
    return "paid_api"


def read_overrides(state_path: Path | None) -> dict[str, Any]:
    """Owner-owned JSON beside setup state: {bindings/models/connections/groups, reset_buffer}."""
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
        if "tiers" in override and (not isinstance(override["tiers"], dict)
                or any(k not in KINDS or type(v) is not int or not 1 <= v <= 5
                       for k, v in override["tiers"].items())):
            raise ValueError("invalid_model_routing_overrides")
        if "cost_class" in override and _cost_entry(override) is None:
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
    for section in ("connections", "models"):
        entries = data.get(section, {})
        if (not isinstance(entries, dict) or any(
                not isinstance(name, str) or not name or _cost_entry(value) is None
                for name, value in entries.items())):
            raise ValueError("invalid_model_routing_overrides")
    paid = data.get("paid_api_windows", [])
    if not isinstance(paid, list) or any(not isinstance(v, str) or not v for v in paid):
        raise ValueError("invalid_model_routing_overrides")
    buffer = data.get("reset_buffer", .03)
    if type(buffer) not in (float, int) or not .0 <= buffer <= .2:
        raise ValueError("invalid_model_routing_overrides")
    if type(data.get("availability_probes", True)) is not bool:
        raise ValueError("invalid_model_routing_overrides")
    groups, group_errors = parse_groups(data.get("groups"))
    data["groups"] = groups
    if group_errors:
        data["group_errors"] = group_errors
        logging.getLogger(__name__).warning("model_routing_overrides.json: ignored %s", ", ".join(group_errors))
    if "paid_subscriptions" in data and not _valid_paid_subscriptions(data["paid_subscriptions"]):
        raise ValueError("invalid_model_routing_overrides")
    pace = data.get("weekly_pace", {})
    if (not isinstance(pace, dict) or set(pace) - set(DEFAULT_WEEKLY_PACE)
            or any(key in pace and type(pace[key]) is not bool for key in ("enabled", "require_fresh", "soft_pacing"))
            or any(key in pace and (not isinstance(pace[key], list)
                                    or any(not isinstance(x, str) or not x for x in pace[key]))
                   for key in ("executors", "providers"))
            or any(key in pace and (type(pace[key]) not in (int, float) or not 0 <= pace[key] <= .5)
                   for key in ("slack", "reserve"))
            or "reserve_release_hours" in pace and (
                type(pace["reserve_release_hours"]) not in (int, float)
                or not 0 <= pace["reserve_release_hours"] <= 72)):
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
