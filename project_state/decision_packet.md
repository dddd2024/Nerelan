```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_local_reverse_training_capability_review_v1",
  "round_id": "round_20260608_local_reverse_training_capability_review_v1",
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

目标：对 `local_reverse` 训练集做一次 **metadata-only 能力复盘**，把已 solved / blocked / inventory_only 样本按题型、证据链、验证方式、失败原因和可复用 solver/profile 缺口结构化，生成下一步队列建议。不得在本轮执行新样本求解。

本轮必须产出：

```text
project_state/local_reverse_training_capability_review.json
```

该 artifact 必须回答：

```text
1. 当前训练集规模与状态分布：sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20。
2. 5 个 solved 样本分别靠什么证据链和验证方式完成。
3. 4 个 blocked 样本的阻塞原因是否属于：缺少题面/密文、无有界输入域、缺少上游 transform、无完整 printable preimage。
4. inventory_only 样本按 category/tags/extension 分桶，优先识别 cpp/pe 与 crypto/cipher 样本。
5. 当前项目已有能力：inventory/status/overlay、artifact_index、console validator、runtime validation artifact、IDA/Ghidra/static evidence artifact、solver profile dispatch/guardrail artifact、project_state build/status/lint。
6. 当前能力缺口：bounded static triage queue、solver/profile 分类、evidence_sources 到 StructuredEvidence 的映射、blocked reason 到下一动作的规则化、crypto/hash 输入域恢复、cipher/RC4/DES 样本的静态证据需求。
7. 下一轮 advisory queue，只能给出候选与理由，不得执行。
```

本轮不得生成 candidate，不得运行样本，不得 runtime validation，不得 attach debugger/hook/emulator/winpty，不得执行 IDA/Ghidra/radare2/objdump，不得读取或提交完整 `solve_reports/`。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`task_packet.json` 仍是 advisory，且当前 `task_packet/current_state` 是 `samplereverse` sample_state 包；不能把其中的 `derived_task=Review bounded window discovery diagnostics` 当成本轮任务。

上一轮审计结论为 **ACCEPTED_WITH_LIMITATIONS**：

```text
1. decision/report/pytest 对齐，上一轮可接受。
2. training status truth source 已确认为 local_reverse_training_status.json 与 status_overlay.json。
3. task_packet/current_state 中 stale local_reverse_training_summary 与 stale cpp2_883e67b9 next_queue_hint 已被 build 移除。
4. 限制项：上一轮 files_changed 包含 project_state/model_gate.json 与 project_state/negative_results.json，属于 build 副作用边界；本轮不返工，但必须避免继续无必要修改这些文件。
```

当前训练集事实：

```text
1. training_materials/local_reverse/status_overlay.json:
   sample_count=29
   solved=5
   blocked=4
   needs_triage=0
   inventory_only=20

2. project_state/local_reverse_training_status.json:
   sample_count=29
   solved=5
   blocked=4
   needs_triage=0
   inventory_only=20
```

已 solved 样本线索：

```text
cpp1_7b504c54:
  known_candidate=WeKnowItOk
  classification=console_runtime_validation
  evidence_sources includes source:local_reverse_cpp1_7b504c54_runtime_validation.json

cpp1_bcbd9979:
  known_candidate=hookapi
  evidence_sources include ida_solver_classification, runtime_validation, local_reverse_validated_candidate_handoff, local_reverse_constraint_recovery_result

cpp2_2f64e68d:
  known_candidate=10013
  classification=oracle_backed_runtime_validated
  evidence_sources include console mature backend, winpty lifecycle hardening, post strcmp oracle extraction, raw input candidate, oracle-backed runtime validation

cpp2_32f1713e:
  known_candidate=KEEP_DREAM
  classification=oracle_backed_runtime_validated
  evidence_sources include targeted_static_solving, keep_dream_runtime_validation, runtime_validation, positive/negative controls

cpp2_883e67b9:
  known_candidate=KaiJu_YiZhi_PEN
  classification=console_runtime_validation
  evidence_sources include source:local_reverse_cpp2_883e67b9_candidate_validation.json, console_runtime_validation, runtime_validated_success
