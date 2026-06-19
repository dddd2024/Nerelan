```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_consumed_report_handoff_repair_v1",
  "round_id": "round_20260619_consumed_report_handoff_repair_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复当前 project_state / gate / report handoff 中的 consumed-by-report 阻塞，并完成上一轮遗留的 report summary 一致性修复。

本轮主线是 `engineering_branch`，不是 `tool_integration` 或 `reverse_solving`。问题已经不是 affine 静态证据桥接能力，而是状态机/门禁/report 生命周期冲突：旧 decision `decision_20260619_affine_report_generated_artifacts_fix_v1` 在未完成核心修复前已经被 `codex_execution_report.md` 消费，导致 preflight 的 `decision_not_consumed_by_report` 阻塞再次执行。

本轮目标：

1. 使用新的 decision_id 解除“旧 decision 已被 report 消费”的执行阻塞。
2. 有界审计 `project_gate preflight` 对 consumed report 的判断，确认本轮是否只是状态 handoff 问题，还是 gate 规则需要后续工程修复。
3. 在不运行 IDA/static triage、solver、runtime、样本的前提下，完成上一轮真正未完成的最小修复：让新的 `codex_report_summary.generated_artifacts` 覆盖 6 个核心 artifact。
4. 产出清晰的 handoff report，说明旧 `decision_20260619_affine_report_generated_artifacts_fix_v1` 为什么 BLOCKED，以及本轮如何用新 decision 收敛状态。

必须确保新的 `project_state/codex_execution_report.md` 顶部 `codex_report_summary.generated_artifacts` 至少包含：

```text
project_state/artifact_index.json
project_state/local_reverse_affine_8cfebe03_current_static_triage.json
project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json
project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json
project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json
project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md
```

成功标准：

- 新 decision 的 preflight 通过，或者如果仍 BLOCKED，报告必须证明阻塞不是“旧 decision 已消费”的重复问题。
- 不复用 `decision_20260619_affine_report_generated_artifacts_fix_v1`。
- `codex_report_summary.generated_artifacts` 包含上述 6 个核心 artifact。
- `codex_report_summary.files_changed` 只列本轮真实改动。
- final-check 无 FAIL；若仍为 `PASSED_WITH_LIMITATIONS`，限制必须是 historical/backlog artifact non-blocking 或 close-round 过程的非阻塞提示。

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 `samplereverse` / `collect_missing_evidence` 建议，且 `execution_scope=decision_packet_controls_current_round`。它不是本轮执行权威。

当前旧 report 状态：

- `decision_20260619_affine_report_generated_artifacts_fix_v1` 已经被 `codex_execution_report.md` 消费，并被 Codex 报告为 `BLOCKED`。
- 旧阻塞点是 preflight `decision_not_consumed_by_report`：同一 decision_id 已有 consumed report，所以 gate 禁止再次进入 Implementation Scope。
- 继续复用旧 decision 只会重复 BLOCKED。

上一轮已经确认的有效 affine/current static artifacts 仍然只是被引用的项目状态产物，不允许重生成：

- `project_state/artifact_index.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

这些有效事实仍成立：

- current static triage artifact 显示 `tool_status=success`、`executed_sample=false`、`static_only=true`、`runtime_validated=false`。
- bridge result 有 4 类 evidence：StaticInputEvidence、StaticCompareEvidence、StaticTransformHintEvidence、StaticAntiDebugEvidence。
- provenance report 的 evidence_counts 已修正为 input=1、compare=1、transform_hints=1、anti_debug=1，其余为 0。
- solver dispatch plan 仍为 `readiness=needs_current_static_provenance`，缺 `transform_constant_evidence`，不得 claim solve-ready。

`negative_results.json` 继续有效：不要回到旧 `sample_solver` blind search，不要只扩 beam/budget/topN，不要把 `compare_semantics_agree=false` candidates 当 primary frontier，不要提交完整 `solve_reports/`。

## 3. Do Not Do

不要复用或再次执行 `decision_20260619_affine_report_generated_artifacts_fix_v1`。

