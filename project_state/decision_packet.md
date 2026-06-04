```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_affine_queue_static_evidence_plan_v1",
  "round_id": "round_20260604_affine_queue_static_evidence_plan_v1",
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

上一轮 `training_dataset` 已经建立了本地样本 inventory、status overlay 和 evaluation queue。审计结论为 `ACCEPTED_WITH_LIMITATIONS`：核心产物可用，但报告文本里仍有少量残留。现在可以进入第一批样本的静态证据提取准备阶段。

本轮目标：从 `project_state/local_reverse_evaluation_queue.json` 中选择 rank 1 样本：

```text
sample_id: affine_8cfebe03
relative_path: 逆向课程2024春补考03/affine.exe
status: inventory_only
proposed_next_mainline: tool_integration
allowed_actions: static_triage
```

本轮只做**有界静态证据提取计划与工具接口复用检查**，不求解 candidate，不运行程序，不做动态调试。

必须完成：

```text
1. 读取 evaluation queue，确认 affine_8cfebe03 是当前 rank 1 且仍为 inventory_only。
2. 读取 inventory/status_overlay，确认该样本的 sha256、size_bytes、relative_path、category、tags。
3. 检查已有静态工具接口和能力，不重复造轮子：
   - reverse_agent/local_reverse_inventory.py
   - reverse_agent/local_reverse_corpus.py
   - reverse_agent/static_feature_extractor.py
   - reverse_agent/tool_runners.py
   - 现有 local_reverse_ida_* 脚本
   - 已有 IDA/Ghidra 相关 runner 或导出器
