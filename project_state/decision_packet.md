```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260630_hygiene_handoff_rework_v1",
  "round_id": "round_20260630_hygiene_handoff_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260630_hygiene_and_handoff_bundle_v1",
  "previous_round_id": "round_20260630_hygiene_and_handoff_bundle_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_22_hygiene_handoff_rework",
  "primary_goal": "Rework the hygiene and handoff bundle round by hard-blocking dirty source/test startup baselines, fixing artifact taxonomy semantics, and repairing Required Audit answer alignment without expanding runner capabilities.",
  "command_plan_authority_required": true,
  "accepted_requires_startup_snapshot_immediate_after_startup_status": true,
  "accepted_requires_source_test_clean_start_hard_block": true,
  "accepted_requires_no_authorized_source_test_dirty_override": true,
  "accepted_requires_no_preflight_before_startup_snapshot": true,
  "accepted_requires_artifact_role_taxonomy": true,
  "accepted_requires_generated_artifacts_exclude_historical_only_artifacts": true,
  "accepted_requires_required_audit_answer_alignment": true,
  "accepted_requires_existing_handoff_bundle_validation_preserved": true,
  "accepted_requires_no_new_runner_capability": true,
  "accepted_requires_report_summary_fields_match_synthesis": true,
  "accepted_requires_execute_decision_contract_passed": true,
  "accepted_requires_run_closeout_exit_zero": true,
  "accepted_requires_closeout_nested_failures_absent": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/project_control_plane.py",
    "tests/test_project_gate.py",
    "tests/test_project_agent_runner.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_reports.py",
    "tests/test_project_state.py"
  ],
  "preserve_only_files": [
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
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
    "project_state/jobs/job_20260630_hygiene_handoff_rework_v1.json",
    "project_state/rounds/round_20260630_hygiene_handoff_rework_v1/*"
  ],
  "historical_artifacts_must_not_be_generated_unless_current_round_rebuilt": [
    "project_state/gates/phase1_completion_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/state_hygiene_inventory.json",
    "project_state/gates/audit_inventory_result.json",
    "project_state/gates/naming_migration_plan.json"
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

Implement **Hygiene Handoff Rework v1**.

This is a rework-only round after the audit of `decision_20260630_hygiene_and_handoff_bundle_v1` returned `REWORK_REQUIRED`. Do not advance new runner functionality. Preserve the existing local non-executing handoff bundle and replay validation capabilities only insofar as needed to keep current tests and final-check coherent.

Primary goals:

1. Fix startup baseline enforcement. If the startup `git status --short` contains any dirty `reverse_agent/` or `tests/` path, startup-snapshot must not report a clean source/test start. The accepted state must be blocked rather than converted into an authorized inherited dirty baseline.
2. Enforce startup command order as a hard acceptance rule. The first six recorded command blocks must be:
   - `Set-Location F:\reverse-agent`
   - `Get-Location`
   - `Test-Path F:\reverse-agent`
   - `git rev-parse --show-toplevel`
   - `git status --short`
   - `python -m reverse_agent.project_gate startup-snapshot --state-dir project_state`
3. Prevent any project gate command, including `preflight`, from appearing before startup-snapshot in an accepted transcript.
4. Fix artifact taxonomy. `generated_artifacts` and `generated_or_updated_artifacts` must contain only artifacts actually generated or updated in the current round. Historical or stale gate artifacts must be moved to `referenced_artifacts` or `historical_nonblocking_artifacts`, unless they are explicitly regenerated in this round with current decision/round provenance.
5. Fix Required Audit answer alignment. Every Required Audit item must answer its own question with directly related evidence. Template cycling or mismatched evidence must be rejected by final-check or a report-summary/Required Audit alignment check.
6. Preserve but do not expand the existing local handoff bundle/replay validation feature from the failed round. The rework may keep `agent_runner_handoff_bundle.json` and `agent_runner_handoff_validation.json` current, but it must not implement real execution, external dispatch, background runner, API calls, or Web/DB/queue/scheduler work.

Preferred final outcome:

- `codex_report_summary.status: SUCCESS`.
- `acceptance_recommendation: ACCEPTED`.
- `pytest_result_summary.status: PASSED`.
- Startup source/test baseline is clean in actual startup `git status --short`, not just reclassified by code.
- `startup_snapshot.source_test_clean_start: true` only when no dirty `reverse_agent/` or `tests/` paths exist at startup.
- `final-check` fails accepted reports when startup source/test is dirty.
- `generated_artifacts` excludes historical-only artifacts.
- `required_audit_coverage` or equivalent rejects placeholder or mismatched audit answers.
- `report_summary_fields_match_synthesis: PASS`.
- `execute_decision_contract: PASS`.
- `run-closeout: PASSED`, close-round `CLOSED`, and no nested active FAIL/FAILED states.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current task is controlled by this `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only and still refers to an older `samplereverse` sample state. It must not drive this engineering rework.

