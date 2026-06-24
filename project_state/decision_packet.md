```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260625_executor_neutral_archive_manifest_sync_rework_v1",
  "round_id": "round_20260625_executor_neutral_archive_manifest_sync_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260625_executor_neutral_report_alias_compat_v1",
  "previous_round_id": "round_20260625_executor_neutral_report_alias_compat_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair executor-neutral report alias closeout evidence: pytest transcript, archive manifest policy, run-closeout internal status, and Required Audit must be synchronized without removing legacy compatibility.",
  "command_plan_authority_required": true,
  "accepted_requires_legacy_report_compatibility": true,
  "accepted_requires_neutral_report_alias": true,
  "accepted_requires_legacy_and_neutral_summary_semantic_parity": true,
  "accepted_requires_pytest_transcript_consistent_with_final_artifacts": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_final_check_passed_no_warnings": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_closeout_internal_report_status_success": true,
  "accepted_requires_archive_manifest_policy_sync": true,
  "accepted_requires_required_audit_aligned_answers": true,
  "accepted_requires_required_commands_recorded": true,
  "accepted_requires_state_hygiene_inventory_scope_complete": true,
  "accepted_requires_no_legacy_delete_or_rename": true,
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
    "project_state/rounds/round_20260625_executor_neutral_archive_manifest_sync_rework_v1/*"
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
  "neutral_alias_paths_that_must_remain": [
    "project_state/execution_report.md",
    "project_state/gates/execution_report_auto_summary.json"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement Executor-Neutral Archive Manifest Sync Rework v1.

The previous executor-neutral report alias compatibility round created the intended compatibility surface, but audit found final evidence drift:

- `project_state/pytest_result.txt` summary said `PASSED`, while its command transcript still recorded `execution-log: FAILED` and `run-closeout: FAILED`.
- `project_state/gates/final_gate_result.json` had `gate_status: PASSED`, but still carried a warning for non-minimal archive state: `round_manifest is non-minimal: unexpected files: execution_report.md`, with `archive_status: non_minimal`.
- `project_state/gates/run_closeout_result.json` had outer `closeout_status: PASSED`, but its nested `close_round_result.report_status` was `PARTIAL`.
- closeout/archive evidence did not consistently treat `execution_report.md` as an expected archive artifact.
- Required Audit answers were present but several answers were aligned with the wrong questions.

This round must not add new functionality. It must repair the executor-neutral alias evidence so the previous compatibility layer can be accepted cleanly. Preserve both legacy Codex-named artifacts and the new executor-neutral aliases.

Final accepted state must have:

1. `codex_execution_report.md` with `SUCCESS / ACCEPTED` and correctly aligned Required Audit answers.
2. `execution_report.md` generated and semantically equivalent to `codex_execution_report.md`.
3. `codex_report_auto_summary.json` and `execution_report_auto_summary.json` generated and semantically equivalent.
4. `pytest_result.txt` summary and command transcript consistent with final gate artifacts; no final transcript evidence of failed `execution-log` or failed `run-closeout` accepted as success.
5. `execution_log.json.gate_status: PASSED` and all required command-plan commands recorded.
6. `report_summary_synthesis.json.synthesis_status: PASSED` with no diffs/errors/warnings.
7. `final_gate_result.json.gate_status: PASSED` with no warnings and no blocking reasons.
8. `run_closeout_result.json.closeout_status: PASSED`, non-empty executed steps, nested close-round state coherent with final `SUCCESS`, and no active warnings.
9. archive/round manifest policy synchronized: if `execution_report.md` is archived, it must be expected and covered; if it is not archived, reports must not claim archived neutral report evidence.
10. no legacy report artifact deletion or rename.

This remains `engineering_branch` Phase 1.5. Do not enter Phase 2 CI/Web/AgentRunner/database/multi-executor runtime work.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state and is not authoritative. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260625_executor_neutral_report_alias_compat_v1`.

Accepted prior-round facts to preserve:

- legacy `project_state/codex_execution_report.md` remained generated.
- neutral `project_state/execution_report.md` was generated with `execution_report_summary`.
- legacy `project_state/gates/codex_report_auto_summary.json` remained generated.
- neutral `project_state/gates/execution_report_auto_summary.json` was generated.
- final-check had parity checks for `execution_report.md` and `execution_report_auto_summary.json`.
- tests grew to cover executor-neutral report alias behavior.

Blocking prior-round facts to repair:

