```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_fix_corpus_loader_path_consistency_and_test_record",
  "round_id": "round_20260531_fix_corpus_loader_path_consistency_and_test_record",
  "based_on_state_build_id": "state_20260527_153028_1d6dd81ecbd6",
  "based_on_state_digest": "1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

本轮属于 **engineering_branch**。目标是对 `corpus_static_audit` 返工做最后收口：修复 `corpus_loader.validate_corpus()` 的路径一致性校验缺口，并补齐 `pytest_result.txt` 的测试记录证据链。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍是旧状态派生建议，不自动覆盖本 decision。

本轮只做最小修复，不新增 solver，不推进 DES/RC4/SEH 能力，不运行任何样本二进制。

## 1. Goal

修复上一轮审计留下的两个阻断问题：

```text
1. project_state/pytest_result.txt 未完整记录本轮必须运行的 CLI、py_compile、lint-decision、lint-report、git diff --check。
2. reverse_agent/corpus_loader.py 的 validate_corpus() 没有严格校验 metadata.sample_path、case.json cases 结构、case_id、input_value 与 metadata.sample_path 的一致性。
```

完成后，应满足：

```text
1. metadata.sample_path 必须等于 sample_corpus/reverse/<case_id>/sample.exe。
2. case.json 顶层 cases 必须存在且长度为 1。
3. case.json cases[0].case_id 必须等于目录 case_id。
4. case.json cases[0].input_value 必须等于 metadata.sample_path。
5. pytest_result.txt 的 tests_ran 必须完整列出本轮实际运行的所有规定命令。
6. codex_execution_report.md 与本 decision_id / round_id 对齐。
```

## 2. Current Evidence

上一轮已经完成或基本完成：

```text
1. codex_execution_report.md 顶部 fenced block 已改为 ```json codex_report_summary。
2. codex_execution_report.md 的 based_on_decision_id 已对齐上一轮返工 decision。
3. corpus_static_audit.run_audit() 已先调用 validate_corpus()。
4. invalid corpus 时 CLI 已返回非零退出码。
5. corpus_classifier.py 的 SEH NameError bug 已修复。
6. tests 已覆盖 SEH keyword 分类路径。
7. 未见 .codex-skills/、samplereverse 主线、sample_solver.py 或 sample.exe 修改。
```

仍需修复：

```text
1. pytest_result.txt 的 tests_ran 只列出 5 个 pytest，没有记录 CLI、py_compile、lint-decision、lint-report、git diff --check。
2. validate_corpus() 只检查 metadata.sample_path 是否绝对、是否含 local_reverse_samples、是否含 ..，没有验证它等于 sample_corpus/reverse/<case_id>/sample.exe。
3. validate_corpus() 没有检查 case.json cases 必须存在且长度为 1。
4. validate_corpus() 没有检查 cases[0].case_id == case_id。
5. validate_corpus() 没有检查 cases[0].input_value == metadata.sample_path。
6. tests/test_corpus_loader.py 中所谓 input_value mismatch 测试实际测的是 .. 逃逸路径，不是真正的 input_value != metadata.sample_path。
```

当前主线仍是：

```text
engineering_branch
```

当前 skill profiles：

```text
reverse-agent-iteration@v2
```

不使用：

```text
samplereverse-frontier@v2
```

artifact freshness 约束：

```text
1. 本轮不依赖 solve_reports/ runtime artifact。
2. artifact_index.latest_artifacts_v2 中的 stale/missing runtime artifact 不作为本轮证据。
3. 本轮只允许重建 project_state/corpus_static_audit.json 和 project_state/corpus_solver_gap_report.md。
```

## 3. Do Not Do

严禁：

```text
1. 不执行任何 sample.exe。
2. 不运行 IDA / OllyDbg / Frida / pywinauto。
3. 不运行 runtime probe。
4. 不运行 Base64/RC4 breakpoint probe。
5. 不运行 samplereverse harness。
6. 不读取完整 solve_reports/。
7. 不读取完整 PROJECT_PROGRESS_LOG.txt。
8. 不修改 .codex-skills/。
9. 不修改 reverse_agent/strategies/compare_aware_search.py。
10. 不修改 reverse_agent/profiles/samplereverse.py。
11. 不修改 reverse_agent/sample_solver.py。
12. 不修改 sample_corpus/reverse/*/sample.exe。
13. 不新增 solver.py。
14. 不把分类结果升级为确定解题结论。
15. 不一次性实现 DES/RC4/SEH solver。
16. 不重写 static_feature_extractor 或 classifier 主体逻辑，除非测试暴露必须修复的小 bug。
```

## 4. Files To Inspect

