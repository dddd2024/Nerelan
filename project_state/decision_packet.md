```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260623_report_summary_and_closeout_log_coverage_rework_v1",
  "round_id": "round_20260623_report_summary_and_closeout_log_coverage_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260623_manifest_status_and_artifact_coverage_hardening_v1",
  "previous_round_id": "round_20260623_manifest_status_and_artifact_coverage_hardening_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "primary_goal": "Fix report-summary convergence and closeout execution log coverage/freshness so a SUCCESS/ACCEPTED report cannot coexist with a FAILED synthesized summary, stale closeout execution log evidence, or missing generated_artifacts coverage for current-round closeout log artifacts.",
  "command_plan_authority_required": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_report_summary_fields_match": true,
  "accepted_requires_report_auto_summary_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_closeout_execution_log_current_or_exempt": true,
  "accepted_requires_generated_artifacts_closeout_log_coverage": true,
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
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/rounds/round_20260623_report_summary_and_closeout_log_coverage_rework_v1/*"
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

Implement Report Summary and Closeout Log Coverage Rework v1.

The previous round partially succeeded: it added current-round manifest status matching and the current round manifest reached `SUCCESS / ACCEPTED`. However, the audit outcome is `REWORK_REQUIRED` because two blocking issues remain in the acceptance chain:

1. `project_state/gates/report_summary_synthesis.json` still had `synthesis_status: FAILED` and synthesized `status: FAILED` / `acceptance_recommendation: REWORK_REQUIRED`, while live `project_state/codex_execution_report.md` claimed `status: SUCCESS` / `acceptance_recommendation: ACCEPTED`. `final-check` allowed this as a WARN, but for a final SUCCESS report this status-source split must not be accepted.
2. `project_state/gates/run_closeout_execution_log.json` appeared in dirty-state and files_changed evidence, but it was not included in `generated_artifacts`, and its content still referenced an older round (`round_20260622_post_closeout_evidence_refresh_v1`). This leaves closeout execution-log freshness and generated_artifacts coverage unresolved.

This round must close both gaps. A report may be accepted as `SUCCESS / ACCEPTED` only when:

- `report_summary_synthesis.json` is `PASSED` and its synthesized status/recommendation matches the live report summary;
- `codex_report_auto_summary.json` is `PASSED` and agrees with the live report summary;
- `final-check` has no blocking reasons and no report-summary status/recommendation mismatch for a SUCCESS report;
- `run_closeout_execution_log.json`, if present as current dirty/files_changed/gate evidence, is current-round evidence and is covered by `generated_artifacts`, or is explicitly classified as stale/non-current/exempt with auditable reasoning and tests;
- `run-closeout` is `PASSED` and closeout-internal evidence remains scoped outside the top-level pytest command stream.

This is an engineering rework round only. Do not add new features or resume reverse solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state. It suggests `collect_missing_evidence`, but it is not authoritative. This `decision_packet.md` controls the current round.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260623_manifest_status_and_artifact_coverage_hardening_v1`.

Previous round accepted facts:

- `decision_meta` was valid and approved.
- `codex_execution_report.md` claimed `SUCCESS / ACCEPTED` for `round_20260623_manifest_status_and_artifact_coverage_hardening_v1`.
- `pytest_result.txt` recorded `PASSED`, with 794 `tests/test_project_gate.py` tests and 1092 combined `tests/test_project_gate.py tests/test_project_state.py` tests passing.
- `round_manifest.json` for `round_20260623_manifest_status_and_artifact_coverage_hardening_v1` correctly recorded `report_status: SUCCESS` and `acceptance_recommendation: ACCEPTED`.
- `final-check` included and passed `round_manifest_status_matches_report`.
- command-plan used `full` profile, `closeout_allowed: true`, and `omitted_commands: []`.
- policy-lint and policy-impact passed.

Blocking facts from audit:

- `report_summary_synthesis.json` had `synthesis_status: FAILED`.
- The synthesized summary expected `status: FAILED` and `acceptance_recommendation: REWORK_REQUIRED`, while live `codex_report_summary` was `SUCCESS / ACCEPTED`.
- `final-check` recorded `report_summary_fields_match_synthesis` as `WARN`, not PASS, with status and acceptance_recommendation mismatches.
- `final-check` still summarized as `PASSED` despite that mismatch.
- `run_closeout_execution_log.json` appeared in `files_changed`, `round_delta_summary.final_dirty_files`, and `round_delta_summary.new_dirty_files_since_baseline`.
- `run_closeout_execution_log.json` was not present in `generated_artifacts` and was not present in `generated_artifacts_cover_gate_artifacts.existing_gate_artifacts`.
- The live `run_closeout_execution_log.json` content still referenced the older `round_20260622_post_closeout_evidence_refresh_v1`, not the current `round_20260623_manifest_status_and_artifact_coverage_hardening_v1`.

