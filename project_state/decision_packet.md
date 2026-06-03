```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_semantic_rule_extraction_v1",
  "round_id": "round_20260603_local_reverse_semantic_rule_extraction_v1",
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

本轮继续 `local_reverse_simple_training`，从上一轮 **bounded xref / disassembly extraction v1** 推进到 **bounded semantic rule extraction v1**。

上一轮已经完成：

```text
1. 新增 local_reverse_xref_disassembly.py。
2. 对 3 个指定 ready_static_string_compare 目标做 PE mapping、xref 搜索和 Capstone 反汇编窗口提取。
3. 找到 xrefs=35、disassembly_windows=34。
4. 只验证了 xref-derived candidates=6，没有重跑上一轮 90 个候选。
5. 三个样本仍 solved=false。
```

上一轮失败原因已经推进为：

```text
new_xref_candidates_failed_runtime_validation
```

这说明继续扩大候选池收益低。本轮不得再继续扩大 xref、扩大候选、重跑旧候选，而是要从已提取的 disassembly windows 中识别：

```text
1. 输入缓冲区位置；
2. 循环边界；
3. 字符变换；
4. cmp 常量；
5. 分支条件；
6. success/failure path；
7. 可逆规则；
8. 由规则生成的候选输入。
```

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。旧 `task_packet.json` 中的 `samplereverse` 字段仍只作为旧状态背景，不能覆盖本 decision。

---

## 1. Goal

本轮目标是实现第一版 **semantic rule extraction**，把上一轮的反汇编窗口转成可验证的解题规则。

核心目标：

```text
1. 只处理上一轮 3 个 unsolved 目标：
   - 4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
   - bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
   - 18019fca52b389fe -> 逆向课程2024春01/sha_256.exe

2. 读取 project_state/local_reverse_xref_disassembly_result.json。

3. 从 disassembly_windows 中识别基础语义模式：
   - for/while 风格循环；
   - index variable；
   - stack buffer；
   - byte load/store；
   - add/sub/xor/and/or 立即数变换；
   - cmp immediate；
   - conditional branch；
   - replacement rule；
   - fixed length check。

4. 输出每个样本的 semantic_rules。

5. 基于 semantic_rules 生成少量新候选。
   默认每个样本最多 20 个候选。

6. 使用已有 runtime harness 验证候选。
   默认每个样本最多 20 次验证。

7. 输出 project_state/local_reverse_semantic_rule_result.json。

8. 如果仍未 solved，输出更具体 missing_evidence：
   - semantic_rule_not_found
   - transform_rule_found_but_inverse_failed
   - compare_constants_incomplete
   - needs_symbolic_execution
   - needs_ida_decompiler_summary
   - needs_manual_address_seed
```

本轮不是重新实现 xref extraction，不是继续扩大 disassembly windows，不是全量 brute force，不是 GUI/前端整合，也不是处理 22 个样本。

---

## 2. Current Evidence

当前主线：

```text
reverse_solving / local_reverse_simple_training
```

上一轮有效输入产物：

```text
project_state/local_reverse_xref_disassembly_result.json
```

上一轮结果摘要：

```text
status=PARTIAL
target_count=3
solved_count=0
xrefs found=35
disassembly windows=34
xref-derived candidate validations=6
```

上一轮三个目标状态：

```text
18019fca52b389fe -> pe_mapping_status=ok, capstone_status=available_used, xrefs=12, disassembly_windows=11, new_candidate_count=2, validated_candidate_count=2, solved=false, missing_evidence=new_xref_candidates_failed_runtime_validation

4c69f173f2bd0211 -> pe_mapping_status=ok, capstone_status=available_used, xrefs=13, disassembly_windows=13, new_candidate_count=1, validated_candidate_count=1, solved=false, missing_evidence=new_xref_candidates_failed_runtime_validation

bcbd9979db015bfd -> pe_mapping_status=ok, capstone_status=available_used, xrefs=10, disassembly_windows=10, new_candidate_count=3, validated_candidate_count=3, solved=false, missing_evidence=new_xref_candidates_failed_runtime_validation
```

关键正向证据：

```text
sha_256.exe 的 disassembly window 已出现疑似字符变换和约束：

