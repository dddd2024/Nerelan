```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260523_engineering_artifact_hygiene_sidecar_health_schema",
  "round_id": "round_20260523_engineering_artifact_hygiene_sidecar_health_schema",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮属于工程架构改造支线，不推进 `samplereverse` 逆向解题主线。

核心目标：解决两个导致 Codex 每轮 diff 过大的工程根因：

```text
A. artifact hygiene：
   archive-round 默认把 git_diff.patch、current_state.json、artifact_index.json 等历史快照写入
   project_state/rounds/，并且这些文件未被 Git 忽略，导致每轮改动量被生成物撑大。

B. sidecar health schema：
   sidecar 运行状态字段在 sidecar payload、compare_aware_search.py、candidate metadata、
   stage_fields、final artifact、fixture、report 中多层重复搬运，导致小字段变成大 diff。
```

本轮只做轻量、兼容旧字段、可测试的小步改造。不要引入重型 runtime、数据库或平台化依赖。

## 1. Goal

本轮目标：

```text
1. 将 archive-round 默认行为改成 minimal archive，避免默认生成 git_diff.patch 和完整 state snapshot。
2. 增加显式开关：只有用户/Codex 明确传参时，才归档完整 state snapshot 或 git diff。
3. 更新 .gitignore，阻止新的 round 大快照和 git_diff.patch 继续进入 Git。
4. 建立统一 sidecar_health schema / normalizer，减少 sidecar 状态字段在多层手工复制。
5. 至少把当前 last-writer / hook-install 相关 sidecar 路径接入 sidecar_health。
6. 保留旧 top-level 字段兼容，不破坏现有消费者和测试。
7. 增加测试证明 archive minimal mode 与 sidecar_health normalizer 行为。
```

期望最终边界：

```text
Git 保留：
- 当前活跃 project_state/*.json
- 当前 decision_packet.md
- 当前 codex_execution_report.md
- 当前 pytest_result.txt
- 每轮 round_manifest.json
- 每轮 decision_packet.md / codex_execution_report.md / pytest_result.txt

Git 默认不保留：
- project_state/rounds/*/git_diff.patch
- project_state/rounds/*/current_state.json
- project_state/rounds/*/artifact_index.json
- project_state/rounds/*/negative_results.json
- project_state/rounds/*/model_gate.json
- project_state/rounds/*/task_packet.json
```

## 2. Current Evidence

当前任务主线判断：工程架构改造支线。

当前仓库中的 `task_packet.json` 仍主要来自样本状态派生，`task_packet.task` / `derived_task` 不是本轮工程支线的执行目标。本轮 Codex 实际执行权威以 `project_state/decision_packet.md` 为准。

当前已观察到两个工程问题：

```text
1. archive-round 归档膨胀：
   reverse_agent/project_state.py 中 archive_round 会通过 _archive_source_file_bytes()
   复制 ARCHIVE_STATE_NAMES，并写入 git_diff.patch。
   git_diff.patch 来自 git diff --no-ext-diff。
   project_state/rounds 下的 git_diff.patch 与完整 JSON 快照会显著放大每轮 Git diff。

2. sidecar 字段重复搬运：
   最近 sidecar 报告已经包含大量 lifecycle / hook / message / subprocess 字段，例如：
   - js_top_level_seen
   - js_hooks_install_begin_seen
   - js_hooks_installed_seen
   - python_message_count_total
   - python_message_decode_error_count
   - module_base_resolution_status
   - hook_install_status
   - hook_count
   - requested_hook_count
   - same_process_compare_args_captured
   - diagnostic_compare_args_captured
   - subprocess_returncode
   - subprocess_timed_out
   - script_load_status

   这些字段有价值，但目前新增字段通常要在多层重复搬运，导致 compare_aware_search.py、
   final artifact、candidate metadata、fixture 和 report 同时膨胀。
```

成熟项目管理原则，用于本轮设计约束：

```text
1. 源码仓库应主要保存源码、配置、少量当前 handoff 状态；运行日志、完整 diff、临时快照不应默认提交。
2. build output / report files / runtime logs 更适合按 artifact 管理，而不是长期混进源码树。
3. 运行观测字段应有统一 schema / semantic convention，避免每个消费层自定义和手工复制字段。
4. 归档应默认最小化，需要完整快照时使用显式开关。
5. 旧字段消费者必须被兼容，改造优先 additive。
```

当前活跃审计入口仍需要保留：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/model_gate.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

## 3. Do Not Do

不要做以下事情：

```text
不要推进 samplereverse 逆向 sidecar。
不要运行 Base64/RC4 breakpoint probe。
不要运行任何 runtime probe。
不要扩大 beam、budget、timeout、topN、frontier iteration。
不要读取完整 solve_reports。
不要修改 PROJECT_PROGRESS_LOG.txt。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph。
不要引入 PostgreSQL / Redis / Kubernetes。
不要把所有 project_state 文件都从 Git 移除。
不要删除当前 active project_state/*.json。
不要破坏旧字段消费者；所有 sidecar_health 改动必须 additive / backward-compatible。
不要一次性重构整个 compare_aware_search.py。
不要把 schema 做成重依赖系统；优先使用 dataclass / TypedDict / 普通 dict normalizer。
不要自动删除用户历史 round 文件；如需解除 Git 跟踪，只在报告中给出 git rm --cached 建议。
不要把历史 project_state/rounds 下的大文件继续作为必须提交的审计依据。
不要让本轮 diff 超过 1000 行；若超过，必须停止并报告原因。
```

## 4. Files To Inspect

必须检查：

```text
.gitignore
reverse_agent/project_state.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_lhs_last_writer_provenance.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
tests/test_project_state.py
tests/test_compare_aware_search_strategy.py
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必要时检查：

```text
project_state/rounds/<latest>/round_manifest.json
project_state/rounds/<latest>/git_diff.patch
docs/phase1_project_state_stability_plan.md
docs/phase2_harness_reproducibility_completion.md
```

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
```

## 5. Required Audit

Codex 修改前必须先完成并在报告中记录以下审计：

```text
1. 列出 archive-round 当前默认归档哪些文件。
2. 确认 git_diff.patch 当前是否由 archive-round 默认生成。
3. 统计 project_state/rounds 下哪些文件类型是主要 diff 膨胀来源。
4. 判断这些 round 大文件是否已经被 Git 跟踪；如已跟踪，只报告 git rm --cached 建议，不自动删除历史。
5. 列出 sidecar health 字段当前在哪些层重复出现。
6. 找出 compare_aware_search.py 中负责 candidate metadata / stage_fields / final artifact 字段搬运的函数或代码块。
7. 找出 tests fixture 中重复校验单个 sidecar 字段的地方。
8. 确认本轮不会破坏 GPT 审计入口文件。
9. 确认本轮不会运行逆向 runtime probe。
```

## 6. Implementation Scope

### Phase A：archive-round minimal mode

修改 `reverse_agent/project_state.py`：

```text
1. 将 archive_round 默认模式改成 minimal archive。
2. minimal archive 默认只归档：
   - decision_packet.md
   - codex_execution_report.md
   - pytest_result.txt
   - round_manifest.json
3. 增加 CLI 参数：
   - --include-state-snapshot
   - --include-diff
4. 只有显式传 --include-state-snapshot 时，才归档：
   - artifact_index.json
   - current_state.json
   - negative_results.json
   - model_gate.json
   - task_packet.json
5. 只有显式传 --include-diff 时，才生成 git_diff.patch。
6. round_manifest.json 增加 additive 字段：
   - archive_mode: "minimal" | "state_snapshot" | "full"
   - included_diff: bool
   - included_state_snapshot: bool
   - omitted_files: list[str]
7. 保持旧 round_manifest.files 字段兼容。
8. 保持 pack_context 逻辑可用，但不要让 pack_context 依赖默认存在 git_diff.patch。
```

### Phase B：.gitignore 规则

修改 `.gitignore`，新增：

```gitignore
project_state/rounds/*/git_diff.patch
project_state/rounds/*/artifact_index.json
project_state/rounds/*/current_state.json
project_state/rounds/*/negative_results.json
project_state/rounds/*/model_gate.json
project_state/rounds/*/task_packet.json
```

如果这些文件已被 Git 跟踪，Codex 只在报告中给出建议命令，不自动执行：

```bash
git rm --cached project_state/rounds/*/git_diff.patch
git rm --cached project_state/rounds/*/artifact_index.json
git rm --cached project_state/rounds/*/current_state.json
git rm --cached project_state/rounds/*/negative_results.json
git rm --cached project_state/rounds/*/model_gate.json
git rm --cached project_state/rounds/*/task_packet.json
```

### Phase C：sidecar_health normalizer

新增文件：

```text
reverse_agent/sidecar_health.py
```

实现最低功能：

```text
1. 定义 normalize_sidecar_health(raw: dict) -> dict。
2. 定义 summarize_sidecar_health(health: dict) -> dict。
3. 定义 merge_candidate_sidecar_health(candidate_payload: dict, sidecar_payload: dict) -> dict。
4. 将已知 flat fields 归入统一结构：
   - lifecycle
   - subprocess
   - frida
   - hook_install
   - message_bridge
   - observations
   - fallback
   - classification
5. 未识别字段放入 health["extra"]，避免丢字段。
6. sidecar_health 必须包含 schema_version = 1。
7. 旧 flat fields 仍保留在 artifact 中，sidecar_health 是新增统一视图。
```

建议结构：

```python
sidecar_health = {
    "schema_version": 1,
    "lifecycle": {
        "script_load_status": "...",
        "js_top_level_seen": True,
        "js_hooks_install_begin_seen": True,
        "js_hooks_installed_seen": True,
    },
    "subprocess": {
        "subprocess_returncode": 124,
        "subprocess_timed_out": True,
    },
    "message_bridge": {
        "python_message_count_total": 47,
        "python_message_decode_error_count": 0,
    },
    "hook_install": {
        "hook_install_status": "installed",
        "hook_count": 3,
        "requested_hook_count": 3,
        "hook_address_by_name": {},
        "per_hook_install_results": [],
    },
    "observations": {
        "same_process_compare_args_captured": False,
        "diagnostic_compare_args_captured": True,
    },
    "fallback": {
        "compare_probe_fallback_used": True,
        "compare_probe_fallback_is_provenance": False,
    },
    "classification": {
        "instrumentation_failure_stage": "hook_not_hit",
        "root_cause_hypothesis": "hook_not_hit",
    },
    "extra": {},
}
```

### Phase D：接入 compare_aware_search.py，但不大规模重构

修改原则：

```text
1. 保留现有 top-level 字段，避免旧测试和旧消费者损坏。
2. 在 final artifact 和 candidate metadata 中新增 sidecar_health。
3. stage_fields 聚合优先从 summarize_sidecar_health() 获取核心字段。
4. 后续新增 sidecar 状态字段时，必须先进入 sidecar_health.py。
5. 不允许为每个新字段继续在 compare_aware_search.py 多处手写复制逻辑。
```

最低接入范围：

```text
- compare_lhs_last_writer_provenance 相关 sidecar payload。
- hook-install / message bridge / subprocess lifecycle 相关字段。
- tests 中至少覆盖 hook_not_hit、hook_installed、message_bridge_health、unknown extra 字段。
```

### Phase E：diff budget / archive guard

新增轻量检测或测试：

```text
1. archive-round 默认不生成 git_diff.patch。
2. archive-round 默认不归档完整 state snapshot。
3. archive-round --include-diff 才生成 git_diff.patch。
4. archive-round --include-state-snapshot 才归档完整 state JSON。
5. 如果 git diff 中出现 project_state/rounds/*/git_diff.patch，报告为 generated archive pollution。
```

可以实现为测试 helper，不要求接入正式 CI。

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/project_state.py reverse_agent/sidecar_health.py reverse_agent/strategies/compare_aware_search.py
python -m pytest -q tests/test_project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "sidecar_health or compare_lhs_last_writer or archive"
python -m pytest -q tests/test_compare_aware_search_strategy.py
```

