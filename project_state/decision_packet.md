```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260622_close_round_archive_cycle_fix_v1",
  "round_id": "round_20260622_close_round_archive_cycle_fix_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260622_run_closeout_log_isolation_evidence_rework_v1",
  "previous_round_id": "round_20260622_run_closeout_log_isolation_evidence_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "primary_goal": "Fix the close-round/archive cycle so run-closeout can create the round manifest and then allow archive-dependent final-check checks to pass, without weakening command-plan authority or log isolation.",
  "command_plan_authority_required": true,
  "accepted_requires_close_round_exit_zero": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_round_manifest_created": true,
  "accepted_requires_archive_matches_live_report_and_pytest": true,
  "accepted_requires_execution_log_consistency_passed": true,
  "accepted_requires_report_auto_summary_consistency_passed": true,
  "accepted_requires_required_audit_coverage_passed": true,
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
    "project_state/rounds/round_20260622_close_round_archive_cycle_fix_v1/*"
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

Implement Close-Round Archive Cycle Fix v1.

The previous evidence rework substantially improved the top-level command-plan authority chain and preserved `run-closeout` nested log isolation, but audit still returned `REWORK_REQUIRED`. The remaining hard problem is a closeout/archive cycle:

- `run-closeout` calls `close-round`.
- `close-round` exits 1 because the round manifest is missing.
- The round manifest is normally created by successful close-round.
- Because close-round fails, archive-dependent final-check checks remain WARN: `round_manifest_present`, `archived_report_matches_live_report`, `archived_pytest_result_matches_live_pytest_result`, and `generated_artifacts_cover_round_archive`.
- Because archive-dependent checks remain unresolved, the report stays `PARTIAL / NEEDS_REVIEW` instead of `SUCCESS / ACCEPTED`.

This round must break that cycle safely. The fix must make close-round able to create the round archive/manifest when the current live report, pytest_result, command-plan authority, report-summary, and final-check are otherwise valid. It must not weaken command-plan authority, log isolation, stale artifact checks, or real failure detection.

Acceptance requires:

- `run-closeout` passes;
- `close-round` exits 0;
- `project_state/rounds/round_20260622_close_round_archive_cycle_fix_v1/round_manifest.json` exists;
- archived report and archived pytest_result match live report and live pytest_result at closeout time;
- `generated_artifacts` covers round archive files;
- `execution_log_consistency` passes;
- `report_auto_summary_consistency` passes;
- Required Audit coverage passes with no placeholder answers;
- final-check passes, not merely WARN;
- report status is `SUCCESS` and acceptance recommendation is `ACCEPTED`, except only if a real blocker is explicitly documented.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only sample-solving state and must not control this round. This `decision_packet.md` controls the current round.

Previous audit findings:

- `decision_20260622_run_closeout_log_isolation_evidence_rework_v1` was valid and approved, but not accepted.
- Top-level command-plan authority improved: `command_plan_execution_authority` passed.
- `pytest_result_exit_codes_match_command_plan` passed.
- `report_summary_fields_match_synthesis` passed.
- `stale_artifact_ids` passed.
- `report-summary` command passed.
- `final-check` was only WARN, not PASSED.
- `run-closeout` failed because close-round exited 1.
- The blocking loop was: round manifest missing -> close-round fails -> archive checks cannot pass -> final report remains PARTIAL.
- `execution_log_consistency` still warned because execution_log and pytest_result disagreed for `report-summary` and `final-check` exit codes.
- `report_auto_summary_consistency` still warned because live report and auto-summary `tests_ran` disagreed.
- `required_audit_coverage` still warned because one Required Audit answer was placeholder-like.
- historical/backlog sample artifact warnings remain non-blocking for this engineering round and must not be the sole reason for PARTIAL.

Existing capabilities to reuse:

- `run-round --execute` and `run-round --dry-run`.
- `run-closeout`, `close-round`, round archive, and round manifest logic.
- `run_closeout_execution_log.json` or equivalent scoped closeout internal evidence.
- `command-plan` and omitted-command authority checks.
- `execution-log` derived from top-level `pytest_result.txt` and command-plan.
- `report-auto-summary`.
- `report-summary` / `build_report_summary_synthesis()`.
- `final-check`.
- `policy-lint` and `policy-impact`.
- Existing closeout, log-isolation, and report-summary tests in `tests/test_project_gate.py`.

Artifact freshness:

- Any artifact from `round_20260622_run_round_execute_pipeline_v1`, `round_20260622_run_closeout_log_isolation_v1`, or `round_20260622_run_closeout_log_isolation_evidence_rework_v1` is previous-round context only.
- Current proof must be regenerated with `decision_20260622_close_round_archive_cycle_fix_v1` and `round_20260622_close_round_archive_cycle_fix_v1`.
- Historical/backlog sample artifacts are non-blocking unless this round claims sample-solving progress.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this touches closeout/archive/final-check behavior, command-plan should use or require `full` validation.
- Tests remain subordinate to command-plan.
- Closeout may run only if command-plan authorizes it and profile allows it.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect or run sample binaries.
- Do not use IDA, Ghidra, debuggers, emulators, runtime probes, solvers, harnesses, or full `solve_reports/` scans.

## 3. Do Not Do

Do not add new architecture or expand scope beyond fixing the close-round/archive cycle and evidence convergence.

Do not build AgentRunner, Codex adapter, Trae adapter, job manager, database, queue, scheduler, daemon, Web UI, API planner, API auditor, GitHub Actions workflow, or background worker.

Do not weaken command-plan authority. Real unauthorized top-level commands must still fail or warn.

Do not weaken log isolation. Nested `run-closeout` internals must remain outside the top-level `pytest_result.txt` command stream and remain auditable in scoped closeout evidence.

Do not convert close-round failure into success by ignoring missing archive artifacts. The fix must create valid archive/manifest artifacts, not suppress checks.

Do not mark archive checks non-blocking unless the decision explicitly makes archive optional. This decision requires closeout/archive success.

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

Prior-round artifacts may be read only by exact path if needed to diagnose the close-round cycle. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What exact close-round/archive cycle caused `run-closeout` to fail, and which checks depended on the missing round manifest?
2. What code path now creates or validates `round_manifest.json`, and why no circular dependency remains?
3. How does `run-closeout` now order report-summary, final-check, close-round, archive creation, and any post-closeout summary/final-check refresh?
4. How do archived report and archived pytest_result prove they match the live report and live pytest_result at closeout time?
5. How does final-check distinguish real archive mismatches from pre-closeout/archive-pending state, and why final state is PASSED?
6. How were `execution_log_consistency` and `report_auto_summary_consistency` resolved so execution_log, pytest_result, auto-summary, synthesis, and live report agree?
7. What regression tests prove close-round can create the manifest, archive checks pass after closeout, archive mismatches still fail, log isolation is preserved, and command-plan authority remains strict?
8. How does this round preserve `run-round --execute`, `run-round --dry-run`, scoped closeout logs, command-plan authority, omitted-command blocking, policy-lint, policy-impact, prompt-doc immutability, and non-blocking historical/backlog sample artifact handling?

Each answer must include concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. Do not write TODO, TBD, PENDING, should-converge placeholders, or speculative answers.

## 6. Implementation Scope

Primary scope: fix close-round/archive cycle and regenerate clean current-round evidence.

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
- `project_state/rounds/round_20260622_close_round_archive_cycle_fix_v1/*` only if command-plan authorizes closeout

Required behavior:

1. Establish a current-round baseline before modifications.
2. Identify why `close-round` exits 1 when the manifest is missing.
3. Modify the smallest necessary close-round/run-closeout logic so close-round can create the round archive and manifest instead of requiring the manifest before creation.
4. Preserve strict validation after archive creation: if archive files are missing, stale, or do not match live report/pytest_result, final-check must still fail or warn according to policy.
5. Keep nested closeout internals in scoped closeout evidence, not in top-level `pytest_result.txt`.
6. Regenerate clean current-round `pytest_result.txt` with all command-plan-authorized top-level commands.
7. Regenerate current-round `execution_log.json` and make it pass without exit-code mismatch or stale-command warnings.
8. Regenerate current-round `codex_report_auto_summary.json`, `report_summary_synthesis.json`, and `final_gate_result.json` after closeout/archive creation.
9. Ensure `round_manifest.json`, archived report, archived pytest_result, and archived decision packet exist under `project_state/rounds/round_20260622_close_round_archive_cycle_fix_v1/`.
10. Ensure `report-summary` and `final-check` pass after closeout.
11. Ensure `codex_report_summary.status` is `SUCCESS` and `acceptance_recommendation` is `ACCEPTED` unless a real blocker remains.
12. Add focused regression tests for close-round archive cycle behavior and preserve previous log-isolation tests.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_close_round_archive_cycle_fix_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_close_round_archive_cycle_fix_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260622_close_round_archive_cycle_fix_v1
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
- the fix would require weakening command-plan authority or archive validation;
- closeout internals cannot remain auditable after log isolation;
- implementation requires files outside allowed source scope;
- state updates require forbidden paths;
- close-round still exits nonzero after the fix;
- round manifest cannot be created;
- archive report or archive pytest_result cannot be made to match live artifacts;
- final-check reports blocking reasons after closeout refresh;
- execution-log or report-auto-summary remains inconsistent with live report;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, `run-closeout` remains FAILED, `close-round` exit remains 1, `round_manifest_present` remains WARN/FAIL, archived report/pytest mismatch remains WARN/FAIL, `execution_log_consistency` remains WARN/FAIL, `report_auto_summary_consistency` remains WARN/FAIL, or the report remains `PARTIAL / NEEDS_REVIEW` for reasons other than explicitly non-blocking historical/backlog sample artifacts.
