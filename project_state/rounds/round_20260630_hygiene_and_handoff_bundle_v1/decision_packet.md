```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260630_hygiene_and_handoff_bundle_v1",
  "round_id": "round_20260630_hygiene_and_handoff_bundle_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260630_local_runner_dry_run_foundation_v1",
  "previous_round_id": "round_20260630_local_runner_dry_run_foundation_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_21_hygiene_and_runner_handoff_bundle",
  "primary_goal": "Fix startup-snapshot ordering and artifact taxonomy limitations while advancing the local non-executing runner chain from dry-run evidence to a sealed handoff bundle plus replay validation artifact.",
  "command_plan_authority_required": true,
  "accepted_requires_startup_snapshot_immediate_after_startup_status": true,
  "accepted_requires_no_preflight_before_startup_snapshot": true,
  "accepted_requires_artifact_role_taxonomy": true,
  "accepted_requires_generated_artifacts_exclude_historical_only_artifacts": true,
  "accepted_requires_agent_runner_dry_run_artifact": true,
  "accepted_requires_handoff_bundle_artifact": true,
  "accepted_requires_handoff_bundle_replay_validation": true,
  "accepted_requires_handoff_bundle_non_executable": true,
  "accepted_requires_no_command_execution": true,
  "accepted_requires_no_external_invocation": true,
  "accepted_requires_control_plane_handoff_readiness_evidence": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_agent_runner.py",
    "tests/test_project_runner_contract.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_jobs.py",
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
    "project_state/gates/agent_runner_dry_run_result.json",
    "project_state/gates/agent_runner_handoff_bundle.json",
    "project_state/gates/agent_runner_handoff_validation.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
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
    "project_state/jobs/job_20260630_hygiene_and_handoff_bundle_v1.json",
    "project_state/rounds/round_20260630_hygiene_and_handoff_bundle_v1/*"
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

Implement **Hygiene and Local Runner Handoff Bundle v1**.

This round is intentionally a combined repair-and-progress round. It must fix the two limitations from the latest audit and then advance the non-executing runner chain one layer beyond dry-run preview.

Repair goals:

1. Enforce startup ordering: after `Set-Location`, `Get-Location`, `Test-Path`, `git rev-parse --show-toplevel`, and `git status --short`, the first gate command must be `python -m reverse_agent.project_gate startup-snapshot --state-dir project_state`. No `preflight`, `command-plan`, `final-check`, or other project gate command may appear before startup-snapshot in accepted evidence.
2. Add or harden final-check/run-closeout validation so a `SUCCESS` / `ACCEPTED` report is blocked when startup-snapshot is delayed or when preflight appears before startup-snapshot.
3. Introduce clear artifact role taxonomy in report summaries and report-summary synthesis. The taxonomy must distinguish at least:
   - `generated_artifacts` or `generated_or_updated_artifacts` for artifacts actually created or updated this round;
   - `referenced_artifacts` for read-only supporting evidence;
   - `historical_nonblocking_artifacts` for stale or old gate/sample artifacts;
   - `archived_artifacts` for files copied into `project_state/rounds/<round_id>/` during closeout.
4. Keep backward compatibility with existing `generated_artifacts`, but stop treating stale/historical-only gate artifacts as generated current-round artifacts.

Progress goals:

1. Advance the local non-executing runner chain from `agent_runner_dry_run_result.json` to a sealed **handoff bundle**.
2. Add an artifact such as `project_state/gates/agent_runner_handoff_bundle.json` that contains a deterministic future-runner handoff packet derived from current decision metadata, job artifact, command-plan, runner contract, dry-run result, and control-plane snapshot.
3. Add a replay validation artifact such as `project_state/gates/agent_runner_handoff_validation.json` that verifies the handoff bundle against current local artifacts without executing commands.
4. The bundle must include artifact digests or equivalent stable fingerprints for consumed inputs, explicit non-execution policy, dispatch prohibition, allowed command preview, forbidden/omitted command evidence, allowed write paths, and control-plane readiness summary.
5. The replay validator must fail closed on stale IDs, digest mismatch, missing input artifacts, executable or dispatch-enabled flags, external invocation flags, unsafe write paths, command-plan mismatch, dry-run mismatch, or real dispatch readiness being true.
6. Extend `project_gate.py` with `agent-runner-handoff-bundle` and/or `agent-runner-handoff-validate` gates, or an equivalent single gate that writes both bundle and validation artifacts.
7. Extend final-check so ACCEPTED is blocked if the handoff bundle or replay validation artifact is missing, stale, invalid, executable, dispatch-enabled, externally invoking, or inconsistent with current dry-run and runner contract evidence.
8. Extend control-plane evidence so it distinguishes `local_dry_run_ready`, `handoff_bundle_ready`, `handoff_replay_validated`, and `real_dispatch_readiness`.

This remains an `engineering_branch` round. It does not implement real AgentRunner execution. It does not call Codex, Trae, Claude Code, Aider, model APIs, GitHub Actions, Web services, databases, queues, schedulers, or reverse-solving tools.

Preferred final outcome:

- `codex_report_summary.status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `pytest_result_summary.status: PASSED`.
- `startup-snapshot` is the first gate command after the five startup status commands in the recorded pytest result.
- `report_summary_fields_match_synthesis: PASS`.
- `agent_runner_dry_run_result.json: PASSED`.
- `agent_runner_handoff_bundle.json` is current and non-executable.
- `agent_runner_handoff_validation.json` is current and `PASSED`.
- `final-check: PASSED` after closeout.
- `run-closeout: PASSED`, close-round `CLOSED`, no active warnings, no nested FAIL/FAILED states.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by this `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only and still refers to the older `samplereverse` sample state; it must not drive this engineering round.

Latest audited round:

- `decision_20260630_local_runner_dry_run_foundation_v1` / `round_20260630_local_runner_dry_run_foundation_v1` was audited as `ACCEPTED_WITH_LIMITATIONS`.
- The accepted work added `reverse_agent/project_agent_runner.py`, generated `agent_runner_dry_run_result.json`, hardened runner contract command coverage and write-path checks, extended control-plane dry-run readiness, and passed final-check and run-closeout.
- The accepted work remained local and non-executing: no subprocess, no external runner, no model API, no GitHub Actions trigger, no remote mutation, and no reverse-solving.

Limitations to fix from latest audit:

1. `startup-snapshot` was not recorded as the first gate command after the five startup status commands; `preflight --allow-consumed` appeared before it in the transcript. Current final-check accepted this because the source/test baseline was clean, but the next policy must harden the ordering.
2. `generated_artifacts` still mixed current generated artifacts with historical or generic gate artifacts. The report should separate generated/updated, referenced, historical_nonblocking, and archived artifacts.

Existing capability to reuse:

- `project_agent_runner.py` builds a deterministic local dry-run preview without executing commands.
- `project_runner_contract.py` validates command coverage, omitted command preservation, write path scope, executable/dispatch flags, and external invocation flags.
- `project_gate.py` already has gate plumbing for command-plan, job-orchestration, runner-contract, agent-runner-dry-run, control-plane-snapshot, final-check, execution-log, report-summary, run-closeout, and close-round.
- `project_control_plane.py` already distinguishes local dry-run readiness from real dispatch readiness.
- Tests already cover runner contract negative cases and dry-run fail-closed behavior.

Artifact freshness:

- Current-round artifacts must carry `decision_20260630_hygiene_and_handoff_bundle_v1` and `round_20260630_hygiene_and_handoff_bundle_v1`.
- Historical audit inventory, phase1, policy lint, state hygiene, and sample artifacts may be referenced only as read-only or historical/nonblocking unless actually regenerated in this round.
- Existing `missing` sample artifacts in `artifact_index.json` remain nonblocking historical backlog for this engineering round.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, compare_semantics_agree=false frontier reuse, full solve_reports commits, and repeated old runtime candidate branches.
- This round must not run samples, solve a reverse challenge, read full solve_reports, run runtime probes, or modify negative_results.

Command-plan policy:

- `command-plan` is the command execution authority.
- Codex may only execute commands authorized by command-plan.
- The ordering invariant is stricter than ordinary command-plan flexibility: the first six recorded command blocks must be the five startup status commands followed immediately by startup-snapshot.
- If Tests and command-plan conflict, command-plan controls the exact command list, but it must not override startup-first ordering, startup-snapshot immediacy, clean source/test baseline, artifact role taxonomy, no real execution, no dispatch, no external invocation, final-check, or closeout consistency.

## 3. Do Not Do

Do not implement real AgentRunner execution.

Do not spawn shell subprocesses from `project_agent_runner.py` or the handoff bundle builder/validator.

Do not call Codex CLI, Trae, Claude Code, Aider, model APIs, browser automation, GitHub Actions, remote services, or external runners.

Do not execute command-plan commands through the handoff bundle or replay validator. They may list, fingerprint, and validate commands; they must not run them.

Do not enable dispatch. `dispatch_enabled`, `can_dispatch`, `allow_agent_dispatch`, `executable`, `external_invocation`, `remote_mutation`, and equivalent flags must remain false.

Do not create a Web UI, API Planner, API Auditor, database, queue daemon, scheduler, worker process, message bus, Kubernetes workflow, or long-running service.

Do not modify GitHub workflows, prompt docs, `.codex-skills/`, `current_state.json`, `task_packet.json`, `artifact_index.json`, or `negative_results.json`.

Do not read full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full `project_state/rounds/`.

Do not perform reverse-solving, sample execution, runtime probe, dynamic debugging, emulator execution, hook execution, or binary analysis.

Do not weaken old protections from previous accepted rounds: command-plan remains authority, omitted commands stay forbidden, write paths remain bounded, report-summary must converge, final-check must pass, closeout must converge.

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

Inspect implementation and tests:

1. `reverse_agent/project_agent_runner.py`
2. `reverse_agent/project_runner_contract.py`
3. `reverse_agent/project_control_plane.py`
4. `reverse_agent/project_gate.py`
5. `tests/test_project_agent_runner.py`
6. `tests/test_project_runner_contract.py`
7. `tests/test_project_control_plane.py`
8. `tests/test_project_gate.py`
9. `tests/test_project_reports.py`
10. `tests/test_project_state.py`

Inspect bounded gate artifacts:

1. `project_state/gates/startup_snapshot.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/job_orchestration_result.json`
4. `project_state/gates/runner_contract_result.json`
5. `project_state/gates/agent_runner_dry_run_result.json`
6. `project_state/gates/control_plane_snapshot.json`
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/run_closeout_result.json`
10. `project_state/gates/execution_log.json`
11. `project_state/gates/round_baseline.json`
12. `project_state/gates/round_delta_summary.json`

