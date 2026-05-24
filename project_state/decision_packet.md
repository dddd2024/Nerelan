```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260524_phase2_skill_centered_handoff_refactor",
  "round_id": "round_20260524_phase2_skill_centered_handoff_refactor",
  "based_on_state_build_id": "state_20260524_042629_10b992a9fad9",
  "based_on_state_digest": "10b992a9fad9e13c9c445709a1f2fb6cee05ed8450b451e0b3d2c80226af04fd",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2-draft",
    "project-state-handoff@v1-draft"
  ]
}
```

# DECISION_PACKET

本轮属于**工程架构改造支线**，不是 `samplereverse` 逆向解题主线。

当前 `task_packet.task` / `derived_task` 仍来自样本 artifact，内容是 `Improve compare lhs last-writer instrumentation`；本轮不要把它当作 Codex 当前任务。`task_packet.execution_scope = decision_packet_controls_current_round`，因此本轮执行权威以本 `project_state/decision_packet.md` 为准。

本轮目标来自已提交的长期计划：

```text
docs/phase2_compact_handoff_skill_hygiene_plan.md
```

本轮只执行 Phase 2A + Phase 2B 的最小可审计范围：审计并重写现有 `.codex-skills`，把 skill 从旧的动态状态备忘录改成 project_state-first 的长期流程规范层。不要推进逆向解题，不要运行 runtime harness。

## 1. Goal

本轮目标：

```text
1. 审计当前 .codex-skills 下的现有 skill，确认哪些内容已经 stale、哪些内容与当前 project_state-first 协作规范冲突。
2. 将 .codex-skills/reverse-agent-iteration/SKILL.md 改造成通用 project_state-first 工作流 skill。
3. 将 .codex-skills/samplereverse-frontier/SKILL.md 去动态事实化，或迁移/重命名为 sample profile skill；不得继续把当前 candidate、旧 run、旧 artifact path 写死在 active skill 中。
4. 在 docs/phase2_compact_handoff_skill_hygiene_plan.md 的基础上，补充本轮 skill inventory / stale audit 结果，或新增一个 bounded audit 文档。
5. 必要时小幅更新 AGENT_GUIDE_FOR_AI.md 中的 Codex Skill Workflow，使其指向 project_state-first 规范。
6. 不实现 registry / schema / lint-decision 的完整 Phase 2C-2F，除非非常小且不扩大 diff；本轮主要完成 Phase 2A + Phase 2B。
```

本轮不是求解 flag，不修 compare-aware search，不生成新的 reverse runtime artifact。

## 2. Current Evidence

当前任务主线判断：**工程架构改造支线**。

当前状态包显示：

```text
state_build_id = state_20260524_042629_10b992a9fad9
based_on_state_digest = 10b992a9fad9e13c9c445709a1f2fb6cee05ed8450b451e0b3d2c80226af04fd
execution_scope = decision_packet_controls_current_round
active_strategy = CompareAwareSearchStrategy
profile = samplereverse
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
```

这些样本字段解释了为什么旧 sample skill 容易 stale，但不构成本轮逆向执行任务。本轮只处理 skill / handoff 工程稳定性。

当前 `artifact_index.latest_artifacts_v2` 中存在大量 `stale` / `missing` artifact，同时当前 run 为：

```text
sr_lhs_hook_observation_reliability_20260524_r4
```

这进一步说明 active skill 不能写死旧 run、旧 candidate、旧 artifact path；动态事实必须从 `project_state/current_state.json` 和 `project_state/artifact_index.json` 读取。

当前已知 `.codex-skills` 至少包括：

```text
.codex-skills/reverse-agent-iteration/SKILL.md
.codex-skills/samplereverse-frontier/SKILL.md
```

当前 `tools/sync_codex_skills.ps1` 只负责从 `.codex-skills/<skill-name>/SKILL.md` 复制到 `$CODEX_HOME/skills`，不负责 stale 审计或 deprecated 控制。因此本轮必须先做 inventory，不要直接删除不确定 skill。

本轮应把 skill 职责重新定义为：

```text
skill 层：长期重复流程规范。
project_state 层：动态事实来源。
decision_packet 层：本轮差异任务。
lint/sync 层：后续约束检查与本地 Codex skill 发布。
```

