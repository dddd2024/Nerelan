"""Provider-free weekly quota pacing tests."""
from datetime import datetime, timedelta, timezone
import pytest
from reverse_agent.model_access.quota_pacing import plan_pace

START = datetime(2026, 10, 12, 9, tzinfo=timezone.utc)
RESET = START + timedelta(days=7)


def p(day=3, used=30, **updates):
    now = START + timedelta(days=day)
    opts = dict(used_percent=used, window_started_at=START, next_reset_at=RESET,
                observed_at=now, now=now, eligible_work=3, short_window_available=True)
    opts.update(updates)
    return plan_pace(**opts)


def test_target_95_percent_by_four_and_half_days():
    r = p(0, 0)
    assert r["state"] == "ON_PACE"
    assert r["needed_percent_per_day"] == pytest.approx(95/4.5, abs=0.001)
    assert r["target_at"] == (START + timedelta(days=4.5)).isoformat()


def test_lagging_weekly_quota_can_prioritize_useful_work():
    r = p(3, 30)
    assert r["state"] == "BEHIND"
    assert r["advice"] == "PRIORITIZE_USEFUL_TASKS"
    assert r["target_used_by_now_percent"] == pytest.approx(63.333, abs=.001)


def test_ahead_quota_can_choose_other_models():
    assert p(3, 85)["advice"] == "PREFER_OTHER_ELIGIBLE_RESOURCES"


def test_no_work_never_generates_purpose_less_spend():
    assert p(3, 20, eligible_work=0)["advice"] == "NO_MEANINGFUL_WORK"


def test_short_window_exhaustion_blocks_even_when_weekly_behind():
    assert p(3, 20, short_window_available=False)["advice"] == "WAIT_SHORT_WINDOW"


def test_unknown_short_window_requires_check():
    assert p(3, 20, short_window_available=None)["advice"] == "VERIFY_SHORT_WINDOW"


def test_weekly_target_reached_preserves_reserve():
    assert p(4, 96)["advice"] == "PRESERVE_RESERVE"


def test_four_day_preference():
    assert p(2, 35, target_days=4)["target_used_by_now_percent"] == 47.5


def test_after_target_date_no_infinite_burn_rate():
    assert p(5, 65)["needed_percent_per_day"] is None


def test_next_real_reset_requires_new_observation():
    assert p(8, 99)["reason"] == "reset_not_yet_observed"


def test_external_consumption_is_in_observed_usage_not_claimed_as_our_cost():
    r = p(3, 99)
    assert r["state"] == "TARGET_REACHED"
    assert r["non_authoritative"] is True
    assert "cash" not in r and "tokens" not in r


def test_shorter_real_window_changes_target():
    r = p(2, 60, next_reset_at=START+timedelta(days=3))
    assert r["target_at"] == (START+timedelta(days=3)).isoformat()


@pytest.mark.parametrize("updates", [
    {"used_percent": None}, {"used_percent": 120},
    {"used_percent": float("nan")}, {"used_percent": True},
    {"window_started_at": None}, {"next_reset_at": None},
    {"observed_at": None}, {"observed_at": START},
    {"window_started_at": RESET},
    {"observed_at": START+timedelta(days=4)},
    {"target_days": 0}, {"target_used_percent": 101},
    {"short_window_available": "yes"}, {"eligible_work": -1},
    {"now": START.replace(tzinfo=None)},
])
def test_invalid_unknown_evidence_fails_closed(updates):
    assert p(3, 30, **updates)["state"] == "UNKNOWN"