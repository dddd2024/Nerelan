```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_fix_corpus_static_audit_validation_and_report",
  "round_id": "round_20260531_fix_corpus_static_audit_validation_and_report",
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

本轮属于 **engineering_branch**。目标是修复上一轮 `corpus_static_audit_route2` 的审计阻断问题，使 corpus 静态 audit 基础设施满足项目报告、测试和安全校验要求。

本轮只做最小返工：修复 report / pytest_result 对齐、补跑 lint、修复 audit 前置校验、修复 SEH 分类 bug、补强 corpus loader 路径校验和对应测试。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍是旧状态派生建议，不自动覆盖本 decision。

## 1. Goal

修复 `corpus_static_audit_route2` 的审计阻断问题，使 corpus 静态 audit 基础设施满足项目报告、测试和安全校验要求。

本轮只做最小返工：

```text
1. 修复 codex_execution_report.md 顶部 fenced block 名称。
2. 更新 pytest_result.txt，使其与当前返工 decision/report/round 对齐。
3. 补跑并记录 lint-decision、lint-report、git diff --check。
4. 修复 corpus_static_audit CLI，使其先 validate_corpus，不合规则停止。
5. 修复 corpus_classifier.py 的 SEH 分支 bug。
6. 补强 corpus_loader 对 metadata.sample_path 和 case.json input_value 的校验。
7. 补强测试覆盖上述问题。
```

不扩大为新 solver，不推进 DES/RC4/SEH solver，不运行样本二进制。

## 2. Current Evidence

当前上一轮实现新增了：

```text
reverse_agent/corpus_loader.py
reverse_agent/static_feature_extractor.py
reverse_agent/corpus_classifier.py
reverse_agent/corpus_static_audit.py
tests/test_corpus_loader.py
tests/test_static_feature_extractor.py
tests/test_corpus_classifier.py
tests/test_corpus_static_audit.py
project_state/corpus_static_audit.json
project_state/corpus_solver_gap_report.md
```

但存在阻断问题：

```text
1. pytest_result.txt 仍指向 decision_20260531_fix_sample_corpus_migration_incomplete_paths。
2. codex_execution_report.md 顶部是 ```json，不是 ```json codex_report_summary。
3. report tests_ran 未包含 lint-decision、lint-report、git diff --check。
4. corpus_static_audit.run_audit() 未调用 validate_corpus。
5. tests/test_corpus_static_audit.py 中存在 sha256 明显不匹配但 audit 仍成功的 fixture。
6. corpus_classifier.py 的 SEH feature 分支引用未定义的 seh_hits。
7. corpus_loader 未验证 metadata.sample_path 和 case.json input_value。
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

原因：本轮修复 corpus audit 工程基础设施，不推进 samplereverse runtime candidate/frontier，也不依赖 solve_reports runtime artifact。

artifact freshness 约束：

```text
1. 本轮不依赖 solve_reports/ 中的 runtime artifact。
2. artifact_index.latest_artifacts_v2 中的 stale/missing runtime artifact 不作为本轮证据。
3. 本轮只重建 project_state/corpus_static_audit.json 和 project_state/corpus_solver_gap_report.md。
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
```

特别限制：

```text
1. 只允许读取 sample.exe 字节用于 hash、size、字符串和静态特征抽取。
2. 如果修复需要执行样本二进制，立即停止并报告 BLOCKED。
3. 如果修复需要引入动态调试器或重型逆向框架，立即停止并报告 BLOCKED。
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
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
reverse_agent/corpus_loader.py
reverse_agent/static_feature_extractor.py
reverse_agent/corpus_classifier.py
reverse_agent/corpus_static_audit.py
tests/test_corpus_loader.py
tests/test_static_feature_extractor.py
tests/test_corpus_classifier.py
tests/test_corpus_static_audit.py
project_state/corpus_static_audit.json
project_state/corpus_solver_gap_report.md
sample_corpus/reverse/manifest.json
sample_corpus/reverse/*/metadata.json
sample_corpus/reverse/*/case.json
```

允许修改：

