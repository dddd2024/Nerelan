"""Supervisor requests (Owner decision 2026-11-10). Provider-free: no server, model or dispatch."""
from __future__ import annotations

import json

import pytest

from reverse_agent.platform_v1 import supervisor_requests
from reverse_agent.platform_v1.control_store import OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT
from reverse_agent.platform_v1.quick_start import PRESETS
from reverse_agent.platform_v1.run_store import TaskStoreError
from reverse_agent.platform_v1.supervisor_requests import DIRECTORY, SupervisorRequests

from test_owner_window import setup, untouched  # noqa: F401 - shared fixture (rootdir import mode)


@pytest.fixture
def state(setup, tmp_path, monkeypatch):  # noqa: F811
    """The host's state directory, with supervisor activation turned on by the Owner."""
    monkeypatch.setattr(setup.host._store, "_state_path", tmp_path / "model_setup_state.json", raising=False)
    settings = tmp_path / "owner_window_settings.json"
    settings.write_text(json.dumps({"supervisor_activation": True}), encoding="utf-8")
    return settings


def digest(setup, preset, *goals):  # noqa: F811
    admission = setup.host._owner_window_admission
    ids = [goal.id for goal in goals]
    report = admission.preflight(ids, **admission.supervisor_request(ids, preset))
    assert report["ok"] is True, report["checks"]
    return report["card_digest"]


class TestPresetBounds:
    @pytest.mark.parametrize("preset", sorted(PRESETS))
    def test_the_request_is_the_preset(self, setup, state, preset):  # noqa: F811
        goal = setup.planned("a", "codex", "pinned", tasks=2)
        request = setup.host._owner_window_admission.supervisor_request([goal.id], preset)
        values = PRESETS[preset]
        assert "goal_ids" not in request
        assert request["hours"] == float(values["hours"])
        assert request["max_concurrent"] == values["max_concurrent"]
        assert request["max_retries"] == values["max_retries"]
        assert request["max_token_units"] == values["max_token_units"]
        assert request["max_tasks"] == 2 * (1 + values["max_retries"])
        assert request["max_cost_micro_units"] == 0

    @pytest.mark.parametrize("preset", ["", "month", None, 3])
    def test_an_unknown_preset_is_refused(self, setup, state, preset):  # noqa: F811
        goal = setup.planned("a", "codex", "pinned")
        with pytest.raises(TaskStoreError, match="owner_window_preset_invalid"):
            setup.host._owner_window_admission.supervisor_request([goal.id], preset)

    @pytest.mark.parametrize("goal_ids", [[], "g1", None, [3], ["bad id"]])
    def test_malformed_goal_ids_are_refused(self, setup, state, goal_ids):  # noqa: F811
        with pytest.raises(TaskStoreError, match="owner_window_request_invalid"):
            setup.host._owner_window_admission.supervisor_request(goal_ids, "day")


