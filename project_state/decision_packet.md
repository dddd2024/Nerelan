```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260626_ci_state_gate_and_naming_provenance_v1",
  "round_id": "round_20260626_ci_state_gate_and_naming_provenance_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260626_neutral_primary_report_source_rework_v1",
  "previous_round_id": "round_20260626_neutral_primary_report_source_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_ci_foundation",
  "primary_goal": "Create the first GitHub CI state-gate foundation while currentizing naming_migration_plan.json provenance and preserving accepted neutral-primary report semantics.",
  "command_plan_authority_required": true,
  "accepted_requires_ci_workflows_created": true,
  "accepted_requires_ci_uses_project_gate": true,
  "accepted_requires_naming_plan_current_ids": true,
  "accepted_requires_stale_naming_plan_id_detection": true,
  "accepted_requires_neutral_primary_semantics_preserved": true,
  "accepted_requires_pytest_result_status_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_no_web_or_agentrunner_scope": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_config_files": [
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

Implement CI State Gate and Naming Provenance v1.

The previous accepted round finished the practical report-name neutralization target: `execution_report.md` and `execution_report_summary` became the primary live report path/block, while `codex_execution_report.md` and `codex_report_summary` remained compatibility aliases. It was accepted with one limitation: `project_state/gates/naming_migration_plan.json` still carried the previous migration round's `decision_id` and `round_id`.

This round should not be a tiny one-file metadata-only fix. It should combine that provenance fix with the next structural automation step from the architecture roadmap: add the first GitHub CI state-gate foundation.

Final accepted state must satisfy:

1. Add `.github/workflows/ci.yml` for baseline repository validation on push / pull_request.
2. Add `.github/workflows/state-gate.yml` for project-state and gate-sensitive validation on relevant path changes.
3. CI workflows must run bounded project commands, not invoke LLMs, not push, and not mutate repository state.
4. CI must use `reverse_agent.project_gate` checks where appropriate, especially decision-lint / policy-lint or final-check equivalents available in the current implementation.
5. CI must run focused pytest coverage for project gate/state behavior.
6. `project_state/gates/naming_migration_plan.json` must be regenerated or updated with the current decision_id and round_id for this round, or the report must clearly justify why it is historical and not current evidence.
7. final-check or an equivalent gate/test must detect stale `naming_migration_plan.json` decision_id / round_id whenever the report claims it as current naming-migration evidence.
8. Preserve accepted neutral-primary semantics: `report_summary_synthesis.json.sources.execution_report` remains `project_state/execution_report.md`, `execution_report_summary` remains primary, and legacy Codex-named report artifacts remain compatibility aliases.
9. Preserve `execute-decision --mode execute`, command-plan authority, pytest_result transcript, execution-log, final-check, report-summary, and run-closeout convergence.
10. Do not implement Web console, AgentRunner, job state machine, API planner/auditor, self-hosted runner, database, queue, scheduler, or reverse-solving in this round.

## 2. Current Evidence

Mainline: `engineering_branch`.

The previous round `decision_20260626_neutral_primary_report_source_rework_v1` was accepted with limitations.

Accepted current capabilities to preserve:

- `report_summary_synthesis.json.sources.execution_report` points to `project_state/execution_report.md`.
- `report_summary_synthesis.json.sources.execution_report_summary_block` is `execution_report_summary`.
- `project_state/codex_execution_report.md` is a legacy compatibility alias.
- final-check says `execution_report_summary matches synthesized summary` rather than legacy-primary wording.
- closeout reports neutral execution report summary parsed from `execution_report.md`.
- pytest_result, execution-log, final-check, and run-closeout passed.
- The short executor entrypoint `python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id <round_id> --mode execute` is established.

Remaining limitation to fix:

- `project_state/gates/naming_migration_plan.json` still carried `decision_20260626_neutral_primary_report_migration_v1` / `round_20260626_neutral_primary_report_migration_v1` even after the source rework round. It was semantically useful but stale as current provenance evidence.

Architecture context:

- The broader automation roadmap says the system should become a controlled orchestration system where decision controls the task, command-plan controls execution, execution_log records fact, GitHub CI performs repeatable verification, final-check is the hard gate, and LLM audit handles semantic judgment. The near-term roadmap places basic GitHub CI (`ci.yml` and `state-gate.yml`) before job state machine, Web MVP, AgentRunner, and API planner/auditor.

`task_packet.json` remains non-authoritative background state and explicitly says `decision_packet_controls_current_round`.

`current_state.json` remains the digest baseline for this engineering round.

`negative_results.json` contains reverse-solving prohibitions; this round does not enter reverse_solving and must not repeat those directions.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not implement Web UI, Web backend, API Planner, API Auditor, Job Manager, AgentRunner, self-hosted runner automation, database, queue, scheduler, or multi-agent orchestration in this round.

Do not add workflows that run LLM calls, push commits, create PRs, or modify remote state.

Do not add broad CI that scans full `solve_reports/` or executes reverse-solving samples.

Do not delete `project_state/codex_execution_report.md`.

Do not delete `project_state/gates/codex_report_auto_summary.json`.

Do not break parser support for `codex_report_summary`.

Do not claim full Codex naming removal while compatibility aliases, historical archives, `.codex-skills`, or legacy summary names remain.

Do not rename `.codex-skills/` or modify `.codex-skills/registry.json`.

Do not rewrite historical round archives.

Do not modify docs prompt files in this round.

Do not let `naming_migration_plan.json` carry stale decision_id or round_id when it is claimed as current evidence.

Do not weaken accepted checks for pytest_result PASSED, failed command block absence, archive parity, execution-log required command coverage, command-plan artifact parity, execute-decision contract, run-closeout final-success semantics, and nested closeout failure absence.

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
3. `.github/workflows/ci.yml` if present
4. `.github/workflows/state-gate.yml` if present
5. `project_state/gates/naming_migration_plan.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/command_plan.json`
10. `project_state/gates/execute_decision_result.json`
11. `project_state/gates/execution_log.json`
12. `project_state/gates/run_closeout_execution_log.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`
15. `project_state/gates/policy_impact_audit.json` if present
16. `project_state/gates/policy_lint_result.json` if present
17. current/previous round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, the current live report must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Which GitHub workflow files were created or updated, and what exact commands do they run?
2. How does `ci.yml` provide baseline repository validation without mutating project state or remote state?
3. How does `state-gate.yml` validate project_state / gate-sensitive changes using project_gate and pytest?
4. Does `naming_migration_plan.json` now carry current decision_id and round_id, or is it explicitly marked historical rather than current evidence?
5. Which test or final-check logic detects stale `naming_migration_plan.json` ids when the artifact is claimed as current evidence?
6. How were accepted neutral-primary report semantics preserved: `execution_report.md`, `execution_report_summary`, and legacy alias parity?
7. How were execute-decision `--mode execute`, command-plan authority, pytest_result transcript, execution-log, final-check, report-summary, and run-closeout convergence preserved?
8. How does this round avoid Web/AgentRunner/DB/queue/scheduler/reverse-solving/heavy artifact scope and forbidden path mutation?

Do not write TODO, TBD, PENDING, `should pass`, `expected to pass`, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed config / CI files:

- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`

