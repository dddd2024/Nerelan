```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_fix_sample_corpus_migration_incomplete_paths",
  "round_id": "round_20260531_fix_sample_corpus_migration_incomplete_paths",
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

本轮属于 **engineering_branch**。目标是修复上一轮 `sample_corpus/reverse/` 迁移不完整问题，使该目录真正成为可提交、可审计、可复现的逆向样本语料库。

本轮只做 corpus 迁移修复、文档语义修复、测试补强和 report 对齐；不推进 `samplereverse` 解题，不运行任何样本二进制，不运行 runtime probe。

## 1. Goal

修复上一轮迁移后的阻断问题：

```text
1. 修复 sample_corpus/reverse/*/case.json 中仍指向 local_reverse_samples/ 的 input_value。
2. 修复 sample_corpus/reverse/*/codex_task.md 中仍指向 local_reverse_samples/ 的路径、harness 命令和旧语义。
3. 补强 tests/test_sample_corpus.py，使其真实读取 sample.exe 并校验 sha256 / size_bytes。
4. 补强 tests/test_sample_corpus.py，使其校验 case.json input_value 与 metadata.sample_path 一致，并且指向 sample_corpus/reverse/。
5. 更新根 README.txt，明确 local_reverse_samples/ 与 sample_corpus/reverse/ 的职责区别。
6. 审计 sample_corpus/reverse/*/solver.py 是否应提交；默认应删除，除非能证明它是经过脱敏的 curated artifact。
7. 修正 project_state/codex_execution_report.md，使 codex_report_summary.files_changed 完整列出实际变更文件。
8. 因上一轮修改了 reverse_agent/simple_static_patterns.py，本轮必须补跑 simple_static_patterns 相关测试。
```

完成后，`sample_corpus/reverse/` 应满足：

```text
1. 每个 case 目录都有 sample.exe / metadata.json / case.json / notes.md / codex_task.md。
2. 每个 metadata.json 都有 sha256 / size_bytes / upload_allowed=true / safe_to_run=false。
3. 每个 case.json 的 input_value 都指向 sample_corpus/reverse/<case_id>/sample.exe。
4. 每个 codex_task.md 都使用 sample_corpus/reverse/<case_id>/... 路径。
5. tests/test_sample_corpus.py 能检测旧 local_reverse_samples 路径残留。
6. tests/test_sample_corpus.py 能检测真实 sample.exe hash 与 metadata 不一致。
7. 根 README.txt 不再把当前已迁移样本描述为 local-only。
```

## 2. Current Evidence

当前主线：`engineering_branch`。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍是旧 `reverse_solving` 状态派生建议，不自动覆盖本 decision。

当前 skill profiles：

```text
reverse-agent-iteration@v2
```

不使用：

```text
samplereverse-frontier@v2
```

原因：本轮不推进 `samplereverse` 样本，不涉及 candidate、frontier、runtime evidence 或 artifact freshness 推进。

artifact freshness：

```text
1. 本轮不依赖 solve_reports/ artifact 作为当前证据。
2. artifact_index.latest_artifacts_v2 中的 samplereverse runtime artifacts 不作为本轮实现依据。
3. 不得把 stale / missing runtime artifact 当作本轮 corpus 迁移证据。
```

上一轮审计结论为 `REWORK_REQUIRED`，关键证据如下：

```text
1. sample_corpus/reverse/*/case.json 仍引用 local_reverse_samples/<case_id>/sample.exe。
2. sample_corpus/reverse/*/codex_task.md 仍引用 local_reverse_samples/<case_id>/sample.exe、case.json 和 solver.py。
3. tests/test_sample_corpus.py 只校验 manifest.sha256 == metadata.sha256，没有真实读取 sample.exe 计算 sha256。
4. tests/test_sample_corpus.py 没有校验 case.json input_value。
5. README.txt 仍只描述 local_reverse_samples/ 为本地训练样本目录，没有加入 sample_corpus/reverse/ 的可提交 corpus 语义。
6. project_state/codex_execution_report.md 的 files_changed 不完整，漏列大量实际提交的 corpus 文件。
7. sample_corpus/reverse/*/solver.py 被提交，但上一轮 decision 未明确允许提交 solver.py。
8. reverse_agent/simple_static_patterns.py 被修改，但 pytest_result.txt 未记录 py_compile 或 tests/test_simple_static_patterns.py。
```

## 3. Do Not Do

严禁：

```text
1. 不执行任何 sample.exe。
2. 不运行 IDA / OllyDbg / Frida / runtime probe。
3. 不运行 samplereverse harness。
4. 不读取完整 solve_reports/。
5. 不读取完整 PROJECT_PROGRESS_LOG.txt。
6. 不修改 .codex-skills/。
7. 不修改 reverse_agent/strategies/compare_aware_search.py。
8. 不修改 reverse_agent/profiles/samplereverse.py。
9. 不修改 reverse_agent/harness.py。
10. 不修改 reverse_agent/local_samples.py。
11. 不提交 solve_reports/。
12. 不把 local_reverse_samples/ 重新提交为样本副本。
13. 不把 stale / missing artifact 当作 current evidence。
14. 不把本轮任务扩大为逆向解题或 runtime 能力提升。
```

特别限制：

```text
1. 所有上传样本 safe_to_run 必须保持 false。
2. 所有上传样本 upload_allowed 必须保持 true。
3. 本轮只做路径修复、语义修复、测试补强和报告对齐。
4. 如果必须执行样本二进制才能完成，立即停止并报告 BLOCKED。
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

