```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260524_phase2_skill_handoff_closeout",
  "round_id": "round_20260524_phase2_skill_handoff_closeout",
  "based_on_state_build_id": "state_20260524_042629_10b992a9fad9",
  "based_on_state_digest": "10b992a9fad9e13c9c445709a1f2fb6cee05ed8450b451e0b3d2c80226af04fd",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

本轮属于**工程架构改造支线收口**，不是 `samplereverse` 逆向解题主线。

当前 `task_packet.task` / `derived_task` 仍来自样本 artifact，内容是 `Improve compare lhs last-writer instrumentation`；本轮不要把它当作 Codex 当前任务。`task_packet.execution_scope = decision_packet_controls_current_round`，因此本轮执行权威以本 `project_state/decision_packet.md` 为准。

Phase 2A-F 已基本完成：

```text
Phase 2A/2B: skill inventory + reverse-agent-iteration project_state-first + samplereverse-frontier 去动态事实化。
Phase 2C/2D: .codex-skills/schema.md、registry.json、audit_codex_skills.py、tests/test_codex_skills.py。
Phase 2E: decision_meta.skill_profiles 接入 lint-decision。
Phase 2F: sync_codex_skills.ps1 支持 -List/-Check/-DryRun/-IncludeDeprecated，默认 active-only，不删除 unknown local skill。
```

本轮只做 Phase 2 closeout：更新完成状态、运行现有门禁、生成收口报告，并明确后续是否回到逆向解题主线。不要继续扩张 skill 系统，不要引入新的 agent runtime。

## 1. Goal

本轮目标：

```text
1. 更新 docs/phase2_compact_handoff_skill_hygiene_plan.md，标记 Phase 2A-F 的完成状态、实际落地文件、剩余限制和后续建议。
2. 如更清晰，可新增 docs/phase2_skill_handoff_closeout_report.md，作为 Phase 2 工程支线收口报告。
3. 收口报告必须说明：
   - skill 层：长期流程规范；
   - project_state 层：动态事实来源；
   - decision_packet 层：本轮差异任务；
   - lint/sync 层：机器校验与受控发布。
4. 收口报告必须列出当前已完成的机制：
   - active skill 不默认读 PROJECT_PROGRESS_LOG；
   - active skill 不默认扫完整 solve_reports；
   - sample profile 不写死 candidate/run/artifact；
   - registry/schema/audit 已落地；
   - lint-decision 校验 skill_profiles；
   - sync 脚本 registry-aware 且 active-only。
5. 收口报告必须列出已知限制：
   - round_manifest.source_git_commit 通常仍是执行前 commit；
   - 工程支线 round_manifest.source_harness_run 仍继承样本 run，语义有噪声；
   - archived skill 仍保守跳过，没有 IncludeArchived；
   - mainline policy 仍以 warning 为主，不应在本轮收紧。
6. 运行一次现有 status/lint/audit/sync/test 门禁，证明 Phase 2 闭环处于可用状态。
7. 写入本轮 CODEX_EXECUTION_REPORT，建议下一步回到逆向解题主线，除非用户明确继续工程支线。
```

本轮不是求解 flag，不修 compare-aware search，不生成新的 reverse runtime artifact。

## 2. Current Evidence

当前任务主线判断：**工程架构改造支线收口**。

当前状态包显示：

```text
state_build_id = state_20260524_042629_10b992a9fad9
based_on_state_digest = 10b992a9fad9e13c9c445709a1f2fb6cee05ed8450b451e0b3d2c80226af04fd
execution_scope = decision_packet_controls_current_round
active_strategy = CompareAwareSearchStrategy
profile = samplereverse
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
```

这些样本字段只是 `project_state` 的动态事实，不构成本轮逆向执行任务。

当前 `artifact_index.latest_artifacts_v2` 仍混有 `current`、`stale`、`missing` artifact；这说明 Phase 2 closeout 不应重写样本事实，也不应把 stale artifact 写回 skill。动态事实继续归属 `project_state/current_state.json` 和 `project_state/artifact_index.json`。

上一轮 Codex 报告显示：

```text
report_id = report_20260524_phase2_sync_codex_skills_hygiene
based_on_decision_id = decision_20260524_phase2_sync_codex_skills_hygiene
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

