```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_local_reverse_state_freshness_rebuild_v1",
  "round_id": "round_20260608_local_reverse_state_freshness_rebuild_v1",
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

目标：在 `cpp2_883e67b9` 已完成 candidate validation 与 training overlay sync 返工后，刷新并审计 `project_state` 动态状态，使 `current_state.json`、`task_packet.json`、`artifact_index.json`、`codex_execution_report.md`、`pytest_result.txt` 与当前训练集状态一致。

本轮不是新样本求解轮，不进入 `reverse_solving`。本轮不得生成 candidate，不得运行样本，不得 runtime validation，不得执行 IDA/Ghidra/debugger/hook/emulator/winpty，不得读取或提交完整 `solve_reports/`。

必须完成：

```text
1. 重新确认 project_state/decision_packet.md 是本轮唯一执行权威；task_packet.json 只是 advisory。
2. 读取默认 project_state 文件，并核对上一轮 report/pytest 是否绑定 decision_20260608_cpp2_883e67b9_training_overlay_sync_artifact_rework_v1。
3. 核对当前训练状态：status_overlay.json 与 local_reverse_training_status.json 均应为 sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20。
4. 核对 current_state.json 与 task_packet.json 是否仍含旧 solved=4 / inventory_only=21 或把 cpp2_883e67b9 当下一队列样本的 stale hint。
5. 运行或修复现有 project_state build/status 流程，使动态 project_state 反映 solved=5 的当前状态。
6. 若 task_packet/current_state 仍包含 next queue hint，必须保证它指向 inventory_only/unsolved 样本，且明确仍只是 advisory；不得继续指向已 solved 的 cpp2_883e67b9。
7. 生成一个小型审计 artifact，记录 refresh 前后摘要、stale 字段、修复动作、未运行样本/工具的声明。
8. 更新 artifact_index 对该 refresh artifact 的登记，标记 freshness=current、source_run=round_20260608_local_reverse_state_freshness_rebuild_v1。
9. 更新 codex_execution_report.md 与 pytest_result.txt，绑定当前 decision_id/round_id。
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 明确写有 `active_decision_packet=project_state/decision_packet.md`，但其内容仍含 advisory next queue hint，不能直接作为执行任务。

默认状态文件显示存在新鲜度不一致：

```text
1. task_packet/current_state 的 state_build_id 仍为 state_20260602_053948_4e3984041cd7。
2. current_state 中 local_reverse_training_summary 仍是 solved=4、inventory_only=21。
3. task_packet 中 local_reverse_next_queue_hint 仍指向 cpp2_883e67b9，并声明 proposed_next_mainline=tool_integration。
4. 但 cpp2_883e67b9 已在后续轮完成 runtime-backed candidate validation 与 training overlay sync。
```

当前较新的训练事实：

```text
1. training_materials/local_reverse/status_overlay.json：sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20。
2. project_state/local_reverse_training_status.json：sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20。
3. cpp2_883e67b9 overlay entry：training_status=solved，known_candidate=KaiJu_YiZhi_PEN，solved_by=console_runtime_validation，solved_at=2026-06-08T14:42:30Z。
4. project_state/local_reverse_cpp2_883e67b9_candidate_validation.json：candidate_plaintext=KaiJu_YiZhi_PEN，validation.status=VALIDATED_SUCCESS，runtime_validation_attempted=true，rerun_in_this_round=false。
5. project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json 已修复 after_overlay_entry.solved_at=2026-06-08T14:42:30Z。
6. 最新 codex_execution_report.md 为 SUCCESS / ACCEPTED，based_on_decision_id=decision_20260608_cpp2_883e67b9_training_overlay_sync_artifact_rework_v1。
7. pytest_result.txt 绑定上一轮 rework decision/report/round，状态 PASSED，pytest 记录为 158 passed。
```

`artifact_index.json` 已登记 `local_reverse_cpp2_883e67b9_candidate_validation` 与 `local_reverse_cpp2_883e67b9_training_status_overlay_sync`，说明下一轮不能回退到对该样本做 bounded static triage/readiness 的旧 advisory。

`negative_results.json` 仍必须遵守：不回到 old sample_solver blind search，不只扩大 beam/budget，不提交 full solve_reports，不把 stale/missing artifact 当 current，不重复已失败的 samplereverse 方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

已有相关能力边界：

```text
1. 本项目已有 local reverse training/status/project_state 相关模块，本轮优先使用现有 build/status/lint 能力，不新增平行状态系统。
2. 已有 console validator 产物可作为历史已验证事实，但本轮不得重新运行 validator。
3. artifact_index 中存在 IDA/Ghidra/static evidence 相关 artifact，但本轮只是状态新鲜度修复，不执行 IDA/Ghidra/static extraction。
4. 不允许运行 debugger/hook/emulator/winpty/runtime probe。
5. 不允许读取完整 solve_reports；只允许通过 artifact_index 与明确 project_state artifact 读取必要 metadata。
```

---

## 3. Do Not Do

严格禁止：

