# Next Step After Fast Close-Round Key Fix Audit

> **Roadmap material — not execution authority.** This document records the recommended next project-governance step after the external audit of `decision_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1`. It does not authorize commands, file changes, runner dispatch, workflow dispatch, sample solving, Web runtime, database work, deletion, migration, closeout, close-round, or report mutation. Current execution authority remains `project_state/decision_packet.md`; command authority remains `project_state/gates/command_plan.json`.

## 1. Current Position

The current repository state has an important governance mismatch:

```text
The current decision has been consumed/submitted,
but the current round is not cleanly accepted,
and the final gate evidence still reports blocking failures.
```

Observed state:

```text
decision_id: decision_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1
round_id: round_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1
mainline: project_governance
profile: fast
external audit conclusion: REWORK_REQUIRED
```

The uploaded audit document is:

```text
docs/audits/20260707_fast_close_round_key_fix_audit.md
```

That audit document is evidence only. It does not repair the active execution state.

## 2. Why a New Decision Is Required

The already-consumed decision cannot safely be reused to mutate execution reports or gate state.

The previous user instruction for execution was effectively:

```text
Only execute one round of approved tasks.
Do not re-plan.
```

Therefore the following actions exceed a simple audit upload and require a new `decision_packet.md`:

```text
1. Creating or replacing an execution-authoritative decision.
2. Generating a new command-plan.
3. Modifying project_state/codex_execution_report.md.
4. Modifying project_state/execution_report.md.
5. Regenerating project_state/gates/report_summary_synthesis.json.
6. Regenerating project_state/gates/final_gate_result.json.
7. Changing the accepted/rework status of the current round.
8. Fixing gate/status-policy code.
9. Reclassifying stale run_closeout_result.json failures for fast-profile rounds.
```

In short:

```text
Document upload can record the audit.
Only a new decision can authorize state repair.
```

## 3. Recommended Next Mainline

The next round should stay on:

```text
project_governance
```

Do not switch to:

```text
reverse_solving
tool_integration
training_dataset
web_workbench
automation_runner
crash_triage
```

The immediate issue is governance status consistency, not sample solving or feature expansion.

## 4. Recommended Next Work Item

Recommended work item:

```text
Fast Profile Report Status Reconciliation Rework
```

Purpose:

```text
Make report-summary, final-check, codex_execution_report, execution_report, and pytest_result agree on one truthful status for a closeout-forbidden fast-profile round.
```

This should be a small governance rework, not a broad state-taxonomy migration.

## 5. Primary Problem to Fix

Current evidence indicates:

```text
project_state/gates/report_summary_synthesis.json -> FAILED / REWORK_REQUIRED
project_state/gates/final_gate_result.json -> FAILED with blocking_reasons
project_state/codex_execution_report.md -> ACCEPTED_WITH_LIMITATIONS
project_state/execution_report.md -> ACCEPTED_WITH_LIMITATIONS
project_state/pytest_result.txt -> PASSED command transcript under expected-exit policy
```

This creates an invalid acceptance story:

```text
pytest_result PASSED only means command exit codes matched command-plan expectations.
It does not override final-check blocking failures.
```

The next round must choose one truthful outcome:

```text
Option A: If final-check remains FAILED, reports must say REWORK_REQUIRED.
Option B: If reports say ACCEPTED_WITH_LIMITATIONS, final-check must have no blocking_reasons.
```

## 6. Recommended Decision Scope

A future `decision_packet.md` should use a narrow scope.

Allowed categories, if explicitly authorized:

```text
1. Read current decision/report/gate evidence.
2. Regenerate report-summary and final-check after the report is updated.
3. Update codex_execution_report.md and execution_report.md to match gate truth.
4. Optionally adjust gate/status-policy logic only if the new decision explicitly authorizes source changes.
5. Optionally reclassify stale run_closeout_result.json failures as historical/non-current only if supported by source-level gate change and tests.
```

Recommended default path:

```text
First make the reports truthful.
Do not attempt a large source-level gate redesign unless strictly necessary.
```

## 7. Do Not Do in the Next Round

The next round should explicitly forbid:

```text
1. Do not implement Phase A.1 scoped metadata visibility refresh.
2. Do not create project_state/domains/*.
3. Do not copy or migrate current_state.json.
4. Do not split negative_results.json.
5. Do not convert top-level current_state.json into a global summary.
6. Do not run closeout or close-round unless the new decision explicitly allows it.
7. Do not run sample solving or candidate search.
8. Do not invoke IDA, Ghidra, OllyDbg, radare2, MCP, debugger, emulator, or external reverse tools.
9. Do not run Web/frontend runtime.
10. Do not create or migrate a database.
11. Do not run cleanup apply, file deletion, file move, tombstone write, or archive compaction apply.
12. Do not dispatch GitHub Actions, local runners, remote runners, or model APIs.
13. Do not commit/push/branch/PR/merge/rebase from the local executor.
14. Do not claim ACCEPTED or ACCEPTED_WITH_LIMITATIONS if final-check still reports blocking_reasons.
```

