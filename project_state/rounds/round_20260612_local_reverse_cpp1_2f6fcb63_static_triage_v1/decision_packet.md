```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_local_reverse_cpp1_2f6fcb63_static_triage_v1",
  "round_id": "round_20260612_local_reverse_cpp1_2f6fcb63_static_triage_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮目标是在本地逆向训练集队列中只选择一个样本 `cpp1_2f6fcb63` 做静态 triage，验证并复用现有 IDA 静态证据收集链路，把结果记录为 GitHub-safe metadata artifact。

本轮不是 reverse_solving；不得求 flag、不得生成 candidate、不得运行 solver、不得运行目标程序、不得做 runtime probe。允许的工具动作仅限 existing single-sample static triage adapter 调用 IDA 静态分析路径；如果本地样本或 IDA 不可用，必须产出 blocked metadata artifact，而不是扩大范围。

目标样本来自 `project_state/local_reverse_evaluation_queue.json` rank 1：

- `sample_id`: `cpp1_2f6fcb63`
- `relative_path`: `逆向课程2023春01/CPP1.exe`
- `allowed_actions`: only `static_triage`
- `forbidden_actions`: `runtime_probe`, `bruteforce`, `upload_binary`

必须完成：

1. 使用现有 `reverse_agent.local_reverse_single_sample_static_triage` 对 `cpp1_2f6fcb63` 执行一次 bounded static triage。
2. 输出 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`。
3. 确认 artifact 满足：`sample_id == cpp1_2f6fcb63`、`analysis_mode == single_sample_static_triage`、`static_only == true`、`executed_sample == false`、`runtime_validated == false`、无 candidate。
4. 将该 triage artifact 登记进 `project_state/artifact_index.json`，freshness 必须能反映这是本轮新产物；不得把旧 stale artifact 当 current。
5. 如果现有 status/queue builder 能无源码修改地消费该 artifact，可更新 GitHub-safe status/queue metadata；如果不能，保持原 metadata 并在 report 中说明。
6. 删除或不保留 IDA database sidecar（如 `.i64`, `.id0`, `.id1`, `.nam`, `.til`）。不得上传原始样本或 IDA database。
7. 更新 `project_state/pytest_result.txt` 和 `project_state/codex_execution_report.md`，并 archive 本轮 round。

## 2. Current Evidence

- 当前执行权威是 `project_state/decision_packet.md`；`task_packet.json` 仍包含旧 `samplereverse` 求解背景，只能作为 advisory/background，不能覆盖本轮 decision。
- 上一轮 `training_metadata_contract_repair_rework_v1` 已 ACCEPTED，final gate 通过，当前 report/pytest/gate/archive 一致。
- `project_state/local_reverse_training_inventory_audit.md` 记录：训练集 inventory 有 50 个 metadata entries，全部 `github_upload_policy: metadata_only`；status overlay 为 1 solved / 2 blocked / 1 needs_triage / 46 inventory_only。
- `project_state/local_reverse_evaluation_queue.json` 有 41 个 queue items，policy 为 `simple_static_first_unsolved_only`；rank 1 是 `cpp1_2f6fcb63`，只允许 `static_triage`，禁止 `runtime_probe`、`bruteforce`、`upload_binary`。
- 现有能力检查：`reverse_agent/local_reverse_single_sample_static_triage.py` 已存在，会通过 queue/inventory 和 `LOCAL_REVERSE_ROOT` 定位样本，并复用 `reverse_agent.tool_runners._resolve_ida_executable`、`reverse_agent.tool_runners._resolve_ida_script` 与默认 IDA script `reverse_agent/ida_scripts/collect_evidence.py`。
- 该 adapter 明确不执行目标二进制、不生成 candidate；工具不可用、timeout、parse failure 或无 evidence output 时，会生成 blocked metadata artifact。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active。
- `negative_results.json` 继续禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 `solve_reports/`、重复失败 runtime/probe 方向。本轮不触发这些方向。
- `artifact_index.json` 仍包含大量 stale/missing 历史 samplereverse artifact；本轮不得使用这些作为 current evidence。

## 3. Do Not Do

- 不执行目标二进制。
- 不运行 runtime probe、debugger hook、emulator、OllyDbg/x64dbg runtime session。
- 不运行 solver、candidate search、bruteforce、validation 或 harness case campaign。
- 不生成 candidate、flag 或答案。
- 不推进 `samplereverse`、`affine_8cfebe03` 或任何非 `cpp1_2f6fcb63` 样本。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不上传原始样本、二进制、IDA database、完整 `solve_reports/` 或本地绝对路径泄露 artifact。
- 不修改 `.codex-skills/`。
- 不新增 IDA/Ghidra/debugger/solver/harness 接口；必须复用现有 adapter 和 tool_runners。
- 不修改 solver modules、harness code、IDA scripts、Ghidra/debugger integration、project gate/schema，除非先停止并报告 BLOCKED。
- 不把 stale/missing artifact 当 current evidence。
- 不把 blocked static triage artifact 误写成 solved。

