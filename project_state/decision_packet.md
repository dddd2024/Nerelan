```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_local_reverse_validated_handoff_and_test_record_v1",
  "round_id": "round_20260603_local_reverse_validated_handoff_and_test_record_v1",
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

本轮合并两个任务：

```text
1. 补齐上一轮 pytest_result.txt 的命令级测试记录，使其包含 py_compile、CLI、json.tool、结构断言、pytest、lint、git diff --check。
2. 将已验证的 Cpp1.exe candidate `hookapi` 做成正式 handoff artifact，并同步 project_state。
```

上一轮已接受的事实：

```text
project_state/local_reverse_constraint_recovery_result.json
stage=local_reverse_constraint_recovery_sprint_v1
status=PARTIAL
target_count=3
candidate_count=2
validated_count=1
validated target=bcbd9979db015bfd / Cpp1.exe
validated_candidate=hookapi
validation transcript contains congratulations!
```

本轮必须输出：

```text
project_state/local_reverse_validated_candidate_handoff.json
```

该 handoff 必须记录：

```text
1. validated sample_id、relative_path、candidate。
2. candidate 来源：xor_constants_against_literal / string_target=realpwd。
3. 约束来源：project_state/local_reverse_constraint_recovery_result.json。
4. runtime 验证摘要：exit_code、timeout、stdout_preview、stderr_preview、duration_ms、validation_status。
5. 未解决样本摘要：sha_256.exe 和 CPP2.exe 的 blocked_reason / next_action。
6. provenance：source_result、source_run、artifact keys、freshness=current。
```

本轮不是继续求解新样本，不扩大样本，不重跑 IDA/Ghidra/debugger。可以为了再现 handoff 可信性，重新运行现有 `local_reverse_constraint_recovery` CLI 和 policy-bounded candidate validation；不得无界 brute force。

---

## 2. Current Evidence

当前主线：

```text
reverse_solving
```

理由：本轮把一个真实 validated candidate 纳入 local reverse 求解状态，并生成 handoff artifact。同步测试记录属于同一交付的审计补强。

当前执行权威是本 `decision_packet.md`，不是 `task_packet.task`。

当前可信证据入口：

```text
project_state/local_reverse_constraint_recovery_result.json
project_state/artifact_index.json -> latest_artifacts_v2.local_reverse_constraint_recovery_result freshness=current
project_state/current_state.json -> local_reverse_training.current_ida_evidence
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
```

当前已知状态：

```text
1. Cpp1.exe 已验证 candidate=hookapi。
2. sha_256.exe 仍 blocked: NO_BOUNDED_HASH_PREIMAGE_DOMAIN。
3. CPP2.exe 仍 blocked: MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005。
4. 上一轮 pytest_result.txt 只记录 pytest 集合，没有完整记录 py_compile、CLI、json.tool、lint、git diff --check。
```

旧 `samplereverse` 字段仍只能作为背景兼容字段，不能覆盖 local_reverse 当前证据。

---

## 3. Do Not Do

严禁：

```text
1. 不扩大到 22 个样本。
2. 不处理这 3 个 local_reverse 样本之外的 binary。
3. 不复制、上传、提交、base64/hex 编码 E:\reverse 下的样本二进制。
4. 不提交完整 solve_reports/。
5. 不读取完整 solve_reports/。
6. 不读取完整 PROJECT_PROGRESS_LOG.txt。
7. 不修改 .codex-skills/。
8. 不回旧 sample_solver 盲搜。
9. 不做无界 brute force。
10. 不把 SHA-256/hash 当作可逆解密。
11. 不伪造 validated。
12. 不重新运行 IDA/Ghidra/debugger。
13. 不新增动态调试器、hook 框架、数据库、消息队列或重型 workflow。
14. 不把 `hookapi` 写入长期 skill 或硬编码成通用 solver 规则。
15. 不把测试记录写成未实际运行的命令。
```

允许：

```text
1. 读取 project_state/local_reverse_constraint_recovery_result.json。
2. 重新运行 local_reverse_constraint_recovery CLI，以刷新/复现 result 和 runtime transcript。
3. 使用现有 local_reverse_runtime_policy.json 进行 policy-bounded validation。
4. 生成 project_state/local_reverse_validated_candidate_handoff.json。
5. 更新 artifact_index latest_artifacts_v2，登记 local_reverse_validated_candidate_handoff。
6. 更新 current_state.json local_reverse_training.latest_validated_candidates。
7. 更新 task_packet.json local_reverse advisory 字段。
8. 更新 codex_execution_report.md。
9. 更新 pytest_result.txt，并记录完整命令结果。
10. 必要时只做最小 schema/format 修复，不做新求解逻辑。
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
project_state/local_reverse_constraint_recovery_result.json
project_state/local_reverse_ida_summary.json
project_state/local_reverse_ida_solver_result.json
project_state/local_reverse_runtime_policy.json
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_runtime.py
tests/test_local_reverse_constraint_recovery.py
tests/test_local_reverse_ida_guided_solver.py
```

有界读取，仅限 artifact_index/current_state 指向的 3 个 raw IDA JSON；不得遍历完整 solve_reports：

```text
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\18019fca52b389fe\sha_256_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\4c69f173f2bd0211\CPP2_ida_evidence.json
solve_reports\tool_artifacts\local_reverse_ida_evidence_integration_v1\bcbd9979db015bfd\Cpp1_ida_evidence.json
```

---

## 5. Required Audit

Codex 必须在 `project_state/codex_execution_report.md` 中写明：

```text
1. 当前 decision_packet 是执行权威。
2. 本轮合并 test record refresh 与 validated candidate handoff。
3. mainline=reverse_solving。
4. 是否重新运行 constraint_recovery CLI。
5. handoff artifact path、status、validated_count。
6. Cpp1 handoff candidate、source relation、validation transcript 摘要。
7. sha_256/CPP2 未解决状态和下一步 blocker。
8. artifact_index/current_state/task_packet 更新内容。
9. pytest_result.txt 已补齐哪些命令记录。
10. 未扩大样本。
11. 未复制、提交、上传或编码样本二进制。
12. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
13. 未修改 .codex-skills/。
14. 未重跑 IDA/Ghidra/debugger。
15. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_local_reverse_validated_handoff_and_test_record_v1",
  "round_id": "round_20260603_local_reverse_validated_handoff_and_test_record_v1",
  "based_on_decision_id": "decision_20260603_local_reverse_validated_handoff_and_test_record_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 Handoff artifact

