```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_state_build_decision_sync_workflow_v1",
  "round_id": "round_20260619_state_build_decision_sync_workflow_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Define and implement a safe state rebuild workflow that does not break `decision_packet.md` / `current_state.json` consistency.

The previous hygiene round established that `python -m reverse_agent.project_state build` exists, but running it during an already-approved decision changes `state_build_id` / `state_digest` and causes `decision-lint` to fail because the live decision was based on the old state. This round must close that workflow gap.

This is an engineering workflow round. The goal is not to solve any reverse sample. The goal is to make state rebuilds auditable and usable without forcing Codex or GPT into an invalid state.

Success criteria:

1. Identify the exact state rebuild / digest / decision-lint interaction.
2. Implement a bounded workflow improvement, preferably a dry-run or proposed-state handoff path, so a state rebuild can be prepared without mutating the live execution state under an already-approved decision.
3. Produce clear operator guidance for the canonical sequence: build state, then generate decision against that state, then execute decision.
4. Preserve `decision_packet.md` as the execution authority during Codex execution.
5. Preserve strict gate behavior for stale/missing artifacts and reverse-solving candidate/solution claims.

## 2. Current Evidence

The prior accepted round was `decision_20260619_project_state_hygiene_rebuild_v1` with conclusion `ACCEPTED_WITH_LIMITATIONS`.

What it established:

- `doctor`, `decision-lint`, `preflight`, pytest, `gate-profile`, `command-plan`, `report-summary`, and `final-check` all passed.
- The round was archived successfully.
- `status_policy_valid` passed and historical/backlog missing artifacts were classified as non-blocking external state notices for engineering hygiene.
- No source files were modified in that hygiene round.

Remaining workflow limitation:

- `task_packet.json` still points to old `samplereverse` state.
- `current_state.json` still points to old `samplereverse` state.
- `artifact_index.json` still contains about 50 historical/backlog missing artifacts.
- Running `python -m reverse_agent.project_state build` inside an already-approved decision changes `state_build_id` / `state_digest`, causing the current decision's `based_on_state_build_id` / `based_on_state_digest` to mismatch.
- Therefore the system lacks a clean, explicit pre-decision state rebuild workflow or proposed-state handoff artifact.

Important semantic rule:

- The current `task_packet.json` remains advisory only.
- This `decision_packet.md` controls the current round.
- Do not use the old `samplereverse` task as execution authority.

Negative-results still apply:

- Do not return to old sample_solver blind search.
- Do not only increase beam/budget.
- Do not use compare_semantics_agree=false candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat the current 5-candidate transform-trace audit without new runtime evidence.

Existing relevant capabilities to check before changing code:

- `reverse_agent.project_state` build/doctor/lint/status-summary logic.
- `reverse_agent.project_gate` decision-lint/preflight/final-check/command-plan logic.
- Existing state package classification for authoritative/advisory/derived_cache/archive/heavy_history.
- Existing round archive and gate-profile behavior.

## 3. Do Not Do

Do not continue affine solving.

Do not resume `samplereverse` candidate search.

Do not run target binaries, runtime probes, debuggers, emulators, hooks, or dynamic validation.

Do not read complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

Do not create fake historical artifacts or placeholder runtime outputs.

Do not weaken decision-lint by allowing arbitrary state digest mismatches.

Do not let Codex modify the live `decision_packet.md` as part of execution.

Do not weaken reverse-solving candidate/solution validation.

Do not change solver logic.

Do not modify `.codex-skills/`.

## 4. Files To Inspect

Default context:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

State/gate implementation:

1. `reverse_agent/project_state.py`
2. `reverse_agent/project_gate.py`
3. `tests/test_project_state.py`
4. `tests/test_project_gate.py`

Gate/status artifacts:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/preflight_result.json`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/round_delta_summary.json`
6. `project_state/gates/gate_profile_plan.json`

Archive reference:

1. `project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/round_manifest.json`
2. `project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/codex_execution_report.md`
3. `project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/pytest_result.txt`

## 5. Required Audit

Before implementation, answer:

1. Where is `state_digest` computed and which fields are excluded from digest calculation?
2. Which command mutates `current_state.json`, `task_packet.json`, and `artifact_index.json`?
3. Why does running `project_state build` after a decision is approved break `decision-lint`?
4. Is there already a dry-run, output-dir, or preview mode for state build?
5. Is there already a state package / context pack command that can produce a proposed state without mutating live `project_state`?
6. Can the workflow be fixed with documentation/reporting only, or does it require a small CLI improvement?
7. Does the proposed fix preserve decision immutability during Codex execution?
8. Does the proposed fix preserve strict checks for actual stale/missing evidence used as current evidence?

## 6. Implementation Scope

Preferred implementation is small and workflow-oriented.

Acceptable fixes, in priority order:

1. Add or improve a non-mutating state rebuild preview path, for example a dry-run/proposed-state artifact, that computes the would-be `state_build_id` and `state_digest` without overwriting live `current_state.json` / `task_packet.json` under the current decision.
2. Add an explicit state-rebuild handoff artifact, for example `project_state/state_rebuild_handoff.json`, containing:
   - current live state id/digest;
   - proposed next state id/digest;
   - whether live files were mutated;
   - recommended next GPT action;
   - exact command that should be run before generating the next decision.
3. Improve `doctor` / `decision-lint` messaging so it distinguishes:
   - invalid decision/state mismatch;
   - expected pre-decision rebuild mismatch;
   - unsafe live mutation during decision execution.
4. If no code change is needed, produce a precise blocker or operator guide artifact explaining the safe sequence and why no implementation change is appropriate.

Allowed source/test changes:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`

Allowed project_state outputs:

- `project_state/state_rebuild_handoff.json`
- `project_state/state_rebuild_handoff.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/*`

Do not update live `current_state.json`, `task_packet.json`, or `artifact_index.json` unless the implementation explicitly proves that doing so is safe under the current decision and `decision-lint` remains valid. The safer default is to generate a proposed-state handoff artifact, not to mutate live state.

## 7. Tests

Run and record all commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If a new CLI option/subcommand is added, add focused tests covering:

1. preview/dry-run does not mutate live `current_state.json`, `task_packet.json`, or `artifact_index.json`;
2. preview output contains proposed `state_build_id` and `state_digest`;
3. decision-lint still fails on real live decision/state mismatch;
4. doctor or handoff messaging gives the correct next action;
5. reverse-solving candidate/solution gate behavior is unchanged.

If final-check passes, run close-round when gate-profile says closeout is allowed:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_state_build_decision_sync_workflow_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. repository root cannot be confirmed;
2. decision metadata is invalid;
3. mainline is not `engineering_branch`;
4. skill profile is not active;
5. the proposed fix requires reading complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
6. the proposed fix requires fake historical artifacts;
7. the proposed fix weakens decision-lint by allowing arbitrary digest mismatch;
8. the proposed fix mutates live state and leaves `decision-lint` broken;
9. implementation changes solver logic;
10. implementation weakens reverse-solving candidate/solution gates;
11. source changes exceed allowed project-state/gate files;
12. pytest fails;
13. final-check has any FAIL;
14. report/decision/pytest/final-gate IDs mismatch;
15. report claims affine or samplereverse solving progress.
