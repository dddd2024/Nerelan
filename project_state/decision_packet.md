```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_training_status_static_blocked_overlay_rework_v1",
  "round_id": "round_20260605_training_status_static_blocked_overlay_rework_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **training_dataset**。

目标：修复本地训练集状态覆盖逻辑，使 `project_state/local_reverse_training_status.json` 和 `project_state/local_reverse_evaluation_queue.json` 能正确反映已经完成的 current static-blocked artifacts，尤其是 `cpp1_2f6fcb63` 的最新 `target_provenance_recheck` 结果。

当前 `cpp1_2f6fcb63` 已经有 current artifacts 证明：

```text
provenance_verdict=CONFIRMED_NO_PRINTABLE_PREIMAGE
current_target_matches_raw_data=true
alternative_printable_span_count=0
candidate=null
known_candidate=""
runtime_validated=false
status=BLOCKED
blocked_reason=CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE
```

但 `local_reverse_training_status.json` 仍把 `cpp1_2f6fcb63` 标为 `inventory_only`，并且 `local_reverse_evaluation_queue.json` 仍把它排在下一轮 triage 第一位。这会导致训练集调度重复处理已经静态阻断的样本。

本轮要做的是 **状态/训练集索引一致性修复**，不是继续求解 `cpp1_2f6fcb63`，也不是打开新样本求解。

预期结果：

```text
1. `cpp1_2f6fcb63` 在 training_status 中变为 blocked。
2. blocked_reason 来自 current target_provenance_recheck artifact。
3. evidence_sources 包含 source:local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json 和 static_handoff/static_blocked_artifact 类标记。
4. known_candidate 仍为空。
5. evaluation_queue 不再包含 `cpp1_2f6fcb63`。
6. 不修改任何样本求解结果，不标记 solved。
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮；其 `task` 仍是 `Review bounded window discovery diagnostics`，并明确 `project_state/decision_packet.md` 才是当前执行权威。

当前 `current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id` 为：

```text
state_20260602_053948_4e3984041cd7
```

`based_on_state_digest` 为：

```text
4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

本轮不以 samplereverse 最新 harness 为主线，不读取 full solve_reports。

当前 `artifact_index.json` 中，`cpp1_2f6fcb63` 相关 artifacts 均为 current，包括：

```text
local_reverse_cpp1_2f6fcb63_static_triage
local_reverse_cpp1_2f6fcb63_target_bytes
local_reverse_cpp1_2f6fcb63_inverse_handoff
local_reverse_cpp1_2f6fcb63_transform_recheck
local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck
local_reverse_cpp1_2f6fcb63_signed_transform_recheck
local_reverse_cpp1_2f6fcb63_target_provenance_recheck
```

其中最新 target provenance artifact：

```text
kind=local_reverse_cpp1_target_provenance_recheck
path=project_state\local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json
freshness=current
source_run=round_20260605_cpp1_target_byte_provenance_recheck_v1
sample_id=cpp1_2f6fcb63
modified_at=2026-06-05T14:37:53Z
```

上一轮 `codex_execution_report.md`：

```text
report_id=report_20260605_cpp1_target_byte_provenance_recheck_v1
based_on_decision_id=decision_20260605_cpp1_target_byte_provenance_recheck_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt`：

```text
status=PASSED
Total Commands=12
Passed=12
Failed=0
project_state status: decision_report_id_match=True, decision_consumed_by_report=True
```

`project_state/local_reverse_training_status.json` 当前是旧输出：

```text
generated_at=2026-06-05T06:40:11Z
sample_count=29
status_summary.solved=1
status_summary.blocked=3
status_summary.inventory_only=25
```

其中 `cpp1_2f6fcb63` 当前仍错误地显示：

```text
training_status=inventory_only
known_candidate=""
blocked_reason=""
evidence_sources=[]
next_action="static triage and manual evaluation required"
```

`project_state/local_reverse_evaluation_queue.json` 当前也仍把 `cpp1_2f6fcb63` 列为 rank 1，allowed action 为 `static_triage`，这与已经存在的 current static-blocked artifacts 不一致。

已有相关实现能力：

```text
reverse_agent/local_reverse_training_status.py 已存在。
它负责合并 inventory、validated_candidate_handoff、constraint_recovery、ida_solver_result、artifact_index。
它已有严格静态 overlay gate：static_only=True、executed_sample=False、runtime_validated=False、candidate is None、status=BLOCKED、blocked_reason non-empty。
它当前只通过 `_STATIC_HANDOFF_SUFFIXES` / `_STATIC_ANALYSIS_SUFFIXES` 识别少数 artifact key 前缀，没有覆盖 `local_reverse_cpp1_2f6fcb63_target_provenance_recheck` 这类 current blocked static artifact。
tests/test_local_reverse_training_status.py 已存在，并已有 static overlay gate 测试。
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

