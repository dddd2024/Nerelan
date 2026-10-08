# Approved current-candidate publication and real acceptance

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue118_current_candidate_acceptance_r3_v1",
  "round_id": "round_20261008_issue118_current_candidate_acceptance_r3_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": []
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "ISSUE118_CURRENT_CANDIDATE_DRAFT_CI_NATIVE_RESTART_ACCEPTANCE",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 Owner via explicit chat approval 批准",
  "approval_basis": "Owner approved immutable proposal SHA256 ead6fb5e342fb717ee37bef8d5c4df02a7553bf78ea874f3d13679ee7bb7365f",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-delegated-native-recovery-r3-v1-20261007",
  "base_sha": "82c9b185a66561d17cf8a6857cd3add2d23215ca",
  "activation_base_sha": "82c9b185a66561d17cf8a6857cd3add2d23215ca",
  "starting_head": "8ff92498f46a329d0f2bedd6ee83f9f1b330baa6",
  "required_branch": "codex/issue118-current-candidate-acceptance-r3-20261008",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": true,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 5,
  "draft_pr_creation_limit": 2,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": true,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": true,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "# 待批准：当前候选的 Draft、CI、独立复审与真实前端验收\n\n状态：PROPOSAL_ONLY，不是执行授权。未激活、未推送、未启动浏览器或系统任务。\n\n## 精确候选与目标\n\n仓库：dddd2024/Nerelan。当前候选 8ff92498f46a329d0f2bedd6ee83f9f1b330baa6，本地全量2151通过、22跳过、4原有opt-in排除、1模拟崩溃线程警告；完整82c9..HEAD差异检查通过。\n明确接纳已提交候选作为只读起点，保留全部旧Decision/失败/额度/绝对截止时间。本方案是独立的新授权，不能重置或延长任何旧授权。\n集成分支：codex/issue118-delegated-native-recovery-r3-v1-20261007，必须仍等于 82c9b185a66561d17cf8a6857cd3add2d23215ca。新分支：codex/issue118-current-candidate-acceptance-r3-20261008，从当前候选8ff92498f46a329d0f2bedd6ee83f9f1b330baa6创建；承接已批准的既有历史，起始head为8ff92498f46a329d0f2bedd6ee83f9f1b330baa6，审查/PR基线为82c9b185a66561d17cf8a6857cd3add2d23215ca，merge-base必须为82c9b185a66561d17cf8a6857cd3add2d23215ca。本阶段明确允许这种已有候选承接，不伪造从集成基线重新实现。\n首先提交新的不可变 APPROVED Path-B Decision，声明 starting_head、activation parent、集成基线、history reuse、精确路径和候选源码清单，再运行现有 canonical plan/preflight。只有 PRE_EXECUTION_AUTHORIZED 才可推进；任何不可满足的Gate停止，不能改Gate。\n\n## 新窗口与累计额度\n\n批准后首次激活时固定一个新的4小时绝对窗口，起止时间一次写入后不可延长。旧2026-10-07窗口和2026-10-08两次本地修复截止保持原值。\n追加：Decision激活1；源码修复2；开发检查4；必需检查8（最多2次完整pytest，各<=2400秒，focused<=900秒，静态<=120秒）；源码提交3；精确非main push5；新Draft最多1个（创建尝试2次，失败后先去重）；描述更新4；独立只读审计1名。\n运行额度：新拥有的克隆1、受控栈启动2、浏览器启动2、原生观察4（每次<=180秒）、身份绑定清理2（每次<=120秒）、真实provider-free窗口激活1、Task1、任务重试0。冷重启必须沿用原数据库、Goal/Task/window/slot与原支出，绝不以新任务、新窗口或重置预算替代恢复。\n所有尝试开始即累加/fsync，旧记录不可改。只允许在同一不可变授权及剩余额度内修复列明范围的实际错误；强制检查失败阻止发布/运行，直到授权内修正并重新通过。不得自动创建后继Decision、扩大范围或重置计数。\n\n## 源码与证据范围\n\n原候选携带的精确产品路径及额外既有启动器路径见 frozen-source-manifest.json。可修复仅为其中路径上的候选验收/启动/窗口/历史恢复故障，最多2次；不允许增加测试排除、跳过、放宽断言或Git空白策略。原候选的全部源码blob与SHA已冻结，其他文件不可改变。\n新的 project_state/decision_packet.md 为唯一可提交的治理入口；既有五个 generated gate 文件可生成但不可提交。复用现有Gate、SQLite、receipt、Goal/Task、private transport和外部证据目录，不新增 tracked Gate/receipt/verifier 家族。\n允许适配原有外部prepare/runtime/native observer/probe/cleanup脚本到当前精确候选及新授权；这些适配不能替代产品源码修复，必须经过授权内静态检查并保留哈希/身份记录。\n\n## 发布与独立验收\n\n只可推送上述新非main分支，并创建对上述冻结集成分支的精确Draft及更新描述。快照绑定当前Decision/源码/head/base，不能把旧CI或旧审计改称新head结果。\n等待原始自然CI run/job；允许限量只读查询与获取其原始日志/JUnit，不允许 rerun/dispatch/no-op commit。检查来源和实际checkout/commit必须匹配。继承已通过且源码表面不变的本地检查须明确原head，不无理由重跑。\n允许1名独立只读Codex审计员审查原集成基线到当前精确head的完整源码范围、实际检查和必需条件；该审计员不得改代码或审批自己的实现。报告写既有外部证据，不写PR/Issue评论。新head必须重新绑定审计。\n保持Draft。无Ready、merge、main push、auto-merge、tag/release、部署或发布产品权限。\n\n## 真实运行验收\n\n只有当前精确head的必需本地/自然CI检查通过且独立审计接受源码后才能运行。\n新拥有目录仅F:/nrl-118-accept-20261008；明确空闲loopback端口18917(Task)、18918(Model control但live调用0)、18919(frontend)。复用现有依赖只读，隔离Vite缓存；不安装依赖、不修改全局配置、不触碰历史Task数据库或其他人的栈。\n固定Node路径E:/Program Files/nodejs/node.exe，启动前重新验证已知SHA58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f。Edge仅现安装路径C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe：启动前必须重新验证Microsoft有效签名并冻结当前版本/哈希；允许现安装Microsoft有效签名的自动更新导致版本变化，记录新指纹后继续，不安装或更换浏览器。其他可执行文件不能据此获权。\n真实新policy/window/activation-slot/host/database/Goal-idempotency/checker scope全部在新Decision里精确固定并由既有编译器验证；Owner批准只通过可信host映射成DELEGATED_CONTROLLER授权，不伪装个人GitHub验收，不靠renderer的local-owner/ACTIVATE/verified字段授权。\n仅固定 git_diff_check/validate_task：冻结frontend/src/components/sidebar.tsx和CHECK001，Task1、并发1、重试0、模型/Provider/GitHub写/发布预算0。这个Goal必须明确说明只检查差异，不能标记任意代码实现目标已完成。\n使用实际拥有的Edge/private broker观察小窗口→最大化→还原，依据实际native客户区与浏览器报告的inner/outer/viewport数据，不要求最大化必定增加固定100px；UIA重复同值去重、矛盾值失败。真实检查首页/任务/设置，侧栏底部设置可见、滚动与内容随视口变化；保存原始JSON/截图并实际查看。\n通过真实UI或既有private client创建该固定Goal，等原live handle；验证真实Goal/Task/evidence/receipt、模型调用0、原窗口预算及最近任务可见。随后关闭原拥有栈/浏览器并验证退出，再以相同数据库进行一次冷重启，验证同一Task/Goal/支出/receipt仍在、没有重复执行，刷新后最近任务仍显示。不能把SQLite close/reopen fixture、HTTP脚本或终端截图当作真实浏览器/冷重启证据。\n每次关闭必须核对原PID+creation time/原live handle，证明broker退出及readiness失效。只允许清理该新拥有目录和测试scratch，先验证解析后路径仍在该目录；不删除旧证据、工作树或历史数据。\n\n## 禁止与完成边界\n\n模型/API调用0、raw credentials/secrets0、main/Ready/merge/auto-merge0、tag/release/package/container/deploy0、workflow/dependency修改0、CI rerun/dispatch0、跨仓库写0。无未知二进制、全局配置改变、历史数据库迁移/覆盖、reset/clean/stash/restore/amend/rebase/force/bulk-stage。\n摘要必须分别报告本地实现、源码Draft/CI/独立审查、真实窗口/任务/冷重启证据与失败；即使本阶段通过，仍不是全部GitHub待办完成、不是完整Issue118所有适配器完成，也不是mainline landing。真正代码实现任务与后续GitHub/release/deploy适配器须另有适用授权，不能用固定checker Goal代替。\n\nFROZEN_NEW_START=2026-10-08T03:39:22.061791+00:00\nFROZEN_NEW_EXPIRES=2026-10-08T07:39:22.061791+00:00",
    "completion_boundary": "Current-source Draft/CI/independent review plus real fixed checker Goal/native resize/cold restart; not arbitrary coding, mainline or full backlog completion."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "docs/local-client-session.md",
    "frontend/src/components/autonomous-window-editor.tsx",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/hooks/use-platform.ts",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/src/lib/goal-start-operation.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/policy-serializer.ts",
    "frontend/src/schemas/policy.ts",
    "frontend/tests/approvals.test.tsx",
    "frontend/tests/compact-goal-composer.test.tsx",
    "frontend/tests/goal-continuation-activation-errors.test.ts",
    "frontend/tests/goal-start-recovery.test.ts",
    "frontend/tests/policy-serialization.test.ts",
    "frontend/tests/policy-validation.test.ts",
    "frontend/trusted-client.mjs",
    "reverse_agent/platform_v1/authority_adapter.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/publication_controller.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_artifact_handoff_http.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_autonomy_window_lifecycle.py",
    "tests/platform_v1/test_goal_completion_evidence.py",
    "tests/platform_v1/test_goal_functional_checks.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_task_client_auth.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_unattended_coordinator_shutdown.py",
    "tests/test_trust_authorization_adapter.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "docs/local-client-session.md",
    "frontend/src/components/autonomous-window-editor.tsx",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/hooks/use-platform.ts",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/src/lib/goal-start-operation.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/policy-serializer.ts",
    "frontend/src/schemas/policy.ts",
    "frontend/tests/approvals.test.tsx",
    "frontend/tests/compact-goal-composer.test.tsx",
    "frontend/tests/goal-continuation-activation-errors.test.ts",
    "frontend/tests/goal-start-recovery.test.ts",
    "frontend/tests/policy-serialization.test.ts",
    "frontend/tests/policy-validation.test.ts",
    "frontend/trusted-client.mjs",
    "reverse_agent/platform_v1/authority_adapter.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/publication_controller.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_artifact_handoff_http.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_autonomy_window_lifecycle.py",
    "tests/platform_v1/test_goal_completion_evidence.py",
    "tests/platform_v1/test_goal_functional_checks.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_task_client_auth.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_unattended_coordinator_shutdown.py",
    "tests/test_trust_authorization_adapter.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "reverse_agent/platform_v1/local_client_session.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/service.py",
    ".github/workflows/ci.yml",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/repository-client.ts"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "pyproject.toml",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "**/secrets/**",
    "**/.env",
    "**/auth.json"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "mark_ready",
    "merge",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "raw_secret_read_or_export",
    "model_provider_config_mutation",
    "payment",
    "process_stop_without_identity",
    "issue_comment",
    "pull_request_comment",
    "raw_credential_read_copy_or_print",
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass",
    "existing_runtime_or_configuration_mutation",
    "application_model_retry",
    "model_fallback",
    "raw_managed_session_access",
    "existing_task_or_runtime_mutation",
    "destructive_outside_new_owned_disposable_fixture_process_groups_or_scratch",
    "self_independent_acceptance"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": true,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Owned18917Task/18918ModelControl(live0)/18919Frontend and ephemeral provider-free fixture loopbacks only."
    ],
    "github_control_plane_network_exceptions": [
      "Only <=5 pushes of codex/issue118-current-candidate-acceptance-r3-20261008, one Draft <=2 deduplicated attempts against codex/issue118-delegated-native-recovery-r3-v1-20261007@82c9b185a66561d17cf8a6857cd3add2d23215ca, <=4 descriptions and bounded original CI reads. No comments/landing/other writes."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/functional_validation.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "native.bootstrap",
      "command": "Fresh bounded Decision-only activation and canonical gates",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "local_static_check",
        "command_plan_generation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "native.implementation",
      "command": "# 待批准：当前候选的 Draft、CI、独立复审与真实前端验收\n\n状态：PROPOSAL_ONLY，不是执行授权。未激活、未推送、未启动浏览器或系统任务。\n\n## 精确候选与目标\n\n仓库：dddd2024/Nerelan。当前候选 8ff92498f46a329d0f2bedd6ee83f9f1b330baa6，本地全量2151通过、22跳过、4原有opt-in排除、1模拟崩溃线程警告；完整82c9..HEAD差异检查通过。\n明确接纳已提交候选作为只读起点，保留全部旧Decision/失败/额度/绝对截止时间。本方案是独立的新授权，不能重置或延长任何旧授权。\n集成分支：codex/issue118-delegated-native-recovery-r3-v1-20261007，必须仍等于 82c9b185a66561d17cf8a6857cd3add2d23215ca。新分支：codex/issue118-current-candidate-acceptance-r3-20261008，从当前候选8ff92498f46a329d0f2bedd6ee83f9f1b330baa6创建；承接已批准的既有历史，起始head为8ff92498f46a329d0f2bedd6ee83f9f1b330baa6，审查/PR基线为82c9b185a66561d17cf8a6857cd3add2d23215ca，merge-base必须为82c9b185a66561d17cf8a6857cd3add2d23215ca。本阶段明确允许这种已有候选承接，不伪造从集成基线重新实现。\n首先提交新的不可变 APPROVED Path-B Decision，声明 starting_head、activation parent、集成基线、history reuse、精确路径和候选源码清单，再运行现有 canonical plan/preflight。只有 PRE_EXECUTION_AUTHORIZED 才可推进；任何不可满足的Gate停止，不能改Gate。\n\n## 新窗口与累计额度\n\n批准后首次激活时固定一个新的4小时绝对窗口，起止时间一次写入后不可延长。旧2026-10-07窗口和2026-10-08两次本地修复截止保持原值。\n追加：Decision激活1；源码修复2；开发检查4；必需检查8（最多2次完整pytest，各<=2400秒，focused<=900秒，静态<=120秒）；源码提交3；精确非main push5；新Draft最多1个（创建尝试2次，失败后先去重）；描述更新4；独立只读审计1名。\n运行额度：新拥有的克隆1、受控栈启动2、浏览器启动2、原生观察4（每次<=180秒）、身份绑定清理2（每次<=120秒）、真实provider-free窗口激活1、Task1、任务重试0。冷重启必须沿用原数据库、Goal/Task/window/slot与原支出，绝不以新任务、新窗口或重置预算替代恢复。\n所有尝试开始即累加/fsync，旧记录不可改。只允许在同一不可变授权及剩余额度内修复列明范围的实际错误；强制检查失败阻止发布/运行，直到授权内修正并重新通过。不得自动创建后继Decision、扩大范围或重置计数。\n\n## 源码与证据范围\n\n原候选携带的精确产品路径及额外既有启动器路径见 frozen-source-manifest.json。可修复仅为其中路径上的候选验收/启动/窗口/历史恢复故障，最多2次；不允许增加测试排除、跳过、放宽断言或Git空白策略。原候选的全部源码blob与SHA已冻结，其他文件不可改变。\n新的 project_state/decision_packet.md 为唯一可提交的治理入口；既有五个 generated gate 文件可生成但不可提交。复用现有Gate、SQLite、receipt、Goal/Task、private transport和外部证据目录，不新增 tracked Gate/receipt/verifier 家族。\n允许适配原有外部prepare/runtime/native observer/probe/cleanup脚本到当前精确候选及新授权；这些适配不能替代产品源码修复，必须经过授权内静态检查并保留哈希/身份记录。\n\n## 发布与独立验收\n\n只可推送上述新非main分支，并创建对上述冻结集成分支的精确Draft及更新描述。快照绑定当前Decision/源码/head/base，不能把旧CI或旧审计改称新head结果。\n等待原始自然CI run/job；允许限量只读查询与获取其原始日志/JUnit，不允许 rerun/dispatch/no-op commit。检查来源和实际checkout/commit必须匹配。继承已通过且源码表面不变的本地检查须明确原head，不无理由重跑。\n允许1名独立只读Codex审计员审查原集成基线到当前精确head的完整源码范围、实际检查和必需条件；该审计员不得改代码或审批自己的实现。报告写既有外部证据，不写PR/Issue评论。新head必须重新绑定审计。\n保持Draft。无Ready、merge、main push、auto-merge、tag/release、部署或发布产品权限。\n\n## 真实运行验收\n\n只有当前精确head的必需本地/自然CI检查通过且独立审计接受源码后才能运行。\n新拥有目录仅F:/nrl-118-accept-20261008；明确空闲loopback端口18917(Task)、18918(Model control但live调用0)、18919(frontend)。复用现有依赖只读，隔离Vite缓存；不安装依赖、不修改全局配置、不触碰历史Task数据库或其他人的栈。\n固定Node路径E:/Program Files/nodejs/node.exe，启动前重新验证已知SHA58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f。Edge仅现安装路径C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe：启动前必须重新验证Microsoft有效签名并冻结当前版本/哈希；允许现安装Microsoft有效签名的自动更新导致版本变化，记录新指纹后继续，不安装或更换浏览器。其他可执行文件不能据此获权。\n真实新policy/window/activation-slot/host/database/Goal-idempotency/checker scope全部在新Decision里精确固定并由既有编译器验证；Owner批准只通过可信host映射成DELEGATED_CONTROLLER授权，不伪装个人GitHub验收，不靠renderer的local-owner/ACTIVATE/verified字段授权。\n仅固定 git_diff_check/validate_task：冻结frontend/src/components/sidebar.tsx和CHECK001，Task1、并发1、重试0、模型/Provider/GitHub写/发布预算0。这个Goal必须明确说明只检查差异，不能标记任意代码实现目标已完成。\n使用实际拥有的Edge/private broker观察小窗口→最大化→还原，依据实际native客户区与浏览器报告的inner/outer/viewport数据，不要求最大化必定增加固定100px；UIA重复同值去重、矛盾值失败。真实检查首页/任务/设置，侧栏底部设置可见、滚动与内容随视口变化；保存原始JSON/截图并实际查看。\n通过真实UI或既有private client创建该固定Goal，等原live handle；验证真实Goal/Task/evidence/receipt、模型调用0、原窗口预算及最近任务可见。随后关闭原拥有栈/浏览器并验证退出，再以相同数据库进行一次冷重启，验证同一Task/Goal/支出/receipt仍在、没有重复执行，刷新后最近任务仍显示。不能把SQLite close/reopen fixture、HTTP脚本或终端截图当作真实浏览器/冷重启证据。\n每次关闭必须核对原PID+creation time/原live handle，证明broker退出及readiness失效。只允许清理该新拥有目录和测试scratch，先验证解析后路径仍在该目录；不删除旧证据、工作树或历史数据。\n\n## 禁止与完成边界\n\n模型/API调用0、raw credentials/secrets0、main/Ready/merge/auto-merge0、tag/release/package/container/deploy0、workflow/dependency修改0、CI rerun/dispatch0、跨仓库写0。无未知二进制、全局配置改变、历史数据库迁移/覆盖、reset/clean/stash/restore/amend/rebase/force/bulk-stage。\n摘要必须分别报告本地实现、源码Draft/CI/独立审查、真实窗口/任务/冷重启证据与失败；即使本阶段通过，仍不是全部GitHub待办完成、不是完整Issue118所有适配器完成，也不是mainline landing。真正代码实现任务与后续GitHub/release/deploy适配器须另有适用授权，不能用固定checker Goal代替。\n",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "docs/local-client-session.md",
        "frontend/src/components/autonomous-window-editor.tsx",
        "frontend/src/components/goal-composer.tsx",
        "frontend/src/components/sidebar.tsx",
        "frontend/src/hooks/use-platform.ts",
        "frontend/src/lib/goal-continuation-operation.ts",
        "frontend/src/lib/goal-start-operation.ts",
        "frontend/src/lib/platform-client.ts",
        "frontend/src/lib/policy-serializer.ts",
        "frontend/src/schemas/policy.ts",
        "frontend/tests/approvals.test.tsx",
        "frontend/tests/compact-goal-composer.test.tsx",
        "frontend/tests/goal-continuation-activation-errors.test.ts",
        "frontend/tests/goal-start-recovery.test.ts",
        "frontend/tests/policy-serialization.test.ts",
        "frontend/tests/policy-validation.test.ts",
        "frontend/trusted-client.mjs",
        "reverse_agent/platform_v1/authority_adapter.py",
        "reverse_agent/platform_v1/autonomy.py",
        "reverse_agent/platform_v1/control_store.py",
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/publication_controller.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/task_runtime.py",
        "reverse_agent/platform_v1/task_service.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "reverse_agent/platform_v1/unattended_coordinator.py",
        "tests/platform_v1/test_artifact_handoff_http.py",
        "tests/platform_v1/test_autonomy.py",
        "tests/platform_v1/test_autonomy_window_lifecycle.py",
        "tests/platform_v1/test_goal_completion_evidence.py",
        "tests/platform_v1/test_goal_functional_checks.py",
        "tests/platform_v1/test_goal_service.py",
        "tests/platform_v1/test_task_client_auth.py",
        "tests/platform_v1/test_task_runtime.py",
        "tests/platform_v1/test_task_service.py",
        "tests/platform_v1/test_trusted_host.py",
        "tests/platform_v1/test_unattended_coordinator.py",
        "tests/platform_v1/test_unattended_coordinator_shutdown.py",
        "tests/test_trust_authorization_adapter.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validation",
      "command": "Applicable scoped checks, exact committed-range diff, canonical gates, original natural exact-head CI/JUnit and independent read-only audit; only then owned native viewport/Goal/cold restart, within exact proposal limits.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "candidate.publication",
      "command": "Exact non-main candidate publication, deduplicated Draft, bound description and original CI reads under approved proposal.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [],
    "stage_allowed": false,
    "note": "Only explicitly owned runtime F:/nrl-118-accept-20261008 plus external test scratch; historical DB/worktrees untouched."
  },
  "workstream_id": "issue118-current-candidate-acceptance-20261008",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 2,
  "execution_window_hours": 4,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 2,
  "frontend_launch_limit": 2,
  "approval_event_or_time": "2026-10-08T03:39:22.061791+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 4,
  "runtime_acceptance_limits": {
    "clone": 1,
    "stack_start": 2,
    "browser_start": 2,
    "observations": 4,
    "normal_cleanup": 2,
    "real_provider_free_windows": 1,
    "source_corrections": 2,
    "expires_at": "2026-10-08T07:39:22.061791+00:00",
    "owned_runtime_root": "F:/nrl-118-accept-20261008"
  },
  "development_check_run_limit": 4,
  "development_correction_round_limit": 2,
  "mandatory_pytest_process_limit": 2,
  "owned_test_scratch_root": "F:\\reverse-agent-artifacts\\worktree-audit-20261002-56c5\\issue118-current-candidate-acceptance-20261008\\test-scratch",
  "cumulative_prior_development_checks": 27,
  "cumulative_prior_correction_rounds": 23,
  "cumulative_development_check_limit": 31,
  "cumulative_correction_round_limit": 25,
  "mandatory_check_run_limit": 8,
  "autonomy_policy_authority": {
    "schema_version": 1,
    "confirmation_mode": "DELEGATED_CONTROLLER",
    "personally_human": false,
    "controller_identity": "Codex/root under explicit Owner bounded-controller delegation",
    "upper_proposal_sha256": "ead6fb5e342fb717ee37bef8d5c4df02a7553bf78ea874f3d13679ee7bb7365f",
    "upper_expires_at": "2026-10-08T07:39:22.061791+00:00",
    "phase_ordinal": 1,
    "policy_id": "issue118-current-acceptance-policy1",
    "policy_revision": 1,
    "policy": {
      "mode": "CONTROLLER_REVIEW",
      "repository": "dddd2024/Nerelan",
      "resourceAccess": {
        "filesystem": {
          "allowedPaths": [
            "frontend/src/components/sidebar.tsx"
          ],
          "writablePaths": []
        },
        "network": {
          "allowedDomains": [],
          "allowWrite": false
        },
        "shell": {
          "allowedCommands": [
            "git_diff_check"
          ],
          "deniedCommands": []
        },
        "secrets": {
          "access": "none",
          "allowedKeys": []
        },
        "workerApproval": {
          "required": false,
          "approvers": []
        }
      },
      "githubCapabilities": [],
      "publicationCapabilities": [],
      "publicationPolicy": {
        "allowedArtifactOrPackage": [],
        "allowedRegistry": [],
        "allowedRepository": [],
        "allowedEnvironment": []
      },
      "mergePolicy": {
        "allowedRepositories": [],
        "allowedBaseBranches": [],
        "requiredChecks": [],
        "allowedMergeMethods": [],
        "requireExactHead": true
      },
      "autonomousWindow": {
        "enabled": true,
        "startsAt": "2026-10-08T03:39:22.061791Z",
        "expiresAt": "2026-10-08T07:39:22.061791Z",
        "maxPrsOpened": 0,
        "maxMergesToMain": 0,
        "maxReleasesCreated": 0,
        "maxDeploysToEnvironment": 0,
        "stopConditions": [
          {
            "type": "budget_exhausted",
            "scope": "window"
          },
          {
            "type": "window_expired",
            "scope": "window"
          },
          {
            "type": "manual_stop",
            "scope": "window"
          },
          {
            "type": "authority_revoked",
            "scope": "window"
          }
        ]
      },
      "budgets": {
        "maxPrsOpened": 0,
        "maxMergesToMain": 0,
        "maxReleasesCreated": 0,
        "maxDeploysToEnvironment": 0
      }
    },
    "policy_digest_sha256": "16a5d43bd8a552be99048c7e7a61bfc88ad714bddcd0ce906a31110cff58779e",
    "window_id": "issue118-current-acceptance-window1",
    "delegation_slot_id": "issue118-current-acceptance-20261008-slot1",
    "slot_ordinal": 1,
    "max_real_window_activations": 1,
    "host_instance_id": "issue118-current-acceptance-host",
    "runtime_instance_kind": "acceptance",
    "database_path": "F:/nrl-118-accept-20261008/.platform_v1_runtime/tasks.sqlite3",
    "workspace_path": "F:/nrl-118-accept-20261008",
    "allowed_operations": [
      "validate_task"
    ],
    "validation_command_ids": [
      "git_diff_check"
    ],
    "validation_paths": [
      "frontend/src/components/sidebar.tsx"
    ],
    "max_tasks": 1,
    "max_retries": 0,
    "max_concurrent_tasks": 1,
    "model_call_limit": 0,
    "provider_call_limit": 0,
    "github_write_limit": 0,
    "goal_idempotency_key": "issue118-current-acceptance-git-diff-check-goal1",
    "plan_task_id": "CHECK001"
  },
  "adopted_candidate_head": "8ff92498f46a329d0f2bedd6ee83f9f1b330baa6",
  "adopted_candidate_blobs": {
    "docs/local-client-session.md": {
      "git_blob": "d77cea05e99d0f0e05d8588c5416bba407077963",
      "committed_sha256": "b135286aa71e105ad5752cadee470950fe24b5c909894df65971ae5c0fad3493"
    },
    "frontend/src/components/autonomous-window-editor.tsx": {
      "git_blob": "6a114eba0881aa6451301fbfa4715500241b7e20",
      "committed_sha256": "730d8957453685bbfd8eb969ba214ac1da4d6973c21f169ce71fbc4d3b3b8d54"
    },
    "frontend/src/components/goal-composer.tsx": {
      "git_blob": "d04013ec20bf715c1ca60e94805730de2c8454a3",
      "committed_sha256": "27b981369ae1cad7f478ef29866a6238bc977e5499bc5d5cb06b653ecff7c7e4"
    },
    "frontend/src/components/sidebar.tsx": {
      "git_blob": "111e8b0777c12713936177679b1bf1c77de39c0e",
      "committed_sha256": "521cdffe0d07da21cd1bc02fec03831060802d066b75033fbb2b5e931a57c1da"
    },
    "frontend/src/hooks/use-platform.ts": {
      "git_blob": "bcd2a024328e817e887a4ab574e797baf74dbc92",
      "committed_sha256": "d96a42049d809850c67463c44c99a0a7c7313667375cab9ad09a73d4c986eea5"
    },
    "frontend/src/lib/goal-continuation-operation.ts": {
      "git_blob": "707feee19adfa31137852950d10d77346f3c00b7",
      "committed_sha256": "487bc8c655bcb246d4502311ab197593c6b5d2502a2e8bdec60b4282025fdc6e"
    },
    "frontend/src/lib/goal-start-operation.ts": {
      "git_blob": "9de59be17570b2c8cc774e84af4c669210a41bf3",
      "committed_sha256": "d60fc322dfa5d211e052ab28ede0fb06646fb7f541069313b001f66df1e9543e"
    },
    "frontend/src/lib/platform-client.ts": {
      "git_blob": "98500353434247a8b8e672cd3494af58b178cc8b",
      "committed_sha256": "f5591e64901b50bb941d7060c8b4ee43a556e7b1874880469c77c7765f01c5f7"
    },
    "frontend/src/lib/policy-serializer.ts": {
      "git_blob": "090bccc103288f54ffff73fd1fd63cdad0a94978",
      "committed_sha256": "4fbba236a9c1bd3b38b6018a7ecb6a55e599e7636e637883b0b33610d097406e"
    },
    "frontend/src/schemas/policy.ts": {
      "git_blob": "6b2066c34e083153e319ecbaf3cce50f3f143979",
      "committed_sha256": "563c149197bdd38963f2c8f16ead46dd79e0487d4728b885f7fe5423322e0027"
    },
    "frontend/tests/approvals.test.tsx": {
      "git_blob": "4f6814196ff11695030d86dd5ecf4374c1453edd",
      "committed_sha256": "dc7bf479466f14838b55c3a4ed6f773f3a0615b6fb5db498d105114fdb3cf42f"
    },
    "frontend/tests/compact-goal-composer.test.tsx": {
      "git_blob": "7d0baa91fbe25efa889af4d9b47d139feb51134e",
      "committed_sha256": "adb3390887ff531f312d6c8d7d56814e5a7f87a5a357279019ec1eafe9d3898f"
    },
    "frontend/tests/goal-continuation-activation-errors.test.ts": {
      "git_blob": "10d7a6bb6a9fb4f37bd145c932c4d9e6d4451542",
      "committed_sha256": "56860df9b3014d75e964b303395e00a5fab55f21c49448e3571895bea9709359"
    },
    "frontend/tests/goal-start-recovery.test.ts": {
      "git_blob": "66d7f3b7118f2ef103dce7030f7e9fbe70c764f2",
      "committed_sha256": "fc71275769ca0585874d3463b08c1f0d3c0d15662a74bc8aec20584af3957643"
    },
    "frontend/tests/policy-serialization.test.ts": {
      "git_blob": "d5d12b14d53128d718d7801a60f59bff28c31d49",
      "committed_sha256": "940e825b23a54d225645104735bb77971bd36fc82b54fd1f4d0e0320080edbbd"
    },
    "frontend/tests/policy-validation.test.ts": {
      "git_blob": "b7fc69e33dd9e79c3ba16737821f8f98142e31d9",
      "committed_sha256": "4924e5ca42d7463aa1c054ecc747db68d60097ca7757670b4a7729d5c2223c41"
    },
    "frontend/trusted-client.mjs": {
      "git_blob": "39bcb1d7b6b6ad01a9a87c688ffe5ccf85b11d80",
      "committed_sha256": "36c006d2fd8824676db5971e4fea3fa2068425daa5d29a1fda2c48734b59de31"
    },
    "reverse_agent/platform_v1/authority_adapter.py": {
      "git_blob": "c0045f9dfa9d54099cf8ea65e88be7bee6583a20",
      "committed_sha256": "053b4e5c2c8619d8ac322cb5656e1ffdcefc1797056a5b63a368e411a39f4aaa"
    },
    "reverse_agent/platform_v1/autonomy.py": {
      "git_blob": "3ff599b2cf791601747cfd04809c433bc6f08991",
      "committed_sha256": "60c6efac833561ad7e419195e2911c47d2e0819fe32752a83a72525b1d567749"
    },
    "reverse_agent/platform_v1/control_store.py": {
      "git_blob": "a29e385d0032c5478e50dc2c0b8722b92d1b5afa",
      "committed_sha256": "a5da3129399cfa0b5cff1fdca37c9980889c371dd0afad2bbdc4c4594f8138af"
    },
    "reverse_agent/platform_v1/goal_service.py": {
      "git_blob": "da61a1749cf37882df853b54e76754c43a4460fa",
      "committed_sha256": "d656bb3472187739ca8ecf1dd1fbe2ad5de013cede22689ec98bfba0dc12ec3f"
    },
    "reverse_agent/platform_v1/publication_controller.py": {
      "git_blob": "1fd04c9c024836c6fd89fb075d00bdafaad2e519",
      "committed_sha256": "5aea326521e2ccc8f90ecad41374ad1c854d790266086ee73bffd93a3256c9d7"
    },
    "reverse_agent/platform_v1/task_execution.py": {
      "git_blob": "96fd1d49d52be98d6b7506b5c563a08a3c5547e4",
      "committed_sha256": "3f233ec08be7b93314a956b0f3257bd59c9043becd9de8067d4d7bc6cc6cc151"
    },
    "reverse_agent/platform_v1/task_runtime.py": {
      "git_blob": "d06f14b9e2ce029f1546ba8eabb6d7c4418bc211",
      "committed_sha256": "86ab5bb6e42e4a0cf7386e09d1e900cdb23ab2e5b6830bef5f24d2216081e4b0"
    },
    "reverse_agent/platform_v1/task_service.py": {
      "git_blob": "2467a36e2ef525d09de91717adb41b203fb2eb77",
      "committed_sha256": "1610baf13e3765fa1efbdd8e75aa9817630146e3019ab74c989de4c73557d159"
    },
    "reverse_agent/platform_v1/trusted_host.py": {
      "git_blob": "77c69351f4fd26936f538a028e155ff6d15c0b9f",
      "committed_sha256": "dc13dbd8a74b7142f011f1a96df85290c36f46378847a3e77f2b72c46d8036f0"
    },
    "reverse_agent/platform_v1/unattended_coordinator.py": {
      "git_blob": "a3c5df583920f6d1dff26bc42d4dd485802112c6",
      "committed_sha256": "859e4c0568ef6e8f171bb47d04b07f265906ea4a6e061b3638dfe687de0a872d"
    },
    "tests/platform_v1/test_artifact_handoff_http.py": {
      "git_blob": "d20309368f1cd397c0c1fb2ecdd91882f06c474a",
      "committed_sha256": "fafc99efa34848fd6632466832a58aae02f71f8bf29ca9967b02ea031921f46d"
    },
    "tests/platform_v1/test_autonomy.py": {
      "git_blob": "dda730fa501eea0afbb11a254d1a770982407b04",
      "committed_sha256": "8517946ec53cd0b9dcb8505fb50e6a6fc704c09025c02820999e01307b5195a5"
    },
    "tests/platform_v1/test_autonomy_window_lifecycle.py": {
      "git_blob": "6e1f676c6a70b4f936504abb637c0ad2bae4890b",
      "committed_sha256": "53c8f3120cff8776f98e898b3421fa052c78fc91bf537ae269ab7c70953f40e5"
    },
    "tests/platform_v1/test_goal_completion_evidence.py": {
      "git_blob": "15ac1b5ee16b71470b07887d6c81cd1de86d7c01",
      "committed_sha256": "6beb80853906d337a8c3f534fa74c6dca9311b8ab46cbfffce9fec160d6e5e29"
    },
    "tests/platform_v1/test_goal_functional_checks.py": {
      "git_blob": "ee572f64e23ac7c76126f4280bfea0c19ecf9e3a",
      "committed_sha256": "654ee7f8b743593435d9760c5f77b7a05187dfb53259e852c1c7f92b068c633b"
    },
    "tests/platform_v1/test_goal_service.py": {
      "git_blob": "1983db59ba085b8eee000e3960f13450a9754414",
      "committed_sha256": "52e21cd15fbeee13d9257884bff19c2026c84f18b89cb07378745b3a0788cdd8"
    },
    "tests/platform_v1/test_task_client_auth.py": {
      "git_blob": "8c37f226786853d139e4eafa83f872156eec3b38",
      "committed_sha256": "d05925ba110c33b21ba957fdbb9b62cc1ae09c2bdb7a00fd3a2f2c323e4ae04a"
    },
    "tests/platform_v1/test_task_runtime.py": {
      "git_blob": "94f4fc12a27aa24b2cb96c94d7dd1fe3e4b4264e",
      "committed_sha256": "29d570e1abbf92256b7777ae408e6397f28465bdabcf8eb7ec27742417a52bec"
    },
    "tests/platform_v1/test_task_service.py": {
      "git_blob": "34eda7484367b3d81a8bd2eba17bc57a113c45d6",
      "committed_sha256": "c4a9b8691c5fe7a2ba481fe323a3e8a14102d09b3414327749cd47885706572d"
    },
    "tests/platform_v1/test_trusted_host.py": {
      "git_blob": "50a7a68abcdf3a882e45fb80671981bfc77b066f",
      "committed_sha256": "ba6338f13c98ff1090ebd7f24da2803c8d8683a2925797e4d3b07b35e169fc6c"
    },
    "tests/platform_v1/test_unattended_coordinator.py": {
      "git_blob": "5bee66c7c84829041e849c2fe193d660955d5f40",
      "committed_sha256": "e372ee0f8260ebbbd6ee6ca7aec177ae413a5facc81990ee471fd17d1a9777b3"
    },
    "tests/platform_v1/test_unattended_coordinator_shutdown.py": {
      "git_blob": "8a0e77015a10e04966a540fcfff12d8ff24305cd",
      "committed_sha256": "ac54b22e6b77490a82c7bf22732b7a3493e8890dee7b698415fb34b341ce3d99"
    },
    "tests/test_trust_authorization_adapter.py": {
      "git_blob": "c0401c815d88452500c97008345f03d55f5d0b12",
      "committed_sha256": "760ce935ee42e7902a8400891e713ef6cc3c349924801bef5a2930deb68a0f72"
    }
  }
}
```
