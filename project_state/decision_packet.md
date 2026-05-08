# DECISION_PACKET

## 1. Goal

把当前瓶颈从“重复运行 Base64/RC4 breakpoint probe”转为“定位可 hook 的 Base64/RC4 构造点”。

当前 probe 已经能打到 `compare_buffer`，但 `utf16le_payload / base64_input / base64_output / rc4_key / rc4_input / rc4_output` 全部 unavailable；静态发现只找到每类 1 个 unresolved point，且 `hookable_count=0`。因此下一轮目标不是继续搜索候选，而是补强或人工确认静态点发现逻辑，产出可用于断点捕获的 `module_offset` / instruction address。

## 2. Current Evidence

- 当前 active strategy 是 `CompareAwareSearchStrategy`，主线仍是 `L15(prefix8)`。已知 transform 链路是 `input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`。
- 当前 best exact2 仍是 `78d540b49c59077041414141414141`，`runtime_ci_exact_wchars=2`，`runtime_ci_distance5=246`，且 `compare_semantics_agree=true`。frontier/exact1 是 `5a3e7f46ddd474d041414141414141`，`runtime_ci_exact_wchars=1`，`distance5=258`。
- 最新 `base64_rc4_breakpoint_probe` 的 classification 是 `base64_rc4_static_points_unavailable`。3 个候选都有 runtime backing，也有 3 个 hook events，但 first captured material 只有 `compare_buffer`。
- artifact index 显示本轮已有 `base64_rc4_breakpoint_probe`、`transform_trace_consistency`、`profile_transform_hypothesis_matrix` 等 artifact，但 `case_results` 和 `summary` 缺失。
- Codex 上一轮报告确认：breakpoint fallback 对 3 个 diagnostic candidates 都命中了 compare hook，但 Base64/RC4 构造点不可用；下一步应定位 hookable Base64/RC4 construction addresses，而不是扩 candidate search。

## 3. Do Not Do

- Do not return to old `sample_solver` blind search.
- Do not only increase guided pool beam, budget, topN, timeout, or frontier iteration limits.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports` directory.
- Do not repeat exact2 basin value-pool evaluation with pools `0:78 1:d5/3e/3c 2:40/7f/80 3:b4/8f 4:9c`.
- Do not repeat fixed H1/H3 8-candidate Base64 boundary contrast set.
- Do not repeat current 5-candidate transform trace consistency audit without new runtime evidence.
- Do not rerun scripted Base64/RC4 breakpoint probe with the same current static access points. Negative results already mark that route as nonproductive.

## 4. Files To Inspect

Inspect first:

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_tool_runners.py
tests/test_project_state.py
```

Inspect artifact only as needed, not full `solve_reports`:

```text
solve_reports\harness_runs\samplereverse_base64_rc4_breakpoint_probe_20260507\reports\tool_artifacts\samplereverse\base64_rc4_breakpoint_probe\base64_rc4_breakpoint_probe.json
solve_reports\harness_runs\samplereverse_base64_rc4_breakpoint_probe_20260507\reports\tool_artifacts\samplereverse\profile_transform_hypothesis_matrix.json
```

## 5. Required Audit

Before implementing anything, Codex must audit:

1. Where `base64_rc4_breakpoint_probe.py` generates or consumes static points.
2. Why static discovery reports exactly one point for each family but `hookable_count=0`.
3. Whether the unresolved points contain enough evidence to map to:
   - file offset,
   - RVA,
   - module offset,
   - function address,
   - instruction address,
   - call site,
   - or compare-site producer.
4. Whether Base64/RC4 logic is inline, library-like, table-driven, or compiler-optimized.
5. Whether the current probe is searching for the wrong layer:
   - Base64 encoder call,
   - Base64 output buffer,
   - RC4 KSA state initialization,
   - RC4 PRGA loop,
   - encrypted const load,
   - compare buffer producer.
6. Whether IDA/x64dbg/manual disassembly is required because the automated static detector cannot safely infer hook points.

## 6. Implementation Scope

### A. Add a bounded static-point discovery improvement

Implement or repair a narrow static discovery pass that produces a compact JSON artifact with entries like:

```json
{
  "kind": "base64_output | rc4_ksa | rc4_prga | rc4_input | rc4_output | encrypted_const | compare_producer",
  "module_offset": "0x...",
  "rva": "0x...",
  "function": "0x...",
  "instruction": "0x...",
  "hookable": true,
  "confidence": "low | medium | high",
  "evidence": [
    "nearby constant",
    "loop shape",
    "xref from compare",
    "buffer write before compare",
    "RC4 S-box 256-byte permutation pattern"
  ]
}
```

The output must distinguish:

- found but not hookable,
- hookable but untested,
- hookable and instruction-confirmed,
- ambiguous and requiring manual IDA/x64dbg confirmation.

### B. Do not immediately rerun the breakpoint probe

Only rerun `base64_rc4_breakpoint_probe` after the static discovery pass produces at least one instruction-confirmed `hookable=true` point for Base64 or RC4.

If no hookable point is produced, stop and report `static_point_discovery_failed` with the unresolved evidence.

### C. Keep the candidate set fixed

If rerun is allowed, use only the existing bounded diagnostic set:

```text
78d540b49c59077041414141414141
78d540b49c59077040414141414141
5a3e7f46ddd474d041414141414141
```

No new beam, no new guided pool, no wider frontier expansion.

### D. Update project_state compactly

Expose only compact evidence:

```text
latest_static_point_discovery.artifact
latest_static_point_discovery.hookable_count
latest_static_point_discovery.by_kind
latest_static_point_discovery.best_points
latest_static_point_discovery.next_bounded_action
```

Do not commit bulky runtime artifacts.

## 7. Tests

Minimum tests:

```powershell
python -m py_compile reverse_agent\olly_scripts\base64_rc4_breakpoint_probe.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py
python -m pytest -q
```

Add or update tests to verify:

```text
- static discovery output schema
- hookable_count aggregation
- project_state compact rendering
- no candidate ranking change
- no beam/budget/search expansion
- no rerun of breakpoint probe unless hookable=true instruction-confirmed points exist
```

Only after hookable points exist, run the bounded harness/probe again.

## 8. Stop Conditions

Stop and report immediately if any condition occurs:

1. Static discovery produces zero hookable Base64/RC4 points.
2. Static discovery produces hookable points but no instruction-level evidence.
3. Base64/RC4 logic appears inline/optimized and cannot be safely hooked by current automation.
4. Manual IDA/x64dbg confirmation is required.
5. Rerun captures any of:
   - `utf16le_payload`
   - `base64_input`
   - `base64_output`
   - `rc4_key`
   - `rc4_input`
   - `rc4_output`
   - `compare_buffer`
6. Candidate ranking changes unexpectedly.
7. Any candidate reaches exact3+ or improves beyond current exact2 / distance5 baseline.
8. Codex would need to scan full `solve_reports` or expand search budget to proceed.

## Expected Codex Output

Codex should produce:

```text
project_state/codex_execution_report.md
updated project_state/current_state.json
updated project_state/artifact_index.json
updated/added tests
optional static-point discovery artifact reference
```

The report must explicitly classify the next bottleneck as one of:

```text
static_point_discovery_failed
manual_disassembly_required
hookable_points_found
breakpoint_probe_ready
base64_material_captured
rc4_material_captured
compare_only_capture
runtime_execution_failure
```

核心判断：**下一轮不是“继续找候选”，而是“把 Base64/RC4 的可断点位置找准”。**
