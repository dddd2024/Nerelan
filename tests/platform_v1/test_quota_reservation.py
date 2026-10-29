from reverse_agent.platform_v1 import quota_reservation as reservation
from reverse_agent.model_access import subscription_quota
import pytest


def evidence(source="official", at=1000, account="a"):
    return {"account_ref": account, "source": source, "observed_at": at,
            "windows": [{"window": "five_hour"}], "state": "OBSERVED"}


def test_sources_identity_and_freshness():
    result = reservation.observation("a", [evidence("cli", 1100), evidence(), evidence(account="b")], clock=lambda: 1200)
    assert result["source"] == "official"
    assert result["observed_at"] == "1970-01-01T00:16:40Z"
    assert result["eligible"]
    assert not reservation.observation("b", [evidence()], clock=lambda: 1200)["eligible"]
    assert reservation.observation("a", [evidence()], clock=lambda: 1600)["fresh"]
    assert not reservation.observation("a", [evidence()], clock=lambda: 1601)["eligible"]
    assert reservation.observation("a", [], small_task=True)["uncertain"]
    assert reservation.observation("a", [], small_task=True)["eligible"]


def test_refresh_and_fallback():
    calls = []
    def refresh(account):
        calls.append(account)
        return [evidence("cli", 2000)]
    result = reservation.observation("a", [evidence()], clock=lambda: 2000, refresh=refresh)
    assert result["source"] == "cli" and calls == ["a"]
    assert not reservation.observation("a", [evidence(at=2001)], clock=lambda: 2000)["fresh"]


def history():
    return [{"binding_ref": "b", "kind": "code", "difficulty": "easy", "ok": True,
             "tokens": {"input": n, "cache_read": n, "output": n}, "turn_count": n,
             "observed_at": "1970-01-01T00:16:40Z"} for n in range(1, 6)]


def estimate(records, **kwargs):
    return reservation.task_need(records, binding="b", kind="code", difficulty="easy",
                                 model="unknown", clock=lambda: 1000, **kwargs)


def test_percentiles_and_sparse_prior():
    need = estimate(history())
    assert need["tokens"]["input"]["median"] == 3
    assert need["tokens"]["output"]["p80"] == pytest.approx(4.2)
    assert need["tokens"]["turn_count"]["median"] == 3
    assert estimate(history()[:1])["tokens"]["input"]["median"] == 12000
    assert estimate([dict(r, binding_ref="other") for r in history()])["samples"] == 0
    assert estimate([dict(r, difficulty="hard") for r in history()])["samples"] == 0


def test_cold_start_and_calibration():
    need = estimate(history(), cold_gap=0, cold_input=10)
    assert need["cold_start"]
    assert need["tokens"]["input"]["median"] == 16
    assert need["tokens"]["cache_read"]["median"] == 0
    need = dict(need, units={"median": 2, "p80": 4}, uncertain=False)
    converted = reservation.window_need(need, "a", {"a": {"five_hour": 2, "weekly": 4}, "b": {"weekly": 99}})
    assert converted["windows"] == {"five_hour": {"median": 1, "p80": 2}, "weekly": {"median": .5, "p80": 1}}
    assert not converted["uncertain"]
    assert reservation.window_need(need, "c", {})["uncertain"]
    assert reservation.window_need(dict(need, units={"median": None}), "a", {"a": {"weekly": 4}})["uncertain"]


def test_magpie_accounts_remain_separate():
    accounts = [{"account_ref": ref, "provider": "codex", "state": "FRESH",
                 "observed_at": "1970-01-01T00:16:40Z", "windows": [
                     {"name": "five_hour", "used_percent": used}]} for ref, used in [("a", 5), ("b", 95)]]
    result = subscription_quota.magpie_account_quotas({"status": "available", "accounts": accounts}, now=1000)
    assert result["a"]["windows"][0]["used_percent"] == 5
    assert result["b"]["windows"][0]["used_percent"] == 95


def test_pricing_is_injected_through_module(monkeypatch):
    seen = []
    def cost(model, tokens):
        seen.append(tokens)
        return {"usd": tokens["input"] + tokens["output"]}
    monkeypatch.setattr(reservation.pricing, "equivalent_cost", cost)
    need = estimate(history())
    assert need["units"]["median"] == 6
    assert need["units"]["p80"] == pytest.approx(8.4)
    assert len(seen) == 2


def test_estimates_unknown_and_configured_freshness():
    ranged = evidence("estimated", 1200)
    assert reservation.observation("a", [ranged], clock=lambda: 1200)["fresh"]
    assert not reservation.observation("a", [evidence()], clock=lambda: 1011, freshness=10)["fresh"]
    assert not reservation.observation("a", [evidence("unrecognized")], clock=lambda: 1000)["eligible"]
    assert not reservation.observation("a", [dict(evidence(), observed_at="invalid")], clock=lambda: 1000)["eligible"]


