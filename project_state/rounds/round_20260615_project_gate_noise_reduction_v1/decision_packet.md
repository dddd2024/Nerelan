```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_project_gate_noise_reduction_v1",
  "round_id": "round_20260615_project_gate_noise_reduction_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮继续 `engineering_branch`，只修复上一轮门禁闭环中的两个质量噪声，不推进 `run-round --execute` 的 live 使用，也不推进任何逆向样本。

目标是让门禁输出更稳定、更少误报：

1. 修复 `command-plan` 的命令抽取边界，避免从说明性 / 禁止性 / 单测描述文本中误抽出 bare `python -m reverse_agent.project_gate run-round` 这类并未作为本轮执行命令要求的条目。
2. 修复 `report-summary` / `final-check` 对 `files_changed` 的合成与比较逻辑，使允许范围内实际修改的 source/test 文件不会因为 synthesis 只偏向 generated artifacts 而产生无意义的 summary mismatch。

本轮不是继续硬化 execute 模式本身。`run-round --execute` 仍然不得在 live `project_state` 上运行；live 验证仍只允许 `run-round --dry-run --json`。

## 2. Current Evidence

当前 `task_packet.json` 和 `current_state.json` 仍是旧的 `samplereverse` 压缩样本状态，`task_packet.task=collect_missing_evidence` 只能作为建议；当前轮执行权威是本 `project_state/decision_packet.md`。本轮不推进样本，不补样本 runtime evidence。

`artifact_index.json` 仍有大量历史样本 artifact 为 `missing`。这些缺失只能作为历史限制或状态噪声，不能作为本轮工程改动的 current evidence，也不能触发回到 reverse_solving。

`negative_results.json` 中的失败方向仍约束样本求解路径：旧 `sample_solver` blind search、只扩 beam/budget、`compare_semantics_agree=false` frontier、提交完整 `solve_reports`、重复 cpp1 printable inverse path 等。本轮不触碰这些方向。

上一轮 `decision_20260615_project_gate_run_round_execute_hardening_v1` 已被 `codex_report_20260615_project_gate_run_round_execute_hardening_v1` 消费，报告状态 `SUCCESS`，建议 `ACCEPTED_WITH_LIMITATIONS`。报告说明 `run-round --execute` 已通过 self-invocation guard、close-round delegation、command-block recording 做了测试化硬化，但 live `project_state` 只跑了 dry-run。

上一轮 `pytest_result.txt` 显示本轮门禁记录中出现了两条 run-round 命令：

- `python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json`
- `python -m reverse_agent.project_gate run-round`

其中第一条是 decision 明确要求的 live dry-run；第二条 bare `run-round` 不是 `Tests` 必需命令，应作为命令抽取噪声处理。

上一轮 final gate 为 `PASSED_WITH_LIMITATIONS`，blocking_reasons 为空，recommended_next_action 为 `no_action_required`。非阻塞 warnings 包括：

- `files_changed_excludes_inherited_dirty_files`：`files_changed` 包含 inherited baseline dirty files，且报告解释这些文件在允许 source/test scope 内。
- `report_summary_fields_match_synthesis`：`codex_report_summary` 与 synthesized summary 的 `files_changed` 字段不同。
- `report_summary_status_source_available`：report summary synthesis 有 source warnings。

这些 warnings 不代表实现失败，但会降低门禁信噪比。当前最合理的下一步是修复门禁抽取和合成逻辑，而不是继续扩大 `run-round --execute` 或转回样本求解。

当前相关实现集中在：

- `reverse_agent/project_gate.py`：`command_plan()`、命令抽取、`build_report_summary_synthesis()`、`final_check()`、baseline-aware files_changed 相关检查。
- `tests/test_project_gate.py`：已有大量 command-plan、report-summary、final-check、close-round、run-round 测试。

`.codex-skills/registry.json` 中 `reverse-agent-iteration` 为 active，version=2，可继续作为本轮 skill profile。

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

不要通过删除 source/test 文件记录来消除 `files_changed` warning；应修复 synthesis / comparison 逻辑，使其正确表达实际修改。

不要放宽 final gate 到忽略真实 mismatch；本轮只消除已知误报和抽取噪声。

不要引入数据库、队列、workflow engine、后台任务、GitHub Actions 或重型调度系统。

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

May bounded-read, only for current evidence / compatibility checks:

- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/round_manifest.json`

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
4. Previous execute-hardening report is consumed by a SUCCESS report with ACCEPTED_WITH_LIMITATIONS。
5. `pytest_result.txt` shows bare `python -m reverse_agent.project_gate run-round` was recorded as a command-plan command even though it is not a required command in the Tests sequence。
6. `final_gate_result.json` shows report-summary mismatch around `files_changed` source/test entries and no blocking reasons。

