"""Focused provider-free lifecycle regressions for Work Item #385 V12."""

from __future__ import annotations

import socket
import threading
from typing import Any

import pytest

import reverse_agent.platform_v1.trusted_host as trusted_host_module
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.trusted_host import (
    CombinedTrustedHost,
    _wait_for_owned_serving_threads,
)


from _local_client_fixture import client_session, client_headers

def _make_store(tmp_path) -> TaskStore:
    return TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))


def test_owned_thread_wait_returns_immediately_without_threads() -> None:
    class Host:
        _threads: list[threading.Thread] = []

    _wait_for_owned_serving_threads(Host(), poll_interval=0.01)


def test_owned_thread_wait_blocks_until_live_thread_terminates() -> None:
    release = threading.Event()
    worker = threading.Thread(target=release.wait, daemon=True)
    worker.start()

    class Host:
        pass

    host = Host()
    host._threads = [worker]
    finished = threading.Event()

    def wait_for_host() -> None:
        _wait_for_owned_serving_threads(host, poll_interval=0.01)
        finished.set()

    waiter = threading.Thread(target=wait_for_host, daemon=True)
    waiter.start()
    assert not finished.wait(0.05)

    release.set()
    assert finished.wait(1.0)
    waiter.join(timeout=1.0)
    worker.join(timeout=1.0)
    assert not waiter.is_alive()
    assert not worker.is_alive()


def _install_fake_entrypoint_host(monkeypatch, tmp_path, *, wait_error=None):
    captured = {"host": None, "duplicate_serve": 0}

    class FakeServer:
        def serve_forever(self) -> None:
            captured["duplicate_serve"] += 1
            raise AssertionError("entrypoint must not own a second serving loop")

    class FakeHost:
        def __init__(self, **kwargs: Any) -> None:
            self.model_control_url = "http://127.0.0.1:18765"
            self.task_api_url = "http://127.0.0.1:18766"
            self.relay_url = "http://127.0.0.1:18767"
            self._model_server = FakeServer()
            self._threads: list[threading.Thread] = []
            self.start_calls = 0
            self.stop_calls = 0
            captured["host"] = self

        def start(self) -> None:
            self.start_calls += 1

        def stop(self) -> None:
            self.stop_calls += 1

    monkeypatch.setenv("REVERSE_AGENT_TASK_DB_DIR", str(tmp_path))
    monkeypatch.setattr(trusted_host_module, "CombinedTrustedHost", FakeHost)
    monkeypatch.setattr(
        trusted_host_module,
        "_resolve_trusted_authority_sha",
        lambda: "authority-test-sha",
    )
    monkeypatch.setattr(
        trusted_host_module,
        "_resolve_trusted_planning_sha",
        lambda: "planning-test-sha",
    )
    if wait_error is not None:
        def raise_from_wait(host: Any) -> None:
            raise wait_error()
        monkeypatch.setattr(
            trusted_host_module,
            "_wait_for_owned_serving_threads",
            raise_from_wait,
        )
    return captured


def test_entrypoint_has_no_second_serve_loop_and_stops_once_on_normal_return(
    tmp_path,
    monkeypatch,
) -> None:
    captured = _install_fake_entrypoint_host(monkeypatch, tmp_path)

    trusted_host_module.run_combined_trusted_host()

    host = captured["host"]
    assert host is not None
    assert host.start_calls == 1
    assert host.stop_calls == 1
    assert captured["duplicate_serve"] == 0


@pytest.mark.parametrize("wait_error", [KeyboardInterrupt, SystemExit])
def test_entrypoint_interrupts_converge_through_one_public_stop(
    tmp_path,
    monkeypatch,
    wait_error,
) -> None:
    captured = _install_fake_entrypoint_host(
        monkeypatch,
        tmp_path,
        wait_error=wait_error,
    )

    trusted_host_module.run_combined_trusted_host()

    host = captured["host"]
    assert host is not None
    assert host.start_calls == 1
    assert host.stop_calls == 1
    assert captured["duplicate_serve"] == 0


