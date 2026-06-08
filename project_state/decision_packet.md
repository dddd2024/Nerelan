```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_missing_branch_reconciliation_v1",
  "round_id": "round_20260608_cpp2_883e67b9_missing_branch_reconciliation_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **tool_integration**。

目标：基于已 ACCEPTED 的 `cpp2_883e67b9_loop_semantics_mapping`，对 `focus_backward_sites_missing_from_annotation=[0x5f68, 0x60a4, 0x60b6]` 做有界 reconciler artifact，明确这些 missing sites 是真正的解码缺口、source artifact 表述差异，还是只存在于 targeted static solving 的候选线索。

本轮不是 reverse_solving。不要生成 candidate，不要验证 candidate，不运行样本，不调用 IDA/Ghidra/debugger/hook/probe/winpty，不重新读取样本二进制，不扩张静态窗口。

必须完成：

```text
1. 读取 current source artifacts：
   - project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
   - project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json
   - project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json

2. 检查现有 project_state / StructuredEvidence / solver profile / artifact_index 接口，复用已有格式，不新建重复框架。

3. 产出新 artifact：
   project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json

4. 新 artifact 必须至少包含：
   - sample_id / relative_path / identity_verified
   - source_artifacts 与 source_run / source decision
   - observed_backward_sites：0x6040、0x6081、0x61e8、0x6390、0x647d
   - missing_backward_sites：0x5f68、0x60a4、0x60b6
   - per-site reconciliation record：site_rva、source_claims、observed_in_loop_mapping、observed_in_bounded_loop_evidence、observed_in_targeted_static_solving、classification、confidence、impact
   - allowed classification：confirmed_missing_decode | source_only_hint | resolved_not_backward | blocked_insufficient_evidence
   - 不允许把 missing site 当 confirmed formula 或 candidate source
   - reconciliation_status: RECONCILED_WITH_LIMITATIONS | BLOCKED
   - evidence_gaps_carried_forward：known_compare_constant_count_zero、input_length_unknown、no_complete_formula_recovered
   - recommended_next_mainline：tool_integration，并解释理由
   - candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false、training_status_modified=false、status_overlay_modified=false

5. 更新 project_state/artifact_index.json，将新 artifact 登记到 latest_artifacts、latest_artifacts_v2、artifact_refs，freshness=current，source_run 为本轮 round，并写入真实 sha256 与 size_bytes。

6. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 decision/report/round。
```

本轮不要求修改 solver 逻辑；除非现有接口无法表达 reconciliation schema，否则不要改 production code。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 `loop_semantics_mapping` 已 ACCEPTED。当前 report/pytest 已绑定：

```text
report_id=report_20260608_cpp2_883e67b9_loop_semantics_mapping_v1
round_id=round_20260608_cpp2_883e67b9_loop_semantics_mapping_v1
decision_id=decision_20260608_cpp2_883e67b9_loop_semantics_mapping_v1
status=SUCCESS / PASSED
```

`artifact_index.latest_artifacts_v2.local_reverse_cpp2_883e67b9_loop_semantics_mapping` 当前 provenance 已可核验：

```text
path=project_state\local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_loop_semantics_mapping_v1
sha256=8cbe833fd112771459cc5562c40cd8e07dfca4962975de5d539148719829f8fa
size_bytes=12804
sample_id=cpp2_883e67b9
loop_semantics_status=MAPPED_WITH_LIMITATIONS
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
next_recommended_mainline=tool_integration
```

Loop semantics mapping 已经结构化：

```text
assert_path region: 0x5f00-0x6500
focus_assert_path_rva=0x61c3
observed backward branches:
  0x6040 -> 0x6014
  0x6081 -> 0x6059
  0x61e8 -> 0x61b7
  0x6390 -> 0x6376
  0x647d -> 0x62bb
