"""Durable quarantine regressions for the remote broker (#1364).

Every case drives the public ``RemoteJobBroker.quarantine(job_id, reason)``
contract and observes only durable bytes, the returned report, receipt state
and fake transport traffic. Nothing asserts on private fence bookkeeping, so a
quarantine that silently no-ops -- or a discovery path that stops consulting
the fence -- breaks these tests instead of passing quietly.
"""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import threading
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import remote_jobs
from reverse_agent.platform_v1.remote_jobs import RemoteJobBroker

from test_remote_jobs import receipt, remote, request, setup

JOB = "e001-baseline"
REASON = "owner quarantine: #1364 regression"
QUARANTINE_DIR = remote_jobs.QUARANTINE_DIR
QUARANTINE_FENCE = remote_jobs.QUARANTINE_FENCE


def duplicate_outbox(broker, source, job_id=JOB, worktree="second-worktree"):
    """A second outbox carrying the same id but different bytes."""
    target = broker.profile.scan_roots[0] / worktree / ".nerelan-remote/outbox" / job_id
    shutil.copytree(source, target)
    (target / "run.py").write_text("print('duplicate')", encoding="utf-8")
    data = json.loads((target / "job.json").read_text(encoding="utf-8"))
    data["command"] = "python run.py --seed 1"
    (target / "job.json").write_text(json.dumps(data), encoding="utf-8")
    return target


@pytest.fixture
def prepare(setup):
    """One RESULT_COLLECTED receipt plus two distinct duplicate outboxes."""
    broker, transport, now = setup
    outboxes = [request(broker, JOB, gpu=False)]
    outboxes.append(duplicate_outbox(broker, outboxes[0]))
    broker.tick()
    assert receipt(broker, JOB)["state"] == "RUNNING"
    job = remote(transport, JOB)
    (job / "exit_code").write_text("0")
    broker.tick()
    assert receipt(broker, JOB)["state"] == "RESULT_COLLECTED"
    transport.calls.clear()
    transport.launches.clear()
    return broker, transport, now, outboxes


def fence_of(broker, job_id=JOB):
    path = broker.profile.local_root / QUARANTINE_DIR / job_id / QUARANTINE_FENCE
    return json.loads(path.read_text(encoding="utf-8"))


def _fail_archive_at(monkeypatch, index):
    """Raise from the ``index``-th _archive_tree call; every other move runs."""
    calls = []
    original = remote_jobs._archive_tree

    def interrupted(source, dest, limit):
        calls.append(str(source))
        if len(calls) == index:
            raise OSError("injected interruption after the fence was written")
        return original(source, dest, limit)

    monkeypatch.setattr(remote_jobs, "_archive_tree", interrupted)
    return calls


def _assert_fenced_contract(broker, transport):
    """Observable contract of a fenced id: archived, readable, never dispatched."""
    assert not transport.calls, transport.calls
    assert not transport.launches
    assert broker.receipts() == []
    assert not (broker.profile.local_root / JOB).exists()
    assert broker.quarantines(), "the durable fence must still be readable"


