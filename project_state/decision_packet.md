```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260721_architecture_spine_evidence_runtime_closeout_v1",
  "round_id": "round_20260721_architecture_spine_evidence_runtime_closeout_v1",
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
  "follows_last_decision_id": "decision_20260721_architecture_spine_authority_closure_rework_v1",
  "follows_last_round_id": "round_20260721_architecture_spine_authority_closure_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "architecture-spine-evidence-runtime-closeout-v1",
  "source_pull_request": 9,
  "required_branch": "codex/architecture-spine-v1",
  "activation_base_sha": "97c28ac0647c7653f6eedffac5314297ded8a508",
  "audited_implementation_head_sha": "976122bdaeb98c05f04bcb54affec54d130a8e45",
  "roadmap_path": "docs/roadmap/architecture_spine_evidence_runtime_closeout_v1.md",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_kernel_required": true,
  "final_architecture_spine_closeout_round": true,
  "legacy_state_maintenance_is_primary_goal": false,
  "legacy_final_check_is_acceptance_authority": false,
  "legacy_closeout_is_acceptance_authority": false,
  "legacy_state_manifest_is_acceptance_authority": false,
  "required_command_coverage_required": true,
  "strict_execution_record_schema_required": true,
  "bootstrap_provenance_machine_derived_required": true,
  "pre_post_execution_gate_split_required": true,
  "plan_driven_capability_enforcement_required": true,
  "runtime_path_risk_wiring_required": true,
  "path_contract_separation_required": true,
  "report_truth_runtime_integration_required": true,
  "exact_head_remote_truth_externalized_required": true,
  "bootstrap_exception_authorized": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_reason": "The audited implementation added structured command authority but still permits incomplete required-command coverage, caller-supplied bootstrap classification, omitted operations, and a combined pre/post transition gate. A narrowly bounded bootstrap is required to introduce stable command IDs, strict execution records, and separate pre-execution/post-execution validation before normal closeout work can proceed.",
  "bootstrap_exception_expires_when": "The active Decision generates a command plan with stable command IDs and authority origins, strict execution record schema validation exists, transition-preflight --mode pre passes without consuming historical completion evidence, and bootstrap state is persisted as BOOTSTRAP_EXPIRED.",
  "bootstrap_exception_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/transition.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_authority_closure.py",
    "tests/test_execution_evidence.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git rev-parse HEAD",
    "git branch --show-current",
    "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_authority_closure.py tests/test_execution_evidence.py -q",
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
      "authority_origin": "normal_plan"
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
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "test.evidence_control_plane",
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_authority_closure.py tests/test_execution_evidence.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "exact_head_ci",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "test.runtime_risk_graph",
      "command": "python -m pytest tests/test_architecture_contracts.py tests/test_risk_classifier.py tests/test_development_graph.py tests/test_runtime_risk_policy.py tests/test_trust_authorization_adapter.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "exact_head_ci",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "test.report_truth",
      "command": "python -m pytest tests/test_report_truth.py tests/test_transition_report.py tests/test_planning_and_github_adapters.py -q",
      "phase": "test",
      "required": true,
      "required_evidence_source": "exact_head_ci",
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
      "diagnostic_only": true,
      "required_evidence_source": "exact_head_ci",
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["full_repository_test"],
      "network_access": false,
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
      "authority_origin": "normal_plan"
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
      "command_id": "gate.post_execution",
      "command": "python -m reverse_agent.project_gate transition-reconcile --state-dir project_state --mode post",
      "phase": "gate",
      "required": true,
      "required_evidence_source": "local_provenance",
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["post_execution_reconciliation"],
      "network_access": false,
      "authority_origin": "normal_plan"
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
    },
    {
      "command_id": "ci.install",
      "command": "python -m pip install -e \".[test]\"",
      "phase": "ci_dependency",
      "required": true,
      "required_evidence_source": "exact_head_ci",
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["dependency_install", "network_access"],
      "network_access": true,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "ci.test",
      "command": "python -m pytest -q",
      "phase": "ci_test",
      "required": true,
      "required_evidence_source": "exact_head_ci",
      "expected_exit_codes": [0, 1],
      "execution_surface": "ci_only",
      "operations": ["full_repository_test"],
      "network_access": false,
      "authority_origin": "normal_plan"
    },
    {
      "command_id": "ci.transition_preflight",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state",
      "phase": "ci_gate",
      "required": true,
      "required_evidence_source": "exact_head_ci",
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["authority_validation"],
      "network_access": false,
      "authority_origin": "normal_plan"
    }
  ],
  "reference_paths": [
    "docs/roadmap/architecture_spine_evidence_runtime_closeout_v1.md",
    "docs/roadmap/reverse_agent_unified_architecture_and_trust_roadmap.md",
    "docs/architecture/architecture-spine-v1.md",
    "docs/architecture/control-plane-transition-kernel.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/reconciliation_result.json",
    "project_state/gates/changed_file_inventory.json",
    "project_state/gates/remote_observation_payload.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/execution_log.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md"
  ],
  "allowed_mutated_paths": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/architecture/contracts.py",
    "reverse_agent/architecture/risk_classifier.py",
    "reverse_agent/architecture/report_truth.py",
    "reverse_agent/workflows/graph.py",
    "reverse_agent/workflows/nodes/classify_risk.py",
    "reverse_agent/adapters/github_truth.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_authority_closure.py",
    "tests/test_execution_evidence.py",
    "tests/test_architecture_contracts.py",
    "tests/test_risk_classifier.py",
    "tests/test_development_graph.py",
    "tests/test_runtime_risk_policy.py",
    "tests/test_trust_authorization_adapter.py",
    "tests/test_report_truth.py",
    "tests/test_transition_report.py",
    "tests/test_planning_and_github_adapters.py"
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
  "path_contract_conflict_policy": "BLOCKED",
  "generated_artifact_write_policy": "generator_only",
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
  "risk_combination_policy": "max(operation_risk,path_risk,capability_flag_risk)",
  "risk_policy_snapshot_required": true,
  "missing_risk_policy_policy": "BLOCKED",
  "unknown_operation_policy": "BLOCKED",
  "unknown_sensitive_path_policy": "BLOCKED",
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
    "ci_network_exceptions": [
      "python -m pip install -e \".[test]\""
    ],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "execution_evidence_required_fields": [
    "command_id",
    "command",
    "execution_surface",
    "operations",
    "mutated_paths",
    "exit_code",
    "started_at",
    "observed_at",
    "head_before",
    "head_after",
    "stdout_digest",
    "stderr_digest",
    "authority_origin"
  ],
  "required_command_coverage_policy": "ALL_REQUIRED_BY_EVIDENCE_SOURCE",
  "diagnostic_truth_required": true,
  "changed_files_from_activation_base_diff_required": true,
  "local_report_remote_pass_forbidden": true,
  "remote_truth_location": "pull_request_audit_comment",
  "remote_truth_required_fields": [
    "observed_head_sha",
    "ci_run_id",
    "ci_conclusion",
    "state_gate_run_id",
    "state_gate_conclusion",
    "decision_preflight_run_id",
    "decision_preflight_conclusion",
    "observed_at",
    "auditor_outcome"
  ],
  "draft_pull_request_allowed": true,
  "existing_pull_request_only": 9,
  "new_pull_request_allowed": false,
  "scope_policy": "final_evidence_runtime_closeout_only",
  "stop_after_independent_audit_handoff": true
}
```

