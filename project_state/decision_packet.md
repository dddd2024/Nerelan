```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260721_architecture_spine_attestation_policy_seal_v1",
  "round_id": "round_20260721_architecture_spine_attestation_policy_seal_v1",
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
  "follows_last_decision_id": "decision_20260721_architecture_spine_evidence_runtime_closeout_v1",
  "follows_last_round_id": "round_20260721_architecture_spine_evidence_runtime_closeout_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "architecture-spine-attestation-policy-seal-v1",
  "source_pull_request": 9,
  "required_branch": "codex/architecture-spine-v1",
  "activation_base_sha": "ed634162b0189acaa60c11b4ad8e080479748f98",
  "audited_implementation_head_sha": "19c081410b3ee2bc9c81eeb52b0c0a21f200d02a",
  "roadmap_path": "docs/roadmap/architecture_spine_attestation_policy_seal_v1.md",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_kernel_required": true,
  "final_architecture_spine_seal_round": true,
  "legacy_state_maintenance_is_primary_goal": false,
  "legacy_final_check_is_acceptance_authority": false,
  "legacy_closeout_is_acceptance_authority": false,
  "legacy_state_manifest_is_acceptance_authority": false,
  "machine_generated_execution_evidence_required": true,
  "future_timestamp_rejection_required": true,
  "real_sha256_digest_validation_required": true,
  "raw_evidence_digest_verification_required": true,
  "self_reconciliation_forbidden": true,
  "local_remote_seal_separation_required": true,
  "evidence_source_normalization_required": true,
  "decision_issued_risk_policy_required": true,
  "workflow_identity_policy_digest_binding_required": true,
  "command_bound_mutation_grants_required": true,
  "global_generated_artifact_exemption_forbidden": true,
  "report_subject_tree_binding_required": true,
  "remote_publication_seal_externalized_required": true,
  "bootstrap_exception_authorized": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_reason": "The audited implementation added strict-looking execution records, local/remote report artifacts and runtime policy snapshots, but the evidence fields are not cryptographically or temporally validated, the post gate includes itself in its subject, runtime policy identity checks are self-referential, and generated artifact exemptions are not bound to a designated command. A narrow bootstrap is required to add the recorder, subject sealing and trusted policy provider before normal validation can proceed.",
  "bootstrap_exception_expires_when": "A machine-generated command plan for this Decision exists; transition-lint passes; transition-preflight --mode pre passes; evidence timestamp, digest and head validation tests pass; a persisted bootstrap state is BOOTSTRAP_EXPIRED; and subsequent execution records cannot claim bootstrap authority.",
  "bootstrap_exception_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/evidence_recorder.py",
    "reverse_agent/control_plane/local_seal.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_execution_evidence.py",
    "tests/test_evidence_authenticity.py",
    "tests/test_local_execution_seal.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git rev-parse HEAD",
    "git branch --show-current",
    "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_local_execution_seal.py -q",
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
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "status.git_head",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "required_evidence_source": "repository_truth",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "status.git_branch",
      "command": "git branch --show-current",
      "phase": "status",
      "required": true,
      "required_evidence_source": "repository_truth",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "gate.command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["command_plan_generation"],
      "network_access": false,
      "authority_origin": "normal_plan",
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
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authority_validation"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "gate.pre_execution",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pre_execution_authorization"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "test.evidence_authenticity",
      "command": "python -m pytest tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_local_execution_seal.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "test.runtime_policy_binding",
      "command": "python -m pytest tests/test_runtime_risk_policy.py tests/test_policy_provider.py tests/test_development_graph.py tests/test_risk_classifier.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "test.mutation_grants_report",
      "command": "python -m pytest tests/test_command_mutation_grants.py tests/test_transition_report.py tests/test_report_truth.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "test.control_plane",
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_authority_closure.py tests/test_execution_evidence.py tests/test_evidence_authenticity.py tests/test_local_execution_seal.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "test.full_repository",
      "command": "python -m pytest -q",
      "phase": "diagnostic",
      "required": false,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["full_repository_test"],
      "network_access": false,
      "diagnostic_only": true,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "report.generate_local",
      "command": "python -m reverse_agent.project_gate transition-report --state-dir project_state",
      "phase": "report",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["report_generation"],
      "network_access": false,
      "authority_origin": "normal_plan",
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
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "gate.reconcile_evaluate",
      "command": "python -m reverse_agent.project_gate transition-reconcile-evaluate --state-dir project_state",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["post_execution_evaluation"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "subject_to_reconciliation": false,
      "produced_artifacts": [
        "project_state/gates/reconciliation_candidate.json"
      ]
    },
    {
      "command_id": "gate.seal_local",
      "command": "python -m reverse_agent.project_gate transition-seal-local --state-dir project_state",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_execution_seal"],
      "network_access": false,
      "authority_origin": "normal_plan",
      "subject_to_reconciliation": false,
      "produced_artifacts": [
        "project_state/gates/local_execution_seal.json"
      ]
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin codex/architecture-spine-v1",
      "phase": "publication",
      "required": false,
      "required_evidence_source": "repository_truth",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "allowed_only_after_validation": true,
      "authority_origin": "normal_plan"
    }
  ],
  "reference_paths": [
    "docs/roadmap/architecture_spine_attestation_policy_seal_v1.md",
    "docs/roadmap/reverse_agent_unified_architecture_and_trust_roadmap.md",
    "docs/architecture/**",
    "project_state/decision_packet.md"
  ],
  "allowed_mutated_paths": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/evidence_recorder.py",
    "reverse_agent/control_plane/local_seal.py",
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
    "tests/test_local_execution_seal.py",
    "tests/test_runtime_risk_policy.py",
    "tests/test_policy_provider.py",
    "tests/test_development_graph.py",
    "tests/test_risk_classifier.py",
    "tests/test_command_mutation_grants.py",
    "tests/test_transition_report.py",
    "tests/test_report_truth.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/execution_log.json",
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
    "project_state/gates/reconciliation_candidate.json",
    "project_state/gates/local_execution_seal.json",
    "project_state/gates/changed_file_inventory.json",
    "project_state/gates/remote_observation_payload.json",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt"
  ],
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
  "scope_policy": "attestation_policy_seal_only",
  "stop_after_independent_audit_handoff": true
}
```

