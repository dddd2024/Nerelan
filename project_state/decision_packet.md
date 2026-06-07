```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1",
  "round_id": "round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **reverse_solving**，任务是修复上一轮 `cpp2_883e67b9_targeted_static_solving` 的 metadata、schema、status、artifact_index 和 next-step 问题。

上一轮产物包含有价值的局部静态分析，但不能验收，原因是：

```text
1. decision 要求 mainline=reverse_solving，但 report 正文和 artifact 写成 tool_integration。
2. 无 candidate、无完整 proof chain，却把 static_solving_status 写成 SUCCESS。
3. artifact 字段名偏离 decision schema：source_extraction_artifact/source_extraction_status/raw_offset_correction。
4. artifact 缺少 candidate_validation_attempted、candidate_acceptance_status 等必需字段。
5. next_recommended_action 建议 runtime validation guesses / bounded brute-force，违反本轮禁止项。
6. pytest_result 没有捕获 mainline/status/schema/next-step 这些关键错误。
```

目标：保留上一轮有价值的 bounded region analysis，但规范化为 **PARTIAL targeted static solving artifact**。不得运行样本，不得 runtime validation，不得 brute force，不得生成 candidate guesses，不得修改训练状态。

必须修复：

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 artifact 的可复用证据：

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json:
  sample_id=cpp2_883e67b9
  identity_verified=true
  expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
  expected_size_bytes=196689
  source_extraction_artifact=project_state\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
  source_extraction_status=SUCCESS
  pe_layout_reverified exists
  raw_offset_correction.status=corrected
  prompt_path analyzed around 0x4010ad
  failure_path analyzed around 0x4010e6
  assert_path analyzed around 0x4061c3
  constants in assert_path include 194, 141, 133, 0x1102, 0x10c, 0x108, 255, 0x100
  loop_indicators found in assert_path
  candidate_generated=false
  candidate_validated=false
  training_status_modified=false
  status_overlay_modified=false
  executed_sample=false
  ran_runtime_tools=false
```

But the previous artifact is nonconforming and must be rewritten in-place using the required schema.

Current training facts must remain unchanged:

```text
project_state/local_reverse_training_status.json:
  cpp2_883e67b9.training_status=inventory_only
  cpp2_883e67b9.known_candidate=""
  cpp2_883e67b9.blocked_reason=""
  cpp2_883e67b9.classification=""
  cpp2_883e67b9.evidence_sources=[]
```

Required corrected interpretation:

```text
static_solving_status=PARTIAL
status=PARTIAL
acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
candidate_generated=false
unvalidated_candidate_hypothesis=null OR candidate=null with explicit no_candidate_extracted status
next step must be deeper bounded static evidence extraction / local disassembly / loop reconstruction, not runtime guesses or brute-force
```

negative_results mainly concerns old `samplereverse` directions. This round must not repeat blind search, budget expansion, stale artifact assumptions, full solve_reports commits, or candidate search.

Skill profile must remain `reverse-agent-iteration@v2`, which is active in `.codex-skills/registry.json`.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run the sample executable.
3. Do not execute any candidate or control input.
4. Do not attach debugger, hook, emulator, instrumentation probe, breakpoint probe, dynamic trace collector, winpty, console validator, or runtime harness.
5. Do not perform runtime validation.
6. Do not brute force, dictionary search, fuzz, enumerate inputs, rank candidates, or generate candidate guesses.
7. Do not solve cpp2_883e67b9 in this round.
8. Do not modify project_state/local_reverse_training_status.json.
9. Do not modify training_materials/local_reverse/status_overlay.json.
10. Do not mark cpp2_883e67b9 solved, blocked, validated, or partially solved in training status.
11. Do not write known_candidate for cpp2_883e67b9.
12. Do not alter accepted solved facts for cpp2_2f64e68d / 10013 or cpp2_32f1713e / KEEP_DREAM.
13. Do not upload, copy into repo, base64-embed, or commit the sample binary.
14. Do not store raw binary bytes, full strings dump, full imports, full sections, full disassembly, full decompilation, screenshots, memory dumps, or bulky static output.
15. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
16. Do not modify .codex-skills.
17. Do not create duplicate IDA/Ghidra/debugger/static extraction/runtime interfaces.
18. Do not use stale IDA/Ghidra/static artifacts as current evidence for cpp2_883e67b9.
19. Do not claim IDA/Ghidra evidence was used unless current artifact proves it for this sample and this round.
20. Do not leave any next_recommended_action that suggests runtime validation guesses, brute force, dictionary search, fuzzing, enumeration, candidate ranking, or candidate guesses.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current bounded static extraction and targeted static solving artifacts for cpp2_883e67b9.
3. Read local_reverse_training_status/status_overlay only for current state verification.
4. Reuse previous bounded region analysis as source content.
5. Rewrite targeted_static_solving artifact schema/status/mainline/next-step metadata.
6. Update artifact_index metadata for local_reverse_cpp2_883e67b9_targeted_static_solving.
7. Write codex_execution_report.md and pytest_result.txt.
```

---

## 4. Files To Inspect

Must inspect:

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
.codex-skills/registry.json
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Do not read by default:

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse tree or any sample binary
```

