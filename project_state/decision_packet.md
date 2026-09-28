# System-owned direct-session and Windows environment repair, successor v2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260928_issue372_windows_isolation_r3_v2",
  "round_id": "round_20260928_issue372_windows_isolation_r3_v2",
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
  "decision_scope": "DIRECT_SESSION_ENV_CONFINEMENT_AND_989_WINDOWS_RESIDUAL",
  "source_issue": 372,
  "parent_issue": 1010,
  "approved_by": "dddd2024 via explicit delegated Owner authorization",
  "approval_basis": "Owner explicitly authorizes autonomous recovery and all configured APIs, system-only implementation and supervisor independent acceptance. V1 Agnes output repeatedly rejected; only exact system role env and CLI changes retained locally, no product commit/publication. Preserve v1 Draft1018 and worktree. Fresh successor at unchanged main18c5030f; PR1016 mainCI36390503168 SUCCESS native6768/0/0/23 and receipt EMITTED/PASSED. Reuse enabled coding-default exact deepseek-flash/sensenova-6.8-flash-lite via existing trusted relay with no model tools. No Binding/settings mutations. Transfer only reviewed v1 exact system bytes after new activation Draft. System completes all remaining source/tests.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "18c5030fabeb72288ea2de56314579e339995182",
  "activation_base_sha": "18c5030fabeb72288ea2de56314579e339995182",
  "starting_head": "18c5030fabeb72288ea2de56314579e339995182",
  "fresh_base": "18c5030fabeb72288ea2de56314579e339995182",
  "current_main_expected": "18c5030fabeb72288ea2de56314579e339995182",
  "required_branch": "codex/issue372-windows-isolation-system-v2-20260928",
  "workstream_id": "issue372-windows-isolation-system-v2",
  "follows_last_decision_id": "decision_20260928_issue372_windows_isolation_r3_v1",
  "follows_last_round_id": "round_20260928_issue372_windows_isolation_r3_v1",
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_child_environment_isolation.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_child_environment_isolation.py"
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
    "specification": "System implements explicit minimal childenv admission for ordinarynoBindingCLI, direct sequentialplanner/coder/reviewer andserver, andauthnone/external_cli_session/account_login. Never iterate/copy arbitraryparentenv orinheritimplicitprocessenv. PreservefixedOpenCodeflags androle/providerconfig. Use repository existingaccountauthnonsecretlocationallowlist ascompatibilityprecedent; justify mode-specific subset, no arbitrarysecret/proxy forwarding. Binding/relay remainsminimallyconfined; onlyexplicit989WindowsSystemDrive/PATHEXTvalidationresidualmaychangeBindingenv. EnsuretypedvalidSystemDriveavailable/derivedfromvalidSystemRootonWindows; missing/invalidPATHEXT handlingpreserves997safeextensiondiscovery andrejectsunsafecontrol/pathinjection. Preservemerged989lifetime/980evidence. Replaceobsolete testdirectauthenticatedparentmarkersassertion withstrongersecretconfinementcoverage; do notdeleteacceptedregressions. Adddeterministic guardedMapping(noitems/iteration),sentinelGH/provider/cloud/package/passwordexclusion,realCLI/serverkwargs androles/authmodes/safetyconfig coverage. No rawenvvaluesinstore/events/errors. ActualWindowsknownGit --version andknowncmd/PowerShellNoProfile fixedread-onlycommands inpytest-ownedtemp verifyminimalenvandSystemDriveexpansion,noliteralSystemDrivecachepath. No realOpenCode/OAuth/credentialstoretest,model/providercallsintests ordependencyinstall. No frontend/TaskStore/coordinator/credentialrelay redesign. Threeproductpaths only; systemauthorsallbytes through8tool-freemaxcalls,0autoretry,600sectimeout/no spendcap; supervisorvalidatesstrictallowlist/nonlinks/exactoldtextandreviewsbeforefixedtests.",
    "completion_boundary": "Onefinalproductcommit/twopushes/oneDraft. Exactheadfocusedandfullplatformproviderfreechecks,diff,gates,naturalCI andindependentacceptance. No source-stageReady/merge/closure/deployment. Laterseparatelandingmayclose372and989onlyafteralltheirresidualproofs andmainreceipt/CI;299fullOSsandboxstaysOPEN. NoTaskAPInativeverificationclaim forsupervisedtextinference."
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
      "Read public Binding identity; use existing enabled coding-default with connection deepseek-flash and model sensenova-6.8-flash-lite. Existing trusted ModelProfileStore/OSvault/relay resolves credential at point of use; no raw secret read/output/export. Max8 text-only calls,600sec each,0 tools/dispatch/automatic retry. No Binding/Connection/key mutations. Approved provider-free tests including loopback and known Git/Windows read-only temp proof allowed."
    ],
    "github_control_plane_network_exceptions": [
      "Canonical exact branch activation/implementation pushes and one Draft; descriptions only. No Ready/merge/tag/release under source stage."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue372v2.bootstrap",
      "command": "Fresh exactbase 18c5030fabeb72288ea2de56314579e339995182 checkout F:\\Nerelan-issue372-system-v2-20260928 branchcodex/issue372-windows-isolation-system-v2-20260928;writeimmutableDecisionUTF8LFoneactivationcommit; existingstartup-snapshot/transition-command-plan/transition-lint/transition-preflight --modepre/worktree-publication-readiness andgitdiffcheckbaseHEAD. FirstDraftbeforeproductchanges; neverstagegeneratedgates.",
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
      "command_id": "issue372v2.runtime",
      "command": "No runtime restart/deployment or active OpenCodeTask. Read public Binding identity; use existing enabled coding-default with connection deepseek-flash and model sensenova-6.8-flash-lite. Existing trusted ModelProfileStore/OSvault/relay resolves credential at point of use; no raw secret read/output/export. Max8 text-only calls,600sec each,0 tools/dispatch/automatic retry. No Binding/Connection/key mutations. Approved provider-free tests including loopback and known Git/Windows read-only temp proof allowed.",
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
      "command_id": "issue372v2.system",
      "command": "AfteractivationDraft up to8projectnative text-only SenseNova Flash-Lite calls, noOpenCodeTask/modeltools/dispatch. Promptselectedexactsourceandapprovedrequirements. ModelreturnsJSONedits only; allow exactlythreeproductpaths, oldtextunique, newfileonlyifdeclaredabsent, rejectlinks/reparse/absolute/traversal/ADS/unlisted/commands. Supervisortransfers exactmodelbytesonly,review/developmenttests,onefinalproductcommit. After activation Draft transfer exact reviewed v1 role-helper and CLI-only system edits; no other v1 proposal accepted.",
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
        "tests/platform_v1/test_opencode_executor.py",
        "tests/platform_v1/test_child_environment_isolation.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue372v2.checks",
      "command": "Developmentchecks/fixesbeforefreeze; finalexacthead python -B -m pytest tests/platform_v1/test_child_environment_isolation.py -q -p no:cacheprovider; python -B -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py tests/platform_v1/test_execution_runtime_budget.py -q -p no:cacheprovider; python -B -m pytest tests/platform_v1 -q -p no:cacheprovider; git diff --check 18c5030fabeb72288ea2de56314579e339995182 HEAD. Providerfree only, syntheticsentinels/fakeprocess exceptexplicitfixedWindowsGit/cmd/PowerShell read-only temp proofs. Beforestagecachedstartupreadiness;aftercommitall5gatesagain. Mandatoryfailurestopspublicationnofixforward.",
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
      "command_id": "issue372v2.publish",
      "command": "Atmost2pushesactivation/final exactbranchcodex/issue372-windows-isolation-system-v2-20260928 andoneDraftagainstmain@18c5030fabeb72288ea2de56314579e339995182;rebindexactheadbody. Requireallchecks/PUBLICATION_READY/freshbase/scope. NoReady/merge/closure/historyrewrite.",
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
      "command_id": "issue372v2.ci",
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
      "command_id": "issue372v2.audit",
      "command": "Independent supervisor source/sink/compatibilityreview, actualminimalenvpositivecontrols andsentinelnegatives, bothtransports+ordinaryroles,Windowsproof. No modelselfacceptance orOSsandboxclaim. Distinguishmainline/source fromdirtylocalhost.",
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
      1015,
      1017,
      1018
    ],
    "policy": "Preserve all prior PRs/worktrees, root edits/manual settings. V1 source remains incomplete/unaccepted, no further model calls there. PR1016 mainCI and receipt verified. No deployment or user Binding changes. Agnes returned unusable broad patches; reuse SenseNova tool-free only; #299 remains unresolved."
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
    "tests/platform_v1/test_trusted_host_lifecycle.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/platform_v1/test_execution_runtime_budget.py"
  ],
  "source_issues": [
    372,
    989
  ],
  "required_provider_free_checks": [
    "python -B -m pytest tests/platform_v1/test_child_environment_isolation.py -q -p no:cacheprovider",
    "python -B -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py tests/platform_v1/test_execution_runtime_budget.py -q -p no:cacheprovider",
    "python -B -m pytest tests/platform_v1 -q -p no:cacheprovider",
    "git diff --check 18c5030fabeb72288ea2de56314579e339995182 HEAD"
  ]
}
```
