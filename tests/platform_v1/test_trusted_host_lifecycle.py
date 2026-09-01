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

    host = CombinedTrustedHost(task_store=_make_store(tmp_path), vault=None)
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
