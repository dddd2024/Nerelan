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

# Observed usage covers this many recent model-backed tasks (the agent-profile window).
OBSERVATION_WINDOW_TASKS = 500

_PROFILE_FIELDS = ("attempts", "ok", "failed", "timeouts", "rate_limited", "success_rate",
                   "median_ok_seconds", "median_ok_tokens", "observed_tokens")
_TOTAL_FIELDS = ("attempts", "ok", "failed", "observed_tokens")

UNKNOWN_QUOTA = {"state": "UNKNOWN", "provenance": "UNAVAILABLE", "reason": "no_official_quota_source"}


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


def build_resource_view(store: Any, profiles: Callable[[], Mapping[str, Mapping[str, Any]]]) -> dict[str, Any]:
    """Connections -> credential, executors, bindings, observed usage and quota, sanitized."""
    executors = {item["executor_id"]: item for item in store.list_executors_public()}
    bindings = store.list_bindings_public()
    observed, observation_status = _read_profiles(profiles)
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
        for binding in (b for b in bindings if b["connection_id"] == connection_id):
            usage = _observed(observed.get(binding["binding_id"]))
            for field in _TOTAL_FIELDS if usage else ():
                totals[field] += _count(usage.get(field))
            rows.append({"binding_id": binding["binding_id"], "model_id": binding["model_id"],
                         "executor_id": binding["executor_id"], "enabled": binding["enabled"],
                         "usable": bool(binding["enabled"] and ready.get(binding["executor_id"])),
                         "observed": usage})
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
            "quota": dict(UNKNOWN_QUOTA),
        })
    return {"resources": resources,
            "summary": {"connections": len(resources),
                        "usable_bindings": sum(row["usable"] for item in resources for row in item["bindings"]),
                        "quota_known": 0}}
