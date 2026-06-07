```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_static_triage_rework_v1",
  "round_id": "round_20260607_cpp2_32f1713e_static_triage_rework_v1",
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

本轮主线是 **tool_integration**，并且是上一轮 `cpp2_32f1713e_static_triage_v1` 的 **rework**。

目标：只修复上一轮审计发现的两个阻断项：

```text
1. project_state/artifact_index.json 中 local_reverse_cpp2_32f1713e_static_triage 只登记到了 artifact_refs，未登记到 latest_artifacts 和 latest_artifacts_v2。
2. project_state/codex_execution_report.md 顶部 codex_report_summary.acceptance_recommendation 使用了 NEEDS_REVIEW，不符合允许枚举。
```

本轮不重新 triage 样本，不重新读取本地 PE，不运行任何静态提取工具，不运行 IDA/Ghidra/debugger/hook/emulator/runtime probe/winpty/console validator，不生成 candidate，不做 bruteforce/dictionary search，不做 runtime validation。

必须保持上一轮已生成 artifact 的事实：

```text
artifact=project_state/local_reverse_cpp2_32f1713e_static_triage.json
sample_id=cpp2_32f1713e
triage_status=PARTIAL
local_sample_available=false
local_sample_unavailable_reason=LOCAL_REVERSE_ROOT_NOT_SET
executed_sample=false
ran_runtime_tools=false
ran_debugger=false
ran_bruteforce=false
uploaded_binary=false
recommended_next_mainline=tool_integration
```

本轮接受目标不是把 static triage 变成 SUCCESS，而是把 **PARTIAL static triage artifact 的登记和报告 schema 修正完整**。若修复成功，报告建议使用 `ACCEPTED_WITH_LIMITATIONS`，限制为：本地样本根未设置，静态 strings/imports/sections 未提取。

---

## 2. Current Evidence

当前 `decision_packet.md` 是本轮唯一执行权威。`project_state/task_packet.json` 中的 `task` 仍是旧 `samplereverse` advisory，不控制本轮。

上一轮审计结论为 `REWORK_REQUIRED`，核心证据：

```text
project_state/local_reverse_cpp2_32f1713e_static_triage.json:
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
  local_sample_available=false
  local_sample_unavailable_reason=LOCAL_REVERSE_ROOT_NOT_SET
  triage_status=PARTIAL
```

上一轮 artifact_index 当前状态：

```text
artifact_refs["local_reverse_cpp2_32f1713e_static_triage"] exists.
latest_artifacts["local_reverse_cpp2_32f1713e_static_triage"] is missing.
latest_artifacts_v2["local_reverse_cpp2_32f1713e_static_triage"] is missing.
```

上一轮 report 当前状态：

```text
report_id=report_20260607_cpp2_32f1713e_static_triage_v1
round_id=round_20260607_cpp2_32f1713e_static_triage_v1
based_on_decision_id=decision_20260607_cpp2_32f1713e_static_triage_v1
status=PARTIAL
acceptance_recommendation=NEEDS_REVIEW  # invalid for project audit conclusion enum
```

训练状态必须保持不变：

```text
project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status=inventory_only
  cpp2_32f1713e.known_candidate=""
  cpp2_32f1713e.blocked_reason=""
  cpp2_32f1713e.classification=""
```

队列上下文必须保持不变：

```text
project_state/local_reverse_evaluation_queue.json:
  rank 1 sample_id=cpp2_32f1713e
  allowed_actions=[static_triage]
  forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