如果新增独立测试文件，额外运行：

```bash
python -m pytest -q tests/test_sidecar_health.py
```

必须新增或更新测试覆盖：

```text
1. archive-round 默认不生成 git_diff.patch。
2. archive-round 默认不归档 current_state.json / artifact_index.json / negative_results.json / model_gate.json / task_packet.json。
3. archive-round --include-diff 会生成 git_diff.patch。
4. archive-round --include-state-snapshot 会归档完整 state JSON。
5. round_manifest 记录 archive_mode / included_diff / included_state_snapshot / omitted_files。
6. normalize_sidecar_health 能从旧 flat payload 生成 sidecar_health。
7. unknown sidecar 字段进入 extra，不丢字段。
8. compare_aware_search final artifact 同时保留旧 flat fields 和新增 sidecar_health。
9. hook 安装失败、hook 已安装但未命中、message bridge 正常、subprocess timeout 能被 sidecar_health 正确表达。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. 发现 project_state/rounds 下历史大文件已经大量被 Git 跟踪，需要用户确认是否执行 git rm --cached。
2. 修改 archive-round 会破坏 tests/test_project_state.py 大量旧语义，超过小步兼容范围。
3. sidecar_health 接入需要重写 compare_aware_search.py 大段逻辑。
4. 无法在不运行 runtime probe 的情况下构造测试 fixture。
5. 需要读取完整 solve_reports 才能继续。
6. 本轮 diff 超过 1000 行，且主要不是测试或必要兼容逻辑。
7. 发现当前 project_state active 文件缺失或 decision/report 状态不可审计。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含 `codex_report_summary`，并明确记录：

```text
1. 是否完成 archive minimal mode。
2. 是否完成 .gitignore 规则。
3. 是否发现已被 Git 跟踪的历史 round 大文件。
4. 是否新增 sidecar_health.py。
5. compare_aware_search.py 中减少了哪些重复字段搬运。
6. 哪些旧字段保留兼容。
7. 哪些测试真实运行。
8. git diff --stat 输出摘要。
9. 本轮是否没有运行任何 samplereverse runtime probe。
```

验收标准：

```text
ACCEPTED：
- archive-round 默认不再生成 git_diff.patch。
- archive-round 默认不再复制完整 state snapshot。
- .gitignore 阻止新的 round 大快照进入 Git。
- sidecar_health normalizer 已建立并至少接入一个当前 sidecar 路径。
- 旧字段兼容保留。
- 测试通过。
- diff 主要集中在 project_state.py、sidecar_health.py、相关测试和少量 compare_aware_search.py。

REWORK_REQUIRED：
- 仍默认生成 git_diff.patch。
- 仍默认归档完整 current_state/artifact_index。
- 为了 sidecar_health 大规模重写 compare_aware_search.py。
- 删除 active project_state 文件。
- 运行了逆向 runtime probe。
- 测试缺失或报告没有真实命令。
```
