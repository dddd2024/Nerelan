```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260625_executor_neutral_report_alias_compat_v1",
  "round_id": "round_20260625_executor_neutral_report_alias_compat_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260624_closeout_final_state_sync_rework_v1",
  "previous_round_id": "round_20260624_closeout_final_state_sync_rework_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Add an executor-neutral report alias compatibility layer while preserving legacy codex_* report paths and summary blocks. This is compatibility, not deletion or migration.",
  "command_plan_authority_required": true,
  "accepted_requires_legacy_report_compatibility": true,
  "accepted_requires_neutral_report_alias": true,
  "accepted_requires_neutral_auto_summary_alias": true,
  "accepted_requires_legacy_and_neutral_summary_semantic_parity": true,
  "accepted_requires_parser_accepts_legacy_and_neutral_summary_blocks": true,
  "accepted_requires_no_legacy_delete_or_rename": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_required_commands_recorded": true,
  "accepted_requires_state_hygiene_inventory_scope_complete": true,
  "accepted_requires_no_phase2_scope": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/naming_migration_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/state_hygiene_inventory.json",
    "project_state/rounds/round_20260625_executor_neutral_report_alias_compat_v1/*"
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
  ],
  "legacy_paths_that_must_remain": [
    "project_state/codex_execution_report.md",
    "project_state/gates/codex_report_auto_summary.json"
  ],
  "neutral_alias_paths_allowed_this_round": [
    "project_state/execution_report.md",
    "project_state/gates/execution_report_auto_summary.json"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement Executor-Neutral Report Alias Compatibility v1.

Phase 1.5 closeout and final-state synchronization are now accepted. The next small engineering step is to remove the architectural coupling between the reporting pipeline and the Codex executor name, without deleting or renaming any legacy artifacts.

This round must introduce an executor-neutral compatibility layer for report artifacts:

- legacy live report path remains: `project_state/codex_execution_report.md`;
- neutral live report alias is allowed and should be generated: `project_state/execution_report.md`;
- legacy report summary block remains supported: `codex_report_summary`;
- neutral report summary block should be supported: `execution_report_summary`;
- legacy auto-summary path remains: `project_state/gates/codex_report_auto_summary.json`;
- neutral auto-summary alias is allowed and should be generated: `project_state/gates/execution_report_auto_summary.json`.

This is compatibility work, not a migration cleanup. Do not delete, rename, or stop generating legacy Codex-named artifacts. Do not change the audit contract to require users or tools to switch immediately. The accepted result must prove that legacy and neutral report artifacts are semantically equivalent and that all existing gates still pass.

This is still `engineering_branch` Phase 1.5. Do not enter Phase 2 CI/Web/AgentRunner/database/multi-executor runtime work.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state and is not authoritative. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `ACCEPTED` for `decision_20260624_closeout_final_state_sync_rework_v1`.

Accepted prior-round facts:

- `codex_execution_report.md` reached `SUCCESS / ACCEPTED` with current decision/report/round IDs.
- `pytest_result.txt` reached `PASSED`.
- `execution_log.json.gate_status` reached `PASSED`.
- `report_summary_synthesis.json.synthesis_status` reached `PASSED` with no diffs, errors, or warnings.
- `final_gate_result.json.gate_status` reached `PASSED`, with `archive_status: archived`, no warnings, and no blocking reasons.
- `run_closeout_result.json.closeout_status` reached `PASSED` with non-empty executed closeout steps.
- current round archive files were generated and covered.
- `execution_log_required_commands_recorded` was PASS.
- `state_hygiene_inventory_scope_complete` was PASS.

Relevant naming evidence from the previous naming-hygiene inventory:

- `codex_execution_report.md` was identified as executor-specific naming debt.
- `codex_report_summary` was identified as executor-specific report block naming debt.
- `codex_report_auto_summary.json` was identified as executor-specific gate artifact naming debt.
- neutral target names were proposed: `execution_report.md`, `execution_report_summary`, and `execution_report_auto_summary.json`.

Artifact freshness:

- All proof for this round must be regenerated under `decision_20260625_executor_neutral_report_alias_compat_v1` and `round_20260625_executor_neutral_report_alias_compat_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices only and must not be claimed as current evidence.

Existing capabilities to preserve:

