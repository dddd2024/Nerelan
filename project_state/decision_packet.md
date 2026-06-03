```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_ida_evidence_integration_v1",
  "round_id": "round_20260603_local_reverse_ida_evidence_integration_v1",
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

本轮继续 `local_reverse_simple_training`，但不继续执行上一版 `bounded_symbolic_execution_v1` 计划。用户已指出：项目以前已经接入过 IDA，不能重建一套 IDA 接入，必须复用已有模块。

因此本轮从上一轮 `semantic_rule_extraction_v1` 的 blocker：

```text
needs_symbolic_execution
```

调整为：**reuse existing IDA automation for local_reverse IDA evidence integration v1**。

当前仓库已有可复用模块：

```text
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
```

本轮任务不是新建一套 IDA 启动逻辑，不是重做 GUI/IDA pipeline，而是复用现有 `tool_runners.py` 和 `collect_evidence.py`，把 IDA evidence 接入 `local_reverse_*` 训练线，针对 3 个未解样本输出轻量、机器可读的 `project_state/local_reverse_ida_summary.json`。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。旧 `task_packet.json` 中的 `samplereverse` 字段仍只作为旧状态背景，不能覆盖本 decision。

---

## 1. Goal

本轮目标是把已有 IDA 自动化能力接入当前本地逆向训练线。

核心目标：

```text
1. 只处理上一轮 3 个 unsolved / needs_symbolic_execution 目标：
   - 4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
   - bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
   - 18019fca52b389fe -> 逆向课程2024春01/sha_256.exe

2. 复用现有 IDA runner：
   - reverse_agent/tool_runners.py
   - ToolAutomationConfig
   - _resolve_ida_executable
   - _resolve_ida_script
   - _run_ida 或等价公共封装

3. 复用现有 IDA 脚本：
   - reverse_agent/ida_scripts/collect_evidence.py

4. 必要时小幅扩展 collect_evidence.py，但不得重写：
   - string_xrefs
   - validation_function_candidates
   - decompiler_snippets（仅 Hex-Rays 可用时）
   - solver_hint

5. 新增 local_reverse 专用 orchestrator：
   - reverse_agent/local_reverse_ida_summary.py

6. 输出：
   - project_state/local_reverse_ida_summary.json

