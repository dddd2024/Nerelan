# A2b — required-check producer and exact-commit binding

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260930_issue1041_check_producer_r2_v1","round_id":"round_20260930_issue1041_check_producer_r2_v1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "A2B_REQUIRED_CHECK_PRODUCER_AND_EXACT_COMMIT_BINDING",
  "source_issue": 1041,
  "parent_issue": 379,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via the explicit delegated next-round implementation request in this conversation",
  "approval_basis": "The user requests the next task under the fixed priority table #1010. A2b is next. Source github_remote_verifier.py at main was reconstructed and verified as Git blob a84be31b991a58ea380812d6c5278d09acfeaf91. The actual verify_check_run_contexts method, with disclosed simulated HTTP responses, wrongly accepted foreign or missing App identity, wrong head, empty requirements, incomplete pages and a success masking a failure/pending result. Fresh GitHub reads show Actions App id15368/slug github-actions and required ruleset contexts without integration_id. Repair the existing read-only verifier predicate and document the residual server-ruleset/workflow-source boundary; do not change settings or claim a production attack. Reuse GitHub native check identity and pagination rather than add a framework. ChatGPT is the delegated source author, not an independent acceptance authority. Preserve all previous candidates and other owners.",
  "risk_tier": "R2", "authorized_risk_tier": "R2", "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20260930-check-producer-binding-r2-v1",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight","transition_reconcile","worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 5,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 7,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0, "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0, "runner_dispatch_limit": 0, "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0, "provider_network_call_limit": 0, "credential_access_limit": 0,
  "pr_creation_allowed": true, "issue_comment_allowed": true, "pull_request_comment_allowed": true,
  "merge_allowed": false, "mark_ready_allowed": false,
  "workflow_rerun_allowed": false, "workflow_dispatch_allowed": false, "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false, "auto_merge_allowed": false, "force_push_allowed": false,
  "rebase_during_execution_allowed": false, "dependency_install_allowed": false,
  "live_provider_access_allowed": false, "credential_access_allowed": false,
  "local_browser_execution_allowed": false, "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false, "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false, "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false, "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Repair only verify_check_run_contexts and its narrowly necessary internal constants/helpers inside github_remote_verifier.py. Require bounded nonempty unique context names, exact lowercase Git SHA and a safe repository identity before reads. For the GitHub.com first-party context path, require observed App integer id15368 and slug github-actions; unknown API hosts cannot borrow this policy. The producer is repository-owned policy, never learned from the submitted evidence or a display name. Fetch complete latest-filter check-run pages with a maximum of1000 records, enforce strict count/type/identity and consistent pagination, reject duplicated IDs, wrong-head or wrong-repository check URLs and malformed/truncated/changing observations. No partial-page success. Only a completed success from the expected producer satisfies a required name. Same-name trusted failure/pending/unknown results prevent an older success from hiding conflict. Skipped records never satisfy a context but a separately skipped event does not veto a distinct actual success, preserving current multi-event GitHub workflows; no skipped test is presented as passing. Return actual successful check IDs and scoped diagnostics without new authority. Preserve the existing API signature and all unrelated methods. Add provider-free tests using the actual module, mocked HTTP boundaries and full transport/JSON parsing; no original test, dependency, workflow, ruleset, approval or runtime changes. Document that App identity is not protected workflow-source revision, dependency closure, independent process/reviewer or complete functional acceptance.",
    "reuse": "Existing GitHubRemoteAcceptanceVerifier, read-only REST transport and mainline callers, native check-run app/head/id fields, existing blocking Platform V1 suite. No second verifier framework, authority engine, database, receipt schema or general policy DSL.",
    "execution_surface_note": "Require actual PRE_EXECUTION_AUTHORIZED on the Decision-only Draft before product work. Natural unchanged GitHub CI is the full-checkout gate and integration surface. Hash-verified exact modules may run provider-free tests in the isolated worker; that is not a full local checkout. GitHub reads for observed data use the existing connection. No credential reads or remote state-changing product tests.",
    "completion_boundary": "One Draft and three exact product paths. Original tests remain intact. Required exact-head CI and independent acceptance are separate. No Ready, merge, closure, settings mutation or deployment. Update #1041/#1010 with actual results; record broader A2b residuals under #379/#653. Do not claim complete protected-verifier provenance or automatic merge from this patch."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": ["project_state/decision_packet.md","project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json","reverse_agent/github_remote_verifier.py","tests/platform_v1/test_check_producer_binding.py","docs/check-producer-binding.md"],
  "authorized_risk_paths": ["project_state/decision_packet.md","project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json","reverse_agent/github_remote_verifier.py","tests/platform_v1/test_check_producer_binding.py","docs/check-producer-binding.md"],
  "generated_artifact_paths": ["project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "reference_paths": ["AGENTS.md","docs/agents/governance-reference.md","tests/test_mainline_landing.py","reverse_agent/mainline_landing.py",".github/workflows/ci.yml"],
  "forbidden_mutated_paths": ["AGENTS.md","docs/agents/**",".github/**",".codex-skills/**","reverse_agent/control_plane/**","reverse_agent/model_access/**","reverse_agent/project_gate.py","reverse_agent/mainline_landing.py","reverse_agent/platform_v1/**","tests/test_mainline_landing.py","frontend/**","project_state/rounds/**","project_state/mainline_merge_intents/**","launch_nerelan.bat","launch_reverse_agent.bat","dev-up.ps1","dev-down.ps1","pyproject.toml","requirements*.txt","**/secrets/**","**/.env"],
  "forbidden_operations": ["direct_push_main","auto_merge","force_push","rebase","squash","amend","history_rewrite","mark_ready","merge","workflow_rerun","workflow_dispatch","runner_dispatch","model_api_invocation","provider_network_call","credential_access","unknown_binary_execution","external_reverse_tool_invocation","destructive","tag_or_release","dependency_install","local_browser_execution","generated_governance_commit"],
  "capability_policy": {
    "runner_dispatch_allowed": false, "workflow_dispatch_allowed": false, "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false, "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false, "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false, "force_push_allowed": false, "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false, "merge_allowed": false, "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": ["Unchanged natural CI dependency setup and provider-free tests only. No rerun or dispatch."],
    "trusted_worker_network_exceptions": [], "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": ["Only this exact branch and one Draft against main@9092911f41a089e249f27c883526904299be1d17. Decision-only bootstrap first, three product paths after actual preflight. Canonical repository reads and updates to #1041/#1010/#379/#653 task progress. No Ready, merge, ruleset/settings mutation, release, deployment or other-owner source change."]
  },
  "path_risk_floor": [{"pattern":"project_state/**","minimum_risk":"R2"},{"pattern":"reverse_agent/github_remote_verifier.py","minimum_risk":"R2"}],
  "allowed_commands": [
    {"command_id":"producer.bootstrap","command":"Verify exact base and Decision-only activation. Existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and publication readiness run on an authorized trusted checkout when available; natural unchanged CI provides full-checkout gate evidence. Require actual PRE_EXECUTION_AUTHORIZED; do not fabricate or commit generated gates.","phase":"bootstrap","required":false,"expected_exit_codes":[0],"execution_surface":"trusted_worker","operations":["code_read","local_static_check","command_plan_generation"],"network_access":false,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"]},
    {"command_id":"producer.implement","command":"After actual preflight implement only check-run producer/head/pagination admission in the existing verifier and the new regression/doc paths. Preserve all other methods, old tests and actual authority; do not modify the live ruleset or other candidates.","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"trusted_worker","operations":["source_edit","unit_test","local_static_check"],"network_access":false,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":["reverse_agent/github_remote_verifier.py","tests/platform_v1/test_check_producer_binding.py","docs/check-producer-binding.md"],"produced_artifacts":[]},
    {"command_id":"producer.validate","command":"Run python -m pytest tests/platform_v1/test_check_producer_binding.py -q; python -m pytest tests/test_mainline_landing.py -q; unchanged natural blocking Platform V1 tests; git diff --check. Test positive/negative source identity, correct artifact, nonvacuous requirements, complete multi-page and conflicting observations through actual functions/transport parsing with disclosed HTTP doubles. No new skips, test weakening, provider or live mutation.","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"ci_only","operations":["unit_test","local_static_check","diff_validation"],"network_access":false,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"producer.publish","command":"Publish only the approved branch and one Draft and rebind exact head. Update #1041/#1010/#379/#653 after completed or blocked phases using fresh facts. Preserve existing work/history and disclose author verification, not independent acceptance. No Ready, merge, closure or deployment.","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"github_control_plane","operations":["push","draft_pr","pull_request_comment","issue_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"producer.observe","command":"Read exact head/base, full scoped diff, immutable Decision and natural CI. Retain failed evidence and distinguish partial local tests, full CI and independent acceptance. Keep Draft and update the index.","phase":"final_evidence","required":true,"expected_exit_codes":[0],"execution_surface":"remote_observation","operations":["read_only_audit","code_read"],"network_access":false,"required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "issue_completion_close_allowed": []
}
```

## Scope of proof

Producer identity is a necessary boundary, not proof that an unchanged protected workflow ran, that dependencies are trusted, that reviewers are independent, or that all user requirements were verified. Current live ruleset source pins remain a separately governed configuration task. This source Decision authorizes neither itself nor its candidate for merge.
