```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_training_status_overlay_v1",
  "round_id": "round_20260605_affine_training_status_overlay_v1",
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

上一轮 `decision_20260605_affine_inverse_handoff_artifact_consistency_rework_v1` 已被审计为 `ACCEPTED`。当前已确认：

```text
project_state/local_reverse_affine_inverse_handoff.json
  sample_id: affine_8cfebe03
  analysis_mode: affine_inverse_handoff_static_only
  executed_sample: false
  static_only: true
  runtime_validated: false
  cipher_type: affine_cipher
  inverse_transform.inverse_a: 21
  expected_ciphertext: null
  ciphertext_provenance: null
  candidate: null
  status: BLOCKED
  blocked_reason: MISSING_EXPECTED_CIPHERTEXT
```

但是 `project_state/local_reverse_training_status.json` 仍把 `affine_8cfebe03` 记录为：

```text
training_status: inventory_only
category: unknown
classification: ""
evidence_sources: []
next_action: static triage and manual evaluation required
```

同时 `project_state/local_reverse_evaluation_queue.json` 仍把 `affine_8cfebe03` 排在 rank 1，建议继续 static_triage。该状态已经过期：affine 样本已完成静态 triage，并被 current handoff 明确阻断于 `MISSING_EXPECTED_CIPHERTEXT`。

本轮目标：**把已接受的 static handoff 结果接入训练状态 overlay，使 affine 样本从 inventory_only 转为 blocked，并从 evaluation queue 中移除。**

本轮不是继续解题，不生成 candidate，不运行样本，不读取完整 solve_reports。

---

## 2. Current Evidence

当前 `task_packet.json` 仍含旧 samplereverse advisory 信息，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前事实：

```text
1. affine handoff artifact 已 accepted，freshness=current。
2. artifact_index.latest_artifacts_v2.local_reverse_affine_inverse_handoff:
   freshness=current
   source_run=round_20260605_affine_inverse_handoff_artifact_consistency_rework_v1
   sample_id=affine_8cfebe03
3. handoff artifact 的实际内容包含 ciphertext_provenance:null。
4. handoff artifact 明确 status=BLOCKED, blocked_reason=MISSING_EXPECTED_CIPHERTEXT, candidate=null。
5. local_reverse_training_status.py 当前只从 inventory / validated_candidate_handoff / constraint_recovery / ida_solver_result 生成训练状态。
6. local_reverse_training_status.py 当前不会消费 local_reverse_affine_inverse_handoff.json 这种 static handoff artifact。
7. local_reverse_training_status.json 因此仍把 affine_8cfebe03 当 inventory_only。
8. local_reverse_evaluation_queue.json 因此仍把 affine_8cfebe03 放在 rank 1。
```

已有相关能力：

```text
reverse_agent/local_reverse_training_status.py
  - build_training_status()
  - _build_solved_map()
  - _build_blocked_map()
  - _build_evidence_sources_map()
  - _build_sample_entry()
  - _build_evaluation_queue()

该模块已经负责训练状态 overlay 和 evaluation queue。不得新建重复的训练状态生成器。
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
6. 不发明 expected_ciphertext。
7. 不把 MISSING_EXPECTED_CIPHERTEXT 改写成已 solved。
8. 不把静态 handoff 说成 runtime validation。
9. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
10. 不提交 full solve_reports、IDA .i64、log 或原始样本。
11. 不修改 .codex-skills。
12. 不新建第二套训练状态系统。
13. 不把 affine_8cfebe03 单样本逻辑硬编码成不可复用分支。
14. 不扩大到批量跑训练集。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_training_status.py，增加通用 static handoff overlay 输入能力。
2. 新增或修改 tests，覆盖 static handoff blocked overlay。
3. 重新生成 project_state/local_reverse_training_status.json。
4. 重新生成 project_state/local_reverse_evaluation_queue.json。
5. 如项目已有 training_materials/local_reverse/status_overlay.json，可同步更新。
6. 必要时更新 artifact_index.json 中 training status / queue 相关 artifact 的 sha256、size_bytes、modified_at；如果 artifact_index 当前没有这些 key，可不新增，除非已有规范要求。
7. 更新 codex_execution_report.md 和 pytest_result.txt。
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
7. 是否实现通用 static handoff overlay，而不是 affine_8cfebe03 单样本硬编码。
8. 是否重新生成 local_reverse_training_status.json。
9. 是否确认 affine_8cfebe03 的 training_status=blocked。
10. 是否确认 affine_8cfebe03 的 blocked_reason=MISSING_EXPECTED_CIPHERTEXT。
11. 是否确认 affine_8cfebe03 的 classification/category/tags/evidence_sources 已反映 affine_cipher / static handoff evidence。
12. 是否确认 affine_8cfebe03 不再出现在 local_reverse_evaluation_queue.json 的 items 中。
13. 是否没有生成 candidate / known_candidate。
14. 是否没有运行 affine.exe 或任何本地样本。
15. 是否没有运行 runtime probe、debugger、emulator。
16. 是否没有提交 solve_reports、IDA .i64、log、原始样本。
17. 是否没有修改 .codex-skills。
18. 是否更新 codex_execution_report.md 与 pytest_result.txt。
19. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_training_status_overlay_v1。
20. codex_report_summary.tests_ran 是否完整列出 required commands。
21. pytest_result.txt 是否记录每条命令、Exit code 和输出摘要。
```

---

## 6. Implementation Scope

优先实现：在 `reverse_agent/local_reverse_training_status.py` 中增加 **通用 static handoff overlay**。

建议设计：

```text
1. 增加 CLI 参数：
   --static-handoff project_state/local_reverse_affine_inverse_handoff.json
   可重复或支持逗号/列表均可，但实现必须简单、可测试。