def quota_evidence(used=20, weekly=20, now=1000):
    return dict(evidence(at=now), windows=[
        {"window": "five_hour", "used_percent": used, "resets_at": now + 1000},
        {"window": "weekly", "used_percent": weekly, "resets_at": now + 2000}])


def quota_need(value=40):
    return {"windows": {name: {"p80": value} for name in ("five_hour", "weekly")}}


def test_weekly_buffer_and_october_19_replay():
    assert reservation.admission(quota_evidence(weekly=90), quota_need(), now=1000)["blocking_windows"] == ["weekly"]
    replay = reservation.admission(quota_evidence(used=90), quota_need(5), now=1000)
    assert replay["decision"] == "quota_wait"
    assert replay["until"] == "1970-01-01T00:33:20Z"
    assert reservation.admission(quota_evidence(), quota_need(65), now=1000, buffer=15)["decision"] == "ok"


def test_unknown_small_bounds_and_reset_do_not_invent_usage():
    assert reservation.admission(quota_evidence(), quota_need(), now=3001)["state"] == "UNKNOWN"
    assert reservation.admission(quota_evidence(), quota_need(), now=3001)["decision"] == "quota_wait"
    assert reservation.admission(quota_evidence(), quota_need(.5), now=3001, small_task=True)["state"] == "UNKNOWN"
    assert reservation.admission(quota_evidence(), quota_need(2), now=3001, small_task=True)["decision"] == "quota_wait"


def test_completed_usage_is_not_counted_twice_but_unknown_is_retained():
    row = {"account_ref": "a", "quota_windows": {"five_hour": 50, "weekly": 50},
           "state": "RECONCILED", "reconciled_at": "1970-01-01T00:16:39Z"}
    assert reservation.admission(quota_evidence(), quota_need(30), [row], now=1000)["decision"] == "ok"
    # Unknown spend stays held against an estimate taken after completion ...
    estimated = dict(quota_evidence(), source="estimated")
    assert reservation.admission(estimated, quota_need(30), [dict(row, state="UNKNOWN")], now=1000)["decision"] == "quota_wait"
    assert reservation.admission(estimated, quota_need(30), [dict(row, quota_state="UNKNOWN")], now=1000)["decision"] == "quota_wait"
    # ... but a provider-reported percentage taken after completion already includes it.
    assert reservation.admission(quota_evidence(), quota_need(30), [dict(row, state="UNKNOWN")], now=1000)["decision"] == "ok"
    # Before completion (or still running) it is always held.
    late = dict(row, state="UNKNOWN", reconciled_at="1970-01-01T00:16:41Z")
    assert reservation.admission(quota_evidence(), quota_need(30), [late], now=1000)["decision"] == "quota_wait"
    assert reservation.admission(quota_evidence(), quota_need(30), [dict(row, state="ACTIVE")], now=1000)["decision"] == "quota_wait"


def test_atomic_account_reservation_separate_connections(tmp_path):
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor
    from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    from reverse_agent.platform_v1.autonomy import AutonomyService
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    from tests.platform_v1.test_unattended_coordinator import _budget_window
    db = str(tmp_path / "quota.sqlite3")
    first = TaskStore(db)
    ca = PlatformControlStore(first)
    service = AutonomyService(control_store=ca, capabilities=CapabilityRegistry())
    wa = _budget_window(service, policy_id="quota-a", max_tokens=0, reservation=0)
    wb = wa
    tasks = [first.create_task(title=str(i), executor_kind="opencode", binding_ref=f"binding-{i}") for i in range(2)]
    second = TaskStore(db)
    cb = PlatformControlStore(second)
    for control, task in zip((ca, cb), tasks):
        control.prepare_quota_admission(task_id=task.id, binding_ref=task.binding_ref, account_ref="a",
            evidence=quota_evidence(now=time.time()), need=quota_need())
    barrier = threading.Barrier(2)
    def claim(args):
        control, task, window = args
        barrier.wait(timeout=5)
        try:
            return control.claim_task(window_id=window.id, task_id=task.id, owner="test", lease_ms=60000)[0]
        except TaskStoreError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, [(ca, tasks[0], wa), (cb, tasks[1], wb)]))
    assert sum(isinstance(r, int) for r in results) == 1
    assert sum(str(r).startswith("QUOTA_WAIT:") for r in results) == 1
    assert first._conn.execute("SELECT COUNT(*) FROM platform_budget_reservations WHERE state='ACTIVE'").fetchone()[0] == 1

    winner = results.index(1)
    winner_task = tasks[winner]
    with first._conn:
        first._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?", (winner_task.id,))
    epoch, _ = ca.claim_task(window_id=wa.id, task_id=winner_task.id, owner="retry", lease_ms=60000)
    assert epoch == 2
    assert first._conn.execute("SELECT COUNT(*) FROM platform_budget_reservations WHERE state='ACTIVE'").fetchone()[0] == 1

    held = tasks[1 - winner]
    hold = first._conn.execute("SELECT verdict_json FROM platform_quota_admissions WHERE task_id=?", (held.id,)).fetchone()[0]
    import json
    assert json.loads(hold)["decision"] == "quota_wait"
    ca.prepare_quota_admission(task_id=held.id, binding_ref=held.binding_ref, account_ref="a",
        evidence=quota_evidence(used=0, weekly=0, now=time.time()), need=quota_need())
    assert ca.claim_task(window_id=wa.id, task_id=held.id, owner="after-refresh", lease_ms=60000)[0] == 1
    assert ca._conn.execute("SELECT COUNT(*) FROM platform_budget_reservations WHERE state='ACTIVE'").fetchone()[0] == 2
    assert first.active_quota_reservation(held.id)["account_ref"] == "a"


