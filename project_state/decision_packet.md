```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_local_reverse_metadata_inventory_v1",
  "round_id": "round_20260604_local_reverse_metadata_inventory_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **training_dataset**。

用户明确要求：本地训练样本目录在 `E:\reverse`，但原始样本文件不上传到 GitHub。本轮只上传训练集建设计划，并要求下一轮 Codex 建立 metadata-only inventory。

下一轮目标：

```text
1. 以 E:\reverse 为本地样本根目录。
2. 只读取样本文件的元数据，不复制样本本体。
3. 生成本地样本清单 inventory。
4. 生成可提交到 GitHub 的 metadata-only inventory。
5. 生成 harness-compatible cases metadata。
6. 更新 README，说明原始样本只保留在本地。
7. 更新 project_state 报告和测试记录。
```

本轮上传的是计划，不执行扫描，不上传样本，不生成 candidate，不求解具体题目。

## 2. Current Evidence

当前 project_state 已经包含本地逆向样本相关状态和 IDA evidence artifact。上一轮报告显示本地样本方向已经进入证据提取阶段，但还缺少稳定的训练集 inventory 层。

当前 `task_packet.json` 中仍有旧样本求解派生字段，但本轮执行权威是本 `project_state/decision_packet.md`。

本轮主线改为 `training_dataset`，不是 `reverse_solving`，不是 `tool_integration`。

## 3. Do Not Do

严禁：

```text
1. 不上传 E:\reverse 中的原始样本文件。
2. 不复制 E:\reverse 到仓库。
3. 不提交 local_reverse_samples 下的本地内容。
4. 不提交 solve_reports 全量目录。
5. 不运行动态分析或调试。
6. 不生成 candidate 或 flag。
7. 不修改 .codex-skills。
8. 不引入数据库、服务端平台或重型工作流系统。
9. 不把单题事实写入长期 skill。
```

允许：

```text
1. 新增轻量 inventory 生成脚本。
2. 生成 metadata-only JSON。
3. 生成 cases metadata。
4. 更新 README 和 project_state。
5. 使用测试样本夹做单元测试。
```

## 4. Files To Inspect

默认必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
```

必须检查已有能力：

```text
reverse_agent/local_samples.py
reverse_agent/harness.py
README.txt
.gitignore
tests/test_local_samples.py
tests/test_project_state.py
```

允许新增：

```text
reverse_agent/local_reverse_inventory.py
tests/test_local_reverse_inventory.py
training_materials/local_reverse/README.md
training_materials/local_reverse/inventory.json
training_materials/local_reverse/cases/*.json
project_state/local_reverse_inventory.json
```

不要默认读取完整历史产物目录或完整进度日志。

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否只生成 metadata，没有提交原始样本。
2. inventory 是否包含 sample_id、relative_path、sha256、size_bytes、extension、category、tags。
3. GitHub-safe inventory 是否避免本地绝对路径。
4. cases metadata 是否兼容 reverse_agent.harness.load_harness_cases。
5. README 是否说明原始样本保留在本地。
6. 是否没有提交本地样本目录或运行产物目录。
7. 是否没有运行动态分析或调试。
8. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_local_reverse_metadata_inventory_v1。
9. pytest_result.txt 是否记录真实测试命令。
```

## 6. Implementation Scope

推荐新增 CLI：

```powershell
python -m reverse_agent.local_reverse_inventory scan --samples-root E:\reverse --out project_state\local_reverse_inventory.json --github-out training_materials\local_reverse\inventory.json --cases-dir training_materials\local_reverse\cases
```

推荐 metadata 字段：

```text
sample_id
display_name
relative_path
sha256
size_bytes
extension
guessed_file_type
category
tags
status
github_upload_policy
```

GitHub-safe 输出只能保存相对路径和哈希等元数据。需要本地运行时，通过 `LOCAL_REVERSE_ROOT` 指向 `E:\reverse`。

## 7. Tests

必须运行：

```text
python -m py_compile reverse_agent/local_reverse_inventory.py
python -m pytest -q tests/test_local_reverse_inventory.py
python -m pytest -q tests/test_local_samples.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

测试最低覆盖：

```text
1. 使用测试样本夹生成 inventory。
2. sample_id 稳定且安全。
3. metadata 字段正确。
4. GitHub-safe inventory 不含本地绝对路径。
5. cases metadata 可被 harness loader 读取。
6. README 说明 metadata-only 策略。
```

## 8. Stop Conditions

立即停止并报告 BLOCKED：

```text
1. E:\reverse 不存在且必须扫描真实目录。
2. 需要上传原始样本才能继续。
3. metadata 输出无法避免本地绝对路径。
4. cases metadata 无法兼容现有 harness loader。
5. project_state lint 失败且无法小范围修复。
```

完成条件：

```text
1. inventory CLI 可用。
2. 生成 project_state/local_reverse_inventory.json。
3. 生成 training_materials/local_reverse/inventory.json。
4. 生成 training_materials/local_reverse/cases/*.json。
5. README 记录 metadata-only 策略。
6. 未提交原始样本。
7. 测试和 lint 通过。
8. 报告与测试记录对齐本 decision_id。
```
