# Issue 1336 retry guard (T001)

Narrow scope only: `GoalService.escalate_failed_tasks` now skips replacement
creation for an explicit cleanup-uncertain failure, before contract snapshots,
retention or replacement side effects:

- `failure_classification == "cleanup_unconfirmed"`
- `failure_classification == "timeout"` with `failure_detail` starting
  `opencode_timeout:cleanup_unconfirmed:`

Unknown reservations, charges, the original failed task/Goal history and the
existing ordinary-failure/timeout policy are unchanged. No provider, quota,
score, config, benchmark or scheduling changes. No full issue-1336 patch and
no f236 application.

Tests were added only to `tests/platform_v1/test_agent_escalation.py` using the
existing in-memory `_launched`/`_link` helpers plus real `claim_task` ->
`append_usage_observation(UNKNOWN)` -> `complete_task_claim` -> escalation.
They cover both uncertainty forms (no new task, no escalation, no snapshot
evidence, reservation stays `UNKNOWN` with null observed counts) and a positive
control proving UNKNOWN usage alone does not disable ordinary retries.

## Verification

- `python -m py_compile reverse_agent/platform_v1/goal_service.py tests/platform_v1/test_agent_escalation.py` -> syntax-ok.
- `test_agent_escalation.py` and `test_goal_service.py` were not run in this
  CLI; host execution is pending.
- No live DB, provider or model calls were made.

## Still unfinished

Process ownership, partial diagnostics, and the whole of issue 1336 remain
unfinished. This pinned delivery does not prove the scheduler is fixed.
Independent exact-head review, CI and landing are still required.
