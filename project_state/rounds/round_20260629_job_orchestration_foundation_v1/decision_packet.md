```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260629_job_orchestration_foundation_v1",
  "round_id": "round_20260629_job_orchestration_foundation_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260629_startup_snapshot_and_control_plane_rework_v1",
  "previous_round_id": "round_20260629_startup_snapshot_and_control_plane_rework_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_18_job_orchestration_foundation",
  "primary_goal": "Build a non-dispatching job orchestration foundation by extending existing project_jobs validation into job planning, runner contract generation, control-plane readiness, and gate evidence without implementing real AgentRunner execution.",
  "command_plan_authority_required": true,
  "accepted_requires_startup_snapshot_artifact": true,
  "accepted_requires_clean_source_test_start": true,
  "accepted_requires_job_orchestration_artifact": true,
  "accepted_requires_runner_contract_artifact": true,
  "accepted_requires_control_plane_job_readiness": true,
  "accepted_requires_dispatch_disabled_by_default": true,
  "accepted_requires_no_remote_mutation": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_jobs.py",
    "tests/test_project_runner_contract.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_gate.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_audits.py",
    "reverse_agent/project_rounds.py",
    "tests/test_project_audits.py",
    "tests/test_project_rounds.py",
    "docs/prompts/codex_execution_prompt.md",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "allowed_new_gate_artifacts": [
    "project_state/gates/job_orchestration_result.json",
    "project_state/gates/runner_contract_result.json",
    "project_state/gates/control_plane_snapshot.json"
  ],
  "allowed_new_job_artifacts": [
    "project_state/jobs/job_20260629_job_orchestration_foundation_v1.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/README.md",
    "project_state/audits/audit_20260629_rework_required_audit_inventory_gate.md",
    "project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Job Orchestration Foundation v1**.

This is a deliberately larger engineering step than a single inventory gate. The previous accepted round hardened startup evidence and made the control-plane snapshot reflect final closeout state. The next useful layer is to make the system capable of representing, validating, and preparing jobs for future runners without actually dispatching any external agent.

Goal:

1. Extend the existing `project_jobs.py` local job contract validator into a bounded job orchestration foundation.
2. Add deterministic job planning for the current active decision, producing a DRAFT/READY-safe job artifact that remains non-dispatching by default.
3. Add a runner contract builder/validator that converts a validated job plus command-plan into a machine-readable `TaskContract`-style artifact for a future runner, without invoking Codex, Trae, Claude Code, Aider, GitHub Actions, or any external tool.
4. Expose the orchestration evidence through `project_gate` with bounded CLI commands such as `job-orchestration` and `runner-contract`, or equivalent names.
5. Generate current gate artifacts:
   - `project_state/gates/job_orchestration_result.json`
   - `project_state/gates/runner_contract_result.json`
   - updated `project_state/gates/control_plane_snapshot.json`
6. Optionally generate a single local job artifact:
   - `project_state/jobs/job_20260629_job_orchestration_foundation_v1.json`
7. Integrate job orchestration and runner contract evidence into final-check or an equivalent gate evidence path.
8. Extend control-plane snapshot so it can summarize job queue status, runner contract readiness, and dispatch safety for UI/runner consumers.
9. Keep dispatch disabled by default. This round must not run an AgentRunner, not call model APIs, not trigger GitHub Actions, not push/PR, and not execute any command outside command-plan.

Preferred final outcome:

- `codex_report_summary.status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `limitations` absent or empty.
- startup snapshot and startup-first ordering remain valid from the previous accepted round.
- job orchestration artifact is current and PASSED.
- runner contract artifact is current and PASSED.
- control-plane snapshot reports job/runner readiness accurately and keeps `can_dispatch_next_decision: false` unless explicit safe dispatch evidence exists.
- final-check is `PASSED`, not `PASSED_WITH_LIMITATIONS`.
- run-closeout exits 0, close-round is `CLOSED`, and closeout has no active warnings or nested failures.

This is an `engineering_branch` round. It advances toward Web/AgentRunner automation, but does not implement Web UI, AgentRunner adapters, API Planner/Auditor, database, queue daemon, scheduler, self-hosted runner automation, GitHub Actions mutation, automatic remote writes, or reverse-solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by `project_state/decision_packet.md` as the task contract. `project_state/task_packet.json` remains background only and still refers to older `samplereverse` missing evidence; it must not drive this engineering round.

