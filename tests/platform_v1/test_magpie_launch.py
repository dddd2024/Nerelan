"""Provider-free Magpie launch acceptance with injected probes/process operations."""
import json
from unittest.mock import Mock

import pytest

from reverse_agent.model_access.store import ModelProfileStore, StoreError
from reverse_agent.platform_v1.magpie_launch import MagpieLaunch
from reverse_agent.model_access.magpie import DEFAULT_MAGPIE, validate_settings


@pytest.fixture(autouse=True)
def forbid_live_io(monkeypatch):
    import reverse_agent.platform_v1.magpie_launch as magpie_launch_module
    import subprocess

    def forbidden(*args, **kwargs):
        pytest.fail("test attempted live network or process launch")
    monkeypatch.setattr(magpie_launch_module, "urlopen", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)


@pytest.fixture
def config(tmp_path):
    exe = tmp_path / "magpie.exe"
    exe.write_bytes(b"fixture only; never executable")
    return {"enabled": True, "executable": str(exe), "base_url": DEFAULT_MAGPIE["base_url"]}


class Clock:
    def __init__(self):
        self.now = 0.0
    def __call__(self):
        return self.now
    def sleep(self, seconds):
        self.now += seconds


def manager(config, results=None, *, running=False, launch_error=None):
    clock = Clock()
    probe = Mock(side_effect=results or [OSError("down")] * 200)
    launch = Mock(side_effect=launch_error)
    active = Mock(return_value=running)
    instance = MagpieLaunch(lambda: dict(config), probe=probe, launcher=launch,
                            running=active, clock=clock, sleep=clock.sleep)
    return instance, probe, launch, active, clock


def test_disabled_has_no_probe_inspection_or_launch(config):
    config["enabled"] = False
    instance, probe, launch, running, _ = manager(config)
    instance.check()
    assert instance.status() == {"status": "MAGPIE_DISABLED", "reason": "", "last_probe_at": None, "model_count": 0}
    probe.assert_not_called()
    running.assert_not_called()
    launch.assert_not_called()


def test_already_running(config):
    instance, probe, launch, running, _ = manager(config, [4])
    instance.check()
    assert instance.status()["status"] == "ALREADY_RUNNING"
    assert instance.status()["model_count"] == 4
    assert instance.status()["last_probe_at"]
    probe.assert_called_once_with(config["base_url"], 2.0)
    launch.assert_not_called()
    running.assert_not_called()


def test_down_launches_once_then_started(config):
    instance, _, launch, _, _ = manager(config, [OSError(), OSError(), 5, 5])
    instance.check()
    assert instance.status()["status"] == "STARTED"
    assert instance.status()["model_count"] == 5
    instance.check()
    launch.assert_called_once_with(config["executable"])


@pytest.mark.parametrize("error", [PermissionError(), OSError()])
def test_launch_failure_is_bounded(config, error):
    instance, _, launch, _, _ = manager(config, launch_error=error)
    instance.check()
    assert instance.status()["status"] == "START_FAILED"
    assert instance.status()["reason"] == type(error).__name__
    launch.assert_called_once()


def test_never_healthy_times_out(config):
    instance, probe, launch, _, clock = manager(config)
    instance.check()
    assert instance.status()["status"] == "START_FAILED"
    assert instance.status()["reason"] == "health_timeout"
    assert instance.status()["model_count"] == 0
    assert clock.now == 30
    assert all(call.args[1] <= 2 for call in probe.call_args_list)
    launch.assert_called_once()


def test_existing_process_dead_port_never_duplicates(config):
    instance, _, launch, _, _ = manager(config, running=True)
    for _ in range(5):
        instance.check()
    assert instance.status()["status"] == "UNREACHABLE"
    assert instance.status()["reason"] == "process_running_but_unreachable"
    launch.assert_not_called()


def test_process_inspection_failure_never_launches(config):
    instance, _, launch, running, _ = manager(config)
    running.side_effect = OSError("inspection unavailable")
    instance.check()
    assert instance.status()["status"] == "START_FAILED"
    launch.assert_not_called()


