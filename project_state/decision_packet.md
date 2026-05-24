```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260524_phase2_sync_codex_skills_hygiene",
  "round_id": "round_20260524_phase2_sync_codex_skills_hygiene",
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

本轮属于**工程架构改造支线**，不是 `samplereverse` 逆向解题主线。

当前 `task_packet.task` / `derived_task` 仍来自样本 artifact，内容是 `Improve compare lhs last-writer instrumentation`；本轮不要把它当作 Codex 当前任务。`task_packet.execution_scope = decision_packet_controls_current_round`，因此本轮执行权威以本 `project_state/decision_packet.md` 为准。

上一轮 `decision_20260524_phase2_skill_profiles_lint_decision` 已完成 Phase 2E：`decision_meta.skill_profiles` 已接入 `lint-decision`，当前 decision 使用 `reverse-agent-iteration@v2` 可通过 lint；`codex_execution_report.md` 与 `pytest_result.txt` 显示测试通过。本轮继续执行 Phase 2F：增强 `tools/sync_codex_skills.ps1` 的受控同步能力。

本轮只做 skill sync hygiene。不要推进逆向解题，不要运行 runtime harness，不要改 solver / compare-aware runtime 逻辑。

## 1. Goal

本轮目标：

```text
1. 增强 tools/sync_codex_skills.ps1，使它支持：
   - -List
   - -Check
   - -DryRun
   - -IncludeDeprecated
2. 让 sync 脚本默认读取 .codex-skills/registry.json，而不是只按目录扫描 active skill。
3. 默认只同步 registry 中 status=active 的 skill。
4. deprecated / archived skill 默认不同步；只有显式 -IncludeDeprecated 时才可纳入候选。
5. -Check 应执行或等价复用 tools/audit_codex_skills.py 的审计结果；如果 audit 失败，应以非零退出或明确失败。
6. -DryRun 只打印计划同步项，不写 DestinationRoot。
7. -List 只列出 registry / source 中可见 skill 与 status/scope/version，不写 DestinationRoot。
8. 保持原有 -SkillName、-SourceRoot、-DestinationRoot 行为兼容。
9. 不删除 $CODEX_HOME/skills 或 DestinationRoot 下的未知本地 skill。
10. 补充测试或测试记录，覆盖 list/check/dry-run/active-only/include-deprecated/skill-name filtering。
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

这些样本字段只是 `project_state` 的动态事实，不构成本轮逆向执行任务。

当前 `artifact_index.latest_artifacts_v2` 仍混有 `current`、`stale`、`missing` artifact。此事实说明 active skill 和 sync 脚本都不能绕过 `project_state` / registry，把旧 run、旧 artifact path 或旧 candidate 当成长期同步依据。

上一轮 Codex 报告显示：

```text
report_id = report_20260524_phase2_skill_profiles_lint_decision
based_on_decision_id = decision_20260524_phase2_skill_profiles_lint_decision
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

上一轮测试记录显示：

```text
python -m py_compile reverse_agent/project_state.py = passed
python -m py_compile tools/audit_codex_skills.py = passed
python tools/audit_codex_skills.py = passed, skills_checked=2
python -m pytest -q tests/test_codex_skills.py = 6 passed
python -m pytest -q tests/test_project_state.py = 135 passed
python -m reverse_agent.project_state lint-decision --state-dir project_state = passed
python -m reverse_agent.project_state lint-report --state-dir project_state = passed
```

当前 `.codex-skills/registry.json` 已登记：

```text
reverse-agent-iteration: active, version 2, scope generic_workflow
samplereverse-frontier: active, version 2, scope sample_profile
```

当前 `tools/sync_codex_skills.ps1` 的行为较简单：

```text
1. 读取 .codex-skills 下含 SKILL.md 的目录。
2. 如果传入 -SkillName，则按目录名过滤。
3. 对每个匹配目录复制全部内容到 DestinationRoot/<skill-name>。
4. 不读取 registry。
5. 不区分 active/deprecated/archived。
6. 不支持 -List/-Check/-DryRun/-IncludeDeprecated。
7. 不删除未知本地 skill。
```

本轮要在不破坏旧同步能力的基础上，把 sync 脚本接到 Phase 2C/2D/2E 已建立的 registry / audit / lint 体系。

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
不要删除 skill。
不要删除 $CODEX_HOME/skills 或 DestinationRoot 下的未知本地 skill。
不要让 -Check 或 -List 写入 DestinationRoot。
不要让 -DryRun 写入 DestinationRoot。
不要默认同步 deprecated / archived skill。
不要联网下载第三方 skill。
不要执行 skill 目录中的任意脚本。
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
```

可能需要检查：

```text
AGENT_GUIDE_FOR_AI.md
docs/phase2_compact_handoff_skill_hygiene_plan.md
```