## 3. Do Not Do

不要做以下事情：

```text
不要推进 samplereverse 解题。
不要修改 reverse_agent/strategies/compare_aware_search.py。
不要修改 reverse_agent/olly_scripts/*。
不要运行 samplereverse runtime harness。
不要运行 Base64/RC4 breakpoint probe。
不要回 old sample_solver blind search。
不要扩大 beam / topN / budget / timeout / frontier iteration。
不要提交完整 solve_reports。
不要默认读取完整 solve_reports。
不要默认读取 PROJECT_PROGRESS_LOG.txt。
不要把旧 candidate / 旧 run / 旧 artifact path 继续写入 active skill。
不要直接删除 skill，除非已有 inventory 证明它被安全迁移或标记 deprecated。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph runtime。
不要引入 PostgreSQL / Redis / Kubernetes。
不要引入联网下载第三方 skill 的流程。
不要让 sync 脚本自动删除 $CODEX_HOME/skills 下的未知本地 skill。
不要破坏旧 project_state JSON 字段兼容性。
```

还要避免 negative_results 中已有禁止方向：

```text
不要回 old sample_solver blind search。
不要只增加 guided_pool beam 或 budget。
不要使用 compare_semantics_agree=false candidates 作为主 frontier。
不要提交完整 solve_reports。
不要重复 Base64/RC4 breakpoint probe。
不要复用旧 [ebp-0x1170] 作为真实 LHS 证据。
```

## 4. Files To Inspect

必须检查：

```text
project_state/decision_packet.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
.codex-skills/reverse-agent-iteration/SKILL.md
.codex-skills/samplereverse-frontier/SKILL.md
tools/sync_codex_skills.ps1
AGENT_GUIDE_FOR_AI.md
docs/phase2_compact_handoff_skill_hygiene_plan.md
```

建议检查：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/schema.md
```

仅在需要确认现有 decision/report/status 解析和 skill_profiles 兼容性时读取。

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
历史 project_state/rounds/* 全量目录
```

如果必须读取历史 round，只能读取与 skill/handoff 工程支线直接相关的 bounded 文件，并在报告中说明原因。

## 5. Required Audit

Codex 修改前必须完成并在报告中记录以下审计：

```text
1. 读取本 decision_meta，确认本轮 decision_id = decision_20260524_phase2_skill_centered_handoff_refactor，status=APPROVED，mainline=engineering_branch。
2. 读取 task_packet，确认 task/derived_task 是样本派生任务，但 execution_scope 表明当前执行权威来自 decision_packet.md。
3. 读取 current_state，确认当前动态样本事实仍属于 project_state，不应写入 active skill。
4. 读取 artifact_index.latest_artifacts_v2，确认存在 current/stale/missing freshness 区分；active skill 不应绕过 artifact_index 直接指定旧 solve_reports 路径。
5. 读取 negative_results，确认本轮不会触发 old sample_solver、Base64/RC4 probe、完整 solve_reports commit 等禁止方向。
6. 审计 .codex-skills/reverse-agent-iteration/SKILL.md：
   - 是否默认读取 PROJECT_PROGRESS_LOG.txt；
   - 是否默认 inspect newest solve_reports/harness_runs/*；
   - 是否没有明确 project_state-first 读取顺序；
   - 是否混入样本动态事实。
7. 审计 .codex-skills/samplereverse-frontier/SKILL.md：
   - 是否写死 candidate hex；
   - 是否写死旧 run name；
   - 是否写死旧 artifact path；
   - 是否把动态 baseline 当长期事实；
   - 是否缺少 stale/deprecated 声明。
8. 审计 tools/sync_codex_skills.ps1：
   - 当前是否只复制 skill；
   - 是否不会删除本地未知 skill；
   - 是否支持按 SkillName 同步；
   - 本轮是否需要修改，还是留到 Phase 2F。
9. 审计 AGENT_GUIDE_FOR_AI.md：
   - Codex Skill Workflow 是否仍可用；
   - 是否需要补一句 project_state-first / 不要默认 PROJECT_PROGRESS_LOG / 不要默认 solve_reports。
10. 明确说明本轮不需要 runtime harness、不需要完整 solve_reports、不需要 PROJECT_PROGRESS_LOG。
```