def test_restart_budget_is_three_attempts_per_rolling_hour(config):
    instance, probe, launch, _, clock = manager(config, [2])
    instance.check()
    probe.side_effect = None
    probe.return_value = 2
    # Each watch sees a stopped gateway followed by a successful restart.
    for _ in range(3):
        probe.side_effect = [OSError(), 2]
        clock.now += 60
        instance.check()
        assert instance.status()["status"] == "STARTED"
    probe.side_effect = [OSError()]
    clock.now += 60
    instance.check()
    assert launch.call_count == 3
    assert instance.status()["status"] == "UNREACHABLE"
    assert "3 restarts per hour" in instance.status()["reason"]
    # Budget exhaustion does not suppress health observation/recovery.
    probe.side_effect = [7]
    instance.check()
    assert instance.status()["status"] == "ALREADY_RUNNING"
    clock.now = 3660
    probe.side_effect = [OSError(), 3]
    instance.check()
    assert launch.call_count == 4


def test_initial_launch_is_separate_from_restart_budget(config):
    instance, probe, launch, _, _ = manager(config, [OSError(), 1])
    instance.check()
    for _ in range(4):
        probe.side_effect = [OSError(), 1]
        instance.check()
    assert launch.call_count == 4  # initial start plus three restarts
    assert instance.status()["status"] == "UNREACHABLE"


@pytest.mark.parametrize("field,value", [
    ("executable", "relative.exe"), ("executable", "C:relative.exe"),
    ("executable", "missing.exe"), ("base_url", "http://example.com:3425"),
    ("base_url", "http://127.0.0.1.evil.test:3425"),
    ("base_url", "http://user:password@127.0.0.1:3425"),
    ("base_url", "http://127.0.0.1:3425/path"),
    ("base_url", "http://127.0.0.1:70000"),
    ("base_url", "file:///tmp/magpie"), ("enabled", "true"),
])
def test_rejects_invalid_settings(config, field, value):
    with pytest.raises(ValueError):
        validate_settings({**config, field: value})


def test_rejects_existing_non_exe_and_missing_absolute_path(config, tmp_path):
    other = tmp_path / "magpie.cmd"
    other.touch()
    for path in (other, tmp_path / "missing.exe", tmp_path):
        with pytest.raises(ValueError):
            validate_settings({**config, "executable": str(path)})


@pytest.mark.parametrize("url", ["http://127.0.0.1:3425", "http://localhost:3425", "http://[::1]:3425", "https://localhost"])
def test_accepts_loopback_origins(config, url):
    assert validate_settings({**config, "base_url": url})["base_url"] == url


def test_persistence_and_missing_executable_do_not_block_state_load(config, tmp_path):
    state_path = tmp_path / "model_setup_state.json"
    store = ModelProfileStore(state_path=state_path)
    assert store.get_magpie() == DEFAULT_MAGPIE
    store.put_magpie(config)
    document = json.loads(state_path.read_text())
    assert document["magpie"] == config
    # Executable disappearance is a runtime failure, not corrupt model metadata.
    from pathlib import Path
    Path(config["executable"]).unlink()
    loaded = ModelProfileStore(state_path=state_path)
    assert loaded.get_magpie() == config
    instance, _, launch, _, _ = manager(loaded.get_magpie())
    instance.check()
    launch.assert_not_called()
    assert instance.status()["status"] == "START_FAILED"


def test_persistence_failure_rolls_back(config, tmp_path, monkeypatch):
    import reverse_agent.model_access.store as store_module

    store = ModelProfileStore(state_path=tmp_path / "state.json")
    monkeypatch.setattr(store_module, "_write_atomic", Mock(side_effect=OSError()))
    with pytest.raises(StoreError):
        store.put_magpie(config)
    assert store.get_magpie() == DEFAULT_MAGPIE


