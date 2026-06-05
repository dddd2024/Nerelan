```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_7b504c54_static_triage_v1",
  "round_id": "round_20260605_cpp1_7b504c54_static_triage_v1",
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

目标：按 `project_state/local_reverse_evaluation_queue.json` 的 rank 1 项，对本地训练样本 `cpp1_7b504c54` 做一次 **bounded static triage**，只使用现有静态工具接口提取轻量证据，并登记 current artifact。

目标样本：

```text
sample_id=cpp1_7b504c54
relative_path=逆向课程2023春补考01/Cpp1.exe
sha256=7b504c54c165100549a0eacb7eb7cad26bc235ec0c4bed5c38c95a827ff81a3c
size_bytes=184398
category=cpp
tags=local, reverse, cpp, pe
queue_rank=1
allowed_actions=static_triage
forbidden_actions=runtime_probe, bruteforce, upload_binary
```

本轮只允许：

```text
1. 复用现有 `reverse_agent/local_reverse_single_sample_static_triage.py`。
2. 复用现有 `reverse_agent/tool_runners.py` 的 IDA resolver。
3. 复用现有 `reverse_agent/ida_scripts/collect_evidence.py`。
4. 生成轻量 JSON artifact：`project_state/local_reverse_cpp1_7b504c54_static_triage.json`。
5. 将该 artifact 登记进 `project_state/artifact_index.json`，freshness=current。
```

本轮不得：

```text
1. 新建第二套 IDA runner。
2. 动态执行样本。
3. runtime validation。
4. debugger/runtime probe/hook/emulator。
5. brute force / solver / candidate generation。
6. 写 candidate / known_candidate。
7. 标记 solved。
8. 修改训练状态队列，除非只是报告明确说明需要下一轮单独决定。
```

预期 artifact key：

```text
local_reverse_cpp1_7b504c54_static_triage
```

artifact_index 登记要求：

```text
kind=local_reverse_single_sample_static_triage
path=project_state\local_reverse_cpp1_7b504c54_static_triage.json
freshness=current
source_run=round_20260605_cpp1_7b504c54_static_triage_v1
sample_id=cpp1_7b504c54
```

如果 IDA 或本地样本路径不可用，Codex 必须生成 blocked static triage artifact，说明 `STATIC_TOOL_UNAVAILABLE`、`BINARY_NOT_FOUND` 或等价原因；仍不得改为动态执行或 brute force。

---

## 2. Current Evidence

当前 `project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。其 `execution_scope=decision_packet_controls_current_round`，并且 `local_reverse_task_packet_authority_note` 明确 `project_state/decision_packet.md` 才是当前执行权威。

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态：

```text
state_build_id=state_20260602_053948_4e3984041cd7
state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 engineering branch 已完成并通过审计：

```text
decision_id=decision_20260605_report_summary_generated_artifacts_schema_fix_v1
report_id=report_20260605_report_summary_generated_artifacts_schema_fix_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt` 显示：

```text
status=PASSED
Total Commands=8
Passed=8
Failed=0
lint-decision: OK
lint-report: OK
generated_artifacts_count=2
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

当前 `project_state/local_reverse_training_status.json` 显示：

```text
sample_count=29
status_summary.solved=1
status_summary.blocked=4
status_summary.inventory_only=24
```

其中 `cpp1_2f6fcb63` 已正确为 static-only blocked：

```text
training_status=blocked
known_candidate=""
blocked_reason=CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE
```

当前 `project_state/local_reverse_evaluation_queue.json` 的 rank 1 为：

```text
sample_id=cpp1_7b504c54
relative_path=逆向课程2023春补考01/Cpp1.exe
proposed_next_mainline=tool_integration
allowed_actions=[static_triage]
forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

当前 `artifact_index.json` 中尚未看到 `local_reverse_cpp1_7b504c54_static_triage`。已存在的 `cpp1_2f6fcb63` current artifacts 只是前一个样本的证据，不能用于 `cpp1_7b504c54`。

已有相关工具能力：

```text
reverse_agent/local_reverse_single_sample_static_triage.py
  - 已存在。
  - 说明中明确 reads evaluation queue / inventory。
  - 复用 existing tool_runners / collect_evidence.py。
  - Does NOT execute target binary。
  - Does NOT generate candidates。

