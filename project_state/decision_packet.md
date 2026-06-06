```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_training_status_legacy_index_closeout_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_training_status_legacy_index_closeout_v1",
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

目标：对上一轮 `cpp2_2f64e68d` training status blocked overlay 做一次 **small closeout**，只修复审计中发现的两个非阻断问题：

```text
1. project_state/artifact_index.json 的 latest_artifacts_v2 已登记 local_reverse_cpp2_2f64e68d_training_status_sync，但 legacy latest_artifacts 未登记该 key。
2. project_state/pytest_result.txt 只有摘要，缺少本轮命令级输出记录，审计强度不足。
```

本轮不得继续推进 CPP2 解题，不得改 solver/validator/probe，不得重新运行 CPP2 或任何真实样本。预期结果：

```text
artifact_index.latest_artifacts["local_reverse_cpp2_2f64e68d_training_status_sync"] = "project_state\\local_reverse_cpp2_2f64e68d_training_status_sync.json"
latest_artifacts_v2 中同名 key 保持 current，不被破坏
pytest_result.txt 记录本轮实际运行命令、退出码、关键输出摘要和 decision/report/round 绑定信息
codex_execution_report.md 与本 decision_id/round_id 匹配
```

---

## 2. Current Evidence

当前 `project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
task=Review bounded window discovery diagnostics
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态：

```text
state_build_id=state_20260602_053948_4e3984041cd7
state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 active report：

```text
report_id=report_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1
round_id=round_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮核心目标已达成：

```text
project_state/local_reverse_training_status.json:
  cpp2_2f64e68d.training_status=blocked
  cpp2_2f64e68d.known_candidate=""
  blocked_reason="Windows platform but no mature backend available (pywinpty/winpty/wexpect/ConPTY API)"

project_state/local_reverse_evaluation_queue.json:
  cpp2_2f64e68d 不在 queue items 中

training_materials/local_reverse/status_overlay.json:
  cpp2_2f64e68d.training_status=blocked
  known_candidate=""
```

审计限制项：

```text
1. project_state/artifact_index.json 的 latest_artifacts_v2 已包含：
   local_reverse_cpp2_2f64e68d_training_status_sync:
     kind=local_reverse_training_status_sync
     path=project_state\\local_reverse_cpp2_2f64e68d_training_status_sync.json
     freshness=current
     source_run=round_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1
     sample_id=cpp2_2f64e68d

2. 但 legacy latest_artifacts 只到：
   local_reverse_cpp2_2f64e68d_console_mature_backend_probe
   未登记 local_reverse_cpp2_2f64e68d_training_status_sync。

3. project_state/pytest_result.txt 当前只有：
   tests_ran=41
   passed=41
   lint_decision=PASS
   lint_report=PASS (after update)
   status=PASS
   缺少命令级输出和 exit code 记录。
```

已有能力：

```text
1. reverse_agent.project_state lint-decision/lint-report/status 已存在。
2. tests/test_project_state.py 已存在并用于 handoff/report lint 约束。
3. artifact_index 同时保留 latest_artifacts legacy 字段和 latest_artifacts_v2 字段；本轮只做兼容字段同步，不改 schema。
```

`negative_results.json` 仍禁止旧 samplereverse 失败方向。本轮不触碰解题路径，不重复任何 solver/bruteforce/guided pool/runtime probe。

是否允许运行工具：

```text
允许运行 project_state lint/status、tests/test_project_state.py、git diff/status。
允许读取和修改 project_state/artifact_index.json、codex_execution_report.md、pytest_result.txt。
不允许运行 CPP2.exe、pair validator CLI、mature backend probe CLI、local_reverse_training_status CLI、IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
```

是否允许读取重型 artifact：

```text
不允许默认读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
不允许读取 project_state/rounds 全量历史。
只允许读取上一轮直接相关的小文件和当前 project_state 小文件。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe 或任何真实 binary target。
2. 不运行 console pair validator CLI。
3. 不运行 mature backend probe CLI。
4. 不运行 local_reverse_training_status CLI 重新生成训练状态。
5. 不运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
6. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
7. 不改 reverse_agent/local_reverse_training_status.py。
8. 不改 tests/test_local_reverse_training_status.py。
9. 不改 reverse_agent/local_reverse_console_pair_validator.py。
10. 不改 reverse_agent/local_reverse_console_mature_backend_probe.py。
11. 不改任何 IDA/Ghidra runner 或 solver。
12. 不改 project_state/local_reverse_training_status.json。
13. 不改 project_state/local_reverse_evaluation_queue.json。
14. 不改 training_materials/local_reverse/status_overlay.json。
15. 不把 ippio 写成 known_candidate、candidate、solved 或 flag。
16. 不提交 solve_reports。
17. 不修改 .codex-skills/*。
18. 不读取完整 PROJECT_PROGRESS_LOG.txt。
19. 不新增依赖。
```

允许：

