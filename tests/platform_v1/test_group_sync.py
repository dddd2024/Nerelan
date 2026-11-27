"""Provider-free tests for #1664 / #1533 Magpie routing group sync planner."""
from __future__ import annotations

from pathlib import Path

from reverse_agent.platform_v1.group_sync import _telemetry_by_member, plan_group_sync


def test_group_sync_excludes_paid_subscriptions_and_unhealthy_accounts_and_ranks_composited() -> None:
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
    # Composite rank: unmetered free + lower credit burn + high reliability/cache ahead of flaky/unknown cost
    assert groups["group/nerelan-glm-5-3"]["members"] == [
        "opencode-zen-free/glm-5.3",
        "raccoon/glm-5.3",
        "workbuddy/glm-5.3",
        "trae-cn/glm-5.3",
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


def test_group_sync_rejects_account_when_any_mandatory_window_is_exhausted() -> None:
    models_payload = {
        "object": "list",
        "data": [
            {"id": "raccoon/glm-5.3"},
            {"id": "workbuddy/glm-5.3"},
            {"id": "trae-cn/glm-5.3"},
        ],
    }
    quotas_snapshot = {
        "accounts": [
            {
                "provider": "raccoon",
                "state": "FRESH",
                "windows": [
                    {"name": "Weekly", "remaining_percent": 0.0},
                    {"name": "Daily pool", "remaining_percent": 80.0},
                ],
            },
            {"provider": "workbuddy", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 50.0}]},
            {"provider": "trae-cn", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 40.0}]},
        ]
    }
    result = plan_group_sync(models_payload, quotas_snapshot)
    assert result["groups"]["group/nerelan-glm-5-3"]["members"] == [
        "workbuddy/glm-5.3",
        "trae-cn/glm-5.3",
    ]
    removed = {entry["member"]: entry["reason"] for entry in result["diff"]["removed_unhealthy"]}
    assert removed["raccoon/glm-5.3"] == "quota_exhausted"


def test_group_sync_preserves_default_paid_exclusions_under_partial_override() -> None:
    models_payload = {
        "data": [
            {"id": "claude/claude-opus-4"},
            {"id": "codex/gpt-5.3"},
            {"id": "custom-paid/glm-5.3"},
            {"id": "workbuddy/glm-5.3"},
            {"id": "trae-cn/glm-5.3"},
        ],
    }
    res_no_providers = plan_group_sync(models_payload, paid_subscriptions={"other": True})
    assert res_no_providers["diff"]["excluded_paid_subscription"] == [
        "claude/claude-opus-4",
        "codex/gpt-5.3",
    ]
    res_custom = plan_group_sync(
        models_payload,
        paid_subscriptions={"providers": {"custom-paid": {"enabled": True}}},
    )
    assert res_custom["diff"]["excluded_paid_subscription"] == [
        "claude/claude-opus-4",
        "codex/gpt-5.3",
        "custom-paid/glm-5.3",
    ]


def test_run_group_sync_wires_magpie_fetch_and_usage_cache(tmp_path: Path, monkeypatch) -> None:
    from datetime import datetime, timezone
    import json
    from reverse_agent.model_access import http_safe
    from reverse_agent.platform_v1.group_sync import run_group_sync

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    cache_file = tmp_path / "magpie_usage_cache.jsonl"
    cache_file.write_text(
        json.dumps({
            "served": "workbuddy/glm-5.3",
            "status": 200,
            "rejected": False,
            "input": 100,
            "cache_read": 900,
            "cache_write": 0,
        }) + "\n",
        encoding="utf-8",
    )

    class _Resp:
        def __init__(self, payload: dict) -> None:
            self._data = json.dumps(payload).encode("utf-8")

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def _fake_urlopen(req, timeout=3.0):  # noqa: ARG001
        url = req.full_url
        if url.endswith("/v1/models"):
            return _Resp({"data": [{"id": "workbuddy/glm-5.3"}, {"id": "trae-cn/glm-5.3"}, {"id": "codex/gpt-5.3"}]})
        if "/v1/magpie/quotas" in url:
            return _Resp({
                "object": "list",
                "data": [
                    {"provider": "workbuddy", "kind": "subscription", "readAt": now_iso, "windows": [{"name": "Credits", "used": 50, "remaining": 50}]},
                    {"provider": "trae-cn", "kind": "subscription", "readAt": now_iso, "windows": [{"name": "Credits", "used": 60, "remaining": 40}]},
                ],
            })
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(http_safe, "urlopen", _fake_urlopen)
    plan = run_group_sync(magpie_url="http://127.0.0.1:3425", cache_path=cache_file)
    assert plan["groups"]["group/nerelan-glm-5-3"]["members"] == ["workbuddy/glm-5.3", "trae-cn/glm-5.3"]
    assert plan["diff"]["excluded_paid_subscription"] == ["codex/gpt-5.3"]


