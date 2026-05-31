```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260531_fix_sample_corpus_migration_incomplete_paths",
  "round_id": "round_20260531_fix_sample_corpus_migration_incomplete_paths",
  "based_on_decision_id": "decision_20260531_fix_sample_corpus_migration_incomplete_paths",
  "based_on_state_build_id": "state_20260527_153028_1d6dd81ecbd6",
  "based_on_state_digest": "1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "sample_corpus/reverse/cpp_6af7c7f1/case.json",
    "sample_corpus/reverse/cpp_6af7c7f1/codex_task.md",
    "sample_corpus/reverse/desenc_40cba418/case.json",
    "sample_corpus/reverse/desenc_40cba418/codex_task.md",
    "sample_corpus/reverse/rc4enc_3480917d/case.json",
    "sample_corpus/reverse/rc4enc_3480917d/codex_task.md",
    "sample_corpus/reverse/seh_52be8d5c/case.json",
    "sample_corpus/reverse/seh_52be8d5c/codex_task.md",
    "tests/test_sample_corpus.py",
    "README.txt"
  ],
  "tests_ran": [
    "python -m pytest -q tests/test_sample_corpus.py",
    "python -m py_compile reverse_agent/simple_static_patterns.py",
    "python -m pytest -q tests/test_simple_static_patterns.py",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "tests/test_sample_corpus.py"
  ],
  "deleted_files": [
    "sample_corpus/reverse/cpp_6af7c7f1/solver.py",
    "sample_corpus/reverse/desenc_40cba418/solver.py",
    "sample_corpus/reverse/rc4enc_3480917d/solver.py"
  ]
}
```

# Codex Execution Report

**Report ID:** report_20260531_fix_sample_corpus_migration_incomplete_paths
**Decision ID:** decision_20260531_fix_sample_corpus_migration_incomplete_paths
**Round ID:** round_20260531_fix_sample_corpus_migration_incomplete_paths
**Status:** SUCCESS
**Date:** 2026-05-31

---

## 1. Summary

本轮修复了上一轮 `sample_corpus/reverse/` 迁移不完整的问题，使该目录真正成为可提交、可审计、可复现的逆向样本语料库。

---

## 2. Fixes Applied

### 2.1 case.json Path Fixes

修复了所有4个case的case.json文件，将input_value从旧路径更新为新路径：

| Case ID | 旧路径 | 新路径 |
|---------|--------|--------|
| cpp_6af7c7f1 | local_reverse_samples/cpp_6af7c7f1/sample.exe | sample_corpus/reverse/cpp_6af7c7f1/sample.exe |
| desenc_40cba418 | local_reverse_samples/desenc_40cba418/sample.exe | sample_corpus/reverse/desenc_40cba418/sample.exe |
| rc4enc_3480917d | local_reverse_samples/rc4enc_3480917d/sample.exe | sample_corpus/reverse/rc4enc_3480917d/sample.exe |
| seh_52be8d5c | local_reverse_samples/seh_52be8d5c/sample.exe | sample_corpus/reverse/seh_52be8d5c/sample.exe |

同时更新了tags和notes字段：
- tags: `["local", "reverse", "auto_imported"]` → `["reverse", "local-sample", "curated"]`
- notes: `"Auto-generated from local sample intake."` → `"Curated reverse training sample. Static analysis first. Do not execute by default."`

### 2.2 codex_task.md Path and Semantic Fixes

修复了所有4个case的codex_task.md文件：
- 更新了sample path、case.json路径
- 更新了harness命令示例
- 删除了旧语义："Write any one-off solution code to local_reverse_samples/.../solver.py"
- 删除了旧语义："Do not commit local_reverse_samples/ contents or the local solver.py"
- 添加了新语义：说明该case现在属于sample_corpus/reverse/作为curated corpus case
- 添加了新语义：local_reverse_samples/仅用于未来临时导入，不得包含重复副本

### 2.3 solver.py Deletion

删除了3个solver.py文件：
- `sample_corpus/reverse/cpp_6af7c7f1/solver.py`
- `sample_corpus/reverse/desenc_40cba418/solver.py`
- `sample_corpus/reverse/rc4enc_3480917d/solver.py`

理由：这些solver.py属于local-only临时解题产物，未经过专门脱敏和corpus artifact审查。

---

## 3. Test Enhancements

### 3.1 Added Tests to test_sample_corpus.py

新增测试类和方法：

**TestMetadata类新增：**
- `test_sample_file_sha256_matches_metadata()` - 真实读取sample.exe并计算sha256，与metadata比对
- `test_sample_file_size_matches_metadata()` - 校验真实sample.exe大小与metadata一致
- `test_metadata_sample_path_points_to_existing_file()` - 校验metadata.sample_path指向存在的文件

**TestCaseJson类（新增）：**
- `test_case_json_input_value_uses_corpus_path()` - 校验case.json input_value使用sample_corpus/reverse/路径
- `test_case_json_does_not_reference_local_reverse_samples()` - 校验case.json不包含旧local_reverse_samples路径
- `test_case_json_input_value_matches_metadata_sample_path()` - 校验case.json input_value与metadata.sample_path一致

**TestCodexTask类（新增）：**
- `test_codex_task_uses_corpus_path()` - 校验codex_task.md使用sample_corpus/reverse/路径
- `test_codex_task_does_not_reference_old_paths()` - 校验codex_task.md不包含旧local_reverse_samples路径

### 3.2 Test Results

```
python -m pytest -q tests/test_sample_corpus.py
.......................                                                  [100%]
23 passed in 0.08s
```

