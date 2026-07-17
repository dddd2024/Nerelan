```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260717_branch_evidence_convergence_rework_v4",
  "round_id": "round_20260717_branch_evidence_convergence_rework_v4",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260716_terminal_status_propagation_and_seal_restart_rework_v3",
  "follows_last_round_id": "round_20260716_terminal_status_propagation_and_seal_restart_rework_v3",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "restart_mode": "explicit_new_round",
  "previous_round_artifacts_read_only": true,
  "required_profile": "full",
  "decision_branch_mode": "branch_local_authority",
  "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
  "base_branch": "main",
  "reuse_existing_draft_pr_number": 5,
  "decision_commit_must_precede_v4_implementation": true,
  "decision_content_digest_lock_required": true,
  "command_plan_branch_binding_required": true,
  "command_plan_digest_lock_required": true,
  "command_plan_precedes_execution_required": true,
  "explicit_restart_segment_required": true,
  "canonical_lock_snapshot_required": true,
  "required_audit_lock_parity_required": true,
  "startup_snapshot_order_required": true,
  "remote_check_observation_required": true,
  "remote_green_required_for_acceptance": true,
  "final_evidence_seal_required": true,
  "closeout_required": true,
  "close_round_required": true,
  "pytest_required": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state.py"
  ],
  "allowed_project_state_files": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/*"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements*.txt",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/user_solve_*.py",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/roadmap/workstreams.json",
    "project_state/domains/*",
    "project_state/jobs/*",
    "project_state/user_sessions/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/*.db",
    "project_state/index.sqlite",
    "docs/roadmap/*"
  ],
  "publication_authorization": {
    "granted_by_user": true,
    "allowed_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
    "base_branch": "main",
    "reuse_existing_draft_pr_number": 5,
    "commit_allowed": true,
    "push_allowed": true,
    "draft_pr_allowed": true,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "merge_allowed": false,
    "rebase_allowed": false,
    "workflow_mutation_allowed": false,
    "secrets_mutation_allowed": false,
    "git_add_all_allowed": false,
    "stage_only_explicit_allowed_paths": true,
    "publish_only_after_required_validation": true
  }
}
```

# DECISION_PACKET

## 1. Goal

Complete one bounded `project_governance` rework round on the existing Draft PR #5 branch:

```text
agent/terminal-status-propagation-seal-restart-rework-v3
```

Do not create a second branch or PR.

Reuse the existing command-plan, execution-log, report-summary, final-check, closeout, archive, context, state-manifest, seal, and publication mechanisms. Repair only these remaining defects:

1. the v3 report cites an obsolete command-plan lock digest, lock time, and restart count;
2. the final lock records substantive execution before the final lock and no canonical accepted post-restart segment;
3. the startup-snapshot order check reported `PASS` despite contradictory observed chronology;
4. the publication receipt stopped at `IN_PROGRESS`, while CI, State Gate, and Decision Preflight later failed at `Install package`;
5. local `1555 passed` and local seal success were treated as sufficient even though report/lock parity and remote checks were not converged.

Required order:

```text
verify branch and PR
→ commit and lock v4 Decision
→ decision-lint
→ gate-profile
→ generate and lock branch-bound command-plan
→ create explicit restart segment
→ startup snapshot and round baseline
→ implementation
→ selected pytest
→ report/lock/restart parity validation
→ final-check
→ close-round and archive
→ context and state-manifest sync
→ final evidence seal
→ push same branch
→ observe PR checks to terminal state
```

## 2. Current Evidence

- The branch-local `project_state/decision_packet.md` is the current task authority; `task_packet.json` is background only.
- Current mainline is `project_governance`.
- Draft PR #5 is open, unmerged, and uses branch `agent/terminal-status-propagation-seal-restart-rework-v3`.
- The context packet and workstream registry exist. The registry states that roadmap entries are not execution authority.
- Existing foundations include command-plan locking, execution-log chronology, report-summary, final-check, run-closeout, close-round archive, context sync, state-manifest freshness, final seal, publication truth, policy-lint, prompt-consistency, Job foundations, Runner contract foundations, manual Web orchestration, User Solve, and CI/state-gate foundations.
- Existing capabilities must be strengthened, not reimplemented.
- `current_state.json`, `task_packet.json`, and `artifact_index.json` contain older sample-oriented facts and are read-only for this round.
- `negative_results.json` is reverse-solving scope; this round does not repeat those failed directions or commit `solve_reports`.
- v3 local evidence records `1555 passed`, local final gate `PASSED`, run-closeout `PASSED`, and seal `PASSED`.
- v3 Required Audit cites lock digest `76c8d5a0...`, lock time `2026-07-16T15:21:24.3340244Z`, and `restart_count=1`.
- The final v3 lock and seal bind digest `3b5c1b6d...`, lock time `2026-07-16T15:56:17.7096176Z`, and `restart_count=2`.
- The final lock records `first_substantive_command_at=2026-07-16T15:22:05.2192179Z`, earlier than the final lock time.
- The execution log records `run-closeout` and pytest before command-plan generation.
- The final-check startup-snapshot check was marked `PASS` although its observed sixth command was `run-closeout`.
- PR #5 remote CI, State Gate, and Decision Preflight checks all reached `failure` at the `Install package` step.
- The exact install failure may be inspected and classified, but packaging and workflow files are not authorized for mutation.
- v3 archives and sealed artifacts are historical read-only evidence.
- Missing reverse-solving sample artifacts are nonblocking.
- Local deterministic Python and tests are allowed. Reverse tools, model APIs, Runner dispatch, Web runtime, databases, cleanup apply, and destructive actions are not allowed.
- Closeout is allowed only after the v4 Decision and command-plan locks exist and a canonical restart segment proves accepted substantive work occurred after the final lock.
- This round does not duplicate an existing feature.

