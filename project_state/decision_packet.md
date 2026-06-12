```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_rework2_cleanup_and_deterministic_queue_build_v1",
  "round_id": "round_20260612_rework2_cleanup_and_deterministic_queue_build_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]
}
```

# DECISION_PACKET

## 1. Goal

第二次返工上一轮错误执行。必须清理三个被误提交的占位文件：`.git_old2`、`.git_corrupt`、`.git_corrupt_v2`；恢复训练状态与 overlay 一致；按 metadata-only 方式生成确定性的 local_reverse 训练队列；最后完成完整 gate closeout。

本轮只做训练集 metadata 修复。不得运行样本、IDA/Ghidra/debugger/harness/solver，不得生成任何答案类内容。

必须完成：

1. 从版本控制中移除 `.git_old2`、`.git_corrupt`、`.git_corrupt_v2`。不得把它们改成 placeholder；最终 `git ls-files` 中不得再出现这三个路径。不得触碰真实 `.git/` 目录。
2. 纠正上一轮伪成功：`lint-report`、`doctor`、`final-check` 任一失败时，report 不得写 `SUCCESS + ACCEPTED`。
3. 恢复或修正 `project_state/local_reverse_training_status.json` 与 `training_materials/local_reverse/status_overlay.json` 的 50 样本状态一致性。当前 overlay 摘要为 `solved=1, blocked=2, needs_triage=1, inventory_only=46`；不得继续提交 `needs_triage=2, inventory_only=45` 的不一致状态，除非同时有 metadata-only 依据更新 overlay 并在 report 中说明。
4. 修复 `reverse_agent/local_reverse_training_review.py build`，使其支持：`--status`、`--overlay`、`--inventory`、`--artifact-index`、`--out`、`--queue-out`、`--github-queue-out`。
5. `build` 必须从 status/overlay/inventory/artifact_index 读取 metadata 并生成队列。不得通过会隐式改写训练状态的旧路径制造新的 status/overlay 不一致。
6. 生成或更新：`project_state/local_reverse_training_capability_review.json`、`project_state/local_reverse_training_next_queue.json`、`training_materials/local_reverse/queue.json`。
7. 队列 artifact 必须包含：`source_files`、输入摘要或 sha、`status_summary`、`primary_queue`、`secondary_queue`、`reference_or_support_queue`、`blocked_review_queue`。不得再只生成单一 `items` 数组。
8. `primary_queue` 只能包含 `inventory_only + guessed_file_type=pe + category=cpp` 的 binary target。不得包含 solved、blocked、needs_triage、Python/reference/support、text/support、crypto/cipher PE。
9. `secondary_queue` 放 crypto/cipher PE，并标注 pending cipher static evidence profile。
10. `reference_or_support_queue` 放 Python solver/reference、text/support 等非 primary target。
11. `blocked_review_queue` 放 blocked / needs_triage 样本，并保留 blocked_reason、missing evidence、next_action。
12. 跑完整 gate 链并 close-round。只有 `lint-report`、`doctor`、`final-check` 全部通过，才允许写 `SUCCESS + ACCEPTED`。

## 2. Current Evidence

- 最新审计结论仍是 `REWORK_REQUIRED`。
- 最新提交仍保留 `.git_old2`、`.git_corrupt`、`.git_corrupt_v2`，只是把内容改成 `placeholder`；这没有解决仓库污染。
- 最新 report 承认 `lint-report` 和 `doctor` 退出码为 1，却仍写 `SUCCESS + ACCEPTED`。
- 最新 `pytest_result.txt` 不是 fenced `pytest_result_summary` JSON，且没有覆盖完整 gate 链。
- 最新 `project_state/gates/final_gate_result.json` 和 `command_plan.json` 仍指向旧工程轮次。
- 最新 `local_reverse_training_review.py build` 缺少 `--status`、`--overlay`、`--out`、`--github-queue-out`。
- 最新生成的是 `project_state/local_reverse_training_review_queue.json`，结构是单一 `items`，不是分桶队列。
- 最新队列把 Python 文件 `sha_cd947414` 放入队列并标为 PE sample，违反 primary target 规则。
- 最新 `project_state/local_reverse_training_status.json` 与 `training_materials/local_reverse/status_overlay.json` 摘要不一致。
- `negative_results.json` 仍禁止重复旧盲搜、预算扩张、重复 runtime/breakpoint probe、提交完整 solve_reports 等方向。本轮不得触碰这些方向。
- `task_packet.json` 只能作为 advisory；当前执行权威是本 `decision_packet.md`。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、winpty、harness campaign、solver 或 candidate search。
- 不生成 candidate、flag、password 或答案。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不读取或上传 raw sample、sample binary、IDA database、debug trace、大体积历史 artifact。
- 不修改 `.codex-skills/`。
- 不触碰真实 `.git/` 目录。
- 不把 `.git_old2`、`.git_corrupt`、`.git_corrupt_v2` 改成 placeholder 或继续保留在版本控制。
- 不把 stale/missing artifact 改成 current。
- 不把旧 29 样本 capability review 当作当前事实。
- 不把 Python solver/reference 文件当成 primary binary target。
- 不把 crypto/cipher PE 放进 primary_queue。
- 不把 queue builder 扩成求解器、数据库、消息队列或重型 workflow engine。
- 不修改 solver、harness、IDA/Ghidra/debugger 接口。

## 4. Files To Inspect

必须先读：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/local_reverse_training_status.json`
- `training_materials/local_reverse/status_overlay.json`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/README.md`
- `project_state/local_reverse_training_capability_review.json`
- `project_state/local_reverse_training_review_queue.json` if present
- `reverse_agent/local_reverse_training_review.py`
- `tests/test_local_reverse_training_review.py`

