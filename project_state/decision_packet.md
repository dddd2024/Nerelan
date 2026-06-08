```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_local_reverse_capability_review_bucket_rework_v1",
  "round_id": "round_20260608_local_reverse_capability_review_bucket_rework_v1",
  "based_on_state_build_id": "state_20260608_152003_e6fc7ab3ce85",
  "based_on_state_digest": "e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067",
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

目标：对上一轮生成的 `project_state/local_reverse_training_capability_review.json` 做一次 **metadata-only 小范围返工**，只修正 inventory 分桶统计和分类瑕疵，不推进任何新样本求解。

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`，需要修复两个明确问题：

```text
1. crypto_cipher_inventory_only.count=5，但 sample_ids 实际包含 6 个样本。
2. unknown_pe_inventory_only 中包含 pwd_030127ca；该样本是 .txt / guessed_file_type=text，不应归入 unknown PE。
```

本轮必须完成：

```text
1. 读取默认 project_state 文件，确认 decision_packet 是唯一执行权威，task_packet 只是 advisory。
2. 读取 project_state/local_reverse_training_capability_review.json。
3. 读取 project_state/local_reverse_training_status.json 与 training_materials/local_reverse/status_overlay.json 作为 truth source。
4. 修正 review artifact 的 inventory_buckets，使 bucket count 与 sample_ids 数量一致，且分类符合 extension/guessed_file_type/category。
5. 保持 status_summary 不变：sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20。
6. 不修改 solved_cases、blocked_cases、capability_gaps、next_queue_candidates，除非需要同步 bucket 名称引用；不得引入新求解结论。
7. 更新 artifact_index 中 local_reverse_training_capability_review 的 sha256、size_bytes、modified_at、source_run，使其指向本轮 rework。
8. 更新 codex_execution_report.md 和 pytest_result.txt，绑定本轮 decision_id/round_id。
```

本轮不得生成 candidate，不得运行样本，不得 runtime validation，不得执行 IDA/Ghidra/radare2/objdump，不得 attach debugger/hook/emulator/winpty，不得读取或提交完整 `solve_reports/`。

---

## 2. Current Evidence

当前事实来源优先级仍是 GitHub 当前代码与 `project_state/`。当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威；`project_state/task_packet.json` 仍是 advisory，且其内容可能仍是 `samplereverse` sample_state，不能作为本轮任务。

上一轮 `codex_execution_report.md`：

```text
report_id=report_20260608_local_reverse_training_capability_review_v1
round_id=round_20260608_local_reverse_training_capability_review_v1
based_on_decision_id=decision_20260608_local_reverse_training_capability_review_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
mainline=training_dataset
candidate_generated=false
runtime_validation_attempted=false
ida_ghidra_static_extraction_attempted=false
full_solve_reports_read=false
```

上一轮 `pytest_result.txt`：

```text
status=PASSED
pytest=158 passed
lint-decision=OK
lint-report=OK
project_state status=OK
```

上一轮 review artifact 已完成主体复盘：

```text
status_summary:
  sample_count=29
  solved=5
  blocked=4
  needs_triage=0
  inventory_only=20

solved_cases: 5
blocked_cases: 4
next_queue_candidates: advisory only
```

需要返工的两个证据点：

```text
crypto_cipher_inventory_only:
  count=5
  sample_ids 实际列出 6 个：
    des_interactive_solver_256e1726
    desenc_0e0b5203
    desenc_14c58fcd
    desenc_40cba418
    rc4enc_3480917d
    rc4_add1978d

unknown_pe_inventory_only:
  sample_ids 包含 pwd_030127ca，但该样本在 local_reverse_training_status 中为：
    extension=.txt
    guessed_file_type=text
    category=unknown
```

`local_reverse_training_status.json` 中 inventory-only 样本应被合理分桶：

