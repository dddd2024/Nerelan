```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1",
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

目标：修复 `project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json` 的 JSON 语法错误，并补充最小校验，确保该 artifact 可被解析后再继续登记为 current。

本轮不是 reverse_solving。不要生成 candidate，不要验证 candidate，不运行样本，不调用 IDA/Ghidra/debugger/hook/probe/winpty/emulator，不重新读取样本二进制，不扩张静态窗口。

必须完成：

```text
1. 读取并确认当前失败点：
   - project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
   - project_state/artifact_index.json
   - project_state/codex_execution_report.md
   - project_state/pytest_result.txt
   - project_state/decision_packet.md

2. 修复 compare_constants_mapping artifact 中 0x62cb record 的 JSON 语法错误：
   当前错误："confirmed_formula_constant", false
   正确字段："confirmed_formula_constant": false

3. 用显式 JSON parse 命令验证该 artifact 可解析。

4. 重新计算 compare_constants_mapping artifact 的真实 sha256 与 size_bytes。

5. 更新 project_state/artifact_index.json 中 local_reverse_cpp2_883e67b9_compare_constants_mapping 的 sha256/size_bytes，并保持 freshness=current、source_run 为本轮 round。

6. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 decision/report/round，并记录 JSON parse 校验。
```

本轮不要求修改 solver 逻辑；除非现有 project_state lint 无法覆盖 artifact JSON parse，否则不要改 production code。若必须补测试，只允许小范围补充 project_state/artifact JSON parse 校验。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 compare constants mapping 已提交，但审计发现新 artifact 自身不是合法 JSON。

失败点：

```text
file: project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
record: constant_semantic_mapping entry for rva=0x62cb
bad field: "confirmed_formula_constant", false
expected:  "confirmed_formula_constant": false
```

影响：

```text
1. artifact 不能被 json.load/json.loads 解析。
2. artifact_index 已登记该 artifact 为 current，但对应文件不可解析。
3. codex_execution_report.md 与 pytest_result.txt 声称 PASS，但未捕获该 artifact parse failure。
4. 因此上一轮结论为 REWORK_REQUIRED，不能 ACCEPTED。
```

需要保持的事实：

```text
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
mainline=tool_integration
known_compare_constant_count=0
constants_mapping_status=MAPPED_WITH_LIMITATIONS
formula_recovered=false
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
recommended_next_mainline=tool_integration
```

`negative_results.json` 仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要运行 E:\reverse 样本。
2. 不要执行 candidate generation、candidate validation、negative control、runtime validation。
3. 不要 attach debugger / hook / emulator / probe / winpty。
4. 不要调用 IDA/Ghidra。
5. 不要重新读取样本二进制或扩张静态窗口。
6. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
7. 不要把 cpp2_883e67b9 推进到 candidate 层。
8. 不要把任何 compare constant 标成 confirmed formula 或 candidate source。
9. 不要修改 local_reverse_training_status.json。
10. 不要修改 training_materials/local_reverse/status_overlay.json。
11. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
12. 不要新建重复 IDA/Ghidra/debugger/runtime interface。
13. 不要重写成熟工具已有的反汇编/反编译能力。
14. 不要读取完整 solve_reports。
15. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
16. 不要提交 full solve_reports。
17. 不要把 task_packet.task 当执行权威。
18. 不要把 stale/missing/unknown artifact 当 current。
19. 不要把本轮变成 reverse_solving、训练状态同步或 runtime validation 轮。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取并修复 project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json。
3. 更新 project_state/artifact_index.json 中该 artifact 的 sha256/size_bytes 与本轮 provenance。
4. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
5. 执行显式 JSON parse 校验。
6. 如确有必要，补充小范围测试以防 artifact JSON parse regression。
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
project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
```

必要时检查：

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
2. mainline 是否为 tool_integration？
3. task_packet 是否仅为 advisory？
4. 是否确认本轮不是 reverse_solving，不生成/验证 candidate？
5. 是否修复 compare_constants_mapping.json 的 JSON 语法错误？
6. 是否用 python json.load/json.loads 成功解析该 artifact？
7. artifact_index 中登记的 sha256 与 size_bytes 是否按修复后的文件重新计算？
8. 是否保持 known_compare_constant_count=0？
9. 是否保持 constants_mapping_status=MAPPED_WITH_LIMITATIONS？
10. 是否保持 formula_recovered=false、candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false？
11. 是否没有修改 training_status/status_overlay？
12. 是否没有运行样本、runtime validation、debugger、hook、emulator、probe、winpty？
13. 是否没有调用 IDA/Ghidra 或重新读取样本二进制？
14. 是否没有修改 solver production code？如果修改了，为什么必须修改？
15. 是否运行 py_compile？
16. 是否运行相关 pytest？结果是多少？
17. 是否运行 lint-decision、lint-report、project_state status？
18. 是否运行 git diff --check、git status --short、git diff --name-status？
19. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Repair artifact syntax only

修复：

```text
project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
```

将错误字段：

```text
"confirmed_formula_constant", false
```

改为：

```text
"confirmed_formula_constant": false
```

不要改变语义分类，不要新增 candidate，不要把任何常量升级为 confirmed。

### Phase B — Validate artifact parse

必须运行：

```text
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json', encoding='utf-8'))"
```

如果失败，立即停止。

### Phase C — Update artifact_index provenance

修复 artifact 后，重新计算：

```text
sha256
size_bytes
```

更新：

```text
project_state/artifact_index.json
```

目标 entry：

```text
latest_artifacts_v2.local_reverse_cpp2_883e67b9_compare_constants_mapping
```

必须保持：

```text
kind=local_reverse_compare_constants_mapping
path=project_state\local_reverse_cpp2_883e67b9_compare_constants_mapping.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
constants_mapping_status=MAPPED_WITH_LIMITATIONS
known_compare_constant_count=0
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

### Phase D — Update report and pytest record

更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必须绑定：

```text
report_id=report_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1
round_id=round_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1
decision_id=decision_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json', encoding='utf-8'))"
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增 helper 或 schema test，必须补充对应 pytest 并记录完整命令。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. compare_constants_mapping.json 修复后仍不能被 json.load 解析。
3. artifact_index 无法登记修复后 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
4. 需要运行样本、runtime validation、debugger、hook、emulator、probe、winpty、IDA/Ghidra 才能完成本轮。
5. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
6. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
7. 需要生成或验证 candidate。
8. 需要扩大静态窗口、预算、枚举空间或重新做二进制分析。
9. 新 artifact 把任何 constant 标为 confirmed formula / candidate source，但没有 current source artifact 支持。
10. lint-report/status 无法通过。
11. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若 JSON 修复成功且 constants_mapping_status 仍为 MAPPED_WITH_LIMITATIONS，下一轮再考虑 input length evidence recovery。
