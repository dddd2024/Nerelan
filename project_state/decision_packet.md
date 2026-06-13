```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_select_non_samplereverse_target_v1",
  "round_id": "round_20260613_select_non_samplereverse_target_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮只做本地样本选择，不解题。

用户已确认：当前目标不是 `samplereverse`；当前目标来自 `E:\reverse` 中除 `samplereverse` 以外的题目。`samplereverse` 以后若再处理，必须继承已有历史结论，不能从零重做。

本轮目标：扫描或读取 `E:\reverse` 的 metadata，排除 `samplereverse`，生成非 `samplereverse` 队列，并选出一个明确的 next target sample，供下一轮单样本分析使用。

## 2. Current Evidence

- 当前 `task_packet.json` 和 `current_state.json` 仍指向 `samplereverse`，与用户新约束冲突。
- 当前 `artifact_index.json` 里的缺失项属于旧 sample state，不能作为新样本证据。
- `negative_results.json` 中的禁止方向仍有效：不得盲目扩大搜索、不得重复旧失败方向、不得提交完整历史输出。
- `reverse-agent-iteration@v2` 为 active skill。
- 已有本地 inventory、静态摘要、project_state、artifact_index、报告和 gate 能力；本轮只复用，不重写。
- `decision_packet.md` 是当前执行权威，`task_packet.json` 只是建议。

## 3. Do Not Do

- 不继续把 `samplereverse` 当当前目标。
- 不删除 `samplereverse` 历史记录。
- 不批量解所有题。
- 不运行求解、验证、动态执行或调试流程。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不提交本地样本文件或大体积产物。
- 不修改 `.codex-skills/` 或 `training_materials/`。
- 不重复实现已有工具接口。
- 不把旧 artifact 当新样本 current evidence。

## 4. Files To Inspect

必须读取：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/static_feature_extractor.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`

可生成或更新：

- `project_state/local_reverse_inventory.json`
- `project_state/local_reverse_non_samplereverse_queue.json`
- `project_state/local_reverse_non_samplereverse_selection.json`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_select_non_samplereverse_target_v1/*`

不得默认读取完整历史目录或样本大文件内容。

## 5. Required Audit

Codex 必须：

1. 确认工作目录是 `F:\reverse-agent`。
2. 确认 `E:\reverse` 存在。
3. 校验 decision_meta：status=`APPROVED`，mainline=`training_dataset`，skill active。
4. 记录 `task_packet.json` 不是当前权威，不能继续按 `samplereverse` 执行。
5. 检查现有 inventory/static/project_state 能力，不能重复实现。
6. 生成或更新 `project_state/local_reverse_inventory.json`，只写 project_state，不写 training_materials。
7. 从 inventory 中排除所有 `sample_id`、`display_name`、`relative_path` 或文件名 stem 含 `samplereverse` 的条目，并排除 sha256=`ca74a7867fe97e54e003970d627891cdb6df41c5ad953632fe49e9bce9c619c1`。
8. 生成 `project_state/local_reverse_non_samplereverse_queue.json`，列出最多 30 个 ranked candidates。
9. 生成 `project_state/local_reverse_non_samplereverse_selection.json`，选择一个 next target，且必须标记 `is_samplereverse=false`。
10. 如更新 `current_state.json`、`task_packet.json` 或 `artifact_index.json`，只能写 selected sample 的 metadata，不能伪造已完成证据。

选择规则：优先未解决样本；优先可执行/二进制类文件；优先类别已知；优先 1KB 到 20MB；最后按 relative_path 和 sha256 稳定排序。

## 6. Implementation Scope

允许修改或生成：

- `project_state/local_reverse_inventory.json`
- `project_state/local_reverse_non_samplereverse_queue.json`
- `project_state/local_reverse_non_samplereverse_selection.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_select_non_samplereverse_target_v1/*`

只有 schema 不足时，才允许最小修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

不允许修改：`.codex-skills/`、`solve_reports/`、`PROJECT_PROGRESS_LOG.txt`、`training_materials/`、求解器、运行器、GUI、原始样本文件。

## 7. Tests

必须至少运行并记录：

- `pwd`
- `Test-Path F:\reverse-agent`
- `Test-Path E:\reverse`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- inventory 扫描到 `project_state/local_reverse_inventory.json`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py tests/test_tool_capability_inventory.py -q`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `git diff --name-only`

若 `project_state build` 会把状态重置回 `samplereverse`，本轮不要运行它；只有能明确指定 selected sample 时才允许运行。

## 8. Stop Conditions

必须停止并报告：

- `E:\reverse` 不存在。
- inventory 扫描失败。
- 排除 `samplereverse` 后没有候选。
- 无法生成 queue 或 selection。
- selected sample 仍是 `samplereverse`。
- 需要进入解题、验证、动态执行或深度分析才能继续。
- 需要读取完整历史目录才能继续。
- 实现试图重复已有工具能力。
