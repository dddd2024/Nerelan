```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_32f1713e_static_triage_v1",
  "round_id": "round_20260606_cpp2_32f1713e_static_triage_v1",
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

目标：按当前 `project_state/local_reverse_evaluation_queue.json` 的第 1 项，对 `cpp2_32f1713e` 执行一次 **有界单样本静态 triage**，只复用现有静态工具接口收集结构化证据，不运行目标样本、不做 runtime validation、不生成 candidate、不推进 solver。

目标样本：

```text
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
category=cpp
file_type=pe
queue_rank=1
allowed_actions=[static_triage]
forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

预期产物：

```text
project_state/local_reverse_cpp2_32f1713e_static_triage.json
artifact_index.latest_artifacts["local_reverse_cpp2_32f1713e_static_triage"]
artifact_index.latest_artifacts_v2["local_reverse_cpp2_32f1713e_static_triage"]
```

接受的结果状态：

```text
A. tool_status=success：IDA 静态证据提取成功，artifact 包含 strings/functions/compare_contexts/solver_profile_hypotheses/decompiler_snippets 等结构化摘要。
B. tool_status=blocked：本地样本根、IDA executable 或 IDA script 不可用，artifact 必须明确 blocked_reason，例如 BINARY_NOT_FOUND 或 STATIC_TOOL_UNAVAILABLE:*。
```

无论 A/B，都不得把样本标记为 solved，不得写入 known_candidate，不得生成 flag。

---

## 2. Current Evidence

当前 `project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
task=Review bounded window discovery diagnostics
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态：

```text
state_build_id=state_20260602_053948_4e3984041cd7
state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 closeout 已审计 ACCEPTED：

```text
report_id=report_20260606_cpp2_2f64e68d_training_status_legacy_index_closeout_v1
round_id=round_20260606_cpp2_2f64e68d_training_status_legacy_index_closeout_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_training_status_legacy_index_closeout_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
files_changed=[project_state/artifact_index.json, project_state/codex_execution_report.md, project_state/pytest_result.txt]
```

`project_state/pytest_result.txt` 已是命令级记录，且上一轮 tests/lint/status 均通过：

```text
python -m pytest -q tests/test_project_state.py -> 158 passed
lint-decision -> OK
lint-report -> OK
status -> OK
git diff --name-status -> only allowed project_state files
```

当前训练队列证据：

```text
project_state/local_reverse_evaluation_queue.json
rank=1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
reason=PE sample (196686 bytes), static triage tags: pe, reverse, cpp, local
proposed_next_mainline=tool_integration
allowed_actions=[static_triage]
forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

当前 case metadata 证据：

```text
training_materials/local_reverse/cases/cpp2_32f1713e.json
input_value=${LOCAL_REVERSE_ROOT}/逆向课程2023春补考02/Cpp2.exe
expected_flag=""
category=cpp
tags=[local, reverse, cpp, pe]
```

已有工具接口能力：

```text
reverse_agent/local_reverse_single_sample_static_triage.py
  - 已存在单样本静态 triage adapter。
  - 复用 tool_runners / collect_evidence.py / IDA 静态证据提取。
  - 文件头说明：Does NOT execute the target binary. Does NOT generate candidates.
  - run_static_triage() 能生成 success artifact 或 blocked artifact。
  - success artifact 中 executed_sample=false、static_only=true、runtime_validated=false、candidate=None、known_candidate=""。
  - blocked artifact 中同样 executed_sample=false、static_only=true、runtime_validated=false、candidate=None、known_candidate=""。

tests/test_local_reverse_single_sample_static_triage.py
  - 已覆盖 sample root、sample locate、path resolve、IDA evidence parse、blocked artifact、run_static_triage 等逻辑。
```

现有成熟工具优先原则：

```text
本轮只允许使用现有 IDA/IDAPython 静态导出接口。
不得为 strings/functions/compare_contexts/decompiler 重新造轮子。
不得新增重复 IDA runner。
不得新增自研反汇编器或二进制解析器。
```

`negative_results.json` 仍主要约束旧 samplereverse 失败方向。本轮不触碰这些方向，尤其不运行 old sample_solver blind search、guided_pool、Base64/RC4 breakpoint probe、CompareProbe、runtime hook 或 solve_reports 全量扫描。

artifact freshness 当前相关事实：

```text
cpp2_32f1713e 尚无 current static_triage artifact。
cpp2_2f64e68d 的 training_status_sync 已在 latest_artifacts 和 latest_artifacts_v2 双字段登记完成；本轮不得回改该 closeout。
```

是否允许运行工具：

```text
允许：
  - python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp2_32f1713e --out project_state/local_reverse_cpp2_32f1713e_static_triage.json
  - 该 CLI 内部仅允许解析 LOCAL_REVERSE_ROOT 下这一份样本路径，并调用现有 IDA 静态提取。
  - python 单元测试、project_state lint/status、git diff/status。

