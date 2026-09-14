# Decision Packet — #891 false/none pre-merge attestation closure v2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260914_issue891_false_none_premerge_attestation_r2_v2",
  "round_id": "round_20260914_issue891_false_none_premerge_attestation_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "FALSE_NONE_PREMERGE_ATTESTATION_ENTRYPOINT_CLOSURE",
  "source_issue": 891,
  "parent_issue": 156,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated Agent Owner authoring",
  "approval_basis": "The user explicitly delegated repository Owner execution and requested completion of the highest-priority non-overlapping work. Fresh exact-head audit of closed-unmerged PR892 proved v1 added a correct-looking standalone premerge validator but did not connect it to the real State Gate transition-preflight landing path; natural CI also exposed stale generated command-plan evidence. This fresh v2 corrects the proven entrypoint omission without rewriting v1 history and grants no Ready/Merge.",
  "supersedes_decision_id": "decision_20260914_issue891_false_none_premerge_attestation_r2_v1",
  "superseded_evidence": "PR892 exact head 27e30c65690e86a5f3e46bbe05a8ed6c27fe3904 is CLOSED_UNMERGED_R2_NEGATIVE_IMPLEMENTATION_EVIDENCE. Natural Decision Preflight 522 and State Gate 3093/3094 succeeded; natural CI 1277 failed because tracked command_plan.json remained bound to Issue884. More importantly, semantic audit proved validate_premerge_landing() had no production caller while project_gate._check_landing_authority() returned success immediately for cutover false/none after remote PR binding. No v1 history, commit, check, or review is v2 acceptance; read-only byte/logic inspection is permitted.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "required_branch": "owner/issue891-false-none-attestation-r2-v2",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "workflow_profile": "baseline",
  "semantic_implementation_contract": {
    "specification": "Close the real false/none pre-merge landing path. The production Ready/non-Draft route is State Gate landing-state-gate -> project_gate transition-preflight --event-path -> transition_preflight() -> _check_landing_authority(). Today cutover mode verifies event/base and remote PR/head/base then returns candidate PASS without the existing OWNER_LANDING_MERGE_ATTESTATION. V2 must reuse the existing attestation parser/digest/binding/post-merge semantics and require exactly one valid current Owner landing attestation before that cutover route may continue. The validation must bind exact target PR/head/base, exact unmerged landing-authority Decision/head/base, required exact-head workflow evidence, Owner review and current formal landing-state-gate context. Missing, duplicate, stale, wrong-target, wrong-head/base, wrong-authority or wrong-workflow evidence blocks transition-preflight. Draft/non-landing transition preflight remains unchanged. Legacy mainline-merge-intent behavior remains unchanged. No PR-number-specific exception, second receipt family or weakened post-merge validator.",
    "execution_surface_note": "Decision-only activation/publication uses GitHub control plane. Natural full-checkout Decision Preflight/State Gate must first produce PRE_EXECUTION_AUTHORIZED. Then a clean trusted-worker checkout must generate and commit the current v2 generated governance artifacts before semantic publication, avoiding the v1 stale command-plan CI failure. Semantic authoring and focused tests run on trusted_worker; natural exact-head CI provides final validation. No user-local-specific, provider/model, credential, browser or Windows proof is required.",
    "completion_boundary": "Draft corrective implementation only. PR892 and historical PR886/run34820409545 remain immutable negative evidence. No Ready/Merge under this Decision. A separately authorized landing must later produce a new natural main-push State Gate SUCCESS before current main can be called governance-green."
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
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/transition.py",
    ".github/workflows/state-gate.yml",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/**",
    "frontend/**",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "force_push",
    "rebase",
    "merge",
    "mark_ready",
    "tag_or_release",
    "runner_dispatch",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "browser_execution",
    "workflow_dispatch"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
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
      "Publish only owner/issue891-false-none-attestation-r2-v2 in dddd2024/Nerelan and one Draft against main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. Initial publication is Decision-only. Semantic publication requires PRE_EXECUTION_AUTHORIZED plus one current generated-governance commit produced from a clean trusted checkout. Update only that Draft and bounded Issue891/156 evidence. Never Ready or Merge."
    ]
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/mainline_landing.py", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/project_gate.py", "minimum_risk": "R2"}
  ],
  "allowed_commands": [
    {
      "command_id": "issue891v2.bootstrap",
      "command": "On a fresh clean trusted checkout at exact main d3ffafc8924614f309a8f85b6224137f94b2d8c1 and branch owner/issue891-false-none-attestation-r2-v2, verify the immutable v2 Decision and no unrelated tracked mutation; run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. After PRE_EXECUTION_AUTHORIZED, commit exactly one generated-governance commit containing only current v2 generated artifacts required by the Decision. Do not copy stale startup evidence or reuse PR892 commits/history.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue891v2.implement",
      "command": "Only after v2 PRE_EXECUTION_AUTHORIZED and the current generated-governance commit, implement the correction in exactly reverse_agent/mainline_landing.py, reverse_agent/project_gate.py, tests/test_mainline_landing.py and tests/test_project_gate.py. Re-materialize logic from first principles/current main plus read-only PR892 evidence; do not cherry-pick or reuse v1 history. Wire the false/none cutover branch of project_gate._check_landing_authority into the existing Owner attestation validator so a real Ready/non-Draft transition-preflight blocks without valid evidence. Preserve exact remote target binding, Draft/non-landing behavior, legacy intent path and unchanged post-merge validation. Add real transition-preflight route regressions, not helper-only tests.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "unit_test", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/mainline_landing.py",
        "reverse_agent/project_gate.py",
        "tests/test_mainline_landing.py",
        "tests/test_project_gate.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue891v2.validate",
      "command": "On the full exact implementation head run python -m pytest tests/test_mainline_landing.py tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_decision_preflight.py -q; git diff --check. Explicitly prove transition_preflight on a Ready/non-Draft false/none event blocks with no/duplicate/stale/wrong Owner attestation and proceeds only with one exact valid attestation; prove a Draft event does not demand landing evidence and legacy intent behavior is unchanged. Natural exact-head CI, Decision Preflight and State Gate must succeed. No rerun/dispatch, deselection or skip may hide a failure.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue891v2.publish",
      "command": "Publish only owner/issue891-false-none-attestation-r2-v2 and one Draft against main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. Decision-only Draft publication is allowed to obtain natural transition preflight. Subsequent pushes must preserve the v2 D->G->S chronology and exact scope. Rebind exact head in the Draft and record bounded evidence on PR/Issues891/156. Never mark Ready or Merge.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue891v2.observe",
      "command": "Fresh-read exact base/head, full changed-path set, natural CI/Decision Preflight/State Gate and real production call chain. Confirm PR892 and run34820409545 remain unchanged negative evidence. Confirm project_gate._check_landing_authority no longer has a cutover early-success path that bypasses OWNER_LANDING_MERGE_ATTESTATION. Same-agent review is not independent acceptance. No Ready/Merge or governance-green main claim until separately authorized landing and a new natural main-push State Gate success.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Goal

Make the real false/none Owner landing entrypoint fail closed before merge on missing or invalid existing-format Owner landing attestation.

## Current evidence

Current main remains `d3ffafc8924614f309a8f85b6224137f94b2d8c1`. PR892/v1 is closed unmerged. Its exact-head audit proved two independent blockers: stale tracked generated authority and, critically, no production caller for its new premerge validator. Current `project_gate._check_landing_authority()` returns success early for false/none cutover after only exact event/base and remote PR/head/base binding.

## Build vs reuse

Reuse the current State Gate transition-preflight route, existing `OWNER_LANDING_MERGE_ATTESTATION`, parser/digest/binding rules, `GitHubRemoteAcceptanceVerifier`, post-merge validator and Git primitives. Add only the missing project-gate connection and tests. No new Gate, receipt family, queue, client, scheduler, database, workflow, dependency or policy engine.

## Implementation scope

After actual v2 pre-execution authorization and current generated-governance commit, exactly four semantic paths:

- `reverse_agent/mainline_landing.py`
- `reverse_agent/project_gate.py`
- `tests/test_mainline_landing.py`
- `tests/test_project_gate.py`

## Stop conditions

Stop on changed main/base, Decision mutation, missing `PRE_EXECUTION_AUTHORIZED`, stale generated-governance identity, scope expansion, mandatory test/check failure, unavailable trusted-worker surface or exhausted commit/publication budget. Never repair v1 or historical merge evidence in place.
