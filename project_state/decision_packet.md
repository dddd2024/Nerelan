```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_codex_startup_prompt_contract_rework_v1",
  "round_id": "round_20260617_codex_startup_prompt_contract_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Create a corrected Codex startup/execution prompt contract that removes the ambiguity causing clean startup states to later be reported as inherited source/test dirty, and prevents preflight hard-stop failures from being reported as completed work.

This round is prompt/documentation first. Do not continue gate implementation, generated-artifact work, solver work, reverse solving, or sample work.

Required end state:

- add a reusable prompt contract at `project_state/codex_startup_prompt_contract.md`;
- the prompt contract must clearly distinguish three states:
  1. startup clean before implementation;
  2. startup dirty before implementation;
  3. expected source/test dirty after implementation;
- the prompt contract must state that source/test files modified after startup are this-round changes, not inherited baseline dirty files;
- the prompt contract must state that `COMPLETED_WITH_LIMITATIONS` is a human final-reply label only, not a valid `codex_report_summary.status` unless the project schema explicitly supports it;
- the prompt contract must state that if preflight fails, Codex must stop after recording startup/preflight evidence and write `BLOCKED` or `FAILED` plus `REWORK_REQUIRED`, not continue through the full gate pipeline;
- do not modify Python source, tests, solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` in this round.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Reason for this rework:

- The user provided a startup screenshot showing `git status --short = 空`, meaning the local working tree can be clean before Codex starts implementation.
- Previous rounds repeatedly produced reports where later source/test modifications were treated as startup baseline/inherited dirty, or where preflight hard-stop failures were described as completion with limitations.
- The current external prompt has two ambiguous parts:
  - it says startup dirty files should be recorded as baseline dirty, but later decisions require source/test startup dirty to be a hard stop;
  - it asks for final item 12 to use `COMPLETED_WITH_LIMITATIONS`, while the project report schema/final gate has rejected unsupported `codex_report_summary.status=COMPLETED_WITH_LIMITATIONS`.
- Therefore the first fix should be prompt-level: make the startup/preflight/report-status contract unambiguous before continuing implementation work.

Important interpretation:

- If the startup `git status --short` is clean, Codex must record that fact and treat later `reverse_agent/*.py` or `tests/*.py` changes as this-round modifications.
- Codex must not rerun or recapture startup baseline after modifying source/test files and then call those files inherited dirty.
- If startup source/test dirty exists before implementation, Codex must stop and report `BLOCKED` or `FAILED/REWORK_REQUIRED`, unless the active decision had an explicit trusted allowlist before execution.
- If preflight fails, the full Tests list is not a command sequence to blindly continue; it becomes a stop condition unless the command is part of a controlled unit-test fixture.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
- `decision_immutability` hard stop;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` structural mismatch FAIL behavior;
- generated-artifact live-path existence checks;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check;
- gate-profile classifier behavior.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this prompt-contract rework.
- This round does not depend on reverse sample artifacts.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat old `samplereverse` failed candidate/runtime branches.

Allowed tool execution:

- Read compact `project_state/` metadata and the existing prompt/guide files needed to write the prompt contract.
- Run only lightweight file/status validation and any non-invasive project-state lint needed for the prompt artifact.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not modify Python source or tests in this round.

Do not continue expanding generated-artifact functionality.

Do not rewrite clean-start guard, report-summary, final-check, or close-round code.

Do not modify `.codex-skills/` or `.codex-skills/registry.json`.

Do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, runtime probe, GUI/frontend, sample runner, raw sample files, or training sample metadata.

Do not run sample binaries.

Do not run IDA/Ghidra/debugger/harness/solver/runtime probe commands.

Do not use unsupported `codex_report_summary.status=COMPLETED_WITH_LIMITATIONS`.

Do not call this round `COMPLETED` if only the prompt artifact was written but required validation/report files are missing.

Do not treat `task_packet.task` as current execution authority.

Do not upload, push, create PR, merge, rebase, or switch branches from Codex unless a separate user message explicitly says to do so.

## 4. Files To Inspect

Read default project-state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect only as needed:

- `AGENT_GUIDE_FOR_AI.md`
- `README.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`

Do not inspect unrelated solver/harness/tool-runner modules.

## 5. Required Audit

Before writing the prompt contract, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any modification.
3. If startup source/test files are dirty, do not edit code; because this round is prompt/document-only, either stop with `BLOCKED` or proceed only if the dirty files are known inherited user work and are not touched.
4. If startup `project_state/decision_packet.md` is dirty, stop and report `BLOCKED`.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. Current decision controls execution; `task_packet.json` is not authoritative.
7. Confirm the prompt ambiguity before writing the prompt contract:
   - startup clean vs post-implementation dirty;
   - inherited baseline dirty vs this-round files_changed;
   - human final label vs `codex_report_summary.status` schema;
   - preflight failure stop condition vs full gate pipeline.
8. No mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed documentation/prompt artifact:

- `project_state/codex_startup_prompt_contract.md` (create or replace)

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json` only if preflight is run for lightweight validation
- `project_state/gates/command_plan.json` only if command-plan is run for lightweight validation
- `project_state/gates/gate_profile_plan.json` only if gate-profile is run for lightweight validation

