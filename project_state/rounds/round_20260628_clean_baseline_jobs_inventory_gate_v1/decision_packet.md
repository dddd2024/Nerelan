```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260628_clean_baseline_jobs_inventory_gate_v1",
  "round_id": "round_20260628_clean_baseline_jobs_inventory_gate_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260628_job_inventory_closeout_convergence_rework_v1",
  "previous_round_id": "round_20260628_job_inventory_closeout_convergence_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_14_clean_baseline_jobs_inventory_gate",
  "primary_goal": "Eliminate the remaining baseline limitation by requiring a clean source/test startup baseline, then expose the existing jobs inventory validator through a bounded project_gate CLI/gate artifact.",
  "command_plan_authority_required": true,
  "accepted_requires_clean_source_test_start": true,
  "accepted_requires_no_baseline_capture_order_warn": true,
  "accepted_requires_jobs_inventory_gate_artifact": true,
  "accepted_requires_job_inventory_preserved": true,
  "accepted_requires_no_agent_dispatch": true,
  "accepted_requires_no_remote_mutation": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_jobs.py",
    "tests/test_project_jobs.py",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "allowed_existing_job_files": [
    "project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json"
  ],
  "allowed_new_gate_artifacts": [
    "project_state/gates/jobs_inventory_result.json"
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

Implement Clean Baseline Jobs Inventory Gate v1.

The previous round fixed the report-summary, execute-decision, and closeout convergence failures, but the audit outcome remained `ACCEPTED_WITH_LIMITATIONS` because `baseline_capture_order` was WARN. The warning was caused by `reverse_agent/project_gate.py` and `tests/test_project_gate.py` being dirty at startup and also appearing in `files_changed`.

This round combines cleanup and forward progress:

1. Require a clean source/test startup baseline before implementation.
2. Preserve the existing job inventory implementation and DRAFT job contract.
3. Expose the existing `project_jobs.validate_jobs_dir` behavior through a bounded `project_gate` gate/CLI artifact.
4. Generate or update `project_state/gates/jobs_inventory_result.json` as a current, auditable, read-only gate artifact.
5. Add tests proving the jobs inventory gate validates existing jobs, handles missing jobs directory, reports invalid jobs without dispatch, and is represented in final-check or an equivalent gate evidence path.

Preferred final outcome:

- `status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` null or absent.
- startup source/test baseline is clean.
- `baseline_capture_order` is PASS or absent.
- `jobs_inventory_result.json` exists, is current, and records the current decision/round IDs.
- the existing DRAFT job contract remains DRAFT, non-dispatching, and safe.
- `execution_log.json.source` remains hybrid/direct, not derived-only.
- `report_summary_fields_match_synthesis`, `execute_decision_contract`, `run-closeout`, and `closeout_nested_failures_absent` all pass.

Fallback acceptable outcome:

- If startup source/test baseline is dirty, stop with `BLOCKED` before modifying files.
- Do not use `ACCEPTED_WITH_LIMITATIONS` to mask a dirty baseline. The point of this round is to eliminate the baseline limitation.
- If the previous job inventory implementation is missing or inconsistent, stop with `BLOCKED` and report the missing prerequisite.

This is still an engineering round. It must not implement Web UI, AgentRunner, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, automatic remote writes, GitHub Actions mutation, or reverse-solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md`; `task_packet.json` remains non-authoritative background only.

Previous round: `decision_20260628_job_inventory_closeout_convergence_rework_v1`.

Accepted evidence from the previous round:

- `report-summary` passed.
- `execute_decision_contract` passed.
- `run-closeout` exited 0.
- `run_closeout_result.closeout_status` was `PASSED`.
- `close_round_result.close_status` was `CLOSED`.
- `closeout_nested_failures_absent` passed.
- focused job tests passed with 19 tests.
- combined gate/state/jobs tests passed with 1262 tests.
- `execution_log.json.source` remained `hybrid_from_pytest_result_command_plan_and_run_closeout_execution_log`.
- `project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json` remained a valid DRAFT, non-dispatching, safe job contract.

Remaining limitation from the previous round:

- `baseline_capture_order` was WARN because `reverse_agent/project_gate.py` and `tests/test_project_gate.py` were dirty in startup baseline and also appeared in `files_changed`.

Existing job capability to build on:

- `reverse_agent/project_jobs.py` already defines job statuses, terminal states, transition validation, optional lock/lease validation, safe permission validation, `validate_job_payload`, `validate_job_file`, and `validate_jobs_dir` or equivalent inventory validation.
- `tests/test_project_jobs.py` already covers individual job validation and inventory-level behavior.
- This round must not rewrite that layer. It should only call it from `project_gate.py` and surface it as a current gate artifact.

Artifact freshness:

- `current_state.json` and `artifact_index.json` still include sample-state and missing historical sample artifacts.
- Those sample artifacts are non-blocking for this engineering round because no sample-solving evidence is claimed.
- Do not upgrade missing/stale sample evidence to current.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full solve_reports, and repeating old runtime evidence directions.
- This round must not perform reverse-solving, sample execution, runtime probing, or full solve_reports scans.

## 3. Do Not Do

Do not begin implementation if startup `git status --short` shows dirty source/test paths under `reverse_agent/` or `tests/`. Stop with `BLOCKED` instead.

Do not use `ACCEPTED_WITH_LIMITATIONS` to mask a dirty startup source/test baseline.

Do not redo or rewrite `project_jobs.py`. Preserve its job state-machine, inventory validation, transition validation, lock/lease validation, DRAFT job contract, and safety restrictions.

Do not change `project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json` from DRAFT to READY or RUNNING.

Do not enable dispatch. `runner.dispatch_enabled` must remain false.

Do not allow remote mutation, LLM calls, agent dispatch, or reverse-solving permissions in job contracts.

