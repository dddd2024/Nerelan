```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_compare_site_extraction_doc_cleanup",
  "round_id": "round_20260603_local_reverse_compare_site_extraction_doc_cleanup",
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

本轮继续 `local_reverse_simple_training`，但不重复上一轮 `string_compare_static_solver_v1` 的候选生成/验证逻辑。

上一轮已经完成第一版 bounded string-compare solver，但结果为：

```text
target_count=3
solved_count=0
negative_result=NO_CANDIDATE_VALIDATED
missing_evidence=needs_compare_constant_or_disassembly
```

因此本轮主任务是：对这 3 个未解出的 `ready_static_string_compare` 样本做 **bounded compare-site static extraction**，补齐静态 compare 常量、比较点、字符串引用、输入长度约束等证据。

同时，本轮必须执行之前未完成的 README 清理任务：移除或改写已经过期的 `local_reverse_samples\<case_id>\solver.py`、`local_samples add`、`local_samples solve`、本地单题 solver 旧流程说明。该清理任务上轮已经写入计划，但 Codex 实际 report 仍对应旧 decision，未执行 README 清理。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。旧 `task_packet.json` 中的 `samplereverse` 字段仍只作为旧状态背景，不能覆盖本 decision。

---

## 1. Goal

本轮目标有两个，必须同时完成：

```text
1. 能力提升主任务：
   基于上一轮 string solver 的失败结果，对 3 个目标样本做 bounded compare-site static extraction，
   输出 compare-site / candidate-source 证据，为下一轮候选生成提供更强依据。

2. 文档清理补任务：
   清理 README.txt 中已过期的 local_reverse_samples / solver.py / local_samples add / local_samples solve 旧流程，
   避免后续 GPT/Codex 继续引用已经移除的设计。
```

本轮不是重新实现 string solver，不是全量 brute force，不是扩展到 22 个样本，也不是重新做 runtime benchmark。

---

## 2. Current Evidence

上一轮 string solver report 显示：

```text
report_id=report_20260603_local_reverse_string_compare_solver_v1
status=PARTIAL
acceptance_recommendation=NEEDS_REVIEW
```

它只处理了 3 个 `ready_static_string_compare` 样本：

```text
1. 4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
2. bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
3. 18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
```

结果：

```text
4c69f173f2bd0211 -> candidate_count=50, validated_candidate_count=50, solved=false
bcbd9979db015bfd -> candidate_count=50, validated_candidate_count=50, solved=false
18019fca52b389fe -> candidate_count=50, validated_candidate_count=50, solved=false
negative_result=NO_CANDIDATE_VALIDATED
missing_evidence=needs_compare_constant_or_disassembly
```

所以本轮应推进到：

```text
bounded compare-site static extraction
```

而不是继续扩大候选池。

README 当前仍包含过期入口：

```text
local_reverse_samples\
local solver.py
python -m reverse_agent.local_samples add
python -m reverse_agent.local_samples solve
local_reverse_samples\<case_id>\solver.py
```

这些旧说明必须清理。

Artifact freshness 判断：

```text
1. project_state/local_reverse_string_solver_result.json 是上一轮 solver 失败证据。
2. project_state/local_reverse_solve_benchmark.json 是本轮 3 个目标样本来源。
3. project_state/local_reverse_corpus_index.json 提供 sha256 / relative_path / artifact_role。
4. README.txt 是本轮文档清理目标，不是 solver 运行事实来源。
5. samplereverse artifacts 只能作为旧背景，不得用于本轮证据。
```

---

## 3. Do Not Do

严禁：

```text
1. 不重新实现上一轮 local_reverse_string_solver.py。
2. 不重复验证同一批 50 candidates，除非 compare-site extraction 产生新候选。
3. 不扩大到 22 个样本。
4. 不处理 3 个目标之外的 challenge binary。
5. 不做无界 brute force。
6. 不扩大 beam / topN / frontier search。
7. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
8. 不回旧 sample_solver 盲搜。
9. 不读取完整 solve_reports/。
10. 不读取完整 PROJECT_PROGRESS_LOG.txt。
11. 不提交 E:\reverse 下的二进制样本。
12. 不把 E:\reverse 样本复制进 Git 仓库。
13. 不把样本二进制转成 base64 或 hex 提交。
14. 不修改 .codex-skills/。
15. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
16. 不建设重型 agent 平台。
17. 不伪造 solved=true。
18. 不把 README 清理扩大成整体文档重写。
19. 不重新引入 local_reverse_samples\<case_id>\solver.py 旧流程。
```

允许：

```text
1. 有界读取 3 个目标 exe 的 bytes。
2. 提取 ASCII / UTF-16LE strings。
3. 检查 PE sections、imports、字符串交叉引用的轻量证据。
4. 使用 capstone 或已有轻量反汇编工具做 bounded disassembly，如果项目已有依赖或可选导入。
5. 若无 capstone，不强行新增重依赖；可以输出 BLOCKED_BY_MISSING_DISASSEMBLY_BACKEND。
6. 从 compare-site extraction 结果生成新的有限候选。
7. 对新候选做 runtime 验证。
8. 输出 project_state/local_reverse_compare_site_result.json。
9. 修改 README.txt 清理旧 local_reverse_samples 单题 solver 说明。
10. 更新测试。
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
README.txt
```

必须检查：

```text
reverse_agent/local_reverse_runtime.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/static_feature_extractor.py
tests/test_local_reverse_runtime.py
tests/test_local_reverse_string_solver.py
README.txt
```

允许新增：

```text
reverse_agent/local_reverse_compare_site.py
tests/test_local_reverse_compare_site.py
project_state/local_reverse_compare_site_result.json
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
2. 上一轮 string solver 已完成，不重复实现。
3. 本轮 mainline=reverse_solving，具体方向=local_reverse_compare_site_extraction_doc_cleanup。
4. 只处理 3 个指定 unsolved ready_static_string_compare 样本。
5. 未处理 3 个指定样本之外的 challenge binary。
6. 未运行 E:\reverse 之外的 exe。
7. 未复制、提交、上传或编码任何样本二进制。
8. 未修改 .codex-skills/。
9. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
10. compare-site extraction 是有界的，有 max bytes / max instructions / max candidates 限制。
11. 如果产生新候选并验证，必须记录 runtime evidence。
12. 如果仍未 solved，必须输出更具体 missing_evidence。
13. README.txt 中过期 local_reverse_samples / solver.py / local_samples add/solve 旧流程已清理。
14. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_compare_site_extraction_doc_cleanup",
  "round_id": "round_20260603_local_reverse_compare_site_extraction_doc_cleanup",
  "based_on_decision_id": "decision_20260603_local_reverse_compare_site_extraction_doc_cleanup",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 新增 compare-site extraction 模块

