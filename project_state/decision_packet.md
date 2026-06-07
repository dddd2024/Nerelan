```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1",
  "round_id": "round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1",
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

本轮主线是 **training_dataset**，任务是修复上一轮 queue refresh 的 path、artifact key、provenance、pytest 检查对象和低 token 字段不一致问题。

上一轮 queue refresh 已部分完成：`task_packet.json` 与 `current_state.json` 中的核心训练摘要、recent_solved、next_queue_hint 已大体更新为 `cpp2_32f1713e / KEEP_DREAM` 和 `cpp2_883e67b9`。但上一轮实际 artifact 命名为：

```text
project_state/local_reverse_cpp2_32f1713e_queue_refresh.json
local_reverse_cpp2_32f1713e_queue_refresh
```

这与上一轮 decision 要求的规范名不一致。本轮必须修复为：

```text
project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json
local_reverse_queue_refresh_after_cpp2_32f1713e
```

本轮只做 metadata rework，不推进新样本求解，不运行样本，不做 IDA/Ghidra/static extraction/runtime validation/debugger/hook/probe。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory；上一轮已部分刷新，但仍存在低 token 字段偏差。

Accepted source evidence:

```text
project_state/local_reverse_cpp2_32f1713e_training_status_sync.json:
  decision_id=decision_20260607_cpp2_32f1713e_training_status_sync_v1
  round_id=round_20260607_cpp2_32f1713e_training_status_sync_v1
  sample_id=cpp2_32f1713e
  candidate=KEEP_DREAM
  source_runtime_validation_status=VALIDATED
  post_sync_status=solved
  post_sync_known_candidate=KEEP_DREAM
  aggregate_counts_after={sample_count:29, solved:4, blocked:4, needs_triage:0, inventory_only:21}
  unrelated_samples_modified=false
  executed_sample=false
  ran_runtime_tools=false
```

Current training files remain correct and must not be modified in this round:

```text
project_state/local_reverse_training_status.json:
  sample_count=29
  status_summary.solved=4
  status_summary.blocked=4
  status_summary.needs_triage=0
  status_summary.inventory_only=21
  cpp2_32f1713e.training_status=solved
  cpp2_32f1713e.known_candidate=KEEP_DREAM

training_materials/local_reverse/status_overlay.json:
  sample_count=29
  status_summary.solved=4
  status_summary.blocked=4
  status_summary.needs_triage=0
  status_summary.inventory_only=21
  cpp2_32f1713e.training_status=solved
  cpp2_32f1713e.known_candidate=KEEP_DREAM
```

上一轮 nonconforming artifact may be used only as legacy source:

```text
project_state/local_reverse_cpp2_32f1713e_queue_refresh.json:
  decision_id=decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1
  round_id=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1
  solved_sample_id=cpp2_32f1713e
  solved_candidate=KEEP_DREAM
  next_queue_hint.sample_id=cpp2_883e67b9
  aggregate_counts_final={sample_count:29, solved:4, blocked:4, needs_triage:0, inventory_only:21}
  executed_sample=false
  ran_runtime_tools=false
```

Current mismatches to fix:

```text
1. Required artifact path/key missing:
   project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json
   local_reverse_queue_refresh_after_cpp2_32f1713e

2. artifact_index currently registers nonconforming key:
   local_reverse_cpp2_32f1713e_queue_refresh

3. artifact_index.latest_artifacts_v2 source_run for the nonconforming key is:
   round_20260607_cpp2_32f1713e_queue_refresh_v1
   but current decision provenance must use this rework round:
   round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1

4. pytest_result checks nonconforming key:
   local_reverse_cpp2_32f1713e_queue_refresh
   instead of required key:
   local_reverse_queue_refresh_after_cpp2_32f1713e

5. task_packet/current_state recent_solved.accepted_round points to runtime validation round, but this low-token state should point to accepted training sync round:
   round_20260607_cpp2_32f1713e_training_status_sync_v1

6. task_packet local_reverse_next_suggested_task still mentions cpp2_32f1713e static_triage and must mention cpp2_883e67b9.

