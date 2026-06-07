```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_883e67b9_bounded_static_extraction_v1",
  "round_id": "round_20260607_cpp2_883e67b9_bounded_static_extraction_v1",
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

本轮主线是 **tool_integration**，任务是对 `cpp2_883e67b9` 做 **bounded static extraction**。

目标：基于上一轮 readiness artifact 中确认的 PE32/string triage 信息，定位关键字符串引用、相邻候选比较区域、可能的输入长度/初始阶段判断证据，并将其整理为低 token 的 `StructuredEvidence` 或等价结构化证据。不得生成 candidate，不得求解，不得运行样本。

必须产出：

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
```

本轮允许读取样本文件作只读静态提取；允许使用已有项目接口或成熟静态工具的 bounded 输出；禁止 runtime validation、debugger、hook、emulator、bruteforce、candidate search 和训练状态修改。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 readiness 审计结论为 **ACCEPTED_WITH_LIMITATIONS**：

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json:
  decision_id=decision_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1
  round_id=round_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1
  sample_id=cpp2_883e67b9
  relative_path=逆向课程2024春02/CPP2.exe
  command_scoped_root=E:\reverse
  resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
  expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
  expected_size_bytes=196689
  identity_verified=true
  readiness_status=READY
  training_status_before=inventory_only
  known_candidate_before=""
  existing_tool_interfaces_checked=true
  static_tools_used=[python_stdlib_pe_parser, bounded_strings_extractor]
  structured_evidence_ready=false
  candidate_generated=false
  candidate_validation_attempted=false
  candidate_validated=false
  training_status_modified=false
  status_overlay_modified=false
  executed_sample=false
```

Useful bounded triage facts from the readiness artifact:

```text
file_format=PE32
platform=Windows
architecture=i386
bitness=32
entry_point_rva=0x1c10
image_base=0x400000
sections=[.text, .rdata, .data, .idata, .reloc]
import_table.present=false
compiler_clues=[Visual C++ CRT debug strings present, statically linked runtime]
key_strings:
  0x2702c: "Please input your flag:"             input_prompt
  0x27069: "--- Sorry, but try it again! ---"    failure_message
  0x27c44: "flag == 0 || flag == 1"              debug_assert
  0x281e8: "You are wrong in the initial phase!" failure_message
challenge_type_hypothesis=console_password_checker_with_flag_assert
similarity_to_cpp2_32f1713e=high_same_course_same_name_similar_strings
```

Current training facts must remain unchanged:

```text
project_state/local_reverse_training_status.json:
  cpp2_883e67b9.training_status=inventory_only
  cpp2_883e67b9.known_candidate=""
  cpp2_883e67b9.blocked_reason=""
  cpp2_883e67b9.sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
  cpp2_883e67b9.size_bytes=196689
```

Available/checked tool context from readiness:

```text
project interface available:
  reverse_agent/local_reverse_single_sample_static_triage.py, requires IDA
  reverse_agent/tool_runners.py, IDA/OLLY config and runner
  reverse_agent/local_reverse_console_validator.py, runtime validator but forbidden here
  reverse_agent/ida_scripts/, collect_evidence.py, extract_named_data.py, forced_function_extract.py
current external tool availability:
  IDA direct unavailable
  Ghidra unavailable
  radare2 unavailable
  objdump unavailable
allowed fallback from readiness:
  Python stdlib PE parser + bounded strings extractor
