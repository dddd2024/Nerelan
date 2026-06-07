```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_bounded_static_extraction_v1",
  "round_id": "round_20260607_cpp2_32f1713e_bounded_static_extraction_v1",
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

目标：基于上一轮 current/READY 的 command-scoped readiness，对 `cpp2_32f1713e` 执行一次 **bounded static extraction**，为后续 `reverse_solving` 提供 current 静态证据。必须使用上一轮验证过的 command-scoped local root 注入方式访问目标样本：

```text
LOCAL_REVERSE_ROOT=E:\reverse
sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
```

本轮只允许静态证据提取和结构化登记，不允许运行样本，不允许调试，不允许 runtime probe，不允许 brute force，不允许 solver search，不允许生成或验证 candidate，不允许标记 solved/blocked。

必须产出新的静态提取 artifact：

```text
project_state/local_reverse_cpp2_32f1713e_bounded_static_extraction.json
```

该 artifact 必须是 metadata/StructuredEvidence 风格的低风险摘要：记录 PE 身份、工具可用性、入口点、节区概要、导入概要、有限字符串线索、显著常量/比较线索、成熟工具接口使用情况、下一步建议。不得记录原始二进制、完整 strings dump、完整反汇编、完整导入表、完整节区 dump、截图、内存 dump 或本地绝对路径之外的批量文件内容。

如果静态提取发现明显比较点/字符串/常量，只能形成 **static handoff recommendation**，不得直接进入求解或 candidate validation。下一轮若要解题，必须单独生成 `reverse_solving` 决策，并以本轮 current artifact 为证据来源。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮执行。

上一轮 readiness 审计结论为 **ACCEPTED_WITH_LIMITATIONS**：它只证明 command-scoped local root 下目标样本身份可确认，不构成静态分析或解题证据。

Current readiness artifact：

```text
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json:
  decision_id=decision_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
  round_id=round_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
  sample_id=cpp2_32f1713e
  expected_root=E:\reverse
  inherited_env_visible=false
  command_scoped_root=E:\reverse
  command_scoped_env_visible=true
  command_scoped_env_matches_expected=true
  resolved_sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
  path_exists=true
  is_regular_file=true
  size_bytes=196686
  sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
  ready_for_static_extraction=true
  readiness_status=READY
  executed_sample=false
  ran_static_extraction_tools=false
  ran_runtime_tools=false
  ran_debugger=false
  ran_bruteforce=false
  uploaded_binary=false
```

`artifact_index.latest_artifacts_v2` registers the readiness artifact as current:

```text
local_reverse_cpp2_32f1713e_command_scoped_env_readiness:
  kind=local_reverse_command_scoped_env_readiness
  freshness=current
  source_run=round_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
  sample_id=cpp2_32f1713e
  readiness_status=READY
  ready_for_static_extraction=true
```

Training queue remains:

```text
project_state/local_reverse_evaluation_queue.json:
  items[0].sample_id=cpp2_32f1713e
  items[0].relative_path=逆向课程2023春补考02/Cpp2.exe
  items[0].proposed_next_mainline=tool_integration
  items[0].allowed_actions=[static_triage]
  items[0].forbidden_actions includes runtime_probe, bruteforce, upload_binary
```

Training state must remain unchanged:

```text
project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status=inventory_only
  cpp2_32f1713e.known_candidate=""
  cpp2_32f1713e.blocked_reason=""
  cpp2_32f1713e.classification=""

training_materials/local_reverse/status_overlay.json:
  cpp2_32f1713e.training_status=inventory_only
  cpp2_32f1713e.known_candidate=""
  cpp2_32f1713e.blocked_reason=""
