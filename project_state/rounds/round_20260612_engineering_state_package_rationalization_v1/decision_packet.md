```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_state_package_rationalization_v1",
  "round_id": "round_20260612_engineering_state_package_rationalization_v1",
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

本轮目标是做 `project_state` 状态包职责收口，降低默认上下文冗余，为后续 `close-round` 设计做前置工程清理。

本轮只做状态包分类与只读诊断输出，不物理合并文件，不删除状态包，不实现自动 `close-round`，不推进样本求解。

必须完成：

1. 在现有工程能力内定义 `project_state` 文件分类，至少包含：
   - `authoritative`：当前执行权威或必须事实源；
   - `advisory`：只提供建议，不能覆盖 decision；
   - `derived_cache`：可由命令重新生成的 gate/cache 产物；
   - `archive`：历史归档，默认不进入上下文；
   - `heavy_history`：重型历史产物，默认不读取。
2. 让 `python -m reverse_agent.project_state status --state-dir project_state` 输出状态包分类摘要。
3. 让 `python -m reverse_agent.project_state doctor --state-dir project_state` 和 `--json` 输出状态包分类检查，明确：
   - `task_packet.json` 是 `advisory`；
   - `decision_packet.md` 是当前执行权威；
   - `gates/*.json` 是 `derived_cache`；
   - `rounds/<round_id>/*` 是 `archive`；
   - `solve_reports/` 和 `PROJECT_PROGRESS_LOG.txt` 默认不是上下文。
4. 保持 `preflight` / `command-plan` / `final-check` 既有行为不削弱。
5. 添加回归测试，确保 `task_packet.json` 不会覆盖 `decision_packet.md`，且状态包分类在 status/doctor 输出中稳定出现。
6. 不改变现有 `decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt` 的正式 schema。

## 2. Current Evidence

- 当前主线是 `engineering_branch`，不是 `reverse_solving`、`tool_integration` 或 `training_dataset`。
- 上一轮 `decision_20260611_engineering_gate_command_plan_audit_hardening_v1` 已有 `SUCCESS` report，`based_on_decision_id` 与上一轮 decision 匹配，`acceptance_recommendation` 为 `ACCEPTED`。
- 上一轮已实现 `final-check` 对 `command_plan.json`、`codex_execution_report.md`、`pytest_result.txt` 的一致性检查，并记录 `220 passed`。
- 当前 `task_packet.json` 仍含旧 `samplereverse` 样本求解上下文和大量 `solve_reports` artifact refs，只能作为 advisory 背景，不能覆盖本轮 decision。
- 当前 `current_state.json` 与 `artifact_index.json` 仍含大量历史样本 artifact；`artifact_index.latest_artifacts_v2` 显示许多 artifact 为 `stale`，另有若干 missing/null 旧字段，不能当 current evidence。
- `negative_results.json` 继续禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 `solve_reports` 等方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active skill profile。
- 现有相关工程能力包括：`project_state status`、`project_state doctor`、`project_state lint-report`、`project_state archive-round`、`project_gate preflight`、`project_gate command-plan`、`project_gate final-check`。
- 本轮不需要 IDA、Ghidra、debugger、solver、harness、runtime probe、sidecar 或训练集接口能力；不得假设这些能力不存在，也不得修改它们。
- 允许读取默认 project_state 文件和 gate 产物；不得读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

## 3. Do Not Do

- 不实现自动 `close-round`。
- 不物理合并、删除或迁移 `task_packet.json`、`current_state.json`、`artifact_index.json`、`negative_results.json`、`decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt`。
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
- `project_state/rounds/round_20260611_engineering_gate_command_plan_audit_hardening_v1/round_manifest.json`

不得默认检查：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- sample binaries

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent` using `Get-Location` or equivalent shell output.
2. Confirm `Test-Path F:\reverse-agent` succeeds and `git status --short` is captured before modification.
3. Read the default project_state files in order:
   - `project_state/task_packet.json`
   - `project_state/current_state.json`
   - `project_state/artifact_index.json`
   - `project_state/negative_results.json`
   - `project_state/codex_execution_report.md`
   - `project_state/decision_packet.md`
   - `project_state/pytest_result.txt`
4. Confirm this packet is the active decision and `status` is `APPROVED`.
5. Run `python -m reverse_agent.project_gate preflight --state-dir project_state` before modification. If it blocks, stop and report.
6. Confirm this is `engineering_branch`, not sample-solving.
7. Inspect existing `status_summary()`, `doctor()`, `lint_report()`, and gate code before implementing classification output.
8. Reuse existing parsing helpers and avoid adding a second independent decision/report parser.
9. Add a small state package classification helper or equivalent structure that can be reused by `status` and `doctor`.
10. Ensure `task_packet.json` is explicitly classified as `advisory` and cannot override `decision_packet.md` in any status/doctor/preflight output.
11. Ensure `gates/preflight_result.json`, `gates/command_plan.json`, and `gates/final_gate_result.json` are described as `derived_cache`, not original facts.
12. Ensure `rounds/<round_id>/*` is described as `archive`, not default context.
13. Ensure any stale/missing artifact summary remains non-blocking for healthy engineering rounds and is not reinterpreted as current sample evidence.
14. Add tests for:
    - status output includes state package classification;
    - doctor JSON includes package classification entries;
    - task_packet is advisory-only;
    - decision_packet remains authoritative even when task_packet suggests an old sample task;
    - gate derived files are marked derived/cache;
    - ordinary existing final-check and preflight behavior remains compatible.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py` only if gate output needs to consume the shared classification helper

Allowed tests:

- `tests/test_project_state.py`
- `tests/test_project_gate.py` only if gate compatibility tests need updates

Allowed generated files:

- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260612_engineering_state_package_rationalization_v1/*`

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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_engineering_state_package_rationalization_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

`pytest_result.txt` 必须使用正式 `pytest_result_summary`，记录所有命令 stdout/stderr。若 `command-plan --json` 被记录，stdout 不得摘要化。

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `preflight` cannot pass before modifications.
- Implementing this requires deleting, physically merging, or migrating core project_state files.
- Implementing this requires changing formal `decision_packet` / `codex_execution_report` / `pytest_result` schemas.
- `task_packet.json` cannot be cleanly represented as advisory-only.
- status/doctor classification would require reading full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.
- Existing `preflight` / `command-plan` / `final-check` compatible behavior breaks.
- Fixing this requires implementing automatic `close-round`.
- Fixing this requires touching sample-solving/tooling/training modules.
- Final git status contains scope-out files.
```