```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260724_p0_minimal_integration_and_legacy_containment_rework_v2",
  "round_id": "round_20260724_p0_minimal_integration_and_legacy_containment_rework_v2",
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
  "follows_last_decision_id": "decision_20260724_p0_minimal_integration_and_legacy_containment_v1",
  "follows_last_round_id": "round_20260724_p0_minimal_integration_and_legacy_containment_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "p0-minimal-integration-and-legacy-containment-rework-v2",
  "source_issue": 28,
  "program_issue": 26,
  "source_pull_request": 27,
  "failed_activation_head": "0ab1d85bd7c38c7cce922c42ea7d1fb79066028d",
  "required_branch": "codex/p0-minimal-integration-baseline-v1",
  "activation_base_sha": "38de9106d191d6b66d5f878354144817095e7bca",
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
      "command_id": "test.minimal_integration_contracts",
      "command": "python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py -q",
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
      "command": "git push origin codex/p0-minimal-integration-baseline-v1",
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
      "command": "gh pr create --draft --base main --head codex/p0-minimal-integration-baseline-v1",
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
    "AGENTS.md",
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    "docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    "project_state/decision_packet.md",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "reference_paths": [
    "README.md",
    "pyproject.toml",
    "reverse_agent/architecture/contracts.py",
    "reverse_agent/workflows/development_graph.py",
    "project_state/current_state.json",
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
    "reverse_agent/**",
    "tests/**",
    "pyproject.toml",
    ".github/workflows/**",
    "frontend/**",
    "solve_reports/**",
    "local_reverse_samples/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/context/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/schemas/**",
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
    "merge",
    "destructive",
    "unknown_binary_execution",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "runner_dispatch",
    "bmad_installation",
    "tag_or_release"
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
      "git push origin codex/p0-minimal-integration-baseline-v1",
      "gh pr create --draft --base main --head codex/p0-minimal-integration-baseline-v1"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": ".env", "minimum_risk": "R3"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"},
    {"pattern": "**/credentials/**", "minimum_risk": "R3"},
    {"pattern": "**/*.exe", "minimum_risk": "R3"},
    {"pattern": "**/*.dll", "minimum_risk": "R3"},
    {"pattern": "**/*.bin", "minimum_risk": "R3"}
  ],
  "scope_policy": "p0_minimal_integration_and_legacy_containment_only",
  "stop_after_exact_head_ci": true
}
```

# DECISION_PACKET

## Goal

Complete one bounded direction-convergence round without building a new generic AI software-development platform.

The active development chain becomes:

```text
approved specification
→ GitHub Issue / Work Item
→ Codex implementation
→ deterministic GitHub Actions
→ independent review
→ human merge
```

This round is documentation and repository-guidance only. The failed v1 activation at `0ab1d85b...` remains immutable history; no documentation implementation occurred under it.

## Current Evidence

- `main` is fixed at `38de9106d191d6b66d5f878354144817095e7bca`.
- Issue #26 is the top-level direction-convergence plan.
- Issue #28 is the current Work Item and acceptance checklist.
- PR #27 is the active Draft PR and branch-local execution surface.
- CI succeeded on the v1 activation head, while Decision Preflight and State Gate stopped at Transition lint; no later Gate or implementation step ran.
- README and `pyproject.toml` still describe conflicting repository identities.
- the Architecture Spine contains reusable contracts, while its LangGraph graph remains non-dispatching and is not the next product runtime.
- PR #11, #19, #21 and #24 remain outside this round.

## Do Not Do

- do not modify product source, tests, dependencies or GitHub workflows;
- do not implement a new Gate, receipt, production verifier, LangGraph runtime, Agent Registry or Web console;
- do not install or bootstrap Spec Kit, BMAD, Open SWE or OpenHands;
- do not start any reverse-engineering, hostile-binary, crash, patch, malware or firmware implementation;
- do not mutate PR #11, #19, #21 or #24;
- do not merge, mark ready, rebase, squash, force-push, tag, release or push directly to `main`;
- do not create a new tracked per-run artifact family;
- do not treat Issue comments as command authority;
- do not continue when the generated Command Plan or preflight is not valid.

## Files To Inspect

- `README.md`
- `pyproject.toml`
- `reverse_agent/architecture/contracts.py`
- `reverse_agent/workflows/development_graph.py`
- `docs/roadmap/**`
- `docs/architecture/**`
- `.github/ISSUE_TEMPLATE/**`
- Issue #26, Issue #28 and Draft PR #27

## Required Audit

1. Is exactly one roadmap marked active?
2. Does it define integration/minimal extension rather than a generic platform build?
3. Does `AGENTS.md` let Codex execute a normal R0/R1 task without reading the legacy closeout corpus?
4. Is GitHub authoritative for Issue, PR, checks and merge state?
5. Are R0/R1 instructions lightweight while R2/R3 remain fail-closed?
6. Are runtime logs and per-run artifacts kept out of tracked source state?
7. Are legacy components classified as retain, compatibility, no-new-features, deferred or archive candidate?
8. Are Architecture Spine contracts inventoried individually rather than accepted or rejected wholesale?
9. Are all security/binary directions explicitly deferred as extension candidates?
10. Did the round avoid all product source, test, dependency and workflow changes?
11. Did focused tests and `git diff --check` pass?
12. Is PR creation the publication boundary, with merge still forbidden?

## Implementation Scope

Create only:

- `AGENTS.md`;
- `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md`;
- `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md`;
- `docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md`;
- `docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md`;
- `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml`.

The roadmap must classify previous plans as `HISTORICAL_REFERENCE`, `COMPATIBILITY_PLAN`, `EXTENSION_CANDIDATE` or `SUPERSEDED`.

The Issue template must capture approved specification, allowed paths, forbidden operations, acceptance criteria and required checks. It must state that an Issue does not authorize R2/R3 operations.

## Tests

Run the compiler-authorized commands, including:

```text
python -m reverse_agent.project_gate transition-command-plan --state-dir project_state
python -m reverse_agent.project_gate transition-lint --state-dir project_state
python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre
python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py -q
git diff --check
```

Do not expand into a full repository repair round for unrelated historical failures.

## Stop Conditions

Stop immediately when:

- Decision or generated Command Plan does not validate;
- branch, base SHA or allowed path differs from this Decision;
- implementation requires source, test, dependency or workflow changes;
- a new governance artifact family appears necessary;
- any operation would mutate an older Draft PR or `main`;
- focused tests fail for reasons inside this round;
- exact-head CI is not green;
- independent audit has not accepted the final head.

Completion target:

```text
MINIMAL_AI_DEVELOPMENT_INTEGRATION_BASELINE_ACCEPTED
```

The round ends after one immutable Draft PR head has successful exact-head checks. Merge remains separately authorized and human-controlled.