不允许：
  - 运行 Cpp2.exe / CPP2.exe 本体。
  - runtime_probe、pair validator、mature backend probe、debugger、hook、emulator、CompareProbe、solver、bruteforce。
```

是否允许读取本地样本：

```text
仅允许通过 LOCAL_REVERSE_ROOT + relative_path 解析 cpp2_32f1713e 这一份样本，并只作为 IDA 静态输入读取。
不允许上传、复制、提交样本 binary。
不允许批量扫描 E:\reverse 或其他训练目录。
```

是否允许读取重型 artifact：

```text
不允许默认读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
不允许读取 project_state/rounds 全量历史。
只允许读取本轮 target、queue、inventory、case、static_triage 源码/测试和 artifact_index 相关小文件。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行 Cpp2.exe / CPP2.exe 目标程序。
2. 不做 runtime_probe。
3. 不运行 console pair validator。
4. 不运行 mature backend probe。
5. 不运行 debugger、OllyDbg、x64dbg、Frida hook、emulator、CompareProbe。
6. 不运行 solver、bruteforce、guided pool、symbolic search、constraint recovery。
7. 不扫描完整 E:\reverse、D:\reverse、C:\reverse、F:\reverse 或 ~/reverse。
8. 不上传、复制、提交任何样本 binary。
9. 不新增 IDA runner、Ghidra runner、二进制解析器、反汇编器或反编译器。
10. 不修改 reverse_agent/local_reverse_single_sample_static_triage.py，除非测试暴露出阻塞 bug，且必须最小修复并说明。
11. 不修改 solver/validator/probe 代码。
12. 不修改 .codex-skills/*。
13. 不提交 solve_reports。
14. 不读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不把任何静态字符串、candidate-looking literal 或 compare operand 写成 known_candidate/solved/flag。
16. 不更新 local_reverse_training_status.json、local_reverse_evaluation_queue.json 或 status_overlay.json，除非后续单独 decision 明确要求训练状态同步。
```

允许：

```text
1. 读取 queue/inventory/case metadata。
2. 运行现有 single_sample_static_triage CLI，限定 sample_id=cpp2_32f1713e。
3. 如 LOCAL_REVERSE_ROOT/IDA/script 不可用，生成 blocked static triage artifact。
4. 新建 project_state/local_reverse_cpp2_32f1713e_static_triage.json。
5. 更新 project_state/artifact_index.json，登记 latest_artifacts 与 latest_artifacts_v2。
6. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
7. 可新建本轮 minimal round archive，只包含 decision/report/pytest/round_manifest；不要包含 sample binary 或完整 state snapshot。
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
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
training_materials/local_reverse/cases/cpp2_32f1713e.json
reverse_agent/local_reverse_single_sample_static_triage.py
tests/test_local_reverse_single_sample_static_triage.py
```

必要时读取：

```text
reverse_agent/tool_runners.py
reverse_agent/project_state.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
本地训练样本目录全量
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认目标样本来自 evaluation_queue rank=1: cpp2_32f1713e。
5. 是否确认 allowed_actions 只有 static_triage，forbidden_actions 包含 runtime_probe/bruteforce/upload_binary。
6. 是否确认使用了现有 reverse_agent.local_reverse_single_sample_static_triage 接口，没有新建重复 IDA/Ghidra/debugger 接口。
7. 是否确认没有运行目标程序本体。
8. 是否确认没有运行 runtime validator、mature backend probe、debugger、hook、emulator、CompareProbe、solver、bruteforce。
9. 是否确认没有上传/复制/提交 sample binary。
10. 是否确认若访问 LOCAL_REVERSE_ROOT，只访问 cpp2_32f1713e 的相对路径，且仅供 IDA 静态读取。
11. 是否确认 artifact 中 executed_sample=false、static_only=true、runtime_validated=false。
12. 是否确认 artifact 中 candidate is null、known_candidate=""、solved 不为 true。
13. 是否确认 artifact_index latest_artifacts/latest_artifacts_v2 已登记 local_reverse_cpp2_32f1713e_static_triage。
14. 是否确认未修改 local_reverse_training_status.json / local_reverse_evaluation_queue.json / status_overlay.json。
15. 是否确认未修改 .codex-skills 和 solve_reports。
16. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
17. 是否确认测试/lint/status 结果真实记录。
18. 是否确认 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

小步推进，不跨主线扩张。

具体执行：

```text
1. 确认 cpp2_32f1713e 在 project_state/local_reverse_evaluation_queue.json 中 rank=1，allowed_actions=[static_triage]。
2. 确认 project_state/local_reverse_inventory.json 或 training_materials/local_reverse/cases/cpp2_32f1713e.json 中 relative_path 与 sha/category/tags 一致。
3. 运行现有 CLI：
   python -m reverse_agent.local_reverse_single_sample_static_triage \
     --sample-id cpp2_32f1713e \
     --queue project_state/local_reverse_evaluation_queue.json \
     --inventory project_state/local_reverse_inventory.json \
     --artifact-index project_state/artifact_index.json \
     --out project_state/local_reverse_cpp2_32f1713e_static_triage.json
4. 如果 CLI 输出 success artifact：保留 strings/functions/compare_contexts/validation_function_candidates/solver_profile_hypotheses/decompiler_snippets 等摘要；不生成 candidate。
5. 如果 CLI 输出 blocked artifact：保留 blocked_reason；不要尝试绕过 LOCAL_REVERSE_ROOT/IDA/script 缺失；不要自行实现替代工具。
6. 更新 project_state/artifact_index.json：
   - latest_artifacts["local_reverse_cpp2_32f1713e_static_triage"] = "project_state\\local_reverse_cpp2_32f1713e_static_triage.json"
   - latest_artifacts_v2["local_reverse_cpp2_32f1713e_static_triage"] = {
       kind="local_reverse_single_sample_static_triage",
       path="project_state\\local_reverse_cpp2_32f1713e_static_triage.json",
       freshness="current",
       source_run="round_20260606_cpp2_32f1713e_static_triage_v1",
       sha256=<artifact file sha256>,
       size_bytes=<artifact file size>,
       modified_at=<artifact mtime iso>,
       sample_id="cpp2_32f1713e"
     }
7. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
```

不得做：

```text
- 不更新训练状态 overlay。
- 不从 static candidate 进入 runtime validation。
- 不从 compare_context 直接生成 known_candidate。
- 不写 solve report。
```

---

## 7. Tests

必须运行并记录：

```text
python -m py_compile reverse_agent/local_reverse_single_sample_static_triage.py
python -m pytest -q tests/test_local_reverse_single_sample_static_triage.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp2_32f1713e --queue project_state/local_reverse_evaluation_queue.json --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp2_32f1713e_static_triage.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. project_state/local_reverse_cpp2_32f1713e_static_triage.json 存在。
2. artifact.sample_id == "cpp2_32f1713e"。
3. artifact.mainline == "tool_integration"。
4. artifact.executed_sample is false。
5. artifact.static_only is true。
6. artifact.runtime_validated is false。
7. artifact.candidate is null。
8. artifact.known_candidate == ""。
9. artifact.solved is not true 或 solved 字段不存在。
10. 如果 tool_status=success，则 source_tool == "IDA"，并包含 triage dict。
11. 如果 tool_status=blocked，则 blocked_reason 非空，且不得继续尝试 runtime/solver。
12. artifact_index latest_artifacts 和 latest_artifacts_v2 均登记 local_reverse_cpp2_32f1713e_static_triage。
13. local_reverse_training_status.json / local_reverse_evaluation_queue.json / status_overlay.json 未被修改。
14. git diff --name-status 只包含允许文件。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 SUCCESS/ACCEPTED，如果出现任一情况：

```text
1. cpp2_32f1713e 不再是 evaluation_queue rank=1，且没有明确理由选择它。
2. queue 中该样本 allowed_actions 不包含 static_triage。
3. 需要运行目标程序、runtime validator、debugger、hook、emulator、CompareProbe、solver 或 bruteforce 才能继续。
4. 需要上传、复制或提交样本 binary。
5. 现有 static_triage CLI 需要大范围改造或新增重复 IDA/Ghidra interface 才能继续。
6. 生成 artifact 中出现 known_candidate、candidate 非空、solved=true 或 runtime_validated=true。
7. artifact_index 无法登记 current provenance。
8. pytest、lint-decision、lint-report、status 任一失败且无法在本轮范围内最小修复。
9. git diff 显示 .codex-skills、solve_reports、训练状态 overlay 或无关源码变更。
10. 需要读取完整 solve_reports、完整 PROJECT_PROGRESS_LOG 或扫描完整本地训练目录。
```
