```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_round_baseline_capture_order_guard_v1",
  "round_id": "round_20260615_round_baseline_capture_order_guard_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 round baseline 捕获顺序问题，防止源码/测试文件已经被本轮修改后，才生成 `project_state/gates/round_baseline.json`，再通过 `Allowed Inherited Dirty Baseline Files` 把这些本轮修改解释为 inherited dirty。

本轮目标：

1. 明确区分三种状态：
   - 执行前真实 inherited dirty；
   - 本轮执行后新增 dirty；
   - late baseline capture 导致本轮修改被错误吸收到 baseline。
2. `preflight` / `run-round` / `final-check` 应能发现：当前 decision 的 source/test 文件在 baseline 中 dirty，但 baseline 不是在实现前稳定捕获的情况。
3. `Allowed Inherited Dirty Baseline Files` 只能用于真实执行前 inherited dirty，不应作为 late baseline capture 的常规豁免。
4. 如果 baseline 中包含当前 Implementation Scope 内 source/test dirty files，且 close snapshot / round delta 表明这些文件也是本轮 `files_changed`，gate 至少应 `WARN`；如没有明确的“启动前已存在”证据，应 `FAIL`。
5. 保留已修复行为：
   - `_report_explains_inherited_baseline_files()` 必须继续使用 `_NEGATION_PHRASES`；
   - Implementation Scope 不能自动成为 inherited dirty allowlist；
   - 只有 `engineering_branch` 可把 historical sample missing/stale artifacts 作为 non-blocking external state notices。

## 2. Current Evidence

当前 `decision_20260615_baseline_report_negation_guard_rework_v2` 已完成：

- `codex_execution_report.md` 对应 v2，`status=SUCCESS`；
- `pytest_result.txt` 记录 `493 passed in 60.10s`；
- `close-round` 已执行并归档；
- `final_gate_result.json` 为 `PASSED`；
- negation guard 已实际使用 `_NEGATION_PHRASES`。

但仍有一个流程限制：

- `final_gate_result.json` 记录 inherited dirty files 包含 `reverse_agent/project_gate.py` 和 `tests/test_project_gate.py`；
- `files_changed_excludes_inherited_dirty_files` 为 `WARN`，原因是 files_changed 仍包含 inherited source/test baseline dirty files，可能是 late baseline capture。

因此下一轮应从“允许解释 late baseline”转向“防止 late baseline 发生”。

## 3. Do Not Do

不要推进任何样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要清空、伪造或删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要回退 artifact freshness strictness 修复。

不要回退 `_NEGATION_PHRASES` / `_report_explains_inherited_baseline_files()` 的否定语义检查。

不要把 Implementation Scope 重新当成 inherited dirty allowlist。

不要把 late baseline capture 简单写进 allowlist 后继续 PASS。

## 4. Files To Inspect

必须读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

重点检查：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260615_baseline_report_negation_guard_rework_v2/round_manifest.json`

## 5. Required Audit

执行前确认：

1. 当前 decision 是 `decision_20260615_round_baseline_capture_order_guard_v1`。
2. `task_packet.json` 仍只是 advisory/state input。
3. 当前任务来自 `project_state/decision_packet.md`，不来自 `task_packet.task`。
4. `reverse-agent-iteration@v2` 必须来自 active registry。
5. 历史 sample artifacts 的 missing 状态仍只能作为 engineering_branch 的 external_state_notices，不得当作本轮阻塞。
6. baseline capture order 的事实来源应包括：
   - `round_baseline.json`
   - `round_delta_summary.json`
   - `round_close_snapshot.json`
   - `pytest_result.txt` 中启动阶段 `git status --short`
   - `codex_execution_report.md` 中 files_changed

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

必要时允许修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

允许生成：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/*`

只读，不得修改：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

具体要求：

1. 增加或收紧 baseline capture order 检查，例如：
   - `_baseline_capture_order_checks(...)`
   - 或整合进 `_baseline_lifecycle_checks()` / `_round_delta_checks()`。
2. 检查 `baseline_dirty_files ∩ files_changed ∩ source_test_scope`。
3. 如果这些文件存在，且同时属于当前 Implementation Scope，应默认视为 suspicious late baseline capture。
4. 只有存在明确 evidence 表明这些文件在 Codex 实现开始前已经 dirty，才允许降级为 WARN 或 PASS。
5. 不要仅凭 `Allowed Inherited Dirty Baseline Files` 直接 PASS。allowlist 只能说明“允许继承”，不能证明“不是 late baseline”。
6. 在 `final_gate_result.json` 中输出清晰字段：
   - `suspected_late_baseline_files`
   - `allowed_inherited_dirty_files`
   - `baseline_dirty_source_test_files`
   - `files_changed_overlap`
   - `capture_order_status`
7. 如果发现 suspected late baseline capture 且无启动前证据，应：
   - `final-check`: `FAIL` 或至少 `WARN`；
   - `report-summary`: 不得把 `SUCCESS/ACCEPTED` 合成为完全无问题；
   - `close-round`: 不得用 archive 动作掩盖该问题。
8. 继续保留现有 negation guard 测试和 artifact freshness strictness 测试。

## 7. Tests

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
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_round_baseline_capture_order_guard_v1
```

必须新增或更新测试：

1. baseline clean，source/test 修改出现在 `new_dirty_files_since_baseline`：PASS。
2. baseline 中 source/test dirty，但这些文件不在 `files_changed`：允许作为真实 inherited dirty，按 allowlist 规则处理。
3. baseline 中 source/test dirty，且同一文件也在 `files_changed`：判定为 suspected late baseline capture，至少 WARN。
4. 上述情况即使 decision 有 `Allowed Inherited Dirty Baseline Files`，也不能直接 PASS。
5. 无启动前 evidence + suspected late baseline capture：FAIL 或 WARN，测试必须固定预期。
6. 有启动前 evidence 明确证明这些文件本来就是 inherited dirty：可以 PASS 或 WARN，但必须在 detail 中说明证据来源。
7. `_report_explains_inherited_baseline_files()` 现有 11 个测试继续通过。
8. `reverse_solving / tool_integration / training_dataset` artifact freshness strictness 测试继续通过。

## 8. Stop Conditions

如果需要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver 或 harness，停止并报告 `BLOCKED`。

如果需要删除 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果修改会削弱 `reverse_solving / tool_integration / training_dataset` 的 artifact freshness strictness，停止并报告 `REWORK_REQUIRED`。

如果修改会回退 `_NEGATION_PHRASES` 或 allowlist section 检查，停止并报告 `REWORK_REQUIRED`。

如果修复只能靠继续扩大 `Allowed Inherited Dirty Baseline Files` 完成，停止并报告 `REWORK_REQUIRED`。

如果 pytest、lint-report、report-summary、final-check 或 close-round 失败，不得提交 `SUCCESS` 报告。
