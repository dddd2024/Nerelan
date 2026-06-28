```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260628_clean_baseline_and_job_state_machine_v1",
  "round_id": "round_20260628_clean_baseline_and_job_state_machine_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260628_hybrid_execution_log_provenance_v1",
  "previous_round_id": "round_20260628_hybrid_execution_log_provenance_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_11_clean_baseline_and_job_state_machine",
  "primary_goal": "Combine cleanup of the remaining baseline warning with bounded forward progress on the project_state job state machine.",
  "command_plan_authority_required": true,
  "accepted_requires_no_baseline_capture_order_warn_for_pure_accepted": true,
  "accepted_requires_job_state_machine_v1": true,
  "accepted_requires_no_agent_dispatch": true,
  "accepted_requires_no_remote_mutation": true,
  "accepted_requires_pytest_summary_matches_command_blocks": true,
  "accepted_requires_final_check_and_closeout_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_jobs.py",
    "tests/test_project_jobs.py"
  ],
  "inspect_only_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "preserve_only_files": [
    ".github/workflows/decision-preflight.yml",
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

Implement Clean Baseline and Job State Machine v1.

The previous round succeeded in upgrading `execution_log.json` from derived-only to hybrid provenance, but it still ended as `ACCEPTED_WITH_LIMITATIONS` because `baseline_capture_order` returned to WARN when `reverse_agent/project_gate.py` and `tests/test_project_gate.py` were already dirty at startup and also appeared in `files_changed`.

This round combines cleanup and forward progress:

1. Avoid repeating the baseline overlap problem by not modifying the inherited dirty project gate files.
2. Preserve the hybrid execution-log provenance work.
3. Extend the already existing non-dispatching job contract validator into a small job state-machine foundation.
4. Add tests for valid and invalid job status transitions, lock/lease metadata validation, and safe READY/RUNNING/DONE job contracts.
5. Optionally generate one current `project_state/jobs/job_20260628_clean_baseline_and_job_state_machine_v1.json` example job contract if the implementation can do so without violating scope.

Final preferred outcome:

- `status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` null or absent.
- `baseline_capture_order` PASS or absent.
- `execution_log.json.source` remains hybrid/direct, not derived-only.
- pytest summary, report-summary synthesis, final-check, and run-closeout all pass.

Fallback acceptable outcome:

- `status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED_WITH_LIMITATIONS`.
- explicit limitation naming baseline/source-test inherited dirty state.
- This fallback is acceptable only if all implementation requirements are satisfied and the limitation is accurately represented. It is not acceptable to claim pure ACCEPTED while baseline WARN remains.

This is still an engineering round. Do not implement Web UI, AgentRunner, API Planner/Auditor, self-hosted runner automation, database, queue, scheduler, automatic remote writes, or reverse-solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md`; `task_packet.json` is non-authoritative background only.

The previous round `decision_20260628_hybrid_execution_log_provenance_v1` ended with audit outcome `ACCEPTED_WITH_LIMITATIONS`.

Accepted evidence from the previous round:

- `execution_log.json.source` was upgraded to `hybrid_from_pytest_result_command_plan_and_run_closeout_execution_log`.
- `execution_log.json.provenance.classification` was `hybrid`.
- final-check included `execution_log_provenance_valid: PASS`.
- both required pytest commands passed.
- `pytest_result_summary.status` matched recorded command exits.
- final-check and run-closeout passed.
- report-summary synthesis matched the reports.
- startup order and `startup_command_position_order` remained valid.
- reverse_solving strict freshness semantics remained intact.

Remaining limitation from the previous round:

- `baseline_capture_order` was WARN because `reverse_agent/project_gate.py` and `tests/test_project_gate.py` overlapped between startup baseline dirty files and files_changed.

Existing job capability to build on:

- `reverse_agent/project_jobs.py` already defines `JOB_STATUSES`, `JOB_RUNNER_KINDS`, required fields, permission flags, budget validation, `validate_job_payload`, `load_job_file`, and `validate_job_file`.
- `tests/test_project_jobs.py` already covers valid non-dispatching contracts, missing fields, unknown status rejection, dispatch/remote mutation rejection, and JSON file validation.
- This round must extend that foundation, not replace it.

Artifact freshness:

- `current_state.json` and `artifact_index.json` still describe sample-state and missing historical sample artifacts.
- Those sample artifacts are non-blocking for this engineering round because no sample-solving evidence is claimed.
- Do not upgrade missing/stale sample evidence to current.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full solve_reports, and repeating old runtime evidence directions.
- This round must not perform reverse-solving, sample execution, runtime probing, or full solve_reports scans.

## 3. Do Not Do

Do not modify `reverse_agent/project_gate.py` or `tests/test_project_gate.py` unless a narrow compatibility fix is absolutely required and explicitly justified in the report. The intended path is to avoid these files so the previous inherited dirty overlap does not recur.

