```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260722_p0_command_plan_contract_compatibility_rework_v3",
  "round_id": "round_20260722_p0_command_plan_contract_compatibility_rework_v3",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260722_p0_standard_profile_compatibility_rework_v2",
  "follows_last_round_id": "round_20260722_p0_standard_profile_compatibility_rework_v2",
  "previous_audit_outcome": "BLOCKED_STALE_COMMAND_PLAN_EXPECTATION",
  "workstream_id": "p0-command-plan-contract-compatibility-rework-v3",
  "source_issue": 13,
  "source_pull_request": 11,
  "required_branch": "agent/architecture-constitution-plan-v1",
  "activation_base_sha": "642405d545d6a50d511df976da255086ad3aeb6e",
  "starting_remote_head": "642405d545d6a50d511df976da255086ad3aeb6e",
  "frozen_pr9_head": "43418818af61d9be3208d2444fd6ce5120f73fab",
  "roadmap_basis": "docs/roadmap/p0_architecture_constitution_execution_plan_v1.md",
  "risk_tier": "R1",
  "required_profile": "standard",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "command_plan_precedes_execution_required": true,
  "command_plan_digest_lock_required": true,
  "command_plan_kinds_compiler_derived": true,
  "startup_snapshot_separate_required": true,
  "startup_required_in_command_plan_commands": false,
  "bounded_run_round_allowed": true,
  "run_closeout_execution_allowed": false,
  "close_round_execution_allowed": false,
  "unknown_command_allowed": false,
  "closeout_required": false,
  "close_round_required": false,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "documentation_only": false,
  "source_code_change_allowed": false,
  "test_code_change_allowed": true,
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
  "allowed_test_files": [
    "tests/test_project_gate.py"
  ],
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
    "project_state/rounds/round_20260722_p0_command_plan_contract_compatibility_rework_v3/*"
  ],
  "read_only_reference_files": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    ".codex-skills/registry.json",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "reverse_agent/project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state.py"
  ],
  "forbidden_mutated_paths": [
    "reverse_agent/*",
    "reverse_agent/**",
    "tests/test_project_reports.py",
    "tests/test_project_state.py",
    "frontend/*",
    ".github/workflows/*",
    ".github/workflows/**",
    ".codex-skills/*",
    ".codex-skills/**",
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
    "applies_to": "the v3 command-plan-contract Decision activation commit and later validated P0 test/document/evidence commit on PR #11",
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
    "squash_allowed": false,
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

以新的不可变 v3 Decision 取代包含陈旧 Command Plan 预期的 v2 Decision，接受当前 compiler 对 `standard` Profile 的 bounded orchestration 投影，并继续 Issue #13 的单一测试 fixture 兼容性修复及尚未发布的 **P0：Architecture Constitution and Migration Baseline** 文档成果。

本轮只允许：

1. 对 `tests/test_project_gate.py` 中失败的 generated-audit semantic-alignment 测试及其最小相邻 helper/fixture 做 hermetic 修复；
2. 保留、复核并发布已经完成的 P0 架构文档、ADR 和 roadmap；
3. 生成本 replacement round 必需的 Gate、测试与报告证据。

## 2. Current Evidence

- 用户已明确批准 `decision_20260722_p0_command_plan_contract_compatibility_rework_v3` 与对应 round。
- v1 Decision 已作为单文件 commit `35977b412df6eb15f6dc5701572296df0be8cad0` 保留在 Git 历史；其 automatic Gate Profile 正确推导为 `standard`、`closeout_allowed=true`，与 v1 的 `fast`、`closeout_allowed=false` 冲突，因此 v1 状态为 `BLOCKED / SUPERSEDED`，不得 amend、reset 或重写。
- v2 Decision commit `642405d545d6a50d511df976da255086ad3aeb6e` 保留在 Git 历史；其 automatic `standard` Profile 正确，但它错误要求 startup 必须出现在 `command_plan.commands` 并错误禁止 bounded `run-round`，因此 v2 状态为 `BLOCKED_STALE_COMMAND_PLAN_EXPECTATION`，不得 amend、reset 或重写。
- 当前 v3 authority 继续接受 automatic `standard` Profile 和 `closeout_allowed=true`，同时保持 `closeout_required=false`、`close_round_required=false`。
- 执行工作树为既有 `F:\reverse-agent-p0`；它属于 `F:\reverse-agent` 同一仓库且承载全部未提交 P0 成果，没有创建新工作树。
- 当前分支为 `agent/architecture-constitution-plan-v1`。
- PR #11 starting remote head 与 v3 activation base 均为未改写的 v2 commit `642405d545d6a50d511df976da255086ad3aeb6e`。
- PR #9 保持 Draft、open、unmerged，并冻结在 exact head `43418818af61d9be3208d2444fd6ce5120f73fab`。
- 上一轮已通过 automatic fast Gate Profile、Command Plan、startup snapshot 与 preflight。
- 上一轮 required pytest 实际结果为 `1488 passed, 1 failed`；唯一失败是 `tests/test_project_gate.py::test_closeout_order_provenance_generated_audit_is_semantically_aligned`。
- Issue #13 已判定该测试读取 live `project_state/decision_packet.md` 并硬编码历史 `48` 问题数量，属于 fixture 设计缺陷。
- PR #11 的远端 workflow 当前在 package installation 阶段失败，因为 `main` 缺少已冻结在 PR #9 中的 packaging baseline；本轮不得复制 packaging 或修改 workflow。

## 3. Inherited Authorized WIP Inventory

以下 21 个唯一文件（7 architecture + 10 ADR + 4 roadmap）在本 Decision 激活前已经存在于工作树，分类统一为 `inherited_authorized_wip`。Issue 指令中的“20”是计数差异；为遵守“不丢弃成果”和 Issue #13 既有路径 allowlist，本 Decision 如实保留全部 21 个。记录的 SHA-256 是激活前内容摘要；不得 reset、clean、discard、覆盖或从零重新生成这些文件。

### Allowed Inherited Dirty Baseline Files

- `docs/architecture/architecture-spine-v2.md` — Architecture Spine v2 — `a2383803113cfc92f2fd0364add9687190b1a631ecb41ca46a5e8ee124d30075`
- `docs/architecture/trust-model.md` — Trust Model — `8899e2a2e01ebb6600ebe91735ed3bad8dbf160256535d6b6c9d486ccd79a51c`
- `docs/architecture/data-contracts.md` — Analysis Data Contracts — `f82f8ea98e6abbe834a7c5895afce080ca146e2418922f035b1f08010c913752`
- `docs/architecture/storage-and-artifact-ownership.md` — Storage and Artifact Ownership — `ecb91e06c315efbd449a2e75af97b92e5ff1829dea76626280dece7501680bea`
- `docs/architecture/sandbox-and-execution-boundary.md` — Sandbox and Execution Boundary — `5551f9b5c66e4787bccaf69e87718227008b757dcdb9b26d33705d4bc0c90566`
- `docs/architecture/migration-and-legacy-exit.md` — Migration and Legacy Control Plane Exit — `46e708a49a51140022f55ec1bc5b05ebee926c16cdcacfe8d79091d357b6d64b`
- `docs/architecture/governance-cost-model.md` — Governance Cost Model — `4e01f9bc14d91fcc5f9bb52e7685aaba112ba04a6f8957508e2028e9ddfae810`
- `docs/adr/ADR-001-modular-monolith.md` — ADR-001 Modular Monolith — `467efb53a7f909f4141451561f4d1f553798341bc590921147ca5e5caba0d781`
- `docs/adr/ADR-002-separate-development-and-analysis-workflows.md` — ADR-002 Separate Development and Analysis Workflows — `4c47af50dd83985c3a2f47e0f2d8f26e9b1f45e7a4286a04f23c1ce2c5750f01`
- `docs/adr/ADR-003-separate-trust-bounded-contexts.md` — ADR-003 Separate Trust Bounded Contexts — `c0c9192dafa3a1e7c2fbfa9331f93840a045184e44bc5a1e40a07df3c4a5f1a8`
- `docs/adr/ADR-004-unique-source-of-truth.md` — ADR-004 Unique Source of Truth — `be515dd67a4beb22edd470c03845fff76f9e316da9d226470935420d51e41f1e`
- `docs/adr/ADR-005-storage-ownership.md` — ADR-005 Storage Ownership — `93e5aafbfbdd6ecdfb16233765d5460ff569c0eedd22d053cabe67dd4710a0f2`
- `docs/adr/ADR-006-evidence-and-claim-versioning.md` — ADR-006 Evidence and Claim Versioning — `2a77e952ae60710847ec7f41356b519bb513cfe241628cb19155f7e103c0312e`
- `docs/adr/ADR-007-langgraph-workflow-ownership.md` — ADR-007 LangGraph Workflow Ownership — `ee19916a9801067fad5c4c150e80d5ed4a2724572c578bfaa2afe24671eed94a`
- `docs/adr/ADR-008-sandbox-worker-boundary.md` — ADR-008 Sandbox Worker Boundary — `ba60e95d16d9cc8bd31117f5d4a2ffd45ab3d2c797f45989cd23646b082ce4f0`
- `docs/adr/ADR-009-telemetry-is-not-analysis-evidence.md` — ADR-009 Telemetry Is Not Analysis Evidence — `50a4be4676cdbb7b0a4de7c43278579065545855224229458dfefe4b7de18cbf`
- `docs/adr/ADR-010-legacy-control-plane-exit.md` — ADR-010 Legacy Control Plane Exit — `2136245727ae4ed8bae974f0f67727813cfb537d67620785dfc0e40b9f34e6cc`
- `docs/roadmap/long-term-implementation-plan-v2.md` — Long-term Implementation Plan v2 — `00827ebe5e64b5758a274e93f2be33ab926041a9771a578e781141b12eb7730c`
- `docs/roadmap/architecture_constitution_and_migration_baseline_v1.md` — Architecture Constitution and Migration Baseline v1 — `71d03453cfd32a630fd6a0b9d97bc966daba828ee0f3e4037e1a7bba72b1eea3`
- `docs/roadmap/architecture_constitution_implementation_plan_v1.md` — Architecture Constitution Implementation Plan v1 — `ac973888ebe2eef873c573ed07e07f622dfde16c4802e55e64e6dda8ad43e56d`
- `docs/roadmap/p0_architecture_constitution_execution_plan_v1.md` — P0 Architecture Constitution Execution Plan v1 — `c145a74fdb43cfeac438d2c39bd99984c1e8b19d0b1f578cc96d36122f02380f`

### Inherited Gate and report evidence to refresh after activation

以下旧轮证据已被单独识别，不得与 P0 文档混淆。它们仅可在 Decision activation commit 完成后，按新 Command Plan 生成当前轮版本：

- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`

