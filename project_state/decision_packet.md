```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260721_architecture_spine_authority_closure_rework_v1",
  "round_id": "round_20260721_architecture_spine_authority_closure_rework_v1",
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
  "follows_last_decision_id": "decision_20260720_transition_bootstrap_and_architecture_spine_v1",
  "follows_last_round_id": "round_20260720_transition_bootstrap_and_architecture_spine_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "architecture-spine-authority-closure-rework-v1",
  "source_pull_request": 9,
  "required_branch": "codex/architecture-spine-v1",
  "activation_base_sha": "aa87aad81404bf940f8c262a3be5dcf7222258db",
  "source_architecture_head_sha": "71c794dc16477fa68943dd42ca4978f744f93f7e",
  "roadmap_path": "docs/roadmap/architecture_spine_authority_closure_rework_v1.md",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_kernel_required": true,
  "authority_closure_required": true,
  "legacy_state_maintenance_is_primary_goal": false,
  "legacy_final_check_is_acceptance_authority": false,
  "legacy_closeout_is_acceptance_authority": false,
  "legacy_state_manifest_is_acceptance_authority": false,
  "command_plan_generated_from_active_decision_required": true,
  "command_plan_precedes_normal_implementation_required": true,
  "execution_reconciliation_required": true,
  "capability_policy_mapping_required": true,
  "reference_mutation_scope_separation_required": true,
  "path_risk_floor_required": true,
  "github_truth_reconciliation_required": true,
  "bootstrap_exception_authorized": true,
  "bootstrap_exception_reason": "The current transition command-plan builder can only consume bootstrap_exception_commands and transition-preflight can pass command authority without reconciling the real execution set. A narrowly bounded bootstrap is required to add structured allowed_commands and real execution reconciliation before the normal rework can be authorized.",
  "bootstrap_exception_expires_when": "A command plan generated from allowed_commands matches this Decision, transition-lint passes, transition-preflight validates the current branch and scope, and the bootstrap execution records are explicitly classified as bootstrap exceptions.",
  "bootstrap_exception_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_authority_closure.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/execution_log.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git rev-parse HEAD",
    "git branch --show-current",
    "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_authority_closure.py -q",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state",
    "git diff --check"
  ],
  "allowed_commands": [
    {
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false
    },
    {
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false
    },
    {
      "command": "git branch --show-current",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false
    },
    {
      "command": "python -m pip install -e \".[test]\" --no-deps",
      "phase": "dependency",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["dependency_install"],
      "network_access": false
    },
    {
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["command_plan_generation"],
      "network_access": false
    },
    {
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authority_validation"],
      "network_access": false
    },
    {
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authority_validation"],
      "network_access": false
    },
    {
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_authority_closure.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test"],
      "network_access": false
    },
    {
      "command": "python -m pytest tests/test_architecture_contracts.py tests/test_risk_classifier.py tests/test_development_graph.py tests/test_trust_authorization_adapter.py tests/test_planning_and_github_adapters.py tests/test_report_truth.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test"],
      "network_access": false
    },
    {
      "command": "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py tests/test_control_plane_transition.py tests/test_authority_closure.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false
    },
    {
      "command": "python -m pytest -q",
      "phase": "diagnostic",
      "required": false,
      "diagnostic_only": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["full_repository_test"],
      "network_access": false
    },
    {
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false
    },
    {
      "command": "git push origin codex/architecture-spine-v1",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "allowed_only_after_validation": true
    },
    {
      "command": "python -m pip install -e \".[test]\"",
      "phase": "ci_dependency",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["dependency_install", "network_access"],
      "network_access": true
    },
    {
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "ci_gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["command_plan_generation"],
      "network_access": false
    },
    {
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "ci_gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["authority_validation"],
      "network_access": false
    },
    {
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state",
      "phase": "ci_gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["authority_validation"],
      "network_access": false
    }
  ],
  "reference_paths": [
    "docs/roadmap/architecture_spine_authority_closure_rework_v1.md",
    "docs/roadmap/reverse_agent_unified_architecture_and_trust_roadmap.md",
    "docs/architecture/architecture-spine-v1.md",
    "docs/architecture/control-plane-transition-kernel.md",
    "project_state/decision_packet.md",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "allowed_mutated_paths": [
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/architecture/contracts.py",
    "reverse_agent/architecture/risk_classifier.py",
    "reverse_agent/architecture/report_truth.py",
    "reverse_agent/workflows/nodes/classify_risk.py",
    "reverse_agent/adapters/github_truth.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_architecture_contracts.py",
    "tests/test_risk_classifier.py",
    "tests/test_development_graph.py",
    "tests/test_trust_authorization_adapter.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_authority_closure.py",
    "tests/test_report_truth.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md"
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
    "**/credentials/**"
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
  "unknown_operation_policy": "BLOCKED",
  "unknown_sensitive_path_policy": "BLOCKED",
  "report_truth_required": true,
  "changed_files_from_git_diff_required": true,
  "exact_head_remote_observation_required": true,
  "remote_status_values": [
    "REMOTE_NOT_OBSERVED",
    "REMOTE_PENDING",
    "REMOTE_PASSED",
    "REMOTE_FAILED"
  ],
  "local_status_values": [
    "LOCAL_VALIDATED",
    "LOCAL_PARTIAL",
    "LOCAL_FAILED"
  ],
  "draft_pull_request_allowed": true,
  "existing_pull_request_only": 9,
  "new_pull_request_allowed": false,
  "scope_policy": "authority_closure_only",
  "stop_after_independent_audit_handoff": true
}
```

# DECISION_PACKET

## 1. Goal

Repair the Architecture Spine v1 authority boundary without expanding product scope.

The result must close the following chain:

```text
active Decision
→ structured allowed_commands
→ generated current command plan
→ pre-execution authorization
→ actual execution records
→ post-execution reconciliation
→ capability and path-risk enforcement
→ truthful Git/GitHub report
```

The previous round established the intended architecture, but the independent audit found that its command plan covered only bootstrap commands while the real execution included additional tests, dependency installation and final validation. The current transition preflight can also report command authority as passed when no real execution envelopes are supplied. These defects must be repaired before PR #9 can be accepted.

---

## 2. Current Evidence

- Continue only on `codex/architecture-spine-v1` and Draft PR #9.
- The planning baseline is commit `aa87aad81404bf940f8c262a3be5dcf7222258db`.
- The previous Architecture Spine implementation head was `71c794dc16477fa68943dd42ca4978f744f93f7e`.
- The previous focused architecture suite and control-plane suite passed.
- The previous full suite had one known legacy audit-document failure outside the prior Decision scope.
- Exact-head CI, State Gate and Decision Preflight for the previous head were observed successful.
- The current blocker is authority truth, not general Architecture Spine functionality.
- The roadmap document is context only and may not authorize implementation.
- This Decision must be committed before any new implementation.

---

## 3. Phase A — Authority Bootstrap Closure

Before normal implementation, use only the explicit bootstrap exception to:

1. add support for structured `allowed_commands`;
2. generate the current command plan from this Decision;
3. add execution-surface, operations and network fields to command authority;
4. record bootstrap commands separately from normal plan-authorized commands;
5. run the bootstrap-focused tests;
6. run transition-command-plan, transition-lint and transition-preflight.

If the generated plan identity, branch, activation base, path scope or command schema is invalid, stop. Do not continue to normal implementation.

---

## 4. Phase B — Real Execution Reconciliation

Implement a deterministic reconciliation path that checks actual execution records against the generated plan.

Required behavior:

1. real command, execution surface, paths, operations and exit code are preserved;
2. each actual command is matched against one exact plan entry;
3. undeclared commands block;
4. cross-surface execution blocks;
5. missing execution evidence cannot produce a positive reconciliation claim;
6. bootstrap exceptions are identified explicitly;
7. pre-execution authorization and post-execution reconciliation remain separate statuses;
8. report generation consumes reconciliation facts rather than inferred coverage.

---

## 5. Phase C — Capability and Scope Enforcement

Implement complete mapping for all capability fields in the Decision.

Reference paths are read-only. They must not be added to mutable scope merely because they are named in the Decision.

The Decision file and roadmap are immutable during implementation. Any attempted mutation must block.

Network access is denied by default. Only the exact declared publication command and CI dependency-install command are exceptions. No generic `git pull`, package resolution or remote API access is authorized.

---

## 6. Phase D — Path-Aware Risk Classification

Change risk calculation to use the highest of:

```text
operation risk
path risk floor
capability flag risk
```

A caller cannot lower workflow, dependency, Decision, gate, secret, binary or destructive work by labeling it as a generic source edit.

Add negative tests for operation under-reporting, sensitive paths, unknown operations and unknown sensitive paths.

---

## 7. Phase E — Report Truth Closure

Generate changed-file inventory from the real Git diff.

The final report must clearly separate local validation from remote observations. It must not simultaneously claim that exact-head checks are both observed and pending.

After local validation:

```text
push current branch
→ observe exact remote head
→ observe CI, State Gate and Decision Preflight
→ update final report
→ stop
```

The PR remains Draft and must not be merged.

---

## 8. Required Tests

At minimum, test:

1. structured command-plan generation;
2. Decision/round identity invalidation;
3. undeclared command rejection;
4. execution-surface mismatch rejection;
5. missing real execution evidence rejection;
6. bootstrap exception separation;
7. capability flag mapping;
8. local network denial and exact exceptions;
9. reference paths remain read-only;
10. allowed/forbidden path conflicts block;
11. workflow and dependency paths reach at least R2;
12. secrets, binaries and destructive paths reach R3;
13. operation under-reporting cannot reduce risk;
14. changed-file inventory matches Git diff;
15. remote status is internally consistent;
16. stale observation cannot support a new head.

Run the required focused suites and `git diff --check`. Run the full repository suite as a diagnostic and preserve its exact outcome. Do not convert a diagnostic failure into a full pass.

---

## 9. Do Not Do

Do not:

- alter this Decision after activation;
- modify roadmap or architecture documents;
- modify GitHub workflows or `pyproject.toml`;
- repair unrelated legacy audit documents;
- install BMAD;
- add a second workflow runtime;
- dispatch coding Agents;
- call model APIs;
- run unknown binaries or reverse tools;
- modify User Solve, frontend, solver or harness code;
- modify legacy closeout, final-seal, context or state-manifest systems;
- create another branch or pull request;
- push directly to main;
- merge, rebase, force-push, tag or release;
- begin Evidence Trust Schema or Binary Evidence Firewall work.

---

## 10. Completion Criteria

The round may recommend `ACCEPTED` only if:

1. this Decision generated the current structured command plan;
2. transition-lint and transition-preflight pass;
3. all real execution records reconcile with the plan or an explicit bootstrap exception;
4. no undeclared command is hidden by an empty-envelope preflight;
5. capability flags are enforced;
6. reference and mutable scopes are separated;
7. path-aware risk floors are enforced;
8. focused tests pass;
9. full-suite truth is preserved;
10. changed-file inventory matches Git diff;
11. exact-head CI, State Gate and Decision Preflight are observed;
12. the final report contains no local/remote status contradiction;
13. PR #9 remains Draft and unmerged.

If any authority, scope, risk or report-truth condition remains open, the result is `REWORK_REQUIRED`.

After completion, stop for independent audit. Do not automatically start BMAD adoption or the Trust Layer product phase.