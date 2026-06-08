```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_local_reverse_capability_gap_text_cleanup_v1",
  "round_id": "round_20260608_local_reverse_capability_gap_text_cleanup_v1",
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

目标：对 `project_state/local_reverse_training_capability_review.json` 做一次 **极小范围 metadata cleanup**，只修正上一轮 bucket rework 后残留在 `capability_gaps` 中的旧 crypto/cipher 分桶文案，不进入新样本求解，不修改 solver/runtime/tool 接口。

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`，核心 bucket rework 已完成，但仍有一个残留文案：

```text
capability_gaps[].gap_id=crypto_cipher_static_evidence_requirements_for_DES_RC4_samples
current_state="5 crypto/cipher inventory_only samples await static evidence requirements definition"
evidence_basis="crypto_cipher_inventory_only bucket has 5-6 samples, all inventory_only"
```

该描述已经与当前修正后的分桶不一致。当前正确分桶应为：

```text
crypto_cipher_pe_inventory_only=count=4
  desenc_0e0b5203
  desenc_14c58fcd
  desenc_40cba418
  rc4enc_3480917d

crypto_cipher_python_reference_inventory_only=count=2
  des_interactive_solver_256e1726
  rc4_add1978d
```

本轮必须完成：

```text
1. 读取默认 project_state 文件，确认 decision_packet 是唯一执行权威，task_packet 只是 advisory。
2. 读取 project_state/local_reverse_training_capability_review.json。
3. 读取 project_state/local_reverse_training_status.json 与 training_materials/local_reverse/status_overlay.json 作为 truth source。
4. 只更新 capability_gaps 中 crypto_cipher_static_evidence_requirements_for_DES_RC4_samples 的 current_state/evidence_basis/description，消除旧 bucket 名称 crypto_cipher_inventory_only、旧数量 5-6、旧“5 samples”等不准确信息。
5. 保持 status_summary 不变：sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20。
6. 保持 inventory_buckets 当前修正结构不变：7+4+2+3+3+1+0=20。
7. 保持 solved_cases、blocked_cases、next_queue_candidates、guardrails 不变；不得引入新求解结论。
8. 更新 artifact_index 中 local_reverse_training_capability_review 的 sha256、size_bytes、modified_at、source_run，使其指向本轮 cleanup。
9. 更新 codex_execution_report.md 和 pytest_result.txt，绑定本轮 decision_id/round_id。
```

本轮不得生成 candidate，不得运行样本，不得 runtime validation，不得执行 IDA/Ghidra/radare2/objdump，不得 attach debugger/hook/emulator/winpty，不得读取或提交完整 `solve_reports/`。

---

## 2. Current Evidence

当前事实来源优先级仍是 GitHub 当前代码与 `project_state/`。当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威；`project_state/task_packet.json` 仍是 advisory，且其内容可能仍是 `samplereverse` sample_state，不能作为本轮任务。

上一轮 `codex_execution_report.md`：

