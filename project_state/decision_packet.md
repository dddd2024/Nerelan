```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2",
  "round_id": "round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2",
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

本轮主线是 **reverse_solving**，任务是修复 `cpp2_883e67b9_targeted_static_solving` 返工失败遗留问题。

只做 metadata / schema / report / test 修复，不做新静态分析，不运行样本，不改训练状态。

上一轮 rework 仍未修复：

```text
1. artifact.mainline 仍为 tool_integration。
2. report 正文 mainline 仍为 tool_integration。
3. report summary 仍为 SUCCESS / ACCEPTED。
4. artifact 仍使用 source_extraction_artifact / source_extraction_status / raw_offset_correction。
5. artifact 缺少 candidate_validation_attempted=false。
6. artifact 缺少 candidate_acceptance_status=null。
7. next_recommended_action 仍包含 runtime validation guesses / debugger / emulator / bounded brute-force。
8. pytest_result 未检查上述核心条件。
```

必须修复以下文件：

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
.codex-skills/*
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

Current source static extraction artifact is already accepted with limitations:

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json:
  sample_id=cpp2_883e67b9
  identity_verified=true
  extraction_status=SUCCESS
  source_readiness_status=READY
  candidate_generated=false
  candidate_validation_attempted=false
  executed_sample=false
```

Current nonconforming targeted solving artifact contains reusable bounded analysis but wrong metadata/schema:

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json:
  mainline=tool_integration                 # wrong, must be reverse_solving
  static_solving_status=PARTIAL             # correct
  source_extraction_artifact=...            # wrong field name
  source_extraction_status=SUCCESS          # wrong field name
  raw_offset_correction={...}               # wrong field name
  candidate_generated=false                 # correct
  candidate_validated=false                 # correct
  missing candidate_validation_attempted
  missing candidate_acceptance_status
  next_recommended_action still suggests runtime validation guesses/debugger/emulator/brute-force
