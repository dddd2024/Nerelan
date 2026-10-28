"""ModelReview reviewer RPC intent journal (#1191): fake providers only.

The reviewer call is reserved once per consumer execution in the accepted
external-operation journal. Post-intent crashes and lost replies park the task
as BLOCKED with the journal PENDING; they never call the reviewer twice. These
are provider-free fakes and do not prove real reboot or billing behaviour.
"""
import json
import threading
import time

import pytest

from test_goal_functional_checks import goal_checks
from test_model_review_execution import review_setup, run_review, evidence, REJECT, Reviewer
from test_model_review_toolless import toolless, run as run_toolless
from test_functional_execution import durable
from test_external_operation_invariants import _make_store, _leased_task, _record, _rows
from reverse_agent.platform_v1 import model_review, durable_execution, model_review_transport as transport
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


def assert_parked(h, result):
    task = h["store"].get_task(h["consumer"])
    assert not result.success and result.failure_classification == "model_review_completion_unknown", result
    assert task.status == "BLOCKED" and task.failure_classification == "blocked"
    assert task.failure_detail.startswith("model_review_completion_unknown:")
    assert "not replayed" in task.failure_detail
    assert not evidence(h["store"], h["consumer"])


@pytest.mark.parametrize("seam,calls_before", [("MODEL_REVIEW_AFTER_INTENT", 0),
    ("MODEL_REVIEW_AFTER_CALL", 1), ("MODEL_REVIEW_BEFORE_EVIDENCE", 1)])
def test_post_intent_crash_parks_without_second_call(harness, monkeypatch, seam, calls_before):
    calls, result = crash_and_resume(harness, monkeypatch, seam)
    assert calls == calls_before
    assert_parked(harness, result)
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
    assert _record(store, task, lease) == first  # old callers keep exact replay
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
