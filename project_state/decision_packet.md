# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

当前目标：定位 `module+0x258b: push esi` 之前真正把 compare LHS 指针装入 `ESI` 的来源。

最新状态已经排除旧 frame anchor：`compare_real_lhs_provenance_audit` 的 classification 是 `old_frame_anchor_rejected`，`old_slot_ebp_minus_1170_valid = false`，`identified_producers = []`，并且 next action 明确要求：keep old `[ebp-0x1170]` blocked and hook the earlier source that loads ESI before `module+0x258b`。

本轮核心问题：

> 在 `module+0x258b: push esi` 之前，哪条 instruction / 哪个 basic block / 哪个 helper return 真正写入了 `ESI`，使其成为最终 compare `arg0`？

Expected output artifact:

`compare_esi_source_before_push_audit.json`

或如果 Codex 认为更适合复用现有 sidecar，也可以窄幅扩展 `compare_real_lhs_provenance_audit`，但必须避免把旧 `[ebp-0x1170]` 重新作为默认 anchor。

## 2. Current Evidence

当前 active strategy 是 `CompareAwareSearchStrategy`。当前 best candidate 没有变化：

- exact2:
  - `78d540b49c59077041414141414141`
  - runtime exact wchar count: `2`
  - runtime distance5: `246`
- exact1/frontier:
  - `5a3e7f46ddd474d041414141414141`
  - runtime exact wchar count: `1`
  - runtime distance5: `258`

这说明仍然没有证据支持扩大候选搜索。

最新 harness run:

`sr_lhs_arg0_provenance_20260515_r4`

最新核心 artifact:

`solve_reports\harness_runs\sr_lhs_arg0_provenance_20260515_r4\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json`

该 artifact 是当前最新 indexed artifact，大小约 69KB，project_state missing 为空。

当前 bottleneck:

- stage: `compare_real_lhs_provenance_audit`
- reason: `old_frame_anchor_rejected`
- confidence: `medium`

task packet 也明确本轮任务是调查 `compare_real_lhs_provenance_audit` 卡点。

已确认事实：

- compare callsite 已确认，不再是当前问题。
- `arg0` 是 candidate-dependent LHS。
- `arg1` 是 constant flag side。
- 旧 `[ebp-0x1170]` 被拒绝。
- `breakpoint_probe_allowed = false`。
- `identified_producers = []`。
- 下一步应 hook `0x258b` 前更早的 ESI source。

旧报告 `codex_execution_report.md` 仍停留在 2026-05-14，记录的是更早的 `sr_callsite_reanchor_20260514_r5 / inconclusive` 状态，已经落后于当前 `current_state.json`。Codex 本轮结束时必须补写新的 CODEX_EXECUTION_REPORT。

## 3. Do Not Do

1. Do not return to old `sample_solver` blind search.
2. Do not only increase beam / budget / timeout / topN.
3. Do not use `compare_semantics_agree=false` candidates as primary frontier.
4. Do not commit full `solve_reports`.
5. Do not repeat exact2 basin value-pool evaluation.
6. Do not repeat H1/H3 fixed 8-candidate Base64 boundary contrast set.
7. Do not repeat transform trace consistency audit without new runtime evidence.
8. Do not rerun Base64/RC4 breakpoint probe before real LHS producer identification.
9. Do not reuse old `[ebp-0x1170]` without real-lhs provenance evidence.
10. Do not treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic evidence.
11. Do not scan entire `solve_reports` unless explicitly needed.
12. Do not re-run the previous arg0 provenance audit unchanged; it already classified `old_frame_anchor_rejected`.

Negative cache 已明确新增两条约束：不要复用旧 `[ebp-0x1170]`，不要在 real lhs producer identification 之前运行 Base64/RC4 breakpoint probe。

## 4. Files To Inspect

先读 project state：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`

重点代码：

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py`
- `reverse_agent/olly_scripts/compare_callsite_reanchor_and_lhs_provenance_audit.py`
- `reverse_agent/olly_scripts/*lhs*provenance*.py` if present
- `reverse_agent/function_semantics.py`
- `reverse_agent/project_state.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

只读取 targeted artifacts：

- `solve_reports\harness_runs\sr_lhs_arg0_provenance_20260515_r4\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json`
- `solve_reports\harness_runs\sr_lhs_arg0_provenance_20260515_r4\summary.json`
- `solve_reports\harness_runs\sr_lhs_arg0_provenance_20260515_r4\run_manifest.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_handoff_return_site_probe\compare_handoff_return_site_probe.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_producer_material_confirmation\compare_producer_material_confirmation.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\function_semantic_audit\function_semantic_audit.json`

Do not load full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports`.

## 5. Required Audit

实现一个 bounded audit：`compare_esi_source_before_push_audit`。

### A. Static ESI definition slice

以 `module+0x258b: push esi` 为 sink，向前做局部静态切片，只找能到达 `0x258b` 的 ESI writer。

必须识别以下类型：

- `mov esi, ...`
- `lea esi, ...`
- `pop esi`
- `xchg esi, ...`
- `call` 后 callee / return convention 是否可能改变 `esi`
- string/memory helper 是否通过 side effect 影响 `esi`
- predecessor basic blocks 中最后一次写 `esi`

输出应列出：

- `esi_sink = module+0x258b`
- predecessor block range
- each candidate ESI writer:
  - module offset
  - instruction
  - instruction boundary status
  - basic block / path to `0x258b`
  - whether hookable
  - why selected
  - whether it is before final compare call

不要全局扫描，只做 bounded CFG slice。

### B. Runtime ESI writer validation

对 static slice 产出的候选 ESI writer 做 runtime hook，固定三候选：

- `78d540b49c59077041414141414141`
- `78d540b49c59076f41414141414141`
- `5a3e7f46ddd474d041414141414141`

