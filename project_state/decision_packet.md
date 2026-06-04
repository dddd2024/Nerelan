```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_affine_static_feature_index_repair_v1",
  "round_id": "round_20260604_affine_static_feature_index_repair_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮是上一轮 `decision_20260604_affine_static_feature_extraction_v1` 的状态索引返工。

上一轮已经生成：

```text
project_state/local_reverse_affine_static_feature_result.json
project_state/local_reverse_affine_static_feature_summary.json
```

但 `artifact_index.json` 未登记这两个新 artifact，导致它们不能作为 current evidence 使用。

本轮目标：**只修复 artifact/current-state 登记与报告一致性**。

---

## 2. Current Evidence

当前可用证据：

```text
decision_packet.md: decision_20260604_affine_static_feature_extraction_v1
codex_execution_report.md: report_20260604_affine_static_feature_extraction_v1
pytest_result.txt: PASSED
generated artifacts:
  - project_state/local_reverse_affine_static_feature_result.json
  - project_state/local_reverse_affine_static_feature_summary.json
```

两个 artifact 内容显示：

```text
sample_id: affine_8cfebe03
analysis_mode: static_only
executed_sample: false
tool_used: reverse_agent/static_feature_extractor.py
recommended_next_action: run_ida_static_export
```

问题：

```text
artifact_index.json 未登记 local_reverse_affine_static_feature_result
artifact_index.json 未登记 local_reverse_affine_static_feature_summary
generated_at 早于本轮 artifact 修改时间
```

`task_packet.json` 仍可能保留旧 samplereverse 派生任务或其他 advisory 字段；本轮以本 `project_state/decision_packet.md` 为执行权威，不以 `task_packet.task` 为准。

`negative_results.json` 中仍需遵守：不回 old sample_solver blind search、不只扩大 beam/budget、不提交 full solve_reports、不重复已失败方向。本轮不涉及样本求解和 runtime probe，因此不应触发这些负面方向。

已有工具能力已确认：`static_feature_extractor.py`、`tool_runners.py`、`local_reverse_ida_summary.py`、`local_reverse_ida_guided_solver.py`、`local_reverse_forced_ida_extract.py`、`local_reverse_targeted_static_reextract.py` 均已存在。Ghidra runner 缺失，但本轮不需要新增。

---

## 3. Do Not Do

严禁：

```text
1. 不重新运行 affine.exe。
2. 不运行 solver。
3. 不运行 IDA/Ghidra。
4. 不运行 debugger/runtime probe/emulator。
5. 不上传原始样本。
6. 不修改 .codex-skills。
7. 不读取完整 solve_reports。
8. 不重做静态扫描，除非发现两个 artifact 文件缺失或 JSON 损坏。
9. 不扩大到其他样本。
10. 不把 affine 单题结论写入长期 skill。
11. 不新建重复 static extractor、IDA runner 或 Ghidra runner。
12. 不把 stale/missing artifact 当作 current evidence。
```

允许：

```text
1. 读取 project_state 下本轮两个 affine static feature artifact。
2. 读取 artifact_index/current_state 中与 local_reverse artifact 登记直接相关的字段。
3. 运行 project_state build 或做最小 artifact_index 兼容登记。
4. 更新 codex_execution_report.md 和 pytest_result.txt。
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
project_state/local_reverse_affine_static_feature_result.json
project_state/local_reverse_affine_static_feature_summary.json
```

必要时读取：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认两个 affine static feature artifact 存在且 JSON 可解析。
2. 是否确认 artifact sample_id 为 affine_8cfebe03。
3. 是否确认 executed_sample=false。
4. 是否没有重新运行样本。
5. 是否没有运行 solver/IDA/Ghidra/debugger/runtime probe。
6. 是否将两个 artifact 登记进 artifact_index latest_artifacts。
7. 是否将两个 artifact 登记进 artifact_index latest_artifacts_v2。
8. latest_artifacts_v2 是否包含 freshness=current。
9. source_run 是否为本轮 round_id。
10. sha256/size_bytes/modified_at 是否记录。
11. 是否更新 codex_execution_report.md。
12. 是否更新 pytest_result.txt。
13. 是否没有修改 .codex-skills。
14. 是否没有提交 solve_reports 全量目录。
15. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_affine_static_feature_index_repair_v1。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/artifact_index.json
project_state/current_state.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

优先方式：

```bash
python -m reverse_agent.project_state build
```

如果 build 不能自动纳入本轮两个 artifact，允许最小手动登记，但必须保持旧字段兼容：

```text
latest_artifacts.local_reverse_affine_static_feature_result
latest_artifacts.local_reverse_affine_static_feature_summary
latest_artifacts_v2.local_reverse_affine_static_feature_result
latest_artifacts_v2.local_reverse_affine_static_feature_summary
```

建议 `kind`：

```text
local_reverse_affine_static_feature_result
local_reverse_affine_static_feature_summary
```

`latest_artifacts_v2` 每个条目至少包含：

```json
{
  "kind": "local_reverse_affine_static_feature_result",
  "path": "project_state\\local_reverse_affine_static_feature_result.json",
  "freshness": "current",
  "source_run": "round_20260604_affine_static_feature_index_repair_v1",
  "sha256": "<computed sha256>",
  "size_bytes": 0,
  "modified_at": "<file modified timestamp>"
}
```

summary artifact 使用同样结构，`kind/path` 对应 summary 文件。

如果更新 `current_state.json`，只允许补充 local_reverse_training 或 artifact_refs 中与本轮两个 artifact 直接相关的最小字段，不得覆盖已有 samplereverse 兼容字段，不得删除旧 local_reverse IDA/solver 证据。

---

## 7. Tests

必须运行并记录：

```bash
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

如果修改了 project_state builder 代码，额外运行：

```bash
python -m py_compile reverse_agent/project_state.py
```

以及相关 project_state 测试。

所有 required commands 必须 Exit code 0。若任何命令失败，`codex_execution_report.md` 不得写 `SUCCESS/ACCEPT`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 两个 affine artifact 文件缺失。
2. 两个 artifact JSON 无法解析。
3. artifact 内容显示 sample_id 不是 affine_8cfebe03。
4. artifact 内容显示 executed_sample 不是 false。
5. project_state build 会覆盖或删除现有关键 state。
6. 需要运行样本、IDA/Ghidra、solver 或 runtime probe 才能完成登记。
7. 需要上传原始样本才能完成登记。
```

完成条件：

```text
1. 两个 affine artifact 已进入 artifact_index。
2. latest_artifacts_v2 标记 freshness=current。
3. provenance/source_run 指向本轮 round。
4. report/pytest 与本轮 decision_id 对齐。
5. required tests 全部 Exit code 0。
6. 未运行样本、solver、IDA/Ghidra、debugger、runtime probe。
7. 未上传原始样本。
```
