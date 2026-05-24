```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260524_reverse_arg0_pointer_origin_trace",
  "round_id": "round_20260524_reverse_arg0_pointer_origin_trace",
  "based_on_state_build_id": "state_20260524_155155_c3441de6ffe8",
  "based_on_state_digest": "c3441de6ffe8a5f84b665dcc35dc25a487bb1f5e491d50f78d75c713ae0b64c2",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续**逆向解题主线**，不是工程架构改造支线。当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`，不是 `task_packet.task` 或 `task_packet.derived_task`。

上一轮已经把 `raw_writes_not_intersecting_arg0` 归因为更具体的 `arg0_pointer_origin_untracked`。当前已知：actual compare `arg0` 是 runtime-backed、candidate-dependent 的真实 LHS；但当前 write monitor 捕获到的 raw writes 没有覆盖 actual compare `arg0` 指向的 buffer。因此本轮不再继续给 raw-write gap 增加分类字段，而是做最小 bounded pointer-origin trace。

## 1. Goal

本轮目标：为 `module+0x258c` actual compare `arg0` 建立最小 runtime-backed pointer-origin 证据。

具体目标：

```text
1. 从 current project_state 确认当前 blocker 是 arg0_pointer_origin_untracked。
2. 只基于 freshness=current 的 compare_real_lhs_provenance_audit artifact 和 selected run sr_lhs_hook_observation_reliability_20260524_r4 建立下一步诊断。
3. 新增或扩展一个 bounded diagnostic，用于追踪 0x258c 前 actual compare arg0 pointer 的来源，而不是继续解释 raw writes 为什么不相交。
4. 最小 hook 范围优先限定在 0x2559..0x258c 的 ESI / stack / push-arg0 窗口：
   - module+0x2559: reload before compare-side window
   - module+0x258b: push esi / compare arg0 preparation
   - module+0x258c: wide compare call / actual arg0 confirmation
5. 如静态指令边界或 existing sidecar 显示 0x2559 的 source slot 不可靠，不得复用旧 [ebp-0x1170] 作为结论；只能记录 observed slot/value relation。
6. 输出每个 candidate 的 arg0 pointer origin trace：
   - actual_arg0 at 0x258c
   - ESI value immediately before push/call
   - any stack slot / register value loaded into ESI in the bounded window
   - whether that value equals actual_arg0
   - whether the source is candidate-dependent
   - whether the observed source is a pointer alias, final writer, or still only a pointer carrier
7. 如果可以确定 pointer carrier 但不能确定 final data writer，则明确分类为 pointer_carrier_identified_writer_missing，不得伪称 final writer 已找到。
8. 更新 project_state projection，使 blocker 从 arg0_pointer_origin_untracked 进一步细化为可审计状态，例如：
   - arg0_pointer_carrier_identified
   - arg0_pointer_carrier_identified_writer_missing
   - arg0_pointer_source_slot_unstable
   - arg0_pointer_origin_trace_schema_gap
```

本轮不求最终 flag，不做 candidate search，不扩大 frontier，不扩大 runtime budget。

## 2. Current Evidence

当前主线：**reverse_solving**。

当前 project_state 基础：

```text
state_build_id = state_20260524_151823_940c73e97585
based_on_state_digest = 940c73e97585b6f5613da67ec913a1fe2a2d5d6d46a9fa067c7254e8978acca2
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
current_bottleneck.blocker = arg0_pointer_origin_untracked
```

`task_packet.task` / `task_packet.derived_task` 仍是 `Improve compare lhs last-writer instrumentation`，但它只是派生建议。当前轮权威是本 `decision_packet.md`。

当前 artifact freshness：

```text
latest_harness_run = sr_lhs_hook_observation_reliability_20260524_r4
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_lhs_hook_observation_reliability_20260524_r4
latest_artifacts_v2.compare_probe.freshness = current
latest_artifacts_v2.run_manifest.freshness = current
latest_artifacts_v2.summary.freshness = current
```

当前 compare_real_lhs_provenance_audit 关键结论：