```

Inventory identity for the one target sample:

```text
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
expected_root=E:\reverse
expected_sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
size_bytes=196686
extension=.exe
guessed_file_type=pe
category=cpp
github_upload_policy=metadata_only
```

`negative_results.json` mostly concerns old `samplereverse` blind search, budget expansion, compare breakpoint probes, and stale producer assumptions. This round must not touch any reverse-solving direction, old sample_solver blind search, budget expansion, breakpoint probing, or `solve_reports` bulk commit.

Existing capability rule: before invoking or adding any extractor, Codex must inspect existing project interfaces for IDA/Ghidra/debugger/static extraction/StructuredEvidence/artifact registration. Mature tools are preferred; project code must not duplicate IDA/Ghidra/debugger functionality. If an existing static extraction or IDA/Ghidra runner is available and already integrated, prefer that interface. If unavailable or unsuitable, use a minimal bounded metadata script only for this artifact, without adding a new long-term duplicate interface.

Artifact freshness rule: current readiness is usable as precondition. Old `local_reverse_cpp2_32f1713e_static_triage.json` can be used only as historical context and must not be treated as current static extraction. Stale/missing `samplereverse` artifacts are irrelevant to this local sample.

Allowed tools in this round are static only: existing project static extractor interfaces, IDA/Ghidra static export runner if already present and bounded, and common static utilities or libraries such as `file`, `pefile`, `lief`, `strings`, `objdump`, `radare2` if available. All tool use must be metadata-only and bounded to the one target sample.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run the sample executable.
3. Do not attach debugger, hook, emulator, runtime probe, winpty, console validator, or dynamic harness.
4. Do not run brute force, dictionary search, solver search, candidate generation, candidate ranking, or candidate validation.
5. Do not generate a candidate or mark cpp2_32f1713e solved/blocked.
6. Do not modify project_state/local_reverse_training_status.json or training_materials/local_reverse/status_overlay.json.
7. Do not alter cpp2_2f64e68d / 10013 solved facts.
8. Do not upload, copy into repo, base64-embed, or commit the sample binary.
9. Do not store raw binary bytes, full strings dump, full disassembly, full import table, full section dump, screenshots, memory dumps, or local binary data in any artifact.
10. Do not commit DLL/EXE/PDB/dump/screenshot/solve_reports/.venv/site-packages/wheel/local binary data.
11. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
12. Do not rebuild full inventory.
13. Do not modify .codex-skills.
14. Do not create duplicate IDA/Ghidra/debugger/static extraction interfaces when existing interfaces are available.
15. Do not use stale artifact evidence as current static evidence.
16. Do not proceed into reverse_solving in this round even if a likely password/string is found.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read inventory/training/queue metadata only for cpp2_32f1713e and direct consistency checks.
3. Read or inspect existing project static tool interfaces using bounded file search/grep.
4. Use command-scoped LOCAL_REVERSE_ROOT=E:\reverse to access only E:\reverse\逆向课程2023春补考02\Cpp2.exe.
5. Verify sample identity again by size and sha256.
6. Run bounded static-only extraction tools on that one file, preferring existing project interfaces and mature tools.
7. Extract PE metadata: format, architecture if available, entry point, image base, subsystem, timestamp if available, section names/sizes/characteristics summary, import DLL/function summary counts, bounded suspicious/string indicators.
8. Extract bounded strings evidence: at most 80 selected strings, each capped to 160 characters, filtered for likely challenge semantics such as success/failure prompts, input prompts, format strings, compare-related strings, crypto/API names, and obvious constants. Do not store all strings.
9. Extract bounded code/static cues only if available without full disassembly: function labels/counts, XREF/count summaries, compare/API references, immediate constants, or IDA/Ghidra decompiler snippets capped to small excerpts.
10. Generate project_state/local_reverse_cpp2_32f1713e_bounded_static_extraction.json.
11. Register the artifact in artifact_index.latest_artifacts, artifact_index.latest_artifacts_v2, and artifact_index.artifact_refs.
12. Optionally add low-token pointers in current_state/task_packet while preserving task advisory semantics.
13. Write codex_execution_report.md and pytest_result.txt.
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
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
project_state/local_reverse_cpp2_32f1713e_local_env_readiness.json
project_state/local_reverse_cpp2_32f1713e_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Must inspect bounded existing capability surface before implementing/executing extraction:

```text
Search repository for: ida, ghidra, static_triage, static_extraction, StructuredEvidence, pefile, lief, r2, radare2, objdump, strings, artifact_index.
Inspect only the directly relevant existing modules/scripts/tests found by that search.
Prefer existing interfaces; do not create duplicates.
```

Do not read by default:

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse full tree beyond E:\reverse\逆向课程2023春补考02\Cpp2.exe
```

