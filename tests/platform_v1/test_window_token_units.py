"""Window token budgets are charged in cost-equivalent units (#1504).

A prompt-cache read costs about a tenth of fresh input on most providers, so
a window's ``observed_token_units`` weighs cache reads (and cache writes)
instead of summing every counter at 1. Raw counters stay untouched in
``task_usage_observations`` and in reports; unknown usage stays unknown.
"""
from __future__ import annotations

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.usage_ledger import cost_equivalent_units
from reverse_agent.platform_v1.window_report import build_report

from tests.platform_v1.test_unattended_coordinator import _budget_window


def _observation(**overrides):
    row = {
        "status": "OBSERVED",
        "source_kind": "step_finish",
        "input_units": 0,
        "cache_read_units": 0,
        "cache_write_units": 0,
        "output_units": 0,
        "reasoning_units": 0,
    }
    row.update(overrides)
    return row


def test_cache_read_is_charged_at_a_tenth_of_fresh_input():
    row = _observation(input_units=1000, cache_read_units=100_000, output_units=500)
    assert cost_equivalent_units(row) == 11_500
    assert cost_equivalent_units(row) != 101_500


def test_cache_write_is_charged_at_its_premium_weight():
    assert cost_equivalent_units(_observation(cache_write_units=400)) == 500
    assert cost_equivalent_units(_observation(input_units=1000, cache_write_units=400,
                                              output_units=500)) == 2000


def test_separately_reported_reasoning_counts_but_native_summary_is_not_double_counted():
    streamed = _observation(source_kind="assistant_message", output_units=500, reasoning_units=500)
    assert cost_equivalent_units(streamed) == 1000
    native = _observation(source_kind="native_summary", output_units=500, reasoning_units=500)
    assert cost_equivalent_units(native) == 500


def test_weight_overrides_replace_only_the_named_counters():
    row = _observation(input_units=1000, cache_read_units=100_000, output_units=500)
    assert cost_equivalent_units(row, {"cache_read": 1.0}) == 101_500
    assert cost_equivalent_units(row, {"cache_read": 0.05}) == 6_500


def test_unknown_usage_stays_unknown():
    assert cost_equivalent_units(_observation(status="UNKNOWN", input_units=10)) is None
    assert cost_equivalent_units(_observation(status="PARTIAL", input_units=10)) is None
    assert cost_equivalent_units(_observation(input_units=10, output_units=None)) is None
    assert cost_equivalent_units(_observation()) == 0
    assert cost_equivalent_units(
        _observation(status="PARTIAL", input_units=10, cache_read_units=100),
        unknown_as_zero=True) == 20


def _charged_window(*, max_tokens, reservation, key,
                    observation=None, status="OBSERVED", owner_window=False):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(autonomy, policy_id=key, max_tokens=max_tokens,
                            reservation=reservation)
    task = store.create_task(title="charged attempt", executor_kind="opencode",
                             binding_ref="coding-glm")
    epoch, _ = control.claim_task(window_id=window.id, task_id=task.id,
                                  owner="owner", lease_ms=60_000)
    if owner_window:
        store._conn.execute(
            "UPDATE platform_autonomous_windows SET confirmation_mode='OWNER_WINDOW', "
            "enforcement_class='HARD_ADMISSION_ENFORCED' WHERE id=?", (window.id,))
        store._conn.commit()
    metrics = observation or dict(input_units=1000, cache_read_units=100_000,
                                  cache_write_units=0, output_units=500,
                                  reasoning_units=0, cost_micro_units=0)
    if status == "UNKNOWN":
        metrics = {}
    store.append_usage_observation(task.id, observation_id=f"usage-{key}",
                                   execution_id=f"exec-{key}", role="executor",
                                   model_id="glm", provider_id="relay",
                                   source_kind="step_finish", source_id=f"part-{key}",
                                   status=status, **metrics)
    control.complete_task_claim(window_id=window.id, task_id=task.id, owner="owner",
                                epoch=epoch, result="terminal")
    return store, control, window, task


def test_a_window_is_charged_cost_equivalent_units_not_the_raw_sum():
    store, control, window, task = _charged_window(max_tokens=20_000,
                                                   reservation=15_000, key="weighted")
    after = control.get_window(window.id)
    assert (after.status, after.stop_reason or "") == ("ACTIVE", "")
    assert after.observed_token_units == 11_500
    reservation = store._conn.execute(
        "SELECT state, observed_token_units FROM platform_budget_reservations WHERE task_id=?",
        (task.id,)).fetchone()
    assert (reservation["state"], reservation["observed_token_units"]) == ("RECONCILED", 11_500)
    summary = control.window_budget_summary(window.id)
    assert summary["remaining_token_units"] == 8_500
    raw = store._conn.execute(
        "SELECT input_units, cache_read_units, output_units FROM task_usage_observations "
        "WHERE task_id=?", (task.id,)).fetchone()
    assert (raw["input_units"], raw["cache_read_units"], raw["output_units"]) == (1000, 100_000, 500)