```text
classification = compare_lhs_runtime_backed_writer_missing
runtime_backed_count = 3
actual_compare.lhs_side = arg0
actual_compare.flag_side = arg1
actual_compare.arg0_candidate_dependent = true
actual_compare.arg1_candidate_dependent = false
actual_compare.entry = 0x258c
write_monitor_health.enabled = true
write_monitor_health.raw_write_count = 27
write_monitor_health.filtered_intersecting_write_count = 0
last_writer_summary.raw_write_event_count = 27
last_writer_summary.retained_write_count = 0
last_writer_summary.connects_to_actual_arg0 = false
last_writer_candidates = []
raw_write_gap_summary.blocker = arg0_pointer_origin_untracked
```

当前 actual compare evidence：

```text
candidate 78d540b49c59077041414141414141 -> actual_arg0 = 0x35cd018
candidate 5a3e7f46ddd474d041414141414141 -> actual_arg0 = 0x378cfd8
candidate 78d540b49c59076f41414141414141 -> actual_arg0 = 0x421d018
actual_arg0 preview varies by candidate
actual_arg1 = 0x1141c4c and is not candidate-dependent
```

当前已排除事项：

```text
旧 [ebp-0x1170] 已被 current artifact 拒绝为真实 LHS source。
compare_probe fallback 只能证明 actual arg0/arg1，不是 writer provenance。
raw writes 存在，但都不 intersect actual arg0 window。
Base64/RC4 breakpoint probe 仍被禁止，直到 runtime-backed real LHS producer 被识别。
```

当前 skill_profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

## 3. Do Not Do

不要做以下事情：

```text
不要继续工程支线或 Phase 2 skill 改造。
不要修改 .codex-skills/、registry、sync 或 audit 工具。
不要默认读取完整 solve_reports/。
不要默认读取 PROJECT_PROGRESS_LOG.txt。
不要运行 Base64/RC4 breakpoint probe。
不要运行 Base64/RC4 probe 的任何变体。
不要回 old sample_solver blind search。
不要扩大 beam / topN / budget / timeout / frontier iteration。
不要新增 candidate search。
不要把 compare_semantics_agree=false candidates 作为 primary frontier。
不要提交完整 solve_reports。
不要把 stale / missing artifact 当 current evidence。
不要把 compare_probe fallback args 当 writer provenance。
不要复用旧 [ebp-0x1170] 作为真实 LHS source，除非本轮产生新的 runtime-backed provenance 并解释为什么旧 rejection 不再适用。
不要把 0x4019e0、0x401b50、0x4018cd、0x401be3 直接称为 Base64/RC4 producer，除非本轮产生新的语义证据。
不要为了推进而伪造 final writer。
不要继续只添加 blocker 命名字段而不产生新的 pointer-origin evidence。
```

必须遵守 `project_state/negative_results.json`，尤其是：

```text
old sample_solver blind search
only increase guided_pool beam or budget
use compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
rerun Base64/RC4 breakpoint probe before confirming a Base64/RC4 instruction hook
repeat producer material confirmation without adding instruction-level evidence
reuse old [ebp-0x1170] without real-lhs provenance evidence
run Base64/RC4 breakpoint probe before real lhs producer identification
```

## 4. Files To Inspect

必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界读取的 artifact：

```text
project_state/artifact_index.json 中 latest_artifacts_v2["compare_real_lhs_provenance_audit"].path
```

可有界读取：

```text
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/summary.json
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/run_manifest.json
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/case_results/samplereverse-compare-producer-backtrace.json
```

仅当需要确认 instruction boundary 或 current sidecar hook layout 时，才允许有界读取相关 Olly sidecar 输出片段。不要扫描完整 `solve_reports/`。

