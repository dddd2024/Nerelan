```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260624_state_hygiene_archive_scope_rework_v1",
  "round_id": "round_20260624_state_hygiene_archive_scope_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260623_naming_hygiene_inventory_v1",
  "previous_round_id": "round_20260623_naming_hygiene_inventory_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair state_hygiene_inventory archive-scope coverage by adding bounded current-round and previous-accepted-round archive entries, without renaming, deleting, migrating, or entering Phase 2.",
  "command_plan_authority_required": true,
  "accepted_requires_state_hygiene_inventory": true,
  "accepted_requires_archive_scope_complete": true,
  "accepted_requires_current_round_archive_entries": true,
  "accepted_requires_previous_accepted_round_archive_entries": true,
  "accepted_requires_round_archive_artifact_category": true,
  "accepted_requires_archive_entries_safe_to_delete_false": true,
  "accepted_requires_no_full_rounds_scan": true,
  "accepted_requires_no_rename": true,
  "accepted_requires_no_delete": true,
  "accepted_requires_no_phase2_scope": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_report_status_success": true,
  "accepted_requires_report_acceptance_accepted": true,
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
    "project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/*"
  ],
  "bounded_archive_dirs_to_inventory": [
    "project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1",
    "project_state/rounds/round_20260623_naming_hygiene_inventory_v1",
    "project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/README.md",
    "project_state/execution_report.md",
    "project_state/gates/execution_report_auto_summary.json"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement State Hygiene Archive Scope Rework v1.

The previous Phase 1.5 inventory round generated `project_state/gates/naming_migration_plan.json` and `project_state/gates/state_hygiene_inventory.json`, preserved inventory-only behavior, and did not rename or delete files. However, audit found one blocking issue: `state_hygiene_inventory.json` covered only live root/gate state files and did not include the bounded archive directories that the decision explicitly required.

This round must repair only that scope gap. Extend `state_hygiene_inventory.json` so it includes bounded archive entries from:

1. the current round archive directory after closeout: `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/*`;
2. the previous reworked inventory round: `project_state/rounds/round_20260623_naming_hygiene_inventory_v1/*`;
3. the previous accepted Phase 1 evidence hardening round: `project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1/*`.

These archive entries must be classified as `round_archive_artifact`, must have `safe_to_delete: false`, and must not trigger any deletion or migration.

This is still Phase 1.5 inventory work. Do not perform naming migration, compatibility dual-write, live artifact rename, deletion, cleanup, Phase 2 CI, Web UI, AgentRunner, database, queue, scheduler, or multi-executor implementation.

Required accepted outputs:

1. `project_state/gates/state_hygiene_inventory.json` with complete bounded archive coverage.
2. `project_state/gates/naming_migration_plan.json` preserved or regenerated as inventory-only evidence if needed.
3. final-check coverage proving archive scope completeness.
4. `project_state/codex_execution_report.md` with all Required Audit items answered.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state and is not authoritative. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260623_naming_hygiene_inventory_v1`.

Accepted prior-round facts:

- `naming_migration_plan.json` existed, carried current decision/round IDs, and correctly marked `action_this_round: inventory_only`, `no_rename: true`, `no_delete: true`, and `no_neutral_live_path_created: true`.
- `naming_migration_plan.json` identified the main Codex-bound names and proposed neutral targets without performing migration.
- `state_hygiene_inventory.json` existed and included live root/gate inventory entries.
- All inspected inventory entries had `safe_to_delete: false`.
- No evidence showed actual rename, deletion, or creation of `project_state/execution_report.md` or `project_state/gates/execution_report_auto_summary.json`.
- command-plan, pytest, naming-hygiene, execution-log, report-auto-summary, report-summary, final-check, and run-closeout passed in the previous inventory round.

Blocking prior-round facts:

- The previous decision required inventory generation to inspect bounded live directories plus the current round archive directory and previous accepted round archive directory.
- The previous report stated `state_hygiene_inventory.json` contained entries across `project_state/` immediate files and `project_state/gates/` immediate JSON files only.
- The previous report stated no `round_archive_artifact` entries appeared because the scan was bounded to live state roots only.
- Current and previous accepted archive manifests exist and list archive files such as `codex_execution_report.md`, `decision_packet.md`, and `pytest_result.txt` under their round directories.
- final-check did not detect the missing bounded archive inventory scope.

Artifact freshness:

- All proof for this rework must be regenerated under `decision_20260624_state_hygiene_archive_scope_rework_v1` and `round_20260624_state_hygiene_archive_scope_rework_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices only and must not be claimed as current evidence.

Scope of archive inventory:

- Read only the three explicitly bounded archive directories listed in `decision_contract.bounded_archive_dirs_to_inventory`.
- Do not recursively scan the full `project_state/rounds/` tree.
- Archive scope is file-level inventory of known round archive files, not semantic validation of every archived report.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round changes gate logic and final-check coverage, command-plan should select or require `full` validation.
- Tests are subordinate to command-plan. If this Tests section conflicts with command-plan, command-plan is authoritative.
- Closeout may run only if command-plan authorizes it and the selected profile allows closeout.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not rename any live artifact in this round.

Do not create `project_state/execution_report.md` in this round.

Do not create `project_state/gates/execution_report_auto_summary.json` in this round.

Do not delete files in this round.

Do not mark any `round_archive_artifact`, `candidate_orphan_artifact`, `candidate_legacy_artifact`, `legacy_compat_artifact`, or `unknown_requires_manual_review` entry as safe-to-delete.

Do not remove legacy Codex-named files in this round.

Do not modify `project_state/artifact_index.json` in this round.

Do not write dynamic findings into `.codex-skills/`.

Do not scan full `project_state/rounds/`. Only inspect the bounded archive directories explicitly listed in this decision.

Do not broaden this round into Phase 2 GitHub CI, `ci.yml`, `state-gate.yml`, PR automation, branch protection, Web UI, AgentRunner, Codex adapter, Trae adapter, Job Manager, database, queue, scheduler, daemon, API Planner, API Auditor, self-hosted runner, or background worker work.

Do not continue `samplereverse` solving or any sample-solving task.

Do not read the full `solve_reports/` directory or full `PROJECT_PROGRESS_LOG.txt`.

Do not treat old sample artifacts or prior-round gate artifacts as current evidence.

Do not weaken command-plan authority, execution-log consistency, report-auto-summary consistency, report-summary consistency, final-check strictness, archive strictness, run-closeout evidence scoping, generated_artifacts coverage, Required Audit coverage, or Phase 1 completion evidence-path checks.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`
- `project_state/execution_report.md`
- `project_state/gates/execution_report_auto_summary.json`

Do not introduce a `medium` profile.

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
19. `project_state/rounds/round_20260623_naming_hygiene_inventory_v1/round_manifest.json`
20. `project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1/round_manifest.json`

For archive inventory generation, inspect only these bounded archive directories:

1. `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/` after closeout, if it exists at that point;
2. `project_state/rounds/round_20260623_naming_hygiene_inventory_v1/`;
3. `project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1/`.

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Which archive directories were required by this decision, and which exact files from each were added to `state_hygiene_inventory.json`?
2. How does `state_hygiene_inventory.json` classify current-round, previous inventory-round, and previous accepted Phase 1 evidence-hardening round archive files as `round_archive_artifact`?
3. How does the implementation guarantee every archive entry has `safe_to_delete: false` and a delete reason that deletion is deferred?
4. How does the implementation prove it scanned only the bounded archive directories and did not recursively scan the full `project_state/rounds/` tree?
5. What final-check rule now verifies archive scope completeness, and how does it fail if any required bounded archive file is missing from the inventory?
6. Which regression tests prove current-round archive files and previous accepted round archive files are inventoried, classified correctly, safe-to-delete false, and bounded-scan only?
7. How were existing naming hygiene guarantees preserved: no rename, no delete, no neutral live report path creation, no forbidden path mutation, and no safe-to-delete candidates?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no heavy artifact scan, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, or speculative answers.

## 6. Implementation Scope

Primary scope: repair archive-scope coverage in state hygiene inventory and add final-check/test enforcement.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/codex_report_auto_summary.json`
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
- `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Extend the naming-hygiene/state-hygiene implementation so `state_hygiene_inventory.json` includes archive entries from the explicitly bounded directories only.
3. Add archive entries for the previous inventory round archive directory: `project_state/rounds/round_20260623_naming_hygiene_inventory_v1/*`.
4. Add archive entries for the previous accepted Phase 1 evidence-hardening round archive directory: `project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1/*`.
5. Ensure the current rework round archive directory is included after closeout or explain the exact sequencing used to regenerate/validate inventory after archive creation. The accepted final state must include current round archive entries if the directory exists.
6. Classify all bounded archive entries as `round_archive_artifact`.
7. Set `safe_to_delete: false` for all archive entries.
8. Include `referenced_by`, `freshness_basis`, `delete_reason`, and `notes` for each archive entry.
9. Add or harden final-check validation, preferably named `state_hygiene_inventory_scope_complete`, that verifies required bounded archive files are present in `state_hygiene_inventory.json` and classified correctly.
10. Ensure this check fails if the archive scope is missing or incomplete.
11. Add focused regression tests for archive inventory coverage, category assignment, safe-to-delete false, bounded scan behavior, and final-check blocking behavior.
12. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `state_hygiene_inventory.json`, and `codex_execution_report.md`.
13. Run closeout if and only if command-plan authorizes it.
14. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, `state_hygiene_inventory_scope_complete: PASS`, report-summary `PASSED`, execution-log `PASSED`, report-auto-summary `PASSED`, run-closeout `PASSED`, and no blocking reasons.

Do not implement actual naming migration, rename, deletion, compatibility dual-write, schema migration, Phase 2, Web, CI, database, or multi-executor adapter in this round.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_state_hygiene_archive_scope_rework_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_state_hygiene_archive_scope_rework_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260624_state_hygiene_archive_scope_rework_v1
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
- the fix requires modifying files outside allowed source scope;
- state updates require forbidden paths;
- implementation requires renaming live report paths;
- implementation requires deleting files;
- implementation requires creating new neutral live report paths;
- implementation requires modifying prompt/skill files;
- implementation requires scanning full `project_state/rounds/` instead of the explicit bounded archive dirs;
- implementation requires weakening command-plan authority, execution-log consistency, archive strictness, report-summary consistency, report-auto-summary consistency, final-check strictness, generated_artifacts coverage, or Required Audit coverage;
- inventory generation would require full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full recursive `project_state/rounds/` scans;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, execution-log regresses, report-auto-summary regresses, report-summary regresses, policy-lint fails, policy-impact fails, `state_hygiene_inventory.json` is missing, required archive entries are missing, archive entries are not classified as `round_archive_artifact`, any archive entry has `safe_to_delete: true`, bounded-scan proof is missing, `state_hygiene_inventory_scope_complete` is missing or not PASS, inventory artifacts are absent from generated_artifacts, any file is renamed, any file is deleted, any neutral live report path is created, any forbidden path is mutated, run-closeout fails, final-check has warnings or blocking reasons, or the final report remains `PARTIAL / NEEDS_REVIEW` for reasons other than a clearly documented real blocker.
