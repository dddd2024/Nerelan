```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_targeted_static_solving_v1",
  "round_id": "round_20260607_cpp2_32f1713e_targeted_static_solving_v1",
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

本轮主线是 **reverse_solving**，但范围限定为 `cpp2_32f1713e` 的 **targeted static solving preparation**。

目标：基于 current 静态提取证据，围绕输入提示、success/failure 字符串、`flag == 0 || flag == 1`、`%.2X `、CompareStringA/W 以及可能的 main/check 逻辑，定位比较点和目标数据来源，判断是否存在可静态证明的候选构造路径。

本轮可以产出 **static solver handoff** 或 **unvalidated static candidate hypothesis**，但必须明确未经过 runtime validation，不得写入 solved 状态，不得修改 training status。若无法静态证明候选，则必须输出 PARTIAL/BLOCKED，并说明需要下一轮 IDA/Ghidra 反编译或 runtime oracle validation。

必须产出：

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json
```

本轮禁止运行样本、禁止调试、禁止 runtime probe、禁止 winpty/console validator、禁止 brute force、禁止 dictionary search、禁止 runtime candidate validation、禁止标记 solved/blocked。若需要验证候选，必须下一轮单独生成 runtime validation 决策。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮静态提取审计结论为 **ACCEPTED_WITH_LIMITATIONS**：它提供 current 静态证据，但不是解题结果，也没有 candidate validation。

Current static extraction artifact:

```text
project_state/local_reverse_cpp2_32f1713e_bounded_static_extraction.json:
  decision_id=decision_20260607_cpp2_32f1713e_bounded_static_extraction_v1
  round_id=round_20260607_cpp2_32f1713e_bounded_static_extraction_v1
  sample_id=cpp2_32f1713e
  identity_verified=true
  static_extraction_status=SUCCESS
  file_type=PE
  architecture=i386
  bitness=32
  entry_point_rva=0x1440
  image_base=0x400000
  subsystem=Windows CUI (Console)
  sections=.text/.rdata/.data/.idata/.reloc
  import_dll_count=1
  imported_dlls=KERNEL32.dll
  notable_imports=CompareStringA, CompareStringW
  selected challenge strings:
    Plase give me your answer:
    Congratulations! You are right!
    Sorry, you are wrong!
    Sorry,you are wrong!
    flag == 0 || flag == 1
    %.2X 
  solver_profile_hypotheses:
    direct_string_compare_password_checker
    hex_encoded_comparison
  executed_sample=false
  ran_runtime_tools=false
  ran_debugger=false
  ran_bruteforce=false
  candidate_generated=false
  candidate_validation_attempted=false
  uploaded_binary=false
```

`artifact_index.latest_artifacts_v2` registers the static artifact as current:

```text
local_reverse_cpp2_32f1713e_bounded_static_extraction:
  kind=local_reverse_bounded_static_extraction
  freshness=current
  source_run=round_20260607_cpp2_32f1713e_bounded_static_extraction_v1
  sample_id=cpp2_32f1713e
  static_extraction_status=SUCCESS
  identity_verified=true
  source_readiness_artifact=project_state\\local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
```

The readiness artifact remains current and usable as local access precondition:

