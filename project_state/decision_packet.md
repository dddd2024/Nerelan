```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_close_round_design_only_v1",
  "round_id": "round_20260612_engineering_close_round_design_only_v1",
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

本轮目标是做自动 `close-round` 的设计-only 收口，为后续最小实现轮提供稳定边界、接口契约和测试矩阵。

本轮必须只产出设计文档，不实现 `close-round` 命令，不修改状态机执行逻辑，不新增实际归档自动化流程，不推进样本求解。

必须完成：

1. 新增或更新 `project_state/close_round_design.md`，作为当前 `close-round` 设计文档。
2. 设计文档必须定义 `close-round` 的职责边界：
   - 只在所有前置条件满足时做 round 收口；
   - 不生成下一轮 decision；
   - 不修改 `decision_packet.md`；
   - 不执行 command plan；
   - 不运行 pytest；
   - 不运行 solver/sample/tooling；
   - 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
3. 设计文档必须给出拟议 CLI contract，至少包括：
   - `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id <round_id>`；
   - `--json` 行为；
   - 退出码策略；
   - 输出 JSON 字段草案。
4. 设计文档必须给出 close-round 前置条件清单，至少覆盖：
   - `decision_meta` 存在且 `status == APPROVED`；
   - `codex_report_summary` 存在；
   - `report.based_on_decision_id == decision.decision_id`；
   - `report.round_id == decision.round_id == --round-id`；
   - `pytest_result_summary` 与 report 匹配；
   - `command_plan` 一致性 checks PASS；
   - `final-check` 可 PASS；
   - `files_changed` 覆盖 git diff；
   - forbidden paths absent；
   - compact state package classification 不全量展开历史 archives。
5. 设计文档必须给出 close-round 执行动作边界，限定为：
   - 验证前置条件；
   - 调用或复用现有 `archive-round` 能力；
   - 重新运行或复用 `final-check`；
   - 写入/更新 `project_state/gates/final_gate_result.json`；
   - 返回结构化结果。
6. 设计文档必须给出 failure modes 与 stop conditions，说明何时不得 close。
7. 设计文档必须给出测试矩阵，区分 design 后续最小实现需要的成功路径、失败路径、兼容路径。
8. 设计文档必须给出从 design-only 到 minimal implementation 的下一轮建议，但不得在本轮实现。
9. 保持现有 `preflight` / `command-plan` / `final-check` 行为不变。
10. 不改变现有 `decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt` 的正式 schema。

## 2. Current Evidence

- 当前主线是 `engineering_branch`，不是 `reverse_solving`、`tool_integration` 或 `training_dataset`。
- 上一轮 `decision_20260612_engineering_state_package_compact_output_v1` 已有 `SUCCESS` report，`based_on_decision_id` 与上一轮 decision 匹配，`acceptance_recommendation` 为 `ACCEPTED`。
- 上一轮测试记录显示 `227 passed`，并已记录 `pwd`、`Test-Path F:\reverse-agent`、`git rev-parse --show-toplevel`、`git status --short`、`preflight`、`command-plan`、`status`、`doctor`、`final-check`、`archive-round`、archive 后 `final-check`。
- 上一轮 `doctor --json` 已 compact：`entries_compacted=true`，`archive_total_count=111`，`archive_included_count=1`，`archive_omitted_count=110`，默认不再全量展开历史 archive entries。
- 当前 `task_packet.json` 与 `current_state.json` 仍含旧 `samplereverse` 样本求解上下文和大量 `solve_reports` artifact refs，只能作为 advisory/background，不能覆盖本轮 decision。
- 当前 `artifact_index.json` 仍含大量 stale/missing 历史样本 artifact；本轮不得把它们当 current evidence。
- `negative_results.json` 继续禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 `solve_reports` 等方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active skill profile。
- 现有相关工程能力包括：`project_state status`、`project_state doctor`、`project_state lint-report`、`project_state archive-round`、`project_gate preflight`、`project_gate command-plan`、`project_gate final-check`。
- 本轮是 close-round 设计，不需要 IDA、Ghidra、debugger、solver、harness、runtime probe、sidecar 或训练集接口能力；不得假设这些能力不存在，也不得修改它们。
- 允许读取默认 project_state 文件、gate 产物、当前 round manifest、相关 project_state/project_gate 代码与测试；不得读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

## 3. Do Not Do

- 不实现 `close-round` 命令。
- 不新增实际 CLI 子命令。
- 不修改 `archive-round` 的执行逻辑。
- 不修改 `final-check` / `preflight` / `command-plan` 的现有行为。
- 不新增自动执行 command plan 的能力。
- 不自动生成下一轮 decision。
- 不修改 `decision_packet.md` 的 schema。
- 不修改 `codex_execution_report.md` 的 schema。
- 不修改 `pytest_result.txt` 的 schema。
- 不物理合并、删除或迁移 project_state 核心文件。
- 不删除或压缩实际 `project_state/rounds/` 历史归档文件。
- 不新增数据库、队列、workflow engine 或重型状态管理层。
- 不把 `.codex-skills/` 当动态状态写入目标。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不运行样本二进制。
- 不运行 solver、candidate search、runtime probe、debugger、hook、emulator、sidecar。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何具体样本求解。
- 不修改训练集状态、训练样本 inventory、IDA/Ghidra/debugger/runtime/probe 模块。
- 不把 stale/missing artifact 当 current evidence。

## 4. Files To Inspect

必须检查：

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
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
- 当前 report round 的 `project_state/rounds/round_20260612_engineering_state_package_compact_output_v1/round_manifest.json`

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
8. Inspect existing `archive_round`, `final_check`, `preflight`, `command_plan`, `status_summary`, `doctor`, and compact state package classification before writing the design.
9. Inspect existing tests only to design the future test matrix; do not add implementation tests unless required for a documentation-only invariant.
10. Verify `task_packet.json` remains advisory-only in the design and cannot override `decision_packet.md`.
11. Verify `gates/*.json` remain treated as derived_cache in the design.
12. Verify historical `rounds/<round_id>/*` remain archive, not current execution authority.
13. Verify stale/missing sample artifacts remain non-blocking for healthy engineering rounds and are not reinterpreted as current sample evidence.
14. Ensure the design explicitly references existing capabilities instead of inventing parallel parsers or duplicate gate logic.
15. Ensure the design does not require reading full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

## 6. Implementation Scope

Allowed design artifact:

- `project_state/close_round_design.md`

Allowed source files:

- None by default. Do not modify source code in this design-only round.

Allowed tests:

- None by default. Do not modify tests in this design-only round.

Allowed generated files:

- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260612_engineering_close_round_design_only_v1/*`

Disallowed:

- `reverse_agent/project_state.py` modifications
- `reverse_agent/project_gate.py` modifications
- `tests/test_project_state.py` modifications
- `tests/test_project_gate.py` modifications
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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_engineering_close_round_design_only_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

`pytest_result.txt` 必须使用正式 `pytest_result_summary`，记录所有命令 stdout/stderr。`doctor --json` 输出必须保持 compact，不得全量写入 historical archive entries。

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `preflight` cannot pass before modifications.
- A credible close-round design would require immediate source-code implementation.
- A credible close-round design would require changing formal `decision_packet` / `codex_execution_report` / `pytest_result` schemas.
- The design would require executing command plan automatically.
- The design would require running pytest automatically inside close-round.
- The design would require generating the next decision automatically.
- The design would require reading full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.
- The design would require deleting, merging, or migrating core project_state files.
- The design would require touching sample-solving/tooling/training modules.
- Existing `preflight` / `command-plan` / `final-check` compatible behavior breaks.
- Final git status contains scope-out files.
```