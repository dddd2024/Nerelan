```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1",
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

目标：修复上一轮 `cpp2_2f64e68d` static triage 产物的 schema 闭环问题。上一轮已经成功生成 IDA static triage artifact 并登记 artifact_index，但 artifact 缺少 decision 要求的最低字段，导致审计结论为 `REWORK_REQUIRED`。

本轮只允许做 **metadata/schema rework**：

```text
1. 不重新运行 IDA。
2. 不运行目标样本。
3. 不进行 runtime validation。
4. 不生成 candidate，不写 known_candidate，不标记 solved。
5. 只补齐 project_state/local_reverse_cpp2_2f64e68d_static_triage.json 的最低 schema 字段。
6. 因 artifact 内容变更，更新 artifact_index 中该 artifact 的 sha256、size_bytes、modified_at。
7. 重写 codex_execution_report.md 和 pytest_result.txt，使其对应本 rework decision。
8. 补充 readonly consistency check，必须实际断言本轮缺失字段已经存在且语义正确。
```

上一轮已完成的有效事实保留：

```text
sample_id=cpp2_2f64e68d
relative_path=逆向课程2025春03/CPP2.exe
sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
size_bytes=196689
queue_rank=1
source_tool=IDA
tool_status=success
interesting_strings=50
functions=30
compare_contexts=2
solver_profile_hypotheses=string_compare_password_checker, standard_input_based, strcmp_direct_compare
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。当前执行权威是本 `project_state/decision_packet.md`。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。

上一轮 static triage 已执行并生成 artifact：

```text
commit=dd7042a8c97372fde41e701afdfc1ec8385e212a
message=Add cpp2 static triage artifact and closeout metadata
report_id=report_20260606_cpp2_2f64e68d_static_triage_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_static_triage_v1
round_id=round_20260606_cpp2_2f64e68d_static_triage_v1
status=SUCCESS
```

上一轮 report/pytest 已匹配，但 artifact schema 不完整：

```text
actual artifact path=project_state/local_reverse_cpp2_2f64e68d_static_triage.json
actual analysis_mode=single_sample_static_triage
actual tool_status=success
actual source_tool=IDA
actual candidate=null
actual known_candidate=""
```

上一轮审计失败点：

```text
1. analysis_mode 没有使用要求值 local_reverse_single_sample_static_triage。
2. 缺少 source_artifact_freshness=current。
3. 缺少 status=STATIC_TRIAGE_COMPLETE or BLOCKED。
4. 缺少 solved=false。
5. 缺少 ida_attempted=true/false。
6. 缺少 ida_success=true/false。
7. 缺少 ida_output_path 字段。
8. readonly consistency check 没有证明检查了上述字段。
```

当前 artifact_index 已登记：

```text
local_reverse_cpp2_2f64e68d_static_triage:
  kind=local_reverse_single_sample_static_triage
  path=project_state\local_reverse_cpp2_2f64e68d_static_triage.json
  freshness=current
  source_run=round_20260606_cpp2_2f64e68d_static_triage_v1
  sample_id=cpp2_2f64e68d
```

本轮修复后必须把 `source_run` 更新为本 rework round：

```text
source_run=round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1
```

