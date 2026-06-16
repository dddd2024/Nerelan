```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_bounded_runtime_boundary_probe_v1",
  "round_id": "round_20260616_cpp1_bounded_runtime_boundary_probe_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Use the current `cpp1_2f6fcb63` target-byte evidence to perform a **bounded runtime boundary diagnostic** on the local trusted sample.

The user has clarified that the local samples are known safe/non-malicious, so runtime execution is allowed when it materially speeds up solving. This does not remove the project requirements for bounded execution, SHA/path checks, provenance, stdout/stderr/exit-code capture, and artifact registration.

This round's objective is to resolve the current contradiction:

- Current target bytes revalidation is `PASSED` and current.
- Static inverse over target bytes yields a nonprintable all-byte preimage preview.
- Success-boundary static recheck says the current 18-byte preview should not be called solved because `Destination[16]` is not input-controlled and `byte_429A30[16] == 0x00` appears to match the static zero model.

Therefore this round may run the local sample only as a bounded diagnostic to determine whether the runtime path agrees with or contradicts the static success-boundary model. It must not blindly search candidates or expand to other samples.

## 2. Current Evidence

The current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` still contain historical `samplereverse` state and must not override this decision.

The previous accepted round was `round_20260616_cpp1_target_revalidation_closeout_rework_v1`, an `engineering_branch` closeout that reconciled report-summary, final-check, pytest_result, and archive. It did not change the `cpp1` solving evidence.

Current cpp1 evidence:

- `project_state/artifact_index.json` registers `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` as `freshness=current`, sample_id `cpp1_2f6fcb63`, path `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`.
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json` has `revalidation_status=PASSED`, `target_symbol=byte_429A30`, `target_address=0x00429A30`, `target_length=16`, and `target_bytes_hex=d596c4f60745577776e5f64847f74817`.
- The forward transform is `(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)`.
- The static pseudocode includes `strlen(Str) != 18`, `strncpy(Destination, Str, 0x10u)`, the transform loop, `Destination[i] == byte_429A30[i]`, and success condition `if (i == 16)`.
- `project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json` says `byte_429A30[16] == 0x00`, `Destination[16]` is not input-controlled by `strncpy(..., 0x10u)`, and the current preview is not success-boundary safe under the static fresh-buffer model.
- The same success-boundary artifact recommends `STOP_TARGET_OR_BOUNDARY_CONTRADICTION`, not solved.
- `negative_results.json` must still be respected: do not repeat the printable inverse path and do not go back to old blind solver search.

Existing capability audit:

- `reverse_agent/local_reverse_runtime.py` already provides a bounded local runtime policy and subprocess runner for local samples.
- `reverse_agent/local_reverse_cpp1_inverse_handoff.py` already contains the bit permutation forward/inverse logic, but it was originally written for the older target-bytes artifact and may need a minimal compatibility update to accept `target_bytes_current_revalidation`.
- There is no need to create a second generic runtime framework. If targeted raw-stdin support is missing, extend or reuse existing runtime helpers minimally rather than duplicating policy/path/SHA checks.
- IDA/Ghidra/debugger automation is not the default path for this round. If runtime diagnostic contradicts static evidence, stop and record it; do not start ad hoc debugging in this round.

## 3. Do Not Do

Do not analyze or solve `samplereverse`.

Do not use `task_packet.task` as the current execution task.

Do not run old `sample_solver`, blind search, brute force, SMT, beam/topN/budget expansion, or candidate-pool exploration.

Do not repeat the printable inverse path for `cpp1_2f6fcb63`; the current path is an all-byte nonprintable preimage plus bounded runtime diagnostic, not printable ASCII recovery.

Do not run more than 4 sample executions in this round.

Do not run the sample outside the local root, do not upload/copy the binary into the repository, and do not allow network access.

Do not mark solved merely because a static inverse candidate exists.

Do not print a nonprintable candidate as normal text. If a runtime-success input exists, record it as `candidate_bytes_hex` and only include `candidate_text` when all bytes are printable ASCII.

Do not modify `.codex-skills/`, raw samples, training materials, GUI/frontend, or complete `solve_reports/`.

Do not create duplicate IDA/Ghidra/debugger/solver/harness interfaces.

Do not change existing benchmark behavior in `local_reverse_runtime.py` while adding any targeted raw-stdin helper.

## 4. Files To Inspect

Read the default project state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect:

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json`
- `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `project_state/local_reverse_corpus_index.json`
- `project_state/local_reverse_inventory.json`
- `reverse_agent/local_reverse_runtime.py`
- `reverse_agent/local_reverse_cpp1_inverse_handoff.py`
- `reverse_agent/local_reverse_cpp1_input_delivery_review.py`
- directly relevant tests for any touched module

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=reverse_solving`, and `reverse-agent-iteration@v2` is active.
3. `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` is current in `artifact_index.json` and `revalidation_status=PASSED`.
4. The target sample is `cpp1_2f6fcb63`, relative path `逆向课程2023春01/CPP1.exe`, SHA256 `2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede`.
5. The runtime policy is explicitly based on the user's assertion that local samples are safe, and still enforces local-root path, SHA256, timeout, execution-count, and no-network boundaries.
6. The success-boundary static recheck is considered; this round is a diagnostic to resolve that contradiction, not a blind validation shortcut.
7. Existing runtime and inverse-transform helpers are reused or minimally extended; no duplicate framework is introduced.

Required runtime probes, maximum 4 executions:

- `baseline_18_A`: stdin bytes `4141414141414141414141414141414141410a` (`AAAAAAAAAAAAAAAAAA\n`), expected not to succeed.
- `raw_inverse_AA`: stdin bytes `5d5a1cde131557d7d69dde2417df245341410a`, derived from all-byte inverse first 16 bytes plus `AA\n`; diagnostic only.
- `raw_inverse_BB`: stdin bytes `5d5a1cde131557d7d69dde2417df245342420a`, same first 16 bytes plus `BB\n`; tests whether suffix choice affects boundary behavior.

Optional fourth execution only if needed:

- `raw_inverse_no_newline`: stdin bytes `5d5a1cde131557d7d69dde2417df24534141`, same payload without newline, only if newline delivery changes behavior or causes timeout.

The output artifact must be:

- `project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json`

It must include at least:

- `schema_version`
- `decision_id`
- `round_id`
- `sample_id`
- `relative_path`
- `sha256`
- `analysis_mode="bounded_runtime_boundary_probe"`
- `mainline="reverse_solving"`
- `executed_sample=true` if any probe executed
- `runtime_validated` true only if an exact success condition is observed under the strict rules below
- `runtime_allowed_reason="user_asserted_local_samples_pretested_no_virus"`
- `runtime_policy` with local root, network disabled, max executions, timeout seconds, and SHA check
- `source_artifacts` and source freshness for target revalidation and success boundary static recheck
- `probes` with `probe_name`, `stdin_hex`, `timeout`, `exit_code`, `stdout_preview`, `stderr_preview`, `duration_ms`, `success_marker_seen`, `failure_marker_seen`
- `baseline_probe_name="baseline_18_A"`
- `candidate_probe_name` if any candidate succeeds
- `candidate_bytes_hex` only if exact success is observed and baseline fails
- `candidate_text` only if the bytes are printable ASCII; otherwise null
- `static_boundary_contradicted` true if runtime success contradicts the static boundary model
- `verdict`, one of `RUNTIME_SUCCESS_CONFIRMED`, `STATIC_BOUNDARY_CONFIRMED_NO_SUCCESS`, `RUNTIME_CONTRADICTS_STATIC_NEEDS_TOOL_RECHECK`, `BLOCKED_RUNTIME_UNAVAILABLE`, `INCONCLUSIVE_TIMEOUT_OR_IO`
- `recommended_next_action`

Strict success rule:

- A probe may be treated as runtime-success only if stdout/stderr contains the exact success message or an unambiguous equivalent from the binary, such as `Congratulations! You are right!`, while the baseline probe does not.
- If `raw_inverse_AA` or `raw_inverse_BB` succeeds but this contradicts static boundary evidence, set `static_boundary_contradicted=true` and record the input bytes. Do not perform debugger/xref repair in this round.
- If no probe succeeds and baseline fails normally, set verdict `STATIC_BOUNDARY_CONFIRMED_NO_SUCCESS` and recommend a separate static/tool recheck of control flow, SEH/division-by-zero path, or target boundary semantics.

## 6. Implementation Scope

Allowed generated/updated files:

- `project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json`
- `project_state/artifact_index.json`, only to register the runtime boundary probe artifact
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
- `project_state/rounds/round_20260616_cpp1_bounded_runtime_boundary_probe_v1/*`

Allowed source changes only if needed:

- `reverse_agent/local_reverse_runtime.py`, only to add or expose bounded single-sample raw-stdin probe support while preserving existing benchmark behavior
- `reverse_agent/local_reverse_cpp1_inverse_handoff.py`, only to accept `target_bytes_current_revalidation` artifacts or avoid requiring `expected_target_length` when `target_length=16` is present
- `reverse_agent/local_reverse_cpp1_runtime_boundary_probe.py`, only if a thin cpp1-specific wrapper is needed and it reuses shared runtime helpers rather than duplicating policy/path/SHA logic
- directly relevant tests

Do not modify solver strategy, harness campaign behavior, IDA runner semantics, GUI/frontend, `.codex-skills/`, or sample inventory semantics.

## 7. Tests

Record commands, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

Startup commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Required gate/status commands:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
```

Required diagnostic command must be whichever CLI Codex implements or reuses for bounded raw-stdin probing. If a new wrapper is added, use this shape:

```powershell
python -m reverse_agent.local_reverse_cpp1_runtime_boundary_probe --target-revalidation project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json --success-boundary project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json --timeout-seconds 5
```

If no source code is changed, run:

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

If source code is changed, run directly relevant tests plus:

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

If `local_reverse_runtime.py` is changed, include its tests or add focused tests for raw-stdin behavior with a harmless Python fixture, not the real PE binary.

If `local_reverse_cpp1_inverse_handoff.py` is changed, include its focused tests or add a focused test for accepting target-bytes revalidation artifacts.

Finish with:

```powershell
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_bounded_runtime_boundary_probe_v1
```

## 8. Stop Conditions

Stop if startup path is not `F:\reverse-agent` or repository root is wrong.

Stop if current target revalidation artifact is missing, not current, or not `PASSED`.

Stop if the local sample file cannot be resolved under the local root or its SHA256 does not match expected metadata.

Stop if implementing raw runtime support would require broad harness rewrites, debugger automation, network access, binary upload, or changes outside the allowed source scope.

Stop if more than 4 executions would be needed.

Stop if all runtime probes time out or cannot capture stdout/stderr; report `INCONCLUSIVE_TIMEOUT_OR_IO`.

Stop if any command fails, pytest_result is missing/mismatched, report-summary/final-check disagrees with live report, or close-round exits nonzero.

Do not write SUCCESS or ACCEPTED if close-round fails.