```text
report_id=report_20260608_local_reverse_capability_review_bucket_rework_v1
round_id=round_20260608_local_reverse_capability_review_bucket_rework_v1
based_on_decision_id=decision_20260608_local_reverse_capability_review_bucket_rework_v1
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

上一轮 bucket rework 已完成的事实：

```text
cpp_pe_inventory_only=count=7
crypto_cipher_pe_inventory_only=count=4
crypto_cipher_python_reference_inventory_only=count=2
python_solver_like_inventory_only=count=3
unknown_pe_inventory_only=count=3
text_or_support_inventory_only=count=1
other_inventory_only=count=0
sum=20
pwd_030127ca 已归入 text_or_support_inventory_only
unknown_pe_inventory_only 不再包含 pwd_030127ca
next_queue_candidates 仍为 advisory only
```

当前残留问题只在 `capability_gaps` 文案，不在 bucket 结构：

```text
gap_id=crypto_cipher_static_evidence_requirements_for_DES_RC4_samples
current_state 仍写 "5 crypto/cipher inventory_only samples..."
evidence_basis 仍写旧 bucket "crypto_cipher_inventory_only" 与 "5-6 samples"
```

建议替换为类似：

```text
description="No cipher-specific static evidence profile for DES/RC4 PE samples; Python crypto/cipher files should be treated as references, not primary binary targets."
current_state="4 crypto/cipher PE samples await static evidence profile; 2 crypto/cipher Python files are reference material."
evidence_basis="crypto_cipher_pe_inventory_only.count=4 and crypto_cipher_python_reference_inventory_only.count=2 in local_reverse_training_capability_review.json."
```

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
18. 不要改变 inventory_buckets 的样本归属。
19. 不要改变 next_queue_candidates 的授权边界；它们仍只能是 advisory。
20. 不要新增或删除 capability_gaps，只允许修正文案字段。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 project_state/local_reverse_training_capability_review.json。
3. 读取 project_state/local_reverse_training_status.json。
4. 读取 training_materials/local_reverse/status_overlay.json。
5. 读取 training_materials/local_reverse/README.md。
6. 修改 project_state/local_reverse_training_capability_review.json 中指定 gap 的 description/current_state/evidence_basis 与必要 updated_at/rework metadata。
7. 更新 project_state/artifact_index.json 中该 review artifact 的索引元数据。
8. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
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
4. 本轮是否仅修复 capability_gaps crypto/cipher stale wording？
5. status_summary 是否仍为 sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20？
6. inventory_buckets 是否保持 7+4+2+3+3+1+0=20，且所有 count == len(sample_ids)？
7. capability_gaps 中是否不再出现旧 bucket 名 crypto_cipher_inventory_only？
8. capability_gaps 中是否不再出现旧数量文本 "5-6 samples" 或 "5 crypto/cipher inventory_only samples"？
9. crypto/cipher gap 是否明确区分 4 个 PE cipher 样本与 2 个 Python reference 样本？
10. next_queue_candidates 是否仍排除 solved/blocked 样本，且仍为 advisory only？
11. 是否没有生成 candidate、没有运行样本、没有 runtime validation？
12. 是否没有执行 IDA/Ghidra/static extraction/debugger/hook/emulator/winpty？
13. 是否没有读取或提交 full solve_reports / PROJECT_PROGRESS_LOG？
14. 是否没有修改 .codex-skills？
15. 是否没有提交样本二进制或本地绝对路径？
16. artifact_index 是否更新 review artifact 的 sha256/size_bytes/modified_at/source_run？
17. codex_report_summary.files_changed 是否与 git diff --name-status 一致？
18. 是否运行 JSON parse 校验？
19. 是否运行 JSON content 校验？
20. 是否运行 py_compile？
21. 是否运行 focused pytest？结果是多少？
22. 是否运行 lint-decision、lint-report、project_state status？
23. 是否运行 git diff --check、git status --short、git diff --name-status？
```

---

## 6. Implementation Scope

### Phase A — Confirm authority and narrow scope

读取默认状态文件，确认：

```text
1. 本轮 decision_packet 控制执行。
2. task_packet 只是 advisory。
3. 上一轮 bucket rework report/pytest 是可审计 SUCCESS/PASSED。
4. 返工目标仅为 capability_gaps 中一个 crypto/cipher gap 的 stale 文案。
5. 不需要也不允许新样本求解。
```

### Phase B — Clean stale gap text

修改：

```text
project_state/local_reverse_training_capability_review.json
```

仅允许修改：

```text
capability_gaps[].description
capability_gaps[].current_state
capability_gaps[].evidence_basis
updated_at / rework_decision_id / rework_round_id / cleanup metadata
```

目标 gap：

```text
gap_id=crypto_cipher_static_evidence_requirements_for_DES_RC4_samples
```

推荐新文案：

