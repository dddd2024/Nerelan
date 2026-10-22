"""Provider-free broker tests: no SSH, network or experiment execution."""

from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time

from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import remote_jobs, trusted_host
from reverse_agent.platform_v1.remote_jobs import (
    REMOTE_COMMAND,
    REMOTE_HELPER,
    RemoteJobBroker,
    RemoteJobProfile,
    SSHTransport,
    _remote_program,
    configured_broker,
    main,
)


def _program_request(program: str) -> dict:
    """Extract the request JSON the broker hands the helper through sys.argv."""
    lines = program.splitlines()
    assert lines[0] == "import sys as _sys"
    prefix = "_sys.argv = ['-', "
    assert lines[1].startswith(prefix), lines[1][:60]
    assert lines[1].endswith("]")
    return json.loads(json.loads(lines[1][len(prefix):-1]))


class FakeTransport:
    """Run the fixed helper against a fake home and fake OS processes."""
    def __init__(self, home, monkeypatch):
        self.home = home
        home.mkdir()
        self.monkeypatch = monkeypatch
        self.launches = []
        self.calls = []
        self.killed = []
        self.alive = True
        self.fail = None
        self.fail_after_launch = False
        self.start_time = 123
        self.boot_id = "fake-boot"
        self.deny_signal = False
        self.ignore_term = True
        self.ignore_kill = False
        self.leader_alive = True
        self.deny_on_signal = None

    def run(self, argv, timeout, stdin_text=None):
        assert argv[:6] == ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "lab"]
        assert argv[6:] == ["python3", "-"]
        assert stdin_text is not None
        program = stdin_text
        data = _program_request(program)
        self.calls.append(data)
        if self.fail == data["op"]:
            self.fail = None
            return 255, "", "fake disconnected"
        output = io.StringIO()
        previous = Path.cwd()
        def spawn(args, **kwargs):
            self.alive = True
            self.launches.append((args, kwargs["env"]["CUDA_VISIBLE_DEVICES"], Path.cwd()))
            return SimpleNamespace(pid=4321)
        def kill(pid, sig):
            assert pid == 4321 and sig == 0
            if not self.alive:
                raise ProcessLookupError()
        read_text = Path.read_text
        iterdir = Path.iterdir
        def read(path, *args, **kwargs):
            if path.as_posix() == "/proc/sys/kernel/random/boot_id":
                return self.boot_id
            if path.as_posix() in {"/proc/4321/stat", "/proc/4322/stat"}:
                if not self.alive or (path.parent.name == "4321" and not self.leader_alive):
                    raise FileNotFoundError()
                return "4321 (fake (worker)) S 1 4321 4321 " + "0 " * 15 + str(self.start_time)
            return read_text(path, *args, **kwargs)
        def killpg(pid, sig):
            assert pid == 4321
            if self.deny_signal or self.deny_on_signal == sig:
                raise PermissionError("fake permission denied")
            if not self.alive:
                raise ProcessLookupError()
            if sig:
                self.killed.append((pid, sig))
                if (sig == signal.SIGKILL and not self.ignore_kill) or (sig == signal.SIGTERM and not self.ignore_term):
                    self.alive = False
        try:
            with self.monkeypatch.context() as patch, redirect_stdout(output):
                patch.setattr(Path, "home", classmethod(lambda cls: self.home))
                patch.setattr(subprocess, "Popen", spawn)
                patch.setattr(os, "kill", kill)
                patch.setattr(os, "killpg", killpg, raising=False)
                patch.setattr(signal, "SIGKILL", 9, raising=False)
                patch.setattr(Path, "read_text", read)
                patch.setattr(Path, "iterdir", lambda path: iter([Path("/proc/4321"), Path("/proc/4322")]) if path.as_posix() == "/proc" else iterdir(path))
                exec(compile(program, "<fixed-remote-helper>", "exec"), {})
        except SystemExit as exc:
            if exc.code:
                return 1, "", str(exc)
        except Exception as exc:
            return 1, "", str(exc)
        finally:
            os.chdir(previous)
        if data["op"] == "launch" and self.fail_after_launch:
            self.fail_after_launch = False
            return 255, "", "fake lost launch response"
        return 0, output.getvalue(), ""

    def upload(self, local_dir, remote_dir):
        if self.fail == "upload":
            self.fail = None
            raise OSError("fake upload failure")
        shutil.copytree(local_dir, self.home / remote_dir, dirs_exist_ok=True)

    def download(self, remote_path, local_path):
        if self.fail == "download":
            self.fail = None
            raise OSError("fake download failure")
        shutil.copyfile(self.home / remote_path, local_path)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    profile = RemoteJobProfile("lab", "wjc/jobs", tmp_path / "receipts", (tmp_path / "ws",),
                               max_wall_seconds=100, poll_seconds=1, max_upload_bytes=1024,
                               max_download_bytes=2048)
    transport = FakeTransport(tmp_path / "home", monkeypatch)
    now = [1000.0]
    broker = RemoteJobBroker(profile, transport, lambda: now[0])
    return broker, transport, now