```

Blocked 样本线索：

```text
affine_8cfebe03:
  blocked_reason=MISSING_EXPECTED_CIPHERTEXT
  next_action=Provide expected ciphertext from challenge statement or another allowed evidence source before candidate generation.

cpp1_2f6fcb63:
  blocked_reason=CURRENT_TARGET_CONFIRMED_NO_COMPLETE_PRINTABLE_PREIMAGE
  classification=target byte provenance recheck confirmed_no_printable_preimage

cpp2_4c69f173:
  blocked_reason=MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005
  classification=bounded_input_range_hash_output_increment_compare
  next_action=recover sub_401005 transform or bounded dictionary before inversion

sha_256_18019fca:
  blocked_reason=NO_BOUNDED_HASH_PREIMAGE_DOMAIN
  classification=sha256_hex_compare_with_post_hash_character_adjustment
  next_action=targeted static re-extraction of input length/domain or request problem statement hint
```

Inventory-only 优先线索：

```text
cpp2_f2738577: category=cpp, extension=.exe, guessed_file_type=pe, next_action=static triage and manual evaluation required
cpp2_fc735338: category=cpp, extension=.exe, guessed_file_type=pe, next_action=static triage and manual evaluation required
cpp3_019fcdc8: category=cpp, extension=.exe, guessed_file_type=pe, next_action=static triage and manual evaluation required
cpp3_e5a33e0b: category=cpp, extension=.exe, guessed_file_type=pe, next_action=static triage and manual evaluation required
cpp4_ab1b6104 / cpp5_2ea076a7 / cpp_6af7c7f1: category=cpp, extension=.exe, guessed_file_type=pe
rc4enc_3480917d / desenc_*: category=crypto/cipher, extension=.exe, guessed_file_type=pe
byte_shift_transform_solver_3718a6fa / xor_array_solver_4e6d25f0: python solver-like artifacts, not immediate binary solving targets
```

`negative_results.json` 仍必须遵守：不回到 old sample_solver blind search，不只扩大 beam/budget，不提交 full solve_reports，不把 stale/missing artifact 当 current，不重复已失败方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

已有工具/接口边界：

```text
1. 现有 project_state build/status/lint 能力优先使用。
2. 现有 local_reverse inventory/status/overlay 能力优先使用。
3. 现有 console/runtime validation artifacts 只能作为历史证据引用，不能重新运行。
4. 现有 IDA/Ghidra/static evidence artifacts 只能作为 artifact_index/status 中的 metadata 线索，不能执行工具。
5. 若源码中已有 solver profile dispatch / guardrail / training status helper，不得新建平行系统。
6. 不允许新增 IDA/Ghidra/debugger/runtime/solver 接口。
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
17. 不要继续无必要修改 project_state/model_gate.json 或 project_state/negative_results.json。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 training_materials/local_reverse/status_overlay.json。
3. 读取 project_state/local_reverse_training_status.json。
4. 读取 project_state/local_reverse_inventory.json 和 training_materials/local_reverse/inventory.json，只用于 metadata 分桶。
5. 读取 training_materials/local_reverse/README.md，确认 metadata-only policy。
6. 读取 project_state/local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.json。
7. 读取 artifact_index 中 current/stale/missing metadata，不读取 heavy artifact 内容。
8. 有界读取与 training/status/profile dispatch 相关源码和测试。
9. 生成 project_state/local_reverse_training_capability_review.json。
10. 更新 artifact_index、codex_execution_report.md、pytest_result.txt。
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
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_training_status.json
project_state/local_reverse_state_freshness_rebuild_after_cpp2_883e67b9.json
training_materials/local_reverse/README.md
```

建议有界读取：

```text
project_state/local_reverse_inventory.json
training_materials/local_reverse/inventory.json
reverse_agent/project_state.py
reverse_agent/local_reverse_training.py
reverse_agent/local_reverse_training_status.py
reverse_agent/sample_metadata.py
与 solver profile dispatch / guardrail 直接相关的源码或测试（先搜索文件名或符号，不要盲读全仓库）
tests/test_project_state.py
local_reverse / training_status 相关测试文件（如存在）
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
4. 上一轮 ACCEPTED_WITH_LIMITATIONS 的限制项是否被识别：model_gate/negative_results build 副作用不继续扩大？
5. status_overlay 与 local_reverse_training_status 是否一致：sample_count=29、solved=5、blocked=4、needs_triage=0、inventory_only=20？
6. 是否没有生成 candidate、没有运行样本、没有 runtime validation？
7. 是否没有执行 IDA/Ghidra/static extraction/debugger/hook/emulator/winpty？
8. 是否没有读取或提交 full solve_reports / PROJECT_PROGRESS_LOG？
9. 是否没有修改 .codex-skills？
10. 是否没有提交样本二进制或本地绝对路径？
11. local_reverse_training_capability_review.json 是否包含 solved_cases、blocked_cases、inventory_buckets、capability_gaps、next_queue_candidates？
12. solved_cases 是否逐项列出 evidence_sources、validation_class、candidate_known、reusability_notes？
13. blocked_cases 是否逐项列出 blocked_reason、required_missing_evidence、next_allowed_action、not_to_retry？
14. inventory_buckets 是否至少按 cpp/pe、crypto/cipher、python solver-like、unknown/pe 分桶？
15. capability_gaps 是否从现有状态推导，不编造未见证据？
16. next_queue_candidates 是否只给 advisory，不授权执行；是否排除已 solved/blocked 样本，优先 inventory_only 样本？
17. artifact_index 是否登记 review artifact，freshness=current，source_run=round_20260608_local_reverse_training_capability_review_v1？
18. codex_report_summary.files_changed 是否与 git diff --name-status 一致？
19. 是否运行 JSON parse 校验？
20. 是否运行 py_compile？
21. 是否运行 focused pytest？结果是多少？
22. 是否运行 lint-decision、lint-report、project_state status？
23. 是否运行 git diff --check、git status --short、git diff --name-status？
```

---

## 6. Implementation Scope

### Phase A — Authority and source consistency

读取默认状态文件，确认：

```text
1. 本轮以 decision_packet 为唯一执行权威。
2. task_packet/current_state 的 samplereverse 内容不得作为本轮任务。
3. training status truth source 是 status_overlay.json 与 local_reverse_training_status.json。
4. 二者状态摘要一致。
5. 上一轮 report/pytest 已通过，但有 ACCEPTED_WITH_LIMITATIONS 范围限制。
```

### Phase B — Build capability review artifact

生成：

```text
project_state/local_reverse_training_capability_review.json
```

最低字段要求：

```json
{
  "schema_version": 1,
  "mainline": "training_dataset",
  "artifact_kind": "local_reverse_training_capability_review",
  "decision_id": "decision_20260608_local_reverse_training_capability_review_v1",
  "round_id": "round_20260608_local_reverse_training_capability_review_v1",
  "source_files": [],
  "status_summary": {
    "sample_count": 29,
    "solved": 5,
    "blocked": 4,
    "needs_triage": 0,
    "inventory_only": 20
  },
  "solved_cases": [],
  "blocked_cases": [],
  "inventory_buckets": [],
  "capability_gaps": [],
  "next_queue_candidates": [],
  "guardrails": {
    "candidate_generated": false,
    "runtime_validation_attempted": false,
    "ida_ghidra_static_extraction_attempted": false,
    "debugger_attached": false,
    "emulator_used": false,
    "full_solve_reports_read": false
  }
}
```

`solved_cases` 每项至少包含：

```text
sample_id
relative_path
category
guessed_file_type / extension（如可从 training_status 得到）
known_candidate_present=true/false，不要把 candidate 写入 capability gap 或 skill
classification / solved_by / validation_class
evidence_sources
reusable_pattern，例如 console_runtime_validation、oracle_backed_runtime_validated、ida_static_plus_runtime、targeted_static_solving_plus_runtime
reusability_notes
```

`blocked_cases` 每项至少包含：

```text
sample_id
relative_path
category
blocked_reason
classification
observed_evidence_sources
required_missing_evidence
next_allowed_action
not_to_retry
```

`inventory_buckets` 至少包含：

```text
cpp_pe_inventory_only
crypto_cipher_inventory_only
python_solver_like_inventory_only
unknown_pe_inventory_only
other_inventory_only
```

`capability_gaps` 必须从现有状态推导，建议包括：

```text
1. bounded_static_triage_profile_for_inventory_cpp_pe
2. solver_profile_dispatch_from_training_status_and_artifact_index
3. blocked_reason_to_next_action_rules
4. hash_preimage_domain_recovery_or_problem_statement_hint_gate
5. upstream_transform_recovery_gate_for_cpp2_4c69f173
6. expected_ciphertext_provenance_gate_for_affine
7. printable_preimage_vs_nonprintable_input_policy_for_cpp1_2f6fcb63
8. crypto_cipher_static_evidence_requirements_for_DES_RC4_samples
```

`next_queue_candidates` 只允许 advisory，建议优先：

```text
1. cpp2_f2738577 — cpp/pe inventory_only，接近已有 CPP2 成功模式；下一轮只可做 bounded static triage/readiness。
2. cpp2_fc735338 — cpp/pe inventory_only，可作为第二 CPP2 queue。
3. cpp3_019fcdc8 或 cpp3_e5a33e0b — cpp/pe inventory_only，适合在 CPP2 后扩展到 CPP3。
4. rc4enc_3480917d 或 desenc_* — crypto/cipher inventory_only，只有在已有 cipher static evidence profile 可用后再排队。
```

不得把任何 advisory candidate 写成当前执行任务。

### Phase C — Artifact index and reports

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 需要新增或更新：

```text
latest_artifacts.local_reverse_training_capability_review = project_state\local_reverse_training_capability_review.json
latest_artifacts_v2.local_reverse_training_capability_review.kind = local_reverse_training_capability_review
latest_artifacts_v2.local_reverse_training_capability_review.path = project_state\local_reverse_training_capability_review.json
latest_artifacts_v2.local_reverse_training_capability_review.freshness = current
latest_artifacts_v2.local_reverse_training_capability_review.source_run = round_20260608_local_reverse_training_capability_review_v1
latest_artifacts_v2.local_reverse_training_capability_review.sha256 = <真实 sha256>
latest_artifacts_v2.local_reverse_training_capability_review.size_bytes = <真实 size>
latest_artifacts_v2.local_reverse_training_capability_review.modified_at = <实际更新时间>
```

报告 summary 必须包含：

```text
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

