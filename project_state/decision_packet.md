```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_ida_summary_guided_solver_v1",
  "round_id": "round_20260603_ida_summary_guided_solver_v1",
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

本轮目标是基于当前已经登记为 current 的 local reverse IDA evidence，对 3 个样本执行有界的 `ida_summary_guided_solver_v1`。

只处理以下 3 个样本：

```text
18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
```

必须输出：

```text
project_state/local_reverse_ida_solver_result.json
```

该结果必须至少包含：

```text
1. 每个样本的 IDA evidence provenance。
2. 每个样本的题型分类。
3. 选择的 solver profile。
4. 候选 candidate；若无候选，必须给出 bounded failure reason。
5. 验证状态：validated / rejected / unverified / blocked。
6. 是否需要下一轮动态验证或人工补充输入约束。
```

本轮可以做有界求解，但不能把一次样本结论硬编码成长期 solver 逻辑。若需要新增 solver 能力，必须以通用 profile / extractor / verifier 的形式实现，并覆盖测试。

---

## 2. Current Evidence

当前主线：

```text
reverse_solving
```

理由：本轮进入 3 个具体样本的有界求解与验证，不再只是 project_state 登记。

当前执行权威是本 `decision_packet.md`，不是 `task_packet.task`。

`task_packet.json` 中旧 `samplereverse` 字段仍只能作为背景兼容字段；当前 local reverse 证据必须来自：

```text
project_state/current_state.json -> local_reverse_training.current_ida_evidence
project_state/artifact_index.json -> local_reverse_ida_summary / local_reverse_ida_evidence_*
project_state/local_reverse_ida_summary.json
```

上一轮返工已确认：

```text
local_reverse_training.current_ida_evidence 存在
current_ida_evidence 长度为 3
三个条目 ida_status=success
state_refresh_round=round_20260603_local_reverse_current_state_rework_v1
```

`artifact_index.json` 中当前 local reverse artifact keys：

```text
local_reverse_ida_summary
local_reverse_ida_evidence_18019fca52b389fe
local_reverse_ida_evidence_4c69f173f2bd0211
local_reverse_ida_evidence_bcbd9979db015bfd
```

已有相关能力必须先检查并复用：

```text
reverse_agent/local_reverse_string_solver.py
reverse_agent/advanced_solvers.py
reverse_agent/sample_solver.py
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
```

规则：

```text
1. 成熟工具优先：已有 IDA evidence 已足够作为静态证据，本轮不要重跑 IDA/Ghidra/debugger。
2. 现有 solver 能力优先复用，禁止直接回旧 sample_solver 盲搜。
3. 旧 negative_results 中的 old sample_solver blind search、仅扩 beam/budget、旧 samplereverse Base64/RC4 probes 不得重复。
4. 若现有 solver 不适合，允许新增最小的 IDA-summary-guided solver profile，但必须通用、可测试、可审计。
```

当前 3 个样本的初步题型线索只能作为假设，必须由 raw IDA evidence 复核：

```text
18019fca52b389fe / sha_256.exe: 疑似 SHA-256/hash hex compare，不允许声称哈希可逆。
4c69f173f2bd0211 / CPP2.exe: 疑似字符范围约束 + 字符变换/移位/字符串比较。
bcbd9979db015bfd / Cpp1.exe: 疑似 realpwd/pwd/API 辅助密码校验。
```

---

## 3. Do Not Do

严禁：

```text
1. 不扩大到 22 个样本。
2. 不处理这 3 个样本之外的 binary。
3. 不复制、上传、提交、base64/hex 编码 E:\reverse 下的样本二进制。
4. 不重新运行 IDA。
5. 不运行 Ghidra，除非本轮明确 BLOCKED 后下一轮再申请。
6. 不运行 OllyDbg/x64dbg/Frida/dynamic probe/debugger。
7. 不读取完整 solve_reports/。
8. 不读取完整 PROJECT_PROGRESS_LOG.txt。
9. 不修改 .codex-skills/。
10. 不把旧 samplereverse 字段当 current evidence。
11. 不回旧 sample_solver 盲搜。
12. 不做无界 brute force。
13. 不用“增加 beam/topN/budget/timeout”代替证据驱动求解。
14. 不把 hash preimage 当作可逆解密。
15. 不把 IDA 字符串中的 Correct!/Wrong!/realpwd 等提示直接当答案，除非有数据流/比较证据支持并经过验证。
16. 不把单样本常量硬编码进长期 solver 模块。
17. 不把 runtime-specific local path 写进 .codex-skills/。
18. 不引入数据库、消息队列、Redis、Celery、Kubernetes、Airflow、Temporal、LangGraph。
```

允许：

```text
1. 有界读取 project_state/local_reverse_ida_summary.json。
2. 有界读取 artifact_index 中登记的 3 个 raw IDA evidence JSON。
3. 检查现有 solver 模块并复用。
4. 新增或扩展一个最小的 IDA-summary-guided solver/orchestrator，如果现有模块无法表达当前证据流。
5. 对候选进行有界验证；验证必须遵守 local_reverse_runtime_policy.json。
6. 写入 project_state/local_reverse_ida_solver_result.json。
7. 必要时更新 artifact_index/current_state/task_packet 的 local_reverse advisory 字段。
8. 更新 codex_execution_report.md 和 pytest_result.txt。
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
project_state/local_reverse_runtime_policy.json
project_state/local_reverse_corpus_index.json
project_state/local_reverse_semantic_rule_result.json
reverse_agent/local_reverse_string_solver.py
reverse_agent/advanced_solvers.py
reverse_agent/sample_solver.py
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
```

有界读取，仅限 artifact_index/current_state 指向的 3 个 raw IDA JSON：

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\bcbd9979db015bfd\Cpp1_ida_evidence.json
```

