```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_rework_training_queue_rebuild_and_repo_cleanup_v1",
  "round_id": "round_20260612_rework_training_queue_rebuild_and_repo_cleanup_v1",
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

返工上一轮错误执行：清理被误提交的 `.git_old2` / `.git_corrupt*` 仓库污染，恢复合法 report / pytest_result / gate closeout 合同，并按原目标完成 **metadata-only local_reverse training queue rebuild**。

本轮不是逆向解题，不运行样本，不运行 IDA/Ghidra/debugger/harness/solver，不生成 candidate。核心目标是把训练队列从当前 50 个样本的 metadata 状态中确定性重建出来，并让 project_state 可审计收尾。

必须完成：

1. 删除被误提交的仓库污染文件：`.git_old2`、`.git_corrupt`、`.git_corrupt_v2`。如果本地还存在同名目录，必须先确认它们不是当前仓库真实 `.git`，再清理；不得删除 `.git/`。
2. 修复上一轮非法报告状态：不得继续使用 `status = completed`、旧 `decision-2026-...` 风格 ID、`2026-06-12-r1` round_id。正式报告必须基于本 decision，并使用合法 report status：`SUCCESS`、`PARTIAL`、`FAILED` 或 `BLOCKED`。
3. 保留或重构 `reverse_agent/local_reverse_training_review.py`，但必须实现原 decision 要求的 `build` 子命令和 queue rebuild 能力，而不是只做 completeness/quality review。
4. `build` 命令必须支持：
   - `--status project_state/local_reverse_training_status.json`
   - `--overlay training_materials/local_reverse/status_overlay.json`
   - `--inventory training_materials/local_reverse/inventory.json`
   - `--artifact-index project_state/artifact_index.json`
   - `--out project_state/local_reverse_training_capability_review.json`
   - `--queue-out project_state/local_reverse_training_next_queue.json`
   - `--github-queue-out training_materials/local_reverse/queue.json`
5. 生成或更新当前训练队列 artifact，必须以当前 50 样本 `local_reverse_training_status.json` 和 `status_overlay.json` 为准，不得继续使用旧 29 样本 capability review 作为当前事实。
6. 队列输出必须至少包含：`source_files`、输入摘要/sha、`status_summary`、`primary_queue`、`secondary_queue`、`reference_or_support_queue`、`blocked_review_queue`，以及每个样本的 `sample_id`、`relative_path`、`category`、`training_status`、`reason`、`allowed_next_action`、`not_allowed`。
7. 增加或修正回归测试，证明输出是 GitHub-safe metadata only：不含绝对本地路径、不含 raw binary 内容、不含 candidate/flag/password；`primary_queue` 不包含 solved/blocked/needs_triage，也不包含 Python solver/reference/support 文件；cpp/pe inventory_only 样本排序稳定。
8. 跑完整 gate 链并 close-round：preflight、pytest、queue build、command-plan、lint-report、status、doctor、final-check、close-round、二次 final-check、最终 git status/diff。

## 2. Current Evidence

- 最新审计结论是 `REWORK_REQUIRED`。
- 当前 GitHub HEAD 中，`.git_corrupt`、`.git_corrupt_v2`、`.git_old2` 被误提交为普通仓库文件。这解释了截图中 pytest 遍历 `.git_old2` 的路径问题：本地存在异常 Git 备份/损坏项，并且已经污染到版本控制。
- 当前 `project_state/decision_packet.md` 在上一轮上传时要求执行 `decision_20260612_training_local_reverse_queue_rebuild_v1`，主线为 `training_dataset`，目标是 metadata-only queue rebuild。
- 错误执行后的 `codex_execution_report.md` 使用了不匹配的 `based_on_decision_id = decision-2026-06-12-training-dataset-local-reverse-review-001`、`round_id = 2026-06-12-r1`，且 `status = completed` 不是合法 report schema 状态。
- 错误执行只记录了 4 条命令，缺少 preflight、queue build、command-plan、lint-report、status、doctor、final-check、close-round 和最终 git status/diff。
- 错误执行新增的 `local_reverse_training_review.py` 只支持 `completeness` / `quality` review；当前 CLI 没有 `build` 子命令，也没有 `--status`、`--overlay`、`--github-queue-out` 等原 decision 要求的参数。
- 当前训练状态文件声明 `sample_count = 50`，`status_summary = { solved: 1, blocked: 2, needs_triage: 1, inventory_only: 46 }`。`training_materials/local_reverse/status_overlay.json` 同样是 50 样本摘要。
- 旧 `project_state/local_reverse_training_capability_review.json` 仍是 29 样本旧摘要，不能继续作为当前 queue/review 事实。
- `training_materials/local_reverse/README.md` 明确仓库只保存 metadata，原始样本位于 `E:\reverse` 或 `LOCAL_REVERSE_ROOT`，不得上传样本二进制。
- `negative_results.json` 禁止重复旧 sample_solver blind search、只扩 beam/budget、重复 breakpoint/runtime probe、完整 `solve_reports/` 提交等方向。本轮不得触碰这些方向。
- `task_packet.json` 仍可能包含旧 samplereverse reverse_solving 建议，只能作为 advisory；当前执行权威是本 `decision_packet.md`。

## 3. Do Not Do

- 不运行任何样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、winpty、harness campaign、solver、candidate search 或 bruteforce。
- 不生成 candidate、flag、密码或答案。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不读取或上传 raw sample、sample binary、IDA database、debug trace、大体积历史 artifact。
- 不修改 `.codex-skills/`。
- 不删除真实 `.git/` 目录。
- 不把 `.git_old2`、`.git_corrupt`、`.git_corrupt_v2` 或任何 `.git*` 异常文件继续留在版本控制里。
- 不把 stale/missing artifact 改成 current。
- 不把旧 29 样本 capability review 当作当前事实。
- 不把 Python solver/reference 文件当成 primary binary target。
- 不把 training queue builder 扩成求解器、数据库、消息队列或重型 workflow engine。
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
- `reverse_agent/local_reverse_training_review.py`
- `tests/test_local_reverse_training_review.py`
- Existing local_reverse-related source/tests before creating new files.

可有界读取：

- `project_state/local_reverse_post_solve_state_sync.json`
- `project_state/local_reverse_training_status_summary_sync.json`
- `project_state/local_reverse_solver_profile_dispatch_integration_audit.json`
- Existing `tests/test_local_reverse_*.py` directly related to metadata inventory/status/queue.

不得默认读取：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- raw local samples under `E:\reverse`
- historical round archives except this round’s generated archive and explicitly listed metadata summaries.

## 5. Required Audit

Codex 必须：

1. 确认工作目录为 `F:\reverse-agent`。
2. 记录启动 baseline：`git status --short` 与 `git diff --name-only`。
3. 运行或记录：`git ls-files .git_old2 .git_corrupt .git_corrupt_v2`，确认这些污染文件是否被跟踪。
4. 使用 `git rm --ignore-unmatch -- .git_old2 .git_corrupt .git_corrupt_v2` 从版本控制移除污染文件；如果本地还有同名目录或文件，先确认不是真实 `.git/`，再清理。
5. 读取默认 project_state 文件，并确认本 decision 是当前执行权威，`task_packet.json` 只是 advisory。
6. 确认 skill profiles active。
7. 对比 `local_reverse_training_status.json`、`status_overlay.json`、旧 capability review 的 sample_count/status_summary，明确以当前 50 样本 status/overlay 为准。
8. 检查 negative_results，确认本轮没有重复 solver/blind search/budget/runtime probe 等失败方向。
9. 检查工具边界，确认本轮 metadata-only，不运行 IDA/Ghidra/debugger/solver/harness。
10. 修复或重构 `local_reverse_training_review`，实现 `build` 子命令和队列输出；如果保留 completeness/quality review，也不得影响 build 行为。
11. 完成后真实记录所有命令 stdout/stderr/exit code，更新 `codex_execution_report.md` 与 `pytest_result.txt`。
12. 用 `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_rework_training_queue_rebuild_and_repo_cleanup_v1` 归档本轮。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/local_reverse_training_review.py`
- `reverse_agent/local_reverse_inventory.py` only for tiny metadata-only compatibility reuse
- `reverse_agent/project_state.py` only if tiny report/status integration is strictly required

