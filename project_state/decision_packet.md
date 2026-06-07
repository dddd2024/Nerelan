```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1",
  "round_id": "round_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1",
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

目标：解决 `cpp2_32f1713e` 在 Codex 当前进程中仍看不到 `LOCAL_REVERSE_ROOT` 的阻塞，但不要重复上一轮的同一失败检查。允许做一次 **command-scoped local root readiness preflight**：在单条 `cmd` / Python 命令的作用域内显式注入 `LOCAL_REVERSE_ROOT=E:\reverse`，只验证单个目标样本路径、大小和 sha256 是否满足后续静态提取前置条件。

本轮不是静态提取，不是逆向求解，不运行样本、IDA/Ghidra、strings/objdump/radare2/file/pefile/lief/capstone、调试器、winpty、solver、candidate generation 或 candidate validation。

必须产出新的环境覆盖预检 artifact：

```text
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
```

该 artifact 只记录：继承环境是否仍不可见、命令作用域覆盖值、单个样本路径存在性、size/sha256 校验、是否可进入下一轮 bounded static extraction。不得记录样本二进制内容、字符串 dump、导入表、节区、反汇编、截图、dump 或任何静态提取结果。

如果 command-scoped readiness 通过，下一轮再单独生成 static extraction 决策，并明确要求使用同样的 command-scoped root 注入方式。本轮不得顺手执行 static extraction，也不得生成 `project_state/local_reverse_cpp2_32f1713e_static_extraction.json`。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，只提供历史状态和下一队列线索，不覆盖本 decision。

上一轮审计结论为 **BLOCKED but compliant**：

```text
decision_id=decision_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1
report_id=report_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1
round_id=round_20260607_cpp2_32f1713e_local_env_readiness_after_setx_v1
mainline=tool_integration
status=BLOCKED
block_reason=LOCAL_REVERSE_ROOT_NOT_VISIBLE_TO_CODEX_PROCESS_AFTER_SETX
```

上一轮 readiness artifact 已确认：

```text
project_state/local_reverse_cpp2_32f1713e_local_env_readiness.json:
  cmd_env_value=%LOCAL_REVERSE_ROOT%
  python_env_value=<unset>
  env_visible=false
  env_matches_expected=false
  resolved_sample_path=null
  path_exists=false
  size_bytes=null
  sha256=null
  readiness_status=BLOCKED
  block_reason=LOCAL_REVERSE_ROOT_NOT_VISIBLE_TO_CODEX_PROCESS_AFTER_SETX
  executed_sample=false
  ran_static_extraction_tools=false
  ran_runtime_tools=false
  ran_debugger=false
  ran_bruteforce=false
  uploaded_binary=false
```

`artifact_index.latest_artifacts_v2` 已将 `local_reverse_cpp2_32f1713e_local_env_readiness` 标记为 `freshness=current`，`readiness_status=BLOCKED`，source_run 指向上一轮 readiness。

训练队列当前仍以 `cpp2_32f1713e` 为 rank 1：

```text
project_state/local_reverse_evaluation_queue.json:
  items[0].sample_id=cpp2_32f1713e
  items[0].relative_path=逆向课程2023春补考02/Cpp2.exe
  items[0].proposed_next_mainline=tool_integration
  items[0].allowed_actions=[static_triage]
  items[0].forbidden_actions includes runtime_probe, bruteforce, upload_binary
```

训练状态必须保持不变：

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

Inventory metadata for the one target sample:

```text
sample_id=cpp2_32f1713e
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

`negative_results.json` 主要针对旧 `samplereverse` 和盲搜/预算扩展/断点探测失败方向。本轮不得触碰这些方向；不得用 command-scoped readiness 作为借口启动 reverse_solving 或 runtime validation。

已有相关能力检查：项目已有 IDA/Ghidra/debugger/static extraction/harness/solver 相关接口和 artifact 登记机制。本轮不得新增重复接口，也不得调用这些成熟工具；只允许使用 Windows `cmd` 和 Python 标准库做环境变量、路径、文件大小和 sha256 元数据校验。成熟工具调用只能由后续单独的 static extraction decision 授权。

