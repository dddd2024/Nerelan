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
