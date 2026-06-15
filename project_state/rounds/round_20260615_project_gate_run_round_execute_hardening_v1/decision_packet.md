```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_project_gate_run_round_execute_hardening_v1",
  "round_id": "round_20260615_project_gate_run_round_execute_hardening_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮继续 `engineering_branch`，在上一轮 `run-round --dry-run` 已验收的基础上，硬化 `run-round --execute` 的安全执行契约。

目标不是让 live `project_state` 直接用 `run-round --execute` 关闭本轮，而是先把执行模式中最容易造成门禁失控的两个问题做成可测试规则：

1. 防止 `run-round --execute` 执行 command-plan 中的 `run-round` 自调用，避免递归或重复编排。
2. 为 execute 模式建立 pytest_result command block 记录能力，确保每条真实执行命令都能记录 stdout、stderr、exit_code，同时避免与 `close-round` 自己追加的 command block 重复。

本轮结束时，`run-round --dry-run --json` 仍然是 live `project_state` 上允许执行的验证命令；`run-round --execute` 只能通过临时 state 目录和 fake/injected runner 单测验证，不得用于关闭本轮自己的改动。

## 2. Current Evidence

当前 `task_packet.json` / `current_state.json` 仍是旧的 `samplereverse` 压缩样本状态，`task_packet.task=collect_missing_evidence` 只能作为建议；当前轮执行权威是本 `project_state/decision_packet.md`。本轮不推进 `samplereverse`，不收集样本 runtime evidence。

`artifact_index.json` 仍有大量历史样本 artifact 为 `missing`。这些缺失只能作为历史限制，不能作为本轮工程实现的 current evidence，也不能因此回到样本求解主线。

上一轮 `decision_20260615_project_gate_run_round_orchestrator_v1` 已被 `codex_report_20260615_project_gate_run_round_orchestrator_v1` 消费，报告状态 `SUCCESS`，建议 `ACCEPTED_WITH_LIMITATIONS`。限制项明确说明：`run-round --execute` 只用 injected runner 做了单测，live `project_state` 只跑了 `--dry-run`。

上一轮 final gate 为 `PASSED_WITH_LIMITATIONS`，blocking_reasons 为空，recommended_next_action 为 `no_action_required`。限制来自历史样本 artifact 缺失，不是本轮门禁工程失败。

当前 `project_gate.py` 已有相关能力：

- `RUN_ROUND_NAME = "run-round"`。
- `RUN_ROUND_RESULT_NAME = "run_round_result.json"`。
- `_command_kind()` 能把 `project_gate run-round` 分类为 `run-round`。
- `_command_phase()` 能把 `run-round` 归类为 `gate`。
- `run_round(..., dry_run=True)` 会调用 `preflight()` 和 `command_plan()`，但不执行 planned commands。
- `run_round(..., dry_run=False)` 已有 fail-fast 基础逻辑，会保存 `executed_commands` 到 `run_round_result.json`，但还没有明确的自调用 skip 策略和 pytest_result command block 记录契约。
- `close-round` CLI 已经自己负责在成功关闭时追加 close-round command block 到 `project_state/pytest_result.txt`。

当前 `project_state/gates/run_round_result.json` 显示 live dry-run：`run_status=PASSED`、`mode=dry-run`、`command_count=15`、`executed_commands=[]`、`recommended_next_action=review_plan_before_execute`。

当前测试已覆盖：dry-run JSON 输出、dry-run 不执行 planned commands、command-plan 将 run-round 分类为 gate、execute 模式 fail-fast fake runner。下一步应扩展这些测试，不应删除或弱化它们。

`negative_results.json` 中的失败方向仍只约束样本求解路径，包括旧 sample_solver blind search、只扩 beam/budget、compare_semantics_agree=false frontier、提交完整 solve_reports、cpp1 printable inverse path等。本轮不触碰这些路径。

## 3. Do Not Do

不要推进 `samplereverse`、`cpp1_2f6fcb63` 或任何其他样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/` 或 `.codex-skills/registry.json`。

不要把动态事实写入 `.codex-skills/`。

不要把 stale/missing artifact 当作 current evidence。

不要把 `task_packet.task` 当作本轮执行权威。

不要在 live `project_state` 上执行 `python -m reverse_agent.project_gate run-round --state-dir project_state --execute`。

不要让 `run-round --execute` 执行 command-plan 里的任何 `run-round` 自调用；必须将其显式 skip 并记录 skip reason。

