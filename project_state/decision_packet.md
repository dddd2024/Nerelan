```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_static_triage_v1",
  "round_id": "round_20260607_cpp2_32f1713e_static_triage_v1",
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

目标：对训练队列第一项 `cpp2_32f1713e` 做一次 **bounded static triage**，确认该本地 PE 样本的静态证据入口、可复用工具接口和后续候选分析路线。

本轮不是求解，不生成 candidate，不做 runtime validation。允许的动作仅限：

```text
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
mainline=tool_integration
allowed_actions=[static_triage]
forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

本轮必须产出一个可审计的静态 triage artifact，并登记到 artifact_index：

```text
project_state/local_reverse_cpp2_32f1713e_static_triage.json
```

Artifact 目标不是证明答案，而是回答：

```text
1. 该样本在训练队列和训练状态中是否仍是 inventory_only。
2. 现有项目中可复用哪些静态/IDA/StructuredEvidence/solver/harness 接口。
3. 当前样本是否已有 current 静态 artifact；若没有，是否能用已有接口生成静态证据。
4. 初步识别样本类型、PE 元数据、字符串/导入/比较点/常量线索。
5. 给出下一轮 reverse_solving 或继续 tool_integration 的最小可执行建议。
```

---

## 2. Current Evidence

当前 `decision_packet.md` 是本轮唯一执行权威。`project_state/task_packet.json` 的 `task` 仍是旧 `samplereverse` advisory，不控制本轮。

最近一轮 `training_dataset` 汇总同步已经 ACCEPTED：

```text
project_state/local_reverse_training_status.json:
  sample_count=29
  solved=3
  blocked=4
  needs_triage=0
  inventory_only=22

project_state/local_reverse_training_status_summary_sync.json:
  executed_sample=false
  ran_static_tools=false
  ran_runtime_tools=false
  before_summary={sample_count=29, solved=2, blocked=5, needs_triage=0, inventory_only=22}
  after_summary={sample_count=29, solved=3, blocked=4, needs_triage=0, inventory_only=22}
```

Current queue context:

```text
project_state/local_reverse_evaluation_queue.json:
  queue_policy=simple_static_first_unsolved_only
  exclude_solved_samples includes cpp2_2f64e68d
  rank 1 sample_id=cpp2_32f1713e
  relative_path=逆向课程2023春补考02/Cpp2.exe
  proposed_next_mainline=tool_integration
  allowed_actions=[static_triage]
  forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

Training status context:

```text
project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status=inventory_only
  cpp2_32f1713e.known_candidate=""
  cpp2_32f1713e.blocked_reason=""
  cpp2_32f1713e.classification=""
  cpp2_32f1713e.next_action="static triage and manual evaluation required"
```

Existing related capabilities found in repository state/search and must be inspected before implementation:

```text
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_targeted_static_reextract.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_training_status.py
reverse_agent/project_state.py
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
project_state/local_reverse_forced_ida_extraction_result.json
project_state/local_reverse_training_status_summary_sync.json
```

Known existing static/IDA evidence keys in artifact_index/current_state include prior local_reverse IDA evidence and solver outputs for other samples, but there is no current static triage artifact for `cpp2_32f1713e`. Do not treat artifacts for other samples as current evidence for this sample.

`negative_results.json` mainly records old `samplereverse` forbidden directions. They remain applicable as global safety constraints: do not return to blind search, do not expand beam/budget, do not run breakpoint probes, and do not commit solve_reports.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not solve cpp2_32f1713e in this round.
3. Do not generate or validate a candidate.
4. Do not run the sample executable.
5. Do not run debugger, hook, emulator, runtime probe, console validator, winpty, or dynamic harness.
6. Do not bruteforce or run dictionary search.
7. Do not upload, copy, commit, base64-embed, or otherwise add any sample binary to GitHub.
8. Do not commit solve_reports, .venv, site-packages, wheel, DLL, EXE, PDB, dump, screenshot, or local binary data.
9. Do not scan full solve_reports, full PROJECT_PROGRESS_LOG.txt, or the entire local sample tree.
10. Do not rebuild full inventory.
11. Do not modify .codex-skills.
12. Do not create a duplicate IDA/Ghidra/debugger interface if an existing interface can be reused.
13. Do not mark cpp2_32f1713e solved or blocked in training_status/status_overlay.
14. Do not change any existing solved sample, especially cpp2_2f64e68d / 10013.
15. Do not use stale artifacts for other samples as current evidence for cpp2_32f1713e.
```

Allowed:

```text
1. Read default project_state files.
2. Read .codex-skills/registry.json.
3. Inspect existing local_reverse static/IDA/training modules and tests.
4. Read local inventory/training metadata for cpp2_32f1713e only.
5. If the local binary exists, run static-only metadata extraction using mature tools or existing project wrappers: file/strings/objdump/radare2/pefile/IDA batch static export, with no process execution.
6. If IDA/Ghidra/static tools are unavailable, record availability=false and proceed with repository metadata/static alternatives only.
7. Generate project_state/local_reverse_cpp2_32f1713e_static_triage.json.
8. Update artifact_index latest_artifacts and latest_artifacts_v2 for the new artifact.
9. Optionally add low-token pointers in current_state/task_packet; preserve old fields and task advisory semantics.
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
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_training_status_summary_sync.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
reverse_agent/local_reverse_training_status.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_targeted_static_reextract.py
reverse_agent/local_reverse_constraint_recovery.py
tests/test_project_state.py
```

Inspect if present and directly relevant:

```text
project_state/local_reverse_inventory.json
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
project_state/local_reverse_forced_ida_extraction_result.json
project_state/local_reverse_cpp2_32f1713e_static_triage.json  # should be missing/stale before this round
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
3. Did it confirm task_packet.task remains advisory and not this round's task?
4. Did it confirm cpp2_32f1713e is rank 1 in local_reverse_evaluation_queue?
5. Did it confirm cpp2_32f1713e is inventory_only before this round?
6. Did it confirm no sample executable was run?
7. Did it confirm no debugger/hook/emulator/runtime probe/winpty/console validator was run?
8. Did it confirm no bruteforce/dictionary search/candidate validation was run?
9. Did it confirm no sample binary was uploaded or committed?
10. Did it inspect existing static/IDA/tool interfaces before adding any code?
11. Did it avoid duplicate IDA/Ghidra/debugger interface implementation?
12. Did it list which mature/static tools were available and used or unavailable?
13. Did it generate project_state/local_reverse_cpp2_32f1713e_static_triage.json?
14. Did the static triage artifact record tool availability, metadata source, sample id/path/sha if available, and extracted static evidence?
15. Did it register the new artifact in artifact_index.latest_artifacts and latest_artifacts_v2?
16. Did it preserve training_status/status_overlay sample state and not mark solved/blocked?
17. Did it preserve old current_state/task_packet compatibility fields?
18. Did it explain why negative_results was not changed, or update it only if a new failed direction was actually discovered?
19. Did it run py_compile and pytest/lint checks?
20. Did pytest_result.txt use this decision_id/report_id/round_id?
21. Did final lint-report run after report write?
22. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded task. Prefer mature tools and existing wrappers. Do not add heavy architecture.

### Phase A — preflight state checks

Use `.venv\Scripts\python` for Python commands.

Assert:

```text
project_state/local_reverse_evaluation_queue.json:
  items[0].sample_id == cpp2_32f1713e
  items[0].allowed_actions == [static_triage]
  items[0].forbidden_actions includes runtime_probe, bruteforce, upload_binary

project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
  cpp2_32f1713e.blocked_reason == ""