```

Existing interface rule remains: do not create duplicate IDA/Ghidra/debugger/static extraction interfaces. If a suitable existing parser/extractor exists, reuse it. If no wrapper exists and IDA/Ghidra/radare2 are unavailable, use bounded Python stdlib parsing only and record that as a fallback.

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
6. Do not generate a candidate.
7. Do not brute force, dictionary search, fuzz, enumerate inputs, or rank candidates.
8. Do not solve cpp2_883e67b9 in this round.
9. Do not modify project_state/local_reverse_training_status.json.
10. Do not modify training_materials/local_reverse/status_overlay.json.
11. Do not mark cpp2_883e67b9 solved, blocked, validated, or partially solved.
12. Do not alter accepted solved facts for cpp2_2f64e68d / 10013 or cpp2_32f1713e / KEEP_DREAM.
13. Do not upload, copy into repo, base64-embed, or commit the sample binary.
14. Do not store raw binary bytes, full strings dump, full imports, full sections, full disassembly, full decompilation, screenshots, memory dumps, or bulky static output.
15. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
16. Do not modify .codex-skills.
17. Do not create duplicate IDA/Ghidra/debugger/static extraction/runtime interfaces.
18. Do not use stale IDA/Ghidra/static artifacts as current evidence for cpp2_883e67b9.
19. Do not claim IDA/Ghidra evidence was used unless current artifact proves it for this sample and this round.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current readiness artifact for cpp2_883e67b9.
3. Read local_reverse_training_status/status_overlay only for current state verification.
4. Inspect existing repository interfaces for PE/static extraction/StructuredEvidence/artifact_index helpers.
5. Resolve and read only E:\reverse\逆向课程2024春02\CPP2.exe for sha256/size/bounded static extraction.
6. Use existing interfaces if available; otherwise use bounded Python stdlib PE parser/string-reference search.
7. Produce bounded evidence: string RVAs, VA/RVA mapping, small candidate xref windows, candidate compare-region metadata, and next bounded action.
8. Generate project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json.
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
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Must inspect bounded existing capability surface before writing extraction code or invoking tools:

```text
Search repository for directly relevant interfaces/schemas:
  local_reverse_single_sample_static_triage
  static_extraction
  StructuredEvidence
  strings
  pe parser
  rva
  xref
  ida
  ghidra
  radare2
  objdump
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
2. Did it confirm mainline=tool_integration?
3. Did it confirm this is bounded static extraction, not solving or validation?
4. Did it confirm task_packet remains advisory?
5. Did it confirm readiness artifact is current/READY/identity_verified for cpp2_883e67b9?
6. Did it confirm cpp2_883e67b9 remains inventory_only/known_candidate="" before and after?
7. Did it confirm cpp2_32f1713e/KEEP_DREAM and cpp2_2f64e68d/10013 solved facts remain unchanged?
8. Did it inspect existing static extraction / StructuredEvidence / tool interfaces before acting?
9. Which existing interfaces/tools were available and which were used?
10. Did it avoid creating duplicate tool interfaces?
11. Did it resolve the sample only through command-scoped LOCAL_REVERSE_ROOT=E:\reverse?
12. Did it reverify size_bytes=196689 and sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8?
13. Did it map key string offsets to RVAs/VAs in bounded form?
14. Did it attempt bounded xref/reference discovery from .text to key string RVAs/VAs?
15. Did it identify bounded candidate functions/regions/windows without full disassembly dump?
16. Did it emit StructuredEvidence or explain why structured_evidence_ready=false?
17. Did it avoid candidate generation, brute force, dictionary search, and input enumeration?
18. Did it avoid sample execution/runtime validation/debugger/hook/emulator/probe?
19. Did it avoid binary upload/copy/embed/full dumps?
20. Did it avoid modifying training_status/status_overlay?
21. Did it generate project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json?
22. Did it register the artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
23. Did the artifact make a clear bounded next recommendation, e.g. targeted static solving, IDA setup, or deeper bounded xref extraction?
24. Did it explain negative_results unchanged or non-use?
25. Did it run required py_compile/pytest/lint/status/git checks?
26. Did pytest_result.txt use this decision_id/report_id/round_id?
27. Did final lint-report run after report write?
28. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded static extraction only.

### Phase A — state preflight

Use `.venv\Scripts\python` for repository Python commands.

Verify:

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json:
  sample_id == cpp2_883e67b9
  identity_verified == true
  readiness_status == READY
  expected_sha256 == 883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
  expected_size_bytes == 196689
  candidate_generated == false
  candidate_validation_attempted == false
  executed_sample == false

