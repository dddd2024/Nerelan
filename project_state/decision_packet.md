# A2b-2a — immutable source-object binding

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260930_issue1043_exact_source_r2_v1","round_id":"round_20260930_issue1043_exact_source_r2_v1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "A2B_EXACT_SOURCE_OBJECT_BINDING",
  "source_issue": 1043,
  "parent_issue": 379,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner next-round request in this conversation",
  "approval_basis": "The user requests the next task under #1010. A2b-2 needs protected verifier/source identity. This bounded prerequisite hardens existing remote file reads rather than introducing a new verifier. Hash-verified baseline github_remote_verifier.py a84be31b991a58ea380812d6c5278d09acfeaf91 accepted mutable refs and incorrect path/object/type/size metadata when simulated Contents bytes matched the digest. Existing mainline callers already use the two affected methods for committed authority reads. GitHub Git-data commit/tree/blob APIs provide exact regular-file identity without Contents symlink dereferencing. Explicitly migrate only the existing _verify_contents_payload HTTP fixture to the new read protocol while preserving all test expectations and cases. Source work starts only after actual PRE_EXECUTION_AUTHORIZED. ChatGPT is the delegated author, not an independently accepted system runtime. Preserve #1042 and its different-method patch; no other task takeover.",
  "risk_tier": "R2", "authorized_risk_tier": "R2", "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20260930-exact-source-binding-r2-v1",
  "fresh_worktree_creation_required": false, "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true, "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true, "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight","transition_reconcile","worktree_publication_readiness"],
  "decision_activation_commit_limit": 1, "product_change_commit_limit": 5,
  "generated_governance_commit_limit": 0, "normal_push_attempt_limit": 7,
  "draft_pr_creation_limit": 1, "mark_ready_attempt_limit": 0, "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0, "runner_dispatch_limit": 0, "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0, "provider_network_call_limit": 0, "credential_access_limit": 0,
  "pr_creation_allowed": true, "issue_comment_allowed": true, "pull_request_comment_allowed": true,
  "merge_allowed": false, "mark_ready_allowed": false, "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false, "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false, "auto_merge_allowed": false, "force_push_allowed": false,
  "rebase_during_execution_allowed": false, "dependency_install_allowed": false,
  "live_provider_access_allowed": false, "credential_access_allowed": false,
  "local_browser_execution_allowed": false, "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false, "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false, "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false, "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "In existing GitHubRemoteAcceptanceVerifier replace only verify_ref_file_sha256 and load_ref_file_bytes internals with a shared bounded exact Git-data reader. Validate full lowercase commit SHA and safe exact path/repository before I/O. Read actual commit and nonrecursive trees, reject missing/truncated/duplicated/malformed entries and symlink/submodule traversal. Require final regular blob mode100644/100755, actual commit/tree/blob identity, genuine integer sizes, strict base64, bounded decoded bytes and computed Git object hashes. Recompute tree hashes from canonical entries rather than treating display paths as proof. Keep caller-supplied expected SHA256 comparison; return observed identity with existing verified/bytes/sha256 fields as applicable. Never insert path text into API URLs, resolve mutable refs, follow Contents symlinks or fall back after errors. Bounds:32 path components,10000 entries per tree,1MiB file. Existing authenticated read-only transport remains the trust boundary; no claim of commit-signature verification or that a workflow actually executed the read bytes.",
    "test_fixture_migration": "In tests/test_mainline_landing.py only adapt _verify_contents_payload to supply valid synthetic commit/tree/blob transport responses around the unchanged payload under test. Preserve all original test functions, assertions, expected outcomes, whitespace/base64/empty-content and digest-mismatch cases. No test removal, skip, deselection, relaxed assertion or general monkeypatch. The test file's original base blob is da24acccc929db37860a85e8f6bebdc6e3790a2c.",
    "reuse": "Existing remote verifier, standard Git object identity, authenticated REST transport and current mainline consumers; no new gate/receipt/authority schema, store, framework or dependency. Add dedicated blocking Platform V1 tests and one scoped document.",
    "execution_surface_note": "Natural GitHub CI supplies full checkout and existing gates. Isolated trusted-worker partial-source tests may use actual Git objects and fixed Git subprocesses in disposable test repositories with disclosed HTTP doubles. No user PC, live provider/model, credential discovery or repository-setting mutation. Trusted-worker network has no exception. Read-only canonical GitHub observation uses the already connected control plane.",
    "completion_boundary": "One Draft, four exact product paths, actual preflight before implementation. Source identity correctness is not protected execution, independent acceptance, complete dependency closure, automatic merge or completed A2. Preserve other candidates and record their CI status separately. No Ready, merge, closure or deployment."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"], "bootstrap_exception_commands": [],
  "allowed_mutated_paths": ["project_state/decision_packet.md","project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json","reverse_agent/github_remote_verifier.py","tests/platform_v1/test_exact_source_binding.py","tests/test_mainline_landing.py","docs/exact-source-binding.md"],
  "authorized_risk_paths": ["project_state/decision_packet.md","project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json","reverse_agent/github_remote_verifier.py","tests/platform_v1/test_exact_source_binding.py","tests/test_mainline_landing.py","docs/exact-source-binding.md"],
  "generated_artifact_paths": ["project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "reference_paths": ["AGENTS.md","docs/agents/governance-reference.md","reverse_agent/mainline_landing.py",".github/workflows/ci.yml"],
  "forbidden_mutated_paths": ["AGENTS.md","docs/agents/**",".github/**",".codex-skills/**","reverse_agent/control_plane/**","reverse_agent/platform_v1/**","reverse_agent/model_access/**","reverse_agent/project_gate.py","reverse_agent/mainline_landing.py","frontend/**","project_state/rounds/**","project_state/mainline_merge_intents/**","launch_nerelan.bat","launch_reverse_agent.bat","pyproject.toml","requirements*.txt","**/secrets/**","**/.env"],
  "forbidden_operations": ["direct_push_main","auto_merge","force_push","rebase","squash","amend","history_rewrite","mark_ready","merge","workflow_rerun","workflow_dispatch","runner_dispatch","model_api_invocation","provider_network_call","credential_access","unknown_binary_execution","external_reverse_tool_invocation","destructive","tag_or_release","dependency_install","local_browser_execution","generated_governance_commit"],
  "capability_policy": {
    "runner_dispatch_allowed":false,"workflow_dispatch_allowed":false,"model_api_invocation_allowed":false,"external_reverse_tool_invocation_allowed":false,"unknown_binary_execution_allowed":false,"destructive_operations_allowed":false,"network_access_default_allowed":false,"direct_push_to_main_allowed":false,"force_push_allowed":false,"rebase_during_execution_allowed":false,"tag_or_release_allowed":false,"merge_allowed":false,"remote_observation_read_only_allowed":true,
    "local_network_exceptions":[],"trusted_worker_network_exceptions":[],"user_local_network_exceptions":[],
    "ci_network_exceptions":["Unchanged natural CI dependency setup and provider-free tests only; no rerun or dispatch."],
    "github_control_plane_network_exceptions":["Only canonical repository observation, this exact source branch and one Draft against the locked main. Decision-only activation first, source publication after actual preflight. Update #1043/#1010/#379/#653 and #1041 final CI observation. No settings/ruleset/workflow mutation, Ready, merge, release, deployment or other-source takeover."]
  },
  "path_risk_floor": [{"pattern":"project_state/**","minimum_risk":"R2"},{"pattern":"reverse_agent/github_remote_verifier.py","minimum_risk":"R2"}],
  "allowed_commands": [
    {"command_id":"source.bootstrap","command":"Verify exact base and Decision-only activation; existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight and worktree publication readiness on an authorized trusted checkout. Unchanged natural CI supplies full-checkout gates. Require actual PRE_EXECUTION_AUTHORIZED. No hand-written or committed generated gates.","phase":"bootstrap","required":false,"expected_exit_codes":[0],"execution_surface":"trusted_worker","operations":["code_read","local_static_check","command_plan_generation"],"network_access":false,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"]},
    {"command_id":"source.implement","command":"After actual preflight implement the two existing file-read methods and shared exact Git-object reader, new tests/doc and only the named existing HTTP fixture adaptation. Preserve all unrelated methods and test assertions. No alternate authority or imported candidate patch.","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"trusted_worker","operations":["source_edit","unit_test","local_static_check"],"network_access":false,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":["reverse_agent/github_remote_verifier.py","tests/platform_v1/test_exact_source_binding.py","tests/test_mainline_landing.py","docs/exact-source-binding.md"],"produced_artifacts":[]},
    {"command_id":"source.validate","command":"Run python -m pytest tests/platform_v1/test_exact_source_binding.py -q; python -m pytest tests/test_mainline_landing.py -q; existing natural CI blocking tests/platform_v1; git diff --check. Real disposable Git plus disclosed HTTP doubles. No model/provider, new skip/deselect or changed assertions. Partial-source results remain supplemental to full CI.","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"ci_only","operations":["unit_test","local_static_check","diff_validation"],"network_access":false,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"source.publish","command":"Publish only exact branch and one Draft with current exact head; update #1043/#1010/#379/#653 and prior #1041 CI. Preserve other owners, failed records and review-wait candidates. No Ready, merge, closure or deployment.","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"github_control_plane","operations":["push","draft_pr","pull_request_comment","issue_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"source.observe","command":"Read exact main/head/diff and natural checks. Confirm immutable Decision and scoped fixture-only migration. Distinguish source identity, actual tests, independent acceptance and landing; update progress after completion or blockage.","phase":"final_evidence","required":true,"expected_exit_codes":[0],"execution_surface":"remote_observation","operations":["read_only_audit","code_read"],"network_access":false,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "issue_completion_close_allowed": []
}
```

Source-object identity is a prerequisite, not proof that the protected verifier executed those bytes. Independent workflow/runtime/dependency and reviewer/promotion identity enforcement remain separately scoped. No automatic-merge permission is created.
