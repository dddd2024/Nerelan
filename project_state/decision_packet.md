```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260630_runner_contract_command_coverage_v1",
  "round_id": "round_20260630_runner_contract_command_coverage_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260629_job_orchestration_foundation_v1",
  "previous_round_id": "round_20260629_job_orchestration_foundation_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_19_runner_contract_command_coverage",
  "primary_goal": "Harden the non-dispatching runner contract by requiring complete command-plan coverage, explicit omitted-command preservation, and bounded write-path alignment without implementing or dispatching any real runner.",
  "command_plan_authority_required": true,
  "accepted_requires_startup_snapshot_artifact": true,
  "accepted_requires_clean_source_test_start": true,
  "accepted_requires_runner_contract_artifact": true,
  "accepted_requires_runner_contract_required_command_coverage": true,
  "accepted_requires_runner_contract_omitted_command_preservation": true,
  "accepted_requires_runner_contract_write_scope_alignment": true,
  "accepted_requires_runner_contract_non_executable": true,
  "accepted_requires_dispatch_disabled_by_default": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_runner_contract.py",
    "tests/test_project_gate.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_audits.py",
    "reverse_agent/project_rounds.py",
    "tests/test_project_jobs.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_audits.py",
    "tests/test_project_rounds.py",
    "docs/prompts/codex_execution_prompt.md",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/runner_contract_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/rounds/round_20260630_runner_contract_command_coverage_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/README.md",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_control_plane.py",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Runner Contract Command Coverage v1**.

The previous accepted round created a non-dispatching local job orchestration foundation and a runner-facing contract artifact. That foundation is sufficient as a representation layer, but it still needs stricter contract-level guarantees before any future AgentRunner, Web dispatcher, or GitHub Actions dispatcher can safely consume it.

Goal:

1. Harden `reverse_agent/project_runner_contract.py` so `validate_runner_contract_payload()` requires `allowed_commands` to exactly cover every required command from `project_state/gates/command_plan.json`, not merely avoid extra commands.
2. Keep optional/non-required command handling conservative: required command-plan commands must be present; omitted commands must remain represented as forbidden and must never appear in `allowed_commands`.
3. Add or strengthen write-path alignment checks so `allowed_write_paths` is bounded to job required outputs plus approved gate artifacts, includes required runner-contract artifacts, and does not include unrelated source/test, workflow, prompt, skill, solve_reports, or remote-mutation paths.
4. Extend `runner-contract` gate evidence and `final-check` checks so missing required command coverage, omitted-command drift, executable contracts, enabled dispatch, enabled external invocation, or widened write scope block ACCEPTED.
5. Extend tests for positive and negative cases in `tests/test_project_runner_contract.py` and, where final-check behavior is involved, `tests/test_project_gate.py`.
6. Preserve the existing non-dispatching contract. This round must not implement a real AgentRunner, must not dispatch a job, must not call Codex/Trae/Claude Code/Aider/GitHub Actions/model APIs, and must not mutate remote state beyond the user-authorized upload of this decision packet.

Preferred final outcome:

- `codex_report_summary.status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `final-check: PASSED`.
- `runner_contract_result.json` is current for this decision and reports `gate_status: PASSED`.
- Runner contract validation reports complete required command coverage, preserved forbidden omitted commands, bounded allowed write paths, `dispatch_enabled: false`, `executable: false`, and all external invocation flags false.
- `run-closeout` exits 0, close-round is `CLOSED`, and closeout has no active warnings or nested failures.

This is an `engineering_branch` round. It advances the control plane toward future AgentRunner/Web automation, but it does not implement Web UI, API Planner/Auditor, database, queue daemon, scheduler, self-hosted runner automation, GitHub Actions mutation, automatic remote writes, or reverse-solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only and still refers to older `samplereverse` missing evidence; it must not drive this engineering round.

Accepted previous round:

