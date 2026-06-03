```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_ida_state_refresh_v1",
  "round_id": "round_20260603_local_reverse_ida_state_refresh_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮目标是把上一轮已成功生成的 local reverse IDA evidence 正式登记进 `project_state`，修复当前状态仍被旧 `samplereverse` 字段污染的问题。

上一轮已经完成：

```text
project_state/local_reverse_ida_summary.json
status=SUCCESS
target_count=3
success_count=3
ida_available=true
hexrays_available_any=true
```

本轮不进入 solver。目标是为下一轮 `ida_summary_guided_solver_v1` 建立可信、current、可审计的状态入口。

必须完成：

```text
1. 将 project_state/local_reverse_ida_summary.json 登记为 current artifact。
2. 将 3 个 raw IDA evidence JSON 路径登记进 artifact_index，并标注 provenance/freshness。
3. 在 current_state.json 中添加或刷新 local_reverse_training/current_ida_evidence 摘要。
4. 必要时在 task_packet.json 中添加 local_reverse 下一步建议，但不得把 task_packet 当执行权威。
5. 保持旧 samplereverse 字段为背景或兼容字段，不得让它覆盖本轮 local_reverse 状态。
6. 运行 project_state lint 和相关 JSON/pytest 校验。
```

本轮完成后，下一轮才允许生成 `ida_summary_guided_solver_v1` 决策。

---

## 2. Current Evidence

当前主线判定为：

```text
engineering_branch
```

理由：本轮处理 `project_state`、`artifact_index`、状态 freshness 和 provenance，不推进具体样本求解。

上一轮 `codex_execution_report.md` 显示：

```text
based_on_decision_id=decision_20260603_local_reverse_ida_path_rerun_v1
status=SUCCESS
resolved_ida_executable=E:\Program Files\ida_pro\idat64.exe
```

上一轮只处理 3 个 local reverse 目标，未进入 solver，未扩大样本，未复制二进制，未修改 `.codex-skills/`。

上一轮生成的 current evidence：

```text
project_state/local_reverse_ida_summary.json
```

其 summary 应包含：

```text
status=SUCCESS
target_count=3
ida_available=true
hexrays_available_any=true
success_count=3
```

三个 raw IDA evidence 路径来自 summary 中的 `ida_output_path`：

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\bcbd9979db015bfd\Cpp1_ida_evidence.json
```

当前问题：

```text
1. task_packet.json 仍主要是旧 samplereverse 状态。
2. current_state.json 仍主要是旧 samplereverse 状态。
3. artifact_index.json generated_at 仍是旧状态时间，并且 latest_artifacts_v2 未登记 local_reverse_ida_summary/current raw IDA evidence。
```

这些旧字段不能作为下一轮 solver 的 current evidence。

可用 skill profile：

```text
reverse-agent-iteration@v2
```

---

## 3. Do Not Do

严禁：

```text
1. 不进入 solver。
2. 不运行 ida_summary_guided_solver_v1。
3. 不重新跑 IDA，除非为了验证 artifact 存在性需要读取已生成 JSON；不要重新执行 idat64.exe。
4. 不扩大到 22 个样本。
5. 不处理这 3 个目标之外的 challenge binary。
6. 不复制、提交、上传、base64/hex 编码 E:\reverse 下的样本二进制。
7. 不提交完整 solve_reports/。
8. 不读取完整 solve_reports/。
9. 不读取完整 PROJECT_PROGRESS_LOG.txt。
10. 不修改 .codex-skills/。
11. 不新建数据库、消息队列、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
12. 不把 task_packet.task 当执行权威。
13. 不删除旧 samplereverse 兼容字段，除非已有 project_state schema 明确支持迁移。
14. 不把 stale/missing artifact 标为 current。
15. 不伪造 raw IDA evidence 的 sha256/size/modified_at；本地不存在时必须标为 missing 或 unknown。
```

允许：

```text
1. 读取 project_state/local_reverse_ida_summary.json。
2. 有界读取 summary 中列出的 3 个 raw IDA evidence JSON，用于计算 sha256/size/freshness。
3. 更新 project_state/artifact_index.json。
4. 更新 project_state/current_state.json 中的 local_reverse 状态摘要。
5. 必要时更新 project_state/task_packet.json 的 local_reverse 下一步建议。
6. 更新 project_state/codex_execution_report.md。
7. 更新 project_state/pytest_result.txt。
8. 如果已有 project_state builder/linter 支持 local_reverse artifact indexing，优先复用；否则做最小 JSON 更新，不引入重型状态系统。
```

---

## 4. Files To Inspect

必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/local_reverse_ida_summary.json
project_state/local_reverse_corpus_index.json
project_state/local_reverse_semantic_rule_result.json
project_state/local_reverse_runtime_policy.json
reverse_agent/project_state.py
```

必要时读取：

```text
tests/test_project_state.py
tests/test_local_reverse_ida_summary.py
```

有界读取，且仅限 summary 中列出的 3 个 raw JSON：

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\bcbd9979db015bfd\Cpp1_ida_evidence.json
```

不要默认读取：

```text
solve_reports/ 全目录
PROJECT_PROGRESS_LOG.txt
```

---

## 5. Required Audit

Codex 必须在 `project_state/codex_execution_report.md` 中写明：

