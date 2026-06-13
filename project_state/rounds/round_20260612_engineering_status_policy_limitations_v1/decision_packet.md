```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_status_policy_limitations_v1",
  "round_id": "round_20260612_engineering_status_policy_limitations_v1",
  "based_on_state_build_id": "state_20260612_154305_9877218db479",
  "based_on_state_digest": "9877218db479bcb3f914fe77bcf71da3f217beb5e780eccd84fb47fbaf997626",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮只做工程状态策略修复：把 `status_policy_valid`、`doctor WARN`、历史 missing artifacts、`ACCEPTED_WITH_LIMITATIONS` 的语义正式纳入 gate/report 体系。

目标不是继续修工具库存，也不是继续修 archive 路径。上一轮已经证明：

- `project_state build` 能成功执行。
- `report-summary` 已经 PASSED。
- round archive 已经创建。
- final-check 已经没有 blocking_reasons，只剩 `status_policy_valid` WARN。
- 当前卡点是 report 仍为 `PARTIAL/NEEDS_REVIEW`，而不是 `SUCCESS` 或可验收的 `ACCEPTED_WITH_LIMITATIONS`。

本轮应新增或完善一条明确规则：

> 如果所有当前轮必需产物、round archive、pytest、command-plan、report-summary 都通过，而 doctor 仅因历史 missing artifacts 或项目级历史 artifact 缺口给 WARN，则 final-check 可以进入 `ACCEPTED_WITH_LIMITATIONS` 路径；但如果缺的是当前轮必需 artifact，则必须继续 FAIL/BLOCK。

本轮不进入样本分析、不运行外部逆向工具、不扩展工具库存语义内容。

## 2. Current Evidence

- 上一轮 `decision_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1` 已把 closeout 技术链路从 BLOCK 推进到可审查限制状态。
- 上一轮完成了 `python -m reverse_agent.project_state build`，并生成新的 `state_build_id=state_20260612_154305_9877218db479` 与 digest `9877218db479bcb3f914fe77bcf71da3f217beb5e780eccd84fb47fbaf997626`。
- 上一轮 pytest 记录：`tests/test_tool_capability_inventory.py` 为 28 passed，`tests/test_project_gate.py tests/test_project_state.py` 为 269 passed。
- 上一轮 close-round 已创建 `project_state/rounds/round_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1/round_manifest.json`。
- 上一轮 post-close-round `report-summary` 为 PASSED，且 archive/live report 与 pytest_result 一致。
- 当前 `final_gate_result.json` 为 WARN，不是 FAILED；`blocking_reasons=[]`。
- 当前唯一实质限制点是 `status_policy_valid` 为 WARN：report 为 `PARTIAL`，doctor 为 `WARN`。
- 当前 report 顶部仍为 `status=PARTIAL`、`acceptance_recommendation=NEEDS_REVIEW`，这说明工程策略尚未把“当前轮完整、历史 artifact 缺口存在”的情况规范成可验收限制状态。
- `task_packet.json` 只能作为 advisory；当前执行权威是本 `decision_packet.md`。
- `artifact_index.json` 中仍有大量历史 sample-solving artifact missing/null，这些不得被当作 current evidence。
- `negative_results.json` 禁止旧 sample_solver blind search、扩 beam/budget、compare_semantics_agree=false candidate、提交完整 solve_reports 等方向。本轮不得触碰这些方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active。

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
- 不扩展 `tool_capability_inventory.json` / `structured_evidence_gap_report.json` 的语义内容。
- 不修改 solver、harness、IDA/Ghidra/debugger 执行逻辑。
- 不把当前轮必需 artifact 缺失降级为 WARN。
- 不通过粗暴忽略 doctor / artifact freshness 来制造假通过。
- 不把 stale/missing artifact 当作 current evidence。

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
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

可有界读取：

- `project_state/rounds/round_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1/round_manifest.json`
- `project_state/rounds/round_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1/pytest_result.txt`
- 与 `status_policy_valid`、`doctor_status`、artifact freshness 分类直接相关的测试片段。

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须：

1. 明确区分两类 artifact freshness：
   - **current-round required artifacts**：本轮 report、pytest、gate artifacts、round archive、report-summary、command-plan 等。缺失必须 FAIL。
   - **historical/project-level missing artifacts**：由旧 sample-solving 历史、旧 solve_reports、旧 artifact_index 留下的 missing 项。可 WARN，但必须列出并说明不作为 current evidence。
2. 新增或完善 `doctor` / `final-check` 的状态策略：
   - 当前轮必需 artifact 缺失：`FAILED`。
   - 当前轮必需 artifact 完整，但历史 artifact missing：`WARN` / `ACCEPTED_WITH_LIMITATIONS`。
   - 不允许把 stale/missing artifact 当 current evidence。
3. 修改 report summary 规则：
   - 如果只有历史 missing artifacts 导致限制，report 可使用：
     - `status=SUCCESS`
     - `acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`
     - 新增 `limitations` 字段列出历史 artifact 缺口。
   - 或使用项目已有等价字段，但必须让 final-check/report-summary/doctor 语义一致。
4. 更新 `status_policy_valid`：
   - 若 current-round 产物完整、pytest 通过、report-summary PASSED、archive/live 一致，则 `status_policy_valid` 不应仅因历史 missing artifacts 反复保持 WARN 后阻塞下一轮。
   - 若 report 仍为 `PARTIAL/NEEDS_REVIEW`，必须说明是否属于人工审查状态；不能与“可验收限制状态”混用。
5. 更新测试覆盖：
   - 当前轮 artifact 缺失时 final-check FAIL。
   - 历史 missing artifacts 存在但当前轮 artifacts 完整时 final-check 可 `PASSED` 或 `PASSED_WITH_LIMITATIONS`。
   - report `ACCEPTED_WITH_LIMITATIONS` 时 report-summary synthesis 能匹配。
   - `PARTIAL/NEEDS_REVIEW` 不得被当作完全验收。
   - stale/missing artifact 不得被当作 current evidence。
6. 确认本轮没有运行样本、IDA/Ghidra/debugger/radare2/file/strings/objdump、harness campaign、solver、candidate search 或 runtime probe。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/preflight_result.json`
- `project_state/rounds/round_20260612_engineering_status_policy_limitations_v1/*`

