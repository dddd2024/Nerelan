```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_staged_state_rebuild_workflow_v1",
  "round_id": "round_20260619_staged_state_rebuild_workflow_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Implement a staged state rebuild workflow so the proposed next compact state can be materialized and reviewed without mutating the live `project_state` used by the active decision.

The previous accepted round added `project_state rebuild-preview`, which computes proposed `state_build_id` / `state_digest` in memory and writes `project_state/state_rebuild_handoff.json`. That handoff now says `live_files_would_change=true` and recommends running `python -m reverse_agent.project_state build` before generating the next decision. Running live `build` inside a normal approved decision would still invalidate the decision/state digest relation. This round must close the next workflow gap by adding a safe staged-output path.

This is an engineering workflow round. Do not run live `project_state build` against `project_state` as part of this decision. Do not solve any reverse sample.

Success criteria:

1. Add a non-mutating staged rebuild command or option that writes proposed state files to a separate staging directory, not to live `project_state`.
2. The staged output must include proposed `artifact_index.json`, `current_state.json`, `negative_results.json`, `model_gate.json`, and `task_packet.json`, with their proposed `state_build_id` / `state_digest`.
3. The workflow must produce an apply-plan artifact explaining how an operator should promote staged files only before generating a new decision.
4. `decision-lint` must remain strict for the live state and must not allow arbitrary digest mismatches.
5. Tests must prove staged rebuild does not mutate live `project_state` files.

## 2. Current Evidence

The current accepted state-rebuild preview round is `decision_20260619_state_build_decision_sync_workflow_v1`.

It established:

- `rebuild-preview` exists and is non-mutating.
- `state_rebuild_handoff.json` is generated.
- `live_files_mutated=false`.
- `live_files_would_change=true`.
- Live state is still `state_20260618_134029_d6bd033d2532` / `d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5`.
- Proposed state is `state_20260619_140730_d8f93e18db4b` / `d8f93e18db4b09c062c0086f6cc8a2d722184a0a0de11a1484cf854d3e4035e5`.
- Recommended next action is to run `python -m reverse_agent.project_state build` before generating the next decision.

Remaining workflow limitation:

- `rebuild-preview` reports the proposed id/digest, but does not materialize the full proposed state files for review.
- Live `task_packet.json` and `current_state.json` still point to old `samplereverse` state.
- Directly running live `project_state build` under this already-approved decision would make the live decision stale.
- A safe staged state package would let GPT/Codex review proposed state outputs before any live promotion.

`task_packet.json` remains advisory only. This `decision_packet.md` controls the current round.

Negative-results still apply:

- Do not return to old sample_solver blind search.
- Do not only increase beam/budget.
- Do not use compare_semantics_agree=false candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat current 5-candidate transform-trace audit without new runtime evidence.

Existing related capabilities to inspect first:

- `reverse_agent.project_state build_project_state()` writes live state files.
- `reverse_agent.project_state rebuild_preview()` computes proposed state in memory and writes handoff only.
- `reverse_agent.project_state pack` packs context but does not produce proposed state files.
- Gate policy already treats `decision_packet.md` as execution authority and `task_packet.json` as advisory.

## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build` against `project_state` in this round.

Do not mutate live `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/model_gate.json`, or `project_state/negative_results.json` unless this decision is explicitly revised later.

Do not continue affine solving.

Do not resume `samplereverse` candidate search.

Do not run target binaries, runtime probes, debuggers, emulators, hooks, or dynamic validation.

Do not read complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

Do not create fake historical artifacts or placeholder runtime outputs.

Do not weaken `decision-lint` by allowing arbitrary state digest mismatches.

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

State rebuild handoff:

1. `project_state/state_rebuild_handoff.json`

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

1. `project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/round_manifest.json`
2. `project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/codex_execution_report.md`
3. `project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/pytest_result.txt`

## 5. Required Audit

Before implementation, answer:

1. Does `rebuild_preview()` already compute all proposed state payloads before discarding them?
2. Can proposed state payloads be written to a separate staging directory without reusing live output paths?
3. Which fields in staged files must match the proposed `state_build_id` and `state_digest`?
4. What path should hold staged output so it is clearly not live execution state?
5. How should the apply-plan explain promotion order: stage -> review -> live build/promote -> generate new decision?
6. Can the implementation reuse `build_project_state()` logic without duplicating mature state-building code?
7. Does the implementation preserve live decision immutability and live state digest matching during this round?
8. Does it preserve strict stale/missing evidence checks for current evidence claims?

## 6. Implementation Scope

Preferred implementation is a small extension of the existing rebuild-preview workflow.

Acceptable approaches:

1. Add a new CLI subcommand, for example:
   - `python -m reverse_agent.project_state rebuild-stage --state-dir project_state --out-dir project_state/proposed_state`
2. Or add an option to existing preview, for example:
   - `python -m reverse_agent.project_state rebuild-preview --write-staged --out-dir project_state/proposed_state`

Required behavior:

- It must compute the proposed state using existing build logic.
- It must write proposed state files only under the staging directory.
- It must not overwrite live files under `project_state/` root.
- It must write an apply-plan artifact, for example `project_state/state_rebuild_apply_plan.json`, containing:
  - live state id/digest;
  - proposed state id/digest;
  - staging directory path;
  - list of proposed files;
  - whether live files were mutated;
  - exact safe promotion sequence;
  - warning that a new decision must be generated after live promotion;
  - warning that normal Codex execution must not promote state under an already-approved decision.

Allowed source/test changes:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `reverse_agent/project_gate.py` only if command-plan/final-check coverage needs a small corresponding update
- `tests/test_project_gate.py` only if `project_gate.py` is touched

Allowed project_state outputs:

- `project_state/state_rebuild_apply_plan.json`
- `project_state/state_rebuild_handoff.json` if regenerated by the command
- `project_state/proposed_state/artifact_index.json`
- `project_state/proposed_state/current_state.json`
- `project_state/proposed_state/negative_results.json`
- `project_state/proposed_state/model_gate.json`
- `project_state/proposed_state/task_packet.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_staged_state_rebuild_workflow_v1/*`

Do not update live compact state files in `project_state/` root in this round.

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

1. staged rebuild writes proposed files only under the staging directory;
2. staged rebuild does not mutate live `current_state.json`, `task_packet.json`, `artifact_index.json`, `model_gate.json`, or `negative_results.json`;
3. staged files contain internally consistent proposed `state_build_id` and `state_digest`;
4. apply-plan contains the staging path and promotion sequence;
5. CLI command returns exit 0;
6. `decision-lint` still fails on real live decision/state mismatch;
7. reverse-solving candidate/solution gate behavior is unchanged.

If final-check passes, run close-round when gate-profile says closeout is allowed:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_staged_state_rebuild_workflow_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. repository root cannot be confirmed;
2. decision metadata is invalid;
3. mainline is not `engineering_branch`;
4. skill profile is not active;
5. the implementation requires reading complete `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
6. the implementation requires fake historical artifacts;
7. the implementation weakens decision-lint by allowing arbitrary digest mismatch;
8. the implementation mutates live state root files and leaves `decision-lint` broken;
9. implementation changes solver logic;
10. implementation weakens reverse-solving candidate/solution gates;
11. source changes exceed allowed project-state/gate files;
12. pytest fails;
13. final-check has any FAIL;
14. report/decision/pytest/final-gate IDs mismatch;
15. report claims affine or samplereverse solving progress.
