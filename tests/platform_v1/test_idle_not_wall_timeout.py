"""#1551 (Owner decision 2026-11-15): stop a continuous-window attempt on silence, not total time."""
import sqlite3
import threading
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import durable_execution as de
from reverse_agent.platform_v1 import opencode_executor as oe


def store_with(window_expires_at: str, mode: str = "OWNER_WINDOW"):
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE platform_goal_task_links (goal_id TEXT, goal_revision INTEGER, task_id TEXT);"
        "CREATE TABLE platform_goals (id TEXT, revision INTEGER, window_id TEXT);"
        "CREATE TABLE platform_autonomous_windows (id TEXT, confirmation_mode TEXT, expires_at TEXT);")
    conn.execute("INSERT INTO platform_goal_task_links VALUES ('g', 1, 't')")
    conn.execute("INSERT INTO platform_goals VALUES ('g', 1, 'w')")
    conn.execute("INSERT INTO platform_autonomous_windows VALUES ('w', ?, ?)", (mode, window_expires_at))
    return SimpleNamespace(_lock=threading.Lock(), _conn=conn)


def test_only_a_continuous_owner_window_task_qualifies():
    assert de._continuous_owner_task(store_with(""), "t")
    assert not de._continuous_owner_task(store_with("2026-11-20T00:00:00Z"), "t")  # expiring window
    assert not de._continuous_owner_task(store_with("", mode="DELEGATED"), "t")
    assert not de._continuous_owner_task(store_with(""), "other-task")
    bare = SimpleNamespace(_lock=threading.Lock(), _conn=sqlite3.connect(":memory:"))
    assert not de._continuous_owner_task(bare, "t")  # library store without control tables


@pytest.mark.parametrize("raw, expected", [("", 86400), ("7200", 7200), ("60", 3600),
                                           ("999999", 86400), ("junk", 86400)])
def test_runaway_guard_setting(monkeypatch, raw, expected):
    monkeypatch.setenv("REVERSE_AGENT_EXECUTOR_RUNAWAY_SECONDS", raw)
    assert de.executor_runaway_seconds() == expected


def test_an_unleased_attempt_with_a_stall_guard_may_run_past_one_hour(monkeypatch):
    monkeypatch.delenv("REVERSE_AGENT_EXECUTOR_STALL_SECONDS", raising=False)
    assert oe.OpenCodeExecutor(model_id="test/model", timeout=86400)._timeout == 86400


def test_without_the_stall_guard_the_one_hour_cap_stays(monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_EXECUTOR_STALL_SECONDS", "0")
    assert oe.OpenCodeExecutor(model_id="test/model", timeout=86400)._timeout == 3600


def test_a_relay_leased_attempt_keeps_the_one_hour_cap(monkeypatch):
    monkeypatch.delenv("REVERSE_AGENT_EXECUTOR_STALL_SECONDS", raising=False)
    resolution = SimpleNamespace(executor_id="opencode", auth_method="api_key", relay_required=True,
                                 model_id="test/model", external_session_status="")
    executor = oe.OpenCodeExecutor(binding_resolution=resolution, timeout=86400,
                                   lease_provider=lambda resolution: None)
    assert executor._timeout == 3600
