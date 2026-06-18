```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_training_coverage_matrix_gap_report_v1",
  "round_id": "round_20260618_training_coverage_matrix_gap_report_v1",
  "based_on_state_build_id": "state_20260618_114539_14d4ec94f06b",
  "based_on_state_digest": "14d4ec94f06bab113eb55fdf774e82b449b2851672e927f2b0df7a6052a95cc2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

从已有本地逆向训练样本 inventory 出发，生成题型覆盖矩阵、solver/tool 能力映射和两周训练缺口报告。

本轮不是从零建立 inventory。已有事实包括：`training_materials/local_reverse/inventory.json` 曾记录 50 个 metadata-only 样本，`status_overlay.json` 曾记录 1 solved、2 blocked、1 needs_triage、46 inventory_only，`project_state/local_reverse_evaluation_queue.json` 曾记录 41 个 static-triage-first 队列项。本轮目标是在这些已有基础上刷新 current 状态，并把“样本清单”推进到“能力建设地图”。

目标产物：

1. `project_state/local_reverse_training_inventory_refresh.json`
2. `project_state/local_reverse_training_coverage_matrix.json`
3. `project_state/local_reverse_solver_tool_capability_map.json`
4. `project_state/local_reverse_training_gap_report.md`
5. 必要时更新 `project_state/artifact_index.json`、`project_state/current_state.json`、`project_state/codex_execution_report.md`、`project_state/pytest_result.txt` 和 gate artifacts。

覆盖矩阵必须面向用户两周目标，至少覆盖：字符串比较、XOR、移位、位运算、查表、RC4、DES、TEA、Base64、hash/MD5/SHA、GUI 校验、简单反调试、mixed/unknown。

本轮不求解样本，不运行样本，不执行 runtime probe。只允许 metadata/status/coverage 层面的只读分析和已有工具接口审计。

## 2. Current Evidence

主线是 `training_dataset`。

已有训练集基础不是空白：历史 `training_local_reverse_inventory_audit_v1` 已确认本地训练样本 inventory、status overlay 和 evaluation queue 存在。当前 `task_packet.json` 仍指向旧 `samplereverse` reverse-solving 建议，但执行权威是 `project_state/decision_packet.md`。

当前 `task_packet.json` 的 state build 已刷新为 `state_20260618_114539_14d4ec94f06b`，digest 为 `14d4ec94f06bab113eb55fdf774e82b449b2851672e927f2b0df7a6052a95cc2`，但内容仍偏 sample_state/reverse-solving，不足以支撑训练集能力建设。

`negative_results.json` 中禁止旧 reverse-solving 方向，包括 old sample_solver blind search、budget-only expansion、compare_semantics_agree=false candidate、提交完整 solve_reports，以及重复旧 samplereverse 失败分支。本轮不触碰这些方向。

本轮进入 training_dataset 前必须检查已有能力：sample metadata、training inventory、status overlay、evaluation queue、solver 模板、static triage、IDA/Ghidra/debugger/tool runner/harness/StructuredEvidence 接口。成熟工具优先，不重复实现已有接口。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner 或 GUI/frontend workflow。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要提交完整 `solve_reports/`。

不要修改 `.codex-skills/`。

不要把单个样本 candidate、flag、本地绝对路径、一次性运行结论写进 skill。

不要把训练集建设变成单样本硬编码。

不要默认读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

不要把 `task_packet.task` 当成本轮执行权威。

不要把 stale/missing artifact 当 current evidence。

## 4. Files To Inspect

默认先读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

训练集相关重点检查：

1. `training_materials/local_reverse/inventory.json`
2. `training_materials/local_reverse/status_overlay.json`
3. `project_state/local_reverse_evaluation_queue.json`
4. `project_state/local_reverse_training_inventory_audit.md`
5. `project_state/local_reverse_training_resume_plan.json`
6. `reverse_agent/local_reverse_inventory.py`
7. `reverse_agent/local_reverse_training_status.py`
8. `reverse_agent/local_reverse_single_sample_static_triage.py`
9. `reverse_agent/tool_runners.py`
10. `tests/test_local_reverse_training_status.py`
11. 与 solver/tool capability 直接相关的现有源码和测试入口。

只允许有界读取历史 round：

- `project_state/rounds/round_20260612_training_local_reverse_inventory_audit_v1/*`
- `project_state/rounds/round_20260612_training_metadata_contract_repair_v1/*`
- `project_state/rounds/round_20260616_local_reverse_training_resume_plan_v1/*`

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录。
5. `decision_meta.status=APPROVED`。
6. `mainline=training_dataset`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. 本轮是训练集 metadata/coverage 工作，不是逆向样本求解。

必须审计并记录：

1. 当前 inventory 样本数、metadata-only 策略是否仍有效。
2. 当前 status overlay 的 solved/blocked/needs_triage/inventory_only 统计。
3. 当前 evaluation queue 的 item 数、策略、允许/禁止动作。
4. 每个样本已有 category/tags 是否足以映射到题型覆盖矩阵。
5. 已有 solver/tool/harness/static-triage 能力入口有哪些，哪些题型已有能力，哪些只是未验证能力。
6. 是否存在 IDA/IDAPython runner、Ghidra runner、debugger runner、strings/file/objdump/radare2 静态提取入口、StructuredEvidence 转换、candidate verification/harness。
7. 题型覆盖矩阵中每个能力结论的证据来源和 freshness。

## 6. Implementation Scope

优先只生成/更新 project_state training artifacts：

- `project_state/local_reverse_training_inventory_refresh.json`
- `project_state/local_reverse_training_coverage_matrix.json`
- `project_state/local_reverse_solver_tool_capability_map.json`
- `project_state/local_reverse_training_gap_report.md`
- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260618_training_coverage_matrix_gap_report_v1/*` only if close-round actually runs and succeeds.

只有当现有 training status 工具无法输出所需 metadata/coverage 字段时，才允许小范围修改：

- `reverse_agent/local_reverse_training_status.py`
- `tests/test_local_reverse_training_status.py`
- `reverse_agent/local_reverse_inventory.py`

不得修改 solver 主逻辑、harness 主逻辑、tool runner 主逻辑，除非只是只读 capability introspection 的小补丁且有测试覆盖。

`local_reverse_training_coverage_matrix.json` 至少包含：

- `schema_version`
- `generated_at`
- `based_on_inventory`
- `type_rows`
- 每类题的 `sample_count`、`sample_ids`、`known_solved_count`、`candidate_solver_modules`、`tool_evidence_available`、`harness_available`、`coverage_status`、`confidence`、`gap`、`next_minimal_task`。

`local_reverse_solver_tool_capability_map.json` 至少包含：

- solver templates
- static extraction tools
- IDA/Ghidra/debugger interfaces
- harness/candidate verification
- StructuredEvidence path
- GUI/CLI entry points
- per-capability tests or evidence freshness

`local_reverse_training_gap_report.md` 必须面向两周目标，输出：

- 当前 50 样本状态摘要。
- 每类题是否已有可复现解题能力。
- 一周内优先补齐的 3-5 个能力缺口。
- 每个缺口的最小下一步任务，不允许直接批量盲跑。
- 哪些能力只能 metadata-level 判断，尚未 live/static triage 验证。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
```

如果已有 training inventory/status CLI，运行只读命令并记录 stdout/stderr；没有则在 report 中明确说明缺口。优先尝试：

```powershell
python -m reverse_agent.local_reverse_training_status --help
python -m reverse_agent.local_reverse_training_status --json
```

随后运行 gate：

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`，运行 close-round 并再次 final-check：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_training_coverage_matrix_gap_report_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 APPROVED。
3. `mainline` 不是 `training_dataset`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、debugger、IDA/Ghidra、emulator、runtime probe 或 sidecar。
6. 需要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改允许范围之外的文件。
8. 发现 inventory/status/queue 缺失且无法只读重建。
9. 题型覆盖矩阵无法说明证据来源或 freshness。
10. 把单次样本 flag/candidate/本地绝对路径写入长期 skill。
11. `report-summary` 或 `final-check` 最终出现 FAIL。
12. 报告声称题型能力已具备，但没有 solver/tool/harness 或测试证据支撑。
