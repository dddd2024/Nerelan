```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_round_delta_scope_guard_v1",
  "round_id": "round_20260612_engineering_round_delta_scope_guard_v1",
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

本轮只做工程结构改进：降低后续返工率，重点解决 `files_changed` / baseline dirty files / round archive 之间的责任边界不清问题。

目标：新增一个轻量的 round delta scope guard，使 Codex 在每轮开始时能记录 baseline dirty files，在收尾时能区分“本轮新增/修改文件”和“进入本轮前已经脏的历史残留文件”。最终 report 不得再把历史 baseline dirty files 混进 `files_changed` 当作本轮改动。

本轮不是逆向解题，不推进训练队列业务，不运行样本，不运行 IDA/Ghidra/debugger/harness/solver，不生成 candidate、flag、password 或答案。

## 2. Current Evidence

- 上一轮 `decision_20260612_rework4_final_gate_closeout_contract_v1` 已验收，`final-check`、`doctor`、`lint-report`、`close-round` 均通过。
- 上一轮解决了 command-plan unknown kind、pytest_result command block 匹配、round archive 缺失等 closeout 结构问题。
- 仍存在一个结构性残留：report 的 `files_changed` 会混入进入本轮前已经脏的 baseline 文件，例如 `harness.py`、`task_packet.json`、`artifact_index.json`、`model_gate.json` 等。上一轮虽然 final-check 通过，但这是因为 gate 只检查 `files_changed` 是否覆盖当前 git dirty files，没有区分“本轮改动”和“历史残留”。
- 这种混合会导致审计时难以判断 Codex 是否越界修改，从而增加返工率。
- `task_packet.json` 仍只能作为 advisory；当前执行权威是本 `decision_packet.md`。
- `negative_results.json` 禁止旧盲搜、预算扩张、重复 runtime/breakpoint probe、完整 `solve_reports/` 提交等方向。本轮不得触碰这些方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active；本轮继续使用这两个 skill profile。

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
- 不把 baseline dirty files 继续混入 `codex_report_summary.files_changed` 当作本轮改动。

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
- `project_state/rounds/round_20260612_rework4_final_gate_closeout_contract_v1/round_manifest.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

可有界读取：

- `project_state/gates/preflight_result.json`
- `project_state/rounds/round_20260612_rework4_final_gate_closeout_contract_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_rework4_final_gate_closeout_contract_v1/pytest_result.txt`

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须：

1. 记录启动 baseline：`pwd`、`Test-Path F:\reverse-agent`、`git rev-parse --show-toplevel`、`git status --short`、`git diff --name-only`。
2. 说明当前 git dirty files 中哪些是进入本轮前已经存在的 baseline dirty files。
3. 新增或扩展一个 round baseline / round delta 机制，能在 project_state/gates 下记录：
   - `decision_id`
   - `round_id`
   - `head_commit`
   - `baseline_git_status_short`
   - `baseline_git_diff_name_only`
   - `baseline_dirty_files`
   - `generated_at`
4. 新增或扩展一个收尾 diff summary，能记录：
   - `final_git_status_short`
   - `final_git_diff_name_only`
   - `final_dirty_files`
   - `new_dirty_files_since_baseline`
   - `inherited_dirty_files`
   - `baseline_dirty_files_resolved`
5. 更新 final-check 或 lint-report：
   - 若存在 baseline summary，`codex_report_summary.files_changed` 应优先覆盖 `new_dirty_files_since_baseline` 与本轮 round archive，而不是无脑覆盖所有 final dirty files。
   - `inherited_dirty_files` 必须单独记录，不能算作本轮 `files_changed`。
   - 如果 report 把 inherited dirty files 写进 `files_changed`，必须 FAIL 或 WARN，并要求说明/回退。
6. 保持兼容旧字段：没有 baseline summary 的旧轮次不能被直接判死；可以回退到现有检查，但必须给 warning。
7. 更新测试，覆盖：
   - 无 baseline summary 时保持旧行为并产生兼容 warning。
   - 有 baseline summary 时，report.files_changed 不得混入 inherited dirty files。
   - 本轮新增文件和 round archive 文件必须被 report.files_changed / generated_artifacts 覆盖。
   - final-check 能检测 baseline/current diff 分类。
8. 确认本轮没有修改训练队列业务逻辑、solver、harness、IDA/Ghidra/debugger 接口。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report/lint/status integration requires a small compatibility change
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state lint/report integration is touched

允许生成或更新：

- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260612_engineering_round_delta_scope_guard_v1/*`

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_engineering_round_delta_scope_guard_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

验收条件：

- pytest 必须通过。
- `command-plan` 不得出现 unknown kind。
- `lint-report`、`doctor`、`final-check`、`close-round` 均不得 FAIL。
- `round_baseline.json` 和 `round_delta_summary.json` 必须存在，且 decision_id/round_id 指向本轮。
- `round_delta_summary.json` 必须区分 `new_dirty_files_since_baseline` 与 `inherited_dirty_files`。
- `codex_report_summary.files_changed` 不得把 inherited dirty files 当成本轮改动列入；若确实触碰了 inherited dirty file，必须在 report 中单独说明并由 decision scope 明确允许。
- `generated_artifacts` 必须覆盖 gate artifacts、round_delta artifacts、round archive。
- `pytest_result.txt` 必须包含 fenced `pytest_result_summary` JSON，并覆盖 report 中所有 `tests_ran`。
- close-round 必须成功生成 round manifest。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要运行样本、solver、IDA/Ghidra/debugger 才能完成本轮。
- 需要读取完整 `solve_reports/`。
- 需要修改 `.codex-skills/`。
- 无法区分 baseline dirty files 与本轮新增 dirty files。
- final-check 只能通过降低校验强度来通过。
- `close-round` 仍无法生成有效 round manifest。