class TestSupervisorActivation:
    def test_it_activates_with_a_receipt_that_says_a_supervisor_asked(self, setup, state):  # noqa: F811
        a, b = setup.planned("a", "codex", "pinned"), setup.planned("b", "opencode", "free")
        window = setup.host._owner_window_admission.admit_from_supervisor(
            [a.id, b.id], preset="day", card_digest=digest(setup, "day", a, b), requested_by="claude-supervisor")
        assert window.confirmation_mode == OWNER_WINDOW_MODE and window.status == "ACTIVE"
        rows = setup.db._conn.execute("SELECT evidence_json FROM platform_operation_receipts WHERE operation_type = ?",
                                      (OWNER_WINDOW_RECEIPT,)).fetchall()
        evidence = [json.loads(row["evidence_json"]) for row in rows]
        assert len(evidence) == 2
        assert {item["mechanism"] for item in evidence} == {
            "supervisor request file under the Owner's standing delegation; preset bounds only"}
        assert {item["requested_by"] for item in evidence} == {"claude-supervisor"}
        assert {item["envelope"]["max_retries"] for item in evidence} == {PRESETS["day"]["max_retries"]}

    def test_it_is_off_by_default(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        card = digest(setup, "day", a)
        state.unlink()
        with pytest.raises(TaskStoreError, match="owner_window_supervisor_activation_disabled"):
            setup.host._owner_window_admission.admit_from_supervisor([a.id], preset="day", card_digest=card)
        untouched(setup, a)

    def test_strict_terminal_mode_refuses_it(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        card = digest(setup, "day", a)
        state.write_text(json.dumps({"confirmation": "terminal", "supervisor_activation": True}), encoding="utf-8")
        with pytest.raises(TaskStoreError, match="owner_window_supervisor_activation_disabled"):
            setup.host._owner_window_admission.admit_from_supervisor([a.id], preset="day", card_digest=card)
        untouched(setup, a)

    @pytest.mark.parametrize("content", ['{"supervisor_activation": "yes"}', '{"supervisor_activation": 1}', "[]"])
    def test_bad_settings_fail_closed(self, setup, state, content):  # noqa: F811
        state.write_text(content, encoding="utf-8")
        with pytest.raises(TaskStoreError, match="owner_window_settings_invalid"):
            setup.host._owner_window_admission.supervisor_enabled()

    def test_another_presets_digest_is_refused(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        card = digest(setup, "trial", a)
        with pytest.raises(TaskStoreError, match="owner_window_scope_changed"):
            setup.host._owner_window_admission.admit_from_supervisor([a.id], preset="week", card_digest=card)
        untouched(setup, a)

    def test_a_goal_replanned_after_the_preflight_is_refused(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        card = digest(setup, "day", a)
        replanned = setup.host._goal_service.plan(a.id, expected_revision=a.revision, tasks=[
            {"id": "T0", "title": "Different", "instruction": "Other work"}]).goal
        with pytest.raises(TaskStoreError, match="owner_window_scope_changed"):
            setup.host._owner_window_admission.admit_from_supervisor([a.id], preset="day", card_digest=card)
        untouched(setup, replanned)

    @pytest.mark.parametrize("card", ["", "x" * 64, None])
    def test_a_malformed_digest_is_refused(self, setup, state, card):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        with pytest.raises(TaskStoreError, match="owner_window_card_digest_invalid"):
            setup.host._owner_window_admission.admit_from_supervisor([a.id], preset="day", card_digest=card)
        untouched(setup, a)

    def test_the_terminal_and_card_surfaces_keep_their_receipt_text(self):
        from reverse_agent.platform_v1 import owner_window
        assert owner_window._MECHANISMS["terminal"] == "owner typed a one-time code at the host terminal"
        assert owner_window._MECHANISMS["ui"] == "owner pressed Start on the Nerelan confirmation card"


class TestRequestFiles:
    def put(self, state, name, payload, suffix=".request.json"):
        directory = state.parent / DIRECTORY
        directory.mkdir(exist_ok=True)
        path = directory / f"{name}{suffix}"
        path.write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
        return path

    def result(self, state, name):
        return json.loads((state.parent / DIRECTORY / f"{name}.result.json").read_text(encoding="utf-8"))

    def test_preflight_then_activate_through_files(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        watcher = SupervisorRequests(setup.host)
        request = self.put(state, "aaaaaaaa", {"action": "preflight", "preset": "trial", "goal_ids": [a.id]})
        assert watcher.poll_once() == 1 and not request.exists()
        report = self.result(state, "aaaaaaaa")
        assert report["ok"] is True and report["result"]["ok"] is True
        self.put(state, "bbbbbbbb", {"action": "activate", "preset": "trial", "goal_ids": [a.id],
                                     "card_digest": report["result"]["card_digest"], "requested_by": "test"})
        assert watcher.poll_once() == 1
        activated = self.result(state, "bbbbbbbb")
        assert activated["ok"] is True and activated["result"]["status"] == "ACTIVE"
        assert len(setup.host._control_store.list_windows()) == 1
        assert watcher.poll_once() == 0  # the request file is gone: it cannot run twice
        assert len(setup.host._control_store.list_windows()) == 1

    def test_a_request_cannot_carry_bounds(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        card = digest(setup, "day", a)
        self.put(state, "cccccccc", {"action": "activate", "preset": "day", "goal_ids": [a.id],
                                     "card_digest": card, "hours": 100})
        assert SupervisorRequests(setup.host).poll_once() == 1
        assert self.result(state, "cccccccc") == {"ok": False, "action": "activate",
                                                  "error": "supervisor_request_invalid"}
        untouched(setup, a)

    def test_disabled_requests_are_answered_and_do_nothing(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        card = digest(setup, "day", a)
        state.unlink()
        for name, payload in (("dddddddd", {"action": "activate", "preset": "day", "goal_ids": [a.id],
                                            "card_digest": card}),
                              ("eeeeeeee", {"action": "draft", "text": "do x", "repository": "owner/repo"})):
            self.put(state, name, payload)
        assert SupervisorRequests(setup.host).poll_once() == 2
        for name in ("dddddddd", "eeeeeeee"):
            assert self.result(state, name)["error"] == "owner_window_supervisor_activation_disabled"
        untouched(setup, a)

    @pytest.mark.parametrize("payload", ["not json", "[]", '{"action": "merge"}', '{"action": "preflight", "x": 1}'])
    def test_malformed_requests_are_refused(self, setup, state, payload):  # noqa: F811
        self.put(state, "ffffffff", payload)
        assert SupervisorRequests(setup.host).poll_once() == 1
        assert self.result(state, "ffffffff")["error"] == "supervisor_request_invalid"

    def test_an_oversized_request_is_refused(self, setup, state):  # noqa: F811
        self.put(state, "gggggggg", " " * (supervisor_requests.MAX_REQUEST_BYTES + 1))
        assert SupervisorRequests(setup.host).poll_once() == 1
        assert self.result(state, "gggggggg")["error"] == "supervisor_request_too_large"

    def test_a_badly_named_request_is_removed_without_an_answer(self, setup, state):  # noqa: F811
        request = self.put(state, "Bad Name", {"action": "preflight"})
        assert SupervisorRequests(setup.host).poll_once() == 0
        assert not request.exists()
        assert list((state.parent / DIRECTORY).glob("*.result.json")) == []

    def test_no_directory_means_nothing_to_do(self, setup, state):  # noqa: F811
        assert SupervisorRequests(setup.host).poll_once() == 0

    def test_submit_withdraws_an_unanswered_request(self, state):
        answer = supervisor_requests.submit(state.parent, {"action": "preflight"}, wait_seconds=0.2, poll_seconds=0.05)
        assert answer == {"ok": False, "action": "preflight", "error": "supervisor_request_unanswered",
                          "request_id": answer["request_id"]}
        assert list((state.parent / DIRECTORY).glob("*.request.json")) == []

    def test_the_host_starts_the_watcher_with_the_coordinator_and_stops_it(self):
        import inspect
        from reverse_agent.platform_v1 import trusted_host
        source = inspect.getsource(trusted_host.CombinedTrustedHost)
        start = source[source.index("self._coordinator.start()"):]
        assert "self._supervisor_requests.start()" in start[:300]
        assert "self._supervisor_requests.stop()" in inspect.getsource(
            trusted_host.CombinedTrustedHost._cleanup_runtime_resources)


class TestReviewFindings:
    """Cases from the independent review of 5eda6a6b."""

    put = TestRequestFiles.put
    result = TestRequestFiles.result

    def test_a_request_the_host_took_is_never_reported_as_unanswered(self, state):
        """B1: the host takes the file, the wait runs out, then the host answers."""
        import threading
        import time
        directory = state.parent / DIRECTORY
        directory.mkdir()

        def slow_host():
            while not list(directory.glob("*.request.json")):
                time.sleep(0.01)
            request = next(directory.glob("*.request.json"))
            request.unlink()
            time.sleep(0.6)
            name = request.name[:-len(".request.json")]
            (directory / f"{name}.result.json").write_text(
                json.dumps({"ok": True, "action": "activate", "result": {"status": "ACTIVE"}}), encoding="utf-8")
        thread = threading.Thread(target=slow_host)
        thread.start()
        answer = supervisor_requests.submit(state.parent, {"action": "activate"}, wait_seconds=0.2,
                                            poll_seconds=0.05, taken_grace_seconds=5)
        thread.join()
        assert answer["ok"] is True and answer["result"] == {"status": "ACTIVE"} and answer["request_id"]

    def test_a_taken_request_with_no_answer_is_reported_as_pending_with_its_result_path(self, state):
        import threading
        import time
        directory = state.parent / DIRECTORY
        directory.mkdir()

        def host_takes_and_stalls():
            while not list(directory.glob("*.request.json")):
                time.sleep(0.01)
            next(directory.glob("*.request.json")).unlink()
        thread = threading.Thread(target=host_takes_and_stalls)
        thread.start()
        answer = supervisor_requests.submit(state.parent, {"action": "activate"}, wait_seconds=0.2,
                                            poll_seconds=0.05, taken_grace_seconds=0.2)
        thread.join()
        assert answer["ok"] is False and answer["error"] == "supervisor_request_taken_result_pending"
        assert answer["result_path"].endswith(f"{answer['request_id']}.result.json")

    def test_a_missing_state_directory_is_not_created(self, tmp_path):
        answer = supervisor_requests.submit(tmp_path / "typo", {"action": "preflight"}, wait_seconds=0.1)
        assert answer["error"] == "supervisor_state_dir_missing" and not (tmp_path / "typo").exists()

    def test_the_switch_is_read_at_start_and_cannot_be_turned_on_later(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        card = digest(setup, "day", a)
        state.unlink()
        watcher = SupervisorRequests(setup.host)
        watcher.start()
        watcher.stop()
        state.write_text(json.dumps({"supervisor_activation": True}), encoding="utf-8")
        self.put(state, "hhhhhhhh", {"action": "activate", "preset": "day", "goal_ids": [a.id], "card_digest": card})
        assert watcher.poll_once() == 1
        assert self.result(state, "hhhhhhhh")["error"] == "owner_window_supervisor_activation_disabled"
        untouched(setup, a)

    def test_turning_the_switch_off_works_at_once(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        card = digest(setup, "day", a)
        watcher = SupervisorRequests(setup.host)
        assert watcher.poll_once() == 0 and watcher._latched() is True
        state.write_text(json.dumps({"supervisor_activation": False}), encoding="utf-8")
        self.put(state, "iiiiiiii", {"action": "activate", "preset": "day", "goal_ids": [a.id], "card_digest": card})
        assert watcher.poll_once() == 1
        assert self.result(state, "iiiiiiii")["error"] == "owner_window_supervisor_activation_disabled"
        untouched(setup, a)

    def test_a_disabled_draft_creates_no_goal(self, setup, state):  # noqa: F811
        state.unlink()
        before = setup.db._conn.execute("SELECT COUNT(*) FROM platform_goals").fetchone()[0]
        self.put(state, "jjjjjjjj", {"action": "draft", "text": "do x", "repository": "owner/repo"})
        assert SupervisorRequests(setup.host).poll_once() == 1
        assert setup.db._conn.execute("SELECT COUNT(*) FROM platform_goals").fetchone()[0] == before

    def test_a_request_with_a_byte_order_mark_is_read(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        directory = state.parent / DIRECTORY
        directory.mkdir()
        (directory / "kkkkkkkk.request.json").write_bytes(
            b"\xef\xbb\xbf" + json.dumps({"action": "preflight", "preset": "day", "goal_ids": [a.id]}).encode())
        assert SupervisorRequests(setup.host).poll_once() == 1
        assert self.result(state, "kkkkkkkk")["ok"] is True

    @pytest.mark.parametrize("label", [5, {"a": 1}, ["x"], None])
    def test_a_non_string_requester_is_refused(self, setup, state, label):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        with pytest.raises(TaskStoreError, match="owner_window_request_invalid"):
            setup.host._owner_window_admission.admit_from_supervisor(
                [a.id], preset="day", card_digest=digest(setup, "day", a), requested_by=label)
        untouched(setup, a)

    def test_the_requester_label_keeps_printable_text_only(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        setup.host._owner_window_admission.admit_from_supervisor(
            [a.id], preset="day", card_digest=digest(setup, "day", a), requested_by="cla\x00ude\n" + "x" * 300)
        row = setup.db._conn.execute("SELECT evidence_json FROM platform_operation_receipts WHERE operation_type = ?",
                                     (OWNER_WINDOW_RECEIPT,)).fetchone()
        label = json.loads(row["evidence_json"])["requested_by"]
        assert label.startswith("claude") and len(label) == 200 and label.isprintable()

    def test_a_result_that_cannot_be_written_does_not_stop_the_other_requests(self, setup, state):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        directory = state.parent / DIRECTORY
        directory.mkdir()
        (directory / "aaaaaaa1.result.json").mkdir()  # the first answer cannot replace a directory
        for name in ("aaaaaaa1", "aaaaaaa2"):
            self.put(state, name, {"action": "preflight", "preset": "day", "goal_ids": [a.id]})
        assert SupervisorRequests(setup.host).poll_once() == 1
        assert self.result(state, "aaaaaaa2")["ok"] is True
        assert list(directory.glob("*.tmp")) == []

    def test_entries_that_cannot_be_taken_do_not_starve_the_queue(self, setup, state, monkeypatch):  # noqa: F811
        a = setup.planned("a", "codex", "pinned")
        directory = state.parent / DIRECTORY
        directory.mkdir()
        monkeypatch.setattr(supervisor_requests, "MAX_REQUESTS_PER_POLL", 1)
        (directory / "00000000.request.json").mkdir()  # sorts first, is not a file
        self.put(state, "zzzzzzzz", {"action": "preflight", "preset": "day", "goal_ids": [a.id]})
        assert SupervisorRequests(setup.host).poll_once() == 1

    def test_the_watcher_thread_starts_stops_and_restarts(self, setup, state):  # noqa: F811
        import threading
        watcher = SupervisorRequests(setup.host, poll_seconds=0.05)
        watcher.start()
        first = watcher._thread
        watcher.start()
        assert watcher._thread is first and first.is_alive()
        watcher.stop()
        assert not first.is_alive()
        watcher.start()
        assert watcher._thread is not first and watcher._thread.is_alive()
        watcher.stop()
        assert not [t for t in threading.enumerate() if t.name == "supervisor-requests"]
