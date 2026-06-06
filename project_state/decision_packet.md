```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp1_7b504c54_training_status_sync_v1",
  "round_id": "round_20260606_cpp1_7b504c54_training_status_sync_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **training_dataset**。

目标：把上一轮已经 runtime validated 的 `cpp1_7b504c54` 同步到训练集状态文件、评估队列和 status overlay，使训练数据状态与 current artifact evidence 一致。

上一轮已经完成并审计接受：

```text
runtime_validation_artifact=project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
sample_id=cpp1_7b504c54
candidate=WeKnowItOk
known_candidate=WeKnowItOk
executed_sample=true
runtime_validated=true
validation_status=VALIDATED_SUCCESS
success_observed=true
solved=true
target_sha256=7b504c54c165100549a0eacb7eb7cad26bc235ec0c4bed5c38c95a827ff81a3c
```

当前不一致点：

```text
1. project_state/local_reverse_training_status.json 仍把 cpp1_7b504c54 标为 inventory_only，known_candidate 为空。
2. training_materials/local_reverse/status_overlay.json 仍把 cpp1_7b504c54 标为 inventory_only，known_candidate 为空。
3. project_state/local_reverse_evaluation_queue.json 仍把 cpp1_7b504c54 放在 rank=1，allowed_actions=static_triage。
```

本轮只做状态收敛，不继续求解新样本，不运行工具，不生成新的候选。

预期结果：

```text
1. cpp1_7b504c54 在 training_status 与 status_overlay 中变为 solved。
2. cpp1_7b504c54 的 known_candidate 变为 WeKnowItOk。
3. status_summary 从 solved=1, blocked=4, needs_triage=0, inventory_only=24 更新为 solved=2, blocked=4, needs_triage=0, inventory_only=23。
4. cpp1_7b504c54 从 evaluation_queue.items 中移除，其余 item 重新连续编号 rank。
5. 生成一个轻量同步审计 artifact：project_state/local_reverse_cpp1_7b504c54_training_status_sync.json。
6. artifact_index 登记该同步 artifact，freshness=current。
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，`task=Review bounded window discovery diagnostics`，并明确 `project_state/decision_packet.md` 才是当前轮执行权威。`task_packet.task` 不控制本轮。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮有关 local reverse 训练状态的事实以 current artifact 和 training files 为准。

上一轮 `codex_execution_report.md` 已闭合：

```text
report_id=report_20260606_cpp1_7b504c54_runtime_validation_v1
based_on_decision_id=decision_20260606_cpp1_7b504c54_runtime_validation_v1
round_id=round_20260606_cpp1_7b504c54_runtime_validation_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt` 已记录真实测试：

```text
status=PASSED
Total Commands=10
Passed=10
Failed=0
runtime_validation=VALIDATED_SUCCESS, solved=True, candidate=WeKnowItOk
lint-report=OK
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

当前 runtime validation artifact：

```text
path=project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
schema_version=1
sample_id=cpp1_7b504c54
analysis_mode=console_runtime_validation
mainline=reverse_solving
source_artifact_freshness=current
relative_path=逆向课程2023春补考01/Cpp1.exe
candidate_source_field=static_candidate_text
candidate=WeKnowItOk
known_candidate=WeKnowItOk
executed_sample=true
runtime_validated=true
validation_status=VALIDATED_SUCCESS
success_token=Congratulations! You are right!
success_observed=true
failure_observed=false
length_error_observed=false
return_code=0
solved=true
blocked_reason=""
target_sha256=7b504c54c165100549a0eacb7eb7cad26bc235ec0c4bed5c38c95a827ff81a3c
```

当前 artifact_index 已登记：

```text
local_reverse_cpp1_7b504c54_static_triage:
  kind=local_reverse_single_sample_static_triage
  freshness=current
  sample_id=cpp1_7b504c54

local_reverse_cpp1_7b504c54_xor_handoff:
  kind=local_reverse_cpp1_xor_handoff
  freshness=current
  sample_id=cpp1_7b504c54

local_reverse_cpp1_7b504c54_runtime_validation:
  kind=local_reverse_console_runtime_validation
  path=project_state\local_reverse_cpp1_7b504c54_runtime_validation.json
  freshness=current
  source_run=round_20260606_cpp1_7b504c54_runtime_validation_v1
  sample_id=cpp1_7b504c54