- `decision_20260629_job_orchestration_foundation_v1` / `round_20260629_job_orchestration_foundation_v1` was audited as `ACCEPTED`.
- The previous round added deterministic non-dispatching job planning through `project_jobs.build_planned_job_payload()`.
- The generated job artifact was DRAFT, `runner.kind: none`, `runner.dispatch_enabled: false`, and dangerous permissions were false.
- The previous round added `project_runner_contract.py` with a non-executable runner contract builder/validator.
- Current runner contract validation already rejects commands outside command-plan, rejects omitted commands in `allowed_commands`, rejects executable contracts, rejects dispatch-enabled contracts, and rejects enabled external invocations.
- Current tests cover those baseline behaviors, but the next hardening step is to require full coverage of command-plan required commands and stricter write-path boundaries.
- `project_state/gates/final_gate_result.json` from the accepted round reported `PASSED` with `job_orchestration_artifact`, `runner_contract_artifact`, `execution_log_consistency`, `execution_log_provenance_valid`, `forbidden_paths_absent`, and closeout checks passing.

Existing capability to build on:

- `reverse_agent/project_runner_contract.py` already builds a contract from decision metadata, a validated job payload, and `command_plan.json`.
- `reverse_agent/project_gate.py` already exposes `runner-contract`, reads `runner_contract_result.json`, and checks current IDs, non-executable status, dispatch status, allowed/forbidden command list shape, allowed write path list shape, and external invocations.
- `tests/test_project_runner_contract.py` already contains positive and negative coverage for command-plan packaging, outside-command rejection, omitted-command rejection, executable-contract rejection, and external invocation rejection.
- `project_jobs.py` already validates non-dispatching job payloads and must be preserved rather than rewritten.

Artifact freshness:

- `runner_contract_result.json`, `command_plan.json`, `final_gate_result.json`, `execution_log.json`, `run_closeout_result.json`, and report-summary artifacts must carry this decision ID and round ID after execution.
- Historical audit/job inventory artifacts from older decisions may be treated as historical/nonblocking unless this decision explicitly requires them.
- Older sample artifacts with `missing`, `stale`, or unknown freshness may be referenced only as backlog/context, not as current evidence.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full solve_reports, and repeating old bounded runtime branches.
- This round does not perform reverse-solving, runtime probing, dynamic debugging, sample execution, or full solve_reports scans, so it must not repeat any blocked sample-solving direction.

Allowed tool scope:

- It is allowed to run bounded local project gate commands and pytest commands authorized by command-plan.
- It is allowed to update generated current-round gate/report/pytest/round artifacts listed in the decision contract.
- It is not allowed to dispatch a job, acquire a live runner, call model APIs, trigger GitHub Actions, push to GitHub, create a PR, or mutate remote state unless the user separately instructs the executor to upload execution results.
- It is not allowed to read full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full `project_state/rounds/`.

## 3. Do Not Do

Do not implement a real AgentRunner. No Codex CLI adapter, Trae adapter, Claude Code adapter, Aider adapter, GitHub Action adapter, local runner daemon, workflow dispatcher, or external process dispatcher may be added in this round.

Do not enable dispatch. `runner.dispatch_enabled`, `dispatch_enabled`, `executable`, `permissions.allow_agent_dispatch`, and any control-plane `can_dispatch_next_decision` field must remain false unless a future decision explicitly enables a safe dispatch policy.

Do not call model APIs, GitHub Actions, remote services, or external runners.

Do not create a database, queue daemon, scheduler, Web UI, API Planner/Auditor service, self-hosted runner integration, or background worker.

Do not mutate GitHub workflows, prompt docs, `.codex-skills/`, `current_state.json`, `task_packet.json`, `artifact_index.json`, or `negative_results.json`.

Do not modify `project_jobs.py` or `project_control_plane.py` in this round unless a hard blocker makes the runner contract impossible to validate otherwise. Prefer a rework decision if those files truly need changes.