7. next_queue_hint actions are incomplete; allowed_actions must include static_triage and bounded_static_extraction_readiness, and forbidden_actions must include runtime_probe, brute_force, debugger, hook, emulator, upload_binary.
```

Next queue sample remains:

```text
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
training_status=inventory_only
known_candidate=""
blocked_reason=""
```

negative_results remain unchanged and mainly concern old `samplereverse` directions. This round must not run blind search, expand budgets, commit full solve_reports, or use stale artifacts as current evidence.

Skill profile must remain `reverse-agent-iteration@v2`, which is active in `.codex-skills/registry.json`.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run any sample executable.
3. Do not run runtime validation, console validation, winpty, subprocess execution, debugger, hook, emulator, breakpoint probe, or instrumentation.
4. Do not run IDA/Ghidra/static extraction for cpp2_883e67b9 or any other sample.
5. Do not solve or triage cpp2_883e67b9 in this round.
6. Do not generate candidates.
7. Do not run brute force, dictionary search, fuzzing, candidate search, or broad input enumeration.
8. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
9. Do not upload, copy into repo, base64-embed, or commit any sample binary.
10. Do not modify .codex-skills.
11. Do not modify project_state/local_reverse_training_status.json.
12. Do not modify training_materials/local_reverse/status_overlay.json.
13. Do not change accepted solved facts for cpp2_2f64e68d / 10013 or cpp2_32f1713e / KEEP_DREAM.
14. Do not leave task_packet/current_state next_queue_hint pointing to cpp2_32f1713e.
15. Do not make the nonconforming key local_reverse_cpp2_32f1713e_queue_refresh the only current queue refresh artifact for this rework.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current local_reverse_training_status.json and status_overlay.json only for consistency checks.
3. Read current cpp2_32f1713e training_status_sync artifact.
4. Read previous nonconforming local_reverse_cpp2_32f1713e_queue_refresh artifact as legacy source.
5. Update low-token local_reverse fields in task_packet.json and current_state.json to correct accepted_round, next_suggested_task and action lists.
6. Generate project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json.
7. Register local_reverse_queue_refresh_after_cpp2_32f1713e in artifact_index.
8. Optionally leave old local_reverse_cpp2_32f1713e_queue_refresh as legacy/previous artifact, but it must not replace the required key.
9. Write codex_execution_report.md and pytest_result.txt.
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
project_state/local_reverse_cpp2_32f1713e_training_status_sync.json
project_state/local_reverse_cpp2_32f1713e_queue_refresh.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Do not read by default:

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse tree or any sample binary
```

---

## 5. Required Audit

Codex report must answer:

```text
1. Did it confirm decision_packet is the sole execution authority?
2. Did it confirm mainline=training_dataset?
3. Did it confirm this is queue refresh rework, not solving or validation?
4. Did it confirm task_packet is advisory?
5. Did it confirm source training status sync artifact is current/accepted evidence for cpp2_32f1713e solved?
6. Did it confirm training_status and status_overlay remain solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29?
7. Did it confirm cpp2_32f1713e remains solved / KEEP_DREAM?
8. Did it confirm next queue sample remains cpp2_883e67b9?
9. Did it create project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json?
10. Did it register local_reverse_queue_refresh_after_cpp2_32f1713e in latest_artifacts/latest_artifacts_v2/artifact_refs?
11. Did latest_artifacts_v2 for local_reverse_queue_refresh_after_cpp2_32f1713e use source_run=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1?
12. Did it treat project_state/local_reverse_cpp2_32f1713e_queue_refresh.json only as legacy source?
13. Did it fix task_packet/current_state recent_solved.accepted_round to round_20260607_cpp2_32f1713e_training_status_sync_v1?
14. Did it fix task_packet/current_state next_suggested_task to mention cpp2_883e67b9 rather than cpp2_32f1713e?
15. Did it set next_queue_hint.allowed_actions to include static_triage and bounded_static_extraction_readiness?
16. Did it set next_queue_hint.forbidden_actions to include runtime_probe, brute_force, debugger, hook, emulator, upload_binary?
17. Did task_packet.task remain advisory and not become execution authority?
18. Did it avoid modifying training_status/status_overlay?
19. Did it avoid sample execution and runtime tools?
20. Did it avoid IDA/Ghidra/static extraction/debugger/hook/emulator/probe?
21. Did it avoid brute force/dictionary/search/fuzzing?
22. Did it avoid binary upload/copy/embed/full dumps?
23. Did it explain negative_results unchanged or non-use?
24. Did it run required py_compile/pytest/lint/status/git checks?
25. Did pytest_result.txt use this rework decision_id/report_id/round_id?
26. Did pytest_result check local_reverse_queue_refresh_after_cpp2_32f1713e, not local_reverse_cpp2_32f1713e_queue_refresh?
27. Did final lint-report run after report write?
28. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded metadata rework only.

### Phase A — preflight

Use `.venv\Scripts\python` for repository Python commands.

Verify accepted sync artifact:

```text
project_state/local_reverse_cpp2_32f1713e_training_status_sync.json:
  sample_id == cpp2_32f1713e
  candidate == KEEP_DREAM
  source_runtime_validation_status == VALIDATED
  post_sync_status == solved
  post_sync_known_candidate == KEEP_DREAM
  aggregate_counts_after.sample_count == 29
  aggregate_counts_after.solved == 4
  aggregate_counts_after.blocked == 4
  aggregate_counts_after.needs_triage == 0
  aggregate_counts_after.inventory_only == 21
  unrelated_samples_modified == false
  executed_sample == false
  ran_runtime_tools == false
