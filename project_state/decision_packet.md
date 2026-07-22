```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260722_architecture_constitution_gate_compatibility_rework_v1",
  "round_id": "round_20260722_architecture_constitution_gate_compatibility_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260722_architecture_constitution_and_migration_baseline_v1",
  "follows_last_round_id": "round_20260722_architecture_constitution_and_migration_baseline_v1",
  "previous_audit_outcome": "BLOCKED",
  "workstream_id": "architecture-constitution-gate-compatibility-rework-v1",
  "source_issue": 12,
  "source_pull_request": 11,
  "required_branch": "agent/architecture-constitution-plan-v1",
  "activation_base_sha": "53606188e34a580e6e534bbef03a56af5eecbf41",
  "roadmap_basis": "docs/roadmap/p0_architecture_constitution_execution_plan_v1.md",
  "risk_tier": "R1",
  "required_profile": "fast",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "command_plan_precedes_execution_required": true,
  "command_plan_digest_lock_required": true,
  "closeout_required": false,
  "close_round_required": false,
  "closeout_allowed": false,
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
    "docs/architecture/storage-and-artifact-ownership.md",
    "docs/architecture/sandbox-and-execution-boundary.md",
    "docs/architecture/migration-and-legacy-exit.md",
    "docs/architecture/governance-cost-model.md",
    "docs/adr/ADR-001-modular-monolith.md",
    "docs/adr/ADR-002-separate-development-and-analysis-workflows.md",
    "docs/adr/ADR-003-separate-trust-bounded-contexts.md",
    "docs/adr/ADR-004-unique-source-of-truth.md",
    "docs/adr/ADR-005-storage-ownership.md",
    "docs/adr/ADR-006-evidence-and-claim-versioning.md",
    "docs/adr/ADR-007-langgraph-workflow-ownership.md",
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
    "project_state/rounds/round_20260722_architecture_constitution_gate_compatibility_rework_v1/*"
  ],
  "read_only_reference_files": [
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
    "applies_to": "the replacement Decision commit and later validated documentation-only commits on PR #11",
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

以新的不可变 Decision 替换被 preflight 阻塞的 P0 v1 Decision，并继续执行 **P0：Architecture Constitution and Migration Baseline** 文档轮。

本轮仍只冻结产品边界、模块边界、两条 Workflow、两个 trust bounded context、唯一事实源、存储归属、Evidence/Claim 版本规则、Sandbox 边界、Legacy 退出路线和 P1-P16 顺序。

本 Decision 专门修复两个授权兼容问题：

1. 允许文档路径不得再触发 sample scope 误判；
2. 显式 Profile、自动 Profile 与 Command Plan 必须一致。

## 2. Current Evidence

- 当前工作分支为 `agent/architecture-constitution-plan-v1`。
- PR #11 在本 Decision 激活前的 head 为 `53606188e34a580e6e534bbef03a56af5eecbf41`。
- PR #9 仍冻结在 exact head `43418818af61d9be3208d2444fd6ce5120f73fab`。
- 上一 Decision 的 decision-lint、显式 Gate Profile、Command Plan 和 startup snapshot 已通过。
- 上一 Decision 的 preflight 在任何架构正文修改前阻塞。
- 第一项阻塞来自允许文档文件名被旧 mainline-scope 规则误判。
- 第二项阻塞来自显式 `standard` Profile 与 preflight 自动推导的 `fast` Profile 冲突。
- 上一 Decision 声明激活后不可变，因此不得原地编辑；本 Decision 以新的 ID 和 Round 正式替换它。
- P0 是 R1 文档轮。为与现有自动推导保持一致，本轮使用 `fast` Profile，不要求 run-closeout 或 close-round。
- 未修改架构正文、ADR、源码、测试、依赖、Workflow、Skill 或 PR #9。

## 3. Do Not Do

不得：

- 修改已经被阻塞的上一 Decision 的 Git 历史；
- 在新 Command Plan 和 preflight 通过前修改架构正文、ADR 或长期路线正文；
- 修改 Gate 源码、测试代码、依赖、Workflow 或 Skill；
- 重新强制选择 `standard` 或 `full` Profile；
- 在本轮运行 run-closeout 或 close-round；
- 修改或合并 PR #9；
- 实现 EvidenceUnit、Claim、数据库、CAS、Sandbox、Provider、Web 或新的 AgentRunner；
- 执行未知二进制或调用逆向工具；
- 直接 push main、rebase、squash、force-push、tag 或 release；
- 使用 `git add -A` 或提交无关文件。

## 4. Files To Inspect

执行前必须检查：

- `project_state/decision_packet.md`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/gates/preflight_result.json`
- 三份现有 P0 规划文档
- `.codex-skills/registry.json`
- `.codex-skills/reverse-agent-iteration/SKILL.md`
- `reverse_agent/project_gate.py`，只读
- `tests/test_project_gate.py`、`tests/test_project_reports.py`、`tests/test_project_state.py`，只读
- PR #9、PR #11 和 Issue #12 的远端状态
- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`

不得读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

最终报告必须逐项回答：

1. 当前 Decision 与 Round ID 是否为本 replacement Decision？
2. 上一 Decision 是否保留在 Git 历史且未被原地改写？
3. 当前分支和 activation base SHA 是否准确？
4. 自动 Gate Profile 是否为 `fast`？
5. Command Plan 是否不包含 run-closeout 和 close-round？
6. 新 Command Plan 是否在所有正文修改和测试前生成并锁定？
7. preflight 是否不再出现路径 scope 误判？
8. preflight 是否不再出现 Profile/closeout 冲突？
9. 实际变更是否仅位于允许的 docs、ADR 和当前轮证据文件？
10. PR #9 是否保持 exact head 且未修改？
11. Development Workflow 与 Binary Analysis Workflow 是否分离？
12. Engineering Control Plane 与 Binary Analysis Trust Domain 是否分离？
13. 每类动态事实是否只有一个可变权威？
14. `Trust != Confidence != Validation` 是否明确？
15. EvidenceUnit、ActionReceipt、ValidationResult 和 sealed CapsuleManifest 是否不可覆盖？
16. Claim 是否仅通过 revision 演化？
17. Metadata、Artifact、Checkpoint、Telemetry 和 Capsule 的归属是否唯一？
18. Sandbox S0-S3 和 Worker 权限边界是否明确？
19. Legacy 退出路线和治理成本上限是否明确？
20. 本轮是否没有源码、测试代码、依赖、Workflow、数据库或运行时变更？
21. 必要测试、文档一致性检查、execution-log 和 final-check 是否通过？

## 6. Implementation Scope

允许完成：

- `docs/architecture/architecture-spine-v2.md`
- `docs/architecture/trust-model.md`
- `docs/architecture/data-contracts.md`
- `docs/architecture/storage-and-artifact-ownership.md`
- `docs/architecture/sandbox-and-execution-boundary.md`
- `docs/architecture/migration-and-legacy-exit.md`
- `docs/architecture/governance-cost-model.md`
- ADR-001 至 ADR-010，其中 ADR-007 使用 workflow ownership 文件名
- `docs/roadmap/long-term-implementation-plan-v2.md`
- 对三份现有规划文件进行必要的文件名、交叉引用和状态修正

执行顺序：

```text
replacement Decision activation
→ discard or isolate stale v1 gate outputs
→ automatic fast gate-profile
→ new command-plan and digest lock
→ startup snapshot
→ preflight
→ architecture documents and ADRs
→ roadmap consistency
→ tests and document checks
→ reports, execution-log and final-check
→ ARCHITECTURE_CONSTITUTION_ACCEPTED
```

## 7. Tests

在新 Command Plan 和 preflight 通过后，至少运行：

```text
git status --short
git diff --check
git diff --name-only
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

