```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_constraint_recovery_sprint_v1",
  "round_id": "round_20260603_local_reverse_constraint_recovery_sprint_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮进入一次更主动的 `local_reverse_constraint_recovery_sprint_v1`。

目标不是只做 triage，而是基于已经通过 trust gate 的 current IDA evidence，对 3 个 unresolved local reverse 样本做静态约束恢复、候选生成和 policy-bounded 验证。

只处理这 3 个样本：

```text
18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
```

本轮允许大胆推进，但必须有界：

```text
1. 对 Cpp1 做 lstrcmpA/WriteFile/realpwd/pwd 数据流恢复，解释 hookapi 为什么被 rejected，并生成新的候选。
2. 对 CPP2 做上游 transform/hash routine 恢复，尝试从 64-byte compare target 反推 post-increment 前状态，并建立可执行的约束模型。
3. 对 sha_256 做输入域发现：从 IDA strings、decompiler snippets、metadata、样本提示中提取 bounded dictionary / prefix / length 约束；不得把 SHA-256 当可逆加密。
4. 可新增通用的 local reverse constraint recovery 模块，而不是把单样本答案硬编码进 solver。
5. 可对每个样本最多生成 64 个 evidence-backed candidates，并使用现有 policy-bounded runtime verifier 验证。
```

必须输出：

```text
project_state/local_reverse_constraint_recovery_result.json
```

该结果必须包含：

```text
schema_version
stage=local_reverse_constraint_recovery_sprint_v1
status=SUCCESS|PARTIAL|BLOCKED
target_count=3
candidate_count
validated_count
targets[]: sample_id, classification, recovered_constraints, candidate_generation, candidates, validation_results, next_action
```

如果出现 validated candidate，必须有真实验证记录；如果没有 validated，也可以接受，但必须给出更具体的下一步阻塞点，不允许只写“需要更多分析”。

---

## 2. Current Evidence

当前主线：

```text
reverse_solving
```

理由：本轮围绕 3 个具体样本做约束恢复、候选生成和验证。

当前执行权威是本 `decision_packet.md`，不是 `task_packet.task`。`task_packet.json` 中的旧 `samplereverse` 字段仍是背景兼容字段；local reverse advisory 字段只作为提示。

当前可信证据入口：

```text
project_state/current_state.json -> local_reverse_training.current_ida_evidence
project_state/artifact_index.json -> latest_artifacts_v2 local_reverse_* freshness=current
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
```

上一轮 trust gate 已修复：

```text
1. local_reverse_ida_guided_solver 只使用 latest_artifacts_v2 freshness=current 的 raw IDA evidence。
2. stale/missing/unknown artifact 会 blocked。
3. filename-only 不会触发具体 profile。
4. success+failure 输出不会 validated。
5. 当前 solver result 仍为 PARTIAL, solved_count=0, validated_count=0。
```

当前 3 个样本状态：

```text
sha_256.exe:
  classification=sha256_hex_compare_with_post_hash_character_adjustment
  status=unverified
  blocker=hash target exists but no bounded preimage/input-domain evidence

CPP2.exe:
  classification=bounded_input_range_hash_output_increment_compare
  status=unverified
  blocker=visible post-transform target still depends on uninverted upstream hash/transform routine

Cpp1.exe:
  classification=api_assisted_password_write_and_compare
  candidate=hookapi
  status=rejected
  blocker=runtime output contains try again; static XOR candidate relation is incomplete or wrong