```text
cpp_pe_inventory_only:
  cpp2_f2738577
  cpp2_fc735338
  cpp3_019fcdc8
  cpp3_e5a33e0b
  cpp4_ab1b6104
  cpp5_2ea076a7
  cpp_6af7c7f1

crypto_cipher_pe_inventory_only:
  desenc_0e0b5203
  desenc_14c58fcd
  desenc_40cba418
  rc4enc_3480917d

crypto_cipher_python_reference_inventory_only:
  des_interactive_solver_256e1726
  rc4_add1978d

python_solver_like_inventory_only:
  byte_shift_transform_solver_3718a6fa
  sha_cd947414
  xor_array_solver_4e6d25f0

unknown_pe_inventory_only:
  main_36c51ec1
  main_fb1f8cc0
  seh_52be8d5c

text_or_support_inventory_only:
  pwd_030127ca
```

以上分桶总数应为 20：7 + 4 + 2 + 3 + 3 + 1 = 20。

`negative_results.json` 仍必须遵守：不回到 old sample_solver blind search，不只扩大 beam/budget，不提交 full solve_reports，不把 stale/missing artifact 当 current，不重复已失败方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 是 active skill，本轮只使用该 profile。

已有能力边界：

```text
1. 使用现有 project_state/artifact_index/report/pytest 结构。
2. 使用现有 local_reverse_training_status/status_overlay metadata。
3. 不新增 solver/runtime/tool/IDA/Ghidra/debugger 接口。
4. 不修改 .codex-skills。
5. 不读取 heavy solve_reports artifact 内容。
```

---

## 3. Do Not Do

严格禁止：

```text
1. 不要进入 reverse_solving。
2. 不要选择并求解新样本。
3. 不要生成 candidate。
4. 不要运行样本、console validator、negative control、runtime validation、winpty、debugger、hook、emulator、probe。
5. 不要执行 IDA/Ghidra/radare2/objdump/static extraction。
6. 不要 brute force、dictionary search、fuzz、beam/topN、扩大 timeout/budget。
7. 不要新增 solver/harness/runtime/IDA/Ghidra/debugger 接口。
8. 不要修改 solver production code。
9. 不要修改 .codex-skills。
10. 不要读取完整 solve_reports。
11. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
12. 不要提交 full solve_reports。
13. 不要提交样本二进制或本地绝对路径。
14. 不要把 task_packet.task 当执行权威。
15. 不要把 stale/missing/unknown artifact 当 current。
16. 不要把单样本 candidate、flag、run name、runtime metric 写入长期 skill。
17. 不要无必要修改 project_state/model_gate.json 或 project_state/negative_results.json。
18. 不要改变 next_queue_candidates 的授权边界；它们仍只能是 advisory。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 project_state/local_reverse_training_capability_review.json。
3. 读取 project_state/local_reverse_training_status.json。
4. 读取 training_materials/local_reverse/status_overlay.json。
5. 读取 training_materials/local_reverse/README.md。
6. 有界读取 project_state/local_reverse_inventory.json 或 training_materials/local_reverse/inventory.json，只用于确认 extension/type/category。
7. 修改 project_state/local_reverse_training_capability_review.json 的 inventory_buckets 和必要的 generated_at/metadata 字段。
8. 更新 project_state/artifact_index.json 中该 review artifact 的索引元数据。
9. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
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
project_state/local_reverse_training_capability_review.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
training_materials/local_reverse/README.md
```

必要时有界读取：

