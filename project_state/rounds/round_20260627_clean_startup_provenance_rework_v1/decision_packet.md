```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260627_clean_startup_provenance_rework_v1",
  "round_id": "round_20260627_clean_startup_provenance_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260626_preflight_job_foundation_and_clean_provenance_v1",
  "previous_round_id": "round_20260626_preflight_job_foundation_and_clean_provenance_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_6_clean_startup_provenance_rework",
  "primary_goal": "Fix the provenance/report mismatch from the previous round without redoing the accepted decision-preflight workflow or minimal job schema foundation.",
  "command_plan_authority_required": true,
  "accepted_requires_startup_five_command_order_first": true,
  "accepted_requires_report_claims_match_transcript": true,
  "accepted_requires_derived_execution_log_limitation_or_direct_capture": true,
  "accepted_requires_baseline_warning_not_claimed_clean": true,
  "accepted_requires_no_rewrite_of_completed_preflight_or_job_schema_work": true,
  "accepted_requires_pytest_result_status_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_existing_files_to_preserve_only": [
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

Implement Clean Startup Provenance Rework v1.

The previous round successfully added the bounded `decision-preflight.yml` workflow and a minimal non-dispatching `project_jobs.py` validator, but audit returned `REWORK_REQUIRED` because the round claimed clean provenance that the transcript did not support.

This rework must not broaden scope. It must repair the provenance/report mismatch and preserve already-valid work.

Final accepted state must satisfy:

1. The transcript must record the full startup sequence before any substantive command: `Set-Location F:\reverse-agent`, `Get-Location`, `Test-Path F:\reverse-agent`, `git rev-parse --show-toplevel`, and `git status --short` must all appear before any `preflight`, `command-plan`, `report-summary`, `pytest`, `execution-log`, `run-closeout`, or `final-check` command block in `project_state/pytest_result.txt`.
2. `command_plan.json` and `execution_log.json` must not imply a different command order than the transcript. If command-plan contains startup commands, they should be ordered before substantive commands; if command-plan represents logical authorization order rather than transcript order, that distinction must be explicit and tested.
3. The live report must not claim that `git rev-parse` or `git status --short` ran before command-plan unless the recorded transcript actually proves it.
4. If `execution_log.json` remains `derived_from_pytest_result_and_command_plan`, the report and final-check/status policy must explicitly expose that as a provenance limitation and use `ACCEPTED_WITH_LIMITATIONS` rather than pure `ACCEPTED`; alternatively, implement direct or hybrid command capture sufficient to justify pure `ACCEPTED`.
5. If `baseline_capture_order` remains `WARN`, the round must not claim clean provenance or pure `ACCEPTED`; either remove the warning by producing clean evidence, or keep the result limited and explicit.
6. Preserve the existing `.github/workflows/decision-preflight.yml`, `reverse_agent/project_jobs.py`, and `tests/test_project_jobs.py` behavior unless a narrow compatibility change is required by gate checks. Do not redesign them.
7. Preserve existing CI/state-gate workflows, neutral-primary report semantics, legacy aliases, command-plan authority, execute-decision `--mode execute`, pytest_result, execution-log, final-check, report-summary, and run-closeout convergence.
8. Do not implement Web console, AgentRunner, automatic Codex/Trae dispatch, API Planner/Auditor, self-hosted runner automation, database, queue, scheduler, automatic push, or reverse-solving in this round.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current live decision was `decision_20260626_preflight_job_foundation_and_clean_provenance_v1`. It produced a report with `status=SUCCESS` and `acceptance_recommendation=ACCEPTED`, but audit returned `REWORK_REQUIRED`.

Accepted work to preserve from that round:

- `.github/workflows/decision-preflight.yml` exists and runs bounded validation: install package, project_gate preflight, project_gate command-plan, and focused tests.
- `reverse_agent/project_jobs.py` implements a minimal local, non-dispatching job contract validator.
- `tests/test_project_jobs.py` covers valid non-dispatching contracts, missing required fields, unknown statuses, dispatch/mutation permission rejection, and JSON file loading.
- Focused tests passed in the previous run.
- final-check and run-closeout reported PASSED in the previous run.

Rework evidence that must be addressed:

- In the previous transcript, only `Set-Location`, `Get-Location`, and `Test-Path` appeared before the first substantive `preflight` command. `git rev-parse --show-toplevel` and `git status --short` appeared later, after report-summary.
- The previous report claimed the exact startup commands appeared before command-plan, but the transcript did not support that claim.
- `execution_log.json` still used `source: derived_from_pytest_result_and_command_plan`.
- `baseline_capture_order` remained a final-check WARN, and final-check still listed it in final warnings.
- The previous report/final-check represented the result as pure `ACCEPTED` with no limitations despite the above provenance constraints.

`task_packet.json` remains non-authoritative background state and explicitly says the decision packet controls the current round. Do not execute `task_packet.task` as authority.

`current_state.json` and `artifact_index.json` still describe sample-state and missing historical sample artifacts. They are non-blocking for this engineering round because no sample-solving evidence is claimed.

`negative_results.json` contains reverse-solving prohibitions. This round must not repeat old sample_solver blind search, beam/budget expansion, compare_semantics_agree=false primary frontier usage, full solve_reports commits, or repeated runtime evidence directions.

This is not a reverse-solving round. Do not inspect, execute, debug, emulate, or solve sample binaries. Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not redo, redesign, or broaden the already accepted `decision-preflight.yml` and `project_jobs.py` foundation unless a narrow compatibility adjustment is strictly required.

Do not implement Web UI, Web backend, API Planner, API Auditor, AgentRunner, self-hosted runner automation, database, queue, scheduler, or multi-agent orchestration.

Do not add workflows that run LLM calls, push commits, create PRs, modify remote state, dispatch agents, or execute sample binaries.

Do not add automatic pull/push behavior for agents.

Do not scan full `solve_reports/` or execute reverse-solving samples.

Do not delete `project_state/codex_execution_report.md`.

Do not delete `project_state/gates/codex_report_auto_summary.json`.

Do not break parser support for `codex_report_summary`.

Do not rename `.codex-skills/` or modify `.codex-skills/registry.json`.

Do not modify docs prompt files in this round.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Do not use `COMPLETED_WITH_LIMITATIONS` as report status.

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
3. `reverse_agent/project_jobs.py` only to confirm preservation
4. `tests/test_project_jobs.py` only to confirm preservation
5. `.github/workflows/decision-preflight.yml` only to confirm preservation
6. `.github/workflows/ci.yml` only to confirm preservation
7. `.github/workflows/state-gate.yml` only to confirm preservation
8. `project_state/gates/command_plan.json`
9. `project_state/gates/execution_log.json`
10. `project_state/gates/final_gate_result.json`
11. `project_state/gates/report_summary_synthesis.json`
12. `project_state/gates/run_closeout_result.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`
15. `project_state/gates/run_closeout_execution_log.json`
16. current round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, the current live report must answer all seven items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. What exact startup command blocks appear in `project_state/pytest_result.txt`, in what order, and before which first substantive command?
2. Does `project_state/pytest_result.txt` prove that all five startup commands ran before any `preflight`, `command-plan`, `report-summary`, `pytest`, `execution-log`, `run-closeout`, or `final-check` command?
3. Is `execution_log.json` direct, hybrid, or derived-only? If derived-only, where is the limitation recorded and why is the acceptance recommendation not pure `ACCEPTED`?
4. Is `baseline_capture_order` PASS, WARN, or absent? If WARN remains, where is the resulting limitation recorded?
5. Which previous report claim was corrected regarding startup order and transcript evidence?
6. How were `decision-preflight.yml`, `project_jobs.py`, and `tests/test_project_jobs.py` preserved without redesign or agent dispatch?
7. How were command-plan authority, pytest_result transcript, execution-log, final-check, report-summary, and run-closeout convergence preserved?

Do not write TODO, TBD, PENDING, `should pass`, `expected to pass`, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed only if strictly necessary for compatibility, otherwise preserve unchanged:

- `.github/workflows/decision-preflight.yml`
- `reverse_agent/project_jobs.py`
- `tests/test_project_jobs.py`
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`

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
- `project_state/rounds/round_20260627_clean_startup_provenance_rework_v1/*`

