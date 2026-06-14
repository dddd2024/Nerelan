```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1",
  "round_id": "round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

恢复本地训练队列 rank=1 样本 `cpp1_2f6fcb63` 的有界静态证据提取闭环：审计并修复现有 `reverse_agent/local_reverse_single_sample_static_triage.py` 复用 IDA/tool_runners/collect_evidence 的路径，使它能够为 `cpp1_2f6fcb63` 生成可信、可登记、可审计的 current static triage artifact；如果 IDA 或脚本环境仍不可用，必须生成带真实 blocker、exit/log/provenance 的 blocked artifact，不得合成 stdout 或伪造成功。

本轮主线是 `tool_integration`，不是 `reverse_solving`。目标是工具接入与 StructuredEvidence/static triage 产物登记，不是生成 candidate、flag、password，也不是运行样本。

## 2. Current Evidence

当前上一轮 `decision_20260614_close_round_recording_real_execution_rework_v1` 已达到 `ACCEPTED_WITH_LIMITATIONS`：report/pytest/gate/archive 已绑定同一 decision/round，`close-round` 是最后 command block，live 与 archived pytest/report 一致。遗留 warning 属于非阻塞 gate limitation，final gate recommended_next_action 为 `no_action_required`。

`project_state/task_packet.json` 与 `project_state/current_state.json` 仍包含旧 `samplereverse` sample_state 背景，只能作为历史背景；当前轮执行权威是本 decision。不得根据旧 `task_packet.task=collect_missing_evidence` 回到 `samplereverse` 求解线。

`project_state/local_reverse_evaluation_queue.json` 当前显示：`cpp1_2f6fcb63` 是 rank=1，relative_path 为 `逆向课程2023春01/CPP1.exe`，`proposed_next_mainline=tool_integration`，allowed_actions 只有 `static_triage`，forbidden_actions 包含 `runtime_probe`、`bruteforce`、`upload_binary`。

`project_state/local_reverse_training_status.json` 当前显示训练集总计 65 个样本，`solved=1`、`blocked=2`、`needs_triage=3`、`inventory_only=59`。`cpp1_2f6fcb63` 在只读核验中为 `rank=1, training_status=inventory_only`。

已有与 `cpp1_2f6fcb63` 相关的旧产物和脚本不能被当作 current success evidence：

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 是旧 blocked artifact，`generated_at=2026-06-12T07:10:53Z`，`tool_status=blocked`，`blocked_reason=STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`。
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json` 是旧 reverse_solving 线索，状态为 `BLOCKED`，原因是 `STATIC_CANDIDATE_NONPRINTABLE`；本轮不能把它作为 candidate 或求解依据。
- `reverse_agent/local_reverse_single_sample_static_triage.py` 已存在，并声明只复用 IDA 静态 evidence collection，不执行目标二进制、不生成 candidate。其 `_run_ida_static_triage()` 通过 `tool_runners._resolve_ida_executable()` 和 `_resolve_ida_script()` 启动 IDA，并期望 `REVERSE_AGENT_IDA_OUT` 产出 `ida_evidence.json`。
- 当前 adapter 在 `evidence_out` 不存在时只返回 `STATIC_TOOL_NO_OUTPUT`，但 blocked artifact 里没有足够的 IDA command、log path、exit code、stdout/stderr 摘要、script path、output path 等 provenance，导致后续无法判断是 IDA runner、脚本、路径、环境变量还是输出登记问题。
- `run_static_triage()` 接受 `artifact_index_path` 参数，但需要审计是否真实更新 `artifact_index.json`；本轮必须确保工具输出进入 artifact_index 并标记 current provenance，不能只写裸 JSON。

`negative_results.json` 禁止回到旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 `samplereverse` 失败方向。本轮不触碰这些方向。对 `cpp1_2f6fcb63`，还必须避免重复旧 `STATIC_CANDIDATE_NONPRINTABLE` inverse handoff 方向，除非本轮获得新的 current static triage evidence。

现有工具能力必须优先复用：IDA / IDAPython / `tool_runners` / `collect_evidence.py` / `local_reverse_single_sample_static_triage.py` / training inventory and queue / project_gate report-summary/final-check/close-round。不得新建重复 IDA runner，不得绕过成熟工具重新写反汇编器。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许有界读取与 `cpp1_2f6fcb63` 当前静态 triage 直接相关的 project_state 产物、上一轮对应 round manifest/report/pytest、现有 IDA/tool_runner/triage adapter 代码和测试。

