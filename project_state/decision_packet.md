# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_pr146_agent_canvas_landing_provenance_fix_v19",
  "round_id": "round_20260809_pr146_agent_canvas_landing_provenance_fix_v19",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_issue136_agent_canvas_draft_pr_landing_v18",
  "follows_last_round_id": "round_20260809_issue136_agent_canvas_draft_pr_landing_v18",
  "previous_audit_outcome": "PR146_AUDIT_FOUND_STALE_PR134_INTENT_AND_PROVENANCE_DOC_DRIFT",
  "workstream_id": "pr146-agent-canvas-landing-provenance-fix-v19",
  "source_issue": 136,
  "parent_issue": 127,
  "active_pr": 146,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_head": "7731fb15a2a0a7c617e4720a665f571a33e5d51e",
  "activation_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
  "accepted_stage_b_evidence_head": "ab00b03952d96c2421be8297f29699a59ec69fda",
  "allowed_merge_method": "merge",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": true,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": false,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
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
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "preexisting_provider_session_use_allowed": false,
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "audit_findings": {
    "pr146_pre_v19_head": "7731fb15a2a0a7c617e4720a665f571a33e5d51e",
    "pr146_draft": true,
    "pr146_mergeable": true,
    "review_threads": 0,
    "decision_preflight_run": 31293014404,
    "decision_preflight_conclusion": "success",
    "state_gate_pull_request_run": 31293014442,
    "state_gate_pull_request_conclusion": "success",
    "model_access_run": 31293014414,
    "model_access_conclusion": "success",
    "ci_run": 31293014417,
    "ci_conclusion": "failure",
    "ci_failure_classification": "STALE_MAINLINE_INTENT_ONLY",
    "ci_failure_tests": [
      "tests/test_mainline_landing.py::test_committed_active_intent_binds_exact_current_authority",
      "tests/test_mainline_landing.py::test_production_pre_merge_simulation"
    ],
    "ci_pre_failure_green": "1706 passed, 1 skipped; 282 passed; 11 passed",
    "stale_intent_source_pr": 134,
    "provenance_doc_drift": [
      "frontend/THIRD_PARTY_NOTICES.md still described the current frontend as fixture-driven/offline and all runtime/backend dependencies as deterministic fixtures",
      "frontend/OPENHANDS_REUSE_MAP.md retained unlabeled fixture-only PR119 architecture statements that can be misread as current runtime truth",
      "Agent Canvas v1.6.1 copyright line omitted the upstream LICENSE year 2025"
    ],
    "nonblocking_ui_debt_issue": 145
  },
  "provenance_fix_contract": {
    "allowed_files": [
      "frontend/THIRD_PARTY_NOTICES.md",
      "frontend/OPENHANDS_REUSE_MAP.md"
    ],
    "third_party_notice_requirements": [
      "Agent Canvas copyright must match upstream v1.6.1 LICENSE: Copyright © 2025 OpenHands contributors",
      "remove current-product fixture-driven/offline claim",
      "remove claim that all OpenHands runtime/backend dependencies are deterministic fixtures",
      "state that reverse-agent Task API/TaskStore/executor/validation/evidence/model-control remain reverse-agent-owned"
    ],
    "reuse_map_requirements": [
      "mark the old OpenHands structural source-to-target table as a historical PR119 snapshot",
      "mark old fixture-only exclusions as historical PR119 snapshot",
      "make explicit that current runtime uses reverse-agent Task API/OpenCode and the fixture-only wording is historical evidence"
    ],
    "product_source_change_allowed": false,
    "screenshot_change_allowed": false
  },
  "mainline_intent_contract": {
    "archive_source": "project_state/mainline_merge_intents/active.json",
    "expected_old_intent_id": "pr134_frontend_opencode_devup_landing_v1",
    "expected_old_source_pr": 134,
    "archive_path": "project_state/mainline_merge_intents/archive/pr134_v1.json",
    "archive_must_be_byte_identical": true,
    "new_intent_id": "pr146_agent_canvas_landing_v1",
    "new_source_pr": 146,
    "locked_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
    "allowed_merge_method": "merge",
    "merge_tree_policy": "equal_to_accepted_head_tree",
    "required_workflows": [
      "CI",
      "Decision Preflight",
      "State Gate (pull_request)",
      "State Gate (push)"
    ],
    "expires_at": "2026-08-16T23:59:59Z",
    "decision_and_command_plan_hashes_must_be_observed_from_committed_files": true
  },
  "owner_landing_contract": {
    "pr": 146,
    "base_branch": "main",
    "expected_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
    "head_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
    "draft_until_final_audit": true,
    "owner_only_ready_and_merge": true,
    "expected_head_protection_required": true,
    "merge_method": "merge",
    "before_ready_and_merge_require": [
      "CI exact-head success",
      "Decision Preflight exact-head success",
      "State Gate pull_request exact-head success",
      "State Gate push exact-head success",
      "Model Access exact-head success",
      "no unresolved review threads",
      "PR mergeable",
      "PR base remains dd4cb074ab5b9baacf300706878b29bd745f12c3",
      "PR head remains the audited v19 implementation head"
    ],
    "auto_merge_forbidden": true
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git fetch origin main",
    "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
    "git show origin/owner/issue136-agent-canvas-reuse-spike-v2:project_state/decision_packet.md",
    "git switch owner/issue136-agent-canvas-reuse-spike-v2",
    "git merge --ff-only origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "git rev-parse HEAD",
    "git rev-parse origin/main",
    "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "validation.accepted_evidence_ancestor",
      "command": "git merge-base --is-ancestor ab00b03952d96c2421be8297f29699a59ec69fda HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "exact_head_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "validation.old_intent_identity",
      "command": "python -c \"import json; from pathlib import Path; x=json.loads(Path('project_state/mainline_merge_intents/active.json').read_text(encoding='utf-8')); assert x['intent_id']=='pr134_frontend_opencode_devup_landing_v1'; assert x['source_pr']==134; print('OLD_INTENT_PR134_VALID')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.archive_pr134_intent",
      "command": "python -c \"from pathlib import Path; s=Path('project_state/mainline_merge_intents/active.json'); d=Path('project_state/mainline_merge_intents/archive/pr134_v1.json'); assert s.exists(); assert not d.exists(); d.write_bytes(s.read_bytes()); print('PR134_INTENT_ARCHIVED')\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["governance_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/mainline_merge_intents/archive/pr134_v1.json"]
    },
    {
      "command_id": "validation.archive_identity",
      "command": "python -c \"from pathlib import Path; import hashlib; a=hashlib.sha256(Path('project_state/mainline_merge_intents/active.json').read_bytes()).hexdigest(); b=hashlib.sha256(Path('project_state/mainline_merge_intents/archive/pr134_v1.json').read_bytes()).hexdigest(); assert a==b; print('PR134_ARCHIVE_IDENTICAL SHA256='+a)\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.third_party_notice_fix",
      "command": "python -c \"from pathlib import Path; p=Path('frontend/THIRD_PARTY_NOTICES.md'); s=p.read_text(encoding='utf-8'); a='**Copyright:** Copyright © OpenHands contributors'; b='**Copyright:** Copyright © 2025 OpenHands contributors'; c='for a fixture-driven, offline prototype.'; d=\\\"while the current product uses reverse-agent's real Task API and executor paths.\\\"; e='All OpenHands runtime/backend dependencies are stubbed or replaced with deterministic fixtures.'; f=\\\"Agent Canvas/OpenHands presentation reuse does not supply reverse-agent's Task API, TaskStore, executor, validation/evidence, model-control, or credential handling.\\\"; assert s.count(a)==1 and s.count(c)==1 and s.count(e)==1; s=s.replace(a,b).replace(c,d).replace(e,f); p.write_text(s,encoding='utf-8'); print('THIRD_PARTY_NOTICE_CORRECTED')\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["governance_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["frontend/THIRD_PARTY_NOTICES.md"]
    },
    {
      "command_id": "mutation.reuse_map_historical_labels",
      "command": "python -c \"from pathlib import Path; p=Path('frontend/OPENHANDS_REUSE_MAP.md'); s=p.read_text(encoding='utf-8'); a='## Source-to-target reuse map (exact upstream paths)'; b='## Historical OpenHands 1.8.0 structural map (PR #119 snapshot)\\n\\nThe table below records the pre-PR #134 fixture-only baseline. Its fixture-only wording is retained as historical evidence and does not describe the current runtime, which uses reverse-agent Task API and OpenCode paths.'; c='## Not reused (concrete incompatibilities)'; d='## Historical PR #119 exclusions (snapshot)\\n\\nThese exclusions describe the historical structural-adaptation baseline, not current reverse-agent runtime. Current Task API/OpenCode data flow is not a fixture-only browser path.'; assert s.count(a)==1 and s.count(c)==1; s=s.replace(a,b).replace(c,d); p.write_text(s,encoding='utf-8'); print('REUSE_MAP_HISTORICAL_LABELS_CORRECTED')\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["governance_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["frontend/OPENHANDS_REUSE_MAP.md"]
    },
    {
      "command_id": "validation.provenance_docs",
      "command": "python -c \"from pathlib import Path; a=Path('frontend/THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8'); b=Path('frontend/OPENHANDS_REUSE_MAP.md').read_text(encoding='utf-8'); assert 'Copyright © 2025 OpenHands contributors' in a; assert 'fixture-driven, offline prototype' not in a; assert 'All OpenHands runtime/backend dependencies are stubbed or replaced with deterministic fixtures.' not in a; assert 'Historical OpenHands 1.8.0 structural map (PR #119 snapshot)' in b; assert 'Historical PR #119 exclusions (snapshot)' in b; print('PROVENANCE_DOCS_VALID')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.write_pr146_intent",
      "command": "python -c \"from pathlib import Path; import hashlib,json; decision=hashlib.sha256(Path('project_state/decision_packet.md').read_bytes()).hexdigest(); plan=hashlib.sha256(Path('project_state/gates/command_plan.json').read_bytes()).hexdigest(); x={'schema_version':1,'intent_id':'pr146_agent_canvas_landing_v1','repository':'dddd2024/reverse-agent','source_pr':146,'locked_base_sha':'dd4cb074ab5b9baacf300706878b29bd745f12c3','allowed_merge_method':'merge','decision_identity':{'decision_id':'decision_20260809_pr146_agent_canvas_landing_provenance_fix_v19','decision_content_sha256':decision},'command_plan_sha256':plan,'merge_tree_policy':'equal_to_accepted_head_tree','required_workflows':['CI','Decision Preflight','State Gate (pull_request)','State Gate (push)'],'expires_at':'2026-08-16T23:59:59Z'}; Path('project_state/mainline_merge_intents/active.json').write_text(json.dumps(x,indent=2)+'\\n',encoding='utf-8'); print('PR146_INTENT_WRITTEN DECISION_SHA256='+decision+' COMMAND_PLAN_SHA256='+plan)\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["governance_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/mainline_merge_intents/active.json"]
    },
    {
      "command_id": "validation.pr146_intent",
      "command": "python -c \"from pathlib import Path; import hashlib,json; x=json.loads(Path('project_state/mainline_merge_intents/active.json').read_text(encoding='utf-8')); assert x['intent_id']=='pr146_agent_canvas_landing_v1' and x['source_pr']==146 and x['locked_base_sha']=='dd4cb074ab5b9baacf300706878b29bd745f12c3'; assert x['decision_identity']['decision_id']=='decision_20260809_pr146_agent_canvas_landing_provenance_fix_v19'; assert x['decision_identity']['decision_content_sha256']==hashlib.sha256(Path('project_state/decision_packet.md').read_bytes()).hexdigest(); assert x['command_plan_sha256']==hashlib.sha256(Path('project_state/gates/command_plan.json').read_bytes()).hexdigest(); print('PR146_INTENT_VALID')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.docs_contracts",
      "command": "python -m pytest tests/test_minimal_integration_baseline_docs.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.mainline_landing",
      "command": "python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.platform_v1",
      "command": "python -m pytest tests/platform_v1 -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.gate_regression",
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.diff_check",
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
      "command_id": "publication.stage",
      "command": "git add -- frontend/OPENHANDS_REUSE_MAP.md frontend/THIRD_PARTY_NOTICES.md project_state/mainline_merge_intents/active.json project_state/mainline_merge_intents/archive/pr134_v1.json project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_stage"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/OPENHANDS_REUSE_MAP.md",
        "frontend/THIRD_PARTY_NOTICES.md",
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr134_v1.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "publication.cached_check",
      "command": "git diff --cached --check",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.staged_paths",
      "command": "git diff --cached --name-only",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.commit",
      "command": "git commit -m \"landing: bind PR146 and correct frontend provenance\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.commit_paths",
      "command": "git diff-tree --no-commit-id --name-only -r HEAD",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.push",
      "command": "git push origin owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.local_head",
      "command": "git rev-parse HEAD",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.remote_head",
      "command": "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.final_status",
      "command": "git status --short",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "frontend/OPENHANDS_REUSE_MAP.md",
    "frontend/THIRD_PARTY_NOTICES.md",
    "frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-task-detail-1440x900.png",
    "frontend/src/components/app-shell.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/index.css",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-workbench-frame.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/resize-handle.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/sidebar-collapsed-icon-slot.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/sidebar-layout.ts",
    "frontend/tests/workspace.test.tsx",
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr134_v1.json"
  ],
  "carry_forward_cumulative_paths": [
    "frontend/OPENHANDS_REUSE_MAP.md",
    "frontend/THIRD_PARTY_NOTICES.md",
    "frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-task-detail-1440x900.png",
    "frontend/src/components/app-shell.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/index.css",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-workbench-frame.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/resize-handle.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/sidebar-collapsed-icon-slot.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/sidebar-layout.ts",
    "frontend/tests/workspace.test.tsx",
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    "project_state/schemas/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/package.json",
    "frontend/package-lock.json",
    ".frontend_stage/**",
    ".platform_v1_runtime/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
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
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "task_create",
    "task_execute",
    "browser_capture",
    "runtime_service_start"
  ],
  "capability_policy": {
    "mode": "deny_by_default",
    "default_decision": "deny",
    "allowed_operations": [
      "repository_observation",
      "exact_head_validation",
      "run_checks",
      "governance_artifact_mutation",
      "diff_validation",
      "repository_stage",
      "repository_commit",
      "repository_push",
      "network_access"
    ],
    "forbidden_operations": [
      "direct_push_main",
      "auto_merge",
      "force_push",
      "rebase",
      "amend",
      "squash",
      "release",
      "deployment",
      "credential_access",
      "model_api_invocation",
      "opencode_invocation",
      "codex_invocation",
      "openhands_invocation",
      "task_create",
      "task_execute",
      "browser_capture",
      "runtime_service_start"
    ],
    "network_policy": "deny_unless_command_explicitly_marks_network_access"
  },
  "external_prerequisites": [],
  "generated_at": "2026-08-09T03:50:00Z",
  "created_by": "chatgpt-owner"
}
```

## Owner audit and execution policy

PR #146 Stage B product/runtime evidence remains accepted. The exact-head CI failure on `7731fb15...` is not a frontend regression: CI completed the broad repository suite (`1706 passed, 1 skipped`), supervisor/repository hygiene (`282 passed`), and Codex skill sync (`11 passed`), then failed only the two mainline-landing tests because `project_state/mainline_merge_intents/active.json` still binds the already-landed PR #134 authority.

A separate Owner audit found provenance documentation drift that must be corrected before merge. The Agent Canvas v1.6.1 upstream LICENSE states `Copyright © 2025 OpenHands contributors`; the current notice omitted `2025`. The historical OpenHands structural mapping also retained fixture-only language without sufficiently marking those rows/exclusions as a PR #119-era snapshot, while current reverse-agent has a real Task API/OpenCode path.

After synchronizing to this v19 Decision and obtaining `PRE_EXECUTION_AUTHORIZED`, the local Agent may execute only the compiler-generated commands above. It must archive the current PR #134 intent byte-for-byte before replacing it, correct only the two provenance documents, bind `active.json` to PR #146 using hashes observed from the committed v19 Decision and generated command plan, run the required validation, stage only the nine authorized files, commit once, and normal-push the existing branch.

No frontend source, frontend tests, screenshots, backend, workflow, dependency, model/executor configuration, Task API, TaskStore, OpenCode task, credential, browser, runtime service, or main branch mutation is authorized locally.

The local Agent must not mark PR #146 Ready and must not merge. Those actions remain Owner-only and are allowed by this Decision only after the resulting exact head has all required CI/Decision Preflight/State Gate push+PR/Model Access checks successful, no unresolved review threads, the PR remains mergeable, and base/head identities remain exact. Owner merge must use merge-commit method with expected-head protection.

Terminal after local publication:

`PR146_V19_LANDING_PREP_PUBLISHED_AWAITING_EXACT_HEAD_CHECKS`