```

Verify current training files without modifying them:

```text
project_state/local_reverse_training_status.json:
  sample_count == 29
  status_summary.solved == 4
  status_summary.inventory_only == 21
  cpp2_32f1713e.training_status == solved
  cpp2_32f1713e.known_candidate == KEEP_DREAM
  cpp2_883e67b9.training_status == inventory_only
  cpp2_883e67b9.known_candidate == ""

training_materials/local_reverse/status_overlay.json:
  sample_count == 29
  status_summary.solved == 4
  status_summary.inventory_only == 21
  cpp2_32f1713e.training_status == solved
  cpp2_32f1713e.known_candidate == KEEP_DREAM
  cpp2_883e67b9.training_status == inventory_only
  cpp2_883e67b9.known_candidate == ""
```

### Phase B — fix low-token state

Update only low-token local_reverse fields in `project_state/task_packet.json` and `project_state/current_state.json`.

Required final values:

```text
local_reverse_recent_solved.sample_id=cpp2_32f1713e
local_reverse_recent_solved.known_candidate=KEEP_DREAM
local_reverse_recent_solved.validation_artifact=project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
local_reverse_recent_solved.accepted_round=round_20260607_cpp2_32f1713e_training_status_sync_v1

local_reverse_training_summary.sample_count=29
local_reverse_training_summary.solved=4
local_reverse_training_summary.blocked=4
local_reverse_training_summary.needs_triage=0
local_reverse_training_summary.inventory_only=21

local_reverse_current_artifact=project_state\\local_reverse_queue_refresh_after_cpp2_32f1713e.json
local_reverse_current_artifact_keys includes:
  local_reverse_cpp2_32f1713e_training_status_sync
  local_reverse_queue_refresh_after_cpp2_32f1713e

local_reverse_next_queue_hint.sample_id=cpp2_883e67b9
local_reverse_next_queue_hint.relative_path=逆向课程2024春02/CPP2.exe
local_reverse_next_queue_hint.proposed_next_mainline=tool_integration
local_reverse_next_queue_hint.allowed_actions=[static_triage, bounded_static_extraction_readiness]
local_reverse_next_queue_hint.forbidden_actions=[runtime_probe, brute_force, debugger, hook, emulator, upload_binary]

local_reverse_next_suggested_task=Advisory next queue hint only: cpp2_883e67b9 needs a future bounded static triage/readiness decision; do not execute from task_packet alone.
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

Do not rewrite unrelated samplereverse/frontier fields unless existing project_state tooling requires serialization normalization.

### Phase C — generate required queue refresh artifact

Create:

```text
project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json
```

Required top-level fields:

```text
schema_version=1
mainline=training_dataset
round_id=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1
decision_id=decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1
source_training_status_sync_artifact=project_state\\local_reverse_cpp2_32f1713e_training_status_sync.json
source_training_status_sync_status=ACCEPTED
legacy_source_artifact=project_state\\local_reverse_cpp2_32f1713e_queue_refresh.json
legacy_source_key=local_reverse_cpp2_32f1713e_queue_refresh
rework_reason=path_key_provenance_and_low_token_field_alignment
sample_count=29
status_summary={solved:4, blocked:4, needs_triage:0, inventory_only:21}
recent_solved={sample_id:cpp2_32f1713e, known_candidate:KEEP_DREAM, validation_artifact:project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json, accepted_round:round_20260607_cpp2_32f1713e_training_status_sync_v1}
next_queue_hint={sample_id:cpp2_883e67b9, relative_path:逆向课程2024春02/CPP2.exe, training_status:inventory_only, known_candidate:"", blocked_reason:"", proposed_next_mainline:tool_integration, allowed_actions:[static_triage,bounded_static_extraction_readiness], forbidden_actions:[runtime_probe,brute_force,debugger,hook,emulator,upload_binary]}
task_packet_updated=true
current_state_updated=true
training_status_modified=false
status_overlay_modified=false
executed_sample=false
ran_runtime_tools=false
ran_ida=false
ran_ghidra=false
ran_static_extraction=false
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
next_recommended_mainline=tool_integration
next_recommended_action=Generate a bounded static triage/readiness decision for cpp2_883e67b9.
generated_at=<timestamp>
```

