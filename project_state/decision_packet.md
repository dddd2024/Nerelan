```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_conpty_gate_validation_record_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_conpty_gate_validation_record_rework_v1",
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

目标：只修复上一轮 ConPTY gate 返工的验证记录问题。代码修复方向已经正确，本轮重点是重新在当前 GitHub/main 同步后的工作树中运行 project_state 检查，并写入真实 `codex_execution_report.md` 与 `pytest_result.txt`。

不得继续修改 gate 逻辑，除非重新运行测试发现当前代码实际失败。

---

## 2. Current Evidence

`project_state/task_packet.json` 与 `project_state/current_state.json` 在当前 GitHub/main 中实际存在。上一轮 Codex 报告声称这两个文件在 prior commit 中被删除，并将 `lint-decision Exit Code 1` 记录为 PASSED；该验证记录不可信，需要返工。

上一轮代码已经完成核心语义：

```text
ConPTY API presence 不再计入 mature backend availability。
仅 pywinpty/winpty/wexpect 可触发 READY_FOR_MATURE_BACKEND_VALIDATION。
ConPTY-only 情况输出 BLOCKED_MATURE_BACKEND_MISSING_CONPTY_ONLY。
```

但上一轮测试记录中：

```text
lint-decision Exit Code=1
lint-decision: FAILED
missing project_state/current_state.json
missing project_state/task_packet.json
```

同时又被标成：

```text
Result: PASSED
Overall: PASSED
```

当前 GitHub/main 中 `project_state/task_packet.json` 和 `project_state/current_state.json` 实际存在，因此需要重新在干净/同步后的工作树中运行验证。

当前 `negative_results.json` 仍禁止 old sample_solver blind search、仅扩 beam/budget、compare_semantics_agree=false primary frontier、提交 full solve_reports、无新证据重复 dynamic probe、Base64/RC4 breakpoint probe before lhs producer identification。本轮不触碰这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不重新运行 mature backend probe CLI 覆盖 project_state artifact。
3. 不运行 pair validator。
4. 不运行 IDA/Ghidra。
5. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
6. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
7. 不测试任何 candidate/control 输入。
8. 不修改 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
9. 不修改 project_state/artifact_index.json。
10. 不修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。
11. 不修改 training status、queue、overlay 或 cpp1 artifacts。
12. 不提交 solve_reports。
13. 不把 lint-decision Exit Code 1 标成 PASSED。
```

允许：

```text
1. 更新 project_state/codex_execution_report.md。
2. 更新 project_state/pytest_result.txt。
3. 只有在重新运行测试发现代码实际失败时，才允许修改 reverse_agent/local_reverse_console_mature_backend_probe.py。
4. 只有在重新运行测试发现测试断言实际失败时，才允许修改 tests/test_local_reverse_console_mature_backend_probe.py。
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

Codex 报告必须回答：

```text
1. 是否确认 task_packet.json/current_state.json 在当前工作树中存在。
2. 是否确认当前 decision_packet 是本轮唯一执行权威。
3. 是否确认本轮只修复验证记录，不改 artifact_index，不改 probe artifact。
4. 是否确认没有运行 CPP2.exe。
5. 是否确认没有运行 mature backend probe CLI 覆盖 artifact。
6. 是否确认 lint-decision Exit Code 是 0。
7. 如果 lint-decision 仍为 1，必须把本轮 status 标为 BLOCKED 或 FAILURE，不能写 SUCCESS/ACCEPTED。
8. 是否确认 pytest_result.txt 中每个命令的 Exit Code 与 Result 一致。
9. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
10. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

只有在测试发现代码实际失败时，才允许修改：

```text
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
```

不得修改：

```text
project_state/artifact_index.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/task_packet.json
project_state/current_state.json
project_state/negative_results.json
.codex-skills/*
solve_reports/*
requirements.txt
requirements-dev.txt
pyproject.toml
```

---

## 7. Tests

必须重新运行并记录真实结果：

```bash
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
1. lint-decision 必须 Exit Code 0 才能写 SUCCESS/ACCEPTED。
2. 若任何必跑命令 Exit Code 非 0，report status 不能写 SUCCESS。
3. pytest_result.txt 不能把失败命令写成 PASSED。
```

---

## 8. Stop Conditions

完成后停止于：

```text
1. 所有必跑命令 Exit Code 0。
2. codex_execution_report.md 使用本轮 decision_id/round_id。
3. pytest_result.txt 使用本轮 decision_id/report_id/round_id。
4. git status 只包含允许文件。
```

本轮不要继续推进 CPP2 解题或交互验证。
