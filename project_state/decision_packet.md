```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_policy_impact_generated_artifacts_coverage_fix_v1",
  "round_id": "round_20260621_policy_impact_generated_artifacts_coverage_fix_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_policy_impact_audit_v1",
  "previous_round_id": "round_20260621_policy_impact_audit_v1",
  "previous_acceptance": "ACCEPTED_WITH_LIMITATIONS",
  "primary_goal": "Fix generated_artifacts coverage for policy_impact_audit.json and related gate artifacts.",
  "command_plan_authority_required": true,
  "accepted_requires_policy_impact_artifact_in_generated_artifacts": true,
  "accepted_requires_report_summary_detection_for_missing_policy_impact_artifact": true,
  "accepted_requires_final_check_passed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
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
    "project_state/rounds/round_20260621_policy_impact_generated_artifacts_coverage_fix_v1/*"
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

Fix generated artifact coverage for `project_state/gates/policy_impact_audit.json` and related gate artifacts.

The previous round `decision_20260621_policy_impact_audit_v1` was accepted with limitations because `policy_impact_audit.json` was generated and passed, but `codex_report_summary.generated_artifacts` did not list it. This round must close that reporting gap so future `SUCCESS` / `ACCEPTED` reports cannot omit a generated policy-impact artifact while still passing report-summary or final-check.

This is a small engineering cleanup. Do not expand into a new policy system.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is background only. It still describes stale `samplereverse` work and must not control this round.

Previous round status: `decision_20260621_policy_impact_audit_v1` was `ACCEPTED_WITH_LIMITATIONS`.

Accepted evidence from the previous round:

- `policy_impact_audit.json` existed and had `gate_status=PASSED`.
- It identified policy-sensitive files: `reverse_agent/project_gate.py` and `tests/test_project_gate.py`.
- It identified impacted domains: `command_plan`, `final_check`, `policy_lint`, `report_status_schema`, `report_summary`, and `tests`.
- `missing_report_topics=[]` and `blocking_reasons=[]`.
- final-check ultimately passed.

Limitation to fix:

- `codex_report_summary.files_changed` included `project_state/gates/policy_impact_audit.json`.
- `codex_report_summary.generated_artifacts` omitted `project_state/gates/policy_impact_audit.json`.
- The project rule is that generated or updated gate artifacts must be listed in `generated_artifacts`, especially when the decision contract explicitly requires that artifact.

Existing relevant capabilities to reuse:

- `report-summary` synthesis and diff checks
- final-check `generated_artifacts_cover_round_delta`, `generated_artifacts_cover_round_archive`, `required_closeout_artifacts_covered`, and related report/round checks
- round delta evidence from `project_state/gates/round_delta_summary.json`
- policy-impact artifact at `project_state/gates/policy_impact_audit.json`
- command-plan execution authority and report-summary/final-check status checks
- tests in `tests/test_project_gate.py`

This is not a reverse-solving round. Do not inspect or run sample binaries. Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or full `solve_reports/`.

## 3. Do Not Do

Do not redesign Policy Impact Audit.

Do not change the policy-sensitive domain mapping unless it is strictly necessary to test artifact coverage.

Do not create a policy manifest, prompt generator, database, workflow engine, or `execution_log.json`.

Do not modify prompt docs in this round. The limitation is in artifact reporting, not prompt wording.

Do not weaken final-check to accept missing generated artifacts.

Do not remove `policy_impact_audit.json` from `files_changed` to hide the problem. The fix must add or require it in `generated_artifacts`.

Do not change profile names. The current profile names are `fast`, `standard`, and `full`; do not introduce `medium` as a profile.

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

Then inspect only files relevant to this artifact coverage cleanup:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/policy_impact_audit.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/round_delta_summary.json`
7. `project_state/gates/round_close_snapshot.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/rounds/round_20260621_policy_impact_audit_v1/round_manifest.json` only if needed to understand the prior limitation

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What exact generated_artifacts omission from the previous round is being fixed?
2. Which code path now ensures `project_state/gates/policy_impact_audit.json` appears in `codex_report_summary.generated_artifacts` when it is generated or updated?
3. How does report-summary detect a missing `policy_impact_audit.json` generated_artifacts entry?
4. How does final-check detect or block the same omission for a `SUCCESS` / `ACCEPTED` report?
5. Does the fix generalize to other generated gate artifacts under `project_state/gates/*.json`, or is it intentionally limited to policy-impact? Explain the boundary.
6. How does the fix avoid false failures for rounds where policy-impact was not run and no `policy_impact_audit.json` was generated?
7. What regression tests prove the previous omission now fails and the corrected report now passes?
8. How does this round preserve Policy Impact Audit v1, policy-lint, command-plan authority, report-summary, final-check, and closeout behavior?

## 6. Implementation Scope

Implement one bounded cleanup: generated_artifacts coverage for `policy_impact_audit.json` and any directly related gate artifact accounting.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
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
- `project_state/rounds/round_20260621_policy_impact_generated_artifacts_coverage_fix_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Ensure `policy_impact_audit.json` is included in the synthesized `generated_artifacts` list when it is generated or appears in the current round delta as a gate artifact.
2. Ensure final-check treats a missing generated_artifacts entry for `project_state/gates/policy_impact_audit.json` as a failure for `SUCCESS` / `ACCEPTED` reports when the file exists and belongs to the current round.
3. Prefer a general gate-artifact coverage rule for generated `project_state/gates/*.json` artifacts, but keep the change bounded. Do not introduce broad historical scanning.
4. Preserve the distinction between `files_changed` and `generated_artifacts`: source/test files belong in `files_changed`; generated project_state/gates artifacts belong in both `files_changed` when changed and `generated_artifacts` when generated or updated.
5. Ensure report-summary synthesis and final-check agree on the expected `generated_artifacts` set.
6. Ensure closeout refresh preserves the corrected `generated_artifacts` list.
7. Add regression tests for:
   - report summary/final-check failing when `policy_impact_audit.json` is omitted from `generated_artifacts`;
   - passing when it is included;
   - no false failure when policy-impact was not run and the artifact is absent for the current round;
   - existing policy-impact, policy-lint, command-plan, final-check, report-summary, and closeout tests still passing.
8. Do not modify prompt docs or `.codex-skills/` in this round.

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

Run policy-lint and policy-impact only if command-plan explicitly includes or authorizes them:

```powershell
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_policy_impact_generated_artifacts_coverage_fix_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation for unrelated reasons;
2. this requires redesigning report-summary, final-check, closeout, or Policy Impact Audit beyond artifact coverage accounting;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. prompt docs, `.codex-skills/`, or forbidden project_state source files need changes;
5. the fix requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
6. the fix hides the artifact by removing it from `files_changed` instead of adding it to `generated_artifacts`;
7. command-plan authority, policy-impact, policy-lint, decision-command-plan conflict detection, report-summary, final-check, or closeout regresses;
8. `codex_execution_report.md`, `pytest_result.txt`, or gate artifacts use stale decision_id/round_id;
9. tests fail or any required command exit code is nonzero;
10. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
