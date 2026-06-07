```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1",
  "round_id": "round_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1",
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

本轮主线是 **tool_integration**，任务是对下一个本地训练样本 `cpp2_883e67b9` 做 **command-scoped environment readiness + bounded static triage readiness**。

目标不是解题，不是生成 candidate，也不是 runtime validation；目标是确认样本身份、确认可用的成熟静态工具/已有项目接口、产出低 token 静态 triage/readiness artifact，并为下一轮 bounded static extraction 或 IDA/Ghidra evidence extraction 决策提供依据。

必须产出：

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
```

本轮允许读取本地样本文件用于 identity/hash/file-type/read-only static triage；禁止运行样本、调试、hook、emulator、runtime probe、bruteforce 或 candidate search。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮执行。

上一轮 queue refresh rework 审计结论为 `ACCEPTED_WITH_LIMITATIONS`：

```text
project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json:
  decision_id=decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1
  round_id=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1
  recent_solved.sample_id=cpp2_32f1713e
  recent_solved.known_candidate=KEEP_DREAM
  recent_solved.accepted_round=round_20260607_cpp2_32f1713e_training_status_sync_v1
  next_queue_hint.sample_id=cpp2_883e67b9
  next_queue_hint.relative_path=逆向课程2024春02/CPP2.exe
  next_queue_hint.training_status=inventory_only
  next_queue_hint.known_candidate=""
  next_queue_hint.allowed_actions=[static_triage, bounded_static_extraction_readiness]
  next_queue_hint.forbidden_actions=[runtime_probe, brute_force, debugger, hook, emulator, upload_binary]
```

Known current training state:

```text
project_state/local_reverse_training_status.json:
  sample_count=29
  status_summary.solved=4
  status_summary.blocked=4
  status_summary.needs_triage=0
  status_summary.inventory_only=21
  cpp2_32f1713e.training_status=solved
  cpp2_32f1713e.known_candidate=KEEP_DREAM
  cpp2_883e67b9.training_status=inventory_only
  cpp2_883e67b9.known_candidate=""
  cpp2_883e67b9.blocked_reason=""
  cpp2_883e67b9.relative_path=逆向课程2024春02/CPP2.exe
  cpp2_883e67b9.sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
  cpp2_883e67b9.size_bytes=196689
```

The next sample should be resolved under command-scoped root:

```text
LOCAL_REVERSE_ROOT=E:\reverse
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
sample_id=cpp2_883e67b9
expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
expected_size_bytes=196689
```

Current project rules for tool integration:

```text
1. Mature tools first: IDA, Ghidra, strings, file, objdump, radare2, existing solver/harness/StructuredEvidence interfaces.
2. Do not create duplicate IDA/Ghidra/debugger/static extraction interfaces if existing interfaces are available.
3. Tool outputs must be summarized into bounded project_state artifacts and artifact_index entries.
4. No stale artifact may be treated as current evidence.
5. Static analysis and runtime probe are not equivalent; this round forbids runtime probes.
```

Known limitation from previous audit: `artifact_index.latest_artifacts_v2[local_reverse_queue_refresh_after_cpp2_32f1713e]` is current but has incomplete optional metadata. This round may use it as a pointer only; do not spend this round on artifact_index hygiene unless required to register the new artifact.

negative_results mainly concerns old `samplereverse` directions. This round must not repeat blind search, budget expansion, stale artifact assumptions, or full solve_reports commits.

Skill profile must remain `reverse-agent-iteration@v2`, which is active in `.codex-skills/registry.json`.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run the sample executable.
3. Do not execute any candidate or control input.
4. Do not attach debugger, hook, emulator, instrumentation probe, breakpoint probe, dynamic trace collector, winpty, console validator, or runtime harness.
5. Do not do runtime validation.
6. Do not generate a candidate.
7. Do not brute force, dictionary search, fuzz, enumerate inputs, or rank candidates.
8. Do not solve cpp2_883e67b9 in this round.
9. Do not modify project_state/local_reverse_training_status.json.
10. Do not modify training_materials/local_reverse/status_overlay.json.
11. Do not mark cpp2_883e67b9 solved, blocked, or validated.
12. Do not alter accepted solved facts for cpp2_2f64e68d / 10013 or cpp2_32f1713e / KEEP_DREAM.
13. Do not upload, copy into repo, base64-embed, or commit the sample binary.
14. Do not store raw binary bytes, full strings dump, full imports, full sections, full disassembly, full decompilation, screenshots, memory dumps, or bulky tool output.
15. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
16. Do not modify .codex-skills.
17. Do not create duplicate IDA/Ghidra/debugger/static extraction/runtime interfaces.
18. Do not use stale IDA/Ghidra/static artifacts as current evidence for cpp2_883e67b9.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read local_reverse_training_status/status_overlay only for current state verification.
3. Read queue refresh artifact and artifact_index as pointers.
4. Inspect existing repository interfaces for IDA/Ghidra/strings/file/objdump/radare2/StructuredEvidence/artifact_index registration.
5. Resolve E:\reverse\逆向课程2024春02\CPP2.exe under command-scoped LOCAL_REVERSE_ROOT.
6. Read the sample file only for sha256/size/file type and bounded static triage.
7. Run mature static tools if already available or system-provided, provided outputs are bounded summaries only.
8. Generate project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json.
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
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Must inspect bounded existing capability surface before any static tool invocation:

```text
Search repository for directly relevant existing tool interfaces and schemas:
  ida
  ghidra
  radare2
  r2
  strings
  objdump
  file
  static_extraction
  StructuredEvidence
  artifact_index
  local_reverse

Inspect only directly relevant modules/tests discovered by the search.
Prefer existing interfaces; do not create duplicates.
```

May inspect if directly relevant and bounded:

```text
project_state/local_reverse_inventory.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_ida_summary.json
existing project_state artifacts that describe current tool availability, only as capability hints, not as evidence for cpp2_883e67b9 unless sample_id/provenance is current.
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
3. Did it confirm this is static triage/readiness, not solving or validation?
4. Did it confirm task_packet remains advisory?
5. Did it confirm cpp2_883e67b9 is the next inventory_only sample from current queue/training state?
6. Did it confirm cpp2_32f1713e/KEEP_DREAM and cpp2_2f64e68d/10013 solved facts remain unchanged?
7. Did it inspect existing IDA/Ghidra/strings/file/objdump/radare2/StructuredEvidence/artifact_index interfaces before acting?
8. Which existing interfaces/tools are available?
9. Which existing interfaces/tools were used, if any?
10. Did it avoid creating duplicate tool interfaces?
11. Did it resolve the sample only through command-scoped LOCAL_REVERSE_ROOT=E:\reverse?
12. Did it verify size_bytes=196689 and sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8?
13. Did it classify file type/architecture/platform in bounded form?
14. Did it collect only bounded static triage summaries, not full dumps?
15. Did it avoid sample execution/runtime validation/debugger/hook/emulator/probe?
16. Did it avoid candidate generation/bruteforce/dictionary/search/fuzzing?
17. Did it avoid binary upload/copy/embed/full dumps?
18. Did it avoid modifying training_status/status_overlay?
19. Did it generate project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json?
20. Did it register the artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
21. Did the artifact make a clear recommendation for the next bounded decision, e.g. IDA/Ghidra evidence extraction or static constraint extraction?
22. Did it explain negative_results unchanged or non-use?
23. Did it run required py_compile/pytest/lint/status/git checks?
24. Did pytest_result.txt use this decision_id/report_id/round_id?
25. Did final lint-report run after report write?
26. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded tool-integration readiness only.

### Phase A — state preflight

Use `.venv\Scripts\python` for repository Python commands.

Verify:

```text
project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json:
  next_queue_hint.sample_id == cpp2_883e67b9
  next_queue_hint.training_status == inventory_only
  next_queue_hint.known_candidate == ""
  next_queue_hint.allowed_actions includes static_triage
  next_queue_hint.allowed_actions includes bounded_static_extraction_readiness

project_state/local_reverse_training_status.json:
  cpp2_883e67b9.training_status == inventory_only
  cpp2_883e67b9.known_candidate == ""
  cpp2_883e67b9.blocked_reason == ""
  cpp2_883e67b9.sha256 == 883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
  cpp2_883e67b9.size_bytes == 196689
