```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_cpp1_success_boundary_static_recheck_v1",
  "round_id": "round_20260615_cpp1_success_boundary_static_recheck_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

纠正上一份误指向 `samplereverse` 的下一轮计划。本轮当前样本按近期 current artifact 和 negative_results 判定为 `cpp1_2f6fcb63`，相对路径为 `逆向课程2023春01/CPP1.exe`。

本轮目标是做 `cpp1_2f6fcb63` 的**成功边界静态重查**：确认 `byte_429A30[16]` / compare loop 在 `strlen(Str)==18`、`strncpy(..., 0x10u)`、`if (i == 16)` 组合下的边界语义，产出可审计 artifact，决定下一轮是否允许进行有界 raw stdin runtime validation。

本轮不是解 `samplereverse`，不是重新做 target bytes printable inverse，不是 candidate blind search，也不是直接运行样本。

## 2. Current Evidence

当前 `task_packet.json` 与 `current_state.json` 仍残留 `samplereverse` 压缩状态，因此不能把其中的 sample/profile 当成当前真实任务权威。`task_packet.json` 只能作为旧建议；当前轮执行权威是本 `project_state/decision_packet.md`。

`artifact_index.json` 的 current artifact 已显示 `cpp1_2f6fcb63` 是近期实际推进样本：

- `local_reverse_cpp1_2f6fcb63_static_triage`：freshness=current，source_run=`round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1`。
- `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation`：freshness=current，source_run=`round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1`。
- `local_reverse_cpp1_2f6fcb63_static_inverse_handoff`：freshness=current，source_run=`round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1`。
- `local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review`：freshness=current，source_run=`round_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1`。
- `local_reverse_cpp1_2f6fcb63_input_delivery_review`：freshness=current，source_run=`round_20260614_cpp1_2f6fcb63_input_delivery_review_v1`。

Current static triage confirms IDA static-only evidence for `cpp1_2f6fcb63`: sample path `逆向课程2023春01/CPP1.exe`, PE/cpp category, `tool_status=success`, `source_tool=IDA`, `executed_sample=false`, `runtime_validated=false`; allowed_actions only include `static_triage`, and forbidden_actions include `runtime_probe`, `bruteforce`, `upload_binary`.

Current target revalidation confirms:

- target symbol: `byte_429A30`
- target address: `0x00429A30`
- target length: 16
- target bytes hex: `d596c4f60745577776e5f64847f74817`
- main function: `_main_0`
- forward transform: `(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)`
- static notes: input length check is `strlen(Str) != 18`, copy is `strncpy(Destination, Str, 0x10u)`, compare expression is `Destination[i] == byte_429A30[i]`.

Current static inverse handoff is BLOCKED with `NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES`. It found a unique all-byte preimage but no complete printable ASCII preimage. This path is now recorded in `negative_results.json` and must not be repeated.

Current alternative static semantics review says the transform is a single-byte bit permutation, signed/unsigned models are equivalent after `u8` truncation, no xor/add/sub/table/previous-byte dependency was seen, and the nonprintable all-byte preview is `5d5a1cde131557d7d69dde2417df2453`.

Current input delivery review says raw byte delivery appears feasible, suggested payload preview is `5d5a1cde131557d7d69dde2417df24534141`, but success boundary remains `UNKNOWN_NEEDS_STATIC_OR_TOOL_RECHECK` because `byte_429A30[16]` is not available in the current 16-byte target revalidation. It explicitly recommends `NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK` before runtime.

`negative_results.json` must be respected. In particular, do not repeat `cpp1_2f6fcb63 current target bytes printable inverse path`; it already established no complete printable preimage under current target bytes, with missing printable indices `2, 3, 4, 5, 7, 8, 9, 10, 12, 13`.

Existing tool capabilities must be reused, not reimplemented:

- IDA / IDAPython interface already exists through `tool_runners.py` and `reverse_agent/ida_scripts/collect_evidence.py`.
- artifact_index freshness tracking already exists in `project_state.py` / `project_gate.py`.
- StructuredEvidence primitives already exist in `evidence.py`.
- Harness exists, but this round must not run runtime validation unless the success boundary is first resolved and a later decision explicitly permits it.
- Ghidra is not the required path for this round; do not create a Ghidra runner.

## 3. Do Not Do

Do not solve or analyze `samplereverse` in this round.

Do not use `task_packet.sample=samplereverse` as current task authority.

Do not repeat the `cpp1_2f6fcb63 current target bytes printable inverse path`.

Do not call the nonprintable preview or `5d5a1cde131557d7d69dde2417df24534141` a solved password without runtime proof.

Do not run runtime_probe, dynamic debugger, hook, emulator, or sample execution in this round.

Do not run brute force, blind solver search, old `sample_solver`, or budget/beam/topN expansion.

Do not create duplicate IDA / debugger / harness / solver interfaces.

Do not modify `.codex-skills/`, `training_materials/`, or complete `solve_reports/`.

Do not treat stale/missing artifact as current evidence.

Do not widen to other local samples such as `affineenc_333f8ca9` unless the inspected current artifact proves `cpp1_2f6fcb63` is not the active sample; if so, stop and report mismatch instead of guessing.

## 4. Files To Inspect

Must read in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Must bounded-read current cpp1 artifacts:

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `project_state/local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json`
- `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`

Must inspect existing tool/code only if needed for the static recheck:

- `reverse_agent/tool_runners.py`
- `reverse_agent/ida_scripts/collect_evidence.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- directly relevant tests for any touched module

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Startup commands must be recorded first:

- `Set-Location F:\reverse-agent`
- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`

If startup dirty files exist, record baseline before doing work and do not classify inherited dirty files as current round changes.

Perform these checks before producing any result:

1. Verify `decision_meta` is parseable, `status=APPROVED`, `mainline=reverse_solving`, and `skill_profiles` are active in `.codex-skills/registry.json`.
2. Verify the current cpp1 artifact paths in `artifact_index.json` have `freshness=current` and `sample_id=cpp1_2f6fcb63`.
3. Verify the prior negative result for `cpp1_2f6fcb63 current target bytes printable inverse path` is not repeated.
4. Verify no runtime execution is performed.
5. Verify no new tool interface is created when existing IDA static extraction capability is available.

Required output artifact:

- `project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json`

The artifact must include at least:

- `schema_version`
- `decision_id`
- `round_id`
- `sample_id`
- `relative_path`
- `sha256`
- `analysis_mode="success_boundary_static_recheck"`
- `mainline="reverse_solving"`
- `executed_sample=false`
- `runtime_validated=false`
- `source_artifacts` with freshness for all cpp1 current artifacts used
- `negative_results_considered`
- `target_symbol`
- `target_address`
- `target_length_known=16`
- `requested_boundary_indices=[16,17]` or explicit reason if only index 16 is relevant
- `byte_429A30_index_16_status`: one of `KNOWN_MATCH_BLOCKER`, `KNOWN_MISMATCH_SAFE`, `UNKNOWN_REQUIRES_TOOL_RECHECK`, `CONTRADICTED_STOP`
- `destination_index_16_source_review`
- `compare_loop_exit_reason_review`
- `payload_preview_hex` from current input_delivery_review, but not as solved answer
- `recommended_next_action`: one of `ALLOW_SEPARATE_BOUNDED_RAW_STDIN_RUNTIME_VALIDATION`, `STOP_TARGET_OR_BOUNDARY_CONTRADICTION`, `NEEDS_TOOL_RECHECK`, `NO_SAFE_NEXT_ACTION`
- `stop_conditions_for_next_round`

If the current artifacts do not contain enough data to determine `byte_429A30[16]`, Codex may run only an existing bounded IDA static extraction path, using existing IDA runner/script, to extract adjacent bytes around `0x00429A30` or xrefs required for boundary semantics. If IDA cannot be run or configured, stop with `NEEDS_TOOL_RECHECK`; do not invent the byte.

## 6. Implementation Scope

Default: no source code changes.

Allowed generated/updated files:

- `project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260615_cpp1_success_boundary_static_recheck_v1/*`

Only if existing code cannot register or validate this static recheck artifact, Codex may make minimal changes to:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- relevant tests

Do not modify solver logic, strategy logic, harness runtime behavior, IDA runner semantics, or sample-specific solver profiles in this round.

## 7. Tests

Must record commands, stdout/stderr, and exit code in `project_state/pytest_result.txt`.

Required commands:

- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`

If no source code is modified, run:

- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`

If source code is modified, run the directly relevant focused tests plus:

- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`

Finish with:

- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_cpp1_success_boundary_static_recheck_v1`

## 8. Stop Conditions

If startup path is not `F:\reverse-agent`, stop.

If `decision_meta` is invalid, stop.

If registry does not contain active `reverse-agent-iteration@v2`, stop.

If current artifacts do not support `cpp1_2f6fcb63` as the active sample, stop and report state mismatch instead of falling back to `samplereverse`.

If success boundary remains unknown and existing IDA static extraction cannot safely resolve it, stop with `NEEDS_TOOL_RECHECK`.

If runtime validation becomes necessary, do not run it in this round; write a separate next decision requiring bounded raw stdin delivery validation.

If any forbidden path or negative-result repeat is touched, report `REWORK_REQUIRED`.

If pytest_result/report/decision/round ids mismatch, report `REWORK_REQUIRED`.
