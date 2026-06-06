```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1",
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

本轮主线是 **reverse_solving**。

目标：修复上一轮 `cpp2_2f64e68d` runtime pair validation 的 report/pytest 闭环问题。上一轮 runtime artifact 本身保守且可保留：`validation_status=AMBIGUOUS_OUTPUT`、`known_candidate=""`、`solved=false`。但上一轮 `pytest_result.txt` 明确记录 `lint-report` Exit Code 1，`project_state status` 仍显示 `decision_execution_state=READY_FOR_EXECUTION`，同时 `codex_execution_report.md` 却写 `status=SUCCESS` / `acceptance_recommendation=ACCEPTED`，因此不能接受。

本轮只允许做 **report/pytest metadata rework**：

```text
1. 不重新运行 CPP2.exe。
2. 不重新运行 pair validator。
3. 不修改 runtime_pair_validation artifact。
4. 不修改 static triage artifact 或 strcmp handoff artifact。
5. 不修改 artifact_index，除非只读检查发现已经登记的 runtime_pair_validation entry 与现有 artifact 不一致。
6. 重写 project_state/codex_execution_report.md，使其对应本 rework decision。
7. 重写 project_state/pytest_result.txt，记录本 rework 轮真实检查，并确保 lint-report/status 在最终 report 写入后闭合。
```

本轮完成后必须满足：

```text
lint-report exit code 0
project_state status exit code 0
decision_consumed_by_report=True
decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
pytest_result.status=PASSED
report.status=SUCCESS
acceptance_recommendation=ACCEPTED
runtime artifact remains AMBIGUOUS_OUTPUT / solved=false / known_candidate=""
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，`task=Review bounded window discovery diagnostics`，且 `execution_scope=decision_packet_controls_current_round`。`task_packet.task` 不控制本轮。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮 local reverse 事实以 current project_state artifacts 与 artifact_index 为准。

上一轮提交：

```text
commit=3e1c99f56188e6b77701cf351ee45011b1cafbd2
message=feat(cpp2): add runtime pair validation for ippio candidate (AMBIGUOUS_OUTPUT)
decision_id=decision_20260606_cpp2_2f64e68d_runtime_pair_validation_v1
round_id=round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1
```

上一轮有效 runtime artifact：

```text
path=project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
sample_id=cpp2_2f64e68d
analysis_mode=console_runtime_pair_validation
source_artifact_freshness=current
candidate_input=ippio
negative_control_input=jppio
max_runs=2
executed_sample=true
runtime_validated=false
validation_status=AMBIGUOUS_OUTPUT
candidate_run.stdout_tail="Please input a string : \nSorry! Hang on!"
candidate_run.return_code=4294967295
negative_control_run.stdout_tail="Please input a string : \nSorry! Hang on!"
negative_control_run.return_code=4294967295
outputs_differ=false
candidate=null
known_candidate=""
solved=false
blocked_reason=AMBIGUOUS_OUTPUT
candidate_accepted=false
control_rejected=false
```

该 artifact 符合保守原则：candidate/control 输出和返回码一致，因此不能将 `ippio` 标记为已验证答案。

当前 `artifact_index.json` 已登记：

```text
local_reverse_cpp2_2f64e68d_runtime_pair_validation:
  kind=local_reverse_console_pair_runtime_validation
  path=project_state\local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
  freshness=current
  source_run=round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1
  sample_id=cpp2_2f64e68d
```

上一轮闭环失败点：

```text
project_state/pytest_result.txt:
  status=PASSED  # 错误，因为存在失败命令
  Command 7 lint-report:
    Exit Code=1
    error=based_on_decision_id does not match current decision_id
    error=report round_id does not match current decision round_id
    Result=FAILED
  Command 8 project_state status:
    decision_execution_state=READY_FOR_EXECUTION
    decision_ready_for_execution=True

project_state/codex_execution_report.md:
  status=SUCCESS
  acceptance_recommendation=ACCEPTED
  test_results.lint_report=FAILED
  test_results.project_state_status=READY_FOR_EXECUTION
```

这说明上一轮是在写入最终 report 之前运行了 `lint-report/status`，但没有在最终 report 写入后重跑闭环检查。

当前 `negative_results.json` 仍禁止旧 samplereverse blind search、beam/budget 扩展、compare_semantics_agree=false frontier、提交 full solve_reports、无新证据重复 runtime probe、Base64/RC4 breakpoint probe 等方向。本轮不触碰这些方向。

已有能力检查：

```text
1. runtime pair validator 已生成并测试；本轮不得重跑。
2. current runtime pair validation artifact 已存在；本轮不得修改。
3. artifact_index 已登记 runtime pair validation；本轮只做只读核对。
4. 本轮缺口仅是 report/pytest 闭环，不是 solver/tool/runtime 能力缺口。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不运行 reverse_agent.local_reverse_console_pair_validator。
3. 不运行 IDA/Ghidra。
4. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
5. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
6. 不测试任何新输入。
7. 不修改 project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json。
8. 不修改 project_state/local_reverse_cpp2_2f64e68d_static_triage.json。
9. 不修改 project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json。
10. 不修改 project_state/local_reverse_training_status.json。
11. 不修改 project_state/local_reverse_evaluation_queue.json。
12. 不修改 training_materials/local_reverse/status_overlay.json。
13. 不修改 cpp1_7b504c54 的任何 artifact。
14. 不修改 reverse_agent/local_reverse_console_pair_validator.py 或其测试。
15. 不修改 .codex-skills。
16. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
17. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
18. 不把 AMBIGUOUS_OUTPUT 当作 solved。
19. 不写 known_candidate=ippio。
20. 不设置 solved=true。
```

允许：