```

现有能力必须先检查并复用：

```text
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/advanced_solvers.py
reverse_agent/local_reverse_runtime.py
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
```

已有 negative_results 中禁止：旧 sample_solver 盲搜、只加 beam/budget、提交完整 solve_reports、旧 samplereverse Base64/RC4 probe 等。本轮不得重复这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不扩大到 22 个样本。
2. 不处理这 3 个样本之外的 binary。
3. 不复制、上传、提交、base64/hex 编码 E:\reverse 下的样本二进制。
4. 不提交完整 solve_reports/。
5. 不读取完整 solve_reports/。
6. 不读取完整 PROJECT_PROGRESS_LOG.txt。
7. 不修改 .codex-skills/。
8. 不回旧 sample_solver 盲搜。
9. 不做无界 brute force。
10. 不只通过增加 beam/topN/budget/timeout 推进。
11. 不把 SHA-256/hash 当作可逆解密。
12. 不用 filename-only / relative_path-only 触发分类或候选。
13. 不把 Correct!/Wrong!/realpwd/pwd 字符串直接当答案，除非有数据流证据和验证。
14. 不伪造 validated。
15. 不把单样本常量硬编码进长期 solver。
16. 不引入数据库、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
17. 不新建动态调试器或 hook 框架。
18. 不运行 OllyDbg/x64dbg/Frida/debugger。
```

默认不重新运行 IDA/Ghidra。若 raw IDA JSON 中缺少必要 decompiler snippet，本轮只允许 `BLOCKED_NEEDS_TARGETED_STATIC_REEXTRACTION`，不要擅自重跑工具。下一轮再申请 targeted static re-extraction。

允许：

```text
1. 有界读取 project_state/local_reverse_ida_summary.json。
2. 有界读取 artifact_index/current_state 指向的 3 个 raw IDA JSON。
3. 新增 reverse_agent/local_reverse_constraint_recovery.py 或等价小模块。
4. 扩展 reverse_agent/local_reverse_ida_guided_solver.py，但不得破坏 trust gate。
5. 新增 tests/test_local_reverse_constraint_recovery.py。
6. 每个样本最多生成 64 个 evidence-backed candidate。
7. 使用 reverse_agent/local_reverse_runtime.py 的现有 run_probe 做 policy-bounded candidate validation。
8. runtime validation 总次数最多 192 次，单样本最多 64 次，timeout 必须遵守 local_reverse_runtime_policy.json。
9. 将验证 transcript 摘要写入 result JSON，但不得提交二进制或大体积 runtime 输出。
10. 更新 artifact_index/current_state/task_packet 的 local_reverse advisory 字段。
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
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
project_state/local_reverse_runtime_policy.json
project_state/local_reverse_corpus_index.json
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/advanced_solvers.py
reverse_agent/local_reverse_runtime.py
reverse_agent/tool_runners.py
```

有界读取，仅限 artifact_index/current_state 指向的 3 个 raw IDA JSON：

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\bcbd9979db015bfd\Cpp1_ida_evidence.json
```

必要时读取：

```text
tests/test_local_reverse_ida_guided_solver.py
tests/test_local_reverse_string_solver.py
tests/test_local_reverse_ida_summary.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ 全目录
PROJECT_PROGRESS_LOG.txt
```

---

## 5. Required Audit

Codex 必须在 `project_state/codex_execution_report.md` 中写明：

```text
1. 当前 decision_packet 是执行权威。
2. 本轮 mainline=reverse_solving。
3. task_packet.task 和旧 samplereverse 字段只是背景。
4. 使用了哪些 current local_reverse artifacts，列出 artifact keys 和 freshness。
5. 是否读取了 3 个 raw IDA JSON，列出具体路径。
6. 是否新增模块；如果新增，说明为什么 local_reverse_ida_guided_solver 不足以表达约束恢复。
7. Cpp1 的 lstrcmpA/WriteFile/realpwd/pwd 数据流恢复结果。
8. CPP2 的 transform/hash routine 恢复结果。
9. sha_256 的输入域/字典/长度/prefix 约束发现结果。
10. 每个样本生成了多少 candidates，候选来源是什么。
11. 每个样本验证了多少 candidates，validated/rejected/unverified 数量是多少。
12. 若出现 validated candidate，给出真实 stdout/stderr/returncode/timeout 摘要。
13. 未扩大样本。
14. 未复制、提交、上传或编码样本二进制。
15. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
16. 未修改 .codex-skills/。
17. 未重跑 IDA/Ghidra/debugger；如果没有重跑，明确说明。
18. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_constraint_recovery_sprint_v1",
  "round_id": "round_20260603_local_reverse_constraint_recovery_sprint_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_constraint_recovery_sprint_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 新增约束恢复模块