### Phase D — artifact_index registration

Register the required key:

```text
artifact_index.latest_artifacts["local_reverse_queue_refresh_after_cpp2_32f1713e"]
artifact_index.latest_artifacts_v2["local_reverse_queue_refresh_after_cpp2_32f1713e"]
artifact_index.artifact_refs["local_reverse_queue_refresh_after_cpp2_32f1713e"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_queue_refresh
after_sample_id=cpp2_32f1713e
path=project_state\\local_reverse_queue_refresh_after_cpp2_32f1713e.json
freshness=current
source_run=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
recent_solved_sample_id=cpp2_32f1713e
next_queue_sample_id=cpp2_883e67b9
next_queue_relative_path=逆向课程2024春02/CPP2.exe
training_status_modified=false
status_overlay_modified=false
legacy_source_artifact=project_state\\local_reverse_cpp2_32f1713e_queue_refresh.json
rework_of=local_reverse_cpp2_32f1713e_queue_refresh
```

The old `local_reverse_cpp2_32f1713e_queue_refresh` key may remain as legacy/previous, but it must not be the only current queue refresh artifact for this rework.

### Phase E — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1",
  "round_id": "round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1",
  "based_on_decision_id": "decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
successful metadata rework -> status=SUCCESS, acceptance_recommendation=ACCEPTED
state drift requiring human decision -> status=BLOCKED, acceptance_recommendation=BLOCKED
forbidden action or inconsistent metadata -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
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
decision_id=decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1
report_id=report_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1
round_id=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1
```

Content assertions to record:

```text
1. source training status sync artifact is current/accepted evidence for cpp2_32f1713e solved.
2. training_status summary remains solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29.
3. status_overlay summary remains solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29.
4. task_packet local_reverse_training_summary is solved=4/inventory_only=21.
5. current_state local_reverse_training_summary is solved=4/inventory_only=21.
6. task_packet local_reverse_recent_solved is cpp2_32f1713e / KEEP_DREAM with accepted_round=round_20260607_cpp2_32f1713e_training_status_sync_v1.
7. current_state local_reverse_recent_solved is cpp2_32f1713e / KEEP_DREAM with accepted_round=round_20260607_cpp2_32f1713e_training_status_sync_v1.
8. task_packet next_queue_hint is cpp2_883e67b9 with complete allowed/forbidden actions.
9. current_state next_queue_hint is cpp2_883e67b9 with complete allowed/forbidden actions.
10. task_packet next_suggested_task mentions cpp2_883e67b9, not cpp2_32f1713e.
11. current_state next_suggested_task or equivalent local_reverse hint mentions cpp2_883e67b9, not cpp2_32f1713e.
12. required queue refresh artifact project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json exists.
13. artifact_index registers local_reverse_queue_refresh_after_cpp2_32f1713e as current.
14. artifact_index.latest_artifacts_v2[local_reverse_queue_refresh_after_cpp2_32f1713e].source_run equals round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_rework_v1.
15. pytest_result checks local_reverse_queue_refresh_after_cpp2_32f1713e, not local_reverse_cpp2_32f1713e_queue_refresh.
16. training_status/status_overlay were not modified in this round.
17. no sample executable was run.
18. no runtime tools/debugger/hook/emulator/probe were run.
19. no IDA/Ghidra/static extraction was run.
20. no brute force/dictionary/search/fuzzing was run.
21. no binary was uploaded, copied, embedded, or committed.
22. pytest_result uses this rework decision_id/report_id/round_id.
23. final lint-report ran after report write.
24. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED` if:

```text
1. required artifact path exists;
2. artifact_index registers required key as current;
3. latest_artifacts_v2 required key source_run matches this rework round;
4. task_packet/current_state accepted_round points to training_status_sync round;
5. task_packet/current_state next_suggested_task no longer points to cpp2_32f1713e;
6. next_queue_hint action lists are complete;
7. pytest_result checks required key/path;
8. training_status/status_overlay are not modified;
9. no sample execution or forbidden tool action occurred;
10. tests/lint/report metadata align with this rework decision/report/round.
```

Stop with `BLOCKED` if:

```text
1. training_status/status_overlay disagree on aggregate counts;
2. source training sync artifact is missing/stale;
3. cpp2_32f1713e is not solved/KEEP_DREAM in current training files;
4. no deterministic next inventory_only sample can be identified.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. any forbidden execution/tool action occurs;
2. training_status/status_overlay are modified without explicit inconsistency justification;
3. task_packet/current_state still point next_queue_hint to cpp2_32f1713e after refresh;
4. artifact_index/report/pytest_result do not align with this rework decision.
```
