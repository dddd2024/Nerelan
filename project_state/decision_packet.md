```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_engineering_close_round_minimal_implementation_v1",
  "round_id": "round_20260612_engineering_close_round_minimal_implementation_v1",
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

本轮目标是实现 `close-round` 的最小可测试版本：在 `project_gate` 中增加 `close-round` CLI 与对应函数，复用现有 decision/report/pytest/command-plan/final-check/archive-round 能力完成 round 收口。

本轮不是重构状态系统，不改变正式 schema，不自动生成下一轮 decision，不执行 command plan，不运行样本求解。

必须完成：

1. 在 `reverse_agent/project_gate.py` 中新增最小 `close_round(...)` 函数和 CLI 子命令：
   - `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id <round_id>`；
   - `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id <round_id> --json`。
2. `close-round` 必须复用现有能力，不新增平行解析器：
   - 复用 `read_decision_meta` / `read_codex_report_summary` / `validate_pytest_result_for_report`；
   - 复用现有 command-plan consistency helper；
   - 复用 `final_check`；
   - 复用 `archive_round`。
3. `close-round` 前置条件必须至少检查：
   - `decision_meta` 存在且 `status == APPROVED`；
   - `decision.round_id == --round-id`；
   - `codex_report_summary` 存在；
   - `report.based_on_decision_id == decision.decision_id`；
   - `report.round_id == decision.round_id == --round-id`；
   - `pytest_result_summary` 与 report 匹配；
   - `pytest_result_summary.tests_ran` 覆盖 `codex_report_summary.tests_ran`；
   - 若 report/tests 记录 command-plan，则 `project_state/gates/command_plan.json` 存在、`plan_status == PASSED`、decision/round 匹配、覆盖 report/pytest commands、recorded command exit codes 符合 `expected_exit_codes`；
   - `final-check` 可通过；
   - forbidden paths absent；
   - compact state package classification 不全量展开 historical archive entries。
4. `close-round` 执行动作必须限制为：
   - 验证前置条件；
   - 调用 `final_check` 进行 archive 前检查；
   - 若 round 尚未归档，调用 `archive_round(state_dir=..., round_id=...)`，不得包含 state snapshot 或 git diff；
   - 若 round 已归档，只允许 idempotent close；若已有 archive 与当前 live report/pytest/decision 不一致，必须失败；
   - 归档后再次调用 `final_check`；
   - 写入/更新 `project_state/gates/final_gate_result.json`；
   - 返回结构化结果。
5. `close-round` 输出：
   - text mode 输出 `close-round: CLOSED|BLOCKED|FAILED`、decision/report/round ids、checks、actions、recommended_next_action；
   - json mode 输出结构化 payload，至少含 `schema_version`、`gate_name`、`close_status`、`decision_id`、`report_id`、`round_id`、`checks`、`actions`、`archive`、`blocking_reasons`、`warnings`、`recommended_next_action`。
6. 退出码：
   - `0`：closed 或 idempotent already-closed；
   - `1`：前置条件不满足、final-check 失败、archive 不一致、禁止路径等 policy failure；
   - `2`：CLI usage error、无效 state-dir/round-id、关键 metadata 无法读取或严重 malformed。
7. 添加聚焦测试，覆盖成功、失败和兼容路径。
8. 本轮实现 `close-round`，但当前 round 的归档仍使用现有 `archive-round + final-check` 流程完成；不要强行用刚实现的 `close-round` 关闭本轮自身，避免 close-round 命令验证自己的尚未记录 stdout 造成自引用问题。
9. `pytest_result.txt` 必须记录所有 listed commands 的真实 stdout/stderr，不得再使用 `Recorded in closeout run; command exited 0.` 这类占位文本替代实际输出。
10. 不改变现有 `decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt` 正式 schema。

## 2. Current Evidence

- 当前主线是 `engineering_branch`，不是 `reverse_solving`、`tool_integration` 或 `training_dataset`。
- 上一轮 `decision_20260612_engineering_close_round_design_only_v1` 已有 `SUCCESS` report，`based_on_decision_id` 与上一轮 decision 匹配，`acceptance_recommendation` 为 `ACCEPTED`。
- 上一轮新增 `project_state/close_round_design.md`，没有修改源码或测试，设计已定义 close-round 作为 thin closeout coordinator。
- 上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`：设计文档本身可接受，但 `pytest_result.txt` 后半部分使用了 `Recorded in closeout run; command exited 0.` 占位输出，没有记录真实 stdout/stderr。
- 上一轮测试记录显示 `227 passed`，`preflight`、`command-plan`、`final-check`、`archive-round` 均 exit 0。
- 当前 `task_packet.json` 与 `current_state.json` 仍含旧 `samplereverse` 样本求解上下文和大量 `solve_reports` artifact refs，只能作为 advisory/background，不能覆盖本轮 decision。
- 当前 `artifact_index.json` 仍含大量 stale/missing 历史样本 artifact；本轮不得把它们当 current evidence。
- `negative_results.json` 继续禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 `solve_reports` 等方向。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active skill profile。
- 现有相关工程能力包括：`project_state status`、`project_state doctor`、`project_state lint-report`、`project_state archive-round`、`project_gate preflight`、`project_gate command-plan`、`project_gate final-check`、compact state package classification。
- 本轮需要检查已有 `archive_round`、`final_check`、command-plan consistency、round archive consistency、status/doctor compact output；不得假设这些能力不存在，不得重复实现成熟逻辑。
- 本轮不需要 IDA、Ghidra、debugger、solver、harness、runtime probe、sidecar 或训练集接口能力；不得修改它们。
- 允许读取默认 project_state 文件、gate 产物、当前 round manifest、`project_state/close_round_design.md`、相关 project_state/project_gate 代码与测试；不得读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

