# Phase 2 工程计划：Skill-Centered Handoff Refactor

本计划用于指导 reverse-agent 的第二阶段工程支线改造。Phase 2 不推进 `samplereverse` 解题，不修改逆向策略，不运行 runtime probe；目标是把长期重复工作流程沉淀到 `.codex-skills/`，让 `project_state` 继续作为动态事实来源，让 `decision_packet.md` 只承载本轮差异任务。

## 1. 背景与问题

当前协作已经形成了较稳定的 `project_state` 闭环：

1. Web GPT 负责读取状态、审查 Codex 结果、生成下一轮决策。
2. Codex 负责本地仓库执行、审计、修改、测试、写入报告。
3. `project_state/task_packet.json`、`current_state.json`、`artifact_index.json`、`negative_results.json`、`decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt` 是默认事实来源。
4. `PROJECT_PROGRESS_LOG.txt` 是人工总账，不应作为每轮默认上下文。
5. `solve_reports/` 是运行产物，不应被默认全量读取，应通过 `artifact_index.latest_artifacts_v2` 做有界引用。

但当前存在两个工程问题：

1. 每轮 `decision_packet.md` 都重复大量固定协议，例如 Do Not Do、Tests、Stop Conditions、report schema、artifact freshness 规则。
2. 仓库已有 `.codex-skills/`，但 skill 内容仍带有早期工作流痕迹，尤其是默认读 `PROJECT_PROGRESS_LOG.txt`、默认检查最新 `solve_reports/harness_runs/*`、把旧 `samplereverse` 候选和 run 名写死到 skill 中。

因此 Phase 2 的目标不是简单“删掉旧 skill”，而是把 skill 正式升级为长期流程规范层。

## 2. 总体设计

Phase 2 采用四层分工：

```text
skill 层：长期重复流程规范。
project_state 层：动态事实来源。
decision_packet 层：本轮差异任务。
lint/sync 层：约束检查与本地 Codex skill 发布。
```

核心原则：

```text
1. skill 负责稳定流程，不负责记录当前候选、当前 run、当前 artifact freshness。
2. project_state 负责动态事实，例如 current_state、artifact_index、negative_results、decision/report 状态。
3. decision_packet 只写本轮目标、证据差异、允许改动范围、额外约束和测试。
4. lint 负责保证短 decision 不丢失长期约束。
5. sync 脚本负责安全同步 active skill，不默认同步 deprecated skill。
```

## 3. 当前 skill 资产

当前仓库已有：

```text
.codex-skills/reverse-agent-iteration/SKILL.md
.codex-skills/samplereverse-frontier/SKILL.md
tools/sync_codex_skills.ps1
AGENT_GUIDE_FOR_AI.md 中的 Codex Skill Workflow 说明
```

### 3.0 Current Skill Inventory / Stale Audit

本审计基于 `decision_20260524_phase2_skill_centered_handoff_refactor`，时间点为 2026-05-24。本轮只审计 repo-tracked `.codex-skills`，不读取完整 `solve_reports/`，不读取完整 `PROJECT_PROGRESS_LOG.txt`，不运行 runtime harness。

| skill_name | path | status_before | scope_before | contains_dynamic_facts | contains_project_progress_log_default | contains_full_solve_reports_default | contains_stale_run_or_candidate | recommended_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `reverse-agent-iteration` | `.codex-skills/reverse-agent-iteration/SKILL.md` | active source, pre-v2 workflow | generic reverse-agent iteration | no sample candidate facts, but artifact workflow assumed dynamic latest run discovery | yes, `Start Every Iteration` required reading `PROJECT_PROGRESS_LOG.txt` tail | yes, required inspecting newest `solve_reports/harness_runs/*` | no candidate hex, but latest harness discovery could bypass `artifact_index` freshness | rewrite in place as project_state-first generic workflow skill |
| `samplereverse-frontier` | `.codex-skills/samplereverse-frontier/SKILL.md` | active source, stale sample handoff | sample-specific frontier handoff | yes, included baselines, metrics, run name, and preferred artifact paths | no | yes, preferred newest matching harness/tool artifact path outside `artifact_index` | yes, included exact1/exact2 candidate hex and `samplereverse_exact1_borderline_escape_20260423` | rewrite in place as stable sample profile guardrail |

