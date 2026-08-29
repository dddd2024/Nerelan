"""Task runtime tests: ExecutorRouter, DeterministicFixtureExecutor, validation."""

import os
import subprocess
import tempfile

import pytest

from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import (
    DeterministicFixtureExecutor,
    ExecutorRuntimeError,
    ExecutorRouter,
    LocalValidationRunner,
)


def test_router_dispatches_fixture_executor() -> None:
    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        router = ExecutorRouter()
        result = router.dispatch_execute(
            task_id="task-r1",
            store=store,
            executor_kind="deterministic_fixture",
            workspace_root=td,
        )
        assert result.success is True
        assert result.validation_exit_code == 0
        assert result.validation_command_id == "git_diff_check"
        assert result.changed_files
        assert result.workspace
        assert result.execution_id == "exec-task-r1"


def test_executor_router_create_executor_opencode_returns_open_code_executor() -> None:
    from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor

    router = ExecutorRouter()
    executor = router.create_executor(
        executor_kind="opencode",
        model_id="sensetime/sensenova-6.7-flash-lite",
        opencode_exe="/fake/opencode",
    )
    assert isinstance(executor, OpenCodeExecutor)
    assert executor._model_id == "sensetime/sensenova-6.7-flash-lite"


def test_router_rejects_unknown_executor_kind() -> None:
    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        router = ExecutorRouter()
        with pytest.raises(ExecutorRuntimeError):
            router.dispatch_execute(
                task_id="task-r2",
                store=store,
                executor_kind="unknown",
                workspace_root=td,
            )


def test_executor_requires_workspace_root() -> None:
    executor = DeterministicFixtureExecutor()
    with pytest.raises(ExecutorRuntimeError):
        executor.execute("task-r3", TaskStore(":memory:"))


def test_executor_emits_events_via_callback() -> None:
    with tempfile.TemporaryDirectory() as td:
        received: list[dict] = []

        def cb(task_id: str, event: dict) -> None:
            received.append({"task_id": task_id, **event})

        executor = DeterministicFixtureExecutor()
        executor.execute(
            "task-r4",
            TaskStore(":memory:"),
            workspace_root=td,
            event_callback=cb,
        )
        types = [e["type"] for e in received]
        assert "WORKSPACE_READY" in types
        assert "EXECUTOR_FINISHED" in types
        assert "LOCAL_VALIDATED" in types
        assert "VALIDATED" in types


def test_executor_changes_file() -> None:
    with tempfile.TemporaryDirectory() as td:
        executor = DeterministicFixtureExecutor()
        result = executor.execute("task-r5", TaskStore(":memory:"), workspace_root=td)
        paths = [f["path"] for f in result.changed_files]
        assert "fixture.txt" in paths
        modified = next(f for f in result.changed_files if f["path"] == "fixture.txt")
        assert modified["additions"] >= 1


def test_validation_runner_rejects_unknown_command() -> None:
    with tempfile.TemporaryDirectory() as td:
        runner = LocalValidationRunner()
        with pytest.raises(ExecutorRuntimeError):
            runner.run(task_id="t", command_id="not_approved", cwd=td)


def test_validation_runner_runs_git_diff_check() -> None:
    with tempfile.TemporaryDirectory() as td:
        git_init = subprocess.run(
            ["git", "init", "-q"],
            cwd=td,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        assert git_init.returncode == 0
        runner = LocalValidationRunner()
        exit_code, output, digest = runner.run(
            task_id="t",
            command_id="git_diff_check",
            cwd=td,
        )
        assert exit_code == 0
        assert digest
        assert len(digest) == 64


def test_registration_allows_new_executor_kind_and_normalizes_lookup() -> None:
    router = ExecutorRouter()

    class DummyExecutor:
        def execute(self, task_id, store, *, workspace_root="", event_callback=None):
            from reverse_agent.platform_v1.task_runtime import FixtureExecutorResult

            return FixtureExecutorResult(
                success=True,
                validation_exit_code=0,
                validation_command_id="noop",
                validation_output_digest="x",
                validation_output_summary="",
                changed_files=[],
                workspace="",
                execution_id="exec-dummy",
            )

    router.register(" Dummy ", lambda: DummyExecutor())
    with tempfile.TemporaryDirectory() as td:
        result = router.dispatch_execute(
            task_id="task-r6",
            store=TaskStore(":memory:"),
            executor_kind="DUMMY",
            workspace_root=td,
        )
        assert result.validation_command_id == "noop"


def test_registration_rejects_duplicate_normalized_kind_and_preserves_factory() -> None:
    router = ExecutorRouter()

    class FirstExecutor:
        def execute(self, task_id, store, *, workspace_root="", event_callback=None):
            from reverse_agent.platform_v1.task_runtime import FixtureExecutorResult

            return FixtureExecutorResult(
                success=True,
                validation_exit_code=0,
                validation_command_id="first",
                validation_output_digest="first",
                validation_output_summary="",
                execution_id="exec-first",
            )

    class ReplacementExecutor(FirstExecutor):
        pass

    first_factory = lambda: FirstExecutor()
    router.register("custom", first_factory)

    with pytest.raises(ExecutorRuntimeError, match=r"^duplicate_executor_kind:custom$"):
        router.register(" CUSTOM ", lambda: ReplacementExecutor())

    assert router._registry["custom"] is first_factory
    with tempfile.TemporaryDirectory() as td:
        result = router.dispatch_execute(
            task_id="task-duplicate-custom",
            store=TaskStore(":memory:"),
            executor_kind=" Custom ",
            workspace_root=td,
        )
    assert result.validation_command_id == "first"


def test_registration_cannot_shadow_builtin_opencode_alias() -> None:
    from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor

    router = ExecutorRouter()
    original_factory = router._registry["opencode"]

    with pytest.raises(ExecutorRuntimeError, match=r"^duplicate_executor_kind:opencode$"):
        router.register(" OPENCODE ", lambda: object())

    assert router._registry["opencode"] is original_factory
    executor = router.create_executor(
        executor_kind=" OpenCode ",
        model_id="sensetime/sensenova-6.7-flash-lite",
        opencode_exe="/fake/opencode",
    )
    assert isinstance(executor, OpenCodeExecutor)


def test_registration_cannot_shadow_builtin_fixture_alias() -> None:
    router = ExecutorRouter()
    original_factory = router._registry["deterministic_fixture"]

    with pytest.raises(
        ExecutorRuntimeError,
        match=r"^duplicate_executor_kind:deterministic_fixture$",
    ):
        router.register(" DETERMINISTIC_FIXTURE ", lambda: object())

    assert router._registry["deterministic_fixture"] is original_factory
    with tempfile.TemporaryDirectory() as td:
        result = router.dispatch_execute(
            task_id="task-fixture-alias",
            store=TaskStore(":memory:"),
            executor_kind=" Deterministic_Fixture ",
            workspace_root=td,
        )
    assert result.success is True
