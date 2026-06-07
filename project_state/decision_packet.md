```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1",
  "round_id": "round_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1",
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

目标：只做 `cpp2_32f1713e` 的 **local environment readiness preflight**，验证用户通过 `setx LOCAL_REVERSE_ROOT "E:\reverse"` 持久化后，Codex 当前执行进程是否已经能看到该环境变量，并验证单个目标样本路径、大小和 sha256 是否满足后续静态提取的前置条件。

本轮不是静态提取，不是逆向求解，不运行任何样本、IDA/Ghidra、strings/objdump、调试器、winpty、solver 或 candidate validation。

必须产出环境预检 artifact：

```text
project_state/local_reverse_cpp2_32f1713e_local_env_readiness.json
```

该 artifact 只记录环境变量、单个样本路径存在性、size/sha256 校验、下一步建议；不得记录样本二进制内容、字符串 dump、反汇编、PE 节区/导入或任何静态提取结果。

如果 readiness 通过，下一轮再单独生成 static extraction 决策；本轮不得顺手执行 strings/objdump/IDA 或生成 `local_reverse_cpp2_32f1713e_static_extraction.json`。

---

## 2. Current Evidence

当前 `decision_packet.md` 是本轮唯一执行权威。`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。

最近两轮 `static_extraction` / `static_extraction_retry` 均为预期内 `BLOCKED`，原因是 Codex 执行环境中仍看不到 `LOCAL_REVERSE_ROOT`：

```text
cmd /c echo %LOCAL_REVERSE_ROOT% -> %LOCAL_REVERSE_ROOT%
Python os.environ.get("LOCAL_REVERSE_ROOT") -> <unset>
project_state/local_reverse_cpp2_32f1713e_static_extraction.json not generated
artifact_index static_extraction registration not added
no static tools ran
training_status/status_overlay unchanged
```

用户随后执行了：

```bat
setx LOCAL_REVERSE_ROOT "E:\reverse"
```

并看到 Windows 输出：

```text
成功：指定的值已得到保存。
```

该事实只说明变量已写入当前 Windows 用户环境；是否被 Codex 当前进程继承，必须由本轮在实际 Codex 执行进程中重新检查。

已有 current triage artifact：

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

Inventory metadata to verify:

```text
relative_path=逆向课程2023春补考02/Cpp2.exe
expected_root=E:\reverse
expected_sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
size_bytes=196686
extension=.exe
guessed_file_type=pe
category=cpp
github_upload_policy=metadata_only
```

`negative_results.json` mostly concerns old `samplereverse` directions. This round must not touch blind search, budget expansion, breakpoint probes, solve_reports, or any reverse-solving direction.

---

## 3. Do Not Do

Strictly forbidden:

```text
1. Do not treat task_packet.task as current execution authority.
2. Do not run the sample executable.
3. Do not run strings, objdump, radare2, file, pefile, lief, capstone, IDA, Ghidra, or any static extraction tool.
4. Do not attach debugger, hook, emulator, runtime probe, winpty, console validator, or dynamic harness.
5. Do not run bruteforce, dictionary search, solver search, candidate generation, or candidate validation.
6. Do not generate project_state/local_reverse_cpp2_32f1713e_static_extraction.json in this round.
7. Do not generate any candidate or mark the sample solved/blocked.
8. Do not upload, copy into repo, base64-embed, or commit the sample binary.
9. Do not store raw binary bytes, strings dump, disassembly, imports, sections, screenshots, dumps, or local binary data in any artifact.
10. Do not commit DLL/EXE/PDB/dump/screenshot/solve_reports/.venv/site-packages/wheel/local binary data.
11. Do not scan full solve_reports, full PROJECT_PROGRESS_LOG.txt, or full E:\reverse tree.
12. Do not rebuild full inventory.
13. Do not modify .codex-skills.
14. Do not create duplicate IDA/Ghidra/debugger/static extraction interfaces.
15. Do not alter cpp2_2f64e68d / 10013 solved facts.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read inventory/training/queue metadata for cpp2_32f1713e.
3. Verify LOCAL_REVERSE_ROOT in the actual Codex process using both cmd and Python environment access.
4. Resolve LOCAL_REVERSE_ROOT + relative_path for this one sample only.
5. Check whether that path exists and is a regular file.
6. Compute file size and sha256 for this one target file only.
7. Generate project_state/local_reverse_cpp2_32f1713e_local_env_readiness.json.
8. Register the readiness artifact in artifact_index latest_artifacts, latest_artifacts_v2, and artifact_refs.
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
project_state/local_reverse_cpp2_32f1713e_static_triage.json
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
E:\reverse full tree beyond E:\reverse\逆向课程2023春补考02\Cpp2.exe
```