def request(broker, job_id="e001-baseline", **changes):
    directory = broker.profile.scan_roots[0] / "task" / ".nerelan-remote/outbox" / job_id
    directory.mkdir(parents=True, exist_ok=True)
    data = {"job_id": job_id, "command": "python run.py --seed 0", "files": ["run.py"],
            "outputs": ["results/*.json", "metrics.csv"], "max_wall_seconds": 10,
            "gpu": True, "purpose": "baseline"}
    data.update(changes)
    (directory / "run.py").write_text("print('fixture')", encoding="utf-8")
    (directory / "job.json").write_text(json.dumps(data), encoding="utf-8")
    return directory


def receipt(broker, job_id="e001-baseline"):
    return next(r for r in broker.receipts() if r["job_id"] == job_id)


def remote(transport, job_id="e001-baseline"):
    return transport.home / "wjc/jobs" / job_id


def test_full_lifecycle_and_manifest(setup):
    broker, transport, now = setup
    source = request(broker)
    broker.tick()
    assert receipt(broker)["state"] == "RUNNING"
    job = remote(transport)
    (job / "results").mkdir()
    (job / "results/a.json").write_bytes(b'{"score": 42}')
    (job / "metrics.csv").write_bytes(b"seed,score\n0,42\n")
    (job / "stdout.log").write_bytes(b"x" * (1024 * 1024 + 20))
    (job / "exit_code").write_text("0")
    (source / "run.py").write_text("changed after launch")
    broker.tick()
    result = receipt(broker)
    assert [e["state"] for e in result["history"] if not e["detail"]] == [
        "PREPARED", "UPLOADED", "LAUNCHED", "RUNNING", "SUCCEEDED"]
    assert result["state"] == "RESULT_COLLECTED" and result["outcome"] == "SUCCEEDED", result["history"]
    local = broker.profile.local_root / result["job_id"]
    manifest = json.loads((local / "manifest.json").read_text())
    assert manifest["request_digest"] == result["request_digest"]
    assert {f["path"] for f in manifest["files"]} == {
        "outputs/results/a.json", "outputs/metrics.csv", "stdout.log", "stderr.log"}
    for entry in manifest["files"]:
        content = (local / entry["path"]).read_bytes()
        assert entry["sha256"] == hashlib.sha256(content).hexdigest()
        assert entry["size"] == len(content)
    assert (local / "stdout.log").stat().st_size == 1024 * 1024
    assert (local / "request/run.py").read_text() == "print('fixture')"


@pytest.mark.parametrize("changes,reason", [
    ({"job_id": "BAD"}, "job_id"),
    ({"files": ["../run.py"]}, "relative"),
    ({"files": ["/run.py"]}, "relative"),
    ({"files": ["C:/run.py"]}, "relative"),
    ({"outputs": ["../*.json"]}, "relative"),
    ({"outputs": ["/tmp/*"]}, "relative"),
    ({"unknown": 1}, "unknown"),
    ({"max_wall_seconds": 101}, "profile limit"),
    ({"max_wall_seconds": True}, "positive integer"),
    ({"command": ""}, "command"),
    ({"gpu": "true"}, "gpu"),
    ({"files": ["launch.json"]}, "reserved"),
])
def test_invalid_requests_rejected(setup, changes, reason):
    broker, transport, _ = setup
    request(broker, **changes)
    broker.tick()
    result = broker.receipts()[0]
    assert result["state"] == "REJECTED"
    assert reason in result["history"][-1]["detail"]
    assert transport.calls == []


