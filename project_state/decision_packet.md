```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_training_inventory_existing_capability_audit_v1",
  "round_id": "round_20260615_training_inventory_existing_capability_audit_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

审计并复用仓库中已经存在的 training inventory / local reverse training 能力，避免重复实现 sample inventory skeleton。

本轮不是新建 inventory 骨架，而是确认现有能力的边界、测试覆盖、CLI/报告入口和 project_state 关联是否清晰。若已有能力可用，只补最小测试或文档缺口；只有发现明确缺口且无法由现有模块承担时，才允许做小范围修补。

本轮目标：

1. 梳理现有 training inventory 相关实现与历史 round。
2. 确认 `reverse_agent/local_reverse_inventory.py`、`reverse_agent/local_reverse_training_status.py`、`reverse_agent/local_reverse_training_review.py`、`training_materials/local_reverse/README.md`、`project_state/local_reverse_training_inventory_audit.md` 等现有产物的职责。
3. 确认是否已有测试覆盖 inventory 不执行样本、不写 absolute path、稳定排序、忽略大目录/临时目录、sha256/size/suffix/relative_path 等基础约束。
4. 若测试或文档不足，最小补齐；不得重复创建新的 inventory CLI 或新的并行 schema。
5. 不扫描真实外部样本目录，不运行 solver，不推进任何具体样本求解。

## 2. Current Evidence

已通过仓库搜索确认 training inventory 相关能力并非空白：

- `reverse_agent/local_reverse_inventory.py` 已存在；
- `reverse_agent/local_reverse_training_status.py` 已存在；
- `reverse_agent/local_reverse_training_review.py` 已存在；
- `training_materials/local_reverse/README.md` 已存在；
- `project_state/local_reverse_training_inventory_audit.md` 已存在；
- 历史 rounds 中已有：
  - `round_20260611_refresh_training_inventory_and_queue_v1`
  - `round_20260611_rework_training_inventory_test_and_report_integrity_v1`
  - `round_20260612_training_local_reverse_inventory_audit_v1`
  - `round_20260612_training_metadata_contract_repair_v1`
  - `round_20260613_training_queue_static_triage_hygiene_v1`

因此，上一份 `training_dataset_inventory_skeleton_v1` 的方向过于接近重复造轮子。当前任务改为 existing capability audit / gap repair。

上一轮工程门禁状态稳定：

- `round_20260615_startup_status_baseline_consistency_guard_v1` 已 ACCEPTED；
- `startup_baseline_consistency` 已通过；
- final gate 无 blocking / warnings；
- archive 已完成。

## 3. Do Not Do

不要新建第二套 inventory 模块、第二套 metadata schema、第二套 training queue 或第二套 CLI，除非先证明现有实现无法承担且报告中说明原因。

不要推进任何逆向样本求解。

不要运行 sample、solver、runtime probe、debugger、hook、emulator、sidecar、IDA、Ghidra、x64dbg、OllyDbg、radare2、strings 批量提取、file 批量扫描或 harness run。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要扫描真实外部样本目录，例如 `E:\reverse`、`D:\reverse`、`C:\Users\*\Downloads`。

不要创建数据库、队列服务、前端、多 agent 调度或 workflow engine。

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

必须有界读取现有 training inventory 能力：

- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_training_review.py`
- `training_materials/local_reverse/README.md`
- `project_state/local_reverse_training_inventory_audit.md`

必须有界读取相关历史 round 的 summary / report，而不是完整历史目录：

- `project_state/rounds/round_20260611_refresh_training_inventory_and_queue_v1/codex_execution_report.md`
- `project_state/rounds/round_20260611_rework_training_inventory_test_and_report_integrity_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_training_local_reverse_inventory_audit_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_training_metadata_contract_repair_v1/codex_execution_report.md`
- `project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/codex_execution_report.md`

查找相关测试，但不要无界读取全仓：

- `tests/test_local_reverse_inventory.py`
- `tests/test_local_reverse_training_status.py`
- `tests/test_local_reverse_training_review.py`
- 其他 `tests/test_*inventory*` / `tests/test_*training*` / `tests/test_*dataset*`

## 5. Required Audit

执行前确认：

1. 当前 `decision_packet.md` 是 `decision_20260615_training_inventory_existing_capability_audit_v1`。
2. `reverse-agent-iteration@v2` 来自 active registry。
3. 当前主线是 `training_dataset`。
4. `task_packet.json` 只是 advisory/state input，不能覆盖本轮 decision。
5. 旧 `samplereverse` 状态不能作为当前训练集任务的执行依据。
6. 本轮不得切换到 `reverse_solving`、`tool_integration` 或工程重构。
7. 必须先复用现有 `local_reverse_inventory` / training status / review 能力，不能假设不存在。
8. 若发现已有测试已覆盖本轮核心要求，允许只补审计报告和归档，不做源码修改。
9. 若发现文档与实现不一致，优先修正文档或测试，不新建模块。
10. 若需要真实样本目录才能继续，停止并报告 `BLOCKED`。