def test_quarantine_archives_the_receipt_and_every_duplicate_outbox_bytewise(prepare):
    broker, transport, now, outboxes = prepare
    receipt_dir = broker.profile.local_root / JOB
    receipt_bytes = (receipt_dir / "receipt.json").read_bytes()
    saved = json.loads(receipt_bytes)
    history = saved["history"]
    expected_run = {str(path): (path / "run.py").read_bytes() for path in outboxes}
    expected_files = {}
    for path in sorted(receipt_dir.rglob("*")):
        if path.is_file():
            expected_files["receipt/" + path.relative_to(receipt_dir).as_posix()] = path.read_bytes()
    outbox_snapshots = {}
    for path in outboxes:
        for source in sorted(path.rglob("*")):
            if source.is_file():
                outbox_snapshots[(str(path), source.relative_to(path).as_posix())] = source.read_bytes()

    report = broker.quarantine(JOB, reason=REASON)

    source_to_archive = {record["source"]: record["path"] for record in report["outboxes"]}
    assert set(source_to_archive) == {str(path) for path in outboxes}
    for (source, rel), blob in outbox_snapshots.items():
        expected_files[source_to_archive[source] + "/" + rel] = blob

    # Quarantining is local-only: no probe, upload, launch, poll or download.
    assert transport.calls == []
    assert report["state"] == "QUARANTINED"
    assert report["reason"] == REASON
    assert report["quarantined_at"] == now[0]
    assert not receipt_dir.exists()
    assert [path.exists() for path in outboxes] == [False, False]

    archive = Path(report["archive"])
    assert archive.is_dir()

    archived_receipt = (archive / "receipt" / "receipt.json").read_bytes()
    assert archived_receipt == receipt_bytes           # moved, never rewritten
    assert json.loads(archived_receipt)["history"] == history

    assert report["receipt"] == {
        "state": saved["state"],
        "request_digest": saved["request_digest"],
        "history_events": len(history)}

    # Every archived byte is recorded with its size and sha256.
    assert len(report["manifest"]) == len(expected_files)
    assert {entry["path"] for entry in report["manifest"]} == set(expected_files)
    for entry in report["manifest"]:
        blob = (archive / entry["path"]).read_bytes()
        assert blob == expected_files[entry["path"]]
        assert len(blob) == entry["size"]
        assert hashlib.sha256(blob).hexdigest() == entry["sha256"]
    assert report["files"] == len(report["manifest"])
    assert report["bytes"] == sum(entry["size"] for entry in report["manifest"])

    # Each duplicate outbox is archived separately, with its own bytes intact.
    expected = expected_run
    assert {record["source"] for record in report["outboxes"]} == set(expected)
    assert [record["path"] for record in report["outboxes"]] == ["outbox/0", "outbox/1"]
    for record in report["outboxes"]:
        assert (archive / record["path"] / "run.py").read_bytes() == expected[record["source"]]
        assert (archive / record["path"] / "job.json").is_file()
        assert record["files"] == 2
        assert record["bytes"] == sum(
            entry["size"] for entry in report["manifest"]
            if entry["path"].startswith(record["path"] + "/"))

    fence = json.loads((archive / QUARANTINE_FENCE).read_text(encoding="utf-8"))
    assert fence["state"] == "COMMITTED"
    assert fence["job_id"] == JOB
    assert fence["reason"] == REASON
    assert fence["quarantined_at"] == now[0]
    assert fence["manifest"] == report["manifest"]
    assert fence["receipt_dir"] == str(receipt_dir)
    assert sorted(fence["outbox_dirs"]) == sorted(expected)
    assert broker.quarantines() == [fence]


def test_the_fence_survives_later_ticks_a_restart_and_a_resubmission(prepare):
    broker, transport, now, _ = prepare
    assert broker.quarantine(JOB, reason=REASON)["state"] == "QUARANTINED"

    broker.tick()
    broker.tick()
    assert transport.calls == []
    assert transport.launches == []
    assert broker.receipts() == []

    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    assert transport.calls == []
    assert transport.launches == []
    assert restarted.receipts() == []
    assert restarted.quarantines()

    # Re-submitting the same id must not re-enter discovery or dispatch.
    request(broker, JOB, gpu=False)
    restarted.tick()
    assert transport.calls == []
    assert transport.launches == []
    assert restarted.receipts() == []
    assert restarted.quarantines()[0]["state"] == "COMMITTED"


def test_quarantine_of_a_missing_id_is_a_noop(setup):
    broker, transport, _ = setup
    assert broker.quarantine("never-submitted") is None
    assert not (broker.profile.local_root / QUARANTINE_DIR).exists()
    assert broker.quarantines() == []
    assert transport.calls == []


def test_quarantine_of_an_already_fenced_id_is_a_noop(prepare):
    broker, transport, _, _ = prepare
    first = broker.quarantine(JOB, reason=REASON)
    assert first["state"] == "QUARANTINED"
    assert broker.quarantine(JOB, reason="a second attempt") is None
    fence = fence_of(broker)
    assert fence["state"] == "COMMITTED"
    assert fence["reason"] == REASON                  # the first fence is untouched
    assert fence["manifest"] == first["manifest"]
    assert transport.calls == []


@pytest.mark.parametrize("job_id,reason", [
    ("UPPER-CASE", REASON),
    ("ab", REASON),
    ("has space", REASON),
    (1234, REASON),
    (JOB, ""),
    (JOB, "x" * 1001),
])
def test_quarantine_validates_its_arguments_before_touching_the_tree(setup, job_id, reason):
    broker, transport, _ = setup
    request(broker, JOB, gpu=False)
    with pytest.raises(ValueError):
        broker.quarantine(job_id, reason=reason)
    assert not (broker.profile.local_root / QUARANTINE_DIR).exists()
    assert broker.receipts() == []
    assert transport.calls == []


