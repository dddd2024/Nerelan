```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260523_engineering_pytest_result_provenance",
  "round_id": "round_20260523_engineering_pytest_result_provenance",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮属于工程架构改造支线，不推进 `samplereverse` 逆向解题主线。

核心目标：修复 `project_state/pytest_result.txt` 的当前轮可信记录问题。上一轮工程审计结论是 `ACCEPTED_WITH_LIMITATIONS`：`archive-round minimal mode` 与 `sidecar_health` 第一阶段已经可接受，但 `pytest_result.txt` 混入上一轮逆向 runtime sidecar 记录，导致 GPT 后续审计无法稳定判断哪些测试属于当前 decision。

本轮只做小步工程 hygiene：让 `pytest_result.txt` 具备机器可读 header、当前轮覆盖写入语义、与 `codex_report_summary.based_on_decision_id` 的一致性检查。不要继续扩展 `sidecar_health`，不要推进逆向 runtime。

## 1. Goal

本轮目标：

```text
1. 定义 pytest_result.txt 的最小可信格式。
2. 让本轮测试记录默认覆盖当前轮内容，而不是追加旧轮历史。
3. 在 pytest_result.txt 顶部写入机器可读 header，至少包含 schema_version、decision_id、report_id、round_id、generated_at、status、tests_ran。
4. 增加 project_state 侧的解析 / 校验 helper，用于确认 pytest_result.txt 是否对应当前 codex_report_summary。
5. 将 status / lint-report 或等价审计路径接入该校验；如果 pytest_result stale、missing、decision mismatch，应明确报告。
6. 更新测试覆盖当前轮通过、旧轮 stale/mismatch、legacy 无 header 不应被误判为当前可信证据。
7. 保持旧文本测试记录可读，不破坏人工阅读。
```

可信测试证据必须能回答：

```text
- 这是哪个 decision_id 的测试？
- 对应哪个 report_id？
- 对应哪个 round_id？
- 实际运行了哪些命令？
- 是否和当前 codex_report_summary.based_on_decision_id 一致？
```

## 2. Current Evidence

当前任务主线判断：工程架构改造支线。

`task_packet.json` 仍来自 `samplereverse` 样本状态，`task_packet.task` / `derived_task` 是逆向主线派生建议，不是本轮工程任务。本轮 Codex 实际执行权威以 `project_state/decision_packet.md` 为准。

上一轮 `project_state/codex_execution_report.md` 的 `codex_report_summary` 显示：

```text
report_id = report_20260523_engineering_artifact_hygiene_sidecar_health_schema
based_on_decision_id = decision_20260523_engineering_artifact_hygiene_sidecar_health_schema
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

上一轮核心工程目标已基本完成：

```text
1. archive-round 默认 minimal archive。
2. --include-state-snapshot / --include-diff 显式化。
3. .gitignore 阻止新的 round 大生成物进入 Git。
4. 新增 reverse_agent/sidecar_health.py。
5. compare_lhs_last_writer 路径附加 sidecar_health 视图并保留旧 flat fields。
```

但 `project_state/pytest_result.txt` 当前混合了两段不同 decision 的记录：

```text
A. decision_20260523_samplereverse_sidecar_hooks_installed_observation_blocker
   包含 bounded runtime sidecar、solve_reports artifact path、classification=hook_not_hit 等逆向 runtime 记录。

B. decision_20260523_engineering_artifact_hygiene_sidecar_health_schema
   包含本轮工程测试：
   - py_compile project_state.py / sidecar_health.py / compare_aware_search.py
   - tests/test_project_state.py
   - tests/test_compare_aware_search_strategy.py
   - tests/test_sidecar_health.py
```

这个混合状态不阻断上一轮工程代码验收，但会破坏后续审计闭环：GPT 读取 `pytest_result.txt` 时无法机器判断当前测试证据是否对应当前 `codex_report_summary.based_on_decision_id`。

artifact freshness 说明：

```text
本轮是工程 hygiene，不依赖 solve_reports 逆向 artifact。
artifact_index.latest_artifacts_v2 中的逆向 artifact freshness 只作为背景，不应作为本轮执行依据。
不要因 stale/missing 逆向 artifact 去重跑 runtime probe。
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
不要继续扩展 sidecar_health schema，除非测试记录校验必须引用其结果。
不要大规模重构 compare_aware_search.py。
不要改动 olly_scripts。
不要删除 active project_state/*.json。
不要把 task_packet.task 当成本轮执行目标。
不要自动执行 git rm --cached 历史 round 文件；这不是本轮目标。
不要引入数据库、调度平台、外部服务或重型依赖。
不要让本轮 diff 超过 600 行；如果超过，停止并报告原因。
```

