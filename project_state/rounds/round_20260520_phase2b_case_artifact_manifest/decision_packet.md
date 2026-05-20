```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase2b_case_artifact_manifest_20260520",
  "round_id": "round_20260520_phase2b_case_artifact_manifest",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 2B：为每个 harness case_result 增加 `artifact_manifest`，并让 `project_state.artifact_index` 在可用时优先使用 case-level artifact provenance。

本轮属于工程架构改造支线中的 harness 可复现 / 可恢复 / 可比较方向。不要推进 `samplereverse` 逆向解题，不运行 runtime probe，不修改 GPT/Codex 协作协议，不进入 harness compare / resource budget / workflow lifecycle 的后续任务。

## 1. Goal

当前 `project_state` 主要通过扫描 `solve_reports` 和路径推断来建立 artifact_index。Phase 1C 已经有 `latest_artifacts_v2` provenance/freshness 字段，但 artifact provenance 仍主要来自全局路径推断，而不是每个 harness case 的直接输出记录。

Phase 2B 目标是在 harness case result 中直接记录轻量 artifact manifest，让后续 `project_state` 构建、跨 run 比较、stale/current 判断更稳定。

本轮目标：

```text
1. 在 HarnessCaseResult 中新增 additive 字段 artifact_manifest。
2. 从 SolveResult.tool_artifacts / ToolRunArtifact.output_path 生成每个 case 的 artifact_manifest。
3. artifact_manifest 只记录轻量元数据，不内嵌 artifact 内容。
4. project_state 构建 artifact_index 时，在 case_result.artifact_manifest 存在且有效时优先使用它补充或生成 latest_artifacts_v2。
5. 保持旧 case_result 兼容：没有 artifact_manifest 的旧结果仍可加载。
6. 不改变 decision_meta / codex_report_summary / lint-handoff 协作协议。
7. 不运行任何逆向 runtime probe。
```

建议 artifact_manifest 最小结构：

```json
{
  "artifact_manifest": [
    {
      "kind": "compare_real_lhs_provenance_audit",
      "path": "solve_reports\\harness_runs\\...\\compare_real_lhs_provenance_audit.json",
      "size_bytes": 105629,
      "sha256": "...",
      "classification": "compare_lhs_runtime_backed_writer_missing",
      "tool_name": "...",
      "owner_profile": "...",
      "strategy_name": "..."
    }
  ]
}
```

字段要求：

```text
kind:
  优先从 artifact 文件名、ToolRunArtifact.tool_name、或现有 artifact key 规则推导。
  不要求一次覆盖所有历史 artifact 类型。

path:
  使用相对仓库或 reports-dir 可读路径；不要写绝对 Windows 本机路径作为唯一来源。

size_bytes / sha256:
  如果文件存在则必须填写；文件不存在则可为 null，并应避免当作 current 证据。

classification:
  如果 artifact 是 JSON 且顶层存在 classification 字段，则读取；否则为 "" 或 null。

兼容性:
  旧 case_result 缺少 artifact_manifest 时不能崩溃。
```

## 2. Current Evidence

当前任务主线：工程架构改造支线，具体为 Phase 2B case artifact manifest。

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

Phase 2A 已完成并经 GPT 审查：

```text
decision_id = decision_phase2a_harness_resume_policy_20260520
report_id = report_phase2a_harness_resume_policy_20260520
report_status = SUCCESS
acceptance_recommendation = ACCEPTED
GPT review = ACCEPTED_WITH_LIMITATIONS
主要限制 = archived git_diff.patch 对新增测试文件可回放性不够清晰；resume_policy/rerun_statuses 未进入 manifest 可审计字段。
```

这些限制不阻断 Phase 2B，但本轮应避免扩大到完整 archive-round 重构。若能以小改动改善新增文件归档可见性，可在 Required Audit 中说明；否则只记录为后续 Phase 2D `lint-round` / archive 改进任务。

当前 artifact_index 现状：

```text
latest_artifacts_v2 已存在。
compare_probe / compare_probe_log / compare_real_lhs_provenance_audit / summary / run_manifest 等当前 run artifact 标记为 current。
frontier_summary / function_semantic_audit / base64_rc4_static_point_discovery 等 legacy tool_artifacts 标记为 stale。
多个未生成 artifact 标记为 missing。
```

现有代码证据：

```text
reverse_agent.pipeline.SolveResult 已有 tool_artifacts: list[ToolRunArtifact]。
reverse_agent.tool_runners.ToolRunArtifact 已有 tool_name / output_path / owner_profile / strategy_name 等字段。
```

因此本轮应优先复用 `SolveResult.tool_artifacts` 和 `ToolRunArtifact.output_path`，不要新建并行工具产物体系。

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
不要实现 harness compare。
不要实现 resource_budget。
不要实现 queue / backpressure / worker pool。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph。
不要引入 PostgreSQL / Redis / Kubernetes。
不要为了 artifact_manifest 重构 harness 主流程。
不要内嵌 artifact 文件内容到 case_result。
不要把 missing/stale artifact 当作 current evidence。
```

