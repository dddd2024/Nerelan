# Explicit successor allocation for reviewed defects exact landing

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261009_issue118_reviewed_defects_exact_landing_r3_v1",
  "round_id": "round_20261009_issue118_reviewed_defects_exact_landing_r3_v1",
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
  "decision_scope": "ISSUE118_REVIEWED_DEFECTS_1106_EXPLICIT_SUCCESSOR_LANDING_ALLOCATION",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "Codex/root acting under explicit dddd2024 Owner delegation",
  "approval_basis": "\u8fd9\u4e9b\u6388\u6743\u4e5f\u662f\u4f60\u6765\u505a\uff0c\u73b0\u5728\u76ee\u6807\u662f\u957f\u671f\u65e0\u4eba\u5e72\u9884\u7684\u5e73\u53f0\uff0c\u8fd9\u6837\u4e00\u76f4\u505c\u4e5f\u662f\u95ee\u9898\u9700\u8981\u4fee\u6b63; Root explicitly appends bounded90min successor allowance for SAME1106@7a/mainDec landing goal after observer interruption and old absolute expiry. Prior setup spending1WT/1Decision/2checks/1push/1Draft and review/attestation/Ready/merge0 preserved. No old expiry extension, counter reset, source/runtime/body edits or oldPR writes. New exact Authority local+original CI+independent acceptance and actual new Ready proof mandatory.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "main",
  "base_sha": "dec321721ab9c33a0107a0b2283839654d569a88",
  "activation_base_sha": "dec321721ab9c33a0107a0b2283839654d569a88",
  "starting_head": "dec321721ab9c33a0107a0b2283839654d569a88",
  "required_branch": "codex/issue118-reviewed-defects-exact-landing-r3-20261009",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Distinct exact conditional landing Work Item for source1106@7a818bf/baseDec only. Decision-only Authority stays Draft/unmerged. Source and Authority exact local, original natural CI and independent acceptance mandatory before delegated review/Ready; actual new Ready ordinary completion, canonical attestation, whole workflow/formal success and independent Ready acceptance before one expected-head merge; verify actual new main/two parents/postmerge original CI/receipt. Preserve all old source/landing grants, failures, spending and deadlines; no source/runtime renewal, old1104/1105 writes, valid review resolution, new models/providers or deployment. This is an explicit appended successor allocation for the SAME landing goal, not unrelated work or silent expiry renewal. Old Authority1107/1105 and source1104 receive no writes; source1106 code/test/body frozen. All fresh Authority and current actual Ready acceptance remain mandatory.",
    "reuse": "Existing canonical Decision/compiler/preflight, corrected actual-Ready-ID mainline verifier/StateGate and existing canonical attestation/postmerge receipt. No new Gate/schema/receipt family or runtime.",
    "execution_surface_note": "Actual accepted project host is a bounded fixed checker and lacks this GitHub landing executor; supervised Codex alternative under recorded Owner delegation.",
    "completion_boundary": "Only sourcePR1106@7a818bfa73c2ed2d8655c3d182f1fb5f62010765 exact landing; new source63 foundation/57frozen/6fixes. Authority remains Draft/unmerged; old1104/1105 and valid reviews unchanged. Bounded coding profile, evidence integration and full unattended/backlog remain incomplete."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/command_authority.py",
    "tests/test_mainline_landing.py",
    ".github/workflows/state-gate.yml",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    ".github/**",
    ".codex-skills/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "local_browser_execution",
    "generated_governance_commit",
    "active_json_rewrite",
    "ruleset_change",
    "bypass_required_checks",
    "merge_authority_pr",
    "issue_close"
  ],
  "capability_policy": {
    "github_control_plane_network_exceptions": [
      "Publish only codex/issue118-reviewed-defects-exact-landing-r3-20261009 and one new AuthorityDraft; one new truthful delegated review, actual-currentReadyID canonical attestation, Ready and protected merge of exact1106 after all required acceptance. No oldPR writes, source/body/runtime edits, model/provider, dispatch/rerun, bypass, mainpush, release/deploy."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "AGENTS.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "docs/agents/governance-reference.md",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "landing.validation",
      "command": "python -m pytest tests/test_mainline_landing.py -q -p no:cacheprovider; git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "unit_test",
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "landing.authority_publication",
      "command": "Publish only exact codex/issue118-reviewed-defects-exact-landing-r3-20261009 and one new AuthorityDraft after PUBLICATION_READY; keep Draft/unmerged; old1107 stays untouched.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "landing.evidence",
      "command": "One truthful delegated COMMENTED exact-head review and canonical actual-currentReadyID attestation on source1106 only; not independent/human selfapproval.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "pull_request_comment"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "landing.ready",
      "command": "Only after independent source+Authority exact local/original natural CI acceptance and fresh state/principal/ruleset/no blocking threads, Ready source1106 once and bind actual new Ready ID.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "mark_ready"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "landing.merge",
      "command": "Only after actual whole Ready/formal success and independent Ready acceptance plus immediate exact state/ruleset/threads, merge source1106 once with merge method and match-head 7a818bfa73c2ed2d8655c3d182f1fb5f62010765; verify actual main/two parents/original postmerge CI/receipt.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "merge"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "approval_event_or_time": "2026-10-09T01:51:56.927002+00:00",
  "owner_delegation_sha256": "c0505f9642fecc45d4dd33fa95a0d2396a7772ff3823c5c377d82957508bdd26",
  "confirmation_mode": "DELEGATED_CONTROLLER",
  "personally_human": false,
  "development_check_run_limit": 0,
  "development_correction_round_limit": 0,
  "mandatory_check_run_limit": 2,
  "execution_expires_at": "2026-10-09T03:21:56.927002+00:00",
  "target_pr": 1106,
  "accepted_exact_head_sha": "7a818bfa73c2ed2d8655c3d182f1fb5f62010765",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge"
}
```