project_state/local_reverse_training_status.json:
  cpp2_883e67b9.training_status == inventory_only
  cpp2_883e67b9.known_candidate == ""
  cpp2_883e67b9.blocked_reason == ""
```

If readiness/training state has drifted, stop as BLOCKED rather than proceeding silently.

### Phase B — existing interface inspection

Search/inspect existing project interfaces before implementing extraction logic:

```text
local_reverse_single_sample_static_triage.py
static extraction helpers
StructuredEvidence schema/converters
artifact_index helpers
IDA/Ghidra/radare2 wrappers
PE parsing or RVA helpers
```

Decision rule:

```text
1. Reuse existing helpers if they already support bounded PE/string/RVA extraction.
2. Do not create a generic new tool interface.
3. If no helper exists, implement only narrow local script/code inside the current execution workflow or minimal project_state-safe helper if absolutely necessary; prefer artifact-only bounded parsing over adding reusable code.
4. Do not add IDA/Ghidra/radare2 integrations in this round.
```

### Phase C — command-scoped identity recheck

Resolve only this file:

```text
LOCAL_REVERSE_ROOT=E:\reverse
relative_path=逆向课程2024春02/CPP2.exe
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
```

Allowed identity check:

```bat
cmd /c "set LOCAL_REVERSE_ROOT=E:\reverse&& .venv\Scripts\python -c \"import os, pathlib, hashlib; p=pathlib.Path(os.environ['LOCAL_REVERSE_ROOT'])/'逆向课程2024春02'/'CPP2.exe'; b=p.read_bytes(); print(p); print(len(b)); print(hashlib.sha256(b).hexdigest())\""
```

Do not print or store raw bytes.

### Phase D — bounded static extraction

Use the PE section mapping from readiness. Extract bounded evidence only:

```text
1. Confirm PE layout and section RVA/raw mappings.
2. Convert key string raw offsets to RVA and VA.
3. Search .text for little-endian immediate references to key string VAs/RVAs if applicable.
4. If direct xrefs are not found, record bounded negative result and search nearby code/data references only within a small bounded window.
5. Identify at most a small number of candidate reference sites or function/region windows.
6. For each candidate window, record offset/RVA/VA, reason, nearby opcode bytes limited to a small window, and semantic hypothesis such as prompt path/failure path/assert path.
7. Do not dump full .text, full strings, full imports, full sections, full disassembly, or full decompilation.
8. Do not derive final password/candidate.
```

Suggested evidence categories:

```text
input_prompt_anchor
failure_message_anchor
initial_phase_failure_anchor
debug_assert_anchor
candidate_compare_or_branch_region
unknown_reference_region
bounded_negative_result
```

### Phase E — artifact generation

Generate:

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
```

Required top-level fields:

```text
schema_version=1
mainline=tool_integration
round_id=round_20260607_cpp2_883e67b9_bounded_static_extraction_v1
decision_id=decision_20260607_cpp2_883e67b9_bounded_static_extraction_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
command_scoped_root=E:\reverse
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
expected_size_bytes=196689
identity_verified=true|false
extraction_status=SUCCESS|PARTIAL|BLOCKED|FAILED
training_status_before=inventory_only
known_candidate_before=""
source_readiness_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
source_readiness_status=READY
existing_tool_interfaces_checked=true
static_tools_used=[...]
pe_layout_summary={...bounded...}
string_anchor_map=[...bounded...]
xref_search_summary={...bounded...}
candidate_regions=[...bounded...]
structured_evidence_ready=true|false
structured_evidence={...bounded or null...}
candidate_generated=false
candidate_validation_attempted=false
candidate_validated=false
training_status_modified=false
status_overlay_modified=false
executed_sample=false
ran_runtime_tools=false
ran_ida=true|false
ran_ghidra=true|false
ran_strings=true|false
ran_file=true|false
ran_objdump=true|false
ran_radare2=true|false
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
next_recommended_mainline=tool_integration|reverse_solving
next_recommended_action=<bounded next step>
generated_at=<timestamp>
```