## 6. Implementation Scope

### Phase A：Skill inventory / stale audit

生成或更新一个有界审计结果。允许形式二选一：

```text
1. 在 docs/phase2_compact_handoff_skill_hygiene_plan.md 中增加 “Current Skill Inventory” 小节；或
2. 新增 docs/phase2_skill_inventory_audit.md。
```

审计结果至少包含：

```text
skill_name
path
status_before
scope_before
contains_dynamic_facts
contains_project_progress_log_default
contains_full_solve_reports_default
contains_stale_run_or_candidate
recommended_action
```

### Phase B：改造 reverse-agent-iteration

将 `.codex-skills/reverse-agent-iteration/SKILL.md` 改成通用 project_state-first 工作流 skill。

必须包含：

```text
1. 默认读取顺序：
   - project_state/task_packet.json
   - project_state/current_state.json
   - project_state/artifact_index.json
   - project_state/negative_results.json
   - project_state/codex_execution_report.md
   - project_state/decision_packet.md
   - project_state/pytest_result.txt
2. 明确 decision_packet.md 是当前 Codex 执行权威。
3. 明确 task_packet.task / derived_task 只是建议任务或状态派生任务，不自动等于当前执行任务。
4. 明确 PROJECT_PROGRESS_LOG.txt 只在指定条件下读取。
5. 明确 solve_reports 只通过 artifact_index 有界读取。
6. 明确工程支线与逆向主线需要先判别，不要混淆。
7. 明确报告必须写入 project_state/codex_execution_report.md，并包含 codex_report_summary。
```

不得包含：

```text
当前 best candidate
当前 run name
当前 artifact path
默认读取 PROJECT_PROGRESS_LOG.txt tail
默认 inspect newest solve_reports/harness_runs/*
```

### Phase C：改造 samplereverse-frontier

允许两种实现方案。

方案 1：原地去动态事实化。

```text
保留 .codex-skills/samplereverse-frontier/SKILL.md，但将其改成 sample profile skill。
删除旧 candidate / 旧 run / 旧 artifact path。
强调当前事实必须从 project_state/current_state.json 与 artifact_index.json 读取。
```

方案 2：迁移为新 skill。

```text
新增 .codex-skills/samplereverse-profile/SKILL.md。
将 .codex-skills/samplereverse-frontier/SKILL.md 标记 deprecated，或移动到 .codex-skills/archive/samplereverse-frontier-20260423/SKILL.md。
```

无论选择哪种方案，active sample skill 必须只保留稳定约束：

```text
1. samplereverse 当前事实以 project_state 为准。
2. 使用 CompareAwareSearchStrategy 相关路径时必须检查 artifact freshness。
3. 不默认运行 Base64/RC4 breakpoint probe。
4. 不默认回 old sample_solver。
5. 不默认扩大 beam/topN/budget。
6. 不复用旧 [ebp-0x1170] 作为真实 LHS 来源，除非有新 runtime-backed provenance。
7. 不把 stale artifact 当 current evidence。
```

### Phase D：AGENT_GUIDE 小幅同步

如有必要，更新 `AGENT_GUIDE_FOR_AI.md` 中 Codex Skill Workflow 小节：

```text
1. 说明 repo-tracked skill source 位于 .codex-skills/<skill-name>/SKILL.md。
2. 说明 skill 是长期流程规范，不是动态状态事实来源。
3. 说明动态事实以 project_state 为准。
4. 说明同步命令仍是 tools/sync_codex_skills.ps1。
```

不要重写整个 AGENT_GUIDE。

### Phase E：暂不做或只做极小增强

本轮默认不实现以下内容，除非 diff 很小且测试简单：

```text
.codex-skills/registry.json
.codex-skills/schema.md
tools/audit_codex_skills.py
sync_codex_skills.ps1 -List/-Check/-DryRun
lint-decision skill_profiles 检查
```

