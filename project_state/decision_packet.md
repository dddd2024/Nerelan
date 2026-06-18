```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_fast_artifact_only_validation_v5_parser_safe_scope",
  "round_id": "round_20260618_fast_artifact_only_validation_v5_parser_safe_scope",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Redo the fast artifact-only validation with parser-safe decision text and strict current-artifact hygiene.

This round exists because v4 failed preflight before normal validation. The failure was not caused by startup command order. It was caused by decision-scope parsing: path-like forbidden entries written under the implementation-scope section were interpreted as allowed scope. This v5 decision avoids that ambiguity by listing only allowed files in Implementation Scope and expressing prohibited areas in prose outside that list.

Target behavior:

- `gate-profile` classifies this decision as `profile=fast`.
- `gate-profile` sets `closeout_allowed=false`.
- `command-plan` records omitted `pytest` metadata.
- `command-plan` records omitted `close-round` metadata.
- Active `command-plan` commands do not include pytest.
- Active `command-plan` commands do not include close-round.
- `run-round --dry-run --json` may be omitted by fast profile. If omitted, the report must say it was omitted and must not claim the old dry-run artifact as current.
- Stale closeout snapshot artifacts from previous full rounds must not be listed as current generated artifacts.
- `final-check` may be `WARN` before archive because this fast validation intentionally does not close the round, but it must have no FAIL checks for a successful report.
- If final-check is `WARN`, the report must say `WARN with no FAIL checks`; it must not call that `PASSED`.
- No source or test code is modified.
- No close-round is run.
- No normal round archive is produced.

This is an `engineering_branch` artifact-only validation round. It must not become another source-fix round.

## 2. Current Evidence

Current execution authority is this live `project_state/decision_packet.md`. `task_packet.json` remains advisory only and must not override this decision.

State summary:

- `task_packet.json` still says `execution_scope=decision_packet_controls_current_round`; therefore this decision controls Codex execution.
- `current_state.json` still describes old `samplereverse` reverse-solving state with missing candidate/runtime evidence. That state is not current evidence for this engineering validation.
- `artifact_index.json` still shows most historical `samplereverse` artifacts as missing. Those reverse artifacts must not be used as current evidence.
- `negative_results.json` still blocks old reverse-solving directions, including blind old solver search, budget-only expansion, compare-semantics-disagree candidates as primary frontier, committing full solve report outputs, and repeated failed `samplereverse` branches. This round must not touch those directions.
- `.codex-skills/registry.json` contains active `reverse-agent-iteration` version 2, so `reverse-agent-iteration@v2` is valid.

Previous accepted source-fix evidence:

- `decision_20260618_fast_non_closeout_prose_precision_rework_v1` was audited as `ACCEPTED_WITH_LIMITATIONS`.
- It replaced raw `close-round` substring matching with precise close-round/archive success predicates.
- It added regression tests showing legal omission prose passes, close-round/archive success prose fails, archive paths still fail, and full-profile behavior is unchanged.

Previous v3/v4 validation evidence:

- v3 proved the core fast behavior: `profile=fast`, `closeout_allowed=false`, omitted pytest, omitted close-round, no active pytest, no active close-round, and `fast_profile_closeout_consistency` passed.
- v3 failed audit because stale closeout snapshot data from an older round was listed as generated/current evidence, and because dry-run omission semantics were not explicit enough.
- v4 addressed the stale-artifact wording but failed preflight because the decision text placed path-like forbidden entries in a section parsed as implementation scope.
- v4 Codex correctly reported `FAILED/REWORK_REQUIRED` instead of faking success. It also preserved the useful fast observations: `profile=fast`, `closeout_allowed=false`, pytest omitted, close-round omitted, no active pytest, and no active close-round.

Execution-order evidence from v4:

- The actual startup command blocks were ordered correctly: set location, get location, test path, rev-parse, git status, then preflight.
- The preflight failure came from scope parsing, not from startup command order.
- Command-plan may list diagnostic commands in a different order, but actual execution order in `pytest_result.txt` must still place startup checks before preflight.

Existing implementation to use, not modify:

- The existing gate/profile/report/final-check implementation is sufficient for this round.
- The existing tests from the accepted source-fix round are sufficient; do not run pytest in this fast validation.

Tool capability boundary:

- This round is not reverse-solving.
- Do not run reverse-engineering tools, debugger hooks, emulators, sample runners, runtime probes, GUI/frontend workflows, or raw sample analysis.
- Do not inspect or modify mature reverse-engineering tool integrations.

Artifact freshness rule for this round:

- Gate artifacts may be current evidence only if they carry current v5 decision/round/report IDs where applicable.
- Any gate artifact carrying an older decision or round ID is stale and must not appear in generated artifacts or be described as current for v5.
- A stale closeout snapshot is expected to remain from a previous full closeout round. It must be excluded from current v5 generated evidence.

## 3. Do Not Do

Do not modify source code.

Do not modify test files.

Do not run pytest.

Do not run close-round.

Do not create a normal round archive for this fast non-closeout validation.

Do not claim normal archive success, close-round success, archived closeout success, or closed-round success.

Do not list stale gate artifacts as generated or current evidence.

Do not claim an old dry-run artifact as current if the current fast command-plan omits dry-run.

Do not use stale or missing reverse-sample artifacts as current evidence.

Do not repeat any negative reverse-solving direction.

Do not read the full progress log or full solve report output tree.

Do not modify skill files, solve report outputs, solver code, harness code, strategy code, transform code, debugger/tool-runner integrations, sample runner code, GUI/frontend code, or raw sample files.

Do not update this decision file during Codex execution. If this decision file is dirty at startup, stop.

## 4. Files To Inspect

Read default project-state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Inspect generated gate/report artifacts only as evidence:

- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`

