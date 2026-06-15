```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_project_gate_run_round_orchestrator_v1",
  "round_id": "round_20260615_project_gate_run_round_orchestrator_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮切回 `engineering_branch`，实现门禁流程的一键化基础能力，减少 Codex/GPT 每轮反复复制、执行、整理门禁命令的操作成本。

目标是在现有 `reverse_agent.project_gate` 中新增 `run-round` 编排入口，复用现有 `preflight`、`command-plan`、`report-summary`、`final-check`、`close-round` 语义，不改变现有各门禁的判定规则。

本轮只做门禁工程，不推进任何样本求解，不运行 runtime probe，不修改 solver / strategy / IDA / Ghidra / debugger / harness 语义。

本轮交付的核心能力：

- `python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json` 可生成结构化 `project_state/gates/run_round_result.json`。
- `run-round` 能从现有 `command-plan` 读取待执行命令，产出机器可读的执行计划 / dry-run 结果。
- 为后续轮次启用 `run-round --execute` 打基础，但本轮不能用未验证的新 `run-round --execute` 关闭自己的改动。

## 2. Current Evidence

当前 `task_packet.json` 和 `current_state.json` 仍残留 `samplereverse` 压缩状态，但本轮不是样本求解，`task_packet.task` 只能作为建议，当前执行权威是本 `project_state/decision_packet.md`。

上一轮 `decision_20260615_cpp1_success_boundary_static_recheck_v1` 已被 `codex_report_20260615_cpp1_success_boundary_static_recheck_v1` 消费，报告状态为 `SUCCESS`，建议为 `ACCEPTED_WITH_LIMITATIONS`。`final_gate_result.json` 显示上一轮 `gate_status=PASSED_WITH_LIMITATIONS`，无 blocking reasons，round archive 已存在。

上一轮 `cpp1_2f6fcb63` 的静态边界重查产物 `project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json` 给出 `recommended_next_action=STOP_TARGET_OR_BOUNDARY_CONTRADICTION`。因此不应继续拿当前 18 字节 payload 做 runtime validation，也不应重复 printable inverse path。

当前工程已有门禁能力：

- `project_gate.py` 已有 `preflight`、`command-plan`、`report-summary`、`final-check`、`close-round` 子命令。
- `command_plan()` 已能从 `Required Audit` 和 `Tests` 提取命令，分类 command kind，并写出 `project_state/gates/command_plan.json`。
- `preflight()` 已在启动阶段捕获 round baseline，检查 `decision_meta`、主线、skill、scope、artifact freshness、tool capability audit 等。
- `final_check()` 已检查 report / pytest / command_plan / round archive / generated_artifacts / forbidden paths 等一致性。
- `close_round()` 已负责归档 round，并在成功关闭时把 close-round command block 追加回 `pytest_result.txt`。
- 当前 `project_gate.py` 没有 `run-round` 子命令；`_command_kind()` 也没有识别 `run-round`。

已有相关测试：

- `tests/test_project_gate.py` 已覆盖 `preflight`、`command_plan`、`final_check`、`report_summary`、`close_round`、CLI `main()` 等门禁核心路径。
- `tests/test_project_state.py` 是 project_state / gate 一致性相关的配套测试。

本轮应复用这些能力，不要新建独立门禁系统，不要把一键门禁做成与现有 `command-plan` / `final-check` 并行的第二套规则。

## 3. Do Not Do

不要推进 `samplereverse`、`cpp1_2f6fcb63` 或任何其他样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要新建重复门禁系统；必须复用现有 `preflight`、`command-plan`、`report-summary`、`final-check`、`close-round`。

不要让 `run-round --execute` 在本轮关闭自己的实现改动；本轮只能对 live `project_state` 跑 `run-round --dry-run`，执行模式必须通过临时目录单测覆盖。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要把动态事实写入 `.codex-skills/`。

不要修改 `.codex-skills/registry.json`。

不要把 stale/missing artifact 当作 current evidence。

不要把上一轮 `cpp1` 的 `STOP_TARGET_OR_BOUNDARY_CONTRADICTION` 绕开后继续做 runtime validation。

## 4. Files To Inspect

Must read in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Must inspect implementation files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if needed for pytest_result writing / command result compatibility
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if a project_state helper is touched

May bounded-read, only for current evidence / stop condition confirmation:

- `project_state/gates/final_gate_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck.json`

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Startup commands must be recorded first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

If startup dirty files exist, capture them as baseline before implementation and do not classify inherited dirty files as current round work.

Before changing code, verify:

1. `decision_meta` is parseable, `status=APPROVED`, `mainline=engineering_branch`。
2. `reverse-agent-iteration@v2` exists and is active in `.codex-skills/registry.json`。
3. Current `decision_packet.md` is the execution authority; `task_packet.json` is advisory only。
4. Existing `project_gate` already has individual gate commands and command-plan extraction; do not duplicate these rules。
5. `run-round` is absent or incomplete before implementation; if it already exists locally after pull, inspect and extend it instead of replacing it。
6. The previous `cpp1` sample route is stopped by boundary contradiction; do not continue it in this engineering round。

Required implementation audit:

- Add a new result artifact name, e.g. `RUN_ROUND_RESULT_NAME = "run_round_result.json"` and write to `project_state/gates/run_round_result.json`。
- Add a new command kind for `run-round` so `command-plan` can classify `python -m reverse_agent.project_gate run-round ...`。
- Add a `run_round(...)` function or equivalent internal entry point that reuses `preflight()` and `command_plan()`。
- `--dry-run` must not execute command-plan commands; it should validate/generate the plan and write a structured result。
- Execution-mode internals may be implemented, but must be tested only in temporary test state directories in this round。
- If execution-mode is implemented, it must be fail-fast by default: stop after the first command with an unexpected exit code, record the failing command, and avoid running later gates after a blocking failure。
- If execution-mode is implemented, avoid duplicate close-round recording: when `close-round` is executed as a subprocess, do not append a second duplicate close-round command block from `run-round`。
- `run_round_result.json` must include at least: `schema_version`, `gate_name="run-round"`, `run_status`, `decision_id`, `round_id`, `mode`, `command_count`, `commands`, `executed_commands`, `blocking_reasons`, `warnings`, `recommended_next_action`。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if `reverse_agent/project_state.py` is touched

Allowed generated files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260615_project_gate_run_round_orchestrator_v1/*`

