"""Dispatch hold on a nearly full disk: provider-free coordinator, guard and chaos checks."""
from __future__ import annotations

import logging
import random
import threading
import time
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import workspace_reclaim
from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator

Usage = namedtuple("Usage", "total used free")
GB = 2 ** 30


class Disk:
    """A fake volume; ``None`` is an unreadable one."""

    def __init__(self, free_gb):
        self.free_gb = free_gb

    def __call__(self, _root):
        if self.free_gb is None:
            raise OSError("unreadable")
        return Usage(100 * GB, 0, int(self.free_gb * GB))


class Host:
    def __init__(self, tmp_path, disk, *, concurrent=3, landing_loop=None, publication=None):
        self.tmp_path, self.disk = tmp_path, disk
        self.store = TaskStore(":memory:")
        self.control = PlatformControlStore(self.store)
        self.autonomy = AutonomyService(control_store=self.control, capabilities=CapabilityRegistry())
        self.goals = GoalService(store=self.store, control_store=self.control)
        now = datetime.now(timezone.utc)
        self.window = self.autonomy.activate({
            "policy_id": "disk-window", "policy_revision": 1, "owner_identity": "owner",
            "starts_at": (now - timedelta(seconds=2)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "repositories": ["dddd2024/Nerelan"], "capabilities": ["execute_task"],
            "max_concurrent_tasks": concurrent, "max_tasks": 100, "max_retries": 0,
            "confirmation": "ACTIVATE"})
        self.ran: list[str] = []
        self.guard = workspace_reclaim.DispatchDiskGuard(tmp_path, disk_usage=disk)
        self.execute = self.finish

    def goal(self, name, count=1, chain=False):
        goal = self.goals.create({
            "objective": name, "repository": "dddd2024/Nerelan", "idempotency_key": "disk-" + name,
            "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
        self.goals.plan(goal.id, expected_revision=1, tasks=[
            {"id": f"T{i:03d}", "title": name, "instruction": name,
             **({"dependencies": [f"T{i - 1:03d}"]} if chain and i else {})} for i in range(count)])
        self.goals.approve(goal.id, expected_revision=1)
        self.goals.launch(goal.id, expected_revision=1, window_id=self.window.id)
        return goal.id, [row["task_id"] for row in self.control.list_goal_tasks(goal.id)]

    def finish(self, task_id):
        self.ran.append(task_id)
        for status in ("PREPARING_WORKSPACE", "RUNNING_FIXTURE", "VALIDATING", "READY_FOR_REVIEW_FIXTURE"):
            self.store.transition_to(task_id, status)
        return SimpleNamespace(success=True)

    def coordinator(self, **kwargs):
        return UnattendedCoordinator(
            store=self.store, control_store=self.control, autonomy=self.autonomy,
            router=ExecutorRouter(), workspace_root=self.tmp_path,
            task_executor=lambda task_id: self.execute(task_id), poll_interval=0.1,
            disk_guard=self.guard, goals=kwargs.pop("goals", None), **kwargs)

    def facts(self):
        """Everything a held tick must leave exactly as it found it."""
        window = self.control.get_window(self.window.id)
        tables = [row[0] for row in self.store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return (window.tasks_started, window.retries_used,
                {name: [tuple(row) for row in self.store._conn.execute(f"SELECT * FROM {name}")]
                 for name in tables})


def wait_for(predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.03)
    return False


# --- the guard ------------------------------------------------------------------------------

def test_guard_holds_below_the_floor_and_resumes_clearly_above_it(tmp_path):
    disk = Disk(2.0)
    guard = workspace_reclaim.DispatchDiskGuard(tmp_path / "not-created-yet", disk_usage=disk, clock=lambda: 0)
    state = guard.check()
    assert (state["hold"], state["reason"], state["held_since"]) == (False, "", None)
    assert (state["free_gb"], state["total_gb"], state["low"]) == (2.0, 100.0, True)
    disk.free_gb = 1.9
    state = guard.check()
    assert (state["hold"], state["reason"]) == (True, "disk_space_critical")
    assert state["held_since"] == "1970-01-01T00:00:00+00:00"
    for free in (2.0, 2.4, None):  # hovering or unreadable keeps the hold
        disk.free_gb = free
        assert guard.check()["hold"] is True
    disk.free_gb = 2.5
    assert guard.check()["hold"] is False
    disk.free_gb = None  # unreadable never starts one
    assert guard.check() == {**guard.check(), "hold": False, "free_gb": None}


def test_guard_logs_transitions_only(tmp_path, caplog):
    disk = Disk(1.0)
    guard = workspace_reclaim.DispatchDiskGuard(tmp_path, disk_usage=disk)
    with caplog.at_level(logging.INFO):
        for _ in range(50):
            guard.check()
        disk.free_gb = 2.2
        for _ in range(50):
            guard.check()
        disk.free_gb = 20
        for _ in range(50):
            guard.check()
    assert [record.message.split(":")[0] for record in caplog.records] == ["dispatch held", "dispatch resumed"]


def test_guard_config_is_independent_of_the_reclaim_mode(tmp_path):
    for mode in ("", "off", "report", "apply"):
        env = {"REVERSE_AGENT_WORKSPACE_RECLAIM": mode}
        assert workspace_reclaim.configured_disk_guard(tmp_path, env).floor_gb == 2.0
    for raw, expected in (("5", 5.0), ("0", 0.0), ("-1", 2.0), ("nan", 2.0), ("x", 2.0)):
        env = {"REVERSE_AGENT_DISPATCH_MIN_FREE_GB": raw}
        assert workspace_reclaim.configured_disk_guard(tmp_path, env).floor_gb == expected
    off = workspace_reclaim.DispatchDiskGuard(tmp_path, floor_gb=0, disk_usage=Disk(0))
    assert off.check()["hold"] is False


def test_guard_and_reclaimer_read_the_same_disk(tmp_path):
    reclaimer = workspace_reclaim.AutoReclaimer(tmp_path, "db", disk_usage=Disk(4.8))
    guard = workspace_reclaim.DispatchDiskGuard(tmp_path, disk_usage=Disk(4.8))
    assert reclaimer.disk().items() <= guard.check().items()


# --- the coordinator ------------------------------------------------------------------------

def test_held_tick_changes_nothing_and_resumes_by_itself(tmp_path):
    host = Host(tmp_path, Disk(1.0))
    goal_id, tasks = host.goal("held", count=2)
    coordinator = host.coordinator()
    before = host.facts()
    for _ in range(5):
        assert coordinator.tick() == 0
    assert host.facts() == before, "no claim, receipt, event, reservation or retry"
    status = coordinator.status()
    assert status["disk"]["hold"] is True and status["disk"]["reason"] == "disk_space_critical"
    assert status["disk"]["waiting_task_count"] == 2
    assert sorted(status["disk"]["waiting_task_ids"]) == sorted(tasks)
    assert status["last_error"] == ""
    host.disk.free_gb = 8
    assert coordinator.tick() == 2
    assert sorted(host.ran) == sorted(tasks)
    assert host.control.get_goal(goal_id).status == "COMPLETED"
    disk = coordinator.status()["disk"]
    assert (disk["hold"], disk["waiting_task_count"], disk["free_gb"]) == (False, 0, 8.0)


@pytest.mark.parametrize("status", ["INTERRUPTED", "QUOTA_WAIT"])
def test_resumes_wait_too_without_quota_work(tmp_path, status):
    host = Host(tmp_path, Disk(1.0))
    _, [task_id] = host.goal("resume")
    host.store._conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    host.store._conn.commit()
    calls = []
    coordinator = host.coordinator(quota_preparer=calls.append, quota_rerouter=calls.append)
    before = host.facts()
    assert coordinator.tick() == 0
    assert host.facts() == before and calls == [] and host.ran == []


def test_running_task_continues_while_new_ones_wait(tmp_path):
    host = Host(tmp_path, Disk(50))
    _, [first] = host.goal("first")
    started, release = threading.Event(), threading.Event()

    def execute(task_id):
        if task_id == first:
            started.set()
            assert release.wait(10)
        return host.finish(task_id)

    host.execute = execute
    coordinator = host.coordinator()
    try:
        coordinator.start()
        assert started.wait(5)
        host.disk.free_gb = 0.5
        assert wait_for(lambda: coordinator._disk_hold)
        _, [second] = host.goal("second")
        assert wait_for(lambda: coordinator.status()["disk"]["waiting_task_ids"] == [second])
        release.set()
        assert wait_for(lambda: host.store.get_task(first).status == "READY_FOR_REVIEW_FIXTURE")
        ticks = coordinator.status()["ticks"]
        assert wait_for(lambda: coordinator.status()["ticks"] > ticks + 2)
        assert host.ran == [first] and host.store.get_task(second).status == "QUEUED"
        host.disk.free_gb = 50
        assert wait_for(lambda: host.store.get_task(second).status == "READY_FOR_REVIEW_FIXTURE")
    finally:
        release.set()
        coordinator.stop(timeout=5)


def test_a_full_slot_is_not_reported_as_waiting_for_disk(tmp_path):
    host = Host(tmp_path, Disk(1.0), concurrent=1)
    _, [task_id] = host.goal("slots")
    coordinator = host.coordinator()
    coordinator.tick()
    assert coordinator.status()["disk"]["waiting_task_count"] == 1
    coordinator._active_task_ids.add("another")
    coordinator.tick(background=True)
    assert coordinator.status()["disk"]["waiting_task_count"] == 0


def test_broken_guard_never_stops_dispatch(tmp_path):
    host = Host(tmp_path, Disk(50))
    host.goal("broken")
    coordinator = host.coordinator()
    coordinator.disk_guard = SimpleNamespace(check=lambda: 1 / 0)
    assert coordinator.tick() == 1
    assert coordinator.status()["disk"] is None


@pytest.mark.parametrize("reviewed", [False, True])
def test_landing_starts_no_review_but_finishes_reviewed_work(tmp_path, monkeypatch, reviewed):
    from reverse_agent.platform_v1 import artifact_handoff
    published, ticked = [], []
    host = Host(tmp_path, Disk(1.0))
    goal_id, [task_id] = host.goal("landing")
    host.store._conn.execute("UPDATE tasks SET status='READY_FOR_REVIEW' WHERE id=?", (task_id,))
    host.store._conn.commit()
    monkeypatch.setattr(artifact_handoff, "_load_evidence", lambda *a, **k: {"commit": "a" * 40})
    monkeypatch.setattr(host.control, "ready_window_tasks", lambda window_id: [task_id])
    monkeypatch.setattr(host.control, "landing_recovery_identity", lambda window: "recovery")
    loop = SimpleNamespace(tick=lambda identity, **k: ticked.append(identity),
                           publish_and_review=lambda task, **k: published.append(task))
    coordinator = host.coordinator(landing_loop=loop, publication=object(), goals=host.goals)
    monkeypatch.setattr(coordinator, "_landing_is_reviewed", lambda goal, task: reviewed)
    coordinator.tick()
    assert ticked == ["recovery"], "the gated merge of landed work continues"
    assert published == ([task_id] if reviewed else [])
    host.disk.free_gb = 50
    coordinator.tick()
    assert published == [task_id] * (2 if reviewed else 1)


# --- chaos: random disk readings and coordinator restarts --------------------------------------

@pytest.mark.parametrize("seed", range(12))
def test_random_disk_pressure_never_strands_or_spends(tmp_path, seed):
    rng = random.Random(seed)
    disk = Disk(50)
    host = Host(tmp_path, disk, concurrent=rng.randint(1, 3))
    goals = [host.goal(f"g{n}", count=rng.randint(1, 4), chain=rng.random() < 0.5) for n in range(4)]
    total = sum(len(tasks) for _, tasks in goals)
    coordinator = host.coordinator()
    for _ in range(40):
        disk.free_gb = rng.choice([0.0, 0.5, 1.99, 2.0, 2.3, 2.5, 50, None])
        if rng.random() < 0.2:  # host restart: the hold is re-derived, nothing is persisted
            host.guard = workspace_reclaim.DispatchDiskGuard(tmp_path, disk_usage=disk)
            coordinator = host.coordinator()
        before, ran = host.facts(), len(host.ran)
        coordinator.tick()
        if coordinator._disk_hold:
            assert len(host.ran) == ran and host.facts() == before
        if disk.free_gb is not None and disk.free_gb < 2:
            assert coordinator._disk_hold
    disk.free_gb = 50
    for _ in range(total + 1):
        coordinator.tick()
    assert len(host.ran) == len(set(host.ran)) == total
    assert [host.control.get_goal(goal_id).status for goal_id, _ in goals] == ["COMPLETED"] * 4
    window = host.control.get_window(host.window.id)
    assert (window.tasks_started, window.retries_used) == (total, 0)


def test_real_host_reports_the_hold_with_reclaim_off(tmp_path, monkeypatch):
    from reverse_agent.model_access.store import ModelProfileStore
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    monkeypatch.setenv("REVERSE_AGENT_MODEL_CONTROL_LIVE", "0")
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    monkeypatch.setenv("REVERSE_AGENT_WORKSPACE_RECLAIM", "off")
    monkeypatch.setenv("REVERSE_AGENT_DISPATCH_MIN_FREE_GB", "1000000000")
    host = CombinedTrustedHost(
        store=ModelProfileStore(), task_store=TaskStore(db_path=str(tmp_path / "tasks.sqlite3")),
        model_control_port=0, task_api_port=0, vault=None)
    try:
        host.start(coordinator_paused=True)
        assert host._workspace_reclaimer is None
        handler = object.__new__(host._task_server.RequestHandlerClass)
        disk = handler._platform_status_response()["coordinator"]["disk"]
        assert disk["hold"] is True and disk["free_gb"] > 0
        assert disk["reason"] == "disk_space_critical" and disk["waiting_task_count"] == 0
    finally:
        host.stop()
        host._task_store._conn.close()
