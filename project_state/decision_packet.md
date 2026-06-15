```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_training_dataset_inventory_skeleton_v1",
  "round_id": "round_20260615_training_dataset_inventory_skeleton_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

开始训练集主线的最小可审计建设：建立 **sample inventory / metadata skeleton**，用于以后管理本地逆向题目目录。

本轮目标不是解题，不是批量运行 solver，也不是接入 IDA/Ghidra/debugger。目标是让项目具备一个可测试、可扩展、不会误触发求解流程的样本清单骨架。

本轮只允许完成以下小目标：

1. 审计仓库中是否已有 sample inventory、dataset metadata、harness sample registry、artifact 登记或训练集相关实现。
2. 若已有能力，优先复用并补测试/文档，不重复造轮子。
3. 若没有已有能力，新增一个最小 sample inventory 模块或 CLI。
4. inventory 只记录静态文件元数据，不执行样本，不运行 solver，不调用 runtime probe。
5. 用 pytest 临时目录构造假样本，验证 inventory 输出稳定。
6. 不读取真实外部样本目录，例如 `E:\reverse`，除非后续新 decision 明确授权。

## 2. Current Evidence

上一轮 `round_20260615_startup_status_baseline_consistency_guard_v1` 已经 ACCEPTED：

- `codex_execution_report.md` 为 `SUCCESS / ACCEPTED`；
- `pytest_result.txt` 记录 `559 passed`；
- `command-plan` 为 `PASSED`；
- `startup_baseline_consistency` 为 `PASS`；
- `final_gate_result.json` 为 `PASSED`，`blocking_reasons: []`，`warnings: []`；
- round archive 已完成。

当前工程门禁已经足够支撑下一步小范围主线切换。

仍需注意：

- `task_packet.json` 仍保留旧 `samplereverse / collect_missing_evidence / sample_state` 信息；
- 这些旧信息只能作为历史状态或 advisory/state input；
- 当前执行权威仍是 `project_state/decision_packet.md`；
- 当前主线是 `training_dataset`，不得被旧 sample task 牵引回 `reverse_solving`。

## 3. Do Not Do

不要推进任何具体逆向样本求解。

不要运行 sample、solver、runtime probe、debugger、hook、emulator、sidecar、IDA、Ghidra、x64dbg、OllyDbg、radare2、strings 批量提取、file 批量扫描或 harness run。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要扫描真实外部样本目录，例如 `E:\reverse`、`D:\reverse`、`C:\Users\*\Downloads`。

不要创建大规模数据库、队列、服务端、前端、多 agent 调度或 workflow engine。

不要修改 solver、strategy、transform、probe、IDA/Ghidra/debugger/harness 语义。

不要修改 `.codex-skills/`。

不要修改 live `project_state/decision_packet.md`。

不要清空、伪造或删除旧 `artifact_index.json` 中的 missing/stale historical artifacts。

不要把 `task_packet.task` 或 `task_packet.derived_task` 当作当前执行任务。

不要把单个样本的 candidate、flag、local absolute path、runtime metric 写入长期 skill 或默认 metadata。

## 4. Files To Inspect

必须读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `project_state/gates/final_gate_result.json`
9. `.codex-skills/registry.json`
10. `README.md`
11. `pyproject.toml` 或等价测试/入口配置文件

必须有界搜索现有能力，避免重复实现：

- sample inventory / dataset / metadata / registry；
- harness sample discovery；
- artifact_index 登记；
- CLI 入口；
- existing schema / pydantic / dataclass；
- IDA / Ghidra / debugger / strings / file / objdump / radare2 工具接口；
- solver 模板与 harness 入口，但只读，不调用。

重点检查可能相关文件：

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `reverse_agent/**/harness*`
- `reverse_agent/**/sample*`
- `reverse_agent/**/dataset*`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`
- 任何已有 `tests/test_*sample*` / `tests/test_*dataset*` / `tests/test_*inventory*`

## 5. Required Audit

执行前确认：

1. 当前 `decision_packet.md` 是 `decision_20260615_training_dataset_inventory_skeleton_v1`。
2. `reverse-agent-iteration@v2` 来自 active registry。
3. 当前主线是 `training_dataset`。
4. `task_packet.json` 只是 advisory/state input，不能覆盖本轮 decision。
5. 旧 `samplereverse` 状态不能作为当前训练集 inventory 的唯一依据。
6. 本轮不得切换到 `reverse_solving`、`tool_integration` 或 `engineering_branch` 重构。
7. 必须先检查已有 training/sample/dataset/harness 能力，不能假设不存在。
8. 若发现已有 inventory 能力，优先补测试/文档；不得新建重复 CLI 或重复 schema。
9. 若要使用 `file`、`strings`、IDA/Ghidra 等成熟工具，本轮只能登记为未来扩展点，不得执行。
10. 若本轮需要真实样本目录才能继续，停止并报告 `BLOCKED`，不要扫描外部路径。

