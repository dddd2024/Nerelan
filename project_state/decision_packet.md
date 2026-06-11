```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_engineering_gate_preflight_v1",
  "round_id": "round_20260611_engineering_gate_preflight_v1",
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

建设门禁系统第二阶段：在已有只读 `final-check` 基础上，新增 Codex 开工前使用的只读 `preflight` 门禁，降低任务开始阶段的方向错配、scope 越界和旧 artifact 误用风险。

本轮只做 `preflight` 门禁，不做自动执行命令的 `close-round`，不推进样本求解，不修 IDA/static triage 输出问题。

必须完成：

1. 扩展现有门禁 CLI，新增：
   ```bash
   python -m reverse_agent.project_gate preflight --state-dir project_state
   ```
2. 输出结构化结果：
   ```text
   project_state/gates/preflight_result.json
   ```
3. 复用现有 `project_state` 与 `project_gate final-check` 能力，不重复实现 decision/report/pytest/archive 解析。
4. `preflight` 必须只读，不改 live state，除写入 `project_state/gates/preflight_result.json` 外不得修改其他文件。
5. `preflight` 必须检查：
   - `decision_meta` 是否存在且合法；
   - `status == APPROVED`；
   - `mainline` 是否在允许集合内；
   - `skill_profiles` 是否来自 active registry；
   - `task_packet.task / derived_task` 只是建议，不能覆盖 `decision_packet`；
   - 当前 decision 是否已被 report 消费，若已消费则不能开工；
   - `implementation_scope` / allowed files / disallowed files 是否可解析；
   - 工程主线不得推进样本求解；
   - 训练/逆向/tool 主线如果出现则必须要求检查现有 IDA/Ghidra/debugger/solver/harness 能力；
   - forbidden paths 不得出现在 allowed scope 中；
   - stale/missing artifact 不能被声明为 current evidence。
6. 添加测试覆盖 preflight 的关键失败场景。

## 2. Current Evidence

- 上一轮 `decision_20260611_engineering_gate_final_check_v1` 已完成，`project_gate final-check` 第一阶段门禁落地。
- 当前 `project_gate final-check` 已能检查 decision/report/pytest/archive/git diff 关闭阶段一致性。
- 当前 `task_packet.json` 与 `current_state.json` 仍包含旧 `samplereverse` 样本求解上下文、历史 artifact 指针和 `derived_task: repair_harness_case_result_materialization`，但本轮不应被这些旧建议带回 reverse_solving。
- 当前 `artifact_index.json` 仍有大量 stale/missing 历史样本 artifact。engineering_branch 轮中这些只能作为历史背景，不能作为 current evidence。
- `.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 与 `samplereverse-frontier@v2` 均为 active。
- `negative_results.json` 明确禁止旧 sample_solver 盲搜、单纯扩 beam/budget、提交完整 solve_reports 等方向。本轮不触碰这些方向。
- 返工率高的根因之一是 Codex 开工前没有强制检查：当前 decision 是否仍有效、scope 是否明确、主线是否被旧 task_packet 干扰。因此下一步应建设 `preflight`。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 solver、candidate search、runtime probe、debugger、hook、emulator、sidecar。
- 不修 `affine_8cfebe03` 的 IDA evidence 输出问题。
- 不推进 `samplereverse` 或任何具体样本求解。
- 不修改训练集 inventory/status/queue。
- 不读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
- 不修改 `.codex-skills/`。
- 不实现自动命令执行器或 `close-round`。
- 不把 `preflight` 设计成会修改 decision/report/pytest/archive 的工具。
- 不把 stale/missing artifacts 当 current evidence。
- 不删除或削弱已有 `final-check` 规则。

## 4. Files To Inspect

必须检查：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/decision_packet.md`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`

必要时检查：

- `README.md`
- `pyproject.toml`

## 5. Required Audit

Codex must:

1. Confirm current working directory is `F:\reverse-agent`.
2. Confirm active decision is this packet and `status` is `APPROVED`.
3. Confirm this is `engineering_branch` and not a sample-solving round.
4. Confirm skill profiles are active in `.codex-skills/registry.json`.
5. Inspect existing `project_gate.final_check()` before implementing `preflight`.
6. Reuse existing helpers from `project_state.py` and `project_gate.py` where possible.
7. Add a structured result schema similar to:
   ```json
   {
     "schema_version": 1,
     "gate_name": "preflight",
     "gate_status": "PASSED | FAILED | BLOCKED | WARN",
     "decision_id": "",
     "round_id": "",
     "mainline": "",
     "checks": [],
     "blocking_reasons": [],
     "warnings": [],
     "recommended_next_action": ""
   }
   ```
8. Add preflight checks for:
   - `decision_meta_parse`;
   - `decision_approved`;
   - `mainline_valid`;
   - `skill_profiles_active`;
   - `decision_not_consumed_by_report`;
   - `task_packet_is_non_authoritative`;
   - `implementation_scope_present`;
   - `forbidden_paths_not_allowed`;
   - `mainline_scope_policy`;
   - `artifact_freshness_policy`;
   - `tool_capability_audit_required_when_applicable`.
9. Ensure `preflight` can fail before Codex changes code when the decision is stale, consumed, invalid, or scope is unsafe.
10. Add tests proving recent failure modes are caught:
    - missing/invalid `decision_meta`;
    - status not `APPROVED`;
    - invalid mainline;
    - inactive or unknown skill profile;
    - decision already consumed by matching report;
    - allowed scope includes forbidden path such as `.codex-skills/` or `solve_reports/`;
    - engineering_branch decision tries to run sample solver/runtime;
    - reverse/tool/training decision lacks required tool capability audit wording;
    - stale artifact is described as current evidence.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if helper exposure is strictly necessary

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if shared helper tests are necessary

Allowed generated files:

- `project_state/gates/preflight_result.json`
- `project_state/gates/final_gate_result.json` only if final-check is rerun
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_engineering_gate_preflight_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
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
python -m reverse_agent.project_gate preflight --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_engineering_gate_preflight_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

`pytest_result.txt` 必须使用正式 `pytest_result_summary`，并记录所有命令 stdout/stderr。

注意：如果在 archive 前运行 `final-check`，其 failure 只能作为 expected diagnostic，不能让最终 `pytest_result_summary.status` 伪装为 PASSED。更推荐在 archive 后再运行 final-check，或在 summary 中显式记录 expected nonzero diagnostic commands。

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `preflight` 需要重写 existing project_state parser 才能实现。
- `preflight` 会修改除 `project_state/gates/preflight_result.json` 之外的 live state。
- 无法检测 consumed/stale decision。
- 无法区分 `task_packet` 建议与 `decision_packet` 权威。
- 无法检测 forbidden paths in allowed scope。
- 无法检测 engineering_branch 中混入 sample-solving/runtime/solver 行为。
- 无法给 reverse/tool/training mainline 添加 tool capability audit requirement。
- tests 不能覆盖上述 failure modes。
- 实现触碰 sample solving、IDA runner、training status、solver/runtime/debugger/probe 逻辑。
- final git status 出现 scope 外文件。
