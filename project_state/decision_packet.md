```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_training_dataset_queue_refresh_v1",
  "round_id": "round_20260619_training_dataset_queue_refresh_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

刷新本地逆向训练集的当前状态、类型覆盖和下一步队列，把上一轮已接受的 claim-aware gate policy 落到训练集推进流程里。

本轮主线是 `training_dataset`。目标不是解某一个样本，而是建立一个可执行的下一步训练队列：从现有 `training_materials/local_reverse/`、`project_state/local_reverse_*`、`artifact_index.json` 和既有训练状态中，生成当前的 local reverse training status、evaluation queue、type coverage summary 和下一步候选计划。

本轮必须保持 metadata-only：不运行本地样本，不运行 solver candidate generation，不运行 runtime probe，不运行 IDA/Ghidra/debugger/emulator，不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`，不上传样本二进制。

预期输出：

- 当前训练状态是否可用；
- 每类题型的 solved / blocked / needs_triage / inventory_only 概览；
- 下一步优先样本和允许动作；
- 若下一步指向 `affine_8cfebe03`，必须标注现有 affine static evidence 是历史证据，需要在下一轮 reverse_solving/tool_integration 中做 bounded provenance verification，不能在本轮直接当 current evidence 求解。

## 2. Current Evidence

上一轮 `decision_20260619_claim_aware_artifact_freshness_policy_v1` 已被审计接受。该轮属于 `engineering_branch`，修复了 project gate/status policy，使非样本主线不会再被历史 sample missing artifacts 错误阻塞；但这不等于任何 sample artifact 已成为 current evidence。

当前 `task_packet.json` 仍是旧 `samplereverse` / `collect_missing_evidence` 建议。它不是本轮执行权威。本轮执行以本 `project_state/decision_packet.md` 为准。

当前 `current_state.json` 仍指向 `samplereverse`，best candidates 为空，多个 artifact 字段为空；不能作为 local reverse training 的 current sample evidence。

当前 `artifact_index.json` 对 `samplereverse` 记录大量 `freshness=missing` artifact。这些是历史/backlog 状态，不能作为当前 reverse-solving 证据，也不应阻塞本轮 metadata-only training_dataset 刷新。

`negative_results.json` 的禁止方向继续有效：不回到旧 `sample_solver` blind search，不只扩 beam/budget/topN，不把 `compare_semantics_agree=false` candidates 当 primary frontier，不提交完整 `solve_reports/`，不重复 samplereverse 已失败的 exact2/H1-H3/transform-trace 方向。

已有训练集相关能力和产物：

- `reverse_agent/local_reverse_training_status.py` 已存在，用于合并 inventory、validated handoff、constraint recovery、solver result 和 artifact_index，生成 training status / evaluation queue / status overlay。优先复用，不要新写第三套 corpus scanner。
- `reverse_agent/local_reverse_training_review.py`、`reverse_agent/local_reverse_corpus.py`、`reverse_agent/tool_capability_inventory.py` 已存在；先检查再决定是否需要读取或修改。
- `training_materials/local_reverse/inventory.json`、`training_materials/local_reverse/queue.json`、`training_materials/local_reverse/cases/*.json` 是训练集 metadata 入口。
- `project_state/local_reverse_training_resume_plan.md` 显示旧快照：solved=1、blocked=2、needs_triage=1、inventory_only=46；高优先级包括 `affine_8cfebe03` 和 `cpp1_2f6fcb63`。
- `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json` 记录历史上 `affine_8cfebe03` 的 `STATIC_TOOL_NO_OUTPUT` blocker 已被修复，root cause 是 IDA output dir 路径问题，下一步曾建议 full static triage。
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 记录历史 IDA static evidence：`tool_status=success`，分类仍是 `unknown`，有 `_strncmp` compare context 和 solver hints，下一步是 `constraint_recovery_or_targeted_decompilation`；但它不是本轮 current evidence，必须在后续样本轮重新做 provenance/freshness 判断。