```text
1. 当前 decision_packet 是执行权威。
2. 本轮主线是 engineering_branch，不是 reverse_solving solver 执行。
3. 上一轮 IDA summary 成功，当前任务是状态登记。
4. 是否读取了 raw IDA evidence；如果读取，只能列出那 3 个具体 JSON。
5. artifact_index.json 中新增或更新了哪些 local_reverse artifact keys。
6. 每个登记 artifact 的 freshness、path、source_run、sha256、size_bytes、modified_at。
7. current_state.json 新增或更新的 local_reverse 状态摘要。
8. task_packet.json 是否更新；如果更新，必须说明 task_packet.task 仍只是建议。
9. 未重新运行 IDA。
10. 未运行 solver。
11. 未处理 3 个目标之外的样本。
12. 未复制、提交、上传或编码任何样本二进制。
13. 未修改 .codex-skills/。
14. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
15. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_ida_state_refresh_v1",
  "round_id": "round_20260603_local_reverse_ida_state_refresh_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_ida_state_refresh_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 优先复用已有 project_state 能力

先检查：

```bash
python -m reverse_agent.project_state --help
python -m reverse_agent.project_state build --help
```

如果已有 builder/linter 能登记 local_reverse artifact，则优先使用已有入口，不新增重复实现。

### 6.2 更新 artifact_index.json

必须至少登记：

```text
local_reverse_ida_summary
```

推荐在 `latest_artifacts_v2` 中添加或更新：

```json
"local_reverse_ida_summary": {
  "kind": "local_reverse_ida_summary",
  "path": "project_state\\local_reverse_ida_summary.json",
  "freshness": "current",
  "source_run": "round_20260603_local_reverse_ida_path_rerun_v1",
  "sha256": "<actual sha256>",
  "size_bytes": <actual size>,
  "modified_at": "<actual mtime or generated_at>"
}
```

同时为 3 个 raw evidence 添加独立条目，例如：

```text
local_reverse_ida_evidence_18019fca52b389fe
local_reverse_ida_evidence_4c69f173f2bd0211
local_reverse_ida_evidence_bcbd9979db015bfd
```

每个条目必须有：

```text
kind
path
freshness
source_run
sha256
size_bytes
modified_at
sample_id
```

如果 raw JSON 本地不存在，则对应条目不得标为 current，必须标为 missing 或 unknown，并在报告中说明。

### 6.3 更新 current_state.json

在不破坏旧字段兼容的前提下，添加或刷新：

```json
"local_reverse_training": {
  "stage": "ida_evidence_ready",
  "latest_summary": "project_state\\local_reverse_ida_summary.json",
  "summary_status": "SUCCESS",
  "target_count": 3,
  "success_count": 3,
  "ida_available": true,
  "hexrays_available_any": true,
  "targets": [
    {
      "sample_id": "18019fca52b389fe",
      "relative_path": "逆向课程2024春01/sha_256.exe",
      "ida_status": "success",
      "ida_output_path": "solve_reports\\tool_artifacts\\local_reverse_ida_evidence_integration_v1\\18019fca52b389fe\\sha_256_ida_evidence.json",
      "next_action": "ida_summary_guided_solver_v1"
    }
  ],
  "next_recommended_decision": "ida_summary_guided_solver_v1"
}
```

保留旧 `samplereverse` 字段，但必须确保报告说明它们是背景兼容字段，不是当前执行权威。

### 6.4 可选更新 task_packet.json

如果更新 `task_packet.json`，只添加 low-token 建议字段，例如：

```json
"local_reverse_next_suggested_task": "Generate ida_summary_guided_solver_v1 decision from current IDA evidence",
"local_reverse_current_artifact": "project_state\\local_reverse_ida_summary.json"
```

不得把旧 `task_packet.task` 当权威，也不得删除旧字段导致兼容性问题。

---

## 7. Tests

必须运行：

```bash
python -m json.tool project_state\artifact_index.json > NUL
python -m json.tool project_state\current_state.json > NUL
python -m json.tool project_state\task_packet.json > NUL
```

必须运行：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

必须运行项目状态相关测试：

```bash
python -m pytest -q tests\test_project_state.py tests\test_local_reverse_ida_summary.py
```

如果修改了 `reverse_agent/project_state.py` 或公共状态生成逻辑，必须运行：

```bash
python -m pytest -q
```

最后运行：

```bash
git diff --check
```

测试结果必须写入：

```text
project_state/pytest_result.txt
```

---

## 8. Stop Conditions

出现以下任一情况立即停止并报告：

```text
1. project_state/local_reverse_ida_summary.json 缺失。
2. local_reverse_ida_summary.json 不是 SUCCESS。
3. success_count 不是 3。
4. summary 中的 raw ida_output_path 缺失。
5. raw IDA evidence JSON 本地不存在，且无法安全标为 missing/unknown。
6. artifact_index schema 不清楚，无法在不破坏旧字段的情况下添加 latest_artifacts_v2 条目。
7. 需要读取完整 solve_reports/ 才能继续。
8. 需要读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
9. 需要重新运行 IDA 才能继续。
10. 需要进入 solver 才能继续。
11. 任何样本二进制将被复制、提交、上传或编码。
```

本轮完成标准：

```text
project_state/artifact_index.json 能指向 current local_reverse IDA artifacts；
project_state/current_state.json 有 local_reverse_training/current_ida_evidence 摘要；
project_state/codex_execution_report.md 记录状态刷新事实；
project_state/pytest_result.txt 记录真实测试；
没有运行 solver；
没有重新运行 IDA；
没有扩大样本；
没有提交 solve_reports/ 原始目录内容。
```
