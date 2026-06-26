```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260626_neutral_primary_report_source_rework_v1",
  "round_id": "round_20260626_neutral_primary_report_source_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260626_neutral_primary_report_migration_v1",
  "previous_round_id": "round_20260626_neutral_primary_report_migration_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair neutral-primary report migration so report-summary, final-check, and closeout treat execution_report.md / execution_report_summary as the primary source and legacy Codex-named artifacts only as compatibility aliases.",
  "command_plan_authority_required": true,
  "accepted_requires_synthesis_execution_report_source_neutral": true,
  "accepted_requires_legacy_report_source_marked_alias": true,
  "accepted_requires_final_check_primary_neutral_wording": true,
  "accepted_requires_closeout_primary_neutral_wording": true,
  "accepted_requires_required_audit_alignment": true,
  "accepted_requires_pytest_result_status_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_no_phase2_scope": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
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

Repair Neutral Primary Report Source Rework v1.

The previous round `decision_20260626_neutral_primary_report_migration_v1` generated `execution_report.md` and `execution_report_summary`, but audit found that report-summary synthesis and closeout still described the legacy Codex report as the primary source. This round must fix the source semantics.

Final accepted state must satisfy:

1. `project_state/gates/report_summary_synthesis.json` must identify `project_state/execution_report.md` as the primary execution report source.
2. The same synthesis artifact must identify `project_state/codex_execution_report.md` only as a legacy or compatibility alias source.
3. `execution_report_summary` must be the preferred current-round summary block when both neutral and legacy blocks are available.
4. `codex_report_summary` must remain a fallback compatibility block, not the primary live summary block.
5. final-check details must no longer describe `codex_report_summary` as the primary synthesis alignment object for current-round accepted reports.
6. closeout details must no longer report only `codex report summary parsed` when the neutral report is available and primary; it must report neutral parsing or an equivalent neutral-primary detail.
7. dual-file and dual-block semantic parity must remain enforced.
8. `naming_migration_plan.json` must continue to describe `neutral_primary_with_legacy_alias`, without claiming full legacy removal.
9. Existing `execute-decision --mode execute`, command-plan authority, pytest_result transcript, execution-log, final-check, report-summary, and run-closeout behavior must not regress.
10. No Phase 2, Web UI, CI, AgentRunner, database, queue, scheduler, reverse-solving, or heavy artifact scan work is allowed.

## 2. Current Evidence

Mainline: `engineering_branch`.

The previous round `decision_20260626_neutral_primary_report_migration_v1` is not accepted by audit. It produced apparently passing gates, but its primary-source semantics did not meet the decision goal.

Blocking evidence from the failed round:

- `project_state/execution_report.md` used neutral fenced block `execution_report_summary`.
- `project_state/codex_execution_report.md` used legacy fenced block `codex_report_summary`.
- `project_state/gates/naming_migration_plan.json` changed from inventory-only to `action_this_round: neutral_primary_with_legacy_alias`, `neutral_live_path_created: true`, and `legacy_alias_retained: true`.
- `project_state/gates/report_summary_synthesis.json` still used `"execution_report": "project_state/codex_execution_report.md"` and `"neutral_execution_report": "project_state/execution_report.md"`, so synthesis still treated the legacy path as primary and the neutral path as secondary.
- `project_state/gates/final_gate_result.json` still said `codex_report_summary matches synthesized summary`, which is legacy-primary wording.
- `project_state/gates/run_closeout_result.json` still said `codex report summary parsed`, which is legacy-primary closeout wording.
- Required Audit answers were misaligned: item 1 did not directly prove that neutral report was primary, and item 5 discussed tests instead of how `naming_migration_plan.json` was updated.

`task_packet.json` remains non-authoritative background state. It describes a stale `samplereverse` evidence collection suggestion but explicitly says `decision_packet_controls_current_round`.

`current_state.json` still reflects old sample state and is only the digest baseline for this engineering round.

`negative_results.json` contains reverse-solving prohibitions such as old sample_solver blind search, beam/budget expansion, compare_semantics_agree=false frontiers, and committing full solve_reports. This round does not enter reverse-solving and must not repeat those directions.

Existing implementation evidence to preserve:

- `execution_report.md` and `execution_report_summary` already exist and must remain generated.
- `codex_execution_report.md` and `codex_report_summary` must remain compatibility aliases.
- final-check already verifies dual-file and dual-block parity; those checks must not be weakened.
- execute-decision `--mode execute` and command-plan authority were previously accepted and must not regress.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not delete `project_state/codex_execution_report.md` in this round.

Do not delete `project_state/gates/codex_report_auto_summary.json` in this round.

Do not break parser support for `codex_report_summary` in this round.

Do not claim "Codex wording fully removed" while compatibility aliases, historical archives, `.codex-skills`, or legacy summary names still exist.

Do not rename `.codex-skills/` or modify `.codex-skills/registry.json` in this round.

Do not rewrite historical round archives or attempt global repository-wide Codex string removal.

Do not modify docs prompt files in this round.

Do not let `report_summary_synthesis.json` continue to label `project_state/codex_execution_report.md` as `execution_report` when `project_state/execution_report.md` exists.

Do not let final-check or closeout use legacy-primary wording in an accepted neutral-primary round.

Do not let Required Audit answers pass if they answer the wrong item.

Do not weaken accepted checks for pytest_result PASSED, failed command block absence, archive parity, execution-log required command coverage, command-plan artifact parity, execute-decision contract, run-closeout final-success semantics, and nested closeout failure absence.

Do not leave neutral and legacy report summaries semantically divergent.

Do not let final-check pass if `execution_report.md` and `codex_execution_report.md` are both present but inconsistent.

Do not let final-check pass if `execution_report_auto_summary.json` and `codex_report_auto_summary.json` are both present but inconsistent.

Do not implement Web UI, CI integration, AgentRunner adapters, database, queue, scheduler, background daemon, or multi-agent orchestration in this round.

Do not inspect, run, solve, debug, or emulate sample binaries.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Do not use `COMPLETED_WITH_LIMITATIONS` as report status.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message given to the executor.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/execution_report.md` if present
7. `project_state/decision_packet.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Then inspect only bounded implementation and gate evidence:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/naming_migration_plan.json`
7. `project_state/gates/codex_report_auto_summary.json` if present
8. `project_state/gates/execution_report_auto_summary.json` if present
9. `project_state/gates/command_plan.json`
10. `project_state/gates/execute_decision_result.json`
11. `project_state/gates/execution_log.json`
12. `project_state/gates/run_closeout_execution_log.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`
15. `project_state/gates/round_close_snapshot.json` if present
16. `project_state/gates/policy_impact_audit.json` if present
17. `project_state/gates/policy_lint_result.json` if present
18. current/previous round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, the current live report must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Does `report_summary_synthesis.json.sources.execution_report` now point to `project_state/execution_report.md`?
2. Is `project_state/codex_execution_report.md` now identified as a legacy or compatibility alias source in synthesis/final-check/closeout evidence?
3. Does final-check align the synthesized summary against `execution_report_summary` or neutral-primary report evidence, not legacy-primary `codex_report_summary` wording?
4. Does closeout report neutral-primary parsing, or an equivalent detail that proves `execution_report.md` is the primary live report source?
5. Are dual-file and dual-block semantic parity checks still enforced for neutral and legacy reports?
6. Does `naming_migration_plan.json` accurately describe neutral-primary + legacy-alias status without claiming legacy deletion or full Codex removal?
7. Did the round preserve execute-decision `--mode execute`, command-plan authority, pytest_result transcript, execution-log, final-check, and run-closeout convergence?
8. How does this rework preserve no forbidden path mutation, no `.codex-skills` rename, no docs prompt mutation, no Web/CI/AgentRunner/database/queue/scheduler work, no reverse-solving, and no heavy artifact scans?

