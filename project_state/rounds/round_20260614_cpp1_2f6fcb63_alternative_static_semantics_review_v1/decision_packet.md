```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1",
  "round_id": "round_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

对 `cpp1_2f6fcb63` 做一轮 2–3 小时工作量的替代静态语义审查，目标不是重复当前 target bytes printable inverse path，而是系统性审计为什么 current target bytes 下 printable ASCII preimage 不完整，并判断下一步应走哪条不同证据路线。

本轮以 current artifacts 为入口：

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`

需要生成新的 current artifact：

- `project_state/local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json`

该 artifact 应回答：

1. 当前 `byte_429A30` target bytes 是否仍是最合理比较目标；
2. transform 方向、signed/unsigned 解释、位运算公式是否存在可替代语义；
3. `strlen(Str) == 18` 与 `strncpy(Destination, Str, 0x10u)` 只处理前 16 字节之间的关系是什么；
4. 输入是否实际要求 printable ASCII，还是 `%s` + `strlen` 仅要求非空白/非 NUL 字节；
5. 旧 `STATIC_CANDIDATE_NONPRINTABLE` 和当前 `NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES` 是否意味着“题目应允许非打印输入”、还是说明 target/transform/compare 语义仍有缺口；
6. 下一轮应选择：nonprintable-input handling / alternative target symbol review / transform-direction review / IDA cross-reference recheck / bounded runtime validation decision，还是保持 blocked。

本轮允许产生静态候选预览，但不得把它称为 flag/password/solved answer；不得运行样本，不得 runtime validate，不得调用 debugger/emulator/harness。若产生非打印 all-byte preimage，应记录为 `nonprintable_static_preimage_preview`，并标记 `runtime_validated=false`、`authoritative=false`、`requires_input_delivery_review=true`。

## 2. Current Evidence

上一轮 `decision_20260614_gate_close_round_idempotency_status_policy_rework_v1` 已收口：final gate 为 `PASSED_WITH_LIMITATIONS`，blocking reasons 为空，historical `samplereverse` missing artifacts 已降级为 non-blocking limitation，close-round 幂等性已改善，archive no-op 路径可返回 success。工程 gate 线可暂停，不应继续围绕 closeout 返工。

当前 `project_state/artifact_index.json` 已登记 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` 为 `freshness=current`，source_run 为 `round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1`；也已登记 `local_reverse_cpp1_2f6fcb63_static_inverse_handoff` 为 `freshness=current`，source_run 为 `round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1`。

当前 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json` 显示 target symbol 为 `byte_429A30`，target address 为 `0x00429A30`，target length 为 16，target bytes hex 为 `d596c4f60745577776e5f64847f74817`，main function 为 `_main_0`，并确认 `strlen(Str) != 18`、`strncpy(Destination, Str, 0x10u)`、transform formula fragments 和 `Destination[i] == byte_429A30[i]` 语义一致。

当前 `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json` 显示 signed/unsigned transform model 在 0x00..0xff 域内等价；所有 target bytes 都有唯一 all-byte-domain preimage；但是 printable ASCII 0x20..0x7e 域不完整，missing printable indices 为 `2, 3, 4, 5, 7, 8, 9, 10, 12, 13`。因此它的 status 是 `BLOCKED`，blocked_reason 为 `NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES`。

当前 `project_state/negative_results.json` 已新增 `cpp1_2f6fcb63 current target bytes printable inverse path`，要求不要重复当前 target bytes 下的 printable inverse 路线，除非有新的证据和明确 override reason。本轮必须尊重该 negative result。

旧 `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json` 是 stale/blocked context，不能作为 current solved evidence。旧 `local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json`、`local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json`、`local_reverse_cpp1_2f6fcb63_target_bytes.json` 只能作为 historical context，不得替代 current artifacts。

`task_packet.json` 与 `current_state.json` 仍可能含旧 `samplereverse` 背景，只能作为 advisory/historical background；本轮执行权威是本 `decision_packet.md`。

