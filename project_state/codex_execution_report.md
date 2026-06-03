```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_targeted_static_reextraction_v1",
  "round_id": "round_20260603_local_reverse_targeted_static_reextraction_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_targeted_static_reextraction_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "ACCEPT",
  "files_changed": [
    "reverse_agent/local_reverse_targeted_static_reextract.py",
    "tests/test_local_reverse_targeted_static_reextract.py",
    "project_state/local_reverse_targeted_static_reextraction_result.json",
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "tests/test_local_reverse_targeted_static_reextract.py",
    "tests/test_local_reverse_constraint_recovery.py",
    "tests/test_local_reverse_ida_guided_solver.py",
    "tests/test_local_reverse_ida_summary.py",
    "tests/test_project_state.py"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_targeted_static_reextraction_result.json"
  ]
}
```

# Codex Execution Report

## 1. 执行权威与轮次说明

- **当前 decision_packet**：`project_state/decision_packet.md` 是本轮唯一执行权威。
- **本轮性质**：targeted static re-extraction for two unresolved samples。
- **主线**：`reverse_solving`。
- **Cpp1 hookapi**：已作为 accepted handoff 保留，本轮不处理。

## 2. 执行摘要

| 项目 | 值 |
|------|-----|
| 目标样本数 | 2（sha_256.exe, CPP2.exe） |
| extraction_status | 两个均为 `partial` |
| blocker_resolved | 两个均为 `false` |
| 新增代码 | `reverse_agent/local_reverse_targeted_static_reextract.py` |
| 新增测试 | `tests/test_local_reverse_targeted_static_reextract.py`（14 个测试） |

## 3. 是否复用现有 IDA runner / IDAPython

**否**。检查了 `tool_runners.py`、`local_reverse_ida_summary.py` 和 `collect_evidence.py` 后发现：
- 现有 `collect_evidence.py` 的评分机制不追踪从 `_main_0` 到 `sub_401005` 的调用图
- `sub_401005` 在两个二进制中均未被反编译（scored 0）
- raw IDA JSON 中已有 `_main_0` 完整伪代码，但缺少 `sub_401005` 伪代码

因此新增了 `local_reverse_targeted_static_reextract.py`，从现有 raw IDA JSON 中提取已有证据，并明确指出 `sub_401005` 伪代码缺失的精确缺口。**未运行 IDA**。

## 4. sha_256.exe 证据发现

### 4.1 已恢复证据

- **input_api**：`scanf("%s", Source)`，Source 为 1021 字节 buffer
- **min_length**：5（`strlen(Source) >= 5`）
- **prefix_copy_length**：4（`strncpy(&Destination, Source, 4u)`）
- **post_increment**：dual wrap 规则：
  - `if (++Str1[i] == 103) Str1[i] = 97` — 'g'→'a'
  - `if (Str1[i] == 58) Str1[i] = 48` — ':'→'0'
- **compare_target**：`493f877692ea8d507fa98355a054efede85e7c7bbc9ba9890ea99b7b33e281fc`（64 hex chars）
- **sub_401005 调用**：`sub_401005(Str1, &Destination, v4)` — 4 字符输入 → 64 字节 hex 输出

### 4.2 bounded_input_domain 状态

**`not_found`**。sha_256.exe 没有输入范围检查、没有内置字典、没有固定 prefix、没有长度上界。只有 4 个任意字符传入 SHA-256-like hash，**NO_BOUNDED_HASH_PREIMAGE_DOMAIN 保持有效**。

### 4.3 sub_401005 证据

- **pseudocode_available**：`false`
- **精确缺口**：`collect_evidence.py` 评分不追踪调用图，`sub_401005` scored 0，未被反编译
- **transform_hypothesis**：SHA-256 hash + hex encoding（基于 32 字节输出和地址 0x401005），但无伪代码确认

## 5. CPP2.exe 证据发现

### 5.1 已恢复证据

