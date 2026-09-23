"""Provider-free regression coverage for the failed long-running system task."""
from datetime import datetime, timedelta, timezone
import subprocess

import pytest

from reverse_agent.model_access import credential_relay as relay
from reverse_agent.model_access.contracts import ExecutionSnapshot
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1 import opencode_executor as oe
from reverse_agent.platform_v1.binding_resolver import OpenCodeBindingResolution
from reverse_agent.platform_v1.opencode_server_transport import (
    ServerTransportResult, OpenCodeServerTransportError,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


@pytest.fixture
def clock(monkeypatch):
    class Clock(datetime):
        value = datetime(2026, 9, 23, tzinfo=timezone.utc)
        elapsed = 0.0

        @classmethod
        def now(cls, tz=None):
            return cls.value

    monkeypatch.setattr(relay, "datetime", Clock)
    monkeypatch.setattr(relay.time, "monotonic", lambda: Clock.elapsed)
    return Clock


def snapshot():
    return ExecutionSnapshot(
        binding_id="test-binding", binding_enabled=True, executor_id="opencode",
        raw_model_id="test-model", connection_id="test-connection",
        connection_enabled=True, provider="openai-compatible",
        base_url="https://example.invalid/v1", auth_method="api_key",
        resolved_api_key="synthetic-upstream-secret", external_session_status="not_applicable",
    )


def request(manager, lease_id, model="test-model"):
    return manager._validate_lease_for_request(
        lease_id, method="POST", path="/chat/completions", model=model,
    )


def test_long_task_remains_valid_then_expires_at_deadline(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.bind_execution_deadline(lease.lease_id, 300)
    clock.value += timedelta(seconds=126)
    assert request(manager, lease.lease_id).snapshot.binding_id == "test-binding"
    clock.value += timedelta(seconds=203)
    request(manager, lease.lease_id)
    clock.value += timedelta(seconds=1)
    with pytest.raises(relay.CredentialRelayError, match="expired"):
        request(manager, lease.lease_id)


@pytest.mark.parametrize("seconds", [True, False, 0, -1, float("nan"), float("inf"), 3601, 10**1000, "300"])
def test_invalid_budget_rejected_before_executor_or_lease_effects(clock, seconds):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    before = manager._leases[lease.lease_id].expires_at
    with pytest.raises(relay.CredentialRelayError, match="invalid_execution_timeout"):
        manager.bind_execution_deadline(lease.lease_id, seconds)
    assert manager._leases[lease.lease_id].expires_at == before
    with pytest.raises(oe.ExecutorRuntimeError, match="invalid_execution_timeout"):
        oe.OpenCodeExecutor(model_id="test/model", timeout=seconds)


def test_no_rebinding_revival_or_cross_lease_extension(clock):
    manager = relay.CredentialRelayManager()
    a = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    b = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.bind_execution_deadline(a.lease_id, 300)
    deadline = manager._leases[a.lease_id].expires_at
    with pytest.raises(relay.CredentialRelayError, match="already_bound"):
        manager.bind_execution_deadline(a.lease_id, 3600)
    assert manager._leases[a.lease_id].expires_at == deadline
    with pytest.raises(relay.CredentialRelayError, match="model_mismatch"):
        request(manager, a.lease_id, "different-model")
    clock.value += timedelta(seconds=120)
    with pytest.raises(relay.CredentialRelayError, match="unavailable"):
        manager.bind_execution_deadline(b.lease_id, 300)
    request(manager, a.lease_id)
    manager.release_lease(a.lease_id)
    with pytest.raises(relay.CredentialRelayError):
        request(manager, a.lease_id)
    with pytest.raises(relay.CredentialRelayError, match="unavailable"):
        manager.bind_execution_deadline(a.lease_id, 300)


def test_absolute_cap_and_backward_clock(clock):
    manager = relay.CredentialRelayManager()
    issued = clock.value
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    clock.value -= timedelta(seconds=1)
    with pytest.raises(relay.CredentialRelayError, match="clock_invalid"):
        manager.bind_execution_deadline(lease.lease_id, 300)
    clock.value = issued + timedelta(seconds=10)
    manager.bind_execution_deadline(lease.lease_id, 3600)
    assert manager._leases[lease.lease_id].expires_at == issued + timedelta(seconds=3630)


def test_wall_clock_rollback_cannot_extend_bound_lifetime(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.bind_execution_deadline(lease.lease_id, 300)
    clock.value -= timedelta(hours=1)
    clock.elapsed = 330
    with pytest.raises(relay.CredentialRelayError, match="expired"):
        request(manager, lease.lease_id)


@pytest.mark.parametrize("bound", [False, True])
def test_observed_expiration_is_irreversible_after_clock_rollback(clock, bound):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    if bound:
        manager.bind_execution_deadline(lease.lease_id, 300)
    before = clock.value
    clock.value += timedelta(hours=1)
    with pytest.raises(relay.CredentialRelayError, match="expired"):
        request(manager, lease.lease_id)
    clock.value = before
    with pytest.raises(relay.CredentialRelayError, match="expired"):
        request(manager, lease.lease_id)
    with pytest.raises(relay.CredentialRelayError, match="unavailable"):
        manager.bind_execution_deadline(lease.lease_id, 300)


def resolution():
    s = snapshot()
    return OpenCodeBindingResolution(
        binding_ref=s.binding_id, connection_id=s.connection_id, executor_id="opencode",
        provider_id=s.provider, model_id=s.provider + "/" + s.raw_model_id,
        base_url=s.base_url, auth_method="api_key", external_session_status="not_applicable",
        relay_required=True,
    )


def test_actual_host_provider_wires_bounded_deadline_and_release(clock):
    store = ModelProfileStore()
    s = snapshot()
    store.upsert_connection(dict(connection_id=s.connection_id, name="Synthetic",
        provider=s.provider, base_url=s.base_url, auth_method="api_key", enabled=True,
        api_key=s.resolved_api_key))
    store.upsert_binding(dict(binding_id=s.binding_id, name="Synthetic",
        executor_id="opencode", connection_id=s.connection_id, model_id=s.raw_model_id, enabled=True))
    host = CombinedTrustedHost(store=store, task_store=TaskStore(":memory:"), vault=None)
    host.relay_url = "http://127.0.0.1:1"
    handle = host._lease_provider_factory()(resolution())
    assert handle._deadline_callback is not None
    handle.bind_execution_deadline(300)
    clock.value += timedelta(seconds=126)
    request(host.relay_manager, handle.lease_id)
    assert s.resolved_api_key not in repr(handle)
    handle.release()
    handle.release()
    assert not host.relay_manager.has_active_lease(handle.lease_id)


@pytest.mark.parametrize("transport", ["cli", "server"])
@pytest.mark.parametrize("outcome", ["success", "nonzero", "timeout", "exception", "bind_error", "cancel", "event_error", "argv_error"])
def test_both_transports_bind_actual_budget_and_release(monkeypatch, tmp_path, transport, outcome):
    if transport == "server" and outcome == "argv_error":
        # Server uses its own transport rather than the CLI argv builder.
        outcome = "exception"
    calls = []
    def bind(seconds):
        calls.append(("bind", seconds))
        if outcome == "bind_error":
            raise RuntimeError("synthetic bind failure")
    handle = oe.ExecutionLeaseHandle("synthetic-lease", "http://127.0.0.1:1", "relay/test-model",
        _release_callback=lambda: calls.append(("release",)), _deadline_callback=bind)
    executor = oe.OpenCodeExecutor(binding_resolution=resolution(), timeout=247,
        lease_provider=lambda _: handle, parent_env={}, transport_kind=transport)
    store = TaskStore(":memory:")
    task = store.create_task(title="Synthetic task", executor_kind="opencode")
    monkeypatch.setattr(oe, "_collect_changed_files", lambda _: [])
    def run_cli(argv, **kwargs):
        if kwargs.get("timeout") == 247:
            calls.append(("run", kwargs["timeout"]))
            if outcome == "timeout":
                raise subprocess.TimeoutExpired(argv, 247)
            if outcome == "exception":
                raise RuntimeError("synthetic launch failure")
            if outcome == "cancel":
                raise KeyboardInterrupt()
            return subprocess.CompletedProcess(argv, int(outcome == "nonzero"), "", "")
        return subprocess.CompletedProcess(argv, 0, "", "")
    monkeypatch.setattr(oe.subprocess, "run", run_cli)
    if outcome == "argv_error":
        def fail_argv(*_, **__):
            raise RuntimeError("synthetic argv failure")
        monkeypatch.setattr(oe, "build_opencode_argv", fail_argv)
    def run_server(**kwargs):
        calls.append(("run", kwargs["timeout"]))
        if outcome in {"timeout", "exception"}:
            raise OpenCodeServerTransportError("server_" + outcome)
        if outcome == "cancel":
            raise KeyboardInterrupt()
        return ServerTransportResult(success=outcome in {"success", "event_error"}, failure_classification=("server_nonzero" if outcome == "nonzero" else ""))
    monkeypatch.setattr(oe, "run_managed_server_role", run_server)
    monkeypatch.setattr(store, "active_usage_budget_snapshot", lambda _: {})
    args = dict(task_id=task.id, store=store, worktree=tmp_path, execution_id="test-exec", base_sha="a" * 40,
        cli_path="fake-opencode", is_cmd=False, event_callback=None,
        role_context=oe.RoleContext("executor", task.id, tmp_path))
    if outcome == "event_error":
        def fail_event(*_):
            raise RuntimeError("synthetic event failure")
        args["event_callback"] = fail_event
    if outcome == "cancel":
        with pytest.raises(KeyboardInterrupt):
            executor._run_executor_core(**args)
    elif transport == "cli" and outcome in {"exception", "bind_error", "argv_error"}:
        with pytest.raises(RuntimeError):
            executor._run_executor_core(**args)
    else:
        result = executor._run_executor_core(**args)
        assert result.success == (outcome in {"success", "event_error"})
    assert calls[0] == ("bind", 247)
    assert calls[-1] == ("release",)
    assert calls.count(("release",)) == 1
    if outcome not in {"bind_error", "argv_error"}:
        assert ("run", 247) in calls


def test_windows_environment_is_minimal_and_validated():
    parent = {"PATH": "safe", "SystemRoot": "C:\\Windows", "SYSTEMDRIVE": "C:",
        "PATHEXT": ".COM;.EXE;.BAT;.CMD", "OPENAI_API_KEY": "must-not-pass", "HTTP_PROXY": "must-not-pass"}
    for builder in [lambda: oe.build_binding_child_env(parent, "{}"),
                    lambda: oe.build_role_child_env(parent, "{}", "coder")]:
        child = builder()
        assert child["SystemDrive"] == "C:"
        assert child["PATHEXT"] == parent["PATHEXT"]
        assert "OPENAI_API_KEY" not in child and "HTTP_PROXY" not in child
    for key, value in [("SystemDrive", "%SystemDrive%"), ("PATHEXT", ".EXE\x00"), ("PATHEXT", ".EXE;../bad")]:
        with pytest.raises(oe.ExecutorRuntimeError, match="invalid_child"):
            oe.build_binding_child_env({key: value}, "{}")