Allowed tests:

- `tests/test_local_reverse_training_review.py`
- `tests/test_project_state.py` only for project_state metadata/report integration checks
- `tests/test_project_gate.py` only if gate/report generated artifact coverage requires adjustment

Allowed generated metadata artifacts:

- `project_state/local_reverse_training_capability_review.json`
- `project_state/local_reverse_training_next_queue.json`
- `training_materials/local_reverse/queue.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_rework_training_queue_rebuild_and_repo_cleanup_v1/*`

Allowed cleanup:

- Delete tracked files `.git_old2`, `.git_corrupt`, `.git_corrupt_v2`.

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
git rm --ignore-unmatch -- .git_old2 .git_corrupt .git_corrupt_v2
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_local_reverse_training_review.py tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.local_reverse_training_review build --status project_state/local_reverse_training_status.json --overlay training_materials/local_reverse/status_overlay.json --inventory training_materials/local_reverse/inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_capability_review.json --queue-out project_state/local_reverse_training_next_queue.json --github-queue-out training_materials/local_reverse/queue.json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_rework_training_queue_rebuild_and_repo_cleanup_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

验收条件：

- `.git_old2`、`.git_corrupt`、`.git_corrupt_v2` 不再出现在 `git ls-files` 输出中。
- pytest 必须通过。
- queue build 命令必须退出 0。
- 新 review/queue 的 `sample_count` / `status_summary` 必须与当前 `local_reverse_training_status.json` 和 `status_overlay.json` 一致。
- 输出文件不得包含 `E:\reverse`、绝对本地路径、raw binary bytes、candidate、flag、密码。
- `primary_queue` 不得包含 solved/blocked/needs_triage，也不得包含 Python/reference/support 文件。
- `secondary_queue`、`reference_or_support_queue`、`blocked_review_queue` 必须清楚标注 `allowed_next_action` / `not_allowed`。
- `codex_report_summary.based_on_decision_id` 必须等于 `decision_20260612_rework_training_queue_rebuild_and_repo_cleanup_v1`。
- `codex_report_summary.round_id` 必须等于 `round_20260612_rework_training_queue_rebuild_and_repo_cleanup_v1`。
- `codex_report_summary.status` 必须是合法值。
- `pytest_result.txt` 必须包含 fenced `pytest_result_summary` JSON，并覆盖 report 中的 `tests_ran`。
- lint-report、doctor、final-check 不得 FAIL。
- 若 final-check 为 WARN，则 report 不得写 `SUCCESS + ACCEPTED`；必须写 `PARTIAL + NEEDS_REVIEW` 并说明原因。
- close-round 必须成功或明确 BLOCKED。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要删除真实 `.git/` 目录。
- 需要读取或运行 `E:\reverse` 中的样本内容才能完成。
- 需要运行 IDA/Ghidra/debugger/emulator/harness/solver/candidate search 才能完成。
- 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 需要修改 `.codex-skills/`。
- 需要改动 solver/harness/debugger/IDA/Ghidra 接口。
- 发现当前 `local_reverse_training_status.json` 与 `status_overlay.json` 50 样本状态冲突且无法按 metadata-only 方式判定权威。
- 测试显示队列生成器会把 solved/blocked/needs_triage、Python reference/support 文件放入 primary_queue。
- 输出 artifact 含绝对本地路径、raw binary 内容、candidate、flag 或密码。
- 需要改动本轮 scope 外文件。