本轮只刷新训练集状态和下一步计划，不把历史 affine evidence 直接升级为 current reverse-solving 依据。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何本地样本可执行文件。

不要生成 candidate、flag、密码、key 或 solver 输出。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner、solver、harness 或 GUI/frontend workflow。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要上传、复制、提交本地样本二进制。

不要新建重复的 corpus scanner、IDA runner、Ghidra runner、debugger runner、solver 或 harness。

不要修改 `.codex-skills/`。

不要修改 `reverse_agent/local_reverse_single_sample_static_triage.py`、IDA/Ghidra/debugger/tool runner/solver/harness，除非本轮仅做 metadata refresh 时发现现有 training status 代码有明确、可测试、范围内的小 bug；若需要工具接入修复，停止并在报告中建议下一轮转 `tool_integration`。

不要把 `samplereverse` 的 stale/missing artifact 当作当前训练集证据。

不要把 `affine_8cfebe03` 的历史 static evidence 当作 current reverse-solving 证据。

不要把本轮扩展成单样本硬编码或批量盲跑。

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

训练集和现有能力相关文件：

1. `reverse_agent/local_reverse_training_status.py`
2. `reverse_agent/local_reverse_training_review.py`
3. `reverse_agent/local_reverse_corpus.py`
4. `reverse_agent/tool_capability_inventory.py`
5. `training_materials/local_reverse/inventory.json`
6. `training_materials/local_reverse/queue.json`
7. `training_materials/local_reverse/status_overlay.json`
8. `project_state/local_reverse_training_status.json`
9. `project_state/local_reverse_evaluation_queue.json`
10. `project_state/local_reverse_training_resume_plan.md`
11. `project_state/local_reverse_training_resume_plan.json`
12. `project_state/local_reverse_training_coverage_matrix.json`
13. `project_state/local_reverse_type_coverage_matrix.json`
14. `project_state/local_reverse_training_next_queue.json`
15. `project_state/local_reverse_training_inventory_refresh.json`
16. `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`
17. `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`
18. `project_state/local_reverse_affine_8cfebe03_static_triage.json`

只允许有界读取与训练队列相关的 `project_state/rounds/<round_id>/round_manifest.json` 或最近相关 round 的 report/pytest；不要读取完整 `solve_reports/`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录；若已有 dirty files，必须记录 baseline 并排除继承脏改动。
5. `decision_meta.status=APPROVED`。
6. `mainline=training_dataset`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. `task_packet.json` 不是执行权威。
9. 本轮是 metadata-only training_dataset refresh，不是 sample solving。
10. `reverse_agent/local_reverse_training_status.py` 已存在，优先复用，不重复实现 corpus scanner。
11. 若现有 inventory/status/queue 已足够，优先生成 refresh/plan artifacts，而不是改源码。
12. 若发现需要修改训练状态生成逻辑，只允许小范围修改 training status/review/corpus 相关代码，并写测试；不得修改 solver、IDA/Ghidra/debugger/tool runner/harness。
13. 历史 affine static evidence 只能作为下一轮候选线索，不能在本轮作为 current solving evidence。
14. 本轮不运行 IDA/Ghidra/runtime/solver/harness/sample。
15. 本轮不读取完整 heavy history。

必须审计并记录：

1. 当前 inventory 中样本数量、分类字段、status overlay 是否一致。
2. 当前 training status 的 solved / blocked / needs_triage / inventory_only 计数。
3. 类型覆盖矩阵是否能支持“两周内覆盖每类题型”的路线选择。
4. 下一步候选是否来自 current metadata/status，而不是来自 stale sample artifact。
5. `affine_8cfebe03`、`cpp1_2f6fcb63`、`cpp2_4c69f173`、`sha_256_18019fca` 是否仍在队列中，以及它们的优先级和下一动作是否需要更新。
6. 是否存在 current tool capability evidence；若没有，只记录缺口，不运行工具补证据。
7. 是否需要下一轮转 `tool_integration` 或 `reverse_solving`。

