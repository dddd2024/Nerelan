```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_state_package_compact_output_v1",
  "round_id": "round_20260612_engineering_state_package_compact_output_v1",
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

本轮目标是收口上一轮 `project_state` 状态包分类输出：保留 authoritative / advisory / derived_cache / archive / heavy_history 分类能力，但让默认 `status`、`doctor`、`doctor --json` 输出保持紧凑，避免把全部历史 `project_state/rounds/<round_id>/*` archive 条目写入默认上下文和 `pytest_result.txt`。

本轮只做输出压缩与只读诊断改进，不物理合并状态文件，不删除历史 round，不实现自动 `close-round`，不推进样本求解。

必须完成：

1. 保持 `build_state_package_classification()` 或等效 helper 能识别：
   - `authoritative`；
   - `advisory`；
   - `derived_cache`；
   - `archive`；
   - `heavy_history`。
2. 修改默认 `status` / `doctor` / `doctor --json` 输出策略，使其默认只输出：
   - 分类 `summary`；
   - 固定核心 entries：`decision_packet.md`、`current_state.json`、`artifact_index.json`、`negative_results.json`、`codex_execution_report.md`、`pytest_result.txt`、`task_packet.json`；
   - gate derived cache entries：`project_state/gates/preflight_result.json`、`project_state/gates/command_plan.json`、`project_state/gates/final_gate_result.json`；
   - heavy history entries：`solve_reports/`、`PROJECT_PROGRESS_LOG.txt`；
   - 当前 report/decision round 对应的 archive entry；
   - 至多少量 archive examples 或 `archive_omitted_count`，不能全量展开历史 archive。
3. 在 JSON 输出中显式提供：
   - `entries_compacted: true`；
   - `archive_total_count`；
   - `archive_included_count`；
   - `archive_omitted_count`；
   - 若存在当前 round archive，必须包含当前 round archive entry。
4. 保持非 JSON `doctor` 输出为单行或少量行摘要，不打印全部 archive entries。
5. 保持 `status` 输出只给 summary 和 compactness 标记，不打印全部 entries。
6. 添加测试，证明：
   - `doctor --json` 默认不会全量输出所有 historical round archive entries；
   - 当前 round archive entry 仍被保留；
   - `archive_omitted_count` 正确大于 0 when many archives exist；
   - `task_packet.json` 仍是 `advisory` 且不能覆盖 decision；
   - gate outputs 仍是 `derived_cache`；
   - `solve_reports/` 与 `PROJECT_PROGRESS_LOG.txt` 仍是 `heavy_history`；
   - 现有 `preflight`、`command-plan`、`final-check` 行为不被削弱。
7. 不改变现有 `decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt` 的正式 schema。

## 2. Current Evidence

- 当前主线是 `engineering_branch`，不是 `reverse_solving`、`tool_integration` 或 `training_dataset`。
- 上一轮 `decision_20260612_engineering_state_package_rationalization_v1` 已有 `SUCCESS` report，`based_on_decision_id` 与上一轮 decision 匹配，`acceptance_recommendation` 为 `ACCEPTED`。
- 上一轮测试记录显示 `225 passed`，`preflight`、`command-plan`、`final-check` 均通过。
- 上一轮实现已让 `status` 输出 `state_package_classification` summary，当前 live 输出中分类计数为 `authoritative=6`、`advisory=2`、`derived_cache=3`、`archive=110`、`heavy_history=2`。
- 上一轮 `doctor` 和 `doctor --json` 已明确：`task_packet.json` advisory、`decision_packet.md` authoritative、`gates/*.json` derived_cache、`rounds/<round_id>/*` archive、`solve_reports/` 和 `PROJECT_PROGRESS_LOG.txt` heavy_history。
- 审计限制：当前 `doctor --json` 默认会将约 110 个 historical round archive entries 全量写入 JSON 输出，并被记录进 `pytest_result.txt`，这与降低默认上下文冗余的目标冲突。
- 当前 `task_packet.json` 与 `current_state.json` 仍含旧 `samplereverse` 样本求解上下文和大量 `solve_reports` artifact refs，只能作为 advisory/background，不能覆盖本轮 decision。
- 当前 `artifact_index.json` 仍含大量 stale/missing 历史样本 artifact；本轮不得把它们当 current evidence。
- `negative_results.json` 继续禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 `solve_reports` 等方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active skill profile。
- 现有相关工程能力包括：`project_state status`、`project_state doctor`、`project_state lint-report`、`project_state archive-round`、`project_gate preflight`、`project_gate command-plan`、`project_gate final-check`。
- 本轮不需要 IDA、Ghidra、debugger、solver、harness、runtime probe、sidecar 或训练集接口能力；不得假设这些能力不存在，也不得修改它们。

## 3. Do Not Do

- 不实现自动 `close-round`。
- 不物理合并、删除或迁移 `task_packet.json`、`current_state.json`、`artifact_index.json`、`negative_results.json`、`decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt`。
- 不删除或压缩实际 `project_state/rounds/` 历史归档文件。
- 不新增数据库、队列、workflow engine 或重型状态管理层。
- 不把 `.codex-skills/` 当动态状态写入目标。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不运行样本二进制。
- 不运行 solver、candidate search、runtime probe、debugger、hook、emulator、sidecar。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何具体样本求解。
- 不修改训练集状态、训练样本 inventory、IDA/Ghidra/debugger/runtime/probe 模块。
- 不把 stale/missing artifact 当 current evidence。
- 不改变现有 report/pytest/decision 正式 schema。
- 不削弱 `preflight`、`command-plan`、`final-check` 的现有检查。
- 不把 compact 输出变成隐藏错误：summary counts 必须仍准确反映 archive 总数。

## 4. Files To Inspect

必须检查：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`

必要时检查：

- `.codex-skills/registry.json`
- 当前 report round 的 `project_state/rounds/round_20260612_engineering_state_package_rationalization_v1/round_manifest.json`

不得默认检查：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- sample binaries

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent` using `Get-Location` or equivalent shell output.
2. Confirm `Test-Path F:\reverse-agent` succeeds and record it in `pytest_result.txt`.
3. Capture `git status --short` before modification.
4. Read the default project_state files in order:
   - `project_state/task_packet.json`
   - `project_state/current_state.json`
   - `project_state/artifact_index.json`
   - `project_state/negative_results.json`
   - `project_state/codex_execution_report.md`
   - `project_state/decision_packet.md`
   - `project_state/pytest_result.txt`
5. Confirm this packet is the active decision and `status` is `APPROVED`.
6. Run `python -m reverse_agent.project_gate preflight --state-dir project_state` before modification. If it blocks, stop and report.
7. Confirm this is `engineering_branch`, not sample-solving.
8. Inspect existing `status_summary()`, `doctor()`, `build_state_package_classification()` or equivalent helper, `lint_report()`, and gate code before implementing compact output.
9. Reuse existing parsing helpers and avoid adding a second independent decision/report parser.
10. Implement compact output through a small helper or option that separates full classification inventory from default displayed/serialized entries.
11. Ensure compact JSON still contains enough information for audit: summary counts, compactness metadata, core entries, current round archive entry, omitted archive count.
12. Ensure `task_packet.json` remains explicitly `advisory` and cannot override `decision_packet.md` in status/doctor/preflight output.
13. Ensure `gates/preflight_result.json`, `gates/command_plan.json`, and `gates/final_gate_result.json` remain `derived_cache`, not original facts.
14. Ensure `rounds/<round_id>/*` remains classified as `archive`, but historical archives are not all emitted by default.
15. Ensure stale/missing artifact summary remains non-blocking for healthy engineering rounds and is not reinterpreted as current sample evidence.
16. Add tests for compactness and compatibility.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py` only if gate output needs to consume compact classification metadata

Allowed tests:

- `tests/test_project_state.py`
- `tests/test_project_gate.py` only if gate compatibility tests need updates

Allowed generated files:

- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260612_engineering_state_package_compact_output_v1/*`

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
- physical deletion or migration of existing project_state files

## 7. Tests

Run and record exact outputs:

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\\reverse-agent"
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_engineering_state_package_compact_output_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

`pytest_result.txt` 必须使用正式 `pytest_result_summary`，记录所有命令 stdout/stderr。`doctor --json` 输出必须是 compact 版本，不能把全部 historical archive entries 全量写入 `pytest_result.txt`。

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `preflight` cannot pass before modifications.
- Compact output would require deleting, physically merging, or migrating core project_state files.
- Compact output would require changing formal `decision_packet` / `codex_execution_report` / `pytest_result` schemas.
- Compact output loses required summary counts or hides current round archive entry.
- `task_packet.json` stops being advisory-only.
- `gates/*.json` stops being classified as derived_cache.
- status/doctor compact classification would require reading full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.
- Existing `preflight` / `command-plan` / `final-check` compatible behavior breaks.
- Fixing this requires implementing automatic `close-round`.
- Fixing this requires touching sample-solving/tooling/training modules.
- Final git status contains scope-out files.
```