def _break_archive_root(broker, shape):
    base = broker.profile.local_root / QUARANTINE_DIR
    if shape == "root-is-a-file":
        base.write_bytes(b"not a directory")
        return
    base.mkdir(parents=True, exist_ok=True)
    if shape == "entry-is-a-file":
        (base / JOB).write_bytes(b"not a directory")
    elif shape == "entry-name-is-invalid":
        entry = base / "not a job id"
        entry.mkdir()
        (entry / QUARANTINE_FENCE).write_text("{}", encoding="utf-8")
    elif shape == "entry-has-no-fence":
        (base / JOB).mkdir()
    elif shape == "fence-is-a-directory":
        (base / JOB / QUARANTINE_FENCE).mkdir(parents=True)


@pytest.mark.parametrize("shape", [
    "root-is-a-file",
    "entry-is-a-file",
    "entry-name-is-invalid",
    "entry-has-no-fence",
    "fence-is-a-directory",
])
def test_malformed_archive_root_refuses_before_any_transport_call(prepare, shape):
    broker, transport, _, _ = prepare
    _break_archive_root(broker, shape)
    with pytest.raises(ValueError):
        broker.tick()
    assert transport.calls == []
    assert transport.launches == []
    assert receipt(broker, JOB)["state"] == "RESULT_COLLECTED"


@pytest.mark.parametrize("content", [
    b"",
    b"{not json",
    b"[]",
    b"null",
    b'{"state": "BOGUS"}',
    b'{"job_id": "another-job", "state": "COMMITTED"}',
])
def test_malformed_fence_content_stays_fail_closed(prepare, content):
    broker, transport, now, outboxes = prepare
    receipt_dir = broker.profile.local_root / JOB
    receipt_bytes = (receipt_dir / "receipt.json").read_bytes()
    archive = broker.profile.local_root / QUARANTINE_DIR / JOB
    archive.mkdir(parents=True)
    (archive / QUARANTINE_FENCE).write_bytes(content)

    broker.tick()                                     # no raise, no dispatch

    assert transport.calls == []
    assert transport.launches == []
    saved = receipt(broker, JOB)
    assert saved["state"] == "RESULT_COLLECTED"
    assert not any("error" in event["detail"] for event in saved["history"])
    assert [path.exists() for path in outboxes] == [True, True]
    # The receipt is still on disk; the fence only blocked dispatch, so it is
    # byte-for-byte unchanged with no new history event appended.
    assert (receipt_dir / "receipt.json").read_bytes() == receipt_bytes

    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    assert transport.calls == []
    assert transport.launches == []
    assert (receipt_dir / "receipt.json").read_bytes() == receipt_bytes


def _make_junction(link, target):
    if os.name != "nt":
        pytest.skip("directory junctions require Windows")
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                            capture_output=True, text=True)
    if result.returncode:
        pytest.skip("this platform cannot create a directory junction: " + result.stderr.strip())


def test_a_junction_in_the_outbox_is_refused_with_foreign_bytes_untouched(prepare):
    broker, transport, now, outboxes = prepare
    foreign = broker.profile.scan_roots[0] / "foreign-data"
    foreign.mkdir(parents=True)
    sentinel = foreign / "sentinel.bin"
    sentinel.write_bytes(b"outside-the-archive")
    untouched = sentinel.read_bytes()

    junction = outboxes[0] / "results"
    _make_junction(junction, foreign)
    assert junction.is_junction()

    with pytest.raises(ValueError, match="link-like"):
        broker.quarantine(JOB, reason=REASON)

    assert transport.calls == []
    assert transport.launches == []
    assert sentinel.exists()
    assert sentinel.read_bytes() == untouched         # foreign bytes were never moved or written
    assert junction.exists()                          # the link was neither followed nor deleted
    assert outboxes[0].exists()
    assert (outboxes[0] / "run.py").read_text() == "print('fixture')"

    fence = fence_of(broker)
    assert fence["state"] == "INCOMPLETE"
    assert "link-like" in fence["error"]

    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    assert transport.calls == []
    assert transport.launches == []
    assert restarted.receipts() == []
    assert fence_of(broker)["state"] == "INCOMPLETE"
    assert sentinel.read_bytes() == untouched