必须本地检查：

```text
.gitignore
README.txt
sample_corpus/reverse/manifest.json
sample_corpus/reverse/README.md
sample_corpus/reverse/*/metadata.json
sample_corpus/reverse/*/case.json
sample_corpus/reverse/*/codex_task.md
sample_corpus/reverse/*/notes.md
sample_corpus/reverse/*/analysis_notes.md
sample_corpus/reverse/*/solve_result.json
sample_corpus/reverse/*/solver.py
sample_corpus/reverse/*/sample.exe
tests/test_sample_corpus.py
reverse_agent/simple_static_patterns.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许修改：

```text
README.txt
sample_corpus/reverse/README.md
sample_corpus/reverse/*/case.json
sample_corpus/reverse/*/codex_task.md
sample_corpus/reverse/*/metadata.json      # 仅在发现路径/字段不一致时修复
sample_corpus/reverse/manifest.json        # 仅在发现路径/字段不一致时修复
tests/test_sample_corpus.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许删除：

```text
sample_corpus/reverse/*/solver.py
```

删除条件：这些 solver.py 属于 local-only 临时解题产物，未经过专门脱敏和 corpus artifact 审查。

允许有条件保留：

```text
sample_corpus/reverse/*/analysis_notes.md
sample_corpus/reverse/*/solve_result.json
sample_corpus/reverse/*/solver.py
```

保留条件：内容必须不包含本地绝对敏感路径、不包含完整反汇编 dump、不包含不适合提交的临时运行数据；如果保留 solver.py，必须在 README/report 中说明它是 curated artifact 而不是临时 solver。

不应修改：

```text
.codex-skills/
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
reverse_agent/harness.py
reverse_agent/local_samples.py
```

如果必须修改 `harness.py` 或 `local_samples.py` 才能完成，停止并报告 `BLOCKED`，不要扩大范围。

## 5. Required Audit

Codex 报告必须回答：

```text
1. 所有 case.json 的 input_value 是否已经改为 sample_corpus/reverse/<case_id>/sample.exe。
2. 所有 case.json 是否不再包含 local_reverse_samples。
3. 所有 codex_task.md 是否已经改为 sample_corpus/reverse/<case_id>/... 路径。
4. 所有 codex_task.md 是否不再包含旧 local_reverse_samples/<case_id>/sample.exe、case.json、solver.py 路径。
5. tests/test_sample_corpus.py 是否真实读取每个 sample.exe 并计算 sha256。
6. tests/test_sample_corpus.py 是否校验真实 sample.exe size_bytes。
7. tests/test_sample_corpus.py 是否校验 case.json input_value 与 metadata.sample_path 一致。
8. tests/test_sample_corpus.py 是否校验 case.json input_value 以 sample_corpus/reverse/ 开头。
9. README.txt 是否说明 local_reverse_samples/ 与 sample_corpus/reverse/ 的区别。
10. solver.py 是删除还是保留；如果保留，为什么可提交，是否已脱敏。
11. codex_report_summary.files_changed 是否完整列出实际变更文件。
12. 是否补跑 py_compile reverse_agent/simple_static_patterns.py。
13. 是否补跑 tests/test_simple_static_patterns.py。
14. 是否没有执行任何 sample.exe。
15. 是否没有运行 runtime probe。
16. 是否没有修改 .codex-skills/。
17. 是否没有修改 samplereverse 主线。
```

## 6. Implementation Scope

### 6.1 修复 case.json

对每个 case：

```text
sample_corpus/reverse/<case_id>/case.json
```

将：

```json
"input_value": "local_reverse_samples/<case_id>/sample.exe"
```

改为：

```json
"input_value": "sample_corpus/reverse/<case_id>/sample.exe"
```

同时建议把 tags 中的旧 `local` / `auto_imported` 语义改成更适合 corpus 的标签：

```json
"tags": [
  "reverse",
  "local-sample",
  "curated"
]
```

每个 case.json 应保持：

```json
{
  "cases": [
    {
      "case_id": "<case_id>",
      "input_value": "sample_corpus/reverse/<case_id>/sample.exe",
      "expected_flag": "",
      "category": "unknown",
      "tags": [
        "reverse",
        "local-sample",
        "curated"
      ],
      "notes": "Curated reverse training sample. Static analysis first. Do not execute by default."
    }
  ]
}
```

### 6.2 修复 codex_task.md

每个 `codex_task.md` 必须改为新 corpus 语义：

```text
sample path: sample_corpus/reverse/<case_id>/sample.exe
case.json: sample_corpus/reverse/<case_id>/case.json
```

harness 示例命令使用：

```powershell
python -m reverse_agent.harness --dataset sample_corpus\reverse\<case_id>\case.json --run-name corpus_<case_id>_static --analysis-mode "Static Analysis" --case-id <case_id>
```

删除或改写旧语义：

```text
1. 删除 “Write any one-off solution code to local_reverse_samples/.../solver.py”。
2. 删除 “Do not commit local_reverse_samples/ contents or the local solver.py”。
3. 不得继续把本 case 描述为 local-only 样本。
```

替换为：

```text
1. This case now belongs to sample_corpus/reverse/ as a curated, upload-approved corpus case.
2. local_reverse_samples/ is only for future temporary intake and must not contain a duplicate copy of this case.
3. Keep analysis static-first. Do not execute sample.exe by default.
4. Do not run IDA / OllyDbg / Frida / runtime probes unless a future decision explicitly authorizes it.
```

### 6.3 审计或删除 solver.py

默认执行策略：删除 `sample_corpus/reverse/*/solver.py`。

理由：上一轮正式 decision 只允许新增 case 文件、metadata、case、notes、codex_task、README、manifest 和测试；`solver.py` 不在默认允许提交范围内。

如果 Codex 判断必须保留 solver.py，则必须同时完成：

```text
1. 在 sample_corpus/reverse/README.md 增加 solver.py 提交政策。
2. 在每个保留 solver.py 的 case notes.md 或 metadata.json 中说明 solver.py 是 curated artifact，不是临时运行产物。
3. 确认 solver.py 不包含本地绝对路径。
4. 确认 solver.py 不执行 sample.exe。
5. 确认 solver.py 不包含完整反汇编 dump 或敏感临时数据。
6. 在 codex_execution_report.md 中完整列出保留理由。
```

如果无法判断 solver.py 是否适合提交，删除它们。

### 6.4 更新根 README.txt

必须加入或修正以下语义：

```text
local_reverse_samples/：未来临时本地导入目录，被 .gitignore 忽略，不上传；用于暂存用户新导入、尚未审计或尚未明确允许上传的逆向样本。

