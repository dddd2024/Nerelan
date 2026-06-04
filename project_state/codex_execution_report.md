```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260604_fix_training_status_overlay_audit_v1",
  "round_id": "round_20260604_fix_training_status_overlay_audit_v1",
  "based_on_decision_id": "decision_20260604_fix_training_status_overlay_audit_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPT",
  "files_changed": [
    "reverse_agent/local_reverse_training_status.py",
    "tests/test_local_reverse_training_status.py",
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_evaluation_queue.json",
    "training_materials/local_reverse/status_overlay.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md"
  ],
  "tests_ran": [
    "tests/test_local_reverse_training_status.py",
    "tests/test_local_reverse_inventory.py",
    "tests/test_local_samples.py",
    "tests/test_project_state.py"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_evaluation_queue.json",
    "training_materials/local_reverse/status_overlay.json"
  ]
}
```

# Codex Execution Report

## 1. 执行权威与轮次说明

- **当前 decision_packet**：`project_state/decision_packet.md` 是本轮唯一执行权威。
- **本轮性质**：生成训练集状态层，合并 metadata inventory 与已有 solved/blocked 结果。
- **主线**：`training_dataset`。

## 2. 执行摘要

| 项目 | 值 |
|------|-----|
| 样本总数 | 29 |
| solved | 1 (Cpp1.exe) |
| blocked | 2 (sha_256.exe, CPP2.exe) |
| inventory_only | 26 |
| evaluation_queue 条目数 | 23 |

## 3. 新增模块说明

### `reverse_agent/local_reverse_training_status.py`

- CLI：`python -m reverse_agent.local_reverse_training_status`
- 参数：
  - `--inventory`：metadata inventory 路径
  - `--validated`：validated candidate handoff 路径
  - `--constraint-recovery`：constraint recovery 结果路径
  - `--solver-result`：IDA solver result 路径
  - `--out`：training status JSON 输出
  - `--queue-out`：evaluation queue JSON 输出
  - `--github-status-out`：GitHub-safe status overlay JSON 输出
- 功能：
  - 读取 inventory 和已有结果文件
  - 合并生成每个样本的 training status（solved/blocked/inventory_only）
  - 生成 prioritized evaluation queue（排除 solved/blocked，优先简单静态题）
  - 生成 GitHub-safe status overlay（不含本地绝对路径）

### `tests/test_local_reverse_training_status.py`

- 11 个测试覆盖：
  - solved map 构建（仅 validated 状态计入 solved）
  - blocked map 构建（仅 blocked 状态计入 blocked）
  - sample entry 构建（solved/blocked 状态正确）
  - evaluation queue 排除 solved/blocked
  - evaluation queue 排除 solver scripts
  - end-to-end 集成测试（Cpp1 solved, sha_256 blocked, CPP2 blocked, rc4enc inventory_only）
  - 无真实本地路径泄漏
  - CLI 主函数测试
  - Cpp1 不会被误标为 solved（未 validated 时）
  - evaluation queue 优先级排序（simple tags 优先）

## 4. 状态合并逻辑

### Sample ID 匹配策略

- inventory 使用 `sample_id`（文件名 + sha256 前缀）
- 已有结果文件使用 sha256 前 16 位作为 `sample_id`
- 匹配时先尝试完整 `sample_id`，再尝试 `sha256[:16]` 短 ID

### 状态优先级

1. **solved**：validated handoff 中 `validation_status == "validated"`
2. **blocked**：constraint recovery 中 `constraint_status == "blocked"`
3. **inventory_only**：无已有结果

### Evaluation Queue 排序

1. 排除 solved 和 blocked
2. 排除 solver scripts（文件名含 solver/script/decrypt/encrypt/interactive）
3. 优先 simple static tags：xor, shift, strcmp, array_compare, base64
4. 其次 crypto tags：rc4, des, aes
5. 最后 deferred tags：hash, packed_or_obfuscated

## 5. 关键样本状态

| 样本 | 状态 | 原因 |
|------|------|------|
| Cpp1.exe (逆向课程2022春补考01) | **solved** | validated candidate = "hookapi" |
| sha_256.exe (逆向课程2024春01) | **blocked** | NO_BOUNDED_HASH_PREIMAGE_DOMAIN |
| CPP2.exe (逆向课程2022春02) | **blocked** | MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005 |
| rc4enc.exe 等 23 个 | **inventory_only** | 待静态分析评估 |

## 6. 审计合规声明

| # | 审计项 | 状态 |
|---|--------|------|
| 1 | 复用了 local_reverse_inventory.py | ✅ |
| 2 | 复用了/整合了 local_reverse_corpus.py，未新建第三套 scanner | ✅ |
| 3 | 读取了已有 validated/blocked 结果 | ✅ |
| 4 | Cpp1.exe 被标记为 solved/validated | ✅ |
| 5 | sha_256.exe 被标记为 blocked: NO_BOUNDED_HASH_PREIMAGE_DOMAIN | ✅ |
| 6 | CPP2.exe 被标记为 blocked，未误标为 solved | ✅ |
| 7 | 生成了 local_reverse_training_status.json | ✅ |
| 8 | 生成了 local_reverse_evaluation_queue.json | ✅ |
| 9 | evaluation queue 优先选择简单、可静态分析、未 solved 的样本 | ✅ |
| 10 | 没有上传原始样本 | ✅ |
| 11 | 没有运行动态分析或 solver | ✅ |
| 12 | pytest_result.txt 记录真实测试命令 | ✅ |
| 13 | codex_report_summary.based_on_decision_id 等于 decision_20260604_local_reverse_training_status_overlay_v1 | ✅ |

## 7. 停止条件检查

本轮未触发任何停止条件：
- inventory sample_id 与已有结果可靠匹配 ✅
- 未与 local_reverse_corpus.py 的 sample_id 规则冲突 ✅
- 未运行 solver 或动态验证 ✅
- 未读取完整 solve_reports ✅
- 输出未泄露本地绝对路径 ✅

## 8. 下一步建议

- evaluation queue 中的 23 个 inventory_only 样本可按优先级逐步进行静态分析。
- 优先处理 queue 中 rank 靠前的 simple static 样本（xor/shift/strcmp/array_compare/base64）。
- hash 题（如 sha_256.exe）需要 bounded domain 证据后才能继续。
- DES/RC4 等 crypto 题作为第二批处理。