推荐新增：

```text
reverse_agent/local_reverse_constraint_recovery.py
```

CLI：

```bash
python -m reverse_agent.local_reverse_constraint_recovery --ida-summary project_state\local_reverse_ida_summary.json --artifact-index project_state\artifact_index.json --solver-result project_state\local_reverse_ida_solver_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_constraint_recovery_result.json
```

模块职责：

```text
1. 复用 local_reverse_ida_guided_solver 的 trust gate 或等价 current artifact resolver。
2. 读取 3 个 raw IDA JSON。
3. 对每个样本恢复约束。
4. 生成 evidence-backed candidates。
5. 调用现有 run_probe 验证 candidates。
6. 输出结构化 result JSON。
```

不得复制粘贴一套新的 artifact trust gate；优先从 `local_reverse_ida_guided_solver.py` 导出可复用 resolver，或 thin import。

### 6.2 Cpp1 aggressive path

目标：解释 `hookapi` 为什么 rejected，并尝试恢复真实输入关系。

必须从 IDA evidence 提取：

```text
1. lstrcmpA 调用点上下文。
2. realpwd/pwd 字符串 xrefs。
3. WriteFile/GetProcAddress 相关 decompiler snippets。
4. Str[i] 常量数组。
5. Buffer / file content / user input 的数据流关系。
6. success/failure branch 的输出字符串附近上下文。
```

允许生成候选策略：

```text
1. XOR constants against realpwd。
2. XOR constants against pwd-like strings。
3. Reverse XOR direction variants。
4. Include/exclude trailing null/newline variants。
5. Candidate with file side-effect hypothesis: if program writes transformed input to file then compares file buffer, test direct and transformed candidates separately。
6. Try exact case variants only when evidence contains case-insensitive or ASCII transform hints。
```

每个 Cpp1 候选必须记录：

```text
candidate
source_relation
constants_used
string_target
transform_formula
why_bounded
validation_status
```

上限：64 candidates。

### 6.3 CPP2 aggressive path

目标：恢复上游 transform routine，不再停留在“upstream hash/transform remains uninverted”。

必须从 IDA evidence 提取：

```text
1. input range check: Source[i] < 65 || Source[i] > 122。
2. post-transform ++Str1 的确切位置和长度。
3. 64-byte compare target。
4. subroutine call graph / validation_function_candidates。
5. 与 sprintf/%08x 或 hash-like routine 相关的 snippets。
```

允许建模：

```text
1. target_before_increment = target_after_compare - 1 per byte。
2. 如果存在 hex-like digest routine，只做 bounded dictionary/domain 验证，不做无界 preimage。
3. 如果 evidence 显示逐字符 affine/add/xor/shift/rot，则实现可逆变换。
4. 如果 transform routine 不可恢复，输出 exact missing function/snippet name，不要泛泛写 blocked。
```

候选生成上限：64。只允许来源于明确约束：已知 input range、target_before_increment、可逆 transform、dictionary/domain hints。

### 6.4 sha_256 aggressive path

目标：找输入域，不做无界 SHA preimage。

必须从 IDA evidence 提取：

```text
1. 64-byte hash target。
2. sprintf("%08x" * 8) context。
3. 输入 length 限制。
4. prompt strings / success strings / failure strings / copied Source prefix。
5. metadata/case notes 中可能存在的 expected prefix 或 training hint。
```

允许生成候选策略：

```text
1. strings-derived dictionary。
2. prompt-derived dictionary。
3. known small training tokens: password/test/flag/admin/reverse/sha256 等，但必须标记为 heuristic_dictionary，不超过 32 个。
4. prefix+small suffix 只允许 suffix 空间 <= 256。
5. 不允许全量 brute force。
```

如果没有 bounded input domain，必须输出：

```text
blocked_reason=NO_BOUNDED_HASH_PREIMAGE_DOMAIN
next_action=targeted static re-extraction of input length/domain or request problem statement hint
```

### 6.5 输出格式

`project_state/local_reverse_constraint_recovery_result.json` 必须包含：

