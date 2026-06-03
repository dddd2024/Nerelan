```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_constraint_recovery_delivery_rework_v1",
  "round_id": "round_20260603_local_reverse_constraint_recovery_delivery_rework_v1",
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

本轮是 `local_reverse_constraint_recovery_sprint_v1` 的交付返工轮。

上一轮审计确认：

```text
reverse_agent/local_reverse_constraint_recovery.py 已存在；
tests/test_local_reverse_constraint_recovery.py 已存在；
但 project_state/local_reverse_constraint_recovery_result.json 缺失；
codex_execution_report.md 仍对应旧 decision_20260603_ida_guided_solver_trust_gate_v1；
pytest_result.txt 仍对应旧 decision_20260603_ida_guided_solver_trust_gate_v1。
```

本轮目标不是重新设计，不是扩大求解范围，而是补齐当前约束恢复轮的正式交付：

```text
1. 运行现有 reverse_agent.local_reverse_constraint_recovery CLI。
2. 生成 project_state/local_reverse_constraint_recovery_result.json。
3. 写入与本 decision 匹配的 project_state/codex_execution_report.md。
4. 写入与本 decision 匹配的 project_state/pytest_result.txt。
5. 必要时只做最小代码修复，确保 CLI、result JSON、测试和 lint 通过。
6. 必要时更新 artifact_index/current_state/task_packet 的 local_reverse advisory 字段。
```

完成后必须能审计：本轮确实基于 3 个 current IDA evidence 样本完成约束恢复结果输出，而不是继续沿用上一轮 trust gate 报告。

---

## 2. Current Evidence

当前主线：

```text
reverse_solving
```

理由：本轮仍围绕 3 个具体 local reverse 样本输出 constraint recovery result，只是当前重点是修复交付缺口。

当前执行权威是本 `decision_packet.md`，不是 `task_packet.task`。

已知当前状态：

```text
1. current decision 已要求 local_reverse_constraint_recovery_result.json。
2. reverse_agent/local_reverse_constraint_recovery.py 已新增，并复用 local_reverse_ida_guided_solver 的 trust gate 函数。
3. tests/test_local_reverse_constraint_recovery.py 已新增，覆盖 Cpp1 候选、CPP2 target_before_increment、sha256 无输入域、candidate 上限、stale artifact blocked。
4. codex_execution_report.md 和 pytest_result.txt 仍是旧 trust_gate 轮，必须重写。
5. project_state/local_reverse_constraint_recovery_result.json 当前缺失，必须生成并提交。
```

可信 local_reverse 证据入口仍是：

```text
project_state/current_state.json -> local_reverse_training.current_ida_evidence
project_state/artifact_index.json -> latest_artifacts_v2 local_reverse_* freshness=current
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
```

3 个样本范围固定：

```text
18019fca52b389fe -> 逆向课程2024春01/sha_256.exe
4c69f173f2bd0211 -> 逆向课程2022春02/CPP2.exe
bcbd9979db015bfd -> 逆向课程2022春补考01/Cpp1.exe
```

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
12. 不伪造 validated。
13. 不把旧 trust_gate 报告复制成当前轮报告。
14. 不让 codex_execution_report.md 或 pytest_result.txt 继续保留旧 decision_id。
15. 不新增动态调试器、hook 框架、数据库、消息队列或重型 workflow。
16. 不重新运行 IDA/Ghidra/debugger；若确实需要更多静态证据，只能在结果中标记 targeted static re-extraction required。
```

允许：

```text
1. 运行 reverse_agent.local_reverse_constraint_recovery CLI。
2. 有界读取 current artifact 指向的 3 个 raw IDA JSON。
3. 使用现有 local_reverse_runtime_policy.json 进行 policy-bounded candidate validation。
4. 最小修复 reverse_agent/local_reverse_constraint_recovery.py。
5. 最小修复 tests/test_local_reverse_constraint_recovery.py。
6. 生成 project_state/local_reverse_constraint_recovery_result.json。
7. 更新 artifact_index/current_state/task_packet 的 local_reverse advisory 字段。
8. 更新 project_state/codex_execution_report.md。
9. 更新 project_state/pytest_result.txt。
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
reverse_agent/local_reverse_constraint_recovery.py
tests/test_local_reverse_constraint_recovery.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_runtime.py
```