```

当前 `project_state/local_reverse_training_status.json` 仍不一致：

```text
status_summary.solved=1
status_summary.blocked=4
status_summary.needs_triage=0
status_summary.inventory_only=24
samples[cpp1_7b504c54].training_status=inventory_only
samples[cpp1_7b504c54].known_candidate=""
samples[cpp1_7b504c54].classification=""
samples[cpp1_7b504c54].evidence_sources=[]
samples[cpp1_7b504c54].next_action="static triage and manual evaluation required"
```

当前 `training_materials/local_reverse/status_overlay.json` 仍不一致：

```text
status_summary.solved=1
status_summary.blocked=4
status_summary.needs_triage=0
status_summary.inventory_only=24
samples[cpp1_7b504c54].training_status=inventory_only
samples[cpp1_7b504c54].known_candidate=""
samples[cpp1_7b504c54].blocked_reason=""
```

当前 `project_state/local_reverse_evaluation_queue.json` 仍不一致：

```text
items[0].rank=1
items[0].sample_id=cpp1_7b504c54
items[0].allowed_actions=["static_triage"]
items[0].forbidden_actions includes runtime_probe
```

这与 current runtime validation artifact 冲突，应移出待评估队列。

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

已有能力检查：

```text
1. IDA/IDAPython 能力已存在，且当前 static triage 已来自 IDA；本轮不运行 IDA。
2. Console runtime validator 已新增并通过上一轮 13 个单元测试；本轮不再次运行目标 binary。
3. artifact_index 已能登记 project_state artifacts；本轮只增加 training_status_sync artifact。
4. 当前缺口不是 solver 能力，而是训练集状态未与 current validation evidence 同步。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行目标样本，不做 runtime validation。
2. 不运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
3. 不运行 solver/bruteforce/guided pool/constraint recovery。
4. 不推进任何新样本求解。
5. 不批量跑 local_reverse_samples / E:\reverse。
6. 不修改 project_state/local_reverse_cpp1_7b504c54_runtime_validation.json。
7. 不修改 project_state/local_reverse_cpp1_7b504c54_xor_handoff.json。
8. 不修改 project_state/local_reverse_cpp1_7b504c54_static_triage.json。
9. 不修改 reverse_agent/local_reverse_console_validator.py 或其测试，除非只读发现语法损坏；默认不改代码。
10. 不修改 .codex-skills。
11. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
12. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
13. 不把其他 inventory_only 样本顺手改成 solved/blocked。
14. 不把 cpp1_7b504c54 保留在 evaluation_queue 中。
15. 不把 training_status 与 status_overlay 更新成彼此不一致的状态。
```

允许：

```text
1. 修改 project_state/local_reverse_training_status.json。
2. 修改 project_state/local_reverse_evaluation_queue.json。
3. 修改 training_materials/local_reverse/status_overlay.json。
4. 新增 project_state/local_reverse_cpp1_7b504c54_training_status_sync.json。
5. 更新 project_state/artifact_index.json 登记 training status sync artifact。
6. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
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
project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
.codex-skills/registry.json
```

只读参考，默认不要修改：

```text
project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
project_state/local_reverse_cpp1_7b504c54_static_triage.json
reverse_agent/local_reverse_console_validator.py
tests/test_local_reverse_console_validator.py
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
3. 是否确认本轮主线为 training_dataset。
4. 是否确认 runtime validation artifact 为 current 且 solved=true。
5. 是否确认 artifact_index 中 runtime validation entry 为 freshness=current。
6. 是否确认未运行目标样本、未做 runtime validation。
7. 是否确认未运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
8. 是否确认未运行 solver/bruteforce/guided pool/constraint recovery。
9. 是否确认未修改 runtime validation artifact、XOR handoff artifact、static triage artifact。
10. 是否确认只同步 cpp1_7b504c54 一个样本。
11. 是否确认 training_status 中 cpp1_7b504c54.training_status=solved。
12. 是否确认 training_status 中 cpp1_7b504c54.known_candidate=WeKnowItOk。
13. 是否确认 training_status.status_summary 为 solved=2, blocked=4, needs_triage=0, inventory_only=23。
14. 是否确认 status_overlay 与 training_status 对 cpp1_7b504c54 的状态一致。
15. 是否确认 status_overlay.status_summary 同步为 solved=2, blocked=4, needs_triage=0, inventory_only=23。
16. 是否确认 cpp1_7b504c54 已从 evaluation_queue.items 移除。
17. 是否确认 evaluation_queue 剩余 items 的 rank 从 1 开始连续递增。
18. 是否确认生成 training_status_sync artifact 并在 artifact_index 中登记 freshness=current。
19. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
20. 是否确认 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
21. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

