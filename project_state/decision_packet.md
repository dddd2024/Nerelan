```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260702_ci_workflow_coverage_audit_gate_v1",
  "round_id": "round_20260702_ci_workflow_coverage_audit_gate_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260701_local_execution_loop_foundation_v1",
  "previous_round_id": "round_20260701_local_execution_loop_foundation_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_28_ci_workflow_coverage_audit_gate",
  "primary_goal": "Create a bounded local project-gate artifact that audits existing GitHub workflow coverage against the accepted local execution loop artifacts, without modifying workflow files or adding runner/dispatcher behavior.",
  "command_plan_authority_required": true,
  "accepted_requires_ci_workflow_coverage_artifact": true,
  "accepted_requires_workflow_static_validation_tests": true,
  "accepted_requires_existing_workflows_read_only": true,
  "accepted_requires_local_execution_loop_not_regressed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260702_ci_workflow_coverage_audit_gate_v1/*"
  ],
  "read_only_files": [
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "forbidden_mutated_paths": [
    ".github/workflows/*",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/*",
    "solve_reports/*"
  ],
  "preserve_only_files": [
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_audits.py",
    "reverse_agent/project_rounds.py",
    "reverse_agent/project_state.py"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **CI Workflow Coverage Audit Gate v1**.

This is an `engineering_branch` round. The previous accepted round produced the local execution loop foundation through current gate artifacts: `local_execution_bundle.json`, `codex_prompt_packet.json`, and `audit_precheck_result.json`.

The next step is not to change CI yet. First create a bounded local gate that audits the existing workflow files and records whether they cover the current local execution loop. This avoids silently assuming that GitHub CI already validates the new bundle / prompt / audit-precheck path.

Primary objective:

1. Add or repair a project-gate subcommand that writes `project_state/gates/ci_workflow_coverage_result.json`.
2. The artifact must statically inspect `.github/workflows/ci.yml` and `.github/workflows/state-gate.yml` as read-only inputs.
3. The artifact must report whether existing workflows cover:
   - baseline import / focused pytest;
   - `tests/test_project_reports.py`;
   - preflight;
   - command-plan;
   - audit-inventory;
   - audit-readiness-packet;
   - current-handoff-packet;
   - local-execution-bundle;
   - codex-prompt-packet;
   - audit-precheck;
   - report-summary;
   - execution-log;
   - final-check.
4. The artifact must also report unsafe workflow capabilities if present, including write permissions, workflow commands that mutate repository state, autonomous agent execution, external model calls, self-hosted runner use, sample execution, harness execution, or full `solve_reports/` scanning.
5. Add regression tests for the workflow coverage parser and unsafe-pattern detector.
6. Preserve the accepted local execution loop artifacts and final-check / closeout behavior.
7. Do not modify `.github/workflows/*` in this round.

Target accepted state:

- `codex_execution_report.md` status: `SUCCESS`.
- acceptance recommendation: `ACCEPTED` if the new audit gate and tests pass, even if the audit artifact reports workflow coverage gaps as nonblocking findings for a future workflow-update round.
- `pytest_result.txt` status: `PASSED`.
- `ci_workflow_coverage_result.json`: current decision ID, current round ID, current report ID, evidence-only, read-only, non-mutating, and explicit about workflow coverage status.
- `final_gate_result.json`: `PASSED`.
- `run_closeout_result.json`: `PASSED`.
- close-round: `CLOSED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only.

Previous accepted round:

- `decision_20260701_local_execution_loop_foundation_v1`
- `round_20260701_local_execution_loop_foundation_v1`
- audit outcome: `ACCEPTED`

Accepted evidence to preserve:

- `local_execution_bundle.json` was current, evidence-only, non-executable, non-dispatching, non-mutating, and command-plan aligned.
- `codex_prompt_packet.json` was current and derived from current bundle / handoff evidence.
- `audit_precheck_result.json` was current and ultimately recommended `READY_FOR_GPT_AUDIT` when report, pytest, final-check, closeout, readiness, bundle, and prompt evidence aligned.
- `audit_readiness_packet.json` was current with `READY`, `ACCEPTED`, and `no_action_required`.
- `final_gate_result.json` passed with no blocking reasons or warnings.
- `run_closeout_result.json` passed and close-round was `CLOSED`.

Existing workflow evidence:

- `.github/workflows/ci.yml` exists and performs baseline repository validation.
- `.github/workflows/state-gate.yml` exists and performs state-gate validation.
- These workflows were introduced before the current local execution loop foundation. They must be audited before deciding whether a workflow-update round is needed.

Artifact freshness policy:

- Current-round generated artifacts must carry `decision_20260702_ci_workflow_coverage_audit_gate_v1` and `round_20260702_ci_workflow_coverage_audit_gate_v1`.
- Historical artifacts may be referenced only as historical or nonblocking unless rebuilt with current IDs.
- Reverse-solving artifacts in `artifact_index.json` remain missing/non-current and must not be treated as current engineering evidence.

Negative-results policy:

- This is not a reverse-solving round.
- Do not repeat directions blocked in `negative_results.json`, including blind sample_solver search, budget-only expansion, compare_semantics_agree=false primary frontier, committing full solve_reports, or repeated stale candidate audits.

Command-plan policy:

- `project_state/gates/command_plan.json` remains the only command execution authority.
- The Tests section does not authorize commands by itself.
- `command_plan.omitted_commands` must not be executed.

## 3. Do Not Do

Do not modify `.github/workflows/*` in this round. The workflows are read-only evidence.

Do not implement a runner, dispatcher, scheduler, service, Web/API layer, queue, database, self-hosted runner controller, external integration, model API caller, remote executor, or remote automation.

Do not execute reverse-solving samples, solvers, harnesses, IDA, Ghidra, OllyDbg, x64dbg, radare2, emulators, dynamic debugging, or full historical `solve_reports/` scans.

Do not modify preserve-only modules:

- `reverse_agent/project_agent_runner.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_audits.py`
- `reverse_agent/project_rounds.py`
- `reverse_agent/project_state.py`

Do not modify forbidden paths:

- `.github/workflows/*`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/*`
- `solve_reports/*`

Do not write dynamic run facts, candidate data, runtime metrics, artifact freshness, or one-round conclusions into `.codex-skills/`.

Do not weaken existing checks for command-plan authority, startup-snapshot ordering, report-summary synthesis, execution-log consistency, audit inventory, audit readiness, local execution bundle, codex prompt packet, audit precheck, final-check, run-closeout, or close-round archive behavior.

Do not use `COMPLETED_WITH_LIMITATIONS` as report status.

Do not claim CI workflows were updated. This round only creates local audit evidence about the current workflow files.

## 4. Files To Inspect

Read first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/execution_report.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Inspect bounded current gate artifacts:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/final_gate_result.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/audit_inventory_result.json`
7. `project_state/gates/audit_readiness_packet.json`
8. `project_state/gates/current_handoff_packet.json`
9. `project_state/gates/local_execution_bundle.json`
10. `project_state/gates/codex_prompt_packet.json`
11. `project_state/gates/audit_precheck_result.json`

Inspect implementation and tests:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`

Read-only workflow evidence:

1. `.github/workflows/ci.yml`
2. `.github/workflows/state-gate.yml`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer all items below with concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Did startup commands confirm `F:\reverse-agent`, repo root, and clean or explicitly baselined `git status --short` before any project gate?
2. Was `startup-snapshot` still the immediate sixth command and first project gate?
3. Did `decision_meta` remain valid and `APPROVED` on `engineering_branch` with active `reverse-agent-iteration@v2`?
4. Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?
5. Were `.github/workflows/ci.yml` and `.github/workflows/state-gate.yml` inspected only as read-only evidence?
6. Was `project_state/gates/ci_workflow_coverage_result.json` generated with current decision ID, round ID, and report ID?
7. What workflow coverage does the artifact report for baseline pytest, `tests/test_project_reports.py`, preflight, command-plan, local-execution-bundle, codex-prompt-packet, audit-precheck, report-summary, execution-log, and final-check?
8. What unsafe workflow capabilities does the artifact check for, and were any found?
9. Do tests fail when required workflow coverage is missing from synthetic workflow content?
10. Do tests fail when unsafe workflow patterns are present in synthetic workflow content?
11. Did implementation stay within allowed source/test files and generated artifacts?
12. Were forbidden and preserve-only files not modified?
13. Did local execution bundle remain current, evidence-only, non-executable, non-dispatching, non-mutating, and command-plan aligned?
14. Did codex prompt packet remain current and non-executable?
15. Did audit precheck preserve `READY_FOR_GPT_AUDIT` and `DO_NOT_ACCEPT`/blocking semantics?
16. Did report-summary match pytest, changed files, generated artifacts, decision ID, round ID, and new workflow coverage artifact status?
17. Did execution-log align with command-plan and pytest_result, with no omitted command executed?
18. Did final-check pass?
19. Did run-closeout pass, close-round become `CLOSED`, and post-closeout final-check pass?
20. Did the report clearly state that workflow files were not modified and that any workflow coverage gaps are input for a future decision?

Do not answer with placeholder text or unsupported claims.

## 6. Implementation Scope

Allowed source/test changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`

Allowed generated or updated artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260702_ci_workflow_coverage_audit_gate_v1/*`

Required behavior:

1. Add or repair a bounded project-gate command such as `ci-workflow-coverage` that writes `project_state/gates/ci_workflow_coverage_result.json`.
2. The command must read workflow files without modifying them.
3. The output artifact must include:
   - schema_version;
   - artifact_name;
   - gate_name;
   - gate_status;
   - decision_id;
   - round_id;
   - report_id;
   - generated_at;
   - inspected_workflows;
   - required_coverage;
   - observed_coverage;
   - missing_coverage;
   - unsafe_patterns_checked;
   - unsafe_patterns_found;
   - recommendation;
   - evidence_only;
   - executable;
   - can_execute;
   - can_dispatch;
   - mutates_state;
   - warnings;
   - errors.
4. The gate should distinguish structural gate success from workflow coverage completeness. Example: artifact generation can pass while recommendation says `WORKFLOW_UPDATE_RECOMMENDED` if current workflows omit coverage.
5. Add tests for valid current workflow parsing.
6. Add tests with synthetic workflow text where required coverage is missing.
7. Add tests with synthetic workflow text where unsafe patterns are present.
8. Add final-check/report-summary integration if needed so the new artifact is not orphaned.
9. Preserve local execution bundle, codex prompt packet, audit precheck, current handoff, audit inventory, audit readiness, execution-log, final-check, and closeout behavior.
10. Do not update `.github/workflows/*`.

## 7. Tests

Startup sequence must be recorded first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
```

Required command-plan and gate flow:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate ci-workflow-coverage --state-dir project_state
python -m reverse_agent.project_gate audit-inventory --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate current-handoff-packet --state-dir project_state
python -m reverse_agent.project_gate local-execution-bundle --state-dir project_state
python -m reverse_agent.project_gate codex-prompt-packet --state-dir project_state
python -m reverse_agent.project_gate audit-precheck --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required focused pytest:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
```

Required closeout path:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260702_ci_workflow_coverage_audit_gate_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required regression coverage:

- valid current workflow files produce a current `ci_workflow_coverage_result.json`;
- synthetic workflow missing `tests/test_project_reports.py` is reported as missing coverage;
- synthetic workflow missing `local-execution-bundle` is reported as missing coverage;
- synthetic workflow missing `codex-prompt-packet` is reported as missing coverage;
- synthetic workflow missing `audit-precheck` is reported as missing coverage;
- synthetic workflow missing `report-summary` or `final-check` is reported as missing coverage;
- synthetic workflow with unsafe remote mutation or autonomous-agent patterns is reported unsafe;
- current local execution bundle remains valid;
- current codex prompt packet remains valid;
- audit precheck remains valid;
- final-check and closeout exit 0 in accepted state.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

The Tests section does not itself authorize execution. If Tests and `command_plan.json` conflict, `command_plan.json` is authoritative.

## 8. Stop Conditions

Stop with `BLOCKED` if:

- startup path or repository root is wrong;
- startup `git status --short` has dirty source/test files outside the allowed baseline;
- startup-snapshot is not immediate after startup status commands;
- any project gate runs before startup-snapshot;
- decision metadata or skill profile is invalid;
- command-plan is missing, unsafe, or omits the new `ci-workflow-coverage` gate when required;
- implementing the gate requires modifying `.github/workflows/*`;
- implementing the gate requires preserve-only modules or forbidden paths;
- implementing the gate requires runner, dispatcher, scheduler, Web/API, database, queue, self-hosted runner controller, external integration, model API caller, remote executor, or reverse-solving behavior.

Stop with `REWORK_REQUIRED` if:

- `ci_workflow_coverage_result.json` is missing, stale, malformed, or not current-round aligned;
- the artifact does not inspect both workflow files when they exist;
- the artifact does not report required coverage, observed coverage, missing coverage, unsafe patterns checked, unsafe patterns found, and recommendation;
- the artifact is executable, dispatching, mutating, or claims command authority;
- tests do not cover missing required workflow coverage;
- tests do not cover unsafe workflow patterns;
- `.github/workflows/*` is modified;
- local execution bundle regresses;
- codex prompt packet regresses;
- audit precheck regresses;
- audit readiness regresses from `READY` / `ACCEPTED` / `no_action_required`;
- report-summary omits the new artifact status;
- execution-log does not align with command-plan and pytest_result;
- final-check fails;
- run-closeout fails;
- close-round is not `CLOSED`;
- closeout nested failure scan finds active failures;
- forbidden files are modified;
- report status is `SUCCESS` without real pytest and gate evidence.

If all required local tests and gates pass, accept the round even if the new workflow coverage artifact recommends a future workflow-update decision. That recommendation is planning evidence, not failure of this audit-gate round.
```