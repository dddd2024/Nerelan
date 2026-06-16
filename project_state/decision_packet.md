```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_success_target_reanchor_v1",
  "round_id": "round_20260616_cpp1_success_target_reanchor_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Re-anchor the `cpp1_2f6fcb63` success target and compare-boundary evidence using mature static tooling.

Current evidence shows the simple 16-byte inverse path is rejected by runtime output, and the static boundary model says `Destination[16]` and `byte_429A30[16]` both become `0x00`, preventing the compare loop from exiting at `i == 16`. This round must determine whether that conclusion is final for the current target, or whether the project has anchored the wrong target bytes / wrong success path / wrong decompiler boundary.

This is a `tool_integration` round. It must reuse existing IDA/IDAPython, tool runner, and artifact-index infrastructure. It is not a solver round and not a new runtime campaign.

Required outcome:

- produce `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`;
- determine whether `_main_0`, `byte_429A30`, and the success string xref all belong to the same decisive success path;
- extract or confirm the exact compare-loop assembly/control-flow boundary around the `i == 16` success check;
- extract or confirm data/xrefs for `byte_429A30[0..23]` and whether bytes beyond index 15 are part of the intended compare target;
- extract or confirm whether any static write can make `Destination[16]` nonzero or otherwise mismatch `byte_429A30[16]`;
- recommend one of: `CURRENT_TARGET_PATH_REJECTED`, `TARGET_REANCHOR_NEEDED`, `DECOMPILER_BOUNDARY_NEEDS_IDA_RECHECK`, `BLOCKED_TOOL_UNAVAILABLE`.

## 2. Current Evidence

The current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain historical `samplereverse` state inputs and must not override this decision.

Current mainline: `tool_integration`.

Accepted previous closeout:

- `decision_20260616_cpp1_pause_review_closeout_rework_v1`
- `round_20260616_cpp1_pause_review_closeout_rework_v1`
- result: `ACCEPTED`

Current cpp1 evidence:

- `local_reverse_cpp1_2f6fcb63_static_triage` is current in `artifact_index.json`.
- `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` is current and has `revalidation_status=PASSED`.
- `local_reverse_cpp1_2f6fcb63_runtime_boundary_probe` is current and records bounded prior runtime probes, but this round must not rerun them.
- `local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review` is current; it classifies `baseline_18_A`, `raw_inverse_AA`, and `raw_inverse_BB` as `FAILURE_MARKER_SEEN`, with `current_preview_status=REJECTED_BY_RUNTIME_OUTPUT` and `runtime_validated=false`.
- `local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck` says:
  - required input length is 18;
  - `strncpy(Destination, Str, 0x10u)` controls only destination indices 0..15;
  - transform loop touches indices 0..17 for 18-byte input;
  - compare loop condition is `i < strlen(Str) && Destination[i] == byte_429A30[i]`;
  - success condition is `i == 16`;
  - `byte_429A30[16] == 0x00` and `byte_429A30[17] == 0x00`;
  - static fresh-buffer model predicts `Destination[16] == 0x00`, so index 16 matches rather than producing the required boundary mismatch;
  - current all-byte inverse payload preview must not be called solved or runtime validated.

Existing tool capability audit:

- IDA / IDAPython runner, IDA script library, and IDA evidence parsing already exist. Do not create a duplicate IDA interface.
- OllyDbg/debugger artifacts and runner support exist, but this round is static-first and must not run debugger automation by default.
- Ghidra capability is currently missing; do not add Ghidra in this round.
- Solver templates, symbolic solvers, and harness exist, but this round must not use them for candidate search or runtime validation.
- `artifact_index.json` already tracks freshness; stale/missing artifacts must not be used as current evidence.

Negative results to respect:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use compare_semantics_agree=false candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat the printable inverse path unless target bytes or transform semantics change.
- Do not rerun the same CPP1 payloads that are already rejected by pause-aware runtime output.

Tool execution permission:

- Static IDA/IDAPython extraction is allowed if the existing tool interface is configured locally.
- Raw runtime execution of `CPP1.exe` is not allowed in this round.
- Debugger execution is not allowed in this round unless the existing static tool chain cannot answer basic xref/control-flow questions and Codex stops with `BLOCKED_TOOL_UNAVAILABLE` instead of improvising a debugger run.

## 3. Do Not Do

Do not rerun `CPP1.exe`.

Do not run new runtime probes, debugger automation, hook, emulator, harness campaign, or console automation.

Do not patch the sample binary.

Do not generate password/candidate/flag.

Do not mark CPP1 as solved.

Do not analyze or solve `samplereverse`.

Do not use old `sample_solver`, brute force, SMT, beam/topN/budget expansion, or candidate-pool exploration.

Do not repeat the printable inverse path or the already rejected `raw_inverse_AA` / `raw_inverse_BB` validation route.

Do not create duplicate IDA/Ghidra/debugger/solver/harness interfaces.

Do not modify `.codex-skills/`, raw samples, training materials, GUI/frontend, complete `solve_reports/`, solver strategy, runtime runner behavior, debugger runner behavior, or harness behavior.

Do not remove historical missing artifact entries just to pass gates.

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

Also inspect:

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json`
- `project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json`
- `project_state/local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json`
- `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `reverse_agent/tool_capability_inventory.py`
- `reverse_agent/tool_runners.py`
- `reverse_agent/ida_scripts/`, only existing scripts directly relevant to function/string/data/xref extraction; do not read unrelated scripts in full unless selected by name
- existing source modules/tests relevant to any new thin artifact builder

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before changing files, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=tool_integration`, and `reverse-agent-iteration@v2` is active.
3. `task_packet.json/current_state.json` are historical `samplereverse` state, not current execution authority.
4. Current CPP1 artifacts listed above exist or are explicitly reported as missing/stale.
5. Current target revalidation and pause-aware runtime review are current in `artifact_index.json`.
6. Existing IDA / IDAPython interfaces are checked before adding any code.
7. This round does not require running the sample or debugger.

