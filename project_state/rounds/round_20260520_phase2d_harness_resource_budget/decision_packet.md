```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase2d_harness_resource_budget_20260520",
  "round_id": "round_20260520_phase2d_harness_resource_budget",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 2D：为 harness 增加本地 `resource_budget` 记录能力，并把预算写入 `run_manifest.json`。

本轮属于工程架构改造支线中的 harness 可复现 / 可恢复 / 可比较方向。不要推进 `samplereverse` 逆向解题，不运行 runtime probe，不修改 GPT/Codex 协作协议，不实现队列、调度、backpressure 或 worker pool。

## 1. Goal

Phase 2A 已改善 resume 语义；Phase 2B 已让 `case_result` 记录 artifact provenance；Phase 2C 已新增 `harness compare`。下一步需要让每次 harness run 明确记录本地资源预算，避免长时间 GUI / Olly / Frida / UIA / tool artifact 膨胀造成结果不可复现。

本轮目标是**记录和最小校验 resource_budget**，不是实现完整资源调度系统。

本轮目标：

```text
1. 在 harness 配置中新增 resource_budget 字段或等价结构。
2. 新增 CLI 参数用于设置本地预算。
3. 将 resource_budget 写入 run_manifest.json。
4. 保持 run_manifest 旧字段兼容，不破坏已有 config_digest / pipeline_defaults 结构。
5. 最小校验预算值必须为正整数或 null，不接受负数。
6. 不实现 queue/backpressure/worker pool。
7. 不强制 kill 进程，不强制清理 artifact，不改变 runtime 行为。
8. 不修改 project_state 协作协议，不运行逆向 runtime probe。
```

建议 resource_budget 结构：

```json
{
  "resource_budget": {
    "max_case_seconds": 21600,
    "max_tool_seconds": 300,
    "max_artifact_bytes": 52428800,
    "max_recent_artifacts": 20,
    "max_context_pack_bytes": 1048576,
    "max_candidate_count": 5000,
    "max_probe_candidates": 50
  }
}
```

字段语义：

```text
max_case_seconds:
  单个 case 的建议最大运行时间。Phase 2D 只记录，不强制终止。

max_tool_seconds:
  单个外部工具的建议最大运行时间。可先只记录，不覆盖现有 ida/olly/copilot timeout。

max_artifact_bytes:
  单个 artifact 或单次 run artifact 的建议上限。Phase 2D 只记录，不删除文件。

max_recent_artifacts:
  project_state / context pack / summary 中展示 recent artifacts 的建议数量。Phase 2D 不要求修改 project_state。

max_context_pack_bytes:
  上下文包建议最大字节数。Phase 2D 只记录，不修改 pack_context 行为。

max_candidate_count:
  单轮候选数量建议上限。Phase 2D 只记录，不裁剪候选。

max_probe_candidates:
  runtime probe 候选数量建议上限。Phase 2D 只记录，不运行 probe。
