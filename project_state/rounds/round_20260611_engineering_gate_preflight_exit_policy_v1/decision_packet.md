```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_engineering_gate_preflight_exit_policy_v1",
  "round_id": "round_20260611_engineering_gate_preflight_exit_policy_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

修正 `project_gate preflight` 的阻断语义，让它真正成为 Codex 开工前的强制门禁。

本轮只修：

1. `preflight` 在 `FAILED` 或 `BLOCKED` 时必须返回非 0 exit code。
2. 明确区分：
   - 开工前 `preflight`：应为 `PASSED` 才能继续；
   - report 生成后的 consumed decision：应为 `BLOCKED`，这是正确诊断，但不能作为成功命令伪装通过。
3. 调整测试与 pytest_result 记录方式，避免 `pytest_result_summary.status: PASSED` 包含未解释的 `BLOCKED` 命令。
4. 保持 `final-check` 现有能力不削弱。

## 2. Current Evidence

- `preflight` 已经实现并能检测 consumed decision。
- 当前 live `preflight_result.json` 显示 `gate_status: BLOCKED`，原因是当前 decision 已被 report 消费。
- 当前 `pytest_result.txt` 中 `preflight` 输出 `BLOCKED`，但命令 exit code 仍是 0。
- `final-check` 已能在归档后通过，说明 closeout 门禁本身可用。
- 这轮不应修改样本求解、IDA、solver、训练状态。

## 3. Do Not Do

- 不进入 `reverse_solving`。
- 不修 `affine_8cfebe03`。
- 不运行样本二进制。
- 不运行 solver、runtime probe、debugger、hook、emulator、sidecar。
- 不修改 `.codex-skills/`。
- 不读取完整 `solve_reports/`。
- 不实现 `close-round`。
- 不削弱 `final-check`。
- 不把 `BLOCKED` 当作命令成功。

## 4. Files To Inspect

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/final_gate_result.json`

## 5. Required Audit

Codex must:

1. Confirm repo root is `F:\reverse-agent`.
2. Confirm active decision is this packet.
3. Confirm mainline is `engineering_branch`.
4. Confirm `preflight` currently returns 0 for `BLOCKED`.
5. Change CLI exit policy:
   ```text
   preflight PASSED -> exit 0
   preflight WARN -> exit 0 or configurable nonzero, but must be documented
   preflight BLOCKED -> exit nonzero
   preflight FAILED -> exit nonzero
   final-check PASSED -> exit 0
   final-check BLOCKED -> exit 0 only if BLOCKED report is internally consistent
   final-check FAILED -> exit nonzero
   ```
6. Add tests proving:
   - `main(["preflight", ...]) == 0` when `gate_status == PASSED`;
   - `main(["preflight", ...]) != 0` when consumed decision causes `BLOCKED`;
   - `main(["preflight", ...]) != 0` when decision invalid causes `FAILED`;
   - `final-check` behavior remains unchanged for consistent `BLOCKED` reports.
7. Adjust required command order so preflight is run before report consumption in normal use.
8. If post-report `preflight` is intentionally run as a diagnostic, it must be recorded as expected nonzero, not hidden inside `PASSED`.

## 6. Implementation Scope

Allowed:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `project_state/gates/preflight_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- sample binaries
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- solver modules
- IDA/Ghidra/debugger/runtime/probe modules
- training inventory/status/queue files

## 7. Tests

Run and record exact outputs:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_engineering_gate_preflight_exit_policy_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Note: current decision will be consumed after report generation, so closeout must not record post-report `preflight BLOCKED` as an ordinary successful command. If post-report preflight is run intentionally, record it as an expected nonzero diagnostic.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `preflight BLOCKED` still returns exit 0.
- Consumed-decision nonzero exit cannot be tested.
- Fixing this changes the already-passing `final-check` closeout behavior.
- The change requires touching sample solving, IDA runner, solver, runtime, or training status.
- Final git status has scope-out files.
