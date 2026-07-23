```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260723_p0_exact_scope_inherited_baseline_and_publication_v7",
  "round_id": "round_20260723_p0_exact_scope_inherited_baseline_and_publication_v7",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260723_p0_exact_tests_contract_and_publication_v6",
  "follows_last_round_id": "round_20260723_p0_exact_tests_contract_and_publication_v6",
  "previous_audit_outcome": "BLOCKED_PREFLIGHT_SCOPE_AND_INHERITED_BASELINE_PARSER_MISMATCH",
  "workstream_id": "p0-exact-scope-inherited-baseline-and-publication-v7",
  "source_issue": 15,
  "source_pull_request": 11,
  "required_branch": "agent/architecture-constitution-plan-v1",
  "activation_base_sha": "e2424b3423436304c943a015e9880e32a03f5752",
  "starting_remote_head": "e2424b3423436304c943a015e9880e32a03f5752",
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
    "project_state/rounds/round_20260723_p0_exact_scope_inherited_baseline_and_publication_v7/*"
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
    "applies_to": "the v7 Decision activation commit and the later compiler-validated P0 source/test/document/evidence publication commit on PR #11",
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

以新的不可变 v7 Decision 取代因 preflight 解析合同不完整而阻塞的 v6，在不修改 parser/compiler、不扩大实现范围的前提下，使用当前 Gate 可精确解析的 `Implementation Scope`、`Allowed:` 路径清单和 `Allowed Inherited Dirty Baseline Files` 章节，重新生成 Command Plan、startup、preflight、full-profile 验证与 closeout，并发布既有 P0 成果到 PR #11。

本轮不是新功能实现轮。v4-v6 已完成或保留的源码、测试、文档和证据修改必须作为继承 WIP 继续保留；不得 reset、clean、discard、覆盖或从零重新生成。

## 2. Current Evidence

- v6 Decision activation commit 为 `e2424b3423436304c943a015e9880e32a03f5752`，必须保留在 Git 历史，状态为 `BLOCKED_PREFLIGHT_SCOPE_AND_INHERITED_BASELINE_PARSER_MISMATCH`。
- v6 的 `decision-lint` 已通过，automatic Profile 已正确推导为 `full`，Command Plan 和 startup snapshot 已生成；preflight 因两个治理文本解析问题失败，未运行后续测试、未提交最终成果、未推送最终成果。
- 第一项失败：v6 使用 `Implementation Scope and Execution Order`，没有提供 compiler 可独立识别的精确 `Implementation Scope` 和直接 `Allowed:` 路径清单。
- 第二项失败：`project_state/state_manifest.json` 与 `project_state/context/current_context_packet.json` 虽在 JSON allowlist 中，但没有出现在专用 `Allowed Inherited Dirty Baseline Files` 章节，导致 inherited-baseline 校验失败。
- 本 v7 只修复上述治理合同表达，不授权修改 parser/compiler 来绕过 preflight。
- 当前执行工作树必须是保存全部本地 WIP 的既有 `F:\reverse-agent-p0`。
- PR #9 必须保持 Draft、open、unmerged，并冻结在 exact head `43418818af61d9be3208d2444fd6ce5120f73fab`。
- PR #11 远端 workflow 在 `Install package` 阶段失败属于 P1 前 packaging baseline 债务；本轮不得复制 packaging 或修改 workflow。

## 3. Do Not Do

不得：

- 将 Issue 或 PR 评论作为执行权威；只读取本 Decision 和 compiler 锁定后的 Command Plan；
- amend、reset、重写或删除 v1-v6 Decision 历史；
- 修改 parser/compiler 以绕过本轮 preflight；
- 人工覆盖 `full` Profile；
- 手工编辑、删除或重排 compiler-generated Command Plan；
- reset、clean、discard、覆盖、重新生成或静默遗漏继承 WIP；
- 修改 `reverse_agent/project_gate.py` 之外的生产源码；
- 修改 allowlist 之外的测试、文档或 project-state 文件；
- 修改 workflow、packaging、dependency、Skill、PR #9 或 main；
- 执行未知二进制、样本或逆向工具；
- merge、mark ready、rebase、squash、force-push、tag 或 release；
- 使用 `git add -A` 或 `git add .`；
- 通过 skip、xfail、删除断言、弱化 Gate、伪造报告或忽略真实失败获得通过。

## 4. Files To Inspect

执行前和每个 Gate 阶段至少检查：

- `project_state/decision_packet.md`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/gates/preflight_result.json`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `reverse_agent/project_gate.py`
- 实际修改的 allowlisted tests
- 21 个 P0 文档
- `git status --short`
- `git diff --check`
- `git diff --name-only`
- PR #11 和冻结 PR #9 的精确远端状态

