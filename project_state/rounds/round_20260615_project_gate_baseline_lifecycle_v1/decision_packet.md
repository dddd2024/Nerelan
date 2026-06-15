```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_project_gate_baseline_lifecycle_v1",
  "round_id": "round_20260615_project_gate_baseline_lifecycle_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮继续 `engineering_branch`，只修复 project gate 的 round baseline 生命周期语义，不推进样本求解、不继续扩大 `run-round --execute`、不做新的调度系统。

目标是解决上一轮暴露的 baseline 残留问题：`preflight` 在当前 round 已有 baseline 时不会重新捕获，这是正确的；但 `close-round` 归档后没有写入“关闭快照 / baseline inactive”语义，导致旧 baseline 的 `dirty_files` 可能在 round 已关闭或工作区已变干净后仍被后续 gate 当作 active inherited dirty source，从而产生长期 `PASSED_WITH_LIMITATIONS` 噪声。

本轮要实现的是 baseline lifecycle 闭环，而不是覆盖原始 baseline：

1. 保留原始 `round_baseline.json` 作为“本轮开始前状态”的审计证据，不清空、不覆盖、不重捕获。
2. 在 `close-round` 阶段写入独立的 round close snapshot / lifecycle artifact，记录 close 时的 git 状态和 baseline 是否仍 active。
3. 让 `final-check` / `report-summary` 区分 active baseline 与 closed baseline：round 已 closed/archived 后，不再把旧 baseline 的 dirty files 直接当成 active inherited dirty warning；只有 close snapshot 显示 close 时仍 dirty 且未解释时才继续 warning。

## 2. Current Evidence

当前 `task_packet.json` 和 `current_state.json` 仍是旧的 `samplereverse` 压缩样本状态，`task_packet.task=collect_missing_evidence` 只能作为建议；当前轮执行权威是本 `project_state/decision_packet.md`。本轮不推进样本，不补样本 runtime evidence。

`artifact_index.json` 仍有大量历史样本 artifact 为 `missing`。这些缺失只能作为历史限制或状态噪声，不能作为本轮工程改动的 current evidence，也不能触发回到 `reverse_solving`。

`negative_results.json` 中的失败方向仍约束样本求解路径：旧 `sample_solver` blind search、只扩 beam/budget、`compare_semantics_agree=false` frontier、提交完整 `solve_reports`、重复 cpp1 printable inverse path 等。本轮不触碰这些方向。

上一轮 `decision_20260615_project_gate_noise_reduction_v1` 已被 `codex_report_20260615_project_gate_noise_reduction_v1` 消费，报告状态 `SUCCESS`，建议 `ACCEPTED_WITH_LIMITATIONS`。报告说明 command extraction noise reduction 和 report-summary files_changed alignment 已完成。

上一轮 `pytest_result.txt` 显示 `command-plan` 已降为 15 条，只有明确要求的 `python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json`，不再抽取 bare `python -m reverse_agent.project_gate run-round`。

上一轮 `final_gate_result.json` 显示：

- `report_summary_fields_match_synthesis` 已为 PASS，`diffs=[]`。
- `blocking_reasons=[]`，`recommended_next_action=no_action_required`。
- 剩余 warnings 主要是 `files_changed_excludes_inherited_dirty_files` 和 `report_summary_status_source_available`，源头仍是 inherited baseline dirty files：`reverse_agent/project_gate.py`、`tests/test_project_gate.py`。

这说明 `_allowed_inherited_files` 修复已解决 synthesis 对齐问题，但 baseline lifecycle 还未闭环。继续在 report-summary 层做对症补丁意义有限；下一步应处理 close-round 后 baseline active/closed 语义。

当前相关实现集中在：

- `reverse_agent/project_gate.py`：`_capture_round_baseline()`、`_build_round_delta_summary()`、`_round_delta_checks()`、`build_report_summary_synthesis()`、`final_check()`、`close_round()`。
- `tests/test_project_gate.py`：已有 preflight、round baseline/delta、report-summary、final-check、close-round 测试，可扩展覆盖 baseline lifecycle。

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

不要通过重捕获、清空、覆盖或删除 `round_baseline.json` 来消除 warning。原始 baseline 必须作为审计证据保留。

不要把 baseline lifecycle 修成“总是忽略 inherited dirty files”。round 仍 active 或 close snapshot 显示仍 dirty 时，仍应保留真实 warning。

不要通过删除 source/test 文件记录来消除 `files_changed` warning；应修复 baseline active/closed 语义。

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

- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/command_plan.json`
- `project_state/rounds/round_20260615_project_gate_noise_reduction_v1/round_manifest.json`

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
4. Previous noise-reduction report is consumed by a SUCCESS report with ACCEPTED_WITH_LIMITATIONS。
5. Previous command-plan noise and report-summary mismatch are fixed: 15 commands, no bare `run-round`, `report_summary_fields_match_synthesis=PASS`。
6. Remaining warning source is baseline lifecycle, specifically active use of inherited baseline dirty files after close/archive semantics are available.