- command-plan authority and omitted-command enforcement.
- required-command recording enforcement.
- report-auto-summary consistency.
- report-summary synthesis and final-check strictness.
- Required Audit placeholder blocking.
- closeout/final-state archive synchronization.
- `state_hygiene_inventory_scope_complete`.
- naming-hygiene inventory-only/no-delete behavior for legacy artifacts.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round changes report parsing/generation and final-check/report-summary semantics, command-plan should select or require `full` validation.
- Tests are subordinate to command-plan. If this Tests section conflicts with command-plan, command-plan is authoritative.
- Closeout may run only if command-plan authorizes it and the selected profile allows closeout.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not delete `project_state/codex_execution_report.md`.

Do not delete `project_state/gates/codex_report_auto_summary.json`.

Do not rename legacy Codex-named artifacts in this round.

Do not make `execution_report.md` the only supported report path in this round.

Do not make `execution_report_summary` the only supported summary block in this round.

Do not break parsing of legacy `codex_report_summary` blocks.

Do not break any existing audit workflow that still reads `project_state/codex_execution_report.md`.

Do not weaken report-summary, final-check, execution-log, closeout, required-command, Required Audit, archive, or generated_artifacts coverage to make neutral aliases pass.

Do not treat byte-for-byte identity as mandatory if the neutral report block name differs from the legacy block name; semantic parity of required fields is the acceptance criterion. If byte-for-byte mirrors are used, document that choice clearly.

Do not write dynamic findings into `.codex-skills/`.

Do not modify `project_state/artifact_index.json` in this round.

Do not broaden this round into Phase 2 GitHub CI, Web UI, AgentRunner, Codex adapter, Trae adapter, Job Manager, database, queue, scheduler, daemon, API Planner, API Auditor, self-hosted runner, or background worker work.

Do not continue `samplereverse` solving or any sample-solving task.

Do not read the full `solve_reports/` directory or full `PROJECT_PROGRESS_LOG.txt`.

Do not treat old sample artifacts or prior-round gate artifacts as current evidence.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Do not introduce a `medium` profile.

Do not use `COMPLETED_WITH_LIMITATIONS` as a report status.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message given to the executor.

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

Then inspect only relevant implementation and gate evidence files:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/codex_report_auto_summary.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/gate_profile_plan.json`
9. `project_state/gates/naming_migration_plan.json`
10. `project_state/gates/state_hygiene_inventory.json`
11. `project_state/gates/preflight_result.json`
12. `project_state/gates/policy_lint_result.json`
13. `project_state/gates/policy_impact_audit.json`
14. `project_state/gates/run_round_result.json`
15. `project_state/gates/run_closeout_result.json`
16. `project_state/gates/run_closeout_execution_log.json`
17. `project_state/gates/round_delta_summary.json`
18. `project_state/gates/round_close_snapshot.json` if present
19. `project_state/rounds/round_20260624_closeout_final_state_sync_rework_v1/round_manifest.json` only as bounded prior-round diagnostic evidence if needed
20. `project_state/rounds/round_20260624_closeout_final_state_sync_rework_v1/codex_execution_report.md` only as bounded prior-round diagnostic evidence if needed
21. `project_state/rounds/round_20260624_closeout_final_state_sync_rework_v1/pytest_result.txt` only as bounded prior-round diagnostic evidence if needed

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Which legacy report artifacts remain supported and generated, and how was backward compatibility verified?
2. Which neutral report alias artifacts are generated, and how are they related to the legacy artifacts?
3. How does the report parser support both `codex_report_summary` and `execution_report_summary` without breaking legacy reports?
4. How does final-check or report-summary verify semantic parity between legacy and neutral report summaries, including report_id, round_id, based_on_decision_id, status, acceptance_recommendation, files_changed, tests_ran, and generated_artifacts?
5. How are `codex_report_auto_summary.json` and `execution_report_auto_summary.json` kept consistent, and what fields are allowed to differ if any?
6. Which regression tests prove legacy-only reports still parse, neutral-only reports parse, dual reports detect drift, and legacy/neutral generated aliases stay semantically equivalent?
7. How were `execution_log_required_commands_recorded: PASS`, `state_hygiene_inventory_scope_complete: PASS`, report-summary PASS, final-check PASS, run-closeout PASS, and archive synchronization preserved?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no heavy artifact scan, no legacy deletion/rename, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Primary scope: add executor-neutral report alias compatibility while preserving legacy Codex-named artifacts.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/execution_report_auto_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/naming_migration_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/state_hygiene_inventory.json`
- `project_state/rounds/round_20260625_executor_neutral_report_alias_compat_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Introduce explicit legacy and neutral report path constants or equivalent centralized helpers.
3. Add parsing support for both legacy `codex_report_summary` blocks and neutral `execution_report_summary` blocks.
4. Preserve the current legacy `codex_execution_report.md` generation path.
5. Generate a neutral `project_state/execution_report.md` alias for the same current report.
6. Preserve `project_state/gates/codex_report_auto_summary.json` generation.
7. Generate `project_state/gates/execution_report_auto_summary.json` as a neutral auto-summary alias.
8. Add final-check or report-summary validation that compares legacy and neutral report summaries for semantic parity.
9. Add final-check or report-summary validation that compares legacy and neutral auto-summary JSON for semantic parity.
10. Ensure generated_artifacts and files_changed include both legacy and neutral artifacts when present.
11. Ensure report-summary still synthesizes the accepted status from live gate artifacts and does not accept a false SUCCESS.
12. Ensure closeout archives the appropriate current report evidence without breaking existing archive semantics. If only the legacy report is archived this round, document why; if both are archived, ensure manifest and generated_artifacts cover both.
13. Preserve `execution_log_required_commands_recorded: PASS` and `state_hygiene_inventory_scope_complete: PASS`.
14. Add focused tests for legacy report parsing, neutral report parsing, dual summary parity, dual summary drift detection, auto-summary alias parity, generated_artifact coverage, and full success path.
15. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `execution_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `run_closeout_result.json`, `run_closeout_execution_log.json`, `state_hygiene_inventory.json`, `codex_execution_report.md`, and `execution_report.md`.
16. Run closeout if and only if command-plan authorizes it.
17. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, report-summary `PASSED`, execution-log `PASSED`, report-auto-summary `PASSED`, run-closeout `PASSED`, legacy/neutral alias parity PASS, complete Required Audit, no active closeout warnings, and no blocking reasons.

