```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260723_p0_exact_tests_contract_and_publication_v6",
  "round_id": "round_20260723_p0_exact_tests_contract_and_publication_v6",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260723_p0_full_profile_convergence_and_publication_v5",
  "follows_last_round_id": "round_20260723_p0_full_profile_convergence_and_publication_v5",
  "previous_audit_outcome": "BLOCKED_PREPLAN_TESTS_SECTION_HEADING_MISMATCH",
  "workstream_id": "p0-exact-tests-contract-and-publication-v6",
  "source_issue": 15,
  "source_pull_request": 11,
  "required_branch": "agent/architecture-constitution-plan-v1",
  "activation_base_sha": "3d487e29e467b3a0eea325e3286afd63331b5367",
  "starting_remote_head": "3d487e29e467b3a0eea325e3286afd63331b5367",
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
    "project_state/rounds/round_20260723_p0_exact_tests_contract_and_publication_v6/*"
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
    "applies_to": "the v6 Decision activation commit and the later compiler-validated P0 source/test/document/evidence publication commit on PR #11",
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

以新的不可变 v6 Decision 取代因测试章节标题不符合现有 compiler 精确解析契约而被阻塞的 v5 Decision。v6 保持 v5 的 `full` Profile、源码/测试/文档范围和发布目标不变，只修正 pre-plan 解析契约，并接管、保留和重新绑定尚未提交的 v4/v5 本地成果。

本轮不是新的功能实现轮。只允许：

1. 将现有 source、test、document 和 evidence 修改盘点为 `inherited_authorized_wip_from_v4_v5`；
2. 在不扩大功能范围的前提下复核 `reverse_agent/project_gate.py` 的 legacy Gate convergence 修改；
3. 按 compiler 生成的 `full` Command Plan 重新运行测试、Gate、closeout 和 round archive；
4. 刷新当前 v6 Decision/Round/Report 绑定的 manifest、context、execution-log、report 和 final evidence；
5. 显式提交并推送 21 个 P0 文档和经验证的源码、测试及证据到现有 PR #11；
6. 推送后停止分支修改，等待独立审计。

## 2. Current Evidence

- v5 Decision activation commit 为 `3d487e29e467b3a0eea325e3286afd63331b5367`，必须保留在 Git 历史且不得 amend、reset 或重写。
- v5 的 `decision-lint` 通过，automatic Gate Profile 正确为 `full`。
- v5 的 Command Plan 编译在 substantive execution 前失败，唯一已知原因是 Decision 使用标题 `## 8. Tests and Evidence`，而现有 compiler 只接受精确标题 `## 8. Tests`。
- v5 没有授权在 Command Plan、startup 和 preflight 之前修改 compiler，因此 Agent 正确停止；v5 状态为 `BLOCKED_PREPLAN_TESTS_SECTION_HEADING_MISMATCH`。
- 当前 v6 使用精确章节标题 `## 8. Tests`，不要求或授权修改 parser/compiler 来绕过该问题。
- 本地 v4/v5 WIP 已被报告为完整保留，尚未提交或推送；不得通过 reset、clean、discard、新工作树或重新生成丢失。
- 历史本地技术证据 `1544 passed`、`run-round=PASSED`、`report-summary=0`、`final-check=0`、`git diff --check=0` 仅作为继承证据，必须在 v6 下重新绑定和验证。
- 当前目标分支为 `agent/architecture-constitution-plan-v1`，v6 activation base 为 `3d487e29e467b3a0eea325e3286afd63331b5367`。
- PR #9 必须保持 Draft、open、unmerged，并冻结在 exact head `43418818af61d9be3208d2444fd6ce5120f73fab`。
- PR #11 远端检查在 `Install package` 阶段失败属于 P1 前 packaging baseline 债务；v6 不得修改 packaging 或 workflow。

## 3. Inherited Authorized WIP

在任何 substantive edit、cleanup、stash、checkout、重新生成或测试执行前，必须：

