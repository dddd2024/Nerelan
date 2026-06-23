```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260623_manifest_status_and_artifact_coverage_hardening_v1",
  "round_id": "round_20260623_manifest_status_and_artifact_coverage_hardening_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260622_self_referential_status_convergence_v1",
  "previous_round_id": "round_20260622_self_referential_status_convergence_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "primary_goal": "Harden closeout/round-manifest status consistency and generated_artifacts coverage so future SUCCESS/ACCEPTED reports cannot leave stale PARTIAL/NEEDS_REVIEW manifest metadata or omit current round gate artifacts from generated_artifacts without an explicit audited exemption.",
  "command_plan_authority_required": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_round_manifest_status_match": true,
  "accepted_requires_generated_artifacts_gate_round_coverage": true,
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
    "project_state/rounds/round_20260623_manifest_status_and_artifact_coverage_hardening_v1/*"
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

Implement Manifest Status and Generated Artifact Coverage Hardening v1.

The previous engineering round fixed the self-referential `report-auto-summary` / `final-check` status-source cycle and reached a usable `SUCCESS / ACCEPTED` state. The audit outcome is `ACCEPTED_WITH_LIMITATIONS`, not a clean `ACCEPTED`, because two closeout/audit-chain weaknesses remain:

1. `project_state/rounds/round_20260622_self_referential_status_convergence_v1/round_manifest.json` still recorded stale status metadata: `report_status: PARTIAL` and `acceptance_recommendation: NEEDS_REVIEW`, while the live and archived `codex_execution_report.md` summary had converged to `SUCCESS / ACCEPTED`.
2. Some current-round gate artifacts that were changed or generated, especially closeout/snapshot artifacts such as `project_state/gates/run_closeout_execution_log.json` and `project_state/gates/round_close_snapshot.json`, were visible in dirty-state / files_changed evidence but were not consistently represented in generated_artifacts unless covered by existing gate exceptions.

This round must convert those limitations into enforceable project-gate behavior:

- A `SUCCESS / ACCEPTED` report must not be accepted when the current round manifest records stale `PARTIAL / NEEDS_REVIEW` report metadata.
- Current-round generated or updated gate/round artifacts must either be listed in `generated_artifacts` or explicitly classified as non-generated / diagnostic / exempt with auditable reasoning.
- The fix must preserve command-plan authority, execution-log consistency, report-auto-summary consistency, archive strictness, policy-lint, policy-impact, and no-sample-solving boundaries.

This is an engineering hardening round only. It must not continue or reopen reverse solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is still background-only `samplereverse` sample state. It suggests `collect_missing_evidence`, but it is not authoritative for this round. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `ACCEPTED_WITH_LIMITATIONS` for `decision_20260622_self_referential_status_convergence_v1`.

Accepted previous-round evidence:

- `codex_execution_report.md` carried `status: SUCCESS` and `acceptance_recommendation: ACCEPTED`.
- `pytest_result.txt` reported `PASSED` and recorded 781 focused `tests/test_project_gate.py` tests and 1079 combined `tests/test_project_gate.py tests/test_project_state.py` tests passing.
- `final_gate_result.json` reported `gate_status: PASSED`, no blocking reasons, and `recommended_next_action: no_action_required`.
- `command_plan.json` used `full` profile, `closeout_allowed: true`, and `omitted_commands: []`.
- `execution_log.json` reported 19 command entries and `gate_status: PASSED`.
- `policy_lint_result.json` and `policy_impact_audit.json` both reported `PASSED`.
- `report_summary_synthesis.json` and `codex_report_auto_summary.json` both converged to `SUCCESS / ACCEPTED`.

Remaining limitation to fix:

- The archived round manifest for the previous round still had `acceptance_recommendation: NEEDS_REVIEW` and `report_status: PARTIAL` even though the archived report summary had `SUCCESS / ACCEPTED`. This must become a detectable and preventable inconsistency.
- The previous round's report/files_changed evidence included closeout and round snapshot artifacts. This round must make generated_artifacts coverage strict enough that current gate/round artifacts cannot silently drift out of generated_artifacts coverage.

Artifact freshness:

- Current evidence for this round must be regenerated under `decision_20260623_manifest_status_and_artifact_coverage_hardening_v1` and `round_20260623_manifest_status_and_artifact_coverage_hardening_v1`.
- Artifacts from `round_20260622_self_referential_status_convergence_v1` are prior-round context only.
- The 50 missing historical/backlog `samplereverse` artifacts remain external state notices for this engineering round and must not be claimed as current evidence.

Existing capabilities to reuse:

- `preflight` and decision metadata validation.
- `command-plan`, including profile selection and omitted-command authority checks.
- `execution-log` derived from top-level `pytest_result.txt` and `command_plan.json`.
- `report-auto-summary` and `report-summary` synthesis.
- `final-check`, including report/pytest/command-plan/execution-log consistency.
- `run-closeout`, `close-round`, round manifest creation, round archive checks, and close snapshot handling.
- `policy-lint` and `policy-impact`.
- Existing tests in `tests/test_project_gate.py` for closeout, archive, command-plan authority, generated artifact coverage, report-summary synthesis, and status policy.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round changes closeout/final-check/report-summary behavior and tests, command-plan should select or require `full` validation.
- Tests are subordinate to command-plan. If this Tests section and command-plan conflict, command-plan is the execution authority.
- Closeout may run only if command-plan authorizes it and the selected profile allows closeout.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not broaden this round into Web UI, AgentRunner, Codex adapter, Trae adapter, job manager, database, queue, scheduler, daemon, API planner, API auditor, GitHub Actions workflow, or background worker work.

Do not continue `samplereverse` solving or any sample-solving task.

Do not read the full `solve_reports/` directory or full `PROJECT_PROGRESS_LOG.txt`.

Do not treat old sample artifacts as current evidence.

Do not weaken command-plan authority. Real unauthorized top-level commands must still fail final-check.

Do not weaken execution-log consistency. Top-level commands must remain auditable through `pytest_result.txt` and `execution_log.json`.

Do not weaken report-auto-summary consistency. Real mismatches in `tests_ran`, `files_changed`, `generated_artifacts`, IDs, exit codes, archive artifacts, or Required Audit coverage must still fail or warn according to existing policy.

Do not weaken archive strictness. Archived report and archived pytest_result must still match the live artifacts at closeout.

Do not manually edit only `round_manifest.json` to mask the previous symptom. The required output is code plus regression tests that prevent recurrence.

Do not classify all manifest/status mismatches as acceptable. Only explicitly modeled historical/diagnostic metadata may be non-blocking, and not for a final `SUCCESS / ACCEPTED` current-round manifest mismatch.

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
9. `project_state/gates/run_closeout_execution_log.json` if present
10. `project_state/gates/round_close_snapshot.json` if present
11. `project_state/gates/round_delta_summary.json`
12. `project_state/gates/policy_lint_result.json`
13. `project_state/gates/policy_impact_audit.json`
14. `project_state/rounds/round_20260622_self_referential_status_convergence_v1/round_manifest.json` only as bounded prior-round diagnostic evidence
15. `project_state/rounds/round_20260622_self_referential_status_convergence_v1/codex_execution_report.md` only as bounded prior-round diagnostic evidence

Do not scan the full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. What exact fields in the previous round manifest were stale, and how did they differ from the live/archived `codex_report_summary`?
2. What code path creates or refreshes `round_manifest.json`, and why did stale `PARTIAL / NEEDS_REVIEW` metadata survive after report convergence?
3. What rule now ensures a current `SUCCESS / ACCEPTED` report cannot pass final-check when the current round manifest status/recommendation disagrees with the report summary?
4. What rule now ensures current-round gate/round artifacts such as `run_closeout_execution_log.json` and `round_close_snapshot.json` are covered by `generated_artifacts` or explicitly exempted with auditable reasoning?
5. How does the fix preserve real mismatch detection for command-plan authority, execution-log consistency, report-summary fields, report-auto-summary fields, archive artifacts, and Required Audit coverage?
6. How does closeout now make live report, archived report, live pytest_result, archived pytest_result, and round manifest agree at the accepted final state?
7. Which regression tests prove stale manifest status mismatch detection, generated_artifacts coverage hardening, non-regression for allowed diagnostic artifacts, and command-plan authority preservation?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no forbidden path mutation, and no heavy artifact scan?

Do not write TODO, TBD, PENDING, “should pass”, or speculative answers.

## 6. Implementation Scope

Primary scope: harden project-gate closeout/final-check/report-summary behavior for round manifest status consistency and generated_artifacts coverage.

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
- `project_state/rounds/round_20260623_manifest_status_and_artifact_coverage_hardening_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Add or harden final-check coverage so that, for a current `SUCCESS / ACCEPTED` report, the current round manifest's `report_status` and `acceptance_recommendation` must match the live/archived report summary.
3. Ensure closeout/close-round writes or refreshes manifest status metadata after the report has converged, or add an explicit post-close manifest refresh step that is auditable and covered by tests.
4. Ensure archived report and live report still match byte-for-byte or by the existing strict comparison rule already used by final-check.
5. Ensure generated_artifacts coverage includes all current-round generated or updated gate/round artifacts, especially closeout/snapshot artifacts, unless a narrowly defined diagnostic exemption is recorded and tested.
6. Ensure a stale previous-round manifest may remain as historical evidence, but a stale current-round manifest must fail or block acceptance.
7. Keep historical/backlog sample artifact notices non-blocking for engineering rounds when not claimed as current evidence.
8. Add focused regression tests for stale manifest status mismatch, manifest refresh after convergence, generated_artifacts coverage for closeout/snapshot artifacts, and non-regression of command-plan/execution-log authority.
9. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, and `codex_execution_report.md`.
10. Run closeout if and only if command-plan authorizes it.
11. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, run-closeout `PASSED`, and no blocking reasons.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260623_manifest_status_and_artifact_coverage_hardening_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260623_manifest_status_and_artifact_coverage_hardening_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260623_manifest_status_and_artifact_coverage_hardening_v1
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
- current-round manifest status cannot be made to match final report summary;
- generated_artifacts coverage cannot be made strict or explicitly auditable;
- run-closeout cannot keep nested command evidence scoped outside the top-level command stream;
- final-check cannot distinguish stale previous-round manifest evidence from current-round manifest mismatch;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, execution-log consistency regresses, policy-lint fails, policy-impact fails, run-closeout fails, final-check has blocking reasons, current round manifest remains stale, generated_artifacts coverage remains incomplete without explicit exemption, or the final report remains `PARTIAL / NEEDS_REVIEW` for reasons other than a clearly documented real blocker.