def test_group_sync_rejects_missing_stale_or_empty_quota_and_unknown_credit_not_zero() -> None:
    models = {
        "data": [
            {"id": "workbuddy/glm-5.3"},
            {"id": "trae-cn/glm-5.3"},
            {"id": "raccoon/glm-5.3"},
            {"id": "opencode-zen-free/glm-5.3"},
            {"id": "minimax-code/glm-5.3"},
        ]
    }
    quotas = {
        "accounts": [
            {"provider": "workbuddy", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 60.0}]},
            {"provider": "trae-cn", "state": "STALE", "windows": [{"name": "Credits", "remaining_percent": 90.0}]},
            {"provider": "raccoon", "state": "FRESH", "windows": []},
            # minimax-code omitted completely -> unknown_quota:no_quota_row
        ]
    }
    res = plan_group_sync(models, quotas)
    members = res["groups"]["group/nerelan-glm-5-3"]["members"]
    assert set(members) == {"opencode-zen-free/glm-5.3", "workbuddy/glm-5.3"}
    removed = {entry["member"]: entry["reason"] for entry in res["diff"]["removed_unhealthy"]}
    assert removed["trae-cn/glm-5.3"] == "unknown_quota:stale"
    assert removed["raccoon/glm-5.3"] == "unknown_quota:empty_windows"
    assert removed["minimax-code/glm-5.3"] == "unknown_quota:no_quota_row"

    # Missing telemetry / missing reported_credits must stay None, never 0.0.
    telemetry = _telemetry_by_member([
        {"served_model": "workbuddy/glm-5.3", "status": 200, "tokens": {"input": 100, "cache_read": 0}},
        {"served_model": "trae-cn/glm-5.3", "status": 200, "tokens": {}},
    ])
    assert telemetry["workbuddy/glm-5.3"]["credits_per_1m"] is None
    assert telemetry["trae-cn/glm-5.3"]["cache_hit_rate"] is None
    assert telemetry["trae-cn/glm-5.3"]["credits_per_1m"] is None


def test_group_sync_filters_meta_models_compliance_and_avoids_cache_only_ranking() -> None:
    models = {
        "data": [
            {"id": "copilot/gpt-5.3"},
            {"id": "custom-compliant/glm-5.3"},
            {"id": "workbuddy/auto"},
            {"id": "workbuddy/default"},
            {"id": "trae-cn/max-model"},
            {"id": "workbuddy/glm-5.3"},
            {"id": "raccoon/glm-5.3"},
        ]
    }
    quotas = {
        "accounts": [
            {"provider": "workbuddy", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 70.0}]},
            {"provider": "raccoon", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 70.0}]},
        ]
    }
    # raccoon has high cache hit (90%) BUT high failure rate (40%) + high credit burn; workbuddy is reliable & cheap.
    usage = [
        {"served_model": "raccoon/glm-5.3", "status": 200, "tokens": {"input": 100, "cache_read": 900}, "reported_credits": 50.0},
        {"served_model": "raccoon/glm-5.3", "status": 500, "rejected": True, "tokens": {"input": 100, "cache_read": 900}, "reported_credits": 50.0},
        {"served_model": "workbuddy/glm-5.3", "status": 200, "tokens": {"input": 400, "cache_read": 600, "output": 1000}, "reported_credits": 2.0},
        {"served_model": "workbuddy/glm-5.3", "status": 200, "tokens": {"input": 400, "cache_read": 600, "output": 1000}, "reported_credits": 2.0},
    ]
    res = plan_group_sync(models, quotas, usage, compliance_excluded=["copilot", "custom-compliant"])
    assert res["diff"]["excluded_compliance"] == ["copilot/gpt-5.3", "custom-compliant/glm-5.3"]
    assert res["diff"]["excluded_meta_models"] == ["trae-cn/max-model", "workbuddy/auto", "workbuddy/default"]
    assert res["groups"]["group/nerelan-glm-5-3"]["members"] == ["workbuddy/glm-5.3", "raccoon/glm-5.3"]
    # credits_per_1m matches observed_credit_multipliers output-inclusive token denominator: 4 credits / 4000 tokens = 1000/1M
    assert _telemetry_by_member(usage)["workbuddy/glm-5.3"]["credits_per_1m"] == 1000.0
    # Without explicit compliance_excluded, copilot is not silently excluded by undocumented hardcode.
    default_res = plan_group_sync(
        {"data": [{"id": "copilot/glm-5.3"}, {"id": "workbuddy/glm-5.3"}]},
        {"accounts": [{"provider": "copilot", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 50.0}]},
                      {"provider": "workbuddy", "state": "FRESH", "windows": [{"name": "Credits", "remaining_percent": 50.0}]}]},
    )
    assert default_res["diff"]["excluded_compliance"] == []