Do not redesign `project_jobs.py`. Extend the existing validator with small, testable state-machine helpers.

Do not enable dispatch. `runner.dispatch_enabled` must remain false.

Do not allow remote mutation, LLM calls, agent dispatch, or reverse-solving permissions in job contracts.

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
3. `reverse_agent/project_gate.py` only to understand existing job validation integration; do not modify by default
4. `tests/test_project_gate.py` only if a compatibility regression appears; do not modify by default
5. `project_state/gates/execution_log.json`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/run_closeout_result.json`
8. `project_state/gates/round_baseline.json`
9. `project_state/gates/round_delta_summary.json`
10. `project_state/gates/command_plan.json`
11. existing `project_state/jobs/*.json` if present

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. What source/test files were dirty at startup, and did any of them overlap with files_changed?
2. Is `baseline_capture_order` PASS, WARN, or absent? If WARN remains, why is acceptance limited?
3. Was `reverse_agent/project_gate.py` left unmodified? If not, why was modification unavoidable?
4. Was `tests/test_project_gate.py` left unmodified? If not, why was modification unavoidable?
5. What job state-machine helpers were added to `project_jobs.py`?
6. What are the allowed job status transitions, and which invalid transitions are rejected by tests?
7. How are lock/lease metadata fields validated while keeping old job contracts compatible?
8. Does `runner.dispatch_enabled` remain false and do forbidden permission flags remain blocked?
9. Was any example job contract generated under `project_state/jobs/`, and did validation pass?
10. Did both required pytest commands exit 0, and what are their pass counts?
11. Did final-check and run-closeout pass?
12. Did hybrid execution-log provenance remain valid and non-derived-only?
13. Were forbidden paths, full solve_reports scans, reverse-solving, Web/AgentRunner/DB/queue/scheduler scope, and remote mutation avoided?

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_jobs.py`
- `tests/test_project_jobs.py`

Inspect-only by default; modify only if a narrow compatibility issue blocks tests and the report justifies it:

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
- `project_state/jobs/job_20260628_clean_baseline_and_job_state_machine_v1.json`
- `project_state/rounds/round_20260628_clean_baseline_and_job_state_machine_v1/*`

Required behavior:

1. Add a small, explicit allowed-transition table for job statuses.
2. Add a helper such as `validate_job_transition(from_status, to_status)` or equivalent.
3. Add payload-level validation for optional lock/lease metadata, while keeping existing job contracts valid when those fields are absent.
4. Ensure `READY -> RUNNING -> DONE -> FINAL_CHECKED -> AUDITED -> ACCEPTED/ACCEPTED_WITH_LIMITATIONS/REWORK_REQUIRED/BLOCKED` is supported where appropriate.
5. Ensure unsafe transitions are rejected, for example `DRAFT -> RUNNING`, terminal status back to `RUNNING`, or `ACCEPTED -> REWORK_REQUIRED` without a new job.
6. Preserve strict rejection of dispatch and remote mutation permissions.
7. Add tests for valid transitions, invalid transitions, lock/lease validation, backwards compatibility with existing minimal contracts, and safe example job file validation.
8. If an example job file is generated, it must be non-dispatching, no remote mutation, no LLM calls, no reverse-solving, and must reference current decision/round IDs.
9. Preserve hybrid execution-log provenance and status policy behavior.
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

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260628_clean_baseline_and_job_state_machine_v1 --mode execute
python -m pytest tests/test_project_jobs.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260628_clean_baseline_and_job_state_machine_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls, except it must not override startup-first ordering, pytest summary consistency, baseline warning honesty, hybrid provenance preservation, or closeout consistency.

Write all top-level commands and exit codes to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- decision_meta is invalid;
- status is not APPROVED;
- mainline is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or unsafe;
- implementation requires forbidden path mutation;
- implementation requires modifying `reverse_agent/project_gate.py` or `tests/test_project_gate.py` for anything broader than a narrow compatibility fix;
- implementation requires Web UI, AgentRunner, external dispatch, database, queue, scheduler, automatic remote writes, GitHub Actions mutation, or sample-solving work.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- `execution_log.json` regresses to derived-only while report/final-check claims pure `ACCEPTED`;
- baseline_capture_order remains WARN while report/final-check claims pure `ACCEPTED`;
- source/test files dirty at startup overlap with files_changed and the limitation is not reported;
- job status transitions are not implemented or not tested;
- invalid job transitions are accepted;
- job lock/lease validation breaks existing minimal job contracts;
- dispatch or remote mutation permissions become allowed;
- report-summary synthesis and report summaries disagree;
- final-check fails unexpectedly;
- run-closeout fails;
- startup transcript order regresses;
- reverse_solving strict freshness semantics regress;
- preservation-only workflows are redesigned;
- forbidden paths are modified;
- tests fail.
