```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_current_state_rework_v1",
  "round_id": "round_20260603_local_reverse_current_state_rework_v1",
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

只返工 `project_state/current_state.json` 的 local reverse 状态摘要。

上一次状态刷新轮已经把 local reverse IDA summary 和 3 个 raw IDA evidence JSON 登记进 `artifact_index.json`，并在 `task_packet.json` 中添加了 advisory 字段；但审计未能在当前仓库内容中验证到 `current_state.json` 存在 `local_reverse_training.current_ida_evidence`。本轮只修正这个缺口。

必须在 `project_state/current_state.json` 中添加或修正：

```json
"local_reverse_training": {
  "stage": "ida_evidence_ready",
  "latest_summary": "project_state\\local_reverse_ida_summary.json",
  "summary_status": "SUCCESS",
  "target_count": 3,
  "success_count": 3,
  "ida_available": true,
  "hexrays_available_any": true,
  "source_run": "round_20260603_local_reverse_ida_path_rerun_v1",
  "state_refresh_round": "round_20260603_local_reverse_current_state_rework_v1",
  "current_ida_evidence": [
    {
      "sample_id": "18019fca52b389fe",
      "relative_path": "逆向课程2024春01/sha_256.exe",
      "ida_status": "success",
      "hexrays_available": true,
      "ida_output_path": "solve_reports\\tool_artifacts\\local_reverse_ida_evidence_integration_v1\\18019fca52b389fe\\sha_256_ida_evidence.json",
      "artifact_key": "local_reverse_ida_evidence_18019fca52b389fe",
      "next_action": "ida_summary_guided_solver_v1"
    },
    {
      "sample_id": "4c69f173f2bd0211",
      "relative_path": "逆向课程2022春02/CPP2.exe",
      "ida_status": "success",
      "hexrays_available": true,
      "ida_output_path": "solve_reports\\tool_artifacts\\local_reverse_ida_evidence_integration_v1\\4c69f173f2bd0211\\CPP2_ida_evidence.json",
      "artifact_key": "local_reverse_ida_evidence_4c69f173f2bd0211",
      "next_action": "ida_summary_guided_solver_v1"
    },
    {
      "sample_id": "bcbd9979db015bfd",
      "relative_path": "逆向课程2022春补考01/Cpp1.exe",
      "ida_status": "success",
      "hexrays_available": true,
      "ida_output_path": "solve_reports\\tool_artifacts\\local_reverse_ida_evidence_integration_v1\\bcbd9979db015bfd\\Cpp1_ida_evidence.json",
      "artifact_key": "local_reverse_ida_evidence_bcbd9979db015bfd",
      "next_action": "ida_summary_guided_solver_v1"
    }
  ],
  "next_recommended_decision": "ida_summary_guided_solver_v1"
}
```

本轮完成后，下一轮才允许生成 `ida_summary_guided_solver_v1` 决策。

---

## 2. Current Evidence

当前主线：

```text
engineering_branch
```

理由：本轮只修复 `project_state/current_state.json` 的状态登记缺口，不推进具体样本求解。

已验证事实：

```text
1. project_state/artifact_index.json 已登记 local_reverse_ida_summary。
2. project_state/artifact_index.json 已登记 3 个 local_reverse_ida_evidence_* artifact。
3. 这些 artifact 在 latest_artifacts_v2 中标为 freshness=current。
4. project_state/task_packet.json 已有 local_reverse_next_suggested_task / local_reverse_current_artifact / local_reverse_current_artifact_keys advisory 字段。
5. 审计未能在 current_state.json 中验证 local_reverse_training/current_ida_evidence。
```

已有 current artifact keys：

```text
local_reverse_ida_summary
local_reverse_ida_evidence_18019fca52b389fe
local_reverse_ida_evidence_4c69f173f2bd0211
local_reverse_ida_evidence_bcbd9979db015bfd
```

当前 `negative_results.json` 中的 hard/soft blocks 主要属于旧 `samplereverse` 解题线；本轮不运行 solver、不重复旧 sample_solver、不读取完整 solve_reports，因此不触发这些失败方向。

---

## 3. Do Not Do

严禁：

```text
1. 不重新运行 IDA。
2. 不运行 solver。
3. 不运行 ida_summary_guided_solver_v1。
4. 不处理新样本。
5. 不扩大到 22 个样本。
6. 不复制、上传、提交、base64/hex 编码 E:\reverse 下的样本二进制。
7. 不读取完整 solve_reports/。
8. 不读取完整 PROJECT_PROGRESS_LOG.txt。
9. 不修改 .codex-skills/。
10. 不删除旧 samplereverse 兼容字段。
11. 不大改 artifact_index.json；除非发现 current_state 需要同步 artifact_key 名称，只允许最小同步。
12. 不把 task_packet.task 当执行权威。
13. 不将 stale/missing artifact 标为 current。
```

允许：

```text
1. 修改 project_state/current_state.json。
2. 修改 project_state/codex_execution_report.md。
3. 修改 project_state/pytest_result.txt。
4. 必要时只同步 project_state/task_packet.json 的 state_refresh_round/advisory 字段，但不得修改旧 task_packet.task。
5. 读取 project_state/artifact_index.json 来引用 artifact keys 和 paths。
6. 读取 project_state/local_reverse_ida_summary.json 来确认 3 个目标的 summary 状态。
```

---

## 4. Files To Inspect

必须读取：

```text
project_state/current_state.json
project_state/artifact_index.json
project_state/local_reverse_ida_summary.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/decision_packet.md
```

必要时读取：

```text
project_state/task_packet.json
project_state/negative_results.json
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/
PROJECT_PROGRESS_LOG.txt
```

---

## 5. Required Audit

Codex 必须在 `project_state/codex_execution_report.md` 中写明：

```text
1. 当前 decision_packet 是执行权威。
2. 本轮是 REWORK，目标只修正 current_state.json 的 local_reverse_training/current_ida_evidence。
3. 上一轮 artifact_index 的 local_reverse artifact 登记保持不变或只做必要最小同步。
4. 未重新运行 IDA。
5. 未运行 solver。
6. 未运行 ida_summary_guided_solver_v1。
7. 未处理新样本。
8. 未扩大样本。
9. 未修改 .codex-skills/。
10. 未读取完整 solve_reports/。
11. 未读取完整 PROJECT_PROGRESS_LOG.txt。
12. current_state.json 中可通过文本搜索命中 local_reverse_training。
13. current_state.json 中可通过文本搜索命中 current_ida_evidence。
14. current_ida_evidence 包含 3 个目标，且 sample_id 与 artifact_index 中 3 个 local_reverse_ida_evidence_* 对应。
15. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_current_state_rework_v1",
  "round_id": "round_20260603_local_reverse_current_state_rework_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_current_state_rework_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

