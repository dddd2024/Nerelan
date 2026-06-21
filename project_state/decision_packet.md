```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_run_round_scaffold_v1",
  "round_id": "round_20260621_run_round_scaffold_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_codex_report_auto_summary_v1",
  "previous_round_id": "round_20260621_codex_report_auto_summary_v1",
  "previous_acceptance": "ACCEPTED",
  "primary_goal": "Add run-round scaffold v1 as a command-plan-governed orchestration scaffold without replacing Codex implementation work.",
  "command_plan_authority_required": true,
  "accepted_requires_run_round_result_artifact": true,
  "accepted_requires_dry_run_mode": true,
  "accepted_requires_no_unauthorized_command_execution": true,
  "accepted_requires_pytest_result_and_execution_log_compatibility": true,
  "accepted_requires_report_auto_summary_compatibility": true,
  "accepted_requires_final_check_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/codex_report_auto_summary.json",
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
    "project_state/gates/run_round_result.json",
    "project_state/rounds/round_20260621_run_round_scaffold_v1/*"
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

Add Run-Round Scaffold v1.

The previous accepted round added Codex Report Auto-Summary v1, so the project can now synthesize and validate `codex_report_summary` from structured artifacts. The next gap is orchestration shape: Codex still receives a long manual prompt and manually executes startup checks, preflight, command-plan, tests, gates, report-summary, final-check, and closeout.

This round must add a bounded `run-round` scaffold that produces a structured orchestration artifact and validates the current command-plan-governed execution contract. It must not replace Codex as the implementation actor and must not execute arbitrary implementation work. v1 is a scaffold/dry-run and validation layer that prepares the project for a later full `execute-decision` runner.

The intended outcome is:

- a CLI entrypoint such as `python -m reverse_agent.project_gate run-round --state-dir project_state --round-id <round_id> --dry-run`;
- a structured artifact `project_state/gates/run_round_result.json`;
- command-plan recognition for the `run-round` command kind;
- report-summary/final-check/generated-artifact coverage for `run_round_result.json`;
- tests proving the scaffold is command-plan-governed and does not run omitted or unauthorized commands.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is background only. It still describes stale `samplereverse` work and must not control this round.

Previous round status: `decision_20260621_codex_report_auto_summary_v1` was accepted. Its evidence showed:

- `project_state/gates/codex_report_auto_summary.json` was generated with `gate_status=PASSED`.
- `codex_report_summary` was synthesized from structured evidence and remained consistent with the live report summary.
- `execution_log.json` was used as the source for `tests_ran`.
- report-summary and final-check passed.
- `report_auto_summary_consistency` passed.
- `tests/test_project_gate.py -q` passed with 740 tests.
- combined `tests/test_project_gate.py tests/test_project_state.py -q` passed with 1038 tests.
- closeout passed.

Current gap:

- The workflow still lacks a canonical run-round entrypoint.
- Startup/preflight/command-plan/gate execution order exists as prompt text and tests, but not as a structured run-round artifact.
- Command-plan already contains command kind concepts and required command kinds, but v1 needs a safe run-round scaffold before any full automation.

Existing capabilities to reuse:

- command-plan and command kind classification
- preflight checks and baseline capture
- execution_log.json
- codex_report_auto_summary.json
- report-summary synthesis
- final-check command authority and artifact coverage checks
- run-closeout and round archive behavior
- tests in `tests/test_project_gate.py`

This is not a reverse-solving round. Do not inspect or run sample binaries. Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or full `solve_reports/`.

## 3. Do Not Do

Do not build a full autonomous runner in this round.

Do not make `run-round` execute arbitrary implementation commands, edit source files, solve samples, call tools, or run background work.

Do not replace Codex implementation work. Codex still performs implementation under `decision_packet.md` and command-plan constraints.

Do not replace `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, report-summary, final-check, or run-closeout.

Do not bypass command-plan. The run-round scaffold must read or generate command-plan and must never bless omitted or unauthorized commands.

Do not make run-round recursively execute itself unless explicitly operating in a bounded dry-run/plan-only mode.

