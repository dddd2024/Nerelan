```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_baseline_report_negation_guard_rework_v1",
  "round_id": "round_20260615_baseline_report_negation_guard_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 baseline inherited dirty report explanation 的否定语义漏检。

当前 gate 只检查报告文本是否同时包含 `baseline` 和 `inherited`，这会把 `No inherited baseline dirty files` 错误识别为“已解释 inherited baseline files”。

本轮目标：

1. 报告中出现 `no inherited baseline dirty files`、`no inherited dirty files`、`working tree was clean`、`no baseline dirty files` 等否定性描述时，不能视为 allowlist explanation。
2. 如果 `baseline_dirty_files` / `inherited_dirty_files` 中存在显式 allowed source/test files，而报告使用否定描述，应产生 `WARN` 或 `FAIL`。
3. 保留上一轮已完成的显式 allowlist 机制：Implementation Scope 内文件不能自动变成 inherited dirty allowlist。
4. 保留 artifact freshness strictness：只有 `engineering_branch` 可把 historical sample missing/stale artifacts 作为 non-blocking external state notices。

## 2. Current Evidence

上一轮已完成：

- `_allowed_inherited_files()` 只读取 `Allowed Inherited Dirty Baseline Files`；
- `_baseline_lifecycle_checks()` 不再自动允许 Implementation Scope 内 baseline dirty source/test files；
- `files_changed_excludes_inherited_dirty_files` 会对 inherited source/test dirty files 产生 WARN；
- `pytest` 为 `482 passed`；
- `final_gate_result.json` 为 `PASSED`。

但当前仍有漏洞：

- `baseline_inherited_allowlist_explained` 使用 `baseline in report_lower and inherited in report_lower` 判断解释是否存在；
- 这会把否定句 `No inherited baseline dirty files` 误判为解释；
- 测试没有覆盖该否定短语。

## 3. Do Not Do

不要推进任何样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要清空、伪造或删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要回退 artifact freshness strictness 修复。

不要把 Implementation Scope 重新当成 inherited dirty allowlist。

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

## 5. Required Audit

执行前确认：

1. 当前 decision 是本轮 `decision_20260615_baseline_report_negation_guard_rework_v1`。
2. `task_packet.json` 仍只是 advisory/state input。
3. `Allowed Inherited Dirty Baseline Files` 是唯一 inherited dirty allowlist 来源。
4. 报告中的否定性 baseline/inherited 语句不能被当作解释。
5. 上一轮 artifact freshness strictness 行为不得削弱。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

允许生成：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_baseline_report_negation_guard_rework_v1/*`

只读，不得修改：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

具体要求：

1. 新增 helper，例如 `_report_explains_inherited_baseline_files(report_text: str) -> bool`。
2. 该 helper 至少要拒绝这些否定性短语：
   - `no inherited baseline dirty files`
   - `no inherited dirty files`
   - `no baseline dirty files`
   - `working tree was clean`
   - `working tree clean`
   - `no dirty files at round start`
3. 用该 helper 替换当前的：
   - `"baseline" in report_lower and "inherited" in report_lower`
4. 增加测试：
   - allowlist 存在 + 报告明确解释 inherited baseline dirty files → PASS；
   - allowlist 存在 + 报告写 `No inherited baseline dirty files` → FAIL；
   - allowlist 存在 + 报告写 `working tree was clean` → FAIL；
   - allowlist 存在 + 报告不提 baseline/inherited → FAIL；
   - 无 allowlist + baseline source/test dirty → 仍 FAIL；
   - Implementation Scope 内文件不自动 allowed → 继续通过现有测试。
5. 不要扩大 scope 到其他 gate 重构。

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_baseline_report_negation_guard_rework_v1
```

## 8. Stop Conditions

如果需要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver 或 harness，停止并报告 `BLOCKED`。

如果需要删除 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果修改会削弱 `reverse_solving / tool_integration / training_dataset` 的 artifact freshness strictness，停止并报告 `REWORK_REQUIRED`。

如果修改会让 Implementation Scope 文件重新自动成为 inherited dirty allowlist，停止并报告 `REWORK_REQUIRED`。

如果 pytest、lint-report、report-summary、final-check 或 close-round 失败，不得提交 `SUCCESS` 报告。

## Allowed Inherited Dirty Baseline Files

本轮 baseline 在代码修改后捕获（late baseline capture），以下源码/测试文件在 baseline 捕获时已是 dirty 状态，属于本轮 Implementation Scope 内的合法修改，非外部继承的 dirty files：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
