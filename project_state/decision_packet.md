# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

当前目标：把已经识别出的 ESI source 提升为 bounded material-hook validation，判断它是否只是 compare-side buffer / string handoff，还是已经可以作为 transform material 的稳定观测点。

最新状态已经前进到：

- stage: `compare_esi_source_window_audit`
- reason: `esi_source_identified`
- task: `Promote identified ESI source into bounded material-hook validation`

这说明上一轮已经不再卡在 “ESI 从哪里来”，而是已经识别出 ESI source。下一步要验证这些 source 是否足以打开真正的 material probe / Base64-RC4 路径。

Expected output artifact:

`material_hook_runtime_validation_from_esi_source.json`

或如果已有 material validation 框架更合适，也可以扩展现有：

`material_hook_runtime_validation.json`

但必须明确标记这轮 source 来自：

`compare_esi_source_window_audit / esi_source_identified`

## 2. Current Evidence

当前 active strategy 仍是：

`CompareAwareSearchStrategy`

当前 best candidate 没有变化：

- exact2:
  - `78d540b49c59077041414141414141`
  - runtime exact wchar count: `2`
  - runtime distance5: `246`
- exact1/frontier:
  - `5a3e7f46ddd474d041414141414141`
  - runtime exact wchar count: `1`
  - runtime distance5: `258`

这说明仍然不应该扩大候选搜索。

最新 harness run:

`sr_esi_source_window_20260515_r1`

最新核心 artifact:

`solve_reports\harness_runs\sr_esi_source_window_20260515_r1\reports\tool_artifacts\samplereverse\compare_esi_source_window_audit\compare_esi_source_window_audit.json`

artifact index 显示该 artifact 是当前最新核心 artifact，大小约 113860 bytes，`missing = []`。

当前 `compare_esi_source_window_audit` 已确认：

- `classification = esi_source_identified`
- `breakpoint_probe_allowed = true`
- `candidate_count = 3`
- `identified_producers` 非空
- `next_bounded_action = promote the identified ESI source as the next bounded material-hook start`

已识别的关键 producer candidates 包括：

1. `module+0x2559`
   - hook name: `initial_lhs_reload`
   - instruction: `mov esi, dword ptr [ebp - 0x1170]`
   - role: `initial_esi_source`
   - candidate-dependent: true
   - connects to compare LHS: true
   - compare_lhs_match_count: 3
   - runtime_backed_count: 3

2. `module+0x255f`
   - hook name: `esi_length_load`
   - instruction: `mov ecx, dword ptr [esi - 8]`
   - role: `esi_length_check`
   - candidate-dependent: true
   - connects to compare LHS: true
   - compare_lhs_match_count: 3
   - runtime_backed_count: 3

3. `module+0x2567`
   - hook name: `esi_length_sub`
   - instruction: `sub eax, dword ptr [esi - 4]`
   - role: `esi_length_check`
   - candidate-dependent: true
   - connects to compare LHS: true
   - compare_lhs_match_count: 3
   - runtime_backed_count: 3

这三点已经证明 ESI source / compare-side LHS buffer 路径成立，但还没有证明它们是 UTF-16LE / Base64 / RC4 transform material。

旧 `codex_execution_report.md` 仍然主要记录较早的 2026-05-14 / 2026-05-13 状态，明显落后于当前 `sr_esi_source_window_20260515_r1`。Codex 本轮结束时必须补写最新 CODEX_EXECUTION_REPORT。

## 3. Do Not Do

1. Do not return to old `sample_solver` blind search.
2. Do not only increase beam / budget / timeout / topN.
3. Do not use `compare_semantics_agree=false` candidates as primary frontier.
4. Do not commit full `solve_reports`.
5. Do not repeat exact2 basin value-pool evaluation.
6. Do not repeat H1/H3 fixed 8-candidate Base64 boundary contrast set.
7. Do not repeat transform trace consistency audit without new runtime evidence.
8. Do not repeat compare return-site audit without using its classification.
9. Do not treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic evidence.
10. Do not classify `0x2559 / 0x255f / 0x2567` as transform material only because they are candidate-dependent.
11. Do not expand search before validating material hook status.
12. Do not scan entire `solve_reports` unless explicitly needed.
13. Do not commit bulky runtime artifacts.

Negative cache still blocks old blind search, budget-only expansion, stale return-site repeats, and unproven function material assumptions.

## 4. Files To Inspect