## 4. Do Not Do

不得：

- reset、clean、discard、覆盖或重新生成上述 `inherited_authorized_wip` 文档；
- 在 v3 Decision activation commit 已推送、新 automatic standard Gate Profile、compiler-generated Command Plan digest lock、独立 startup snapshot 和 preflight 全部通过前修改测试或 P0 文档；
- 修改 `tests/test_project_gate.py` 之外的任何测试文件；
- 修改 `reverse_agent/**`、`.github/workflows/**`、`.codex-skills/**`、`pyproject.toml` 或 `requirements*.txt`；
- 通过 skip、xfail、删除断言、弱化 production validation 或读取 live Decision 来规避失败；
- 添加 packaging、修改 workflow 或复制 PR #9 内容以伪造远端 CI 通过；
- 修改、合并或标记 ready PR #9；
- 实现 Issue #14、EvidenceUnit、Claim、数据库、CAS、Sandbox、Provider、Web 或 AgentRunner；
- 执行未知二进制或调用逆向工具；
- 直接 push main、merge、rebase、squash、force-push、tag 或 release；
- 使用 `git add -A`、`git add .` 或提交未明确授权路径。

## 5. Files To Inspect

执行前及每个 Gate 阶段必须检查：

- `project_state/decision_packet.md`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/gates/preflight_result.json`
- 上述 21 个唯一 `inherited_authorized_wip` 文档
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`，只读
- `tests/test_project_state.py`，只读
- `reverse_agent/project_gate.py`，只读
- PR #9、PR #11、Issue #13 的远端状态
- `git status --short`
- `git diff --check`
- `git diff --name-only`