## 3. Do Not Do

- 不自动生成下一轮 decision。
- 不执行 command plan。
- 不让 close-round 运行 pytest。
- 不让 close-round 运行 solver、sample、runtime probe、debugger、hook、emulator、sidecar。
- 不修改 `decision_packet.md` schema。
- 不修改 `codex_execution_report.md` schema。
- 不修改 `pytest_result.txt` schema。
- 不新增数据库、队列、workflow engine 或重型状态管理层。
- 不把 `.codex-skills/` 当动态状态写入目标。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不运行样本二进制。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何具体样本求解。
- 不修改训练集状态、训练样本 inventory、IDA/Ghidra/debugger/runtime/probe 模块。
- 不把 stale/missing artifact 当 current evidence。
- 不删除、合并、压缩或迁移 project_state 核心文件。
- 不删除或压缩实际 `project_state/rounds/` 历史归档文件。
- 不用占位文本代替命令真实 stdout/stderr。

## 4. Files To Inspect

必须检查：

- `project_state/close_round_design.md`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
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
- 当前 report round 的 `project_state/rounds/round_20260612_engineering_close_round_design_only_v1/round_manifest.json`

不得默认检查：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- sample binaries

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent` using `Get-Location` or equivalent shell output.
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
5. Confirm this packet is the active decision and `status` is `APPROVED`.
6. Run `python -m reverse_agent.project_gate preflight --state-dir project_state` before modification. If it blocks, stop and report.
7. Confirm this is `engineering_branch`, not sample-solving.
8. Inspect `project_state/close_round_design.md` before implementation.
9. Inspect existing `archive_round`, `classify_round_archive`, `build_round_consistency`, `final_check`, command-plan consistency helpers, `preflight`, `command_plan`, `status_summary`, `doctor`, and compact state package classification before coding.
10. Reuse existing parsers and helpers. Do not add a second independent decision/report/pytest/command-plan parser.
11. Add tests for close-round success path, failure paths, idempotent already-closed path, and compatibility with existing gates.
12. Ensure `task_packet.json` remains advisory-only and cannot override `decision_packet.md`.
13. Ensure `gates/*.json` remain treated as derived_cache.
14. Ensure historical `rounds/<round_id>/*` remain archive, not current execution authority.
15. Ensure stale/missing sample artifacts remain non-blocking for healthy engineering rounds and are not reinterpreted as current sample evidence.
16. Ensure compact `doctor --json` output remains compact and does not expand historical archives.
17. Ensure all commands listed in `pytest_result_summary.tests_ran` have real command blocks with actual stdout/stderr and exit code. Do not write placeholder blocks.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if a small reusable helper is necessary for round archive consistency or metadata reuse

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if `project_state.py` helper behavior changes

Allowed generated files:

- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260612_engineering_close_round_minimal_implementation_v1/*`

Allowed documentation:

- `project_state/close_round_design.md` only if the implemented minimal CLI contract differs from the design and the difference must be documented

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

Run and record exact outputs. Every listed command must have a real command block with actual stdout/stderr and exit code in `pytest_result.txt`; placeholder lines such as `Recorded in closeout run; command exited 0.` are forbidden.

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\\reverse-agent"
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate close-round --help
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_engineering_close_round_minimal_implementation_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

Important testing note:

- Do not use the newly implemented `close-round` command to close this same live round. This round should still be closed with the existing `archive-round + final-check` flow to avoid a self-reference problem where `close-round` would need to validate its own not-yet-recorded stdout.
- Functional behavior of `close-round` must be tested through focused pytest temp-state tests in `tests/test_project_gate.py`.
- `command-plan --json` stdout must contain the full commands array, not an abbreviated string.
- `doctor --json` output must remain compact and must not expand all historical archive entries.

Required pytest coverage:

- close-round closes a healthy temp round with matching decision/report/pytest ids.
- close-round returns idempotent success for already archived identical temp round.
- close-round fails on missing or non-APPROVED decision.
- close-round fails on `--round-id` mismatch.
- close-round fails on missing or mismatched report.
- close-round fails on mismatched pytest_result.
- close-round fails when command_plan is required but missing or mismatched.
- close-round fails when recorded command exits do not match expected exit codes.
- close-round fails when command-plan --json recorded stdout is abbreviated.
- close-round fails when forbidden paths appear.
- close-round fails when existing archive manifest differs.
- existing preflight, command-plan, final-check, status, doctor, and archive-round behavior remains compatible.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `preflight` cannot pass before modifications.
- Implementing close-round requires changing formal `decision_packet` / `codex_execution_report` / `pytest_result` schemas.
- Implementing close-round requires executing command plan automatically.
- Implementing close-round requires running pytest automatically inside close-round.
- Implementing close-round requires generating the next decision automatically.
- Implementing close-round requires reading full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.
- Implementing close-round requires deleting, merging, or migrating core project_state files.
- Implementing close-round requires touching sample-solving/tooling/training modules.
- Existing `preflight` / `command-plan` / `final-check` compatible behavior breaks.
- `doctor --json` compact output regresses by expanding historical archives.
- `pytest_result.txt` uses placeholder stdout/stderr for any listed command.
- Functional close-round tests cannot be implemented without scope expansion.
- Final git status contains scope-out files.
```