# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue136_agent_canvas_direct_reuse_spike_v1",
  "round_id": "round_20260808_issue136_agent_canvas_direct_reuse_spike_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_pr134_frontend_opencode_devup_landing_v1",
  "follows_last_round_id": "round_20260808_pr134_frontend_opencode_devup_landing_v1",
  "previous_audit_outcome": "PR134_LANDED_AND_MANUAL_GUI_EXPOSED_STRUCTURAL_ADAPTATION_GAP",
  "workstream_id": "issue136-agent-canvas-direct-reuse-spike-v1",
  "source_issue": 136,
  "parent_issue": 127,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v1",
  "starting_head": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
  "activation_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": true,
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_provider_probe_allowed": false,
  "model_execution_required": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "agent_canvas_ui_reference_execution_allowed": true,
  "package_installation_allowed": true,
  "package_installation_scope": [
    "F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/**",
    "F:/reverse-agent-workspaces/issue136-agent-canvas-embed-probe/**",
    "F:/reverse-agent-workspaces/issue136-agent-canvas-capture/**"
  ],
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "bounded_external_source_access_allowed": true,
  "bounded_external_sources": [
    "npm registry metadata and packages for @openhands/agent-canvas@1.6.1 and screenshot/build-only harness dependencies",
    "official OpenHands Agent Canvas repository pinned to tag v1.6.1"
  ],
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git fetch origin main",
    "git switch main",
    "git merge --ff-only origin/main",
    "git rev-parse HEAD",
    "git rev-parse origin/main",
    "git diff --name-only 200964fee8c5bf7325addee0496cfb287e2da857..HEAD",
    "git ls-remote --heads origin owner/issue136-agent-canvas-reuse-spike-v1",
    "git switch -c owner/issue136-agent-canvas-reuse-spike-v1",
    "git add project_state/decision_packet.md",
    "git commit -m governance: authorize issue136 Agent Canvas reuse spike",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "observation.git_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.git_head",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.git_main",
      "command": "git rev-parse origin/main",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.git_merge_base",
      "command": "git merge-base HEAD origin/main",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/startup_snapshot.json"]
    },
    {
      "command_id": "gate.transition_command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"]
    },
    {
      "command_id": "gate.transition_lint",
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "gate.transition_preflight",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/transition_preflight_result.json", "project_state/gates/bootstrap_state.json"]
    },
    {
      "command_id": "observation.node_version",
      "command": "node --version",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.npm_version",
      "command": "npm --version",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.frontend_peers",
      "command": "npm --prefix frontend ls react react-dom react-router --depth=0",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["dependency_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.package_metadata",
      "command": "npm view @openhands/agent-canvas@1.6.1 version license engines repository peerDependencies exports --json",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_network_access", "package_metadata_observation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "experiment.clone_upstream",
      "command": "git clone --branch v1.6.1 --depth 1 https://github.com/All-Hands-AI/agent-canvas.git F:/reverse-agent-upstreams/agent-canvas-v1.6.1",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_network_access", "external_source_checkout"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "experiment.package_probe_install",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe install @openhands/agent-canvas@1.6.1",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_network_access", "external_package_installation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": []
    },
    {
      "command_id": "experiment.agent_canvas_help",
      "command": "F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/node_modules/.bin/agent-canvas.cmd --help",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["upstream_ui_reference_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "experiment.agent_canvas_frontend_only",
      "command": "F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/node_modules/.bin/agent-canvas.cmd --frontend-only",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0, 130],
      "execution_surface": "local",
      "operations": ["upstream_ui_reference_execution", "local_process_execution"],
      "network_access": false,
      "required_evidence_source": "screenshot_evidence"
    },
    {
      "command_id": "experiment.capture_install",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-capture install playwright-core",
      "phase": "experiment",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_network_access", "external_package_installation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": []
    },
    {
      "command_id": "experiment.capture_screenshots",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-capture run capture",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["browser_execution", "screenshot_capture", "file_mutation"],
      "network_access": false,
      "required_evidence_source": "screenshot_evidence",
      "allowed_mutated_paths": ["frontend/artifacts/agent-canvas-v1.6.1/**"]
    },
    {
      "command_id": "experiment.embed_normal_install",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-embed-probe install @openhands/agent-canvas@1.6.1",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["bounded_network_access", "external_package_installation", "compatibility_probe"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": []
    },
    {
      "command_id": "experiment.embed_diagnostic_install",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-embed-probe install --legacy-peer-deps @openhands/agent-canvas@1.6.1",
      "phase": "experiment",
      "required": false,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["bounded_network_access", "external_package_installation", "diagnostic_compatibility_probe"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": []
    },
    {
      "command_id": "experiment.embed_build",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-embed-probe run build",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["local_build", "compatibility_probe"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": []
    },
    {
      "command_id": "validation.frontend_test",
      "command": "npm --prefix frontend test",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.frontend_typecheck",
      "command": "npm --prefix frontend run typecheck",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.frontend_lint",
      "command": "npm --prefix frontend run lint",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.frontend_build",
      "command": "npm --prefix frontend run build",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.git_diff_check",
      "command": "git diff --check dd4cb074ab5b9baacf300706878b29bd745f12c3..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.git_diff_name_only",
      "command": "git diff --name-only dd4cb074ab5b9baacf300706878b29bd745f12c3..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.commit_evidence",
      "command": "git commit -m frontend: evaluate direct Agent Canvas reuse",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/gates/**",
        "frontend/AGENT_CANVAS_DIRECT_REUSE_SPIKE.md",
        "frontend/artifacts/agent-canvas-v1.6.1/**"
      ]
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push -u origin owner/issue136-agent-canvas-reuse-spike-v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/AGENT_CANVAS_DIRECT_REUSE_SPIKE.md",
    "frontend/artifacts/agent-canvas-v1.6.1/**"
  ],
  "reference_paths": [
    "AGENTS.md",
    "frontend/package.json",
    "frontend/src/**",
    "frontend/tests/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/**",
    "frontend/tests/**",
    "frontend/*.ts",
    "frontend/*.tsx",
    "frontend/*.css",
    "dev-up.ps1",
    "dev-down.ps1",
    "docs/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "provider_login",
    "provider_configuration_mutation",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_agent_invocation",
    "agent_task_submission",
    "github_publication_controller_implementation",
    "production_frontend_workbench_replacement",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "unbounded_network_access",
    "create_pr",
    "pr_creation",
    "draft_pr_creation",
    "pr_body_update",
    "merge",
    "mark_ready",
    "reset_hard",
    "git_clean"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "agent_canvas_ui_reference_execution_allowed": true,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "npm view @openhands/agent-canvas@1.6.1 version license engines repository peerDependencies exports --json",
      "git clone --branch v1.6.1 --depth 1 https://github.com/All-Hands-AI/agent-canvas.git F:/reverse-agent-upstreams/agent-canvas-v1.6.1",
      "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe install @openhands/agent-canvas@1.6.1",
      "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-capture install playwright-core",
      "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-embed-probe install @openhands/agent-canvas@1.6.1",
      "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-embed-probe install --legacy-peer-deps @openhands/agent-canvas@1.6.1",
      "git push -u origin owner/issue136-agent-canvas-reuse-spike-v1"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "frontend/AGENT_CANVAS_DIRECT_REUSE_SPIKE.md",
    "frontend/artifacts/agent-canvas-v1.6.1/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "frontend/AGENT_CANVAS_DIRECT_REUSE_SPIKE.md", "minimum_risk": "R1"},
    {"pattern": "frontend/artifacts/agent-canvas-v1.6.1/**", "minimum_risk": "R1"}
  ]
}
```

## Goal

Issue #136 Stage A is a bounded compatibility and architecture-selection spike against `@openhands/agent-canvas@1.6.1`. It is not a production frontend implementation.

The spike will run the pinned upstream Agent Canvas frontend reference without submitting any agent or model task, capture sanitized 1440x900 screenshots of the real upstream reference and the current reverse-agent mock frontend, test normal package installation against the current reverse-agent React/React DOM/React Router versions, and trace public package imports plus runtime context dependencies in disposable external harnesses.

The final report must select exactly one disposition:

```text
AGENT_CANVAS_PACKAGE_EMBED_ACCEPTED
AGENT_CANVAS_PINNED_SOURCE_FORK_SELECTED
```

Package embed may be accepted only when the mature shell renders through public exports while reverse-agent retains its Task API, TaskStore, task client/hooks, OpenCode executor, and evidence contracts, with only thin presentation/data adapters. It must be rejected if it requires fake OpenHands Agent Server endpoints, substantial settings/config or conversation API emulation, a fake backend registry, a large provider/context layer, or a parallel execution state model.

If package embed is rejected, the report must identify the smallest exact pinned upstream source subset for Stage B and state, per file, why it is directly reused, which OpenHands data hook is removed, and which reverse-agent adapter replaces it. Stage A must not implement that fork.

## Credential and model boundary

Running the published Agent Canvas UI/reference binary in frontend-only/static mode is allowed. Running an OpenHands Agent, configuring a provider, logging into a provider, invoking OpenCode or Codex, or submitting any task that can call a model is forbidden.

Credential values, credential files, environment variable values, provider configuration, private repository contents, personal account data, API keys, tokens, cookies, and login blobs must not be read, printed, copied, transformed, uploaded, or committed. Only zero-count statements and non-secret dependency/runtime metadata may be recorded.

Required final counts:

```text
model calls = 0
OpenCode calls = 0
Codex calls = 0
provider credential reads = 0
provider config mutations = 0
```

## Acceptance

1. The branch starts at exact main `dd4cb074ab5b9baacf300706878b29bd745f12c3`; the accepted PR134 product-tree ancestor `200964fee8c5bf7325addee0496cfb287e2da857` has zero changed files through that main head.
2. The Decision commit precedes all gate generation, npm metadata/package access, upstream clone, frontend reference execution, browser capture, and compatibility experiments.
3. The standard transition sequence passes: transition-command-plan `PASS`, transition-lint `PASS`, transition-preflight `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`.
4. Package installation occurs only in the named external scratch harnesses, never in `frontend/`.
5. Official upstream source is pinned to release tag `v1.6.1`, its full commit SHA is recorded, and the checkout remains unmodified.
6. The real Agent Canvas frontend reference is run with zero Agent/model execution and captured at 1440x900 without credentials or personal data.
7. The current reverse-agent frontend is run in deterministic/mock mode with zero model execution and captured at 1440x900 without production frontend changes.
8. Normal npm installation against current reverse-agent peer versions is attempted first; any conflict is preserved as evidence. A forced or legacy-peer diagnostic install cannot by itself justify package-embed acceptance.
9. The root/provider, sidebar, conversation, files, settings, and terminal surfaces are evaluated using actual public exports, builds, runtime renders, import traces, and runtime errors rather than inference.
10. `frontend/AGENT_CANVAS_DIRECT_REUSE_SPIKE.md` contains every required section, exact metadata and matrices, a single selected disposition, evidence rejecting the alternative, and an exact Stage B boundary.
11. Both screenshots are committed under `frontend/artifacts/agent-canvas-v1.6.1/` and are inspected before acceptance.
12. `npm --prefix frontend test`, `typecheck`, `lint`, and `build` pass without installing or changing packages in the tracked frontend.
13. Only the authorized Decision, gate artifacts, report, and screenshots are changed; no production TS/TSX/CSS/package, backend, test, workflow, script, doc, mainline-intent, or schema path changes.
14. `git diff --check dd4cb074ab5b9baacf300706878b29bd745f12c3..HEAD` passes.
15. Evidence is committed with the exact message and normally pushed only to `owner/issue136-agent-canvas-reuse-spike-v1`; local and remote heads match.
16. No PR is created. No Issue #135 mutation, Stage B implementation, Ready, merge, main push, release, deploy, force push, rebase, amend, reset, or clean occurs.

```text
ISSUE136_STAGE_A_AGENT_CANVAS_DIRECT_REUSE_EVIDENCE_READY_FOR_OWNER_AUDIT
```

## Execution policy

- This R3 Decision follows and supersedes `decision_20260808_pr134_frontend_opencode_devup_landing_v1` only for Issue #136 Stage A.
- Preserve `.frontend_stage/`, `.platform_v1_runtime/`, and every other pre-existing staged, unstaged, or untracked path. Stop on unknown tracked changes.
- External scratch roots are fixed to `F:/reverse-agent-upstreams/agent-canvas-v1.6.1` and `F:/reverse-agent-workspaces/issue136-agent-canvas-{package-probe,embed-probe,capture}`. If a target exists and identity cannot be proven safe, stop; never delete, reset, or overwrite it.
- Do not begin experimental execution until preflight returns `PRE_EXECUTION_AUTHORIZED` with no blockers.
- Product Design screenshot/audit work is evidence-only and cannot broaden the authorized repository paths, network destinations, browser identity, runtime behavior, or publication boundary.
- Publication ends after the exact spike branch normal push and remote-head equality check. Owner audit and a separate Stage B Decision are required for any production frontend work.
