```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework",
  "round_id": "round_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Redo fast artifact-only validation with strict stale-gate-artifact hygiene.

The goal is not to change source code or tests. The goal is to validate fast non-closeout behavior while ensuring the report, pytest result, report-summary synthesis, and final-check only claim current artifacts from this round.

The specific v4 target behavior is:

- `gate-profile` classifies this decision as `profile=fast`.
- `gate-profile` sets `closeout_allowed=false`.
- `command-plan` records omitted `pytest` and omitted `close-round` metadata.
- Active `command-plan` commands do not include pytest or close-round.
- `run-round --dry-run --json` is either actually executed and recorded under current v4 IDs, or explicitly omitted by fast profile and not claimed as generated/current evidence.
- `project_state/gates/round_close_snapshot.json` must not be listed as a current generated artifact unless it is regenerated with the current v4 decision/round IDs. The expected behavior is to leave it unclaimed or remove stale mention from report artifacts, not to run close-round.
- `final-check` may be `WARN` before archive because fast non-closeout intentionally does not close the round, but it must have no FAIL checks.
- The report must describe final-check accurately as `WARN with no FAIL checks` if that is the actual output.
- No normal round archive is produced, no close-round is run, and no `project_state/rounds/round_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework/**` path is created or claimed.

This is an `engineering_branch` artifact-only rework validation round.

## 2. Current Evidence

Current execution authority is this live `project_state/decision_packet.md`. `task_packet.json` remains advisory only and must not override this decision.

State summary:

- `task_packet.json` still says `execution_scope=decision_packet_controls_current_round`; therefore this decision controls Codex execution.
- `current_state.json` still describes old `samplereverse` reverse-solving state with missing candidate/runtime evidence. That state is not current evidence for this engineering gate validation.
- `artifact_index.json` still shows most historical `samplereverse` artifacts as `missing`; stale/missing reverse artifacts must not be used as current evidence.
- `negative_results.json` still blocks old reverse-solving directions such as old `sample_solver` blind search, beam/budget-only expansion, `compare_semantics_agree=false` primary frontier, committing full `solve_reports/`, and repeated failed `samplereverse` branches. This round must not touch those directions.
- `.codex-skills/registry.json` contains active `reverse-agent-iteration` version 2, so `reverse-agent-iteration@v2` is valid.

Previous accepted source-fix evidence:

- `decision_20260618_fast_non_closeout_prose_precision_rework_v1` was audited as `ACCEPTED_WITH_LIMITATIONS`.
- It replaced raw `close-round` substring matching with precise close-round/archive success predicates.
- It added regression tests showing legal omission prose passes, close-round/archive success prose fails, archive paths still fail, and full-profile behavior is unchanged.

Previous v3 validation evidence:

- `decision_20260618_fast_artifact_only_validation_v3` proved the core fast behavior: `profile=fast`, `closeout_allowed=false`, omitted pytest, omitted close-round, no active pytest, no active close-round, and `fast_profile_closeout_consistency` passed.
- v3 is not acceptable because `project_state/gates/round_close_snapshot.json` was listed in `generated_artifacts` even though that file still carried the previous `decision_20260618_fast_non_closeout_prose_precision_rework_v1` decision/round IDs.
- v3 also had a Tests/command mismatch: the decision text required `run-round --dry-run --json`, but command-plan omitted run-round and no executed command block recorded it. v4 must make the fast omission semantics explicit and must not claim stale `run_round_result.json` as current unless it is actually regenerated with v4 IDs.
- v3 report prose overstated final-check as `PASSED with no FAIL checks` even though the final-check artifact had `gate_status=WARN`; v4 must state the actual final-check status precisely.

Existing implementation to use, not modify:

- `reverse_agent/project_gate.py` already provides gate-profile classification, command-plan trimming, report-summary synthesis, final-check, close-round, baseline/delta checks, generated artifact existence checks, and fast-profile closeout consistency checks.
- `tests/test_project_gate.py` already contains source-level regression tests from the accepted prose-precision fix.

Tool capability boundary:

- This round is not reverse-solving.
- Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger hooks, emulator, solver, harness, sample runner, runtime probe, GUI/frontend, or raw sample analysis.
- Do not inspect or modify mature reverse-engineering tool integrations.

Artifact freshness rule for this round:

- Gate artifacts under `project_state/gates/` may be current evidence only if they carry current v4 decision/round/report IDs where applicable.
- If a gate artifact carries an older decision or round ID, it is stale and must not appear in `generated_artifacts` or be described as generated/current for v4.
- `round_close_snapshot.json` is expected to be stale from the previous full closeout round. It must be excluded from current v4 generated evidence unless regenerated with v4 IDs, which should not happen because close-round is disallowed.

## 3. Do Not Do

Do not modify `reverse_agent/*.py`.

Do not modify `tests/*.py`.

Do not run pytest.

Do not run close-round.

Do not create or update `project_state/rounds/round_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework/**`.

Do not claim normal archive success, close-round success, archived closeout success, or closed-round success.

Do not list stale gate artifacts as generated/current evidence.

Do not list `project_state/gates/round_close_snapshot.json` in `files_changed` or `generated_artifacts` unless it carries current v4 IDs. The expected valid path is to leave it unclaimed.

Do not list `project_state/gates/run_round_result.json` in `files_changed` or `generated_artifacts` unless it was actually regenerated under current v4 IDs.

Do not use stale/missing reverse artifacts as current evidence.

Do not repeat any `negative_results.json` reverse-solving direction.

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not modify solver, harness, strategy, transform, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw sample, `.codex-skills/`, or `solve_reports/` files.

Do not update this decision file during Codex execution. If `project_state/decision_packet.md` is dirty at startup, stop.

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
- `project_state/gates/run_round_result.json` only if actually regenerated in this round
- `project_state/gates/round_close_snapshot.json` only to confirm it is stale and must not be claimed as current
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`

Do not inspect implementation files unless a fast gate output explicitly reports a contradiction that cannot be understood from generated artifacts. If implementation inspection or source modification becomes necessary, stop and report `REWORK_REQUIRED` instead of modifying code.

## 5. Required Audit

Before writing any report or artifact, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded after path confirmation and before any file modification.
3. `project_state/decision_packet.md` is not dirty at startup.
4. No source/test files are dirty at startup.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. `task_packet.json` is non-authoritative and this decision controls execution.
7. This decision has artifact-only scope and should classify as `profile=fast`.
8. `closeout_allowed=false` is present in the gate-profile output.

During validation, verify:

1. `command-plan` includes omitted `pytest` metadata if the extracted decision test block contains a pytest command.
2. `command-plan` includes omitted `close-round` metadata, with no active close-round command.
3. `command-plan` active commands do not include pytest.
4. `command-plan` active commands do not include close-round.
5. If `run-round --dry-run --json` is omitted by fast profile, the report must state that it was omitted and must not list `run_round_result.json` as generated/current unless it was regenerated with current v4 IDs.
6. The report body explicitly states that `close-round` was intentionally omitted because `closeout_allowed=false`.
7. The report body accurately states the final-check status. If final-check returns `WARN` with no FAIL checks, the report must say exactly that rather than claiming final-check `PASSED`.
8. `fast_profile_closeout_consistency` passes despite legal omission prose.
9. `report_summary_synthesis` matches the report summary.
10. `final-check` has no FAIL checks.
11. No generated artifact path under `project_state/rounds/` is listed.
12. No source/test path appears in `files_changed` or `generated_artifacts`.
13. `round_close_snapshot.json` is not listed as generated/current unless it carries current v4 IDs.
14. All generated/current gate artifacts listed in `generated_artifacts` carry current v4 IDs where those artifacts have ID fields.

## 6. Implementation Scope

Allowed files for this validation round:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json` only if actually regenerated with current v4 IDs

Explicitly disallowed files:

- `reverse_agent/project_gate.py`
- any other `reverse_agent/*.py`
- any `tests/*.py`
- `.codex-skills/**`
- `solve_reports/**`
- `project_state/rounds/round_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework/**`
- `project_state/gates/round_close_snapshot.json` unless it is regenerated with current v4 IDs, which is not expected because close-round is disallowed

Required report shape:

- `codex_report_summary.status` may be `SUCCESS` only if the validation actually has no FAIL checks.
- `codex_report_summary.acceptance_recommendation` may be `ACCEPTED` only if final-check has no FAIL checks and all freshness rules above are satisfied.
- `files_changed` and `generated_artifacts` must include only allowed current project_state/gate/report artifacts.
- The report body must include a short limitation note that this fast round did not run pytest and did not run close-round by design.
- The report body must explicitly state `close-round intentionally omitted because closeout_allowed=false`.
- The report body must explicitly avoid claiming archived closeout, normal round archive, or close-round success.
- If final-check is `WARN`, the report body must say `final-check: WARN with no FAIL checks`.

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

Do not run:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework
```

`run-round --dry-run --json` is not required in v4 if `command-plan` omits it under fast profile. If it is omitted, do not list `project_state/gates/run_round_result.json` as generated/current unless it was regenerated with current v4 IDs.

The `pytest_result.txt` header must include:

- `decision_id=decision_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework`
- `round_id=round_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework`
- final `report_id`
- every command actually run
- explicit note that pytest and close-round were intentionally omitted by fast profile
- explicit note whether run-round dry-run was omitted by fast profile or actually regenerated under current v4 IDs

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- startup path is not `F:\reverse-agent`;
- `project_state/decision_packet.md` is dirty at startup;
- any source/test file is dirty at startup;
- `decision_meta` is missing or not `APPROVED`;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- `gate-profile` does not classify this round as `profile=fast`;
- `gate-profile` does not set `closeout_allowed=false`;
- `command-plan` includes active pytest;
- `command-plan` includes active close-round;
- the validation cannot pass without modifying source or tests;
- final-check reports any FAIL check;
- `fast_profile_closeout_consistency` fails on legal omission prose;
- any stale gate artifact is listed as current generated evidence;
- `round_close_snapshot.json` is listed as generated/current while carrying non-v4 IDs;
- `run_round_result.json` is listed as generated/current while carrying non-v4 IDs or without being regenerated in v4;
- any artifact path under `project_state/rounds/round_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework/**` is created or claimed;
- any source/test path appears in `files_changed` or `generated_artifacts`;
- any reverse-solving, solver, harness, IDA/Ghidra/debugger/tool-runner, sample, GUI/frontend, or `.codex-skills/` modification becomes necessary.
