```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_training_local_reverse_inventory_audit_v1",
  "round_id": "round_20260612_training_local_reverse_inventory_audit_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮目标是从工程门禁主线切回训练集主线，对本地逆向训练集做一次有界 inventory/status audit，明确当前训练材料、状态覆盖、队列优先级和元数据缺口，为下一轮小规模样本 triage 或工具接入提供可靠入口。

本轮只做训练集 metadata 审计和计划收口，不批量跑样本、不执行 solver、不运行 runtime probe、不动态调试、不生成 candidate、不写入长期 skill。

必须完成：

1. 新增 `project_state/local_reverse_training_inventory_audit.md`，作为当前训练集审计报告。
2. 审计报告必须基于现有训练集能力，而不是新建第三套扫描器：
   - `reverse_agent/local_reverse_inventory.py`；
   - `reverse_agent/local_reverse_training_status.py`；
   - `reverse_agent/local_reverse_single_sample_static_triage.py`；
   - `training_materials/local_reverse/inventory.json`；
   - `training_materials/local_reverse/status_overlay.json`。
3. 审计报告必须说明当前 inventory/status 事实：
   - inventory 是否是 metadata-only，不上传原始样本；
   - status overlay 的 sample_count、solved、blocked、needs_triage、inventory_only；
   - 哪些条目已经有 solved/blocked/needs_triage 状态；
   - evaluation queue 是否只应包含未解决样本；
   - solver script / support file 是否应被排除出优先评估队列。
4. 审计报告必须定义下一步训练集 metadata contract，至少包含字段：
   - `sample_id`；
   - `display_name`；
   - `relative_path`；
   - `sha256`；
   - `size_bytes`；
   - `extension`；
   - `guessed_file_type`；
   - `platform`；
   - `architecture`；
   - `category`；
   - `tags`；
   - `expected_input` / `expected_output` when known；
   - `training_status`；
   - `solver_used` when solved；
   - `tool_evidence_used`；
   - `run_history`；
   - `failure_reason` / `blocked_reason`；
   - `github_upload_policy`。
5. 审计报告必须区分现有事实与缺口，不得把未知字段伪造成已知。
6. 审计报告必须给出下一轮可执行的小步建议，优先级应是：
   - 先补 metadata audit/helper 或 status overlay 字段；
   - 再做单样本静态 triage；
   - 最后才考虑 solver/验证。
7. 若建议下一轮做单样本 triage，必须限定为从 queue 中选择 1 个 `inventory_only` 或 `needs_triage` 样本，并且仅允许静态 triage，不能运行目标二进制。
8. 明确检查已有 IDA/Ghidra/debugger/solver/harness 能力：
   - 已有 IDA 静态 triage 适配器；
   - 已有 `tool_runners` / `collect_evidence.py` 复用路径；
   - 本轮不新增 IDA/Ghidra/debugger 接口；
   - 本轮不重复实现成熟工具能力。
9. 保持现有 `preflight`、`command-plan`、`final-check`、`close-round` 行为不变。
10. 不改变 formal `decision_packet.md` / `codex_execution_report.md` / `pytest_result.txt` schema。

## 2. Current Evidence

- 当前主线切换为 `training_dataset`，不是 `engineering_branch`、`reverse_solving` 或 `tool_integration`。
- 上一轮 `decision_20260612_engineering_close_round_contract_rework_v1` 已有 `SUCCESS` report，`based_on_decision_id` 与 decision 匹配，`acceptance_recommendation` 为 `ACCEPTED`。
- 上一轮 pytest 为 `243 passed`，`final-check` PASSED，round 已归档；工程门禁/收口体系可以视为基本建立完毕。
- 当前 `task_packet.json` 与 `current_state.json` 仍含旧 `samplereverse` 样本求解上下文和大量 `solve_reports` artifact refs，只能作为 advisory/background，不能覆盖本轮 decision。
- 当前 `artifact_index.json` 仍含大量 stale/missing 历史样本 artifact；本轮不得把它们当 current training evidence。
- `negative_results.json` 继续禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 `solve_reports` 等方向。
- 现有训练集 inventory 已存在：`training_materials/local_reverse/inventory.json`，其策略是 metadata-only。
- 现有训练集 status overlay 已存在：`training_materials/local_reverse/status_overlay.json`，当前显示 `sample_count=50`，`solved=1`，`blocked=2`，`needs_triage=1`，`inventory_only=46`。
- `reverse_agent/local_reverse_training_status.py` 已能合并 inventory、validated handoff、constraint recovery、IDA solver result、artifact_index overlays，并生成 training status 与 evaluation queue。
- `reverse_agent/local_reverse_single_sample_static_triage.py` 已声明复用 IDA static evidence collection，不执行目标二进制，不生成 candidate。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active skill profile。
- 本轮允许检查工具能力接口，但不得运行 IDA/Ghidra/debugger/runtime probe，不得批量跑样本。

## 3. Do Not Do

- 不批量运行本地样本。
- 不运行目标二进制。
- 不运行 solver、candidate search、runtime probe、debugger、hook、emulator、sidecar。
- 不生成 candidate、flag 或答案。
- 不把旧 `samplereverse` artifact 当 current training evidence。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不提交原始样本或二进制。
- 不提交完整 `solve_reports/`。
- 不把单次样本结论写入 `.codex-skills/`。
- 不新增第三套训练集扫描器。
- 不重复实现 IDA/Ghidra/debugger/solver/harness 已有能力。
- 不修改 `preflight` / `command-plan` / `final-check` / `close-round` 行为。
- 不改变 formal report/pytest/decision schema。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何具体样本求解。

## 4. Files To Inspect

必须检查：

- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `tests/test_local_reverse_training_status.py`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/status_overlay.json`
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

