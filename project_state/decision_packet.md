```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260524_phase2_skill_registry_audit",
  "round_id": "round_20260524_phase2_skill_registry_audit",
  "based_on_state_build_id": "state_20260524_042629_10b992a9fad9",
  "based_on_state_digest": "10b992a9fad9e13c9c445709a1f2fb6cee05ed8450b451e0b3d2c80226af04fd",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2-draft"
  ]
}
```

# DECISION_PACKET

本轮属于**工程架构改造支线**，不是 `samplereverse` 逆向解题主线。

当前 `task_packet.task` / `derived_task` 仍来自样本 artifact，内容是 `Improve compare lhs last-writer instrumentation`；本轮不要把它当作 Codex 当前任务。`task_packet.execution_scope = decision_packet_controls_current_round`，因此本轮执行权威以本 `project_state/decision_packet.md` 为准。

上一轮 `decision_20260524_phase2_skill_centered_handoff_refactor` 已完成 Phase 2A + Phase 2B：active skill 已改成 project_state-first，`samplereverse-frontier` 已去动态事实化，测试通过。上一轮审计结论是 `ACCEPTED_WITH_LIMITATIONS`，主要限制是没有生成对应 round manifest；本轮不要尝试重构上一轮历史状态，但本轮结束时应尽量保证本轮 report / pytest / lint 状态可审计，并在可行时运行 `archive-round` 生成本轮归档。

本轮目标来自：

```text
docs/phase2_compact_handoff_skill_hygiene_plan.md
```

本轮只执行 Phase 2C + Phase 2D 的最小可审计范围：为 `.codex-skills` 增加 registry/schema，并新增一个轻量 skill audit 工具，机械检查 active skill 是否含有 forbidden defaults 或 stale dynamic facts。不要推进逆向解题，不要运行 runtime harness。

## 1. Goal

本轮目标：

```text
1. 新增 .codex-skills/schema.md，固化 skill frontmatter、registry、active/deprecated/archived、dynamic facts policy、forbidden defaults 等规范。
2. 新增 .codex-skills/registry.json，登记当前 repo-tracked skill，至少包括：
   - reverse-agent-iteration
   - samplereverse-frontier
3. 为当前 active skill 补齐最小 frontmatter 元数据：version、status、scope、owner、last_reviewed，并尽量包含 facts_policy / forbidden_defaults 等字段。
4. 新增 tools/audit_codex_skills.py，使用 Python 标准库完成 skill registry/frontmatter/内容审计。
5. 新增或扩展测试，验证 audit 工具能发现：
   - active skill 默认读取 PROJECT_PROGRESS_LOG.txt；
   - active skill 默认扫描完整 solve_reports 或 newest harness run；
   - sample profile active skill 写死 candidate hex、旧 run name、旧 artifact path；
   - registry 路径缺失或 frontmatter 缺失。
6. 更新 docs/phase2_compact_handoff_skill_hygiene_plan.md，标记 Phase 2C/2D 的实现约束与后续 Phase 2E/2F 剩余工作。
7. 本轮默认不改 sync_codex_skills.ps1；`-List/-Check/-DryRun/-IncludeDeprecated` 留到 Phase 2F，除非 Codex 证明改动极小且不会扩大测试面。
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

这些样本字段只是当前 `project_state` 的动态事实，不构成本轮逆向执行任务。

上一轮 Codex 报告显示：

```text
report_id = report_20260524_phase2_skill_centered_handoff_refactor
based_on_decision_id = decision_20260524_phase2_skill_centered_handoff_refactor
status = SUCCESS
acceptance_recommendation = ACCEPTED
files_changed = .codex-skills/reverse-agent-iteration/SKILL.md, .codex-skills/samplereverse-frontier/SKILL.md, AGENT_GUIDE_FOR_AI.md, docs/phase2_compact_handoff_skill_hygiene_plan.md, project_state/codex_execution_report.md, project_state/pytest_result.txt
```

上一轮测试记录显示：

```text
python -m py_compile reverse_agent/project_state.py = passed
python -m pytest -q tests/test_project_state.py = 126 passed
sync_codex_skills.ps1 reverse-agent-iteration temporary sync = passed
sync_codex_skills.ps1 samplereverse-frontier temporary sync = passed
python -m reverse_agent.project_state lint-report --state-dir project_state = passed, with expected not-archived warning
```

当前 `.codex-skills/reverse-agent-iteration/SKILL.md` 已经改成 project_state-first 工作流；当前 `.codex-skills/samplereverse-frontier/SKILL.md` 已经去掉旧 candidate/run/artifact path，变成 sample profile guardrail。

当前 `artifact_index.latest_artifacts_v2` 中存在大量 `stale` / `missing` artifact，同时当前 run 为：

```text
sr_lhs_hook_observation_reliability_20260524_r4
```

这说明本轮 audit 工具必须能阻止 active skill 绕过 `artifact_index`，避免重新把 stale run/candidate/artifact 写死进 skill。

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
不要把旧 candidate / 旧 run / 旧 artifact path 写入 active skill。
不要删除 skill，除非 registry/schema 明确标记 archive/deprecated 且有迁移说明；本轮默认不删除。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph runtime。
不要引入 PostgreSQL / Redis / Kubernetes。
不要引入联网下载第三方 skill 的流程。
不要让 sync 脚本自动删除 $CODEX_HOME/skills 下的未知本地 skill。
不要引入 PyYAML 或其它外部依赖；audit 工具必须使用 Python 标准库。
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
project_state/codex_execution_report.md
project_state/pytest_result.txt
.codex-skills/reverse-agent-iteration/SKILL.md
.codex-skills/samplereverse-frontier/SKILL.md
tools/sync_codex_skills.ps1
docs/phase2_compact_handoff_skill_hygiene_plan.md
AGENT_GUIDE_FOR_AI.md
```