`reverse_agent/project_state.py` 只读。不得扫描完整 `solve_reports/`，不得执行样本。

## 5. Required Audit

最终报告必须逐项使用 `Question ID / Status / Answer / Evidence / Limitations` 回答：

1. 当前 Decision、Round、branch 与 activation base 是否准确？
2. v6 是否保留且标记为 `BLOCKED_PREFLIGHT_SCOPE_AND_INHERITED_BASELINE_PARSER_MISMATCH`？
3. v7 activation commit 是否只修改 `project_state/decision_packet.md`？
4. PR #9 是否保持 Draft、open、unmerged 且 exact head 未变？
5. 所有继承 WIP 是否在 v7 执行前完成路径、分类和 SHA-256 盘点？
6. compiler 是否识别精确 `Implementation Scope` 和 `Allowed:` 路径清单？
7. inherited-baseline parser 是否识别专用 `Allowed Inherited Dirty Baseline Files` 章节？
8. automatic Gate Profile 是否为 `full` 且没有 override？
9. Command Plan 是否由 compiler 生成并锁定，没有手工修改？
10. startup snapshot 与 preflight 是否在 substantive execution 前通过？
11. 实际修改是否严格限制在 `Allowed:` 路径清单？
12. focused regressions 与 compiler-authorized full pytest 是否零失败？
13. `doctor`、`lint-report`、bounded `run-round` 与 pre-closeout `final-check` 是否通过？
14. compiler-required `run-closeout` / `close-round` 是否成功？
15. round manifest、archived report、archived pytest_result 与 post-closeout evidence 是否当前且一致？
16. execution-log、report-summary 与 final-check 重复生成是否语义稳定？
17. `git diff --check` 是否通过，staged paths 是否全部在 allowlist？
18. 21 个 P0 文档是否全部提交并推送到 PR #11？
19. 远端 packaging 失败是否如实记录，而未宣称远端检查通过？
20. 是否没有 merge、mark-ready、workflow、packaging、PR #9 或 main mutation？

状态只能为 `PASS`、`FAIL`、`BLOCKED` 或 `NOT_APPLICABLE`。

## 6. Implementation Scope

Allowed:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`
- `tests/test_project_context.py`
- `tests/test_project_state_manifest.py`
- `docs/architecture/architecture-spine-v2.md`
- `docs/architecture/trust-model.md`
- `docs/architecture/data-contracts.md`
- `docs/architecture/storage-and-artifact-ownership.md`
- `docs/architecture/sandbox-and-execution-boundary.md`
- `docs/architecture/migration-and-legacy-exit.md`
- `docs/architecture/governance-cost-model.md`
- `docs/adr/ADR-001-modular-monolith.md`
- `docs/adr/ADR-002-separate-development-and-analysis-workflows.md`
- `docs/adr/ADR-003-separate-trust-bounded-contexts.md`
- `docs/adr/ADR-004-unique-source-of-truth.md`
- `docs/adr/ADR-005-storage-ownership.md`
- `docs/adr/ADR-006-evidence-and-claim-versioning.md`
- `docs/adr/ADR-007-langgraph-workflow-ownership.md`
- `docs/adr/ADR-008-sandbox-worker-boundary.md`
- `docs/adr/ADR-009-telemetry-is-not-analysis-evidence.md`
- `docs/adr/ADR-010-legacy-control-plane-exit.md`
- `docs/roadmap/architecture_constitution_and_migration_baseline_v1.md`
- `docs/roadmap/architecture_constitution_implementation_plan_v1.md`
- `docs/roadmap/p0_architecture_constitution_execution_plan_v1.md`
- `docs/roadmap/long-term-implementation-plan-v2.md`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/gates/*.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/rounds/round_20260723_p0_exact_scope_inherited_baseline_and_publication_v7/*`

Read-only:

- `reverse_agent/project_state.py`
- `.codex-skills/registry.json`
- `.codex-skills/reverse-agent-iteration/SKILL.md`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`

Execution order:

```text
verify PR #11 and PR #9 exact heads
→ inventory and hash inherited v4-v6 WIP
→ confirm v7 Decision activation commit is present locally
→ decision-lint
→ automatic full Gate Profile without override
→ compiler-generate and digest-lock Command Plan
→ independently generate startup snapshot
→ preflight
→ inspect inherited diff and map every path to Allowed
→ run focused regressions required by the plan
→ run complete compiler-authorized full pytest
→ doctor and lint-report
→ refresh v7 state_manifest and current_context_packet
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
→ publish a short human-readable status notification
→ stop branch mutation for independent audit
```

具体 command kinds 和命令文本只能来自锁定后的 Command Plan。

## Allowed Inherited Dirty Baseline Files

以下路径在 v7 激活前已经存在于保存本地成果的工作树中，并由 startup snapshot / inherited-WIP inventory 证明。允许它们作为继承脏基线继续存在，但不得据此扩大最终提交范围：

- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`

