"""ModelReview reviewer RPC intent journal (#1191): fake providers only.

The reviewer call is reserved once per consumer execution in the accepted
external-operation journal. Post-intent crashes, lost replies and post-reply
persistence errors park the task as BLOCKED with the journal PENDING; they never
call the reviewer twice. These are provider-free fakes and do not prove real
reboot or billing behaviour.
"""
from dataclasses import asdict
import json
import sqlite3
import threading
import time

import pytest

from test_goal_functional_checks import goal_checks
from test_model_review_execution import review_setup, run_review, evidence, REJECT, Reviewer
from test_model_review_toolless import toolless, run as run_toolless
from test_functional_execution import durable
from test_external_operation_invariants import _make_store, _leased_task, _record, _rows
from reverse_agent.platform_v1 import model_review, durable_execution, artifact_handoff, model_review_transport as transport
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStoreError


@pytest.fixture(params=["native", "toolless"])
def harness(request, review_setup):
    store, router, _, consumer, created, options, root = review_setup
    if request.param == "native":
        return {"store": store, "consumer": consumer, "options": options, "kind": "native",
                "run": lambda: run_review(review_setup),
                "service": lambda: durable(store, router),
                "calls": lambda: sum(len(item.calls) for item in created)}
    s = request.getfixturevalue("toolless")
    return {"store": store, "consumer": consumer, "options": options, "kind": "toolless", "state": s,
            "run": lambda: run_toolless(s), "service": lambda: s["service"],
            "calls": lambda: len(s["calls"])}


def journal(store, consumer):
    key = model_review.rpc_intent_key(store.get_task(consumer).execution_id)
    return [dict(row) for row in store._conn.execute(
        "SELECT * FROM durable_external_operations WHERE idempotency_key = ? ORDER BY created_at",
        (key,)).fetchall()]


def crash_at(monkeypatch, seam):
    original = durable_execution._check_crash_seam
    def crash(checkpoint):
        if checkpoint == seam:
            raise durable_execution._CrashSimulated(checkpoint)
        return original(checkpoint)
    monkeypatch.setattr(durable_execution, "_check_crash_seam", crash)
    return original


def crash_and_resume(h, monkeypatch, seam, before_resume=None):
    original = crash_at(monkeypatch, seam)
    with pytest.raises(durable_execution._CrashSimulated):
        h["run"]()
    monkeypatch.setattr(durable_execution, "_check_crash_seam", original)
    calls = h["calls"]()
    if before_resume:
        before_resume()
    store = h["store"]
    now = int(time.time() * 1000)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?", (now - 10000, h["consumer"]))
    service = h["service"]()
    service.reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    return calls, service.resume_single(h["consumer"], lease_owner="review-restart")


def assert_blocked(h, result, marker=""):
    task = h["store"].get_task(h["consumer"])
    assert not result.success and result.failure_classification == "model_review_completion_unknown", result
    assert task.status == "BLOCKED" and task.failure_classification == "blocked"
    assert task.failure_detail.startswith("model_review_completion_unknown:" + marker)
    assert "not replayed" in task.failure_detail


def assert_parked(h, result, marker=""):
    assert_blocked(h, result, marker)
    assert not evidence(h["store"], h["consumer"])


def escalate(h):
    """Run the real GoalService retry path that replaces FAILED review attempts."""
    store = h["store"]
    control = PlatformControlStore(store)
    goal_id = control.goal_id_for_task(h["consumer"])
    store._conn.execute("UPDATE platform_goals SET orchestration_mode = 'agent_team' WHERE id = ?", (goal_id,))
    store._conn.execute("UPDATE platform_autonomous_windows SET max_retries = 10")
    def resolver(plan, **kwargs):
        return dict(executor_kind="codex", binding_ref="local-test-binding", model_id="local/test",
                    reason="provider-free fixture")
    before = [link["task_id"] for link in control.list_goal_tasks(goal_id)]
    replacements = GoalService(store=store, control_store=control,
                               task_resolver=resolver).escalate_failed_tasks(goal_id)
    return replacements, before, [link["task_id"] for link in control.list_goal_tasks(goal_id)]


def assert_no_replacement(h):
    calls = h["calls"]()
    replacements, before, after = escalate(h)
    assert replacements == () and after == before
    assert h["calls"]() == calls == 1


@pytest.mark.parametrize("seam,calls_before", [("MODEL_REVIEW_AFTER_INTENT", 0),
    ("MODEL_REVIEW_AFTER_CALL", 1), ("MODEL_REVIEW_BEFORE_EVIDENCE", 1)])
