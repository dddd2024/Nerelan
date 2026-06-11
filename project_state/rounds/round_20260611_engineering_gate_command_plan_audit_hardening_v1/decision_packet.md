```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_engineering_gate_command_plan_audit_hardening_v1",
  "round_id": "round_20260611_engineering_gate_command_plan_audit_hardening_v1",
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

建设门禁系统第三阶段的审计加固层：增强 `project_gate final-check`，让它校验 `project_state/gates/command_plan.json` 与 `codex_execution_report.md`、`pytest_result.txt` 的一致性。

本轮只做 `command-plan` 审计加固，不实现自动 `close-round`，不执行 command plan，不推进样本求解。

必须完成：

1. 在 `final-check` 中新增命令计划一致性检查。
2. 当 report 的 `tests_ran` 或 generated artifacts 涉及 `command-plan` 时，必须检查：
   - `project_state/gates/command_plan.json` 存在；
   - `command_plan.plan_status == PASSED`；
   - `command_plan.decision_id`、`round_id` 与当前 decision/report 一致；
   - `command_plan.commands[].command` 覆盖 `codex_execution_report.md` 的 `tests_ran`；
   - `pytest_result_summary.tests_ran` 覆盖 report `tests_ran`；
   - `pytest_result.txt` 正文中的每个 recorded command exit code 符合 `command_plan.commands[].expected_exit_codes`；
   - `command_plan --json` 的 recorded stdout 包含完整 `commands` 数组，不能是摘要字符串；
   - report 的 `generated_artifacts` 包含 `project_state/gates/command_plan.json`。
3. 将上述规则作为新的 `final-check` check，例如：
   - `command_plan_present`
   - `command_plan_ids_match`
   - `command_plan_covers_report_tests`
   - `pytest_result_exit_codes_match_command_plan`
   - `command_plan_json_stdout_full`
   - `command_plan_generated_artifact_recorded`
4. 添加测试覆盖正常通过和关键失败场景。
5. 保持 `preflight`、`command-plan` 既有行为不削弱。

## 2. Current Evidence

- 上一轮 `decision_20260611_rework_command_plan_exact_json_output_v1` 已完成并被审计接受。
- `command-plan --json` 的完整 stdout 已重新写入 `pytest_result.txt`。
- 当前 `command_plan.json` 已包含完整 `commands` 数组、expected exit codes、phase/kind 信息。
- 当前 `final-check` 仍主要检查 report/pytest/archive/git diff 一致性，尚未强制验证 `command_plan.json` 与 report/pytest_result 的逐命令一致性。
- 当前 `task_packet.json` 和历史 artifact 仍带有旧 `samplereverse` 样本上下文；本轮仍必须保持 `engineering_branch`，不能被旧建议带回 reverse_solving。
- `negative_results.json` 仍禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 solve_reports 等方向。
- 本轮不涉及样本求解、IDA、solver、runtime、training status。

## 3. Do Not Do

- 不实现自动 `close-round`。
- 不执行 command plan 中的命令。
- 不运行样本二进制。
- 不运行 solver、candidate search、runtime probe、debugger、hook、emulator、sidecar。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何具体样本求解。
- 不修改 `.codex-skills/`。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不修改训练集状态、IDA runner、solver/runtime/debugger/probe 模块。
- 不削弱现有 `preflight`、`command-plan` 或 `final-check` 基础规则。
- 不把 stale/missing artifacts 当 current evidence。

## 4. Files To Inspect

必须检查：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`

必要时检查：

- `.codex-skills/registry.json`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent`.
2. Confirm active decision is this packet and `status` is `APPROVED`.
3. Run `python -m reverse_agent.project_gate preflight --state-dir project_state` before modification. If it blocks, stop and report.
4. Confirm this is `engineering_branch`, not sample-solving.
5. Inspect existing `final_check()`, `command_plan()`, and pytest result parsing code before adding checks.
6. Reuse existing helpers where possible; avoid a second independent decision/report parser.
7. Add or reuse a small parser for `pytest_result.txt` recorded command blocks that extracts:
   - command string;
   - exit code;
   - stdout/stderr body;
   - whether command output contains JSON.
8. Add `final-check` checks that fail when:
   - command plan is missing while report/tests mention `command-plan`;
   - command plan IDs mismatch current decision/report round;
   - command plan commands do not cover report `tests_ran`;
   - report `tests_ran` or pytest_result_summary tests are not covered by command plan;
   - any recorded command has an exit code outside `expected_exit_codes`;
   - `command-plan --json` recorded stdout lacks full `commands` list or has `commands` as a string summary;
   - `generated_artifacts` omits `project_state/gates/command_plan.json`.
9. Existing successful closeout should still produce `final-check: PASSED`.
10. Add tests for:
    - successful command-plan/report/pytest_result consistency;
    - missing command_plan.json;
    - command_plan decision_id or round_id mismatch;
    - command_plan missing a report test command;
    - pytest_result command exit code not in command_plan expected_exit_codes;
    - command-plan --json output abbreviated as string instead of full list;
    - report generated_artifacts missing command_plan.json;
    - final-check behavior for ordinary rounds without command-plan remains compatible.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if shared helper exposure is strictly necessary

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if shared helper tests are necessary

Allowed generated files:

- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_engineering_gate_command_plan_audit_hardening_v1/*`

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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_engineering_gate_command_plan_audit_hardening_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

`pytest_result.txt` 必须使用正式 `pytest_result_summary`，并记录所有命令 stdout/stderr。`command-plan --json` 的 stdout 必须包含完整 `commands` 数组。

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `preflight` cannot pass before modifications.
- final-check cannot detect command_plan/report/pytest_result mismatch.
- command exit code parsing is unreliable or silently ignores malformed command blocks.
- `command-plan --json` full-output check cannot distinguish a list from a summary string.
- Existing final-check compatible behavior breaks for rounds without command-plan.
- Fixing this requires implementing automatic `close-round`.
- Fixing this requires touching sample-solving/tooling modules.
- Final git status contains scope-out files.
