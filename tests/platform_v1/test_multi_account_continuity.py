"""Continuity across a restart, a replay and a rollback — the unattended case.

The per-module suites already pin each guard in isolation. What an unattended
run actually depends on is the *composition*: after a crash the cost window, the
alert dedupe state, the policy chain and the run clock must all come back, and a
terminal receipt that arrives twice must not spend, train or sample twice.

These tests drive only the public facade (:class:`MultiAccountOrchestrator`) and
the on-disk ledger, so they fail if any of those guarantees regresses in wiring
rather than inside a single module.
"""
from __future__ import annotations

import json

import pytest

from reverse_agent.platform_v1.multi_account import (
    AlertSeverity, MultiAccountConfig, MultiAccountOrchestrator,
)

T0 = 1_800_000_000.0


def _config(**overrides) -> MultiAccountConfig:
    """A run bound tight enough to observe, still a legal configuration."""
    base = dict(
        cost_budget_enabled=True,
        cost_budget_units=10.0,
        cost_budget_default_task_units=1.0,
        max_run_duration_seconds=3600.0,
        policy_min_samples=2,
        policy_step_ratio=0.25,
    )
    base.update(overrides)
    return MultiAccountConfig(**base)


def _orchestrator(path, clock, **config):
    return MultiAccountOrchestrator(_config(**config), clock=lambda: clock[0],
                                    store_path=path)


def test_every_loop_survives_one_restart(tmp_path):
    """Cost window, alert dedupe, policy version and run clock all come back."""
    state = tmp_path / "brain.json"
    clock = [T0]
    first = _orchestrator(state, clock)
    first.start_run(now=T0)
    admission = first.admit(2.5, now=T0, account_ref="acct-a")
    first.settle(admission["reservation"], cost_units=2.5, account_ref="acct-a", now=T0)
    first.raise_alert("host_callback_failed", severity="error", subject="feedback",
                      message="回调失败", now=T0)
    # A pool that is failing drives one bounded policy step.
    for attempt in range(2):
        first.record_account_outcome("acct-a", ok=False, failure_kind="task_failed",
                                     now=T0 + attempt)
    assert first.policy_view()["version"] >= 1

    before_budget = first.budget_status(now=T0)
    before_policy = first.policy_view()

    clock[0] = T0 + 120.0
    second = _orchestrator(state, clock)          # the restart
    after_budget = second.budget_status(now=clock[0])
    after_policy = second.policy_view()
    run = second.run_status(now=clock[0])

    assert after_budget["spent_units"] == before_budget["spent_units"] == 2.5
    assert after_policy["version"] == before_policy["version"]
    assert after_policy["effective"] == before_policy["effective"]
    assert run["started_at"] == T0, "a restart must not restart the run clock"
    assert run["elapsed_seconds"] == pytest.approx(120.0, abs=0.5)

    # Alert suppression state survived, so the same fact is not re-emitted.
    repeated = second.raise_alert("host_callback_failed", severity="error",
                                  subject="feedback", message="回调失败", now=clock[0])
    assert repeated == []


def test_a_replayed_receipt_spends_and_samples_once(tmp_path):
    """The same terminal receipt must not settle, train or sample twice."""
    clock = [T0]
    brain = _orchestrator(tmp_path / "brain.json", clock)
    admission = brain.admit(3.0, now=T0, account_ref="acct-b")
    receipt = dict(account_ref="acct-b", ok=False, cost_units=3.0, wall_seconds=42.0,
                   failure_kind="task_failed", outcome_id="task-7/attempt-2",
                   budget_token=admission["reservation"], task_id="task-7")

    brain.record_account_outcome(**receipt, now=T0)
    spent_once = brain.budget_status(now=T0)["spent_units"]
    samples_once = brain._attempts_since_policy

    # The coordinator retries the callback after a timeout: same terminal receipt.
    brain.record_account_outcome(**receipt, now=T0 + 1.0)

    assert brain.budget_status(now=T0 + 1.0)["spent_units"] == spent_once == 3.0
    assert brain._attempts_since_policy == samples_once
    assert brain.account_scores()["acct-b"]["attempts"] == 1


def test_a_conflicting_replay_is_refused_not_absorbed(tmp_path):
    """A re-used receipt id with different content is a bug, not a retry."""
    clock = [T0]
    brain = _orchestrator(tmp_path / "brain.json", clock)
    brain.record_account_outcome("acct-c", ok=True, outcome_id="task-9/attempt-1", now=T0)

    with pytest.raises(ValueError):
        brain.record_account_outcome("acct-c", ok=False, outcome_id="task-9/attempt-1",
                                     failure_kind="task_failed", now=T0 + 1.0)
    assert brain.account_scores()["acct-c"]["attempts"] == 1