def test_post_intent_crash_parks_without_second_call(harness, monkeypatch, seam, calls_before):
    calls, result = crash_and_resume(harness, monkeypatch, seam)
    assert calls == calls_before
    assert_parked(harness, result)
    assert "may have been dispatched" in harness["store"].get_task(harness["consumer"]).failure_detail
    assert harness["calls"]() == calls_before
    rows = journal(harness["store"], harness["consumer"])
    assert len(rows) == 1 and rows[0]["state"] == "PENDING" and rows[0]["operation_key"] == "model_review_rpc"
    assert "fake-lease" not in json.dumps(rows[0])  # no credential in the receipt


def test_before_call_crash_executes_exactly_once_on_resume(harness, monkeypatch):
    calls, result = crash_and_resume(harness, monkeypatch, "MODEL_REVIEW_BEFORE_CALL")
    assert calls == 0 and result.success, result
    assert harness["calls"]() == 1 and len(evidence(harness["store"], harness["consumer"])) == 1
    rows = journal(harness["store"], harness["consumer"])
    assert len(rows) == 1 and rows[0]["state"] == "SUCCESS" and rows[0]["result_state"] == "success"


def test_after_evidence_crash_reconciles_saved_response(harness, monkeypatch):
    calls, result = crash_and_resume(harness, monkeypatch, "MODEL_REVIEW_AFTER_EVIDENCE")
    assert result.success, result
    assert calls == 1 and harness["calls"]() == 1
    rows = journal(harness["store"], harness["consumer"])
    record = json.loads(evidence(harness["store"], harness["consumer"])[0]["detail"])
    assert len(rows) == 1 and rows[0]["state"] == "SUCCESS"
    assert rows[0]["external_operation_id"] == record["request_id"]


def test_successful_replay_keeps_terminal_receipt(harness):
    assert harness["run"]().success
    before = journal(harness["store"], harness["consumer"])
    assert len(before) == 1 and before[0]["state"] == "SUCCESS"
    assert harness["service"]().resume_single(harness["consumer"]).success
    assert harness["calls"]() == 1 and journal(harness["store"], harness["consumer"]) == before


def test_historical_v1_review_without_journal_replays_unchanged(harness):
    store, consumer = harness["store"], harness["consumer"]
    assert harness["run"]().success
    store._conn.execute("DELETE FROM durable_external_operations WHERE idempotency_key = ?",
                        (model_review.rpc_intent_key(store.get_task(consumer).execution_id),))
    saved = evidence(store, consumer)
    assert json.loads(saved[0]["detail"])["version"] == 1
    assert harness["service"]().resume_single(consumer).success
    assert harness["calls"]() == 1 and evidence(store, consumer) == saved
    assert journal(store, consumer) == []


def test_changed_request_scope_after_intent_is_not_replayed(harness, monkeypatch):
    changed = {**model_review.REVIEW_CHECKLIST, "version": "changed-scope"}
    calls, result = crash_and_resume(harness, monkeypatch, "MODEL_REVIEW_AFTER_INTENT",
        before_resume=lambda: monkeypatch.setattr(model_review, "REVIEW_CHECKLIST", changed))
    assert_parked(harness, result)
    assert "intent_scope_conflict" in harness["store"].get_task(harness["consumer"]).failure_detail
    assert calls == 0 and harness["calls"]() == 0
    assert [row["state"] for row in journal(harness["store"], harness["consumer"])] == ["PENDING"]


def test_saved_response_with_wrong_operation_kind_is_not_settled(harness, monkeypatch):
    store, consumer = harness["store"], harness["consumer"]
    snapshot = {}
    def retag():
        rows = journal(store, consumer)
        assert len(rows) == 1 and rows[0]["state"] == "PENDING"
        store._conn.execute("UPDATE durable_external_operations SET operation_key = ? WHERE operation_id = ?",
                            ("another-operation-kind", rows[0]["operation_id"]))
        snapshot.update(rows=journal(store, consumer), saved=evidence(store, consumer))
    calls, result = crash_and_resume(harness, monkeypatch, "MODEL_REVIEW_AFTER_EVIDENCE", before_resume=retag)
    assert_blocked(harness, result, "intent_scope_conflict")
    assert calls == 1 and harness["calls"]() == 1
    rows = journal(store, consumer)
    assert rows == snapshot["rows"] and rows[0]["state"] == "PENDING"
    assert rows[0]["operation_key"] == "another-operation-kind" and rows[0]["result_state"] in ("", None)
    assert len(snapshot["saved"]) == 1 and evidence(store, consumer) == snapshot["saved"]


