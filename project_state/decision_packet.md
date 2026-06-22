```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260622_run_closeout_log_isolation_evidence_rework_v1",
  "round_id": "round_20260622_run_closeout_log_isolation_evidence_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260622_run_closeout_log_isolation_v1",
  "previous_round_id": "round_20260622_run_closeout_log_isolation_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "primary_goal": "Close the run-closeout log isolation evidence gap by regenerating current-round top-level pytest_result, execution_log, report summary, final-check, and closeout/archive artifacts without stale prior-round command blocks.",
  "command_plan_authority_required": true,
  "accepted_requires_top_level_pytest_result_current_round_only": true,
  "accepted_requires_no_prior_round_command_blocks": true,
  "accepted_requires_run_closeout_nested_log_current_round": true,
  "accepted_requires_execution_log_passed_without_unauthorized_warnings": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_report_status_success": true,
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
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_round_result.json",
    "project_state/rounds/round_20260622_run_closeout_log_isolation_evidence_rework_v1/*"
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

Complete Run-Closeout Log Isolation Evidence Rework v1.

The previous round attempted to isolate `run-closeout` internal command logging from top-level `pytest_result.txt`, but audit returned `REWORK_REQUIRED`. The implementation may contain useful log-isolation code and tests, but current-round evidence did not close: top-level `pytest_result.txt` and `execution_log.json` still contained commands from `round_20260622_run_round_execute_pipeline_v1`, while command-plan expected `round_20260622_run_closeout_log_isolation_v1`. Report-summary and final-check failed, and `codex_report_summary` remained `PARTIAL` / `NEEDS_REVIEW`.

This round is an evidence-closure rework with minimal code fixes only if necessary. It must regenerate the current round from a clean top-level command record so that:

- top-level `pytest_result.txt` contains only commands authorized by the current round command-plan;
- top-level `pytest_result.txt` contains no command block or artifact reference from `round_20260622_run_round_execute_pipeline_v1`;
- current-round `run-round --dry-run`, `run-round --execute`, and `run-closeout` commands are recorded when command-plan authorizes them;
- `run-closeout` internal command blocks remain auditable in a nested/scoped artifact such as `run_closeout_execution_log.json`, not in the top-level command stream;
- `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, and `final_gate_result.json` all carry this rework round ID;
- report-summary and final-check pass;
- if only historical/backlog sample artifact notices remain, `codex_report_summary.status` must converge to `SUCCESS` with `acceptance_recommendation: ACCEPTED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only sample-solving state and does not control this round. This `decision_packet.md` is the current round authority.

Previous audit findings:

- `decision_20260622_run_closeout_log_isolation_v1` was valid and approved, but execution was not accepted.
- `codex_execution_report.md` remained `PARTIAL` / `NEEDS_REVIEW`.
- Required Audit item 6 acknowledged that current report-auto-summary still showed `PARTIAL` because stale gate artifacts had not been regenerated for the current round IDs.
- `pytest_result_summary.status` was `PARTIAL`.
- `report-summary` failed with `pytest_result_summary.tests_ran omits command_plan commands` and ID/list diffs.
- `final-check` failed on decision/report mismatch, archive mismatch, command-plan coverage, exit-code coverage, stale artifact IDs, report-summary mismatch, and status policy.
- `execution_log.json` warned that commands from `round_20260622_run_round_execute_pipeline_v1` were not in current `command_plan.commands` and that current-round `run-round` / `run-closeout` commands were missing.
- The top-level evidence stream still contained prior-round commands, so the round did not prove the log-isolation fix.

Existing capabilities to reuse:

- `run-round --execute` and `run-round --dry-run`.
- `command-plan` and omitted-command authority checks.
- `execution-log` derived from top-level `pytest_result.txt` and command-plan.
- `run-closeout`, `run_closeout_result.json`, and any scoped closeout log implementation from the previous attempt.
- `report-auto-summary`.
- `report-summary` / `build_report_summary_synthesis()`.
- `final-check`.
- `policy-lint` and `policy-impact`.
- Existing log-isolation regression tests in `tests/test_project_gate.py`.

Artifact freshness:

- Any artifact or command block mentioning `round_20260622_run_round_execute_pipeline_v1` is stale for this round.
- Any artifact from `round_20260622_run_closeout_log_isolation_v1` is prior-attempt context only, not current acceptance evidence.
- Current proof must be regenerated with `decision_20260622_run_closeout_log_isolation_evidence_rework_v1` and `round_20260622_run_closeout_log_isolation_evidence_rework_v1`.
- Historical/backlog sample artifacts remain non-blocking for this engineering round unless code claims sample-solving progress.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this touches execution evidence, status derivation, and closeout behavior, command-plan should use or require `full` validation.
- Tests remain subordinate to command-plan.
- Closeout may run only if command-plan authorizes it and profile allows it.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect or run sample binaries.
- Do not use IDA, Ghidra, debuggers, emulators, runtime probes, solvers, harnesses, or full `solve_reports/` scans.

## 3. Do Not Do

Do not add new architecture or expand scope beyond closing the log-isolation evidence gap.

Do not build AgentRunner, Codex adapter, Trae adapter, job manager, database, queue, scheduler, daemon, Web UI, API planner, API auditor, GitHub Actions workflow, or background worker.

Do not weaken command-plan authority. Real unauthorized top-level commands must still fail or warn.

Do not suppress errors by deleting evidence. Top-level evidence and nested closeout evidence must both remain auditable.

Do not execute commands from `command-plan.omitted_commands`.

Do not treat prior-round artifacts or command blocks as current evidence.

Do not allow `round_20260622_run_round_execute_pipeline_v1` command blocks to remain in top-level `pytest_result.txt` for this round.

Do not modify `.codex-skills/` or prompt docs.

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

Then inspect relevant files:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/run_round_result.json`
6. `project_state/gates/run_closeout_result.json`
7. `project_state/gates/run_closeout_execution_log.json` if present
8. `project_state/gates/report_summary_synthesis.json`
9. `project_state/gates/final_gate_result.json`
10. `project_state/gates/codex_report_auto_summary.json`
11. `project_state/gates/policy_lint_result.json`
12. `project_state/gates/policy_impact_audit.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`
15. `project_state/gates/round_close_snapshot.json`