sample_corpus/reverse/：可提交、可审计、可复现的精选逆向样本语料库；只保存用户明确允许上传、已补齐 metadata/case/notes/codex_task 的 curated 样本。
```

根 README 中原来关于 `local_reverse_samples/` 的段落不能让读者误以为当前已上传样本仍应存在于 local-only 目录。

### 6.5 加强 tests/test_sample_corpus.py

必须新增或修复以下测试：

```text
1. test_sample_file_sha256_matches_metadata
2. test_sample_file_size_matches_metadata
3. test_case_json_input_value_matches_metadata_sample_path
4. test_case_json_input_value_uses_corpus_path
5. test_case_json_does_not_reference_local_reverse_samples
6. test_codex_task_uses_corpus_path
7. test_codex_task_does_not_reference_old_case_paths
8. test_metadata_sample_path_points_to_existing_file
```

测试实现要求：

```python
import hashlib

actual_sha256 = hashlib.sha256(sample_path.read_bytes()).hexdigest()
assert actual_sha256 == metadata["sha256"]
assert sample_path.stat().st_size == metadata["size_bytes"]
```

`case.json` 校验要求：

```python
case = case_json["cases"][0]
assert case["case_id"] == case_id
assert case["input_value"] == metadata["sample_path"]
assert case["input_value"].startswith("sample_corpus/reverse/")
assert "local_reverse_samples" not in case["input_value"]
```

`codex_task.md` 校验要求：

```python
assert f"sample_corpus/reverse/{case_id}/sample.exe" in content
assert f"local_reverse_samples/{case_id}/sample.exe" not in content
assert f"local_reverse_samples\\{case_id}\\sample.exe" not in content
```

### 6.6 修复 codex_execution_report.md

更新 `project_state/codex_execution_report.md`：

```text
1. codex_report_summary.based_on_decision_id 必须等于 decision_20260531_fix_sample_corpus_migration_incomplete_paths。
2. round_id 必须等于 round_20260531_fix_sample_corpus_migration_incomplete_paths。
3. status 根据实际执行结果填写 SUCCESS / BLOCKED。
4. files_changed 必须完整列出实际变更文件，包括 case.json / codex_task.md / README / tests / project_state files，以及删除的 solver.py（如有）。
5. tests_ran 必须完整列出实际运行命令。
6. generated_artifacts 必须只列出本轮实际生成或更新的产物。
7. 报告正文必须包含 Required Audit 中所有问题的回答。
```

### 6.7 更新 pytest_result.txt

`project_state/pytest_result.txt` 必须包含 fenced JSON block：

```json
{
  "schema_version": 1,
  "decision_id": "decision_20260531_fix_sample_corpus_migration_incomplete_paths",
  "report_id": "report_20260531_fix_sample_corpus_migration_incomplete_paths",
  "round_id": "round_20260531_fix_sample_corpus_migration_incomplete_paths",
  "status": "PASSED",
  "tests_ran": []
}
```

并记录所有实际命令和结果。

## 7. Tests

必须运行：

```text
python -m pytest -q tests/test_sample_corpus.py
python -m py_compile reverse_agent/simple_static_patterns.py
python -m pytest -q tests/test_simple_static_patterns.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