reverse_agent/tool_runners.py
  - 已存在 `_resolve_ida_executable`。
  - 已存在 `_resolve_ida_script`。
  - 默认 IDA script 为 `reverse_agent/ida_scripts/collect_evidence.py`。

tests/test_local_reverse_single_sample_static_triage.py
  - 已存在。
  - 覆盖 sample root、queue/inventory locate、binary path resolve、IDA evidence parse、blocked artifact 等行为。
```

当前 negative_results 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. use compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat dynamic-probe directions without new evidence
6. run Base64/RC4 breakpoint probe before real lhs producer identification
```

本轮不触碰这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不推进 `cpp1_2f6fcb63`。
2. 不打开 rank 2 或后续样本。
3. 不运行 solver、bruteforce、guided pool、constraint recovery。
4. 不生成 candidate。
5. 不写 known_candidate。
6. 不标记 solved。
7. 不动态执行样本。
8. 不做 runtime validation。
9. 不运行 debugger/runtime probe/hook/emulator。
10. 不新建 IDA runner 或重复实现 IDA/Ghidra/strings/objdump 已有能力。
11. 不上传、提交或复制本地 binary。
12. 不提交 IDA `.i64`、`.id0`、`.id1`、`.nam`、`.til`、log、raw temp、`project_state/triage_*` 临时目录或 full `solve_reports`。
13. 不修改 `.codex-skills`。
14. 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
15. 不把 `task_packet.task` 当执行权威。
16. 不修改 `local_reverse_training_status.json` / `local_reverse_evaluation_queue.json`，除非 report 明确说明只是被测试框架意外触发；正常本轮不得改。
```

允许：

```text
1. 读取 queue/inventory/status/artifact_index。
2. 运行现有 single-sample static triage CLI。
3. 运行 IDA headless static extraction，前提是只针对 `cpp1_7b504c54` 且不执行样本逻辑。
4. 生成 `project_state/local_reverse_cpp1_7b504c54_static_triage.json`。
5. 更新 `project_state/artifact_index.json`，登记该 artifact。
6. 更新 `project_state/codex_execution_report.md` 和 `project_state/pytest_result.txt`。
7. 必要时对 `local_reverse_single_sample_static_triage.py` 做最小修复，前提是只修复 static triage 输出、artifact hygiene 或 CLI 默认值问题，并用测试覆盖。
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
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
tests/test_local_reverse_single_sample_static_triage.py
tests/test_tool_runners.py
.codex-skills/registry.json
```

按需读取：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
# 仅作旧样本 static triage artifact 格式参考，不得当作当前样本证据。
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
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认本轮只处理 `cpp1_7b504c54`。
5. 是否确认 evaluation_queue rank 1 与本轮 sample_id 一致。
6. 是否确认 allowed_actions 只有 static_triage，且 forbidden_actions 包含 runtime_probe、bruteforce、upload_binary。
7. 是否确认使用了现有 `local_reverse_single_sample_static_triage.py` 和 `tool_runners` / IDA script，没有新建 IDA runner。
8. 是否说明 IDA 是否实际运行；如果运行，必须说明是 headless static extraction，不是动态执行。
9. 是否确认没有运行 debugger/runtime probe/hook/emulator。
10. 是否确认没有动态执行样本，没有 runtime validation。
11. 是否确认没有 solver/bruteforce/guided pool。
12. 是否确认没有写 candidate / known_candidate。
13. 是否确认没有标记 solved。
14. 是否确认没有修改 training_status / evaluation_queue。
15. 是否确认没有提交本地 binary、IDA sidecar、raw temp、triage temp dir 或 solve_reports。
16. 是否生成 `project_state/local_reverse_cpp1_7b504c54_static_triage.json`。
17. 是否将 artifact 登记到 `project_state/artifact_index.json`，freshness=current，source_run=round_20260605_cpp1_7b504c54_static_triage_v1。
18. 是否说明 artifact 中的 `executed_sample=false`、`static_only=true`、`runtime_validated=false`。
19. 如果 tool_status=success，是否列出 input_apis、interesting_strings、functions、compare_contexts、validation_function_candidates、solver_profile_hypotheses 的数量摘要。
20. 如果 tool_status=blocked，是否给出明确 blocked_reason，并说明下一步仍应停留在工具/路径可用性修复而不是求解。
21. 是否 `codex_report_summary.generated_artifacts` 包含本轮生成/重写的 project_state artifacts。
22. 是否 `pytest_result.txt` 记录每条命令、Exit Code 和输出摘要。
23. 是否 `git status --short` 和 `git diff --name-status` 只包含允许文件。
```