# DECISION_PACKET

## 1. Goal

Complete the final Architecture Spine v1 closeout by repairing evidence completeness and wiring already-implemented policy logic into the actual runtime path.

The audited implementation at `976122bdaeb98c05f04bcb54affec54d130a8e45` is retained. This round must not redesign the architecture. It must close the remaining chain:

```text
active Decision
→ stable command IDs
→ strict pre-execution authorization
→ complete required-command coverage
→ plan-driven capability enforcement
→ path-aware LangGraph routing
→ generated current-round local report
→ exact-head GitHub Actions
→ PR-bound independent audit observation
```

---

## 2. Audit Findings That Must Be Closed

1. Three bootstrap commands currently produce `POST_EXECUTION_RECONCILED` even though required implementation and test commands are absent.
2. Empty execution operations can bypass operation, network and capability checks.
3. Bootstrap identity is caller-supplied rather than derived from authority state.
4. `classify_risk_node()` does not pass path-risk or capability policy into the classifier.
5. preflight applies reference and path-risk checks only to paths outside allowed scope.
6. report-truth code is not connected to the actual project reports.
7. current report and pytest artifacts still belong to the previous Decision.
8. local execution evidence lacks stable command IDs, timestamps, head binding and output digests.

---

## 3. Bootstrap Phase

