```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_training_overlay_sync_artifact_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_training_overlay_sync_artifact_rework_v1",
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

目标：修复 `training_status_overlay_sync` 轮中 sync artifact 与实际 `training_materials/local_reverse/status_overlay.json` 的 `cpp2_883e67b9.solved_at` 不一致问题。

本轮只修状态同步 artifact、artifact_index sha/size、report、pytest_result。不得重新解题，不得生成 candidate，不得运行样本，不得 runtime validation，不得执行 IDA/Ghidra/static extraction，不得修改 solver production code。

必须完成：

```text
1. 读取 training_materials/local_reverse/status_overlay.json 中 cpp2_883e67b9 的实际 entry。
2. 修正 project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json：
   - after_overlay_entry 必须与 status_overlay.json 中 cpp2_883e67b9 的实际 entry 完全一致；
   - 特别是 solved_at 必须改为 status_overlay.json 的实际值：2026-06-08T14:42:30Z，除非先同步修改 overlay 文件本身并给出必要理由。
3. 重新计算 sync artifact 的 sha256 / size_bytes。
4. 更新 artifact_index.latest_artifacts_v2.local_reverse_cpp2_883e67b9_training_status_overlay_sync 的 sha256 / size_bytes / modified_at。
5. 更新 artifact_index.artifact_refs 中该 sync artifact 的 sha256 / size_bytes / source_run，如存在。
6. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 rework decision/report/round。
7. 记录本轮没有重新生成 candidate、没有运行样本、没有 runtime validation、没有 IDA/Ghidra/static extraction。
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论为 REWORK_REQUIRED。已完成的有效内容：

```text
1. training_materials/local_reverse/status_overlay.json 已将 cpp2_883e67b9 从 inventory_only 同步为 solved。
2. status_summary 已更新为 solved=5、blocked=4、needs_triage=0、inventory_only=20。
3. cpp2_883e67b9 overlay entry 已包含：
   training_status=solved
   known_candidate=KaiJu_YiZhi_PEN
   solved_by=console_runtime_validation
   solved_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
   evidence_source=project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
4. sync artifact 已生成并登记到 artifact_index latest_artifacts / latest_artifacts_v2 / artifact_refs。
5. report/pytest_result 已绑定 training_status_overlay_sync_v1，且测试记录通过。
```

阻断问题：

```text
1. 实际 status_overlay.json 中 cpp2_883e67b9.solved_at=2026-06-08T14:42:30Z。
2. sync artifact 的 after_overlay_entry.solved_at=2026-06-08T15:10:00Z。
3. 因此 sync artifact 的 after_overlay_entry 不能精确复现实际 overlay entry，审计链条不闭合。
```

`negative_results.json` 仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current，不重复旧 samplereverse 失败方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要进入 reverse_solving 解题流程。
2. 不要生成 candidate、验证 candidate、运行 negative control 或 runtime validation。
3. 不要运行样本交互逻辑。
4. 不要执行 IDA/Ghidra/static extraction。
5. 不要 attach debugger / hook / emulator / probe / winpty。
6. 不要 brute force、dictionary search、fuzz、beam/topN、扩大 timeout/budget。
7. 不要新增 solver/harness/runtime/IDA/Ghidra/debugger 接口。
8. 不要修改 solver production code。
9. 不要修改 .codex-skills。
10. 不要提交根目录工具 dump。
11. 不要读取完整 solve_reports。
12. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
13. 不要提交 full solve_reports。
14. 不要把 task_packet.task 当执行权威。
15. 不要把 stale/missing/unknown artifact 当 current。
16. 不要修改 cpp2_883e67b9 以外的样本状态。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 training_materials/local_reverse/status_overlay.json。
3. 修正 project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json。
4. 更新 artifact_index 中该 sync artifact 的 sha256 / size_bytes / modified_at。
5. 更新 codex_execution_report.md 和 pytest_result.txt。
6. 运行 JSON parse、py_compile、pytest、lint、project_state status、git diff check。
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
project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json
training_materials/local_reverse/status_overlay.json
```

必须核对但不要修改，除非发现与本轮 timestamp 修复直接相关的登记字段：

```text
project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
project_state/local_reverse_training_status.json
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 training_dataset？
3. task_packet 是否仅为 advisory？
4. 是否没有生成 candidate、没有运行样本、没有 runtime validation？
5. 是否没有执行 IDA/Ghidra/static extraction？
6. status_overlay.json 中 cpp2_883e67b9 的实际 solved_at 是多少？
7. sync artifact after_overlay_entry 是否与 status_overlay.json 的 cpp2_883e67b9 entry 完全一致？
8. sync artifact 的 after_overlay_entry.solved_at 是否为 2026-06-08T14:42:30Z？
9. artifact_index latest_artifacts_v2 中 sync artifact 的 sha256 / size_bytes 是否已重新计算并同步？
10. artifact_refs 中 sync artifact 的 sha256 / size_bytes 是否同步，如存在？
11. codex_report_summary.files_changed 是否与实际 git diff --name-status 一致？
12. 是否没有修改 .codex-skills？
13. 是否没有提交根目录工具 dump？
14. 是否没有读取或提交 full solve_reports / PROJECT_PROGRESS_LOG？
15. 是否运行 JSON parse 校验？
16. 是否运行 py_compile？
17. 是否运行相关 pytest？结果是多少？
18. 是否运行 lint-decision、lint-report、project_state status？
19. 是否运行 git diff --check、git status --short、git diff --name-status？
20. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Read actual overlay entry