def test_the_window_budget_check_admits_work_the_raw_sum_would_refuse():
    store, control, window, _ = _charged_window(max_tokens=26_500,
                                                 reservation=15_000, key="admit")
    assert control.get_window(window.id).observed_token_units == 11_500
    fits = store.create_task(title="fits after weighted charge", executor_kind="opencode")
    control.claim_task(window_id=window.id, task_id=fits.id, owner="owner", lease_ms=60_000)
    denied = store.create_task(title="over the weighted budget", executor_kind="opencode")
    try:
        control.claim_task(window_id=window.id, task_id=denied.id, owner="owner", lease_ms=60_000)
        raised = None
    except TaskStoreError as exc:
        raised = str(exc)
    assert raised == "window_token_budget_exhausted"


def test_the_stream_budget_snapshot_uses_the_same_weighted_units():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(autonomy, policy_id="snapshot", max_tokens=20_000,
                            reservation=15_000)
    task = store.create_task(title="streaming attempt", executor_kind="opencode",
                             binding_ref="coding-glm")
    control.claim_task(window_id=window.id, task_id=task.id, owner="owner", lease_ms=60_000)
    store.append_usage_observation(task.id, observation_id="usage-snapshot",
                                   execution_id="exec-snapshot", role="executor",
                                   model_id="glm", provider_id="relay", source_kind="step_finish",
                                   source_id="part-snapshot", status="OBSERVED",
                                   input_units=1000, cache_read_units=100_000,
                                   cache_write_units=0, output_units=500,
                                   reasoning_units=0, cost_micro_units=0)
    snapshot = store.active_usage_budget_snapshot(task.id)
    assert snapshot["observed_token_units"] == 11_500
    assert snapshot["token_units"] == 15_000
    assert (snapshot["observation_count"], snapshot["unknown_observation_count"]) == (1, 0)
    store.append_usage_observation(task.id, observation_id="usage-snapshot-unknown",
                                   execution_id="exec-snapshot", role="executor",
                                   model_id="glm", provider_id="relay", source_kind="step_finish",
                                   source_id="part-unknown", status="UNKNOWN")
    refreshed = store.active_usage_budget_snapshot(task.id)
    assert refreshed["observed_token_units"] == 11_500
    assert refreshed["unknown_observation_count"] == 1


def test_unknown_usage_still_blocks_the_window_and_is_recorded_as_unknown():
    store, control, window, task = _charged_window(max_tokens=20_000,
                                                   reservation=15_000, key="unknown",
                                                   status="UNKNOWN")
    stopped = control.get_window(window.id)
    assert (stopped.status, stopped.stop_reason) == ("BLOCKED", "usage_unknown")
    assert stopped.enforcement_class == "USAGE_UNKNOWN"
    assert stopped.unknown_observation_count == 1
    reservation = store._conn.execute(
        "SELECT state, observed_token_units FROM platform_budget_reservations WHERE task_id=?",
        (task.id,)).fetchone()
    assert (reservation["state"], reservation["observed_token_units"]) == ("UNKNOWN", None)


def test_owner_window_partial_charge_uses_the_weighted_unit():
    store, control, window, task = _charged_window(
        max_tokens=1_000_000, reservation=11_000, key="owner-partial",
        status="PARTIAL", owner_window=True)
    after = control.get_window(window.id)
    assert (after.status, after.stop_reason or "") == ("ACTIVE", "")
    assert after.observed_token_units == 11_500
    reservation = store._conn.execute(
        "SELECT state, observed_token_units FROM platform_budget_reservations WHERE task_id=?",
        (task.id,)).fetchone()
    assert (reservation["state"], reservation["observed_token_units"]) == ("UNKNOWN", None)


def test_the_window_report_shows_both_cost_equivalent_and_raw_totals(tmp_path):
    from types import SimpleNamespace

    from reverse_agent.platform_v1.goal_service import GoalService
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
    from tests.platform_v1.test_unattended_coordinator import _parallel_goal

    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    window = _budget_window(autonomy, policy_id="report", max_tokens=20_000,
                            reservation=15_000)
    goal = _parallel_goal(goals, window.id, key="report", count=1)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]

    def execute(task_id):
        store.transition_to(task_id, "PREPARING_WORKSPACE")
        store.transition_to(task_id, "RUNNING_FIXTURE")
        store.append_usage_observation(task_id, observation_id="usage-report",
                                       execution_id="exec-report", role="executor",
                                       model_id="glm", provider_id="relay",
                                       source_kind="step_finish", source_id="part-report",
                                       status="OBSERVED", input_units=1000,
                                       cache_read_units=100_000, cache_write_units=0,
                                       output_units=500, reasoning_units=0,
                                       cost_micro_units=0)
        store.transition_to(task_id, "VALIDATING")
        store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
        return SimpleNamespace(success=True)

    coordinator = UnattendedCoordinator(store=store, control_store=control,
                                        autonomy=autonomy, router=ExecutorRouter(),
                                        workspace_root=tmp_path, task_executor=execute)
    assert coordinator.tick() == 1
    report = build_report(control, store, window.id)
    charged = report["window"]
    assert charged["observed_token_units"] == 11_500
    assert charged["raw_token_units"] == 101_500
    assert charged["raw_token_counters"] == {
        "input_units": 1000, "cache_read_units": 100_000, "cache_write_units": 0,
        "output_units": 500, "reasoning_units": 0}
    binding = report["bindings"][""]
    assert binding["total_tokens"] == 101_500
    assert binding["cost_equivalent_tokens"] == 11_500