不得读取或修改完整 `solve_reports/`；本轮不是逆向求解轮。

## 6. Required Audit

最终报告必须逐项回答：

1. 当前 Decision 与 Round ID 是否为本 replacement Decision？
2. v1 与 v2 Decision 是否保留在 Git 历史且未被 amend、reset 或重写，v2 是否标记为 `BLOCKED_STALE_COMMAND_PLAN_EXPECTATION`？
3. 当前分支、PR #11 starting remote head 与 activation base SHA 是否准确？
4. PR #9 是否保持 Draft、open、unmerged 且 exact head 未变？
5. 21 个唯一继承 P0 文件是否在激活前完成路径、标题和 SHA-256 盘点并标记为 `inherited_authorized_wip`，且是否解释了 Issue 文本中的计数差异？
6. Decision activation commit 是否只包含 `project_state/decision_packet.md`？
7. automatic Gate Profile 是否为 `standard` 且 `closeout_allowed=true`，没有使用强制 override？
8. 新 Command Plan 是否由当前 compiler 自动生成、未被手工编辑/删除/重排，并在任何测试修复和后续 P0 修改前锁定？
9. Command Plan 是否不含 `run-closeout`、`close-round`、未知或越权命令，并正确允许 compiler 生成的 bounded `run-round`？
10. startup 是否通过独立 startup snapshot 和实际启动 command blocks 验证，而不要求出现在 `command_plan.commands`；preflight 是否通过且没有 scope/profile/closeout 冲突？
11. 测试是否不再读取仓库 live `project_state/decision_packet.md`？
12. fixture 是否显式定义 Required Audit 问题并由 fixture 推导数量与顺序？
13. 历史 48-question 场景与至少一个 non-48 场景是否均被覆盖？
14. 测试是否验证问题 identity、order、answer alignment 与 semantic correspondence，而不是固定总数？
15. 是否只有 `tests/test_project_gate.py` 被修改且未弱化 production validation？
16. required focused test 和完整 P0 pytest 命令是否均为零失败？
17. Development Workflow 与 Binary Analysis Workflow 是否分离？
18. Engineering Control Plane 与 Binary Analysis Trust Domain 是否分离？
19. 每类动态事实是否只有一个可变权威？
20. `Trust != Confidence != Validation` 是否明确？
21. EvidenceUnit、ActionReceipt、ValidationResult 和 sealed CapsuleManifest 是否不可覆盖，Claim 是否只通过 revision 演化？
22. Metadata、Artifact、Checkpoint、Telemetry 和 Capsule 的归属是否唯一？
23. Sandbox S0-S3、Worker 权限、Legacy 退出路线和治理成本上限是否明确？
24. P1-P16 顺序是否在全部文档中一致，且 PR #9 integration 是否仍为独立 P1 Decision？
25. 实际变更是否仅位于允许测试、P0 文档及当前轮 Gate/report 证据？
26. report-summary、execution-log 与 final-check 是否通过？
27. 远端 package-install 失败是否被如实报告为 pre-P1 baseline debt，而没有宣称远端 CI 通过？

