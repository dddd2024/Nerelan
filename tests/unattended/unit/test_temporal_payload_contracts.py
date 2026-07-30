from __future__ import annotations

import asyncio
import inspect
import types
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin, get_type_hints

import pytest
from temporalio import activity
from temporalio.client import WorkflowFailureError
from temporalio.converter import DataConverter
from temporalio.exceptions import ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

from reverse_agent.unattended.activities import (
    cleanup_attempt,
    collect_openhands_result,
    launch_or_reconcile_attempt,
    start_openhands_conversation,
    wait_attempt_server,
)
from reverse_agent.unattended.contracts import ExecutionHandle
from reverse_agent.unattended.identifiers import (
    SANDBOX_CONTROLLER_TASK_QUEUE,
    TASK_QUEUE,
    executor_id,
    workspace_id,
)
from reverse_agent.unattended.temporal_contracts import (
    ActivityProgress,
    AttemptReadinessProgress,
    AttemptReadinessResult,
    CleanupResult,
    Gate2WorkflowResult,
    LaunchAttemptResult,
    OpenHandsLifecycleResult,
    SanitizedFailureCategory,
    TaskSubmissionEvidence,
)
from reverse_agent.unattended.workflows import UnattendedGate2Workflow

_BOUNDARY_VALUES = (
    LaunchAttemptResult(
        container_name="reverse-agent-attempt-fixed",
        state="running",
        image_digest="sha256:" + ("a" * 64),
        workspace_destination="/workspace/attempt",
        network_name="runtime-proof_model-executor",
        privileged=False,
        no_new_privileges=True,
        read_only_rootfs=True,
    ),
    AttemptReadinessResult(
        alive=True,
        health=True,
        poll_count=3,
        last_state="alive",
    ),
    OpenHandsLifecycleResult(
        conversation_id="11111111-1111-5111-8111-111111111111",
        attempt=1,
        lifecycle_state="started_or_reconciled",
        reconciled=True,
    ),
    TaskSubmissionEvidence(
        verdict="PROVIDER_FREE_RUNTIME_PROOF",
        summary="bounded",
        changed_paths=("provider-free-runtime-proof.txt",),
        commands_executed=("terminal_or_file_editor_action",),
        test_evidence=("typed_submission",),
        limitations=("no_real_provider",),
        failure_reason=None,
    ),
    CleanupResult(
        attempt_container_absent=True,
        attempt_workspace_absent=True,
    ),
    SanitizedFailureCategory(
        code="ATTEMPT_READINESS_FAILED",
        stage="readiness",
        retryable=True,
    ),
    ActivityProgress(stage="readiness", completed=False),
    AttemptReadinessProgress(
        state="connection_refused",
        poll_count=2,
        elapsed_milliseconds=250,
        next_delay_milliseconds=500,
    ),
)
_BOUNDARY_VALUES = _BOUNDARY_VALUES + (
    Gate2WorkflowResult(
        submission=_BOUNDARY_VALUES[3],
        cleanup=_BOUNDARY_VALUES[4],
        result_label="PROVIDER_FREE_RUNTIME_PROOF",
    ),
)


def _handle(suffix: str = "typed-contract") -> ExecutionHandle:
    identifier = f"unattended:dddd2024/reverse-agent:issue:83-{suffix}"
    return ExecutionHandle(
        identifier,
        1,
        workspace_id(identifier),
        executor_id(identifier, 1),
        "2026-07-30T03:30:00+00:00",
    )


async def _round_trip(value: object) -> object:
    converter = DataConverter.default
    payloads = await converter.encode([value])
    return (await converter.decode(payloads, [type(value)]))[0]


@pytest.mark.parametrize("value", _BOUNDARY_VALUES)
def test_pinned_default_data_converter_round_trips_every_boundary(
    value: object,
) -> None:
    assert asyncio.run(_round_trip(value)) == value


def _assert_supported(annotation: object, *, trail: str) -> None:
    if annotation in {Any, object}:
        raise AssertionError(f"{trail}: arbitrary type")
    if annotation in {str, int, bool, float, type(None)}:
        return
    origin = get_origin(annotation)
    arguments = get_args(annotation)
    if origin in {dict, Mapping} or (
        inspect.isclass(origin) and issubclass(origin, Mapping)
    ):
        raise AssertionError(f"{trail}: arbitrary mapping")
    if origin in {types.UnionType, getattr(types, "UnionType", None)}:
        concrete = tuple(item for item in arguments if item is not type(None))
        if len(arguments) != 2 or len(concrete) != 1:
            raise AssertionError(f"{trail}: unsupported union")
        _assert_supported(concrete[0], trail=trail)
        return
    if origin is tuple:
        if len(arguments) != 2 or arguments[1] is not Ellipsis:
            raise AssertionError(f"{trail}: tuple must have one concrete type")
        _assert_supported(arguments[0], trail=f"{trail}[]")
        return
    if annotation is ExecutionHandle or is_dataclass(annotation):
        for field in fields(annotation):
            resolved = get_type_hints(annotation)[field.name]
            _assert_supported(resolved, trail=f"{trail}.{field.name}")
        return
    raise AssertionError(f"{trail}: unsupported {annotation!r}")


