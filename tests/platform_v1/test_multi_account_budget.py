"""Rolling-window cost ceiling: admission, reservation and settlement.

The ceiling is the one absolute constraint the scheduler lacked: relative cost
ranking cannot stop a pool of cheap accounts from spending without bound.
"""
import json

from reverse_agent.platform_v1.multi_account.budget import CostBudgetGovernor
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.scheduler import select_account
from reverse_agent.platform_v1.multi_account.status import AccountHealth, AccountStatus

NOW = 1_700_000_000.0


def cfg(**overrides):
    base = dict(cost_budget_enabled=True, cost_budget_units=10.0,
                cost_budget_window_seconds=100.0, cost_budget_soft_ratio=0.8,
                cost_budget_default_task_units=1.0)
    base.update(overrides)
    return MultiAccountConfig(**base)


def governor(config=None, *, state=None):
    clock = lambda: NOW  # noqa: E731 - fixed clock keeps the arithmetic exact
    return CostBudgetGovernor(config or cfg(), clock=clock, state=state)


def spend(gov, units, *, at=NOW):
    token = gov.reserve(units, now=at)
    return gov.settle(token, actual_units=units, now=at)


# --- admission ---------------------------------------------------------------

def test_disabled_budget_always_allows_and_reports_not_enforced():
    gov = CostBudgetGovernor(MultiAccountConfig(), clock=lambda: NOW)
    decision = gov.admit(100.0, now=NOW)
    assert decision["decision"] == "allow"
    assert decision["enforced"] is False
    assert decision["reason"] == "budget_disabled"


def test_allows_below_soft_threshold():
    gov = governor()
    spend(gov, 2.0)
    decision = gov.admit(1.0, now=NOW)
    assert decision["decision"] == "allow"
    assert decision["reason"] == "within_budget"


def test_degrades_at_soft_threshold_but_still_dispatches():
    gov = governor()
    spend(gov, 7.5)                      # 75% of 10; forecast pushes past 80%
    decision = gov.admit(1.0, now=NOW)
    assert decision["decision"] == "degrade"
    assert decision["reason"] == "cost_budget_soft_cap"


def test_denies_at_ceiling_and_reports_when_spend_rolls_off():
    gov = governor()
    for _ in range(10):
        spend(gov, 1.0)
    decision = gov.admit(1.0, now=NOW)
    assert decision["decision"] == "deny"
    assert decision["reason"] == "cost_budget_exhausted"
    # The oldest spend expires one window after it was recorded.
    assert decision["retry_at"] == NOW + 100.0


def test_forecast_larger_than_the_whole_ceiling_is_never_admitted():
    gov = governor()
    decision = gov.admit(25.0, now=NOW)
    assert decision["decision"] == "deny"
    assert decision["reason"] == "forecast_exceeds_cap"
    assert decision["retry_at"] is None


def test_reservation_blocks_concurrent_overshoot():
    gov = governor()
    spend(gov, 9.5)
    gov.reserve(1.0, now=NOW)
    decision = gov.admit(0.0, now=NOW)
    assert decision["decision"] == "deny"
    # Only in-flight work blocks, so there is no future moment to wait for.
    assert decision["reason"] == "cost_budget_reserved"
    assert decision["retry_at"] is None


def test_reservations_can_be_excluded_from_the_ceiling():
    gov = governor(cfg(cost_budget_include_reservations=False))
    spend(gov, 9.5)
    gov.reserve(1.0, now=NOW)
    assert gov.admit(0.0, now=NOW)["decision"] in ("degrade", "allow")


def test_admit_with_reserve_returns_a_token_that_settles():
    gov = governor()
    decision = gov.admit(2.0, now=NOW, account_ref="a", reserve=True)
    assert decision["decision"] == "allow"
    result = gov.settle(decision["reservation"], actual_units=1.5, now=NOW)
    assert result["charged_units"] == 1.5
    assert gov.spent_units(now=NOW) == 1.5


# --- settlement semantics ----------------------------------------------------

def test_unpriced_attempt_is_charged_its_reservation_not_zero():
    gov = governor()
    token = gov.reserve(2.0, now=NOW)
    result = gov.settle(token, actual_units=None, now=NOW)
    assert result["charged_units"] == 2.0
    assert result["priced"] is True
    assert gov.status(now=NOW)["unpriced_attempts"] == 0


def test_unknown_attempt_without_reservation_is_counted_as_unpriced():
    gov = governor()
    result = gov.settle(None, actual_units=None, now=NOW)
    assert result["charged_units"] == 0.0
    assert result["priced"] is False
    assert gov.status(now=NOW)["unpriced_attempts"] == 1


def test_release_drops_a_reservation_without_spending():
    gov = governor()
    token = gov.reserve(3.0, now=NOW)
    gov.release(token)
    assert gov.reserved_units(now=NOW) == 0.0
    assert gov.spent_units(now=NOW) == 0.0


def test_window_rolls_spend_out():
    gov = governor()
    spend(gov, 10.0)
    assert gov.spent_units(now=NOW) == 10.0
    assert gov.spent_units(now=NOW + 101.0) == 0.0
    assert gov.admit(1.0, now=NOW + 101.0)["decision"] == "allow"


# --- persistence -------------------------------------------------------------