```text
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json:
  readiness_status=READY
  ready_for_static_extraction=true
  command_scoped_root=E:\reverse
  resolved_sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
  size_bytes=196686
  sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
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

`negative_results.json` mainly concerns old `samplereverse` directions: blind search, budget expansion, compare breakpoint probes, stale function assumptions, and full solve_reports commit. This round must not repeat those directions. For local `cpp2_32f1713e`, the relevant policy is: no runtime probe, no brute force, no upload_binary, no full dumps.

Existing capability evidence from last report:

```text
reverse_agent/local_reverse_single_sample_static_triage.py: IDA-dependent; IDA unavailable in last run
reverse_agent/tool_runners.py: IDA/ollydbg runners; IDA unavailable in last run
reverse_agent/evidence.py: StructuredEvidence class available
reverse_agent/static_feature_extractor.py and simple_static_patterns.py: general static support
pefile/lief/radare2/objdump unavailable in last run
Python stdlib PE parser + strings extractor used successfully
```

Mature tools remain preferred. If IDA/Ghidra becomes available in this Codex environment, use the existing interface only and keep output bounded. If unavailable, do not create a duplicate decompiler/disassembler; either do bounded static reasoning from existing artifact or perform a minimal focused byte/XREF-like scan only around current string/import indicators.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run the sample executable.
3. Do not attach debugger, hook, emulator, runtime probe, winpty, console validator, or dynamic harness.
4. Do not run brute force, dictionary search, candidate search over broad domains, candidate ranking by runtime, or runtime candidate validation.
5. Do not mark cpp2_32f1713e solved or blocked.
6. Do not modify project_state/local_reverse_training_status.json or training_materials/local_reverse/status_overlay.json.
7. Do not alter cpp2_2f64e68d / 10013 solved facts.
8. Do not upload, copy into repo, base64-embed, or commit the sample binary.
9. Do not store raw binary bytes, full strings dump, full disassembly, full decompilation, full import table, full section dump, screenshots, memory dumps, or local binary data in any artifact.
10. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
11. Do not rebuild full inventory.
12. Do not modify .codex-skills.
13. Do not create duplicate IDA/Ghidra/debugger/static extraction interfaces.
14. Do not use stale artifact evidence as current static evidence.
15. Do not claim a candidate is valid without a future runtime validation decision.
16. Do not start runtime oracle validation in this round even if a plausible candidate is recovered.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current readiness and bounded static extraction artifacts for cpp2_32f1713e.
3. Read inventory/training/queue metadata only for cpp2_32f1713e and direct consistency checks.
4. Use command-scoped LOCAL_REVERSE_ROOT=E:\reverse to access only E:\reverse\逆向课程2023春补考02\Cpp2.exe for bounded static analysis.
5. Reverify sample identity by size and sha256 before any new local static scan.
6. Inspect existing IDA/Ghidra/static extraction interfaces before choosing tooling.
7. If existing IDA/Ghidra static export runner is available, run it only in static mode and cap output.
8. If mature tools remain unavailable, use only bounded stdlib byte/string/reference scans around known indicators from the current artifact.
9. Locate string offsets/RVAs for prompt/success/failure/flag/%.2X indicators.
10. Search bounded code/data references to those string RVAs when possible without full disassembly dump.
11. Identify likely compare/check region, target constant, transform clue, and whether direct-string or hex-encoded comparison is better supported.
12. Generate a static solver handoff or unvalidated static candidate hypothesis only if the evidence path is explicit and bounded.
13. Register artifact in artifact_index.
14. Write codex_execution_report.md and pytest_result.txt.
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
project_state/local_reverse_cpp2_32f1713e_bounded_static_extraction.json
project_state/local_reverse_cpp2_32f1713e_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Must inspect bounded existing capability surface before local static solving:

```text
Search repository for: ida, ghidra, static_triage, static_extraction, StructuredEvidence, xref, compare, string reference, pefile, lief, r2, radare2, objdump, artifact_index.
Inspect only directly relevant existing modules/scripts/tests found by that search.
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
2. Did it confirm mainline=reverse_solving?
3. Did it confirm this is targeted static solving, not runtime validation?
4. Did it confirm task_packet.task remains advisory?
5. Did it confirm current bounded static extraction artifact is current/SUCCESS/identity_verified?
6. Did it confirm current readiness is READY and command-scoped local root is available?
7. Did it confirm cpp2_32f1713e remains inventory_only / known_candidate=""?
8. Did it reverify path/size/sha256 before any local static scan?
9. Did it inspect existing IDA/Ghidra/static extraction/StructuredEvidence interfaces before choosing tools?
10. Which tools/interfaces were used or unavailable?
11. Did it avoid creating duplicate mature-tool interfaces?
12. Did it locate string offsets/RVAs for prompt/success/failure/flag/%.2X indicators?
13. Did it attempt bounded reference or compare-region recovery without full disassembly dump?
14. Did it determine whether evidence supports direct_string_compare or hex_encoded_comparison, or remain inconclusive?
15. Did it generate local_reverse_cpp2_32f1713e_targeted_static_solving.json?
16. Did it register the artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
17. Did it avoid sample execution?
18. Did it avoid debugger/hook/emulator/runtime probe/winpty/console validator?
19. Did it avoid brute force/dictionary/runtime candidate validation?
20. If a candidate hypothesis was generated, did it mark it unvalidated and keep training state unchanged?
21. Did it confirm no solved/blocked status was written?
22. Did it confirm no binary or full dumps were committed?
23. Did it preserve cpp2_2f64e68d solved facts?
24. Did it explain negative_results unchanged or non-use?
25. Did it run required py_compile/pytest/lint/status/git checks?
26. Did pytest_result.txt use this decision_id/report_id/round_id?
27. Did final lint-report run after report write?
28. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded targeted static solving only.

### Phase A — state and artifact preflight

Use `.venv\\Scripts\\python` for repository Python commands.

Verify:

