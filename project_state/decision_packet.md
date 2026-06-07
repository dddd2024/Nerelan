```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_training_status_sync_v1",
  "round_id": "round_20260607_cpp2_32f1713e_training_status_sync_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **training_dataset**，范围限定为把已 runtime validated 的 `cpp2_32f1713e / KEEP_DREAM` 同步进本地训练集状态。

目标：基于上一轮 current runtime validation artifact，将 `cpp2_32f1713e` 从 `inventory_only` 更新为 `solved`，写入 `known_candidate=KEEP_DREAM`，并记录验证证据来源。

必须产出：

```text
project_state/local_reverse_cpp2_32f1713e_training_status_sync.json
```

允许修改：

```text
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

本轮不运行样本、不做新求解、不做新的静态提取、不做调试/hook/probe。只做训练状态同步和一致性审计。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论为 **ACCEPTED_WITH_LIMITATIONS**：`KEEP_DREAM` 已通过 bounded runtime validation，但 training status sync 被明确推迟到单独一轮。

Current runtime validation artifact:

```text
project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json:
  decision_id=decision_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
  round_id=round_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
  sample_id=cpp2_32f1713e
  candidate=KEEP_DREAM
  negative_control=KEEP_DREAN
  validation_status=VALIDATED
  candidate_success_signal_captured=true
  candidate_failure_signal_captured=false
  control_success_signal_captured=false
  control_failure_signal_captured=true
  oracle_verdict_source=stdout_signal
  executed_sample=true
  execution_count=2
  ran_debugger=false
  ran_hook=false
  ran_emulator=false
  ran_probe=false
  ran_bruteforce=false
  ran_dictionary_search=false
  candidate_search_performed=false
  uploaded_binary=false
  training_status_modified=false
```

`artifact_index.latest_artifacts_v2` registers the runtime validation artifact as current:

```text
local_reverse_cpp2_32f1713e_keep_dream_runtime_validation:
  kind=local_reverse_candidate_runtime_validation
  path=project_state\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
  freshness=current
  source_run=round_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
  sample_id=cpp2_32f1713e
  candidate=KEEP_DREAM
  validation_status=VALIDATED
  candidate_success_signal_captured=true
  control_failure_signal_captured=true
  source_static_solving_artifact=project_state\local_reverse_cpp2_32f1713e_targeted_static_solving.json
  training_status_modified=false
```

Current normalized static solving artifact remains relevant evidence:

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json:
  static_solving_status=SUCCESS
  unvalidated_candidate_hypothesis.candidate=KEEP_DREAM
  candidate_acceptance_status=unvalidated
```

Current training state before this sync must be:

```text
project_state/local_reverse_training_status.json:
  sample_count=29
  status_summary.solved=3
  status_summary.blocked=4
  status_summary.needs_triage=0
  status_summary.inventory_only=22
  cpp2_32f1713e.training_status=inventory_only
  cpp2_32f1713e.known_candidate=""
  cpp2_32f1713e.blocked_reason=""
  cpp2_32f1713e.classification=""

training_materials/local_reverse/status_overlay.json:
  sample_count=29
  status_summary.solved=3
  status_summary.blocked=4
  status_summary.needs_triage=0
  status_summary.inventory_only=22
  cpp2_32f1713e.training_status=inventory_only
  cpp2_32f1713e.known_candidate=""
  cpp2_32f1713e.blocked_reason=""