def test_partial_cleanup_shutdowns_only_started_servers_and_closes_all_created(
    tmp_path,
) -> None:
    class FakeServer:
        def __init__(self) -> None:
            self.shutdown_calls = 0
            self.close_calls = 0

        def shutdown(self) -> None:
            self.shutdown_calls += 1

        def server_close(self) -> None:
            self.close_calls += 1

    class FakeThread:
        def __init__(self) -> None:
            self.join_calls: list[float | None] = []

        def join(self, timeout: float | None = None) -> None:
            self.join_calls.append(timeout)

    class FakeAccountAuth:
        def __init__(self) -> None:
            self.close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

    class FakeRelayManager:
        def __init__(self) -> None:
            self.release_calls = 0

        def release_all(self) -> None:
            self.release_calls += 1

    host = CombinedTrustedHost(task_store=_make_store(tmp_path), vault=None, local_client_session=client_session(activate=False),)
    started = FakeServer()
    never_started = FakeServer()
    relay_never_started = FakeServer()
    thread = FakeThread()
    account_auth = FakeAccountAuth()
    relay_manager = FakeRelayManager()

    host._model_server = started
    host._task_server = never_started
    host._relay_server_inner = relay_never_started
    host._started_servers = [started]
    host._threads = [thread]
    host._account_auth = account_auth
    host._relay_manager = relay_manager
    host._coordinator = None

    host.stop()

    assert started.shutdown_calls == 1
    assert never_started.shutdown_calls == 0
    assert relay_never_started.shutdown_calls == 0
    assert started.close_calls == 1
    assert never_started.close_calls == 1
    assert relay_never_started.close_calls == 1
    assert thread.join_calls == [3.0]
    assert account_auth.close_calls == 1
    assert relay_manager.release_calls == 1


def test_real_host_stop_allows_exact_model_and_task_port_reuse(tmp_path) -> None:
    first_dir = tmp_path / "first"
    first_dir.mkdir()
    first = CombinedTrustedHost(
        task_store=_make_store(first_dir),
        vault=None,
        local_client_session=client_session(activate=False),
    )
    first.start(model_control_port=0, task_api_port=0)
    assert first._model_server is not None
    assert first._task_server is not None
    model_port = first._model_server.server_address[1]
    task_port = first._task_server.server_address[1]
    relay_port = first._relay_server_port
    first.stop()

    relay_probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        relay_probe.bind(("127.0.0.1", relay_port))
    finally:
        relay_probe.close()

    second_dir = tmp_path / "second"
    second_dir.mkdir()
    second = CombinedTrustedHost(
        task_store=_make_store(second_dir),
        vault=None,
        local_client_session=client_session(activate=False),
    )
    try:
        second.start(
            model_control_port=model_port,
            task_api_port=task_port,
        )
        assert second.model_control_url.endswith(f":{model_port}")
        assert second.task_api_url.endswith(f":{task_port}")
    finally:
        second.stop()