默认读取：

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
reverse_agent/corpus_loader.py
tests/test_corpus_loader.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/corpus_static_audit.json
project_state/corpus_solver_gap_report.md
sample_corpus/reverse/manifest.json
sample_corpus/reverse/*/metadata.json
sample_corpus/reverse/*/case.json
```

允许修改：

```text
reverse_agent/corpus_loader.py
tests/test_corpus_loader.py
project_state/corpus_static_audit.json
project_state/corpus_solver_gap_report.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

原则上不修改：

```text
reverse_agent/static_feature_extractor.py
reverse_agent/corpus_classifier.py
reverse_agent/corpus_static_audit.py
tests/test_static_feature_extractor.py
tests/test_corpus_classifier.py
tests/test_corpus_static_audit.py
sample_corpus/reverse/*/metadata.json
sample_corpus/reverse/*/case.json
README.txt
```

不得修改：

```text
.codex-skills/
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
reverse_agent/sample_solver.py
sample_corpus/reverse/*/sample.exe
solve_reports/
```

如果真实 corpus 的 metadata/case.json 本身不满足 stricter validation，先报告具体不一致；只允许做最小文本修复，不得改 sample.exe。

## 5. Required Audit

Codex 报告必须逐项回答：

```text
1. pytest_result.txt 的 decision_id/report_id/round_id 是否与本 decision 对齐。
2. pytest_result.txt 的 tests_ran 是否完整列出所有规定命令。
3. validate_corpus() 是否要求 metadata.sample_path 存在。
4. validate_corpus() 是否要求 metadata.sample_path 等于 sample_corpus/reverse/<case_id>/sample.exe。
5. validate_corpus() 是否拒绝 metadata.sample_path 指向其他相对路径。
6. validate_corpus() 是否要求 case.json 顶层 cases 存在。
7. validate_corpus() 是否要求 cases 长度为 1。
8. validate_corpus() 是否要求 cases[0].case_id == case_id。
9. validate_corpus() 是否要求 cases[0].input_value == metadata.sample_path。
10. tests 是否覆盖 metadata.sample_path 指向其他相对路径 -> invalid。
11. tests 是否覆盖 case.json cases 为空 -> invalid。
12. tests 是否覆盖 case.json cases 长度大于 1 -> invalid。
13. tests 是否覆盖 case.json case_id 不匹配 -> invalid。
14. tests 是否覆盖 case.json input_value != metadata.sample_path -> invalid。
15. 是否重新运行 corpus_static_audit CLI 并重建 corpus_static_audit.json / corpus_solver_gap_report.md。
16. 是否运行并记录 lint-decision。
17. 是否运行并记录 lint-report。
18. 是否运行并记录 git diff --check。
19. 是否没有执行任何 sample.exe。
20. 是否没有运行 runtime probe。
21. 是否没有修改 .codex-skills/。
22. 是否没有修改 samplereverse 主线。
```

## 6. Implementation Scope

### 6.1 修复 validate_corpus 路径一致性

在 `reverse_agent/corpus_loader.py` 中补强 `validate_corpus()`。

对每个 case，读取 metadata 后必须检查：

```text
1. metadata.sample_path 存在且非空。
2. metadata.sample_path 是相对路径。
3. metadata.sample_path 不包含 local_reverse_samples。
4. metadata.sample_path 不包含 ..。
5. metadata.sample_path == sample_corpus/reverse/<case_id>/sample.exe。
```

建议实现时不要硬编码 Windows 分隔符。可以统一转换为 POSIX：

```python
expected_sample_path = f"sample_corpus/reverse/{case_id}/sample.exe"
actual_sample_path = str(PurePosixPath(metadata["sample_path"].replace("\\", "/")))
if actual_sample_path != expected_sample_path:
    error(...)
```

### 6.2 修复 case.json 结构校验

对每个 case 的 `case.json`，必须检查：

```text
1. case.json 可解析。
2. 顶层 cases 存在。
3. cases 是 list。
4. len(cases) == 1。
5. cases[0].case_id == case_id。
6. cases[0].input_value 存在且非空。
7. cases[0].input_value == metadata.sample_path。
8. cases[0].input_value 不包含 local_reverse_samples。
9. cases[0].input_value 不包含 ..。
```

如果任何一项失败，`validate_corpus()` 必须返回 `valid=false` 并给出包含 `[case_id]` 的错误信息。

### 6.3 补强测试

修改 `tests/test_corpus_loader.py`，新增或修正以下测试：

