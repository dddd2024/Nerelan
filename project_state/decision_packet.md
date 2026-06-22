```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260622_run_round_execute_pipeline_v1",
  "round_id": "round_20260622_run_round_execute_pipeline_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260622_closeout_consistency_evidence_rework_v1",
  "previous_round_id": "round_20260622_closeout_consistency_evidence_rework_v1",
  "previous_acceptance": "ACCEPTED",
  "primary_goal": "Add a bounded run-round execute pipeline so Codex can invoke one project entrypoint for command-plan-authorized gate/test/closeout commands instead of manually running the full pipeline.",
  "command_plan_authority_required": true,
  "accepted_requires_no_unauthorized_command_execution": true,
  "accepted_requires_pytest_result_and_execution_log_compatibility": true,
  "accepted_requires_current_round_final_check": true,
  "accepted_requires_closeout_when_authorized": true,
  "accepted_requires_prompt_unchanged": true,
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
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/rounds/round_20260622_run_round_execute_pipeline_v1/*"
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

Implement Run-Round Execute Pipeline v1.

The previous accepted round closed the evidence gap: current-round `codex_execution_report.md`, `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, and closeout artifacts were consistent and accepted. The next project step is to reduce manual Codex prompting by making the project provide a single safe entrypoint for running the command-plan-authorized validation pipeline.

This round must add a bounded execute mode to the existing `run-round` scaffold or an equivalent project-gate entrypoint that performs only command-plan-authorized gate/status/test/closeout commands. It must not become a general agent runner and must not execute arbitrary implementation/edit commands.

Intended user-facing direction after this round:

```powershell
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id <round_id> --execute
```

or an equivalent explicit project-gate command if the implementation chooses a clearer name. The command must:

- perform startup/preflight/command-plan checks;
- obey `project_state/gates/command_plan.json` as the execution authority;
- execute only authorized commands, never omitted commands;
- record command output and exit codes into `project_state/pytest_result.txt` or a compatible structured path consumed by `execution-log`;
- regenerate `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, and `final_gate_result.json`;
- run closeout only when command-plan authorizes it and the gate profile allows it;
- preserve dry-run behavior.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only sample-solving context and must not control this round.

Current decision control: this `decision_packet.md` controls the current round. `task_packet.task` is not execution authority.

Accepted previous evidence:

- `decision_20260622_closeout_consistency_evidence_rework_v1` was accepted.
- Its report status was `SUCCESS` and `acceptance_recommendation` was `ACCEPTED`.
- Its command-plan used `full` profile, `closeout_allowed: true`, and `omitted_commands: []`.
- Its `pytest_result.txt` recorded command-plan, run-round dry-run, preflight, report-summary, final-check, two pytest commands, policy-lint, policy-impact, execution-log, report-auto-summary, and run-closeout.
- Its `execution_log.json` was current-round, derived from `pytest_result.txt` and `command_plan.json`, and had no warnings or blocking reasons.
- Its `final_gate_result.json` passed, with `command_plan_execution_authority`, `report_summary_fields_match_synthesis`, `stale_artifact_ids`, `required_audit_coverage`, `execution_log_consistency`, and `report_auto_summary_consistency` all passing.
- Historical/backlog sample artifact gaps remain non-blocking for engineering rounds.

Existing capabilities to reuse:

- `run-round --dry-run` scaffold and `run_round_result.json`.
- `command-plan` profile/kind classification and omitted-command logic.
- `preflight`.
- `execution-log` derived from `pytest_result.txt` and command-plan.
- `report-auto-summary`.
- `report-summary` / `build_report_summary_synthesis()`.
- `final-check`.
- `run-closeout`.
- policy-lint and policy-impact gates.
- Existing regression tests in `tests/test_project_gate.py`.

Artifact freshness:

- Current evidence must come from this round.
- Do not treat prior accepted artifacts as current proof after implementation.
- Any artifact with older `decision_id`, `round_id`, or `report_id` is stale for this round.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this changes project-gate execution behavior, command-plan should normally select or require `full` validation.
- Tests must remain subordinate to command-plan.
- Closeout may run only when command-plan authorizes it and profile allows it.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect or run sample binaries.
- Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, solvers, or full `solve_reports/` scans.

## 3. Do Not Do

Do not build AgentRunner, Codex adapter, Trae adapter, job manager, database, queue, scheduler, daemon, web UI, API planner, API auditor, or GitHub Actions workflow in this round.

Do not make the new execute mode run arbitrary implementation commands, source editing commands, package installation, network commands, git commit/push, branch changes, PR creation, rebase, merge, or remote mutation.

Do not weaken command-plan authority. The execute mode must be stricter than manual execution, not looser.

Do not execute commands listed in `command-plan.omitted_commands`.

Do not hide failing commands by dropping them from `pytest_result.txt`, `execution_log.json`, or `run_round_result.json`.

Do not change `.codex-skills/` or prompt docs in this round.

Do not introduce a `medium` profile.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `.codex-skills/registry.json`, or `docs/prompts/*`.

Do not continue `samplereverse` solving or any sample-solving work.

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message.

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

Then inspect relevant implementation and gate files:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/run_round_result.json`
6. `project_state/gates/run_closeout_result.json`
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/codex_report_auto_summary.json`
10. `project_state/gates/policy_lint_result.json`
11. `project_state/gates/policy_impact_audit.json`
12. `project_state/gates/round_baseline.json`
13. `project_state/gates/round_delta_summary.json`
14. `project_state/gates/round_close_snapshot.json`

Prior-round artifacts may be read only by exact path if needed to understand accepted behavior. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What exact command or CLI option was added or changed, and how should a human/Codex invoke it?
2. What command kinds can execute mode run, and what command kinds are blocked or never executed?
3. How does execute mode prove that every executed command came from `command-plan.commands` and no command came from `command-plan.omitted_commands`?
4. How does execute mode record stdout/stderr or relevant output, exit codes, and command order so `execution-log` can validate it?
5. How does execute mode handle failing commands, expected exit codes, and stop conditions?
6. How does execute mode preserve dry-run behavior and existing run-round artifacts?
7. How does execute mode integrate with report-auto-summary, report-summary, final-check, and run-closeout without causing recursion or stale artifact IDs?
8. What regression tests prove: dry-run unchanged, execute mode uses only authorized commands, omitted commands are blocked, unauthorized commands are not run, pytest_result/execution_log compatibility holds, closeout runs only when authorized, and real failures are surfaced?

Each Required Audit item must include evidence and status. Use only `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. Do not write TODO/TBD/PENDING placeholders.

## 6. Implementation Scope

Implement one bounded feature: Run-Round Execute Pipeline v1.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260622_run_round_execute_pipeline_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Add an explicit execute mode to `run-round` or an equivalent `project_gate` command. The mode name must be unambiguous, for example `--execute`.
2. Preserve existing `--dry-run` behavior exactly.
3. Load or generate command-plan before executing any non-startup/preflight command.
4. Build the executable command list exclusively from `command-plan.commands`.
5. Refuse commands from `command-plan.omitted_commands`.
6. Refuse unknown or unsupported command kinds unless they are explicitly modeled and tested.
7. Prevent recursion: execute mode must not recursively execute itself or an unbounded closeout loop.
8. Record command blocks in `pytest_result.txt` or a compatible structured result consumed by `execution-log`.
9. Preserve expected-exit-code semantics from command-plan.
10. Stop on blocking command failures unless command-plan marks the command as diagnostic and expected exit code permits continuation.
11. Ensure `execution-log`, `report-auto-summary`, `report-summary`, and `final-check` can validate the execute-mode run.
12. Run closeout only if command-plan authorizes it and closeout is allowed.
13. Add focused tests in `tests/test_project_gate.py` for execute-mode behavior using a fake command runner; do not rely on real external commands for unit tests.

Do not implement prompt rewriting, Web UI, job state machine, background worker, or remote automation.

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

Generate command-plan and obey it:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

After implementation, run only command-plan-authorized commands. If authorized, expected validation includes:

```powershell
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_run_round_execute_pipeline_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_run_round_execute_pipeline_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260622_run_round_execute_pipeline_v1
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all executed commands in `project_state/pytest_result.txt`, including command, relevant output, stderr if present, exit code, and conclusion.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- execute mode would need to run a command not present in `command-plan.commands`;
- execute mode would run a command present in `command-plan.omitted_commands`;
- execute mode would run arbitrary implementation/source-editing/remote mutation commands;
- implementation requires files outside allowed source scope;
- state updates require forbidden paths;
- final-check reports blocking reasons;
- execution-log shows unauthorized commands or exit-code mismatches;
- report-auto-summary/report-summary/final-check become stale or disagree;
- Required Audit is incomplete.

Stop with `REWORK_REQUIRED` if tests fail, dry-run behavior regresses, closeout recursion occurs, omitted commands are executed, unsupported command kinds execute, or `pytest_result.txt` cannot serve as auditable execution evidence.