cmp dword ptr [ebp - 0x450], 0x40
mov cl, byte ptr [ebp + eax - 0x44]
add cl, 1
mov byte ptr [ebp + edx - 0x44], cl
cmp ecx, 0x67
mov byte ptr [ebp + edx - 0x44], 0x61
cmp ecx, 0x3a
mov byte ptr [ebp + edx - 0x44], 0x30
```

这类窗口应进入 semantic rule extraction，而不是普通字符串候选生成。

Artifact freshness 判断：

```text
1. project_state/local_reverse_xref_disassembly_result.json 是本轮直接输入证据。
2. project_state/local_reverse_compare_site_result.json 是上一阶段辅助证据。
3. project_state/local_reverse_solve_benchmark.json 是目标来源。
4. project_state/local_reverse_corpus_index.json 提供 sha256 / relative_path / artifact_role。
5. README 清理已经完成，不是本轮任务。
6. samplereverse artifacts 只能作为旧背景，不得用于本轮 local reverse 证据。
```

---

## 3. Do Not Do

严禁：

```text
1. 不重新实现 local_reverse_string_solver.py。
2. 不重新实现 local_reverse_compare_site.py。
3. 不重新实现 local_reverse_xref_disassembly.py。
4. 不重跑上一轮 90 个 compare-site candidates。
5. 不重跑上一轮 6 个 xref candidates，除非 semantic rule 给出新的 revalidation reason。
6. 不继续扩大候选池。
7. 不继续扩大 xref 搜索窗口。
8. 不对 22 个样本全量求解。
9. 不处理 3 个目标之外的 challenge binary。
10. 不做无界 brute force。
11. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
12. 不回旧 sample_solver 盲搜。
13. 不读取完整 solve_reports/。
14. 不读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不提交 E:\reverse 下的二进制样本。
16. 不把 E:\reverse 样本复制进 Git 仓库。
17. 不把样本二进制转成 base64 或 hex 提交。
18. 不修改 .codex-skills/。
19. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
20. 不建设重型 agent 平台。
21. 不伪造 solved=true。
22. 不把本轮扩展为 GUI 前端整合。
```

允许：

```text
1. 读取 project_state/local_reverse_xref_disassembly_result.json。
2. 从已有 disassembly_windows 中做 bounded semantic extraction。
3. 识别有限指令语义：mov、movsx、lea、add、sub、xor、cmp、test、jcc、jmp、call、push。
4. 识别栈变量模式，如 [ebp - 0x44]、[ebp - 0x450]。
5. 识别循环边界和 index update。
6. 识别 byte-level transform。
7. 识别 cmp immediate constants。
8. 从规则生成少量候选并 runtime 验证。
9. 新增 reverse_agent/local_reverse_semantic_rules.py。
10. 新增 tests/test_local_reverse_semantic_rules.py。
11. 输出 project_state/local_reverse_semantic_rule_result.json。
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
project_state/local_reverse_solve_benchmark.json
project_state/local_reverse_string_solver_result.json
project_state/local_reverse_compare_site_result.json
project_state/local_reverse_xref_disassembly_result.json
README.txt
```

必须检查：

```text
reverse_agent/local_reverse_runtime.py
reverse_agent/local_reverse_compare_site.py
reverse_agent/local_reverse_xref_disassembly.py
reverse_agent/local_reverse_string_solver.py
tests/test_local_reverse_runtime.py
tests/test_local_reverse_compare_site.py
tests/test_local_reverse_xref_disassembly.py
```

允许新增：

```text
reverse_agent/local_reverse_semantic_rules.py
tests/test_local_reverse_semantic_rules.py
project_state/local_reverse_semantic_rule_result.json
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
2. 上一轮 xref_disassembly_result 已完成但 solved_count=0，本轮不是重跑 xref/candidates。
3. 本轮 mainline=reverse_solving，具体方向=local_reverse_semantic_rule_extraction_v1。
4. 只处理 3 个指定 unsolved ready_static_string_compare 样本。
5. 未处理 3 个指定样本之外的 challenge binary。
6. 未运行 E:\reverse 之外的 exe。
7. 未复制、提交、上传或编码任何样本二进制。
8. 未修改 .codex-skills/。
9. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
10. semantic extraction 是有界的，有 max windows / max instructions / max rules / max candidates 限制。
11. 如果产生新候选并验证，必须记录 semantic rule source 和 runtime evidence。
12. 如果仍未 solved，必须输出更具体 missing_evidence。
13. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_semantic_rule_extraction_v1",
  "round_id": "round_20260603_local_reverse_semantic_rule_extraction_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_semantic_rule_extraction_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 新增 semantic rule extraction 模块

新增：

```text
reverse_agent/local_reverse_semantic_rules.py
```

建议 CLI：

```bash
python -m reverse_agent.local_reverse_semantic_rules ^
  --corpus-index project_state\local_reverse_corpus_index.json ^
  --xref-result project_state\local_reverse_xref_disassembly_result.json ^
  --policy project_state\local_reverse_runtime_policy.json ^
  --out project_state\local_reverse_semantic_rule_result.json
```

默认只处理 `local_reverse_xref_disassembly_result.json` 中：

```text
sample_id in {4c69f173f2bd0211, bcbd9979db015bfd, 18019fca52b389fe}
solved=false
missing_evidence=new_xref_candidates_failed_runtime_validation
```

### 6.2 语义规则识别范围

第一版只识别简单、可审计规则，不做完整反编译。

支持模式：