不要求运行：

```text
python -m pytest -q
任何 sample.exe
IDA / OllyDbg / Frida runtime probe
samplereverse harness
Base64/RC4 runtime probe
```

如果 Codex 未修改 `reverse_agent/simple_static_patterns.py`，仍必须补跑 `py_compile` 和 `tests/test_simple_static_patterns.py`，因为上一轮已经修改过该文件但没有记录对应测试。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 任一样本文件缺失。
2. 任一样本真实 sha256 与 metadata 不一致。
3. 任一样本真实 size_bytes 与 metadata 不一致。
4. 任一 case.json 无法安全更新为 sample_corpus/reverse/...。
5. 任一 codex_task.md 无法安全去除旧 local_reverse_samples 路径。
6. 必须执行 sample.exe 才能完成。
7. 必须运行 runtime probe 才能完成。
8. 必须修改 harness.py 或 local_samples.py 才能完成。
9. 必须修改 .codex-skills/ 才能完成。
10. 无法判断 solver.py 是否适合提交，且无法安全删除。
11. tests/test_sample_corpus.py 无法通过。
12. lint-decision 或 lint-report 无法通过。
```

完成条件：

```text
1. 所有 case.json 路径修复。
2. 所有 codex_task.md 路径和语义修复。
3. 根 README.txt 说明 local_reverse_samples/ 与 sample_corpus/reverse/ 的双目录语义。
4. tests/test_sample_corpus.py 真实校验 sample.exe sha256 / size_bytes。
5. tests/test_sample_corpus.py 覆盖 case.json input_value。
6. tests/test_sample_corpus.py 覆盖旧 local_reverse_samples 路径残留。
7. solver.py 已删除，或经过明确审计后作为 curated artifact 保留。
8. codex_execution_report.md 的 files_changed 完整。
9. pytest_result.txt 与本 decision / report / round 对齐。
10. 所有规定测试通过。
11. 未执行任何样本二进制。
12. 未运行 runtime probe。
13. 未修改 .codex-skills/。
14. 未修改 samplereverse 主线。
```
