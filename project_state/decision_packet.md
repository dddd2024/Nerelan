```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_static_extraction_v1",
  "round_id": "round_20260607_cpp2_32f1713e_static_extraction_v1",
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

目标：在 `LOCAL_REVERSE_ROOT` 可解析本地样本路径的前提下，对 `cpp2_32f1713e` 做一次真正的 **bounded static extraction**，补齐上一轮只能 PARTIAL 的静态证据：文件/PE 元数据、导入、节区、bounded strings、比较点/输入输出字符串/变换线索，以及是否已有足够证据进入后续 `reverse_solving`。

本轮仍不是求解，不生成 candidate，不做 runtime validation。允许动作仅限静态提取和证据结构化：

```text
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
mainline=tool_integration
allowed_actions=[static_extraction, static_triage_evidence_enrichment]
forbidden_actions=[runtime_probe, debugger, hook, emulator, winpty, console_validator, bruteforce, dictionary_search, candidate_validation, upload_binary]
```

必须产出：

```text
project_state/local_reverse_cpp2_32f1713e_static_extraction.json
```

该 artifact 只记录结构化静态证据，不记录样本二进制内容，不记录完整大字符串 dump，不提交本地样本。

若 `LOCAL_REVERSE_ROOT` 未设置、样本路径不存在或样本 sha256 与 inventory 不一致，**不要重复生成无新增信息的 PARTIAL static triage**；直接停止并写 `status=BLOCKED` 的 report/pytest_result，说明需要在本地设置 `LOCAL_REVERSE_ROOT` 后重跑。

---

## 2. Current Evidence

当前 `decision_packet.md` 是本轮唯一执行权威。`project_state/task_packet.json` 的 `task` 仍是旧 `samplereverse` advisory，不控制本轮。

上一轮 static triage 与 rework 已接受但有限制：

```text
project_state/local_reverse_cpp2_32f1713e_static_triage.json:
  triage_status=PARTIAL
  local_sample_available=false
  local_sample_unavailable_reason=LOCAL_REVERSE_ROOT_NOT_SET
  executed_sample=false
  ran_runtime_tools=false
  ran_debugger=false
  ran_bruteforce=false
  uploaded_binary=false
  recommended_next_mainline=tool_integration
  recommended_next_action=set LOCAL_REVERSE_ROOT and perform static-only extraction

project_state/artifact_index.json:
  latest_artifacts["local_reverse_cpp2_32f1713e_static_triage"] exists
  latest_artifacts_v2["local_reverse_cpp2_32f1713e_static_triage"].freshness=current
  artifact_refs["local_reverse_cpp2_32f1713e_static_triage"] exists
```

Training state must remain unchanged during this round:

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

Queue state:

```text
project_state/local_reverse_evaluation_queue.json:
  rank 1 sample_id=cpp2_32f1713e
  relative_path=逆向课程2023春补考02/Cpp2.exe
  proposed_next_mainline=tool_integration
  allowed_actions=[static_triage]
  forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

Inventory metadata from the accepted triage artifact:

```text
sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
size_bytes=196686
extension=.exe
guessed_file_type=pe
category=cpp
github_upload_policy=metadata_only
```

Existing capability evidence from previous triage:

```text
existing_ida_interface=true
existing_ghidra_interface=false
existing_strings_or_file_static_path=true
existing_radare2_or_objdump_static_path=true
existing_structured_evidence_conversion=true
existing_solver_templates=true
existing_harness_or_validation_path=true but forbidden this round
strings.exe available if local path resolves
objdump.exe available if local path resolves
pefile/lief/capstone unavailable in .venv during previous triage
```

