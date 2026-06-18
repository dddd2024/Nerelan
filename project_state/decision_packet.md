```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_static_type_tag_contract_scope_repair_v1",
  "round_id": "round_20260618_static_type_tag_contract_scope_repair_v1",
  "based_on_state_build_id": "state_20260618_114539_14d4ec94f06b",
  "based_on_state_digest": "14d4ec94f06bab113eb55fdf774e82b449b2851672e927f2b0df7a6052a95cc2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复上一轮 `static_triage_type_tag_contract_v1` 的 scope 问题，并继续推进训练集静态题型标签契约。

上一轮被 preflight 阻断，原因是 Implementation Scope 允许修改 `reverse_agent/local_reverse_single_sample_static_triage.py`，该文件在当前 gate 规则下属于 forbidden path；`training_dataset` 主线当前不允许修改该路径。本轮返工目标是收窄范围：只生成 project_state contract artifact 和 synthetic/unit tests，不修改 static triage 主入口、evidence、tool runner、solver、harness 或 gate 源码。

目标产物：

1. `project_state/local_reverse_static_type_tag_contract.json`
2. `project_state/local_reverse_static_type_tag_contract_report.md`
3. `tests/test_local_reverse_static_type_tags.py`

本轮只定义 schema/contract 与合约一致性测试，不运行样本，不运行逆向工具，不批量 backfill inventory，不声称任何 metadata-level 类别已经 static-verified 或 solved。

## 2. Current Evidence

主线是 `training_dataset`。

上一轮 `decision_20260618_static_triage_type_tag_contract_v1` 当前状态为 `BLOCKED`：preflight 在 `forbidden_paths_not_allowed` 处失败；Implementation Scope 未开始；tests 未运行；type-tag contract artifacts 未创建。

上一轮阻塞根因是 decision scope 过宽，而不是 Codex 执行错误。本轮必须移除 forbidden source paths，只保留 project_state artifact 与 tests 范围。

已有训练集事实来自上一轮已接受的 coverage matrix/gap report：local project_state inventory 有 65 个 metadata-only entries；read-only builder status 为 solved=1、blocked=2、needs_triage=0、inventory_only=62；coverage matrix 覆盖 string comparison、XOR、shift/affine、bit operations、lookup table、RC4、DES、TEA/XTEA、Base64、hash/MD5/SHA、GUI、simple anti-debug、mixed/unknown；多数类别仍是 metadata/source-audit level。

已有能力检查必须以当前 project_state 产物和 capability map 为依据，优先复用既有 sample metadata、inventory/status overlay、evaluation queue、solver/tool capability map、StructuredEvidence/tool-output 能力描述；不得重复实现成熟工具能力。

`task_packet.json` 仍保留旧 sample_state/reverse-solving 建议；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`negative_results.json` 中禁止方向继续有效：旧 sample_solver blind search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports 等均不得触碰。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner 或 GUI/frontend workflow。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要读取或提交完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要修改任何 `reverse_agent/` 源码文件。

不要修改 solver、harness、tool runner、evidence、static triage、project gate 主逻辑。

不要把文件名启发式或 metadata-level hint 声称为 current static evidence。

不要批量 backfill inventory type tags。

不要把任何单次样本 candidate、flag、本地绝对路径或 runtime metric 写入长期 skill 或 project_state contract。

## 4. Files To Inspect

默认先读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

重点检查 project_state 训练产物：

1. `project_state/local_reverse_training_coverage_matrix.json`
2. `project_state/local_reverse_training_gap_report.md`
3. `project_state/local_reverse_solver_tool_capability_map.json`
4. `project_state/local_reverse_training_inventory_refresh.json`
5. `project_state/local_reverse_training_status.json` if present
6. `project_state/local_reverse_evaluation_queue.json` if present

重点检查测试文件是否存在，避免重复新增同名测试：

1. `tests/test_local_reverse_static_type_tags.py` if present
2. `tests/test_local_reverse_training_status.py`

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录。
5. `decision_meta.status=APPROVED`。
6. `mainline=training_dataset`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. 当前 decision 的 Implementation Scope 不包含 forbidden source paths。
9. 本轮是 contract/schema artifact 工作，不是样本求解或工具执行。

必须审计并记录：

1. 上一轮 BLOCKED 的具体原因，并确认本轮 scope 已移除 forbidden paths。
2. capability map 中已有的 inventory、static triage、IDA static extraction、debugger dynamic extraction、StructuredEvidence、solver template、harness、GUI/CLI entrypoint 能力状态；只记录能力，不执行工具。
3. coverage matrix/gap report 中每个目标 type 的 status、gap、next_minimal_task。
4. contract 对每个 type tag 的 evidence requirements、allowed evidence sources、confidence rules、not sufficient conditions 是否明确。
5. synthetic tests 是否验证 contract schema 与关键 tag 规则，而不是验证样本结果。

## 6. Implementation Scope

允许新增或修改：

- `project_state/local_reverse_static_type_tag_contract.json`
- `project_state/local_reverse_static_type_tag_contract_report.md`
- `tests/test_local_reverse_static_type_tags.py`
- `tests/test_local_reverse_training_status.py` only if needed for shared test fixture reuse
- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260618_static_type_tag_contract_scope_repair_v1/*`

明确禁止修改：

- any `reverse_agent/` source file
- `.codex-skills/*`
- `solve_reports/*`
- sample binaries or local training corpus files

Contract 至少覆盖这些 tag ids：

- `string_comparison`
- `xor`
- `shift_affine`
- `bit_operations`
- `lookup_table`
- `rc4`
- `des`
- `tea_xtea`
- `base64`
- `hash_md5_sha`
- `gui_validation`
- `simple_antidebug`
- `mixed_unknown`

每个 tag 至少包含：

- `evidence_requirements`
- `allowed_evidence_sources`
- `confidence_rules`
- `solver_or_tool_route`
- `not_sufficient_conditions`
- `next_minimal_task`
- `metadata_only_allowed`
- `static_verified_requires`

Tests 必须使用 synthetic/static contract fixtures，验证：

1. contract 覆盖所有 required tag ids。
2. 每个 tag 具有 required fields。
3. filename/metadata hints 不足以成为 static_verified。
4. string comparison、XOR、shift/affine、lookup table、RC4、DES、hash、simple anti-debug 均有明确 evidence requirements。
5. cipher/hash/anti-debug 类不因 sample name 或 solver module name 单独升级为 static_verified。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_local_reverse_static_type_tags.py tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.local_reverse_training_status --json

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`，运行：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_static_type_tag_contract_scope_repair_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：

- profile 与 closeout_allowed；
- 是否运行 close-round；
- contract artifact 路径；
- tests 覆盖的 tag ids；
- 哪些类别仍为 metadata-level only；
- 是否存在 forbidden path 修改；
- final-check 状态。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 APPROVED。
3. `mainline` 不是 `training_dataset`。
4. `reverse-agent-iteration@v2` 不是 active。
5. preflight 再次出现 `forbidden_paths_not_allowed`。
6. 需要修改任何 `reverse_agent/` source file。
7. 需要运行样本、debugger、IDA/Ghidra、emulator、runtime probe 或 sidecar。
8. 需要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
9. 需要修改允许范围之外的文件。
10. contract 把 metadata/file-name hints 声称为 current static evidence。
11. contract 或测试把某类题声称为 solved/static-verified 但没有 evidence 规则支持。
12. report-summary 或 final-check 最终出现 FAIL。
13. 报告声称完成 type tag contract，但没有 project_state contract artifact 或没有 synthetic/unit tests。
