"""One read-only view of every AI resource the host can use (P0-3, #1151).

It joins what already exists instead of adding a second authority: Connections
(API keys and subscription CLI accounts), the executors each one can drive and
whether they are ready, the model x executor Bindings, and what Nerelan itself
observed those Bindings do. Provider-side balance or quota is reported only when
an official source supplies it; otherwise it is UNKNOWN, never a guess or zero.

Nothing here reads secrets, calls a provider or writes state.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .contracts import NATIVE_CLI_PROVIDERS, is_anthropic_relay_connection
from .pricing import equivalent_cost

# Observed usage covers this many recent model-backed tasks (the agent-profile window).
OBSERVATION_WINDOW_TASKS = 500

_PROFILE_FIELDS = ("attempts", "ok", "failed", "timeouts", "rate_limited", "success_rate",
                   "median_ok_seconds", "median_ok_tokens", "observed_tokens")
_TOTAL_FIELDS = ("attempts", "ok", "failed", "observed_tokens")

UNKNOWN_QUOTA = {"state": "UNKNOWN", "provenance": "UNAVAILABLE", "reason": "no_official_quota_source", "windows": []}
_TOKEN_COUNTERS = ("input", "cache_read", "cache_write", "output", "reasoning")


def _credential(connection: Mapping[str, Any]) -> dict[str, Any]:
    auth = connection.get("auth_method")
    if auth == "api_key":
        return {"kind": "api_key", "configured": connection.get("credential_configured") is True,
                "status": connection.get("secret_status")}
    if auth in {"external_cli_session", "account_login"}:
        status = connection.get("external_session_status")
        return {"kind": "subscription", "configured": status in {"available", "executor_managed"},
                "status": status}
    return {"kind": "none", "configured": True, "status": "not_applicable"}


def _executor_ready(executor: Mapping[str, Any] | None, connection: Mapping[str, Any]) -> bool:
    if executor is None:
        return False
    if executor.get("operational") is True:
        return True
    # The Claude Code relay runs on the connection's key, not a claude.ai login.
    return (executor.get("executor_id") == "claude_code"
            and executor.get("readiness_status") == "managed_login_unavailable"
            and is_anthropic_relay_connection(connection))


def _session_usable(connection: Mapping[str, Any]) -> bool:
    """The resolver refuses a CLI-session binding whose session is not available."""
    if connection.get("auth_method") not in {"external_cli_session", "account_login"}:
        return True
    return connection.get("external_session_status") in {"available", "executor_managed"}


def _count(value: Any) -> int:
    return value if type(value) is int and value >= 0 else 0


def _observed(profile: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(profile, Mapping) or not profile:
        return None
    return {field: profile.get(field) for field in _PROFILE_FIELDS} | {"provenance": "LOCAL_METERING"}


def _read_profiles(profiles: Callable[[], Mapping[str, Mapping[str, Any]]]) -> tuple[dict[str, Any], str]:
    # Observed usage is an addition to the view; losing it must not hide the resources.
    try:
        observed = profiles()
        return (dict(observed), "available") if isinstance(observed, Mapping) else ({}, "unavailable")
    except Exception:  # noqa: BLE001 - any profile failure only drops the usage figures
        return {}, "unavailable"


def _token_usage(entry: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(entry, Mapping):
        return None
    return {key: _count(entry.get(key)) for key in (*_TOKEN_COUNTERS, "tasks", "tasks_with_tokens",
                                                     "cache_write_unknown_tasks")} | {"provenance": "LOCAL_METERING"}


def _price_binding(model_id: str, entry: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Equivalent list-price cost of one binding's tokens, model by model."""
    if not isinstance(entry, Mapping) or not entry.get("tasks_with_tokens"):
        return None
    parts = []
    for model, tokens in (entry.get("models") or {}).items():
        if isinstance(tokens, Mapping) and any(tokens.get(key) for key in _TOKEN_COUNTERS):
            parts.append(equivalent_cost(model or model_id, tokens))
    return _combine_costs(parts, cli_reported=entry.get("cli_reported_cost_usd"))


def _combine_costs(parts: list[Mapping[str, Any]], *, cli_reported: Any = None) -> dict[str, Any] | None:
    if not parts:
        return None
    priced = [part for part in parts if part.get("usd") is not None]
    state = "ESTIMATED" if len(priced) == len(parts) and all(p.get("state") == "ESTIMATED" for p in parts) \
        else "PARTIAL" if priced else "UNKNOWN"
    result = {"state": state, "usd": round(sum(part["usd"] for part in priced), 6) if priced else None,
              "currency": "USD", "provenance": "ESTIMATED_LIST_PRICE",
              "price_source": parts[0].get("price_source"), "price_as_of": parts[0].get("price_as_of"),
              "unpriced": sorted({r for part in parts for r in ([part["reason"]] if part.get("reason") else
                                                                 part.get("unpriced", []))}),
              "notes": sorted({note for part in parts for note in part.get("notes", ())})}
    if type(cli_reported) in (int, float):
        # Claude Code's own API-price figure for the same runs, as a cross-check.
        result["cli_reported_usd"] = round(float(cli_reported), 6)
    return result


def _read_source(source: Callable[[], Any] | None) -> Mapping[str, Any]:
    if source is None:
        return {}
    try:
        value = source()
    except Exception:  # noqa: BLE001 - an extra figure must never hide the resources
        return {}
    return value if isinstance(value, Mapping) else {}