```text
1. length_check:
   cmp <index_or_len>, imm

2. loop_bound:
   cmp <loop_var>, imm
   jge / jl / jne / jmp backedge

3. byte_load:
   mov/movsx reg, byte ptr [base + index + disp]

4. byte_store:
   mov byte ptr [base + index + disp], reg_or_imm

5. byte_add_const:
   add reg8, imm

6. byte_sub_const:
   sub reg8, imm

7. byte_xor_const:
   xor reg8, imm

8. byte_cmp_const:
   cmp reg, imm

9. replacement_rule:
   cmp reg, imm_a
   jne target
   mov byte ptr [...], imm_b

10. stack_buffer:
   [ebp - offset] style buffer access
```

输出规则必须保守：

```text
rule_type
confidence=low|medium|high
source_window
source_instructions
inferred_constraint
candidate_generation_enabled=true|false
```

### 6.3 候选生成

候选只能来自 semantic rules。

允许生成：

```text
1. 从 byte_cmp_const 反推字符。
2. 从 byte_add_const / byte_sub_const / byte_xor_const 做逆变换。
3. 从 replacement_rule 生成替换前/替换后候选。
4. 从 length_check 约束候选长度。
5. 从 stack buffer + loop_bound 判断固定长度。
```

严格限制：

```text
max_rules_per_sample=20
max_candidates_per_sample=20
max_runtime_validations_per_sample=20
```

不得重复上一轮已失败 candidate，除非记录：

```text
revalidated_reason=semantic_rule_derived
```

### 6.4 runtime 验证

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
project_state/local_reverse_semantic_rule_result.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "stage": "bounded_semantic_rule_extraction",
  "status": "SUCCESS|PARTIAL|BLOCKED",
  "target_count": 3,
  "solved_count": 0,
  "bounds": {
    "max_windows_per_sample": 12,
    "max_rules_per_sample": 20,
    "max_candidates_per_sample": 20,
    "max_runtime_validations_per_sample": 20
  },
  "targets": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "previous_missing_evidence": "new_xref_candidates_failed_runtime_validation",
      "semantic_rules": [
        {
          "rule_type": "byte_add_const",
          "confidence": "medium",
          "source_window": "...",
          "source_instructions": [],
          "inferred_constraint": "byte[i] = byte[i] + 1"
        }
      ],
      "new_candidate_count": 0,
      "validated_candidate_count": 0,
      "solved": false,
      "solution": null,
      "runtime_evidence": null,
      "missing_evidence": "semantic_rule_found_but_inverse_failed",
      "next_action": "manual address seed or IDA decompiler summary"
    }
  ]
}
```

---

## 7. Tests

必须新增或更新：

```text
tests/test_local_reverse_semantic_rules.py
tests/test_local_reverse_xref_disassembly.py
```

最低测试：

```text
1. 只选择 xref_result 中 3 个 unsolved target。
2. 已 solved target 不进入 semantic extraction。
3. 非目标样本不进入 extraction。
4. 能识别 byte_add_const: add cl, 1。
5. 能识别 byte_cmp_const: cmp ecx, 0x67。
6. 能识别 replacement_rule: cmp ecx, 0x67 -> mov byte ptr [...], 0x61。
7. 能识别 length/loop bound: cmp var, 0x40。
8. 候选数量受 max_candidates_per_sample 限制。
9. 旧失败候选不重复验证，除非 revalidated_reason=semantic_rule_derived。
10. wrong/sorry/fail/try again 输出不能 solved=true。
11. 没有规则时输出 semantic_rule_not_found。
12. 规则存在但验证失败时输出 semantic_rule_found_but_inverse_failed 或 inverse_candidates_failed_runtime_validation。
13. result JSON schema 正确。
```

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_runtime.py reverse_agent\local_reverse_xref_disassembly.py reverse_agent\local_reverse_semantic_rules.py
python -m pytest -q tests\test_local_reverse_xref_disassembly.py tests\test_local_reverse_semantic_rules.py
python -m reverse_agent.local_reverse_semantic_rules --corpus-index project_state\local_reverse_corpus_index.json --xref-result project_state\local_reverse_xref_disassembly_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_semantic_rule_result.json
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
4. semantic rule extraction 需要无界反编译。
5. 需要全文件反汇编才能继续。
6. 需要无界 brute force。
7. 需要复杂 GUI 自动化。
8. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
9. 需要修改 .codex-skills/。
10. 需要复制、提交、上传或编码样本二进制。
11. 测试失败。
```

停止时输出：

```text
1. 每个目标样本 semantic_rules 数量。
2. 每个目标样本识别到的 rule_type。
3. 每个目标样本新候选数量和验证数量。
4. 每个目标样本是否 solved。
5. 未 solved 的更具体 missing_evidence。
6. 下一轮是否需要 manual address seed、IDA decompiler summary、或特定样本专用逆变换。
```