def test_legacy_state_defaults_disabled(tmp_path):
    state_path = tmp_path / "state.json"
    state_path.write_text('{"schema_version":2,"connections":[],"bindings":[]}')
    assert ModelProfileStore(state_path=state_path).get_magpie() == DEFAULT_MAGPIE


def test_settings_routes_and_automatic_observation(config, monkeypatch):
    import reverse_agent.model_access.service as service_module
    from reverse_agent.model_access.service import _handler_factory
    store = ModelProfileStore()
    handler_type = _handler_factory(store, live_enabled=False, allowed_origin="http://localhost")
    handler = object.__new__(handler_type)
    handler._check_origin = lambda: True
    sent = Mock()
    handler._send_json = sent
    handler._segments = lambda: ["api", "magpie"]
    handler._read_json = lambda: config
    handler.do_PUT()
    assert sent.call_args.args[1] == config
    handler.do_GET()
    assert sent.call_args.args[1]["settings"] == config
    snapshot = Mock(return_value={"status": "available", "models": [], "accounts": []})
    monkeypatch.setattr(service_module, "fetch_magpie_snapshot", snapshot)
    monkeypatch.delenv("REVERSE_AGENT_MAGPIE", raising=False)
    handler._segments = lambda: ["api", "resources"]
    handler.path = "/api/resources"
    handler.do_GET()
    snapshot.assert_called_once_with(config["base_url"])


@pytest.mark.parametrize("launch_error,reason", [(OSError(), "OSError"), (None, "health_timeout")])
def test_status_route_fields_and_failed_launch_host_still_starts(config, tmp_path, monkeypatch, launch_error, reason):
    import reverse_agent.platform_v1.trusted_host as trusted_host_module
    import reverse_agent.model_access.credential_relay as credential_relay_module
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    from reverse_agent.platform_v1.run_store import TaskStore
    class Server:
        def __init__(self, address=("127.0.0.1", 8765), handler=None):
            self.server_address = address
            self.RequestHandlerClass = handler
        def serve_forever(self): pass
        def shutdown(self): pass
        def server_close(self): pass
    monkeypatch.setattr(trusted_host_module, "ThreadingHTTPServer", Server)
    monkeypatch.setattr(credential_relay_module, "run_credential_relay_server", lambda **kw: Server())
    store = ModelProfileStore()
    store.put_magpie(config)
    instance, _, launch, _, _ = manager(config, launch_error=launch_error)
    task_store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    host = CombinedTrustedHost(store=store, task_store=task_store, auth_list_probe=lambda: {},
                               magpie_factory=lambda settings: instance)
    try:
        host.start(coordinator_paused=True)
        assert host.task_api_url
        handler = object.__new__(host._task_server.RequestHandlerClass)
        handler._check_origin = lambda: True
        handler._check_local_client = lambda: True
        handler.path = "/api/platform/status"
        handler._segments = lambda: ["api", "platform", "status"]
        handler._send_json = Mock()
        handler.do_GET()
        status = handler._send_json.call_args.args[1]["magpie"]
        assert status["status"] == "START_FAILED"
        assert status["last_probe_at"]
        assert status["model_count"] == 0
        assert status["reason"] == reason
        launch.assert_called_once()
    finally:
        host.stop()
        task_store._conn.close()
    assert not instance._thread.is_alive()
    launch.assert_called_once()


def test_magpie_bindings_not_runnable_when_gateway_unreachable(config):
    from reverse_agent.model_access.resources import build_resource_view
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    from reverse_agent.platform_v1.binding_resolver import BindingResolutionError
    from reverse_agent.platform_v1.run_store import TaskStore
    store = ModelProfileStore()
    store.put_magpie(config)
    store.upsert_connection({"connection_id": "gateway", "name": "Magpie", "provider": "openai",
                             "base_url": config["base_url"] + "/v1", "auth_method": "api_key", "api_key": "fixture"})
    store.upsert_binding({"binding_id": "gateway-model", "name": "Model", "executor_id": "opencode",
                          "connection_id": "gateway", "model_id": "model"})
    instance, _, _, _, _ = manager(config, running=True)
    instance.check()
    task_store = TaskStore(db_path=":memory:")
    host = CombinedTrustedHost(store=store, task_store=task_store, magpie_factory=lambda settings: instance)
    try:
        view = build_resource_view(store, lambda: {})
        assert view["summary"]["usable_bindings"] == 0
        with pytest.raises(BindingResolutionError, match="magpie_unreachable"):
            host._binding_resolver_factory("http://127.0.0.1:8765").resolve("gateway-model", task_executor="opencode")
        instance._status.update(status="STARTED")
        assert build_resource_view(store, lambda: {})["summary"]["usable_bindings"] == 1
    finally:
        task_store._conn.close()