先读 project state：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`

重点代码：

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/olly_scripts/material_hook_runtime_validation.py`
- `reverse_agent/olly_scripts/*esi*source*.py`
- `reverse_agent/olly_scripts/*lhs*provenance*.py`
- `reverse_agent/function_semantics.py`
- `reverse_agent/project_state.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

Targeted artifacts only:

- `solve_reports\harness_runs\sr_esi_source_window_20260515_r1\reports\tool_artifacts\samplereverse\compare_esi_source_window_audit\compare_esi_source_window_audit.json`
- `solve_reports\harness_runs\sr_esi_source_window_20260515_r1\summary.json`
- `solve_reports\harness_runs\sr_esi_source_window_20260515_r1\run_manifest.json`
- `solve_reports\harness_runs\sr_esi_source_window_20260515_r1\reports\tool_artifacts\samplereverse\samplereverse_compare_probe.json`
- `solve_reports\tool_artifacts\samplereverse_base64_rc4_static_point_discovery_20260508\base64_rc4_static_point_discovery.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\function_semantic_audit\function_semantic_audit.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_producer_material_confirmation\compare_producer_material_confirmation.json`

Do not load full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports`.

## 5. Required Audit

实现一个 bounded validation：

`material_hook_runtime_validation_from_esi_source`

### A. Validate identified ESI-source hooks as material hooks

候选 hook 起点来自 latest `compare_esi_source_window_audit`：

- `module+0x2559`
  - `mov esi, dword ptr [ebp - 0x1170]`
  - role: `initial_esi_source`
- `module+0x255f`
  - `mov ecx, dword ptr [esi - 8]`
  - role: `esi_length_check`
- `module+0x2567`
  - `sub eax, dword ptr [esi - 4]`
  - role: `esi_length_check`

必须判断每个 hook 是：

1. `confirmed_transform_material`
   - observed buffer is candidate-dependent;
   - connects to compare LHS;
   - content is consistent with transform-chain material, not merely final compare buffer metadata;
   - relation holds across fixed candidates.

2. `compare_side_buffer_only`
   - connects to compare LHS;
   - candidate-dependent;
   - but appears to be final compare buffer / BSTR / string metadata / length check only.

3. `copy_or_handoff_only`
   - source is a pointer handoff/copy;
   - not enough evidence that this instruction produces transform material.

4. `length_or_metadata_check_only`
   - reads `[esi-8]` / `[esi-4]` or metadata;
   - does not produce material.

5. `hook_coverage_failed`
   - hook did not hit, bad boundary, timeout, UI failure, unreadable pointer.

6. `inconclusive`

### B. Required runtime observations

Run only the fixed three candidates:

- `78d540b49c59077041414141414141`
- `78d540b49c59076f41414141414141`
- `5a3e7f46ddd474d041414141414141`

For each hook and candidate, collect:

- hit count
- module offset
- instruction
- register values:
  - `eax`
  - `ecx`
  - `edx`
  - `esi`
  - `edi`
  - `esp`
  - `ebp`
- pointer previews:
  - `esi_preview`
  - `eax_preview`
  - `[ebp-0x1170]_preview`
  - `[ebp-0x1168]_preview`
  - `[ebp-0x116c]_preview`
- metadata reads:
  - `[esi-8]`
  - `[esi-4]`
  - possible length / capacity / BSTR header fields
- compare reference:
  - confirmed compare `arg0_value`
  - confirmed compare `arg0_preview`
  - confirmed compare `arg1_preview`
- whether preview equals compare arg0
- whether preview appears before final compare
- whether content is final compare buffer, source input, encoded material, encrypted material, or unknown

### C. Distinguish final compare buffer from transform material

The audit must explicitly answer:

1. Is `0x2559` just loading final compare buffer pointer?
2. Are `0x255f` and `0x2567` only reading string/BSTR metadata?
3. Does any observed preview look like:
   - UTF-16LE input?
   - Base64 text?
   - RC4 ciphertext / binary bytes?
   - final compare-side wide/binary buffer?
4. Does the observed buffer at `0x2559` already equal compare arg0?
5. Is there any earlier material pointer exposed through `[ebp-0x1168]`, `[ebp-0x116c]`, `eax`, or `edi` that is closer to transform material than final compare buffer?

### D. Relation to existing static Base64/RC4 discovery

Use `base64_rc4_static_point_discovery` only as reference, not as proof.

Known state:

- compare-producer hookable points exist.
- Base64 / RC4 / encrypted const / UTF-16LE construction points are still not instruction-confirmed.
- Therefore, do not run broad Base64/RC4 probe unless this material validation returns `ACCEPT`.

### E. Top-level classification

Top-level classification must be one of:

1. `ACCEPT`
   - at least one ESI-source hook is confirmed as transform material;
   - `breakpoint_probe_allowed = true`;
   - next action may be narrow Base64/RC4 breakpoint probe or transform material probe.

2. `BLOCKED_COMPARE_BUFFER_ONLY`
   - ESI-source hooks are final compare buffer / metadata only;
   - not enough to probe Base64/RC4;
   - next action moves earlier to producer of `[ebp-0x1170]`.

3. `BLOCKED_COPY_OR_HANDOFF_ONLY`
   - source is pointer copy/handoff;
   - next action should trace writer of `[ebp-0x1170]`, `[ebp-0x1168]`, or `[ebp-0x116c]`.

4. `BLOCKED_LENGTH_METADATA_ONLY`
   - observed hooks are only `[esi-8]` / `[esi-4]` length/metadata operations;
   - next action should move earlier.

5. `HOOK_COVERAGE_FAILED`

6. `INCONCLUSIVE`

Top-level fields:

- `classification`
- `candidate_count`
- `runtime_backed_count`
- `source_artifact`
- `validated_hooks`
- `blocked_hooks`
- `confirmed_transform_material_hooks`
- `compare_side_buffer_hooks`
- `metadata_only_hooks`
- `copy_or_handoff_hooks`
- `candidate_dependent_fields`
- `compare_lhs_connection`
- `breakpoint_probe_allowed`
- `next_bounded_action`

## 6. Implementation Scope

Allowed:

- Reuse existing `material_hook_runtime_validation` framework if present.
- Add a new bounded artifact if clearer:
  - `material_hook_runtime_validation_from_esi_source.json`
- Add one thin runtime script if necessary.
- Add project_state indexing for the new artifact if using a new name.
- Update negative cache so that if hooks are compare-buffer-only, Codex does not rerun the same validation unchanged.
- Update `codex_execution_report.md` with latest 2026-05-15 status.

Not allowed:

- no candidate generation
- no search expansion
- no broad Base64/RC4 probe before `ACCEPT`
- no full solve_reports scan
- no classifying metadata reads as transform material
- no treating `0x401b50` as transform material without new evidence
- no committing runtime output directories

## 7. Tests

Minimum compile checks:

```bat
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\function_semantics.py
```

If runtime script is touched or added:

```bat
python -m py_compile reverse_agent\olly_scripts\material_hook_runtime_validation.py
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
python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_material_from_esi_source_20260515_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled
```

Rebuild state:

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_material_from_esi_source_20260515_r1
python -m reverse_agent.project_state status
```

Required test coverage:

1. `ACCEPT`
   - transform material hook confirmed;
   - breakpoint gate allowed.

2. `BLOCKED_COMPARE_BUFFER_ONLY`
   - hook connects to compare arg0 but is final buffer only;
   - Base64/RC4 remains blocked.

3. `BLOCKED_COPY_OR_HANDOFF_ONLY`
   - hook copies pointer but does not produce transform material.

4. `BLOCKED_LENGTH_METADATA_ONLY`
   - hook only reads `[esi-8]` / `[esi-4]`.

5. `HOOK_COVERAGE_FAILED`
   - hook failures do not become semantic rejection.

6. project_state indexing
   - latest artifact appears in `current_state.json`;
   - bottleneck reason updates.

## 8. Stop Conditions

Stop and report if:

1. Material hook validation returns `ACCEPT`.
   - Report exact hook offset.
   - Report why it is transform material.
   - State next narrow probe: Base64/RC4 or transform material probe.

2. Hooks are compare-buffer-only.
   - Report that `0x2559 / 0x255f / 0x2567` are final compare-side buffer or metadata.
   - Next action: trace writer of `[ebp-0x1170]`.

3. Hooks are copy/handoff-only.
   - Report source slot/register.
   - Next action: trace upstream writer.

4. Hooks are metadata-only.
   - Report `[esi-8]` / `[esi-4]` meaning.
   - Move earlier.

5. Hook coverage fails.
   - Report address, boundary, timeout, UI/runtime error.

6. Tests fail.
   - Stop after collecting failure output.
   - Do not run harness until fixed.

本轮核心判断：`ESI source` 已经找到，且 gate 已从之前的 blocked 状态推进到可做 material validation。下一步不是搜索候选，也不是重复 ESI source audit，而是判断 `0x2559 / 0x255f / 0x2567` 到底是不是 transform material。如果是，进入窄 Base64/RC4 probe；如果不是，继续追 `[ebp-0x1170]` 的上游 writer。