```text
1. 修改 project_state/artifact_index.json：只补 legacy latest_artifacts 中的 local_reverse_cpp2_2f64e68d_training_status_sync key，并保持 latest_artifacts_v2 原样 current。
2. 修改 project_state/codex_execution_report.md：写本轮 codex_report_summary 和执行报告。
3. 修改 project_state/pytest_result.txt：记录本轮命令级测试/lint/status 输出摘要。
4. 可新建 project_state/rounds/round_20260606_cpp2_2f64e68d_training_status_legacy_index_closeout_v1/ minimal archive，只包含 decision_packet.md、codex_execution_report.md、pytest_result.txt、round_manifest.json。
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
.codex-skills/registry.json
project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
```

必要时读取：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
本地 E:\reverse 样本目录
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 engineering_branch。
4. 是否确认上一轮 training status blocked overlay 已完成但有 legacy index/pytest_result 记录限制项。
5. 是否确认本轮没有改代码、测试、solver、validator、probe。
6. 是否确认 artifact_index.latest_artifacts_v2 中 local_reverse_cpp2_2f64e68d_training_status_sync 保持 current。
7. 是否确认 artifact_index.latest_artifacts 中已补 local_reverse_cpp2_2f64e68d_training_status_sync。
8. 是否确认没有修改 local_reverse_training_status.json / evaluation_queue.json / status_overlay.json。
9. 是否确认没有运行 CPP2.exe 或任何真实 target。
10. 是否确认没有运行 pair validator CLI、mature backend probe CLI、local_reverse_training_status CLI。
11. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
12. 是否确认没有把 ippio 标记为 known_candidate/candidate/solved/flag。
13. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
14. 是否确认 pytest_result.txt 记录了每个命令、退出码和关键输出摘要。
15. 是否确认 lint-decision、lint-report、status 结果真实记录。
16. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
17. 是否确认没有提交 solve_reports 或修改 .codex-skills。
```

---

## 6. Implementation Scope

小步 closeout，不跨主线扩张。

具体实现：

```text
1. 读取 project_state/artifact_index.json。
2. 找到 latest_artifacts_v2["local_reverse_cpp2_2f64e68d_training_status_sync"]。
3. 验证其 freshness=current、path=project_state\\local_reverse_cpp2_2f64e68d_training_status_sync.json、sample_id=cpp2_2f64e68d。
4. 在 legacy latest_artifacts 中补：
   "local_reverse_cpp2_2f64e68d_training_status_sync": "project_state\\local_reverse_cpp2_2f64e68d_training_status_sync.json"
5. 不改变其他 latest_artifacts_v2 内容。
6. 不重算 sha256/size/modified_at，除非只针对本轮 report/pytest 文件自身；artifact_index 中 sync artifact 的 v2 metadata 不应被无谓改写。
7. 更新 project_state/codex_execution_report.md，必须包含 codex_report_summary。
8. 更新 project_state/pytest_result.txt，必须绑定本轮 decision_id/report_id/round_id，并记录命令级输出摘要。
```

如果发现 `latest_artifacts_v2` 中 sync artifact 缺失或不是 current，则停止并写 `status=BLOCKED`，不要自行重跑上一轮训练状态生成。

---

## 7. Tests

必须运行并记录：

```text
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. project_state/artifact_index.json latest_artifacts_v2["local_reverse_cpp2_2f64e68d_training_status_sync"].freshness == "current"。
2. project_state/artifact_index.json latest_artifacts["local_reverse_cpp2_2f64e68d_training_status_sync"] == "project_state\\local_reverse_cpp2_2f64e68d_training_status_sync.json"。
3. project_state/local_reverse_training_status.json 未被修改，且 cpp2_2f64e68d 仍为 blocked/known_candidate=""。
4. project_state/local_reverse_evaluation_queue.json 未被修改，且 cpp2_2f64e68d 不在 queue。
5. training_materials/local_reverse/status_overlay.json 未被修改。
6. git diff --name-status 只包含允许文件。
```

不要求运行 `tests/test_local_reverse_training_status.py`，因为本轮不改 training status 代码；如运行也可以，但不得因此修改训练状态产物。

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 SUCCESS/ACCEPTED，如果出现任一情况：

```text
1. latest_artifacts_v2 中 local_reverse_cpp2_2f64e68d_training_status_sync 缺失、stale 或 path 不匹配。
2. 需要重新运行 local_reverse_training_status CLI 才能继续。
3. 需要运行 CPP2.exe、pair validator CLI、mature backend probe CLI、IDA/Ghidra/debugger/hook/emulator/solver 才能继续。
4. 需要修改 Python 源码、测试、solver、validator、probe。
5. 需要修改 local_reverse_training_status.json、evaluation_queue.json 或 status_overlay.json。
6. pytest、lint-decision、lint-report、status 任一失败且无法在本轮范围内只通过 report/pytest/artifact_index 修复。
7. git diff 显示 solve_reports、.codex-skills 或无关文件变更。
8. pytest_result.txt 仍只有摘要，没有命令级输出记录。
```