已有相关能力必须优先复用：`local_reverse_cpp1_signed_transform_recheck.py` 的 transform/preimage 函数、`local_reverse_cpp1_target_byte_extract.py` 的 target/provenance 结构、IDA static triage artifact、artifact_index、negative_results、project_gate/report-summary/final-check/close-round。不得新建重复 solver 或重复 IDA runner。

## 3. Do Not Do

不得重复执行 current target bytes printable inverse path。也就是说，不得只重新运行同一 `--from-revalidation` inverse handoff 并再次报告 missing printable indices；这一点已在 negative_results 中记录。

不得运行目标样本二进制；不得做 runtime probe、debugger、emulator、hook、harness campaign、动态验证、bruteforce、SMT、sample_solver 或 candidate validation。

不得运行 IDA/Ghidra/radare2/objdump 重新提取 target bytes，除非本轮静态 review 发现明确的 current artifact 冲突；即便发现，也应先记录 `BLOCKED_NEEDS_TOOL_RECHECK`，由下一轮 tool_integration decision 决定是否重新跑工具。

不得把非打印 all-byte preimage 直接称为 flag/password/solved answer；不得更新训练状态为 solved。

不得手工伪造 candidate、stdout/stderr、tool success、artifact freshness 或 sample result。

不得修改 raw sample 文件、`training_materials/`、`.codex-skills/`、完整 `solve_reports/`、训练状态/队列语义、solver/harness/runtime/debugger/emulator code。

不得扩大到其他样本；本轮只允许 `cpp1_2f6fcb63`。

