"""Paid subscriptions are never dispatched through a gateway (Owner decision 2026-11-23, #1743).

A paid subscription (Claude, Codex/GPT, Antigravity) runs only in its official agent;
Magpie may read its quota. This module is the single rule. Selection, the binding
resolver, the execution snapshot (leases, probes, reviews) and binding-less dispatch
all ask it, so no pin, group, ``auto/*`` id, retry or newly found binding goes around it.

The providers are a setting: ``paid_subscriptions.providers`` in
``model_routing_overrides.json``. The list replaces the defaults; absent means defaults.
"""
from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path
import re
from socket import inet_aton
from typing import Any, Mapping
from urllib.parse import urlsplit

from ..model_access.contracts import NATIVE_CLI_PROVIDER_FOR_EXECUTOR
from .routing_inputs import DEFAULT_PAID_SUBSCRIPTIONS, read_overrides, routing_group_id

BLOCKED = "paid_subscription_gateway"
#: The stored failure class of a dispatch this rule refused.
BLOCKED_CLASS = f"binding_resolution_failed:{BLOCKED}"

# A resolved model id carries its connection's provider in front of the gateway's own id.
_TRANSPORT_PREFIXES = frozenset({"magpie", "openai-compatible", "litellm-proxy", "reverse-agent-relay"})
# Magpie reads these vendors' accounts as the subscriptions themselves, so on a gateway the
# vendor alone does not say "API key". ``openrouter/openai/...`` names its provider.
_VENDOR_NAMES = frozenset({"openai", "anthropic", "google"})


class PaidSubscriptionGatewayError(ValueError):
    """The trusted host refused to read execution material for a blocked binding."""

    def __init__(self, cause: str):
        super().__init__(f"{BLOCKED}:{cause}")
        self.cause = cause


def _tokens(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]


def _named(text: str, names: Any, *, prefix: bool = False) -> str:
    """The configured name that is a word of ``text`` (``codex-2``, ``gpt5``, ``gpt4o``), or "".

    With ``prefix`` a longer word counts too (``claudecode``).
    """
    for token in _tokens(text):
        for name in names:
            if token.startswith(name) and (prefix or len(token) == len(name) or token[len(name)].isdigit()):
                return name
    return ""


def _providers(owner: Mapping[str, Any]) -> Mapping[str, Any]:
    setting = owner.get("paid_subscriptions")
    chosen = setting.get("providers") if isinstance(setting, Mapping) else None
    return chosen if isinstance(chosen, Mapping) and chosen else DEFAULT_PAID_SUBSCRIPTIONS["providers"]


def _families(owner: Mapping[str, Any]) -> set[str]:
    providers = _providers(owner)
    return {family for families in providers.values() for family in families} | set(providers)


def _segments(model_id: str, executor_provider: str = "") -> list[str]:
    parts = [part for part in model_id.strip().lower().split("/") if part.strip()]
    prefixes = _TRANSPORT_PREFIXES | ({executor_provider.lower()} if executor_provider else set())
    while len(parts) > 1 and parts[0] in prefixes:
        parts = parts[1:]
    return parts


def _paid_namespace(parts: list[str], owner: Mapping[str, Any]) -> str:
    return next((name for part in parts[:-1] if (name := _named(part, _providers(owner), prefix=True))), "")


def is_native_route(executor_id: Any, connection: Mapping[str, Any]) -> bool:
    """The official Codex / Claude Code CLI on its own login; never a gateway request."""
    native = NATIVE_CLI_PROVIDER_FOR_EXECUTOR.get(executor_id)
    return (native is not None and connection.get("auth_method") == "external_cli_session"
            and (connection.get("executor_provider_id") or connection.get("provider")) == native)


def _local_address(url: Any) -> bool:
    try:
        host = (urlsplit(url).hostname or "").lower().rstrip(".")
    except (TypeError, ValueError, AttributeError):
        return True
    try:
        # inet_aton also reads the short and hexadecimal spellings a client accepts (127.1).
        return not ip_address(host if ":" in host else inet_aton(host)).is_global
    except (OSError, UnicodeError, ValueError):
        return "." not in host or host.endswith((".local", ".lan", ".internal", ".localhost"))


