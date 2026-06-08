```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_structured_evidence_projection_v1",
  "round_id": "round_20260608_cpp2_883e67b9_structured_evidence_projection_v1",
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

目标：对 `cpp2_883e67b9` 的 current 静态证据链做小步结构化投影，使后续 solver dispatch 可以消费明确的 `StructuredEvidence` / profile readiness 结论，而不是继续依赖散落的 PARTIAL 静态 artifact。

本轮不是 reverse_solving，不生成 candidate，不验证 candidate，不运行样本。

当前阻断点：`cpp2_883e67b9` 已有 current 的 bounded static readiness、bounded static extraction、targeted static solving、bounded loop evidence extraction；其中 static extraction 为 SUCCESS，但 `structured_evidence_ready=false`，targeted static solving 和 loop evidence extraction 仍是 PARTIAL。下一步应把这些 current artifact 中的可用事实和缺口压缩成一个可审计的 StructuredEvidence projection / readiness artifact，为未来 solver 选择提供输入。

必须完成：

```text
1. 读取并审计当前 cpp2_883e67b9 的 current artifacts：
   - project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
   - project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
   - project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
   - project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json

2. 检查现有 StructuredEvidence / solver profile / constraint recovery / artifact registration 接口，复用已有实现，不新建重复框架。

3. 产出一个新的轻量 artifact：
   project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json

4. 新 artifact 必须说明：
   - sample_id / relative_path / expected_sha256 / actual_sha256 / identity_verified
   - 使用了哪些 source artifacts 与 source_run
   - static extraction status / targeted static solving status / loop evidence status
   - 已能结构化的证据类型，例如 PE mapping、bounded loop region、branch/backward branch、assert-path focus RVA、known compare constants availability
   - 当前不能结构化的缺口，例如 structured_evidence_ready=false、known_compare_constant_count=0、candidate_generated=false
   - solver_profile_readiness: READY_WITH_LIMITATIONS | BLOCKED
   - recommended_next_mainline: reverse_solving 或 tool_integration，并说明理由

5. 更新 project_state/artifact_index.json，将新 artifact 登记到 latest_artifacts、latest_artifacts_v2、artifact_refs，freshness=current，source_run 为本轮 round。

6. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 decision/report/round。
```

本轮不要求修改 solver 逻辑；除非现有接口无法表达 projection schema，否则不要改 production code。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制执行。

上一轮 metadata rework 已 ACCEPTED：

```text
report_id=report_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
round_id=round_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
decision_id=decision_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
status=SUCCESS / PASSED
```

`task_packet.json` 的 local_reverse queue hint 只作为建议：

```text
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
proposed_next_mainline=tool_integration
allowed_actions=static_triage, bounded_static_extraction_readiness
forbidden_actions=runtime_probe, brute_force, debugger, hook, emulator, upload_binary
```

当前 artifact_index 中 `cpp2_883e67b9` 相关 current 证据：

```text
1. local_reverse_cpp2_883e67b9_bounded_static_triage_readiness
   freshness=current
   readiness_status=READY
   identity_verified=true
   next_recommended_mainline=tool_integration

2. local_reverse_cpp2_883e67b9_bounded_static_extraction
   freshness=current
   extraction_status=SUCCESS
   identity_verified=true
   structured_evidence_ready=false
   next_recommended_mainline=tool_integration

3. local_reverse_cpp2_883e67b9_targeted_static_solving
   freshness=current
   static_solving_status=PARTIAL
   candidate_generated=false
   candidate_validation_attempted=false
   candidate_validated=false
   next_recommended_mainline=tool_integration

4. local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction
   freshness=current
   evidence_extraction_status=PARTIAL
   acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
   candidate_generated=false
   candidate_validation_attempted=false
   candidate_validated=false
   next_recommended_mainline=tool_integration
