```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260628_pytest_summary_and_closeout_consistency_rework_v1",
  "round_id": "round_20260628_pytest_summary_and_closeout_consistency_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260627_limited_acceptance_status_policy_rework_v1",
  "previous_round_id": "round_20260627_limited_acceptance_status_policy_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_9_pytest_summary_and_closeout_consistency_rework",
  "primary_goal": "Fix the failed test, pytest summary contradiction, and closeout/report-summary state mismatch while preserving the already-correct startup and limited-acceptance policy work.",
  "command_plan_authority_required": true,
  "accepted_requires_pytest_commands_all_exit_zero": true,
  "accepted_requires_pytest_summary_matches_command_blocks": true,
  "accepted_requires_reverse_solving_synthesis_regression_fixed": true,
  "accepted_requires_report_summary_matches_synthesis": true,
  "accepted_requires_closeout_passed": true,
  "accepted_requires_acceptance_with_limitations_when_derived_log_remains": true,
  "allowed_source_files": ["reverse_agent/project_gate.py", "tests/test_project_gate.py"],
  "preserve_only_files": [
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/project_jobs.py",
    "tests/test_project_jobs.py",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
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

Implement Pytest Summary and Closeout Consistency Rework v1.

The previous round did not reach an acceptable limited-acceptance state. It correctly avoided pure `ACCEPTED`, but it ended as `FAILED / REWORK_REQUIRED` because a regression test failed, `pytest_result_summary.status` contradicted recorded command exits, final-check failed, and run-closeout failed.

This round must fix the real failures. Do not broaden scope and do not redo completed work.

Final acceptable state:

1. `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q` exits 0.
2. `python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q` exits 0.
3. `pytest_result_summary.status` is `PASSED` only if every required recorded command block that should pass has exit code 0. If any required command exits nonzero, summary status must not be `PASSED`.
4. `TestReportSummarySynthesisMainlineAware::test_reverse_solving_historical_blocks_in_synthesis` passes. Engineering status-policy changes must not break reverse_solving strict freshness semantics.
5. `report_summary_fields_match_synthesis` passes: live report summaries, auto summaries, report-summary synthesis, and final-check agree on status and acceptance recommendation.
6. `run-closeout` exits 0 and `run_closeout_result.closeout_status` is `PASSED`.
7. `final_gate_result.gate_status` is `PASSED`.
8. If `execution_log.json.source` remains `derived_from_pytest_result_and_command_plan`, then final acceptance must be `ACCEPTED_WITH_LIMITATIONS`, with non-null limitations that name the derived execution-log provenance. `status` may remain `SUCCESS` only if tests and gates pass.
9. Preserve the existing correct startup transcript order and `startup_command_position_order` check.
10. Preserve `baseline_capture_order: PASS` if still achievable. If it regresses to WARN, acceptance must remain limited and limitations must name it.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md`; `task_packet.json` remains background only.

Evidence from the failed previous round:

- `codex_execution_report.md` reported `status: FAILED` and `acceptance_recommendation: REWORK_REQUIRED`.
- `pytest_result_summary.status` said `PASSED`, but a recorded pytest command exited 1.
- The failing test was `tests/test_project_gate.py::TestReportSummarySynthesisMainlineAware::test_reverse_solving_historical_blocks_in_synthesis`.
- final-check reported `gate_status: FAILED`.
- run-closeout reported `closeout_status: FAILED` and close-round exited 1.
- report-summary synthesis expected `SUCCESS / ACCEPTED_WITH_LIMITATIONS`, but the live report said `FAILED / REWORK_REQUIRED`.
- `startup_command_position_order` remained PASS.
- `baseline_capture_order` was PASS in the final-check evidence.
- derived execution-log limitation was recorded, but the round did not close cleanly.

Previously accepted work to preserve:

- startup transcript order;
- `startup_command_position_order`;
- limited-acceptance rule for derived execution-log provenance;
- `baseline_capture_order` clean handling;
- `decision-preflight.yml`;
- `project_jobs.py` and `tests/test_project_jobs.py`;
- neutral-primary report semantics and legacy aliases;
- command-plan, pytest_result, execution-log, report-summary, final-check, and run-closeout chain.

Historical sample artifacts remain non-blocking for this engineering round. Do not use sample-state as current engineering evidence. Do not execute sample-solving work.

