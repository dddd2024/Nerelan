```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_bounded_symbolic_execution_v1",
  "round_id": "round_20260603_local_reverse_bounded_symbolic_execution_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 `local_reverse_simple_training`，从上一轮 **bounded semantic rule extraction v1** 推进到 **bounded symbolic execution over semantic windows v1**。

上一轮已经完成：

```text
1. 新增 reverse_agent/local_reverse_semantic_rules.py。
2. 只处理 3 个指定 ready_static_string_compare 目标。
3. 从已有 disassembly_windows 提取 semantic_rules=60。
4. 基于 semantic rules 生成并验证候选 45 个。
5. 三个样本仍 solved=false。
```

上一轮 blocker 已推进为：

```text
needs_symbolic_execution
```

这说明继续扩大候选、扩大 xref、扩大 disassembly window 没有意义。本轮不得继续写普通候选生成器。本轮要在已有 semantic_rules 基础上实现小型、可审计、强约束的 symbolic state executor：组合 stack buffer、loop bound、byte transform、cmp constant、replacement rule，导出完整输入约束，再生成候选并 runtime 验证。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。旧 `task_packet.json` 中的 `samplereverse` 字段仍只作为旧状态背景，不能覆盖本 decision。

---

## 1. Goal

本轮目标是实现第一版 **bounded symbolic execution over semantic windows**，把上一轮独立的 semantic rules 组合成可求解约束。

核心目标：

```text
1. 只处理上一轮 3 个 unsolved 目标：
   - 4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
   - bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
   - 18019fca52b389fe -> 逆向课程2024春01/sha_256.exe

2. 读取 project_state/local_reverse_semantic_rule_result.json。

3. 对每个目标从 semantic_rules 建立 bounded symbolic model：
   - symbolic input bytes: input[i]
   - stack buffer aliases: [ebp - offset]
   - loop variable and loop bound
   - byte transform chain: add/sub/xor
   - cmp immediate constraints
   - replacement rules
   - success/failure branch hints

4. 只支持简单线性 byte-level 规则，不做完整二进制符号执行。

5. 如果能导出完整或部分约束，生成少量候选输入。
   默认每个样本最多 12 个候选。

6. 使用已有 runtime harness 验证候选。
   默认每个样本最多 12 次验证。

7. 输出 project_state/local_reverse_symbolic_execution_result.json。

8. 如果仍未 solved，输出更具体 missing_evidence：
   - symbolic_model_incomplete
   - loop_body_not_reconstructed
   - constraint_conflict
   - branch_condition_unresolved
   - requires_ida_decompiler_summary
   - requires_manual_address_seed
```

本轮不是重做 xref/disassembly，不是重做 semantic extraction，不是接 GUI，不是处理 22 个样本，不是无界 brute force。

---

## 2. Current Evidence

当前主线：

```text
reverse_solving / local_reverse_simple_training
```

上一轮有效输入产物：

```text
project_state/local_reverse_semantic_rule_result.json
```

上一轮结果摘要：

```text
status=PARTIAL
target_count=3
solved_count=0
semantic rules extracted=60
semantic candidate validations=45
```

上一轮三个目标状态：

```text
18019fca52b389fe -> semantic_rule_count=20, generated_candidate_count=20, validated_candidate_count=20, solved=false, missing_evidence=needs_symbolic_execution
4c69f173f2bd0211 -> semantic_rule_count=20, generated_candidate_count=13, validated_candidate_count=13, solved=false, missing_evidence=needs_symbolic_execution
bcbd9979db015bfd -> semantic_rule_count=20, generated_candidate_count=12, validated_candidate_count=12, solved=false, missing_evidence=needs_symbolic_execution
```

关键正向证据：

```text
sha_256.exe 已识别出：
- loop_bound: cmp dword ptr [ebp - 0x450], 0x40 / jge 0x401ee4
- byte_load: mov cl, byte ptr [ebp + eax - 0x44]
- byte_add_const: add cl, 1
- byte_cmp_const / replacement-related rules
```

但上一轮候选生成仍停留在重复字符，例如 `00000`、`11111`、`AAAAA`，没有把多个规则组合成完整输入约束。因此本轮需要 symbolic state composition。

Artifact freshness 判断：

```text
1. project_state/local_reverse_semantic_rule_result.json 是本轮直接输入证据。
2. project_state/local_reverse_xref_disassembly_result.json 是辅助证据，只在 semantic result 不足时有界读取摘要。
3. project_state/local_reverse_corpus_index.json 提供 sha256 / relative_path / artifact_role。
4. project_state/local_reverse_runtime_policy.json 提供 runtime policy。
5. samplereverse artifacts 只能作为旧背景，不得用于本轮 local reverse 证据。
```

---

## 3. Do Not Do

严禁：

```text
1. 不重新实现 local_reverse_string_solver.py。
2. 不重新实现 local_reverse_compare_site.py。
3. 不重新实现 local_reverse_xref_disassembly.py。
4. 不重新实现 local_reverse_semantic_rules.py。
5. 不重跑上一轮 90 个 compare-site candidates。
6. 不重跑上一轮 6 个 xref candidates。
7. 不重跑上一轮 45 个 semantic candidates，除非 symbolic model 给出新的 revalidation reason。
8. 不继续扩大候选池。
9. 不继续扩大 xref 搜索窗口。
10. 不继续扩大 disassembly window。
11. 不对 22 个样本全量求解。
12. 不处理 3 个目标之外的 challenge binary。
13. 不做无界 brute force。
14. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
15. 不回旧 sample_solver 盲搜。
16. 不读取完整 solve_reports/。
17. 不读取完整 PROJECT_PROGRESS_LOG.txt。
18. 不提交 E:\reverse 下的二进制样本。
19. 不把 E:\reverse 样本复制进 Git 仓库。
20. 不把样本二进制转成 base64 或 hex 提交。
21. 不修改 .codex-skills/。
22. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
23. 不建设重型 agent 平台。
24. 不伪造 solved=true。
25. 不把本轮扩展为 GUI 前端整合。
```

允许：

```text
1. 读取 project_state/local_reverse_semantic_rule_result.json。
2. 有界读取 project_state/local_reverse_xref_disassembly_result.json 的对应目标摘要，用于补充 source_window/address 信息。
3. 新增 reverse_agent/local_reverse_symbolic_execution.py。
4. 新增 tests/test_local_reverse_symbolic_execution.py。
5. 建立 pattern-based symbolic state，不要求完整 CPU/内存模型。
6. 支持 byte-level add/sub/xor 逆变换。
7. 支持 loop_bound 推断候选长度。
8. 支持 replacement_rule 约束合并。
9. 生成最多 12 个 symbolic-derived candidates 并 runtime 验证。
10. 输出 project_state/local_reverse_symbolic_execution_result.json。
```

---

## 4. Files To Inspect

默认读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
project_state/local_reverse_corpus_index.json
project_state/local_reverse_runtime_policy.json
project_state/local_reverse_semantic_rule_result.json
project_state/local_reverse_xref_disassembly_result.json
README.txt
```

