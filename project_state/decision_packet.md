```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_cpp1_2f6fcb63_target_bytes_current_reextract_v1",
  "round_id": "round_20260614_cpp1_2f6fcb63_target_bytes_current_reextract_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

基于 current 的 `cpp1_2f6fcb63` IDA static triage 产物，重新提取并登记当前轮的 `byte_429A30` target bytes、`_main_0` 伪代码、长度约束、compare expression 与 transform 语义，形成可审计、可复现、可进入后续 solver 的 current StructuredEvidence。

本轮主线是 `tool_integration`。目标是修复/完成现有 target-byte extraction 工具链和 artifact_index 登记，不是 `reverse_solving`，不是生成 candidate、flag、password，也不是运行样本。

如果 IDA 或 extract script 不可用，或者不能提取 `byte_429A30`，必须生成带真实 blocker/provenance 的 blocked artifact，并在 artifact_index 中登记为本轮 current blocked artifact；不得伪造 target bytes 或复用旧 target bytes 当 current。

## 2. Current Evidence

上一轮 `decision_20260614_gate_status_semantics_rework_v1` 已达到可接受状态：当前 report 绑定该 decision/round，`status=SUCCESS`、`acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`；`report_summary_synthesis.json` 为 `PASSED`，final gate 为 `PASSED_WITH_LIMITATIONS`，blocking reasons 为空，archive 已生成。该轮主线已收口，不应继续围绕 gate 状态语义返工。

`project_state/task_packet.json` 与 `project_state/current_state.json` 仍保留旧 `samplereverse` sample_state 背景：`task_packet.task=collect_missing_evidence`、`sample=samplereverse`、`current_state.workflow_status=REPORT_AVAILABLE`。这些只能作为历史背景，不能覆盖本 decision。当前执行权威是本 `project_state/decision_packet.md`。

`project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 是 current 静态 triage 证据，来自 `round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1`，字段显示：`executed_sample=false`、`static_only=true`、`runtime_validated=false`、`tool_status=success`、`source_tool=IDA`、`queue_rank=1`、`candidate=null`、`known_candidate=""`。该 artifact 可作为当前静态证据入口，但不能被解读为 solved。

该 current triage 产物中的 `_main_0` decompiler snippet 显示：程序读取 `%s` 到 `Str`，检查 `strlen(Str) != 18`，`strncpy(Destination, Str, 0x10u)`，随后对 `Destination[i]` 应用位运算公式，并与 `byte_429A30[i]` 比较；当 `i == 16` 时输出成功。该证据说明需要当前 target bytes 和 transform 语义，但还不足以直接提交 candidate。

`project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json` 是旧产物，`generated_at=2026-06-05T09:11:46Z`，虽然含有 `byte_429A30`、target bytes 和 `_main_0` 伪代码，但不是当前 round 产物，不能直接作为本轮 current evidence。旧 inverse handoff 也不能作为 current 求解依据。

`reverse_agent/local_reverse_cpp1_target_byte_extract.py` 已存在，目标是读取 static triage artifact、复用 IDA 的 `extract_named_data.py` 提取 `byte_429A30` 和 `_main_0` pseudocode，并生成 target-bytes artifact。该脚本声明不执行样本、不生成 candidate。不得新建重复 extractor。

当前脚本存在需要审计的工程问题：

- `run_target_byte_extraction()` 生成 target bytes artifact 后看起来没有同步更新 `artifact_index.json`；本轮必须修复，使 `local_reverse_cpp1_2f6fcb63_target_bytes` 在 `latest_artifacts_v2` 中登记为 `freshness=current`，`source_run=round_20260614_cpp1_2f6fcb63_target_bytes_current_reextract_v1`。
- provenance recheck 相关常量 `TARGET_PROVENANCE_SOURCE_RUN` 仍硬编码为旧 round；本轮如果触碰 provenance recheck 逻辑，必须改为从参数或当前 round 推导，不得再写旧 source_run。
- blocked artifact 当前应包含足够 provenance：IDA executable/script resolution、command args、exit code、expected output path、log path/log tail、stdout/stderr 摘要、target symbol、target length。不能只写一个笼统 blocker。

