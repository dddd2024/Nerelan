```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_training_local_reverse_queue_rebuild_v1",
  "round_id": "round_20260612_training_local_reverse_queue_rebuild_v1",
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

在工程 gate 已恢复为 `SUCCESS + ACCEPTED / final-check PASSED` 后，回到训练集主线，修复本地逆向训练队列和能力评审的“手工产物易过期”问题。

本轮只做 **metadata-only training dataset queue rebuild**：基于当前 `local_reverse_training_status.json`、`status_overlay.json`、`inventory.json` 和 `artifact_index.json` 重新生成可审计的训练队列与能力评审摘要，不读取样本二进制，不运行 IDA/Ghidra/debugger/harness，不生成 candidate。

必须完成：

1. 复核当前 local_reverse 训练状态输入，确认以 50 个样本的当前 `local_reverse_training_status.json` / `status_overlay.json` 为准，而不是旧的 29 样本 capability review。
2. 建立或修复一个确定性的 metadata-only 队列生成入口，优先复用已有 `local_reverse_inventory` / project_state 相关能力；若没有现成入口，新增小型、可测试模块，不引入重型工作流。
3. 生成当前训练队列 artifact，至少包含：
   - `source_files` 和输入 sha/摘要；
   - `status_summary`；
   - `primary_queue`：`inventory_only` + PE + cpp 样本，优先 CPP2/CPP3，再 CPP4/CPP5/其它 C++ PE；
   - `secondary_queue`：crypto/cipher PE 样本，标记为 pending cipher static evidence profile；
   - `reference_or_support_queue`：Python solver/reference、text/support 文件，明确不是 primary binary solving target；
   - `blocked_review_queue`：blocked/needs_triage 样本及其 missing evidence / next_action；
   - 每个 candidate 的 `sample_id`、`relative_path`、`category`、`training_status`、`reason`、`allowed_next_action`、`not_allowed`。
4. 重新生成 `project_state/local_reverse_training_capability_review.json` 或新增 `project_state/local_reverse_training_next_queue.json`；如果保留旧 review 文件，必须让其 sample_count/status_summary 与当前训练状态一致，不能继续保留 29 样本摘要作为当前事实。
5. 增加回归测试，证明 queue builder：
   - 不使用绝对本地路径；
   - 不读取样本文件内容；
   - 不把 solved/blocked/needs_triage 放进 primary_queue；
   - 不把 Python solver/reference 文件当作 primary binary target；
   - 对 cpp/pe inventory_only 样本生成稳定排序；
   - 输出 GitHub-safe metadata only。
6. 更新本轮 report、pytest_result、gate artifacts，并使用 close-round 归档。

## 2. Current Evidence

- 最新工程 closeout 已验收：`codex_execution_report.md` 使用 `SUCCESS + ACCEPTED`，并基于 `decision_20260612_engineering_gate_success_policy_for_legacy_artifacts_v1`。
- `pytest_result.txt` 记录 `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q` 为 `255 passed in 32.59s`，command-plan、doctor、final-check、close-round 均已记录并退出 0。
- `project_state/local_reverse_training_status.json` 当前声明 `sample_count = 50`，`status_summary = { solved: 1, blocked: 2, needs_triage: 1, inventory_only: 46 }`。
- `training_materials/local_reverse/status_overlay.json` 当前同样声明 `sample_count = 50` 与相同 status summary，说明 GitHub-safe overlay 与 project_state status 已同步。
- 旧 `project_state/local_reverse_training_capability_review.json` 仍显示旧摘要：`sample_count = 29`、`solved = 5`、`blocked = 4`、`inventory_only = 20`，其 `next_queue_candidates` 只能作为历史线索，不能当当前队列事实。
- 当前 status 中 `cpp2_f2738577`、`cpp2_fc735338`、`cpp3_019fcdc8`、`cpp3_e5a33e0b`、`cpp4_ab1b6104`、`cpp5_2ea076a7`、`cpp_6af7c7f1` 等均为 `inventory_only` / `cpp` / `pe`，`next_action` 为 static triage/manual evaluation。
- `training_materials/local_reverse/README.md` 明确：原始样本二进制不提交 GitHub，实际样本位于 `E:\reverse` 或 `LOCAL_REVERSE_ROOT`，仓库只保存 hashes、relative paths、categories、tags 等 metadata。
- `artifact_index.json` 包含大量 stale historical sample artifacts，同时有 `local_reverse_affine_8cfebe03_static_triage`、`local_reverse_cpp1_2f6fcb63_static_triage` 等 project_state metadata artifacts；本轮不得把 stale artifacts 当 current evidence。
- `negative_results.json` 禁止旧 sample_solver blind search、只扩 beam/budget、重复旧 breakpoint/runtime probe、提交完整 `solve_reports/` 等方向。本轮不触碰这些方向。
- 现有能力：`reverse_agent/local_reverse_inventory.py` 已有 local sample inventory scanner 和 GitHub-safe metadata 输出；`reverse_agent/project_state.py` 已有 status/doctor/report/archive/gate 支撑；`reverse_agent/local_reverse_constraint_recovery.py` 和相关 solver profile dispatch audit 说明 solver profile dispatch 存在但不应在本轮触发候选生成。
- 当前 `task_packet.json` 仍含旧 samplereverse reverse_solving 任务建议，只能作为 advisory；当前执行权威是本 `decision_packet.md`。

## 3. Do Not Do

- 不处理任何具体样本的求解。
- 不运行样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、winpty、harness campaign、solver、candidate search 或 bruteforce。
- 不生成 candidate、flag、密码或答案。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不读取或上传 raw sample、sample binary、IDA database、debug trace、大体积历史 artifact。
- 不修改 `.codex-skills/`。
- 不把 stale/missing artifact 改成 current。
- 不把旧 `local_reverse_training_capability_review.json` 的 29 样本摘要当作当前事实。
- 不把 Python solver/reference 文件当成 primary binary target。
- 不把 training queue builder 扩成求解器、调度器、数据库、消息队列或重型 workflow engine。
- 不修改 solver、harness、IDA/Ghidra/debugger 接口，除非发现已有 metadata-only queue 入口必须做极小兼容修复；若需要超出 scope，停止并报告。

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
- `project_state/local_reverse_solver_profile_dispatch_integration_audit.json`
- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/project_state.py`
- Existing local_reverse-related source/tests before creating any new module.