4. 生成 affine 样本的 static evidence request/package。
5. 若已有安全静态提取入口可复用，允许只对 affine.exe 做有界静态提取，不运行样本。
6. 生成 project_state/local_reverse_affine_static_evidence_plan.json。
7. 生成 project_state/local_reverse_affine_tool_capability_audit.json。
8. 更新 codex_execution_report.md 和 pytest_result.txt。
9. 顺手清理上一轮报告/pytest 文本残留，但不得扩大 scope。
```

本轮不要求解出 `affine.exe`，不要求生成 solver，不要求验证 flag。

---

## 2. Current Evidence

当前 `project_state/local_reverse_training_status.json` 已有训练状态层：

```text
sample_count = 29
solved = 1
blocked = 2
inventory_only = 26
```

关键已知样本状态：

```text
Cpp1.exe：solved / validated，candidate = hookapi
sha_256.exe：blocked，NO_BOUNDED_HASH_PREIMAGE_DOMAIN
CPP2.exe：blocked，不能声称 solved
```

当前 `training_materials/local_reverse/status_overlay.json` 已恢复为真实 29 个样本，不再是 todo1/todo.exe fixture。

当前 `project_state/local_reverse_evaluation_queue.json` 的 rank 1 是：

```text
affine_8cfebe03
逆向课程2024春补考03/affine.exe
reason: PE sample (196688 bytes), static triage tags: reverse, local, pe
```

当前 `task_packet.json` 仍保留旧 samplereverse 派生任务，但其中已声明 `project_state/decision_packet.md` 是执行权威。本轮以本 decision 为准，不以旧 task_packet.task 为准。

上一轮审计限制仍需顺手清理：

```text
1. codex_execution_report.md 中不要再出现旧 decision id 字符串。
2. pytest_result_summary.tests_ran 不要列未在 command-level record 中真实运行的测试。
3. pytest detail 不要保留不一致统计。
```

这些只作为 preflight hygiene，不是本轮主目标。

---

## 3. Do Not Do

严禁：

```text
1. 不上传 E:\reverse 原始样本。
2. 不复制 affine.exe 或任何样本到仓库。
3. 不运行 affine.exe。
4. 不运行动态调试、runtime probe、Frida、OllyDbg、x64dbg、emulator。
5. 不生成 candidate、flag 或最终 solver。
6. 不回到 old sample_solver blind search。
7. 不扩大 beam/budget/bruteforce。
8. 不提交 solve_reports 全量目录。
9. 不修改 .codex-skills。
10. 不新建重复 IDA/Ghidra/debugger 接口。
11. 不把 affine 的单题结论写入长期 skill。
12. 不把 inventory_only 误标为 solved。
```

允许：

```text
1. 检查已有静态工具接口和 local_reverse_* 能力。
2. 对 affine.exe 生成 metadata-only 静态证据请求。
3. 如果现有工具接口已经支持安全静态提取，允许对 affine.exe 做有界静态提取，前提是不执行样本。
4. 生成 project_state 下的小型 JSON 计划/审计产物。
5. 更新 report 和 pytest_result。
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
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
training_materials/local_reverse/status_overlay.json
training_materials/local_reverse/inventory.json
reverse_agent/local_reverse_inventory.py
reverse_agent/local_reverse_corpus.py
reverse_agent/static_feature_extractor.py
reverse_agent/tool_runners.py
```

必须检查已有 tool integration，不得假设不存在：

```text
reverse_agent/local_reverse_ida_summary.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/local_reverse_targeted_static_reextract.py
reverse_agent/local_reverse_ida_guided_solver.py
任何现有 ida/ghidra/tool runner 相关文件
tests/test_local_reverse_inventory.py
tests/test_local_reverse_training_status.py
tests/test_project_state.py
```

必要时检查：

```text
project_state/local_reverse_ida_summary.json
project_state/local_reverse_forced_ida_extraction_result.json
project_state/local_reverse_constraint_recovery_result.json
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
1. 是否确认 affine_8cfebe03 仍是 evaluation queue rank 1。
2. 是否确认 affine_8cfebe03 仍为 inventory_only，未误标 solved。
3. 是否读取了 inventory/status_overlay 中 affine.exe 的 sha256、size_bytes、relative_path、tags。
4. 是否检查了已有 local_reverse_inventory/local_reverse_corpus/static_feature_extractor/tool_runners 能力。
5. 是否检查了已有 IDA/Ghidra/local_reverse_ida_* 接口，避免重复造轮子。
6. 是否生成 local_reverse_affine_static_evidence_plan.json。
7. 是否生成 local_reverse_affine_tool_capability_audit.json。
8. 如果运行了静态提取，是否明确说明只做静态读取，不执行样本。
9. 是否没有运行 solver、IDA/Ghidra 动态调试、runtime probe 或样本程序。
10. 是否没有上传原始样本。
11. 是否没有提交 solve_reports 全量目录。
12. 是否清理上一轮 report/pytest 文本残留。
13. pytest_result.txt 是否记录真实测试命令且全部 Exit code 0。
14. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_affine_queue_static_evidence_plan_v1。
```

---

## 6. Implementation Scope

允许新增：

```text
project_state/local_reverse_affine_static_evidence_plan.json
project_state/local_reverse_affine_tool_capability_audit.json
```

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必要时允许新增 focused test：

```text
tests/test_local_reverse_affine_static_evidence_plan.py
```

如果已有 CLI 或 helper 可复用，可新增一个很薄的 plan builder，例如：

```text
reverse_agent/local_reverse_static_evidence_plan.py
```

但只有在不复制现有 inventory/corpus/tool runner 逻辑的前提下才允许。优先写小型 JSON 产物，不要引入框架。

`local_reverse_affine_static_evidence_plan.json` 建议结构：

```json
{
  "schema_version": 1,
  "sample_id": "affine_8cfebe03",
  "relative_path": "逆向课程2024春补考03/affine.exe",
  "sha256": "...",
  "size_bytes": 196688,
  "training_status": "inventory_only",
  "mainline": "tool_integration",
  "allowed_actions": ["static_triage", "static_strings", "static_file_type", "static_tool_export_if_available"],
  "forbidden_actions": ["runtime_probe", "debugger", "execute_sample", "bruteforce", "upload_binary"],
  "evidence_to_collect": [
    "file kind / architecture if already available",
    "bounded strings",
    "import names if existing static extractor supports it",
    "candidate compare API names if statically visible",
    "constants and small byte arrays if existing extractor supports it",
    "whether IDA/Ghidra static export interface already exists"
  ],
  "next_decision_needed": "after evidence exists, choose whether to run IDA/Ghidra static extraction or a solver-specific static triage"
}
```

`local_reverse_affine_tool_capability_audit.json` 建议结构：

```json
{
  "schema_version": 1,
  "checked_capabilities": {
    "local_reverse_inventory": "present|missing",
    "local_reverse_corpus": "present|missing",
    "static_feature_extractor": "present|missing",
    "tool_runners": "present|missing",
    "ida_runner_or_script": "present|missing",
    "ghidra_runner_or_script": "present|missing"
  },
  "reuse_decision": "reuse existing interfaces; do not create duplicate runners",
  "static_only_policy": true
}
```

---

## 7. Tests

必须运行并记录：

```text
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

如果新增 Python helper/test，则还必须运行：

```text
python -m py_compile reverse_agent/local_reverse_static_evidence_plan.py
python -m pytest -q tests/test_local_reverse_affine_static_evidence_plan.py
```

如果只生成 JSON 计划，不新增代码，则无需新增 py_compile。

所有 required commands 必须记录真实 Exit code 0。若任何命令失败，codex_execution_report.md 不得写 SUCCESS/ACCEPT。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. affine_8cfebe03 不再是 rank 1，或已经不是 inventory_only。
2. 无法从 inventory/status_overlay 可靠定位 affine.exe。
3. 需要读取完整 solve_reports 才能完成本轮。
4. 需要运行 affine.exe 或动态调试才能完成本轮。
5. 需要上传原始样本才能完成本轮。
6. 发现已有 IDA/Ghidra/tool runner 接口但无法判断如何复用，且新建接口会重复造轮子。
7. 输出会泄露 E:\reverse 或其他真实本地绝对路径。
```

完成条件：

```text
1. affine rank/status 已确认。
2. tool capability audit 已生成。
3. static evidence plan 已生成。
4. 没有运行样本或动态分析。
5. 没有上传原始样本。
6. report/pytest 记录对齐本 decision_id。
7. lint-decision、lint-report、git diff --check 通过。
```
