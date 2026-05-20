```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase2c_harness_compare_20260520",
  "round_id": "round_20260520_phase2c_harness_compare",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 2C：新增 `harness compare` 命令，用于比较两个 harness run 的 case 结果、计数变化和 artifact classification 变化。

本轮属于工程架构改造支线中的 harness 可复现 / 可恢复 / 可比较方向。不要推进 `samplereverse` 逆向解题，不运行 runtime probe，不修改 GPT/Codex 协作协议，不进入 resource budget / lint-round / archive-round 语义重构。

## 1. Goal

Phase 2A 已改善 resume，Phase 2B 已让新 case_result 记录 `artifact_manifest`。下一步需要让多个 harness run 之间可以直接比较，而不是只靠人工看 summary 或 pass/fail。

本轮目标：

```text
1. 新增命令：python -m reverse_agent.harness compare --base-run <old> --head-run <new>。
2. 比较两个 run 下 case_results/*.json，输出机器可读 JSON。
3. 比较 case status、selected_flag、candidate_count、validation_count、tool_artifact_count、structured_evidence_count。
4. 比较 artifact_manifest 中同 kind artifact 的 classification 变化。
5. 如果 artifact_manifest 对应 artifact JSON 可读，可额外读取顶层 runtime_backed_count、candidate_count、evidence_gate、classification 等轻量字段用于 compare。
6. 支持 case 只存在于 base 或 head 的情况。
7. 保持现有 harness run CLI 兼容：原有 `python -m reverse_agent.harness --dataset ...` 不得被破坏。
8. 不运行 pipeline，不运行 runtime probe，不读取完整 solve_reports。
```

建议命令：

```powershell
python -m reverse_agent.harness compare --base-run sr_old --head-run sr_new --reports-dir solve_reports
```

建议输出结构：

```json
{
  "base_run": "sr_old",
  "head_run": "sr_new",
  "base_run_dir": "solve_reports\\harness_runs\\sr_old",
  "head_run_dir": "solve_reports\\harness_runs\\sr_new",
  "case_deltas": [
    {
      "case_id": "samplereverse",
      "presence": "both",
      "status_change": "completed_no_expected -> completed_no_expected",
      "selected_flag_change": "NOT_FOUND -> NOT_FOUND",
      "candidate_count_delta": 0,
      "validation_count_delta": 0,
      "tool_artifact_count_delta": 1,
      "structured_evidence_count_delta": 0,
      "artifact_deltas": [
        {
          "kind": "compare_real_lhs_provenance_audit",
          "classification_change": "compare_lhs_runtime_backed_writer_missing -> instrumentation_incomplete",
          "runtime_backed_count_delta": -3,
          "candidate_count_delta": 0,
          "evidence_gate_changed": true
        }
      ]
    }
  ],
  "summary": {
    "cases_compared": 1,
    "cases_added": 0,
    "cases_removed": 0,
    "status_changes": 0,
    "artifact_classification_changes": 1
  }
}
```

## 2. Current Evidence

当前任务主线：工程架构改造支线，具体为 Phase 2C harness compare。

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

Phase 2B 已完成并经 GPT 审查：

```text
decision_id = decision_phase2b_case_artifact_manifest_20260520
report_id = report_phase2b_case_artifact_manifest_20260520
report_status = SUCCESS
acceptance_recommendation = ACCEPTED
full pytest = 366 passed
final lint-handoff = REVIEW_COMPLETE
GPT review = ACCEPTED_WITH_LIMITATIONS
```

Phase 2B 遗留限制：

```text
1. artifact_manifest.path 在 reports_dir 位于仓库外时可能退回绝对路径。
2. round_manifest.source_git_commit 仍继承 current_state 的 source commit，不等于本轮工程提交。
```

这些限制不阻断 Phase 2C。本轮 compare 命令应能容忍已有 absolute/relative path，但不要扩大到路径 schema 重构；round_manifest commit 语义留给 Phase 2D。

为什么本轮适合做 compare：

```text
reverse-agent 的很多轮是诊断 sidecar，不一定改变 selected_flag 或 pass/fail。
真正需要比较的是 classification、runtime_backed_count、candidate_count、validation_count、evidence_gate 等诊断指标。
Phase 2B 的 artifact_manifest 已经给 compare 提供了 case-level artifact provenance。
```

## 3. Do Not Do

不要做以下事情：

```text
不要推进 samplereverse 解题。
不要运行 Base64/RC4 breakpoint probe。
不要运行任何逆向 runtime sidecar。
不要修改 reverse_agent/strategies/compare_aware_search.py。
不要修改 reverse_agent/olly_scripts/*。
不要扩大 beam、topN、budget、timeout、frontier iteration。
不要回旧 sample_solver。
不要提交完整 solve_reports。
不要默认读取完整 PROJECT_PROGRESS_LOG.txt。
不要默认读取完整 solve_reports。
不要修改 GPT/Codex 协作协议。
不要修改 decision_meta / codex_report_summary schema。
不要修改 lint-decision / lint-report / lint-handoff 语义。
不要实现 start-round / close-round / lint-round。
不要实现 resource_budget。
不要实现 queue / backpressure / worker pool。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph。
不要引入 PostgreSQL / Redis / Kubernetes。
不要为了 compare 重构 harness 主流程。
不要运行 pipeline 或模型调用。
不要内嵌 artifact 内容到 compare 输出。
不要把 missing artifact 当作 current evidence。
不要在本轮修复 round_manifest commit 语义。
不要在本轮重构 artifact_manifest path schema。
```

## 4. Files To Inspect

必须审计：

```text
reverse_agent/harness.py
tests/test_harness.py
tests/test_harness_resume.py
tests/test_harness_artifact_manifest.py
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
```

如果现有测试结构不适合承载 compare 测试，允许新增：

```text
tests/test_harness_compare.py
```

可选参考：

```text
reverse_agent/project_state.py
project_state/rounds/round_20260520_phase2b_case_artifact_manifest/round_manifest.json
project_state/rounds/round_20260520_phase2b_case_artifact_manifest/git_diff.patch
```

不要默认读取完整 `solve_reports/`。测试必须使用临时目录构造最小 harness_runs fixture。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 reverse_agent.harness main() 是 flat CLI 还是 subcommand CLI。
2. 如何新增 compare 命令且不破坏现有 `python -m reverse_agent.harness --dataset ...` 用法。
3. 当前 HarnessCaseResult JSON 字段包括哪些 compare 可用指标。
4. 当前 artifact_manifest 的字段结构和分类来源。
5. compare 是否需要读取 artifact JSON；如果读取，只允许读取顶层轻量字段。
6. compare 如何处理 base/head 中缺失 case。
7. compare 如何处理 case_result JSON 缺字段、旧格式或无 artifact_manifest。
8. compare 如何处理 artifact_manifest.path 为相对路径、绝对路径、缺失路径、无效 JSON。
9. compare 输出是否稳定排序，便于 diff 和测试。
10. 是否已有等价 compare 功能；如果有，优先复用，不重复实现。
11. 本轮是否只需要改 harness.py 和 compare 测试。
12. 是否存在误运行 pipeline、runtime probe、或读取完整 solve_reports 的风险。
13. Phase 2B 遗留的 path/round commit 问题是否被扩大；如果不处理，明确列为 Phase 2D 后续项。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/harness.py
tests/test_harness.py
tests/test_harness_resume.py
tests/test_harness_artifact_manifest.py
tests/test_harness_compare.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许重新生成或更新：

```text
project_state/rounds/<new_round_id>/*
```

不要修改：

```text
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

如果 Codex 发现必须修改 `project_state.py` 才能完成 compare，应停止并报告；本轮 compare 应独立在 harness 层完成。

### 6.1 CLI 兼容要求

当前 harness CLI 是主要入口。新增 compare 时必须保持：

```powershell
python -m reverse_agent.harness --dataset dataset.json --reports-dir solve_reports --run-name demo
```

继续可用。

建议实现方式：

```text
1. 如果 argv 第一个参数是 compare，则进入 compare parser。
2. 否则沿用现有 run parser。
```

不要强制把现有 run 命令迁移成 `run` subcommand，避免破坏旧脚本。

### 6.2 compare 输入

compare 命令参数：

```text
--base-run <run_name>    必填
--head-run <run_name>    必填
--reports-dir <dir>      默认 solve_reports
--output <path>          可选；不传则打印 JSON 到 stdout
```

建议不做 `--json`，因为 compare 默认输出就是 JSON。

### 6.3 compare 数据源

只允许读取：

```text
solve_reports/harness_runs/<base-run>/case_results/*.json
solve_reports/harness_runs/<head-run>/case_results/*.json
必要时读取 artifact_manifest entry.path 指向的单个 JSON 顶层字段
```

不要递归扫描完整 `solve_reports`。

### 6.4 case delta 字段

每个 case delta 至少包含：

```text
case_id
presence: both | base_only | head_only
status_change
selected_flag_change
candidate_count_delta
validation_count_delta
tool_artifact_count_delta
structured_evidence_count_delta
artifact_deltas
```

对缺失 case：

```text
base_only: head 侧字段为空或 null。
head_only: base 侧字段为空或 null。
```

### 6.5 artifact delta 字段

对 artifact_manifest 按 `kind` 对齐。每个 artifact_delta 至少包含：

```text
kind
presence: both | base_only | head_only
classification_change
runtime_backed_count_delta
candidate_count_delta
evidence_gate_changed
base_path
head_path
```

规则：

```text
1. classification 优先来自 manifest entry.classification。
2. 如果 manifest classification 为空且 artifact JSON 可读，则读取 JSON 顶层 classification。
3. runtime_backed_count / candidate_count / evidence_gate 仅从 artifact JSON 顶层读取。
4. artifact JSON 读取失败时，不使 compare 失败；对应字段为 null。
5. 不读取大型嵌套内容，不把 artifact 内容写入 compare 输出。
```

### 6.6 输出稳定性

必须保证：

```text
case_deltas 按 case_id 排序。
artifact_deltas 按 kind 排序。
JSON 使用 indent=2, sort_keys=True 或等价稳定输出。
```

### 6.7 report 绑定要求

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase2c_harness_compare_20260520",
  "round_id": "round_20260520_phase2c_harness_compare",
  "based_on_decision_id": "decision_phase2c_harness_compare_20260520",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

`files_changed`、`tests_ran`、`generated_artifacts` 必须填写真实值，不能留空。

## 7. Tests

必须新增或修改测试，覆盖：

```text
test_harness_compare_detects_status_change
test_harness_compare_detects_artifact_classification_change
test_harness_compare_detects_candidate_and_validation_count_delta
test_harness_compare_handles_base_only_and_head_only_cases
test_harness_compare_cli_outputs_json_without_dataset
test_harness_compare_preserves_existing_run_cli
test_harness_compare_handles_missing_or_invalid_artifact_json
test_harness_compare_output_is_stably_sorted
```

至少必须运行并记录：

```powershell
python -m py_compile reverse_agent\harness.py
python -m pytest -q tests\test_harness_compare.py
python -m pytest -q tests\test_harness.py
python -m pytest -q tests\test_harness_resume.py
python -m pytest -q tests\test_harness_artifact_manifest.py
python -m pytest -q
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2c_harness_compare
```

注意：

```text
在最终 report 写入前，lint-report 可能因为 report.based_on_decision_id 仍指向 Phase 2B 而失败。
这属于 expected pre-report mismatch，必须在 pytest_result.txt 中标注。
最终 report 写入后，lint-report / lint-handoff 必须恢复为 OK / REVIEW_COMPLETE。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要运行逆向 runtime probe。
2. 需要运行 pipeline 或模型调用。
3. 需要修改 compare_aware_search、olly_scripts 或逆向策略。
4. 需要修改 GPT/Codex 协作协议才能完成。
5. 需要修改 decision_meta / codex_report_summary schema。
6. 需要修改 project_state.py 才能完成。
7. 需要实现 resource_budget、lint-round、archive-round commit 语义或 path schema 重构才能完成。
8. 需要 queue/backpressure/worker pool 才能完成。
9. 需要递归读取完整 solve_reports 才能完成。
10. 需要提交完整 solve_reports 才能完成。
11. 无法保持现有 `python -m reverse_agent.harness --dataset ...` 兼容。
12. 无法让 compare 输出稳定 JSON。
13. 无法让 report.based_on_decision_id 绑定当前 decision_id。
14. 无法让 pytest_result.txt 记录本轮真实测试。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. `python -m reverse_agent.harness compare --base-run <old> --head-run <new>` 可用。
2. compare 不要求 --dataset，不运行 pipeline，不运行 runtime probe。
3. 旧 run CLI 保持兼容。
4. compare 输出稳定 JSON。
5. case_deltas 能显示 status_change、selected_flag_change、candidate_count_delta、validation_count_delta。
6. artifact_deltas 能显示 classification_change。
7. 如果 artifact JSON 可读，artifact_deltas 能显示 runtime_backed_count_delta、candidate_count_delta、evidence_gate_changed。
8. base_only/head_only case 可正确表示。
9. 缺失或无效 artifact JSON 不导致 compare 失败。
10. 测试覆盖 compare CLI、case delta、artifact delta、排序、旧 CLI 兼容。
11. 全量 pytest 通过，或如有环境相关跳过/失败，必须在 report 中解释。
12. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
13. project_state/pytest_result.txt 记录真实测试和最终 lint-handoff 输出。
14. 不修改 GPT/Codex 协作协议，不运行 runtime probe，不实现 Phase 2D。
```
