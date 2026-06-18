```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_fast_non_closeout_status_semantics_fix_v1",
  "round_id": "round_20260618_fast_non_closeout_status_semantics_fix_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Fix the remaining fast-profile non-closeout status semantics defect that blocked `decision_20260618_fast_artifact_only_validation_v2` from being accepted.

The desired behavior is precise:

- A `fast` non-closeout artifact/report-only validation may report `status=SUCCESS` and `acceptance_recommendation=ACCEPTED` when the validation itself succeeded.
- That same report must not be interpreted as claiming normal `close-round` success or normal round archive success.
- `fast_profile_closeout_consistency` must reject actual closeout/archive success claims in fast non-closeout rounds, not reject a successful validation result merely because it is successful.
- `report_summary_synthesis` and `final-check` must continue to exempt fast non-closeout rounds from normal archive requirements.
- `full` and `standard` profile behavior must remain unchanged.

This is an `engineering_branch` source-fix round. It must stay limited to gate/report-status semantics and tests. Do not turn this into reverse solving, tool integration, training dataset work, frontend work, or sample solving.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json`, `current_state.json`, and old sample-solving state are advisory only and must not override this decision.

State facts:

- `task_packet.json` still says `execution_scope=decision_packet_controls_current_round`; therefore Codex must use this live decision as the current execution authority.
- `current_state.json` still describes old `samplereverse` sample state with missing candidate/runtime evidence; those reverse artifacts are not current evidence for this engineering gate task.
- `artifact_index.json` shows the historical `samplereverse` artifacts are mostly `missing`; those artifacts must not drive this round.
- `negative_results.json` still blocks old reverse-solving directions such as old `sample_solver` blind search, beam/budget-only expansion, `compare_semantics_agree=false` primary frontier, full `solve_reports/` commits, and repeated failed `samplereverse` candidate branches. None of those directions are relevant to this engineering source fix.
- `.codex-skills/registry.json` contains active `reverse-agent-iteration` version 2, so `reverse-agent-iteration@v2` is the active skill profile for this round.

Previous round evidence:

- `project_state/codex_execution_report.md` currently corresponds to `decision_20260617_fast_non_closeout_semantics_source_fix_v1`, not to the later artifact-only validation decision. It reports `SUCCESS/ACCEPTED`, changed `reverse_agent/project_gate.py` and `tests/test_project_gate.py`, and says 741 tests passed.
- `project_state/pytest_result.txt` currently also corresponds to `decision_20260617_fast_non_closeout_semantics_source_fix_v1`, not to `decision_20260618_fast_artifact_only_validation_v2`.
- The attempted `decision_20260618_fast_artifact_only_validation_v2` was audited as `REWORK_REQUIRED`: the validation exposed a status-semantics deadlock in `fast_profile_closeout_consistency` / synthesis. A successful fast non-closeout validation could not be represented as `SUCCESS/ACCEPTED` without being treated as a prohibited closeout success claim, while `FAILED/REWORK_REQUIRED` could pass the closeout-consistency check but would no longer represent validation success.

Existing related implementation to inspect and preserve:

- `reverse_agent/project_gate.py` already has gate-profile tiering: `fast`, `standard`, `full`.
- `reverse_agent/project_gate.py` classifies changes to `reverse_agent/project_gate.py` itself as `full` profile scope; therefore this source-fix round must run the full validation path.
- `reverse_agent/project_gate.py` already includes command-plan, gate-profile, report-summary, final-check, close-round, baseline/delta, generated artifact existence, decision immutability, and fast-profile checks. Do not duplicate those systems.
- Existing tests in `tests/test_project_gate.py` and `tests/test_project_state.py` are the relevant regression surface.

Existing tool capability boundary:

- This round is not reverse-solving.
- Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger hooks, emulator, solver, harness, sample runner, or runtime probe.
- Do not modify mature reverse-engineering tool integrations.

Artifact freshness:

- No reverse-sample artifact is current evidence for this gate semantics fix.
- Gate artifacts under `project_state/gates/` may be regenerated as part of the full engineering round, but stale gate artifacts must not be treated as proof until regenerated under this decision.

## 3. Do Not Do

Do not modify any files outside the allowed scope below.

Do not modify solver, harness, strategy, transform, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw sample, `.codex-skills/`, or `solve_reports/` files.

Do not repeat any `negative_results.json` reverse-solving direction.

Do not implement a second gate framework, second report-summary system, or second closeout model. Patch the existing checks in `reverse_agent/project_gate.py` only.

Do not make `fast` profile perform normal archive closeout.

Do not relax `full` profile close-round/archive requirements.

Do not let `fast` non-closeout reports claim normal archive success, normal close-round success, or round archive paths as if they were produced.

Do not make `ACCEPTED` globally mean closeout success. It may mean validation success only when the report/gate metadata explicitly says the round is fast, non-closeout, and non-archived.

Do not update `project_state/decision_packet.md` during execution. If this file is dirty at startup, stop.

Do not commit full `solve_reports/`.

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

Inspect these implementation/test files:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if existing project-state report/lint/pytest-result validation behavior is directly affected

Inspect generated gate artifacts only as evidence, not as implementation sources:

- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json` if close-round is run

Do not inspect unrelated solver/harness/tool-runner/debugger modules unless a gate command reports a forbidden-path blocker that explicitly names them.

## 5. Required Audit

Before modifying files, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. If startup `git status --short` already shows dirty `project_state/decision_packet.md`, stop immediately with `BLOCKED` / `REWORK_REQUIRED`.
4. If startup `git status --short` already shows dirty `reverse_agent/project_gate.py`, `tests/test_project_gate.py`, or `tests/test_project_state.py`, record it as inherited baseline only if the decision explicitly allows it. This decision does not allow inherited source/test dirty files, so stop unless the user separately resolves or authorizes that baseline.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. Current decision controls execution; `task_packet.json` is not authoritative.
7. Confirm this is a gate/report-status source fix, not reverse-solving.
8. Confirm existing gate-profile classification makes this a `full` profile round because `reverse_agent/project_gate.py` is in scope.

After implementation, audit:

1. `fast_profile_closeout_consistency` distinguishes validation success from closeout/archive success.
2. Fast non-closeout report metadata can represent `SUCCESS/ACCEPTED` validation without claiming normal archive/close-round success.
3. Fast non-closeout report metadata still fails if it claims `close-round` ran, `closeout_allowed=true`, normal round archive files, or normal archived closeout success.
4. Full-profile report/closeout/archive checks still require the normal archive path and are not weakened.
5. Standard-profile behavior is not widened unexpectedly.
6. `report_summary_synthesis` agrees with `final_check` for fast non-closeout success.
7. `command-plan` still records omitted `pytest` and omitted `close-round` entries for fast non-closeout artifact-only decisions.
8. No mature reverse tool integration is modified.

## 6. Implementation Scope

Allowed source/test files:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if needed for existing report/pytest-result validation compatibility

Allowed project-state/report artifacts:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/round_close_snapshot.json` if produced by close-round
- `project_state/rounds/round_20260618_fast_non_closeout_status_semantics_fix_v1/codex_execution_report.md` if close-round succeeds
- `project_state/rounds/round_20260618_fast_non_closeout_status_semantics_fix_v1/decision_packet.md` if close-round succeeds
- `project_state/rounds/round_20260618_fast_non_closeout_status_semantics_fix_v1/pytest_result.txt` if close-round succeeds
- `project_state/rounds/round_20260618_fast_non_closeout_status_semantics_fix_v1/round_manifest.json` if close-round succeeds

Required implementation shape:

- Prefer a small helper or narrowly scoped predicate that identifies a successful fast non-closeout validation as distinct from a normal closeout success claim.
- The predicate must be based on explicit metadata already present or added to gate/report synthesis, such as `profile=fast`, `closeout_allowed=false`, omitted `close-round`, absence of archive artifacts, and report prose/summary not claiming archived closeout success.
- Do not infer non-closeout solely from lack of archive files if `closeout_allowed=true`.
- Keep failure semantics strict for reports that claim `close-round`, archive success, or normal archive artifacts under fast non-closeout.
- Add regression tests that fail before this fix and pass after it.

Required tests to add or update:

1. Fast non-closeout artifact-only report with `status=SUCCESS` and `acceptance_recommendation=ACCEPTED`, explicit omitted `close-round`, no archive artifacts, and no archive success claim should pass `fast_profile_closeout_consistency` and synthesis/final-check expectations.
2. Fast non-closeout report with `status=SUCCESS` / `ACCEPTED` but report prose or summary claims normal archive/close-round success should fail.
3. Fast non-closeout report with archive paths in `generated_artifacts` should fail unless closeout is explicitly allowed, which it should not be for `fast`.
4. Fast non-closeout report with `FAILED` / `REWORK_REQUIRED` should remain allowed when validation actually fails; this must not be the only way to satisfy `fast_profile_closeout_consistency`.
5. Full profile source-change round must still require normal archive/close-round behavior and must not inherit the fast non-closeout exemption.
6. Command-plan for fast artifact-only decisions must still include omitted `pytest` and omitted `close-round` entries and must not include them as active commands.

Stop after this source-fix round. Do not run the next artifact-only validation as part of this same decision. The next GPT decision should be a separate `fast` artifact-only validation v3 once this source fix is accepted.

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
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If `final-check` has no FAIL checks and the worktree state is acceptable, run:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_fast_non_closeout_status_semantics_fix_v1
```

The pytest/result header must include:

- `decision_id=decision_20260618_fast_non_closeout_status_semantics_fix_v1`
- `round_id=round_20260618_fast_non_closeout_status_semantics_fix_v1`
- final `report_id`
- every command actually run
- exact pytest outcome
- explicit note whether close-round was run or intentionally skipped

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- startup path is not `F:\reverse-agent`;
- live `project_state/decision_packet.md` is dirty at startup;
- startup already has dirty source/test files in this decision's scope;
- `decision_meta` is missing or not `APPROVED`;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- implementing the fix requires modifying files outside the allowed scope;
- making fast non-closeout `SUCCESS/ACCEPTED` pass requires weakening full-profile archive/closeout checks;
- `command-plan` no longer records omitted close-round for fast non-closeout artifact-only decisions;
- report-summary and final-check still disagree on successful fast non-closeout validation;
- any reverse-solving, solver, harness, IDA/Ghidra/debugger/tool-runner, sample, GUI/frontend, or `.codex-skills/` modification becomes necessary;
- pytest fails and the failure is not explained with a bounded, decision-scoped next action;
- final-check reports FAIL after the report is written.