```text
1. 不要进入 reverse_solving 解题流程。
2. 不要选择、分析、求解或验证新样本。
3. 不要对 cpp2_883e67b9 重新生成 candidate 或重新 runtime validation。
4. 不要运行样本、negative control、console validator、winpty、debugger、hook、emulator、runtime probe。
5. 不要执行 IDA/Ghidra/radare2/objdump/static extraction。
6. 不要 brute force、dictionary search、fuzz、beam/topN、扩大 timeout/budget。
7. 不要新增 solver/harness/runtime/IDA/Ghidra/debugger 接口。
8. 不要修改 solver production code，除非 project_state build/status 存在明确 bug 且修复范围只限状态构建。
9. 不要修改 .codex-skills。
10. 不要提交根目录工具 dump。
11. 不要读取完整 solve_reports。
12. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
13. 不要提交 full solve_reports。
14. 不要把 task_packet.task 或旧 local_reverse_next_queue_hint 当执行权威。
15. 不要把 stale/missing/unknown artifact 当 current。
16. 不要把已 solved 的 cpp2_883e67b9 继续作为下一队列执行目标。
17. 不要把单样本 candidate、flag、本地绝对路径、临时 runtime metric 写入 .codex-skills。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 training_materials/local_reverse/status_overlay.json。
3. 读取 project_state/local_reverse_training_status.json。
4. 读取 project_state/local_reverse_cpp2_883e67b9_candidate_validation.json。
5. 读取 project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json。
6. 读取与 project_state build/status/lint 直接相关的源码和测试。
7. 运行 python -m reverse_agent.project_state build / status / lint-decision / lint-report。
8. 运行 JSON parse、py_compile、focused pytest、git diff checks。
9. 生成 project_state/local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.json 这类小型 metadata-only 审计 artifact。
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
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_training_status.json
project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
project_state/local_reverse_cpp2_883e67b9_training_status_overlay_sync.json
```

若需要修复 build/status 流程，允许有界读取：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_training.py
reverse_agent/local_reverse_training_status.py
reverse_agent/sample_metadata.py
tests/test_project_state.py
相关 local_reverse training/status 测试文件
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
任何本地样本二进制
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. task_packet 是否仅为 advisory？
3. mainline 是否为 engineering_branch？
4. 上一轮 codex_report_summary 是否存在，based_on_decision_id 是否匹配 decision_20260608_cpp2_883e67b9_training_overlay_sync_artifact_rework_v1？
5. 上一轮 pytest_result 是否存在并绑定同一 decision/report/round？
6. status_overlay.json 当前 summary 是否为 sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20？
7. local_reverse_training_status.json 当前 summary 是否为 sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20？
8. current_state.json / task_packet.json 在本轮前是否含 solved=4、inventory_only=21 或 cpp2_883e67b9 stale next queue hint？
9. 本轮后 current_state.json / task_packet.json 是否已反映 solved=5、inventory_only=20？如 build 工具不写这些字段，必须解释并生成 audit artifact 记录限制。
10. 本轮后 task_packet/current_state 是否仍把已 solved 的 cpp2_883e67b9 当下一执行目标？若是，必须 REWORK_REQUIRED。
11. 是否生成了 metadata-only state refresh artifact？
12. artifact_index 是否登记该 refresh artifact，freshness=current，source_run=round_20260608_local_reverse_state_freshness_rebuild_v1？
13. 是否没有生成 candidate、没有运行样本、没有 runtime validation？
14. 是否没有执行 IDA/Ghidra/static extraction/debugger/hook/emulator/winpty？
15. 是否没有修改 .codex-skills？
16. 是否没有读取或提交 full solve_reports / PROJECT_PROGRESS_LOG？
17. codex_report_summary.files_changed 是否与 git diff --name-status 一致？
18. 是否运行 JSON parse 校验？
19. 是否运行 py_compile？
20. 是否运行 focused pytest？结果是多少？
21. 是否运行 lint-decision、lint-report、project_state status？
22. 是否运行 git diff --check、git status --short、git diff --name-status？
23. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Authority and stale-state confirmation

读取默认 project_state 文件，确认：

```text
1. 当前 decision_packet 控制本轮。
2. task_packet 只是 advisory。
3. 上一轮 rework report/pytest 是可审计的 SUCCESS/PASSED。
4. current_state/task_packet 的 local_reverse summary 与 status_overlay/local_reverse_training_status 存在 solved=4 vs solved=5 的新鲜度差异。
5. 旧 next queue hint 不能再指向已 solved 的 cpp2_883e67b9。
```

### Phase B — Use existing project_state build/status path

优先运行现有命令：

```powershell
.venv\Scripts\python.exe -m reverse_agent.project_state build
```

如果 Codex 环境使用 `python` 而不是 `.venv\Scripts\python.exe`，可以改用等价解释器，但报告中必须记录实际命令。

要求：

```text
1. 不允许该命令触发样本运行、runtime validation、debugger、IDA/Ghidra 或读取 full solve_reports。
2. 若 build 命令需要 reports-dir/sample/run 参数才能工作，先停止并报告需要的最小参数；不得盲扫 solve_reports。
3. 若 build 命令成功更新 current_state/task_packet/artifact_index，继续 Phase C。
4. 若 build 命令成功但不覆盖 stale local_reverse 字段，允许小范围修复 project_state build/status 逻辑；修复必须有测试，且不得改 solver/runtime/tool 接口。
```