def test_lost_reply_after_provider_accepted_stays_pending(harness, monkeypatch):
    if harness["kind"] == "toolless":
        s = harness["state"]
        def accepted_then_timeout(handle, body):
            s["calls"].append(body)
            raise TimeoutError()
        monkeypatch.setattr(transport, "chat", accepted_then_timeout)
    else:
        def accepted_then_lost(self, prepared, store, *, task_id, prompt):
            self.calls.append("reviewer")
            raise OSError("reply lost")
        monkeypatch.setattr(Reviewer, "execute_review_prepared", accepted_then_lost)
    result = harness["run"]()
    assert_parked(harness, result)
    assert harness["calls"]() == 1
    assert [row["state"] for row in journal(harness["store"], harness["consumer"])] == ["PENDING"]
    if harness["kind"] == "toolless":
        assert harness["state"]["released"] == [True]
    assert_no_replacement(harness)


def test_evidence_save_failure_after_reply_parks_without_replacement(harness, monkeypatch):
    store = harness["store"]
    original = store._bind_artifact_evidence
    def fail(*args, **kwargs):
        if kwargs.get("category") == model_review.CATEGORY:
            raise TaskStoreError("synthetic_evidence_write_failed")
        return original(*args, **kwargs)
    monkeypatch.setattr(store, "_bind_artifact_evidence", fail)
    result = harness["run"]()
    assert_parked(harness, result, "response_unsaved")
    assert "synthetic_evidence_write_failed" in store.get_task(harness["consumer"]).failure_detail
    assert harness["calls"]() == 1
    assert [row["state"] for row in journal(store, harness["consumer"])] == ["PENDING"]
    monkeypatch.setattr(store, "_bind_artifact_evidence", original)
    assert_no_replacement(harness)


def test_input_rebinding_failure_after_reply_parks_without_replacement(harness, monkeypatch):
    original = artifact_handoff.bind_consumer_input
    failed = []
    def fail(*args, **kwargs):
        if (not failed and harness["calls"]() == 1 and kwargs.get("lease") is not None
                and kwargs.get("allow_create") is False):
            failed.append(True)
            raise TaskStoreError("synthetic_binding_write_failed")
        return original(*args, **kwargs)
    monkeypatch.setattr(artifact_handoff, "bind_consumer_input", fail)
    result = harness["run"]()
    assert failed == [True]
    assert_parked(harness, result, "response_unsaved")
    assert harness["calls"]() == 1
    assert [row["state"] for row in journal(harness["store"], harness["consumer"])] == ["PENDING"]
    monkeypatch.setattr(artifact_handoff, "bind_consumer_input", original)
    assert_no_replacement(harness)


def test_settlement_write_failure_preserves_saved_response(harness, monkeypatch):
    store, consumer = harness["store"], harness["consumer"]
    original = store._reconcile_external_operation
    def fail(**kwargs):
        if kwargs.get("result_state") == "success":
            raise TaskStoreError("synthetic_receipt_write_failed")
        return original(**kwargs)
    monkeypatch.setattr(store, "_reconcile_external_operation", fail)
    result = harness["run"]()
    assert_blocked(harness, result, "receipt_unsettled")
    assert harness["calls"]() == 1
    saved = evidence(store, consumer)
    assert len(saved) == 1
    record = json.loads(saved[0]["detail"])
    assert record["result"] == {"verdict": "ACCEPT", "findings": []} and record["request_id"]
    rows = journal(store, consumer)
    assert len(rows) == 1 and rows[0]["state"] == "PENDING" and rows[0]["result_state"] in ("", None)
    monkeypatch.setattr(store, "_reconcile_external_operation", original)
    assert_no_replacement(harness)
    assert evidence(store, consumer) == saved and journal(store, consumer) == rows


def test_known_invalid_output_keeps_failed_contract(harness):
    if harness["kind"] == "toolless":
        harness["state"]["payload"]["choices"][0]["message"]["content"] = "not json"
    else:
        harness["options"]["response"] = "not json"
    result = harness["run"]()
    assert result.failure_classification == "model_review_invalid_output", result
    assert harness["store"].get_task(harness["consumer"]).status == "FAILED"
    rows = journal(harness["store"], harness["consumer"])
    assert len(rows) == 1 and rows[0]["state"] == "RECONCILED" and rows[0]["result_state"] == "failure"
    # Positive control for the no-replacement regressions: a known failed
    # review is still retried by the same GoalService path.
    replacements, before, after = escalate(harness)
    assert len(replacements) == 1 and after != before
    assert harness["calls"]() == 1