## 7. Implementation Scope

### Allowed test file

- `tests/test_project_gate.py`

只允许修复 `test_closeout_order_provenance_generated_audit_is_semantically_aligned` 及其最小相邻 helper/fixture：

- 不读取 live `project_state/decision_packet.md`；
- 使用临时隔离 Decision fixture；
- 从 fixture 推导 expected count/order；
- 覆盖历史 48-question 和至少一个 non-48 question shape；
- 保持 semantic identity、ordering、answer alignment、semantic correspondence 检查。

### Allowed inherited P0 documents

允许复核和发布第 3 节列出的 21 个唯一 `inherited_authorized_wip` 文件；不得从零重写。

### Allowed generated/project-state files

- `project_state/gates/*.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/rounds/round_20260722_p0_command_plan_contract_compatibility_rework_v3/*`

执行顺序不可调整：

```text
verify exact heads
→ inventory and hash inherited P0 WIP
→ commit replacement Decision only
→ push Decision commits to existing PR #11 branch
→ automatic standard Gate Profile without override
→ compiler-generate and lock replacement Command Plan without manual edits
→ validate no run-closeout, close-round, unknown or unauthorized commands
→ separately generate startup snapshot
→ preflight
→ hermetic fixture repair
→ focused pytest
→ full required P0 pytest
→ P0 document consistency review
→ allowlist and git diff checks
→ report-summary
→ execution-log
→ final-check
→ explicit-path commit
→ one push to existing PR #11
→ stop branch mutation for independent audit
```