必要时读取：

```text
tests/test_local_reverse_string_solver.py
tests/test_local_reverse_ida_summary.py
tests/test_tool_runners.py
tests/test_project_state.py
README.txt
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
3. task_packet.task 是建议/背景，不是执行权威。
4. current_state 中旧 samplereverse 字段仅为背景兼容字段。
5. 当前证据入口是 local_reverse_training.current_ida_evidence + artifact_index local_reverse_*。
6. 是否读取了 3 个 raw IDA JSON；如果读取，列出具体路径。
7. 是否复用现有 solver 模块；如果新增模块，说明为什么现有模块不足。
8. 每个样本的题型分类和证据来源。
9. 每个样本选择的 solver profile。
10. 每个样本的 candidate / no-candidate reason。
11. 每个 candidate 的验证方式和验证结果。
12. 未重新运行 IDA/Ghidra/debugger/dynamic probe。
13. 未扩大样本。
14. 未复制、提交、上传或编码样本二进制。
15. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
16. 未修改 .codex-skills/。
17. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_ida_summary_guided_solver_v1",
  "round_id": "round_20260603_ida_summary_guided_solver_v1",
  "based_on_decision_id": "decision_20260603_ida_summary_guided_solver_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 先做证据驱动 triage，不先写大 solver

对每个样本从 raw IDA JSON 提取：

```text
1. strings_summary / strings
2. compare_contexts / compare_contexts_summary
3. local_check_contexts / local_check_contexts_summary
4. string_xrefs / string_xrefs_summary
5. validation_function_candidates
6. decompiler_snippets
7. solver_hints
```

输出 per-sample triage：

```text
sample_id
relative_path
classification
classification_evidence
candidate_sources
selected_solver_profile
verification_plan
risk_or_blocker
```

### 6.2 Solver profile 选择规则

至少支持这些 profile 名称；没有证据时不要硬套：

```text
hash_hex_compare_static
bounded_char_transform_inversion
direct_or_api_password_extraction
string_compare_direct
needs_more_static_evidence
```

建议映射：

```text
1. sha_256.exe：若证据确认 sprintf("%08x" * 8) + strncmp 64 hex，则选 hash_hex_compare_static。
   - 不尝试无界 preimage。
   - 只允许从 evidence 中已有明文候选、训练题 metadata、明显常量、或小而明确的输入域中验证。
   - 若无输入域，输出 unverified/blocked，并说明需要动态或题目域约束。

2. CPP2.exe：若证据确认输入范围 65..122 且存在可逆的逐字符变换/移位/XOR/加减，则选 bounded_char_transform_inversion。
   - 只实现从 decompiler/IDA evidence 可见的变换。
   - 不猜测未知变换。
   - 反解 candidate 后必须验证。

3. Cpp1.exe：若证据确认 realpwd/pwd 或 API 写出/读取密码路径，则选 direct_or_api_password_extraction。
   - 追踪 realpwd/pwd xrefs、validation candidates、decompiler snippets。
   - 只有能证明比较关系时才输出 candidate。