只有当需要更新文档说明新 sync 参数时才修改。

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
1. 读取本 decision_meta，确认本轮 decision_id = decision_20260524_phase2_sync_codex_skills_hygiene，status=APPROVED，mainline=engineering_branch，skill_profiles 包含 reverse-agent-iteration@v2。
2. 运行或读取当前 lint-decision 行为，确认当前 decision 可通过 skill_profiles registry 检查。
3. 读取 task_packet，确认 task/derived_task 是样本派生任务，但 execution_scope 表明当前执行权威来自 decision_packet.md。
4. 读取上一轮 codex_execution_report.md 与 pytest_result.txt，确认 Phase 2E 已完成且测试通过。
5. 读取 .codex-skills/registry.json，确认 registry 只登记真实存在的 skill。
6. 读取 .codex-skills/schema.md，确认 status/scope/version 和 active/deprecated/archived 语义。
7. 读取 tools/audit_codex_skills.py，确认 -Check 可调用它或等价执行它。
8. 读取 tools/sync_codex_skills.ps1，记录当前参数、目录扫描行为和缺少 registry/status/dry-run/list/check 的现状。
9. 明确说明本轮不需要 runtime harness、不需要完整 solve_reports、不需要 PROJECT_PROGRESS_LOG。
```

## 6. Implementation Scope

### Phase A：PowerShell 参数扩展

修改：

```text
tools/sync_codex_skills.ps1
```

新增参数：

```powershell
[switch]$List
[switch]$Check
[switch]$DryRun
[switch]$IncludeDeprecated
```

保持兼容：

```powershell
[string]$SourceRoot
[string]$DestinationRoot
[string[]]$SkillName = @()
```

要求：

```text
1. 旧命令仍可用：
   powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
2. 未传 -List/-Check/-DryRun 时，行为仍是实际同步。
3. DestinationRoot 只在实际同步时创建；-List/-Check/-DryRun 不应创建或写入 DestinationRoot。
```

### Phase B：Registry-aware skill discovery

同步候选应优先来自：

```text
<SourceRoot>/registry.json
```

默认 `SourceRoot` 仍是：

```text
.codex-skills
```

规则：

```text
1. registry 存在时，以 registry.skills 为权威。
2. registry 中 path 必须存在且指向 SKILL.md。
3. 默认只纳入 status=active 的 skill。
4. status=deprecated 或 status=archived 默认跳过。
5. -IncludeDeprecated 时可纳入 deprecated；archived 仍建议默认跳过，除非 Codex 有明确理由支持 archived 同步。
6. -SkillName 过滤应作用在 registry skill name 上。
7. 如果 -SkillName 指定不存在的 skill，应报错或至少非零退出；不要静默 No skills matched。
8. registry 缺失时可以 fallback 到旧目录扫描，但必须输出 warning，并且 -Check 应失败或警告；具体策略要写入报告和测试。
```

建议：registry 缺失时普通同步可以 fallback warning，`-Check` 必须失败。

### Phase C：List / DryRun / Check 行为

`-List`：

```text
1. 打印 skill name、status、scope、version、path。
2. 不写 DestinationRoot。
3. 不复制文件。
4. 可配合 -IncludeDeprecated 显示 deprecated；若不配合，只显示 active 或明确标注 skipped。
```

`-DryRun`：

```text
1. 打印将同步的 skill 与目标路径。
2. 不创建 DestinationRoot。
3. 不复制文件。
4. 应尊重 -SkillName 和 -IncludeDeprecated。
```

`-Check`：

```text
1. 调用 python tools/audit_codex_skills.py，或复用等价检查。
2. 如果 audit 返回非零，sync 脚本也返回非零。
3. 输出 audit 结果。
4. 不写 DestinationRoot。
5. 不复制文件。
```

组合行为建议：

```text
-List 和 -Check 可单独运行。
-DryRun 可与 -SkillName / -IncludeDeprecated 组合。
如果同时传 -List 和 -DryRun，可以先 list 再 dry-run，或明确报错；需测试覆盖。
```

### Phase D：Tests

优先新增或扩展：

```text
tests/test_codex_skills.py
```

可用 Python subprocess 调 PowerShell；如果当前环境无法保证 PowerShell，可使用 pytest skip 条件：

```python
pytest.importorskip 或 shutil.which("powershell") / shutil.which("pwsh")
```

测试至少覆盖：

```text
1. -List 不创建 DestinationRoot，输出 reverse-agent-iteration 与 samplereverse-frontier。
2. -DryRun 不创建 DestinationRoot，输出将同步 reverse-agent-iteration。
3. 默认实际同步只复制 active skill。
4. -SkillName reverse-agent-iteration 只同步该 skill。
5. -Check 调用 audit 并成功。
6. registry 中 deprecated skill 默认不同步；-IncludeDeprecated 时可纳入 deprecated。
7. 指定不存在的 -SkillName 应失败或产生明确错误。
8. 不删除 DestinationRoot 下预先存在的 unknown-local-skill 目录。
```

若 PowerShell 不可用，必须至少在 `pytest_result.txt` 中记录 skip 原因，并手动运行等价命令不可作为 passed。

### Phase E：Docs update

必要时更新：

```text
.codex-skills/schema.md
或 docs/phase2_compact_handoff_skill_hygiene_plan.md
或 AGENT_GUIDE_FOR_AI.md
```

记录：

```text
1. sync 脚本的新参数。
2. 默认只同步 active skill。
3. -Check 使用 audit。
4. -DryRun / -List 不写 DestinationRoot。
5. 不删除未知本地 skill。
```

不要重写整份文档。

### Phase F：report / archive

本轮完成后写入：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果可行，运行：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260524_phase2_sync_codex_skills_hygiene
```