```json
{
  "gap_id": "crypto_cipher_static_evidence_requirements_for_DES_RC4_samples",
  "description": "No cipher-specific static evidence profile for DES/RC4 PE samples; Python crypto/cipher files should be treated as references, not primary binary targets.",
  "current_state": "4 crypto/cipher PE samples await static evidence profile; 2 crypto/cipher Python files are reference material.",
  "evidence_basis": "crypto_cipher_pe_inventory_only.count=4 and crypto_cipher_python_reference_inventory_only.count=2 in local_reverse_training_capability_review.json."
}
```

不得修改：

```text
status_summary
solved_cases
blocked_cases
inventory_buckets sample_ids/counts
next_queue_candidates
candidate / validation / runtime guardrails
```

如果 Codex 发现 artifact 中还有其他 stale 文案，只能报告，不得扩大修改范围，除非该文案直接引用同一个旧 crypto_cipher_inventory_only bucket。

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
source_run=round_20260608_local_reverse_capability_gap_text_cleanup_v1
sha256=<真实 sha256>
size_bytes=<真实 size>
modified_at=<实际更新时间>
```

`codex_report_summary` 必须绑定：

```text
based_on_decision_id=decision_20260608_local_reverse_capability_gap_text_cleanup_v1
round_id=round_20260608_local_reverse_capability_gap_text_cleanup_v1
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

必须追加 JSON content 校验，至少检查：

```text
1. status_summary.inventory_only == 20
2. sum(bucket.count for bucket in inventory_buckets) == 20
3. 每个 bucket.count == len(bucket.sample_ids)
4. capability_gaps 中不出现 crypto_cipher_inventory_only
5. capability_gaps 中不出现 "5-6 samples"
6. capability_gaps 中不出现 "5 crypto/cipher inventory_only samples"
7. crypto cipher gap 文案同时包含 crypto_cipher_pe_inventory_only.count=4 和 crypto_cipher_python_reference_inventory_only.count=2，或等价明确表述
8. next_queue_candidates 不包含 solved/blocked 样本
9. guardrails.runtime_validation_attempted == false
10. guardrails.ida_ghidra_static_extraction_attempted == false
```

如存在 local_reverse training/status 专项测试，必须追加运行并记录；若不存在，报告中说明未发现专项测试。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. 需要运行样本、runtime validation、console validator、debugger、hook、emulator、winpty、IDA/Ghidra/static extraction。
2. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
3. status_overlay.json 与 local_reverse_training_status.json 的 summary 不一致。
4. review artifact 的 bucket count 与 sample_ids 长度不一致。
5. inventory bucket sample_id 总数不是 20，或存在重复 sample_id。
6. capability_gaps 仍包含旧 bucket 名 crypto_cipher_inventory_only。
7. capability_gaps 仍包含 "5-6 samples" 或 "5 crypto/cipher inventory_only samples"。
8. crypto/cipher gap 仍没有区分 4 个 PE cipher 样本与 2 个 Python reference 样本。
9. next_queue_candidates 包含已 solved 或 blocked 样本，或被写成当前执行任务。
10. artifact_index 未登记 review artifact 或 freshness/source_run/sha256/size_bytes 缺失。
11. codex_report_summary 缺失或 based_on_decision_id/round_id 不匹配。
12. pytest_result 缺失或未绑定当前 decision/report/round。
13. JSON parse、JSON content 校验、lint-report、project_state status 或 focused pytest 失败。
14. git diff 包含 full solve_reports、PROJECT_PROGRESS_LOG 全量改动、.codex-skills 动态事实、样本二进制、本地绝对路径或无关代码变更。
15. 本轮修改 solver/runtime/tool 接口。
16. 本轮无必要修改 model_gate.json 或 negative_results.json，且报告没有解释为必要副作用。
```

完成后不要推进新样本求解。若本轮通过，下一轮可基于清理后的 `local_reverse_training_capability_review.json` 选择 `cpp2_f2738577` 做 **bounded static triage/readiness**；仍需单独 DECISION_PACKET 授权。
