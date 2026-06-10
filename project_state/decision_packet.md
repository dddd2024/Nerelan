```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260610_rework_run_missing_harness_compare_test_v1",
  "round_id": "round_20260610_rework_run_missing_harness_compare_test_v1",
  "based_on_state_build_id": "state_20260610_105707_1114a74dbc48",
  "based_on_state_digest": "1114a74dbc482a6cdcef792426ec10b895a15da031744a6e295ca39d770800fb",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]
}
```

# DECISION_PACKET

## 1. Goal

补齐上一轮缺失的必跑测试证据。上一轮实现方向暂不扩大，不做新功能，不改 solver，不推进 reverse solving。核心目标是运行完整 decision 要求的 pytest 命令，并更新 `pytest_result.txt`、`codex_execution_report.md` 和 round archive，使测试证据与当前报告一致。

本轮不是新的功能开发轮，也不是一键解题改造轮。当前唯一目标是把 `decision_20260610_rework_run_missing_harness_compare_test_v1` 执行闭环做完整，避免再次出现 report 声称 SUCCESS 但测试命令不满足 decision 要求的问题。

Codex 执行前必须确认当前工作目录确实是本地仓库根目录：

```powershell
cd F:\reverse-agent
pwd
git status --short
git rev-parse --show-toplevel
```

如果 `git rev-parse --show-toplevel` 不是 `F:\reverse-agent`，必须停止并报告 `BLOCKED`，不要在错误目录生成或修改文件。

## 2. Current Evidence

- 上一轮审计结论：`REWORK_REQUIRED`。
- 原因：`decision_packet.md` 要求运行 `tests/test_project_state.py tests/test_harness_artifact_manifest.py tests/test_harness_compare.py`，但报告和 `pytest_result.txt` 只记录了前两个测试文件。
- 当前主线仍为 `engineering_branch`。
- `model_gate.json` 已正确保留 `fallback_evidence_incomplete`，并生成 `repair_diagnostics`。
- 当前 `next_local_action` 为 `repair_harness_case_result_materialization`。
- 不允许把本轮扩张为逆向求解、候选生成、runtime probe、IDA/Ghidra/debugger 调试。
- `task_packet.json` 只是 advisory；当前轮执行权威是本 `project_state/decision_packet.md`。
- `artifact_index.json` 仍包含 stale artifacts；stale/missing artifact 不能作为 current 证据。
- negative_results 仍然禁止盲搜、扩 beam/budget、重复失败 runtime probe、复用 stale hook、提交完整 `solve_reports/`。
- 这是测试证据返工轮，不需要运行 IDA/Ghidra/debugger/solver/harness real sample。
- 当前项目已经具备 project_state build/status/lint/archive 相关入口，不得新建重复状态管理器。
- 当前轮只需要补齐测试证据和状态报告闭环；`doctor` / `solve` 自动化应在本轮 ACCEPTED 后另开新 decision。

## 3. Do Not Do

- 不要运行样本二进制。
- 不要运行 harness real sample。
- 不要生成、验证、排序 candidate。
- 不要运行 solver/search/runtime/debugger/probe/IDA/Ghidra。
- 不要改 `.codex-skills/`。
- 不要改 solver/search/runtime/debugger/probe 代码。
- 不要读取完整 `solve_reports/`。
- 不要读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不要把 fallback evidence 提升为 current/latest。
- 不要修改 historical `solve_reports/` 来制造通过状态。
- 不要只改报告文本而不真实运行缺失测试。
- 不要把本轮扩张为 reverse_solving、tool_integration 或 training_dataset。
- 不要在本轮实现 `project_state doctor`、`solve --dry-run` 或完整 `solve`。
- 不要修改与三文件 pytest 证据补齐无关的源码。

## 4. Files To Inspect

必须读取：

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/model_gate.json`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `tests/test_harness_compare.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

仅在三文件 pytest 失败且失败栈明确指向相关源码时，才允许有界读取：

- `reverse_agent/project_state.py`
- `reverse_agent/harness.py`

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

Codex 必须确认：

