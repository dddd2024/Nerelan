# Decision Packet — EBA-0 truthful authorization and preapproval diagnostics

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260929_issue1033_evidence_bound_autonomy_r2_v1",
  "round_id": "round_20260929_issue1033_evidence_bound_autonomy_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "EBA_0_TRUTHFUL_AUTHORIZATION_AND_PREAPPROVAL_DIAGNOSTICS",
  "source_issue": 1033,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner implementation request in the current conversation",
  "approval_basis": "User requests fixing evidence-bound autonomous work into GitHub and completing all feasible concrete implementation. Preserve existing directions #252/#118/#653/#379. This bounded R2 round repairs authorization-only completion claims, adds a non-authorizing preapproval diagnostic over existing Path-A rules, fixes DeltaObservation head output and documents the phased contract. Current connected user machine is offline and the isolated worker cannot resolve GitHub, so natural GitHub Actions are the full-checkout gate/validation surface. ChatGPT authors this source under delegated authority; do not represent it as Nerelan-runtime-authored or independently accepted. The historical #1026 candidate is not imported and no other active task is taken over.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20260929-evidence-bound-autonomy-r2-v1",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 8,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 10,
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
    "specification": "In existing path_a.verify_path_a_r1 keep product_accepted and implementation_complete false for all authorization-only stages, preserving existing authority, exact identity, risk, command and selection semantics. In write_task_check_outputs bind emitted exact_head_sha to DeltaObservation.head_sha rather than the undefined local head_sha. Add work_item_preflight.py as a read-only diagnostic API and module CLI reusing the existing Path-A parser/digest/command/path-risk/check mapping. It validates bounded UTF-8 candidate bodies, unambiguous required sections, forbidden command metacharacters, safe bounded paths, declared R1 path-risk floors, branch/base/SHA shape and optional caller-supplied observed base/occupied paths. Optional Draft snapshot validation reuses parse_snapshot and verifies exact body/repository/branch/base ties. Embedded snapshots, malformed/duplicate sections, conflicting observations and unknown inputs fail closed with bounded stable diagnostics. APPROVAL_READY is static structural readiness only and always carries approval/execution/Ready/merge/product-completion authority false. No commands from the Issue are run. Preserve existing exact body digest/reapproval policy; no semantic-digest migration, automatic approval, base refresh or new authority engine. Add blocking provider-free regressions and a scoped evidence-bound-autonomy design/acceptance document.",
    "execution_surface_note": "GitHub-first and CI-first. Natural State Gate generates the command plan and preflight using the unchanged base implementation before semantic publication. Partial exact-file tests in an isolated worker may supplement but never replace full-checkout exact-head CI. No live model/provider, credentials, user-local runtime, dependency or workflow mutation.",
    "completion_boundary": "One Draft, up to eight bounded implementation commits. Product source starts only after actual PRE_EXECUTION_AUTHORIZED from the Decision-only Draft. Existing denial cases remain effective. New regressions run in tests/platform_v1, which current CI treats as blocking. Final exact-head CI and independent review are separate; self-review is not independent acceptance. No Ready, merge, Issue closure or deployment. This foundation does not claim full autonomous operation or universal verification."
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
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/work_item_preflight.py",
    "tests/platform_v1/test_evidence_bound_autonomy.py",
    "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/work_item_preflight.py",
    "tests/platform_v1/test_evidence_bound_autonomy.py",
    "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"
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
    "tests/test_path_a_gate.py",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/task_store.py",
    ".github/workflows/ci.yml"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/platform_v1/**",
    "reverse_agent/model_access/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "frontend/**",
    "tests/test_path_a_gate.py",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "launch_nerelan.bat",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "dev-down.ps1",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "squash", "amend", "history_rewrite",
    "mark_ready", "merge", "workflow_rerun", "workflow_dispatch", "runner_dispatch",
    "model_api_invocation", "provider_network_call", "credential_access", "unknown_binary_execution",
    "external_reverse_tool_invocation", "destructive", "tag_or_release", "dependency_install",
    "local_browser_execution", "generated_governance_commit"
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
    "ci_network_exceptions": ["Unchanged natural repository CI dependency setup and provider-free tests only; no new workflow, rerun or dispatch."],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": ["Canonical exact branch owner/20260929-evidence-bound-autonomy-r2-v1 and one Draft against main@9092911f41a089e249f27c883526904299be1d17. Initial write is Decision-only. Semantic publication requires actual PRE_EXECUTION_AUTHORIZED. Write only approved paths and task/parent progress records. No Ready, merge, auto-merge, settings changes, tag or release."]
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/control_plane/**", "minimum_risk": "R2"}
  ],
  "allowed_commands": [
    {
      "command_id": "eba0.bootstrap",
      "command": "Verify exact base and Decision-only activation. Existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and publication readiness may be produced by the unchanged natural GitHub workflows on a full checkout. No generated gate file is hand-written or committed. Wait for actual PRE_EXECUTION_AUTHORIZED before semantic source edits.",
      "phase": "bootstrap", "required": false, "expected_exit_codes": [0], "execution_surface": "ci_only",
      "operations": ["code_read", "local_static_check", "command_plan_generation"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [],
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"]
    },
    {
      "command_id": "eba0.implement",
      "command": "After actual PRE_EXECUTION_AUTHORIZED implement only the exact EBA-0 claim-ceiling, DeltaObservation output fix, read-only Work Item preflight, provider-free regressions and architecture document. Reuse Path-A rules and existing evidence ownership. Do not import historical branches, change approval policy or alter active runtime/frontend work.",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "trusted_worker",
      "operations": ["source_edit", "unit_test", "local_static_check"], "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": ["reverse_agent/control_plane/path_a.py", "reverse_agent/control_plane/work_item_preflight.py", "tests/platform_v1/test_evidence_bound_autonomy.py", "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"],
      "produced_artifacts": []
    },
    {
      "command_id": "eba0.validate",
      "command": "On the exact head run python -m pytest tests/platform_v1/test_evidence_bound_autonomy.py tests/test_path_a_gate.py -q; python -m pytest tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_decision_preflight.py -q; git diff --check. Existing natural CI additionally runs all blocking tests/platform_v1. Tests invoke no provider/network/credential access and no submitted Issue commands. Report partial local checks separately from full CI; preserve all existing assertions and skip policy.",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "eba0.publish",
      "command": "Publish exact approved branch and one Draft PR through canonical GitHub tools. Decision-only bootstrap first; semantic tree publication only after preflight. Rebind exact head in Draft description after implementation and record progress on #1033/#653/#252/#1010. Preserve #1024/#1031/#1032 and historical sidecars. No Ready, merge, Issue closure or deployment.",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "eba0.observe",
      "command": "Fresh-read exact main/head and complete source diff, natural State Gate/Decision Preflight/CI and new regression outcomes. Preserve failed checks as evidence. Record author self-review separately; never present it as independent acceptance. The work remains Draft unless a future separate landing authority and independent acceptance are obtained.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Build / reuse and acceptance

Reuse the existing Path-A parser, digest, command validator, path risk policy and fixed test mapping. Do not add a second authority or evidence store. All authority-only results retain false completion/acceptance claims. Preapproval readiness is advisory and never grants approval or execution. Historical shell-placeholder errors, ambiguous/duplicate sections, invalid paths, sensitive risk floors, stale observed base, occupied paths and snapshot drift must be diagnosed before approval. The output-file head must be the observed DeltaObservation head. No test/model self-report certifies product completion.

## Source-stage limits

Only Decision bootstrap plus the four exact EBA-0 paths may be published. Generated artifacts remain uncommitted observations. No source-stage Ready, merge, scope expansion, credentials, provider calls, user-runtime changes or self-certified independent acceptance. Existing exact authority remains mandatory. Full autonomous delegation, protected verifier infrastructure and end-to-end completion projection are later scoped slices under the existing parent Issues.
