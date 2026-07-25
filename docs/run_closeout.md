# Run-Closeout Workflow

> **Legacy / Compatibility Documentation.**
> This file is retained for legacy compatibility and historical reference. It is **not** the default workflow for ordinary R0/R1 Path-A work in the current minimal-integration baseline.
>
> Ordinary R0/R1 authority comes from an **approved immutable GitHub Work Item snapshot** (Issue created from the R1 template, `r1-approved` label applied by the repository owner/maintainer, normalized Issue-body SHA-256 digest recorded in the Draft PR body). Ordinary R0/R1 does **not** require `project_state/decision_packet.md`, `project_state/gates/command_plan.json`, or `run-closeout`.
>
> The Decision / Command Plan / `run-closeout` model described below applies only to:
> - legacy rounds that were planned under the older Path-B/Decision-driven model; and
> - current transition / R2-R3 Path-B work that has a bounded approved Decision and `PRE_EXECUTION_AUTHORIZED`.
>
> Active guidance:
> - [`../AGENTS.md`](../AGENTS.md)
> - [`roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md`](roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md)
> - [`architecture/SOURCE_OF_TRUTH_MATRIX.md`](architecture/SOURCE_OF_TRUTH_MATRIX.md)

## Execution Authority

> **Scope qualifier.** The statements below describe the legacy Path-B / older-branch authority model. For ordinary current R0/R1 Path-A work, the execution authority is the approved immutable GitHub Work Item snapshot, not `project_state/decision_packet.md`.

- `project_state/decision_packet.md` is the sole execution authority for each legacy/transition Path-B round.
- `project_state/task_packet.json` is advisory only and must not override the decision packet.

## Default Closeout Command

> **Scope qualifier.** `run-closeout` is the legacy / default closeout command only when an applicable Path-B Decision and gate profile require it. It is **not** required for ordinary R0/R1 Path-A work, which is closed through the immutable Work Item snapshot, Draft PR, independent audit, and human merge sequence described in `AGENTS.md`.

After implementation work on an approved engineering or tool-integration round, the default closeout command is:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id <active_round_id>
```

`run-closeout` orchestrates the full gate pipeline:

1. `decision-lint`
2. `preflight`
3. `pytest`
4. `gate-profile`
5. `command-plan`
6. `command-plan --json`
7. `report-summary`
8. `final-check`
9. `close-round`
10. `final-check` (after close)

When the active decision is APPROVED, closeout is allowed by the gate profile, and the mainline supports `run-closeout`, `command-plan` recommends the `run-closeout` command as the preferred next action. The Do Not Do section is analyzed at line level: only lines that explicitly prohibit running `run-closeout` (e.g. "Do not run run-closeout") suppress the recommendation. Mentions of `run-closeout` in other contexts (e.g. "Do not replace run-closeout with a workflow engine") do not suppress it.

## Manual Fallback

Manual command-plan execution remains as a fallback when:

- `run-closeout` is not supported for the mainline.
- Closeout is not allowed by the gate profile.
- Decision metadata is invalid or missing.
- The decision explicitly prohibits running `run-closeout` (line-level negation patterns: "do not run", "do not use", "do not execute", "do not call", "do not invoke" followed by `run-closeout`).

In these cases, `command-plan` recommends `record_and_follow_command_plan_manually`.

## Final-Check Enforcement

When a decision requires `run-closeout` recommendation (approved engineering round with closeout allowed), `final-check` verifies that `command_plan.json` contains `run-closeout` and the active `round_id` in `recommended_next_action`. If the recommendation is still `record_and_follow_command_plan_manually` or omits the round id, `final-check` fails with check `command_plan_recommends_run_closeout`.

## Evidence Artifacts

`run-closeout` writes the following evidence artifacts:

- `project_state/pytest_result.txt` — real test output with command blocks and exit codes.
- `project_state/codex_execution_report.md` — structured report with `codex_report_summary` JSON block.
- `project_state/gates/*.json` — gate result artifacts (preflight, gate-profile, command-plan, report-summary, final-check, close-round, etc.).
- `project_state/rounds/<round_id>/` — round archive containing copies of the report, pytest result, decision packet, and round manifest.

## Required Audit Answers

Required Audit answers in `codex_execution_report.md` must be substantive for `SUCCESS` or `ACCEPTED` reports. Answers containing unresolved markers (such as `(to be filled)`, `TODO`, `TBD`, `PENDING`, `placeholder`, `N/A`, `not yet`, `not implemented`) or empty fields will cause:

- `FAIL` for `SUCCESS` or `ACCEPTED` reports.
- `WARN` for non-success reports.

The `_refresh_codex_report_for_closeout` function prevents the report from being promoted to `SUCCESS` while unresolved markers remain, forcing substantive answers before success.

## Forbidden Live Build

When the active decision's Do Not Do section forbids live `python -m reverse_agent.project_state build`, `command-plan` must not list that command as a required or recommended command. If a status or build-like command is needed, it must be represented as a non-mutating status/read command or omitted with an explicit reason.