只允许改：

```text
project_state/current_state.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

可选最小同步：

```text
project_state/task_packet.json
```

不得改源码，除非 JSON schema/linter 明确阻止添加 `local_reverse_training`，且必须在报告中说明原因。

实现要求：

```text
1. 保留旧 samplereverse 字段。
2. 在 current_state.json 顶层添加 local_reverse_training。
3. local_reverse_training.current_ida_evidence 必须是长度为 3 的数组。
4. 每个条目必须包含 sample_id、relative_path、ida_status、hexrays_available、ida_output_path、artifact_key、next_action。
5. artifact_key 必须与 artifact_index.json 中的 key 一致。
6. next_recommended_decision 必须是 ida_summary_guided_solver_v1。
7. 不把 raw IDA JSON 内容嵌入 current_state，只写路径和摘要。
```

---

## 7. Tests

必须运行：

```bash
python -m json.tool project_state\current_state.json > NUL
```

必须运行文本存在性检查：

```bash
python -c "from pathlib import Path; s=Path('project_state/current_state.json').read_text(encoding='utf-8'); assert 'local_reverse_training' in s and 'current_ida_evidence' in s"
```

必须运行结构检查：

```bash
python -c "import json; d=json.load(open('project_state/current_state.json', encoding='utf-8')); x=d['local_reverse_training']; assert x['summary_status']=='SUCCESS'; assert len(x['current_ida_evidence'])==3; assert all(t['ida_status']=='success' for t in x['current_ida_evidence'])"
```

必须运行：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m pytest -q tests\test_project_state.py
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
1. current_state schema 不允许添加 local_reverse_training。
2. artifact_index.json 中缺少 local_reverse_ida_summary 或 3 个 local_reverse_ida_evidence_* key。
3. local_reverse_ida_summary.json 缺失或不是 SUCCESS。
4. 需要重新运行 IDA 才能继续。
5. 需要进入 solver 才能继续。
6. 需要读取完整 solve_reports/ 才能继续。
7. 需要读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
8. 需要复制、上传、提交或编码样本二进制才能继续。
```

本轮完成标准：

```text
project_state/current_state.json 顶层存在 local_reverse_training；
local_reverse_training.current_ida_evidence 长度为 3；
3 个条目均能指向 artifact_index 中的 current local_reverse_ida_evidence_*；
project_state/codex_execution_report.md 记录返工事实；
project_state/pytest_result.txt 记录真实测试；
没有运行 IDA；
没有运行 solver；
没有扩大样本。
```
