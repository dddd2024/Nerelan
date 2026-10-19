"""Read-only check-in opportunity detection from sanitized resource inventory.

Process existence and connection metadata are *candidate signals*, not proof
of an authenticated account, a claimable reward or automation permission.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

_TRae_URL = "https://forum.trae.cn/t/topic/182999"
_WORKBUDDY_URL = "https://intl.cloud.tencent.com/zh/document/product/1316/84378"

_PROVIDER_HINTS = {
    "trae": ("TRAE Work", "DAILY_CHECK_IN", "VERIFY_FIRST_PARTY_UI", _TRae_URL),
    "traework": ("TRAE Work", "DAILY_CHECK_IN", "VERIFY_FIRST_PARTY_UI", _TRae_URL),
    "trae-work": ("TRAE Work", "DAILY_CHECK_IN", "VERIFY_FIRST_PARTY_UI", _TRae_URL),
    # International Buddy AI daily-active rewards are NOT the same program
    # as WorkBuddy mainland. The latter stays unknown without verified rules.
    "workbuddy-ai": ("WorkBuddy International", "ACTIVITY_REWARD_AUTO", "NO_CHECK_IN", _WORKBUDDY_URL),
    "workbuddy": ("WorkBuddy", "UNKNOWN", "VERIFY_FIRST_PARTY_UI", None),
    "codebuddy": ("CodeBuddy", "UNKNOWN", "VERIFY_FIRST_PARTY_UI", None),
    "codex": ("Codex", "PASSIVE_QUOTA_RESET", "NO_CHECK_IN", None),
    "claude": ("Claude", "PASSIVE_QUOTA_RESET", "NO_CHECK_IN", None),
}
_APP_HINTS = {
    "trae solo cn": "traework",  # Historic process name: app renamed 2026-06-09.
    "traework": "traework",
    "workbuddy": "workbuddy",
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_ref(source: str, name: str) -> str:
    # Don't expose arbitrary raw Connection IDs, names or Magpie identities.
    return hashlib.sha256((source + "\0" + name).encode()).hexdigest()[:24]


def discover_reward_opportunities(
    resource_view: Mapping[str, Any] | None,
    *,
    process_names: Sequence[str] = (),
) -> dict[str, Any]:
    """Describe *possible* reward actions, with no login or provider calls.

    A process is only an installed/running application hint. An external
    resource account is a model-resource record, not a verified check-in
    identity. Neither can be used to authorize an automatic claim.
    """
    snapshot = _as_mapping(resource_view)
    sources: list[tuple[str, str, str]] = []
    for resource in snapshot.get("resources", []) if isinstance(snapshot.get("resources"), list) else []:
        row = _as_mapping(resource)
        name = row.get("upstream_provider_id")
        protocol = row.get("protocol_family")
        if isinstance(name, str) and name.strip():
            connection_id = row.get("connection_id")
            provider = name.lower().strip()
            # A bare openai/anthropic provider is not necessarily a native
            # subscription. Only explicitly identified CLI sessions qualify.
            if provider == "openai" and protocol == "codex-cli":
                provider = "codex"
            elif provider == "anthropic" and protocol == "claude-code-cli":
                provider = "claude"
            if isinstance(connection_id, str) and connection_id:
                sources.append(("model_connection", provider, connection_id))
    magpie = _as_mapping(_as_mapping(snapshot.get("external_sources")).get("magpie"))
    if magpie.get("status") == "available":
        for entry in magpie.get("accounts", []) if isinstance(magpie.get("accounts"), list) else []:
            account = _as_mapping(entry)
            provider, opaque = account.get("provider"), account.get("account_ref")
            if isinstance(provider, str) and isinstance(opaque, str) and provider and opaque:
                sources.append(("magpie_account", provider.lower().strip(), opaque))
    for name in process_names[:128]:
        if not isinstance(name, str):
            continue
        key = _APP_HINTS.get(name.lower().strip())
        if key:
            sources.append(("running_app", key, name.lower().strip()))
    rows, seen = [], set()
    for provenance, provider, identity in sources:
        identity_key = (provenance, provider, identity)
        if identity_key in seen:
            continue
        seen.add(identity_key)
        entry = _PROVIDER_HINTS.get(provider)
        if entry is None:
            continue  # No canonical match: cannot infer a reward from a name.
        display_name, kind, action, url = entry
        rows.append({
            "service": display_name,
            "kind": kind,
            "action": action,
            "source": provenance,
            "source_ref": _safe_ref(provenance, identity),
            "evidence_url": url,
            "account_verified": False,
            "can_auto_claim": False,
            "claim_performed": False,
            "reward_received": None,
            "status": "ACCOUNT_UNVERIFIED",
        })
    return {
        "status": "CANDIDATES_FOUND" if rows else "NOT_CONFIGURED_OR_UNVERIFIED",
        "magpie_status": magpie.get("status") if isinstance(magpie.get("status"), str) else "UNKNOWN",
        "candidates": rows,
        "actual_claims": 0,
    }


def running_reward_app_names() -> list[str]:
    """Return allowlisted Windows application names, never process arguments.

    This optional hint cannot prove a logged-in account. The output remains
    UNKNOWN until the first-party account/session and reward state are checked.
    """
    import csv
    import io
    import os
    import subprocess

    if os.name != "nt":
        return []
    try:
        run = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"], capture_output=True,
            text=True, timeout=3, check=False,
        )
        if run.returncode != 0 or len(run.stdout) > 2_000_000:
            return []
        observed: list[str] = []
        for row in csv.reader(io.StringIO(run.stdout)):
            if not row:
                continue
            value = row[0].removesuffix(".exe").strip().lower()
            if value in _APP_HINTS and value not in observed:
                observed.append(value)
        return observed
    except (OSError, subprocess.TimeoutExpired, csv.Error):
        return []
