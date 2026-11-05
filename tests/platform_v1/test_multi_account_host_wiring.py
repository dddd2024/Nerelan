"""The host seams that make the multi-account brain actually bound a run.

Every other test in this package exercises the brain directly. These drive the
*coordinator* the way a host does, because the v3 modules were correct but
unwired: a cost ceiling nobody consults and a watchdog nobody reads change no
behaviour at all. The contract under test is therefore narrow and behavioural:

* a verdict of ``conclude`` ends the loop while in-flight work still lands;
* a denied cost admission holds a task instead of claiming and dropping it;
* drained alerts reach the injected sink;
* an attempt counts as progress even when its account is unresolvable;
* a raising seam is recorded and never interrupts dispatch.

Absent callbacks must reproduce the previous loop exactly, so the last test
pins the "not injected" payload shape rather than behaviour alone.
"""

from datetime import datetime, timedelta, timezone
import json
import threading
import time

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def _setup(*, max_concurrent=1, max_tasks=3):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "wiring-window", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": max_concurrent, "max_tasks": max_tasks,
        "max_retries": 0, "confirmation": "ACTIVATE",
    })
    return store, control, autonomy, goals, window


def _goal(goals, control, window, name, count=1):
    goal = goals.create({
        "objective": name, "repository": "dddd2024/Nerelan",
        "idempotency_key": "wiring-" + name,
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": f"T{index:03d}", "title": f"{name} worker {index}", "instruction": name}
        for index in range(count)
    ])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    return goal, [row["task_id"] for row in control.list_goal_tasks(goal.id)]


def _finish(store, task_id):
    from types import SimpleNamespace
    for status in ("PREPARING_WORKSPACE", "RUNNING_FIXTURE", "VALIDATING",
                   "READY_FOR_REVIEW_FIXTURE"):
        store.transition_to(task_id, status)
    return SimpleNamespace(success=True)


def _wait_for(predicate, timeout=8.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def _coordinator(tmp_path, store, control, autonomy, *, execute=None, **hooks):
    return UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.05, **hooks,
    )


# --- run duration ------------------------------------------------------------

def test_a_conclude_verdict_ends_the_loop_without_a_stop_request(tmp_path):
    store, control, autonomy, _goals, _window = _setup()
    starts: list[int] = []

    def verdict():
        return {"action": "conclude", "reason": "max_run_duration"}

    coordinator = _coordinator(
        tmp_path, store, control, autonomy,
        run_start=lambda: starts.append(1) or {"action": "continue"},
        run_verdict=verdict,
    )
    coordinator.start()
    try:
        assert _wait_for(lambda: not coordinator.status()["enabled"]), \
            "a concluded run must end by itself"
        assert len(starts) == 1, "the timed window opens exactly once per run"
        assert coordinator.status()["run_conclusion"] == "run_conclude:max_run_duration"
        assert coordinator.status()["last_verdict"]["reason"] == "max_run_duration"
    finally:
        coordinator.stop(timeout=5)


def test_a_conclude_verdict_lets_work_in_flight_land(tmp_path):
    store, control, autonomy, goals, window = _setup()
    _goal_obj, [task_id] = _goal(goals, control, window, "in-flight")
    started = threading.Event()
    release = threading.Event()

    def execute(candidate):
        started.set()
        assert release.wait(timeout=10)
        return _finish(store, candidate)

    concluded = threading.Event()

    def verdict():
        if started.is_set():
            concluded.set()
            return {"action": "conclude", "reason": "max_run_duration"}
        return {"action": "continue"}

    coordinator = _coordinator(
        tmp_path, store, control, autonomy, execute=execute, run_verdict=verdict)
    coordinator.start()
    try:
        assert started.wait(8), "the task must be dispatched before the bound"
        assert _wait_for(concluded.is_set, timeout=8)
        # The verdict ends claiming, not the running attempt: release the
        # executor only now and the task must still land with its evidence.
        release.set()
        assert _wait_for(
            lambda: store.get_task(task_id).status == "READY_FOR_REVIEW_FIXTURE",
            timeout=8), "in-flight work must not be truncated by the bound"
        assert _wait_for(lambda: not coordinator.status()["enabled"], timeout=8)
        assert coordinator.status()["run_conclusion"].startswith("run_conclude")
    finally:
        release.set()
        coordinator.stop(timeout=5)