---

## 5. Required Audit

Codex report must answer:

```text
1. Did it confirm decision_packet is the sole execution authority?
2. Did it confirm mainline=tool_integration?
3. Did it confirm this is bounded static extraction, not reverse_solving?
4. Did it confirm task_packet.task remains advisory?
5. Did it confirm current command-scoped readiness is READY and source_run matches the previous round?
6. Did it confirm cpp2_32f1713e remains rank 1 / inventory_only / known_candidate=""?
7. Did it use command-scoped LOCAL_REVERSE_ROOT=E:\reverse for sample access?
8. Did it verify path/size/sha256 before extraction?
9. Did it inspect existing IDA/Ghidra/debugger/static extraction/StructuredEvidence interfaces before choosing tools?
10. Which mature/static tools or existing interfaces did it use, and which were unavailable?
11. Did it avoid creating duplicate mature-tool interfaces?
12. Did it generate local_reverse_cpp2_32f1713e_bounded_static_extraction.json?
13. Did the artifact include PE identity, entry point, section summary, import summary, bounded strings/static indicators, tool provenance, and next recommended handoff?
14. Did it cap strings/static snippets and avoid full dumps?
15. Did it register the artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
16. Did it avoid sample execution?
17. Did it avoid debugger/hook/emulator/runtime probe/winpty/console validator?
18. Did it avoid brute force/dictionary/solver/candidate validation?
19. Did it avoid candidate generation and solved/blocked status changes?
20. Did it confirm no binary was uploaded/copied/embedded/committed?
21. Did it preserve training_status/status_overlay and cpp2_2f64e68d solved facts?
22. Did it explain negative_results unchanged or any non-use?
23. Did it run required py_compile/pytest/lint/status/git checks?
24. Did pytest_result.txt use this decision_id/report_id/round_id?
25. Did final lint-report run after report write?
26. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded static extraction only.

### Phase A — state and readiness preflight

Use `.venv\\Scripts\\python` for repository Python commands.

Verify:

```text
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json:
  readiness_status == READY
  ready_for_static_extraction == true
  sample_id == cpp2_32f1713e
  size_bytes == 196686
  sha256 == 32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412

project_state/local_reverse_evaluation_queue.json:
  items[0].sample_id == cpp2_32f1713e
  items[0].forbidden_actions includes runtime_probe, bruteforce, upload_binary

project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
  cpp2_32f1713e.blocked_reason == ""
```

Re-verify identity under command-scoped root:

```bat
cmd /c "set LOCAL_REVERSE_ROOT=E:\reverse&& .venv\Scripts\python -c \"import os, pathlib, hashlib; p=pathlib.Path(os.environ['LOCAL_REVERSE_ROOT'])/'逆向课程2023春补考02'/'Cpp2.exe'; b=p.read_bytes(); print(p); print(len(b)); print(hashlib.sha256(b).hexdigest())\""
```

This identity check is allowed. Do not print or store raw bytes.

### Phase B — existing capability inspection

Perform bounded repository search/inspection for existing tool interfaces before any extraction:

```text
ida / IDA / idapython
ghidra
static_triage / static_extraction
StructuredEvidence
pefile / lief
strings / objdump / radare2 / r2
artifact_index registration helpers
```

Decision rule:

```text
1. If an existing project static extraction interface supports this bounded sample and command-scoped root, use it.
2. If an existing IDA/Ghidra static export runner exists and can be run without dynamic execution, prefer it for richer static evidence, but keep output bounded.
3. If mature static tools are unavailable, record unavailability and fall back to minimal Python stdlib PE header/string extraction only for this artifact.
4. Do not add new long-term tool interfaces in this round unless there is no existing interface and the change is minimal, local, and testable. Prefer artifact-only scripting over permanent architecture changes.
```

### Phase C — bounded static extraction

Allowed extraction categories:

```text
identity:
  sample_id, relative_path, size, sha256, path, command_scoped_root