Artifact freshness 规则：上一轮 local env readiness 为 current 但 BLOCKED；旧 static triage 可作历史线索，不等同于当前可访问样本证据；任何 stale/missing samplereverse artifact 不得用于本轮结论。

是否允许运行工具：只允许 `cmd` 和 `.venv\\Scripts\\python` 的元数据检查命令；不允许运行静态逆向工具、动态工具、样本、solver 或验证器。

是否允许读取重型 artifact：不允许默认读取完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、完整 `project_state/rounds/` 或完整 `E:\reverse` 树。

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
8. Do not modify project_state/local_reverse_training_status.json or training_materials/local_reverse/status_overlay.json.
9. Do not alter cpp2_2f64e68d / 10013 solved facts.
10. Do not upload, copy into repo, base64-embed, or commit the sample binary.
11. Do not store raw binary bytes, strings dump, disassembly, imports, sections, screenshots, dumps, or local binary data in any artifact.
12. Do not commit DLL/EXE/PDB/dump/screenshot/solve_reports/.venv/site-packages/wheel/local binary data.
13. Do not scan full solve_reports, full PROJECT_PROGRESS_LOG.txt, full project_state/rounds, or full E:\reverse tree.
14. Do not rebuild full inventory.
15. Do not modify .codex-skills.
16. Do not create duplicate IDA/Ghidra/debugger/static extraction interfaces.
17. Do not classify cpp2_32f1713e beyond readiness status.
```

Allowed:

```text
1. Read default project_state files and .codex-skills/registry.json.
2. Read inventory/training/queue metadata only for cpp2_32f1713e and direct consistency checks.
3. Re-check inherited LOCAL_REVERSE_ROOT in the actual Codex process using cmd and Python.
4. If inherited env is still unset, run a command-scoped override check with LOCAL_REVERSE_ROOT=E:\reverse.
5. Resolve only E:\reverse + 逆向课程2023春补考02/Cpp2.exe.
6. Check whether that one path exists and is a regular file.
7. Compute file size and sha256 for that one target file only.
8. Generate project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json.
9. Register the new readiness artifact in artifact_index.latest_artifacts, artifact_index.latest_artifacts_v2, and artifact_index.artifact_refs.
10. Optionally add low-token pointers in current_state/task_packet while preserving task advisory semantics.
11. Write codex_execution_report.md and pytest_result.txt.
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
project_state/local_reverse_cpp2_32f1713e_local_env_readiness.json
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
3. Did it confirm this is command-scoped local root readiness, not static extraction and not reverse_solving?
4. Did it confirm task_packet.task remains advisory?
5. Did it confirm previous inherited-env readiness artifact is current but BLOCKED?
6. Did it confirm cpp2_32f1713e remains rank 1 / inventory_only / known_candidate=""?
7. Did it re-check inherited LOCAL_REVERSE_ROOT using cmd and Python?
8. Did it run the command-scoped override check only if needed?
9. Did it record the exact command-scoped root value used?
10. Did it resolve the exact sample path for only cpp2_32f1713e?
11. Did it verify path exists and is a regular file?
12. Did it compute size and sha256 for only that one target file?
13. Did size match 196686 and sha256 match 32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412?
14. Did it generate local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json?
15. Did it register the new readiness artifact in latest_artifacts/latest_artifacts_v2/artifact_refs?
16. Did it avoid static extraction artifact generation?
17. Did it avoid strings/objdump/IDA/Ghidra/radare2/file/pefile/lief/capstone?
18. Did it confirm no sample execution occurred?
19. Did it confirm no debugger/hook/emulator/runtime probe/winpty/console validator occurred?
20. Did it confirm no bruteforce/dictionary/candidate validation occurred?
21. Did it confirm no binary was uploaded/copied/embedded/committed?
22. Did it confirm artifact contains no raw binary, strings dump, imports, sections, disassembly, screenshots, or dumps?
23. Did it preserve training_status/status_overlay sample state?
24. Did it explain negative_results unchanged?
25. Did it run required py_compile/pytest/lint/status/git checks?
26. Did pytest_result.txt use this decision_id/report_id/round_id?
27. Did final lint-report run after report write?
28. Did git diff only contain allowed files?
```

---

## 6. Implementation Scope

Small bounded environment-readiness remediation only.

### Phase A — state preflight

Use `.venv\\Scripts\\python` for Python commands when running repository checks.

Verify state:

```text
project_state/local_reverse_evaluation_queue.json:
  items[0].sample_id == cpp2_32f1713e
  items[0].forbidden_actions includes runtime_probe, bruteforce, upload_binary

