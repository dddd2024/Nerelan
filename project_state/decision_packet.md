```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260722_architecture_constitution_and_migration_baseline_v1",
  "round_id": "round_20260722_architecture_constitution_and_migration_baseline_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260716_closeout_final_seal_and_publication_truth_rework_v2",
  "follows_last_round_id": "round_20260716_closeout_final_seal_and_publication_truth_rework_v2",
  "workstream_id": "architecture-constitution-and-migration-baseline-v1",
  "source_issue": 10,
  "source_pull_request": 11,
  "required_branch": "agent/architecture-constitution-plan-v1",
  "activation_base_sha": "7d354ee7bd12107f685419ce3e40d0d1023497d1",
  "roadmap_basis": "docs/roadmap/p0_architecture_constitution_execution_plan_v1.md",
  "risk_tier": "R1",
  "required_profile": "standard_or_full",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "command_plan_precedes_execution_required": true,
  "command_plan_digest_lock_required": true,
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "documentation_only": true,
  "source_code_change_allowed": false,
  "test_code_change_allowed": false,
  "runtime_mutation_allowed": false,
  "dependency_change_allowed": false,
  "workflow_change_allowed": false,
  "database_creation_allowed": false,
  "langgraph_upgrade_allowed": false,
  "bmad_install_allowed": false,
  "unknown_binary_execution_allowed": false,
  "tool_provider_execution_allowed": false,
  "pr9_branch_mutation_allowed": false,
  "pr9_merge_allowed": false,
  "allowed_docs": [
    "docs/architecture/architecture-spine-v2.md",
    "docs/architecture/trust-model.md",
    "docs/architecture/data-contracts.md",
    "docs/architecture/storage-and-runtime.md",
    "docs/architecture/sandbox-and-execution-boundary.md",
    "docs/architecture/migration-and-legacy-exit.md",
    "docs/architecture/governance-cost-model.md",
    "docs/adr/ADR-001-modular-monolith.md",
    "docs/adr/ADR-002-separate-development-and-analysis-workflows.md",
    "docs/adr/ADR-003-separate-trust-bounded-contexts.md",
    "docs/adr/ADR-004-unique-source-of-truth.md",
    "docs/adr/ADR-005-storage-ownership.md",
    "docs/adr/ADR-006-evidence-and-claim-versioning.md",
    "docs/adr/ADR-007-langgraph-runtime-ownership.md",
    "docs/adr/ADR-008-sandbox-worker-boundary.md",
    "docs/adr/ADR-009-telemetry-is-not-analysis-evidence.md",
    "docs/adr/ADR-010-legacy-control-plane-exit.md",
    "docs/roadmap/architecture_constitution_and_migration_baseline_v1.md",
    "docs/roadmap/architecture_constitution_implementation_plan_v1.md",
    "docs/roadmap/p0_architecture_constitution_execution_plan_v1.md",
    "docs/roadmap/long-term-implementation-plan-v2.md"
  ],
  "allowed_project_state_files": [
    "project_state/decision_packet.md",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260722_architecture_constitution_and_migration_baseline_v1/*"
  ],
  "read_only_reference_files": [
    "docs/roadmap/architecture_constitution_and_migration_baseline_v1.md",
    "docs/roadmap/architecture_constitution_implementation_plan_v1.md",
    "docs/roadmap/p0_architecture_constitution_execution_plan_v1.md",
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    ".codex-skills/registry.json",
    ".codex-skills/reverse-agent-iteration/SKILL.md"
  ],
  "forbidden_mutated_paths": [
    "reverse_agent/*",
    "tests/*",
    "frontend/*",
    ".github/workflows/*",
    ".codex-skills/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "pyproject.toml",
    "requirements*.txt",
    "package*.json",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/state_manifest.json",
    "project_state/context/*",
    "project_state/roadmap/workstreams.json",
    "project_state/domains/*",
    "project_state/jobs/*",
    "project_state/user_sessions/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/*.db",
    "project_state/index.sqlite"
  ],
  "publication_authorization": {
    "granted_by_user": true,
    "applies_to": "the activation Decision commit and later validated documentation-only commits on PR #11",
    "allowed_branch": "agent/architecture-constitution-plan-v1",
    "base_branch": "main",
    "decision_activation_commit_publication_allowed": true,
    "substantive_changes_require_command_plan": true,
    "commit_allowed": true,
    "push_allowed": true,
    "draft_pr_update_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "rebase_allowed": false,
    "force_push_allowed": false,
    "tag_mutation_allowed": false,
    "release_allowed": false,
    "workflow_mutation_allowed": false,
    "secrets_mutation_allowed": false,
    "git_add_all_allowed": false,
    "stage_only_explicit_allowed_paths": true
  }
}
```

