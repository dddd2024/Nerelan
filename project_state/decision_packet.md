```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260524_phase2_skill_profiles_lint_decision",
  "round_id": "round_20260524_phase2_skill_profiles_lint_decision",
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

上一轮 `decision_20260524_phase2_skill_registry_audit` 已完成 Phase 2C + Phase 2D：`.codex-skills/schema.md`、`.codex-skills/registry.json`、`tools/audit_codex_skills.py`、`tests/test_codex_skills.py` 已落地；`codex_execution_report.md` 与 `pytest_result.txt` 显示测试通过；本轮在此基础上做 Phase 2E：把 `decision_meta.skill_profiles` 接入 `lint-decision`。

本轮不要修改 `tools/sync_codex_skills.ps1`，sync 脚本增强留到 Phase 2F。

## 1. Goal

本轮目标：

```text
1. 增强 project_state 的 decision lint，使 `decision_meta.skill_profiles` 能被机器校验。
2. lint-decision 应读取 `.codex-skills/registry.json`，检查 skill profile 是否存在、是否 active、version 是否匹配。
3. 规范 skill profile 字符串格式，最小支持：
   - `skill-name@v2`
   - 可选兼容 `skill-name@v2-draft`，但应 warning 或 transitional warning，不应长期作为正式格式。
4. 对工程支线 decision，若缺少 active generic workflow skill，例如 `reverse-agent-iteration@v2`，至少给 warning；如果当前 lint-decision 已有 hard-fail 机制，也可以在新测试中明确策略。
5. 对 reverse_solving decision，若引用 sample profile skill，应检查该 skill 在 registry 中存在且 active。
6. 保持 additive/backward-compatible：旧 decision 没有 `skill_profiles` 时，默认 warning，不要直接导致历史 decision hard fail。
7. 更新 tests，覆盖 valid/missing/unknown/inactive/version-mismatch/draft profile 等场景。
8. 更新 project_state/schema 或 docs/phase2_compact_handoff_skill_hygiene_plan.md，说明 `decision_meta.skill_profiles` 的正式语义。
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

上一轮 Codex 报告显示：

```text
report_id = report_20260524_phase2_skill_registry_audit
based_on_decision_id = decision_20260524_phase2_skill_registry_audit
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

上一轮测试记录显示：

```text
python -m py_compile tools/audit_codex_skills.py = passed
python tools/audit_codex_skills.py = passed, skills_checked=2
python -m pytest -q tests/test_codex_skills.py = 6 passed
python -m pytest -q tests/test_project_state.py = 126 passed
python -m reverse_agent.project_state lint-report --state-dir project_state = passed, archive_status=archived
```

当前 `.codex-skills/registry.json` 已登记：

```text
reverse-agent-iteration: active, version 2, scope generic_workflow
samplereverse-frontier: active, version 2, scope sample_profile
```

当前 active skill frontmatter 已补齐 `version/status/scope/owner/last_reviewed/facts_policy/forbidden_defaults`。本轮要让 decision lint 消费这些 registry/frontmatter 结果，而不是只停留在文档和 audit 工具层。

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
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph runtime。
不要引入 PostgreSQL / Redis / Kubernetes。
不要引入联网下载第三方 skill 的流程。
不要修改 tools/sync_codex_skills.ps1；除非发现当前测试无法运行且需要最小修复，否则 sync 增强留到 Phase 2F。
不要引入 PyYAML 或其它外部依赖；解析 registry/frontmatter 应复用或保持标准库实现。
不要破坏旧 decision_meta / codex_report_summary JSON 字段兼容性。
不要把缺少 skill_profiles 的历史 decision 直接判为 hard fail，除非测试明确只作用于新 schema decision。
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
reverse_agent/project_state.py
tests/test_project_state.py
tests/test_codex_skills.py
```

可能需要检查：

