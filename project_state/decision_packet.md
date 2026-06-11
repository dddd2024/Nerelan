```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_rework_training_inventory_test_and_report_integrity_v1",
  "round_id": "round_20260611_rework_training_inventory_test_and_report_integrity_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

返工上一轮训练集库存刷新结果，目标只处理三个验收阻塞点：

1. 修复或重写失败测试 `test_real_cpp1_target_provenance_recheck_removes_cpp1_from_queue`，使训练集状态测试不再依赖 stale / unavailable 的 live `artifact_index` 事实。
2. 修复 `pytest_result_summary.status` 与 pytest 正文结果不一致的问题，确保出现 `failed` 时不能写成 `PASSED`，`lint-report` / `doctor` 不能误判。
3. 核对并清理 `files_changed` 与最终 `git status --short` 的不一致；所有实际改动必须列入报告，或明确标注为 pre-existing dirty tree 并说明未纳入本轮提交。

本轮仍是 `training_dataset` 主线，不做逆向解题。

## 2. Current Evidence

- 上一轮 decision 合法，但报告把失败测试写成 `PASSED / SUCCESS / ACCEPTED`。
- pytest 正文显示 `1 failed, 231 passed`，失败点为 `test_real_cpp1_target_provenance_recheck_removes_cpp1_from_queue`。
- 失败原因来自 live `project_state/artifact_index.json` 与测试期望不一致；当前 `artifact_index` 主要仍是旧 `samplereverse` 状态，不能被当作当前训练集证据。
- 生成的 inventory、case、status overlay、evaluation queue 方向基本正确：metadata-only、`${LOCAL_REVERSE_ROOT}` 占位符、无样本二进制。
- `reverse_agent/project_state.py` 已被改动以允许四类 mainline；本轮必须补充测试和报告说明，确认这不是未审计 scope drift。
- `negative_results.json` 仍禁止旧 blind search、beam/budget 扩张、stale runtime probe、提交完整 `solve_reports/`。

## 3. Do Not Do

- 不运行 solvers、candidate search、candidate validation。
- 不运行样本二进制。
- 不运行 runtime probe、debugger、emulator、hook、sidecar、IDA、Ghidra、OllyDbg、x64dbg、Frida。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不提交样本二进制、压缩包、提取内容或本地绝对路径。
- 不把 stale / missing artifact 当 current。
- 不通过手改 `pytest_result_summary.status` 掩盖失败。
- 不删除失败测试来制造通过。
- 不修改 `.codex-skills/`。
- 不改 harness 行为；若工作树已有 `reverse_agent/harness.py` 脏改动，只能记录并要求清理，不得扩大到 harness 重构。

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/project_state.py`
- `tests/test_local_reverse_training_status.py`
- `tests/test_project_state.py`
- `project_state/local_reverse_inventory.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/status_overlay.json`
- `training_materials/local_reverse/cases/*.json`

Optional, bounded:

- 只读取与失败测试直接相关的 project_state JSON。
- 不读取 unrelated harness run。
- 不读取完整 `solve_reports/`。

## 5. Required Audit

Codex must:

1. Confirm repository root is `F:\reverse-agent`.
2. Confirm active decision is this packet and `task_packet.json` is advisory only.
3. Confirm both skill profiles are active in `.codex-skills/registry.json`.
4. Re-run the failing pytest target first and record the exact failure.
5. Fix the failing test without relying on stale live `artifact_index`:
   - Preferred: convert the test to deterministic tmp_path fixture artifacts.
   - Acceptable: split live project_state smoke coverage from deterministic overlay behavior, but do not assert unavailable current artifacts.
   - Forbidden: fabricate current local_reverse artifacts in `artifact_index.json`.
6. Add or update tests so `pytest_result_summary.status == PASSED` is invalid when pytest body contains `failed` / `FAILED` result lines.
7. Ensure `lint-report` or `doctor` catches pytest summary/body contradiction.
8. Audit `reverse_agent/project_state.py` mainline handling:
   - keep the four valid mainlines if implemented correctly;
   - add focused test coverage for `engineering_branch`, `reverse_solving`, `tool_integration`, `training_dataset`;
   - do not broaden project_state behavior beyond this.
9. Resolve final `git status --short` mismatch:
   - if files are modified by this round, list them in `files_changed`;
   - if files were pre-existing dirty changes, state that explicitly in the report;
   - do not leave unexplained modified files.
10. Re-run the full required test command. It must produce `0 failed`.
11. Write `project_state/pytest_result.txt` with a truthful status.
12. Write `project_state/codex_execution_report.md` with accurate `files_changed`, `tests_ran`, `generated_artifacts`, and status.
13. Archive the round.
14. Run final `lint-report`, `status`, `doctor`, `doctor --json`.
15. Record final `git status --short`.

## 6. Implementation Scope

Allowed:

- `tests/test_local_reverse_training_status.py`
- `tests/test_project_state.py`
- `reverse_agent/project_state.py`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_rework_training_inventory_test_and_report_integrity_v1/*`

Allowed only if regeneration is necessary after test repair:

- `project_state/local_reverse_inventory.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/status_overlay.json`
- `training_materials/local_reverse/cases/*.json`

Disallowed:

- `.codex-skills/`
- sample binaries or archives
- full `solve_reports/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger integration code
- harness behavior changes
- candidate files
- unrelated project_state rebuilds

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_local_reverse_training_status.py::test_real_cpp1_target_provenance_recheck_removes_cpp1_from_queue -q
python -m pytest tests/test_local_reverse_inventory.py tests/test_local_reverse_training_status.py tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_rework_training_inventory_test_and_report_integrity_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Acceptance requires:

- pytest full command has `0 failed`;
- pytest summary status matches the actual command output;
- `lint-report` is OK after report and pytest are written;
- final `doctor` is PASS, or WARN only for historical artifact freshness;
- report does not claim ACCEPTED if any test fails;
- final `files_changed` matches actual modified files or explains pre-existing dirty files.

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if:

- Any pytest command fails.
- `pytest_result_summary.status` cannot truthfully be `PASSED`.
- The failing test requires current runtime artifacts that are stale, missing, or unavailable.
- Fixing the issue would require running samples, solvers, debuggers, IDA, Ghidra, hooks, sidecars, or runtime probes.
- Fixing the issue would require editing `.codex-skills/`.
- Final `git status --short` contains unexplained modified files.
- `lint-report` fails.
- `doctor` fails.
- The round drifts into reverse solving or tool integration.
