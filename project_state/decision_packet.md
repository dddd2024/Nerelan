# Exact-byte system lifetime continuation with canonical LF authority

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260928_issue989_system_runtime_budget_r3_v5",
  "round_id": "round_20260928_issue989_system_runtime_budget_r3_v5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "repository": "dddd2024/Nerelan",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "provider_free_acceptance_required": true,
  "decision_scope": "ISSUE989_BOUNDED_LEASE_LIFETIME_RESIDUAL_ONLY",
  "source_issue": 989,
  "parent_issue": 1010,
  "approved_by": "dddd2024 via explicit delegated Owner authorization",
  "approval_basis": "Owner latest explicitly authorizes autonomous resolution of this and similar blockers. v4 exactsourceheadc328b1217bf181c2193e24dd28cbbd588ad32eca passed94+193+68tests with1skip, but mandatory base-to-head diffcheckFAILED because its immutableDecisionblobcontainsCRLF435lines. Preservefrozenv4Decision andcandidate andDraft1015, no fixforward/amend/publicationthere. Freshcurrentmain successor writesnewDecisionLF, copiesexactsame system-authored fourproductfiles withno edits, onefinalproductcommit, allfinalchecksagain. No newmodelcall orsourceauthoring. Supervisor remainsnonproductauthor.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "activation_base_sha": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "starting_head": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "fresh_base": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "current_main_expected": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "required_branch": "codex/issue989-runtime-budget-system-v5-20260928",
  "workstream_id": "issue989-system-runtime-budget-v5",
  "follows_last_decision_id": "decision_20260928_issue990_system_source_policy_r3_v2",
  "follows_last_round_id": "round_20260928_issue990_system_source_policy_r3_v2",
  "workflow_profile": "baseline",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
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
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/model_access/credential_relay.py",
    "tests/platform_v1/test_execution_runtime_budget.py",
    "tests/platform_v1/test_opencode_executor.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/model_access/credential_relay.py",
    "tests/platform_v1/test_execution_runtime_budget.py",
    "tests/platform_v1/test_opencode_executor.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "frontend/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/coordinator.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/model_access/store.py",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt"
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
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "snapshot_generation_or_threshold_change",
    "fix_forward_after_mandatory_failure"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/model_access/credential_relay.py",
      "minimum_risk": "R3"
    }
  ],
  "semantic_implementation_contract": {
    "specification": "Exactbyte reuse of four system-authored product/test files at v4commitc328b1217bf181c2193e24dd28cbbd588ad32eca: reverse_agent/platform_v1/opencode_executor.py,reverse_agent/platform_v1/trusted_host.py,reverse_agent/model_access/credential_relay.py,tests/platform_v1/test_execution_runtime_budget.py. No source edits. Preserve v4 system provenance: archivedworkerpartial plus text-onlycalls2/4/5/6,0tools; calls1/3notaccepted. Same lifetimecontract includingdefaults120/300, execution<=3600,margin<=30,lifetime<=3630, finiteadmission/atomicusedstate/noexpiryrevival/terminalrelease. OnlynewDecisionusesLF. Do not import oldDecision or generatedgates. Mandatoryfailurestopsaffectedpublication, nofixforward. Windowsresidualandfullsandboxremainopen.",
    "completion_boundary": "No new implementation/modelcalls. Exactbyte transfer afteractivationDraft, oneproductcommit, exacthead94budget+transport+hostrelaychecks,diffandgates; independentacceptance/naturalCI before laterseparatelanding. No source-stageReady/merge/closure/deployment. Keep989OPENWindowsresidual and299OPEN."
  },
  "runtime_scratch_policy": {
    "paths": [
      ".platform_v1_runtime/**",
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Existing launcher runtime stores/metadata only, preserve persisted settings. For approved provider-free tests ONLY, a test subprocess may set PYTHONPATH to existing trusted installed C:/Users/wjc27/AppData/Roaming/Python/Python313/site-packages so pytest is visible. No install, global env change or product child-env relaxation; no arbitrary home/secret reads. Evidence remains outside tracked source."
  },
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "Unchanged natural CI package setup and provider-free checks only; no added workflow or manual dispatch."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Existingloopbackpublicmetadataread andsyntheticprovider-freetest-ownedloopback only. No liveprovider calls."
    ],
    "github_control_plane_network_exceptions": [
      "Canonical exact branch activation/implementation pushes and one Draft; descriptions only. No Ready/merge/tag/release under source stage."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue989v5.bootstrap",
      "command": "Fresh exactbase 86844b5bc8e42172f2a39d555fd7053973a01155 checkout F:/Nerelan-issue989-system-v5-20260928 branchcodex/issue989-runtime-budget-system-v5-20260928; one immutableDecisionactivationcommit only. Existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness via python -m reverse_agent.project_gate SUBCOMMAND --state-dir project_state. Require PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY. FirstDraft before sourcechanges; generatedgates neverstaged.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "command_plan_generation",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue989v5.runtime",
      "command": "No runtime restart/deployment/modelcalls. Readonlystatus and exactbyteverification.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue989v5.system",
      "command": "AfteractivationDraft copyexactGitblobsof fourapprovedfiles from knownv4systemcommitc328b1217bf181c2193e24dd28cbbd588ad32eca; verifyeachSHA256before/aftertransfer. No sourceedit,modelcall oroldDecisionimport. Oneproductcommitafterdevelopmentchecks andreadiness.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "commit",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "reverse_agent/model_access/credential_relay.py",
        "tests/platform_v1/test_execution_runtime_budget.py",
        "tests/platform_v1/test_opencode_executor.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue989v5.checks",
      "command": "Developmentchecks/fixesbeforefreeze. Finalexactheadmandatory python -B -m pytest tests/platform_v1/test_execution_runtime_budget.py -q -p no:cacheprovider; python -B -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py -q -p no:cacheprovider; python -B -m pytest tests/platform_v1/test_credential_relay.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_trusted_host_lifecycle.py -q -p no:cacheprovider; git diff --check base HEAD. Synthetickeys/fakeclock/testloopbackonly, norealcredentials/providers. Canonicalreadinessbeforestageusingcachedcleanstart; aftercommitallgatesagain. Neverrerunstartupmid-dirtytooverwritecleansnapshot. R3literalrelay-sourceauthorization mustpass existing990policy, no waiver.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue989v5.publish",
      "command": "Exactbranchcodex/issue989-runtime-budget-system-v5-20260928 atmost2pushesactivation/final,oneDraftagainstmain@86844b5bc8e42172f2a39d555fd7053973a01155; headboundbodyupdates. RequirePUBLICATION_READY/freshbase/scope/no concurrentmutation. NoReady/merge/closure/historyrewrite.",
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
    },
    {
      "command_id": "issue989v5.ci",
      "command": "Observe naturalexactheadCI/Decision/State plusnativeartifact, providerfreechecks. No reruns/manualdispatch/dependency/workflowchanges.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue989v5.audit",
      "command": "Independent supervisor exactheadreview including actual composedhost/executor/relay tests, boundeddeadline/clock/type/cleanup and secretisolation; notmodelselfreport. Distinguish sourceacceptance fromdirtyhost/deployment/landing.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "read_only_audit",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "concurrent_work_preservation": {
    "prs": [
      991,
      992,
      995,
      1000,
      1003,
      1007,
      1008,
      1012,
      1013,
      1014,
      1015
    ],
    "policy": "Preservev4frozenDecision/sourcecommit/Draft1015 aftermandatoryCRLFdiffcheckfailure; no v4publication oritsconditionalPR1015landing. Preserveallroot71records/settings/keys/oldworktrees. Newboundedv5correctsactivationformatonly, sourcebytesidentical."
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "dev-up.ps1",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/model_access/contracts.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_credential_relay.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_trusted_host_lifecycle.py"
  ],
  "source_issues": [
    989
  ],
  "required_provider_free_checks": [
    "python -m pytest tests/platform_v1/test_execution_runtime_budget.py -q",
    "python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py -q",
    "python -m pytest tests/platform_v1/test_credential_relay.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_trusted_host_lifecycle.py -q",
    "git diff --check"
  ],
  "runtime_budget_contract": {
    "default_executor_seconds": 300,
    "generic_default_lease_seconds": 120,
    "finite_execution_hard_cap_seconds": 3600,
    "maximum_setup_margin_seconds": 30,
    "finite_lease_hard_cap_seconds": 3630,
    "deadline_semantics": "Retain default executor300 and generic lease120seconds. Bind once before actual CLI/server invocation from validated executor timeout plus at most30seconds setup margin, or equivalent bounded deadline provider API. Only finite positive execution durations <=3600seconds; total execution-scoped lease lifetime <=3630seconds. No recurring renewal, revival of expired/released lease, unlimited grace, or global default extension. Reject expired deadlines/clock ambiguity instead of extending them.",
    "tests": "Synthetic snapshots/fake clock only. Prove request after120seconds succeeds within300-second task; expiry after exact configured deadline plus bounded margin rejects; release immediately rejects. Prove nondefault actual CLI/server timeouts reach binding and release on success/error/timeout/cancellation. Validate NaN/infinity/bool/negative/excessive values before side effects. Existing cancellation semantics only; no new cancellation API."
  },
  "fallback_provenance": {
    "prior_task": "task-1790571994971-a36dab8a3edc",
    "prior_source_pr": 1013,
    "prior_activation": "954135486f474d4186b3df98ee581ee06c6670f1",
    "failure": "Observed GLM token plan entitlement exhausted/rpm exhausted; guarded process termination yielded FAILED/executor_nonzero, no tests run.",
    "healthy_route_task": "task-1790573146048-ec27e932825b",
    "health_session": "ses_f19859ef7ffeNcIJ1WLkRIVBsd",
    "health_response": "READY, zero tools",
    "partial_source_manifest": {
      "status": "UNACCEPTED_PARTIAL",
      "last_tool_updated": 1790572486448,
      "hashes": {
        "reverse_agent/model_access/credential_relay.py": "9347df926260364eac7ad9254ba980881ca719a4d948c04ea287d8b374a776f1",
        "reverse_agent/platform_v1/opencode_executor.py": "b6690a9d6675fb48782dd4e2b8add2fe77e410f552f861688b079dacc740cd5a"
      },
      "task_status": "RUNNING"
    },
    "v3_scope_failure": "task-1790573660303-1c993d91167f FAILED after guardedstop05:50:47Z, externalonebyteprobe written/deleted. Archived4filesUNACCEPTED_SCOPE_VIOLATION. Do not resume unconfinedexecutor."
  }
}
```