`negative_results.json` 仍禁止旧 `sample_solver` 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false candidates 作为主 frontier、提交完整 solve_reports、重复旧 `samplereverse` 失败方向。本轮不触碰这些方向。对 `cpp1_2f6fcb63`，也不得重复旧 `STATIC_CANDIDATE_NONPRINTABLE` inverse handoff 方向，除非本轮获得 current target bytes 与 transform 证据。

现有能力必须优先复用：IDA / IDAPython / `tool_runners` / `ida_scripts/extract_named_data.py` / `local_reverse_single_sample_static_triage.py` / `local_reverse_cpp1_target_byte_extract.py` / `artifact_index.json` / project_gate closeout。不得重写反汇编器，不得新建第二套 IDA runner。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许有界读取与 `cpp1_2f6fcb63` target bytes re-extraction 直接相关的 project_state artifact、现有 extractor、IDA script、tool_runner、tests 和当前 gate/report 文件。

## 3. Do Not Do

不得运行目标样本二进制；不得做 runtime probe、debugger、emulator、hook、harness campaign、动态验证、bruteforce、SMT、solver、sample_solver 或 candidate validation。

不得生成 candidate、flag、password；不得把 `cpp1_2f6fcb63` 标记为 solved。

不得把旧 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json` 或旧 inverse handoff 当作 current evidence；旧文件只能作为对比线索。

不得重复实现 IDA、Ghidra、radare2、objdump 的反汇编/反编译功能；本轮只修复或增强现有 IDA extraction 编排、provenance、artifact_index 登记和测试。

不得新建重复 IDA runner 或重复 `tool_runners` 能力。若 `_resolve_ida_executable()`、`extract_named_data.py` 或 extractor 参数有缺陷，修复现有接口。

不得修改 raw sample 文件，不得上传本地二进制，不得提交完整 `solve_reports/`。

不得手工伪造 IDA 输出、伪造 `named_data_extract.json`、伪造 target bytes、伪造 stdout/stderr、伪造 tool success。

不得手工修改 `local_reverse_training_status.json` 或 `local_reverse_evaluation_queue.json` 来改变样本状态。若需要读取，只读核验即可。

不得扩大到其他样本；本轮只允许 `cpp1_2f6fcb63`。

不得推进 solver 或 inverse-transform candidate。若 current target bytes 成功提取，下一轮再基于 current evidence 生成 solver/reverse_solving decision。

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

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`，只作为 stale baseline
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`，只作为 stale blocked/negative context
- `project_state/local_reverse_training_status.json`，只读
- `project_state/local_reverse_evaluation_queue.json`，只读
- `project_state/local_reverse_inventory.json`，只读
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- `reverse_agent/ida_scripts/extract_named_data.py`
- `reverse_agent/tool_runners.py`
- `tests/test_local_reverse_cpp1_target_byte_extract.py`
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

必要时读取但不得修改：

- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/round_manifest.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/codex_execution_report.md`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/pytest_result.txt`

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=tool_integration`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景，不能覆盖本 decision。
- 上一轮 gate semantics round 已收口；本轮不继续工程 gate 语义返工。
- `cpp1_2f6fcb63` current static triage artifact 为 success、source_tool=IDA、runtime_validated=false、candidate=null。
- 当前 target bytes artifact 不是 current；必须重新提取或生成 truthful blocked artifact。
- 现有 `local_reverse_cpp1_target_byte_extract.py` 和 `ida_scripts/extract_named_data.py` 已存在；不得新建重复 extractor/runner。

必须完成或如实报告：

