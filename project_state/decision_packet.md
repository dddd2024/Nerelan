```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1",
  "round_id": "round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1",
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

本轮主线是 **training_dataset**，任务是完成 `cpp2_32f1713e / KEEP_DREAM` 解题同步后的 **队列与低 token 状态刷新**。

上一轮已 ACCEPTED：`cpp2_32f1713e` 已在训练状态中标记为 solved，`known_candidate=KEEP_DREAM`，aggregate counts 已从 `solved=3 / inventory_only=22` 更新为 `solved=4 / inventory_only=21`。

本轮目标：

```text
1. 修正 project_state/task_packet.json 与 project_state/current_state.json 中仍然残留的旧训练摘要、recent_solved、next_queue_hint。
2. 生成队列刷新 artifact。
3. 让下一轮 Codex 能从正确的 next inventory_only 样本继续，而不是重复 cpp2_32f1713e。
```

必须产出：

```text
project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json
```

本轮只做状态刷新和队列推进，不运行样本、不分析样本、不做 IDA/Ghidra/static extraction/runtime validation。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，且当前已知它包含旧摘要，不能直接作为事实源使用。

已接受的训练状态同步证据：

```text
project_state/local_reverse_cpp2_32f1713e_training_status_sync.json:
  mainline=training_dataset
  decision_id=decision_20260607_cpp2_32f1713e_training_status_sync_v1
  round_id=round_20260607_cpp2_32f1713e_training_status_sync_v1
  sample_id=cpp2_32f1713e
  candidate=KEEP_DREAM
  source_runtime_validation_status=VALIDATED
  pre_sync_status=inventory_only
  post_sync_status=solved
  pre_sync_known_candidate=""
  post_sync_known_candidate=KEEP_DREAM
  aggregate_counts_before={sample_count:29, solved:3, blocked:4, needs_triage:0, inventory_only:22}
  aggregate_counts_after={sample_count:29, solved:4, blocked:4, needs_triage:0, inventory_only:21}
  updated_samples=[cpp2_32f1713e]
  unrelated_samples_modified=false
  executed_sample=false
  ran_runtime_tools=false
```

Current training status file:

```text
project_state/local_reverse_training_status.json:
  sample_count=29
  status_summary.solved=4
  status_summary.solved_count=4
  status_summary.blocked=4
  status_summary.blocked_count=4
  status_summary.needs_triage=0
  status_summary.inventory_only=21
  status_summary.inventory_only_count=21
  cpp2_32f1713e.training_status=solved
  cpp2_32f1713e.known_candidate=KEEP_DREAM
  cpp2_32f1713e.classification=oracle_backed_runtime_validated
```

Current status overlay:

```text
training_materials/local_reverse/status_overlay.json:
  sample_count=29
  status_summary.solved=4
  status_summary.blocked=4
  status_summary.needs_triage=0
  status_summary.inventory_only=21
  cpp2_32f1713e.training_status=solved
  cpp2_32f1713e.known_candidate=KEEP_DREAM
  cpp2_32f1713e.solved_by=bounded_runtime_validation
```

Observed stale low-token state that must be refreshed:

```text
project_state/task_packet.json currently still reports:
  local_reverse_recent_solved.sample_id=cpp2_2f64e68d
  local_reverse_recent_solved.known_candidate=10013
  local_reverse_training_summary.solved=3
  local_reverse_training_summary.inventory_only=22
  local_reverse_next_queue_hint.sample_id=cpp2_32f1713e
  local_reverse_next_queue_hint.allowed_actions=[static_triage]

