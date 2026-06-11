```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1",
  "round_id": "round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1",
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

修复上一轮 affine static triage 的验收与状态闭环问题。核心不是继续解样本，而是让 blocked static triage 被正确记录、正确进入 training status，或者诚实报告 BLOCKED。

必须完成：

1. 修正 report 格式，使用正式 `codex_report_summary`。
2. 修正 `pytest_result.txt`，使用正式 `pytest_result_summary` 并记录完整命令输出。
3. 处理 `project_state/local_reverse_affine_8cfebe03_static_triage.json` 中的 `STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`。
4. 如果该 blocker 属于可消费的 static analysis blocker，则让 `local_reverse_training_status.py` 把 `affine_8cfebe03` 从 `inventory_only` 转为 `blocked` 或 `needs_triage`，并记录 evidence_sources。
5. 如果该 blocker 属于环境/tool failure，不能把样本标为 blocked，必须报告 `BLOCKED` 并解释原因。
6. 补齐 round archive 和 post-archive checks。

## 2. Current Evidence

- 当前 active decision 是 `decision_20260611_affine_rank1_static_triage_status_overlay_v1`，已被 Codex 尝试执行。
- 生成了 `project_state/local_reverse_affine_8cfebe03_static_triage.json`，但 artifact 显示 `tool_status: blocked`，原因是 `STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`。
- `affine_8cfebe03` 在 `local_reverse_training_status.json` 中仍是 `inventory_only`，没有 evidence_sources。
- `artifact_index.json` 没有登记该 static triage artifact 为 current。
- `pytest_result.txt` 不符合正式 schema，且没有完整命令输出。
- `codex_execution_report.md` 不符合正式 `codex_report_summary` schema。
- 当前 round archive 缺失。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 solver、candidate search、bruteforce、runtime probe、debugger、hook、emulator、sidecar。
- 不上传或提交任何本地样本二进制。
- 不读取完整 `solve_reports/`。
- 不创建 affine 专用重复模块。
- 不生成 candidate、known_candidate 或 solved 状态。
- 不把 IDA 工具失败伪装成样本已成功 triage。
- 不手写 `SUCCESS/ACCEPTED` 掩盖 doctor/lint/report 失败。

## 4. Files To Inspect

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/local_reverse_affine_8cfebe03_static_triage.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/artifact_index.json`
- `.codex-skills/registry.json`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/local_reverse_training_status.py`
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_local_reverse_training_status.py`
- `tests/test_project_state.py`

## 5. Required Audit

Codex must:

1. Confirm repo root is `F:\reverse-agent`.
2. Confirm active decision is this rework packet.
3. Confirm skill profiles are active.
4. Inspect the existing affine triage artifact and classify `STATIC_TOOL_NO_OUTPUT` as either:
   - environment/tool blocker; or
   - static analysis blocker that should enter status overlay.
5. If environment/tool blocker: write report status `BLOCKED`; do not claim SUCCESS.
6. If consumable static blocker: update `local_reverse_training_status.py` and tests so the artifact changes `affine_8cfebe03` away from unexplained `inventory_only`.
7. Register the artifact in `artifact_index.json` only if it is legitimate current evidence and clearly mark its status.
8. Rebuild training status and queue.
9. Verify `affine_8cfebe03` state is now explained, or report `BLOCKED`.
10. Write formal `pytest_result.txt` with full command outputs.
11. Write formal `codex_execution_report.md` with `codex_report_summary`.
12. Archive the round and run post-archive lint/status/doctor checks.

## 6. Implementation Scope

Allowed:

- `reverse_agent/local_reverse_training_status.py`
- `tests/test_local_reverse_training_status.py`
- `project_state/artifact_index.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1/*`

Allowed only if test coverage proves necessary:

- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `tests/test_local_reverse_single_sample_static_triage.py`
- `tests/test_project_state.py`

Disallowed:

- `.codex-skills/`
- sample binaries
- `solve_reports/`
- solver/runtime/debugger/IDA/Ghidra runner rewrites
- new affine-specific modules
- candidate generation

## 7. Tests

Run and record exact outputs:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py -q
python -m pytest tests/test_local_reverse_inventory.py tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py tests/test_project_state.py -q
python -m reverse_agent.local_reverse_training_status --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json --github-status-out training_materials/local_reverse/status_overlay.json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `STATIC_TOOL_NO_OUTPUT` cannot be classified safely.
- `affine_8cfebe03` remains unexplained `inventory_only`.
- artifact_index registration would require treating stale evidence as current.
- report or pytest_result cannot be written in formal schema.
- archive cannot be created.
- any required test/lint/status/doctor command fails.
- final git status has unexplained files.
