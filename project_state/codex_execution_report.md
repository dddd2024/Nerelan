```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_cpp2_883e67b9_projection_provenance_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_projection_provenance_rework_v1",
  "based_on_decision_id": "decision_20260608_cpp2_883e67b9_projection_provenance_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "mainline": "engineering_branch",
  "sample_id": "cpp2_883e67b9",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-decision --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-report --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state status --state-dir project_state",
    ".venv\\Scripts\\python -m py_compile reverse_agent/project_state.py",
    ".venv\\Scripts\\python -m pytest -q tests/test_project_state.py",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": [],
  "referenced_artifacts": [
    "project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json"
  ]
}
```

# Codex Execution Report

## 1. Decision Authority Check

- [x] decision_packet 是唯一执行权威
- [x] mainline 为 engineering_branch
- [x] task_packet 仅为 advisory
- [x] 本轮只修 artifact provenance / report / test record，不改 projection 内容、不改 solver、不推进样本求解
- [x] 确认没有运行样本、runtime validation、debugger、hook、emulator、probe、winpty
- [x] 确认没有调用 IDA/Ghidra 或重新读取样本二进制
- [x] 没有修改 solver production code
- [x] 没有修改 tests
- [x] 没有修改 local_reverse_training_status.json
- [x] 没有修改 training_materials/local_reverse/status_overlay.json
- [x] 没有读取 full solve_reports 或 PROJECT_PROGRESS_LOG
- [x] 运行 lint-decision
- [x] 运行 lint-report
- [x] 运行 project_state status
- [x] 运行 git diff --check、git status --short、git diff --name-status
- [x] git diff 只包含允许文件

## 2. Artifact Provenance Fix

### 计算结果

对 `project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json` 计算真实 provenance：

| 字段 | 旧值 | 新值 |
|------|------|------|
| sha256 | "" | `c5e7497de490be4944880908bec8b42e761a5fa4b6831e1aa9763899d9312f62` |
| size_bytes | 0 | 11835 |

### 更新内容

- `project_state/artifact_index.json` 中 `latest_artifacts_v2.local_reverse_cpp2_883e67b9_structured_evidence_projection` 的 sha256 和 size_bytes 已更新为真实值。
- 其他字段保持不变：
  - kind=local_reverse_structured_evidence_projection
  - path=project_state\local_reverse_cpp2_883e67b9_structured_evidence_projection.json
  - freshness=current
  - source_run=round_20260608_cpp2_883e67b9_structured_evidence_projection_v1（artifact 内容未变，仅修正 index provenance）
  - sample_id=cpp2_883e67b9
  - relative_path=逆向课程2024春02/CPP2.exe
  - projection_status=READY_WITH_LIMITATIONS
  - candidate_generated=false
  - candidate_validation_attempted=false
  - runtime_validation_attempted=false
  - training_status_modified=false
  - status_overlay_modified=false

### 内容一致性确认

- projection artifact 文件内容未被修改。
- artifact_index 中 latest_artifacts 与 artifact_refs 仍指向同一 artifact path。

## 3. Tests

### lint-decision
```
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
```
结果：PASS

### lint-report
```
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
```
结果：PASS

### project_state status
```
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
```
结果：PASS

### py_compile
```
.venv\Scripts\python -m py_compile reverse_agent/project_state.py
```
结果：PASS（无语法错误）

### pytest
```
.venv\Scripts\python -m pytest -q tests/test_project_state.py
```
结果：PASS

### git checks
```
git diff --check -> PASS
git status --short -> (recorded)
git diff --name-status -> (recorded)
```

## 4. Stop Conditions

无停止条件触发。sha256 和 size_bytes 已更新为真实值，artifact_index 与实际 artifact 文件一致，未修改 solver/tests/training status/status overlay，git diff 只包含允许文件。

## 5. Next Steps

- 本轮 provenance rework 完成，artifact_index 中该 artifact 的 provenance 现已可核验。
- 不推进 candidate generation 或 runtime validation，不进入 reverse_solving。
