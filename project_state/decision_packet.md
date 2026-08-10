# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260810_state_gate_pr_head_checkout_owner_recovery_v1",
  "round_id": "round_20260810_state_gate_pr_head_checkout_owner_recovery_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": false,
  "owner_recovery_carveout": true,
  "recovery_reason": "Draft PR #160 proved a structural ordinary-R1 bootstrap defect: GitHub pull_request workflows default-checkout the synthetic merge commit while Path-A correctly binds authority to pull_request.head.sha, making workflow_exact_head_mismatch unavoidable before real Path-A evaluation. This narrow recovery repairs only the State Gate checkout seam and does not expand the unresolved general Path-B lifecycle in Issue #156.",
  "workstream_id": "state-gate-pr-head-checkout-owner-recovery-v1",
  "source_issue": 161,
  "parent_issue": 156,
  "blocked_recovery_issue": 159,
  "blocked_product_issue": 151,
  "evidence_pr": 160,
  "evidence_state_gate_run": 31345663992,
  "evidence_state_gate_job": 93327002168,
  "observed_synthetic_merge_sha": "0476a6daa51b8459b1354e25dfbcdc12d0aa04a8",
  "observed_real_pr_head_sha": "de7cdf822bc7ee8c531ed68cfdfe97de5c499bef",
  "observed_error_code": "workflow_exact_head_mismatch",
  "required_branch": "owner/state-gate-pr-head-checkout-fix-authority-v1",
  "starting_head": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "activation_base_sha": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "sanitized_target_branch": "owner/state-gate-pr-head-checkout-fix-v1",
  "risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_commands_forbidden": true,
  "transition_commands_forbidden_reason": "The workflow being repaired is itself part of the authority bootstrap path, and Issue #156 still tracks the unresolved first-class Path-B sidecar/transition lifecycle. This one exact Owner recovery must not recursively depend on the failing lifecycle it is repairing.",
  "required_product_paths": [
    ".github/workflows/state-gate.yml",
    "tests/test_state_gate_exact_head_checkout.py"
  ],
  "required_product_path_count": 2,
  "project_state_paths_in_sanitized_commit": 0,
  "required_behavior": [
    "State Gate pull_request checkout resolves to github.event.pull_request.head.sha",
    "events without pull_request.head.sha retain github.sha fallback",
    "Path-A verifier exact-head semantics remain unchanged",
    "CI synthetic-merge integration behavior remains unchanged",
    "no PR-number-specific exception"
  ],
  "required_tests": [
    "python -m pytest tests/test_state_gate_exact_head_checkout.py tests/test_path_a_gate.py tests/test_control_plane_transition.py tests/test_planning_and_github_adapters.py -q",
    "python -m pytest tests/test_project_gate.py -q",
    "git diff --check"
  ],
  "remote_validation_requirement": "A real Draft PR for the sanitized product branch must demonstrate that State Gate no longer fails workflow_exact_head_mismatch. A later R2/path-risk rejection is not product acceptance but is acceptable evidence that the checkout seam advanced beyond the exact-head contradiction.",
  "final_remote_cas_required": true,
  "planning_head_must_remain": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "branch_creation_allowed": true,
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "normal_push_limit": 1,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "rebase_during_execution_allowed": false,
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "destructive_operations_allowed": false,
  "unknown_binary_execution_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 0,
  "allowed_mutated_paths": [
    ".github/workflows/state-gate.yml",
    "tests/test_state_gate_exact_head_checkout.py"
  ],
  "forbidden_mutated_paths": [
    "project_state/**",
    ".github/workflows/ci.yml",
    ".github/ISSUE_TEMPLATE/**",
    "AGENTS.md",
    "reverse_agent/**",
    "tests/platform_v1/**",
    "tests/test_team_graph.py",
    "docs/**",
    "frontend/**",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    "package.json",
    "package-lock.json"
  ],
  "forbidden_operations": [
    "transition_gate_regeneration",
    "issue159_product_recovery",
    "historical_path_b_transplant",
    "planning_push",
    "main_push",
    "pr_create",
    "merge",
    "mark_ready",
    "reset",
    "clean",
    "restore",
    "stash",
    "rebase",
    "force_push",
    "amend",
    "squash",
    "cherry_pick",
    "tag_or_release",
    "deployment",
    "credential_access",
    "model_api_invocation"
  ]
}
```

## Owner recovery notes

- This Decision authorizes only the two-path #161 State Gate exact-head checkout repair. It does not authorize the broader #156 redesign.
- The authority branch may contain this `project_state/decision_packet.md` commit; the sanitized product branch must start independently from exact planning `5a109df046cf3d8fe74b88fbc049c454ef4d2a53` and must contain no `project_state/**` delta.
- Do not weaken `reverse_agent/control_plane/path_a.py`; the verifier is correct to bind authority to the live PR head.
- Do not modify `.github/workflows/ci.yml`; CI may continue testing the synthetic merge result while State Gate validates the exact PR head.
- Local implementation must stop after one normal non-force push of `owner/state-gate-pr-head-checkout-fix-v1`. Owner will independently audit the exact remote head, create the validation Draft PR, inspect State Gate evidence, and issue any separate landing authority.
- #159/#160 and the frozen #151 worktree remain frozen during this repair. No #151 product mutation is authorized by this Decision.
