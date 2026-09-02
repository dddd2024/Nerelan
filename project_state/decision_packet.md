# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260902_issue530_brand2b_landing_r3_v20","round_id":"round_20260902_issue530_brand2b_landing_r3_v20","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260901_issue444_auth_completion_r3_v5",
  "follows_last_round_id": "round_20260901_issue444_auth_completion_r3_v5",
  "supersedes_decision_id": "decision_20260902_issue530_brand2b_landing_r3_v19",
  "previous_audit_outcome": "V19_FAIL_CLOSED_RUNNER_TRACKED_GATE_ARTIFACT_CLEANUP_BUG",
  "workstream_id": "issue530-brand2b-landing-r3-v20",
  "source_issue": 530,
  "parent_issue": 262,
  "integration_base_ref": "main",
  "base_sha": "0feeb3f35ef164591678caba96fb46477b366f52",
  "activation_base_sha": "0feeb3f35ef164591678caba96fb46477b366f52",
  "starting_head": "0feeb3f35ef164591678caba96fb46477b366f52",
  "required_branch": "owner/issue530-brand2b-landing-r3-v20",
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R3",
  "workflow_profile": "baseline",
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_activation_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "product_change_commit_limit": 1,
  "post_publication_binding_commit_limit": 1,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": true,
  "hosted_python_version_required": "3.13",
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "historical_evidence_rewrite_allowed": false,
  "current_repository": "dddd2024/Nerelan",
  "legacy_repository_alias": "dddd2024/reverse-agent",
  "repository_id_must_remain": 1210115070,
  "historical_intent_versions_frozen": [
    1,
    2,
    3
  ],
  "current_intent_version": 4,
  "current_attestation_version": 4,
  "reviewed_v16_semantic_source_head": "4847d6fd441c0c359eb25ea5b8acc9389a057d96",
  "v16_validation_pr": 539,
  "failed_landing_prs": [
    545,
    546
  ],
  "v18_failed_exact_head": "c138bd539a4f3c4814851970e1d4a3ec31607aed",
  "v18_ci_failure_test": "tests/test_mainline_landing.py::test_production_pre_merge_simulation",
  "v19_failure_mode": "one-time runner deleted tracked transition preview/preflight artifacts before clean-tree assertion; no product commit or PR was produced and rerun was forbidden",
  "authorized_test_change": "inside test_production_pre_merge_simulation only, derive approval_payload.repository and attestation.repository from intent['repository'] instead of hard-coded dddd2024/reverse-agent",
  "implementation_mode": "direct_git_tree_atomic_replay_without_temporary_workflow",
  "visual_snapshot_updates_allowed": false,
  "known_inherited_visual_mismatch_set": "exactly eight Home/Settings light/dark desktop/mobile golden mismatches from pre-BRAND-2B baseline",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify current main remains exactly 0feeb3f35ef164591678caba96fb46477b366f52 and repository id remains 1210115070",
    "verify accepted validation PR 539 remains at 4847d6fd441c0c359eb25ea5b8acc9389a057d96 and failed landing PRs 545 and 546 are closed unmerged",
    "commit this immutable BRAND-2B v20 Decision as the unique first commit",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue530v20.materialize",
      "command": "materialize the deterministic v20 command plan; compiler transition preview and preflight result are authorized ephemeral R2 gate artifacts but commit only command_plan.json",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue530v20.replay_atomic_candidate",
      "command": "construct one Git tree on the v20 branch that replays all twenty-four accepted BRAND-2B v16 product schema documentation and regression files from 4847d6fd441c0c359eb25ea5b8acc9389a057d96; preserve twenty-three files byte-for-byte; only inside tests/test_mainline_landing.py test_production_pre_merge_simulation replace the two hard-coded dddd2024/reverse-agent repository values in approval_payload and attestation with intent['repository']; prove exactly two replacements and no other change in that file; create exactly one product commit and fast-forward only the v20 branch; create no workflow, use no secrets model provider or external service calls",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "test_edit",
        "commit",
        "push",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "AGENTS.md",
        "README.txt",
        "docs/supervisor/audit-instructions.md",
        "frontend/src/components/goal-composer.tsx",
        "frontend/src/lib/platform-client.ts",
        "frontend/src/lib/profile-mapper.ts",
        "frontend/tests/compact-goal-composer.test.tsx",
        "project_state/schemas/mainline_merge_intent_v4.schema.json",
        "project_state/schemas/merge_approval_attestation_v4.schema.json",
        "reverse_agent/mainline_landing.py",
        "reverse_agent/platform_v1/control_store.py",
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/inbox_service.py",
        "reverse_agent/platform_v1/run_store.py",
        "reverse_agent/platform_v1/task_service.py",
        "scripts/supervisor_publish.py",
        "scripts/supervisor_validate.py",
        "tests/platform_v1/test_goal_service.py",
        "tests/platform_v1/test_publication_controller.py",
        "tests/platform_v1/test_run_read_model.py",
        "tests/platform_v1/test_task_service.py",
        "tests/platform_v1/test_unattended_coordinator.py",
        "tests/test_mainline_landing.py",
        "tests/test_project_gate.py"
      ]
    },
    {
      "command_id": "issue530v20.verify_prepublication",
      "command": "verify exactly twenty-four candidate paths plus immutable Decision and command plan differ from locked main, twenty-three replayed files are byte-identical to v16, tests/test_mainline_landing.py differs from v16 only by the authorized two-line production simulation repository derivation, historical evidence and compatibility namespaces remain intact, no workflow was added, and visual snapshots are untouched",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "repository_diff",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue530v20.publish",
      "command": "publish exactly one new Draft landing PR against locked main after prepublication verification; do not reuse PR 539 545 or 546",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue530v20.bind",
      "command": "after GitHub assigns the landing PR number archive the inherited active PR499 schema-v3 intent byte-for-byte and replace active.json once with schema-v4 dddd2024/Nerelan intent bound to the actual PR locked base v20 Decision and command-plan digests baseline profile and merge-only policy",
      "phase": "post_publication_binding",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "commit",
        "push",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr499_v3.json"
      ],
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue530v20.validate",
      "command": "on the final bound exact head observe fresh natural run_attempt=1 CI Decision Preflight State Gate and Model Access without reruns; require all functional governance checks success; Playwright may fail only for the exact inherited eight Home/Settings light/dark desktop/mobile golden mismatches",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "workflow_observation",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "ci_check_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue530v20.audit",
      "command": "perform independent read-only exact-head audit confirming v16 product semantics plus only the authorized two-line simulation fixture repair, immutable authority, valid active v4 PR/Nerelan intent, byte-identical PR499 archive, no snapshots or unresolved blockers and preserved v1-v3 historical semantics; record ACCEPTED or REWORK_REQUIRED",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "repository_diff",
        "pull_request_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue530v20.attest",
      "command": "only after audit ACCEPTED publish one canonical-digest-valid unexpired schema-v4 MAINLINE_MERGE_APPROVAL_ATTESTATION for exact accepted head using owner dddd2024 and exact successful baseline workflow observations",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "pull_request_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue530v20.land",
      "command": "revalidate unchanged base and head active v4 intent owner attestation audit and zero blockers; mark Ready exactly once, observe fresh natural Ready-event required checks if emitted, then merge exactly once using merge method and expected-head protection",
      "phase": "landing",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "mark_ready",
        "workflow_observation",
        "merge",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue530v20.closeout",
      "command": "after merge verify main advanced through expected merge and natural post-merge State Gate push succeeds; close Issue 530 completed, update parent Issue 262, close validation PR 539 as superseded if still open, and record final merge evidence",
      "phase": "closeout",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "workflow_observation",
        "issue_comment",
        "issue_close",
        "pull_request_update",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr499_v3.json",
    "AGENTS.md",
    "README.txt",
    "docs/supervisor/audit-instructions.md",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/profile-mapper.ts",
    "frontend/tests/compact-goal-composer.test.tsx",
    "project_state/schemas/mainline_merge_intent_v4.schema.json",
    "project_state/schemas/merge_approval_attestation_v4.schema.json",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/inbox_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "scripts/supervisor_publish.py",
    "scripts/supervisor_validate.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_publication_controller.py",
    "tests/platform_v1/test_run_read_model.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py"
  ],
  "authorized_risk_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr499_v3.json",
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent_v4.schema.json",
    "project_state/schemas/merge_approval_attestation_v4.schema.json",
    "tests/test_project_gate.py",
    "tests/test_mainline_landing.py"
  ],
  "forbidden_mutated_paths": [
    "project_state/rounds/**",
    "project_state/mainline_recoveries/**",
    "project_state/integration_baselines/**",
    ".github/workflows/**",
    "frontend/e2e/snapshots/**",
    "frontend/tests/e2e/**/*.png",
    "frontend/tests/e2e/**/__screenshots__/**",
    "pyproject.toml",
    "reverse_agent/__init__.py"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/mainline_landing.py",
      "minimum_risk": "R3"
    },
    {
      "pattern": "project_state/schemas/mainline_merge_intent_v4.schema.json",
      "minimum_risk": "R3"
    },
    {
      "pattern": "project_state/schemas/merge_approval_attestation_v4.schema.json",
      "minimum_risk": "R3"
    },
    {
      "pattern": "tests/test_project_gate.py",
      "minimum_risk": "R3"
    },
    {
      "pattern": "tests/test_mainline_landing.py",
      "minimum_risk": "R3"
    }
  ]
}
```