focus_backward_sites_observed=[0x6081, 0x61e8]
focus_backward_sites_missing_from_annotation=[0x5f68, 0x60a4, 0x60b6]
compare constants semantic_role=unknown
formula_recovered=false
candidate_generated=false
recommended_next_mainline=tool_integration
```

Current unresolved gaps：

```text
no_complete_formula_recovered: blocks reverse_solving
known_compare_constant_count_zero: blocks solver_profile_normalization
input_length_unknown: blocks candidate_construction
missing_backward_sites_in_annotation: low severity, blocks none but should be reconciled before deeper static reconstruction
structured_evidence_ready_false: blocks complete_formula_recovery
```

Current training summary 保持：

```text
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
```

`task_packet.json` 中的 queue hint 仍只作建议：`cpp2_883e67b9` proposed_next_mainline=tool_integration，allowed_actions=static_triage / bounded_static_extraction_readiness，forbidden_actions=runtime_probe / brute_force / debugger / hook / emulator / upload_binary。

`negative_results.json` 主要约束旧 samplereverse 路线；本轮仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要运行 E:\reverse 样本。
2. 不要执行 candidate generation、candidate validation、negative control、runtime validation。
3. 不要 attach debugger / hook / emulator / probe / winpty。
4. 不要调用 IDA/Ghidra。
5. 不要重新读取样本二进制或扩张静态窗口。
6. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
7. 不要把 cpp2_883e67b9 推进到 candidate 层。
8. 不要把 missing branch site 当作 confirmed formula 或 candidate source。
9. 不要把 KEEP_DREAM、WeKnowItOk、10013、hookapi 或任何单样本 candidate 写死进 solver/dispatch。
10. 不要修改 local_reverse_training_status.json。
11. 不要修改 training_materials/local_reverse/status_overlay.json。
12. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
13. 不要新建重复 IDA/Ghidra/debugger/runtime interface。
14. 不要重写成熟工具已有的反汇编/反编译能力。
15. 不要读取完整 solve_reports。
16. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
17. 不要提交 full solve_reports。
18. 不要把 task_packet.task 当执行权威。
19. 不要把 stale/missing/unknown artifact 当 current。
20. 不要把本轮变成 reverse_solving、训练状态同步或 runtime validation 轮。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取与 cpp2_883e67b9 直接相关的 current project_state artifacts。
3. 有界读取相关源码以复用现有 StructuredEvidence / project_state / artifact_index / solver profile 接口。
4. 新增 project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json。
5. 更新 artifact_index.json 登记新 artifact，包含真实 sha256/size_bytes。
6. 更新 codex_execution_report.md 和 pytest_result.txt。
7. 如确有必要，为 missing branch reconciliation 增加小型 schema/helper，但必须复用现有模式并有测试。
```

---

## 4. Files To Inspect

必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
.codex-skills/registry.json

project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
```

必须检查已有能力，避免重复造轮子：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
tests/test_project_state.py
tests/test_local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
```

必要时搜索：

```text
StructuredEvidence
normalized_profile_evidence
profile_evidence
artifact_index
local_reverse_cpp2_883e67b9
loop_semantics
missing_backward_sites
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse 样本文件
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 tool_integration？
3. task_packet 是否仅为 advisory？
4. 是否确认本轮不是 reverse_solving，不生成/验证 candidate？
5. 是否确认没有运行样本、runtime validation、debugger、hook、emulator、probe、winpty？
6. 是否确认没有调用 IDA/Ghidra 或重新读取样本二进制？
7. 是否检查了已有 StructuredEvidence / solver profile / project_state / artifact_index 接口？
8. 是否复用了已有接口/格式，而非新建重复框架？
9. 是否读取并只使用 current 的 cpp2_883e67b9 source artifacts？
10. 新 artifact 是否记录 source artifacts/source_run/freshness？
11. 新 artifact 是否记录 observed_backward_sites 与 missing_backward_sites？
12. 新 artifact 是否对 0x5f68、0x60a4、0x60b6 分别给出 classification/confidence/impact？
13. 新 artifact 是否避免把 missing site 标成 confirmed formula 或 candidate source？
14. 新 artifact 是否明确 reconciliation_status 与 recommended_next_mainline？
15. artifact_index 是否登记新 artifact，且 freshness=current、source_run 为当前 round、sha256/size_bytes 为真实值？
16. 是否没有修改 training_status/status_overlay？
17. 是否没有读取 full solve_reports 或 PROJECT_PROGRESS_LOG？
18. 是否没有修改 solver production code？如果修改了，为什么必须修改？
19. 是否运行 py_compile？
20. 是否运行相关 pytest？结果是多少？
21. 是否运行 lint-decision、lint-report、project_state status？
22. 是否运行 git diff --check、git status --short、git diff --name-status？
23. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Inspect source artifacts only

读取并摘要：

```text
project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
```

只使用 artifact 内已有证据，不重新跑样本、不重新跑 IDA/Ghidra、不扩张静态窗口、不读取本地二进制。

### Phase B — Inspect existing interfaces

有界检查：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
```

