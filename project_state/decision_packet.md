```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_samplereverse_bounded_static_evidence_rebuild_v1",
  "round_id": "round_20260613_samplereverse_bounded_static_evidence_rebuild_v1",
  "based_on_state_build_id": "state_20260612_171323_ec5629036418",
  "based_on_state_digest": "ec562903641803f5e09f2a956d1adcc687f281867d8a442e3d58c384fa91797d",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮只做 `samplereverse` 的**有界静态证据重建与 artifact freshness 修复**，为后续 solver/候选验证恢复 current 证据基础。

当前状态显示 `artifact_index.json` 中关键 sample-solving artifact 大量为 `missing`，`case_results/frontier_summary/runtime_validation/strata_summary/summary` 也缺失。因此下一步不是继续猜 candidate，也不是扩大搜索预算，而是使用已有工具接口重新生成或明确记录当前可用的静态证据，并把 provenance/freshness 写回 `project_state`。

本轮允许做的目标：

1. 基于现有仓库能力确认 `samplereverse` 当前样本路径、工具配置和可运行性。
2. 使用已有静态工具链能力收集 current 静态证据：优先 IDA/IDAPython 静态提取；若 IDA 不可用，则使用已有 pure-Python static extractor 生成受限静态特征，并明确标记 IDA 未执行原因。
3. 将新证据以小型 project_state 摘要或 artifact_index 条目登记，标记 `freshness=current`、source/provenance、sha256、size、source_run。
4. 只形成证据摘要和下一步 solver 前置条件，不生成 flag/password/candidate，不运行 runtime probe。

本轮不解决样本，不做动态调试，不运行 harness campaign，不启动 solver。

## 2. Current Evidence

- 主线：`reverse_solving`。本轮回到样本证据主线，但范围只限静态证据重建，不进入 candidate search。
- `task_packet.json` 只能作为建议；当前轮执行权威是本 `project_state/decision_packet.md`。
- `current_state.json` 摘要：sample=`samplereverse`，profile=`samplereverse`，active_strategy=`CompareAwareSearchStrategy`，known_transform=`input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`，review_status=`PENDING_REVIEW`。
- `current_state.json` 当前 state build 为 `state_20260612_171323_ec5629036418`，digest 为 `ec562903641803f5e09f2a956d1adcc687f281867d8a442e3d58c384fa91797d`。
- `artifact_index.json` 中 `latest_artifacts_v2` 的关键条目为 `missing`，包括 `frontier_summary`、`function_semantic_audit`、`guided_pool_validation`、`material_hook_runtime_validation`、`pre_rc4_material_probe`、`strata_summary`、`summary`、`transform_trace_consistency` 等。
- `artifact_index.json` 的 `latest_case_results=[]`，`latest_summary=null`，`missing=[case_results, frontier_summary, runtime_validation, strata_summary, summary]`。
- 旧 `latest_harness_run=solve_reports\\harness_runs\\samplereverse_material_hook_runtime_validation_20260512_rerun6` 只能作为历史线索，不能当 current evidence。
- `negative_results.json` 明确禁止：旧 `sample_solver` blind search、单纯扩大 beam/budget、使用 `compare_semantics_agree=false` candidate 作为 primary frontier、提交完整 `solve_reports`、重复 exact2 basin value-pool、重复 H1/H3 fixed contrast set、无新 runtime evidence 重复 transform trace consistency audit。
- skill profiles：`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 和 `samplereverse-frontier@v2` 均为 active。
- 已有能力检查结果：
  - IDA/IDAPython：已有 `tool_runners.py` IDA runner、`ida_scripts/`、IDA JSON evidence ingestion、StructuredEvidence 转换，不得新建重复 IDA runner。
  - Ghidra：当前 inventory 标记为 missing，不得假设已有 Ghidra runner。
  - OllyDbg/debugger：已有 runner/preflight/scripts，但本轮不允许运行动态调试。
  - strings/static extraction：已有 `static_feature_extractor.py`，可做不执行样本的静态字符串、UTF-16LE、关键字、常量和 Base64-like hints 提取。
  - solver：已有 `sample_solver.py`、`local_reverse_solver_profiles.py`、`samplereverse_z3.py`、`advanced_solvers.py` 等，本轮不得运行。
  - symbolic/constraint solver：已有 Z3/angr/constraint recovery 能力，本轮不得运行。
  - harness：已有 `harness.py` 与 case result/run manifest 输出，本轮不得启动 campaign。
  - artifact_index：已有 freshness/current/stale/missing 机制，本轮必须复用。
  - StructuredEvidence：已有 `evidence.py` 和 `tool_runners.py` ingestion，本轮可复用，不得重写。