上一轮测试记录显示：

```text
python tools/audit_codex_skills.py = passed, skills_checked=2
python -m pytest -q tests/test_codex_skills.py = 11 passed
python -m pytest -q tests/test_project_state.py = 135 passed
powershell sync -List/-Check/-DryRun/actual sync = passed
python -m reverse_agent.project_state lint-decision --state-dir project_state = passed
python -m reverse_agent.project_state lint-report --state-dir project_state = passed
archive-round = passed
```

当前 `.codex-skills/registry.json` 已登记：

```text
reverse-agent-iteration: active, version 2, scope generic_workflow
samplereverse-frontier: active, version 2, scope sample_profile
```

当前 `tools/sync_codex_skills.ps1` 已支持：

```text
-List
-Check
-DryRun
-IncludeDeprecated
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
不要把旧 candidate / 旧 run / 旧 artifact path 写入 active skill。
不要继续扩张 skill 系统。
不要新增远程 skill 下载机制。
不要新增 IncludeArchived，除非只是文档说明为未来工作；本轮不实现。
不要把 warning policy 收紧为 hard fail。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph runtime。
不要引入 PostgreSQL / Redis / Kubernetes。
不要引入 PyYAML 或其它外部依赖。
不要破坏旧参数 -SourceRoot / -DestinationRoot / -SkillName。
不要破坏旧 decision_meta / codex_report_summary JSON 字段兼容性。
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
.codex-skills/registry.json
.codex-skills/schema.md
.codex-skills/reverse-agent-iteration/SKILL.md
.codex-skills/samplereverse-frontier/SKILL.md
tools/audit_codex_skills.py
tools/sync_codex_skills.ps1
tests/test_codex_skills.py
tests/test_project_state.py
docs/phase2_compact_handoff_skill_hygiene_plan.md
```

允许新增或修改：

```text
docs/phase2_compact_handoff_skill_hygiene_plan.md
docs/phase2_skill_handoff_closeout_report.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/rounds/round_20260524_phase2_skill_handoff_closeout/round_manifest.json
```

不要默认检查或修改：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
```

如果必须读取历史 round，只能读取与 Phase 2 skill/handoff 工程支线直接相关的 bounded `round_manifest.json` 或 report，并在报告中说明原因。

## 5. Required Audit

Codex 修改前必须完成并在报告中记录以下审计：

```text
1. 读取本 decision_meta，确认本轮 decision_id = decision_20260524_phase2_skill_handoff_closeout，status=APPROVED，mainline=engineering_branch，skill_profiles 包含 reverse-agent-iteration@v2。
2. 读取 task_packet，确认 task/derived_task 是样本派生任务，但 execution_scope 表明当前执行权威来自 decision_packet.md。
3. 读取上一轮 codex_execution_report.md 与 pytest_result.txt，确认 Phase 2F 已完成且测试通过。
4. 读取 .codex-skills/registry.json，确认 registry 只登记真实存在的 active skill。
5. 读取 .codex-skills/schema.md，确认 decision skill profiles、audit requirements、sync requirements 已写入。
6. 读取 tools/audit_codex_skills.py 与 tools/sync_codex_skills.ps1，确认不需要继续扩展。
7. 读取 docs/phase2_compact_handoff_skill_hygiene_plan.md，判断应更新原计划还是新增 closeout report。
8. 明确说明本轮不需要 runtime harness、不需要完整 solve_reports、不需要 PROJECT_PROGRESS_LOG。
```

## 6. Implementation Scope

### Phase A：Closeout 文档

必须完成至少一种：

```text
1. 更新 docs/phase2_compact_handoff_skill_hygiene_plan.md 的完成状态；或
2. 新增 docs/phase2_skill_handoff_closeout_report.md。
```

建议两者都做，但保持 diff 小。

Closeout 文档至少包含：

```text
1. Phase 2A-F 完成表。
2. 每个阶段的核心文件和测试命令。
3. 当前 skill 体系的最终边界。
4. 当前已知限制。
5. 下一步建议：默认回到逆向解题主线，除非用户明确继续工程支线。
```

### Phase B：状态门禁

运行现有门禁，不实现新功能：

```bash
python tools/audit_codex_skills.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如环境支持 PowerShell，运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -List
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -Check
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -DryRun -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
```

### Phase C：测试

运行：

```bash
python -m pytest -q tests/test_codex_skills.py
python -m pytest -q tests/test_project_state.py
```

不需要新增大测试。只有在 closeout 文档需要简单验证时，才允许极小测试更新。

### Phase D：report / archive

本轮完成后写入：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

建议运行：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260524_phase2_skill_handoff_closeout
```