`negative_results.json` mostly concerns old samplereverse directions. It still prohibits blind search, budget expansion, breakpoint probes without new evidence, and committing solve_reports. This round must not touch those directions.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run the sample executable.
3. Do not attach debugger, hook, emulator, runtime probe, winpty, console validator, or dynamic harness.
4. Do not run bruteforce, dictionary search, solver search, or candidate validation.
5. Do not generate a final candidate or mark the sample solved.
6. Do not upload, copy into repo, base64-embed, or commit the sample binary.
7. Do not commit DLL/EXE/PDB/dump/screenshot/solve_reports/.venv/site-packages/wheel/local binary data.
8. Do not scan full solve_reports, full PROJECT_PROGRESS_LOG.txt, or the full local sample tree.
9. Do not rebuild full inventory.
10. Do not modify .codex-skills.
11. Do not create duplicate IDA/Ghidra/debugger/static extraction interfaces when mature tools or existing wrappers suffice.
12. Do not mark cpp2_32f1713e solved or blocked in training_status/status_overlay.
13. Do not alter cpp2_2f64e68d / 10013 solved facts.
14. Do not store raw binary bytes or full unbounded strings in any artifact.
15. Do not use stale artifacts for other samples as current evidence for cpp2_32f1713e.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read inventory/training/queue metadata for cpp2_32f1713e.
3. Resolve LOCAL_REVERSE_ROOT + relative_path and verify the sample file exists locally.
4. Compute local file sha256 and size; compare with inventory before extraction.
5. Use mature static-only tools such as strings.exe, objdump.exe, file, radare2 in static mode, or existing IDA batch static export route if already present and non-executing.
6. Use Python only to parse tool outputs and assemble JSON evidence; do not implement a new PE parser/disassembler if mature tools are available.
7. Generate project_state/local_reverse_cpp2_32f1713e_static_extraction.json.
8. Update artifact_index latest_artifacts/latest_artifacts_v2/artifact_refs for the new artifact.
9. Optionally add a low-token pointer in current_state/task_packet, preserving all compatibility fields and task advisory semantics.
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
project_state/local_reverse_cpp2_32f1713e_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
reverse_agent/local_reverse_training_status.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_targeted_static_reextract.py
reverse_agent/local_reverse_constraint_recovery.py
tests/test_project_state.py
```

Inspect only if directly needed and bounded:

```text
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
project_state/local_reverse_forced_ida_extraction_result.json
```

Do not default-read:

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
local_reverse_samples/ full tree
E:\reverse full tree
```

---

## 5. Required Audit

Codex report must answer:

```text
1. Did it confirm decision_packet is the sole execution authority?
2. Did it confirm mainline=tool_integration?
3. Did it confirm this is static extraction/evidence enrichment, not reverse_solving?
4. Did it confirm task_packet.task remains advisory?
5. Did it confirm cpp2_32f1713e remains rank 1 / inventory_only / known_candidate=""?
6. Did it resolve LOCAL_REVERSE_ROOT and verify the local sample exists?
7. Did it verify sha256 and size against inventory before extraction?
8. If LOCAL_REVERSE_ROOT/sample/sha check failed, did it stop as BLOCKED without generating another redundant PARTIAL triage artifact?
9. Did it run only static tools and list exact commands/tools used?
10. Did it confirm no sample execution occurred?
11. Did it confirm no debugger/hook/emulator/runtime probe/winpty/console validator occurred?
12. Did it confirm no bruteforce/dictionary/candidate validation occurred?
13. Did it confirm no binary was uploaded, copied, embedded, or committed?
14. Did it inspect existing static/IDA/tool interfaces and avoid duplicate implementation?
15. Did it generate project_state/local_reverse_cpp2_32f1713e_static_extraction.json if and only if local sample access passed?
16. Did the artifact contain bounded strings/imports/sections/compare clues/crypto-transform hints without raw binary or unbounded dumps?
17. Did it register the artifact in latest_artifacts, latest_artifacts_v2, and artifact_refs?
18. Did it preserve training_status/status_overlay sample state?
19. Did it explain negative_results unchanged or update it only for a real new failed direction?
20. Did it run required py_compile/pytest/lint/status/git checks?
21. Did pytest_result.txt use this decision_id/report_id/round_id?
22. Did final lint-report run after report write?
23. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded static extraction only. Prefer mature tools and existing wrappers.

### Phase A — preflight

Use `.venv\\Scripts\\python` for Python commands.

Verify state:

```text
project_state/local_reverse_evaluation_queue.json:
  items[0].sample_id == cpp2_32f1713e
  items[0].forbidden_actions includes runtime_probe, bruteforce, upload_binary

