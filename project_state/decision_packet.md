```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1",
  "round_id": "round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

基于 current 的 `cpp1_2f6fcb63` IDA static triage 产物，对旧 `target_bytes` 与 transform 结果做当前轮 provenance revalidation：复用既有静态结论，核对 sample_id、relative_path、sha256、target symbol/address/length、target bytes、`_main_0` 伪代码、长度约束、copy/transform/compare 语义是否与 current triage 一致，然后生成新的 current revalidation artifact 并登记到 `artifact_index.json`。

本轮主线是 `tool_integration`。目标是把旧 target bytes 结果通过 current triage 一致性校验升级为可审计的当前证据入口，不是重新盲跑 IDA，不是 `reverse_solving`，不是生成 candidate、flag、password，也不是运行样本。

默认不重新提取 `byte_429A30`。只有在旧 target bytes 缺关键字段、与 current triage 明确冲突、或 revalidation 代码无法给出可信结论时，才允许停止并报告 `BLOCKED/REWORK_REQUIRED`，由下一轮单独决定是否重跑 IDA extraction。

## 2. Current Evidence

上一轮 `decision_20260614_gate_status_semantics_rework_v1` 已达到可接受状态：report 绑定该 decision/round，`status=SUCCESS`、`acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`；`report_summary_synthesis.json` 为 `PASSED`，final gate 为 `PASSED_WITH_LIMITATIONS`，blocking reasons 为空，archive 已生成。该工程 gate 语义轮已收口，不应继续围绕 gate 状态语义返工。

`project_state/task_packet.json` 与 `project_state/current_state.json` 仍保留旧 `samplereverse` sample_state 背景：`task_packet.task=collect_missing_evidence`、`sample=samplereverse`、`current_state.workflow_status=REPORT_AVAILABLE`。这些只能作为历史背景，不能覆盖本 decision。当前执行权威是本 `project_state/decision_packet.md`。

`project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 是 current 静态 triage 证据，来自 `round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1`，字段显示：`executed_sample=false`、`static_only=true`、`runtime_validated=false`、`tool_status=success`、`source_tool=IDA`、`queue_rank=1`、`candidate=null`、`known_candidate=""`。该 artifact 可作为当前静态证据入口，但不能被解读为 solved。

current triage 产物中的 `_main_0` decompiler snippet 显示：程序读取 `%s` 到 `Str`，检查 `strlen(Str) != 18`，`strncpy(Destination, Str, 0x10u)`，随后对 `Destination[i]` 应用位运算公式，并与 `byte_429A30[i]` 比较；当 `i == 16` 时输出成功。这与旧 target bytes artifact 的主流程一致。

`project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json` 是旧产物，`generated_at=2026-06-05T09:11:46Z`，含有 `byte_429A30`、target address `0x00429A30`、target length 16、target bytes hex `d596c4f60745577776e5f64847f74817`、`_main_0` 伪代码和 transform 信息。样本没有改变，因此这些静态结果大概率仍有效；问题不是“重新计算”，而是它们缺少当前轮 provenance/freshness。

旧 `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json` 是 reverse_solving 线索，状态为 `BLOCKED`，blocked_reason 为 `STATIC_CANDIDATE_NONPRINTABLE`，candidate 为 null。该 artifact 只能作为 negative context，不能作为当前求解结果。

`reverse_agent/local_reverse_cpp1_target_byte_extract.py` 已存在，包含 target extraction 与 provenance recheck 相关逻辑。不得新建重复 extractor 或第二套 IDA runner。若需要代码改动，应优先在该文件中新增/修正 current revalidation 模式，而不是重跑 extraction。

当前需要避免的偏差：上一个计划把目标写成“重新提取并登记 target bytes”。这会重复已有工作。更合适的工程动作是：使用 current static triage + old target bytes artifact 做一致性校验，生成 `target_bytes_current_revalidation` artifact，并在 `artifact_index.json` 登记 freshness=current、source_run=本轮 round。

