"""Fixed controller Activities for the Gate 2 Attempt lifecycle."""

from __future__ import annotations

import asyncio
from pathlib import Path

from temporalio import activity
from temporalio.exceptions import ApplicationError

from ..attempt_transport import AttemptJsonTransport
from ..contracts import ExecutionHandle
from ..identifiers import workspace_path
from ..openhands import OpenHandsAdapter
from ..readiness import (
    AttemptReadinessTerminal,
    AttemptReadinessTimeout,
    wait_for_attempt_readiness,
)
from ..sandbox import (
    FIXED_LAUNCH_SPEC,
    SandboxController,
    SandboxControllerError,
    SubprocessDockerRunner,
)
from ..temporal_contracts import (
    ActivityProgress,
    AttemptReadinessResult,
    CleanupResult,
    LaunchAttemptResult,
    OpenHandsLifecycleResult,
    SanitizedFailureCategory,
    TaskSubmissionEvidence,
    WorkspaceRootPreflightResult,
)
from ..workspace import WorkspacePreflightError

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


def _raise_sanitized(category: SanitizedFailureCategory) -> None:
    raise ApplicationError(
        "sanitized_activity_failure",
        category,
        type=category.code,
        non_retryable=not category.retryable,
    ) from None


@activity.defn(name="launch_or_reconcile_attempt")
async def launch_or_reconcile_attempt(
    handle: ExecutionHandle,
) -> LaunchAttemptResult:
    try:
        runtime = _configured_runtime()
        metadata = await asyncio.to_thread(
            runtime.controller.launch_or_reconcile,
            handle,
            FIXED_LAUNCH_SPEC,
        )
        return LaunchAttemptResult(
            container_name=metadata.container_name,
            state=metadata.state,
            image_digest=metadata.image_digest,
            workspace_destination=metadata.workspace_destination,
            network_name=metadata.network_name,
            privileged=metadata.privileged,
            no_new_privileges=metadata.no_new_privileges,
            read_only_rootfs=metadata.read_only_rootfs,
        )
    except WorkspacePreflightError as error:
        _raise_sanitized(
            SanitizedFailureCategory(
                error.code,
                "workspace_preflight",
                False,
            )
        )
    except Exception:
        _raise_sanitized(
            SanitizedFailureCategory(
                "ATTEMPT_LAUNCH_FAILED", "launch", True
            )
        )


@activity.defn(name="workspace_root_preflight")
async def workspace_root_preflight(
    handle: ExecutionHandle,
) -> WorkspaceRootPreflightResult:
    try:
        return await asyncio.to_thread(
            _configured_runtime().controller.preflight_workspace,
            handle,
        )
    except WorkspacePreflightError as error:
        _raise_sanitized(
            SanitizedFailureCategory(
                error.code,
                "workspace_preflight",
                False,
            )
        )


@activity.defn(name="wait_attempt_server")
async def wait_attempt_server(handle: ExecutionHandle) -> AttemptReadinessResult:
    runtime = _configured_runtime()
    transport = AttemptJsonTransport(
        runtime.runner,
        handle,
        sensitive_values=(runtime.executor_api_key,),
    )

    async def inspect_container():
        try:
            return await asyncio.to_thread(runtime.controller.inspect, handle)
        except SandboxControllerError as error:
            raise AttemptReadinessTerminal("container_contract_drift") from None

    async def probe_loopback():
        return await asyncio.to_thread(transport.probe_readiness)

    try:
        return await wait_for_attempt_readiness(
            inspect_container=inspect_container,
            probe_loopback=probe_loopback,
            heartbeat=activity.heartbeat,
            cancelled=activity.is_cancelled,
        )
    except AttemptReadinessTimeout:
        _raise_sanitized(
            SanitizedFailureCategory(
                "ATTEMPT_READINESS_TIMEOUT", "readiness", False
            )
        )
    except AttemptReadinessTerminal:
        _raise_sanitized(
            SanitizedFailureCategory(
                "ATTEMPT_READINESS_CONTRACT", "readiness", False
            )
        )