Do not write TODO, TBD, PENDING, `should pass`, `expected to pass`, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

- `project_state/execution_report.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/execution_report_auto_summary.json`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/naming_migration_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/rounds/round_20260626_neutral_primary_report_source_rework_v1/*`

Required behavior:

1. Make report-summary synthesis treat `project_state/execution_report.md` as the primary report source.
2. Rename or add synthesis source fields so `project_state/codex_execution_report.md` is clearly marked as legacy, compatibility, or alias source.
3. Update final-check detail text and checks so current accepted neutral-primary reports do not say only `codex_report_summary matches synthesized summary` as the primary alignment statement.
4. Update closeout detail text and checks so current accepted neutral-primary reports do not say only `codex report summary parsed` as the report-present evidence.
5. Preserve fallback parsing of legacy `codex_report_summary` for older reports and archives.
6. Preserve semantic parity checks for `execution_report.md` vs `codex_execution_report.md` and `execution_report_auto_summary.json` vs `codex_report_auto_summary.json`.
7. Strengthen Required Audit coverage to detect answer/item misalignment like the previous round's item 1 and item 5 errors.
8. Ensure `naming_migration_plan.json` still says neutral primary with legacy alias, no rename, no delete, no historical rewrite.
9. Add focused regression tests for synthesis source naming, final-check neutral-primary wording, closeout neutral-primary wording, Required Audit answer alignment, and legacy fallback compatibility.
10. Preserve execute-decision `--mode execute` behavior and accepted command-plan/final-check/run-closeout convergence.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Then use the accepted short execution path. Run preflight and command-plan first if needed, then execute only command-plan-authorized commands.

The preferred current-round entrypoint is:

```powershell
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260626_neutral_primary_report_source_rework_v1 --mode execute
```

At minimum, validation should include command-plan-authorized equivalents of:

```powershell
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260626_neutral_primary_report_source_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands and exit codes in `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- implementation requires forbidden path mutation;
- implementation requires Phase 2 / Web / CI / AgentRunner scope;
- implementation requires sample-solving or heavy artifact scan.

Stop with `REWORK_REQUIRED` if:

- `report_summary_synthesis.json` still labels `project_state/codex_execution_report.md` as `execution_report` while neutral report exists;
- `report_summary_synthesis.json.sources.execution_report` does not point to `project_state/execution_report.md`;
- `project_state/codex_execution_report.md` is not explicitly marked as legacy/compatibility/alias source;
- final-check still uses legacy-primary `codex_report_summary matches synthesized summary` wording as the primary accepted-state check;
- closeout still says only `codex report summary parsed` when neutral report is available;
- Required Audit answers are missing, placeholder, or semantically misaligned with the numbered questions;
- dual-file or dual-block semantic parity breaks;
- `naming_migration_plan.json` claims full legacy removal or still misrepresents migration state;
- execute-decision `--mode execute` regresses;
- command-plan stdout differs from live command_plan.json;
- execution-log has missing required command-plan commands;
- final-check fails;
- run-closeout fails;
- pytest_result_summary.status is not `PASSED` in accepted state;
- report status disagrees with pytest_result, execution-log, final-check, or run-closeout;
- forbidden paths are modified;
- `.codex-skills` is renamed or registry is modified;
- work enters Web/CI/AgentRunner/database/queue/scheduler/reverse-solving/heavy scan;
- tests fail;
- policy-lint or policy-impact fails.