```text
project_state/local_reverse_cpp2_32f1713e_bounded_static_extraction.json:
  static_extraction_status == SUCCESS
  identity_verified == true
  sample_id == cpp2_32f1713e
  candidate_generated == false
  candidate_validation_attempted == false

project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json:
  readiness_status == READY
  ready_for_static_extraction == true
  sample_id == cpp2_32f1713e

project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
  cpp2_32f1713e.blocked_reason == ""
```

Reverify identity under command-scoped root:

```bat
cmd /c "set LOCAL_REVERSE_ROOT=E:\reverse&& .venv\Scripts\python -c \"import os, pathlib, hashlib; p=pathlib.Path(os.environ['LOCAL_REVERSE_ROOT'])/'逆向课程2023春补考02'/'Cpp2.exe'; b=p.read_bytes(); print(p); print(len(b)); print(hashlib.sha256(b).hexdigest())\""
```

This identity check is allowed. Do not print or store raw bytes.

### Phase B — existing capability inspection

Perform bounded repository search/inspection for existing tool interfaces before any additional static scan:

```text
ida / IDA / idapython
ghidra
static_triage / static_extraction
StructuredEvidence
xref / string reference / compare
pefile / lief
strings / objdump / radare2 / r2
artifact_index registration helpers
```

Decision rule:

```text
1. Prefer existing IDA/Ghidra static export interface if available and bounded.
2. If IDA/Ghidra unavailable, do not create a duplicate disassembler/decompiler.
3. Use bounded byte-level/string-RVA/reference heuristics only as a narrow fallback.
4. Any generated candidate must be labeled unvalidated_static_candidate_hypothesis and must not modify training state.
```

### Phase C — targeted static solving analysis

Allowed analysis categories:

```text
indicator anchoring:
  locate file offsets and RVAs for:
    Plase give me your answer:
    Congratulations! You are right!
    Sorry, you are wrong!
    Sorry,you are wrong!
    flag == 0 || flag == 1
    %.2X 
  record section membership and encoding type (ASCII/UTF-16 if relevant)

bounded reference search:
  search for little-endian VA/RVA references to selected string RVAs in .text/.rdata only
  cap references to 100 total
  do not dump full section bytes

compare/check recovery:
  identify likely region(s) referencing input prompt and success/failure strings
  identify whether CompareStringA/W imports are referenced near those regions if possible
  identify whether `%.2X` is referenced near comparison/output construction
  identify any nearby static constants or string literals that look like target values
  cap snippets to small metadata and at most 40 lines total if disassembly/decompiler output is available

solver classification:
  classify as one of:
    direct_string_compare_password_checker
    hex_encoded_comparison
    transformed_input_compare
    inconclusive_static_only
  include evidence and confidence

candidate handling:
  if and only if a direct static target literal or complete inverse transform is proven, write unvalidated_candidate_hypothesis with proof chain
  otherwise keep candidate_hypothesis=null and explain missing evidence
```

### Phase D — targeted static solving artifact

Generate:

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json
```

Required top-level fields:

```text
schema_version=1
mainline=reverse_solving
round_id=round_20260607_cpp2_32f1713e_targeted_static_solving_v1
decision_id=decision_20260607_cpp2_32f1713e_targeted_static_solving_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
command_scoped_root=E:\reverse
sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
size_bytes=196686
sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
identity_verified=true|false
source_static_artifact=project_state\\local_reverse_cpp2_32f1713e_bounded_static_extraction.json
source_static_status=SUCCESS
source_readiness_artifact=project_state\\local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
source_readiness_status=READY
tools_attempted=[]
tools_used=[]
existing_interfaces_inspected=[]
new_interface_created=false
static_solving_status=SUCCESS|PARTIAL|BLOCKED|FAILED
indicator_anchors=[]
reference_summary={}
compare_region_candidates=[]
solver_classification={}
unvalidated_candidate_hypothesis=null|{}
candidate_generated=true|false
candidate_validation_attempted=false
candidate_validated=false
candidate_acceptance_status=unvalidated|null
executed_sample=false
ran_runtime_tools=false
ran_debugger=false
ran_bruteforce=false
ran_dictionary_search=false
uploaded_binary=false
binary_content_recorded=false
full_strings_dump_recorded=false
full_disassembly_recorded=false
full_decompilation_recorded=false
full_import_table_recorded=false
full_section_dump_recorded=false
training_status_modified=false
next_recommended_mainline=reverse_solving|tool_integration
next_recommended_action=<bounded next step>
generated_at=<timestamp>
```

Status rules:

```text
SUCCESS if a bounded, evidence-backed static proof chain identifies a comparison target or complete solver handoff.
PARTIAL if anchors/reference regions are found but candidate/proof chain remains incomplete.
BLOCKED if required current artifacts are missing/stale or local sample identity cannot be reverified.
FAILED only for unexpected script/tool/report errors or forbidden actions.
```

### Phase E — artifact_index and optional pointers

Register the artifact regardless of SUCCESS/PARTIAL/BLOCKED/FAILED:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_targeted_static_solving"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_targeted_static_solving"]
artifact_index.artifact_refs["local_reverse_cpp2_32f1713e_targeted_static_solving"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_targeted_static_solving
path=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solving.json
freshness=current
source_run=round_20260607_cpp2_32f1713e_targeted_static_solving_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
static_solving_status=SUCCESS|PARTIAL|BLOCKED|FAILED
identity_verified=true|false
candidate_generated=true|false
candidate_validated=false
source_static_artifact=project_state\\local_reverse_cpp2_32f1713e_bounded_static_extraction.json
```

