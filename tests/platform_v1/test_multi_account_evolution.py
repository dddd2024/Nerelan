"""Self-evolution loop: persistence + feedback into mode selection (E1/E2).

Reuses orchestration_selector's decision core; this suite only proves the
persistence and feedback wiring, not the break-even math (covered by
test_orchestration_selector.py).
"""
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

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


def test_disabled_learning_ignores_persisted_policy_without_erasing_evidence(tmp_path):
    path = tmp_path / "feedback.json"
    enabled = SelfEvolutionStore(MultiAccountConfig(), path=path)
    for row in _rich_runs():
        enabled.record_run(row)
    original = path.read_bytes()
    cfg = MultiAccountConfig(enable_self_evolution=False)
    disabled = SelfEvolutionLoop(SelfEvolutionStore(cfg, path=path), cfg)
    assert disabled.recommend_mode({"task_count": 2})["reason"] == "default_multi_task_no_evidence"
    assert disabled.recommend_mode({"task_count": 2}, pin="single")["reason"] == "owner_pin"
    assert path.read_bytes() == original
    assert len(disabled._store.get_runs()) == 6


def test_raised_sample_threshold_rechecks_cached_policy_per_mode_and_band(tmp_path):
    path = tmp_path / "feedback.json"
    store = SelfEvolutionStore(MultiAccountConfig(), path=path)
    for row in _rich_runs():
        store.record_run(row)
    assert store.get_break_even()["sufficient_evidence"] is True
    cfg = MultiAccountConfig(min_observations_per_mode=4)
    stricter = SelfEvolutionStore(cfg, path=path)
    assert stricter.get_break_even()["cross_over_task_count"] is None
    stricter.record_run({**_rich_runs()[0], "size_band": "x"})
    assert stricter.get_break_even()["sufficient_evidence"] is False
    stricter.record_run({**_rich_runs()[3], "size_band": "x"})
    assert stricter.get_break_even()["sufficient_evidence"] is True
    stricter.record_run(_run("single", band="new-band"))
    assert stricter.get_break_even()["sufficient_evidence"] is False


@pytest.mark.parametrize("accepted", ["false", "true", 0, 1, None, [], {}])
def test_invalid_acceptance_cannot_train_or_change_disk(tmp_path, accepted):
    path = tmp_path / "feedback.json"
    store = SelfEvolutionStore(MultiAccountConfig(), path=path)
    with pytest.raises(ValueError, match="accepted"):
        store.record_run(_run("single", accepted=accepted))
    assert not path.exists()
    assert store.get_runs() == []


def test_replayed_outcome_is_idempotent_and_conflict_preserves_original(tmp_path):
    path = tmp_path / "feedback.json"
    first = SelfEvolutionStore(MultiAccountConfig(), path=path)
    second = SelfEvolutionStore(MultiAccountConfig(), path=path)
    event = {**_run("single"), "outcome_id": "goal:1:attempt:1"}
    first.record_run(event, now=1)
    saved = path.read_bytes()
    second.record_run(event, now=2)
    assert path.read_bytes() == saved
    assert len(first.get_runs()) == 1
    with pytest.raises(ValueError, match="conflicting"):
        second.record_run({**event, "accepted": False}, now=3)
    assert path.read_bytes() == saved
    # Separate attempts with equal measurements are still separate evidence.
    second.record_run({**event, "outcome_id": "goal:1:attempt:2"}, now=4)
    assert len(first.get_runs()) == 2


def test_interleaved_host_instances_keep_runs_and_unrelated_sections(tmp_path):
    path = tmp_path / "feedback.json"
    cfg = MultiAccountConfig()
    stores = [SelfEvolutionStore(cfg, path=path) for _ in range(4)]
    stores[0].patch("cooldowns", {"account-a": {"until": 999}})
    def write(index):
        stores[index % 4].record_run({**_run("single"), "outcome_id": str(index)})
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, range(40)))
    stores[1].patch("accounts", {"account-b": {"attempts": 1}})
    fresh = SelfEvolutionStore(cfg, path=path)
    assert len(fresh.get_runs()) == 40
    assert fresh.section("cooldowns") == {"account-a": {"until": 999}}
    assert fresh.section("accounts") == {"account-b": {"attempts": 1}}
    rows = fresh.get_runs()
    rows[0]["tokens"]["executor"] = 999
    assert fresh.get_runs()[0]["tokens"]["executor"] == 2


@pytest.mark.parametrize("value", [True, -1, float("nan"), float("inf"), "0", 10 ** 400])
def test_unknown_or_invalid_measurements_stay_unknown_and_json_finite(tmp_path, value):
    path = tmp_path / "feedback.json"
    store = SelfEvolutionStore(MultiAccountConfig(), path=path)
    store.record_run({**_run("single"), "cost_units": value, "wall_seconds": value,
                      "tokens": {"executor": value}})
    row = store.get_runs()[0]
    assert row["cost_units"] is None
    assert row["wall_seconds"] is None
    assert row["tokens"]["executor"] is None
    json.loads(path.read_text(), parse_constant=lambda value: pytest.fail(value))


def test_zero_cost_is_a_measurement_and_anonymous_runs_are_not_deduplicated():
    store = SelfEvolutionStore(MultiAccountConfig())
    for _ in range(2):
        store.record_run(_run("single", cost=0))
    assert [row["cost_units"] for row in store.get_runs()] == [0, 0]


@pytest.mark.parametrize("content", ['{"runs":', '[]', '{"runs": {}}', '{"runs": [null]}',
                                     '{"cooldowns": null}'])
def test_corrupted_ledger_is_preserved_instead_of_replaced(tmp_path, content):
    path = tmp_path / "feedback.json"
    store = SelfEvolutionStore(MultiAccountConfig(), path=path)
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="unavailable"):
        store.record_run(_run("single"))
    assert path.read_text(encoding="utf-8") == content