具体同步要求：

```text
project_state/local_reverse_training_status.json:
  generated_at 更新为本轮 UTC 时间。
  status_summary 更新为:
    solved=2
    blocked=4
    needs_triage=0
    inventory_only=23
  samples 中 sample_id=cpp1_7b504c54 更新为:
    training_status="solved"
    known_candidate="WeKnowItOk"
    blocked_reason=""
    classification="cpp1_xor_string_compare runtime_validated console_runtime_validation"
    evidence_sources 包含且仅使用 current/local project_state 证据，不使用 solve_reports:
      "source:local_reverse_cpp1_7b504c54_runtime_validation.json"
      "runtime_validation"
      "source:local_reverse_cpp1_7b504c54_xor_handoff.json"
      "static_handoff"
      "source:local_reverse_cpp1_7b504c54_static_triage.json"
      "ida_static_triage"
    next_action="No further solving action required; keep as solved regression sample."

training_materials/local_reverse/status_overlay.json:
  generated_at 更新为本轮 UTC 时间。
  status_summary 同步为 solved=2, blocked=4, needs_triage=0, inventory_only=23。
  samples 中 sample_id=cpp1_7b504c54 更新为:
    training_status="solved"
    known_candidate="WeKnowItOk"
    blocked_reason=""

project_state/local_reverse_evaluation_queue.json:
  generated_at 更新为本轮 UTC 时间。
  从 items 中移除 sample_id=cpp1_7b504c54。
  其余 items 按原相对顺序重新编号 rank=1..N。
  queue_policy 保持不变，除非现有生成逻辑必须补充说明；不得扩大策略。

project_state/local_reverse_cpp1_7b504c54_training_status_sync.json:
  schema_version=1
  sample_id=cpp1_7b504c54
  mainline=training_dataset
  source_artifacts 包含 local_reverse_cpp1_7b504c54_runtime_validation
  source_artifact_freshness=current
  source_run=round_20260606_cpp1_7b504c54_training_status_sync_v1
  training_status_before=inventory_only
  training_status_after=solved
  known_candidate=WeKnowItOk
  status_summary_before={solved:1, blocked:4, needs_triage:0, inventory_only:24}
  status_summary_after={solved:2, blocked:4, needs_triage:0, inventory_only:23}
  queue_removed_sample=true
  overlay_updated=true
  runtime_validation_artifact=project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
  validation_status=VALIDATED_SUCCESS
  solved=true
  blocked_reason=""
  generated_at=<UTC>

project_state/artifact_index.json:
  latest_artifacts.local_reverse_cpp1_7b504c54_training_status_sync = "project_state\\local_reverse_cpp1_7b504c54_training_status_sync.json"
  latest_artifacts_v2.local_reverse_cpp1_7b504c54_training_status_sync = {
    kind="local_reverse_training_status_sync",
    path="project_state\\local_reverse_cpp1_7b504c54_training_status_sync.json",
    freshness="current",
    source_run="round_20260606_cpp1_7b504c54_training_status_sync_v1",
    sha256=<actual file sha256>,
    size_bytes=<actual size>,
    modified_at=<actual UTC timestamp>,
    sample_id="cpp1_7b504c54"
  }
```