---

## 5. Required Audit

Codex report must answer:

```text
1. Did it confirm decision_packet is the sole execution authority?
2. Did it confirm mainline=reverse_solving?
3. Did it confirm this is targeted static solving rework, not runtime validation or solving expansion?
4. Did it confirm task_packet remains advisory?
5. Did it confirm source bounded_static_extraction artifact is current/SUCCESS/identity_verified?
6. Did it confirm cpp2_883e67b9 remains inventory_only/known_candidate="" before and after?
7. Did it confirm cpp2_32f1713e/KEEP_DREAM and cpp2_2f64e68d/10013 solved facts remain unchanged?
8. Did it preserve useful bounded region analysis from the previous artifact?
9. Did it set artifact.mainline=reverse_solving?
10. Did it set static_solving_status=PARTIAL, not SUCCESS?
11. Did it set report status=PARTIAL and acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS?
12. Did it use source_static_extraction_artifact and source_static_extraction_status field names?
13. Did it include prior_raw_offset_fields_treated_as and mapping_correction_summary?
14. Did it include candidate_validation_attempted=false?
15. Did it include candidate_acceptance_status=null?
16. Did it keep candidate_generated=false and candidate_validated=false?
17. Did it avoid claiming a candidate or writing known_candidate?
18. Did next_recommended_action avoid runtime validation guesses, brute force, dictionary search, fuzzing, enumeration, candidate ranking and candidate guesses?
19. Did it update artifact_index latest_artifacts_v2 static_solving_status=PARTIAL?
20. Did it avoid sample execution/runtime validation/debugger/hook/emulator/probe?
21. Did it avoid modifying training_status/status_overlay?
22. Did it explain negative_results unchanged or non-use?
23. Did it run required py_compile/pytest/lint/status/git checks?
24. Did pytest_result.txt use this rework decision_id/report_id/round_id?
25. Did pytest_result explicitly check mainline/status/schema/next-step constraints?
26. Did final lint-report run after report write?
27. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small metadata/schema/status rework only.

### Phase A — preflight

Use `.venv\Scripts\python` for repository Python commands.

Verify:

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json:
  sample_id == cpp2_883e67b9
  identity_verified == true
  extraction_status == SUCCESS
  source_readiness_status == READY
  candidate_generated == false
  candidate_validation_attempted == false
  executed_sample == false

project_state/local_reverse_training_status.json:
  cpp2_883e67b9.training_status == inventory_only
  cpp2_883e67b9.known_candidate == ""
  cpp2_883e67b9.blocked_reason == ""
```

If state has drifted, stop as BLOCKED rather than proceeding silently.

### Phase B — normalize targeted static solving artifact