```text
project_state/schema.md
docs/phase2_compact_handoff_skill_hygiene_plan.md
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
1. 读取本 decision_meta，确认本轮 decision_id = decision_20260524_phase2_skill_profiles_lint_decision，status=APPROVED，mainline=engineering_branch。
2. 读取 task_packet，确认 task/derived_task 是样本派生任务，但 execution_scope 表明当前执行权威来自 decision_packet.md。
3. 读取上一轮 codex_execution_report.md 与 pytest_result.txt，确认 Phase 2C/2D 已完成并测试通过。
4. 读取 .codex-skills/registry.json，确认 registry 只登记真实存在的 active skill。
5. 读取 .codex-skills/schema.md，确认 skill profile / frontmatter / registry 语义。
6. 读取 tools/audit_codex_skills.py，判断是否可复用 registry/frontmatter 解析逻辑，避免重复实现。
7. 审计 reverse_agent/project_state.py 当前 lint-decision 的实现位置、返回格式、测试覆盖方式。
8. 明确说明本轮不需要 runtime harness、不需要完整 solve_reports、不需要 PROJECT_PROGRESS_LOG。
```

## 6. Implementation Scope

### Phase A：定义 skill profile 解析

在合适位置实现或复用 helper，建议放在 `reverse_agent/project_state.py` 或轻量内部函数中。

要求支持：

```text
profile string: skill-name@v2
skill_name = skill-name
version = 2
```

过渡兼容：

```text
skill-name@v2-draft
```

建议行为：

```text
1. `@v2` 是正式格式。
2. `@v2-draft` 可解析为 version=2，但产生 warning：draft skill profile should not be used in APPROVED decisions。
3. 无 @vN、version 非数字、skill name 为空，应产生 lint error。
```

### Phase B：读取 registry

lint-decision 应读取：

```text
.codex-skills/registry.json
```

要求：

```text
1. registry 缺失时：对包含 skill_profiles 的新 decision 产生 error；对旧 decision 可 warning。
2. registry JSON 无效：error。
3. skill_profiles 引用未知 skill：error。
4. skill_profiles 引用非 active skill：error。
5. skill_profiles version 与 registry version 不一致：error。
6. registry 中 scope 可用于 mainline policy warning。
```

不要在本轮实现复杂 alias、远程 skill 下载或本地 `$CODEX_HOME/skills` 检查。

### Phase C：mainline policy

最小策略：

```text
1. mainline=engineering_branch 的 APPROVED decision 应至少引用一个 active generic_workflow skill。
2. mainline=reverse_solving 的 APPROVED decision 应至少引用 generic_workflow；如果涉及 sample profile，可引用 sample_profile skill。
3. 缺少 skill_profiles 的旧 decision：warning，不 hard fail。
4. skill_profiles 存在但全部无效：error。
```

如果当前 `lint-decision` 没有 warning/error 分级，应实现最小兼容方式：

```text
- error 继续导致非零或 FAIL；
- warning 出现在输出中但不破坏旧包。
```

### Phase D：测试

扩展 `tests/test_project_state.py`，或新增 focused tests。

测试至少覆盖：

```text
1. 当前 decision 的 `reverse-agent-iteration@v2` 能通过 lint-decision。
2. `reverse-agent-iteration@v999` version mismatch 失败。
3. `unknown-skill@v1` 失败。
4. `skill-name` 无 version 失败。
5. `reverse-agent-iteration@v2-draft` 在 APPROVED decision 中产生 warning 或 transitional diagnostic。
6. 缺少 skill_profiles 的旧 decision 不 hard fail，只 warning。
7. registry 缺失或无效时，包含 skill_profiles 的 decision 失败。
8. inactive/deprecated skill 被引用时失败；可用临时 registry fixture 模拟。
```

如果方便，复用 `tools/audit_codex_skills.py` 的 frontmatter/registry 解析逻辑，但不要把测试耦合到 CLI 输出过重。

### Phase E：docs/schema update

更新以下任一文件：

```text
project_state/schema.md
或 docs/phase2_compact_handoff_skill_hygiene_plan.md
```

记录：

