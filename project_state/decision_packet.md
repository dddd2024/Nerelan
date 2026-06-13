```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_samplereverse_path_resolution_static_evidence_v2",
  "round_id": "round_20260613_samplereverse_path_resolution_static_evidence_v2",
  "based_on_state_build_id": "state_20260613_051950_55a40c6e6bd4",
  "based_on_state_digest": "55a40c6e6bd4a2240c43d0e377f79f33d5d405c444255cefecb2bfe0dab872d0",
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

本轮只做 `samplereverse` 的**具体样本路径解析 + 有界静态证据重建**，修复上一轮 BLOCKED 的根因：Codex 只知道本地样本根目录 `E:\reverse`，但没有定位到具体样本文件。

用户已补充新约束：

- `samplereverse` 的样本根目录在 `E:\reverse`。
- 这只是根目录，不等于具体样本文件路径。
- Codex 不得再因为“没有 `samples/samplereverse.exe` 或文件名不含 samplereverse”直接停止；必须先按本决策的有界规则枚举和识别候选文件。

本轮目标分两阶段：

1. **样本路径解析阶段**：在 `E:\reverse` 下用已有 inventory/static 能力定位具体 `samplereverse` 样本文件，记录候选、证据、排除原因和最终选择。
2. **静态证据阶段**：仅在唯一定位到具体样本文件后，使用已有 IDA/IDAPython 或 pure-Python static extractor 做不执行样本的静态证据提取，并写入 project_state 小型摘要。若不能唯一定位，则停止并列出候选，不进入 solver/runtime/harness。

本轮不解题，不生成 flag/password/candidate，不运行动态调试，不运行 harness campaign，不运行 solver。

## 2. Current Evidence

- 主线：`reverse_solving`，但范围只限样本路径解析与静态证据重建。
- 当前执行权威是本 `project_state/decision_packet.md`；`task_packet.json` 只能作为 advisory。
- `current_state.json` 摘要：sample=`samplereverse`，profile=`samplereverse`，active_strategy=`CompareAwareSearchStrategy`，known_transform=`input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`。
- 当前 state build 为 `state_20260613_051950_55a40c6e6bd4`，digest 为 `55a40c6e6bd4a2240c43d0e377f79f33d5d405c444255cefecb2bfe0dab872d0`。
- `artifact_index.json` 仍显示关键样本解题 artifact 为 `missing`：`case_results/frontier_summary/runtime_validation/strata_summary/summary` 等均缺失。
- `artifact_index.json` 中旧 `latest_harness_run=solve_reports\harness_runs\samplereverse_material_hook_runtime_validation_20260512_rerun6` 只能作为历史线索，不能当 current evidence。
- `negative_results.json` 禁止：旧 `sample_solver` blind search、单纯扩大 beam/budget、使用 `compare_semantics_agree=false` candidate 作为 primary frontier、提交完整 `solve_reports`、重复 exact2 basin value-pool、重复 H1/H3 fixed contrast set、无新 runtime evidence 重复 transform trace consistency audit。
- skill profiles：`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 和 `samplereverse-frontier@v2` 均为 active。
- 已有工具能力：
  - IDA/IDAPython 已有 runner、IDA scripts、IDA JSON evidence ingestion、StructuredEvidence 转换，不得新建重复接口。
  - Ghidra 当前未接入，不得假设已有 Ghidra runner。
  - OllyDbg/x64dbg/debugger 已有接口，但本轮禁止动态执行。
  - `reverse_agent/static_feature_extractor.py` 已有 pure-Python 静态提取能力。
  - `reverse_agent/local_reverse_inventory.py` 已有本地样本 inventory 扫描能力，默认根目录就是 `E:/reverse`，本轮可复用，但只允许生成 project_state 下 metadata。
  - `reverse_agent/profiles/samplereverse.py` 已有 `_looks_like_samplereverse()` 逻辑：文件名包含 samplereverse，或字符串中同时出现 `输入的密钥是` 与 `密钥不正确`，可作为静态识别依据。
  - solver、symbolic、harness 均已存在，但本轮不得运行。

关键约束修正：

- 上一轮 decision 把 `solve_reports/` 写进允许生成范围，触发 `project_gate preflight` 的 `forbidden_paths_not_allowed`。本轮明确**不允许写入或提交 `solve_reports/`**，静态证据摘要只写入 `project_state/`。
- 上一轮报告使用了非法 `acceptance_recommendation=NOT_ACCEPTED` 和非法 `pytest_result_summary.status=BLOCKED`。本轮报告必须使用项目允许值：BLOCKED 报告的 `acceptance_recommendation` 写 `BLOCKED`；pytest summary 的 `status` 只能写 `PASSED`、`FAILED`、`PARTIAL` 或 `UNKNOWN`。