还要避免重复 negative_results 中已禁止方向：

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
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/decision_packet.md
reverse_agent/project_state.py
tests/test_project_state.py
```

必要时检查：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/rounds/<latest>/round_manifest.json
```

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
reverse_agent/olly_scripts/*
reverse_agent/strategies/compare_aware_search.py，除非测试记录校验确实需要引用已有 report 数据结构
```

## 5. Required Audit

Codex 修改前必须先完成并在报告中记录以下审计：

```text
1. 读取当前 project_state/pytest_result.txt，确认它是否包含多个 decision 的测试记录。
2. 读取当前 project_state/codex_execution_report.md，提取 codex_report_summary：report_id、round_id、based_on_decision_id、status、tests_ran。
3. 读取当前 project_state/decision_packet.md，提取 decision_meta.decision_id。
4. 判断当前 pytest_result.txt 是否能机器对应当前 codex_report_summary.based_on_decision_id。
5. 找出 project_state.py 中 status / lint-report / archive-round 读取 pytest_result.txt 的代码路径。
6. 判断 pytest_result.txt 当前是覆盖写入还是追加写入；如果没有固定写入函数，也要记录 Codex 当前如何生成该文件。
7. 确认本轮不需要读取 solve_reports。
8. 确认本轮不会运行任何逆向 runtime probe。
```

## 6. Implementation Scope

### Phase A：定义 pytest_result header

在 `reverse_agent/project_state.py` 中增加轻量 helper，名称可由 Codex 按现有风格决定，但语义必须清楚：

```text
parse_pytest_result_header(text: str) -> dict
validate_pytest_result_for_report(pytest_text: str, report_summary: dict) -> dict
```

推荐 header 格式：文件顶部使用 fenced JSON block，名称为 `pytest_result_summary`，字段至少包括：

```text
schema_version: 1
decision_id: decision_...
report_id: report_...
round_id: round_...
generated_at: ISO-8601 UTC timestamp
status: PASSED | FAILED | PARTIAL | UNKNOWN
tests_ran: list[str]
```

要求：

```text
1. header 必须在文件顶部。
2. header 后可以继续保留普通文本命令输出，方便人工阅读。
3. parser 必须兼容 legacy 无 header 文件：返回 status=legacy_without_header 或 unknown，而不是抛异常。
4. tests_ran 必须是 list[str]。
5. decision_id 必须能和 codex_report_summary.based_on_decision_id 比对。
6. report_id / round_id 尽量比对；缺失时降级为 warning。
```

### Phase B：覆盖写入语义

Codex 需要找到当前项目中生成或维护 `project_state/pytest_result.txt` 的路径。

若已有函数负责写入：

```text
1. 改成覆盖写入当前轮结果。
2. 写入顶部 pytest_result_summary。
3. 不再追加旧轮内容。
```

若没有统一写入函数：

```text
1. 增加一个小 helper，例如 write_pytest_result(state_dir, summary, body)。
2. 在报告中说明当前仍需 Codex 手动调用/写入，但格式已由 helper 和测试固定。
3. 不要为了这个 helper 重构整个 Codex 工作流。
```

### Phase C：status / lint-report 接入

将校验接入 `python -m reverse_agent.project_state status --state-dir project_state` 或 `lint-report` 中至少一个路径。

最低要求：

```text
status 输出中应能显示：
- pytest_result_status
- pytest_result_decision_id
- pytest_result_report_id
- pytest_result_round_id
- pytest_result_matches_report: true/false/unknown
```

如果已有 `lint-report`，优先接入 `lint-report`：

```text
1. 当前 report_summary.status=SUCCESS 时，pytest_result 缺失 header 或 decision mismatch，应给 warning 或 fail。
2. 对 legacy 文件可以先 warning，不必一刀切 fail，避免破坏旧轮兼容。
3. 对当前 active report，如果 report_summary.tests_ran 非空但 pytest_result 缺失或 mismatch，应至少 warning；若测试里已有严格 lint-report，建议 fail。
```

### Phase D：更新当前 pytest_result.txt

更新 `project_state/pytest_result.txt`，只保留当前轮工程测试或为下一轮执行预留格式。

Codex 执行完成后，`pytest_result.txt` 应该只包含本轮 decision 的测试记录，顶部必须对应：

```text
decision_id = decision_20260523_engineering_pytest_result_provenance
report_id = report_20260523_engineering_pytest_result_provenance
round_id = round_20260523_engineering_pytest_result_provenance
```

不要把上一轮 `decision_20260523_samplereverse_sidecar_hooks_installed_observation_blocker` 的 runtime 记录继续留在当前 active `pytest_result.txt`。

### Phase E：测试

更新或新增 `tests/test_project_state.py` 用例，覆盖：

```text
1. parse_pytest_result_header 能解析 pytest_result_summary。
2. legacy 无 header pytest_result 返回 legacy/unknown，不崩溃。
3. validate_pytest_result_for_report 在 decision_id 匹配时通过。
4. validate_pytest_result_for_report 在 decision_id 不匹配时返回 mismatch。
5. status 或 lint-report 能暴露 pytest_result mismatch。
6. 当前写入 helper 使用覆盖语义，不追加旧文本。
```

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state status --state-dir project_state
```

如果实现或修改了 `lint-report`，额外运行：

```bash
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果测试变动影响到 archive-round 相关逻辑，额外运行：

```bash
python -m pytest -q tests/test_project_state.py -k "archive or pytest_result or report"
```

不需要运行：

```bash
tests/test_compare_aware_search_strategy.py
tests/test_sidecar_health.py
任何 samplereverse runtime probe
```

除非 Codex 修改了相关文件；若修改了，就必须说明为什么越界。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. 找不到任何稳定的 report_summary 解析逻辑，且需要大规模重写 project_state.py。
2. 当前 codex_execution_report.md 缺失 codex_report_summary。
3. 当前 decision_packet.md 缺失 decision_meta。
4. pytest_result.txt 由外部 Codex 平台自动生成，仓库内无法控制写入语义；这种情况下只实现 parser/lint，报告平台限制。
5. lint-report 接入会导致大量旧测试失败，超过兼容小步范围。
6. 需要读取完整 solve_reports 才能继续。
7. 需要运行逆向 runtime probe 才能构造测试。
8. 本轮 diff 超过 600 行，且主要不是 tests/test_project_state.py。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含 `codex_report_summary`，字段要求：

```text
report_id = report_20260523_engineering_pytest_result_provenance
round_id = round_20260523_engineering_pytest_result_provenance
based_on_decision_id = decision_20260523_engineering_pytest_result_provenance
status = SUCCESS / PARTIAL / FAILED / BLOCKED
tests_ran = 真实运行命令列表
generated_artifacts = 本轮更新的 project_state 文件列表
```

报告正文必须明确记录：

```text
1. 当前 pytest_result.txt 是否曾混入多个 decision。
2. 是否实现 pytest_result_summary header。
3. 是否实现覆盖写入 helper，或为什么无法控制写入路径。
4. status / lint-report 是否能识别 stale / mismatch。
5. 当前 active pytest_result.txt 是否只对应本轮 decision。
6. 是否没有运行任何逆向 runtime probe。
7. 真实测试命令和结果。
8. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- pytest_result.txt 顶部存在 pytest_result_summary。
- pytest_result_summary.decision_id 匹配 codex_report_summary.based_on_decision_id。
- 当前 active pytest_result.txt 不再混入上一轮逆向 runtime 记录。
- status 或 lint-report 能暴露 pytest_result 是否 stale/mismatch。
- legacy 无 header 文件兼容，不崩溃。
- tests/test_project_state.py 相关测试通过。
- 未运行任何逆向 runtime probe。

ACCEPTED_WITH_LIMITATIONS：
- header 和 parser 完成，但覆盖写入只能通过 helper 提供，Codex 平台仍需手动使用。
- lint-report 只 warning 不 fail，但 status 能清楚暴露 mismatch。

REWORK_REQUIRED：
- pytest_result.txt 继续混合多个 decision。
- report_summary.status=SUCCESS 但 pytest_result 与 based_on_decision_id 不匹配仍被当成可信。
- 删除 active project_state 文件。
- 运行了逆向 runtime probe。
- 缺少测试或测试记录无法对应当前 decision。

BLOCKED：
- 当前 report/decision meta 缺失，无法建立对应关系。
- 仓库内无可控入口实现写入语义，且无法至少提供 parser/lint。
```