def test_run_combined_trusted_host_publishes_metadata_and_starts_client_before_slow_escalation_sweep(
    tmp_path,
    monkeypatch,
) -> None:
    import json
    import time
    from datetime import datetime, timedelta, timezone
    from reverse_agent.platform_v1.autonomy import AutonomyService
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    from reverse_agent.platform_v1.goal_service import GoalService
    import reverse_agent.platform_v1.trusted_client as trusted_client_module

    db_path = tmp_path / "tasks.sqlite3"
    store = TaskStore(db_path=str(db_path))
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "trusted-host-nonblocking-startup", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 5, "max_retries": 1, "confirmation": "ACTIVATE",
    })
    goal = goals.create({
        "objective": "Startup backlog goal", "repository": "dddd2024/Nerelan",
        "idempotency_key": "startup-backlog-goal", "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "failed", "instruction": "fail"}])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    store._conn.execute(
        "UPDATE tasks SET status='FAILED', failure_classification='deterministic_validation_failure' WHERE id=?",
        (task_id,),
    )
    store._conn.commit()
    store._conn.close()

    sweep_entered = threading.Event()
    allow_finish = threading.Event()
    client_started = threading.Event()
    observed: dict[str, Any] = {}

    def slow_escalate(self, goal_id: str) -> tuple:
        sweep_entered.set()
        allow_finish.wait(timeout=10.0)
        return ()

    class FakeTrustedClient:
        def __init__(self, *, node_executable: str, frontend_url: str, task_api_url: str) -> None:
            self.pid = 12345
            self.ready = True
            self.start_filetime = None
            self.executable = node_executable or "node"
            self._status_listener = None

        def start(self, session_token: str) -> None:
            assert len(session_token) == 64
            client_started.set()

        def observe_status(self, listener) -> None:
            self._status_listener = listener
            listener()

        def stop(self) -> None:
            pass

    def check_ready_and_release(host: Any) -> None:
        observed["host"] = host
        try:
            meta_file = tmp_path / "trusted_host_meta.json"
            assert meta_file.is_file()
            metadata = json.loads(meta_file.read_text(encoding="utf-8"))
            assert metadata["task_api_url"] == host.task_api_url
            assert metadata["client_process_pid"] == 12345
            assert client_started.is_set()
            assert sweep_entered.wait(timeout=5.0)
            assert not allow_finish.is_set()
            recovering_status = host._coordinator.status()
            assert recovering_status["lifecycle"] == "RECOVERING"
            assert recovering_status["recovering"] is True
            assert recovering_status["accepting_work"] is False
        finally:
            allow_finish.set()
        deadline = time.monotonic() + 5.0
        while host._coordinator.status()["recovering"] and time.monotonic() < deadline:
            time.sleep(0.02)
        assert host._coordinator.status()["recovering"] is False

    monkeypatch.setenv("REVERSE_AGENT_TASK_DB_DIR", str(tmp_path))
    monkeypatch.setenv("REVERSE_AGENT_TASK_DB_PATH", str(db_path))
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "1")
    monkeypatch.setenv("REVERSE_AGENT_TRUSTED_CLIENT_UI", "1")
    monkeypatch.setenv("REVERSE_AGENT_MODEL_CONTROL_PORT", "0")
    monkeypatch.setenv("REVERSE_AGENT_TASK_SERVICE_PORT", "0")
    for env_var in (
        "REVERSE_AGENT_CODEX_ENABLED",
        "REVERSE_AGENT_CLAUDE_CODE_ENABLED",
        "REVERSE_AGENT_MULTI_ACCOUNT_ENABLED",
        "REVERSE_AGENT_MODEL_CONTROL_LIVE",
    ):
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setattr(trusted_host_module, "default_vault_adapter", lambda: None)
    monkeypatch.setattr(trusted_host_module, "detect_agent_clis", lambda: {})
    monkeypatch.setattr(trusted_host_module, "execute_opencode_auth_list_probe", lambda: {})
    monkeypatch.setattr(trusted_host_module, "start_opencode_account_auth_server", lambda *args, **kwargs: None)
    monkeypatch.setattr(trusted_host_module, "_resolve_trusted_authority_sha", lambda: "auth-test-sha")
    monkeypatch.setattr(trusted_host_module, "_resolve_trusted_planning_sha", lambda: "plan-test-sha")
    monkeypatch.setattr(GoalService, "escalate_failed_tasks", slow_escalate)
    monkeypatch.setattr(trusted_client_module, "TrustedClient", FakeTrustedClient)
    monkeypatch.setattr(trusted_host_module, "_wait_for_owned_serving_threads", check_ready_and_release)

    try:
        trusted_host_module.run_combined_trusted_host()
    finally:
        allow_finish.set()
        host = observed.get("host")
        if host is not None:
            host._task_store._conn.close()