## 6. Implementation Scope

优先无代码或最小补测试/文档。

允许修改：

- `reverse_agent/local_reverse_inventory.py`，仅限修复现有 inventory bug 或补稳定性接口；
- `reverse_agent/local_reverse_training_status.py`，仅限修复现有 status 汇总 bug；
- `reverse_agent/local_reverse_training_review.py`，仅限修复现有 review 汇总 bug；
- 现有相关测试文件；
- `training_materials/local_reverse/README.md` 或 `project_state/local_reverse_training_inventory_audit.md`，仅限同步现有能力说明。

允许新增：

- `tests/test_local_reverse_inventory.py`，仅在不存在或缺关键覆盖时；
- 小型审计 markdown，例如 `project_state/local_reverse_training_inventory_capability_audit.md`。

不允许新增：

- 新的平行 inventory 模块；
- 新的平行 metadata schema；
- 新的训练集数据库；
- 新的 solver/harness 执行入口。

允许生成或更新：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_training_inventory_existing_capability_audit_v1/*`

只读，不得修改：

- live `project_state/decision_packet.md`，除本文件由 GPT 预先上传外，Codex 执行期间不得修改；
- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- solver / strategy / transform / probe / IDA / Ghidra / debugger 相关模块，除非只是 import-safe 检查且无行为改变。

本轮不应运行 live `project_state build`。若测试需要 inventory 输入，使用 pytest 临时目录和假样本文件。

## 7. Acceptance Criteria

必须产出一份短审计结论，说明：

1. 现有 inventory 能力入口是什么；
2. 它是否支持有界扫描；
3. 它是否避免 absolute local path 写入长期输出；
4. 它是否只登记文件、不执行样本；
5. 它是否有稳定排序和 sha256/size/suffix/relative_path 等字段；
6. 它是否忽略 `.git`、`__pycache__`、`.venv`、`node_modules`、`solve_reports` 或等价目录；
7. 当前缺口是什么；
8. 本轮是否补了测试或文档；
9. 后续若要读取真实 `E:\reverse`，需要新的 explicit decision。

若发现上述能力已经完整，Codex 可以不改源码，只更新 report / pytest / gate / round archive，并说明 `no code changes required`。

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
python -m pytest tests/test_local_reverse_inventory.py tests/test_local_reverse_training_status.py tests/test_local_reverse_training_review.py tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_training_inventory_existing_capability_audit_v1
```

如果部分 listed test files 不存在，Codex 必须选择实际存在的 closest tests，并在 report 中说明缺失文件和替代测试；不得让 pytest 因不存在测试文件失败后仍写 SUCCESS。

必须新增或确认测试覆盖：

1. inventory 不记录 absolute local path；
2. inventory 输出排序稳定；
3. inventory 生成 sha256、size、suffix、relative_path；
4. `.git`、`__pycache__`、`.venv`、`node_modules`、`solve_reports` 默认被忽略或被文档化为不扫描；
5. 有界扫描限制存在或明确由调用方 root 限制；
6. 空目录输出合法；
7. 临时目录中的假 `.exe` / `.bin` 文件只被登记，不被执行；
8. 不触发 solver/harness/runtime probe；
9. project gate 仍能通过；
10. 已有 decision immutability / startup baseline consistency / verified CLI coverage 不回退。

## 9. Stop Conditions

如果发现本轮会重复实现已有 inventory，停止并报告 `REWORK_REQUIRED`。

如果需要运行真实样本、solver、runtime probe、debugger、hook、emulator、sidecar，停止并报告 `BLOCKED`。

如果需要读取完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt` 或外部样本目录才能继续，停止并报告 `BLOCKED`。

如果需要修改 live `project_state/decision_packet.md` 才能通过，停止并报告 `REWORK_REQUIRED`。

如果启动时 live `project_state/decision_packet.md` dirty，停止并报告 `BLOCKED`。

如果 `command-plan` 不是 `PASSED`，不得写 `SUCCESS`。

如果 `report-summary / final-check / close-round` 任一 exit 非 0，不得写 `SUCCESS`。

如果 `pytest_result.txt` 缺失、测试未真实运行、report/decision id 不匹配，不得提交 `SUCCESS` 报告。
