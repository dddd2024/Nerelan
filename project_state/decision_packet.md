```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp1_7b504c54_training_status_sync_rework_v1",
  "round_id": "round_20260606_cpp1_7b504c54_training_status_sync_rework_v1",
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

目标：修复上一轮 `cpp1_7b504c54` 训练状态同步提交的审计闭环问题。上一轮状态同步的实际结果大体正确，但不能接受为最终轮次，因为 `codex_execution_report.md` 仍引用旧 runtime-validation decision，缺少本轮要求的 sync artifact 与 artifact_index 登记，并且存在未按 decision 说明的代码/测试改动。

本轮只允许做 **metadata/report/artifact rework**：

```text
1. 保留已完成的训练状态同步结果，除非一致性检查证明它错误。
2. 新增 project_state/local_reverse_cpp1_7b504c54_training_status_sync.json。
3. 更新 project_state/artifact_index.json，登记 local_reverse_cpp1_7b504c54_training_status_sync。
4. 重写 project_state/codex_execution_report.md，使其对应本 rework decision。
5. 重写 project_state/pytest_result.txt，记录本 rework 轮真实测试。
6. 在报告中明确说明上一轮为什么修改了 reverse_agent/local_reverse_training_status.py 与 tests/test_local_reverse_training_status.py；若无法正当说明，必须回退这两个文件。
```

本轮不继续求解，不运行样本，不运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe，不生成新 candidate。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。当前执行权威是本 `project_state/decision_packet.md`。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。

当前最新提交：

```text
commit=9e1ae7e9873c3d79b844382ebc3db39e16716de0
message=Fix local_reverse training status overlays and archive round
```

该提交显示训练状态同步结果大体已完成：

```text
cpp1_7b504c54 已从 local_reverse_evaluation_queue.json 移除。
下一队列样本变为 cpp2_2f64e68d。
status summary 变为 solved=2, blocked=4, needs_triage=0, inventory_only=23。
pytest_training_status=33 tests passed。
training_status_regeneration=PASSED。
readonly_consistency_check=PASSED。
```

但上一轮审计结论为 `REWORK_REQUIRED`，原因如下：

```text
1. codex_execution_report.md 仍写 Active decision remains decision_20260606_cpp1_7b504c54_runtime_validation_v1。
2. codex_execution_report.md 仍写 Active round remains round_20260606_cpp1_7b504c54_runtime_validation_v1。
3. 当前实际应对应 training_status_sync / rework decision，而不是旧 runtime_validation decision。
4. 缺少 project_state/local_reverse_cpp1_7b504c54_training_status_sync.json。
5. artifact_index 未登记 local_reverse_cpp1_7b504c54_training_status_sync。
6. tests_ran 缺少 python -m reverse_agent.project_state lint-decision --state-dir project_state。
7. 上一轮修改了 reverse_agent/local_reverse_training_status.py 与 tests/test_local_reverse_training_status.py，但未在 decision 允许范围内说明或处理。
```

当前 runtime validation artifact 仍是前置证据：

```text
path=project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
sample_id=cpp1_7b504c54
known_candidate=WeKnowItOk
runtime_validated=true
validation_status=VALIDATED_SUCCESS
success_observed=true
solved=true
```

当前 negative_results 仍禁止：

```text
old sample_solver blind search
increase guided_pool beam/budget only
compare_semantics_agree=false primary frontier
commit full solve_reports directory
repeat dynamic-probe directions without new evidence
Base64/RC4 breakpoint probe before real lhs producer identification
```

本轮不触碰这些方向。

已有能力检查：

```text
1. IDA/IDAPython 能力已存在，但本轮不运行 IDA。
2. Console runtime validator 已存在，但本轮不运行目标 binary。
3. local_reverse_training_status.py 已能再生成 training_status/queue/overlay，但本轮优先不再改实现。
4. artifact_index 已支持 project_state artifact 登记；本轮必须使用它登记 sync artifact。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行目标样本，不重新 runtime validation。
2. 不运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
3. 不运行 solver/bruteforce/guided pool/constraint recovery。
4. 不推进任何新样本求解。
5. 不批量跑 local_reverse_samples / E:\reverse。
6. 不修改 project_state/local_reverse_cpp1_7b504c54_runtime_validation.json。
7. 不修改 project_state/local_reverse_cpp1_7b504c54_xor_handoff.json。
8. 不修改 project_state/local_reverse_cpp1_7b504c54_static_triage.json。
9. 不继续改 reverse_agent/local_reverse_training_status.py 或 tests/test_local_reverse_training_status.py；除非选择回退上一轮越界改动。
10. 不修改 .codex-skills。
11. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
12. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
13. 不把其他样本状态顺手改成 solved/blocked。
14. 不把旧 runtime_validation decision 写成本轮 report 的 based_on_decision_id。
15. 不把 report/pytest_result 留在旧 round_id。
```

允许：

```text
1. 新增 project_state/local_reverse_cpp1_7b504c54_training_status_sync.json。
2. 更新 project_state/artifact_index.json。
3. 更新 project_state/codex_execution_report.md。
4. 更新 project_state/pytest_result.txt。
5. 仅当一致性检查发现状态文件不符合已验证事实时，才修正 project_state/local_reverse_training_status.json、project_state/local_reverse_evaluation_queue.json、training_materials/local_reverse/status_overlay.json。
6. 仅当无法正当解释上一轮代码/测试越界改动时，回退 reverse_agent/local_reverse_training_status.py 与 tests/test_local_reverse_training_status.py。
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

