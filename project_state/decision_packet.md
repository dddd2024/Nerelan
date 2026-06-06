```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_7b504c54_xor_handoff_report_metadata_rework_v1",
  "round_id": "round_20260605_cpp1_7b504c54_xor_handoff_report_metadata_rework_v1",
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

目标：修复上一轮 `decision_20260605_cpp1_7b504c54_xor_handoff_v1` 的报告/metadata 小不一致，不重新推进样本求解。

上一轮功能结果可接受：`project_state/local_reverse_cpp1_7b504c54_xor_handoff.json` 已生成，保持 `static_only=true`、`runtime_validated=false`、`candidate=null`、`known_candidate=""`、`validation_status=not_validated`、`solved=false`，并计算出 static candidate `WeKnowItOk`。但审计发现两个限制项：

```text
1. codex_execution_report.md 的 XOR arrays 摘要与 handoff artifact 实际内容不一致。
2. artifact_index.json 中 local_reverse_cpp1_7b504c54_xor_handoff.kind 使用了样本限定名称 `local_reverse_cpp1_7b504c54_xor_handoff`，而 decision 预期是通用 kind `local_reverse_cpp1_xor_handoff`。
```

本轮只允许修正这些报告/metadata 问题。不得重新运行样本，不得 runtime validation，不得把 `WeKnowItOk` 写入 `known_candidate`，不得标记 solved。

预期处理：

```text
1. 修正 project_state/codex_execution_report.md 中 arrays 摘要，使其与 project_state/local_reverse_cpp1_7b504c54_xor_handoff.json 一致：
   byte_427A30 = 0102030405060708090a
   byte_427A3C = 1112131415161718191a
   byte_427A48 = 4c7e507d7c645a6f5470
2. 将 project_state/artifact_index.json 中 local_reverse_cpp1_7b504c54_xor_handoff.kind 调整为 `local_reverse_cpp1_xor_handoff`。
3. 如果 Codex 判断不应改 kind，必须在 report 中明确说明保留样本限定 kind 的理由，并给出兼容性风险；但优先执行第 2 条。
4. 重新生成 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，使当前 decision 被当前 SUCCESS report 消费。
```

---

## 2. Current Evidence

当前 `project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。当前执行权威是 `project_state/decision_packet.md`。

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态：

```text
state_build_id=state_20260602_053948_4e3984041cd7
state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 `codex_execution_report.md` 当前摘要：

```text
report_id=report_20260605_cpp1_7b504c54_xor_handoff_v1
based_on_decision_id=decision_20260605_cpp1_7b504c54_xor_handoff_v1
round_id=round_20260605_cpp1_7b504c54_xor_handoff_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt` 当前摘要：

```text
status=PASSED
Total Commands=9
Passed=9
Failed=0
lint-report=OK
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

当前 handoff artifact 为事实源，内容如下：

```text
path=project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
sample_id=cpp1_7b504c54
analysis_mode=cpp1_7b504c54_static_xor_handoff
mainline=reverse_solving
executed_sample=false
static_only=true
runtime_validated=false
source_artifact_freshness=current
input_length=10
transform_formula="candidate[i] = byte_427A30[9-i] ^ byte_427A3C[i] ^ byte_427A48[i]"
byte_427A30.bytes_hex=0102030405060708090a
byte_427A3C.bytes_hex=1112131415161718191a
byte_427A48.bytes_hex=4c7e507d7c645a6f5470
static_candidate_hex=57654b6e6f7749744f6b
static_candidate_text=WeKnowItOk
static_candidate_printable=true
forward_transform_verified=true
candidate=null
known_candidate=""
validation_status=not_validated
solved=false
status=READY_FOR_STATIC_REVIEW
```

当前 `artifact_index.json` 已登记：

```text
artifact key=local_reverse_cpp1_7b504c54_xor_handoff
kind=local_reverse_cpp1_7b504c54_xor_handoff
path=project_state\local_reverse_cpp1_7b504c54_xor_handoff.json
freshness=current
source_run=round_20260605_cpp1_7b504c54_xor_handoff_v1
sample_id=cpp1_7b504c54
```

本轮需要把 kind 调整为：

```text
kind=local_reverse_cpp1_xor_handoff
```

上一轮 report 中的错误数组摘要为：

```text
byte_427A30: 0102030405060708090a
byte_427A3C: 00001112131415161718
byte_427A48: 191a00004c7e507d7c64
```

应改为：

```text
byte_427A30: 0102030405060708090a
byte_427A3C: 1112131415161718191a
byte_427A48: 4c7e507d7c645a6f5470
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

本轮不触碰这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不重新运行样本。
2. 不做 runtime validation。
3. 不运行 debugger/runtime probe/hook/emulator。
4. 不运行 IDA/Ghidra。
5. 不重新运行 static triage。
6. 不重新运行 XOR handoff CLI，除非只是为了确认 artifact 可解析且不改 handoff artifact；默认不运行。
7. 不运行 solver/bruteforce/guided pool/constraint recovery。
8. 不修改 project_state/local_reverse_cpp1_7b504c54_xor_handoff.json。
9. 不修改 project_state/local_reverse_cpp1_7b504c54_static_triage.json。
10. 不修改 project_state/local_reverse_training_status.json。
11. 不修改 project_state/local_reverse_evaluation_queue.json。
12. 不修改 training_materials/local_reverse/status_overlay.json。
13. 不修改 reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py。
14. 不修改 tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py。
15. 不写 known_candidate。
16. 不标记 solved。
17. 不把 static_candidate_text 当 validated candidate。
18. 不提交本地 binary、IDA sidecar、raw temp、project_state/triage_* 或 full solve_reports。
19. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
20. 不修改 .codex-skills。
```

