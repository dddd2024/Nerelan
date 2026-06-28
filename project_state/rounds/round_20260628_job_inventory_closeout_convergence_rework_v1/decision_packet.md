```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260628_job_inventory_closeout_convergence_rework_v1",
  "round_id": "round_20260628_job_inventory_closeout_convergence_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260628_clean_baseline_job_inventory_v1",
  "previous_round_id": "round_20260628_clean_baseline_job_inventory_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_13_job_inventory_closeout_convergence_rework",
  "primary_goal": "Preserve the completed job inventory implementation and fix report-summary, execute-decision, pytest summary, and run-closeout convergence failures.",
  "command_plan_authority_required": true,
  "accepted_requires_job_inventory_preserved": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_pytest_summary_matches_command_blocks": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "accepted_requires_clean_source_test_baseline": true,
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
  "allowed_generated_job_files": [
    "project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json"
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

Implement Job Inventory Closeout Convergence Rework v1.

The previous round implemented the intended job inventory layer, but the round failed to close. This round must not redo the job inventory feature. It must preserve that implementation and fix the gate/report closeout convergence problems that prevented acceptance.

Current blocking failures from the previous audit:

1. `pytest_result_summary.status` was `PASSED` even though a required `run-closeout` command block exited 1.
2. `report_summary_fields_match_synthesis` failed because the live report summary and synthesized summary disagreed on fields such as `files_changed` and `generated_artifacts`.
3. `execute_decision_contract` failed because `execute_decision_result.status` was not `PASSED`.
4. `run-closeout` exited 1 because `close-round` failed.
5. `closeout_nested_failures_absent` failed because `run_closeout_result.json` contained active nested FAILED/FAIL states.

Final acceptable outcome:

- `status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` null or absent.
- `pytest_result_summary.status` is `PASSED` only when all required recorded command blocks satisfy command-plan expected exit codes.
- `report_summary_fields_match_synthesis` is PASS with no diffs.
- `execute_decision_contract` is PASS.
- `run-closeout` exits 0.
- `run_closeout_result.closeout_status` is `PASSED`.
- `close_round_result.close_status` is `CLOSED`.
- `closeout_nested_failures_absent` is PASS.
- `execution_log.json.source` remains hybrid/direct, not derived-only.
- startup source/test baseline remains clean.
- the job inventory implementation and current DRAFT job contract remain valid.

Fallback acceptable outcome:

- If startup source/test baseline is dirty, stop with `BLOCKED` before changing source files.
- If the job inventory implementation is missing or inconsistent before work starts, stop with `BLOCKED` and report that the previous implementation state is not present.
- Do not use `ACCEPTED_WITH_LIMITATIONS` to mask closeout failures. A closeout failure is `REWORK_REQUIRED`, not a limitation.

This is still an engineering round. It must not enter Web UI, AgentRunner, API Planner/Auditor, self-hosted runner automation, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or reverse-solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md`; `task_packet.json` is non-authoritative background only.

Previous failed round: `decision_20260628_clean_baseline_job_inventory_v1`.

Evidence accepted from the previous round and to preserve:

- startup `git status --short` had no dirty source/test files under `reverse_agent/` or `tests/`.
- preflight reported `source_test_clean_start: PASS`.
- `baseline_capture_order` was PASS and had no source/test overlap.
- `reverse_agent/project_gate.py` and `tests/test_project_gate.py` were left unmodified in that round.
- `validate_jobs_dir` or equivalent job inventory validation was added.
- missing `project_state/jobs/` inventory handling, invalid JSON reporting, invalid payload reporting, duplicate `job_id` rejection, status counts, and validated paths were covered by tests.
- `project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json` was generated as a DRAFT, non-dispatching, safe job contract with current decision/round IDs.
- dispatch and forbidden permission flags remained blocked.
- focused job tests passed with 19 tests.
- combined gate/state/jobs tests passed with 1260 tests.
- `execution_log.json.source` remained `hybrid_from_pytest_result_command_plan_and_run_closeout_execution_log`.

Blocking evidence from the previous round:

- `codex_report_summary.status` was `FAILED` and `acceptance_recommendation` was `REWORK_REQUIRED`.
- `pytest_result_summary.status` was `PASSED`, but `run-closeout` exited 1.
- `report-summary` exited 1 with diffs in status and acceptance recommendation.
- final-check failed `pytest_result_match`, `pytest_result_exit_codes_match_command_plan`, `report_summary_fields_match_synthesis`, `execute_decision_contract`, `status_policy_valid`, and `closeout_nested_failures_absent`.
- `run_closeout_result.closeout_status` was `FAILED`.
- `close-round` exited 1 with `close_status: FAILED`.

Artifact freshness:

- `current_state.json` and `artifact_index.json` still include sample-state and missing historical sample artifacts.
- Those sample artifacts are non-blocking for this engineering round because no sample-solving evidence is claimed.
- Do not upgrade missing/stale sample evidence to current.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full solve_reports, and repeating old runtime evidence directions.
- This round must not perform reverse-solving, sample execution, runtime probing, or full solve_reports scans.

Existing tool/job capability:

- `project_jobs.py` already contains the job status/state-machine and job inventory foundation from the previous implementation.
- `project_gate.py` already owns report-summary synthesis, final-check, execution-log, execute-decision, and run-closeout behavior.
- This round should modify `project_gate.py` only as needed to fix closeout/report-summary convergence. It should not broaden the job system.

## 3. Do Not Do

Do not redo the job inventory feature. Preserve `validate_jobs_dir`, the DRAFT job contract, duplicate job_id detection, invalid job reporting, status counts, validated paths, transition validation, lock/lease validation, and permission rejection.