不得运行 run-closeout 或 close-round。

## 8. Acceptance Criteria

本轮只有在以下条件全部满足时才能标记：

```text
ARCHITECTURE_CONSTITUTION_ACCEPTED
```

- replacement Decision lint 通过；
- 自动 `fast` Profile、Command Plan、startup snapshot 和 preflight 通过；
- 两个原阻塞均消失；
- 所有架构文档和 ADR 完成；
- 三份旧规划文件的文件名引用已同步；
- 测试、文档一致性检查、execution-log 和 final-check 通过；
- PR #9 始终未修改；
- 没有越权代码或运行时变更；
- 最终报告逐项回答 Required Audit。

## 9. Stop Conditions

遇到以下任一情况必须停止：

- PR #9 accepted head 变化；
- PR #11 出现无法解释的并行提交；
- 当前分支或 activation base 不一致；
- replacement Decision lint、Command Plan、digest lock 或 preflight 阻塞；
- 任何允许路径仍被 mainline scope 误判；
- 自动 Profile 不是 `fast`；
- Command Plan 仍包含 run-closeout 或 close-round；
- 必须修改源码、测试、依赖、Workflow 或 Skill 才能继续；
- 工作树存在无法隔离的无关改动；
- required tests 出现无法在允许范围内解释的失败。

## 10. Next Authorized Boundary

本 Decision 不授权 P1。

P0 接受后，下一步必须创建独立 Decision：

```text
P1: PR #9 Exact-head Integration and Architecture Spine Freeze
```