def test_saved_reject_reconciles_and_keeps_repair_contract(harness):
    if harness["kind"] == "toolless":
        harness["state"]["payload"]["choices"][0]["message"]["content"] = REJECT
    else:
        harness["options"]["response"] = REJECT
    result = harness["run"]()
    assert result.failure_classification == "model_review_rejected", result
    task = harness["store"].get_task(harness["consumer"])
    assert task.status == "FAILED" and task.failure_classification == "model_review_rejected"
    assert [row["state"] for row in journal(harness["store"], harness["consumer"])] == ["SUCCESS"]


def test_require_new_claims_once_under_concurrency(tmp_path):
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    contenders = [_make_store(tmp_path) for _ in range(4)]
    barrier = threading.Barrier(len(contenders))
    outcomes = []
    def claim(other):
        barrier.wait()
        try:
            outcomes.append(_record(other, task, lease, require_new=True).operation_id)
        except TaskStoreError as exc:
            outcomes.append(str(exc))
    threads = [threading.Thread(target=claim, args=(other,)) for other in contenders]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    won = [item for item in outcomes if item.startswith("op-")]
    assert len(won) == 1, outcomes
    assert sorted(item for item in outcomes if not item.startswith("op-")) == [
        "external_operation_already_recorded:idem-1:PENDING"] * 3
    assert [row["operation_id"] for row in _rows(store, "idem-1")] == won


def test_require_new_preserves_old_replay_and_conflict_rules(tmp_path):
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    first = _record(store, task, lease)
    # Each call builds a fresh dataclass type, so compare every field value.
    assert asdict(_record(store, task, lease)) == asdict(first)  # old callers keep exact replay
    with pytest.raises(TaskStoreError, match="external_operation_already_recorded"):
        _record(store, task, lease, require_new=True)
    with pytest.raises(TaskStoreError, match="external_operation_idempotency_conflict"):
        _record(store, task, lease, request_digest="digest-2", require_new=True)
    with pytest.raises(TaskStoreError, match="lease_fenced_external_op"):
        _record(store, task, lease, idempotency_key="idem-2", owner="stale", require_new=True)
    assert _rows(store, "idem-2") == [] and len(_rows(store, "idem-1")) == 1


def test_stale_owner_cannot_reserve_review_intent(harness, monkeypatch):
    original = crash_at(monkeypatch, "MODEL_REVIEW_BEFORE_CALL")
    with pytest.raises(durable_execution._CrashSimulated):
        harness["run"]()
    monkeypatch.setattr(durable_execution, "_check_crash_seam", original)
    store = harness["store"]
    task = store.get_task(harness["consumer"])
    run = store._conn.execute("SELECT run_id, lease_epoch FROM durable_runs WHERE task_id = ?",
                              (task.id,)).fetchone()
    from types import SimpleNamespace
    stale = SimpleNamespace(run_id=run["run_id"], owner="stale-owner", epoch=int(run["lease_epoch"]))
    with pytest.raises(TaskStoreError, match="lease_fenced_external_op"):
        model_review._claim_rpc_intent(store, task, stale, "intent")
    assert journal(store, task.id) == [] and harness["calls"]() == 0


def fail_entry_binding(h, monkeypatch, error):
    """Every consumer binding read raises before this invocation can claim an intent."""
    original = artifact_handoff.bind_consumer_input
    def fail(store, task_id, **kwargs):
        if task_id == h["consumer"]:
            raise error
        return original(store, task_id, **kwargs)
    monkeypatch.setattr(artifact_handoff, "bind_consumer_input", fail)
    return original


def unavailable_journal(monkeypatch):
    def unreadable(store, key):
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(model_review, "_journal_rows", unreadable)


@pytest.mark.parametrize("error", [TaskStoreError("synthetic_recovery_binding_read_failed"),
                                   RuntimeError("synthetic recovery entry fault")])
