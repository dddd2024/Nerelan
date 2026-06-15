```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_project_state_mainline_clarity_v1",
  "round_id": "round_20260615_project_state_mainline_clarity_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮继续 `engineering_branch`，目标是改进 `project_state` / status 输出的主线归一化表达，使已经关闭并通过的工程 round 之后，状态包能明确区分：

1. 最新 accepted / closed engineering round；
2. 当前 `decision_packet.md` 是否已经被消费；
3. `task_packet.json` / `current_state.json` 中旧 sample 状态是否只是 advisory / historical；
4. `artifact_index.json` 中历史 sample missing 是否只是 `external_state_notices`，而不是当前工程主线 blocker；
5. 未来什么时候应切回 `reverse_solving`、`tool_integration` 或 `training_dataset`。

本轮不是样本求解，不修复 `samplereverse` / `cpp1_2f6fcb63` 的 candidate，不补 runtime evidence，不运行 solver。目标是让状态包和 CLI 输出减少歧义，避免后续 Codex 或其他 agent 被旧样本状态误导。

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是本轮执行权威；`task_packet.json` 仍保留旧 `samplereverse` 压缩样本任务，例如 `task=collect_missing_evidence`，只能作为 advisory / historical，不得覆盖本 decision。

上一轮 `decision_20260615_project_gate_mainline_status_policy_v1` 已完成并被报告消费：`codex_execution_report.md` 状态为 `SUCCESS`，`acceptance_recommendation=ACCEPTED`，`final_gate_result.json` 显示 `gate_status=PASSED`，`blocking_reasons=[]`，`warnings=[]`，`recommended_next_action=no_action_required`。

上一轮已实现主线感知 status policy：工程主线下的 `50 missing historical sample artifacts` 被保留为 `external_state_notices`，不再把当前工程 round 降级为 `PASSED_WITH_LIMITATIONS`。这些历史缺失仍必须可见，不得删除或伪装为已修复。

`artifact_index.json` 仍包含大量旧 `samplereverse` missing artifact，也包含若干 `local_reverse_*` current artifact。旧 `samplereverse` missing 不是本轮 current evidence；`local_reverse_*` current artifact 也不是本轮要验证的样本求解证据，除非只读输出需要引用其 provenance。

`negative_results.json` 仍约束样本求解路径：不要回旧 `sample_solver` blind search，不要只扩 beam / budget，不要使用 `compare_semantics_agree=false` candidate 作为 primary frontier，不要提交完整 `solve_reports`，不要重复 cpp1 printable inverse path。本轮不触碰这些方向。

已有相关能力：

- `reverse_agent/project_state.py`：状态构建、doctor、lint-report、status summary、round consistency、report / decision / pytest 校验。
- `reverse_agent/project_gate.py`：preflight、command-plan、run-round、report-summary、final-check、close-round、mainline-aware historical sample limitation policy。
- `tests/test_project_state.py` 和 `tests/test_project_gate.py`：状态包、报告、门禁和 round 闭环测试。

本轮不需要 IDA / Ghidra / debugger / solver / harness 接口；涉及逆向工具能力的内容只允许作为“不得触碰”的边界检查。

## 3. Do Not Do

不要推进 `samplereverse`、`cpp1_2f6fcb63` 或任何其他样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/` 或 `.codex-skills/registry.json`。

不要把动态事实写入 `.codex-skills/`。

不要把 stale / missing artifact 当作 current evidence。

不要把 `task_packet.task` 当作本轮执行权威。

不要通过删除、伪造、清空 `artifact_index.json`、`current_state.json` 或历史 sample state 来消除历史 missing artifact 噪声。

不要把 historical sample missing artifacts 全局忽略。`reverse_solving`、`tool_integration`、`training_dataset` 仍必须严格检查 current artifact freshness。

不要为了得到 `PASSED` 而放宽真实 blocking_reasons、scope violations、report/decision mismatch、pytest mismatch、command-plan mismatch、baseline lifecycle failures。

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

