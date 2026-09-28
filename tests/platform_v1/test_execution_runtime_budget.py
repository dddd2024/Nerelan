"""Provider-free regression coverage for the Issue 989 lease lifetime residual.

A 300-second task must keep working past the generic 120-second lease default,
must expire exactly at the configured execution budget plus the bounded setup
margin, must never be renewed/revived/re-bound, and must be released on every
completion and exception path for both transports.

Synthetic credentials and a virtual clock only. No provider, network, or real
credential access.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import subprocess

import pytest

from reverse_agent.model_access import credential_relay as relay
from reverse_agent.model_access.contracts import ExecutionSnapshot
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1 import opencode_executor as oe
from reverse_agent.platform_v1.binding_resolver import OpenCodeBindingResolution
from reverse_agent.platform_v1.opencode_server_transport import (
    OpenCodeServerTransportError,
    ServerTransportResult,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


# ---------------------------------------------------------------------------
# Virtual clock / synthetic credentials
# ---------------------------------------------------------------------------

_SYNTHETIC_SECRET = "synthetic-upstream-secret"


@pytest.fixture
def clock(monkeypatch):
    """Deterministic UTC wall clock plus an independently movable monotonic."""

    class Clock(datetime):
        value = datetime(2026, 9, 23, tzinfo=timezone.utc)
        elapsed = 0.0

        @classmethod
        def now(cls, tz=None):
            return cls.value

    monkeypatch.setattr(relay, "datetime", Clock)
    monkeypatch.setattr(
        relay, "time", SimpleNamespace(monotonic=lambda: Clock.elapsed)
    )
    return Clock


def snapshot(**overrides):
    base = dict(
        binding_id="test-binding",
        binding_enabled=True,
        executor_id="opencode",
        raw_model_id="test-model",
        connection_id="test-connection",
        connection_enabled=True,
        provider="openai-compatible",
        base_url="https://example.invalid/v1",
        auth_method="api_key",
        resolved_api_key=_SYNTHETIC_SECRET,
        external_session_status="not_applicable",
    )
    base.update(overrides)
    return ExecutionSnapshot(**base)


def request(manager, lease_id, model="test-model"):
    return manager._validate_lease_for_request(
        lease_id,
        method="POST",
        path="/chat/completions",
        model=model,
    )


def active_of(manager, lease_id):
    return manager._leases[lease_id]


# ---------------------------------------------------------------------------
# Deadline semantics
# ---------------------------------------------------------------------------


def test_long_task_survives_default_then_expires_exactly_at_deadline(clock):
    manager = relay.CredentialRelayManager()
    assert manager._default_expiry == 120.0

    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.bind_execution_deadline(lease.lease_id, 300)
    assert active_of(manager, lease.lease_id).expires_at == clock.value + timedelta(
        seconds=330
    )

    clock.value += timedelta(seconds=126)
    request(manager, lease.lease_id)
    clock.value += timedelta(seconds=203)
    assert not active_of(manager, lease.lease_id).expired
    clock.value += timedelta(seconds=1)
    assert active_of(manager, lease.lease_id).expired
    with pytest.raises(relay.CredentialRelayError, match="expired"):
        request(manager, lease.lease_id)


def test_expiry_boundary_is_exact_not_early(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.bind_execution_deadline(lease.lease_id, 300)

    clock.value += timedelta(seconds=329)
    assert not active_of(manager, lease.lease_id).expired
    clock.value += timedelta(seconds=1)
    assert active_of(manager, lease.lease_id).expired


def test_setup_margin_never_extends_the_execution_timeout(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    issued = clock.value

    clock.value += timedelta(seconds=25)
    clock.elapsed = 25.0
    manager.bind_execution_deadline(lease.lease_id, 60)

    deadline = active_of(manager, lease.lease_id).expires_at
    assert deadline == clock.value + timedelta(seconds=90)
    assert deadline == issued + timedelta(seconds=115)


def test_absolute_lease_lifetime_cap_clamps_the_max_budget(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    issued = clock.value

    clock.value += timedelta(seconds=10)
    clock.elapsed = 10.0
    manager.bind_execution_deadline(lease.lease_id, 3600)

    assert active_of(manager, lease.lease_id).expires_at == issued + timedelta(
        seconds=3630
    )
    assert active_of(manager, lease.lease_id).execution_deadline_bound is True


def test_backward_clock_at_bind_time_is_rejected(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    issued = clock.value

    clock.value -= timedelta(seconds=1)
    clock.elapsed = -1.0
    with pytest.raises(relay.CredentialRelayError, match="clock_invalid"):
        manager.bind_execution_deadline(lease.lease_id, 300)
    assert active_of(manager, lease.lease_id).execution_deadline_bound is False

    clock.value = issued + timedelta(seconds=10)
    clock.elapsed = 10.0
    manager.bind_execution_deadline(lease.lease_id, 300)
    assert active_of(manager, lease.lease_id).expires_at == issued + timedelta(
        seconds=340
    )


def test_wall_clock_rollback_cannot_prolong_a_bound_lease(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.bind_execution_deadline(lease.lease_id, 300)

    clock.value -= timedelta(hours=1)
    clock.elapsed = 331.0
    with pytest.raises(relay.CredentialRelayError, match="expired"):
        request(manager, lease.lease_id)


@pytest.mark.parametrize("bound", [False, True])
def test_observed_expiration_is_terminal_after_wall_clock_rollback(clock, bound):
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


def test_release_is_terminal_and_expired_leases_are_cleaned_up(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.release_lease(lease.lease_id)
    with pytest.raises(relay.CredentialRelayError, match="not_found|released"):
        request(manager, lease.lease_id)
    assert manager.lease_count() == 0

    late = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.bind_execution_deadline(late.lease_id, 300)
    clock.value += timedelta(seconds=331)
    assert manager.lease_count() == 0


# ---------------------------------------------------------------------------
# No renewal / rebinding / revival / cross-lease extension
# ---------------------------------------------------------------------------


def test_no_rebinding_no_revival_and_no_cross_lease_extension(clock):
    manager = relay.CredentialRelayManager()
    first = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    second = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")

    manager.bind_execution_deadline(first.lease_id, 300)
    first_deadline = active_of(manager, first.lease_id).expires_at
    with pytest.raises(relay.CredentialRelayError, match="already_bound"):
        manager.bind_execution_deadline(first.lease_id, 3600)
    assert active_of(manager, first.lease_id).expires_at == first_deadline

    manager.bind_execution_deadline(second.lease_id, 60)
    assert active_of(manager, first.lease_id).expires_at == first_deadline
    assert active_of(manager, second.lease_id).expires_at == clock.value + timedelta(
        seconds=90
    )

    request(manager, first.lease_id)
    with pytest.raises(relay.CredentialRelayError, match="already_bound"):
        manager.bind_execution_deadline(first.lease_id, 300)
    manager.release_lease(first.lease_id)
    with pytest.raises(relay.CredentialRelayError):
        request(manager, first.lease_id)
    with pytest.raises(relay.CredentialRelayError, match="unavailable"):
        manager.bind_execution_deadline(first.lease_id, 300)

    consumed = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    request(manager, consumed.lease_id)
    with pytest.raises(relay.CredentialRelayError, match="already_bound"):
        manager.bind_execution_deadline(consumed.lease_id, 300)


def test_released_and_expired_leases_are_never_rebound_or_revived(clock):
    manager = relay.CredentialRelayManager()
    released = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    manager.release_lease(released.lease_id)
    with pytest.raises(relay.CredentialRelayError, match="unavailable"):
        manager.bind_execution_deadline(released.lease_id, 300)

    expired = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    clock.value += timedelta(seconds=121)
    with pytest.raises(relay.CredentialRelayError, match="unavailable"):
        manager.bind_execution_deadline(expired.lease_id, 300)

    with pytest.raises(relay.CredentialRelayError, match="unavailable"):
        manager.bind_execution_deadline("sk-not-a-real-lease", 300)


# ---------------------------------------------------------------------------
# Invalid timing inputs are rejected before any side effect
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "seconds",
    [
        True,
        False,
        0,
        0.0,
        -1,
        -0.5,
        float("nan"),
        float("inf"),
        -float("inf"),
        3600.001,
        3601,
        10**1000,
        -10**1000,
        "300",
        None,
        [300],
        {300: 1},
    ],
)
def test_invalid_execution_timeout_rejected_without_lease_mutation(clock, seconds):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    before = active_of(manager, lease.lease_id).expires_at

    with pytest.raises(relay.CredentialRelayError, match="invalid_execution_timeout"):
        manager.bind_execution_deadline(lease.lease_id, seconds)
    assert active_of(manager, lease.lease_id).expires_at == before
    assert active_of(manager, lease.lease_id).execution_deadline_bound is False
    assert active_of(manager, lease.lease_id).used is False


@pytest.mark.parametrize(
    "seconds",
    [
        True,
        False,
        0,
        -1,
        float("nan"),
        float("inf"),
        -float("inf"),
        3601,
        10**1000,
        -10**1000,
        "300",
        None,
        object(),
    ],
)
def test_invalid_executor_timeout_rejected_without_overflow_or_effect(seconds):
    with pytest.raises(oe.ExecutorRuntimeError, match="invalid_execution_timeout"):
        oe.OpenCodeExecutor(model_id="test/model", timeout=seconds)


def test_executor_timeout_defaults_are_preserved():
    assert oe.OpenCodeExecutor(model_id="test/model")._timeout == 300
    assert oe.OpenCodeExecutor(model_id="test/model", timeout=247)._timeout == 247
    assert oe.OpenCodeExecutor(model_id="test/model", timeout=3600)._timeout == 3600


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"default_expiry_seconds": True}, "invalid_default_expiry"),
        ({"default_expiry_seconds": False}, "invalid_default_expiry"),
        ({"default_expiry_seconds": 0}, "invalid_default_expiry"),
        ({"default_expiry_seconds": -5}, "invalid_default_expiry"),
        ({"default_expiry_seconds": float("nan")}, "invalid_default_expiry"),
        ({"default_expiry_seconds": float("inf")}, "invalid_default_expiry"),
        ({"default_expiry_seconds": 10**1000}, "invalid_default_expiry"),
        ({"default_expiry_seconds": "120"}, "invalid_default_expiry"),
        ({"cleanup_margin_seconds": True}, "invalid_cleanup_margin"),
        ({"cleanup_margin_seconds": False}, "invalid_cleanup_margin"),
        ({"cleanup_margin_seconds": -1}, "invalid_cleanup_margin"),
        ({"cleanup_margin_seconds": float("nan")}, "invalid_cleanup_margin"),
        ({"cleanup_margin_seconds": float("inf")}, "invalid_cleanup_margin"),
        ({"cleanup_margin_seconds": 10**1000}, "invalid_cleanup_margin"),
        ({"cleanup_margin_seconds": "-1"}, "invalid_cleanup_margin"),
    ],
)
def test_manager_lifetime_admission_rejects_invalid_numeric_inputs(kwargs, match):
    with pytest.raises(relay.CredentialRelayError, match=match):
        relay.CredentialRelayManager(**kwargs)


def test_manager_lifetime_defaults_are_not_widened():
    manager = relay.CredentialRelayManager()
    assert manager._default_expiry == 120.0
    assert manager._cleanup_margin == 30.0
    assert relay.CredentialRelayManager(
        default_expiry_seconds=120, cleanup_margin_seconds=0
    )._default_expiry == 120.0


@pytest.mark.parametrize(
    "seconds",
    [True, False, 0, -1, float("nan"), float("inf"), 10**1000, "-1", [1]],
)
def test_create_lease_expiry_override_rejected_before_side_effects(clock, seconds):
    manager = relay.CredentialRelayManager()
    with pytest.raises(relay.CredentialRelayError, match="invalid_expiry_seconds"):
        manager.create_lease(
            snapshot(), relay_url="http://127.0.0.1:1", expiry_seconds=seconds
        )
    assert manager.lease_count() == 0


# ---------------------------------------------------------------------------
# Actual host -> executor -> manager composition
# ---------------------------------------------------------------------------


def resolution():
    return OpenCodeBindingResolution(
        binding_ref="test-binding",
        connection_id="test-connection",
        executor_id="opencode",
        provider_id="openai-compatible",
        model_id="openai-compatible/test-model",
        base_url="https://example.invalid/v1",
        auth_method="api_key",
        external_session_status="not_applicable",
        relay_required=True,
    )


def test_actual_host_provider_binds_bounded_deadline_and_releases(clock):
    store = ModelProfileStore()
    store.upsert_connection(
        dict(
            connection_id="test-connection",
            name="Synthetic",
            provider="openai-compatible",
            base_url="https://example.invalid/v1",
            auth_method="api_key",
            enabled=True,
            api_key=_SYNTHETIC_SECRET,
        )
    )
    store.upsert_binding(
        dict(
            binding_id="test-binding",
            name="Synthetic",
            executor_id="opencode",
            connection_id="test-connection",
            model_id="test-model",
            enabled=True,
        )
    )
    host = CombinedTrustedHost(
        store=store,
        task_store=TaskStore(":memory:"),
        vault=None,
    )
    host.relay_url = "http://127.0.0.1:1"

    handle = host._lease_provider_factory()(resolution())
    assert handle._deadline_callback is not None

    handle.bind_execution_deadline(300)
    assert active_of(host.relay_manager, handle.lease_id).expires_at == (
        clock.value + timedelta(seconds=330)
    )

    clock.value += timedelta(seconds=126)
    assert request(host.relay_manager, handle.lease_id).snapshot.binding_id == (
        "test-binding"
    )
    assert _SYNTHETIC_SECRET not in repr(handle)
    assert host.relay_manager.has_active_lease(handle.lease_id)

    handle.release()
    handle.release()
    assert not host.relay_manager.has_active_lease(handle.lease_id)
    with pytest.raises(relay.CredentialRelayError):
        request(host.relay_manager, handle.lease_id)


@pytest.mark.parametrize("transport", ["cli", "server"])
@pytest.mark.parametrize(
    "outcome",
    [
        "success",
        "nonzero",
        "timeout",
        "exception",
        "bind_error",
        "cancel",
        "event_error",
        "argv_error",
    ],
)
def test_both_transports_bind_once_and_release_once(
    monkeypatch, tmp_path, transport, outcome
):
    if transport == "server" and outcome == "argv_error":
        outcome = "exception"

    calls: list[tuple[str, object]] = []

    def bind(seconds):
        calls.append(("bind", seconds))
        if outcome == "bind_error":
            raise RuntimeError("synthetic bind failure")

    handle = oe.ExecutionLeaseHandle(
        "synthetic-lease",
        "http://127.0.0.1:1",
        "relay/test-model",
        _release_callback=lambda: calls.append(("release", None)),
        _deadline_callback=bind,
    )
    executor = oe.OpenCodeExecutor(
        binding_resolution=resolution(),
        timeout=247,
        lease_provider=lambda _: handle,
        parent_env={},
        transport_kind=transport,
    )
    store = TaskStore(":memory:")
    task = store.create_task(title="Synthetic task", executor_kind="opencode")
    monkeypatch.setattr(oe, "_collect_changed_files", lambda _: [])
    monkeypatch.setattr(
        executor,
        "_run_git",
        lambda argv, cwd, timeout: subprocess.CompletedProcess(argv, 0, "", ""),
    )

    def run_cli(argv, **kwargs):
        calls.append(("run", kwargs.get("timeout")))
        if outcome == "timeout":
            raise subprocess.TimeoutExpired(argv, 247)
        if outcome == "exception":
            raise RuntimeError("synthetic launch failure")
        if outcome == "cancel":
            raise KeyboardInterrupt()
        return subprocess.CompletedProcess(argv, int(outcome == "nonzero"), "", "")

    monkeypatch.setattr(oe.subprocess, "run", run_cli)

    if outcome == "argv_error":
        def fail_argv(*_, **__):
            raise RuntimeError("synthetic argv failure")

        monkeypatch.setattr(oe, "build_opencode_argv", fail_argv)

    def run_server(**kwargs):
        calls.append(("run", kwargs.get("timeout")))
        if outcome in {"timeout", "exception", "bind_error"}:
            raise OpenCodeServerTransportError("server_" + outcome)
        if outcome == "cancel":
            raise KeyboardInterrupt()
        return ServerTransportResult(
            success=outcome in {"success", "event_error"},
            failure_classification=("server_nonzero" if outcome == "nonzero" else ""),
        )

    monkeypatch.setattr(oe, "run_managed_server_role", run_server)
    monkeypatch.setattr(store, "active_usage_budget_snapshot", lambda _: {})

    args = dict(
        task_id=task.id,
        store=store,
        worktree=tmp_path,
        base_sha="a" * 40,
        execution_id="test-exec",
        cli_path="fake-opencode",
        is_cmd=False,
        event_callback=None,
        role_context=oe.RoleContext(
            role="executor", task_id=task.id, workspace=tmp_path
        ),
    )
    if outcome == "event_error":
        def fail_event(*_):
            raise RuntimeError("synthetic event failure")

        args["event_callback"] = fail_event

    expected_timeout = 247.0 if transport == "server" else 247
    if outcome == "cancel":
        with pytest.raises(KeyboardInterrupt):
            executor._run_executor_core(**args)
    elif outcome in {"exception", "bind_error", "argv_error"} and transport == "cli":
        with pytest.raises(RuntimeError):
            executor._run_executor_core(**args)
    else:
        result = executor._run_executor_core(**args)
        assert result.success == (outcome in {"success", "event_error"})

    assert calls[0] == ("bind", 247)
    assert calls.count(("bind", 247)) == 1
    assert calls[-1] == ("release", None)
    assert calls.count(("release", None)) == 1
    if outcome not in {"bind_error", "argv_error"}:
        assert ("run", expected_timeout) in calls


# ---------------------------------------------------------------------------
# Finite-but-huge durations fail closed before any side effect, and the
# generic lease API is not capped below representable absolute expiries.
# ---------------------------------------------------------------------------

_HUGE_FINITE_DURATIONS = (1e300, 10**18, 10**19)


@pytest.mark.parametrize("seconds", _HUGE_FINITE_DURATIONS)
def test_huge_finite_default_rejected_before_token_allocation(clock, monkeypatch, seconds):
    allocations: list[int] = []
    monkeypatch.setattr(
        relay.secrets,
        "token_urlsafe",
        lambda n: allocations.append(n) or "sk-tracked-allocation",
    )

    manager = relay.CredentialRelayManager(default_expiry_seconds=seconds)
    with pytest.raises(relay.CredentialRelayError, match="invalid_default_expiry"):
        manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")

    assert allocations == []
    assert manager.lease_count() == 0


@pytest.mark.parametrize("seconds", _HUGE_FINITE_DURATIONS)
def test_huge_finite_override_rejected_before_token_allocation(clock, monkeypatch, seconds):
    allocations: list[int] = []
    monkeypatch.setattr(
        relay.secrets,
        "token_urlsafe",
        lambda n: allocations.append(n) or "sk-tracked-allocation",
    )

    manager = relay.CredentialRelayManager()
    with pytest.raises(relay.CredentialRelayError, match="invalid_expiry_seconds"):
        manager.create_lease(
            snapshot(), relay_url="http://127.0.0.1:1", expiry_seconds=seconds
        )

    assert allocations == []
    assert manager.lease_count() == 0


@pytest.mark.parametrize("seconds", (3600, 86400, 10**9))
def test_representable_durations_above_default_are_not_capped(clock, seconds):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(
        snapshot(), relay_url="http://127.0.0.1:1", expiry_seconds=seconds
    )

    assert lease.lease_id.startswith("sk-")
    assert lease.expires_at == clock.value + timedelta(seconds=seconds)
    assert manager.lease_count() == 1


def test_successful_validation_marks_used_inside_lock_and_blocks_rebind(clock):
    manager = relay.CredentialRelayManager()
    lease = manager.create_lease(snapshot(), relay_url="http://127.0.0.1:1")
    active = active_of(manager, lease.lease_id)
    expiry_before = (active.expires_at, active.expires_monotonic)

    with pytest.raises(relay.CredentialRelayError, match="lease_model_mismatch"):
        request(manager, lease.lease_id, model="other-model")
    assert active.used is False
    assert (active.expires_at, active.expires_monotonic) == expiry_before

    seen = []
    real_lock = manager._lock

    class TrackedLock:
        def acquire(self, blocking=True, timeout=-1):
            return real_lock.acquire(blocking=blocking, timeout=timeout)

        def release(self):
            return real_lock.release()

        def __enter__(self):
            real_lock.acquire()
            return self

        def __exit__(self, exc_type, exc, tb):
            if not seen:
                seen.append(active.used)
            real_lock.release()
            return False

    manager._lock = TrackedLock()

    returned = request(manager, lease.lease_id)

    assert returned is active
    assert active.used is True
    assert seen == [True]

    with pytest.raises(
        relay.CredentialRelayError, match="execution_deadline_already_bound"
    ):
        manager.bind_execution_deadline(lease.lease_id, timeout_seconds=300.0)
