```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_cpp1_2f6fcb63_input_delivery_review_v1",
  "round_id": "round_20260614_cpp1_2f6fcb63_input_delivery_review_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

对 `cpp1_2f6fcb63` 做一轮小步、可审计的 **nonprintable input-delivery review**。

目标不是重新求 printable password，也不是运行样本验证答案，而是围绕上一轮 current artifact 中的非打印 all-byte preimage，审查它是否存在可交付的输入形式，并生成一个新的 current artifact：

- `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`

该 artifact 必须回答：

1. 当前非打印 16-byte preimage 是否含有 `%s` 的硬阻断字节：NUL、ASCII whitespace、CR/LF、tab、space；
2. `scanf("%s", Str)`、`strlen(Str)==18`、`strncpy(Destination, Str, 0x10u)` 对前 16 字节和后 2 字节的真实输入约束是什么；
3. 第 17、18 字节是否只用于满足 `strlen==18`，是否不参与 `strncpy(Destination, Str, 0x10u)` 复制；
4. 成功边界 `i == 16` 是否需要额外审查 `Destination[16]` 与 `byte_429A30[16]` 的 mismatch 条件，避免把后缀字节误认为能控制 index 16；
5. 哪些输入交付方式是静态上可行的：Windows console 手输、PowerShell 写 raw bytes 后重定向、Python subprocess raw stdin、文件重定向、调试器内存写入；
6. 哪些方式只是下一轮 runtime validation 的候选，不得在本轮直接执行；
7. 下一轮是否可以进入 `READY_FOR_BOUNDED_RUNTIME_VALIDATION_DECISION`，还是应先做 `NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK` / `NEEDS_TARGET_ADJACENT_BYTE_RECHECK` / `BLOCKED_INPUT_DELIVERY_HARD_BLOCKER`。

本轮允许生成 raw-byte delivery plan、payload hex、payload construction recipe、PowerShell/Python 命令模板，但不得运行目标样本，不得把 payload 称为 flag/password/solved answer，不得做 runtime validation。

## 2. Current Evidence

本轮主线为 `reverse_solving`。`task_packet.json` 与 `current_state.json` 仍可能含旧 `samplereverse` advisory/historical 背景；当前执行权威是本 `project_state/decision_packet.md`，不是 `task_packet.task`。

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`：`decision_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1` 完成了静态替代语义审查，但存在 baseline/provenance 限制。上一轮 `git status --short` 阶段已经出现实质性源码、测试和 artifact dirty/untracked，后续报告将它们解释为 inherited baseline。Codex 本轮必须先记录启动 baseline，再做任何修改，不能在 report 中含糊覆盖实质性变更来源。

当前 `artifact_index.json` 已登记以下 current artifacts：

- `local_reverse_cpp1_2f6fcb63_static_triage`：`freshness=current`，source_run 为 `round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1`；
- `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation`：`freshness=current`，source_run 为 `round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1`；
- `local_reverse_cpp1_2f6fcb63_static_inverse_handoff`：`freshness=current`，source_run 为 `round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1`；
- `local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review`：`freshness=current`，source_run 为 `round_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1`。

当前 `local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json` 显示：

- `executed_sample=false`；
- `static_only=true`；
- `runtime_validated=false`；
- `authoritative=false`；
- `candidate=null`；
- `known_candidate=""`；
- `recommended_next_action=NEEDS_INPUT_DELIVERY_REVIEW`；
- `nonprintable_static_preimage_preview_hex=5d5a1cde131557d7d69dde2417df2453`；
- byte classes：control indices 为 `2,4,5,12`，high-bit indices 为 `3,7,8,9,10,13`，NUL/whitespace indices 为空；
- delivery risk 为 console-unfriendly，但 raw stdin/file-redirection 可能可行，需要单独审查。

当前 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json` 显示 target symbol 为 `byte_429A30`，target address 为 `0x00429A30`，target length 为 16，target bytes hex 为 `d596c4f60745577776e5f64847f74817`，main function 为 `_main_0`，并确认 `strlen(Str) != 18`、`strncpy(Destination, Str, 0x10u)`、transform formula fragments 和 `Destination[i] == byte_429A30[i]` 语义一致。

当前 `local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json` 显示 signed/unsigned transform model 在 0x00..0xff 域内等价；所有 target bytes 都有唯一 all-byte-domain preimage；printable ASCII 域不完整，blocked_reason 为 `NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES`。

当前 `negative_results.json` 已记录并禁止重复：

- `cpp1_2f6fcb63 current target bytes printable inverse path`

本轮必须消费该 negative result，不能继续重跑 printable inverse，也不能扩 beam/topN/budget 或切回旧 sample_solver 盲搜。

已有相关能力必须优先复用：

- `reverse_agent/local_reverse_cpp1_alternative_static_semantics_review.py` 的 preimage classification / review artifact 结构；
- `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py` 的 transform/preimage 函数；
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py` 的 target/provenance 结构；
- IDA static triage artifact；
- artifact_index、negative_results、project_gate/report-summary/final-check/close-round；
- 现有 harness/runtime/debugger/IDA/Ghidra 接口只能作为 read-only capability survey，除非本 decision 明确允许，否则不得执行。