## 6. Implementation Scope

允许修改：

- `reverse_agent/training_inventory.py` 或复用已有同类模块；
- `tests/test_training_inventory.py` 或补充到现有相关测试；
- 必要时 `README.md` 或 `docs/training_dataset_inventory.md`，只写最小使用说明；
- 必要时轻量更新 CLI 入口文件，但不得影响现有 project_state / project_gate 行为。

允许生成或更新：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_training_dataset_inventory_skeleton_v1/*`

只读，不得修改：

- live `project_state/decision_packet.md`，除本文件由 GPT 预先上传外，Codex 执行期间不得修改；
- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- solver / strategy / transform / probe / IDA / Ghidra / debugger 相关模块，除非只是 import-safe 检查且无行为改变。

谨慎允许但默认不需要修改：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`

本轮不应运行 live `project_state build`。如果测试需要验证 inventory 产物格式，使用 pytest 临时目录。

## 7. Inventory Requirements

若需要新增 inventory 能力，最小字段建议如下：

- `schema_version`
- `generated_at`
- `root_label` 或 `root_name`
- `samples[]`
  - `sample_id`
  - `relative_path`
  - `filename`
  - `suffix`
  - `size_bytes`
  - `sha256`
  - `file_role`，例如 `binary_candidate`、`archive_candidate`、`text_note`、`unknown`
  - `category_tags`，默认空数组
  - `status`，默认 `unclassified`
  - `notes`，默认空字符串

约束：

1. inventory 必须默认只扫描调用方指定的 root；不得默认扫描磁盘。
2. inventory 必须支持忽略大目录或隐藏目录，例如 `.git`、`__pycache__`、`.venv`、`node_modules`、`solve_reports`。
3. inventory 不能执行样本，不能 import 样本，不能打开可执行文件运行。
4. inventory 不能把 absolute local path 写入长期输出；输出使用相对路径。
5. inventory 的 sha256 只用于文件身份，不代表已分析或已验证。
6. inventory 输出必须 deterministic：排序稳定、字段稳定。
7. 若实现 CLI，至少支持 `--root`、`--output`、`--max-files` 或等价参数，避免无界扫描。
8. 若实现 schema-only 命令，必须能在不扫描真实样本目录的情况下输出 schema 或帮助信息。

## 8. Tests

必须记录命令、stdout/stderr、exit code 到 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
python -m pytest tests/test_training_inventory.py tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_training_dataset_inventory_skeleton_v1
```

如果 `tests/test_training_inventory.py` 不存在且本轮没有新增 inventory 模块，必须在 report 中说明复用了哪个已有测试文件，并把实际测试文件写入 `tests_ran`。

必须新增或确认测试覆盖：

1. inventory 不记录 absolute local path；
2. inventory 输出排序稳定；
3. inventory 生成 sha256、size、suffix、relative_path；
4. `.git`、`__pycache__`、`.venv`、`node_modules`、`solve_reports` 默认被忽略；
5. `--max-files` 或等价机制能限制扫描规模；
6. 空目录输出合法；
7. 临时目录中的假 `.exe` / `.bin` 文件只被登记，不被执行；
8. 不触发 solver/harness/runtime probe；
9. project gate 仍能通过；
10. 已有 decision immutability / startup baseline consistency / verified CLI coverage 不回退。

## 9. Stop Conditions

如果需要运行真实样本、solver、runtime probe、debugger、hook、emulator、sidecar，停止并报告 `BLOCKED`。

如果需要读取完整 `solve_reports/` 或外部样本目录才能继续，停止并报告 `BLOCKED`。

如果发现仓库已有等价 inventory 实现，停止重复造轮子，改为最小补测试/文档。

如果需要修改 live `project_state/decision_packet.md` 才能通过，停止并报告 `REWORK_REQUIRED`。

如果启动时 live `project_state/decision_packet.md` dirty，停止并报告 `BLOCKED`。

如果 `command-plan` 不是 `PASSED`，不得写 `SUCCESS`。

如果 `report-summary / final-check / close-round` 任一 exit 非 0，不得写 `SUCCESS`。

如果 `pytest_result.txt` 缺失、测试未真实运行、report/decision id 不匹配，不得提交 `SUCCESS` 报告。
