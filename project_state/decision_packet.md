```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260721_architecture_spine_trusted_execution_cutover_rework_v1",
  "round_id": "round_20260721_architecture_spine_trusted_execution_cutover_rework_v1",
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
  "follows_last_decision_id": "decision_20260721_architecture_spine_provenance_integration_final_rework_v1",
  "follows_last_round_id": "round_20260721_architecture_spine_provenance_integration_final_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "architecture-spine-trusted-execution-cutover-rework-v1",
  "source_pull_request": 9,
  "required_branch": "codex/architecture-spine-v1",
  "activation_base_sha": "54f7cf693f3435ab0d78b8c16533e7b9e6d83b9f",
  "audited_implementation_head_sha": "70dd217b381d106085bce51857be5e8abdd2fa86",
  "roadmap_path": "docs/roadmap/architecture_spine_trusted_execution_cutover_rework_v1.md",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_kernel_required": true,
  "architecture_spine_new_module_expansion_allowed": false,
  "trusted_execution_cutover_required": true,
  "deterministic_command_projection_required": true,
  "command_id_global_uniqueness_required": true,
  "required_test_file_existence_required": true,
  "stale_evidence_invalidation_required": true,
  "cross_round_log_append_forbidden": true,
  "production_plan_injection_forbidden": true,
  "pre_execution_authorization_required": true,
  "runner_surface_binding_required": true,
  "runner_capability_policy_required": true,
  "runner_bootstrap_state_required": true,
  "runner_validation_state_required": true,
  "atomic_evidence_journal_required": true,
  "journal_lock_required": true,
  "journal_monotonic_sequence_required": true,
  "command_local_mutation_delta_required": true,
  "command_string_fallback_forbidden": true,
  "risk_floor_classification_not_auto_block_required": true,
  "reference_paths_all_mutations_read_only_required": true,
  "current_round_local_seal_required": true,
  "current_round_report_binding_required": true,
  "remote_publication_seal_externalized_required": true,
  "bootstrap_exception_authorized": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_reason": "The audited implementation contains reusable TrustedCommandRunner, authenticity, policy-provider, mutation-grant, and report-binding components, but the committed plan is not the deterministic projection of the active Decision, a required test file is absent, production execution still accepts an injected plan object, the journal can append across rounds without atomic locking, mutation attribution is based on post-command dirty state instead of a before/after delta, and all current evidence artifacts still belong to the previous Decision. A bounded bootstrap is required to recover deterministic authority and implement the production execution context before current-round commands can be rerun.",
  "bootstrap_exception_expires_when": "A command plan generated from this Decision exactly matches its deterministic projection; transition-lint passes; transition-preflight --mode pre passes; command-id uniqueness and required-test-file checks pass; TrustedExecutionContext and atomic journal tests pass; all previous-round evidence is rejected as stale; bootstrap state is persisted as BOOTSTRAP_EXPIRED; and no subsequent command can claim bootstrap authority.",
  "bootstrap_exception_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/evidence_recorder.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/local_seal.py",
    "reverse_agent/control_plane/transition.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_execution_evidence.py",
    "tests/test_evidence_authenticity.py",
    "tests/test_trusted_command_runner.py",
    "tests/test_local_execution_seal.py",
    "tests/test_provenance_integration.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git rev-parse HEAD",
    "git branch --show-current",
    "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_trusted_command_runner.py tests/test_local_execution_seal.py tests/test_provenance_integration.py -q",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "git diff --check"
  ],
  "allowed_commands": [
    {
      "command_id": "status.git_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "status.git_head",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "required_evidence_source": "repository_state_attestation",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "status.git_branch",
      "command": "git branch --show-current",
      "phase": "status",
      "required": true,
      "required_evidence_source": "repository_state_attestation",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["command_plan_generation"],
      "network_access": false,
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
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authority_validation"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.pre_execution",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pre_execution_authorization"],
      "network_access": false,
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
      "command_id": "test.trusted_execution_cutover",
      "command": "python -m pytest tests/test_trusted_command_runner.py tests/test_provenance_integration.py tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_local_execution_seal.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.runtime_policy_integration",
      "command": "python -m pytest tests/test_runtime_risk_policy.py tests/test_policy_provider.py tests/test_development_graph.py tests/test_risk_classifier.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.mutation_report_integration",
      "command": "python -m pytest tests/test_command_mutation_grants.py tests/test_transition_report.py tests/test_report_truth.py tests/test_provenance_integration.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.control_plane",
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_authority_closure.py tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_trusted_command_runner.py tests/test_local_execution_seal.py tests/test_provenance_integration.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.full_repository",
      "command": "python -m pytest -q",
      "phase": "diagnostic",
      "required": false,
      "diagnostic_only": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["full_repository_test"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "report.generate_local",
      "command": "python -m reverse_agent.project_gate transition-report --state-dir project_state",
      "phase": "report",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["report_generation"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/changed_file_inventory.json",
        "project_state/gates/remote_observation_payload.json",
        "project_state/codex_execution_report.md",
        "project_state/execution_report.md",
        "project_state/pytest_result.txt"
      ],
      "produced_artifacts": [
        "project_state/gates/changed_file_inventory.json",
        "project_state/gates/remote_observation_payload.json",
        "project_state/codex_execution_report.md",
        "project_state/execution_report.md",
        "project_state/pytest_result.txt"
      ]
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.reconcile_evaluate",
      "command": "python -m reverse_agent.project_gate transition-reconcile-evaluate --state-dir project_state",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["post_execution_evaluation"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "subject_to_reconciliation": false,
      "allowed_mutated_paths": [
        "project_state/gates/reconciliation_candidate.json"
      ],
      "produced_artifacts": [
        "project_state/gates/reconciliation_candidate.json"
      ]
    },
    {
      "command_id": "gate.seal_local",
      "command": "python -m reverse_agent.project_gate transition-seal-local --state-dir project_state",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["local_execution_seal"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "subject_to_reconciliation": false,
      "allowed_mutated_paths": [
        "project_state/gates/local_execution_seal.json"
      ],
      "produced_artifacts": [
        "project_state/gates/local_execution_seal.json"
      ]
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin codex/architecture-spine-v1",
      "phase": "publication",
      "required": false,
      "required_evidence_source": "repository_state_attestation",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "allowed_only_after_validation": true,
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "runner_managed_artifact_paths": [
    "project_state/gates/execution_log.json",
    "project_state/gates/evidence/**"
  ],
  "runner_managed_artifact_policy": "Only TrustedExecutionContext may write these paths. They are executor provenance and are excluded from subprocess mutation delta while remaining part of the local evidence bundle.",
  "reference_paths": [
    "docs/roadmap/architecture_spine_trusted_execution_cutover_rework_v1.md",
    "docs/roadmap/reverse_agent_unified_architecture_and_trust_roadmap.md",
    "docs/architecture/**",
    "project_state/decision_packet.md"
  ],
  "allowed_mutated_paths": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/evidence_recorder.py",
    "reverse_agent/control_plane/evidence_source.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/local_seal.py",
    "reverse_agent/control_plane/report_binding.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/architecture/contracts.py",
    "reverse_agent/architecture/policy_provider.py",
    "reverse_agent/workflows/development_graph.py",
    "reverse_agent/workflows/nodes/load_work_item.py",
    "reverse_agent/workflows/nodes/classify_risk.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_authority_closure.py",
    "tests/test_execution_evidence.py",
    "tests/test_evidence_authenticity.py",
    "tests/test_trusted_command_runner.py",
    "tests/test_local_execution_seal.py",
    "tests/test_runtime_risk_policy.py",
    "tests/test_policy_provider.py",
    "tests/test_development_graph.py",
    "tests/test_risk_classifier.py",
    "tests/test_command_mutation_grants.py",
    "tests/test_transition_report.py",
    "tests/test_report_truth.py",
    "tests/test_provenance_integration.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/evidence/**",
    "project_state/gates/reconciliation_candidate.json",
    "project_state/gates/local_execution_seal.json",
    "project_state/gates/changed_file_inventory.json",
    "project_state/gates/remote_observation_payload.json",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/evidence/**",
    "project_state/gates/reconciliation_candidate.json",
    "project_state/gates/local_execution_seal.json",
    "project_state/gates/changed_file_inventory.json",
    "project_state/gates/remote_observation_payload.json",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "generated_artifact_paths_are_inventory_only": true,
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    "docs/roadmap/**",
    "docs/architecture/**",
    ".github/workflows/**",
    "pyproject.toml",
    "frontend/**",
    "solve_reports/**",
    "local_reverse_samples/**",
    "training_materials/**",
    "reverse_agent/user_solve_*.py",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/project_runner_contract.py",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
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
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "git push origin codex/architecture-spine-v1"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "authorized_risk_tier": "R2",
  "risk_authorization_source": "active_approved_decision",
  "authorized_risk_paths": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/architecture/**",
    "reverse_agent/workflows/**",
    "tests/**",
    "project_state/gates/**",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "pyproject.toml", "minimum_risk": "R2"},
    {"pattern": "**/*lock*", "minimum_risk": "R2"},
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": ".env", "minimum_risk": "R3"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"},
    {"pattern": "**/credentials/**", "minimum_risk": "R3"},
    {"pattern": "local_reverse_samples/**", "minimum_risk": "R3"},
    {"pattern": "training_materials/local_reverse/**", "minimum_risk": "R3"},
    {"pattern": "**/*.exe", "minimum_risk": "R3"},
    {"pattern": "**/*.dll", "minimum_risk": "R3"},
    {"pattern": "**/*.bin", "minimum_risk": "R3"}
  ],
  "capability_risk_rules": [
    {"operation": "workflow_change", "risk_tier": "R2"},
    {"operation": "dependency_change", "risk_tier": "R2"},
    {"operation": "network_access", "risk_tier": "R2"},
    {"operation": "push", "risk_tier": "R2"},
    {"operation": "permission_policy", "risk_tier": "R2"},
    {"operation": "unknown_binary_execution", "risk_tier": "R3"},
    {"operation": "debugger", "risk_tier": "R3"},
    {"operation": "emulator", "risk_tier": "R3"},
    {"operation": "secrets", "risk_tier": "R3"},
    {"operation": "destructive_delete", "risk_tier": "R3"}
  ],
  "risk_combination_policy": "max(operation_risk,path_risk,capability_flag_risk)",
  "unknown_operation_policy": "BLOCKED",
  "unknown_sensitive_path_policy": "BLOCKED",
  "current_round_evidence_identity_required": true,
  "current_round_plan_digest_required": true,
  "local_seal_status_required": "LOCAL_RECONCILED",
  "remote_publication_seal_required": true,
  "remote_publication_seal_location": "pull_request_comment",
  "required_remote_checks": [
    "CI",
    "State Gate",
    "Decision Preflight"
  ],
  "draft_pull_request_allowed": true,
  "existing_pull_request_only": 9,
  "new_pull_request_allowed": false,
  "scope_policy": "trusted_execution_cutover_only",
  "stop_after_independent_audit_handoff": true
}
```