`negative_results.json` 不需要更新，因为本轮只修复 artifact registration/report schema，不产生新的 reverse-solving failed direction。

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前任务。
2. 不重新 triage 样本。
3. 不读取或执行本地 PE 样本。
4. 不运行 strings/objdump/radare2/file/pefile/lief/capstone/IDA/Ghidra。
5. 不运行 debugger/hook/emulator/runtime probe/winpty/console validator。
6. 不运行 bruteforce、dictionary search、solver 或 candidate validation。
7. 不上传、复制、提交、base64 嵌入任何样本二进制。
8. 不提交 solve_reports、.venv、site-packages、wheel、DLL、EXE、PDB、dump、screenshot 或本地二进制数据。
9. 不扫描 full solve_reports、full PROJECT_PROGRESS_LOG.txt 或本地样本目录。
10. 不修改 .codex-skills。
11. 不创建任何新 IDA/Ghidra/debugger/static extraction interface。
12. 不修改 training_status/status_overlay 的样本状态。
13. 不把 cpp2_32f1713e 标记为 solved 或 blocked。
14. 不改变 cpp2_2f64e68d / 10013 等已接受 solved facts。
15. 不把 static triage 的 PARTIAL 伪装成 SUCCESS。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 .codex-skills/registry.json。
3. 读取 project_state/local_reverse_cpp2_32f1713e_static_triage.json 并计算实际 sha256/size。
4. 更新 artifact_index.latest_artifacts 和 latest_artifacts_v2，补齐 local_reverse_cpp2_32f1713e_static_triage。
5. 保留 artifact_refs 中已存在的 local_reverse_cpp2_32f1713e_static_triage。
6. 写 codex_execution_report.md 和 pytest_result.txt。
7. 必要时只在 artifact_index 或报告中补充 registration provenance；不改 triage artifact 内容，除非只补充 rework_review 字段且不改变 triage 事实。
```

---

## 4. Files To Inspect

必须读取：

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
training_materials/local_reverse/status_overlay.json
reverse_agent/project_state.py
tests/test_project_state.py
```

不要读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
local_reverse_samples/ full tree
E:\reverse full tree
```

---

## 5. Required Audit

Codex report 必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认本轮是 tool_integration rework，不是新 triage，不是 reverse_solving。
3. 是否承认上一轮 static triage artifact 已生成但 artifact_index.latest_artifacts/latest_artifacts_v2 未登记完整。
4. 是否确认上一轮 report 的 acceptance_recommendation=NEEDS_REVIEW 不符合允许枚举。
5. 是否补齐 latest_artifacts["local_reverse_cpp2_32f1713e_static_triage"]。
6. 是否补齐 latest_artifacts_v2["local_reverse_cpp2_32f1713e_static_triage"] 并标记 freshness=current。
7. 是否保留 artifact_refs 中的 local_reverse_cpp2_32f1713e_static_triage。
8. 是否使用 triage artifact 的实际 sha256 和 size_bytes。
9. 是否保持 triage_status=PARTIAL 且没有改成 SUCCESS。
10. 是否保持 local_sample_available=false / LOCAL_REVERSE_ROOT_NOT_SET。
11. 是否没有运行样本或任何静态/动态工具。
12. 是否没有运行 IDA/Ghidra/debugger/hook/emulator/runtime probe/winpty/console validator。
13. 是否没有运行 bruteforce/dictionary/candidate validation。
14. 是否没有上传或提交样本二进制。
15. 是否没有修改 training_status/status_overlay 状态。
16. 是否保持 cpp2_32f1713e inventory_only / known_candidate=""。
17. 是否解释 negative_results 未更新的理由。
18. 是否把 codex_report_summary.acceptance_recommendation 改为 ACCEPTED_WITH_LIMITATIONS 或 REWORK_REQUIRED/BLOCKED；不得再用 NEEDS_REVIEW。
19. 是否重新运行 py_compile、pytest、lint-decision、final lint-report、status、git diff checks。
20. 是否 pytest_result.txt 使用本 rework decision_id/report_id/round_id。
21. 是否 final lint-report 在本轮 report 写入后运行。
22. 是否 git diff 只包含允许文件。
```

---

## 6. Implementation Scope

### Phase A — preflight

确认现有 artifact 存在：

```text
project_state/local_reverse_cpp2_32f1713e_static_triage.json
```

断言：

```text
sample_id == cpp2_32f1713e
triage_status == PARTIAL
local_sample_available == false
local_sample_unavailable_reason == LOCAL_REVERSE_ROOT_NOT_SET
executed_sample == false
ran_runtime_tools == false
ran_debugger == false
ran_bruteforce == false
uploaded_binary == false
```

若断言失败，停止并写 `status=BLOCKED`。

### Phase B — artifact_index repair

计算 triage artifact 的实际 metadata：

```text
sha256=<actual sha256 of project_state/local_reverse_cpp2_32f1713e_static_triage.json>
size_bytes=<actual size of project_state/local_reverse_cpp2_32f1713e_static_triage.json>
modified_at=2026-06-07T10:48:39Z  # artifact generated_at if unchanged
```

补齐 `project_state/artifact_index.json`：

