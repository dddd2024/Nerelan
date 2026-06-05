```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_target_bytes_length_rework_v1",
  "round_id": "round_20260605_cpp1_target_bytes_length_rework_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **tool_integration**。

上一轮 `decision_20260605_cpp1_target_byte_extraction_v1` 审计结论为 `REWORK_REQUIRED`。方向正确，但存在两个阻断问题：

```text
1. required command 缺失：python -m py_compile reverse_agent/tool_runners.py。
2. project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json 只提取了 1 字节：target_length=1, target_bytes_hex=d5；但 _main_0 静态证据显示 compare 成功条件为 i == 16，后续 inverse handoff 至少需要 16 字节 target bytes。
```

本轮目标：**只修复 cpp1_2f6fcb63 target-byte extraction 的长度与 required test 记录缺口**。

必须完成：

```text
1. 补跑并记录 python -m py_compile reverse_agent/tool_runners.py。
2. 修正 byte_429A30 的读取长度：应按 expected_target_length=16 提取连续 16 字节，不能只依赖 IDA 当前 item_size=1。
3. 如果无法可靠提取 16 字节，则 artifact 必须为 BLOCKED / INCOMPLETE_TARGET_BYTES，而不是 success。
4. 不生成 candidate / flag / known_candidate。
5. 不动态执行样本，不运行 solver。
```

本轮仍只补齐静态证据，不进入逆变换求解。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮有效事实：

```text
reverse_agent/local_reverse_cpp1_target_byte_extract.py exists.
reverse_agent/ida_scripts/extract_named_data.py exists.
tests/test_local_reverse_cpp1_target_byte_extract.py exists.
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json exists.
artifact_index.latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_target_bytes exists.
```

上一轮 target byte artifact 当前内容：

```text
sample_id=cpp1_2f6fcb63
analysis_mode=target_compare_byte_extraction
executed_sample=false
static_only=true
runtime_validated=false
tool_status=success
source_tool=IDA
target_symbol=byte_429A30
target_address=0x00429A30
target_length=1
target_bytes_hex=d5
target_bytes=[213]
candidate=null
known_candidate=""
```

关键静态证据仍然是：

```text
strncpy(Destination, Str, 0x10u)
Destination[i] = Destination[i] & 3 | (16 * (Destination[i] & 0xC)) | ((Destination[i] & 0xF0) >> 2)
for ( i = 0; i < v4 && Destination[i] == byte_429A30[i]; ++i )
if ( i == 16 ) success string is printed
```

因此本轮必须把 expected_target_length 明确为 16。若实际连续字节无法提取 16 字节，应将 artifact 标记 blocked，而不是继续 success。

已知技术原因：`extract_named_data.py` 当前通过 `ida_bytes.get_item_size(ea)` 决定读取长度。如果 IDA 将 `byte_429A30` 识别为单个 byte item，就只会读 1 字节。当前代码只有在 `item_size <= 0` 时默认 16，这不满足本样本的 compare evidence。

`negative_results.json` 仍禁止旧盲搜、单纯扩大搜索预算、提交 full solve_reports、重复旧动态探测方向。本轮不得进入这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行本地样本。
2. 不做动态探测或交互式调试。
3. 不运行旧盲搜 solver。
4. 不运行 brute force 或扩大搜索预算。
5. 不生成 candidate、flag、known_candidate。
6. 不把 cpp1_2f6fcb63 标记 solved。
7. 不提交原始样本文件。
8. 不提交 full solve_reports、IDA 数据库副产物或无必要日志。
9. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
10. 不修改 .codex-skills。
11. 不新建第二套 IDA runner。
12. 不把静态字节提取结果说成 runtime validation。
13. 不把 target_length=1 的结果标记为 success。
14. 不在本轮执行 inverse transform 或输出 password。
```

允许：

```text
1. 修改 reverse_agent/ida_scripts/extract_named_data.py，使目标读取长度可由环境变量或 adapter 参数控制。
2. 修改 reverse_agent/local_reverse_cpp1_target_byte_extract.py，传入 expected_target_length=16 并校验 len(target_bytes) == 16。
3. 若提取长度不足，输出 BLOCKED / INCOMPLETE_TARGET_BYTES。
4. 修改 tests/test_local_reverse_cpp1_target_byte_extract.py，覆盖不足 16 字节不能 success。
5. 更新 project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json。
6. 更新 artifact_index.json、codex_execution_report.md、pytest_result.txt。
```

---

## 4. Files To Inspect

默认必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
```

必须检查：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
reverse_agent/tool_runners.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/ida_scripts/extract_named_data.py
tests/test_local_reverse_cpp1_target_byte_extract.py
```

允许修改：