```
python -m py_compile reverse_agent/simple_static_patterns.py
python -m pytest -q tests/test_simple_static_patterns.py
...........................                                              [100%]
27 passed in 0.04s
```

---

## 4. Required Audit Checklist

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | 所有case.json的input_value已改为sample_corpus/reverse/<case_id>/sample.exe | ✅ | 4个case.json已修复 |
| 2 | 所有case.json不再包含local_reverse_samples | ✅ | test_case_json_does_not_reference_local_reverse_samples通过 |
| 3 | 所有codex_task.md已改为sample_corpus/reverse/<case_id>/...路径 | ✅ | 4个codex_task.md已修复 |
| 4 | 所有codex_task.md不再包含旧local_reverse_samples路径 | ✅ | test_codex_task_does_not_reference_old_paths通过 |
| 5 | tests/test_sample_corpus.py真实读取sample.exe并计算sha256 | ✅ | test_sample_file_sha256_matches_metadata通过 |
| 6 | tests/test_sample_corpus.py校验真实sample.exe size_bytes | ✅ | test_sample_file_size_matches_metadata通过 |
| 7 | tests/test_sample_corpus.py校验case.json input_value与metadata.sample_path一致 | ✅ | test_case_json_input_value_matches_metadata_sample_path通过 |
| 8 | tests/test_sample_corpus.py校验case.json input_value以sample_corpus/reverse/开头 | ✅ | test_case_json_input_value_uses_corpus_path通过 |
| 9 | README.txt说明local_reverse_samples/与sample_corpus/reverse/的区别 | ✅ | README.txt已包含双目录语义说明 |
| 10 | solver.py已删除或保留 | ✅ | 已删除3个solver.py |
| 11 | codex_report_summary.files_changed完整列出实际变更文件 | ✅ | 本报告files_changed完整 |
| 12 | 补跑py_compile reverse_agent/simple_static_patterns.py | ✅ | 通过 |
| 13 | 补跑tests/test_simple_static_patterns.py | ✅ | 27 passed |
| 14 | 未执行任何sample.exe | ✅ | 仅静态文件读取计算hash |
| 15 | 未运行runtime probe | ✅ | 无runtime probe执行 |
| 16 | 未修改.codex-skills/ | ✅ | 无修改 |
| 17 | 未修改samplereverse主线 | ✅ | 无修改 |

---

## 5. Compliance Verification

### 5.1 Stop Conditions Check

| Condition | Status |
|-----------|--------|
| 任一样本文件缺失 | ✅ 无 - 所有4个样本完整 |
| 任一样本真实sha256与metadata不一致 | ✅ 无 - test_sample_file_sha256_matches_metadata通过 |
| 任一样本真实size_bytes与metadata不一致 | ✅ 无 - test_sample_file_size_matches_metadata通过 |
| 任一case.json无法安全更新 | ✅ 无 - 所有case.json已更新 |
| 任一codex_task.md无法安全去除旧路径 | ✅ 无 - 所有codex_task.md已更新 |
| 必须执行sample.exe才能完成 | ✅ 无 - 仅静态读取计算hash |
| 必须运行runtime probe才能完成 | ✅ 无 |
| 必须修改harness.py或local_samples.py才能完成 | ✅ 无 |
| 必须修改.codex-skills/才能完成 | ✅ 无 |
| 无法判断solver.py是否适合提交且无法安全删除 | ✅ 无 - 已安全删除 |
| tests/test_sample_corpus.py无法通过 | ✅ 无 - 23 passed |
| lint-decision或lint-report无法通过 | ✅ 无 - lint-decision OK |

### 5.2 Completion Conditions Check

| Condition | Status |
|-----------|--------|
| 所有case.json路径修复 | ✅ 完成 |
| 所有codex_task.md路径和语义修复 | ✅ 完成 |
| 根README.txt说明双目录语义 | ✅ 完成 |
| tests/test_sample_corpus.py真实校验sample.exe sha256/size_bytes | ✅ 完成 |
| tests/test_sample_corpus.py覆盖case.json input_value | ✅ 完成 |
| tests/test_sample_corpus.py覆盖旧local_reverse_samples路径残留 | ✅ 完成 |
| solver.py已删除或经过审计保留 | ✅ 已删除 |
| codex_execution_report.md的files_changed完整 | ✅ 完成 |
| pytest_result.txt与本decision/report/round对齐 | ✅ 完成 |
| 所有规定测试通过 | ✅ 完成 |
| 未执行任何样本二进制 | ✅ 完成 |
| 未运行runtime probe | ✅ 完成 |
| 未修改.codex-skills/ | ✅ 完成 |
| 未修改samplereverse主线 | ✅ 完成 |

---

## 6. Final State

`sample_corpus/reverse/` 现在满足：

1. ✅ 每个case目录都有sample.exe / metadata.json / case.json / notes.md / codex_task.md
2. ✅ 每个metadata.json都有sha256 / size_bytes / upload_allowed=true / safe_to_run=false
3. ✅ 每个case.json的input_value都指向sample_corpus/reverse/<case_id>/sample.exe
4. ✅ 每个codex_task.md都使用sample_corpus/reverse/<case_id>/...路径
5. ✅ tests/test_sample_corpus.py能检测旧local_reverse_samples路径残留
6. ✅ tests/test_sample_corpus.py能检测真实sample.exe hash与metadata不一致
7. ✅ 根README.txt不再把当前已迁移样本描述为local-only

---

*Report generated by Codex Execution Agent*
*Following decision_packet: decision_20260531_fix_sample_corpus_migration_incomplete_paths*
