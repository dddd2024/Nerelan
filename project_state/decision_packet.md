```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1",
  "round_id": "round_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1",
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

本轮主线是 **reverse_solving**，范围限定为 `cpp2_32f1713e` 的 **bounded runtime validation**。

目标：对上一轮静态候选 `KEEP_DREAM` 做最小有界运行验证，确认它是否触发样本成功输出；同时使用一个同长度负控输入确认 oracle 能区分失败路径。

必须产出：

```text
project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
```

本轮只做候选验证，不做新求解、不做训练状态同步。即使 `KEEP_DREAM` 验证成功，也不得在本轮修改：

```text
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
```

若验证成功，下一轮再单独生成 training status sync 决策。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 rework 审计结论为 **ACCEPTED_WITH_LIMITATIONS**：`targeted_static_solving` 的 path/key/schema/provenance 已修复，但候选仍未 runtime validation。

Current normalized static solving artifact:

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json:
  decision_id=decision_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
  round_id=round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
  sample_id=cpp2_32f1713e
  static_solving_status=SUCCESS
  unvalidated_candidate_hypothesis.candidate=KEEP_DREAM
  unvalidated_candidate_hypothesis.validation_status=unvalidated
  unvalidated_candidate_hypothesis.requires_future_runtime_validation=true
  candidate_generated=true
  candidate_validation_attempted=false
  candidate_validated=false
  candidate_acceptance_status=unvalidated
  executed_sample=false
  ran_runtime_tools=false
  ran_debugger=false
  ran_bruteforce=false
  training_status_modified=false
```

`artifact_index.latest_artifacts_v2` registers the normalized static solving artifact as current:

```text
local_reverse_cpp2_32f1713e_targeted_static_solving:
  kind=local_reverse_targeted_static_solving
  path=project_state\local_reverse_cpp2_32f1713e_targeted_static_solving.json
  freshness=current
  source_run=round_20260607_cpp2_32f1713e_targeted_static_solving_rework_v1
  sample_id=cpp2_32f1713e
  static_solving_status=SUCCESS
  candidate_generated=true
  candidate_validated=false
  candidate_acceptance_status=unvalidated
  legacy_source_artifact=project_state\local_reverse_cpp2_32f1713e_targeted_static_solve.json
```

Current readiness artifact:

```text
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json:
  readiness_status=READY
  ready_for_static_extraction=true
  command_scoped_root=E:\reverse
  resolved_sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
  sample_id=cpp2_32f1713e
  size_bytes=196686
  sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
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

Known oracle strings from static artifacts:

```text
success signal: Congratulations! You are right!
failure signals: Sorry, you are wrong! / Sorry,you are wrong!
prompt signal: Plase give me your answer:
```

negative_results mainly concerns old `samplereverse` directions. Do not repeat blind search, budget expansion, stale artifact assumptions, or full solve_reports commits. For local `cpp2_32f1713e`, preserve the queue constraints: no brute force, no upload_binary, no debugger/hook/probe. This round explicitly permits only bounded sample execution for candidate/control runtime validation.

Existing runtime/tooling context from project_state includes prior console/winpty backend work for local reverse samples. Use existing validation interfaces only. Do not create duplicate runtime, debugger, emulator, IDA, Ghidra, or static extraction interfaces.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not generate a new candidate.
3. Do not run brute force, dictionary search, candidate search, fuzzing, or broad input enumeration.
4. Do not attach debugger, hook, emulator, instrumentation probe, breakpoint probe, or dynamic trace collector.
5. Do not use IDA/Ghidra for new analysis in this runtime validation round.
6. Do not create duplicate console/runtime/winpty/debugger/static extraction interfaces.
7. Do not scan full E:\reverse tree, full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full project_state/rounds.
8. Do not upload, copy into repo, base64-embed, or commit the sample binary.
9. Do not store raw binary bytes, memory dumps, screenshots, full stdout logs beyond bounded snippets, full disassembly, or full decompilation.
10. Do not modify project_state/local_reverse_training_status.json.
11. Do not modify training_materials/local_reverse/status_overlay.json.
12. Do not alter cpp2_2f64e68d / 10013 solved facts.
13. Do not mark cpp2_32f1713e solved in this round, even if runtime validation succeeds.
14. Do not write known_candidate=KEEP_DREAM to training status in this round.
15. Do not report validation success unless candidate success signal and negative control rejection are both established, or explicitly explain a weaker oracle verdict.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read current readiness artifact for cpp2_32f1713e.
3. Read current targeted_static_solving artifact for cpp2_32f1713e.
4. Inspect existing console/winpty/runtime validation interfaces before choosing execution method.
5. Reverify sample identity by size and sha256 under command-scoped LOCAL_REVERSE_ROOT=E:\reverse before execution.
6. Execute the sample at most two validation inputs:
   positive candidate: KEEP_DREAM
   negative control: KEEP_DREAN
7. Use bounded timeout handling. If the program waits on pause after printing an oracle signal, classify based on captured stdout before timeout and record timeout semantics explicitly.
8. Generate runtime validation artifact.
9. Register runtime validation artifact in artifact_index.
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
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

Must inspect bounded existing capability surface before runtime execution:

```text
Search repository for directly relevant existing runtime/console validation support:
  winpty
  console
  runtime_validation
  validator
  pywinpty
  subprocess
  artifact_index registration helpers

