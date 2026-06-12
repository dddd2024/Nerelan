```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_rework_cpp1_2f6fcb63_static_triage_closeout_v1",
  "round_id": "round_20260612_rework_cpp1_2f6fcb63_static_triage_closeout_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

修复 `cpp1_2f6fcb63_static_triage_v1` 的 closeout 状态问题。不得重新推进样本分析；本轮只修复 report、pytest_result、gate、files_changed、round archive 和 git diff 一致性。

允许保留已生成的：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
```

但必须把本轮状态修到可审计。

必须完成：

1. 保留并验证 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`，它应仍是 blocked metadata artifact，而不是 solved artifact。
2. 修复 `codex_execution_report.md` 内部状态冲突，不允许 summary 与正文分别写 `REJECTED` 和 `ACCEPTED`。
3. 修复 `pytest_result.txt` summary，不得在真实命令失败时写 `PASSED`。
4. 清理或还原 scope 外 diff，让 `git diff --name-only` 只剩本轮允许文件，或者报告明确 BLOCKED。
5. 让 `project_state/gates/final_gate_result.json` 最终为 `PASSED`；若不能，报告 `FAILED` 或 `BLOCKED`，不得写 `SUCCESS` / `ACCEPTED`。
6. archive 本轮 rework round。

## 2. Current Evidence

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 已生成，`sample_id` 正确，`executed_sample=false`，`static_only=true`，`runtime_validated=false`，`candidate=null`，结果为 `tool_status=blocked`，`blocked_reason=STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`。
- 当前 `project_state/gates/final_gate_result.json` 为 `FAILED`。
- 当前 `pytest_result.txt` summary 写 `PASSED`，但真实命令记录包含 `lint-report`、`doctor`、`doctor --json`、`final-check` 失败。
- 当前 `codex_execution_report.md` 顶部 summary 写 `LIMITED_SUCCESS` / `REJECTED`，正文又写 `SUCCESS` / `ACCEPTED`，报告自相矛盾。
- 当前 `git diff --name-only` 包含 scope 外文件：`project_state/model_gate.json`、`project_state/task_packet.json`、`reverse_agent/harness.py`、`reverse_agent/project_state.py`、`tests/test_project_state.py` 等。
- 本轮主线是 `engineering_branch`，不是 `tool_integration` 或 `reverse_solving`；只修 closeout，不继续运行 static triage、IDA、solver、runtime probe 或 candidate search。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 应为 active。
- `task_packet.json` 仍可能包含旧 samplereverse 求解背景，只能 advisory，不能覆盖本轮 decision。

## 3. Do Not Do

- 不重新运行目标样本。
- 不重新运行 IDA static triage，除非仅用于验证现有 artifact 且不会产生新样本分析事实；优先只验证已有 JSON。
- 不运行 runtime probe、debugger、emulator、solver、candidate search、bruteforce、validation 或 harness campaign。
- 不生成 candidate、flag 或答案。
- 不推进任何非 closeout 修复工作。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不上传 raw sample、sample binary、IDA database sidecar 或完整 `solve_reports/`。
- 不修改 `.codex-skills/`。
- 不修改源码、测试、schema、tool interface、solver、harness、IDA/Ghidra/debugger integration。
- 不把 final-check 失败写成 `SUCCESS` 或 `ACCEPTED`。
- 不把失败命令写成 `PASSED`。
- 不用手工编辑 summary 掩盖真实失败。

## 4. Files To Inspect

必须检查：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/rounds/round_20260612_local_reverse_cpp1_2f6fcb63_static_triage_v1/round_manifest.json`

必须运行或记录：

```bash
git status --short
git diff --name-only
```

不得默认检查：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- IDA database sidecars beyond bounded `project_state` sidecar check

## 5. Required Audit

Codex 必须：

1. 确认工作目录为 `F:\reverse-agent`。
2. 记录启动 baseline：`git status --short` 与 `git diff --name-only`。
3. 读取默认 project_state 文件并确认本 decision 是当前执行权威。
4. 确认 skill profiles active。
5. 验证 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 字段：
   - `sample_id == cpp1_2f6fcb63`
   - `analysis_mode == single_sample_static_triage`
   - `static_only == true`
   - `executed_sample == false`
   - `runtime_validated == false`
   - `candidate` 为 `null` 或空
   - 不得写 solved
6. 清理或还原不属于本轮 scope 的文件：
   - `reverse_agent/harness.py`
   - `reverse_agent/project_state.py`
   - `tests/test_project_state.py`
   - `project_state/model_gate.json`
   - `project_state/task_packet.json`
   - 以及其他不属于本轮 scope 的 diff 文件
7. 统一 `codex_execution_report.md` 状态：若 final-check 通过，才可写 `SUCCESS` / `ACCEPTED`；否则必须写 `FAILED`、`BLOCKED` 或 `LIMITED_SUCCESS` 并推荐返工。
8. `files_changed` 必须覆盖真实 git diff，或者清理 diff 中不属于本轮的文件。
9. `generated_artifacts` 必须包含 round archive 文件和 gate 文件。
10. `pytest_result.txt` 必须真实记录每条命令 stdout/stderr/exit code，并使 summary 与真实结果一致。
11. 重新运行 final-check，必须 `PASSED` 才能给 `ACCEPTED`。
12. archive 新的 rework round。

## 6. Implementation Scope

允许修改：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/artifact_index.json` only if needed to keep the existing cpp1 triage artifact registration consistent
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` only if fixing metadata consistency, not changing the analysis result
- `project_state/rounds/round_20260612_rework_cpp1_2f6fcb63_static_triage_closeout_v1/*`

必须还原或移出本轮范围：

- `reverse_agent/harness.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/model_gate.json`
- `project_state/task_packet.json`
- any other source/test/schema/tool-interface file

不得修改：

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- sample binaries
- IDA database sidecars
- solver modules
- harness modules
- IDA/Ghidra/debugger integration code
- project gate/schema code
- tests

If completing the closeout requires source/test/schema/tool-interface changes, stop and report `BLOCKED`.

## 7. Tests

必须运行并记录真实 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
git diff --name-only
python -m reverse_agent.project_gate preflight --state-dir project_state
python -c "import json, pathlib; p=pathlib.Path('project_state/local_reverse_cpp1_2f6fcb63_static_triage.json'); d=json.loads(p.read_text(encoding='utf-8')); assert d['sample_id']=='cpp1_2f6fcb63'; assert d['analysis_mode']=='single_sample_static_triage'; assert d['static_only'] is True; assert d['executed_sample'] is False; assert d['runtime_validated'] is False; assert d.get('candidate') in (None, ''); print('triage artifact ok:', d.get('tool_status'), d.get('blocked_reason',''))"
powershell -NoProfile -Command "$x=Get-ChildItem -Path project_state -Recurse -Include *.i64,*.id0,*.id1,*.nam,*.til -ErrorAction SilentlyContinue; if ($x) { $x.FullName; exit 1 } else { 'no ida db sidecars' }"
python -m pytest tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_rework_cpp1_2f6fcb63_static_triage_closeout_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

`pytest_result.txt` 必须记录每条命令的真实输出和 exit code。不得使用 placeholder，不得删掉失败输出。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 无法清理 scope 外源码/测试 diff。
- final-check 仍失败。
- command-plan 仍为 WARN 且 final gate 不接受。
- pytest_result 需要伪造 `PASSED` 才能通过。
- report/decision/pytest/round_id 不匹配。
- 需要修改源码、测试、schema 或工具接口。
- IDA database sidecar 仍残留。
- 无法判断 baseline 与本轮修改边界。
