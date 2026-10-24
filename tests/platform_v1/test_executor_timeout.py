"""Executor turn timeout is trusted host configuration with safe bounds."""
import pytest

from reverse_agent.platform_v1 import durable_execution as de


@pytest.mark.parametrize("raw,expected", [
    (None, 600), ("", 600), ("not-a-number", 600),
    ("900", 900), ("3000", 3000), ("3601", 3600), ("10", 60), ("420", 420),
])
def test_executor_timeout_is_bounded_host_configuration(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv("REVERSE_AGENT_EXECUTOR_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("REVERSE_AGENT_EXECUTOR_TIMEOUT_SECONDS", raw)
    assert de.executor_timeout_seconds() == expected


@pytest.mark.parametrize("kind", ["codex", "claude_code"])
@pytest.mark.parametrize("raw,learned,expected", [(None, None, 600), ("3000", None, 3000),
    ("9999", None, 3600), (None, 3000, 3000), (None, 9999, 3600)])
def test_native_kwargs_use_resolved_timeout(monkeypatch, kind, raw, learned, expected):
    from types import SimpleNamespace
    from reverse_agent.platform_v1 import codex_executor, model_profiles
    from reverse_agent.platform_v1.run_store import TaskStore

    if raw is None:
        monkeypatch.delenv("REVERSE_AGENT_EXECUTOR_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("REVERSE_AGENT_EXECUTOR_TIMEOUT_SECONDS", raw)
    store = TaskStore(":memory:")
    try:
        task = store.create_task(title="turn", executor_kind=kind, binding_ref="fixture-binding")
        service = de.DurableExecutionService.__new__(de.DurableExecutionService)
        service.store, service.binding_resolver, service.lease_provider = store, None, None
        monkeypatch.setattr(model_profiles, "recommended_timeout_seconds", lambda *args: learned)
        monkeypatch.setattr(codex_executor, "codex_executor_kwargs",
            lambda *args, **kwargs: {"binding_resolution": SimpleNamespace(relay_required=False)})
        monkeypatch.setattr(de, "_require_native_owner_execution_binding", lambda *args: None)
        assert service._build_executor_kwargs(task)["timeout"] == expected
    finally:
        store._conn.close()


@pytest.mark.parametrize("kind,model", [("codex", "gpt-6.1-sol"), ("claude_code", "sonnet")])
def test_native_executor_timeout_boundary(kind, model):
    from reverse_agent.platform_v1.codex_executor import CodexExecutor
    from reverse_agent.platform_v1.claude_executor import ClaudeCodeExecutor
    from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError

    executor = CodexExecutor if kind == "codex" else ClaudeCodeExecutor
    assert executor(model_id=model, timeout=3600)._timeout == 3600
    for timeout in (3601, 0, -1, True, float("nan"), float("inf")):
        with pytest.raises(ExecutorRuntimeError, match="timeout_invalid"):
            executor(model_id=model, timeout=timeout)
