```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_affine_current_static_bridge_validation_v1",
  "round_id": "round_20260619_affine_current_static_bridge_validation_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

对上一轮已完成的通用 `static artifact -> StructuredEvidence -> solver dispatch plan` 桥接层做一次 current provenance validation。

本轮主线是 `tool_integration`。目标是用现有单样本静态提取接口对 `affine_8cfebe03` 重新生成当前轮 static triage artifact，然后把这个 current artifact 送入通用 `StaticEvidenceBridge`，生成当前轮 bridge result / solver dispatch plan / provenance report。

`affine_8cfebe03` 仍然只是 acceptance target，不允许把本轮扩展成求解该题。本轮只验证工具链：

```text
existing IDA static triage runner -> current static triage artifact -> StaticEvidenceBridge -> StructuredEvidence + SolverDispatchPlan
```

本轮不生成 candidate，不生成 flag，不运行 solver，不运行 runtime validation，不执行样本二进制。若 IDA 或样本路径不可用，允许产生 blocked current artifact 和 BLOCKED report；不要用历史 artifact 伪装 current evidence。

成功标准：

1. `project_state/artifact_index.json` 登记 `local_reverse_affine_8cfebe03_static_triage`，freshness 为 `current`，source_run 为本轮 round。
2. bridge 输出使用当前轮 static triage artifact，而不是历史 fixture。
3. solver dispatch plan 最多进入 `solver_profile_hint_only` 或 `needs_current_static_provenance`，不能声称 solve-ready。
4. 报告明确下一轮是否可以转 `reverse_solving` 做 bounded constraint recovery / targeted decompilation / candidate validation。

## 2. Current Evidence

上一轮 `decision_20260619_generic_static_evidence_bridge_v1` 已被审计为 `ACCEPTED_WITH_LIMITATIONS`。它完成了通用 bridge 第一版：扩展 `reverse_agent/evidence.py`，新增 `reverse_agent/static_evidence_bridge.py`、`reverse_agent/solver_dispatch_plan.py` 和对应测试，pytest 记录为 844 passed。限制是 bridge 的示例输出仍是 `needs_current_static_provenance`，不能直接作为 reverse-solving 输入。

当前 `task_packet.json` 仍是旧 `samplereverse` / `collect_missing_evidence` 建议，且 `execution_scope=decision_packet_controls_current_round`。它不是本轮执行权威。

当前 `current_state.json` 仍是旧 `samplereverse` sample-state，`artifact_refs={}`，best candidates 为空，多个 artifact 字段为空。它不能作为本轮 affine/current static evidence。

当前 `artifact_index.json` 仍含大量 `samplereverse` missing artifact。它们是 historical/backlog notices，不能作为本轮 current evidence，也不应阻塞本轮 `tool_integration`，但 reverse-solving 和 claimed evidence 仍必须保持 strict freshness。

`negative_results.json` 继续有效：不要回到旧 `sample_solver` blind search，不要只扩 beam/budget/topN，不要把 `compare_semantics_agree=false` candidates 当 primary frontier，不要提交完整 `solve_reports/`，不要重复 `samplereverse` 已失败的 exact2/H1-H3/transform-trace 方向。

已有能力必须复用：

- `reverse_agent/local_reverse_single_sample_static_triage.py` 已存在，读取 queue/inventory，运行现有 IDA static evidence collection，明确不执行目标二进制、不生成 candidate，并能更新 `artifact_index.json`。
- 该接口已经把 IDA 输出目录切到系统 temp，以规避旧的 IDA `GetDiskFreeSpaceEx` / NTFS 8.3 路径问题。
- `reverse_agent/static_evidence_bridge.py` 已存在，纯 Python，将 dict-like static artifacts 转成 `StructuredEvidence` 和 `SolverDispatchPlan`。
- `reverse_agent/solver_dispatch_plan.py` 已存在，保守输出 readiness/profile/missing evidence/provenance notes。
- `reverse_agent/evidence.py` 已存在并包含 static evidence kind factory functions。
- 历史 `project_state/local_reverse_affine_8cfebe03_static_triage.json`、`project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 和 `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json` 只能作为格式参考和 expected signal 线索，不能作为 current evidence。