@activity.defn(name="start_openhands_conversation")
async def start_openhands_conversation(
    handle: ExecutionHandle,
) -> OpenHandsLifecycleResult:
    try:
        relative_workspace = str(
            Path(workspace_path(handle.workflow_id, handle.attempt)).relative_to(
                ".var/unattended"
            )
        ).replace("\\", "/")
        started = await asyncio.to_thread(
            _configured_runtime().adapter(handle).start_task,
            handle,
            instruction=_PROVIDER_FREE_INSTRUCTION,
            attempt_workspace=relative_workspace,
            max_iterations=8,
        )
        return OpenHandsLifecycleResult(
            conversation_id=started.executor_id,
            attempt=started.attempt,
            lifecycle_state="started_or_reconciled",
            reconciled=True,
        )
    except Exception:
        _raise_sanitized(
            SanitizedFailureCategory(
                "OPENHANDS_LIFECYCLE_FAILED", "start_conversation", True
            )
        )


@activity.defn(name="collect_openhands_result")
async def collect_openhands_result(
    handle: ExecutionHandle,
) -> TaskSubmissionEvidence:
    runtime = _configured_runtime()
    adapter = runtime.adapter(handle)
    try:
        for _ in range(300):
            status = await asyncio.to_thread(adapter.get_status, handle)
            if status in {"finished", "error", "stuck"}:
                await asyncio.to_thread(adapter.collect_result, handle)
                relative = Path(
                    workspace_path(handle.workflow_id, handle.attempt)
                ).relative_to(".var/unattended")
                proof = (
                    runtime.host_workspace_root
                    / relative
                    / "provider-free-runtime-proof.txt"
                )
                try:
                    content = await asyncio.to_thread(
                        proof.read_text, encoding="utf-8"
                    )
                except OSError as error:
                    raise RuntimeError(
                        "provider_free_workspace_proof_missing"
                    ) from error
                if content != "PROVIDER_FREE_RUNTIME_PROOF":
                    raise RuntimeError(
                        "provider_free_workspace_proof_mismatch"
                    )
                return TaskSubmissionEvidence(
                    verdict="PROVIDER_FREE_RUNTIME_PROOF",
                    summary=(
                        "Provider-free OpenHands conversation completed one "
                        "bounded terminal tool action."
                    ),
                    changed_paths=("provider-free-runtime-proof.txt",),
                    commands_executed=("terminal_or_file_editor_action",),
                    test_evidence=(
                        "executor_virtual_key_authenticated_litellm",
                        "openhands_conversation_create_run",
                        "inside_workspace_create_read",
                        "task_submission_collected",
                    ),
                    limitations=(
                        "No real provider credential or provider completion "
                        "was used.",
                    ),
                    failure_reason=None,
                )
            activity.heartbeat(ActivityProgress("collect_result", False))
            await asyncio.sleep(1)
    except Exception:
        _raise_sanitized(
            SanitizedFailureCategory(
                "TASK_SUBMISSION_FAILED", "collect_result", True
            )
        )
    _raise_sanitized(
        SanitizedFailureCategory(
            "TASK_SUBMISSION_FAILED", "collect_result", True
        )
    )


@activity.defn(name="cleanup_attempt")
async def cleanup_attempt(handle: ExecutionHandle) -> CleanupResult:
    try:
        runtime = _configured_runtime()
        container_absent, workspace_absent = await asyncio.to_thread(
            runtime.controller.cleanup_attempt, handle
        )
        return CleanupResult(
            attempt_container_absent=container_absent,
            attempt_workspace_absent=workspace_absent,
        )
    except Exception:
        _raise_sanitized(
            SanitizedFailureCategory(
                "ATTEMPT_CLEANUP_FAILED", "cleanup", True
            )
        )