```

如果现有代码已有等价字段或 timeout 字段，优先复用并在 report 中解释，不重复制造冲突体系。

## 2. Current Evidence

当前任务主线：工程架构改造支线，具体为 Phase 2D harness local resource budget。

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

Phase 2C 已完成并经 GPT 审查：

```text
decision_id = decision_phase2c_harness_compare_20260520
report_id = report_phase2c_harness_compare_20260520
report_status = SUCCESS
acceptance_recommendation = ACCEPTED
full pytest = 375 passed
final lint-handoff = REVIEW_COMPLETE
GPT review = ACCEPTED_WITH_LIMITATIONS
```

Phase 2C 遗留限制：

```text
1. compare 对不存在 run 可能静默输出空比较。
2. artifact_manifest path 解析仍受 cwd/reports_dir 影响。
3. round_manifest.source_git_commit 仍继承 current_state，不等于本轮工程提交。
```

这些限制不阻断 Phase 2D。本轮不修复 compare strict、path schema 或 round commit 语义，除非实现 resource_budget 时出现直接必要关系；否则记录为后续 Phase 2E / lint-round / archive 审计项。

当前 artifact_index 现状：

```text
latest_artifacts_v2 已存在。
compare_probe / compare_probe_log / compare_real_lhs_provenance_audit / summary / run_manifest 等当前 run artifact 标记为 current。
frontier_summary / function_semantic_audit / base64_rc4_static_point_discovery 等 legacy tool_artifacts 标记为 stale。
多个未生成 artifact 标记为 missing。
```

这些 artifact 只用于说明状态，不是本轮要消费的逆向证据。本轮不要重新扫描完整 `solve_reports/`。

为什么本轮适合做 resource_budget：

```text
reverse-agent 运行环境是本地 Windows GUI / 调试工具链，不是分布式平台。
主要风险来自长跑、工具卡死、artifact 膨胀、上下文包膨胀、候选数量膨胀。
先把预算写入 run_manifest，才能让后续 compare、archive、lint 或人工审查知道一轮 run 的资源边界。
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
不要修改 project_state.py。
不要实现 queue / backpressure / worker pool。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph。
不要引入 PostgreSQL / Redis / Kubernetes。
不要实现多 worker 调度平台。
不要强制 kill 外部进程。
不要强制删除 artifact。
不要修改 pack_context 行为。
不要修改 harness compare 行为。
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
tests/test_harness_compare.py
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
```

如果现有测试结构不适合承载 resource budget 测试，允许新增：

```text
tests/test_harness_resource_budget.py
```

可选参考：

```text
project_state/rounds/round_20260520_phase2c_harness_compare/round_manifest.json
project_state/rounds/round_20260520_phase2c_harness_compare/git_diff.patch
```

不要默认读取完整 `solve_reports/`。测试必须使用临时目录构造最小 harness run。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 HarnessConfig / run_manifest 中已有哪些 timeout 或 budget 相关字段。
2. 当前 copilot_timeout_seconds、ida_timeout_seconds、olly_timeout_seconds 如何记录到 run_manifest。
3. 当前 run_manifest 的 config_payload / pipeline_defaults / config_digest 结构。
4. 新 resource_budget 应放在 run_manifest 顶层，还是 pipeline_defaults 内；选择理由是什么。
5. 是否需要把 resource_budget 纳入 config_digest；若不纳入，如何保证审计可见；若纳入，如何避免破坏 resume 兼容。
6. CLI 参数如何命名，是否与已有 timeout 参数冲突。
7. 预算字段的默认值和合法值范围。
8. 负数、零、非整数输入如何处理。
9. 本轮是否只记录预算，不强制执行预算。
10. 是否已有等价 budget 结构；如果有，优先复用，不重复实现。
11. 是否存在误运行 pipeline、runtime probe、或读取完整 solve_reports 的风险。
12. Phase 2C 遗留的 compare strict / path / round commit 问题是否被扩大；如果不处理，明确列为后续项。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/harness.py
tests/test_harness.py
tests/test_harness_resume.py
tests/test_harness_artifact_manifest.py
tests/test_harness_compare.py
tests/test_harness_resource_budget.py
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

如果 Codex 发现必须修改 `project_state.py`、`tool_runners.py` 或逆向策略才能完成，应停止并报告。本轮预算应独立在 harness 层完成。

### 6.1 Resource budget data model

建议新增 dataclass：

```python
@dataclass
class ResourceBudget:
    max_case_seconds: int | None = 21600
    max_tool_seconds: int | None = 300
    max_artifact_bytes: int | None = 52428800
    max_recent_artifacts: int | None = 20
    max_context_pack_bytes: int | None = 1048576
    max_candidate_count: int | None = 5000
    max_probe_candidates: int | None = 50
```

并在 `HarnessConfig` 中新增：

```python
resource_budget: ResourceBudget = field(default_factory=ResourceBudget)
```

如果项目风格更适合 `dict[str, int | None]`，也可以使用 dict，但必须保证 JSON 输出稳定、字段完整、可测试。

### 6.2 CLI 参数

新增 CLI 参数：

```text
--max-case-seconds
--max-tool-seconds
--max-artifact-bytes
--max-recent-artifacts
--max-context-pack-bytes
--max-candidate-count
--max-probe-candidates
```

规则：

```text
1. 默认值使用 ResourceBudget 默认值。
2. 值必须是正整数。
3. 不建议本轮支持复杂单位，如 50MB、2h；只接受整数。
4. 如果要允许 unlimited，必须用显式空值策略；但 argparse 不易表达时，本轮可不支持 unlimited。
```

### 6.3 run_manifest 写入

在 `_build_manifest()` 生成的 run manifest 中写入顶层字段：

```json
{
  "resource_budget": {
    "max_case_seconds": 21600,
    "max_tool_seconds": 300,
    "max_artifact_bytes": 52428800,
    "max_recent_artifacts": 20,
    "max_context_pack_bytes": 1048576,
    "max_candidate_count": 5000,
    "max_probe_candidates": 50
  }
}
```

建议同时在 `pipeline_defaults` 或 `config_payload` 中保持可见，但不要破坏现有 resume / config digest 语义。如果 Codex 判断纳入 `config_digest` 会导致旧 run 可比性变化，可以：

```text
1. 将 resource_budget 写入 run_manifest 顶层。
2. 不纳入 config_digest。
3. 在 report 中明确说明原因。
```

不要改 `project_state` 的 artifact_index 或 current_state 构建逻辑。

### 6.4 最小校验

新增 helper，例如：

```python
def _positive_int(value: str) -> int:
    ...