目标是复用已有 schema/字段/注册方式，不新建重复 IDA/Ghidra/debugger/runtime 接口。

### Phase C — Create missing branch reconciliation artifact

生成：

```text
project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
```

建议 schema：

```json
{
  "schema_version": 1,
  "mainline": "tool_integration",
  "artifact_kind": "local_reverse_missing_branch_reconciliation",
  "sample_id": "cpp2_883e67b9",
  "relative_path": "逆向课程2024春02/CPP2.exe",
  "round_id": "round_20260608_cpp2_883e67b9_missing_branch_reconciliation_v1",
  "decision_id": "decision_20260608_cpp2_883e67b9_missing_branch_reconciliation_v1",
  "source_artifacts": [...],
  "identity_verified": true,
  "observed_backward_sites": ["0x6040", "0x6081", "0x61e8", "0x6390", "0x647d"],
  "missing_backward_sites": ["0x5f68", "0x60a4", "0x60b6"],
  "site_reconciliation": [
    {
      "site_rva": "0x5f68",
      "source_claims": [...],
      "observed_in_loop_mapping": false,
      "observed_in_bounded_loop_evidence": false,
      "observed_in_targeted_static_solving": true,
      "classification": "source_only_hint|confirmed_missing_decode|resolved_not_backward|blocked_insufficient_evidence",
      "confidence": "low|medium|high",
      "impact": "..."
    }
  ],
  "reconciliation_status": "RECONCILED_WITH_LIMITATIONS",
  "formula_recovered": false,
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "recommended_next_mainline": "tool_integration",
  "recommended_next_action": "..."
}
```

若 evidence 不足以 classify any site, 使用 `blocked_insufficient_evidence` 并说明 source artifact 缺口。

### Phase D — Update artifact_index and report

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须加入：

```text
local_reverse_cpp2_883e67b9_missing_branch_reconciliation
```

并在 latest_artifacts、latest_artifacts_v2、artifact_refs 中登记。latest_artifacts_v2 必须包含：

```text
kind=local_reverse_missing_branch_reconciliation
path=project_state\local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_missing_branch_reconciliation_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
sha256=<真实值>
size_bytes=<真实值>
reconciliation_status=RECONCILED_WITH_LIMITATIONS|BLOCKED
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增 helper 或 schema test，必须补充对应 pytest 并记录完整命令。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. 任一 required source artifact 缺失、stale、unknown，或 sample identity 不匹配。
3. 需要运行样本、runtime validation、debugger、hook、emulator、probe、winpty、IDA/Ghidra 才能完成本轮。
4. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
5. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
6. 需要生成或验证 candidate。
7. 需要扩大静态窗口、预算、枚举空间或重新做二进制分析。
8. 需要新建重复 IDA/Ghidra/debugger/runtime interface。
9. 新 artifact 无法明确区分 observed sites、missing sites 和 source-only hints。
10. artifact_index 无法登记新 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
11. lint-report/status 无法通过。
12. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若 reconciliation_status 为 RECONCILED_WITH_LIMITATIONS 且仍推荐 tool_integration，下一轮优先做 compare constants semantic mapping 或 input length evidence；若 BLOCKED，下一轮先修证据源一致性。