`negative_results.json` 仍禁止旧 `sample_solver` 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false candidates 作为主 frontier、提交完整 solve_reports、重复旧 `samplereverse` 失败方向。本轮不触碰这些方向。对 `cpp1_2f6fcb63`，不得重复旧 `STATIC_CANDIDATE_NONPRINTABLE` inverse handoff 方向，除非后续获得新的 current solver decision。

现有能力必须优先复用：IDA / IDAPython / `tool_runners` / `ida_scripts/extract_named_data.py` / `local_reverse_single_sample_static_triage.py` / `local_reverse_cpp1_target_byte_extract.py` / `artifact_index.json` / project_gate closeout。不得重写反汇编器，不得新建第二套 IDA runner。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许有界读取与 `cpp1_2f6fcb63` target bytes revalidation 直接相关的 project_state artifact、现有 extractor、tests 和当前 gate/report 文件。

## 3. Do Not Do

不得运行目标样本二进制；不得做 runtime probe、debugger、emulator、hook、harness campaign、动态验证、bruteforce、SMT、solver、sample_solver 或 candidate validation。

不得默认运行 IDA target extraction。不得因为旧 target bytes 是 stale 就自动重跑 IDA；应先做 current provenance revalidation。

不得生成 candidate、flag、password；不得把 `cpp1_2f6fcb63` 标记为 solved。

不得把旧 `target_bytes.json` 直接改成 current 而没有 revalidation artifact；不得只改 `artifact_index.json` 指向旧文件来假装 current。

不得把旧 inverse handoff 当作 current solved evidence；它只能作为 blocked/negative context。

不得重复实现 IDA、Ghidra、radare2、objdump 的反汇编/反编译功能；本轮只做 artifact provenance、consistency check、artifact_index 登记和测试。

不得新建重复 IDA runner 或重复 `tool_runners` 能力。若需要读取旧 IDA 输出字段，只通过已有 artifact 和现有 extractor 模块处理。

不得修改 raw sample 文件，不得上传本地二进制，不得提交完整 `solve_reports/`。

不得手工伪造 target bytes、伪造 stdout/stderr、伪造 tool success、伪造 artifact freshness。

不得手工修改 `local_reverse_training_status.json` 或 `local_reverse_evaluation_queue.json` 来改变样本状态。若需要读取，只读核验即可。

不得扩大到其他样本；本轮只允许 `cpp1_2f6fcb63`。

不得推进 solver 或 inverse-transform candidate。若 revalidation 成功，下一轮再基于 current revalidation artifact 生成 solver/reverse_solving decision。

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
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`，只作为 stale blocked/negative context
- `project_state/local_reverse_training_status.json`，只读
- `project_state/local_reverse_evaluation_queue.json`，只读
- `project_state/local_reverse_inventory.json`，只读
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- `tests/test_local_reverse_cpp1_target_byte_extract.py`
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

必要时读取但不得修改：

- `reverse_agent/ida_scripts/extract_named_data.py`
- `reverse_agent/tool_runners.py`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/round_manifest.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/codex_execution_report.md`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/pytest_result.txt`

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=tool_integration`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景，不能覆盖本 decision。
- 上一轮 gate semantics round 已收口；本轮不继续工程 gate 语义返工。
- `cpp1_2f6fcb63` current static triage artifact 为 success、source_tool=IDA、runtime_validated=false、candidate=null。
- 旧 target bytes artifact 已有关键 target bytes 和 `_main_0` 伪代码，但不是 current artifact；本轮目标是 revalidation，不是重复 extraction。
- 现有 `local_reverse_cpp1_target_byte_extract.py` 已存在；不得新建重复 extractor/runner。

必须完成或如实报告：