def test_bad_directory_id_has_safe_rejected_receipt(setup):
    broker, transport, _ = setup
    request(broker, "BAD")
    broker.tick()
    assert broker.receipts()[0]["state"] == "REJECTED"
    assert broker.receipts()[0]["job_id"].startswith("rejected-")


def test_oversized_file_rejected(setup):
    broker, _, _ = setup
    directory = request(broker)
    (directory / "run.py").write_bytes(b"x" * 1025)
    broker.tick()
    assert "max_upload_bytes" in receipt(broker)["history"][-1]["detail"]


def test_symlink_file_rejected(setup, tmp_path):
    broker, _, _ = setup
    directory = request(broker, files=["link"])
    target = tmp_path / "outside"
    target.write_text("outside")
    try:
        (directory / "link").symlink_to(target)
    except OSError:
        pytest.skip("OS does not permit creating symlinks")
    broker.tick()
    assert "symlink" in receipt(broker)["history"][-1]["detail"]


def test_symlink_validation_without_os_symlink_privilege(setup, monkeypatch):
    broker, transport, _ = setup
    directory = request(broker)
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == directory / "run.py" or original(path))
    broker.tick()
    assert receipt(broker)["state"] == "REJECTED"
    assert "symlink" in receipt(broker)["history"][-1]["detail"]
    assert transport.calls == []


def test_duplicate_and_changed_id_never_relaunch(setup):
    broker, transport, _ = setup
    directory = request(broker)
    broker.tick()
    broker.tick()
    request(broker, command="echo changed")
    broker.tick()
    broker.tick()
    assert len(transport.launches) == 1
    assert sum(e["detail"] == "DUPLICATE_ID_CHANGED_REQUEST" for e in receipt(broker)["history"]) == 1
    assert json.loads((broker.profile.local_root / "e001-baseline/request/job.json").read_text())["command"] != "echo changed"


def test_duplicate_ids_across_worktrees_do_not_repeat_events(setup):
    broker, transport, _ = setup
    source = request(broker)
    other = broker.profile.scan_roots[0] / "other" / ".nerelan-remote/outbox/e001-baseline"
    shutil.copytree(source, other)
    broker.tick()
    data = json.loads((other / "job.json").read_text())
    data["command"] = "echo another request"
    (other / "job.json").write_text(json.dumps(data))
    broker.tick()
    broker.tick()
    assert len(transport.launches) == 1
    assert sum(e["detail"] == "DUPLICATE_ID_CHANGED_REQUEST" for e in receipt(broker)["history"]) == 1


@pytest.mark.parametrize("state", ["LAUNCHED", "RUNNING"])
def test_restart_polls_without_launch(setup, state):
    broker, transport, now = setup
    request(broker)
    broker.tick()
    saved = receipt(broker)
    broker._event(saved, state, "restart fixture")
    transport.calls.clear()
    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    assert [c["op"] for c in transport.calls] == ["poll"]
    assert len(transport.launches) == 1


@pytest.mark.parametrize("alive,expected", [(True, "RUNNING"), (False, "RESULT_COLLECTED")])
def test_remote_marker_without_local_receipt(setup, alive, expected):
    broker, transport, _ = setup
    request(broker)
    job = remote(transport)
    job.mkdir(parents=True)
    (job / "launch.json").write_text(json.dumps({"launched_at": 1000, "pid": 4321, "start_time": 123, "boot_id": "fake-boot"}))
    (job / "pid").write_text("4321")
    transport.alive = alive
    broker.tick()
    assert receipt(broker)["state"] == expected
    assert transport.launches == []
    assert all(c["op"] != "launch" for c in transport.calls)
    if not alive:
        assert receipt(broker)["outcome"] == "LOST"