The latest audited execution was `decision_20260630_hygiene_and_handoff_bundle_v1` / `round_20260630_hygiene_and_handoff_bundle_v1`. Its audit conclusion was `REWORK_REQUIRED` for the following concrete reasons:

1. Startup `git status --short` already showed dirty source/test files before startup-snapshot:
   - `reverse_agent/project_agent_runner.py`
   - `reverse_agent/project_control_plane.py`
   - `reverse_agent/project_gate.py`
   - `tests/test_project_agent_runner.py`
   - `tests/test_project_control_plane.py`
   - `tests/test_project_gate.py`
2. `startup_snapshot.json` still recorded `source_test_clean_start: true`, while separately listing those source/test paths under an authorization-style field. This violates the decision requirement that dirty source/test startup baselines must block execution.
3. `final_gate_result.json` marked startup baseline consistency as PASS even though it recognized source/test dirty files.
4. `codex_report_summary.generated_artifacts` and `generated_or_updated_artifacts` still included historical or generic gate artifacts, including `phase1_completion_result.json`, `policy_impact_audit.json`, `policy_lint_result.json`, and `state_hygiene_inventory.json`.
5. `report_summary_synthesis.json` reproduced the same artifact taxonomy issue.
6. `codex_execution_report.md` Required Audit answers were misaligned with their questions. Several answers used unrelated evidence, such as using handoff bundle fingerprints to answer startup ordering, or replay validation to answer startup source/test cleanliness.

Current existing capability to preserve:

- `project_agent_runner.py` already contains local non-executing dry-run and handoff/replay validation work from the failed round.
- `project_gate.py` already exposes or can expose startup-snapshot, command-plan, report-summary, final-check, run-closeout, agent-runner-dry-run, agent-runner-handoff-bundle, and agent-runner-handoff-validate gates.
- `project_control_plane.py` already has readiness fields that can distinguish dry-run/handoff readiness from real dispatch readiness.
- Runner execution, dispatch, external invocation, model API calls, GitHub Actions mutation, Web UI, database, queue, scheduler, reverse-solving, and runtime probes remain forbidden.

Artifact freshness:

- New current-round artifacts must carry `decision_20260630_hygiene_handoff_rework_v1` and `round_20260630_hygiene_handoff_rework_v1`.
- Historical gate artifacts may be referenced only as historical/nonblocking unless regenerated in this round with current IDs and current provenance.
- Existing missing sample artifacts in `artifact_index.json` remain nonblocking historical backlog for this engineering rework.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, only increasing beam/budget, compare_semantics_agree=false candidate frontier reuse, full solve_reports commits, and repeated old runtime candidate branches.
- This round must not run samples, solve a reverse challenge, read full solve_reports, run runtime probes, or modify negative_results.

Command-plan policy:

- `command-plan` is the command execution authority.
- Codex may only execute commands authorized by command-plan.
- However, command-plan must not weaken these hard requirements: startup-snapshot immediacy, dirty source/test startup blocking, no preflight before startup-snapshot, artifact role taxonomy, no real execution, no dispatch, final-check convergence, and closeout convergence.

## 3. Do Not Do

Do not implement new runner features beyond this rework.

Do not implement real AgentRunner execution.

Do not execute handoff bundle commands.

Do not spawn subprocesses from `project_agent_runner.py`, handoff bundle code, replay validation code, final-check code, or report-summary code except through explicit user/command-plan top-level commands that are recorded in `pytest_result.txt`.

Do not call Codex CLI, Trae, Claude Code, Aider, model APIs, browser automation, GitHub Actions, remote services, or external runners.

Do not enable dispatch. `dispatch_enabled`, `can_dispatch`, `allow_agent_dispatch`, `executable`, `external_invocation`, `remote_mutation`, and equivalent flags must remain false.

Do not create a Web UI, API Planner, API Auditor, database, queue daemon, scheduler, worker process, message bus, Kubernetes workflow, or long-running service.

Do not modify GitHub workflows, prompt docs, `.codex-skills/`, `current_state.json`, `task_packet.json`, `artifact_index.json`, or `negative_results.json`.

Do not read full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full `project_state/rounds/`.

Do not perform reverse-solving, sample execution, runtime probe, dynamic debugging, emulator execution, hook execution, or binary analysis.