新增：

```text
reverse_agent/local_reverse_compare_site.py
```

建议 CLI：

```bash
python -m reverse_agent.local_reverse_compare_site ^
  --corpus-index project_state\local_reverse_corpus_index.json ^
  --benchmark project_state\local_reverse_solve_benchmark.json ^
  --string-result project_state\local_reverse_string_solver_result.json ^
  --policy project_state\local_reverse_runtime_policy.json ^
  --out project_state\local_reverse_compare_site_result.json
```

默认只处理上一轮 string solver 中：

```text
solved=false
negative_result=NO_CANDIDATE_VALIDATED
missing_evidence=needs_compare_constant_or_disassembly
```

且属于以下 3 个目标的样本：

```text
4c69f173f2bd0211
bcbd9979db015bfd
18019fca52b389fe
```

### 6.2 compare-site 静态提取范围

对每个目标样本执行 bounded extraction：

```text
1. 验证 relative_path 在 E:\reverse root 下。
2. 验证 sha256 匹配。
3. 读取文件 bytes，但不得提交 bytes。
4. 提取 ASCII / UTF-16LE strings。
5. 识别 success/failure/prompt 字符串。
6. 识别可能的 target strings / compare constants。
7. 如果可行，定位 strcmp/strncmp/memcmp/import 或直接字符串比较线索。
8. 如果无法定位，输出 missing_evidence。
```

如果项目已有轻量 PE / disassembly 工具，允许使用；如果没有，不要强行引入大型依赖。可以先实现 bytes-level 和 strings-neighborhood 版本。

### 6.3 候选生成与验证

候选只来自 compare-site extraction 新证据，不重复上一轮 50 个泛候选。

每个样本限制：

```text
max_new_candidates_per_sample=30
max_runtime_validations_per_sample=30
timeout <= policy.max_timeout_seconds
```