本节只解决 preflight 对上述两个明确继承 project-state 文件的识别。其他 source、test、document 或 generated artifact 仍必须由 startup snapshot、当前 diff 和 `Implementation Scope` 共同校验；不得把新产生或未盘点的文件追认为 inherited dirty baseline。

## 7. Tests

本节标题必须保持精确的 `Tests`。实际执行权威为 compiler-generated full Command Plan。

至少必须证明：

- compiler 成功解析 `Implementation Scope` 的 `Allowed:` 路径；
- preflight 成功识别两个明确列出的 inherited project-state baseline 文件；
- startup evidence 独立有效，缺失或乱序仍失败；
- 历史 artifact 不污染当前 v7 验收；
- stale manifest/context 会失败，当前 v7 freshness 会通过；
- execution-log、report-summary 与 final-check 重复生成后语义稳定；
- Required Audit 结构化答案正确对齐；
- 真正缺失必需证据仍失败，没有降低 Gate；
- compiler-authorized full pytest 零失败；
- compiler-required closeout 与 close-round 成功；
- post-closeout 当前轮证据完整一致；
- `git diff --check` 通过；
- 最终 commit 只包含授权路径。

v7 不要求固定通过数量，只要求实际命令零失败。

## 8. Acceptance Criteria

仅在以下条件全部满足时标记：

```text
P0_EXACT_SCOPE_INHERITED_BASELINE_FULL_PROFILE_AND_ARCHITECTURE_CONSTITUTION_ACCEPTED
```

- v6 保留为 `BLOCKED_PREFLIGHT_SCOPE_AND_INHERITED_BASELINE_PARSER_MISMATCH`；
- v7 activation commit 先于所有 v7 substantive execution；
- compiler 成功解析精确 `Implementation Scope`、`Allowed:` 与 `Tests`；
- inherited-baseline parser 成功识别专用 allowlist；
- automatic Profile 为 `full`，没有 override；
- inherited implementation 与 21 个 P0 文件完整保留并重新验证；
- full tests 零失败；
- final-check、closeout 与 close-round 成功；
- post-closeout artifacts 绑定当前 v7 Decision/Round/Report；
- 只提交允许路径；
- 最终成果推送到现有 Draft PR #11；
- PR #9 exact head 保持不变；
- 远端 packaging 失败如实记录；
- 没有 merge 或 mark-ready。

## 9. Stop Conditions

遇到以下任一情况立即停止：

- v7 激活前 PR #11 head 不是 `e2424b3423436304c943a015e9880e32a03f5752`；
- PR #9 head 不等于 `43418818af61d9be3208d2444fd6ce5120f73fab`；
- 本地 WIP 无法与无关用户改动区分；
- decision-lint 失败；
- compiler 仍不能识别精确 `Implementation Scope`、`Allowed:` 或 `Tests`；
- preflight 仍不能识别两个明确列出的 inherited project-state baseline 文件；
- automatic Profile 不是 `full`；
- Command Plan 要求未授权路径或动作；
- 完成任务需要修改 parser/compiler 或 `reverse_agent/project_gate.py` 之外的生产源码；
- tests 出现新的无关失败；
- 需要 workflow、packaging、dependency 或 Skill 修改；
- closeout 后 evidence 无法在允许范围内收敛；
- 有人提议修改或合并 PR #9、直接 push main、重写历史或发布版本。

## 10. Publication Boundary

本 Decision 已获用户明确授权：

- v7 Decision 作为单文件 activation commit 推送到 `agent/architecture-constitution-plan-v1`；
- 全部本地验收通过后，显式暂存允许的 source、test、document 与 current-round evidence；
- 创建一个最终成果 commit，并向现有 PR #11 分支推送一次；
- 更新 GitHub 人类可读状态摘要。

不得 merge、mark ready、rebase、squash、force-push、tag、release、直接 push main 或修改 PR #9。

## 11. Next Authorized Boundary

P0 独立审计接受后停止。下一轮必须是单独批准的 Integration Decision：

```text
P1: PR #9 Exact-head Integration and Architecture Spine Freeze
```