Command execution authority remains `command-plan`: Codex may only execute commands authorized in `command-plan.commands`, and must not execute commands listed in `command-plan.omitted_commands`. If Tests and command-plan conflict, command-plan controls the concrete command list, but command-plan may not override startup-first ordering, startup snapshot hard gating, clean source/test baseline requirements, artifact freshness, report-summary convergence, final-check, or closeout requirements.

Accepted previous round:

- `decision_20260629_startup_snapshot_and_control_plane_rework_v1` / `round_20260629_startup_snapshot_and_control_plane_rework_v1` is accepted.
- `startup_snapshot.json` is current, PASSED, and records an empty `source_test_dirty_files` list.
- `round_baseline.json` is derived from startup snapshot and records no baseline dirty or untracked implementation files.
- command-plan places startup commands and startup-snapshot first.
- preflight reads startup cleanliness from startup snapshot and no longer excuses source/test dirty files through inherited dirty allowlists.
- final-check is pure `PASSED`, not `PASSED_WITH_LIMITATIONS`.
- control-plane snapshot has `snapshot_mode: final_state`, `final_state_complete: true`, `final_gate_status: PASSED`, `closeout_status: PASSED`, and `close_round_status: CLOSED`.
- runner readiness currently defaults to non-dispatching.

Existing capability to build on:

- `reverse_agent/project_jobs.py` already defines job statuses, terminal statuses, allowed status transitions, runner kinds, required fields, lock/lease validation, permission/budget validation, job payload validation, and jobs directory validation.
- Existing job validation requires `runner.dispatch_enabled` to be false and requires dangerous permission flags such as remote mutation, LLM calls, agent dispatch, and reverse solving to be false.
- `project_gate` already exposes `jobs-inventory`, `control-plane-snapshot`, startup-snapshot, preflight, command-plan, report-summary, execute-decision, execution-log, final-check, and run-closeout surfaces.
- The uploaded Web/automation architecture direction calls for a Job Manager, AgentRunner contract, command-plan authorization, execution logs, final-check, and Web/runner consumable state. This decision implements the local non-dispatching foundation for that path; it does not build the full Web or AgentRunner layer.

Artifact freshness:

- `job_orchestration_result.json`, `runner_contract_result.json`, and `control_plane_snapshot.json` must carry this decision ID and round ID.
- Existing jobs/audit inventory artifacts from older decisions may be treated as historical/nonblocking, not current evidence.
- Older sample artifacts with `missing`, `stale`, or unknown freshness may be referenced only as backlog/context, not as current evidence.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full solve_reports, and repeating old bounded runtime branches.
- This round must not perform reverse-solving, runtime probing, dynamic debugging, sample execution, or full solve_reports scans.

Allowed tool scope:

- It is allowed to run bounded local project gate commands and pytest commands authorized by command-plan.
- It is allowed to create/update exactly one local job artifact under `project_state/jobs/` for this round if needed.
- It is allowed to create/update gate artifacts under `project_state/gates/` listed in Implementation Scope.
- It is not allowed to dispatch a job, acquire a live runner, call model APIs, trigger GitHub Actions, push to GitHub, or mutate remote state unless the user separately instructs the executor to upload.
- It is not allowed to read full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full `project_state/rounds/`.

## 3. Do Not Do

Do not implement a real AgentRunner. No Codex CLI adapter, Trae adapter, Claude Code adapter, Aider adapter, GitHub Action adapter, local runner daemon, or external process dispatcher may be added in this round.

Do not enable dispatch. `runner.dispatch_enabled`, `permissions.allow_agent_dispatch`, and any control-plane `can_dispatch_next_decision` field must remain false unless a future decision explicitly enables a safe dispatch policy.

Do not call model APIs, GitHub Actions, remote services, or external runners.

Do not create a database, queue daemon, scheduler, Web UI, API Planner/Auditor service, self-hosted runner integration, or background worker.

Do not mutate GitHub workflows or remote state.

Do not replace `project_jobs.py` from scratch. Build on the existing job schema/status/transition/permission/budget validator and extend it narrowly.

Do not treat generated job artifacts as active execution authority. The task contract remains `project_state/decision_packet.md`, and command execution authority remains `project_state/gates/command_plan.json`.

Do not let a runner contract override command-plan or broaden allowed commands. A runner contract can only package the already authorized command-plan and current decision metadata.

Do not change `current_state.json`, `task_packet.json`, `artifact_index.json`, `negative_results.json`, `.codex-skills/registry.json`, existing audit records, prompt workspace docs, or GitHub workflows.