不得把旧 stale artifacts 当 current evidence；所有结论必须以 current revalidation/static inverse handoff/static triage 为主，旧 artifacts 只能作为对照。

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

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`，只作 stale source context
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`，只作 stale blocked/negative context
- `project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json`，只作 stale context
- `project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json`，只作 stale context
- `project_state/local_reverse_training_status.json`，只读
- `project_state/local_reverse_evaluation_queue.json`，只读
- `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py`
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- `tests/test_local_reverse_cpp1_signed_transform_recheck.py`
- `tests/test_local_reverse_cpp1_target_byte_extract.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

必要时只读：

- `project_state/rounds/round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1/*`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1/*`
- `project_state/rounds/round_20260614_gate_close_round_idempotency_status_policy_rework_v1/*`

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=reverse_solving`，skill profile 来自 active registry。
- 当前 gate closeout rework 已收口；本轮不继续修 gate。
- 当前 required artifacts：target_bytes_revalidation 与 static_inverse_handoff 都是 current。
- negative_results 已禁止重复 current target bytes printable inverse path。
- 本轮目标是 alternative static semantics review，不是 repeat inverse handoff，不是 runtime validation。

必须完成的审查内容：

### A. 输入域审查

审查 `%s`、`strlen(Str) == 18`、`strncpy(Destination, Str, 0x10u)` 对输入字节的真实约束：

- 是否只是禁止 NUL/空白终止，而不是要求 printable ASCII；
- static all-byte preimage 中的非打印字节是否包含 NUL、空白、CR/LF、tab、space 等会破坏 `%s` 或 `strlen` 的字节；
- all-byte preimage 的 16 字节是否能作为某种 raw stdin / file redirected / escaped input 交付；
- 第 17–18 字节是否完全不参与 transform/compare，是否只用于满足 `strlen == 18`；
- 若输入包含非打印/高位字节，`strlen` 与 `scanf("%s")` 在 Windows 控制台/本地编码下的可交付性风险。

### B. transform 语义审查

审查 current transform formula 与 signed/unsigned model：

- 当前 formula 是否为单字节 bit permutation；
- signed arithmetic shift 是否经过 u8 truncation 后与 unsigned formula 等价；
- 是否可能误把 forward transform 当 inverse transform；
- 是否可能还有 XOR/add/sub/table lookup/previous byte dependency 未纳入 current formula；
- 若 full-byte preimage 唯一但 printable 不完整，是否反而证明 transform/target 组合更像 raw-byte 校验而非 printable key 校验。

### C. target bytes / target symbol 审查

审查 `byte_429A30` 作为 compare target 的充分性：

- target length 16 是否与 loop exit `i == 16` 一致；
- 是否存在邻近数据、字符串、xref 或相同地址 alias 可能导致 target bytes 读取偏移错误；
- current revalidation 是否足以排除旧 target bytes path 的 stale 风险；
- 如果证据不足，记录 `needs_target_xref_tool_recheck=true`，但本轮不得重跑 IDA。

### D. static candidate / nonprintable preimage 审查

从 current static_inverse_handoff 中提取 all-byte unique preimage，生成静态说明：

- 16-byte all-byte preimage hex；
- printable positions and missing positions；
- nonprintable byte classes：control bytes, high-bit bytes, whitespace/NUL-sensitive bytes；
- 可交付性风险分级：`console_unfriendly`、`stdin_raw_possible`、`requires_runtime_input_delivery_review` 等；
- candidate 字段保持 null，或如果必须给出 preview，只能用 `nonprintable_static_preimage_preview_hex`，并明确非 authoritative。

### E. 下一步路线选择

输出一个明确的 next action，不得含糊写“继续完善”。可选结论包括：

- `NEEDS_INPUT_DELIVERY_REVIEW`：如果 all-byte preimage 无 NUL/空白等 `%s` 硬阻断，但不可打印，需要下一轮设计静态/受限 runtime 输入交付验证；
- `NEEDS_TARGET_XREF_TOOL_RECHECK`：如果 target symbol/length/offset 证据不足；
- `NEEDS_TRANSFORM_SEMANTICS_RECHECK`：如果 transform formula 可能缺少额外操作；
- `BLOCKED_NO_PRINTABLE_SOLUTION_UNDER_CURRENT_SEMANTICS`：如果当前语义下只能得出非打印 raw-byte solution，且项目暂不允许运行样本或 raw input 验证；
- `READY_FOR_BOUNDED_RUNTIME_VALIDATION_DECISION`：只有在静态证据说明 raw-byte input delivery 合理且无 NUL/whitespace blocker 时，才能建议下一轮单独生成 runtime validation decision。

必须生成新 artifact：

- `project_state/local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json`

artifact 必须包含：

- `schema_version`
- `sample_id`
- `relative_path`
- `sha256`
- `analysis_mode=alternative_static_semantics_review`
- `mainline=reverse_solving`
- `executed_sample=false`
- `static_only=true`
- `runtime_validated=false`
- `authoritative=false`
- `source_artifacts`
- `source_artifact_freshness`
- `negative_results_considered`
- `input_domain_review`
- `transform_semantics_review`
- `target_symbol_review`
- `all_byte_preimage_review`
- `nonprintable_input_delivery_risk`
- `candidate=null`
- `known_candidate=""`
- `recommended_next_action`
- `stop_conditions_for_next_round`

必须将该 artifact 登记到 `project_state/artifact_index.json`：

- key 建议为 `local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review`
- `kind=alternative_static_semantics_review`
- `freshness=current`
- `source_run=round_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1`
- path 指向 `project_state/local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json`
- sample_id 为 `cpp1_2f6fcb63`

可以有界更新 `negative_results.json`，但只在新 review 得出明确新禁止方向时允许。例如：

- 如果确定 printable route 无意义，保留已有 entry，不重复新增；
- 如果确定 target-symbol review 必须先做，新增禁止“without target xref recheck, repeat raw-byte input validation decision”；
- 如果确定 raw-byte preimage 包含 NUL/whitespace 硬阻断，新增相应 blocked direction。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py`，仅限新增或复用函数来从 current handoff artifact 读取 all-byte preimage / printable analysis，不改变已有 transform 语义
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`，仅限复用/暴露 helper 读取 current target metadata，不重新提取 IDA 数据
- 新文件 `reverse_agent/local_reverse_cpp1_alternative_static_semantics_review.py`，仅当现有两个模块无法容纳 review CLI 时允许；该文件不得运行样本或调用 IDA
- `reverse_agent/project_state.py`，仅限 artifact_index 登记兼容修复

Allowed tests:

- `tests/test_local_reverse_cpp1_signed_transform_recheck.py`
- `tests/test_local_reverse_cpp1_target_byte_extract.py`
- 新文件 `tests/test_local_reverse_cpp1_alternative_static_semantics_review.py`，如果新增 review CLI
- `tests/test_project_state.py`
- `tests/test_project_gate.py`，仅当 gate/report contract 受影响时修改

Allowed generated/state files:

- `project_state/local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`，仅当新增明确不同的 blocked direction
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1/*`

Read-only only:

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- old cpp1 artifacts and old round archives
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`

Forbidden:

- raw sample files
- `solve_reports/`
- `.codex-skills/`
- `training_materials/`
- IDA/Ghidra/debugger/emulator/runtime/harness invocation
- `reverse_agent/strategies/`
- `reverse_agent/transforms/` unless only importing existing helpers is necessary and no file modifications occur
- any artifact or state change that marks `cpp1_2f6fcb63` solved

## 7. Tests

必须真实运行并记录到 `project_state/pytest_result.txt`：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m pytest tests/test_local_reverse_cpp1_signed_transform_recheck.py tests/test_local_reverse_cpp1_target_byte_extract.py -q`
- 如果新增 review CLI：`python -m pytest tests/test_local_reverse_cpp1_alternative_static_semantics_review.py -q`
- 若修改 project_state/project_gate：`python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- current source verification：确认 target_bytes_revalidation 和 static_inverse_handoff 均为 current，sample_id 均为 `cpp1_2f6fcb63`，negative_results 中已存在 current printable inverse prohibition
- review command，例如：`python -m reverse_agent.local_reverse_cpp1_alternative_static_semantics_review --target-revalidation project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json --inverse-handoff project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --artifact-index project_state/artifact_index.json --negative-results project_state/negative_results.json --out project_state/local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review.json`
- artifact_index verification：确认 `local_reverse_cpp1_2f6fcb63_alternative_static_semantics_review` 为 current，source_run 为本轮 round id
- 如果更新 negative_results：验证只新增不同方向，不重复 current target bytes printable inverse path
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_cpp1_2f6fcb63_alternative_static_semantics_review_v1`

新增或更新测试覆盖：

- review refuses to run if source revalidation or inverse handoff is not current;
- review records negative_results_considered and does not repeat forbidden printable inverse route;
- review classifies all-byte nonprintable preimage bytes into NUL/whitespace/control/high-bit/printable buckets;
- review keeps candidate null and does not mark solved;
- review writes artifact_index current metadata with dynamic source_run;
- synthetic case can emit `READY_FOR_BOUNDED_RUNTIME_VALIDATION_DECISION` only when no NUL/whitespace hard blocker exists and sources are current.

`close-round` 必须是 live 与 archived pytest 中最后一个 command block。

## 8. Stop Conditions

如果需要执行目标样本、runtime probe、debugger/emulator/hook/harness/bruteforce，立即停止并报告 `BLOCKED`。

如果 current revalidation artifact 或 current static inverse handoff artifact 缺失、不是 current、sample_id 不匹配，停止并报告 `BLOCKED`。

如果工作退化为重复 current target bytes printable inverse path，停止并报告 `REWORK_REQUIRED`。

如果需要重跑 IDA 或重新提取 `byte_429A30`，停止并输出 `NEEDS_TARGET_XREF_TOOL_RECHECK` 或 `NEEDS_TOOL_INTEGRATION_DECISION`，不要在本轮直接跑工具。

如果 artifact_index 无法登记 current alternative review provenance，停止并报告 `REWORK_REQUIRED`，不得只提交裸 JSON。

如果测试或 gate 失败，`codex_execution_report.md` 必须标记 `FAILED/REWORK_REQUIRED` 或 `BLOCKED`，不能写 `SUCCESS/ACCEPTED`。

如果产生 static preview，必须保持 `runtime_validated=false`、`authoritative=false`、`candidate=null`，不得写 solved。若无法保证这一点，停止。

如果需要修改 forbidden paths 或触碰多个样本，停止并报告 `BLOCKED`。