当前 `negative_results.json` 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. use compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat dynamic-probe directions without new evidence
6. run Base64/RC4 breakpoint probe before real lhs producer identification
```

本轮不触碰旧 samplereverse 搜索、beam、Base64/RC4、CompareProbe、runtime probe 或任何求解方向。

已有工具接口检查：

```text
1. IDA/IDAPython runner 已存在且上一轮已成功使用。
2. 本轮不需要也不得再次运行 IDA。
3. 本轮不需要新增 wrapper、runner、parser、solver 或测试框架。
4. 成熟工具输出已被压缩到 static triage artifact；本轮只做 schema 补齐。
```

---

## 3. Do Not Do

严禁：

```text
1. 不重新运行 IDA/Ghidra。
2. 不运行目标样本。
3. 不做 runtime validation。
4. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
5. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
6. 不生成 candidate。
7. 不写 known_candidate。
8. 不标记 solved=true。
9. 不修改 local_reverse_training_status.json。
10. 不修改 local_reverse_evaluation_queue.json。
11. 不修改 training_materials/local_reverse/status_overlay.json。
12. 不修改 cpp1_7b504c54 的任何 artifact。
13. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
14. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
15. 不新增或修改 IDA/Ghidra/debugger 接口。
16. 不修改 reverse_agent/tool_runners.py。
17. 不修改 reverse_agent/ida_scripts/collect_evidence.py。
18. 不把 static triage evidence 当作已求解结果。
```

允许：

```text
1. 修改 project_state/local_reverse_cpp2_2f64e68d_static_triage.json，补齐 schema 字段。
2. 修改 project_state/artifact_index.json，更新该 artifact 的 sha256、size_bytes、modified_at、source_run。
3. 修改 project_state/codex_execution_report.md。
4. 修改 project_state/pytest_result.txt。
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
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
.codex-skills/registry.json
```

只读参考，默认不要修改：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
reverse_agent/local_reverse_single_sample_static_triage.py
tests/test_local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
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
3. 是否确认本轮主线为 tool_integration。
4. 是否确认本轮是 static triage schema rework，而不是重新 triage。
5. 是否确认没有重新运行 IDA/Ghidra。
6. 是否确认没有运行目标样本。
7. 是否确认没有运行 runtime validation/debugger/hook/emulator/CompareProbe。
8. 是否确认没有运行 solver/bruteforce/guided pool/symbolic search。
9. 是否确认没有修改训练状态、评估队列或 status overlay。
10. 是否确认没有修改 cpp1 artifacts。
11. 是否确认 artifact 现在包含 analysis_mode=local_reverse_single_sample_static_triage。
12. 是否确认 artifact 现在包含 source_artifact_freshness=current。
13. 是否确认 artifact 现在包含 status=STATIC_TRIAGE_COMPLETE。
14. 是否确认 artifact 现在包含 solved=false。
15. 是否确认 artifact 现在包含 ida_attempted=true。
16. 是否确认 artifact 现在包含 ida_success=true。
17. 是否确认 artifact 现在包含 ida_output_path 字段。
18. 是否确认 artifact 仍保持 executed_sample=false/static_only=true/runtime_validated=false/candidate=null/known_candidate=""。
19. 是否确认 artifact_index.latest_artifacts_v2.local_reverse_cpp2_2f64e68d_static_triage 的 sha256、size_bytes、modified_at 已按修改后的 artifact 重算。
20. 是否确认 artifact_index 中 source_run 更新为 round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1。
21. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
22. 是否确认 pytest_result.txt 与本 decision_id/report_id/round_id 匹配。
23. 是否确认 readonly consistency check 实际断言 schema 字段。
24. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

必须把 `project_state/local_reverse_cpp2_2f64e68d_static_triage.json` 补齐为至少包含以下字段和值：

```json
{
  "analysis_mode": "local_reverse_single_sample_static_triage",
  "source_artifact_freshness": "current",
  "status": "STATIC_TRIAGE_COMPLETE",
  "executed_sample": false,
  "static_only": true,
  "runtime_validated": false,
  "candidate": null,
  "known_candidate": "",
  "solved": false,
  "ida_attempted": true,
  "ida_success": true,
  "ida_output_path": "<existing summarized IDA output path or empty string if raw temp was intentionally removed>",
  "blocked_reason": ""
}
```

保留已有有效字段和 triage 内容：

```text
schema_version
sample_id
relative_path
mainline
sha256
size_bytes
file_type
category
tags
queue_rank
triage.input_apis
triage.interesting_strings
triage.functions
triage.compare_contexts
triage.validation_function_candidates
triage.solver_profile_hypotheses
triage.decompiler_snippets
recommended_next_action
```

`ida_output_path` 规则：

```text
1. 如果 artifact 已经包含或可从上一轮 report 推导出 raw IDA evidence path，可写相对路径字符串。
2. 如果上一轮已删除 raw temp evidence 目录，则写空字符串 ""，但必须在 report 中说明 raw temporary IDA evidence directory was removed after extraction。
3. 不允许为了填该字段重新运行 IDA。
```

必须更新 artifact_index：

```text
latest_artifacts.local_reverse_cpp2_2f64e68d_static_triage 保持指向 project_state\\local_reverse_cpp2_2f64e68d_static_triage.json。

