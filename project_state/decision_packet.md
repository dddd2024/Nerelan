```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260623_naming_hygiene_inventory_v1",
  "round_id": "round_20260623_naming_hygiene_inventory_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260623_phase1_completion_evidence_path_hardening_v1",
  "previous_round_id": "round_20260623_phase1_completion_evidence_path_hardening_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Create a bounded naming-neutralization and project_state hygiene inventory before Phase 2, without renaming, deleting, or migrating live artifacts in this round.",
  "command_plan_authority_required": true,
  "accepted_requires_naming_migration_plan": true,
  "accepted_requires_state_hygiene_inventory": true,
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
    "project_state/rounds/round_20260623_naming_hygiene_inventory_v1/*"
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

Implement Naming Hygiene Inventory v1 as the first Phase 1.5 pre-Phase-2 cleanup round.

The previous accepted round closed Phase 1 completion evidence-path hardening. Phase 1 local gate foundations are now acceptable: command-plan authority, execution-log, report-auto-summary, report-summary, final-check, run-round, run-closeout, and Phase 1 completion evidence checks have current structured evidence.

This round must not change live names yet. It must produce a bounded, structured inventory and migration plan for names and state files that will otherwise create confusion in Phase 2. The immediate problem is that some live artifact names still bind the system to Codex even though Phase 2 may introduce other executors such as a local runner, GitHub Actions, Trae, a future AgentRunner, or a Web-triggered executor.

Required outputs:

1. `project_state/gates/naming_migration_plan.json`
2. `project_state/gates/state_hygiene_inventory.json`

`naming_migration_plan.json` must identify executor-specific naming debt, especially Codex-bound names such as `codex_execution_report.md`, `codex_report_summary`, and `codex_report_auto_summary.json`, and propose neutral target names such as `execution_report.md`, `execution_report_summary`, and `execution_report_auto_summary.json`. It must explicitly mark this round as inventory-only and must not perform the migration.

`state_hygiene_inventory.json` must classify bounded state files as one of:

- `current_live_artifact`
- `round_archive_artifact`
- `legacy_compat_artifact`
- `candidate_legacy_artifact`
- `candidate_orphan_artifact`
- `unknown_requires_manual_review`

No file may be deleted in this round. No live artifact may be renamed in this round. No new neutral live report path may be created in this round.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state and is not authoritative. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `ACCEPTED` for `decision_20260623_phase1_completion_evidence_path_hardening_v1`.

Accepted prior-round facts:

- `codex_execution_report.md` reached `SUCCESS / ACCEPTED` for `round_20260623_phase1_completion_evidence_path_hardening_v1`.
- `pytest_result.txt` reached `PASSED`, with `tests/test_project_gate.py` and `tests/test_project_gate.py tests/test_project_state.py` passing.
- `command-plan --json` recorded a full commands array and `omitted_commands=[]`.
- `phase1_completion_result.json` no longer references missing `execute_decision_result.json`; `execute_decision_entrypoint` uses current existing evidence paths: `execution_log.json`, `command_plan.json`, and `run_round_result.json`.
- final-check reached `PASSED` and included `phase1_completion_evidence_paths_exist: PASS` and `phase1_completion_evidence_paths_reported: PASS`.
- `report_summary_synthesis.json` reached `PASSED` with no diffs and synthesized `SUCCESS / ACCEPTED`.
- `run_closeout_result.json` reached `PASSED` and round manifest reached `SUCCESS / ACCEPTED`.

Known naming debt:

- `project_state/codex_execution_report.md` is currently the live execution report path, but the concept is executor-neutral.
- `codex_report_summary` is currently the report summary block name, but the concept is executor-neutral.
- `project_state/gates/codex_report_auto_summary.json` is currently the report-auto-summary gate artifact, but the concept is executor-neutral.
- These names are acceptable for backward compatibility today but should not be carried unexamined into Phase 2 multi-executor or Web/CI integration.

Artifact freshness:

- All evidence for this round must be regenerated under `decision_20260623_naming_hygiene_inventory_v1` and `round_20260623_naming_hygiene_inventory_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices only and must not be claimed as current evidence.

Scope of inventory:

- Inspect only live state roots and bounded current artifacts: `project_state/*.json`, `project_state/*.md`, `project_state/*.txt`, `project_state/gates/*.json`, and the current/previous round manifest/report files explicitly listed in Files To Inspect.
- Do not recursively scan the full `project_state/rounds/` tree.
- Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round changes gate logic and may add a new inventory command/artifact, command-plan should select or require `full` validation.
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

Do not remove legacy Codex-named files in this round.

Do not modify `project_state/artifact_index.json` in this round.

