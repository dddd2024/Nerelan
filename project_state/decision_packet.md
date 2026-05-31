```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_rework_artifact_readability_and_report_scope",
  "round_id": "round_20260531_rework_artifact_readability_and_report_scope",
  "based_on_state_build_id": "state_20260527_153028_1d6dd81ecbd6",
  "based_on_state_digest": "1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮是上一轮 `decision_20260531_resume_samplereverse_handoff_exit_diagnosis` 的返工轮。GPT 审计结论为 `REWORK_REQUIRED`：上一轮诊断文本形式基本完整，但没有闭合 artifact 可读性证据链，并且 report 的变更清单疑似遗漏 `rc4enc_static_analysis_report.md`。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍只能作为状态派生建议，不能覆盖本 decision。

本轮仍属于 **samplereverse 逆向解题主线**，但不是新解题尝试。本轮只做 project_state/report 返工审计，不运行任何 runtime probe，不执行 sample，不扩大搜索。

## 1. Goal

修复上一轮验收链条中的两个阻断问题：

```text
1. 验证 artifact_index 标为 current 的四个 artifact 在 Codex 本地工作树中是否真实存在、是否可读。
2. 修正上一轮报告/诊断对 artifact 可读性的表述，避免把 artifact_index freshness 直接当作可读证据。
3. 解释 `rc4enc_static_analysis_report.md` 的来源，并修正 codex_execution_report 的 files_changed / generated_artifacts。
4. 重新写入 codex_execution_report.md 和 pytest_result.txt，使它们准确反映本轮返工。
```

本轮允许的输出：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/samplereverse_handoff_exit_diagnosis.md  # 仅在需要降级或修正文案时修改
```

可选输出：

```text
project_state/artifact_readability_rework_notes.md
```

不得新增求解 artifact，不得修改 solver/runtime/harness 代码。

## 2. Current Evidence

当前主线：

```text
reverse_solving
```

当前样本：

```text
samplereverse
```

当前 skill profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

当前 `task_packet.json` 的 `task` / `derived_task` 仍是旧派生任务：

```text
Diagnose bounded compare hook path reachability
```

它不是本轮执行权威。本轮执行权威是本 `decision_packet.md`。

上一轮 Codex 报告声称读取了以下 current artifacts：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_hook_path_reachability_audit/compare_hook_path_reachability_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
```

但 GPT 审计通过 GitHub contents API 复核时，至少 `run_manifest.json` 返回 `404 Not Found`。因此，上一轮报告中的 “current artifacts are readable / not required to rebuild project_state” 不能直接验收。

`artifact_index.json` 可以作为索引证据：它标记上述 run/artifacts 为 `freshness=current`；但 freshness 只说明索引状态，不等于当前仓库或本地工作树可读性。Codex 必须在本轮显式区分：

```text
artifact_index_freshness_current != artifact_file_readable
```

上一轮还存在报告范围问题：GPT 对比提交时发现实际仓库差异包含 `rc4enc_static_analysis_report.md`，但上一轮 `codex_execution_report.md` 的 `files_changed` / `generated_artifacts` 未列出该文件。Codex 必须解释其来源并修正报告。

## 3. Do Not Do

严禁：

```text
1. 不运行 sample.exe。
2. 不运行 samplereverse harness。
3. 不运行 runtime probe。
4. 不运行 Base64/RC4 breakpoint probe。
5. 不运行 pywinauto / GUI validation。
6. 不运行 IDA / OllyDbg / Frida。
7. 不回旧 sample_solver 盲搜。
8. 不扩大 beam / topN / budget / timeout。
9. 不重复 exact2 basin value-pool evaluation。
10. 不重复 H1/H3 fixed boundary contrast set。
11. 不重复 current 5-candidate transform trace consistency audit。
12. 不重复 compare return-site audit without using classification。
13. 不重复 producer material confirmation without instruction-level evidence。
14. 不把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当作 Base64/RC4 material producer，除非有新语义证据。
15. 不复用旧 [ebp-0x1170] 作为 real LHS source，除非有 provenance evidence。
16. 不读取完整 solve_reports/。
17. 不读取完整 PROJECT_PROGRESS_LOG.txt。
18. 不修改 .codex-skills/。
19. 不推进 corpus static audit 支线。
20. 不修改 sample_corpus/reverse/。
21. 不修改 reverse_agent/strategies/compare_aware_search.py。
22. 不修改 reverse_agent/harness.py。
23. 不修改 reverse_agent/profiles/samplereverse.py。
24. 不新增 `rc4enc` 解题分析文档，除非只是解释已经存在的未登记文件来源。
```

特别限制：

```text
1. 本轮只做 local file existence/readability audit 与 report correction。
2. 可以直接检查指定 artifact path 是否存在；这不等于扫描完整 solve_reports/。
3. 不得遍历 solve_reports/ 查找替代 artifact。
4. 如果指定 artifact 不存在或不可读，必须把上一轮诊断降级为基于 artifact_index 摘要的未验真诊断，或者报告 BLOCKED。
5. 不得继续声称 “all current artifact paths exist and are readable”，除非本轮用本地文件系统检查证明。
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
project_state/samplereverse_handoff_exit_diagnosis.md
```

必须有界检查这些路径是否存在、是否可读：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_hook_path_reachability_audit/compare_hook_path_reachability_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
```