def test_pending_intent_survives_recovery_entry_error(harness, monkeypatch, error):
    store, consumer = harness["store"], harness["consumer"]
    snapshot = {}
    def entry_fault():
        snapshot.update(rows=journal(store, consumer))
        snapshot["bind"] = fail_entry_binding(harness, monkeypatch, error)
    calls, result = crash_and_resume(harness, monkeypatch, "MODEL_REVIEW_AFTER_CALL", before_resume=entry_fault)
    assert calls == 1
    assert_parked(harness, result, "intent_pending")
    detail = store.get_task(consumer).failure_detail
    assert "may have been dispatched" in detail and snapshot["rows"][0]["operation_id"] in detail
    assert [row["state"] for row in snapshot["rows"]] == ["PENDING"]
    assert journal(store, consumer) == snapshot["rows"]
    # The transient entry fault clears; the real retry path still creates nothing.
    monkeypatch.setattr(artifact_handoff, "bind_consumer_input", snapshot["bind"])
    assert_no_replacement(harness)
    assert journal(store, consumer) == snapshot["rows"] and not evidence(store, consumer)


def test_pending_intent_with_saved_response_survives_recovery_entry_error(harness, monkeypatch):
    store, consumer = harness["store"], harness["consumer"]
    snapshot = {}
    def entry_fault():
        snapshot.update(rows=journal(store, consumer), saved=evidence(store, consumer))
        fail_entry_binding(harness, monkeypatch, TaskStoreError("synthetic_recovery_binding_read_failed"))
    calls, result = crash_and_resume(harness, monkeypatch, "MODEL_REVIEW_AFTER_EVIDENCE", before_resume=entry_fault)
    assert calls == 1 and harness["calls"]() == 1
    assert_blocked(harness, result, "intent_pending")
    assert len(snapshot["saved"]) == 1 and evidence(store, consumer) == snapshot["saved"]
    assert [row["state"] for row in journal(store, consumer)] == ["PENDING"]
    assert journal(store, consumer) == snapshot["rows"]


def test_no_intent_entry_error_keeps_original_failure(harness, monkeypatch):
    fail_entry_binding(harness, monkeypatch, TaskStoreError("synthetic_recovery_binding_read_failed"))
    result = harness["run"]()
    task = harness["store"].get_task(harness["consumer"])
    assert not result.success and result.failure_classification == "synthetic_recovery_binding_read_failed"
    assert task.status == "FAILED" and task.failure_classification == "synthetic_recovery_binding_read_failed"
    assert harness["calls"]() == 0 and journal(harness["store"], harness["consumer"]) == []


def test_unexpected_no_intent_entry_error_keeps_dispatch_failure(harness, monkeypatch):
    fail_entry_binding(harness, monkeypatch, RuntimeError("synthetic recovery entry fault"))
    with pytest.raises(RuntimeError, match="synthetic recovery entry fault"):
        harness["run"]()
    task = harness["store"].get_task(harness["consumer"])
    assert task.status == "FAILED" and task.failure_classification == "executor_dispatch_failed"
    assert harness["calls"]() == 0 and journal(harness["store"], harness["consumer"]) == []


def test_unreadable_journal_on_recovery_entry_error_keeps_pending_ambiguity(harness, monkeypatch):
    store, consumer = harness["store"], harness["consumer"]
    snapshot = {}
    def entry_fault():
        snapshot.update(rows=journal(store, consumer))
        snapshot["bind"] = fail_entry_binding(harness, monkeypatch,
                                              TaskStoreError("synthetic_recovery_binding_read_failed"))
        unavailable_journal(monkeypatch)
    calls, result = crash_and_resume(harness, monkeypatch, "MODEL_REVIEW_AFTER_CALL", before_resume=entry_fault)
    assert calls == 1
    assert_parked(harness, result, "intent_unverifiable")
    assert "may have been dispatched" in store.get_task(consumer).failure_detail
    assert [row["state"] for row in snapshot["rows"]] == ["PENDING"] and journal(store, consumer) == snapshot["rows"]
    monkeypatch.setattr(artifact_handoff, "bind_consumer_input", snapshot["bind"])
    assert_no_replacement(harness)
    assert journal(store, consumer) == snapshot["rows"]


def test_unreadable_journal_cannot_prove_absence_or_authorize_review(harness, monkeypatch):
    fail_entry_binding(harness, monkeypatch, TaskStoreError("synthetic_recovery_binding_read_failed"))
    unavailable_journal(monkeypatch)
    result = harness["run"]()
    assert_parked(harness, result, "intent_unverifiable")
    assert harness["calls"]() == 0 and journal(harness["store"], harness["consumer"]) == []
    replacements, before, after = escalate(harness)
    assert replacements == () and after == before and harness["calls"]() == 0
