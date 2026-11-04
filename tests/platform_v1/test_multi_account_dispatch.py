"""Integration seam: the guarded hand-off from dispatch to the orchestration brain.

These prove the seam degrades safely when the brain is unavailable and returns
the measured decision / reroute when it is present. No dispatch monolith is
touched here — the seam is the unit under test.
"""
import pytest

from reverse_agent.platform_v1.multi_account import dispatch
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.status import AccountHealth, AccountStatus


@pytest.fixture(autouse=True)
def _reset():
    dispatch.reset_orchestrator()
    yield
    dispatch.reset_orchestrator()


def _status(ref, health, headroom=None):
    return AccountStatus(account_ref=ref, provider="codex", health=health,
                         headroom_pct=headroom, anomaly_flags=[], freshness_age=0.0)


def test_fallback_recommendation_when_brain_raises():
    orig = dispatch.get_orchestrator
    dispatch.get_orchestrator = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
    try:
        decision = dispatch.recommend_orchestration_mode({"task_count": 3})
        assert decision["mode"] in ("single", "agent_team")
        assert "reason" in decision
    finally:
        dispatch.get_orchestrator = orig


def test_recommendation_uses_measured_break_even():
    # Seed the in-memory orchestrator with enough outcomes to learn a crossover.
    o = dispatch.get_orchestrator()
    for c, n in [(20.0, 2), (40.0, 4), (80.0, 8)]:
        o.record_outcome({"mode": "single", "accepted": True, "cost_units": c,
                          "task_count": n, "tokens": {"planner": 1, "executor": 2, "reviewer": 3},
                          "wall_seconds": 10.0, "size_band": "x"})
    for c, n in [(30.0, 2), (40.0, 4), (60.0, 8)]:
        o.record_outcome({"mode": "agent_team", "accepted": True, "cost_units": c,
                          "task_count": n, "tokens": {"planner": 1, "executor": 2, "reviewer": 3},
                          "wall_seconds": 20.0, "size_band": "x"})
    decision = dispatch.recommend_orchestration_mode({"task_count": 7})
    assert decision["mode"] == "agent_team" and decision["reason"] == "measured_break_even"


def test_record_outcome_is_best_effort_and_safe():
    assert dispatch.record_goal_outcome({"mode": "single", "accepted": True,
                                        "cost_units": 10.0, "task_count": 2}) is not None
    orig = dispatch.get_orchestrator
    dispatch.get_orchestrator = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
    try:
        assert dispatch.record_goal_outcome({"mode": "single"}) is None  # never raises
    finally:
        dispatch.get_orchestrator = orig


def test_select_dispatch_account_returns_best():
    statuses = [_status("a", AccountHealth.HEALTHY, headroom=80.0),
                _status("b", AccountHealth.HEALTHY, headroom=40.0)]
    decision = dispatch.select_dispatch_account(statuses)
    assert decision["decision"] == "use" and decision["account_ref"] == "a"


def test_select_degrades_to_hold_when_brain_down():
    orig = dispatch.get_orchestrator
    dispatch.get_orchestrator = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
    try:
        decision = dispatch.select_dispatch_account([])
        assert decision["decision"] == "hold"
        assert decision["reason"] == "orchestrator_unavailable"
    finally:
        dispatch.get_orchestrator = orig


def test_reroute_degrades_to_hold_when_brain_down():
    orig = dispatch.get_orchestrator
    dispatch.get_orchestrator = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
    try:
        decision = dispatch.reroute_failed_account([], failed_ref="a",
                                                  failure_kind="quota_exhausted", attempt=1)
        assert decision["decision"] == "hold"
    finally:
        dispatch.get_orchestrator = orig