必须检查：

```text
reverse_agent/local_reverse_runtime.py
reverse_agent/local_reverse_semantic_rules.py
reverse_agent/local_reverse_xref_disassembly.py
tests/test_local_reverse_runtime.py
tests/test_local_reverse_semantic_rules.py
tests/test_local_reverse_xref_disassembly.py
```

允许新增：

```text
reverse_agent/local_reverse_symbolic_execution.py
tests/test_local_reverse_symbolic_execution.py
project_state/local_reverse_symbolic_execution_result.json
```

不要默认读取：

```text
solve_reports/
PROJECT_PROGRESS_LOG.txt
```

---

## 5. Required Audit

Codex 必须审计并写入 `project_state/codex_execution_report.md`：

```text
1. 当前 decision_packet 是执行权威。
2. 上一轮 semantic_rule_result 已完成但 solved_count=0，本轮不是重跑普通候选。
3. 本轮 mainline=reverse_solving，具体方向=local_reverse_bounded_symbolic_execution_v1。
4. 只处理 3 个指定 unsolved ready_static_string_compare 样本。
5. 未处理 3 个指定样本之外的 challenge binary。
6. 未运行 E:\reverse 之外的 exe。
7. 未复制、提交、上传或编码任何样本二进制。
8. 未修改 .codex-skills/。
9. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
10. symbolic execution 是有界的，有 max rules / max states / max candidates / max validations 限制。
11. 如果产生新候选并验证，必须记录 symbolic model source 和 runtime evidence。
12. 如果仍未 solved，必须输出更具体 missing_evidence。
13. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_bounded_symbolic_execution_v1",
  "round_id": "round_20260603_local_reverse_bounded_symbolic_execution_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_bounded_symbolic_execution_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 新增 bounded symbolic execution 模块

新增：

```text
reverse_agent/local_reverse_symbolic_execution.py
```

建议 CLI：

```bash
python -m reverse_agent.local_reverse_symbolic_execution ^
  --corpus-index project_state\local_reverse_corpus_index.json ^
  --semantic-result project_state\local_reverse_semantic_rule_result.json ^
  --xref-result project_state\local_reverse_xref_disassembly_result.json ^
  --policy project_state\local_reverse_runtime_policy.json ^
  --out project_state\local_reverse_symbolic_execution_result.json