## 4. Files To Inspect

必须检查：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/local_reverse_evaluation_queue.json`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_training_inventory_audit.md`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/tool_runners.py`
- `reverse_agent/ida_scripts/collect_evidence.py`
- `tests/test_local_reverse_single_sample_static_triage.py`

必要时只读检查：

- `reverse_agent/local_reverse_training_status.py`
- `tests/test_local_reverse_training_status.py`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`

不得默认检查：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- 其他 local sample binaries
- 任何非 `cpp1_2f6fcb63` 的 raw local sample

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent`.
2. Confirm `Test-Path F:\reverse-agent` succeeds and record actual stdout in `pytest_result.txt`.
3. Capture initial `git status --short` as baseline before modification.
4. Read default project_state files in order.
5. Confirm this decision is active, `status == APPROVED`, `mainline == tool_integration`, and skill profiles are active.
6. Confirm queue rank 1 is exactly `cpp1_2f6fcb63` and allows only `static_triage`.
7. Confirm existing static triage adapter reuses IDA/tool_runners and does not execute target binary or generate candidate.
8. Run the adapter exactly once for `cpp1_2f6fcb63` with explicit queue and inventory paths.
9. Validate the triage output JSON fields listed in Goal.
10. Register the new triage artifact in `project_state/artifact_index.json` without promoting stale artifacts.
11. Remove any IDA database sidecars before final handoff. If evidence/log files are kept, verify they are bounded and GitHub-safe; otherwise delete them after summarizing into the triage artifact.
12. Run required tests and gates, recording real stdout/stderr/exit code.
13. Write a formal `codex_execution_report.md` with `codex_report_summary` for this decision.
14. Write `pytest_result.txt` with real command outputs.
15. Archive the round after report/tests are written.

## 6. Implementation Scope

Allowed generated/current evidence artifacts:

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/artifact_index.json` only to register this one static triage artifact and freshness/provenance

Allowed optional metadata updates only if existing builders support them without source/schema changes:

- `project_state/local_reverse_training_status.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_evaluation_queue.json`

Allowed report/gate/archive files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_local_reverse_cpp1_2f6fcb63_static_triage_v1/*`

Allowed temporary files:

- Temporary files under `project_state/triage_cpp1_2f6fcb63/` during adapter execution only. Before final handoff, delete IDA database sidecars (`*.i64`, `*.id0`, `*.id1`, `*.nam`, `*.til`). Keep JSON/log only if they are bounded, GitHub-safe, and listed in `generated_artifacts`; otherwise remove them.

Allowed source files:

- None.

Allowed test files:

- None.

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- sample binaries
- IDA database sidecars
- solver modules
- harness modules
- IDA/Ghidra/debugger integration code
- project gate/schema code
- tests

If completing the work requires source/test/schema/tool-interface changes, stop and report `BLOCKED`.

## 7. Tests

Run and record exact outputs:

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp1_2f6fcb63 --queue project_state/local_reverse_evaluation_queue.json --inventory training_materials/local_reverse/inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
python -c "import json, pathlib; p=pathlib.Path('project_state/local_reverse_cpp1_2f6fcb63_static_triage.json'); d=json.loads(p.read_text(encoding='utf-8')); assert d['sample_id']=='cpp1_2f6fcb63'; assert d['analysis_mode']=='single_sample_static_triage'; assert d['static_only'] is True; assert d['executed_sample'] is False; assert d['runtime_validated'] is False; assert d.get('candidate') in (None, ''); print('triage artifact ok:', d.get('tool_status'), d.get('blocked_reason',''))"
powershell -NoProfile -Command "$x=Get-ChildItem -Path project_state -Recurse -Include *.i64,*.id0,*.id1,*.nam,*.til -ErrorAction SilentlyContinue; if ($x) { $x.FullName; exit 1 } else { 'no ida db sidecars' }"
python -m pytest tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_local_reverse_cpp1_2f6fcb63_static_triage_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

`pytest_result.txt` must record real stdout/stderr/exit code for every listed command. Placeholder stdout/stderr is forbidden.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- active decision is not this packet or `status != APPROVED`.
- `.codex-skills/registry.json` does not mark declared skill profiles active.
- queue rank 1 is no longer `cpp1_2f6fcb63` or no longer allows `static_triage`.
- adapter cannot create either success or blocked metadata artifact.
- output artifact fails the required field validation.
- any IDA database sidecar remains in git status or final diff.
- source/test/schema/tool-interface changes are required.
- final-check fails.
- `pytest_result.txt` cannot record real command outputs.
- report/decision/pytest round IDs do not match.