def test_an_unknown_or_failing_verdict_never_ends_a_run(tmp_path):
    store, control, autonomy, _goals, _window = _setup()

    def boom():
        raise RuntimeError("clock unavailable")

    coordinator = _coordinator(tmp_path, store, control, autonomy, run_verdict=boom)
    assert coordinator._run_should_conclude() is False
    assert coordinator.status()["run_conclusion"] == ""
    assert coordinator._last_error == "run_verdict_failed:RuntimeError"


def test_a_non_dict_verdict_is_treated_as_continue(tmp_path):
    store, control, autonomy, _goals, _window = _setup()
    coordinator = _coordinator(
        tmp_path, store, control, autonomy, run_verdict=lambda: "conclude")
    assert coordinator._run_should_conclude() is False


# --- cost ceiling ------------------------------------------------------------

def test_a_denied_cost_admission_holds_the_task_without_claiming(tmp_path):
    store, control, autonomy, goals, window = _setup()
    _goal_obj, [task_id] = _goal(goals, control, window, "held")
    seen: list[str] = []

    coordinator = _coordinator(
        tmp_path, store, control, autonomy, execute=seen.append,
        cost_admission=lambda forecast: {"decision": "deny",
                                         "reason": "cost_budget_exhausted",
                                         "retry_at": 1234.0},
    )
    assert coordinator.tick() == 0
    assert seen == [], "a held task must not be executed"
    assert store.get_task(task_id).status == "QUEUED", "held means kept, not dropped"
    assert coordinator.status()["cost_holds"] == 1
    assert coordinator._last_error == "cost_hold:cost_budget_exhausted:until=1234.0"


def test_an_allowing_cost_admission_changes_nothing(tmp_path):
    store, control, autonomy, goals, window = _setup()
    _goal_obj, [task_id] = _goal(goals, control, window, "allowed")
    seen: list[str] = []

    def execute(candidate):
        seen.append(candidate)
        return _finish(store, candidate)

    coordinator = _coordinator(
        tmp_path, store, control, autonomy, execute=execute,
        cost_admission=lambda forecast: {"decision": "allow", "reason": "within_budget"},
    )
    assert coordinator.tick() == 1
    assert seen == [task_id]
    assert coordinator.status()["cost_holds"] == 0
    assert store.get_task(task_id).status == "READY_FOR_REVIEW_FIXTURE"


def test_a_broken_cost_seam_fails_open(tmp_path):
    store, control, autonomy, goals, window = _setup()
    _goal_obj, [task_id] = _goal(goals, control, window, "fail-open")
    seen: list[str] = []

    def execute(candidate):
        seen.append(candidate)
        return _finish(store, candidate)

    def boom(_forecast):
        raise RuntimeError("budget store locked")

    coordinator = _coordinator(
        tmp_path, store, control, autonomy, execute=execute, cost_admission=boom)
    assert coordinator.tick() == 1, "a broken ceiling must not block dispatch"
    assert seen == [task_id]
    assert coordinator._last_error == "cost_admission_failed:RuntimeError"


# --- alert delivery ----------------------------------------------------------