允许修改：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_7b504c54_training_status_sync.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
project_state/local_reverse_cpp1_7b504c54_static_triage.json
reverse_agent/local_reverse_console_validator.py
tests/test_local_reverse_console_validator.py
reverse_agent/tool_runners.py
reverse_agent/olly_scripts/compare_probe.py
.codex-skills/*
solve_reports/*
project_state/triage_*
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m pytest -q tests/test_project_state.py
python - <<'PY'
import json
from pathlib import Path
training=json.loads(Path('project_state/local_reverse_training_status.json').read_text(encoding='utf-8'))
overlay=json.loads(Path('training_materials/local_reverse/status_overlay.json').read_text(encoding='utf-8'))
queue=json.loads(Path('project_state/local_reverse_evaluation_queue.json').read_text(encoding='utf-8'))
sync=json.loads(Path('project_state/local_reverse_cpp1_7b504c54_training_status_sync.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
validation=json.loads(Path('project_state/local_reverse_cpp1_7b504c54_runtime_validation.json').read_text(encoding='utf-8'))
assert validation['sample_id']=='cpp1_7b504c54'
assert validation['validation_status']=='VALIDATED_SUCCESS'
assert validation['known_candidate']=='WeKnowItOk'
assert validation['solved'] is True
expected={'solved':2,'blocked':4,'needs_triage':0,'inventory_only':23}
assert training['status_summary']==expected
assert overlay['status_summary']==expected
train_sample=next(s for s in training['samples'] if s['sample_id']=='cpp1_7b504c54')
overlay_sample=next(s for s in overlay['samples'] if s['sample_id']=='cpp1_7b504c54')
assert train_sample['training_status']=='solved'
assert train_sample['known_candidate']=='WeKnowItOk'
assert overlay_sample['training_status']=='solved'
assert overlay_sample['known_candidate']=='WeKnowItOk'
assert all(item['sample_id']!='cpp1_7b504c54' for item in queue['items'])
assert [item['rank'] for item in queue['items']]==list(range(1, len(queue['items'])+1))
assert sync['sample_id']=='cpp1_7b504c54'
assert sync['training_status_after']=='solved'
assert sync['known_candidate']=='WeKnowItOk'
entry=index['latest_artifacts_v2']['local_reverse_cpp1_7b504c54_training_status_sync']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_training_status_sync'
assert entry['sample_id']=='cpp1_7b504c54'
assert entry['source_run']=='round_20260606_cpp1_7b504c54_training_status_sync_v1'
print('training status sync consistency OK')
PY
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

`codex_report_summary` 建议：

```text
report_id=report_20260606_cpp1_7b504c54_training_status_sync_v1
round_id=round_20260606_cpp1_7b504c54_training_status_sync_v1
based_on_decision_id=decision_20260606_cpp1_7b504c54_training_status_sync_v1
status=SUCCESS only if all checks pass and constraints are respected
acceptance_recommendation=ACCEPTED only if status=SUCCESS
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. runtime validation artifact 缺失或无法解析。
2. runtime validation artifact 不是 sample_id=cpp1_7b504c54。
3. runtime validation artifact 的 validation_status 不是 VALIDATED_SUCCESS。
4. runtime validation artifact 的 known_candidate 不是 WeKnowItOk 或 solved 不是 true。
5. artifact_index 中 runtime validation entry 缺失或 freshness 不是 current。
6. training_status 中找不到 cpp1_7b504c54。
7. status_overlay 中找不到 cpp1_7b504c54。
8. evaluation_queue 中没有 cpp1_7b504c54，但 training_status/overlay 仍不一致，需要报告当前状态而不是猜测。
9. 需要运行目标样本、IDA/Ghidra/debugger/hook/emulator 才能继续。
10. 需要修改 runtime validation/XOR handoff/static triage artifact 才能继续。
11. 状态计数无法自洽。
12. queue rank 无法连续重排。
13. lint-report 或 project_state status 无法闭合。
14. git diff 包含 forbidden files。
```

成功完成的最低标准：

```text
1. training_status 与 status_overlay 均将 cpp1_7b504c54 标为 solved。
2. training_status 与 status_overlay 均记录 known_candidate=WeKnowItOk。
3. status_summary 更新一致。
4. evaluation_queue 移除 cpp1_7b504c54 并重新连续编号。
5. 生成 training_status_sync artifact 并登记到 artifact_index。
6. 未运行任何工具或样本。
7. 未修改 runtime validation/XOR handoff/static triage artifact。
8. pytest_result.txt 完整记录真实测试。
