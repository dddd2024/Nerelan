```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_state_file_sync_and_validation_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_state_file_sync_and_validation_rework_v1",
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

目标：修复 Codex 本地工作树与 GitHub/main 状态不一致导致的验证记录不可信问题。当前 GitHub/main 可读取：

```text
project_state/task_packet.json
project_state/current_state.json
```

因此 Codex 不能继续声称这两个文件在当前 GitHub/main 不存在。必须重新同步工作树，重新运行完整 project_state 检查，并写入真实 report/pytest_result。

本轮不要推进 CPP2 解题、交互验证或任何候选验证。

---

## 2. Current Evidence

GitHub/main 当前存在：

```text
project_state/task_packet.json
project_state/current_state.json
```

上一轮 Codex report 声称这两个文件不存在，导致 `lint-decision Exit Code 1`，并标记 `status=BLOCKED`。这个结果不能接受为最终状态，因为与 GitHub/main 文件事实冲突。

当前 `task_packet.json` 仍是旧 samplereverse advisory，并且包含：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `current_state.json` 仍主要是旧 samplereverse 压缩状态，不能覆盖本轮 decision。

当前 `negative_results.json` 仍禁止 old sample_solver blind search、仅扩 beam/budget、compare_semantics_agree=false primary frontier、提交 full solve_reports、无新证据重复 dynamic probe、Base64/RC4 breakpoint probe before lhs producer identification。本轮不触碰这些方向。

上一轮 ConPTY gate 代码修复本身已经完成，本轮只处理状态文件同步与验证记录可信性。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不重新运行 mature backend probe CLI 覆盖 artifact。
3. 不运行 pair validator。
4. 不运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
5. 不运行 solver/bruteforce/guided pool/symbolic search。
6. 不修改 artifact_index.json。
7. 不修改 local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
8. 不修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。
9. 不修改 task_packet.json/current_state.json/negative_results.json，除非文件在本地确实缺失且需要从 GitHub/main 恢复；恢复时必须保持内容与 GitHub/main 一致。
10. 不把 Exit Code 1 标为 PASSED。
11. 不省略 lint-report 或 project_state status。
12. 不提交 solve_reports。
```

允许：

```text
1. 更新 project_state/codex_execution_report.md。
2. 更新 project_state/pytest_result.txt。
3. 仅当本地缺失但 GitHub/main 存在时，恢复 project_state/task_packet.json 与 project_state/current_state.json，且内容必须与 GitHub/main 一致。
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
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
.codex-skills/registry.json
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
```

---

## 5. Required Audit

Codex 必须回答：

```text
1. git rev-parse HEAD 是多少。
2. git status --short 是否显示 task_packet/current_state 缺失。
3. git ls-files project_state/task_packet.json project_state/current_state.json 的输出是什么。
4. 是否确认本地工作树与 GitHub/main 同步。
5. 是否确认 task_packet.json/current_state.json 在本地存在且被 git 跟踪。
6. 是否确认当前 decision_packet 是本轮唯一执行权威。
7. 是否确认本轮只修复状态文件同步与验证记录，不改 artifact_index，不改 probe artifact。
8. 是否确认没有运行 CPP2.exe。
9. 是否确认没有运行 mature backend probe CLI 覆盖 artifact。
10. lint-decision 是否 Exit Code 0。
11. lint-report 是否 Exit Code 0。
12. project_state status 是否 Exit Code 0。
13. pytest_result.txt 是否完整记录所有必跑命令。
14. codex_report_summary 是否与本 decision_id/round_id 匹配。
15. git diff --name-status 是否只包含允许文件。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

仅当本地缺失但 GitHub/main 存在时，允许恢复：

```text
project_state/task_packet.json
project_state/current_state.json
```

恢复时不得改写内容，只能与 GitHub/main 当前内容一致。

不得修改：

```text
project_state/artifact_index.json
project_state/negative_results.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
.codex-skills/*
solve_reports/*
requirements.txt
requirements-dev.txt
pyproject.toml
```

---

## 7. Tests

必须运行并记录：

```bash
git rev-parse HEAD
git ls-files project_state/task_packet.json project_state/current_state.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m py_compile reverse_agent/local_reverse_console_mature_backend_probe.py
python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

要求：

```text
1. task_packet.json/current_state.json 必须在本地存在且被 git 跟踪。
2. lint-decision 必须 Exit Code 0 才能写 SUCCESS/ACCEPTED。
3. lint-report 必须 Exit Code 0 才能写 SUCCESS/ACCEPTED。
4. project_state status 必须 Exit Code 0 才能写 SUCCESS/ACCEPTED。
5. 若任何必跑命令 Exit Code 非 0，report status 不能写 SUCCESS。
6. pytest_result.txt 不能把失败命令写成 PASSED。
```

---

## 8. Stop Conditions

只有全部满足才可写 `SUCCESS/ACCEPTED`：

```text
1. task_packet.json/current_state.json 在本地存在且被 git 跟踪。
2. lint-decision Exit Code 0。
3. lint-report Exit Code 0。
4. project_state status Exit Code 0。
5. pytest_result.txt 中每个命令 Exit Code 与 Result 一致。
6. git diff 只包含允许文件。
```

本轮不要推进 CPP2 解题或交互验证。