```text
project_state/local_reverse_inventory.json
training_materials/local_reverse/inventory.json
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
任何本地样本二进制
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 training_dataset？
3. task_packet 是否仅为 advisory，且其 samplereverse derived_task 未被执行？
4. 本轮是否仅修复 capability review bucket metadata？
5. status_summary 是否仍为 sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20？
6. inventory_buckets 中所有 count 是否等于 sample_ids 长度？
7. inventory_buckets 的 sample_id 总数是否为 20，且没有重复？
8. crypto/cipher .exe PE 样本是否与 crypto/cipher Python reference 样本分开？
9. unknown_pe_inventory_only 是否只包含 extension=.exe 且 guessed_file_type=pe 的 unknown PE 样本？
10. pwd_030127ca 是否不再归入 unknown_pe_inventory_only，并被归入 text/support 类 bucket？
11. next_queue_candidates 是否仍排除 solved/blocked 样本，且仍为 advisory only？
12. 是否没有生成 candidate、没有运行样本、没有 runtime validation？
13. 是否没有执行 IDA/Ghidra/static extraction/debugger/hook/emulator/winpty？
14. 是否没有读取或提交 full solve_reports / PROJECT_PROGRESS_LOG？
15. 是否没有修改 .codex-skills？
16. 是否没有提交样本二进制或本地绝对路径？
17. artifact_index 是否更新 review artifact 的 sha256/size_bytes/modified_at/source_run？
18. codex_report_summary.files_changed 是否与 git diff --name-status 一致？
19. 是否运行 JSON parse 校验？
20. 是否运行 JSON content 校验？
21. 是否运行 py_compile？
22. 是否运行 focused pytest？结果是多少？
23. 是否运行 lint-decision、lint-report、project_state status？
24. 是否运行 git diff --check、git status --short、git diff --name-status？
```

---

## 6. Implementation Scope

### Phase A — Confirm authority and limitation

读取默认状态文件，确认：

```text
1. 本轮 decision_packet 控制执行。
2. task_packet 只是 advisory。
3. 上一轮 report/pytest 是可审计 SUCCESS/PASSED。
4. 返工目标仅为 capability review 的 inventory bucket metadata。
5. 不需要也不允许新样本求解。
```

### Phase B — Correct inventory buckets

修改：

```text
project_state/local_reverse_training_capability_review.json
```

要求：

```text
1. 保持 artifact_kind=local_reverse_training_capability_review。
2. 保持 decision_id 可为原 review decision，但建议增加或更新字段：rework_decision_id=decision_20260608_local_reverse_capability_review_bucket_rework_v1。
3. 保持 status_summary：29/5/4/0/20。
4. 保持 solved_cases=5 与 blocked_cases=4。
5. 修正 inventory_buckets。
```

推荐修正后的 buckets：

```text
cpp_pe_inventory_only:
  count=7
  sample_ids=[cpp2_f2738577, cpp2_fc735338, cpp3_019fcdc8, cpp3_e5a33e0b, cpp4_ab1b6104, cpp5_2ea076a7, cpp_6af7c7f1]

crypto_cipher_pe_inventory_only:
  count=4
  sample_ids=[desenc_0e0b5203, desenc_14c58fcd, desenc_40cba418, rc4enc_3480917d]

crypto_cipher_python_reference_inventory_only:
  count=2
  sample_ids=[des_interactive_solver_256e1726, rc4_add1978d]

python_solver_like_inventory_only:
  count=3
  sample_ids=[byte_shift_transform_solver_3718a6fa, sha_cd947414, xor_array_solver_4e6d25f0]

unknown_pe_inventory_only:
  count=3
  sample_ids=[main_36c51ec1, main_fb1f8cc0, seh_52be8d5c]

text_or_support_inventory_only:
  count=1
  sample_ids=[pwd_030127ca]

other_inventory_only:
  count=0
  sample_ids=[]
```

如果 Codex 发现 inventory metadata 与上述推荐不一致，必须以 `local_reverse_training_status.json` 和 inventory metadata 为准，并在报告中说明差异。

### Phase C — Update index and reports

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 中 `local_reverse_training_capability_review` 必须更新：

```text
kind=local_reverse_training_capability_review
path=project_state\local_reverse_training_capability_review.json
freshness=current
source_run=round_20260608_local_reverse_capability_review_bucket_rework_v1
sha256=<真实 sha256>
size_bytes=<真实 size>
modified_at=<实际更新时间>
```

