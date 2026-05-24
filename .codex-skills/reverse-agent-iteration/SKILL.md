---
name: reverse-agent-iteration
description: Use when working in the reverse-agent repository on project_state-driven engineering or reverse-solving iterations. This generic workflow layer defines source-of-truth order, decision packet authority, artifact freshness discipline, reporting, and validation without encoding sample-specific candidates, run names, or artifact paths.
metadata:
  short-description: Project_state-first reverse-agent workflow
---

# Reverse Agent Iteration

Use this skill for `reverse-agent` repository work. It provides the durable workflow contract; dynamic facts belong in `project_state`, and sample-specific constraints belong in a sample profile skill.

## Default Source Order

Start from the compact project state packet unless the user's request explicitly narrows the scope further:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`

Treat `project_state/decision_packet.md` as the current Codex execution authority when it exists and its decision status allows execution. `task_packet.task` and `derived_task` are suggested or state-derived tasks; they do not automatically override an active decision packet.

## Mainline Classification

Before choosing work, classify the current round:

- `engineering_branch`: project_state, handoff, reporting, docs, skill, lint, sync, archive, or test infrastructure work.
- `reverse_solving`: bounded sample analysis, runtime evidence, candidate generation, validation, or strategy work.

Do not mix the branches. Engineering rounds must not advance sample solving unless the decision packet explicitly authorizes that expansion. Reverse-solving rounds must still obey `artifact_index` freshness and `negative_results`.

## Artifact Discipline

Use `project_state/artifact_index.json`, especially `latest_artifacts_v2`, to identify current, stale, and missing artifacts. Read referenced artifact files only when the current task needs their contents.

Do not scan full `solve_reports/` by default. Do not inspect the newest `solve_reports/harness_runs/*` directory merely because it exists. If the compact state is missing or contradictory and a bounded artifact read is required, record why the read was necessary.

Read `PROJECT_PROGRESS_LOG.txt` only when:

- the compact project_state packet is missing or unusable;
- `model_gate.context_level=3` requests broader context;
- a strategic retrospective is explicitly requested;
- a state conflict needs historical wording to resolve safely.

## Local Search Policy

- In the Codex desktop Windows environment for this repository, use PowerShell-native search by default: `Get-ChildItem -Recurse -File` with `Select-String`, plus `Get-Content` / `Select-String -Context` for file reads.
- The bundled `rg.exe` may be blocked by Windows app permissions; only retry it when explicitly useful.
- Keep broad recursive searches out of `solve_reports/` unless the decision packet authorizes that scope.

## Choosing Next Work

For engineering rounds, preserve compatibility and keep changes additive unless the decision packet requires a breaking cleanup. Prefer narrow changes to the relevant project_state, docs, skill, sync, or test surface.

For reverse-solving rounds, map the latest bottleneck from `current_state` and current artifacts before touching solver logic:

- `instrumentation`: improve runtime evidence capture or artifact fields.
- `candidate generation`: adjust bounded candidate sources or provenance.
- `gate/filtering`: add diagnostics or refine acceptance bands before expanding search.
- `refine`: improve handoff quality or anchor/context selection.
- `SMT`: adjust variable positions, values, or objective within the existing solver path.
- `validation`: fix compare/runtime consistency, explicit validation candidates, or output paths.
- `reporting/logging`: preserve behavior and repair observability.

Do not expand to blind brute force unless fresh evidence specifically invalidates structured routes and the decision packet authorizes the change.

## Implementation Discipline

- Preserve user or previous-agent edits; inspect dirty state before editing tracked files.
- Keep generic framework changes sample-neutral.
- Put challenge-specific anchors, thresholds, and candidate facts in sample profiles or `project_state`, not this skill.
- Run the narrow relevant tests first, then broader tests when feasible.
- Do not run runtime harnesses or probes during engineering rounds unless the decision packet explicitly requires them.

## Reporting

Write meaningful Codex execution results to `project_state/codex_execution_report.md`. Reports for decision-driven rounds must start with a `codex_report_summary` block and include:

- decision id / round id linkage;
- files changed and generated artifacts;
- tests and sync checks actually run;
- acceptance recommendation;
- remaining limitations and next suggested task.

When reporting to the user, include the files changed, tests run, whether artifacts were complete when relevant, and any residual risk. For engineering rounds, state explicitly that no reverse-solving runtime probe was run.
