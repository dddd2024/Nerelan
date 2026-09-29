# EBA-1a — functional test-report consistency

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260930_issue1037_functional_report_r2_v1",
  "round_id": "round_20260930_issue1037_functional_report_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "EBA_1A_EXISTING_FUNCTIONAL_REPORT_CONSISTENCY",
  "source_issue": 1037,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner request in the current conversation",
  "approval_basis": "The user requests a GitHub priority table, immediate per-task updates and all currently feasible work. Index #1010 A1 selects the smallest reproduced functional-evidence residual. Exact base functional_validation.py blob84a9c3c04e0425b6ec4ed55f7848d102158ee49d was materialized and hash-verified. A disclosed partial-source probe showed eight contradictory report records still project VERIFIED when accepted=True, despite zero/all-skipped/failed/inconsistent/Boolean/negative counts or unsupported format. This bounded delegated implementation repairs the existing predicate, not a new verifier platform. GitHub CI is the full-checkout surface; the isolated worker cannot resolve GitHub. ChatGPT authors this source and cannot claim independent acceptance. No claim that a hostile external actor can write TaskStore, and no claim that consistency checking establishes authentic test provenance. Preserve existing owners #120/#1024, #1031, #1030/#1032 and review-wait #1036.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20260930-functional-report-consistency-r2-v1",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 5,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 7,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
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
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Add a small shared report-consistency predicate inside existing functional_validation.py and consume it from the report parser and functional_evidence. Report tests/passed/failed/skipped must be actual nonnegative integers, not bool/float/string; totals agree, at least one passing test and zero failed tests. Accept only supported junit/tap formats and match python_pytest to junit and npm_test to supported junit/tap. On projection, accepted must still be exactly True; recomputation cannot upgrade explicit False/missing/nonboolean flags. Reject duplicated/contradictory TAP summary keys and unknown parser report kinds instead of last-value-wins. Preserve valid mixed pass/skip behavior, existing result shape, all exact identity/contract/execution bindings and fixture-only distinction. Add negative/control, real fixed pytest/JUnit process and disk-SQLite/Task/Run projection regression tests, reusing existing fixtures with disclosed model/binding doubles. Update existing functional-validation documentation with the precise consistency and non-provenance boundary. No changes to subprocess commands/environment, catalog/version/digest, resume/claim/lease algorithms, Task/Goal lifecycle, existing tests, publication, permissions or unrelated parsing surfaces.",
    "reuse": "Existing functional contracts, results, digests, report parser, TaskStore, Task/Run/Goal projections and provider-free fixture machinery. No new runtime, schema family, database, signed receipt, authority engine, generic judge, workflow or dependency.",
    "execution_surface_note": "GitHub-first/CI-first. Source starts only after actual PRE_EXECUTION_AUTHORIZED on the Decision-only Draft. Unchanged natural CI on a full checkout supplies transition and existing blocking Platform V1 tests. Partial-source worker tests are supplementary and explicitly not integration evidence. Fixed provider-free test subprocesses and temporary Git/SQLite workspaces are allowed; no user-local host, provider, credential or model access.",
    "completion_boundary": "One Draft, three exact product/test/doc paths. Original gate/claim/identity behavior is not relaxed. All mandatory applicable exact-head CI must pass; independent acceptance and landing are separate. Preserve failed evidence, update #1037 and #1010 immediately after source/test/blockage transitions. No Ready, merge, Issue closure, deployment or broad autonomous-completion claim."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/functional_validation.py",
    "tests/platform_v1/test_functional_report_consistency.py",
    "docs/functional-validation.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/functional_validation.py",
    "tests/platform_v1/test_functional_report_consistency.py",
    "docs/functional-validation.md"
  ],
  "generated_artifact_paths": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"],
  "reference_paths": ["AGENTS.md", "docs/agents/governance-reference.md", "tests/platform_v1/test_functional_execution.py", "tests/platform_v1/test_artifact_handoff.py", ".github/workflows/ci.yml"],
  "forbidden_mutated_paths": ["AGENTS.md", "docs/agents/**", ".github/**", ".codex-skills/**", "reverse_agent/control_plane/**", "reverse_agent/model_access/**", "reverse_agent/project_gate.py", "reverse_agent/mainline_landing.py", "reverse_agent/github_remote_verifier.py", "reverse_agent/platform_v1/run_store.py", "reverse_agent/platform_v1/durable_execution.py", "reverse_agent/platform_v1/task_execution.py", "reverse_agent/platform_v1/task_service.py", "reverse_agent/platform_v1/run_read_model.py", "reverse_agent/platform_v1/goal_service.py", "frontend/**", "project_state/rounds/**", "project_state/mainline_merge_intents/**", "launch_nerelan.bat", "launch_reverse_agent.bat", "dev-up.ps1", "dev-down.ps1", "pyproject.toml", "requirements*.txt", "**/secrets/**", "**/.env"],
  "forbidden_operations": ["direct_push_main", "auto_merge", "force_push", "rebase", "squash", "amend", "history_rewrite", "mark_ready", "merge", "workflow_rerun", "workflow_dispatch", "runner_dispatch", "model_api_invocation", "provider_network_call", "credential_access", "unknown_binary_execution", "external_reverse_tool_invocation", "destructive", "tag_or_release", "dependency_install", "local_browser_execution", "generated_governance_commit"],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": ["Unchanged natural repository CI dependency setup and provider-free validation only. No new workflow, rerun or dispatch."],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": ["Publish only owner/20260930-functional-report-consistency-r2-v1 and one Draft against main@9092911f41a089e249f27c883526904299be1d17. Decision-only activation first; three exact product paths only after actual preflight. Read actual checks and update #1037/#1010/#653 progress records. No Ready, merge, settings change, release, deployment or other-owner task mutation."]
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}, {"pattern": "reverse_agent/platform_v1/functional_validation.py", "minimum_risk": "R2"}],
  "allowed_commands": [
    {
      "command_id": "report.bootstrap",
      "command": "Verify exact base and Decision-only activation. Existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and publication readiness run on an authorized trusted checkout when available; unchanged natural CI supplies full-checkout gate evidence. Require actual PRE_EXECUTION_AUTHORIZED before product work. Never fabricate or commit generated gates.",
      "phase": "bootstrap", "required": false, "expected_exit_codes": [0], "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [],
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"]
    },
    {
      "command_id": "report.implement",
      "command": "After actual preflight implement only the existing parser/projection consistency repair, its new provider-free regression file and the existing functional-validation documentation. Reuse exact base bytes and dependencies. Preserve every unrelated line and existing assertion; no other task or authority changes.",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "trusted_worker",
      "operations": ["source_edit", "unit_test", "local_static_check"], "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": ["reverse_agent/platform_v1/functional_validation.py", "tests/platform_v1/test_functional_report_consistency.py", "docs/functional-validation.md"], "produced_artifacts": []
    },
    {
      "command_id": "report.validate",
      "command": "Run python -m pytest tests/platform_v1/test_functional_report_consistency.py -q; python -m pytest tests/platform_v1/test_functional_execution.py tests/platform_v1/test_artifact_handoff.py -q; existing natural CI blocking tests/platform_v1; git diff --check. Verify positive and malformed reports, fixed pytest subprocess output, and real SQLite/read-model composition with model/binding doubles disclosed. No provider calls, new test skips or weakened existing assertions. Keep partial-source results distinct from full CI.",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "report.publish",
      "command": "Publish the exact allowed branch and one Draft after preflight, rebind its exact head, record actual CI and status in #1037/#1010/#653. Preserve other tasks and historical evidence. No Ready, merge, closure or deployment.",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "report.observe",
      "command": "Fresh-read source/base, complete scoped diff, natural exact-head CI and immutable Decision. Report real results and unavailable checks. Author self-review is not independent acceptance. Update priority row and next action immediately; keep Draft until separately valid acceptance/landing authority exists.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Claim ceiling

This repair enforces consistency of existing functional reports. It does not make executor-produced reports unforgeable, prove all task obligations, grant merge rights or deploy the full autonomous system. Those remain separately scoped under #653/#379/#118. All source-stage evidence is exact-head and self-review is not independent acceptance.
