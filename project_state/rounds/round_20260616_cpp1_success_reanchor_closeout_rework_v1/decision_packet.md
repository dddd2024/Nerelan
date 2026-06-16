```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_success_reanchor_closeout_rework_v1",
  "round_id": "round_20260616_cpp1_success_reanchor_closeout_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Close out `round_20260616_cpp1_success_target_reanchor_v1` and fix the gate command-kind limitation that blocked archive.

This is an `engineering_branch` round. Do not rerun `CPP1.exe`. Do not continue solving. Do not regenerate the reanchor artifact unless needed only to verify metadata.

Required end state:

- command-plan recognizes the reanchor CLI or a generic project artifact-builder CLI;
- `command_plan_ids_match` passes;
- `pytest_result_exit_codes_match_command_plan` passes;
- `final_gate_result.json` is not FAILED;
- close-round exits 0;
- round archive for `round_20260616_cpp1_success_reanchor_closeout_rework_v1` exists;
- `local_reverse_cpp1_2f6fcb63_success_target_reanchor` remains current.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain state inputs only and must not override this decision.

Previous round:

- `decision_20260616_cpp1_success_target_reanchor_v1`
- `round_20260616_cpp1_success_target_reanchor_v1`
- mainline: `tool_integration`

Known facts from audit:

- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json` was generated.
- `artifact_index.json` registers `local_reverse_cpp1_2f6fcb63_success_target_reanchor` as `freshness=current`, source_run `round_20260616_cpp1_success_target_reanchor_v1`, sample_id `cpp1_2f6fcb63`.
- The reanchor artifact has `contradiction_resolution=CURRENT_TARGET_PATH_REJECTED`.
- The artifact recommends `TARGET_REANCHOR_NEEDED` and does not mark solved or runtime validated.
- The thin CLI `reverse_agent/local_reverse_cpp1_success_target_reanchor.py` was created and executed successfully.
- `pytest` passed with 559 tests.
- `command-plan` was WARN because command 13 had unknown kind.
- `final-check` failed.
- `close-round` failed with exit 1.
- `codex_execution_report.md` says `PARTIAL / REWORK_REQUIRED`.
- The blocking issue is gate classification, not the reanchor evidence itself.

Historical missing artifacts remain historical external state notices. They must not be treated as current CPP1 evidence. Missing/stale current CPP1 artifacts must still block.

Existing gate problem:

- `project_gate.py` currently uses a finite command-kind classifier.
- New project CLIs under `python -m reverse_agent.<module>` can become `unknown` even when explicitly declared in the decision Tests section.
- A pure one-off mapping would unblock this round, but the same failure will recur for each new thin artifact-builder CLI.

## 3. Do Not Do

Do not rerun `CPP1.exe`.

Do not run debugger, runtime probe, harness campaign, emulator, hook, or console automation.

Do not generate candidate/password/flag.

Do not analyze or solve `samplereverse`.

Do not modify solver logic, harness behavior, runtime runner behavior, IDA runner semantics, debugger integration, `.codex-skills/`, raw samples, training materials, GUI/frontend, or full `solve_reports/`.

Do not downgrade current CPP1 artifacts.

Do not manually patch `final_gate_result.json` to hide failures.

Do not weaken final gate semantics for id matching, pytest result matching, current artifact freshness, forbidden paths, or close-round requirements.

Do not remove historical missing artifact entries just to pass the gate.

## 4. Files To Inspect

Read default state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect:

- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/local_reverse_cpp1_success_target_reanchor.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before changing files, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
3. The reanchor artifact exists and is current in `artifact_index.json`.
4. The prior close-round failed because command-plan did not recognize `reverse_agent.local_reverse_cpp1_success_target_reanchor`.
5. The 50 missing artifacts are historical sample artifacts, not current CPP1 artifacts.
6. The fix is gate command classification only, not a change to solving/evidence semantics.
7. Current artifact freshness remains strict.
8. No runtime/debugger/sample execution is needed.

Required result:

- `command-plan` must be PASSED, not WARN, for the declared reanchor CLI command.
- `final-check` must not be FAILED.
- `close-round` must exit 0 before reporting SUCCESS/ACCEPTED.
- If a generic project CLI fallback is added, tests must prove that it does not authorize undeclared or forbidden runtime/debugger/solver behavior.
- If a one-off mapping is used, report must explain that this is a short-term unblock and recommend replacing repeated one-off mappings with a generic project-cli/artifact-builder policy.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- directly related tests, preferably `tests/test_project_gate.py`

Preferred implementation:

1. Add a generic command classification for declared project CLIs under `python -m reverse_agent.<module>` when the full command is present in the current decision Tests section, classifying safe artifact builders as `project-cli` or `artifact-builder-cli`.
2. Keep sensitive behavior blocked by policy: commands containing or classified as runtime/debugger/harness/sample execution/solver search must still require explicit decision authorization.
3. If generic support is too large for this round, add a narrow mapping for `local_reverse_cpp1_success_target_reanchor` to a stable kind such as `success-target-reanchor`, but do not change broader policy semantics.

Do not change policy semantics except command classification. Current artifact missing/stale must remain blocking. Forbidden paths must remain blocking. Report/decision/pytest/round matching must remain strict.

Allowed state updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260616_cpp1_success_reanchor_closeout_rework_v1/*`

Do not modify:

- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`, except read-only verification;
- `project_state/artifact_index.json`, except if required to preserve existing current registration without changing meaning;
- solver/runtime/debugger/IDA/harness modules;
- `.codex-skills/`.

## 7. Tests

Record command, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

Required commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_success_reanchor_closeout_rework_v1
```

If source changes are made, add or update focused tests for command-kind classification. At minimum, tests should cover:

- the `local_reverse_cpp1_success_target_reanchor` CLI no longer becomes unknown;
- an unknown undeclared `python -m reverse_agent.<module>` command does not silently bypass policy;
- runtime/debugger/harness/sample-execution style commands are not authorized by the generic fallback unless the decision explicitly allows them.

## 8. Stop Conditions

Stop with `REWORK_REQUIRED` if command-plan remains WARN due to unknown kind.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `REWORK_REQUIRED` if report-summary and live report disagree.

Stop with `REWORK_REQUIRED` if final gate remains FAILED.

Stop with `REWORK_REQUIRED` if the fix changes runtime/debugger/solver/harness behavior.

Stop with `REWORK_REQUIRED` if current CPP1 artifacts are downgraded or reinterpreted.

Stop with `BLOCKED` if implementing this requires broad gate policy changes outside command-kind classification.

Do not write SUCCESS or ACCEPTED if final gate or close-round fails.
