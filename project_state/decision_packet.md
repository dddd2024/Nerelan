```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_allowed_paths_source_test_scope_parser_fix_v1",
  "round_id": "round_20260618_allowed_paths_source_test_scope_parser_fix_v1",
  "based_on_state_build_id": "state_20260618_114539_14d4ec94f06b",
  "based_on_state_digest": "14d4ec94f06bab113eb55fdf774e82b449b2851672e927f2b0df7a6052a95cc2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 gate 对 `Implementation Scope` 中 `Allowed paths:` 标题的 source/test scope 识别缺陷。

上一轮 `static_type_tag_contract_scope_wording_repair_v1` 已完成 type-tag contract artifact、contract report、synthetic tests，并记录 `1067 passed`，但 final-check 失败。根因不是 contract 本身失败，而是 `reverse_agent/project_gate.py` 中 `_allowed_source_test_scope_paths` 只识别包含 `allowed source`、`allowed tests` 或 `允许修改` 的标题；当前 decision 使用 `Allowed paths:`，导致 `tests/test_local_reverse_static_type_tags.py` 没被识别为允许的 source/test 变更，gate-profile 错选 `fast` 而不是 `standard`。

本轮目标：

1. 修复 `_allowed_source_test_scope_paths`，使其识别 `Allowed paths:` / `Allowed path:` / 等价 allowed-paths 标题。
2. 保持 forbidden-path parser 严格，不把 forbidden block 当 allowed scope。
3. 添加回归测试：当 `Allowed paths:` 下包含 `tests/test_*.py` 时，gate-profile 不得选择 fast；command-plan 必须包含 pytest；final-check 不应因 fast profile scope 检查失败。
4. 不修改训练 contract 语义，不扩展样本求解范围。
5. 在 gate 修复后，允许保留并验证上一轮已生成的 type-tag contract artifacts 和 tests；最终 `report-summary` 与 `final-check` 不得有 FAIL。

本轮是工程 gate parser 修复，不是逆向样本求解。

## 2. Current Evidence

主线是 `engineering_branch`。

上一轮状态：`decision_20260618_static_type_tag_contract_scope_wording_repair_v1` 的 report 为 `FAILED / REWORK_REQUIRED`。完成项包括：preflight PASSED、type-tag contract JSON 和 report 已创建、`tests/test_local_reverse_static_type_tags.py` 已创建、`1067` tests passed。失败项包括 `fast_profile_scope_valid`、`fast_profile_pytest_not_omitted_with_source_changes`、`command_plan_covers_report_tests` 等，均由 gate-profile 错误选择 fast 引发。

上一轮报告给出的根因：`_allowed_source_test_scope_paths` 没识别 `Allowed paths:`，因此 source/test scope 为空，gate-profile 错选 `fast`。

`task_packet.json` 仍可能保留旧 sample_state/reverse-solving 建议；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`negative_results.json` 中禁止方向继续有效：旧 sample_solver blind search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports 等均不得触碰。

本轮不得运行样本、debugger、IDA/Ghidra、emulator、runtime probe、sidecar 或 GUI/frontend workflow。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner 或 GUI/frontend workflow。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要读取或提交完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要修改 solver、harness、tool runner、evidence、static triage 主逻辑或训练样本 metadata 语义。

不要通过手改 report/pytest_result 掩盖 gate-profile 错选 fast 的问题。

不要降低 standard/full closeout、archive、manifest 严格性。

不要把上一轮 contract artifacts 声称为 accepted，除非本轮 final-check 通过并满足 archive/closeout 规则。

## 4. Files To Inspect

默认先读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

重点检查：

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_state.py`
4. `tests/test_local_reverse_static_type_tags.py` if present
5. `project_state/local_reverse_static_type_tag_contract.json` if present
6. `project_state/local_reverse_static_type_tag_contract_report.md` if present
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/report_summary_synthesis.json`
9. `project_state/gates/gate_profile_plan.json`
10. `project_state/gates/command_plan.json`
11. `project_state/gates/round_delta_summary.json`

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录；若存在上一轮 contract artifacts 和 tests 的 dirty files，应记录为 baseline 并说明来自上一轮 failed-but-substantive work。
5. `decision_meta.status=APPROVED`。
6. `mainline=engineering_branch`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. 本轮是 gate parser 工程修复，不是训练样本求解。

必须审计并记录：

1. `_allowed_source_test_scope_paths` 当前触发条件。
2. `Allowed paths:` 为什么没有让 `tests/test_local_reverse_static_type_tags.py` 进入 allowed source/test scope。
3. gate-profile 为什么因此选择 fast。
4. 修复后 standard/full profile 如何被正确选择。
5. forbidden paths parser 是否仍能阻断 forbidden paths。
6. 上一轮 contract artifacts 是否只是保留和验证，不做语义扩展。

## 6. Implementation Scope

Allowed source/test paths:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `tests/test_local_reverse_static_type_tags.py` if already present from the previous failed round; do not expand its contract semantics unless necessary for gate validation

Allowed project_state artifact paths:

- `project_state/local_reverse_static_type_tag_contract.json` if already present from the previous failed round
- `project_state/local_reverse_static_type_tag_contract_report.md` if already present from the previous failed round
- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260618_allowed_paths_source_test_scope_parser_fix_v1/*`

Implementation requirements:

1. Extend `_allowed_source_test_scope_paths` to recognize `Allowed paths:` as an allowed source/test scope header.
2. Add tests covering `Allowed paths:` with test files, and ensure gate-profile selects at least standard instead of fast when source/test files are in the allowed scope or round delta.
3. Add or preserve tests ensuring forbidden path parsing remains strict.
4. Do not change type-tag contract contents except to keep artifacts synchronized with report/gate state.
5. Do not modify static triage, evidence, tool runners, solver, harness, or sample metadata logic.

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
```

如果 `tests/test_local_reverse_static_type_tags.py` 存在，还必须运行：

```powershell
python -m pytest tests/test_local_reverse_static_type_tags.py tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.local_reverse_training_status --json
```

随后运行 gate：

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`，运行：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_allowed_paths_source_test_scope_parser_fix_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：profile 与 closeout_allowed、是否运行 close-round、parser 修复点、回归测试名称、上一轮 contract artifacts 是否保留、final-check 状态。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 APPROVED。
3. `mainline` 不是 `engineering_branch`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、debugger、IDA/Ghidra、emulator、runtime probe 或 sidecar。
6. 需要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改允许范围之外的文件。
8. 修复会降低 forbidden path 检查严格性。
9. 修复会削弱 standard/full closeout/archive/manifest 要求。
10. report-summary 或 final-check 最终出现 FAIL。
11. 报告声称 parser 修复完成，但没有覆盖 `Allowed paths:` source/test scope 的回归测试。