Optional low-token pointers:

```text
current_state.local_reverse_current_static_solving=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solving.json
task_packet.local_reverse_current_static_solving=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solving.json
```

Do not change `task_packet.task`. Do not alter training_status/status_overlay.

### Phase F — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_targeted_static_solving_v1",
  "round_id": "round_20260607_cpp2_32f1713e_targeted_static_solving_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_targeted_static_solving_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
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
static_solving_status=FAILED  -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

Even on SUCCESS, use ACCEPTED_WITH_LIMITATIONS unless a later runtime validation decision confirms the candidate.

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
decision_id=decision_20260607_cpp2_32f1713e_targeted_static_solving_v1
report_id=report_20260607_cpp2_32f1713e_targeted_static_solving_v1
round_id=round_20260607_cpp2_32f1713e_targeted_static_solving_v1
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage. Acceptance recommendation must remain at most `ACCEPTED_WITH_LIMITATIONS`.

Content assertions to record:

```text
1. source static extraction artifact is current/SUCCESS/identity_verified.
2. source readiness artifact is current/READY.
3. sample identity reverified by size and sha256.
4. targeted static solving artifact exists.
5. static_solving_status follows SUCCESS/PARTIAL/BLOCKED/FAILED rules.
6. artifact_index registers local_reverse_cpp2_32f1713e_targeted_static_solving as current.
7. no sample executable was run.
8. no debugger/hook/emulator/runtime probe/winpty/console validator was run.
9. no brute force/dictionary/runtime candidate validation was run.
10. no candidate was marked validated.
11. no solved/blocked training status was written.
12. no binary was uploaded, copied, embedded, or committed.
13. artifact contains no raw binary, full strings dump, full imports, full sections, full disassembly, full decompilation, screenshots, or dumps.
14. existing mature-tool interfaces were inspected before choosing analysis path.
15. no duplicate IDA/Ghidra/debugger/static extraction interface was created.
16. training_status/status_overlay sample state unchanged.
17. cpp2_2f64e68d solved facts unchanged.
18. pytest_result uses this decision_id/report_id/round_id.
19. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED_WITH_LIMITATIONS` only if:

```text
1. source static artifact is current/SUCCESS/identity_verified;
2. sample identity is reverified;
3. bounded static solving artifact is produced;
4. artifact records an evidence-backed solver classification or proof chain;
5. any candidate hypothesis is explicitly unvalidated;
6. artifact_index registers the artifact as current;
7. no forbidden dynamic/runtime/bruteforce action occurred;
8. tests/lint/report metadata are aligned with this decision/report/round.
```

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. source artifacts and identity are valid;
2. anchors/reference summaries are recovered but static proof chain remains incomplete;
3. all bounds and prohibitions are respected;
4. artifact clearly states missing evidence and next bounded step.
```

Stop with `BLOCKED / BLOCKED` if:

```text
1. source static extraction artifact is missing/stale/not SUCCESS;
2. source readiness is missing/stale/not READY;
3. command-scoped root can no longer access the target;
4. size or sha256 mismatch;
5. no bounded static solving evidence can be extracted without violating constraints.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. report metadata does not match this decision;
2. pytest_result is missing or stale;
3. sample executable is run;
4. debugger/hook/emulator/runtime probe/winpty/console validator is run;
5. brute force/dictionary/runtime candidate validation occurs;
6. candidate is claimed valid without runtime validation;
7. solved/blocked training status is written;
8. binary content, full strings dump, full imports, full sections, full disassembly, full decompilation, screenshots, dumps, or local binary data are committed;
9. artifact_index registration is missing or stale;
10. .codex-skills are modified;
11. a duplicate mature-tool interface is created without necessity and tests.
```
