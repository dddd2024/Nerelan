```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260605_cpp1_target_bytes_length_rework_v1",
  "round_id": "round_20260605_cpp1_target_bytes_length_rework_v1",
  "based_on_decision_id": "decision_20260605_cpp1_target_bytes_length_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPT",
  "files_changed": [
    "reverse_agent/ida_scripts/extract_named_data.py",
    "reverse_agent/local_reverse_cpp1_target_byte_extract.py",
    "tests/test_local_reverse_cpp1_target_byte_extract.py",
    "project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/ida_scripts/extract_named_data.py",
    "python -m py_compile reverse_agent/local_reverse_cpp1_target_byte_extract.py",
    "python -m pytest -q tests/test_local_reverse_cpp1_target_byte_extract.py",
    "python -m pytest -q tests/test_project_state.py",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.local_reverse_cpp1_target_byte_extract --sample-id cpp1_2f6fcb63 --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json",
    "git diff --check",
    "git status --short"
  ],
  "test_results": {
    "py_compile_extract_script": "PASSED (Exit code 0)",
    "py_compile_target_byte_extract": "PASSED (Exit code 0)",
    "pytest_target_bytes": "PASSED (29 passed)",
    "pytest_project_state": "PASSED (157 passed)",
    "lint_decision": "PASSED",
    "lint_report": "PASSED (after report update)",
    "target_byte_cli": "PASSED (Exit code 0, tool_status=success, target_length=16)",
    "git_diff_check": "PASSED",
    "git_status": "PASSED"
  }
}
```

# Codex Execution Report

## 1. 执行权威与轮次说明

- **当前 decision_packet**：`project_state/decision_packet.md` 是本轮唯一执行权威。
- **本轮性质**：tool_integration - cpp1_2f6fcb63 target bytes length rework。
- **主线**：`tool_integration`。
- **本轮 decision_id**：`decision_20260605_cpp1_target_bytes_length_rework_v1`。
- **上一轮状态**：`decision_20260605_cpp1_target_byte_extraction_v1` 审计结论为 `REWORK_REQUIRED`。

## 2. 返工原因与目标

上一轮存在关键问题：

```text
target_bytes_hex 只有 1 字节，而 compare loop 是 16 字节。

expected behavior：
- target_bytes_hex 应该包含 16 字节（或至少 >=16 字节）
- 如果不足 16 字节，artifact 应该 blocked，并记录 actual_target_bytes_hex

actual behavior：
- target_bytes_hex 只有 1 字节（d5），没有 blocked
- 没有 expected_target_length 字段
```

本轮目标：**确保 target bytes 长度 >= expected_target_length (16)，否则 blocked。**

## 3. 执行结果

### 3.1 Required Tests（全部通过）

| # | 命令 | Exit Code | 结果 |
|---|------|-----------|------|
| 1 | py_compile extract_named_data.py | 0 | PASSED |
| 2 | py_compile target_byte_extract.py | 0 | PASSED |
| 3 | pytest target_bytes (29 passed) | 0 | PASSED |
| 4 | pytest project_state (157 passed) | 0 | PASSED |
| 5 | lint-decision | 0 | PASSED |
| 6 | lint-report | 0 | PASSED |
| 7 | target byte CLI | 0 | PASSED |
| 8 | git diff --check | 0 | PASSED |
| 9 | git status --short | 0 | PASSED |

### 3.2 核心代码修改

**extract_named_data.py**:
- 新增 `REVERSE_AGENT_TARGET_LENGTH` 环境变量支持
- 允许显式指定读取长度（默认回退到 `ida_bytes.get_item_size`）

**local_reverse_cpp1_target_byte_extract.py**:
- 新增 `expected_target_length=16` 参数
- 在 `_run_ida_extraction` 中设置 `REVERSE_AGENT_TARGET_LENGTH=16`
- 在 `run_static_triage` 中校验 `actual_target_length >= expected_target_length`
- 不足时返回 `BLOCKED/INCOMPLETE_TARGET_BYTES`，并记录实际字节
- `_blocked_artifact` 新增 `expected_target_length`、`actual_target_length`、`actual_target_bytes`、`actual_target_bytes_hex` 字段

### 3.3 Artifact 验证

| 字段 | 值 | 状态 |
|------|-----|------|
| tool_status | success | ✅ |
| target_symbol | byte_429A30 | ✅ |
| target_address | 0x00429A30 | ✅ |
| target_length | **16** | ✅ (之前是 1) |
| target_bytes_hex | d596c4f607455777... | ✅ (32 hex chars = 16 bytes) |
| expected_target_length | 16 | ✅ (新增字段) |
| executed_sample | False | ✅ |
| static_only | True | ✅ |
| runtime_validated | False | ✅ |
| candidate | None | ✅ |
| known_candidate | "" | ✅ |

### 3.4 测试覆盖

新增测试 `test_ida_incomplete_bytes_blocked`：
- 模拟 IDA 返回 1 字节（< 16）
- 验证返回 `BLOCKED/INCOMPLETE_TARGET_BYTES`
- 验证 `expected_target_length=16`、`target_length=1`
- 验证 `target_bytes_hex` 和 `target_bytes` 记录实际值

## 4. 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `reverse_agent/ida_scripts/extract_named_data.py` | 修改 | 支持 `REVERSE_AGENT_TARGET_LENGTH` 环境变量 |
| `reverse_agent/local_reverse_cpp1_target_byte_extract.py` | 修改 | 添加 `expected_target_length` 校验和 blocked 处理 |
| `tests/test_local_reverse_cpp1_target_byte_extract.py` | 修改 | 新增 `test_ida_incomplete_bytes_blocked`，更新 `test_ida_success_but_no_bytes_blocked` |
| `project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json` | 重新生成 | target_length=16，新增 expected_target_length 字段 |
| `project_state/artifact_index.json` | 修改 | 更新 sha256 和 source_run |
| `project_state/codex_execution_report.md` | 修改 | 更新为当前 round |
| `project_state/pytest_result.txt` | 修改 | 更新为当前 round |

## 5. 审计合规声明

| # | 审计项 | 状态 |
|---|--------|------|
| 1 | 确认当前 decision_packet 是本轮唯一执行权威 | ✅ |
| 2 | 确认 task_packet.task 只是 advisory | ✅ |
| 3 | 确认本轮主线为 tool_integration | ✅ |
| 4 | 修改 extract_named_data.py 支持 REVERSE_AGENT_TARGET_LENGTH | ✅ |
| 5 | 修改 local_reverse_cpp1_target_byte_extract.py 添加 expected_target_length=16 | ✅ |
| 6 | 添加长度校验：actual < expected -> INCOMPLETE_TARGET_BYTES | ✅ |
| 7 | blocked artifact 包含 expected_target_length 和 actual_target_bytes | ✅ |
| 8 | 重新运行 CLI，验证 target_length=16 | ✅ |
| 9 | 更新测试覆盖不足 16 字节场景 | ✅ |
| 10 | 29 个测试全部通过 | ✅ |
| 11 | 更新 artifact_index sha256 和 source_run | ✅ |
| 12 | 更新 codex_execution_report.md 和 pytest_result.txt | ✅ |
| 13 | 没有动态执行样本 | ✅ |
| 14 | artifact 仍为 executed_sample=false / static_only=true / runtime_validated=false | ✅ |
| 15 | artifact 仍为 candidate=null / known_candidate="" | ✅ |
| 16 | codex_report_summary.based_on_decision_id 等于 decision_20260605_cpp1_target_bytes_length_rework_v1 | ✅ |
