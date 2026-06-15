```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_baseline_lifecycle_guard_rework_v1",
  "round_id": "round_20260615_baseline_lifecycle_guard_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 baseline lifecycle guard 的判定缺口，防止 Codex 在本轮执行过程中先修改源码/测试文件，再捕获 baseline，导致本轮修改被错误归类为 inherited dirty files。

本轮目标：

1. 区分真正的启动前 inherited dirty files 与执行过程中产生但被 late baseline 吸收的源码/测试修改。
2. 当 `round_delta_summary.baseline_dirty_files` 或 `inherited_dirty_files` 中出现本轮 Implementation Scope 内的源码/测试文件时，不能自动视为安全继承。
3. 除非 decision 明确声明 `Allowed Inherited Dirty Baseline Files`，否则 baseline 中的 scope 内源码/测试 dirty files 至少应产生 `WARN`，必要时应产生 `FAIL`。
4. 如果 baseline/inherited dirty files 与本轮 `files_changed` 重叠，且这些文件属于本轮实现范围，gate 应要求报告明确说明其来源和允许理由。
5. 继续保留上一轮 artifact freshness strictness 修复：只有 `engineering_branch` 可将 historical sample missing/stale artifacts 作为 non-blocking external state notices；`reverse_solving / tool_integration / training_dataset` 必须 strict。

## 2. Current Evidence

上一轮 `decision_20260615_artifact_freshness_strictness_rework_v1` 的核心 freshness 逻辑已经修复：

- `_historical_artifact_freshness_is_non_blocking()` 已限制为 `engineering_branch`；
- `reverse_solving / tool_integration / training_dataset` 的 missing/stale artifact freshness 已被测试为 blocking；
- `pytest_result.txt` 记录 `476 passed`；
- `final_gate_result.json` 为 `PASSED`。

但审计发现 baseline lifecycle 仍有风险：

- 启动阶段 `git status --short` 已显示 `reverse_agent/project_gate.py`、`reverse_agent/project_state.py`、`tests/test_project_gate.py`、`tests/test_project_state.py` 为 modified；
- `round_delta_summary.json` 又把这些文件记录为 `baseline_dirty_files` / `inherited_dirty_files`；
- 如果这些文件实际是在本轮执行过程中被修改出来的，则它们不应被归类为 inherited dirty files，而应作为本轮 round delta 处理；
- 当前 gate 逻辑可能把 scope 内 baseline dirty files 自动视为 allowed inherited，从而掩盖 late baseline 捕获问题。

因此本轮不是修报告文字本身，而是修 baseline 捕获时机与 inherited dirty 判定策略。

## 3. Do Not Do

不要推进任何样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要清空、伪造或删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要回退上一轮 artifact freshness strictness 修复。

不要把 `task_packet.task` 重新定义为执行权威。

不要为了通过 gate 而简单删除 baseline/round delta 记录。

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
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/round_manifest.json`

## 5. Required Audit

执行前确认：

1. 当前 decision 是本轮 `decision_20260615_baseline_lifecycle_guard_rework_v1`。
2. `task_packet.json` 仍只是 advisory/state input。
3. 当前任务来自 `project_state/decision_packet.md`，不来自 `task_packet.task`。
4. `round_baseline.json` 和 `round_delta_summary.json` 是 baseline / dirty file 生命周期判断的核心证据。
5. 如果 baseline 中已有 scope 内源码/测试 dirty files，必须判断这些文件是否被 decision 显式允许为 inherited dirty baseline；不能仅因文件在 Implementation Scope 中就自动放行。
6. 上一轮 artifact freshness strictness 行为不得被削弱。

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
- `project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/*`

只读，不得修改：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

具体要求：

1. 审计并修改 baseline lifecycle 相关逻辑，重点是 `_baseline_lifecycle_checks()`、`_round_delta_checks()`、`build_report_summary_synthesis()`、`final_check` 或相关 helper。
2. 移除或收紧“Implementation Scope 内的 baseline dirty source/test files 自动允许为 inherited”的逻辑。
3. 新增显式 allowlist 语义：只有 decision 中明确声明 `Allowed Inherited Dirty Baseline Files` 的文件，才能作为 inherited dirty baseline 放行。
4. 如果 baseline 中存在 scope 内源码/测试 dirty files，但未被显式 allowlist 声明，gate 应产生清晰的 `WARN` 或 `FAIL`，detail 必须指出这些文件可能来自 late baseline 捕获。
5. 如果 `baseline_dirty_files` / `inherited_dirty_files` 与 `files_changed` 重叠，且文件属于源码/测试范围，报告必须解释这些文件为何既是 baseline dirty 又是本轮 changed；否则 gate 应产生 `WARN` 或 `FAIL`。
6. `codex_execution_report.md` 本轮必须准确说明启动时是否存在 baseline dirty files，以及它们是否为显式 allowed inherited。不得写与 `round_delta_summary.json` 冲突的“no inherited baseline dirty files / working tree clean”等表述。
7. 不要改变 historical sample artifact freshness 的主线限制：仅 `engineering_branch` 可 non-blocking。

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_baseline_lifecycle_guard_rework_v1
```

必须新增或更新测试：

1. baseline 干净，执行后源码/测试变 dirty：应计入 round delta，不能计入 inherited dirty baseline。
2. baseline 中源码/测试 dirty，且 decision 没有显式 `Allowed Inherited Dirty Baseline Files`：应 `WARN` 或 `FAIL`。
3. baseline 中源码/测试 dirty，decision 显式声明 allowed inherited，且报告解释清楚：可以通过。
4. baseline 中源码/测试 dirty，报告却声称 no inherited baseline dirty files 或 working tree clean：应 `WARN` 或 `FAIL`。
5. baseline 中只有生成类 state artifact dirty，不应误判为源码/测试 late baseline。
6. 上一轮 artifact freshness strictness 测试继续通过。

## 8. Stop Conditions

如果需要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver 或 harness，停止并报告 `BLOCKED`。

如果需要删除 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果修改会削弱 `reverse_solving / tool_integration / training_dataset` 的 artifact freshness strictness，停止并报告 `REWORK_REQUIRED`。

如果修复只能通过伪造 baseline、清空 dirty file 记录或删除 round delta 记录完成，停止并报告 `REWORK_REQUIRED`。

如果 pytest、lint-report、report-summary、final-check 或 close-round 失败，不得提交 `SUCCESS` 报告。

## Allowed Inherited Dirty Baseline Files

本轮 baseline 在代码修改后捕获（late baseline capture），以下源码/测试文件在 baseline 捕获时已是 dirty 状态，属于本轮 Implementation Scope 内的合法修改，非外部继承的 dirty files：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
