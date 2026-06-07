```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1",
  "round_id": "round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1",
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

本轮主线是 **reverse_solving**，任务是修复上一轮 `cpp2_32f1713e` targeted static solving 的 provenance、schema、artifact key、artifact path 和 report/test 对齐问题。

上一轮静态分析可能已经给出有价值候选 `KEEP_DREAM`，但上一轮产物不能直接验收，原因是：

```text
1. decision_packet 要求的 artifact path/key 是 targeted_static_solving；Codex 实际写成 targeted_static_solve。
2. 实际 artifact 内部 decision_id/round_id 使用了 targeted_static_solve_v1，未匹配当前 decision。
3. report 给出 ACCEPTED，但原 decision 要求未 runtime validation 时最多 ACCEPTED_WITH_LIMITATIONS。
4. pytest_result 检查了错误 artifact key/path，并接受了非 decision 指定的状态枚举。
5. artifact schema 没有使用原 decision 要求的 static_solving_status、solver_classification、unvalidated_candidate_hypothesis 等字段。
```

目标：基于上一轮 `project_state/local_reverse_cpp2_32f1713e_targeted_static_solve.json` 中的静态证据，生成规范化 rework artifact：

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json
```

本轮只做状态/产物/报告修复和 bounded consistency audit，不重新扩大逆向分析范围，不运行样本，不做 runtime validation，不修改训练状态。

允许产出 `KEEP_DREAM` 作为 **unvalidated_candidate_hypothesis**，但不得写成 validated、solved 或 training known_candidate。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 Codex report 声明：

```text
report_id=report_20260607_cpp2_32f1713e_targeted_static_solving_v1
round_id=round_20260607_cpp2_32f1713e_targeted_static_solving_v1
based_on_decision_id=decision_20260607_cpp2_32f1713e_targeted_static_solving_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
candidate=KEEP_DREAM
candidate_confidence=HIGH
```

但上一轮实际 generated_artifacts 为：

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solve.json
```

上一轮 actual artifact 内部写入：

```text
round_id=round_20260607_cpp2_32f1713e_targeted_static_solve_v1
decision_id=decision_20260607_cpp2_32f1713e_targeted_static_solve_v1
solving_status=SOLVED_BY_STATIC_ANALYSIS
unvalidated_candidate=KEEP_DREAM
candidate_confidence=HIGH
```

这与当前 decision/report/pytest_result 的 `targeted_static_solving_v1` 命名不一致，属于 provenance mismatch。

上一轮 artifact_index 当前注册：

```text
latest_artifacts["local_reverse_cpp2_32f1713e_targeted_static_solve"]
latest_artifacts_v2["local_reverse_cpp2_32f1713e_targeted_static_solve"]
artifact_refs["local_reverse_cpp2_32f1713e_targeted_static_solve"]
```

但本轮必须改为注册：

```text
latest_artifacts["local_reverse_cpp2_32f1713e_targeted_static_solving"]
latest_artifacts_v2["local_reverse_cpp2_32f1713e_targeted_static_solving"]
artifact_refs["local_reverse_cpp2_32f1713e_targeted_static_solving"]
```

Current source static extraction remains usable if still registered current:

```text
project_state/local_reverse_cpp2_32f1713e_bounded_static_extraction.json:
  sample_id=cpp2_32f1713e
  static_extraction_status=SUCCESS
  identity_verified=true
  candidate_generated=false
  candidate_validation_attempted=false
```

Current readiness remains usable if still registered current:

```text
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json:
  sample_id=cpp2_32f1713e
  readiness_status=READY
  ready_for_static_extraction=true
  command_scoped_root=E:\reverse
  resolved_sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
  size_bytes=196686
  sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
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

negative_results mainly concerns old `samplereverse` directions and must remain respected: do not run blind search, do not commit full solve_reports, do not use stale artifacts as current evidence. For this sample, also preserve the training queue constraints: no runtime_probe, no brute force, no upload_binary.

Skill profile must remain `reverse-agent-iteration@v2`, which is active in `.codex-skills/registry.json`.