Create and inspect if needed:

1. `project_state/jobs/job_20260630_hygiene_and_handoff_bundle_v1.json`
2. `project_state/gates/agent_runner_handoff_bundle.json`
3. `project_state/gates/agent_runner_handoff_validation.json`

Do not scan full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full `project_state/rounds/`.

## 5. Required Audit

The execution report must answer every item with `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`, with concrete file/artifact evidence:

1. Did the first five recorded commands exactly confirm `F:\reverse-agent`, repository root, and `git status --short`?
2. Was `startup-snapshot` the immediate sixth recorded command and the first project gate command?
3. Was `preflight` absent before startup-snapshot?
4. Did startup snapshot report `source_test_clean_start: true` before implementation?
5. Is decision metadata valid: APPROVED, engineering_branch, active `reverse-agent-iteration@v2`?
6. Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?
7. Were the two prior audit limitations explicitly fixed?
8. Did final-check fail or become capable of failing when startup-snapshot is delayed behind preflight or any other gate?
9. Did report summaries include artifact role taxonomy with generated/updated, referenced, historical_nonblocking, and archived artifacts or equivalent fields?
10. Are stale/historical-only gate artifacts excluded from current generated artifacts unless actually regenerated?
11. Does report-summary synthesis check the new artifact taxonomy and report no diffs?
12. Was the existing dry-run runner reused rather than replaced with an external runner?
13. Is `agent_runner_dry_run_result.json` current, PASSED, non-executing, and non-dispatching?
14. Was a handoff bundle artifact generated with current decision/round IDs?
15. Does the handoff bundle include stable fingerprints or digests for consumed inputs?
16. Does the handoff bundle include non-execution policy, dispatch prohibition, allowed commands, forbidden/omitted command evidence, allowed write paths, and readiness summary?
17. Was a replay validation artifact generated and did it pass?
18. Does replay validation fail closed on stale IDs, digest mismatch, missing input artifact, executable/dispatch flags, external invocation flags, unsafe write paths, or command-plan mismatch?
19. Does final-check block missing/stale/invalid handoff bundle or replay validation artifacts?
20. Does control-plane distinguish local_dry_run_ready, handoff_bundle_ready, handoff_replay_validated, and real_dispatch_readiness?
21. Are all dispatch/executable/external invocation/model/GitHub Actions/remote mutation flags false?
22. Did the implementation stay within allowed source/test files?
23. Were preserve-only and forbidden files not modified?
24. Were full solve_reports scans, runtime probes, reverse-solving, Web/API/DB/queue/scheduler work, GitHub Actions mutation, and remote mutation avoided?
25. Did required pytest commands exit 0, with pass counts recorded in `pytest_result.txt`?
26. Did `report_summary_fields_match_synthesis` pass with no diffs?
27. Did `execute_decision_contract` pass?
28. Did `execution_log` provenance remain current-round aligned and non-derived-only where required?
29. Did `run-closeout` exit 0 with `closeout_status: PASSED` and close-round `CLOSED`?
30. Did final-check pass after archive/closeout, not only before archive?
31. Did `closeout_nested_failures_absent` pass?
32. Does `codex_report_summary` match `pytest_result.txt`, generated/updated artifacts, changed files, decision ID, and round ID?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_agent_runner.py`
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_agent_runner.py`
- `tests/test_project_runner_contract.py`
- `tests/test_project_control_plane.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`