# Durable, provider-free Phase B settlement fixtures.
def settled_store(tmp_path, monkeypatch):
    import time
    from reverse_agent.platform_v1 import control_store
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.autonomy import AutonomyService
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    from tests.platform_v1.test_unattended_coordinator import _budget_window
    store = TaskStore(str(tmp_path / "settlement.sqlite3"))
    control = control_store.PlatformControlStore(store)
    window = _budget_window(AutonomyService(control_store=control, capabilities=CapabilityRegistry()),
                            policy_id="settlement", max_tokens=0, reservation=0)
    monkeypatch.setattr(control_store, "_utc_now", lambda: "2026-10-20T14:01:00Z")
    return store, control, window


def measured_claim(store, control, window, n=10):
    import time
    task = store.create_task(title="measured", executor_kind="opencode", binding_ref="b")
    need = estimate(history())
    converted = reservation.window_need(need, "a", {"a": {"five_hour": 1, "weekly": 2}})
    # Deliberately large reservation; actual is measured independently.
    converted["windows"] = quota_need(10)["windows"]
    control.prepare_quota_admission(task_id=task.id, binding_ref="b", account_ref="a",
        evidence=quota_evidence(now=time.time()), need=converted)
    epoch, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="owner", lease_ms=60000)
    append_measurement(store, task, n, f"obs-{task.id}")
    return task, epoch


def append_measurement(store, task, n, identity, status="OBSERVED"):
    metrics = {} if status == "UNKNOWN" else dict(input_units=n, cache_read_units=n,
        cache_write_units=0, output_units=n, reasoning_units=0, cost_micro_units=n * 1000000)
    return store.append_usage_observation(task.id, observation_id=identity, execution_id="exec-test",
        role="coder", model_id="m", provider_id="p", source_kind="assistant_message", source_id=identity,
        status=status, **metrics)


def test_settlement_restart_replay_and_failed_spend(tmp_path, monkeypatch):
    import json
    from reverse_agent.platform_v1 import control_store
    from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
    store, control, window = settled_store(tmp_path, monkeypatch)
    task, epoch = measured_claim(store, control, window, 2)
    control.abandon_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, reason="cancelled")
    row = dict(store._conn.execute("SELECT * FROM platform_budget_reservations").fetchone())
    assert row["observed_token_units"] == 6
    assert json.loads(row["settlement_json"])["actual_windows"] == {"five_hour": 2, "weekly": 1}
    reopened = TaskStore(str(tmp_path / "settlement.sqlite3"))
    recovered = control_store.PlatformControlStore(reopened)
    with pytest.raises(TaskStoreError, match="coordinator_claim_fenced"):
        recovered.abandon_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, reason="cancelled")
    assert reopened._conn.execute("SELECT COUNT(*) FROM platform_usage_charges").fetchone()[0] == 1
    summary = recovered.window_budget_summary(window.id)["accounts"]["a"]
    assert summary["reserved"]["five_hour"] == 10
    assert summary["actual"]["five_hour"] == 2
    assert summary["estimate_error"]["five_hour"] == -8
    assert recovered.get_window(window.id).observed_token_units == 6