# DECISION_PACKET

## 1. Goal

正式启动 **P0：Architecture Constitution and Migration Baseline** 文档轮。

本轮必须在任何 Trust Layer 业务实现之前，冻结以下跨模块决定：

1. 产品边界与模块化单体边界；
2. Development Workflow 与 Binary Analysis Workflow 的分离；
3. Engineering Control Plane 与 Binary Analysis Trust Domain 的分离；
4. 每类动态事实的唯一权威来源；
5. Analysis Repository、Artifact Store、Workflow Checkpointer 与 Telemetry 的存储归属；
6. Evidence、Claim、Validation、Action 与 Capsule 的不可变和版本规则；
7. LangGraph 的唯一 Workflow Runtime 职责；
8. Sandbox S0-S3 与隔离 Worker 的权限边界；
9. PR #9 精确 head 的后续集成规则；
10. Legacy Control Plane 的退出状态和不可逆条件；
11. R0-R3 治理成本上限；
12. P1-P16 的长期实施顺序。

本轮交付物仅为架构文档、ADR、路线图一致性修正和现有控制面的必要执行证据。

## 2. Current Evidence

- 当前任务唯一执行权威是 `project_state/decision_packet.md`；Issue 与 Roadmap 只提供目标和上下文。
- 用户已于 2026-07-22 明确要求正式开始工作，并要求把工作计划上传到 GitHub。
- 工作分支为 `agent/architecture-constitution-plan-v1`。
- PR #11 在激活前的 head 为 `7d354ee7bd12107f685419ce3e40d0d1023497d1`，状态为 Draft、open、unmerged。
- PR #11 已包含三份 `PLANNING_PROPOSAL_ONLY` 参考文件；它们不单独构成执行授权。
- PR #9 仍为 Draft、open、unmerged；已验收 exact head 为 `43418818af61d9be3208d2444fd6ce5120f73fab`。
- PR #9 的已完成 Decision 不允许继续修改该分支，也不允许 merge、rebase、squash、force-push、tag、release 或 mark-ready。
- 当前主分支旧 Decision 属于历史 `project_governance` 收尾轮，不能授权本轮架构文档工作，因此由本 Decision 替换当前分支上的活动权威。
- 当前阶段尚未正式建立轻量 Execution Envelope，因此本次 R1 文档轮继续使用现有 Decision 和 Command Plan 机制。
- 本轮不是 EvidenceUnit、Claim、数据库、Sandbox、LangGraph durable runtime、BMAD、Web 或工具接入轮。

## 3. Do Not Do

不得：