Do not weaken existing protections: runner contracts must not broaden command-plan, must not ignore omitted commands, must not become executable, and must not allow external invocation.

Do not add allowlists that make source/test/workflow/prompt/skill paths valid runner write targets.

Do not scan full `solve_reports/`, run samples, execute runtime probes, or perform dynamic debugging.

Do not claim `SUCCESS` or `ACCEPTED` unless final-check and run-closeout converge without active warnings or nested failures.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly instructs the executor to do so.

## 4. Files To Inspect

Read first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/execution_report.md` if present
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Then inspect implementation and gate evidence:

1. `reverse_agent/project_runner_contract.py`
2. `reverse_agent/project_gate.py`
3. `tests/test_project_runner_contract.py`
4. `tests/test_project_gate.py`
5. `project_state/gates/command_plan.json`
6. `project_state/gates/runner_contract_result.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/execution_log.json`
9. `project_state/gates/run_closeout_result.json`
10. `project_state/gates/report_summary_synthesis.json`
11. `project_state/gates/startup_snapshot.json`
12. `project_state/gates/round_baseline.json`
13. `project_state/jobs/job_20260629_job_orchestration_foundation_v1.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup snapshot generated first and was startup source/test baseline clean?
2. Did decision metadata remain valid: APPROVED, engineering_branch, and active `reverse-agent-iteration@v2` skill?
3. Did the implementation stay within `project_runner_contract.py`, `project_gate.py`, and their tests?
4. What exact runner contract coverage gap from the previous round was addressed?
5. Does `validate_runner_contract_payload()` now fail when any required command-plan command is absent from `allowed_commands`?
6. Does it still fail when `allowed_commands` contains a command outside command-plan?
7. Does it still fail when an omitted command-plan command appears in `allowed_commands`?
8. Does the runner contract preserve omitted commands as `forbidden_commands`, including kind/command/reason where available?
9. Does the runner contract validate that `allowed_write_paths` is a bounded set derived from job required outputs plus approved runner-contract gate artifacts?
10. Does runner contract validation reject unrelated write paths such as `reverse_agent/*.py`, `tests/*.py`, `.github/workflows/*`, `.codex-skills/*`, `docs/prompts/*`, `solve_reports/*`, or remote-mutation paths?
11. Does `runner_contract_result.json` expose command coverage status, omitted-command preservation status, and write-scope validation status or equivalent evidence?
12. Does final-check include runner contract command coverage and write-scope checks, or otherwise fail when `runner_contract_result.json` records those failures?
13. Does the runner contract remain non-executable with `dispatch_enabled: false`, `executable: false`, and all external invocation flags false?
14. Were `project_jobs.py` and `project_control_plane.py` preserved unless explicitly justified by a blocker?
15. Were stale optional inventory artifacts labeled historical/nonblocking rather than current evidence?
16. Did required pytest commands exit 0, and what are their pass counts?
17. Did `report_summary_fields_match_synthesis` pass with no diffs?
18. Did `execute_decision_contract` pass?
19. Did `run-closeout` exit 0, with `closeout_status: PASSED` and `close_round_result.close_status: CLOSED`?
20. Did `closeout_nested_failures_absent` pass with no active nested FAILED/FAIL states?
21. Did hybrid execution-log provenance remain valid and non-derived-only?
22. Were forbidden paths, preserve-only files, full solve_reports scans, Web/AgentRunner/DB/queue/scheduler scope, GitHub Actions mutation, and remote mutation avoided?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_runner_contract.py`
- `tests/test_project_gate.py`

Preserve-only source/test/docs/workflow files:

- `reverse_agent/project_jobs.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_audits.py`
- `reverse_agent/project_rounds.py`
- `tests/test_project_jobs.py`
- `tests/test_project_control_plane.py`
- `tests/test_project_audits.py`
- `tests/test_project_rounds.py`
- `docs/prompts/codex_execution_prompt.md`
- `.github/workflows/decision-preflight.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`

Allowed generated or updated state artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/execution_report_auto_summary.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/execution_log.json`
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
- `project_state/gates/runner_contract_result.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/rounds/round_20260630_runner_contract_command_coverage_v1/*`

