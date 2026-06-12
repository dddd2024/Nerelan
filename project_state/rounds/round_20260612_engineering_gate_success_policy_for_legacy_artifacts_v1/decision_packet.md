```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_gate_success_policy_for_legacy_artifacts_v1",
  "round_id": "round_20260612_engineering_gate_success_policy_for_legacy_artifacts_v1",
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

把上一轮 `PARTIAL + NEEDS_REVIEW` 的 limited closeout 合同推进到可干净验收的工程状态：当本轮是纯 `engineering_branch` gate/report/closeout 修复，且所有工程 gate 检查、测试、archive 和 command-plan 均通过时，历史样本 artifact freshness 不得继续把本轮工程 closeout 限制为 `PARTIAL` 或 `WARN`。

本轮只修工程状态策略，不恢复逆向求解、不跑样本、不刷新训练数据。

必须完成：

1. 让纯工程 gate/report round 可以用合法状态 `SUCCESS + ACCEPTED` 收尾，并让 final-check 达到 `PASSED`。
2. 保留 artifact freshness 可见性：`3 missing, 48 stale` 这类历史样本状态仍应在 status/doctor 中可审计，但在纯工程 gate/report round 中应被归类为 non-current legacy/sample artifact condition，不得作为工程 closeout blocking warning。
3. 不得全局降低 artifact freshness 约束；`reverse_solving`、`tool_integration`、`training_dataset`，以及任何声明或验证 current artifact 的 report，仍必须执行严格 freshness 规则。
4. 增加回归测试，覆盖：
   - 纯工程 gate/report SUCCESS round 在 legacy sample artifacts stale/missing 时仍可 final-check `PASSED`；
   - sample/tool/training 或 report claim current artifact 时 stale/missing 仍不能被静默放行；
   - `PARTIAL` 和 `BLOCKED` 现有合同仍保持上一轮行为；
   - command-plan、archive/live、files_changed/generated_artifacts 检查仍为硬约束。
5. 完成后更新本轮 `codex_execution_report.md`、`pytest_result.txt`、gate artifacts 和 round archive。

## 2. Current Evidence

- 当前 active decision 是 `decision_20260612_engineering_gate_limited_closeout_contract_v1`，主线为 `engineering_branch`，上一轮 report 已合法表达为 `PARTIAL + NEEDS_REVIEW`。
- 上一轮测试真实通过：`python -m pytest tests/test_project_gate.py tests/test_project_state.py -q` 记录为 `248 passed`。
- command-plan 已为 `PASSED`，`git diff --name-only` 已被归类为 `git diff`，不再是 unknown kind。
- final-check 当前为 `WARN`，但 blocking_reasons 为空；唯一 WARN 是 `status_policy_valid: PARTIAL report is internally consistent`，根因是本轮 report 仍是 `PARTIAL` 且 doctor 存在 non-success / artifact freshness warnings。
- doctor 当前 WARN 包含 `decision_execution_state is CONSUMED_BY_NON_SUCCESS_REPORT` 和 `artifacts: 3 missing, 48 stale artifacts`。这些 artifact 是旧 samplereverse/sample context 的 historical condition，不是上一轮工程 gate 修复生成或验证的 current artifact。
- `task_packet.json` 与 `current_state.json` 仍包含旧 samplereverse 求解背景和 candidate/frontier 信息；它们只能作为状态事实/旧上下文，不能覆盖本轮 engineering decision。
- `artifact_index.json` 同时登记了大量 stale sample artifacts 和两个 current static triage metadata artifacts；本轮不得把 stale artifacts 当 current evidence，也不得为了消除 WARN 去伪造 freshness。
- `negative_results.json` 禁止重复旧 sample_solver blind search、扩 beam/budget、重复 breakpoint/runtime probe、提交完整 solve_reports 等方向。本轮不触碰这些方向。
- 已有相关能力：`reverse_agent/project_gate.py` 已包含 `preflight`、`command-plan`、`final-check`、`close-round`；`reverse_agent/project_state.py` 已包含 report schema、lint-report、doctor、status、archive-round。不得新建重复 gate/status 系统。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 为 active。

## 3. Do Not Do

- 不处理任何逆向题目的具体解法。
- 不运行样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、harness campaign、solver、candidate search 或 bruteforce。
- 不生成 candidate、flag、密码或答案。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不上传 raw sample、sample binary、IDA database、debug trace 或完整运行产物目录。
- 不修改 `.codex-skills/`。
- 不把 stale/missing artifact 改成 current。
- 不删除或篡改 artifact_index 中的历史样本事实来消除 WARN。
- 不把 artifact freshness 规则全局降级。
- 不把失败命令改写成成功。
- 不绕过 command-plan、archive/live、files_changed/generated_artifacts 检查。
- 不把 `task_packet.json` 的旧 sample task 当作本轮执行权威。

## 4. Files To Inspect

必须先读：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

可有界读取：

- `project_state/rounds/round_20260612_engineering_gate_limited_closeout_contract_v1/round_manifest.json`
- 与 status/doctor/final-check/report schema 直接相关的测试 fixture

不得默认读取：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- 大体积历史 archive

## 5. Required Audit

Codex 必须：

1. 确认工作目录为 `F:\reverse-agent`。
2. 记录启动 baseline：`git status --short` 与 `git diff --name-only`。
3. 读取默认 project_state 文件，并确认本 decision 是当前执行权威，`task_packet.json` 只是 advisory。
4. 确认 skill profiles active。
5. 审计 `project_state.status_summary()` / `doctor()` / `lint_report()` 中 artifact freshness 的 blocking/warn 语义。
6. 审计 `project_gate.final_check()` 中 `status_policy_valid` 对 `SUCCESS`、`PARTIAL`、`BLOCKED` 的处理。
7. 明确区分两类情况：
   - 纯工程 gate/report closeout，不声明 current artifact、不验证 artifact、不推进样本；legacy sample artifact freshness 只能作为可见信息，不应阻塞工程 SUCCESS。
   - 样本求解、工具接入、训练集，或 report 声明/验证 current artifact；stale/missing artifact 必须继续阻塞或至少保持 blocking warning。
8. 确认不通过修改 `artifact_index.json`、`current_state.json`、`task_packet.json` 来掩盖历史状态。
9. 增加测试，证明上述分类不会导致 stale/missing artifacts 被全局放行。
10. 完成后用 `SUCCESS + ACCEPTED` 更新本轮 report；只有 final-check `PASSED` 后才允许写 `SUCCESS + ACCEPTED`。
11. 使用 `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_engineering_gate_success_policy_for_legacy_artifacts_v1` 完成本轮 archive。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_state.py`
- `tests/test_project_gate.py`