```text
1. test_validate_metadata_sample_path_wrong_relative_path
   - metadata.sample_path = sample_corpus/reverse/<case_id>/other.exe
   - 预期 invalid。

2. test_validate_case_json_cases_empty
   - case.json = {"cases": []}
   - 预期 invalid。

3. test_validate_case_json_cases_multiple
   - case.json 中 cases 有两个元素
   - 预期 invalid。

4. test_validate_case_json_case_id_mismatch
   - cases[0].case_id != case_id
   - 预期 invalid。

5. test_validate_case_json_input_value_mismatch_metadata
   - metadata.sample_path 正确
   - case.json input_value = sample_corpus/reverse/<case_id>/other.exe
   - 预期 invalid。
```

保留上一轮已有测试：

```text
sha256 mismatch
size mismatch
safe_to_run=true
upload_allowed=false
metadata.sample_path absolute path
metadata.sample_path contains local_reverse_samples
case.json input_value contains local_reverse_samples
```

### 6.4 更新 pytest_result.txt

`project_state/pytest_result.txt` 顶部 JSON 必须为：

```json
{
  "schema_version": 1,
  "decision_id": "decision_20260531_fix_corpus_loader_path_consistency_and_test_record",
  "report_id": "report_20260531_fix_corpus_loader_path_consistency_and_test_record",
  "round_id": "round_20260531_fix_corpus_loader_path_consistency_and_test_record",
  "status": "PASSED",
  "tests_ran": []
}
```

其中 `tests_ran` 必须完整列出本轮实际运行的所有命令：

```text
python -m pytest -q tests/test_sample_corpus.py
python -m pytest -q tests/test_corpus_loader.py
python -m pytest -q tests/test_static_feature_extractor.py
python -m pytest -q tests/test_corpus_classifier.py
python -m pytest -q tests/test_corpus_static_audit.py
python -m reverse_agent.corpus_static_audit --corpus-dir sample_corpus/reverse --out project_state/corpus_static_audit.json --gap-report project_state/corpus_solver_gap_report.md
python -m py_compile reverse_agent/corpus_loader.py reverse_agent/static_feature_extractor.py reverse_agent/corpus_classifier.py reverse_agent/corpus_static_audit.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

正文也必须记录这些命令的结果。不能只在 codex_execution_report.md 中记录。

### 6.5 更新 codex_execution_report.md

`codex_execution_report.md` 顶部必须保持：

```text
```json codex_report_summary
```

本轮字段必须对齐：

```text
report_id = report_20260531_fix_corpus_loader_path_consistency_and_test_record
round_id = round_20260531_fix_corpus_loader_path_consistency_and_test_record
based_on_decision_id = decision_20260531_fix_corpus_loader_path_consistency_and_test_record
```

`files_changed` 必须完整列出实际变更文件，包括 project_state 文件。

## 7. Tests

必须运行并记录：

```text
python -m pytest -q tests/test_sample_corpus.py
python -m pytest -q tests/test_corpus_loader.py
python -m pytest -q tests/test_static_feature_extractor.py
python -m pytest -q tests/test_corpus_classifier.py
python -m pytest -q tests/test_corpus_static_audit.py
python -m reverse_agent.corpus_static_audit --corpus-dir sample_corpus/reverse --out project_state/corpus_static_audit.json --gap-report project_state/corpus_solver_gap_report.md
python -m py_compile reverse_agent/corpus_loader.py reverse_agent/static_feature_extractor.py reverse_agent/corpus_classifier.py reverse_agent/corpus_static_audit.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

不得运行：

```text
任何 sample.exe
IDA / OllyDbg / Frida / pywinauto
runtime probe
samplereverse harness
Base64/RC4 breakpoint probe
python -m pytest -q   # 不要求全量，除非 Codex 自愿且耗时可控
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 严格校验后真实 corpus 的 metadata.sample_path 与 case.json input_value 不一致，且不能安全做最小文本修复。
2. lint-report 无法通过。
3. pytest_result.txt 无法与本 decision/report/round 对齐。
4. 修复需要修改 sample_corpus/reverse/*/sample.exe。
5. 修复需要修改 .codex-skills/。
6. 修复需要修改 samplereverse 主线。
7. 修复需要执行任何 sample.exe。
8. 修复需要读取完整 solve_reports/。
```

完成条件：

```text
1. metadata.sample_path 严格等于 sample_corpus/reverse/<case_id>/sample.exe。
2. case.json cases 存在且长度为 1。
3. case.json case_id 与目录 case_id 一致。
4. case.json input_value 与 metadata.sample_path 一致。
5. 上述不一致场景都有测试覆盖。
6. corpus_static_audit.json 重新生成。
7. corpus_solver_gap_report.md 重新生成。
8. pytest_result.txt 完整记录所有规定命令。
9. codex_execution_report.md 与本 decision/report/round 对齐。
10. lint-decision / lint-report / git diff --check 均通过。
11. 未执行任何 sample.exe。
12. 未运行 runtime probe。
13. 未修改 .codex-skills/。
14. 未修改 samplereverse 主线。
```
