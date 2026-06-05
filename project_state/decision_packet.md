```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_2f6fcb63_static_triage_v1",
  "round_id": "round_20260605_cpp1_2f6fcb63_static_triage_v1",
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

上一轮 `decision_20260605_affine_training_status_lint_report_rework_v1` 已审计通过。训练队列中下一项是 `cpp1_2f6fcb63`，当前状态为 `inventory_only`，队列建议为静态 triage。

本轮目标：**只对 `cpp1_2f6fcb63` 生成有界静态 triage artifact**，用于判断后续是否需要 solver、IDA targeted extraction 或其他静态证据补充。

本轮不求解、不生成 candidate、不更新 known_candidate、不改变训练状态为 solved。

目标输出：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
```

该 artifact 应说明：

```text
1. 样本 metadata 与队列 provenance。
2. 是否能使用现有静态工具接口收集证据。
3. 静态证据摘要：字符串、函数、比较点、局部校验上下文、候选校验函数、solver profile hypothesis。
4. 如果无法访问样本或工具不可用，应输出 BLOCKED artifact，并写明 blocker。
5. 推荐下一步，但不得执行下一步求解。
```

---

## 2. Current Evidence

`task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `decision_packet.md` 为唯一执行权威。

当前训练状态摘要：

```text
sample_count=29
solved=1
blocked=3
inventory_only=25
cpp1_bcbd9979: solved, known_candidate=hookapi
cpp2_4c69f173: blocked
sha_256_18019fca: blocked
affine_8cfebe03: blocked / MISSING_EXPECTED_CIPHERTEXT / known_candidate=""
```

当前队列目标：

```text
sample_id: cpp1_2f6fcb63
relative_path: 逆向课程2023春01/CPP1.exe
sha256: 2f6fcb637151a413dae11ab981706ff1f46d2202abc1d60de8a3b534448baede
size_bytes: 196700
file_type: PE
category: cpp
queue_rank: 1
allowed_action: static_triage
```

训练材料 case metadata：

```text
training_materials/local_reverse/cases/cpp1_2f6fcb63.json
expected_flag=""
notes=Auto-generated from local reverse inventory.
```

已存在的工具能力，必须优先复用：

```text
reverse_agent/tool_runners.py
  run_ida_evidence()
  run_tool_automation()
  _run_ida()
  _resolve_ida_executable()
  _resolve_ida_script()

reverse_agent/ida_scripts/collect_evidence.py
  已能收集 strings、functions、compare contexts、local check contexts、string xrefs、validation function candidates、decompiler snippets、solver hints。

reverse_agent/local_reverse_forced_ida_extract.py
  已有 targeted IDA extraction wrapper。

reverse_agent/local_reverse_targeted_static_reextract.py
  已有针对前序样本的静态 JSON 解析器，但不是通用 CPP1 solver。
```

未发现可直接复用的 Ghidra runner。动态调试类路径不是本轮范围。

`negative_results.json` 仍禁止旧盲搜、单纯扩大搜索预算、提交 full solve_reports、重复旧动态探测方向。

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行本地样本。
2. 不做动态探测或交互式调试。
3. 不运行旧盲搜 solver。
4. 不生成 candidate、flag、known_candidate。
5. 不把 cpp1_2f6fcb63 标记 solved。
6. 不提交原始样本文件。
7. 不提交 full solve_reports、IDA 数据库副产物或无必要日志。
8. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
9. 不修改 .codex-skills。
10. 不新建第二套静态分析工具接口。
11. 不重复实现 IDA 已提供的反汇编、反编译、XREF、字符串提取能力。
12. 不同时推进训练状态重构和样本求解。
```

允许：

```text
1. 读取默认 project_state 事实源。
2. 读取 inventory、training status、evaluation queue 与目标 case metadata。
3. 检查并复用现有 IDA/tool_runners 接口。
4. 新增一个小型 single-sample static triage adapter，前提是它复用现有静态工具接口。
5. 如果工具或样本路径不可用，输出 BLOCKED artifact。
6. 更新 artifact_index、codex_execution_report、pytest_result。
7. 添加轻量单元测试，覆盖 queue selection、metadata extraction、blocked artifact、triage schema。
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
training_materials/local_reverse/cases/cpp1_2f6fcb63.json
training_materials/local_reverse/inventory.json
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/local_reverse_targeted_static_reextract.py
```

必要时检查：

