```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1",
  "round_id": "round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

基于 current 的 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`，生成一份有界静态 inverse-transform handoff artifact：复用现有 `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py` 中的 transform/preimage 计算能力，对 `byte_429A30` 的 16 个 target bytes 做全字节域与可打印 ASCII 域逆变换分析，明确是否存在完整 printable preimage、是否唯一、哪些 byte/index 阻塞，并给出下一步求解路线。

本轮主线是 `reverse_solving`，但仍然是 static-only reverse solving handoff：允许生成静态候选约束或静态候选预览；不得运行样本，不得 runtime validate，不得调用 debugger/emulator/harness，不得把任何结果标记为 solved。

如果 printable preimage 完整且唯一，可以在 artifact 中记录 `static_candidate_preview`，但必须标记 `runtime_validated=false`、`authoritative=false`、`requires_runtime_validation=true`。如果 printable preimage 不完整，artifact 必须为 blocked/needs_alternative_static_review，并记录 missing indices 和每字节全域 preimage 信息；不得重复旧 `STATIC_CANDIDATE_NONPRINTABLE` 方向而不说明 current revalidation 是新增证据。

## 2. Current Evidence

上一轮 `decision_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1` 已达到 `ACCEPTED_WITH_LIMITATIONS`：虽然 report status 为 `PARTIAL`、acceptance_recommendation 为 `NEEDS_REVIEW`，但 revalidation artifact 成功生成，artifact_index 已登记 current，pytest 命令记录完整，close-round 为最后 command block，archive 已创建，blocking reasons 为空。

当前 `project_state/decision_packet.md` 是本轮唯一执行权威。`project_state/task_packet.json` 与 `project_state/current_state.json` 仍保留旧 `samplereverse` 背景，只能作为历史背景；不得回到 `samplereverse` 求解线。

`project_state/artifact_index.json` 当前已登记 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation`：`kind=target_bytes_current_revalidation`，path 为 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`，`freshness=current`，`source_run=round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1`，`sample_id=cpp1_2f6fcb63`。

`project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json` 当前显示：`sample_id=cpp1_2f6fcb63`，relative_path 为 `逆向课程2023春01/CPP1.exe`，sha256 为 `2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede`，`analysis_mode=target_bytes_current_revalidation`，`executed_sample=false`，`runtime_validated=false`，`ida_used_this_round=false`，`candidate=null`，`known_candidate=""`，`revalidation_status=PASSED`。

该 current revalidation artifact 已核对通过：target symbol `byte_429A30`、target address `0x00429A30`、target length 16、target bytes hex `d596c4f60745577776e5f64847f74817`、main function `_main_0`、length check `strlen(Str) != 18`、copy `strncpy(Destination, Str, 0x10u)`、transform formula fragments `& 3` / `& 0xC` / `& 0xF0` / `>> 2`、compare expression `Destination[i] == byte_429A30[i]`。

现有 `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py` 已有可复用函数：`unsigned_formula_transform()`、`signed_instruction_transform()`、`compare_models_all_256()`、`printable_preimages_for_target()`。该文件当前的旧 CLI 路径依赖 target_bytes、ida_control_flow、transform_recheck 三个 artifacts，并且 artifact source_run 常量仍指向旧 round；本轮不得直接把旧 signed_transform artifact 当 current 证据。

`project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json`、`project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json`、旧 inverse handoff artifacts 只能作为 stale/negative context。特别是旧 inverse handoff 的 `STATIC_CANDIDATE_NONPRINTABLE` 不能直接复用为 current 结论；本轮必须从 current revalidation artifact 重新生成静态 inverse handoff。

`negative_results.json` 仍禁止旧 `sample_solver` 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false candidates 作为 primary frontier、提交完整 solve_reports、重复旧 `samplereverse` 失败方向。本轮不能用 blind brute force 或扩大预算绕过证据；只能做 bounded inverse transform over explicitly verified target bytes。