Do not modify:

- `reverse_agent/*.py`
- `tests/*.py`
- `.codex-skills/*`
- solver/harness/tool-runner/debugger/sample/GUI files
- raw sample files

Required content for `project_state/codex_startup_prompt_contract.md`:

1. A short purpose statement: this prompt is for Codex local execution in `F:\reverse-agent`.
2. A strict startup block that must run before any file modification.
3. A state classification table:
   - startup clean: continue; later source/test dirty files are this-round changes;
   - startup project_state/generated dirty only: record as baseline and continue with caution;
   - startup source/test dirty: hard stop unless pre-existing decision allowlist exists;
   - startup live decision dirty: hard stop.
4. A preflight rule:
   - run preflight before implementation;
   - if preflight fails, stop and write `BLOCKED` or `FAILED/REWORK_REQUIRED` report;
   - do not run the remaining full gate pipeline after preflight failure.
5. A report status vocabulary rule:
   - `codex_report_summary.status` may use only schema-supported statuses such as `SUCCESS`, `PARTIAL`, `FAILED`, or `BLOCKED`;
   - `COMPLETED_WITH_LIMITATIONS` is only a human final-reply label if used at all, not a JSON report status unless schema explicitly supports it;
   - when preflight or required gates fail, `acceptance_recommendation` must be `REWORK_REQUIRED` or `BLOCKED`, never accepted.
6. A files_changed rule:
   - files changed after startup are this-round changes;
   - baseline dirty files are only those present in startup evidence before implementation;
   - do not classify implementation edits as inherited dirty.
7. A testing rule:
   - the Tests list is conditional on preflight success;
   - if preflight fails, record startup/preflight evidence and stop;
   - if command blocks contain non-zero exit codes, `pytest_result_summary.status` cannot be `PASSED`.
8. A final 12-item reply rule that distinguishes user-facing completion label from JSON report status.
9. A compact corrected prompt block that the user can paste into Codex.

Required report behavior for this round:

- If only the prompt contract is created and validation succeeds, use `status=SUCCESS` or `PARTIAL` according to actual validation.
- If startup dirty source/test files prevent safe editing, use `status=BLOCKED` or `FAILED` and `acceptance_recommendation=REWORK_REQUIRED` or `BLOCKED`.
- Do not use `COMPLETED_WITH_LIMITATIONS` as JSON status.

## 7. Tests

Because this round is documentation/prompt-only, do not run broad pytest unless Python files are modified by mistake.

Run and record lightweight validation in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
Test-Path F:\reverse-agent\project_state\decision_packet.md
Test-Path F:\reverse-agent\project_state\codex_startup_prompt_contract.md
Test-Path F:\reverse-agent\project_state\pytest_result.txt
Test-Path F:\reverse-agent\project_state\codex_execution_report.md
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
```

Optional only if startup state is clean and no source/test files are modified:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Do not run `final-check` or `close-round` if preflight fails or if this prompt-only round intentionally leaves no closeable code implementation.

The pytest result header must include:

- `decision_id=decision_20260617_codex_startup_prompt_contract_rework_v1`
- `round_id=round_20260617_codex_startup_prompt_contract_rework_v1`
- the final `report_id`
- all commands actually run

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` shows live `project_state/decision_packet.md` dirty;
- startup source/test dirty files exist and cannot be safely left untouched while creating only the prompt artifact;
- temporary paths such as `tmp*/` cannot be safely removed or explained;
- implementing this requires modifying Python source/tests or gate code;
- implementing this requires rewriting close-round or replacing the existing gate system;
- the change would require modifying solver/harness/tool-runner/debugger/sample code;
- prompt contract cannot be written without broad refactoring;
- validation fails for reasons outside the narrow prompt-contract scope.