Do not treat `authorized_source_test_dirty_files` or any similarly named field as a substitute for a clean startup baseline. Source/test dirty at startup is blocking.

Do not treat historical artifacts as generated current-round artifacts unless the current round actually generated them with current decision/round provenance.

Do not write `SUCCESS` when Required Audit answers are mismatched, generic, template-cycled, or unrelated to the question.

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

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_agent_runner.py`
3. `reverse_agent/project_control_plane.py`
4. `tests/test_project_gate.py`
5. `tests/test_project_agent_runner.py`
6. `tests/test_project_control_plane.py`
7. `tests/test_project_reports.py`
8. `tests/test_project_state.py`

Inspect bounded gate artifacts:

1. `project_state/gates/startup_snapshot.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/execution_log.json`
7. `project_state/gates/round_baseline.json`
8. `project_state/gates/round_delta_summary.json`
9. `project_state/gates/agent_runner_dry_run_result.json`
10. `project_state/gates/agent_runner_handoff_bundle.json`
11. `project_state/gates/agent_runner_handoff_validation.json`
12. `project_state/gates/control_plane_snapshot.json`

Create/update if needed:

1. `project_state/jobs/job_20260630_hygiene_handoff_rework_v1.json`
2. `project_state/rounds/round_20260630_hygiene_handoff_rework_v1/*`

Do not scan full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or full historical round directories.

## 5. Required Audit

The execution report must answer every item below with `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`, with direct evidence for that exact item. A generic answer or unrelated evidence is a failure.

1. Did the first five recorded commands exactly confirm `F:\reverse-agent`, repository root, and `git status --short`?
2. Was `startup-snapshot` the immediate sixth recorded command and the first project gate command?
3. Was `preflight` absent before startup-snapshot?
4. Did startup `git status --short` show no dirty `reverse_agent/` or `tests/` files?
5. Did `startup_snapshot.source_test_clean_start` match the actual startup source/test dirtiness?
6. Does final-check block SUCCESS/ACCEPTED when startup source/test is dirty?
7. Does final-check block SUCCESS/ACCEPTED when preflight or any gate appears before startup-snapshot?
8. Is decision metadata valid: APPROVED, engineering_branch, active `reverse-agent-iteration@v2`?
9. Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?
10. Were the failed-round issues explicitly addressed rather than hidden by allowlist fields?
11. Does report taxonomy include generated/updated, referenced, historical_nonblocking, and archived artifacts or equivalent fields?
12. Are `phase1_completion_result.json`, `policy_impact_audit.json`, `policy_lint_result.json`, `state_hygiene_inventory.json`, `audit_inventory_result.json`, and `naming_migration_plan.json` excluded from generated/generated_or_updated unless actually regenerated in this round with current IDs?
13. Does report-summary synthesis validate taxonomy and report no diffs?
14. Does final-check detect stale/historical-only artifacts being placed in generated/current artifact lists?
15. Does final-check or report-summary detect Required Audit placeholder/template/misaligned answers?
16. Are Required Audit answers in `codex_execution_report.md` directly aligned with their question and evidence?
17. Is existing `agent_runner_dry_run_result.json` current, PASSED, non-executing, and non-dispatching?
18. Is existing handoff bundle evidence current, non-executing, and non-dispatching if regenerated this round?
19. Is existing handoff replay validation current and PASSED if regenerated this round?
20. Did the rework avoid adding any new real runner, dispatch, external invocation, model API, Web/API/DB/queue/scheduler, GitHub Actions mutation, runtime probe, or reverse-solving capability?
21. Did the implementation stay within allowed source/test files?
22. Were preserve-only and forbidden files not modified?
23. Did required pytest commands exit 0, with pass counts recorded in `pytest_result.txt`?
24. Did `report_summary_fields_match_synthesis` pass with no diffs?
25. Did `execute_decision_contract` pass?
26. Did `execution_log` provenance remain current-round aligned?
27. Did `run-closeout` exit 0 with `closeout_status: PASSED` and close-round `CLOSED`?
28. Did final-check pass after archive/closeout, not only before archive?
29. Did `closeout_nested_failures_absent` pass?
30. Does `codex_report_summary` match `pytest_result.txt`, artifact taxonomy, generated/updated artifacts, changed files, decision ID, and round ID?

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_agent_runner.py`
- `reverse_agent/project_control_plane.py`
- `tests/test_project_gate.py`
- `tests/test_project_agent_runner.py`
- `tests/test_project_control_plane.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`

Preserve-only files:

- `reverse_agent/project_jobs.py`
- `reverse_agent/project_runner_contract.py`
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
- `project_state/jobs/job_20260630_hygiene_handoff_rework_v1.json`
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
- `project_state/rounds/round_20260630_hygiene_handoff_rework_v1/*`

Required implementation behavior:

1. Update startup-snapshot/final-check logic so dirty `reverse_agent/` or `tests/` paths at startup are blocking.
2. Remove or neutralize any acceptance path that treats dirty source/test startup paths as clean because they are in an allowed or inherited list.
3. Add startup transcript order validation that requires startup-snapshot to be command block 6 and first project gate.
4. Add or update tests for dirty source/test startup blocking.
5. Add or update tests for preflight-before-startup-snapshot blocking.
6. Fix artifact taxonomy synthesis and validation.
7. Add or update tests that historical-only artifacts cannot appear in generated/generated_or_updated lists unless current-round regenerated.
8. Add Required Audit answer alignment validation that catches repeated template answers, mismatched evidence labels, placeholder answers, or answers that do not mention the question-specific evidence.
9. Rewrite `codex_execution_report.md` Required Audit answers with direct item-specific evidence.
10. Preserve existing handoff bundle/replay validation behavior but do not expand it into execution or dispatch.

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

Hard startup rules:

- No `python -m reverse_agent.project_gate preflight ...` may be recorded before startup-snapshot.
- No `command-plan`, `final-check`, `jobs-inventory`, `job-orchestration`, `runner-contract`, `agent-runner-dry-run`, `agent-runner-handoff-*`, `control-plane-snapshot`, `report-summary`, `execution-log`, or `run-closeout` command may appear before startup-snapshot.
- If startup `git status --short` shows any dirty `reverse_agent/` or `tests/` path, stop with `BLOCKED` before implementation and do not write `SUCCESS`.

Required focused tests must include the equivalent of:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_agent_runner.py tests/test_project_control_plane.py tests/test_project_reports.py tests/test_project_state.py -q
```

The focused tests must cover at least:

- `test_startup_snapshot_fails_on_source_test_dirty`
- `test_final_check_blocks_source_test_dirty_startup`
- `test_final_check_blocks_preflight_before_startup_snapshot`
- `test_report_summary_taxonomy_excludes_historical_from_generated`
- `test_required_audit_answer_alignment_rejects_template_mismatch`

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
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260630_hygiene_handoff_rework_v1 --mode execute
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260630_hygiene_handoff_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The concrete command list must come from command-plan. Do not run commands outside command-plan. Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately with `BLOCKED` if:

- startup cannot confirm `F:\reverse-agent` and repository root;
- startup `git status --short` shows any dirty `reverse_agent/` or `tests/` path;
- startup-snapshot cannot be generated immediately after the five startup status commands;
- preflight or any other project gate runs before startup-snapshot;
- decision metadata is invalid;
- skill profile is not active;
- command-plan is missing or unsafe;
- the task requires real runner dispatch, external model calls, GitHub Actions triggers, remote mutation, Web/API/DB/queue/scheduler work, reverse-solving, runtime probes, or full solve_reports scanning;
- implementation requires mutating forbidden paths or preserve-only files.

Stop with `REWORK_REQUIRED` if:

- startup source/test dirty files are reclassified as authorized rather than blocking;
- `startup_snapshot.source_test_clean_start` does not match actual startup source/test dirtiness;
- final-check accepts dirty startup source/test evidence;
- startup ordering is still not enforced by final-check or closeout-relevant validation;
- `generated_artifacts` or `generated_or_updated_artifacts` includes stale/historical-only artifacts as current generated artifacts;
- artifact taxonomy fields are missing from summaries or not checked by report-summary synthesis;
- Required Audit answers are generic, placeholder, repeated from a template, or mismatched with their questions;
- final-check cannot detect Required Audit answer misalignment;
- existing handoff bundle or validation artifacts regress if regenerated;
- control-plane readiness conflates handoff readiness with real dispatch readiness;
- any runner/handoff code executes commands, spawns subprocesses, calls external services, or mutates remote state;
- stale sample or historical gate artifacts are treated as current accepted evidence;
- `codex_execution_report.md` omits Required Audit answers;
- `pytest_result.txt` does not match actual commands or exit codes;
- required pytest commands fail;
- `report_summary_fields_match_synthesis` fails;
- `execute_decision_contract` fails;
- `execution_log` provenance regresses;
- `run-closeout` exits nonzero or close status is not CLOSED;
- final-check after archive/closeout does not pass;
- nested failure scan finds active FAILED/FAIL states;
- Codex modifies workflows, prompts, skills, task/current/artifact/negative state, solve_reports, or remote state.