Use the bootstrap exception only to implement:

- stable command IDs and authority origin;
- strict execution record schema;
- explicit BOOTSTRAP_OPEN / BOOTSTRAP_EXPIRED state;
- `transition-preflight --mode pre`;
- `transition-reconcile --mode post` scaffolding;
- current Decision command-plan regeneration.

Bootstrap must not modify workflow risk routing, report truth, general architecture modules or product code.

After pre-execution authorization succeeds, persist `BOOTSTRAP_EXPIRED`. Later execution records cannot self-declare bootstrap authority.

---

## 4. Required Command Coverage

Post-execution reconciliation must validate both sides:

```text
all supplied records are authorized
AND
all required plan entries have evidence from their declared source
```

A subset of valid records is not completion.

Local provenance, repository truth and exact-head CI are distinct evidence sources. CI-replayable tests should be accepted from exact-head Actions rather than a narrative local claim.

---

## 5. Capability Enforcement

Plan declarations are authoritative. Envelope omission cannot weaken them.

If a plan entry declares operations or network access, the observed record must provide matching or stronger facts. Empty operations, inferred surfaces or missing identity fields must block.

---

## 6. Runtime Risk Wiring

Create an immutable risk-policy snapshot bound to the active Decision and pass it through the LangGraph workflow state.

The real classify node must use path-risk and capability-risk inputs. Direct classifier unit tests are insufficient; full graph tests must prove R2/R3 routing.

---

## 7. Path Contract

Keep these concepts separate:

```text
reference_paths
generated_artifact_paths
allowed_mutated_paths
forbidden_mutated_paths
```

Reference files are always read-only. Generated artifacts may be changed only by their generator. Allowed implementation paths still receive risk classification. Forbidden paths always block.

---

## 8. Report Truth

Wire report-truth logic to an actual `transition-report` command.

Repository reports must describe only current local facts and may not claim `REMOTE_PASSED`. Exact-head remote truth is recorded after workflows complete in a PR #9 audit comment bound to the same head SHA. This avoids endless report commits invalidating the head they describe.

---

## 9. Validation

Required negative tests include:

- missing required command coverage;
- bootstrap-only false completion;
- empty operations bypass;
- network omission bypass;
- forged bootstrap origin;
- expired bootstrap record;
- missing/incorrect execution surface;
- stale Decision/round/head evidence;
- runtime graph path-risk routing;
- missing risk-policy snapshot;
- path contract conflicts;
- stale report/pytest identity;
- incorrect changed-file inventory;
- remote observation bound to a different head.

Run focused suites, graph integration suites, report suites, full repository diagnostic and `git diff --check`. Preserve exact outcomes.

---

## 10. Do Not Do

Do not:

- modify this Decision after activation;
- modify roadmap or architecture documents;
- modify GitHub workflows or dependencies;
- repair unrelated legacy audits or closeout artifacts;
- install BMAD;
- dispatch coding Agents or call model APIs;
- execute unknown binaries or reverse tools;
- modify frontend, User Solve, solver or harness code;
- create another branch or PR;
- push to main;
- merge, rebase, force-push, tag or release;
- begin Evidence Trust Schema or Binary Evidence Firewall work.

---

## 11. Completion Criteria

This round may recommend `ACCEPTED` only if:

1. command IDs and evidence sources are stable;
2. bootstrap expires deterministically;
3. required command coverage is complete;
4. incomplete records fail closed;
5. operation/network/capability omission cannot bypass policy;
6. pre and post execution states are distinct;
7. path risk is wired into the actual LangGraph node;
8. full graph R0-R3 tests pass;
9. path contract groups are semantically separate;
10. report truth generates current-round artifacts;
11. report, pytest and inventory match the active Decision and real diff;
12. local report does not claim remote success;
13. exact-head CI, State Gate and Decision Preflight succeed;
14. a PR #9 audit comment records those run IDs against the same head;
15. PR #9 remains Draft until the independent audit publishes `ACCEPTED`.

If any blocking condition remains, the result is `REWORK_REQUIRED`.

After acceptance, stop creating Architecture Spine governance rounds. Mark PR #9 ready for review, merge it through the normal GitHub path, then begin Evidence Trust Schema Foundation as a separate product phase.