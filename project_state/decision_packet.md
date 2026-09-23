# Approved bounded supervised system-authored answer evidence

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_issue988_system_answer_evidence_r3_v1",
  "round_id": "round_20260923_issue988_system_answer_evidence_r3_v1",
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
  "repository": "dddd2024/Nerelan",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "provider_free_acceptance_required": true,
  "decision_scope": "SUPERVISED_SYSTEM_AUTHORED_ANSWER_EVIDENCE",
  "source_issue": 988,
  "parent_issue": 260,
  "approved_by": "dddd2024 via explicit delegated Owner execution",
  "approval_basis": "User explicitly delegates Owner completion and independent audits; latest instruction assigns implementation to Nerelan and observation/acceptance to supervisor. Independently reviewed exact candidate 44376a3ba13834989a7c9f3e2748267a89325b706a60f2a024e687323a2208d2. This fresh bounded round permits accepted-runtime synchronization, one supervised DeepSeek task on its activation commit, exact2path system-authored artifact transfer, provider-free and rendered replay checks, and Draft-only publication. GPT allowance zero; no automatic retry or landing. Host/child evidence and runtime-only paths follow this immutable contract.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "main",
  "base_sha": "58d4068f43ca4914b122445685cae410a8fa156e",
  "activation_base_sha": "58d4068f43ca4914b122445685cae410a8fa156e",
  "starting_head": "58d4068f43ca4914b122445685cae410a8fa156e",
  "fresh_base": "58d4068f43ca4914b122445685cae410a8fa156e",
  "current_main_expected": "58d4068f43ca4914b122445685cae410a8fa156e",
  "required_branch": "codex/system-answer-evidence-r3-v1-20260923",
  "workstream_id": "issue988-system-answer-evidence-r3-v1",
  "follows_last_decision_id": "decision_20260923_issue982_gpt_oauth_network_r3_v1",
  "follows_last_round_id": "round_20260923_issue982_gpt_oauth_network_r3_v1",
  "workflow_profile": "browser_r3",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 3,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": true,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": true,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_opencode_text_evidence.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/src/schemas/model-access.ts",
    "frontend/tests/model-settings.test.tsx",
    "reverse_agent/model_access/account_auth.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/test_model_access.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_opencode_text_evidence.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/src/schemas/model-access.ts",
    "frontend/tests/model-settings.test.tsx",
    "reverse_agent/model_access/account_auth.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/test_model_access.py"
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
    ".github/**",
    ".codex-skills/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/e2e/snapshots/**",
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
    "mark_ready",
    "merge",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "snapshot_generation_or_threshold_change",
    "fix_forward_after_mandatory_failure"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "frontend/e2e/snapshots/**",
      "minimum_risk": "R3"
    }
  ],
  "semantic_implementation_contract": {
    "specification": "Nerelan authors safe assistant evidence normalization/redaction/extraction and bounded event selection. Preserve typed text and legacy field precedence; normalize explicitly handled controls before secret matching and truncation, preserve newline/tab/Unicode. Preserve final assistant text beyond first40 events within existing limits. Test raw JSONL->events->callback->durable fenced store->SQLite reopen->real task/run HTTP projection, malformed records, secret boundaries/keys, task/epoch isolation and nonzero/timeout truth. No source implementation by supervisor in this round; return defects to a subsequent bounded system task if this attempt cannot complete.",
    "completion_boundary": "Exact system provenance, allowed-path diff, provider-free tests, new-evidence HTTP/rendered replay and independent exact-head source acceptance. Draft-only, no landing. Does not complete GPT login, native Codex, discovery/pairing, Chinese polish or real-time streaming."
  },
  "runtime_scratch_policy": {
    "paths": [
      "frontend/node_modules/**",
      "frontend/dist/**",
      "**/__pycache__/**",
      ".pytest_cache/**",
      ".platform_v1_runtime/**"
    ],
    "stage_allowed": false,
    "note": "Existing user runtime stays in its named host; task children under named external root; independent replay scratch under F:/Nerelan-final-audit-evidence-20260911/issue988-replay. Preserve all existing files, no broad cleanup or secret inspection."
  },
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": true,
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
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "Only unchanged natural workflows execute on ci_only. Require applicable exact-head CI, Decision Preflight and State Gate SUCCESS with actual full diagnostic exit0/native0failures/errors; independently verify workflow trigger applicability for other suites. No rerun/dispatch/golden/dependency mutation. Existing CI-only setup unchanged."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "After host preflight, verify no running tasks/login flows via supported loopback APIs. Verify clean named runtime branch/head and exact package-lock equality, verify owned PID/executable/start-time/workspace; stop only those services with existing Windows PowerShell scripts. Fast-forward only local runtime branch from approved old head to 58d4068f43ca4914b122445685cae410a8fa156e using already available local object. Restart hidden NoBrowser with existing Model Control enablement, external task root, SourceDir F:/Nerelan-issue988-system-answer-evidence, and explicit trusted authority/planning identity equal to host activation commit. Verify all3 services/process source provenance and unchanged public connection/binding summaries. Never read keys/auth files, change settings, install, launch OAuth or call models in this step. The only source synchronization command is git -C F:/Nerelan-first-use-20260923 merge --ff-only 58d4068f43ca4914b122445685cae410a8fa156e, after clean branch/head and ancestor checks; require resulting HEAD and tree equal that accepted commit and no new commit. Exact9 runtime-only paths in runtime_only_path_boundary, never implementation edits. Merge prohibitions elsewhere still apply.",
      "After exact host evidence verification create one direct Task via127.0.0.1:8766/api/tasks using coding-default, opencode, single, immutable activation commit as branch, complete bounded instruction plus host plan/preflight evidence as title. Verify saved identity and request digest/256KiB bound before one execute call. Existing trusted credential lease only for saved DeepSeek connection; supervisor never retrieves key values. Existing executor owns external detached worktree and300-second timeout. System alone writes the2 approved paths and may run specified local development checks, no commits/publication/governance/outside reads. No duplicate launch, auto-retry, GPT or fallback.",
      "Observe same actual task/run through supported loopback APIs to terminal; timeouts in observation do not justify relaunch. Record prepared HEAD, exact model/session/usage, status/errors and full changed-file set. Inspect child complete diff/untracked files and unchanged host evidence. Reject all out-of-scope/sensitive/generated changes; preserve failed evidence. Transfer only system-authored allowed-path patch into F:/Nerelan-issue988-system-answer-evidence after independent diff review; record before/after hashes and task provenance. Supervisor may apply that reviewed patch and run checks but cannot author product fixes. No automatic success from READY_FOR_REVIEW or empty diff. During actual system execution, permit one installed headless Playwright browser session observing the existing task page on4173, with timestamped run-state screenshots and comparison to actual Task API. No interactive browser launch or approval bypass. Capture startup/running/terminal truth; do not promise token streaming. Keep this actual execution observation separate from the later synthetic new-answer replay.",
      "Run provider-free development checks before one frozen product commit: python -m pytest tests/platform_v1/test_opencode_text_evidence.py -q; python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py -q; python -m pytest tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_provider_free_task_plane.py -q; git diff --check. Only synthetic/local fixtures, no provider/model calls. At most8 development check rounds, no supervisor product edits. Freeze one product commit then run those exact mandatory checks once, base-to-head diff, sequential startup/plan/lint/preflight/readiness. Mandatory failure stops dependent publication.",
      "Run isolated provider-free new-evidence replay using existing parser/fenced store/TaskService handler and Vite on free loopback8788/4188, external scratch issue988-replay only, no writes to user DB/settings. Reuse installed dependencies after exact package/lock equality; no install. At most2 installed headless Playwright browser launches for rendered task/evidence page screenshots. Do not bypass any browser approval rejection. Label synthetic replay; confirm new answer travels parser->durable store->HTTP->renderedpage. This proves replay display, not live provider, OAuth or realtime streaming. Stop only owned replay services after capture; preserve evidence."
    ],
    "github_control_plane_network_exceptions": [
      "After all mandatory checks/readiness and independent result audit, reobserve locked main/ownership. Publish only identical local Decision plus system-product blob/tree/commit graph through canonical GitHub Git API to codex/system-answer-evidence-r3-v1-20260923, verify allSHAs, create one exact-head Draft against main. No local git push, remote semantic edits, Ready, merge, issue closure, dispatch/rerun or other refs. Assert complete base-to-head graph changes only Decision plus the2 implementation paths; runtime-only synchronization paths must not enter this product delta."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue988v1.bootstrap",
      "command": "After fresh independent remote main/base/ownership observation, create F:/Nerelan-issue988-system-answer-evidence on codex/system-answer-evidence-r3-v1-20260923 from 58d4068f43ca4914b122445685cae410a8fa156e. Commit only approved Decision once, generate startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and publication readiness. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY. Never modify activated Decision; no product edits.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "command_plan_generation",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue988v1.runtime",
      "command": "After host preflight, verify no running tasks/login flows via supported loopback APIs. Verify clean named runtime branch/head and exact package-lock equality, verify owned PID/executable/start-time/workspace; stop only those services with existing Windows PowerShell scripts. Fast-forward only local runtime branch from approved old head to 58d4068f43ca4914b122445685cae410a8fa156e using already available local object. Restart hidden NoBrowser with existing Model Control enablement, external task root, SourceDir F:/Nerelan-issue988-system-answer-evidence, and explicit trusted authority/planning identity equal to host activation commit. Verify all3 services/process source provenance and unchanged public connection/binding summaries. Never read keys/auth files, change settings, install, launch OAuth or call models in this step. The only source synchronization command is git -C F:/Nerelan-first-use-20260923 merge --ff-only 58d4068f43ca4914b122445685cae410a8fa156e, after clean branch/head and ancestor checks; require resulting HEAD and tree equal that accepted commit and no new commit. Exact9 runtime-only paths in runtime_only_path_boundary, never implementation edits. Merge prohibitions elsewhere still apply.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "machine_specific_execution",
        "network_access",
        "source_edit"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/src/components/connection-binding-editor.tsx",
        "frontend/src/routes/settings.tsx",
        "frontend/src/schemas/model-access.ts",
        "frontend/tests/model-settings.test.tsx",
        "project_state/decision_packet.md",
        "reverse_agent/model_access/account_auth.py",
        "reverse_agent/platform_v1/opencode_executor.py",
        "tests/platform_v1/test_opencode_executor.py",
        "tests/test_model_access.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue988v1.dispatch",
      "command": "After exact host evidence verification create one direct Task via127.0.0.1:8766/api/tasks using coding-default, opencode, single, immutable activation commit as branch, complete bounded instruction plus host plan/preflight evidence as title. Verify saved identity and request digest/256KiB bound before one execute call. Existing trusted credential lease only for saved DeepSeek connection; supervisor never retrieves key values. Existing executor owns external detached worktree and300-second timeout. System alone writes the2 approved paths and may run specified local development checks, no commits/publication/governance/outside reads. No duplicate launch, auto-retry, GPT or fallback.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "model_api_invocation",
        "integration_test",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "tests/platform_v1/test_opencode_text_evidence.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue988v1.supervise",
      "command": "Observe same actual task/run through supported loopback APIs to terminal; timeouts in observation do not justify relaunch. Record prepared HEAD, exact model/session/usage, status/errors and full changed-file set. Inspect child complete diff/untracked files and unchanged host evidence. Reject all out-of-scope/sensitive/generated changes; preserve failed evidence. Transfer only system-authored allowed-path patch into F:/Nerelan-issue988-system-answer-evidence after independent diff review; record before/after hashes and task provenance. Supervisor may apply that reviewed patch and run checks but cannot author product fixes. No automatic success from READY_FOR_REVIEW or empty diff. During actual system execution, permit one installed headless Playwright browser session observing the existing task page on4173, with timestamped run-state screenshots and comparison to actual Task API. No interactive browser launch or approval bypass. Capture startup/running/terminal truth; do not promise token streaming. Keep this actual execution observation separate from the later synthetic new-answer replay.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "local_static_check",
        "diff_validation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "tests/platform_v1/test_opencode_text_evidence.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue988v1.validate",
      "command": "Run provider-free development checks before one frozen product commit: python -m pytest tests/platform_v1/test_opencode_text_evidence.py -q; python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py -q; python -m pytest tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_provider_free_task_plane.py -q; git diff --check. Only synthetic/local fixtures, no provider/model calls. At most8 development check rounds, no supervisor product edits. Freeze one product commit then run those exact mandatory checks once, base-to-head diff, sequential startup/plan/lint/preflight/readiness. Mandatory failure stops dependent publication.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "diff_validation",
        "commit",
        "command_plan_generation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "tests/platform_v1/test_opencode_text_evidence.py"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue988v1.render",
      "command": "Run isolated provider-free new-evidence replay using existing parser/fenced store/TaskService handler and Vite on free loopback8788/4188, external scratch issue988-replay only, no writes to user DB/settings. Reuse installed dependencies after exact package/lock equality; no install. At most2 installed headless Playwright browser launches for rendered task/evidence page screenshots. Do not bypass any browser approval rejection. Label synthetic replay; confirm new answer travels parser->durable store->HTTP->renderedpage. This proves replay display, not live provider, OAuth or realtime streaming. Stop only owned replay services after capture; preserve evidence.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "integration_test",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue988v1.publish",
      "command": "After all mandatory checks/readiness and independent result audit, reobserve locked main/ownership. Publish only identical local Decision plus system-product blob/tree/commit graph through canonical GitHub Git API to codex/system-answer-evidence-r3-v1-20260923, verify allSHAs, create one exact-head Draft against main. No local git push, remote semantic edits, Ready, merge, issue closure, dispatch/rerun or other refs. Assert complete base-to-head graph changes only Decision plus the2 implementation paths; runtime-only synchronization paths must not enter this product delta.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue988v1.natural_checks",
      "command": "Only unchanged natural workflows execute on ci_only. Require applicable exact-head CI, Decision Preflight and State Gate SUCCESS with actual full diagnostic exit0/native0failures/errors; independently verify workflow trigger applicability for other suites. No rerun/dispatch/golden/dependency mutation. Existing CI-only setup unchanged.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue988v1.audit",
      "command": "Read canonical current main/base/head, Issue988, frozen concurrent heads, immutable Decision and real natural artifacts. Independent exact-head audit must distinguish actual Nerelan-authored patch/task provenance, source/provider-free tests and labelled new-evidence rendered replay. Keep Draft and preserve all other work. Do not claim live OAuth/GPT, nativeCodex, model discovery/pairing or overall completion.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "read_only_audit",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "concurrent_work_preservation": {
    "981": "849af4ae2039bb7d30ebb442404a567e5c7152f2",
    "979": "73128ceac2d3efcab53e8e2964033da53143af2b",
    "978": "d4a227e63347972f3f3bfd3cea27fa7abb0f3222",
    "987": "2d5c2b1a5dd54320a1bfb3866eb2c513ad53a7c9",
    "policy": "Preserve all. PR981 remains frozen historical failed candidate; no import/cherry-pick/amend/closure. New system implementation starts on accepted current main. Shared file edits only evidence helpers; preserve merged983 OAuth/proxy code. Never touch owner979 task_service or tests."
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "frontend/src/components/evidence-panel.tsx",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "runtime_only_path_boundary": {
    "paths": [
      "frontend/src/components/connection-binding-editor.tsx",
      "frontend/src/routes/settings.tsx",
      "frontend/src/schemas/model-access.ts",
      "frontend/tests/model-settings.test.tsx",
      "project_state/decision_packet.md",
      "reverse_agent/model_access/account_auth.py",
      "reverse_agent/platform_v1/opencode_executor.py",
      "tests/platform_v1/test_opencode_executor.py",
      "tests/test_model_access.py"
    ],
    "checkout": "F:/Nerelan-first-use-20260923",
    "restriction": "These extra paths permit only exact accepted-tree synchronization old3b9->58d in this runtime checkout. No edits to their contents, no copying them into the implementation product delta. Implementation commands remain exactly2paths; final product graph must contain Decision plus only these2 implementation paths. Local git merge --ff-only 58d is expressly allowed solely to advance this clean named runtime branch without creating a merge commit; it is not GitHub landing and does not enable merge_allowed."
  },
  "system_task_attempt_limit": 1,
  "system_execution_timeout_seconds": 300,
  "gpt_model_invocation_limit": 0,
  "model_budget_semantics": "One supervised OpenCode task attempt, 300-second existing process timeout, no retries, no fallback. This is not a one-provider-request or hard token/cost cap: agent may use several requests within one task. Observe usage; unknown cost remains unknown. Only saved coding-default / deepseek-flash is allowed. No GPT/Codex/Agnes invocation in this round.",
  "runtime_update_scope": {
    "repo_dir": "F:/Nerelan-first-use-20260923",
    "branch": "codex/first-use-20260923",
    "old_head": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
    "new_head": "58d4068f43ca4914b122445685cae410a8fa156e",
    "source_dir": "F:/Nerelan-issue988-system-answer-evidence",
    "workspace_root": "F:/Nerelan-first-use-task-workspaces-20260923",
    "policy": "Only clean exact local fast-forward and identity-verified owned service restart. Preserve user configuration/task history and credential owner. No reset/clean/stash/install/raw credential reads. Windows PowerShell, hidden launch, NoBrowser. No OAuth operation."
  },
  "host_child_authority_handoff": "Host named branch holds immutable Decision and generates actual command_plan/preflight. Child execution is expressly permitted as detached worktree derived from exact activation commit. Supervisor embeds complete relevant generated plan/preflight bytes with path/digest/host head/branch and Decision digest in task title, verifies request <=256KiB and saves request digest. Old child tracked gates are not current authorization. System verifies child HEAD/Decision and cannot read outside child or regenerate governance. This is approved host evidence transfer, not a new Gate/receipt or claim of child-local preflight. Host gate bytes must remain unchanged through dispatch and collection."
}
```
