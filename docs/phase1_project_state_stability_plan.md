# Phase 1 执行计划：project_state 协作稳定性加固

本计划用于指导 reverse-agent 的第一阶段 harness 工程改造。Phase 1 不改解题算法，不引入无人值守 agent runtime，不引入 Redis/PostgreSQL/Kubernetes/Temporal/Dagster/Airflow/Argo。目标是先把 GPT/Codex 多轮人工闭环协作状态做稳。

## 目标

Phase 1 要让每一轮任务都能回答清楚：

1. 当前状态是谁生成的。
2. GPT 的 decision 是基于哪一版 state。
3. Codex 的 report 是否对应这次 decision。
4. artifact 是否来自当前 run。
5. negative_results 是否阻止了重复错误方向。
6. archive-round 是否能完整回放这一轮。

## 总边界

### 允许修改

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/*.json`
- `project_state/*.md`
- `project_state/README.md`
- `project_state/schema.md`
- `README.txt`

### 谨慎修改

- `reverse_agent/harness.py`

只允许做辅助字段读取或路径适配，不要改 harness 主流程。

### 禁止修改或执行

- 不要改 `compare_aware_search` 主策略。
- 不要运行 Base64/RC4 probe。
- 不要回旧 `sample_solver`。
- 不要扩大 beam、topN、budget、timeout、frontier iteration。
- 不要引入 Redis、PostgreSQL、Kubernetes、Temporal、Dagster、Airflow、Argo。
- 不要默认读取完整 `solve_reports/`。
- 不要把 `PROJECT_PROGRESS_LOG.txt` 作为默认上下文。

## Phase 1A：状态身份锚点

### 目标

给 `project_state` 每次 build 增加稳定身份字段，避免 GPT/Codex 基于旧状态继续推进。

### current_state.json 新增字段

```json
{
  "schema_version": 2,
  "state_build_id": "state_20260518_050402_<short_hash>",
  "round_id": "round_20260518_050402",
  "workflow_status": "REPORT_AVAILABLE",
  "current_owner": "web_gpt",
  "review_status": "PENDING_REVIEW",
  "source_git_commit": "<git_commit>",
  "source_harness_run": "sr_lhs_last_writer_health_20260518_r2",
  "generated_at": "2026-05-18T05:04:02Z",
  "state_digest": "<sha256>"
}
```

### task_packet.json 新增字段

```json
{
  "schema_version": 2,
  "state_build_id": "...",
  "round_id": "...",
  "based_on_state_digest": "...",
  "expected_gpt_output": "project_state/decision_packet.md"
}
```

### workflow_status 枚举

```text
NEEDS_STATE_BUILD
REPORT_AVAILABLE
DECISION_READY
CODEX_EXECUTING
ACCEPTED
REWORK_REQUIRED
BLOCKED
STALE_STATE
```

当前默认可先使用 `REPORT_AVAILABLE`。

### 测试

新增或补充：

- `test_current_state_has_identity_fields`
- `test_task_packet_has_based_on_state_digest`
- `test_state_digest_is_stable_for_same_inputs`
- `test_state_digest_changes_when_current_state_changes`

### 验收标准

- `project_state build` 后，`current_state.json` 有 `schema_version`、`state_build_id`、`round_id`、`state_digest`。
- `task_packet.json` 有 `based_on_state_digest`。
- 同样输入重复 build，digest 稳定。
- artifact 或 current_state 变更后，digest 变化。

## Phase 1B：decision/report 有效性标记

### 目标

防止 GPT/Codex 把模板文件、旧 decision、旧 report 当成有效状态。

### decision_packet.md 顶部增加机器可读块

````markdown
```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_<sha256>",
  "based_on_state_build_id": "state_...",
  "based_on_state_digest": "...",
  "status": "APPROVED",
  "created_by": "web_gpt",
  "created_at": "2026-05-18T05:20:00Z"
}
```
````

`status` 枚举：

```text
TEMPLATE_ONLY
DRAFT
APPROVED
SUPERSEDED
```

### codex_execution_report.md 顶部增加机器可读块

````markdown
```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_<sha256>",
  "round_id": "round_...",
  "based_on_decision_id": "decision_...",
  "status": "PARTIAL",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [],
  "next_suggested_task": ""
}
```
````

`status` 枚举：

```text
TEMPLATE_ONLY
SUCCESS
PARTIAL
FAILED
BLOCKED
```

`acceptance_recommendation` 枚举：

```text
ACCEPTED
REWORK_REQUIRED
BLOCKED
NEEDS_REVIEW
```

### 测试

新增或补充：

- `test_extract_decision_meta_json`
- `test_extract_codex_report_summary_json`
- `test_template_only_decision_is_not_treated_as_approved`
- `test_template_only_report_is_not_treated_as_final`
- `test_report_summary_links_to_decision_id`

## Phase 1C：artifact_index provenance / freshness

### 目标

让 `artifact_index.json` 不只是路径索引，而是能说明 artifact 是否来自当前 run、是否新鲜、是否可作为当前证据。

### 新增兼容字段

保留旧字段 `latest_artifacts`，新增：

```json
{
  "latest_artifacts_v2": {
    "compare_real_lhs_provenance_audit": {
      "path": "solve_reports\\harness_runs\\...",
      "kind": "compare_real_lhs_provenance_audit",
      "source_run": "sr_lhs_last_writer_health_20260518_r2",
      "source_round_id": "round_...",
      "modified_at": "2026-05-18T05:03:50Z",
      "size_bytes": 28940,
      "sha256": "<sha256_or_null>",
      "freshness": "current",
      "classification": "instrumentation_incomplete",
      "accepted_by_decision_id": null,
      "supersedes": []
    }
  }
}
```

### freshness 枚举

```text
current
stale
superseded
missing
unknown
```

### 最小规则

1. 如果 artifact 来自 `latest_harness_run`，则 `freshness = current`。
2. 如果 artifact 不来自 `latest_harness_run` 但仍被引用，则 `freshness = stale`。
3. 如果 artifact 路径缺失，则 `freshness = missing`。
4. 如果无法判断，则 `freshness = unknown`。

### 测试

新增或补充：

- `test_artifact_index_v2_contains_source_run_and_freshness`
- `test_artifact_from_latest_run_marked_current`
- `test_artifact_from_old_run_marked_stale`
- `test_missing_artifact_marked_missing`

## Phase 1D：archive-round 可回放

### 目标

让每一轮归档都能证明：

- 这一轮有哪些输入状态。
- 有哪些输出文件。
- 每个文件 digest 是什么。
- 这轮对应哪个 source_run、decision、report。

### 新增文件

每次执行：

```bash
python -m reverse_agent.project_state archive-round
```

生成：

```text
project_state/rounds/<round_id>/round_manifest.json
```

### round_manifest.json 建议结构

```json
{
  "schema_version": 1,
  "round_id": "round_20260518_050402",
  "archived_at": "2026-05-18T05:30:00Z",
  "source_git_commit": "<git_commit>",
  "source_harness_run": "sr_lhs_last_writer_health_20260518_r2",
  "state_build_id": "state_...",
  "state_digest": "...",
  "decision_id": "decision_...",
  "report_id": "report_...",
  "workflow_status": "REPORT_AVAILABLE",
  "files": {
    "task_packet.json": {
      "path": "project_state/task_packet.json",
      "sha256": "..."
    },
    "current_state.json": {
      "path": "project_state/current_state.json",
      "sha256": "..."
    },
    "artifact_index.json": {
      "path": "project_state/artifact_index.json",
      "sha256": "..."
    },
    "negative_results.json": {
      "path": "project_state/negative_results.json",
      "sha256": "..."
    },
    "codex_execution_report.md": {
      "path": "project_state/codex_execution_report.md",
      "sha256": "..."
    },
    "decision_packet.md": {
      "path": "project_state/decision_packet.md",
      "sha256": "..."
    }
  }
}
```

### 幂等规则

同一个 `round_id` 重复归档时：

- 如果 manifest digest 一致：允许，视为 no-op。
- 如果 manifest digest 不一致：拒绝覆盖，提示使用新 `round_id` 或显式 `--force`。

第一阶段可以先不实现 `--force`。

### 测试

新增或补充：

- `test_archive_round_writes_round_manifest`
- `test_round_manifest_contains_expected_files`
- `test_round_manifest_file_digests_match`
- `test_archive_round_is_idempotent_for_same_round`

## Phase 1E：negative_results 最小门禁

### 目标

让 `negative_results.json` 从“人工提醒”升级为“执行前检查”。

### 新增命令

```bash
python -m reverse_agent.project_state lint-decision
```

### 检查内容

1. `decision_packet.md` 是否违反 hard_block。
2. `decision_packet.md` 是否触发 soft_block 但没有 override reason。
3. `decision_packet.md` 是否要求默认读取完整 `solve_reports`。
4. `decision_packet.md` 是否要求回旧 `sample_solver`。
5. `decision_packet.md` 是否要求 Base64/RC4 probe，但当前 gate 未满足。
6. `decision_packet.md` 是否缺 Stop Conditions。
7. `decision_packet.md` 是否缺 Acceptance Criteria。
8. `decision_packet.md` 的 `based_on_state_digest` 是否与当前 `state_digest` 不一致。

### 输出示例

```json
{
  "status": "failed",
  "violations": [
    {
      "severity": "hard_block",
      "rule": "run Base64/RC4 breakpoint probe before real lhs producer identification",
      "evidence_artifact": "solve_reports\\...",
      "message": "Decision packet violates hard negative result."
    }
  ],
  "warnings": []
}
```

### 测试

新增或补充：

- `test_lint_decision_blocks_hard_negative_result`
- `test_lint_decision_warns_soft_negative_result_without_override`
- `test_lint_decision_allows_soft_negative_result_with_override`
- `test_lint_decision_requires_stop_conditions`
- `test_lint_decision_detects_stale_state_digest`

## Phase 1F：schema 文档固化

### 目标

让 GPT 和 Codex 都有稳定协议可遵守，不再靠口头约定。

### 新增文件

```text
project_state/schema.md
```

### 内容建议

- `current_state.json` 字段说明、必填字段、状态枚举。
- `task_packet.json` 字段说明、`based_on_state_digest` 规则。
- `artifact_index.json` 的 `latest_artifacts` 与 `latest_artifacts_v2` 兼容规则。
- `negative_results.json` 的 hard_block / soft_block / override 规则。
- `decision_packet.md` 必须包含的章节。
- `codex_execution_report.md` 的 machine-readable summary。
- `archive-round` 的 `round_manifest.json` 结构。

## 推荐实施顺序

不要一次性让 Codex 做太多。建议分两轮执行 Phase 1。

### 第一轮：Phase 1A + Phase 1D

先实现：

- `schema_version`
- `state_build_id`
- `round_id`
- `state_digest`
- `based_on_state_digest`
- `workflow_status`
- `current_owner`
- `archive-round -> round_manifest.json`

测试重点：

- identity fields
- digest stable/change
- archive manifest
- archive idempotent

### 第二轮：Phase 1B + Phase 1C + Phase 1E + Phase 1F

再实现：

- `decision_meta` 解析
- `codex_report_summary` 解析
- `latest_artifacts_v2`
- `freshness`
- `lint-decision`
- `project_state/schema.md`

测试重点：

- report summary schema
- artifact freshness
- hard/soft negative gate
- stale decision detection

## Phase 1 完成标准

Phase 1 算完成的条件：

1. `project_state build` 能生成带身份字段的 `current_state.json` 和 `task_packet.json`。
2. `state_digest` 能防止旧 decision 被误用。
3. `archive-round` 能生成 `round_manifest.json`。
4. `artifact_index.json` 能说明 artifact 来源和 freshness。
5. `codex_execution_report.md` 有机器可读 summary。
6. `negative_results.json` 能通过 `lint-decision` 阻止明显重复方向。
7. `tests/test_project_state.py` 覆盖上述行为。
8. README 或 `project_state/schema.md` 固化新协议。

## 最低通过命令

```bash
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse
python -m reverse_agent.project_state archive-round
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
```

## 给 Codex 的 Phase 1 DECISION_PACKET

### 1. Goal

完成 Phase 1：加固 `project_state` 人工闭环协作协议。

本轮只做 `project_state` 层面的身份、归档、stale 检查和 negative gate，不修改 `samplereverse` 解题策略，不扩大搜索，不运行新的 runtime probe。

### 2. Current Evidence

当前项目已有：

```text
reverse_agent/harness.py:
- JSON dataset
- run_name
- run_manifest.json
- case_results/*.json
- summary.json / summary.md
- config_digest / dataset_digest
- git_commit
- resume
- fail_fast
- case_id/tag/limit

reverse_agent/project_state.py:
- artifact_index/current_state/task_packet/negative_results/model_gate 构建
- decision_packet/codex_execution_report 模板
- archive-round
- pack

project_state 当前事实：
- active_strategy = CompareAwareSearchStrategy
- profile = samplereverse
- current_mainline = L15(prefix8)
- current_bottleneck.stage = compare_real_lhs_provenance_audit
- current_bottleneck.reason = instrumentation_incomplete
```

本轮目标是协作稳定性，不是逆向推进。

### 3. Do Not Do

- 不要修改 compare-aware search 算法。
- 不要运行 Base64/RC4 probe。
- 不要回旧 `sample_solver`。
- 不要扩大 beam、topN、budget、timeout、frontier iteration。
- 不要引入 Temporal/Dagster/Airflow/Argo/LangGraph runtime。
- 不要引入 PostgreSQL/Redis/Kubernetes。
- 不要提交完整 `solve_reports/`。
- 不要默认读取 `PROJECT_PROGRESS_LOG.txt`。
- 不要破坏旧 project_state JSON 字段兼容性。

### 4. Files To Inspect

- `README.txt`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`

### 5. Required Audit

实现前必须确认：

1. `build_project_state` 当前如何生成 `task_packet/current_state/artifact_index`。
2. `archive_round` 当前归档目录结构。
3. `decision_packet.md` 和 `codex_execution_report.md` 当前模板格式。
4. `negative_results.json` 当前字段是否已有 `severity / do_not_repeat / override_allowed`。
5. `tests/test_project_state.py` 当前 fixture 和 helper。

如果已有等价能力，优先复用，不重复实现。

### 6. Implementation Scope

第一轮建议只实现：

- `schema_version`
- `state_build_id`
- `round_id`
- `state_digest`
- `based_on_state_digest`
- `workflow_status`
- `current_owner`
- `archive-round -> round_manifest.json`
- `tests/test_project_state.py` 对应测试

第二轮再实现：

- `decision_meta`
- `codex_report_summary`
- `latest_artifacts_v2 / freshness`
- `lint-decision`
- `project_state/schema.md`

### 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
```

如果本地有 `solve_reports`，再运行：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse
python -m reverse_agent.project_state archive-round
python -m reverse_agent.project_state status
```

如果实现了 lint：

```bash
python -m reverse_agent.project_state lint-decision
```

### 8. Stop Conditions

遇到以下情况必须停止：

1. 需要大规模重构 `project_state.py`。
2. 需要修改 `compare_aware_search` 主策略。
3. 需要引入外部依赖或服务。
4. 需要读取完整 `solve_reports` 才能完成。
5. 发现 `archive-round` 已有等价 `round_manifest` 实现。
6. 新字段会破坏旧 `task_packet/current_state/artifact_index` 消费方。
7. `tests/test_project_state.py` 需要大规模重写才能通过。
