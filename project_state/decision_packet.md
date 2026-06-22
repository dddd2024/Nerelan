```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260622_run_closeout_log_isolation_v1",
  "round_id": "round_20260622_run_closeout_log_isolation_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260622_run_round_execute_pipeline_v1",
  "previous_round_id": "round_20260622_run_round_execute_pipeline_v1",
  "previous_acceptance": "ACCEPTED_WITH_LIMITATIONS",
  "primary_goal": "Isolate run-closeout subprocess/internal command logging so top-level pytest_result.txt contains only top-level command-plan authorized command blocks and command_plan_execution_authority can converge cleanly.",
  "command_plan_authority_required": true,
  "accepted_requires_no_unauthorized_command_execution": true,
  "accepted_requires_top_level_pytest_result_not_polluted_by_nested_closeout_commands": true,
  "accepted_requires_execution_log_current_round_consistency": true,
  "accepted_requires_report_status_success_when_only_historical_backlog_warning_remains": true,
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
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/rounds/round_20260622_run_closeout_log_isolation_v1/*"
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

Implement Run-Closeout Log Isolation v1.

The previous round implemented a bounded `run-round --execute` entrypoint and was accepted with limitations. The remaining design limitation is not the execute entrypoint itself. The issue is that `run-closeout` can run as a subprocess and append its own internal command blocks into the top-level `project_state/pytest_result.txt`. That pollutes the top-level command evidence with nested closeout-internal commands that are not part of the top-level `command-plan.commands`, which can make `command_plan_execution_authority` detect apparent unauthorized commands and force `PARTIAL` / `NEEDS_REVIEW` even when the intended top-level command was authorized.

This round must isolate nested closeout command evidence from the top-level execution evidence.

The intended outcome is:

- the top-level `pytest_result.txt` records the top-level command-plan commands only;
- the top-level `execution_log.json` validates against the top-level `command_plan.json` without seeing run-closeout internal commands as unauthorized;
- run-closeout internal command details remain auditable in a separate nested artifact, such as `project_state/gates/run_closeout_execution_log.json`, `project_state/gates/run_closeout_result.json`, or a scoped archive artifact;
- final-check can verify both top-level command-plan authority and nested closeout evidence without conflating the two scopes;
- if the only remaining warning is historical/backlog sample artifact state, the report can converge to `SUCCESS` / `ACCEPTED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only sample-solving context and must not control this round. Current execution authority is this `decision_packet.md`.

Previous accepted-with-limitations evidence:

- `decision_20260622_run_round_execute_pipeline_v1` added `run-round --execute`.
- Execute mode used command-plan as execution authority and preserved dry-run behavior.
- Tests passed for the new execute mode.
- `execution_log.json` and final-check could validate the command-plan chain, but the top-level status remained limited because summary/status convergence was affected by nested closeout logging.
- The execution-time limitation explicitly identified the problem: `run-closeout` subprocess appends internal command blocks to top-level `pytest_result.txt`, causing command-plan authority checks to see commands that were not top-level authorized commands.
- `status_policy_valid` may still report a non-blocking historical/backlog artifact warning; that warning alone must not prevent a successful engineering round.

Existing capabilities to reuse:

- `run-round --execute` and `run-round --dry-run`.
- `command-plan` command list and omitted-command logic.
- `execution-log` derivation from `pytest_result.txt` and command-plan.
- `run-closeout` and `run_closeout_result.json`.
- `report-auto-summary`.
- `report-summary` / `build_report_summary_synthesis()`.
- `final-check`.
- policy-lint and policy-impact.
- Existing fake command-runner based tests in `tests/test_project_gate.py`.

Artifact freshness:

- Current proof must be regenerated for this round.
- Prior artifacts may be used only as context, not as current acceptance evidence.
- Any artifact with older decision_id, round_id, or report_id is stale for this round.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this changes execution evidence semantics, command-plan should normally select or require `full` validation.
- Tests remain subordinate to command-plan.
- Closeout may run only if command-plan authorizes it and profile allows it.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect or run sample binaries.
- Do not use IDA, Ghidra, debuggers, emulators, runtime probes, solvers, harnesses, or full solve_reports scans.

## 3. Do Not Do

Do not build AgentRunner, Codex adapter, Trae adapter, job manager, database, queue, scheduler, daemon, Web UI, API planner, API auditor, or GitHub Actions workflow in this round.