## 4. Files To Inspect

必须审计：

```text
reverse_agent/harness.py
reverse_agent/pipeline.py
reverse_agent/tool_runners.py
reverse_agent/project_state.py
tests/test_harness.py
tests/test_harness_resume.py
tests/test_project_state.py
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
```

如果现有测试结构不适合承载新增 artifact manifest 测试，允许新增：

```text
tests/test_harness_artifact_manifest.py
```

必要时参考：

```text
project_state/rounds/round_20260520_phase2a_harness_resume_policy/round_manifest.json
project_state/rounds/round_20260520_phase2a_harness_resume_policy/git_diff.patch
```

不要默认读取完整 `solve_reports/`。需要 fixture artifact 时，在临时目录构造最小 JSON artifact 即可。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. HarnessCaseResult 当前如何序列化到 case_results/<case>.json。
2. SolveResult.tool_artifacts 当前字段结构。
3. ToolRunArtifact.output_path 是否稳定可用。
4. 当前 artifact_index 如何从 solve_reports / latest_harness_run 推导 latest_artifacts_v2。
5. project_state 是否已经有 artifact kind 推导函数；如果有，优先复用。
6. 旧 case_result 缺少 artifact_manifest 时如何兼容。
7. artifact_manifest 缺失、artifact 文件不存在、JSON 无 classification 时如何处理。
8. case_result.artifact_manifest 与 existing artifact_index path scan 的优先级关系。
9. 是否需要更新 schema 文档；如果需要，仅做 additive 字段说明，不改协议。
10. 本轮是否只需要改 harness.py / project_state.py / tests。
11. 是否存在误推进 reverse runtime 或提交完整 solve_reports 的风险。
12. Phase 2A 审查中提到的归档 diff 新增文件可见性问题是否与本轮相关；若不处理，明确列为后续 Phase 2D。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/harness.py
reverse_agent/project_state.py
tests/test_harness.py
tests/test_harness_resume.py
tests/test_project_state.py
tests/test_harness_artifact_manifest.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

可选修改：

```text
project_state/schema.md
```

仅允许添加 `case_result.artifact_manifest` additive 字段说明，不要改 decision/report 协议。

允许重新生成或更新：

```text
project_state/rounds/<new_round_id>/*
```

不要修改：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
reverse_agent/pipeline.py 中非必要主流程
reverse_agent/tool_runners.py 中非必要工具执行逻辑
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
```

### 6.1 HarnessCaseResult artifact_manifest

建议新增 dataclass：

```python
@dataclass
class CaseArtifactManifestEntry:
    kind: str
    path: str
    size_bytes: int | None = None
    sha256: str | None = None
    classification: str = ""
    tool_name: str = ""
    owner_profile: str = ""
    strategy_name: str = ""
```

或者使用 `list[dict[str, object]]`，但必须保持 JSON 简单、可序列化。

在 `HarnessCaseResult` 中新增：

```python
artifact_manifest: list[dict[str, object]] = field(default_factory=list)
```

注意：

```text
必须保证旧 JSON 反序列化时缺少 artifact_manifest 不会失败。
如果当前 _load_case_result 直接 HarnessCaseResult(**data)，需要为缺失字段提供 dataclass default 即可。
```

### 6.2 从 ToolRunArtifact 生成 manifest

建议新增 helper：

```python
def _build_case_artifact_manifest(tool_artifacts: list[ToolRunArtifact]) -> list[dict[str, object]]:
    ...
```

规则：

```text
1. 只处理 output_path 非空的 artifact。
2. 如果 output_path 指向存在文件：填 size_bytes / sha256。
3. 如果 output_path 指向 JSON 文件：尝试读取顶层 classification。
4. kind 优先使用：
   - JSON 顶层 kind 字段；
   - 或从 path 文件名 stem 推导；
   - 或 tool_name。