```json
{
  "schema_version": 1,
  "stage": "local_reverse_constraint_recovery_sprint_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "source_solver_result": "project_state\\local_reverse_ida_solver_result.json",
  "target_count": 3,
  "candidate_count": 0,
  "validated_count": 0,
  "targets": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "constraint_status": "recovered|partial|blocked",
      "recovered_constraints": [],
      "candidate_generation": {
        "strategy": "...",
        "count": 0,
        "bounded_reason": "..."
      },
      "candidates": [],
      "validation_results": [],
      "validated_candidate": "",
      "blocked_reason": "",
      "next_action": "..."
    }
  ]
}
```

若产生 validated candidate，可同时更新：

```text
project_state/current_state.json local_reverse_training latest_validated_candidates
project_state/artifact_index.json local_reverse_constraint_recovery_result
project_state/task_packet.json local_reverse_next_suggested_task
```

---

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_constraint_recovery.py
```

必须新增测试：

```text
tests/test_local_reverse_constraint_recovery.py
```

测试至少覆盖：

```text
1. Cpp1 XOR relation variants generate hookapi and at least one alternate candidate, but rejected candidate does not become validated。
2. CPP2 target_before_increment 正确逐字节 -1。
3. sha_256 无 bounded input domain 时不生成无界 preimage candidate。
4. candidate generation 单样本不超过 64。
5. runtime validation 同时出现 Correct 和 try again 时判 rejected。
6. stale artifact 通过 trust gate 后 blocked，不读取 legacy latest_artifacts。
7. output JSON target_count=3 且每个 target 有 constraint_status 和 next_action。
```

必须运行 CLI：

```bash
python -m reverse_agent.local_reverse_constraint_recovery --ida-summary project_state\local_reverse_ida_summary.json --artifact-index project_state\artifact_index.json --solver-result project_state\local_reverse_ida_solver_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_constraint_recovery_result.json
```

必须校验：

```bash
python -m json.tool project_state\local_reverse_constraint_recovery_result.json > NUL
python -c "import json; d=json.load(open('project_state/local_reverse_constraint_recovery_result.json', encoding='utf-8')); assert d['target_count']==3; assert len(d['targets'])==3; assert all(t.get('constraint_status') for t in d['targets']); assert all(t.get('next_action') for t in d['targets'])"
```

必须运行相关回归：

```bash
python -m pytest -q tests\test_local_reverse_constraint_recovery.py tests\test_local_reverse_ida_guided_solver.py tests\test_local_reverse_string_solver.py tests\test_local_reverse_ida_summary.py tests\test_project_state.py
```

最后运行：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

若修改公共 runtime/verifier，再运行全量：

```bash
python -m pytest -q
```

测试结果必须写入：

```text
project_state/pytest_result.txt
```

---

## 8. Stop Conditions

出现以下任一情况立即停止并报告：

```text
1. current local_reverse IDA evidence 缺失或 freshness 不是 current。
2. raw IDA JSON 无法解析。
3. 需要读取完整 solve_reports/ 才能继续。
4. 需要读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
5. 需要扩大到 3 个样本之外才能继续。
6. 需要无界 brute force 才能继续。
7. 需要重新运行 IDA/Ghidra/debugger 才能继续。
8. 需要复制、提交、上传或编码样本二进制才能继续。
9. candidate 超过单样本 64 个或总数超过 192 个。
10. validation 输出不明确；此时必须标记 unverified/rejected，不得 validated。
```

本轮完成标准：

```text
project_state/local_reverse_constraint_recovery_result.json 已生成；
3 个样本都有具体 recovered_constraints 或精确 blocked_reason；
Cpp1 必须解释 hookapi rejected 的可能数据流原因，并尝试至少一种 evidence-backed alternate candidate；
CPP2 必须至少恢复 target_before_increment 或指出缺失的具体 upstream function/snippet；
sha_256 必须明确输入域是否存在，且不得无界 hash preimage；
若 validated_count > 0，必须有真实 runtime transcript 摘要；
没有扩大样本、没有重跑 IDA/Ghidra/debugger、没有提交二进制。
```
