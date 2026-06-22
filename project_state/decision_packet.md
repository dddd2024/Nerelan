```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260622_post_closeout_evidence_refresh_v1",
  "round_id": "round_20260622_post_closeout_evidence_refresh_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260622_close_round_archive_cycle_fix_v1",
  "previous_round_id": "round_20260622_close_round_archive_cycle_fix_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "primary_goal": "Refresh post-closeout evidence so live report, pytest_result, execution_log, report-auto-summary, report-summary, final-check, and archived round artifacts converge to SUCCESS/ACCEPTED without changing close-round core logic unless strictly necessary.",
  "command_plan_authority_required": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_close_round_exit_zero": true,
  "accepted_requires_round_manifest_present": true,
  "accepted_requires_archive_matches_live_report_and_pytest": true,
  "accepted_requires_execution_log_consistency_passed": true,
  "accepted_requires_report_auto_summary_consistency_passed": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_required_audit_coverage_passed": true,
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
    "project_state/rounds/round_20260622_post_closeout_evidence_refresh_v1/*"
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

Implement Post-Closeout Evidence Refresh v1.

The previous round fixed the main close-round/archive cycle: `run-closeout` passed, `close-round` exited 0, and the round archive/manifest could be created. However, audit still returned `REWORK_REQUIRED` because the post-closeout evidence did not converge. The live report remained `PARTIAL / NEEDS_REVIEW`, `pytest_result_summary.status` was `FAILED`, `execution-log` was `FAILED`, `report-summary` was `FAILED`, `final-check` was `FAILED`, and `final_gate_result.json` still contained blocking evidence-mismatch reasons.

This round must not redesign close-round. It must perform the narrow post-closeout evidence refresh and, if necessary, apply the smallest code fix that lets live and archived state converge after closeout.

The target final state is:

- `run-closeout` is `PASSED`;
- `close-round` exits 0;
- the round manifest exists under `project_state/rounds/round_20260622_post_closeout_evidence_refresh_v1/round_manifest.json`;
- archived report and archived pytest_result match live report and live pytest_result at the final accepted state;
- top-level `pytest_result.txt` contains only current-round command-plan-authorized command blocks;
- `execution_log.json` is current-round and `PASSED` with no stale prior-round commands;
- `codex_report_auto_summary.json`, `report_summary_synthesis.json`, live `codex_report_summary`, and `final_gate_result.json` agree;
- Required Audit coverage passes with no missing or placeholder answers;
- final-check is `PASSED`, not merely WARN or FAILED;
- `codex_report_summary.status` is `SUCCESS` and `acceptance_recommendation` is `ACCEPTED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only sample-solving state and must not control this round. This `decision_packet.md` controls the current round.

Previous audit findings from `decision_20260622_close_round_archive_cycle_fix_v1`:

- The decision was valid and approved.
- `run-closeout` became `PASSED`.
- `close-round` became `PASSED` with exit 0.
- `round_manifest_present`, `archived_report_matches_live_report`, `archived_pytest_result_matches_live_pytest_result`, and `generated_artifacts_cover_round_archive` improved to PASS in the post-closeout gate artifact.
- But live `codex_execution_report.md` still reported `PARTIAL / NEEDS_REVIEW`.
- `pytest_result_summary.status` was `FAILED`.
- The command log still showed `execution-log: FAILED`, `report-summary: FAILED`, and `final-check: FAILED` before the later closeout state.
- `final_gate_result.json` remained `FAILED` with a blocking reason: `final_check_stdout_matches_gate_status` mismatch.
- `execution_log_consistency` still warned because `execution_log.json` disagreed with `pytest_result` or command-plan and still contained stale prior-round `round_20260622_run_closeout_log_isolation_evidence_rework_v1` commands.
- `report_auto_summary_consistency` still warned because `codex_report_auto_summary.json` and the live report disagreed on `tests_ran`.
- `required_audit_coverage` still warned because the Required Audit section was missing all 8 answers in final-check's view.
- historical/backlog sample artifact warnings remain non-blocking and must not be the only reason for `PARTIAL`.

Existing capabilities to reuse:

- `run-round --execute` and `run-round --dry-run`.
- `run-closeout`, `close-round`, round archive, and manifest creation.
- scoped closeout internal evidence in `run_closeout_execution_log.json` or equivalent.
- `command-plan` and omitted-command authority checks.
- `execution-log` derived from top-level `pytest_result.txt` and command-plan.
- `report-auto-summary`.
- `report-summary` / `build_report_summary_synthesis()`.
- `final-check`.
- `policy-lint` and `policy-impact`.
- Existing closeout, log-isolation, archive, and report-summary tests in `tests/test_project_gate.py`.

Artifact freshness:

- Any artifact from `round_20260622_run_round_execute_pipeline_v1`, `round_20260622_run_closeout_log_isolation_v1`, `round_20260622_run_closeout_log_isolation_evidence_rework_v1`, or `round_20260622_close_round_archive_cycle_fix_v1` is previous-round context only.
- Current proof must be regenerated with `decision_20260622_post_closeout_evidence_refresh_v1` and `round_20260622_post_closeout_evidence_refresh_v1`.
- Historical/backlog sample artifacts are non-blocking unless this round claims sample-solving progress.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this touches evidence refresh, report-summary, final-check, and closeout/archive state, command-plan should use or require `full` validation.
- Tests remain subordinate to command-plan.
- Closeout may run only if command-plan authorizes it and profile allows it.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect or run sample binaries.
- Do not use IDA, Ghidra, debuggers, emulators, runtime probes, solvers, harnesses, or full `solve_reports/` scans.