5. 不读取大型内容，只读取 JSON 顶层少数字段；遇到解析失败直接 classification=""。
6. 不因 artifact 缺失导致 case 失败。
```

在 `_case_result_from_solve_result()` 中填充：

```text
artifact_manifest = _build_case_artifact_manifest(solve_result.tool_artifacts)
```

### 6.3 project_state 使用 artifact_manifest

在 `reverse_agent/project_state.py` 中，构建 artifact_index 时：

```text
1. 优先读取 latest_harness_run/case_results/*.json 中的 artifact_manifest。
2. 对 manifest entry 生成或补充 latest_artifacts_v2 条目。
3. 如果 artifact_manifest 不存在，则保留旧扫描逻辑。
4. 如果 artifact_manifest entry 指向的 path 与 latest_harness_run 一致，freshness=current。
5. 如果 path 存在但不属于 latest_harness_run，freshness=stale 或按现有规则判断。
6. 如果 path 缺失，freshness=missing，不要当作 current。
7. 保留 latest_artifacts 旧字段兼容。
```

不要删除旧扫描逻辑。本轮是 additive improvement。

### 6.4 归档可审计性限制

Phase 2A 审查发现 `git_diff.patch` 对新增测试文件的可回放性不够清晰。本轮不要大改 archive-round，但可以做一个小的低风险补充：

```text
如果 archive-round 已经能记录新增文件，Codex 只需说明它为何足够。
如果 archive-round 不能完整记录新增文件，Codex 在 report 中把该问题列为后续 Phase 2D lint-round/archive 改进项。
```

不要因为这个问题扩大本轮范围。

### 6.5 report 绑定要求

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase2b_case_artifact_manifest_20260520",
  "round_id": "round_20260520_phase2b_case_artifact_manifest",
  "based_on_decision_id": "decision_phase2b_case_artifact_manifest_20260520",
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
test_case_result_includes_artifact_manifest
test_case_result_artifact_manifest_includes_size_sha256_and_classification
test_case_result_artifact_manifest_handles_missing_or_invalid_artifact
test_load_old_case_result_without_artifact_manifest_remains_compatible
test_artifact_index_uses_case_artifact_manifest_when_present
test_artifact_index_falls_back_to_legacy_scan_without_case_artifact_manifest
test_artifact_index_manifest_missing_path_marked_missing
```

至少必须运行并记录：

```powershell
python -m py_compile reverse_agent\harness.py reverse_agent\project_state.py
python -m pytest -q tests\test_harness.py
python -m pytest -q tests\test_harness_resume.py
python -m pytest -q tests\test_project_state.py
python -m pytest -q tests\test_harness_artifact_manifest.py
python -m pytest -q
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

如果没有新增 `tests/test_harness_artifact_manifest.py`，则必须在 report 中说明对应测试放入了哪个现有测试文件。

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase2b_case_artifact_manifest
```

注意：

```text
在最终 report 写入前，lint-report 可能因为 report.based_on_decision_id 仍指向 Phase 2A 而失败。
这属于 expected pre-report mismatch，必须在 pytest_result.txt 中标注。
最终 report 写入后，lint-report / lint-handoff 必须恢复为 OK / REVIEW_COMPLETE。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要运行逆向 runtime probe。
2. 需要修改 compare_aware_search、olly_scripts 或逆向策略。
3. 需要修改 GPT/Codex 协作协议才能完成。
4. 需要修改 decision_meta / codex_report_summary schema。
5. 需要实现 harness compare 或 resource_budget 才能完成。
6. 需要 queue/backpressure/worker pool 才能完成。
7. 需要读取或提交完整 solve_reports 才能完成。
8. 需要内嵌 artifact 内容到 case_result 才能完成。
9. 无法兼容旧 case_result JSON。
10. 无法保留 latest_artifacts 旧字段兼容。
11. 无法防止 missing artifact 被标记为 current。
12. 无法让 report.based_on_decision_id 绑定当前 decision_id。
13. 无法让 pytest_result.txt 记录本轮真实测试。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. HarnessCaseResult 新增 artifact_manifest，且为 additive 兼容字段。
2. 新 case_result JSON 会写出 artifact_manifest。
3. artifact_manifest entry 包含 kind/path/size_bytes/sha256/classification 的最小元数据。
4. artifact 缺失、JSON 无效、classification 缺失时不会导致 case 失败。
5. 旧 case_result 缺少 artifact_manifest 时仍能加载。
6. project_state artifact_index 在可用时优先使用 case_result.artifact_manifest。
7. latest_artifacts_v2 保留 path/kind/source_run/modified_at/size_bytes/sha256/freshness 等既有语义。
8. legacy latest_artifacts 仍保留兼容。
9. missing artifact 不会被当作 current evidence。
10. 测试覆盖 harness artifact_manifest 和 project_state manifest ingestion。
11. 全量 pytest 通过，或如有环境相关跳过/失败，必须在 report 中解释。
12. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
13. project_state/pytest_result.txt 记录真实测试和最终 lint-handoff 输出。
14. 不修改 GPT/Codex 协作协议，不运行 runtime probe，不实现 Phase 2C/2D。
```
