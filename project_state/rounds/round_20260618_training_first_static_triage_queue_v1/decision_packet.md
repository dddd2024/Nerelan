```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_training_first_static_triage_queue_v1",
  "round_id": "round_20260618_training_first_static_triage_queue_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

生成本地逆向训练集的首批静态取证队列，把已经通过审计的 static type-tag contract 转换成下一轮可执行、可审计、可测试的小批量任务。

本轮目标是计划和状态产物，不是样本求解：

- 为当前有样本的主要类型各选择 1 个代表样本，形成 `first_static_triage_queue`。
- 对每个队列项记录：样本 id、目标类型、选择理由、所需静态证据、允许使用的已有工具/接口、禁止动作、预期输出 artifact、阻塞条件。
- 对当前没有样本的类型记录 `blocked_no_current_sample`，不伪造覆盖率。
- 新增轻量 schema/synthetic tests，确保队列不把文件名/metadata 当成 static_verified 证据。
- 不运行 IDA、Ghidra、debugger、runtime probe、sample runner、solver 或 harness。

本轮属于 `training_dataset`。它服务于两周内形成本地样本各题型解题能力的计划推进，但不直接进入 reverse-solving。

## 2. Current Evidence

主线是 `training_dataset`。

当前审计结论：上一轮 `decision_20260618_static_type_tag_contract_acceptance_rerun_v1` 已经 `SUCCESS` 并 close-round；最终接受等级是 `ACCEPTED_WITH_LIMITATIONS`，限制项是 50 个历史样本 artifact 缺失。该限制不阻塞训练集队列规划，但禁止把样本求解 artifact 当作 current evidence。

`task_packet.json` 仍保留 `collect_missing_evidence` / sample-state 建议；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`current_state.json` 当前 sample 仍是 `samplereverse`，但 `best_candidates` 为空，多个 runtime/static artifact 字段为空；这些不能作为当前样本求解证据。

`artifact_index.json` 的 latest_artifacts_v2 大量为 `freshness=missing`，包括 case_results、frontier_summary、runtime_validation、strata_summary、summary 等。不得把 missing/stale/unknown artifact 当 current evidence。

`negative_results.json` 中禁止方向继续有效：

- 不回到旧 `sample_solver` blind search。
- 不做 only beam/budget/topN expansion。
- 不把 `compare_semantics_agree=false` candidate 作为 primary frontier。
- 不提交完整 `solve_reports/`。
- 不重复已失败的 exact2 basin/H1-H3 fixed contrast/transform trace audit 方向。

上一轮 contract 已确认 13 个 required tag ids：

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

当前 coverage matrix 显示：

- local project_state inventory 有 65 个 metadata-only entries。
- read-only builder status：solved=1、blocked=2、needs_triage=0、inventory_only=62。
- string_comparison 有 35 个样本，1 个 solved，仍有 metadata gap。
- xor 有 2 个样本，coverage 为 `gap_or_tool_only`。
- shift/affine 有 4 个样本，coverage 为 `metadata_level_unverified`。
- lookup_table 有 3 个样本，coverage 为 `gap_or_tool_only`，tool_evidence_available=false。
- rc4 有 8 个样本，coverage 为 `metadata_level_unverified`。
- des 有 5 个样本，coverage 为 `metadata_level_unverified`。
- tea_xtea 当前 0 个样本。
- base64 当前 0 个样本。
- hash_md5_sha 有 2 个样本，coverage 为 `metadata_level_unverified`，其中 SHA-256 类方向需要 bounded input domain。
- gui_validation 当前 0 个样本。
- simple_antidebug 有 1 个样本，coverage 为 `metadata_level_unverified`。
- mixed_unknown 有 7 个样本，coverage 为 `metadata_level_unverified`。

已有能力检查结论：

- inventory_builder 已实现，但本轮不运行扫描。
- training_status_builder 已实现，read-only JSON 支持已可用。
- single_sample_static_triage 已实现，但本轮不执行。
- IDA static evidence collector 已实现，但本轮不执行。
- debugger_dynamic_extraction 已实现，但本轮 out of scope。
- StructuredEvidence 支持 CandidateEvidence、RuntimeCompareEvidence、StaticStringEvidence、ConstraintEvidence、Base64、RC4、UTF-16LE material evidence。
- solver_templates、harness、GUI/CLI entry points 已存在；本轮只引用能力，不执行求解或验证。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何本地样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner、solver、harness 或 GUI/frontend workflow。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要修改 `.codex-skills/`。

不要修改任何 `reverse_agent/` source file。

不要修改 solver、harness、tool runner、evidence、static triage、project gate 主逻辑。

不要把 filename、sample id、category、solver module name、inventory metadata 或 coverage matrix row 当成 static_verified evidence。

不要把本轮队列说成已经解题、已经 static-verified、已经 runtime-validated 或已经跑过 IDA/Ghidra。

不要批量 backfill inventory/status。

不要提交完整 `solve_reports/`。

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

重点读取：

1. `project_state/local_reverse_static_type_tag_contract.json`
2. `project_state/local_reverse_static_type_tag_contract_report.md`
3. `project_state/local_reverse_training_coverage_matrix.json`
4. `project_state/local_reverse_training_gap_report.md`
5. `project_state/local_reverse_solver_tool_capability_map.json`
6. `project_state/local_reverse_training_status.json`
7. `project_state/local_reverse_evaluation_queue.json`
8. `project_state/local_reverse_inventory.json`
9. `tests/test_local_reverse_static_type_tags.py`
10. `tests/test_local_reverse_training_status.py`
11. `project_state/gates/gate_profile_plan.json`
12. `project_state/gates/command_plan.json`
13. `project_state/gates/final_gate_result.json`
14. `project_state/gates/report_summary_synthesis.json`

如果某个 inventory/status 文件不存在或 GitHub-safe mirror 只有 50 entries，不要补写整个 inventory；在报告中记录 limitation。

不要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录；若有 baseline dirty files，必须记录并避免纳入本轮成果。
5. `decision_meta.status=APPROVED`。
6. `mainline=training_dataset`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. `task_packet.json` 只是建议，不覆盖本 decision。
9. `artifact_index` 中 missing/stale artifact 没有被当作 current evidence。
10. `negative_results.json` 禁止方向没有被重复。
11. 已有 IDA/Ghidra/debugger/tool runner/solver/harness 接口已检查，且本轮没有重复实现。
12. 本轮没有运行任何 sample/tool/runtime execution。

必须审计并记录：

1. 队列是否只从 coverage matrix / inventory / contract / capability map 中选取 metadata-level representative，不声称已验证。
2. 队列是否覆盖有样本的优先类型：`string_comparison`、`xor`、`shift_affine`、`lookup_table`、`rc4`、`des`、`hash_md5_sha`、`simple_antidebug`、`mixed_unknown`。
3. `bit_operations` 是否作为 cross-cutting tag 处理：可作为 secondary tag，但不要单独用 filename-derived bit metadata 宣称 static evidence。
4. `tea_xtea`、`base64`、`gui_validation` 若当前没有样本，必须记录为 `blocked_no_current_sample`，不得伪造代表样本。
5. 每个 queued item 是否包含 required evidence checklist 和 allowed route。
6. report 是否说明这是 planning/schema artifact，不是 solver result。
7. 测试是否验证队列 schema、blocked no-sample categories、no name-only upgrade rule、no runtime/tool execution claims。

## 6. Implementation Scope

Allowed paths:

- `project_state/local_reverse_first_static_triage_queue.json`
- `project_state/local_reverse_first_static_triage_queue_report.md`
- `tests/test_local_reverse_first_static_triage_queue.py`
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
- `project_state/rounds/round_20260618_training_first_static_triage_queue_v1/*`

Implementation requirements:

1. Create `project_state/local_reverse_first_static_triage_queue.json`.
2. JSON schema must include:
   - `schema_version`
   - `decision_id`
   - `round_id`
   - `based_on_artifacts`
   - `queue_policy`
   - `queued_items`
   - `blocked_categories`
   - `limitations`
3. Each `queued_items[]` entry must include:
   - `queue_id`
   - `type_id`
   - `sample_id`
   - `selection_source`
   - `metadata_confidence`
   - `coverage_status_before_triage`
   - `why_selected`
   - `required_static_evidence`
   - `allowed_existing_routes`
   - `forbidden_actions`
   - `expected_next_artifacts`
   - `promotion_rule`
   - `stop_condition`
4. Select at most one representative sample per primary type for this first queue.
5. For current sample-bearing rows, prefer sample ids already listed in `local_reverse_training_coverage_matrix.json`; do not invent sample ids.
6. Treat `bit_operations` as secondary/cross-cutting unless a concrete sample is selected with a specific primary route. Do not duplicate the same sample only to inflate coverage.
7. Put `tea_xtea`, `base64`, and `gui_validation` into `blocked_categories` when current sample_count is 0.
8. If `lookup_table` has `tool_evidence_available=false`, queue it only as `needs_static_triage_field_support_or_manual_static_evidence`, not as ready for automated proof.
9. For hash samples, include a `bounded_domain_required=true` field and explicitly prohibit brute-force without length/charset/format evidence.
10. For simple_antidebug, require static triage first and prohibit debugger execution in this round.
11. Create `project_state/local_reverse_first_static_triage_queue_report.md` summarizing queue order, rationale, limitations, and next authorized round types.
12. Add `tests/test_local_reverse_first_static_triage_queue.py` with schema/safety tests only.
13. Do not modify `reverse_agent/` source files.
14. Do not modify inventory/status files unless a test fixture absolutely requires it; prefer no changes to existing state inputs.

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_local_reverse_first_static_triage_queue.py tests/test_local_reverse_static_type_tags.py tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_training_first_static_triage_queue_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：

- selected queue items
- blocked categories
- queue schema checks
- metadata-only limitations
- no sample/tool/runtime execution confirmation
- no `reverse_agent/` modifications confirmation
- gate profile and final-check status

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 `APPROVED`。
3. `mainline` 不是 `training_dataset`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、solver、harness、IDA、Ghidra、debugger、emulator、runtime probe、sidecar 或 GUI workflow。
6. 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改允许范围之外的文件。
8. 需要修改任何 `reverse_agent/` source file。
9. 队列或报告把 filename/metadata hint 声称为 static evidence。
10. 队列或报告把某类型声称为 solved/static-verified/runtime-validated。
11. 需要批量 backfill inventory/status。
12. 队列样本无法从现有 coverage matrix/inventory/status 中确认来源。
13. `pytest_result.txt` 没有真实测试记录。
14. report/decision/pytest_result 的 decision_id 或 round_id 不匹配。
15. `report-summary` 或 `final-check` 出现 FAIL。