- 修复 `run_target_byte_extraction()`，使成功或 blocked 产物都带真实 provenance，并把 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json` 登记到 `project_state/artifact_index.json` 的 `latest_artifacts_v2`，freshness 必须为 `current`，source_run 必须为本轮 round id。
- 若提取成功，artifact 必须包含：sample_id、relative_path、target_symbol、target_address、target_length、target_bytes_hex、target_bytes、main_function、main_function_address、main_pseudocode 摘要、forward_transform、compare_expression、loop_context、evidence_notes、tool_provenance、executed_sample=false、static_only=true、runtime_validated=false、candidate=null、known_candidate=""。
- 若提取 blocked，artifact 必须包含：blocked_reason、IDA/script resolver 结果、command args、exit code、expected output path、log path/log tail、stdout/stderr 摘要、target symbol、expected_target_length，并且 artifact_index 仍登记为 current blocked artifact。
- 如果需要调整 `TARGET_PROVENANCE_SOURCE_RUN` 或相关 artifact_index 更新逻辑，必须使 source_run 动态来自 CLI 参数或当前 decision/round，不得保留旧硬编码 source_run。
- 不得运行 `--provenance-recheck`，除非它依赖的 target_bytes、transform_recheck、signed_transform_recheck、ida_control_flow 四个 source artifact 都是 current；否则只记录 blocked reason，不得把旧依赖提升为 current。
- `codex_execution_report.md` 必须明确说明 target extraction 的 tool outcome：success、blocked 或 partial；不能写 solved。
- `pytest_result.txt` 必须记录真实命令、stdout/stderr 摘要和 exit code，close-round 仍必须是最后 command block。
- `report_summary_synthesis.json`、`final_gate_result.json`、round archive 必须与 live report/pytest 一致。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- `reverse_agent/ida_scripts/extract_named_data.py`，仅限修复现有 named data / function / compare context extraction 输出
- `reverse_agent/tool_runners.py`，仅限现有 IDA executable/script resolution 的兼容修复
- `reverse_agent/project_state.py`，仅限 artifact_index 登记或 lint/doctor 兼容必要修复

Allowed tests:

- `tests/test_local_reverse_cpp1_target_byte_extract.py`
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`，仅当 gate/report contract 受影响时修改

Allowed generated/state files:

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_target_bytes_current_reextract_v1/*`

Read-only only:

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_inventory.json`
- old cpp1 round archives

Forbidden:

- raw sample files
- `solve_reports/`
- `.codex-skills/`
- `training_materials/`
- solver/harness/runtime/debugger/emulator code
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- any new candidate/flag/password artifact
- any change that marks `cpp1_2f6fcb63` solved

## 7. Tests

必须真实运行并记录到 `project_state/pytest_result.txt`：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m pytest tests/test_local_reverse_cpp1_target_byte_extract.py tests/test_local_reverse_single_sample_static_triage.py -q`
- 若修改 project_state/project_gate：`python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- current static triage verification：确认 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 为 current、tool_status=success、candidate=null、runtime_validated=false
- target extraction command：`python -m reverse_agent.local_reverse_cpp1_target_byte_extract --sample-id cpp1_2f6fcb63 --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`
- artifact_index verification：确认 `local_reverse_cpp1_2f6fcb63_target_bytes` 在 `latest_artifacts_v2` 中为 current，path 指向 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`，source_run 为本轮 round id
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_cpp1_2f6fcb63_target_bytes_current_reextract_v1`

必须新增或更新测试覆盖：

- target byte extraction success writes artifact_index current metadata with dynamic source_run;
- blocked extraction still writes artifact and artifact_index current metadata;
- no candidate / known_candidate is produced;
- provenance fields are present when IDA output is missing or parse fails.

`close-round` 必须是 live 与 archived pytest 中最后一个 command block。

## 8. Stop Conditions

如果需要执行目标样本、runtime probe、debugger/emulator/hook/harness/solver/bruteforce，立即停止并报告 `BLOCKED`。

如果 IDA executable 或 `extract_named_data.py` 无法定位，生成 truthful blocked artifact and stop；不得新建重复 runner 或伪造 evidence。

如果 IDA 运行但没有 extraction JSON，必须保留真实 blocker/provenance；不得把空 target bytes 写成 success。

如果 artifact_index 无法登记 current provenance，停止并报告 `REWORK_REQUIRED`，不得只提交裸 target bytes JSON。

如果测试或 gate 失败，`codex_execution_report.md` 必须标记 `FAILED/REWORK_REQUIRED` 或 `BLOCKED`，不能写 `SUCCESS/ACCEPTED`。

如果发现当前 static triage 不是 current 或不属于 `cpp1_2f6fcb63`，停止并报告 `BLOCKED`。

如果需要修改 forbidden paths 或触碰多个样本，停止并报告 `BLOCKED`。