Conditionally allowed source file:

- `reverse_agent/project_state.py` only if required for reusable pytest_result command-block writing; otherwise do not touch it。

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- `reverse_agent/ida_scripts/`
- `reverse_agent/olly_scripts/`
- `reverse_agent/probes/`
- solver / harness / sample-specific modules unrelated to project gate execution

## 7. Tests

Must record commands, stdout/stderr, and exit code in `project_state/pytest_result.txt`.

Required command sequence for this implementation round:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_gate_run_round_orchestrator_v1
```

Unit test requirements:

- Test `run-round --dry-run --json` returns zero exit and writes `project_state/gates/run_round_result.json`。
- Test `run_round(..., dry_run=True)` does not execute planned commands。
- Test `command_plan()` classifies `run-round` as a known gate command, not `unknown`。
- Test execution-mode logic, if implemented, using a temporary state directory and injected/fake command runner; do not execute live project_state through `--execute` in this round。
- Test fail-fast behavior for an unexpected nonzero exit, if execution mode is implemented。
- Test report/final gate compatibility when `run_round_result.json` is a generated gate artifact。

## 8. Stop Conditions

If current working directory is not `F:\reverse-agent`, stop.

If startup repository root is not `F:/reverse-agent` or equivalent, stop.

If `decision_meta` is invalid or `reverse-agent-iteration@v2` is not active, stop.

If there are inherited dirty source/test files outside allowed scope, stop or report baseline explicitly before modifying anything.

If implementing `run-round` requires changing solver, strategy, harness runtime, IDA/Ghidra/debugger, or sample-specific code, stop and report `BLOCKED`。

If `run-round --dry-run --json` cannot be made safe and non-executing, stop before adding execution mode。

If command execution recording cannot preserve stdout, stderr, and exit code in the existing command-block format, do not claim `run-round --execute` is ready。

If `close-round` behavior would create duplicate command blocks or inconsistent archive metadata, keep execution mode disabled or test-only and report the limitation。

If pytest, report-summary, final-check, or close-round fails, do not upload a success report; mark `REWORK_REQUIRED` with blocking reasons。
