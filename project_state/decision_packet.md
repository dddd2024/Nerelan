```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260724_p1a_premerge_authorization_mainline_validation_rework_v2",
  "round_id": "round_20260724_p1a_premerge_authorization_mainline_validation_rework_v2",
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
  "follows_last_decision_id": "decision_20260724_p1a_current_merge_bound_mainline_validation_v1",
  "follows_last_round_id": "round_20260724_p1a_current_merge_bound_mainline_validation_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "p1a-v2-premerge-authorization-mainline-validation-rework",
  "source_issue": 22,
  "program_issue": 18,
  "source_pull_request": 21,
  "frozen_pr21_head_sha": "976fb86021d6e230b1a1b574960c78c8457e8983",
  "program_bundle_sha256": "394f02387230710cb158782affc77a11a651819a6e66221fae9ed95912295c97",
  "required_branch": "codex/p1a-v2-premerge-authorization",
  "activation_base_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "frozen_previous_main_sha": "5884cf2abb37945652ef166cf0e78fa24593b0d5",
  "frozen_subject_head_sha": "43418818af61d9be3208d2444fd6ce5120f73fab",
  "frozen_merge_commit_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "frozen_pr11_head_sha": "d500c145a3201f59f90fcb330fc400596fba10b8",
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
      "command_id": "test.premerge_authorization",
      "command": "python -m pytest tests/test_premerge_authorization.py -q",
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
      "command": "git push origin codex/p1a-v2-premerge-authorization",
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
    "docs/architecture/premerge-authorization.md",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/integration_baselines/architecture_spine_v1.json",
    "project_state/schemas/integration_baseline.schema.json",
    "project_state/schemas/mainline_merge_authorization.schema.json",
    "project_state/schemas/mainline_integration_receipt.schema.json",
    "reverse_agent/project_gate.py",
    "tests/test_integration_baseline.py",
    "tests/test_current_merge_validation.py",
    "tests/test_premerge_authorization.py"
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
      "git push origin codex/p1a-v2-premerge-authorization"
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
    "project_state/mainline_authorizations/**",
    "project_state/mainline_receipts/**",
    "project_state/schemas/**",
    "reverse_agent/project_gate.py",
    "tests/test_integration_baseline.py",
    "tests/test_current_merge_validation.py",
    "tests/test_premerge_authorization.py",
    "docs/architecture/main-integration-baseline.md",
    "docs/architecture/premerge-authorization.md"
  ],
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_authorizations/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_receipts/**", "minimum_risk": "R2"},
    {"pattern": ".env", "minimum_risk": "R3"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"},
    {"pattern": "**/credentials/**", "minimum_risk": "R3"},
    {"pattern": "**/*.exe", "minimum_risk": "R3"},
    {"pattern": "**/*.dll", "minimum_risk": "R3"},
    {"pattern": "**/*.bin", "minimum_risk": "R3"}
  ],
  "scope_policy": "p1a_v2_premerge_authorization_mainline_validation_rework_only",
  "stop_after_exact_head_ci": true
}
```

# DECISION_PACKET

## Goal