---

## 5. Required Audit

Codex report must answer:

```text
1. Did it confirm decision_packet is the sole execution authority?
2. Did it confirm mainline=tool_integration?
3. Did it confirm this is local env readiness preflight, not static extraction and not reverse_solving?
4. Did it confirm task_packet.task remains advisory?
5. Did it confirm cpp2_32f1713e remains rank 1 / inventory_only / known_candidate=""?
6. Did it verify LOCAL_REVERSE_ROOT in the actual Codex execution process using cmd and Python?
7. Did it record whether setx is visible to Codex after process restart?
8. Did it resolve the exact sample path for only cpp2_32f1713e?
9. Did it verify path exists and is a regular file?
10. Did it compute size and sha256 for only that one target file?
11. Did size match 196686 and sha256 match 32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412?
12. Did it generate local_reverse_cpp2_32f1713e_local_env_readiness.json?
13. Did it register the readiness artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
14. Did it avoid static extraction artifact generation?
15. Did it avoid strings/objdump/IDA/Ghidra/radare2/file/pefile/lief/capstone?
16. Did it confirm no sample execution occurred?
17. Did it confirm no debugger/hook/emulator/runtime probe/winpty/console validator occurred?
18. Did it confirm no bruteforce/dictionary/candidate validation occurred?
19. Did it confirm no binary was uploaded/copied/embedded/committed?
20. Did it preserve training_status/status_overlay sample state?
21. Did it explain negative_results unchanged?
22. Did it run required py_compile/pytest/lint/status/git checks?
23. Did pytest_result.txt use this decision_id/report_id/round_id?
24. Did final lint-report run after report write?
25. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded readiness preflight only.

### Phase A — state preflight

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

### Phase B — environment visibility check

Run and record exact outputs:

```bat
cmd /c echo %LOCAL_REVERSE_ROOT%
.venv\Scripts\python -c "import os; print(os.environ.get('LOCAL_REVERSE_ROOT', '<unset>'))"
```

Also record expected value:

```text
expected_LOCAL_REVERSE_ROOT=E:\reverse
```

### Phase C — single-file path/hash check

If and only if `LOCAL_REVERSE_ROOT` is visible and non-empty, resolve:

```text
sample_path=%LOCAL_REVERSE_ROOT%\逆向课程2023春补考02\Cpp2.exe
```

Check only this path:

```text
path_exists=true|false
is_regular_file=true|false
size_bytes=<actual or null>
sha256=<actual or null>
size_matches=(actual == 196686)
sha256_matches=(actual == 32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412)
```

Do not read strings, imports, sections, PE headers, or disassembly.

### Phase D — readiness artifact

Generate:

```text
project_state/local_reverse_cpp2_32f1713e_local_env_readiness.json
```

Required fields:

```text
schema_version=1
mainline=tool_integration
round_id=round_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1
decision_id=decision_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
expected_root=E:\reverse
cmd_env_value=<recorded>
python_env_value=<recorded>
env_visible=true|false
env_matches_expected=true|false
resolved_sample_path=<path or null>
path_exists=true|false
is_regular_file=true|false
size_bytes=<actual or null>
sha256=<actual or null>
size_matches=true|false|null
sha256_matches=true|false|null
ready_for_static_extraction=true|false
readiness_status=READY|BLOCKED|FAILED
block_reason=<null or reason>
executed_sample=false
ran_static_extraction_tools=false
ran_runtime_tools=false
ran_debugger=false
ran_bruteforce=false
uploaded_binary=false
candidate_generated=false
candidate_validation_attempted=false
next_recommended_mainline=tool_integration
next_recommended_action=<bounded next step>
generated_at=<timestamp>
```

Readiness rules:

```text
READY only if env_visible=true, env_matches_expected=true, path_exists=true, is_regular_file=true, size_matches=true, sha256_matches=true.
BLOCKED if env is unset, path missing, file not regular, size mismatch, or sha mismatch.
FAILED only for unexpected script/tool/report errors.
```

### Phase E — artifact_index and optional pointers

Register readiness artifact regardless of READY/BLOCKED status:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_local_env_readiness"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_local_env_readiness"]
artifact_index.artifact_refs["local_reverse_cpp2_32f1713e_local_env_readiness"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_local_env_readiness
path=project_state\\local_reverse_cpp2_32f1713e_local_env_readiness.json
freshness=current
source_run=round_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
readiness_status=READY|BLOCKED|FAILED
```

