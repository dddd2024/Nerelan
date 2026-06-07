```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_883e67b9_targeted_static_solving_v1",
  "round_id": "round_20260607_cpp2_883e67b9_targeted_static_solving_v1",
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

本轮主线是 **reverse_solving**，任务是对 `cpp2_883e67b9` 做 **targeted static solving**。

目标：基于上一轮 current bounded static extraction artifact，围绕 `assert_path=0x4061c3`、`failure_path=0x4010e6`、`prompt_path=0x4010ad` 做有界静态分析，恢复输入长度/初始阶段判断/比较逻辑/常量表或变换证据链。允许在证据充分时产出 **unvalidated_candidate_hypothesis**；禁止运行样本、runtime validation、debugger/hook/emulator、bruteforce、字典搜索、训练状态修改。

必须产出：

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
```

本轮不是训练状态同步轮。即使产出候选，也只能是未验证静态假设，不得写入 `known_candidate`、不得标记 solved。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 bounded static extraction 审计结论为 **ACCEPTED_WITH_LIMITATIONS**：

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json:
  decision_id=decision_20260607_cpp2_883e67b9_bounded_static_extraction_v1
  round_id=round_20260607_cpp2_883e67b9_bounded_static_extraction_v1
  sample_id=cpp2_883e67b9
  identity_verified=true
  extraction_status=SUCCESS
  training_status_before=inventory_only
  known_candidate_before=""
  source_readiness_status=READY
  static_tools_used=[python_stdlib_pe_parser, bounded_strings_extractor, push_imm32_xref_searcher]
  structured_evidence_ready=false
  candidate_generated=false
  candidate_validation_attempted=false
  candidate_validated=false
  training_status_modified=false
  executed_sample=false
```

Bounded extraction facts to use:

```text
PE layout:
  file_type=PE32
  architecture=i386
  image_base=0x400000
  entry_point_rva=0x1c10
  sections=.text,.rdata,.data,.idata,.reloc

String anchors:
  input_prompt:              "Please input your flag:"             VA=0x42702c, ref_va=0x4010ad
  failure_message:           "--- Sorry, but try it again! ---"    VA=0x427069, no direct push refs found
  debug_assert:              "flag == 0 || flag == 1"              VA=0x427c44, ref_va=0x4061c3
  initial_phase_failure:     "You are wrong in the initial phase!" VA=0x4281e8, ref_va=0x4010e6

Candidate regions:
  prompt_path:  anchor_ref_va=0x4010ad, region_rva_start=0xead,  region_rva_end=0x12ad, region_size=1024
  assert_path:  anchor_ref_va=0x4061c3, region_rva_start=0x5fc3, region_rva_end=0x64c3, region_size=1280
  failure_path: anchor_ref_va=0x4010e6, region_rva_start=0xce6,  region_rva_end=0x12e6, region_size=1280

Bounded negative result:
  "--- Sorry, but try it again! ---" has no direct push imm32 refs in .text and may be referenced indirectly.
```

Important caution from audit:

```text
The previous artifact's string_anchor_map used raw_offset values that appear equal to RVA values. Before using any raw offset for byte reads or local decoding, Codex must rederive file_offset/RVA/VA mapping from the PE section table and record whether prior raw_offset fields were corrected or treated as RVA-only.
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

Tool availability/context:

```text
Existing project interfaces checked in prior rounds:
  reverse_agent/local_reverse_single_sample_static_triage.py requires IDA
  reverse_agent/tool_runners.py supports IDA/OLLY config
  reverse_agent/local_reverse_console_validator.py exists but is forbidden in this round
  reverse_agent/ida_scripts/ exists
  local_reverse_xref_disassembly.py has useful PEMapping/RVA helper patterns
Current external tools from readiness:
  IDA direct unavailable
  Ghidra unavailable
  radare2 unavailable
  objdump unavailable
Allowed fallback:
  bounded Python stdlib PE parsing and local byte-window analysis
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
6. Do not brute force, dictionary search, fuzz, enumerate inputs, or rank candidates.
7. Do not solve by broad candidate search.
8. Do not modify project_state/local_reverse_training_status.json.
9. Do not modify training_materials/local_reverse/status_overlay.json.
10. Do not mark cpp2_883e67b9 solved, blocked, validated, or partially solved.
11. Do not write known_candidate for cpp2_883e67b9.
12. Do not alter accepted solved facts for cpp2_2f64e68d / 10013 or cpp2_32f1713e / KEEP_DREAM.
13. Do not upload, copy into repo, base64-embed, or commit the sample binary.
14. Do not store raw binary bytes, full strings dump, full imports, full sections, full disassembly, full decompilation, screenshots, memory dumps, or bulky static output.
15. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
16. Do not modify .codex-skills.
17. Do not create duplicate IDA/Ghidra/debugger/static extraction/runtime interfaces.
18. Do not use stale IDA/Ghidra/static artifacts as current evidence for cpp2_883e67b9.
19. Do not claim IDA/Ghidra evidence was used unless current artifact proves it for this sample and this round.
20. Do not use previous raw_offset fields as file offsets until PE mapping is rederived.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current bounded static extraction and readiness artifacts for cpp2_883e67b9.
3. Read local_reverse_training_status/status_overlay only for current state verification.
4. Inspect existing repository helpers for PE mapping, xref disassembly, byte-window extraction, StructuredEvidence, solver templates, artifact_index helpers.
5. Resolve and read only E:\reverse\逆向课程2024春02\CPP2.exe for sha256/size and bounded static byte-window analysis.
6. Use bounded Python stdlib PE parser and local byte-window inspection if IDA/Ghidra/radare2 remain unavailable.
7. Record small opcode windows and decoded local instruction summaries only for the targeted regions.
8. Produce unvalidated_candidate_hypothesis only if a non-search static proof chain is complete.
9. Generate project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json.
10. Register the artifact in artifact_index.
11. Write codex_execution_report.md and pytest_result.txt.
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
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Must inspect bounded existing capability surface before adding any code or local parser snippets:

```text
Search repository for directly relevant interfaces/schemas:
  local_reverse_xref_disassembly
  local_reverse_single_sample_static_triage
  static_extraction
  StructuredEvidence
  solver templates
  xor solver
  bit operation solver
  pe parser
  rva
  xref
  artifact_index
  local_reverse

Inspect only directly relevant modules/tests discovered by the search.
Prefer existing interfaces; do not create duplicates.
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
2. Did it confirm mainline=reverse_solving?
3. Did it confirm this is targeted static solving, not runtime validation?
4. Did it confirm task_packet remains advisory?
5. Did it confirm source bounded_static_extraction artifact is current/SUCCESS/identity_verified?
6. Did it confirm cpp2_883e67b9 remains inventory_only/known_candidate="" before and after?
7. Did it confirm cpp2_32f1713e/KEEP_DREAM and cpp2_2f64e68d/10013 solved facts remain unchanged?
8. Did it inspect existing PE/xref/static extraction/solver/StructuredEvidence interfaces before acting?
9. Which existing helpers or fallback parsers were used?
10. Did it avoid creating duplicate tool interfaces?
11. Did it resolve the sample only through command-scoped LOCAL_REVERSE_ROOT=E:\reverse?
12. Did it reverify size_bytes=196689 and sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8?
13. Did it rederive file_offset/RVA/VA mappings and address the prior raw_offset caution?
14. Did it analyze only bounded windows around prompt_path/assert_path/failure_path and optional indirect Sorry reference search?
15. Did it recover any input length, initial phase, comparison logic, constants, table, branch predicate, or transform evidence?
16. If it produced unvalidated_candidate_hypothesis, is the proof chain non-search and static-only?
17. If no candidate was produced, did it record bounded blockers and next evidence needed?
18. Did it avoid brute force, dictionary search, candidate enumeration, and ranking?
19. Did it avoid sample execution/runtime validation/debugger/hook/emulator/probe?
20. Did it avoid binary upload/copy/embed/full dumps?
21. Did it avoid modifying training_status/status_overlay?
22. Did it generate project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json?
23. Did it register the artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
24. Did the artifact make a clear bounded next recommendation, e.g. runtime validation if candidate exists, or deeper IDA/static evidence extraction if not?
25. Did it explain negative_results unchanged or non-use?
26. Did it run required py_compile/pytest/lint/status/git checks?
27. Did pytest_result.txt use this decision_id/report_id/round_id?
28. Did final lint-report run after report write?
29. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded targeted static solving only.