file/PE metadata:
  file_type, architecture/machine if available, bitness if available, subsystem if available, image_base if available, entry_point/RVA if available, timestamp if available

sections summary:
  section_count, section names, virtual_size/raw_size, entropy if already available cheaply, characteristics summary
  cap to all section headers only; do not dump section bytes

imports summary:
  imported DLL names and selected imported function names/counts
  cap imported function list to 200 entries; do not store full raw tables if larger

strings indicators:
  selected ASCII/UTF-16 strings only, max 80 strings, max 160 chars each
  prefer strings containing prompt/success/failure/check/password/input/flag/error/format/crypto/API/compare semantics
  include selection criteria and total_strings_seen if known

static code/cue summary:
  if tool output supports it, record bounded function count, likely main/check functions, compare/API references, XREF count summaries, suspicious constants, and short snippets capped to 40 lines total
  do not store full disassembly or full decompilation

tool provenance:
  tools attempted, tools used, command category, versions if cheap, unavailable reasons

handoff recommendation:
  next_recommended_mainline=reverse_solving or tool_integration depending evidence sufficiency
  next_recommended_action must be bounded and must not include direct candidate unless evidence explicitly supports a future solver decision
```

### Phase D — static extraction artifact

Generate:

```text
project_state/local_reverse_cpp2_32f1713e_bounded_static_extraction.json
```

Required top-level fields:

```text
schema_version=1
mainline=tool_integration
round_id=round_20260607_cpp2_32f1713e_bounded_static_extraction_v1
decision_id=decision_20260607_cpp2_32f1713e_bounded_static_extraction_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
command_scoped_root=E:\reverse
sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
size_bytes=196686
sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
identity_verified=true|false
source_readiness_artifact=project_state\\local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
source_readiness_status=READY
tools_attempted=[]
tools_used=[]
existing_interfaces_inspected=[]
new_interface_created=false
static_extraction_status=SUCCESS|PARTIAL|BLOCKED|FAILED
file_metadata={}
sections_summary=[]
imports_summary={}
strings_summary={}
static_indicators=[]
structured_evidence={}
extraction_bounds={}
executed_sample=false
ran_runtime_tools=false
ran_debugger=false
ran_bruteforce=false
candidate_generated=false
candidate_validation_attempted=false
uploaded_binary=false
binary_content_recorded=false
full_strings_dump_recorded=false
full_disassembly_recorded=false
full_import_table_recorded=false
full_section_dump_recorded=false
training_status_modified=false
next_recommended_mainline=tool_integration|reverse_solving
next_recommended_action=<bounded next step>
generated_at=<timestamp>
```

Status rules:

```text
SUCCESS if identity verified and at least one mature/existing/static extraction path produced useful bounded evidence.
PARTIAL if identity verified but only minimal metadata/strings could be extracted due tool availability.
BLOCKED if sample identity cannot be reverified or no static access is possible.
FAILED only for unexpected script/tool/report errors or forbidden actions.
```

### Phase E — artifact_index and optional pointers

Register the artifact regardless of SUCCESS/PARTIAL/BLOCKED/FAILED:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_bounded_static_extraction"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_bounded_static_extraction"]
artifact_index.artifact_refs["local_reverse_cpp2_32f1713e_bounded_static_extraction"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_bounded_static_extraction
path=project_state\\local_reverse_cpp2_32f1713e_bounded_static_extraction.json
freshness=current
source_run=round_20260607_cpp2_32f1713e_bounded_static_extraction_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
static_extraction_status=SUCCESS|PARTIAL|BLOCKED|FAILED
identity_verified=true|false
source_readiness_artifact=project_state\\local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
```

