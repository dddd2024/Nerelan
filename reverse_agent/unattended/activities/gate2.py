"""Fixed controller Activities for the Gate 2 Attempt lifecycle."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path

from temporalio import activity

from ..attempt_transport import AttemptJsonTransport
from ..contracts import ExecutionHandle, TaskSubmission
from ..identifiers import workspace_path
from ..openhands import OpenHandsAdapter
from ..sandbox import FIXED_LAUNCH_SPEC, SandboxController, SubprocessDockerRunner

_PROVIDER_FREE_INSTRUCTION = (
    "Create provider-free-runtime-proof.txt with the exact text "
    "PROVIDER_FREE_RUNTIME_PROOF, read it back using a tool, then submit "
    "a concise completion result."
)
_runtime: ControllerActivityRuntime | None = None


class ControllerActivityRuntime:
    """Controller-only dependencies that never enter Workflow history."""

    def __init__(
        self,
        controller: SandboxController,
        runner: SubprocessDockerRunner,
        *,
        host_workspace_root: Path,
        executor_api_key: str,
    ) -> None:
        if not host_workspace_root.is_absolute():
            raise ValueError("host_workspace_root_must_be_absolute")
        if (
            not isinstance(executor_api_key, str)
            or not executor_api_key
            or "\x00" in executor_api_key
        ):
            raise ValueError("executor_api_key_invalid")
        self.controller = controller
        self.runner = runner
        self.host_workspace_root = host_workspace_root
        self.executor_api_key = executor_api_key

    def adapter(self, handle: ExecutionHandle) -> OpenHandsAdapter:
        return OpenHandsAdapter(
            AttemptJsonTransport(
                self.runner,
                handle,
                sensitive_values=(self.executor_api_key,),
            ),
            host_workspace_root=self.host_workspace_root,
            executor_api_key=self.executor_api_key,
        )


def configure_controller_activity_runtime(
    runtime: ControllerActivityRuntime,
) -> None:
    global _runtime
    _runtime = runtime


def _configured_runtime() -> ControllerActivityRuntime:
    if _runtime is None:
        raise RuntimeError("controller_activity_runtime_not_configured")
    return _runtime


@activity.defn(name="launch_or_reconcile_attempt")
async def launch_or_reconcile_attempt(
    handle: ExecutionHandle,
) -> dict[str, object]:
    runtime = _configured_runtime()
    metadata = await asyncio.to_thread(
        runtime.controller.launch_or_reconcile,
        handle,
        FIXED_LAUNCH_SPEC,
    )
    return asdict(metadata)


@activity.defn(name="wait_attempt_server")
async def wait_attempt_server(handle: ExecutionHandle) -> dict[str, bool]:
    adapter = _configured_runtime().adapter(handle)
    for _ in range(60):
        checks = await asyncio.to_thread(adapter.health)
        if checks == {"/alive": "PASS", "/health": "PASS"}:
            return {"alive": True, "health": True}
        activity.heartbeat({"server_ready": False})
        await asyncio.sleep(1)
    raise RuntimeError("attempt_server_readiness_timeout")


@activity.defn(name="start_openhands_conversation")
async def start_openhands_conversation(
    handle: ExecutionHandle,
) -> ExecutionHandle:
    relative_workspace = str(
        Path(workspace_path(handle.workflow_id, handle.attempt)).relative_to(
            ".var/unattended"
        )
    ).replace("\\", "/")
    return await asyncio.to_thread(
        _configured_runtime().adapter(handle).start_task,
        handle,
        instruction=_PROVIDER_FREE_INSTRUCTION,
        attempt_workspace=relative_workspace,
        max_iterations=8,
    )


@activity.defn(name="collect_openhands_result")
async def collect_openhands_result(
    handle: ExecutionHandle,
) -> TaskSubmission:
    runtime = _configured_runtime()
    adapter = runtime.adapter(handle)
    try:
        for _ in range(300):
            status = await asyncio.to_thread(adapter.get_status, handle)
            if status in {"finished", "error", "stuck"}:
                return await asyncio.to_thread(adapter.collect_result, handle)
            activity.heartbeat({"conversation_terminal": False})
            await asyncio.sleep(1)
        raise RuntimeError("openhands_conversation_timeout")
    except BaseException:
        await asyncio.to_thread(runtime.controller.stop_and_remove, handle)
        raise


@activity.defn(name="cleanup_attempt")
async def cleanup_attempt(handle: ExecutionHandle) -> dict[str, bool]:
    runtime = _configured_runtime()
    await asyncio.to_thread(runtime.controller.stop_and_remove, handle)
    return {"attempt_removed": True}
