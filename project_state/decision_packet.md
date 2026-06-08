```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_training_status_overlay_sync_v1",
  "round_id": "round_20260608_cpp2_883e67b9_training_status_overlay_sync_v1",
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

目标：在不重新解题、不重跑样本、不执行 runtime validation、不执行 IDA/Ghidra/static extraction 的前提下，把 `cpp2_883e67b9` 已通过 runtime validation solved 的状态同步到训练集 overlay 和轻量状态同步 artifact。

当前已 ACCEPTED 的事实：

```text
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
candidate=KaiJu_YiZhi_PEN
validation_status=VALIDATED_SUCCESS
source artifact=project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
artifact_index.latest_artifacts_v2.local_reverse_cpp2_883e67b9_candidate_validation freshness=current
```

本轮必须完成：

```text
1. 读取默认 project_state 文件，确认 decision_packet 是唯一执行权威，task_packet 仅为 advisory。
2. 读取并核对 current candidate_validation artifact 与 artifact_index latest_artifacts_v2 entry。
3. 核对 project_state/local_reverse_training_status.json 中 cpp2_883e67b9 已为 solved。
4. 同步 training_materials/local_reverse/status_overlay.json：
   - 将 cpp2_883e67b9 从 inventory_only 更新为 solved；
   - known_candidate=KaiJu_YiZhi_PEN；
   - blocked_reason=""；
   - solved_by=console_runtime_validation；
   - solved_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1 或更精确的 accepted validation round；
   - evidence_source=project_state/local_reverse_cpp2_883e67b9_candidate_validation.json。
5. 更新 status_overlay.json 的 status_summary：solved 应从 4 到 5，inventory_only 应从 21 到 20，blocked 保持 4，needs_triage 保持 0。
6. 生成轻量同步 artifact：
   project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json
7. 更新 artifact_index，将该 sync artifact 登记到 latest_artifacts、latest_artifacts_v2、artifact_refs，freshness=current，source_run 为当前 round，并写入真实 sha256 / size_bytes。
8. 更新 codex_execution_report.md 和 pytest_result.txt，绑定当前 decision/report/round。
```

本轮不得生成 candidate，不得验证 candidate，不得运行样本，不得运行 IDA/Ghidra/debugger/hook/probe/emulator/winpty，不得修改 solver production code，不得读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍包含旧 samplereverse / compare-aware 摘要，但在本轮只作为 advisory，不控制执行。

`artifact_index.latest_artifacts_v2.local_reverse_cpp2_883e67b9_candidate_validation` 已是 current，并记录：

```text
kind=local_reverse_candidate_validation
source_run=round_20260608_cpp2_883e67b9_candidate_schema_exact_rework_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
candidate_generated=true
candidate_validation_attempted=true
runtime_validation_attempted=true
validation_status=VALIDATED_SUCCESS
```

`project_state/local_reverse_cpp2_883e67b9_candidate_validation.json` 已完整闭合：

```text
artifact_kind=local_reverse_candidate_validation
identity_verified=true
candidate_plaintext=KaiJu_YiZhi_PEN
candidate_hex=4b61694a755f59695a68695f50454e
candidate_length=15
validation.status=VALIDATED_SUCCESS
status_update_recommendation.training_status_already_updated=true
status_overlay_update_needed=false was previously recorded, but actual status_overlay remains stale and must be reconciled.
```

`project_state/local_reverse_training_status.json` 已把 `cpp2_883e67b9` 标为 solved：

```text
training_status=solved
known_candidate=KaiJu_YiZhi_PEN
classification=console_runtime_validation
evidence_sources includes source:local_reverse_cpp2_883e67b9_candidate_validation.json, console_runtime_validation, runtime_validated_success
next_action=sample solved by console runtime validation; no further solving required
```

`training_materials/local_reverse/status_overlay.json` 当前仍旧：

```text
status_summary.solved=4
status_summary.inventory_only=21
cpp2_883e67b9.training_status=inventory_only
cpp2_883e67b9.known_candidate=""
```

所以本轮只做训练集状态 overlay 的最小同步和审计登记。

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
16. 不要把本轮变成新样本求解或工程重构。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 current candidate_validation artifact。
3. 读取和更新 training_materials/local_reverse/status_overlay.json。
4. 读取并只在必要时核对 project_state/local_reverse_training_status.json。
5. 生成 project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json。
6. 更新 artifact_index 登记 sync artifact。
7. 更新 codex_execution_report.md 和 pytest_result.txt。
8. 运行 JSON parse、py_compile、pytest、lint、project_state status、git diff check。
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
project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
```