```

默认只处理 `local_reverse_semantic_rule_result.json` 中：

```text
sample_id in {4c69f173f2bd0211, bcbd9979db015bfd, 18019fca52b389fe}
solved=false
missing_evidence=needs_symbolic_execution
```

### 6.2 Symbolic model v1 范围

只实现小型 pattern-based model：

```text
1. InputByte(i): symbolic byte。
2. TransformChain: input[i] -> add/sub/xor const -> transformed[i]。
3. LoopBound: 推断 i in [0, bound)。
4. CmpConst: transformed or loaded reg == constant。
5. ReplacementRule: if transformed == compare_constant then store replacement_constant。
6. StackAlias: [ebp - offset] 映射为 input buffer / temp buffer / loop index。
```

不要求：

```text
1. 完整 x86 模拟。
2. 完整路径爆炸搜索。
3. 完整内存模型。
4. 支持函数间传播。
5. 支持 GUI 自动化。
```

### 6.3 候选生成策略

候选只能来自 symbolic model。

允许生成：

```text
1. 如果有 loop_bound=64 且 byte_add_const(+1)，尝试构造 inverse transform skeleton。
2. 如果存在 byte_cmp_const constants，按 rule order 组合成 candidate prefix/sequence。
3. 如果有 replacement_rule，尝试 before/after 两条路径。
4. 如果只有部分约束，生成 partial-shape candidates 并标记 partial_model=true。
```

严格限制：

```text
max_rules_per_sample=20
max_symbolic_states_per_sample=64
max_candidates_per_sample=12
max_runtime_validations_per_sample=12
```

不得重复上一轮已失败候选，除非记录：

```text
revalidated_reason=symbolic_model_derived
```

### 6.4 Runtime 验证

使用已有 `run_probe`：

```text
stdin = candidate + "\n"
timeout <= policy.max_timeout_seconds
preview_limit <= 4096
```

成功判定沿用保守语义：

```text
1. stdout/stderr 出现 success/correct/right/congratulations/well done/you win 等成功语义；
2. 且没有 wrong/sorry/fail/invalid/try again 等失败语义；
3. 否则不得 solved=true。
```

### 6.5 输出 result artifact

新增：

```text
project_state/local_reverse_symbolic_execution_result.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "stage": "bounded_symbolic_execution_over_semantic_windows",
  "status": "SUCCESS|PARTIAL|BLOCKED",
  "target_count": 3,
  "solved_count": 0,
  "bounds": {
    "max_rules_per_sample": 20,
    "max_symbolic_states_per_sample": 64,
    "max_candidates_per_sample": 12,
    "max_runtime_validations_per_sample": 12
  },
  "targets": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "previous_missing_evidence": "needs_symbolic_execution",
      "symbolic_model_status": "complete|partial|failed",
      "symbolic_rules_used": [],
      "constraints": [],
      "candidate_count": 0,
      "validated_candidate_count": 0,
      "solved": false,
      "solution": null,
      "runtime_evidence": null,
      "missing_evidence": "symbolic_model_incomplete",
      "next_action": "IDA decompiler summary or manual address seed"
    }
  ]
}
```

产物必须保持轻量：不要把上一轮所有 disassembly windows 全量复制进新 JSON，只记录被使用的 rule_id / address / compact constraint summary。

---

## 7. Tests

必须新增或更新：

```text
tests/test_local_reverse_symbolic_execution.py
tests/test_local_reverse_semantic_rules.py
```

最低测试：

```text
1. 只选择 semantic_rule_result 中 3 个 unsolved target。
2. 已 solved target 不进入 symbolic execution。
3. 非目标样本不进入 symbolic execution。
4. 能将 loop_bound=64 纳入 model。
5. 能将 byte_add_const(+1) 纳入 transform chain。
6. 能将 byte_cmp_const 反推 inverse constraint。
7. 能将 replacement_rule 分成 before/after path candidate。
8. 候选数量受 max_candidates_per_sample 限制。
9. symbolic model 不得重复旧失败候选，除非 revalidated_reason=symbolic_model_derived。
10. wrong/sorry/fail/try again 输出不能 solved=true。
11. 约束不完整时输出 symbolic_model_incomplete 或 branch_condition_unresolved。
12. result JSON schema 正确且不复制大体积 disassembly windows。
```

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_runtime.py reverse_agent\local_reverse_semantic_rules.py reverse_agent\local_reverse_symbolic_execution.py
python -m pytest -q tests\test_local_reverse_semantic_rules.py tests\test_local_reverse_symbolic_execution.py
python -m reverse_agent.local_reverse_symbolic_execution --corpus-index project_state\local_reverse_corpus_index.json --semantic-result project_state\local_reverse_semantic_rule_result.json --xref-result project_state\local_reverse_xref_disassembly_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_symbolic_execution_result.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

---

## 8. Stop Conditions

出现以下情况必须停止：

```text
1. 三个指定样本任一文件缺失或 sha256 mismatch。
2. 样本路径逃逸出 E:\reverse。
3. runtime policy 不允许执行。
4. symbolic execution 需要完整 x86 模拟才能继续。
5. 需要函数间分析或完整路径爆炸搜索。
6. 需要无界 brute force。
7. 需要复杂 GUI 自动化。
8. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
9. 需要修改 .codex-skills/。
10. 需要复制、提交、上传或编码样本二进制。
11. 测试失败。
```

停止时输出：

```text
1. 每个目标样本 symbolic_model_status。
2. 每个目标样本 symbolic_rules_used 数量。
3. 每个目标样本 constraints 数量。
4. 每个目标样本 candidate_count 和 validated_candidate_count。
5. 每个目标样本是否 solved。
6. 未 solved 的更具体 missing_evidence。
7. 下一轮是否需要 IDA decompiler summary、manual address seed、或特定样本专用逆变换。
```