```

Expected training state after this sync:

```text
sample_count=29
status_summary.solved=4
status_summary.blocked=4
status_summary.needs_triage=0
status_summary.inventory_only=21
cpp2_32f1713e.training_status=solved
cpp2_32f1713e.known_candidate=KEEP_DREAM
cpp2_32f1713e.blocked_reason=""
cpp2_32f1713e.classification=runtime_validated_console_password_checker or oracle_backed_runtime_validated
```

negative_results mainly concerns old `samplereverse` directions. This round must not run blind search, not expand budgets, not commit full solve_reports, not use stale artifacts as current evidence. For `cpp2_32f1713e`, do not repeat runtime validation; use only the current runtime validation artifact.

Skill profile must remain `reverse-agent-iteration@v2`, which is active in `.codex-skills/registry.json`.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run the sample executable.
3. Do not rerun KEEP_DREAM or KEEP_DREAN validation.
4. Do not execute any candidate or control input.
5. Do not generate a new candidate.
6. Do not run brute force, dictionary search, candidate search, fuzzing, or broad input enumeration.
7. Do not attach debugger, hook, emulator, instrumentation probe, breakpoint probe, or dynamic trace collector.
8. Do not use IDA/Ghidra for new analysis in this training sync round.
9. Do not create duplicate training inventory/status/artifact_index helpers unless strictly required by existing project_state code.
10. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
11. Do not upload, copy into repo, base64-embed, or commit the sample binary.
12. Do not store raw binary bytes, stdout dumps, memory dumps, screenshots, full disassembly, or full decompilation.
13. Do not modify .codex-skills.
14. Do not alter unrelated samples except aggregate solved/inventory counts required by this one-sample status transition.
15. Do not alter cpp2_2f64e68d / 10013 solved facts.
16. Do not mark cpp2_32f1713e solved unless the current runtime validation artifact is present, current, and VALIDATED.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current runtime validation artifact for cpp2_32f1713e.
3. Read current targeted_static_solving artifact for cpp2_32f1713e.
4. Read and update project_state/local_reverse_training_status.json.
5. Read and update training_materials/local_reverse/status_overlay.json.
6. Generate project_state/local_reverse_cpp2_32f1713e_training_status_sync.json.
7. Register the sync artifact in artifact_index.
8. Write codex_execution_report.md and pytest_result.txt.
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
project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

May inspect if directly needed:

```text
project_state/local_reverse_training_status_summary_sync.json
project_state/local_reverse_post_solve_state_sync.json
project_state/local_reverse_inventory.json
```

Do not read by default:

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse tree or sample binary
```

---

## 5. Required Audit

Codex report must answer:

```text
1. Did it confirm decision_packet is the sole execution authority?
2. Did it confirm mainline=training_dataset?
3. Did it confirm this is training status sync, not runtime validation or solving?
4. Did it confirm task_packet.task remains advisory?
5. Did it confirm current runtime validation artifact is current/VALIDATED/KEEP_DREAM?
6. Did it confirm candidate success signal and control failure signal are recorded in current artifact?
7. Did it confirm source targeted_static_solving artifact is current/SUCCESS?
8. Did it confirm pre-sync training status for cpp2_32f1713e was inventory_only / known_candidate=""?
9. Did it update project_state/local_reverse_training_status.json for only cpp2_32f1713e plus aggregate counts?
10. Did it update training_materials/local_reverse/status_overlay.json for only cpp2_32f1713e plus aggregate counts?
11. Did it set cpp2_32f1713e.training_status=solved?
12. Did it set cpp2_32f1713e.known_candidate=KEEP_DREAM?
13. Did it clear blocked_reason and set a runtime validation classification?
14. Did it record evidence source project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json?
15. Did it keep cpp2_2f64e68d solved facts unchanged?
16. Did it avoid modifying unrelated sample statuses?
17. Did it avoid sample execution and runtime tools?
18. Did it avoid debugger/hook/emulator/probe/instrumentation?
19. Did it avoid brute force/dictionary/search/fuzzing?
20. Did it avoid binary upload/copy/embed/full dumps?
21. Did it generate project_state/local_reverse_cpp2_32f1713e_training_status_sync.json?
22. Did it register the sync artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
23. Did aggregate status summary become solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29?
24. Did it explain negative_results unchanged or non-use?
25. Did it run required py_compile/pytest/lint/status/git checks?
26. Did pytest_result.txt use this decision_id/report_id/round_id?
27. Did final lint-report run after report write?
28. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded training status sync only.

### Phase A — preflight

Use `.venv\Scripts\python` for repository Python commands.

Verify current runtime validation artifact:

```text
project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json:
  sample_id == cpp2_32f1713e
  candidate == KEEP_DREAM
  negative_control == KEEP_DREAN
  validation_status == VALIDATED
  candidate_success_signal_captured == true
  control_failure_signal_captured == true
  training_status_modified == false