project_state/local_reverse_training_status.json:
  cpp2_32f1713e.training_status == inventory_only
  cpp2_32f1713e.known_candidate == ""
  cpp2_32f1713e.blocked_reason == ""

project_state/local_reverse_cpp2_32f1713e_local_env_readiness.json:
  readiness_status == BLOCKED
  block_reason == LOCAL_REVERSE_ROOT_NOT_VISIBLE_TO_CODEX_PROCESS_AFTER_SETX
  env_visible == false
  ready_for_static_extraction == false
```

### Phase B — inherited environment re-check

Run and record exact outputs:

```bat
cmd /c echo %LOCAL_REVERSE_ROOT%
.venv\Scripts\python -c "import os; print(os.environ.get('LOCAL_REVERSE_ROOT', '<unset>'))"
```

Record:

```text
inherited_cmd_env_value=<output>
inherited_python_env_value=<output>
inherited_env_visible=true|false
```

### Phase C — command-scoped override path/hash check

If inherited environment is still unset or not equal to `E:\reverse`, perform command-scoped override checks. Do not persist environment variables; do not use setx; do not alter user/system environment.

Allowed command pattern:

```bat
cmd /c "set LOCAL_REVERSE_ROOT=E:\reverse&& .venv\Scripts\python -c \"import os; print(os.environ.get('LOCAL_REVERSE_ROOT', '<unset>'))\""
```

Then, in a single bounded Python script or one-liner, with the same command-scoped root value, resolve and hash only:

```text
E:\reverse\逆向课程2023春补考02\Cpp2.exe
```

Required checks:

```text
command_scoped_root=E:\reverse
command_scoped_env_visible=true|false
resolved_sample_path=E:\reverse\逆向课程2023春补考02\Cpp2.exe
path_exists=true|false
is_regular_file=true|false
size_bytes=<actual or null>
sha256=<actual or null>
size_matches=(actual == 196686)
sha256_matches=(actual == 32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412)
```

Do not read strings, imports, sections, PE headers, disassembly, resources, or any binary-derived semantic data. Hashing the one file for identity verification is allowed.

### Phase D — readiness artifact

Generate:

```text
project_state/local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
```

Required fields:

```text
schema_version=1
mainline=tool_integration
round_id=round_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
decision_id=decision_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
expected_root=E:\reverse
previous_readiness_artifact=project_state\\local_reverse_cpp2_32f1713e_local_env_readiness.json
previous_readiness_status=BLOCKED
previous_block_reason=LOCAL_REVERSE_ROOT_NOT_VISIBLE_TO_CODEX_PROCESS_AFTER_SETX
inherited_cmd_env_value=<recorded>
inherited_python_env_value=<recorded>
inherited_env_visible=true|false
command_scoped_root=E:\reverse
command_scoped_env_visible=true|false
command_scoped_env_matches_expected=true|false
resolved_sample_path=<path or null>
path_exists=true|false
is_regular_file=true|false
size_bytes=<actual or null>
sha256=<actual or null>
expected_size_bytes=196686
expected_sha256=32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412
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
binary_content_recorded=false
strings_dump_recorded=false
disassembly_recorded=false
imports_or_sections_recorded=false
next_recommended_mainline=tool_integration
next_recommended_action=<bounded next step>
generated_at=<timestamp>
```

Readiness rules:

```text
READY only if command_scoped_env_visible=true, command_scoped_env_matches_expected=true, path_exists=true, is_regular_file=true, size_matches=true, sha256_matches=true.
BLOCKED if command-scoped env cannot be set, path missing, file not regular, size mismatch, or sha mismatch.
FAILED only for unexpected script/tool/report errors.
```

### Phase E — artifact_index and optional pointers

Register the new readiness artifact regardless of READY/BLOCKED status:

```text
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_command_scoped_env_readiness"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_command_scoped_env_readiness"]
artifact_index.artifact_refs["local_reverse_cpp2_32f1713e_command_scoped_env_readiness"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_command_scoped_env_readiness
path=project_state\\local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
freshness=current
source_run=round_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_32f1713e
readiness_status=READY|BLOCKED|FAILED
ready_for_static_extraction=true|false
```

Optional low-token pointers:

```text
current_state.local_reverse_current_env_readiness=project_state\\local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
task_packet.local_reverse_current_env_readiness=project_state\\local_reverse_cpp2_32f1713e_command_scoped_env_readiness.json
```

Do not change `task_packet.task`. Do not alter training_status/status_overlay.

### Phase F — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1",
  "round_id": "round_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1",
  "based_on_decision_id": "decision_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Recommended mapping:

```text
readiness_status=READY   -> status=SUCCESS, acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS
readiness_status=BLOCKED -> status=BLOCKED, acceptance_recommendation=BLOCKED
readiness_status=FAILED  -> status=FAILED, acceptance_recommendation=REWORK_REQUIRED
```

If READY, limitation must say: readiness only proves file identity under command-scoped local root; no static extraction or solve evidence exists yet.

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
decision_id=decision_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
report_id=report_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
round_id=round_20260607_cpp2_32f1713e_command_scoped_env_readiness_v1
```

Content assertions to record:

```text
1. command-scoped readiness artifact exists.
2. readiness_status follows READY/BLOCKED/FAILED rules.
3. static extraction artifact was not generated.
4. no sample executable was run.
5. no strings/objdump/IDA/Ghidra/radare2/file/pefile/lief/capstone was run.
6. no debugger/hook/emulator/runtime probe/winpty/console validator was run.
7. no bruteforce/dictionary/candidate validation was run.
8. no binary was uploaded, copied, embedded, or committed.
9. artifact contains no raw binary, strings dump, imports, sections, disassembly, screenshots, or dumps.
10. artifact_index registers local_reverse_cpp2_32f1713e_command_scoped_env_readiness as current.
11. training_status/status_overlay sample state unchanged.
12. pytest_result uses this decision_id/report_id/round_id.
13. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop with `SUCCESS / ACCEPTED_WITH_LIMITATIONS` only if:

```text
1. command-scoped root E:\reverse is visible to the bounded check;
2. target path E:\reverse\逆向课程2023春补考02\Cpp2.exe exists and is a regular file;
3. size_bytes == 196686;
4. sha256 == 32f1713e236775873176c68f432a8404fdb6fb51e3575792d0e52ca7940cf412;
5. new readiness artifact is registered current;
6. no forbidden tool/action was run;
7. tests and lint records are aligned with this decision/report/round.
```

Stop with `BLOCKED / BLOCKED` if:

```text
1. command-scoped env cannot be set or observed;
2. target path is missing;
3. target path is not a regular file;
4. file size mismatches;
5. sha256 mismatches;
6. local sample remains unavailable for metadata-only identity verification.
```

Stop with `FAILED / REWORK_REQUIRED` if:

```text
1. report metadata does not match this decision;
2. pytest_result is missing or stale;
3. static extraction artifact is generated in this round;
4. any forbidden tool/action runs;
5. binary content, strings dump, imports, sections, disassembly, screenshots, dumps, or local binary data are committed;
6. training status or solved facts are changed;
7. artifact_index registration is missing or stale;
8. .codex-skills are modified.
```
