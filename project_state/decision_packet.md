```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_baseline_lifecycle_guard_v1",
  "round_id": "round_20260612_engineering_baseline_lifecycle_guard_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
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

本轮只做工程结构改进：修复上一轮审计中发现的 baseline 生命周期缺口。

目标：让 `round_baseline.json` 真正代表“本轮开工前状态”，并让 gate 能识别 baseline 采集过晚的情况。若 baseline 中已经包含本轮允许修改的源码/测试文件，而 decision 没有显式声明这些文件是进入本轮前允许继承的 dirty baseline，则 final-check 必须 FAIL，不能把这些文件静默归类为 `inherited_dirty_files` 后仍然 `SUCCESS + ACCEPTED`。

本轮不是逆向解题，不推进训练队列业务，不运行样本，不运行 IDA/Ghidra/debugger/harness/solver，不生成 candidate、flag、password 或答案。

## 2. Current Evidence

- 上一轮 `decision_20260612_engineering_report_summary_autogen_v1` 功能侧已完成，新增了 `project_gate report-summary`，并生成 `project_state/gates/report_summary_synthesis.json`。
- 上一轮 final-check 当前为 `PASSED`，report-summary synthesis 也为 `PASSED`。
- 上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`，限制点是 baseline 采集过晚：`round_baseline.json` 已经包含 `reverse_agent/project_gate.py` 和 `tests/test_project_gate.py`，而这两个文件正是本轮实际修改的源码/测试文件。
- 这种情况会让 `round_delta_summary.json` 把真实本轮 source/test 修改错误归为 `inherited_dirty_files`，从而让 report 的 `files_changed` 不列出实际 source/test diff，仍然通过 final-check。
- 本轮应修复这个生命周期缺口，而不是继续扩展 report-summary 功能。
- `task_packet.json` 只能作为 advisory；当前执行权威是本 `decision_packet.md`。
- `current_state.json` 和 `artifact_index.json` 仍包含旧 sample solving / stale artifact 事实，本轮不得把这些 stale artifact 当作当前证据。
- `negative_results.json` 禁止旧盲搜、预算扩张、重复 runtime/breakpoint probe、完整 `solve_reports/` 提交等方向。本轮不得触碰这些方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active。

已有相关能力：

- 已有 `project_gate preflight`、`command-plan`、`report-summary`、`final-check`、`close-round`。
- 已有 `round_baseline.json` / `round_delta_summary.json`。
- 已有 `report_summary_synthesis.json`，能校验 `codex_report_summary` 与自动合成字段一致。
- 本轮应复用这些能力，不重复实现已有 parser、archive、pytest_result、report-summary 合成逻辑。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、winpty、harness campaign、solver 或 candidate search。
- 不生成 candidate、flag、password 或答案。
- 不读取完整 `solve_reports/`。
- 不读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不读取或上传 raw sample、sample binary、IDA database、debug trace、大体积历史 artifact。
- 不修改 `.codex-skills/`。
- 不修改训练队列业务分类规则。
- 不修改 solver、harness、IDA/Ghidra/debugger 接口。
- 不通过放宽 final-check 来制造假通过。
- 不把 baseline 中的 source/test dirty files 静默当作 inherited dirty files 后通过验收。
- 不用人工硬编码本轮文件列表绕过 baseline lifecycle 校验。

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
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260612_engineering_report_summary_autogen_v1/round_manifest.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

可有界读取：

- `project_state/rounds/round_20260612_engineering_report_summary_autogen_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_engineering_report_summary_autogen_v1/pytest_result.txt`

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须：

1. 启动前先记录并报告：`pwd`、`Test-Path F:\reverse-agent`、`git rev-parse --show-toplevel`、`git status --short`、`git diff --name-only`。
2. 在任何源码/测试修改前运行 `preflight`，并确认本轮 baseline 已生成且属于当前 decision/round。
3. 解释上一轮为什么 baseline 会包含 `reverse_agent/project_gate.py` 和 `tests/test_project_gate.py`，以及为什么这是生命周期风险。
4. 增强 baseline lifecycle 校验：
   - 若 `round_baseline.json.baseline_dirty_files` 非空，必须检查这些 dirty files 是否被当前 decision 明确允许为 inherited baseline。
   - 若 baseline dirty file 命中本轮 Implementation Scope 的允许源码/测试文件，且没有明确 inherited-baseline allowlist，则 final-check 必须 FAIL。
   - 允许新增一个明确小节，例如 `Allowed Inherited Dirty Baseline Files`；缺失该小节时默认不允许 source/test inherited dirty。
   - generated gate artifacts、report、pytest_result、round archive 可以在 baseline 后生成，不应误判为 late baseline。
5. 更新 report-summary / round-delta 相关校验，使它不能通过“把 source/test 真实改动归入 inherited dirty files”来漏报 `files_changed`。
6. 保持兼容旧轮：旧 archive 或没有 baseline 的历史 round 可以 WARN，但当前 active round 若主张 `SUCCESS + ACCEPTED`，必须满足 baseline lifecycle guard。
7. 更新测试，覆盖：
   - clean baseline + source/test 本轮修改能通过。
   - baseline 中已有 source/test dirty 且无 inherited allowlist 时 final-check FAIL。
   - baseline 中已有 source/test dirty 且 decision 明确 allowlist 时 final-check 可以通过，但 report 必须在正文说明。
   - baseline 中只有 project_state/gates 或 round archive 生成物时不误判。
   - report-summary synthesis 不能掩盖 late baseline。
8. 确认本轮没有运行样本、IDA/Ghidra/debugger/harness campaign、solver、candidate search 或 runtime probe。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report/lint/status integration requires a small compatibility change
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state integration is touched

允许生成或更新：

- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260612_engineering_baseline_lifecycle_guard_v1/*`

不允许修改：

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `training_materials/local_reverse/`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_training_next_queue.json`
- `training_materials/local_reverse/queue.json`
- raw local samples
- sample binaries
- solver/harness/IDA/Ghidra/debugger 功能逻辑
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
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_engineering_baseline_lifecycle_guard_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

验收条件：

- pytest 必须通过。
- `command-plan` 不得出现 unknown kind。
- `report-summary` 必须运行并生成 `project_state/gates/report_summary_synthesis.json`。
- `lint-report`、`doctor`、`final-check`、`close-round` 均不得 FAIL。
- `round_baseline.json` 和 `round_delta_summary.json` 必须存在，且 decision_id/round_id 指向本轮。
- 若 `round_baseline.json.baseline_dirty_files` 包含本轮允许源码/测试文件，必须有 explicit inherited-baseline allowlist；否则 final-check 必须 FAIL。
- `codex_report_summary.files_changed` 不得遗漏本轮真实 source/test 改动，也不得把未授权 inherited dirty files 当作可忽略项。
- `generated_artifacts` 必须覆盖 gate artifacts、round_delta artifacts、report-summary artifact、round archive。
- `pytest_result.txt` 必须包含 fenced `pytest_result_summary` JSON，并覆盖 report 中所有 `tests_ran`。
- close-round 必须成功生成 round manifest。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要运行样本、solver、IDA/Ghidra/debugger 才能完成本轮。
- 需要读取完整 `solve_reports/`。
- 需要修改 `.codex-skills/`。
- 无法可靠区分 clean pre-edit baseline 与 late baseline。
- final-check 只能通过降低校验强度来通过。
- `close-round` 仍无法生成有效 round manifest。