可有界读取：

- `project_state/local_reverse_post_solve_state_sync.json`
- `project_state/local_reverse_training_status_summary_sync.json`
- Existing `tests/test_local_reverse_*.py` directly related to inventory/status/solver profile metadata.

不得默认读取：

- 完整 `solve_reports/`
- 完整 `PROJECT_PROGRESS_LOG.txt`
- raw local samples under `E:\reverse`
- historical round archives except this round’s generated archive and explicitly listed metadata summaries.

## 5. Required Audit

Codex 必须：

1. 确认工作目录为 `F:\reverse-agent`。
2. 记录启动 baseline：`git status --short` 与 `git diff --name-only`。
3. 读取默认 project_state 文件，并确认本 decision 是当前执行权威，`task_packet.json` 只是 advisory。
4. 确认 skill profiles active。
5. 检查已有 local_reverse inventory/status/queue/review 相关能力；已有入口能扩展时，不新建重复模块。
6. 对比 `local_reverse_training_status.json`、`status_overlay.json`、旧 capability review 的 sample_count/status_summary，明确以当前 50 样本 status/overlay 为准。
7. 检查 current artifacts freshness，只把 current metadata artifact 作为当前证据；stale historical sample artifacts 只能作为历史线索。
8. 检查 negative_results，不得重复旧 sample_solver blind search、扩 budget、runtime probe、breakpoint probe 或完整 `solve_reports/` 提交方向。
9. 检查工具边界：本轮 metadata-only，不运行 IDA/Ghidra/debugger/solver/harness；如果队列生成需要样本文件内容或工具输出，停止并报告 BLOCKED。
10. 完成后真实记录命令 stdout/stderr/exit code，更新 `codex_execution_report.md` 与 `pytest_result.txt`。
11. 用 `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_training_local_reverse_queue_rebuild_v1` 归档本轮。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/local_reverse_training_review.py` or another already-existing local_reverse metadata queue/review module if present
- `reverse_agent/local_reverse_inventory.py` only for small metadata-only compatibility reuse
- `reverse_agent/project_state.py` only if a tiny CLI/status registration is required for the generated queue artifact

Allowed tests:

- `tests/test_local_reverse_training_review.py` or existing local_reverse metadata test file if more appropriate
- `tests/test_project_state.py` only for project_state metadata/report integration checks
- `tests/test_project_gate.py` only if gate/report generated artifact coverage requires adjustment

Allowed generated metadata artifacts:

- `project_state/local_reverse_training_capability_review.json`
- `project_state/local_reverse_training_next_queue.json`
- `training_materials/local_reverse/queue.json` only if GitHub-safe and contains no absolute paths or raw binary content
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_training_local_reverse_queue_rebuild_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- sample binaries
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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_training_local_reverse_queue_rebuild_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

若复用已有模块导致命令名不同，必须在 `codex_execution_report.md` 说明替代命令和理由，并保持同等验证强度。

验收条件：

- pytest 必须通过。
- queue/review build 命令必须退出 0。
- 新 review/queue 的 sample_count/status_summary 必须与当前 `local_reverse_training_status.json` 和 `status_overlay.json` 一致。
- 输出文件不得包含 `E:\reverse`、绝对本地路径、raw binary bytes、candidate、flag、密码。
- primary_queue 不得包含 solved/blocked/needs_triage，也不得包含 Python/reference/support 文件。
- secondary/reference/blocked 队列必须清楚标注 allowed_next_action / not_allowed。
- lint-report、doctor、final-check 不得 FAIL。
- 若 final-check 为 WARN，则 report 不得写 `SUCCESS + ACCEPTED`；必须写 `PARTIAL + NEEDS_REVIEW` 并说明原因。
- close-round 必须成功或明确 BLOCKED。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要读取或运行 `E:\reverse` 中的样本内容才能完成。
- 需要运行 IDA/Ghidra/debugger/emulator/harness/solver/candidate search 才能完成。
- 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 需要修改 `.codex-skills/`。
- 需要改动 solver/harness/debugger/IDA/Ghidra 接口。
- 发现当前 `local_reverse_training_status.json` 与 `status_overlay.json` 50 样本状态冲突且无法按 metadata-only 方式判定权威。
- 测试显示队列生成器会把 solved/blocked/needs_triage、Python reference/support 文件放入 primary_queue。
- 输出 artifact 含绝对本地路径、raw binary 内容、candidate、flag 或密码。
- 需要改动本轮 scope 外文件。
