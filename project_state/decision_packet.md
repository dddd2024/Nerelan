```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_report_summary_autogen_v1",
  "round_id": "round_20260612_engineering_report_summary_autogen_v1",
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

本轮只做工程结构改进：把 `codex_execution_report.md` 顶部 `codex_report_summary` 的核心字段改为可由工具生成或校验，减少人工维护 `files_changed`、`tests_ran`、`generated_artifacts` 时产生的返工。

目标：新增一个小型 report-summary 自动生成/校验入口，让 Codex 在收尾阶段能基于 `decision_packet.md`、`command_plan.json`、`pytest_result.txt`、`round_delta_summary.json`、`final_gate_result.json` 和 round archive 自动合成 report summary 草案或校验当前 report summary。最终 gate 应能发现并阻止：report 手写遗漏 tests、遗漏 generated_artifacts、混入 inherited dirty files、或 status/acceptance 与 final-check 结果不一致。

本轮不是逆向解题，不推进训练队列业务，不运行样本，不运行 IDA/Ghidra/debugger/harness/solver，不生成 candidate、flag、password 或答案。

## 2. Current Evidence

- 上一轮 `decision_20260612_engineering_round_delta_scope_guard_v1` 已验收，`final_gate_result.json` 为 `PASSED`，blocking_reasons 和 warnings 为空。
- 上一轮已新增 `round_baseline.json` 与 `round_delta_summary.json`，并能区分 `new_dirty_files_since_baseline` 与 `inherited_dirty_files`。
- 当前仍有一个结构性返工源：`codex_execution_report.md` 的 `files_changed`、`tests_ran`、`generated_artifacts` 仍主要依赖 Codex 手写。即使 gate 能检查结果，错误仍经常到收尾时才暴露。
- 本轮应把人工填写的字段收敛为工具生成/校验的结果，而不是继续靠提示词要求 Codex 手动同步多份文件。
- `task_packet.json` 只能作为 advisory；当前执行权威是本 `decision_packet.md`。
- `current_state.json` 和 `artifact_index.json` 仍包含旧 sample solving / stale artifact 事实，本轮不得把这些 stale artifact 当作当前证据。
- `negative_results.json` 禁止旧盲搜、预算扩张、重复 runtime/breakpoint probe、完整 `solve_reports/` 提交等方向。本轮不得触碰这些方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active。

已有相关能力：

- 已有 `project_gate preflight`、`command-plan`、`final-check`、`close-round`。
- 已有 `project_state lint-report`、`doctor`、`archive_round`、`parse_pytest_result_header`、`read_codex_report_summary`、`validate_pytest_result_for_report`。
- 已有 `round_baseline.json` / `round_delta_summary.json` 可提供本轮真实改动范围。
- 本轮应复用这些能力，不重复实现已有 report parser、pytest parser、round archive 逻辑。

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
- 不用人工硬编码本轮文件列表绕过自动生成逻辑。
- 不把 `round_delta_summary.inherited_dirty_files` 放入 report 的 `files_changed`。

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
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260612_engineering_round_delta_scope_guard_v1/round_manifest.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

可有界读取：

- `project_state/rounds/round_20260612_engineering_round_delta_scope_guard_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_engineering_round_delta_scope_guard_v1/pytest_result.txt`

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须：

1. 说明当前 report summary 哪些字段仍是人工维护风险点。
2. 设计并实现一个小型自动生成/校验入口，名称可为以下之一，但必须保持工程内命令风格一致：
   - `python -m reverse_agent.project_state synth-report --state-dir project_state`
   - 或 `python -m reverse_agent.project_gate report-summary --state-dir project_state`
3. 自动生成/校验逻辑至少覆盖：
   - `report_id`
   - `round_id`
   - `based_on_decision_id`
   - `status`
   - `acceptance_recommendation`
   - `files_changed`
   - `tests_ran`
   - `generated_artifacts`
4. 字段来源必须明确：
   - `round_id` / `based_on_decision_id` 来自 decision_meta。
   - `tests_ran` 优先来自 `command_plan.json.commands[].command`，并与 `pytest_result_summary.tests_ran` 比对。
   - `files_changed` 优先来自 `round_delta_summary.new_dirty_files_since_baseline` 加本轮 round archive 路径；不得包含 inherited dirty files。
   - `generated_artifacts` 来自 gate artifacts、round baseline/delta artifacts、pytest_result/report、round archive。
   - `status` / `acceptance_recommendation` 必须由 final-check / close-round 结果映射，不能由 Codex 手写为成功。
5. 保持兼容：如果缺少 `round_delta_summary.json` 或 `command_plan.json`，不得静默成功；应产生 WARN/BLOCKED/FAILED，并说明缺失来源。
6. 更新 final-check 或 lint-report：检查 report summary 与自动合成 summary 的关键字段一致；若不一致，明确列出差异。
7. 更新测试，覆盖：
   - 自动 summary 能从 command_plan + pytest_result + round_delta 生成预期字段。
   - report summary 漏 tests_ran 时失败。
   - report summary 把 inherited dirty file 放入 files_changed 时失败。
   - report status 与 final-check 结果矛盾时失败。
   - 缺少 round_delta_summary 或 command_plan 时不能假通过。
8. 确认本轮没有运行样本、IDA/Ghidra/debugger/harness campaign、solver、candidate search 或 runtime probe。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

允许生成或更新：

- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260612_engineering_report_summary_autogen_v1/*`

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
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_engineering_report_summary_autogen_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

如果实现的是 `project_state synth-report` 或 `project_gate report-summary`，必须把该命令加入 tests_ran，并完整记录 stdout/stderr/exit code。该命令应在 `lint-report` / `final-check` 之前运行。

验收条件：

- pytest 必须通过。
- `command-plan` 不得出现 unknown kind。
- 自动 report summary 入口必须存在并被测试覆盖。
- `lint-report`、`doctor`、`final-check`、`close-round` 均不得 FAIL。
- report summary 与自动合成字段一致；不一致时 gate 必须失败。
- `round_baseline.json` 和 `round_delta_summary.json` 必须存在，且 decision_id/round_id 指向本轮。
- `codex_report_summary.files_changed` 不得包含 inherited dirty files。
- `generated_artifacts` 必须覆盖 gate artifacts、round_delta artifacts、自动 report summary 相关 artifacts、round archive。
- `pytest_result.txt` 必须包含 fenced `pytest_result_summary` JSON，并覆盖 report 中所有 `tests_ran`。
- close-round 必须成功生成 round manifest。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要运行样本、solver、IDA/Ghidra/debugger 才能完成本轮。
- 需要读取完整 `solve_reports/`。
- 需要修改 `.codex-skills/`。
- 无法从现有 command_plan / pytest_result / round_delta / final_gate 生成可靠 report summary。
- final-check 只能通过降低校验强度来通过。
- `close-round` 仍无法生成有效 round manifest。