7. 如果 IDA 不可用、Hex-Rays 不可用、或本地路径不可访问，必须输出 BLOCKED/PARTIAL 证据，不得伪造 IDA 结果。
```

本轮不是继续扩 symbolic execution，不是重跑 semantic candidates，不是处理 22 个样本，不是 GUI 前端整合。

---

## 2. Current Evidence

上一轮有效结果：

```text
project_state/local_reverse_semantic_rule_result.json
```

上一轮摘要：

```text
status=PARTIAL
target_count=3
solved_count=0
semantic rules extracted=60
semantic candidate validations=45
```

三个目标状态：

```text
18019fca52b389fe -> semantic_rule_count=20, generated_candidate_count=20, validated_candidate_count=20, solved=false, missing_evidence=needs_symbolic_execution
4c69f173f2bd0211 -> semantic_rule_count=20, generated_candidate_count=13, validated_candidate_count=13, solved=false, missing_evidence=needs_symbolic_execution
bcbd9979db015bfd -> semantic_rule_count=20, generated_candidate_count=12, validated_candidate_count=12, solved=false, missing_evidence=needs_symbolic_execution
```

已有 IDA 接入证据：

```text
1. reverse_agent/ida_scripts/collect_evidence.py 已存在。
2. collect_evidence.py 已能采集 strings / functions / compare_contexts / local_check_contexts / control_id_contexts。
3. reverse_agent/tool_runners.py 已有 ToolAutomationConfig、_run_ida、_resolve_ida_executable、_resolve_ida_script。
4. tool_runners.py 已支持 IDA -A -S<script> headless execution，并通过 REVERSE_AGENT_IDA_OUT 输出 JSON。
```

Artifact freshness 判断：

```text
1. project_state/local_reverse_semantic_rule_result.json 是本轮目标来源。
2. project_state/local_reverse_corpus_index.json 提供 sha256 / relative_path / artifact_role。
3. project_state/local_reverse_runtime_policy.json 提供 root 和 runtime policy。
4. existing IDA modules 是代码事实来源，不是动态样本证据。
5. samplereverse artifacts 只能作为旧背景，不得用于本轮 local_reverse IDA evidence。
```

---

## 3. Do Not Do

严禁：

```text
1. 不重建 IDA 启动逻辑。
2. 不复制 tool_runners.py 里的 _run_ida 实现到新文件。
3. 不重写 collect_evidence.py。
4. 不把本轮做成新的独立 IDA 框架。
5. 不继续执行 bounded_symbolic_execution_v1。
6. 不重跑上一轮 45 个 semantic candidates。
7. 不重跑上一轮 90 个 compare-site candidates。
8. 不重跑上一轮 6 个 xref candidates。
9. 不扩大到 22 个样本。
10. 不处理 3 个目标之外的 challenge binary。
11. 不做无界 brute force。
12. 不继续 samplereverse 的窗口发现、compare handoff、Base64/RC4 breakpoint probe。
13. 不回旧 sample_solver 盲搜。
14. 不读取完整 solve_reports/。
15. 不读取完整 PROJECT_PROGRESS_LOG.txt。
16. 不提交 E:\reverse 下的二进制样本。
17. 不把 E:\reverse 样本复制进 Git 仓库。
18. 不把样本二进制转成 base64 或 hex 提交。
19. 不修改 .codex-skills/。
20. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
21. 不建设重型 agent 平台。
22. 不伪造 IDA / Hex-Rays 输出。
23. 不把本轮扩展为 GUI 前端整合。
```

允许：

```text
1. 读取 project_state/local_reverse_semantic_rule_result.json。
2. 读取 project_state/local_reverse_corpus_index.json。
3. 读取 project_state/local_reverse_runtime_policy.json。
4. 新增 reverse_agent/local_reverse_ida_summary.py。
5. 对 reverse_agent/tool_runners.py 做最小 additive refactor，例如暴露公共 run_ida_evidence 函数，避免复制 _run_ida。
6. 小幅扩展 reverse_agent/ida_scripts/collect_evidence.py，保留既有输出兼容性。
7. 新增 tests/test_local_reverse_ida_summary.py。
8. 输出 project_state/local_reverse_ida_summary.json。
9. 如果 IDA 不可用，用 mock/fake IDA evidence 测试 orchestrator 逻辑；真实运行标记 BLOCKED_BY_IDA_UNAVAILABLE。
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
README.txt
```

必须检查：

```text
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/gui.py
reverse_agent/pipeline.py
reverse_agent/local_reverse_semantic_rules.py
tests/test_local_reverse_semantic_rules.py
```

允许新增/修改：

```text
reverse_agent/local_reverse_ida_summary.py
tests/test_local_reverse_ida_summary.py
project_state/local_reverse_ida_summary.json
```

允许最小修改：

```text
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
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
2. 本轮替代上一版 bounded_symbolic_execution_v1，原因是已有 IDA 接入应复用。
3. 本轮 mainline=reverse_solving，具体方向=local_reverse_ida_evidence_integration_v1。
4. 只处理 3 个指定 needs_symbolic_execution 样本。
5. 未处理 3 个指定样本之外的 challenge binary。
6. 未运行 E:\reverse 之外的 exe。
7. 未复制、提交、上传或编码任何样本二进制。
8. 未修改 .codex-skills/。
9. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
10. 已复用现有 tool_runners.py / collect_evidence.py，没有重建 IDA 启动逻辑。
11. 如果修改 collect_evidence.py，必须保持旧字段 strings/functions/compare_contexts/local_check_contexts/control_id_contexts 兼容。
12. 如果 IDA 不可用，必须明确 BLOCKED_BY_IDA_UNAVAILABLE，不得伪造成功。
13. 如果 Hex-Rays 不可用，必须明确 hexrays_available=false，不得伪造 decompiled_snippets。
14. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_ida_evidence_integration_v1",
  "round_id": "round_20260603_local_reverse_ida_evidence_integration_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_ida_evidence_integration_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 复用现有 IDA runner

优先方案：在 `tool_runners.py` 中做 additive refactor，暴露公共函数，例如：

```text
run_ida_evidence(file_path, artifacts_dir, ida_executable, ida_script_path, timeout_seconds, log)
```

要求：

```text
1. 内部复用现有 _run_ida 逻辑或把 _run_ida 的公共部分抽出。
2. 不复制粘贴一份 IDA subprocess 逻辑到 local_reverse_ida_summary.py。
3. 保持 GUI / pipeline 原有 IDA 功能兼容。
4. 现有 ToolRunArtifact 行为不破坏。
```

### 6.2 小幅扩展 collect_evidence.py

如果可行，扩展 `ida_scripts/collect_evidence.py`，但必须保留旧输出字段。

新增字段建议：

```text
string_xrefs
validation_function_candidates
hexrays_available
decompiler_snippets
solver_hints
```

字段语义：

```text
string_xrefs:
  针对 wrong/correct/success/input/flag/password/sha/md5/strcmp/memcmp 等关键词字符串，列出 xref 函数、xref 地址、附近指令。

validation_function_candidates:
  综合 compare_contexts、local_check_contexts、string_xrefs、函数名、success/failure 字符串，排序出疑似校验函数。

hexrays_available:
  true/false。

decompiler_snippets:
  仅 Hex-Rays 可用时，导出疑似校验函数的短伪代码片段；必须限长。

solver_hints:
  direct_strcmp | transform_then_compare | hash_compare | gui_input | unknown。
```