## 3. Do Not Do

Do not paper over the failed pytest result by manually changing the summary header.

Do not set `pytest_result_summary.status` to `PASSED` if any required recorded command block exits nonzero.

Do not break reverse_solving strict freshness semantics while fixing engineering limited acceptance.

Do not turn the previous failed round into accepted by editing archived evidence.

Do not redo the startup-order implementation unless a narrow compatibility fix is required.

Do not change `decision-preflight.yml`, `project_jobs.py`, or `tests/test_project_jobs.py` except for narrow compatibility preservation.

Do not modify forbidden paths listed in `decision_contract`.

Do not enter Web UI, external runner dispatch, database, queue, scheduler, automatic remote writes, or sample-solving scope.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly instructs the executor to do so.

## 4. Files To Inspect

Read first:

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
6. `project_state/gates/execution_log.json`
7. `project_state/gates/command_plan.json`
8. `project_state/gates/execute_decision_result.json`
9. `project_state/gates/round_baseline.json`
10. `project_state/gates/round_delta_summary.json`
11. preservation-only files named in `decision_contract.preserve_only_files` only to confirm they were not redesigned.

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Did the two required pytest commands exit 0, and what are their pass counts?
2. Does `pytest_result_summary.status` match the recorded command-block exit codes?
3. Was `TestReportSummarySynthesisMainlineAware::test_reverse_solving_historical_blocks_in_synthesis` fixed without weakening reverse_solving strict freshness semantics?
4. What are the final `status`, `acceptance_recommendation`, and `limitations` in `codex_report_summary`, `execution_report_summary`, auto summaries, synthesis, and final-check?
5. Does `report_summary_fields_match_synthesis` pass?
6. Does `execute_decision_result` pass, and does it match the transcript?
7. Does `run-closeout` exit 0 and does `run_closeout_result.closeout_status` equal `PASSED`?
8. Are startup order and `startup_command_position_order` preserved?
9. Is `execution_log.json` direct, hybrid, or derived-only? If derived-only, where is the `ACCEPTED_WITH_LIMITATIONS` limitation recorded?
10. Was any preservation-only file redesigned? If no, list the preserved files.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

- `project_state/execution_report.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/execution_report_auto_summary.json`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/state_hygiene_inventory.json`
- `project_state/rounds/round_20260628_pytest_summary_and_closeout_consistency_rework_v1/*`

Required behavior:

1. Fix the reverse_solving synthesis regression so acceptance recommendation is never `None` when strict freshness should block or require review.
2. Fix pytest_result summary generation or validation so summary status cannot contradict command-block exits.
3. Align report-summary synthesis, live report summaries, auto summaries, final-check, and report body.
4. Make the clean intended end state `SUCCESS / ACCEPTED_WITH_LIMITATIONS` when tests pass and only derived execution-log limitation remains.
5. Make run-closeout and close-round pass only when report-summary and final-check are consistent.
6. Preserve startup-order behavior and limited-acceptance semantics.
7. Keep implementation small and avoid broad refactors.

## 7. Tests

Record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260628_pytest_summary_and_closeout_consistency_rework_v1 --mode execute
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260628_pytest_summary_and_closeout_consistency_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative, but it must not override startup-first ordering, pytest summary consistency, or closeout consistency requirements.

Write all top-level commands and exit codes to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- decision_meta is invalid;
- status is not APPROVED;
- mainline is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or unsafe;
- forbidden path mutation is required;
- scope requires Web UI, external runner dispatch, database, queue, scheduler, automatic remote writes, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- reverse_solving synthesis returns `None` for acceptance recommendation where strict freshness requires review or rework;
- report-summary synthesis and report summaries disagree;
- `execute_decision_result` is not PASSED;
- final-check fails;
- run-closeout fails;
- close-round fails;
- clean intended state is not `SUCCESS / ACCEPTED_WITH_LIMITATIONS` when only derived execution-log limitation remains;
- startup transcript order regresses;
- `startup_command_position_order` disappears or fails;
- limitations remain but `limitations` is null;
- preservation-only files are unnecessarily redesigned;
- neutral-primary report semantics regress;
- legacy alias parity breaks;
- forbidden paths are modified;
- tests fail.