```text
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/ida_scripts/extract_named_data.py
tests/test_local_reverse_cpp1_target_byte_extract.py
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
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
2. 是否确认 task_packet.task 只是 advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认目标样本只限 cpp1_2f6fcb63。
5. 是否确认本轮只修复 target bytes length 和 required test 记录。
6. 是否补跑 python -m py_compile reverse_agent/tool_runners.py。
7. 是否补跑 python -m py_compile reverse_agent/local_reverse_cpp1_target_byte_extract.py。
8. 是否运行 tests/test_local_reverse_cpp1_target_byte_extract.py。
9. 是否运行 tests/test_project_state.py。
10. 是否运行 lint-decision 与 lint-report。
11. 是否重新运行 target byte extraction CLI。
12. 是否明确 expected_target_length=16。
13. 如果 tool_status=success，是否确认 target_length=16 且 len(target_bytes)=16。
14. 如果无法提取 16 字节，是否输出 BLOCKED / INCOMPLETE_TARGET_BYTES。
15. 是否确认 artifact 仍为 executed_sample=false / static_only=true / runtime_validated=false。
16. 是否确认 artifact 仍为 candidate=null / known_candidate=""。
17. 是否没有动态执行样本。
18. 是否没有运行 solver / brute force。
19. 是否没有提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 修改。
20. 是否 artifact_index 登记 source_run=round_20260605_cpp1_target_bytes_length_rework_v1。
21. 是否 codex_execution_report.md 与 pytest_result.txt 对齐当前 decision_id/round_id。
22. tests_ran 是否完整列出 required commands，且无省略号。
23. pytest_result.txt 是否记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

首选修复：保留现有 adapter 与 IDAPython 脚本，但添加可控读取长度。

建议实现约束：

```text
1. 在 local_reverse_cpp1_target_byte_extract.py 中设置 expected_target_length=16。
2. 通过环境变量传给 IDAPython，例如 REVERSE_AGENT_TARGET_LENGTH=16。
3. 在 extract_named_data.py 中读取 REVERSE_AGENT_TARGET_LENGTH；若存在且为正数，则用该长度读取 named data bytes，而不是仅用 ida_bytes.get_item_size(ea)。
4. 在 adapter parse/build 阶段校验：len(target_bytes) == expected_target_length。
5. 若 target_length < expected_target_length 或 bytes_hex 长度不匹配，则 output blocked artifact：
   tool_status=blocked
   blocked_reason=INCOMPLETE_TARGET_BYTES
   target_length=<actual>
   expected_target_length=16
   target_bytes=<actual bytes if available>
6. success artifact 必须包含 expected_target_length=16。
```

不得在本轮进行 inverse transform。即使拿到 16 字节，也只推荐下一轮 inverse-transform handoff。

建议 success artifact 关键字段：

```json
{
  "tool_status": "success",
  "expected_target_length": 16,
  "target_length": 16,
  "target_bytes": [/* 16 ints */],
  "candidate": null,
  "known_candidate": ""
}
```

建议 blocked artifact 关键字段：

```json
{
  "tool_status": "blocked",
  "blocked_reason": "INCOMPLETE_TARGET_BYTES",
  "expected_target_length": 16,
  "target_length": 1,
  "target_bytes": [213],
  "candidate": null,
  "known_candidate": ""
}
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/tool_runners.py
python -m py_compile reverse_agent/local_reverse_cpp1_target_byte_extract.py
python -m pytest -q tests/test_local_reverse_cpp1_target_byte_extract.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.local_reverse_cpp1_target_byte_extract --sample-id cpp1_2f6fcb63 --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
git diff --check
git status --short
```

Tests must additionally cover：

```text
1. parse_extraction with 16 bytes -> success-capable.
2. parse_extraction with 1 byte but expected 16 -> incomplete.
3. run_target_byte_extraction returns BLOCKED / INCOMPLETE_TARGET_BYTES when actual length < expected length.
4. blocked artifact preserves candidate=null and known_candidate="".
5. success artifact preserves candidate=null and known_candidate="".
6. IDAPython env length parsing can use REVERSE_AGENT_TARGET_LENGTH=16.
```

Expected results：

```text
1. All required commands Exit Code 0.
2. Artifact either success with 16 bytes or blocked with INCOMPLETE_TARGET_BYTES.
3. Artifact includes expected_target_length=16.
4. Artifact includes executed_sample=false, static_only=true, runtime_validated=false.
5. Artifact does not contain candidate/flag/known_candidate.
6. artifact_index registers local_reverse_cpp1_2f6fcb63_target_bytes with freshness=current and source_run=round_20260605_cpp1_target_bytes_length_rework_v1.
7. git status --short does not include original samples, full solve_reports, IDA database side products, or .codex-skills.
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 无法补跑 py_compile reverse_agent/tool_runners.py。
2. 无法让 extraction 区分 expected_target_length=16 与 actual target_length=1。
3. 需要动态执行样本才能完成。
4. 需要运行 solver / brute force 才能完成。
5. 需要提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 才能完成。
6. 修复过程中出现 candidate/known_candidate/flag 生成倾向。
```

完成条件：

```text
1. project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json 存在。
2. Artifact 是 success with 16 bytes，或 BLOCKED / INCOMPLETE_TARGET_BYTES。
3. Artifact includes expected_target_length=16。
4. Artifact includes executed_sample=false, static_only=true, runtime_validated=false。
5. Artifact 不含 candidate/flag/known_candidate。
6. artifact_index source_run=round_20260605_cpp1_target_bytes_length_rework_v1。
7. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision_id/round_id。
8. required tests 全部记录。
9. 未动态执行样本，未运行 solver，未修改 .codex-skills，未提交大型副产物或原始样本。
```