必须检查是否存在未登记或未解释的文件：

```text
rc4enc_static_analysis_report.md
```

允许只读检查源码或 git 状态：

```text
git status --short
git diff --name-only HEAD~1..HEAD  # 或等价范围；只用于确认本轮变更范围
```

如果本地提交历史范围不一致，Codex 必须在报告中说明使用了什么命令确认变更范围。

不得读取：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
```

不得修改：

```text
.codex-skills/
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
reverse_agent/sample_solver.py
reverse_agent/harness.py
sample_corpus/reverse/
solve_reports/
```

## 5. Required Audit

Codex 报告必须逐项回答：

```text
1. 当前 mainline 是否为 reverse_solving。
2. task_packet.task / derived_task 是否只是派生任务，而不是当前执行权威。
3. 本 decision_packet.md 是否控制当前轮。
4. 当前 skill_profiles 是否为 reverse-agent-iteration@v2 + samplereverse-frontier@v2。
5. artifact_index 是否把 run_manifest 标为 current。
6. 本地工作树中 run_manifest.json 是否存在、是否可读。
7. artifact_index 是否把 summary 标为 current。
8. 本地工作树中 summary.json 是否存在、是否可读。
9. artifact_index 是否把 compare_hook_path_reachability_audit 标为 current。
10. 本地工作树中 compare_hook_path_reachability_audit.json 是否存在、是否可读。
11. artifact_index 是否把 compare_real_lhs_provenance_audit 标为 current。
12. 本地工作树中 compare_real_lhs_provenance_audit.json 是否存在、是否可读。
13. 是否明确区分 artifact freshness 与 file readability。
14. 如果任一 current artifact 不存在或不可读，是否把上一轮 diagnosis 降级或标记 BLOCKED。
15. 是否解释 `rc4enc_static_analysis_report.md` 的来源。
16. 如果 `rc4enc_static_analysis_report.md` 是本轮/上一轮 Codex 产物，是否补入 files_changed / generated_artifacts。
17. 是否没有运行 sample.exe。
18. 是否没有运行 runtime probe。
19. 是否没有运行 Base64/RC4 breakpoint probe。
20. 是否没有读取完整 solve_reports/。
21. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
22. 是否没有修改 .codex-skills/。
23. 是否没有修改 sample_corpus/reverse/。
24. 是否没有回旧 sample_solver 或扩大搜索预算。
25. 是否没有重复 negative_results 中已失败方向。
26. lint-decision 是否通过。
27. lint-report 是否通过。
28. git diff --check 是否通过。
```

## 6. Implementation Scope

### 6.1 Artifact readability audit

Codex 必须用本地文件系统直接检查四个指定 path。

允许方式示例：

```text
python - <<'PY'
from pathlib import Path
paths = [
  Path('solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json'),
  Path('solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json'),
  Path('solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_hook_path_reachability_audit/compare_hook_path_reachability_audit.json'),
  Path('solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json'),
]
for p in paths:
    print(p, 'exists=', p.exists(), 'is_file=', p.is_file())
    if p.is_file():
        print('size=', p.stat().st_size)