@pytest.mark.parametrize("operation,expected", [("upload", "PREPARED"), ("launch", "UPLOADED"), ("poll", "LAUNCHED")])
def test_transport_failure_preserves_state_and_retries(setup, operation, expected):
    broker, transport, now = setup
    request(broker)
    transport.fail = operation
    broker.tick()
    result = receipt(broker)
    assert result["state"] == expected
    assert "error" in result["history"][-1]["detail"]
    calls = len(transport.calls)
    broker.tick()
    assert len(transport.calls) == calls  # backoff
    now[0] += 601
    broker.tick()
    assert len(transport.launches) == 1


def test_launch_response_lost_then_restart_is_idempotent(setup):
    broker, transport, now = setup
    request(broker)
    transport.fail_after_launch = True
    broker.tick()
    assert receipt(broker)["state"] == "UPLOADED"
    assert len(transport.launches) == 1
    now[0] += 3
    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    assert receipt(broker)["state"] == "RUNNING"
    assert len(transport.launches) == 1


def test_incomplete_remote_reservation_is_lost_without_launch(setup):
    broker, transport, _ = setup
    request(broker)
    job = remote(transport)
    job.mkdir(parents=True)
    (job / "launch.json").write_text('{"job_id":')
    broker.tick()
    assert receipt(broker)["outcome"] == "LOST"
    assert receipt(broker)["state"] == "RESULT_COLLECTED"
    assert transport.launches == []


def test_download_failure_resumes_frozen_results_after_restart(setup):
    broker, transport, now = setup
    request(broker)
    broker.tick()
    (remote(transport) / "metrics.csv").write_bytes(b"original result")
    (remote(transport) / "exit_code").write_text("0")
    transport.fail = "download"
    broker.tick()
    assert receipt(broker)["state"] == "SUCCEEDED"
    (remote(transport) / "metrics.csv").write_bytes(b"modified after snapshot")
    now[0] += 3
    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    assert receipt(broker)["state"] == "RESULT_COLLECTED"
    assert (broker.profile.local_root / "e001-baseline/outputs/metrics.csv").read_bytes() == b"original result"
    assert len(transport.launches) == 1


def test_remote_digest_mismatch_is_preserved_as_evidence(setup):
    broker, transport, _ = setup
    request(broker)
    job = remote(transport)
    job.mkdir(parents=True)
    (job / "launch.json").write_text(json.dumps({"launched_at": 1000, "request_digest": "another-request", "pid": 4321, "start_time": 123, "boot_id": "fake-boot"}))
    (job / "exit_code").write_text("0")
    broker.tick()
    result = receipt(broker)
    assert result["remote_request_digest"] == "another-request"
    manifest = json.loads((broker.profile.local_root / "e001-baseline/manifest.json").read_text())
    assert manifest["remote_request_digest"] == "another-request"
    assert any("different request digest" in e["detail"] for e in result["history"])
    assert transport.launches == []


def test_unfinished_local_snapshot_is_not_reused(setup):
    broker, transport, _ = setup
    request(broker)
    frozen = broker.profile.local_root / "e001-baseline/request"
    frozen.mkdir(parents=True)
    (frozen / "unexpected.py").write_text("old partial snapshot")
    broker.tick()
    assert receipt(broker)["state"] == "REJECTED"
    assert "incomplete local preparation" in receipt(broker)["history"][-1]["detail"]
    assert transport.launches == []


def test_daemon_stops_without_transport_calls(setup):
    broker, transport, _ = setup
    broker.start()
    broker.stop()
    assert not broker._thread.is_alive()
    assert transport.calls == []


def test_fifo_concurrency_and_timeout_process_group(setup):
    broker, transport, now = setup
    request(broker, "e001-first")
    request(broker, "e002-second")
    broker.tick()
    assert len(transport.launches) == 1
    assert receipt(broker, "e002-second")["state"] == "PREPARED"
    now[0] += 11
    broker.tick()
    first = receipt(broker, "e001-first")
    assert first["state"] == "TIMED_OUT_KILL_PENDING", first["history"]
    assert len(transport.launches) == 1
    marker = json.loads((remote(transport, "e001-first") / "launch.json").read_text())
    assert marker["termination_grace_seconds"] == 30
    now[0] += 29
    broker.tick()
    assert len(transport.killed) == 1
    now[0] += 1
    broker.tick()
    first = receipt(broker, "e001-first")
    assert first["state"] == "RESULT_COLLECTED" and first["outcome"] == "TIMED_OUT"
    assert [sig for _, sig in transport.killed] == [signal.SIGTERM, 9]
    assert transport.killed[0][0] == 4321
    assert len(transport.launches) == 2


