"""Self-evolution loop: persistence + feedback into mode selection (E1/E2).

Reuses orchestration_selector's decision core; this suite only proves the
persistence and feedback wiring, not the break-even math (covered by
test_orchestration_selector.py).
"""
import json

from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.evolution import (
    SelfEvolutionLoop, SelfEvolutionStore,
)


def _run(mode, *, accepted=True, cost=10.0, count=4, band="trivial"):
    return {"mode": mode, "accepted": accepted, "cost_units": cost,
            "task_count": count, "tokens": {"planner": 1, "executor": 2, "reviewer": 3},
            "wall_seconds": 60.0, "size_band": band}


def _rich_runs():
    single = [{"mode": "single", "accepted": True, "cost_units": c, "task_count": n,
               "tokens": {"planner": 1, "executor": 2, "reviewer": 3},
               "wall_seconds": 10.0, "size_band": "x"}
              for c, n in [(20.0, 2), (40.0, 4), (80.0, 8)]]
    team = [{"mode": "agent_team", "accepted": True, "cost_units": c, "task_count": n,
             "tokens": {"planner": 1, "executor": 2, "reviewer": 3},
             "wall_seconds": 20.0, "size_band": "x"}
            for c, n in [(30.0, 2), (40.0, 4), (60.0, 8)]]
    return single + team


def test_recommend_default_without_data():
    loop = SelfEvolutionLoop(SelfEvolutionStore(MultiAccountConfig(), path=None), MultiAccountConfig())
    decision = loop.recommend_mode({"task_count": 3})
    assert decision["reason"] in ("default_single_task", "default_multi_task_no_evidence")


def test_break_even_persists_and_recommends():
    store = SelfEvolutionStore(MultiAccountConfig(), path=None)
    loop = SelfEvolutionLoop(store, MultiAccountConfig())
    for r in _rich_runs():
        loop.record_outcome(r)
    be = store.get_break_even()
    assert be and be.get("sufficient_evidence") is True
    assert be.get("cross_over_task_count") is not None
    # The measured break-even now drives the recommendation.
    small = loop.recommend_mode({"task_count": 2})
    large = loop.recommend_mode({"task_count": 7})
    assert small["mode"] == "single" and large["mode"] == "agent_team"
    assert small["reason"] == "measured_break_even"


def test_owner_pin_wins_after_learning():
    store = SelfEvolutionStore(MultiAccountConfig(), path=None)
    loop = SelfEvolutionLoop(store, MultiAccountConfig())
    for r in _rich_runs():
        loop.record_outcome(r)
    decision = loop.recommend_mode({"task_count": 7}, pin="single")
    assert decision["mode"] == "single" and decision["reason"] == "owner_pin"


def test_reset_clears_ledger():
    store = SelfEvolutionStore(MultiAccountConfig(), path=None)
    loop = SelfEvolutionLoop(store, MultiAccountConfig())
    loop.record_outcome(_run("single"))
    assert store.get_runs()
    store.reset()
    assert store.get_runs() == []
    assert store.get_break_even() is None


def test_file_persistence_round_trip(tmp_path):
    path = tmp_path / "be.json"
    store1 = SelfEvolutionStore(MultiAccountConfig(), path=path)
    loop1 = SelfEvolutionLoop(store1, MultiAccountConfig())
    loop1.record_outcome(_run("single"))
    assert path.exists()
    # A fresh store at the same path reloads the written ledger.
    store2 = SelfEvolutionStore(MultiAccountConfig(), path=path)
    assert len(store2.get_runs()) == 1
    # The file is valid JSON and atomic-write safe.
    json.loads(path.read_text(encoding="utf-8"))


def test_calibration_feedback_disabled_returns_none():
    cfg = MultiAccountConfig(calibration_feedback_enabled=False)
    loop = SelfEvolutionLoop(SelfEvolutionStore(cfg, path=None), cfg)
    assert loop.calibration_feedback({}, {}, []) is None


def test_calibration_feedback_enabled_does_not_raise():
    cfg = MultiAccountConfig(calibration_feedback_enabled=True)
    loop = SelfEvolutionLoop(SelfEvolutionStore(cfg, path=None), cfg)
    # delta_calibration may succeed or be guarded; either way it must not raise.
    result = loop.calibration_feedback({"a": 1}, {"a": 2}, [{"x": 1}])
    assert result is None or isinstance(result, dict)
