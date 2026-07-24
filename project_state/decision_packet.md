```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260724_p1a_current_merge_bound_mainline_validation_v1",
  "round_id": "round_20260724_p1a_current_merge_bound_mainline_validation_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
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
  "follows_last_decision_id": "decision_20260724_stage_a_freeze_baseline_ci_repair_v2",
  "follows_last_round_id": "round_20260724_stage_a_freeze_baseline_ci_repair_v2",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "p1a-current-merge-bound-mainline-validation-v1",
  "source_issue": 20,
  "source_pull_request": 19,
  "program_issue": 18,
  "program_bundle_sha256": "394f02387230710cb158782affc77a11a651819a6e66221fae9ed95912295c97",
  "required_branch": "codex/p1a-current-merge-validation-v2",
  "activation_base_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "frozen_previous_main_sha": "5884cf2abb37945652ef166cf0e78fa24593b0d5",
  "frozen_subject_head_sha": "43418818af61d9be3208d2444fd6ce5120f73fab",
  "frozen_merge_commit_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "frozen_pr11_head_sha": "d500c145a3201f59f90fcb330fc400596fba10b8",
  "frozen_pr19_head_sha": "38a0a934d92e2cb6eef508b2b32ec580d976b058",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json"
  ],
  "bootstrap_exception_commands": [],
  "allowed_commands": [
    {
      "command_id": "status.git_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ]
    },
    {
      "command_id": "gate.transition_lint",
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authority_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.pre_execution",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pre_execution_authorization"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ],
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
    },
    {
      "command_id": "test.integration_baseline",
      "command": "python -m pytest tests/test_integration_baseline.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.current_merge_validation",
      "command": "python -m pytest tests/test_current_merge_validation.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.integration_baseline",
      "command": "python -m reverse_agent.project_gate integration-baseline --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["baseline_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin codex/p1a-current-merge-validation-v2",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml",
    "docs/architecture/main-integration-baseline.md",
    "docs/architecture/current-merge-validation.md",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/integration_baselines/architecture_spine_v1.json",
    "project_state/schemas/integration_baseline.schema.json",
    "project_state/schemas/mainline_integration_receipt.schema.json",
    "reverse_agent/project_gate.py",
    "tests/test_integration_baseline.py",
    "tests/test_current_merge_validation.py"
  ],
  "reference_paths": [
    "project_state/current_state.json",
    "project_state/artifactindex.json",
    "project_state/state_manifest.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "forbidden_mutated_paths": [
    "frontend/**",
    "solve_reports/**",
    "local_reverse_samples/**",
    "training_materials/**",
    "reverse_agent/user_solve_*.py",
    "reverse_agent/strategies/**",
    "project_state/current_state.json",
    "project_state/artifactindex.json",
    "project_state/state_manifest.json",
    "project_state/context/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    ".codex-skills/**",
    ".env",
    "**/secrets/**",
    "**/credentials/**",
    "**/*.exe",
    "**/*.dll",
    "**/*.bin"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "force_push",
    "rebase",
    "destructive",
    "unknown_binary_execution",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "runner_dispatch",
    "bmad_installation"
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
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "git push origin codex/p1a-current-merge-validation-v2"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml",
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/integration_baselines/**",
    "project_state/mainline_receipts/**",
    "project_state/schemas/**",
    "reverse_agent/project_gate.py",
    "tests/test_integration_baseline.py",
    "tests/test_current_merge_validation.py",
    "docs/architecture/main-integration-baseline.md",
    "docs/architecture/current-merge-validation.md"
  ],
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_receipts/**", "minimum_risk": "R2"},
    {"pattern": ".env", "minimum_risk": "R3"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"},
    {"pattern": "**/credentials/**", "minimum_risk": "R3"},
    {"pattern": "**/*.exe", "minimum_risk": "R3"},
    {"pattern": "**/*.dll", "minimum_risk": "R3"},
    {"pattern": "**/*.bin", "minimum_risk": "R3"}
  ],
  "scope_policy": "p1a_current_merge_bound_mainline_validation_only",
  "stop_after_exact_head_ci": true
}
```

# DECISION_PACKET

## Goal

Bind mainline transition checks to the current merge so that a later unrelated
commit on `main` cannot pass merely because an older accepted merge remains in
ancestry. This Decision supersedes PR #19 by combining the Stage A frozen
baseline invariant with a new current-merge validation gate in a single
replacement branch, as required by Issue #20.

The frozen Architecture Spine baseline is:

- previous main: `5884cf2abb37945652ef166cf0e78fa24593b0d5`;
- accepted PR #9 head: `43418818af61d9be3208d2444fd6ce5120f73fab`;
- merge commit: `38de9106d191d6b66d5f878354144817095e7bca`;
- merge tree: exactly equal to the accepted PR #9 head tree;
- PR #11 remains read-only at `d500c145a3201f59f90fcb330fc400596fba10b8`;
- PR #19 frozen audited head: `38a0a934d92e2cb6eef508b2b32ec580d976b058` (kept
  as audit history; this Decision opens a replacement branch rather than
  mutating PR #19).

## Required implementation

1. Preserve the historical `integration-baseline(architecture_spine_v1)` gate
   as an invariant proving the accepted PR #9 integration remains present and
   unchanged.
2. Add a separate `MainlineIntegrationReceipt` schema and a fail-closed
   `current-merge-validation` gate that binds the current `main` HEAD to an
   accepted current-merge receipt. Receipts are selected deterministically by
   HEAD sha (`project_state/mainline_receipts/<merge_commit_sha>.json`), so a
   stale receipt cannot validate a later commit.
3. Main pushes must run both the historical frozen-baseline invariant and the
   current-merge authorization. The current-merge check must fail closed when
   the checked-out HEAD cannot be tied to an accepted current merge receipt.
4. The pre-merge accepted PR head becomes a post-merge receipt through a
   separate R2 merge Decision that records the merge commit, ordered parents,
   trees, exact-head runs, PR, and Decision identity. The receipt is only
   created after the merge is authorised.
5. Add focused tests including the eight required negative cases from
   Issue #20 using hermetic temporary git repositories, plus architecture
   documentation.

## Pre-merge Authorization vs post-merge Receipt responsibilities

- **Pre-merge Authorization** (this Decision, R1/R2 execution): authorizes
  implementation, tests, and publication of the replacement branch. Does not
  authorize merge. The `current-merge-validation` gate is implemented but
  intentionally fail-closes on this branch because no receipt exists for the
  current HEAD (the merge has not happened yet).
- **Post-merge Receipt** (separate R2 merge Decision): after the replacement
  PR is merged, a `MainlineIntegrationReceipt` is committed at
  `project_state/mainline_receipts/<merge_commit_sha>.json` binding the actual
  merge commit. Only then will `current-merge-validation` pass on `main`.

This separation preserves `expected_head_sha` and human R2 approval: the
receipt is only created after the merge is authorised, and the gate only
passes when HEAD exactly matches the recorded merge commit.

## Do not do

Do not modify PR #9, PR #11, or PR #19 branches. Do not mutate solve
artifacts, samples, frontend, reverse-solving logic, dependencies, secrets,
binaries, tags, or releases. Do not execute unknown binaries. Do not push
directly to main, force-push, rebase, squash, or merge under this Decision.
Do not create Trust Layer, Stage C protocol, Web, tool integration, or
unknown-binary execution work.

## Completion

This Decision is complete only when local focused tests pass, the branch is
published in a new Draft PR, and exact-head CI, State Gate, and Decision
Preflight are green. The PR then waits for a separately authorized R2 merge
Decision that will also commit the post-merge `MainlineIntegrationReceipt`.
