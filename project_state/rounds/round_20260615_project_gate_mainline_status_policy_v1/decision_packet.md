```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_project_gate_mainline_status_policy_v1",
  "round_id": "round_20260615_project_gate_mainline_status_policy_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮继续 `engineering_branch`，只修复 project gate 的 status policy 主线作用域问题，不推进样本求解、不继续扩大 `run-round --execute`、不做新的调度系统。

目标是解决当前最后一个门禁噪声：在工程主线 round 已经无 blocking_reasons、无 gate warnings、report-summary 已 PASSED、baseline lifecycle 已闭环的情况下，final gate 仍因为历史样本 artifact 缺失显示 `PASSED_WITH_LIMITATIONS`。这些历史样本 artifact 缺失来自旧 `samplereverse` / artifact_index 压缩状态，不是当前 `engineering_branch` decision 的 current evidence，也不是本轮工程改动的验收依据。

本轮要实现主线感知的 status policy：

1. 对 `engineering_branch`，历史样本 artifact 缺失只能作为 external state notice / historical context，不应导致当前工程 round 被降级为 `PASSED_WITH_LIMITATIONS`。
2. 对 `reverse_solving`、`tool_integration`、`training_dataset`，如果 decision 当前依赖样本 artifact、工具 artifact、训练 inventory 或 current evidence，缺失仍应保留为 warning / limitation / blocking reason，不得被全局忽略。
3. final-check、report-summary synthesis、lint-report / status policy 的结论应一致：当工程 round 只有历史样本缺失这一类外部限制时，允许 gate_status 变为 `PASSED`，recommended_next_action 仍为 `no_action_required`。
4. 保留历史样本缺失的可见性：可以记录为 `external_state_notices`、`historical_limitations_ignored_for_mainline` 或等价字段，但不得伪装为已修复样本 artifact。

## 2. Current Evidence

当前 `task_packet.json` 和 `current_state.json` 仍是旧的 `samplereverse` 压缩样本状态，`task_packet.task=collect_missing_evidence` 只能作为建议；当前轮执行权威是本 `project_state/decision_packet.md`。本轮不推进样本，不补样本 runtime evidence。

`artifact_index.json` 仍有大量历史样本 artifact 为 `missing`。这些缺失只能作为历史限制或状态噪声，不能作为本轮工程改动的 current evidence，也不能触发回到 `reverse_solving`。

`negative_results.json` 中的失败方向仍约束样本求解路径：旧 `sample_solver` blind search、只扩 beam/budget、`compare_semantics_agree=false` frontier、提交完整 `solve_reports`、重复 cpp1 printable inverse path 等。本轮不触碰这些方向。

上一轮 `decision_20260615_project_gate_baseline_lifecycle_v1` 已被 `codex_report_20260615_project_gate_baseline_lifecycle_v1` 消费，报告状态 `SUCCESS`，建议 `ACCEPTED_WITH_LIMITATIONS`。

上一轮已完成 baseline lifecycle closure：

- `project_state/gates/round_close_snapshot.json` 已生成。
- `round_closed=true`。
- `baseline_active=false`。
- `final-check` 中 `files_changed_excludes_inherited_dirty_files=PASS`。
- `baseline_lifecycle_guard=PASS`。
- `report_summary_fields_match_synthesis=PASS`。
- `report_summary_status_source_available=PASS`。
- `blocking_reasons=[]`。
- `warnings=[]`。

上一轮 final gate 仍为 `PASSED_WITH_LIMITATIONS`，唯一可见限制是 `status_policy_valid` 中的 `limitations=["50 missing historical sample artifacts"]`。这说明剩余问题不是 baseline lifecycle，也不是 command-plan/report-summary mismatch，而是 status policy 对历史样本状态缺少 mainline scoping。

当前相关实现集中在：

- `reverse_agent/project_gate.py`：`status_summary()` usage, `final_check()`, status policy checks, `_status_policy_failure_is_historical_artifacts_only()`, `_patch_gate_result_historical_artifacts()`, `build_report_summary_synthesis()`, report acceptance recommendation synthesis.
- `tests/test_project_gate.py`：已有 final-check、report-summary、close-round、baseline lifecycle、status policy 相关测试，可扩展覆盖 mainline-scoped historical limitations。

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

不要通过删除、伪造、清空 `artifact_index.json` 或历史 sample state 来消除 `50 missing historical sample artifacts`。

不要把 historical sample missing artifacts 全局忽略。`reverse_solving`、`tool_integration`、`training_dataset` 仍需要严格检查 current artifact freshness。

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

Must inspect implementation files:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

May bounded-read, only for current evidence / compatibility checks:

- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/rounds/round_20260615_project_gate_baseline_lifecycle_v1/round_manifest.json`

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
4. Previous baseline-lifecycle report is consumed by a SUCCESS report with ACCEPTED_WITH_LIMITATIONS。
5. Previous baseline lifecycle issue is fixed: close snapshot exists, `baseline_active=false`, report-summary synthesis PASSED, final gate warnings empty。
6. Remaining limitation is historical sample artifacts only, visible as `50 missing historical sample artifacts` under status policy limitations。