```

`local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json` 中已经有可结构化的 bounded evidence：

```text
mainline=tool_integration
sample_id=cpp2_883e67b9
identity_verified=true
evidence_extraction_status=PARTIAL
source_targeted_static_solving_status=PARTIAL
source_static_extraction_status=SUCCESS
existing_helpers_checked=true
helpers_or_tools_used 包含 python_stdlib_pe_parser、bounded_x86_byte_window_annotation、StructuredEvidence_lightweight_schema_reviewed
optional_dependencies: capstone_available=false, pefile_available=false
bounded region assert_path_local_loop_window: start_rva=0x5f00, end_rva_exclusive=0x6500, focus_assert_path_rva=0x61c3, instruction_count_scanned=798, branch_count=65, backward_branch_count=5, known_compare_constant_count=0
```

当前 training summary 保持：

```text
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
```

`negative_results.json` 主要约束旧 samplereverse 路线；本轮仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

工具能力边界：项目已有 IDA-guided solver、runtime probe、constraint recovery、string solver、project_state lint/status、artifact_index 注册和本地静态提取 artifact。成熟工具优先；已有 IDA/Ghidra/debugger/runtime interface 时不得重复造轮子。本轮只做 current artifact 的结构化投影，不调用 IDA/Ghidra，不运行 debugger/runtime。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要运行 E:\reverse 样本。
2. 不要执行 candidate generation、candidate validation、negative control、runtime validation。
3. 不要 attach debugger / hook / emulator / probe / winpty。
4. 不要调用 IDA/Ghidra，也不要重新读取样本二进制来扩张静态分析。
5. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
6. 不要推进 cpp2_883e67b9 求解到 candidate 层。
7. 不要把 KEEP_DREAM、WeKnowItOk、10013、hookapi 或任何单样本 candidate 写死进 solver/dispatch。
8. 不要修改 local_reverse_training_status.json 中 solved/blocked/inventory 状态。
9. 不要修改 training_materials/local_reverse/status_overlay.json。
10. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
11. 不要新建重复 IDA/Ghidra/debugger/runtime interface。
12. 不要重写成熟工具已有的反汇编/反编译能力。
13. 不要读取完整 solve_reports。
14. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不要提交 full solve_reports。
16. 不要把 task_packet.task 当执行权威。
17. 不要把 stale/missing/unknown artifact 当 current。
18. 不要把本轮变成 reverse_solving、训练状态同步或 runtime validation 轮。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取与 cpp2_883e67b9 直接相关的 current project_state artifacts。
3. 有界读取相关源码以复用现有 StructuredEvidence / project_state / artifact_index / solver profile 接口。
4. 新增一个 project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json artifact。
5. 更新 artifact_index.json 登记新 artifact。
6. 更新 codex_execution_report.md 和 pytest_result.txt。
7. 如确有必要，为 projection 增加小型 schema/helper，但必须复用现有模式并有测试。
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

project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json
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
11. 新 artifact 是否记录 identity_verified 与 sha256/size 事实？
12. 新 artifact 是否区分可结构化证据和证据缺口？
13. 新 artifact 是否明确 solver_profile_readiness 与 recommended_next_mainline？
14. artifact_index 是否登记新 artifact，且 freshness=current、source_run 为当前 round？
15. 是否没有修改 training_status/status_overlay？
16. 是否没有读取 full solve_reports 或 PROJECT_PROGRESS_LOG？
17. 是否没有修改 solver production code？如果修改了，为什么必须修改？
18. 是否运行 py_compile？
19. 是否运行相关 pytest？结果是多少？
20. 是否运行 lint-decision、lint-report、project_state status？
21. 是否运行 git diff --check、git status --short、git diff --name-status？
22. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Inspect current source artifacts

读取并摘要以下 current artifacts：

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json
```

只使用 artifact 内已有证据，不重新跑样本、不重新跑 IDA/Ghidra、不扩张静态窗口。

### Phase B — Inspect existing interfaces

有界检查：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
```

目标是找已有 schema/字段/注册方式，例如 `normalized_profile_evidence`、`profile_evidence`、`StructuredEvidence`、artifact_index update 约定。不要新建重复 IDA/Ghidra/debugger/runtime 接口。

### Phase C — Create projection artifact

生成：

```text
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
```

建议 schema：

```json
{
  "schema_version": 1,
  "mainline": "tool_integration",
  "artifact_kind": "local_reverse_structured_evidence_projection",
  "sample_id": "cpp2_883e67b9",
  "relative_path": "逆向课程2024春02/CPP2.exe",
  "round_id": "round_20260608_cpp2_883e67b9_structured_evidence_projection_v1",
  "decision_id": "decision_20260608_cpp2_883e67b9_structured_evidence_projection_v1",
  "identity": {
    "expected_sha256": "...",
    "actual_sha256": "...",
    "identity_verified": true
  },
  "source_artifacts": [...],
  "source_status": {
    "bounded_static_triage_readiness": "READY",
    "bounded_static_extraction": "SUCCESS",
    "targeted_static_solving": "PARTIAL",
    "bounded_loop_evidence_extraction": "PARTIAL"
  },
  "structured_evidence": {
    "pe_mapping": {...},
    "bounded_regions": [...],
    "branch_summary": {...},
    "compare_constants": {...},
    "evidence_gaps": [...]
  },
  "solver_profile_readiness": "READY_WITH_LIMITATIONS",
  "recommended_next_mainline": "reverse_solving|tool_integration",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "training_status_modified": false,
  "status_overlay_modified": false
}
```

如果 evidence 不足以 mark `READY_WITH_LIMITATIONS`，使用 `BLOCKED` 并说明 missing fields。

### Phase D — Update artifact_index and report

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须加入：

```text
local_reverse_cpp2_883e67b9_structured_evidence_projection
```

并在 latest_artifacts、latest_artifacts_v2、artifact_refs 中登记。latest_artifacts_v2 必须包含：

```text
kind=local_reverse_structured_evidence_projection
path=project_state\local_reverse_cpp2_883e67b9_structured_evidence_projection.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_structured_evidence_projection_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
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

如果新增 projection helper 或 schema test，必须补充对应 pytest 并记录完整命令。

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
9. 新 artifact 无法明确区分可结构化证据和证据缺口。
10. artifact_index 无法登记新 artifact 的 current provenance。
11. lint-report/status 无法通过。
12. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若 projection 为 READY_WITH_LIMITATIONS，下一轮再单独决策是否进入 reverse_solving；若 projection 为 BLOCKED，下一轮仍保持 tool_integration 并只补缺失证据。
