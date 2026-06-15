```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_baseline_report_negation_guard_rework_v2",
  "round_id": "round_20260615_baseline_report_negation_guard_rework_v2",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 baseline report negation guard 的残留漏洞。

上一轮新增了 `_NEGATION_PHRASES`，但 `_report_explains_inherited_baseline_files()` 没有实际使用该 tuple。当前 helper 只检查 `Allowed Inherited Dirty Baseline Files` section 是否含列表项，因此如果 report 同时包含 allowlist section 和否定句，仍可能误判为解释有效。

本轮目标：

1. `_report_explains_inherited_baseline_files()` 必须实际使用 `_NEGATION_PHRASES`。
2. 如果 report 任意位置出现明确否定性 dirty/baseline/inherited 描述，应返回 `False`，除非该否定句位于测试说明/decision 引用等明确非报告结论区域；不要做复杂 NLP，保守处理即可。
3. 至少拒绝：
   - `no inherited baseline dirty files`
   - `no inherited dirty files`
   - `no baseline dirty files`
   - `working tree was clean`
   - `working tree clean`
   - `no dirty files at round start`
4. 覆盖“有 allowlist section + 有列表项 + 其他位置出现否定句”的冲突场景。
5. 保留显式 allowlist 机制：Implementation Scope 内文件不能自动变成 inherited dirty allowlist。
6. 保留 artifact freshness strictness：只有 `engineering_branch` 可把 historical sample missing/stale artifacts 作为 non-blocking external state notices。

## 2. Current Evidence

当前已完成：

- `decision_20260615_baseline_report_negation_guard_rework_v1` 已执行；
- `pytest` 为 `488 passed`；
- `final-check` 和 `close-round` 已完成；
- `_NEGATION_PHRASES` 已定义；
- `_report_explains_inherited_baseline_files()` 已替换旧的 keyword-only 判断。

但仍有缺口：

- `_NEGATION_PHRASES` 没有被 helper 使用；
- helper 只检查 allowlist section 是否有列表项；
- 测试没有覆盖所有 decision 指定的否定短语；
- 测试没有覆盖“section 有列表项但 report 其他位置否认 inherited dirty”的冲突文本。

## 3. Do Not Do

不要推进任何样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要清空、伪造或删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要回退 artifact freshness strictness 修复。

不要把 Implementation Scope 重新当成 inherited dirty allowlist。

不要用“section 有列表项”绕过明确否定句。

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
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260615_baseline_report_negation_guard_rework_v1/round_manifest.json`

## 5. Required Audit

执行前确认：

1. 当前 decision 是 `decision_20260615_baseline_report_negation_guard_rework_v2`。
2. `task_packet.json` 仍只是 advisory/state input。
3. `Allowed Inherited Dirty Baseline Files` 是唯一 inherited dirty allowlist 来源。
4. `_NEGATION_PHRASES` 必须参与实际判断。
5. 报告中的否定性 baseline/inherited/dirty 语句不能被 section list item 覆盖掉。
6. 上一轮 artifact freshness strictness 行为不得削弱。

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

允许生成：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_baseline_report_negation_guard_rework_v2/*`

只读，不得修改：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

具体要求：

1. 修改 `_report_explains_inherited_baseline_files(report_text: str) -> bool`。
2. helper 必须实际检查 `_NEGATION_PHRASES`。
3. 如果 report 文本中出现 `_NEGATION_PHRASES` 中任一短语，应返回 `False`，至少在当前简单实现中不要允许 section list item 覆盖否定句。
4. 保留 positive case：存在 `Allowed Inherited Dirty Baseline Files` section 且包含列表项，且全文没有否定短语时，返回 `True`。
5. 增加测试：
   - allowlist section + list item + 正向解释 → `True`；
   - `no inherited baseline dirty files` → `False`；
   - `no inherited dirty files` → `False`；
   - `no baseline dirty files` → `False`；
   - `working tree was clean` → `False`；
   - `working tree clean` → `False`；
   - `no dirty files at round start` → `False`；
   - allowlist section + list item + `No inherited baseline dirty files` → `False`；
   - allowlist section + list item + `working tree was clean` → `False`；
   - `_baseline_lifecycle_checks()` 在 allowlist 存在但 report 否认 inherited dirty 时产生 `FAIL`。
6. 不要扩大 scope 到其他 gate 重构。

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_baseline_report_negation_guard_rework_v2
```

## 8. Stop Conditions

如果需要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver 或 harness，停止并报告 `BLOCKED`。

如果需要删除 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果修改会削弱 `reverse_solving / tool_integration / training_dataset` 的 artifact freshness strictness，停止并报告 `REWORK_REQUIRED`。

如果修改会让 Implementation Scope 文件重新自动成为 inherited dirty allowlist，停止并报告 `REWORK_REQUIRED`。

如果 pytest、lint-report、report-summary、final-check 或 close-round 失败，不得提交 `SUCCESS` 报告。
