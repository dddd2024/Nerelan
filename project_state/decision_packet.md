```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_static_triage_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_static_triage_v1",
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

目标：对训练队列 rank 1 的 `cpp2_2f64e68d` 做有界静态 triage，优先复用项目已有 IDA/IDAPython 工具接口，生成 current static triage artifact，并登记到 `artifact_index.json`。

本轮只做工具取证与证据结构化，不求解、不生成 candidate、不运行样本、不做 runtime validation。

目标样本：

```text
sample_id=cpp2_2f64e68d
relative_path=逆向课程2025春03/CPP2.exe
sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
size_bytes=196689
category=cpp
tags=local, reverse, cpp, pe
queue_rank=1
queue_allowed_actions=static_triage
queue_forbidden_actions=runtime_probe, bruteforce, upload_binary
```

预期产物：

```text
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
```

预期登记：

```text
artifact_index.latest_artifacts.local_reverse_cpp2_2f64e68d_static_triage
artifact_index.latest_artifacts_v2.local_reverse_cpp2_2f64e68d_static_triage
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，`task=Review bounded window discovery diagnostics`，且明确 `project_state/decision_packet.md` 是当前执行权威。`task_packet.task` 不控制本轮。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮 local reverse 事实以 `local_reverse_training_status.json`、`local_reverse_evaluation_queue.json`、`artifact_index.json` 为准。

上一轮 rework 已闭合：

```text
report_id=report_20260606_cpp1_7b504c54_training_status_sync_rework_v1
based_on_decision_id=decision_20260606_cpp1_7b504c54_training_status_sync_rework_v1
round_id=round_20260606_cpp1_7b504c54_training_status_sync_rework_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt` 已闭合：

```text
status=PASSED
lint-decision=OK
pytest_training_status=33 passed
lint-report=OK
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

当前训练状态：

```text
status_summary.solved=2
status_summary.blocked=4
status_summary.needs_triage=0
status_summary.inventory_only=23
cpp1_7b504c54.training_status=solved
cpp1_7b504c54.known_candidate=WeKnowItOk
```

当前评估队列：

```text
items[0].rank=1
items[0].sample_id=cpp2_2f64e68d
items[0].relative_path=逆向课程2025春03/CPP2.exe
items[0].proposed_next_mainline=tool_integration
items[0].allowed_actions=["static_triage"]
items[0].forbidden_actions=["runtime_probe", "bruteforce", "upload_binary"]
```

当前 `artifact_index.json` 已登记 `cpp1_7b504c54` 的 current artifacts：

```text
local_reverse_cpp1_7b504c54_static_triage=current
local_reverse_cpp1_7b504c54_xor_handoff=current
local_reverse_cpp1_7b504c54_runtime_validation=current
local_reverse_cpp1_7b504c54_training_status_sync=current
```

当前未发现 `local_reverse_cpp2_2f64e68d_static_triage` 的 current artifact；本轮目标就是建立该 artifact。

已有工具接口检查：

```text
1. reverse_agent/tool_runners.py 已有 run_ida_evidence(file_path, artifacts_dir, log, ida_executable, ida_script_path, timeout_seconds)。
2. reverse_agent/tool_runners.py 已有默认 IDA 脚本解析逻辑：reverse_agent/ida_scripts/collect_evidence.py。
3. run_ida_evidence 会生成 *_ida_evidence.json，并提取 strings/functions/compare_contexts/local_check_contexts/control_id_contexts/string_xrefs/validation_function_candidates/decompiler_snippets/solver_hints。
4. tool_runners.py 也有 OllyDbg/CompareProbe 接口，但当前队列明确 forbidden runtime_probe；本轮不得使用。
5. 成熟工具优先，不要在项目中重写反汇编器、反编译器、PE parser 或 debugger。
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

