```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260630_local_runner_dry_run_foundation_v1",
  "round_id": "round_20260630_local_runner_dry_run_foundation_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_accepted_decision_id": "decision_20260629_job_orchestration_foundation_v1",
  "previous_accepted_round_id": "round_20260629_job_orchestration_foundation_v1",
  "previous_accepted_audit_outcome": "ACCEPTED",
  "supersedes_unexecuted_decision_id": "decision_20260630_runner_contract_command_coverage_v1",
  "supersedes_unexecuted_round_id": "round_20260630_runner_contract_command_coverage_v1",
  "phase_label": "phase_2_20_local_agent_runner_dry_run_foundation",
  "primary_goal": "Build a local non-dispatching AgentRunner dry-run foundation that consumes job artifacts, runner contracts, and command-plan evidence to produce a deterministic execution preview, lifecycle validation, dry-run result artifact, and final-check evidence without executing commands or invoking external runners.",
  "command_plan_authority_required": true,
  "accepted_requires_startup_snapshot_artifact": true,
  "accepted_requires_clean_source_test_start": true,
  "accepted_requires_job_orchestration_artifact": true,
  "accepted_requires_runner_contract_artifact": true,
  "accepted_requires_runner_contract_required_command_coverage": true,
  "accepted_requires_runner_contract_omitted_command_preservation": true,
  "accepted_requires_runner_contract_write_scope_alignment": true,
  "accepted_requires_agent_runner_dry_run_artifact": true,
  "accepted_requires_dry_run_no_command_execution": true,
  "accepted_requires_dry_run_no_external_invocation": true,
  "accepted_requires_dry_run_lifecycle_validation": true,
  "accepted_requires_control_plane_runner_readiness_evidence": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_agent_runner.py",
    "tests/test_project_runner_contract.py",
    "tests/test_project_jobs.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_gate.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_audits.py",
    "reverse_agent/project_rounds.py",
    "reverse_agent/project_state.py",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/README.md",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/jobs/job_20260630_local_runner_dry_run_foundation_v1.json",
    "project_state/gates/agent_runner_dry_run_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/control_plane_snapshot.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/job_orchestration_result.json",
    "project_state/gates/jobs_inventory_result.json",
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
    "project_state/rounds/round_20260630_local_runner_dry_run_foundation_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/README.md",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    "solve_reports/*"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Local AgentRunner Dry-Run Foundation v1**.

This decision deliberately supersedes the narrower `decision_20260630_runner_contract_command_coverage_v1`. The command coverage work is still required, but it is no longer the whole round. This round should move one layer further toward the future Web/AgentRunner architecture while remaining safe, local, deterministic, and auditable.

The target is a local dry-run runner layer that can consume existing project-state evidence and prove that the system is ready to hand a job to a future executor without actually executing that job.

Required capabilities:

1. Create or extend a local runner module, preferably `reverse_agent/project_agent_runner.py`, that models a **non-executing dry-run AgentRunner**.
2. The dry-run runner must consume:
   - current `decision_packet.md` metadata;
   - a validated job artifact;
   - `project_state/gates/command_plan.json`;
   - `project_state/gates/runner_contract_result.json` or a freshly built runner contract payload.
3. The dry-run runner must generate a deterministic artifact, `project_state/gates/agent_runner_dry_run_result.json`, showing what a future runner would be allowed to execute, what it is forbidden to execute, what files it may write, what lifecycle transition would be attempted, and why no real execution occurred.
4. Harden runner contract validation at the same time:
   - `allowed_commands` must completely cover required `command_plan.commands`;
   - commands outside command-plan must still be rejected;
   - omitted commands must remain forbidden and must not appear in `allowed_commands`;
   - `allowed_write_paths` must be bounded to approved job/gate/report artifacts and must reject source/test/workflow/prompt/skill/solve_reports/remote paths.
5. Extend job lifecycle validation enough for a dry-run handoff:
   - the dry-run can validate a proposed transition such as `DRAFT -> READY` or `READY -> DRY_RUN_PLANNED` if the existing status model supports it;
   - if the existing status model does not support a new terminal/nonterminal dry-run state, preserve the existing status model and represent dry-run state only in the dry-run result artifact;
   - do not break older job artifacts.
6. Extend `project_gate.py` with an `agent-runner-dry-run` gate command or equivalent current-round gate entry.
7. Extend `final-check` so ACCEPTED is blocked if the dry-run artifact is missing, stale, executable, dispatch-enabled, command-plan-incomplete, write-scope-widened, or externally invoking.
8. Extend control-plane evidence if necessary so it can report local dry-run readiness separately from real dispatch readiness.
9. Keep all work local. No command execution through the dry-run runner. No model API calls. No GitHub Actions triggers. No Web server. No database. No queue daemon. No scheduler. No background worker. No reverse-solving.

This is still an `engineering_branch` round. It is intentionally larger than the prior contract-only plan, but it must remain one coherent engineering slice: **job + runner contract + dry-run runner + gate evidence + final-check closure**.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by this `project_state/decision_packet.md`. `project_state/task_packet.json` is background only and must not drive implementation.

The previous accepted engineering round was `decision_20260629_job_orchestration_foundation_v1`. It created the non-dispatching job orchestration foundation, deterministic job artifact generation, runner contract generation, gate evidence, and final-check integration.

The narrower decision `decision_20260630_runner_contract_command_coverage_v1` was uploaded but is superseded before execution by this decision. Codex must not execute that superseded decision as a separate authority. Its useful requirements are absorbed into this larger dry-run runner foundation.

Current existing capabilities to reuse:

- `project_jobs.py` already has job validation, status handling, runner fields, dangerous permission checks, and jobs inventory behavior.
- `project_runner_contract.py` already builds and validates non-executable runner contracts from decision/job/command-plan evidence.
- `project_gate.py` already exposes gate commands for command-plan, job orchestration, runner contract, control-plane snapshot, final-check, execute-decision, execution-log, report-summary, and closeout.
- Existing tests cover project jobs, runner contract baseline behavior, control plane, gate behavior, state gate, and final-check behavior.

Current gaps to close in this round:

- There is no first-class local AgentRunner dry-run consumer.
- The runner contract is a representation artifact, but there is not yet a consumer that proves future runner handoff semantics without executing.
- Command coverage must be strict, not only non-expansive.
- Omitted commands must remain visible to future runners as forbidden commands.
- Allowed write paths need explicit bounded validation before a future runner can safely consume a contract.
- final-check must recognize dry-run runner readiness evidence while still blocking real dispatch.

Artifact freshness rules:

- Current-round artifacts must carry `decision_20260630_local_runner_dry_run_foundation_v1` and `round_20260630_local_runner_dry_run_foundation_v1`.
- Historical sample artifacts marked `missing`, `stale`, or unknown must remain historical/background and must not be used as current evidence.
- Existing job artifacts from older rounds may be used only to understand schema compatibility; the current accepted evidence must be regenerated for this round.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, budget-only expansion, compare_semantics_agree=false frontier reuse, full solve_reports commits, and old runtime-branch repetition.
- This round does not solve a sample, run a sample, debug a binary, probe runtime behavior, or read full solve_reports, so it must not repeat blocked reverse-solving directions.

Command-plan policy:

- `command-plan` is the execution authority.
- Codex may inspect this decision and generate command-plan evidence, but it must execute only commands authorized by command-plan.
- If the Tests section and command-plan conflict, command-plan controls the executable command list, except startup-first ordering, startup snapshot, clean source/test baseline, no real execution, no dispatch, no remote mutation, dry-run artifact generation, final-check, and closeout consistency remain mandatory.

## 3. Do Not Do

Do not implement a real external runner. The dry-run runner must not spawn Codex, Trae, Claude Code, Aider, shell subprocesses, GitHub Actions, API calls, browser automation, or any external executor.

Do not execute the command-plan through the dry-run runner. It may list allowed commands, validate them, and write a dry-run preview, but it must not run them.

Do not enable dispatch. Any field named `dispatch_enabled`, `can_dispatch`, `allow_agent_dispatch`, `executable`, `external_invocation`, `remote_mutation`, or equivalent must remain false for the dry-run runner.

Do not create a Web UI, API Planner, API Auditor, database, queue daemon, scheduler, worker process, message bus, Kubernetes workflow, or long-running service.

Do not trigger GitHub Actions or mutate workflow files.

Do not modify prompt docs, `.codex-skills/`, `current_state.json`, `task_packet.json`, `artifact_index.json`, or `negative_results.json`.

Do not read full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full `project_state/rounds/`.

Do not perform reverse-solving, sample execution, runtime probe, dynamic debugging, emulator execution, hook execution, or binary analysis in this round.

Do not claim the system can run unattended. This round proves only local dry-run readiness and evidence closure.

Do not weaken old protections from the accepted job orchestration round: runner kind remains non-external, dangerous permissions remain false, command-plan remains authoritative, omitted commands stay forbidden, report-summary must match, final-check must pass, and closeout must converge.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly instructs the executor to upload execution results.

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

Then inspect implementation and gate/test files:

1. `reverse_agent/project_jobs.py`
2. `reverse_agent/project_runner_contract.py`
3. `reverse_agent/project_control_plane.py`
4. `reverse_agent/project_gate.py`
5. `tests/test_project_jobs.py`
6. `tests/test_project_runner_contract.py`
7. `tests/test_project_control_plane.py`
8. `tests/test_project_gate.py`
9. `tests/test_project_state.py`

Then inspect current gate artifacts as bounded evidence:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/job_orchestration_result.json`
3. `project_state/gates/jobs_inventory_result.json`
4. `project_state/gates/runner_contract_result.json`
5. `project_state/gates/control_plane_snapshot.json`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/execution_log.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/report_summary_synthesis.json`
10. `project_state/gates/startup_snapshot.json`
11. `project_state/gates/round_baseline.json`
12. `project_state/jobs/job_20260629_job_orchestration_foundation_v1.json`

Create and inspect, if needed:

1. `reverse_agent/project_agent_runner.py`
2. `tests/test_project_agent_runner.py`
3. `project_state/jobs/job_20260630_local_runner_dry_run_foundation_v1.json`
4. `project_state/gates/agent_runner_dry_run_result.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer every item with `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`, and cite concrete files or generated artifact fields:

1. Did startup checks run first and confirm `F:\reverse-agent` as repository root?
2. Was startup source/test baseline clean before implementation?
3. Is decision metadata valid: APPROVED, engineering_branch, active `reverse-agent-iteration@v2`?
4. Did Codex treat `decision_packet.md` as the only execution authority and treat `task_packet.json` as background only?
5. Was the narrower `decision_20260630_runner_contract_command_coverage_v1` treated as superseded rather than independently executed?
6. Were existing job/runner/control-plane/gate capabilities reused instead of reimplemented from scratch?
7. Was a local dry-run AgentRunner module or equivalent implementation added with no external runner invocation?
8. Does the dry-run consume decision metadata, job artifact, command-plan evidence, and runner contract evidence?
9. Does the dry-run artifact include current `decision_id` and `round_id`?
10. Does the dry-run artifact explicitly state that no commands were executed?
11. Does the dry-run artifact expose allowed commands, forbidden commands, omitted commands, allowed write paths, and blocked execution reasons?
12. Does runner contract validation fail when any required command-plan command is absent from `allowed_commands`?
13. Does runner contract validation fail when `allowed_commands` contains a command outside command-plan?
14. Does runner contract validation fail when omitted commands appear in `allowed_commands`?
15. Are omitted commands preserved as forbidden commands with enough reason/provenance for audit?
16. Does runner contract validation reject unrelated write paths such as source, tests, workflows, prompt docs, skills, solve_reports, absolute paths, parent traversal, URLs, or remote mutation paths?
17. Does job lifecycle validation remain backward-compatible with older job artifacts?
18. If a dry-run lifecycle state is introduced, is it local/evidence-only and non-executable?
19. Does `project_gate.py` expose an `agent-runner-dry-run` gate or equivalent current-round gate check?
20. Does final-check fail when `agent_runner_dry_run_result.json` is missing, stale, executable, dispatch-enabled, externally invoking, command-incomplete, or write-scope widened?
21. Does control-plane evidence distinguish dry-run readiness from real dispatch readiness?
22. Do all dispatch/executable/external invocation flags remain false?
23. Were forbidden files and preserve-only files not modified?
24. Were full solve_reports scans, runtime probes, reverse-solving, Web/API/DB/queue/scheduler work, GitHub Actions mutation, and remote mutation avoided?
25. Did required pytest commands exit 0, with pass counts recorded in `pytest_result.txt`?
26. Did `report_summary_fields_match_synthesis` pass with no diffs?
27. Did `execute_decision_contract` pass?
28. Did `execution_log` provenance remain non-derived-only and current-round aligned?
29. Did `run-closeout` exit 0 with `closeout_status: PASSED` and `close_round_result.close_status: CLOSED`?
30. Did `closeout_nested_failures_absent` pass?
31. Does `codex_report_summary` match `pytest_result.txt`, generated artifacts, changed files, decision ID, and round ID?