Required implementation audit:

- Tighten command extraction so only explicit executable commands in approved command-bearing contexts are emitted:
  - fenced command blocks under `Required Audit` / `Tests`;
  - backtick commands that contain complete executable command lines under `Required Audit` / `Tests`;
  - approved Chinese natural-language gate checklist expansion already covered by tests.
- Do not extract commands from `Do Not Do`, `Current Evidence`, `Stop Conditions`, ordinary prose, unit-test bullet descriptions, or prohibition examples.
- Add regression test using a decision text that contains `run-round` in prose / prohibition / unit-test requirement text; command-plan must keep the required dry-run command but must not emit bare `python -m reverse_agent.project_gate run-round`.
- Preserve existing command-plan behavior for legitimate explicit commands in `Required Audit` and `Tests`.
- Repair report-summary synthesis so `files_changed` comparison aligns with final gate semantics:
  - generated artifacts remain generated artifacts;
  - substantive source/test files changed within allowed scope may appear in `files_changed` without causing `report_summary_fields_match_synthesis` warning solely because synthesis omitted them;
  - inherited baseline dirty files that are explicitly allowed and explained should not create a summary mismatch if they are also substantive allowed scope files.
- Add regression test where report `files_changed` includes `reverse_agent/project_gate.py` and `tests/test_project_gate.py` plus generated artifacts; report-summary synthesis and final-check should not warn solely on that difference.
- Preserve detection of real report-summary mismatch; do not make synthesis comparison always pass.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

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
- `project_state/rounds/round_20260615_project_gate_noise_reduction_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- `reverse_agent/ida_scripts/`
- `reverse_agent/olly_scripts/`
- `reverse_agent/probes/`
- `reverse_agent/project_state.py` unless a blocking test proves `project_gate.py` cannot own the fix
- solver / harness / sample-specific modules unrelated to project gate command extraction or report-summary synthesis

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_gate_noise_reduction_v1
```

Unit test requirements:

- Test command-plan does not extract bare `python -m reverse_agent.project_gate run-round` from `Do Not Do`, `Stop Conditions`, or unit-test requirement prose.
- Test command-plan still extracts the explicit live dry-run command from the Tests command sequence.
- Test command-plan still extracts valid fenced and backtick commands under `Required Audit` / `Tests`.
- Test report-summary synthesis includes or normalizes allowed source/test `files_changed` consistently with final gate expectations.
- Test final-check no longer emits `report_summary_fields_match_synthesis` WARN when the only difference is allowed source/test files that are actually part of the round delta and are explicitly reported.
- Test final-check still fails or warns for real mismatches, such as missing required generated artifacts or source/test files outside allowed scope.

## 8. Stop Conditions

If current working directory is not `F:\reverse-agent`, stop.

If startup repository root is not `F:/reverse-agent` or equivalent, stop.

If `decision_meta` is invalid or `reverse-agent-iteration@v2` is not active, stop.

If there are inherited dirty source/test files outside allowed scope, stop or report baseline explicitly before modifying anything.

If implementing this requires changing solver, strategy, harness runtime, IDA/Ghidra/debugger, or sample-specific code, stop and report `BLOCKED`。

If command-plan noise cannot be fixed without breaking existing explicit command extraction, stop and report `REWORK_REQUIRED`。

If report-summary mismatch can only be hidden by ignoring all files_changed differences, stop and report `REWORK_REQUIRED`。

If live validation would require `run-round --execute`, stop; live command must remain `run-round --dry-run --json`。

If pytest, report-summary, final-check, or close-round fails, do not upload a SUCCESS report; mark `REWORK_REQUIRED` with blocking reasons。