Required artifact:

- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`

The artifact must include at least:

- `schema_version`
- `decision_id`
- `round_id`
- `sample_id`
- `relative_path`
- `sha256`
- `analysis_mode="success_target_reanchor"`
- `mainline="tool_integration"`
- `executed_sample=false`
- `runtime_validated=false`
- `debugger_or_hook_used=false`
- `candidate_bytes_hex=null`
- `candidate_text=null`
- `source_artifacts`
- `source_artifact_freshness`
- `tool_capability_review`, including existing IDA/tool runner status and whether any new interface was added
- `success_string_xrefs`, with source function/address if recoverable
- `failure_string_xrefs`, with source function/address if recoverable
- `main_function_reanchor`, including whether `_main_0` is still the decisive validation function
- `compare_loop_assembly_or_pseudocode_evidence`, including loop condition, compare operand sources, branch condition, and success check
- `target_data_reanchor`, including `byte_429A30` xrefs, bytes 0..23, and whether index 16 is target-owned or padding/terminator
- `destination_index_16_write_sources`, including whether any static write reaches `Destination[16]` before compare
- `contradiction_resolution`, one of `CURRENT_TARGET_PATH_REJECTED`, `TARGET_REANCHOR_NEEDED`, `DECOMPILER_BOUNDARY_NEEDS_IDA_RECHECK`, `BLOCKED_TOOL_UNAVAILABLE`
- `recommended_next_action`
- `stop_conditions_for_next_round`

Expected result unless new IDA/tool evidence contradicts it:

- `contradiction_resolution=CURRENT_TARGET_PATH_REJECTED`
- reason: current target bytes and current boundary evidence make the simple inverse preview a rejected path; next solving work must re-anchor target/success path or identify a different validation path before any new runtime validation.

`artifact_index.json` must register `local_reverse_cpp1_2f6fcb63_success_target_reanchor` as current only if the artifact is generated successfully.

If the existing local static tool path is unavailable, generate a BLOCKED artifact with `contradiction_resolution=BLOCKED_TOOL_UNAVAILABLE` and do not fabricate evidence.

## 6. Implementation Scope

Prefer no source changes if Codex can produce the reanchor artifact directly from current JSON evidence plus existing IDA/static artifacts.

Allowed project_state updates:

- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`
- `project_state/artifact_index.json`, only to register the new reanchor artifact
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
- `project_state/rounds/round_20260616_cpp1_success_target_reanchor_v1/*`

Allowed source change only if needed for reproducibility:

- `reverse_agent/local_reverse_cpp1_success_target_reanchor.py`, as a thin artifact builder that consumes current JSON evidence and existing static/IDA outputs.
- Existing IDA script reuse is preferred. Add a new IDA script only if no existing script can extract the required string xrefs/data xrefs/disassembly slice, and only as a narrow script under existing IDA script conventions.
- Directly related focused tests.

Do not modify `reverse_agent/project_gate.py` in this round.

Do not modify runtime runner behavior, debugger integration, solver logic, harness behavior, GUI/frontend, `.codex-skills/`, raw samples, or sample inventory semantics.

## 7. Tests

Record commands, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

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
```

If a new thin CLI is added, use this shape:

```powershell
python -m reverse_agent.local_reverse_cpp1_success_target_reanchor --static-triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --target-revalidation project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json --success-boundary project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json --pause-review project_state/local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json
```

If no source code is changed, run:

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

If source code is changed, run focused tests plus:

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

Finish with:

```powershell
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_success_target_reanchor_v1
```

## 8. Stop Conditions

Stop with `BLOCKED` if current target revalidation or pause-aware runtime review is missing or not current.

Stop with `BLOCKED_TOOL_UNAVAILABLE` if existing static/IDA evidence cannot support the required reanchor checks and no existing tool interface is available.

Stop with `REWORK_REQUIRED` if the artifact lacks source freshness, compare-loop evidence, target-data evidence, or a clear contradiction resolution.

Stop with `REWORK_REQUIRED` if any runtime execution of `CPP1.exe` occurs in this round.

Stop with `REWORK_REQUIRED` if `project_gate.py` is modified.

Stop with `REWORK_REQUIRED` if report-summary and live report disagree.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Do not write SUCCESS or ACCEPTED if final gate or close-round fails.