本轮不会触碰这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不继续求解 `cpp1_2f6fcb63`。
2. 不打开新样本求解。
3. 不运行 IDA/Ghidra/debugger/runtime probe/hook/emulator。
4. 不动态执行任何样本。
5. 不做 runtime validation。
6. 不运行 brute force / old sample_solver / guided pool。
7. 不扩大 beam、topN、budget、timeout。
8. 不写 candidate。
9. 不写 known_candidate。
10. 不标记任何样本 solved，除非已有 validated_candidate_handoff 中存在 validation_status=validated。
11. 不把 static blocked artifact 当 solved。
12. 不提交原始样本、IDA sidecar、raw temp、full solve_reports 或本地绝对路径。
13. 不修改 `.codex-skills`。
14. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
15. 不把 task_packet.task 当执行权威。
16. 不为单一样本写死训练集逻辑；必须形成可复用 overlay 规则。
```

允许：

```text
1. 修改 `reverse_agent/local_reverse_training_status.py`。
2. 修改 `tests/test_local_reverse_training_status.py`。
3. 重新生成 `project_state/local_reverse_training_status.json`。
4. 重新生成 `project_state/local_reverse_evaluation_queue.json`。
5. 如果现有 CLI 需要，同步生成/更新 `training_materials/local_reverse/status_overlay.json`。
6. 更新 `project_state/codex_execution_report.md` 和 `project_state/pytest_result.txt`。
7. 只读取 current artifact_index 和 current static-blocked artifact JSON 的轻量内容。
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
project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
.codex-skills/registry.json
```

按需读取：

```text
project_state/local_reverse_inventory.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_validated_candidate_handoff.json
project_state/local_reverse_constraint_recovery_result.json
project_state/local_reverse_ida_solver_result.json
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
3. 是否确认本轮主线为 training_dataset。
4. 是否确认本轮没有继续求解 cpp1，也没有打开新样本求解。
5. 是否确认本轮没有运行 IDA/Ghidra/debugger/runtime probe/hook/emulator。
6. 是否确认本轮没有动态执行样本、没有 runtime validation。
7. 是否确认没有写 candidate / known_candidate。
8. 是否确认没有把任何 static-only artifact 标记为 solved。
9. 是否确认 `cpp1_2f6fcb63` 的 overlay 来源是 current `local_reverse_cpp1_2f6fcb63_target_provenance_recheck` artifact。
10. 是否确认该 artifact 满足 strict static blocked gate：static_only=true、executed_sample=false、runtime_validated=false、candidate=null、status=BLOCKED、blocked_reason non-empty。
11. 是否说明训练状态 overlay 规则是通用规则，不是只为 `cpp1_2f6fcb63` 硬编码。
12. 是否说明如果存在多个 current blocked static artifacts，同一样本 overlay 的优先级如何确定。
13. 是否确认 `local_reverse_training_status.json` 中 `cpp1_2f6fcb63.training_status=blocked`。
14. 是否确认 `cpp1_2f6fcb63.known_candidate=""`。
15. 是否确认 `cpp1_2f6fcb63.blocked_reason=CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE`。
16. 是否确认 `local_reverse_evaluation_queue.json` 不再包含 `cpp1_2f6fcb63`。
17. 是否确认 status_summary 的 blocked/inventory_only 计数已随之更新。
18. 是否确认 GitHub-safe status overlay 不包含真实本地绝对路径。
19. 是否 tests_ran 完整列出 required commands。
20. 是否 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
21. 是否 git status/diff 没有原始样本、IDA sidecar、raw temp、solve_reports 或无关文件。
```

---

## 6. Implementation Scope

允许修改：

```text
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改，除非测试暴露确定错误且报告中说明：