```

Verify source static artifact:

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json:
  sample_id == cpp2_32f1713e
  static_solving_status == SUCCESS
  unvalidated_candidate_hypothesis.candidate == KEEP_DREAM
```

Verify pre-sync training state:

```text
project_state/local_reverse_training_status.json:
  status_summary.solved == 3
  status_summary.inventory_only == 22
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""

training_materials/local_reverse/status_overlay.json:
  status_summary.solved == 3
  status_summary.inventory_only == 22
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
```

If pre-sync counts differ only because another accepted sync already updated the same sample, stop as BLOCKED and report state drift rather than double-counting.

### Phase B — update training status files

Update only `cpp2_32f1713e` and aggregate counts.

In `project_state/local_reverse_training_status.json`, set:

```text
status_summary.solved=4
status_summary.solved_count=4 if present
status_summary.inventory_only=21
status_summary.inventory_only_count=21 if present
status_summary.blocked=4
status_summary.blocked_count=4 if present
status_summary.needs_triage=0
sample cpp2_32f1713e:
  training_status=solved
  known_candidate=KEEP_DREAM
  blocked_reason=""
  classification=oracle_backed_runtime_validated
  evidence_sources includes:
    source:local_reverse_cpp2_32f1713e_targeted_static_solving.json
    source:local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
    runtime_validation
    runtime_validated_success
    positive_candidate:KEEP_DREAM
    negative_control:KEEP_DREAN
  next_action=sample solved by bounded runtime validation; no further solving required
```

In `training_materials/local_reverse/status_overlay.json`, set:

```text
status_summary.solved=4
status_summary.inventory_only=21
status_summary.blocked=4
status_summary.needs_triage=0
sample cpp2_32f1713e:
  training_status=solved
  known_candidate=KEEP_DREAM
  blocked_reason=""
  solved_by=bounded_runtime_validation
  solved_at=<timestamp>
  solved_round=round_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
  evidence_source=project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
```

Do not change other samples except aggregate counts.

### Phase C — generate sync artifact

Generate:

```text
project_state/local_reverse_cpp2_32f1713e_training_status_sync.json
```

Required top-level fields:

```text
schema_version=1
mainline=training_dataset
round_id=round_20260607_cpp2_32f1713e_training_status_sync_v1
decision_id=decision_20260607_cpp2_32f1713e_training_status_sync_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
candidate=KEEP_DREAM
source_runtime_validation_artifact=project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
source_runtime_validation_status=VALIDATED
source_static_solving_artifact=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solving.json
pre_sync_status=inventory_only
post_sync_status=solved
pre_sync_known_candidate=""
post_sync_known_candidate=KEEP_DREAM
training_status_file=project_state\\local_reverse_training_status.json
status_overlay_file=training_materials\\local_reverse\\status_overlay.json
aggregate_counts_before={sample_count:29, solved:3, blocked:4, needs_triage:0, inventory_only:22}
aggregate_counts_after={sample_count:29, solved:4, blocked:4, needs_triage:0, inventory_only:21}
updated_samples=[cpp2_32f1713e]
unrelated_samples_modified=false
executed_sample=false
ran_runtime_tools=false
ran_debugger=false
ran_hook=false
ran_emulator=false
ran_probe=false
ran_bruteforce=false
ran_dictionary_search=false
candidate_search_performed=false
uploaded_binary=false
binary_content_recorded=false
full_stdout_recorded=false
memory_dump_recorded=false
full_disassembly_recorded=false
full_decompilation_recorded=false
next_recommended_mainline=training_dataset
next_recommended_action=<advance to next inventory_only sample or refresh queue summary>
generated_at=<timestamp>
```

### Phase D — artifact_index registration