def test_spend_survives_a_restart(tmp_path):
    path = tmp_path / "budget.json"
    first = CostBudgetGovernor(
        cfg(), clock=lambda: NOW,
        persist=lambda snap: path.write_text(json.dumps(snap), encoding="utf-8"))
    spend(first, 4.0)
    restored = CostBudgetGovernor(cfg(), clock=lambda: NOW,
                                  state=json.loads(path.read_text(encoding="utf-8")))
    assert restored.spent_units(now=NOW) == 4.0


def test_reset_forgets_the_window():
    gov = governor()
    spend(gov, 9.0)
    gov.reset()
    assert gov.spent_units(now=NOW) == 0.0


# --- scheduler integration ---------------------------------------------------

def mk(ref, health=AccountHealth.HEALTHY, headroom=50.0):
    return AccountStatus(account_ref=ref, provider="codex", health=health,
                         headroom_pct=headroom)


def test_scheduler_holds_when_the_budget_denies():
    gov = governor()
    for _ in range(10):
        spend(gov, 1.0)
    decision = select_account([mk("a")], config=gov._config, now=NOW, budget=gov)
    assert decision["decision"] == "hold"
    assert decision["reason"] == "cost_budget_exhausted"
    assert decision["retry_at"] == NOW + 100.0
    assert decision["account_ref"] is None


def test_scheduler_prefers_the_cheapest_account_under_soft_cap():
    from reverse_agent.platform_v1.multi_account.scoring import AccountScoreboard

    config = cfg()
    gov = governor(config)
    scores = AccountScoreboard(config, clock=lambda: NOW)
    scores.observe("cheap", ok=True, cost_units=1.0, now=NOW)
    scores.observe("dear", ok=True, cost_units=8.0, now=NOW)
    spend(gov, 7.5)
    decision = select_account([mk("cheap", headroom=40.0), mk("dear", headroom=90.0)],
                              config=config, now=NOW, scores=scores, budget=gov)
    assert decision["decision"] == "use"
    assert decision["account_ref"] == "cheap"
    assert decision["reason"] == "cheapest_within_budget"


def test_scheduler_without_budget_is_unchanged():
    decision = select_account([mk("a", headroom=10.0), mk("b", headroom=90.0)],
                              config=cfg(), now=NOW)
    assert decision["account_ref"] == "b"
    assert decision["evidence"]["budget"] is None


# --- unusable measurements must degrade, never crash --------------------------

def test_an_unrepresentable_cost_is_treated_as_unknown_not_as_a_crash():
    """Telemetry can hand us a 10**400 int; the ceiling must still answer.

    ``float()`` on it raises ``OverflowError``. Failing here would take down the
    dispatch path on a bad number, which is strictly worse than charging the
    reservation and counting the attempt as unpriced.
    """
    gov = governor(cfg(cost_budget_units=5.0))
    admission = gov.admit(2.0, now=NOW, account_ref="a", reserve=True)
    result = gov.settle(admission["reservation"], actual_units=10 ** 400, now=NOW)

    assert result["charged_units"] == 2.0, "the reservation is charged, not zero"
    assert result["priced"] is False, "an unusable measurement is not evidence of cost"
    assert gov.status(now=NOW)["unpriced_attempts"] == 1


def test_a_nan_cost_cannot_poison_the_window():
    gov = governor(cfg(cost_budget_units=5.0))
    result = gov.settle(None, actual_units=float("nan"), now=NOW)
    assert result["charged_units"] == 0.0
    assert gov.spent_units(now=NOW) == 0.0
    assert gov.admit(1.0, now=NOW)["decision"] == "allow", "comparisons stay ordered"


def test_an_unusable_forecast_falls_back_to_the_measured_basis():
    """An unknown forecast must not park work, and must not pretend to be zero.

    It falls back to the configured default / measured mean, so the decision is
    still grounded in what attempts actually cost.
    """
    gov = governor(cfg(cost_budget_units=5.0, cost_budget_default_task_units=4.0))
    decision = gov.admit(10 ** 400, now=NOW)
    # 4.0 against a 5.0 ceiling crosses the 0.8 soft threshold: degraded, not
    # admitted freely, and never silently treated as a zero-cost attempt.
    assert decision["forecast_units"] == 4.0
    assert decision["decision"] == "degrade"
    assert decision["reason"] == "cost_budget_soft_cap"


def test_an_out_of_window_view_says_so_instead_of_looking_empty():
    """"Spend is 0" and "nothing was ever recorded" must not look the same.

    An operator inspecting a ledger with a later clock (or a different window)
    gets ``spent_units == 0``; the record counters are what tell them the spend
    exists but has aged out of the window.
    """
    gov = governor(cfg(cost_budget_units=5.0, cost_budget_window_seconds=600.0))
    gov.settle(None, actual_units=2.0, now=NOW)
    fresh = gov.status(now=NOW + 1.0)
    assert (fresh["spent_units"], fresh["records_in_window"], fresh["records_total"]) == (2.0, 1, 1)

    aged = gov.status(now=NOW + 601.0)
    assert aged["spent_units"] == 0.0
    assert aged["records_in_window"] == 0
    assert aged["records_total"] >= 1, "the record is still held, only out of window"