@pytest.mark.parametrize("exit_code,outcome", [("0", "SUCCEEDED"), ("17", "FAILED")])
def test_exit_status(setup, exit_code, outcome):
    broker, transport, _ = setup
    request(broker)
    broker.tick()
    (remote(transport) / "exit_code").write_text(exit_code)
    broker.tick()
    assert receipt(broker)["outcome"] == outcome


@pytest.mark.parametrize("gpu,devices", [(True, "0"), (False, "")])
def test_gpu_and_command_quoting(setup, gpu, devices):
    broker, transport, _ = setup
    command = '''python run.py --name 'a $HOME' --other "$(echo unsafe)"'''
    request(broker, command=command, gpu=gpu)
    broker.tick()
    args, actual_devices, cwd = transport.launches[0]
    assert actual_devices == devices
    assert cwd == remote(transport)
    assert args[:4] == ["setsid", "nohup", "bash", "-c"]
    # bash receives one quoted command argument, including literal quotes/$.
    assert shlex.split(args[4].split("; rc=$?", 1)[0]) == ["bash", "-c", command]
    marker = json.loads((cwd / "launch.json").read_text())
    assert marker["request_digest"] == receipt(broker)["request_digest"]


def test_download_limit_and_retry(setup):
    broker, transport, now = setup
    request(broker)
    broker.tick()
    (remote(transport) / "metrics.csv").write_bytes(b"x" * 2049)
    (remote(transport) / "exit_code").write_text("0")
    broker.tick()
    result = receipt(broker)
    assert result["state"] == "SUCCEEDED"
    assert "max_download_bytes" in result["history"][-1]["detail"]
    assert not (broker.profile.local_root / "e001-baseline/manifest.json").exists()
    (remote(transport) / "metrics.csv").write_bytes(b"ok")
    now[0] += 3
    broker.tick()
    assert receipt(broker)["state"] == "RESULT_COLLECTED"
    assert len(transport.launches) == 1


@pytest.mark.parametrize("root", ["/wjc/jobs", "../wjc", "wjc/../other", "other/jobs", "wjc-other", "wjc\\jobs", "C:/wjc"])
def test_remote_root_rule(setup, root):
    broker, _, _ = setup
    with pytest.raises(ValueError):
        RemoteJobProfile("lab", root, broker.profile.local_root, broker.profile.scan_roots)


@pytest.mark.parametrize("root", ["wjc", "wjc/jobs", "wjc/experiments/jobs"])
def test_valid_remote_roots(setup, root):
    broker, _, _ = setup
    assert RemoteJobProfile("lab", root, broker.profile.local_root, broker.profile.scan_roots).remote_root == root


def test_config_disabled_and_invalid_profile(tmp_path, monkeypatch):
    monkeypatch.delenv("REVERSE_AGENT_REMOTE_JOB_PROFILE", raising=False)
    assert configured_broker() is None
    path = tmp_path / "profile.json"
    path.write_text(json.dumps({"ssh_alias": "lab", "remote_root": "outside", "local_root": str(tmp_path), "scan_roots": [str(tmp_path)]}))
    monkeypatch.setenv("REVERSE_AGENT_REMOTE_JOB_PROFILE", str(path))
    assert configured_broker() is None
    with pytest.raises(SystemExit):
        main(["status"])


def test_profile_loading_does_not_start_transport(tmp_path, monkeypatch):
    profile = {"ssh_alias": "lab", "remote_root": "wjc/research",
               "local_root": str(tmp_path / "receipts"), "scan_roots": [str(tmp_path / "ws")],
               "gpu_devices": ["0", "2"], "poll_seconds": 5}
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile))
    monkeypatch.setenv("REVERSE_AGENT_REMOTE_JOB_PROFILE", str(path))
    def no_subprocess(*args, **kwargs):
        raise AssertionError("loading a profile must not start SSH")
    monkeypatch.setattr(subprocess, "run", no_subprocess)
    configured = configured_broker()
    assert configured.profile.remote_root == "wjc/research"
    assert configured.profile.gpu_devices == ["0", "2"]
    assert configured._thread is None


