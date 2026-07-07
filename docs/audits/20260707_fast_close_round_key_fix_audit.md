# Audit: fast close-round key fix round

> Audit material — not execution authority. This document records an external audit conclusion for the current project-governance round. It does not authorize commands, file changes, runner dispatch, workflow dispatch, sample solving, Web runtime, database work, deletion, migration, closeout, or close-round. Current execution authority remains `project_state/decision_packet.md`; command authority remains `project_state/gates/command_plan.json`.

## Conclusion

```text
REWORK_REQUIRED
```

The current round cannot be accepted as `ACCEPTED_WITH_LIMITATIONS` because the current gate evidence still reports blocking final-check/report-summary failures.

## Audited Round

```text
decision_id: decision_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1
round_id: round_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1
mainline: project_governance
profile: fast
```

## Evidence Inspected

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
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
project_state/roadmap/workstreams.json
docs/roadmap/next_step_after_scoped_metadata_foundation.md
```

## Findings

### 1. Decision metadata is valid

The decision packet contains `decision_meta` with:

```text
status: APPROVED
mainline: project_governance
skill_profiles: reverse-agent-iteration@v2
```

The registry marks `reverse-agent-iteration` as active version 2. This part is acceptable.

### 2. Scope is fast roadmap registration only

The current decision is a fast project-governance roadmap-registration round. It explicitly forbids:

```text
closeout / close-round
Phase A.1 implementation
project_state/domains/* creation
current_state.json migration
task_packet.json modification
negative_results split or migration
source/test modification
Web/frontend runtime
runner dispatch
workflow dispatch
model API invocation
database work
sample solving
external reverse tools
local commit/push/branch/PR/merge/rebase by executor
```

The command-plan correctly uses a fast profile with `closeout_allowed=false` and only authorizes startup, preflight, command-plan, report-summary, and final-check commands.

### 3. Command execution coverage is mostly compliant

The execution log records 12 commands, all matching command-plan expected exit codes. Omitted commands such as pytest, run-closeout, and close-round were not executed. This means there is no obvious command-plan overreach in the observed transcript.

However, this only proves command authorization compliance. It does not prove the round is acceptable.

### 4. Report-summary failed

`project_state/gates/report_summary_synthesis.json` reports:

```text
synthesis_status: FAILED
synthesized status: FAILED
synthesized acceptance_recommendation: REWORK_REQUIRED
```

It differs from the execution report, which claims:

```text
status: ACCEPTED_WITH_LIMITATIONS
acceptance_recommendation: ACCEPTED_WITH_LIMITATIONS
```

This is a direct status mismatch.

### 5. Final-check failed

`project_state/gates/final_gate_result.json` reports:

```text
gate_status: FAILED
```

Blocking reasons include:

```text
report_summary_fields_match_synthesis: execution_report_summary differs from synthesized summary
status_policy_valid: status policy found blocking issues
closeout_nested_failures_absent: run_closeout_result.json contains active nested FAIL/FAILED states
```

A failed final-check cannot support `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS` under this decision's own audit rules.

### 6. pytest_result PASSED is not enough

`project_state/pytest_result.txt` reports `status=PASSED`, but that status means the recorded command exit codes matched the command-plan expected exit codes. The command-plan allowed report-summary and final-check to exit with either 0 or 1 as diagnostic commands.

Therefore, pytest_result can be command-transcript-valid while final-check still fails. In this state, the report must not claim acceptance.

### 7. current_state/task_packet remain non-authoritative sample state

`project_state/current_state.json` and `project_state/task_packet.json` still contain `samplereverse` / reverse-solving sample state. They are not current execution authority for this project-governance round.

This is acceptable as background, but it confirms that the current round must be judged from `decision_packet.md`, command-plan, report-summary, final-check, and execution report consistency.

## Blocking Issues

```text
1. final_gate_result.json gate_status is FAILED.
2. report_summary_synthesis.json synthesis_status is FAILED.
3. codex_execution_report.md claims ACCEPTED_WITH_LIMITATIONS despite synthesis/final-check saying FAILED/REWORK_REQUIRED.
4. run_closeout_result.json stale nested failures are still treated as active blockers by final-check.
5. status_policy_valid remains FAIL.
```

## Required Rework

The next decision should be a small `project_governance` rework round focused only on truthful fast-profile status reconciliation.

Recommended goal:

```text
Fix the fast roadmap-registration round status mismatch so report-summary, final-check, codex_execution_report, execution_report, and pytest_result agree on one truthful status.
```

Recommended scope:

```text
- Do not run closeout.
- Do not create project_state/domains/*.
- Do not implement Phase A.1.
- Do not modify reverse-solving, Web, frontend, runner, database, or external-tool paths.
- Either fix stale run_closeout_result handling for closeout-forbidden fast rounds, or downgrade the execution report honestly to REWORK_REQUIRED.
```

Acceptance rule for the rework:

```text
If final-check remains FAILED, report status must be REWORK_REQUIRED.
If report status is ACCEPTED_WITH_LIMITATIONS, final-check must not contain blocking_reasons.
report_summary_synthesis, final_gate_result, codex_execution_report, execution_report, and pytest_result must be mutually consistent.
```

## Final Audit Result

```text
REWORK_REQUIRED
```