需要实现时检查：

```text
reverse_agent/project_state.py
tests/test_project_state.py
tests/
```

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
历史 project_state/rounds/* 全量目录
```

如果必须读取历史 round，只能读取与 Phase 2 skill/handoff 工程支线直接相关的 bounded 文件，并在报告中说明原因。

## 5. Required Audit

Codex 修改前必须完成并在报告中记录以下审计：

```text
1. 读取本 decision_meta，确认本轮 decision_id = decision_20260524_phase2_skill_registry_audit，status=APPROVED，mainline=engineering_branch。
2. 读取 task_packet，确认 task/derived_task 是样本派生任务，但 execution_scope 表明当前执行权威来自 decision_packet.md。
3. 读取 current_state，确认当前动态样本事实仍属于 project_state，不应写入 active skill。
4. 读取 artifact_index.latest_artifacts_v2，确认 current/stale/missing freshness 仍是动态事实来源。
5. 读取 negative_results，确认本轮不会触发 old sample_solver、Base64/RC4 probe、完整 solve_reports commit 等禁止方向。
6. 读取上一轮 codex_execution_report.md 与 pytest_result.txt，确认上一轮 Phase 2A/2B 已完成且 tests 通过。
7. 审计当前 .codex-skills/reverse-agent-iteration/SKILL.md 是否已经 project_state-first；若不是，先报告 mismatch。
8. 审计当前 .codex-skills/samplereverse-frontier/SKILL.md 是否仍写死 candidate hex / run name / artifact path；若仍存在，优先修复，再做 registry/audit 工具。
9. 审计 tools/sync_codex_skills.ps1 当前行为；本轮除非必要，不修改 sync 脚本。
10. 明确说明本轮不需要 runtime harness、不需要完整 solve_reports、不需要 PROJECT_PROGRESS_LOG。
```

## 6. Implementation Scope

### Phase A：Skill schema

新增：

```text
.codex-skills/schema.md
```

内容至少包含：

```text
1. skill 目录结构：.codex-skills/<skill-name>/SKILL.md。
2. frontmatter 必填字段：name、description、version、status、scope、owner、last_reviewed。
3. status 枚举：active / deprecated / archived。
4. scope 枚举：generic_workflow / engineering_branch / reverse_solving / sample_profile / tool_usage。
5. facts_policy 规则：active 长期 workflow skill 默认不得存储动态事实。
6. forbidden_defaults 规则：不得默认读取完整 solve_reports、不得默认读取 PROJECT_PROGRESS_LOG、不得默认运行 runtime probe。
7. registry.json 结构与路径一致性规则。
8. audit 工具的最低检查项。
```

### Phase B：Skill registry

新增：

```text
.codex-skills/registry.json
```

最小内容：

```json
{
  "schema_version": 1,
  "skills": {
    "reverse-agent-iteration": {
      "path": ".codex-skills/reverse-agent-iteration/SKILL.md",
      "status": "active",
      "scope": "generic_workflow",
      "version": 2
    },
    "samplereverse-frontier": {
      "path": ".codex-skills/samplereverse-frontier/SKILL.md",
      "status": "active",
      "scope": "sample_profile",
      "version": 2
    }
  }
}
```

不要在 registry 中登记不存在的 skill。`project-state-handoff`、`reverse-solving-handoff`、`samplereverse-profile` 可以作为后续计划写入 docs，但本轮 registry 只登记当前实际存在且可审计的 skill，除非本轮显式新增对应目录和 `SKILL.md`。

### Phase C：Frontmatter 补齐

对当前 active skill 做最小补齐：

```text
.codex-skills/reverse-agent-iteration/SKILL.md
.codex-skills/samplereverse-frontier/SKILL.md
```

要求：

```text
1. name 与目录名一致。
2. version 与 registry 一致。
3. status=active。
4. scope 分别为 generic_workflow / sample_profile。
5. owner=project_state。
6. last_reviewed=2026-05-24 或当前日期。
7. 若添加 facts_policy / forbidden_defaults，audit 工具必须能解析或至少能忽略未知字段而不误报。
```

### Phase D：Audit 工具

新增：

```text
tools/audit_codex_skills.py
```

要求：

```text
1. 只使用 Python 标准库。
2. 默认从仓库根目录读取 .codex-skills/registry.json。
3. 检查 registry 是否存在、schema_version 是否存在、skills 是否为对象。
4. 检查每个 registry path 是否存在。
5. 检查每个 SKILL.md 是否有 frontmatter。
6. 检查 name/version/status/scope 是否存在且与 registry 一致。
7. 检查 active skill 是否包含 forbidden defaults：
   - 默认读取 PROJECT_PROGRESS_LOG.txt；
   - 默认扫描完整 solve_reports；
   - inspect newest solve_reports/harness_runs/*；
   - run runtime probe by default。
8. 检查 sample_profile active skill 是否包含明显动态事实：
   - candidate_hex / long hex candidate；
   - old run name pattern，如 *_202604* / *_202605* run；
   - direct solve_reports artifact path。
9. 输出 JSON 摘要，字段至少包含：status、skills_checked、errors、warnings。
10. 失败时 exit code 非 0；通过时 exit code 0。
```

注意：不要用粗暴字符串规则误杀合理的禁止语句。例如 skill 中出现 “Do not scan full solve_reports/ by default” 应视为合格，不应当作违规。Audit 工具至少要区分明显默认行为和禁止行为；如果无法可靠判断，输出 warning 而不是 hard error，并在测试中覆盖。

### Phase E：Tests

新增或扩展测试，建议新增：

```text
tests/test_codex_skills.py
```

测试至少覆盖：

```text
1. 当前 registry + 当前 skills audit 通过。
2. 缺失 registry path 会失败。
3. active skill 默认读取 PROJECT_PROGRESS_LOG tail 会失败或产生 hard error。
4. active skill 默认 inspect newest solve_reports/harness_runs/* 会失败或产生 hard error。
5. sample_profile skill 写死 candidate hex 或 direct solve_reports artifact path 会失败或产生 hard error。
6. 禁止句式如 “Do not scan full solve_reports/ by default” 不应误报为 hard error。
```

### Phase F：Docs update

更新：

```text
docs/phase2_compact_handoff_skill_hygiene_plan.md
```

记录：

```text
1. Phase 2C/2D 已计划或已完成的 schema/registry/audit tool。
2. Phase 2E/2F 仍剩余：decision_meta.skill_profiles lint-decision 集成、sync_codex_skills.ps1 -List/-Check/-DryRun/-IncludeDeprecated。
```

## 7. Tests

必须运行：

```bash
python -m py_compile tools/audit_codex_skills.py
python tools/audit_codex_skills.py
python -m pytest -q tests/test_codex_skills.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果修改了 `reverse_agent/project_state.py`，必须额外运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py
```

如果修改了 `tools/sync_codex_skills.ps1`，必须额外运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -SkillName samplereverse-frontier -DestinationRoot <temp_dir>
```

本轮默认不修改 sync 脚本，但可以运行现有同步检查作为非阻断验证：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
```

不需要运行：

```bash
samplereverse runtime harness
Base64/RC4 breakpoint probe
old sample_solver
full pytest unrelated to project_state / codex skill audit
完整 solve_reports scan
```

本轮结束时建议运行：

```bash
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果 `archive-round` 能安全归档当前 round，允许运行：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state
```

但不要为了归档当前 round 反向重构上一轮已覆盖的 decision_packet；上一轮未归档作为已知限制记录即可。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. .codex-skills 目录在本地缺失，且无法从 Git 恢复。
2. 当前 skill 内容与上一轮报告描述明显不一致，且无法解释。
3. registry/schema 需要引入外部 YAML/JSON schema 依赖才能实现。
4. audit 工具需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG 才能判断。
5. audit 工具无法避免把 “Do not scan full solve_reports” 这类禁止句误判为违规。
6. 需要运行 samplereverse runtime harness 才能判断 skill 是否有效。
7. 需要修改 compare_aware_search 或 olly_scripts 才能完成本轮。
8. 需要删除本地 $CODEX_HOME/skills 下的未知 skill 才能继续。
9. 需要大规模改写 sync_codex_skills.ps1，超过 Phase 2D 范围。
10. 本轮 diff 超过 600 行，且主要不是 schema/registry/audit/tests/docs。
11. 测试命令无法运行且没有合理环境原因。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_phase2_skill_registry_audit",
  "round_id": "round_20260524_phase2_skill_registry_audit",
  "based_on_decision_id": "decision_20260524_phase2_skill_registry_audit",
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
1. registry.json 中登记了哪些 skill。
2. schema.md 定义了哪些字段和状态。
3. audit_codex_skills.py 的检查项、输出格式和失败策略。
4. 是否补齐 active skill frontmatter。
5. audit 工具是否能检测 PROJECT_PROGRESS_LOG 默认读取、完整 solve_reports 默认扫描、sample dynamic facts。
6. 是否修改 sync_codex_skills.ps1；如果没有，说明留到 Phase 2F。
7. 真实测试命令和结果。
8. 是否运行 archive-round；如果未运行，说明原因。
9. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- .codex-skills/schema.md 存在且覆盖核心 skill 元数据语义。
- .codex-skills/registry.json 存在且只登记实际存在的 skill。
- active skill frontmatter 与 registry 一致。
- tools/audit_codex_skills.py 存在，使用标准库，可输出 JSON，可返回正确 exit code。
- audit 工具能发现 forbidden defaults 和 sample dynamic facts，且不会误杀禁止句式。
- tests 通过。
- 未修改逆向策略，未运行 runtime probe。

ACCEPTED_WITH_LIMITATIONS：
- registry/schema/audit 工具完成，但测试只覆盖最小路径；或 audit 对部分复杂自然语言只能 warning。
- 未做 archive-round，但 lint-report/status 清楚记录限制。
- 未创建 project-state-handoff / reverse-solving-handoff 独立 skill，但已明确留到后续。

REWORK_REQUIRED：
- registry 登记不存在的 active skill。
- active skill frontmatter 与 registry 不一致。
- audit 工具误把 “Do not scan full solve_reports” 当作违规 hard error。
- audit 工具不能发现明显 candidate hex / stale run / direct solve_reports path。
- 引入外部依赖。
- 修改逆向策略或运行禁止 probe。
- codex_report_summary.based_on_decision_id 不匹配。

BLOCKED：
- 本地缺失 .codex-skills 且无法恢复。
- 无法运行 Python 或 pytest 基础测试。
- 当前 Git 状态存在未解释冲突。
```
