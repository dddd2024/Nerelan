```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_fast_profile_command_trimming_pilot_v1",
  "round_id": "round_20260617_fast_profile_command_trimming_pilot_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Pilot limited command trimming for the `fast` gate profile only.

The goal is to make `fast` useful for artifact/report-only or documentation-only rounds by producing a shorter command plan, while preserving full safety for source/test/gate/project_state logic changes.

Required end state:

- implement a small deterministic `fast` profile command-plan trim for artifact/report-only scenarios;
- keep `full` as the default for gate/project_state/source/test logic changes and for ambiguity;
- do not advance `standard` profile in this round except to preserve existing metadata behavior;
- `fast` must never silently bypass preflight, decision immutability, report-summary, final-check, stale artifact, generated-artifact existence, or report-body checks;
- `fast` must not allow close-round/archive unless profile policy and final-check explicitly mark the scenario closeout-safe;
- command-plan JSON must clearly show which commands were omitted because of `fast`, and why;
- final-check must verify that any fast-trimmed command plan is only used for allowed artifact/report-only files and current decision/report/round IDs;
- full-path behavior must remain unchanged and covered by existing tests;
- do not touch solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

This is an engineering-branch gate architecture task. It must not turn into reverse-solving, tool-integration, or training-dataset work.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are advisory inputs only and must not override this decision.

Previous accepted-with-limitations round:

- `decision_20260617_gate_profile_tier_integration_v1`
- `round_20260617_gate_profile_tier_integration_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Known state from the previous audit:

- `fast / standard / full` profile metadata was integrated into `gate-profile` and `command-plan`.
- `gate-profile --json` emitted `profile`, `profile_reason`, `risk_reasons`, `closeout_allowed`, and `required_command_kinds`.
- `command-plan --json` emitted `profile_meta`.
- final-check validated current `gate_profile_plan.json` and profile consistency with `command_plan.json`.
- close-round included `gate_profile_closeout_safety`.
- current gate/profile integration round ran as `full`, which was correct for `project_gate` changes.
- pytest passed with 719 tests.
- final-check and close-round passed.
- Remaining limitations were non-blocking: `run-round --dry-run` showed a failed dry-run status while exit 0; `doctor/lint-report/report-summary/final-check` may show intermediate diagnostic states; fast/standard had not yet become true reduced command paths.

Meaning:

- The profile metadata and safety checks exist.
- The next step should be a narrow `fast` pilot only.
- `standard` should not be expanded in this round.
- Closeout safety must remain conservative.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
- startup/baseline consistency check;
- stale artifact ID check;
- current-report gate regeneration behavior;
- command-plan expected-exit semantics;
- conditional close-round behavior;
- report-body consistency check;
- gate-profile metadata and consistency checks;
- `gate_profile_closeout_safety` check;
- preflight-failure handoff check;
- `decision_immutability` FAIL behavior;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` mismatch detection;
- generated-artifact live-path existence behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this fast-profile pilot.
- This round does not depend on reverse sample artifacts.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat old `samplereverse` failed candidate/runtime branches.

Existing tool capability boundary:

- This round is not reverse-solving.
- This round does not require IDA/Ghidra/debugger/solver/harness execution.
- Mature reverse tools must not be modified or reimplemented.

Allowed execution:

- Read repository source/tests and compact `project_state/` metadata.
- Run only the gate/status/test commands listed in the Tests section.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not implement or expand `standard` command trimming in this round.

Do not let `fast` silently replace `full` for source/test/gate/project_state logic changes.

Do not allow `fast` to close/archive unless the profile policy and final-check explicitly mark it closeout-safe for artifact/report-only scope.

Do not weaken final-check, close-round, preflight, decision immutability, startup/baseline, stale artifact, generated-artifact, command-plan, report-body, or profile consistency checks.

Do not globally allow reduced checks for all rounds.

Do not implement LLM-based profile selection.

Do not add another independent gate engine.

Do not rewrite command-plan, final-check, or close-round from scratch.

Do not expand this into frontend, GUI, solver, harness, sample runner, reverse tools, IDA/Ghidra/debugger, or training dataset work.

Do not run sample binaries.

Do not run IDA/Ghidra/debugger/harness/solver/runtime probe commands.

Do not modify `.codex-skills/`.

Do not add a database, queue, Kubernetes, workflow engine, or new external service.

Do not treat `task_packet.task` as current execution authority.

Do not modify live `project_state/decision_packet.md` during execution to add a late allowlist or change the active task.

Do not use this fast-profile pilot to bypass close-round failures.

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

Also inspect:

- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if command-plan/report validation plumbing strictly requires it
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed
- current Git changed filenames / diff summary

Do not inspect unrelated solver/harness/tool-runner modules unless a failing test directly requires it.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. If startup `git status --short` is clean, later source/test dirty files must be treated as this-round changes, not inherited baseline dirty.
4. If startup `git status --short` already shows source/test dirty files, stop immediately and write `codex_execution_report.md` with `status=BLOCKED` or `status=FAILED` and `acceptance_recommendation=REWORK_REQUIRED`; do not implement changes.
5. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write a BLOCKED report; do not implement changes.
6. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
7. Current decision controls execution; `task_packet.json` is not authoritative.
8. Confirm existing profile metadata and closeout safety behavior before changing command trimming.
9. Confirm existing command-plan expected-exit behavior remains intact.
10. Confirm no mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if command-plan/report validation plumbing strictly requires it

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed

Allowed project-state/report files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260617_fast_profile_command_trimming_pilot_v1/*`