```text
project_state/artifact_index.json
project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/local_reverse_cpp1_transform_recheck.py
reverse_agent/local_reverse_cpp1_signed_transform_recheck.py
.codex-skills/*
```

实现要求：

```text
1. 保留现有 solved_map / blocked_map / static overlay 的优先级：validated solved > constraint blocked > current static blocked overlay > inventory_only。
2. 扩展 `_build_static_handoff_overlay`，使它能识别 current blocked static artifacts，而不是只识别 affine/legacy key prefix。
3. 识别规则必须依赖 artifact metadata + artifact payload gate，不能只靠 sample_id。
4. 必须继续跳过 stale/missing artifacts。
5. 必须继续跳过 executed_sample=true、runtime_validated=true、candidate present、status != BLOCKED、blocked_reason 为空的 artifact。
6. 如果同一样本有多个 current static blocked artifact，优先使用更具体/更下游的 artifact，例如：target_provenance_recheck > signed_transform_recheck > transform_recheck > inverse_handoff > static triage/decompile evidence。
7. evidence_sources 至少包含 artifact 文件名和 `static_handoff` 或等价的 `static_blocked_artifact` 标记。
8. classification 可以由 artifact 的 `analysis_mode`、`provenance_verdict`、`blocked_reason` 等字段组成，但不得把 candidate 或 local path 写入。
9. evaluation_queue 必须继续只包含 inventory_only/needs_triage 且未 blocked/solved 的样本。
10. 不得把 `local_reverse_training_status.json` 的旧 inventory_only 覆盖 artifact_index 的 current evidence。
```

新增/修改测试至少覆盖：

```text
1. current `local_reverse_cpp1_target_provenance_recheck` 风格 artifact 能产生 blocked overlay。
2. stale 同类 artifact 被跳过。
3. runtime_validated=true 同类 artifact 被跳过。
4. candidate present 同类 artifact 被跳过。
5. 多个同一样本 artifacts 时，target_provenance_recheck 优先级高于 transform_recheck/inverse_handoff。
6. end-to-end build 后 cpp1_2f6fcb63 从 queue 中移除。
7. GitHub status overlay 不包含 E:\reverse、D:\reverse、C:\reverse 或其他真实本地绝对路径。
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_training_status.py
python -m pytest -q tests/test_local_reverse_training_status.py
python -m reverse_agent.local_reverse_training_status --inventory project_state/local_reverse_inventory.json --validated project_state/local_reverse_validated_candidate_handoff.json --constraint-recovery project_state/local_reverse_constraint_recovery_result.json --solver-result project_state/local_reverse_ida_solver_result.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json --github-status-out training_materials/local_reverse/status_overlay.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果现有 CLI 参数名与上述命令不同，Codex 可以按实际 parser 参数调整，但必须在报告中写明替换原因和实际命令。

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
1. `project_state/artifact_index.json` 缺失，或 target_provenance artifact 不是 freshness=current。
2. `project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json` 缺失或不满足 strict static blocked gate。
3. 需要动态执行样本才能更新训练状态。
4. 需要运行 IDA/Ghidra/debugger/runtime probe/hook/emulator。
5. 需要读取 full solve_reports 或 PROJECT_PROGRESS_LOG 才能继续。
6. 需要提交原始样本、IDA sidecar、raw temp 或 full solve_reports。
7. 实现会把 static-only blocked artifact 标记为 solved。
8. 实现必须硬编码 `cpp1_2f6fcb63` 才能通过测试，而不能形成通用 overlay 规则。
```

成功完成的最低标准：

```text
1. training_status 中 cpp1_2f6fcb63 为 blocked。
2. cpp1_2f6fcb63 的 blocked_reason 来自 current target_provenance artifact。
3. cpp1_2f6fcb63 仍无 known_candidate。
4. evaluation_queue 不再包含 cpp1_2f6fcb63。
5. tests 和 project_state lint/status 记录完整。
6. report 明确说明没有推进样本求解，只修复训练集状态覆盖。
```