A stale closeout snapshot may be inspected only to confirm that it is stale and therefore must not be claimed as current. Do not list it as generated evidence unless it actually carries the current v5 IDs, which is not expected because close-round is disallowed.

A dry-run artifact may be inspected only if it was actually regenerated in this v5 round. If the fast command-plan omits dry-run, do not list that artifact as generated evidence.

Do not inspect implementation files unless a fast gate output explicitly reports a contradiction that cannot be understood from generated artifacts. If implementation inspection or source modification becomes necessary, stop and report `REWORK_REQUIRED` instead of modifying code.

## 5. Required Audit

Before writing any report or artifact, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded after path confirmation and before any file modification.
3. The decision file is not dirty at startup.
4. No source or test files are dirty at startup.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. `task_packet.json` is non-authoritative and this decision controls execution.
7. This decision has artifact-only scope and should classify as `profile=fast`.
8. `closeout_allowed=false` is present in the gate-profile output.
9. Preflight must pass before normal validation continues. If preflight fails, stop normal validation and write an honest failed handoff report only.

During validation, verify:

1. `command-plan` includes omitted pytest metadata.
2. `command-plan` includes omitted close-round metadata.
3. Active command-plan commands do not include pytest.
4. Active command-plan commands do not include close-round.
5. If dry-run is omitted by fast profile, the report states that it was omitted and does not claim an old dry-run artifact as current.
6. The report body explicitly states that close-round was intentionally omitted because `closeout_allowed=false`.
7. The report body accurately states the final-check status. If final-check returns `WARN` with no FAIL checks, the report must say exactly that.
8. `fast_profile_closeout_consistency` passes despite legal omission prose.
9. `report_summary_synthesis` matches the report summary.
10. `final-check` has no FAIL checks for a successful report.
11. No generated artifact path points to a round archive tree.
12. No source or test path appears in `files_changed` or `generated_artifacts`.
13. Stale closeout snapshot data is not listed as generated/current evidence.
14. All generated/current gate artifacts listed in `generated_artifacts` carry current v5 IDs where those artifacts have ID fields.
15. Actual command blocks in `pytest_result.txt` keep startup checks before preflight.

## 6. Implementation Scope

Allowed files for this validation round are only:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`

No other file is in implementation scope for this round.

Required report shape:

- `codex_report_summary.status` may be `SUCCESS` only if the validation has no FAIL checks.
- `codex_report_summary.acceptance_recommendation` may be `ACCEPTED` only if final-check has no FAIL checks and all freshness rules above are satisfied.
- `files_changed` and `generated_artifacts` must include only the allowed current project-state gate/report artifacts listed in this Implementation Scope section.
- The report body must include a short limitation note that this fast round did not run pytest and did not run close-round by design.
- The report body must explicitly state `close-round intentionally omitted because closeout_allowed=false`.
- The report body must explicitly avoid claiming archived closeout, normal round archive, or close-round success.
- If final-check is `WARN`, the report body must say `final-check: WARN with no FAIL checks`.
- If preflight fails, the report must use `FAILED/REWORK_REQUIRED` and must not continue as a successful validation.

## 7. Tests

Run and record the following in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Do not run these commands in this fast validation round:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_fast_artifact_only_validation_v5_parser_safe_scope
```

Dry-run is not required in v5 if command-plan omits it under fast profile. If omitted, do not list the dry-run artifact as generated/current.

The result record must include:

- `decision_id=decision_20260618_fast_artifact_only_validation_v5_parser_safe_scope`
- `round_id=round_20260618_fast_artifact_only_validation_v5_parser_safe_scope`
- final `report_id`
- every command actually run
- explicit note that pytest and close-round were intentionally omitted by fast profile
- explicit note whether dry-run was omitted by fast profile or actually regenerated under current v5 IDs
- explicit evidence that startup checks were executed before preflight

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- startup path is not `F:\reverse-agent`;
- the decision file is dirty at startup;
- any source or test file is dirty at startup;
- `decision_meta` is missing or not `APPROVED`;
- `reverse-agent-iteration@v2` is not active;
- preflight fails;
- gate-profile does not classify this round as `profile=fast`;
- gate-profile does not set `closeout_allowed=false`;
- command-plan includes active pytest;
- command-plan includes active close-round;
- the validation cannot pass without modifying source or tests;
- final-check reports any FAIL check;
- `fast_profile_closeout_consistency` fails on legal omission prose;
- any stale gate artifact is listed as current generated evidence;
- stale closeout snapshot data is listed as generated/current evidence;
- an old dry-run artifact is listed as generated/current evidence without being regenerated in v5;
- any artifact path points to a round archive tree;
- any source or test path appears in `files_changed` or `generated_artifacts`;
- any reverse-solving, solver, harness, debugger/tool-runner, sample, GUI/frontend, skill-file, or solve-report-output modification becomes necessary.