# DECISION_PACKET

## 1. Goal

Complete the Architecture Spine v1 proof chain without expanding product scope.

The round must establish:

```text
active Decision
→ machine-generated execution evidence
→ non-self-referential local reconciliation
→ Decision-issued runtime risk policy
→ command-bound mutation grants
→ truthful local report
→ external exact-head publication seal
```

The audited implementation at `19c081410b3ee2bc9c81eeb52b0c0a21f200d02a` is retained. Only the audit findings listed in `docs/roadmap/architecture_spine_attestation_policy_seal_v1.md` may be repaired.

---

## 2. Bootstrap Phase

Use the bootstrap exception only to implement:

1. strict timestamp, digest and Git SHA validation;
2. the controlled evidence recorder;
3. subject-set sealing and non-self-referential local reconciliation;
4. command-specific artifact production fields;
5. the tests required to prove these mechanisms;
6. generation of the current command plan and pre-execution result.

After bootstrap expiry, no new execution record may claim bootstrap authority.

---

## 3. Normal Implementation

After the generated plan and preflight pass:

1. normalize evidence source semantics;
2. issue runtime risk policy from the active Decision;
3. bind Decision, round and policy digest into workflow identity;
4. reject caller-supplied or tampered policy snapshots;
5. replace global generated-artifact exemption with command-bound grants;
6. bind the local report to subject tree and diff digests;
7. produce a `LOCAL_RECONCILED` local seal;
8. push the branch once local validation is complete;
9. stop for independent exact-head remote audit.

---

## 4. Acceptance Boundary

The repo-local implementation cannot declare final remote acceptance.

Final acceptance requires an independent PR audit comment binding the subject commit to successful exact-head runs for:

```text
CI
State Gate
Decision Preflight
```

Do not commit another report after the remote seal. A new commit invalidates the previous remote seal.

---

## 5. Do Not Do

Do not:

- modify this Decision after activation;
- modify roadmap or architecture documents;
- modify GitHub workflows or dependencies;
- repair unrelated legacy audit files;
- install BMAD;
- dispatch Agents or invoke model APIs;
- execute unknown binaries or reverse tools;
- modify frontend, User Solve, solvers or harnesses;
- extend legacy closeout/final-seal systems;
- create another branch or PR;
- push directly to main;
- merge, rebase, force-push, tag or release;
- begin Evidence Trust Schema or Binary Evidence Firewall implementation.

---

## 6. Completion Criteria

Recommend `ACCEPTED` only after an independent audit confirms:

1. evidence records are machine generated and cryptographically/temporally valid;
2. no future timestamp or placeholder digest is accepted;
3. local reconciliation excludes evaluator and sealer from its subject;
4. required local evidence is complete;
5. local commands are not falsely represented as CI evidence;
6. runtime policy is issued from the active Decision;
7. workflow identity binds the authorized policy digest;
8. policy tampering and stale replay block;
9. artifact mutation grants are command-specific;
10. local report represents the actual implementation subject;
11. local status is `LOCAL_RECONCILED` with no contradictory PASSED/BLOCKED fields;
12. focused tests pass and full-suite truth is recorded;
13. the subject commit has successful exact-head CI, State Gate and Decision Preflight;
14. the remote publication seal is posted as a PR audit comment;
15. PR #9 remains Draft until that final audit completes.

If any condition fails, the outcome remains `REWORK_REQUIRED`.