### Phase A — state preflight

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

### Phase B — helper/interface inspection

Search/inspect existing project helpers before implementing any local analysis:

```text
local_reverse_xref_disassembly.py
PE mapping helpers
static extraction helpers
StructuredEvidence schema/converters
solver templates for XOR/bit operation/string compare/table lookup
artifact_index helpers
```

Decision rule:

```text
1. Reuse existing PE mapping/xref helpers if they already support bounded byte-window analysis.
2. Do not add a generic new tool integration.
3. If no helper is reusable, use a narrow in-round Python stdlib parser only to generate the artifact; avoid committing a new reusable module unless absolutely necessary.
4. Do not add IDA/Ghidra/radare2 integrations in this round.
```

### Phase C — command-scoped identity and PE mapping recheck

Resolve only this file:

```text
LOCAL_REVERSE_ROOT=E:\reverse
relative_path=逆向课程2024春02/CPP2.exe
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
```

Recompute:

```text
size_bytes
sha256
section table
raw_to_rva
rva_to_raw
va_to_raw
```

Record explicitly:

```text
prior_raw_offset_fields_treated_as=RVA_only|corrected_file_offsets|confirmed_file_offsets
mapping_correction_summary={...}
```

### Phase D — bounded window analysis

Analyze only bounded windows:

```text
1. prompt_path around VA 0x4010ad.
2. failure_path around VA 0x4010e6.
3. assert_path around VA 0x4061c3.
4. Optional bounded indirect search for "--- Sorry, but try it again! ---" reference, limited to local data/code reference patterns and a small result cap.
```

For each region, record:

```text
region_id
anchor_va
window_va_start/window_va_end
window_size
local_instruction_summary_or_opcode_features bounded to a small list
constants_seen bounded list
branch_predicates_seen bounded list
calls_seen bounded list
stack_or_buffer_hints bounded list
semantic_hypothesis
solver_relevance
```

Preferred recovery targets:

```text
input length check
initial phase predicate
byte/char comparison loop
target constant/table bytes
transform formula such as XOR/shift/bit swap/add/sub/mod
success/failure branch condition
expected candidate length or character class
```

No broad search. No candidate enumeration. No runtime.

### Phase E — artifact generation

Generate:

```text
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
```

Required top-level fields:

```text
schema_version=1
mainline=reverse_solving
round_id=round_20260607_cpp2_883e67b9_targeted_static_solving_v1
decision_id=decision_20260607_cpp2_883e67b9_targeted_static_solving_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
command_scoped_root=E:\reverse
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
expected_size_bytes=196689
identity_verified=true|false
static_solving_status=SUCCESS|PARTIAL|BLOCKED|FAILED
training_status_before=inventory_only
known_candidate_before=""
source_static_extraction_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
source_static_extraction_status=SUCCESS
prior_raw_offset_fields_treated_as=RVA_only|corrected_file_offsets|confirmed_file_offsets
mapping_correction_summary={...bounded...}
existing_helpers_checked=true
helpers_or_tools_used=[...]
target_regions_analyzed=[...bounded...]
logic_evidence={...bounded...}
solver_classification={type:string_compare|xor|bit_operation|table_lookup|unknown, confidence:...}
static_proof_chain=[...]
unvalidated_candidate_hypothesis=null|{candidate, confidence, validation_status:unvalidated, proof_chain_summary, requires_future_runtime_validation:true}
candidate_generated=true|false
candidate_validation_attempted=false
candidate_validated=false
candidate_acceptance_status=unvalidated|null
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
next_recommended_action=<bounded next step>
generated_at=<timestamp>
```

