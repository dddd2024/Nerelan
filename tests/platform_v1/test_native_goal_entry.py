"""Provider-free entry tests. Synthetic identity/dialog are fixtures, not consent."""
import json
import socket
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from reverse_agent.platform_v1 import native_goal_entry as entry
from reverse_agent.platform_v1 import trusted_host as trusted
from reverse_agent.platform_v1 import native_goal_admission as native
from reverse_agent.platform_v1.run_store import TaskStoreError
from _local_client_fixture import client_session, client_headers
from test_native_goal_admission import setup, unchanged  # shared persisted Goal fixture


@pytest.mark.parametrize("argv", [
    ["--native-admit-goal"], ["--native-admit-goal", ""],
    ["--native-admit-goal", " goal-1"], ["--native-admit-goal", "goal\nforged"],
    ["--native-admit-goal", "a/b"], ["--native-admit-goal", "x" * 257],
    ["--native-admit-goal", "one", "two"],
    ["--native-admit-goal", "one", "--native-admit-goal", "one"],
    ["--native-admit", "one"], ["--yes"], ["--auto-yes"], ["--test"],
])
def test_invalid_commands_before_startup(monkeypatch, argv):
    monkeypatch.setattr(trusted, "run_combined_trusted_host",
                        lambda **kw: pytest.fail("host startup reached"))
    with pytest.raises(SystemExit) as error:
        entry.main(argv)
    assert error.value.code == 2


def test_no_command_uses_unchanged_startup(monkeypatch):
    calls = []
    monkeypatch.setattr(trusted, "run_combined_trusted_host", lambda **kw: calls.append(kw))
    entry.main([])
    assert calls == [{}]


def install_host(monkeypatch, tmp_path, host):
    """Use the real official host with ephemeral ports and no provider probes."""
    monkeypatch.delenv("REVERSE_AGENT_AUTONOMOUS", raising=False)
    monkeypatch.delenv("REVERSE_AGENT_TRUSTED_CLIENT_UI", raising=False)
    monkeypatch.delenv("REVERSE_AGENT_CODEX_ENABLED", raising=False)
    monkeypatch.delenv("REVERSE_AGENT_CLAUDE_CODE_ENABLED", raising=False)
    monkeypatch.setenv("REVERSE_AGENT_TASK_DB_DIR", str(tmp_path))
    monkeypatch.setattr(trusted, "_resolve_trusted_authority_sha", lambda: "")
    monkeypatch.setattr(trusted, "_resolve_trusted_planning_sha", lambda: "")
    host._model_control_port = host._task_api_port = 0
    host._local_client_session = client_session(activate=False)
    monkeypatch.setattr(trusted, "CombinedTrustedHost", lambda **kw: host)
    monkeypatch.setattr(trusted, "_wait_for_owned_serving_threads", lambda host: None)
    stopped = []
    stop = host.stop
    def tracked_stop():
        stopped.append(True)
        stop()
    monkeypatch.setattr(host, "stop", tracked_stop)
    return stopped


def test_explicit_command_exact_persisted_goal_and_no_http_authority(setup, monkeypatch, tmp_path):
    host, goal, seen = setup
    other = host._goal_service.create({"objective": "Untouched", "repository": "owner/repo",
        "idempotency_key": "two", "executor_kind": "codex", "binding_ref": "pinned",
        "orchestration_mode": "single"})
    stopped = install_host(monkeypatch, tmp_path, host)
    def inspect(running):
        assert running is host and host._started_servers
        assert host._control_store.get_goal(goal.id).status == "RUNNING"
        assert host._control_store.get_goal(other.id) == other
        links = host._control_store.list_goal_tasks(goal.id)
        assert len(links) == 1 and links[0]["status"] == "QUEUED"
        for route in ("/native-admit-goal", f"/goals/{goal.id}/native-admit",
                      "/_native_owner_admit_goal"):
            request = Request(host.task_api_url + route, data=b"{}", method="POST",
                              headers=client_headers({"Content-Type": "application/json"}))
            with pytest.raises(HTTPError) as error:
                urlopen(request, timeout=3)
            assert error.value.code == 404
    monkeypatch.setattr(trusted, "_wait_for_owned_serving_threads", inspect)
    entry.main(["--native-admit-goal", goal.id])
    assert len(seen) == 1 and goal.id in seen[0]
    assert stopped == [True] and host._started_servers == []
    metadata = json.loads((tmp_path / "trusted_host_meta.json").read_text())
    assert "nonce" not in metadata and "consent" not in metadata