```text
tests/test_project_state.py
tests/test_local_reverse_training_status.py
tests/test_local_reverse_targeted_static_reextract.py
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
5. 是否确认 cpp1_2f6fcb63 当前为 queue rank 1 与 inventory_only。
6. 是否确认本轮只做 static triage。
7. 是否复用现有 tool_runners / IDA collect_evidence 能力。
8. 是否没有新建重复静态工具接口。
9. 是否没有动态执行本地样本。
10. 是否没有生成 candidate / flag / known_candidate。
11. 是否没有把目标样本标记 solved。
12. 是否生成 project_state/local_reverse_cpp1_2f6fcb63_static_triage.json。
13. 如果工具或样本不可用，是否输出明确 BLOCKED artifact。
14. 是否更新 artifact_index.latest_artifacts 与 latest_artifacts_v2，freshness=current，source_run=round_20260605_cpp1_2f6fcb63_static_triage_v1。
15. 是否没有提交 full solve_reports、IDA 数据库副产物、原始样本或 .codex-skills 修改。
16. 是否更新 codex_execution_report.md 与 pytest_result.txt。
17. based_on_decision_id 是否匹配当前 decision_id。
18. tests_ran 是否完整列出 required commands。
19. pytest_result.txt 是否记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

首选实现：新增一个薄封装 CLI：

```text
reverse_agent/local_reverse_single_sample_static_triage.py
```

它的职责只包括：

```text
1. 从 queue / inventory 中定位指定 sample_id。
2. 解析 metadata 与本地路径。
3. 调用现有静态工具接口；不可用时生成 BLOCKED artifact。
4. 将 raw 静态输出压缩成 compact triage summary。
5. 写入 project_state/local_reverse_cpp1_2f6fcb63_static_triage.json。
```

允许新增：

```text
reverse_agent/local_reverse_single_sample_static_triage.py
tests/test_local_reverse_single_sample_static_triage.py
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
```

允许修改：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

建议 artifact schema：

```json
{
  "schema_version": 1,
  "sample_id": "cpp1_2f6fcb63",
  "relative_path": "逆向课程2023春01/CPP1.exe",
  "analysis_mode": "single_sample_static_triage",
  "mainline": "tool_integration",
  "executed_sample": false,
  "static_only": true,
  "runtime_validated": false,
  "tool_status": "success_or_blocked",
  "blocked_reason": "",
  "source_tool": "IDA_or_none",
  "triage": {
    "file_type": "pe",
    "input_apis": [],
    "interesting_strings": [],
    "compare_contexts": [],
    "local_check_contexts": [],
    "validation_function_candidates": [],
    "solver_profile_hypotheses": []
  },
  "candidate": null,
  "known_candidate": "",
  "recommended_next_action": ""
}
```

实现约束：

```text
1. 样本路径缺失时：输出 BLOCKED / BINARY_NOT_FOUND。
2. 静态工具不可用时：输出 BLOCKED / STATIC_TOOL_UNAVAILABLE。
3. 静态工具成功时：输出 success static triage summary。
4. 不提交大型副产物。
5. 不更新 training_status 为 solved/blocked；本轮只产出 triage evidence。
6. 如果发现明显 solver profile，只写 recommended_next_action，不执行 solver。
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/tool_runners.py
python -m py_compile reverse_agent/local_reverse_single_sample_static_triage.py
python -m pytest -q tests/test_local_reverse_single_sample_static_triage.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp1_2f6fcb63 --queue project_state/local_reverse_evaluation_queue.json --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
git diff --check
git status --short
```

如果没有新增 CLI，必须用等价的可复现命令替换上述 CLI/测试命令，并在报告中说明原因；但仍必须生成 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`。

测试期望：

```text
1. CLI 生成 success 或 BLOCKED artifact，且 Exit Code 0。
2. artifact 包含 executed_sample=false、static_only=true、runtime_validated=false。
3. artifact 不包含 candidate/flag/known_candidate。
4. artifact_index 登记 local_reverse_cpp1_2f6fcb63_static_triage 为 freshness=current。
5. git status --short 不出现 solve_reports bulk files、静态工具数据库副产物、原始样本或 .codex-skills。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. cpp1_2f6fcb63 不再是 queue rank 1，且未说明 override。
2. 样本路径不可用，且无法生成 metadata-only BLOCKED artifact。
3. 静态工具接口不可用，且无法生成 BLOCKED artifact。
4. 需要动态执行样本才能完成。
5. 需要提交原始样本或大型工具副产物才能完成。
6. 需要修改 .codex-skills 才能完成。
7. 需要生成 candidate/flag/known_candidate 才能完成。
```

完成条件：

```text
1. project_state/local_reverse_cpp1_2f6fcb63_static_triage.json 存在。
2. artifact 为 success static triage 或明确 BLOCKED。
3. artifact includes executed_sample=false, static_only=true, runtime_validated=false。
4. artifact_index 登记新 artifact，freshness=current，source_run=round_20260605_cpp1_2f6fcb63_static_triage_v1。
5. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision。
6. required tests 已记录。
7. 未动态执行样本，未生成 candidate/flag，未修改 .codex-skills，未提交大型副产物或原始样本。
```
