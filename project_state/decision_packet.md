# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

本轮目标：追踪 `0x2559` 之前 `[ebp-0x1170]` 的写入者和真实 source。

上一轮已经验证失败：

- `module+0x2559`
- instruction: `mov esi, dword ptr [ebp - 0x1170]`
- hook name: `initial_lhs_reload`
- material kind: `rc4_output`
- classification: `REJECTED`
- observed_count: `0`
- readable_count: `0`
- expected_rc4_output_match_count: `0`

因此下一步不是继续把 `0x2559` 当 RC4/Base64 material hook，而是定位：

1. 谁在 `0x2559` 之前写入 `[ebp-0x1170]`
2. 写入值来自哪个寄存器 / 调用返回值 / frame slot
3. 该 source 是否比最终 compare LHS 更接近 UTF-16LE / Base64 / RC4 transform material
4. 如果 `[ebp-0x1170]` 只是 compare-side final buffer 指针，则继续往更早的 producer 追

Expected output artifact:

`compare_lhs_upstream_writer_audit.json`

或者如果已有同名框架，扩展现有：

`compare_lhs_upstream_writer_audit`

## 2. Current Evidence

当前 active strategy 是：

`CompareAwareSearchStrategy`

当前 best candidate 仍无变化：

- exact2:
  - `78d540b49c59077041414141414141`
  - runtime exact wchar count: `2`
  - runtime distance5: `246`
- exact1/frontier:
  - `5a3e7f46ddd474d041414141414141`
  - runtime exact wchar count: `1`
  - runtime distance5: `258`

说明目前没有理由扩展候选搜索。当前真正瓶颈是 runtime material hook 没有确认。

最新可用 harness run：

`sr_esi_material_hook_20260515_r3`

核心 artifact：

`solve_reports\harness_runs\sr_esi_material_hook_20260515_r3\reports\tool_artifacts\samplereverse\material_hook_runtime_validation\material_hook_runtime_validation.json`

artifact index 显示该 run 是最新 harness run，且 `missing = []`。

关键事实：

- `material_hook_runtime_validation.classification = REJECTED`
- blocked hook: `module+0x2559`
- `connects_to_compare_lhs = true`
- `connects_to_transform_chain = false`
- `candidate_dependent = false`
- `hit_count = 0`
- `breakpoint_probe_allowed = false`
- `next_bounded_action = reject 0x2559 material-hook hypothesis and trace writer/source before 0x2559 / [ebp-0x1170]`

旧 `decision_packet.md` 要求验证 ESI source，但这个阶段已经完成并失败；不能继续执行旧 packet。旧 packet 的核心目标仍是 “Promote identified ESI source into bounded material-hook validation”，这与当前 `task_packet/current_state` 不一致。

## 3. Do Not Do

1. Do not return to old `sample_solver` blind search.
2. Do not only increase beam / budget / timeout / topN.
3. Do not use `compare_semantics_agree=false` candidates as primary frontier.
4. Do not commit full `solve_reports`.
5. Do not repeat exact2 basin value-pool evaluation.
6. Do not repeat H1/H3 fixed 8-candidate Base64 boundary contrast set.
7. Do not rerun Base64/RC4 breakpoint probe before confirming a real material construction hook.
8. Do not repeat current transform trace consistency audit without new runtime evidence.
9. Do not repeat compare return-site audit.
10. Do not repeat producer material confirmation without instruction-level evidence.
11. Do not treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic evidence.
12. Do not treat `0x2559` as RC4 output material after the latest validation rejected it.
13. Do not scan full `solve_reports` unless specifically needed.

这些限制已经写入 negative cache，尤其是：不能在 `0x2559` material hook 被拒绝后继续跑 Base64/RC4 probe。

## 4. Files To Inspect