生成：

```text
project_state/local_reverse_validated_candidate_handoff.json
```

最低结构：

```json
{
  "schema_version": 1,
  "stage": "local_reverse_validated_candidate_handoff_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "source_result": "project_state\\local_reverse_constraint_recovery_result.json",
  "validated_count": 1,
  "validated_candidates": [
    {
      "sample_id": "bcbd9979db015bfd",
      "relative_path": "逆向课程2022春补考01/Cpp1.exe",
      "candidate": "hookapi",
      "source_relation": "xor_constants_against_literal",
      "string_target": "realpwd",
      "transform_formula": "candidate[i] = constants[i] XOR target[i]",
      "validation_status": "validated",
      "validation_stdout_preview": "...congratulations!...",
      "validation_exit_code": 0,
      "validation_timeout": false
    }
  ],
  "unresolved_targets": [
    {
      "sample_id": "18019fca52b389fe",
      "blocked_reason": "NO_BOUNDED_HASH_PREIMAGE_DOMAIN",
      "next_action": "..."
    },
    {
      "sample_id": "4c69f173f2bd0211",
      "blocked_reason": "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005",
      "next_action": "..."
    }
  ]
}
```

如果 `local_reverse_constraint_recovery_result.json` does not contain validated candidate anymore after re-run, set handoff status=`BLOCKED` and do not fabricate `hookapi`.