- 是否允许运行工具：允许仅运行不执行样本的静态提取；允许 IDA headless/static evidence extraction，前提是使用现有 runner/script 且不执行样本逻辑。禁止 OllyDbg/x64dbg/debugger/runtime probe/harness/solver。
- 是否允许读取重型 artifact：默认不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取 artifact_index 指向的必要小型 JSON 元数据；如路径 missing/stale，则不得强行打开历史目录。

## 3. Do Not Do

- 不运行旧 `sample_solver` blind search。
- 不扩大 beam、topN、budget、timeout 来碰运气。
- 不生成 candidate、flag、password 或最终答案。
- 不使用 `compare_semantics_agree=false` 候选作为主 frontier。
- 不重复 exact2 basin value-pool 或 H1/H3 fixed contrast set。
- 不在没有新 runtime evidence 的情况下重复 transform trace consistency audit。
- 不运行 OllyDbg、x64dbg、debugger、emulator、runtime probe、CompareProbe、material hook、breakpoint probe。
- 不运行 harness campaign，不做 runtime validation。
- 不运行 solver、Z3、angr、constraint recovery。
- 不读取完整 `solve_reports/`。
- 不读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不提交完整 `solve_reports/`。
- 不提交 raw sample、IDA database、debug trace、大体积二进制产物。
- 不修改 `.codex-skills/`。
- 不新建重复 IDA/Ghidra/debugger/solver/harness 接口。
- 不把 stale/missing artifact 当 current evidence。
- 不用历史 `latest_harness_run` 结论替代本轮 current 静态证据。

## 4. Files To Inspect

必须读取：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `reverse_agent/tool_capability_inventory.py`
- `reverse_agent/tool_runners.py`
- `reverse_agent/static_feature_extractor.py`
- `reverse_agent/evidence.py`
- `reverse_agent/ida_scripts/collect_evidence.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- 与 artifact_index 更新、tool evidence ingestion、static feature extraction 直接相关的测试文件

可有界读取：

- `project_state/tool_capability_inventory.json`（若存在）
- `project_state/structured_evidence_gap_report.json`（若存在）
- `project_state/gates/final_gate_result.json`
- 当前 round 需要生成或更新的小型 project_state 证据摘要
- artifact_index 指向且 freshness/provenance 可确认的小型 JSON artifact

不得默认读取：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- raw local samples 之外的大体积历史 archive
- 历史 debug trace / IDA database / dumped memory

## 5. Required Audit

Codex 必须先完成以下审计，再执行任何证据重建：

1. 确认工作目录为 `F:\reverse-agent`，并记录 `pwd` / `Test-Path F:\reverse-agent` / `git rev-parse --show-toplevel` / `git status --short`。
2. 解析本 `decision_packet.md` 的 `decision_meta`：status 必须为 `APPROVED`，mainline 必须为 `reverse_solving`，skill profiles 必须来自 active registry。
3. 明确记录 `task_packet.json` 只是 advisory，本轮以 decision_packet 为准。
4. 检查 `negative_results.json`，确认本轮不重复 forbidden directions。
5. 检查已有工具接口：IDA runner、IDA script、tool_runners ingestion、static_feature_extractor、artifact_index、StructuredEvidence、harness/solver/debugger 接口是否已存在；不得重复实现。
6. 检查 IDA 可用性：
   - 若 IDA executable 和 `ida_scripts/collect_evidence.py` 可用，只允许通过现有 IDA runner 做 headless/static evidence extraction。
   - 若 IDA 不可用，不得补造 runner；记录 blocker，并使用已有 pure-Python `static_feature_extractor.py` 做 fallback 静态摘要。
7. 检查样本定位：必须从现有状态、metadata 或已有配置中定位 `samplereverse`；如果样本路径缺失或不可访问，停止证据重建并写明 blocker，不得猜路径。
8. 新产物必须进入 artifact_index 或 project_state 小型摘要，并标记 provenance、freshness、sha256、size_bytes、source_run。
9. 若仅得到 static feature fallback，不得声称 IDA 已证明，也不得声称 runtime_validation 已完成。
10. 本轮报告必须明确区分：current static evidence、missing runtime evidence、historical stale evidence。

## 6. Implementation Scope

允许修改或生成：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/model_gate.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260613_samplereverse_bounded_static_evidence_rebuild_v1/*`
- 小型 evidence summary，例如 `project_state/samplereverse_static_evidence_rebuild_summary.json` 或项目已有等价路径

