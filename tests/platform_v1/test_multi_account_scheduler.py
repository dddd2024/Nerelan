"""Account-aware scheduling and bounded reroute / dead-letter.

Pure decision logic over AccountStatus; no I/O, no credentials.
"""
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.scheduler import (
    AccountAwareScheduler, next_after_failure, select_account,
)
from reverse_agent.platform_v1.multi_account.status import AccountHealth, AccountStatus


CFG = MultiAccountConfig()
NOW = 1_700_000_000.0


def mk(ref, health, *, headroom=None, flags=(), provider="codex", fresh=0.0):
    return AccountStatus(account_ref=ref, provider=provider, health=health,
                         headroom_pct=headroom, anomaly_flags=list(flags),
                         freshness_age=fresh)


def test_select_picks_highest_headroom_healthy():
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=30.0),
                mk("b", AccountHealth.HEALTHY, headroom=70.0)]
    decision = select_account(statuses, config=CFG, now=NOW)
    assert decision["decision"] == "use"
    assert decision["account_ref"] == "b"


def test_select_holds_when_all_exhausted():
    statuses = [mk("a", AccountHealth.EXHAUSTED), mk("b", AccountHealth.ABNORMAL)]
    decision = select_account(statuses, config=CFG, now=NOW)
    assert decision["decision"] == "hold"
    assert decision["reason"] == "all_accounts_exhausted"


def test_select_holds_when_nothing_observed():
    decision = select_account([], config=CFG, now=NOW)
    assert decision["decision"] == "hold"
    assert decision["reason"] == "no_accounts_observed"


def test_small_task_may_use_stale_account():
    statuses = [mk("a", AccountHealth.STALE, headroom=50.0, fresh=1200.0)]
    decision = select_account(statuses, config=CFG, now=NOW, small_task=True,
                             need={"p80_percent": 0.5})
    assert decision["decision"] == "use"
    assert decision["account_ref"] == "a"


def test_small_task_ceiling_blocks_oversized_need():
    statuses = [mk("a", AccountHealth.STALE, headroom=50.0, fresh=1200.0)]
    decision = select_account(statuses, config=CFG, now=NOW, small_task=True,
                             need={"p80_percent": 5.0})
    assert decision["decision"] == "hold"
    assert decision["reason"] == "small_task_ceiling_exceeded"


def test_reroute_moves_to_next_best():
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=80.0),
                mk("b", AccountHealth.HEALTHY, headroom=40.0)]
    result = next_after_failure(statuses, config=CFG, failed_ref="a",
                               failure_kind="quota_exhausted", attempt=1, now=NOW)
    assert result["decision"] == "reroute"
    assert result["next_account_ref"] == "b"


def test_dead_letter_after_max_reroutes():
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=80.0),
                mk("b", AccountHealth.HEALTHY, headroom=40.0)]
    result = next_after_failure(statuses, config=CFG, failed_ref="a",
                               failure_kind="quota_exhausted",
                               attempt=CFG.reroute_max_attempts, now=NOW)
    assert result["decision"] == "dead_letter"
    assert "max_reroutes_exceeded" in result["reason"]


def test_stateful_wrapper_excludes_failed_account():
    sched = AccountAwareScheduler(CFG)
    statuses = [mk("a", AccountHealth.HEALTHY, headroom=80.0),
                mk("b", AccountHealth.HEALTHY, headroom=40.0)]
    first = sched.select(statuses)
    assert first["account_ref"] == "a"
    after = sched.on_failure(statuses, failed_ref="a", failure_kind="task_failed",
                            attempt=1)
    assert after["decision"] == "reroute"
    # The failed account is now excluded; select must skip it.
    again = sched.select(statuses)
    assert again["account_ref"] == "b"
    sched.reset_for_task()
    assert sched.select(statuses)["account_ref"] == "a"