```text
latest_artifacts["local_reverse_cpp2_32f1713e_static_triage"] = "project_state\\local_reverse_cpp2_32f1713e_static_triage.json"
```

补齐：

```json
"latest_artifacts_v2": {
  "local_reverse_cpp2_32f1713e_static_triage": {
    "kind": "local_reverse_static_triage",
    "path": "project_state\\local_reverse_cpp2_32f1713e_static_triage.json",
    "freshness": "current",
    "source_run": "round_20260607_cpp2_32f1713e_static_triage_v1",
    "sha256": "<actual sha256>",
    "size_bytes": <actual size>,
    "modified_at": "2026-06-07T10:48:39Z",
    "sample_id": "cpp2_32f1713e",
    "rework_review": {
      "rework_round_id": "round_20260607_cpp2_32f1713e_static_triage_rework_v1",
      "rework_decision_id": "decision_20260607_cpp2_32f1713e_static_triage_rework_v1",
      "artifact_modified_in_rework": false,
      "review_note": "Rework only repaired latest_artifacts/latest_artifacts_v2 registration for the existing PARTIAL static triage artifact. Static triage remains partial because LOCAL_REVERSE_ROOT was not set."
    }
  }
}
```

Do not remove older local_reverse entries. Do not alter stale/missing samplereverse artifacts.

### Phase C — report schema repair

Write `project_state/codex_execution_report.md` with top block:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_static_triage_rework_v1",
  "round_id": "round_20260607_cpp2_32f1713e_static_triage_rework_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_static_triage_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Report body must state:

```text
- This is a rework of round_20260607_cpp2_32f1713e_static_triage_v1.
- The original triage artifact remains PARTIAL.
- The rework succeeded because artifact_index registration and report schema were repaired.
- Limitation: no local sample extraction was performed because LOCAL_REVERSE_ROOT was not set in the original triage round.
```

### Phase D — pytest_result

`project_state/pytest_result.txt` must use:

```text
decision_id=decision_20260607_cpp2_32f1713e_static_triage_rework_v1
report_id=report_20260607_cpp2_32f1713e_static_triage_rework_v1
round_id=round_20260607_cpp2_32f1713e_static_triage_rework_v1
status=PASSED
```

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

Content assertions required in report/pytest_result:

```text
1. Existing static triage artifact exists and remains triage_status=PARTIAL.
2. local_sample_available remains false and LOCAL_REVERSE_ROOT_NOT_SET remains recorded.
3. No sample executable run.
4. No static extraction tool newly run.
5. No debugger/hook/emulator/runtime probe/winpty/console validator run.
6. No bruteforce/dictionary/candidate validation run.
7. No binary uploaded or committed.
8. artifact_index.latest_artifacts contains local_reverse_cpp2_32f1713e_static_triage.
9. artifact_index.latest_artifacts_v2 contains local_reverse_cpp2_32f1713e_static_triage with freshness=current.
10. artifact_refs still contains local_reverse_cpp2_32f1713e_static_triage.
11. training_status/status_overlay sample state unchanged.
12. codex_report_summary.acceptance_recommendation is not NEEDS_REVIEW.
13. pytest_result uses this rework decision_id/report_id/round_id.
14. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop and write `status=FAILED` or `status=BLOCKED`, not ACCEPT, if any condition occurs:

```text
1. project_state/local_reverse_cpp2_32f1713e_static_triage.json is missing.
2. triage artifact no longer says triage_status=PARTIAL.
3. triage artifact no longer says local_sample_available=false / LOCAL_REVERSE_ROOT_NOT_SET.
4. artifact_index.latest_artifacts still lacks local_reverse_cpp2_32f1713e_static_triage after repair.
5. artifact_index.latest_artifacts_v2 still lacks local_reverse_cpp2_32f1713e_static_triage after repair.
6. report still uses acceptance_recommendation=NEEDS_REVIEW.
7. Any sample/static extraction/runtime/debugger/solver/bruteforce tool is needed.
8. training_status/status_overlay would need state mutation.
9. pytest_result does not include py_compile reverse_agent/project_state.py.
10. pytest_result does not match this rework decision/report/round.
11. lint-report after final report write fails.
12. git diff includes .venv, site-packages, DLL, EXE, sample binary, solve_reports, or .codex-skills.
```