@pytest.mark.parametrize("with_files", [False, True])
def test_scp_transport_uses_argv_and_quotes_remote_paths(setup, monkeypatch, tmp_path, with_files):
    broker, _, _ = setup
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        assert isinstance(argv, list)
        assert not kwargs.get("shell", False)
        assert kwargs["timeout"] == 120
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(subprocess, "run", run)
    transport = SSHTransport(broker.profile)
    path = "wjc/a 'quoted' $dollar/e001-job"
    source = tmp_path / "source with spaces"
    source.mkdir()
    (source / "job.json").write_text('{}', encoding="utf-8")
    entries = [source / "job.json"]
    if with_files:
        (source / "input file.txt").write_text("input", encoding="utf-8")
        (source / "nested").mkdir()
        (source / "nested" / "run.py").write_text("pass", encoding="utf-8")
        entries = [source / "input file.txt", source / "job.json", source / "nested"]
    transport.upload(source, path)
    transport.download(path + "/file with spaces", tmp_path / "destination")
    assert calls[0] == [
        "scp", "-O", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
        "-r", *(str(entry) for entry in entries), "lab:" + shlex.quote(path + "/"),
    ]
    for argv in calls:
        assert argv[:6] == ["scp", "-O", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]
    assert shlex.split(calls[0][-1].split(":", 1)[1]) == [path + "/"]
    assert shlex.split(calls[1][-2].split(":", 1)[1]) == [path + "/file with spaces"]


def test_cli_status(setup, monkeypatch, capsys):
    broker, _, _ = setup
    request(broker, unknown=True)
    broker.tick()
    monkeypatch.setattr(remote_jobs, "configured_broker", lambda: broker)
    main(["status", "--json"])
    assert json.loads(capsys.readouterr().out)[0]["state"] == "REJECTED"


def test_host_broker_lifecycle(tmp_path, monkeypatch):
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    monkeypatch.delenv("REVERSE_AGENT_REMOTE_JOB_PROFILE", raising=False)
    monkeypatch.delenv("REVERSE_AGENT_AUTONOMOUS", raising=False)
    host = CombinedTrustedHost(task_store=TaskStore(db_path=str(tmp_path / "tasks.sqlite3")), vault=None)
    host.start(model_control_port=0, task_api_port=0)
    try:
        assert host._remote_job_broker is None
    finally:
        host.stop()
    events = []
    fake = SimpleNamespace(start=lambda: events.append("start"), stop=lambda: events.append("stop"))
    monkeypatch.setattr(trusted_host, "configured_broker", lambda: fake)
    host.start(model_control_port=0, task_api_port=0)
    host.stop()
    assert events == ["start", "stop"]


@pytest.mark.parametrize("field", ["files", "outputs"])
@pytest.mark.parametrize("character", ["\n", "\r", "\t", "\x1b", "\x7f", "\x85"])
def test_control_characters_rejected(setup, field, character):
    broker, transport, _ = setup
    request(broker, **{field: ["bad" + character + "name"]})
    broker.tick()
    assert receipt(broker)["state"] == "REJECTED"
    assert not transport.calls


@pytest.mark.parametrize("change", ["start", "boot", "permission"])
@pytest.mark.parametrize("pending", [False, True])
def test_identity_mismatch_and_permission_never_signal(setup, change, pending):
    broker, transport, now = setup
    request(broker)
    broker.tick()
    if pending:
        now[0] += 11
        broker.tick()
    signals_before = list(transport.killed)
    if change == "start":
        transport.start_time += 1
    elif change == "boot":
        transport.boot_id = "rebooted"
    else:
        transport.deny_signal = True
    now[0] += 11
    broker.tick()
    assert receipt(broker)["outcome"] == "LOST"
    assert transport.killed == signals_before