现有能力必须优先复用：`local_reverse_cpp1_signed_transform_recheck.py`、`local_reverse_cpp1_target_byte_extract.py`、artifact_index、project_gate/report-summary/final-check/close-round。不得新建重复 transform solver，不得重写反汇编器，不得新建第二套 IDA runner。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许有界读取与 `cpp1_2f6fcb63` static inverse handoff 直接相关的 project_state artifacts、现有 transform/preimage code、tests 和当前 gate/report 文件。

## 3. Do Not Do

不得运行目标样本二进制；不得做 runtime probe、debugger、emulator、hook、harness campaign、动态验证、bruteforce、SMT、sample_solver 或 candidate validation。

不得运行 IDA、Ghidra、radare2、objdump 或重新提取 target bytes。当前 target bytes 已通过 revalidation，除非发现 revalidation artifact 不一致或 missing，否则本轮不应回到 tool extraction。

不得把任何静态 preimage 直接称为 flag/password/solved answer。不得更新训练状态为 solved。

不得重复旧 `STATIC_CANDIDATE_NONPRINTABLE` inverse handoff 结论而不重新从 current revalidation artifact 计算；如果得到同类 blocked 结论，必须记录本轮 current evidence、具体 missing indices、每字节 preimage 情况和下一步 alternate static review 方向。

不得修改 raw sample 文件，不得上传本地二进制，不得提交完整 `solve_reports/`。

不得手工伪造 candidate、stdout/stderr、tool success 或 artifact freshness。

不得手工修改 `local_reverse_training_status.json` 或 `local_reverse_evaluation_queue.json` 来改变样本状态；只允许只读核验。

不得扩大到其他样本；本轮只允许 `cpp1_2f6fcb63`。

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
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`，只作 current static context
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`，只作 old source context
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`，只作 stale blocked/negative context
- `project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json`，只作 stale context
- `project_state/local_reverse_training_status.json`，只读
- `project_state/local_reverse_evaluation_queue.json`，只读
- `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py`
- `tests/test_local_reverse_cpp1_signed_transform_recheck.py`
- `tests/test_local_reverse_cpp1_target_byte_extract.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

必要时读取但不得修改：

- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- old cpp1 round archives

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=reverse_solving`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景，不能覆盖本 decision。
- current evidence 是 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation`，freshness=current，source_run 为 `round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1`。
- revalidation artifact 的 `revalidation_status=PASSED`，`candidate=null`，`known_candidate=""`，`runtime_validated=false`。
- 现有 `local_reverse_cpp1_signed_transform_recheck.py` 已有 transform/preimage 函数，必须复用；不得新建重复 solver。
- 旧 signed transform / inverse handoff artifacts 不是 current，不能当作当前结论。

必须完成或如实报告：

- 在现有 `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py` 中新增或修正基于 current revalidation artifact 的 static inverse handoff 模式；允许新增 CLI 参数，例如 `--from-revalidation` 或 `--current-revalidation`。
- 新模式必须只读取 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json` 和 `artifact_index.json`，可选读取旧 target/static triage 作为 context，但不得依赖 stale artifacts 作为 required current source。
- 对 target bytes 执行：
  - unsigned formula model over 0..255;
  - signed instruction model over 0..255;
  - printable ASCII 0x20..0x7e preimage search;
  - all-byte 0x00..0xff preimage search;
  - per-index preimage count、printable availability、unique status、missing printable indices。
- 生成新 artifact：`project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`。该 artifact 必须包含 `analysis_mode=static_inverse_transform_handoff`、`mainline=reverse_solving`、`executed_sample=false`、`static_only=true`、`runtime_validated=false`、`source_artifacts`、`source_artifact_freshness`、`transform_models`、`model_equivalence`、`per_byte_preimages`、`printable_preimage_status`、`candidate`、`known_candidate`、`authoritative=false`、`recommended_next_action`。
- 如果 printable preimage 完整且唯一，可以设置 `candidate` 为静态候选预览，但必须设置 `runtime_validated=false`、`authoritative=false`、`requires_runtime_validation=true`，不得标记 solved。
- 如果 printable preimage 不完整，必须设置 `candidate=null`、`known_candidate=""`，`status=BLOCKED` 或 `NEEDS_ALTERNATIVE_STATIC_REVIEW`，并记录 `blocked_reason=NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES` 及 missing indices。
- `project_state/artifact_index.json` 必须登记新 artifact key，例如 `local_reverse_cpp1_2f6fcb63_static_inverse_handoff`，`freshness=current`，`source_run=round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1`，path 指向新 artifact，sample_id 为 `cpp1_2f6fcb63`。
- 如果 blocked 结论确认当前 target bytes 下 printable preimage 不完整，可以有界更新 `project_state/negative_results.json`，加入 `cpp1_2f6fcb63 current target bytes printable inverse path` 的禁止重复方向；必须说明 current evidence 和 missing indices。若未确认，不要更新 negative_results。
- `codex_execution_report.md` 必须明确说明是否生成静态候选预览、是否 blocked、是否修改 negative_results；不能写 solved。
- `pytest_result.txt` 必须记录真实命令、stdout/stderr 摘要和 exit code，close-round 仍必须是最后 command block。
- `report_summary_synthesis.json`、`final_gate_result.json`、round archive 必须与 live report/pytest 一致。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py`
- `reverse_agent/project_state.py`，仅限 artifact_index 或 lint/doctor 兼容必要修复