## 8. Tests

startup 与 preflight 是独立的激活 Gate，不要求出现在 `command_plan.commands`。先运行：

```text
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
```

只有 preflight 通过后，才按 Gate Profile 与当前 compiler 自动生成的 Command Plan 执行后续命令；Decision 不手工枚举固定 command-kind 集合。原定 hermetic fixture 和 P0 验证目标保持不变，但不得执行 `run-closeout` 或 `close-round`。

原定验证参考如下，实际执行权威仍是锁定后的 Command Plan：

```text
python -m pytest tests/test_project_gate.py::test_closeout_order_provenance_generated_audit_is_semantically_aligned -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git diff --name-only
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

验收要求零失败，不要求或宣称固定的 passed 总数。bounded `run-round` 可以由 compiler 生成；不得执行 `run-closeout` 或 `close-round`。

## 9. Acceptance Criteria

本轮只有在以下条件全部满足时才能标记：

```text
P0_TEST_COMPATIBILITY_AND_ARCHITECTURE_CONSTITUTION_ACCEPTED
```

- v1/v2 Decision commits 保留且未改写，v2 标记为 `BLOCKED_STALE_COMMAND_PLAN_EXPECTATION`，v3 replacement Decision 单文件 activation commit 已推送；
- automatic `standard` Profile、`closeout_allowed=true`、Command Plan digest lock、startup snapshot 和 preflight 全部通过；
- hermetic fixture 不再依赖 live Decision，且保留 48 与 non-48 场景覆盖；
- required focused test 与完整 P0 pytest 命令零失败；
- 全部 P0 文档、ADR 和 roadmap 已复核并提交；
- 只修改允许的测试、文档与当前轮证据路径；
- final-check 通过；
- PR #9 始终保持冻结 exact head；
- 远端 package-install 失败被如实记录为 P1 前基线债务；
- 最终报告完整回答本 Decision 的 Required Audit。

## 10. Stop Conditions

遇到以下任一情况必须立即停止：

- PR #9 或 PR #11 远端 head 意外变化；
- 当前分支或 activation base 不一致；
- 继承 P0 文件无法与无关工作区分；
- replacement Decision lint、automatic standard Profile、`closeout_allowed=true`、compiler-generated Command Plan、digest lock、独立 startup snapshot 或 preflight 阻塞；
- Command Plan 包含 `run-closeout`、`close-round`、未知或越权命令，或被手工编辑、删除、重排；
- hermetic test 修复必须修改 `reverse_agent/**`；
- required tests 出现与同一 live-Decision fixture 缺陷无关的新失败；
- path scope 要求修改 Gate 源码；
- 有人提议在 P1 前添加 packaging/workflow 变更以使 PR #11 远端 CI 变绿。

## 11. Publication Boundary

本 Decision 允许在全部本地验收通过后：

- 仅显式暂存授权路径；
- 提交 test repair、P0 文档和当前轮证据；
- 向 `agent/architecture-constitution-plan-v1` 推送一次；
- 更新现有 Draft PR #11 与 Issue #13 的精确最终 head 和真实验证状态。

不得合并、mark ready、rebase、squash、force-push、tag、release、直接 push main 或修改 PR #9。

## 12. Next Authorized Boundary

P0 独立审计接受后停止。下一轮必须是单独批准的 Integration Decision：

```text
P1: PR #9 Exact-head Integration and Architecture Spine Freeze
```
