# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260727_executor_neutral_binding_rework_v2","round_id":"round_20260727_executor_neutral_binding_rework_v2","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260727_executor_neutral_vertical_slice_v1",
  "follows_last_round_id": "round_20260727_executor_neutral_vertical_slice_v1",
  "previous_audit_outcome": "REWORK_REQUIRED_HEAD_2ca90c52_F1_F2_F3_F4",
  "workstream_id": "executor-neutral-binding-rework-v2",
  "source_issue": 61,
  "predecessor_issue": 59,
  "active_pr": 60,
  "required_branch": "codex/executor-neutral-vertical-slice-v1",
  "starting_head": "2ca90c52ae59dfc5567c251066952d169dc7352c",
  "activation_base_sha": "61570724495aa7053eba78bd2e34d8bda22f6407",
  "risk_tier": "R1",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "stop_after_exact_head_ci": true,
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
      "command": "git push origin codex/executor-neutral-vertical-slice-v1",
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
      "command_id": "publication.update_pr_body",
      "command": "gh pr edit 60 --body-file PR_BODY_TEMP_PATH",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_edit", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.comment_pr_evidence",
      "command": "gh pr comment 60 --body-file PR_COMMENT_TEMP_PATH",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/executor_neutral/**",
    "tests/executor_neutral/**"
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
    "new branch",
    "new pull request",
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
    "shell policy engine implementation",
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
      "git push origin codex/executor-neutral-vertical-slice-v1",
      "gh pr edit 60 --body-file PR_BODY_TEMP_PATH",
      "gh pr comment 60 --body-file PR_COMMENT_TEMP_PATH"
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
    "scope": "executor_neutral_binding_rework_v2",
    "implementation_risk_tier": "R1",
    "governance_artifact_risk_tier": "R2",
    "allow_product_source": true,
    "allow_test_changes": true,
    "allow_dependency_changes": false,
    "allow_workflow_changes": false,
    "allow_gate_runtime_changes": false,
    "allow_path_a_changes": false,
    "allow_new_branch_or_pr": false,
    "allow_pr47_or_pr49_mutation": false
  },
  "rework_semantics": {
    "audit_findings": ["F1", "F2", "F3", "F4"],
    "temporary_index_snapshot_required": true,
    "real_index_path_and_bytes_immutable": true,
    "tree_based_changed_paths_required": true,
    "tree_based_diff_check_required": true,
    "contract_digest_binding_required": true,
    "minimal_allowed_path_grammar_required": true,
    "fixed_required_check_timeout_required": true,
    "repository_identity_role": "descriptive routing identity included in canonical TaskContract digest; base_commit, base_tree, and observed_tree are authoritative content identities",
    "required_checks_role": "trusted TaskContract command authority; this rework does not add a shell policy engine or sandbox",
    "sanitized_demo_json_comment_required": true
  },
  "stop_conditions": [
    "startup_state_mismatch",
    "transition_lint_failure",
    "preflight_not_authorized",
    "focused_tests_failure",
    "regression_test_failure",
    "diff_check_failure",
    "scope_violation_detected",
    "implementation_before_PRE_EXECUTION_AUTHORIZED",
    "exact_head_CI_failure",
    "exact_head_State_Gate_failure",
    "exact_head_Decision_Preflight_failure",
    "attempted_new_branch_or_PR",
    "attempted_merge_mark_ready_auto_merge_tag_release_or_main_push",
    "PR47_or_PR49_mutation"
  ]
}
```

## DECISION_PACKET

### Goal

Repair only audit findings F1-F4 on existing Draft PR #60, existing branch
`codex/executor-neutral-vertical-slice-v1`, starting from exact head
`2ca90c52ae59dfc5567c251066952d169dc7352c` and exact base
`61570724495aa7053eba78bd2e34d8bda22f6407`.

### Risk and authority boundary

- The executor-neutral product and test rework is R1.
- The existing transition kernel classifies the committed Decision and generated
  Gate artifacts as R2 governance paths. That narrow R2 authorization applies
  only to the listed `project_state` files and does not broaden implementation.
- Authority is this committed APPROVED Decision plus its generated Command Plan
  and `PRE_EXECUTION_AUTHORIZED`.
- The independent audit and Issue #61 describe the required repair but are not
  execution authority by themselves.

### Implementation Scope

Only the following repository paths may change:

1. `project_state/decision_packet.md`
2. the five listed compiler-owned Gate artifacts
3. `reverse_agent/executor_neutral/**`
4. `tests/executor_neutral/**`

PR #60 body and comments may be updated after the branch is pushed. No new branch
or PR is authorized.

### Required repairs

1. Build an immutable observed workspace tree using a function-owned temporary
   Git index, `read-tree`, `add -A -- .`, and `write-tree`. Resolve the real index
   with `git rev-parse --git-path index`; verify its path and bytes do not change;
   clean up only the function-owned temporary index in `finally`.
2. Derive changed paths and `git diff --check` from the base tree to the observed
   tree. Cover staged, unstaged, deleted, renamed, and non-ignored untracked files.
3. Add the exact canonical `TaskContract.digest` to evidence and acceptance.
   Fail closed on contract, schema, task, base commit/tree, observed tree, or
   digest mismatch/malformed values.
4. Normalize allowed paths at TaskContract construction. Accept only exact
   repository-relative file paths and a terminal recursive `/**` directory
   prefix. Reject every other wildcard, traversal, absolute, empty-component,
   and ambiguous form. Do not use general `fnmatch` authorization.
5. Add one fixed documented timeout for each trusted required-check string.
   Convert `TimeoutExpired` into structured failed evidence containing command,
   timeout state/seconds, exit code, and captured stdout/stderr.

`repository_identity` is a descriptive routing identity included in canonical
TaskContract bytes and therefore bound by `contract_digest`. `base_commit`,
`base_tree`, and `observed_tree` are the authoritative content identities.

Required-check strings remain trusted TaskContract command authority. A shell
policy engine and sandbox are explicitly outside this rework.

### Verification and evidence

Add the Issue #61 test matrix for staged/unstaged/deleted/untracked/ignored tree
content, immutable real index, tree/digest mutation, path grammar, untracked
whitespace errors, timeout evidence, claim non-authority, and malformed binding
fields. Use temporary fixture repositories only.

Run the focused suite, the four specified regression files, `git diff --check`,
and all other required commands in the generated plan.

After tests pass, create exactly two new disposable repositories outside
reverse-agent. Publish sanitized TaskContract, ExecutionEvidence,
AcceptanceResult, and CapabilityObservation JSON plus tree/digest/check details
to PR #60. Do not publish credentials, private paths, unrelated source, or commit
demo repositories to reverse-agent.

### Explicit exclusions and stop boundary

Do not create a branch or PR; mutate PR #47, PR #49, main, workflows, Path-A,
Gate runtime, dependencies, or unrelated documentation; implement OpenHands,
Open SWE, Agent Loop, Sandbox, shell policy engine, LangGraph platform, Agent
Registry, Web UI, GitHub App, automatic merge, capability routing, or model calls;
or rebase, force-push, squash, mark-ready, merge, auto-merge, tag, or release.

After pushing the existing branch, updating Draft PR #60, publishing sanitized
demo evidence, and observing CI, State Gate, and Decision Preflight all succeed
on one exact final head, stop for independent audit.