## 3. Do Not Do

- 不运行旧 `sample_solver` blind search。
- 不运行任何 candidate search、candidate validation、flag/password 求解。
- 不扩大 beam、topN、budget、timeout。
- 不使用 `compare_semantics_agree=false` candidate 作为主 frontier。
- 不重复 exact2 basin value-pool、H1/H3 fixed contrast set、transform trace consistency audit。
- 不运行 OllyDbg、x64dbg、debugger、emulator、runtime probe、CompareProbe、material hook、breakpoint probe。
- 不运行 harness campaign，不做 runtime validation。
- 不运行 solver、Z3、angr、constraint recovery。
- 不读取完整 `solve_reports/`。
- 不读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不写入或提交完整 `solve_reports/`。
- 不提交 raw sample、sample binary、IDA database、debug trace、大体积二进制产物。
- 不修改 `.codex-skills/`。
- 不修改 `training_materials/`，不要用 inventory 默认 `--github-out` 或 `--cases-dir` 生成训练集文件。
- 不新建重复 IDA/Ghidra/debugger/solver/harness 接口。
- 不把 stale/missing artifact 当 current evidence。
- 不把“E:\reverse 存在”直接等同于“samplereverse 样本已定位”。

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
- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/static_feature_extractor.py`
- `reverse_agent/profiles/samplereverse.py`
- `reverse_agent/tool_capability_inventory.py`
- `reverse_agent/tool_runners.py`
- `reverse_agent/evidence.py`
- `reverse_agent/ida_scripts/collect_evidence.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- 与 project_state 小型摘要、sample path resolution、static evidence summary 直接相关的测试

可有界读取：