---

## 6. Implementation Scope

优先执行现有 CLI，不要改代码：

```bash
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp1_7b504c54 --queue project_state/local_reverse_evaluation_queue.json --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_7b504c54_static_triage.json
```

允许修改：

```text
project_state/local_reverse_cpp1_7b504c54_static_triage.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

仅在现有 static triage 脚本存在直接阻断本轮目标的 bug 时允许修改，并必须用测试覆盖：

```text
reverse_agent/local_reverse_single_sample_static_triage.py
tests/test_local_reverse_single_sample_static_triage.py
```

不得修改：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_2f6fcb63_*.json
reverse_agent/project_state.py
reverse_agent/local_reverse_training_status.py
.codex-skills/*
solve_reports/*
```

`local_reverse_cpp1_7b504c54_static_triage.json` 至少包含：

```text
schema_version
sample_id=cpp1_7b504c54
relative_path
analysis_mode=single_sample_static_triage
mainline=tool_integration
executed_sample=false
static_only=true
runtime_validated=false
generated_at
tool_status=success|blocked
blocked_reason
source_tool
sha256
size_bytes
file_type
category
tags
queue_rank=1
triage.input_apis
triage.interesting_strings
triage.functions
triage.compare_contexts
triage.validation_function_candidates
triage.solver_profile_hypotheses
candidate=null
known_candidate=""
recommended_next_action
```

Artifact hygiene：

```text
1. 不得把 LOCAL_REVERSE_ROOT 的真实本地绝对路径写入 artifact。
2. 不得把 IDA sidecar path 写入 artifact。
3. 不得提交 `project_state/triage_cpp1_7b504c54/` 或等价临时目录。
4. 若 IDA 产生临时 `.i64` / log / raw evidence 文件，必须从 git working tree 中排除或删除，只保留轻量 JSON artifact。
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_single_sample_static_triage.py
python -m pytest -q tests/test_local_reverse_single_sample_static_triage.py
python -m pytest -q tests/test_tool_runners.py
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp1_7b504c54 --queue project_state/local_reverse_evaluation_queue.json --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_7b504c54_static_triage.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果 IDA 或 LOCAL_REVERSE_ROOT 不可用，第四条命令仍应生成 blocked artifact 并 Exit Code 0；如果实际 CLI 当前不能这样做，Codex 可以做最小修复并补测试。

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED 结果；
5. 本轮 decision_id、round_id、report_id。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. `cpp1_7b504c54` 不再是 evaluation_queue rank 1，且没有用户新指令允许切换样本。
2. queue/inventory 中找不到 `cpp1_7b504c54`。
3. 需要动态执行样本才能继续。
4. 需要 debugger/runtime probe/hook/emulator。
5. 需要 solver/bruteforce/candidate generation。
6. 需要上传或提交本地 binary。
7. 需要新建 IDA runner 而不是复用现有 tool_runners/collect_evidence。
8. 需要读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
9. 运行 static triage 会产生必须提交的 IDA sidecar/raw temp 文件。
10. artifact_index 更新会覆盖或降级已有 current artifacts。
```

成功完成的最低标准：

```text
1. 生成 `project_state/local_reverse_cpp1_7b504c54_static_triage.json`。
2. artifact 明确 static_only=true、executed_sample=false、runtime_validated=false。
3. artifact 不含 candidate / known_candidate。
4. artifact_index 登记 current artifact。
5. report/pytest 通过 schema 要求，codex_report_summary.generated_artifacts 完整。
6. git diff 只包含允许文件。
```
