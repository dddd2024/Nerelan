"""Real ledger/feedback boundaries; no provider, credential or live store access."""
from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.multi_account import MultiAccountConfig, MultiAccountOrchestrator, dispatch
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
from reverse_agent.platform_v1.usage_ledger import task_feedback_metrics


def observation(store, task, key, *, model="claude-sonnet-5-5", status="OBSERVED", epoch=0,
                window="", input_units=1000, output_units=100, reasoning_units=0,
                cache_read_units=0, cache_write_units=0):
    store._conn.execute(
        "INSERT INTO task_usage_observations (id, task_id, window_id, claim_epoch, execution_id, role, "
        "model_id, provider_id, source_kind, source_id, status, input_units, output_units, reasoning_units, "
        "cache_read_units, cache_write_units, payload_digest, created_at) "
        "VALUES (?, ?, ?, ?, ?, 'executor', ?, 'fixture', 'fixture', ?, ?, ?, ?, ?, ?, ?, '', '')",
        (key, task.id, window, epoch, task.execution_id, model, key, status, input_units,
         output_units, reasoning_units, cache_read_units, cache_write_units))
    store._conn.commit()


@pytest.fixture
def ledger():
    store = TaskStore(":memory:")
    task = store.create_task(title="feedback", executor_kind="opencode", binding_ref="binding", repository="o/r")
    yield store, task
    store._conn.close()


@pytest.mark.parametrize("bad", ["unpriced", "partial", "unknown"])
def test_partial_prices_do_not_become_a_complete_attempt_cost(ledger, bad):
    store, task = ledger
    observation(store, task, "priced")
    if bad == "unpriced":
        observation(store, task, "bad", model="unknown-model")
    elif bad == "partial":
        observation(store, task, "bad", status="PARTIAL", input_units=None)
    else:
        observation(store, task, "bad", status="UNKNOWN", input_units=None,
                    output_units=None, reasoning_units=None, cache_read_units=None, cache_write_units=None)
    result = task_feedback_metrics(store, task.id)
    assert result["cost_units"] is None and result["cost_state"] == "UNKNOWN"
    assert result["observation_count"] == 2 and result["unpriced_observations"] == 1


def test_complete_tokens_can_be_list_priced_when_cash_is_unknown(ledger):
    store, task = ledger
    observation(store, task, "partial-cash", status="PARTIAL")
    result = task_feedback_metrics(store, task.id)
    assert result["cost_units"] > 0 and result["cost_state"] == "ESTIMATED_LIST_PRICE"
    assert result["basis"] == "list_price"


def test_zero_tokens_and_unknown_price_are_distinct(ledger):
    store, task = ledger
    observation(store, task, "zero", input_units=0, output_units=0)
    assert task_feedback_metrics(store, task.id)["cost_units"] == 0
    observation(store, task, "unpriced-zero", model="unknown-model", input_units=0, output_units=0)
    assert task_feedback_metrics(store, task.id)["cost_units"] is None


def completed_attempt(store, task, *, account="frozen-account", status="COMPLETE", state="RECONCILED"):
    control = PlatformControlStore(store)
    store._conn.execute("INSERT INTO platform_coordinator_claims VALUES (?, 'window', 'fixture', 2, 0, ?, '', '')",
                        (task.id, status))
    # No real window is activated: only the existing durable feedback schema is
    # seeded, never authority or dispatch. Production claim methods have separate tests.
    columns = {row["name"]: row for row in store._conn.execute("PRAGMA table_info(platform_budget_reservations)")}
    values = {"task_id": task.id, "window_id": "window", "claim_epoch": 2, "state": state,
              "account_ref": account, "binding_ref": "frozen-binding"}
    for name, column in columns.items():
        if name not in values and column["notnull"] and column["dflt_value"] is None:
            values[name] = 0 if column["type"] == "INTEGER" else ""
    store._conn.execute(f"INSERT INTO platform_budget_reservations ({','.join(values)}) "
                        f"VALUES ({','.join('?' for _ in values)})", tuple(values.values()))
    store._conn.commit()
    return control


def test_feedback_uses_only_the_completed_attempt_and_frozen_account(ledger, monkeypatch, tmp_path):
    store, task = ledger
    completed_attempt(store, task)
    observation(store, task, "old-attempt", model="unknown-model", epoch=1, window="window")
    observation(store, task, "current-attempt", epoch=2, window="window")
    result = task_feedback_metrics(store, task.id)
    assert result["observation_count"] == 1
    assert result["scope"] == "claim_attempt" and result["account_ref"] == "frozen-account"
    assert result["cost_units"] > 0 and result["wall_seconds"] is None
    brain = MultiAccountOrchestrator(store_path=tmp_path / "feedback.json")
    host = object.__new__(CombinedTrustedHost)
    host._task_store = store
    host._binding_account_resolver = lambda _binding: "changed-live-account"
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    monkeypatch.setattr(dispatch, "get_orchestrator", lambda *args, **kwargs: brain)
    host._report_account_feedback_to_brain(task, True)
    host._report_account_feedback_to_brain(task, True)
    assert set(brain.account_scores()) == {"frozen-account"}
    assert brain.scores.get("frozen-account").attempts == 1
    assert brain.scores.get("frozen-account").mean_wall_seconds is None