## 3. Do Not Do

Do not:

- work on another branch or open another PR;
- merge PR #5;
- modify v3 archived or sealed artifacts;
- edit old evidence to make v3 pass;
- reuse v3 `SUCCESS`, `ACCEPTED`, or `PASSED` as v4 acceptance evidence;
- treat a restart counter without a concrete restart segment as proof;
- accept stale lock values in reports;
- reorder transcript or execution-log entries;
- mark an ordering check `PASS` when observed and expected order disagree;
- hide or downgrade failed remote checks;
- modify `.github/workflows/*`, packaging files, dependency files, Skills, Runner, Job, frontend, User Solve, reverse-solving, roadmap, database, or cleanup modules;
- read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`;
- run reverse tools, runtime probes, debuggers, emulators, hooks, or model APIs;
- use `git add -A`;
- force-push, rebase, merge, tag, edit workflows or secrets, delete branches, or push directly to `main`;
- execute commands absent from the locked command-plan;
- modify v4 sealed artifacts after sealing.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/command_plan_lock.json`
- `project_state/gates/decision_content_lock.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/final_evidence_seal.json`
- `project_state/gates/publication_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/rounds/round_20260716_terminal_status_propagation_and_seal_restart_rework_v3/*`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`
- `.codex-skills/registry.json`

Read-only CI context:

- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`
- `.github/workflows/decision-preflight.yml`
- `pyproject.toml`
- CI run `29522575928`
- State Gate run `29522575937`
- Decision Preflight run `29522576149`

Required Git observations:

- current branch and HEAD;
- `git status --short`;
- v4 Decision commit ancestry;
- PR #5 head/base/draft/merge state;
- terminal workflow, job, step, and conclusion for each remote check.

## 5. Required Audit

Each final answer must include the artifact path, field or observation, concrete value, status, and item-specific conclusion.

1. Is the branch exactly `agent/terminal-status-propagation-seal-restart-rework-v3`?
2. Is Draft PR #5 still the sole unmerged review surface?
3. Is the v4 Decision commit an ancestor of all v4 implementation and evidence commits?
4. Is the Decision `APPROVED`, `project_governance`, and bound to active `reverse-agent-iteration@v2`?
5. Is `decision_packet.md` the task authority and `task_packet.json` background only?
6. Were v3 archives and seal left read-only?
7. Was the v4 Decision digest locked before command-plan generation?
8. Does the v4 command-plan bind the exact IDs, branch, Decision digest, and HEAD?
9. Was the final command-plan locked before accepted substantive execution?
10. Does `restart_segment.json` identify the invalidated prefix and accepted post-restart segment?
11. Is the accepted first substantive timestamp later than the final lock timestamp?
12. Are invalidated commands excluded from acceptance coverage?
13. Do report lock digest, lock time, restart ID, and restart count match canonical final lock artifacts?
14. Do report-summary and final-check reject stale lock values?
15. Does startup-snapshot ordering match observed chronology?
16. Does an ordering contradiction hard-fail under strict policy?
17. Do execution log and pytest transcript preserve actual order?
18. Do changed source/test files remain within scope?
19. Did selected pytest pass and cover changed tests?
20. Do report aliases and summaries agree?
21. Are context and state manifest current after final gate?
22. Do live and archive aliases match?
23. Does the final seal bind the final lock, restart segment, report, final gate, context, state manifest, and round manifest?
24. Were sealed artifacts unchanged afterward?
25. Were PR #5 remote checks observed to terminal state?
26. If a remote check failed, does the report avoid `ACCEPTED` and record the exact workflow, job, and failed step?
27. If all remote checks passed, are their run IDs and conclusions recorded?
28. Were workflow, packaging, dependency, Skill, Runner, frontend, User Solve, reverse-solving, roadmap, database, and cleanup files untouched?
29. Were prohibited Git operations avoided?
30. Do final-check, closeout, seal, reports, context, state manifest, round manifest, publication receipt, and remote observations agree on the final recommendation?

