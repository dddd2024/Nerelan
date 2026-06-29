# Codex Execution Prompt

This document defines stable local Codex execution rules for the reverse-agent repository. It is a version-controlled prompt template, not dynamic project state.

## Working Directory

The working directory must be `F:\reverse-agent`. All operations must occur within this repository.

## Startup Checks

Before any file modification, execute and record:

1. `Set-Location F:\reverse-agent`
2. `Get-Location` — must show `F:\reverse-agent`
3. `Test-Path F:\reverse-agent` — must be `True`
4. `git rev-parse --show-toplevel` — must point to `F:/reverse-agent`
5. `git status --short` — the first output is the startup baseline

If the directory is missing, not a Git repository, or the startup baseline has source/test files dirty under `reverse_agent/` or `tests/`, stop immediately. Current-round source/test inherited dirty allowlists are not valid substitutes for a clean startup snapshot.

## Decision Packet Authority

`project_state/decision_packet.md` is the sole execution authority for the current round. `project_state/task_packet.json` provides background only and must not control execution.

## Preflight Before Implementation

Run preflight before any implementation modification:

```powershell
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
```

If preflight fails, stop. Do not continue the gate pipeline.

## Command-Plan Authority

After preflight passes, generate or read the command-plan:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Only commands listed in `command-plan.commands` may be executed. Do not execute commands from `command-plan.omitted_commands`. If the decision Tests section conflicts with command-plan, command-plan takes precedence.

## Allowed Commands Only

Do not execute commands outside the command-plan authorized list, except for startup confirmation, preflight, and command-plan generation itself.

## Report and pytest_result Requirements

After implementation, update:

- `project_state/pytest_result.txt` — must record decision_id, round_id, test commands, stdout, stderr, exit code, and conclusion.
- `project_state/codex_execution_report.md` — must contain a `codex_report_summary` fenced JSON block with all required fields.

The `codex_report_summary.status` must be one of: `SUCCESS`, `PARTIAL`, `FAILED`, `BLOCKED`. Do not use `COMPLETED_WITH_LIMITATIONS` as the status value.

## Closeout Rules

Run closeout only if command-plan authorizes it:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id <current_round_id>
```

If closeout runs, rerun report-summary and final-check afterward.

## Final Response Fields

The final response must contain 12 fields including current directory, decision_id/round_id, modified files, generated artifacts, test commands, test results, pytest_result status, codex_execution_report status, Test-Path results, git status summary, git diff summary, and a completion conclusion.

The conclusion must be one of: `COMPLETED`, `COMPLETED_WITH_LIMITATIONS`, `REWORK_REQUIRED`, `BLOCKED`.

## No Remote Mutation

Do not execute `git commit`, `git push`, create PRs, upload to GitHub, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message.

## Profile Names

Use `fast`, `standard`, or `full` profiles. Do not use `medium` as a profile name.