- `pytest_result.txt` command transcript retained failed `execution-log` and `run-closeout` commands while the summary claimed `PASSED`.
- `final_gate_result.json` retained a warning and `archive_status: non_minimal` because `execution_report.md` was unexpected in the archive manifest policy.
- `run_closeout_result.json.close_round_result.report_status` was `PARTIAL` while the final report claimed `SUCCESS`.
- closeout archive copied/manifest/generated_artifacts handling for `execution_report.md` was inconsistent.
- Required Audit answers were not aligned with their questions.

Artifact freshness:

- All proof for this rework must be regenerated under `decision_20260625_executor_neutral_archive_manifest_sync_rework_v1` and `round_20260625_executor_neutral_archive_manifest_sync_rework_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices only and must not be claimed as current evidence.

Existing capabilities to preserve:

- command-plan authority and omitted-command enforcement.
- required-command recording enforcement.
- legacy and neutral report parsing.
- legacy and neutral report/auto-summary alias generation.
- report-summary synthesis and final-check strictness.
- Required Audit placeholder blocking.
- closeout/final-state archive synchronization.
- `state_hygiene_inventory_scope_complete`.
- naming-hygiene inventory-only/no-delete behavior.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round touches closeout/archive/report-summary/final-check evidence, command-plan should select or require `full` validation.
- Tests are subordinate to command-plan. If this Tests section conflicts with command-plan, command-plan is authoritative.
- Closeout may run only if command-plan authorizes it and the selected profile allows closeout.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not delete `project_state/codex_execution_report.md`.

Do not delete `project_state/gates/codex_report_auto_summary.json`.

Do not delete `project_state/execution_report.md`.

Do not delete `project_state/gates/execution_report_auto_summary.json`.

Do not rename legacy Codex-named artifacts in this round.

Do not make neutral aliases the only supported path or block.

Do not break parsing of legacy `codex_report_summary` blocks.

Do not break parsing of neutral `execution_report_summary` blocks.

Do not weaken report-summary, final-check, execution-log, closeout, required-command, Required Audit, archive, or generated_artifacts coverage to make aliases pass.

Do not accept `pytest_result_summary.status: PASSED` if the final command transcript still records failed required `execution-log`, `report-summary`, `final-check`, or `run-closeout` outcomes for the accepted state.

Do not accept `final_gate_result.json` with warnings or blocking reasons.

Do not accept `archive_status: non_minimal` as final accepted state for this round.

Do not accept `run_closeout_result.json.close_round_result.report_status: PARTIAL` when the final report is `SUCCESS / ACCEPTED`.

Do not treat a misaligned Required Audit answer as valid merely because it is non-placeholder.

Do not write dynamic findings into `.codex-skills/`.

Do not modify `project_state/artifact_index.json` in this round.

Do not broaden this round into Phase 2 GitHub CI, Web UI, AgentRunner, Codex adapter, Trae adapter, Job Manager, database, queue, scheduler, daemon, API Planner, API Auditor, self-hosted runner, or background worker work.

Do not continue `samplereverse` solving or any sample-solving task.

Do not read the full `solve_reports/` directory or full `PROJECT_PROGRESS_LOG.txt`.

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
6. `project_state/execution_report.md` if present
7. `project_state/decision_packet.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Then inspect only relevant implementation and gate evidence files:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/codex_report_auto_summary.json`
6. `project_state/gates/execution_report_auto_summary.json` if present
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/gate_profile_plan.json`
10. `project_state/gates/naming_migration_plan.json`
11. `project_state/gates/state_hygiene_inventory.json`
12. `project_state/gates/preflight_result.json`
13. `project_state/gates/policy_lint_result.json`
14. `project_state/gates/policy_impact_audit.json`
15. `project_state/gates/run_round_result.json`
16. `project_state/gates/run_closeout_result.json`
17. `project_state/gates/run_closeout_execution_log.json`
18. `project_state/gates/round_delta_summary.json`
19. `project_state/gates/round_close_snapshot.json` if present
20. `project_state/rounds/round_20260625_executor_neutral_report_alias_compat_v1/round_manifest.json` only as bounded prior-round diagnostic evidence if needed

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. What prior drift caused this rework, and which live artifacts proved it?
2. How was the final `pytest_result.txt` transcript made consistent with final `execution_log`, `report-summary`, `final-check`, and `run-closeout` artifacts?
3. What is the archive manifest policy for `execution_report.md`, and how does the final manifest/generated_artifacts evidence prove it is synchronized?
4. How does `run_closeout_result.json` prove outer closeout status, nested close-round status, nested report_status, and final report status are coherent?
5. How do `codex_execution_report.md` and `execution_report.md` remain semantically equivalent while preserving both legacy and neutral summary blocks?
6. How do `codex_report_auto_summary.json` and `execution_report_auto_summary.json` remain semantically equivalent?
7. Which regression tests cover pytest transcript/final artifact consistency, archive manifest policy for neutral aliases, closeout internal status sync, Required Audit answer alignment, and legacy/neutral alias parity?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no heavy artifact scan, no legacy deletion/rename, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Primary scope: repair evidence synchronization for the already-added executor-neutral report alias compatibility layer.

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
- `project_state/rounds/round_20260625_executor_neutral_archive_manifest_sync_rework_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Preserve legacy/neutral report alias generation and parsing from the previous round.
3. Decide and implement archive policy for `execution_report.md`: either it is an expected archived report file or it is not claimed as archived evidence. The accepted state must not be `non_minimal`.
4. If `execution_report.md` is archived, ensure closeout copies it, manifest lists it as expected, generated_artifacts includes it, and final-check treats it as expected.
5. If `execution_report.md` is not archived, ensure generated_artifacts/report claims do not list archived neutral report evidence and final-check has a clear documented policy reason.
6. Ensure the final live `pytest_result.txt` command transcript is coherent with final gate artifacts; no final accepted transcript should retain failed required `execution-log` or `run-closeout` outcomes.
7. Ensure `execution_log.json` records all required command-plan commands, including execution-log/report-auto-summary/run-closeout, without self-missing required command drift.
8. Ensure `run_closeout_result.json` has non-empty executed steps and no active warnings/blocking reasons.
9. Ensure `run_closeout_result.json.close_round_result.report_status` is coherent with final report status. For final `SUCCESS / ACCEPTED`, nested close-round report_status must not remain `PARTIAL`.
10. Ensure `final_gate_result.json.gate_status: PASSED`, `warnings: []`, `blocking_reasons: []`, and no `archive_status: non_minimal`.
11. Ensure `report_summary_synthesis.json.synthesis_status: PASSED` with no diffs/errors/warnings.
12. Ensure Required Audit answers are aligned to their actual questions and remain substantive.
13. Add or update focused tests for archive manifest policy, neutral alias archive behavior, pytest transcript/final artifact consistency, closeout internal status sync, and Required Audit answer alignment where feasible.
14. Preserve `execution_log_required_commands_recorded: PASS` and `state_hygiene_inventory_scope_complete: PASS`.
15. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `execution_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `run_closeout_result.json`, `run_closeout_execution_log.json`, `state_hygiene_inventory.json`, `codex_execution_report.md`, and `execution_report.md`.
16. Run closeout if and only if command-plan authorizes it.
17. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, report-summary `PASSED`, execution-log `PASSED`, report-auto-summary `PASSED`, run-closeout `PASSED`, legacy/neutral alias parity PASS, complete aligned Required Audit, no active closeout warnings, and no blocking reasons.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260625_executor_neutral_archive_manifest_sync_rework_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260625_executor_neutral_archive_manifest_sync_rework_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260625_executor_neutral_archive_manifest_sync_rework_v1
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
- implementation requires weakening command-plan authority, required-command recording, report-summary strictness, final-check strictness, closeout strictness, archive strictness, Required Audit strictness, or alias parity checks;
- implementation requires accepting transcript/final artifact drift as success;
- implementation requires accepting `archive_status: non_minimal` as final success;
- implementation requires accepting `COMPLETED_WITH_LIMITATIONS` as a report status;
- implementation requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
- Required Audit remains incomplete, placeholder-like, or question-answer misaligned.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, required command recording regresses, legacy `codex_execution_report.md` is not generated, neutral `execution_report.md` is not generated, legacy `codex_report_auto_summary.json` is not generated, neutral `execution_report_auto_summary.json` is not generated, legacy/neutral report summary parity fails, legacy/neutral auto-summary parity fails, legacy report parsing regresses, neutral report parsing fails, `codex_execution_report.md` is not `SUCCESS / ACCEPTED`, `pytest_result_summary.status` is not `PASSED`, final transcript records failed required execution-log/report-summary/final-check/run-closeout outcomes as accepted success, Required Audit contains PENDING/placeholders/misaligned answers, `execution_log.json.gate_status` is not `PASSED`, report-summary is not `PASSED`, final-check is not `PASSED`, final-check has warnings or blocking reasons, final archive status is non-minimal, run-closeout is not `PASSED`, `run_closeout_result.json.close_round_result.report_status` is not coherent with final report status, policy-lint fails, policy-impact fails, `state_hygiene_inventory_scope_complete` is missing or not PASS, `execution_log_required_commands_recorded` is missing or not PASS, legacy artifacts are deleted/renamed, forbidden paths are mutated, or the final report remains non-success for reasons other than a clearly documented real blocker.
