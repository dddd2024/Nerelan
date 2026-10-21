"""Read-only check for the one-time move of legacy API-key connections into Magpie (#1170).

The Owner adds each provider (and its key) in Magpie's own Providers UI. This module only
compares the saved Nerelan connections and bindings with the models Magpie lists, and
proposes the Magpie model id each legacy binding would use. It reads no credentials,
writes no configuration and sends no inference request, so it can never mark a provider
TESTED: that needs a bounded live request the Owner authorizes separately.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from .magpie import fetch_magpie_snapshot

# Upstream base hosts of the legacy connections and the Magpie provider id their models
# appear under. OpenRouter, Groq and Mistral are Magpie presets; SenseNova and Agnes are
# custom vendors whose id follows the name the Owner gives them in Magpie.
DEFAULT_PROVIDER_BY_HOST = {
    "openrouter.ai": "openrouter",
    "api.groq.com": "groq",
    "api.mistral.ai": "mistral",
    "token.sensenova.cn": "sensenova",
    "apihub.agnes-ai.com": "agnes",
}

# Connection-level prefixes legacy bindings carry for LiteLLM routing; Magpie spells the
# same model as ``provider/model`` without them.
_LEGACY_MODEL_PREFIXES = ("litellm-proxy/",)


def magpie_model_id(provider: str, legacy_model_id: str) -> str:
    model = legacy_model_id
    for prefix in _LEGACY_MODEL_PREFIXES:
        if model.startswith(prefix):
            model = model[len(prefix):]
    return f"{provider}/{model}"


def _magpie_connection_ids(connections: Iterable[Mapping[str, Any]], magpie_base_url: str) -> set[str]:
    origin = urlsplit(magpie_base_url)
    result = set()
    for connection in connections:
        url = urlsplit(str(connection.get("base_url") or ""))
        if url.hostname in ("127.0.0.1", "::1", "localhost") and url.port == origin.port:
            result.add(str(connection.get("connection_id")))
    return result


def build_report(state: Mapping[str, Any], snapshot: Mapping[str, Any], *,
                 magpie_base_url: str = "http://127.0.0.1:3425",
                 provider_overrides: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Classify every saved connection; only ``api_key`` connections are migration candidates."""
    connections = [c for c in state.get("connections", []) if isinstance(c, dict)]
    bindings = [b for b in state.get("bindings", []) if isinstance(b, dict)]
    overrides = dict(provider_overrides or {})
    available = snapshot.get("status") == "available"
    listed = {m["model_id"] for m in snapshot.get("models", []) if isinstance(m, dict) and m.get("model_id")}
    listed_providers = {model.split("/", 1)[0] for model in listed if "/" in model}
    magpie_ids = _magpie_connection_ids(connections, magpie_base_url)
    magpie_bindings = {(b.get("executor_id"), b.get("model_id")): b.get("binding_id")
                       for b in bindings if b.get("connection_id") in magpie_ids}

    rows = []
    for connection in connections:
        connection_id = str(connection.get("connection_id"))
        row: dict[str, Any] = {"connection_id": connection_id, "enabled": connection.get("enabled") is True}
        rows.append(row)
        if connection_id in magpie_ids:
            row.update(action="MAGPIE_GATEWAY")
            continue
        if connection.get("auth_method") != "api_key":
            # Official CLI sessions keep their native login; they are not keys to move.
            row.update(action="KEEP_NATIVE")
            continue
        host = urlsplit(str(connection.get("base_url") or "")).hostname or ""
        provider = overrides.get(connection_id) or DEFAULT_PROVIDER_BY_HOST.get(host)
        row.update(action="MIGRATE", upstream_host=host, magpie_provider=provider)
        if not available:
            row["status"] = "UNKNOWN"
            row["reason"] = f"magpie_{snapshot.get('status') or 'unavailable'}"
        elif provider is None:
            row["status"] = "UNKNOWN"
            row["reason"] = "no_magpie_provider_mapping"
        else:
            row["status"] = "IMPORTED" if provider in listed_providers else "NOT_IMPORTED"
        row["bindings"] = []
        for binding in bindings:
            if binding.get("connection_id") != connection_id:
                continue
            target = magpie_model_id(provider, str(binding.get("model_id"))) if provider else None
            row["bindings"].append({
                "binding_id": binding.get("binding_id"),
                "enabled": binding.get("enabled") is True,
                "executor_id": binding.get("executor_id"),
                "legacy_model_id": binding.get("model_id"),
                "magpie_model_id": target,
                "model_listed": bool(available and target in listed),
                "magpie_binding_id": magpie_bindings.get((binding.get("executor_id"), target)),
            })

    candidates = [row for row in rows if row["action"] == "MIGRATE"]
    return {
        "magpie": {"status": snapshot.get("status"), "version": snapshot.get("version"),
                   "model_count": len(listed), "reason": snapshot.get("reason")},
        "connections": rows,
        "summary": {
            "candidates": len(candidates),
            "imported": sum(1 for row in candidates if row.get("status") == "IMPORTED"),
            # A listed provider is not a tested one: TESTED needs an authorized live request.
            "tested": 0,
            "complete": False,
        },
    }


def _parse_overrides(values: Iterable[str]) -> dict[str, str]:
    result = {}
    for value in values:
        connection_id, sep, provider = value.partition("=")
        if not sep or not connection_id or not provider:
            raise argparse.ArgumentTypeError(f"expected connection_id=magpie_provider, got {value!r}")
        result[connection_id] = provider
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m reverse_agent.model_access.magpie_migration",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--state", required=True, type=Path, help="model_setup_state.json to read")
    parser.add_argument("--magpie-url", default=None,
                        help="Magpie origin; defaults to the state file's magpie.base_url or http://127.0.0.1:3425")
    parser.add_argument("--provider", action="append", default=[], metavar="CONNECTION=PROVIDER",
                        help="Magpie provider id for a connection whose host has no default mapping")
    args = parser.parse_args(argv)
    try:
        overrides = _parse_overrides(args.provider)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    state = json.loads(args.state.read_text(encoding="utf-8"))
    base_url = args.magpie_url or (state.get("magpie") or {}).get("base_url") or "http://127.0.0.1:3425"
    report = build_report(state, fetch_magpie_snapshot(base_url), magpie_base_url=base_url,
                          provider_overrides=overrides)
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
