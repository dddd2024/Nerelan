```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_training_metadata_contract_repair_v1",
  "round_id": "round_20260612_training_metadata_contract_repair_v1",
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

本轮目标是修补上一轮本地逆向训练集 inventory/status audit 的 metadata contract 缺口，使 `project_state/local_reverse_training_inventory_audit.md` 明确覆盖训练集长期字段：`solver_used`、`tool_evidence_used`、`failure_reason` / `blocked_reason`，并保持 metadata-only、GitHub-safe、不可伪造未知事实的约束。

本轮只做训练集 metadata contract 文档修补与门禁验证，不运行样本、不运行 IDA/Ghidra/debugger、不执行 solver、不做 runtime probe、不生成 candidate、不推进任何具体逆向题求解。

必须完成：

1. 修改 `project_state/local_reverse_training_inventory_audit.md` 的 “Metadata Contract for Future GitHub-Safe Training Work” 部分，显式补齐以下字段行或等价说明：
   - `solver_used`：仅 solved 样本在已有验证事实中明确时填写；未知时必须标为 unknown / not first-class，不得由 `known_candidate` 反推。
   - `tool_evidence_used`：明确表示 IDA/Ghidra/debugger/static strings/compare contexts/solver hints 等工具证据来源；当前可由 richer local output 的 `evidence_sources` 映射，但字段名必须在 contract 中显式出现。
   - `failure_reason`：表示已尝试路径的失败原因；必须与 `blocked_reason` 区分。`blocked_reason` 表示当前阻塞条件，`failure_reason` 表示历史失败路径，二者不得混用。
2. 保留并强化已存在的 metadata-only 约束：不上传原始样本、不提交二进制、不读取完整 `solve_reports/`、不把 stale/missing artifact 当 current evidence。
3. 保留上一轮审计报告已有事实：inventory 50 entries、全部 `github_upload_policy: metadata_only`、status overlay 为 1 solved / 2 blocked / 1 needs_triage / 46 inventory_only、evaluation queue 为 41 items 且只允许 `static_triage`。
4. 审计报告中必须明确：本轮修补 contract 后，下一轮才可以考虑从 `project_state/local_reverse_evaluation_queue.json` 中选择 exactly one `inventory_only` 样本做静态 triage；本轮不得执行该 triage。
5. 不修改 `reverse_agent/local_reverse_training_status.py`、`reverse_agent/local_reverse_inventory.py`、`reverse_agent/local_reverse_single_sample_static_triage.py`，除非 Codex 发现文档无法准确描述现有行为；若发现这种情况，必须停止并报告 BLOCKED，不要临时改源码扩大范围。
6. 不改变 formal `decision_packet.md` / `codex_execution_report.md` / `pytest_result.txt` schema。

## 2. Current Evidence

- 当前主线为 `training_dataset`。本轮不是 `reverse_solving`，也不是 `tool_integration`；因此不得默认运行 IDA/Ghidra/debugger 或任何目标二进制。
- `task_packet.json` 与 `current_state.json` 仍包含旧 `samplereverse` 求解上下文和大量历史 artifact refs，只能作为 advisory/background，不能覆盖本轮 `decision_packet.md`。
- `artifact_index.json` 中大量 `latest_artifacts_v2` 为 stale/missing 历史样本 artifact；本轮不得把这些 artifact 当 current training evidence。
- `negative_results.json` 继续禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 `solve_reports/`、重复失败 runtime/probe 方向。
- 上一轮 `codex_execution_report.md` 对应 `decision_20260612_training_local_reverse_inventory_audit_v1`，状态 `SUCCESS`，`acceptance_recommendation` 为 `ACCEPTED`。
- 上一轮 `pytest_result.txt` 对应同一 decision/report/round，状态 `PASSED`，记录 `288 passed`，并记录 preflight、command-plan、doctor、final-check、archive-round 等命令。
- 上一轮审计报告 `project_state/local_reverse_training_inventory_audit.md` 已正确记录 inventory/status/queue/tool surface，但 metadata contract 表中没有以原字段名显式列出 `solver_used` 与 `tool_evidence_used`，且 `failure_reason` 与 `blocked_reason` 的区别需要补充。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active skill profile。
- 现有能力检查结论保持不变：已有 `reverse_agent/local_reverse_inventory.py`、`reverse_agent/local_reverse_training_status.py`、`reverse_agent/local_reverse_single_sample_static_triage.py`、`reverse_agent/tool_runners.py`、IDA evidence collector path `reverse_agent/ida_scripts/collect_evidence.py`。本轮只读这些能力，不新增接口，不运行工具。

## 3. Do Not Do

- 不运行本地样本。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、hook、runtime probe 或 sidecar。
- 不运行 solver、candidate search、bruteforce、validation 或 harness。
- 不生成 candidate、flag 或答案。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何具体样本求解。
- 不从 queue 中实际执行 static triage；本轮只允许说明下一轮可选择 exactly one queue item。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不提交原始样本、二进制或完整 `solve_reports/`。
- 不修改 `.codex-skills/`。
- 不修改 source code、tests、project gate、project state schema 或 training status builder。
- 不把未知字段伪造成已知；特别是不得把 `known_candidate` 当作 `solver_used`，不得把 stale artifact 当作 `tool_evidence_used`。
- 不改变 formal report/pytest/decision schema。

## 4. Files To Inspect

必须检查：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `project_state/local_reverse_training_inventory_audit.md`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_evaluation_queue.json`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/tool_runners.py`
- `.codex-skills/registry.json`

必要时只读检查：

- `tests/test_local_reverse_training_status.py`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/rounds/round_20260612_training_local_reverse_inventory_audit_v1/round_manifest.json`