def test_incomplete_observation_stays_unknown(tmp_path, monkeypatch):
    import json
    store, control, window = settled_store(tmp_path, monkeypatch)
    task, epoch = measured_claim(store, control, window)
    append_measurement(store, task, 0, "unresolved", "UNKNOWN")
    control.abandon_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, reason="failure")
    row = dict(store._conn.execute("SELECT * FROM platform_budget_reservations").fetchone())
    assert row["state"] == "UNKNOWN" and row["observed_token_units"] is None
    assert json.loads(row["settlement_json"])["tokens"]["input"] is None
    assert control.window_budget_summary(window.id)["accounts"]["a"]["actual"]["five_hour"] is None
    assert row["quota_windows_json"] != "{}"


def test_retry_charges_each_observation_once(tmp_path, monkeypatch):
    store, control, window = settled_store(tmp_path, monkeypatch)
    task, epoch = measured_claim(store, control, window, 2)
    store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?", (task.id,))
    store.set_state(task.id, "INTERRUPTED")
    retry, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="retry", lease_ms=60000)
    assert retry == epoch + 1
    # Replay prior execution plus one new model turn after a crash/retry.
    append_measurement(store, task, 2, f"obs-{task.id}")
    append_measurement(store, task, 3, "retry-observation")
    control.complete_task_claim(window_id=window.id, task_id=task.id, owner="retry", epoch=retry, result="done")
    assert control.get_window(window.id).observed_token_units == 15
    assert store._conn.execute("SELECT COUNT(*) FROM platform_usage_charges").fetchone()[0] == 2


def test_persisted_measurements_update_p80(tmp_path, monkeypatch):
    from reverse_agent.platform_v1.usage_ledger import estimation_records
    from reverse_agent.platform_v1 import control_store
    from reverse_agent.platform_v1.run_store import TaskStore
    store, control, window = settled_store(tmp_path, monkeypatch)
    for n in range(1, 6):
        task, epoch = measured_claim(store, control, window, n)
        # Refresh precedes each new execution in this synthetic clock.
        store._conn.execute("UPDATE platform_budget_reservations SET reconciled_at='1970-01-01T00:00:01Z' WHERE state<>'ACTIVE'")
        control.abandon_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, reason="failed-after-spend")
    reopened = TaskStore(str(tmp_path / "settlement.sqlite3"))
    control_store.PlatformControlStore(reopened)
    records = estimation_records(reopened)
    learned = reservation.task_need(records, binding="b", kind="code", difficulty="easy", model="unknown",
        clock=lambda: 1792504860)
    assert learned["samples"] == 5
    assert learned["tokens"]["output"]["p80"] == pytest.approx(4.2)
    assert learned["tokens"]["turn_count"]["p80"] == 1
    assert learned["tokens"]["input"]["p80"] < estimate([])["tokens"]["input"]["p80"]


def test_settled_actual_is_held_until_later_observation():
    row = {"account_ref": "a", "state": "RECONCILED", "quota_state": "ESTIMATED",
        "reconciled_at": "1970-01-01T00:16:41Z", "quota_windows": {"five_hour": 50, "weekly": 50},
        "actual_windows": {"five_hour": 65, "weekly": 65}}
    assert reservation.admission(quota_evidence(), quota_need(10), [row], now=1000)["decision"] == "quota_wait"
    assert reservation.admission(quota_evidence(now=1002), quota_need(10), [row], now=1002)["decision"] == "ok"
    later_estimate = dict(quota_evidence(now=1002), source="estimated")
    assert reservation.admission(later_estimate, quota_need(30), [dict(row, state="UNKNOWN")], now=1002)["decision"] == "quota_wait"
    assert reservation.admission(quota_evidence(now=1002), quota_need(30), [dict(row, state="UNKNOWN")], now=1002)["decision"] == "ok"


def test_calibration_requires_explicit_attribution_and_stable_window():
    before = quota_evidence(now=1000)
    after = quota_evidence(used=30, weekly=25, now=1100)
    for old, new in zip(before["windows"], after["windows"]):
        old["resets_at"] = new["resets_at"] = "1970-01-01T01:00:00Z"
    rows = [{"account_ref": "a", "created_at": "1970-01-01T00:16:41Z",
        "reconciled_at": "1970-01-01T00:17:00Z", "settlement": {"cost_units": 20, "observation_ids": ["o"]}}]
    assert reservation.attributable_calibration(before, after, rows) == {}
    after["attributed_observation_ids"] = ["o"]
    # Use normalized persisted timestamps, as the observation selector does.
    before = reservation.observation("a", [before], clock=lambda: 1000)
    after = reservation.observation("a", [after], clock=lambda: 1100)
    assert reservation.attributable_calibration(before, after, rows) == {"five_hour": 2, "weekly": 4}
    assert reservation.attributable_calibration(before, dict(after, account_ref="b"), rows) == {}
    after["windows"][0]["resets_at"] = "1970-01-01T02:00:00Z"
    assert reservation.attributable_calibration(before, after, rows) == {"weekly": 4}


