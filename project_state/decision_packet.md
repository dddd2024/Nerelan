# DECISION_PACKET

Generated: 2026-05-05

## 1. Goal

本轮目标：

```text
handoff_helper_dynamic_probe_for_samplereverse_compare_lhs
```

当前主线仍然是：

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

但上一轮已经确认：UTF-16LE expanded payload 可以从 compare-frame stack preview 中看到；compare-site 静态锚点也已经确认。当前不再需要重复 Base64/RC4 静态 access probe，也不应继续扩大候选搜索。

本轮目标是沿上一轮 `compare_stack_pivot_probe` 给出的精确 hook 点，捕获 compare lhs buffer 进入 `[ebp-0x1170]` 前后的真实运行时证据：

```text
module+0x1b50 enter
module+0x1b50 return / helper effect
module+0x2559 post_handoff_lhs_reload
```

成功标准不是新增更多候选，而是生成一个更近的运行时 artifact，回答：

```text
1. call 0x401b50 前，哪些参数/指针进入 handoff helper；
2. call 0x401b50 后，[ebp-0x1170] 指向哪里；
3. module+0x2559 处 esi 是否等于 compare lhs buffer；
4. compare lhs buffer 的 UTF-16LE/Base64/RC4 后数据是否能被完整 dump；
5. 能否从 helper enter/return 还原上游 buffer、长度、拷贝/转换关系。
```

---

## 2. Current Evidence

当前 active strategy：

```text
CompareAwareSearchStrategy
```

当前瓶颈：

```text
stage = compare_stack_pivot_probe
reason = compare_stack_pivot_complete
confidence = medium
```

当前最优候选：

```text
exact2:
candidate_hex = 78d540b49c59077041414141414141
candidate_prefix = 78d540b49c590770
compare_semantics_agree = true
runtime_ci_exact_wchars = 2
runtime_ci_distance5 = 246
source = pairscan

exact1 / frontier:
candidate_hex = 5a3e7f46ddd474d041414141414141
candidate_prefix = 5a3e7f46ddd474d0
compare_semantics_agree = true
runtime_ci_exact_wchars = 1
runtime_ci_distance5 = 258
source = exact2_seed -> refine(seed) -> guided(frontier)
```

上一轮 Codex 结论：

```text
classification = compare_stack_pivot_complete
candidates = 3
UTF-16LE stack payloads found = 3
static anchor = static_anchor_confirmed
compare call = RVA 0x258c
compare helper = RVA 0x1028ac, case_insensitive_wchar_compare
```

关键静态切片：

```text
0x253a: mov dword ptr [ebp - 0x1170], eax
0x2554: call 0x401b50
0x2559: mov esi, dword ptr [ebp - 0x1170]
0x2584: push 5
0x2586: push 0x551c4c
0x258b: push esi
0x258c: call 0x5028ac
```

上一轮测试结果：

```text
python -m pytest -q tests/test_compare_aware_search_strategy.py -> 78 passed
python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py -> 22 passed
python -m pytest -q -> 167 passed
```

证据来源：`task_packet.json`、`current_state.json`、`artifact_index.json` 和 `CODEX_EXECUTION_REPORT.md` 均指向同一条下一步：hook `module+0x1b50` 与 `module+0x2559`，捕获 handoff into `[ebp-0x1170]`。

---

## 3. Do Not Do

Codex 不要做：

```text
1. Do not return to old sample_solver blind search.
2. Do not only increase guided_pool beam or budget.
3. Do not increase topN, timeout, frontier iterations, or Copilot timeout.
4. Do not use compare_semantics_agree=false candidates as primary frontier.
5. Do not repeat exact2 basin value-pool evaluation.
6. Do not repeat H1/H3 fixed boundary candidate set.
7. Do not repeat current 5-candidate transform_trace_consistency audit without new runtime evidence.
8. Do not repeat scripted Base64/RC4 breakpoint probe before using compare stack pivot hook points.
9. Do not scan full solve_reports.
10. Do not commit full solve_reports directory.
11. Do not create a new broad candidate generator.
12. Do not treat exact2->exact3 as the required success condition for this round.
```

特别注意：

```text
compare_semantics_agree=false candidates are hard-blocked as primary frontier.
```

负面结果已经明确这些方向不可重复，尤其是 blind search、单纯扩大预算、compare_semantics_agree=false 主线、提交完整 solve_reports。

---