如果 archive manifest 的 `source_git_commit` 仍只能记录执行前 commit，应在 report 中说明 limitation，不要为此重写 archive-round。

## 7. Tests

必须运行：

```bash
python -m py_compile tools/audit_codex_skills.py
python tools/audit_codex_skills.py
python -m pytest -q tests/test_codex_skills.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

必须运行 PowerShell sync 检查；Windows PowerShell 可用时使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -List
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -Check
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -DryRun -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
powershell -ExecutionPolicy Bypass -File .\tools\sync_codex_skills.ps1 -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
```

如果环境只有 PowerShell Core，可用：

```powershell
pwsh -File ./tools/sync_codex_skills.ps1 -List
pwsh -File ./tools/sync_codex_skills.ps1 -Check
pwsh -File ./tools/sync_codex_skills.ps1 -DryRun -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
pwsh -File ./tools/sync_codex_skills.ps1 -SkillName reverse-agent-iteration -DestinationRoot <temp_dir>
```

还应测试 unknown-local-skill 不被删除：

```text
1. 在临时 DestinationRoot 下预建 unknown-local-skill/SKILL.md。
2. 执行实际同步 active skill。
3. 确认 unknown-local-skill 仍存在。
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
1. .codex-skills/registry.json 缺失，且无法从 Git 恢复。
2. tools/audit_codex_skills.py 当前 audit 失败，且不是本轮可解释的小问题。
3. 当前 sync 脚本需要大规模重写成复杂包管理器才能实现本轮目标。
4. 需要删除本地未知 skill 才能通过测试。
5. 需要联网下载或安装第三方 PowerShell / Python 依赖。
6. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG 才能判断。
7. 需要运行 samplereverse runtime harness 才能判断。
8. 需要修改 compare_aware_search 或 olly_scripts 才能完成本轮。
9. 无法在当前环境运行 powershell 或 pwsh，且也无法提供可信 skip / fallback 说明。
10. -DryRun 或 -List 无法避免创建 DestinationRoot。
11. registry-aware 同步会破坏原有 -SkillName/-DestinationRoot 基本用法。
12. 本轮 diff 超过 600 行，且主要不是 sync 脚本 / tests / 小文档更新。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_phase2_sync_codex_skills_hygiene",
  "round_id": "round_20260524_phase2_sync_codex_skills_hygiene",
  "based_on_decision_id": "decision_20260524_phase2_sync_codex_skills_hygiene",
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
1. sync 脚本新增了哪些参数。
2. registry-aware discovery 的行为。
3. active/deprecated/archived 的同步策略。
4. -List/-Check/-DryRun 是否写 DestinationRoot。
5. -SkillName 不存在时的行为。
6. unknown-local-skill 是否被保留。
7. 是否调用或复用 audit_codex_skills.py。
8. 真实测试命令和结果。
9. 是否运行 archive-round；如果未运行，说明原因。
10. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- sync 脚本支持 -List/-Check/-DryRun/-IncludeDeprecated。
- 默认只同步 active skill。
- -Check 能调用或等价执行 audit 并传播失败。
- -DryRun 和 -List 不写 DestinationRoot。
- -SkillName 过滤可用，不存在时不静默成功。
- deprecated 默认不同步，IncludeDeprecated 行为有测试。
- unknown local skill 不被删除。
- tests 通过。
- 未修改逆向策略，未运行 runtime probe。

ACCEPTED_WITH_LIMITATIONS：
- PowerShell 环境导致部分测试 skip，但 skip 原因明确，核心逻辑有单元测试覆盖。
- archived skill 策略只保守跳过，未提供 IncludeArchived；可接受。
- registry 缺失 fallback 只 warning，后续可收紧。

REWORK_REQUIRED：
- -DryRun 或 -List 会写 DestinationRoot。
- 默认同步 deprecated / archived skill。
- 删除未知本地 skill。
- -Check 不实际调用/复用 audit，或 audit 失败仍返回成功。
- 指定不存在 SkillName 静默成功。
- 引入外部依赖。
- 修改逆向策略或运行禁止 probe。
- codex_report_summary.based_on_decision_id 不匹配。

BLOCKED：
- 当前环境无法运行 PowerShell 且无法提供可信替代测试。
- registry/audit 工具状态不可信。
- 无法运行 Python 或 pytest 基础测试。
```
