```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260628_clean_baseline_job_inventory_v1",
  "round_id": "round_20260628_clean_baseline_job_inventory_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260628_clean_baseline_and_job_state_machine_v1",
  "previous_round_id": "round_20260628_clean_baseline_and_job_state_machine_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_12_clean_baseline_job_inventory",
  "primary_goal": "Require a clean source/test startup baseline, then extend the existing job layer with project_state/jobs inventory validation and one safe non-dispatching DRAFT job contract.",
  "command_plan_authority_required": true,
  "accepted_requires_source_test_clean_start": true,
  "accepted_requires_no_baseline_capture_order_warn": true,
  "accepted_requires_job_inventory_v1": true,
  "accepted_requires_safe_draft_job_contract": true,
  "accepted_requires_no_agent_dispatch": true,
  "accepted_requires_no_remote_mutation": true,
  "accepted_requires_pytest_summary_matches_command_blocks": true,
  "accepted_requires_final_check_and_closeout_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_jobs.py",
    "tests/test_project_jobs.py"
  ],
  "forbidden_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "preserve_only_files": [
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

Implement Clean Baseline Job Inventory v1.

The previous round successfully added the job state-machine foundation, but final audit remained `ACCEPTED_WITH_LIMITATIONS` because `baseline_capture_order` was WARN. This round must stop accumulating baseline limitations and make actual forward progress only from a clean source/test baseline.

This round combines cleanup and implementation:

1. Enforce a clean source/test startup baseline before any code change.
2. Preserve the existing hybrid execution-log provenance and job state-machine helpers.
3. Extend the existing `project_jobs.py` layer with bounded `project_state/jobs/*.json` inventory validation.
4. Add a safe non-dispatching DRAFT job contract under `project_state/jobs/` for the current round.
5. Add tests proving inventory validation, duplicate job detection, invalid job file reporting, status counts, backward compatibility, and safety restrictions.

Preferred final outcome:

- `status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` null or absent.
- startup source/test baseline is clean.
- `baseline_capture_order` is PASS or absent.
- `execution_log.json.source` remains hybrid/direct, not derived-only.
- job inventory validation is implemented and tested.
- the generated DRAFT job contract validates and cannot dispatch or mutate remote state.
- final-check and run-closeout pass.

Fallback outcome:

- If source/test files are dirty at startup, do not implement. Stop with `BLOCKED` and explain that the local worktree must be cleaned before this decision can run.
- Do not downgrade to `ACCEPTED_WITH_LIMITATIONS` merely to continue from a dirty source/test baseline. The point of this round is to eliminate that class of limitation.

This is an engineering round. Do not implement Web UI, AgentRunner, API Planner/Auditor, self-hosted runner automation, database, queue, scheduler, automatic remote writes, or reverse-solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md`; `task_packet.json` is non-authoritative background only.

Previous accepted-with-limitations round: `decision_20260628_clean_baseline_and_job_state_machine_v1`.

Accepted evidence from that round:

- `reverse_agent/project_jobs.py` gained `JOB_TERMINAL_STATUSES`, `JOB_STATUS_TRANSITIONS`, lock/lease validation, `validate_job_transition`, and payload-level transition validation.
- `tests/test_project_jobs.py` covered valid transitions, unsafe transitions, lock/lease metadata, backward compatibility, safe current example validation, dispatch rejection, and remote mutation rejection.
- job tests passed.
- full gate/state/jobs pytest passed.
- final-check and run-closeout passed.
- `execution_log.json.source` remained `hybrid_from_pytest_result_command_plan_and_run_closeout_execution_log`.

Remaining limitation:

- `baseline_capture_order` was WARN because source/test files were dirty at startup and overlapped with files_changed.

Existing job capability to build on:

- `project_jobs.py` already validates individual `project_state/jobs/*.json` contracts.
- It already rejects dispatch and forbidden permissions.
- It already supports safe state transitions and optional lock/lease metadata.
- This round must extend that foundation with inventory-level validation, not replace it.

Strategic context:

- The long-term architecture moves from manual GPT/Codex loops toward Web console + Planner API + command-plan + AgentRunner + CI + final-check + Auditor, but current implementation should proceed in bounded layers.
- The next safe layer is job inventory and job contract validation, not database, Web UI, full AgentRunner, or automatic dispatch.

Artifact freshness:

- `current_state.json` and `artifact_index.json` still describe sample-state and missing historical sample artifacts.
- Those sample artifacts are non-blocking for this engineering round because no sample-solving evidence is claimed.
- Do not upgrade missing/stale sample evidence to current.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full solve_reports, and repeating old runtime evidence directions.
- This round must not perform reverse-solving, sample execution, runtime probing, or full solve_reports scans.

## 3. Do Not Do

Do not start implementation if startup `git status --short` shows dirty source/test files under `reverse_agent/` or `tests/`. Stop with `BLOCKED` instead.

Do not modify `reverse_agent/project_gate.py` or `tests/test_project_gate.py` in this round.

Do not redesign `project_jobs.py`. Extend existing validators with small, testable inventory helpers.

Do not enable dispatch. `runner.dispatch_enabled` must remain false.

Do not allow remote mutation, LLM calls, agent dispatch, or reverse-solving permissions in job contracts.

Do not create a READY/RUNNING job that an executor could treat as runnable. The generated job contract must be DRAFT and non-dispatching.

Do not introduce Web UI, AgentRunner, API Planner/Auditor, database, queue, scheduler, self-hosted runner automation, GitHub Actions mutation, automatic push, or reverse-solving.

Do not add a heavy workflow engine.

Do not modify forbidden paths listed in `decision_contract`.

Do not scan full `solve_reports/` or execute reverse samples.

Do not change `.codex-skills/registry.json` or store dynamic run facts in `.codex-skills/`.

Do not claim pure `ACCEPTED` if `baseline_capture_order` remains WARN.

Do not claim pure `ACCEPTED` if `execution_log.json` regresses to derived-only.

Do not manually edit `pytest_result.txt` to hide failed command blocks.

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

Then inspect bounded implementation files:

1. `reverse_agent/project_jobs.py`
2. `tests/test_project_jobs.py`
3. existing `project_state/jobs/*.json` if present
4. `project_state/gates/execution_log.json`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/run_closeout_result.json`
7. `project_state/gates/round_baseline.json`
8. `project_state/gates/round_delta_summary.json`
9. `project_state/gates/command_plan.json`

Inspect only for regression context, do not modify:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup source/test baseline clean before implementation?
2. Is `baseline_capture_order` PASS, WARN, or absent? If WARN remains, why did the round not claim pure `ACCEPTED`?
3. Were `reverse_agent/project_gate.py` and `tests/test_project_gate.py` left unmodified?
4. What job inventory helper(s) were added to `project_jobs.py`?
5. How does inventory validation handle a missing `project_state/jobs/` directory?
6. How does inventory validation report invalid job files without dispatching anything?
7. How are duplicate `job_id` values detected?
8. What status counts are returned for valid job inventories?
9. Was `project_state/jobs/job_20260628_clean_baseline_job_inventory_v1.json` generated, and is it DRAFT/non-dispatching/safe?
10. Does the generated job contract reference the current decision and round IDs?
11. Do dispatch and forbidden permission flags remain blocked?
12. Did both required pytest commands exit 0, and what are their pass counts?
13. Did final-check and run-closeout pass?
14. Did hybrid execution-log provenance remain valid and non-derived-only?
15. Were forbidden paths, full solve_reports scans, reverse-solving, Web/AgentRunner/DB/queue/scheduler scope, and remote mutation avoided?

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_jobs.py`
- `tests/test_project_jobs.py`

Forbidden source/test changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

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
- `project_state/rounds/round_20260628_clean_baseline_job_inventory_v1/*`

Required behavior:

1. Add bounded job inventory validation for `project_state/jobs/*.json`.
2. Add a helper such as `validate_jobs_dir(state_dir)` or equivalent.
3. Missing `project_state/jobs/` should be valid with zero jobs.
4. Invalid JSON or invalid job payloads should be reported as inventory errors without raising uncaught exceptions.
5. Duplicate `job_id` values across job files must be rejected.
6. Valid inventories should return counts by job status and a list of validated job paths.
7. Preserve existing single-job validation, transition validation, lock/lease validation, and dispatch/permission rejection.
8. Generate a safe current DRAFT job contract under `project_state/jobs/`.
9. The generated job must be non-dispatching, forbid remote mutation/LLM calls/agent dispatch/reverse-solving, and reference the current decision and round IDs.
10. Preserve hybrid execution-log provenance and status policy behavior.
11. Keep implementation small and avoid broad refactors.

## 7. Tests

Before implementation, record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Hard startup rule:

- If `git status --short` contains dirty source/test paths under `reverse_agent/` or `tests/`, stop with `BLOCKED` before modifying any file.
- Project-state generated files may be dirty, but source/test dirty baseline is not allowed for this round.

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260628_clean_baseline_job_inventory_v1 --mode execute
python -m pytest tests/test_project_jobs.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260628_clean_baseline_job_inventory_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls, except it must not override startup-first ordering, clean source/test baseline, pytest summary consistency, baseline warning honesty, hybrid provenance preservation, or closeout consistency.

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
- implementation requires modifying `reverse_agent/project_gate.py` or `tests/test_project_gate.py`;
- implementation requires forbidden path mutation;
- implementation requires Web UI, AgentRunner, external dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- `execution_log.json` regresses to derived-only while report/final-check claims pure `ACCEPTED`;
- `baseline_capture_order` remains WARN while report/final-check claims pure `ACCEPTED`;
- startup source/test dirty baseline was ignored and implementation proceeded;
- `reverse_agent/project_gate.py` or `tests/test_project_gate.py` is modified;
- job inventory validation is not implemented or not tested;
- invalid job files are silently accepted;
- duplicate job IDs are accepted;
- the generated job contract is READY/RUNNING or dispatch-enabled;
- dispatch or remote mutation permissions become allowed;
- report-summary synthesis and report summaries disagree;
- final-check fails unexpectedly;
- run-closeout fails;
- startup transcript order regresses;
- reverse_solving strict freshness semantics regress;
- preservation-only workflows are redesigned;
- forbidden paths are modified;
- tests fail.
