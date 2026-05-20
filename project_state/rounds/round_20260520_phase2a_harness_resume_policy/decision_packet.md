```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase2a_harness_resume_policy_20260520",
  "round_id": "round_20260520_phase2a_harness_resume_policy",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 2A：增强 harness resume 语义。

本轮属于工程架构改造支线中的 harness 可复现 / 可恢复 / 可比较方向。不要推进 `samplereverse` 逆向解题，不运行 runtime probe，不修改 GPT/Codex 协作协议，不进入 artifact manifest / harness compare / resource budget 的后续 Phase 2 子任务。

## 1. Goal

当前 harness resume 语义过粗：同一 `run_name` 下只要 `case_results/<case>.json` 存在就跳过。这个行为对稳定终态结果合理，但对 `error`、`timeout`、`interrupted`、`partial`、`blocked` 等非终态结果不可靠。

本轮目标：

```text
1. 将 harness resume 默认策略改为 terminal-only：
   - 只默认跳过明确终态 case result。
   - 非终态、临时错误、中断、超时结果默认允许重跑。
2. 保留旧行为 all-existing：
   - 用户显式传入 --resume-policy all-existing 时，继续“只要已有 case result 就跳过”。
3. 增加按 status 强制重跑能力：
   - --rerun-status <status> 可重复传入。
   - --rerun-error 作为 --rerun-status error 的便捷语法糖。
4. 明确 status 判定函数，避免散落字符串判断。
5. 增加 harness resume 单元测试，证明 terminal / non-terminal / legacy policy 行为。
6. 不改 project_state 协作协议，不改 reverse strategy，不运行 runtime probe。
```

建议状态分类：

```text
默认跳过的 terminal statuses:
- passed
- failed_expected
- completed_no_expected
- not_found