def test_probe_adapter_uses_models_get_and_two_second_timeout(monkeypatch):
    import reverse_agent.platform_v1.magpie_launch as magpie_launch_module
    from reverse_agent.platform_v1.magpie_launch import probe_models
    response = Mock()
    response.status = 200
    response.read.return_value = b'{"data":[{"id":"first"},{"id":"second"}]}'
    opened = Mock()
    opened.__enter__ = Mock(return_value=response)
    opened.__exit__ = Mock(return_value=False)
    opener = Mock(return_value=opened)
    monkeypatch.setattr(magpie_launch_module, "urlopen", opener)
    assert probe_models("http://127.0.0.1:3425") == 2
    assert opener.call_args.args[0].full_url == "http://127.0.0.1:3425/v1/models"
    assert opener.call_args.args[0].get_method() == "GET"
    assert opener.call_args.args[0].get_header("Authorization") == "Bearer magpie-nerelan"
    assert opener.call_args.kwargs["timeout"] == 2
    response.read.return_value = b'{"data":"not a model list"}'
    with pytest.raises(ValueError):
        probe_models("http://127.0.0.1:3425")


def test_launcher_adapter_detaches_without_arguments_or_shell(config, monkeypatch):
    from reverse_agent.platform_v1.magpie_launch import launch_process
    import subprocess
    launched = Mock()
    monkeypatch.setattr(subprocess, "Popen", launched)
    # Constants exist only on Windows; keep this unit test portable.
    monkeypatch.setattr(subprocess, "DETACHED_PROCESS", 8, raising=False)
    monkeypatch.setattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 512, raising=False)
    launch_process(config["executable"])
    args, kwargs = launched.call_args
    assert args == ([config["executable"]],)
    assert kwargs == {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
                      "stderr": subprocess.DEVNULL, "close_fds": True, "creationflags": 520}


def test_watcher_checks_every_sixty_seconds_and_stop_only_stops_watcher(config, monkeypatch):
    import reverse_agent.platform_v1.magpie_launch as magpie_launch_module

    instance, probe, launch, _, _ = manager(config, [1, 1, 1])
    event = Mock()
    event.wait.side_effect = [False, False, True]
    instance._stop = event
    class Thread:
        def __init__(self, *, target, **kwargs):
            self.target = target
        def start(self):
            self.target()
        def join(self, **kwargs): pass
    monkeypatch.setattr(magpie_launch_module.threading, "Thread", Thread)
    instance.start()
    assert probe.call_count == 3
    assert [call.args for call in event.wait.call_args_list] == [(60,), (60,), (60,)]
    instance.stop()
    event.set.assert_called_once()
    launch.assert_not_called()


def test_disabled_setting_preserves_manual_gateway_binding_behavior():
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "manual", "name": "Manual gateway", "provider": "openai",
                             "base_url": "http://127.0.0.1:3425/v1", "auth_method": "api_key", "api_key": "fixture"})
    assert store.magpie_connection_runnable("manual")


def test_failed_restarts_consume_budget(config):
    instance, _, launch, _, _ = manager(config, launch_error=OSError())
    for _ in range(5):
        instance.check()
    assert launch.call_count == 4  # one initial attempt, three restart attempts
    assert instance.status()["status"] == "UNREACHABLE"
    assert "restart_budget_exhausted" in instance.status()["reason"]
