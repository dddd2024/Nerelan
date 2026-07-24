```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260724_p1a_exact_head_external_merge_approval_rework_v3",
  "round_id": "round_20260724_p1a_exact_head_external_merge_approval_rework_v3",
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
  "follows_last_decision_id": "decision_20260724_p1a_premerge_authorization_mainline_validation_rework_v2",
  "follows_last_round_id": "round_20260724_p1a_premerge_authorization_mainline_validation_rework_v2",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "p1a-v3-exact-head-external-merge-approval",
  "source_issue": 23,
  "program_issue": 18,
  "source_pull_request": 21,
  "frozen_pr21_head_sha": "976fb86021d6e230b1a1b574960c78c8457e8983",
  "frozen_v2_prototype_head": "708aeefaaa69f571c520d9ab55b07d6e7c082371",
  "program_bundle_sha256": "394f02387230710cb158782affc77a11a651819a6e66221fae9ed95912295c97",
  "required_branch": "codex/p1a-v3-exact-head-external-approval",
  "activation_base_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "frozen_previous_main_sha": "5884cf2abb37945652ef166cf0e78fa24593b0d5",
  "frozen_subject_head_sha": "43418818af61d9be3208d2444fd6ce5120f73fab",
  "frozen_merge_commit_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "frozen_pr11_head_sha": "d500c145a3201f59f90fcb330fc400596fba10b8",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "merge_allowed": false,
  "stop_after_exact_head_ci": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json"
  ],
  "bootstrap_exception_commands": [],
  "allowed_commands": [
    {
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/startup_snapshot.json"
      ],
      "produced_artifacts": [
        "project_state/gates/startup_snapshot.json"
      ]
    },
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
      "command_id": "test.exact_head_lifecycle",
      "command": "python -m pytest tests/test_exact_head_lifecycle.py -q",
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
      "command_id": "test.remote_evidence_authenticity",
      "command": "python -m pytest tests/test_remote_evidence_authenticity.py -q",
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
      "command_id": "test.pr_approval_binding",
      "command": "python -m pytest tests/test_pr_approval_binding.py -q",
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
      "command_id": "test.expiry_and_receipt",
      "command": "python -m pytest tests/test_expiry_and_receipt.py -q",
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
      "command_id": "test.integration_baseline_regression",
      "command": "python -m pytest tests/test_integration_baseline.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["regression_test"],
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
      "command": "git push origin codex/p1a-v3-exact-head-external-approval",
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
    },
    {
      "command_id": "publication.create_draft_pr",
      "command": "gh pr create --draft --base main --head codex/p1a-v3-exact-head-external-approval",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pr_creation", "network_access"],
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
    "docs/architecture/exact-head-external-approval.md",
    "docs/architecture/main-integration-baseline.md",
    "project_state/decision_packet.md",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/integration_baselines/architecture_spine_v1.json",
    "project_state/schemas/integration_baseline.schema.json",
    "project_state/schemas/merge_intent.schema.json",
    "project_state/schemas/merge_approval_attestation.schema.json",
    "project_state/schemas/mainline_integration_receipt.schema.json",
    "reverse_agent/project_gate.py",
    "reverse_agent/remote_acceptance_verifier.py",
    "tests/test_exact_head_lifecycle.py",
    "tests/test_remote_evidence_authenticity.py",
    "tests/test_pr_approval_binding.py",
    "tests/test_expiry_and_receipt.py",
    "tests/test_integration_baseline.py"
  ],
  "reference_paths": [
    "project_state/current_state.json",
    "project_state/artifactindex.json",
    "project_state/state_manifest.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
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
    "project_state/mainline_authorizations/**",
    "project_state/mainline_receipts/**",
    "project_state/mainline_merge_intents/**",
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
    "bmad_installation",
    "merge"
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
    "pr_creation_allowed": true,
    "local_network_exceptions": [
      "git push origin codex/p1a-v3-exact-head-external-approval",
      "gh pr create --draft --base main --head codex/p1a-v3-exact-head-external-approval"
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
    "project_state/schemas/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/remote_acceptance_verifier.py",
    "tests/test_exact_head_lifecycle.py",
    "tests/test_remote_evidence_authenticity.py",
    "tests/test_pr_approval_binding.py",
    "tests/test_expiry_and_receipt.py",
    "tests/test_integration_baseline.py",
    "docs/architecture/exact-head-external-approval.md",
    "docs/architecture/main-integration-baseline.md"
  ],
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"},
    {"pattern": ".env", "minimum_risk": "R3"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"},
    {"pattern": "**/credentials/**", "minimum_risk": "R3"},
    {"pattern": "**/*.exe", "minimum_risk": "R3"},
    {"pattern": "**/*.dll", "minimum_risk": "R3"},
    {"pattern": "**/*.bin", "minimum_risk": "R3"}
  ],
  "scope_policy": "p1a_v3_exact_head_external_merge_approval_only",
  "stop_after_exact_head_ci": true
}
```

# DECISION_PACKET

## Goal

Bind mainline merge approval to the actual exact PR head and verified GitHub
evidence. The v2 prototype (commit `708aeefa`, branch
`codex/p1a-v2-premerge-authorization`) is frozen as audit evidence; it is not
merged, not marked ready, and not used as the v3 base.

