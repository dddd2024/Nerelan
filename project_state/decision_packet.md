```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1",
  "round_id": "round_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1",
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

本轮主线是 **tool_integration**，任务是对 `cpp2_883e67b9` 做 **deeper bounded static evidence extraction / local disassembly / loop reconstruction**。

目标：基于当前 `targeted_static_solving` 的 PARTIAL 证据，围绕 `assert_path` 的 `0x4061c3` 附近循环、比较常量、局部控制流和可能的比较操作数做更深但有界的静态证据提取，产出可供下一轮 targeted static solving 使用的结构化证据。

本轮不是求解轮，不生成 candidate，不做 runtime validation，不运行样本，不改训练状态。

必须产出：

```text
project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 `targeted_static_solving_rework_v2` 审计结论为 **ACCEPTED_WITH_LIMITATIONS**：

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json:
  decision_id=decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
  round_id=round_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
  mainline=reverse_solving
  sample_id=cpp2_883e67b9
  identity_verified=true
  static_solving_status=PARTIAL
  partial_reason=bounded_region_analysis_complete_but_no_candidate_extracted
  source_static_extraction_artifact=project_state\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
  source_static_extraction_status=SUCCESS
  prior_raw_offset_fields_treated_as=corrected_file_offsets
  candidate_generated=false
  candidate_validation_attempted=false
  candidate_validated=false
  candidate_acceptance_status=null
  training_status_modified=false
  executed_sample=false
```

Known bounded static facts to preserve and deepen:

```text
PE32 i386, image_base=0x400000
sections=.text,.rdata,.data,.idata,.reloc
input_prompt string: "Please input your flag:" VA=0x42702c, direct ref VA=0x4010ad
initial_phase_failure string: "You are wrong in the initial phase!" VA=0x4281e8, direct ref VA=0x4010e6
debug_assert string: "flag == 0 || flag == 1" VA=0x427c44, direct ref VA=0x4061c3
failure string: "--- Sorry, but try it again! ---" VA=0x427069, no direct refs found
assert_path window: rva 0x5f00-0x6500, anchor VA=0x4061c3
assert_path constants include: 194, 141, 133, 0x1102, 0x10c, 0x108, 255, 0x100
loop indicators include backward jumps at RVAs 0x5f68, 0x6081, 0x60a4, 0x60b6, 0x61e8
complete_candidate_proof_chain=false
no_complete_formula_recovered=true
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

Existing tool/interface context:

```text
Existing project helpers observed in prior decisions:
  local_reverse_xref_disassembly.py patterns may be relevant for PE mapping/local byte windows
  reverse_agent/local_reverse_single_sample_static_triage.py requires IDA
  reverse_agent/tool_runners.py supports IDA/OLLY config
  reverse_agent/ida_scripts/ exists
Current external tool availability from readiness:
  IDA direct unavailable
  Ghidra unavailable
  radare2 unavailable
  objdump unavailable
Allowed fallback:
  bounded Python stdlib PE parser plus narrow local x86 byte-window decoding/annotation if no existing helper suffices
```

negative_results mainly concerns old `samplereverse` directions. This round must not repeat blind search, budget expansion, stale artifact assumptions, full solve_reports commits, runtime probing, or candidate search.

Skill profile must remain `reverse-agent-iteration@v2`, which is active in `.codex-skills/registry.json`.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run the sample executable.
3. Do not execute any candidate or control input.
4. Do not perform runtime validation.
5. Do not attach debugger, hook, emulator, instrumentation probe, breakpoint probe, dynamic trace collector, winpty, console validator, or runtime harness.
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
20. Do not expand beyond bounded local disassembly / evidence extraction around specified regions.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current targeted static solving, bounded static extraction and readiness artifacts for cpp2_883e67b9.
3. Read local_reverse_training_status/status_overlay only for state verification.
4. Inspect existing repository helpers for PE mapping, local xref, byte-window extraction, StructuredEvidence and artifact_index helpers.
5. Resolve and read only E:\reverse\逆向课程2024春02\CPP2.exe for sha256/size and bounded byte-window evidence extraction.
6. Use bounded Python stdlib PE mapping and local x86 instruction decoding/annotation only inside the specified windows if existing helpers are insufficient.
7. Record small local instruction summaries, operand summaries, branch summaries and loop summaries; do not dump full disassembly.
8. Generate a structured evidence artifact for the next static solving round.
9. Register the artifact in artifact_index.
10. Write codex_execution_report.md and pytest_result.txt.
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
project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Must inspect bounded existing capability surface before writing analysis logic:

```text
Search repository for directly relevant helpers/schemas:
  local_reverse_xref_disassembly
  PE mapping
  disassembly
  x86
  capstone
  StructuredEvidence
  static_extraction
  artifact_index
  local_reverse

Inspect only directly relevant modules/tests discovered by the search.
Prefer existing helpers; do not create duplicate interfaces.
```

May inspect if directly relevant and bounded:

```text
project_state/local_reverse_inventory.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json
existing project_state artifacts describing current tool availability, only as capability hints.
```

