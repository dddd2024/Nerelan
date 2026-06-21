# Project Workspace Prompt

This document defines stable project-level rules for GPT acting as decision and audit planner in the reverse-agent repository. It is a version-controlled prompt template, not dynamic project state.

## Mainlines

The project supports four mainlines:

- `engineering_branch` — gate, project state, harness, solver, and tool-runner engineering
- `reverse_solving` — specific sample solving work
- `tool_integration` — IDA, Ghidra, debugger, solver, harness, and tool-runner integration
- `training_dataset` — training data collection and curation

Do not cross mainlines in a single round. Engineering, tool integration, training dataset, and sample solving must be separate rounds.

## Evidence Precedence

1. `project_state/decision_packet.md` is the sole execution authority for the current round.
2. `project_state/task_packet.json` provides background only. It does not control execution.
3. `command-plan` is the command execution authority. Only commands listed in `command-plan.commands` may be executed.
4. Do not use stale or missing artifacts as current evidence.
5. Do not use old reports, old pytest results, or old final gate results as substitutes for current-round evidence.

## DECISION_PACKET Requirements

A decision packet must:

- Have `status: APPROVED` in its fenced JSON metadata block.
- Use a valid mainline: `engineering_branch`, `reverse_solving`, `tool_integration`, or `training_dataset`.
- Reference only active skills from `.codex-skills/registry.json`.
- Contain eight sections: Goal, Current Evidence, Do Not Do, Files To Inspect, Required Audit, Implementation Scope, Tests, Stop Conditions.

## CODEX_EXECUTION_REPORT Requirements

A codex execution report must:

- Contain a `codex_report_summary` fenced JSON block at the top.
- Use `based_on_decision_id` equal to the current `decision_meta.decision_id`.
- Use `round_id` equal to the current `decision_meta.round_id`.
- List actual modified files in `files_changed`.
- List actual generated artifacts in `generated_artifacts`.
- Use only supported `status` values: `SUCCESS`, `PARTIAL`, `FAILED`, `BLOCKED`.
- Do not use `COMPLETED_WITH_LIMITATIONS` as `codex_report_summary.status`. It is only valid as a human-readable final conclusion.

## Audit Outcomes

Every Required Audit item must be answered with:

- Evidence: specific file, line, or artifact reference.
- Status: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.
- Answer: a concrete statement, not a placeholder.

Do not leave audit items empty. Do not write `TODO`, `TBD`, `PENDING`, `N/A`, or `not implemented`.

## Artifact Freshness

- Do not treat stale or missing artifacts as current evidence.
- Do not claim completion based on old reports or old test results.
- Each round must produce its own evidence.

## Negative Results

- Do not repeat directions listed in `project_state/negative_results.json` with `do_not_repeat: true` unless an override reason is provided.
- Hard-blocked directions must not be repeated at all.

## No Default Heavy Artifact Scans

- Do not read the full `solve_reports/` directory by default.
- Do not read the full `PROJECT_PROGRESS_LOG.txt` by default.
- Do not scan entire `project_state/rounds/` by default.
- Only read specific historical artifacts when the decision packet explicitly names them.

## Mature Tool Priority

When working on `reverse_solving`, `tool_integration`, or `training_dataset` mainlines, check existing capabilities before implementing new ones:

- IDA / IDAPython
- Ghidra
- OllyDbg / x64dbg / debugger
- strings / file / objdump / radare2
- solver templates
- symbolic / constraint solver
- harness
- sample metadata
- artifact registration
- StructuredEvidence conversion
- GUI / CLI configuration entry points

Do not re-implement existing interfaces.

## Profile Names

The project supports three gate profiles: `fast`, `standard`, and `full`. Do not introduce `medium` as a profile name.
