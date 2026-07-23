```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260723_p0_evidence_derived_audit_and_command_coverage_rework_v8",
  "round_id": "round_20260723_p0_evidence_derived_audit_and_command_coverage_rework_v8",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260723_p0_exact_scope_inherited_baseline_and_publication_v7",
  "follows_last_round_id": "round_20260723_p0_exact_scope_inherited_baseline_and_publication_v7",
  "previous_audit_outcome": "REWORK_REQUIRED_EVIDENCE_PROJECTION_AND_COMMAND_COVERAGE",
  "workstream_id": "p0-evidence-derived-audit-and-command-coverage-rework-v8",
  "source_issue": 16,
  "source_pull_request": 11,
  "required_branch": "agent/architecture-constitution-plan-v1",
  "activation_base_sha": "b5ae4399e7f32df5ff16e6231e827d7c9458c722",
  "starting_remote_head": "b5ae4399e7f32df5ff16e6231e827d7c9458c722",
  "frozen_pr9_head": "43418818af61d9be3208d2444fd6ce5120f73fab",
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
  "unknown_binary_execution_allowed": false,
  "tool_provider_execution_allowed": false,
  "pr9_branch_mutation_allowed": false,
  "pr9_merge_allowed": false,
  "evidence_derived_required_audit_required": true,
  "required_kind_command_plan_completeness_required": true,
  "lifecycle_chronology_required": true,
  "run_round_result_pass_required": true,
  "doctor_command_block_required": true,
  "lint_report_command_block_required": true,
  "remote_observation_required_for_remote_pass": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py"
  ],
  "allowed_project_state_files": [
    "project_state/decision_packet.md",
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260723_p0_evidence_derived_audit_and_command_coverage_rework_v8/*"
  ],
  "read_only_reference_files": [
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
    "docs/roadmap/long-term-implementation-plan-v2.md",
    "project_state/rounds/round_20260723_p0_exact_scope_inherited_baseline_and_publication_v7/**",
    "reverse_agent/project_state.py",
    ".github/workflows/**",
    "project_state/task_packet.json",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json"
  ],
  "forbidden_mutated_paths": [
    "docs/architecture/*",
    "docs/architecture/**",
    "docs/adr/*",
    "docs/adr/**",
    "docs/roadmap/*",
    "docs/roadmap/**",
    "project_state/rounds/round_20260723_p0_exact_scope_inherited_baseline_and_publication_v7/*",
    "project_state/rounds/round_20260723_p0_exact_scope_inherited_baseline_and_publication_v7/**",
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
    "applies_to": "the local v8 Decision activation commit and the later compiler-validated v8 source/test/evidence commit on PR #11",
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

修复 v7 独立审计确认的三个治理缺陷：Required Audit 的静态全 PASS 投影、full Profile 必需命令种类缺失，以及 execution-log 生命周期顺序错误。保持 21 个 P0 文档与 v7 archive 完全只读，生成新的 v8 当前轮证据并发布到现有 Draft PR #11。

## 2. Current Evidence

- PR #11 activation base 必须为 `b5ae4399e7f32df5ff16e6231e827d7c9458c722`。
- PR #9 必须保持 Draft/open/unmerged，exact head 为 `43418818af61d9be3208d2444fd6ce5120f73fab`。
- v7 的 bounded pytest 为 1547 passed，但独立审计判定 `REWORK_REQUIRED`。
- v7 `run_round_result.json` 为 FAILED，却被静态 Required Audit 标为 PASS。
- v7 full Gate Profile 要求 `run-round`、`doctor`、`lint-report`，但 Command Plan 和 transcript 未覆盖。
- v7 execution-log 把 run-closeout 排在 preflight/pytest 前。
- 远端 workflow 因缺少 packaging baseline 在 `Install package` 失败；本轮不得修 packaging 或 workflow。
- 用户已明确授权 Issue #16 生成本 Decision 并执行。

## 3. Do Not Do

不得修改 P0 文档、v7 archive、workflow、packaging、dependency、Skill、PR #9、main 或无关源码；不得执行未知二进制或逆向工具；不得 merge、mark-ready、rebase、squash、force-push、tag 或 release；不得使用 skip、xfail、删除断言、弱化 Gate 或伪造证据获得通过。

## 4. Files To Inspect

- `project_state/decision_packet.md`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `git status --short`
- PR #11 与 PR #9 exact-head 元数据

## 5. Required Audit

最终报告逐项使用 `Question ID / Status / Answer / Evidence / Limitations` 回答。每项状态必须从当前机器可读证据计算，只能为 `PASS`、`FAIL`、`BLOCKED` 或 `NOT_APPLICABLE`：

1. 当前 Decision、Round、branch 与 activation base 是否准确？
2. v7 是否保留为 `REWORK_REQUIRED_EVIDENCE_PROJECTION_AND_COMMAND_COVERAGE` 且 archive 未修改？
3. automatic Gate Profile 是否为 `full` 且无 override？
4. Command Plan 是否覆盖 full Profile 的全部 required command kinds？
5. startup snapshot 与 preflight 是否在 substantive execution 前通过？
6. Required Audit 是否由当前证据计算，缺失或失败证据能否阻止 PASS？
7. doctor 与 lint-report 是否有显式成功 command block？
8. bounded run-round 是否当前且 `gate_status=PASSED`、`run_status=PASSED`？
9. lifecycle chronology 是否为 preflight → pytest/doctor/lint-report/run-round → pre-closeout final-check → run-closeout → close-round？
10. compiler-authorized pytest 是否零失败？
11. pre-closeout final-check、run-closeout 与 close-round 是否成功？
12. v8 round manifest、archive、manifest 与 context 是否当前且一致？
13. P0 21 个文档和 v7 archive 是否保持只读且内容未变？
14. 实际修改和 staged paths 是否全部在 v8 allowlist？
15. `git diff --check` 是否通过？
16. PR #9 exact head 是否保持不变？
17. 远端 PR/CI 结论是否来自不可变观察证据；没有证据时是否避免 PASS？
18. 是否没有 workflow、packaging、dependency、PR #9 或 main mutation？
19. 是否没有 merge、mark-ready、rebase、squash、force-push、tag 或 release？
20. v8 最终 commit 是否推送到现有 Draft PR #11，且推送后停止分支变更？

## 6. Implementation Scope

Allowed:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `project_state/decision_packet.md`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/gates/*.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/rounds/round_20260723_p0_evidence_derived_audit_and_command_coverage_rework_v8/*`