Do not write dynamic findings into `.codex-skills/`.

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
9. `project_state/gates/phase1_completion_result.json`
10. `project_state/gates/preflight_result.json`
11. `project_state/gates/policy_lint_result.json`
12. `project_state/gates/policy_impact_audit.json`
13. `project_state/gates/run_round_result.json`
14. `project_state/gates/run_closeout_result.json`
15. `project_state/gates/run_closeout_execution_log.json`
16. `project_state/gates/round_delta_summary.json`
17. `project_state/gates/round_close_snapshot.json` if present
18. `project_state/gates/naming_migration_plan.json` if present
19. `project_state/gates/state_hygiene_inventory.json` if present
20. `project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1/round_manifest.json` only as bounded prior-round diagnostic evidence
21. `project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1/codex_execution_report.md` only as bounded prior-round diagnostic evidence

For inventory generation, inspect only bounded live directories:

- `project_state/` immediate files
- `project_state/gates/` immediate JSON files
- the current round archive directory after closeout
- the previous accepted round archive directory listed above

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Which Codex-bound names were found in live report paths, JSON block names, gate artifact names, code constants, tests, and generated artifacts? Which are true executor-neutral naming debt versus acceptable legacy references?
2. What does `project_state/gates/naming_migration_plan.json` contain, and how does it distinguish inventory-only recommendations from actual migration actions?
3. What neutral target names are proposed for `codex_execution_report.md`, `codex_report_summary`, and `codex_report_auto_summary.json`, and what compatibility strategy is recommended for a later round?
4. What does `project_state/gates/state_hygiene_inventory.json` contain, and how are files classified as `current_live_artifact`, `round_archive_artifact`, `legacy_compat_artifact`, `candidate_legacy_artifact`, `candidate_orphan_artifact`, or `unknown_requires_manual_review`?
5. How does the inventory prove that no file was renamed, no file was deleted, no neutral live report path was created, and no forbidden path was mutated?
6. How does the implementation prevent `candidate_orphan_artifact` or `candidate_legacy_artifact` from being treated as safe-to-delete in this round?
7. Which regression tests cover naming inventory generation, state hygiene classification, no-delete/no-rename enforcement, generated artifact coverage, and preservation of existing final-check/report-summary behavior?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no heavy artifact scan, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, or speculative answers.

## 6. Implementation Scope

Primary scope: add bounded naming and state-hygiene inventory generation for Phase 1.5.

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
- `project_state/rounds/round_20260623_naming_hygiene_inventory_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Add or reuse a bounded CLI/gate command such as `naming-hygiene` or an equivalent project-gate command to generate `naming_migration_plan.json` and `state_hygiene_inventory.json`.
3. Inventory Codex-bound names in live report paths, JSON block names, gate artifact names, code/test references, and generated artifact names.
4. Classify each Codex-bound name as `must_keep_current_compat`, `candidate_neutralization`, `archive_only_reference`, or `unknown_requires_manual_review`.
5. Propose neutral target names but do not create those target files.
6. Build a bounded state file inventory covering only live root state files, live gate JSON files, and explicitly allowed current/previous round archive files.
7. Classify each inventoried state path into one of the approved categories.
8. Set `safe_to_delete` to `false` for every entry in this round, including candidate orphan and candidate legacy entries. Deletion is explicitly deferred.
9. Include fields such as `path`, `category`, `referenced_by`, `freshness_basis`, `safe_to_delete`, `delete_reason`, `migration_target`, and `notes` where applicable.
10. Ensure the new inventory artifacts are included in `generated_artifacts` and covered by final-check/generated_artifacts checks.
11. Add focused regression tests for naming migration plan generation, state hygiene inventory generation, bounded scan behavior, no-delete/no-rename behavior, and report/final-check integration.
12. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `naming_migration_plan.json`, `state_hygiene_inventory.json`, and `codex_execution_report.md`.
13. Run closeout if and only if command-plan authorizes it.
14. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, naming migration plan present, state hygiene inventory present, report-summary `PASSED`, execution-log `PASSED`, report-auto-summary `PASSED`, run-closeout `PASSED`, and no blocking reasons.

Do not implement actual migration, rename, deletion, compatibility dual-write, schema migration, Phase 2, Web, CI, database, or multi-executor adapter in this round.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260623_naming_hygiene_inventory_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260623_naming_hygiene_inventory_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260623_naming_hygiene_inventory_v1
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
- implementation requires weakening command-plan authority, execution-log consistency, archive strictness, report-summary consistency, report-auto-summary consistency, final-check strictness, generated_artifacts coverage, or Required Audit coverage;
- inventory generation would require full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full recursive `project_state/rounds/` scans;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, execution-log regresses, report-auto-summary regresses, report-summary regresses, policy-lint fails, policy-impact fails, `naming_migration_plan.json` is missing, `state_hygiene_inventory.json` is missing, inventory artifacts are absent from generated_artifacts, any file is renamed, any file is deleted, any neutral live report path is created, any forbidden path is mutated, any candidate artifact is marked safe-to-delete in this round, run-closeout fails, final-check has warnings or blocking reasons, or the final report remains `PARTIAL / NEEDS_REVIEW` for reasons other than a clearly documented real blocker.