Must inspect current gate/status artifacts:

- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/rounds/round_20260615_project_gate_mainline_status_policy_v1/round_manifest.json`

Must inspect implementation files:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`

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
4. Previous round `decision_20260615_project_gate_mainline_status_policy_v1` was consumed by a `SUCCESS` / `ACCEPTED` report。
5. Previous final gate is `PASSED` and exposes historical sample artifact missing as `external_state_notices`。
6. Historical sample artifact missing remains visible; it must not be deleted from `artifact_index.json`。

Required implementation audit:

- Identify where `status_summary()` / `doctor()` / `build_round_consistency()` / build output currently expose decision consumption, active decision, current mainline, advisory task packet classification, and historical sample artifact notices.
- Reuse existing state/status functions where possible. Do not create a parallel state system.
- Prefer adding small, stable fields or check details that clarify mainline authority and historical/advisory status, for example:
  - `active_decision_state`
  - `latest_closed_round_id`
  - `latest_accepted_round_id`
  - `task_packet_role=advisory`
  - `historical_external_state_notices`
  - `current_mainline_status`
  - or equivalent existing-schema-compatible names.
- If existing fields already provide the information, improve CLI output and tests instead of adding redundant fields.
- Preserve backward compatibility with existing `task_packet.json`, `current_state.json`, `artifact_index.json`, and gate artifacts.
- Do not mutate `artifact_index.json` as part of the fix.
- Do not hide actual project_state schema errors, report/decision mismatch, pytest mismatch, command-plan mismatch, baseline lifecycle failures, forbidden paths, or scope violations.

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
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260615_project_state_mainline_clarity_v1/*`

Read-only / no mutation:

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- `reverse_agent/ida_scripts/`
- `reverse_agent/olly_scripts/`
- `reverse_agent/probes/`
- solver / harness / sample-specific modules unrelated to project state and project gate status reporting

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
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_state_mainline_clarity_v1
```

Unit test requirements:

- Test engineering_branch closed / accepted round exposes clear latest closed / accepted decision or equivalent status field.
- Test consumed `decision_packet.md` is not confused with advisory `task_packet.json`.
- Test old sample `task_packet.task=collect_missing_evidence` remains advisory / historical when current mainline is engineering_branch.
- Test historical sample artifact missing remains visible as external / historical notice and does not block engineering_branch.
- Test reverse_solving / tool_integration / training_dataset do not ignore current artifact freshness when the current decision depends on artifact evidence.
- Test report/decision mismatch still fails.
- Test pytest_result/report mismatch still fails.
- Test forbidden path or scope violation still fails.
- Test command-plan / report-summary / final-check remain consistent after any added field/output changes.

## 8. Stop Conditions

If current working directory is not `F:\reverse-agent`, stop.

If startup repository root is not `F:/reverse-agent` or equivalent, stop.

If `decision_meta` is invalid or `reverse-agent-iteration@v2` is not active, stop.

If there are inherited dirty source/test files outside allowed scope, stop or report baseline explicitly before modifying anything.

If implementing this requires changing solver, strategy, harness runtime, IDA/Ghidra/debugger, or sample-specific code, stop and report `BLOCKED`。

If the only possible implementation is to edit, delete, or clear historical sample artifact entries from `artifact_index.json`, stop and report `REWORK_REQUIRED`。

If status clarity can only be achieved by ignoring all limitations globally, stop and report `REWORK_REQUIRED`。

If `reverse_solving`, `tool_integration`, or `training_dataset` current artifact checks would be weakened, stop and report `REWORK_REQUIRED`。

If live validation would require `run-round --execute`, stop; live command must remain `run-round --dry-run --json`。

If pytest, lint-report, report-summary, final-check, or close-round fails, do not upload a `SUCCESS` report; mark `REWORK_REQUIRED` with blocking reasons。
