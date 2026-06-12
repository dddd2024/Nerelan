```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1",
  "round_id": "round_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1",
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

只返工上一轮 `tool_integration` closeout 的剩余阻塞，不扩展工具库存内容，不进入样本 triage，不新增求解能力。

本轮必须同时解决两个根因：

1. **project_state artifact freshness 阻塞**：当前 `status_policy_valid` 因 `3 missing, 48 stale artifacts` 失败。必须先通过 `python -m reverse_agent.project_state build` 重建当前状态，刷新 `current_state.json`、`artifact_index.json`、`model_gate.json`、`task_packet.json` 等 project_state 派生产物，使 `doctor` / `status_policy_valid` 不再因 stale/missing artifact 阻塞。
2. **close-round 时序阻塞**：必须修复或显式处理 `pre-archive` / `post-archive` 校验时序。`close-round` 创建 archive 之前，不应因 round archive 文件尚不存在而 BLOCK；`close-round` 创建 archive 之后，必须严格要求精确 archive 路径、round manifest 存在、archive/live report 和 pytest_result 一致。

最终目标：

- `codex_execution_report.md` 顶部 `codex_report_summary.status=SUCCESS`。
- `acceptance_recommendation=ACCEPTED`。
- `project_state/gates/report_summary_synthesis.json` 为 `PASSED`。
- `project_state/gates/final_gate_result.json` 为 `PASSED`。
- `project_state/rounds/round_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1/round_manifest.json` 真实存在。
- `pytest_result.txt` 不得再出现 `(pending...)` 伪记录。
- `doctor` / `status_policy_valid` 不得再因 `3 missing, 48 stale artifacts` 阻塞。

上一轮已经生成 `project_state/tool_capability_inventory.json` 与 `project_state/structured_evidence_gap_report.json`。本轮只允许重建 provenance / freshness / closeout 一致性；不得继续扩大 inventory/gap report 的语义内容。

## 2. Current Evidence

- 上一轮 `decision_20260612_rework_tool_inventory_closeout_consistency_v1` 仍未通过验收。
- 当前 `codex_execution_report.md` 仍为 `PARTIAL/CONDITIONAL`，违反上一轮验收条件。
- 当前 `project_state/gates/final_gate_result.json` 仍为 `FAILED`。
- 当前 blocking reason 已收敛到 `status_policy_valid`，其根因是 `doctor` 检测到 `3 missing, 48 stale artifacts`。
- 当前 `report_summary_synthesis.json` 至少为 WARN/未完全闭环，曾提示 `final_gate_result.json is missing or not for current round; status fields cannot be gate-derived yet`。
- 当前 round archive 仍未完全闭环，`round_manifest_present` 仍可能为 WARN，`archive_status` 仍可能为 `not_archived`。
- 当前 `pytest_result.txt` 曾用 `(pending...)` 代替真实命令输出并标记 `EXIT: 0`，不能作为验收依据。
- 之前已经修掉或接近修掉的点包括：`command-plan --json` 完整 stdout、`files_changed_covers_git_diff`、`baseline_lifecycle_guard`、`report_summary_fields_match_synthesis`。本轮不得回退这些检查。
- `task_packet.json` 仍只能作为 advisory；当前执行权威是本 `decision_packet.md`。
- `current_state.json` 和 `artifact_index.json` 含有旧 sample-solving / stale artifact 事实；本轮允许通过 `project_state build` 刷新状态，但不得把 stale artifact 当作 current evidence。
- `negative_results.json` 禁止旧 sample_solver blind search、扩 beam/budget、compare_semantics_agree=false candidate、提交完整 solve_reports 等方向。本轮不得触碰这些方向。

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
- 不继续扩展 `tool_capability_inventory.json` / `structured_evidence_gap_report.json` 的能力内容；只可重生成以对齐当前 decision/round/provenance/freshness。
- 不把 wildcard round archive 路径写进 `files_changed` 或 `generated_artifacts`。
- 不把 `(pending...)` 写入 `pytest_result.txt` 并标记成功。
- 不把 `PARTIAL/CONDITIONAL` 当作成功。
- 不通过降低 post-archive final-check / report-summary 校验强度来制造假通过。

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
- `project_state/tool_capability_inventory.json`
- `project_state/structured_evidence_gap_report.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `reverse_agent/tool_capability_inventory.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `tests/test_tool_capability_inventory.py`

可有界读取：

- 最新上一轮 commit diff 或 round artifact manifest，用于确认 live artifacts 与 report 不一致的原因。
- `project_state/rounds/round_20260612_rework_tool_inventory_closeout_consistency_v1/*`，仅用于确认上一轮 closeout 失败原因。

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须完成以下审计和修复：

1. 解释为什么上一轮 `status_policy_valid` 仍失败，以及 `3 missing, 48 stale artifacts` 为什么需要先运行 `python -m reverse_agent.project_state build`。
2. 在任何 closeout 判断前运行 `python -m reverse_agent.project_state build`，然后重新运行 `doctor` 和 `doctor --json`，确认 artifact freshness 不再作为 blocking reason。
3. 明确修复或验证 `close-round` 的时序：
   - pre-archive 阶段：允许 round archive 文件尚不存在；archive/live 一致性和 round manifest 缺失不能 BLOCK close-round。
   - post-archive 阶段：必须要求 round manifest 存在、archive/live report 和 pytest_result 一致、`files_changed` / `generated_artifacts` 使用精确 archive 文件路径。
4. 若需要修改代码，只能在 `reverse_agent/project_gate.py` / `reverse_agent/project_state.py` 中小步修复 pre-archive/post-archive 判断，不得削弱 post-archive 严格校验。
5. 删除或替换所有 `(pending...)` 命令记录，所有命令必须真实运行并记录 stdout/stderr/exit code。
6. 将 report 状态改为 `SUCCESS/ACCEPTED`；如果不能做到，按 Stop Conditions 报告 `BLOCKED`，不得提交 `PARTIAL/CONDITIONAL` 作为成功。
7. `report_summary_synthesis.json` 必须为 `PASSED`，不得只停在 WARN。
8. `final_gate_result.json` 必须为 `PASSED`，且 `status_policy_valid` 必须 PASS。
9. `round_manifest.json` 必须真实存在，并被 `generated_artifacts` 精确列出。
10. `tool_capability_inventory.json` 与 `structured_evidence_gap_report.json` 必须仍存在，且 provenance 对齐本轮 rework 或在 report 中明确标记为上一轮产物经本轮验证。
11. 确认本轮没有运行样本、IDA/Ghidra/debugger/radare2/file/strings/objdump、harness campaign、solver、candidate search 或 runtime probe。

## 6. Implementation Scope

允许修改：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/task_packet.json`，仅限 `project_state build` 派生更新
- `project_state/current_state.json`，仅限 `project_state build` 派生更新
- `project_state/artifact_index.json`，仅限 `project_state build` 派生更新
- `project_state/model_gate.json`，仅限 `project_state build` 派生更新
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/preflight_result.json`
- `project_state/tool_capability_inventory.json` only to update decision_id/round_id/provenance if required by closeout consistency
- `project_state/structured_evidence_gap_report.json` only to update decision_id/round_id/provenance if required by closeout consistency
- `project_state/rounds/round_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1/*`
- `reverse_agent/project_gate.py` only if needed to fix pre-archive/post-archive close-round/final-check/report-summary timing without weakening post-archive checks
- `reverse_agent/project_state.py` only if needed to fix state freshness rebuild / doctor / status_policy_valid integration without weakening freshness policy
- `tests/test_project_gate.py` only if needed for closeout timing regression coverage
- `tests/test_project_state.py` only if needed for freshness/status_policy regression coverage
- `tests/test_tool_capability_inventory.py` only if needed to keep inventory CLI tests green after provenance-only updates

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
- inventory/gap report semantic scope beyond provenance/closeout consistency
- unrelated source modules
- unrelated tests

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
python -m reverse_agent.tool_capability_inventory build --state-dir project_state
python -m pytest tests/test_tool_capability_inventory.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_rework2_tool_inventory_state_freshness_and_close_round_v1
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

如修改了 close-round 时序逻辑，必须增加或更新测试覆盖：

- pre-archive final-check 不因 round archive 文件缺失而 BLOCK close-round。
- post-archive final-check 必须要求 round manifest 存在、archive/live 一致、精确 archive paths。
- `status_policy_valid` 不得因已经通过 `project_state build` 修复的 stale/missing artifacts 继续 FAIL。

验收条件：

- `python -m pytest tests/test_tool_capability_inventory.py -q` 必须通过。
- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q` 必须通过。
- `python -m reverse_agent.project_state build` 必须成功。
- `doctor` / `doctor --json` 不得因 `3 missing, 48 stale artifacts` 产生 blocking failure。
- `status_policy_valid` 必须 PASS。
- `command-plan` 不得出现 unknown kind。
- `command-plan --json` 的 stdout 必须记录完整 JSON commands array。
- `lint-report`、`doctor`、`doctor --json`、`report-summary`、`final-check`、`final-check --json`、`close-round` 均不得以 exit code 1 作为最终状态。
- `report_summary_synthesis.json` 必须为 `PASSED`。
- `final_gate_result.json` 必须为 `PASSED`。
- `codex_execution_report.md` 的 `codex_report_summary.status` 必须为 `SUCCESS`，`acceptance_recommendation` 必须为 `ACCEPTED`。
- `files_changed` 和 `generated_artifacts` 必须使用精确路径，不能使用 `round_id/*` wildcard。
- round archive 必须存在，且 archive/live report、pytest_result 一致。
- `tool_capability_inventory.json` 与 `structured_evidence_gap_report.json` 必须存在，且 provenance 对齐本轮 rework 或被 report 明确标记为上一轮产物经本轮验证。
- `pytest_result.txt` 必须包含 fenced `pytest_result_summary` JSON，并覆盖 report 中所有 `tests_ran`。
- `pytest_result.txt` 不得包含 `(pending...)` 伪命令结果。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- `python -m reverse_agent.project_state build` 无法成功。
- 运行 `project_state build` 后 `doctor` 仍因 artifact freshness 报 `3 missing, 48 stale artifacts` 或同类 blocking freshness failure。
- 无法让 `status_policy_valid` PASS。
- 无法让 `report_summary_synthesis.json` 和 `final_gate_result.json` 同时 PASSED。
- 无法解释或清理 `PARTIAL/CONDITIONAL` report 状态。
- 无法消除 wildcard archive 路径。
- 无法真实创建 round manifest。
- 无法处理 close-round pre-archive/post-archive 时序依赖。
- 需要运行样本、solver、IDA/Ghidra/debugger/radare2/file/strings/objdump 才能完成本轮。
- 需要读取完整 `solve_reports/`。
- 需要修改 `.codex-skills/`。
- final-check 只能通过降低 post-archive 校验强度来通过。
