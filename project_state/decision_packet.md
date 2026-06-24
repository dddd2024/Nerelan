```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260624_closeout_transient_warning_normalization_v1",
  "round_id": "round_20260624_closeout_transient_warning_normalization_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260624_report_closeout_summary_consistency_rework_v1",
  "previous_round_id": "round_20260624_report_closeout_summary_consistency_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Normalize run-closeout transient pre-archive warning reporting so a resolved pre-archive report-summary/archive drift is scoped as diagnostic history rather than an active closeout warning, without weakening final-check/report-summary/closeout gates.",
  "command_plan_authority_required": true,
  "accepted_requires_report_status_success": true,
  "accepted_requires_report_acceptance_accepted": true,
  "accepted_requires_required_audit_complete": true,
  "accepted_requires_pytest_result_passed": true,
  "accepted_requires_execution_log_passed": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_no_active_closeout_warnings": true,
  "accepted_requires_pre_archive_transient_warnings_scoped": true,
  "accepted_requires_final_check_after_archive_passed": true,
  "accepted_requires_report_summary_fields_match_synthesis_passed_in_final_state": true,
  "accepted_requires_required_commands_recorded": true,
  "accepted_requires_state_hygiene_inventory_scope_complete": true,
  "accepted_requires_no_rename": true,
  "accepted_requires_no_delete": true,
  "accepted_requires_no_phase2_scope": true,
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
    "project_state/rounds/round_20260624_closeout_transient_warning_normalization_v1/*"
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

Implement Closeout Transient Warning Normalization v1.

The previous round closed the main report/pytest/final-check/closeout consistency gap and was accepted with limitations. Its final live state was coherent: `codex_execution_report.md` was `SUCCESS / ACCEPTED`, Required Audit was complete, `pytest_result.txt` was `PASSED`, `execution_log.json` was `PASSED`, `report_summary_synthesis.json` was `PASSED`, `final_gate_result.json` was `PASSED`, `run_closeout_result.json.closeout_status` was `PASSED`, and the round manifest was `SUCCESS / ACCEPTED`.

The remaining limitation is narrow: `project_state/gates/run_closeout_result.json` kept a pre-archive diagnostic warning inside `close_round_result.warnings` for `report_summary_fields_match_synthesis` even though the final post-archive check passed and the live final-check/report-summary state had no active warnings. This creates audit noise: a resolved, transient pre-archive report-summary/archive drift appears indistinguishable from an active closeout warning unless the auditor reads the later `final_check_after_archive` action.

This round must normalize that representation. A resolved pre-archive drift may be retained as structured diagnostic history, but it must be explicitly scoped as pre-archive/transient/resolved and must not remain as an active warning in accepted closeout evidence. The final accepted state must have no active closeout warnings, `final_check_after_archive: PASSED`, final `report_summary_fields_match_synthesis: PASS`, and `run_closeout_result.json` must make it mechanically clear that the final state is clean.

This is a Phase 1.5 closeout/reporting cleanup. Do not perform naming migration, file deletion, neutral report path creation, Phase 2 CI/Web/AgentRunner/database work, or sample solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state and is not authoritative. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `ACCEPTED_WITH_LIMITATIONS` for `decision_20260624_report_closeout_summary_consistency_rework_v1`.

Accepted prior-round facts:

- `codex_execution_report.md` reached `SUCCESS / ACCEPTED`.
- all eight Required Audit items were substantive and `PASS`, with no `PENDING`, `TODO`, `TBD`, or `(to be filled)` placeholder answers.
- `pytest_result_summary.status` reached `PASSED`.
- core tests passed: `tests/test_project_gate.py` and `tests/test_project_gate.py tests/test_project_state.py`.
- `execution_log.json.gate_status` reached `PASSED`, with no warnings and no blocking reasons.
- required command coverage was preserved; `run-round --execute` and `run-closeout` were recorded and passed.
- `report_summary_synthesis.json.synthesis_status` reached `PASSED` with no diffs/errors/warnings.
- `final_gate_result.json.gate_status` reached `PASSED`, with no warnings or blocking reasons.
- `run_closeout_result.json.closeout_status` reached `PASSED`.
- the round manifest reached `SUCCESS / ACCEPTED`.

Accepted-with-limitations fact:

- `run_closeout_result.json.close_round_result.warnings` still carried a warning for `report_summary_fields_match_synthesis: codex_report_summary differs from synthesized summary` from the pre-archive closeout phase.
- the same `run_closeout_result.json` also recorded `final_check_after_archive` as `PASSED` with `gate_status: PASSED`, so the warning was a resolved pre-archive diagnostic, not an active final-state blocker.
- this ambiguity should be cleaned before moving into naming migration or Phase 2.

Artifact freshness:

- All proof for this round must be regenerated under `decision_20260624_closeout_transient_warning_normalization_v1` and `round_20260624_closeout_transient_warning_normalization_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices only and must not be claimed as current evidence.

Existing capabilities to preserve:

- command-plan authority and omitted-command enforcement.
- required-command recording enforcement.
- `execution_log_required_commands_recorded`.
- report-auto-summary no synthetic missing command insertion.
- report-summary synthesis and final-check strictness.
- Required Audit placeholder blocking.
- Phase 1 completion evidence-path checks.
- `state_hygiene_inventory_scope_complete` archive-scope check.
- naming-hygiene inventory-only behavior with no rename/delete/neutral live path creation.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round touches closeout result semantics and final accepted evidence, command-plan should select or require `full` validation.
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