### Phase C — Refresh dynamic state and audit artifact

目标状态：

```text
current_state/task_packet 中 local reverse training summary 应反映：
sample_count=29
solved=5
blocked=4
needs_triage=0
inventory_only=20
latest solved sample includes cpp2_883e67b9 / KaiJu_YiZhi_PEN / project_state\local_reverse_cpp2_883e67b9_candidate_validation.json
```

若保留 next queue hint：

```text
1. 它必须来自 current status_overlay/local_reverse_training_status 中 inventory_only 或未解决样本。
2. 它必须明确 advisory only。
3. 它不得指向 cpp2_883e67b9。
4. 它不得授权 runtime probe、debugger、hook、emulator、brute force 或上传二进制。
```

生成小型审计 artifact：

```text
project_state/local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.json
```

建议字段：

```json
{
  "schema_version": 1,
  "mainline": "engineering_branch",
  "artifact_kind": "local_reverse_state_freshness_rebuild",
  "decision_id": "decision_20260608_local_reverse_state_freshness_rebuild_v1",
  "round_id": "round_20260608_local_reverse_state_freshness_rebuild_v1",
  "source_status_overlay": "training_materials/local_reverse/status_overlay.json",
  "source_training_status": "project_state/local_reverse_training_status.json",
  "before_summary": {"solved": 4, "blocked": 4, "needs_triage": 0, "inventory_only": 21},
  "after_summary": {"solved": 5, "blocked": 4, "needs_triage": 0, "inventory_only": 20},
  "stale_next_queue_hint_removed_or_replaced": true,
  "candidate_generated": false,
  "runtime_validation_attempted": false,
  "ida_ghidra_static_extraction_attempted": false,
  "debugger_attached": false,
  "emulator_used": false
}
```

更新 `project_state/artifact_index.json`：

```text
latest_artifacts.local_reverse_state_freshness_rebuild_after_cpp2_883e67b9 = project_state\local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.json
latest_artifacts_v2.local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.kind = local_reverse_state_freshness_rebuild
latest_artifacts_v2.local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.path = project_state\local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.json
latest_artifacts_v2.local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.freshness = current
latest_artifacts_v2.local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.source_run = round_20260608_local_reverse_state_freshness_rebuild_v1
latest_artifacts_v2.local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.sha256 = <真实 sha256>
latest_artifacts_v2.local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.size_bytes = <真实 size>
latest_artifacts_v2.local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.modified_at = <实际更新时间>
```

### Phase D — Report and tests

更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

`codex_report_summary` 必须绑定：

```text
based_on_decision_id=decision_20260608_local_reverse_state_freshness_rebuild_v1
round_id=round_20260608_local_reverse_state_freshness_rebuild_v1
mainline=engineering_branch
candidate_generated=false
runtime_validation_attempted=false
debugger_attached=false
emulator_used=false
ida_ghidra_static_extraction_attempted=false
```

---

## 7. Tests

必须运行并记录：

```powershell
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/task_packet.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/current_state.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/artifact_index.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('training_materials/local_reverse/status_overlay.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/local_reverse_training_status.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.json', encoding='utf-8'))"
.venv\Scripts\python.exe -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_training.py reverse_agent/local_reverse_training_status.py reverse_agent/sample_metadata.py
.venv\Scripts\python.exe -m pytest -q tests/test_project_state.py
.venv\Scripts\python.exe -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python.exe -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python.exe -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果项目已有更聚焦的 local reverse training/status 测试，必须追加运行并在报告中列出。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. 需要运行样本、runtime validation、debugger、hook、emulator、winpty、IDA/Ghidra/static extraction。
2. project_state build 会盲扫完整 solve_reports 或需要未知重型上下文。
3. current_state/task_packet 在本轮后仍把 cpp2_883e67b9 当下一执行目标。
4. current_state/task_packet 在本轮后仍保留 solved=4、inventory_only=21，且没有明确说明 build 工具限制与后续修复方案。
5. status_overlay.json 与 local_reverse_training_status.json 对 solved/inventory_only 计数不一致。
6. artifact_index 未登记 refresh artifact 或 freshness/source_run/sha256/size_bytes 缺失。
7. codex_report_summary 缺失或 based_on_decision_id/round_id 不匹配。
8. pytest_result 缺失或未绑定当前 decision/report/round。
9. JSON parse、lint-report、project_state status 或 focused pytest 失败。
10. git diff 包含 full solve_reports、PROJECT_PROGRESS_LOG 全量改动、.codex-skills 动态事实、样本二进制或无关代码变更。
11. 修改了 solver/runtime/tool 接口而没有证明 project_state build/status 必须修复。
```

完成后不要推进新样本求解。若本轮通过，下一轮再进入 `training_dataset` 能力复盘：统计已 solved/blocked 样本的题型标签、工具证据链、成功路径、可复用 solver/profile 缺口，并选择一个未解决样本作为后续 advisory 队列；不得把单样本 candidate 写入长期 skill。
