```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260622_closeout_consistency_evidence_rework_v1",
  "round_id": "round_20260622_closeout_consistency_evidence_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260622_report_auto_summary_closeout_consistency_v1",
  "previous_round_id": "round_20260622_report_auto_summary_closeout_consistency_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "primary_goal": "Complete the current-round evidence pipeline for report-auto-summary closeout consistency and replace stale prior-round gate artifacts with current-round artifacts.",
  "command_plan_authority_required": true,
  "accepted_requires_current_round_execution_log": true,
  "accepted_requires_current_round_final_check": true,
  "accepted_requires_current_round_report_auto_summary": true,
  "accepted_requires_pytest_result_covering_command_plan": true,
  "accepted_requires_codex_report_summary_success_or_explicit_blocked_failure": true,
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
    "project_state/rounds/round_20260622_closeout_consistency_evidence_rework_v1/*"
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

Complete Closeout Consistency Evidence Rework v1.

The previous round attempted to fix report-auto-summary / closeout consistency, but the audit result was `REWORK_REQUIRED`. The implementation may contain useful code and tests, but the execution evidence is incomplete and several critical gate artifacts still refer to the older `round_20260621_run_round_scaffold_v1` round. This round is an evidence-closure and current-round gate-artifact rework, not a new feature expansion.

The goal is to complete the full command-plan-authorized validation pipeline for the current round and regenerate all required structured artifacts so that `codex_execution_report.md`, `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, and closeout artifacts all match this rework round.

Acceptance requires:

- current `decision_id`, `round_id`, and `report_id` are consistent across report, pytest result, execution log, auto-summary, synthesis, final-check, and closeout artifacts;
- no stale prior-round gate artifact is used as current evidence;
- command-plan full profile is followed, or any deviation is explicitly blocked by command-plan and recorded;
- `pytest_result.txt` records every executed command, stdout/stderr or relevant output, exit code, and conclusion;
- `execution_log.json` is derived from the current `pytest_result.txt` and current `command_plan.json`;
- `final-check` is run for the current round and has no blocking reasons;
- `codex_report_summary.status` is `SUCCESS` with `acceptance_recommendation: ACCEPTED`, unless there is a real blocker, in which case status must be `BLOCKED` or `FAILED` with exact cause.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only sample state for `samplereverse`; it must not control this round. The current execution authority is this `decision_packet.md`.

Relevant audit findings from the previous round:

- `decision_20260622_report_auto_summary_closeout_consistency_v1` was valid and approved, but its Codex report stayed `PARTIAL` / `NEEDS_REVIEW`.
- That report only recorded three commands: preflight, command-plan `--json`, and `python -m pytest tests/test_project_gate.py -q --tb=line`.
- Its `command_plan.json` used `full` profile, `closeout_allowed: true`, and listed many required commands including report-summary, final-check, run-round, two pytest commands, policy-lint, policy-impact, execution-log, report-auto-summary, and run-closeout.
- `pytest_result.txt` did not record the full command-plan pipeline.
- `execution_log.json`, `final_gate_result.json`, `codex_report_auto_summary.json`, and `report_summary_synthesis.json` still referred to `decision_20260621_run_round_scaffold_v1` / `round_20260621_run_round_scaffold_v1`.
- Therefore the previous round lacked current-round structured execution evidence.

Existing implementation evidence from the previous round may be inspected but not treated as accepted evidence until regenerated for this round:

- `reverse_agent/project_gate.py` may already contain partial report-auto-summary / closeout consistency changes.
- `tests/test_project_gate.py` may already contain six regression tests around report-auto-summary and closeout consistency.
- Those changes must be validated through current-round command-plan-authorized gates.

Artifact freshness:

- Any artifact whose `decision_id` or `round_id` refers to `decision_20260621_run_round_scaffold_v1` / `round_20260621_run_round_scaffold_v1` is stale for this round.
- Any artifact from `decision_20260622_report_auto_summary_closeout_consistency_v1` may be used only as previous-round context, not as current-round acceptance evidence.
- Missing sample artifacts in `artifact_index.json` remain historical/backlog evidence and are non-blocking for this engineering round unless code claims sample-solving progress.

Existing capabilities to reuse:

- `preflight`
- `command-plan`
- `execution-log`
- `report-auto-summary`
- `report-summary`
- `final-check`
- `run-round --dry-run`
- `run-closeout`
- policy-lint and policy-impact gates
- existing tests in `tests/test_project_gate.py`

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this is a gate/report/closeout evidence rework, command-plan should normally use `full`.
- Tests and closeout must remain subordinate to command-plan.
- Run only commands authorized by command-plan. If command-plan omits a command, do not run it.

Tool policy:

- This is not a reverse-solving round.
- Do not run IDA, Ghidra, debuggers, emulators, runtime probes, solvers, harnesses, samples, or full `solve_reports/` scans.
- Do not inspect full historical `project_state/rounds/`; read only exact paths needed to diagnose stale artifact propagation.

## 3. Do Not Do

Do not add a new feature beyond evidence closure and any minimal fix required for current-round gate consistency.

Do not build `execute-decision`, AgentRunner, job manager, database, queue, scheduler, web UI, API planner/auditor, or GitHub Actions workflow.

