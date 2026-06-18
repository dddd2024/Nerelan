```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_static_triage_type_evidence_schema_v1",
  "round_id": "round_20260619_static_triage_type_evidence_schema_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

补强现有单样本静态取证 adapter 的“题型证据承载能力”，为上一轮 `first_static_triage_queue` 中的代表样本提供统一的 type-evidence schema。目标是让后续真正运行静态取证时，产物能够记录 lookup-table、hash bounded-domain、cipher、anti-debug、bit/shift/XOR 等题型证据，而不是只给字符串、函数、compare context 和 solver hints。

本轮属于 `tool_integration`，不是 reverse-solving，也不是训练集批量回填。

本轮目标：

- 复用现有 `reverse_agent/local_reverse_single_sample_static_triage.py` 和 `reverse_agent/ida_scripts/collect_evidence.py`，不新建重复 IDA/Ghidra/debugger 接口。
- 在现有 static triage artifact 中增加稳定、可测试的 `type_evidence` / `type_tag_observations` 结构。
- 对上一轮队列需要的类型提供可承载字段：`string_comparison`、`xor`、`shift_affine`、`bit_operations`、`lookup_table`、`rc4`、`des`、`hash_md5_sha`、`simple_antidebug`、`mixed_unknown`。
- 对 hash 显式记录 `bounded_domain_required` 和 `bounded_domain_evidence`，没有长度/字符集/格式证据时不得允许 solver/bruteforce。
- 对 lookup-table 显式记录 table access/base/size/contents 是否观察到；未观察到时保持 `not_observed` 或 `needs_static_triage_field_support`。
- 新增 synthetic/unit tests，只喂入人工构造的 IDA evidence dict，不运行 IDA、不运行样本、不执行 solver/harness。

## 2. Current Evidence

主线是 `tool_integration`。

上一轮 `decision_20260618_training_first_static_triage_queue_v1` 已完成并审计为 `ACCEPTED_WITH_LIMITATIONS`。产物是首批静态取证队列，不是样本求解，也没有运行 static triage、IDA/Ghidra、runtime 或 harness。

上一轮队列已经选择了 9 个 metadata-only representative：

- `string_comparison`: `cpp2_fc735338`
- `xor`: `xor_array_solver_v2_fb15e14c`
- `shift_affine`: `affineenc_333f8ca9`
- `lookup_table`: `ascii_table_chinese_46efc7ea`
- `rc4`: `rc4enc_a1897c10`
- `des`: `desenc_40cba418`
- `hash_md5_sha`: `sha_256_18019fca`
- `simple_antidebug`: `seh_52be8d5c`
- `mixed_unknown`: `samplereverse_ca74a786`

上一轮也明确：`tea_xtea`、`base64`、`gui_validation` 当前无样本，应继续保持 `blocked_no_current_sample`，不能伪造 coverage。

`project_state/local_reverse_first_static_triage_queue.json` 明确规定：所有 queued item 仍是 `metadata_only`；不得从 filename、sample id、category、solver module name、inventory metadata 或 coverage row membership 推导 static verification。

当前 `reverse_agent/local_reverse_single_sample_static_triage.py` 已经存在，职责是读取 queue/inventory，复用 IDA evidence collection，产生 compact triage artifact。它声明不执行目标 binary、不生成 candidates。现有 `_parse_ida_evidence` 主要抽取：

- `interesting_strings`
- `functions`
- `compare_contexts`
- `validation_function_candidates`
- `solver_hints`
- `decompiler_snippets`
- `input_apis`
- `solver_profile_hypotheses`

当前 `reverse_agent/ida_scripts/collect_evidence.py` 已经会输出：`strings`、`functions`、`compare_contexts`、`local_check_contexts`、`control_id_contexts`、`string_xrefs`、`validation_function_candidates`、`decompiler_snippets`、`forced_decompiler_snippets`、`solver_hints` 等字段。成熟工具输出已经存在，本轮应在 adapter 层做结构化归一，不重复写一个新的 IDA collector。

`task_packet.json` 仍是旧 sample-state / `collect_missing_evidence` 建议；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`current_state.json` 仍指向 `samplereverse`，best candidates 为空，多个 artifact 字段为空；这不能作为当前样本求解证据。

`artifact_index.json` 中大量 sample/runtime artifact 是 `freshness=missing`；不得把 missing/stale/unknown artifact 当作 current evidence。

`negative_results.json` 禁止方向继续有效：

- 不回到旧 `sample_solver` blind search。
- 不做 only beam/budget/topN expansion。
- 不把 `compare_semantics_agree=false` candidate 作为 primary frontier。
- 不提交完整 `solve_reports/`。
- 不重复 exact2 basin/H1-H3 fixed contrast/current 5-candidate transform trace consistency audit。

已有能力检查结论：

- IDA static extraction 已存在：`reverse_agent/tool_runners.py` 和 `reverse_agent/ida_scripts/collect_evidence.py`。
- single-sample static triage adapter 已存在：`reverse_agent/local_reverse_single_sample_static_triage.py`。
- StructuredEvidence 已支持 CandidateEvidence、RuntimeCompareEvidence、StaticStringEvidence、ConstraintEvidence、Base64、RC4、UTF-16LE material evidence。
- debugger/OllyDbg/CompareProbe、solver templates、harness、GUI/CLI entrypoints 已存在，但本轮不运行这些能力。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何本地样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner、solver、harness 或 GUI/frontend workflow。

不要新建重复的 IDA runner、Ghidra runner、debugger runner、emulator runner 或 solver framework。

不要修改 `.codex-skills/`。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 inventory/status/coverage matrix 来伪造进度。

不要把 synthetic/unit test evidence 当作真实 sample static evidence。

不要把 keyword hit、filename、solver module name、sample id 或 queue membership 标记为 `static_verified`。

不要把本轮产物说成已经解题、已运行 IDA/Ghidra、已运行 runtime validation 或已验证 candidate。

不要触碰前端/GUI、pipeline 大重构、数据库、消息队列或多 agent 调度系统。

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

1. `project_state/local_reverse_first_static_triage_queue.json`
2. `project_state/local_reverse_first_static_triage_queue_report.md`
3. `project_state/local_reverse_static_type_tag_contract.json`
4. `project_state/local_reverse_static_type_tag_contract_report.md`
5. `project_state/local_reverse_solver_tool_capability_map.json`
6. `reverse_agent/local_reverse_single_sample_static_triage.py`
7. `reverse_agent/ida_scripts/collect_evidence.py`
8. `reverse_agent/evidence.py`
9. `reverse_agent/tool_runners.py`
10. `tests/test_local_reverse_first_static_triage_queue.py`
11. `tests/test_tool_runners.py`
12. `tests/test_tool_capability_inventory.py`
13. `project_state/gates/gate_profile_plan.json`
14. `project_state/gates/command_plan.json`
15. `project_state/gates/final_gate_result.json`
16. `project_state/gates/report_summary_synthesis.json`

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录；若已有 dirty files，必须记录 baseline 并排除继承脏改动。
5. `decision_meta.status=APPROVED`。
6. `mainline=tool_integration`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. `task_packet.json` 不是执行权威。
9. `artifact_index` 中 missing/stale artifact 没有被当成 current evidence。
10. `negative_results.json` 禁止方向没有被重复。
11. 已有 IDA/Ghidra/debugger/tool runner/solver/harness 接口已检查，且本轮没有重复实现。
12. 本轮所有新增测试是 synthetic/unit tests，不执行样本或外部工具。

必须审计并记录：

1. 是否复用现有 `local_reverse_single_sample_static_triage.py`，而不是新建重复 adapter。
2. 是否只在现有 `_parse_ida_evidence`/artifact assembly 路径上增加 type-evidence normalization。
3. 新增 schema 是否把 `observed_signal`、`candidate_static_signal`、`not_observed` 与 `static_verified` 明确区分。
4. hash profile 是否默认 `bounded_domain_required=true`，且没有 domain evidence 时不会输出 solver-ready 结论。
5. lookup-table profile 是否能记录 table access/base/size/contents 的缺失状态，不能因 filename/table keyword 自动升级。
6. anti-debug profile 是否只记录 static signal，不允许启动 debugger。
7. tests 是否覆盖 blocked artifact 和 success artifact 两种路径。
8. report 是否明确本轮未运行 IDA/Ghidra/sample/runtime，所有观察都来自 synthetic tests 或 adapter schema。

## 6. Implementation Scope

Allowed paths:

- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `tests/test_local_reverse_static_triage_type_evidence_schema.py`
- `project_state/local_reverse_static_triage_type_evidence_schema.json`
- `project_state/local_reverse_static_triage_type_evidence_schema_report.md`
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
- `project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/*`

Implementation requirements:

1. Add a pure helper in `reverse_agent/local_reverse_single_sample_static_triage.py`, for example `_extract_type_evidence(evidence, parsed_triage)` or equivalent. It must not run external tools.
2. Integrate the helper into the success artifact under a stable field such as `triage.type_evidence`.
3. Ensure blocked artifacts also include an empty/default `triage.type_evidence` structure so downstream consumers can rely on the field.
4. `type_evidence` must include at least:
   - `schema_version`
   - `source`
   - `type_tag_observations`
   - `profiles`
   - `promotion_safety`
5. `profiles` must contain stable keys for:
   - `string_comparison`
   - `xor`
   - `shift_affine`
   - `bit_operations`
   - `lookup_table`
   - `rc4`
   - `des`
   - `hash_md5_sha`
   - `simple_antidebug`
   - `mixed_unknown`
6. Each profile must have a `status` chosen from a small explicit set such as `not_observed`, `candidate_static_signal`, `observed_static_signal`, or `blocked_missing_required_evidence`. Do not use `static_verified` in this helper.
7. Each profile must include `required_evidence`, `observed_evidence`, `missing_evidence`, and `promotion_blockers` or equivalent fields.
8. `hash_md5_sha` must include `bounded_domain_required=true` and a bounded-domain subfield that records whether length/charset/format evidence exists.
9. `lookup_table` must include table-access/base/size/contents subfields, even when they are missing.
10. `promotion_safety` must state that keyword hits and metadata are not enough for static verification.
11. Add `project_state/local_reverse_static_triage_type_evidence_schema.json` documenting the schema contract and status vocabulary.
12. Add `project_state/local_reverse_static_triage_type_evidence_schema_report.md` summarizing what changed, what remains unsupported, and why no tool/sample execution occurred.
13. Add `tests/test_local_reverse_static_triage_type_evidence_schema.py` with synthetic evidence dictionaries covering:
   - compare context -> string_comparison candidate signal;
   - XOR/decompiler text -> xor/bit_operations candidate signal;
   - shift/affine text -> shift_affine candidate signal;
   - lookup table text without base/size/contents -> blocked/missing required evidence;
   - RC4 KSA/PRGA/S-box/key text -> rc4 candidate signal;
   - DES S-box/permutation/key schedule text -> des candidate signal;
   - hash constants without bounded domain -> blocked_missing_required_evidence;
   - hash constants with length/charset/format text -> bounded domain evidence present but still not static_verified;
   - anti-debug API/SEH text -> simple_antidebug candidate signal;
   - blocked artifact path contains default empty type_evidence.
14. Keep changes small and local. Do not modify `reverse_agent/ida_scripts/collect_evidence.py` unless the helper cannot consume existing fields; prefer not to modify it in this round.
15. Do not modify `reverse_agent/tool_runners.py`, `reverse_agent/evidence.py`, solver modules, harness modules, GUI/frontend, inventory/status builders, or project gate logic unless a test import break requires a tiny compatibility fix. If such a fix is needed, stop and report `REWORK_REQUIRED` rather than expanding scope.

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_local_reverse_static_triage_type_evidence_schema.py tests/test_local_reverse_first_static_triage_queue.py tests/test_tool_runners.py tests/test_tool_capability_inventory.py tests/test_project_gate.py tests/test_project_state.py -q
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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_static_triage_type_evidence_schema_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：

- 修改的 helper / schema 字段；
- status vocabulary；
- synthetic tests 覆盖的 profile；
- blocked/default artifact path；
- 是否修改 `ida_scripts/collect_evidence.py`，若修改必须解释必要性；
- 是否没有运行 IDA/Ghidra/sample/runtime/solver/harness；
- gate profile、report-summary、final-check 状态。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 `APPROVED`。
3. `mainline` 不是 `tool_integration`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、solver、harness、IDA、Ghidra、debugger、emulator、runtime probe、sidecar 或 GUI workflow。
6. 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
7. 需要新建重复 IDA/Ghidra/debugger/tool runner 接口。
8. 需要修改允许范围之外的 source file。
9. 需要修改 solver/harness/project gate/GUI/frontend 逻辑。
10. 新 schema 把 keyword/metadata/filename/sample id/solver module name 标为 `static_verified`。
11. hash profile 没有 bounded-domain policy。
12. lookup_table profile 不能表达 table evidence 缺失状态。
13. tests 需要真实 IDA/Ghidra/sample/runtime 才能通过。
14. `pytest_result.txt` 没有真实测试记录。
15. report/decision/pytest_result 的 decision_id 或 round_id 不匹配。
16. `report-summary` 或 `final-check` 出现 FAIL。