Inspect only directly relevant modules/tests discovered by that search.
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
3. Did it confirm this is bounded runtime validation, not new solving?
4. Did it confirm task_packet.task remains advisory?
5. Did it confirm current targeted_static_solving artifact is current/SUCCESS/candidate unvalidated?
6. Did it confirm current readiness artifact is READY?
7. Did it confirm cpp2_32f1713e training status remains inventory_only / known_candidate="" before execution?
8. Did it inspect existing runtime/console validation interfaces before choosing tools?
9. Which existing execution interface was used?
10. Did it avoid creating duplicate runtime/debugger/static extraction interfaces?
11. Did it reverify sample identity by size and sha256 before execution?
12. Did it execute only the positive candidate KEEP_DREAM and negative control KEEP_DREAN?
13. Did it capture bounded stdout/stderr snippets and exit/timeout semantics?
14. Did candidate stdout contain the success signal?
15. Did negative control stdout contain a failure signal or otherwise reject success?
16. Did it avoid debugger/hook/emulator/probe/instrumentation?
17. Did it avoid brute force/dictionary/search/fuzzing?
18. Did it avoid binary upload/copy/embed/full dumps?
19. Did it generate project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json?
20. Did it register the artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
21. Did it keep project_state/local_reverse_training_status.json unchanged?
22. Did it keep training_materials/local_reverse/status_overlay.json unchanged?
23. Did it preserve cpp2_2f64e68d solved facts?
24. Did it explain negative_results unchanged or non-use?
25. Did it run required py_compile/pytest/lint/status/git checks?
26. Did pytest_result.txt use this decision_id/report_id/round_id?
27. Did final lint-report run after report write?
28. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded runtime validation only.

### Phase A — state and artifact preflight

Use `.venv\Scripts\python` for repository Python commands.

Verify:

```text
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json:
  static_solving_status == SUCCESS
  sample_id == cpp2_32f1713e
  unvalidated_candidate_hypothesis.candidate == KEEP_DREAM
  unvalidated_candidate_hypothesis.validation_status == unvalidated
  candidate_validation_attempted == false
  candidate_validated == false
  executed_sample == false
  ran_runtime_tools == false

project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json:
  readiness_status == READY
  sample_id == cpp2_32f1713e
  command_scoped_root == E:\reverse
  size_bytes == 196686
  sha256 == 32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412

project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
  cpp2_32f1713e.blocked_reason == ""
```

Reverify identity under command-scoped root before execution:

```bat
cmd /c "set LOCAL_REVERSE_ROOT=E:\reverse&& .venv\Scripts\python -c \"import os, pathlib, hashlib; p=pathlib.Path(os.environ['LOCAL_REVERSE_ROOT'])/'逆向课程2023春补考02'/'Cpp2.exe'; b=p.read_bytes(); print(p); print(len(b)); print(hashlib.sha256(b).hexdigest())\""
```

This identity check is allowed. Do not print or store raw bytes.

### Phase B — existing runtime interface inspection

Perform bounded repository search/inspection for existing runtime validation interfaces:

```text
winpty / pywinpty
console validator
runtime validation
subprocess execution wrappers
artifact_index registration helpers
```

Decision rule:

```text
1. Prefer existing mature console/winpty validation path if available.
2. If existing validator is unavailable but simple subprocess execution is already used in existing local reverse validation code, reuse that pattern narrowly.
3. Do not create a new generic runtime framework.
4. If no bounded execution path is available, stop as BLOCKED and explain missing local runtime capability.
```

### Phase C — bounded execution

Execute at most these two inputs:

```text
positive_candidate_input=KEEP_DREAM
negative_control_input=KEEP_DREAN
```

Expected oracle:

```text
success_signal=Congratulations! You are right!
failure_signal_any=[Sorry, you are wrong!, Sorry,you are wrong!]
```

Classification rules:

```text
VALIDATED if:
  positive candidate stdout contains success_signal
  AND negative control stdout does not contain success_signal
  AND negative control stdout contains at least one failure signal or otherwise cleanly rejects

REJECTED if:
  positive candidate stdout contains a failure signal and no success_signal

AMBIGUOUS if:
  stdout/stderr/timeout prevents distinguishing success from failure
  OR positive and negative both show success
  OR positive and negative both lack usable oracle signal

BLOCKED if:
  sample cannot be executed through allowed existing interface
  OR identity cannot be reverified
  OR required artifacts are missing/stale
```

Timeout handling:

```text
If stdout captures a complete success/failure oracle signal before timeout, and timeout is attributable to post-oracle pause/wait, timeout is non-blocking for oracle classification.
Record:
  timeout_after_oracle_signal_captured=true|false
  timeout_source=inferred_system_pause|unknown|none
  exit_code_required_for_oracle_verdict=false if oracle signal is sufficient
```

### Phase D — runtime validation artifact

Generate:

```text
project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
```

Required top-level fields:

```text
schema_version=1
mainline=reverse_solving
round_id=round_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
decision_id=decision_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
command_scoped_root=E:\reverse
sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
size_bytes=196686
sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
identity_verified=true|false
source_static_solving_artifact=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solving.json
source_static_solving_status=SUCCESS
candidate=KEEP_DREAM
negative_control=KEEP_DREAN
validation_status=VALIDATED|REJECTED|AMBIGUOUS|BLOCKED|FAILED
candidate_success_signal_captured=true|false
candidate_failure_signal_captured=true|false
control_success_signal_captured=true|false
control_failure_signal_captured=true|false
oracle_verdict_source=stdout_signal|timeout_before_signal|execution_error|not_run
exit_code_required_for_oracle_verdict=true|false
candidate_run={bounded metadata only}
control_run={bounded metadata only}
stdout_snippet_policy=bounded_oracle_snippets_only
executed_sample=true|false
execution_count=0|1|2
ran_runtime_tools=true|false
runtime_tool_used=<existing interface name or subprocess wrapper>
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
full_stderr_recorded=false
memory_dump_recorded=false
full_disassembly_recorded=false
full_decompilation_recorded=false
training_status_modified=false
next_recommended_mainline=training_dataset|reverse_solving
next_recommended_action=<bounded next step>
generated_at=<timestamp>
```

### Phase E — artifact_index registration