有界读取，仅限 artifact_index/current_state 指向的 3 个 raw IDA JSON：

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\bcbd9979db015bfd\Cpp1_ida_evidence.json
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
2. 本轮是 delivery rework，修复上一轮缺失的 result/report/pytest 交付。
3. mainline=reverse_solving。
4. 旧 trust_gate 报告和 pytest_result 已被替换，不再作为当前轮报告。
5. 是否运行了 local_reverse_constraint_recovery CLI。
6. project_state/local_reverse_constraint_recovery_result.json 的 status、target_count、candidate_count、validated_count。
7. 3 个样本各自的 constraint_status、candidate count、validation count、validated_candidate。
8. Cpp1 是否解释 hookapi rejected 并尝试 evidence-backed alternate candidate。
9. CPP2 是否输出 target_before_increment 或精确 upstream function blocker。
10. sha_256 是否输出 NO_BOUNDED_HASH_PREIMAGE_DOMAIN 或其它有界输入域结论。
11. 未扩大样本。
12. 未复制、提交、上传或编码样本二进制。
13. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
14. 未修改 .codex-skills/。
15. 未重跑 IDA/Ghidra/debugger。
16. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_constraint_recovery_delivery_rework_v1",
  "round_id": "round_20260603_local_reverse_constraint_recovery_delivery_rework_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_constraint_recovery_delivery_rework_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 首先运行现有 CLI

优先直接运行：

```bash
python -m reverse_agent.local_reverse_constraint_recovery --ida-summary project_state\local_reverse_ida_summary.json --artifact-index project_state\artifact_index.json --solver-result project_state\local_reverse_ida_solver_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_constraint_recovery_result.json
```

不得先重写模块。只有 CLI 报错、输出不符合 schema、或测试失败时，才允许最小修复。

### 6.2 结果文件最低要求

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
  "targets": []
}
```

每个 target 必须有：

```text
sample_id
relative_path
classification
constraint_status
recovered_constraints
candidate_generation
candidates
validation_results
validated_candidate
blocked_reason
next_action
```

若 `validated_count > 0`，必须有真实 runtime transcript 摘要；如果没有 validated，也可以接受，但每个 unresolved target 必须有精确 blocker。

### 6.3 必要最小修复边界

允许修复：

```text
1. CLI 参数或输出路径问题。
2. JSON schema/字段缺失。
3. candidate_count/validated_count 统计错误。
4. Cpp1 candidate 生成没有 alternate candidate 的问题。
5. CPP2 target_before_increment 提取或 blocked_reason 不精确的问题。
6. sha_256 无输入域时错误生成 candidate 的问题。
7. 测试与实际 schema 不一致的问题。
```

不允许：

```text
1. 大幅改造架构。
2. 新增第二套 trust gate。
3. 新增第二套 runtime verifier。
4. 把 sample-specific flag/candidate 硬编码进长期逻辑。
```

### 6.4 状态登记

如果生成 result 成功，必须更新或确认：

```text
artifact_index.latest_artifacts_v2.local_reverse_constraint_recovery_result
```

该条目必须包括：

```text
kind=local_reverse_constraint_recovery_result
path=project_state\local_reverse_constraint_recovery_result.json
freshness=current
source_run=round_20260603_local_reverse_constraint_recovery_delivery_rework_v1
sha256
size_bytes
modified_at
```

可选更新：

```text
current_state.json local_reverse_training.latest_constraint_recovery
current_state.json local_reverse_training.latest_validated_candidates
task_packet.json local_reverse_current_artifact / local_reverse_next_suggested_task
```

---

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_constraint_recovery.py
```

必须运行：

```bash
python -m pytest -q tests\test_local_reverse_constraint_recovery.py
```

必须运行 CLI：

```bash
python -m reverse_agent.local_reverse_constraint_recovery --ida-summary project_state\local_reverse_ida_summary.json --artifact-index project_state\artifact_index.json --solver-result project_state\local_reverse_ida_solver_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_constraint_recovery_result.json
```

必须校验 result：

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

测试结果必须写入：

```text
project_state/pytest_result.txt
```

`pytest_result.txt` 顶部必须对应：

```text
decision_id=decision_20260603_local_reverse_constraint_recovery_delivery_rework_v1
report_id=report_20260603_local_reverse_constraint_recovery_delivery_rework_v1
round_id=round_20260603_local_reverse_constraint_recovery_delivery_rework_v1
```

---

## 8. Stop Conditions

出现以下任一情况立即停止并报告：

```text
1. current local_reverse IDA evidence 缺失或 freshness 不是 current。
2. raw IDA JSON 无法解析。
3. local_reverse_constraint_recovery CLI 无法在最小修复内运行。
4. 需要读取完整 solve_reports/ 才能继续。
5. 需要读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
6. 需要扩大到 3 个样本之外才能继续。
7. 需要无界 brute force 才能继续。
8. 需要重新运行 IDA/Ghidra/debugger 才能继续。
9. 需要复制、提交、上传或编码样本二进制才能继续。
10. validation 输出不明确；此时必须标记 unverified/rejected，不得 validated。
```

本轮完成标准：

```text
project_state/local_reverse_constraint_recovery_result.json 已生成并提交；
project_state/codex_execution_report.md 对应本 decision；
project_state/pytest_result.txt 对应本 decision；
3 个样本都有 recovered_constraints 或精确 blocked_reason；
没有扩大样本、没有重跑 IDA/Ghidra/debugger、没有提交二进制；
相关测试和 lint 通过。
```
