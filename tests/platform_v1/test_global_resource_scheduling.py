"""Provider-free tests for #1533 global resource scheduling foundation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from reverse_agent.model_access.magpie import parse_quotas
from reverse_agent.platform_v1 import resource_allowances as ra
from reverse_agent.platform_v1.model_router import ModelSelectionError, select_model
from reverse_agent.platform_v1.routing_inputs import (
    credit_multiplier_for,
    effective_pool_limits,
    read_overrides,
)
from test_model_router import FIXTURE_TABLE, candidate, choose


def test_physical_pool_max_in_flight_spreads_work_and_blocks_when_saturated() -> None:
    pool_a = candidate("b-zen", "opencode-zen-free/glm-5.3", cost="free")
    pool_b = candidate("b-sense", "token-sensenova/glm-5.3", cost="free")
    limits = {"opencode-zen-free": {"max_in_flight": 1}, "token-sensenova": {"max_in_flight": 1}}

    # When opencode-zen-free already has 1 task running, router diverts 2nd concurrent task to token-sensenova.
    decision = choose(
        [pool_a, pool_b],
        difficulty=2,
        kind="code",
        in_flight_by_upstream={"opencode-zen-free": 1},
        pool_limits=limits,
    )
    assert decision["binding_ref"] == "b-sense"
    assert decision["excluded_summary"] == {"pool_concurrency_limit": 1}

    # When every eligible pool is at cap, ModelSelectionError marks temporary_resource_blocked.
    with pytest.raises(ModelSelectionError, match="no_runnable_model") as exc_info:
        choose(
            [pool_a, pool_b],
            difficulty=2,
            kind="code",
            in_flight_by_upstream={"opencode-zen-free": 1, "token-sensenova": 1},
            pool_limits=limits,
        )
    assert exc_info.value.decision.get("temporary_resource_blocked") is True
    assert isinstance(exc_info.value.decision.get("retry_at"), float)


def test_real_credit_multiplier_ranks_lower_burn_route_first() -> None:
    cheap = candidate("wb-low", "workbuddy/kimi-k3", cost="subscription", credit_multiplier=1.0)
    expensive = candidate("wb-high", "workbuddy/claude-sonnet-4-6", cost="subscription", credit_multiplier=5.0)
    # Give both identical tier=5 via custom capability table so only credit burn separates them.
    cap_table = {
        "workbuddy/kimi-k3": {"tiers": {"code": 4}},
        "workbuddy/claude-sonnet-4-6": {"tiers": {"code": 4}},
    }
    decision = select_model(
        [expensive, cheap],
        difficulty=3,
        kind="code",
        capability_table=cap_table,
        profiles={
            "wb-low": {"task_buckets": {"code:4": {"attempts": 3, "success_rate": 1.0, "timeouts": 0}}},
            "wb-high": {"task_buckets": {"code:4": {"attempts": 3, "success_rate": 1.0, "timeouts": 0}}},
        },
        allow_paid=True,
    )
    assert decision["binding_ref"] == "wb-low"
    by_id = {c["binding_id"]: c for c in decision["candidates"]}
    assert by_id["wb-low"]["score_breakdown"]["credit_cost_penalty"] == 0.0
    assert by_id["wb-high"]["score_breakdown"]["credit_cost_penalty"] > 0.9


def test_overrides_validate_credit_multiplier_and_pool_limits(tmp_path: Path) -> None:
    state = tmp_path / "model_setup_state.json"
    overrides = tmp_path / "model_routing_overrides.json"
    overrides.write_text(
        json.dumps({
            "models": {"workbuddy/glm-5.3": {"credit_multiplier": 4.8}},
            "pool_limits": {"opencode-zen-free": {"max_in_flight": 2}},
        }),
        encoding="utf-8",
    )
    loaded = read_overrides(state)
    assert credit_multiplier_for({"binding_id": "b1", "model_id": "workbuddy/glm-5.3"}, loaded) == 4.8
    assert credit_multiplier_for({"binding_id": "b2", "model_id": "workbuddy/other"}, loaded) == 1.0
    limits = effective_pool_limits(loaded)
    assert limits["opencode-zen-free"]["max_in_flight"] == 2
    assert limits["token-sensenova"]["max_in_flight"] == 1


def test_free_channel_task_adaptation_steers_light_work_to_free_and_keeps_hard_work_guarded() -> None:
    free_light = candidate("hy4-free", "auto/hy4flash-free", cost="free")
    sub_heavy = candidate("sub-opus", "claude/opus", cost="subscription")
    cap_table = {
        "auto/hy4flash-free": {"tiers": {"writing": 3, "code": 2}},
        "claude/opus": {"tiers": {"writing": 5, "code": 5}},
    }
    profiles = {
        "hy4-free": {"task_buckets": {
            "writing:3": {"attempts": 3, "success_rate": 1.0, "timeouts": 0},
            "code:2": {"attempts": 3, "success_rate": 1.0, "timeouts": 0},
        }},
        "sub-opus": {"task_buckets": {
            "writing:5": {"attempts": 3, "success_rate": 1.0, "timeouts": 0},
            "code:5": {"attempts": 3, "success_rate": 1.0, "timeouts": 0},
        }},
    }
    light = select_model(
        [sub_heavy, free_light], difficulty=2, kind="writing",
        capability_table=cap_table, profiles=profiles, allow_paid=True,
    )
    assert light["binding_ref"] == "hy4-free"
    assert light["score_breakdown"]["free_channel_fit_bonus"] == 0.25

    # Harder task (difficulty=4) does not qualify free_light and preserves tier protection.
    hard = select_model(
        [sub_heavy, free_light], difficulty=4, kind="code",
        capability_table=cap_table, profiles=profiles, allow_paid=True,
    )
    assert hard["binding_ref"] == "sub-opus"
    assert hard["score_breakdown"]["free_channel_fit_bonus"] == 0.0


def test_daily_pool_opportunity_urgency_increases_near_reset() -> None:
    now = datetime(2026, 11, 27, 5, 0, tzinfo=timezone.utc)
    ts = now.timestamp()
    soon_iso = (now + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    raccoon = {
        "provider": "raccoon", "kind": "subscription", "plan": "Pro", "user": "u1",
        "readAt": now.isoformat(),
        "windows": [{"name": "Daily pool", "used": 20, "remaining": 80, "limit": 2100, "resetsAt": soon_iso}],
    }
    parsed = parse_quotas({"object": "list", "data": [raccoon]}, now)
    allowances = ra.read_allowances({"status": "available", "accounts": parsed}, now=ts)
    assert "raccoon" in allowances.get("daily_pools", {})

    gateway_conn = {"connection_id": "magpie", "auth_method": "none", "base_url": "http://127.0.0.1:3425/v1"}
    owner = {"models": {"raccoon/glm-5.3": {"cost_class": "subscription"}}}
    cost_class, resources = ra.effective_cost(
        {"binding_id": "r-m", "model_id": "raccoon/glm-5.3", "connection_id": "magpie"},
        gateway_conn,
        owner,
        allowances,
        now=ts,
    )
    assert cost_class == "subscription"
    assert "daily_pool" in resources
    assert 0.0 < ra.urgency(resources, now=ts) < 1.0


def test_claim_time_pool_capacity_blocks_concurrent_gateway_dispatch(tmp_path: Path) -> None:
    from reverse_agent.platform_v1.autonomy import AutonomyService
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    from test_unattended_coordinator import _budget_window

    state = tmp_path / "model_setup_state.json"
    overrides = tmp_path / "model_routing_overrides.json"
    overrides.write_text(
        json.dumps({"pool_limits": {"token-sensenova": {"max_in_flight": 1}}}),
        encoding="utf-8",
    )

    class _FakeStore:
        _state_path = state

        def __init__(self) -> None:
            self._bindings = [{
                "binding_id": "b-sense",
                "connection_id": "magpie",
                "model_id": "token-sensenova/glm-5.3",
                "executor_id": "opencode",
            }]
            self._conns = {"magpie": {"connection_id": "magpie", "auth_method": "none", "account_ref": "magpie"}}

        def list_bindings_public(self):
            return list(self._bindings)

        def list_connections_public(self):
            return list(self._conns.values())

        def get_connection_public(self, cid: str):
            return self._conns[cid]

    task_store = TaskStore(tmp_path / "pool-claim.sqlite3")
    control = PlatformControlStore(task_store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    win = _budget_window(autonomy, policy_id="pool-cap", max_tokens=100_000, reservation=10_000)

    t1 = task_store.create_task(title="pool-1", executor_kind="opencode", binding_ref="b-sense")
    t2 = task_store.create_task(title="pool-2", executor_kind="opencode", binding_ref="b-sense")

    host = CombinedTrustedHost.__new__(CombinedTrustedHost)
    host._store = _FakeStore()
    host._task_store = task_store
    host._control_store = control

    # Claim t1 (status remains QUEUED until background worker starts, matching coordinator fan-out):
    epoch1, _ = control.claim_task(window_id=win.id, task_id=t1.id, owner="o", lease_ms=60_000)
    by_id = {b["binding_id"]: b for b in host._store.list_bindings_public()}
    conns = {c["connection_id"]: c for c in host._store.list_connections_public()}
    assert host._in_flight_by_upstream(by_id, conns) == {"token-sensenova": 1}

    # Re-evaluating t1 itself does not self-block; preparing t2 against the same capped pool raises QUOTA_WAIT.
    host._prepare_task_quota(task_store.get_task(t1.id))
    with pytest.raises(TaskStoreError, match="QUOTA_WAIT:pool_concurrency_limit:token-sensenova:1/1"):
        host._prepare_task_quota(task_store.get_task(t2.id))

    # Releasing t1's claim frees the physical pool slot for t2.
    control.complete_task_claim(window_id=win.id, task_id=t1.id, owner="o", epoch=epoch1, result="success")
    host._prepare_task_quota(task_store.get_task(t2.id))
    task_store._conn.close()


def test_pool_concurrency_check_handles_lockless_store_and_fails_closed_on_sqlite_error(tmp_path: Path) -> None:
    import sqlite3
    from types import SimpleNamespace
    from reverse_agent.platform_v1.run_store import TaskStoreError
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    state = tmp_path / "model_setup_state.json"
    overrides = tmp_path / "model_routing_overrides.json"
    overrides.write_text(
        json.dumps({"pool_limits": {"token-sensenova": {"max_in_flight": 1}}}),
        encoding="utf-8",
    )

    class _FakeStore:
        _state_path = state

        def list_bindings_public(self):
            return [{"binding_id": "b-sense", "connection_id": "magpie", "model_id": "token-sensenova/glm-5.3"}]

        def list_connections_public(self):
            return [{"connection_id": "magpie", "auth_method": "none", "account_ref": "magpie"}]

        def get_connection_public(self, _cid: str):
            return {"connection_id": "magpie", "auth_method": "none", "account_ref": "magpie"}

    # Lockless minimal TaskStore double works cleanly (does not raise AttributeError).
    raw_conn = sqlite3.connect(":memory:")
    raw_conn.row_factory = sqlite3.Row
    raw_conn.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT, binding_ref TEXT)")
    raw_conn.execute("INSERT INTO tasks VALUES ('t-other', 'RUNNING', 'b-sense')")
    host = CombinedTrustedHost.__new__(CombinedTrustedHost)
    host._store = _FakeStore()
    host._task_store = SimpleNamespace(_conn=raw_conn)

    task = SimpleNamespace(id="t-new", binding_ref="b-sense", executor_kind="opencode", status="QUEUED")
    with pytest.raises(TaskStoreError, match="QUOTA_WAIT:pool_concurrency_limit:token-sensenova:1/1"):
        host._prepare_task_quota(task)

    # DB failure fails closed during _prepare_task_quota instead of bypassing pool cap.
    raw_conn.close()
    with pytest.raises(TaskStoreError, match="QUOTA_WAIT:pool_concurrency_check_failed"):
        host._prepare_task_quota(task)


def test_shared_account_pool_rpm_tpm_observed_multipliers_and_promotional_free(tmp_path: Path) -> None:
    from types import SimpleNamespace
    import sqlite3
    from reverse_agent.platform_v1.run_store import TaskStoreError
    from reverse_agent.platform_v1.routing_inputs import (
        configured_credit_multiplier_for,
        observed_credit_multipliers,
        pool_key_for_upstream,
        resolve_credit_multiplier,
    )
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    state = tmp_path / "model_setup_state.json"
    overrides = tmp_path / "model_routing_overrides.json"
    overrides.write_text(
        json.dumps({
            "models": {"workbuddy/claude-sonnet-4-6": {"credit_multiplier": 6.0}},
            "pool_limits": {
                "wb-shared": {"max_in_flight": 1, "rpm_limit": 2, "tpm_limit": 5000},
                "workbuddy": {"max_in_flight": 1, "shared_account_pool": "wb-shared"},
                "workbuddy-ai": {"max_in_flight": 1, "shared_account_pool": "wb-shared"},
            },
            "compliance_excluded_providers": ["copilot"],
        }),
        encoding="utf-8",
    )
    loaded = read_overrides(state)
    assert loaded["compliance_excluded_providers"] == ["copilot"]
    assert pool_key_for_upstream("workbuddy", effective_pool_limits(loaded)) == "wb-shared"
    limits = effective_pool_limits(loaded)
    assert pool_key_for_upstream("workbuddy-ai", limits) == "wb-shared"

    wb = candidate("wb", "workbuddy/glm-5.3", cost="subscription")
    wb_ai = candidate("wb-ai", "workbuddy-ai/glm-5.3", cost="subscription")
    alt = candidate("zen", "opencode-zen-free/glm-5.3", cost="free")
    # Shared physical pool saturation blocks BOTH workbuddy and workbuddy-ai, routing to zen.
    shared_dec = choose(
        [wb, wb_ai, alt],
        in_flight_by_upstream={"wb-shared": 1},
        pool_limits=limits,
    )
    assert shared_dec["binding_ref"] == "zen"
    assert shared_dec["excluded_summary"] == {"pool_concurrency_limit": 2}

    # RPM and TPM limits inherited from shared pool ("wb-shared") exclude logical workbuddy/workbuddy-ai.
    with pytest.raises(ModelSelectionError) as rpm_exc:
        choose([wb, wb_ai], rpm_by_pool={"wb-shared": 2}, pool_limits=limits)
    assert rpm_exc.value.decision["excluded_summary"] == {"pool_rpm_limit": 2}
    assert rpm_exc.value.decision.get("temporary_resource_blocked") is True

    with pytest.raises(ModelSelectionError) as tpm_exc:
        choose([wb, wb_ai], tpm_by_pool={"wb-shared": 5000}, pool_limits=limits)
    assert tpm_exc.value.decision["excluded_summary"] == {"pool_tpm_limit": 2}
    assert tpm_exc.value.decision.get("temporary_resource_blocked") is True

    # Auto per-namespace multiplier derivation without baseline_credits_per_1m, and Owner config wins precedence.
    obs = observed_credit_multipliers([
        {"served_model": "workbuddy/kimi-k3", "provider": "anthropic", "tokens": {"input": 500_000, "output": 500_000}, "reported_credits": 100.0},
        {"served_model": "workbuddy/claude-sonnet-4-6", "provider": "anthropic", "tokens": {"input": 500_000, "output": 500_000}, "reported_credits": 400.0},
    ])
    assert configured_credit_multiplier_for({"binding_id": "wb-1", "model_id": "workbuddy/kimi-k3"}, loaded) is None
    res_obs = resolve_credit_multiplier({"binding_id": "wb-1", "model_id": "workbuddy/kimi-k3"}, loaded, observed_multipliers=obs)
    assert res_obs["source"] == "observed" and res_obs["effective"] == 1.0
    res_cfg = resolve_credit_multiplier({"binding_id": "wb-cfg", "model_id": "workbuddy/claude-sonnet-4-6"}, loaded, observed_multipliers=obs)
    assert res_cfg["source"] == "configured" and res_cfg["effective"] == 6.0 and res_cfg["observed"] == 4.0 and res_cfg["discrepancy_ratio"] == pytest.approx(4.0 / 6.0, rel=1e-3)
    res_unknown = resolve_credit_multiplier({"binding_id": "wb-unk", "model_id": "workbuddy/unknown-m"}, loaded, observed_multipliers=obs)
    assert res_unknown["source"] == "unknown" and res_unknown["effective"] is None

    # Unknown subscription multiplier incurs uncertainty penalty compared with known 1.0x.
    cap_table = {
        "workbuddy/kimi-k3": {"tiers": {"code": 4}},
        "workbuddy/unknown-m": {"tiers": {"code": 4}},
    }
    known_c = candidate("wb-k", "workbuddy/kimi-k3", cost="subscription", credit_multiplier=1.0, credit_multiplier_info=res_obs)
    unk_c = candidate("wb-u", "workbuddy/unknown-m", cost="subscription", credit_multiplier=1.0, credit_multiplier_info=res_unknown)
    ranked_dec = select_model(
        [unk_c, known_c], difficulty=3, kind="code", capability_table=cap_table, allow_paid=True,
        profiles={
            "wb-k": {"task_buckets": {"code:4": {"attempts": 3, "success_rate": 1.0, "timeouts": 0}}},
            "wb-u": {"task_buckets": {"code:4": {"attempts": 3, "success_rate": 1.0, "timeouts": 0}}},
        },
    )
    assert ranked_dec["binding_ref"] == "wb-k"
    assert ranked_dec["candidates"][0]["score_breakdown"]["credit_cost_uncertainty_penalty"] == 0.0
    assert ranked_dec["candidates"][1]["score_breakdown"]["credit_cost_uncertainty_penalty"] == 0.15

    # Promotional free channel promotion + fail-closed when remaining is missing & unlimited is False.
    now_dt = datetime(2026, 11, 27, 5, 0, tzinfo=timezone.utc)
    ts = now_dt.timestamp()
    promo_iso = (now_dt + timedelta(hours=3)).isoformat().replace("+00:00", "Z")
    promo_acct = {
        "provider": "workbuddy", "kind": "subscription", "plan": "Pro", "user": "u1", "readAt": now_dt.isoformat(),
        "windows": [{"name": "Limited-time Free Promo", "used": 10, "remaining": 90, "resetsAt": promo_iso, "models": ["glm-5.3"]}],
    }
    allowances = ra.read_allowances({"status": "available", "accounts": parse_quotas({"object": "list", "data": [promo_acct]}, now_dt)}, now=ts)
    assert "workbuddy" in allowances.get("promotions", {})
    no_rem = ra.read_allowances({
        "status": "available",
        "accounts": [{
            "provider": "workbuddy", "state": "FRESH",
            "windows": [{"name": "Limited-time Free Promo", "unlimited": False, "resets_at": promo_iso}],
        }],
    }, now=ts)
    assert "promotions" not in no_rem
    c_class, res = ra.effective_cost(
        {"binding_id": "wb", "model_id": "workbuddy/glm-5.3", "connection_id": "magpie"},
        {"connection_id": "magpie", "auth_method": "none", "base_url": "http://127.0.0.1:3425/v1"},
        {},
        allowances,
        now=ts,
    )
    assert c_class == "free" and "promotional_free" in res
    assert ra.urgency(res, now=ts) > 0.0

    # End-to-end real magpie_usage_ingest rows (vendor provider="openai", nested tokens={...}) feed real _recent_pool_rates & _prepare_task_quota.
    from reverse_agent.platform_v1.magpie_usage_ingest import merge_into_cache, parse_usage_csv
    cache_path = tmp_path / "magpie_usage_cache.jsonl"
    now_iso_recent = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    csv_rows = parse_usage_csv("\n".join([
        "time,agent,provider,served_model,status,rejected,input_tokens,output_tokens,request_id,credits,cost_usd",
        f"{now_iso_recent},opencode,openai,workbuddy/glm-5.3,200,false,2500,500,r1,5.0,0.0",
        f"{now_iso_recent},opencode,openai,workbuddy-ai/glm-5.3,200,false,2000,500,r2,5.0,0.0",
    ]))
    assert len(csv_rows) == 2
    merge_into_cache(csv_rows, path=cache_path)

    raw_conn = sqlite3.connect(":memory:")
    raw_conn.row_factory = sqlite3.Row
    raw_conn.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT, binding_ref TEXT)")
    host = CombinedTrustedHost.__new__(CombinedTrustedHost)
    host._store = SimpleNamespace(
        _state_path=state,
        list_bindings_public=lambda: [{"binding_id": "wb-ai", "connection_id": "magpie", "model_id": "workbuddy-ai/glm-5.3"}],
        list_connections_public=lambda: [{"connection_id": "magpie", "auth_method": "none", "account_ref": "magpie"}],
        get_connection_public=lambda _c: {"connection_id": "magpie", "auth_method": "none", "account_ref": "magpie"},
    )
    host._task_store = SimpleNamespace(_conn=raw_conn)
    import os
    old_cache = os.environ.get("REVERSE_AGENT_MAGPIE_CACHE")
    os.environ["REVERSE_AGENT_MAGPIE_CACHE"] = str(cache_path)
    try:
        rpm_map, tpm_map = host._recent_pool_rates(limits)
        assert rpm_map == {"wb-shared": 2} and tpm_map == {"wb-shared": 5500}
        with pytest.raises(TaskStoreError, match="QUOTA_WAIT:pool_rpm_limit:wb-shared:2/2"):
            host._prepare_task_quota(SimpleNamespace(id="t-rpm", binding_ref="wb-ai", executor_kind="opencode", status="QUEUED"))
    finally:
        if old_cache is None:
            os.environ.pop("REVERSE_AGENT_MAGPIE_CACHE", None)
        else:
            os.environ["REVERSE_AGENT_MAGPIE_CACHE"] = old_cache
    raw_conn.close()