Required implementation audit:

- Identify where `50 missing historical sample artifacts` is derived and how it flows into:
  - `status_policy_valid`
  - final gate `gate_status`
  - report-summary synthesis `limitations`
  - report acceptance recommendation synthesis
- Add a mainline-aware classification for historical sample artifact limitations.
- For `engineering_branch`, if historical sample artifact missing is not referenced by the current decision's Files To Inspect / Implementation Scope / Tests / Current Evidence as required current evidence, classify it as non-blocking external state notice.
- For `engineering_branch`, when there are no blocking reasons and no warnings besides historical sample artifact limitations, final gate should be allowed to return `PASSED` rather than `PASSED_WITH_LIMITATIONS`.
- Preserve visibility by emitting structured data such as:
  - `external_state_notices`
  - `ignored_historical_limitations`
  - `mainline_scoped_limitations`
  - or equivalent field in final gate / report-summary output.
- For `reverse_solving`, `tool_integration`, and `training_dataset`, missing current artifacts must remain warnings/limitations or blocking reasons according to existing freshness and decision evidence rules.
- If a future engineering decision explicitly lists sample artifacts as current required evidence, do not ignore those missing artifacts.
- Do not mutate `artifact_index.json` as part of the fix.
- Do not hide actual project_state schema errors, report/decision mismatch, pytest mismatch, command-plan mismatch, baseline lifecycle failures, forbidden paths, or scope violations.

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
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260615_project_gate_mainline_status_policy_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `project_state/artifact_index.json`
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- `reverse_agent/ida_scripts/`
- `reverse_agent/olly_scripts/`
- `reverse_agent/probes/`
- `reverse_agent/project_state.py` unless a blocking test proves `project_gate.py` cannot own the fix
- solver / harness / sample-specific modules unrelated to project gate status policy scoping

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_gate_mainline_status_policy_v1
```

Unit test requirements:

- Test engineering_branch final-check treats historical sample artifact missing as external state notice when not required by the current decision.
- Test engineering_branch final-check can return `PASSED` when the only previous limitation is historical sample artifact missing and all gate checks pass.
- Test report-summary synthesis for engineering_branch does not synthesize `ACCEPTED_WITH_LIMITATIONS` solely from historical sample artifact missing.
- Test external/historical limitations remain visible in structured output.
- Test reverse_solving does not ignore missing current sample artifacts.
- Test tool_integration / training_dataset or capability mainline does not globally ignore missing current tool/sample/inventory artifacts.
- Test explicit engineering decision references to sample artifacts as required current evidence preserve warning/limitation behavior.
- Test real failures still fail: report/decision mismatch, pytest mismatch, forbidden paths, command-plan mismatch, baseline lifecycle failure.

## 8. Stop Conditions

If current working directory is not `F:\reverse-agent`, stop.

If startup repository root is not `F:/reverse-agent` or equivalent, stop.

If `decision_meta` is invalid or `reverse-agent-iteration@v2` is not active, stop.

If there are inherited dirty source/test files outside allowed scope, stop or report baseline explicitly before modifying anything.

If implementing this requires changing solver, strategy, harness runtime, IDA/Ghidra/debugger, or sample-specific code, stop and report `BLOCKED`。

If the only possible implementation is to edit or remove historical sample artifact entries from `artifact_index.json`, stop and report `REWORK_REQUIRED`。

If status policy scoping can only be achieved by ignoring all limitations globally, stop and report `REWORK_REQUIRED`。

If `reverse_solving` missing current artifact checks would be weakened, stop and report `REWORK_REQUIRED`。

If live validation would require `run-round --execute`, stop; live command must remain `run-round --dry-run --json`。

If pytest, report-summary, final-check, or close-round fails, do not upload a SUCCESS report; mark `REWORK_REQUIRED` with blocking reasons。