@pytest.mark.parametrize("operation", ["poll", "collect", "probe"])
@pytest.mark.parametrize("reply", ["not json", "{}", "[]", '{"state": []}', '{"files": [{}], "logs": {}}'])
def test_malformed_reply_isolated_with_backoff(setup, monkeypatch, operation, reply):
    broker, transport, now = setup
    request(broker, "e001-bad")
    request(broker, "e002-good")
    if operation != "probe":
        broker.tick()
    if operation == "collect":
        (remote(transport, "e001-bad") / "exit_code").write_text("0")
    transport.calls.clear()
    original = transport.run
    def run(argv, timeout, stdin_text=None):
        data = _program_request(stdin_text)
        if data["op"] == operation and data["job_id"] == "e001-bad":
            return 0, reply, ""
        return original(argv, timeout, stdin_text=stdin_text)
    monkeypatch.setattr(transport, "run", run)
    broker.tick()
    bad = receipt(broker, "e001-bad")
    assert bad["errors"] == 1
    assert bad["retry_at"] > now[0]
    assert "error" in bad["history"][-1]["detail"]
    # The next job is still probed even when the first job's slot is retained.
    assert any(c["job_id"] == "e002-good" for c in transport.calls)
    assert receipt(broker, "e002-good")["state"] == ("PREPARED" if operation == "poll" else "RUNNING")
    broker.tick()
    assert receipt(broker, "e001-bad")["errors"] == 1


def test_stop_abandons_blocked_transport_and_prevents_restart(setup, monkeypatch):
    broker, transport, _ = setup
    request(broker)
    entered, release = threading.Event(), threading.Event()
    def run(argv, timeout, stdin_text=None):
        entered.set()
        assert release.wait(5)
        return 0, '{"marker": false}', ""
    monkeypatch.setattr(transport, "run", run)
    broker.start()
    assert entered.wait(2)
    try:
        started = time.monotonic()
        broker.stop()
        assert time.monotonic() - started < 2
        assert broker._thread.is_alive()
        with pytest.raises(RuntimeError):
            broker.start()
    finally:
        release.set()
        broker._thread.join(2)
    assert not broker._thread.is_alive()
    assert receipt(broker)["state"] == "PREPARED"
    assert not transport.launches



def test_timeout_tracks_descendants_and_waits_for_kill_completion(setup):
    broker, transport, now = setup
    request(broker)
    request(broker, "e002-next")
    broker.tick()
    transport.leader_alive = False
    transport.ignore_kill = True
    now[0] += 11
    broker.tick()
    assert receipt(broker)["state"] == "TIMED_OUT_KILL_PENDING"
    (remote(transport) / "exit_code").write_text("0")
    now[0] += 30
    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    assert receipt(broker)["state"] == "TIMED_OUT_KILL_PENDING"
    assert [sig for _, sig in transport.killed] == [signal.SIGTERM, 9]
    assert len(transport.launches) == 1
    transport.alive = False
    restarted.tick()
    assert receipt(broker)["outcome"] == "TIMED_OUT"
    assert len(transport.launches) == 2


@pytest.mark.parametrize("sig", [signal.SIGTERM, 9])
def test_permission_failure_during_timeout_signal_is_lost(setup, sig):
    broker, transport, now = setup
    request(broker)
    broker.tick()
    now[0] += 11
    if sig == 9:
        broker.tick()
        now[0] += 30
    transport.deny_on_signal = sig
    broker.tick()
    assert receipt(broker)["outcome"] == "LOST"
    assert receipt(broker)["state"] == "RESULT_COLLECTED"


@pytest.mark.parametrize("component", ["home", "wjc"])
def test_remote_symlinked_home_or_wjc_refused(setup, monkeypatch, component):
    broker, transport, _ = setup
    request(broker)
    original = Path.is_symlink
    target = transport.home if component == "home" else transport.home / "wjc"
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == target or original(path))
    broker.tick()
    assert not transport.launches
    assert "symlink" in receipt(broker)["history"][-1]["detail"]


