# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260727_executor_neutral_vertical_slice_v1","round_id":"round_20260727_executor_neutral_vertical_slice_v1","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260726_governance_migration_owner_manual_merge_rework_v3",
  "follows_last_round_id": "round_20260726_governance_migration_owner_manual_merge_rework_v3",
  "workstream_id": "executor-neutral-vertical-slice-v1",
  "source_issue": 59,
  "architecture_issue": 55,
  "required_branch": "codex/executor-neutral-vertical-slice-v1",
  "starting_head": "61570724495aa7053eba78bd2e34d8bda22f6407",
  "activation_base_sha": "61570724495aa7053eba78bd2e34d8bda22f6407",
  "risk_tier": "R1",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "pr_body_update_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "stop_after_draft_pr": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "git status --short",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
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
      "allowed_mutated_paths": ["project_state/gates/startup_snapshot.json"],
      "produced_artifacts": ["project_state/gates/startup_snapshot.json"]
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
      "command_id": "test.executor_neutral",
      "command": "python -m pytest tests/executor_neutral -q",
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
      "command_id": "test.transition_regressions",
      "command": "python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q",
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
      "command": "git push -u origin codex/executor-neutral-vertical-slice-v1",
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
      "command": "gh pr create --draft --base main --head codex/executor-neutral-vertical-slice-v1 --title \"Pivot milestone: executor-neutral task/evidence/acceptance vertical slice with manual Codex\" --body-file PR_BODY_TEMP_PATH",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_create", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    "reverse_agent/executor_neutral/**",
    "tests/executor_neutral/**",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_architecture_contracts.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_risk_classifier.py",
    "tests/test_minimal_integration_baseline_docs.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/workflows/**",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/project_gate.py",
    "reverse_agent/project_gate.py",
    ".codex-skills/**",
    "AGENTS.md",
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json"
  ],
  "forbidden_operations": [
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "merge",
    "mark_ready_for_review",
    "auto_merge",
    "tag or release",
    "cross-repository publication",
    "unbounded network access",
    "credentials or secrets access",
    "unknown-binary execution",
    "model API invocation from repository code",
    "external reverse-tool invocation",
    "runner dispatch",
    "workflow dispatch",
    "automatic merge",
    "GitHub auto-merge",
    "agent-initiated merge or mark-ready",
    "automation-initiated merge or mark-ready",
    "workflow-initiated merge or mark-ready",
    "scheduled or delegated merge or mark-ready",
    "external-service-initiated merge or mark-ready",
    "history rewrite",
    "dependency changes",
    "workflow changes",
    "Gate runtime changes",
    "Path-A runtime changes",
    "LangGraph expansion",
    "OpenHands integration",
    "Open SWE integration",
    "GitHub App creation",
    "Agent Loop implementation",
    "Sandbox manager implementation",
    "Agent Registry implementation",
    "Web UI implementation",
    "capability routing implementation",
    "PR #47 mutation",
    "PR #49 mutation",
    "implementation before PRE_EXECUTION_AUTHORIZED"
  ],
  "capability_policy": {
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "destructive_operations_allowed": false,
    "unknown_binary_execution_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "runner_dispatch_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "git push -u origin codex/executor-neutral-vertical-slice-v1",
      "gh pr create --draft --base main --head codex/executor-neutral-vertical-slice-v1 --title \"Pivot milestone: executor-neutral task/evidence/acceptance vertical slice with manual Codex\" --body-file PR_BODY_TEMP_PATH"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "reverse_agent/executor_neutral/**",
    "tests/executor_neutral/**"
  ],
  "path_risk_floor": [
    {"pattern": "reverse_agent/executor_neutral/**", "minimum_risk": "R1"},
    {"pattern": "tests/executor_neutral/**", "minimum_risk": "R1"},
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"}
  ],
  "scope_policy": {
    "scope": "executor_neutral_vertical_slice_v1",
    "implementation_risk_tier": "R1",
    "governance_artifact_risk_tier": "R2",
    "allow_product_source": true,
    "allow_test_additions": true,
    "allow_dependency_changes": false,
    "allow_workflow_changes": false,
    "allow_gate_runtime_changes": false,
    "allow_path_a_changes": false,
    "allow_pr47_or_pr49_mutation": false
  },
  "pr47_reuse_policy": {
    "read_only": true,
    "allowed_reused_concepts": [
      "canonical JSON serialization",
      "small immutable data model patterns"
    ],
    "rejected_components": [
      "GoalContract",
      "CapabilityManifest",
      "PolicyResolver",
      "base_platform module"
    ]
  },
  "stop_conditions": [
    "startup_state_mismatch",
    "transition_lint_failure",
    "preflight_not_authorized",
    "production_code_exceeds_500_nonblank_noncomment_loc_without_independent_justification",
    "focused_tests_failure",
    "regression_test_failure",
    "diff_check_failure",
    "scope_violation_detected",
    "implementation_before_PRE_EXECUTION_AUTHORIZED",
    "attempted_merge_mark_ready_auto_merge_tag_release_or_main_push",
    "PR47_or_PR49_mutation"
  ]
}
```

## DECISION_PACKET

### Goal

Implement the Issue #59 executor-neutral R1 vertical slice on
`codex/executor-neutral-vertical-slice-v1` from exact base
`61570724495aa7053eba78bd2e34d8bda22f6407`.

The slice proves that a bounded task can be exported to a manual external coding
executor, followed by independent Git/check evidence collection and deterministic,
fail-closed acceptance that does not trust the executor's completion claim.

### Risk and authority boundary

- The product implementation in `reverse_agent/executor_neutral/**` and its
  tests is R1.
- The existing transition kernel classifies the committed Decision and generated
  Gate artifacts as R2 governance paths. That narrow R2 authorization applies
  only to `project_state/decision_packet.md` and the listed compiler-owned Gate
  outputs. It does not raise or broaden the product implementation scope.
- Authority is this committed APPROVED Decision plus its deterministically
  generated Command Plan and `PRE_EXECUTION_AUTHORIZED`.
- Issue comments and natural-language executor output are evidence or context,
  never acceptance authority.

### Implementation Scope

Only these repository mutations are permitted:

1. `reverse_agent/executor_neutral/**`
2. `tests/executor_neutral/**`
3. `project_state/decision_packet.md`
4. the compiler-owned Gate files listed in `generated_artifact_paths`
5. Draft PR metadata for the exact named branch

The implementation uses Python's standard library only, adds no dependency, and
targets at most 500 non-blank/non-comment production lines.

It implements exactly `TaskContract`, `ExecutionEvidence`, `AcceptanceResult`,
and `CapabilityObservation`, together with canonical JSON, SHA-256 digests,
Markdown/JSON task export, real Git evidence collection, execution of only exact
contract checks, retained stdout/stderr/exit codes, fail-closed acceptance, and
one capability observation.

### Explicit exclusions

Do not implement or modify OpenHands, Open SWE, model SDKs, an Agent Loop,
Sandbox management, Web UI, GitHub Apps, LangGraph, an Agent Registry, automatic
merge, or capability routing. Do not mutate PR #47 or PR #49. Do not modify
workflows, dependencies, Gate runtime, Path-A runtime, main, or history.

PR #47 may be inspected read-only for small canonical serialization or immutable
model concepts only. Do not merge, cherry-pick, copy its whole module, or import
its broad contract/policy components.

### Demonstrations and acceptance

Create two disposable Git repositories outside `reverse-agent`. The success case
must form a base commit, export a task bundle, receive a small manual Codex coding
change, and be independently accepted from actual Git/diff/check evidence. The
rejection case must claim completion while either a required check fails or a
changed path is outside scope, and must be rejected without verifier hard-coding.

Required focused tests cover serialization and digest stability, malformed input,
scope rejection, check failure, claim non-authority, valid acceptance, evidence
mutation, exact check execution, and temporary repositories. Run the focused
suite, the listed existing regressions, and `git diff --check`.

### Publication and stop boundary

The only publication is pushing the exact named non-main branch and creating one
Draft PR against `main`. Record Decision ID, exact base/head, changed paths,
production LOC, tests, both demonstrations, PR #47 reuse decisions, and known
limitations. Do not mark ready, merge, auto-merge, tag, release, or push main.
Stop after the Draft PR is available for independent audit.