def test_interruption_before_the_first_move_keeps_the_fence_fail_closed(prepare, monkeypatch):
    broker, transport, now, outboxes = prepare
    receipt_dir = broker.profile.local_root / JOB
    receipt_bytes = (receipt_dir / "receipt.json").read_bytes()
    runs_before = {str(path): (path / "run.py").read_bytes() for path in outboxes}

    calls = _fail_archive_at(monkeypatch, 1)          # interrupted before any move
    with pytest.raises(OSError, match="injected interruption"):
        broker.quarantine(JOB, reason=REASON)

    assert len(calls) == 1
    fence = fence_of(broker)
    assert fence["state"] == "INCOMPLETE"
    assert "injected interruption" in fence["error"]
    assert fence["job_id"] == JOB
    assert fence["reason"] == REASON
    # Nothing was moved: the receipt and every outbox are byte-for-byte unchanged.
    assert (receipt_dir / "receipt.json").read_bytes() == receipt_bytes
    for path in outboxes:
        assert path.exists()
        assert (path / "run.py").read_bytes() == runs_before[str(path)]
    assert not (broker.profile.local_root / QUARANTINE_DIR / JOB / "receipt").exists()

    # A reopened broker must not dispatch anything it never archived.
    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    restarted.tick()
    assert transport.calls == []
    assert transport.launches == []
    assert (receipt_dir / "receipt.json").read_bytes() == receipt_bytes
    for path in outboxes:
        assert (path / "run.py").read_bytes() == runs_before[str(path)]
    assert fence_of(broker)["state"] == "INCOMPLETE"
    assert broker.quarantines() == [fence]


def test_interruption_after_the_first_moves_leaves_the_remaining_source_undispatched(
        prepare, monkeypatch):
    broker, transport, now, outboxes = prepare
    receipt_dir = broker.profile.local_root / JOB
    runs_before = {str(path): (path / "run.py").read_bytes() for path in outboxes}

    calls = _fail_archive_at(monkeypatch, 3)          # receipt and one outbox move, the last fails
    with pytest.raises(OSError, match="injected interruption"):
        broker.quarantine(JOB, reason=REASON)

    assert len(calls) == 3
    fence = fence_of(broker)
    assert fence["state"] == "INCOMPLETE"
    assert "injected interruption" in fence["error"]
    assert not receipt_dir.exists()                    # the first move did land

    archive = broker.profile.local_root / QUARANTINE_DIR / JOB
    assert (archive / "receipt").is_dir()
    assert (archive / "outbox/0").is_dir()
    assert not (archive / "outbox/1").exists()

    remaining = [path for path in outboxes if path.exists()]
    assert len(remaining) == 1                         # one source was never archived
    assert (remaining[0] / "run.py").read_bytes() == runs_before[str(remaining[0])]

    # A reopened broker must not dispatch the source the archive never reached.
    restarted = RemoteJobBroker(broker.profile, transport, lambda: now[0])
    restarted.tick()
    restarted.tick()
    assert transport.calls == []
    assert transport.launches == []
    assert restarted.receipts() == []
    assert remaining[0].exists()
    assert (remaining[0] / "run.py").read_bytes() == runs_before[str(remaining[0])]
    assert fence_of(broker)["state"] == "INCOMPLETE"


def test_quarantine_refuses_to_race_a_tick_holding_the_broker_file_lock(setup):
    broker, transport, _ = setup
    request(broker, JOB, gpu=False)
    broker.tick()
    (remote(transport, JOB) / "exit_code").write_text("0")
    broker.tick()
    assert receipt(broker, JOB)["state"] == "RESULT_COLLECTED"
    transport.calls.clear()
    transport.launches.clear()

    with remote_jobs._BrokerLock(broker.profile.local_root / ".broker.lock"):
        error, outcome = [], object()

        def attempt():
            nonlocal outcome
            try:
                outcome = broker.quarantine(JOB, reason=REASON)
            except BaseException as exc:
                error.append(exc)

        worker = threading.Thread(target=attempt, name="quarantine-attempt")
        worker.start()
        worker.join(10)
        assert not worker.is_alive()

    assert error and isinstance(error[0], OSError)
    assert outcome is not None
    assert receipt(broker, JOB)["state"] == "RESULT_COLLECTED"
    assert not (broker.profile.local_root / QUARANTINE_DIR).exists()
    assert transport.calls == []
    assert transport.launches == []


def test_a_noop_quarantine_breaks_the_contract(setup, monkeypatch):
    """Regression guard: these checks must fail if quarantine stops archiving."""
    broker, transport, _ = setup
    request(broker, JOB, gpu=False)
    broker.tick()
    (remote(transport, JOB) / "exit_code").write_text("0")
    broker.tick()
    assert receipt(broker, JOB)["state"] == "RESULT_COLLECTED"
    transport.calls.clear()
    transport.launches.clear()

    monkeypatch.setattr(RemoteJobBroker, "quarantine",
                        lambda self, job_id, reason="owner quarantine": None)
    broker.quarantine(JOB, reason=REASON)
    broker.tick()

    with pytest.raises(AssertionError):
        _assert_fenced_contract(broker, transport)


