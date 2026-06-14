```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_gate_preimplementation_baseline_lifecycle_rework_v1",
  "round_id": "round_20260615_gate_preimplementation_baseline_lifecycle_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 project gate 的 baseline 生命周期问题。

问题时间线已经明确：工作区开始时是干净的；实现阶段创建了新源码、新测试和新 state artifact；之后才运行 command-plan 并捕获 baseline。结果 gate 把本轮新建文件误归为 inherited dirty files。

本轮目标：

1. 让 baseline 明确表示 implementation 之前的工作区状态；
2. 让 late baseline 被 gate 检测出来；
3. 让 files_changed 必须覆盖源码、测试、artifact 等实质变更；
4. 让 pytest_result 覆盖 required startup commands；
5. 防止以后只靠报告文字解释 late baseline 并通过 final gate。

本轮只处理工程 gate，不继续推进任何样本分析。

## 2. Current Evidence

当前执行权威是本 decision_packet。task_packet 和 current_state 只能作为 advisory context。

上一轮暴露的工程问题：

- 初始 git status 为空，说明启动时工作区干净；
- 实现阶段创建了新文件；
- command-plan 在实现后才捕获 baseline；
- report 把本轮新文件解释为 inherited dirty files；
- codex_report_summary.files_changed 没有列出实质性源码、测试和 artifact 变更。

这说明需要修 project_gate/project_state 的检查规则，而不是只修改报告正文。

已有能力必须优先复用：

- project_gate 的 preflight / command-plan / report-summary / final-check / close-round；
- project_state 的 doctor / lint-report / report parsing；
- tests/test_project_gate.py；
- tests/test_project_state.py；
- project_state/gates/*.json schema。

## 3. Do Not Do

不得推进样本分析。不得修改样本相关结论。不得修改 .codex-skills、training_materials、solve_reports。不得引入重型 workflow 系统。不得只改报告文字后宣称修复。

## 4. Files To Inspect

必须按顺序读取：

1. project_state/task_packet.json
2. project_state/current_state.json
3. project_state/artifact_index.json
4. project_state/negative_results.json
5. project_state/codex_execution_report.md
6. project_state/decision_packet.md
7. project_state/pytest_result.txt
8. .codex-skills/registry.json

必须有界读取：

- reverse_agent/project_gate.py
- reverse_agent/project_state.py
- tests/test_project_gate.py
- tests/test_project_state.py
- project_state/gates/round_baseline.json
- project_state/gates/round_delta_summary.json
- project_state/gates/command_plan.json
- project_state/gates/final_gate_result.json
- project_state/rounds/round_20260614_cpp1_2f6fcb63_input_delivery_review_v1/round_manifest.json

## 5. Required Audit

Codex 必须先记录启动命令：

- Set-Location F:\reverse-agent
- Get-Location
- Test-Path F:\reverse-agent
- git rev-parse --show-toplevel
- git status --short

必须完成三项修复：

### A. Baseline lifecycle

审查 command-plan 或 gate 何时生成 round_baseline.json，并新增规则：

- baseline 必须代表实现前状态；
- 如果 baseline 缺失而工作区已出现本轮新增源码、测试或 artifact，不能把这些文件当作普通 inherited dirty；
- 如果无法证明 baseline 是实现前捕获，final-check 必须暴露 baseline_lifecycle_violation 或等价状态；
- late baseline 可以被记录，但不能被 clean accept。

### B. files_changed coverage

修复 report-summary / final-check 覆盖规则：

- files_changed 必须覆盖本轮实质性源码、测试、artifact、state 变更；
- 如果 summary 只列 gate/round 文件，但实际有源码、测试、artifact 变更，final-check 必须失败或给出不可 clean accept 的状态；
- inherited dirty allowlist 只能用于启动前真实 dirty 文件。

### C. startup command coverage

修复 required command coverage：

- pytest_result 必须包含 Set-Location F:\reverse-agent；
- command-plan 要求的启动命令必须被 pytest_result 覆盖；
- 缺失 required startup command 时，gate 应报告 coverage failure。

## 6. Implementation Scope

允许修改：

- reverse_agent/project_gate.py
- reverse_agent/project_state.py，仅限 gate/report parsing 需要
- tests/test_project_gate.py
- tests/test_project_state.py
- 可新增 tests/test_project_gate_baseline_lifecycle.py

允许生成或更新：

- project_state/codex_execution_report.md
- project_state/pytest_result.txt
- project_state/gates/command_plan.json
- project_state/gates/preflight_result.json
- project_state/gates/report_summary_synthesis.json
- project_state/gates/final_gate_result.json
- project_state/gates/round_baseline.json
- project_state/gates/round_delta_summary.json
- project_state/rounds/round_20260615_gate_preimplementation_baseline_lifecycle_rework_v1/*

不得修改样本分析 artifact 或样本相关源码测试。

## 7. Tests

必须真实运行并记录到 pytest_result：

- Set-Location F:\reverse-agent
- Get-Location
- Test-Path F:\reverse-agent
- git rev-parse --show-toplevel
- git status --short
- python -m reverse_agent.project_gate preflight --state-dir project_state
- python -m reverse_agent.project_gate command-plan --state-dir project_state
- python -m reverse_agent.project_gate command-plan --state-dir project_state --json
- python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
- 如果新增测试文件：python -m pytest tests/test_project_gate_baseline_lifecycle.py -q
- python -m reverse_agent.project_state doctor --state-dir project_state
- python -m reverse_agent.project_state lint-report --state-dir project_state
- python -m reverse_agent.project_gate report-summary --state-dir project_state
- python -m reverse_agent.project_gate final-check --state-dir project_state
- python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_gate_preimplementation_baseline_lifecycle_rework_v1

新增或更新测试必须覆盖：

- pre-implementation baseline 可以通过；
- implementation 后才 baseline 会触发 lifecycle violation；
- files_changed 漏掉源码、测试或 artifact 变更时不能 clean accept；
- pytest_result 缺少 Set-Location 时应被检测；
- inherited dirty allowlist 不能吞掉本轮新增文件；
- close-round 后 archive 与 live report/pytest 一致。

## 8. Stop Conditions

如果修复需要超出 gate/state 小步范围，停止并报告 BLOCKED_BASELINE_LIFECYCLE_DESIGN_NEEDED。

如果测试或 gate 失败，codex_execution_report 必须标记 FAILED、REWORK_REQUIRED 或 BLOCKED，不能写 SUCCESS/ACCEPTED。

如果 report、pytest、decision id 不匹配，不能 close-round 为 accepted。