## 4. Files To Inspect

Codex 必须先读：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
```

重点代码文件：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_probe.py
reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py
reverse_agent/olly_scripts/pre_rc4_material_probe.py
reverse_agent/tool_runners.py
reverse_agent/project_state.py
reverse_agent/transforms/samplereverse.py
reverse_agent/profiles/samplereverse.py
```

本轮可以新增文件：

```text
reverse_agent/olly_scripts/compare_handoff_probe.py
```

或者在已有 probe 体系里新增：

```text
run_compare_handoff_probe()
```

只读必要 artifact：

```text
solve_reports/harness_runs/samplereverse_compare_stack_pivot_probe_20260505/summary.json
solve_reports/harness_runs/samplereverse_compare_stack_pivot_probe_20260505/run_manifest.json
solve_reports/harness_runs/samplereverse_compare_stack_pivot_probe_20260505/reports/tool_artifacts/samplereverse/compare_stack_pivot_probe/compare_stack_pivot_probe.json
```

不要默认读取：

```text
full PROJECT_PROGRESS_LOG.txt
full solve_reports directory
full historical harness runs
```

---

## 5. Required Audit

### A. 审计上一轮 compare stack pivot 结果

Codex 必须确认：

```text
1. compare call RVA 0x258c 是否仍然是当前二进制中的真实 compare call；
2. wide flag target VA 0x551c4c / RVA 0x151c4c 是否仍然有效；
3. module+0x2559 是否确实是 call 0x401b50 后第一处 reload [ebp-0x1170] 到 esi；
4. module+0x1b50 是否确实是 handoff/copy helper；
5. [ebp-0x1170] 在 0x253a、0x2554、0x2559 之间是否保持同一 slot；
6. compare lhs pointer、UTF-16LE payload、stack preview 三者是否可稳定关联。
```

输出要求：

```json
{
  "compare_stack_pivot_audit": {
    "compare_call_rva": "0x258c",
    "handoff_helper_rva": "0x1b50",
    "post_handoff_reload_rva": "0x2559",
    "lhs_slot": "[ebp-0x1170]",
    "static_anchor_valid": true,
    "reason": []
  }
}
```

### B. 实现 bounded handoff dynamic probe

新增或扩展 probe，名称建议：

```text
compare_handoff_probe
```

目标 hook 点：

```text
module+0x1b50 enter
module+0x1b50 return
module+0x2559 post_handoff_lhs_reload
```

每个 hook 至少记录：

```json
{
  "hook_name": "",
  "address": "module+0x...",
  "registers": {
    "eax": "",
    "ebx": "",
    "ecx": "",
    "edx": "",
    "esi": "",
    "edi": "",
    "esp": "",
    "ebp": ""
  },
  "stack_preview_hex": "",
  "lhs_slot_ptr": "",
  "lhs_buffer_preview_utf16le": "",
  "lhs_buffer_preview_hex": "",
  "candidate_hex": "",
  "candidate_prefix": "",
  "runtime_ci_exact_wchars": 0,
  "runtime_ci_distance5": 0
}
```

### C. 捕获 handoff 前后差异

Codex 必须对同一个 candidate 比较：

```text
before call 0x401b50
after call 0x401b50
after module+0x2559 reload
before compare call 0x5028ac
```

需要回答：

```text
1. eax 在 0x253a 写入 [ebp-0x1170] 前是什么；
2. call 0x401b50 是否修改 [ebp-0x1170] 指向的内容；
3. call 0x401b50 是否只是 copy/handoff，还是执行了 transform；
4. esi 在 0x2559 后是否稳定指向 compare lhs；
5. compare lhs buffer 是否包含完整 UTF-16LE payload 或最终 wide compare buffer；
6. 如果只看到 24/60 bytes，缺失部分是因为 stack preview 截断，还是 buffer 本身短。
```

### D. 产出 artifact

建议 artifact：

```text
solve_reports/.../tool_artifacts/samplereverse/compare_handoff_probe/compare_handoff_probe.json
```

必须包含：

```json
{
  "classification": "handoff_capture_complete | handoff_capture_partial | handoff_capture_failed",
  "candidate_count": 0,
  "runtime_backed_count": 0,
  "hook_results": {
    "handoff_helper_enter": "available | unavailable",
    "handoff_helper_return": "available | unavailable",
    "post_handoff_lhs_reload": "available | unavailable",
    "compare_lhs_buffer": "available | unavailable",
    "lhs_slot": "available | unavailable"
  },
  "handoff_observations": [],
  "next_bounded_action": ""
}
```

