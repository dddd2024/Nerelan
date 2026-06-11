```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_engineering_gate_command_plan_v1",
  "round_id": "round_20260611_engineering_gate_command_plan_v1",
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

建设门禁系统第三阶段的准备层：新增只读 `command-plan` / `closeout-plan` 能力，把 `decision_packet.md` 的 `Tests` 命令解析成结构化执行计划，为后续自动 `close-round` 做前置准备。

本轮只做“解析和计划生成”，不执行计划中的命令，不自动写 report，不自动 archive，不推进样本求解。

必须完成：

1. 扩展现有 `project_gate` CLI，新增只读命令：
   ```bash
   python -m reverse_agent.project_gate command-plan --state-dir project_state
   ```
2. 输出结构化计划：
   ```text
   project_state/gates/command_plan.json
   ```
3. 从当前 active `decision_packet.md` 的 `## 7. Tests` / fenced bash block 中提取命令序列。
4. 每条命令生成结构化字段：
   - `index`
   - `command`
   - `phase`
   - `required`
   - `expected_exit_codes`
   - `records_stdout_stderr`
   - `notes`
5. 识别并标记门禁命令：
   - `preflight`
   - `final-check`
   - `lint-report`
   - `status`
   - `doctor`
   - `archive-round`
   - `pytest`
   - `git status`
6. 识别不应该作为普通成功命令处理的 expected nonzero diagnostic，例如 post-report `preflight BLOCKED`。
7. 提供 `--json` 输出模式，stdout 可打印完整 JSON。
8. 添加测试覆盖命令解析、phase 分类、expected exit code、空 Tests、缺 fenced bash block、post-report preflight 诊断分类等场景。

## 2. Current Evidence

- 上一轮 `decision_20260611_engineering_gate_preflight_exit_policy_v1` 已完成并被审计接受。
- `project_gate preflight` 已能在 `BLOCKED` / `FAILED` 时返回非 0，具备开工前强制阻断能力。
- `project_gate final-check` 已能检查 report/pytest/archive/git diff 的收尾一致性。
- 当前 `task_packet.json` 与 `current_state.json` 仍包含旧 `samplereverse` 样本求解上下文和历史 artifact 指针；本轮必须继续保持 `engineering_branch`，不能被旧建议带回 reverse_solving。
- `artifact_index.json` 仍有大量 stale/missing 历史样本 artifact。engineering round 不应声明它们为 current evidence。
- `negative_results.json` 明确禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 solve_reports 等方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active。
- 现在的主要返工点已经从“手工发现 report/archive 不一致”转为“如何安全自动化 close-round”。下一步应先生成 command plan，避免直接做执行器。

## 3. Do Not Do

- 不实现自动 `close-round`。
- 不执行 command plan 中的命令。
- 不自动生成或重写 `codex_execution_report.md`。
- 不自动生成或重写 `pytest_result.txt`，除本轮真实测试记录外。
- 不运行样本二进制。
- 不运行 solver、candidate search、runtime probe、debugger、hook、emulator、sidecar。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何具体样本求解。
- 不修改 `.codex-skills/`。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不削弱现有 `preflight` 和 `final-check` 规则。
- 不把 stale/missing artifacts 当 current evidence。

## 4. Files To Inspect

必须检查：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/decision_packet.md`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`

必要时检查：

- `README.md`
- `pyproject.toml`

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent`.
2. Confirm active decision is this packet and `status` is `APPROVED`.
3. Run or inspect `project_gate preflight` before modifying code; if it blocks, stop and report.
4. Confirm this is `engineering_branch` and not a sample-solving round.
5. Confirm skill profiles are active.
6. Inspect existing `project_gate.preflight()` and `project_gate.final_check()` before adding `command-plan`.
7. Reuse existing markdown parsing helpers if suitable; avoid a second independent decision parser.
8. Add a command-plan schema similar to:
   ```json
   {
     "schema_version": 1,
     "plan_name": "command-plan",
     "decision_id": "",
     "round_id": "",
     "mainline": "",
     "commands": [],
     "warnings": [],
     "blocking_reasons": [],
     "recommended_next_action": ""
   }
   ```
9. Each command entry must include:
   ```json
   {
     "index": 1,
     "command": "python -m pytest ...",
     "phase": "preflight | test | gate | archive | post_archive | status | unknown",
     "required": true,
     "expected_exit_codes": [0],
     "records_stdout_stderr": true,
     "notes": ""
   }
   ```
10. Classification rules must distinguish:
    - `preflight` before report consumption: expected exit `[0]`;
    - post-report `preflight` diagnostic: expected nonzero is allowed only when explicitly marked in decision text;
    - `final-check`: expected `[0]` unless the plan explicitly marks expected failure;
    - `archive-round`: expected `[0]`;
    - pytest commands: expected `[0]`;
    - lint/status/doctor: expected `[0]`.
11. If `Tests` is missing or no fenced bash command block exists, `command-plan` must return `FAILED` or include blocking_reasons.
12. Add tests for:
    - normal command extraction from fenced bash block;
    - phase classification;
    - expected_exit_codes for preflight/final-check/archive/pytest;
    - missing Tests section;
    - empty bash block;
    - post-report preflight diagnostic only allowed when decision says expected nonzero;
    - command-plan CLI writes `project_state/gates/command_plan.json`;
    - `preflight` and `final-check` existing tests still pass.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if helper exposure is strictly necessary

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if shared helper tests are necessary

Allowed generated files:

- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_engineering_gate_command_plan_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- sample binaries
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- solver modules
- IDA/Ghidra/debugger/runtime/probe modules
- training inventory/status/queue files

## 7. Tests

Run and record exact outputs:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_engineering_gate_command_plan_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

`pytest_result.txt` 必须使用正式 `pytest_result_summary`，并记录所有命令 stdout/stderr。

注意：本轮 `command-plan` 只能生成计划，不得执行计划中的命令。若需要执行计划，应停止并生成下一轮 decision。

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `preflight` 不能通过。
- 无法可靠解析 `Tests` 命令块。
- `command-plan` 会执行命令。
- `command-plan` 会修改除 `project_state/gates/command_plan.json` 之外的 live state。
- 无法区分 post-report preflight diagnostic 与 normal preflight。
- 实现需要触碰 sample solving、IDA runner、solver、runtime、training status。
- final-check 被削弱或现有 gate tests 失败。
- final git status 出现 scope 外文件。