必须检查上一轮越界改动：

```text
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
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
4. 是否确认本轮是 rework：修复 report/pytest/artifact_index/sync artifact 闭环。
5. 是否确认 runtime validation artifact 仍为 current 且 solved=true。
6. 是否确认 cpp1_7b504c54 在 training_status 与 status_overlay 中为 solved。
7. 是否确认 cpp1_7b504c54.known_candidate=WeKnowItOk。
8. 是否确认 status_summary 为 solved=2, blocked=4, needs_triage=0, inventory_only=23。
9. 是否确认 cpp1_7b504c54 已从 evaluation_queue 中移除。
10. 是否确认 queue rank 连续递增。
11. 是否生成 local_reverse_cpp1_7b504c54_training_status_sync.json。
12. 是否在 artifact_index.latest_artifacts 与 latest_artifacts_v2 登记 sync artifact。
13. 是否确认 sync artifact freshness=current。
14. 是否确认 codex_report_summary 的 based_on_decision_id 等于 decision_20260606_cpp1_7b504c54_training_status_sync_rework_v1。
15. 是否确认 codex_report_summary 的 round_id 等于 round_20260606_cpp1_7b504c54_training_status_sync_rework_v1。
16. 是否确认 pytest_result_summary 使用本 rework decision_id/report_id/round_id。
17. 是否确认本轮运行了 lint-decision、lint-report、project_state status。
18. 是否确认没有运行目标样本、IDA/Ghidra/debugger/hook/emulator/CompareProbe。
19. 是否确认没有修改 runtime validation/XOR handoff/static triage artifact。
20. 是否说明上一轮 reverse_agent/local_reverse_training_status.py 与 tests/test_local_reverse_training_status.py 的处理方式：保留并解释，或回退。
21. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

必须新增 sync artifact：

```json
{
  "schema_version": 1,
  "sample_id": "cpp1_7b504c54",
  "mainline": "training_dataset",
  "analysis_mode": "training_status_sync_rework",
  "source_run": "round_20260606_cpp1_7b504c54_training_status_sync_rework_v1",
  "source_artifacts": [
    "local_reverse_cpp1_7b504c54_runtime_validation"
  ],
  "source_artifact_freshness": "current",
  "runtime_validation_artifact": "project_state/local_reverse_cpp1_7b504c54_runtime_validation.json",
  "validation_status": "VALIDATED_SUCCESS",
  "training_status_before": "inventory_only",
  "training_status_after": "solved",
  "known_candidate": "WeKnowItOk",
  "status_summary_before": {
    "solved": 1,
    "blocked": 4,
    "needs_triage": 0,
    "inventory_only": 24
  },
  "status_summary_after": {
    "solved": 2,
    "blocked": 4,
    "needs_triage": 0,
    "inventory_only": 23
  },
  "queue_removed_sample": true,
  "overlay_updated": true,
  "solved": true,
  "blocked_reason": "",
  "rework_reason": "previous report referenced runtime_validation decision and omitted sync artifact registration",
  "generated_at": "<UTC>"
}
```

必须更新 artifact_index：

```text
latest_artifacts.local_reverse_cpp1_7b504c54_training_status_sync = "project_state\\local_reverse_cpp1_7b504c54_training_status_sync.json"