```text
reverse_agent/corpus_loader.py
reverse_agent/corpus_classifier.py
reverse_agent/corpus_static_audit.py
tests/test_corpus_loader.py
tests/test_corpus_classifier.py
tests/test_corpus_static_audit.py
project_state/corpus_static_audit.json
project_state/corpus_solver_gap_report.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

原则上不修改：

```text
reverse_agent/static_feature_extractor.py
sample_corpus/reverse/*
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

如果必须修改 `sample_corpus/reverse/*/metadata.json` 或 `case.json` 才能通过校验，先报告具体不一致原因；只允许做最小修复，不得重整 corpus 结构。

## 5. Required Audit

Codex 报告必须逐项回答：

```text
1. codex_execution_report.md 顶部是否为 ```json codex_report_summary。
2. pytest_result.txt 是否与 decision_20260531_fix_corpus_static_audit_validation_and_report 对齐。
3. 是否运行并记录 lint-decision。
4. 是否运行并记录 lint-report。
5. 是否运行并记录 git diff --check。
6. corpus_static_audit.run_audit() 是否先调用 validate_corpus。
7. validate_corpus 失败时 CLI 是否停止并返回非零或明确 BLOCKED。
8. tests 是否覆盖 sha256 mismatch 时 audit 不应成功。
9. tests 是否覆盖 size mismatch。
10. tests 是否覆盖 safe_to_run=true 被拒绝。
11. tests 是否覆盖 upload_allowed=false 被拒绝。
12. corpus_classifier.py 的 SEH feature 分支是否修复。
13. tests 是否覆盖 keyword_hits 中出现 exception/handler/seh 的 SEH 分类路径。
14. corpus_loader 是否校验 metadata.sample_path。
15. corpus_loader 是否校验 case.json input_value。
16. 是否没有执行任何 sample.exe。
17. 是否没有运行 runtime probe。
18. 是否没有修改 .codex-skills/。
19. 是否没有修改 samplereverse 主线。
20. 是否没有读取完整 solve_reports/。
21. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
```

## 6. Implementation Scope

### 6.1 修复 report fenced block

将 `project_state/codex_execution_report.md` 顶部：

```text
```json
```

改为：

```text
```json codex_report_summary
```

并确保 fenced JSON block 包含：

```text
schema_version
report_id
round_id
based_on_decision_id
status
acceptance_recommendation
files_changed
tests_ran
generated_artifacts
```

本轮报告 ID 必须是：

```text
report_20260531_fix_corpus_static_audit_validation_and_report
```

`based_on_decision_id` 必须是：

```text
decision_20260531_fix_corpus_static_audit_validation_and_report
```

### 6.2 更新 pytest_result.txt

`project_state/pytest_result.txt` 必须使用当前返工轮次：

```json
{
  "schema_version": 1,
  "decision_id": "decision_20260531_fix_corpus_static_audit_validation_and_report",
  "report_id": "report_20260531_fix_corpus_static_audit_validation_and_report",
  "round_id": "round_20260531_fix_corpus_static_audit_validation_and_report",
  "status": "PASSED",
  "tests_ran": []
}
```

正文必须记录所有实际命令输出。

### 6.3 修复 corpus_static_audit CLI

`run_audit(corpus_dir)` 或 CLI `main()` 必须先执行 corpus 校验。

建议实现：

```python
validation = validate_corpus(corpus_dir)
if not validation["valid"]:
    raise ValueError("Invalid corpus: ...")
```

CLI 入口必须把 invalid corpus 转换为非零退出，或在报告中明确 `BLOCKED`，但不得继续生成正常 `static_profiled` audit。

要求：

```text
1. sha256 mismatch 不得继续生成正常 audit。
2. size mismatch 不得继续生成正常 audit。
3. safe_to_run=true 不得继续生成正常 audit。
4. upload_allowed=false 不得继续生成正常 audit。
5. metadata.sample_path 不合法不得继续生成正常 audit。
6. case.json input_value 不合法不得继续生成正常 audit。
7. 错误信息必须说明具体 case_id 和原因。
```

### 6.4 修复 corpus_classifier SEH bug

修复错误逻辑：

```python
seh_hits = [h for h in features.keyword_hits if any(k in h["keyword"] for k in seh_hits)]
```

建议改为：

```python
seh_keywords = ["seh", "exception", "handler", "__except", "unhandled"]
seh_hits = [
    h for h in features.keyword_hits
    if any(
        k in h.get("keyword", "").lower()
        or k in h.get("context", "").lower()
        or k in h.get("source", "").lower()
        for k in seh_keywords
    )
]
```