允许：

```text
1. 修改 project_state/artifact_index.json 中 local_reverse_cpp1_7b504c54_xor_handoff.kind。
2. 修改 project_state/codex_execution_report.md，修正数组摘要并记录本轮 rework。
3. 修改 project_state/pytest_result.txt，记录本轮真实测试结果。
4. 只读检查 project_state/local_reverse_cpp1_7b504c54_xor_handoff.json。
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
project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
.codex-skills/registry.json
```

按需读取：

```text
project_state/local_reverse_cpp1_7b504c54_static_triage.json
reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py
tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py
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
4. 是否确认本轮只修正 report/metadata，不继续求解 cpp1_7b504c54。
5. 是否确认未运行样本，未做 runtime validation。
6. 是否确认未运行 IDA/Ghidra/debugger/runtime probe/hook/emulator。
7. 是否确认未运行 solver/bruteforce/guided pool/constraint recovery。
8. 是否确认未修改 XOR handoff artifact。
9. 是否确认未修改 static triage artifact。
10. 是否确认未修改 training_status / evaluation_queue。
11. 是否确认未写 known_candidate。
12. 是否确认未标记 solved。
13. 是否确认 report 中 arrays 摘要与 handoff artifact 一致。
14. 是否确认 artifact_index kind 已改为 `local_reverse_cpp1_xor_handoff`，或解释未修改理由。
15. 是否确认 artifact_index freshness/current/source_run/sample_id 未被降级或覆盖。
16. 是否确认 codex_report_summary.generated_artifacts 包含本轮修改的 project_state artifacts。
17. 是否确认 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
18. 是否确认 lint-report Exit Code=0。
19. 是否确认 project_state status 显示 decision_consumed_by_report=True。
20. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
project_state/local_reverse_cpp1_7b504c54_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py
tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
.codex-skills/*
solve_reports/*
project_state/triage_*
```

`codex_report_summary` 建议：

```text
report_id=report_20260605_cpp1_7b504c54_xor_handoff_report_metadata_rework_v1
round_id=round_20260605_cpp1_7b504c54_xor_handoff_report_metadata_rework_v1
based_on_decision_id=decision_20260605_cpp1_7b504c54_xor_handoff_report_metadata_rework_v1
status=SUCCESS only if lint-report/status pass and constraints respected
acceptance_recommendation=ACCEPTED only if status=SUCCESS
generated_artifacts=["project_state/artifact_index.json", "project_state/codex_execution_report.md", "project_state/pytest_result.txt"]
```

如果 artifact_index kind is changed, do not alter:

```text
path
freshness
source_run
sha256
size_bytes
modified_at
sample_id
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

建议追加只读校验命令，如已有工具支持，可用 Python one-liner 或小脚本检查：

```bash
python - <<'PY'
import json
from pathlib import Path
h=json.loads(Path('project_state/local_reverse_cpp1_7b504c54_xor_handoff.json').read_text(encoding='utf-8'))
i=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
a=h['arrays']
assert a['byte_427A30']['bytes_hex']=='0102030405060708090a'
assert a['byte_427A3C']['bytes_hex']=='1112131415161718191a'
assert a['byte_427A48']['bytes_hex']=='4c7e507d7c645a6f5470'
assert h['known_candidate']=='' and h['runtime_validated'] is False and h['solved'] is False
entry=i['latest_artifacts_v2']['local_reverse_cpp1_7b504c54_xor_handoff']
assert entry['freshness']=='current'
assert entry['sample_id']=='cpp1_7b504c54'
assert entry['source_run']=='round_20260605_cpp1_7b504c54_xor_handoff_v1'
PY
```

如果运行该 one-liner，必须写入 `pytest_result.txt`；如果不运行，必须在 report 中说明只执行了 required tests。

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED 结果；
5. 本轮 decision_id、round_id、report_id。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. 当前 handoff artifact 缺失或无法解析。
2. artifact_index 缺少 local_reverse_cpp1_7b504c54_xor_handoff。
3. 需要重新生成 XOR handoff artifact 才能修复。
4. 需要运行样本或 runtime validation。
5. 需要运行 IDA/Ghidra/debugger/runtime probe/hook/emulator。
6. 需要修改 training_status 或 evaluation_queue。
7. 需要写 known_candidate 或标记 solved。
8. lint-report 或 project_state status 无法闭合。
9. git diff 包含 forbidden files。
```

成功完成的最低标准：

```text
1. codex_execution_report.md 的数组摘要与 handoff artifact 一致。
2. artifact_index kind 问题已修正或报告中明确解释。
3. handoff artifact 未被修改。
4. 不写 known_candidate，不标记 solved，不做 runtime validation。
5. lint-report/status 全部闭合。
6. git diff 只包含允许文件。
```