允许由 `project_state build` 派生更新：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`

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
- inventory/gap report semantic scope
- unrelated modules/tests

## 6.1 Allowed Inherited Dirty Baseline Files

以下文件在基线中已经是脏的（来自前几轮），本轮允许作为继承脏基线：

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`
- `reverse_agent/harness.py`

## 7. Tests

必须真实运行并完整记录 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
git diff --name-only
python -m reverse_agent.project_state build
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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_engineering_status_policy_limitations_v1
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

验收条件：

- pytest 必须通过。
- `project_state build` 必须成功。
- `command-plan` 不得出现 unknown kind。
- `command-plan --json` 必须记录完整 JSON commands array。
- `lint-report`、`doctor`、`doctor --json`、`report-summary`、`final-check`、`final-check --json`、`close-round` 均不得以 exit code 1 作为最终状态。
- `report_summary_synthesis.json` 必须 PASSED。
- round archive 必须存在，archive/live report 与 pytest_result 必须一致。
- `status_policy_valid` 必须明确区分 current-round missing 和 historical missing。
- 若仍是 historical missing artifacts，必须输出可审计 limitations，而不是反复 BLOCK。
- `codex_execution_report.md` 不得再使用 `PARTIAL/NEEDS_REVIEW` 表示已经可验收的结果。
- `pytest_result.txt` 不得包含 `(pending...)` 伪命令结果。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 无法区分 current-round required artifact 与 historical missing artifact。
- 需要运行样本、solver、IDA/Ghidra/debugger/radare2/file/strings/objdump 才能完成本轮。
- 需要读取完整 `solve_reports/`。
- 需要修改 `.codex-skills/`。
- final-check 只能通过忽略 artifact freshness 来通过。
- report 仍只能保持 `PARTIAL/NEEDS_REVIEW`，且无法解释是否为可验收限制状态。
