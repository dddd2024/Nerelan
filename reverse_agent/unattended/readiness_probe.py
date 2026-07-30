"""One-shot direct diagnostic for the fixed Attempt readiness policy."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from .attempt_transport import AttemptJsonTransport, AttemptTransportError
from .contracts import ExecutionHandle
from .identifiers import executor_id, workspace_id
from .readiness import (
    READINESS_DEADLINE_SECONDS,
    READINESS_MAX_POLL_INTERVAL_SECONDS,
    AttemptReadinessTerminal,
    AttemptReadinessTimeout,
    wait_for_attempt_readiness,
)
from .sandbox import (
    FIXED_LAUNCH_SPEC,
    SandboxController,
    SandboxControllerError,
    SubprocessDockerRunner,
)
from .temporal_contracts import AttemptReadinessProgress

_PROJECT_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,62}\Z")
_WORKFLOW_ID = "unattended:dddd2024/reverse-agent:issue:84:readiness-diagnostic"


def run_direct_readiness_probe(
    *,
    repository_root: Path,
    compose_project: str,
) -> dict[str, Any]:
    """Launch once, apply the production readiness policy, and clean exactly."""

    if _PROJECT_NAME.fullmatch(compose_project) is None:
        return _failure("compose_project_invalid")
    root = (repository_root / ".var" / "unattended").resolve()
    handle = ExecutionHandle(
        workflow_id=_WORKFLOW_ID,
        attempt=1,
        workspace_id=workspace_id(_WORKFLOW_ID),
        executor_id=executor_id(_WORKFLOW_ID, 1),
        started_at="2026-07-30T04:00:00+00:00",
    )
    runner = SubprocessDockerRunner()
    controller = SandboxController(
        runner,
        host_workspace_root=root,
        executor_network=f"{compose_project}_model-executor",
    )
    transport = AttemptJsonTransport(runner, handle)
    progress: list[AttemptReadinessProgress] = []
    metadata = None
    result = None
    failure_category = None
    cleanup_passed = False

    async def inspect_container():
        try:
            return await asyncio.to_thread(controller.inspect, handle)
        except SandboxControllerError:
            raise AttemptReadinessTerminal("container_contract_drift") from None

    async def probe_loopback():
        return await asyncio.to_thread(transport.probe_readiness)

    async def execute():
        return await wait_for_attempt_readiness(
            inspect_container=inspect_container,
            probe_loopback=probe_loopback,
            heartbeat=progress.append,
            cancelled=lambda: False,
        )

    try:
        metadata = controller.launch_or_reconcile(handle, FIXED_LAUNCH_SPEC)
        result = asyncio.run(execute())
    except AttemptReadinessTimeout:
        failure_category = "ATTEMPT_READINESS_TIMEOUT"
    except AttemptReadinessTerminal as error:
        failure_category = error.state
    except SandboxControllerError:
        failure_category = "container_contract_drift"
    except AttemptTransportError:
        failure_category = "transport_protocol_violation"
    except OSError:
        failure_category = "unexpected_terminal_failure"
    finally:
        try:
            cleanup_passed = all(controller.cleanup_attempt(handle))
        except SandboxControllerError:
            cleanup_passed = False

    passed = (
        result is not None
        and result.alive
        and result.health
        and cleanup_passed
        and failure_category is None
    )
    report: dict[str, Any] = {
        "status": "PASS" if passed else "FAIL",
        "readiness": "PASS" if result is not None else "FAIL",
        "states": tuple(item.state for item in progress)
        + (("alive",) if result is not None else ()),
        "poll_count": result.poll_count if result is not None else len(progress),
        "deadline_seconds": int(READINESS_DEADLINE_SECONDS),
        "max_poll_interval_milliseconds": int(
            READINESS_MAX_POLL_INTERVAL_SECONDS * 1000
        ),
        "cleanup": "PASS" if cleanup_passed else "FAIL",
        "failure_category": failure_category,
    }
    if metadata is not None:
        report["image_digest"] = metadata.image_digest
        report["mount_destination"] = metadata.workspace_destination
        report["network_name"] = metadata.network_name
    return report


def _failure(category: str) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "readiness": "FAIL",
        "states": (),
        "poll_count": 0,
        "deadline_seconds": int(READINESS_DEADLINE_SECONDS),
        "max_poll_interval_milliseconds": int(
            READINESS_MAX_POLL_INTERVAL_SECONDS * 1000
        ),
        "cleanup": "PASS",
        "failure_category": category,
    }
