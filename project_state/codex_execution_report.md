```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_winpty_py_target_spawn_fix_v1",
  "round_id": "round_20260607_winpty_py_target_spawn_fix_v1",
  "based_on_decision_id": "decision_20260607_winpty_py_target_spawn_fix_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/local_reverse_winpty_py_target_spawn_fix.json",
    "project_state/local_reverse_winpty_synthetic_smoke.json",
    "project_state/pytest_result.txt",
    "reverse_agent/local_reverse_console_pair_validator.py",
    "tests/test_local_reverse_console_pair_validator.py"
  ],
  "tests_ran": [
    ".venv\\Scripts\\python -c \"import sys; print(sys.executable); import winpty; print('winpty_import_ok')\"",
    ".venv\\Scripts\\python -c \"import winpty; print(hasattr(winpty, 'PTY')); print([name for name in dir(winpty.PTY) if not name.startswith('_')])\"",
    ".venv\\Scripts\\python -c \"import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True\"",
    ".venv\\Scripts\\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py",
    ".venv\\Scripts\\python -m pytest -q tests/test_local_reverse_console_pair_validator.py",
    ".venv\\Scripts\\python -m pytest -q tests/test_project_state.py",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-decision --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-report --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state status --state-dir project_state",
    "<synthetic winpty smoke command using .venv\\Scripts\\python>",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_winpty_py_target_spawn_fix.json",
    "project_state/local_reverse_winpty_synthetic_smoke.json"
  ],
  "next_suggested_task": "Open a separate reverse_solving decision for bounded cpp2_2f64e68d ippio/jppio winpty validation."
}
```

# Codex Execution Report

## Summary

本轮执行成功。当前 `project_state/decision_packet.md` 是唯一执行权威，`task_packet.task=Review bounded window discovery diagnostics` 只是旧 `samplereverse` advisory；本轮主线是 `tool_integration`，不是 `reverse_solving`。

修复点限制在 `_run_single_winpty` 的 `.py` target spawn 参数：`.py` 目标现在使用 `Path(sys.executable).name` 作为 `appname`，`cmdline` 仅包含临时脚本路径；`.exe` target、subprocess backend、candidate/control 判定、hash check、timeout/read/write 生命周期未改变。

## Audit Result

1. 当前 decision_packet 是本轮唯一执行权威：是，`decision_20260607_winpty_py_target_spawn_fix_v1`。
2. task_packet.task 只是旧 samplereverse advisory：是，不控制本轮。
3. 本轮主线为 tool_integration：是，不是 reverse_solving。
4. 上一轮 synthetic smoke BLOCKED 且 Phase B / CPP2.exe 未运行：确认。
5. 本轮没有运行 CPP2.exe / Cpp2.exe 或任何真实训练样本：确认，只运行临时 Python synthetic script。
6. 本轮没有重复 ippio/jppio validation：确认。
7. 没有改写 cpp2 runtime validation artifact 为 solved：确认，`project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json` 未修改。
8. 没有重跑 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce：确认。
9. 原错误：`.py` target 通过 winpty spawn 时重复把 `sys.executable` 放入 `appname` 和 `cmdline`，导致 Python 把 `python.exe` 自身当作脚本解析。
10. 修复方式：`.py` target 使用 `appname=Path(sys.executable).name`，`cmdline=list2cmdline([script_path])`。
11. mock/fake winpty 测试覆盖 `.py` target spawn 参数、`.exe` target 参数和 subprocess backend 不变。
12. synthetic smoke 使用临时 Python 脚本，不访问训练样本、不包含 candidate/flag、不读取 `E:
everse` 或 `local_reverse_samples`。
13. synthetic smoke artifact 已写入 `project_state/local_reverse_winpty_synthetic_smoke.json`。
14. spawn fix artifact 已写入 `project_state/local_reverse_winpty_py_target_spawn_fix.json`。
15. artifact_index 已登记两个 artifact 的 current provenance。
16. cpp2_2f64e68d training status 仍为 blocked，known_candidate 仍为空，未设置 solved=true。
17. 所有 Python 命令都使用 `.venv\Scripts\python`。
18. lint-report 将在本报告写入后最终运行并记录到 pytest_result.txt。
19. pytest_result.txt 使用本 decision_id/report_id/round_id。
20. git diff --check、git status --short、git diff --name-status 均采集真实输出。
21. files_changed 完整列出实际变更文件。
22. 没有提交或修改 `.venv`、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 `.codex-skills`。

## Synthetic Smoke

`project_state/local_reverse_winpty_synthetic_smoke.json`:

- smoke_status: `PASS`
- executed: `True`
- timed_out: `False`
- return_code: `None`
- stdout contains `synthetic_seen=synthetic_input`: `True`
- failure_stage: `read_loop`
- stderr_tail: `winpty read failed:`

The smoke proves the `.py` target is no longer interpreted as `python.exe`; it reached the temporary script, accepted `synthetic_input`, and emitted `synthetic_seen=synthetic_input`. The residual empty winpty read error is preserved as adapter tail evidence and did not block the smoke PASS condition.

## Generated Artifacts

- `project_state/local_reverse_winpty_py_target_spawn_fix.json`: synthetic_smoke_status=`PASS`, executed_real_sample=false, repeated_ippio_jppio_validation=false, candidate=null, known_candidate="", solved=false.
- `project_state/local_reverse_winpty_synthetic_smoke.json`: uses_training_sample=false, candidate=null, known_candidate="", solved=false.

## Tests

- winpty import/API/capability checks: PASS.
- py_compile: PASS.
- `tests/test_local_reverse_console_pair_validator.py`: 32 passed.
- `tests/test_project_state.py`: 158 passed.
- lint-decision: PASS.
- final lint-report/status/git checks are recorded in `pytest_result.txt`.

## Next Suggested Task

Open a separate `reverse_solving` decision for bounded cpp2_2f64e68d `ippio`/`jppio` winpty validation. Do not fold that validation into this tool-integration round.