def test_the_ceiling_reports_when_it_can_admit_again(tmp_path):
    """Exhausted money is a wait with a time, not a silent stall."""
    clock = [T0]
    brain = _orchestrator(tmp_path / "brain.json", clock,
                          cost_budget_units=2.0, cost_budget_window_seconds=600.0)
    first = brain.admit(2.0, now=T0, account_ref="acct-d")
    brain.settle(first["reservation"], cost_units=2.0, account_ref="acct-d", now=T0)

    denied = brain.admit(1.0, now=T0, account_ref="acct-d")
    assert denied["decision"] == "deny"
    assert denied["reason"] == "cost_budget_exhausted"
    assert denied["retry_at"] == pytest.approx(T0 + 600.0, abs=1.0)

    # Once the window rolls, the same request is admissible without a restart.
    clock[0] = T0 + 601.0
    assert brain.admit(1.0, now=clock[0], account_ref="acct-d")["decision"] == "allow"


def test_rollback_restores_the_configured_baseline_and_is_audited(tmp_path):
    """A learned weight change can be undone, and the undo is on the record."""
    clock = [T0]
    brain = _orchestrator(tmp_path / "brain.json", clock)
    baseline = brain.policy_view()["effective"]

    for attempt in range(2):
        brain.record_account_outcome("acct-e", ok=False, failure_kind="task_failed",
                                     now=T0 + attempt)
    learned = brain.policy_view()
    assert learned["version"] >= 1
    assert learned["effective"] != baseline

    learned_version = brain.policy_view()["version"]
    result = brain.rollback_policy(0, now=clock[0], reason="operator_rollback")
    assert result["changed"] is True
    # Restoring is itself a versioned, audited change: history is appended, not
    # erased, so "who removed what" survives the rollback.
    assert brain.policy_view()["effective"] == baseline
    assert brain.policy_view()["version"] > learned_version
    audit = brain.policy_audit()
    assert audit[-1]["reason"] == "operator_rollback"
    assert audit[-1]["kind"] == "rollback"
    assert audit[-1]["after"] == baseline
    # The rollback is an operator-visible fact, not a silent state change.
    assert any(alert.code == "policy_rolled_back" for alert in brain.drain_alerts())


def test_the_alert_journal_stays_bounded_on_disk(tmp_path):
    """A multi-week unattended run must not fill the disk with alert JSONL."""
    journal = tmp_path / "alerts.jsonl"
    clock = [T0]
    brain = _orchestrator(tmp_path / "brain.json", clock,
                          alert_quiet_seconds=0.0,
                          alert_journal_path=str(journal),
                          alert_journal_max_bytes=2048)
    for index in range(120):
        clock[0] = T0 + index
        brain.raise_alert("bulk_event", subject=f"task-{index}",
                          message="x" * 40, now=clock[0])

    assert journal.exists()
    assert journal.stat().st_size <= 2048 + 4096, "rotation must bound the file"
    for line in journal.read_text(encoding="utf-8").splitlines():
        assert json.loads(line)["code"] == "bulk_event"

    # History itself is bounded too, so memory cannot grow with the journal.
    assert len(brain.alert_history()) <= _config().alert_max_history


def test_a_bounded_run_concludes_instead_of_running_forever(tmp_path):
    clock = [T0]
    brain = _orchestrator(tmp_path / "brain.json", clock, max_run_duration_seconds=60.0)
    brain.start_run(now=T0)
    assert brain.run_verdict(now=T0 + 30.0)["action"] == "continue"
    verdict = brain.run_verdict(now=T0 + 61.0)
    assert verdict["action"] in ("conclude", "stop")
    assert verdict["reason"] == "run_deadline_reached"
    # Past the deadline the loop keeps refusing work; it cannot "un-conclude".
    assert brain.run_verdict(now=T0 + 120.0)["action"] != "continue"


def test_a_healthy_pool_is_never_retuned(tmp_path):
    """No capacity or quality pressure means the learned weights stay put."""
    clock = [T0]
    brain = _orchestrator(tmp_path / "brain.json", clock, policy_min_samples=2)
    for attempt in range(6):
        brain.record_account_outcome("acct-f", ok=True, cost_units=0.1, wall_seconds=30.0,
                                     now=T0 + attempt)
    assert brain.policy_view()["version"] == 0
    assert brain.last_policy_decision() is not None
    assert brain.last_policy_decision()["reason"] == "stable_no_change"


def test_alerts_carry_a_severity_an_operator_can_rank(tmp_path):
    clock = [T0]
    brain = _orchestrator(tmp_path / "brain.json", clock)
    raised = brain.raise_alert("run_degraded", severity="warning", message="慢", now=T0)
    assert raised and raised[0].severity is AlertSeverity.WARNING
    assert raised[0].to_dict()["severity"] == "warning"