每个 hook 采集：

- hit count
- candidate hex
- module offset
- instruction
- before/after registers:
  - `eax`
  - `ecx`
  - `edx`
  - `esi`
  - `edi`
  - `esp`
  - `ebp`
- pointer previews:
  - `esi_preview`
  - candidate compare arg0 preview
- stack words around `esp`
- frame slots only as diagnostic:
  - `[ebp-0x1168]`
  - `[ebp-0x116c]`
  - `[ebp-0x1170]`
- whether `esi` equals confirmed compare arg0 pointer
- whether `esi_preview` matches confirmed compare arg0 preview
- whether observed value varies by candidate

### C. Confirmed compare arg0 reference

Use latest `compare_real_lhs_provenance_audit` as reference, not old frame anchor.

For each candidate, import:

- compare `arg0_value_by_candidate`
- compare `arg0_preview_by_candidate`
- compare `arg1_value_by_candidate`
- compare `arg1_preview_by_candidate`
- `lhs_side = arg0`
- `flag_side = arg1`

The audit must compare every candidate ESI writer observation against confirmed compare `arg0`, not against `[ebp-0x1170]`.

### D. Classifications

Top-level classification must be one of:

1. `esi_source_identified`
   - a runtime-backed ESI writer is observed;
   - its resulting `ESI` equals confirmed compare `arg0` pointer or preview;
   - relation holds across the fixed three candidates.

2. `esi_source_candidates_identified_static_only`
   - static slice found plausible ESI writers;
   - runtime validation did not complete or did not hit;
   - no semantic rejection should be inferred.

3. `esi_source_window_rejected`
   - bounded slice around known compare path does not contain a real ESI writer connected to arg0;
   - next action should move earlier in CFG, not expand search.

4. `esi_source_hook_coverage_failed`
   - key hooks failed because of address, boundary, timeout, UI, or path issue.

5. `inconclusive`
   - partial observations exist but insufficient to classify.

Top-level fields:

- `classification`
- `candidate_count`
- `runtime_backed_count`
- `esi_sink`
- `confirmed_compare_arg0_by_candidate`
- `confirmed_compare_arg0_preview_by_candidate`
- `static_esi_writer_candidates`
- `runtime_validated_esi_sources`
- `unconnected_candidate_dependent_points`
- `hook_coverage_failures`
- `old_frame_anchor_status`
- `breakpoint_probe_allowed`
- `next_bounded_action`

`breakpoint_probe_allowed` must remain false unless the audit identifies a runtime-backed ESI source and proves it is transform material, not just a compare-side copy.

## 6. Implementation Scope

Allowed:

- Add one bounded sidecar: `compare_esi_source_before_push_audit`.
- Or narrowly extend `compare_real_lhs_provenance_audit` with a separate ESI source section.
- Add one thin runtime script if required.
- Add project_state indexing for the new artifact.
- Add negative-cache entries for:
  - repeating old frame anchor after rejection;
  - running Base64/RC4 before ESI source / real lhs producer is identified.
- Update `codex_execution_report.md` with the latest 2026-05-15 run status.

Not allowed:

- no new candidate generation
- no search expansion
- no Base64/RC4 breakpoint probe
- no full solve_reports scan
- no reuse of `[ebp-0x1170]` as primary source
- no classification based only on candidate dependence
- no assumption that `0x401b50` is material producer without new evidence

## 7. Tests

Minimum compile checks:

```bat
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\function_semantics.py
```

If new runtime script is added:

```bat
python -m py_compile reverse_agent\olly_scripts\<new_script>.py
```

Targeted tests:

```bat
python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py
```

Full tests:

```bat
python -m pytest -q
```

Runtime validation:

```bat
python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_esi_source_before_push_20260515_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled
```

Rebuild state:

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_esi_source_before_push_20260515_r1
python -m reverse_agent.project_state status
```

Required test coverage:

1. `esi_source_identified`
   - static writer candidate exists;
   - runtime ESI equals confirmed compare arg0;
   - relation holds for three candidates;
   - Base64/RC4 remains blocked unless transform material is proven.

2. `esi_source_candidates_identified_static_only`
   - static slice returns hookable candidates;
   - runtime absent or not run;
   - classification does not imply semantic rejection.

3. `esi_source_window_rejected`
   - runtime evidence proves candidate writers do not connect to compare arg0;
   - next action moves earlier in CFG.

4. `esi_source_hook_coverage_failed`
   - hooks fail due to address/boundary/path/timeout/UI;
   - no semantic inference.

5. project_state indexing
   - latest artifact appears in `current_state.json`;
   - bottleneck reason updates.

## 8. Stop Conditions

Stop and report if:

1. ESI source is identified.
   - Report exact instruction offset.
   - Report before/after ESI.
   - Report compare arg0 pointer / preview match for all three candidates.
   - Keep Base64/RC4 blocked unless transform material is also proven.

2. Only static ESI candidates are found.
   - Report candidate offsets and hookability.
   - Do not infer semantics.
   - Recommend runtime validation next.

3. Current bounded window is rejected.
   - Report why no ESI writer connects to compare arg0.
   - Move earlier in CFG, not into candidate search.

4. Hook coverage fails.
   - Report address, module base, instruction boundary, path reachability, timeout, UI/runtime errors.

5. Tests fail.
   - Stop after collecting failure output.
   - Do not run harness until fixed.

本轮核心判断：`old [ebp-0x1170]` 已经被拒绝；真正要找的是 `0x258b push esi` 前谁把最终 compare LHS buffer 放进了 `ESI`。只有找到这个来源，后面才有资格继续判断它是 copy/handoff 还是 UTF-16LE/Base64/RC4 transform material。