# DECISION_PACKET

## 1. Goal

Complete the Architecture Spine trusted-execution cutover without adding another governance layer.

The required chain is:

```text
active Decision
→ deterministic current command plan
→ TrustedExecutionContext
→ authorize-before-execute
→ trusted runner
→ atomic current-round evidence journal
→ command-local mutation delta
→ authenticity and mutation reconciliation
→ current LOCAL_RECONCILED seal
→ current subject-bound report
→ independent exact-head publication seal
```

The implementation at `70dd217b381d106085bce51857be5e8abdd2fa86` is retained as the starting point. Only the defects listed in `docs/roadmap/architecture_spine_trusted_execution_cutover_rework_v1.md` may be repaired.

---

## 2. Bootstrap Phase

Use the bootstrap exception only to:

1. make all command fields round-trip through generator and committed plan;
2. enforce globally unique command IDs;
3. add the missing `tests/test_provenance_integration.py`;
4. implement `TrustedExecutionContext.from_state_dir()`;
5. implement authorize-before-execute checks;
6. make the evidence journal cross-round safe, locked, monotonic and atomic;
7. invalidate all previous-round evidence as completion evidence;
8. generate this Decision's command plan and preflight result.

After bootstrap expiry, no command may execute outside the production trusted-runner path.

---