- 在生成并锁定当前 Decision 对应的 Command Plan 前修改任何架构正文、ADR 或长期路线正文；
- 修改 `reverse_agent/**`、`tests/**`、frontend、依赖、Workflow、Skill 或运行时；
- 修改或合并 PR #9；
- rebase、squash、force-push、tag、release、直接 push `main`；
- 安装 BMAD 或升级 LangGraph；
- 实现 EvidenceUnit、Claim、Analysis Repository、CAS、Sandbox、Provider、Action Provenance、Web 或新的 AgentRunner；
- 运行未知二进制，或调用 IDA、Ghidra、debugger、emulator、hook、MCP 或模型 API；
- 批量刷新整个 `project_state`；
- 修改 `current_state.json`、`task_packet.json`、`artifact_index.json`、`negative_results.json`、`workstreams.json` 或 domain/job/session 状态；
- 使用 `git add -A` 或提交无关文件；
- 把 CI 成功解释为二进制 Claim 已验证；
- 把工具退出码 0 解释为 Evidence 正确；
- 把 OpenTelemetry 数据自动提升为分析证据；
- 在同一轮提前执行 P1、P2 或 P3。

## 4. Files To Inspect

执行前必须检查：

- `project_state/decision_packet.md`
- `docs/roadmap/architecture_constitution_and_migration_baseline_v1.md`
- `docs/roadmap/architecture_constitution_implementation_plan_v1.md`
- `docs/roadmap/p0_architecture_constitution_execution_plan_v1.md`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `.codex-skills/registry.json`
- `.codex-skills/reverse-agent-iteration/SKILL.md`
- `reverse_agent/project_gate.py`，只读，用于确认实际可用 Gate 命令
- `tests/test_project_gate.py`、`tests/test_project_reports.py`、`tests/test_project_state.py`，只读
- PR #9、PR #11 和 Issue #10 的远端元数据
- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git log --oneline --decorate -n 20`

不要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

执行者必须逐项确认并在最终报告中分别回答：

1. 当前 Decision 与 Round ID 是否准确且状态为 `APPROVED`？
2. 当前分支是否为 `agent/architecture-constitution-plan-v1`？
3. Decision 激活提交是否先于任何架构正文修改？
4. 当前 Command Plan 是否在所有正文修改、测试和 closeout 命令之前生成？
5. 实际变更是否严格限制在允许的 docs、ADR 和必要当前轮证据文件？
6. PR #9 是否保持 exact head `43418818af61d9be3208d2444fd6ce5120f73fab` 且没有分支修改？
7. Development Workflow 与 Binary Analysis Workflow 是否使用独立 Graph、State Schema 和 Checkpoint namespace？
8. Engineering Control Plane 与 Binary Analysis Trust Domain 是否形成不重叠 bounded context？
9. 每类动态事实是否只有一个可变权威？
10. Domain 层是否明确禁止依赖 LangGraph、GitHub、FastAPI、数据库驱动、逆向工具和 Telemetry？
11. `Trust != Confidence != Validation` 是否被固定为永久规则？
12. EvidenceUnit、ActionReceipt、ValidationResult 和 sealed CapsuleManifest 是否不可覆盖？
13. Claim 是否只通过 revision 演化？
14. Metadata、Artifact、Checkpoint、Telemetry 和 Capsule 的存储归属是否唯一？
15. Sandbox S0-S3 和 Worker 凭据/文件系统边界是否明确？
16. OpenTelemetry 是否被明确限定为运行遥测而非分析证据？
17. Legacy Control Plane 是否具有 `ACTIVE_COMPATIBILITY → READ_ONLY_COMPATIBILITY → ARCHIVED → REMOVED_FROM_RUNTIME` 路线？
18. R0-R3 是否具有不同的治理成本上限？
19. PR #9 是否被安排在独立 P1 Decision 中精确集成，而非本轮合并？
20. P1-P16 顺序是否不再需要重新讨论基础存储、运行时和事实源选型？
21. 本轮是否没有源码、测试代码、依赖、Workflow、数据库或运行时变更？
22. 所有要求的控制面测试、文档一致性检查和 `git diff --check` 是否通过？

## 6. Implementation Scope

允许完成以下文档：

- `docs/architecture/architecture-spine-v2.md`
- `docs/architecture/trust-model.md`
- `docs/architecture/data-contracts.md`
- `docs/architecture/storage-and-runtime.md`
- `docs/architecture/sandbox-and-execution-boundary.md`
- `docs/architecture/migration-and-legacy-exit.md`
- `docs/architecture/governance-cost-model.md`
- ADR-001 至 ADR-010
- `docs/roadmap/long-term-implementation-plan-v2.md`
- 对三份现有规划文件进行必要的矛盾修正、交叉引用和最终状态同步

实施顺序必须是：

```text
baseline observation
→ Decision activation commit
→ command-plan generation and digest lock
→ preflight
→ architecture document skeletons
→ architecture and trust boundaries
→ data and storage boundaries
→ sandbox and migration boundaries
→ ADR-001..ADR-010
→ long-term roadmap consistency
→ scope and consistency validation
→ required tests
→ reports and final-check
→ closeout and close-round
```

建议提交拆分：

1. `Authorize architecture constitution documentation round` — 本 Decision，仅此文件；
2. `Define architecture and trust boundaries`；
3. `Define data contracts and storage ownership`；
4. `Define sandbox and legacy migration boundaries`；
5. `Finalize architecture implementation roadmap`；
6. `Close architecture constitution round`。

## 7. Tests

在 Command Plan 和 preflight 通过后，至少运行：

```text
git status --short
git diff --check
git diff --name-only
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`command-plan`、`gate-profile`、`preflight`、`run-closeout` 和 `close-round` 的实际命令必须以当前 `project_gate --help` 与生成的 Command Plan 为准。

