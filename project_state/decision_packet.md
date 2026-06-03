```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260603_ida_guided_solver_trust_gate_v1",
  "round_id": "round_20260603_ida_guided_solver_trust_gate_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮目标是补强 `reverse_agent/local_reverse_ida_guided_solver.py` 的证据可信边界，修复上一轮审计指出的两个工程风险：

```text
1. artifact 解析主要看 key/path 是否存在，没有强制校验 latest_artifacts_v2.freshness == current。
2. 样本分类仍允许文件名作为较强触发条件，存在 filename-only 误分类风险。
```

本轮不继续求解 3 个样本，不重新运行 IDA，不重新运行 Ghidra/debugger，不扩大样本。目标是让后续 `ida_summary_guided_solver` 只能使用 current provenance 的 IDA evidence，并且分类必须由 IDA evidence 内容支持，而不是由文件名单独触发。

必须完成：

```text
1. local_reverse_ida_guided_solver 的 artifact resolver 默认优先并要求 latest_artifacts_v2。
2. raw IDA evidence artifact 必须 freshness=current 才可用于分类/候选生成。
3. stale/missing/unknown artifact 必须导致该目标 blocked，不能退回旧 latest_artifacts 当 current。
4. 分类逻辑不得仅凭 relative_path/filename 成功；文件名只能作为弱线索。
5. 增加测试覆盖 stale artifact、filename-only 分类、hash no-candidate、success+failure validation 不得 validated。
6. 不改变上一轮 solver result 的语义结论：3 个目标仍未 validated，除非真实测试证明有变化。
```

---

## 2. Current Evidence

当前主线：

```text
engineering_branch
```

理由：本轮只修 solver orchestrator 的 artifact freshness/provenance gate 和测试，不推进新的样本求解。

上一轮 `ida_summary_guided_solver_v1` 已完成并被审计为 `ACCEPTED_WITH_LIMITATIONS`：

```text
project_state/local_reverse_ida_solver_result.json
status=PARTIAL
target_count=3
solved_count=0
validated_count=0
runtime_validation_attempted_count=1
```

上一轮的关键限制：

```text
1. _preflight() 只检查 artifact key 是否存在，没有强制 latest_artifacts_v2.freshness=current。
2. _artifact_path() 优先使用 latest_artifacts，绕过 latest_artifacts_v2 的 freshness/provenance metadata。
3. classify_target() 对 sha_256.exe 使用了文件名作为分类条件之一；长期上应禁止 filename-only 分类。
4. 新增测试覆盖偏薄。
```

当前可用 current local_reverse artifact keys：

```text
local_reverse_ida_summary
local_reverse_ida_evidence_18019fca52b389fe
local_reverse_ida_evidence_4c69f173f2bd0211
local_reverse_ida_evidence_bcbd9979db015bfd
local_reverse_ida_solver_result
```

其中 local_reverse IDA evidence 在 `latest_artifacts_v2` 中应为：

```text
freshness=current
source_run=round_20260603_local_reverse_ida_path_rerun_v1
```

当前执行权威是本 `decision_packet.md`。`task_packet.json` 中旧 `samplereverse` 字段仍为背景兼容字段，不得覆盖本轮任务。

---

## 3. Do Not Do

严禁：

```text
1. 不重新运行 IDA。
2. 不运行 Ghidra。
3. 不运行 OllyDbg/x64dbg/Frida/debugger。
4. 不继续解 sha_256/CPP2/Cpp1 的静态约束。
5. 不扩大到 22 个样本。
6. 不处理 3 个 local_reverse target 之外的 binary。
7. 不复制、上传、提交、base64/hex 编码 E:\reverse 下的样本二进制。
8. 不读取完整 solve_reports/。
9. 不读取完整 PROJECT_PROGRESS_LOG.txt。
10. 不修改 .codex-skills/。
11. 不回旧 sample_solver 盲搜。
12. 不把 stale/missing/unknown artifact 当 current evidence。
13. 不用 filename-only 或 relative_path-only 触发题型分类。
14. 不因为测试 mock 输出 Correct 就放宽真实验证规则。
15. 不把 single-sample 常量硬编码成长期 solver 逻辑。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_ida_guided_solver.py。
2. 修改 tests/test_local_reverse_ida_guided_solver.py。
3. 必要时更新 project_state/local_reverse_ida_solver_result.json，但不得伪造 validated。
4. 必要时更新 project_state/artifact_index.json/current_state.json/task_packet.json 的 local_reverse advisory 字段。
5. 更新 project_state/codex_execution_report.md。
6. 更新 project_state/pytest_result.txt。
7. 有界读取 project_state/local_reverse_ida_summary.json 和 artifact_index 中登记的 3 个 raw IDA JSON。
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
reverse_agent/local_reverse_ida_guided_solver.py
tests/test_local_reverse_ida_guided_solver.py
```

必要时读取：

```text
reverse_agent/local_reverse_string_solver.py
reverse_agent/local_reverse_runtime.py
tests/test_local_reverse_string_solver.py
tests/test_local_reverse_ida_summary.py
tests/test_project_state.py
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
2. 本轮 mainline=engineering_branch，不是新的 reverse_solving 求解轮。
3. 本轮目标是 trust gate：artifact freshness/provenance + classification evidence gate。
4. 是否修改 _preflight/_artifact_path 或等价 resolver。
5. 是否强制 latest_artifacts_v2 freshness=current。
6. stale/missing/unknown artifact 的行为是什么。
7. 是否禁止 filename-only 分类成功。
8. 新增了哪些测试用例。
9. 是否重新生成 local_reverse_ida_solver_result；如生成，结果 status/solved_count/validated_count 是什么。
10. 未重新运行 IDA/Ghidra/debugger/dynamic probe。
11. 未扩大样本。
12. 未复制、提交、上传或编码样本二进制。
13. 未读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
14. 未修改 .codex-skills/。
15. 测试真实运行并写入 project_state/pytest_result.txt。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260603_ida_guided_solver_trust_gate_v1",
  "round_id": "round_20260603_ida_guided_solver_trust_gate_v1",
  "based_on_decision_id": "decision_20260603_ida_guided_solver_trust_gate_v1",
  "status": "SUCCESS_OR_PARTIAL_OR_BLOCKED",
  "acceptance_recommendation": "ACCEPT_OR_NEEDS_REVIEW_OR_REWORK",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 6. Implementation Scope

