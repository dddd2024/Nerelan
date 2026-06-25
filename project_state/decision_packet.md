```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260625_executor_neutral_gate_status_scope_rework_v1",
  "round_id": "round_20260625_executor_neutral_gate_status_scope_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260625_executor_neutral_archive_manifest_sync_rework_v1",
  "previous_round_id": "round_20260625_executor_neutral_archive_manifest_sync_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair executor-neutral alias rework by fixing gate status aggregation, scope drift, closeout internal consistency, report-summary state, report-auto-summary parity, and Required Audit completeness without expanding scope.",
  "command_plan_authority_required": true,
  "accepted_requires_no_scope_drift": true,
  "accepted_requires_no_unauthorized_source_changes": true,
  "accepted_requires_required_audit_complete": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_final_check_passed_no_internal_failures": true,
  "accepted_requires_run_closeout_passed_no_internal_failures": true,
  "accepted_requires_report_auto_summary_consistency": true,
  "accepted_requires_archive_status_consistent": true,
  "accepted_requires_legacy_neutral_alias_parity": true,
  "accepted_requires_required_commands_recorded": true,
  "accepted_requires_state_hygiene_inventory_scope_complete": true,
  "accepted_requires_no_phase2_scope": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "cleanup_only_paths_must_not_remain_in_final_delta": [
    ".claude/settings.local.json",
    "reverse_agent/project_state.py"
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
    "project_state/rounds/round_20260625_executor_neutral_gate_status_scope_rework_v1/*"
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

Implement Executor-Neutral Gate Status Scope Rework v1.

The previous rework did not reach an acceptable final state. It improved the top-level command transcript, but live artifacts still contradicted the report:

- `codex_execution_report.md` claimed `SUCCESS / ACCEPTED` while `report_summary_synthesis.json` was `FAILED`.
- `final_gate_result.json` had top-level `gate_status: PASSED` while internal checks still contained `FAIL` entries such as archived report mismatch and report-auto-summary mismatch.
- `run_closeout_result.json` had top-level `closeout_status: PASSED` while `close-round` and nested `close_round_result.close_status` were `FAILED`.
- `codex_execution_report.md` lacked the required 8 audit answers.
- the round delta included out-of-scope files: `.claude/settings.local.json` and `reverse_agent/project_state.py`.

This round must only repair those hard failures. Do not add new executor-neutral functionality. Do not remove the executor-neutral alias layer. Do not enter Phase 2.

Final accepted state must have:

1. no out-of-scope final source/config delta;
2. `codex_execution_report.md` with `SUCCESS / ACCEPTED` and complete, aligned Required Audit answers;
3. `execution_report.md` present and semantically equivalent to `codex_execution_report.md`;
4. `codex_report_auto_summary.json` and `execution_report_auto_summary.json` present and semantically equivalent;
5. `pytest_result.txt` summary and transcript consistent with final artifacts;
6. `execution_log.json.gate_status: PASSED` and all required command-plan commands recorded;
7. `report_summary_synthesis.json.synthesis_status: PASSED` with no diffs/errors/warnings;
8. `final_gate_result.json.gate_status: PASSED` with no internal `FAIL`, no warnings, and no blocking reasons;
9. `run_closeout_result.json.closeout_status: PASSED` with no failed internal steps, no failed nested close-round state, no active warnings, and coherent archive status;
10. archive action, archive status, manifest contents, generated_artifacts, and live/archived report parity synchronized.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains a non-authoritative `samplereverse` background packet. This round is controlled only by `project_state/decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260625_executor_neutral_archive_manifest_sync_rework_v1`.

Blocking evidence from the previous round:

- decision allowed source changes only in `reverse_agent/project_gate.py` and `tests/test_project_gate.py`, but report/final-gate evidence showed `.claude/settings.local.json` and `reverse_agent/project_state.py` in the round delta;
- `codex_execution_report.md` ended after the header and did not contain the Required Audit section;
- `report_summary_synthesis.json` was `FAILED`;
- `final_gate_result.json` had top-level `PASSED` but internal failures including archived report mismatch and report-auto-summary consistency failure;
- `run_closeout_result.json` had top-level `PASSED` but internal close-round failure and blocking reasons;
- archive action/status/manifest evidence was internally inconsistent.

Accepted facts to preserve:

- legacy `codex_execution_report.md` path remains supported;
- neutral `execution_report.md` alias remains supported;
- legacy `codex_report_auto_summary.json` remains supported;
- neutral `execution_report_auto_summary.json` remains supported;
- legacy and neutral parser compatibility must remain intact;
- command-plan authority and required-command recording remain mandatory.

Artifact freshness:

- All proof must be regenerated under `decision_20260625_executor_neutral_gate_status_scope_rework_v1` and `round_20260625_executor_neutral_gate_status_scope_rework_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices and must not be claimed as current evidence.

Gate/command-plan strategy:

- Valid profiles are only `fast`, `standard`, and `full`.
- Because this round repairs report-summary/final-check/closeout evidence, command-plan should select or require `full` validation.
- Tests are subordinate to command-plan. If Tests and command-plan conflict, command-plan is authoritative.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not add new architectural functionality in this round.

Do not enter Phase 2, CI, Web UI, AgentRunner, database, queue, scheduler, or multi-executor runtime work.

Do not delete or rename legacy Codex-named artifacts.

Do not delete or rename executor-neutral alias artifacts.

Do not make neutral aliases the only supported path or block.

Do not break parsing of `codex_report_summary` or `execution_report_summary`.

Do not accept any top-level gate status as `PASSED` if nested required checks contain `FAIL`.