不得默认检查：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- sample binaries
- raw local samples from `E:\reverse` or any other local sample root

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent`.
2. Confirm `Test-Path F:\reverse-agent` succeeds and record actual stdout in `pytest_result.txt`.
3. Capture `git status --short` before modification.
4. Read default project_state files in order:
   - `project_state/task_packet.json`
   - `project_state/current_state.json`
   - `project_state/artifact_index.json`
   - `project_state/negative_results.json`
   - `project_state/codex_execution_report.md`
   - `project_state/decision_packet.md`
   - `project_state/pytest_result.txt`
5. Confirm this packet is active and `status == APPROVED`.
6. Run `python -m reverse_agent.project_gate preflight --state-dir project_state` before modification. If it blocks, stop and report.
7. Confirm this is `training_dataset`, not sample-solving and not tool-integration execution.
8. Inspect `project_state/local_reverse_training_inventory_audit.md` and identify exactly where the metadata contract omits or aliases `solver_used`, `tool_evidence_used`, and `failure_reason`.
9. Inspect `reverse_agent/local_reverse_training_status.py` enough to verify current richer local output has `known_candidate`, `blocked_reason`, `classification`, `evidence_sources`, and `next_action`, but does not make `solver_used` first-class in the compact GitHub overlay.
10. Inspect `training_materials/local_reverse/status_overlay.json` enough to verify compact overlay remains metadata-only and does not include raw sample bytes.
11. Inspect `project_state/local_reverse_evaluation_queue.json` enough to verify future queue action remains exactly one static triage item, while this round executes none.
12. Amend only the audit report contract section, preserving current facts and adding explicit unknown/not-first-class status where needed.
13. Verify no original sample, bulky artifact, source-code change, test-code change, solver change, IDA/Ghidra/debugger change, or `.codex-skills/` change is present.
14. Write a formal `codex_execution_report.md` with `codex_report_summary` for this decision and real `tests_ran`.
15. Write `pytest_result.txt` with real stdout/stderr/exit code for every required command.
16. Archive the round after report/tests are written.

## 6. Implementation Scope

Allowed documentation file:

- `project_state/local_reverse_training_inventory_audit.md`

Allowed generated/state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_training_metadata_contract_repair_v1/*`

Allowed source files:

- None.

Allowed test files:

- None.

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_training_status.json`
- sample binaries
- raw local samples
- solver modules
- IDA/Ghidra/debugger/runtime/probe modules
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- tests

If Codex finds checked-in metadata is stale, it must not refresh metadata in this round. It should document the staleness and stop with `BLOCKED` if the contract cannot be repaired safely from existing files.

## 7. Tests

Run and record exact outputs:

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\\reverse-agent"
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_local_reverse_training_status.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_training_metadata_contract_repair_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

`pytest_result.txt` must record real stdout/stderr/exit code for every listed command. Placeholder stdout/stderr is forbidden.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- preflight cannot pass before modification.
- `project_state/local_reverse_training_inventory_audit.md` is missing.
- the active decision is not this packet or `status != APPROVED`.
- `.codex-skills/registry.json` does not mark the declared skill profiles active.
- repairing the contract requires source code or schema changes.
- Codex needs to inspect raw sample binaries, run IDA/Ghidra/debugger, run target binaries, or read full `solve_reports/` to proceed.
- any source/test/tool/schema file must be changed to complete the work.
- `pytest_result.txt` cannot record real command outputs.
- report/decision/pytest round IDs do not match.
- final-check fails after the round is archived.