Register the sync artifact:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_training_status_sync"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_training_status_sync"]
artifact_index.artifact_refs["local_reverse_cpp2_32f1713e_training_status_sync"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_training_status_sync
path=project_state\\local_reverse_cpp2_32f1713e_training_status_sync.json
freshness=current
source_run=round_20260607_cpp2_32f1713e_training_status_sync_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
candidate=KEEP_DREAM
training_status=solved
known_candidate=KEEP_DREAM
source_runtime_validation_artifact=project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
source_runtime_validation_status=VALIDATED
aggregate_counts_after={sample_count:29, solved:4, blocked:4, needs_triage:0, inventory_only:21}
```

Optional low-token pointers:

```text
current_state.local_reverse_recent_solved.sample_id=cpp2_32f1713e
current_state.local_reverse_recent_solved.known_candidate=KEEP_DREAM
current_state.local_reverse_recent_solved.validation_artifact=project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
current_state.local_reverse_training_summary.solved=4
current_state.local_reverse_training_summary.inventory_only=21
task_packet.local_reverse_recent_solved.sample_id=cpp2_32f1713e
task_packet.local_reverse_recent_solved.known_candidate=KEEP_DREAM
task_packet.local_reverse_training_summary.solved=4
task_packet.local_reverse_training_summary.inventory_only=21
```

Do not change `task_packet.task`.

### Phase E — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_training_status_sync_v1",
  "round_id": "round_20260607_cpp2_32f1713e_training_status_sync_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_training_status_sync_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
successful one-sample sync -> status=SUCCESS, acceptance_recommendation=ACCEPTED
state drift before sync -> status=BLOCKED, acceptance_recommendation=BLOCKED
forbidden action or inconsistent counts -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
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

`pytest_result.txt` must include:

```text
decision_id=decision_20260607_cpp2_32f1713e_training_status_sync_v1
report_id=report_20260607_cpp2_32f1713e_training_status_sync_v1
round_id=round_20260607_cpp2_32f1713e_training_status_sync_v1
```

Content assertions to record:

```text
1. source runtime validation artifact is current/VALIDATED/KEEP_DREAM.
2. source targeted_static_solving artifact is current/SUCCESS/KEEP_DREAM.
3. pre-sync cpp2_32f1713e status was inventory_only/known_candidate="".
4. post-sync cpp2_32f1713e status is solved/known_candidate=KEEP_DREAM.
5. project_state/local_reverse_training_status.json aggregate counts are solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29.
6. training_materials/local_reverse/status_overlay.json aggregate counts are solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29.
7. evidence sources include runtime validation artifact.
8. cpp2_2f64e68d solved facts remain unchanged.
9. unrelated sample statuses remain unchanged.
10. no sample executable was run.
11. no runtime tools/debugger/hook/emulator/probe were run.
12. no brute force/dictionary/search/fuzzing was run.
13. no binary was uploaded, copied, embedded, or committed.
14. sync artifact exists.
15. artifact_index registers local_reverse_cpp2_32f1713e_training_status_sync as current.
16. pytest_result uses this decision_id/report_id/round_id.
17. final lint-report ran after report write.
18. git diff --name-status only contains allowed files.
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage.

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED` if:

```text
1. source runtime validation artifact is current and VALIDATED;
2. source static solving artifact is current and SUCCESS;
3. cpp2_32f1713e is updated to solved with known_candidate=KEEP_DREAM;
4. aggregate counts are solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29;
5. status_overlay matches training_status for this sample and counts;
6. sync artifact is produced and registered current;
7. no sample execution or forbidden runtime/debugger/search action occurred;
8. tests/lint/report metadata align with this decision/report/round.
```

Stop with `BLOCKED` if:

```text
1. source runtime validation artifact is missing/stale/not VALIDATED;
2. source static solving artifact is missing/stale/not SUCCESS;
3. pre-sync status has already changed and would cause double-counting;
4. required status files are missing or malformed.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. any forbidden action occurs;
2. unrelated sample statuses are modified;
3. aggregate counts are inconsistent;
4. artifact_index/report/pytest_result do not align with this decision.
```