Do not read by default:

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse full tree beyond E:\reverse\逆向课程2024春02\CPP2.exe
```

---

## 5. Required Audit

Codex report must answer:

```text
1. Did it confirm decision_packet is the sole execution authority?
2. Did it confirm mainline=tool_integration?
3. Did it confirm this is bounded static evidence extraction / local disassembly, not solving or runtime validation?
4. Did it confirm task_packet remains advisory?
5. Did it confirm targeted_static_solving source artifact is current/PARTIAL/rework_v2/identity_verified?
6. Did it confirm source bounded_static_extraction artifact is current/SUCCESS/identity_verified?
7. Did it confirm cpp2_883e67b9 remains inventory_only/known_candidate="" before and after?
8. Did it confirm cpp2_32f1713e/KEEP_DREAM and cpp2_2f64e68d/10013 solved facts remain unchanged?
9. Did it inspect existing PE/local xref/disassembly/StructuredEvidence/artifact_index helpers before acting?
10. Which existing helpers or fallback parser/decoder were used?
11. Did it avoid creating duplicate tool interfaces?
12. Did it resolve the sample only through command-scoped LOCAL_REVERSE_ROOT=E:\reverse?
13. Did it reverify size_bytes=196689 and sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8?
14. Did it extract only bounded local disassembly/evidence around assert_path 0x4061c3 and directly relevant loops?
15. Did it recover bounded instruction/operand summaries for compare constants and loop branches?
16. Did it avoid full disassembly and full binary dumps?
17. Did it avoid candidate generation, runtime validation, brute force, dictionary search, fuzzing, enumeration and ranking?
18. Did it avoid sample execution/runtime/debugger/hook/emulator/probe?
19. Did it avoid modifying training_status/status_overlay?
20. Did it generate project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json?
21. Did it register the artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
22. Did the artifact provide clear next bounded recommendation for targeted static solving refinement, not runtime validation?
23. Did it explain negative_results unchanged or non-use?
24. Did it run required py_compile/pytest/lint/status/git checks?
25. Did pytest_result.txt use this decision_id/report_id/round_id?
26. Did final lint-report run after report write?
27. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded static evidence extraction only.

### Phase A — state preflight

Use `.venv\Scripts\python` for repository Python commands.

Verify:

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json:
  sample_id == cpp2_883e67b9
  identity_verified == true
  static_solving_status == PARTIAL
  decision_id == decision_20260607_cpp2_883e67b9_targeted_static_solving_rework_v2
  candidate_generated == false
  candidate_validation_attempted == false
  executed_sample == false
  next_recommended_mainline == tool_integration

project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json:
  sample_id == cpp2_883e67b9
  identity_verified == true
  extraction_status == SUCCESS
  source_readiness_status == READY

project_state/local_reverse_training_status.json:
  cpp2_883e67b9.training_status == inventory_only
  cpp2_883e67b9.known_candidate == ""
  cpp2_883e67b9.blocked_reason == ""
```

If state has drifted, stop as BLOCKED rather than proceeding silently.

### Phase B — helper/interface inspection

Search/inspect existing project helpers before implementing local analysis:

```text
local_reverse_xref_disassembly.py
PE mapping helpers
local byte-window extraction helpers
StructuredEvidence schema/converters
artifact_index helpers
capstone dependency or x86 decoding utility if present
```

Decision rule:

```text
1. Reuse existing helper if it can provide bounded local instruction summaries.
2. If no helper exists, use a narrow in-round parser/decoder only to generate this artifact; do not add a general new tool interface unless absolutely necessary.
3. Do not add IDA/Ghidra/radare2 integrations in this round.
4. If no bounded local disassembly path is available, stop as BLOCKED and record missing capability.
```

### Phase C — command-scoped identity recheck

Resolve only this file:

```text
LOCAL_REVERSE_ROOT=E:\reverse
relative_path=逆向课程2024春02/CPP2.exe
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
```

Recheck `size_bytes` and `sha256`. Do not print or store raw bytes.

### Phase D — bounded local disassembly / loop evidence extraction

Analyze only these bounded regions:

```text
primary_assert_window:
  VA around 0x4061c3
  RVA window 0x5f00-0x6500, or a smaller justified subset if enough

loop_focus_sites:
  backward jumps at RVAs 0x5f68, 0x6081, 0x60a4, 0x60b6, 0x61e8

optional prompt/failure context:
  VA 0x4010ad and 0x4010e6 only if needed to link input setup or failure branch