Replace the self-referential `MainlineIntegrationReceipt` design (PR #21,
audited as `REWORK_REQUIRED` per Issue #22) with a pre-merge
`MainlineMergeAuthorization` artifact that is committed in the accepted PR
head before merge, and a mainline validation gate that validates the actual
two-parent merge commit directly at HEAD without requiring any file inside
the merge commit being validated.

The frozen Architecture Spine baseline is:

- previous main: `5884cf2abb37945652ef166cf0e78fa24593b0d5`;
- accepted PR #9 head: `43418818af61d9be3208d2444fd6ce5120f73fab`;
- merge commit: `38de9106d191d6b66d5f878354144817095e7bca`;
- PR #11 remains read-only at `d500c145a3201f59f90fcb330fc400596fba10b8`;
- PR #21 frozen audited head: `976fb86021d6e230b1a1b574960c78c8457e8983`
  (kept as audit history; this Decision opens a replacement branch).

## Required implementation

1. Preserve the historical `integration-baseline(architecture_spine_v1)`
   gate as an independent invariant proving the accepted PR #9 integration
   remains present and unchanged.
2. Add a `MainlineMergeAuthorization` schema and a pre-merge authorization
   artifact committed at
   `project_state/mainline_authorizations/<accepted_head_sha>.json` in the
   accepted PR head before merge. The artifact binds:
   - `source_pr`, `accepted_head_sha`, `locked_base_sha`;
   - `allowed_merge_method` (must be `merge`, not squash/rebase);
   - Decision ID and Decision content digest;
   - Command Plan digest;
   - required exact-head workflow observations with trust-source contracts;
   - human R2 approval reference;
   - expiry / supersession state.
3. Add a `mainline-merge-validation` gate that runs on pushes to `main` and
   validates the actual merge commit at HEAD:
   - HEAD is exactly one two-parent merge commit;
   - first parent == authorization.locked_base_sha;
   - second parent == authorization.accepted_head_sha;
   - merge method is merge commit (not squash/rebase);
   - merge tree satisfies the declared equality/conflict policy;
   - Decision digest matches the committed Decision artifact in the accepted
     head's tree;
   - Command Plan digest matches the committed locked plan;
   - Authorization is not expired or superseded;
   - All required workflow observations meet the declared trust boundary.
   Authorization selection is deterministic from the second parent
   (accepted head sha), so a stale authorization cannot validate a later
   unrelated commit.
4. Convert `MainlineIntegrationReceipt` to post-merge audit output. The
   receipt is not a prerequisite for validating the merge commit. If a later
   Git commit stores the receipt, the validator validates the recorded merge
   ancestor and does not require
   `receipt_commit_HEAD == receipt.merge_commit_sha`.
5. Strengthen authorization identity: the validator binds the authorization
   to committed, exact Decision and Command Plan digests and to an explicit
   R2 approval reference. Unknown or mismatched references fail closed.
6. Strengthen remote workflow evidence: the authorization declares a
   `minimum_trust_source` for observations. `github_actions_run` observations
   are required for production; `local_asserted` observations are rejected
   when the minimum is `github_actions_run`. The trust boundary is explicit
   and tested.
7. Add focused tests including the required positive lifecycle test and all
   16 negative cases from Issue #22 using hermetic temporary git
   repositories, plus a workflow routing test, plus architecture
   documentation.

## Pre-merge Authorization vs post-merge Receipt responsibilities

- **Pre-merge Authorization** (this Decision, R1/R2 execution): authorizes
  implementation, tests, and publication of the replacement branch. The
  `MainlineMergeAuthorization` artifact is committed in the accepted PR head
  and binds the Decision, Command Plan, and required observations. Does not
  authorize merge.
- **Post-merge Receipt** (separate R2 merge Decision): after the replacement
  PR is merged, a `MainlineIntegrationReceipt` is emitted as audit output
  (PR comment or GitHub Actions artifact). It records the actual merge
  commit, ordered parents, trees, and observation references. It is not a
  prerequisite for validating the merge.

This separation eliminates the self-referential lifecycle: the
authorization exists before the merge, the merge is validated directly at
HEAD, and the receipt is an output that never needs to be inside the merge
commit being validated.

## Do not do

Do not modify PR #9, PR #11, PR #19, or PR #21 branches. Do not mutate solve
artifacts, samples, frontend, reverse-solving logic, dependencies, secrets,
binaries, tags, or releases. Do not execute unknown binaries. Do not push
directly to main, force-push, rebase, squash, or merge under this Decision.
Do not create Trust Layer, Stage C protocol, Web, tool integration, or
unknown-binary execution work.

## Completion

This Decision is complete only when local focused tests pass, the branch is
published in a new Draft PR, and exact-head CI, State Gate, and Decision
Preflight are green. The PR then waits for a separately authorized R2 merge
Decision that will authorize the merge and emit the post-merge
`MainlineIntegrationReceipt`.