如果存在 local reverse training/status 专项测试，必须追加运行并记录实际命令。若不存在，报告中明确写明未发现专项测试。

建议增加一个 JSON 内容校验 one-liner，至少检查：

```text
1. status_summary.solved == 5
2. len(solved_cases) == 5
3. len(blocked_cases) == 4
4. next_queue_candidates 不包含 training_status=solved 或 blocked 的样本
5. guardrails.runtime_validation_attempted == false
6. guardrails.ida_ghidra_static_extraction_attempted == false
```

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. 需要运行样本、runtime validation、console validator、debugger、hook、emulator、winpty、IDA/Ghidra/static extraction。
2. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
3. status_overlay.json 与 local_reverse_training_status.json 的 summary 不一致。
4. 无法从 metadata 得到 solved=5 / blocked=4 / inventory_only=20 的一致状态。
5. review artifact 把 advisory queue 写成当前执行任务。
6. next_queue_candidates 包含已 solved 或 blocked 样本。
7. review artifact 编造未在 metadata 中出现的证据或声称 stale/missing artifact 为 current。
8. artifact_index 未登记 review artifact 或 freshness/source_run/sha256/size_bytes 缺失。
9. codex_report_summary 缺失或 based_on_decision_id/round_id 不匹配。
10. pytest_result 缺失或未绑定当前 decision/report/round。
11. JSON parse、lint-report、project_state status 或 focused pytest 失败。
12. git diff 包含 full solve_reports、PROJECT_PROGRESS_LOG 全量改动、.codex-skills 动态事实、样本二进制、本地绝对路径或无关代码变更。
13. 本轮修改了 solver/runtime/tool 接口。
14. 本轮继续无必要修改 model_gate.json 或 negative_results.json，且报告没有解释为 build/lint 必要副作用。
```

完成后不要推进新样本求解。若本轮通过，下一轮可基于 `local_reverse_training_capability_review.json` 选择一个 inventory_only 样本做 **bounded static triage/readiness**，优先考虑 `cpp2_f2738577`，但仍需单独 DECISION_PACKET 授权。