def test_partial_native_counters_never_imply_zero_cost(tmp_path, monkeypatch):
    import json
    store, control, window = settled_store(tmp_path, monkeypatch)
    task, epoch = measured_claim(store, control, window)
    store._conn.execute("DELETE FROM task_usage_observations WHERE task_id=?", (task.id,))
    store.append_usage_observation(task.id, observation_id="native", execution_id="exec-native", role="executor",
        model_id="m", provider_id="p", source_kind="native_summary", source_id="native", status="PARTIAL",
        input_units=100, cache_read_units=50, output_units=20)
    control.abandon_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, reason="cancelled")
    fact = json.loads(store._conn.execute("SELECT settlement_json FROM platform_budget_reservations").fetchone()[0])
    assert fact["tokens"]["input"] == 100 and fact["tokens"]["output"] == 20
    assert fact["tokens"]["cache_write"] is None and fact["cost_units"] is None
    assert fact["turn_count"] is None and fact["state"] == "UNKNOWN"


def test_calibration_evidence_survives_restart(tmp_path, monkeypatch):
    import json
    import time
    from reverse_agent.platform_v1 import control_store
    from reverse_agent.platform_v1.run_store import TaskStore
    store, control, window = settled_store(tmp_path, monkeypatch)
    task, epoch = measured_claim(store, control, window, 20)
    control.abandon_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, reason="usage_limit")
    now = time.time()
    iso = reservation.quota_forecast.iso
    before = quota_evidence(now=now-100)
    after = quota_evidence(used=30, weekly=25, now=now)
    for old, new in zip(before["windows"], after["windows"]):
        old["resets_at"] = new["resets_at"] = now+1000
    after["attributed_observation_ids"] = [f"obs-{task.id}"]
    store._conn.execute("UPDATE platform_budget_reservations SET created_at=?, reconciled_at=?", (iso(now-90), iso(now-20)))
    store._conn.execute("UPDATE platform_quota_observations SET observed_at=?, evidence_json=?",
        (iso(now-100), json.dumps(dict(before, observed_at=iso(now-100)))))
    control.prepare_quota_admission(task_id=task.id, binding_ref="b", account_ref="a", evidence=after, need=quota_need())
    assert control.quota_calibration("a") == {"five_hour": 2, "weekly": 4}
    reopened = control_store.PlatformControlStore(TaskStore(str(tmp_path / "settlement.sqlite3")))
    assert reopened.quota_calibration("a") == control.quota_calibration("a")
    assert reopened.window_budget_summary(window.id)["accounts"]["a"]["limit_cutoff_count"] == 1
    persisted = reopened._conn.execute("SELECT evidence_json FROM platform_quota_calibrations").fetchone()[0]
    assert json.loads(persisted)["after"]["attributed_observation_ids"] == [f"obs-{task.id}"]


def test_accounts_include_tasks_held_before_first_claim(tmp_path, monkeypatch):
    import time
    from reverse_agent.platform_v1.run_store import TaskStoreError
    store, control, window = settled_store(tmp_path, monkeypatch)
    task = store.create_task(title="held", executor_kind="opencode", binding_ref="held-binding")
    control.prepare_quota_admission(task_id=task.id, binding_ref="held-binding", account_ref="a",
        evidence=quota_evidence(used=99, now=time.time()), need=quota_need())
    with pytest.raises(TaskStoreError, match="QUOTA_WAIT"):
        control.claim_task(window_id=window.id, task_id=task.id, owner="owner", lease_ms=60000)
    assert control.window_budget_summary(window.id)["accounts"]["a"]["quota_held_tasks"] == 1


def test_refresh_between_turns_absorbs_only_earlier_measured_spend():
    row = {"account_ref": "a", "state": "RECONCILED", "quota_state": "ESTIMATED",
        "reconciled_at": "1970-01-01T00:17:00Z", "quota_windows": {"five_hour": 70, "weekly": 70},
        "actual_windows": {"five_hour": 65, "weekly": 65}, "actual_observations": [
            {"observed_at": "1970-01-01T00:16:39Z", "windows": {"five_hour": 60, "weekly": 60}},
            {"observed_at": "1970-01-01T00:16:41Z", "windows": {"five_hour": 5, "weekly": 5}}]}
    assert reservation.admission(quota_evidence(), quota_need(10), [row], now=1000)["decision"] == "ok"
    # An unresolved execution retains the entire reservation, even after refresh.
    assert reservation.admission(quota_evidence(), quota_need(10), [dict(row, state="UNKNOWN")], now=1000)["decision"] == "quota_wait"