def _local_gateway(connection: Mapping[str, Any]) -> bool:
    """Whether the endpoint can be a gateway holding the Owner's accounts.

    Keyless, or on this machine/network whatever it signs in with; an unreadable address
    counts as one. A public
    endpoint with a key or an executor's own login is that vendor's, not a gateway.
    """
    if connection.get("auth_method") not in {"api_key", "external_cli_session", "account_login"}:
        return True
    # Claude Code uses a connection's Anthropic endpoint, the other executors its base URL.
    urls = [url for url in (connection.get("base_url"), connection.get("anthropic_base_url")) if url]
    return not urls or any(_local_address(url) for url in urls)


def _group_cause(group: str, owner: Mapping[str, Any]) -> str:
    groups = owner.get("groups")
    entry = next((value for key, value in groups.items()
                  if isinstance(key, str) and key.strip().lower() == group), None) if isinstance(groups, Mapping) else None
    entry = entry if isinstance(entry, Mapping) else {}
    raw = entry.get("members")
    members = [m for m in raw if isinstance(m, str)] if isinstance(raw, (list, tuple)) else []
    for member in members:
        paid = _paid_namespace(_segments(member), owner)
        if paid:
            return f"group_member:{paid}"
    head, _, name = group.partition("/")
    identity = entry.get("identity") if isinstance(entry.get("identity"), str) else ""
    capable = bool(_named(" ".join((name, identity, *members)), _families(owner)))
    if head == "auto":
        # The gateway fills an auto group by itself, so a declaration proves nothing about it.
        return "auto_membership_unknown" if capable or name in {"auto", "default"} or routing_group_id(name) else ""
    errors = {str(error).lower() for error in owner.get("group_errors", ())}
    if not entry or f"invalid_model_routing_group_members:{group}" in errors or capable and not members:
        return "group_membership_unknown"
    return ""


def block_cause(model_id: Any, connection: Mapping[str, Any], executor_id: Any,
                owner: Mapping[str, Any] | None) -> str:
    """Why this route must not be dispatched, or "". ``owner`` None means unreadable settings."""
    if is_native_route(executor_id, connection):
        return ""
    unreadable, owner = owner is None, owner or {}
    local = _local_gateway(connection)
    if not isinstance(model_id, str) or not model_id.strip():
        return "model_unknown" if local else ""
    own_provider = str(connection.get("executor_provider_id") or connection.get("provider") or "")
    named = _named(own_provider, _providers(owner), prefix=True)
    if named and local:
        return f"provider:{named}"  # the connection itself is named after a paid account
    parts = _segments(model_id, own_provider)
    paid = _paid_namespace(parts, owner)
    if paid:
        return f"provider:{paid}"
    group = routing_group_id("/".join(parts))
    if unreadable and (local or group):
        return "settings_unreadable"
    if group:
        return _group_cause(group, owner)
    if local and (len(parts) == 1 or len(parts) == 2 and parts[0] in _VENDOR_NAMES):
        # Without a provider of its own the gateway picks the account from the model name.
        name = parts[-1]
        if name in {"auto", "default"}:
            return "model_unknown"
        # The open-weight model as Ollama (gpt-oss:20b) and LM Studio (openai/gpt-oss-20b) name it.
        if not name.startswith("gpt-oss:" if len(parts) == 1 else "gpt-oss"):
            family = _named(name, _families(owner))
            if family:
                return f"model_family:{family}"
    return ""


def owner_settings(state_path: Any) -> Mapping[str, Any] | None:
    """The routing overrides beside the setup state; None when they cannot be read."""
    if state_path is None:
        return {}
    try:
        return read_overrides(Path(state_path))
    except ValueError:
        return None


def unbound_model_cause(model_id: str) -> str:
    """The rule for a task with no binding: its endpoint is unknown, so a gateway is assumed."""
    return block_cause(model_id, {}, "opencode", {}) if (model_id or "").strip() else ""
