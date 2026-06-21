```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_codex_report_auto_summary_v1",
  "round_id": "round_20260621_codex_report_auto_summary_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_structured_execution_log_v1",
  "previous_round_id": "round_20260621_structured_execution_log_v1",
  "previous_acceptance": "ACCEPTED",
  "primary_goal": "Add Codex report auto-summary v1 using execution_log, command-plan, round delta, and gate artifacts while preserving the human-written report body.",
  "command_plan_authority_required": true,
  "accepted_requires_auto_summary_artifact": true,
  "accepted_requires_summary_can_be_generated_from_structured_sources": true,
  "accepted_requires_report_summary_final_check_consistency": true,
  "accepted_requires_manual_report_body_preserved": true,
  "accepted_requires_final_check_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/README.md"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Add Codex Report Auto-Summary v1.

The previous accepted round added `project_state/gates/execution_log.json`, giving the project a structured command ledger while preserving `project_state/pytest_result.txt`. The next gap is report summary generation: `codex_report_summary` is still hand-written by Codex even though most of its fields can now be synthesized from structured artifacts.

This round must add a bounded auto-summary capability that can generate or validate the top fenced `codex_report_summary` JSON block from existing structured sources:

- `project_state/decision_packet.md`
- `project_state/gates/execution_log.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/round_delta_summary.json`
- reportable `project_state/gates/*.json` artifacts
- round archive metadata when available
- final-check/report-summary status evidence when available

The feature must preserve the human-written body of `codex_execution_report.md`, especially Required Audit answers. This is not full report generation and not a runner.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is background only. It still describes stale `samplereverse` work and must not control this round.

Previous round status: `decision_20260621_structured_execution_log_v1` was accepted. Its evidence showed:

- `project_state/gates/execution_log.json` was generated with `gate_status=PASSED`.
- `execution_log.json` recorded 17 commands with `index`, `command`, `kind`, `phase`, `expected_exit_codes`, `exit_code`, and `status`.
- `codex_report_summary.generated_artifacts` included `project_state/gates/execution_log.json`.
- `pytest_result_summary.status` was `PASSED`.
- `tests/test_project_gate.py -q` passed with 725 tests.
- `tests/test_project_gate.py tests/test_project_state.py -q` passed with 1023 tests.
- `execution_log_consistency` passed in final-check.
- command-plan authority, policy-lint, policy-impact, report-summary, final-check, and closeout passed.

Current gap:

- `codex_report_summary` is still manually written.
- `report-summary` can compare a report summary to synthesized evidence, but there is not yet a dedicated auto-summary artifact or write/update path for the report summary block.
- Future `run-round` / `execute-decision` needs a deterministic way to generate the summary fields before a human or model fills in the report body.

Existing capabilities to reuse:

- existing report-summary synthesis logic
- command-plan and execution-log artifacts
- round delta and generated artifact coverage checks
- policy-impact and policy-lint artifact accounting
- final-check status-policy checks
- closeout report refresh logic
- tests in `tests/test_project_gate.py`

This is not a reverse-solving round. Do not inspect or run sample binaries. Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or full `solve_reports/`.

## 3. Do Not Do

Do not implement full report-body generation.

Do not generate Required Audit answers. Required Audit answers remain human/model-authored and must still be substantive.

Do not replace `project_state/codex_execution_report.md`. This round should only automate the top `codex_report_summary` block or produce a draft artifact for it.

Do not replace `project_state/pytest_result.txt` or `project_state/gates/execution_log.json`.

Do not build a full runner, scheduler, AgentRunner, background worker, database, queue, web UI, or message bus.

Do not weaken report-summary or final-check. If generated summary and live report summary disagree, a `SUCCESS` / `ACCEPTED` report must not silently pass.

Do not let auto-summary invent unsupported statuses. `codex_report_summary.status` must remain one of the supported report statuses such as `SUCCESS`, `PARTIAL`, `FAILED`, or `BLOCKED`. Do not write `COMPLETED_WITH_LIMITATIONS` into report status.

Do not write `SUCCESS` / `ACCEPTED` merely because some commands ran. Status/acceptance must remain consistent with tests, final-check, command-plan authority, and report status policy.

Do not modify prompt docs in this round.

Do not change profile names. The current profile names are `fast`, `standard`, and `full`; do not introduce `medium`.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `.codex-skills/registry.json`, or `docs/prompts/*`.

Do not continue `samplereverse` solving. Do not run samples, solvers, harnesses, runtime probes, IDA/Ghidra, debuggers, emulators, GUI workflows, or full `solve_reports/` scans.

Do not push, commit, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Then inspect only files relevant to auto-summary:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/execution_log.json`
4. `project_state/gates/command_plan.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/round_delta_summary.json`
8. `project_state/gates/policy_impact_audit.json`
9. `project_state/gates/policy_lint_result.json`
10. `project_state/gates/codex_report_auto_summary.json` if it already exists

Historical files may be read only by exact path when needed for a focused regression fixture. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What fields does Codex Report Auto-Summary v1 generate, and which structured source supplies each field?
2. What artifact is written for the generated summary, and what schema does it use?
3. How does the auto-summary path preserve the human-written report body and Required Audit answers?
4. How does the feature handle status and acceptance recommendation without inventing unsupported statuses or premature SUCCESS claims?
5. How does report-summary/final-check compare the live `codex_report_summary` against the generated auto-summary?
6. How does auto-summary use `execution_log.json` when available and fall back to existing evidence when absent?
7. What regression tests prove generated fields match execution_log, command-plan, round delta, generated artifacts, and closeout archive expectations?
8. How does this round preserve structured execution log, policy-impact, policy-lint, command-plan authority, report-summary, final-check, closeout, and prompt-doc behavior?

## 6. Implementation Scope

Implement one bounded feature: Codex Report Auto-Summary v1 for the top `codex_report_summary` JSON block.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/rounds/round_20260621_codex_report_auto_summary_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Add an auto-summary builder that synthesizes the `codex_report_summary` fields from structured evidence.
2. The generated summary must include at least: `schema_version`, `report_id`, `round_id`, `based_on_decision_id`, `status`, `acceptance_recommendation`, `files_changed`, `tests_ran`, `generated_artifacts`, `referenced_artifacts`, and `required_closeout_artifacts`.
3. Write a bounded artifact such as `project_state/gates/codex_report_auto_summary.json` containing the generated summary, source provenance, warnings, blocking_reasons, and recommended_next_action.
4. Add a CLI entrypoint such as `python -m reverse_agent.project_gate report-auto-summary --state-dir project_state` if it fits existing CLI structure. If reusing `report-summary`, keep the command behavior clear and testable.
5. Do not auto-generate the report body or Required Audit answers.
6. Preserve `pytest_result.txt` and `execution_log.json`; use execution_log for `tests_ran` when available, with a pytest_result fallback for backward compatibility.
7. Ensure report-summary/final-check compare live `codex_report_summary` against the generated auto-summary or the same synthesis source. A `SUCCESS` / `ACCEPTED` report with mismatched summary fields must fail.
8. Ensure closeout refresh preserves or applies the generated summary fields without losing the human-written body.
9. Add regression tests for: field synthesis, execution_log-derived tests_ran, round_delta-derived files_changed, gate-artifact-derived generated_artifacts, unsupported status rejection, mismatch failure, missing execution_log fallback, body preservation, and closeout preservation.
10. Keep the feature bounded. Do not add persistent storage outside project_state/gates and round archives.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Run preflight before implementation:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
```

If preflight passes, run command-plan and follow only command-plan-authorized commands:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Targeted tests:

```powershell
python -m pytest tests/test_project_gate.py -q
```

Run policy-lint, policy-impact, execution-log, and report-auto-summary only if command-plan explicitly includes or authorizes them:

```powershell
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
```

Final validation commands, only when authorized by command-plan:

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Run closeout only if command-plan explicitly includes or authorizes the closeout command for this round:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_codex_report_auto_summary_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation for unrelated reasons;
2. this requires full report-body generation, Required Audit answer generation, a runner, scheduler, AgentRunner, database, queue, web UI, or background execution automation;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. prompt docs, `.codex-skills/`, or forbidden project_state source files need changes;
5. the implementation replaces or removes `pytest_result.txt` or `execution_log.json`;
6. auto-summary can write unsupported report statuses or premature `SUCCESS`/`ACCEPTED` values;
7. live `codex_report_summary` can disagree with generated auto-summary while final-check still passes for a SUCCESS report;
8. the fix requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
9. structured execution log, policy-impact, policy-lint, command-plan authority, decision-command-plan conflict detection, report-summary, final-check, or closeout regresses;
10. tests fail or any required command exit code is nonzero;
11. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
