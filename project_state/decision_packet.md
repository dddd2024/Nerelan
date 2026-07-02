```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260702_ci_workflow_update_from_coverage_audit_v1",
  "round_id": "round_20260702_ci_workflow_update_from_coverage_audit_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260702_ci_workflow_coverage_audit_gate_v1",
  "previous_round_id": "round_20260702_ci_workflow_coverage_audit_gate_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_29_ci_workflow_update_from_coverage_audit",
  "primary_goal": "Update existing GitHub CI workflow files to close the nonblocking coverage gaps reported by ci_workflow_coverage_result.json, while preserving read-only remote behavior and avoiding any runner, dispatcher, Web/API, database, model call, or reverse-solving scope.",
  "command_plan_authority_required": true,
  "accepted_requires_workflow_files_updated": true,
  "accepted_requires_ci_workflow_coverage_no_missing_required_coverage": true,
  "accepted_requires_no_unsafe_workflow_patterns": true,
  "accepted_requires_tests_project_reports_in_workflow": true,
  "accepted_requires_state_gate_local_execution_loop_coverage": true,
  "accepted_requires_local_execution_loop_not_regressed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_config_files": [
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260702_ci_workflow_update_from_coverage_audit_v1/*"
  ],
  "forbidden_mutated_paths": [
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

Implement **CI Workflow Update from Coverage Audit v1**.

This is an `engineering_branch` round. The previous accepted round created a local audit gate, `project_state/gates/ci_workflow_coverage_result.json`, which inspected the existing GitHub workflow files and reported workflow coverage gaps as nonblocking planning evidence.

This round should now close those gaps by updating only the existing workflow files:

1. `.github/workflows/ci.yml`
2. `.github/workflows/state-gate.yml`

Primary objective:

1. Update the existing workflows so the CI / state-gate configuration includes `tests/test_project_reports.py` coverage.
2. Update the existing workflows so state-gate validation covers the current local execution loop gate surface:
   - `audit-inventory`
   - `audit-readiness-packet`
   - `current-handoff-packet`
   - `local-execution-bundle`
   - `codex-prompt-packet`
   - `audit-precheck`
   - `report-summary`
   - `execution-log`
   - `final-check`
3. Preserve bounded, read-only remote behavior: workflows may validate the checked-out workspace, but they must not push, commit, create PRs, call model APIs, invoke autonomous agents, use self-hosted runners, run reverse-solving samples, execute harnesses, or scan full `solve_reports/`.
4. Regenerate `ci_workflow_coverage_result.json` after the workflow changes and require it to report no missing required coverage and no unsafe patterns.
5. Preserve accepted local execution loop evidence: current handoff packet, local execution bundle, codex prompt packet, audit precheck, audit readiness, report-summary, execution-log, final-check, and closeout.
6. Do not implement Web, AgentRunner, job dispatch, API planner/auditor, database, queue, scheduler, self-hosted runner automation, IDA/Ghidra/OllyDbg integration, User Solve Layer, IDA MCP adapter, or reverse-solving behavior in this round.

Target accepted state:

- `codex_execution_report.md` status: `SUCCESS`.
- acceptance recommendation: `ACCEPTED`.
- `pytest_result.txt` status: `PASSED`.
- `.github/workflows/ci.yml` and/or `.github/workflows/state-gate.yml` updated only as needed to close coverage gaps.
- `ci_workflow_coverage_result.json` current with current decision ID, round ID, and report ID.
- `ci_workflow_coverage_result.json.missing_coverage` is empty for required coverage from this decision.
- `ci_workflow_coverage_result.json.unsafe_patterns_found` is empty.
- `ci_workflow_coverage_result.json.workflow_files_dirty` contains only the workflow files intentionally updated this round, or an equivalent field clearly records the workflow changes as authorized.
- `final_gate_result.json`: `PASSED`.
- `run_closeout_result.json`: `PASSED`.
- close-round: `CLOSED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only and must not control execution.

Previous accepted round:

- `decision_20260702_ci_workflow_coverage_audit_gate_v1`
- `round_20260702_ci_workflow_coverage_audit_gate_v1`
- audit outcome: `ACCEPTED`

Current accepted evidence from the previous round:

1. `codex_execution_report.md` was current with `SUCCESS` and `ACCEPTED`.
2. `pytest_result.txt` was current with `PASSED` and included the focused pytest command containing `tests/test_project_reports.py`.
3. `ci_workflow_coverage_result.json` was current and evidence-only.
4. `ci_workflow_coverage_result.json` inspected `.github/workflows/ci.yml` and `.github/workflows/state-gate.yml` as read-only inputs.
5. `ci_workflow_coverage_result.json` reported `unsafe_patterns_found: []`.
6. `ci_workflow_coverage_result.json` reported `recommendation: WORKFLOW_UPDATE_RECOMMENDED`.
7. `ci_workflow_coverage_result.json` reported these missing coverage items:
   - `tests_project_reports_py`
   - `audit_inventory`
   - `audit_readiness_packet`
   - `current_handoff_packet`
   - `local_execution_bundle`
   - `codex_prompt_packet`
   - `audit_precheck`
   - `report_summary`
   - `execution_log`