默认不跳过、应允许重跑的 non-terminal / unstable statuses:
- error
- timeout
- interrupted
- partial
- blocked
```

建议 CLI：

```powershell
python -m reverse_agent.harness run ... --resume --resume-policy terminal-only
python -m reverse_agent.harness run ... --resume --resume-policy all-existing
python -m reverse_agent.harness run ... --resume --rerun-error
python -m reverse_agent.harness run ... --resume --rerun-status error --rerun-status timeout
```

默认规则建议：

```text
如果 --resume 启用但未显式指定 --resume-policy，则使用 terminal-only。
```

## 2. Current Evidence

当前任务主线：工程架构改造支线，具体为 Phase 2A harness resume 可靠性。

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

Phase 1F 已完成：

```text
decision_id = decision_phase1f_lint_handoff_aggregate_20260520
report_id = report_phase1f_lint_handoff_aggregate_20260520
report_status = SUCCESS
acceptance_recommendation = ACCEPTED
tests/test_project_state.py = 101 passed
full pytest = 354 passed
final lint-handoff = REVIEW_COMPLETE
decision_execution_state = CONSUMED_BY_SUCCESS_REPORT
decision_ready_for_execution = False
```

artifact freshness 现状：

```text
latest_artifacts_v2 已存在。
compare_probe / compare_probe_log / compare_real_lhs_provenance_audit / summary / run_manifest 等当前 run artifact 标记为 current。
frontier_summary / function_semantic_audit / base64_rc4_static_point_discovery 等 legacy tool_artifacts 标记为 stale。
多个未生成 artifact 标记为 missing。
```

这些 artifact 只用于说明状态，不是本轮要消费的逆向证据。本轮不要重新扫描完整 `solve_reports/`。

为什么本轮适合做 resume：

```text
reverse-agent 的动态调试、Olly、Frida、UIA、Windows GUI 工具链容易出现临时 error/timeout/interrupted。
如果这些非终态结果被 --resume 永久缓存，就会造成假稳定，后续 run 会误以为该 case 已经完成。
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
不要修改 project_state 协作协议。
不要修改 decision_meta / codex_report_summary schema。
不要修改 lint-decision / lint-report / lint-handoff 语义。
不要实现 start-round / close-round / lint-round。
不要实现 case_result artifact_manifest。
不要实现 harness compare。
不要实现 resource_budget。
不要实现 queue / backpressure / worker pool。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph。
不要引入 PostgreSQL / Redis / Kubernetes。
不要为了本轮任务重构 harness 主流程。
```

## 4. Files To Inspect

必须审计：

```text
reverse_agent/harness.py
tests/test_harness.py
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
```

如果现有测试结构不适合承载新增 resume 测试，允许新增：

```text
tests/test_harness_resume.py
```

必要时参考：

```text
project_state/rounds/round_20260520_phase1f_lint_handoff/round_manifest.json
project_state/rounds/round_20260520_phase1f_lint_handoff/git_diff.patch
```

不要默认读取完整 `solve_reports/`。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 reverse_agent/harness.py 的 --resume 行为在哪里实现。
2. 当前 case_results/<case>.json 的 status 字段来源和可能取值。
3. 当前跳过 case 的判定是否只检查文件存在。
4. 当前 argparse / CLI 子命令结构中 run 命令如何接收 resume 参数。
5. 当前 tests/test_harness.py 是否已有 resume 或 run_name 测试。
6. 是否已有等价 resume-policy 能力；如果有，优先复用，不重复实现。
7. 为什么 error/timeout/interrupted/partial/blocked 不应被 terminal-only 默认跳过。
8. 如何保留 all-existing 旧行为，避免破坏需要旧语义的使用方式。
9. --rerun-status 与 --resume-policy 的优先级。
10. 本轮是否可以只改 harness.py 与 harness 测试。
11. 是否存在误推进 reverse runtime 或修改 project_state 协作协议的风险。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/harness.py
tests/test_harness.py
tests/test_harness_resume.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许重新生成或更新：

```text
project_state/rounds/<new_round_id>/*
```

不建议修改，但如果测试导入路径确有需要，可做最小兼容调整：

```text
tests/conftest.py
```

不要修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
reverse_agent/harness.py 中与 runtime probe 执行无关的大块主流程
project_state/schema.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
```

### 6.1 resume status 分类

建议在 `reverse_agent/harness.py` 中新增或集中定义：

```python
TERMINAL_CASE_STATUSES = {
    "passed",
    "failed_expected",
    "completed_no_expected",
    "not_found",
}

NON_TERMINAL_RERUN_CASE_STATUSES = {
    "error",
    "timeout",
    "interrupted",
    "partial",
    "blocked",
}
```

如果项目已有等价枚举或常量，优先复用现有结构，不重复建新体系。

### 6.2 resume policy

新增 CLI 参数：

```text
--resume-policy terminal-only
--resume-policy all-existing
```

建议规则：

```text
1. 只有 --resume 启用时，resume-policy 才生效。
2. --resume-policy 默认值为 terminal-only。
3. terminal-only:
   - 已存在 result 且 status 属于 TERMINAL_CASE_STATUSES -> skip。
   - 已存在 result 但 status 属于 NON_TERMINAL_RERUN_CASE_STATUSES -> rerun。
   - 已存在 result 但 status 缺失、无法解析、未知 -> rerun，并记录 warning 或 debug 说明。
4. all-existing:
   - 已存在 result -> skip，保持旧行为。
5. 如果未启用 --resume:
   - 不因已有 result 跳过。
```

### 6.3 rerun status 覆盖规则

新增 CLI 参数：

```text
--rerun-status <status>
--rerun-error
```

建议优先级：

```text
1. 如果 --rerun-error 出现，则等价于追加 --rerun-status error。
2. 如果已有 result 的 status 命中 rerun_status 集合，则 rerun。
3. rerun_status 优先级高于 --resume-policy all-existing。
4. 如果 --resume 未启用，但传入 --rerun-status，可以接受但不需要特殊处理，因为未 resume 本来就会运行；可输出 warning，但不要失败。
```

### 6.4 跳过记录

如果当前 harness 已有 summary / run_manifest 记录 skipped cases，本轮应尽量保留并扩展 skip reason。

建议 skip reason：

```text
resume_terminal_result
resume_all_existing
```

如果当前没有 skip reason 结构，不要为了本轮大改 summary schema。只要测试能证明行为即可。

### 6.5 兼容性

必须保持：

```text
1. 未使用 --resume 的旧行为不变。
2. 显式 --resume-policy all-existing 时，旧 resume 行为不变。
3. terminal-only 是新的默认 resume 策略。
4. 现有 harness smoke / manifest / dataset / summary 测试不回退。
```

### 6.6 report 绑定要求

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase2a_harness_resume_policy_20260520",
  "round_id": "round_20260520_phase2a_harness_resume_policy",
  "based_on_decision_id": "decision_phase2a_harness_resume_policy_20260520",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

`files_changed`、`tests_ran`、`generated_artifacts` 必须填写真实值，不能留空。

## 7. Tests

必须新增或修改 harness 测试，覆盖：

```text
test_harness_resume_skips_terminal_result
test_harness_resume_reruns_error_by_default_or_policy
test_harness_resume_all_existing_keeps_old_behavior
test_harness_resume_rerun_status_overrides_all_existing
test_harness_resume_rerun_error_aliases_error_status
test_harness_resume_unknown_or_missing_status_reruns_under_terminal_only
```

至少必须运行并记录：

```powershell
python -m py_compile reverse_agent\harness.py
python -m pytest -q tests\test_harness.py
python -m pytest -q tests\test_harness_resume.py
python -m pytest -q
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

如果 `tests/test_harness_resume.py` 没有新增，则对应命令替换为：

```powershell
python -m pytest -q tests\test_harness.py
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2a_harness_resume_policy
```

注意：

```text
在最终 report 写入前，lint-report 可能因为 report.based_on_decision_id 仍指向 Phase 1F 而失败。
这属于 expected pre-report mismatch，必须在 pytest_result.txt 中标注。
最终 report 写入后，lint-report / lint-handoff 必须恢复为 OK / REVIEW_COMPLETE。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要运行逆向 runtime probe。
2. 需要修改 compare_aware_search、olly_scripts 或逆向策略。
3. 需要修改 project_state 协作协议才能完成。
4. 需要修改 decision_meta / codex_report_summary schema。
5. 需要实现 artifact_manifest、harness compare 或 resource_budget 才能完成。
6. 需要 queue/backpressure/worker pool 才能完成。
7. 需要读取完整 solve_reports 才能完成。
8. 无法识别 case_result status 字段或现有 result schema。
9. 无法保留 --resume-policy all-existing 的旧行为。
10. 无法让 terminal-only 成为默认 resume 策略且保持现有测试通过。
11. 无法让 report.based_on_decision_id 绑定当前 decision_id。
12. 无法让 pytest_result.txt 记录本轮真实测试。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. --resume 默认策略为 terminal-only。
2. terminal-only 会跳过 passed / failed_expected / completed_no_expected / not_found。
3. terminal-only 不会默认跳过 error / timeout / interrupted / partial / blocked。
4. --resume-policy all-existing 保留旧行为：已有 case result 即跳过。
5. --rerun-status 可重复传入，并能覆盖 all-existing skip。
6. --rerun-error 等价于 --rerun-status error。
7. status 缺失、无法解析、未知时，terminal-only 不应静默当作完成。
8. harness resume 行为有专门测试覆盖。
9. 全量 pytest 通过，或如有环境相关跳过/失败，必须在 report 中解释。
10. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
11. project_state/pytest_result.txt 记录真实测试和最终 lint-handoff 输出。
12. 不修改 project_state 协作协议，不运行 runtime probe，不实现 Phase 2B/2C/2D。
```