Allowed tests:

- `tests/test_local_reverse_cpp1_signed_transform_recheck.py`
- `tests/test_local_reverse_cpp1_target_byte_extract.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`，仅当 gate/report contract 受影响时修改

Allowed generated/state files:

- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`，仅当 blocked result 确认需要记录禁止重复方向
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1/*`

Read-only only:

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`
- `project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- old cpp1 round archives

Forbidden:

- raw sample files
- `solve_reports/`
- `.codex-skills/`
- `training_materials/`
- solver/harness/runtime/debugger/emulator code outside the allowed static transform module
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
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
- 若修改 project_state/project_gate：`python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- current revalidation verification：确认 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` 为 current、revalidation_status=PASSED、candidate=null、runtime_validated=false
- static inverse handoff command，例如：`python -m reverse_agent.local_reverse_cpp1_signed_transform_recheck --from-revalidation project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- artifact_index verification：确认 `local_reverse_cpp1_2f6fcb63_static_inverse_handoff` 在 `latest_artifacts_v2` 中为 current，source_run 为本轮 round id
- 若更新 negative_results：negative_results verification，确认仅新增 cpp1 当前 target bytes inverse path 的精确 blocked 方向，不影响旧 entries
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1`

必须新增或更新测试覆盖：

- current revalidation input can drive static inverse handoff without IDA/control-flow artifacts;
- full-byte preimage and printable preimage results are recorded per target byte;
- no complete printable preimage produces blocked/needs-review status, candidate=null, known_candidate="";
- complete unique printable preimage, if tested with synthetic data, produces static candidate preview but not solved/runtime_validated;
- artifact_index uses dynamic current source_run;
- old target bytes and old inverse handoff artifacts remain unchanged.

`close-round` 必须是 live 与 archived pytest 中最后一个 command block。

## 8. Stop Conditions

如果需要执行目标样本、runtime probe、debugger/emulator/hook/harness/bruteforce，立即停止并报告 `BLOCKED`。

如果 current revalidation artifact 缺失、不是 current、sample_id 不匹配、或 `revalidation_status != PASSED`，停止并报告 `BLOCKED`。

如果 existing transform/preimage functions cannot be reused and would require new solver architecture, stop and report `REWORK_REQUIRED`; 不得新建重复 solver。

如果 artifact_index 无法登记 current inverse handoff provenance，停止并报告 `REWORK_REQUIRED`，不得只提交裸 JSON。

如果测试或 gate 失败，`codex_execution_report.md` 必须标记 `FAILED/REWORK_REQUIRED` 或 `BLOCKED`，不能写 `SUCCESS/ACCEPTED`。

如果生成 static candidate preview，必须保持 `runtime_validated=false`、`authoritative=false`，不得写 solved。若无法保证这一点，停止。

如果需要修改 forbidden paths 或触碰多个样本，停止并报告 `BLOCKED`。