project_state/current_state.json still contains older samplereverse/frontier fields and local_reverse summaries that do not reflect cpp2_32f1713e solved as the most recent accepted sample.
```

Next queue candidate inferred from current ordered training status / status overlay after `cpp2_32f1713e` is:

```text
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
training_status=inventory_only
known_candidate=""
blocked_reason=""
category=cpp
allowed next action for a future decision=static_triage / bounded static extraction readiness, not execution in this round
forbidden in this round=runtime_probe, brute force, upload_binary, debugger, hook, emulator, sample execution
```

negative_results mainly concerns old `samplereverse` directions. This round must not use stale artifacts as current evidence, must not commit full solve_reports, and must not repeat blind search or budget expansion.

Skill profile must remain `reverse-agent-iteration@v2`, which is active in `.codex-skills/registry.json`.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run any sample executable.
3. Do not run runtime validation, winpty, console validation, subprocess execution, debugger, hook, emulator, breakpoint probe, or instrumentation.
4. Do not run IDA/Ghidra/static extraction for cpp2_883e67b9 in this round.
5. Do not solve or triage cpp2_883e67b9 in this round.
6. Do not generate candidates.
7. Do not run brute force, dictionary search, fuzzing, candidate search, or broad input enumeration.
8. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
9. Do not upload, copy into repo, base64-embed, or commit any sample binary.
10. Do not modify .codex-skills.
11. Do not change accepted solved facts for cpp2_2f64e68d / 10013 or cpp2_32f1713e / KEEP_DREAM.
12. Do not modify local_reverse_training_status.json or status_overlay.json unless only correcting a direct inconsistency discovered against the accepted sync artifact; if such inconsistency exists, stop as BLOCKED instead of silently rewriting.
13. Do not change task_packet.task semantics except low-token local_reverse status hints if needed.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current local_reverse_training_status.json and status_overlay.json.
3. Read current cpp2_32f1713e training_status_sync artifact.
4. Read artifact_index and register a queue refresh artifact.
5. Update low-token local_reverse fields in task_packet.json and current_state.json to reflect solved=4 / inventory_only=21 and next_queue_hint=cpp2_883e67b9.
6. Generate project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json.
7. Write codex_execution_report.md and pytest_result.txt.
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
reverse_agent/project_state.py
tests/test_project_state.py
```

May inspect if directly needed and bounded:

```text
project_state/local_reverse_inventory.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_training_status_summary_sync.json
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
3. Did it confirm this is queue/status refresh, not solving or validation?
4. Did it confirm task_packet is advisory and stale before this refresh?
5. Did it confirm cpp2_32f1713e training_status_sync artifact is current/accepted evidence?
6. Did it confirm training_status summary is solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29?
7. Did it confirm status_overlay has the same counts?
8. Did it confirm cpp2_32f1713e is solved / KEEP_DREAM?
9. Did it confirm cpp2_2f64e68d / 10013 solved facts remain unchanged?
10. Did it identify next inventory_only sample as cpp2_883e67b9 from ordered training/status overlay data?
11. Did it update task_packet low-token local_reverse summary to solved=4 / inventory_only=21?
12. Did it update task_packet recent_solved to cpp2_32f1713e / KEEP_DREAM?
13. Did it update task_packet next_queue_hint to cpp2_883e67b9 with future allowed_actions limited to static_triage / bounded static extraction readiness?
14. Did it update current_state low-token local_reverse summary/recent_solved/next_queue_hint consistently?
15. Did it avoid changing task_packet.task as the execution authority?
16. Did it generate project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json?
17. Did it register the queue refresh artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
18. Did it avoid modifying training_status/status_overlay except not needed?
19. Did it avoid sample execution and runtime tools?
20. Did it avoid IDA/Ghidra/static extraction/debugger/hook/emulator/probe?
21. Did it avoid brute force/dictionary/search/fuzzing?
22. Did it avoid binary upload/copy/embed/full dumps?
23. Did it explain negative_results unchanged or non-use?
24. Did it run required py_compile/pytest/lint/status/git checks?
25. Did pytest_result.txt use this decision_id/report_id/round_id?
26. Did final lint-report run after report write?
27. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded low-token state refresh only.

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

Verify current training files:

```text
project_state/local_reverse_training_status.json:
  sample_count == 29
  status_summary.solved == 4
  status_summary.inventory_only == 21
  cpp2_32f1713e.training_status == solved
  cpp2_32f1713e.known_candidate == KEEP_DREAM

training_materials/local_reverse/status_overlay.json:
  sample_count == 29
  status_summary.solved == 4
  status_summary.inventory_only == 21
  cpp2_32f1713e.training_status == solved
  cpp2_32f1713e.known_candidate == KEEP_DREAM