def test_alerts_are_drained_into_the_injected_sink(tmp_path):
    store, control, autonomy, _goals, _window = _setup()
    delivered: list[list[dict]] = []
    queue: list[list[dict]] = [[{"code": "cost_budget_soft_cap", "severity": "warning"}]]

    def source():
        return queue.pop() if queue else []

    coordinator = _coordinator(
        tmp_path, store, control, autonomy,
        alert_source=source, alert_sink=delivered.append)
    coordinator._deliver_account_alerts()
    assert delivered == [[{"code": "cost_budget_soft_cap", "severity": "warning"}]]
    assert coordinator.status()["alerts_delivered"] == 1
    # Draining is exactly once: an empty queue delivers nothing further.
    coordinator._deliver_account_alerts()
    assert len(delivered) == 1


def test_a_raising_alert_sink_does_not_lose_the_loop(tmp_path):
    store, control, autonomy, _goals, _window = _setup()

    def sink(_alerts):
        raise RuntimeError("webhook down")

    coordinator = _coordinator(
        tmp_path, store, control, autonomy,
        alert_source=lambda: [{"code": "x"}], alert_sink=sink)
    coordinator._deliver_account_alerts()
    assert coordinator._last_error == "alert_sink_failed:RuntimeError"
    assert coordinator.status()["alerts_delivered"] == 0


# --- progress accounting -----------------------------------------------------

def test_an_attempt_counts_as_progress_without_a_resolvable_account(tmp_path):
    """Idle detection must not conclude a run that is still finishing work."""
    store, control, autonomy, goals, window = _setup()
    _goal_obj, [_task_id] = _goal(goals, control, window, "progress")
    beats: list[int] = []

    def execute(candidate):
        return _finish(store, candidate)

    coordinator = _coordinator(
        tmp_path, store, control, autonomy, execute=execute,
        # No account_feedback: the host cannot resolve an account here, which is
        # exactly the case that used to leave the watchdog at zero attempts.
        run_progress=lambda: beats.append(1),
    )
    coordinator.tick()
    assert beats, "a finished attempt is progress even with no account feedback"


def test_a_raising_progress_hook_is_recorded_only(tmp_path):
    store, control, autonomy, goals, window = _setup()
    _goal_obj, [_task_id] = _goal(goals, control, window, "progress-boom")

    def execute(candidate):
        return _finish(store, candidate)

    def boom():
        raise RuntimeError("nope")

    coordinator = _coordinator(
        tmp_path, store, control, autonomy, execute=execute, run_progress=boom)
    assert coordinator.tick() == 1
    assert coordinator._last_error == "run_progress_failed:RuntimeError"


# --- host opt-in gate --------------------------------------------------------

def test_the_host_injects_nothing_unless_the_feature_is_enabled(monkeypatch):
    """An unconfigured deployment must construct the previous coordinator."""
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    host = object.__new__(CombinedTrustedHost)
    monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", raising=False)
    assert host._multi_account_loop_hooks() == {}

    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    hooks = host._multi_account_loop_hooks()
    assert set(hooks) == {"run_start", "run_verdict", "run_progress",
                          "alert_source", "alert_sink", "cost_admission",
                          "pool_refresh"}


def test_the_host_cost_seam_never_leaks_a_reservation(monkeypatch):
    """An unsettled reservation would hold ceiling room forever."""
    from reverse_agent.platform_v1.multi_account import dispatch
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    captured: dict = {}

    def fake_admit(forecast=None, *, account_ref=None, reserve=True, store_path=None):
        captured["reserve"] = reserve
        return {"decision": "allow", "reservation": None}

    monkeypatch.setattr(dispatch, "admit_cost", fake_admit)
    host = object.__new__(CombinedTrustedHost)
    host._multi_account_loop_hooks()["cost_admission"](2.0)
    assert captured["reserve"] is False


def test_the_host_keeps_a_bounded_alert_tail(monkeypatch):
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    host = object.__new__(CombinedTrustedHost)
    host._deliver_account_alerts([{"code": f"c{index}"} for index in range(3)])
    assert [alert["code"] for alert in host.multi_account_alerts()] == ["c0", "c1", "c2"]
    assert host.multi_account_alerts(limit=1) == [{"code": "c2"}]
    # Bounded: a long unattended run cannot grow this without limit.
    host._deliver_account_alerts([{"code": "x"}] * 500)
    assert len(host._multi_account_alert_tail) == 200