本轮不触碰旧 samplereverse 搜索、beam、Base64/RC4、CompareProbe 或 runtime probe 方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行目标样本。
2. 不做 runtime validation。
3. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
4. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
5. 不生成 candidate，不写 known_candidate，不标记 solved。
6. 不修改 local_reverse_training_status.json。
7. 不修改 local_reverse_evaluation_queue.json。
8. 不修改 training_materials/local_reverse/status_overlay.json。
9. 不修改 cpp1_7b504c54 的任何 artifact。
10. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
11. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
12. 不新增重复 IDA/Ghidra/debugger 接口。
13. 不把 IDA missing/timeout 当作样本分析失败；应写成 blocked/static_triage_not_completed artifact。
14. 不将 stale/unknown artifact 当 current evidence。
```

允许：

```text
1. 使用已有 run_ida_evidence / collect_evidence.py 对 cpp2_2f64e68d 执行一次有界 IDA static extraction。
2. 若 IDA 不可用或目标 binary 不存在，生成清晰的 static_triage artifact，状态为 BLOCKED 或 NOT_ATTEMPTED，并记录 blocked_reason。
3. 新增 project_state/local_reverse_cpp2_2f64e68d_static_triage.json。
4. 更新 project_state/artifact_index.json 登记该 artifact。
5. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
6. 如现有代码没有可直接运行的 CLI 入口，可新增一个很薄的 wrapper，但必须复用现有 run_ida_evidence，不得重写成熟工具能力。
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
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
.codex-skills/registry.json
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
```

按需读取：

```text
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
README.md
pyproject.toml
requirements.txt
requirements-dev.txt
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
4. 是否确认目标样本为 cpp2_2f64e68d，而不是 cpp1_7b504c54。
5. 是否确认 cpp2_2f64e68d 是 evaluation_queue rank 1。
6. 是否确认 queue 只允许 static_triage，禁止 runtime_probe/bruteforce/upload_binary。
7. 是否检查了已有 IDA/IDAPython 接口。
8. 是否复用了 run_ida_evidence / collect_evidence.py，或明确说明为什么只能生成 blocked artifact。
9. 是否确认没有新增重复 IDA/Ghidra/debugger 接口。
10. 是否确认没有运行目标样本。
11. 是否确认没有运行 OllyDbg/Frida/hook/emulator/CompareProbe。
12. 是否确认没有运行 solver/bruteforce/guided pool/symbolic search。
13. 是否确认没有生成 candidate/known_candidate/solved=true。
14. 是否生成 project_state/local_reverse_cpp2_2f64e68d_static_triage.json。
15. 是否在 artifact_index.latest_artifacts 与 latest_artifacts_v2 登记 local_reverse_cpp2_2f64e68d_static_triage。
16. 是否确认 artifact freshness=current。
17. 是否确认若 IDA 不可用，则 blocked_reason 清晰，且不把它当作样本失败。
18. 是否确认未修改 training_status/evaluation_queue/status_overlay。
19. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
20. 是否确认 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
21. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

产物最低字段：

```text
schema_version=1
sample_id=cpp2_2f64e68d
mainline=tool_integration
analysis_mode=local_reverse_single_sample_static_triage
relative_path=逆向课程2025春03/CPP2.exe
sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
size_bytes=196689
source_tool=IDA or fallback_static_triage
source_artifact_freshness=current
executed_sample=false
static_only=true
runtime_validated=false
candidate=null
known_candidate=""
solved=false
status=STATIC_TRIAGE_COMPLETE or BLOCKED
blocked_reason="" or TARGET_MISSING / IDA_MISSING / IDA_TIMEOUT / IDA_OUTPUT_MISSING / IDA_OUTPUT_UNPARSEABLE
ida_attempted=true/false
ida_success=true/false
ida_output_path="..." or ""
strings_summary
functions_summary
compare_contexts_summary
local_check_contexts_summary
string_xrefs_summary
validation_function_candidates_summary
decompiler_snippets_summary
solver_hints_summary
generated_at=<UTC>
```

若 IDA 成功，artifact 应尽量压缩并结构化：

```text
1. 记录入口地址。
2. 记录关键字符串，尤其是 prompt/success/failure/length/error 字符串。
3. 记录比较函数调用点或局部校验函数候选。
4. 记录 main 或 validation function 的反编译片段摘要。
5. 记录 solver_hints，但不得直接求解。
6. 记录原始 IDA evidence 的路径或摘要，不提交 IDA database。
```

必须更新 artifact_index：