可有界读取：

- `project_state/local_reverse_post_solve_state_sync.json`
- `project_state/local_reverse_training_status_summary_sync.json`
- `project_state/local_reverse_solver_profile_dispatch_integration_audit.json`
- `tests/test_local_reverse_training_status.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须：

1. 确认工作目录为 `F:\reverse-agent`。
2. 记录启动 baseline：`git status --short`、`git diff --name-only`。
3. 记录 `git ls-files .git_old2 .git_corrupt .git_corrupt_v2` 的输出。
4. 通过正常 Git 文件删除流程从版本控制中移除上述三个路径。
5. 再次记录 `git ls-files .git_old2 .git_corrupt .git_corrupt_v2`，输出必须为空。
6. 确认本 decision 是当前执行权威，`task_packet.json` 只是 advisory。
7. 确认 skill profiles active。
8. 比对 `local_reverse_training_status.json` 与 `status_overlay.json`，恢复或同步到一致状态。
9. 检查 negative_results，确认本轮没有重复失败方向。
10. 检查工具边界，确认本轮 metadata-only，不运行 IDA/Ghidra/debugger/solver/harness。
11. 修复 build CLI 与分桶队列输出。
12. 真实记录所有命令 stdout/stderr/exit code，更新 report 与 pytest_result。
13. 用 `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_rework2_cleanup_and_deterministic_queue_build_v1` 归档本轮。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/local_reverse_training_review.py`
- `reverse_agent/local_reverse_inventory.py` only for tiny metadata-only compatibility reuse
- `reverse_agent/project_state.py` only if tiny report/status integration is strictly required

Allowed tests:

- `tests/test_local_reverse_training_review.py`
- `tests/test_local_reverse_training_status.py` only if status/overlay consistency tests are needed
- `tests/test_project_state.py` only for project_state metadata/report integration checks
- `tests/test_project_gate.py` only if gate/report generated artifact coverage requires adjustment

Allowed generated metadata/state artifacts:

- `project_state/local_reverse_training_status.json` only to restore/sync metadata consistency with overlay
- `training_materials/local_reverse/status_overlay.json` only if metadata-only sync requires it and report explains why
- `project_state/local_reverse_training_capability_review.json`
- `project_state/local_reverse_training_next_queue.json`
- `training_materials/local_reverse/queue.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_rework2_cleanup_and_deterministic_queue_build_v1/*`

Allowed cleanup:

- Delete tracked files `.git_old2`, `.git_corrupt`, `.git_corrupt_v2`.
- Delete obsolete `project_state/local_reverse_training_review_queue.json` if replaced by `project_state/local_reverse_training_next_queue.json`.

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- sample binaries
- real `.git/` directory
- IDA/Ghidra/debugger/harness/solver modules
- candidate validation outputs
- unrelated source modules
- unrelated tests
- historical round archives except read-only inspection

## 7. Tests

必须运行并记录真实 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
git diff --name-only
git ls-files .git_old2 .git_corrupt .git_corrupt_v2
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_local_reverse_training_review.py tests/test_local_reverse_training_status.py tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.local_reverse_training_review build --status project_state/local_reverse_training_status.json --overlay training_materials/local_reverse/status_overlay.json --inventory training_materials/local_reverse/inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_capability_review.json --queue-out project_state/local_reverse_training_next_queue.json --github-queue-out training_materials/local_reverse/queue.json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_rework2_cleanup_and_deterministic_queue_build_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

验收条件：

- `.git_old2`、`.git_corrupt`、`.git_corrupt_v2` 不再出现在 `git ls-files` 输出中。
- pytest 必须通过。
- queue build 命令必须退出 0。
- 新 review/queue 的 `sample_count` / `status_summary` 必须与当前 status/overlay 一致。
- 输出文件不得包含 `E:\reverse`、绝对本地路径、raw binary bytes、candidate、flag、password。
- `primary_queue` 不得包含 solved/blocked/needs_triage、Python/reference/support、crypto/cipher PE。
- `secondary_queue`、`reference_or_support_queue`、`blocked_review_queue` 必须清楚标注 `allowed_next_action` / `not_allowed`。
- `codex_report_summary.based_on_decision_id` 必须等于 `decision_20260612_rework2_cleanup_and_deterministic_queue_build_v1`。
- `codex_report_summary.round_id` 必须等于 `round_20260612_rework2_cleanup_and_deterministic_queue_build_v1`。
- `codex_report_summary.status` 必须是合法值。
- `pytest_result.txt` 必须包含 fenced `pytest_result_summary` JSON，并覆盖 report 中的 `tests_ran`。
- `project_state/gates/command_plan.json` 与 `final_gate_result.json` 必须指向本轮 decision/round。
- lint-report、doctor、final-check 不得 FAIL。
- 若 final-check 为 WARN，则 report 不得写 `SUCCESS + ACCEPTED`；必须写 `PARTIAL + NEEDS_REVIEW` 并说明原因。
- close-round 必须成功或明确 BLOCKED。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要触碰真实 `.git/` 目录。
- 需要读取或运行 `E:\reverse` 中的样本内容才能完成。
- 需要运行 IDA/Ghidra/debugger/emulator/harness/solver/candidate search 才能完成。
- 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 需要修改 `.codex-skills/`。
- 需要改动 solver/harness/debugger/IDA/Ghidra 接口。
- 无法按 metadata-only 方式恢复 status/overlay 一致性。
- 测试显示队列生成器会把 solved/blocked/needs_triage、Python reference/support、crypto/cipher PE 放入 primary_queue。
- 输出 artifact 含绝对本地路径、raw binary 内容、candidate、flag、password。
- 需要改动本轮 scope 外文件。