Do not modify `reverse_agent/project_jobs.py` or `tests/test_project_jobs.py` unless a narrowly scoped compatibility issue is found and explicitly justified. They are preserve-only for this round.

Do not change the generated DRAFT job contract into READY or RUNNING.

Do not weaken job safety. `runner.dispatch_enabled` must remain false and forbidden permission flags must remain false.

Do not manually edit `pytest_result.txt` to hide failed command blocks.

Do not set `pytest_result_summary.status` to `PASSED` if any required recorded command block exits outside command-plan expected exit codes.

Do not claim `SUCCESS / ACCEPTED` until report-summary synthesis, execute-decision contract, final-check, run-closeout, and close-round all converge.

Do not treat `run-closeout exit 1` as an acceptable limitation.

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
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/execute_decision_result.json`
10. `project_state/gates/execution_log.json`
11. `project_state/gates/run_closeout_execution_log.json`
12. `project_state/gates/command_plan.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup source/test baseline clean before implementation?
2. Was the existing job inventory implementation preserved rather than rewritten?
3. Does the generated DRAFT job contract still validate as DRAFT, non-dispatching, and safe?
4. Did dispatch and forbidden permission flags remain blocked?
5. What caused the previous `report_summary_fields_match_synthesis` failure, and what exact behavior now prevents the mismatch?
6. Do live report summaries, auto summaries, and `report_summary_synthesis.json` agree on `status`, `acceptance_recommendation`, `files_changed`, `generated_artifacts`, `tests_ran`, and `limitations`?
7. What caused the previous `execute_decision_contract` failure, and why is `execute_decision_result.status` now `PASSED`?
8. If execute-decision self-invocation guard is used, how is it represented without failing the execute-decision contract?
9. Does `pytest_result_summary.status` match all required recorded command-block exit codes?
10. Did both required pytest commands exit 0, and what are their pass counts?
11. Did `final-check` pass before closeout or produce only allowed diagnostic states?
12. Did `run-closeout` exit 0?
13. Is `run_closeout_result.closeout_status` `PASSED`, and is `close_round_result.close_status` `CLOSED`?
14. Does `closeout_nested_failures_absent` pass with no active nested FAILED/FAIL states?
15. Did hybrid execution-log provenance remain valid and non-derived-only?
16. Were forbidden paths, full solve_reports scans, reverse-solving, Web/AgentRunner/DB/queue/scheduler scope, and remote mutation avoided?

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Preserve-only source/test files unless a narrow compatibility issue is explicitly justified:

- `reverse_agent/project_jobs.py`
- `tests/test_project_jobs.py`

Allowed generated or updated state artifacts:

- `project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json`
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
- `project_state/rounds/round_20260628_job_inventory_closeout_convergence_rework_v1/*`

Required behavior:

1. Preserve the completed job inventory feature and its tests.
2. Fix report-summary synthesis alignment so report summaries and synthesis agree on all required summary fields.
3. Ensure `generated_artifacts` and `files_changed` include all expected current round artifacts, including `execute_decision_result.json` and `run_round_result.json` when the synthesis expects them.
4. Fix or regenerate `execute_decision_result.json` so the execute-decision contract passes.
5. Represent self-invocation guard/skipped run-round behavior as a passing/valid execute-decision outcome when it is expected and safe.
6. Fix `pytest_result_summary.status` logic so nonzero required command blocks prevent `PASSED` until the transcript is rerun successfully.
7. Rerun the full authorized command chain after fixes so the final `pytest_result.txt` contains no required command block outside expected exit codes.
8. Make run-closeout and close-round converge with no active nested failures.
9. Preserve hybrid execution-log provenance and startup order checks.
10. Keep implementation small and avoid broad refactors.

## 7. Tests

Record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Startup rule:

- If `git status --short` contains dirty source/test paths under `reverse_agent/` or `tests/` before implementation, stop with `BLOCKED` unless those paths are exactly known committed work already present in the remote checkout and no local source/test dirty state remains after sync.
- Do not proceed from an unexplained source/test dirty baseline.

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260628_job_inventory_closeout_convergence_rework_v1 --mode execute
python -m pytest tests/test_project_jobs.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260628_job_inventory_closeout_convergence_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls, except it must not override startup-first ordering, pytest summary consistency, report-summary convergence, execute-decision contract, hybrid provenance preservation, or closeout consistency.

Write all top-level commands and exit codes to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- unexplained source/test dirty files exist under `reverse_agent/` or `tests/` before implementation;
- decision_meta is invalid;
- status is not APPROVED;
- mainline is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or unsafe;
- the previous job inventory implementation is missing and cannot be preserved;
- implementation requires forbidden path mutation;
- implementation requires Web UI, AgentRunner, external dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- `report_summary_fields_match_synthesis` fails;
- report summaries, auto summaries, synthesis, and final-check disagree on summary fields;
- `execute_decision_contract` fails;
- `execute_decision_result.status` is not `PASSED` in the accepted end state;
- `run-closeout` exits nonzero;
- `close_round_result.close_status` is not `CLOSED`;
- `closeout_nested_failures_absent` fails;
- `execution_log.json` regresses to derived-only while report/final-check claims pure `ACCEPTED`;
- `baseline_capture_order` regresses to WARN while report/final-check claims pure `ACCEPTED`;
- generated DRAFT job contract becomes READY/RUNNING or dispatch-enabled;
- dispatch or remote mutation permissions become allowed;
- startup transcript order regresses;
- reverse_solving strict freshness semantics regress;
- forbidden paths are modified;
- tests fail.
