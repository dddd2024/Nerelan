```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260622_self_referential_status_convergence_v1",
  "round_id": "round_20260622_self_referential_status_convergence_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260622_post_closeout_evidence_refresh_v1",
  "previous_round_id": "round_20260622_post_closeout_evidence_refresh_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "primary_goal": "Break the self-referential report-auto-summary/final-check status-source cycle so a round with passed closeout, no blocking evidence mismatches, and only historical/backlog warnings can converge to SUCCESS/ACCEPTED without weakening real mismatch detection.",
  "command_plan_authority_required": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_close_round_exit_zero": true,
  "accepted_requires_final_check_no_blocking_reasons": true,
  "accepted_requires_only_non_blocking_warnings": true,
  "accepted_requires_report_auto_summary_consistency_passed_or_explicitly_non_blocking_self_reference": true,
  "accepted_requires_status_policy_historical_backlog_non_blocking": true,
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
    "project_state/rounds/round_20260622_self_referential_status_convergence_v1/*"
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

Implement Self-Referential Status Convergence v1.

The previous round moved the system close to closure: `close_round()` succeeded, the archive was created, all 775 focused project-gate tests passed, and final-check reportedly converged to `WARN` with only two non-blocking warnings. The remaining blocker is a self-referential status-source cycle:

- `report-auto-summary` derives status from `final_gate_result.json`;
- `final_gate_result.json` includes a `report_auto_summary_consistency` check;
- for non-`SUCCESS` reports, that check can remain WARN because auto-summary and live report disagree only on the report status source itself;
- the WARN prevents status convergence to `SUCCESS`, which then preserves the non-`SUCCESS` condition that caused the WARN;
- `status_policy_valid` also warns about 50 missing historical/backlog sample artifacts, which is explicitly external and non-blocking for this engineering round.

This round must break only that self-referential status-source cycle. It must not weaken command-plan authority, execution-log consistency, archive validation, stale artifact detection, Required Audit coverage, or real report-auto-summary mismatch detection.

The accepted final state is:

- `run-closeout` is `PASSED`;
- `close-round` exits 0;
- the current round archive and `round_manifest.json` exist;
- archived report and archived pytest_result match live report and live pytest_result at the accepted final state;
- command-plan authority passes;
- execution-log consistency passes, or any diagnostic skip is explicitly modeled as non-executable and not a missing required evidence command;
- final-check has no blocking reasons;
- the only remaining warnings, if any, are explicitly classified as non-blocking historical/backlog artifact notices or non-blocking self-referential status-source notices;
- report-auto-summary consistency is `PASS`, or a distinct `NON_BLOCKING`/`WARN` classification is used only for the self-referential status-source edge and does not block `SUCCESS`;
- `codex_report_summary.status` is `SUCCESS` and `acceptance_recommendation` is `ACCEPTED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only sample-solving state and must not control this round. This `decision_packet.md` controls the current round.

User-provided current execution evidence from the previous attempt:

- `close_round()` succeeded and archive was created.
- `final-check` converged to `WARN` with exit 0 and only two non-blocking warnings.
- 775 focused tests passed with no regressions.
- `report_auto_summary_consistency` remained WARN because auto-summary derived status from `final_gate_result.json`, which itself carried a retriable status-source failure. This creates a circular dependency for non-`SUCCESS` reports rather than a real evidence mismatch.
- `status_policy_valid` WARN came from 50 missing historical sample artifacts, which are external/historical/backlog and non-blocking for an engineering round.

Prior GitHub audit evidence from `decision_20260622_post_closeout_evidence_refresh_v1`:

- The decision was valid and approved.
- `pytest_result_summary.status` had already improved to `PASSED` in the fetched state.
- `run-closeout` was recorded as `PASSED`.
- archive checks such as `round_manifest_present`, `archived_report_matches_live_report`, `archived_pytest_result_matches_live_pytest_result`, and `generated_artifacts_cover_round_archive` had improved to PASS.
- Required Audit coverage had improved to PASS in final-check.
- Remaining blockers centered on `report_status: PARTIAL`, `report_auto_summary_consistency: WARN`, and status-policy treatment of historical/backlog artifacts.

Existing capabilities to reuse:

- `run-round --execute` and `run-round --dry-run`.
- `run-closeout`, `close-round`, round archive, and manifest creation.
- scoped closeout internal evidence in `run_closeout_execution_log.json` or equivalent.
- `command-plan` and omitted-command authority checks.
- `execution-log` derived from top-level `pytest_result.txt` and command-plan.
- `report-auto-summary`.
- `report-summary` / `build_report_summary_synthesis()`.
- `final-check`.
- `status_policy_valid` / artifact freshness policy.
- `policy-lint` and `policy-impact`.
- Existing closeout, archive, log-isolation, report-summary, and status-policy tests in `tests/test_project_gate.py`.

Artifact freshness:

- Any artifact from `round_20260622_run_round_execute_pipeline_v1`, `round_20260622_run_closeout_log_isolation_v1`, `round_20260622_run_closeout_log_isolation_evidence_rework_v1`, `round_20260622_close_round_archive_cycle_fix_v1`, or `round_20260622_post_closeout_evidence_refresh_v1` is previous-round context only.
- Current proof must be regenerated with `decision_20260622_self_referential_status_convergence_v1` and `round_20260622_self_referential_status_convergence_v1`.
- Historical/backlog sample artifacts are non-blocking unless this round claims sample-solving progress.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this changes status derivation and final-check/report-summary policy, command-plan should use or require `full` validation.
- Tests remain subordinate to command-plan.
- Closeout may run only if command-plan authorizes it and profile allows it.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect or run sample binaries.
- Do not use IDA, Ghidra, debuggers, emulators, runtime probes, solvers, harnesses, or full `solve_reports/` scans.

## 3. Do Not Do

Do not add new architecture or expand scope beyond self-referential status convergence.

Do not build AgentRunner, Codex adapter, Trae adapter, job manager, database, queue, scheduler, daemon, Web UI, API planner, API auditor, GitHub Actions workflow, or background worker.

Do not redesign close-round or run-closeout unless a minimal ordering fix is strictly required to reproduce status convergence.

Do not weaken command-plan authority. Real unauthorized top-level commands must still fail or warn.

Do not weaken log isolation. Nested `run-closeout` internals must remain outside the top-level `pytest_result.txt` command stream and remain auditable in scoped closeout evidence.

Do not suppress real report-auto-summary mismatches. Only the status-source self-reference edge may be separated or classified as non-blocking, and only when all substantive fields match.

Do not mark archive checks optional. Archive checks must remain strict.

Do not treat all WARN statuses as acceptable. Only explicitly classified non-blocking warnings may permit `SUCCESS`.

Do not execute commands from `command-plan.omitted_commands`.

Do not treat prior-round artifacts or command blocks as current evidence.

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

Prior-round artifacts may be read only by exact path if needed to diagnose status-source self-reference. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What exact self-referential dependency kept `report_auto_summary_consistency` in WARN, and which fields were substantive mismatches versus status-source-only mismatches?
2. What status derivation rule changed so final report status can become `SUCCESS` when only non-blocking historical/backlog and status-source self-reference warnings remain?
3. How does the new rule still fail real report-auto-summary mismatches in `tests_ran`, `files_changed`, `generated_artifacts`, IDs, exit codes, stale artifacts, archive artifacts, or Required Audit coverage?
4. How does `status_policy_valid` distinguish historical/backlog sample artifact warnings from current-round evidence failures?
5. How do final-check, report-auto-summary, report-summary synthesis, live `codex_report_summary`, and closeout archive agree after the fix?
6. How does command-plan authority remain strict, including omitted-command handling and non-executable/self-invocation command modeling?
7. What regression tests prove self-referential status convergence, real mismatch detection, non-blocking historical/backlog handling, archive strictness, log isolation, and command-plan authority?
8. How does this round preserve `run-round --execute`, `run-round --dry-run`, scoped closeout logs, policy-lint, policy-impact, prompt-doc immutability, and no sample-solving behavior?

Each answer must include concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. Do not write TODO, TBD, PENDING, should-converge placeholders, or speculative answers.

## 6. Implementation Scope

Primary scope: fix self-referential status-source convergence. Apply minimal source changes only if required.

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
- `project_state/rounds/round_20260622_self_referential_status_convergence_v1/*` only if command-plan authorizes closeout

Required behavior:

1. Establish a current-round baseline before modifications.
2. Identify the exact status-source path where `report-auto-summary` reads `final_gate_result.json`, and where final-check compares auto-summary against live report.
3. Separate substantive auto-summary mismatches from self-referential status-source mismatches.
4. Permit `SUCCESS / ACCEPTED` only when all substantive checks pass and the only remaining warnings are explicitly classified non-blocking warnings.
5. Keep historical/backlog sample artifact warnings non-blocking for engineering rounds.
6. Ensure a real mismatch in `tests_ran`, `files_changed`, `generated_artifacts`, IDs, exit codes, stale artifacts, archive artifacts, or Required Audit still causes WARN/FAIL according to existing policy.
7. Ensure final-check can produce `PASSED` when only non-blocking warnings remain and report status is otherwise converged.
8. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, and live `codex_execution_report.md`.
9. Run closeout if command-plan authorizes it and ensure archive files are current.
10. Ensure final report status is `SUCCESS` and `acceptance_recommendation` is `ACCEPTED`.
11. Add focused regression tests for the self-referential status-source case and real mismatch negative cases.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_self_referential_status_convergence_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_self_referential_status_convergence_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260622_self_referential_status_convergence_v1
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
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
- the fix would require weakening command-plan authority, log isolation, archive validation, or real mismatch detection;
- closeout internals cannot remain auditable after log isolation;
- implementation requires files outside allowed source scope;
- state updates require forbidden paths;
- round manifest cannot be created;
- archive report or archive pytest_result cannot be made to match live artifacts;
- execution-log cannot be made consistent with pytest_result and command-plan;
- real report-auto-summary mismatches remain;
- final-check reports blocking reasons after refresh;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, `run-closeout` remains failed, close-round regresses, round manifest or archive checks regress, real `report_auto_summary_consistency` mismatches remain, status-source self-reference remains unclassified, historical/backlog warnings still force PARTIAL, or the report remains `PARTIAL / NEEDS_REVIEW` for reasons other than a clearly documented real blocker.
