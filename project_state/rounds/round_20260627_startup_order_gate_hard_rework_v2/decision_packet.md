```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260627_startup_order_gate_hard_rework_v2",
  "round_id": "round_20260627_startup_order_gate_hard_rework_v2",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260627_clean_startup_provenance_rework_v1",
  "previous_round_id": "round_20260627_clean_startup_provenance_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_7_startup_order_gate_hard_rework",
  "primary_goal": "Make startup command order and limited-provenance acceptance mechanically enforceable.",
  "command_plan_authority_required": true,
  "accepted_requires_first_five_commands_exact_startup": true,
  "accepted_requires_no_pure_accepted_for_derived_execution_log": true,
  "accepted_requires_no_pure_accepted_for_baseline_warn": true,
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

Implement Startup Order Gate Hard Rework v2.

The previous round failed audit because it still treated startup command coverage as startup command order. The transcript showed only `Set-Location`, `Get-Location`, and `Test-Path` before `command-plan`; `git rev-parse --show-toplevel` and `git status --short` appeared later. The report nevertheless claimed all five startup commands preceded substantive work.

This round must make that impossible. The project gate and tests must reject a pure accepted result when the transcript does not prove the required order.

A pure `ACCEPTED` result is valid only if all are true:

1. The first five top-level `===== COMMAND:` blocks in `project_state/pytest_result.txt` are exactly:
   1. `Set-Location F:\reverse-agent`
   2. `Get-Location`
   3. `Test-Path F:\reverse-agent`
   4. `git rev-parse --show-toplevel`
   5. `git status --short`
2. No command-plan, preflight, report-summary, pytest, final-check, execution-log, run-closeout, execute-decision, decision-lint, gate-profile, or close-round command appears before those five blocks.
3. `execution_log.json` is not merely `derived_from_pytest_result_and_command_plan`, unless the report is limited.
4. `baseline_capture_order` is not WARN, unless the report is limited.
5. final-check exposes this as a dedicated position/order check, not just command coverage.

If `execution_log.json` remains derived-only or `baseline_capture_order` remains WARN, the report must use `acceptance_recommendation: ACCEPTED_WITH_LIMITATIONS` and must record explicit limitations. `status` may remain `SUCCESS` if tests and gates pass, but pure `ACCEPTED` is not allowed.

Preserve the existing decision-preflight workflow and job schema foundation. Do not redesign them.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current decision is controlled by `project_state/decision_packet.md`; `task_packet.json` is background only.

The previous round failed for three concrete reasons:

- The first substantive command appeared before the complete five-command startup block.
- `execution_log.json` was still derived from pytest_result and command_plan.
- `baseline_capture_order` remained WARN while the report still recommended pure `ACCEPTED`.

Previously accepted work to preserve:

- `.github/workflows/decision-preflight.yml`
- `reverse_agent/project_jobs.py`
- `tests/test_project_jobs.py`
- existing CI/state-gate workflows
- neutral-primary report semantics and legacy aliases
- command-plan, pytest_result, execution-log, report-summary, final-check, and run-closeout chain

Historical sample artifacts remain non-blocking for this engineering round. Do not use sample-state files as current evidence for this task.

## 3. Do Not Do

Do not solve this by report prose only.

Do not mark Required Audit PASS when the transcript contradicts it.

Do not let startup command coverage substitute for startup command order.

Do not allow pure `ACCEPTED` when execution_log is derived-only without explicit limitation.

Do not allow pure `ACCEPTED` when baseline_capture_order remains WARN without explicit limitation.

Do not modify forbidden paths listed in decision_contract.

Do not redesign `decision-preflight.yml`, `project_jobs.py`, or `tests/test_project_jobs.py` unless a narrow compatibility change is unavoidable.

Do not add web UI, external runner dispatch, database, queue, scheduler, automatic remote writes, or sample-solving work.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly tells the executor to do so.

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

Then inspect only:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/run_closeout_result.json`
8. `project_state/gates/round_baseline.json`
9. `project_state/gates/round_delta_summary.json`
10. preservation-only files named in `preserve_only_files`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. What are the first five top-level command blocks in `project_state/pytest_result.txt`, exactly and in order?
2. What is the first substantive command block, and is it after the five startup commands?
3. Which final-check/test rule fails if `git rev-parse` or `git status --short` appears after a substantive command?
4. Is command-plan order authorization order or transcript order, and how is that distinction represented?
5. Is `execution_log.json` direct, hybrid, or derived-only? If derived-only, why is pure `ACCEPTED` blocked or limited?
6. Is `baseline_capture_order` PASS, WARN, or absent? If WARN remains, why is pure `ACCEPTED` blocked or limited?
7. What previous false PASS claim was corrected?
8. How were decision-preflight, project_jobs, command-plan, pytest_result, execution-log, final-check, report-summary, and run-closeout preserved?

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
- `project_state/rounds/round_20260627_startup_order_gate_hard_rework_v2/*`

Required behavior:

1. Add or fix a position-based startup-order check.
2. Add regression tests where `git rev-parse` or `git status --short` after command-plan causes failure for pure accepted state.
3. Add or fix status policy so derived-only execution_log blocks pure `ACCEPTED` unless limitations are explicit.
4. Add or fix status policy so baseline_capture_order WARN blocks pure `ACCEPTED` unless limitations are explicit.
5. Preserve neutral-primary report semantics and legacy aliases.
6. Preserve execute-decision, command-plan, pytest_result, execution-log, report-summary, final-check, and run-closeout behavior.

## 7. Tests

Record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Only after those five blocks, run command-plan-authorized validation, including:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260627_startup_order_gate_hard_rework_v2 --mode execute
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260627_startup_order_gate_hard_rework_v2
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative, except it must not override the five-startup-commands-first requirement for accepted state.

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
- scope requires web UI, external runner dispatch, database, queue, scheduler, automatic remote writes, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- the first five top-level command blocks are not exactly the required startup sequence;
- any substantive command appears before those five startup commands;
- final-check lacks a dedicated position-based startup-order check;
- report claims startup order that the transcript does not prove;
- execution_log remains derived-only while report/final-check claims pure `ACCEPTED` without limitation;
- baseline_capture_order remains WARN while report/final-check claims pure `ACCEPTED` without limitation;
- command-plan order and transcript order differ but no explicit order semantics explains the distinction;
- preservation-only files are unnecessarily redesigned;
- neutral-primary report semantics regress;
- legacy alias parity breaks;
- execute-decision or command-plan authority regresses;
- final-check or run-closeout fails unexpectedly;
- pytest_result_summary.status is not PASSED in accepted or accepted-with-limitations state;
- forbidden paths are modified;
- tests fail.