Artifact freshness:

- All proof for this rework must be regenerated under `decision_20260623_report_summary_and_closeout_log_coverage_rework_v1` and `round_20260623_report_summary_and_closeout_log_coverage_rework_v1`.
- Prior-round artifacts from `round_20260623_manifest_status_and_artifact_coverage_hardening_v1` are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external state notices for this engineering round and must not be claimed as current evidence.

Existing capabilities to reuse:

- `preflight`, decision metadata validation, and task_packet non-authority checks.
- `command-plan`, including full profile and omitted-command authority.
- `execution-log` derived from top-level `pytest_result.txt` and `command_plan.json`.
- `report-auto-summary` and `report-summary` synthesis.
- `final-check`, including report/pytest/command-plan/execution-log/archive/manifest consistency.
- `run-closeout`, `close-round`, round archive, round manifest creation, and close snapshot handling.
- `policy-lint` and `policy-impact`.
- Existing tests in `tests/test_project_gate.py` for command-plan, closeout, archive, generated_artifacts, report-summary, report-auto-summary, manifest status consistency, and status policy.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this rework touches report-summary/final-check/closeout evidence behavior, command-plan should use or require `full` validation.
- Tests remain subordinate to command-plan. If the Tests section conflicts with command-plan, command-plan is authoritative.
- Closeout may run only if command-plan authorizes it and the selected profile allows closeout.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect or run sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not broaden this round into Web UI, AgentRunner, Codex adapter, Trae adapter, job manager, database, queue, scheduler, daemon, API planner, API auditor, GitHub Actions workflow, or background worker work.

Do not continue `samplereverse` solving or any sample-solving task.

Do not read the full `solve_reports/` directory or full `PROJECT_PROGRESS_LOG.txt`.

Do not treat old sample artifacts as current evidence.

Do not weaken command-plan authority. Real unauthorized top-level commands must still fail final-check or execution-log checks.

Do not weaken execution-log consistency. Top-level commands must remain auditable through `pytest_result.txt` and `execution_log.json`.

Do not weaken report-summary or report-auto-summary consistency. For a `SUCCESS / ACCEPTED` report, real status/recommendation mismatches must not be accepted as a generic WARN.

Do not weaken archive strictness. Archived report and archived pytest_result must still match live artifacts according to the existing strict comparison rule.

Do not simply remove `run_closeout_execution_log.json` from the file system or from checks to hide the problem. If it is current evidence, it must be fresh and covered. If it is stale, it must be explicitly excluded from current evidence with a tested rule.

Do not mark all closeout execution-log mismatches as non-blocking. A stale current-round closeout log or missing generated_artifacts coverage for a current dirty closeout log must block acceptance.

Do not manually edit only state JSON to mask the symptom. The required output is code plus regression tests that prevent recurrence.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Do not introduce a `medium` profile.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message given to the executor.

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