### Phase F — artifact_index registration

Register regardless of extraction_status:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_883e67b9_bounded_static_extraction"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_883e67b9_bounded_static_extraction"]
artifact_index.artifact_refs["local_reverse_cpp2_883e67b9_bounded_static_extraction"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_bounded_static_extraction
path=project_state\\local_reverse_cpp2_883e67b9_bounded_static_extraction.json
freshness=current
source_run=round_20260607_cpp2_883e67b9_bounded_static_extraction_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
extraction_status=SUCCESS|PARTIAL|BLOCKED|FAILED
identity_verified=true|false
training_status_before=inventory_only
candidate_generated=false
candidate_validated=false
structured_evidence_ready=true|false
source_readiness_artifact=project_state\\local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
next_recommended_mainline=<value>
```

Do not modify `local_reverse_training_status.json` or `status_overlay.json`.

### Phase G — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_883e67b9_bounded_static_extraction_v1",
  "round_id": "round_20260607_cpp2_883e67b9_bounded_static_extraction_v1",
  "based_on_decision_id": "decision_20260607_cpp2_883e67b9_bounded_static_extraction_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
extraction_status=SUCCESS -> status=SUCCESS, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
extraction_status=PARTIAL -> status=PARTIAL, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
extraction_status=BLOCKED -> status=BLOCKED, acceptance_recommendation=BLOCKED
extraction_status=FAILED -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

Use `ACCEPTED_WITH_LIMITATIONS` for SUCCESS/PARTIAL because this round does not solve or validate a candidate.

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
decision_id=decision_20260607_cpp2_883e67b9_bounded_static_extraction_v1
report_id=report_20260607_cpp2_883e67b9_bounded_static_extraction_v1
round_id=round_20260607_cpp2_883e67b9_bounded_static_extraction_v1
```

Content assertions to record:

```text
1. decision_packet is the sole authority.
2. mainline=tool_integration.
3. source readiness artifact is current/READY/identity_verified.
4. cpp2_883e67b9 training_status remains inventory_only/known_candidate="".
5. sample identity reverified by size and sha256, or artifact records BLOCKED reason.
6. existing static extraction / StructuredEvidence / tool interfaces were checked before tool use.
7. no duplicate tool interface was created.
8. artifact exists at project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json.
9. artifact_index registers local_reverse_cpp2_883e67b9_bounded_static_extraction as current.
10. artifact records bounded string anchor map and xref/reference search summary.
11. candidate_generated=false.
12. candidate_validation_attempted=false.
13. training_status/status_overlay were not modified.
14. no sample executable was run.
15. no runtime tools/debugger/hook/emulator/probe were run.
16. no brute force/dictionary/search/fuzzing was run.
17. no binary was uploaded, copied, embedded, or committed.
18. no full strings/imports/sections/disassembly/decompilation dump was recorded.
19. pytest_result uses this decision_id/report_id/round_id.
20. final lint-report ran after report write.
21. git diff --name-status only contains allowed files.
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage.

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. readiness artifact is current/READY and sample identity is reverified;
2. bounded static extraction artifact is produced and registered current;
3. artifact contains bounded string anchors and xref/reference search summary;
4. artifact gives clear next bounded recommendation;
5. no candidate is generated or validated;
6. no sample execution or forbidden runtime/debugger/search action occurred;
7. training_status/status_overlay remain unchanged;
8. tests/lint/report metadata align with this decision/report/round.
```

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. identity is verified but xref/reference recovery is incomplete;
2. artifact records bounded negative results and a next step;
3. no forbidden action occurred.
```

Stop with `BLOCKED` if:

```text
1. source readiness artifact is missing/stale/not READY;
2. sample file is missing under command-scoped root;
3. size/sha256 mismatch;
4. no bounded static extraction path is available.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. any forbidden execution/tool action occurs;
2. candidate is generated or validation attempted;
3. training_status/status_overlay are modified;
4. artifact_index/report/pytest_result do not align with this decision.
```