不要默认读取：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
历史 rounds 下的完整大文件
.codex-skills/**
```

## 5. Required Audit

Codex 修改前必须完成并在 report 中记录：

```text
1. 确认本 decision_meta：decision_id=decision_20260524_reverse_arg0_pointer_origin_trace，status=APPROVED，mainline=reverse_solving。
2. 确认 skill_profiles 为 reverse-agent-iteration@v2 和 samplereverse-frontier@v2。
3. 确认 task_packet.task / derived_task 只是派生建议，当前执行权威是 decision_packet.md。
4. 确认 artifact_index.latest_artifacts_v2.compare_real_lhs_provenance_audit 的 freshness=current，source_run=sr_lhs_hook_observation_reliability_20260524_r4。
5. 有界读取 current compare_real_lhs_provenance_audit artifact。
6. 复核上一轮 gap 结论：raw writes 存在，但不 intersect actual arg0 window。
7. 审计 compare_pre_compare_handoff_target_probe.py 当前 hook 是否已经能观察：0x2559、0x258b、0x258c、ESI、stack slot、actual compare arg0。
8. 审计 compare_aware_search.py 当前 projection 是否能容纳 pointer-carrier 与 final-writer 的区别。
9. 判断最小新增 runtime evidence 应来自：
   - 现有 artifact 重新聚合即可；
   - sidecar schema 扩展但无需 harness；
   - sidecar schema 扩展且需要一次 bounded harness rerun。
10. 确认本轮没有运行 Base64/RC4 probe、old solver、candidate search、beam/budget 扩张。
```

报告中必须明确回答：

```text
actual compare arg0 在 0x258c 前由哪个 register/slot 携带？
这个 carrier 是否 runtime-backed？
这个 carrier 是否等于 final writer？如果不是，缺口是什么？
是否仍然需要下一轮追 data writer？
为什么本轮不是 Base64/RC4 probe？
```

## 6. Implementation Scope

### Phase A：只读 pointer-origin feasibility audit

先不改代码，先根据 current artifact 和现有 sidecar 代码判断是否已经能从现有字段恢复：

```text
0x258c actual arg0
0x258b pre-push ESI
0x2559 reload target/source
stack slot value if present
source slot address if present
candidate-dependence relation
```

如果现有 artifact 缺字段，记录 schema gap，不要猜。

### Phase B：最小 sidecar schema 扩展

如果现有 artifact 不足，允许最小修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
```

新增诊断字段应集中在一个 bounded section，例如：

```text
arg0_pointer_origin_trace
```

建议字段：

```text
candidate_hex
actual_arg0_at_compare
pre_compare_esi_value
pre_compare_esi_equals_arg0
reload_site
reload_source_kind
reload_source_address
reload_source_value
reload_source_equals_arg0
carrier_candidate_dependent
carrier_relation
pointer_origin_status
pointer_origin_gap_reason
recommended_next_hook_points
```

允许的状态值：

```text
carrier_identified
carrier_identified_writer_missing
source_slot_unstable
source_slot_rejected
schema_gap
not_observed
```

严格区分：

```text
pointer carrier: 指针从哪里被带到 compare arg0。
final data writer: 谁写入 actual arg0 指向的 buffer 内容。
```

本轮可以只证明 pointer carrier，不能把 carrier 伪称为 final data writer。

### Phase C：strategy aggregation / artifact projection

如新增 sidecar 字段，允许最小更新：

```text
reverse_agent/strategies/compare_aware_search.py
```

目标：将 `arg0_pointer_origin_trace` 聚合进 `compare_real_lhs_provenance_audit`，并保留旧 artifact 兼容。

必须保持：

```text
compare_probe fallback 不得升级为 writer provenance。
old [ebp-0x1170] rejection 不得被无条件覆盖。
last_writer_candidates 只有在真实 writes intersect actual arg0 时才能填充。
```

### Phase D：project_state 投影

如新增稳定分类，允许最小更新：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

目标是把 blocker 从 `arg0_pointer_origin_untracked` 进一步投影为更具体状态，例如：

```text
arg0_pointer_carrier_identified
arg0_pointer_carrier_identified_writer_missing
arg0_pointer_source_slot_unstable
arg0_pointer_origin_trace_schema_gap
```

不要把动态 run name、candidate、artifact path、freshness 或 runtime metric 写入 `.codex-skills/`。

### Phase E：bounded harness rerun

默认不运行 harness。只有满足以下条件才允许一次 bounded harness rerun：

```text
1. sidecar schema 已经最小扩展；
2. unit/fixture test 无法验证 runtime字段；
3. rerun 不扩大 candidate set、budget、timeout、beam 或 frontier；
4. rerun 不触发 Base64/RC4 probe。
```

如必须运行，run-name 必须是新的、明确的：

```text
sr_arg0_pointer_origin_trace_20260524_r1
```

限制：

```text
只使用当前 samplereverse sample。
只使用当前 fixed candidates / current strategy。
不得扩大 beam / topN / budget / timeout。
不得运行 Base64/RC4 probe。
不得提交完整 solve_reports。
```

### Phase F：报告与状态

本轮结束必须更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果 project_state 派生逻辑或 artifact schema 有变化，运行：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <selected_or_new_run_name>
```

如没有运行 harness，必须说明仍基于 selected run `sr_lhs_hook_observation_reliability_20260524_r4`，并说明没有产生新的 runtime artifact。

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or pointer or raw_write or last_writer or provenance or classification"
python -m pytest -q tests/test_project_state.py -k "artifact or provenance or bottleneck or decision or report or pointer"
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果修改了 `reverse_agent/project_state.py`，必须补充：

```bash
python -m pytest -q tests/test_project_state.py
```

如果修改了 sidecar 或 artifact schema，必须补充至少一个不依赖真实 harness 的 fixture/unit test，覆盖：

```text
actual arg0 is runtime-backed at 0x258c
pre-compare ESI carries actual arg0
pointer carrier is identified but final writer is still missing
old [ebp-0x1170] is not promoted unless runtime evidence supports it
compare_probe fallback must not promote writer provenance
raw writes exist but do not intersect actual arg0 window
```

如果运行 project_state build，必须补充：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <selected_or_new_run_name>
```

如果运行 harness，必须记录完整命令和 run-name，并说明为什么单元测试不足。

不需要运行：

```bash
full unrelated pytest suite
Base64/RC4 breakpoint probe
old sample_solver
full solve_reports scan
PROJECT_PROGRESS_LOG read
```

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. compare_real_lhs_provenance_audit artifact 缺失或 freshness 不是 current。
2. current artifact 与 current_state 的 bottleneck/blocker 冲突，且无法解释。
3. 必须读取完整 solve_reports 才能继续。
4. 必须读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
5. 必须运行 Base64/RC4 probe、old solver、beam/budget 扩张或 candidate search 才能继续。
6. 无法区分 actual compare arg0 evidence、pointer carrier 和 final writer provenance。
7. 需要新增大范围 memory scan / global hook 才能继续。
8. 需要修改 .codex-skills 或 registry 才能继续。
9. 测试无法运行且没有环境原因。
10. 代码改动会把 stale/missing artifact 当 current evidence。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_reverse_arg0_pointer_origin_trace",
  "round_id": "round_20260524_reverse_arg0_pointer_origin_trace",
  "based_on_decision_id": "decision_20260524_reverse_arg0_pointer_origin_trace",
  "status": "SUCCESS / PARTIAL / FAILED / BLOCKED",
  "acceptance_recommendation": "ACCEPTED / NEEDS_REVIEW / REWORK_REQUIRED / BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [],
  "next_suggested_task": []
}
```

报告正文必须包含：

```text
1. current artifact path/source_run/freshness。
2. current actual arg0 values and preview relation by candidate。
3. 0x2559..0x258c pointer-origin trace table。
4. pointer carrier 与 final writer 的区分结论。
5. 是否新增 sidecar 字段；如果新增，字段和理由。
6. 是否运行 harness；默认应为 no，除非 sidecar runtime field 必须验证。
7. 是否产生新 artifact；如没有，说明仍基于 current selected run。
8. 真实测试命令和结果。
9. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- current artifact freshness 被正确核验。
- actual arg0 pointer carrier 被 runtime-backed 证据解释，或明确证明 schema gap。
- pointer carrier 与 final writer provenance 被严格区分。
- 如果有代码变更，测试覆盖旧 artifact 兼容和新字段投影。
- 未运行禁止 probe，未扩大搜索。
- tests 通过。

ACCEPTED_WITH_LIMITATIONS：
- 完成 pointer-origin trace schema 或静态/现有 artifact 审计，但没有运行 harness 或没有 final data writer。
- 结论能指导下一轮 bounded writer hook，而不是回到旧 solver/RC4/Base64。

REWORK_REQUIRED：
- 把 stale artifact 当 current evidence。
- 把 compare_probe fallback 当 writer provenance。
- 把 pointer carrier 伪称为 final writer。
- 未读取 current artifact 就修改分类逻辑。
- 运行 Base64/RC4 probe、old solver 或扩大搜索预算。
- codex_report_summary.based_on_decision_id 不匹配。

BLOCKED：
- current artifact 缺失且无法 rebuild。
- project_state 与 artifact_index 严重冲突。
- 必要测试无法运行。
```