Then inspect only relevant implementation and gate evidence files:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/codex_report_auto_summary.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/run_closeout_execution_log.json`
10. `project_state/gates/round_close_snapshot.json` if present
11. `project_state/gates/round_delta_summary.json`
12. `project_state/gates/policy_lint_result.json`
13. `project_state/gates/policy_impact_audit.json`
14. `project_state/rounds/round_20260623_manifest_status_and_artifact_coverage_hardening_v1/round_manifest.json` only as bounded prior-round diagnostic evidence
15. `project_state/rounds/round_20260623_manifest_status_and_artifact_coverage_hardening_v1/codex_execution_report.md` only as bounded prior-round diagnostic evidence

Do not scan the full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Why did the previous round's `report_summary_synthesis.json` synthesize `FAILED / REWORK_REQUIRED` while the live report claimed `SUCCESS / ACCEPTED`?
2. What rule now prevents a `SUCCESS / ACCEPTED` live report from passing final-check when `report_summary_synthesis.json` is FAILED or when status/recommendation fields differ?
3. How do `report-summary`, `report-auto-summary`, live `codex_report_summary`, and final-check now converge to the same status and acceptance recommendation?
4. Why was the previous `run_closeout_execution_log.json` stale, and what identifies the current-round closeout execution log as current evidence now?
5. How does generated_artifacts coverage now handle `run_closeout_execution_log.json` when it appears in dirty/files_changed/round_delta evidence?
6. How does the fix distinguish stale previous-round closeout execution logs from current-round closeout execution logs without hiding current evidence?
7. Which regression tests prove report-summary mismatch blocking, report-summary convergence, closeout execution-log freshness, generated_artifacts coverage for closeout logs, stale-log exclusion, and command-plan authority preservation?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no forbidden path mutation, no heavy artifact scan, and no weakening of archive or execution-log strictness?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, or speculative answers.

## 6. Implementation Scope

Primary scope: rework project-gate report-summary/final-check/closeout-log coverage behavior.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

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
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260623_report_summary_and_closeout_log_coverage_rework_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Make `report_summary_synthesis.json` converge to `PASSED` for the final accepted state.
3. For `SUCCESS / ACCEPTED` reports, make status/recommendation mismatches between report-summary synthesis and live `codex_report_summary` blocking unless they are a narrowly proven status-source-only transient that is regenerated away before acceptance.
4. Ensure final accepted `final_gate_result.json` has `report_summary_fields_match_synthesis: PASS`, not WARN, for status/recommendation fields.
5. Ensure `codex_report_auto_summary.json`, `report_summary_synthesis.json`, live `codex_execution_report.md`, and `final_gate_result.json` agree on report status and acceptance recommendation at closeout.
6. Ensure `run_closeout_execution_log.json`, if present as current dirty/files_changed/gate evidence, contains current `decision_id`/`round_id` or current closeout commands, and is covered by `generated_artifacts`.
7. If a stale previous-round `run_closeout_execution_log.json` exists, classify it as stale/non-current and exclude it from current reportable gate artifacts only when it is not part of current dirty/files_changed evidence. This rule must be tested.
8. Ensure `generated_artifacts_cover_gate_artifacts` or a new explicit final-check item fails when `run_closeout_execution_log.json` appears in current dirty/files_changed evidence but is absent from `generated_artifacts`.
9. Preserve the nested closeout log isolation rule: closeout-internal command blocks must not be injected into top-level `pytest_result.txt`, but must remain auditable in scoped closeout evidence.
10. Keep historical/backlog sample artifacts non-blocking for engineering rounds when not claimed as current evidence.
11. Add focused regression tests for all blocking conditions above.
12. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, and `codex_execution_report.md`.
13. Run closeout if and only if command-plan authorizes it.
14. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, report-summary `PASSED`, report-auto-summary `PASSED`, run-closeout `PASSED`, and no blocking reasons.

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

Generate and obey command-plan:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

After implementation, run only command-plan-authorized commands. If authorized, expected validation includes:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260623_report_summary_and_closeout_log_coverage_rework_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260623_report_summary_and_closeout_log_coverage_rework_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260623_report_summary_and_closeout_log_coverage_rework_v1
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands in `project_state/pytest_result.txt`. Do not include nested closeout-internal command blocks in the top-level command stream. Record nested closeout command evidence in `project_state/gates/run_closeout_execution_log.json` or the existing scoped closeout evidence artifact.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- the fix requires modifying files outside allowed source scope;
- state updates require forbidden paths;
- implementation requires weakening command-plan authority, execution-log consistency, archive strictness, report-summary consistency, report-auto-summary consistency, or Required Audit coverage;
- final-check cannot make report-summary mismatch blocking for final SUCCESS reports;
- `run_closeout_execution_log.json` cannot be made current-round evidence or explicitly stale/non-current with tests;
- generated_artifacts coverage cannot be made strict for closeout execution logs;
- run-closeout cannot keep nested command evidence scoped outside the top-level command stream;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, execution-log consistency regresses, policy-lint fails, policy-impact fails, run-closeout fails, final-check has blocking reasons, `report_summary_synthesis.json` remains FAILED, `report_summary_fields_match_synthesis` remains WARN/FAIL for status or acceptance_recommendation, `codex_report_auto_summary.json` disagrees with the live report, `run_closeout_execution_log.json` remains stale while treated as current evidence, `run_closeout_execution_log.json` appears in dirty/files_changed but not generated_artifacts, or the final report remains `PARTIAL / NEEDS_REVIEW` for reasons other than a clearly documented real blocker.