- **input_api**：`scanf("%s", Source)`，Source 为 1021 字节 buffer
- **min_length**：5（`v5 >= 5`）
- **input_range**：65('A')..122('z')，但 **enforcement=warning_only**（不退出，继续执行）
- **prefix_copy_length**：4（`strncpy(&Destination, Source, 4u)`）
- **post_increment**：simple `++Str1[j]`，64 次迭代，无 wrap
- **compare_target**：`1f2e28649c4g:25:8bb:24c3D3EGF6GFg22dff:1dbd916df13239513g21e4663`（含大写、小写、数字、冒号、'g'）

### 5.2 bounded_input_domain 状态

**`partial`**。有范围检查 65..122 但仅打印警告不退出，4 字符前缀给出 58^4 = 11,316,496 可能输入（若严格执行），但 enforcement 是 warning_only。

### 5.3 sub_401005 证据

- **pseudocode_available**：`false`
- **精确缺口**：同 sha_256，`collect_evidence.py` 评分不追踪调用图
- **transform_hypothesis**：同 sha_256，SHA-256 hash + hex encoding

## 6. Blocker 是否解除

| 样本 | blocker | 是否解除 | 原因 |
|------|--------|----------|------|
| sha_256.exe | NO_BOUNDED_HASH_PREIMAGE_DOMAIN | **否** | 4 个任意字符，无 bounded domain |
| CPP2.exe | MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005 | **否** | sub_401005 伪代码缺失 |

## 7. 状态更新

- **artifact_index.json**：新增 `local_reverse_targeted_static_reextraction_result` 条目
- **current_state.json**：新增 `latest_targeted_static_reextraction` / `latest_targeted_static_reextraction_status` / `latest_targeted_static_reextraction_round`
- **task_packet.json**：更新 `local_reverse_current_artifact` / `local_reverse_next_suggested_task` / `local_reverse_current_artifact_keys`

## 8. 审计合规声明

| # | 审计项 | 状态 |
|---|--------|------|
| 1 | 当前 decision_packet 是执行权威 | ✅ |
| 2 | mainline=reverse_solving | ✅ |
| 3 | 只处理 sha_256.exe 和 CPP2.exe | ✅ |
| 4 | Cpp1 hookapi 只作为已解决 handoff 保留 | ✅ |
| 5 | 未复用 IDA runner（不需要，raw JSON 已有足够证据） | ✅ |
| 6 | 未运行 targeted IDA re-extraction | ✅（从 raw JSON 提取） |
| 7 | 只读取两个 unresolved 样本的 raw IDA JSON | ✅ |
| 8 | sha_256 输入域证据已记录 | ✅ |
| 9 | CPP2 sub_401005 证据和精确缺口已记录 | ✅ |
| 10 | 两个 blocker 均未解除，已说明原因 | ✅ |
| 11 | 新 artifact path、status、target_count 已记录 | ✅ |
| 12 | artifact_index/current_state/task_packet 已更新 | ✅ |
| 13 | 未扩大样本 | ✅ |
| 14 | 未复制、提交、上传或编码样本二进制 | ✅ |
| 15 | 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt | ✅ |
| 16 | 未修改 .codex-skills/ | ✅ |
| 17 | 未运行 debugger/dynamic probe/Ghidra | ✅ |
| 18 | 测试真实运行并写入 pytest_result.txt | ✅ |

## 9. 停止条件检查

本轮未触发任何停止条件：
- handoff artifact 存在且 hookapi 仍为 validated ✅
- raw IDA evidence freshness=current ✅
- 未需要读取完整 solve_reports/ ✅
- 未需要读取完整 PROJECT_PROGRESS_LOG.txt ✅
- 未扩大到两个 unresolved 样本之外 ✅
- 未使用无界 brute force ✅
- 未运行 debugger/dynamic probe/Ghidra ✅
- 未复制、提交、上传或编码样本二进制 ✅