如果 archive manifest 的 `source_git_commit` 仍只能记录执行前 commit，应在 report 中说明 limitation，不要为此重写 archive-round。

## 7. Tests

必须运行：

```bash
python tools/audit_codex_skills.py
python -m pytest -q tests/test_codex_skills.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

建议运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -List
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -Check
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -DryRun -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
```

不需要运行：

```bash
samplereverse runtime harness
Base64/RC4 breakpoint probe
old sample_solver
完整 solve_reports scan
```

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. Phase 2F report 与 current decision/report 状态不匹配。
2. audit_codex_skills.py 当前失败，且不是本轮文档 closeout 可解释的问题。
3. sync_codex_skills.ps1 当前 -List/-Check/-DryRun 不可用，需要大规模修复才可 closeout。
4. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG 才能完成 closeout。
5. 需要运行 samplereverse runtime harness 才能完成 closeout。
6. 需要修改 compare_aware_search 或 olly_scripts 才能完成 closeout。
7. 需要继续扩张 skill 系统或新增 runtime 平台。
8. 本轮 diff 超过 400 行，且主要不是文档/report/pytest_result。
9. 测试命令无法运行且没有合理环境原因。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_phase2_skill_handoff_closeout",
  "round_id": "round_20260524_phase2_skill_handoff_closeout",
  "based_on_decision_id": "decision_20260524_phase2_skill_handoff_closeout",
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
1. Phase 2A-F 完成状态。
2. closeout 文档路径。
3. skill/audit/lint/sync 当前门禁结果。
4. 是否仍存在 round_manifest source_git_commit/source_harness_run 限制。
5. 是否建议回到逆向解题主线。
6. 真实测试命令和结果。
7. 是否运行 archive-round；如果未运行，说明原因。
8. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- Phase 2 closeout 文档存在或原计划已更新完成状态。
- 文档明确 Phase 2A-F 完成、当前机制、已知限制、下一步建议。
- audit/lint/status/test 门禁通过。
- 未修改逆向策略，未运行 runtime probe。
- report/pytest_result/round_manifest 可审计。

ACCEPTED_WITH_LIMITATIONS：
- closeout 文档完成，但 PowerShell sync 检查因环境原因跳过且原因明确。
- round_manifest 仍记录执行前 commit 或继承 sample source_harness_run，但 report 已说明。

REWORK_REQUIRED：
- closeout 文档未完成。
- Phase 2 完成状态与实际文件不一致。
- 修改逆向策略或运行禁止 probe。
- 没有真实运行测试或测试记录不可信。
- codex_report_summary.based_on_decision_id 不匹配。

BLOCKED：
- 当前 project_state 状态不可信。
- audit/lint 基础工具失败且无法在 closeout 范围内修复。
- 无法运行 Python 或 pytest 基础测试。
```