Required behavior:

1. Ensure the complete startup sequence is recorded before any substantive command in `pytest_result.txt`.
2. Ensure command-plan, execution-log, and final-check do not contradict the transcript command order.
3. Add or update tests that fail if `git rev-parse` or `git status --short` appear after substantive commands while the report claims clean startup provenance.
4. Add or update tests/status-policy checks that prevent pure `ACCEPTED` when `execution_log.json` is derived-only and the report lacks an explicit limitation.
5. Add or update tests/status-policy checks that prevent pure `ACCEPTED` when `baseline_capture_order` remains WARN and the report lacks an explicit limitation.
6. Preserve neutral-primary report source semantics and legacy alias compatibility.
7. Preserve execute-decision `--mode execute`, command-plan convergence, pytest_result, execution-log, final-check, report-summary, and run-closeout behavior.
8. Keep implementation small and avoid broad refactors.

## 7. Tests

Run startup checks first and record them before substantive commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Then use command-plan authority. Run preflight and command-plan only after the full five-command startup block is recorded.

Preferred current-round entrypoint:

```powershell
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260627_clean_startup_provenance_rework_v1 --mode execute
```

At minimum, validation should include command-plan-authorized equivalents of:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260627_clean_startup_provenance_rework_v1 --mode execute
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260627_clean_startup_provenance_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict, but command-plan must not authorize an accepted-state transcript that violates the five-command startup-first requirement without explicit limitation.

Record all top-level commands and exit codes in `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- implementation requires forbidden path mutation;
- implementation requires Web / AgentRunner / DB / queue / scheduler scope;
- implementation requires automatic push, PR creation, or remote mutation;
- implementation requires sample-solving or heavy artifact scan.

Stop with `REWORK_REQUIRED` if:

- full five-command startup block is not recorded before the first substantive command;
- report claims startup order that the transcript does not prove;
- execution_log remains derived-only while report/final-check claims pure `ACCEPTED` without limitation;
- `baseline_capture_order` remains WARN while report/final-check claims pure `ACCEPTED` without limitation;
- existing `decision-preflight.yml`, `project_jobs.py`, or `tests/test_project_jobs.py` is unnecessarily redesigned;
- work enters AgentRunner, Web, database, queue, scheduler, API Planner/Auditor, automatic push, or reverse-solving scope;
- neutral-primary report semantics regress;
- legacy alias parity breaks;
- execute-decision `--mode execute` regresses;
- command-plan stdout differs from live command_plan.json;
- execution-log has missing required command-plan commands;
- final-check fails;
- run-closeout fails;
- pytest_result_summary.status is not `PASSED` in accepted or accepted-with-limitations state;
- report status disagrees with pytest_result, execution-log, final-check, or run-closeout;
- forbidden paths are modified;
- `.codex-skills` is renamed or registry is modified;
- tests fail;
- policy-lint or policy-impact fails.
