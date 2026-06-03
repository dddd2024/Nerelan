```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_bounded_xref_disassembly_v1",
  "round_id": "round_20260603_local_reverse_bounded_xref_disassembly_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 `local_reverse_simple_training`，从上一轮 **bounded compare-site static extraction** 推进到 **bounded xref / disassembly extraction v1**。

上一轮已经完成：

```text
1. README 过期 local_reverse_samples / solver.py / local_samples add/solve 流程清理。
2. 新增 local_reverse_compare_site.py。
3. 只处理 3 个指定 ready_static_string_compare 目标。
4. 每个样本生成 30 个新候选并各验证 30 次。
5. 三个样本仍 solved=false。
```

上一轮失败原因已经从：

```text
needs_compare_constant_or_disassembly
```

推进为：

```text
new_candidates_failed_runtime_validation
```

这说明继续扩大候选池收益很低。本轮不得再重复上一轮 90 个候选验证，也不得继续只靠 strings/keyword/import evidence。本轮主任务是对 3 个未解样本做 **bounded xref / disassembly extraction**：从 prompt / failure / success / CompareString 字符串引用出发，定位可能的调用点、基本块、附近比较指令、输入长度约束和目标常量来源。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。旧 `task_packet.json` 中的 `samplereverse` 字段仍只作为旧状态背景，不能覆盖本 decision。

---

## 1. Goal

本轮目标是把上一轮“找到字符串/导入线索但候选验证失败”的状态，推进到可解释的 xref / disassembly 证据。

核心目标：

```text
1. 只处理上一轮 3 个 unsolved 目标：
   - 4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
   - bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
   - 18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
2. 基于 project_state/local_reverse_compare_site_result.json 中的 success/failure/prompt/compare keyword strings，做 bounded xref / disassembly extraction。
3. 如果 capstone 可用，使用 capstone 做有界反汇编；如果不可用，输出明确 BLOCKED_BY_MISSING_DISASSEMBLY_BACKEND。
4. 对每个目标输出可能的 xref、基本块窗口、call/cmp/test/jcc 指令摘要、邻近字符串和候选常量。
5. 只从新 xref/disassembly 证据生成少量新候选；默认每样本最多 20 个。
6. 用已有 runtime harness 验证新候选；默认每样本最多 20 次。
7. 输出 project_state/local_reverse_xref_disassembly_result.json。
8. 如果仍未 solved，输出比 new_candidates_failed_runtime_validation 更具体的 missing_evidence。
```

本轮不是重新实现 string solver，不是重跑 compare_site v1，不是全量 brute force，不是扩展到 22 个样本，也不是 GUI/IDA 前端整合。

---

## 2. Current Evidence

当前主线：

```text
reverse_solving / local_reverse_simple_training
```

`task_packet.json` 和 `current_state.json` 仍包含旧 `samplereverse` 字段，只能作为旧背景。当前执行权威是本 decision。

上一轮有效产物：

```text
project_state/local_reverse_compare_site_result.json
```

上一轮结果摘要：

```text
status=PARTIAL
target_count=3
solved_count=0
max_new_candidates_per_sample=30
max_runtime_validations_per_sample=30
blocked_reasons=[]
```

三个目标的上一轮状态：

```text
18019fca52b389fe -> compare_site_status=found, new_candidate_count=30, validated_candidate_count=30, solved=false, missing_evidence=new_candidates_failed_runtime_validation
4c69f173f2bd0211 -> compare_site_status=found, new_candidate_count=30, validated_candidate_count=30, solved=false, missing_evidence=new_candidates_failed_runtime_validation
bcbd9979db015bfd -> compare_site_status=found, new_candidate_count=30, validated_candidate_count=30, solved=false, missing_evidence=new_candidates_failed_runtime_validation
```

上一轮关键限制：

```text
1. compare_site_status=found 主要来自 strings/import/keyword，不等于真正定位到比较指令。
2. capstone 显示 available 但 used=false。
3. candidate_constant_strings 噪声较高，包含 Rich、SVW、CRT 文件名、运行库字符串等。
4. 90 个候选全部 runtime validation 失败。
```

Artifact freshness 判断：

```text
1. project_state/local_reverse_compare_site_result.json 是本轮直接输入证据。
2. project_state/local_reverse_string_solver_result.json 是上一阶段负结果来源。
3. project_state/local_reverse_solve_benchmark.json 是 3 个目标来源。
4. project_state/local_reverse_corpus_index.json 提供 sha256 / relative_path / artifact_role。
5. README.txt 已完成清理，不是本轮主任务。
6. samplereverse artifacts 只能作为旧背景，不得用于本轮 local reverse 证据。
```

---

## 3. Do Not Do

严禁：

```text
1. 不重新实现 local_reverse_string_solver.py。
2. 不重跑上一轮 90 个 compare-site candidates。
3. 不继续扩大候选池。
4. 不对 22 个样本全量求解。
5. 不处理 3 个目标之外的 challenge binary。
6. 不做无界 brute force。
7. 不扩大 beam / topN / frontier search。
8. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
9. 不回旧 sample_solver 盲搜。
10. 不读取完整 solve_reports/。
11. 不读取完整 PROJECT_PROGRESS_LOG.txt。
12. 不提交 E:\reverse 下的二进制样本。
13. 不把 E:\reverse 样本复制进 Git 仓库。
14. 不把样本二进制转成 base64 或 hex 提交。
15. 不修改 .codex-skills/。
16. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
17. 不建设重型 agent 平台。
18. 不伪造 solved=true。
19. 不把本轮扩展为 GUI 前端整合。
20. 不恢复 README 中已清理的 local_reverse_samples/<case_id>/solver.py 旧流程。
```

允许：

```text
1. 有界读取 3 个目标 exe 的 bytes。
2. 有界解析 PE header / section / import table，如果项目已有或可轻量实现。
3. 使用 capstone 做 bounded disassembly。
4. 从 success/failure/prompt/CompareString 字符串偏移做 xref-like 搜索。
5. 在 section / VA / raw offset 映射可用时，定位引用这些字符串地址的指令窗口。
6. 每个字符串最多分析固定数量 xref，例如 20。
7. 每个 xref 最多反汇编固定窗口，例如前后 64 条指令或 512 bytes。
8. 从新 xref/disassembly 证据生成最多 20 个新候选并 runtime 验证。
9. 输出 project_state/local_reverse_xref_disassembly_result.json。
10. 新增 reverse_agent/local_reverse_xref_disassembly.py 和 tests/test_local_reverse_xref_disassembly.py。
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
README.txt
```

必须检查：

```text
reverse_agent/local_reverse_runtime.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/local_reverse_compare_site.py
reverse_agent/static_feature_extractor.py
tests/test_local_reverse_runtime.py
tests/test_local_reverse_string_solver.py
tests/test_local_reverse_compare_site.py
```

允许新增：

```text
reverse_agent/local_reverse_xref_disassembly.py
tests/test_local_reverse_xref_disassembly.py
project_state/local_reverse_xref_disassembly_result.json
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
2. 上一轮 compare_site_result 已完成但 solved_count=0，本轮不是重跑候选。
3. 本轮 mainline=reverse_solving，具体方向=local_reverse_bounded_xref_disassembly_v1。
4. 只处理 3 个指定 unsolved ready_static_string_compare 样本。
5. 未处理 3 个指定样本之外的 challenge binary。
6. 未运行 E:\reverse 之外的 exe。
7. 未复制、提交、上传或编码任何样本二进制。
8. 未修改 .codex-skills/。
9. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
10. xref/disassembly extraction 是有界的，有 max strings / max xrefs / max instructions / max bytes / max candidates 限制。
11. 如果使用 capstone，记录 capstone_used=true 和 disassembly bounds。
12. 如果未使用 capstone，说明具体 blocked / skipped 原因。
13. 如果产生新候选并验证，必须记录 runtime evidence。
14. 如果仍未 solved，必须输出更具体 missing_evidence。
15. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_bounded_xref_disassembly_v1",
  "round_id": "round_20260603_local_reverse_bounded_xref_disassembly_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_bounded_xref_disassembly_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 新增 bounded xref / disassembly 模块