Rewrite:

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
```

Required corrected top-level fields:

```text
schema_version=1
mainline=reverse_solving
round_id=round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1
decision_id=decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
command_scoped_root=E:\reverse
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
expected_size_bytes=196689
identity_verified=true
static_solving_status=PARTIAL
training_status_before=inventory_only
known_candidate_before=""
source_static_extraction_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
source_static_extraction_status=SUCCESS
prior_raw_offset_fields_treated_as=corrected_file_offsets 或 RVA_only，按上一轮实际映射结论选择
mapping_correction_summary={bounded summary preserving prior finding}
existing_helpers_checked=true
helpers_or_tools_used=[python_stdlib_pe_parser, bounded_static_window_analysis, local_reverse_xref_disassembly_patterns]
target_regions_analyzed=[preserve prompt/failure/assert summaries]
logic_evidence={preserve constants, loops, no candidate proof chain}
solver_classification={type:unknown, confidence:medium, reason:multi_phase_loop_comparison_no_complete_formula}
static_proof_chain=[] OR partial proof chain clearly marked incomplete
unvalidated_candidate_hypothesis=null OR {candidate:null, validation_status:unvalidated, candidate_source:no_candidate_extracted, requires_future_runtime_validation:false}
candidate_generated=false
candidate_validation_attempted=false
candidate_validated=false
candidate_acceptance_status=null
training_status_modified=false
status_overlay_modified=false
executed_sample=false
ran_runtime_tools=false
ran_ida=false
ran_ghidra=false
ran_strings=false
ran_file=false
ran_objdump=false
ran_radare2=false
ran_static_extraction=true
ran_debugger=false
ran_hook=false
ran_emulator=false
ran_probe=false
ran_bruteforce=false
ran_dictionary_search=false
candidate_search_performed=false
uploaded_binary=false
binary_content_recorded=false
full_strings_dump_recorded=false
full_import_table_recorded=false
full_section_dump_recorded=false
full_disassembly_recorded=false
full_decompilation_recorded=false
bounded_negative_results=[preserve no Sorry direct/indirect refs; no complete candidate proof chain]
next_recommended_mainline=tool_integration
next_recommended_action=Generate a deeper bounded local disassembly/xref evidence extraction decision for cpp2_883e67b9, focused on assert_path 0x4061c3 loop reconstruction and precise comparison operand recovery. Do not run runtime validation, brute force, dictionary search, fuzzing, enumeration, candidate ranking, or candidate guesses until a concrete static candidate exists.
generated_at=<timestamp>
```

### Phase C — artifact_index registration

Update the existing key:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_883e67b9_targeted_static_solving"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_883e67b9_targeted_static_solving"]
artifact_index.artifact_refs["local_reverse_cpp2_883e67b9_targeted_static_solving"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_targeted_static_solving
path=project_state\\local_reverse_cpp2_883e67b9_targeted_static_solving.json
freshness=current
source_run=round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
static_solving_status=PARTIAL
identity_verified=true
training_status_before=inventory_only
candidate_generated=false
candidate_validated=false
candidate_acceptance_status=null
source_static_extraction_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
next_recommended_mainline=tool_integration
```

Do not modify `local_reverse_training_status.json` or `status_overlay.json`.

### Phase D — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1",
  "round_id": "round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1",
  "based_on_decision_id": "decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1",
  "status": "PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Expected successful rework mapping:

```text
status=PARTIAL
acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
```

---

## 7. Tests

Required checks:

```bat
.venv\Scripts\python -m py_compile reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

`pytest_result.txt` must include:

```text
decision_id=decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1
report_id=report_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1
round_id=round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v1
```

Content assertions must include:

```text
1. artifact.mainline == reverse_solving
2. report正文不再声称 mainline=tool_integration
3. static_solving_status == PARTIAL when candidate_generated=false
4. report status == PARTIAL
5. acceptance_recommendation == ACCEPTED_WITH_LIMITATIONS
6. schema uses source_static_extraction_artifact/source_static_extraction_status
7. schema includes prior_raw_offset_fields_treated_as and mapping_correction_summary
8. candidate_validation_attempted=false
9. candidate_acceptance_status=null
10. next_recommended_action does not contain runtime validation guesses
11. next_recommended_action does not contain brute force / dictionary / fuzz / enumeration / candidate ranking / candidate guesses
12. artifact_index latest_artifacts_v2 mirrors PARTIAL and source_run=this rework round
13. training_status/status_overlay not modified
14. no sample executable was run
15. no runtime tools/debugger/hook/emulator/probe were run
16. no brute force/dictionary/search/fuzzing/candidate enumeration was run
17. no binary was uploaded, copied, embedded, or committed
18. no full strings/imports/sections/disassembly/decompilation dump was recorded
19. final lint-report ran after report write
20. git diff --name-status only contains allowed files
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage.

---

## 8. Stop Conditions

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. artifact and report mainline are reverse_solving;
2. static_solving_status is PARTIAL;
3. artifact schema uses required field names;
4. no candidate is claimed;
5. next recommendation is bounded static evidence extraction only;
6. artifact_index/report/pytest_result are aligned with this rework decision;
7. training_status/status_overlay remain unchanged;
8. no runtime/search/validation action occurred.
```

Stop with `BLOCKED` if:

```text
1. source static extraction artifact is missing/stale/not SUCCESS;
2. training state has drifted and cannot be safely preserved;
3. required artifact cannot be normalized without rerunning forbidden actions.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. any forbidden execution/tool/search action occurs;
2. candidate validation is attempted;
3. training_status/status_overlay are modified;
4. artifact_index/report/pytest_result do not align with this rework decision.
```
