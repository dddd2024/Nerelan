```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_training_status_overlay_rework_v1",
  "round_id": "round_20260605_affine_training_status_overlay_rework_v1",
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

上一轮 `decision_20260605_affine_training_status_overlay_v1` 审计结论为 `REWORK_REQUIRED`。功能上已经把 `affine_8cfebe03` 从 `inventory_only` 转为 `blocked`，并从 `local_reverse_evaluation_queue.json` 移除；但仍存在三个验收缺口：

```text
1. required command 缺失：pytest_result.txt / codex_report_summary.tests_ran 未记录 python -m reverse_agent.project_state lint-report --state-dir project_state。
2. static handoff overlay 越界：当前实现允许 status=READY 且 candidate 非空的 static handoff 直接变成 solved / known_candidate。
3. affine_8cfebe03 的 training tags/category 未充分反映 affine/static_handoff/missing_expected_ciphertext 训练标签。
```

本轮目标：**只返工 static handoff overlay 的验收缺口**。

必须完成：

```text
1. static handoff overlay 只接收 BLOCKED 静态 handoff，不允许 READY + candidate 直接变 solved。
2. 明确校验 static_only=true、executed_sample=false、runtime_validated=false、candidate=null。
3. 补全 affine_8cfebe03 的训练标签，使其反映 affine/static_handoff/missing_expected_ciphertext。
4. 补跑并记录 lint-report。
5. 重新生成 local_reverse_training_status.json、local_reverse_evaluation_queue.json、codex_execution_report.md、pytest_result.txt。
```

本轮不是继续解题，不生成 candidate，不运行样本，不读取完整 solve_reports。

---

## 2. Current Evidence

当前 `task_packet.json` 仍含旧 samplereverse advisory 信息，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮已完成且应保留的事实：

```text
project_state/local_reverse_training_status.json:
  affine_8cfebe03.training_status == blocked
  affine_8cfebe03.blocked_reason == MISSING_EXPECTED_CIPHERTEXT
  affine_8cfebe03.known_candidate == ""
  affine_8cfebe03.evidence_sources includes source:local_reverse_affine_inverse_handoff.json

project_state/local_reverse_evaluation_queue.json:
  affine_8cfebe03 已不在 items 中

现有 solved/blocked 状态应保持：
  cpp1_bcbd9979 remains solved
  cpp2_4c69f173 remains blocked
  sha_256_18019fca remains blocked
```

当前问题：

```text
reverse_agent/local_reverse_training_status.py:
  _build_static_handoff_overlay() 当前存在：
    if candidate and status == "READY":
        training_status = TRAINING_STATUS_SOLVED

该分支违反本轮 training_dataset 约束。static handoff 是静态证据，不得直接产生 solved / known_candidate。

当前 tests/test_local_reverse_training_status.py 中也有 READY + candidate -> solved 的测试，必须删除或改为“不会 solved”。
```

当前 affine handoff artifact 仍为 accepted/current evidence：

```text
project_state/local_reverse_affine_inverse_handoff.json
  sample_id: affine_8cfebe03
  static_only: true
  executed_sample: false
  runtime_validated: false
  expected_ciphertext: null
  ciphertext_provenance: null
  candidate: null
  status: BLOCKED
  blocked_reason: MISSING_EXPECTED_CIPHERTEXT
```

`negative_results.json` 仍禁止 old sample_solver blind search、only increase beam/budget、commit full solve_reports、重复旧 runtime/probe 失败方向。本轮不得进入这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行任何本地样本。
3. 不运行 runtime probe、debugger、Frida、OllyDbg、x64dbg、emulator。
4. 不运行 old sample_solver blind search。
5. 不生成 flag、candidate 或 known_candidate。
6. 不把 static handoff 的 READY + candidate 标记为 solved。
7. 不把静态 handoff 说成 runtime validation。
8. 不发明 expected_ciphertext。
9. 不把 MISSING_EXPECTED_CIPHERTEXT 改写成 solved。
10. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
11. 不提交 full solve_reports、IDA .i64、log 或原始样本。
12. 不修改 .codex-skills。
13. 不新建第二套训练状态系统。
14. 不把 affine_8cfebe03 单样本逻辑硬编码成不可复用分支。
15. 不扩大到批量跑训练集。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_training_status.py，收紧 static handoff overlay 接收条件。
2. 修改 tests/test_local_reverse_training_status.py，覆盖 READY + candidate 不得 solved。
3. 重新生成 project_state/local_reverse_training_status.json。
4. 重新生成 project_state/local_reverse_evaluation_queue.json。
5. 如当前命令会更新 training_materials/local_reverse/status_overlay.json，可同步提交；如果不提交，报告必须解释原因。
6. 更新 codex_execution_report.md 和 pytest_result.txt。
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
project_state/local_reverse_affine_inverse_handoff.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
```

