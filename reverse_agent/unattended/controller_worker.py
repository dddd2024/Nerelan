"""Temporal worker that is the sole Docker authority for Attempt Activities."""

from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Sequence
from pathlib import Path

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import (
    ControllerActivityRuntime,
    cleanup_attempt,
    collect_openhands_result,
    configure_controller_activity_runtime,
    launch_or_reconcile_attempt,
    start_openhands_conversation,
    wait_attempt_server,
)
from .identifiers import SANDBOX_CONTROLLER_TASK_QUEUE
from .sandbox import SandboxController, SubprocessDockerRunner

_CONTROLLER_ACTIVITIES = [
    launch_or_reconcile_attempt,
    wait_attempt_server,
    start_openhands_conversation,
    collect_openhands_result,
    cleanup_attempt,
]


def build_controller_worker(client: Client) -> Worker:
    return Worker(
        client,
        task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
        workflows=[],
        activities=_CONTROLLER_ACTIVITIES,
    )


async def run_controller_worker(
    address: str,
    namespace: str,
    *,
    host_workspace_root: Path,
    executor_network: str,
    executor_key_file: Path,
) -> None:
    executor_api_key = executor_key_file.read_text(encoding="utf-8").strip()
    runner = SubprocessDockerRunner()
    controller = SandboxController(
        runner,
        host_workspace_root=host_workspace_root,
        executor_network=executor_network,
    )
    configure_controller_activity_runtime(
        ControllerActivityRuntime(
            controller,
            runner,
            host_workspace_root=host_workspace_root,
            executor_api_key=executor_api_key,
        )
    )
    client = await Client.connect(address, namespace=namespace)
    await build_controller_worker(client).run()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--address", default=os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    )
    parser.add_argument(
        "--namespace", default=os.environ.get("TEMPORAL_NAMESPACE", "default")
    )
    parser.add_argument(
        "--workspace-root",
        default=os.environ.get("UNATTENDED_HOST_WORKSPACE_ROOT"),
        type=Path,
    )
    parser.add_argument(
        "--executor-network",
        default=os.environ.get("UNATTENDED_EXECUTOR_NETWORK"),
    )
    parser.add_argument(
        "--executor-key-file",
        default=os.environ.get("UNATTENDED_LITELLM_EXECUTOR_KEY_FILE"),
        type=Path,
    )
    args = parser.parse_args(argv)
    if (
        args.workspace_root is None
        or args.executor_network is None
        or args.executor_key_file is None
    ):
        parser.error("controller runtime paths and network are required")
    asyncio.run(
        run_controller_worker(
            args.address,
            args.namespace,
            host_workspace_root=args.workspace_root,
            executor_network=args.executor_network,
            executor_key_file=args.executor_key_file,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