允许由现有工具生成但不提交完整内容：

- `solve_reports/` 下本轮 bounded static extraction 的小型 JSON 输出，前提是只在 `artifact_index.json` 中登记路径、sha256、size、source_run，不提交完整 `solve_reports/`。

只有在发现现有 schema 无法登记本轮静态证据时，才允许小范围修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- 与 artifact_index 登记/静态证据摘要直接相关的最小测试

不允许修改：

- `.codex-skills/`
- `solve_reports/` 的完整历史内容
- `PROJECT_PROGRESS_LOG.txt`
- `reverse_agent/harness.py`
- `reverse_agent/sample_solver.py`
- `reverse_agent/local_reverse_solver_profiles.py`
- `reverse_agent/samplereverse_z3.py`
- `reverse_agent/advanced_solvers.py`
- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/olly_scripts/`
- `reverse_agent/ida_scripts/`（除非只是读取，不修改）
- raw sample / sample binary
- GUI 无关模块
- training queue/status/capability review 文件

## 7. Tests

必须真实运行并完整记录 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state build
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m pytest tests/test_project_state.py tests/test_project_gate.py tests/test_tool_capability_inventory.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

如果本轮实际修改了 `reverse_agent/project_state.py` 或新增 artifact_index 相关测试，还必须运行对应新增测试或包含它们的 pytest 子集。

如果执行了 IDA/static extraction，还必须在 `codex_execution_report.md` 中记录：

- tool name
- command 或调用入口
- attempted/success/error
- output path
- sha256
- size_bytes
- artifact_index freshness
- 是否产生 StructuredEvidence

验收条件：

- preflight 必须通过。
- pytest 必须通过。
- `project_state build` 必须成功。
- `doctor` 不得出现阻塞性 FAIL。
- `final-check` 不得出现 blocking_reasons。
- 新 static evidence 或 fallback summary 必须可追溯并登记。
- 若 IDA 不可用，报告必须是 `SUCCESS` 或 `PARTIAL` 的受限状态，并明确 blocker；不得伪造 IDA current evidence。
- 若样本路径不可定位，必须停止证据重建并报告 `BLOCKED`，不得猜路径或转向 solver。

## 8. Stop Conditions

遇到以下情况必须停止并写入 `codex_execution_report.md`，不得继续扩大范围：

- `decision_meta` 缺失、不合法、status 不是 `APPROVED`。
- skill profile 不在 active registry 中。
- 工作目录不是 `F:\reverse-agent`。
- 样本路径无法从现有状态/metadata/config 中定位。
- IDA 不可用且 pure-Python static extractor 也无法对样本读取。
- 需要运行动态调试、runtime probe、harness campaign、solver 或 candidate search 才能继续。
- 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt` 才能继续。
- artifact_index 无法登记新产物 provenance/freshness。
- 新证据与 negative_results 禁止方向冲突。
- 发现已有 IDA/Ghidra/debugger/solver/harness 接口已能完成任务，但本轮实现试图重复造轮子。