project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
  cpp2_32f1713e.blocked_reason == ""

project_state/local_reverse_cpp2_32f1713e_static_triage.json:
  triage_status == PARTIAL
  local_sample_available == false
  local_sample_unavailable_reason == LOCAL_REVERSE_ROOT_NOT_SET
```

Resolve sample path:

```text
sample_path = %LOCAL_REVERSE_ROOT%\逆向课程2023春补考02\Cpp2.exe
```

Required local checks:

```text
LOCAL_REVERSE_ROOT is set
sample_path exists
sample_path is a regular file
size_bytes == 196686
sha256 == 32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
```

If any local check fails, stop and write `status=BLOCKED`, with no new static_extraction artifact and no artifact_index registration for static_extraction. Do not run fallback dynamic tools. Do not generate another duplicate PARTIAL triage artifact.

### Phase B — capability and tool selection

Inspect existing project wrappers before running tools:

```text
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_targeted_static_reextract.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_training_status.py
```

Use mature tools where possible. Acceptable static-only sources include:

```text
strings.exe -a -n 4 <sample_path>
objdump.exe -x <sample_path>
objdump.exe -h <sample_path>
objdump.exe -d <sample_path>   # bounded output parsing only; do not store full disassembly
file <sample_path>             # if available
radare2 static info commands only, if available and non-executing
existing IDA static export route, only if already implemented and it does not execute the binary
```

Do not create a new IDA/Ghidra/debugger runner. A tiny local script to run existing tools, bound output, and assemble JSON is acceptable if not committed as project source; if committed source is necessary, stop and write BLOCKED unless scope is explicitly amended.

### Phase C — extraction content

Generate bounded evidence:

```text
file_metadata:
  sha256, size_bytes, guessed file type, architecture/bitness/subsystem if obtainable

sections_summary:
  section name, virtual size, raw size, entropy if available from tool output or simple bounded calculation

imports_summary:
  imported DLLs and functions, bounded and grouped

strings_summary:
  counts and bounded selected strings only
  include input/output prompts, success/failure messages, format strings, suspicious constants, crypto labels
  do not store full strings dump

compare_clues:
  static references to strcmp/strncmp/memcmp/lstrcmp/StrCmp, scanf/cin/getline/read APIs, puts/printf/cout, branch-near-compare clues if obtainable

crypto_or_transform_hints:
  xor/shift/base64/rc4/des/aes/md5/sha table constants or labels if visible

candidate_status:
  candidate_generated=false
  candidate_validation_attempted=false
```

### Phase D — artifact generation

Generate:

```text
project_state/local_reverse_cpp2_32f1713e_static_extraction.json
```

Required fields:

```text
schema_version=1
mainline=tool_integration
round_id=round_20260607_cpp2_32f1713e_static_extraction_v1
decision_id=decision_20260607_cpp2_32f1713e_static_extraction_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
source_static_triage=project_state\\local_reverse_cpp2_32f1713e_static_triage.json
training_status_before=inventory_only
known_candidate_before=""
executed_sample=false
ran_runtime_tools=false
ran_debugger=false
ran_bruteforce=false
uploaded_binary=false
local_sample_available=true
local_sample_sha256_verified=true
local_sample_size_verified=true
static_tools_used=[...]
static_tools_unavailable=[...]
existing_tool_interfaces={...}
duplicate_interface_created=false
file_metadata={...}
sections_summary=[...]
imports_summary={...}
strings_summary={...}
compare_clues=[...]
crypto_or_transform_hints=[...]
candidate_generated=false
candidate_validation_attempted=false
extraction_status=SUCCESS|PARTIAL
recommended_next_mainline=reverse_solving|tool_integration|training_dataset
recommended_next_action=<bounded next step>
generated_at=<timestamp>
```

`extraction_status=PARTIAL` is allowed only if local sample access succeeded but some optional mature tools were unavailable. It is not allowed for `LOCAL_REVERSE_ROOT_NOT_SET`; that case must be BLOCKED.

### Phase E — artifact_index and optional pointers

If the extraction artifact is generated, update:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_static_extraction"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_static_extraction"]
artifact_index.artifact_refs["local_reverse_cpp2_32f1713e_static_extraction"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_static_extraction
path=project_state\\local_reverse_cpp2_32f1713e_static_extraction.json
freshness=current
source_run=round_20260607_cpp2_32f1713e_static_extraction_v1
sha256=<actual sha256>
size_bytes=<actual size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
```