Status mapping guidance:

```text
SUCCESS: static logic and candidate hypothesis recovered with a coherent non-search proof chain.
PARTIAL: relevant regions and some logic recovered, but no candidate or incomplete proof chain.
BLOCKED: source artifact missing/stale, identity mismatch, or no bounded static path.
FAILED: forbidden action, malformed artifact, or inconsistent metadata.
```

### Phase F — artifact_index registration

Register regardless of static_solving_status:

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
source_run=round_20260607_cpp2_883e67b9_targeted_static_solving_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
static_solving_status=SUCCESS|PARTIAL|BLOCKED|FAILED
identity_verified=true|false
training_status_before=inventory_only
candidate_generated=true|false
candidate_validated=false
candidate_acceptance_status=unvalidated|null
source_static_extraction_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
next_recommended_mainline=<value>
```

Do not modify `local_reverse_training_status.json` or `status_overlay.json`.

### Phase G — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_883e67b9_targeted_static_solving_v1",
  "round_id": "round_20260607_cpp2_883e67b9_targeted_static_solving_v1",
  "based_on_decision_id": "decision_20260607_cpp2_883e67b9_targeted_static_solving_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
static_solving_status=SUCCESS -> status=SUCCESS, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
static_solving_status=PARTIAL -> status=PARTIAL, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
static_solving_status=BLOCKED -> status=BLOCKED, acceptance_recommendation=BLOCKED
static_solving_status=FAILED -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

Even if a candidate hypothesis is produced, use `ACCEPTED_WITH_LIMITATIONS` because runtime validation is intentionally deferred.

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
decision_id=decision_20260607_cpp2_883e67b9_targeted_static_solving_v1
report_id=report_20260607_cpp2_883e67b9_targeted_static_solving_v1
round_id=round_20260607_cpp2_883e67b9_targeted_static_solving_v1
```

Content assertions to record:

```text
1. decision_packet is the sole authority.
2. mainline=reverse_solving.
3. source bounded_static_extraction artifact is current/SUCCESS/identity_verified.
4. cpp2_883e67b9 training_status remains inventory_only/known_candidate="".
5. sample identity reverified by size and sha256, or artifact records BLOCKED reason.
6. prior raw_offset caution is addressed by rederived PE mapping.
7. existing PE/xref/static extraction/solver/StructuredEvidence helpers were checked before tool use.
8. no duplicate tool interface was created.
9. artifact exists at project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json.
10. artifact_index registers local_reverse_cpp2_883e67b9_targeted_static_solving as current.
11. artifact records target regions analyzed and logic evidence or bounded blockers.
12. candidate, if generated, is only unvalidated_candidate_hypothesis.
13. candidate_validation_attempted=false.
14. training_status/status_overlay were not modified.
15. no sample executable was run.
16. no runtime tools/debugger/hook/emulator/probe were run.
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
1. source static extraction artifact is current/SUCCESS and sample identity is reverified;
2. target regions are analyzed with corrected file_offset/RVA/VA mapping;
3. static proof chain is coherent and, if candidate is produced, it is recorded only as unvalidated_candidate_hypothesis;
4. artifact is produced and registered current;
5. no runtime validation or forbidden dynamic/search action occurred;
6. training_status/status_overlay remain unchanged;
7. tests/lint/report metadata align with this decision/report/round.
```

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. identity and mapping are verified;
2. bounded region analysis recovers partial logic but no complete candidate proof chain;
3. artifact records blockers and next bounded evidence step;
4. no forbidden action occurred.
```

Stop with `BLOCKED` if:

```text
1. source static extraction artifact is missing/stale/not SUCCESS;
2. sample file is missing under command-scoped root;
3. size/sha256 mismatch;
4. corrected PE mapping cannot be established;
5. no bounded static solving path is available.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. any forbidden execution/tool/search action occurs;
2. candidate validation is attempted;
3. training_status/status_overlay are modified;
4. artifact_index/report/pytest_result do not align with this decision.
```