Additional audit notes:

```text
1. decision_packet.md is APPROVED and mainline=engineering_branch.
2. task_packet.task / derived_task are sample-derived, but execution_scope=decision_packet_controls_current_round makes the decision packet authoritative.
3. current_state keeps dynamic sample facts under project_state: profile=samplereverse, active_strategy=CompareAwareSearchStrategy, current_bottleneck.reason=compare_lhs_runtime_backed_writer_missing.
4. artifact_index.latest_artifacts_v2 has current/stale/missing freshness, including current run sr_lhs_hook_observation_reliability_20260524_r4 and multiple stale legacy artifacts.
5. negative_results blocks old sample_solver, Base64/RC4 probe repetition before real LHS producer identification, full solve_reports commit, and reuse of old [ebp-0x1170] without runtime-backed provenance.
6. tools/sync_codex_skills.ps1 only copies repo skills to a destination root, supports -SkillName, and does not delete unknown local skills; Phase 2F should handle registry/list/check/dry-run behavior later.
7. AGENT_GUIDE_FOR_AI.md already states project_state-first startup and bounded solve_reports reads, but Codex Skill Workflow needed a tighter statement that skills are stable workflow sources, not dynamic fact storage.
```

### 3.1 reverse-agent-iteration

定位：通用 reverse-agent 迭代工作流。

当前问题：

```text
1. Start Every Iteration 仍要求默认读取 AGENT_GUIDE_FOR_AI.md。
2. 仍要求读取 PROJECT_PROGRESS_LOG.txt tail。
3. 仍要求 inspect newest solve_reports/harness_runs/*。
4. 这与当前 project_state-first 协作规范冲突。
```

改造方向：

```text
1. 改成 project_state-first 默认读取顺序。
2. 明确 task_packet.task / derived_task 只是建议任务，当前执行权威以 decision_packet.md 为准。
3. 明确只有在状态缺失、context_level=3、战略复盘或状态冲突时才读 PROJECT_PROGRESS_LOG.txt。
4. 明确 solve_reports 只能通过 artifact_index 有界读取。
5. 明确工程支线和逆向解题主线的判别规则。
```

### 3.2 samplereverse-frontier

定位：早期 `samplereverse` 样本事实和 frontier 工作流。

当前问题：

```text
1. 写死 L15(prefix8)、exact1/exact2 baseline、候选 hex、旧 run 名。
2. 写死 2026-04 的 frontier/refine 默认方向。
3. 这些事实已经可能 stale，且应由 project_state/current_state/artifact_index 维护。
```

改造方向：

```text
1. 改名或重写为 samplereverse-profile。
2. 删除当前 best candidate、旧 run、旧 artifact path 等动态事实。
3. 只保留稳定约束：使用 CompareAwareSearchStrategy、优先 artifact_index、遵守 negative_results、不默认 Base64/RC4 probe、不回 old sample_solver、不默认扩大 beam/topN/budget。
4. 若保留旧内容，应移动到 archive 并标记 deprecated。
```

## 4. 目标目录结构

Phase 2 完成后建议形成：

```text
.codex-skills/
  reverse-agent-iteration/
    SKILL.md
  project-state-handoff/
    SKILL.md
  reverse-solving-handoff/
    SKILL.md
  samplereverse-profile/
    SKILL.md
  archive/
    samplereverse-frontier-20260423/
      SKILL.md
  registry.json
  schema.md

tools/
  sync_codex_skills.ps1
  audit_codex_skills.py

docs/
  phase2_compact_handoff_skill_hygiene_plan.md
```

## 5. Skill 职责划分

### 5.1 reverse-agent-iteration

通用入口 skill，不含样本动态事实。

职责：

```text
1. 确认工作区是 reverse-agent。
2. 使用 project_state-first 读取顺序。
3. 判别工程支线 vs 逆向解题主线。
4. 说明 Web GPT / Codex 分工。
5. 说明默认禁止完整 solve_reports 和 PROJECT_PROGRESS_LOG。
6. 说明报告必须写入 codex_execution_report.md。
```

### 5.2 project-state-handoff

