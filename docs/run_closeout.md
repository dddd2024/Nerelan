# Run-Closeout Workflow

## Execution Authority

- `project_state/decision_packet.md` is the sole execution authority for each round.
- `project_state/task_packet.json` is advisory only and must not override the decision packet.

## Default Closeout Command

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

When the active decision is APPROVED, closeout is allowed by the gate profile, and the mainline supports `run-closeout`, `command-plan` recommends the `run-closeout` command as the preferred next action.

## Manual Fallback

Manual command-plan execution remains as a fallback when:

- `run-closeout` is not supported for the mainline.
- Closeout is not allowed by the gate profile.
- Decision metadata is invalid or missing.
- The decision explicitly prohibits `run-closeout`.

In these cases, `command-plan` recommends `record_and_follow_command_plan_manually`.

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
