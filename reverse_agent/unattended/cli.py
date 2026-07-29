"""Command-line diagnostics for the unattended Gate 2 baseline."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .probe import run_temporal_probe

_PROJECTION_SHA256 = "e7c334033f8999d7b53fdd7b4b34e4469c3f87a871d4524e4270c707b7f2f83d"
_REQUIRED_SECRET_NAMES = (
    "POSTGRES_PASSWORD",
    "OH_SESSION_API_KEYS_0",
    "OH_SECRET_KEY",
    "LITELLM_MASTER_KEY",
    "LITELLM_SALT_KEY",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def doctor_report() -> dict[str, Any]:
    root = _repo_root()
    lock_path = root / "deploy" / "unattended" / "component-lock.yaml"
    compose_path = root / "deploy" / "unattended" / "compose.yaml"
    lock_text = lock_path.read_text(encoding="utf-8")
    compose_text = compose_path.read_text(encoding="utf-8")
    version = importlib.metadata.version("temporalio")
    checks = {
        "python_at_least_3_13": tuple(__import__("sys").version_info[:2]) >= (3, 13),
        "temporalio_exact_1_30_0": version == "1.30.0",
        "component_projection_present": _PROJECTION_SHA256 in lock_text,
        "floating_latest_absent": "latest" not in lock_text.lower()
        and "latest" not in compose_text.lower(),
        "github_token_not_in_runtime_compose": "GITHUB_TOKEN" not in compose_text,
        "worker_has_no_docker_socket": "reverse-agent-worker" not in compose_text
        or "/var/run/docker.sock" not in _service_block(
            compose_text, "reverse-agent-worker"
        ),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "temporalio_version": version,
        "component_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "configured_secret_names": {
            name: bool(os.environ.get(name)) for name in _REQUIRED_SECRET_NAMES
        },
    }


def _service_block(compose_text: str, service: str) -> str:
    marker = f"\n  {service}:\n"
    if marker not in compose_text:
        return ""
    block = compose_text.split(marker, 1)[1]
    next_service = block.find("\n  ")
    return block if next_service < 0 else block[:next_service]


async def _gate2_report(address: str, namespace: str) -> dict[str, Any]:
    report = doctor_report()
    if report["status"] != "PASS":
        return report
    report["temporal"] = await run_temporal_probe(
        address=address,
        namespace=namespace,
    )
    report["status"] = (
        "PASS"
        if all(value == "PASS" for key, value in report["temporal"].items() if key != "result")
        else "FAIL"
    )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor")
    probe = subparsers.add_parser("gate2-probe")
    probe.add_argument(
        "--temporal-address",
        default=os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
    )
    probe.add_argument(
        "--temporal-namespace",
        default=os.environ.get("TEMPORAL_NAMESPACE", "default"),
    )
    args = parser.parse_args(argv)
    if args.command == "doctor":
        report = doctor_report()
    else:
        report = asyncio.run(
            _gate2_report(args.temporal_address, args.temporal_namespace)
        )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