这些留到后续 Phase 2C-2F。若 Codex 判断某个极小增强可以顺手完成，必须先确保不超过本轮 diff 和测试边界，并在报告中说明。

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py
```

如果只修改 `.codex-skills/*.md`、`docs/*.md`、`AGENT_GUIDE_FOR_AI.md`，且没有修改 Python 代码，上述测试仍建议运行，用于证明 project_state 基础门禁未被破坏。

必须运行或等价检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -SkillName reverse-agent-iteration
```

如果本地环境不允许真正同步到 `$CODEX_HOME/skills`，允许用临时目录替代：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -DestinationRoot <temp_dir>
```

如果修改了 `tools/sync_codex_skills.ps1`，必须补充：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -SkillName samplereverse-frontier -DestinationRoot <temp_dir>
```

不需要运行：

```bash
samplereverse runtime harness
Base64/RC4 breakpoint probe
old sample_solver
full pytest unrelated to project_state
完整 solve_reports scan
```

Codex 报告中必须记录真实运行的测试命令和结果。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. .codex-skills 目录在本地缺失，且无法从 Git 恢复。
2. reverse-agent-iteration 或 samplereverse-frontier 的内容与 GitHub 当前 main 不一致，存在未解释本地改动。
3. 需要读取完整 solve_reports 才能完成 skill 改造。
4. 需要读取完整 PROJECT_PROGRESS_LOG.txt 才能完成 skill 改造。
5. 需要运行 samplereverse runtime harness 才能判断 skill 是否有效。
6. 需要修改 compare_aware_search 或 olly_scripts 才能完成本轮。
7. 需要删除本地 $CODEX_HOME/skills 下的未知 skill 才能继续。
8. 无法安全判断 samplereverse-frontier 应该原地改写还是迁移 archive。
9. 修改会导致 active skill 继续写死 stale candidate/run/artifact。
10. 本轮 diff 超过 500 行，且不是文档/skill 小规模重构。
11. 测试命令无法运行且没有合理环境原因。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_phase2_skill_centered_handoff_refactor",
  "round_id": "round_20260524_phase2_skill_centered_handoff_refactor",
  "based_on_decision_id": "decision_20260524_phase2_skill_centered_handoff_refactor",
  "status": "SUCCESS / PARTIAL / FAILED / BLOCKED",
  "acceptance_recommendation": "ACCEPTED / NEEDS_REVIEW / REWORK_REQUIRED / BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [],
  "next_suggested_task": []
}
```

报告正文必须明确记录：

```text
1. 当前 skill inventory。
2. reverse-agent-iteration 改造前后的关键差异。
3. samplereverse-frontier 是原地去动态事实化，还是迁移为 samplereverse-profile/deprecated archive。
4. 是否仍有 active skill 默认读取 PROJECT_PROGRESS_LOG.txt。
5. 是否仍有 active skill 默认扫完整 solve_reports。
6. 是否仍有 active sample skill 写死 candidate/run/artifact。
7. sync_codex_skills.ps1 是否修改；如果未修改，说明为什么留到后续 Phase 2F。
8. 真实测试命令和结果。
9. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- reverse-agent-iteration 已改成 project_state-first。
- active skill 不再默认读取 PROJECT_PROGRESS_LOG.txt。
- active skill 不再默认扫完整 solve_reports。
- active samplereverse skill 不再写死当前 candidate/run/artifact。
- 已有 skill inventory / stale audit 记录。
- sync 脚本仍可同步至少 reverse-agent-iteration。
- tests 通过。
- 未修改逆向策略，未运行 runtime probe。

ACCEPTED_WITH_LIMITATIONS：
- 完成 inventory 和 reverse-agent-iteration 改造，但 samplereverse skill 只标记 deprecated 或仍需后续迁移。
- registry/schema/lint 未实现，但已明确留到后续 Phase 2C-2F。
- sync 脚本未增强，但未破坏原行为。

REWORK_REQUIRED：
- 未完成核心 skill 改造。
- active skill 仍默认读 PROJECT_PROGRESS_LOG.txt。
- active skill 仍默认扫完整 solve_reports。
- active sample skill 继续写死 stale run/candidate/artifact。
- 直接删除 skill 且无 inventory。
- 修改逆向策略或运行禁止 probe。
- codex_report_summary.based_on_decision_id 不匹配。

BLOCKED：
- 本地缺失 .codex-skills 且无法恢复。
- 无法判断当前 Git 状态或存在未解释冲突。
- 无法运行任何必要测试或同步检查。
```