## 3. Do Not Do

不得运行目标样本二进制；不得做 runtime probe、debugger、emulator、hook、harness campaign、动态验证、bruteforce、SMT、solver、sample_solver 或 candidate validation。

不得生成 candidate、flag、password；不得把 `cpp1_2f6fcb63` 标记为 solved。

不得回到旧 `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json` 的非打印 candidate 分支；该 artifact 只能作为 stale/blocked 线索，不是 current evidence。

不得重复实现 IDA、Ghidra、radare2、objdump 已有的反汇编/反编译功能；本轮只修复/增强现有工具编排、产物登记和 blocked provenance。

不得新建第二套 IDA runner 或重复 `tool_runners` 的能力。若现有 `_resolve_ida_executable()` / `_resolve_ida_script()` / `collect_evidence.py` 有缺陷，修复现有接口。

不得修改 raw sample 文件，不得上传本地二进制，不得提交完整 `solve_reports/`。

不得手工伪造 IDA 输出、伪造 `ida_evidence.json`、伪造 stdout/stderr、伪造 tool success。

不得手工编辑 `local_reverse_training_status.json` 或 `local_reverse_evaluation_queue.json` 来掩盖状态；如需更新训练状态/队列，必须通过现有生成器或明确的小范围状态构建命令产生，并在 report 中记录命令。

不得把 stale/missing artifact 当作 current evidence。若 current static triage 仍 blocked，报告必须是 blocked/partial 的真实状态，而不是 SUCCESS 解题状态。

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

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_inventory.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`，若存在，只能作为 stale/blocked baseline
- `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`，若存在，只能作为 stale/blocked negative context
- `training_materials/local_reverse/cases/cpp1_2f6fcb63.json`，若存在，只读 sample metadata，不改 training_materials
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/tool_runners.py`
- 现有 IDAPython evidence collection script；通过 `tool_runners._resolve_ida_script()` 或代码搜索定位，不得新建重复脚本
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_local_reverse_training_status.py`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`

必要时读取上一轮或历史 `cpp1_2f6fcb63` round：

- `project_state/rounds/round_20260612_local_reverse_cpp1_2f6fcb63_static_triage_v1/decision_packet.md`
- `project_state/rounds/round_20260612_local_reverse_cpp1_2f6fcb63_static_triage_v1/codex_execution_report.md`
- `project_state/rounds/round_20260612_local_reverse_cpp1_2f6fcb63_static_triage_v1/pytest_result.txt`
- `project_state/rounds/round_20260612_rework_cpp1_2f6fcb63_static_triage_closeout_v1/round_manifest.json`

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=tool_integration`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景，不能覆盖本 decision。
- `cpp1_2f6fcb63` 在 evaluation queue 中为 rank=1，且 allowed_actions 只有 `static_triage`。
- 现有 `local_reverse_single_sample_static_triage.py` 明确不执行目标样本、不生成 candidate。
- 现有 IDA/tool_runner/collect_evidence 接口是否已经存在；不得新建重复 runner。
- 旧 static triage artifact blocked due to `STATIC_TOOL_NO_OUTPUT`；若要重试，必须说明新增审计和修复点。
- artifact_index 是否已有 `cpp1_2f6fcb63` 条目；若没有或 stale/missing/unknown，本轮必须在生成 artifact 后登记 current provenance。

必须完成或如实报告：

- 审计 `_run_ida_static_triage()` 的 command、env、script path、output path、log path、db path 和 exit code 记录；blocked artifact 必须包含足够 provenance 让下一轮知道为什么没有 evidence JSON。
- 若 IDA executable 或 script 不可用，生成 blocked artifact，blocked_reason 必须区分 `STATIC_TOOL_UNAVAILABLE: IDA executable not found` 与 `STATIC_TOOL_UNAVAILABLE: IDA script not found`，并记录 resolver inputs/outputs。
- 若 IDA 运行但没有 `ida_evidence.json`，blocked artifact 必须记录 exit_code、log path、stdout/stderr 摘要、expected evidence path、script path、db path，以及是否存在 IDA log。
- 若 IDA 成功产生 evidence JSON，生成 compact static triage artifact，包含 strings/functions/compare_contexts/validation_function_candidates/solver_profile_hypotheses/decompiler_snippets/solver_hints，且 `candidate=null`、`known_candidate=''`、`runtime_validated=false`。
- 不论 success 还是 blocked，`project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 必须更新为本轮 current artifact，并在 `project_state/artifact_index.json` 中登记 freshness=current、kind、path、sha256、size_bytes、source_run=`round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1`。
- 若训练状态/队列需要刷新，必须通过现有生成器或明确命令生成，不得手工修补；若当前状态仍应是 `inventory_only` 或 `needs_triage`，必须在 report 中说明依据。
- `codex_execution_report.md` 必须明确区分：工具接入成功、静态 triage artifact success、静态 triage artifact blocked、或环境 blocked。不得把 blocked triage 写成 solved。
- `pytest_result.txt` 必须记录真实命令、stdout/stderr 摘要和 exit code。不得合成日志。
- `project_state/gates/report_summary_synthesis.json`、`final_gate_result.json`、round archive 必须和 live report/pytest 一致。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/tool_runners.py`，仅限修复现有 IDA executable/script resolution 或暴露更清晰 provenance
- 现有 IDAPython evidence collection script，路径必须由 `tool_runners` 解析确认；仅限修复 evidence JSON 输出，不得新建重复 runner
- `reverse_agent/project_state.py`，仅限 artifact_index/status 构建必要的兼容修复

Allowed tests:

- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_local_reverse_training_status.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`，仅当 report/gate contract 受影响时修改