## 8. Files to Inspect in the Next Round

Minimum required files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/preflight_result.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/state_manifest.json
project_state/artifact_index.json
project_state/current_state.json
project_state/task_packet.json
project_state/negative_results.json
docs/audits/20260707_fast_close_round_key_fix_audit.md
docs/roadmap/next_step_after_fast_close_round_key_fix_audit.md
```

Optional files:

```text
project_state/context/current_context_packet.json
project_state/roadmap/workstreams.json
project_state/gates/gate_profile_plan.json
project_state/gates/round_baseline.json
project_state/gates/round_delta_summary.json
```

Do not read full `solve_reports/`.

Do not read full `PROJECT_PROGRESS_LOG.txt` unless a required gate artifact explicitly references it.

## 9. Required Audit for the Next Round

The next round must answer:

```text
1. Is the new decision_meta present, valid, APPROVED, and on mainline project_governance?
2. Is the selected skill profile active in .codex-skills/registry.json?
3. Does the new decision explicitly acknowledge the previous decision was already consumed/submitted?
4. Does the new decision avoid reusing consumed execution authority?
5. Does command-plan match the new decision and round IDs?
6. Were all executed commands authorized by command-plan?
7. Were any omitted commands executed?
8. Did the round avoid closeout if closeout remains forbidden?
9. Did the round avoid source/test changes unless explicitly allowed?
10. Did the round avoid domains/current_state/negative_results migration?
11. Does report-summary match execution_report?
12. Does final-check pass if the report claims ACCEPTED or ACCEPTED_WITH_LIMITATIONS?
13. If final-check fails, does the report honestly state REWORK_REQUIRED?
14. Is pytest_result aligned with command-plan and report IDs?
15. Does execution_log cover required command-plan commands?
16. Does the report avoid claiming Phase A.1 or Phase B completion?
```

Audit conclusion must be exactly one of:

```text
ACCEPTED
ACCEPTED_WITH_LIMITATIONS
REWORK_REQUIRED
BLOCKED
```

## 10. Acceptance Criteria

The next round can be accepted only if one of the following is true.

### Path 1: Honest REWORK_REQUIRED Close

Use this if final-check remains failed.

Required result:

```text
codex_execution_report.md status: REWORK_REQUIRED
execution_report.md status: REWORK_REQUIRED
report_summary_synthesis: matches report
final_gate_result: may remain FAILED, but report must not claim acceptance
pytest_result: current IDs and transcript present
execution_log: current IDs and command coverage present
```

This path is acceptable if the goal is to stop false acceptance and hand off a clean rework decision.

### Path 2: True ACCEPTED_WITH_LIMITATIONS

Use this only if final-check blocking failures are resolved.

Required result:

```text
codex_execution_report.md status: ACCEPTED_WITH_LIMITATIONS
execution_report.md status: ACCEPTED_WITH_LIMITATIONS
report_summary_synthesis: PASSED or no blocking status mismatch
final_gate_result: no blocking_reasons
pytest_result: current IDs and transcript present
execution_log: current IDs and command coverage present
limitations: explicit and non-blocking
```

This path requires resolving stale `run_closeout_result.json` treatment so old closeout failures do not remain active blockers for a closeout-forbidden fast-profile round.

## 11. Recommended Conservative Path

Prefer the conservative path first:

```text
Generate a new decision that authorizes only report truthfulness repair.
If final-check still fails, make the reports say REWORK_REQUIRED.
Do not attempt source-level gate repair in the same round unless the decision explicitly permits it.
```

Reason:

```text
The immediate defect is false acceptance.
False acceptance must be eliminated before deeper gate-policy repair.
```

After that, a later separate decision can address:

```text
fast-profile stale closeout artifact handling
status-policy canonical source rules
final-check treatment of historical run_closeout_result.json
Phase A.1 scoped metadata visibility refresh
```

## 12. Candidate Next Decision Shape

The next actual `decision_packet.md` should be a formal DECISION_PACKET with:

```text
schema_version: 1
status: APPROVED
mainline: project_governance
skill_profiles: ["reverse-agent-iteration@v2"]
```

Suggested decision id:

```text
decision_20260707_fast_profile_report_truth_rework_v1
```

Suggested round id:

```text
round_20260707_fast_profile_report_truth_rework_v1
```

Suggested goal:

```text
Repair the status-truthfulness mismatch left by the fast close-round key fix round by ensuring execution reports, report-summary, final-check, pytest_result, and execution_log agree on a truthful REWORK_REQUIRED or accepted-with-limitations state.
```

This section is only a candidate shape. It is not itself execution authority.

## 13. Final Recommendation

Next action:

```text
Create a new project_governance decision_packet for fast-profile report truthfulness rework.
```

Do not proceed directly to:

```text
Phase A.1
Phase B domain skeletons
User Solve Layer
Web workbench
Tool integration
Crash triage
Automation runner
```

The current governance state must first stop carrying a false acceptance claim.

## 14. One-Line Summary

```text
Before any new feature or migration, create a new decision that reconciles fast-profile report status with report-summary and final-check evidence.
```