必要时检查：

```text
training_materials/local_reverse/status_overlay.json
training_materials/local_reverse/inventory.json
tests/test_project_state.py
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
3. 是否确认本轮主线为 training_dataset，且没有扩大到 reverse_solving / tool_integration。
4. 是否确认 affine handoff artifact 为 freshness=current。
5. 是否确认 handoff artifact status=BLOCKED、blocked_reason=MISSING_EXPECTED_CIPHERTEXT、candidate=null。
6. 是否复用 reverse_agent/local_reverse_training_status.py，而不是新建第二套训练状态系统。
7. 是否把 static handoff overlay 收紧为只接受 BLOCKED 静态 handoff。
8. 是否移除或改写 READY + candidate -> solved 的逻辑。
9. 是否测试 READY + candidate 不会生成 solved/known_candidate。
10. 是否测试缺少 static_only/executed_sample/runtime_validated 字段的 artifact 不会被接收为 blocked。
11. 是否重新生成 local_reverse_training_status.json。
12. 是否确认 affine_8cfebe03 仍为 training_status=blocked。
13. 是否确认 affine_8cfebe03 的 blocked_reason=MISSING_EXPECTED_CIPHERTEXT。
14. 是否确认 affine_8cfebe03 的 known_candidate=""。
15. 是否确认 affine_8cfebe03 的 evidence_sources 包含 source:local_reverse_affine_inverse_handoff.json。
16. 是否确认 affine_8cfebe03 的 tags 或 classification 明确包含 affine/static_handoff/missing_expected_ciphertext 信息。
17. 是否确认 affine_8cfebe03 不再出现在 local_reverse_evaluation_queue.json 的 items 中。
18. 是否确认 cpp1_bcbd9979 remains solved。
19. 是否确认 cpp2_4c69f173 remains blocked。
20. 是否确认 sha_256_18019fca remains blocked。
21. 是否没有生成 candidate / known_candidate。
22. 是否没有运行 affine.exe 或任何本地样本。
23. 是否没有运行 runtime probe、debugger、emulator。
24. 是否没有提交 solve_reports、IDA .i64、log、原始样本。
25. 是否没有修改 .codex-skills。
26. 是否更新 codex_execution_report.md 与 pytest_result.txt。
27. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_training_status_overlay_rework_v1。
28. codex_report_summary.tests_ran 是否完整列出 required commands，包括 lint-report。
29. pytest_result.txt 是否记录每条命令、Exit code 和输出摘要。
```

---

## 6. Implementation Scope

必须修改 `reverse_agent/local_reverse_training_status.py`：

```text
1. _build_static_handoff_overlay() 只接受满足以下条件的 artifact：
   - sample_id 非空
   - static_only is true
   - executed_sample is false
   - runtime_validated is false
   - status == BLOCKED
   - candidate is None
   - blocked_reason 非空

2. 不允许 static handoff READY + candidate 产生 TRAINING_STATUS_SOLVED。

3. 对不满足条件的 static artifact：
   - 应跳过，或标记为 needs_triage，但不得 solved。
   - 更推荐跳过，避免把未验证 candidate 写进训练状态。

4. 对 accepted affine handoff：
   - training_status=blocked
   - blocked_reason=MISSING_EXPECTED_CIPHERTEXT
   - known_candidate=""
   - evidence_sources 包含 source:local_reverse_affine_inverse_handoff.json 与 static_cipher_analysis 或 static_handoff
   - next_action 继续指向 provide expected ciphertext

5. 补全 affine 的训练标签：
   - 如果框架允许修改 tags，则 tags 至少包含 affine_cipher 或 affine、static_handoff、blocked_missing_expected_ciphertext。
   - 如果框架只允许保留 inventory tags，则 classification 必须明确包含 affine_cipher/static_handoff/missing_expected_ciphertext，并在报告中说明 tags 未改的原因。

6. 不得让 static handoff 覆盖 already solved 样本。
```