Required implementation audit:

- Preserve `_capture_round_baseline()` behavior: if current round already has matching baseline, do not recapture or overwrite it.
- Add an explicit close snapshot / lifecycle artifact, for example `project_state/gates/round_close_snapshot.json` or equivalent, written during `close-round`.
- The close snapshot must include at least:
  - `schema_version`
  - `artifact_name`
  - `decision_id`
  - `round_id`
  - `closed_at`
  - `round_closed: true`
  - `baseline_active: false`
  - `close_git_status_short`
  - `close_git_diff_name_only`
  - `close_dirty_files`
  - `close_worktree_clean`
  - `baseline_dirty_files`
  - `inherited_dirty_files_at_close`
  - `recommended_next_action`
- `round_baseline.json` must remain unchanged as original start snapshot. Do not mutate it to fake a clean baseline.
- Update round delta / final-check / report-summary logic to prefer close snapshot semantics when the requested round is closed/archived.
- For an active round without close snapshot, existing inherited dirty warning behavior must remain.
- For a closed/archived round with close snapshot and `close_worktree_clean=true`, do not warn solely because original baseline had dirty files.
- For a closed/archived round with close snapshot and `close_worktree_clean=false`, warn based on `close_dirty_files`, not only on stale `baseline_dirty_files`.
- If close snapshot is missing for an archived round, keep a conservative warning explaining that baseline lifecycle state is unknown.
- Add tests proving baseline is preserved, close snapshot is written, and final-check/report-summary distinguish active baseline from closed baseline.
- Preserve detection of real scope violations and real source/test dirty files. Do not make final-check always pass.

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
- `project_state/rounds/round_20260615_project_gate_baseline_lifecycle_v1/*`

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
- solver / harness / sample-specific modules unrelated to project gate baseline lifecycle

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_gate_baseline_lifecycle_v1
```

Unit test requirements:

- Test preflight does not recapture or overwrite an existing matching `round_baseline.json`.
- Test close-round writes a close snapshot / lifecycle artifact with required fields.
- Test original `round_baseline.json` remains unchanged after close-round.
- Test final-check for active round still warns when `files_changed` includes inherited dirty source/test files.
- Test final-check for closed/archived round with `close_worktree_clean=true` does not warn solely from stale baseline dirty files.
- Test final-check for closed/archived round with `close_worktree_clean=false` warns based on close snapshot dirty files.
- Test report-summary synthesis uses close snapshot semantics and does not reintroduce `report_summary_fields_match_synthesis` false warnings.
- Test real scope violations or unallowed inherited dirty files still produce warnings/failures.

## 8. Stop Conditions

If current working directory is not `F:\reverse-agent`, stop.

If startup repository root is not `F:/reverse-agent` or equivalent, stop.

If `decision_meta` is invalid or `reverse-agent-iteration@v2` is not active, stop.

If there are inherited dirty source/test files outside allowed scope, stop or report baseline explicitly before modifying anything.

If implementing this requires changing solver, strategy, harness runtime, IDA/Ghidra/debugger, or sample-specific code, stop and report `BLOCKED`。

If the only possible implementation is to overwrite or delete `round_baseline.json`, stop and report `REWORK_REQUIRED`。

If closed baseline semantics can only be achieved by ignoring all inherited dirty files, stop and report `REWORK_REQUIRED`。

If live validation would require `run-round --execute`, stop; live command must remain `run-round --dry-run --json`。

If pytest, report-summary, final-check, or close-round fails, do not upload a SUCCESS report; mark `REWORK_REQUIRED` with blocking reasons。