Do not expand execute mode into arbitrary implementation command execution.

Do not weaken command-plan authority by ignoring unauthorized commands. The correct fix is scope separation: top-level command blocks must be validated against top-level command-plan, and closeout-internal command blocks must be recorded in a nested/closeout-specific artifact.

Do not simply delete closeout evidence. Closeout internals must remain auditable, but not as top-level command-plan commands.

Do not hide failing commands by dropping them from all artifacts.

Do not execute commands from `command-plan.omitted_commands`.

Do not change `.codex-skills/` or prompt docs.

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

Prior-round artifacts may be read only by exact path if needed to confirm the pollution pattern. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What exact nested closeout command pollution occurred previously, and which command blocks were incorrectly visible to the top-level command-plan authority check?
2. What log/evidence scopes now exist: top-level pytest_result / execution_log versus nested run-closeout command evidence?
3. Where are run-closeout internal commands recorded after the fix, and how are they linked to `run_closeout_result.json` or round archive artifacts?
4. How does top-level `execution_log.json` prove every top-level command came from `command-plan.commands` and no command came from `command-plan.omitted_commands`?
5. How does final-check validate closeout evidence without treating nested closeout internals as top-level unauthorized commands?
6. How does report-auto-summary / report-summary derive `SUCCESS` / `ACCEPTED` when command-plan authority, execution-log, final-check, and closeout pass and only historical/backlog sample warnings remain?
7. What regression tests prove nested closeout logs are isolated, top-level authorization remains strict, closeout internals remain auditable, and real unauthorized top-level commands still fail?
8. How does this round preserve `run-round --execute`, `run-round --dry-run`, command-plan authority, omitted-command blocking, status-kind handling, policy-lint, policy-impact, prompt-doc immutability, and closeout behavior?

Each answer must include concrete evidence and a status of `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. Do not write TODO, TBD, PENDING, or placeholder answers.

## 6. Implementation Scope

Implement one bounded fix: Run-Closeout Log Isolation v1.

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
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/rounds/round_20260622_run_closeout_log_isolation_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Identify the current mechanism by which `run-closeout` subprocess/internal commands append to top-level `project_state/pytest_result.txt`.
2. Introduce a scoped recording mechanism so top-level `pytest_result.txt` records only the top-level `run-closeout` command block and not the internal closeout command blocks.
3. Preserve closeout-internal command evidence in a nested artifact, for example `run_closeout_execution_log.json`, nested fields inside `run_closeout_result.json`, or a round archive artifact.
4. Ensure top-level `execution_log.json` ignores nested closeout internals and validates only top-level command-plan commands.
5. Ensure final-check still fails on real unauthorized top-level commands.
6. Ensure final-check can still audit closeout internals through their nested artifact/provenance.
7. Ensure report-auto-summary and report-summary include the nested artifact when generated and do not confuse it with top-level command blocks.
8. Ensure `status_policy_valid` treats historical/backlog sample artifact warnings as non-blocking for engineering rounds.
9. Preserve `run-round --execute` and `run-round --dry-run` behavior.
10. Add focused tests in `tests/test_project_gate.py` using fake command runners where possible.

Do not implement prompt rewriting, Web UI, job state machine, background worker, remote automation, or new agent adapters.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_run_closeout_log_isolation_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_run_closeout_log_isolation_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260622_run_closeout_log_isolation_v1
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level executed commands in `project_state/pytest_result.txt`, including command, relevant output, stderr if present, exit code, and conclusion. Do not include nested closeout-internal command blocks in the top-level command block stream. Record nested closeout command evidence in its scoped artifact.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- the fix would require weakening command-plan authority;
- closeout internals cannot be preserved anywhere after removing them from top-level pytest_result;
- implementation requires files outside allowed source scope;
- state updates require forbidden paths;
- final-check reports blocking reasons;
- execution-log shows unauthorized top-level commands or exit-code mismatches;
- report-auto-summary/report-summary/final-check become stale or disagree;
- Required Audit is incomplete.

Stop with `REWORK_REQUIRED` if tests fail, nested closeout internals still pollute top-level `pytest_result.txt`, closeout internals are no longer auditable, real unauthorized top-level command detection regresses, or the report remains `PARTIAL / NEEDS_REVIEW` for reasons other than explicitly non-blocking historical/backlog sample artifacts.