新增：

```text
reverse_agent/local_reverse_xref_disassembly.py
```

建议 CLI：

```bash
python -m reverse_agent.local_reverse_xref_disassembly ^
  --corpus-index project_state\local_reverse_corpus_index.json ^
  --benchmark project_state\local_reverse_solve_benchmark.json ^
  --string-result project_state\local_reverse_string_solver_result.json ^
  --compare-site-result project_state\local_reverse_compare_site_result.json ^
  --policy project_state\local_reverse_runtime_policy.json ^
  --out project_state\local_reverse_xref_disassembly_result.json
```

默认只处理 `local_reverse_compare_site_result.json` 中：

```text
sample_id in {4c69f173f2bd0211, bcbd9979db015bfd, 18019fca52b389fe}
solved=false
missing_evidence=new_candidates_failed_runtime_validation
```

### 6.2 PE / offset mapping

对每个目标样本，尽量实现轻量 PE 映射：

```text
1. 解析 DOS header / PE header / section table。
2. 记录 image_base。
3. 建立 raw_offset <-> RVA <-> VA 的 section 映射。
4. 如果 PE 解析失败，输出 missing_evidence=pe_mapping_failed。
```

不要求完整 PE loader，不要求处理重定位和复杂异常表。

### 6.3 xref-like 搜索

基于上一轮 result 中的字符串：

```text
prompt_strings
failure_strings
success_strings
compare_keyword_strings
```

对每个字符串：

```text
1. 取 raw offset。
2. 映射为 VA/RVA。
3. 在代码 section 中搜索 little-endian VA / RVA / raw_offset 引用。
4. 每个字符串最多保留 20 个 xref candidates。
5. 每个样本最多处理 12 个关键字符串。
```

