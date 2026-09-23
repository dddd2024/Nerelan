# Decision Packet — Issue #120 resume identity binding and auditable write-gate v2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_issue120_resume_identity_receipts_r2_v2",
  "round_id": "round_20260923_issue120_resume_identity_receipts_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "ISSUE120_RESUME_IDENTITY_BOUND_RECEIPTED_WRITE_GATE",
  "source_issue": 120,
  "parent_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit current request to assess the new Issue #120 review concern and fix the project where warranted",
  "approval_basis": "Fresh current-main audit confirms the concern is real: durable runs persist execution_authority_sha/planning_sha, but coordinator claims and budget reservations do not bind those identities, and operation receipts persist only an input digest. An interrupted task can therefore mutate claim/retry/reservation control state before DurableExecutionService later rejects a planning mismatch, and the stored receipt is not sufficient to reconstruct which identities were checked. This v2 successor preserves closed stale PR #979 as historical evidence and authorizes one current-main correction. It grants no Ready/Merge/direct-main publication.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "58d4068f43ca4914b122445685cae410a8fa156e",
  "activation_base_sha": "58d4068f43ca4914b122445685cae410a8fa156e",
  "starting_head": "58d4068f43ca4914b122445685cae410a8fa156e",
  "required_branch": "owner/issue120-resume-identity-receipts-r2-v2-20260923",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight","transition_reconcile","worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 5,
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
    "specification": "Re-anchor the public Resume write-gate from closed stale PR #979 onto current main and strengthen it so resume admission is identity-bound and auditable. Reuse the existing durable run identity, owner window, AutonomyService, PlatformControlStore claim/budget reservation, and operation-receipt tables. Add execution_authority_sha/planning_sha binding to coordinator claims and budget reservations; compare current identities to the durable run inside the same BEGIN IMMEDIATE claim transaction before claim/retry/budget mutation; fail closed on disagreement. Existing legacy active reservations without identity may be bound only by an explicit atomic compatible migration when the durable run exactly matches the current identities, and that migration must be receipted. Extend the existing operation receipt with a bounded non-secret identity snapshot rather than creating a Vestige subsystem or second audit table. Successful resume admission must persist its allow receipt atomically with the claim/reservation before any durable executor/tool re-entry. Denied resume admission must record a deny receipt when the referenced window exists; failure to record an allow receipt must prevent execution. Reuse the same identity-bound claim path for unattended Resume and manual Task API Resume. Preserve DurableExecutionService repository/worktree/HEAD/checkpoint checks.",
    "execution_surface_note": "GitHub-first, provider-free. No live provider/model calls, credentials, dependency installation or user-local machine work. Natural repository workflows provide transition/preflight and exact-head evidence.",
    "completion_boundary": "Draft implementation only. Deterministic tests must prove planning mismatch causes no claim/retry/budget mutation and no executor/tool dispatch; budget-reservation planning mismatch fails closed before dispatch; allow and deny receipts expose bounded checked identity facts; legacy unbound active reservation is only safely rebound when durable/current identities agree; admitted manual and unattended Resume use the identity-bound claim path. No Ready/Merge or Issue closure."
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
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_unattended_coordinator.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_unattended_coordinator.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_run_resume_control.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/model_access/**",
    "frontend/**",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_run_resume_control.py",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main","auto_merge","force_push","rebase","squash","amend","history_rewrite",
    "mark_ready","merge","workflow_rerun","workflow_dispatch","runner_dispatch",
    "model_api_invocation","provider_network_call","credential_access","unknown_binary_execution",
    "external_reverse_tool_invocation","destructive","tag_or_release","dependency_install","local_browser_execution"
  ],
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
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only owner/issue120-resume-identity-receipts-r2-v2-20260923 and one Draft PR against exact main@58d4068f43ca4914b122445685cae410a8fa156e. Initial publication is Decision-only. Semantic publication requires PRE_EXECUTION_AUTHORIZED. Update that Draft and Issue #120 only. Never Ready or Merge."
    ]
  },
  "path_risk_floor": [
    {"pattern":"project_state/**","minimum_risk":"R2"},
    {"pattern":"reverse_agent/platform_v1/control_store.py","minimum_risk":"R2"},
    {"pattern":"reverse_agent/platform_v1/task_service.py","minimum_risk":"R2"},
    {"pattern":"reverse_agent/platform_v1/unattended_coordinator.py","minimum_risk":"R2"}
  ],
  "allowed_commands": [
    {
      "command_id":"issue120v2.bootstrap",
      "command":"On the exact fresh branch/base verify the immutable Decision-only activation; run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and publication-readiness. Natural GitHub workflows may produce the full-checkout evidence. Do not fabricate gates.",
      "phase":"bootstrap","required":false,"expected_exit_codes":[0],"execution_surface":"trusted_worker",
      "operations":["code_read","local_static_check","command_plan_generation"],"network_access":false,
      "required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],
      "produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"]
    },
    {
      "command_id":"issue120v2.implement",
      "command":"After actual PRE_EXECUTION_AUTHORIZED, implement only the identity-bound claim/reservation, existing-receipt identity snapshot, current-main manual Resume write-gate and unattended Resume binding in the exact authorized source/test paths. Reuse current stores/services; no new audit subsystem/table/dependency.",
      "phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"trusted_worker",
      "operations":["source_edit","unit_test","local_static_check"],"network_access":false,
      "required_evidence_source":"repository_state_attestation",
      "allowed_mutated_paths":[
        "reverse_agent/platform_v1/control_store.py",
        "reverse_agent/platform_v1/task_service.py",
        "reverse_agent/platform_v1/unattended_coordinator.py",
        "tests/platform_v1/test_autonomy.py",
        "tests/platform_v1/test_task_service.py",
        "tests/platform_v1/test_unattended_coordinator.py"
      ],"produced_artifacts":[]
    },
    {
      "command_id":"issue120v2.validate",
      "command":"On a full exact-head checkout run python -m pytest -q tests/platform_v1/test_autonomy.py tests/platform_v1/test_task_service.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_run_resume_control.py and git diff --check. Exact-head CI remains mandatory. No provider/model calls, skips or weakened expectations.",
      "phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"ci_only",
      "operations":["unit_test","local_static_check","diff_validation"],"network_access":false,
      "required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]
    },
    {
      "command_id":"issue120v2.publish",
      "command":"Publish only owner/issue120-resume-identity-receipts-r2-v2-20260923 and its single Draft PR against exact main@58d4068f43ca4914b122445685cae410a8fa156e. Rebind exact_head_sha after implementation and record the analysis/answer on Issue #120. Never Ready or Merge.",
      "phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"github_control_plane",
      "operations":["push","draft_pr","pull_request_comment","issue_comment","network_access"],"network_access":true,
      "required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]
    },
    {
      "command_id":"issue120v2.observe",
      "command":"Fresh-read exact base/head, natural State Gate/Decision Preflight/CI and scoped diff. Confirm planning/budget identity disagreement fails before claim/retry/reservation/executor mutation and receipts expose bounded identity evidence. Do not call self-review independent acceptance or Draft landing.",
      "phase":"final_evidence","required":true,"expected_exit_codes":[0],"execution_surface":"remote_observation",
      "operations":["read_only_audit","code_read"],"network_access":false,
      "required_evidence_source":"repository_state_attestation","allowed_mutated_paths":[],"produced_artifacts":[]
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Build vs reuse

```text
REUSE DurableRun execution_authority_sha / planning_sha
REUSE PlatformControlStore coordinator claim + budget reservation transaction
REUSE platform_operation_receipts as the audit trail
REUSE AutonomyService owner-window/capability policy
REUSE DurableExecutionService final repository/worktree/HEAD/checkpoint validation

SELF-DEVELOP only:
  identity columns + compatible migration
  atomic resume-claim identity comparison
  bounded receipt identity snapshot
  manual/unattended resume wiring
  focused regressions

DO NOT create a new "Vestige" subsystem/table, second budget ledger or second authority engine.
```

## Why this improvement is warranted

The existing late DurableExecutionService planning check prevents executor/tool re-entry under a stale plan, but it occurs after the unattended coordinator can already claim the task, increment retry usage and move/reuse a budget reservation. The claim/reservation itself has no planning identity. Existing receipts store only a digest of their input, so later audit cannot reconstruct which authority/planning identities were compared.

Therefore the current state is safer than an unchecked resume, but still not sufficient for a fail-closed identity-bound write-gate.

## Acceptance

1. resume claim compares current authority/planning identity to DurableRun inside the same SQLite claim transaction;
2. planning mismatch causes no claim, retry increment, budget reservation move/create, or executor dispatch;
3. an active reservation bound to another planning identity fails closed;
4. legacy blank identity may only be atomically bound when current and DurableRun identities exactly agree, with an auditable receipt;
5. successful resume claim and its allow receipt are committed together before durable resume;
6. deny receipt records current/stored identity facts when the referenced window exists;
7. receipts expose only bounded non-secret identity values, never prompts/tokens/credentials;
8. both manual API Resume and unattended Resume use the same bound claim semantics;
9. existing DurableExecutionService authority/worktree/HEAD/checkpoint checks remain unchanged;
10. exact-head blocking CI passes.

## Stop conditions

Changed base, Decision mutation, missing PRE_EXECUTION_AUTHORIZED, active overlapping ownership of the same source paths, out-of-scope diff, failed mandatory checks or stale current-main authority stops semantic publication.