Mature tools rule still applies, but this rework should not create or modify IDA/Ghidra/debugger/static extraction interfaces. It should only normalize project_state artifacts and report/test metadata.

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
15. Do not claim candidate KEEP_DREAM is valid without a future runtime validation decision.
16. Do not start runtime oracle validation in this round.
17. Do not keep the previous ACCEPTED recommendation; unvalidated static candidate means at most ACCEPTED_WITH_LIMITATIONS.
18. Do not register only local_reverse_cpp2_32f1713e_targeted_static_solve as the current artifact for this decision.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read project_state/local_reverse_cpp2_32f1713e_targeted_static_solve.json as legacy source evidence.
3. Read current readiness and bounded static extraction artifacts for cpp2_32f1713e.
4. Read inventory/training/queue metadata only for cpp2_32f1713e and direct consistency checks.
5. Generate project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json using normalized schema.
6. Register local_reverse_cpp2_32f1713e_targeted_static_solving in artifact_index latest_artifacts, latest_artifacts_v2 and artifact_refs.
7. Optionally leave the old targeted_static_solve artifact as legacy source, but do not make it the required current artifact for this decision.
8. Write codex_execution_report.md and pytest_result.txt for this rework.
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
project_state/local_reverse_cpp2_32f1713e_targeted_static_solve.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Do not read by default:

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse full tree beyond direct identity metadata already established
```

---

## 5. Required Audit

Codex report must answer:

```text
1. Did it confirm decision_packet is the sole execution authority?
2. Did it confirm this is a rework of targeted_static_solving metadata/schema/provenance?
3. Did it confirm mainline=reverse_solving?
4. Did it confirm no runtime validation is allowed in this round?
5. Did it inspect previous targeted_static_solve artifact only as legacy source evidence?
6. Did it create project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json?
7. Did new artifact decision_id equal decision_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1?
8. Did new artifact round_id equal round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1?
9. Did new artifact use static_solving_status instead of SOLVED_BY_STATIC_ANALYSIS?
10. Did it put KEEP_DREAM only under unvalidated_candidate_hypothesis?
11. Did it set candidate_validation_attempted=false and candidate_validated=false?
12. Did it avoid solved/blocked training status changes?
13. Did it register artifact_index key local_reverse_cpp2_32f1713e_targeted_static_solving as current?
14. Did latest_artifacts_v2 include kind=local_reverse_targeted_static_solving?
15. Did latest_artifacts_v2 include source_run=round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1?
16. Did it record old targeted_static_solve only as legacy_source_artifact if needed?
17. Did it avoid sample execution?
18. Did it avoid debugger/hook/emulator/runtime probe/winpty/console validator?
19. Did it avoid brute force/dictionary/runtime candidate validation?
20. Did it confirm no binary or full dumps were committed?
21. Did it preserve cpp2_2f64e68d solved facts?
22. Did it explain negative_results unchanged or non-use?
23. Did it run required py_compile/pytest/lint/status/git checks?
24. Did pytest_result.txt use this rework decision_id/report_id/round_id?
25. Did pytest_result check targeted_static_solving, not targeted_static_solve?
26. Did final lint-report run after report write?
27. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded rework only.

### Phase A — state and legacy artifact preflight

Use `.venv\Scripts\python` for repository Python commands.

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

project_state/local_reverse_cpp2_32f1713e_targeted_static_solve.json:
  sample_id == cpp2_32f1713e
  unvalidated_candidate == KEEP_DREAM
  candidate_validation_attempted == false
  executed_sample == false
  ran_runtime_tools == false
  ran_debugger == false
  ran_bruteforce == false

project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
  cpp2_32f1713e.blocked_reason == ""
```

This is a metadata/provenance rework. Do not repeat sample identity hashing unless needed for consistency checks; do not access or run the binary in this round.

### Phase B — generate normalized artifact

Create:

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json
```

Required top-level fields:

```text
schema_version=1
mainline=reverse_solving
round_id=round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
decision_id=decision_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
command_scoped_root=E:\reverse
sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
size_bytes=196686
sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
identity_verified=true
source_static_artifact=project_state\\local_reverse_cpp2_32f1713e_bounded_static_extraction.json
source_static_status=SUCCESS
source_readiness_artifact=project_state\\local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
source_readiness_status=READY
legacy_source_artifact=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solve.json
legacy_source_round_id=round_20260607_cpp2_32f1713e_targeted_static_solve_v1
legacy_source_decision_id=decision_20260607_cpp2_32f1713e_targeted_static_solve_v1
rework_reason=provenance_schema_key_alignment
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
next_recommended_mainline=reverse_solving
next_recommended_action=<bounded runtime validation decision, if candidate hypothesis remains strong>
generated_at=<timestamp>
```

If carrying forward `KEEP_DREAM`, encode it as:

```json
"unvalidated_candidate_hypothesis": {
  "candidate": "KEEP_DREAM",
  "confidence": "HIGH",
  "validation_status": "unvalidated",
  "proof_chain_summary": [
    "target table NEEP_AXEDG from legacy static artifact",
    "transform swaps bit positions 1 and 2 in low nibble",
    "transform is self-inverse for all 256 byte values",
    "inverse transform yields KEEP_DREAM",
    "length check requires 10 bytes"
  ],
  "requires_future_runtime_validation": true
}
```

Do not use `solving_status=SOLVED_BY_STATIC_ANALYSIS` in the new artifact. Use `static_solving_status=SUCCESS` if the normalized proof chain is complete, or `PARTIAL` if Codex cannot confidently normalize the previous evidence.

### Phase C — artifact_index registration

Register the new artifact regardless of SUCCESS/PARTIAL/BLOCKED/FAILED:

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
source_run=round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
static_solving_status=SUCCESS|PARTIAL|BLOCKED|FAILED
identity_verified=true
candidate_generated=true|false
candidate_validated=false
candidate_acceptance_status=unvalidated|null
source_static_artifact=project_state\\local_reverse_cpp2_32f1713e_bounded_static_extraction.json
legacy_source_artifact=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solve.json
rework_of=local_reverse_cpp2_32f1713e_targeted_static_solve
```

Do not remove old artifact unless project_state helpers require cleanup. If it remains, it must not be the only current artifact for this rework.

Optional low-token pointers:

```text
current_state.local_reverse_current_static_solving=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solving.json
task_packet.local_reverse_current_static_solving=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solving.json
```

Do not change `task_packet.task`. Do not alter training_status/status_overlay.

### Phase D — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1",
  "round_id": "round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1",
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
static_solving_status=FAILED  -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

Even on SUCCESS, use `ACCEPTED_WITH_LIMITATIONS` because no runtime validation happened.

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
decision_id=decision_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
report_id=report_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
round_id=round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
```

Content assertions to record:

```text
1. source static extraction artifact is current/SUCCESS/identity_verified.
2. source readiness artifact is current/READY.
3. legacy targeted_static_solve artifact is read only as legacy source.
4. new targeted_static_solving artifact exists.
5. new artifact decision_id/round_id match this rework decision.
6. new artifact uses static_solving_status SUCCESS/PARTIAL/BLOCKED/FAILED.
7. artifact_index registers local_reverse_cpp2_32f1713e_targeted_static_solving as current.
8. artifact_index latest_artifacts_v2 kind is local_reverse_targeted_static_solving.
9. old targeted_static_solve is not the only current artifact for this rework.
10. no sample executable was run.
11. no debugger/hook/emulator/runtime probe/winpty/console validator was run.
12. no brute force/dictionary/runtime candidate validation was run.
13. no candidate was marked validated.
14. KEEP_DREAM, if present, is only unvalidated_candidate_hypothesis.
15. no solved/blocked training status was written.
16. no binary was uploaded, copied, embedded, or committed.
17. artifact contains no raw binary, full strings dump, full imports, full sections, full disassembly, full decompilation, screenshots, or dumps.
18. no duplicate IDA/Ghidra/debugger/static extraction interface was created.
19. training_status/status_overlay sample state unchanged.
20. cpp2_2f64e68d solved facts unchanged.
21. pytest_result uses this rework decision_id/report_id/round_id.
22. final lint-report ran after report write.
23. git diff --name-status only contains allowed files.
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage. Acceptance recommendation must remain at most `ACCEPTED_WITH_LIMITATIONS`.

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED_WITH_LIMITATIONS` only if:

```text
1. project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json exists;
2. new artifact decision_id/round_id match this rework decision;
3. new artifact schema uses required fields and allowed status enums;
4. KEEP_DREAM, if present, is explicitly unvalidated;
5. artifact_index registers local_reverse_cpp2_32f1713e_targeted_static_solving as current;
6. report recommendation is ACCEPTED_WITH_LIMITATIONS, not ACCEPTED;
7. no forbidden dynamic/runtime/bruteforce action occurred;
8. training_status/status_overlay remain unchanged for cpp2_32f1713e;
9. tests/lint/report metadata are aligned with this rework decision/report/round.
```

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. provenance/key/schema are corrected;
2. legacy static evidence cannot be confidently normalized into SUCCESS;
3. all bounds and prohibitions are respected;
4. artifact clearly states missing evidence and next bounded step.
```

Stop with `BLOCKED` if required current source artifacts are missing/stale or the legacy source artifact is unavailable and cannot be normalized without redoing analysis.

Stop with `FAILED / REWORK_REQUIRED` if any forbidden action occurs, report/test metadata still refer to `targeted_static_solve` as the required key, or training status is modified.