Optional low-token pointers:

```text
current_state.local_reverse_current_static_extraction=project_state\\local_reverse_cpp2_32f1713e_static_extraction.json
task_packet.local_reverse_current_static_extraction=project_state\\local_reverse_cpp2_32f1713e_static_extraction.json
```

Do not change `task_packet.task`. Do not alter training_status/status_overlay.

### Phase F — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_static_extraction_v1",
  "round_id": "round_20260607_cpp2_32f1713e_static_extraction_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_static_extraction_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

If extraction succeeds but evidence is insufficient for solving, use `status=PARTIAL` and `acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`, not NEEDS_REVIEW. If local root/sample is unavailable, use `status=BLOCKED` and `acceptance_recommendation=BLOCKED`.

---

## 7. Tests

All Python commands must use `.venv\\Scripts\\python`.

Must run and record:

```text
.venv\\Scripts\\python -m py_compile reverse_agent/project_state.py
.venv\\Scripts\\python -m pytest -q tests/test_project_state.py
.venv\\Scripts\\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\\Scripts\\python -m reverse_agent.project_state lint-report --state-dir project_state   # final after report write
.venv\\Scripts\\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

If project source code is modified, run targeted tests for the changed source. If only project_state artifacts are changed, `tests/test_project_state.py` is sufficient.

Content assertions required in report/pytest_result:

```text
1. task_packet.task remains advisory.
2. cpp2_32f1713e remains inventory_only and known_candidate="".
3. Local sample path was verified before extraction, or report is BLOCKED.
4. Local sha256/size matched inventory before extraction, or report is BLOCKED.
5. No sample executable run.
6. No debugger/hook/emulator/runtime probe/winpty/console validator run.
7. No bruteforce/dictionary/candidate validation run.
8. No binary uploaded, copied, embedded, or committed.
9. Existing static/IDA interfaces were inspected and no duplicate interface was created.
10. Static extraction artifact exists only if local sample verification passed.
11. Static extraction artifact contains bounded evidence and no raw binary/unbounded dump.
12. artifact_index registers local_reverse_cpp2_32f1713e_static_extraction as current if artifact exists.
13. training_status/status_overlay sample state unchanged.
14. pytest_result uses this decision_id/report_id/round_id.
15. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop and write `status=BLOCKED` or `status=FAILED`, not ACCEPT, if any condition occurs:

```text
1. LOCAL_REVERSE_ROOT is unset.
2. sample_path does not exist.
3. sample size or sha256 does not match inventory.
4. Any sample execution would be required.
5. Any debugger/hook/emulator/runtime probe/winpty/console validator would be required.
6. Any bruteforce/dictionary/candidate validation would be required.
7. A duplicate mature-tool interface would be needed.
8. Sample binary would need to be uploaded, copied, embedded, or committed.
9. training_status/status_overlay would need solved/blocked mutation.
10. static extraction artifact would contain raw binary or unbounded dump.
11. artifact_index cannot register the extraction artifact after successful extraction.
12. pytest_result does not include py_compile reverse_agent/project_state.py.
13. pytest_result does not match this decision/report/round.
14. lint-report after final report write fails.
15. git diff includes .venv, site-packages, DLL, EXE, sample binary, solve_reports, or .codex-skills.
```