`codex_report_summary` 必须绑定：

```text
based_on_decision_id=decision_20260608_local_reverse_capability_review_bucket_rework_v1
round_id=round_20260608_local_reverse_capability_review_bucket_rework_v1
mainline=training_dataset
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
debugger_attached=false
emulator_used=false
ida_ghidra_static_extraction_attempted=false
full_solve_reports_read=false
```

---

## 7. Tests

必须运行并记录：

```powershell
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/task_packet.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/current_state.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/artifact_index.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('training_materials/local_reverse/status_overlay.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/local_reverse_training_status.json', encoding='utf-8'))"
.venv\Scripts\python.exe -c "import json; json.load(open('project_state/local_reverse_training_capability_review.json', encoding='utf-8'))"
.venv\Scripts\python.exe -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_training.py reverse_agent/local_reverse_training_status.py reverse_agent/sample_metadata.py
.venv\Scripts\python.exe -m pytest -q tests/test_project_state.py
.venv\Scripts\python.exe -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python.exe -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python.exe -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

必须追加一个 JSON content 校验，至少检查：

```text
1. status_summary.inventory_only == 20
2. sum(bucket.count for bucket in inventory_buckets) == 20
3. 每个 bucket.count == len(bucket.sample_ids)
4. 所有 inventory bucket sample_id 无重复
5. crypto_cipher_pe_inventory_only 只包含 desenc_0e0b5203/desenc_14c58fcd/desenc_40cba418/rc4enc_3480917d 或 metadata 等价 PE crypto/cipher 样本
6. crypto_cipher_python_reference_inventory_only 包含 des_interactive_solver_256e1726 与 rc4_add1978d
7. unknown_pe_inventory_only 不包含 pwd_030127ca
8. text_or_support_inventory_only 包含 pwd_030127ca
9. next_queue_candidates 不包含 solved/blocked 样本
10. guardrails.runtime_validation_attempted == false
11. guardrails.ida_ghidra_static_extraction_attempted == false
```

如存在 local_reverse training/status 专项测试，必须追加运行并记录；若不存在，报告中说明未发现专项测试。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. 需要运行样本、runtime validation、console validator、debugger、hook、emulator、winpty、IDA/Ghidra/static extraction。
2. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
3. status_overlay.json 与 local_reverse_training_status.json 的 summary 不一致。
4. 无法从 metadata 得到 inventory_only=20 的一致状态。
5. review artifact 的 bucket count 与 sample_ids 长度仍不一致。
6. inventory bucket sample_id 总数不是 20，或存在重复 sample_id。
7. unknown_pe_inventory_only 仍包含非 PE/text/support 样本，如 pwd_030127ca。
8. crypto/cipher PE 与 Python reference 仍混在同一个未说明类型的 bucket 中。
9. next_queue_candidates 包含已 solved 或 blocked 样本，或被写成当前执行任务。
10. artifact_index 未登记 review artifact 或 freshness/source_run/sha256/size_bytes 缺失。
11. codex_report_summary 缺失或 based_on_decision_id/round_id 不匹配。
12. pytest_result 缺失或未绑定当前 decision/report/round。
13. JSON parse、JSON content 校验、lint-report、project_state status 或 focused pytest 失败。
14. git diff 包含 full solve_reports、PROJECT_PROGRESS_LOG 全量改动、.codex-skills 动态事实、样本二进制、本地绝对路径或无关代码变更。
15. 本轮修改 solver/runtime/tool 接口。
16. 本轮无必要修改 model_gate.json 或 negative_results.json，且报告没有解释为必要副作用。
```

完成后不要推进新样本求解。若本轮通过，下一轮才可基于修正后的 `local_reverse_training_capability_review.json` 选择 `cpp2_f2738577` 做 **bounded static triage/readiness**；仍需单独 DECISION_PACKET 授权。
