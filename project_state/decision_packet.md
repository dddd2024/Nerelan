```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260723_p0_full_profile_convergence_and_publication_v5",
  "round_id": "round_20260723_p0_full_profile_convergence_and_publication_v5",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260722_p0_legacy_gate_convergence_and_completion_v4",
  "follows_last_round_id": "round_20260722_p0_legacy_gate_convergence_and_completion_v4",
  "previous_audit_outcome": "BLOCKED_IMMUTABLE_PROFILE_CONTRACT_MISMATCH",
  "workstream_id": "p0-full-profile-convergence-and-publication-v5",
  "source_issue": 15,
  "source_pull_request": 11,
  "required_branch": "agent/architecture-constitution-plan-v1",
  "activation_base_sha": "ce6562cf18efd46e40b037b55c17368c575da82b",
  "starting_remote_head": "ce6562cf18efd46e40b037b55c17368c575da82b",
  "frozen_pr9_head": "43418818af61d9be3208d2444fd6ce5120f73fab",
  "roadmap_basis": "docs/roadmap/p0_architecture_constitution_execution_plan_v1.md",
  "risk_tier": "R1",
  "required_profile": "full",
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "command_plan_precedes_execution_required": true,
  "command_plan_digest_lock_required": true,
  "command_plan_kinds_compiler_derived": true,
  "profile_override_allowed": false,
  "startup_snapshot_separate_required": true,
  "startup_required_in_command_plan_commands": false,
  "bounded_run_round_allowed": true,
  "run_closeout_execution_allowed": true,
  "close_round_execution_allowed": true,
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "unknown_command_allowed": false,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "documentation_only": false,
  "source_code_change_allowed": true,
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
  "allowed_source_files": [
    "reverse_agent/project_gate.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state.py",
    "tests/test_project_context.py",
    "tests/test_project_state_manifest.py"
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
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260723_p0_full_profile_convergence_and_publication_v5/*"
  ],
  "read_only_reference_files": [
    ".codex-skills/registry.json",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "reverse_agent/project_state.py",
    "project_state/task_packet.json",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json"
  ],
  "forbidden_mutated_paths": [
    "reverse_agent/architecture/*",
    "reverse_agent/architecture/**",
    "reverse_agent/control_plane/*",
    "reverse_agent/control_plane/**",
    "reverse_agent/workflows/*",
    "reverse_agent/workflows/**",
    "frontend/*",
    ".github/workflows/*",
    ".github/workflows/**",
    ".codex-skills/*",
    ".codex-skills/**",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "pyproject.toml",
    "setup.py",
    "requirements*.txt",
    "package*.json",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
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
    "applies_to": "the v5 Decision activation commit and the later compiler-validated P0 source/test/document/evidence publication commit on PR #11",
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

以新的不可变 v5 Decision 接管并保留 v4 已完成但因治理合同矛盾而未发布的本地成果，在当前 compiler 正确推导的 `full` Profile 下重新绑定、验证、收尾并发布 **P0：Architecture Constitution and Migration Baseline**。

本轮不是新的功能实现轮。只允许：

1. 将 v4 本地 source、test、document 和 evidence 变更盘点为 `inherited_authorized_wip_from_v4`；
2. 在不扩大功能范围的前提下复核 `reverse_agent/project_gate.py` 的 legacy Gate convergence 修改；
3. 重新运行 full Profile 所要求的测试、Gate、closeout 和 archive/round evidence；
4. 刷新当前 v5 Decision/Round/Report 绑定的 manifest、context、execution-log、report 和 final evidence；
5. 显式提交并推送已经完成的 21 个 P0 文档和经验证的源码、测试及证据到现有 PR #11；
6. 推送后停止分支修改，等待独立审计。

## 2. Current Evidence

- 用户已明确批准由本审计方给出的 v5 Decision，并要求将其直接提交到 GitHub；本仓库文件是正式执行权威，Issue 和 PR 评论仅作为人类可读记录。
- v4 Decision activation commit 为 `ce6562cf18efd46e40b037b55c17368c575da82b`，必须保留在 Git 历史且不得 amend、reset 或重写。
- v4 同时声明 `required_profile=standard` 并授权修改 `reverse_agent/project_gate.py`；仓库已验证的 Gate Profile 规则会将该路径归为 `full`，因此 v4 状态为 `BLOCKED_IMMUTABLE_PROFILE_CONTRACT_MISMATCH`。
- 执行 Agent 在 v4 下正确停止，没有 profile override，也没有修改已激活 Decision。
- 本地已报告的技术证据包括：`1544 passed`、`run-round=PASSED`、`report-summary=0`、`final-check=0`、`git diff --check=0`。这些属于历史本地证据，必须在 v5 下重新生成并绑定，不能直接作为 v5 验收结论。
- 21 个 P0 架构、ADR 和 roadmap 文件仍保存在既有 `F:\reverse-agent-p0` 工作树；不得通过新工作树、reset、clean、discard 或重新生成丢失这些成果。
- 当前目标分支为 `agent/architecture-constitution-plan-v1`，v5 activation base 为 `ce6562cf18efd46e40b037b55c17368c575da82b`。
- PR #9 必须保持 Draft、open、unmerged，并冻结在 exact head `43418818af61d9be3208d2444fd6ce5120f73fab`。
- PR #11 的远端 CI、Decision Preflight 和 State Gate 当前在 `Install package` 阶段失败，因为 `main` 缺少 packaging baseline；该基线已存在于冻结 PR #9。本轮不得复制 packaging 或修改 workflow。

## 3. Inherited Authorized WIP From v4

在任何 substantive edit、reset、cleanup、stash、checkout、重新生成或测试执行前，必须对现有本地修改执行：

1. 记录 `git status --short`、当前 HEAD、远端 PR #11 head 和 PR #9 exact head；
2. 列出全部未提交路径；
3. 为每个继承文件计算 SHA-256；
4. 区分 v4 授权成果与无关用户改动；
5. 将合法成果标记为 `inherited_authorized_wip_from_v4`；
6. 将路径和摘要写入当前 v5 startup/baseline evidence；
7. 不得 reset、clean、discard、覆盖、静默遗漏或从零重写继承成果。

预期继承范围可能包括：

- `reverse_agent/project_gate.py`；
- v4 allowlist 中实际修改的 Gate/state tests；
- 当前本地 `state_manifest.json`、`current_context_packet.json` 和 Gate/report evidence；
- 以下 21 个 P0 文件：

```text
docs/architecture/architecture-spine-v2.md
docs/architecture/trust-model.md
docs/architecture/data-contracts.md
docs/architecture/storage-and-artifact-ownership.md
docs/architecture/sandbox-and-execution-boundary.md
docs/architecture/migration-and-legacy-exit.md
docs/architecture/governance-cost-model.md
docs/adr/ADR-001-modular-monolith.md
docs/adr/ADR-002-separate-development-and-analysis-workflows.md
docs/adr/ADR-003-separate-trust-bounded-contexts.md
docs/adr/ADR-004-unique-source-of-truth.md
docs/adr/ADR-005-storage-ownership.md
docs/adr/ADR-006-evidence-and-claim-versioning.md
docs/adr/ADR-007-langgraph-workflow-ownership.md
docs/adr/ADR-008-sandbox-worker-boundary.md
docs/adr/ADR-009-telemetry-is-not-analysis-evidence.md
docs/adr/ADR-010-legacy-control-plane-exit.md
docs/roadmap/architecture_constitution_and_migration_baseline_v1.md
docs/roadmap/architecture_constitution_implementation_plan_v1.md
docs/roadmap/p0_architecture_constitution_execution_plan_v1.md
docs/roadmap/long-term-implementation-plan-v2.md
```

如继承成果无法与无关改动区分，立即停止并列出精确路径。

## 4. Do Not Do

不得：

- 将 Issue #15 或 PR 评论作为运行时执行权威；Agent 只读取本 `decision_packet.md` 和 compiler 锁定后的 Command Plan；
- amend、reset、重写或删除 v1-v4 Decision 历史；
- 人工覆盖 `full` Profile，或手工编辑、删除、重排 compiler-generated Command Plan；
- 重新实现已在 v4 完成的代码，除非 v5 重新验证暴露同一范围内的真实缺陷；
- 修改 `reverse_agent/project_gate.py` 之外的生产源码；
- 修改 allowlist 之外的测试；
- 修改 `.github/workflows/**`、`pyproject.toml`、`setup.py`、`requirements*.txt`、`.codex-skills/**` 或任何 packaging；
- 修改、合并或标记 ready PR #9；
- 实现 BMAD、LangGraph、EvidenceUnit、Claim、数据库、CAS、Sandbox、Provider、Web 或 AgentRunner；
- 执行未知二进制、样本或调用逆向工具；
- 直接 push main、merge、rebase、squash、force-push、tag 或 release；
- 使用 `git add -A` 或 `git add .`；
- 通过 skip、xfail、删除断言、弱化 Gate、伪造报告或忽略真实失败获得通过。

## 5. Files To Inspect

执行前和每个 Gate 阶段至少检查：

- `project_state/decision_packet.md`；
- `project_state/gates/gate_profile_plan.json`；
- `project_state/gates/command_plan.json`；
- `project_state/gates/startup_snapshot.json`；
- `project_state/gates/preflight_result.json`；
- `project_state/state_manifest.json`；
- `project_state/context/current_context_packet.json`；
- `project_state/pytest_result.txt`；
- `project_state/codex_execution_report.md`；
- `project_state/execution_report.md`；
- `reverse_agent/project_gate.py`；
- v4 allowlist 中实际修改的测试；
- 21 个 P0 文件；
- `git status --short`、`git diff --check`、`git diff --name-only`；
- PR #11 和冻结 PR #9 的精确远端状态。

`reverse_agent/project_state.py` 只读。不得扫描完整 `solve_reports/` 或执行样本。

## 6. Required Audit

最终报告必须逐项使用 `Question ID / Status / Answer / Evidence / Limitations` 回答：

1. 当前 Decision、Round、branch 和 activation base 是否准确？
2. v4 是否保留且标记为 `BLOCKED_IMMUTABLE_PROFILE_CONTRACT_MISMATCH`？
3. 本 v5 Decision activation commit 是否只修改 `project_state/decision_packet.md`？
4. PR #9 是否保持 Draft、open、unmerged 且 exact head 未变？
5. 所有 v4 本地成果是否在执行前完成路径、分类和 SHA-256 盘点？
6. 是否不存在 reset、clean、discard、覆盖、重新生成或静默遗漏继承成果？
7. automatic Gate Profile 是否为 `full` 且没有 override？
8. Command Plan 是否由当前 compiler 生成并锁定，没有手工修改？
9. startup snapshot 和 preflight 是否在 substantive execution 前通过？
10. 实际修改是否严格限制在允许源码、测试、P0 文档及当前轮状态证据？
11. startup evidence、current-round artifact isolation、manifest/context freshness 是否具备回归测试？
12. execution-log、report-summary 和 final evidence 是否重复生成后保持语义幂等？
13. 不适用于当前轮的历史检查是否被明确判定为 NOT_APPLICABLE，而不是伪造或删除？
14. Required Audit 答案是否与问题 identity、顺序和语义一一对应？
15. focused regressions 是否零失败？
16. compiler-authorized full pytest 是否零失败？
17. `doctor` 与 `lint-report` 是否完成且无未解释阻塞？
18. `run-round` 是否仅在 Command Plan 授权时执行并保持 bounded？
19. `final-check` 是否在 closeout 前通过？
20. compiler-required `run-closeout` / `close-round` 是否成功完成？
21. round manifest、archived report、archived pytest_result 和 post-closeout evidence 是否当前且相互一致？
22. closeout 后重新生成的 execution-log、report-summary 和 final-check 是否通过且稳定？
23. `git diff --check` 是否通过，最终 staged paths 是否全部在 allowlist 内？
24. 21 个 P0 文档是否全部提交到 PR #11？
25. 远端 package-install 失败是否如实记录为 P1 前基线债务，而未宣称远端检查通过？
26. 是否没有 merge、mark-ready、workflow、packaging、PR #9 或 main mutation？

每项状态只能是 `PASS`、`FAIL`、`BLOCKED` 或 `NOT_APPLICABLE`，不得使用 TODO、TBD、PENDING 或推测性答案。

## 7. Implementation Scope and Execution Order

本轮优先复核并重用 v4 已完成实现，不得无理由重新修改。执行顺序：

```text
verify PR #11 and PR #9 exact heads
→ inventory and hash inherited v4 WIP
→ confirm v5 Decision activation commit is present locally
→ automatic full Gate Profile without override
→ compiler-generate and digest-lock Command Plan
→ independently generate startup snapshot
→ preflight
→ inspect inherited diff and map every path to the allowlist
→ run focused regressions generated or required by the plan
→ run complete compiler-authorized full pytest
→ doctor and lint-report
→ refresh v5 state_manifest and current_context_packet
→ regenerate current-round Gate and report evidence
→ run bounded run-round only if generated
→ execution-log
→ report-summary
→ final-check
→ compiler-authorized run-closeout / close-round
→ regenerate post-closeout execution-log / report-summary / final-check as required
→ repeat consistency generation to prove semantic idempotence
→ git diff --check and explicit allowlist review
→ explicitly stage authorized paths only
→ commit final source/test/document/evidence result
→ push once to existing PR #11
→ publish a short status notification containing the exact final head and validation facts
→ stop branch mutation for independent audit
```

具体 command kinds 和命令文本只能来自当前锁定的 Command Plan，不由本 Decision 正文另行覆盖。

## 8. Tests and Evidence

实际执行权威为 compiler-generated full Command Plan。至少必须证明：

- startup evidence 独立有效，缺失或乱序仍会失败；
- 历史 artifact 不污染当前 v5 验收；
- stale manifest/context 会失败，当前 v5 freshness 会通过；
- execution-log/report-summary/final-check 的重复生成语义稳定；
- Required Audit 结构化答案正确对齐；
- 真正缺失必需证据仍会失败，没有降低 Gate；
- full pytest 零失败；
- closeout 和 close-round 成功；
- post-closeout 当前轮证据完整一致；
- `git diff --check` 通过；
- 最终 commit 只包含授权路径。

`1544 passed` 只能作为 v4 历史本地证据。v5 不要求固定通过数量，必须报告实际结果和零失败状态。

## 9. Acceptance Criteria

本轮只有在以下条件全部满足时才能标记：

```text
P0_FULL_PROFILE_CONVERGENCE_AND_ARCHITECTURE_CONSTITUTION_ACCEPTED
```

- v4 保留为 `BLOCKED_IMMUTABLE_PROFILE_CONTRACT_MISMATCH`；
- v5 Decision activation commit 先于所有 v5 evidence regeneration；
- automatic Profile 为 `full`，没有 override；
- inherited v4 implementation 和 21 个 P0 文件被完整保留并重新验证；
- full tests 零失败；
- final-check、compiler-required closeout 和 close-round 成功；
- post-closeout artifacts 绑定当前 v5 Decision/Round/Report 并保持一致；
- 只提交允许路径；
- 最终成果推送到现有 Draft PR #11；
- PR #9 exact head 保持不变；
- 远端 packaging 失败被如实记录；
- 没有 merge 或 mark-ready。

## 10. Stop Conditions

遇到以下任一情况立即停止，不扩大范围：

- v5 激活前 PR #11 head 不是 `ce6562cf18efd46e40b037b55c17368c575da82b`；
- PR #9 head 不等于 `43418818af61d9be3208d2444fd6ce5120f73fab`；
- 本地 v4 WIP 无法与无关用户改动区分；
- automatic Profile 不是 `full`；
- Command Plan 要求未授权路径或动作；
- 完成任务需要修改 `reverse_agent/project_gate.py` 之外的生产源码；
- tests 出现新的无关失败；
- 需要 workflow、packaging、dependency 或 Skill 修改；
- closeout 后 evidence 无法在允许范围内收敛；
- 有人提议修改或合并 PR #9、直接 push main、重写历史或发布版本。

## 11. Publication Boundary

本 Decision 已获用户明确授权：

- v5 Decision 作为单文件 activation commit 推送到 `agent/architecture-constitution-plan-v1`；
- 在全部本地验收通过后，显式暂存允许的 source、test、document 和 current-round evidence；
- 创建一个最终成果 commit，并向现有 PR #11 分支推送一次；
- 更新 GitHub 人类可读状态摘要。

不得 merge、mark ready、rebase、squash、force-push、tag、release、直接 push main 或修改 PR #9。

## 12. Next Authorized Boundary

P0 独立审计接受后停止。下一轮必须是单独批准的 Integration Decision：

```text
P1: PR #9 Exact-head Integration and Architecture Spine Freeze
```