Register the artifact regardless of validation_status:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_keep_dream_runtime_validation"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_keep_dream_runtime_validation"]
artifact_index.artifact_refs["local_reverse_cpp2_32f1713e_keep_dream_runtime_validation"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_candidate_runtime_validation
path=project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
freshness=current
source_run=round_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
candidate=KEEP_DREAM
validation_status=VALIDATED|REJECTED|AMBIGUOUS|BLOCKED|FAILED
candidate_success_signal_captured=true|false
control_failure_signal_captured=true|false
source_static_solving_artifact=project_state\\local_reverse_cpp2_32f1713e_targeted_static_solving.json
training_status_modified=false
```

Optional low-token pointers:

```text
current_state.local_reverse_current_runtime_validation=project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
task_packet.local_reverse_current_runtime_validation=project_state\\local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json
```

Do not change `task_packet.task`. Do not alter training_status/status_overlay.

### Phase F — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1",
  "round_id": "round_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS|BLOCKED|REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
validation_status=VALIDATED -> status=SUCCESS, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
validation_status=REJECTED -> status=SUCCESS, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
validation_status=AMBIGUOUS -> status=PARTIAL, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
validation_status=BLOCKED -> status=BLOCKED, acceptance_recommendation=BLOCKED
validation_status=FAILED -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

Use `ACCEPTED_WITH_LIMITATIONS` even when validated because training status sync is intentionally deferred to a later decision.

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
decision_id=decision_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
report_id=report_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
round_id=round_20260607_cpp2_32f1713e_keep_dream_runtime_validation_v1
```

Content assertions to record:

```text
1. source targeted_static_solving artifact is current/SUCCESS/unvalidated candidate KEEP_DREAM.
2. source readiness artifact is current/READY.
3. sample identity reverified by size and sha256.
4. existing runtime/console validation interface inspected before execution.
5. exactly positive candidate KEEP_DREAM and negative control KEEP_DREAN were executed, unless blocked before execution.
6. no debugger/hook/emulator/probe/instrumentation was used.
7. no brute force/dictionary/search/fuzzing was used.
8. runtime validation artifact exists.
9. validation_status follows VALIDATED/REJECTED/AMBIGUOUS/BLOCKED/FAILED rules.
10. artifact_index registers local_reverse_cpp2_32f1713e_keep_dream_runtime_validation as current.
11. stdout snippets are bounded and contain no full dump.
12. no binary was uploaded, copied, embedded, or committed.
13. no memory dumps/screenshots/full disassembly/full decompilation were recorded.
14. training_status/status_overlay sample state unchanged.
15. cpp2_2f64e68d solved facts unchanged.
16. pytest_result uses this decision_id/report_id/round_id.
17. final lint-report ran after report write.
18. git diff --name-status only contains allowed files.
```

If `pytest` reports no tests collected, record it explicitly and do not claim full test coverage. Acceptance recommendation must remain at most `ACCEPTED_WITH_LIMITATIONS`.

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. source static solving artifact and readiness artifact are valid/current;
2. sample identity is reverified;
3. exactly bounded candidate/control validation is performed;
4. validation artifact is produced and registered current;
5. candidate/control oracle verdict is VALIDATED or REJECTED;
6. no forbidden debugger/hook/probe/bruteforce/search action occurred;
7. no training status sync occurred in this round;
8. tests/lint/report metadata align with this decision/report/round.
```

Stop with `PARTIAL / ACCEPTED_WITH_LIMITATIONS` if:

```text
1. execution occurred but oracle is AMBIGUOUS;
2. artifact records exact ambiguity reason and bounded next step;
3. all prohibitions and metadata requirements are respected.
```

Stop with `BLOCKED` if:

```text
1. source artifacts are missing/stale;
2. identity cannot be reverified;
3. no allowed existing runtime execution path is available;
4. local environment cannot execute the sample under command-scoped root.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. any forbidden action occurs;
2. more than the two allowed inputs are executed;
3. training status/status_overlay are modified;
4. artifact_index/report/pytest_result do not align with this decision.
```