Allowed generated/state files:

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/artifact_index.json`
- `project_state/local_reverse_training_status.json`，仅允许由现有状态生成器更新
- `project_state/local_reverse_evaluation_queue.json`，仅允许由现有队列生成器更新
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/*`

Read-only only:

- `project_state/local_reverse_inventory.json`
- `training_materials/local_reverse/cases/cpp1_2f6fcb63.json`
- old `project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json`
- old cpp1 round archives

Forbidden:

- raw sample files
- `solve_reports/`
- `.codex-skills/`
- `training_materials/` writes
- solver/harness/runtime/debugger/emulator code
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- any new candidate/flag/password artifact
- any change that marks `cpp1_2f6fcb63` solved

## 7. Tests

必须真实运行并记录：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m pytest tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py -q`
- 若修改了 project_state/project_gate：`python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- 只读 queue/inventory verification：确认 `cpp1_2f6fcb63 rank=1`、relative_path、allowed_actions/forbidden_actions、training_status
- tool capability verification：确认 IDA executable/script resolver 结果；不得输出本地敏感路径到长期 skill，但可以在 report/pytest 中记录必要路径摘要
- `python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp1_2f6fcb63 --mainline tool_integration --out project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- artifact_index verification：确认 cpp1 static triage artifact 登记为 current，source_run 为本轮 round_id
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1`

如果 IDA 不可用或输出缺失，static triage command 仍可 exit 0 only if it writes a truthful blocked artifact; report must mark tool outcome as blocked/partial, not solved. If command exits nonzero, record it and stop with `BLOCKED` or `REWORK_REQUIRED`.

`close-round` 必须是 live 与 archived pytest 中最后一个 command block。

## 8. Stop Conditions

如果需要执行目标样本、runtime probe、debugger/emulator/hook/harness/solver/bruteforce，立即停止并报告 `BLOCKED`。

如果 IDA runner 或 script 无法定位，生成 truthful blocked artifact and stop; 不得新建重复 runner 或伪造 evidence。

如果 IDA 运行但没有 evidence JSON，必须保留真实 blocker/provenance；不得把空 triage 写成 success。

如果 artifact_index 无法登记 current provenance，停止并报告 `REWORK_REQUIRED`，不得只提交裸 triage JSON。

如果测试或 gate 失败，`codex_execution_report.md` 必须标记 `FAILED/REWORK_REQUIRED` 或 `BLOCKED`，不能写 `SUCCESS/ACCEPTED`。

如果发现旧 inverse handoff 方向仍然是唯一证据，停止；本轮不得用它求解。

如果需要修改 forbidden paths 或触碰多个样本，停止并报告 `BLOCKED`。
