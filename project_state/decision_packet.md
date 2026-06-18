```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_gate_profile_tier_commit_and_state_rebuild_v1",
  "round_id": "round_20260618_gate_profile_tier_commit_and_state_rebuild_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

解决上一轮 `gate_profile_tier_verification_v1` 的 closeout 失败问题。用户已明确要求把当前 gate profile tier verification 成果上传到 GitHub，因此本轮授权 Codex 对上一轮已验证的 `tests/test_project_gate.py` 与相关 `project_state/` 产物执行本地提交和远端上传，然后 rebuild project_state 并重新运行 gate pipeline。

上一轮有效成果：三档 profile 验证测试已补充，pytest 通过，`project_state/gate_profile_tier_verification.json` 已记录 `fast / standard / full` 三档验证结果。上一轮失败原因不是测试失败，而是 close-round 在 dirty worktree 下执行，导致 `baseline_lifecycle_guard`、archived/live report、archived/live pytest_result 三类失败。

目标行为：提交并上传上一轮验证成果；刷新 project_state；重新运行 gate；只在 final-check 无 FAIL 且 closeout_allowed=true 时重新 close-round；close-round 后不再修改 live report 或 pytest_result；最终 report-summary 和 final-check 不得有 FAIL。

## 2. Current Evidence

主线是 `engineering_branch`。`task_packet.json` 仍是旧 `samplereverse` reverse-solving 建议，本轮执行权威是 `project_state/decision_packet.md`。

上一轮 `gate_profile_tier_verification_v1` 当前结论为 `FAILED / REWORK_REQUIRED`。有效成果包括 `784 passed`、新增 `TestGateProfileTierVerification`、生成 gate tier verification artifact。阻塞项包括 archived report 与 live report 不一致、archived pytest_result 与 live pytest_result 不一致、close snapshot 含未授权 dirty files。

`negative_results.json` 中 reverse-solving 禁止方向仍有效；本轮不触碰旧 sample_solver、budget-only 扩展、compare_semantics_agree=false candidate、完整 solve_reports 提交等方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 有效。

## 3. Do Not Do

不要运行 reverse-solving、样本执行、IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe。

不要修改 `.codex-skills/`，不要提交完整 `solve_reports/`，不要新增 `medium` profile，当前命名仍是 `standard`。

不要降低 full profile 的 closeout、archive、manifest 严格性。不要把 FAIL/WARN 写成 PASSED。不要把 stale archive 或 stale snapshot 当 current evidence。

不要在 close-round 后再次修改 live `project_state/codex_execution_report.md` 或 `project_state/pytest_result.txt`；如果必须修改，必须重新运行 gate 并重新 close-round。

## 4. Files To Inspect

默认先读取：`project_state/task_packet.json`、`project_state/current_state.json`、`project_state/artifact_index.json`、`project_state/negative_results.json`、`project_state/codex_execution_report.md`、`project_state/decision_packet.md`、`project_state/pytest_result.txt`、`.codex-skills/registry.json`。

重点检查：`tests/test_project_gate.py`、`project_state/gate_profile_tier_verification.json`、`project_state/gates/final_gate_result.json`、`project_state/gates/report_summary_synthesis.json`、`project_state/gates/round_close_snapshot.json`、`project_state/gates/round_delta_summary.json`、上一轮 round manifest/report/pytest。

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

执行前确认工作目录、仓库根、启动 dirty 状态、decision_meta、mainline、active skill。启动 dirty 状态必须记录为 baseline；如果 dirty 内容超出 `tests/test_project_gate.py` 和相关 `project_state/` gate/report 产物，停止并报告。

必须说明：上一轮 baseline_lifecycle_guard 为什么失败；本轮本地提交和远端上传是否成功；state build 是否成功；build 后 state_build_id/state_digest；最终 final-check 是否无 FAIL；如果 close-round 运行，archive report/pytest 是否与 live 一致。

## 6. Implementation Scope

用户已授权本轮提交并上传上一轮 gate profile tier verification 成果。

允许纳入提交范围：`tests/test_project_gate.py`、`project_state/gate_profile_tier_verification.json`、当前 gate/report/pytest/state 产物，以及本轮生成的 `project_state/rounds/round_20260618_gate_profile_tier_commit_and_state_rebuild_v1/*`。

允许生成或更新：`project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/gates/*.json`、`project_state/artifact_index.json`、`project_state/current_state.json`、`project_state/task_packet.json`、本轮 round archive。

只有发现明确 bounded gate bug 时，才允许小范围修改 `reverse_agent/project_gate.py`、`tests/test_project_gate.py`、`tests/test_project_state.py`。不得修改其它源码模块。

## 7. Tests

必须记录到 `project_state/pytest_result.txt`：启动目录与仓库确认、启动 git 状态、用户授权范围的本地提交与远端上传结果、`python -m reverse_agent.project_state build`、`python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`、preflight、gate-profile、gate-profile --json、command-plan、command-plan --json、report-summary、final-check。

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`，运行 close-round 使用 round id `round_20260618_gate_profile_tier_commit_and_state_rebuild_v1`，随后再次运行 final-check。close-round 后不得再改 live report/pytest_result。

报告必须包含 commit SHA、远端上传状态、state_build_id/state_digest、files_changed、tests_ran、generated_artifacts、final-check 状态、close-round 是否运行和结果。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：目录或仓库不正确；decision_meta 不合法；skill inactive；dirty 文件超出授权范围；远端上传失败；state build 失败；需要运行样本或逆向工具；需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG；需要修改允许范围外文件；降低 full closeout 严格性；close-round 后又修改 live report/pytest_result；最终 report-summary 或 final-check 有 FAIL；报告声称 closeout 成功但 archived report/pytest 与 live 不一致。
