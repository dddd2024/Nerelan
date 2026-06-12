```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_tool_integration_capability_inventory_v1",
  "round_id": "round_20260612_tool_integration_capability_inventory_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮转入 `tool_integration` 主线，只做工具能力盘点与 StructuredEvidence 接入缺口分析，不推进具体样本求解。

目标：建立一个可复用的工具能力库存，明确项目内现有 IDA/Ghidra/debugger/radare2/strings/file/objdump/solver/harness/StructuredEvidence 相关入口、产物路径、freshness 规则和缺口，防止后续逆向任务继续重复造轮子或假设工具接口不存在。

本轮必须产出：

- `project_state/tool_capability_inventory.json`
- `project_state/structured_evidence_gap_report.json`

如果仓库中已经存在同类 inventory/gap report 生成逻辑，则必须复用并小步增强；如果不存在，可新增轻量 CLI，但只允许扫描仓库源码和 project_state，不允许运行外部逆向工具或样本。

## 2. Current Evidence

- 上一轮 `decision_20260612_engineering_baseline_lifecycle_guard_v1` 已验收，final-check、report-summary、lint-report、doctor、close-round 均通过；baseline 生命周期问题已修复。
- 当前 gate closeout 链已经相对稳定，可以从工程自检回到能力建设主线。
- `project_state/local_reverse_training_next_queue.json` 显示本地训练集共有 50 个样本，其中 `inventory_only=46`，`primary_queue` 的条目允许 `bounded_static_triage` 和 `readiness_check`，但不允许 `reverse_solving`、`candidate_generation`、`runtime_validation` 或 `upload_binary`。
- `project_state/local_reverse_training_capability_review.json` 显示 C++ PE inventory-only 样本有 26 个，crypto/cipher PE inventory-only 样本有 6 个，reference/support 文件有 8 个，unknown PE inventory-only 样本有 6 个。
- `current_state.json` 和 `artifact_index.json` 仍包含旧 sample-solving 事实与 stale artifact；本轮不得把这些 stale artifact 当作 current 证据。
- `negative_results.json` 明确禁止旧 sample_solver blind search、单纯扩 beam/budget、使用 compare_semantics_agree=false candidate、提交完整 `solve_reports/` 等方向。本轮不得触碰这些方向。
- `task_packet.json` 只能作为 advisory；当前执行权威是本 `decision_packet.md`。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active。

已有相关能力必须先检查，不能假设不存在：

- IDA / IDAPython 相关 runner、script、artifact adapter。
- Ghidra 相关 runner、script、headless analyzer、artifact adapter。
- OllyDbg / x64dbg / debugger / runtime probe 相关入口。
- strings / file / objdump / radare2 静态工具入口。
- solver 模板、symbolic/constraint solver、harness。
- sample metadata、artifact_index、StructuredEvidence 转换、GUI/CLI 配置入口。

工具运行权限：

- 允许：扫描仓库源码、tests、project_state 的文本和 JSON；运行项目自身 CLI、pytest、lint/doctor/final-check；生成 metadata-only inventory/gap report。
- 不允许：运行 IDA/Ghidra/debugger/radare2/file/strings/objdump 等外部逆向工具；不允许打开、执行、上传或分析样本二进制；不允许运行 harness campaign、solver、candidate search 或 runtime probe。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、winpty、harness campaign、solver 或 candidate search。
- 不运行 radare2、objdump、strings、file 等外部静态工具处理样本。
- 不生成 candidate、flag、password 或答案。
- 不读取完整 `solve_reports/`。
- 不读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不读取、上传或复制 raw sample、sample binary、IDA database、debug trace、大体积历史 artifact。
- 不修改 `.codex-skills/`。
- 不修改训练队列业务分类规则。
- 不修改 solver、harness、IDA/Ghidra/debugger 的执行逻辑；本轮只允许盘点/登记/轻量 schema 或 CLI glue。
- 不把 stale/missing artifact 当 current evidence。
- 不重复实现成熟工具已有能力。
- 不把某一个本地样本的结论写入长期 skill 或通用逻辑。

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
- `project_state/local_reverse_training_next_queue.json`
- `project_state/local_reverse_training_capability_review.json`
- `project_state/local_reverse_training_status.json`
- `training_materials/local_reverse/queue.json`
- `training_materials/local_reverse/status_overlay.json`
- `README.md`
- `reverse_agent/`
- `tests/`

必须有界搜索的关键词：

- `ida`, `idapython`, `ghidra`, `headless`, `x64dbg`, `ollydbg`, `debugger`, `radare2`, `r2`, `objdump`, `strings`, `file`, `StructuredEvidence`, `artifact_index`, `harness`, `solver`, `symbolic`, `z3`, `constraint`, `metadata`, `local_reverse`。

可有界读取：

- 与上述关键词直接命中的源码、测试、schema、README 小节。
- 最新 round manifest，用于确认上轮 gate 状态。

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须：

1. 启动前记录并报告：`pwd`、`Test-Path F:\reverse-agent`、`git rev-parse --show-toplevel`、`git status --short`、`git diff --name-only`。
2. 在任何修改前运行 `python -m reverse_agent.project_gate preflight --state-dir project_state`，确保 baseline 属于当前 decision/round。
3. 明确列出现有工具能力，不得写“项目没有 IDA/Ghidra/debugger 接口”除非已经用有界搜索证实。
4. 对每类能力输出：
   - `capability_name`
   - `tool_family`
   - `existing_entrypoints`
   - `existing_tests`
   - `artifact_outputs`
   - `structured_evidence_mapping`
   - `freshness_policy`
   - `current_status`，只允许 `implemented`、`partial`、`planned`、`missing`、`unknown`
   - `do_not_duplicate`
   - `safe_next_action`
5. `tool_capability_inventory.json` 至少覆盖：
   - IDA / IDAPython
   - Ghidra
   - OllyDbg / x64dbg / debugger
   - strings / file / objdump / radare2
   - solver templates
   - symbolic / constraint solver
   - harness
   - sample metadata
   - artifact_index
   - StructuredEvidence conversion
   - GUI / CLI configuration
6. `structured_evidence_gap_report.json` 必须指出：
   - 哪些工具输出已经能登记进 artifact_index。
   - 哪些工具输出只能作为线索，不能当 current evidence。
   - 哪些工具输出缺少 StructuredEvidence 映射。
   - 下一轮若要对 primary_queue 做 bounded_static_triage，最小需要补齐哪些 adapter/schema 字段。
7. 如果新增 CLI，例如 `python -m reverse_agent.tool_capability_inventory build --state-dir project_state`，必须：
   - 只扫描仓库源码与 project_state。
   - 不运行外部逆向工具。
   - 输出稳定 JSON。
   - 有测试覆盖。
   - 更新 command-plan kind，避免 unknown kind。
8. 若不新增 CLI，只手工生成 JSON，也必须用测试或 project_state doctor/lint 确保 schema 可读、字段完整、决策 ID 匹配。
9. 确认本轮没有运行样本、IDA/Ghidra/debugger/radare2/file/strings/objdump、harness campaign、solver、candidate search 或 runtime probe。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py` only if command-plan kind / gate artifact validation must recognize a new inventory command
- `reverse_agent/project_state.py` only if lint/doctor needs a small compatibility check for the new artifacts
- `tests/test_project_gate.py` only if command-plan/final-check integration is touched
- `tests/test_project_state.py` only if project_state lint/doctor integration is touched
- New lightweight module under `reverse_agent/` only if no equivalent inventory generator exists, for example `reverse_agent/tool_capability_inventory.py`
- New tests only for this inventory/gap-report behavior