```

If the queue or training state has drifted, stop as BLOCKED rather than selecting a different sample silently.

### Phase B — existing tool capability inspection

Search/inspect the repository for existing interfaces before using or adding anything:

```text
IDA / IDAPython runner or scripts
Ghidra runner or scripts
strings/file/objdump/radare2 wrappers or invocation patterns
StructuredEvidence conversion/schema
artifact_index registration helpers
local_reverse inventory/evaluation helpers
solver templates and static extraction templates
```

Decision rule:

```text
1. Use existing interfaces when available.
2. Use system mature static tools directly only if there is no project wrapper and output remains bounded.
3. Do not create a new generic tool interface in this round.
4. If no static triage path is available, still produce BLOCKED readiness artifact with missing capability details.
```

### Phase C — command-scoped sample identity/readiness

Resolve only this file:

```text
LOCAL_REVERSE_ROOT=E:\reverse
relative_path=逆向课程2024春02/CPP2.exe
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
```

Allowed identity checks:

```bat
cmd /c "set LOCAL_REVERSE_ROOT=E:\reverse&& .venv\Scripts\python -c \"import os, pathlib, hashlib; p=pathlib.Path(os.environ['LOCAL_REVERSE_ROOT'])/'逆向课程2024春02'/'CPP2.exe'; b=p.read_bytes(); print(p); print(len(b)); print(hashlib.sha256(b).hexdigest())\""
```

Do not print/store raw bytes.

### Phase D — bounded static triage

Collect only bounded summary fields, for example:

```text
file_format / platform / architecture / bitness if available
entrypoint if available
section names/counts only, no full section dump
import library/function count and only highly relevant names, no full import table
bounded strings indicators: success/failure/prompt/check keywords, max small snippets
presence of known packer/compiler clues if available
existing static-tool capability suitability: IDA/Ghidra/strings/file/objdump/radare2 available or blocked
recommended next bounded action
```

Do not infer a final candidate. Do not classify solved/blocked unless the triage itself is blocked by missing file/tool capability.

### Phase E — artifact generation

Generate:

```text
project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
```

Required top-level fields:

```text
schema_version=1
mainline=tool_integration
round_id=round_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1
decision_id=decision_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
command_scoped_root=E:\reverse
resolved_sample_path=E:\reverse\逆向课程2024春02\CPP2.exe
expected_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
expected_size_bytes=196689
identity_verified=true|false
readiness_status=READY|PARTIAL|BLOCKED|FAILED
training_status_before=inventory_only
known_candidate_before=""
source_queue_refresh_artifact=project_state\\local_reverse_queue_refresh_after_cpp2_32f1713e.json
existing_tool_interfaces_checked=true
existing_tool_interfaces={...bounded summary...}
static_tools_used=[...]
static_triage_summary={...bounded summary...}
structured_evidence_ready=true|false
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
next_recommended_mainline=tool_integration|reverse_solving|training_dataset
next_recommended_action=<bounded next step>
generated_at=<timestamp>
```

### Phase F — artifact_index registration

Register the artifact regardless of readiness_status:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_883e67b9_bounded_static_triage_readiness"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_883e67b9_bounded_static_triage_readiness"]
artifact_index.artifact_refs["local_reverse_cpp2_883e67b9_bounded_static_triage_readiness"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_bounded_static_triage_readiness
path=project_state\\local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json
freshness=current
source_run=round_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
readiness_status=READY|PARTIAL|BLOCKED|FAILED
identity_verified=true|false
training_status_before=inventory_only
candidate_generated=false
candidate_validated=false
source_queue_refresh_artifact=project_state\\local_reverse_queue_refresh_after_cpp2_32f1713e.json
next_recommended_mainline=<value>
```

Do not modify `local_reverse_training_status.json` or `status_overlay.json`.

### Phase G — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1",
  "round_id": "round_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1",
  "based_on_decision_id": "decision_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
readiness_status=READY -> status=SUCCESS, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
readiness_status=PARTIAL -> status=PARTIAL, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
readiness_status=BLOCKED -> status=BLOCKED, acceptance_recommendation=BLOCKED
readiness_status=FAILED -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

Use `ACCEPTED_WITH_LIMITATIONS` for READY/PARTIAL because no candidate solving or validation occurs in this round.

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
decision_id=decision_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1
report_id=report_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1
round_id=round_20260607_cpp2_883e67b9_bounded_static_triage_readiness_v1
```

Content assertions to record:

```text
1. decision_packet is the sole authority.
2. mainline=tool_integration.
3. source queue refresh points to cpp2_883e67b9.
4. cpp2_883e67b9 training_status remains inventory_only/known_candidate="".
5. sample identity verified by size and sha256, or artifact records BLOCKED reason.
6. existing IDA/Ghidra/strings/file/objdump/radare2/StructuredEvidence interfaces were checked before tool use.
7. no duplicate tool interface was created.
8. artifact exists at project_state/local_reverse_cpp2_883e67b9_bounded_static_triage_readiness.json.
9. artifact_index registers local_reverse_cpp2_883e67b9_bounded_static_triage_readiness as current.
10. candidate_generated=false.
11. candidate_validation_attempted=false.
12. training_status/status_overlay were not modified.
13. no sample executable was run.
14. no runtime tools/debugger/hook/emulator/probe were run.
15. no brute force/dictionary/search/fuzzing was run.
16. no binary was uploaded, copied, embedded, or committed.
17. no full strings/imports/sections/disassembly/decompilation dump was recorded.
18. pytest_result uses this decision_id/report_id/round_id.
19. final lint-report ran after report write.
20. git diff --name-status only contains allowed files.
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage.

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. cpp2_883e67b9 remains the current next queue sample;
2. identity is verified by command-scoped root, size, and sha256;
3. existing static/tool interfaces are inspected and no duplicate interface is created;
4. bounded triage/readiness artifact is produced and registered current;
5. artifact contains bounded static summary and clear next recommended decision;
6. no candidate is generated or validated;
7. no sample execution or forbidden runtime/debugger/search action occurred;
8. training_status/status_overlay remain unchanged;
9. tests/lint/report metadata align with this decision/report/round.
```

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. identity is verified but some static tools are unavailable;
2. artifact records unavailable capabilities and next bounded step;
3. no forbidden action occurred.
```

Stop with `BLOCKED` if:

```text
1. queue state no longer points to cpp2_883e67b9;
2. sample file is missing under command-scoped root;
3. size/sha256 mismatch;
4. no bounded static triage path is available.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. any forbidden execution/tool action occurs;
2. candidate is generated or validation attempted;
3. training_status/status_overlay are modified;
4. artifact_index/report/pytest_result do not align with this decision.
```
