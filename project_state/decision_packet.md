# Bounded tool-free system-authored lifetime continuation

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260928_issue989_system_runtime_budget_r3_v4",
  "round_id": "round_20260928_issue989_system_runtime_budget_r3_v4",
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
  "approval_basis": "Owner latest explicitly instructs supervisor to resolve this scope violation and future similar blockers autonomously, use newly configured APIs and continue prioritized tasks. Preserve system-only product authorship. Fresh bounded continuation uses existing project ModelProfileStore/default_vault_adapter and CredentialRelayManager/forward_to_upstream for text-only inference; provider credentials resolved only internally by existing trusted store, never printed/exported. No OpenCode tools/process/model shell. Model response is untrusted patch data, exact five-path and old-text validation then supervisor transfers bytes/reviews before deterministic tests. Scope violation v3candidate remains unaccepted reference. No weakening gates or scope.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "activation_base_sha": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "starting_head": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "fresh_base": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "current_main_expected": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "required_branch": "codex/issue989-runtime-budget-system-v4-20260928",
  "workstream_id": "issue989-system-runtime-budget-v4",
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
  "live_model_call_limit": 8,
  "provider_network_call_limit": 8,
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
  "live_provider_access_allowed": true,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": true,
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
    "specification": "System adapts existing unaccepted989 bounded-deadline candidate to current main. Bind actual validated CLI/server execution budget once before invocation to the execution-scoped relay capability. Preserve generic default120seconds, executor default300seconds; executor budget finite positive <=3600, total lease lifetime <=3630 including at most30seconds setup margin. Reject bool/nonfinite/nonpositive/excessive/invalid timing before effects. Validate existing manager default/override lifetime and cleanup margin finite/type semantics too using existing error classes, without widening API/defaults. Never renew/rebind/revive used/expired/released leases; clock rollback cannot prolong effective lifetime or undo observed expiry. Preserve connection/model isolation and upstream secret confinement. Release on success/error/timeout/cancel and setup/argv/event/bind exceptions in both CLI/server paths; release is safe idempotent. Preserve current main980assistant evidence and997WindowsPATHEXT changes byte-semantically; do not reapply obsolete Windows hunks or fix372direct-session isolation here. No model-selector override/failover/TaskStore/UI/refactor. Reuse existing callback/manager/host abstractions and old989tests; system authors all five allowed files. Supervisor supplies oldcandidateasread-onlytaskdata, neveroldDecision or rootdirtysource. Prior partial v2 two-file diff may be supplied as read-only task data along with old989reference; worker still starts at this fresh activation, no product-input commit. It is incomplete and unaccepted, not a finished patch. Use targeted source reads and real pytest via approved installed dependency path. WindowsSystemDrive remains a separate verified residual; do not close all989 after this lifetime slice. Existing v3 four-file partial may be copied after activation Draft as unaccepted system-authored development input, exact archived hashes. No product-input commit. Model returns JSON edits with exact path/old/new strings only; supervisor never authors repairs or executes model commands. Reject absolute/parent/alternate-stream/unlisted paths, symlink/reparse targets and mismatched originals. Review complete generated code before tests. Max8 modelcalls, zero automatic retry, each<=600seconds, no token/spend cap; no tool definitions or tool dispatch of any kind. No OSsandbox closure claim.",
    "completion_boundary": "All source/test bytes system-authored via bounded tool-free calls, independent source review and provider-free checks, one final source commit, exact-head natural CI and independent acceptance. No native TaskAPI functional receipt claimed: this is supervised text-only recovery through project inference boundary, not an OpenCode Task. No Ready/merge/closure/deployment. Keep989OPEN forWindowsresidual and299OPEN forfullsandbox."
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
    "model_api_invocation_allowed": true,
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
      "Existing project native credential relay forwarding to unchanged coding-default Binding only, max8 text-only model calls with600sec timeout, no tools/schema tools/callback dispatch. Existing trusted store internally resolves OS-vault credential at point of use only, no rawcredentialread/output/export. Public API metadata read only. Synthetic provider-free tests and test-owned loopback only."
    ],
    "github_control_plane_network_exceptions": [
      "Canonical exact branch activation/implementation pushes and one Draft; descriptions only. No Ready/merge/tag/release under source stage."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue989v4.bootstrap",
      "command": "Fresh exactbase 86844b5bc8e42172f2a39d555fd7053973a01155 checkout F:/Nerelan-issue989-system-v4-20260928 branchcodex/issue989-runtime-budget-system-v4-20260928; one immutableDecisionactivationcommit only. Existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness via python -m reverse_agent.project_gate SUBCOMMAND --state-dir project_state. Require PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY. FirstDraft before sourcechanges; generatedgates neverstaged.",
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
      "command_id": "issue989v4.runtime",
      "command": "Read-only existing runtime status; no runtime restart or deployment needed. Use current clean source worktree imports for existing ModelProfileStore/OSvault/relay APIs in supervisor-owned external temporary helper. Explicit model state path F:/reverse-agent/.platform_v1_runtime/model_setup_state.json consumed only by existing store, not displayed. No userconfigurationwrites.",
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
      "command_id": "issue989v4.system",
      "command": "After activationDraft, copy exactly archived v3system four-file partial as unaccepted development input; no inputcommit. Up to8 text-only project-native relay calls unchanged coding-default. Prompt only approved/relevant source, no secrets. No model tools or execution loop. Treat responses as data, reject toolcalls, validate fixed five-path allowlist/regular files/exactoldtext/no symlink or alternatepath before applying exactsystemedits. Supervisor independently reviews then fixed approvedpytest/diff checks. Onefinalproductcommit. No OpenCode child or TaskAPI dispatch.",
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
        "machine_specific_execution",
        "model_api_invocation",
        "network_access"
      ],
      "network_access": true,
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
      "command_id": "issue989v4.checks",
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
      "command_id": "issue989v4.publish",
      "command": "Exactbranchcodex/issue989-runtime-budget-system-v4-20260928 atmost2pushesactivation/final,oneDraftagainstmain@86844b5bc8e42172f2a39d555fd7053973a01155; headboundbodyupdates. RequirePUBLICATION_READY/freshbase/scope/no concurrentmutation. NoReady/merge/closure/historyrewrite.",
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
      "command_id": "issue989v4.ci",
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
      "command_id": "issue989v4.audit",
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
      1014
    ],
    "policy": "Preserve old989dirtypatch and Decision, old991, otherPRs, root71records, userConnections/Bindings/APIkeys. Main990receipt/CI closure remains separately supervised. No deployment/root source import or manual source edits. Preserve v2Draft1013activation95413548 andworkerpartial manifest, failedTask andquotaerrors; do not publish fromv2."
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