## 3. Normal Implementation

After transition-lint and pre-execution authorization pass:

1. remove production plan injection;
2. bind command ID to execution surface;
3. remove transition command-string fallback;
4. compute command-local pre/post mutation delta;
5. distinguish runner-managed evidence writes from subprocess mutations;
6. change path-risk handling from automatic blocking to classification plus explicit active-Decision authorization;
7. check reference read-only status against every observed mutation;
8. wire report subject binding into the real transition-report command;
9. run every required command through the trusted runner;
10. produce a current-round evidence bundle and local seal;
11. push once and stop for independent audit.

---

## 4. Evidence Rules

A current-round execution record is acceptable only when:

```text
decision_id matches active Decision
round_id matches active round
plan_digest matches current deterministic plan
command_id is globally unique and present
execution surface matches
raw evidence exists
digests match raw bytes
timestamps are real and monotonic
Git objects exist
bootstrap timing is valid
sequence is unique and monotonic
mutation delta is command-local
```

Records from previous Decisions must be rejected, not rewritten or re-labeled.

---

## 5. Do Not Do

Do not:

- alter this Decision after activation;
- add another governance abstraction or workflow runtime;
- modify GitHub workflows or dependencies;
- weaken transition-lint, path scope, mutation grants or capability policy;
- install BMAD;
- dispatch Agents or call model APIs;
- execute binaries or reverse tools;
- modify frontend, User Solve or reverse-solving business logic;
- modify unrelated legacy closeout systems;
- create another branch or PR;
- push directly to main;
- merge, rebase, force-push, tag or release;
- begin Evidence Trust Schema or Binary Evidence Firewall work.

---

## 6. Completion Criteria

Recommend `ACCEPTED` only if:

1. committed plan exactly equals the active Decision projection;
2. all required test files exist;
3. transition-lint and preflight pass;
4. production runner loads authority from state_dir and rejects injected plans;
5. authorization occurs before subprocess execution;
6. the journal is current-round only, atomic and locked;
7. mutation attribution uses before/after delta;
8. command IDs are unique and no string fallback exists;
9. path risk is correctly classified and authorized by the active Decision;
10. reference paths remain read-only across all mutations;
11. every required command has authentic current evidence;
12. reconciliation is `RECONCILED`;
13. local seal is `LOCAL_RECONCILED` for this Decision;
14. reports bind the real implementation subject;
15. exact-head CI, State Gate and Decision Preflight all succeed;
16. the independent PR publication seal binds exact HEAD and run IDs;
17. PR #9 remains Draft and unmerged.

Otherwise the result remains `REWORK_REQUIRED`.

After acceptance, stop Architecture Spine governance repair and hand off to a separately authorized product phase.