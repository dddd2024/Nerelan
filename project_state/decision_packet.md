# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue206_post_coder_product_only_validation_r2_v3",
  "round_id": "round_20260816_issue206_post_coder_product_only_validation_r2_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue206_post_coder_product_only_validation_r2_v2",
  "follows_last_round_id": "round_20260816_issue206_post_coder_product_only_validation_r2_v2",
  "previous_audit_outcome": "ISSUE206_V2_OWNER_VALIDATION_PLAN_DEFECT_STALE_BASELINE_AND_UTF16_EVIDENCE",
  "workstream_id": "issue206-post-coder-product-only-validation-r2-v3",
  "source_issue": 206,
  "parent_issue": 205,
  "required_branch": "owner/issue206-post-coder-resume-validation-r2-v3",
  "starting_head": "a21e3db13c0b40221444793815e5edada510bbd3",
  "activation_base_sha": "a21e3db13c0b40221444793815e5edada510bbd3",
  "canonical_planning_sha": "a21e3db13c0b40221444793815e5edada510bbd3",
  "product_only_candidate_sha": "c5561a20360df4e3295ee4baf25705412f874ba0",
  "implementation_candidate_sha": "6565f46560ef6297e999fe354e2530f8d81eaf74",
  "observed_baseline_variance_node": "tests/platform_v1/test_credential_relay.py::TestRelayHttpIntegration::test_non_loopback_relay_only",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": true,
  "local_commit_allowed": false,
  "normal_push_allowed": false,
  "push_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "package_installation_allowed": true,
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue205-post-coder-resume-product-only-v1",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue206-post-coder-resume-validation-r2-v3",
      "python -m pip install langgraph==1.0.10 langgraph-checkpoint-sqlite==3.1.0"
    ],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "bootstrap_exception_files": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git -C F:/reverse-agent-planning-smoke status --short",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue205-post-coder-resume-product-only-v1",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue206-post-coder-resume-validation-r2-v3",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue205-post-coder-resume-product-only-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue206-post-coder-resume-validation-r2-v3",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue206-post-coder-resume-validation-r2-v3);if($b){'ISSUE206_V3_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue206-post-coder-resume-validation-r2-v3'){'ISSUE206_V3_AUTH_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue206-baseline-v3'){'ISSUE206_V3_BASELINE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue206-product-v3'){'ISSUE206_V3_PRODUCT_ALREADY_EXISTS';exit 22};if(Test-Path -LiteralPath 'F:/reverse-agent-issue206-evidence-v3'){'ISSUE206_V3_EVIDENCE_ALREADY_EXISTS';exit 21};'ISSUE206_V3_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue206-post-coder-resume-validation-r2-v3 F:/reverse-agent-issue206-post-coder-resume-validation-r2-v3 origin/owner/issue206-post-coder-resume-validation-r2-v3",
    "Set-Location F:/reverse-agent-issue206-post-coder-resume-validation-r2-v3",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD a21e3db13c0b40221444793815e5edada510bbd3",
    "git show HEAD:project_state/decision_packet.md",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue206v3.dependencies_install",
      "command": "python -m pip install langgraph==1.0.10 langgraph-checkpoint-sqlite==3.1.0",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["package_installation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.dependencies_identity",
      "command": "python -c \"import importlib.metadata as m; assert m.version('langgraph')=='1.0.10'; assert m.version('langgraph-checkpoint-sqlite')=='3.1.0'; print('ISSUE206_V3_DEPENDENCIES_OK')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.evidence_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue206-evidence-v3' -ErrorAction Stop | Out-Null; Write-Output 'ISSUE206_V3_EVIDENCE_ROOT_CREATED'\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_evidence_directory_creation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.baseline_create",
      "command": "git worktree add --detach F:/reverse-agent-issue206-baseline-v3 a21e3db13c0b40221444793815e5edada510bbd3",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_creation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.baseline_identity",
      "command": "python -c \"import subprocess;root=r'F:/reverse-agent-issue206-baseline-v3';h=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert h=='a21e3db13c0b40221444793815e5edada510bbd3',h;s=subprocess.check_output(['git','-C',root,'status','--porcelain'],text=True);assert not s,s;print('ISSUE206_V3_BASELINE_IDENTITY_OK')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.product_create",
      "command": "git worktree add --detach F:/reverse-agent-issue206-product-v3 c5561a20360df4e3295ee4baf25705412f874ba0",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_creation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.product_identity_scope",
      "command": "python -c \"import subprocess;root=r'F:/reverse-agent-issue206-product-v3';h=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert h=='c5561a20360df4e3295ee4baf25705412f874ba0',h;s=subprocess.check_output(['git','-C',root,'status','--porcelain'],text=True);assert not s,s;paths=sorted(p for p in subprocess.check_output(['git','-C',root,'diff','--name-only','a21e3db13c0b40221444793815e5edada510bbd3','HEAD'],text=True).splitlines() if p.strip());exp=sorted(['reverse_agent/platform_v1/durable_execution.py','tests/platform_v1/test_durable_execution.py']);assert paths==exp,(paths,exp);print('ISSUE206_V3_PRODUCT_SCOPE_OK')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.flaky_surface_unchanged",
      "command": "git -C F:/reverse-agent-issue206-product-v3 diff --quiet a21e3db13c0b40221444793815e5edada510bbd3 HEAD -- tests/platform_v1/test_credential_relay.py reverse_agent/model_access",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.validation_driver",
      "command": "python F:/reverse-agent-issue206-evidence-v3/validation_driver.py",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "external_evidence_write"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.worktrees_clean",
      "command": "python -c \"import subprocess;roots=[r'F:/reverse-agent-issue206-baseline-v3',r'F:/reverse-agent-issue206-product-v3'];dirty={r:subprocess.check_output(['git','-C',r,'status','--porcelain'],text=True) for r in roots};assert all(not v for v in dirty.values()),dirty;print('ISSUE206_V3_WORKTREES_CLEAN')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.product_diff_check",
      "command": "git -C F:/reverse-agent-issue206-product-v3 diff --check a21e3db13c0b40221444793815e5edada510bbd3 HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue206v3.final_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    }
  ],
  "external_validation_driver_contract": {
    "path": "F:/reverse-agent-issue206-evidence-v3/validation_driver.py",
    "creation_surface": "local_agent_file_write_outside_repository",
    "repository_mutation": false,
    "baseline_root": "F:/reverse-agent-issue206-baseline-v3",
    "product_root": "F:/reverse-agent-issue206-product-v3",
    "evidence_root": "F:/reverse-agent-issue206-evidence-v3",
    "evidence_encoding": "utf-8",
    "full_suite_command": ["python", "-m", "pytest", "tests/platform_v1", "-q"],
    "full_run_count_per_side": 3,
    "full_run_allowed_exit_codes": [0, 1],
    "failed_node_regex": "^FAILED\\s+([^\\s]+)",
    "error_node_regex": "^ERROR\\s+([^\\s]+)",
    "allowed_full_run_failure_nodes": [
      "tests/platform_v1/test_credential_relay.py::TestRelayHttpIntegration::test_non_loopback_relay_only"
    ],
    "full_run_requirements": [
      "Every baseline and product run has zero ERROR nodes.",
      "Every FAILED node across all six full runs is a member of allowed_full_run_failure_nodes.",
      "Any merge-intent, contract, durable, task-service, trusted-host, or other failure is unexpected and fails validation.",
      "Do not require the allowed relay timeout to occur the same number of times on baseline and product."
    ],
    "nonvariance_suite": {
      "deselect_only": "tests/platform_v1/test_credential_relay.py::TestRelayHttpIntegration::test_non_loopback_relay_only",
      "baseline_required_exit_code": 0,
      "product_required_exit_code": 0,
      "no_other_deselects": true
    },
    "relay_probe": {
      "node": "tests/platform_v1/test_credential_relay.py::TestRelayHttpIntegration::test_non_loopback_relay_only",
      "runs_per_side": 3,
      "purpose": "record timing variance only",
      "allowed_exit_codes": [0, 1],
      "error_nodes_must_be_empty": true,
      "pass_count_equality_not_required": true
    },
    "focused_product_suite": [
      "tests/platform_v1/test_durable_execution.py",
      "tests/platform_v1/test_task_service.py",
      "tests/platform_v1/test_trusted_host.py"
    ],
    "focused_product_required_exit_code": 0,
    "output_files": [
      "baseline_full_1.txt", "baseline_full_2.txt", "baseline_full_3.txt",
      "product_full_1.txt", "product_full_2.txt", "product_full_3.txt",
      "baseline_relay_probe.json", "product_relay_probe.json", "summary.json"
    ],
    "stdout_success_terminal": "ISSUE206_V3_VALIDATION_ACCEPTED",
    "success_exit_code": 0,
    "failure_rule": "On any unexpected failed node, ERROR node, nonvariance exit != 0, focused exit != 0, or evidence/encoding error, write summary.json if possible and exit nonzero without repository mutation."
  },
  "allowed_mutated_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/platform_v1/durable_execution.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_credential_relay.py",
    "reverse_agent/model_access/**",
    "tests/platform_v1/**",
    "project_state/decision_packet.md",
    "project_state/mainline_merge_intents/active.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md", "README.md", "pyproject.toml", "requirements*.txt", "poetry.lock", "uv.lock",
    ".github/**", "frontend/**", "docs/**", "reverse_agent/**", "tests/**",
    "project_state/decision_packet.md", "project_state/mainline_merge_intents/**",
    "project_state/current_state.json", "project_state/state_manifest.json",
    "project_state/artifact_index.json", "project_state/schemas/**",
    "project_state/rounds/**", "project_state/audits/**"
  ],
  "forbidden_operations": [
    "product_mutation", "test_mutation", "governance_artifact_mutation", "commit", "push",
    "pr_creation", "merge", "direct_push_main", "auto_merge", "force_push", "rebase",
    "amend", "squash", "tag_or_release", "release", "deployment", "credential_access",
    "credential_publication", "model_api_invocation", "opencode_invocation", "codex_invocation",
    "openhands_invocation", "runner_dispatch", "external_provider_invocation"
  ],
  "success_terminal": "ISSUE206_POST_CODER_PRODUCT_ONLY_EQUIVALENCE_PROVEN",
  "failure_terminal": "ISSUE206_POST_CODER_PRODUCT_ONLY_EQUIVALENCE_NOT_PROVEN"
}
```