不要让 `run-round` 自己重复追加 `close-round` 的 command block；`close-round` 子进程仍是 close-round block 的唯一 owner。

不要为了实现 execute 硬化引入数据库、队列、workflow engine、后台任务、GitHub Actions 或重型调度系统。

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
- `tests/test_project_gate.py`

Conditionally inspect:

- `reverse_agent/project_state.py` only if command-block writing must reuse existing pytest_result helpers located there.
- `tests/test_project_state.py` only if `reverse_agent/project_state.py` is touched.

May bounded-read, only for current evidence / compatibility checks:

- `project_state/gates/run_round_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/rounds/round_20260615_project_gate_run_round_orchestrator_v1/round_manifest.json`

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
4. Previous `run-round --dry-run` round is consumed by a SUCCESS report with ACCEPTED_WITH_LIMITATIONS。
5. `project_state/gates/run_round_result.json` exists and records dry-run mode with `executed_commands=[]`。
6. Existing `close-round` command block append behavior remains the owner for close-round output; do not duplicate it from `run-round`。

Required implementation audit:

- Add an explicit self-invocation guard for `run_round(..., dry_run=False)`。
- Any command whose kind is `run-round`, or whose command text invokes `python -m reverse_agent.project_gate run-round`, must be skipped by default during execute mode。
- Skipped self-invocation commands must be recorded in `run_round_result.json` under a structured field such as `skipped_commands` with at least: `index`, `command`, `kind`, `phase`, `reason`。
- `run_round_result.json` must continue to include existing fields: `schema_version`, `gate_name`, `run_status`, `decision_id`, `round_id`, `mode`, `command_count`, `commands`, `executed_commands`, `blocking_reasons`, `warnings`, `recommended_next_action`。
- Add fields needed to audit execution logging, e.g. `skipped_commands`, `recorded_command_blocks`, or equivalent。
- In execute mode, record stdout/stderr/exit_code for executed commands in the existing `pytest_result.txt` command-block format when a safe test state path is provided。
- Do not duplicate the close-round command block. If execute mode reaches a `close-round` command, either skip run-round's own append for that command and let `close-round` append itself, or record a clear test-only policy proving no duplicate block occurs。
- Preserve fail-fast behavior: after the first executed command with an unexpected exit code, stop executing later commands and record blocking_reasons。
- Preserve dry-run behavior: dry-run must not execute or append any command blocks。
- Preserve existing CLI behavior: `run-round --dry-run --json` must still return JSON and write `project_state/gates/run_round_result.json`。

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
- `project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/*`

Conditionally allowed source file:

- `reverse_agent/project_state.py` only if required to reuse or expose command-block writing helpers; otherwise do not touch it。

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
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_gate_run_round_execute_hardening_v1
```

Unit test requirements:

- Test `run_round(..., dry_run=False)` skips command-plan entries whose kind is `run-round` and records them in `skipped_commands`。
- Test a command text containing `python -m reverse_agent.project_gate run-round --state-dir ... --execute` is skipped and not executed。
- Test execute mode records non-run-round executed command stdout/stderr/exit_code in memory result and command-block output in a temporary `pytest_result.txt`。
- Test execute mode fail-fast still stops after the first unexpected exit code and does not execute later commands。
- Test dry-run still leaves `executed_commands=[]` and does not append command blocks。
- Test close-round command block duplication is prevented or explicitly delegated to close-round。
- Test `run-round --dry-run --json` still returns exit code 0 and writes `project_state/gates/run_round_result.json`。

## 8. Stop Conditions

If current working directory is not `F:\reverse-agent`, stop.

If startup repository root is not `F:/reverse-agent` or equivalent, stop.

If `decision_meta` is invalid or `reverse-agent-iteration@v2` is not active, stop.

If there are inherited dirty source/test files outside allowed scope, stop or report baseline explicitly before modifying anything.

If implementing this requires changing solver, strategy, harness runtime, IDA/Ghidra/debugger, or sample-specific code, stop and report `BLOCKED`。

If execute-mode command block recording cannot preserve stdout, stderr, and exit code, do not claim execute mode is hardened。

If self-invocation guard cannot reliably prevent recursive `run-round --execute`, stop and report `BLOCKED`。

If close-round command block behavior would become duplicated or inconsistent, keep execute mode test-only and report the limitation。

If pytest, report-summary, final-check, or close-round fails, do not upload a SUCCESS report; mark `REWORK_REQUIRED` with blocking reasons。