成功判定仍然保守：

```text
1. 出现 correct/success/right/congratulations/you win 等成功语义；
2. 且不出现 wrong/sorry/fail/invalid/try again 等失败语义；
3. 否则不得 solved=true。
```

如果仍未成功，输出更具体的缺失证据，例如：

```text
compare_site_not_found
target_constant_not_found
success_string_found_but_no_xref_backend
needs_disassembly_backend
needs_ida_script
```

### 6.4 输出 result artifact

新增：

```text
project_state/local_reverse_compare_site_result.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "stage": "bounded_compare_site_static_extraction",
  "status": "SUCCESS|PARTIAL|BLOCKED",
  "target_count": 3,
  "solved_count": 0,
  "targets": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "sha256": "...",
      "previous_negative_result": "NO_CANDIDATE_VALIDATED",
      "compare_site_status": "found|not_found|blocked",
      "strings_summary": {
        "prompt_strings": [],
        "failure_strings": [],
        "success_strings": [],
        "candidate_constant_strings": []
      },
      "new_candidate_count": 0,
      "validated_candidate_count": 0,
      "solved": false,
      "solution": null,
      "runtime_evidence": null,
      "missing_evidence": "compare_site_not_found",
      "next_action": "bounded IDA/capstone compare-site extraction"
    }
  ]
}
```

### 6.5 README 清理

修改 `README.txt`：

```text
1. 删除或改写 local_reverse_samples\ 作为本地 solver.py 推荐目录的说明。
2. 删除或改写 local_samples add / local_samples solve 的旧流程。
3. 删除“后续单题 solver.py 应继续保存在 local_reverse_samples\<case_id>\ 下”的说法。
4. 将当前本地训练方向说明为：
   - E:\reverse 是用户本地样本根；
   - project_state/local_reverse_* JSON 是当前事实来源；
   - local_reverse_corpus / local_reverse_runtime / local_reverse_string_solver / local_reverse_compare_site 是当前能力训练入口；
   - 独立脚本如果用户自管，不作为项目 README 主流程。
5. 不改 .codex-skills/。
```

---

## 7. Tests

必须新增或更新：

```text
tests/test_local_reverse_compare_site.py
tests/test_local_reverse_string_solver.py
tests/test_local_reverse_runtime.py
```

最低测试：

```text
1. 只选择 string_solver_result 中 3 个 unsolved target。
2. 已 solved 的样本不进入 compare-site extraction。
3. 非目标样本不进入 compare-site extraction。
4. sha256 mismatch 阻止读取/验证。
5. path escape 阻止读取/验证。
6. strings_summary 能分类 prompt/failure/success/candidate strings。
7. 新候选数受 max_new_candidates_per_sample 限制。
8. wrong/sorry/fail/try again 输出不能 solved=true。
9. 如果 compare-site 不足，输出 missing_evidence。
10. README.txt 不再包含 local_reverse_samples\\<case_id>\\solver.py 作为当前推荐流程。
11. README.txt 不再把 local_samples add/solve 作为当前主流程。
12. result JSON schema 正确。
```

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_runtime.py reverse_agent\local_reverse_string_solver.py reverse_agent\local_reverse_compare_site.py
python -m pytest -q tests\test_local_reverse_runtime.py tests\test_local_reverse_string_solver.py tests\test_local_reverse_compare_site.py
python -m reverse_agent.local_reverse_compare_site --corpus-index project_state\local_reverse_corpus_index.json --benchmark project_state\local_reverse_solve_benchmark.json --string-result project_state\local_reverse_string_solver_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_compare_site_result.json
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
4. compare-site extraction 需要读取或提交样本二进制。
5. 需要无界 brute force。
6. 需要复杂 GUI 自动化。
7. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
8. 需要修改 .codex-skills/。
9. README 清理需要恢复已经移除的 local_reverse_samples 单题 solver 旧流程。
10. 测试失败。
```

停止时输出：

```text
1. 每个目标样本 compare-site extraction 状态。
2. 每个目标样本新候选数量。
3. 每个目标样本是否 solved。
4. 未 solved 的更具体 missing_evidence。
5. README 过期入口清理结果。
6. 下一轮是否需要 IDA script / capstone backend / specific compare xref extraction。
```
