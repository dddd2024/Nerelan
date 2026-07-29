"""Temporal worker entrypoint for the unattended v0 task queue."""

from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Sequence

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import run_synthetic_activity
from .identifiers import TASK_QUEUE
from .workflows import UnattendedGate2Workflow


def build_worker(client: Client) -> Worker:
    return Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[UnattendedGate2Workflow],
        activities=[run_synthetic_activity],
    )


async def run_worker(address: str, namespace: str) -> None:
    client = await Client.connect(address, namespace=namespace)
    await build_worker(client).run()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--address", default=os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    )
    parser.add_argument(
        "--namespace", default=os.environ.get("TEMPORAL_NAMESPACE", "default")
    )
    args = parser.parse_args(argv)
    asyncio.run(run_worker(args.address, args.namespace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