工程支线 skill。

职责：

```text
1. 维护 decision_meta / codex_report_summary / pytest_result_summary。
2. 维护 artifact_index.latest_artifacts_v2 provenance/freshness。
3. 维护 archive-round / round_manifest 可回放语义。
4. 维护 lint-decision / lint-report / status 输出。
5. 约束工程支线不推进 samplereverse 解题。
```

### 5.3 reverse-solving-handoff

逆向解题主线 skill。

职责：

```text
1. 默认读取 current_state、artifact_index、negative_results、decision_packet。
2. 必须检查 latest_artifacts_v2 freshness。
3. 不重复 negative_results 中已禁止方向。
4. 不默认扩大 beam/topN/budget/timeout。
5. 不默认回 old sample_solver。
6. 不默认运行 Base64/RC4 probe。
7. 不默认读取完整 solve_reports。
```

### 5.4 samplereverse-profile

样本 profile skill，只保留稳定样本约束，不写动态事实。

职责：

```text
1. 指出 samplereverse 使用 CompareAwareSearchStrategy 相关路径。
2. 当前瓶颈、candidate、run、artifact 必须从 project_state 读取。
3. Base64/RC4 material producer 必须有新 instruction-level evidence 才能升级。
4. 不复用旧 [ebp-0x1170] 作为真实 LHS 来源。
5. 不把 stale artifact 当 current 证据。
```

## 6. Skill frontmatter 规范

每个 active skill 顶部必须有 frontmatter：

```yaml
---
name: reverse-agent-iteration
version: 2
status: active
scope: generic_workflow
owner: project_state
activation:
  mainlines:
    - engineering
    - reverse_solving
facts_policy:
  dynamic_facts_allowed: false
  source_of_truth:
    - project_state/task_packet.json
    - project_state/current_state.json
    - project_state/artifact_index.json
forbidden_defaults:
  - read_full_solve_reports
  - read_project_progress_log_by_default
  - run_runtime_probe_without_decision
last_reviewed: "2026-05-24"
---
```

字段语义：

```text
name: skill 名称，必须等于目录名或在 registry 中声明 alias。
version: 整数版本。
status: active / deprecated / archived。
scope: generic_workflow / engineering_branch / reverse_solving / sample_profile / tool_usage。
owner: 事实归属，通常为 project_state。
activation.mainlines: 适用主线。
facts_policy.dynamic_facts_allowed: active 长期流程 skill 默认 false。
facts_policy.source_of_truth: 该 skill 允许依赖的事实来源。
forbidden_defaults: 该 skill 明确禁止的默认行为。
last_reviewed: 最近审查日期。
```

## 7. registry.json 规范