Do not add database, queue, scheduler, AgentRunner service, web UI, daemon, or message bus.

Do not generate Required Audit answers or full report bodies.

Do not modify prompt docs in this round.

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

Then inspect only files relevant to run-round scaffold:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/codex_report_auto_summary.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/round_delta_summary.json`
9. `project_state/gates/run_closeout_result.json`
10. `project_state/gates/run_round_result.json` if it already exists

Historical files may be read only by exact path when needed for a focused regression fixture. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What does Run-Round Scaffold v1 do, and what does it explicitly not do?
2. What schema does `project_state/gates/run_round_result.json` use, and which fields are required?
3. How does the scaffold derive its phase order from startup checks, preflight, command-plan, execution-log, report-auto-summary, report-summary, final-check, and closeout without executing arbitrary implementation work?
4. How does run-round remain subordinate to command-plan, including handling omitted commands and unauthorized commands?
5. How are `run_round_result.json`, `execution_log.json`, `codex_report_auto_summary.json`, and `pytest_result.txt` kept compatible?
6. How does final-check/report-summary cover `run_round_result.json` as a generated gate artifact?
7. What regression tests prove dry-run behavior, command-plan authority, no recursion, no unauthorized execution, artifact coverage, and backward compatibility?
8. How does this round preserve structured execution log, report-auto-summary, policy-impact, policy-lint, command-plan authority, report-summary, final-check, closeout, and prompt-doc behavior?

## 6. Implementation Scope

Implement one bounded feature: Run-Round Scaffold v1.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/codex_report_auto_summary.json`
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
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260621_run_round_scaffold_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Add a CLI entrypoint such as `python -m reverse_agent.project_gate run-round --state-dir project_state --round-id <round_id> --dry-run`.
2. The v1 command must produce `project_state/gates/run_round_result.json` and must not execute arbitrary implementation commands or mutate source/test files.
3. The artifact must include at minimum: `schema_version`, `artifact_name`, `gate_name`, `gate_status`, `decision_id`, `round_id`, `generated_at`, `mode`, `phases`, `authorized_commands`, `omitted_commands`, `would_run_commands`, `skipped_commands`, `warnings`, `blocking_reasons`, and `recommended_next_action`.
4. In dry-run mode, record the intended phase order and command-plan-authorized commands without executing them.
5. If command-plan contains omitted commands, record them and ensure run-round does not mark them as runnable.
6. If a command is not present in command-plan, run-round must not include it in `would_run_commands`.
7. Add command kind recognition and expected-exit-code handling for run-round if needed, without weakening command-plan authority.
8. Add `run_round_result.json` to reportable gate artifact coverage and closeout/archive coverage when present.
9. Ensure report-summary/final-check can require or validate `run_round_result.json` when the command was run.
10. Add regression tests for dry-run output, command-plan integration, omitted-command handling, no-recursive-execution behavior, generated artifact coverage, and backward compatibility when run-round is absent.

Do not implement a full execution runner. v1 is a scaffold and validation artifact only.

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

Run policy-lint, policy-impact, execution-log, report-auto-summary, and run-round only if command-plan explicitly includes or authorizes them:

```powershell
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260621_run_round_scaffold_v1 --dry-run
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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_run_round_scaffold_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation for unrelated reasons;
2. this requires a full runner, scheduler, AgentRunner, background execution, database, queue, web UI, daemon, or message bus;
3. run-round must execute arbitrary implementation commands to pass;
4. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
5. prompt docs, `.codex-skills/`, or forbidden project_state source files need changes;
6. the implementation replaces or removes `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, report-summary, final-check, or run-closeout;
7. command-plan authority becomes weaker or run-round marks omitted/unauthorized commands as runnable;
8. run-round can recursively execute itself in v1;
9. the fix requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
10. structured execution log, report-auto-summary, policy-impact, policy-lint, command-plan authority, decision-command-plan conflict detection, report-summary, final-check, or closeout regresses;
11. tests fail or any required command exit code is nonzero;
12. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