1. 当前工作目录确实是 `F:\reverse-agent`。
2. 当前 `decision_packet.md` 是执行权威，`task_packet.json` 只是 advisory。
3. `decision_meta.status == APPROVED`。
4. `decision_meta.mainline == engineering_branch`。
5. `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 和 `samplereverse-frontier@v2` 仍为 active。
6. 上一轮 report/decision 匹配，但测试命令缺少 `tests/test_harness_compare.py`。
7. 当前返工只补测试证据，不做工程功能扩张。
8. `model_gate.json` 的 `fallback_evidence_incomplete`、`repair_diagnostics`、`next_local_action` 不被回退。
9. 没有运行样本、solver、probe、debugger、IDA/Ghidra。
10. 新 `pytest_result.txt` 必须完整记录三文件 pytest 命令输出。
11. 新 `codex_execution_report.md` 必须绑定本返工 decision_id。
12. archive 后 `lint-report` 和 `status` 必须显示 consumed/archived。
13. 若三文件 pytest 失败，必须如实报告失败原因，不得只更新报告绕过失败。
14. 若需要源码修复，必须保持最小范围并说明为什么测试证据返工暴露该问题。
15. 最终 Git diff 必须包含 live `project_state/codex_execution_report.md` 和 live `project_state/pytest_result.txt` 的真实更新，不能只有 round archive。
16. 完成前必须确认文件真实写入 `F:\reverse-agent\project_state\...`，不能只在临时目录或错误工作树中生成。

## 6. Implementation Scope

允许修改：

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260610_rework_run_missing_harness_compare_test_v1/*`

通常不需要修改源码。除非完整三文件 pytest 暴露真实失败，才允许最小修复相关测试或工程代码；若需要源码修复，必须在报告中明确说明原因、文件、影响范围和新增测试结果。

若测试失败且必须修源码，允许的最大源码范围为：

- `reverse_agent/project_state.py`
- `reverse_agent/harness.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`
- `tests/test_harness_compare.py`

禁止修改：

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interfaces
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay
- historical `solve_reports/`
- unrelated source/test files

## 7. Tests

必须运行并记录完整输出：

```bash
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py tests/test_harness_compare.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_run_missing_harness_compare_test_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

还必须记录一次最终文件/差异自检：

```bash
git status --short
git diff -- project_state/codex_execution_report.md project_state/pytest_result.txt project_state/rounds/round_20260610_rework_run_missing_harness_compare_test_v1
```

Acceptance requirements:

- 三文件 pytest 命令真实运行并通过。
- `tests_ran` 必须显式包含 `tests/test_harness_compare.py`。
- `pytest_result.txt` 的 summary 绑定本 decision_id、report_id、round_id。
- `codex_execution_report.md` 顶部包含合法 `codex_report_summary`，并绑定本 decision_id。
- 最终 `lint-report: OK`。
- 最终 status 显示 `decision_report_id_match: True`。
- 最终 status 显示 `decision_consumed_by_report: True`。
- 最终 status 显示 `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`。
- 最终 status 显示 `round_manifest_present: True` 和 `archive_status: archived`。
- `model_gate.json` 仍保留 `fallback_evidence_incomplete` 和 precise `next_local_action`。
- 没有样本、solver、probe、debugger、IDA/Ghidra 执行。
- 没有 `.codex-skills/` 修改。
- 没有把 stale/missing artifact 提升为 current。
- live report/test 文件确实被更新，不能只有 archive 文件变化。

## 8. Stop Conditions

停止并报告 `FAILED` 或 `BLOCKED`，如果：

- 当前目录不是 `F:\reverse-agent`。
- 三文件 pytest 命令失败。
- 需要运行样本二进制才能修复。
- 需要 solver/search/runtime/debugger/probe/IDA/Ghidra。
- 需要修改 `.codex-skills/`。
- 需要修改 historical `solve_reports/`。
- `lint-report` 无法通过。
- final status 无法达到 consumed/archived。
- 返工范围无法保持在测试证据补齐和最小修复内。
- 只能通过修改报告文本而非真实测试来满足验收条件。

## 9. Next Round After Acceptance

本轮 ACCEPTED 后，下一轮再启动 `project_state doctor` 改造，主线仍为 `engineering_branch`。`doctor` 第一版只做状态一致性检查，不做解题、不跑样本、不接入新 solver。目标是把本轮暴露的问题自动检查出来，例如：

- required tests 缺失；
- report/decision mismatch；
- pytest_result/report mismatch；
- archive 未生成；
- stale/missing artifact 被误用；
- decision 未 consumed；
- live report/test 未真实更新。

不要在当前返工轮同时实现 `doctor`。