PY
```

只能检查这些精确 path，不得遍历 `solve_reports/`。

### 6.2 Diagnosis correction

如果四个 artifact 全部存在且可读：

```text
1. 保留上一轮 diagnosis 的核心结论。
2. 在 diagnosis 或 report 中补充一节 Artifact Readability Verification。
3. 明确说明 GitHub contents API 可能无法复核 solve_reports 本地 runtime artifacts，因此 GitHub 审计只能验证 project_state/report 文件，artifact 细节来自 Codex 本地工作树读取。
```

如果任一 artifact 不存在或不可读：

```text
1. 修改 samplereverse_handoff_exit_diagnosis.md，把相关 runtime 细节降级为 artifact_index/current_state 摘要证据，而不是已读取 artifact 证据。
2. 报告状态不得写 SUCCESS + ACCEPTED。
3. codex_report_summary.status 应为 BLOCKED 或 PARTIAL。
4. acceptance_recommendation 应为 REWORK_REQUIRED 或 BLOCKED。
5. Stop condition 应建议重新 build project_state：
   python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
```

### 6.3 Report scope correction

Codex 必须解释 `rc4enc_static_analysis_report.md`：

```text
1. 它是否存在于当前工作树。
2. 它是否是本轮 Codex 生成。
3. 它是否应当提交。
4. 如果已经提交但不属于本轮，应说明它来自哪个提交或外部操作。
5. 如果属于本轮/上一轮 Codex 改动，必须补入 codex_execution_report.md 的 files_changed / generated_artifacts。
6. 如果不应存在，不能擅自删除；只能报告需要人工或后续 decision 处理。
```

### 6.4 不实现新功能

本轮不得实现：

```text
1. new solver。
2. new guided pool search。
3. new candidate expansion。
4. new runtime hook / breakpoint probe。
5. sample_solver fallback。
6. rc4enc 解题文档扩写。
```

## 7. Tests

必须运行并记录：

```text
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

本轮通常不需要 pytest，因为不应修改代码。若 Codex 修改了任何 Python 源码或测试文件，必须运行相关 pytest，并在 `pytest_result.txt` 和 `codex_execution_report.md` 中记录。

`pytest_result.txt` 顶部必须包含 fenced JSON block，名称为：

```text
pytest_result_summary
```

至少包含：

```json
{
  "schema_version": 1,
  "decision_id": "decision_20260531_rework_artifact_readability_and_report_scope",
  "report_id": "<actual_report_id>",
  "round_id": "round_20260531_rework_artifact_readability_and_report_scope",
  "status": "PASSED_or_FAILED_or_BLOCKED",
  "tests_ran": []
}
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 的条件：

```text
1. 任一必须检查的 artifact path 不存在或不可读，并且无法仅靠 project_state 摘要安全修正 diagnosis。
2. project_state 文件互相冲突，例如 artifact_index 标 current，但 current_state 指向不同 selected run。
3. `lint-decision` 或 `lint-report` 失败且不能通过只修改 project_state 报告文件修复。
4. 发现 `rc4enc_static_analysis_report.md` 来源不明且可能污染本轮 diff，但无法在不删除文件的前提下解释。
```

如果停止，报告中必须给出下一步最小命令，不得泛泛要求“继续完善”。优先建议：

```text
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
```

验收标准：

```text
ACCEPTED 仅在以下条件全部满足时成立：
1. decision/report/pytest_result 三者 id 对齐。
2. 四个 current artifact 的本地存在性和可读性被明确审计，或诊断被正确降级为 BLOCKED/PARTIAL。
3. `rc4enc_static_analysis_report.md` 的来源被解释，report 文件清单被修正。
4. 未运行任何 runtime/sample/probe。
5. 未修改 .codex-skills/、sample_corpus/reverse/、solver/runtime/harness 代码。
6. lint-decision、lint-report、git diff --check 均通过。
```
