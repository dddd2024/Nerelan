```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_projection_provenance_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_projection_provenance_rework_v1",
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

目标：修复上一轮 `cpp2_883e67b9_structured_evidence_projection` 的 artifact provenance 记录。

当前唯一阻断点：

```text
artifact_index.latest_artifacts_v2["local_reverse_cpp2_883e67b9_structured_evidence_projection"].sha256 == ""
artifact_index.latest_artifacts_v2["local_reverse_cpp2_883e67b9_structured_evidence_projection"].size_bytes == 0
```

本轮只修 provenance / report / test record，不改 projection 内容、不改 solver、不推进样本求解。

必须完成：

```text
1. 对 project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json 计算真实 sha256 和 size_bytes。
2. 更新 project_state/artifact_index.json 中 local_reverse_cpp2_883e67b9_structured_evidence_projection 的 sha256 / size_bytes。
3. 保持 freshness=current、source_run=round_20260608_cpp2_883e67b9_structured_evidence_projection_v1 或明确说明是否改为本轮 rework round。
4. 更新 project_state/codex_execution_report.md，绑定当前 rework decision/report/round。
5. 更新 project_state/pytest_result.txt，绑定当前 rework decision/report/round。
6. 重新运行并记录 project_state lint/status 和 git diff 检查。
```

建议产出：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

默认不要修改：

```text
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
reverse_agent/
tests/
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮提交：

```text
commit=7990b4091b123e943925d09335f44ef8bf8fba32
message=feat(project_state): add structured evidence projection for cpp2_883e67b9
round=round_20260608_cpp2_883e67b9_structured_evidence_projection_v1
decision=decision_20260608_cpp2_883e67b9_structured_evidence_projection_v1
```

上一轮可接受部分：

```text
1. 新增 structured evidence projection artifact。
2. codex_execution_report.md identity 已匹配 structured evidence projection 轮。
3. pytest_result.txt 记录 py_compile、pytest、lint/status/git checks。
4. diff 没有修改 solver/tests/training status/status overlay。
5. candidate_generated=false，candidate_validation_attempted=false，runtime_validation_attempted=false。
6. mainline=tool_integration，未进入 reverse_solving。
```

上一轮不可接受部分：

```text
artifact_index.latest_artifacts_v2.local_reverse_cpp2_883e67b9_structured_evidence_projection.sha256 为空。
artifact_index.latest_artifacts_v2.local_reverse_cpp2_883e67b9_structured_evidence_projection.size_bytes 为 0。
```

原因：current artifact 的 provenance 必须可核验。空 hash / 0 size 不能作为 current 可信证据。

当前 training summary 应保持不变：

```text
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
```

`negative_results.json` 主要约束旧 samplereverse 路线；本轮仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要运行 E:\reverse 样本。
2. 不要生成或验证 candidate。
3. 不要 runtime validation / debugger / hook / emulator / probe / winpty。
4. 不要调用 IDA/Ghidra。
5. 不要重新做二进制分析。
6. 不要改 solver production code。
7. 不要改 tests。
8. 不要改 local_reverse_training_status.json。
9. 不要改 training_materials/local_reverse/status_overlay.json。
10. 不要读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
11. 不要把本轮扩张成 reverse_solving。
12. 不要修改 projection artifact 内容；如果 hash 计算前后发现内容变化，停止并报告。
13. 不要把 task_packet.task 当执行权威。
14. 不要把 sha256 仍为空或 size_bytes 仍为 0 的 artifact 标为 current 可接受。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 projection artifact 本身以计算 sha256/size。
3. 修改 artifact_index.json 中该 artifact 的 sha256/size_bytes provenance。
4. 修改 codex_execution_report.md 和 pytest_result.txt 以绑定当前 rework。
5. 运行 project_state lint/status 与 git diff 检查。
```

---

## 4. Files To Inspect

必须读取：

```text
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/artifact_index.json
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
project_state/task_packet.json
project_state/current_state.json
project_state/negative_results.json
.codex-skills/registry.json
```

必要时读取：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse 样本文件
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 engineering_branch？
3. task_packet 是否仅为 advisory？
4. 是否只修 artifact provenance/report/test record？
5. 新 artifact 的真实 sha256 是什么？
6. 新 artifact 的真实 size_bytes 是多少？
7. artifact_index.latest_artifacts_v2 是否已更新真实 sha256/size？
8. latest_artifacts 与 artifact_refs 是否仍指向同一 artifact path？
9. 是否未修改 projection artifact 内容？如果修改了，为什么？
10. 是否未运行样本、IDA/Ghidra、debugger、hook、probe、winpty？
11. 是否未改 solver/tests/training status/status overlay？
12. 是否重新运行 lint-decision？
13. 是否重新运行 lint-report？
14. 是否重新运行 project_state status？
15. 是否运行 git diff --check？
16. 是否记录 git status --short 和 git diff --name-status？
17. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Calculate real projection artifact provenance

对文件计算真实 sha256 和 size：

```text
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
```

要求：

```text
1. 不修改该 artifact 内容。
2. 计算结果必须写入报告。
3. 如果本地工作区中的文件与 GitHub/当前索引不一致，立即停止并报告。
```

### Phase B — Update artifact_index provenance

只更新 `project_state/artifact_index.json` 中：

```text
latest_artifacts_v2.local_reverse_cpp2_883e67b9_structured_evidence_projection.sha256
latest_artifacts_v2.local_reverse_cpp2_883e67b9_structured_evidence_projection.size_bytes
```

并确认以下字段仍存在且合理：

```text
kind=local_reverse_structured_evidence_projection
path=project_state\local_reverse_cpp2_883e67b9_structured_evidence_projection.json
freshness=current
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
projection_status=READY_WITH_LIMITATIONS
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

source_run 可保持上一轮 source artifact 生成 run：

```text
round_20260608_cpp2_883e67b9_structured_evidence_projection_v1
```

如果 Codex 改为本轮 rework round，必须解释 provenance 语义：artifact 内容未变，只是 index provenance 修正。

### Phase C — Update report and pytest_result

更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必须使用当前 identity：

```text
report_id=report_20260608_cpp2_883e67b9_projection_provenance_rework_v1
round_id=round_20260608_cpp2_883e67b9_projection_provenance_rework_v1
based_on_decision_id=decision_20260608_cpp2_883e67b9_projection_provenance_rework_v1
mainline=engineering_branch
sample_id=cpp2_883e67b9
```

`files_changed` 应只包含允许文件：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果 projection artifact 内容未改，不要把它放入 files_changed；可以在 generated_artifacts 或 referenced_artifacts 中说明它是被修正 provenance 的 existing artifact。

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

建议运行：

```text
.venv\Scripts\python -m py_compile reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
```

如果报告继续声明完整 pytest 通过，必须真实重跑并记录完整 pytest 命令；否则不要复用上一轮 `179 passed`。

---

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` / `BLOCKED`，如果出现任一情况：

```text
1. sha256 仍为空。
2. size_bytes 仍为 0。
3. artifact_index 与实际 artifact 文件不一致。
4. 需要修改 solver/tests 才能通过。
5. 需要运行样本或调用 IDA/Ghidra/debugger/hook/probe/winpty。
6. report/pytest_result identity 不匹配当前 rework decision。
7. projection artifact 内容被修改但没有充分说明。
8. git diff 包含允许范围外文件。
```

本轮完成后不要进入 reverse_solving。
