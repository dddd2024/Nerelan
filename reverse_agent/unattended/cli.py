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
from .readiness_probe import run_direct_readiness_probe
from .sandbox_probe import run_sandbox_boundary_probe
from .workspace_probe import run_workspace_preflight_probe
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
        "controller_worker_is_sole_docker_authority": (
            "/var/run/docker.sock"
            in _service_block(compose_text, "sandbox-controller-worker")
            and "/var/run/docker.sock"
            not in _service_block(compose_text, "reverse-agent-worker")
        ),
        "long_lived_agent_server_absent": "  agent-server:" not in compose_text,
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
    selected: list[str] = []
    for line in compose_text.split(marker, 1)[1].splitlines():
        if line.startswith("  ") and not line.startswith("    "):
            break
        selected.append(line)
    return "\n".join(selected)


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
    runtime_proof = subparsers.add_parser("gate2-runtime-proof")
    runtime_proof.add_argument(
        "--temporal-address",
        default=os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
    )
    runtime_proof.add_argument(
        "--temporal-namespace",
        default=os.environ.get("TEMPORAL_NAMESPACE", "default"),
    )
    runtime_proof.add_argument(
        "--workflow-id",
        default=os.environ.get(
            "UNATTENDED_RUNTIME_PROOF_WORKFLOW_ID",
            "unattended:dddd2024/reverse-agent:issue:82:runtime-proof",
        ),
    )
    runtime_proof.add_argument(
        "--executor-key-file",
        default=os.environ.get("UNATTENDED_LITELLM_EXECUTOR_KEY_FILE"),
        type=Path,
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
    sandbox_probe = subparsers.add_parser("sandbox-boundary-probe")
    sandbox_probe.add_argument(
        "--compose-project",
        default=os.environ.get(
            "UNATTENDED_COMPOSE_PROJECT",
            "reverse-agent-issue81-sandbox",
        ),
    )
    readiness_probe = subparsers.add_parser("attempt-readiness-probe")
    readiness_probe.add_argument(
        "--compose-project",
        required=True,
    )
    workspace_probe = subparsers.add_parser("workspace-preflight")
    workspace_probe.add_argument("--compose-project", required=True)
    workspace_probe.add_argument(
        "--stack-mode",
        required=True,
        choices=("fresh", "restart"),
    )
    sandbox_probe.add_argument(
        "--executor-key-file",
        default=os.environ.get("UNATTENDED_LITELLM_EXECUTOR_KEY_FILE"),
    )
    args = parser.parse_args(argv)
    if args.command == "doctor":
        report = doctor_report()
    elif args.command in {"gate2-probe", "gate2-runtime-proof"}:
        report = asyncio.run(
            _gate2_report(
                args.temporal_address,
                args.temporal_namespace,
            )
            if args.command == "gate2-probe"
            else _runtime_proof_report(args)
        )
    elif args.command == "secret-preflight":
        report = provider_secret_preflight(
            args.secret_file,
            repository_root=_repo_root(),
        )
    elif args.command == "executor-key-preflight":
        report = executor_key_secret_preflight(
            args.secret_file,
            repository_root=_repo_root(),
        )
    elif args.command == "sandbox-boundary-probe":
        key_file = (
            Path(args.executor_key_file)
            if args.executor_key_file
            else Path("")
        )
        report = run_sandbox_boundary_probe(
            repository_root=_repo_root(),
            compose_project=args.compose_project,
            executor_key_file=key_file,
        )
    elif args.command == "attempt-readiness-probe":
        report = run_direct_readiness_probe(
            repository_root=_repo_root(),
            compose_project=args.compose_project,
        )
    else:
        report = run_workspace_preflight_probe(
            repository_root=_repo_root(),
            compose_project=args.compose_project,
            stack_mode=args.stack_mode,
        )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


async def _runtime_proof_report(args: argparse.Namespace) -> dict[str, Any]:
    if args.executor_key_file is None:
        raise ValueError("executor_key_file_required")
    executor_key = args.executor_key_file.read_text(encoding="utf-8").strip()
    if not executor_key or "\x00" in executor_key:
        raise ValueError("executor_key_invalid")
    report = await run_temporal_probe(
        address=args.temporal_address,
        namespace=args.temporal_namespace,
        probe_workflow_id=args.workflow_id,
        sensitive_values=(executor_key,),
    )
    checks = (
        report["temporal_connection"],
        report["activity_execution"],
        report["workflow_history_secret_scan"],
        report["workflow_replay"],
        report["cleanup"],
    )
    report["status"] = "PASS" if all(value == "PASS" for value in checks) else "FAIL"
    return report


if __name__ == "__main__":
    raise SystemExit(main())