从 `training_materials/local_reverse/status_overlay.json` 读取 `sample_id=cpp2_883e67b9` 的完整 entry，作为唯一 after_overlay_entry 来源。

不得手写猜测 timestamp。不得用当前时间替代实际 overlay 文件中的 `solved_at`。

### Phase B — Repair sync artifact

修正：

```text
project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json
```

要求：

```text
after_overlay_entry == status_overlay.json.samples[cpp2_883e67b9]
```

至少必须满足：

```text
after_overlay_entry.solved_at=2026-06-08T14:42:30Z
```

保持：

```text
mainline=training_dataset
artifact_kind=local_reverse_training_status_overlay_sync
sample_id=cpp2_883e67b9
status_sync_performed=true
candidate_generated=false
runtime_validation_attempted=false
ida_ghidra_static_extraction_attempted=false
training_status_modified=false
status_overlay_modified=true
```

### Phase C — Update index and reports

重新计算 sync artifact 的真实 sha256 / size_bytes，更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index latest_artifacts_v2 entry 应保持：

```text
local_reverse_cpp2_883e67b9_training_status_overlay_sync
kind=local_reverse_training_status_overlay_sync
path=project_state\local_reverse_cpp2_883e67b9_training_status_overlay_sync.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_training_overlay_sync_artifact_rework_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
status_sync_performed=true
training_status_modified=false
status_overlay_modified=true
candidate_generated=false
runtime_validation_attempted=false
sha256=<真实值>
size_bytes=<真实值>
modified_at=<当前更新时间>
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json', encoding='utf-8'))"
.venv\Scripts\python -c "import json; json.load(open('training_materials/local_reverse/status_overlay.json', encoding='utf-8'))"
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_training.py reverse_agent/local_reverse_training_status.py reverse_agent/sample_metadata.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. sync artifact 的 after_overlay_entry 仍与 status_overlay.json 实际 entry 不一致。
2. after_overlay_entry.solved_at 仍不是 2026-06-08T14:42:30Z，且没有同步修改 overlay 文件本身的充分理由。
3. artifact_index 中 sync artifact 的 sha256 / size_bytes 未更新为真实值。
4. 需要重新生成 candidate、运行样本、runtime validation、IDA/Ghidra/static extraction。
5. 需要修改 solver production code 或新建工具接口。
6. JSON parse、lint-report、project_state status 或 tests 失败。
7. git diff 包含根目录工具 dump、full solve_reports、.codex-skills 动态事实或无关代码变更。
8. 修改了 cpp2_883e67b9 以外样本状态。
```

完成后不要推进新样本求解。若该返工通过，下一轮可规划训练集能力复盘：统计 `cpp2_883e67b9` 的题型标签、工具证据链、成功路径、可复用 solver/profile 缺口，但不得把单样本 candidate 写入长期 skill。