@pytest.mark.parametrize("operation", ["upload", "download"])
def test_stop_abandons_scp_at_persisted_step(setup, monkeypatch, operation):
    broker, transport, _ = setup
    request(broker)
    if operation == "download":
        broker.tick()
        (remote(transport) / "metrics.csv").write_bytes(b"result")
        (remote(transport) / "exit_code").write_text("0")
    entered, release = threading.Event(), threading.Event()
    original = getattr(transport, operation)
    def blocked(*args):
        entered.set()
        assert release.wait(5)
        original(*args)
    monkeypatch.setattr(transport, operation, blocked)
    broker.start()
    assert entered.wait(2)
    try:
        started = time.monotonic()
        broker.stop()
        assert time.monotonic() - started < 2
    finally:
        release.set()
        broker._thread.join(2)
    assert not broker._thread.is_alive()
    assert receipt(broker)["state"] == ("PREPARED" if operation == "upload" else "SUCCEEDED")
    assert not (broker.profile.local_root / "e001-baseline/manifest.json").exists()


@pytest.mark.parametrize("data", [
    {"state": []}, {"state": "BOGUS"}, {"state": "RUNNING"},
    {"state": "RUNNING", "request_digest": 1},
])
def test_poll_schema_validation(setup, data):
    broker, _, _ = setup
    with pytest.raises(ValueError):
        broker._validate_reply("poll", {"launched_at": 1000, **data})



def test_timeout_term_can_finish_without_kill(setup):
    broker, transport, now = setup
    request(broker)
    broker.tick()
    transport.ignore_term = False
    now[0] += 11
    broker.tick()
    assert receipt(broker)["outcome"] == "TIMED_OUT"
    assert transport.killed == [(4321, signal.SIGTERM)]


def test_remote_program_carries_the_request_out_of_band() -> None:
    data = {"op": "collect", "job_id": "e" * 48, "outputs": ["results/x%d.json" % i for i in range(64)]}
    program = _remote_program(data)
    assert REMOTE_HELPER in program
    assert _program_request(program) == data


def test_broker_never_puts_the_helper_on_the_ssh_command_line(setup, monkeypatch):
    """#1328 P0-A: the remote program must travel on stdin, not in argv.

    A POSIX-quoted helper plus its JSON request does not fit the Windows
    process command line (8191 characters); the quiet truncation left the
    remote bash with an unterminated quote. The command line therefore stays
    a quote-free constant and the program goes through stdin.
    """
    broker, transport, _ = setup
    seen = []
    original = transport.run

    def run(argv, timeout, stdin_text=None):
        seen.append((list(argv), stdin_text))
        return original(argv, timeout, stdin_text=stdin_text)

    monkeypatch.setattr(transport, "run", run)
    request(broker)
    broker.tick()

    assert seen
    for argv, program in seen:
        assert argv[6:] == list(REMOTE_COMMAND)
        assert sum(len(part) + 1 for part in argv) < 512
        assert not ({"'", '"', "\\", "$", "`"} & set("".join(argv)))
        assert isinstance(program, str) and REMOTE_HELPER in program
        # the payload must still reach the helper unchanged
        assert _program_request(program)["job_id"] == "e001-baseline"


def test_remote_program_carries_the_request_out_of_band() -> None:
    data = {"op": "collect", "job_id": "e" * 48, "outputs": ["results/x%d.json" % i for i in range(64)]}
    program = _remote_program(data)
    assert REMOTE_HELPER in program
    assert _program_request(program) == data


def test_broker_never_puts_the_helper_on_the_ssh_command_line(setup, monkeypatch):
    """#1328 P0-A: the remote program must travel on stdin, not in argv.

    A POSIX-quoted helper plus its JSON request does not fit the Windows
    process command line (8191 characters); the quiet truncation left the
    remote bash with an unterminated quote. The command line therefore stays
    a quote-free constant and the program goes through stdin.
    """
    broker, transport, _ = setup
    seen = []
    original = transport.run

    def run(argv, timeout, stdin_text=None):
        seen.append((list(argv), stdin_text))
        return original(argv, timeout, stdin_text=stdin_text)

    monkeypatch.setattr(transport, "run", run)
    request(broker)
    broker.tick()

    assert seen
    for argv, program in seen:
        assert argv[6:] == list(REMOTE_COMMAND)
        assert sum(len(part) + 1 for part in argv) < 512
        assert not ({"'", '"', "\\", "$", "`"} & set("".join(argv)))
        assert isinstance(program, str) and REMOTE_HELPER in program
        # the payload must still reach the helper unchanged
        assert _program_request(program)["job_id"] == "e001-baseline"