Optional low-token pointers:

```text
current_state.local_reverse_current_static_extraction=project_state\\local_reverse_cpp2_32f1713e_bounded_static_extraction.json
task_packet.local_reverse_current_static_extraction=project_state\\local_reverse_cpp2_32f1713e_bounded_static_extraction.json
```

Do not change `task_packet.task`. Do not alter training_status/status_overlay.

### Phase F — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_bounded_static_extraction_v1",
  "round_id": "round_20260607_cpp2_32f1713e_bounded_static_extraction_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_bounded_static_extraction_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
static_extraction_status=SUCCESS -> status=SUCCESS, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
static_extraction_status=PARTIAL -> status=PARTIAL, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
static_extraction_status=BLOCKED -> status=BLOCKED, acceptance_recommendation=BLOCKED
static_extraction_status=FAILED  -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

Even on SUCCESS, use ACCEPTED_WITH_LIMITATIONS because this round provides static evidence only and no candidate validation.

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
decision_id=decision_20260607_cpp2_32f1713e_bounded_static_extraction_v1
report_id=report_20260607_cpp2_32f1713e_bounded_static_extraction_v1
round_id=round_20260607_cpp2_32f1713e_bounded_static_extraction_v1
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage. In that case acceptance recommendation must remain at most `ACCEPTED_WITH_LIMITATIONS` even if static extraction succeeded.

Content assertions to record:

```text
1. source command-scoped readiness artifact is current and READY.
2. sample identity reverified by size and sha256.
3. bounded static extraction artifact exists.
4. static_extraction_status follows SUCCESS/PARTIAL/BLOCKED/FAILED rules.
5. artifact_index registers local_reverse_cpp2_32f1713e_bounded_static_extraction as current.
6. no sample executable was run.
7. no debugger/hook/emulator/runtime probe/winpty/console validator was run.
8. no brute force/dictionary/solver/candidate validation was run.
9. no candidate was generated.
10. no binary was uploaded, copied, embedded, or committed.
11. artifact contains no raw binary, full strings dump, full imports, full sections, full disassembly, screenshots, or dumps.
12. existing mature-tool interfaces were inspected before choosing extraction path.
13. no duplicate IDA/Ghidra/debugger/static extraction interface was created unless explicitly justified as minimal and local.
14. training_status/status_overlay sample state unchanged.
15. cpp2_2f64e68d solved facts unchanged.
16. pytest_result uses this decision_id/report_id/round_id.
17. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED_WITH_LIMITATIONS` only if:

```text
1. source readiness is current and READY;
2. sample identity is reverified by size and sha256;
3. bounded static evidence is produced and stored in project_state/local_reverse_cpp2_32f1713e_bounded_static_extraction.json;
4. artifact stores only bounded metadata/indicators, not full dumps or binary content;
5. artifact_index registers the artifact as current;
6. no forbidden dynamic/reverse-solving action occurred;
7. tests/lint/report metadata are aligned with this decision/report/round.
```

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. source readiness and identity are valid;
2. only minimal metadata or limited strings can be extracted because mature tools are unavailable;
3. all bounds and prohibitions are respected;
4. artifact clearly records unavailable tools and limitations.
```

Stop with `BLOCKED / BLOCKED` if:

```text
1. source readiness is missing/stale/not READY;
2. command-scoped root can no longer access the target;
3. size or sha256 mismatch;
4. no static metadata can be extracted without violating constraints.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. report metadata does not match this decision;
2. pytest_result is missing or stale;
3. sample executable is run;
4. debugger/hook/emulator/runtime probe/winpty/console validator is run;
5. brute force/solver/candidate generation/candidate validation occurs;
6. binary content, full strings dump, full imports, full sections, full disassembly, screenshots, dumps, or local binary data are committed;
7. training status, status overlay, or solved facts are changed;
8. artifact_index registration is missing or stale;
9. .codex-skills are modified;
10. a duplicate mature-tool interface is created without necessity and tests.
```