先读 project state：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`

重点代码：

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/project_state.py`
- `reverse_agent/function_semantics.py`
- `reverse_agent/olly_scripts/material_hook_runtime_validation.py`
- `reverse_agent/olly_scripts/*lhs*writer*.py`
- `reverse_agent/olly_scripts/*lhs*producer*.py`
- `reverse_agent/olly_scripts/*provenance*.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

Targeted artifacts only：

- `solve_reports\harness_runs\sr_esi_material_hook_20260515_r3\summary.json`
- `solve_reports\harness_runs\sr_esi_material_hook_20260515_r3\run_manifest.json`
- `solve_reports\harness_runs\sr_esi_material_hook_20260515_r3\reports\tool_artifacts\samplereverse\material_hook_runtime_validation\material_hook_runtime_validation.json`
- `solve_reports\harness_runs\sr_esi_material_hook_20260515_r3\reports\tool_artifacts\samplereverse\samplereverse_compare_probe.json`
- `solve_reports\tool_artifacts\samplereverse_base64_rc4_static_point_discovery_20260508\base64_rc4_static_point_discovery.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\function_semantic_audit\function_semantic_audit.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_producer_material_confirmation\compare_producer_material_confirmation.json`

不要读取完整 `PROJECT_PROGRESS_LOG.txt`。当前 `context_level = 2`，事实文件足够。

## 5. Required Audit

实现或补全一个 bounded audit：

`compare_lhs_upstream_writer_audit`

目标是追 `[ebp-0x1170]` 的写入链，而不是验证 `0x2559` 本身。

### A. Static audit

从当前已知窗口出发：

- `0x253a`: `mov dword ptr [ebp - 0x1170], eax`
- `0x2554`: `call 0x401b50`
- `0x2559`: `mov esi, dword ptr [ebp - 0x1170]`
- `0x258b`: `push esi`
- `0x258c`: compare call

必须确认：

1. `[ebp-0x1170]` 在 `0x253a` 被写入时，`eax` 来自哪里。
2. `0x253a` 之前最近的 `eax` producer 是：
   - call return?
   - stack/frame load?
   - string/BSTR allocation?
   - transform function output?
   - copy/handoff output?
3. `0x2554 call 0x401b50` 是否修改 `[ebp-0x1170]`、`eax`、`esi` 或相关 frame slot。
4. `[ebp-0x1168]`、`[ebp-0x116c]` 是否是更早的 material pointer 或只是 metadata / temporary pointer。

### B. Runtime audit

固定三候选，不扩展搜索：

- `78d540b49c59077041414141414141`
- `78d540b49c59076f41414141414141`
- `5a3e7f46ddd474d041414141414141`

在以下点采集 runtime state：

- `module+0x253a` before/after
- `module+0x2554` before call
- `module+0x2559` before reload
- 若可稳定 hook：`0x401b50` entry/return
- 若静态分析发现更早 eax writer，则添加该 writer 的 before/after hook

每个候选至少采集：

- hit count
- `eax/ecx/edx/esi/edi/esp/ebp`
- `[ebp-0x1170]`
- `[ebp-0x1168]`
- `[ebp-0x116c]`
- `eax_preview`
- `esi_preview`
- `[ebp-0x1170]_preview`
- `[ebp-0x1168]_preview`
- `[ebp-0x116c]_preview`
- compare arg0 / arg1 pointer and preview if available
- whether each preview is candidate-dependent
- whether each preview equals compare LHS
- whether each preview resembles:
  - UTF-16LE input
  - Base64 text
  - binary RC4 output
  - final compare-side wide buffer
  - BSTR/string metadata only
  - unknown

### C. Classification

Top-level `classification` must be one of：

1. `UPSTREAM_WRITER_IDENTIFIED`
   - `[ebp-0x1170]` writer is confirmed.
   - writer source is runtime-backed.
   - next action can validate the writer source as material hook.

2. `FINAL_COMPARE_BUFFER_CONFIRMED`
   - `[ebp-0x1170]` only feeds final compare LHS.
   - no transform material is exposed at this slot.
   - next action must move earlier than the writer.

3. `COPY_OR_HANDOFF_CONFIRMED`
   - `[ebp-0x1170]` receives copied/handoff pointer.
   - next action must trace the source of the copied pointer.

4. `METADATA_OR_LENGTH_ONLY`
   - observed operations are only string/BSTR length/capacity metadata reads.

5. `HOOK_COVERAGE_FAILED`
   - hook missed, bad boundary, timeout, or unreadable pointer.

6. `INCONCLUSIVE`

Required top-level fields：

- `classification`
- `candidate_count`
- `runtime_backed_count`
- `writer_instruction`
- `writer_offset`
- `writer_source_register`
- `writer_source_slot`
- `source_preview_by_candidate`
- `candidate_dependent_fields`
- `compare_lhs_connection`
- `transform_material_evidence`
- `blocked_reason`
- `breakpoint_probe_allowed`
- `next_bounded_action`

`breakpoint_probe_allowed` must remain `false` unless the audit identifies a runtime-backed source that is candidate-dependent and connected to transform material, not merely final compare LHS.

## 6. Implementation Scope

Allowed：

- Add or complete `compare_lhs_upstream_writer_audit`.
- Add one thin runtime script if needed.
- Reuse existing Frida/UIA collection patterns from previous sidecars.
- Add project_state indexing for:
  - `latest_compare_lhs_upstream_writer_audit`
- Add negative cache entries for:
  - rejected `[ebp-0x1170]` final-buffer-only reuse
  - failed `0x2559` material-hook repetition
- Update `project_state/codex_execution_report.md` after execution.
- Update `project_state/decision_packet.md` only if Codex is asked to persist the new plan.

Not allowed：

- no new candidate generation
- no beam/budget expansion
- no broad Base64/RC4 probe
- no full `solve_reports` commit
- no classifying compare-side buffer as transform material
- no rerunning old ESI material validation unchanged

## 7. Tests

Minimum compile checks：

```bat
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\function_semantics.py
```

If runtime script is added or modified：

```bat
python -m py_compile reverse_agent\olly_scripts\compare_lhs_upstream_writer_audit.py
```

Targeted tests：

```bat
python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py
```

Full tests：

```bat
python -m pytest -q
```

Runtime validation：

```bat
python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_lhs_upstream_writer_20260516_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled
```

Rebuild state：

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_upstream_writer_20260516_r1
python -m reverse_agent.project_state status
```