- 在现有 `reverse_agent/local_reverse_cpp1_target_byte_extract.py` 中新增或修正 current revalidation 能力；允许新增 CLI 参数，例如 `--current-revalidation`，但不得把它实现成默认重跑 IDA。
- revalidation 必须读取 current triage artifact 和旧 target bytes artifact，核对 sample_id、relative_path、sha256、target_symbol、target_address、target_length、target_bytes_hex、target_bytes、main_function、长度检查、copy length、transform formula、compare expression。
- 生成新 artifact：`project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`。该 artifact 必须包含 `analysis_mode=target_bytes_current_revalidation`、`mainline=tool_integration`、`executed_sample=false`、`static_only=true`、`runtime_validated=false`、`candidate=null`、`known_candidate=""`、`source_artifacts`、`source_artifact_freshness`、`revalidation_checks`、`revalidation_status`、`target_bytes_hex`、`target_address`、`forward_transform`、`recommended_next_action`。
- 如果所有关键字段一致，`revalidation_status` 应为 `PASSED`，但不得标记 solved；recommended_next_action 应指向“下一轮可基于 current revalidation artifact 做 solver/reverse_solving decision”。
- 如果出现字段缺失或冲突，`revalidation_status` 应为 `BLOCKED` 或 `FAILED`，并明确 `blocked_reason`/`mismatched_fields`；不得自动重跑 IDA 修补。
- `project_state/artifact_index.json` 必须登记新 artifact key，例如 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation`，`freshness=current`，`source_run=round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1`，path 指向新 revalidation artifact，sample_id 为 `cpp1_2f6fcb63`。
- 不得把旧 `local_reverse_cpp1_2f6fcb63_target_bytes.json` 直接改写为 current，除非同时保留 revalidation provenance 并明确说明；优先新增 revalidation artifact，保留旧 target bytes artifact 原样。
- `codex_execution_report.md` 必须明确说明本轮没有重新提取 target bytes、没有运行 IDA、没有运行样本、没有生成 candidate。
- `pytest_result.txt` 必须记录真实命令、stdout/stderr 摘要和 exit code，close-round 仍必须是最后 command block。
- `report_summary_synthesis.json`、`final_gate_result.json`、round archive 必须与 live report/pytest 一致。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- `reverse_agent/project_state.py`，仅限 artifact_index 登记或 lint/doctor 兼容必要修复

Allowed tests:

- `tests/test_local_reverse_cpp1_target_byte_extract.py`
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`，仅当 gate/report contract 受影响时修改

Allowed generated/state files:

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1/*`

Read-only only:

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json`
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_inventory.json`
- `reverse_agent/ida_scripts/extract_named_data.py`
- `reverse_agent/tool_runners.py`
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
- target bytes revalidation command，例如：`python -m reverse_agent.local_reverse_cpp1_target_byte_extract --current-revalidation --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- artifact_index verification：确认 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` 在 `latest_artifacts_v2` 中为 current，path 指向 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`，source_run 为本轮 round id
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_cpp1_2f6fcb63_target_bytes_current_revalidation_v1`

必须新增或更新测试覆盖：

- current revalidation success creates a revalidation artifact without rerunning IDA;
- revalidation writes artifact_index current metadata with dynamic source_run;
- mismatch in sample_id/sha256/target bytes/transform produces blocked or failed revalidation, not success;
- no candidate / known_candidate is produced;
- old target bytes artifact remains unchanged.

`close-round` 必须是 live 与 archived pytest 中最后一个 command block。

## 8. Stop Conditions

如果需要执行目标样本、runtime probe、debugger/emulator/hook/harness/solver/bruteforce，立即停止并报告 `BLOCKED`。

如果 revalidation 发现旧 target bytes 与 current triage 冲突，停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，不得自动重跑 IDA，也不得伪造一致性。

如果 artifact_index 无法登记 current revalidation provenance，停止并报告 `REWORK_REQUIRED`，不得只提交裸 revalidation JSON。

如果测试或 gate 失败，`codex_execution_report.md` 必须标记 `FAILED/REWORK_REQUIRED` 或 `BLOCKED`，不能写 `SUCCESS/ACCEPTED`。

如果发现 current static triage 不是 current 或不属于 `cpp1_2f6fcb63`，停止并报告 `BLOCKED`。

如果需要修改 forbidden paths 或触碰多个样本，停止并报告 `BLOCKED`。