Do not scan full `solve_reports/`, run samples, execute runtime probes, or perform dynamic debugging.

Do not downgrade startup snapshot hard gate, startup-first ordering, or clean source/test baseline behavior from the previous accepted round.

Do not claim `SUCCESS` or `ACCEPTED` unless final-check and run-closeout converge without active warnings or nested failures.

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

Then inspect implementation and gate evidence:

1. `reverse_agent/project_jobs.py`
2. `reverse_agent/project_control_plane.py`
3. `reverse_agent/project_gate.py`
4. `tests/test_project_jobs.py`
5. `tests/test_project_control_plane.py`
6. `tests/test_project_gate.py`
7. `project_state/gates/startup_snapshot.json`
8. `project_state/gates/command_plan.json`
9. `project_state/gates/preflight_result.json`
10. `project_state/gates/control_plane_snapshot.json`
11. `project_state/gates/final_gate_result.json`
12. `project_state/gates/run_closeout_result.json`
13. `project_state/gates/execution_log.json`
14. `project_state/gates/report_summary_synthesis.json`
15. `project_state/jobs/*.json`

If implementation creates a dedicated runner contract helper or tests, inspect:

1. `reverse_agent/project_runner_contract.py`
2. `tests/test_project_runner_contract.py`
3. `project_state/gates/runner_contract_result.json`
4. `project_state/gates/job_orchestration_result.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The report must answer all items with concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`:

1. Was startup snapshot generated first and was startup source/test baseline clean?
2. Did the round preserve startup snapshot hard gate and startup-first command-plan behavior?
3. What existing job validation behavior was reused from `project_jobs.py` rather than reimplemented?
4. What new job orchestration helper/gate was added, and where is it implemented?
5. Does `job_orchestration_result.json` exist, carry current decision/round IDs, and report PASSED?
6. Was at most one local job artifact created for this round, and is it DRAFT or READY-safe without dispatch?
7. Does the job artifact validate required inputs, required outputs, permissions, budgets, status, runner, lock/lease, and transitions?
8. Does job orchestration reject invalid transitions, duplicate job IDs, missing required fields, unsafe permissions, or dispatch-enabled runners?
9. What runner contract builder/validator was added, and where is it implemented?
10. Does `runner_contract_result.json` exist, carry current decision/round IDs, and report PASSED?
11. Does the runner contract package decision ID, round ID, repo path, command-plan path, allowed commands, allowed write paths, permission profile, budget profile, and dispatch-disabled policy?
12. Does the runner contract refuse commands not present in command-plan and preserve `omitted_commands` as forbidden?
13. Does the runner contract remain non-executable and avoid invoking Codex, Trae, Claude Code, Aider, GitHub Actions, local scripts, or external services?
14. Does control-plane snapshot summarize job queue status, runner contract readiness, and dispatch safety without enabling dispatch?
15. Are stale optional inventory artifacts labeled historical/nonblocking rather than current?
16. Did required pytest commands exit 0, and what are their pass counts?
17. Did `report_summary_fields_match_synthesis` pass with no diffs?
18. Did `execute_decision_contract` pass?
19. Did `run-closeout` exit 0, with `closeout_status: PASSED` and `close_round_result.close_status: CLOSED`?
20. Did `closeout_nested_failures_absent` pass with no active nested FAILED/FAIL states?
21. Did hybrid execution-log provenance remain valid and non-derived-only?
22. Were forbidden paths, preserve-only files, full solve_reports scans, Web/AgentRunner/DB/queue/scheduler scope, GitHub Actions mutation, and remote mutation avoided?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_jobs.py`
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_jobs.py`
- `tests/test_project_runner_contract.py`
- `tests/test_project_control_plane.py`
- `tests/test_project_gate.py`

Preserve-only source/test/docs files:

- `reverse_agent/project_audits.py`
- `reverse_agent/project_rounds.py`
- `tests/test_project_audits.py`
- `tests/test_project_rounds.py`
- `docs/prompts/codex_execution_prompt.md`
- `.github/workflows/decision-preflight.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`

Allowed generated or updated state artifacts:

- `project_state/jobs/job_20260629_job_orchestration_foundation_v1.json`
- `project_state/gates/job_orchestration_result.json`
- `project_state/gates/runner_contract_result.json`
- `project_state/gates/control_plane_snapshot.json`
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
- `project_state/gates/startup_snapshot.json`
- `project_state/gates/state_hygiene_inventory.json`
- `project_state/rounds/round_20260629_job_orchestration_foundation_v1/*`

