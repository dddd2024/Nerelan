```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260624_command_plan_execution_log_required_command_rework_v1",
  "round_id": "round_20260624_command_plan_execution_log_required_command_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260624_state_hygiene_archive_scope_rework_v1",
  "previous_round_id": "round_20260624_state_hygiene_archive_scope_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair command-plan, pytest_result, execution_log, report-auto-summary, report-summary, and final-check consistency so a required command missing from the actual execution log cannot be accepted as SUCCESS.",
  "command_plan_authority_required": true,
  "accepted_requires_required_commands_recorded": true,
  "accepted_requires_execution_log_passed": true,
  "accepted_requires_no_execution_log_warnings": true,
  "accepted_requires_report_tests_match_execution_log": true,
  "accepted_requires_report_auto_summary_no_synthetic_missing_commands": true,
  "accepted_requires_final_check_blocks_execution_log_warn": true,
  "accepted_requires_state_hygiene_inventory_scope_complete": true,
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
    "project_state/rounds/round_20260624_command_plan_execution_log_required_command_rework_v1/*"
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

Implement Command-Plan Execution-Log Required Command Rework v1.

The previous round fixed the original archive-scope blocker: `state_hygiene_inventory.json` now includes bounded archive entries for the current round, the previous naming-hygiene round, and the previous Phase 1 evidence-hardening round; those entries are classified as `round_archive_artifact` and have `safe_to_delete: false`. It also added a final-check rule named `state_hygiene_inventory_scope_complete`.

However, audit found a new blocker in the execution-record chain. `command_plan.json` required `python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_state_hygiene_archive_scope_rework_v1 --execute`, and `codex_execution_report.md` / `pytest_result.txt` summary claimed it was run. But the actual `pytest_result.txt` command blocks skipped from `run-round --dry-run --json` directly to pytest, and `execution_log.json` reported `gate_status: WARN` with a warning that this required command was not recorded. Despite that, final-check and report-summary accepted the report as `SUCCESS / ACCEPTED`.

This round must repair that consistency failure. A required command from command-plan that is absent from the actual command blocks or execution log must not be accepted as SUCCESS. `execution_log.json` must become a hard evidence gate for required command coverage. `report-auto-summary` must not synthesize a missing command into `tests_ran`. `final-check` must block `execution_log.gate_status == WARN` or non-empty execution-log warnings when those warnings indicate missing required commands.

This is still Phase 1.5 engineering hardening. Preserve the archive-scope fix and do not start naming migration, deletion, Phase 2 CI, Web UI, AgentRunner, database, queue, scheduler, or multi-executor implementation.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state and is not authoritative. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260624_state_hygiene_archive_scope_rework_v1`.

Accepted prior-round facts:

- `state_hygiene_inventory.json` contained `bounded_archive_dirs` for:
  - `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1`
  - `project_state/rounds/round_20260623_naming_hygiene_inventory_v1`
  - `project_state/rounds/round_20260623_phase1_completion_evidence_path_hardening_v1`
- Current-round archive entries were present for `codex_execution_report.md`, `decision_packet.md`, `pytest_result.txt`, and `round_manifest.json`.
- Previous naming-hygiene archive entries were present for `codex_execution_report.md`, `decision_packet.md`, `pytest_result.txt`, and `round_manifest.json`.
- Previous Phase 1 evidence-hardening archive entries were present for `codex_execution_report.md`, `decision_packet.md`, `pytest_result.txt`, and `round_manifest.json`.
- Archive entries were classified as `round_archive_artifact` and had `safe_to_delete: false`.
- final-check included `state_hygiene_inventory_scope_complete: PASS`.

Blocking prior-round facts:

- `command_plan.json` included required command `python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_state_hygiene_archive_scope_rework_v1 --execute`.
- `codex_execution_report.md.tests_ran` claimed that command was run.
- `pytest_result_summary.tests_ran` claimed that command was run.
- The actual `pytest_result.txt` command blocks did not contain that command.
- `execution_log.json` had `gate_status: WARN` and warning text that command-plan had one command not recorded in execution_log: the required `run-round --execute` command.
- final-check still reported `execution_log_consistency: PASS` and accepted the report as `SUCCESS / ACCEPTED`.
- `codex_report_auto_summary.json` listed `tests_ran_source: execution_log.json` while its `tests_ran` included the missing command, creating a provenance mismatch.

Artifact freshness:

- All proof for this rework must be regenerated under `decision_20260624_command_plan_execution_log_required_command_rework_v1` and `round_20260624_command_plan_execution_log_required_command_rework_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices only and must not be claimed as current evidence.

Existing capabilities to preserve:

- command-plan authority and omitted-command enforcement.
- startup command coverage checks.
- `command_plan_json_stdout_full`.
- report-summary synthesis.
- final-check status hardening.
- Phase 1 completion evidence-path checks.
- `state_hygiene_inventory_scope_complete` archive-scope check.
- naming-hygiene inventory-only behavior with no rename/delete/neutral live path creation.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round changes command logging, report-summary, and final-check semantics, command-plan should select or require `full` validation.
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

Do not weaken command-plan authority by treating required commands as optional.

Do not let `codex_execution_report.md.tests_ran`, `pytest_result_summary.tests_ran`, `codex_report_auto_summary.json.summary.tests_ran`, or `report_summary_synthesis.json.synthesized_summary.tests_ran` contain commands that are absent from the actual top-level `pytest_result.txt` command blocks unless there is an explicit, current, structured nested-evidence field and final-check understands the distinction.

Do not let `execution_log.json` remain `WARN` for missing required command coverage while final-check passes.

Do not hide missing required commands by inserting them into report-summary without actual command-block evidence.

Do not inject closeout-internal commands into the top-level command stream. Nested closeout commands must remain scoped in `run_closeout_execution_log.json` or equivalent closeout evidence.

Do not broaden this round into naming migration, compatibility dual-write, Phase 2 GitHub CI, `ci.yml`, `state-gate.yml`, PR automation, branch protection, Web UI, AgentRunner, Codex adapter, Trae adapter, Job Manager, database, queue, scheduler, daemon, API Planner, API Auditor, self-hosted runner, or background worker work.

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
19. `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/round_manifest.json` only as bounded prior-round diagnostic evidence
20. `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/codex_execution_report.md` only as bounded prior-round diagnostic evidence
21. `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/pytest_result.txt` only as bounded prior-round diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Which required command was missing in the previous round, and how does the new logic detect required command absence from actual `pytest_result.txt` command blocks?
2. How does `execution_log.json` now treat command-plan required commands missing from actual command blocks: `PASSED`, `WARN`, or `FAILED`? Why is that status acceptable?
3. How does final-check now block `execution_log.gate_status == WARN` or `FAILED` when warnings/errors involve missing required command coverage?
4. How does report-auto-summary ensure it does not synthesize a command into `tests_ran` if that command is absent from `execution_log.commands` or actual `pytest_result.txt` command blocks?
5. How do `codex_execution_report.md`, `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, and `report_summary_synthesis.json` now agree on `tests_ran`?
6. Which regression tests prove missing required commands fail execution-log/final-check/report-summary, and that truly recorded `run-round --execute` passes?
7. How was `state_hygiene_inventory_scope_complete` preserved as PASS while fixing the execution-log/report-summary issue?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no heavy artifact scan, no rename/delete/neutral live path creation, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, or speculative answers.

## 6. Implementation Scope

Primary scope: enforce required command coverage from command-plan through pytest_result, execution_log, report-auto-summary, report-summary, and final-check.

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
- `project_state/rounds/round_20260624_command_plan_execution_log_required_command_rework_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Inspect how `pytest_result.txt` command blocks are parsed and how `tests_ran` summary is derived.
3. Inspect how `execution_log.json` compares command-plan commands against actual command blocks.
4. Treat any command-plan command with `required: true` and not recorded in actual top-level command blocks as a blocking execution-log failure, unless it is explicitly a nested closeout-internal command represented by a scoped closeout artifact.
5. Do not allow a missing required top-level command to remain a mere warning if the report claims `SUCCESS / ACCEPTED`.
6. Ensure `report-auto-summary` derives `tests_ran` from actual recorded command evidence, not from command-plan alone.
7. Ensure `report-summary` detects mismatches among live report summary, auto-summary, pytest_result summary, and execution_log command records.
8. Ensure final-check fails if `execution_log.json.gate_status` is `WARN` or `FAILED` for missing required command coverage, or if `execution_log.json.warnings` includes missing required commands.
9. Ensure a correctly recorded `run-round --execute` command appears in actual command blocks, execution_log, report-auto-summary, report-summary, and live report `tests_ran`.
10. Preserve `state_hygiene_inventory_scope_complete: PASS` and archive entries as `round_archive_artifact` with `safe_to_delete: false`.
11. Preserve naming-hygiene inventory-only behavior: no rename, no delete, no neutral live report path creation.
12. Add focused regression tests for missing required command failure, execution-log WARN blocking, report-auto-summary no synthetic command insertion, report-summary tests_ran consistency, and success when `run-round --execute` is truly recorded.
13. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `state_hygiene_inventory.json`, and `codex_execution_report.md`.
14. Run closeout if and only if command-plan authorizes it.
15. Final accepted report must be `SUCCESS / ACCEPTED` with `execution_log.json.gate_status: PASSED`, no execution-log warnings, final-check `PASSED`, report-summary `PASSED`, report-auto-summary `PASSED`, `state_hygiene_inventory_scope_complete: PASS`, run-closeout `PASSED`, and no blocking reasons.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_command_plan_execution_log_required_command_rework_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_command_plan_execution_log_required_command_rework_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260624_command_plan_execution_log_required_command_rework_v1
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
- implementation requires renaming live report paths;
- implementation requires deleting files;
- implementation requires creating new neutral live report paths;
- implementation requires modifying prompt/skill files;
- implementation requires weakening command-plan authority;
- implementation requires accepting missing required commands as warnings in a SUCCESS report;
- implementation requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, any required command is missing from actual command blocks without scoped nested evidence, `execution_log.json.gate_status` is `WARN` or `FAILED`, execution-log warnings are non-empty for required command coverage, report-auto-summary invents missing commands, report-summary tolerates tests_ran divergence, final-check does not block execution-log warnings, policy-lint fails, policy-impact fails, `state_hygiene_inventory_scope_complete` is missing or not PASS, inventory artifacts are absent from generated_artifacts, any file is renamed, any file is deleted, any neutral live report path is created, any forbidden path is mutated, run-closeout fails, final-check has warnings or blocking reasons, or the final report remains `PARTIAL / NEEDS_REVIEW` for reasons other than a clearly documented real blocker.