## 6. Implementation Scope

### 6.1 Preserve v3

Do not modify:

```text
project_state/rounds/round_20260716_terminal_status_propagation_and_seal_restart_rework_v3/
```

Create a new v4 round and supersede only live current artifacts through normal v4 generation.

### 6.2 Canonical restart segment

Extend the existing gate system with:

```text
project_state/gates/restart_segment.json
```

Required fields:

```text
decision_id
round_id
restart_id
restart_reason
invalidated_command_plan_sha256
invalidated_execution_chain_head
accepted_command_plan_sha256
accepted_command_plan_locked_at
startup_snapshot_generated_at
first_substantive_command_after_restart_at
accepted_execution_chain_head
invalidated_prefix_excluded_from_acceptance
restart_status
```

Hard-fail if accepted substantive execution precedes the final lock, invalidated commands satisfy accepted coverage, or a restart counter has no matching restart segment.

### 6.3 Canonical lock parity

`decision_content_lock.json`, `command_plan_lock.json`, and `restart_segment.json` are canonical.

Report generation, report-summary, final-check, closeout, and seal must consume identical values for:

```text
decision_packet_sha256
command_plan_sha256
command_plan_generated_at
command_plan_locked_at
restart_id
restart_count
first_substantive_command_after_restart_at
execution_branch
head_sha_at_plan_generation
```

Reject stale/intermediate values.

### 6.4 Truthful lifecycle checks

When strict startup ordering is required, expected and observed order must agree. A contradiction cannot be converted to `PASS` by setting `required=false`.

### 6.5 Remote check observation

Generate:

```text
project_state/gates/remote_check_observation.json
```

Record workflow name, run ID, job ID, terminal conclusion, failed step, failure summary, and observation time.

This round may classify the install failure, but may not modify workflow or packaging files. If such changes are required, stop and recommend a separate CI/package Decision.

### 6.6 Compatibility

Preserve existing CLI names and legacy artifact readability. Use additive fields and strict-mode checks. Do not create a second command, report, execution-log, or seal framework.

## 7. Tests

The v4 Decision commit and command-plan lock must precede tests.

Minimum command:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q
```

Required regression coverage:

1. obsolete lock digest/time/restart count in report fails;
2. report-summary and final-check use final lock snapshot;
3. substantive execution before final lock fails without valid restart segment;
4. restart count without restart artifact fails;
5. invalidated commands cannot satisfy accepted coverage;
6. accepted post-restart commands occur after final lock;
7. chronology is preserved;
8. startup expected/actual mismatch fails;
9. contradictory lifecycle check cannot pass;
10. correct full lifecycle passes;
11. v3 artifacts remain readable but cannot support v4 acceptance;
12. final failure propagates to report, closeout, recommendation, and seal;
13. failed remote checks prevent `ACCEPTED`;
14. `IN_PROGRESS` is not terminal success;
15. successful remote checks require concrete run IDs;
16. workflow/package mutation remains prohibited;
17. existing context, manifest, archive, report parity, and seal tests remain passing;
18. legacy artifacts remain readable.

Required generated evidence:

- v4 Decision and command-plan locks;
- `restart_segment.json`;
- `remote_check_observation.json`;
- execution log;
- pytest result;
- report aliases and report summary;
- final gate and closeout;
- context packet and state manifest;
- v4 round manifest and archive aliases;
- final evidence seal.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- branch, PR, Decision ancestry, or v4 IDs cannot be verified;
- Decision or command-plan lock cannot be established before substantive execution;
- invalidated and accepted execution segments cannot be separated;
- report generation cannot consume canonical final lock facts;
- lifecycle checks still pass contradictory evidence;
- required tests fail;
- report, execution log, final gate, closeout, context, state manifest, archive, seal, publication receipt, or remote observation disagree;
- v3 archived/sealed artifacts must be modified;
- v4 sealed artifacts must be modified after sealing;
- fixing `Install package` requires workflow, packaging, dependency, secret, or other forbidden changes;
- remote terminal status cannot be observed;
- remote checks remain failed after the latest authorized push;
- another mainline or forbidden file is required;
- unrelated work cannot be excluded from staging;
- publication commands are unauthorized;
- publication requires direct push to `main`, force push, rebase, merge, workflow/secret mutation, tag mutation, or branch deletion.

Do not expand scope. Preserve evidence and recommend one concrete next Decision.
