# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_pr146_agent_canvas_owner_provenance_landing_v22",
  "round_id": "round_20260809_pr146_agent_canvas_owner_provenance_landing_v22",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_pr146_agent_canvas_carryover_safe_landing_v21",
  "follows_last_round_id": "round_20260809_pr146_agent_canvas_carryover_safe_landing_v21",
  "previous_audit_outcome": "V21_PREFLIGHT_AUTHORIZED_THIRD_PARTY_MUTATION_FAILED_ON_MARKDOWN_LINE_WRAP",
  "source_issue": 136,
  "parent_issue": 127,
  "active_pr": 146,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_head": "cb4cb80432fda2aba932451c25c524a4095cdeb1",
  "activation_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
  "accepted_stage_b_evidence_head": "ab00b03952d96c2421be8297f29699a59ec69fda",
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "owner_preapplied_provenance_contract": {
    "owner_github_write_allowed": true,
    "paths": [
      "frontend/THIRD_PARTY_NOTICES.md",
      "frontend/OPENHANDS_REUSE_MAP.md"
    ],
    "decision_must_precede_writes": true,
    "local_agent_mutation_allowed": false,
    "local_validation_required": true
  },
  "preexisting_carryover_contract": {
    "kernel_followup_issue": 147,
    "paths": [".frontend_stage/**", ".platform_v1_runtime/**"],
    "decision_scope_only": true,
    "normal_command_mutation_grant": false,
    "must_not_be_staged": true,
    "must_not_be_cleaned_or_stashed": true
  },
  "mainline_intent_contract": {
    "expected_old_intent_id": "pr134_frontend_opencode_devup_landing_v1",
    "expected_old_source_pr": 134,
    "archive_path": "project_state/mainline_merge_intents/archive/pr134_v1.json",
    "archive_may_preexist_locally_from_v21": true,
    "new_intent_id": "pr146_agent_canvas_landing_v1",
    "new_source_pr": 146,
    "locked_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
    "allowed_merge_method": "merge",
    "merge_tree_policy": "equal_to_accepted_head_tree",
    "required_workflows": ["CI", "Decision Preflight", "State Gate (pull_request)", "State Gate (push)"],
    "expires_at": "2026-08-16T23:59:59Z"
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
      "command_id": "mutation.ensure_pr134_archive",
      "command": "python -c \"from pathlib import Path; s=Path('project_state/mainline_merge_intents/active.json'); d=Path('project_state/mainline_merge_intents/archive/pr134_v1.json'); data=s.read_bytes(); d.parent.mkdir(parents=True,exist_ok=True); d.write_bytes(data) if not d.exists() else None; assert d.read_bytes()==data; print('PR134_ARCHIVE_READY')\"",
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
      "command": "python -c \"from pathlib import Path; import hashlib,json; decision=hashlib.sha256(Path('project_state/decision_packet.md').read_bytes()).hexdigest(); plan=hashlib.sha256(Path('project_state/gates/command_plan.json').read_bytes()).hexdigest(); x={'schema_version':1,'intent_id':'pr146_agent_canvas_landing_v1','repository':'dddd2024/reverse-agent','source_pr':146,'locked_base_sha':'dd4cb074ab5b9baacf300706878b29bd745f12c3','allowed_merge_method':'merge','decision_identity':{'decision_id':'decision_20260809_pr146_agent_canvas_owner_provenance_landing_v22','decision_content_sha256':decision},'command_plan_sha256':plan,'merge_tree_policy':'equal_to_accepted_head_tree','required_workflows':['CI','Decision Preflight','State Gate (pull_request)','State Gate (push)'],'expires_at':'2026-08-16T23:59:59Z'}; Path('project_state/mainline_merge_intents/active.json').write_text(json.dumps(x,indent=2)+'\\n',encoding='utf-8',newline='\\n'); print('PR146_INTENT_WRITTEN DECISION_SHA256='+decision+' PLAN_SHA256='+plan)\"",
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
      "command": "python -c \"from pathlib import Path; import hashlib,json; x=json.loads(Path('project_state/mainline_merge_intents/active.json').read_text(encoding='utf-8')); assert x['intent_id']=='pr146_agent_canvas_landing_v1' and x['source_pr']==146 and x['locked_base_sha']=='dd4cb074ab5b9baacf300706878b29bd745f12c3'; assert x['decision_identity']['decision_id']=='decision_20260809_pr146_agent_canvas_owner_provenance_landing_v22'; assert x['decision_identity']['decision_content_sha256']==hashlib.sha256(Path('project_state/decision_packet.md').read_bytes()).hexdigest(); assert x['command_plan_sha256']==hashlib.sha256(Path('project_state/gates/command_plan.json').read_bytes()).hexdigest(); print('PR146_INTENT_VALID')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
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
      "command_id": "publication.stage",
      "command": "git add -- project_state/mainline_merge_intents/active.json project_state/mainline_merge_intents/archive/pr134_v1.json project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json",
      "phase": "publication",
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
      "command": "git commit -m \"landing: bind PR146 v22 intent\"",
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
    "unknown_binary_execution",
    "destructive"
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
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": ["git push origin owner/issue136-agent-canvas-reuse-spike-v2"],
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

v21 proved the carryover-safe preflight workaround: startup snapshot, command-plan, lint and preflight all passed. The local archive was created and verified byte-identical, but `mutation.third_party_notice_fix` failed before write because the stale disclaimer sentence is physically wrapped between `or` and `replaced`, while v21 required a single-line exact string. The v21 validation had the same latent single-line assumption.

v22 removes all local provenance-document mutation. After this Decision commit, the Owner will correct only `frontend/THIRD_PARTY_NOTICES.md` and `frontend/OPENHANDS_REUSE_MAP.md` through GitHub and independently re-read them. The local Agent may only validate those documents. Its remaining duties are to preserve/verify the PR134 archive (accepting the v21 local file only if byte-identical), bind `active.json` to the committed v22 Decision and generated v22 command plan, run the three required test groups, stage exactly the seven landing/gate paths, commit, and normal-push. `.frontend_stage/**` and `.platform_v1_runtime/**` remain pre-existing carryover scope only; no normal command may mutate or stage them. Ready/merge remain Owner-only after fresh exact-head workflows and final PR audit.