## 3. Do Not Do

不得运行目标样本二进制；不得做 runtime probe、debugger、emulator、hook、harness campaign、candidate validation 或动态验证。

不得运行 IDA/Ghidra/radare2/objdump 重新提取数据。若发现 current artifacts 无法回答 success-boundary 或 adjacent-byte 问题，应记录 `NEEDS_TARGET_ADJACENT_BYTE_RECHECK` 或 `NEEDS_TOOL_INTEGRATION_DECISION`，由下一轮单独决定是否跑工具。

不得重复 current target bytes printable inverse path；不得只重新报告 missing printable indices；不得回退到旧 `sample_solver` 盲搜；不得仅扩大 beam/topN/budget。

不得把 `5d5a1cde131557d7d69dde2417df2453` 或任何 18-byte payload 称为 flag、password、candidate 或 solved answer。本轮最多可写为 `nonprintable_static_preimage_preview_hex` 或 `payload_preview_hex`，并且必须保持 `candidate=null`、`known_candidate=""`、`runtime_validated=false`、`authoritative=false`。

不得修改 raw sample 文件、`training_materials/`、`.codex-skills/`、完整 `solve_reports/`、训练状态 solved 字段、solver/harness/runtime/debugger/emulator code。

不得扩大到其他样本；本轮只允许 `cpp1_2f6fcb63`。

不得把 stale/missing/unknown artifact 当 current evidence。

## 4. Files To Inspect

必须按顺序读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

还必须有界读取：

- `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`，若已存在，只作 stale/previous context，除非 artifact_index 已登记本轮 current；
- `project_state/local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json`；
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`；
- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`；
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`；
- `reverse_agent/local_reverse_cpp1_alternative_static_semantics_review.py`；
- `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py`；
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`；
- `tests/test_local_reverse_cpp1_alternative_static_semantics_review.py`；
- `tests/test_local_reverse_cpp1_signed_transform_recheck.py`；
- `tests/test_local_reverse_cpp1_target_byte_extract.py`；
- `tests/test_project_gate.py`；
- `tests/test_project_state.py`。

允许 read-only capability survey，但不得执行：

- 现有 runtime validation / harness / debugger / emulator / IDA / Ghidra 相关模块；
- 只读目的是确认已有接口，避免重复实现或错误假设工具不存在。

禁止默认读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

Codex 必须先完成启动审计：

- 执行并记录 `Set-Location F:\reverse-agent`、`Get-Location`、`Test-Path F:\reverse-agent`、`git rev-parse --show-toplevel`、`git status --short`；
- 若无法进入 `F:\reverse-agent`、路径不存在、不是 git 仓库，立即停止；
- 若启动时已有 dirty/untracked 文件，必须写入 `project_state/gates/round_baseline.json` 或等效 baseline 记录，并在 report 中逐项说明 inherited baseline 与本轮新增 delta，不能把本轮新增源码/测试混入 inherited baseline；
- 确认 decision_meta 合法，`status=APPROVED`，`mainline=reverse_solving`，skill profile 来自 active registry；
- 确认 `task_packet.json` 只是 advisory，当前执行权威为本 `decision_packet.md`。

必须完成的审查内容：

### A. 输入字节域审查

基于 current alternative review 的 `nonprintable_static_preimage_preview_hex`，重新分类 16-byte preimage：

- NUL indices；
- ASCII whitespace indices，包括 `0x09,0x0a,0x0b,0x0c,0x0d,0x20`；
- control indices；
- high-bit indices；
- printable ASCII indices；
- `%s` token hard blockers；
- `strlen` hard blockers；
- Windows console manual entry risk。

### B. 18-byte payload 约束审查

明确区分：

- 前 16 字节：由 `strncpy(Destination, Str, 0x10u)` 复制并参与 transform/compare；
- 第 17、18 字节：只用于让 `strlen(Str)==18`，不能假设它们能控制 `Destination[16]` 或 `Destination[17]`；
- payload 后缀必须是非 NUL、非 whitespace，建议 printable placeholder，例如 `AA`，但不得称为 candidate；
- payload preview 可以记录为 `payload_preview_hex`，但必须标记 `runtime_validated=false`、`authoritative=false`。

### C. success-boundary 审查

必须审查 `if (i == 16)` 的成功边界风险：