1. 记录当前 HEAD、PR #11 remote head、PR #9 exact head 和 `git status --short`；
2. 列出全部未提交路径并计算 SHA-256；
3. 区分 v4/v5 授权成果与无关用户改动；
4. 将合法成果标记为 `inherited_authorized_wip_from_v4_v5`；
5. 将路径和摘要写入 v6 startup/baseline evidence；
6. 不得 reset、clean、discard、覆盖、静默遗漏或从零重写继承成果。

预期范围包括 `reverse_agent/project_gate.py`、实际修改的 allowlisted tests、当前状态证据，以及 decision contract 中列出的 21 个 P0 文档。无法区分时立即停止并报告精确路径。

## 4. Do Not Do

不得：

- 将 Issue 或 PR 评论作为运行时执行权威；只读取本 Decision 和锁定后的 Command Plan；
- amend、reset、重写或删除 v1-v5 Decision 历史；
- 人工覆盖 `full` Profile；
- 手工编辑、删除或重排 compiler-generated Command Plan；
- 为修复标题问题修改 compiler/parser；
- 修改 `reverse_agent/project_gate.py` 之外的生产源码；
- 修改 allowlist 之外的测试；
- 修改 workflow、Skill、dependency、packaging 或 PR #9；
- 重新实现已完成的 v4 修改，除非 v6 验证暴露同一范围内的真实缺陷；
- 执行未知二进制、样本或逆向工具；
- push main、merge、mark ready、rebase、squash、force-push、tag 或 release；
- 使用 `git add -A` 或 `git add .`；
- skip、xfail、删除断言、弱化 Gate、伪造证据或忽略真实失败。

## 5. Files To Inspect

至少检查：

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
- 实际修改的 allowlisted tests；
- 21 个 P0 文档；
- Git diff/status 和 PR #9、PR #11 精确远端状态。

`reverse_agent/project_state.py` 只读。不得扫描完整 `solve_reports/` 或执行样本。

## 6. Required Audit

最终报告必须逐项使用 `Question ID / Status / Answer / Evidence / Limitations` 回答：

1. 当前 Decision、Round、branch 和 activation base 是否准确？
2. v5 是否保留且标记为 `BLOCKED_PREPLAN_TESTS_SECTION_HEADING_MISMATCH`？
3. v6 activation commit 是否只修改 `project_state/decision_packet.md`？
4. PR #9 是否保持 Draft、open、unmerged 且 exact head 未变？
5. 所有继承 WIP 是否在执行前完成路径、分类和 SHA-256 盘点？
6. automatic Gate Profile 是否为 `full` 且没有 override？
7. compiler 是否识别精确 `## 8. Tests` 章节并成功生成 Command Plan？
8. Command Plan 是否由 compiler 生成并锁定，没有手工修改？
9. startup snapshot 和 preflight 是否在 substantive execution 前通过？
10. 实际修改是否严格限制在 allowlist？
11. focused regressions 和 full pytest 是否零失败？
12. `doctor`、`lint-report`、bounded `run-round` 和 pre-closeout `final-check` 是否通过？
13. compiler-required `run-closeout` / `close-round` 是否成功？
14. round manifest、archived report、archived pytest_result 和 post-closeout evidence 是否当前且一致？
15. execution-log、report-summary 和 final-check 重复生成是否语义稳定？
16. `git diff --check` 是否通过，staged paths 是否全部在 allowlist？
17. 21 个 P0 文档是否全部提交并推送到 PR #11？
18. 远端 packaging 失败是否如实记录，而未宣称远端检查通过？
19. 是否没有 merge、mark-ready、workflow、packaging、PR #9 或 main mutation？

状态只能为 `PASS`、`FAIL`、`BLOCKED` 或 `NOT_APPLICABLE`。

## 7. Implementation Scope and Execution Order

执行顺序不可调整：

