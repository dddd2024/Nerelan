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
from .component_lock import load_component_lock
from .secrets import executor_key_secret_preflight, provider_secret_preflight

_REQUIRED_SECRET_NAMES = (
    "POSTGRES_PASSWORD",
    "LITELLM_DATABASE_PASSWORD",
    "LITELLM_MASTER_KEY",
    "LITELLM_SALT_KEY",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def doctor_report() -> dict[str, Any]:
    root = _repo_root()
    lock_path = root / "deploy" / "unattended" / "component-lock.yaml"
    compose_path = root / "deploy" / "unattended" / "compose.yaml"
    lock = load_component_lock(lock_path)
    lock_text = lock_path.read_text(encoding="utf-8")
    compose_text = compose_path.read_text(encoding="utf-8")
    version = importlib.metadata.version("temporalio")
    checks = {
        "python_at_least_3_13": tuple(__import__("sys").version_info[:2]) >= (3, 13),
        "temporalio_exact_1_30_0": version == "1.30.0",
        "component_projection_valid": bool(lock["projection_sha256"]),
        "floating_latest_absent": "latest" not in lock_text.lower()
        and "latest" not in compose_text.lower(),
        "github_token_not_in_runtime_compose": "GITHUB_TOKEN" not in compose_text,
        "provider_key_not_in_runtime_environment": "OPENAI_API_KEY:" not in compose_text,
        "provider_secret_file_boundary": (
            "UNATTENDED_OPENAI_API_KEY_FILE" in compose_text
            and "source: openai_api_key" in compose_text
        ),
        "worker_has_no_docker_socket": "reverse-agent-worker" not in compose_text
        or "/var/run/docker.sock" not in _service_block(
            compose_text, "reverse-agent-worker"
        ),
        "long_lived_agent_server_absent": "  agent-server:" not in compose_text,
        "docker_socket_absent_from_compose": "/var/run/docker.sock" not in compose_text,
        "internal_model_executor_network": (
            "  model-executor:" in compose_text
            and "    internal: true" in compose_text
        ),
        "litellm_virtual_key_boundary": (
            "litellm-key-bootstrap:" in compose_text
            and "litellm_executor_key" in compose_text
            and "postgresql://litellm:" in compose_text
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
    secret_preflight = subparsers.add_parser("secret-preflight")
    secret_preflight.add_argument(
        "--secret-file",
        default=os.environ.get("UNATTENDED_OPENAI_API_KEY_FILE"),
    )
    executor_key_preflight = subparsers.add_parser("executor-key-preflight")
    executor_key_preflight.add_argument(
        "--secret-file",
        default=os.environ.get("UNATTENDED_LITELLM_EXECUTOR_KEY_FILE"),
    )
    args = parser.parse_args(argv)
    if args.command == "doctor":
        report = doctor_report()
    elif args.command == "gate2-probe":
        report = asyncio.run(
            _gate2_report(args.temporal_address, args.temporal_namespace)
        )
    elif args.command == "secret-preflight":
        report = provider_secret_preflight(
            args.secret_file,
            repository_root=_repo_root(),
        )
    else:
        report = executor_key_secret_preflight(
            args.secret_file,
            repository_root=_repo_root(),
        )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
