```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_fast_non_closeout_semantics_source_fix_v1",
  "round_id": "round_20260617_fast_non_closeout_semantics_source_fix_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Fix fast-profile non-closeout semantics in source code.

The prior artifact-only rework correctly diagnosed that the current gate/report system cannot cleanly represent `profile=fast`, `closeout_allowed=false`, no close-round command, and no normal archive. This round may modify only the gate implementation and its tests to make that state first-class and auditable.

Required end state:

- `command-plan --json` for `profile=fast` and `closeout_allowed=false` must explicitly record close-round as omitted, even when close-round was not present in the decision Tests section;
- `omitted_commands` must include a close-round omission entry with a reason such as `omitted by fast profile: closeout not allowed`;
- `fast_profile_closeout_consistency` must no longer PASS with `close_round_omitted=false` while `closeout_allowed=false` and no close-round command exists;
- final-check must treat absence of close-round under `closeout_allowed=false` as a recognized fast non-closeout state, not as normal archive success;
- `report_summary_synthesis` and final-check expected file sets must not require normal round archive files for fast non-closeout rounds;
- if fast non-closeout report status is intended to be a successful validation without archive, report/final gate must expose that as non-archived/non-closeout success rather than pretending close-round ran;
- full close-round behavior must remain unchanged;
- standard profile behavior must remain unchanged;
- no solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw sample, or `.codex-skills/` behavior may be changed.

This is an engineering-branch gate semantics task. It must not turn into reverse-solving, tool-integration, or training-dataset work.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are advisory inputs only and must not override this decision.

Previous accepted-with-limitations diagnostic round:

- `decision_20260617_fast_artifact_only_validation_rework_v1`
- `round_20260617_fast_artifact_only_validation_rework_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Evidence from the diagnostic round:

- It did not modify `reverse_agent/*.py` or `tests/*.py`.
- It did not run pytest.
- It did not run close-round.
- Startup was clean and preflight passed.
- `gate-profile` auto-selected `profile=fast`.
- `closeout_allowed=false`.
- `command-plan` omitted pytest and recorded pytest in `omitted_commands`.
- `command-plan` still did not record close-round in `omitted_commands` because close-round was absent from the decision Tests section.
- `final-check` still reported `fast_profile_closeout_consistency` as PASS with `close_round_omitted=false`, `closeout_allowed=false`.
- `report_summary_synthesis` and final-check still expected normal archive paths for a fast non-closeout round.
- The diagnostic report correctly used `status=PARTIAL` and `acceptance_recommendation=REWORK_REQUIRED`.

Meaning:

- Fast classifier and no-source/no-test evidence are already proven.
- The remaining issue is source-level gate/report semantics.
- This round must be a small source fix with tests.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
- startup/baseline consistency check;
- stale artifact ID check;
- current-report gate regeneration behavior;
- command-plan expected-exit semantics;
- report-body consistency check;
- gate-profile metadata and consistency checks;
- `gate_profile_closeout_safety` check;
- fast profile scope checks;
- fast pytest omitted-command metadata;
- preflight-failure handoff check;
- `decision_immutability` FAIL behavior;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` mismatch detection;
- generated-artifact live-path existence behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check;
- full-profile close-round and archive behavior.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this source fix.
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

## 3. Do Not Do

Do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` files.

Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Do not expand `standard` behavior.

Do not weaken full-profile close-round or archive validation.

Do not make fast closeout run close-round when `closeout_allowed=false`.

Do not treat missing archive files as globally non-blocking; only fast non-closeout rounds may avoid normal archive requirements.

Do not mark fast non-closeout as archived.

Do not rewrite command-plan, final-check, close-round, or report-summary from scratch.

Do not add another independent gate engine.

Do not treat `task_packet.task` as current execution authority.

Do not modify live `project_state/decision_packet.md` during execution to add a late allowlist or change the active task.

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
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if a project-state test is strictly required
- current Git changed filenames / diff summary

Do not inspect unrelated solver/harness/tool-runner modules unless a gate command directly reports them as a blocking forbidden path.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. If startup `git status --short` is clean, later source/test dirty files are this-round changes, not inherited baseline dirty.
4. If startup `git status --short` already shows source/test dirty files, stop unless they are explicitly the current decision's allowed files and are documented as baseline dirty; otherwise write BLOCKED/REWORK report.
5. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write a BLOCKED report; do not continue.
6. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
7. Current decision controls execution; `task_packet.json` is not authoritative.
8. Confirm existing fast profile auto-selection and closeout_allowed=false behavior before changing code.
9. Confirm no mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if strictly required by a project-state support change; prefer not to modify it.

Allowed project-state/report files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json` only if produced by an allowed command and not used to fake normal archive success
- `project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/*` only if final-check proves close-round is allowed; otherwise do not create a normal archive

Required implementation details:

- Update command-plan generation so fast non-closeout plans include an explicit omitted close-round entry even when close-round was absent from the decision Tests section.
- The omitted entry must include at least command/kind/reason fields.
- Update `fast_profile_closeout_consistency` to compute close-round absence from both `commands` and `omitted_commands`.
- If `profile=fast` and `closeout_allowed=false` and no close-round command exists, the check should recognize this as an intentional fast non-closeout state, not `close_round_omitted=false`.
- If a report claims archive/closeout success under fast non-closeout, final-check must fail.
- Update report-summary/final-check expected archive behavior so fast non-closeout rounds do not require normal archive files.
- Preserve normal archive requirements for full profile and any profile with `closeout_allowed=true`.
- Preserve all existing full-path tests.
- Add focused tests for fast non-closeout semantics; do not do broad test rewrites.

Required tests:

1. fast command-plan with `closeout_allowed=false` includes close-round in `omitted_commands` even if close-round is not in decision Tests.
2. omitted close-round entry has a clear reason: closeout not allowed under fast profile.
3. `fast_profile_closeout_consistency` recognizes close-round absent from commands and present in omitted_commands as intentional non-closeout.
4. `fast_profile_closeout_consistency` fails if fast report claims archived/closeout success while `closeout_allowed=false`.
5. report-summary synthesis does not require normal round archive files for fast non-closeout.
6. final-check does not require normal archive files for fast non-closeout.
7. full profile still requires normal archive files as before.
8. command-plan expected-exit semantics still pass.
9. report-body consistency tests still pass.
10. startup/baseline consistency tests still pass.
11. stale artifact ID tests still pass.
12. generated-artifact live-path tests still pass.
13. tmp-path dirty-state tests still pass.
14. preflight handoff and decision immutability tests still pass.

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
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Do not run close-round unless final-check explicitly proves close-round is allowed for the current profile. Expected behavior for fast non-closeout is no normal close-round archive.

The pytest_result header must include:

- `decision_id=decision_20260617_fast_non_closeout_semantics_source_fix_v1`
- `round_id=round_20260617_fast_non_closeout_semantics_source_fix_v1`
- the final `report_id`
- all commands actually run
- explicit notation whether close-round was intentionally omitted due to fast non-closeout

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- implementation requires modifying files outside the allowed source/test scope;
- implementation requires changing solver/harness/tool-runner/debugger/sample code;
- fast non-closeout cannot be represented without weakening full close-round safety;
- final-check cannot distinguish fast non-closeout from normal archived closeout;
- tests fail for reasons outside the narrow fast non-closeout semantics scope.
