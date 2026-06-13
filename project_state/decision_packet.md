```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_rework_static_triage_state_closure_v1",
  "round_id": "round_20260613_rework_static_triage_state_closure_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复上一轮 one-sample static triage 的状态闭环问题。目标不是继续解题，而是让 `affine_8cfebe03` 的静态 triage 结果可以被 project_state 正确审计、登记和复用。

本轮不生成 candidate、flag、password，不运行 runtime validation、debugger、emulator、hook、solver 或 harness campaign。

## 2. Current Evidence

- `project_state/decision_packet.md` 是当前执行权威，`task_packet.json` 只能作为建议。
- 上一轮 Codex 报告为 `PARTIAL`，`acceptance_recommendation=BLOCKED`，不能直接验收。
- 上一轮已选择 rank=1 样本 `affine_8cfebe03`，不是 `samplereverse`。
- 已生成 `project_state/local_reverse_affine_8cfebe03_static_triage.json`。
- 该 artifact 记录 `executed_sample=false`、`static_only=true`、`runtime_validated=false`、`tool_status=blocked`、`blocked_reason=STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`。
- IDA 无 evidence JSON 是 static tool blocker，不是样本语义失败，也不是解题结果。
- 当前问题不是继续分析样本，而是状态闭环缺陷：
  - preflight / command-plan / pytest / lint-report / final-check 未形成通过闭环；
  - triage artifact 的 `mainline` 与本轮 `training_dataset` 主线不一致；
  - triage artifact 未作为 current metadata artifact 登记进 `artifact_index.json`；
  - queue reason 对非 PE 文件固定写成 “PE sample”；
  - decision Tests 格式不满足 command-plan 的 fenced bash block 要求。
- `negative_results.json` 的禁止方向仍有效：不得回到 blind search、不得单纯扩大预算、不得提交完整运行目录、不得重复旧失败方向。
- 现有工具能力必须复用：`local_reverse_training_status.py`、`local_reverse_single_sample_static_triage.py`、IDA evidence collector、project_state/project_gate；不得重复实现 inventory、queue builder、static triage adapter。

## 3. Do Not Do

- 不运行 solver。
- 不生成 candidate、flag、password。
- 不运行 runtime validation、debugger、emulator、hook、harness campaign。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不修改 `.codex-skills/`。
- 不批量处理 `E:\reverse`。
- 不提交 raw sample、IDA database、debug trace 或大体积本地产物。
- 不把 IDA 无输出改写成样本语义失败。
- 不把旧 `samplereverse` artifact 当作当前样本证据。
- 不把 `samplereverse` 重新作为本轮目标。
- 不重复实现已有 IDA/Ghidra/debugger/solver/harness 接口。

## 4. Files To Inspect

必须读取：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_selected_static_triage_target.json`
- `project_state/local_reverse_affine_8cfebe03_static_triage.json`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`
- `tests/test_tool_capability_inventory.py`

可按需读取：

- `.codex-skills/registry.json`
- 当前 active skill profile
- `reverse_agent/tool_runners.py`
- `reverse_agent/ida_scripts/collect_evidence.py`

## 5. Required Audit

Codex 必须确认：

1. 当前目录是 `F:\reverse-agent`。
2. `project_state/decision_packet.md` 是当前执行权威。
3. `task_packet.json/current_state.json` 仍是旧 `samplereverse` 状态，不能作为本轮样本权威。
4. 上一轮 report 是 `PARTIAL/BLOCKED`，不能直接验收。
5. `affine_8cfebe03` triage artifact 存在。
6. triage artifact 中 `executed_sample=false`、`static_only=true`、`runtime_validated=false`。
7. IDA 无输出记录为 static tool blocker。
8. triage artifact 当前未正确进入 `artifact_index.json`。
9. triage artifact 的 `mainline` 字段存在与本轮主线不一致的问题。
10. queue reason 对非 PE 文件存在固定 “PE sample” 文案问题。
11. 本轮不做任何解题、候选生成或运行时验证。
12. 如发现 preflight、command-plan、doctor、lint-report、report-summary、final-check 的失败是 decision 格式或 gate 实现问题，必须做最小修复并记录证据。

## 6. Implementation Scope

允许最小修改：

- `reverse_agent/local_reverse_single_sample_static_triage.py`
  - 不要硬编码 `mainline=tool_integration`。
  - 应允许由 caller、queue 或 decision 指定当前 decision mainline；或者明确拆分 `decision_mainline` 与 `proposed_next_mainline`，避免把 triage 后续建议误写成本轮主线。
  - blocked artifact 和 success artifact 都必须保持一致字段。

- `reverse_agent/local_reverse_training_status.py`
  - 修复 `_queue_reason()`，不要对 PDF、脚本、非 PE 文件固定写 “PE sample”。
  - queue item 可保留 `proposed_next_mainline=tool_integration`，但不得影响本轮 `decision_meta.mainline=training_dataset`。

- `reverse_agent/project_state.py` 或现有 artifact index 写入逻辑
  - 将 `project_state/local_reverse_affine_8cfebe03_static_triage.json` 作为 current metadata artifact 登记进 `artifact_index.json`。
  - kind 建议为 `local_reverse_single_sample_static_triage`。
  - 必须记录 path、sha256、size_bytes、modified_at、source_run、freshness=current。
  - 不得把旧 `samplereverse` missing artifacts 当作当前证据。

- 对应最小测试
  - 覆盖 static triage artifact mainline/provenance。
  - 覆盖 queue reason 非 PE 文案。
  - 覆盖 static tool blocker artifact 可被 training status overlay 识别为 `needs_triage`，不是 `blocked/solved`。

允许更新或生成：

- `project_state/artifact_index.json`
- `project_state/local_reverse_affine_8cfebe03_static_triage.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_training_status.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_rework_static_triage_state_closure_v1/*`
- 与上述最小源码修改对应的测试文件

不允许修改：

- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw sample 文件
- solver 模块
- harness 模块
- debugger/olly scripts
- IDA evidence collector，除非确认只是调用参数错误，且修复范围最小、有测试覆盖

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```bash
pwd
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.local_reverse_training_status --github-status-out ""
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id affine_8cfebe03 --queue project_state/local_reverse_evaluation_queue.json --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_affine_8cfebe03_static_triage.json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_project_gate.py tests/test_tool_capability_inventory.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
git diff --name-only
```

验收标准：

- preflight 通过，或若仍失败，必须明确是本轮无法解决的 gate 缺陷并给出最小复现。
- command-plan 能解析 Tests fenced bash block。
- `local_reverse_affine_8cfebe03_static_triage.json` 已登记进 `artifact_index.json`，freshness 为 current。
- triage artifact 不再把本轮主线错误写成 `tool_integration`。
- queue reason 不再把非 PE 文件固定写成 “PE sample”。
- pytest 无新增失败；如仍有 baseline 失败，必须证明与本轮无关并在报告中列出。
- report-summary 与 final-check 必须运行；不能再以“依赖 report 更新”为理由跳过最终闭环。

## 8. Stop Conditions

必须停止并报告：

- preflight 仍因 Implementation Scope 或 forbidden paths 失败，且不能通过 decision 格式修复解决。
- command-plan 仍无法解析 Tests section。
- artifact 仍无法登记进 `artifact_index.json`。
- triage artifact 仍把本轮主线写错。
- pytest 出现新增失败。
- Codex 需要运行 runtime/debugger/solver 才能继续。
- 任何修改越过本轮 Implementation Scope。
- 发现需要修改 `.codex-skills/`、`training_materials/`、`solve_reports/` 或 raw sample 文件才能继续。
