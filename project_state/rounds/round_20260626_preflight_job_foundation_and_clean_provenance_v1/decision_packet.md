```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260626_preflight_job_foundation_and_clean_provenance_v1",
  "round_id": "round_20260626_preflight_job_foundation_and_clean_provenance_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260626_ci_state_gate_and_naming_provenance_v1",
  "previous_round_id": "round_20260626_ci_state_gate_and_naming_provenance_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_5_clean_provenance_and_preflight_job_foundation",
  "primary_goal": "Eliminate inherited-dirty/startup-order/execution-log provenance ambiguity while advancing the automation roadmap with decision-preflight CI and a minimal non-dispatching job schema foundation.",
  "command_plan_authority_required": true,
  "accepted_requires_startup_order_hardened": true,
  "accepted_requires_clean_or_explicit_baseline_semantics": true,
  "accepted_requires_execution_log_source_improved_or_explicitly_qualified": true,
  "accepted_requires_decision_preflight_workflow": true,
  "accepted_requires_minimal_job_schema_validation": true,
  "accepted_requires_no_agentrunner_or_auto_push": true,
  "accepted_requires_pytest_result_status_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_jobs.py",
    "tests/test_project_gate.py",
    "tests/test_project_jobs.py"
  ],
  "allowed_config_files": [
    ".github/workflows/decision-preflight.yml"
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

Implement Preflight Job Foundation and Clean Execution Provenance v1.

The previous round established the first GitHub CI foundation and currentized `project_state/gates/naming_migration_plan.json`. It was accepted with limitations because workflow files were already untracked in the round baseline, startup command evidence was not recorded as a completely first-class ordered block, and `execution_log.json` was still derived from `pytest_result.txt` plus `command_plan.json` rather than being a stronger executor-side record.

This round must both address those audit limitations and continue the automation roadmap. The target is not just cleanup. It must add the next bounded automation layer: a decision-preflight GitHub workflow and a minimal job schema/validator foundation that prepares for future AgentRunner work without implementing AgentRunner yet.

Final accepted state must satisfy:

1. Startup provenance is hardened: accepted rounds must show `Set-Location`, `Get-Location`, `Test-Path`, `git rev-parse --show-toplevel`, and `git status --short` before substantive pytest/gate/report-summary execution, or the report must explicitly mark the round as limited rather than full clean provenance.
2. Baseline semantics are clearer: inherited dirty files must be distinguished from files created or changed by the current round; untracked implementation/config files in baseline must not be silently treated as newly created current-round work.
3. `execution_log.json` must be improved beyond an unqualified derived-only log, or the gate/report must explicitly downgrade/qualify the provenance level when the log is derived from `pytest_result.txt`.
4. Add `.github/workflows/decision-preflight.yml` for bounded remote validation of a proposed decision before execution.
5. Add a minimal job schema/validator foundation for future orchestration: enough to validate a `project_state/jobs/*.json` job contract and status vocabulary, but not enough to dispatch an agent.
6. Preserve the existing CI foundation: `.github/workflows/ci.yml` and `.github/workflows/state-gate.yml` must remain bounded, read-only, and non-mutating.
7. Preserve neutral-primary report semantics: `execution_report.md` and `execution_report_summary` remain primary, while Codex-named files/blocks remain compatibility aliases.
8. Preserve command-plan authority, execute-decision `--mode execute`, pytest_result transcript, execution-log checks, report-summary, final-check, and run-closeout convergence.
9. Do not implement Web console, AgentRunner, automatic Codex/Trae dispatch, API Planner/Auditor, self-hosted runner automation, database, queue, scheduler, automatic push, or reverse-solving in this round.

## 2. Current Evidence

Mainline: `engineering_branch`.

The previous round `decision_20260626_ci_state_gate_and_naming_provenance_v1` was accepted with limitations. Current accepted capabilities to preserve:

- `.github/workflows/ci.yml` exists and provides baseline repository validation with read-only permissions.
- `.github/workflows/state-gate.yml` exists and runs project_gate validation plus focused pytest on state/gate-sensitive path changes.
- `project_state/gates/naming_migration_plan.json` carries current decision_id and round_id.
- `report_summary_synthesis.json.sources.execution_report` points to `project_state/execution_report.md`.
- `report_summary_synthesis.json.sources.execution_report_summary_block` is `execution_report_summary`.
- `project_state/codex_execution_report.md` and `codex_report_summary` remain legacy compatibility aliases.
- pytest_result, command-plan, execution-log, final-check, report-summary, and run-closeout passed.

Known limitations to address:

- `.github/workflows/ci.yml` and `.github/workflows/state-gate.yml` appeared as untracked files in the previous round baseline, so their creation provenance was not clean.
- startup evidence was present but not fully ordered as the first top-level block before all substantive commands.
- `execution_log.json` was derived from pytest_result and command_plan; this is acceptable for legacy/manual rounds but should be explicitly qualified or strengthened before automated execution.
- final-check retained a non-blocking `baseline_capture_order` warning.

`task_packet.json` remains non-authoritative background state. It says `decision_packet_controls_current_round`; do not treat `task_packet.task` as execution authority.

`current_state.json` remains a sample-state digest baseline, but this round is not a reverse-solving round.

`artifact_index.json` contains many missing historical sample artifacts. They are non-blocking because this round does not claim sample-solving evidence.

`negative_results.json` contains reverse-solving prohibitions. This round must not repeat old sample_solver blind search, beam/budget expansion, compare_semantics_agree=false primary frontier usage, full solve_reports commits, or repeated runtime evidence directions.

Existing tool/interface policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.
- Do not implement AgentRunner or any external agent dispatcher yet.

Roadmap context:

- The system is moving from manual GPT/Codex loops toward controlled orchestration: decision controls the task, command-plan controls execution, execution_log records facts, CI performs repeatable verification, final-check is the hard gate, and LLM audit handles semantic judgment.
- The next bounded step after baseline CI is decision preflight and a minimal job-state foundation, not Web UI or full automatic execution.

## 3. Do Not Do

Do not implement Web UI, Web backend, API Planner, API Auditor, AgentRunner, self-hosted runner automation, database, queue, scheduler, or multi-agent orchestration in this round.

Do not add workflows that run LLM calls, push commits, create PRs, modify remote state, or execute sample binaries.

Do not add automatic pull/push behavior for agents.

Do not add a runner that dispatches Codex, Trae, Claude Code, Aider, or any other external coding agent.

Do not scan full `solve_reports/` or execute reverse-solving samples.

Do not delete `project_state/codex_execution_report.md`.

Do not delete `project_state/gates/codex_report_auto_summary.json`.

Do not break parser support for `codex_report_summary`.

Do not rename `.codex-skills/` or modify `.codex-skills/registry.json`.

Do not modify docs prompt files in this round.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Do not use `COMPLETED_WITH_LIMITATIONS` as report status.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message given to the executor.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/execution_report.md` if present
7. `project_state/decision_packet.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Then inspect only bounded implementation and gate evidence:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `reverse_agent/project_jobs.py` if present
4. `tests/test_project_jobs.py` if present
5. `.github/workflows/ci.yml`
6. `.github/workflows/state-gate.yml`
7. `.github/workflows/decision-preflight.yml` if present
8. `project_state/gates/command_plan.json`
9. `project_state/gates/execution_log.json`
10. `project_state/gates/final_gate_result.json`
11. `project_state/gates/report_summary_synthesis.json`
12. `project_state/gates/run_closeout_result.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`
15. `project_state/gates/run_closeout_execution_log.json`
16. `project_state/jobs/*.json` only if created by this round
17. current round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, the current live report must answer all nine items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. How were previous audit limitations addressed: inherited dirty CI files, startup order ambiguity, derived-only execution_log, and baseline_capture_order warning?
2. What exact startup commands were recorded, in what order, and before which substantive command?
3. What is the execution-log provenance level now: direct capture, hybrid capture, or explicitly qualified derived capture?
4. Which GitHub workflow files now exist, and what exact commands does `decision-preflight.yml` run?
5. How does `decision-preflight.yml` avoid mutation, LLM calls, agent execution, push, PR creation, and reverse-solving?
6. What minimal job schema/status vocabulary was added, and how is it validated without dispatching any agent?
7. How were existing `ci.yml` and `state-gate.yml` preserved as bounded read-only validation workflows?
8. How were neutral-primary report semantics and legacy alias parity preserved?
9. How were command-plan authority, pytest_result transcript, execution-log, final-check, report-summary, and run-closeout convergence preserved?

Do not write TODO, TBD, PENDING, `should pass`, `expected to pass`, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_jobs.py`
- `tests/test_project_jobs.py`

Allowed config / CI files:

- `.github/workflows/decision-preflight.yml`

Existing workflow files may be inspected and preserved, but avoid changing them unless a small compatibility adjustment is strictly necessary:

- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`

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
- `project_state/jobs/*.json` if used for a minimal non-dispatching job contract fixture or current-round job record
- `project_state/rounds/round_20260626_preflight_job_foundation_and_clean_provenance_v1/*`

Required behavior:

1. Add or harden gate logic so startup command order is auditable. In accepted state, startup commands must be recorded before substantive execution, or the report/final-check must preserve an explicit limitation rather than silently claiming clean provenance.
2. Clarify baseline semantics. Gate/report logic must distinguish inherited dirty files from current-round created/changed files and must not let baseline untracked implementation/config files masquerade as newly produced work without explicit limitation.
3. Improve execution-log provenance. Preferred: make `execute-decision` or related gate commands write executor-side command records with exit codes and timestamps. Acceptable fallback: keep derived execution_log but add explicit provenance_level and make final-check/report downgrade claims accordingly.
4. Add `.github/workflows/decision-preflight.yml` with read-only permissions and bounded commands. It should validate decision/preflight/command-plan and may run focused tests, but must not run closeout, mutate state, call LLMs, dispatch agents, push, create PRs, or solve samples.
5. Add a minimal job schema/validator foundation. The schema should cover `job_id`, `round_id`, `decision_id`, `mainline`, `status`, `runner`, `required_inputs`, `required_outputs`, permission/budget fields as applicable, and a small status vocabulary such as `DRAFT`, `READY`, `RUNNING`, `DONE`, `FINAL_CHECKED`, `AUDITED`, `ACCEPTED`, `ACCEPTED_WITH_LIMITATIONS`, `REWORK_REQUIRED`, `BLOCKED`. Validation must be local and non-dispatching.
6. Preserve existing CI/state-gate workflow behavior.
7. Preserve neutral-primary report source semantics and legacy alias compatibility.
8. Preserve execute-decision `--mode execute`, command-plan convergence, pytest_result, execution-log, final-check, report-summary, and run-closeout behavior.
9. Keep implementation small and avoid broad refactors.

## 7. Tests

Run startup checks first and record them before substantive commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Then use command-plan authority. Run preflight and command-plan first if needed, then execute only command-plan-authorized commands.

Preferred current-round entrypoint:

```powershell
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260626_preflight_job_foundation_and_clean_provenance_v1 --mode execute
```

At minimum, validation should include command-plan-authorized equivalents of:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260626_preflight_job_foundation_and_clean_provenance_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If `tests/test_project_jobs.py` is not created because job validation was implemented inside existing tests, the report must justify that choice and list the exact test coverage.

Also statically validate `.github/workflows/decision-preflight.yml` using a YAML parser if available, or bounded text/schema tests if not.

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands and exit codes in `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- implementation requires forbidden path mutation;
- implementation requires Web / AgentRunner / DB / queue / scheduler scope;
- implementation requires automatic push, PR creation, or remote mutation;
- implementation requires sample-solving or heavy artifact scan.

Stop with `REWORK_REQUIRED` if:

- previous audit limitations are not addressed or explicitly preserved as limitations;
- startup commands are not recorded in a first-class ordered way before substantive execution;
- baseline semantics still allow inherited untracked implementation/config files to be claimed as clean current-round creation without limitation;
- execution_log remains derived-only but the report/final-check claims full direct execution provenance;
- `.github/workflows/decision-preflight.yml` is missing;
- `decision-preflight.yml` runs LLM calls, dispatches agents, pushes, creates PRs, mutates repository state, runs closeout, or executes reverse-solving samples;
- no minimal job schema/validator foundation is added;
- job validation dispatches or implies actual agent execution;
- existing `ci.yml` or `state-gate.yml` becomes mutating or loses bounded validation behavior;
- neutral-primary report semantics regress;
- legacy alias parity breaks;
- execute-decision `--mode execute` regresses;
- command-plan stdout differs from live command_plan.json;
- execution-log has missing required command-plan commands;
- final-check fails;
- run-closeout fails;
- pytest_result_summary.status is not `PASSED` in accepted state;
- report status disagrees with pytest_result, execution-log, final-check, or run-closeout;
- forbidden paths are modified;
- `.codex-skills` is renamed or registry is modified;
- work enters Web/AgentRunner/database/queue/scheduler/reverse-solving/heavy scan;
- tests fail;
- policy-lint or policy-impact fails.