def forecast_task(identity, amount=30, account="a", binding="b"):
    return {"task_id": identity, "binding_ref": binding, "account_ref": account,
            "need": dict(quota_need(amount), uncertain=True)}


def test_goal_fit_cumulative_shared_account_and_weekly_bottleneck():
    tasks = [forecast_task("T1", binding="b1"), forecast_task("T2", binding="b2")]
    before = repr(tasks)
    evidence = {"a": quota_evidence(weekly=40)}
    result = reservation.goal_fit(tasks, evidence, now=1000)
    assert result["status"] == "needs_a_reset"
    assert result["accounts"]["a"]["need"]["windows"]["weekly"]["p80"] == 60
    assert result["accounts"]["a"]["blocking_windows"] == ["weekly"]
    assert result["accounts"]["a"]["until"] == "1970-01-01T00:50:00Z"
    assert all(reservation.goal_fit([t], evidence, now=1000)["status"] == "fits_now" for t in tasks)
    assert result["uncertain"] and result["forecast_only"] and not result["availability_guaranteed"]
    assert repr(tasks) == before


def test_goal_fit_outstanding_and_alternative_model():
    tasks = [forecast_task("T1"), forecast_task("T2")]
    outstanding = [{"account_ref": "a", "state": "ACTIVE", "quota_windows": {"five_hour": 20, "weekly": 20}}]
    evidence = {"a": quota_evidence(), "other": dict(quota_evidence(), account_ref="other")}
    result = reservation.goal_fit(tasks, evidence, outstanding, now=1000,
                                 alternatives=[forecast_task("T2", account="other", binding="other-model")])
    assert result["status"] == "needs_another_model"
    assert result["alternative"]["status"] == "fits_now"
    assert outstanding[0]["quota_windows"]["weekly"] == 20
    # Sharing another binding on the same account cannot create more capacity.
    assert reservation.goal_fit(tasks, evidence, outstanding, now=1000,
        alternatives=[forecast_task("T2", binding="same-account")])["status"] == "needs_a_reset"


@pytest.mark.parametrize("change", ["missing", "stale", "reset", "calibration"])
def test_goal_fit_never_reports_unknown_as_observed_fit(change):
    evidence = {"a": quota_evidence()}
    task = forecast_task("T1", .5)
    if change == "missing":
        evidence = {}
    elif change == "stale":
        evidence["a"]["observed_at"] = "1970-01-01T00:00:01Z"
    elif change == "reset":
        evidence["a"]["windows"][0]["resets_at"] = 999
    else:
        task["need"]["windows"]["weekly"]["p80"] = None
    result = reservation.goal_fit([task], evidence, now=1000)
    assert result["status"] == "UNKNOWN" and result["uncertain"]
    assert result["accounts"]["a"]["state"] == "UNKNOWN"


def test_goal_fit_demand_exceeding_a_whole_window_needs_another_model():
    result = reservation.goal_fit([forecast_task("T1", 50), forecast_task("T2", 50)],
                                  {"a": quota_evidence()}, now=1000)
    assert result["status"] == "needs_another_model"


def magpie_codex(now, used=9, weekly=22):
    # Shape produced by subscription_quota.magpie_quota_windows (2026-10-21 live snapshot).
    return {"state": "OBSERVED", "provenance": "EXTERNAL_MAGPIE", "source": "magpie", "observed_at": now - 300,
            "account_ref": "acct", "windows": [
                {"window": "5 hours", "basis": "official_percent", "used_percent": used, "resets_at": now + 3600},
                {"window": "7 days", "basis": "official_percent", "used_percent": weekly, "resets_at": now + 86400}]}


def uncalibrated_need():
    need = estimate(history())
    return reservation.window_need(dict(need, units={"median": 2, "p80": 4}), "acct", {})


def test_real_window_names_and_uncalibrated_prior_admit_fresh_headroom():
    now = 10_000
    selected = reservation.observation("acct", [magpie_codex(now)], clock=lambda: now)
    assert [w["window"] for w in selected["windows"]] == ["five_hour", "weekly"]
    need = uncalibrated_need()
    assert need["windows"] == reservation.UNCALIBRATED_WINDOW_NEED
    assert need["prior_windows"] == ["five_hour", "weekly"] and need["uncertain"]
    verdict = reservation.admission(magpie_codex(now), need, now=now)
    assert verdict["decision"] == "ok", verdict


def test_uncalibrated_prior_still_holds_near_exhaustion_and_stale_evidence():
    now = 10_000
    need = uncalibrated_need()
    assert reservation.admission(magpie_codex(now, used=70), need, now=now)["blocking_windows"] == ["five_hour"]
    assert reservation.admission(magpie_codex(now, weekly=90), need, now=now)["blocking_windows"] == ["weekly"]
    stale = dict(magpie_codex(now), observed_at=now - 3600)
    assert reservation.admission(stale, need, now=now)["decision"] == "quota_wait"


