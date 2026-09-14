# Decision Packet — instruction repair, corrected activation

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260914_issue884_compact_instructions_r2_v2",
  "round_id": "round_20260914_issue884_compact_instructions_r2_v2",
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
  "approval_basis": "The user requested an article-based instruction audit and corrections and previously delegated repository Owner authoring. This is disclosed Agent authoring, not independent human review. One fresh corrective activation is approved for the exact missing authorized_risk_paths declaration identified in failed PR885; it replaces no historical evidence and grants no Ready/Merge.",
  "supersedes_decision_id": "decision_20260914_issue884_compact_instructions_r2_v1",
  "superseded_evidence": "PR885 head ff4fc42105fe3239d95e83a3d28aacf58d4ad2d7; Decision Preflight run34813559273 job103879488607. All shown preflight predicates except path_risk_floor_enforced passed. The failed authoring omitted authorized_risk_paths for generated R2 artifacts. No semantic implementation was published. Preserve v1 unchanged; no rerun or history rewrite.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "activation_base_sha": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "starting_head": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "required_branch": "owner/issue642-compact-instructions-r2-v2",
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
    "specification": "Repair the eleven instruction/test paths defined below. Compact AGENTS into a current Nerelan entry and conditional router without weakening existing authority, risk, immutable scope, exact base/head, dirty-work, security, Draft, independent review or human-versus-Agent landing predicates. Do not implement #677. Narrow skill descriptions, place detailed project-state/sample workflows in skill-local references and retain registry names/scopes/v2 compatibility. Make execution and planning prompts short non-authoritative locators with canonical repository, Work Item, role/surface, outcome and optional stale-detection hints. Ordinary Path A uses its approved Issue snapshot, Path B uses its immutable Decision and generated preflight; no universal Windows drive, historical report stack or reverse-solving default. Preserve legacy report/sample constraints only when the active task selects them. Allow safe development iteration only within existing permissions and budget; final mandatory acceptance failure, drift, missing authority/capability or exhausted budget remains blocking. Define completion as implemented and checked on actual artifacts, otherwise report explicit limitations. Add provider-free text/routing/link/authority regression tests; do not weaken existing tests or policy lint. Measure bytes/lines only, not unmeasured model tokens, speed or quality.",
    "execution_surface_note": "GitHub-first activation and publication; real trusted tool runtime for bounded authoring/isolated static checks; existing repository CI for full exact-head checkout validation. A partial local materialization is not a full checkout. Natural CI must first produce actual pre-execution authorization on this Decision-only activation. Do not hand-author successful gate outputs. No user-local installation or worktree changes.",
    "completion_boundary": "Draft only; no Ready/Merge, no parent closure. Failed v1 remains evidence. This corrective activation has no further automatic successor budget. Missing or failed mandatory proof remains blocked."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json",
    "AGENTS.md", "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md", ".codex-skills/reverse-agent-iteration/references/project-state-round.md",
    ".codex-skills/samplereverse-frontier/SKILL.md", ".codex-skills/samplereverse-frontier/references/sample-guardrails.md",
    "docs/prompts/README.md", "docs/prompts/codex_execution_prompt.md", "docs/prompts/project_workspace_prompt.md", "docs/prompts/legacy-project-state-reference.md", "tests/test_agent_instruction_context.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json",
    "AGENTS.md", "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md", ".codex-skills/reverse-agent-iteration/references/project-state-round.md",
    ".codex-skills/samplereverse-frontier/SKILL.md", ".codex-skills/samplereverse-frontier/references/sample-guardrails.md",
    "docs/prompts/README.md", "docs/prompts/codex_execution_prompt.md", "docs/prompts/project_workspace_prompt.md", "docs/prompts/legacy-project-state-reference.md", "tests/test_agent_instruction_context.py"
  ],
  "generated_artifact_paths": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"],
  "reference_paths": [".codex-skills/registry.json", ".codex-skills/schema.md", "tools/audit_codex_skills.py", "tools/sync_codex_skills.ps1", "tests/test_codex_skills.py", "tests/test_minimal_integration_baseline_docs.py", "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md", "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md"],
  "forbidden_mutated_paths": [".github/**", "reverse_agent/**", "frontend/**", ".codex-skills/registry.json", ".codex-skills/schema.md", "tools/**", "tests/test_codex_skills.py", "tests/test_minimal_integration_baseline_docs.py", "project_state/rounds/**", "project_state/mainline_merge_intents/**", "pyproject.toml", "requirements*.txt", "**/secrets/**", "**/.env"],
  "forbidden_operations": ["direct_push_main", "force_push", "rebase", "merge", "mark_ready", "tag_or_release", "runner_dispatch", "model_api_invocation", "external_reverse_tool_invocation", "unknown_binary_execution", "destructive", "browser_execution", "workflow_dispatch"],
  "capability_policy": {
    "runner_dispatch_allowed": false, "model_api_invocation_allowed": false, "external_reverse_tool_invocation_allowed": false, "unknown_binary_execution_allowed": false, "destructive_operations_allowed": false, "bmad_installation_allowed": false, "network_access_default_allowed": false, "direct_push_to_main_allowed": false, "force_push_allowed": false, "rebase_during_execution_allowed": false, "tag_or_release_allowed": false, "merge_allowed": false, "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [], "ci_network_exceptions": [], "trusted_worker_network_exceptions": [], "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": ["Publish only owner/issue642-compact-instructions-r2-v2 in dddd2024/Nerelan and one Draft against main@a019b0f7ec3c807869eb076883be737c4dc3116d. Initial publication is Decision-only for natural preflight; semantic publication requires actual pre-execution authorization. Rebind the exact head in the Draft body. Record progress on this Draft and Issues884/642/296 and failed PR885. Never Ready or Merge."]
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}, {"pattern": "AGENTS.md", "minimum_risk": "R2"}, {"pattern": ".codex-skills/**", "minimum_risk": "R2"}],
  "allowed_commands": [
    {
      "command_id": "issue884.bootstrap", "command": "In a real trusted checkout observe the exact base, branch and immutable Decision-only activation; run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Existing repository CI may independently produce preflight evidence on its actual full checkout. Never treat partial materialization as complete or fabricate gate outputs.",
      "phase": "bootstrap", "required": false, "expected_exit_codes": [0], "execution_surface": "trusted_worker", "operations": ["code_read", "local_static_check", "command_plan_generation"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"]
    },
    {
      "command_id": "issue884.implement", "command": "After actual pre-execution authorization author only the eleven semantic paths. Preserve every existing authority/acceptance predicate and complete the frozen instruction repair. Use installed provider-free tooling for bounded isolated development checks, accurately identifying partial-materialization limits. No existing test, registry, workflow, dependency, control-plane or other active-lane mutation.",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "trusted_worker", "operations": ["source_edit", "local_static_check", "unit_test"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": ["AGENTS.md", "docs/agents/governance-reference.md", ".codex-skills/reverse-agent-iteration/SKILL.md", ".codex-skills/reverse-agent-iteration/references/project-state-round.md", ".codex-skills/samplereverse-frontier/SKILL.md", ".codex-skills/samplereverse-frontier/references/sample-guardrails.md", "docs/prompts/README.md", "docs/prompts/codex_execution_prompt.md", "docs/prompts/project_workspace_prompt.md", "docs/prompts/legacy-project-state-reference.md", "tests/test_agent_instruction_context.py"], "produced_artifacts": []
    },
    {
      "command_id": "issue884.validate", "command": "On a full exact-head checkout run python -m pytest tests/test_agent_instruction_context.py tests/test_codex_skills.py tests/test_minimal_integration_baseline_docs.py -q; python tools/audit_codex_skills.py; python -m reverse_agent.project_gate policy-lint --state-dir project_state; git diff --check. Existing repository workflows retain unchanged setup/checks. Missing full-checkout or PowerShell sync evidence is not success. No skips, exclusions, dependency updates or weakened expectations to hide failures.",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "ci_only", "operations": ["unit_test", "local_static_check", "diff_validation"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue884.publish", "command": "Publish only owner/issue642-compact-instructions-r2-v2 in dddd2024/Nerelan and one Draft against main@a019b0f7ec3c807869eb076883be737c4dc3116d. Initial publication is Decision-only for natural preflight; semantic publication requires actual pre-execution authorization. Rebind the exact head in the Draft body. Record progress on this Draft and Issues884/642/296 and failed PR885. Never Ready or Merge.",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane", "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"], "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue884.observe", "command": "Fresh-read remote base/head, natural State Gate/Decision Preflight/CI and evidence. Review the full scoped diff and retained authority predicates. Compare actual text bytes/lines only. Do not mislabel self-review as independent, substitute old proof, rerun workflows, or call a blocked Draft completed or merged.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "remote_observation", "operations": ["read_only_audit", "code_read"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Goal

Complete #884's bounded instruction repair under #642/#296; no product behavior or governance permission change.

## Current Evidence

The official source is https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra. Base main was freshly observed at the exact SHA above. PR885 preserves the failed first activation and its known missing risk-path declaration; this fresh activation fixes that declaration without rewriting it.

## Do Not Do

No Ready/Merge, force/history rewrite, workflow rerun/dispatch, policy weakening, dependency changes, provider/browser/binary execution, user-local sync, historical evidence rewrite or other active-lane mutation.

## Files To Inspect

Only task-relevant semantic paths, their referenced contracts/tests and actual generated evidence. No broad historical report replay.

## Required Audit

Retained authority predicates, concise and unambiguous triggers, valid conditional references, sample isolation, current authority routing, full-checkout check provenance and truthful completion.

## Implementation Scope

The eleven exact semantic paths, after actual pre-execution authorization. No new context framework, schema or Gate.

## Tests

The four focused validation commands and applicable natural CI. Development checks on partial files are isolated evidence only.

## Stop Conditions

Missing pre-execution proof, changed base, Decision mutation, out-of-scope changes, failed mandatory acceptance or exhausted budget remain blocking. This corrective activation has no further automatic successor budget. Keep blocked evidence; no false green.
