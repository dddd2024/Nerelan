```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **engineering_branch**。

目标：对已 ACCEPTED 的 console backend contract test safety rework 做一次 **minimal archive closeout**，让 active report 从：

```text
round_manifest_present=False
archive_status=not_archived
```

收束为：

```text
round_manifest_present=True
archive_status=archived
```

本轮只做工程状态归档，不改 Python 源码、不改测试、不运行任何真实样本、不运行任何逆向工具、不做 runtime validation。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。它包含：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮不得改写 sample state 或 task_packet。

上一轮 console backend contract test safety rework 已 ACCEPTED：

```text
report_id=report_20260606_cpp2_2f64e68d_console_backend_contract_test_safety_rework_v1
round_id=round_20260606_cpp2_2f64e68d_console_backend_contract_test_safety_rework_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_console_backend_contract_test_safety_rework_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
pytest_result_status=PASSED
focused console backend tests=34 passed
project_state tests=158 passed
lint-decision=0
lint-report=0
project_state status=0
```

上一轮已确认测试安全边界修复：

```text
tests/test_local_reverse_console_pair_validator.py no longer contains CPP2.exe
tests/test_local_reverse_console_pair_validator.py no longer contains 逆向课程2025春03/CPP2.exe
default relative_path is synthetic/nonexistent/unit_test_binary.exe
_validate_console_pair unit tests monkeypatch _resolve_target_path to None
_validate_console_pair unit tests monkeypatch _run_single to raise AssertionError if reached
```

当前 active `lint-report/status` 仍显示：

```text
warning: report round not archived yet
round_manifest_present=False
archive_status=not_archived
decision_consumed_by_report=True
decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

本轮只处理这个工程 closeout 状态。

当前 `negative_results.json` 仍禁止以下方向，本轮不得触碰：

```text
old sample_solver blind search
only increase guided_pool beam or budget
use compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
repeat dynamic/base64/rc4 breakpoint directions without new producer evidence
reuse old [ebp-0x1170] without real-lhs provenance evidence
```

已有相关能力：

```text
1. reverse_agent.project_state archive-round 已用于 minimal archive closeout。
2. project_state lint-report/status 能识别 archive_status。
3. 历史 minimal archive round 已证明只允许 decision_packet.md、codex_execution_report.md、pytest_result.txt、round_manifest.json。
```

是否允许运行工具：

```text
允许运行 project_state lint/status/archive-round、pytest tests/test_project_state.py、git diff/status。
不允许运行 CPP2.exe、任何真实 target、mature backend probe CLI、pair validator CLI、IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
```

是否允许读取重型 artifact：

```text
不允许默认读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
不允许读取 project_state/rounds 全量历史。
只允许读取本轮 round 目录和与 active report/pytest/decision 直接相关的小文件。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不运行任何真实 binary target。
3. 不运行 mature backend probe CLI。
4. 不运行 console pair validator CLI。
5. 不运行任何真实 candidate/control 输入。
6. 不访问 E:\reverse、D:\reverse、C:\reverse、F:\reverse、~/reverse 或 LOCAL_REVERSE_ROOT/REVERSE_ROOT 指向的真实样本路径。
7. 不运行 IDA/Ghidra。
8. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
9. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
10. 不修改 reverse_agent/local_reverse_console_pair_validator.py。
11. 不修改 reverse_agent/local_reverse_console_mature_backend_probe.py。
12. 不修改 tests/test_local_reverse_console_pair_validator.py。
13. 不修改 tests/test_local_reverse_console_mature_backend_probe.py。
14. 不修改 artifact_index.json。
15. 不修改 current_state.json、task_packet.json、negative_results.json。
16. 不修改 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
17. 不修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。
18. 不修改 .codex-skills/*。
19. 不提交 solve_reports。
20. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
21. 不运行 archive-round --include-diff。
22. 不运行 archive-round --include-state-snapshot。
23. 不让 round_manifest 包含 git_diff.patch 或 full state snapshot。
```

允许：

