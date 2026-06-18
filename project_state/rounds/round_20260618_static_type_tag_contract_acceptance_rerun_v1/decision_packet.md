```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_static_type_tag_contract_acceptance_rerun_v1",
  "round_id": "round_20260618_static_type_tag_contract_acceptance_rerun_v1",
  "based_on_state_build_id": "state_20260618_114539_14d4ec94f06b",
  "based_on_state_digest": "14d4ec94f06bab113eb55fdf774e82b449b2851672e927f2b0df7a6052a95cc2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

重新验证并收尾静态题型标签契约，使上一轮已经生成但未被 clean final-check 接受的 type-tag contract 进入可审计成功态。

前序情况：

1. `static_type_tag_contract_scope_wording_repair_v1` 已创建 `project_state/local_reverse_static_type_tag_contract.json`、`project_state/local_reverse_static_type_tag_contract_report.md` 和 `tests/test_local_reverse_static_type_tags.py`，并记录 `1067 passed`，但因为 gate 当时不识别 `Allowed paths:`，错误选择 fast profile，导致 final-check FAILED。
2. `allowed_paths_source_test_scope_parser_fix_v1` 已在 `engineering_branch` 修复 `_allowed_source_test_scope_paths`，新增 `Allowed paths:` 支持，并通过 full gate closeout。

本轮目标：

- 在修复后的 gate 下重新验证 existing static type-tag contract artifacts 和 synthetic/unit tests。
- 不扩展 contract 语义，不新增样本求解，不批量 backfill inventory。
- 只允许在发现 contract artifact 与测试不一致时做最小同步修正。
- 最终 `report-summary` 和 `final-check` 不得有 FAIL。
- 如果 `gate_profile_plan.closeout_allowed=true`，必须运行 close-round 并确认 archived report/pytest 与 live 一致。

本轮属于 `training_dataset`，不是 reverse-solving，也不是 tool_integration。

## 2. Current Evidence

主线是 `training_dataset`。

已有事实：

- 本地训练覆盖矩阵确认 local project_state inventory 有 65 个 metadata-only entries，read-only builder status 为 solved=1、blocked=2、needs_triage=0、inventory_only=62，多数类别仍为 metadata/source-audit level。
- 覆盖矩阵要求先建立 type tag enrichment、simple transform recipes、cipher static evidence profile、hash bounded-domain policy、GUI/anti-debug metadata fields。
- `static_type_tag_contract_scope_wording_repair_v1` 已生成 contract JSON、contract report 和 synthetic tests，但最终未被接受，原因是 gate-profile 错选 fast，而不是 contract 语义失败。
- `allowed_paths_source_test_scope_parser_fix_v1` 已修复 gate parser，final-check PASSED，archive_status=archived，report_status=SUCCESS，acceptance_recommendation=ACCEPTED。

`task_packet.json` 仍可能保留旧 sample_state/reverse-solving 建议；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`negative_results.json` 中禁止方向继续有效：旧 sample_solver blind search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports 等不得触碰。

本轮必须检查已有能力：sample metadata、inventory/status overlay、evaluation queue、solver/tool capability map、StructuredEvidence/tool-output 能力描述、IDA/Ghidra/debugger/tool runner/harness/GUI/CLI entrypoint。只记录能力，不执行工具。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner 或 GUI/frontend workflow。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要读取或提交完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要修改任何 `reverse_agent/` source file。

不要修改 solver、harness、tool runner、evidence、static triage 或 project gate 主逻辑。

不要把 filename/metadata hints 声称为 current static evidence。

不要把任何 type-tag category 声称为 solved 或 live/static-triage verified，除非 contract 中有明确 evidence rule 且测试只验证 schema/synthetic rule。

不要批量 backfill inventory type tags。

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

重点检查：

1. `project_state/local_reverse_static_type_tag_contract.json`
2. `project_state/local_reverse_static_type_tag_contract_report.md`
3. `tests/test_local_reverse_static_type_tags.py`
4. `tests/test_local_reverse_training_status.py`
5. `project_state/local_reverse_training_coverage_matrix.json`
6. `project_state/local_reverse_training_gap_report.md`
7. `project_state/local_reverse_solver_tool_capability_map.json`
8. `project_state/local_reverse_training_inventory_refresh.json`
9. `project_state/gates/gate_profile_plan.json`
10. `project_state/gates/command_plan.json`
11. `project_state/gates/final_gate_result.json`
12. `project_state/gates/report_summary_synthesis.json`

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
8. 本轮是 training contract validation，不是样本求解或工具执行。
9. gate 已包含 `Allowed paths:` parser fix；若 gate-profile 仍错误选择 fast 且 tests/source files 在 allowed scope 或 round delta 中，立即停止并报告 `REWORK_REQUIRED`。

必须审计并记录：

1. contract artifact 是否存在且包含全部 required tag ids。
2. 每个 tag 是否包含 required fields。
3. tests 是否覆盖 metadata hints 不足以 static_verified、关键 transform/cipher/hash/anti-debug evidence requirements。
4. contract report 是否明确哪些类别仍为 metadata-level only。
5. 本轮是否没有修改任何 `reverse_agent/` source file。
6. gate-profile 是否为 standard 或其它允许 pytest 的 profile；如果 profile 是 fast，必须解释为什么没有 source/test delta 且 command-plan/pytest/report 一致。

## 6. Implementation Scope

Allowed paths:

- `project_state/local_reverse_static_type_tag_contract.json`
- `project_state/local_reverse_static_type_tag_contract_report.md`
- `tests/test_local_reverse_static_type_tags.py`
- `tests/test_local_reverse_training_status.py` only if needed for shared test fixture consistency
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
- `project_state/rounds/round_20260618_static_type_tag_contract_acceptance_rerun_v1/*`

Implementation requirements:

1. Prefer no semantic changes to contract contents; validate existing artifacts and tests first.
2. If contract artifact and tests disagree, make the smallest project_state/test-only correction inside allowed paths.
3. Contract must cover these tag ids: `string_comparison`, `xor`, `shift_affine`, `bit_operations`, `lookup_table`, `rc4`, `des`, `tea_xtea`, `base64`, `hash_md5_sha`, `gui_validation`, `simple_antidebug`, `mixed_unknown`.
4. Each tag must include: `evidence_requirements`, `allowed_evidence_sources`, `confidence_rules`, `solver_or_tool_route`, `not_sufficient_conditions`, `next_minimal_task`, `metadata_only_allowed`, `static_verified_requires`.
5. Report must state that the contract is schema/synthetic-test validated only, not sample-solved or live static-triage verified.
6. Do not modify any `reverse_agent/` source file.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_static_type_tag_contract_acceptance_rerun_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：profile 与 closeout_allowed、是否运行 close-round、contract artifact 路径、tests 覆盖的 tag ids、metadata-level only 类别、是否修改 `reverse_agent/`、final-check 状态。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 APPROVED。
3. `mainline` 不是 `training_dataset`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、debugger、IDA/Ghidra、emulator、runtime probe 或 sidecar。
6. 需要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改允许范围之外的文件。
8. 需要修改任何 `reverse_agent/` source file。
9. contract 把 metadata/file-name hints 声称为 current static evidence。
10. contract 或报告把某类题声称为 solved/static-verified 但没有 evidence rule 支撑。
11. gate-profile 仍因 `Allowed paths:` 解析问题误选 fast。
12. report-summary 或 final-check 最终出现 FAIL。
13. 报告声称完成 contract acceptance，但没有 project_state contract artifact 或没有 synthetic/unit tests。