Required test coverage：

1. `[ebp-0x1170]` writer identified.
2. writer is final compare buffer only.
3. writer is copy/handoff only.
4. hook coverage failure does not become semantic rejection.
5. Base64/RC4 gate remains blocked unless transform material is proven.
6. project_state correctly indexes `latest_compare_lhs_upstream_writer_audit`.

## 8. Stop Conditions

Stop and report if：

1. `[ebp-0x1170]` writer is identified.
   - Report writer offset.
   - Report source register/slot.
   - Report whether source is candidate-dependent.
   - Report whether source connects to transform material or only compare LHS.

2. The slot is final compare buffer only.
   - Report `FINAL_COMPARE_BUFFER_CONFIRMED`.
   - Keep Base64/RC4 blocked.
   - Next action: move earlier than the writer source.

3. The slot is copy/handoff only.
   - Report copied pointer source.
   - Next action: trace copied pointer’s upstream producer.

4. Hook coverage fails.
   - Report exact hook, boundary, timeout, or unreadable pointer reason.
   - Do not infer semantics from missing hits.

5. Tests fail.
   - Stop after collecting failure output.
   - Do not run harness until compile/unit tests pass.

本轮一句话：不要再验证 `0x2559` 是不是 material hook；最新结果已经拒绝。下一步应该追 `0x253a` 写入 `[ebp-0x1170]` 时 `eax` 的来源，并判断这个 upstream writer 是否才是真正的 transform material 入口。