## 3. Do Not Do

Do not add new architecture or expand scope beyond post-closeout evidence refresh and status convergence.

Do not build AgentRunner, Codex adapter, Trae adapter, job manager, database, queue, scheduler, daemon, Web UI, API planner, API auditor, GitHub Actions workflow, or background worker.

Do not redesign close-round or run-closeout if a narrower post-closeout refresh order/state fix is sufficient.

Do not weaken command-plan authority. Real unauthorized top-level commands must still fail or warn.

Do not weaken log isolation. Nested `run-closeout` internals must remain outside the top-level `pytest_result.txt` command stream and remain auditable in scoped closeout evidence.

Do not convert failures into success by ignoring mismatches. The fix must make report, pytest_result, execution_log, auto-summary, synthesis, final-check, and archive actually agree.

Do not mark archive checks optional. This decision requires closeout/archive success.

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

Prior-round artifacts may be read only by exact path if needed to diagnose stale evidence leakage. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What exact post-closeout evidence mismatch remained after `close-round` started succeeding, and which files showed it?
2. How was top-level `pytest_result.txt` rebuilt or refreshed so it contains only current-round command-plan-authorized command blocks and no stale prior-round commands?
3. How was `execution_log.json` regenerated so it agrees with `pytest_result.txt` and `command_plan.json` without stale prior-round commands or exit-code mismatches?
4. How were `codex_report_auto_summary.json`, `report_summary_synthesis.json`, and live `codex_report_summary` regenerated so `tests_ran`, `files_changed`, `generated_artifacts`, status, and acceptance recommendation agree?
5. How does final-check now prove `round_manifest_present`, archived report/pytest matching, generated archive coverage, command-plan authority, stale artifact IDs, Required Audit coverage, execution-log consistency, and report-auto-summary consistency all pass?
6. How does `run-closeout` now order close-round, archive creation, live artifact refresh, report-summary, report-auto-summary, and final-check so the accepted live state and archived state do not drift?
7. What regression tests prove post-closeout evidence refresh, archive/live agreement, stale command exclusion, real mismatch detection, log isolation, and command-plan authority remain correct?
8. How does this round preserve `run-round --execute`, `run-round --dry-run`, scoped closeout logs, command-plan authority, omitted-command blocking, policy-lint, policy-impact, prompt-doc immutability, and non-blocking historical/backlog sample artifact handling?

Each answer must include concrete evidence and status `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. Do not write TODO, TBD, PENDING, should-converge placeholders, or speculative answers.

## 6. Implementation Scope

Primary scope: refresh and converge post-closeout evidence. Apply minimal source changes only if required to make the refresh order/state reproducible.

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
- `project_state/rounds/round_20260622_post_closeout_evidence_refresh_v1/*` only if command-plan authorizes closeout

Required behavior:

1. Establish a current-round baseline before modifications.
2. Ensure command-plan is current for `round_20260622_post_closeout_evidence_refresh_v1`.
3. Regenerate clean current-round `pytest_result.txt` with all command-plan-authorized top-level commands.
4. Ensure `pytest_result_summary.status` reflects the final evidence state and is not left `FAILED` when the command body contains no real failure markers.
5. Ensure top-level `pytest_result.txt` contains no prior-round command blocks from the four previous engineering rounds.
6. Regenerate current-round `execution_log.json` after the final top-level command stream is stable.
7. Regenerate current-round `codex_report_auto_summary.json` and `report_summary_synthesis.json` after `execution_log.json` and `final_gate_result.json` are stable.
8. Regenerate live `codex_execution_report.md` so summary fields exactly match synthesis and auto-summary.
9. Run closeout if command-plan authorizes it, and ensure archive files are created for this round.
10. After closeout, run the necessary report-summary / report-auto-summary / final-check refresh sequence so live and archived evidence agree, or apply the minimal code fix that makes this sequence reproducible.
11. Ensure final-check passes with no blocking reasons.
12. Ensure Required Audit contains all 8 concrete answers and no placeholder answers.
13. Ensure report status is `SUCCESS` and acceptance recommendation is `ACCEPTED` unless a real blocker remains.
14. Add focused regression tests only if needed to lock the refresh order/state convergence.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_post_closeout_evidence_refresh_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260622_post_closeout_evidence_refresh_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260622_post_closeout_evidence_refresh_v1
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
- the fix would require weakening command-plan authority, log isolation, or archive validation;
- closeout internals cannot remain auditable after log isolation;
- implementation requires files outside allowed source scope;
- state updates require forbidden paths;
- round manifest cannot be created;
- archive report or archive pytest_result cannot be made to match live artifacts;
- execution-log cannot be made consistent with pytest_result and command-plan;
- report-auto-summary cannot be made consistent with live report;
- final-check reports blocking reasons after refresh;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, `run-closeout` remains failed, `close-round` regresses, `round_manifest_present` regresses, archived report/pytest mismatch remains, `execution_log_consistency` remains WARN/FAIL, `report_auto_summary_consistency` remains WARN/FAIL, Required Audit coverage remains WARN/FAIL, or the report remains `PARTIAL / NEEDS_REVIEW` for reasons other than explicitly non-blocking historical/backlog sample artifacts.