Prior-round artifacts may be read only by exact path if needed to diagnose stale-command leakage. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. Which prior-round command blocks or artifact IDs caused the previous `REWORK_REQUIRED`, and where were they found?
2. How was top-level `pytest_result.txt` rebuilt so it contains only this rework round's command-plan-authorized commands?
3. How does the current top-level `execution_log.json` prove there are no stale `round_20260622_run_round_execute_pipeline_v1` command blocks and no unauthorized top-level commands?
4. Where is nested `run-closeout` internal command evidence recorded now, and how is it linked to `run_closeout_result.json` or round archive artifacts?
5. Which current-round command-plan commands were authorized, executed, skipped, or omitted, and why?
6. How do `report-auto-summary`, `report-summary`, and `final-check` agree on current `report_id`, `round_id`, `based_on_decision_id`, `files_changed`, `tests_ran`, and `generated_artifacts`?
7. What tests prove log isolation, top-level authorization strictness, closeout auditability, stale round exclusion, real unauthorized command detection, and status convergence?
8. How does this rework preserve `run-round --execute`, `run-round --dry-run`, command-plan authority, omitted-command blocking, policy-lint, policy-impact, prompt-doc immutability, and closeout behavior?

Each answer must include concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. Do not write TODO, TBD, PENDING, or placeholders.

## 6. Implementation Scope

Primary scope: close the evidence gap and fix any minimal source issue that prevents clean current-round evidence.

Allowed source changes only if required:

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
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260622_run_closeout_log_isolation_evidence_rework_v1/*` only if command-plan authorizes closeout

Required behavior:

1. Establish a current-round baseline before modifications.
2. Regenerate a clean top-level `pytest_result.txt` for this rework round.
3. Ensure top-level `pytest_result.txt` records current round command-plan commands, including current `run-round --dry-run`, current `run-round --execute`, and current `run-closeout` if authorized.
4. Ensure top-level `pytest_result.txt` contains no stale command block or command text from `round_20260622_run_round_execute_pipeline_v1`.
5. Ensure nested `run-closeout` internals are written to scoped closeout evidence, not top-level command blocks.
6. Regenerate current-round `execution_log.json` and make it pass without stale/unauthorized command warnings.
7. Regenerate current-round `codex_report_auto_summary.json`, `report_summary_synthesis.json`, and `final_gate_result.json`.
8. Run closeout if command-plan authorizes it and archive current-round report/pytest/decision/manifest artifacts.
9. Ensure `report-summary` and `final-check` pass after closeout.
10. Ensure `codex_report_summary.status` is `SUCCESS` and `acceptance_recommendation` is `ACCEPTED` unless a real blocker remains.
11. Preserve tests from the previous log-isolation attempt and add focused regression only if needed.

Do not implement new user-facing features.

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

After implementation or evidence cleanup, run only command-plan-authorized commands. If authorized, expected validation includes:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_run_closeout_log_isolation_evidence_rework_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_run_closeout_log_isolation_evidence_rework_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260622_run_closeout_log_isolation_evidence_rework_v1
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands in `project_state/pytest_result.txt`. Do not include nested closeout-internal command blocks in the top-level command stream. Record nested closeout command evidence in its scoped artifact.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- top-level `pytest_result.txt` cannot be rebuilt without stale prior-round command blocks;
- nested closeout internals cannot be preserved after removing them from top-level command blocks;
- implementation requires files outside allowed source scope;
- state updates require forbidden paths;
- final-check reports blocking reasons after rerun;
- execution-log shows unauthorized top-level commands or stale prior-round commands;
- report-auto-summary/report-summary/final-check remain stale or disagree;
- Required Audit is incomplete.

Stop with `REWORK_REQUIRED` if tests fail, top-level `pytest_result.txt` still contains `round_20260622_run_round_execute_pipeline_v1`, current-round `run-round` / `run-closeout` command blocks are missing, closeout internals are no longer auditable, real unauthorized top-level command detection regresses, or the report remains `PARTIAL / NEEDS_REVIEW` for reasons other than explicitly non-blocking historical/backlog sample artifacts.