输出：

```text
string_value
string_role=prompt|failure|success|compare_keyword
raw_offset
rva
va
xref_candidates=[...]
```

### 6.4 bounded disassembly

如果 capstone 可用：

```text
1. 只反汇编 xref 附近窗口。
2. 每个 xref 最多前后 64 条指令或 512 bytes。
3. 记录 call/cmp/test/jcc/mov/lea/push 指令摘要。
4. 标记疑似 input read、string compare、success/failure branch。
```

如果 capstone 不可用：

```text
1. 不新增重依赖。
2. 输出 capstone=missing。
3. missing_evidence=needs_disassembly_backend。
```

### 6.5 候选生成与 runtime 验证

候选只能来自新的 xref/disassembly 证据，例如：

```text
1. 比较指令附近直接引用的 printable constants。
2. success 分支附近的邻近常量。
3. compare call 前 push/mov/lea 指向的字符串。
4. 明确长度约束附近的 token。
```

每个样本限制：

```text
max_new_candidates_per_sample=20
max_runtime_validations_per_sample=20
timeout <= policy.max_timeout_seconds
```

不得重复上一轮已验证失败的候选，除非本轮 xref/disassembly 给出新的强证据，并在 result 中记录 `revalidated_reason`。

### 6.6 输出 result artifact

新增：

```text
project_state/local_reverse_xref_disassembly_result.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "stage": "bounded_xref_disassembly_extraction",
  "status": "SUCCESS|PARTIAL|BLOCKED",
  "target_count": 3,
  "solved_count": 0,
  "bounds": {
    "max_strings_per_sample": 12,
    "max_xrefs_per_string": 20,
    "max_instructions_per_xref": 64,
    "max_new_candidates_per_sample": 20,
    "max_runtime_validations_per_sample": 20
  },
  "targets": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "sha256": "...",
      "previous_missing_evidence": "new_candidates_failed_runtime_validation",
      "pe_mapping_status": "ok|failed",
      "capstone_status": "available_used|available_not_used|missing",
      "xref_summary": [],
      "disassembly_windows": [],
      "new_candidate_count": 0,
      "validated_candidate_count": 0,
      "solved": false,
      "solution": null,
      "runtime_evidence": null,
      "missing_evidence": "xref_not_found|compare_branch_not_identified|target_constant_not_recovered|new_xref_candidates_failed_runtime_validation|needs_ida_script",
      "next_action": "bounded IDA string xref extraction"
    }
  ]
}
```

---

## 7. Tests

必须新增或更新：

```text
tests/test_local_reverse_xref_disassembly.py
tests/test_local_reverse_compare_site.py
```

最低测试：

```text
1. 只选择 compare_site_result 中 3 个 unsolved target。
2. 已 solved 的样本不进入 xref/disassembly extraction。
3. 非目标样本不进入 extraction。
4. sha256 mismatch 阻止读取/验证。
5. path escape 阻止读取/验证。
6. PE section raw/rva/va 映射基本正确。
7. 能从字符串 raw offset 构造 xref-like search target。
8. xref 数量受 max_xrefs_per_string 限制。
9. disassembly 窗口受 max_instructions_per_xref 或 max bytes 限制。
10. 不重复上一轮已验证失败候选。
11. wrong/sorry/fail/try again 输出不能 solved=true。
12. 如果找不到 xref，输出 xref_not_found 或 needs_ida_script。
13. result JSON schema 正确。
```

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_runtime.py reverse_agent\local_reverse_compare_site.py reverse_agent\local_reverse_xref_disassembly.py
python -m pytest -q tests\test_local_reverse_runtime.py tests\test_local_reverse_compare_site.py tests\test_local_reverse_xref_disassembly.py
python -m reverse_agent.local_reverse_xref_disassembly --corpus-index project_state\local_reverse_corpus_index.json --benchmark project_state\local_reverse_solve_benchmark.json --string-result project_state\local_reverse_string_solver_result.json --compare-site-result project_state\local_reverse_compare_site_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_xref_disassembly_result.json
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
4. PE mapping 无法建立且没有可用 fallback。
5. capstone 不可用且 bytes-level xref 不足以继续。
6. 需要无界 disassembly 或全文件反汇编才能继续。
7. 需要无界 brute force。
8. 需要复杂 GUI 自动化。
9. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
10. 需要修改 .codex-skills/。
11. 需要复制、提交、上传或编码样本二进制。
12. 测试失败。
```

停止时输出：

```text
1. 每个目标样本 PE mapping 状态。
2. 每个目标样本 xref_summary 数量。
3. 每个目标样本 disassembly_windows 数量。
4. 每个目标样本新候选数量和验证数量。
5. 每个目标样本是否 solved。
6. 未 solved 的更具体 missing_evidence。
7. 下一轮是否需要 IDA script / stronger xref backend / per-sample manual address seed。
```