Required fast profile pilot behavior:

- Define a minimal `fast` command set for artifact/report-only rounds.
- The fast command set must include at least startup/status checks, preflight, gate-profile, command-plan, report-summary, final-check, and any required artifact/currentness checks.
- The fast command set may omit pytest and heavy close-round only when no source/test logic files are changed and the profile is not closeout-safe.
- If closeout is required, full path remains required unless fast is explicitly proven closeout-safe by policy and final-check.
- `command-plan --json` must include `omitted_commands` or equivalent metadata listing commands skipped due to `fast`, including reasons.
- `command-plan --json` must include `profile_meta.profile=fast` when fast is selected.
- `final-check` must validate that fast trimming is only used when dirty files and files_changed are limited to allowed artifact/report/documentation/project_state cleanup paths.
- `final-check` must fail if fast omits pytest while source/test logic files are changed.
- `final-check` must fail if fast omits close-round but report claims archived/accepted closeout.
- `final-check` must fail if fast attempts close-round with `closeout_allowed=false`.
- `full` command-plan output must remain unchanged except for backward-compatible metadata fields.
- Do not change `standard` behavior except preserving metadata compatibility.
- Preserve command-plan expected-exit semantics from prior rounds.
- Preserve report-body consistency behavior.
- Preserve startup/baseline consistency behavior.
- Preserve stale artifact ID behavior.
- Preserve generated-artifact live-path existence behavior.
- Preserve report-prose claimed source/test coverage behavior.
- Preserve `tmp*/` dirty-state check behavior.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. fast profile for artifact/report-only scope omits pytest and records the omission with reason.
2. fast profile includes startup, preflight, gate-profile, command-plan, report-summary, and final-check command kinds.
3. fast profile does not include close-round when `closeout_allowed=false`.
4. fast profile cannot claim archived/accepted closeout when close-round was omitted.
5. fast profile fails final-check if source/test logic files are present in round delta.
6. fast profile fails final-check if pytest is omitted while source/test logic files changed.
7. fast profile fails final-check if close-round is attempted while `closeout_allowed=false`.
8. fast profile command-plan includes omitted command metadata and reasons.
9. full profile command-plan remains compatible with existing full tests.
10. standard profile behavior remains unchanged except metadata compatibility.
11. stale or mismatched gate_profile_plan/command_plan profile metadata still fails final-check.
12. existing command-plan expected-exit tests continue to pass.
13. existing report-body consistency tests continue to pass.
14. existing startup/baseline consistency tests continue to pass.
15. existing stale artifact ID tests continue to pass.
16. existing generated-artifact live-path tests continue to pass.
17. existing tmp-path dirty-state tests continue to pass.
18. existing preflight handoff and decision immutability tests continue to pass.

## 7. Tests

Run and record the following commands in `project_state/pytest_result.txt`:

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_fast_profile_command_trimming_pilot_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_fast_profile_command_trimming_pilot_v1`
- `round_id=round_20260617_fast_profile_command_trimming_pilot_v1`
- the final `report_id`
- all commands actually run

If preflight fails due to actual startup source/test dirty, Codex must stop after recording startup/preflight evidence and write a BLOCKED/REWORK report instead of running the remaining commands.

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files before implementation begins;
- startup `git status --short` already shows live `project_state/decision_packet.md` dirty;
- temporary paths such as `tmp*/` cannot be safely removed or explained;
- implementing this requires replacing the existing gate system;
- implementing this requires changing solver/harness/tool-runner/debugger/sample code;
- fast trimming cannot be expressed with a small deterministic rule table;
- close-round safety would need to be weakened to make fast pass;
- tests fail for reasons outside the narrow fast-profile command trimming pilot scope.