2. build_training_status() 增加可选参数 static_handoff_paths: list[Path]。

3. 新增 helper，例如：
   _build_static_handoff_blocked_map(static_handoff_data_list)

4. 只接受满足以下条件的 handoff artifact：
   - sample_id 非空
   - static_only is true
   - executed_sample is false
   - runtime_validated is false
   - status == BLOCKED
   - candidate is None
   - blocked_reason 非空

5. 对这些 artifact 生成 blocked overlay：
   training_status=blocked
   blocked_reason=<handoff.blocked_reason>
   classification=<cipher_type 或 analysis_mode 派生，例如 affine_cipher_encoder_static_only>
   known_candidate=""
   evidence_sources 包含 source:local_reverse_affine_inverse_handoff.json 与 static_handoff
   next_action 对 MISSING_EXPECTED_CIPHERTEXT 应为：
     provide expected ciphertext from challenge statement or another allowed evidence source

6. 合并优先级：
   solved > static_handoff_blocked > existing constraint_blocked > inventory_only
   不得让 static handoff 覆盖 already solved 样本。

7. 更新 category/tags 时保持保守：
   - category 可设为 crypto/classical 或 crypto/cipher，如现有 taxonomy 不确定则保持原 category 但添加 classification/tags。
   - tags 至少应包含 affine_cipher 或 affine、static_handoff、blocked_missing_expected_ciphertext。
   不得改 unrelated samples。
```

输出要求：

```text
project_state/local_reverse_training_status.json:
  affine_8cfebe03.training_status == blocked
  affine_8cfebe03.blocked_reason == MISSING_EXPECTED_CIPHERTEXT
  affine_8cfebe03.known_candidate == ""
  affine_8cfebe03.evidence_sources includes source:local_reverse_affine_inverse_handoff.json
  affine_8cfebe03.next_action mentions expected ciphertext

project_state/local_reverse_evaluation_queue.json:
  items must not contain sample_id == affine_8cfebe03

training_materials/local_reverse/status_overlay.json if updated:
  affine_8cfebe03 should also be blocked with the same blocked_reason.
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
python -m reverse_agent.local_reverse_training_status --static-handoff project_state/local_reverse_affine_inverse_handoff.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

如果 CLI 参数名称不同，必须在报告中说明实际命令和原因，但必须保持“通用 static handoff overlay”语义。

测试期望：

```text
1. tests/test_local_reverse_training_status.py 覆盖 static handoff blocked overlay。
2. local_reverse_training_status.json 中 affine_8cfebe03 为 blocked / MISSING_EXPECTED_CIPHERTEXT。
3. local_reverse_evaluation_queue.json 中不存在 affine_8cfebe03。
4. 不生成 candidate 或 known_candidate。
5. 现有 solved/blocked 样本状态不回退。
6. git status --short 不出现 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. project_state/local_reverse_affine_inverse_handoff.json 缺失或不是 freshness=current。
2. handoff artifact 不再是 BLOCKED / MISSING_EXPECTED_CIPHERTEXT / candidate=null。
3. 需要运行 affine.exe 或任何本地样本才能完成。
4. 需要 runtime probe/debugger/emulator 才能完成。
5. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG 才能完成。
6. 需要提交 solve_reports、IDA .i64、log 或原始样本才能完成。
7. 需要修改 .codex-skills 才能完成。
8. 实现只能通过 affine_8cfebe03 单样本硬编码完成，无法形成通用 static handoff overlay。
9. 更新训练状态会覆盖 solved 样本或损坏现有 blocked 样本。
```

完成条件：

```text
1. local_reverse_training_status.py 支持通用 static handoff overlay。
2. tests/test_local_reverse_training_status.py 覆盖新 overlay。
3. project_state/local_reverse_training_status.json 已重新生成。
4. affine_8cfebe03 从 inventory_only 转为 blocked。
5. affine_8cfebe03 blocked_reason 为 MISSING_EXPECTED_CIPHERTEXT。
6. affine_8cfebe03 不再出现在 local_reverse_evaluation_queue.json。
7. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision。
8. required tests 全部通过。
9. 未运行样本、runtime probe、debugger、emulator、old sample_solver blind search。
10. 未提交 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```