Required behavior:

1. Extend `project_jobs.py` to support a deterministic non-dispatching job plan for the active decision, or add a small adjacent helper while preserving existing validation functions.
2. The generated job artifact must include schema version, job ID, decision ID, round ID, mainline, status, runner object, required inputs, required outputs, permissions, budgets, and optional lock/lease/transition fields.
3. Dangerous permission flags must remain false: remote mutation, LLM calls, agent dispatch, reverse solving, and any equivalent new flags.
4. Runner dispatch must remain disabled in both the job artifact and validation result.
5. Job orchestration must validate duplicate IDs and invalid statuses/transitions without mutating unrelated jobs.
6. Add a runner contract builder/validator that creates a non-executing TaskContract-style object from the current decision, command-plan, and validated job.
7. The runner contract must include command-plan authorized commands and forbidden omitted commands, not a free-form command list invented by the runner.
8. The runner contract must include permission/budget metadata and must state `dispatch_enabled: false` or equivalent.
9. Add `python -m reverse_agent.project_gate job-orchestration --state-dir project_state` or equivalent.
10. Add `python -m reverse_agent.project_gate runner-contract --state-dir project_state` or equivalent.
11. Extend final-check to require current job orchestration and runner contract artifacts for this decision.
12. Extend control-plane snapshot to summarize job orchestration status, runner contract status, job queue counts, ready/running job counts, and dispatch safety.
13. Preserve historical/nonblocking treatment for stale jobs/audit inventory artifacts.
14. Keep implementation deterministic, file-based, and local. No database, queue daemon, scheduler, Web UI, AgentRunner adapter, external service, or remote mutation.

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

- If `git status --short` or `startup_snapshot.json` contains dirty source/test paths under `reverse_agent/` or `tests/`, stop with `BLOCKED` before modifying any source/test file.
- Existing dirty generated state artifacts may be recorded but must not excuse source/test dirty files.

Then run command-plan-authorized validation. At minimum include:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate jobs-inventory --state-dir project_state
python -m reverse_agent.project_gate job-orchestration --state-dir project_state
python -m reverse_agent.project_gate runner-contract --state-dir project_state
python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260629_job_orchestration_foundation_v1 --mode execute
python -m pytest tests/test_project_jobs.py tests/test_project_runner_contract.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py tests/test_project_runner_contract.py tests/test_project_control_plane.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260629_job_orchestration_foundation_v1
python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state --final-state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The command-plan-authorized set is authoritative. If this Tests section conflicts with command-plan, command-plan controls the concrete command list, except it must not override startup-first ordering, startup-snapshot generation, clean source/test baseline, pytest summary consistency, job orchestration evidence, runner contract evidence, control-plane final-state evidence, report-summary convergence, execute-decision contract, hybrid provenance preservation, or closeout consistency.

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
- implementation requires mutating existing audit records or forbidden state files;
- implementation requires modifying preserve-only audit/round/workflow/prompt files.

Stop with `REWORK_REQUIRED` if:

- any required pytest command exits nonzero;
- `pytest_result_summary.status` contradicts recorded command-block exit codes;
- startup source/test dirty baseline is ignored and implementation proceeds;
- job orchestration gate command or artifact is missing;
- runner contract gate command or artifact is missing;
- generated job artifact is missing required fields or enables dispatch;
- job permissions allow remote mutation, LLM calls, agent dispatch, reverse solving, or equivalent unsafe behavior;
- invalid job transitions, duplicate job IDs, missing required fields, or unsafe runner settings are silently accepted;
- runner contract contains commands not authorized by command-plan;
- runner contract treats omitted commands as allowed;
- runner contract invokes or configures a real external runner;
- control-plane snapshot does not summarize job/runner readiness or incorrectly enables dispatch;
- stale optional artifacts are mislabeled as current evidence;
- final-check does not include job orchestration and runner contract evidence or equivalent checks;
- `report_summary_fields_match_synthesis` fails;
- `execute_decision_contract` fails;
- `run-closeout` exits nonzero;
- `close_round_result.close_status` is not `CLOSED`;
- `closeout_nested_failures_absent` fails;
- `execution_log.json` regresses to derived-only while report/final-check claims `ACCEPTED`;
- startup transcript order regresses;
- reverse_solving strict freshness semantics regress;
- forbidden paths are modified;
- tests fail.