```

Infer next queue sample from the first `inventory_only` sample after current solved block in current ordered training/status overlay data. Expected:

```text
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
category=cpp
training_status=inventory_only
known_candidate=""
blocked_reason=""
```

If next sample differs due to accepted intervening changes, use the current ordered data and record the reason in the artifact/report.

### Phase B — update low-token state

Update only low-token local_reverse fields in `project_state/task_packet.json` and `project_state/current_state.json`.

Required target values:

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
local_reverse_current_artifact_keys includes local_reverse_cpp2_32f1713e_training_status_sync and local_reverse_queue_refresh_after_cpp2_32f1713e

local_reverse_next_queue_hint.sample_id=cpp2_883e67b9
local_reverse_next_queue_hint.relative_path=逆向课程2024春02/CPP2.exe
local_reverse_next_queue_hint.proposed_next_mainline=training_dataset or tool_integration
local_reverse_next_queue_hint.allowed_actions=[static_triage, bounded_static_extraction_readiness]
local_reverse_next_queue_hint.forbidden_actions=[runtime_probe, brute_force, debugger, hook, emulator, upload_binary]

local_reverse_next_suggested_task=Advisory next queue hint only: cpp2_883e67b9 needs a future bounded static triage/readiness decision; do not execute from task_packet alone.
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

Do not rewrite unrelated samplereverse/frontier fields unless existing project_state tooling requires serialization normalization.

### Phase C — generate queue refresh artifact

Generate:

```text
project_state/local_reverse_queue_refresh_after_cpp2_32f1713e.json
```

Required top-level fields:

```text
schema_version=1
mainline=training_dataset
round_id=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1
decision_id=decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1
source_training_status_sync_artifact=project_state\\local_reverse_cpp2_32f1713e_training_status_sync.json
source_training_status_sync_status=ACCEPTED
sample_count=29
status_summary={solved:4, blocked:4, needs_triage:0, inventory_only:21}
recent_solved={sample_id:cpp2_32f1713e, known_candidate:KEEP_DREAM, validation_artifact:project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json, accepted_round:round_20260607_cpp2_32f1713e_training_status_sync_v1}
next_queue_hint={sample_id:cpp2_883e67b9, relative_path:逆向课程2024春02/CPP2.exe, training_status:inventory_only, known_candidate:"", blocked_reason:"", proposed_next_mainline:training_dataset, allowed_actions:[static_triage,bounded_static_extraction_readiness], forbidden_actions:[runtime_probe,brute_force,debugger,hook,emulator,upload_binary]}
task_packet_updated=true|false
current_state_updated=true|false
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
next_recommended_mainline=training_dataset
next_recommended_action=Generate a bounded static triage/readiness decision for cpp2_883e67b9.
generated_at=<timestamp>
```

### Phase D — artifact_index registration

Register:

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
source_run=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1
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
```

### Phase E — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1",
  "round_id": "round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1",
  "based_on_decision_id": "decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
successful low-token state refresh -> status=SUCCESS, acceptance_recommendation=ACCEPTED
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
decision_id=decision_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1
report_id=report_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1
round_id=round_20260607_local_reverse_queue_refresh_after_cpp2_32f1713e_v1
```

Content assertions to record:

```text
1. source training status sync artifact is current/accepted evidence for cpp2_32f1713e solved.
2. training_status summary is solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29.
3. status_overlay summary matches solved=4, blocked=4, needs_triage=0, inventory_only=21, sample_count=29.
4. task_packet local_reverse_training_summary is updated to solved=4/inventory_only=21.
5. current_state local_reverse_training_summary is updated to solved=4/inventory_only=21.
6. task_packet local_reverse_recent_solved is cpp2_32f1713e / KEEP_DREAM.
7. current_state local_reverse_recent_solved is cpp2_32f1713e / KEEP_DREAM.
8. task_packet next_queue_hint is cpp2_883e67b9 unless current ordered data justifies a different sample.
9. current_state next_queue_hint is cpp2_883e67b9 unless current ordered data justifies a different sample.
10. task_packet.task remains advisory and does not become execution authority.
11. queue refresh artifact exists.
12. artifact_index registers local_reverse_queue_refresh_after_cpp2_32f1713e as current.
13. training_status/status_overlay were not modified in this round.
14. no sample executable was run.
15. no runtime tools/debugger/hook/emulator/probe were run.
16. no IDA/Ghidra/static extraction was run.
17. no brute force/dictionary/search/fuzzing was run.
18. no binary was uploaded, copied, embedded, or committed.
19. pytest_result uses this decision_id/report_id/round_id.
20. final lint-report ran after report write.
21. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED` if:

```text
1. accepted cpp2_32f1713e training sync evidence is current;
2. task_packet and current_state low-token local_reverse summaries reflect solved=4/inventory_only=21;
3. recent_solved points to cpp2_32f1713e / KEEP_DREAM;
4. next_queue_hint points to the next inventory_only sample, expected cpp2_883e67b9;
5. queue refresh artifact is produced and registered current;
6. no training_status/status_overlay changes occurred in this round;
7. no sample execution or forbidden tool action occurred;
8. tests/lint/report metadata align with this decision/report/round.
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
4. artifact_index/report/pytest_result do not align with this decision.
```