The v2 audit (Issue #22 comment, 2026-07-24T08:27:29Z) found seven blocking
issues (F1-F7). This v3 Decision addresses all seven by replacing the
single-artifact authorization model with a three-object lifecycle that
separates committed merge intent (pre-CI) from external acceptance evidence
(post-CI), and by adding a real remote-observation verifier.

## v3 Architecture: three separate objects

### A. Committed Merge Intent (in PR head, before CI)

A `MergeIntent` artifact committed at
`project_state/mainline_merge_intents/active.json` in the exact PR head before
final CI. It binds:

- `source_pr`, `locked_base_sha`, `allowed_merge_method`;
- Decision identity and Command Plan digest;
- `merge_tree_policy`, `expiry_policy`;
- required workflow names (NOT run IDs — those come post-CI).

It must NOT contain its own future commit SHA or post-CI run IDs. The exact PR
head is the commit that becomes the merge's second parent — no branch commit
is allowed after exact-head acceptance.

### B. External Merge Approval Attestation (post-CI, outside Git tree)

A `MergeApprovalAttestation` created only after final exact-head CI succeeds.
Stored as a GitHub PR comment or Actions artifact (NOT in the PR Git tree).
It binds:

- repository, `source_pr`, `locked_base_sha`, `accepted_exact_head_sha`;
- required workflow run IDs, workflow file/name, event type, run attempt,
  conclusion;
- human approver identity, approval object/comment ID;
- content digest, expiry/supersession.

### C. Post-merge Integration Receipt (output only)

The `MainlineIntegrationReceipt` remains audit output (kept from v2). It is
NOT a prerequisite for validating the merge. Produced after validating the
actual merge, stored as Actions artifact or Issue/PR comment, not as a new
ordinary `main` commit.

## RemoteAcceptanceVerifier

A narrow interface in `reverse_agent/remote_acceptance_verifier.py`. The
production GitHub Actions implementation queries GitHub using read-only
permissions (`contents: read`, `actions: read`, `pull-requests: read`,
`issues: read`) and proves every run/approval fact. Hermetic tests use a
fixture implementation. API failure, missing permission, unknown run, or
mismatched identity fails closed.

## PR and R2 approval binding

The gate proves:

- PR exists in `dddd2024/reverse-agent`;
- PR head == `accepted_exact_head_sha`;
- PR base == `locked_base_sha`;
- approval reference exists;
- approval was produced by an allowed approver;
- approval content binds the same base/head/PR/method.

A non-empty string is insufficient.

## Time-based expiry

Reject when `authorization_status != active` OR `expires_at <= validation_time`
OR `superseded_by` is set. Uses an injected clock in tests.

## Addresses v2 audit findings

- **F1**: Merge Intent path is `active.json` (fixed, non-self-referential);
  validation binds `second_parent == accepted_exact_head` (the actual PR head),
  not `second_parent's_parent`.
- **F2**: The exact PR head IS the merge second parent — no post-CI
  authorization commit exists in the Git tree.
- **F3**: `RemoteAcceptanceVerifier` queries GitHub API to verify run identity;
  `trust_source` is no longer a self-authored label.
- **F4**: `source_pr` and `human_r2_approval_reference` are verified against
  GitHub PR and comment data.
- **F5**: Test 21 implements the coherent forgery case (rewrite Decision/PR
  fields, recompute digests, still fails without matching external approval).
- **F6**: Test 22 explicitly covers `active` + past `expires_at`.
- **F7**: Draft PR creation is authorized (`pr_creation_allowed: true`).

## Required tests (26, from Issue #23)

### Exact-head lifecycle (tests 1-7) — `tests/test_exact_head_lifecycle.py`
1. Final PR head contains all code and committed merge intent.
2. All required remote observations bind that exact final head.
3. Actual merge second parent equals that exact final head.
4. Mainline validation passes at the real two-parent merge commit.
5. Any commit added after accepted exact-head checks causes failure.
6. An "authorization-only" post-CI commit causes failure.
7. A post-CI commit containing unrelated source changes causes failure.

### Remote evidence authenticity (tests 8-15) — `tests/test_remote_evidence_authenticity.py`
8. `trust_source=github_actions_run` with nonexistent run ID fails.
9. Run from another repository fails.
10. Run for another SHA fails.
11. Wrong workflow name or workflow file fails.
12. Wrong event type fails.
13. Failed/cancelled/skipped/in-progress run fails.
14. Stale run attempt or superseded run fails where applicable.
15. Missing one required run fails.

### PR and approval binding (tests 16-21) — `tests/test_pr_approval_binding.py`
16. Wrong `source_pr` fails even if other digests are recomputed.
17. PR head/base mismatch fails.
18. Nonexistent approval reference fails.
19. Approval by an unauthorized identity fails.
20. Approval digest/base/head/method mismatch fails.
21. Coherently rewritten local Decision/PR fields and recomputed ordinary
    digests still fail without matching external approval.

### Expiry and receipt (tests 22-26) — `tests/test_expiry_and_receipt.py`
22. `authorization_status=active` with past `expires_at` fails.
23. Superseded approval fails.
24. Post-merge receipt is emitted as output without becoming a validation
    prerequisite.
25. Receipt publication does not create an ordinary `main` commit that
    immediately violates the merge-at-HEAD gate.
26. Historical `integration-baseline(architecture_spine_v1)` remains active.

## Do not do

Do not modify PR #9, PR #11, PR #19, PR #21, or the v2 prototype branch. Do
not mutate solve artifacts, samples, frontend, reverse-solving logic,
dependencies, secrets, binaries, tags, or releases. Do not execute unknown
binaries. Do not push directly to main, force-push, rebase, squash, or merge
under this Decision. Do not create Trust Layer, Stage C protocol, Web, tool
integration, or unknown-binary execution work. Do not add a post-CI branch
commit containing authorization data.

## Completion

This Decision is complete only when:
- local focused tests pass (26 v3 tests + integration baseline regression);
- the branch is published and a Draft PR is created;
- exact-head CI, State Gate, and Decision Preflight are green on the same
  exact head;
- the historical Architecture Spine baseline remains active.

The PR then waits for a separately authorized R2 merge Decision.
