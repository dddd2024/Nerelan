```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260626_neutral_primary_report_migration_v1",
  "round_id": "round_20260626_neutral_primary_report_migration_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260626_execute_decision_cli_flag_transcript_rework_v1",
  "previous_round_id": "round_20260626_execute_decision_cli_flag_transcript_rework_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Migrate live report handling to neutral execution-report primary semantics while keeping legacy Codex-named report artifacts as compatibility aliases for one or more rounds.",
  "command_plan_authority_required": true,
  "accepted_requires_neutral_report_primary": true,
  "accepted_requires_legacy_alias_parity": true,
  "accepted_requires_dual_block_or_equivalent_compat": true,
  "accepted_requires_no_legacy_delete": true,
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

Implement Neutral Primary Report Migration v1.

The previous accepted round made `execute-decision --mode execute` usable and auditable. The next engineering step is to resume the earlier naming-neutralization track without breaking existing reports, gates, tests, or round archives.

This round must make neutral execution-report naming the primary live contract while keeping legacy Codex-named artifacts as compatibility aliases. It must not delete or rename existing historical artifacts, and it must not remove legacy parser support in this round.

Final accepted state must satisfy:

1. `project_state/execution_report.md` is treated as the primary live report path for new current-round report parsing, synthesis, final-check, and closeout.
2. `project_state/codex_execution_report.md` remains generated as a compatibility alias with semantic parity to `project_state/execution_report.md`.
3. A neutral top-level summary block named `execution_report_summary` is supported and preferred for newly generated reports.
4. Legacy `codex_report_summary` remains accepted as fallback compatibility, and if both neutral and legacy summary blocks exist they must be semantically identical.
5. `project_state/gates/execution_report_auto_summary.json` is treated as the primary auto-summary artifact.
6. `project_state/gates/codex_report_auto_summary.json` remains generated as a compatibility alias with semantic parity.
7. `naming_migration_plan.json` must be updated from inventory-only status to reflect the neutral-primary / legacy-alias migration state, without claiming that legacy names were removed.
8. Existing `execute-decision --mode execute`, command-plan authority, pytest_result transcript, execution-log, final-check, report-summary, and run-closeout behavior must not regress.
9. No Phase 2, Web UI, CI, AgentRunner, database, queue, scheduler, reverse-solving, or heavy artifact scan work is allowed.

## 2. Current Evidence

Mainline: `engineering_branch`.

The immediately previous round `decision_20260626_execute_decision_cli_flag_transcript_rework_v1` was accepted. It established:

- `--mode execute` as the canonical execute-decision convention;
- current-round pytest_result status `PASSED`;
- `execute_decision_result.json` with `mode: execute` and `contract_mode: delegated_execution`;
- execution-log required command coverage;
- final-check PASSED;
- run-closeout PASSED.

The current `naming_migration_plan.json` is older and still says `action_this_round: inventory_only`, `no_rename: true`, `no_delete: true`, and `no_neutral_live_path_created: true`. It identifies these Codex-bound names as migration candidates:

- `project_state/codex_execution_report.md` -> `project_state/execution_report.md`;
- `codex_report_summary` -> `execution_report_summary`;
- `project_state/gates/codex_report_auto_summary.json` -> `project_state/gates/execution_report_auto_summary.json`;
- internal and CLI references for `codex_report_auto_summary` and `codex_execution_report`.

The same inventory reports many current code and test references to legacy Codex-bound names in `reverse_agent/project_gate.py` and `tests/test_project_gate.py`. Therefore this round must be a compatibility migration, not a hard deletion or global rename.

`task_packet.json` remains non-authoritative background state. It describes a stale `samplereverse` evidence collection suggestion but explicitly says `decision_packet_controls_current_round`.

`current_state.json` still reflects old sample state and is only the digest baseline for this engineering round.

`negative_results.json` contains reverse-solving prohibitions such as old sample_solver blind search, beam/budget expansion, compare_semantics_agree=false frontiers, and committing full solve_reports. This round does not enter reverse-solving and must not repeat those directions.

Existing implementation evidence to preserve:

- `project_state/execution_report.md` and `project_state/gates/execution_report_auto_summary.json` already exist as neutral aliases in recent accepted artifacts.
- final-check already verifies neutral alias presence and semantic parity against legacy aliases.
- execute-decision and command-plan now provide a shorter controlled local execution path.

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
3. `project_state/gates/naming_migration_plan.json`
4. `project_state/gates/codex_report_auto_summary.json` if present
5. `project_state/gates/execution_report_auto_summary.json` if present
6. `project_state/gates/command_plan.json`
7. `project_state/gates/execute_decision_result.json`
8. `project_state/gates/run_round_result.json` if present
9. `project_state/gates/execution_log.json`
10. `project_state/gates/final_gate_result.json`
11. `project_state/gates/run_closeout_result.json`
12. `project_state/gates/run_closeout_execution_log.json`
13. `project_state/gates/report_summary_synthesis.json`
14. `project_state/gates/round_baseline.json`
15. `project_state/gates/round_delta_summary.json`
16. `project_state/gates/round_close_snapshot.json` if present
17. `project_state/gates/policy_impact_audit.json` if present
18. `project_state/gates/policy_lint_result.json` if present
19. current/previous round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, the current live report must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Is `execution_report.md` now the primary live report path for current report parsing, synthesis, final-check, and closeout?
2. How is `codex_execution_report.md` preserved as a compatibility alias, and how is semantic parity enforced?
3. Is `execution_report_summary` supported and preferred, and how does legacy `codex_report_summary` fallback remain compatible?
4. How are `execution_report_auto_summary.json` and `codex_report_auto_summary.json` generated and checked for semantic parity?
5. How was `naming_migration_plan.json` updated to reflect neutral-primary / legacy-alias status without claiming full legacy removal?
6. Which regression tests cover neutral-primary report parsing, legacy fallback parsing, dual-block parity, auto-summary alias parity, final-check alias enforcement, and closeout compatibility?
7. How did the round preserve execute-decision `--mode execute`, command-plan authority, pytest_result transcript, execution-log, final-check, and run-closeout convergence?
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
- `project_state/gates/command_plan.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/rounds/round_20260626_neutral_primary_report_migration_v1/*`

Required behavior:

1. Update report parsing so neutral `execution_report_summary` is preferred when present.
2. Preserve legacy `codex_report_summary` parsing as fallback.
3. If both neutral and legacy summary blocks are present, compare them semantically and fail final-check on divergence.
4. Generate `execution_report.md` as the primary live report artifact for the current round.
5. Continue generating `codex_execution_report.md` as a semantic compatibility alias.
6. Generate or update `execution_report_auto_summary.json` as the primary auto-summary artifact.
7. Continue generating `codex_report_auto_summary.json` as a semantic compatibility alias.
8. Update final-check and closeout checks to treat neutral artifacts as primary and legacy Codex artifacts as compatibility aliases.
9. Update `naming_migration_plan.json` to reflect this round's migration status: neutral-primary live report, legacy alias retained, no historical rewrite, no deletion yet.
10. Add focused regression tests for neutral-primary behavior and legacy compatibility.
11. Preserve execute-decision `--mode execute` behavior and accepted command-plan/final-check/run-closeout convergence.

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
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260626_neutral_primary_report_migration_v1 --mode execute
```

At minimum, validation should include command-plan-authorized equivalents of:

```powershell
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260626_neutral_primary_report_migration_v1
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

- `execution_report.md` is not primary for current-round report parsing/synthesis/final-check/closeout;
- `codex_execution_report.md` compatibility alias is missing or semantically diverges from `execution_report.md`;
- `execution_report_summary` is unsupported or not preferred when present;
- `codex_report_summary` fallback breaks;
- dual neutral/legacy summary blocks diverge without final-check failure;
- `execution_report_auto_summary.json` and `codex_report_auto_summary.json` diverge;
- `naming_migration_plan.json` still says inventory-only/no-neutral-live-path-created after this migration;
- report claims full Codex naming removal while legacy compatibility names remain;
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
