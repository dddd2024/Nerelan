```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260627_limited_acceptance_status_policy_rework_v1",
  "round_id": "round_20260627_limited_acceptance_status_policy_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260627_startup_order_gate_hard_rework_v2",
  "previous_round_id": "round_20260627_startup_order_gate_hard_rework_v2",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_8_limited_acceptance_status_policy_rework",
  "primary_goal": "Fix acceptance recommendation and limitation policy when startup order is correct but provenance is still limited.",
  "command_plan_authority_required": true,
  "accepted_requires_preserve_startup_order_check": true,
  "accepted_requires_derived_log_limited_acceptance": true,
  "accepted_requires_baseline_warn_limited_acceptance": true,
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

Implement Limited Acceptance Status Policy Rework v1.

The previous round fixed the startup transcript order and added a dedicated `startup_command_position_order` final-check. Audit still returned `REWORK_REQUIRED` because the report remained pure `ACCEPTED` even though `execution_log.json` was derived-only and `baseline_capture_order` remained WARN.

This round must not rework the startup-order solution. Preserve it. The target is only status-policy and report-summary consistency.

Final acceptable outcome:

1. If `execution_log.json.source == "derived_from_pytest_result_and_command_plan"`, pure `ACCEPTED` is blocked unless a direct or hybrid provenance artifact exists.
2. If `baseline_capture_order` is WARN, pure `ACCEPTED` is blocked unless the warning is actually cleared.
3. If either limitation remains, `codex_report_summary.acceptance_recommendation` and `execution_report_summary.acceptance_recommendation` must be `ACCEPTED_WITH_LIMITATIONS`.
4. If either limitation remains, final-check `status_policy_valid.limitations` must be non-null and must name the limitation.
5. `status` may remain `SUCCESS` when tests and gates pass. Do not invent unsupported status values.
6. The report body must explicitly list limitations instead of claiming fully clean provenance.
7. The existing correct startup order and `startup_command_position_order` check must remain intact.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by this `decision_packet.md`; `task_packet.json` is background only.

Evidence from the previous round:

- `pytest_result.txt` correctly started with `Set-Location`, `Get-Location`, `Test-Path`, `git rev-parse --show-toplevel`, and `git status --short` before `command-plan`.
- final-check contained `startup_command_position_order: PASS`.
- tests passed.
- `execution_log.json.source` remained `derived_from_pytest_result_and_command_plan`.
- `baseline_capture_order` remained WARN.
- `codex_report_summary.acceptance_recommendation` still said `ACCEPTED`.
- final-check `status_policy_valid.limitations` was null.

Previously accepted work to preserve:

- startup command order in `pytest_result.txt`;
- `startup_command_position_order` check;
- `decision-preflight.yml`;
- `project_jobs.py` and `tests/test_project_jobs.py`;
- neutral-primary report semantics and legacy aliases;
- command-plan, pytest_result, execution-log, report-summary, final-check, and run-closeout chain.

Historical sample artifacts remain non-blocking for this engineering round. Do not use sample-state as current evidence.

## 3. Do Not Do

Do not redo the startup-order implementation unless a narrow compatibility fix is required.

Do not change `decision-preflight.yml`, `project_jobs.py`, or `tests/test_project_jobs.py` except to preserve compatibility.

Do not claim pure `ACCEPTED` if execution_log is derived-only.

Do not claim pure `ACCEPTED` if `baseline_capture_order` remains WARN.

Do not set `limitations` to null when acceptance is limited.

Do not modify forbidden paths listed in `decision_contract`.

Do not enter web UI, external runner dispatch, database, queue, scheduler, automatic remote writes, or sample-solving scope.

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

Then inspect only:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/execution_log.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/round_baseline.json`
7. `project_state/gates/round_delta_summary.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/command_plan.json`
10. preservation-only files named in `decision_contract.preserve_only_files`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Is the first-five-command startup order still correct?
2. Does `startup_command_position_order` still pass?
3. Is `execution_log.json` direct, hybrid, or derived-only?
4. If execution_log is derived-only, where is the limitation recorded, and why is pure `ACCEPTED` blocked?
5. Is `baseline_capture_order` PASS, WARN, or absent?
6. If `baseline_capture_order` remains WARN, where is the limitation recorded, and why is pure `ACCEPTED` blocked?
7. What are the final `status`, `acceptance_recommendation`, and `limitations` fields in both report summaries and final-check?
8. How were preserved files and existing gate chain behavior kept unchanged?

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
- `project_state/rounds/round_20260627_limited_acceptance_status_policy_rework_v1/*`

Required behavior:

1. Preserve startup transcript order and `startup_command_position_order` behavior.
2. Add or fix tests so derived-only execution_log blocks pure `ACCEPTED` unless explicit limitations are present.
3. Add or fix tests so `baseline_capture_order` WARN blocks pure `ACCEPTED` unless explicit limitations are present.
4. Make report-summary synthesis, auto-summary aliases, final-check, and report body agree on `ACCEPTED_WITH_LIMITATIONS` when limitations remain.
5. Keep implementation small and avoid broad refactors.

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
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260627_limited_acceptance_status_policy_rework_v1 --mode execute
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260627_limited_acceptance_status_policy_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative, but it must not override the startup-first requirement or limited-acceptance policy.

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

- startup transcript order regresses;
- `startup_command_position_order` disappears or fails;
- execution_log remains derived-only while report/final-check claims pure `ACCEPTED`;
- `baseline_capture_order` remains WARN while report/final-check claims pure `ACCEPTED`;
- limitations remain but `limitations` is null;
- report summaries, auto summaries, final-check, and report body disagree on acceptance recommendation;
- preservation-only files are unnecessarily redesigned;
- neutral-primary report semantics regress;
- legacy alias parity breaks;
- execute-decision or command-plan authority regresses;
- final-check or run-closeout fails unexpectedly;
- pytest_result_summary.status is not PASSED in accepted or accepted-with-limitations state;
- forbidden paths are modified;
- tests fail.