```

### 6.3 复用/新增代码边界

优先复用：

```text
reverse_agent/local_reverse_string_solver.py
reverse_agent/advanced_solvers.py
```

禁止把本轮变成旧 `sample_solver.py` 盲搜。可以检查 `sample_solver.py` 以了解旧失败方向，但不得直接把它作为 primary path。

如果必须新增，推荐新增最小模块：

```text
reverse_agent/local_reverse_ida_guided_solver.py
```

该模块应提供 CLI：

```bash
python -m reverse_agent.local_reverse_ida_guided_solver --ida-summary project_state\local_reverse_ida_summary.json --artifact-index project_state\artifact_index.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_ida_solver_result.json
```

模块职责：

```text
1. 读取已登记 IDA summary 和 raw JSON。
2. 分类样本。
3. 选择 solver profile。
4. 生成 candidate 或 blocked reason。
5. 调用有界验证入口，或在无法安全验证时标为 unverified/blocked。
6. 输出结构化 JSON。
```

### 6.4 验证边界

候选验证必须：

```text
1. 只对这 3 个样本。
2. 遵守 project_state/local_reverse_runtime_policy.json。
3. 使用已有 harness/tool runner；不要新建动态调试器。
4. timeout 不超过 policy max_timeout_seconds。
5. 记录 stdout/stderr/returncode/timeout，但不要提交 binary。
```

如果当前项目没有安全的 local_reverse candidate verifier，允许本轮只输出 `unverified`，同时生成明确的下一轮 verifier 接入 decision 建议；不要伪造 validated。

### 6.5 输出格式

`project_state/local_reverse_ida_solver_result.json` 必须包含：

```json
{
  "schema_version": 1,
  "stage": "ida_summary_guided_solver_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "source_summary": "project_state\\local_reverse_ida_summary.json",
  "target_count": 3,
  "solved_count": 0,
  "validated_count": 0,
  "targets": [
    {
      "sample_id": "...",
      "relative_path": "...",
      "classification": "...",
      "classification_evidence": [],
      "selected_solver_profile": "...",
      "candidate": "",
      "candidate_source": "",
      "validation_status": "validated|rejected|unverified|blocked",
      "validation_evidence": [],
      "blocked_reason": "",
      "next_action": "..."
    }
  ]
}
```

若任何样本 solved/validated，必须说明验证依据。若无样本 solved，也可以 ACCEPT，只要分类、blocked reason 和下一步证据需求清楚且测试通过。

---

## 7. Tests

必须运行 JSON 校验：

```bash
python -m json.tool project_state\current_state.json > NUL
python -m json.tool project_state\artifact_index.json > NUL
python -m json.tool project_state\local_reverse_ida_summary.json > NUL
```

若新增 `reverse_agent/local_reverse_ida_guided_solver.py`，必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_ida_guided_solver.py
```

必须运行 solver CLI 或等价入口：

```bash
python -m reverse_agent.local_reverse_ida_guided_solver --ida-summary project_state\local_reverse_ida_summary.json --artifact-index project_state\artifact_index.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_ida_solver_result.json
```

必须校验输出：

```bash
python -m json.tool project_state\local_reverse_ida_solver_result.json > NUL
python -c "import json; d=json.load(open('project_state/local_reverse_ida_solver_result.json', encoding='utf-8')); assert d['target_count']==3; assert len(d['targets'])==3; assert all(t.get('classification') for t in d['targets']); assert all(t.get('selected_solver_profile') for t in d['targets'])"
```

必须运行相关测试：

```bash
python -m pytest -q tests\test_local_reverse_string_solver.py tests\test_local_reverse_ida_summary.py tests\test_project_state.py
```

若新增模块，必须新增或扩展测试，例如：

```text
tests/test_local_reverse_ida_guided_solver.py
```

并运行：

```bash
python -m pytest -q tests\test_local_reverse_ida_guided_solver.py
```

最后运行：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

测试结果必须写入：

```text
project_state/pytest_result.txt
```

---

## 8. Stop Conditions

出现以下任一情况立即停止并报告：

```text
1. current_state.json 缺少 local_reverse_training.current_ida_evidence。
2. current_ida_evidence 不是 3 个目标。
3. artifact_index.json 缺少 local_reverse_ida_summary 或 3 个 local_reverse_ida_evidence_*。
4. local_reverse_ida_summary.json 不是 SUCCESS。
5. raw IDA JSON 缺失或无法解析。
6. 需要重新运行 IDA/Ghidra/debugger 才能继续。
7. 需要扩大样本才能继续。
8. 需要读取完整 solve_reports/ 才能继续。
9. 需要复制/提交/上传/编码样本二进制才能继续。
10. 无法安全验证 candidate；此时必须标记 unverified/blocked，不得伪造 validated。
11. 发现现有 solver 已能完成同等功能；此时不得重复造轮子，只能复用并补充 thin wrapper/test。
```

本轮完成标准：

```text
project_state/local_reverse_ida_solver_result.json 已生成；
3 个样本均有 evidence-backed classification；
3 个样本均有 selected_solver_profile；
candidate/blocked_reason/next_action 清楚；
若声称 validated，必须有真实验证记录；
未重跑 IDA/Ghidra/debugger；
未扩大样本；
未复制或提交二进制；
codex_execution_report.md 和 pytest_result.txt 对应本 decision。
```