- compare loop 是 `i < v4 && Destination[i] == byte_429A30[i]`，当 `v4==18` 时，若 index 0..15 match 且 index 16 mismatch，则 loop 停在 `i==16` 并进入 success branch；
- 若 index 16 也 match，loop 可能继续到 17/18，导致 `i != 16`，反而失败；
- 因为 `strncpy(..., 0x10u)` 只复制 16 字节，输入后缀不应被错误建模为控制 `Destination[16]`；
- 如果 current static artifacts 没有足够数据判断 `Destination[16]` 与 `byte_429A30[16]`，本轮必须记录 `success_boundary_status=UNKNOWN_NEEDS_STATIC_OR_TOOL_RECHECK`，不得伪造结论；
- 如果 current artifacts 足够证明 index 16 mismatch 或 target length 16 boundary 安全，则记录证据路径和字段来源。

### D. 输入交付方式审查

输出 delivery plan，不执行：

- Windows console manual entry：预计不可行或高风险，因为存在 control/high-bit bytes；
- PowerShell raw-byte file creation + redirection：可作为下一轮 runtime validation 候选命令模板；
- Python raw stdin/subprocess：可作为下一轮 runtime validation 候选命令模板；
- file redirection：可作为下一轮 runtime validation 候选；
- debugger memory patch / stdin hook：本轮不得执行，只有当 raw stdin/file redirection 不可行时才可建议下一轮 tool_integration decision。

所有模板必须是 inert/template，不得在本轮调用目标 exe。

### E. 下一步路线选择

输出明确 `recommended_next_action`，只能从以下值中选择：

- `READY_FOR_BOUNDED_RUNTIME_VALIDATION_DECISION`：只有在无 NUL/whitespace hard blocker，且 success-boundary 风险已静态解释为可进入单独 runtime validation decision 时使用；
- `NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK`：如果输入交付可行，但 index 16 boundary 证据不足；
- `NEEDS_TARGET_ADJACENT_BYTE_RECHECK`：如果需要重新确认 `byte_429A30[16]` 或邻接数据；
- `BLOCKED_INPUT_DELIVERY_HARD_BLOCKER`：如果 preimage 或必要 suffix 含 NUL/whitespace 等 `%s` 硬阻断；
- `NEEDS_TOOL_INTEGRATION_DECISION`：如果必须调用 IDA/Ghidra/debugger/harness 才能继续。

必须生成新 artifact：

- `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`

artifact 必须包含：

- `schema_version`
- `sample_id`
- `relative_path`
- `sha256`
- `analysis_mode=input_delivery_review`
- `mainline=reverse_solving`
- `executed_sample=false`
- `static_only=true`
- `runtime_validated=false`
- `authoritative=false`
- `source_artifacts`
- `source_artifact_freshness`
- `negative_results_considered`
- `preimage_input_domain_review`
- `payload_length_review`
- `suffix_policy`
- `success_boundary_review`
- `delivery_options_review`
- `payload_preview_hex`
- `candidate=null`
- `known_candidate=""`
- `recommended_next_action`
- `stop_conditions_for_next_round`

必须将该 artifact 登记到 `project_state/artifact_index.json`：

- key：`local_reverse_cpp1_2f6fcb63_input_delivery_review`
- `kind=input_delivery_review`
- `freshness=current`
- `source_run=round_20260614_cpp1_2f6fcb63_input_delivery_review_v1`
- path 指向 `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`
- sample_id 为 `cpp1_2f6fcb63`

可以有界更新 `negative_results.json`，但只在发现新的明确 hard blocker 或禁止方向时允许。例如：

- 如果 success boundary 无证据，不要新增 solved/candidate；可新增禁止“without success-boundary evidence, run raw-byte validation as solved”；
- 如果发现 NUL/whitespace hard blocker，可新增对应 blocked direction；
- 不得重复新增 already-existing printable inverse prohibition。

## 6. Implementation Scope

Allowed source files:

- 新文件 `reverse_agent/local_reverse_cpp1_input_delivery_review.py`，仅当现有模块无法容纳 input-delivery review CLI 时允许；该文件不得运行样本、不得调用 IDA/Ghidra/debugger/emulator/harness；
- `reverse_agent/local_reverse_cpp1_alternative_static_semantics_review.py`，仅限复用或暴露分类 helper，不改变上一轮 artifact 语义；
- `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py`，仅限复用 transform helper，不改变 transform 语义；
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`，仅限复用 target/provenance helper，不重新提取 IDA 数据；
- `reverse_agent/project_state.py`，仅限 artifact_index 登记兼容修复。

Allowed tests:

- 新文件 `tests/test_local_reverse_cpp1_input_delivery_review.py`；
- `tests/test_local_reverse_cpp1_alternative_static_semantics_review.py`，仅当复用 helper contract 受影响；
- `tests/test_local_reverse_cpp1_signed_transform_recheck.py`；
- `tests/test_local_reverse_cpp1_target_byte_extract.py`；
- `tests/test_project_state.py`；
- `tests/test_project_gate.py`。

Allowed generated/state files:

- `project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`，仅当新增明确不同 blocked direction
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_input_delivery_review_v1/*`