并新增测试覆盖：

```text
keyword_hits=[{"keyword":"exception", "source":"SEH handler", "context":"exception handler"}]
```

预期分类：

```text
seh_or_exception
```

且不得抛出 `NameError`。

### 6.5 补强 corpus_loader 路径校验

`validate_corpus()` 必须检查：

```text
1. metadata.sample_path 存在。
2. metadata.sample_path 是相对路径。
3. metadata.sample_path 不包含 local_reverse_samples。
4. metadata.sample_path 规范化后指向 corpus_dir/<case_id>/sample.exe。
5. metadata.sample_path 不得逃逸 corpus_dir。
6. case.json 存在且可解析。
7. case.json 顶层 cases 存在且长度为 1。
8. case.json cases[0].case_id == case_id。
9. case.json cases[0].input_value == metadata.sample_path。
10. case.json input_value 不包含 local_reverse_samples。
11. case.json input_value 是相对 corpus 路径，不指向 corpus_dir 外部。
```

如果 manifest 和 metadata 的 sha256/size 同时存在，必须确保它们一致；真实 sample.exe hash/size 必须和 metadata 一致。

### 6.6 补强测试

新增或修改测试：

```text
tests/test_corpus_loader.py
tests/test_corpus_classifier.py
tests/test_corpus_static_audit.py
```

必须覆盖：

```text
1. sha256 mismatch -> validate_corpus invalid。
2. size mismatch -> validate_corpus invalid。
3. safe_to_run=true -> validate_corpus invalid。
4. upload_allowed=false -> validate_corpus invalid。
5. metadata.sample_path absolute path -> invalid。
6. metadata.sample_path outside corpus -> invalid。
7. metadata.sample_path contains local_reverse_samples -> invalid。
8. case.json input_value != metadata.sample_path -> invalid。
9. case.json still references local_reverse_samples -> invalid。
10. run_audit refuses invalid corpus。
11. CLI refuses invalid corpus。
12. SEH keyword feature branch returns seh_or_exception，不抛 NameError。
```

### 6.7 重新生成 corpus audit artifacts

修复后重新运行：

```text
python -m reverse_agent.corpus_static_audit --corpus-dir sample_corpus/reverse --out project_state/corpus_static_audit.json --gap-report project_state/corpus_solver_gap_report.md
```

要求：

```text
1. corpus_static_audit.json 明确 static_only=true。
2. corpus_static_audit.json 明确 executed_samples=false。
3. corpus_static_audit.json 明确 runtime_probe_used=false。
4. corpus_static_audit.json 不包含完整二进制 dump。
5. corpus_solver_gap_report.md 保持能力缺口摘要，不写成已解出结论。
```

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
1. 无法让 pytest_result.txt 与当前 decision/report/round 对齐。
2. lint-report 无法通过。
3. run_audit 无法在不执行样本的前提下校验 corpus。
4. 修复 SEH 分支需要扩大到反汇编或动态执行。
5. 必须修改 sample_corpus/reverse/*/sample.exe。
6. 必须修改 .codex-skills/。
7. 必须修改 samplereverse 主线。
8. 必须读取完整 solve_reports/。
9. 必须执行任何 sample.exe。
10. corpus_static_audit.json 无法在不包含完整 dump 的前提下生成。
```

完成条件：

```text
1. report 顶部 fenced block 名称正确。
2. pytest_result.txt 对齐当前返工轮次。
3. lint-decision / lint-report / git diff --check 均记录通过。
4. run_audit 会拒绝 invalid corpus。
5. CLI 会拒绝 invalid corpus。
6. SEH feature 分支 bug 修复并有测试覆盖。
7. metadata.sample_path 和 case.json input_value 被 validate_corpus 校验。
8. corpus_static_audit.json 重新生成。
9. corpus_solver_gap_report.md 重新生成。
10. 未执行任何 sample.exe。
11. 未运行 runtime probe。
12. 未修改 .codex-skills/。
13. 未修改 samplereverse 主线。
14. 所有规定测试通过并记录在 pytest_result.txt。
15. codex_execution_report.md 与本 decision_id / round_id 对齐。
```