如果 Hex-Rays API 不可用，不要失败；输出：

```text
hexrays_available=false
decompiler_snippets=[]
```

### 6.3 新增 local_reverse orchestrator

新增：

```text
reverse_agent/local_reverse_ida_summary.py
```

建议 CLI：

```bash
python -m reverse_agent.local_reverse_ida_summary ^
  --corpus-index project_state\local_reverse_corpus_index.json ^
  --semantic-result project_state\local_reverse_semantic_rule_result.json ^
  --policy project_state\local_reverse_runtime_policy.json ^
  --out project_state\local_reverse_ida_summary.json ^
  --ida-path "E:\Program Files\ida_pro" 
```

默认只处理：

```text
sample_id in {4c69f173f2bd0211, bcbd9979db015bfd, 18019fca52b389fe}
solved=false
missing_evidence=needs_symbolic_execution
```

### 6.4 输出 result artifact

新增：

```text
project_state/local_reverse_ida_summary.json
```

建议结构：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "stage": "local_reverse_ida_evidence_integration",
  "status": "SUCCESS|PARTIAL|BLOCKED",
  "target_count": 3,
  "ida_available": true,
  "hexrays_available_any": false,
  "targets": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "previous_missing_evidence": "needs_symbolic_execution",
      "ida_status": "success|blocked|failed",
      "ida_output_path": "...",
      "hexrays_available": false,
      "strings_summary": [],
      "compare_contexts_summary": [],
      "local_check_contexts_summary": [],
      "string_xrefs_summary": [],
      "validation_function_candidates": [],
      "decompiler_snippets": [],
      "solver_hints": [],
      "next_action": "ida_summary_guided_solver_v1"
    }
  ]
}
```

产物必须轻量：不要把完整 IDA output 大量复制进 project_state，只保留 summary、top-N context 和 output path。

---

## 7. Tests

必须新增或更新：

```text
tests/test_local_reverse_ida_summary.py
tests/test_local_reverse_semantic_rules.py
```

最低测试：

```text
1. 只选择 semantic_result 中 3 个 solved=false 且 missing_evidence=needs_symbolic_execution 的目标。
2. 已 solved target 不进入 IDA summary。
3. 非目标样本不进入 IDA summary。
4. sha256 mismatch 阻止执行 IDA。
5. path escape 阻止执行 IDA。
6. IDA unavailable 时输出 BLOCKED_BY_IDA_UNAVAILABLE，不伪造成功。
7. fake IDA output 能被转换为 local_reverse_ida_summary target。
8. 旧 collect_evidence 字段 strings/functions/compare_contexts/local_check_contexts/control_id_contexts 保持兼容。
9. Hex-Rays 不可用时 hexrays_available=false 且 decompiler_snippets=[]。
10. summary JSON schema 正确且不会复制完整大体积 IDA 输出。
11. 如果 tool_runners.py 被 refactor，现有 IDA runner 测试或 mock 测试仍通过。
```

必须运行：

```bash
python -m py_compile reverse_agent\tool_runners.py reverse_agent\local_reverse_ida_summary.py reverse_agent\ida_scripts\collect_evidence.py
python -m pytest -q tests\test_local_reverse_ida_summary.py tests\test_local_reverse_semantic_rules.py
python -m reverse_agent.local_reverse_ida_summary --corpus-index project_state\local_reverse_corpus_index.json --semantic-result project_state\local_reverse_semantic_rule_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_ida_summary.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果本地 Codex 环境没有 IDA，应允许 CLI 产出 `BLOCKED` 或 `PARTIAL`，但 pytest 必须通过 fake/mock IDA output 测试 orchestrator。

---

## 8. Stop Conditions

出现以下情况必须停止：

```text
1. 三个指定样本任一文件缺失或 sha256 mismatch。
2. 样本路径逃逸出 E:\reverse。
3. 需要处理 3 个目标之外的样本。
4. 需要重写 IDA 启动逻辑。
5. 需要恢复旧 local_reverse_samples 单题 solver 流程。
6. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
7. 需要修改 .codex-skills/。
8. 需要复制、提交、上传或编码样本二进制。
9. 测试失败。
```

停止时输出：

```text
1. 每个目标样本 IDA status。
2. 每个目标样本 compare_contexts / local_check_contexts / string_xrefs 数量。
3. 每个目标样本是否有 Hex-Rays snippets。
4. 每个目标样本 solver_hints。
5. 如果 IDA/Hex-Rays 不可用，明确 blocked reason。
6. 下一轮是否进入 ida_summary_guided_solver_v1。
```