def test_real_occupied_port_never_prompts_or_attaches(setup, monkeypatch, tmp_path):
    host, goal, seen = setup
    stopped = install_host(monkeypatch, tmp_path, host)
    with socket.socket() as owner:
        owner.bind(("127.0.0.1", 0))
        owner.listen()
        host._model_control_port = owner.getsockname()[1]
        with pytest.raises(OSError):
            entry.main(["--native-admit-goal", goal.id])
        assert owner.getsockname()[1] == host._model_control_port
    assert not seen and stopped == [True]
    unchanged(host, goal)


def test_no_command_real_host_never_requests_consent(setup, monkeypatch, tmp_path):
    host, goal, seen = setup
    stopped = install_host(monkeypatch, tmp_path, host)
    entry.main([])
    assert not seen and stopped == [True]
    unchanged(host, goal)


@pytest.mark.parametrize("mode", ["refusal", "expiry", "dialog_error", "old_claim"])
def test_native_failure_stays_closed_through_entry(setup, monkeypatch, tmp_path, mode):
    host, goal, _ = setup
    stopped = install_host(monkeypatch, tmp_path, host)
    monkeypatch.setattr(trusted, "_wait_for_owned_serving_threads",
                        lambda _: pytest.fail("failed admission reached wait"))
    now = [100.0]
    monkeypatch.setattr(native.time, "monotonic", lambda: now[0])
    def dialog(_):
        if mode == "old_claim":
            pytest.fail("old claim prompted")
        if mode == "dialog_error":
            raise OSError("fixture dialog unavailable")
        if mode == "expiry":
            now[0] += 31
            return True
        return False
    monkeypatch.setattr(native.native_owner_dialog, "confirm_admission", dialog)
    previous = None
    if mode == "old_claim":
        old = host._task_store.create_task(title="Held", executor_kind="deterministic_fixture")
        host._task_store._conn.execute(
            "INSERT INTO platform_coordinator_claims VALUES (?, 'old-window', 'old-owner', "
            "1, 1, 'ACTIVE', 'old', 'old')", (old.id,))
        previous = tuple(host._task_store._conn.execute(
            "SELECT * FROM platform_coordinator_claims").fetchone())
    with pytest.raises((TaskStoreError, OSError)):
        entry.main(["--native-admit-goal", goal.id])
    assert stopped == [True] and not host._started_servers
    if previous is None:
        unchanged(host, goal)
    else:
        assert tuple(host._task_store._conn.execute(
            "SELECT * FROM platform_coordinator_claims").fetchone()) == previous
        assert host._control_store.get_goal(goal.id) == goal
        assert host._control_store.list_windows() == ()
        assert host._task_store.get_task(old.id) == old
    assert host._task_store._conn.execute(
        "SELECT COUNT(*) FROM platform_operation_receipts").fetchone()[0] == 0


@pytest.mark.parametrize("point,error", [
    ("start", OSError), ("admit", RuntimeError), ("wait", RuntimeError),
    ("wait", KeyboardInterrupt), ("admit", KeyboardInterrupt),
])
def test_lifecycle_cleanup_and_no_attach(monkeypatch, tmp_path, point, error):
    events = []
    class Host:
        model_control_url = task_api_url = relay_url = "fixture"
        def start(self):
            events.append("start")
            if point == "start":
                raise error("port already owned")
        def _native_owner_admit_goal(self, goal_id):
            events.append(goal_id)
            if point == "admit":
                raise error("fixture")
        def stop(self):
            events.append("stop")
    monkeypatch.setattr(trusted, "CombinedTrustedHost", lambda **kw: Host())
    monkeypatch.delenv("REVERSE_AGENT_TRUSTED_CLIENT_UI", raising=False)
    monkeypatch.setenv("REVERSE_AGENT_TASK_DB_DIR", str(tmp_path))
    monkeypatch.setattr(trusted, "_resolve_trusted_authority_sha", lambda: "")
    monkeypatch.setattr(trusted, "_resolve_trusted_planning_sha", lambda: "")
    def wait(_):
        events.append("wait")
        raise error("fixture")
    monkeypatch.setattr(trusted, "_wait_for_owned_serving_threads", wait)
    if error is KeyboardInterrupt:
        entry.main(["--native-admit-goal", "goal-exact"])
    else:
        with pytest.raises(error):
            entry.main(["--native-admit-goal", "goal-exact"])
    assert events == (["start", "stop"] if point == "start" else
                      ["start", "goal-exact", "stop"] if point == "admit" else
                      ["start", "goal-exact", "wait", "stop"])