允许生成或更新：

- `project_state/tool_capability_inventory.json`
- `project_state/structured_evidence_gap_report.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260612_tool_integration_capability_inventory_v1/*`

不允许修改：

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `training_materials/local_reverse/queue.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_training_next_queue.json`
- `project_state/local_reverse_training_capability_review.json`
- raw local samples
- sample binaries
- solver/harness/IDA/Ghidra/debugger execution logic
- unrelated source modules
- unrelated tests

## 7. Tests

必须运行并完整记录 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
git diff --name-only
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_tool_integration_capability_inventory_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

如果新增 inventory CLI，必须额外运行并记录：

```bash
python -m reverse_agent.tool_capability_inventory build --state-dir project_state
python -m pytest tests/test_tool_capability_inventory.py -q
```

验收条件：

- pytest 必须通过。
- `command-plan` 不得出现 unknown kind。
- `tool_capability_inventory.json` 与 `structured_evidence_gap_report.json` 必须存在，且 decision_id/round_id 指向本轮。
- inventory 必须覆盖 Required Audit 中列出的 10 类能力。
- gap report 必须明确 current/stale/missing/unknown 的证据使用边界。
- 不得运行外部逆向工具或样本。
- `lint-report`、`doctor`、`report-summary`、`final-check`、`close-round` 均不得 FAIL。
- `codex_report_summary.files_changed` 必须包含本轮真实 source/test/project_state 改动。
- `generated_artifacts` 必须覆盖 gate artifacts、inventory/gap artifacts、report-summary artifact、round archive。
- `pytest_result.txt` 必须包含 fenced `pytest_result_summary` JSON，并覆盖 report 中所有 `tests_ran`。
- close-round 必须成功生成 round manifest。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要运行样本、solver、IDA/Ghidra/debugger/radare2/file/strings/objdump 才能完成本轮。
- 需要读取完整 `solve_reports/`。
- 需要修改 `.codex-skills/`。
- 无法判断现有工具接口是否存在。
- 无法保证 inventory/gap report 不包含 raw sample 或本地敏感路径。
- final-check 只能通过降低校验强度来通过。
- `close-round` 仍无法生成有效 round manifest。