Optional low-token pointers:

```text
current_state.local_reverse_current_env_readiness=project_state\\local_reverse_cpp2_32f1713e_local_env_readiness.json
task_packet.local_reverse_current_env_readiness=project_state\\local_reverse_cpp2_32f1713e_local_env_readiness.json
```

Do not change `task_packet.task`. Do not alter training_status/status_overlay.

### Phase F — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1",
  "round_id": "round_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
readiness_status=READY   -> report status=SUCCESS, acceptance_recommendation=ACCEPTED
readiness_status=BLOCKED -> report status=BLOCKED, acceptance_recommendation=BLOCKED
readiness_status=FAILED  -> report status=FAILED, acceptance_recommendation=REWORK_REQUIRED
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

If project source code is modified, run targeted tests for changed code. If only project_state artifacts are changed, `tests/test_project_state.py` is sufficient.

Content assertions required in report/pytest_result:

```text
1. task_packet.task remains advisory.
2. cpp2_32f1713e remains inventory_only and known_candidate="".
3. LOCAL_REVERSE_ROOT was checked in the actual Codex process using cmd and Python.
4. local_env_readiness artifact exists.
5. readiness_status follows READY/BLOCKED/FAILED rules.
6. Static extraction artifact was not generated in this round.
7. No sample executable run.
8. No strings/objdump/IDA/Ghidra/radare2/file/pefile/lief/capstone run.
9. No debugger/hook/emulator/runtime probe/winpty/console validator run.
10. No bruteforce/dictionary/candidate validation run.
11. No binary uploaded, copied, embedded, or committed.
12. Artifact contains no raw binary, strings dump, imports, sections, or disassembly.
13. artifact_index registers local_reverse_cpp2_32f1713e_local_env_readiness as current.
14. training_status/status_overlay sample state unchanged.
15. pytest_result uses this decision_id/report_id/round_id.
16. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop and write `status=FAILED`, not ACCEPT, if any condition occurs:

```text
1. local_env_readiness artifact cannot be generated.
2. artifact_index cannot register local_env_readiness artifact.
3. Any static extraction tool would need to run.
4. Any sample execution would need to run.
5. Any debugger/hook/emulator/runtime probe/winpty/console validator would need to run.
6. Any bruteforce/dictionary/candidate validation would need to run.
7. Sample binary would need to be uploaded, copied, embedded, or committed.
8. training_status/status_overlay would need solved/blocked mutation.
9. Artifact would contain raw binary, strings dump, imports, sections, disassembly, screenshot, dump, or local binary data.
10. pytest_result does not include py_compile reverse_agent/project_state.py.
11. pytest_result does not match this decision/report/round.
12. lint-report after final report write fails.
13. git diff includes .venv, site-packages, DLL, EXE, sample binary, solve_reports, or .codex-skills.
```