Read-only only:

- current cpp1 artifacts listed above；
- old cpp1 artifacts and old round archives, only as bounded historical context；
- `project_state/local_reverse_training_status.json`；
- `project_state/local_reverse_evaluation_queue.json`；
- existing runtime/harness/debugger/tool integration code, only for capability survey。

Forbidden:

- raw sample files
- complete `solve_reports/`
- `.codex-skills/`
- `training_materials/`
- IDA/Ghidra/debugger/emulator/runtime/harness invocation
- `reverse_agent/strategies/`
- `reverse_agent/transforms/` unless importing existing helpers only and no file modifications occur
- any artifact or state change that marks `cpp1_2f6fcb63` solved

## 7. Tests

必须真实运行并记录到 `project_state/pytest_result.txt`：

- `Set-Location F:\reverse-agent`
- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- review command，例如：`python -m reverse_agent.local_reverse_cpp1_input_delivery_review --input-review project_state/local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json --target-revalidation project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json --inverse-handoff project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --artifact-index project_state/artifact_index.json --negative-results project_state/negative_results.json --out project_state/local_reverse_cpp1_2f6fcb63_input_delivery_review.json`
- `python -m pytest tests/test_local_reverse_cpp1_input_delivery_review.py -q`
- `python -m pytest tests/test_local_reverse_cpp1_alternative_static_semantics_review.py tests/test_local_reverse_cpp1_signed_transform_recheck.py tests/test_local_reverse_cpp1_target_byte_extract.py -q`
- 若修改 project_state/project_gate：`python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- artifact_index verification：确认 `local_reverse_cpp1_2f6fcb63_input_delivery_review` 为 current，source_run 为本轮 round id，sample_id 为 `cpp1_2f6fcb63`
- negative_results verification：确认没有重复新增 printable inverse prohibition
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_cpp1_2f6fcb63_input_delivery_review_v1`

新增或更新测试覆盖：

- review refuses stale/missing/non-current source artifacts；
- review consumes `cpp1_2f6fcb63 current target bytes printable inverse path` negative result；
- review classifies NUL/whitespace/control/high-bit/printable buckets correctly；
- review keeps `candidate=null`、`known_candidate=""`、`runtime_validated=false`、`authoritative=false`；
- review distinguishes first 16 copied bytes from suffix bytes 17–18；
- review does not claim suffix controls `Destination[16]`；
- review emits `NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK` when success-boundary evidence is insufficient；
- review can emit `READY_FOR_BOUNDED_RUNTIME_VALIDATION_DECISION` only when no `%s` hard blocker exists and success-boundary evidence is adequate；
- review writes artifact_index current metadata with dynamic source_run。

`close-round` 必须是 live 与 archived pytest 中最后一个 command block。

## 8. Stop Conditions

如果需要执行目标样本、runtime probe、debugger/emulator/hook/harness/candidate validation，立即停止并报告 `BLOCKED` 或 `NEEDS_SEPARATE_RUNTIME_VALIDATION_DECISION`。

如果 current alternative review、target revalidation、static inverse handoff 或 static triage artifact 缺失、不是 current、sample_id 不匹配，停止并报告 `BLOCKED`。

如果发现输入交付审查退化为重复 printable inverse path，停止并报告 `REWORK_REQUIRED`。

如果需要重跑 IDA/Ghidra/radare2/objdump 或重新提取 `byte_429A30` adjacent bytes，停止并输出 `NEEDS_TARGET_ADJACENT_BYTE_RECHECK` 或 `NEEDS_TOOL_INTEGRATION_DECISION`，不要在本轮直接跑工具。

如果 success-boundary 无法从 current artifacts 判定，不得硬写 ready for runtime；必须输出 `NEEDS_SUCCESS_BOUNDARY_STATIC_RECHECK` 或 `NEEDS_TARGET_ADJACENT_BYTE_RECHECK`。

如果 artifact_index 无法登记 current input-delivery review provenance，停止并报告 `REWORK_REQUIRED`，不得只提交裸 JSON。

如果测试或 gate 失败，`codex_execution_report.md` 必须标记 `FAILED/REWORK_REQUIRED` 或 `BLOCKED`，不能写 `SUCCESS/ACCEPTED`。

如果产生 payload preview，必须保持 `runtime_validated=false`、`authoritative=false`、`candidate=null`，不得写 solved。若无法保证这一点，停止。

如果需要修改 forbidden paths 或触碰多个样本，停止并报告 `BLOCKED`。