def test_calibration_keyed_by_source_window_name_is_used():
    need = dict(estimate(history()), units={"median": 2, "p80": 4}, uncertain=False)
    converted = reservation.window_need(need, "a", {"a": {"5 hours": 2, "7 days": 4}})
    assert converted["windows"] == {"five_hour": {"median": 1, "p80": 2}, "weekly": {"median": .5, "p80": 1}}
    assert converted["prior_windows"] == [] and not converted["uncertain"]


def _quota_host(monkeypatch, provider, quotas, account_ref=None):
    from types import SimpleNamespace
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    host = CombinedTrustedHost.__new__(CombinedTrustedHost)
    connection = {"connection_id": "conn", "executor_provider_id": provider,
                  "auth_method": "external_cli_session", "account_ref": account_ref}
    calls = []
    host._store = SimpleNamespace(
        list_bindings_public=lambda: [{"binding_id": "bind", "connection_id": "conn", "model_id": "gpt-6.1-sol"}],
        get_connection_public=lambda _id: connection)
    host._task_store = SimpleNamespace()
    host._control_store = SimpleNamespace(quota_calibration=lambda account: {},
        prepare_quota_admission=lambda **kw: calls.append(kw))
    monkeypatch.setattr(host, "_subscription_quotas", lambda: quotas, raising=False)
    import reverse_agent.platform_v1.usage_ledger as ledger
    monkeypatch.setattr(ledger, "estimation_records", lambda store: [])
    task = SimpleNamespace(id="t", binding_ref="bind", executor_kind="codex", kind="code", difficulty=3)
    host._prepare_task_quota(task)
    return calls


def test_host_adopts_provider_observation_for_its_own_cli_login(monkeypatch):
    import time
    now = time.time()
    calls = _quota_host(monkeypatch, "codex", {"codex": magpie_codex(now), "claude-code": dict(magpie_codex(now), used=99)})
    [call] = calls
    assert call["account_ref"] == "conn" and call["evidence"]["account_ref"] == "conn"
    assert call["evidence"]["fresh"]
    assert reservation.admission(call["evidence"], call["need"])["decision"] == "ok"


def test_host_keeps_explicit_account_identity_and_skips_quota_less_sessions(monkeypatch):
    import time
    now = time.time()
    [call] = _quota_host(monkeypatch, "codex", {"codex": magpie_codex(now)}, account_ref="other-account")
    assert not call["evidence"]["fresh"]  # another account's observation is never this account's evidence
    assert _quota_host(monkeypatch, "ai", {"codex": magpie_codex(now)}) == []


def test_uncalibrated_account_keeps_admitting_sequential_tasks():
    # Review B1 on #1307: settled uncalibrated tasks (quota_state UNKNOWN) must not pile up.
    now = 10_000
    need = uncalibrated_need()
    settled = []
    for step in range(6):
        observed = now + step * 600
        evidence = dict(magpie_codex(observed), observed_at=observed - 60)
        verdict = reservation.admission(evidence, need, settled, now=observed)
        assert verdict["decision"] == "ok", (step, verdict)
        settled.append({"account_ref": "acct", "state": "UNKNOWN", "quota_state": "UNKNOWN",
                        "quota_windows": {"five_hour": 30.0, "weekly": 6.0},
                        "reconciled_at": quota_forecast_iso(observed + 300)})
    # The latest task finished after the last observation: it is still held.
    held = reservation.admission(dict(magpie_codex(now, used=50), observed_at=now + 5 * 600 - 60),
                                 need, settled, now=now + 5 * 600)
    assert held["decision"] == "quota_wait"


def quota_forecast_iso(at):
    from reverse_agent.model_access import quota_forecast
    return quota_forecast.iso(at)


def _iso(at):
    from reverse_agent.model_access import quota_forecast
    return quota_forecast.iso(at)


def _magpie(at, five, weekly, reset=50_000):
    return {"account_ref": "acct", "source": "magpie", "state": "OBSERVED", "observed_at": _iso(at),
            "windows": [{"window": "5 hours", "used_percent": five, "resets_at": _iso(reset)},
                        {"window": "7 days", "used_percent": weekly, "resets_at": _iso(reset * 10)}]}


def _settled(task_id, created, finished, units=0.8, state="UNKNOWN"):
    return {"task_id": task_id, "account_ref": "acct", "state": state, "created_at": _iso(created),
            "reconciled_at": _iso(finished) if finished else "", "settlement": {"price_units": units}}