不要重新运行 static triage。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator。

不要执行任何本地样本二进制。

不要运行 reverse-solving。

不要运行 solver、runtime probe、harness、GUI/frontend。

不要生成 candidate、flag、密码、key 或最终答案。

不要修改 affine current static artifacts、bridge result、solver dispatch plan、provenance report 或 artifact_index，除非 gate/report synthesis 明确要求更新时间戳或 round metadata；默认只读取并引用它们。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要上传、复制或提交本地样本二进制。

不要修改 `.codex-skills/`。

不要修改 Python 源码，除非有界审计证明 gate consumed-report 逻辑存在可复现工程 bug，并且该修复可以小步测试；默认本轮不改源码。

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

必须读取并交叉核对：

1. `project_state/gates/preflight_result.json`
2. `project_state/gates/final_gate_result.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/command_plan.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
6. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
7. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
8. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
9. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

Gate implementation inspection is allowed only if preflight still blocks this new decision:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_state.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_state.py`

Do not read complete heavy-history directories.

## 5. Required Audit

Before modifying files, audit and record:

1. Worktree is `F:\reverse-agent` and repository root is correct.
2. Startup `git status --short` is recorded. If dirty files exist, record baseline and do not overwrite unrelated work.
3. `decision_meta.status=APPROVED`.
4. `mainline=engineering_branch`.
5. `reverse-agent-iteration@v2` is active in `.codex-skills/registry.json`.
6. `task_packet.json` is advisory, not execution authority.
7. New decision id is not the already consumed `decision_20260619_affine_report_generated_artifacts_fix_v1`.
8. The 6 core artifacts listed in Goal exist and are readable.
9. No source/test file should be modified unless a reproducible gate bug remains after using this new decision id.

Handoff audit must answer:

1. Does preflight pass for `decision_20260619_consumed_report_handoff_repair_v1`?
2. If it fails, is the failure still `decision_not_consumed_by_report`, or a different gate issue?
3. Does the live `codex_execution_report.md` after this round use the new decision id and include the 6 core artifacts in `generated_artifacts`?
4. Does final-check report `report_status=SUCCESS` rather than `PARTIAL`?
5. Are all remaining warnings explicitly non-blocking?

## 6. Implementation Scope

Preferred implementation is metadata/report-only. Do not modify Python source by default.

Allowed files:

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
- `project_state/rounds/round_20260619_consumed_report_handoff_repair_v1/*`

Allowed only if `project_state build` is required and recorded because preflight still cannot distinguish the new decision from the old consumed decision:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`

Allowed source files only if a reproducible gate bug remains after using the new decision id and after `project_state build`:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

If source files are changed, add focused tests. If source files are not changed, do not add tests just to satisfy scope.

Do not modify these core evidence artifacts:

- `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

## 7. Tests

Must run and write results to `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If preflight is still blocked by consumed/stale decision state, stop normal implementation and run only this state rebuild command before retrying preflight once:

```powershell
python -m reverse_agent.project_state build
python -m reverse_agent.project_gate preflight --state-dir project_state
```

If any Python source is changed, additionally run:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
```

If final-check passes or only has explicitly non-blocking warnings, close the round and rerun final-check:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_consumed_report_handoff_repair_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, and `generated_artifacts`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. Cannot confirm repository root `F:\reverse-agent`.
2. `decision_meta` is missing or not `APPROVED`.
3. `mainline` is not `engineering_branch`.
4. `reverse-agent-iteration@v2` is not active.
5. Any of the 6 core artifacts listed in Goal is missing.
6. Fix requires rerunning IDA/static triage.
7. Fix requires running sample binary, solver, runtime probe, debugger, emulator, harness, GUI/frontend, or candidate generation.
8. Fix requires reading complete `solve_reports/` or complete `PROJECT_PROGRESS_LOG.txt`.
9. preflight still reports the new decision as already consumed after one `project_state build` retry.
10. report/decision/pytest_result IDs mismatch after regeneration.
11. final-check has any FAIL.
12. final-check still reports report/provenance/generated_artifacts mismatch.