Do not turn `run-round` into a real executor in this round.

Do not suppress warnings by weakening final-check, report-summary, command-plan, or execution-log. Real mismatches must still fail or warn as designed.

Do not treat prior-round artifacts as current evidence.

Do not claim `SUCCESS` if `execution_log.json`, `final_gate_result.json`, `codex_report_auto_summary.json`, or `report_summary_synthesis.json` still references any older round.

Do not use unsupported report statuses. `codex_report_summary.status` must be one of `SUCCESS`, `PARTIAL`, `FAILED`, or `BLOCKED`.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `.codex-skills/registry.json`, or `docs/prompts/*`.

Do not continue `samplereverse` solving. Do not run samples or reverse tools.

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

Then inspect current gate/source/test files:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/preflight_result.json`
5. `project_state/gates/execution_log.json`
6. `project_state/gates/codex_report_auto_summary.json`
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/policy_lint_result.json`
10. `project_state/gates/policy_impact_audit.json`
11. `project_state/gates/run_round_result.json`
12. `project_state/gates/run_closeout_result.json`
13. `project_state/gates/round_baseline.json`
14. `project_state/gates/round_delta_summary.json`
15. `project_state/gates/round_close_snapshot.json`

Read prior-round artifacts only by exact path if needed to confirm what was stale:

1. `project_state/rounds/round_20260622_report_auto_summary_closeout_consistency_v1/codex_execution_report.md`
2. `project_state/rounds/round_20260622_report_auto_summary_closeout_consistency_v1/pytest_result.txt`
3. `project_state/rounds/round_20260622_report_auto_summary_closeout_consistency_v1/round_manifest.json`

Do not scan entire `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. Which artifacts were stale in the previous attempt, and what prior `decision_id` / `round_id` did they contain?
2. Which current-round artifacts were regenerated in this rework, and what `decision_id` / `round_id` / `report_id` do they contain?
3. Which command-plan commands were authorized, which were executed, and were any omitted or unauthorized commands executed?
4. Does `pytest_result.txt` cover every command claimed in `codex_report_summary.tests_ran` and every current-round command needed by command-plan?
5. Does `execution_log.json` match current `pytest_result.txt` and current `command_plan.json`?
6. Does `codex_report_auto_summary.json` match current live `codex_report_summary` and `report_summary_synthesis.json` after closeout/archive handling?
7. Does current `final_gate_result.json` show no blocking reasons, and what warnings remain if any?
8. Does the rework preserve the previous implementation behavior: report-auto-summary consistency fix, real mismatch detection, status-kind command exclusion from tests_ran, closeout artifact round matching, command-plan authority, run-round dry-run behavior, policy-lint, policy-impact, and prompt-doc immutability?

Each answer must include concrete evidence references to files/artifacts and a status of `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. Do not write placeholders such as TODO, TBD, PENDING, or N/A.

## 6. Implementation Scope

Primary scope: finish the current-round evidence pipeline. Prefer no further source changes if the existing implementation passes validation.

Allowed source changes only if a current-round gate or test proves a real defect:

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
- `project_state/rounds/round_20260622_closeout_consistency_evidence_rework_v1/*` only if command-plan authorizes closeout

Required behavior:

1. Establish a current-round baseline before modifications.
2. Run preflight and command-plan.
3. Follow command-plan exactly.
4. Execute all required full-profile commands unless command-plan omits them.
5. Regenerate execution log, report-auto-summary, report-summary synthesis, final-check, and closeout artifacts for this round.
6. Ensure every regenerated artifact has the current round IDs.
7. Ensure `codex_execution_report.md` top summary exactly matches current evidence.
8. Ensure `pytest_result.txt` is the source of truth for actually executed commands and test output.
9. Ensure stale prior-round gate artifacts are not accepted as current evidence.
10. If the implementation cannot reach `SUCCESS`, stop with `BLOCKED` or `FAILED` and identify the exact failing gate/check.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Run preflight before any implementation modification:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
```

Generate command-plan and obey it:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Then run only command-plan-authorized commands. If authorized, the expected full validation set includes:

```powershell
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260622_closeout_consistency_evidence_rework_v1
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all commands actually executed in `project_state/pytest_result.txt`, including startup checks, gate commands, pytest commands, stdout/stderr or relevant output, exit code, and conclusion.

After closeout, rerun any command-plan-authorized report-summary/final-check/report-auto-summary steps needed to ensure current artifacts match the final live report.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` without further modifications if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- any source change would require files outside the allowed source list;
- any artifact update would require forbidden paths;
- stale prior-round artifacts cannot be regenerated for the current round;
- `pytest_result.txt`, `execution_log.json`, or `final_gate_result.json` cannot be made current-round consistent;
- final-check reports blocking reasons;
- execution-log shows unauthorized commands or exit-code mismatches;
- report-auto-summary consistency remains unresolved for current-round artifacts;
- Required Audit remains incomplete.

Stop with `REWORK_REQUIRED` if tests fail, if generated artifacts still contain old round IDs, if the report stays `PARTIAL / NEEDS_REVIEW` without a precise blocker, or if the result only suppresses warnings instead of producing current-round evidence.