latest_artifacts_v2.local_reverse_cpp1_7b504c54_training_status_sync = {
  kind="local_reverse_training_status_sync",
  path="project_state\\local_reverse_cpp1_7b504c54_training_status_sync.json",
  freshness="current",
  source_run="round_20260606_cpp1_7b504c54_training_status_sync_rework_v1",
  sha256=<actual file sha256>,
  size_bytes=<actual size>,
  modified_at=<actual UTC timestamp>,
  sample_id="cpp1_7b504c54"
}
```

必须重写 report 顶部：

```json
{
  "schema_version": 1,
  "report_id": "report_20260606_cpp1_7b504c54_training_status_sync_rework_v1",
  "round_id": "round_20260606_cpp1_7b504c54_training_status_sync_rework_v1",
  "based_on_decision_id": "decision_20260606_cpp1_7b504c54_training_status_sync_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/local_reverse_cpp1_7b504c54_training_status_sync.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m pytest -q tests/test_local_reverse_training_status.py",
    "python -c (readonly consistency check: sync artifact + artifact_index + training status + queue + overlay)",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_cpp1_7b504c54_training_status_sync.json"
  ]
}
```

如果本轮还修改 training status/queue/overlay 或回退代码/测试，必须把这些文件补入 `files_changed` 并解释原因。不得漏报。

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m pytest -q tests/test_local_reverse_training_status.py
python - <<'PY'
import json
from pathlib import Path
training=json.loads(Path('project_state/local_reverse_training_status.json').read_text(encoding='utf-8'))
overlay=json.loads(Path('training_materials/local_reverse/status_overlay.json').read_text(encoding='utf-8'))
queue=json.loads(Path('project_state/local_reverse_evaluation_queue.json').read_text(encoding='utf-8'))
sync=json.loads(Path('project_state/local_reverse_cpp1_7b504c54_training_status_sync.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
validation=json.loads(Path('project_state/local_reverse_cpp1_7b504c54_runtime_validation.json').read_text(encoding='utf-8'))
expected={'solved':2,'blocked':4,'needs_triage':0,'inventory_only':23}
assert validation['sample_id']=='cpp1_7b504c54'
assert validation['validation_status']=='VALIDATED_SUCCESS'
assert validation['known_candidate']=='WeKnowItOk'
assert validation['solved'] is True
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
assert sync['queue_removed_sample'] is True
assert sync['overlay_updated'] is True
entry=index['latest_artifacts_v2']['local_reverse_cpp1_7b504c54_training_status_sync']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_training_status_sync'
assert entry['sample_id']=='cpp1_7b504c54'
assert entry['source_run']=='round_20260606_cpp1_7b504c54_training_status_sync_rework_v1'
print('training status sync rework consistency OK')
PY
git diff --check
git status --short
git diff --name-status
```

`pytest_result.txt` 必须包含每条命令原文、Exit Code、输出摘要、PASSED/FAILED/BLOCKED 结果，以及本轮 decision_id/report_id/round_id。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. runtime validation artifact 缺失或不是 VALIDATED_SUCCESS。
2. artifact_index 中 runtime validation entry 缺失或 freshness 不是 current。
3. training_status/overlay/queue 当前状态与 solved=2、known_candidate=WeKnowItOk、queue exclude cpp1_7b504c54 不一致，且无法在不运行工具的情况下修正。
4. 无法生成 sync artifact。
5. 无法计算 sync artifact sha256/size/modified_at。
6. lint-decision、lint-report 或 project_state status 失败。
7. pytest_training_status 失败。
8. git diff 包含 forbidden files。
9. 需要运行样本、IDA/Ghidra/debugger/hook/emulator/CompareProbe 才能继续。
10. 需要修改 runtime validation/XOR handoff/static triage artifact 才能继续。
11. report 仍引用旧 runtime_validation decision 或旧 round。
12. pytest_result 仍引用旧 runtime_validation decision 或旧 round。
```

成功完成的最低标准：

```text
1. report/decision/round 三者匹配本 rework decision。
2. pytest_result 匹配本 rework decision。
3. sync artifact 存在且语义完整。
4. artifact_index 登记 sync artifact 为 current。
5. training_status、status_overlay、evaluation_queue 与 validated solved fact 一致。
6. 未运行样本或工具。
7. 未修改 runtime validation/XOR handoff/static triage artifact。
8. 对上一轮代码/测试越界改动给出明确处理：保留并解释，或回退。
```
