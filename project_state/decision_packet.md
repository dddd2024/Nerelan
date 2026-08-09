# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_pr146_agent_canvas_committed_head_landing_v27",
  "round_id": "round_20260809_pr146_agent_canvas_committed_head_landing_v27",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_pr146_stale_local_candidate_reconcile_v26",
  "follows_last_round_id": "round_20260809_pr146_stale_local_candidate_reconcile_v26",
  "previous_audit_outcome": "V26_STALE_LOCAL_CANDIDATE_RECONCILED_PHASE4_EXPECTED_GATE_ARTIFACT_DIRT_FOUND",
  "source_issue": 136,
  "parent_issue": 127,
  "active_pr": 146,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_remote_head": "9e6d98399c1a9ddac45d4b0d898726b23abcc3c2",
  "activation_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
  "accepted_stage_b_evidence_head": "ab00b03952d96c2421be8297f29699a59ec69fda",
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "preexisting_gate_carryover_contract": {
    "source_decision_id": "decision_20260809_pr146_stale_local_candidate_reconcile_v26",
    "reason": "v26 transition generation intentionally rewrote tracked gate artifacts before its read-only clean assertion",
    "tracked_paths": [
      "project_state/gates/bootstrap_state.json",
      "project_state/gates/command_plan.json",
      "project_state/gates/startup_snapshot.json",
      "project_state/gates/transition_command_plan_preview.json",
      "project_state/gates/transition_preflight_result.json"
    ],
    "must_be_exact_dirty_set_before_restore": true,
    "cleanup_command": "git restore --worktree -- project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json",
    "cleanup_only_before_v27_transition_generation": true
  },
  "preexisting_carryover_contract": {
    "kernel_followup_issue": 147,
    "paths": [".frontend_stage/**", ".platform_v1_runtime/**"],
    "decision_scope_only": true,
    "normal_command_mutation_grant": false,
    "must_not_be_staged": true,
    "must_not_be_cleaned_or_stashed": true,
    "must_not_be_deleted": true
  },
  "mainline_intent_contract": {
    "expected_old_intent_id": "pr134_frontend_opencode_devup_landing_v1",
    "expected_old_source_pr": 134,
    "archive_path": "project_state/mainline_merge_intents/archive/pr134_v1.json",
    "new_intent_id": "pr146_agent_canvas_landing_v1",
    "new_source_pr": 146,
    "locked_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
    "allowed_merge_method": "merge",
    "merge_tree_policy": "equal_to_accepted_head_tree",
    "required_workflows": ["CI", "Decision Preflight", "State Gate (pull_request)", "State Gate (push)"],
    "expires_at": "2026-08-16T23:59:59Z"
  },
  "committed_head_validation_contract": {
    "candidate_commit_required_before_tests": true,
    "candidate_commit_must_remain_local_until_all_tests_pass": true,
    "candidate_commit_paths": [
      "project_state/mainline_merge_intents/active.json",
      "project_state/mainline_merge_intents/archive/pr134_v1.json",
      "project_state/gates/bootstrap_state.json",
      "project_state/gates/command_plan.json",
      "project_state/gates/startup_snapshot.json",
      "project_state/gates/transition_command_plan_preview.json",
      "project_state/gates/transition_preflight_result.json"
    ],
    "push_forbidden_until_tests_pass": true,
    "tracked_post_test_diff_must_be_zero": true
  },
  "owner_landing_contract": {
    "pr": 146,
    "base_branch": "main",
    "expected_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
    "head_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
    "draft_until_final_audit": true,
    "owner_only_ready_and_merge": true,
    "merge_method": "merge",
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
    "git switch owner/issue136-agent-canvas-reuse-spike-v2",
    "git merge --ff-only origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "git rev-parse HEAD",
    "git rev-parse origin/main",
    "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "git diff --name-only",
    "git diff --cached --name-only",
    "git restore --worktree -- project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json",
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
      "command_id": "mutation.ensure_pr134_archive",
      "command": "python -c \"from pathlib import Path; s=Path('project_state/mainline_merge_intents/active.json'); d=Path('project_state/mainline_merge_intents/archive/pr134_v1.json'); data=s.read_bytes(); d.parent.mkdir(parents=True,exist_ok=True); assert not d.exists(); d.write_bytes(data); assert d.read_bytes()==data; print('PR134_ARCHIVE_READY')\"",
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
      "command_id": "validation.provenance_docs",
      "command": "python -c \"from pathlib import Path; import re; a=Path('frontend/THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8'); b=Path('frontend/OPENHANDS_REUSE_MAP.md').read_text(encoding='utf-8'); assert a.count('**Copyright:** Copyright © 2025 OpenHands contributors')==2; assert re.search(r'fixture-driven,\\s+offline prototype',a) is None; assert re.search(r'All OpenHands runtime/backend dependencies are stubbed or\\s+replaced with deterministic fixtures\\.',a) is None; assert 'reverse-agent Task API, TaskStore, executor, validation/evidence, model-control, and credential handling' in a; assert '## Historical OpenHands 1.8.0 structural map (PR #119 snapshot)' in b; assert '## Historical PR #119 exclusions (snapshot)' in b; assert 'current runtime uses the reverse-agent Task API and OpenCode paths' in b; print('PROVENANCE_DOCS_VALID')\"",
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
      "command": "python -c \"from pathlib import Path; import hashlib,json; decision=hashlib.sha256(Path('project_state/decision_packet.md').read_bytes()).hexdigest(); plan=hashlib.sha256(Path('project_state/gates/command_plan.json').read_bytes()).hexdigest(); x={'schema_version':1,'intent_id':'pr146_agent_canvas_landing_v1','repository':'dddd2024/reverse-agent','source_pr':146,'locked_base_sha':'dd4cb074ab5b9baacf300706878b29bd745f12c3','allowed_merge_method':'merge','decision_identity':{'decision_id':'decision_20260809_pr146_agent_canvas_committed_head_landing_v27','decision_content_sha256':decision},'command_plan_sha256':plan,'merge_tree_policy':'equal_to_accepted_head_tree','required_workflows':['CI','Decision Preflight','State Gate (pull_request)','State Gate (push)'],'expires_at':'2026-08-16T23:59:59Z'}; Path('project_state/mainline_merge_intents/active.json').write_text(json.dumps(x,indent=2)+'\\n',encoding='utf-8',newline='\\n'); print('PR146_INTENT_WRITTEN DECISION_SHA256='+decision+' PLAN_SHA256='+plan)\"",
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
      "command_id": "validation.pr146_intent_worktree",
      "command": "python -c \"from pathlib import Path; import hashlib,json; x=json.loads(Path('project_state/mainline_merge_intents/active.json').read_text(encoding='utf-8')); assert x['intent_id']=='pr146_agent_canvas_landing_v1' and x['source_pr']==146 and x['locked_base_sha']=='dd4cb074ab5b9baacf300706878b29bd745f12c3'; assert x['decision_identity']['decision_id']=='decision_20260809_pr146_agent_canvas_committed_head_landing_v27'; assert x['decision_identity']['decision_content_sha256']==hashlib.sha256(Path('project_state/decision_packet.md').read_bytes()).hexdigest(); assert x['command_plan_sha256']==hashlib.sha256(Path('project_state/gates/command_plan.json').read_bytes()).hexdigest(); print('PR146_INTENT_WORKTREE_VALID')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.diff_check_precommit",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "candidate.stage",
      "command": "git add -- project_state/mainline_merge_intents/active.json project_state/mainline_merge_intents/archive/pr134_v1.json project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json",
      "phase": "candidate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_stage"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
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
      "command_id": "candidate.cached_check",
      "command": "git diff --cached --check",
      "phase": "candidate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "candidate.staged_paths",
      "command": "git diff --cached --name-only",
      "phase": "candidate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "candidate.commit",
      "command": "git commit -m \"landing: bind PR146 v27 intent\"",
      "phase": "candidate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "candidate.commit_paths",
      "command": "git diff-tree --no-commit-id --name-only -r HEAD",
      "phase": "candidate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "test.mainline_landing_committed_head",
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
      "command_id": "test.platform_v1_committed_head",
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
      "command_id": "test.gate_regression_committed_head",
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
      "command_id": "validation.post_test_tracked_clean",
      "command": "git diff --exit-code",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
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
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr134_v1.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".frontend_stage/**",
    ".platform_v1_runtime/**"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/src/**",
    "frontend/tests/**",
    "frontend/artifacts/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/THIRD_PARTY_NOTICES.md",
    "frontend/OPENHANDS_REUSE_MAP.md",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/src/**",
    "frontend/tests/**",
    "frontend/artifacts/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/THIRD_PARTY_NOTICES.md",
    "frontend/OPENHANDS_REUSE_MAP.md",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/schemas/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "cherry_pick",
    "stash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": true,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "git fetch origin main",
      "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
      "git push origin owner/issue136-agent-canvas-reuse-spike-v2"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": ".github/**", "minimum_risk": "R3"},
    {"pattern": "reverse_agent/**", "minimum_risk": "R2"},
    {"pattern": "tests/**", "minimum_risk": "R2"}
  ],
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr134_v1.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "runner_managed_artifact_paths": [
    "project_state/gates/evidence/**",
    "project_state/gates/execution_log.json"
  ]
}
```

## Owner audit and execution policy

v27 supersedes v26 after v26 achieved its primary objective: the unpublished stale v24 candidate was proven exactly and discarded by the single authorized reset, leaving the local checkout aligned to the v26 remote authority. v26 then regenerated five tracked gate artifacts and correctly stopped when its final read-only tracked-clean assertion observed those expected generated deltas. That Phase 4 failure was a Decision sequencing defect, not a product or Agent execution defect.

v27 explicitly closes that gap. Before v27 transition generation, the local Agent must fetch and fast-forward to the exact v27 remote authority, prove that the only tracked dirty paths are the five v26-generated gate artifacts and that the index is clean, while preserving the two known untracked carryover directories. It may then execute exactly one cleanup command restoring only those five generated gate artifacts to committed HEAD. No reset, clean, stash, rebase, amend, cherry-pick, force operation, or carryover-directory mutation is authorized.

After that bounded cleanup, generate v27 transition artifacts and require transition lint PASS plus `PRE_EXECUTION_AUTHORIZED` with no blocking reasons. The generated v27 gate artifacts are expected candidate content and are therefore not required to leave the working tree clean before staging.

The landing sequence then validates accepted Stage B ancestry, validates and archives the committed PR134 active intent byte-for-byte, read-validates the already-correct provenance documents, writes the PR146 active intent bound to the immutable v27 Decision and generated v27 command-plan digests, stages exactly seven governance paths, and creates one local unpublished commit `landing: bind PR146 v27 intent`.

All required landing, platform, and gate-regression tests run against that committed candidate HEAD. Any failure leaves the candidate local and forbids publication. Only when all committed-head tests pass and tracked post-test diff is zero may the Agent normal-push the branch. Ready and merge remain Owner-only after a fresh exact-head remote audit.