Read-only:

- `docs/architecture/**`
- `docs/adr/**`
- `docs/roadmap/**`
- `project_state/rounds/round_20260723_p0_exact_scope_inherited_baseline_and_publication_v7/**`
- `.github/workflows/**`
- `reverse_agent/project_state.py`
- `.codex-skills/**`

Execution order:

```text
verify PR #11 and PR #9 exact heads
→ commit v8 Decision locally
→ decision-lint
→ automatic full Gate Profile without override
→ compiler-generate and digest-lock Command Plan
→ independently generate startup snapshot
→ preflight
→ implement evidence-derived audit, required-kind completeness and chronology
→ focused negative and positive regressions
→ compiler-authorized full pytest
→ doctor
→ lint-report
→ bounded run-round
→ pre-closeout final-check
→ run-closeout
→ close-round
→ post-closeout execution-log/report-summary/final-check
→ repeat consistency generation
→ git diff --check and explicit allowlist review
→ explicitly stage only authorized paths
→ commit final source/test/evidence result
→ push the local activation and final commits once to existing PR #11
→ publish truthful status notification
→ stop branch mutation
```

具体 command kinds 与命令文本只能来自锁定后的 Command Plan。

## 7. Tests

必须证明：

- missing/failed `run_round_result`、missing doctor output、changed PR head 或 missing archive 不能渲染 PASS；
- full Profile 的每个 `required_command_kind` 都有具体 command，否则 Command Plan 编译失败；
- `run-round`、`doctor`、`lint-report` 命令可执行且出现在 transcript；
- preflight、pytest、doctor、lint-report、run-round 和 pre-closeout final-check 均早于 run-closeout；
- close-round 只在成功 run-closeout 后出现；
- 远端状态没有不可变观察证据时不渲染 PASS；
- exact compiler-authorized pytest 零失败；
- final-check、run-closeout、close-round 和 post-closeout final-check 成功；
- v7 archive 与 21 个 P0 文档无改动；
- `git diff --check` 和路径 allowlist 审查通过。

不要求固定 pytest 通过数量。

## 8. Acceptance Criteria

仅在全部验证与收口通过后标记：

```text
P0_EVIDENCE_DERIVED_AUDIT_COMMAND_COVERAGE_AND_ARCHITECTURE_CONSTITUTION_ACCEPTED
```

## 9. Stop Conditions

以下任一情况立即停止且不扩大范围：

- v8 activation 前 PR #11 head 不等于 `b5ae4399e7f32df5ff16e6231e827d7c9458c722`；
- PR #9 head 不等于 `43418818af61d9be3208d2444fd6ce5120f73fab`；
- compiler 要求 workflow、packaging 或未授权文件；
- 修复必须超出 `reverse_agent/project_gate.py` 和 `tests/test_project_gate.py`；
- v7 archive 或 P0 文档需要改写；
- 无关测试失败；
- 无法在不弱化 Gate 的前提下收敛证据。

## 10. Publication Boundary

本 Decision 已获用户明确授权：本地创建单文件 activation commit；验收通过后创建最终实现 commit；仅向 `agent/architecture-constitution-plan-v1` 推送一次包含两项提交的 fast-forward 更新；保持 PR #11 Draft/open，不 merge 或 mark-ready。

## 11. Next Authorized Boundary

P0 独立审计接受后停止。下一轮仍为单独批准的：

```text
P1: PR #9 Exact-head Integration and Architecture Spine Freeze
```