def test_a_removed_discovery_fence_breaks_the_contract(setup, monkeypatch):
    """Regression guard: these checks must fail if discovery stops consulting the fence."""
    broker, transport, _ = setup
    request(broker, JOB, gpu=False)
    broker.tick()
    (remote(transport, JOB) / "exit_code").write_text("0")
    broker.tick()
    assert receipt(broker, JOB)["state"] == "RESULT_COLLECTED"
    transport.calls.clear()
    transport.launches.clear()

    _fail_archive_at(monkeypatch, 2)
    with pytest.raises(OSError, match="injected interruption"):
        broker.quarantine(JOB, reason=REASON)
    assert fence_of(broker)["state"] == "INCOMPLETE"
    assert (broker.profile.scan_roots[0] / "task" /
            ".nerelan-remote/outbox" / JOB / "job.json").exists()

    # Simulate a discovery path that no longer consults the durable fence.
    monkeypatch.setattr(RemoteJobBroker, "_quarantined_ids", lambda self: set())
    broker.tick()

    with pytest.raises(AssertionError):
        _assert_fenced_contract(broker, transport)


@pytest.mark.parametrize("state", [
    "UPLOADED",
    "LAUNCHED",
    "RUNNING",
    "TIMED_OUT_KILL_PENDING",
    "LOST",
])
def test_quarantine_refuses_active_unconfirmed_state_before_any_change(setup, state):
    """Quarantining a receipt that still occupies (or may occupy) a remote slot
    must refuse before any fence, data movement, history change or transport
    call, so the durable ``max_concurrent`` slot is conserved.  RUNNING is the
    genuine state a real tick leaves behind; the other active unconfirmed states
    are written into the same local receipt file the broker reads, without ever
    importing the private guard set."""
    broker, transport, _ = setup
    request(broker, JOB, gpu=False)
    broker.tick()
    assert receipt(broker, JOB)["state"] == "RUNNING"

    receipt_dir = broker.profile.local_root / JOB
    if state != "RUNNING":
        saved = json.loads((receipt_dir / "receipt.json").read_text(encoding="utf-8"))
        saved["state"] = state
        (receipt_dir / "receipt.json").write_text(json.dumps(saved), encoding="utf-8")
    original_bytes = (receipt_dir / "receipt.json").read_bytes()
    original = json.loads(original_bytes)
    transport.calls.clear()
    transport.launches.clear()

    with pytest.raises(ValueError) as raised:
        broker.quarantine(JOB, reason=REASON)
    assert state in str(raised.value)

    # Refused before any fence, data movement, history change or transport call.
    assert (receipt_dir / "receipt.json").read_bytes() == original_bytes
    assert json.loads(original_bytes)["history"] == original["history"]
    assert receipt(broker, JOB)["state"] == state
    assert (broker.profile.scan_roots[0] / "task" /
            ".nerelan-remote/outbox" / JOB).exists()
    assert not (broker.profile.local_root / QUARANTINE_DIR).exists()
    assert broker.quarantines() == []
    assert transport.calls == []
    assert transport.launches == []


def test_refusal_on_a_running_job_keeps_a_second_job_queued_under_max_concurrent_one(
        setup):
    """With ``max_concurrent == 1`` the refusal to quarantine the running first
    job must not free its slot: the second, queued job stays ``PREPARED`` and
    no second launch, signal or cancellation ever happens."""
    broker, transport, _ = setup
    assert broker.profile.max_concurrent == 1

    request(broker, JOB, gpu=False)
    broker.tick()
    assert receipt(broker, JOB)["state"] == "RUNNING"

    receipt_dir = broker.profile.local_root / JOB
    original_bytes = (receipt_dir / "receipt.json").read_bytes()
    original = json.loads(original_bytes)
    launches = list(transport.launches)

    with pytest.raises(ValueError):
        broker.quarantine(JOB, reason=REASON)

    request(broker, "e002-second", gpu=False)
    broker.tick()

    # Only the genuine first launch ever happened; the second job stayed queued.
    assert receipt(broker, JOB)["state"] == "RUNNING"
    assert receipt(broker, "e002-second")["state"] == "PREPARED"
    assert transport.launches == launches
    assert len(transport.launches) == 1
    assert transport.killed == []                 # no signal or cancellation
    assert (receipt_dir / "receipt.json").read_bytes() == original_bytes
    assert json.loads(original_bytes)["history"] == original["history"]
    assert not (broker.profile.local_root / QUARANTINE_DIR).exists()