### 6.1 Artifact freshness/provenance gate

修改 resolver 行为：

```text
1. raw IDA evidence artifact 必须从 latest_artifacts_v2 读取元数据。
2. required artifact key 缺少 latest_artifacts_v2 条目时，该 target blocked。
3. freshness != current 时，该 target blocked。
4. path 为空、path 不存在、JSON 不可解析时，该 target blocked。
5. latest_artifacts 只能作为 legacy display/backward-compatible hint，不能作为 current evidence source。
6. solver result artifact 可登记在 latest_artifacts/latest_artifacts_v2，但 raw evidence 读取必须走 current v2 metadata。
```

建议实现方式：

```text
- 新增 resolve_current_artifact(artifact_index, artifact_key) -> tuple[Path | None, list[str]] 或等价结构。
- _preflight() 检查 local_reverse_ida_summary 和 3 个 local_reverse_ida_evidence_* 的 latest_artifacts_v2 freshness。
- solve_target() 接收 per-target artifact resolution reason；若非空，validation_status=blocked。
```

### 6.2 Classification evidence gate

修改 `classify_target()`：

```text
1. relative_path/filename 只能作为 weak_hint，不能单独决定 profile。
2. hash_hex_compare_static 至少需要：64-byte compare evidence + %08x/%08X format evidence。
3. bounded_char_transform_inversion 至少需要：64-byte compare + input range evidence + visible transform evidence。
4. direct_or_api_password_extraction 至少需要：realpwd/pwd-like string + compare/API evidence + decompiler/data-flow snippet。
5. 若证据不足，返回 needs_more_static_evidence。
```

不要在本轮扩展新的题型求解逻辑。

### 6.3 Validation safety gate

确认或补测试：

```text
1. stdout 同时包含 success marker 和 failure marker 时，不得 validated。
2. timeout -> unverified。
3. validation_error -> blocked。
4. rejected candidate 不计入 solved_count。
```

若发现 solved_count 当前把 rejected candidate 计入 solved，必须修复。`solved_count` 应只统计 validation_status == validated，或至少 candidate 存在且 validation_status 不为 rejected/blocked；建议与 `validated_count` 保持保守一致。

### 6.4 Output behavior

本轮可以不重新生成 `project_state/local_reverse_ida_solver_result.json`。如果代码修改后需要验证 CLI，可以输出到临时路径或重新生成正式 result；正式 result 不得将任何样本标为 validated，除非有真实成功证据。

如果重新生成正式 result，期望仍为：

```text
status=PARTIAL
target_count=3
solved_count=0
validated_count=0
```

---

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent\local_reverse_ida_guided_solver.py
```

必须新增/扩展并运行：

```bash
python -m pytest -q tests\test_local_reverse_ida_guided_solver.py
```

测试至少覆盖：

```text
1. latest_artifacts_v2.freshness=stale -> target/result blocked，不读取 legacy latest_artifacts 当 current。
2. latest_artifacts_v2 缺失而 latest_artifacts 存在 -> blocked。
3. filename contains sha_256 但缺少 64-byte compare/%08x evidence -> needs_more_static_evidence。
4. hash evidence 完整但无 bounded input domain -> candidate 为空，validation_status=unverified。
5. stdout 同时包含 Correct 和 try again -> rejected，不得 validated。
6. rejected candidate 不增加 solved_count/validated_count。
```

必须运行 JSON 校验：

```bash
python -m json.tool project_state\current_state.json > NUL
python -m json.tool project_state\artifact_index.json > NUL
python -m json.tool project_state\local_reverse_ida_summary.json > NUL
python -m json.tool project_state\local_reverse_ida_solver_result.json > NUL
```

必须运行相关回归测试：

```bash
python -m pytest -q tests\test_local_reverse_string_solver.py tests\test_local_reverse_ida_summary.py tests\test_project_state.py tests\test_local_reverse_ida_guided_solver.py
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
1. 无法在不破坏 current local_reverse artifacts 的情况下强制 freshness=current。
2. latest_artifacts_v2 缺少当前 raw IDA evidence metadata，且无法安全标记 blocked。
3. 需要重新运行 IDA/Ghidra/debugger 才能继续。
4. 需要扩大样本才能继续。
5. 需要读取完整 solve_reports/ 才能继续。
6. 需要复制/提交/上传/编码样本二进制才能继续。
7. 分类证据不足但代码仍会输出具体 profile。
8. 测试无法覆盖 stale artifact 或 filename-only 分类场景。
```

本轮完成标准：

```text
local_reverse_ida_guided_solver 只使用 latest_artifacts_v2 freshness=current 的 raw IDA evidence；
stale/missing/unknown artifact 会 blocked；
filename-only 不会触发具体 profile；
success+failure 输出不会 validated；
相关测试覆盖并通过；
codex_execution_report.md 和 pytest_result.txt 对应本 decision；
没有推进新的样本求解。
```