```

Useful bounded analysis to preserve:

```text
prompt_path around 0x4010ad
failure_path around 0x4010e6
assert_path around 0x4061c3
assert_path constants: 194, 141, 133, 0x1102, 0x10c, 0x108, 255, 0x100
assert_path loop indicators
no candidate extracted
```

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
report status=PARTIAL
acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
candidate_generated=false
candidate_validation_attempted=false
candidate_validated=false
candidate_acceptance_status=null
next step must be deeper bounded static evidence extraction / local disassembly / loop reconstruction only
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
20. Do not leave any next_recommended_action that suggests runtime validation guesses, debugger, emulator, brute force, dictionary search, fuzzing, enumeration, candidate ranking, or candidate guesses.
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

Codex report must answer and pytest_result must explicitly check:

```text
1. artifact.mainline == reverse_solving
2. report正文 mainline == reverse_solving
3. report summary status == PARTIAL
4. report summary acceptance_recommendation == ACCEPTED_WITH_LIMITATIONS
5. artifact.static_solving_status == PARTIAL
6. artifact uses source_static_extraction_artifact
7. artifact uses source_static_extraction_status
8. artifact uses prior_raw_offset_fields_treated_as
9. artifact uses mapping_correction_summary
10. artifact includes candidate_validation_attempted=false
11. artifact includes candidate_acceptance_status=null
12. next_recommended_action does not contain runtime validation guesses
13. next_recommended_action does not contain debugger/emulator
14. next_recommended_action does not contain brute force / dictionary / fuzz / enumeration / ranking / guesses
15. artifact_index latest_artifacts_v2 mirrors PARTIAL, source_run=this rework round, and source_static_extraction_artifact
16. training_status/status_overlay unchanged
17. no sample execution/runtime/debugger/hook/emulator/probe
18. no brute force/dictionary/search/fuzzing/candidate enumeration
19. no binary upload/copy/embed/full dumps
20. final lint-report ran after report write
21. git diff only contains allowed files
```

---

## 6. Implementation Scope

Only rewrite these files:

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

Required corrected artifact values:

```text
schema_version=1
mainline=reverse_solving
round_id=round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
decision_id=decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
command_scoped_root=E:\reverse
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
expected_size_bytes=196689
identity_verified=true
static_solving_status=PARTIAL
partial_reason=bounded_region_analysis_complete_but_no_candidate_extracted
training_status_before=inventory_only
known_candidate_before=""
source_static_extraction_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
source_static_extraction_status=SUCCESS
prior_raw_offset_fields_treated_as=corrected_file_offsets
mapping_correction_summary={bounded summary preserving previous correction: region_rva_start 0xead/0xce6 corrected to anchor RVAs 0x10ad/0x10e6; assert anchor 0x61c3; .rdata string offsets treated safely according to PE mapping}
existing_helpers_checked=true
helpers_or_tools_used=[python_stdlib_pe_parser, bounded_static_window_analysis, local_reverse_xref_disassembly_patterns]
target_regions_analyzed=[preserve prompt/failure/assert summaries]
logic_evidence={preserve constants, loops, no complete candidate proof chain}
solver_classification={type:unknown, confidence:medium, reason:multi_phase_loop_comparison_no_complete_formula}
static_proof_chain=[] OR partial proof chain clearly marked incomplete
unvalidated_candidate_hypothesis=null OR {candidate:null, validation_status:no_candidate, candidate_source:no_candidate_extracted, requires_future_runtime_validation:false}
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
next_recommended_action=Generate a deeper bounded static evidence extraction decision for cpp2_883e67b9, focused on assert_path 0x4061c3 loop reconstruction and precise comparison operand recovery. Do not run runtime validation, debugger/emulator, brute force, dictionary search, fuzzing, enumeration, ranking, or candidate guesses until a concrete static candidate exists.
generated_at=<timestamp>
```

Required artifact_index latest_artifacts_v2 update:

```text
kind=local_reverse_targeted_static_solving
path=project_state\\local_reverse_cpp2_883e67b9_targeted_static_solving.json
freshness=current
source_run=round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
static_solving_status=PARTIAL
identity_verified=true
training_status_before=inventory_only
candidate_generated=false
candidate_validation_attempted=false
candidate_validated=false
candidate_acceptance_status=null
source_static_extraction_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
next_recommended_mainline=tool_integration
```

Required report summary:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2",
  "round_id": "round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2",
  "based_on_decision_id": "decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2",
  "status": "PARTIAL",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Report正文必须写：

```text
mainline=reverse_solving
this is metadata/schema/status rework of targeted static solving artifact
no sample execution, no runtime validation, no debugger/emulator/brute force
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

`pytest_result.txt` must include this rework id triplet:

```text
decision_id=decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
report_id=report_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
round_id=round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
```

`pytest_result.txt` must explicitly include:

```text
artifact.mainline == reverse_solving: PASS
report mainline text == reverse_solving: PASS
report status == PARTIAL: PASS
acceptance_recommendation == ACCEPTED_WITH_LIMITATIONS: PASS
static_solving_status == PARTIAL: PASS
schema source_static_extraction_artifact/source_static_extraction_status present: PASS
prior_raw_offset_fields_treated_as present: PASS
mapping_correction_summary present: PASS
candidate_validation_attempted=false: PASS
candidate_acceptance_status=null: PASS
next_recommended_action forbidden terms absent: PASS
artifact_index mirrors corrected fields: PASS
training_status/status_overlay unchanged: PASS
```

Forbidden-term assertion must fail if `next_recommended_action` contains any of:

```text
runtime validation guesses
debugger
emulator
brute force
brute-force
dictionary
fuzz
enumeration
rank
candidate guesses
```

---

## 8. Stop Conditions

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` only if all required audit and pytest assertions pass.

Stop with `FAILED / REWORK_REQUIRED` if any of the following remain:

```text
1. artifact.mainline != reverse_solving;
2. report status != PARTIAL;
3. acceptance_recommendation != ACCEPTED_WITH_LIMITATIONS;
4. old schema fields are still primary fields;
5. candidate_validation_attempted or candidate_acceptance_status is missing;
6. next_recommended_action contains runtime validation guesses, debugger, emulator, brute force, dictionary, fuzz, enumeration, ranking, or candidate guesses;
7. artifact_index/report/pytest_result do not align with this rework decision;
8. training_status/status_overlay are modified;
9. runtime/search/validation action occurred.
```