Allowed generated or updated state artifacts:

- `project_state/execution_report.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/naming_migration_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/rounds/round_20260626_ci_state_gate_and_naming_provenance_v1/*`

Required behavior:

1. Add `.github/workflows/ci.yml` with bounded baseline checks. Prefer Python setup, dependency install, import check, and focused pytest. It must not run LLMs, push, or mutate state.
2. Add `.github/workflows/state-gate.yml` for changes under `project_state/**`, `reverse_agent/**`, `tests/**`, `.github/workflows/**`, `.codex-skills/**`, and `docs/prompts/**`. It should run project_gate checks and focused pytest appropriate to the current implementation.
3. Currentize `naming_migration_plan.json` ids or explicitly split current vs historical provenance so final-check/report does not treat stale ids as current evidence.
4. Add or update a gate/test that fails when a claimed-current naming migration plan has stale decision_id / round_id.
5. Preserve neutral-primary report source semantics from the previous accepted round.
6. Preserve legacy compatibility aliases.
7. Preserve execute-decision `--mode execute` and command-plan convergence.
8. Keep implementation small and avoid broad refactors.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Then use the accepted short execution path. Run preflight and command-plan first if needed, then execute only command-plan-authorized commands.

Preferred current-round entrypoint:

```powershell
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260626_ci_state_gate_and_naming_provenance_v1 --mode execute
```

At minimum, validation should include command-plan-authorized equivalents of:

```powershell
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260626_ci_state_gate_and_naming_provenance_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Also perform static validation of the new workflow files by checking YAML readability if a YAML parser is available, or by a bounded text/schema test in `tests/test_project_gate.py`.

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
- implementation requires sample-solving or heavy artifact scan.

Stop with `REWORK_REQUIRED` if:

- `.github/workflows/ci.yml` or `.github/workflows/state-gate.yml` is missing;
- workflows run LLM calls, push, create PRs, mutate repository state, or run reverse-solving samples;
- state-gate does not run any project_gate validation;
- CI workflow changes are not covered by tests or bounded validation;
- `naming_migration_plan.json` is claimed as current evidence but carries stale decision_id / round_id;
- no gate/test detects stale naming migration plan ids;
- `report_summary_synthesis.json.sources.execution_report` stops pointing to `project_state/execution_report.md`;
- final-check or closeout regresses to legacy-primary report wording;
- dual-file or dual-block semantic parity breaks;
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