新增 `.codex-skills/registry.json`：

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
    "project-state-handoff": {
      "path": ".codex-skills/project-state-handoff/SKILL.md",
      "status": "active",
      "scope": "engineering_branch",
      "version": 1
    },
    "reverse-solving-handoff": {
      "path": ".codex-skills/reverse-solving-handoff/SKILL.md",
      "status": "active",
      "scope": "reverse_solving",
      "version": 1
    },
    "samplereverse-profile": {
      "path": ".codex-skills/samplereverse-profile/SKILL.md",
      "status": "active",
      "scope": "sample_profile",
      "version": 1
    }
  }
}
```

registry 用于：

```text
1. 给 sync 脚本确定 active/deprecated skill。
2. 给 lint-decision 校验 skill_profiles 是否存在。
3. 给 audit 脚本检查 skill frontmatter 与 registry 是否一致。
```

## 8. decision_packet 压缩方案

在 `decision_meta` 中增加 additive 字段：

```json
{
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "project-state-handoff@v1"
  ]
}
```

兼容规则：

```text
1. skill_profiles 是 additive 字段，不破坏旧 decision_meta 解析。
2. 如果缺失 skill_profiles，lint 只 warning，不 hard fail，避免破坏历史包。
3. 新工程支线 decision 必须声明 skill_profiles。
4. skill_profiles 引用的 skill 必须存在且 status=active。
```

压缩后的 `decision_packet.md` 只需要写：

```text
1. Goal
2. Current Evidence
3. Delta Scope
4. Extra Constraints
5. Tests
6. Stop Conditions
```

固定协议由 skill profile 承载，包括：

```text
1. 默认事实读取顺序。
2. 工程支线 / 逆向支线边界。
3. artifact freshness 规则。
4. negative_results 规则。
5. Codex report schema。
6. 测试和状态命令纪律。
```

## 9. lint / audit 设计

### 9.1 新增 tools/audit_codex_skills.py

检查项：

```text
1. .codex-skills/registry.json 是否存在。
2. registry 中每个 path 是否存在。
3. 每个 SKILL.md 是否有 frontmatter。
4. name/version/status/scope 是否存在。
5. active skill 是否含有 deprecated/stale signal。
6. active skill 是否默认要求读取 PROJECT_PROGRESS_LOG.txt。
7. active skill 是否默认要求扫完整 solve_reports。
8. sample_profile skill 是否写死 candidate hex / run name / artifact path。
9. deprecated skill 是否不会被默认 sync。
```

输出格式：

```json
{
  "status": "passed|failed",
  "skills_checked": 4,
  "errors": [],
  "warnings": []
}
```

### 9.2 增强 lint-decision

新增检查项：

```text
1. decision_meta.skill_profiles 是否存在。
2. skill profile 是否存在于 registry。
3. skill profile 是否 status=active。
4. 工程支线是否引用 project-state-handoff。
5. 逆向主线是否引用 reverse-solving-handoff。
6. decision 是否违反 skill forbidden_defaults。
```

### 9.3 增强 sync_codex_skills.ps1

新增参数建议：

```powershell
-List
-Check
-DryRun
-IncludeDeprecated
```

语义：

```text
-List: 列出 registry 和目录中发现的 skill。
-Check: 调用或等价执行 skill audit。
-DryRun: 显示将同步哪些 skill，不复制。
-IncludeDeprecated: 默认不同步 deprecated skill，显式指定才同步。
```

禁止行为：

```text
1. 不自动删除 $CODEX_HOME/skills 下的未知 skill。
2. 不联网下载第三方 skill。
3. 不执行 skill 目录中的任意脚本。
4. 不默认同步 archived/deprecated skill。
```

## 10. 分阶段执行计划

### Phase 2A：Inventory 与 stale audit

允许修改：

```text
docs/phase2_compact_handoff_skill_hygiene_plan.md
```

允许读取：

```text
.codex-skills/**
tools/sync_codex_skills.ps1
AGENT_GUIDE_FOR_AI.md
project_state/*.json
project_state/*.md
```

输出：

```text
1. 当前 skill inventory。
2. stale/dynamic fact/冲突点列表。
3. 改造建议。
```

不允许：

```text
修改逆向策略
运行 harness
删除 skill
```

### Phase 2B：Skill refactor 最小版

允许修改：

```text
.codex-skills/reverse-agent-iteration/SKILL.md
.codex-skills/samplereverse-frontier/SKILL.md 或迁移到 samplereverse-profile
AGENT_GUIDE_FOR_AI.md
```

目标：

```text
1. reverse-agent-iteration 改成 project_state-first。
2. samplereverse-frontier 去动态事实化。
3. 不再默认读取 PROJECT_PROGRESS_LOG.txt。
4. 不再默认扫描 solve_reports。
```

### Phase 2C：Skill schema / registry

新增：

```text
.codex-skills/schema.md
.codex-skills/registry.json
```

目标：

```text
1. 定义 active/deprecated/archived。
2. 定义 dynamic_facts_allowed。
3. 定义 source_of_truth。
4. 定义 forbidden_defaults。
```

### Phase 2D：Skill audit 工具

新增：

```text
tools/audit_codex_skills.py
```

测试：

```bash
python tools/audit_codex_skills.py
python -m py_compile tools/audit_codex_skills.py
```

当前实现约束（2026-05-24）：

```text
1. audit 工具只使用 Python 标准库。
2. registry 只登记当前实际存在的 repo skill，不登记未来规划 skill。
3. active skill frontmatter 已补齐 version/status/scope/owner/last_reviewed。
4. audit 工具输出 JSON，并以非零 exit code 表示 hard error。
5. audit 工具优先避免误杀禁止句式；复杂自然语言若无法可靠判断，应 warning 而不是 hard error。
6. sync_codex_skills.ps1 仍留到 Phase 2F，不在 Phase 2D 中扩大参数面。
```

### Phase 2E：decision_packet compact profile

允许修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/schema.md
```

目标：

```text
1. decision_meta 支持 skill_profiles。
2. lint-decision 能检查 skill profile。
3. 不破坏旧 decision/report 解析。
```

### Phase 2F：sync hygiene

允许修改：

```text
tools/sync_codex_skills.ps1
```

目标：

```text
1. 支持 -List / -Check / -DryRun / -IncludeDeprecated。
2. 默认只同步 active skill。
3. 不删除本地未知 skill。
```

## 11. 工程量评估

```text
最小可用版：2 轮 Codex
稳妥完整版：4 到 5 轮 Codex
建议每轮 diff 控制在 300 到 500 行以内
```

推荐顺序：

```text
Round 1: Phase 2A + Phase 2B
Round 2: Phase 2C + Phase 2D
Round 3: Phase 2E
Round 4: Phase 2F + 文档收口
```

## 12. 测试要求

最小测试：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py
python tools/audit_codex_skills.py
python -m py_compile tools/audit_codex_skills.py
```

如果修改 sync 脚本，在 Windows PowerShell 中测试：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -List
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -Check
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -DryRun
```

不需要运行：

```text
samplereverse runtime harness
Base64/RC4 probe
old sample_solver
完整 solve_reports scan
```

## 13. Stop Conditions

遇到以下情况停止并报告：

```text
1. 需要修改 compare_aware_search 或 olly_scripts 才能完成 skill 改造。
2. 需要运行 runtime probe 才能判断 skill 是否有效。
3. 需要读取完整 solve_reports 才能完成 inventory。
4. skill 中的动态事实无法安全迁移到 project_state。
5. sync 脚本必须删除本地 skill 才能通过测试。
6. lint-decision 改造会破坏旧 decision_meta 兼容性。
7. diff 超过 500 行且不是纯文档/schema/audit 工具。
```

## 14. 验收标准

### ACCEPTED

```text
1. active skill 不再默认读 PROJECT_PROGRESS_LOG.txt。
2. active skill 不再默认扫完整 solve_reports。
3. sample skill 不再写死当前 candidate/run/artifact。
4. skill registry/schema 存在或已有明确后续计划。
5. skill audit 可运行并能发现 stale skill 风险。
6. decision_packet 可通过 skill_profiles 压缩固定协议。
7. tests 通过。
```

### ACCEPTED_WITH_LIMITATIONS

```text
1. 完成 inventory 和部分 skill 改写，但 registry/lint 未完全实现。
2. 仍保留旧 skill，但已标注 deprecated。
3. sync 脚本未增强，但不会默认同步 deprecated skill。
```

### REWORK_REQUIRED

```text
1. 直接删除 skill 且无 inventory。
2. active skill 仍要求默认读 PROJECT_PROGRESS_LOG.txt。
3. active skill 仍要求默认扫完整 solve_reports。
4. sample skill 继续写死 stale run/candidate。
5. 修改了逆向策略或运行了禁止 probe。
```

### BLOCKED

```text
1. 本地 Codex skill 目录状态不可见且仓库 source 不完整。
2. registry 与实际 .codex-skills 目录严重不一致。
3. 当前 project_state 缺失，无法确认工程支线边界。
```

## 15. 给下一轮 Codex 的推荐执行范围

下一轮只做最小可审计改造：

```text
1. 审计 .codex-skills 下现有 skill。
2. 重写 reverse-agent-iteration 为 project_state-first。
3. 将 samplereverse-frontier 去动态事实化，或迁移为 samplereverse-profile。
4. 新增 skill inventory 结果到 docs 或 codex_execution_report。
5. 不改 reverse_agent/strategies。
6. 不运行 samplereverse harness。
7. 不删除不确定 skill。
```

建议 decision 使用：

```text
decision_id = decision_20260524_phase2_skill_centered_handoff_refactor
round_id = round_20260524_phase2_skill_centered_handoff_refactor
mainline = engineering_branch
```