@pytest.mark.parametrize("status,state", [("ACTIVE", "ACTIVE"), ("COMPLETE", "ACTIVE"), ("COMPLETE", "invalid")])
def test_unfinished_or_invalid_settlement_does_not_train(ledger, status, state):
    store, task = ledger
    completed_attempt(store, task, status=status, state=state)
    observation(store, task, "usage", epoch=2, window="window")
    result = task_feedback_metrics(store, task.id)
    assert result["scope"] == "incomplete_claim" and result["cost_units"] is None


def test_terminal_replay_survives_restart_without_extending_quarantine(tmp_path):
    path = tmp_path / "feedback.json"
    now = [1000.0]
    first = MultiAccountOrchestrator(store_path=path, clock=lambda: now[0])
    event = dict(ok=False, failure_kind="account_abnormal", outcome_id="task:window:2")
    first.record_account_outcome("account", **event)
    saved = path.read_bytes()
    until = first.cooldowns.until("account")
    now[0] += 100
    restored = MultiAccountOrchestrator(store_path=path, clock=lambda: now[0])
    restored.record_account_outcome("account", **event)
    assert path.read_bytes() == saved
    assert restored.scores.get("account").attempts == 1
    assert restored.cooldowns.until("account") == until
    with pytest.raises(ValueError, match="conflicting"):
        restored.record_account_outcome("different-account", **event)
    assert path.read_bytes() == saved


def test_interleaved_instances_preserve_same_account_updates(tmp_path):
    path = tmp_path / "feedback.json"
    brains = [MultiAccountOrchestrator(store_path=path) for _ in range(4)]
    def feedback(index):
        brains[index % 4].record_account_outcome("account", ok=True, outcome_id=f"attempt:{index}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(feedback, range(24)))
    restored = MultiAccountOrchestrator(store_path=path)
    assert restored.scores.get("account").attempts == 24
    assert len(json.loads(path.read_text())["account_feedback"]) == 24


def test_failed_atomic_replace_neither_trains_nor_consumes_receipt(tmp_path, monkeypatch):
    path = tmp_path / "feedback.json"
    brain = MultiAccountOrchestrator(store_path=path)
    brain.record_account_outcome("account", ok=True, outcome_id="first")
    saved = path.read_bytes()
    with monkeypatch.context() as patch:
        def fail(*args):
            raise OSError("fixture storage failure")
        patch.setattr("reverse_agent.platform_v1.multi_account.evolution.os.replace", fail)
        with pytest.raises(OSError):
            brain.record_account_outcome("account", ok=False, outcome_id="second")
    assert path.read_bytes() == saved
    assert brain.scores.get("account").attempts == 1
    brain.record_account_outcome("account", ok=False, outcome_id="second")
    assert brain.scores.get("account").attempts == 2


@pytest.mark.parametrize("value", [True, float("inf"), float("nan"), -1, 10 ** 400])
def test_invalid_measurements_never_pollute_account_scores(tmp_path, value):
    brain = MultiAccountOrchestrator(store_path=tmp_path / "feedback.json")
    brain.record_account_outcome("account", ok=True, cost_units=value, wall_seconds=value)
    score = brain.scores.get("account")
    assert score.mean_cost_units is None and score.mean_wall_seconds is None
    json.dumps(brain.account_scores(), allow_nan=False)


def test_receipt_retention_is_bounded_and_disabled_persistence_stays_in_memory(tmp_path):
    path = tmp_path / "feedback.json"
    cfg = MultiAccountConfig(max_recorded_runs=2, persist_account_state=False)
    brain = MultiAccountOrchestrator(cfg, store_path=path)
    for i in range(4):
        brain.record_account_outcome("account", ok=True, outcome_id=str(i))
    assert len(brain._account_feedback_store.section("account_feedback")) == 2
    assert brain.scores.get("account").attempts == 4
    assert not path.exists()


def test_invalid_acceptance_does_not_modify_scores_or_quarantine(tmp_path):
    path = tmp_path / "feedback.json"
    brain = MultiAccountOrchestrator(store_path=path)
    with pytest.raises(ValueError, match="invalid account feedback"):
        brain.record_account_outcome("account", ok="false", outcome_id="invalid")
    assert not path.exists()
    assert brain.account_scores() == {} and brain.cooldowns.snapshot() == {}


def test_scoreboard_itself_rejects_nonfinite_samples_and_corrupt_state():
    from reverse_agent.platform_v1.multi_account.scoring import AccountScoreboard
    scores = AccountScoreboard(MultiAccountConfig(), state={
        "corrupt": {"reliability": float("nan")}, "negative": {"attempts": -1}})
    assert scores.scores() == {}
    score = scores.observe("account", ok=True, cost_units=float("inf"), wall_seconds=True)
    assert score.mean_cost_units is None and score.mean_wall_seconds is None


def test_unpriced_attempt_in_current_epoch_is_not_hidden_by_old_known_usage(ledger):
    store, task = ledger
    completed_attempt(store, task)
    observation(store, task, "old-priced", epoch=1, window="window")
    observation(store, task, "new-unknown", epoch=2, window="window", status="PARTIAL", input_units=None)
    result = task_feedback_metrics(store, task.id)
    assert result["cost_units"] is None
    assert result["observation_count"] == result["unpriced_observations"] == 1