# --- default (not injected) behaviour ---------------------------------------

def test_without_hooks_the_loop_and_its_payload_are_unchanged(tmp_path):
    store, control, autonomy, goals, window = _setup()
    _goal_obj, [task_id] = _goal(goals, control, window, "no-hooks")

    def execute(candidate):
        return _finish(store, candidate)

    coordinator = _coordinator(tmp_path, store, control, autonomy, execute=execute)
    status = coordinator.status()
    assert status["run_conclusion"] == ""
    assert status["last_verdict"] is None
    assert status["cost_holds"] == 0
    assert status["alerts_delivered"] == 0
    # No verdict, no cost gate: the run is unbounded exactly as before.
    assert coordinator._run_should_conclude() is False
    assert coordinator._cost_allows_dispatch() is True
    assert coordinator.tick() == 1
    assert store.get_task(task_id).status == "READY_FOR_REVIEW_FIXTURE"


# --- perception before the first dispatch ------------------------------------

def _snapshot(accounts):
    return {"status": "available", "version": "0.1.2945", "models": [], "accounts": accounts}


def _live_account(ref, provider, *, used=10.0):
    return {"provider": provider, "kind": "subscription", "plan": None,
            "account_ref": ref, "windows": [{"name": "5 hours", "used_percent": used,
                                             "remaining_percent": 100.0 - used,
                                             "resets_at": None, "unlimited": False}],
            "cached_windows": [], "state": "FRESH", "reason": None,
            "observed_at": "2026-11-05T13:50:00+00:00",
            "provenance": "EXTERNAL_MAGPIE", "source_version": "0.1.2945"}


def test_the_observation_table_is_writable_before_any_dispatch():
    """Admission used to be the only writer, so perception was blind until then."""
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    assert control._conn.execute(
        "SELECT COUNT(*) FROM platform_quota_observations").fetchone()[0] == 0

    rows = [{"account_ref": "aaa", "observed_at": "2026-11-05T13:00:00Z",
             "evidence": {"provider": "claude"}},
            {"account_ref": "bbb", "observed_at": "2026-11-05T13:00:00Z",
             "evidence": {"provider": "codex"}}]
    assert control.record_quota_observations(rows) == 2
    assert control._conn.execute(
        "SELECT COUNT(*) FROM platform_quota_observations").fetchone()[0] == 2


def test_an_older_reading_never_overwrites_a_newer_one():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    control.record_quota_observation("aaa", "2026-11-05T13:00:00Z", '{"provider": "new"}')
    changed = control.record_quota_observation("aaa", "2026-11-05T12:00:00Z",
                                               '{"provider": "old"}')
    assert changed == 0, "a periodic sync must not roll a reading backwards"
    stored = control._conn.execute(
        "SELECT evidence_json FROM platform_quota_observations WHERE account_ref='aaa'"
    ).fetchone()[0]
    assert json.loads(stored)["provider"] == "new"


def test_bad_evidence_is_rejected_instead_of_stored():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    for evidence in ("not-json", "[]", ""):
        try:
            control.record_quota_observation("aaa", "2026-11-05T13:00:00Z", evidence)
        except ValueError:
            continue
        raise AssertionError(f"{evidence!r} should have been rejected")
    assert control._conn.execute(
        "SELECT COUNT(*) FROM platform_quota_observations").fetchone()[0] == 0