### 6.2 State updates

必须更新或确认：

```text
artifact_index.latest_artifacts_v2.local_reverse_validated_candidate_handoff
```

字段必须包括：

```text
kind=local_reverse_validated_candidate_handoff
path=project_state\local_reverse_validated_candidate_handoff.json
freshness=current
source_run=round_20260603_local_reverse_validated_handoff_and_test_record_v1
sha256
size_bytes
modified_at
```

必须在 `current_state.json` 的 `local_reverse_training` 中添加或更新：

```json
"latest_validated_candidates": [
  {
    "sample_id": "bcbd9979db015bfd",
    "relative_path": "逆向课程2022春补考01/Cpp1.exe",
    "candidate": "hookapi",
    "source_artifact": "project_state\\local_reverse_validated_candidate_handoff.json",
    "validation_status": "validated"
  }
]
```

可选更新 `task_packet.json` advisory：

```text
local_reverse_current_artifact=project_state\local_reverse_validated_candidate_handoff.json
local_reverse_next_suggested_task=Generate targeted static re-extraction decision for CPP2 sub_401005 and sha_256 input-domain evidence
```

### 6.3 Test record refresh

`project_state/pytest_result.txt` 必须记录完整命令，不只记录 pytest 集合。

---

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```bash
python -m py_compile reverse_agent\local_reverse_constraint_recovery.py reverse_agent\local_reverse_ida_guided_solver.py
```

```bash
python -m reverse_agent.local_reverse_constraint_recovery --ida-summary project_state\local_reverse_ida_summary.json --artifact-index project_state\artifact_index.json --solver-result project_state\local_reverse_ida_solver_result.json --policy project_state\local_reverse_runtime_policy.json --out project_state\local_reverse_constraint_recovery_result.json
```

```bash
python -m json.tool project_state\local_reverse_constraint_recovery_result.json > NUL
python -m json.tool project_state\local_reverse_validated_candidate_handoff.json > NUL
python -m json.tool project_state\current_state.json > NUL
python -m json.tool project_state\artifact_index.json > NUL
```

```bash
python -c "import json; h=json.load(open('project_state/local_reverse_validated_candidate_handoff.json', encoding='utf-8')); assert h['validated_count']>=1; assert any(c.get('candidate')=='hookapi' and c.get('validation_status')=='validated' for c in h.get('validated_candidates', []))"
```

```bash
python -m pytest -q tests\test_local_reverse_constraint_recovery.py tests\test_local_reverse_ida_guided_solver.py tests\test_local_reverse_string_solver.py tests\test_local_reverse_ida_summary.py tests\test_project_state.py
```

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

若修改公共 project_state logic 或 runtime verifier，运行：

```bash
python -m pytest -q
```

---

## 8. Stop Conditions

出现以下任一情况立即停止并报告：

```text
1. local_reverse_constraint_recovery_result.json 缺失或无法解析。
2. re-run 后 hookapi 不再 validated。
3. validation transcript 不含明确 success marker 或同时含 failure marker。
4. artifact_index 缺少 current local_reverse evidence metadata。
5. 需要读取完整 solve_reports/ 才能继续。
6. 需要读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
7. 需要扩大到 3 个样本之外才能继续。
8. 需要无界 brute force 才能继续。
9. 需要重新运行 IDA/Ghidra/debugger 才能继续。
10. 需要复制、上传、提交或编码样本二进制才能继续。
```

本轮完成标准：

```text
project_state/local_reverse_validated_candidate_handoff.json 已生成；
Cpp1 hookapi 以 validated candidate 进入 handoff；
artifact_index/current_state/task_packet 已同步或明确说明未同步原因；
pytest_result.txt 记录完整命令级测试；
codex_execution_report.md 对应本 decision；
没有扩大样本、没有重跑 IDA/Ghidra/debugger、没有提交二进制。
```