如果 hook 成功但无法得到更多 transform 证据，则下一步必须更窄地转向：

```text
backward slice from handoff helper arguments
```

而不是回到候选扩展。

---

## 6. Implementation Scope

允许做：

```text
1. 新增 compare_handoff_probe 脚本；
2. 在 CompareAwareSearchStrategy 中新增 run_compare_handoff_probe()；
3. 在 tool_runners/project_state 中索引 compare_handoff_probe artifact；
4. 增加 schema 测试；
5. 增加 no-promotion 测试，确保此 probe 不改变候选排名；
6. 运行一次 bounded harness；
7. 更新 project_state；
8. 更新 CODEX_EXECUTION_REPORT.md。
```

不允许做：

```text
1. 新 guided_pool；
2. 新 exact2 basin pool；
3. 新 blind search；
4. 扩大 beam/budget/topN/timeout；
5. 大范围 solve_reports 扫描；
6. 把 compare_semantics_agree=false 候选作为主线；
7. 提交 solve_reports 全目录；
8. 只写自然语言报告而没有机器可读 artifact。
```

---

## 7. Tests

最低测试：

```bash
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py
python -m pytest -q
```

新增或更新测试：

```text
test_compare_handoff_probe_schema
test_compare_handoff_probe_records_hook_points
test_compare_handoff_probe_records_lhs_slot
test_compare_handoff_probe_records_post_handoff_reload
test_compare_handoff_probe_does_not_promote_candidates
test_compare_handoff_probe_does_not_expand_search_budget
test_project_state_indexes_compare_handoff_probe
```

建议 bounded harness：

```powershell
python -m reverse_agent.harness --dataset .\samplereverse_exact1_projected_vs_neighbor_20260424.json --run-name samplereverse_compare_handoff_probe_20260505 --reports-dir solve_reports --analysis-mode "Auto" --model-type "Copilot CLI" --copilot-timeout-seconds 300 --ctf-skill-profile compact --case-id samplereverse-exact1-projected-vs-neighbor --no-resume
```

然后更新 project_state：

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name samplereverse_compare_handoff_probe_20260505
python -m reverse_agent.project_state status
```

---

## 8. Stop Conditions

立即停止并报告：

```text
1. 需要回到 blind search；
2. 需要扩大 beam / budget / topN / timeout；
3. 需要重复 exact2 value-pool；
4. 需要重复 H1/H3 boundary set；
5. 需要重复 current transform_trace_consistency；
6. 需要重复旧 Base64/RC4 static access breakpoint probe；
7. 需要全量扫描 solve_reports；
8. 只能依赖 compare_semantics_agree=false candidate；
9. hook module+0x1b50 / module+0x2559 在当前二进制中无法命中；
10. 目标二进制、调试器或 Frida/Olly 环境不可用。
```

成功停止条件：

```text
1. 生成 compare_handoff_probe.json；
2. project_state 能索引 compare_handoff_probe；
3. 明确记录 module+0x1b50 enter/return 与 module+0x2559 的 runtime 状态；
4. 明确说明 [ebp-0x1170]、eax、esi、compare lhs buffer 的关系；
5. 全部测试通过；
6. CODEX_EXECUTION_REPORT.md 给出下一步二选一：
   a. 若捕获到完整 handoff buffer，转向 buffer-level byte constraint；
   b. 若只捕获到 partial buffer，转向 handoff helper backward slice；
   c. 若 hook 不命中，返回静态地址校验，不扩大搜索。
```

---

## GPT Decision Summary

当前最关键的信息是：上一轮已经把问题从“找不到 construction point”推进到“compare lhs handoff 点已定位”。因此下一轮不应再做静态 Base64/RC4 大方向定位，也不应继续搜候选。

最合理的下一步是：

```text
实现 compare_handoff_probe，hook module+0x1b50 与 module+0x2559，捕获 [ebp-0x1170] 前后变化。
```

这一步的价值在于把现在的黑盒链路：

```text
UTF-16LE/Base64/RC4 -> compare lhs
```

进一步拆成可观察的运行时 buffer 关系。只有确认 handoff helper 是否修改、复制或转换 lhs buffer，后面才有条件做 byte-level 逆推，而不是继续盲目扩展候选。