文档一致性检查必须确认：

- ADR 编号唯一，路径存在；
- 没有两个文档同时声明同一事实的唯一权威；
- 两条 Workflow 没有混用 Graph 或 State；
- Engineering Decision 不等于 Claim Validation；
- Telemetry 不等于 Evidence；
- CI PASS 不等于 Claim verified；
- tool exit 0 不等于 Evidence correct；
- PR #9 head 在所有文档中一致；
- P0-P16 编号和依赖一致。

## 8. Acceptance Criteria

本轮只有在以下条件全部成立时才能标记：

```text
ARCHITECTURE_CONSTITUTION_ACCEPTED
```

1. 每类动态事实有唯一权威；
2. 两条 Workflow 完全分离；
3. 两个 trust bounded context 完全分离；
4. 模块依赖方向明确；
5. Evidence、Claim、Validation、Action 和 Capsule 的对象边界明确；
6. 存储归属明确；
7. 不可变和 revision 规则明确；
8. Sandbox S0-S3 明确；
9. PR #9 exact-head 集成策略明确且本轮未修改；
10. Legacy 退出路线明确；
11. 治理成本上限明确；
12. 长期顺序稳定；
13. 没有越权代码或运行时变更；
14. 测试、Gate 和文档一致性检查通过；
15. 最终报告逐项回答 Required Audit。

## 9. Stop Conditions

遇到以下任意情况必须停止并报告，不得扩大范围：

- PR #9 accepted head 变化；
- PR #11 出现无法解释的并行提交；
- 当前分支不是要求分支；
- Decision lint、Command Plan、digest lock 或 preflight 阻塞；
- Command Plan 无法授权所需文档路径；
- 必须修改源码、测试代码、依赖、Workflow 或 Skill 才能继续；
- 工作树存在无法隔离的无关改动；
- 出现两个无法统一的事实权威；
- 架构结论依赖未验证且会影响不可逆设计的技术假设；
- 需要提前实现数据库、Sandbox、Provider、LangGraph runtime 或 BMAD；
- 需要修改或合并 PR #9；
- required tests 出现与文档轮无关且不能在允许范围内解释的失败。

## 10. Next Authorized Boundary

本 Decision 不授权 P1。

P0 接受后，下一步必须创建独立 Decision：

```text
P1: PR #9 Exact-head Integration and Architecture Spine Freeze
```

P1 才能重新观察 PR #9 checks、比较 main、保留 accepted ancestry、执行授权合并并标记 `FROZEN_BASELINE`。P1 不得与 P2 Repository Hygiene 混合。
