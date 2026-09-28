# Conditional exact-head delegated lifetime landing

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260928_pr1016_delegated_landing_r3_v1",
  "round_id": "round_20260928_pr1016_delegated_landing_r3_v1",
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
  "decision_scope": "EXACT_PR1016_DELEGATED_LANDING_ONLY",
  "source_issue": 989,
  "parent_issue": 1010,
  "approved_by": "dddd2024 via explicit current delegated Owner authorization",
  "approval_basis": "Owner explicitly delegated all pending/new tasks, system implementation, independent AI or supervisor acceptance and publication/merge, with no token/cost cap. This bounded Decision authorizes a Decision-only unmerged authority Draft and exact PR1016 landing under the existing false/none attestation protocol. All Owner-account actions are disclosed delegated automation, never personal human review.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "required_branch": "codex/pr1016-delegated-landing-v1-20260928",
  "workstream_id": "pr1016-delegated-landing-r3-v1",
  "follows_last_decision_id": "decision_20260928_issue989_system_runtime_budget_r3_v5",
  "follows_last_round_id": "round_20260928_issue989_system_runtime_budget_r3_v5",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
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
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "base_sha": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "activation_base_sha": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "starting_head": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "fresh_base": "86844b5bc8e42172f2a39d555fd7053973a01155",
  "current_main_expected": "86844b5bc8e42172f2a39d555fd7053973a01155",
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
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
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    "docs/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt"
  ],
  "forbidden_operations": [
    "source_edit",
    "direct_push_main",
    "force_push",
    "rebase",
    "history_rewrite",
    "auto_merge",
    "tag_or_release",
    "workflow_rerun",
    "runner_dispatch",
    "model_api_invocation",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "dependency_install",
    "generated_governance_commit",
    "active_json_rewrite",
    "authority_pr_ready_or_merge",
    "target_branch_mutation"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    }
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py"
  ],
  "semantic_implementation_contract": {
    "specification": "No source edits. Exact PR1016 head3369e2d3542833e48edac732c69cfa15880c9f2c treeef4ba21e0c0b05b10c050ecdc77c72f51bc94d8f base86844b5bc8e42172f2a39d555fd7053973a01155 sourceDecisiondecision_20260928_issue989_system_runtime_budget_r3_v5. System-authored archivedpartial plus successful tool-free modelcalls2/4/5/6 produceexactfourproductfiles: relay/executor/host/newruntimebudgettest. Supervisoronlyreviews/transfersmodelbytes, no authoredsource. Calls1/3returnednoassistantcontent; notsuccess. Tools exposed/dispatched0. Independent development94runtimebudgetPASS and261regressionsPASS1skip; atomicregressionfailedonprefixandpassedafter. Finalexactheadmandatorychecks/readiness andnaturalCIpendingmustpassbeforeacceptance/attestation/Ready. Keep989OPEN forWindowsSystemDriveresidual and299OPEN forfullOSsandbox; tool-freecontinuationiscontainment, notfullsandboxfix. No deployment/rootdirtyimports. Exactsourcefinalchecks now94PASS,193PASS1skip,68PASS,diffPASS,all5gatesPASS at3369e2d3. Sourcev5preservesexactsystembytesafterv4immutableDecisionCRLFdiffcheckfailure; nofixforward onv4. OldDraft1015andunpublishedconditional1015landingauthoritypreserved andunused. ThisnewauthorityandsourceDecisionuseLF. Natural source/authority CI stillmandatory beforeaction.",
    "completion_boundary": "After source final mandatory checks and target+authority natural CI/Decision/State native diagnostics pass, publish transparent Owner-account COMMENTED exact-head independent supervisor acceptance and existing-format OWNER_LANDING_MERGE_ATTESTATION while targetDraft. Canonical validator must pass. MarkReady once, waitNEWformal landing-state-gate and StateSUCCESS; immediatelyverify main/base/head/CLEAN/requiredCI/reviewthreads/noactivepublication, mergeonce expectedhead methodmerge. Verify mergeparents/tree/main and natural mainCI/State native integrationreceipt before posting partial-completion evidence. Do NOT close Issue989 or299 oranyIssue. No deployment or closure of preserved historical Drafts."
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
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "Unchanged natural CI setup and provider-free checks only."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Only canonical dddd2024/Nerelan exact authority branch push/Draft, PR1016 review/attestation/Ready/expected-head merge and completed Issue990 closure after verification."
    ]
  },
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Only pre-existing/generated ignored local Python scratch; never stage."
  },
  "allowed_commands": [
    {
      "command_id": "pr1016.bootstrap",
      "command": "Commit only this Decision once in fresh exact-base codex/pr1016-delegated-landing-v1-20260928 checkout. Run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre, worktree-publication-readiness using python -m reverse_agent.project_gate SUBCOMMAND --state-dir project_state. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY. Never edit activated Decision or stage generated gates.",
      "phase": "bootstrap",
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation",
        "commit",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required": true,
      "expected_exit_codes": [
        0
      ],
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
      "command_id": "pr1016.validate",
      "command": "Run existing python -B -m pytest tests/test_mainline_landing.py -q -p no:cacheprovider and git diff --check on exact sidecar head. Verify source mandatory checks and system/independent review provenance, target scope and native CI diagnostic.",
      "phase": "validation",
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "unit_test",
        "local_static_check",
        "diff_validation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1016.publish_authority",
      "command": "Push exact authority branch once and create one Draft against locked main. Decision-only sidecar, never Ready/merge. Observe natural authority CI, Decision Preflight and State Gate SUCCESS plus native diagnostic. No reruns or dispatch.",
      "phase": "publication",
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1016.attest",
      "command": "After source and authority checks succeed, fresh-read exact heads/base/Decision digests, blocking review threads, ruleset21023698 and independent ACCEPT. Post one transparent delegated Owner-account COMMENTED review on exact target head. Publish exactly one existing-format OWNER_LANDING_MERGE_ATTESTATION on Draft1016 binding that review, both Decisions, sidecar natural runs, target pre-Ready ordinary State Gate and canonical contexts. Validate with existing read-only false/none validator; no invented schemas or tests bypass.",
      "phase": "final_evidence",
      "execution_surface": "github_control_plane",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1016.ready",
      "command": "Only after valid attestation and no drift, gh pr ready 1016 --repo dddd2024/Nerelan exactly once. Require naturally triggered formal landing-state-gate and ordinary state-gate SUCCESS at exact target head. No rerun, dispatch, conversion cycling or fake context.",
      "phase": "publication",
      "execution_surface": "github_control_plane",
      "operations": [
        "mark_ready",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1016.merge",
      "command": "Immediately verify main/base equal 86844b5bc8e42172f2a39d555fd7053973a01155, target head 3369e2d3542833e48edac732c69cfa15880c9f2c, MERGEABLE/CLEAN, accepted scope, checks and attestation, no concurrent source mutation. gh pr merge 1016 --repo dddd2024/Nerelan --merge --match-head-commit 3369e2d3542833e48edac732c69cfa15880c9f2c once. Verify merged=true, merge parents/tree/main, native mainline receipt and natural main CI/State success. Then post only partial-completion evidence on989; keep989 and299OPEN. No Issue closure. Preserve sidecar Draft and all other Issues/PRs.",
      "phase": "publication",
      "execution_surface": "github_control_plane",
      "operations": [
        "merge",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1016.natural_ci",
      "command": "Observe unchanged natural authority and target/main CI, Decision Preflight and State Gate; no provider calls in tests.",
      "phase": "validation",
      "execution_surface": "ci_only",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "target_pr": 1016,
  "accepted_exact_head_sha": "3369e2d3542833e48edac732c69cfa15880c9f2c",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "workflow_profile": "baseline",
  "source_issues": [
    989
  ]
}
```
