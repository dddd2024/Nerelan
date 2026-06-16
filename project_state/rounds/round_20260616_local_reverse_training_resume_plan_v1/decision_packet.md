```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_local_reverse_training_resume_plan_v1",
  "round_id": "round_20260616_local_reverse_training_resume_plan_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Resume the existing `local_reverse` training dataset workflow from current queue/status artifacts.

This is a `training_dataset` planning and state-recovery round. Do not rebuild the local sample inventory from scratch. Do not solve samples in this round. Do not run local reverse samples. Do not run runtime probes, debuggers, emulators, hooks, or IDA/Ghidra batch extraction unless an existing status artifact explicitly proves the required metadata is missing and this decision is revised.

Required end state:

- existing `local_reverse` inventory, queue, next-queue, status summary, per-sample status, and existing static-triage artifacts are audited rather than recreated;
- a current training execution view is produced from the existing artifacts;
- a type coverage matrix is produced for the currently known local reverse samples;
- the next bounded training targets are selected per reverse-engineering category using current queue/status evidence;
- no sample is solved in this round;
- no solver, sample runner, IDA/debugger/emulator/harness, GUI/frontend, raw sample, `.codex-skills/`, or full `solve_reports/` files are modified;
- `project_state/codex_execution_report.md` and `project_state/pytest_result.txt` are updated with real commands and results;
- `report-summary`, `final-check`, and `close-round` pass and archive `round_20260616_local_reverse_training_resume_plan_v1`.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

The previous engineering clean-baseline round is accepted:

- `decision_20260616_clean_baseline_after_git_fetch_rework_v1`
- `round_20260616_clean_baseline_after_git_fetch_rework_v1`
- audit conclusion: `ACCEPTED`
- clean source/test baseline was proven; final gate status was `PASSED`; no source/test dirty baseline remained.

Training work already exists in the repository. Do not repeat it as if starting from zero. Known existing training-related artifacts and code include:

- `project_state/rounds/round_20260611_refresh_training_inventory_and_queue_v1/decision_packet.md`
- `project_state/rounds/round_20260611_refresh_training_inventory_and_queue_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_training_metadata_contract_repair_v1/decision_packet.md`
- `project_state/rounds/round_20260612_training_metadata_contract_repair_v1/pytest_result.txt`
- `project_state/rounds/round_20260612_training_local_reverse_inventory_audit_v1/decision_packet.md`
- `project_state/rounds/round_20260612_training_local_reverse_inventory_audit_v1/codex_execution_report.md`
- `project_state/local_reverse_training_inventory_audit.md`
- `reverse_agent/local_reverse_training_review.py`
- `reverse_agent/local_reverse_training_status.py`
- `project_state/local_reverse_training_review_queue.json`
- `training_materials/local_reverse/queue.json`
- `project_state/local_reverse_training_next_queue.json`
- `project_state/local_reverse_training_status_summary_sync.json`
- `training_materials/local_reverse/github_safe_status_overlay.json`
- per-sample status or static-triage artifacts such as `project_state/local_reverse_cpp2_32f1713e_training_status_sync.json`, `project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json`, and `project_state/local_reverse_cpp2_32f1713e_static_triage.json`.

`task_packet.json` currently still reflects the old `samplereverse` derived task and is not the current execution authority. `current_state.json` also still reflects old `samplereverse` state and is not a training-dataset execution view.

`negative_results.json` still forbids returning to old sample solver blind search, only increasing beam or budget, using compare_semantics_agree=false candidates as primary frontier, committing full `solve_reports/`, and repeating failed sample-search directions.

Existing tool and workflow capabilities to check before making changes:

- local reverse training inventory/review/status modules;
- queue and next-queue artifacts;
- per-sample training status sync artifacts;
- existing static-triage artifacts;
- artifact index registration conventions;
- project_state gate/report/round lifecycle;
- IDA/Ghidra/debugger/solver/harness interfaces, read-only capability audit only.

## 3. Do Not Do

Do not rebuild the training inventory from scratch.

Do not rescan the full `E:\reverse` tree unless the existing queue/status artifacts are missing or explicitly stale and this decision is revised.

Do not solve any sample in this round.

Do not run local reverse samples.

Do not run runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or radare2 against samples in this round.

Do not modify solver logic, sample runners, IDA runner semantics, debugger/emulator/probe code, harness execution logic, `.codex-skills/`, raw samples, GUI/frontend, or full `solve_reports/`.

Do not return to old `sample_solver` blind search.

Do not merely increase beam, topN, budget, or timeout.

Do not generate candidate flags or candidate bytes.

Do not treat stale/missing artifacts as current evidence.

Do not write sample-specific dynamic facts, flags, local path conclusions, or temporary debug findings into `.codex-skills/`.

Do not turn training dataset planning into single-sample hardcoding.

Do not delete historical missing artifact entries just to pass gates.

Do not treat `task_packet.task` as the current execution authority.

## 4. Files To Inspect

Read the default project_state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Then inspect existing training-dataset state with bounded reads:

- `project_state/local_reverse_training_inventory_audit.md`
- `project_state/local_reverse_training_review_queue.json`
- `project_state/local_reverse_training_next_queue.json`
- `project_state/local_reverse_training_status_summary_sync.json`
- `training_materials/local_reverse/queue.json`
- `training_materials/local_reverse/github_safe_status_overlay.json`
- `reverse_agent/local_reverse_training_review.py`
- `reverse_agent/local_reverse_training_status.py`
- `tests/test_local_reverse_training_status.py`
- any existing `project_state/local_reverse_*_training_status_sync.json` files needed to build a bounded status matrix;
- any existing `project_state/local_reverse_*_static_triage.json` files referenced by the queue/status artifacts;
- `project_state/structured_evidence_gap_report.json` if referenced by status or review artifacts.

Also inspect recent training round manifests/reports only as needed:

- `project_state/rounds/round_20260611_refresh_training_inventory_and_queue_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_training_local_reverse_inventory_audit_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_training_metadata_contract_repair_v1/codex_execution_report.md`
- `project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/decision_packet.md`

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded as baseline.
3. `decision_meta` is valid, `status=APPROVED`, `mainline=training_dataset`, and `reverse-agent-iteration@v2` is active.
4. Current decision controls execution; `task_packet.json` is only state input.
5. Existing local_reverse training inventory/queue/status artifacts exist or are explicitly reported missing.
6. Existing training code and tests are inspected before adding any new code.
7. Existing IDA/Ghidra/debugger/solver/harness capabilities are noted read-only; do not assume they do not exist.
8. `negative_results.json` is checked and no prohibited failed direction is repeated.
9. Artifact freshness is respected. Missing/stale artifacts may be listed as gaps but must not be used as current evidence.
10. No sample execution, dynamic probing, candidate generation, or direct solving occurs.

Required output artifacts:

- `project_state/local_reverse_training_resume_plan.json`
- `project_state/local_reverse_training_resume_plan.md`
- `project_state/local_reverse_type_coverage_matrix.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- normal gate outputs and round archive for `round_20260616_local_reverse_training_resume_plan_v1`.