必须修改 `tests/test_local_reverse_training_status.py`：

```text
1. 删除或改写 READY + candidate -> solved 测试。
2. 新增测试：READY + candidate 的 static handoff 不会产生 solved/known_candidate。
3. 新增测试：缺少 static_only 字段时不接收为 blocked。
4. 新增测试：executed_sample=true 时不接收为 blocked。
5. 新增测试：runtime_validated=true 时不接收为 blocked，runtime validated 应由 validated candidate/handoff 路径处理，不由 static overlay 处理。
6. 保留 MISSING_EXPECTED_CIPHERTEXT -> blocked 测试。
7. 保留 stale artifact skip 测试。
8. 保留 solved > static_handoff_blocked 的优先级测试，避免覆盖 already solved 样本。
```

重新生成输出：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json if CLI updates it
```

不得删除或损坏现有 solved/blocked 状态：

```text
cpp1_bcbd9979 remains solved
cpp2_4c69f173 remains blocked
sha_256_18019fca remains blocked
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_training_status.py
python -m pytest -q tests/test_local_reverse_training_status.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_training_status --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

允许额外运行但不得替代 required commands：

```bash
python -m pytest -q tests/test_local_reverse_affine_inverse_handoff.py
```

测试期望：

```text
1. tests/test_local_reverse_training_status.py 覆盖 static handoff blocked overlay 的收紧条件。
2. READY + candidate static handoff 不会产生 solved/known_candidate。
3. 缺少 static_only/executed_sample/runtime_validated 约束的 artifact 不会被接收为 blocked。
4. local_reverse_training_status.json 中 affine_8cfebe03 为 blocked / MISSING_EXPECTED_CIPHERTEXT。
5. local_reverse_evaluation_queue.json 中不存在 affine_8cfebe03。
6. 不生成 candidate 或 known_candidate。
7. 现有 solved/blocked 样本状态不回退。
8. lint-report 记录并通过。
9. git status --short 不出现 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. project_state/local_reverse_affine_inverse_handoff.json 缺失或不是 freshness=current。
2. handoff artifact 不再是 BLOCKED / MISSING_EXPECTED_CIPHERTEXT / candidate=null。
3. 无法移除 READY + candidate -> solved 的 static overlay 逻辑。
4. 需要运行 affine.exe 或任何本地样本才能完成。
5. 需要 runtime probe/debugger/emulator 才能完成。
6. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG 才能完成。
7. 需要提交 solve_reports、IDA .i64、log 或原始样本才能完成。
8. 需要修改 .codex-skills 才能完成。
9. 更新训练状态会覆盖 solved 样本或损坏现有 blocked 样本。
```

完成条件：

```text
1. static handoff overlay 只接受 BLOCKED 静态 handoff。
2. READY + candidate static handoff 不能把样本标记 solved。
3. tests/test_local_reverse_training_status.py 覆盖该约束。
4. project_state/local_reverse_training_status.json 已重新生成。
5. affine_8cfebe03 保持 blocked / MISSING_EXPECTED_CIPHERTEXT / known_candidate=""。
6. affine_8cfebe03 不再出现在 local_reverse_evaluation_queue.json。
7. cpp1_bcbd9979 remains solved。
8. cpp2_4c69f173 remains blocked。
9. sha_256_18019fca remains blocked。
10. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision。
11. required tests 全部通过，包括 lint-report。
12. 未运行样本、runtime probe、debugger、emulator、old sample_solver blind search。
13. 未提交 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```
