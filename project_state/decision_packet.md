```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_gate_limited_closeout_contract_v1",
  "round_id": "round_20260612_engineering_gate_limited_closeout_contract_v1",
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

修复 gate closeout 合同，让“已真实完成但有受限项”的收尾状态可以被系统稳定表达，而不是在 live 文件、archive 快照、command-plan 和 final-check 之间反复冲突。

本轮目标是工程修复，不处理任何题目内容，不生成答案，不扩大到工具接入。

必须完成：

1. 将受限完成状态统一映射到现有合法状态：`codex_report_summary.status = PARTIAL`，`acceptance_recommendation = NEEDS_REVIEW` 或 `REWORK_REQUIRED`。不得再写 `LIMITED_SUCCESS`、`REJECTED`、`COMPLETED_WITH_LIMITATIONS` 到 report schema 字段。
2. 修复 `project_gate` 的 closeout 判断：truthful `PARTIAL` report 可以形成 `WARN` final-check，并允许 `close-round` 关闭；只有虚假成功、元数据不匹配、未记录命令、archive 缺失、scope 越界才是 `FAIL`。
3. 消除 command-plan 的误报来源：常用工程命令必须被识别或被明确归类，不能因为 `git diff --name-only` 等普通审计命令是 unknown kind 导致 closeout 无法稳定完成。
4. 增加回归测试，覆盖 SUCCESS、PARTIAL、BLOCKED 三类 report 的 final-check / close-round 行为。
5. 更新本轮 report、pytest_result、gate artifacts 和 round archive，确保本轮自身可审计。

## 2. Current Evidence

- 当前 active decision 是上一轮 closeout 修复，mainline 为 `engineering_branch`，但执行结果为受限完成。
- 最新 `codex_execution_report.md` 顶部 summary 使用了非法 report status：`LIMITED_SUCCESS`，acceptance recommendation 使用了非法值：`REJECTED`。现有 schema 只接受 `SUCCESS`、`PARTIAL`、`FAILED`、`BLOCKED` 等合法 report status，以及 `ACCEPTED`、`REWORK_REQUIRED`、`BLOCKED`、`NEEDS_REVIEW` 等合法 recommendation。
- 最新 `pytest_result.txt` 记录了真实命令输出，其中 preflight、lint-report、doctor、final-check 曾出现非零 exit code；这些记录不能被伪造成全通过。
- final-check 当前失败项主要集中在 closeout 合同：archive/live 快照关系、command-plan status/coverage/exit-code 匹配、status policy。
- `reverse_agent/project_gate.py` 已有 `preflight`、`command-plan`、`final-check`、`close-round` 能力；本轮应修复这些已有能力，不新增重复 gate 系统。
- `reverse_agent/project_state.py` 已有 report status 和 acceptance recommendation 枚举；优先复用现有合法状态，不新增同义状态。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 为 active。
- `task_packet.json` 仍可能包含旧求解背景，只能作为 advisory；当前执行权威必须是本 `decision_packet.md`。
- artifact freshness 中存在 historical stale/missing 记录；本轮不得把这些历史记录当作当前证明，也不得为了清理历史状态扩大 scope。

## 3. Do Not Do

- 不处理逆向题目的具体解法。
- 不运行样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、harness campaign、solver、candidate search 或 bruteforce。
- 不生成 candidate、flag、密码或答案。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不上传 raw sample、sample binary、IDA database、debug trace 或完整运行产物目录。
- 不修改 `.codex-skills/`。
- 不把失败命令改写成成功。
- 不用手写 summary 掩盖真实 gate 失败。
- 不把 `LIMITED_SUCCESS`、`REJECTED`、`COMPLETED_WITH_LIMITATIONS` 继续写入 report schema 字段。
- 不在本轮同时推进训练集刷新、题目分析、工具接入和工程 gate 重构之外的工作。

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

- 当前 round archive 的 `round_manifest.json`
- 与 `project_gate` / report schema 直接相关的测试 fixture

不得默认读取：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- 大体积历史 archive

## 5. Required Audit

Codex 必须：

1. 确认工作目录为 `F:\reverse-agent`。
2. 记录启动 baseline：`git status --short`。
3. 读取默认 project_state 文件，并确认本 decision 是当前执行权威，`task_packet.json` 只是建议。
4. 确认 skill profiles active。
5. 审计 `CODEX_REPORT_STATUSES` 与 `CODEX_REPORT_ACCEPTANCE_RECOMMENDATIONS`，不得引入与现有语义重复的新状态。
6. 审计 `project_gate.final_check()` 与 `project_gate.close_round()` 对 `SUCCESS`、`PARTIAL`、`BLOCKED` report 的差异化处理。
7. 审计 command-plan 的 command kind 识别；至少修复普通审计命令造成的 unknown kind 误报。
8. 增加测试证明：
   - `SUCCESS + ACCEPTED` 仍必须严格通过；
   - `PARTIAL + NEEDS_REVIEW` 在元数据、命令记录、scope 和 archive 都一致时，final-check 只能是 `WARN`，不能是 `FAILED`；
   - `BLOCKED + BLOCKED` 在元数据一致时可被稳定记录，不能被误判成虚假成功；
   - archive 前允许仅存在 archive pending 类检查；archive 后 archive/live 检查必须稳定。
9. 完成后更新 `codex_execution_report.md` 和 `pytest_result.txt`，真实记录所有命令 stdout/stderr/exit code。
10. 使用 `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_engineering_gate_limited_closeout_contract_v1` 完成本轮 archive；不要手动删除旧 archive。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if required to keep report schema/status validation consistent

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state schema validation is touched

Allowed generated files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_engineering_gate_limited_closeout_contract_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- training inventory files
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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_engineering_gate_limited_closeout_contract_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

测试判定：

- pytest 必须通过。
- preflight 必须通过。
- command-plan 不得因为本轮列出的普通工程命令出现 unknown kind WARN。
- lint-report 和 doctor 不得因非法 report status 或 report/decision mismatch 失败。
- final-check 若 report status 为 `PARTIAL`，允许 gate status 为 `WARN`；不允许出现 `FAIL` check。
- close-round 必须成功生成本轮 archive，且不得覆盖或删除旧 round archive。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要修改 `.codex-skills/` 才能完成。
- 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt` 才能完成。
- 需要运行题目、调试器、emulator、runtime probe 或工具接入流程。
- 需要改动本轮 scope 外源码、测试或训练材料。
- 不能用合法 report status 表达受限完成。
- 需要伪造命令输出或把失败命令写成成功。
- close-round 仍需要手动删除旧 archive 才能完成。
- final-check 仍存在 `FAIL` check，但 report 却准备写 `SUCCESS` / `ACCEPTED`。