## 6. Implementation Scope

Allowed source/test files:

- `reverse_agent/project_agent_runner.py` new or existing
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_agent_runner.py` new or existing
- `tests/test_project_runner_contract.py`
- `tests/test_project_jobs.py`
- `tests/test_project_control_plane.py`
- `tests/test_project_gate.py`

Preserve-only files:

- `reverse_agent/project_audits.py`
- `reverse_agent/project_rounds.py`
- `reverse_agent/project_state.py`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/README.md`
- `.github/workflows/decision-preflight.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`

Allowed generated or updated artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/jobs/job_20260630_local_runner_dry_run_foundation_v1.json`
- `project_state/gates/agent_runner_dry_run_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/control_plane_snapshot.json`
- `project_state/gates/execution_report_auto_summary.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/job_orchestration_result.json`
- `project_state/gates/jobs_inventory_result.json`
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
- `project_state/rounds/round_20260630_local_runner_dry_run_foundation_v1/*`

Required implementation behavior:

1. Add a dry-run runner representation that is file-based, deterministic, side-effect bounded, and non-executing.
2. It must validate the runner contract before producing dry-run output.
3. It must validate command coverage, forbidden omitted commands, write paths, dispatch flags, executable flags, and external invocation flags.
4. It must produce `agent_runner_dry_run_result.json` with a clear status schema, current IDs, inputs consumed, planned command count, forbidden command count, allowed write paths, non-execution proof fields, lifecycle preview, and validation details.
5. It must fail closed. Missing job, stale contract, mismatched decision/round, incomplete command coverage, unsafe write path, dispatch enabled, executable true, or external invocation true must produce a failed dry-run result and block final-check.
6. If job lifecycle state definitions are extended, extension must be backward-compatible and covered by tests.
7. If control-plane snapshot is extended, it must report local dry-run readiness separately from real dispatch readiness.
8. Tests must include positive dry-run, stale/mismatched artifact negative case, command-incomplete negative case, unsafe write-path negative case, dispatch/executable negative case, and final-check blocking negative case.

## 7. Tests

Startup checks must run first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
```

If startup detects dirty source/test files under `reverse_agent/` or `tests/`, stop with `BLOCKED` before changing files.

Then run command-plan authorized execution. At minimum, the command-plan should authorize the equivalent of:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate jobs-inventory --state-dir project_state
python -m reverse_agent.project_gate job-orchestration --state-dir project_state
python -m reverse_agent.project_gate runner-contract --state-dir project_state
python -m reverse_agent.project_gate agent-runner-dry-run --state-dir project_state
python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state
python -m pytest tests/test_project_agent_runner.py tests/test_project_runner_contract.py tests/test_project_jobs.py tests/test_project_control_plane.py tests/test_project_gate.py -q
python -m pytest tests/test_project_state.py tests/test_project_reports.py tests/test_project_rounds.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260630_local_runner_dry_run_foundation_v1 --mode execute
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260630_local_runner_dry_run_foundation_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The concrete command list must come from command-plan. Do not run commands outside command-plan. If the `agent-runner-dry-run` command does not exist at the beginning of the round, implement it before the final command-plan/final-check cycle and record both pre-implementation and post-implementation gate evidence as appropriate.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately with `BLOCKED` if:

- startup cannot confirm `F:\reverse-agent` and repository root;
- startup source/test baseline is dirty;
- startup snapshot cannot be generated before implementation;
- decision metadata is invalid;
- skill profile is not active;
- command-plan is missing or unsafe;
- the task requires real runner dispatch, external model calls, GitHub Actions triggers, remote mutation, Web/API/DB/queue/scheduler work, or reverse-solving;
- the implementation requires mutating forbidden paths or full solve_reports.

Stop with `REWORK_REQUIRED` if:

- any required pytest or gate command exits nonzero;
- `project_agent_runner.py` or equivalent dry-run implementation executes commands or spawns external processes;
- dry-run artifact is missing, stale, decision/round mismatched, executable, dispatch-enabled, or externally invoking;
- runner contract permits missing required command-plan commands;
- runner contract permits command-plan outside commands;
- runner contract permits omitted commands as allowed commands;
- omitted commands are not preserved as forbidden commands;
- allowed write paths include source/test/workflow/prompt/skill/solve_reports/absolute/path-traversal/URL/remote paths;
- final-check does not block invalid dry-run evidence;
- control-plane readiness conflates dry-run readiness with real dispatch readiness;
- old job artifacts or stale sample artifacts are treated as current accepted evidence;
- `codex_execution_report.md` omits required audit answers;
- `pytest_result.txt` does not match actual commands or exit codes;
- `report_summary_fields_match_synthesis` fails;
- `execute_decision_contract` fails;
- `execution_log` provenance becomes derived-only while claiming success;
- `run-closeout` exits nonzero or close status is not CLOSED;
- nested failure scan finds active FAILED/FAIL states;
- Codex modifies GitHub workflows, prompts, skills, task/current/artifact/negative state, solve_reports, or remote state.