必须做能力检查但默认只读：

- `reverse_agent/tool_runners.py`
- existing IDA evidence collection / `collect_evidence.py` path referenced by local static triage
- existing solver / validation / harness entry points at a high level only

必要时检查：

- `.codex-skills/registry.json`
- `project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/round_manifest.json`

不得默认检查：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- sample binaries

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent`.
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
7. Confirm this is `training_dataset`, not sample-solving.
8. Inspect existing inventory/status/static-triage modules before writing the audit report.
9. Inspect existing tests for training status before deciding whether tests need modification.
10. Check existing IDA/Ghidra/debugger/solver/harness/tool capability interfaces; document what exists and what is not used this round.
11. Verify `task_packet.json` remains advisory-only and cannot override `decision_packet.md`.
12. Verify `gates/*.json` remain derived_cache and historical `rounds/<round_id>/*` remain archive.
13. Verify stale/missing sample artifacts remain non-blocking background and are not used as current training evidence.
14. Ensure audit report distinguishes known metadata from missing metadata.
15. Ensure no original samples or bulky local artifacts are committed.

## 6. Implementation Scope

Allowed documentation artifact:

- `project_state/local_reverse_training_inventory_audit.md`

Allowed source files:

- None by default. Do not modify source code in this audit-only round.

Allowed tests:

- None by default. Do not modify tests in this audit-only round.

Allowed generated files:

- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260612_training_local_reverse_inventory_audit_v1/*`

Allowed only if Codex finds the checked-in metadata is stale and can refresh metadata-only outputs without touching samples:

- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- sample binaries
- raw local samples from `E:\reverse` or any other local sample root
- solver modules
- IDA/Ghidra/debugger/runtime/probe modules
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- physical deletion or migration of project_state core files

## 7. Tests

Run and record exact outputs:

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\\reverse-agent"
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_training_local_reverse_inventory_audit_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

`pytest_result.txt` must record real stdout/stderr/exit code for every listed command. Placeholder stdout/stderr is forbidden.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- preflight cannot pass before modification.
- current inventory/status files are missing and cannot be inspected.
- doing a credible audit would require reading full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.
- doing a credible audit would require running samples, solver, debugger, runtime probe, hook, emulator, or sidecar.
- doing a credible audit would require committing raw sample binaries.
- doing a credible audit would require modifying gate/source/test code outside this decision scope.
- audit report cannot distinguish known metadata from unknown metadata.
- final git status contains scope-out files.
- `pytest_result.txt` uses placeholder stdout/stderr.
```