Allowed generated files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_engineering_gate_success_policy_for_legacy_artifacts_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- sample binaries
- training inventory files
- `project_state/artifact_index.json` except read-only inspection
- `project_state/current_state.json` except read-only inspection
- `project_state/task_packet.json` except read-only inspection
- solver modules
- harness modules
- IDA/Ghidra/debugger integration files
- unrelated source modules
- unrelated tests
- historical round archives except read-only inspection

## 7. Tests

必须运行并记录真实 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
git diff --name-only
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_engineering_gate_success_policy_for_legacy_artifacts_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

验收条件：

- pytest 必须通过。
- preflight 必须通过。
- command-plan 必须 `PASSED`，不得出现 unknown kind WARN。
- lint-report 必须 OK。
- doctor 对本轮 `SUCCESS + ACCEPTED` 不得因为 legacy sample artifacts 返回 blocking WARN/FAIL；若保留信息性 artifact warning，final-check 不得因此降为 WARN。
- final-check 必须 `PASSED`，所有 checks 不得有 `FAIL`；若仍有 `WARN`，report 不得写 `SUCCESS + ACCEPTED`。
- close-round 必须 `CLOSED`，archive/live 一致。
- `git diff --name-only` 只能包含本轮允许文件。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要修改 `.codex-skills/` 才能完成。
- 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt` 才能完成。
- 需要运行题目、调试器、emulator、runtime probe、solver 或工具接入流程。
- 需要修改 `artifact_index.json`、`current_state.json`、`task_packet.json` 来掩盖历史状态。
- 无法区分工程 closeout 与样本/tool/training artifact freshness 约束。
- 回归测试显示 sample/tool/training stale/missing artifacts 被放行。
- final-check 仍为 WARN/FAILED，但 report 准备写 `SUCCESS + ACCEPTED`。
- command-plan、archive/live、files_changed/generated_artifacts 任一检查仍失败。
- 需要改动本轮 scope 外源码、测试或训练材料。