```text
1. 更新 project_state/codex_execution_report.md。
2. 更新 project_state/pytest_result.txt。
3. 新建 project_state/rounds/round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1/ 下的 minimal archive 文件。
```

允许的 round archive 文件仅限：

```text
project_state/rounds/round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1/decision_packet.md
project_state/rounds/round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1/codex_execution_report.md
project_state/rounds/round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1/pytest_result.txt
project_state/rounds/round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1/round_manifest.json
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
reverse_agent/project_state.py
.codex-skills/registry.json
```

必要时读取：

```text
project_state/rounds/round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1/round_manifest.json
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
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 engineering_branch。
4. 是否确认上一轮 test safety rework 已 SUCCESS/ACCEPTED 且 pytest_result PASSED。
5. 是否确认本轮只做 minimal archive closeout，不改代码、不改测试、不改 artifact schema。
6. 是否确认 archive-round 默认/本次执行没有 include-diff。
7. 是否确认 archive-round 默认/本次执行没有 include-state-snapshot。
8. 是否确认 round_manifest 中 files 只包含 decision_packet.md、codex_execution_report.md、pytest_result.txt、round_manifest.json。
9. 是否确认 round_manifest 不包含 git_diff.patch。
10. 是否确认 round_manifest 不包含 current_state.json、artifact_index.json、negative_results.json、task_packet.json、model_gate.json。
11. 是否确认没有运行 CPP2.exe 或任何真实 target。
12. 是否确认没有运行 mature backend probe CLI。
13. 是否确认没有运行 pair validator CLI/runtime validation。
14. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
15. 是否确认没有修改 artifact_index/current_state/task_packet/negative_results/current CPP2 artifacts。
16. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
17. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
18. 是否确认 lint-report Exit Code 0 且 archive_status=archived。
19. 是否确认 project_state status Exit Code 0 且 decision_consumed_by_report=True。
20. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

本轮不改 Python 代码，不改测试。

执行方式建议：

```text
1. 确认上一轮 test safety rework report/pytest_result 已 SUCCESS/ACCEPTED/PASSED。
2. 写入本轮 codex_execution_report.md，report_id 使用：
   report_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1
3. 写入本轮 pytest_result.txt，summary 使用本轮 decision_id/report_id/round_id。
4. 运行本轮必跑检查。
5. 执行 minimal archive：
   python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1
6. 不带 --include-diff。
7. 不带 --include-state-snapshot。
8. 重新运行 lint-report 与 project_state status，确认 archive_status=archived。
```

若当前 CLI 没有 `archive-round` 子命令，必须停止并写 `status=BLOCKED`，不得手工伪造 round_manifest。

若 `archive-round` 生成了 `git_diff.patch` 或 state snapshot，必须停止并写 `status=FAILED` 或 `REWORK_REQUIRED`，不得写 SUCCESS/ACCEPTED。

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260606_cpp2_2f64e68d_console_backend_test_safety_minimal_archive_closeout_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

`pytest_result.txt` 必须记录 archive-round 命令本身，以及 archive 之后的 lint-report/status 输出摘要。

最终 `lint-report` 输出必须包含或等价表达：

```text
lint-report: OK
archive_status=archived
round_manifest_present=True
pytest_result_status=PASSED
pytest_result_matches_report=True
pytest_result_tests_cover_report=True
```

最终 `project_state status` 输出必须包含或等价表达：

```text
decision_consumed_by_report=True
decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
pytest_result_status=PASSED
pytest_result_matches_report=True
pytest_result_tests_cover_report=True
```

---

## 8. Stop Conditions

完成后停止于：

```text
1. 本轮 active report/pytest_result 与本 decision_id/round_id 匹配。
2. minimal archive 目录已生成。
3. round_manifest 只包含允许的 minimal 文件。
4. lint-report Exit Code 0 且 archive_status=archived。
5. project_state status Exit Code 0。
6. git status 只包含允许文件。
```

本轮不要进入 CPP2 交互验证、候选求解、runtime validation 或任何工具接入扩展。
