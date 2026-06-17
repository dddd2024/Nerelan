```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_tiered_gate_profile_plan_v1",
  "round_id": "round_20260617_tiered_gate_profile_plan_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Create the first small, testable engineering step toward a tiered gate system so lightweight artifact-only rounds do not always pay the cost of the full closeout gate pipeline.

This round must not redesign the whole gate system. It should define and implement a read-only gate profile classification layer that can classify a round as `fast`, `standard`, or `full`, explain the selected profile, and expose the recommended command set without changing existing `close-round` enforcement behavior yet.

Required end state:

- introduce a minimal gate profile classifier for `fast`, `standard`, and `full` modes;
- add a CLI/report output that shows the recommended gate profile and command set for the current decision;
- keep existing `preflight`, `command-plan`, `run-round`, `report-summary`, `final-check`, and `close-round` behavior backward-compatible;
- add tests for artifact-only, normal source/test, and gate/project_state/tooling changes;
- do not reduce current safety checks in this round;
- do not run samples, IDA, Ghidra, debugger, harness, runtime probes, or solvers.

The practical motivation is the recent observation that artifact-only/planning rounds spend disproportionate time in gate checks. The target design is:

- `fast`: artifact-only / planning artifacts / resume plan / coverage matrix; expected gate budget 1-3 minutes;
- `standard`: ordinary bounded source/test changes; expected gate budget 3-6 minutes;
- `full`: gate/project_state/harness/solver/tool-runner changes or major closeout; expected gate budget 8-15 minutes.

This round only builds the classification and reporting foundation. It must not immediately switch production closeout to fast mode.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` remain state inputs only and must not override this decision.

Previous accepted-with-limitations round:

- `decision_20260617_artifact_deliverable_reporting_rework_v1`
- `round_20260617_artifact_deliverable_reporting_rework_v1`
- mainline: `engineering_branch`
- result: core artifact-deliverable reporting fix accepted with limitations
- limitation: source/test files were dirty before baseline capture; final gate passed but retained inherited source/test baseline warnings.

Relevant current facts:

- Current gate pipeline is safe but too heavy for artifact-only rounds.
- Existing command-plan currently emits a full fixed command chain for most rounds.
- `project_gate.py` owns command-plan, preflight, run-round, report-summary, final-check, close-round, round baseline/delta, and report summary synthesis.
- `project_state.py` owns doctor, lint-report, report parsing, pytest result validation, artifact freshness, and state package checks.
- The active skill registry contains `reverse-agent-iteration@v2`, and no new skill should be added.

Reason for not continuing training-dataset immediately:

- The recent bottleneck is not solver capability; it is gate overhead and closeout ergonomics.
- A tiered gate profile foundation should reduce future artifact-only training rounds without weakening safety globally.

Existing relevant capabilities to reuse:

- command classification: `_command_kind`, `_command_phase`, command-plan extraction;
- preflight validation: decision meta, mainline, skill profiles, task_packet non-authority, implementation scope, artifact freshness policy;
- report-summary synthesis and final-check checks;
- round delta/baseline tracking;
- pytest result command coverage checks.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this engineering round.
- This round does not depend on reverse sample artifacts.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat old `samplereverse` failed candidate/runtime branches.

Allowed tool execution:

- Read repository source/tests and compact `project_state/` metadata.
- Run gate/status/test commands listed in the Tests section.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not remove or weaken current `close-round` checks.

Do not make `fast` mode the default production closeout path in this round.

Do not skip `final-check` or `report-summary` in existing commands.

Do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, runtime probe, GUI/frontend, sample runner, raw sample, or `.codex-skills/` files.

Do not run sample binaries.

Do not run IDA/Ghidra/debugger/harness/solver/runtime probe commands.

Do not change training sample statuses.

Do not add a database, queue system, workflow engine, or new external dependency.

Do not treat `task_packet.task` as current execution authority.

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

- `project_state/gates/command_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Do not inspect unrelated solver/harness/tool-runner modules unless a failing test directly requires it.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded as baseline.
3. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
4. Current decision controls execution; `task_packet.json` is not authoritative.
5. Existing gate/report-summary/final-check/close-round behavior is understood before changing code.
6. The current round is an engineering gate ergonomics step, not a reverse-solving or training-data sample step.
7. No mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if existing report/status plumbing strictly requires it

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/*`

Required implementation behavior:

- Add a small gate profile classifier with exactly three profile names: `fast`, `standard`, `full`.
- Classify `fast` when the decision scope is artifact-only / project_state planning artifacts and no source/test/tooling files are allowed to change.
- Classify `standard` when the decision allows ordinary bounded source/test changes outside core gate/project_state/harness/solver/tool-runner modules.
- Classify `full` when the decision allows changes to any of:
  - `reverse_agent/project_gate.py`
  - `reverse_agent/project_state.py`
  - harness modules
  - solver modules
  - tool runners
  - IDA/Ghidra/debugger integration
  - runtime probe code
  - `.codex-skills/`
- Include a reason list explaining why the profile was selected.
- Expose the result through a read-only command, preferably under `python -m reverse_agent.project_gate gate-profile --state-dir project_state --json`, or an equivalent minimal CLI if this is easier to integrate safely.
- Write optional JSON output to `project_state/gates/gate_profile_plan.json` when the command is invoked without breaking existing command-plan behavior.
- Do not make command-plan use the reduced profile yet; it may display the selected profile as metadata or advisory text only.
- Preserve backward compatibility for existing command-plan/final-check/close-round tests.

Suggested command sets for reporting only:

- `fast` suggested commands:
  - startup path checks
  - `preflight`
  - schema/artifact validation for touched project_state files
  - focused pytest only if tests are changed
  - `report-summary`
  - `final-check-lite` placeholder or existing `final-check` advisory until lite exists
- `standard` suggested commands:
  - startup path checks
  - `preflight`
  - `command-plan`
  - focused pytest for touched modules
  - `doctor`
  - `lint-report`
  - `report-summary`
  - `final-check`
- `full` suggested commands:
  - current full command-plan behavior including close-round
  - relevant full gate/project_state tests
  - report-summary/final-check/close-round

If `final-check-lite` does not exist, do not implement it in this round. Record it as a future phase in the profile output.

Required tests:

1. Artifact-only decision with only `project_state/*.json` / `.md` generated artifacts classifies as `fast`.
2. Ordinary bounded source/test decision classifies as `standard`.
3. Gate/project_state change classifies as `full`.
4. Harness/solver/tool-runner/debugger/IDA/Ghidra/runtime-probe paths classify as `full`.
5. `.codex-skills/` paths classify as `full` or are rejected according to existing rules.
6. The CLI emits JSON with `profile`, `reasons`, and `suggested_commands`.
7. Existing command-plan/final-check/close-round tests continue to pass.

## 7. Tests

Run and record the following commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_tiered_gate_profile_plan_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_tiered_gate_profile_plan_v1`
- `round_id=round_20260617_tiered_gate_profile_plan_v1`
- the final `report_id`
- all commands actually run

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- implementing this requires rewriting close-round or changing enforcement semantics;
- the change would reduce current safety checks in production rather than only classify/report the recommended tier;
- the change requires modifying solver/harness/tool-runner/debugger/sample code;
- tests fail for reasons outside the narrow gate-profile classification scope;
- adding the CLI would require a broad CLI refactor rather than a small subcommand addition.