本轮要把上一轮的 bridge 从 synthetic/historical fixture 验证推进到 current static provenance 验证。

## 3. Do Not Do

不要运行 reverse-solving。

不要执行任何本地样本二进制。

不要生成 candidate、flag、密码、key 或最终答案。

不要运行 solver、harness、runtime probe、sidecar、emulator、debugger hook、GUI workflow 或 frontend workflow。

不要运行 OllyDbg/x64dbg/debugger。只允许通过现有 `local_reverse_single_sample_static_triage.py` 使用 IDA 静态提取；不得新建重复 IDA runner。

不要运行 Ghidra，除非 IDA current static triage 被明确阻塞且报告仅建议下一轮转 Ghidra fallback；本轮不实现 fallback。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要上传、复制或提交本地样本二进制。

不要修改 `.codex-skills/`。

不要修改 solver 搜索逻辑、beam/topN/budget、runtime validation、harness、GUI/frontend。

不要把历史 affine artifact 标记为 current。

不要把 `affine_8cfebe03` 写入 production bridge 逻辑。它只能出现在命令参数、artifact 名称、报告、测试 fixture 或 current provenance result 中。

不要因为 bridge 输出了 `string_compare` profile 就直接开始 candidate generation。

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

现有工具/桥接能力：

1. `reverse_agent/local_reverse_single_sample_static_triage.py`
2. `reverse_agent/static_evidence_bridge.py`
3. `reverse_agent/solver_dispatch_plan.py`
4. `reverse_agent/evidence.py`
5. `reverse_agent/tool_runners.py`
6. `reverse_agent/tool_capability_inventory.py`
7. `tests/test_static_evidence_bridge.py`
8. `tests/test_solver_dispatch_plan.py`
9. `tests/test_evidence.py`

训练 metadata / sample lookup：

1. `project_state/local_reverse_inventory.json`
2. `project_state/local_reverse_evaluation_queue.json`
3. `training_materials/local_reverse/inventory.json`
4. `training_materials/local_reverse/queue.json`
5. `training_materials/local_reverse/cases/affine_8cfebe03.json`

历史 affine artifact，read boundedly only as format/reference:

1. `project_state/local_reverse_affine_8cfebe03_static_triage.json`
2. `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`
3. `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`

Do not read complete heavy-history directories.

## 5. Required Audit

Before implementation, audit and record:

1. Worktree is `F:\reverse-agent` and repository root is correct.
2. Startup `git status --short` is recorded. If dirty files exist, record baseline and do not overwrite unrelated work.
3. `decision_meta.status=APPROVED`.
4. `mainline=tool_integration`.
5. `reverse-agent-iteration@v2` is active in `.codex-skills/registry.json`.
6. `task_packet.json` is advisory, not execution authority.
7. `local_reverse_single_sample_static_triage.py` exists and is used instead of creating a new IDA/static runner.
8. `StaticEvidenceBridge` exists and is used instead of writing sample-specific parsing.
9. No sample binary execution is performed.
10. IDA use is bounded to static analysis for `affine_8cfebe03` via the existing runner only.
11. If IDA is unavailable or returns blocked/no output, produce a blocked artifact and report the blocker; do not fallback to history as current.
12. Any generated bridge plan includes source artifact path, source_run, and provenance notes.
13. Any readiness stronger than `needs_current_static_provenance` must be justified by current artifact provenance and still must not claim solve-ready.

Must audit result quality:

1. Does current static triage artifact have `tool_status=success` or `blocked`?
2. Does it have `executed_sample=false`, `static_only=true`, `runtime_validated=false`?
3. Does artifact_index mark `local_reverse_affine_8cfebe03_static_triage` as `current` with current round id?
4. Does bridge output contain StaticInputEvidence and/or StaticCompareEvidence?
5. Does solver dispatch plan recommend profiles such as `string_compare`, `affine_shift`, `xor`, or others based on current artifact content?
6. What required missing evidence remains before reverse_solving?
7. Is next mainline `reverse_solving` appropriate, or does the result require another `tool_integration` round?

## 6. Implementation Scope

Preferred path is to run existing code and produce current artifacts. Do not modify source unless the existing bridge lacks a minimal reusable export helper.

Allowed source files only if necessary for a small reusable export/CLI bug fix:

- `reverse_agent/static_evidence_bridge.py`
- `reverse_agent/solver_dispatch_plan.py`
- `reverse_agent/evidence.py`

Allowed tests only if source files are changed:

- `tests/test_static_evidence_bridge.py`
- `tests/test_solver_dispatch_plan.py`
- `tests/test_evidence.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed generated artifacts:

- `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`
- `project_state/artifact_index.json`
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
- `project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/*`

Implementation requirements:

1. Run current static triage through the existing interface:

```powershell
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id affine_8cfebe03 --mainline tool_integration --out project_state/local_reverse_affine_8cfebe03_current_static_triage.json
```

2. Convert the resulting current static triage artifact through `StaticEvidenceBridge` with `has_current_provenance=true`, producing:
   - `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
   - `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`

3. Generate a provenance report that compares only high-level metadata against historical affine artifacts:
   - current artifact path/hash/source_run/tool_status;
   - whether IDA evidence was regenerated this round;
   - evidence counts: input, compare, constants, transform hints, crypto signatures, GUI, anti-debug;
   - dispatch readiness and recommended profiles;
   - missing evidence before solving;
   - next recommended mainline.

4. If the current static triage is blocked, still emit a blocked provenance report and update `codex_execution_report.md` with status `BLOCKED` or `SUCCESS` with `acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`, depending on gate policy. Do not mark historical evidence as current.

5. Do not produce candidate, flag, or validation result.

6. Do not modify source unless needed to expose bridge export cleanly. If source is modified, add tests.

## 7. Tests

Must run and write results to `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id affine_8cfebe03 --mainline tool_integration --out project_state/local_reverse_affine_8cfebe03_current_static_triage.json
python -m pytest tests/test_static_evidence_bridge.py tests/test_solver_dispatch_plan.py tests/test_evidence.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If source files are not modified, existing bridge tests above are sufficient. If source files are modified, update or add tests for the changed behavior and run the same pytest command.

If final-check passes and `gate_profile_plan.closeout_allowed=true`, close the round and rerun final-check:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_affine_current_static_bridge_validation_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, and `generated_artifacts`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. Cannot confirm repository root `F:\reverse-agent`.
2. `decision_meta` is missing or not `APPROVED`.
3. `mainline` is not `tool_integration`.
4. `reverse-agent-iteration@v2` is not active.
5. `affine_8cfebe03` is not found in queue/inventory and cannot be located through metadata.
6. Current static triage requires executing the target binary.
7. Current static triage requires solver, harness, runtime probe, debugger, emulator, GUI/frontend workflow, or sample execution.
8. IDA is unavailable or returns no output; in this case emit a blocked artifact/report and stop without fallback to historical artifacts as current evidence.
9. Bridge conversion requires sample-specific production logic.
10. The implementation needs modifying solver/harness/runtime/debugger/GUI/front-end code.
11. Code would hardcode `affine_8cfebe03` behavior outside command args, artifact names, reports, or tests.
12. `project_state/artifact_index.json` cannot be updated or cannot represent the current static triage artifact with source_run.
13. `pytest_result.txt` lacks real command output.
14. report/decision/pytest_result IDs mismatch.
15. final-check has any FAIL.
