"""Provider-free tests for #1531 real resource settlement host wiring."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import OWNER_WINDOW_MODE, PlatformControlStore
from reverse_agent.platform_v1.multi_account.alerts import evaluate_alerts
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.real_settlement import (
    reconcile_task_usage_from_magpie,
    settle_account_interval_from_store,
)
from reverse_agent.platform_v1.run_store import TaskStore
from test_unattended_coordinator import _budget_window


def _magpie_row(
    *,
    rid: str = "rid-1",
    session: str = "sess-1",
    cost: float | None = 0.045,
    priced: bool = True,
    inp: int = 1000,
    out: int = 250,
    cache_read: int = 4000,
    cache_write: int = 100,
    reasoning: int = 50,
    t: str = "2026-11-26T10:01:00Z",
) -> dict:
    return {
        "rid": rid,
        "session": session,
        "t": t,
        "t_epoch": datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp(),
        "provider_account": "acct-wb",
        "served": "workbuddy/kimi-k3.1-pro",
        "model": "workbuddy/kimi-k3.1-pro",
        "input": inp,
        "output": out,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "cache_write_1h": 0,
        "reasoning": reasoning,
        "cost_usd": cost,
        "priced": priced,
        "handed_on": False,
    }


def test_positive_identity_magpie_reconciliation_upgrades_unknown_and_avoids_double_count(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "settle.sqlite3")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    win = _budget_window(autonomy, policy_id="magpie-reconcile", max_tokens=100_000, reservation=50_000)

    task = store.create_task(title="reconcile-me", executor_kind="opencode", binding_ref="magpie-wb")
    epoch, _ = control.claim_task(window_id=win.id, task_id=task.id, owner="o", lease_ms=60_000)
    store.add_event(
        task.id,
        event_type="EXECUTOR_COMPLETED",
        title="done",
        description="completed",
        metadata={"agent_session_id": "sess-1"},
    )
    # Local executor recorded a PARTIAL/UNKNOWN placeholder before Magpie usage reconciliation ran.
    store.append_usage_observation(
        task.id,
        observation_id="local-partial",
        execution_id=task.execution_id,
        role="executor",
        model_id="workbuddy/kimi-k3.1-pro",
        provider_id="magpie",
        source_kind="step_finish",
        source_id="local-1",
        status="PARTIAL",
        input_units=999999,
        output_units=1,
        reasoning_units=None,
        cache_read_units=None,
        cache_write_units=None,
        cost_micro_units=None,
    )

    rows = [_magpie_row(rid="rid-a", session="sess-1", cost=0.045, priced=True)]
    res = reconcile_task_usage_from_magpie(store, store.get_task(task.id), usage_rows=rows)
    assert res["status"] == "reconciled"
    assert res["observation_status"] == "OBSERVED"
    assert res["cost_micro_units"] == 45_000

    # Also test superseding a local unpriced OBSERVED row of the SAME execution_id without double-counting:
    store.append_usage_observation(
        task.id,
        observation_id="local-unpriced-observed",
        execution_id=task.execution_id,
        role="executor",
        model_id="workbuddy/kimi-k3.1-pro",
        provider_id="magpie",
        source_kind="step_finish",
        source_id="local-2",
        status="OBSERVED",
        input_units=50000,
        output_units=5000,
        reasoning_units=0,
        cache_read_units=0,
        cache_write_units=0,
        cost_micro_units=None,
    )

    # Idempotent second call skips without duplicating observations.
    res2 = reconcile_task_usage_from_magpie(store, store.get_task(task.id), usage_rows=rows)
    assert res2 == {"status": "skipped", "reason": "already_reconciled"}

    control.complete_task_claim(window_id=win.id, task_id=task.id, owner="o", epoch=epoch, result="success")
    # Weighted cost-equivalent units come ONLY from magpie_measured:
    # input(1000) + output(250) + reasoning(50) + 0.1*cache_read(400) + 1.25*cache_write(125) = 1825
    # Local 999999 PARTIAL row is NOT summed with Magpie.
    w = control.get_window(win.id)
    assert w.observed_token_units == 1825
    assert w.observed_cost_micro_units == 45_000
    assert w.unknown_observation_count == 0
    store._conn.close()


def test_unpriced_magpie_row_stays_unknown_cost_not_zero(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "unpriced.sqlite3")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    cash_win = _budget_window(autonomy, policy_id="cash-cap", max_tokens=100_000, reservation=50_000)
    control._conn.execute("UPDATE platform_autonomous_windows SET max_cost_micro_units = 5000000 WHERE id = ?", (cash_win.id,))
    control._conn.commit()

    task = store.create_task(title="unpriced-magpie", executor_kind="opencode", binding_ref="b1")
    epoch, _ = control.claim_task(window_id=cash_win.id, task_id=task.id, owner="o", lease_ms=60_000)
    store.add_event(task.id, event_type="EXECUTOR_COMPLETED", title="done", description="ok", metadata={"agent_session_id": "sess-unpriced"})

    res = reconcile_task_usage_from_magpie(
        store,
        store.get_task(task.id),
        usage_rows=[_magpie_row(rid="rid-u", session="sess-unpriced", cost=None, priced=False)],
    )
    assert res["status"] == "reconciled"
    assert res["cost_micro_units"] is None
    assert res["unpriced_calls"] == 1

    control.complete_task_claim(window_id=cash_win.id, task_id=task.id, owner="o", epoch=epoch, result="success")
    w = control.get_window(cash_win.id)
    # Fail-closed: cash-enforced window must NOT treat unpriced cost as $0.00!
    assert (w.status, w.stop_reason) == ("BLOCKED", "usage_unknown")
    store._conn.close()


def test_pre_dispatch_refusal_settles_confirmed_zero_in_owner_window(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "refusal.sqlite3")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    now = datetime.now(timezone.utc)
    policy = {
        "policy_id": "owner-zero-refusal",
        "policy_revision": 1,
        "owner_identity": "owner@example",
        "starts_at": (now - timedelta(seconds=5)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"],
        "capabilities": ["execute_task", "land_reviewed_pr"],
        "max_tasks": 12,
        "max_token_units": 80_000_000,
        "per_task_token_reservation": 6_600_000,
        "confirmation": "ACTIVATE",
    }
    autonomy.activate(policy)
    win = control.active_window()
    assert win is not None

    task = store.create_task(title="refused-review", repository="dddd2024/Nerelan", executor_kind="codex", binding_ref="chatgpt-gpt")
    epoch, _ = control.claim_task(window_id=win.id, task_id=task.id, owner="o", lease_ms=60_000)
    control._conn.execute("UPDATE platform_autonomous_windows SET confirmation_mode = ? WHERE id = ?", (OWNER_WINDOW_MODE, win.id))
    control._conn.commit()
    store.classify_failure(task.id, classification="review_not_independent", detail="review_not_independent")
    control.complete_task_claim(window_id=win.id, task_id=task.id, owner="o", epoch=epoch, result="terminal:FAILED")

    updated = control.get_window(win.id)
    res_row = store._conn.execute("SELECT state, observed_token_units FROM platform_budget_reservations WHERE task_id = ?", (task.id,)).fetchone()
    # Refused pre-dispatch task must settle at 0 rather than burning 6.6M UNKNOWN reservation!
    assert (res_row["state"], res_row["observed_token_units"]) == ("RECONCILED", 0)
    assert updated.observed_token_units == 0
    assert updated.unknown_observation_count == 0
    store._conn.close()


def test_settle_account_interval_from_store_delegates_to_magpie_settlement(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "interval.sqlite3")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    win = _budget_window(autonomy, policy_id="interval", max_tokens=100_000, reservation=50_000)

    t1 = store.create_task(title="wb-task", executor_kind="opencode", binding_ref="wb-b")
    e1, _ = control.claim_task(window_id=win.id, task_id=t1.id, owner="o", lease_ms=60_000)
    store.add_event(t1.id, event_type="EXECUTOR_COMPLETED", title="done", description="ok", metadata={"agent_session_id": "sess-wb"})
    rows = [_magpie_row(rid="rid-wb-1", session="sess-wb", cost=0.10, priced=True, t="2026-11-26T10:05:00Z")]
    reconcile_task_usage_from_magpie(store, store.get_task(t1.id), usage_rows=rows)
    control.complete_task_claim(window_id=win.id, task_id=t1.id, owner="o", epoch=e1, result="success")
    store._conn.execute("UPDATE platform_budget_reservations SET account_ref = 'acct-wb' WHERE task_id = ?", (t1.id,))
    store._conn.commit()

    before = {"account_ref": "acct-wb", "source": "magpie", "observed_at": "2026-11-26T10:00:00Z", "window": "credits", "credits_remaining": 500.0, "resets_at": "2026-12-01T00:00:00Z"}
    after = {"account_ref": "acct-wb", "source": "magpie", "observed_at": "2026-11-26T10:10:00Z", "window": "credits", "credits_remaining": 494.0, "resets_at": "2026-12-01T00:00:00Z"}
    conv = {"evidenced": True, "account_ref": "acct-wb", "window": "credits", "credits_per_usd": 60.0, "provenance": "magpie-ledger", "observed_at": "2026-11-26T10:10:00Z"}

    settled = settle_account_interval_from_store(store, before=before, after=after, magpie_rows=rows, account_ref="acct-wb", window_id=win.id, credit_conversion=conv)
    assert settled["status"] == "PARTIAL"  # money estimate stays ESTIMATED residual
    assert settled["account_delta_credits"] == 6.0
    assert settled["unattributed_residual_credits"] == 0.0
    assert len(settled["tasks"]) == 1
    store._conn.close()


def test_magpie_disabled_performs_zero_network_calls(tmp_path: Path, monkeypatch) -> None:
    store = TaskStore(tmp_path / "offline.sqlite3")
    task = store.create_task(title="offline", executor_kind="opencode")
    monkeypatch.delenv("REVERSE_AGENT_MAGPIE", raising=False)
    res = reconcile_task_usage_from_magpie(store, task, env={})
    assert res == {"status": "skipped", "reason": "magpie_disabled"}
    store._conn.close()


def test_pool_monitor_alerts_on_exhausted_stop_reason_and_unknown_usage() -> None:
    runtime = {
        "budget": {
            "max_token_units": 80_000_000,
            "remaining_token_units": 0,
            "stop_reason": "usage_unknown_budget_reached",
            "unknown_observation_count": 12,
        }
    }
    alerts = evaluate_alerts({"source": "none"}, runtime, MultiAccountConfig(), now=1000.0)
    keys = {(a.code, a.subject) for a in alerts}
    assert ("window_budget_exhausted", "window") in keys
    assert ("window_unknown_usage", "window") in keys