Do not accept `run_closeout_result.json.closeout_status: PASSED` if any required closeout step is `FAILED`, if `close_round_result.close_status` is `FAILED`, or if closeout blocking reasons remain.

Do not accept `report_summary_synthesis.json` as successful if `synthesis_status` is not `PASSED`.

Do not accept `codex_execution_report.md` with missing, placeholder-like, or misaligned Required Audit answers.

Do not leave `.claude/settings.local.json` in final round delta or final report `files_changed` / `generated_artifacts`.

Do not leave `reverse_agent/project_state.py` in final round delta unless a future decision explicitly allows it. This decision does not allow it.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Do not write dynamic findings into `.codex-skills/`.

Do not read the full `solve_reports/` directory or full `PROJECT_PROGRESS_LOG.txt`.

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

Then inspect only bounded implementation and gate evidence:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/codex_report_auto_summary.json`
6. `project_state/gates/execution_report_auto_summary.json`
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/run_closeout_result.json`
10. `project_state/gates/run_closeout_execution_log.json`
11. `project_state/gates/round_baseline.json`
12. `project_state/gates/round_delta_summary.json`
13. `project_state/gates/round_close_snapshot.json` if present
14. `project_state/gates/state_hygiene_inventory.json`
15. `project_state/gates/preflight_result.json`
16. `project_state/gates/policy_lint_result.json`
17. `project_state/gates/policy_impact_audit.json`
18. prior round manifest only as bounded diagnostic evidence if needed: `project_state/rounds/round_20260625_executor_neutral_archive_manifest_sync_rework_v1/round_manifest.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. What exact prior failures caused this rework, and which artifacts proved them?
2. How was final scope drift removed so `.claude/settings.local.json` and `reverse_agent/project_state.py` do not remain in final delta or report fields?
3. How was Required Audit restored so all eight answers are complete and aligned to their questions?
4. How does report-summary prove `synthesis_status: PASSED` and no diffs/errors/warnings?
5. How does final-check prove there are no nested `FAIL` checks, no warnings, no blocking reasons, and no false top-level `PASSED` aggregation?
6. How does run-closeout prove outer status, executed steps, nested close-round status, blocking reasons, archive action, archive status, and manifest state are mutually consistent?
7. How were legacy/neutral report and auto-summary aliases preserved with semantic parity?
8. How does this round preserve no sample-solving, no prompt/skill mutation, no heavy artifact scan, no legacy deletion/rename, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Primary scope: repair gate status aggregation, report/auto-summary consistency, closeout internal consistency, archive consistency, and final scope hygiene for the already-existing executor-neutral alias layer.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Cleanup-only requirement:

- `.claude/settings.local.json` must not remain in final dirty delta, final `files_changed`, or final `generated_artifacts`.
- `reverse_agent/project_state.py` must not remain in final dirty delta, final `files_changed`, or final `generated_artifacts`.

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
- `project_state/rounds/round_20260625_executor_neutral_gate_status_scope_rework_v1/*`

Required behavior:

1. Establish a current-round baseline before implementation.
2. Preserve legacy and neutral report alias generation/parsing.
3. Ensure report-summary fails if synthesized summary and live report disagree, and ensure final accepted output has no such disagreement.
4. Ensure final-check aggregation cannot be `PASSED` when any required nested check is `FAIL`.
5. Ensure final-check output has no internal `FAIL`, no warnings, and no blocking reasons in accepted state.
6. Ensure run-closeout aggregation cannot be `PASSED` when any required executed step is `FAILED`, close-round is `FAILED`, blocking reasons remain, or archive state is inconsistent.
7. Ensure report-auto-summary and neutral auto-summary match live report summaries.
8. Ensure archive action/status/manifest/copied files/generated_artifacts are coherent.
9. Ensure final `pytest_result.txt`, `execution_log.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `run_closeout_result.json`, `codex_execution_report.md`, and `execution_report.md` all refer to the current decision/report/round and agree.
10. Ensure Required Audit answers are complete and aligned.
11. Add focused tests for nested FAIL aggregation, closeout failed-step aggregation, scope drift exclusion, report-summary/report-auto-summary parity, and Required Audit completeness/alignment where feasible.
12. Regenerate current-round gate/state artifacts according to command-plan authority.
13. Run closeout only if command-plan authorizes it.

Do not implement Phase 2, Web, CI, database, multi-executor runtime adapters, or deletion/migration of legacy artifacts.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260625_executor_neutral_gate_status_scope_rework_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260625_executor_neutral_gate_status_scope_rework_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260625_executor_neutral_gate_status_scope_rework_v1
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands in `project_state/pytest_result.txt`. Record closeout-internal evidence only in scoped closeout artifacts, not as duplicate top-level command transcript.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- implementation requires keeping changes outside allowed source scope;
- implementation requires forbidden path mutations;
- implementation requires deleting or renaming legacy or neutral report artifacts;
- implementation requires weakening report-summary/final-check/closeout strictness;
- implementation requires accepting nested failure as top-level success;
- implementation requires accepting missing Required Audit answers;
- implementation requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, required command recording regresses, `.claude/settings.local.json` remains in final delta/report fields, `reverse_agent/project_state.py` remains in final delta/report fields, Required Audit is missing/misaligned, report-summary is not `PASSED`, final-check contains nested `FAIL`, final-check has warnings or blocking reasons, run-closeout contains failed required steps, close-round remains failed, report-auto-summary consistency fails, alias parity fails, archive action/status/manifest/copied files/generated_artifacts conflict, policy-lint fails, policy-impact fails, `execution_log_required_commands_recorded` is not PASS, `state_hygiene_inventory_scope_complete` is not PASS, or final report remains non-success for reasons other than a clearly documented real blocker.