```text
latest_artifacts.local_reverse_cpp2_2f64e68d_static_triage = "project_state\\local_reverse_cpp2_2f64e68d_static_triage.json"

latest_artifacts_v2.local_reverse_cpp2_2f64e68d_static_triage = {
  kind="local_reverse_single_sample_static_triage",
  path="project_state\\local_reverse_cpp2_2f64e68d_static_triage.json",
  freshness="current",
  source_run="round_20260606_cpp2_2f64e68d_static_triage_v1",
  sha256=<actual file sha256>,
  size_bytes=<actual size>,
  modified_at=<actual UTC timestamp>,
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

按需允许新增薄 wrapper 与测试：

```text
reverse_agent/local_reverse_static_triage.py
tests/test_local_reverse_static_triage.py
```

仅当没有现有 CLI 能调用 `run_ida_evidence` 时才新增 wrapper；wrapper 必须薄，不得重写 IDA/Ghidra/PE parser 能力。

不得修改：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_7b504c54_*.json
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/olly_scripts/*
.codex-skills/*
solve_reports/*
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m pytest -q tests/test_project_state.py
# 如果新增 wrapper，则运行：
python -m py_compile reverse_agent/local_reverse_static_triage.py
python -m pytest -q tests/test_local_reverse_static_triage.py
# 执行静态 triage 命令；若 IDA/target 缺失，必须生成 BLOCKED artifact，而不是崩溃。
python -m reverse_agent.local_reverse_static_triage --sample-id cpp2_2f64e68d --relative-path "逆向课程2025春03/CPP2.exe" --sha256 2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1 --out project_state/local_reverse_cpp2_2f64e68d_static_triage.json
python - <<'PY'
import json
from pathlib import Path
triage=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_static_triage.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
assert triage['sample_id']=='cpp2_2f64e68d'
assert triage['executed_sample'] is False
assert triage['static_only'] is True
assert triage['runtime_validated'] is False
assert triage['candidate'] is None
assert triage['known_candidate']==''
assert triage['solved'] is False
assert triage['status'] in ('STATIC_TRIAGE_COMPLETE','BLOCKED')
entry=index['latest_artifacts_v2']['local_reverse_cpp2_2f64e68d_static_triage']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_single_sample_static_triage'
assert entry['sample_id']=='cpp2_2f64e68d'
assert entry['source_run']=='round_20260606_cpp2_2f64e68d_static_triage_v1'
print('cpp2 static triage consistency OK')
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
5. 本轮 decision_id、round_id、report_id。
```

如果 IDA 或本地目标文件不可用，但 artifact 正确记录 `status=BLOCKED` 且测试闭合，Codex 报告可用 `status=SUCCESS`，但必须把 implementation result 说清楚：完成的是 bounded static triage attempt / blocked artifact，而不是完成 IDA triage。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. 当前 decision_packet 无法解析或 decision_meta 缺失。
2. skill profile 不在 registry active skills 中。
3. evaluation_queue rank 1 不再是 cpp2_2f64e68d，需要报告状态变化，不要猜测。
4. artifact_index 已存在 current local_reverse_cpp2_2f64e68d_static_triage，且 provenance 指向当前样本；不要重复生成，转为 metadata audit。
5. 需要运行目标样本或 runtime probe 才能继续。
6. 需要运行 debugger/hook/emulator/CompareProbe 才能继续。
7. 需要修改 training_status/evaluation_queue/status_overlay 才能继续。
8. 需要新增重型 disassembler/PE parser 才能继续。
9. 需要提交 binary、IDA DB、solve_reports 或临时目录才可继续。
10. lint-report 或 project_state status 无法闭合。
11. git diff 包含 forbidden files。
```

成功完成的最低标准：

```text
1. 生成 cpp2_2f64e68d static triage artifact，状态为 STATIC_TRIAGE_COMPLETE 或 BLOCKED。
2. artifact 明确 executed_sample=false、runtime_validated=false、solved=false。
3. artifact_index 登记 current triage artifact。
4. 未运行样本，未做 runtime。
5. 未改训练状态/队列/overlay。
6. report/pytest_result 与本 decision_id/round_id 匹配。
7. 所有测试与 git 检查真实记录。
```