Do not manually edit `pytest_result.txt` to hide failed command blocks.

Do not claim pure `ACCEPTED` unless baseline is clean and final-check/run-closeout converge without active warnings or nested failures.

Do not modify `current_state.json`, `task_packet.json`, `artifact_index.json`, `negative_results.json`, `.codex-skills/registry.json`, or docs prompts.

Do not scan full `solve_reports/` or execute reverse samples.

Do not introduce Web UI, AgentRunner, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, GitHub Actions mutation, automatic push, or reverse-solving.

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

Then inspect bounded implementation and gate evidence:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `reverse_agent/project_jobs.py`
4. `tests/test_project_jobs.py`
5. `project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json`
6. `project_state/gates/jobs_inventory_result.json` if present
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/execution_log.json`
10. `project_state/gates/command_plan.json`
11. `project_state/gates/report_summary_synthesis.json`
12. `project_state/gates/round_baseline.json`
13. `project_state/gates/round_delta_summary.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup source/test baseline clean before implementation?
2. Is `baseline_capture_order` PASS, WARN, or absent?
3. Was the existing job inventory implementation preserved rather than rewritten?
4. Does the generated DRAFT job contract still validate as DRAFT, non-dispatching, and safe?
5. What `project_gate` CLI/gate surface was added for jobs inventory validation?
6. Does `jobs_inventory_result.json` exist, and does it carry current decision/round IDs?
7. Does the jobs inventory gate report status counts, validated paths, duplicate job errors, and invalid file errors without dispatching anything?
8. How does the jobs inventory gate handle a missing jobs directory?
9. Is jobs inventory evidence included in final-check or an equivalent gate evidence path?
10. Do dispatch and forbidden permission flags remain blocked?
11. Did both required pytest commands exit 0, and what are their pass counts?
12. Did `report_summary_fields_match_synthesis` pass with no diffs?
13. Did `execute_decision_contract` pass?
14. Did `run-closeout` exit 0, with `closeout_status: PASSED` and `close_round_result.close_status: CLOSED`?
15. Did `closeout_nested_failures_absent` pass with no active nested FAILED/FAIL states?
16. Did hybrid execution-log provenance remain valid and non-derived-only?
17. Were forbidden paths, full solve_reports scans, reverse-solving, Web/AgentRunner/DB/queue/scheduler scope, and remote mutation avoided?

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Preserve-only source/test files:

- `reverse_agent/project_jobs.py`
- `tests/test_project_jobs.py`

Allowed existing job file, preserve as DRAFT unless a narrow metadata refresh is required and justified:

- `project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json`

Allowed generated or updated state artifacts:

- `project_state/gates/jobs_inventory_result.json`
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
- `project_state/rounds/round_20260628_clean_baseline_jobs_inventory_gate_v1/*`

Required behavior:

1. Add a bounded `project_gate` command or equivalent gate function for jobs inventory validation.
2. The command should call the existing `project_jobs.validate_jobs_dir` or equivalent and write `project_state/gates/jobs_inventory_result.json`.
3. The artifact must include schema version, gate name, gate status, current decision_id, current round_id, inventory validation status, job count, status counts, validated paths, duplicate job errors, invalid file errors, and dispatch safety status.
4. Missing jobs directory must be valid with zero jobs.
5. Invalid job files must be reported as errors without dispatching anything.
6. Duplicate job IDs must be rejected.
7. Final-check must validate the jobs inventory artifact or include equivalent current inventory evidence.
8. Preserve existing report-summary, execute-decision, run-closeout, close-round, hybrid execution-log, and startup-order behavior.
9. Keep implementation small and avoid broad refactors.

## 7. Tests

Record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Hard startup rule:

- If `git status --short` contains dirty source/test paths under `reverse_agent/` or `tests/`, stop with `BLOCKED` before modifying any source/test file.
- The executor may clean the local worktree only if it can do so without discarding user work; otherwise stop and ask for a clean baseline.

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate jobs-inventory --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260628_clean_baseline_jobs_inventory_gate_v1 --mode execute
python -m pytest tests/test_project_jobs.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260628_clean_baseline_jobs_inventory_gate_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls, except it must not override startup-first ordering, clean source/test baseline, pytest summary consistency, jobs inventory gate evidence, report-summary convergence, execute-decision contract, hybrid provenance preservation, or closeout consistency.

Write all top-level commands and exit codes to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- startup `git status --short` shows dirty source/test files under `reverse_agent/` or `tests/`;
- decision_meta is invalid;
- status is not APPROVED;
- mainline is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or unsafe;
- previous job inventory implementation is missing and cannot be preserved;
- implementation requires modifying preserve-only job files beyond a narrowly justified metadata compatibility fix;
- implementation requires forbidden path mutation;
- implementation requires Web UI, AgentRunner, external dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- startup source/test dirty baseline is ignored and implementation proceeds;
- `baseline_capture_order` remains WARN while report/final-check claims pure `ACCEPTED`;
- jobs inventory gate command or artifact is missing;
- jobs inventory artifact is stale or missing current decision/round IDs;
- invalid job files or duplicate job IDs are silently accepted;
- generated DRAFT job contract becomes READY/RUNNING or dispatch-enabled;
- dispatch or remote mutation permissions become allowed;
- `report_summary_fields_match_synthesis` fails;
- `execute_decision_contract` fails;
- `run-closeout` exits nonzero;
- `close_round_result.close_status` is not `CLOSED`;
- `closeout_nested_failures_absent` fails;
- `execution_log.json` regresses to derived-only while report/final-check claims pure `ACCEPTED`;
- startup transcript order regresses;
- reverse_solving strict freshness semantics regress;
- forbidden paths are modified;
- tests fail.