latest_artifacts_v2.local_reverse_cpp2_2f64e68d_static_triage = {
  kind="local_reverse_single_sample_static_triage",
  path="project_state\\local_reverse_cpp2_2f64e68d_static_triage.json",
  freshness="current",
  source_run="round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1",
  sha256=<modified artifact actual sha256>,
  size_bytes=<modified artifact actual size>,
  modified_at=<current UTC timestamp>,
  sample_id="cpp2_2f64e68d"
}
```

允许修改：

```text
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_7b504c54_*.json
reverse_agent/local_reverse_single_sample_static_triage.py
tests/test_local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/olly_scripts/*
.codex-skills/*
solve_reports/*
project_state/triage_*
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python - <<'PY'
import json
from pathlib import Path
triage=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_static_triage.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
assert triage['schema_version']==1
assert triage['sample_id']=='cpp2_2f64e68d'
assert triage['mainline']=='tool_integration'
assert triage['analysis_mode']=='local_reverse_single_sample_static_triage'
assert triage['source_artifact_freshness']=='current'
assert triage['status']=='STATIC_TRIAGE_COMPLETE'
assert triage['executed_sample'] is False
assert triage['static_only'] is True
assert triage['runtime_validated'] is False
assert triage['candidate'] is None
assert triage['known_candidate']==''
assert triage['solved'] is False
assert triage['ida_attempted'] is True
assert triage['ida_success'] is True
assert 'ida_output_path' in triage
assert triage['blocked_reason']==''
entry=index['latest_artifacts_v2']['local_reverse_cpp2_2f64e68d_static_triage']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_single_sample_static_triage'
assert entry['sample_id']=='cpp2_2f64e68d'
assert entry['source_run']=='round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1'
print('cpp2 static triage schema rework consistency OK')
PY
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

建议追加：

```bash
python -m pytest -q tests/test_project_state.py
```

严禁在测试中重新运行：

```text
python -m reverse_agent.local_reverse_single_sample_static_triage ...
IDA/Ghidra/debugger/runtime validation/CompareProbe/solver/bruteforce
```

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED/BLOCKED 结果；
5. 本轮 decision_id、round_id、report_id。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. 当前 decision_packet 无法解析或 decision_meta 缺失。
2. skill profile 不在 registry active skills 中。
3. project_state/local_reverse_cpp2_2f64e68d_static_triage.json 缺失或无法解析。
4. artifact 不是 sample_id=cpp2_2f64e68d。
5. artifact 现有内容显示 tool_status 不是 success，或 source_tool 不是 IDA；此时不得写 STATIC_TRIAGE_COMPLETE，应报告冲突。
6. 需要重新运行 IDA/Ghidra 才能继续。
7. 需要运行样本、runtime validation、debugger、hook、emulator、CompareProbe 才能继续。
8. 需要修改训练状态、评估队列或 overlay 才能继续。
9. 需要修改代码或测试文件才可继续。
10. 无法重算 artifact_index sha256/size/modified_at。
11. lint-report 或 project_state status 无法闭合。
12. git diff 包含 forbidden files。
13. report 或 pytest_result 仍引用旧 static_triage_v1 decision/round。
```

成功完成的最低标准：

```text
1. cpp2 static triage artifact 补齐 schema 字段。
2. artifact 明确 status=STATIC_TRIAGE_COMPLETE、source_artifact_freshness=current、solved=false。
3. artifact_index 登记已更新到本 rework round，hash/size/time 对应修改后 artifact。
4. 未重新运行 IDA，未运行样本，未做 runtime。
5. 未修改训练状态、队列、overlay 或代码。
6. report/pytest_result 与本 rework decision_id/round_id 匹配。
7. readonly consistency check 实际覆盖缺失字段。
```