```text
1. 修改 project_state/codex_execution_report.md。
2. 修改 project_state/pytest_result.txt。
3. 仅当 artifact_index 当前 entry 与现有 runtime artifact 不一致时，修正 project_state/artifact_index.json 并在 report 中说明；默认不改 artifact_index。
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
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
.codex-skills/registry.json
```

只读参考，默认不要修改：

```text
reverse_agent/local_reverse_console_pair_validator.py
tests/test_local_reverse_console_pair_validator.py
reverse_agent/local_reverse_console_validator.py
reverse_agent/local_reverse_direct_strcmp_handoff.py
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
3. 是否确认本轮主线为 reverse_solving。
4. 是否确认本轮是 report/pytest metadata rework，不是重新 runtime validation。
5. 是否确认没有运行 CPP2.exe。
6. 是否确认没有运行 pair validator。
7. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
8. 是否确认没有运行 solver/bruteforce/guided pool/symbolic search。
9. 是否确认 runtime_pair_validation artifact 未修改。
10. 是否确认 runtime_pair_validation artifact 保持 AMBIGUOUS_OUTPUT、known_candidate=""、solved=false。
11. 是否确认 static triage artifact 与 strcmp handoff artifact 未修改。
12. 是否确认 training status、evaluation queue、status overlay 未修改。
13. 是否确认 artifact_index runtime_pair_validation entry 已存在且 freshness=current。
14. 是否确认 codex_report_summary 的 based_on_decision_id 等于 decision_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1。
15. 是否确认 codex_report_summary 的 round_id 等于 round_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1。
16. 是否确认 pytest_result.txt 使用本 rework decision_id/report_id/round_id。
17. 是否确认本轮 `lint-report` 是在最终 report 写入后运行并 Exit Code 0。
18. 是否确认本轮 `project_state status` 显示 decision_consumed_by_report=True。
19. 是否确认本轮 `project_state status` 显示 decision_execution_state=CONSUMED_BY_SUCCESS_REPORT。
20. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

必须重写 `project_state/codex_execution_report.md` 顶部：

```json
{
  "schema_version": 1,
  "report_id": "report_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1",
  "based_on_decision_id": "decision_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -c (readonly consistency check: runtime_pair_validation artifact + artifact_index + no solved promotion)",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": []
}
```

若 artifact_index 必须被修正，必须把 `project_state/artifact_index.json` 加入 files_changed 并解释具体不一致；否则不得修改。

报告正文必须明确：

```text
1. 上一轮 runtime result 保留为 AMBIGUOUS_OUTPUT。
2. 本轮没有重新运行目标样本。
3. 本轮没有重新运行 pair validator。
4. 本轮只是重新生成 report/pytest，使 lint-report/status 在最终 report 写入后闭合。
5. `ippio` 仍不是 known_candidate。
6. `cpp2_2f64e68d` 仍不是 solved。
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
assert v['sample_id']=='cpp2_2f64e68d'
assert v['analysis_mode']=='console_runtime_pair_validation'
assert v['candidate_input']=='ippio'
assert v['negative_control_input']!='ippio'
assert v['max_runs']==2
assert v['validation_status']=='AMBIGUOUS_OUTPUT'
assert v['outputs_differ'] is False
assert v['candidate'] is None
assert v['known_candidate']==''
assert v['solved'] is False
assert v['candidate_accepted'] is False
assert v['control_rejected'] is False
entry=index['latest_artifacts_v2']['local_reverse_cpp2_2f64e68d_runtime_pair_validation']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_console_pair_runtime_validation'
assert entry['sample_id']=='cpp2_2f64e68d'
assert entry['source_run']=='round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1'
print('cpp2 runtime pair report rework consistency OK')
PY
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED/BLOCKED 结果；
5. 本轮 decision_id、round_id、report_id；
6. lint-report Exit Code 0；
7. project_state status 中 decision_consumed_by_report=True 与 decision_execution_state=CONSUMED_BY_SUCCESS_REPORT。
```

执行顺序要求：

```text
1. 先写好本 rework report 草稿。
2. 再运行 lint-report/status。
3. 最后把真实通过结果写入 pytest_result.txt。
4. 不得把“旧 report 不匹配，因此 lint-report 失败”记为 expected pass。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. runtime_pair_validation artifact 缺失或无法解析。
2. runtime_pair_validation artifact 不是 sample_id=cpp2_2f64e68d。
3. runtime_pair_validation artifact 不是 AMBIGUOUS_OUTPUT / solved=false / known_candidate=""。
4. artifact_index 中 runtime_pair_validation entry 缺失或 freshness 不是 current。
5. 需要重新运行 CPP2.exe 才能继续。
6. 需要重新运行 pair validator 才能继续。
7. 需要修改 runtime_pair_validation artifact 才能继续。
8. 需要修改 static triage / strcmp handoff / training status / queue / overlay 才能继续。
9. lint-report 仍然 Exit Code 非 0。
10. project_state status 不显示 CONSUMED_BY_SUCCESS_REPORT。
11. pytest_result 仍把失败命令当作 Overall PASSED。
12. git diff 包含 forbidden files。
```

成功完成的最低标准：

```text
1. report/decision/round 三者匹配本 rework decision。
2. pytest_result 匹配本 rework decision。
3. lint-report Exit Code 0。
4. project_state status 显示 decision_consumed_by_report=True 和 decision_execution_state=CONSUMED_BY_SUCCESS_REPORT。
5. runtime artifact 保持 AMBIGUOUS_OUTPUT、known_candidate=""、solved=false。
6. 未重新运行样本或 pair validator。
7. 未修改 runtime artifact、source artifacts、训练状态或代码。
8. 所有测试与 git 检查真实记录。
```
