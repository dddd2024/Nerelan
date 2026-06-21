```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_structured_execution_log_v1",
  "round_id": "round_20260621_structured_execution_log_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_policy_impact_generated_artifacts_coverage_fix_v1",
  "previous_round_id": "round_20260621_policy_impact_generated_artifacts_coverage_fix_v1",
  "previous_acceptance": "ACCEPTED",
  "primary_goal": "Add structured execution log v1 while keeping pytest_result.txt as the human-readable execution record.",
  "command_plan_authority_required": true,
  "accepted_requires_execution_log_artifact": true,
  "accepted_requires_command_plan_authority_reads_execution_log_when_available": true,
  "accepted_requires_pytest_result_backward_compatibility": true,
  "accepted_requires_final_check_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/rounds/round_20260621_structured_execution_log_v1/*"
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

Add Structured Execution Log v1 while preserving `project_state/pytest_result.txt` as the human-readable execution record.

The current gate pipeline verifies executed commands by parsing command blocks from `pytest_result.txt`. That works, but it is brittle: command-plan authority, report-summary, final-check, closeout, and future report automation all need a structured command ledger instead of relying only on text parsing. This round must add a bounded structured execution log artifact that records command executions in machine-readable JSON and lets gates use it when available.

This is an engineering infrastructure round. The goal is not to build full automation or a new runner yet. The goal is to add the structured log format, artifact accounting, validation checks, and compatibility behavior needed for the later `run-round` / `execute-decision` and auto-report-summary work.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is background only. It still describes stale `samplereverse` work and must not control this round.

Previous round status: `decision_20260621_policy_impact_generated_artifacts_coverage_fix_v1` was accepted. Its evidence showed:

- `codex_report_summary.generated_artifacts` now includes `project_state/gates/policy_impact_audit.json` and other reportable gate artifacts.
- report-summary/final-check now detect missing generated gate artifacts.
- `pytest_result_summary.status` was `PASSED`.
- `tests/test_project_gate.py -q` passed with 712 tests.
- `tests/test_project_gate.py tests/test_project_state.py -q` passed with 1010 tests.
- `policy-lint`, `policy-impact`, `decision-lint`, `report-summary`, `final-check`, and `run-closeout` all passed.

Current gap:

- `pytest_result.txt` is still the only complete command execution record.
- command-plan authority still depends heavily on parsing text command blocks.
- future auto-report-summary and run-round/execute-decision will need a structured command ledger with command, kind, phase, expected_exit_codes, actual_exit_code, start/end timestamps if available, and stdout/stderr references or summaries.

Existing relevant capabilities to reuse:

- command-plan artifact and expected command list
- command kind and command-plan authority checks
- pytest_result command block parsing
- report-summary synthesis
- final-check checks for command coverage and unauthorized commands
- generated artifact coverage logic for gate artifacts
- run-closeout and round archive behavior
- tests in `tests/test_project_gate.py`

This is not a reverse-solving round. Do not inspect or run sample binaries. Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or full `solve_reports/`.

## 3. Do Not Do

Do not implement a full runner, scheduler, AgentRunner, background worker, database, message queue, workflow engine, or web UI.

Do not replace `project_state/pytest_result.txt`. It remains the required human-readable execution record and must still be written.

Do not remove existing pytest_result parsing in this round. Structured execution log should be additive and backward-compatible.

Do not weaken command-plan authority. If structured execution log and pytest_result disagree, final-check must not silently accept the mismatch.

Do not make execution_log a long-term dynamic memory store. It is a current-round gate artifact under `project_state/gates/`, not a skill, prompt, or historical database.

Do not log full huge stdout/stderr bodies into a separate heavy artifact unless already present in `pytest_result.txt`. Keep v1 compact.

Do not modify prompt docs in this round. The stable docs were accepted previously and are not the target here.

Do not change profile names. The current profile names are `fast`, `standard`, and `full`; do not introduce `medium`.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `.codex-skills/registry.json`, or `docs/prompts/*`.

Do not continue `samplereverse` solving. Do not run samples, solvers, harnesses, runtime probes, IDA/Ghidra, debuggers, emulators, GUI workflows, or full `solve_reports/` scans.

Do not push, commit, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Then inspect only files relevant to structured execution logging:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/round_delta_summary.json`
7. `project_state/gates/run_closeout_result.json`
8. `project_state/gates/execution_log.json` if it already exists

Historical files may be read only by exact path when needed for a focused regression fixture. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What schema does `project_state/gates/execution_log.json` use, and which fields are required per command entry?
2. How is `execution_log.json` created or derived in v1, and why does `pytest_result.txt` remain required?
3. How does command-plan authority use `execution_log.json` when available, and how does it fall back to `pytest_result.txt` when absent?
4. How does final-check detect mismatches between `execution_log.json`, `pytest_result.txt`, `codex_report_summary.tests_ran`, and `command_plan.commands`?
5. How is `execution_log.json` included in `generated_artifacts`, report-summary synthesis, final-check artifact coverage, and round archive coverage?
6. How does v1 avoid creating a heavy runtime log, database, queue, background runner, or replacing pytest_result?
7. What regression tests prove authorized commands pass, unauthorized commands fail, omitted commands fail, mismatch with pytest_result fails, and absence of execution_log remains backward-compatible?
8. How does this round preserve policy-impact, policy-lint, command-plan authority, report-summary, final-check, closeout, and prompt-doc behavior?

## 6. Implementation Scope

Implement one bounded feature: Structured Execution Log v1 as a current-round gate artifact.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/rounds/round_20260621_structured_execution_log_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Define a compact JSON schema for `project_state/gates/execution_log.json`. At minimum include `schema_version`, `artifact_name`, `decision_id`, `round_id`, `report_id` if known, `generated_at`, `source`, `commands`, `warnings`, `blocking_reasons`, and `recommended_next_action`.
2. Each command entry must include at least `index`, `command`, `kind` if known, `phase` if known, `expected_exit_codes`, `exit_code`, and `status` such as `PASSED`, `FAILED`, or `UNKNOWN`.
3. In v1, allow the artifact to be derived from the existing `pytest_result.txt` command blocks plus `command_plan.json`. Do not require a new command runner yet.
4. Add a CLI entrypoint such as `python -m reverse_agent.project_gate execution-log --state-dir project_state` to generate or validate the artifact, if this fits existing project_gate structure.
5. Update report-summary/final-check to include `execution_log.json` in generated gate artifact accounting when present.
6. Update command-plan authority validation to prefer structured execution_log entries when available, while retaining pytest_result fallback for backward compatibility.
7. Add checks so a `SUCCESS` / `ACCEPTED` report fails if execution_log and pytest_result disagree on executed command list or exit codes.
8. Add tests for authorized commands, unauthorized commands, omitted commands, command/exit mismatch, missing execution_log fallback, generated_artifacts coverage, and closeout archive coverage.

Do not build automatic report generation in this round. This round only supplies the structured execution substrate.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Run preflight before implementation:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
```

If preflight passes, run command-plan and follow only command-plan-authorized commands:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Targeted tests:

```powershell
python -m pytest tests/test_project_gate.py -q
```

Run policy-lint, policy-impact, and execution-log only if command-plan explicitly includes or authorizes them:

```powershell
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
```

Final validation commands, only when authorized by command-plan:

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Run closeout only if command-plan explicitly includes or authorizes the closeout command for this round:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_structured_execution_log_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation for unrelated reasons;
2. this requires a full runner, scheduler, AgentRunner, database, queue, web UI, or execution automation beyond generating/validating a structured log;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. prompt docs, `.codex-skills/`, or forbidden project_state source files need changes;
5. the implementation replaces or removes `pytest_result.txt` instead of preserving it;
6. command-plan authority becomes weaker when execution_log exists;
7. execution_log and pytest_result can disagree while final-check still passes for a SUCCESS report;
8. the fix requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
9. policy-impact, policy-lint, command-plan authority, decision-command-plan conflict detection, report-summary, final-check, or closeout regresses;
10. tests fail or any required command exit code is nonzero;
11. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
