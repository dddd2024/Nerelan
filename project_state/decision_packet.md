```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_close_round_contract_rework_v1",
  "round_id": "round_20260612_engineering_close_round_contract_rework_v1",
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

修复 `close-round` 最小实现的 contract 缺口，使其输出、exit code 和测试覆盖完全匹配上一轮设计与 implementation decision。

必须完成：

1. 在 `close_round(...)` 返回 payload 中新增 `archive` 字段。
2. `archive` 至少包含：
   - `status`；
   - `round_manifest_path`；
   - `files`；
   - `included_diff`；
   - `included_state_snapshot`；
   - `copied`；
   - `idempotent`。
3. 实现或明确封装 close-round CLI exit code：
   - `0`：`CLOSED`；
   - `1`：policy/precondition/final-check/archive failure；
   - `2`：usage error、invalid state-dir、invalid round-id、critical malformed metadata。
4. 增加 close-round 专属测试：abbreviated `command-plan --json` stdout 必须导致 close-round FAIL。
5. 保持现有 `preflight`、`command-plan`、`final-check`、`archive-round` 行为不变。
6. 不改 formal `decision_packet` / `codex_execution_report` / `pytest_result` schema。
7. 当前 live round 仍用现有 `archive-round + final-check` 收口，不用 `close-round` 关闭自身。
8. `pytest_result.txt` 必须记录所有 listed commands 的真实 stdout/stderr，不得使用占位文本。

## 2. Current Evidence

- 当前主线是 `engineering_branch`。
- 上一轮 `decision_20260612_engineering_close_round_minimal_implementation_v1` 已有 `SUCCESS` report，`based_on_decision_id` 与 decision 匹配，`acceptance_recommendation` 为 `ACCEPTED`。
- 上一轮已实现 `project_gate close-round` CLI，并添加了 focused tests，pytest 为 `240 passed`。
- 上一轮 final-check 已 PASSED，且当前 round 使用现有 `archive-round + final-check` 完成归档，没有用新 `close-round` 关闭自身。
- 审计结论为 `REWORK_REQUIRED`，原因集中在三个 contract 缺口：
  1. `close_round(...)` 返回 payload 缺少 decision 要求的 `archive` 字段；
  2. close-round exit code 目前只有 `CLOSED -> 0`，否则 `1`，未覆盖要求的 `2`；
  3. 缺少 close-round 专属 abbreviated `command-plan --json` stdout failure test。
- 当前 `task_packet.json` 与 `current_state.json` 仍含旧 `samplereverse` 样本求解上下文和大量 `solve_reports` artifact refs，只能作为 advisory/background，不能覆盖本轮 decision。
- 当前 `artifact_index.json` 仍含大量 stale/missing 历史样本 artifact；本轮不得把它们当 current evidence。
- `negative_results.json` 继续禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 `solve_reports` 等方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active skill profile。
- 本轮不需要 IDA、Ghidra、debugger、solver、harness、runtime probe、sidecar 或训练集接口能力；不得修改它们。

## 3. Do Not Do

- 不重写 gate 系统。
- 不改变 formal schema。
- 不执行 command plan。
- 不让 close-round 运行 pytest。
- 不生成下一轮 decision。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不运行样本二进制。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何具体样本求解。
- 不修改 solver、IDA/Ghidra/debugger、runtime/probe、training 模块。
- 不把 stale/missing artifact 当 current evidence。
- 不删除、合并、压缩或迁移 project_state 核心文件。
- 不删除或压缩实际 `project_state/rounds/` 历史归档文件。
- 不用占位文本代替命令真实 stdout/stderr。

## 4. Files To Inspect

必须检查：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `project_state/close_round_design.md`
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

- `reverse_agent/project_state.py` only if a small helper is required;
- `.codex-skills/registry.json`;
- 当前 report round 的 `project_state/rounds/round_20260612_engineering_close_round_minimal_implementation_v1/round_manifest.json`。

不得默认检查：

- 完整 `solve_reports/`；
- 完整 `PROJECT_PROGRESS_LOG.txt`；
- sample binaries。

## 5. Required Audit

Codex must:

1. Confirm working directory is `F:\reverse-agent`.
2. Confirm `Test-Path F:\reverse-agent` succeeds and record actual stdout in `pytest_result.txt`.
3. Capture `git status --short` before modification.
4. Read the default project_state files in order:
   - `project_state/task_packet.json`
   - `project_state/current_state.json`
   - `project_state/artifact_index.json`
   - `project_state/negative_results.json`
   - `project_state/codex_execution_report.md`
   - `project_state/decision_packet.md`
   - `project_state/pytest_result.txt`
5. Confirm this packet is active and `status == APPROVED`.
6. Run `python -m reverse_agent.project_gate preflight --state-dir project_state` before modification. If it blocks, stop and report.
7. Inspect existing `close_round`, `_close_round_exit_code`, `final_check`, `archive_round`, command-plan consistency helpers, and tests before modifying.
8. Avoid adding a second decision/report/pytest/command-plan parser.
9. Add only focused tests for the missing contract behavior.
10. Ensure `task_packet.json` remains advisory-only and cannot override `decision_packet.md`.
11. Ensure `gates/*.json` remain derived_cache and historical `rounds/<round_id>/*` remain archive.
12. Ensure `doctor --json` compact output does not regress by expanding all historical archives.
13. Ensure every command listed in `pytest_result_summary.tests_ran` has a real command block with actual stdout/stderr and exit code.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if a small reusable helper is necessary

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if `project_state.py` helper behavior changes

Allowed generated files:

- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/*`

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
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate close-round --help
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_engineering_close_round_contract_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

Additional focused pytest requirements:

- `close_round(...)` JSON/result payload includes `archive` with stable keys.
- `close_round(...)` fails when `command-plan --json` recorded stdout is abbreviated.
- `_close_round_exit_code` or equivalent returns `2` for CLI usage / critical metadata errors if that status is represented in result payload.
- Existing close-round success, idempotent, report/pytest/command-plan/forbidden path/archive drift tests remain passing.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- preflight cannot pass before modification.
- fixing this requires schema changes.
- fixing this requires running command plan inside close-round.
- fixing this requires running pytest inside close-round.
- fixing this requires generating the next decision automatically.
- fixing this requires reading full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.
- fixing this requires touching solver/tooling/training/sample files.
- existing `preflight` / `command-plan` / `final-check` compatible behavior breaks.
- `doctor --json` compact output regresses by expanding historical archives.
- `pytest_result.txt` uses placeholder stdout/stderr.
- final git status contains scope-out files.
```