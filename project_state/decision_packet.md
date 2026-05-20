```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase2_completion_audit_20260520",
  "round_id": "round_20260520_phase2_completion_audit",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 2 收尾审计：确认 Phase 2A-D 已形成闭环，产出一份有界 completion report，并把遗留问题分流到 Phase 3 backlog。注意：本轮不是 Phase 2E，不新增 Phase 2 子阶段。

本轮属于工程架构改造支线中的 harness 可复现 / 可恢复 / 可比较方向。不要推进 `samplereverse` 逆向解题，不运行 runtime probe，不修改 GPT/Codex 协作协议，不新增 harness 功能。

## 1. Goal

Phase 2 的正式范围只有 A-D：

```text
Phase 2A = harness resume 语义
Phase 2B = case_result artifact_manifest
Phase 2C = harness compare
Phase 2D = resource_budget 记录
```

本轮目标是做 Phase 2 completion audit，而不是继续扩展 Phase 2：

```text
1. 审计 Phase 2A-D 每轮 decision/report/pytest/round archive 是否完整。
2. 确认 A-D 的核心功能仍能被测试覆盖。
3. 生成 docs/phase2_harness_reproducibility_completion.md，总结 Phase 2 已完成内容、测试证据、已知限制和后续 Phase 3 backlog。
4. 明确修正命名：不要再使用 Phase 2E；此前提到的 compare strict / path schema / round commit 语义归入 Phase 3 backlog 或 post-Phase-2 hardening。
5. 不修改 harness 功能代码，不修改 project_state 协作协议，不运行逆向 runtime。
```

Phase 2 completion report 必须包含：

```text
1. Phase 2 scope：A-D 的边界和目标。
2. Phase 2A summary：resume terminal-only / all-existing / rerun-status 的完成状态和测试证据。
3. Phase 2B summary：case_result artifact_manifest 与 project_state ingestion 的完成状态和测试证据。
4. Phase 2C summary：harness compare 的完成状态和测试证据。
5. Phase 2D summary：resource_budget manifest recording 的完成状态和测试证据。
6. Acceptance matrix：每个子阶段的 GPT 审查结论、report_id、round_id、主要测试结果。
7. Remaining limitations：只列限制，不在本轮修复。
8. Phase 3 backlog：把 compare strict、artifact path schema、round_manifest commit 语义、archive diff 可回放性归入 Phase 3。
9. Explicit closure statement：Phase 2 A-D closed; no Phase 2E.
```

## 2. Current Evidence

当前任务主线：工程架构改造支线，具体为 Phase 2 收尾审计。

当前 live state：

```text
round_id = round_20260520_052928
state_build_id = state_20260520_052928_8a77e6637c6c
state_digest = 8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d
source_harness_run = sr_lhs_thread_follow_timing_20260520_r4
```

当前 `task_packet.json` 仍显示样本派生任务：

```text
task = Improve compare lhs last-writer instrumentation
derived_task = Improve compare lhs last-writer instrumentation
task_source = derived_from_sample_artifacts
execution_scope = decision_packet_controls_current_round
active_decision_packet = project_state/decision_packet.md
```

这说明 `task_packet.task` 不是本轮 Codex 的执行任务；本轮执行权威来自 `project_state/decision_packet.md`。

Phase 2D 当前状态：

```text
decision_id = decision_phase2d_harness_resource_budget_20260520
report_id = report_phase2d_harness_resource_budget_20260520
report_status = SUCCESS
acceptance_recommendation = ACCEPTED
full pytest = 384 passed
lint-decision = OK
lint-report = OK
lint-handoff = OK
handoff_state = REVIEW_COMPLETE
```

Phase 2D report 的 `next_suggested_task` 曾提到 “Phase 2E compare strict/path/round commit cleanup”。该命名应在本轮 completion report 中修正：这些不是 Phase 2E，而是 Phase 3 backlog / post-Phase-2 hardening。

当前 artifact_index 现状：

```text
latest_artifacts_v2 已存在。
compare_probe / compare_probe_log / compare_real_lhs_provenance_audit / summary / run_manifest 等当前 run artifact 标记为 current。
frontier_summary / function_semantic_audit / base64_rc4_static_point_discovery 等 legacy tool_artifacts 标记为 stale。
多个未生成 artifact 标记为 missing。
```

这些 artifact 只用于说明状态，不是本轮要消费的逆向证据。本轮不要重新扫描完整 `solve_reports/`。

## 3. Do Not Do

不要做以下事情：

```text
不要把本轮命名为 Phase 2E。
不要新增 Phase 2 子阶段。
不要推进 samplereverse 解题。
不要运行 Base64/RC4 breakpoint probe。
不要运行任何逆向 runtime sidecar。
不要运行 pipeline 或模型调用作为必要测试。
不要修改 reverse_agent/harness.py，除非只是无法避免的文档字符串 typo；原则上本轮不改代码。
不要修改 reverse_agent/project_state.py。
不要修改 reverse_agent/strategies/compare_aware_search.py。
不要修改 reverse_agent/olly_scripts/*。
不要修改 reverse_agent/pipeline.py。
不要修改 reverse_agent/tool_runners.py。
不要扩大 beam、topN、budget、timeout、frontier iteration。
不要回旧 sample_solver。
不要提交完整 solve_reports。
不要默认读取完整 PROJECT_PROGRESS_LOG.txt。
不要默认读取完整 solve_reports。
不要修改 GPT/Codex 协作协议。
不要修改 decision_meta / codex_report_summary schema。
不要修改 lint-decision / lint-report / lint-handoff 语义。
不要实现 compare strict。
不要重构 artifact_manifest path schema。
不要修改 round_manifest commit 语义。
不要修改 archive-round / git_diff 行为。
不要实现 resource enforcement、process kill、artifact cleanup、candidate truncation 或 context pack truncation。
不要实现 queue / backpressure / worker pool。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph。
不要引入 PostgreSQL / Redis / Kubernetes。
```

## 4. Files To Inspect

必须审计：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/rounds/round_20260520_phase2a_harness_resume_policy/round_manifest.json
project_state/rounds/round_20260520_phase2a_harness_resume_policy/codex_execution_report.md
project_state/rounds/round_20260520_phase2a_harness_resume_policy/pytest_result.txt
project_state/rounds/round_20260520_phase2b_case_artifact_manifest/round_manifest.json
project_state/rounds/round_20260520_phase2b_case_artifact_manifest/codex_execution_report.md
project_state/rounds/round_20260520_phase2b_case_artifact_manifest/pytest_result.txt
project_state/rounds/round_20260520_phase2c_harness_compare/round_manifest.json
project_state/rounds/round_20260520_phase2c_harness_compare/codex_execution_report.md
project_state/rounds/round_20260520_phase2c_harness_compare/pytest_result.txt
project_state/rounds/round_20260520_phase2d_harness_resource_budget/round_manifest.json
project_state/rounds/round_20260520_phase2d_harness_resource_budget/codex_execution_report.md
project_state/rounds/round_20260520_phase2d_harness_resource_budget/pytest_result.txt
```

允许检查但不要修改代码：

```text
reverse_agent/harness.py
tests/test_harness_resume.py
tests/test_harness_artifact_manifest.py
tests/test_harness_compare.py
tests/test_harness_resource_budget.py
```

允许新增：

```text
docs/phase2_harness_reproducibility_completion.md
```

不要默认读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. Phase 2A-D 的 round_id / decision_id / report_id 是否都存在且可读。
2. 每个 Phase 2 round 的 codex_report_summary 是否存在，status 是否 SUCCESS。
3. 每个 Phase 2 report 的 based_on_decision_id 是否匹配对应 archived decision。
4. 每个 Phase 2 round 的 pytest_result.txt 是否记录真实测试。
5. 每个 Phase 2 round 的 round_manifest.json 是否存在。
6. Phase 2D 当前 live lint-decision / lint-report / lint-handoff 是否 OK。
7. Phase 2A-D 是否修改过禁止文件，例如 compare_aware_search.py、olly_scripts 或 project_state 协作协议。
8. Phase 2A-D 是否运行过逆向 runtime probe；如果没有，应明确说明没有推进 samplereverse runtime。
9. Phase 2A-D 的功能边界是否对应原始 Phase 2 目标：resume、artifact_manifest、compare、resource_budget。
10. Phase 2D report 中提到 Phase 2E 的命名是否需要在 completion report 中纠正。
11. 哪些问题应进入 Phase 3 backlog，而不是继续叫 Phase 2E。
12. 本轮是否可以只新增 docs completion report 和更新 live report/pytest/archive，不改功能代码。
```

## 6. Implementation Scope

允许修改：

```text
docs/phase2_harness_reproducibility_completion.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许重新生成或更新：

```text
project_state/rounds/round_20260520_phase2_completion_audit/*
```

不要修改：

```text
reverse_agent/harness.py
reverse_agent/project_state.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
reverse_agent/pipeline.py
reverse_agent/tool_runners.py
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/schema.md
```

如果 Codex 发现必须改代码才能完成，应停止并报告。本轮是收尾审计和文档化，不是功能实现。

### 6.1 Completion report structure

新增 `docs/phase2_harness_reproducibility_completion.md`，建议结构：

```text
# Phase 2 Harness Reproducibility Completion Report

## Scope
- Phase 2A: resume semantics
- Phase 2B: case artifact manifest
- Phase 2C: harness compare
- Phase 2D: resource budget recording
- No Phase 2E

## Acceptance Matrix
| phase | decision_id | report_id | round_id | status | tests | GPT review result |

## Completed Capabilities
...

## Evidence
- archived report paths
- pytest summaries
- lint summaries

## Known Limitations
...

## Phase 3 Backlog
- compare strict behavior for missing runs
- artifact_manifest path normalization
- round_manifest source_state_git_commit vs archive_git_commit
- archive-round/git_diff untracked file replayability

## Closure
Phase 2 A-D is complete. Future work must start as Phase 3 or post-Phase-2 hardening.
```

### 6.2 Report binding requirement

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase2_completion_audit_20260520",
  "round_id": "round_20260520_phase2_completion_audit",
  "based_on_decision_id": "decision_phase2_completion_audit_20260520",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

`files_changed`、`tests_ran`、`generated_artifacts` 必须填写真实值，不能留空。

### 6.3 Naming correction

Completion report 必须明确：

```text
Phase 2E is not an official phase.
The correct next label is Phase 3A or post-Phase-2 hardening.
```

不要回写修改 Phase 2D archived report；只在新的 completion report 中纠正命名。

## 7. Tests

本轮没有代码功能修改，测试重点是确认现有 Phase 2 测试仍可用、handoff 状态可信、文档存在。

至少必须运行并记录：

```powershell
python -m pytest -q tests\test_harness_resume.py
python -m pytest -q tests\test_harness_artifact_manifest.py
python -m pytest -q tests\test_harness_compare.py
python -m pytest -q tests\test_harness_resource_budget.py
python -m pytest -q
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2_completion_audit
```

如果全量 pytest 因环境问题失败，必须在 report 中解释；如果只是文档变更，本轮仍应尽量运行全量 pytest，保持 closure 可信。

注意：

```text
在最终 report 写入前，lint-report 可能因为 report.based_on_decision_id 仍指向 Phase 2D 而失败。
这属于 expected pre-report mismatch，必须在 pytest_result.txt 中标注。
最终 report 写入后，lint-report / lint-handoff 必须恢复为 OK / REVIEW_COMPLETE。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要运行逆向 runtime probe。
2. 需要运行 pipeline 或模型调用。
3. 需要修改 harness 功能代码才能完成。
4. 需要修改 project_state.py 才能完成。
5. 需要修改 compare_aware_search、olly_scripts 或逆向策略。
6. 需要修改 GPT/Codex 协作协议。
7. 需要修改 decision_meta / codex_report_summary schema。
8. 需要读取或提交完整 solve_reports。
9. Phase 2A-D 任一 archived report 缺失或 based_on_decision_id 无法核对。
10. Phase 2A-D 任一 pytest_result 缺失且无法从 archive 恢复。
11. 无法明确区分 Phase 2 closure 与 Phase 3 backlog。
12. 无法让 report.based_on_decision_id 绑定当前 decision_id。
13. 无法让 pytest_result.txt 记录本轮真实测试。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. docs/phase2_harness_reproducibility_completion.md 已生成。
2. completion report 明确 Phase 2 只包含 A-D，没有 Phase 2E。
3. completion report 包含 Phase 2A-D acceptance matrix。
4. completion report 列出每个子阶段的 decision_id / report_id / round_id / 测试摘要。
5. completion report 把 compare strict、artifact path schema、round manifest commit 语义、archive diff 可回放性列入 Phase 3 backlog。
6. 不修改 harness 功能代码。
7. 不修改 project_state 协作协议。
8. 不运行 runtime probe，不推进 samplereverse。
9. Phase 2 相关 harness 测试和全量 pytest 通过，或失败有明确环境解释。
10. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
11. project_state/pytest_result.txt 记录真实测试和最终 lint-handoff 输出。
12. round archive 已生成并包含 completion report 相关 diff。
```
