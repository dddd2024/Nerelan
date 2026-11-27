"""Provider-free tests for #1664 Magpie routing group sync planner."""
from __future__ import annotations

from reverse_agent.platform_v1.group_sync import plan_group_sync


def test_group_sync_excludes_paid_subscriptions_and_unhealthy_accounts_and_orders_by_cache_hit() -> None:
    models_payload = {
        "object": "list",
        "data": [
            {"id": "group/existing"},
            {"id": "auto/hy4flash-free"},
            {"id": "claude/claude-sonnet-4-6"},
            {"id": "codex/gpt-5.3"},
            {"id": "zcode/glm-5.3"},
            {"id": "workbuddy-ai/glm-5.3"},
            {"id": "workbuddy/glm-5.3"},
            {"id": "raccoon/glm-5.3"},
            {"id": "trae-cn/glm-5.3"},
            {"id": "opencode-zen-free/glm-5.3"},
            {"id": "minimax-code/minimax-m2"},
        ],
    }
    quotas_snapshot = {
        "accounts": [
            {"provider": "zcode", "state": "UNKNOWN", "error": "expired", "windows": []},
            {"provider": "workbuddy-ai", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 0}]},
            {"provider": "workbuddy", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 50}]},
            {"provider": "raccoon", "state": "FRESH", "windows": [{"name": "Daily pool", "remaining_percent": 80}]},
            {"provider": "trae-cn", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 10}]},
            {"provider": "minimax-code", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 90}]},
        ]
    }
    usage_rows = [
        # raccoon: 90% cache hit, 100% ok
        {"served_model": "raccoon/glm-5.3", "status": 200, "rejected": False, "tokens": {"input": 100, "cache_read": 900, "cache_write": 0}, "reported_credits": 10.0},
        # workbuddy: 50% cache hit, 100% ok
        {"served_model": "workbuddy/glm-5.3", "status": 200, "rejected": False, "tokens": {"input": 500, "cache_read": 500, "cache_write": 0}, "reported_credits": 20.0},
        # trae-cn: 0% cache hit, 50% ok
        {"served_model": "trae-cn/glm-5.3", "status": 200, "rejected": False, "tokens": {"input": 500, "cache_read": 0, "cache_write": 0}},
        {"served_model": "trae-cn/glm-5.3", "status": 429, "rejected": True, "tokens": {"input": 500, "cache_read": 0, "cache_write": 0}},
        # opencode-zen-free has no usage rows yet -> falls after observed healthy members
    ]

    result = plan_group_sync(models_payload, quotas_snapshot, usage_rows)
    groups = result["groups"]
    assert "group/nerelan-glm-5-3" in groups
    # Ranked: highest cache hit first (raccoon -> workbuddy -> trae-cn -> unobserved opencode-zen-free)
    assert groups["group/nerelan-glm-5-3"]["members"] == [
        "raccoon/glm-5.3",
        "workbuddy/glm-5.3",
        "trae-cn/glm-5.3",
        "opencode-zen-free/glm-5.3",
    ]
    # Single-provider models are omitted when min_providers=2
    assert "group/nerelan-minimax-m2" not in groups
    # Paid subscriptions (#1743) are strictly excluded
    assert result["diff"]["excluded_paid_subscription"] == [
        "claude/claude-sonnet-4-6",
        "codex/gpt-5.3",
    ]
    # Expired (zcode) and exhausted (workbuddy-ai) accounts are excluded
    removed = {entry["member"]: entry["reason"] for entry in result["diff"]["removed_unhealthy"]}
    assert "zcode/glm-5.3" in removed
    assert removed["workbuddy-ai/glm-5.3"] == "quota_exhausted"
