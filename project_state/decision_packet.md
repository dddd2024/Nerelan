```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260721_architecture_spine_provenance_integration_final_rework_v1",
  "round_id": "round_20260721_architecture_spine_provenance_integration_final_rework_v1",
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
  "follows_last_decision_id": "decision_20260721_architecture_spine_attestation_policy_seal_v1",
  "follows_last_round_id": "round_20260721_architecture_spine_attestation_policy_seal_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "architecture-spine-provenance-integration-final-rework-v1",
  "source_pull_request": 9,
  "required_branch": "codex/architecture-spine-v1",
  "activation_base_sha": "f9621761865fd5ee46de220cea0b780d568eef3e",
  "audited_implementation_head_sha": "c3f053a027756edfa749bf9f7aba0f61c596a562",
  "roadmap_path": "docs/roadmap/architecture_spine_provenance_integration_final_rework_v1.md",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_kernel_required": true,
  "final_architecture_spine_rework_round": true,
  "legacy_state_maintenance_is_primary_goal": false,
  "legacy_final_check_is_acceptance_authority": false,
  "legacy_closeout_is_acceptance_authority": false,
  "legacy_state_manifest_is_acceptance_authority": false,
  "trusted_command_runner_required": true,
  "caller_supplied_execution_facts_forbidden": true,
  "raw_evidence_persistence_required": true,
  "authenticity_before_reconciliation_required": true,
  "future_timestamp_rejection_required": true,
  "record_sequence_monotonicity_required": true,
  "generated_at_after_records_required": true,
  "git_object_verification_required": true,
  "bootstrap_time_binding_required": true,
  "decision_issued_risk_policy_required": true,
  "workflow_identity_policy_digest_binding_required": true,
  "policy_fallback_forbidden": true,
  "command_bound_mutation_grants_required": true,
  "global_generated_artifact_exemption_forbidden": true,
  "report_subject_tree_binding_required": true,
  "stale_local_evidence_reuse_forbidden": true,
  "remote_publication_seal_externalized_required": true,
  "bootstrap_exception_authorized": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_reason": "The audited implementation added recorder, local seal, policy provider, mutation-grant and report-binding modules, but exact-head preflight found two out-of-scope source files; committed execution evidence still contains future timestamps and is accepted by the local seal; the policy provider is not wired into the workflow; generated artifacts remain globally exempted; and reports remain bound to the Decision commit. A bounded bootstrap is required to integrate the existing mechanisms rather than add another governance layer.",
  "bootstrap_exception_expires_when": "A command plan generated from this Decision exists; transition-lint passes; transition-preflight --mode pre passes; the trusted runner and authenticity integration focused tests pass; the old execution subject is invalidated; bootstrap state is persisted as BOOTSTRAP_EXPIRED; and subsequent records cannot claim bootstrap authority.",
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
    "tests/test_local_execution_seal.py",
    "tests/test_trusted_command_runner.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git rev-parse HEAD",
    "git branch --show-current",
    "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_local_execution_seal.py tests/test_trusted_command_runner.py -q",
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
        "project_state/gates/transition_preflight_result.json"
      ],
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "test.provenance_pipeline",
      "command": "python -m pytest tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_trusted_command_runner.py tests/test_local_execution_seal.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test"],
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
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_authority_closure.py tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_trusted_command_runner.py tests/test_local_execution_seal.py -q",
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
      "required_evidence_source": "local_command_evidence",
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["full_repository_test"],
      "network_access": false,
      "diagnostic_only": true,
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
      "expected_exit_codes": [0],
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
  "reference_paths": [
    "docs/roadmap/architecture_spine_provenance_integration_final_rework_v1.md",
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
  "scope_policy": "provenance_integration_final_rework_only",
  "stop_after_independent_audit_handoff": true
}
```

# DECISION_PACKET

## 1. Goal

Complete the final integration of the existing Architecture Spine proof mechanisms without expanding product scope or adding another governance layer.

The round must establish:

```text
active Decision
→ trusted command runner
→ persisted raw evidence
→ authenticity validation
→ command-bound mutation validation
→ Decision-issued runtime policy
→ verified workflow identity
→ truthful report subject binding
→ local content seal
→ independent exact-head remote seal
```

The audited implementation at `c3f053a027756edfa749bf9f7aba0f61c596a562` is retained as the starting implementation. Only findings listed in `docs/roadmap/architecture_spine_provenance_integration_final_rework_v1.md` may be repaired.

---

## 2. Immediate blockers

The previous implementation cannot be accepted because:

1. exact-head preflight reports `evidence_source.py` and `report_binding.py` outside authorized scope;
2. committed execution records contain timestamps later than their log generation and independent observation time;
3. a bootstrap record occurs after persisted bootstrap expiry;
4. the local seal does not force authenticity validation before reconciliation;
5. the policy provider is not wired into the real graph path;
6. generated artifacts are still globally exempted in transition validation;
7. the report and inventory remain bound to the Decision commit rather than the implementation subject;
8. exact-head State Gate and Decision Preflight are failed.

---

## 3. Bootstrap phase

Use the bootstrap exception only to:

1. extend command models and parser for per-command mutation grants;
2. turn the recorder into a trusted executor that derives all facts itself;
3. integrate authenticity validation into candidate generation;
4. invalidate the previous execution log, candidate and local seal;
5. add required negative tests;
6. generate the current command plan;
7. run transition-lint and pre-execution validation;
8. persist `BOOTSTRAP_EXPIRED`.

After expiry, no execution record may claim bootstrap authority.

---

## 4. Normal implementation

After bootstrap expiry:

1. rebuild the execution subject exclusively through the trusted runner;
2. persist raw stdout/stderr evidence and verify content digests;
3. enforce command-specific mutation grants in the formal gate;
4. remove global generated-artifact exemption behavior;
5. wire `AuthorizedRiskPolicyProvider` into graph construction and work-item loading;
6. bind Decision, round and policy digest into WorkflowIdentity;
7. make classify risk fail closed on missing or altered policy identity;
8. bind the report to the actual implementation subject tree and diff;
9. generate a trustworthy local reconciliation candidate;
10. generate a trustworthy local content seal;
11. commit and push once;
12. stop for independent exact-head audit.

---

## 5. Do not do

Do not:

- modify this Decision after activation;
- modify roadmap or architecture documents;
- modify GitHub workflows or dependencies;
- create another control-plane abstraction layer;
- repair unrelated legacy audit documents;
- install BMAD;
- dispatch coding Agents;
- call model APIs;
- execute unknown binaries or reverse tools;
- modify frontend, User Solve, solver or harness code;
- modify legacy closeout, final-seal, context or state-manifest systems;
- create another branch or pull request;
- push directly to main;
- merge, rebase, force-push, tag or release;
- begin Evidence Trust Schema or Binary Evidence Firewall work.

---

## 6. Completion criteria

The round may request final merge audit only if:

1. no modified implementation file is outside Decision scope;
2. every normal execution record is created by the trusted runner;
3. timestamps are real, monotonic and not in the future;
4. execution-log generation time follows all included records;
5. raw stdout/stderr exists and matches its digest;
6. recorded Git SHAs resolve in the repository;
7. bootstrap records precede bootstrap expiry;
8. authenticity validation is a hard prerequisite to reconciliation;
9. command-bound mutation grants pass for every mutation;
10. global generated artifact exemption is removed;
11. provider-issued policy is used by the complete graph;
12. workflow identity binds Decision, round and policy digest;
13. policy fallback and caller-supplied policy are rejected;
14. report inventory covers the real implementation subject;
15. local seal is `LOCAL_RECONCILED` and internally verifiable;
16. focused tests pass;
17. full-suite outcome is reported truthfully;
18. exact-head CI succeeds;
19. exact-head State Gate succeeds;
20. exact-head Decision Preflight succeeds;
21. PR #9 remains Draft and unmerged.

If any requirement remains open, the result is `REWORK_REQUIRED`.

After implementation, stop for independent audit. The repository-local implementation must not declare final remote acceptance.