Preserve-only files:

- `reverse_agent/project_jobs.py`
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
- `project_state/jobs/job_20260630_hygiene_and_handoff_bundle_v1.json`
- `project_state/gates/agent_runner_dry_run_result.json`
- `project_state/gates/agent_runner_handoff_bundle.json`
- `project_state/gates/agent_runner_handoff_validation.json`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/command_plan.json`
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
- `project_state/rounds/round_20260630_hygiene_and_handoff_bundle_v1/*`

Required implementation behavior:

1. Add a strict startup ordering check in final-check and closeout-relevant validation.
2. Ensure command-plan generation or run-round execution recommends/records startup-snapshot immediately after the five startup status commands.
3. Add tests that fail if preflight is recorded before startup-snapshot in an accepted report.
4. Add artifact role taxonomy to report summaries and synthesis while preserving old fields for compatibility.
5. Add tests that prevent stale/historical-only artifacts from being classified as generated current-round artifacts.
6. Extend the local dry-run runner or gate layer to build a handoff bundle from current artifacts.
7. Add replay validation for the handoff bundle using local artifact IDs, digests/fingerprints, non-execution flags, command coverage, write path scope, and readiness policy.
8. Extend final-check to require valid current handoff bundle and replay validation artifacts for this decision.
9. Extend control-plane snapshot to report handoff readiness separately from real dispatch readiness.
10. Keep all runner/handoff behavior deterministic, file-based, local, and non-executing.

## 7. Tests

Startup sequence must be recorded first in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
```

Hard ordering rule:

- No `python -m reverse_agent.project_gate preflight ...` may be recorded before startup-snapshot.
- No `command-plan`, `final-check`, `jobs-inventory`, `job-orchestration`, `runner-contract`, `agent-runner-dry-run`, `agent-runner-handoff-*`, `control-plane-snapshot`, `report-summary`, `execution-log`, or `run-closeout` command may appear before startup-snapshot.
- If startup source/test files are dirty, stop with `BLOCKED` before implementation.

Then run command-plan-authorized validation. At minimum include the equivalent of:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate jobs-inventory --state-dir project_state
python -m reverse_agent.project_gate job-orchestration --state-dir project_state
python -m reverse_agent.project_gate runner-contract --state-dir project_state
python -m reverse_agent.project_gate agent-runner-dry-run --state-dir project_state
python -m reverse_agent.project_gate agent-runner-handoff-bundle --state-dir project_state
python -m reverse_agent.project_gate agent-runner-handoff-validate --state-dir project_state
python -m reverse_agent.project_gate control-plane-snapshot --state-dir project_state
python -m pytest tests/test_project_agent_runner.py tests/test_project_runner_contract.py tests/test_project_control_plane.py tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260630_hygiene_and_handoff_bundle_v1 --mode execute
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260630_hygiene_and_handoff_bundle_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If separate `agent-runner-handoff-bundle` and `agent-runner-handoff-validate` commands are not the chosen interface, use an equivalent single gate command that writes both `agent_runner_handoff_bundle.json` and `agent_runner_handoff_validation.json`, and document the equivalence in the execution report.

The concrete command list must come from command-plan. Do not run commands outside command-plan. Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately with `BLOCKED` if:

- startup cannot confirm `F:\reverse-agent` and repository root;
- startup source/test baseline is dirty;
- startup-snapshot cannot be generated immediately after the five startup status commands;
- preflight or any other gate runs before startup-snapshot;
- decision metadata is invalid;
- skill profile is not active;
- command-plan is missing or unsafe;
- the task requires real runner dispatch, external model calls, GitHub Actions triggers, remote mutation, Web/API/DB/queue/scheduler work, reverse-solving, or full solve_reports scanning;
- implementation requires mutating forbidden paths or preserve-only files.

Stop with `REWORK_REQUIRED` if:

- any required pytest or gate command exits nonzero outside expected diagnostic exit codes;
- startup-snapshot ordering is still not enforced by final-check or closeout-relevant validation;
- `generated_artifacts` still includes stale/historical-only artifacts as current generated artifacts;
- artifact taxonomy fields are missing from summaries or not checked by report-summary synthesis;
- handoff bundle artifact is missing, stale, malformed, digest-incomplete, executable, dispatch-enabled, externally invoking, or inconsistent with current dry-run/contract/command-plan evidence;
- handoff replay validation artifact is missing, stale, or not PASSED;
- replay validation does not fail closed on stale IDs, digest mismatch, missing inputs, executable/dispatch flags, external invocation flags, unsafe write paths, or command-plan mismatch;
- control-plane readiness conflates handoff readiness with real dispatch readiness;
- any runner/handoff code executes commands, spawns subprocesses, calls external services, or mutates remote state;
- stale sample or historical gate artifacts are treated as current accepted evidence;
- `codex_execution_report.md` omits Required Audit answers;
- `pytest_result.txt` does not match actual commands or exit codes;
- `report_summary_fields_match_synthesis` fails;
- `execute_decision_contract` fails;
- `execution_log` provenance regresses;
- `run-closeout` exits nonzero or close status is not CLOSED;
- final-check after archive/closeout does not pass;
- nested failure scan finds active FAILED/FAIL states;
- Codex modifies workflows, prompts, skills, task/current/artifact/negative state, solve_reports, or remote state.