def test_temporal_boundary_annotations_reject_arbitrary_shapes() -> None:
    activity_definitions = [
        launch_or_reconcile_attempt.__temporal_activity_definition,
        wait_attempt_server.__temporal_activity_definition,
        start_openhands_conversation.__temporal_activity_definition,
        collect_openhands_result.__temporal_activity_definition,
        cleanup_attempt.__temporal_activity_definition,
    ]
    workflow_definition = UnattendedGate2Workflow.__temporal_workflow_definition
    for definition in [*activity_definitions, workflow_definition]:
        for index, annotation in enumerate(definition.arg_types):
            _assert_supported(annotation, trail=f"{definition.name}.arg{index}")
        _assert_supported(definition.ret_type, trail=f"{definition.name}.return")

    for rejected in (
        object,
        Any,
        dict[str, object],
        Mapping[str, str],
        str | int,
        str | int | None,
    ):
        with pytest.raises(AssertionError):
            _assert_supported(rejected, trail="synthetic")


_MODE = "success"
_CALLS: list[str] = []
_COLLECT_STARTED: asyncio.Event | None = None


@activity.defn(name="launch_or_reconcile_attempt")
async def _fake_launch(handle: ExecutionHandle) -> LaunchAttemptResult:
    _CALLS.append("launch")
    return _BOUNDARY_VALUES[0]


@activity.defn(name="wait_attempt_server")
async def _fake_readiness(handle: ExecutionHandle) -> AttemptReadinessResult:
    _CALLS.append("readiness")
    return _BOUNDARY_VALUES[1]


@activity.defn(name="start_openhands_conversation")
async def _fake_start(handle: ExecutionHandle) -> OpenHandsLifecycleResult:
    _CALLS.append("start")
    return OpenHandsLifecycleResult(
        conversation_id=handle.executor_id,
        attempt=handle.attempt,
        lifecycle_state="started_or_reconciled",
        reconciled=True,
    )


@activity.defn(name="collect_openhands_result")
async def _fake_collect(handle: ExecutionHandle) -> TaskSubmissionEvidence:
    _CALLS.append("collect")
    if _MODE == "failure":
        raise ApplicationError(
            "sanitized_activity_failure",
            type="TASK_SUBMISSION_FAILED",
            non_retryable=True,
        )
    if _MODE == "cancel":
        assert _COLLECT_STARTED is not None
        _COLLECT_STARTED.set()
        await asyncio.Event().wait()
    return _BOUNDARY_VALUES[3]


@activity.defn(name="cleanup_attempt")
async def _fake_cleanup(handle: ExecutionHandle) -> CleanupResult:
    _CALLS.append("cleanup")
    return _BOUNDARY_VALUES[4]


async def _run_replay_scenario(mode: str) -> tuple[int, int]:
    global _MODE, _COLLECT_STARTED
    _MODE = mode
    _CALLS.clear()
    _COLLECT_STARTED = asyncio.Event()
    environment = await WorkflowEnvironment.start_time_skipping()
    async with environment:
        async with (
            Worker(
                environment.client,
                task_queue=TASK_QUEUE,
                workflows=[UnattendedGate2Workflow],
            ),
            Worker(
                environment.client,
                task_queue=SANDBOX_CONTROLLER_TASK_QUEUE,
                activities=[
                    _fake_launch,
                    _fake_readiness,
                    _fake_start,
                    _fake_collect,
                    _fake_cleanup,
                ],
            ),
        ):
            handle = await environment.client.start_workflow(
                UnattendedGate2Workflow.run,
                _handle(mode),
                id=f"temporal-contract-{mode}",
                task_queue=TASK_QUEUE,
            )
            if mode == "cancel":
                await asyncio.wait_for(_COLLECT_STARTED.wait(), timeout=10)
                await handle.cancel()
            if mode == "success":
                result = await handle.result()
                assert result == _BOUNDARY_VALUES[-1]
            else:
                with pytest.raises(WorkflowFailureError):
                    await handle.result()
            history = await handle.fetch_history()
            cleanup_before_replay = _CALLS.count("cleanup")
            await Replayer(
                workflows=[UnattendedGate2Workflow]
            ).replay_workflow(history)
            return cleanup_before_replay, _CALLS.count("cleanup")


@pytest.mark.parametrize("mode", ("success", "failure", "cancel"))
def test_success_failure_cancel_and_replay_cleanup_exactly_once(mode: str) -> None:
    before, after = asyncio.run(_run_replay_scenario(mode))
    assert before == 1
    assert after == 1