## 6. Implementation Scope

Allowed source files only if a small metadata bug is proven:

- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_training_review.py`
- `reverse_agent/local_reverse_corpus.py`

Allowed tests only if source files are changed:

- `tests/test_local_reverse_training_status.py`
- `tests/test_local_reverse_training_review.py`
- `tests/test_local_reverse_corpus.py`

Preferred generated/project-state outputs:

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_training_status_summary_sync.json`
- `project_state/local_reverse_training_queue_refresh.json`
- `project_state/local_reverse_type_coverage_matrix.json`
- `project_state/local_reverse_training_next_queue.json`
- `project_state/local_reverse_next_step_plan.json`
- `project_state/local_reverse_next_step_plan.md`
- `training_materials/local_reverse/status_overlay.json`
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
- `project_state/rounds/round_20260619_training_dataset_queue_refresh_v1/*`

Implementation requirements:

1. 先运行现有 metadata-only status path，确认是否能无副作用输出 JSON：
   - `python -m reverse_agent.local_reverse_training_status --json`
2. 若 JSON 模式正常，再运行写文件模式刷新 training status / queue / status overlay；不要扫描样本二进制，不要运行工具。
3. 生成 `project_state/local_reverse_next_step_plan.json`，至少包含：
   - `schema_version`
   - `decision_id`
   - `round_id`
   - `mainline`
   - `status_summary`
   - `type_coverage_summary`
   - `priority_queue`
   - `recommended_next_mainline`
   - `recommended_next_decision_goal`
   - `evidence_freshness_notes`
   - `do_not_repeat`
4. 生成 `project_state/local_reverse_next_step_plan.md`，用人工可读格式说明下一轮建议。
5. 推荐下一轮时只能给一个主线，不要同时推进工程、工具接入和样本求解。
6. 如果 current metadata 支持，则优先建议下一轮对 `affine_8cfebe03` 做 bounded targeted decompilation / constraint recovery 的 `reverse_solving` 或 `tool_integration`；如果 provenance 不足，则建议下一轮先做 bounded static artifact provenance verification。
7. 如果 `cpp1_2f6fcb63` 的 contradiction 仍比 affine 更高优先级，必须说明依据。
8. 不要把单个样本结果写入 `.codex-skills/`。
9. 不要生成 candidate 或 flag。
10. 兼容旧字段，不破坏现有 inventory/status overlay 格式。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.local_reverse_training_status --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果修改了 Python 源码，必须追加运行对应 pytest，至少：

```powershell
python -m pytest tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
```

如果本轮只生成 metadata/project_state artifacts 且未改源码，允许不跑完整 pytest，但报告必须说明没有源码改动，并记录 training status JSON、doctor、preflight、gate-profile、command-plan、report-summary、final-check 的结果。

如果 `gate_profile_plan.closeout_allowed=true` 且 `final-check` 无 FAIL，运行：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_training_dataset_queue_refresh_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：

- 是否修改源码；
- training status 刷新命令和结果；
- solved / blocked / needs_triage / inventory_only 计数；
- 类型覆盖缺口；
- 下一轮推荐主线和目标；
- 是否把 historical/stale evidence 降级为线索；
- 没有运行 sample/IDA/Ghidra/runtime/solver/harness；
- gate 结果和是否 close-round。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 `APPROVED`。
3. `mainline` 不是 `training_dataset`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、solver、harness、IDA、Ghidra、debugger、emulator、runtime probe、sidecar 或 GUI workflow 才能完成本轮。
6. 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改 solver、IDA/Ghidra/debugger/tool runner/harness 才能完成本轮。
8. 现有 inventory/status overlay 缺失到无法生成训练状态，且需要重新扫描本地样本目录或上传样本二进制。
9. 生成的下一步计划只能依赖 stale/missing sample artifact，无法说明 provenance。
10. pytest_result 没有真实命令记录。
11. report/decision/pytest_result 的 decision_id 或 round_id 不匹配。
12. final-check 仍出现 FAIL。