def _read_external(source: Callable[[], Any]) -> Mapping[str, Any]:
    """Like _read_source, but a failure is surfaced as {"status": "unavailable"}.

    External accounts are listed separately and never folded into a Nerelan
    connection's quota, tokens or cost, so nothing is double counted.
    """
    try:
        value = source()
    except Exception:  # noqa: BLE001 - an external source must never hide the resources
        return {"status": "unavailable"}
    return value if isinstance(value, Mapping) else {"status": "unavailable"}


def _quota(connection: Mapping[str, Any], native: tuple[str, str, str] | None,
           quotas: Mapping[str, Any]) -> dict[str, Any]:
    if native is None:
        reason = "api_key_has_no_subscription_window" if connection.get("auth_method") == "api_key" \
            else "no_official_quota_source"
        return dict(UNKNOWN_QUOTA, reason=reason)
    snapshot = quotas.get(connection.get("executor_provider_id"))
    return dict(snapshot) if isinstance(snapshot, Mapping) and snapshot.get("state") else dict(UNKNOWN_QUOTA)


def _guard_entries(source: Callable[[], Any] | None) -> list[dict[str, Any]]:
    try:
        entries = source() if source else []
    except Exception:  # noqa: BLE001 - the log is an extra
        return []
    keys = ("at", "role", "binding_id", "decision", "reason", "window", "switched_to")
    return [{key: entry.get(key) for key in keys} for entry in (entries or [])[:20] if isinstance(entry, Mapping)]


def build_resource_view(store: Any, profiles: Callable[[], Mapping[str, Mapping[str, Any]]],
                        tokens: Callable[[], Mapping[str, Any]] | None = None,
                        quotas: Callable[[], Mapping[str, Any]] | None = None,
                        guard_log: Callable[[], Any] | None = None,
                        external: Callable[[], Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Connections -> credential, executors, bindings, tokens, equivalent cost and quota, sanitized.

    When *external* is given, its snapshot appears under
    ``external_sources.magpie``; it is never merged into a connection's quota,
    tokens or cost.  When *external* is None (Magpie disabled) the response has
    no ``external_sources`` key.
    """
    executors = {item["executor_id"]: item for item in store.list_executors_public()}
    bindings = store.list_bindings_public()
    observed, observation_status = _read_profiles(profiles)
    token_totals, quota_snapshots = _read_source(tokens), _read_source(quotas)
    resources = []
    for connection in store.list_connections_public():
        connection_id = connection["connection_id"]
        try:
            compatible = store.compatible_executors(connection_id)
        except ValueError:
            compatible = []
        connection_ok = connection.get("enabled") is True and _session_usable(connection)
        ready = {executor_id: connection_ok and _executor_ready(executors.get(executor_id), connection)
                 for executor_id in compatible}
        rows, totals = [], dict.fromkeys(_TOTAL_FIELDS, 0)
        token_sum = dict.fromkeys((*_TOKEN_COUNTERS, "tasks_with_tokens"), 0)
        costs = []
        for binding in (b for b in bindings if b["connection_id"] == connection_id):
            usage = _observed(observed.get(binding["binding_id"]))
            for field in _TOTAL_FIELDS if usage else ():
                totals[field] += _count(usage.get(field))
            token_entry = token_totals.get(binding["binding_id"])
            binding_tokens = _token_usage(token_entry)
            cost = _price_binding(binding["model_id"], token_entry)
            for key in token_sum if binding_tokens else ():
                token_sum[key] += binding_tokens[key]
            if cost:
                costs.append(cost)
            rows.append({"binding_id": binding["binding_id"], "model_id": binding["model_id"],
                         "executor_id": binding["executor_id"], "enabled": binding["enabled"],
                         "usable": bool(binding["enabled"] and ready.get(binding["executor_id"])),
                         "observed": usage, "tokens": binding_tokens, "equivalent_cost": cost})
        native = NATIVE_CLI_PROVIDERS.get(connection.get("executor_provider_id"))
        credential = _credential(connection)
        resources.append({
            "connection_id": connection_id,
            "name": connection["name"],
            "enabled": connection["enabled"],
            "upstream_provider_id": connection.get("upstream_provider_id"),
            "protocol_family": connection.get("protocol_family"),
            "credential": credential,
            # A subscription stays owned by the CLI that signed in; Nerelan owns only API keys.
            "credential_owner": (native[1] if native else "external_cli") if credential["kind"] == "subscription"
            else "nerelan" if credential["kind"] == "api_key" else "none",
            "executors": [{"executor_id": executor_id, "ready": ready[executor_id],
                           "readiness_status": (executors.get(executor_id) or {}).get("readiness_status") or None}
                          for executor_id in compatible],
            "bindings": rows,
            "observed_usage": totals | {"provenance": "LOCAL_METERING", "window_tasks": OBSERVATION_WINDOW_TASKS,
                                        "status": observation_status},
            "token_usage": token_sum | {"provenance": "LOCAL_METERING"},
            "equivalent_cost": _combine_costs(costs),
            "quota": _quota(connection, native, quota_snapshots),
        })
    view = {"resources": resources,
            "summary": {"connections": len(resources),
                        "usable_bindings": sum(row["usable"] for item in resources for row in item["bindings"]),
                        "quota_known": sum(item["quota"].get("state") == "OBSERVED" for item in resources),
                        "tokens": {key: sum(item["token_usage"][key] for item in resources) for key in _TOKEN_COUNTERS},
                        "equivalent_cost": _combine_costs([item["equivalent_cost"] for item in resources
                                                           if item["equivalent_cost"]]),
                        "quota_guard": _guard_entries(guard_log)}}
    if external is not None:
        view["external_sources"] = {"magpie": _read_external(external)}
    return view