def test_settlement_prices_measured_tokens_in_need_units():
    obs = [{"id": "o", "status": "PARTIAL", "source_kind": "native_summary", "input_units": 121186,
            "cache_read_units": 3238400, "cache_write_units": None, "output_units": 21972,
            "reasoning_units": None, "cost_micro_units": None}]
    estimate = {"estimate": {"model": "gpt-6.1-sol"}, "calibration": {}}
    fact = reservation.settlement(obs, estimate, usage_unknown=False)
    assert fact["cost_units"] is None and fact["price_units"] > 0  # never reported as spend
    # #1323: measured tokens keep their list-price price_units even when the
    # settlement stays usage-unknown; the figure only feeds delta calibration.
    assert reservation.settlement(obs, estimate, usage_unknown=True)["price_units"] > 0
    assert reservation.settlement(obs, estimate, usage_unknown=True)["state"] == "UNKNOWN"
    missing = [dict(obs[0], output_units=None)]
    assert reservation.settlement(missing, estimate, usage_unknown=False)["price_units"] is None
    assert reservation.settlement([], estimate, usage_unknown=True)["price_units"] is None


def test_isolated_task_delta_gives_a_conservative_rate():
    # 2026-10-21 shape: admitted at 52%/28%, next fresh Magpie reading 74%/32%.
    rows = [_settled("t", 1010, 1500, units=0.786)]
    rates = reservation.delta_calibration("t", _magpie(1000, 52, 28), _magpie(2000, 74, 32), rows)
    assert rates == pytest.approx({"five_hour": 0.786 / 23, "weekly": 0.786 / 5})


@pytest.mark.parametrize("change", ["overlap", "running_overlap", "reset", "no_increase", "estimated_after",
                                    "estimated_before", "unknown_before",
                                    "started_before", "finished_after", "no_units", "active"])
def test_delta_calibration_refuses_unattributable_intervals(change):
    before, after = _magpie(1000, 52, 28), _magpie(2000, 74, 32)
    rows = [_settled("t", 1010, 1500)]
    if change == "overlap":
        rows.append(_settled("other", 1400, 1600))
    elif change == "running_overlap":
        rows.append(_settled("other", 1200, None, state="ACTIVE"))
    elif change == "reset":
        after = _magpie(2000, 74, 32, reset=60_000)
    elif change == "no_increase":
        after = _magpie(2000, 52, 28)
    elif change == "estimated_after":
        after = dict(after, source="estimated")
    elif change == "estimated_before":
        before = dict(before, source="estimated")  # review B1: an overstated start shrinks the delta
    elif change == "unknown_before":
        before = dict(before, state="UNKNOWN")
    elif change == "started_before":
        rows = [_settled("t", 900, 1500)]
    elif change == "finished_after":
        rows = [_settled("t", 1010, 2500)]
    elif change == "no_units":
        rows = [_settled("t", 1010, 1500, units=None)]
    elif change == "active":
        rows = [_settled("t", 1010, 1500, state="ACTIVE")]
    assert reservation.delta_calibration("t", before, after, rows) == {}


def test_control_store_learns_each_task_once_and_uses_the_median(tmp_path, monkeypatch):
    import json
    store, control, _ = settled_store(tmp_path, monkeypatch)
    conn = store._conn
    for index, (task_id, used_before, used_after) in enumerate((("t1", 10, 20), ("t2", 20, 26), ("t3", 26, 40))):
        task = store.create_task(title=task_id, executor_kind="codex", binding_ref="b")
        start = 1000 + index * 1000
        conn.execute("INSERT OR REPLACE INTO platform_quota_admissions (task_id,binding_ref,account_ref,evidence_json,"
                     "need_json,small_task,safety_buffer) VALUES (?,?,?,?,?,?,?)",
                     (task.id, "b", "acct", json.dumps(_magpie(start, used_before, 1)), "{}", 0, 10))
        rows = [dict(_settled(task.id, start + 10, start + 500, units=1.0))]
        after = _magpie(start + 900, used_after, 1)
        with control._lock, conn:
            control._delta_calibrate_locked("acct", after, rows)
            control._delta_calibrate_locked("acct", after, rows)  # replay learns nothing new
    rates = control.quota_calibration("acct")
    # Samples 1/11, 1/7, 1/15 per pp: the median is used, weekly saw no increase.
    assert rates == pytest.approx({"five_hour": 1 / 11})
    evidence = json.loads(conn.execute("SELECT evidence_json FROM platform_quota_calibrations").fetchone()[0])
    assert len(evidence["delta_samples"]["five_hour"]) == 3 and evidence["basis"] == "provider_delta_lower_bound"