Do not implement actual deletion of legacy artifacts, full migration cleanup, Phase 2, Web, CI, database, or multi-executor adapter in this round.

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

Generate and obey command-plan:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

After implementation, run only command-plan-authorized commands. If authorized, expected validation includes:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate naming-hygiene --state-dir project_state
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260625_executor_neutral_report_alias_compat_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260625_executor_neutral_report_alias_compat_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260625_executor_neutral_report_alias_compat_v1
python -m reverse_agent.project_gate naming-hygiene --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands in `project_state/pytest_result.txt`. Do not include nested closeout-internal command blocks in the top-level command stream. Record nested closeout command evidence in `project_state/gates/run_closeout_execution_log.json` or the existing scoped closeout evidence artifact.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- implementation requires modifying files outside allowed source scope;
- state updates require forbidden paths;
- implementation requires deleting or renaming legacy Codex-named report artifacts;
- implementation requires making neutral aliases the only supported path/block;
- implementation requires modifying prompt/skill files;
- implementation requires weakening command-plan authority, required-command recording, report-summary strictness, final-check strictness, closeout strictness, archive strictness, or Required Audit strictness;
- implementation requires accepting report alias drift as success;
- implementation requires accepting `COMPLETED_WITH_LIMITATIONS` as a report status;
- implementation requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, required command recording regresses, legacy `codex_execution_report.md` is not generated, neutral `execution_report.md` is not generated, legacy `codex_report_auto_summary.json` is not generated, neutral `execution_report_auto_summary.json` is not generated, legacy/neutral report summary parity fails, legacy/neutral auto-summary parity fails, legacy report parsing regresses, neutral report parsing fails, `codex_execution_report.md` is not `SUCCESS / ACCEPTED`, `pytest_result_summary.status` is not `PASSED`, Required Audit contains PENDING/placeholders, `execution_log.json.gate_status` is not `PASSED`, report-summary is not `PASSED`, final-check is not `PASSED`, run-closeout is not `PASSED`, policy-lint fails, policy-impact fails, `state_hygiene_inventory_scope_complete` is missing or not PASS, `execution_log_required_commands_recorded` is missing or not PASS, legacy artifacts are deleted/renamed, forbidden paths are mutated, final-check has warnings or blocking reasons, or the final report remains non-success for reasons other than a clearly documented real blocker.