Required behavior:

1. Extend runner contract validation to compute required command-plan command coverage.
2. A contract must fail validation if a required command from `command_plan.commands` is missing from `allowed_commands`.
3. A contract must still fail validation if `allowed_commands` contains any command outside `command_plan.commands`.
4. A contract must still fail validation if `allowed_commands` includes any command from `omitted_commands`.
5. Omitted commands must be copied to `forbidden_commands` and remain visible to future runners.
6. Add write-scope validation for `allowed_write_paths`.
7. The allowed write path set must be limited to project-state job/gate/report artifacts required by the job and runner contract. It must not include source, tests, workflows, prompt docs, skills, solve_reports, or remote URLs.
8. `runner_contract_result.json` must include enough structured evidence for final-check and audit to see command coverage and write-scope status.
9. Extend final-check so an invalid runner contract coverage/write-scope result blocks ACCEPTED.
10. Keep all behavior deterministic, file-based, and local. No database, queue daemon, scheduler, Web UI, AgentRunner adapter, external service, or remote mutation.

## 7. Tests

Record startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
```

Hard startup rule:

- If `git status --short` or `startup_snapshot.json` contains dirty source/test paths under `reverse_agent/` or `tests/` before implementation, stop with `BLOCKED` before modifying any source/test file.
- Existing dirty generated state artifacts may be recorded but must not excuse source/test dirty files.

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate runner-contract --state-dir project_state
python -m pytest tests/test_project_runner_contract.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_runner_contract.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260630_runner_contract_command_coverage_v1 --mode execute
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260630_runner_contract_command_coverage_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls the concrete command list, except it must not override startup-first ordering, startup-snapshot generation, clean source/test baseline, runner contract required command coverage, omitted-command preservation, write-scope validation, report-summary convergence, execute-decision contract, hybrid provenance preservation, final-check, or closeout consistency.

Write all top-level commands and exit codes to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- startup `git status --short` shows dirty source/test files under `reverse_agent/` or `tests/`;
- `startup_snapshot.json` cannot be created as the first gate artifact;
- `startup_snapshot.json` reports source/test dirty files;
- decision_meta is invalid;
- status is not APPROVED;
- mainline is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, unsafe, or places startup commands after non-startup commands;
- implementation requires dispatching a job or invoking a runner;
- implementation requires model API calls, GitHub Actions triggers, remote mutation, Web UI, database, queue daemon, scheduler, or sample-solving work;
- implementation requires mutating `project_jobs.py`, `project_control_plane.py`, existing audit records, prompt docs, workflow files, skill files, or forbidden state files.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- startup source/test dirty baseline is ignored and implementation proceeds;
- runner contract artifact is missing or stale;
- runner contract validation allows missing required command-plan commands;
- runner contract validation allows commands outside command-plan;
- runner contract validation allows omitted commands as executable/allowed commands;
- omitted commands are not preserved as forbidden commands;
- `allowed_write_paths` accepts unrelated source/test/workflow/prompt/skill/solve_reports/remote paths;
- final-check does not include runner contract command coverage/write-scope evidence or equivalent blocking checks;
- runner contract becomes executable or enables dispatch;
- any external invocation flag is true;
- stale optional artifacts are mislabeled as current evidence;
- `report_summary_fields_match_synthesis` fails;
- `execute_decision_contract` fails;
- `run-closeout` exits nonzero;
- `close_round_result.close_status` is not `CLOSED`;
- `closeout_nested_failures_absent` fails;
- `execution_log.json` regresses to derived-only while report/final-check claims `ACCEPTED`;
- forbidden paths are modified;
- tests fail.