The resume plan must answer:

- what existing inventory/queue/status artifacts were found;
- which artifacts are current, stale, missing, or unknown;
- how many known samples are represented in the current queue/status view;
- per suspected type/category, which samples exist and what their status is;
- which types have evidence, static triage, solver coverage, or blocked status;
- which next bounded targets should be selected per category and why;
- which gaps must be fixed before solving can resume.

## 6. Implementation Scope

Allowed source changes, only if necessary after inspecting existing modules:

- `reverse_agent/local_reverse_training_review.py`
- `reverse_agent/local_reverse_training_status.py`
- related tests, preferably `tests/test_local_reverse_training_status.py`

Prefer no source changes if existing CLI/modules can generate the required plan artifacts.

Allowed generated state/report updates:

- `project_state/local_reverse_training_resume_plan.json`
- `project_state/local_reverse_training_resume_plan.md`
- `project_state/local_reverse_type_coverage_matrix.json`
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
- `project_state/rounds/round_20260616_local_reverse_training_resume_plan_v1/*`

Allowed read-only inputs:

- existing local_reverse queue/status/inventory artifacts;
- existing per-sample status and static-triage artifacts;
- existing training modules/tests;
- `artifact_index.json` for provenance/freshness checks;
- tool capability inventory files if already present.

Do not modify:

- solver/sample-runner/IDA/debugger/emulator/harness modules;
- `.codex-skills/`;
- raw sample files;
- GUI/frontend files;
- full `solve_reports/`;
- existing per-sample evidence artifacts unless this decision is revised;
- `project_state/artifact_index.json` unless only registering the new training resume artifacts through an existing, tested project_state mechanism and documenting the provenance.

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
python -m pytest tests/test_project_state.py tests/test_project_gate.py tests/test_local_reverse_training_status.py -q
```

If a CLI already exists for local_reverse training status/resume planning, run the narrow existing command and record it. If no CLI exists, use the smallest existing module/test path and document the absence of a CLI in the report instead of adding a broad CLI.

After generating the resume plan artifacts, run:

```powershell
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_local_reverse_training_resume_plan_v1
```

Validation expectations:

- tests pass;
- generated resume plan JSON is valid and deterministic;
- generated coverage matrix JSON is valid and deterministic;
- no sample execution occurred;
- no candidate material was generated;
- no forbidden paths were modified;
- report-summary passes;
- final-check passes;
- close-round exits 0;
- archive is created.

## 8. Stop Conditions

Stop with `BLOCKED` if the existing local_reverse queue/status/inventory artifacts are too inconsistent to build a trustworthy resume plan without rebuilding the inventory from scratch.

Stop with `BLOCKED` if a broad rescan of `E:\reverse` is required to proceed.

Stop with `BLOCKED` if a broad training metadata schema migration is required.

Stop with `REWORK_REQUIRED` if any sample is executed, probed dynamically, debugged, or solved.

Stop with `REWORK_REQUIRED` if solver/sample-runner/IDA/debugger/emulator/harness code is modified.

Stop with `REWORK_REQUIRED` if `.codex-skills/`, raw samples, GUI/frontend, or full `solve_reports/` are modified.

Stop with `REWORK_REQUIRED` if old sample_solver blind search, beam/budget expansion, or a negative_results failed direction is repeated.

Stop with `REWORK_REQUIRED` if stale/missing artifacts are treated as current evidence.

Stop with `REWORK_REQUIRED` if the resume plan does not identify next bounded training targets by type/category.

Stop with `REWORK_REQUIRED` if `project_state/local_reverse_training_resume_plan.json` or `project_state/local_reverse_type_coverage_matrix.json` is missing or invalid.

Stop with `REWORK_REQUIRED` if report-summary, final-check, or close-round fails.

Do not write SUCCESS or ACCEPTED if this round solves samples or regenerates the inventory from scratch.
