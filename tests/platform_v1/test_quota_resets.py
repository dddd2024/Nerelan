"""Quota resets detected from account readings, and what they release (provider-free)."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from datetime import datetime, timezone

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1 import trusted_host
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.quota_resets import SCHEMA, QuotaResets, applies_to_model, public_event, window_seconds
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator

HOUR, DAY = 3600.0, 86400.0
T0 = datetime(2026, 11, 20, tzinfo=timezone.utc).timestamp()


def _iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def _at(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def _account(at, windows, *, ref="acct", provider="codex", state="FRESH", plan="pro"):
    rows = [{"name": name, "used_percent": used, "remaining_percent": 100 - used,
             "resets_at": reset if reset is None or isinstance(reset, str) else _iso(reset), "unlimited": False}
            for name, used, reset in windows]
    return {"account_ref": ref, "provider": provider, "plan": plan, "kind": "subscription", "state": state,
            "observed_at": at if isinstance(at, str) or at is None else _iso(at),
            "windows": [] if state == "STALE" else rows, "cached_windows": rows if state == "STALE" else []}


def _snapshot(*accounts):
    return {"status": "available", "accounts": list(accounts)}


@pytest.fixture
def resets():
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row
    for statement in SCHEMA:
        conn.execute(statement)
    return QuotaResets(conn, threading.RLock())


def _feed(resets, at, windows, **account):
    return resets.observe(_snapshot(_account(at, windows, **account)), now=at + 5)


# ---- the 2026-11-24 Antigravity readings, as Magpie recorded them --------------------------

ANTIGRAVITY = [  # read at, Gemini 5 h, Gemini 7 d, Claude & GPT 7 d: (used, resets at)
    ("2026-11-23T08:32:13Z", (99.22, "2026-11-23T08:48:47Z"), (84.51, "2026-11-29T05:16:20Z"), (98.09, "2026-11-29T04:56:33Z")),
    ("2026-11-23T08:36:53Z", (99.22, "2026-11-23T08:48:47Z"), (84.81, "2026-11-29T05:16:20Z"), (98.09, "2026-11-29T04:56:33Z")),
    ("2026-11-23T08:41:32Z", (99.22, "2026-11-23T08:48:47Z"), (83.93, "2026-11-29T05:16:20Z"), (98.09, "2026-11-29T04:56:33Z")),
    ("2026-11-23T08:50:06Z", (0, "2026-11-23T13:48:47Z"), (83.93, "2026-11-29T05:16:20Z"), (98.09, "2026-11-29T04:56:33Z")),
    ("2026-11-23T09:34:30Z", (0, "2026-11-23T14:34:30Z"), (83.93, "2026-11-29T05:16:20Z"), (98.09, "2026-11-29T04:56:33Z")),
    ("2026-11-23T15:08:30Z", (0, "2026-11-23T20:08:29Z"), (83.93, "2026-11-29T05:16:20Z"), (98.09, "2026-11-29T04:56:33Z")),
    ("2026-11-24T03:51:08Z", (0, "2026-11-24T08:51:07Z"), (0, "2026-12-01T03:51:07Z"), (98.09, "2026-11-29T04:56:33Z")),
    ("2026-11-24T05:41:42Z", (0, "2026-11-24T10:41:41Z"), (0, "2026-12-01T05:41:41Z"), (98.09, "2026-11-29T04:56:33Z")),
]


def _antigravity(row, **account):
    at, five, week, other = row
    return _account(at, [("Gemini · 5 hours", *five), ("Gemini · 7 days", *week), ("Claude & GPT · 7 days", *other),
                         ("Claude & GPT · 5 hours", 0, None)], ref="anti", provider="antigravity-bridge", **account)


def _replay(resets, rows=ANTIGRAVITY):
    found = []
    for row in rows:
        # Magpie's 15-minute freshness is usually over when Antigravity is read: cached rows count.
        found += resets.observe(_snapshot(_antigravity(row, state="STALE")), now=_at(row[0]) + 1200)
    return found


def test_replays_the_2026_11_24_gemini_reset(resets):
    found = _replay(resets)
    assert [(e["window"], e["kind"], e["used_before"], e["used_after"]) for e in found] == [
        ("Gemini · 5 hours", "scheduled", 99.22, 0.0), ("Gemini · 7 days", "early", 83.93, 0.0)]
    assert _iso(found[1]["observed_at"]) == "2026-11-24T03:51:08Z"
    assert _iso(found[1]["previous_resets_at"]) == "2026-11-29T05:16:20Z"
    # Re-reading, and the rolling 5 h and weekly windows moving on, add nothing.
    assert _replay(resets) == []
    assert len(resets.recent()) == 2
    assert public_event(resets.recent()[0])["kind"] == "early"


def test_a_gemini_reset_releases_no_claude_or_gpt_hold(resets):
    _replay(resets)
    hit, now = _at("2026-11-23T10:00:00Z"), _at("2026-11-24T05:45:00Z")
    assert resets.released("anti", "antigravity-bridge/gemini-3.5-flash", hit_at=hit, now=now)
    assert not resets.released("anti", "antigravity-bridge/claude-opus-5", hit_at=hit, now=now)
    assert not resets.released("anti", "antigravity-bridge/gpt-oss-120b", hit_at=hit, now=now)
    # A refusal after the reset is a new fact, and an aged reading shows no room.
    assert not resets.released("anti", "gemini-3.5-flash", hit_at=_at("2026-11-24T04:00:00Z"), now=now)
    assert not resets.released("anti", "gemini-3.5-flash", hit_at=hit, now=now + 2 * HOUR)
    # A refusal that stated its own reset is only answered by that very window.
    stated = _at("2026-11-29T05:16:00Z")
    assert resets.released("anti", "gemini-3.5-flash", hit_at=hit, now=now, stated_reset=stated)
    assert not resets.released("anti", "gemini-3.5-flash", hit_at=hit, now=now, stated_reset=stated + DAY)


def test_window_names():
    assert window_seconds("Gemini · 7 days") == 7 * DAY and window_seconds("5 hours") == 5 * HOUR
    assert window_seconds("Weekly") == 7 * DAY and window_seconds("Credits") is None
    assert window_seconds("Gemini 4 Argon · 7 days") == 7 * DAY
    assert applies_to_model("7 days", "gpt-6.1-sol") and applies_to_model("Credits", "x/y")
    assert applies_to_model("7 days · Fable", "claude-fable-5") and not applies_to_model("7 days · Fable", "opus-5")
    assert applies_to_model("Gemini 4 Argon · 7 days", "gemini-4-argon-high")
    assert not applies_to_model("Gemini 4 Argon · 7 days", "gemini-3.5-flash")


# ---- noise ---------------------------------------------------------------------------------

def test_sliding_and_unused_windows_never_reset(resets):
    for i in range(8):  # usage decays while the reset time follows every read
        assert _feed(resets, T0 + i * HOUR, [("5 hours", 90 - i * 10, T0 + i * HOUR + 5 * HOUR),
                                             ("Credits", 90 - i * 10, T0 + i * HOUR + 30 * DAY)]) == []


def test_dips_and_small_moves_are_not_resets(resets):
    reset = T0 + 3 * DAY
    _feed(resets, T0, [("7 days", 85, reset)])
    assert _feed(resets, T0 + 600, [("7 days", 40, reset)]) == []              # a dip, same reset
    assert _feed(resets, T0 + 1200, [("7 days", 37, reset + DAY)]) == []       # later, hardly lower
    assert _feed(resets, T0 + 1800, [("7 days", 20, reset + DAY + 300)]) == []  # lower, reset only drifts
    assert _feed(resets, T0 + 2400, [("7 days", 0, reset)]) == []              # lower, reset earlier
    assert resets.recent() == []


def test_a_gap_in_the_reset_time_keeps_the_comparison(resets):
    _feed(resets, T0, [("7 days", 85, T0 + 3 * DAY)])
    assert _feed(resets, T0 + 600, [("7 days", 0, None)]) == []  # no reset time: proves nothing
    (event,) = _feed(resets, T0 + 1200, [("7 days", 1, T0 + 7 * DAY)])
    assert (event["kind"], event["used_before"]) == ("early", 85.0)


def test_a_passed_reset_needs_a_reading_after_it(resets):
    reset = T0 + HOUR
    _feed(resets, T0, [("5 hours", 100, reset)])
    assert not resets.passed(since=T0, now=reset - 1)
    assert resets.passed(since=T0, now=reset + 1)  # only a reason to read again
    assert resets.recent() == []
    assert _feed(resets, reset + 60, [("5 hours", 100, reset)]) == []  # the provider has not moved yet
    (event,) = _feed(resets, reset + 120, [("5 hours", 0, None)])
    assert event["kind"] == "scheduled"
    assert not resets.passed(since=reset, now=reset + DAY)


def test_stale_duplicate_undated_and_out_of_order_rows_are_ignored(resets):
    reset = T0 + 3 * DAY
    renewed = [("7 days", 0, T0 + 9 * DAY)]
    _feed(resets, T0 + DAY, [("7 days", 90, reset)])
    assert _feed(resets, T0, renewed) == []                        # older than what is known
    assert _feed(resets, T0 + DAY, renewed) == []                  # the same reading time
    late = T0 + DAY + 600
    assert resets.observe(_snapshot(_account(late, renewed)), now=late + 2 * HOUR) == []
    assert resets.observe(_snapshot(_account(late, renewed)), now=late - 60) == []  # from the future
    assert resets.observe(_snapshot(_account(None, renewed, state="UNDATED")), now=late) == []
    assert resets.observe(_snapshot(_account(late, renewed, state="UNKNOWN")), now=late) == []
    row = _account(late, renewed)
    assert resets.observe(_snapshot(row, dict(row)), now=late) == []          # one account twice
    assert resets.observe(_snapshot(_account(late, renewed + renewed)), now=late) == []  # one window twice
    assert resets.observe({"status": "refused"}, now=late) == []
    assert len(resets.observe(_snapshot(row), now=late)) == 1


def test_another_account_plan_or_anonymous_login_is_not_a_reset(resets):
    old, new = [("7 days", 90, T0 + 3 * DAY)], [("7 days", 0, T0 + 8 * DAY)]
    _feed(resets, T0, old)
    assert _feed(resets, T0 + 600, new, ref="other") == []
    assert _feed(resets, T0 + 600, new, plan="free") == []
    anonymous = hashlib.sha256(json.dumps(["codex", None]).encode()).hexdigest()[:12]
    _feed(resets, T0, old, ref=anonymous)
    assert _feed(resets, T0 + 600, new, ref=anonymous) == []


def test_a_reading_back_on_the_old_window_retracts_the_event(resets):
    reset = T0 + 3 * DAY
    _feed(resets, T0, [("7 days", 100, reset)])
    (event,) = _feed(resets, T0 + 600, [("7 days", 0, T0 + 8 * DAY)])
    assert resets.released("acct", "gpt-6.1-sol", hit_at=T0 + 60, now=T0 + 700)
    _feed(resets, T0 + 1200, [("7 days", 100, reset)])
    assert resets.recent() == [] and not resets.released("acct", "gpt-6.1-sol", hit_at=T0 + 60, now=T0 + 1300)
    # The same cycle ending for real later is the same one event.
    assert len(_feed(resets, T0 + 1800, [("7 days", 0, T0 + 8 * DAY)])) == 1
    assert len(resets.recent()) == 1


def test_no_release_while_another_window_of_the_account_is_spent(resets):
    _feed(resets, T0, [("5 hours", 100, T0 + HOUR), ("7 days", 99, T0 + 3 * DAY)])
    assert len(_feed(resets, T0 + HOUR + 60, [("5 hours", 0, T0 + 6 * HOUR), ("7 days", 99, T0 + 3 * DAY)])) == 1
    assert not resets.released("acct", "gpt-6.1-sol", hit_at=T0 + 60, now=T0 + HOUR + 120)


def test_no_release_for_a_window_missing_from_the_newest_reading_or_a_reset_before_the_refusal(resets):
    _feed(resets, T0, [("5 hours", 100, T0 + HOUR), ("7 days", 100, T0 + 3 * DAY)])
    assert len(_feed(resets, T0 + HOUR + 60, [("5 hours", 0, T0 + 6 * HOUR)])) == 1
    assert not resets.released("acct", "gpt-6.1-sol", hit_at=T0 + 60, now=T0 + HOUR + 120)
    _feed(resets, T0, [("5 hours", 100, T0 + 300)], ref="two")
    assert len(_feed(resets, T0 + 1200, [("5 hours", 10, T0 + 5 * HOUR)], ref="two")) == 1
    assert not resets.released("two", "gpt-6.1-sol", hit_at=T0 + 900, now=T0 + 1300)
    assert resets.released("two", "gpt-6.1-sol", hit_at=T0 + 100, now=T0 + 1300)


def test_another_tiers_fresh_reading_lends_no_freshness(resets):
    other = ("Claude & GPT · 7 days", 50, T0 + 3 * DAY)
    _feed(resets, T0, [("Gemini · 7 days", 90, T0 + 3 * DAY), other])
    assert len(_feed(resets, T0 + 600, [("Gemini · 7 days", 0, T0 + 7 * DAY), other])) == 1
    hit = T0 + 60
    assert resets.released("acct", "gemini-3.5-flash", hit_at=hit, now=T0 + 700)
    late = T0 + 600 + 2 * HOUR
    _feed(resets, late, [other])  # the Gemini window is missing from the newest reading
    assert not resets.released("acct", "gemini-3.5-flash", hit_at=hit, now=late + 60)
    # Its own fresh reading answers again.
    _feed(resets, late + 60, [("Gemini · 7 days", 1, T0 + 7 * DAY), other])
    assert resets.released("acct", "gemini-3.5-flash", hit_at=hit, now=late + 120)


@pytest.mark.parametrize("times", [(0, 60, 90), (0, 20, 40, 65), (0, 60, 61, 62, 63)])
def test_frequent_readings_keep_the_anchor_of_a_window_without_a_length(resets, times):
    reset = T0 + 20 * DAY
    for i, offset in enumerate(times):  # the stated reset jitters by a second
        assert _feed(resets, T0 + offset, [("Credits", 90, reset + i % 2)]) == []
    (event,) = _feed(resets, T0 + 120, [("Credits", 0, reset + 30 * DAY)])
    assert event["kind"] == "early"


@pytest.mark.parametrize("step", [1, 3, 20, 59, 61, 1800])
def test_a_sliding_window_never_anchors_at_any_read_rate(resets, step):
    for i in range(100):
        at = T0 + i * step
        assert _feed(resets, at, [("Credits", 90, at + 30 * DAY)]) == []
    assert _feed(resets, at + 1200, [("Credits", 0, at + 1200 + 30 * DAY)]) == []


def test_a_loosely_named_spent_tier_blocks_the_release(resets):
    _feed(resets, T0, [("5 hours", 100, T0 + HOUR), ("7 days · Sonnet only", 100, T0 + 3 * DAY)])
    _feed(resets, T0 + HOUR + 60, [("5 hours", 0, T0 + 6 * HOUR), ("7 days · Sonnet only", 100, T0 + 3 * DAY)])
    assert not resets.released("acct", "claude-sonnet-5", hit_at=T0 + 60, now=T0 + HOUR + 120)
    assert resets.released("acct", "claude-opus-5", hit_at=T0 + 60, now=T0 + HOUR + 120)


def test_an_open_transaction_of_the_caller_is_left_alone(resets):
    resets._conn.execute("BEGIN")
    assert _feed(resets, T0, [("7 days", 1, T0 + DAY)]) == [] and resets._conn.in_transaction
    resets._conn.execute("ROLLBACK")


# ---- the host and the coordinator ----------------------------------------------------------

def _host(monkeypatch, *, connection, model="gpt-6.1-sol"):
    store, tasks = ModelProfileStore(), TaskStore(":memory:")
    store.upsert_connection({"connection_id": "c", "name": "c", "enabled": True, **connection})
    executor = "codex" if connection["auth_method"] == "external_cli_session" else "opencode"
    store.upsert_binding({"binding_id": "b", "name": "b", "connection_id": "c", "executor_id": executor,
                          "model_id": model, "enabled": True})
    host = object.__new__(trusted_host.CombinedTrustedHost)
    host._store, host._task_store, host._control_store = store, tasks, PlatformControlStore(tasks)
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {}, raising=False)
    return host


def _fail(host, at, *, stated=""):
    task = host._task_store.create_task(title="t", repository="o/r", executor_kind="codex", binding_ref="b")
    host._task_store._conn.execute(
        "UPDATE tasks SET status='FAILED', failure_classification='api_error_429', failure_at=?, failure_reset_at=?, "
        "updated_at=? WHERE id=?", (_iso(at), stated, _iso(at), task.id))
    host._task_store._conn.commit()
    return task


NATIVE = {"provider": "codex", "base_url": "https://chatgpt.com", "auth_method": "external_cli_session",
          "account_ref": "acct"}


class _Woken:
    def __init__(self):
        self.calls = 0

    def request_reevaluation(self):
        self.calls += 1


@pytest.mark.parametrize("stated", [False, True])
def test_a_real_429_hold_ends_with_the_reset_and_held_work_wakes(monkeypatch, stated):
    host, now = _host(monkeypatch, connection=NATIVE), time.time()
    host._coordinator = _Woken()
    host._subscription_quota_cache = (time.monotonic(), {})
    old_reset = now + 4 * DAY
    _fail(host, now - 1200, stated=_iso(old_reset) if stated else "")
    connection, binding = host._store.get_connection_public("c"), host._store.get_binding_public("b")
    host._observe_quota_resets(_snapshot(_account(now - 1500, [("7 days", 100, old_reset)])))
    assert host._coordinator.calls == 0 and host._limit_hit_until(connection, binding) is not None
    host._observe_quota_resets(_snapshot(_account(now - 60, [("7 days", 0, now + 7 * DAY)])))
    assert host._coordinator.calls == 1 and "_subscription_quota_cache" not in host.__dict__
    assert host._limit_hit_until(connection, binding) is None
    assert host._quota_reset_released("b", now - 1200)
    assert host._recent_quota_resets()[0]["kind"] == "early"
    # A refusal after the reset holds the account again.
    _fail(host, now - 30)
    assert host._limit_hit_until(connection, binding) is not None
    assert not host._quota_reset_released("b", now - 30)


def test_a_passed_reset_reads_again_at_once(monkeypatch):
    host, now = _host(monkeypatch, connection=NATIVE), time.time()
    host._coordinator = _Woken()
    host._observe_quota_resets(_snapshot(_account(now - 60, [("5 hours", 100, now + 600)])))
    assert host._coordinator.calls == 0
    monkeypatch.setattr(trusted_host.time, "time", lambda: now + 601)
    host._observe_quota_resets(_snapshot())
    assert host._coordinator.calls == 1
    host._observe_quota_resets(_snapshot())
    assert host._coordinator.calls == 1


def test_a_gateway_upstream_is_released_only_through_its_one_account_and_tier(monkeypatch):
    gateway = {"provider": "openai-compatible", "base_url": "http://127.0.0.1:3425/v1", "auth_method": "none"}
    host, now = _host(monkeypatch, connection=gateway, model="antigravity-bridge/gemini-3.5-flash"), time.time()
    monkeypatch.setattr("reverse_agent.platform_v1.resource_allowances.gateway_connection", lambda c: True)
    _fail(host, now - 1200)
    connection, binding = host._store.get_connection_public("c"), host._store.get_binding_public("b")
    for at, used, reset in ((now - 1500, 100, now + DAY), (now - 60, 0, now + 7 * DAY)):
        host._observe_quota_resets(_snapshot(_account(at, [("Gemini · 7 days", used, reset),
                                                           ("Claude & GPT · 7 days", 98.1, now + DAY)],
                                                      ref="anti", provider="antigravity-bridge")))
    host._magpie_provider_accounts = {"antigravity-bridge": ["anti", "second"]}
    assert host._limit_hit_until(connection, binding) is not None
    host._magpie_provider_accounts = {"antigravity-bridge": ["anti"]}
    assert host._limit_hit_until(connection, binding) is None


def test_goal_timeline_shows_the_resets_of_its_accounts(monkeypatch):
    host, now = _host(monkeypatch, connection=NATIVE), time.time()
    task = host._task_store.create_task(title="t", repository="o/r", executor_kind="codex", binding_ref="b")
    for ref in ("acct", "other"):
        for at, used, reset in ((now - 60, 100, now + DAY), (now + 60, 0, now + 7 * DAY)):
            host._control_store.quota_resets.observe(
                _snapshot(_account(at, [("7 days", used, reset)], ref=ref)), now=now + 120)
    goal = {"task_links": [{"task_id": task.id, "attempts": []}]}
    assert [e["account_ref"] for e in host._goal_quota_resets(goal)] == ["acct"]
    assert host._goal_quota_resets({"task_links": []}) == []


def test_observation_faults_never_reach_dispatch():
    object.__new__(trusted_host.CombinedTrustedHost)._observe_quota_resets(_snapshot())


def test_reevaluation_ends_the_idle_wait_and_sweeps_stuck_goals(tmp_path):
    coordinator = object.__new__(UnattendedCoordinator)
    coordinator._stop, coordinator._reevaluate = threading.Event(), threading.Event()
    coordinator._reevaluate.set()
    started = time.monotonic()
    coordinator._idle(started + 60)
    assert time.monotonic() - started < 5
    # One pass of the loop: the mark is taken and unchanged stuck goals are due again.
    coordinator._lifecycle_lock, coordinator._thread = threading.RLock(), None
    coordinator._recovering, coordinator.reconcile_interval = False, 3600
    coordinator._swept = {"goal": ([], time.monotonic() + 3600)}
    swept = []
    coordinator._sweep_escalations = lambda *, stop_event: swept.append(dict(coordinator._swept))

    def tick(*, background):
        coordinator._stop.set()
        raise RuntimeError("end")

    coordinator.tick, coordinator.idle_wait = tick, lambda dispatched: 0
    coordinator.quota_wait = lambda wait: False
    coordinator._batch_threads, coordinator._active_task_ids = set(), set()
    coordinator._manual_tick_idle = threading.Event()
    coordinator._manual_tick_idle.set()
    coordinator._last_error, coordinator._dispatch_active = "", False
    coordinator._run()
    assert swept == [{}] and not coordinator._reevaluate.is_set()