必须检查已有能力，避免重复造轮子：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_training.py
reverse_agent/local_reverse_training_status.py
reverse_agent/sample_metadata.py
tests/test_project_state.py
```

必要时搜索：

```text
status_overlay
local_reverse_training_status
local_reverse_inventory
training_status
cpp2_883e67b9
status_summary
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
4. 是否确认本轮没有生成 candidate、没有运行样本、没有 runtime validation？
5. 是否确认没有执行 IDA/Ghidra/static extraction？
6. 是否确认 candidate_validation artifact 是 current 且 validation_status=VALIDATED_SUCCESS？
7. 是否确认 local_reverse_training_status 中 cpp2_883e67b9 已 solved？
8. status_overlay 中 cpp2_883e67b9 是否已从 inventory_only 同步为 solved？
9. status_overlay summary 是否更新为 solved=5、blocked=4、needs_triage=0、inventory_only=20？
10. 是否生成 training_status_overlay_sync artifact？
11. sync artifact 是否记录 before/after、source artifact、source_run、candidate、validation status、summary delta？
12. artifact_index 是否登记 sync artifact 到 latest_artifacts、latest_artifacts_v2、artifact_refs，freshness=current、source_run 当前 round、sha256/size_bytes 真实？
13. 是否没有修改 .codex-skills？
14. 是否没有提交根目录工具 dump？
15. 是否没有读取或提交 full solve_reports / PROJECT_PROGRESS_LOG？
16. codex_report_summary.files_changed 是否与实际 git diff --name-status 一致？
17. 是否运行 JSON parse 校验？
18. 是否运行 py_compile？
19. 是否运行相关 pytest？结果是多少？
20. 是否运行 lint-decision、lint-report、project_state status？
21. 是否运行 git diff --check、git status --short、git diff --name-status？
22. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Evidence check

确认：

```text
candidate_validation freshness=current
candidate_validation.validation.status=VALIDATED_SUCCESS
sample_id=cpp2_883e67b9
candidate_plaintext=KaiJu_YiZhi_PEN
local_reverse_training_status entry is solved
status_overlay entry is stale/inventory_only before update
```

如 candidate_validation 不是 current、validation_status 不是 VALIDATED_SUCCESS、或 sample identity 不匹配，停止并报告 BLOCKED。

### Phase B — Minimal status_overlay sync

只修改 `training_materials/local_reverse/status_overlay.json` 中：

```text
1. status_summary solved / inventory_only counts；
2. cpp2_883e67b9 sample entry；
3. generated_at / sync metadata if the file already uses such field。
```

目标 sample entry：

```text
sample_id=cpp2_883e67b9
training_status=solved
known_candidate=KaiJu_YiZhi_PEN
blocked_reason=""
solved_by=console_runtime_validation
solved_at=<current timestamp>
solved_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
evidence_source=project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
```

不要改其他样本状态，除非发现 JSON parse 必需格式修正；若改动其他样本，必须停止并说明原因。

### Phase C — Sync artifact

生成：

```text
project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json
```

artifact 必须包含：

```text
schema_version
mainline=training_dataset
artifact_kind=local_reverse_training_status_overlay_sync
sample_id
relative_path
round_id
decision_id
source_artifacts with freshness/source_run
before_overlay_entry
after_overlay_entry
before_status_summary
after_status_summary
summary_delta
candidate_plaintext
validation_status
status_sync_performed=true
candidate_generated=false
runtime_validation_attempted=false
ida_ghidra_static_extraction_attempted=false
training_status_modified=false
status_overlay_modified=true
```

### Phase D — artifact_index / report / tests

Update:

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index latest_artifacts_v2 entry:

```text
local_reverse_cpp2_883e67b9_training_status_overlay_sync
kind=local_reverse_training_status_overlay_sync
path=project_state\local_reverse_cpp2_883e67b9_training_status_overlay_sync.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_training_status_overlay_sync_v1
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

If local training/status tests exist, run the narrow relevant tests and record them. Do not add broad test scope or long-running evaluation.

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. candidate_validation artifact 不是 current 或 validation_status 不是 VALIDATED_SUCCESS。
2. local_reverse_training_status 中 cpp2_883e67b9 未 solved。
3. status_overlay update 需要改动 cpp2_883e67b9 以外样本状态。
4. 需要重新生成 candidate、运行样本、runtime validation、IDA/Ghidra/static extraction。
5. 需要修改 solver production code 或新建工具接口。
6. artifact_index 无法登记 sync artifact 的 current provenance、sha256 或 size_bytes。
7. JSON parse、lint-report、project_state status 或 tests 失败。
8. git diff 包含根目录工具 dump、full solve_reports、.codex-skills 动态事实或无关代码变更。
```

完成后不要推进新样本求解。若该同步通过，下一轮可规划训练集能力复盘：统计本轮 cpp2_883e67b9 的题型标签、工具证据链、成功路径、可复用 solver/profile 缺口，但不得把单样本 candidate 写入长期 skill。