```

要求：

```text
1. 负数失败。
2. 0 失败。
3. 非整数失败。
4. 合法正整数通过。
```

### 6.5 本轮不强制执行预算

本轮只做记录，不做 enforcement：

```text
不 kill case。
不 kill external tool。
不删除 artifact。
不裁剪 candidate。
不裁剪 context pack。
不改变 compare 输出。
不改变 project_state pack_context。
```

### 6.6 report 绑定要求

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase2d_harness_resource_budget_20260520",
  "round_id": "round_20260520_phase2d_harness_resource_budget",
  "based_on_decision_id": "decision_phase2d_harness_resource_budget_20260520",
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
test_harness_manifest_records_default_resource_budget
test_harness_manifest_records_cli_resource_budget_overrides
test_harness_resource_budget_rejects_negative_or_zero_values
test_harness_resource_budget_rejects_non_integer_values
test_harness_resource_budget_does_not_break_existing_run_cli
test_harness_resource_budget_does_not_break_compare_cli
test_harness_resource_budget_not_enforced_by_default
```

至少必须运行并记录：

```powershell
python -m py_compile reverse_agent\harness.py
python -m pytest -q tests\test_harness_resource_budget.py
python -m pytest -q tests\test_harness.py
python -m pytest -q tests\test_harness_resume.py
python -m pytest -q tests\test_harness_artifact_manifest.py
python -m pytest -q tests\test_harness_compare.py
python -m pytest -q
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

如果没有新增 `tests/test_harness_resource_budget.py`，则必须在 report 中说明对应测试放入了哪个现有测试文件。

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2d_harness_resource_budget
```

注意：

```text
在最终 report 写入前，lint-report 可能因为 report.based_on_decision_id 仍指向 Phase 2C 而失败。
这属于 expected pre-report mismatch，必须在 pytest_result.txt 中标注。
最终 report 写入后，lint-report / lint-handoff 必须恢复为 OK / REVIEW_COMPLETE。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要运行逆向 runtime probe。
2. 需要运行 pipeline 或模型调用才能完成测试。
3. 需要修改 compare_aware_search、olly_scripts 或逆向策略。
4. 需要修改 GPT/Codex 协作协议才能完成。
5. 需要修改 decision_meta / codex_report_summary schema。
6. 需要修改 project_state.py 才能完成。
7. 需要实现 resource enforcement、process kill、artifact cleanup、candidate truncation 或 context pack truncation 才能完成。
8. 需要实现 queue/backpressure/worker pool 才能完成。
9. 需要递归读取完整 solve_reports 才能完成。
10. 需要提交完整 solve_reports 才能完成。
11. 无法保持现有 `python -m reverse_agent.harness --dataset ...` 兼容。
12. 无法保持 `python -m reverse_agent.harness compare ...` 兼容。
13. 无法让 run_manifest 写出稳定 resource_budget。
14. 无法让 report.based_on_decision_id 绑定当前 decision_id。
15. 无法让 pytest_result.txt 记录本轮真实测试。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. HarnessConfig 或等价结构能表达 resource_budget。
2. CLI 能配置 max_case_seconds / max_tool_seconds / max_artifact_bytes / max_recent_artifacts / max_context_pack_bytes / max_candidate_count / max_probe_candidates。
3. run_manifest.json 顶层写出 resource_budget。
4. 默认 resource_budget 字段完整且稳定。
5. CLI override 能反映到 run_manifest.resource_budget。
6. 负数、0、非整数参数被拒绝。
7. 旧 run CLI 保持兼容。
8. compare CLI 保持兼容。
9. 本轮不强制执行预算，不 kill 进程，不删除 artifact，不裁剪候选或 context pack。
10. 测试覆盖默认预算、CLI 覆盖、非法参数、旧 run CLI、compare CLI、不执行预算。
11. 全量 pytest 通过，或如有环境相关跳过/失败，必须在 report 中解释。
12. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
13. project_state/pytest_result.txt 记录真实测试和最终 lint-handoff 输出。
14. 不修改 GPT/Codex 协作协议，不运行 runtime probe，不实现队列系统。
```