Do not hide real closeout failures by relabeling them as transient. Only report-summary/archive drift that is demonstrably resolved by `final_check_after_archive: PASSED` may be marked resolved/transient.

Do not remove diagnostics entirely if doing so weakens auditability. Prefer preserving pre-archive diagnostics in a scoped field such as `pre_archive_diagnostics`, `resolved_pre_archive_warnings`, or an equivalent structured field that is explicitly non-final.

Do not accept final output if `run_closeout_result.json` has active top-level warnings, active `close_round_result.warnings`, or ambiguous warning fields that are not marked resolved and pre-archive scoped.

Do not accept final output if `final_check_after_archive` is missing, not PASSED, or has a final gate status other than PASSED.

Do not accept final output if final `report_summary_fields_match_synthesis` is WARN/FAILED.

Do not use `COMPLETED_WITH_LIMITATIONS` as a report status. Supported report status values remain `SUCCESS`, `PARTIAL`, `FAILED`, and `BLOCKED`.

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
19. `project_state/rounds/round_20260624_report_closeout_summary_consistency_rework_v1/round_manifest.json` only as bounded prior-round diagnostic evidence
20. `project_state/rounds/round_20260624_report_closeout_summary_consistency_rework_v1/codex_execution_report.md` only as bounded prior-round diagnostic evidence
21. `project_state/rounds/round_20260624_report_closeout_summary_consistency_rework_v1/pytest_result.txt` only as bounded prior-round diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. What exact pre-archive warning caused the previous `ACCEPTED_WITH_LIMITATIONS`, where was it stored, and why was it transient rather than an active final-state blocker?
2. How does `run_closeout_result.json` now represent pre-archive diagnostics separately from active final closeout warnings?
3. How does the implementation prove that final accepted output has no active top-level closeout warnings, no active `close_round_result.warnings`, and no ambiguous resolved warning fields?
4. How does the implementation prove `final_check_after_archive` is present, PASSED, and has final gate status PASSED?
5. How does final-check/report-summary prove final `report_summary_fields_match_synthesis` is PASS, with no diffs/errors/warnings in the final live state?
6. Which regression tests cover transient pre-archive warning normalization, real unresolved closeout warning blocking, final-check-after-archive enforcement, and no evidence weakening?
7. How were `execution_log_required_commands_recorded: PASS`, `state_hygiene_inventory_scope_complete: PASS`, Required Audit completeness, and report `SUCCESS / ACCEPTED` preserved?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no heavy artifact scan, no rename/delete/neutral live path creation, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Primary scope: normalize closeout result semantics so resolved pre-archive warnings are clearly diagnostic/transient and do not appear as active accepted-state warnings.

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
- `project_state/rounds/round_20260624_closeout_transient_warning_normalization_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Inspect run-closeout and close-round result construction.
3. Distinguish pre-archive diagnostics from final closeout warnings in `run_closeout_result.json`.
4. If a pre-archive `report_summary_fields_match_synthesis` drift is resolved by successful archive and post-archive final-check, move or label it as resolved pre-archive diagnostic evidence, not an active warning.
5. Preserve active warnings for real unresolved closeout/final-check/report-summary failures.
6. Ensure accepted output has `run_closeout_result.json.closeout_status: PASSED`, top-level `warnings: []`, `blocking_reasons: []`, and no active `close_round_result.warnings` that represent resolved pre-archive drift.
7. Ensure `final_check_after_archive` action is present, `status: PASSED`, and `gate_status: PASSED`.
8. Ensure live `final_gate_result.json.gate_status: PASSED` and live `report_summary_synthesis.json.synthesis_status: PASSED` with no diffs/errors/warnings.
9. Add or harden final-check coverage so ambiguous accepted-state closeout warnings are caught.
10. Add focused tests for: resolved pre-archive warning scoping, unresolved closeout warning blocking, missing/failing `final_check_after_archive` blocking, and no change to hard failures.
11. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `run_closeout_result.json`, `run_closeout_execution_log.json`, and `codex_execution_report.md`.
12. Run closeout if and only if command-plan authorizes it.
13. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, report-summary `PASSED`, execution-log `PASSED`, report-auto-summary `PASSED`, run-closeout `PASSED`, complete Required Audit, no active closeout warnings, and no blocking reasons.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_closeout_transient_warning_normalization_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_closeout_transient_warning_normalization_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260624_closeout_transient_warning_normalization_v1
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
- implementation requires weakening command-plan authority, required-command recording, report-summary strictness, final-check strictness, closeout strictness, or Required Audit strictness;
- implementation requires hiding real unresolved closeout warnings as transient/resolved;
- implementation requires accepting `COMPLETED_WITH_LIMITATIONS` as a report status;
- implementation requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, required command recording regresses, `codex_execution_report.md` is not `SUCCESS / ACCEPTED`, `pytest_result_summary.status` is not `PASSED`, Required Audit contains PENDING/placeholders, `execution_log.json.gate_status` is not `PASSED`, report-summary is not `PASSED`, final-check is not `PASSED`, run-closeout is not `PASSED`, top-level closeout warnings are non-empty, resolved pre-archive warnings remain ambiguous active warnings, `final_check_after_archive` is missing or not PASSED, final report-summary has diffs/errors/warnings, policy-lint fails, policy-impact fails, `state_hygiene_inventory_scope_complete` is missing or not PASS, `execution_log_required_commands_recorded` is missing or not PASS, any file is renamed, any file is deleted, any neutral live report path is created, any forbidden path is mutated, final-check has warnings or blocking reasons, or the final report remains non-success for reasons other than a clearly documented real blocker.
