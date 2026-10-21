"""Deterministic host controller proofs; no native cooperative transport claimed."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reverse_agent.platform_v1 import quota_inflight as inflight
from reverse_agent.platform_v1 import run_store
from reverse_agent.platform_v1.codex_protocol import CodexJsonl
from reverse_agent.platform_v1.claude_protocol import ClaudeStreamJson


class InflightCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = run_store.TaskStore(str(self.root / "tasks.db"))
        self.addCleanup(lambda: self.store._conn.close())
        self.task = self.store.create_task(title="partial task", executor_kind="opencode",
                                           orchestration_mode="sequential_team")
        self.now = 1000.0
        self.clock_patch = patch.object(run_store.time, "time", lambda: self.now)
        self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)
        self.lease = self.store._acquire_durable_lease(task_id=self.task.id,
            execution_id=self.task.execution_id, lease_owner="host", worktree_path=str(self.root))
        self.events = []
        self.file = self.root / "partial.txt"
        self.file.write_text("saved prefix", encoding="utf-8")
        self.payload = {"workspace": str(self.root), "artifact_digest": self.digest(),
                        "summary": "prefix saved", "remaining_work": "append suffix",
                        "resume_state": {"offset": 12}}
        self.control = self.controller()

    def digest(self):
        return hashlib.sha256(self.file.read_bytes()).hexdigest()

    def journal(self, state, payload):
        return self.store.quota_checkpoint(self.lease.run_id, "cp-1", "host", self.lease.epoch,
                                           state=state, payload=payload)

    def controller(self, **kwargs):
        return inflight.CooperativeQuotaCheckpoint(checkpoint_id="cp-1", journal=self.journal,
            request=lambda cp: self.events.append(("request", self.now)),
            verify=lambda p: p == self.payload and p["artifact_digest"] == self.digest(),
            stop=kwargs.get("stop", lambda cp: self.events.append(("stop", self.now)) or True),
            clock=lambda: self.now)

    def evidence(self, weekly=70):
        return {"account_ref": "account", "source": "magpie", "observed_at": "1970-01-01T00:16:40Z",
                "windows": [{"window": "five_hour", "used_percent": 10, "resets_at": 2000},
                            {"window": "weekly", "used_percent": weekly, "resets_at": 5000}]}

    def need(self):
        return {"windows": {name: {"p80": 25} for name in ("five_hour", "weekly")}}

    def tick(self, **kwargs):
        return self.control.tick(self.evidence(), self.need(), [], reservation_id="own", **kwargs)

    def test_request_save_stop_then_resume_saved_bytes_after_restart(self):
        self.assertEqual(self.tick(), "REQUESTED")
        self.now += 1
        self.assertEqual(self.control.saved("cp-1", self.payload), "PAUSED")
        self.assertEqual([e[0] for e in self.events], ["request", "stop"])
        self.assertTrue(all(e[1] < 1005 for e in self.events))  # simulated cutoff
        # Reopen persisted state, do not reconstruct it from a role milestone.
        self.store._conn.close()
        self.store = run_store.TaskStore(str(self.root / "tasks.db"))
        resumed = self.controller()
        self.assertEqual(resumed.resume(admit=lambda p: False, dispatch=lambda *a: self.fail()), "QUOTA_WAIT")
        def dispatch(cp, payload):
            self.assertEqual(cp, "cp-1")
            self.assertEqual(payload["resume_state"]["offset"], len(self.file.read_text()))
            self.file.write_text(self.file.read_text() + " suffix")
        self.assertEqual(resumed.resume(admit=lambda p: True, dispatch=dispatch), "RESUMED")
        self.assertEqual(self.file.read_text(), "saved prefix suffix")
        with self.assertRaises(ValueError):
            resumed.resume(admit=lambda p: True, dispatch=dispatch)
        self.assertEqual(self.store._get_durable_run(self.lease.run_id).accepted_checkpoint, "")

    def test_failed_ack_and_failed_clean_stop_are_not_pauses(self):
        self.tick()
        bad = dict(self.payload, artifact_digest="wrong")
        self.assertEqual(self.control.saved("cp-1", bad), "FAILED")
        self.assertEqual(len(self.events), 1)
        with self.assertRaises(ValueError):
            self.control.resume(admit=lambda p: True, dispatch=lambda *a: self.fail())

    def test_unacknowledged_stop_remains_saved(self):
        self.tick()
        controller = self.controller(stop=lambda cp: False)
        self.assertEqual(controller.saved("cp-1", self.payload), "SAVED")
        self.assertEqual(self.journal(None, None)["state"], "SAVED")

    def test_stale_and_expired_lease_cannot_save(self):
        self.tick()
        with self.assertRaises(run_store.TaskStoreError):
            self.store.quota_checkpoint(self.lease.run_id, "cp-1", "other", self.lease.epoch,
                                        state="SAVED", payload=self.payload)
        self.now += 601
        with self.assertRaises(run_store.TaskStoreError):
            self.control.saved("cp-1", self.payload)
        self.assertEqual(len(self.events), 1)

    def test_no_signals_uses_full_need_and_limit_is_separate(self):
        self.assertEqual(self.tick(), "REQUESTED")
        self.control.limit_hit()
        self.assertEqual(self.journal(None, None)["state"], "LIMIT_HIT")
        self.assertEqual(len(self.events), 1)

    def test_duplicate_and_out_of_order_signals(self):
        self.assertTrue(self.control.observe("codex", 2, {"weekly": 4}))
        self.assertFalse(self.control.observe("codex", 1, {"weekly": 99}))
        self.assertFalse(self.control.observe("codex", 2, {"weekly": 99}))
        self.assertTrue(self.control.observe("codex", 3, {"weekly": 2}))
        self.assertEqual(self.control.high_water, {"weekly": 4})
        self.tick()
        self.tick()
        self.assertEqual(len(self.events), 1)

    def test_other_account_and_own_reservations(self):
        rows = [{"reservation_id": "own", "account_ref": "account", "state": "ACTIVE",
                 "quota_windows": {"weekly": 90}},
                {"reservation_id": "other", "account_ref": "account", "state": "ACTIVE",
                 "quota_windows": {"weekly": 20}}]
        decision = inflight.projection(self.evidence(50), self.need(), rows, reservation_id="own",
                                       spent={}, now=self.now)
        self.assertEqual(decision["blocking_windows"], ["weekly"])
        rows[1]["account_ref"] = "different"
        self.assertEqual(inflight.projection(self.evidence(50), self.need(), rows,
            reservation_id="own", spent={}, now=self.now)["decision"], "ok")

    def test_injected_refresh_detects_pressure_without_warning(self):
        self.assertEqual(self.control.tick(self.evidence(10), self.need(), [], reservation_id="own",
            refresh=lambda account: self.evidence(90)), "REQUESTED")

    def test_ambiguous_resume_is_not_dispatched_again(self):
        self.tick()
        self.control.saved("cp-1", self.payload)
        def lost_reply(*args):
            self.events.append(("dispatch", self.now))
            raise OSError("reply lost")
        with self.assertRaises(OSError):
            self.control.resume(admit=lambda p: True, dispatch=lost_reply)
        self.assertEqual(self.journal(None, None)["state"], "RESUMING")
        with self.assertRaises(ValueError):
            self.controller().resume(admit=lambda p: True, dispatch=lost_reply)
        self.assertEqual(sum(e[0] == "dispatch" for e in self.events), 1)

    def test_duplicate_save_is_idempotent(self):
        self.tick()
        self.control.saved("cp-1", self.payload)
        self.control.saved("cp-1", self.payload)
        self.assertEqual(sum(e[0] == "stop" for e in self.events), 1)
        with self.assertRaises(ValueError):
            self.control.saved("cp-1", dict(self.payload, summary="different"))

    def test_live_spend_over_p80_requests_before_simulated_cutoff(self):
        evidence = self.evidence(50)
        for sequence, spend in enumerate((10, 20, 35, 41)):
            self.now = 1000 + sequence
            self.control.observe("fake-stream", sequence, {"weekly": spend})
            state = self.control.tick(evidence, self.need(), [], reservation_id="own")
        self.assertEqual(state, "REQUESTED")
        self.now += 1
        self.assertEqual(self.control.saved("cp-1", self.payload), "PAUSED")
        # Simulated stream next emits a real limit at t=1005; it has already
        # received clean-stop acknowledgement and must not consume that frame.
        self.assertLess(self.events[-1][1], 1005)

    def live(self, *, account="account", attempt="developer-1", estimate=None, owner="host", epoch=None):
        def journal(**kwargs):
            return self.store.quota_live_signal(self.lease.run_id, owner,
                self.lease.epoch if epoch is None else epoch, attempt, account,
                estimate=estimate, **kwargs)
        return journal

    def test_durable_tokens_restart_reset_and_frozen_conversion(self):
        estimate = {"account_ref": "account", "estimate": {"model": "admitted-model"},
                    "calibration": {"five_hour": 2, "weekly": 4}}
        journal = self.live(estimate=estimate)
        def signal(n):
            return {"tokens": {"input_tokens": n, "cached_input_tokens": 0, "output_tokens": 0}}
        with patch.object(inflight.pricing, "equivalent_cost",
                          side_effect=lambda model, tokens: {"usd": tokens["input"]}) as cost:
            first = journal(source="codex", sequence=2, signal=signal(12))
            self.assertEqual(first["high_water"], {"five_hour": 6, "weekly": 3})
            self.assertEqual(cost.call_args.args[0], "admitted-model")
            self.store._conn.close()
            self.store = run_store.TaskStore(str(self.root / "tasks.db"))
            for seq in (1, 2):
                self.assertFalse(journal(source="codex", sequence=seq, signal=signal(99))["accepted"])
            reset = journal(source="codex", sequence=3, signal=signal(2))
            self.assertEqual(reset["high_water"], {"five_hour": 7, "weekly": 3.5})
            next_row = journal(source="codex", sequence=4, signal=signal(4))
            self.assertEqual(next_row["high_water"], {"five_hour": 8, "weekly": 4})
        self.assertEqual(self.live(account="other")()["high_water"], {})
        self.assertEqual(self.live(attempt="developer-2")()["sequences"], {})
        with self.assertRaises(run_store.TaskStoreError):
            self.live(estimate=dict(estimate, calibration={}))()
        self.assertEqual(self.store._get_durable_run(self.lease.run_id).accepted_checkpoint, "")

    def test_durable_signal_fences_and_atomic_validation(self):
        journal = self.live()
        journal(source="measured", sequence=1, signal={"spent": {"weekly": 3}})
        for journal_bad in (self.live(owner="stale"), self.live(epoch=self.lease.epoch + 1)):
            with self.assertRaises(run_store.TaskStoreError):
                journal_bad(source="measured", sequence=2, signal={"spent": {"weekly": 90}})
        with self.assertRaises(ValueError):
            journal(source="measured", sequence=2, signal={"spent": {"weekly": -1}})
        self.assertEqual(journal()["sequences"], {"measured": 1})
        self.now += 601
        with self.assertRaises(run_store.TaskStoreError):
            journal(source="measured", sequence=2, signal={"spent": {"weekly": 90}})

    def test_missing_calibration_preserves_unknown_both_windows(self):
        with patch.object(inflight.pricing, "equivalent_cost", return_value={"usd": 8}):
            row = self.live(estimate={"estimate": {"model": "admitted"},
                                     "calibration": {"five_hour": 2}})(
                source="codex", sequence=1, signal={"tokens": {
                    "input_tokens": 8, "cached_input_tokens": 0, "output_tokens": 0}})
        self.assertTrue(row["uncertain"])
        self.assertEqual(row["high_water"], {"five_hour": 4, "weekly": None})
        decision = inflight.projection(self.evidence(10), self.need(), reservation_id="own",
                                       spent=row["high_water"], now=self.now)
        self.assertEqual(decision["blocking_windows"], ["weekly"])
        with patch.object(inflight.pricing, "equivalent_cost", return_value={"usd": None}):
            row = self.live(attempt="unknown-model")(source="codex", sequence=1,
                signal={"tokens": {"input_tokens": 8, "cached_input_tokens": 0, "output_tokens": 0}})
        self.assertEqual(row["high_water"], {"five_hour": None, "weekly": None})

    def test_durable_claude_pressure_and_restart_threshold(self):
        journal = self.live()
        control = inflight.CooperativeQuotaCheckpoint(checkpoint_id="cp-1", journal=self.journal,
            request=lambda cp: self.events.append(("request", self.now)), verify=lambda p: True,
            stop=lambda cp: True, clock=lambda: self.now, signals=journal)
        self.assertEqual(control.tick(self.evidence(10), self.need(), [], reservation_id="own"), "RUNNING")
        for sequence, window in enumerate(("five_hour", "seven_day")):
            control.observe_signal("claude", sequence, {"rate_limit": {
                "window": window, "utilization": .8, "status": "allowed_warning"}})
        restarted = inflight.CooperativeQuotaCheckpoint(checkpoint_id="cp-1", journal=self.journal,
            request=lambda cp: self.events.append(("request", self.now)), verify=lambda p: True,
            stop=lambda cp: True, clock=lambda: self.now, signals=journal)
        self.assertEqual(restarted.pressure, {"five_hour": 80, "weekly": 80})
        self.assertEqual(restarted.tick(self.evidence(10), self.need(), [], reservation_id="own"), "REQUESTED")

    def test_refresh_does_not_double_count_observed_local_spend(self):
        anchor = self.evidence(50)
        fresh = self.evidence(70)
        verdict = inflight.projection(fresh, self.need(), reservation_id="own",
            spent={"weekly": 20}, now=self.now, anchor=anchor)
        self.assertEqual(verdict["decision"], "ok")  # 70 + remaining 5, not 70 + 25
        crossed = inflight.projection(self.evidence(89), self.need(), reservation_id="own",
            spent={"weekly": 20}, now=self.now, anchor=anchor)
        self.assertEqual(crossed["blocking_windows"], ["weekly"])
        for window in ("five_hour", "weekly"):
            evidence = self.evidence(10)
            self.assertEqual(inflight.projection(evidence, self.need(), reservation_id="own",
                spent={window: 81}, now=self.now)["blocking_windows"], [window])

    def test_native_fake_stream_signals(self):
        items = []
        codex = CodexJsonl(items.append)
        frames = [{"type": "thread.started", "thread_id": "t"}, {"type": "turn.started"},
                  {"type": "token_count", "info": {"total_token_usage": {
                      "input_tokens": 12, "cached_input_tokens": 2, "output_tokens": 3}}}]
        for frame in frames:
            codex.feed((json.dumps(frame) + "\n").encode())
        self.assertEqual(items[-1]["tokens"]["input_tokens"], 12)
        self.assertIsNone(codex.turn.usage)  # no duplicate settlement observation
        claude = ClaudeStreamJson(items.append)
        claude.feed((json.dumps({"type": "rate_limit_event", "rate_limit_info": {
            "status": "allowed_warning", "rateLimitType": "seven_day", "utilization": .9}}) + "\n").encode())
        self.assertEqual(items[-1]["rate_limit"]["window"], "seven_day")