```text
verify PR #11 and PR #9 exact heads
→ inventory and hash inherited v4/v5 WIP
→ confirm v6 Decision activation commit is present locally
→ decision-lint
→ automatic full Gate Profile without override
→ compiler-generate and digest-lock Command Plan
→ independently generate startup snapshot
→ preflight
→ inspect inherited diff and map every path to allowlist
→ run focused regressions required by the plan
→ run complete compiler-authorized full pytest
→ doctor and lint-report
→ refresh v6 state_manifest and current_context_packet
→ regenerate current-round Gate and report evidence
→ run bounded run-round only if generated
→ execution-log
→ report-summary
→ final-check
→ compiler-authorized run-closeout / close-round
→ regenerate post-closeout execution-log / report-summary / final-check as required
→ repeat consistency generation to prove idempotence
→ git diff --check and explicit allowlist review
→ explicitly stage authorized paths only
→ commit final source/test/document/evidence result
→ push once to existing PR #11
→ publish a short human-readable status notification
→ stop branch mutation for independent audit
```

具体 command kinds 和命令文本只能来自锁定的 Command Plan。

## 8. Tests

本节标题必须保持精确的 `## 8. Tests`，不得改名、添加后缀或嵌套为其他标题。实际执行权威为 compiler-generated full Command Plan。

至少必须证明：

- startup evidence 独立有效，缺失或乱序仍会失败；
- 历史 artifact 不污染当前 v6 验收；
- stale manifest/context 会失败，当前 v6 freshness 会通过；
- execution-log、report-summary 和 final-check 重复生成后语义稳定；
- Required Audit 结构化答案正确对齐；
- 真正缺失必需证据仍会失败，没有降低 Gate；
- compiler-authorized full pytest 零失败；
- compiler-required closeout 和 close-round 成功；
- post-closeout 当前轮证据完整一致；
- `git diff --check` 通过；
- 最终 commit 只包含授权路径。

历史 `1544 passed` 不能替代 v6 当前结果。v6 不要求固定通过数量，只要求实际命令零失败。

## 9. Acceptance Criteria

仅在以下条件全部满足时标记：

```text
P0_EXACT_TESTS_CONTRACT_FULL_PROFILE_AND_ARCHITECTURE_CONSTITUTION_ACCEPTED
```

- v5 保留为 `BLOCKED_PREPLAN_TESTS_SECTION_HEADING_MISMATCH`；
- v6 activation commit 先于所有 v6 substantive execution；
- compiler 成功识别 `## 8. Tests`；
- automatic Profile 为 `full`，没有 override；
- inherited implementation 和 21 个 P0 文件完整保留并重新验证；
- full tests 零失败；
- final-check、closeout 和 close-round 成功；
- post-closeout artifacts 绑定当前 v6 Decision/Round/Report；
- 只提交允许路径；
- 最终成果推送到现有 Draft PR #11；
- PR #9 exact head 保持不变；
- 远端 packaging 失败如实记录；
- 没有 merge 或 mark-ready。

## 10. Stop Conditions

遇到以下任一情况立即停止：

- v6 激活前 PR #11 head 不是 `3d487e29e467b3a0eea325e3286afd63331b5367`；
- PR #9 head 不等于 `43418818af61d9be3208d2444fd6ce5120f73fab`；
- 本地 WIP 无法与无关用户改动区分；
- decision-lint 失败；
- compiler 仍不能识别精确 `## 8. Tests`；
- automatic Profile 不是 `full`；
- Command Plan 要求未授权路径或动作；
- 完成任务需要修改 parser/compiler 或 `reverse_agent/project_gate.py` 之外的生产源码；
- tests 出现新的无关失败；
- 需要 workflow、packaging、dependency 或 Skill 修改；
- closeout 后 evidence 无法在允许范围内收敛；
- 有人提议修改或合并 PR #9、直接 push main、重写历史或发布版本。

## 11. Publication Boundary

本 Decision 已获用户明确授权：

- v6 Decision 作为单文件 activation commit 推送到 `agent/architecture-constitution-plan-v1`；
- 全部本地验收通过后，显式暂存允许的 source、test、document 和 current-round evidence；
- 创建一个最终成果 commit，并向现有 PR #11 分支推送一次；
- 更新 GitHub 人类可读状态摘要。

不得 merge、mark ready、rebase、squash、force-push、tag、release、直接 push main 或修改 PR #9。

## 12. Next Authorized Boundary

P0 独立审计接受后停止。下一轮必须是单独批准的 Integration Decision：

```text
P1: PR #9 Exact-head Integration and Architecture Spine Freeze
```