- `project_state/local_reverse_inventory.json`，若存在
- `project_state/tool_capability_inventory.json`，若存在
- `project_state/structured_evidence_gap_report.json`，若存在
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_samplereverse_path_resolution_static_evidence_v2/*`
- `project_state/samplereverse_sample_path_resolution.json`，若本轮生成
- `project_state/samplereverse_static_evidence_rebuild_summary.json`，若本轮生成

不得默认读取：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- raw sample 的完整内容向报告输出
- 历史 debug trace / IDA database / dumped memory

## 5. Required Audit

Codex 必须先完成以下审计，再做静态证据：

1. 确认当前目录为 `F:\reverse-agent`，并记录 `pwd` / `Test-Path F:\reverse-agent` / `git rev-parse --show-toplevel` / `git status --short`。
2. 解析本 decision 的 `decision_meta`：status 必须为 `APPROVED`，mainline 必须为 `reverse_solving`，skill profiles 必须 active。
3. 明确记录 `task_packet.json` 只是 advisory，本轮以 decision_packet 为准。
4. 检查 `negative_results.json`，确认本轮不重复 forbidden directions。
5. 检查已有工具接口：IDA runner、IDA script、static_feature_extractor、local_reverse_inventory、artifact_index、StructuredEvidence、harness/solver/debugger 接口是否已存在；不得重复实现。
6. 检查样本根目录：
   - `Test-Path E:\reverse` 必须为 True。
   - 若 False，报告 BLOCKED，block_reason=`local_reverse_root_missing`。
7. 运行有界样本路径解析：
   - 优先复用 `reverse_agent.local_reverse_inventory.scan_samples()`，只写 `project_state/local_reverse_inventory.json`，不得写 `training_materials/`。
   - 从 inventory 中筛选 PE/可执行候选：`.exe/.dll/.sys/.com` 或 `guessed_file_type=pe`。
   - 对候选执行不运行样本的静态识别：文件名、PE/MZ magic、ASCII/UTF-16LE 字符串、`输入的密钥是`、`密钥不正确`、`flag{`、RC4/Base64 关键字、`SAMPLEREVERSE_ENC_CONST` 片段或 profile detection score。
   - 若只有一个候选满足 `samplereverse` profile evidence，记录为 selected sample。
   - 若多个候选满足，停止并列出最多 20 个候选及每个候选的 evidence score，不得任选。
   - 若没有候选满足，停止并写明：已扫描 `E:\reverse`，没有可静态识别为 `samplereverse` 的文件。
8. 若唯一定位到样本：
   - 先生成 `project_state/samplereverse_sample_path_resolution.json`，字段至少包括：root、selected_relative_path、selected_absolute_path、sha256、size_bytes、evidence_score、matched_signals、candidate_count、rejected_candidate_count、generated_at。
   - 再执行静态证据阶段。
9. 静态证据阶段：
   - 优先使用已有 IDA runner/script 做 headless/static evidence extraction；若 IDA 不可用或 preflight 不允许，则使用 `static_feature_extractor.py` fallback。
   - 不执行样本逻辑，不触发 GUI，不触发 debugger。
   - 输出只写 project_state 小型摘要，例如 `project_state/samplereverse_static_evidence_rebuild_summary.json`。
   - 摘要必须记录 tool name、attempted/success/error、sample sha256、sample relative path、artifact path、sha256、size_bytes、whether StructuredEvidence was produced。
   - 不得声称 runtime_validation 已完成。
10. 报告格式要求：
   - `codex_report_summary.status` 只能使用允许值：`SUCCESS`、`PARTIAL`、`FAILED`、`BLOCKED`、`ACCEPTED_WITH_LIMITATIONS`、`UNKNOWN`。
   - `codex_report_summary.acceptance_recommendation` 若阻塞，必须写 `BLOCKED`，不得写 `NOT_ACCEPTED`。
   - `pytest_result_summary.status` 只能写 `PASSED`、`FAILED`、`PARTIAL` 或 `UNKNOWN`，不得写 `BLOCKED`。

## 6. Implementation Scope

允许修改或生成：

- `project_state/local_reverse_inventory.json`
- `project_state/samplereverse_sample_path_resolution.json`
- `project_state/samplereverse_static_evidence_rebuild_summary.json`
- `project_state/artifact_index.json`（仅当现有 schema 能登记 project_state 静态证据；不得把 runtime artifact 伪标 current）
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
- `project_state/rounds/round_20260613_samplereverse_path_resolution_static_evidence_v2/*`

只有在现有 summary/schema 无法表达样本路径解析或静态证据摘要时，才允许小范围修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- 与 sample path resolution / static evidence summary 直接相关的最小测试

不允许修改：

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `training_materials/`
- `reverse_agent/harness.py`
- `reverse_agent/sample_solver.py`
- `reverse_agent/local_reverse_solver_profiles.py`
- `reverse_agent/samplereverse_z3.py`
- `reverse_agent/advanced_solvers.py`
- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/olly_scripts/`
- `reverse_agent/ida_scripts/`
- raw sample / sample binary
- GUI 无关模块
- training queue/status/capability review 文件

## 7. Tests

必须真实运行并完整记录 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
powershell -NoProfile -Command "Test-Path E:\reverse"
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -c "from pathlib import Path; from reverse_agent.local_reverse_inventory import scan_samples; scan_samples(Path(r'E:\reverse'), Path('project_state/local_reverse_inventory.json'), None, None)"
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

若因 workspace 既有 junction/corrupt git dirs 导致 pytest collection 失败，可使用已记录的 `--rootdir=F:\reverse-agent\tests` 作为 fallback，但必须说明原因并同时记录原命令失败情况。

若修改 `reverse_agent/project_state.py` 或新增测试，必须运行包含相关测试的 pytest 子集。

验收条件：

- `preflight` 不得因 `forbidden_paths_not_allowed` 失败。
- `E:\reverse` 必须存在。
- 样本路径解析必须得到唯一 selected sample，或以 BLOCKED/PARTIAL 形式列出候选/无候选，不得猜测。
- 若唯一定位样本，必须生成 `project_state/samplereverse_sample_path_resolution.json`。
- 若执行静态证据提取，必须生成 `project_state/samplereverse_static_evidence_rebuild_summary.json`。
- 不得运行 solver/runtime/harness/debugger。
- `codex_execution_report.md` 和 `pytest_result.txt` 的 summary 字段必须使用允许状态值。
- `lint-report`、`report-summary`、`final-check` 若失败，报告必须解释是否由本轮新增问题导致，不能把失败掩盖为 SUCCESS。

## 8. Stop Conditions

遇到以下情况必须停止并写入 `codex_execution_report.md`：

- `decision_meta` 缺失、不合法、status 不是 `APPROVED`。
- skill profile 不在 active registry 中。
- 工作目录不是 `F:\reverse-agent`。
- `E:\reverse` 不存在。
- 扫描 `E:\reverse` 后没有任何 PE/可执行候选。
- 扫描后存在多个 `samplereverse` 候选且无法唯一判定。
- 样本文件不可读或 sha256 无法计算。
- IDA 不可用且 pure-Python static extractor 也无法读取唯一样本。
- 需要运行动态调试、runtime probe、harness campaign、solver 或 candidate search 才能继续。
- 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt` 才能继续。
- project_state 无法登记本轮样本路径解析或静态证据摘要。
- 新证据与 negative_results 禁止方向冲突。
- 发现已有 IDA/Ghidra/debugger/solver/harness 接口已能完成任务，但本轮实现试图重复造轮子。