```text
1. decision_meta.skill_profiles 是 additive 字段。
2. 正式格式是 skill-name@vN。
3. draft 格式只允许过渡 warning。
4. lint-decision 会查 .codex-skills/registry.json。
5. 旧 decision 缺少 skill_profiles 只 warning。
```

### Phase F：report / archive

本轮完成后写入：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果可行，运行：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260524_phase2_skill_profiles_lint_decision
```

如果 archive manifest 的 `source_git_commit` 仍只能记录执行前 commit，应在 report 中说明 limitation，不要为此重写 archive-round。

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m py_compile tools/audit_codex_skills.py
python tools/audit_codex_skills.py
python -m pytest -q tests/test_codex_skills.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果新增 dedicated test 文件，额外运行：

```bash
python -m pytest -q tests/test_<new_skill_profile_lint_file>.py
```

不需要运行：

```bash
samplereverse runtime harness
Base64/RC4 breakpoint probe
old sample_solver
full pytest unrelated to project_state / codex skill audit
完整 solve_reports scan
PowerShell sync 脚本测试
```

除非 Codex 修改了 sync 脚本；本轮默认不应修改。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. .codex-skills/registry.json 缺失，且无法从 Git 恢复。
2. tools/audit_codex_skills.py 无法导入或现有 audit 测试失败，且原因与本轮无关。
3. 当前 lint-decision 没有可维护扩展点，必须大规模重写 project_state.py 才能接入 registry。
4. 需要引入外部 YAML/JSON schema 依赖才能实现。
5. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG 才能判断。
6. 需要运行 samplereverse runtime harness 才能判断。
7. 需要修改 compare_aware_search 或 olly_scripts 才能完成本轮。
8. 需要修改 sync_codex_skills.ps1 才能完成 lint-decision。
9. 无法避免把旧 decision 缺少 skill_profiles 误判为 hard fail。
10. 本轮 diff 超过 700 行，且主要不是 project_state lint / tests / docs。
11. 测试命令无法运行且没有合理环境原因。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_phase2_skill_profiles_lint_decision",
  "round_id": "round_20260524_phase2_skill_profiles_lint_decision",
  "based_on_decision_id": "decision_20260524_phase2_skill_profiles_lint_decision",
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
1. skill profile parser 支持的格式。
2. lint-decision 如何读取 .codex-skills/registry.json。
3. unknown skill / inactive skill / version mismatch 的行为。
4. missing skill_profiles 对旧 decision 的行为。
5. draft profile 的 warning 或 transitional behavior。
6. 是否修改 sync_codex_skills.ps1；预期应为 no。
7. 真实测试命令和结果。
8. 是否运行 archive-round；如果未运行，说明原因。
9. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- lint-decision 能解析 decision_meta.skill_profiles。
- lint-decision 能读取 .codex-skills/registry.json。
- unknown skill、inactive skill、version mismatch、bad format 都能被测试覆盖。
- 旧 decision 缺少 skill_profiles 不 hard fail。
- 当前 decision 使用 reverse-agent-iteration@v2 通过 lint-decision。
- tests 通过。
- 未修改逆向策略，未运行 runtime probe。

ACCEPTED_WITH_LIMITATIONS：
- skill_profiles 检查已接入，但 mainline policy 只 warning。
- draft profile 只 warning，没有 hard fail。
- archive-round 未完成但 report/status/lint 记录清楚。

REWORK_REQUIRED：
- lint-decision 未实际消费 registry。
- registry 缺失时仍静默通过新 decision。
- unknown skill / version mismatch 不报错。
- 旧 decision 缺少 skill_profiles 被 hard fail，破坏历史兼容。
- 引入外部依赖。
- 修改逆向策略或运行禁止 probe。
- codex_report_summary.based_on_decision_id 不匹配。

BLOCKED：
- 当前 project_state.py 无法安全扩展。
- registry/audit 工具状态不可信。
- 无法运行 Python 或 pytest 基础测试。
```
