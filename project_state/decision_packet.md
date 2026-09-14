# Decision Packet — bounded instruction repair

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260914_issue884_compact_instructions_r2_v1",
  "round_id": "round_20260914_issue884_compact_instructions_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "BOUNDED_AGENT_INSTRUCTION_REPAIR",
  "source_issue": 884,
  "parent_issue": 642,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated Agent authoring",
  "approval_basis": "The user requested reading the OpenAI article, auditing this project's instructions and correcting them. Existing project Owner delegation is used only for this bounded instruction repair. This is an Agent-authored approval, not independent human review, and does not authorize Ready or Merge.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "activation_base_sha": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "starting_head": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "required_branch": "owner/issue642-compact-instructions-r2-v1",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 5,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Repair the current instruction entry points using progressive disclosure and short authority locators. Root AGENTS becomes a compact current Nerelan entry with conditional references, retaining every existing permission, risk, immutable authority, exact-base/head, dirty-work, Draft and owner-versus-Agent landing predicate. Do not implement #677 or relax Ready/Merge. Narrow the generic engineering and explicit sample skill triggers, move detailed procedures into skill-local references, and retain registry keys/scopes/v2 profile compatibility. Replace universal Windows-drive and Decision-only task prompts with role/surface-specific non-authoritative bootstrap locators. Preserve conditional legacy report and sample constraints without loading them for ordinary Path A. Safe development iterations are allowed only under the existing task authority and budget; mandatory check failure, drift and capability/permission gaps remain blocking. Completion requires actual artifact/check evidence, not a first draft or self-review. Add provider-free regression tests without changing existing tests/lint. Measure text bytes/lines only; no unmeasured model quality/token/latency claims.",
    "execution_surface_note": "This is a GitHub-first branch. The activation is Decision-only and can open one Draft to obtain existing natural CI preflight evidence before semantic publication. Source authoring and isolated checks use the available trusted tool runtime with explicitly partial materialized files; that runtime is not claimed to be a complete repository checkout. Complete exact-head validation belongs to existing repository CI or a real trusted checkout. Do not simulate successful gate artifacts or replace a missing mandatory pre-execution proof with a chat assertion. No user-local actions are authorized.",
    "completion_boundary": "No Ready/Merge or parent closure. A Draft is not landed. Preserve blocked/failed evidence. If existing surfaces cannot establish pre-execution authority, retain the Decision-only Draft and report the blocker before semantic publication."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    ".codex-skills/reverse-agent-iteration/references/project-state-round.md",
    ".codex-skills/samplereverse-frontier/SKILL.md",
    ".codex-skills/samplereverse-frontier/references/sample-guardrails.md",
    "docs/prompts/README.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/legacy-project-state-reference.md",
    "tests/test_agent_instruction_context.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    ".codex-skills/registry.json",
    ".codex-skills/schema.md",
    "tools/audit_codex_skills.py",
    "tools/sync_codex_skills.ps1",
    "tests/test_codex_skills.py",
    "tests/test_minimal_integration_baseline_docs.py",
    "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md"
  ],
  "forbidden_mutated_paths": [
    ".github/**", "reverse_agent/**", "frontend/**",
    ".codex-skills/registry.json", ".codex-skills/schema.md",
    "tools/**", "tests/test_codex_skills.py", "tests/test_minimal_integration_baseline_docs.py",
    "project_state/rounds/**", "project_state/mainline_merge_intents/**",
    "pyproject.toml", "requirements*.txt", "**/secrets/**", "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main", "force_push", "rebase", "merge", "mark_ready", "tag_or_release",
    "runner_dispatch", "model_api_invocation", "external_reverse_tool_invocation",
    "unknown_binary_execution", "destructive", "browser_execution", "workflow_dispatch"
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
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only owner/issue642-compact-instructions-r2-v1 in dddd2024/Nerelan and one Draft against main@a019b0f7ec3c807869eb076883be737c4dc3116d. Initial publication is Decision-only for natural preflight. Semantic publication requires actual pre-execution authority and stays within the eleven exact instruction/test paths. Bind the current head in the Draft body. Record progress only on this Draft and Issues884/642/296. Never Ready or Merge."
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "AGENTS.md", "minimum_risk": "R2"},
    {"pattern": ".codex-skills/**", "minimum_risk": "R2"}
  ],
  "allowed_commands": [
    {
      "command_id": "issue884.bootstrap",
      "command": "In a real trusted checkout, observe the exact base/branch and Decision-only activation; run the existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Existing repository CI may independently produce its own preflight evidence. Do not claim a partial materialization is a complete checkout or fabricate gate outputs.",
      "phase": "bootstrap", "required": false, "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"]
    },
    {
      "command_id": "issue884.implement",
      "command": "After actual pre-execution authorization, author only the eleven exact semantic paths to satisfy the frozen instruction-repair specification. Use short current routers and conditional references; preserve the existing authority and acceptance predicates. Run relevant provider-free isolated checks using installed tooling only; label partial materialization limits. No edits to existing tests, registry, workflows, dependencies, control-plane code or active product lanes.",
      "phase": "implementation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "local_static_check", "unit_test"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": ["AGENTS.md", "docs/agents/governance-reference.md", ".codex-skills/reverse-agent-iteration/SKILL.md", ".codex-skills/reverse-agent-iteration/references/project-state-round.md", ".codex-skills/samplereverse-frontier/SKILL.md", ".codex-skills/samplereverse-frontier/references/sample-guardrails.md", "docs/prompts/README.md", "docs/prompts/codex_execution_prompt.md", "docs/prompts/project_workspace_prompt.md", "docs/prompts/legacy-project-state-reference.md", "tests/test_agent_instruction_context.py"],
      "produced_artifacts": []
    },
    {
      "command_id": "issue884.validate",
      "command": "On a complete exact-head checkout run python -m pytest tests/test_agent_instruction_context.py tests/test_codex_skills.py tests/test_minimal_integration_baseline_docs.py -q; python tools/audit_codex_skills.py; python -m reverse_agent.project_gate policy-lint --state-dir project_state; git diff --check. Existing repository-owned workflows retain their unchanged setup and checks. Missing PowerShell/full-checkout evidence is not success. Do not weaken or exclude failing checks.",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue884.publish",
      "command": "Publish only owner/issue642-compact-instructions-r2-v1 in dddd2024/Nerelan and one Draft against main@a019b0f7ec3c807869eb076883be737c4dc3116d. Initial publication is Decision-only for natural preflight. Semantic publication requires actual pre-execution authority and stays within the eleven exact instruction/test paths. Bind the current head in the Draft body. Record progress only on this Draft and Issues884/642/296. Never Ready or Merge.",
      "phase": "publication", "required": true, "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue884.observe",
      "command": "Fresh-read exact remote base/head, natural State Gate/Decision Preflight/CI and their evidence. Review the complete diff against all retained authority predicates and compare actual text footprint. Do not call a self-audit independent, rerun workflows, substitute old evidence or claim merged/completed while required proof is missing.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [], "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Goal

Implement the bounded instruction correction owned by #884/#642, without changing product behavior or governance permission semantics.

## Current Evidence

Main and the instruction files were freshly read at the exact base. The official OpenAI article is https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra. The Issue records the file-specific findings; it is not execution authority.

## Do Not Do

No Ready/Merge, history rewrite, policy weakening, workflow/dependency changes, provider/browser/binary execution, other active-lane changes, user-local sync or historical evidence rewrite.

## Files To Inspect

Read only the frozen semantic paths, their named reference/test files and generated evidence needed for the current action. Do not replay the repository history.

## Required Audit

Verify the complete retained authority predicate set, valid conditional links, concise triggers, no unconditional Windows/state-stack routing, exact-head check provenance and truthful completion limits.

## Implementation Scope

The eleven exact semantic paths in the contract, only after real pre-execution authorization. No new authority/schema/Gate/runtime machinery.

## Tests

The four focused checks in issue884.validate plus applicable natural CI. No installed model/provider access. Report unavailable or failed evidence accurately.

## Stop Conditions

Stop semantic work on missing pre-execution proof, changed base, Decision mutation, out-of-scope paths/operations, failed mandatory acceptance or exhausted budget. Preserve the Decision-only candidate if the current surfaces cannot establish the required proof.
