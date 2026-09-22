# Approved #891 postmerge State Gate applicability successor

```json decision_meta
{
    "schema_version":  1,
    "decision_id":  "decision_20260922_issue891_postmerge_applicability_r2_v3",
    "round_id":  "round_20260922_issue891_postmerge_applicability_r2_v3",
    "status":  "APPROVED",
    "mainline":  "engineering_branch",
    "skill_profiles":  [
                           "reverse-agent-iteration@v2"
                       ]
}
```

```json decision_contract
{
    "transition_kernel_required":  true,
    "decision_scope":  "POSTMERGE_STATE_GATE_APPLICABILITY_R2_V3",
    "source_issue":  891,
    "parent_issue":  156,
    "repository":  "dddd2024/Nerelan",
    "approved_by":  "dddd2024 via explicitly delegated repository Owner execution",
    "approval_basis":  "User explicitly delegated Owner execution. Fresh Issue #891 scope audit comment 5773910906 fixes postmerge evidence applicability/coherence as the first governance implementation priority after #968 landing. V1 stopped before semantic commit/publication because its immutable selector matched zero tests (comment 5774880763). V2 then proved 44 focused + 194/3 full landing tests but correctly failed five project-gate false_none integration fixtures because the v2 allowlist did not permit updating tests/test_project_gate.py to carry trusted workflow/applicability evidence (comment 5774969237). V3 retains the same production classifier semantics and expands only the test allowlist to that existing integration fixture owner; project_gate.py and state-gate.yml remain reference-only.",
    "risk_tier":  "R2",
    "authorized_risk_tier":  "R2",
    "governance_artifact_risk_tier":  "R2",
    "integration_base_ref":  "main",
    "base_sha":  "3b9eb3806ca59e119d2f8db36537b7efe593c729",
    "activation_base_sha":  "3b9eb3806ca59e119d2f8db36537b7efe593c729",
    "starting_head":  "3b9eb3806ca59e119d2f8db36537b7efe593c729",
    "fresh_base":  "3b9eb3806ca59e119d2f8db36537b7efe593c729",
    "current_main_expected":  "3b9eb3806ca59e119d2f8db36537b7efe593c729",
    "required_branch":  "owner/issue891-postmerge-applicability-r2-v3-20260922",
    "workstream_id":  "issue891-postmerge-applicability-r2-v3",
    "fresh_worktree_creation_required":  true,
    "history_reuse_allowed":  false,
    "decision_commit_must_precede_implementation":  true,
    "decision_commit_must_precede_execution":  true,
    "decision_content_immutable_after_activation":  true,
    "decision_immutability_required":  true,
    "decision_immutability_check_required_in":  [
                                                    "transition_preflight",
                                                    "transition_reconcile",
                                                    "worktree_publication_readiness"
                                                ],
    "decision_activation_commit_limit":  1,
    "product_change_commit_limit":  1,
    "generated_governance_commit_limit":  0,
    "normal_push_attempt_limit":  0,
    "draft_pr_creation_limit":  1,
    "mark_ready_attempt_limit":  0,
    "merge_attempt_limit":  0,
    "workflow_rerun_limit":  0,
    "runner_dispatch_limit":  0,
    "live_model_call_limit":  0,
    "provider_network_call_limit":  0,
    "credential_access_limit":  0,
    "pr_creation_allowed":  true,
    "issue_comment_allowed":  true,
    "pull_request_comment_allowed":  true,
    "merge_allowed":  false,
    "mark_ready_allowed":  false,
    "workflow_rerun_allowed":  false,
    "runner_dispatch_allowed":  false,
    "direct_push_to_main_allowed":  false,
    "auto_merge_allowed":  false,
    "force_push_allowed":  false,
    "rebase_during_execution_allowed":  false,
    "dependency_install_allowed":  false,
    "live_provider_access_allowed":  false,
    "credential_access_allowed":  false,
    "local_browser_execution_allowed":  false,
    "provider_free_acceptance_required":  true,
    "mainline_merge_intent_required":  false,
    "active_pr_binding_mode":  "none",
    "workflow_profile":  "baseline",
    "semantic_implementation_contract":  {
                                             "specification":  "Add one conservative repository-owned State Gate push applicability classifier to the existing false/none landing validator. Derive APPLICABLE / EXPECTED_NOT_APPLICABLE / UNKNOWN only from the trusted locked-base .github/workflows/state-gate.yml bytes plus the exact base-to-accepted-head path set. Current supported workflow grammar is intentionally narrow: push on main, optional positive paths list, exact literal paths and terminal /** directory-prefix patterns. Any workflow mutation by the target, unsupported/negative glob syntax, paths-ignore, malformed/duplicate blocks, incomplete path evidence, Git diff failure, or unknown trigger semantics yields UNKNOWN and blocks before merge. Future false/none landing-authority Decisions must bind the machine-derived classification, workflow SHA-256 and changed-path-set digest; no PR/sidecar prose can self-declare N/A. Reuse the same derivation postmerge so the pre/post contract is coherent.",
                                             "build_vs_reuse":  "REUSE existing false/none attestation/authority validation, current mainline landing path, system Git, hashlib/json and the current State Gate path contract. SELF-DEVELOP only the thin conservative classifier and binding checks. No YAML/pathspec dependency, no new workflow/client/database/receipt/gate family.",
                                             "completion_boundary":  "One immutable Decision commit, one semantic commit touching exactly reverse_agent/mainline_landing.py, tests/test_mainline_landing.py, and tests/test_project_gate.py, one Draft PR, natural exact-head CI/Decision Preflight/State Gate and independent exact-head audit. No Ready/Merge."
                                         },
    "bootstrap_exception_files":  [
                                      "project_state/decision_packet.md"
                                  ],
    "bootstrap_exception_commands":  [

                                     ],
    "allowed_mutated_paths":  [
                                  "project_state/decision_packet.md",
                                  "project_state/gates/command_plan.json",
                                  "project_state/gates/startup_snapshot.json",
                                  "project_state/gates/bootstrap_state.json",
                                  "project_state/gates/transition_command_plan_preview.json",
                                  "project_state/gates/transition_preflight_result.json",
                                  "reverse_agent/mainline_landing.py",
                                  "tests/test_mainline_landing.py",
                                  "tests/test_project_gate.py"
                              ],
    "authorized_risk_paths":  [
                                  "project_state/decision_packet.md",
                                  "project_state/gates/command_plan.json",
                                  "project_state/gates/startup_snapshot.json",
                                  "project_state/gates/bootstrap_state.json",
                                  "project_state/gates/transition_command_plan_preview.json",
                                  "project_state/gates/transition_preflight_result.json",
                                  "reverse_agent/mainline_landing.py",
                                  "tests/test_mainline_landing.py",
                                  "tests/test_project_gate.py"
                              ],
    "generated_artifact_paths":  [
                                     "project_state/gates/command_plan.json",
                                     "project_state/gates/startup_snapshot.json",
                                     "project_state/gates/bootstrap_state.json",
                                     "project_state/gates/transition_command_plan_preview.json",
                                     "project_state/gates/transition_preflight_result.json"
                                 ],
    "reference_paths":  [
                            ".github/workflows/state-gate.yml",
                            "reverse_agent/project_gate.py",
                            "reverse_agent/github_remote_verifier.py",
                            "tests/test_ci_responsibility.py",
                            "AGENTS.md"
                        ],
    "forbidden_mutated_paths":  [
                                    ".github/**",
                                    "reverse_agent/project_gate.py",
                                    "reverse_agent/github_remote_verifier.py",
                                    "reverse_agent/control_plane/**",
                                    "frontend/**",
                                    "docs/**",
                                    "pyproject.toml",
                                    "requirements*.txt",
                                    "project_state/rounds/**",
                                    "project_state/mainline_merge_intents/**",
                                    "**/secrets/**",
                                    "**/.env"
                                ],
    "forbidden_operations":  [
                                 "active_json_rewrite",
                                 "amend",
                                 "auto_merge",
                                 "browser_execution",
                                 "destructive",
                                 "direct_push_main",
                                 "external_reverse_tool_invocation",
                                 "force_push",
                                 "generated_governance_commit",
                                 "history_rewrite",
                                 "mark_ready",
                                 "merge",
                                 "model_api_invocation",
                                 "provider_network_call",
                                 "rebase",
                                 "runner_dispatch",
                                 "squash",
                                 "tag_or_release",
                                 "unknown_binary_execution",
                                 "workflow_dispatch",
                                 "workflow_rerun"
                             ],
    "capability_policy":  {
                              "runner_dispatch_allowed":  false,
                              "model_api_invocation_allowed":  false,
                              "external_reverse_tool_invocation_allowed":  false,
                              "unknown_binary_execution_allowed":  false,
                              "destructive_operations_allowed":  false,
                              "bmad_installation_allowed":  false,
                              "network_access_default_allowed":  false,
                              "direct_push_to_main_allowed":  false,
                              "merge_allowed":  false,
                              "force_push_allowed":  false,
                              "rebase_during_execution_allowed":  false,
                              "tag_or_release_allowed":  false,
                              "remote_observation_read_only_allowed":  true,
                              "local_network_exceptions":  [

                                                           ],
                              "ci_network_exceptions":  [

                                                        ],
                              "trusted_worker_network_exceptions":  [

                                                                    ],
                              "user_local_network_exceptions":  [

                                                                ],
                              "github_control_plane_network_exceptions":  [
                                                                              "Create only the exact Decision/semantic commit graph and branch owner/issue891-postmerge-applicability-r2-v3-20260922 in dddd2024/Nerelan, then one Draft PR against locked main; comment only on Issue #891/#156 and that Draft. Never Ready/Merge."
                                                                          ]
                          },
    "path_risk_floor":  [
                            {
                                "pattern":  "project_state/**",
                                "minimum_risk":  "R2"
                            },
                            {
                                "pattern":  "reverse_agent/mainline_landing.py",
                                "minimum_risk":  "R2"
                            }
                        ],
    "allowed_commands":  [
                             {
                                 "command_id":  "issue891appv3.bootstrap",
                                 "command":  "On the fresh isolated exact-main worktree commit this immutable Decision once. Run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre, focused transition/Decision tests, git diff --check and worktree-publication-readiness. Generated gate files are ephemeral and must not be committed. Require PRE_EXECUTION_AUTHORIZED before semantic mutation.",
                                 "phase":  "bootstrap",
                                 "required":  true,
                                 "expected_exit_codes":  [
                                                             0
                                                         ],
                                 "execution_surface":  "user_local",
                                 "operations":  [
                                                    "code_read",
                                                    "local_static_check",
                                                    "command_plan_generation",
                                                    "commit",
                                                    "machine_specific_execution"
                                                ],
                                 "network_access":  false,
                                 "required_evidence_source":  "repository_state_attestation",
                                 "allowed_mutated_paths":  [
                                                               "project_state/decision_packet.md"
                                                           ],
                                 "produced_artifacts":  [
                                                            "project_state/gates/command_plan.json",
                                                            "project_state/gates/startup_snapshot.json",
                                                            "project_state/gates/bootstrap_state.json",
                                                            "project_state/gates/transition_command_plan_preview.json",
                                                            "project_state/gates/transition_preflight_result.json"
                                                        ]
                             },
                             {
                                 "command_id":  "issue891appv3.implement",
                                 "command":  "After PRE_EXECUTION_AUTHORIZED edit only reverse_agent/mainline_landing.py, tests/test_mainline_landing.py, and tests/test_project_gate.py. Add a conservative State Gate push applicability classifier and bind future false/none authority Decisions to machine-derived applicability + trusted workflow digest + exact changed-path digest. Reuse the same derivation premerge/postmerge. Update only the existing project-gate fake evidence fixtures so they materialize the trusted workflow and sidecar applicability binding. UNKNOWN always blocks. Commit exactly one semantic commit.",
                                 "phase":  "implementation",
                                 "required":  true,
                                 "expected_exit_codes":  [
                                                             0
                                                         ],
                                 "execution_surface":  "user_local",
                                 "operations":  [
                                                    "source_edit",
                                                    "unit_test",
                                                    "local_static_check",
                                                    "commit",
                                                    "machine_specific_execution"
                                                ],
                                 "network_access":  false,
                                 "required_evidence_source":  "repository_state_attestation",
                                 "allowed_mutated_paths":  [
                                                               "reverse_agent/mainline_landing.py",
                                                               "tests/test_mainline_landing.py",
                                                               "tests/test_project_gate.py"
                                                           ],
                                 "produced_artifacts":  [

                                                        ]
                             },
                             {
                                 "command_id":  "issue891appv3.validate",
                                 "command":  "Run python -B -m pytest tests/test_mainline_landing.py -k \u0027false_none or applicability\u0027 -q -p no:cacheprovider; python -B -m pytest tests/test_mainline_landing.py -q -p no:cacheprovider; python -B -m pytest tests/test_project_gate.py -k false_none -q -p no:cacheprovider; python -m compileall -q reverse_agent/mainline_landing.py; git diff --check. Prove #966-style frontend-only paths EXPECTED_NOT_APPLICABLE, #968-style decision/control path APPLICABLE, and UNKNOWN for workflow drift, unsupported trigger syntax and incomplete path evidence.",
                                 "phase":  "validation",
                                 "required":  true,
                                 "expected_exit_codes":  [
                                                             0
                                                         ],
                                 "execution_surface":  "user_local",
                                 "operations":  [
                                                    "unit_test",
                                                    "local_static_check",
                                                    "diff_validation",
                                                    "machine_specific_execution"
                                                ],
                                 "network_access":  false,
                                 "required_evidence_source":  "repository_state_attestation",
                                 "allowed_mutated_paths":  [

                                                           ],
                                 "produced_artifacts":  [

                                                        ]
                             },
                             {
                                 "command_id":  "issue891appv3.publish",
                                 "command":  "Through github_control_plane only, publish the exact locally authored Decision and semantic Git objects to owner/issue891-postmerge-applicability-r2-v3-20260922 and create one Draft PR against locked main. Verify exact tree/commit identities. No local git push, Ready or Merge.",
                                 "phase":  "publication",
                                 "required":  true,
                                 "expected_exit_codes":  [
                                                             0
                                                         ],
                                 "execution_surface":  "github_control_plane",
                                 "operations":  [
                                                    "push",
                                                    "draft_pr",
                                                    "pull_request_comment",
                                                    "issue_comment",
                                                    "network_access"
                                                ],
                                 "network_access":  true,
                                 "required_evidence_source":  "repository_state_attestation",
                                 "allowed_mutated_paths":  [

                                                           ],
                                 "produced_artifacts":  [

                                                        ]
                             },
                             {
                                 "command_id":  "issue891appv3.observe",
                                 "command":  "Fresh-read remote exact commit trees/ref/PR and natural exact-head CI/Decision Preflight/State Gate. Independently audit classifier fail-closed semantics, source scope and #966/#968 controls. Keep Draft; no Ready/Merge.",
                                 "phase":  "final_evidence",
                                 "required":  true,
                                 "expected_exit_codes":  [
                                                             0
                                                         ],
                                 "execution_surface":  "remote_observation",
                                 "operations":  [
                                                    "read_only_audit",
                                                    "code_read",
                                                    "repository_observation"
                                                ],
                                 "network_access":  false,
                                 "required_evidence_source":  "repository_state_attestation",
                                 "allowed_mutated_paths":  [

                                                           ],
                                 "produced_artifacts":  [

                                                        ]
                             }
                         ],
    "issue_completion_close_allowed":  [

                                       ]
}
```