```

For each extracted bounded region, record only summarized evidence:

```text
region_id
window_start_va/window_end_va/window_size
instruction_count_decoded or partial_decode_status
compare_constants with operand context if recoverable
branch_edges bounded list
loop_summaries bounded list
calls bounded list
stack/buffer access hints bounded list
register/operand flow hints bounded list
possible_table_or_state_accesses bounded list
failure/success branch hypotheses if bounded and justified
confidence and limitations
```

Do not record full disassembly. Do not infer or emit a candidate. Do not enumerate possible input.

### Phase E — artifact generation

Generate:

```text
project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json
```

Required top-level fields:

```text
schema_version=1
mainline=tool_integration
round_id=round_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1
decision_id=decision_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
command_scoped_root=E:\reverse
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
expected_size_bytes=196689
identity_verified=true|false
evidence_extraction_status=SUCCESS|PARTIAL|BLOCKED|FAILED
training_status_before=inventory_only
known_candidate_before=""
source_targeted_static_solving_artifact=project_state\\local_reverse_cpp2_883e67b9_targeted_static_solving.json
source_targeted_static_solving_status=PARTIAL
source_static_extraction_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
source_static_extraction_status=SUCCESS
existing_helpers_checked=true
helpers_or_tools_used=[...]
local_disassembly_available=true|false
bounded_regions_analyzed=[...]
loop_evidence=[...]
compare_operand_evidence=[...]
branch_evidence=[...]
state_or_table_access_hints=[...]
structured_evidence_ready=true|false
structured_evidence={...bounded or null...}
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
ran_static_extraction=true|false
ran_local_disassembly=true|false
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
bounded_negative_results=[...]
next_recommended_mainline=reverse_solving|tool_integration
next_recommended_action=<bounded static-only next step>
generated_at=<timestamp>
```

### Phase F — artifact_index registration

Register regardless of status:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction"]
artifact_index.artifact_refs["local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_bounded_loop_evidence_extraction
path=project_state\\local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json
freshness=current
source_run=round_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
evidence_extraction_status=SUCCESS|PARTIAL|BLOCKED|FAILED
identity_verified=true|false
training_status_before=inventory_only
candidate_generated=false
candidate_validation_attempted=false
candidate_validated=false
source_targeted_static_solving_artifact=project_state\\local_reverse_cpp2_883e67b9_targeted_static_solving.json
next_recommended_mainline=<value>
```

Do not modify `local_reverse_training_status.json` or `status_overlay.json`.

### Phase G — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1",
  "round_id": "round_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1",
  "based_on_decision_id": "decision_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
evidence_extraction_status=SUCCESS -> status=SUCCESS, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
evidence_extraction_status=PARTIAL -> status=PARTIAL, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
evidence_extraction_status=BLOCKED -> status=BLOCKED, acceptance_recommendation=BLOCKED
evidence_extraction_status=FAILED -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

Use `ACCEPTED_WITH_LIMITATIONS` for SUCCESS/PARTIAL because no candidate solving or validation occurs.

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
decision_id=decision_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1
report_id=report_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1
round_id=round_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1
```

Content assertions to record:

```text
1. decision_packet is the sole authority.
2. mainline=tool_integration.
3. source targeted_static_solving artifact is current/PARTIAL/rework_v2/identity_verified.
4. source bounded_static_extraction artifact is current/SUCCESS/identity_verified.
5. cpp2_883e67b9 training_status remains inventory_only/known_candidate="".
6. existing PE/local disassembly/StructuredEvidence helpers were checked before tool use.
7. no duplicate tool interface was created.
8. artifact exists at project_state/local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction.json.
9. artifact_index registers local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction as current.
10. artifact records bounded local disassembly or BLOCKED/PARTIAL reason.
11. artifact records loop_evidence or bounded_negative_results.
12. candidate_generated=false.
13. candidate_validation_attempted=false.
14. training_status/status_overlay were not modified.
15. no sample executable was run.
16. no runtime validation/debugger/hook/emulator/probe was run.
17. no brute force/dictionary/search/fuzzing/candidate enumeration was run.
18. no binary was uploaded, copied, embedded, or committed.
19. no full strings/imports/sections/disassembly/decompilation dump was recorded.
20. pytest_result uses this decision_id/report_id/round_id.
21. final lint-report ran after report write.
22. git diff --name-status only contains allowed files.
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage.

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. source targeted static solving artifact is current/PARTIAL/rework_v2;
2. sample identity is reverified;
3. bounded local disassembly / loop evidence artifact is produced and registered current;
4. artifact contains bounded loop/operand/branch evidence or precise static blockers;
5. no candidate is generated or validated;
6. no sample execution or forbidden runtime/debugger/search action occurred;
7. training_status/status_overlay remain unchanged;
8. tests/lint/report metadata align with this decision/report/round.
```

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. identity and source artifacts are verified;
2. local disassembly/evidence recovery is incomplete but bounded evidence or blockers are recorded;
3. no forbidden action occurred.
```

Stop with `BLOCKED` if:

```text
1. source targeted static solving artifact is missing/stale/not PARTIAL/rework_v2;
2. source static extraction artifact is missing/stale/not SUCCESS;
3. sample file is missing under command-scoped root;
4. size/sha256 mismatch;
5. no bounded local disassembly/evidence path is available.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. any forbidden execution/tool/search action occurs;
2. candidate is generated or validation attempted;
3. training_status/status_overlay are modified;
4. artifact_index/report/pytest_result do not align with this decision.
```