training_materials/local_reverse/status_overlay.json:
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
```

If any assertion fails, stop and write `status=BLOCKED`; do not self-correct the queue or status in this round.

### Phase B — capability audit

Inspect existing code before building anything:

```text
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_targeted_static_reextract.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_training_status.py
reverse_agent/project_state.py
tests/test_project_state.py
```

Record in artifact:

```text
existing_ida_interface=true|false
existing_ghidra_interface=true|false
existing_strings_or_file_static_path=true|false
existing_radare2_or_objdump_static_path=true|false
existing_structured_evidence_conversion=true|false
existing_solver_templates=true|false
existing_harness_or_validation_path=true|false
reuse_decision=<which interface to reuse or why unavailable>
duplicate_interface_created=false
```

Do not create a duplicate IDA runner if an existing one is available. If a missing wrapper is discovered, record it as a future gap; do not implement it unless it is a tiny adapter strictly needed for artifact formatting and covered by tests.

### Phase C — static triage extraction

If the local sample file is available at the inventory path, perform static-only extraction. Allowed examples:

```text
file type / PE architecture / subsystem / bitness / imports / exports / sections
strings summary with bounded count and relevant suspicious strings
static compare/import clues: strcmp/strncmp/memcmp/GetProcAddress/ReadFile/scanf/cin/printf/message strings
candidate algorithm hints: xor/shift/base64/rc4/des/sha/md5/aes table constants if visible
IDA/Ghidra static output only if existing integration is present and does not execute the binary
```

Hard limits:

```text
Do not execute the PE.
Do not attach debugger.
Do not invoke harness runtime validation.
Do not brute force or solve.
Do not dump full strings if large; record bounded top/relevant strings only.
Do not store raw binary bytes in artifact.
```

If local sample is unavailable in Codex environment, still generate a BLOCKED or PARTIAL artifact that records:

```text
local_sample_available=false
reason=MISSING_LOCAL_SAMPLE_OR_ROOT
next_action=request local sample access or rerun on local machine
```

### Phase D — artifact generation

Generate:

```text
project_state/local_reverse_cpp2_32f1713e_static_triage.json
```

Required fields:

```text
schema_version=1
mainline=tool_integration
round_id=round_20260607_cpp2_32f1713e_static_triage_v1
decision_id=decision_20260607_cpp2_32f1713e_static_triage_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
training_status_before=inventory_only
known_candidate_before=""
executed_sample=false
ran_runtime_tools=false
ran_debugger=false
ran_bruteforce=false
uploaded_binary=false
local_sample_available=true|false
static_tools_used=[]
static_tools_unavailable=[]
existing_tool_interfaces={...}
duplicate_interface_created=false
file_metadata={...}
static_evidence={strings_summary, imports_summary, sections_summary, compare_clues, crypto_or_transform_hints}
triage_status=SUCCESS|PARTIAL|BLOCKED
recommended_next_mainline=reverse_solving|tool_integration|training_dataset
recommended_next_action=<bounded next step>
generated_at=<timestamp>
```

### Phase E — artifact_index and optional low-token pointers

Update:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_static_triage"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_static_triage"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_static_triage
path=project_state\local_reverse_cpp2_32f1713e_static_triage.json
freshness=current
source_run=round_20260607_cpp2_32f1713e_static_triage_v1
sha256=<actual sha256>
size_bytes=<actual size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
```

Optional low-token updates:

```text
current_state.local_reverse_next_queue_hint may remain cpp2_32f1713e.
current_state may add local_reverse_current_static_triage=project_state\local_reverse_cpp2_32f1713e_static_triage.json.
task_packet may add local_reverse_current_static_triage but must keep task_packet.task advisory.
```

Do not update training_status/status_overlay to solved or blocked in this round. If triage is successful, keep sample as `inventory_only` or at most add a non-status artifact pointer only if existing format supports it; otherwise leave status files unchanged.

### Phase F — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_static_triage_v1",
  "round_id": "round_20260607_cpp2_32f1713e_static_triage_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_static_triage_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Report must explicitly state whether static triage produced enough evidence to schedule a future `reverse_solving` decision, or whether another `tool_integration` evidence extraction step is needed first.

---

## 7. Tests

All Python commands must use `.venv\Scripts\python`.

Must run and record:

```text
.venv\Scripts\python -m py_compile reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state   # final after report write
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

If any project source files are changed, also run targeted tests for the changed code. If only project_state JSON/Markdown artifacts are changed, `tests/test_project_state.py` is sufficient.

Content assertions required in report/pytest_result:

```text
1. No sample executable run.
2. No debugger/hook/emulator/runtime probe/winpty/console validator run.
3. No bruteforce/dictionary/candidate validation run.
4. No binary uploaded or committed.
5. Existing local_reverse static/IDA interfaces were inspected.
6. No duplicate mature-tool interface was created.
7. cpp2_32f1713e remained inventory_only and known_candidate="".
8. local_reverse_cpp2_32f1713e_static_triage.json exists.
9. artifact_index registers local_reverse_cpp2_32f1713e_static_triage as current.
10. pytest_result uses this decision_id/report_id/round_id.
11. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop and write `status=BLOCKED` or `status=FAILED`, not ACCEPT, if any condition occurs:

```text
1. cpp2_32f1713e is not rank 1 in evaluation_queue.
2. cpp2_32f1713e is not inventory_only before triage.
3. Any sample execution would be required.
4. Any debugger/hook/emulator/runtime probe/winpty/console validator would be required.
5. Any bruteforce/dictionary/candidate validation would be required.
6. Existing static/IDA interfaces cannot be inspected.
7. A duplicate mature-tool interface would be needed.
8. The local sample binary would need to be uploaded or committed.
9. The triage artifact cannot be generated.
10. artifact_index cannot register the triage artifact.
11. training_status/status_overlay would need solved/blocked mutation.
12. current_state/task_packet update would delete old compatibility fields.
13. pytest_result does not include py_compile reverse_agent/project_state.py.
14. pytest_result does not match this decision/report/round.
15. lint-report after final report write fails.
16. git diff includes .venv, site-packages, DLL, EXE, sample binary, solve_reports, or .codex-skills.
```