def test_the_host_syncs_live_readings_into_perception(monkeypatch):
    """End to end without a network: snapshot -> store -> the host's own provider."""
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    host = object.__new__(CombinedTrustedHost)
    host._task_store, host._control_store = store, control

    account = _live_account("ref-claude", "claude")
    account["user"] = "someone@example.com"       # must never reach the store
    summary = host.sync_multi_account_observations(fetch=lambda: _snapshot([account]))

    assert summary["written"] == 1
    assert summary["accounts_visible"] == 1
    stored = control._conn.execute(
        "SELECT evidence_json FROM platform_quota_observations").fetchone()[0]
    assert "someone@example.com" not in stored, "personal data must not be persisted"
    assert "user" not in json.loads(stored)

    statuses = host._goal_account_status_provider()
    assert [s.account_ref for s in statuses] == ["ref-claude"]
    assert statuses[0].provider == "claude"


def test_the_host_sync_is_inert_when_disabled(monkeypatch):
    monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", raising=False)
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    host = object.__new__(CombinedTrustedHost)
    summary = host.sync_multi_account_observations(fetch=lambda: _snapshot([]))
    assert summary["enabled"] is False and summary["written"] == 0


def test_an_unavailable_magpie_leaves_perception_as_it_was(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    store = TaskStore(":memory:")
    host = object.__new__(CombinedTrustedHost)
    host._task_store, host._control_store = store, PlatformControlStore(store)
    summary = host.sync_multi_account_observations(
        fetch=lambda: {"status": "unavailable", "reason": "request_failed",
                       "accounts": [_live_account("x", "y")]})
    assert summary["snapshot_status"] == "unavailable"
    assert summary["written"] == 0


# --- perception before the first dispatch ------------------------------------

def _snapshot(accounts):
    return {"status": "available", "version": "0.1.2945", "models": [], "accounts": accounts}


def _live_account(ref, provider, *, used=10.0):
    return {"provider": provider, "kind": "subscription", "plan": None,
            "account_ref": ref, "windows": [{"name": "5 hours", "used_percent": used,
                                             "remaining_percent": 100.0 - used,
                                             "resets_at": None, "unlimited": False}],
            "cached_windows": [], "state": "FRESH", "reason": None,
            "observed_at": "2026-11-05T13:50:00+00:00",
            "provenance": "EXTERNAL_MAGPIE", "source_version": "0.1.2945"}


def test_the_observation_table_is_writable_before_any_dispatch():
    """Admission used to be the only writer, so perception was blind until then."""
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    assert control._conn.execute(
        "SELECT COUNT(*) FROM platform_quota_observations").fetchone()[0] == 0

    rows = [{"account_ref": "aaa", "observed_at": "2026-11-05T13:00:00Z",
             "evidence": {"provider": "claude"}},
            {"account_ref": "bbb", "observed_at": "2026-11-05T13:00:00Z",
             "evidence": {"provider": "codex"}}]
    assert control.record_quota_observations(rows) == 2
    assert control._conn.execute(
        "SELECT COUNT(*) FROM platform_quota_observations").fetchone()[0] == 2


def test_an_older_reading_never_overwrites_a_newer_one():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    control.record_quota_observation("aaa", "2026-11-05T13:00:00Z", '{"provider": "new"}')
    changed = control.record_quota_observation("aaa", "2026-11-05T12:00:00Z",
                                               '{"provider": "old"}')
    assert changed == 0, "a periodic sync must not roll a reading backwards"
    stored = control._conn.execute(
        "SELECT evidence_json FROM platform_quota_observations WHERE account_ref='aaa'"
    ).fetchone()[0]
    assert json.loads(stored)["provider"] == "new"


def test_bad_evidence_is_rejected_instead_of_stored():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    for evidence in ("not-json", "[]", ""):
        try:
            control.record_quota_observation("aaa", "2026-11-05T13:00:00Z", evidence)
        except ValueError:
            continue
        raise AssertionError(f"{evidence!r} should have been rejected")
    assert control._conn.execute(
        "SELECT COUNT(*) FROM platform_quota_observations").fetchone()[0] == 0


def test_the_host_syncs_live_readings_into_perception(monkeypatch):
    """End to end without a network: snapshot -> store -> the host's own provider."""
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    host = object.__new__(CombinedTrustedHost)
    host._task_store, host._control_store = store, control

    account = _live_account("ref-claude", "claude")
    account["user"] = "someone@example.com"       # must never reach the store
    summary = host.sync_multi_account_observations(fetch=lambda: _snapshot([account]))

    assert summary["written"] == 1
    assert summary["accounts_visible"] == 1
    stored = control._conn.execute(
        "SELECT evidence_json FROM platform_quota_observations").fetchone()[0]
    assert "someone@example.com" not in stored, "personal data must not be persisted"
    assert "user" not in json.loads(stored)

    statuses = host._goal_account_status_provider()
    assert [s.account_ref for s in statuses] == ["ref-claude"]
    assert statuses[0].provider == "claude"


def test_the_host_sync_is_inert_when_disabled(monkeypatch):
    monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", raising=False)
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    host = object.__new__(CombinedTrustedHost)
    summary = host.sync_multi_account_observations(fetch=lambda: _snapshot([]))
    assert summary["enabled"] is False and summary["written"] == 0


def test_an_unavailable_magpie_leaves_perception_as_it_was(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    store = TaskStore(":memory:")
    host = object.__new__(CombinedTrustedHost)
    host._task_store, host._control_store = store, PlatformControlStore(store)
    summary = host.sync_multi_account_observations(
        fetch=lambda: {"status": "unavailable", "reason": "request_failed",
                       "accounts": [_live_account("x", "y")]})
    assert summary["snapshot_status"] == "unavailable"
    assert summary["written"] == 0


def test_an_aged_reading_is_refreshed_not_left_stale(monkeypatch):
    """One bootstrap is not enough: readings age out and must be re-synced."""
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    host = object.__new__(CombinedTrustedHost)
    host._task_store, host._control_store = store, control
    control.record_quota_observation("aaa", "2020-01-01T00:00:00Z", '{"provider": "old"}')
    assert host._reading_is_fresh("2020-01-01T00:00:00Z") is False
    calls: list[int] = []
    host.sync_multi_account_observations = lambda **_: calls.append(1) or {}
    host._bootstrap_multi_account_observations()
    assert calls, "an aged table must be refreshed"
    # A fresh reading suppresses the fetch; the debounce is bypassed here so the
    # assertion is about freshness, not wall-clock throttling.
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    assert host._reading_is_fresh(now_iso) is True
    control.record_quota_observation("aaa", now_iso, '{"provider": "new"}')
    host._multi_account_sync_at = 0.0
    host._bootstrap_multi_account_observations()
    assert len(calls) == 1, "a fresh table must not be re-fetched"


def test_the_pool_is_refreshed_on_the_reconcile_cadence_not_per_claim(tmp_path):
    """Perception must neither fossilise nor block a claim on a fetch."""
    store, control, autonomy, _goals, _window = _setup()
    refreshed: list[int] = []
    coordinator = _coordinator(tmp_path, store, control, autonomy,
                               reconcile_interval=0.05,
                               pool_refresh=lambda: refreshed.append(1))
    coordinator.start()
    try:
        assert _wait_for(lambda: len(refreshed) >= 2, timeout=8)
    finally:
        coordinator.stop(timeout=5)
    # It runs on the reconcile branch, so a burst of claims cannot multiply it.
    before = len(refreshed)
    coordinator.tick()
    assert len(refreshed) == before


def test_a_failing_pool_refresh_is_recorded_and_ignored(tmp_path):
    store, control, autonomy, _goals, _window = _setup()

    def boom():
        raise RuntimeError("snapshot unreachable")

    coordinator = _coordinator(tmp_path, store, control, autonomy, pool_refresh=boom)
    coordinator._refresh_pool()
    assert coordinator._last_error == "pool_refresh_failed:RuntimeError"