8. `final_gate_result.json` passed with no blocking reasons or warnings.
9. `run_closeout_result.json` passed and close-round was `CLOSED`.
10. `audit_precheck_result.json` ultimately recommended `READY_FOR_GPT_AUDIT`.
11. `audit_readiness_packet.json` was `READY`, `ACCEPTED`, and `no_action_required`.

Existing workflow evidence:

- `.github/workflows/ci.yml` exists.
- `.github/workflows/state-gate.yml` exists.
- The previous audit showed that the workflows already cover baseline import / focused pytest, preflight, command-plan, and final-check.
- The previous audit also showed that the workflows do not yet cover the local execution loop and report-summary surfaces listed above.

Artifact freshness policy:

- Current-round generated artifacts must carry `decision_20260702_ci_workflow_update_from_coverage_audit_v1` and `round_20260702_ci_workflow_update_from_coverage_audit_v1` when regenerated.
- Historical artifacts may be referenced only as historical or nonblocking unless rebuilt with current IDs.
- Reverse-solving sample artifacts in `artifact_index.json` remain missing/non-current and must not be treated as engineering evidence.

Negative-results policy:

- This is not a reverse-solving round.
- Do not repeat directions blocked in `negative_results.json`, including blind sample_solver search, budget-only expansion, compare_semantics_agree=false primary frontier, committing full solve_reports, or repeated stale candidate audits.

Command-plan policy:

- `project_state/gates/command_plan.json` remains the only command execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- The Tests section states required coverage; it does not override command-plan.

GitHub / remote policy:

- Workflow files may be modified in the local repository as part of this decision.
- The workflow definitions must not push, commit, create PRs, or mutate remote GitHub state.
- The executor must not push results to GitHub unless the user explicitly requests upload in the future execution context.

Longer-term architecture context:

- The uploaded architecture plan says `decision` controls the task, `command-plan` controls execution, `execution_log` records facts, GitHub CI performs repeatable verification, `final-check` is the hard gate, and LLM audit performs semantic judgment.
- This round is only the CI/state-gate coverage update step in that architecture.
- User Solve Layer and IDA/MCP integration are future layers and must not be implemented here.

## 3. Do Not Do

Do not implement or modify a real runner, dispatcher, scheduler, service, queue, database, Web/API layer, external integration, model API caller, self-hosted runner controller, remote executor, or remote automation.

Do not implement User Solve Layer, Fast Solve Wrapper, fallback ladder, tool profiles, runner capabilities, IDA MCP adapter, IDA runner, Ghidra runner, OllyDbg runner, sample execution, dynamic debug, runtime probe, solver expansion, or reverse-solving behavior.

Do not add workflows or workflow steps that:

- push commits;
- create, edit, merge, or close PRs;
- call `gh api` to mutate GitHub state;
- use `contents: write`, `pull-requests: write`, `actions: write`, or `write-all` permissions;
- call OpenAI, Anthropic, Copilot, ChatGPT, or other model APIs;
- run Codex, Trae, Claude Code, Aider, AgentRunner, or equivalent autonomous agent surfaces;
- use `self-hosted` runner labels;
- execute reverse-solving samples;
- execute harnesses;
- scan full `solve_reports/`;
- start databases, queues, services, or schedulers.

Do not modify preserve-only modules:

- `reverse_agent/project_agent_runner.py`
- `reverse_agent/project_control_plane.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_runner_contract.py`
- `reverse_agent/project_audits.py`
- `reverse_agent/project_rounds.py`
- `reverse_agent/project_state.py`

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/*`
- `solve_reports/*`

Do not write dynamic run facts, workflow run IDs, runtime metrics, prompt text, candidate data, sample conclusions, or artifact freshness into `.codex-skills/`.

Do not weaken existing checks for command-plan authority, startup-snapshot ordering, local execution bundle, codex prompt packet, audit precheck, audit readiness, report-summary, execution-log, final-check, run-closeout, or close-round archive behavior.

Do not use `COMPLETED_WITH_LIMITATIONS` as report status.

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

1. `project_state/gates/ci_workflow_coverage_result.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/final_gate_result.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/execution_log.json`
6. `project_state/gates/run_closeout_result.json`
7. `project_state/gates/audit_inventory_result.json`
8. `project_state/gates/audit_readiness_packet.json`
9. `project_state/gates/current_handoff_packet.json`
10. `project_state/gates/local_execution_bundle.json`
11. `project_state/gates/codex_prompt_packet.json`
12. `project_state/gates/audit_precheck_result.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`
15. `project_state/gates/run_closeout_execution_log.json`

Inspect implementation and tests:

1. `.github/workflows/ci.yml`
2. `.github/workflows/state-gate.yml`
3. `reverse_agent/project_gate.py`
4. `tests/test_project_gate.py`
5. `tests/test_project_reports.py`

Read-only context if needed:

1. Historical CI decision/report archive for `round_20260626_ci_state_gate_and_naming_provenance_v1`, only to avoid reintroducing previously rejected or duplicated CI behavior.
2. Current accepted architecture planning notes only as background; do not let them override this decision.

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer all items below with concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Did startup commands confirm `F:\reverse-agent`, repository root, and clean or explicitly baselined `git status --short` before any project gate?
2. Was `startup-snapshot` the immediate sixth recorded command and the first project gate command?
3. Did `decision_meta` remain valid and `APPROVED` on `engineering_branch` with active `reverse-agent-iteration@v2`?
4. Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?
5. Which exact workflow files were modified, and were modifications limited to `.github/workflows/ci.yml` and `.github/workflows/state-gate.yml`?
6. Does `ci.yml` remain bounded to baseline repository validation and focused pytest, with no remote mutation, model API call, autonomous agent, self-hosted runner, sample execution, harness execution, or full `solve_reports/` scan?
7. Does `state-gate.yml` now cover `tests/test_project_reports.py`?
8. Does `state-gate.yml` now cover `audit-inventory`, `audit-readiness-packet`, `current-handoff-packet`, `local-execution-bundle`, `codex-prompt-packet`, `audit-precheck`, `report-summary`, `execution-log`, and `final-check`?
9. Was `ci_workflow_coverage_result.json` regenerated with current decision ID, round ID, and report ID?
10. Does `ci_workflow_coverage_result.json` report no missing required coverage for this round?
11. Does `ci_workflow_coverage_result.json` report no unsafe workflow patterns?
12. Do tests fail or report missing coverage if synthetic workflow text omits `tests/test_project_reports.py`?
13. Do tests fail or report missing coverage if synthetic workflow text omits local execution loop gate commands?
14. Do tests fail or report unsafe patterns when synthetic workflow text contains write permissions, push/commit/PR mutation, model API calls, autonomous agent invocations, self-hosted runner labels, sample execution, harness execution, or full `solve_reports/` scans?
15. Did implementation stay within allowed source/test/config files and generated artifacts?
16. Were forbidden and preserve-only files not modified?
17. Did local execution bundle remain current, evidence-only, non-executable, non-dispatching, non-mutating, and command-plan aligned?
18. Did codex prompt packet remain current and non-executable?
19. Did audit precheck preserve `READY_FOR_GPT_AUDIT` and `DO_NOT_ACCEPT`/blocking semantics?
20. Did audit readiness remain `READY`, `ACCEPTED`, and `no_action_required` after closeout?
21. Did report-summary match pytest, changed files, generated artifacts, decision ID, round ID, workflow updates, and `ci_workflow_coverage_result.json` status?
22. Did execution-log align with command-plan and pytest_result, with no omitted command executed?
23. Did final-check pass?
24. Did run-closeout pass, close-round become `CLOSED`, and post-closeout final-check pass?
25. Did the report clearly state that this round only updated bounded GitHub workflow validation and did not implement Web/API/Runner/User Solve/IDA/MCP/reverse-solving capability?

Do not answer audit items with TODO, TBD, PENDING, placeholders, speculative claims, or unsupported statements.

## 6. Implementation Scope

Allowed source/test/config changes:

- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`
- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`

Allowed generated or updated artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260702_ci_workflow_update_from_coverage_audit_v1/*`

Required behavior:

1. Update existing workflow files rather than creating duplicate CI concepts.
2. Keep workflow permissions minimal, preferably `contents: read` only.
3. Keep workflows on GitHub-hosted Ubuntu runners. Do not add self-hosted runners in this round.
4. Ensure `ci.yml` remains a baseline validation workflow. It may add `tests/test_project_reports.py` to focused pytest if needed.
5. Ensure `state-gate.yml` includes a focused pytest command covering `tests/test_project_gate.py`, `tests/test_project_reports.py`, and `tests/test_project_state.py`.
6. Ensure `state-gate.yml` includes bounded project-gate validation for audit inventory, audit readiness, current handoff, local execution bundle, codex prompt packet, audit precheck, report-summary, execution-log, and final-check.
7. If any gate command would write tracked artifacts in the CI checkout, ensure the workflow still does not commit, push, upload current-state evidence as authoritative, or mutate remote state. Ephemeral workspace artifacts are acceptable only as validation output.
8. Preserve or update workflow static validation tests so missing coverage and unsafe patterns are caught.
9. Regenerate `ci_workflow_coverage_result.json` after workflow changes and require missing coverage to be empty for required coverage in this round.
10. Keep `unsafe_patterns_found` empty.
11. Preserve local execution bundle, codex prompt packet, audit precheck, audit readiness, report-summary, execution-log, final-check, and closeout behavior.
12. Do not refactor unrelated project-gate areas.
13. Do not implement any User Solve Layer, IDA/MCP, Web/API, runner, scheduler, service, queue, database, external model call, or reverse-solving capability.

Expected workflow coverage minimum:

- `python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate audit-inventory --state-dir project_state`
- `python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state`
- `python -m reverse_agent.project_gate current-handoff-packet --state-dir project_state`
- `python -m reverse_agent.project_gate local-execution-bundle --state-dir project_state`
- `python -m reverse_agent.project_gate codex-prompt-packet --state-dir project_state`
- `python -m reverse_agent.project_gate audit-precheck --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate execution-log --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260702_ci_workflow_update_from_coverage_audit_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required regression coverage:

- current workflow files produce a current `ci_workflow_coverage_result.json` with no missing required coverage;
- current workflow files produce `unsafe_patterns_found: []`;
- synthetic workflow missing `tests/test_project_reports.py` is reported as missing coverage;
- synthetic workflow missing `local-execution-bundle` is reported as missing coverage;
- synthetic workflow missing `codex-prompt-packet` is reported as missing coverage;
- synthetic workflow missing `audit-precheck` is reported as missing coverage;
- synthetic workflow missing `report-summary` or `execution-log` is reported as missing coverage;
- synthetic workflow missing `final-check` is reported as missing coverage;
- synthetic workflow with unsafe remote mutation or autonomous-agent/model-call/self-hosted/sample/harness/full-solve-reports patterns is reported unsafe;
- local execution bundle remains valid;
- codex prompt packet remains valid;
- audit precheck remains valid;
- audit readiness remains `READY` / `ACCEPTED` / `no_action_required` after closeout;
- final-check and closeout exit 0 in accepted state.

Write all top-level commands, exit codes, pytest pass/fail counts, and any skipped command with reason to `project_state/pytest_result.txt`.

The Tests section does not itself authorize execution. If Tests and `command_plan.json` conflict, `command_plan.json` is authoritative.

## 8. Stop Conditions

Stop with `BLOCKED` if:

- startup path or repository root is wrong;
- startup `git status --short` has dirty source/test/config files outside the allowed baseline;
- startup-snapshot is not immediate after startup status commands;
- any project gate runs before startup-snapshot;
- decision metadata or skill profile is invalid;
- command-plan is missing, unsafe, or omits the required workflow-update and `ci-workflow-coverage` validation commands;
- workflow update requires adding self-hosted runners, remote mutation, model API calls, autonomous agent execution, sample execution, harness execution, full `solve_reports/` scanning, Web/API, runner, dispatcher, scheduler, service, queue, database, IDA/Ghidra/OllyDbg, User Solve Layer, IDA MCP, or reverse-solving behavior;
- current workflow behavior cannot be statically validated with bounded tests.

Stop with `REWORK_REQUIRED` if:

- `.github/workflows/ci.yml` or `.github/workflows/state-gate.yml` is malformed;
- duplicate workflow concepts are created unnecessarily;
- workflow permissions are broader than needed without explicit justification;
- workflows can push, commit, create PRs, call model APIs, run autonomous agents, use self-hosted runners, run sample solving, run harnesses, start services/databases/queues, or scan full `solve_reports/`;
- `tests/test_project_reports.py` is still missing from workflow coverage;
- any required local execution loop gate remains missing from workflow coverage;
- `ci_workflow_coverage_result.json` is missing, stale, malformed, not current-round aligned, or still has missing required coverage;
- `ci_workflow_coverage_result.json.unsafe_patterns_found` is nonempty;
- workflow static validation tests are missing or do not fail on omitted required coverage;
- workflow static validation tests are missing or do not fail on unsafe patterns;
- source/test/config changes exceed allowed files;
- forbidden or preserve-only files are modified;
- local execution bundle regresses;
- codex prompt packet regresses;
- audit precheck regresses;
- audit readiness regresses from `READY` / `ACCEPTED` / `no_action_required`;
- report-summary omits workflow update or `ci_workflow_coverage_result.json` status;
- execution-log does not align with command-plan and pytest_result;
- final-check fails;
- run-closeout fails;
- close-round is not `CLOSED`;
- closeout nested failure scan finds active failures;
- report status is `SUCCESS` without real pytest and gate evidence.

If all required local tests and gates pass but actual GitHub Actions execution is not observed in this local round, the report may still recommend `ACCEPTED` as long as it clearly states that workflows were statically validated locally and not proven by a live GitHub Actions run.
```